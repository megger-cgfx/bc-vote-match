# `bench/` — reproducible benchmark harness for base-model selection on one RTX 3090

Answers one question with numbers: **which base model should this project serve
from a single 24 GB RTX 3090?** It measures the metrics the selection criteria in
`<task-id>` (m8_candidates.md) are scored on, and it is deliberately
model-agnostic — pass any model id, it does not know or care about the candidate
shortlist.

    bench/
      harness/            # the code (pure stdlib Python 3.11+)
        common.py         # HTTP/SSE client, stats, fingerprints, IO
        vram.py           # nvidia-smi sampler (+ RSS fallback)
        backends.py       # llama.cpp (GGUF) and vLLM (AWQ/GPTQ) adapters
        perf.py           # performance runner  -> machine-readable JSON
        eval_runner.py    # eval-set runner     -> raw generations (JSONL)
        build_eval_set.py # builds M8-Coding-Eval v1 + MANIFEST.json
        verify_results.py # asserts every required metric is present
        summarize.py      # results -> human-readable table
      scripts/
        setup_llamacpp.sh # fetch + pin the runtime
        run_smoke.sh      # end-to-end smoke test
        run_on_3090.sh    # sync to the rented 3090 over SSH, run, pull results
      VERSIONS.json       # pinned runtime versions + hardware assumptions
      requirements.txt    # (empty by design: stdlib core)
      eval/               # frozen eval set + manifest (versioned)
      models/ runtime/ results/   # local state, gitignored

## Pinned versions

See `VERSIONS.json` for the full record. Summary:

| Component | Pin | Notes |
|---|---|---|
| llama.cpp | `b11316` (upstream tag, 2026-10-01), `version: 0.5.0-dev (build 11316, commit 2232bc8b5)` | prebuilt, no compilation |
| llama.cpp build | `llama-b11316-bin-ubuntu-cuda-12.8-x64` + `cudart-llama-b11316-bin-ubuntu-cuda-12.8-x64` | CUDA runtime bundled, sm_86 covered |
| vLLM | `0.30.0` | supported, **not exercised** in this run (see Limitations) |
| Python | 3.11+ (harness is stdlib-only) | no pip install needed for the core |

Host the numbers were taken on: vast.ai instance `<instance-id>` — 1× RTX 3090
(24 576 MiB, compute capability 8.6, driver 595.84), Ubuntu 24.04, CUDA 13.2
toolkit present, 64 vCPU, 6.9 GB disk used.

Create the runtime on any box:

    bench/scripts/setup_llamacpp.sh --variant cuda-12.8   # GPU box
    bench/scripts/setup_llamacpp.sh --variant cpu         # no-GPU box

