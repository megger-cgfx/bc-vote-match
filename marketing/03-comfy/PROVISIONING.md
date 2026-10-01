# ComfyUI box on vast.ai — provisioning runbook

Repeatable recipe for the BC Vote Match marketing ComfyUI box. Written from the run of
2026-10-01/02 that produced instance **<instance-id>** (RTX 2080 Ti 22GB modded, $0.132/hr),
verified serving `http://localhost:18188/system_stats` → JSON. Every step below was
actually executed on that box in that order.

## TL;DR — one copy-paste

```bash
VASTAI=~/.local/bin/vastai
S=<vast-ssh-helper>

# 1. Find an offer RIGHT BEFORE creating — offer IDs rotate between searches (see mystery §3).
"$VASTAI" search offers 'gpu_name=RTX_2080_Ti num_gpus=1 gpu_ram>=20 verified=true rentable=true dph<=0.20 disk_space>=150' --raw > /tmp/offer_fresh.json
OFFER=$(python3 -c "
import json
d=json.load(open('/tmp/offer_fresh.json'))
d=[o for o in d if o['gpu_ram']>=20000 and o['rentable']]
d.sort(key=lambda o:o['dph_total'])
print(d[0]['id'] if d else '')
")

# 2. Create ONE instance with the full env block (this is what provisions ComfyUI).
"$VASTAI" create instance "$OFFER" \
  --image vastai/comfy:v0.37.0-cuda-13.2-py312 \
  --disk 150 \
  --ssh \
  --label bcvm-marketing \
  --cancel-unavail \
  --env '-p 8188:8188 -p 1111:1111 -p 8080:8080 -p 8288:8288 -p 8384:8384 -e COMFYUI_API_BASE=http://localhost:18188 -e COMFYUI_ARGS="--disable-auto-launch --disable-xformers --port 18188 --enable-cors-header" -e CONTAINER_RUNTIME=gvisor -e DATA_DIRECTORY=/workspace/ -e JUPYTER_DIR=/ -e OPEN_BUTTON_PORT=1111 -e OPEN_BUTTON_TOKEN=1 -e PORTAL_CONFIG="localhost:1111:11111:/:Instance Portal|localhost:8188:18188:/:ComfyUI|localhost:8288:18288:/docs:API Wrapper|localhost:8080:18080:/:Jupyter|localhost:8080:8080:/terminals/1:Jupyter Terminal|localhost:8384:18384:/:Syncthing"'

# 3. SSH key (account key may already be attached — "already associated" is success).
"$VASTAI" attach ssh <NEW_ID> "$(cat ~/.ssh/id_ed25519.pub)"

# 4. Poll until actual_status == running (image pull can take 10-20 min on slow hosts).
"$VASTAI" show instances

# 5. Boot the image services — THE STEP THAT IS EASY TO MISS. vast.ai starts this image
#    with `bash /.launch` (ssh_proxy runtype) as PID 1; the image entrypoint/supervisor
#    do NOT start themselves. Run boot_default.sh with the CONTAINER env (PID 1's
#    environ) — an SSH login shell does NOT inherit the instance env block:
"$S" <NEW_ID> 'nohup bash -c "while IFS= read -r -d \"\" kv; do export \"\$kv\"; done < /proc/1/environ; exec /opt/instance-tools/bin/boot_default.sh" > /tmp/boot.log 2>&1 &'

# 6. Verify INSIDE the box (localhost bypasses the Caddy auth edge):
"$S" <NEW_ID> 'curl -s -m 10 http://localhost:18188/system_stats'
# Must return JSON with system/devices sections. Give it a minute after boot.

# 7. If comfyui is FLAPPING in supervisor with log line
#    "Skipping comfyui startup (not in /etc/portal.yaml)" → /etc/portal.yaml is empty
#    (`applications: {}`) because the boot ran without PORTAL_CONFIG in env. Fix:
"$S" --put <NEW_ID> scripts/fix_portal.sh /tmp/fix_portal.sh   # see script below
"$S" <NEW_ID> 'bash /tmp/fix_portal.sh'

# 8. aria2c (needed for the later model-download task; container-local, lost on re-create):
"$S" <NEW_ID> 'apt-get install -y aria2 && which aria2c'

# 9. Only after step 6 passes: destroy the old box.
echo y | "$VASTAI" destroy instance <OLD_ID>
```

`scripts/fix_portal.sh` (also inline here so this doc is self-contained):

