"""Eval-set runner (deliberately separate from the perf runner).

Consumes a JSONL eval set, runs every item through the same serving stack the perf
runner uses, and writes the raw generations plus per-item timings. It performs no
scoring - quality scoring reads this output - so the same harness backs both.

Eval-set format (one JSON object per line):
    {"id": "...", "prompt": "...", "meta": {...}}          # prompt used verbatim
    {"id": "...", "messages": [{"role": "user", ...}]}      # chat form (optional)

Example
-------
python -m harness.eval_runner --backend llamacpp \
    --model models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
    --eval eval/smoke_eval.jsonl --out results/eval_smoke.jsonl \
    --max-new-tokens 64 --limit 4
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request

from . import SCHEMA_VERSION
from .backends import BACKEND_CHOICES, BackendError, make_builder
from .common import env_fingerprint, now_iso, read_jsonl, stream_completion, write_json
from .vram import Sampler, probe_gpu


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harness.eval_runner")
    p.add_argument("--backend", choices=BACKEND_CHOICES, default="llamacpp")
    p.add_argument("--model", required=True)
    p.add_argument("--eval", required=True, help="JSONL eval set")
    p.add_argument("--out", required=True, help="JSONL output (raw generations)")
    p.add_argument("--summary-out", default=None, help="optional JSON summary path")
    p.add_argument("--log-dir", default="results/logs")
    p.add_argument("--label", default=None)
    p.add_argument("--alias", default=None)
    p.add_argument("--limit", type=int, default=None, help="only run the first N items")
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--timeout", type=float, default=900.0)
    p.add_argument("--chat", action="store_true", help="use /v1/chat/completions")
    p.add_argument("--stop", action="append", default=None,
                   help="stop sequence (repeatable); overridden per item by the item's 'stop' key")

    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--ctx", type=int, default=4096)
    p.add_argument("--parallel", type=int, default=1)
    p.add_argument("--ngl", type=int, default=99)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--tensor-split", default=None)
    p.add_argument("--flash-attn", default=None, choices=[None, "on", "off", "auto"])
    p.add_argument("--llamacpp-dir", default=os.environ.get("LLAMACPP_DIR", "runtime/llama-b11316"))
    p.add_argument("--cudart-dir", default=os.environ.get("CUDART_DIR", None))
    p.add_argument("--vllm-python", default=os.environ.get("VLLM_PYTHON", None))
    p.add_argument("--quantization", default=None)
    p.add_argument("--dtype", default=None)
    p.add_argument("--enforce-eager", action="store_true")
    p.add_argument("--tensor-parallel", type=int, default=1)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    p.add_argument("--ready-timeout", type=float, default=1800.0)
    p.add_argument("--vram-interval", type=float, default=0.25)
    p.add_argument("--keep-server", action="store_true")
    return p


def chat_completion(base_url: str, payload: dict, timeout: float) -> dict:
    """Non-streaming chat call, used when the eval set supplies chat messages."""
    url = base_url.rstrip("/") + "/v1/chat/completions"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        evt = json.loads(resp.read().decode("utf-8"))
    total_s = time.perf_counter() - t0
    choice = (evt.get("choices") or [{}])[0]
    usage = evt.get("usage") or {}
    text = (choice.get("message") or {}).get("content", "")
    completion_tokens = usage.get("completion_tokens")
    decode_tps = None
    if completion_tokens and total_s > 0:
        # non-streaming: the whole call is prefill + decode, so this is a lower bound
        decode_tps = completion_tokens / total_s
    return {
        "text": text,
        "completion_tokens": completion_tokens,
        "prompt_tokens": usage.get("prompt_tokens"),
        "total_s": total_s,
        "ttft_s": None,
        "decode_tps": decode_tps,
        "prefill_tps": None,
        "finish_reason": choice.get("finish_reason"),
        "usage": usage,
        "error": None,
    }


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    from .common import LOOPBACK

    if args.host is None:
        args.host = LOOPBACK
    if args.label is None:
        args.label = os.path.splitext(os.path.basename(args.model.rstrip("/")))[0]

    items = list(read_jsonl(args.eval))
    if args.limit:
        items = items[: args.limit]
    if not items:
        raise SystemExit(f"eval set {args.eval} is empty")

    sampler = Sampler(interval_s=args.vram_interval)
    sampler.start()
    gpu = probe_gpu()
    builder = make_builder(args, args.log_dir)

    srv = None
    status = "ok"
    errors: list[str] = []
    skipped = 0
    t_start = time.perf_counter()
    meta = {
        "schema_version": SCHEMA_VERSION,
        "kind": "eval",
        "label": args.label,
        "model": args.model,
        "backend": args.backend,
        "eval_set": os.path.abspath(args.eval),
        "eval_items": len(items),
        "decoding": {
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "seed": args.seed,
            "chat": args.chat,
        },
        "environment": env_fingerprint(),
        "gpu": gpu,
        "started_at": now_iso(),
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    try:
        srv = builder.build()
        srv.start(args.host, ready_timeout=args.ready_timeout)
        assert srv.base_url
        meta["server"] = srv.describe()

        with open(args.out, "w", encoding="utf-8") as out_fh:
            for i, item in enumerate(items, 1):
                if item.get("status") == "skipped":
                    skipped += 1
                    out_fh.write(json.dumps({
                        "id": item.get("id") or item.get("item_id") or f"item-{i}",
                        "index": i, "status": "skipped",
                        "skip_reason": item.get("skip_reason"),
                        "meta": item.get("meta") or {
                            k: item[k] for k in ("part", "party", "question_id", "source_id")
                            if k in item
                        },
                    }, ensure_ascii=False) + "\n")
                    out_fh.flush()
                    print(f"  [{i}/{len(items)}] {item.get('item_id', i)} skipped", flush=True)
                    continue
                payload = {
                    "model": args.alias or args.label,
                    "max_tokens": args.max_new_tokens,
                    "temperature": args.temperature,
                    "top_p": args.top_p,
                    "seed": args.seed,
                    "stream": False,
                    "usage": True,
                }
                stop = item.get("stop", args.stop)
                if stop:
                    payload["stop"] = stop
                try:
                    if args.chat or item.get("messages"):
                        msgs = item.get("messages") or [{"role": "user", "content": item["prompt"]}]
                        payload["messages"] = msgs
                        res = chat_completion(srv.base_url, payload, args.timeout)
                    else:
                        payload["prompt"] = item["prompt"]
                        payload["cache_prompt"] = False
                        res = stream_completion(srv.base_url, {**payload, "stream": True,
                                                              "stream_options": {"include_usage": True}},
                                                timeout=args.timeout)
                        res["error"] = None
                except Exception as exc:  # noqa: BLE001
                    res = {"text": "", "error": f"{type(exc).__name__}: {exc}",
                           "completion_tokens": None, "prompt_tokens": None,
                           "ttft_s": None, "decode_tps": None, "prefill_tps": None,
                           "total_s": None, "finish_reason": None, "usage": None}

                row = {
                    "id": item.get("id") or item.get("item_id") or f"item-{i}",
                    "index": i,
                    "model": args.model,
                    "label": args.label,
                    "output": res.get("text", ""),
                    "prompt_tokens": res.get("prompt_tokens"),
                    "completion_tokens": res.get("completion_tokens"),
                    "ttft_s": res.get("ttft_s"),
                    "decode_tps": res.get("decode_tps"),
                    "prefill_tps": res.get("prefill_tps"),
                    "total_s": res.get("total_s"),
                    "finish_reason": res.get("finish_reason"),
                    "error": res.get("error"),
                }
                if item.get("meta") is not None:
                    row["meta"] = item["meta"]
                elif item.get("part") is not None:
                    row["meta"] = {
                        k: item[k]
                        for k in (
                            "part", "party", "question_id", "coder", "source_id",
                            "reference_code", "reference_confidence", "reference_codes_all",
                            "coder_agreement", "source_policy", "status",
                        )
                        if k in item
                    }
                if item.get("reference") is not None:
                    row["reference"] = item["reference"]
                out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                out_fh.flush()
                if row["error"]:
                    errors.append(f"{row['id']}: {row['error']}")
                state = f"{row['completion_tokens']} tok" if not row["error"] else "ERR"
                print(f"  [{i}/{len(items)}] {row['id']} {state}", flush=True)
    except BackendError as exc:
        status = "backend_error"
        errors.append(str(exc))
        print(f"ERROR: {exc}", flush=True)
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        errors.append(f"{type(exc).__name__}: {exc}")
        print(f"ERROR: {type(exc).__name__}: {exc}", flush=True)

    if srv is not None and not args.keep_server:
        srv.stop()
    sampler.stop()

    meta.update(
        {
            "status": status,
            "errors": errors,
            "items_run": len(items) - skipped,
            "items_skipped": skipped,
            "session_s": time.perf_counter() - t_start,
            "vram": sampler.summary(),
            "output": os.path.abspath(args.out),
            "finished_at": now_iso(),
        }
    )
    if args.summary_out:
        write_json(args.summary_out, meta)
        print(f"wrote {args.summary_out}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
