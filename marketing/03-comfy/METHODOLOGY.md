# ComfyUI headless pipeline — methodology (PROVEN)

Status: **the pipeline was proven end to end on 2026-10-01** on vast.ai instance
**53740912** (RTX 2080 Ti, 22.5 GB VRAM, $0.1323/hr — see the provisioning notes). The
original draft targeted instance <instance-id>, which no longer exists; the reachability
details below were re-verified against 53740912. Proof run: prompt_id
`7b8b0aa5-266d-4dd9-9070-ab63d25403da`, FLUX.1-schnell fp8, 4 steps, 1216x576 ->
`marketing/assets/comfy-raw/pipeline-proof.png` (sha256
`1a23239753dacab153ecf2072329c0abb71a9c1b932af2e49a234d2c7031255a`). The image is a
coherent, photographic-style render of the prompt (misty PNW dawn coastline, rocky
shore, small evergreen islet) — inspected visually, not just size-checked. Measured
numbers are in `methodology.json` and section 5.

## 1. Reaching ComfyUI

- Resolve the SSH endpoint with `vastai ssh-url <instance-id>` (authoritative), or use the
  helper `<vast-ssh-helper> <instance-id> '<cmd>'`.
  Never hand-build host/port; they change when the instance is recreated.
- ComfyUI listens on **internal** port `18188` inside the box. From an SSH session use
  `http://localhost:18188` directly. This bypasses the Caddy auth edge on the public
  ports, which we do not use. An API wrapper sits on internal `18288` (docs at `/docs`);
  we drive ComfyUI's own API and ignore the wrapper.
- Box layout (verified on 53740912, 2026-10-02): ComfyUI at `/workspace/ComfyUI`,
  outputs in `/workspace/ComfyUI/output`, python env `/venv/main`. ComfyUI runs under
  supervisor (`supervisorctl restart comfyui`), serving on internal 18188.

## 2. API call shapes

- Submit: `POST http://localhost:18188/prompt` with JSON `{"prompt": <class_type graph>}`.
  Returns `{"prompt_id": "..."}` on success or an error object.
- Poll: `GET http://localhost:18188/history/<prompt_id>`. When the job finishes, the
  response contains `outputs.<node_id>.images[]` with `{filename, subfolder, type}` for
  the `SaveImage` node.
- Queue gate: `GET http://localhost:18188/queue`. `queue_running` and `queue_pending`
  must both be empty before we submit.
- `example-workflow-flux.json` is the proven graph (used for the proof run):
  CheckpointLoaderSimple(`flux1-schnell-fp8.safetensors`) ->
  CLIPTextEncode(+) / CLIPTextEncode(-) -> KSampler -> VAEDecode -> SaveImage, with
  EmptySD3LatentImage 1216x576. FLUX.1-schnell settings: 4 steps, cfg 1.0, sampler
  `euler`, scheduler `simple`, seed 20261002. All API shapes above are verified
  end to end by prompt_id `7b8b0aa5-266d-4dd9-9070-ab63d25403da`.
- `example-workflow.json` is the earlier minimal SDXL-Turbo graph (3 steps, cfg 1.2,
  `euler_ancestral`/`normal`, 512x512) — kept as the low-VRAM fallback template; not
  itself run (the FLUX run supersedes it as proof).

## 3. Where outputs land and how to get them here

- Output PNG: `/workspace/ComfyUI/output/<filename from history>.png`.
- Copy back: `scp -P <port> root@<host>:/workspace/ComfyUI/output/<file> <local>` using the
  same host/port from `vastai ssh-url`. `comfy_run.py` does exactly this and validates the
  PNG magic bytes plus real IHDR width/height after the copy.

## 4. Lock protocol and failure modes

Cross-agent concurrency on a single GPU/queue. Implemented in `comfy_run.py`:

1. **acquire**: `mkdir -p /workspace/locks` once, then `mkdir /workspace/locks/comfy.lock`.
   `mkdir` is atomic: a non-zero exit means another agent holds it. Retry with ~10 s
   backoff up to `--lock-timeout` (default 900 s), then exit non-zero.
2. **holder file**: on acquire, write `holder` inside the lock dir with pid, hostname and
   an ISO timestamp, so a human can see who is inside.
3. **queue gate**: before `POST /prompt`, poll `GET /queue` until `queue_running` and
   `queue_pending` are both empty (also bounded by the lock timeout).
4. **release**: `rm holder; rmdir /workspace/locks/comfy.lock` in a `finally` block, so a
   crash or timeout does not wedge the lock. `rmdir` only removes an empty dir, so it
   cannot clobber a newer holder's files.
5. **stale safety**: if the lock dir's mtime is older than 20 minutes, log
   "stale lock taken over" and take it (`rm -rf` + `mkdir`). Failure modes:
   - Two agents take a stale lock simultaneously -> last `mkdir` wins the retry loop;
     the loser sees `HELD` and backs off again. Window is one `mkdir` race, mitigated by
     the fact that each agent re-checks `/queue` before submitting.
   - Crash between acquire and finally -> lock survives until the 20-minute stale timer.
   - Clock skew between agents is irrelevant: staleness is measured with the box's own
     `stat -c %Y` and `date +%s`, both run on the box.
   - `rmdir` fails if a holder file exists from a crashed run -> we `rm -f holder` first.

