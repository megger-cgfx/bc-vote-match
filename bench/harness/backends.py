"""Runtime adapters.

A *backend* knows how to (a) build a command line for a model, (b) start it,
(c) report how long the load took, (d) expose an OpenAI-compatible base URL, and
(e) shut down cleanly. Everything else in the harness talks only to the HTTP API,
so both runtimes are measured by identical code paths.

Model specs
-----------
llamacpp : a path to a local .gguf file, or `hf:<user>/<repo>[:<quant>]`, which
           llama.cpp downloads itself (e.g. `hf:Qwen/Qwen2.5-0.5B-Instruct-GGUF:q4_k_m`).
vllm     : a Hugging Face repo id (`Qwen/Qwen2.5-7B-Instruct`) or a local dir,
           plus `--quantization {awq,gptq,...}` when the repo is a quantized one.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time

from .common import LOOPBACK, free_port, now_iso, wait_for_http

READY_PATH = "/health"
BACKEND_CHOICES = ("llamacpp", "vllm")


class BackendError(RuntimeError):
    pass


class Server:
    """A running inference server plus the metadata needed to interpret results."""

    def __init__(self, name: str, cmd: list[str], env: dict, log_path: str):
        self.name = name
        self.cmd = cmd
        self.env = env
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None
        self.port: int | None = None
        self.base_url: str | None = None
        self.load_time_s: float | None = None
        self.started_at: str | None = None
        self.runtime_version: str | None = None

    # -- lifecycle ---------------------------------------------------------- #
    def start(self, host: str, port: int | None = None, ready_timeout: float = 900.0) -> "Server":
        os.makedirs(os.path.dirname(os.path.abspath(self.log_path)) or ".", exist_ok=True)
        self.port = port or self.port or free_port()
        self.base_url = f"http://{host}:{self.port}"
        self.log_fh = open(self.log_path, "w", encoding="utf-8")
        self.started_at = now_iso()
        t0 = time.perf_counter()
        self.proc = subprocess.Popen(
            self.cmd,
            stdout=self.log_fh,
            stderr=subprocess.STDOUT,
            env=self.env,
            cwd=os.getcwd(),
        )
        try:
            self.load_time_s = wait_for_http(
                self.base_url + READY_PATH, timeout=ready_timeout, proc=self.proc
            )
        except RuntimeError as exc:
            tail = self.log_tail()
            self.stop()
            raise BackendError(f"{self.name}: {exc}\n--- server log tail ---\n{tail}") from exc
        # /health is a cheap liveness probe; give the scheduler a moment to settle.
        return self

    def stop(self, grace: float = 20.0) -> None:
        proc = getattr(self, "proc", None)
        if proc is not None and proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=grace)
        fh = getattr(self, "log_fh", None)
        if fh is not None and not fh.closed:
            fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()
        return False

    # -- introspection ------------------------------------------------------ #
    def log_tail(self, lines: int = 40) -> str:
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as fh:
                return "".join(fh.readlines()[-lines:])
        except OSError:
            return "<no log>"

    def describe(self) -> dict:
        return {
            "backend": self.name,
            "command": self.cmd,
            "port": self.port,
            "base_url": self.base_url,
            "load_time_s": self.load_time_s,
            "runtime_version": self.runtime_version,
            "started_at": self.started_at,
            "log_path": self.log_path,
        }


# --------------------------------------------------------------------------- #
# llama.cpp (GGUF)
# --------------------------------------------------------------------------- #
LLAMACPP_ENV_KEYS = ("CUDA_VISIBLE_DEVICES", "GGML_CUDA_ENABLE_UNIFIED_MEMORY")


class LlamaCppBuilder:
    name = "llamacpp"

    def __init__(self, args, log_dir: str):
        self.args = args
        self.log_dir = log_dir

    def _bin(self, which: str) -> str:
        root = self.args.llamacpp_dir
        path = os.path.join(root, which) if root else shutil.which(which)
        if not path or not os.path.exists(path):
            raise BackendError(
                f"llama.cpp binary '{which}' not found "
                f"(looked in {root or '$PATH'}). Run scripts/setup_llamacpp.sh first "
                f"or pass --llamacpp-dir."
            )
        return path

    def version(self) -> str | None:
        try:
            out = subprocess.run(
                [self._bin("llama-server"), "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return (out.stdout + out.stderr).strip().splitlines()[0] if out.returncode == 0 else None
        except Exception:  # noqa: BLE001
            return None

    def build(self) -> Server:
        a = self.args
        model = a.model
        model_flag = ["-m", model]
        if model.startswith("hf:"):
            model_flag = ["-hf", model[3:]]
        port = free_port(a.port)

        cmd = [
            self._bin("llama-server"),
            *model_flag,
            "--host",
            a.host,
            "--port",
            str(port),
            "-c",
            str(a.ctx),
            "-np",
            str(a.parallel),
            "-ngl",
            str(a.ngl),
            "-t",
            str(a.threads),
            "--seed",
            str(a.seed),
            "--no-warmup",
            "--no-log-prefix",
            "--log-timestamps",
            "--alias",
            a.alias or (a.label or "model"),
        ]
        if a.tensor_split:
            cmd += ["-ts", a.tensor_split]
        if a.flash_attn:
            cmd += ["-fa", a.flash_attn]

        env = os.environ.copy()
        env.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        if a.cudart_dir:
            env["LD_LIBRARY_PATH"] = a.cudart_dir + os.pathsep + env.get("LD_LIBRARY_PATH", "")

        srv = Server(
            self.name,
            cmd,
            env,
            log_path=os.path.join(self.log_dir, f"{a.label or 'model'}.{self.name}.log"),
        )
        srv.port = port
        srv.runtime_version = self.version()
        return srv


# --------------------------------------------------------------------------- #
# vLLM (AWQ / GPTQ)
# --------------------------------------------------------------------------- #
class VllmBuilder:
    name = "vllm"

    def __init__(self, args, log_dir: str):
        self.args = args
        self.log_dir = log_dir

    def version(self) -> str | None:
        try:
            out = subprocess.run(
                [self.args.vllm_python or sys.executable, "-c",
                 "import vllm; print(vllm.__version__)"],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            return out.stdout.strip() if out.returncode == 0 else None
        except Exception:  # noqa: BLE001
            return None

    def build(self) -> Server:
        a = self.args
        port = free_port(a.port)
        cmd = [
            a.vllm_python or sys.executable,
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            a.model,
            "--host",
            a.host,
            "--port",
            str(port),
            "--seed",
            str(a.seed),
            "--max-model-len",
            str(a.ctx),
            "--gpu-memory-utilization",
            str(a.gpu_memory_utilization),
            "--served-model-name",
            a.alias or (a.label or "model"),
        ]
        if a.quantization:
            cmd += ["--quantization", a.quantization]
        if a.dtype:
            cmd += ["--dtype", a.dtype]
        if a.enforce_eager:
            cmd += ["--enforce-eager"]
        if a.tensor_parallel > 1:
            cmd += ["--tensor-parallel-size", str(a.tensor_parallel)]

        env = os.environ.copy()
        env.setdefault("VLLM_NO_USAGE_STATS", "1")
        env.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

        srv = Server(
            self.name,
            cmd,
            env,
            log_path=os.path.join(self.log_dir, f"{a.label or 'model'}.{self.name}.log"),
        )
        srv.port = port
        srv.runtime_version = self.version()
        return srv


def make_builder(args, log_dir: str):
    if args.backend == "llamacpp":
        return LlamaCppBuilder(args, log_dir)
    if args.backend == "vllm":
        return VllmBuilder(args, log_dir)
    raise BackendError(f"unknown backend '{args.backend}' (choose from {BACKEND_CHOICES})")


__all__ = [
    "BACKEND_CHOICES",
    "BackendError",
    "LlamaCppBuilder",
    "Server",
    "VllmBuilder",
    "make_builder",
    "LOOPBACK",
]
