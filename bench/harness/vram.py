"""VRAM / GPU-utilisation sampling.

Peak VRAM is defined as the maximum `memory.used` reported by nvidia-smi while a
measurement is in flight. nvidia-smi reports *device* usage, so a busy shared GPU
inflates the number - the harness therefore also records a baseline taken before
the runtime starts, and reports `peak_vram_delta_mb` (peak - baseline) alongside
the absolute peak.

On a machine without nvidia-smi the sampler degrades to sampling the runtime
process's RSS from /proc, and marks `vram.supported = false` so no GPU number is
ever silently invented.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time

from .common import now_iso

NVIDIA_SMI = "nvidia-smi"


def _nvidia_smi(args: list[str], timeout: float = 10.0) -> str | None:
    if shutil.which(NVIDIA_SMI) is None:
        return None
    try:
        out = subprocess.run(
            [NVIDIA_SMI, *args], capture_output=True, text=True, timeout=timeout, check=False
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return None
    return None


def probe_gpu() -> dict:
    """Describe the GPU(s) visible to this process, without assuming one exists."""
    info = {
        "supported": False,
        "reason": None,
        "captured_at": now_iso(),
        "tool": NVIDIA_SMI,
        "devices": [],
    }
    if shutil.which(NVIDIA_SMI) is None:
        info["reason"] = f"{NVIDIA_SMI} not found on PATH (no NVIDIA GPU passthrough)"
        return info

    query = (
        "index,name,driver_version,memory.total,memory.used,compute_cap,"
        "utilization.gpu"
    )
    out = _nvidia_smi([f"--query-gpu={query}", "--format=csv,noheader,nounits"])
    if out is None:
        info["reason"] = f"{NVIDIA_SMI} present but not queryable (driver/tool error)"
        return info

    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        info["devices"].append(
            {
                "index": int(parts[0]) if parts[0].isdigit() else parts[0],
                "name": parts[1],
                "driver_version": parts[2],
                "memory_total_mb": _num(parts[3]),
                "memory_used_mb": _num(parts[4]),
                "compute_cap": parts[5],
                "utilization_gpu_pct": _num(parts[6]),
            }
        )
    info["supported"] = bool(info["devices"])
    if not info["supported"]:
        info["reason"] = "nvidia-smi returned no devices"
    return info


def _num(text: str):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def process_rss_mb(pid: int) -> float | None:
    """Resident set size of `pid` in MB, straight from /proc."""
    try:
        with open(f"/proc/{pid}/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        return None
    return None


class Sampler:
    """Sample device VRAM (and host RSS as a fallback) on a background thread."""

    def __init__(self, pid: int | None = None, interval_s: float = 0.1):
        self.pid = pid
        self.interval_s = interval_s
        self.gpu = probe_gpu()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.samples: list[dict] = []

    # -- lifecycle ---------------------------------------------------------- #
    def start(self) -> "Sampler":
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.samples.append(self._sample())
            self._stop.wait(self.interval_s)

    def _sample(self) -> dict:
        s: dict[str, object] = {"t": time.perf_counter()}
        if self.gpu["supported"]:
            out = _nvidia_smi(
                ["--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                timeout=5.0,
            )
            if out:
                first = out.splitlines()[0].split(",")
                if len(first) >= 2:
                    s["vram_used_mb"] = _num(first[0])
                    s["gpu_util_pct"] = _num(first[1])
        if self.pid is not None:
            s["rss_mb"] = process_rss_mb(self.pid)
        return s

    # -- reporting ---------------------------------------------------------- #
    def _values(self, key: str) -> list[float]:
        return [s[key] for s in self.samples if s.get(key) is not None]

    def summary(self) -> dict:
        used = self._values("vram_used_mb")
        rss = self._values("rss_mb")
        util = self._values("gpu_util_pct")
        return {
            "supported": self.gpu["supported"],
            "reason": self.gpu["reason"],
            "device": self.gpu["devices"][0] if self.gpu["devices"] else None,
            "samples": len(self.samples),
            "interval_s": self.interval_s,
            "peak_vram_mb": max(used) if used else None,
            "min_vram_mb": min(used) if used else None,
            "peak_gpu_util_pct": max(util) if util else None,
            "peak_rss_mb": max(rss) if rss else None,
        }

    def reset(self) -> None:
        self.samples = []