## 5. Measured cost of a job (PROVEN — FLUX.1-schnell fp8, 1216x576, 4 steps)

Real numbers from the proof run on the RTX 2080 Ti (22.5 GB VRAM), 2026-10-01:

| Metric | Value | How measured |
|---|---|---|
| wall clock (end to end) | **75.9 s** | `comfy_run.py` timer: lock + queue gate + submit + 5s-granularity history polling + scp + PNG validation |
| ComfyUI job time | **25.3 s** | `execution_start` -> `execution_success` timestamps in `/history/<prompt_id>` (includes checkpoint load, 4 sampling steps, VAE decode, save) |
| VRAM peak | **19,074 MB** | `nvidia-smi memory.used` sampled every ~1.2 s on the box across the job (123 samples), max |
| VRAM baseline (idle) | 166 MB | pre-job snapshot |
| GPU-seconds | not exposed | ComfyUI does not report per-node GPU time in /history |

Notes:
- fp8 FLUX.1-schnell is a ~17.24 GB checkpoint on a 22.5 GB card: ~19.1 GB peak at
  1216x576, so ~3.4 GB headroom. It fits **without** `--lowvram`; no GPU/memory fix was
  needed for the proof run. Do not batch or run parallel jobs on this card.
- `comfy_run.py`'s built-in sparse sampler reported 5,252 MB (it snapshots once per
  outer loop, catching mid-load). The independent 1 s sampler is the number to trust;
  a dense sampler is the right methodology for any future measurement.
- The first job of a session pays the checkpoint load inside that 25.3 s; expect later
  jobs in the same lock hold to be faster (weights stay resident).

## 6. Production batch guidance (22.5 GB card — FLUX.1-schnell fp8 primary)

Measured against the proof run (see section 5); the SDXL-Turbo figures in the original
draft were replaced where the FLUX run supersedes them:

- FLUX.1-schnell fp8 weights are ~17.24 GB; measured ~19.1 GB resident peak at
  1216x576. That leaves ~3.4 GB headroom — batch_size 1 only, one job at a time
  through the lock. SDXL 1.0 base (6.94 GB) is the low-VRAM fallback and first choice
  for square illustration work with the flat-illustration LoRA.
- Resolution: 1216x576 landscape plates proven; treat anything larger as needing a
  fresh measurement before committing a batch.
- Prompt batching: one KSampler per prompt seed set, sequential submission through the
  lock (never parallel `/prompt` posts). Queue 10–30 prompts per lock hold to amortise
  checkpoint load; the first job pays model load (part of the measured 25.3 s), later
  jobs with weights resident should be faster — measure before promising numbers.
- FLUX.1-schnell: 4 steps, cfg 1.0, `euler`/`simple` (more steps buy nothing).
  SDXL base: 25 steps, cfg 7, `dpmpp_2m`/`karras`. Chroma trio: 26 steps, cfg 3.5,
  `euler`/`beta`, shift 1 (per the official template in DOWNLOADS.md).

## 7. Reproducing the proof run (proven on 2026-10-01)

    S=<vast-ssh-helper>
    "$S" 53740912 'curl -s http://localhost:18188/system_stats'
    python3 marketing/03-comfy/comfy_run.py \
        --workflow marketing/03-comfy/example-workflow-flux.json \
        --instance <instance-id> \
        --out marketing/assets/comfy-raw/pipeline-proof.png

Recorded output of the proof run: `{"prompt_id": "7b8b0aa5-266d-4dd9-9070-ab63d25403da",
"wall_clock_s": 75.9, "vram_peak_mb": 5252, "vram_baseline_mb": 166, "width": 1216,
"height": 576}` (the 5252 is the sparse in-script sample; the dense-sampler peak is
19,074 MB). `comfy_run.py` needed three small fixes before it could run (see
`comfy_run_fixes` in `methodology.json`): instance resolution, and two
Python `%-format` escaping bugs in the lock code. The manifest row for the proof image
is the `pipeline-proof.png` line in `marketing/assets/MANIFEST.jsonl`.

## 8. Model downloads (recommended set — COMPLETE)

All seven DOWNLOADS.md files are on disk and size-verified (39,383,980,331 bytes total,
matching the documented expected sizes): flux1-schnell-fp8 17.236 GB, sd_xl_base_1.0
6.938 GB, Chroma1-HD-fp8mixed 9.193 GB, t5xxl_fp8_e4m3fn_scaled 5.157 GB,
flat-illustration LoRA 0.457 GB, RealESRGAN_x4plus 0.067 GB, ae.safetensors 0.335 GB.
Fetching used the sequential `/tmp/fetch_models.sh` (aria2c `-x8 -s8 -c`) left by the
interrupted previous worker; racing duplicate transfers were killed and their partials
resumed from the `.aria2` control files, so nothing was re-downloaded. `ckpt/` is a
symlink of `checkpoints/` on this image — do not double-count sizes.