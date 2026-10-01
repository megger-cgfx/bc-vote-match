"""Performance runner.

Measures, for one model + runtime configuration:
  * load_time_s          - process start -> server reports ready
  * peak_vram_mb         - max nvidia-smi memory.used sampled during the session
  * ttft_s               - send -> first streamed token
  * prefill_tps          - prompt_tokens / ttft_s
  * decode_tps           - (completion_tokens - 1) / (last_token - first_token)
  * throughput @ c=1,4   - aggregate completion tokens / wall time for c concurrent requests

Every measurement is taken `--repeats` times after `--warmup` discarded runs; the
JSON records each individual sample plus mean/stddev so no number is ever reported
from a single sample.

Example
-------
python -m harness.perf --backend llamacpp \
    --model models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
    --label smoke-qwen0.5b-q4km --ctx 2048 --ngl 99 --parallel 4 \
    --concurrency 1,4 --repeats 3 --out results/smoke-qwen0.5b-q4km.json
"""

from __future__ import annotations

import argparse
import os
import statistics
import threading
import time

from . import SCHEMA_VERSION
from .backends import BACKEND_CHOICES, BackendError, make_builder
from .common import env_fingerprint, now_iso, stream_completion, write_json
from .vram import Sampler, probe_gpu

# A neutral, deterministic corpus used to build prefill prompts. Content does not
# matter for throughput; determinism does.
CORPUS = (
    "The quick brown fox jumps over the lazy dog. "
    "Machine learning systems trade memory bandwidth against compute. "
    "A benchmark is reproducible when its inputs, versions and hardware are fixed. "
    "Throughput at batch size one is dominated by memory bandwidth. "
    "Prefill is compute bound, decode is memory bound. "
)


def make_prompt(target_tokens: int, nonce: str) -> str:
    """Deterministic prompt of roughly `target_tokens` tokens (~4 chars/token)."""
    target_chars = max(16, int(target_tokens) * 4)
    reps = (target_chars // len(CORPUS)) + 1
    body = (CORPUS * reps)[:target_chars]
    return f"{body}\n\nQuestion id: {nonce}\nAnswer in one sentence."


def request_payload(args, prompt: str) -> dict:
    return {
        "model": args.alias or args.label or "model",
        "prompt": prompt,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "top_p": 1.0,
        "seed": args.seed,
        "stream": True,
        "cache_prompt": False,
        "ignore_eos": True,
        "stream_options": {"include_usage": True},
    }


def one_request(base_url: str, payload: dict, timeout: float) -> dict:
    t0 = time.perf_counter()
    try:
        res = stream_completion(base_url, payload, timeout=timeout)
        res["error"] = None
    except Exception as exc:  # noqa: BLE001 - a failed request is data, not a crash
        res = {
            "error": f"{type(exc).__name__}: {exc}",
            "ttft_s": None,
            "decode_tps": None,
            "prefill_tps": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_s": time.perf_counter() - t0,
        }
    res["wall_s"] = time.perf_counter() - t0
    return res


def run_batch(base_url: str, payloads: list[dict], timeout: float) -> dict:
    """Fire len(payloads) requests simultaneously; return per-request and aggregate data."""
    results: list[dict | None] = [None] * len(payloads)
    barrier = threading.Barrier(len(payloads))

    def worker(idx: int):
        barrier.wait()
        results[idx] = one_request(base_url, payloads[idx], timeout)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(payloads))]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall_s = time.perf_counter() - t0

    done = [r for r in results if r is not None]
    ok = [r for r in done if not r.get("error")]
    total_completion = sum(r.get("completion_tokens") or 0 for r in ok)
    errors = [r["error"] for r in done if r.get("error")]

    return {
        "concurrency": len(payloads),
        "wall_s": wall_s,
        "aggregate_decode_tps": (total_completion / wall_s) if wall_s > 0 else None,
        "total_completion_tokens": total_completion,
        "prompt_tokens": ok[0].get("prompt_tokens") if ok else None,
        "per_request": done,
        "mean_ttft_s": statistics.fmean([r["ttft_s"] for r in ok if r.get("ttft_s")]) if ok else None,
        "mean_decode_tps": statistics.fmean([r["decode_tps"] for r in ok if r.get("decode_tps")]) if ok else None,
        "mean_prefill_tps": statistics.fmean([r["prefill_tps"] for r in ok if r.get("prefill_tps")]) if ok else None,
        "errors": errors,
    }