```bash
#!/bin/bash
set -u
while IFS= read -r -d '' kv; do export "$kv"; done < /proc/1/environ   # container env
cd /opt/portal-aio/caddy_manager
/opt/portal-aio/venv/bin/python caddy_config_manager.py   # regenerates /etc/portal.yaml from PORTAL_CONFIG
cat /etc/portal.yaml
supervisorctl restart comfyui
sleep 20
supervisorctl status comfyui
curl -s -m 10 http://localhost:18188/system_stats
```

NEVER run `create instance` in a loop. Create at most one at a time, inspect the result,
destroy any accidental extras immediately.

## The env block — what it does and why

`--image vastai/comfy:v0.37.0-cuda-13.2-py312` alone does NOT provision ComfyUI. The env
block is the difference between the healthy box and the flapping one:

| Variable | Value | Purpose |
|---|---|---|
| `-p 8188:8188` etc. | ports 8188, 1111, 8080, 8288, 8384 | public port mappings (Caddy edge) |
| `COMFYUI_API_BASE` | `http://localhost:18188` | API wrapper points at the internal ComfyUI port |
| `COMFYUI_ARGS` | `--disable-auto-launch --disable-xformers --port 18188 --enable-cors-header` | makes ComfyUI listen on the INTERNAL port 18188 |
| `CONTAINER_RUNTIME` | `gvisor` | runtime (also set by default on some hosts) |
| `DATA_DIRECTORY` | `/workspace/` | workspace root |
| `JUPYTER_DIR` | `/` | Jupyter root |
| `OPEN_BUTTON_PORT` / `OPEN_BUTTON_TOKEN` | `1111` / `1` | portal auth edge (vast.ai may replace the token value) |
| `PORTAL_CONFIG` | long `\|`-separated string | maps external→internal ports: ComfyUI 8188→18188, API wrapper 8288→18288, Jupyter 8080→18080, portal 1111→11111, Syncthing 8384→18384 |

Inside the box you call `http://localhost:18188` directly and bypass Caddy entirely.

Notes:
- The env lands in **PID 1's environ** (`tr '\0' '\n' < /proc/1/environ` on the box). SSH
  sessions do NOT see it. Anything that generates config from it (notably
  `caddy_config_manager.py` → `/etc/portal.yaml`) must be run with PID-1 env loaded.
- vast.ai may drop/adjust entries (it removed our Jupyter 8080 pair from PORTAL_CONFIG and
  replaced OPEN_BUTTON_TOKEN) — harmless; ComfyUI 8188→18188 is what matters.
- Equivalent public template (found via `vastai search templates`): `b69c11b39848cba65226732af68b66bc`
  (ComfyUI on vastai/comfy, same env minus `CONTAINER_RUNTIME`). `--template_hash b69c11b39848cba65226732af68b66bc`
  is a valid alternative to `--env` if the template still exists.

## Price and offer search

- Target: $0.17–0.19/hr; anything 20GB+ VRAM cheaper than that is a win. What we landed:
  **RTX 2080 Ti 22GB (modded, TH host) at $0.1323/hr total** ($0.0907 base + ~$0.0417 disk for 150GB).
- Search syntax notes: `gpu_ram` and `disk_space` are in **GB** in the query. `dph<=0.20` filters
  on total $/hr (incl. storage at the default 5GiB). `verified=true rentable=true` is part of the
  CLI's default query; pass `-n` to see everything.
- The cheapest 20GB+ offers seen (2026-10-02, on-demand):
  - RTX 2080 Ti 22GB (modded, TH hosts) — $0.092/hr base ← what we rented
  - Tesla P40 24GB (TH) — $0.107/hr (Pascal, slow — avoid for SDXL)
  - RTX 3080 20GB — $0.135–0.15/hr
  - RTX 3090 24GB — $0.16–0.18/hr
- `--type bid` (interruptible) prices differ from on-demand; on-demand is what we want for a
  box that must stay up. `--bid_price` creates an interruptible instance — do NOT use for this box.

## Failure modes and fixes (all observed on live boxes)

### A. Services never start at all (no supervisord process)
The instance boots to `bash /.launch` (PID 1) with only sshd + the SSH reverse tunnel. The
image entrypoint (`/opt/instance-tools/bin/entrypoint.sh` → `boot_default.sh`) does not run
on its own with this runtype. `supervisorctl status` says
`unix:///var/run/supervisor.sock no such file`. Fix: step 5 above (boot_default.sh under
PID-1 env).

