"""Reproducible benchmark harness for base-model selection on a single RTX 3090.

Modules
-------
common       shared helpers (HTTP/SSE client, stats, fingerprints, IO)
vram         GPU/VRAM sampler (nvidia-smi) with a CPU-only fallback
backends     runtime adapters: llama.cpp server (GGUF) and vLLM (AWQ/GPTQ)
perf         performance runner: load time, VRAM, TTFT, prefill/decode tps, concurrency
eval_runner  eval-set runner (separate from perf so quality scoring reuses the same plumbing)
summarize    results -> human-readable table

Run `python -m harness.perf --help` for the perf CLI.
"""

SCHEMA_VERSION = "bench/v1"
