"""Shared helpers for the bench harness.

Standard library only: the harness must run unattended on a remote GPU box with
nothing installed beyond a Python 3.11+ interpreter and the runtime binaries.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

SCHEMA_VERSION = "bench/v1"

# Built at runtime on purpose: some tooling rewrites dotted loopback literals,
# so the source file must not contain one.
LOOPBACK = ".".join(["127", "0", "0", "1"])
WILDCARD = ".".join(["0", "0", "0", "0"])


# --------------------------------------------------------------------------- #
# time / io
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def read_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# stats
# --------------------------------------------------------------------------- #
def stats(values) -> dict:
    """mean/stddev/min/max over the samples. stddev is the sample stddev (n-1)."""
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0, "mean": None, "stddev": None, "min": None, "max": None}
    return {
        "n": len(vals),
        "mean": statistics.fmean(vals),
        "stddev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


# --------------------------------------------------------------------------- #
# networking
# --------------------------------------------------------------------------- #
def free_port(preferred: int | None = None) -> int:
    """Return `preferred` if it is free, else an ephemeral free port."""

    def _free(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((LOOPBACK, p))
            except OSError:
                return False
        return True

    if preferred and _free(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((LOOPBACK, 0))
        return s.getsockname()[1]


def http_get(url: str, timeout: float = 10.0):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def http_post_json(url: str, payload: dict, timeout: float = 300.0):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def wait_for_http(url: str, timeout: float, proc=None, interval: float = 0.25) -> float:
    """Block until `url` answers with HTTP 200. Returns elapsed seconds.

    Raises RuntimeError if the server process dies or the timeout expires.
    """
    t0 = time.perf_counter()
    last_err = None
    while time.perf_counter() - t0 < timeout:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(
                f"server process exited with code {proc.returncode} before becoming ready"
            )
        try:
            status, _ = http_get(url, timeout=5.0)
            if status == 200:
                return time.perf_counter() - t0
        except Exception as exc:  # noqa: BLE001 - any error means "not up yet"
            last_err = exc
        time.sleep(interval)
    raise RuntimeError(f"timed out after {timeout}s waiting for {url} ({last_err})")


# --------------------------------------------------------------------------- #
# OpenAI-compatible streaming client
# --------------------------------------------------------------------------- #
def stream_completion(base_url: str, payload: dict, timeout: float = 600.0) -> dict:
    """POST a streaming /v1/completions request and time it client-side.

    Returns a dict with:
      ttft_s, t_first_s, t_last_s, total_s, decode_window_s, prompt_tokens,
      completion_tokens, prefill_tps, decode_tps, finish_reason, usage,
      server_timings, chunks, text
    """
    url = base_url.rstrip("/") + "/v1/completions"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )

    t_send = time.perf_counter()
    t_first = None
    t_last = None
    chunks = 0
    text_parts: list[str] = []
    usage = None
    server_timings = None
    finish_reason = None

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                evt = json.loads(data)
            except json.JSONDecodeError:
                continue
            if evt.get("usage"):
                usage = evt["usage"]
            if evt.get("timings"):
                server_timings = evt["timings"]
            for choice in evt.get("choices", []):
                piece = choice.get("text")
                if piece:
                    now = time.perf_counter()
                    if t_first is None:
                        t_first = now
                    t_last = now
                    chunks += 1
                    text_parts.append(piece)
                if choice.get("finish_reason"):
                    finish_reason = choice["finish_reason"]

    t_end = time.perf_counter()
    completion_tokens = (usage or {}).get("completion_tokens")
    prompt_tokens = (usage or {}).get("prompt_tokens")

    ttft_s = (t_first - t_send) if t_first else None
    decode_window = (t_last - t_first) if (t_first and t_last) else None

    decode_tps = None
    if (
        completion_tokens
        and decode_window
        and decode_window > 0
        and completion_tokens > 1
    ):
        decode_tps = (completion_tokens - 1) / decode_window

    prefill_tps = None
    if prompt_tokens and ttft_s and ttft_s > 0:
        prefill_tps = prompt_tokens / ttft_s

    return {
        "ttft_s": ttft_s,
        "t_first_s": t_first,
        "t_last_s": t_last,
        "total_s": t_end - t_send,
        "decode_window_s": decode_window,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "prefill_tps": prefill_tps,
        "decode_tps": decode_tps,
        "finish_reason": finish_reason,
        "usage": usage,
        "server_timings": server_timings,
        "chunks": chunks,
        "text": "".join(text_parts),
    }


# --------------------------------------------------------------------------- #
# environment fingerprint
# --------------------------------------------------------------------------- #
def _run(cmd: list[str], timeout: float = 10.0) -> str | None:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return None
    return None


def _read_cpu_model() -> str | None:
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def env_fingerprint() -> dict:
    """Everything needed to reproduce (or explain) a measurement."""
    return {
        "captured_at": now_iso(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "cpu_count": os.cpu_count(),
        "cpu_model": _read_cpu_model(),
        "uname": _run(["uname", "-a"]),
        "git_commit": _run(["git", "rev-parse", "HEAD"], timeout=5),
        "git_dirty": bool(_run(["git", "status", "--porcelain"], timeout=5)),
    }


def resolve_path(path: str, base: str | None = None) -> str:
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(base or os.getcwd(), path))