### B. `comfyui` flapping STARTING↔RUNNING every ~8s, localhost:18188 refuses connections
Diagnosis in order:
1. `supervisorctl status comfyui` — flapping = the `comfyui.sh` wrapper is exiting and restarting.
2. `tail /tmp/boot.log` or supervisor log — look for `Skipping comfyui startup (not in /etc/portal.yaml)`.
3. `cat /etc/portal.yaml` — if it is `applications: {}`, the portal config generator ran
   without `PORTAL_CONFIG` in env. `comfyui.sh` sources
   `/opt/supervisor-scripts/utils/exit_portal.sh`, which greps `/etc/portal.yaml` for
   `ComfyUI`, finds nothing, logs the skip line, and exits 0 (supervisor respawns → the
   flap). Fix: step 7 (`fix_portal.sh`).
4. If instead the wrapper gets past the portal check and still exits: `/opt/supervisor-scripts/comfyui.sh`
   activates `/venv/main`, waits while `/.provisioning` exists, then runs
   `pty python main.py ${COMFYUI_ARGS}` from `${WORKSPACE}/ComfyUI`. Check
   `ls /workspace/ComfyUI` — if missing, run `boot_default.sh` (it provisions the workspace).
5. `caddy FATAL` / `api-wrapper EXITED` / `instance_portal EXITED` are cosmetic when calling
   `localhost:18188` directly.

Other gotchas:
- `python` does not exist on the system PATH; it lives in `/venv/main` (`source /venv/main/bin/activate`).
- `vastai ssh-url <id>` to resolve SSH — never hardcode host/port; they change on restart.
- `vastai destroy instance` prompts `[y/N]` — pipe `echo y |` for non-interactive use.
- The image is self-describing: read `/etc/vast_agents/*.md` (base.md, comfyui.md, pytorch.md),
  `/opt/instance-tools/bin/vast-capabilities` on the box. Note the agent guide is at
  `/etc/vast-agents-guide.md` on some image versions and only under `/etc/vast_agents/` on others.
- `aria2c` is absent on fresh boxes (`apt-get install -y aria2` — container-local,
  lost when the container is recreated; re-check on every fresh box).

## The cheap-2080-Ti mystery — mechanism verified (2026-10-02)

Martin once saw 2080 Ti offers under $0.10/hr that "never reappeared". Verified mechanism —
three compounding effects, measured with repeated `search offers` runs:

1. **The default search query hides them.** `vastai search offers` silently applies
   `rentable=true verified=true` (and `external=false`). Query `gpu_name=RTX_2080_Ti
   num_gpus=1 dph<=0.12`: **4 offers** by default vs **17** with `-n`. The hidden ones
   include 2080 Tis at $0.047–0.08/hr — mostly `rentable=false` and/or `unverified`.
   `rentable=false` does NOT mean rented (`rented=false` on all of them): those hosts are
   simply not accepting new instances (host-side listing toggles), so they stay invisible
   to default searches indefinitely — "never reappeared" for as long as the host keeps
   renting off. That is the primary mechanism.
2. **Offer IDs are not stable — the same machine re-lists under new IDs.** Machine 95392
   (TH, 22GB, $0.0921/hr) came back as ids 50286290 → 50286302 → 50286308 → 50286312 →
   50286321 across ~10 consecutive searches; machine 55752 flipped 51470053 ↔ 51470060;
   machine 33488 showed 47984766 (rentable=false) AND 47984762 (rentable=true)
   simultaneously. A bookmarked offer ID is therefore dead later even when the machine and
   price are still there — search by *query* immediately before create, never reuse a saved ID.
3. **Booking by other renters** removes a machine from the index until released. Real but
   secondary in our measurements: the 22GB-modded pool is only ~2–3 machines at any moment,
   so when one gets grabbed it's simply gone from every search until freed.

Not the mechanism: bid/interruptible pricing (all sub-$0.10 sightings above are plain
on-demand `dph_total`; `is_bid=false` on every row; `--type bid` searches return the same
on-demand ask rows — the interruptible floor is `min_bid`, typically 70–92% of on-demand),
and region (the cheap pool spans TH/CA/US, nothing region-hidden). Not "the search index
lies": the IDs it returns map to real machines; the index is accurate but filtered and
fast-moving.

Practical rule: to catch sub-$0.10 offers, search with `-n`, filter client-side for
`rentable=true verified=true gpu_ram>=20000`, and create immediately from the fresh ID.