def summarize_batches(batches: list[dict]) -> list[dict]:
    """Group non-warmup batches by concurrency and report mean/stddev over repeats."""
    out = []
    for conc in sorted({b["concurrency"] for b in batches}):
        group = [b for b in batches if b["concurrency"] == conc and not b.get("warmup")]
        if not group:
            continue
        out.append(
            {
                "concurrency": conc,
                "repeats": len(group),
                "aggregate_decode_tps": _stats([b["aggregate_decode_tps"] for b in group]),
                "ttft_s": _stats([b["mean_ttft_s"] for b in group]),
                "decode_tps_per_stream": _stats([b["mean_decode_tps"] for b in group]),
                "prefill_tps": _stats([b["mean_prefill_tps"] for b in group]),
                "wall_s": _stats([b["wall_s"] for b in group]),
                "errors": sum(len(b.get("errors", [])) for b in group),
            }
        )
    return out


def _stats(values) -> dict:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0, "mean": None, "stddev": None}
    return {
        "n": len(vals),
        "mean": statistics.fmean(vals),
        "stddev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="harness.perf", description="Measure a model's serving performance."
    )
    p.add_argument("--backend", choices=BACKEND_CHOICES, default="llamacpp")
    p.add_argument("--model", required=True, help="gguf path or hf:<repo>[:quant]; vLLM repo id")
    p.add_argument("--label", default=None, help="name for the run (defaults to model basename)")
    p.add_argument("--alias", default=None, help="model name the server advertises")
    p.add_argument("--out", default=None, help="output JSON path")
    p.add_argument("--log-dir", default="results/logs")

    # server
    p.add_argument("--host", default=None, help="bind address (default loopback)")
    p.add_argument("--port", type=int, default=None, help="preferred port (else ephemeral)")
    p.add_argument("--ctx", type=int, default=4096, help="context length / max-model-len")
    p.add_argument("--parallel", type=int, default=None, help="llama.cpp slots (default = max concurrency)")
    p.add_argument("--ngl", type=int, default=99, help="llama.cpp GPU layers (99 = all)")
    p.add_argument("--threads", type=int, default=8, help="llama.cpp CPU threads")
    p.add_argument("--tensor-split", default=None)
    p.add_argument("--flash-attn", default=None, choices=[None, "on", "off", "auto"])
    p.add_argument("--llamacpp-dir", default=os.environ.get("LLAMACPP_DIR", "runtime/llama-b11316"))
    p.add_argument("--cudart-dir", default=os.environ.get("CUDART_DIR", None))
    p.add_argument("--vllm-python", default=os.environ.get("VLLM_PYTHON", None))
    p.add_argument("--quantization", default=None, help="vLLM --quantization (awq, gptq, ...)")
    p.add_argument("--dtype", default=None)
    p.add_argument("--enforce-eager", action="store_true")
    p.add_argument("--tensor-parallel", type=int, default=1)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    p.add_argument("--ready-timeout", type=float, default=1800.0, help="seconds to wait for /health")

    # workload
    p.add_argument("--concurrency", default="1,4", help="comma-separated concurrency levels")
    p.add_argument("--repeats", type=int, default=3, help="measured repeats per level")
    p.add_argument("--warmup", type=int, default=1, help="discarded warmup requests before measuring")
    p.add_argument("--max-tokens", type=int, default=128, help="tokens to decode per request")
    p.add_argument("--prompt-tokens", type=int, default=512, help="approx prompt size in tokens")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--timeout", type=float, default=900.0, help="per-request HTTP timeout")
    p.add_argument("--vram-interval", type=float, default=0.1, help="VRAM sampling period, seconds")
    p.add_argument("--keep-server", action="store_true", help="leave the server running on exit")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    from .common import LOOPBACK

    if args.host is None:
        args.host = LOOPBACK
    if args.label is None:
        args.label = os.path.splitext(os.path.basename(args.model.rstrip("/")))[0]
    if args.parallel is None:
        args.parallel = max(int(c) for c in args.concurrency.split(","))

    levels = [int(c) for c in args.concurrency.split(",") if c.strip()]
    gpu_before = probe_gpu()
    sampler = Sampler(interval_s=args.vram_interval)
    sampler.start()

    builder = make_builder(args, args.log_dir)
    record = {
        "schema_version": SCHEMA_VERSION,
        "kind": "perf",
        "label": args.label,
        "started_at": now_iso(),
        "model": {"spec": args.model, "alias": args.alias or args.label},
        "config": {
            "backend": args.backend,
            "ctx": args.ctx,
            "parallel": args.parallel,
            "ngl": args.ngl,
            "threads": args.threads,
            "quantization": args.quantization,
            "max_tokens": args.max_tokens,
            "prompt_tokens_target": args.prompt_tokens,
            "temperature": args.temperature,
            "seed": args.seed,
            "concurrency": levels,
            "repeats": args.repeats,
            "warmup": args.warmup,
        },
        "environment": env_fingerprint(),
        "gpu": gpu_before,
        "server": None,
        "baseline_vram_mb": None,
        "peak_vram_mb": None,
        "batches": [],
        "summary": [],
        "status": "running",
        "errors": [],
    }

    srv = None
    t_start = time.perf_counter()
    try:
        base = sampler.samples[-1] if sampler.samples else {}
        record["baseline_vram_mb"] = base.get("vram_used_mb")

        srv = builder.build()
        srv.start(args.host, ready_timeout=args.ready_timeout)
        assert srv.base_url, "server did not report a base URL"
        record["server"] = srv.describe()
        record["baseline_vram_mb"] = record["baseline_vram_mb"] or (
            sampler.samples[-1].get("vram_used_mb") if sampler.samples else None
        )

        # ---- warmup (discarded) ------------------------------------------- #
        for i in range(args.warmup):
            payload = request_payload(args, make_prompt(args.prompt_tokens, f"warmup-{i}"))
            batch = run_batch(srv.base_url, [payload], args.timeout)
            batch["warmup"] = True
            batch["repeat"] = -1
            record["batches"].append(batch)

        # ---- measured runs ------------------------------------------------ #
        for level in levels:
            for rep in range(args.repeats):
                payloads = [
                    request_payload(
                        args, make_prompt(args.prompt_tokens, f"c{level}-r{rep}-i{i}")
                    )
                    for i in range(level)
                ]
                batch = run_batch(srv.base_url, payloads, args.timeout)
                batch["warmup"] = False
                batch["repeat"] = rep
                batch["vram_used_mb"] = sampler.samples[-1].get("vram_used_mb") if sampler.samples else None
                record["batches"].append(batch)
                print(
                    f"  c={level} repeat={rep + 1}/{args.repeats} "
                    f"agg={batch['aggregate_decode_tps'] and round(batch['aggregate_decode_tps'], 2)} tok/s "
                    f"ttft={batch['mean_ttft_s'] and round(batch['mean_ttft_s'], 4)}s "
                    f"per-stream={batch['mean_decode_tps'] and round(batch['mean_decode_tps'], 2)} tok/s",
                    flush=True,
                )
                if batch["errors"]:
                    record["errors"].extend(batch["errors"])

        record["summary"] = summarize_batches(record["batches"])
        record["status"] = "ok"
    except BackendError as exc:
        record["status"] = "backend_error"
        record["errors"].append(str(exc))
        print(f"ERROR: {exc}", flush=True)
    except Exception as exc:  # noqa: BLE001
        record["status"] = "failed"
        record["errors"].append(f"{type(exc).__name__}: {exc}")
        print(f"ERROR: {type(exc).__name__}: {exc}", flush=True)

    if srv is not None and not args.keep_server:
        srv.stop()

    record["session_s"] = time.perf_counter() - t_start
    sampler.stop()
    vram = sampler.summary()
    record["vram"] = vram
    record["peak_vram_mb"] = vram.get("peak_vram_mb")
    record["peak_vram_delta_mb"] = (
        (vram["peak_vram_mb"] - record["baseline_vram_mb"])
        if (vram.get("peak_vram_mb") is not None and record.get("baseline_vram_mb") is not None)
        else None
    )
    record["finished_at"] = now_iso()

    if args.out:
        write_json(args.out, record)
        print(f"wrote {args.out}")
    else:
        import json

        print(json.dumps(record, indent=2))
    return 0 if record["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
