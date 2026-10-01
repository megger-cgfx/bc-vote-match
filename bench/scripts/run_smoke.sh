#!/usr/bin/env bash
# End-to-end smoke test: proves the whole harness works on the box it runs on.
#
#   scripts/run_smoke.sh                     # tiny model, CUDA if present
#   scripts/run_smoke.sh --ngl 0             # force CPU
#   scripts/run_smoke.sh --model <gguf|hf:>  # any model id
#
# Steps: resolve eval set -> perf suite (c1 + c4, warmup discarded, 2 repeats)
#        -> eval subset -> verify JSON -> write markdown table.
# Exits non-zero if any step fails or a required metric is missing.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BENCH="$(cd "$HERE/.." && pwd)"
cd "$BENCH"

MODEL="hf:Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M"
LABEL="smoke-qwen2.5-0.5b-q4_k_m"
NGL="${NGL:-99}"
THREADS="${THREADS:-8}"
PY="${PY:-python3}"
LLAMACPP_DIR="${LLAMACPP_DIR:-runtime/llama-b11316}"
CUDART_DIR="${CUDART_DIR:-}"
OUT_DIR="results/smoke"

while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --label) LABEL="$2"; shift 2 ;;
    --ngl)   NGL="$2"; shift 2 ;;
    --threads) THREADS="$2"; shift 2 ;;
    --llamacpp-dir) LLAMACPP_DIR="$2"; shift 2 ;;
    --cudart-dir)   CUDART_DIR="$2"; shift 2 ;;
    --out-dir)      OUT_DIR="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUT_DIR"

# The llama.cpp CUDA build needs its bundled cudart on LD_LIBRARY_PATH.
if [ -n "$CUDART_DIR" ]; then
  export LD_LIBRARY_PATH="$CUDART_DIR:${LD_LIBRARY_PATH:-}"
  echo "LD_LIBRARY_PATH+= $CUDART_DIR"
fi

# 1. eval set + smoke subset (built from the repo data, hashed in eval/MANIFEST.json)
if [ ! -f eval/m8_eval_v1.jsonl ]; then
  echo "== building frozen eval set =="
  "$PY" -m harness.build_eval_set --out-dir eval --smoke-out eval/smoke_eval.jsonl
fi
[ -f eval/smoke_eval.jsonl ] || "$PY" -m harness.build_eval_set --out-dir eval --smoke-out eval/smoke_eval.jsonl

echo
echo "== perf suite =="
"$PY" -u -m harness.perf \
  --backend llamacpp \
  --model "$MODEL" \
  --label "$LABEL" \
  --llamacpp-dir "$LLAMACPP_DIR" \
  ${CUDART_DIR:+--cudart-dir "$CUDART_DIR"} \
  --ctx 2048 --ngl "$NGL" --threads "$THREADS" --parallel 4 \
  --concurrency 1,4 --repeats 2 --warmup 1 \
  --max-tokens 64 --prompt-tokens 256 \
  --out "$OUT_DIR/perf_${LABEL}.json" \
  --log-dir "$OUT_DIR/logs"

echo
echo "== eval subset (harness re-use check) =="
"$PY" -u -m harness.eval_runner \
  --backend llamacpp \
  --model "$MODEL" \
  --label "$LABEL" \
  --llamacpp-dir "$LLAMACPP_DIR" \
  ${CUDART_DIR:+--cudart-dir "$CUDART_DIR"} \
  --ctx 4096 --ngl "$NGL" --threads "$THREADS" --parallel 1 \
  --eval eval/smoke_eval.jsonl \
  --out "$OUT_DIR/eval_${LABEL}.jsonl" \
  --summary-out "$OUT_DIR/eval_${LABEL}.json" \
  --max-new-tokens 512 --temperature 0.0 --seed 0 \
  --log-dir "$OUT_DIR/logs"

echo
echo "== verify + summarise =="
"$PY" -m harness.verify_results "$OUT_DIR/perf_${LABEL}.json"
"$PY" -m harness.summarize --results-dir "$OUT_DIR" --format md | tee "$OUT_DIR/SUMMARY.md"

echo
echo "SMOKE TEST PASSED  (results in $OUT_DIR)"