## Quick start

    cd bench
    python -m harness.perf --backend llamacpp \
        --model hf:Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M \
        --label qwen2.5-0.5b-q4_k_m \
        --ngl 99 --ctx 4096 --parallel 4 \
        --concurrency 1,4 --repeats 3 --warmup 1 \
        --out results/qwen2.5-0.5b-q4_k_m.json
    python -m harness.summarize results/*.json

`--model` accepts a local `.gguf` path or `hf:<repo>[:<quant>]` (llama.cpp
downloads and caches it). For vLLM it is an HF repo id or a local model dir.

Smoke test — proves the whole chain works on the machine it runs on:

    bench/scripts/run_smoke.sh                 # tiny model, CUDA if present
    bench/scripts/run_smoke.sh --ngl 0         # force CPU

On the 3090 (from this WSL box, which has no GPU of its own):

    bench/scripts/run_on_3090.sh 'bash scripts/run_smoke.sh --ngl 99'

## What is measured, and how

Definitions matter more than numbers here, so they are explicit:

| Metric | Definition | How |
|---|---|---|
| `server.load_time_s` | process spawn → `/health` returns 200 | wall clock around `Popen` + readiness poll |
| `peak_vram_mb` | max `memory.used` seen by `nvidia-smi` during the session | background thread, default 100 ms interval |
| `peak_vram_delta_mb` | `peak_vram_mb` − pre-load baseline | same sampler |
| `ttft_s` | request sent → first streamed content token | SSE timestamps, per request |
| `prefill_tps` | `prompt_tokens / ttft_s` | effective prompt-processing rate; the SSE stream starts at the first generated token, so this includes one decode step (server-side `timings.prompt_per_second` is also recorded when the runtime reports it) |
| `decode_tps` (per stream) | `(completion_tokens − 1) / (t_last − t_first)` | SSE timestamps |
| `aggregate_decode_tps` @ concurrency N | `Σ completion_tokens / wall_s` for the whole batch | N simultaneous requests, released from a barrier |
| `throughput c1 / c4` | the two concurrency levels the selection criteria name | `--concurrency 1,4` |

Rules baked in:

- **Warmup is discarded.** One warmup request runs before measurement and is
  tagged `warmup: true`; `summary` is computed from non-warmup batches only.
- **Every reported number is mean ± stddev over ≥ 2 repeats** (`stddev` is
  `null` when n < 2, and `verify_results.py` fails a run whose c1/c4 summary has
  fewer than 2 repeats). The acceptance rule "no metric from a single sample" is
  enforced, not documented.
- **Determinism:** `temperature=0`, fixed `--seed`, `cache_prompt=false`, and a
  per-request nonce so no request can be answered from another's prompt cache.
- **Concurrency is real:** N threads released from a `threading.Barrier`; the
  server is started with `-np ≥ max(concurrency)` so the batch actually batches.
- **Failures are recorded, never dropped:** per-request errors land in
  `batches[].per_request[].error`, batch errors in `errors`, and OOM/abort shows
  up as a non-`ok` `status` with the server log kept next to the result.

## Output

`perf.py` writes one JSON document per model (`results/<label>.json`) plus a
human-readable table via `summarize.py`. Shape:

    schema_version, kind="perf", label, model, config, environment, gpu,
    server{command, load_time_s, runtime_version, ...},
    baseline_vram_mb, peak_vram_mb, peak_vram_delta_mb,
    batches[ {concurrency, warmup, repeat, wall_s, aggregate_decode_tps,
              total_completion_tokens, mean_ttft_s, mean_decode_tps,
              mean_prefill_tps, per_request[...], errors[]} ],
    summary[ {concurrency, repeats, aggregate_decode_tps{mean,stddev,n}, ...} ],
    vram{supported, samples, peak_vram_mb, ...}, status, errors

`eval_runner.py` writes `results/<label>_eval.jsonl` (one row per item: raw
output, timings, error) plus a summary JSON. It is a separate runner on purpose:
quality scoring reuses the same serving stack but is a different program, so a
scoring change can never invalidate a perf number and vice versa.

`verify_results.py` is the acceptance gate:

    python -m harness.verify_results results/smoke/perf_*.json

## The frozen eval set

`harness/build_eval_set.py` builds `M8-Coding-Eval v1` from repository files only,
per m8_candidates.md §4.2, and writes `eval/MANIFEST.json` (§4.5) with the git
rev, the sha256 of `freeze-proposal.json`, of each `data/codings/<party>.json`
used, of each source file used, and of the emitted JSONL:

    python -m harness.build_eval_set --out-dir eval --smoke-out eval/smoke_eval.jsonl

Result: **148 items** — 90 Part A (5 parties × 18 frozen questions) and 58 Part B
null controls (cpb 17, centrebc 25, onebc 11, ndp 3, green 2). 25 Part A items are
emitted `status: "skipped"` because the reference row has no source file: 22 are
pairs where both coders coded `null` (so there is no source text to show the
model) and 3 involve `centrebc-0053`/`centrebc-0056`, which are cited in
`data/codings/centrebc.json` but absent from `data/raw/centrebc/`. §4.2 says not to
substitute another file, so they are skipped and counted, not silently dropped.

    current run: ok=123, skipped=25, part_a=90, part_b=58

## Known limitations — read before quoting a number

1. **This worker host has no GPU.** No `nvidia-smi`, no `/dev/nvidia*`, no WSL GPU
   passthrough. Any `peak_vram_mb` produced here is `null` with
   `vram.supported: false` and a reason string, and `verify_results.py` fails the
   run rather than reporting a fake number. GPU numbers come from the rented 3090
   via `scripts/run_on_3090.sh`.
2. **vLLM arms are unverified.** The adapter exists and is pinned (`0.30.0`), but
   no AWQ/GPTQ model has been served through it yet on this box. Treat any vLLM
   result as needing a first-run sanity check.
3. **Part B source policy is a harness decision, not a spec decision.** m8_candidates.md
   §4.2 says the input text comes from the row's `source_id` — but all 58 null rows
   carry `source_id: null`, so that rule is unimplementable as written. The builder
   therefore exposes `--null-source-policy {corpus,paired,skip}` (default `corpus`:
   the party's own source files concatenated to the same 12 000-character cap,
   which is the null-control's actual question — "given this party's material, is
   there a stated position?"). Every Part B item records which policy produced it.
   **If the quality metric is to be comparable across models this choice must be
   ratified, and any change bumps the set to v2.**
4. **Part A reference labels are noisy.** They come from the `v0.9-prefreeze`
   agent codings (coder A, falling back to coder B where A is null), and 14 of the
   90 pairs are coder disagreements. Each item carries `reference_codes_all` and
   `coder_agreement`, so K1 can be reported on the unanimous subset too. Do not
   present full-set K1 as ground truth.
5. **A shared GPU distorts VRAM.** On the 3090 as rented, ~7 GB is held by other
   services, so `peak_vram_mb` is device-wide. `peak_vram_delta_mb` (vs the
   pre-load baseline) is the figure to compare; `devices` in the result records
   `memory.total`/`memory.used` at capture time. For comparable absolute numbers,
   stop other GPU tenants first.
