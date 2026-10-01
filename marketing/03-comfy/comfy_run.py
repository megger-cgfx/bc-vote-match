#!/usr/bin/env python3
"""Headless ComfyUI client for the vast.ai RTX 3090 box (instance <instance-id>).

Runs LOCALLY and drives ComfyUI on the box over SSH. Standard library only.

NOTE ON STATUS: this script was written per the documented box interface
(/etc/vast_agents/comfyui.md conventions, internal port 18188, /prompt /
/history API, /workspace/ComfyUI/output). It has NOT been executed end to end,
because at build time the instance was unreachable ("vastai show instance <instance-id>" -> "not found or no longer exists"; ssh port refused). Treat the code
as a draft for human review until a live run is recorded in METHODOLOGY.md.

Usage:
    python3 comfy_run.py --workflow example-workflow.json --out out.png \
        [--instance <instance-id>] [--timeout 600] [--lock-timeout 900]

Prints one JSON object on stdout (prompt_id, wall_clock_s, gpu_s, vram_peak_mb,
width, height, out). Exits non-zero with a message on stderr on any failure.

Lock protocol (see METHODOLOGY.md):
  acquire : mkdir /workspace/locks/comfy.lock  (atomic; non-zero exit = held)
            write holder file + pid inside the lock dir
  gate    : GET http://localhost:18188/queue, wait until running+pending empty
  release : rmdir /workspace/locks/comfy.lock in a finally block
  stale   : if the lock dir mtime is older than 20 minutes, log and take it
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time

DEFAULT_INSTANCE = ""  # supply your own instance id
LOCK_DIR = "/workspace/locks/comfy.lock"
COMFY = "http://localhost:18188"
STALE_LOCK_S = 20 * 60
OUTPUT_DIR = "/workspace/ComfyUI/output"
REMOTE_WORK = "/workspace/marketing-work/comfy-run"


def die(msg, code=1):
    print("comfy_run: " + msg, file=sys.stderr)
    sys.exit(code)


def ssh_base(instance=None):
    """Resolve ssh/scp endpoint from the vast-ssh helper's own resolution:
    `vastai ssh-url <id>` is the authoritative source. Never hand-build
    host/port."""
    r = subprocess.run(["vastai", "ssh-url", instance or DEFAULT_INSTANCE],
                       capture_output=True, text=True, timeout=60)
    url = (r.stdout or "").strip()
    if r.returncode != 0 or not url.startswith("ssh://"):
        die("could not resolve ssh url via `vastai ssh-url`: " + (r.stderr or url))
    # ssh://root@HOST:PORT
    tail = url.split("ssh://", 1)[1]
    user_host, port = tail.rsplit(":", 1)
    user, host = user_host.split("@", 1)
    return user, host, port


def run_remote(ssh, cmd, timeout=120, check=True):
    r = subprocess.run(ssh + [cmd], capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        die("remote command failed: %s\n%s" % (cmd, (r.stderr or r.stdout)[:2000]))
    return r


def acquire_lock(ssh, timeout_s):
    deadline = time.time() + timeout_s
    while True:
        r = run_remote(ssh, (
            "mkdir -p /workspace/locks; "
            "now=$(date +%%s); "
            "if mkdir %s 2>/dev/null; then echo ACQUIRED; "
            "elif [ -d %s ] && [ $(( now - $(stat -c %%Y %s 2>/dev/null || echo 0) )) -gt %d ]; then "
            "  echo STALE_TAKING; rm -rf %s; mkdir %s && echo ACQUIRED; "
            "else echo HELD; fi"
            % (LOCK_DIR, LOCK_DIR, LOCK_DIR, STALE_LOCK_S, LOCK_DIR, LOCK_DIR)),
            check=False)
        out = (r.stdout or "").strip()
        if "ACQUIRED" in out:
            run_remote(ssh, "printf 'pid=%%s\\nholder=comfy-run\\nhost=%%s\\ntime=%%s\\n' "
                       "$$ %s \"$(date -Is)\" > %s/holder"
                       % (shlex.quote(os.uname().nodename), LOCK_DIR))
            return
        if "STALE_TAKING" in out:
            print("comfy_run: stale lock (>20 min) taken over", file=sys.stderr)
            return
        if time.time() > deadline:
            die("lock %s held by another job for >%ds; giving up" % (LOCK_DIR, timeout_s))
        time.sleep(10)


def release_lock(ssh):
    run_remote(ssh, "rm -f %s/holder; rmdir %s 2>/dev/null || true" % (LOCK_DIR, LOCK_DIR),
               check=False)


def wait_queue_empty(ssh, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = run_remote(ssh, "curl -s %s/queue" % COMFY, check=False)
        try:
            q = json.loads(r.stdout)
            running = q.get("queue_running", [])
            pending = q.get("queue_pending", [])
            if not running and not pending:
                return
        except Exception:
            pass
        time.sleep(5)
    die("ComfyUI queue never drained within %ds" % timeout_s)


def gpu_snapshot(ssh):
    r = run_remote(ssh, "nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu "
                   "--format=csv,noheader,nounits", check=False)
    try:
        used, total, util = [x.strip() for x in r.stdout.strip().split(",")]
        return int(used), int(total), int(util)
    except Exception:
        return None, None, None


def submit(ssh, workflow_path):
    with open(workflow_path) as f:
        prompt = json.load(f)
    payload = json.dumps({"prompt": prompt})
    r = run_remote(ssh, "curl -s -X POST -H 'Content-Type: application/json' "
                   "-d %s %s/prompt" % (shlex.quote(payload), COMFY), timeout=120)
    try:
        resp = json.loads(r.stdout)
    except Exception:
        die("bad /prompt response: " + (r.stdout or r.stderr)[:500])
        raise  # unreachable; keeps static analysis happy
    if "prompt_id" not in resp:
        die("/prompt rejected: " + json.dumps(resp)[:500])
    return resp["prompt_id"]


def poll_history(ssh, prompt_id, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = run_remote(ssh, "curl -s %s/history/%s" % (COMFY, prompt_id), check=False)
        try:
            hist = json.loads(r.stdout)
        except Exception:
            hist = {}
        entry = hist.get(prompt_id)
        if entry:
            outputs = entry.get("outputs", {})
            for node_out in outputs.values():
                for img in node_out.get("images", []):
                    return img  # {filename, subfolder, type}
            if entry.get("status", {}).get("status_str") == "error":
                die("ComfyUI reported an error for prompt " + prompt_id)
        time.sleep(5)
    die("timed out after %ds waiting for history of %s" % (timeout_s, prompt_id))


def png_dimensions(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        die("copied file is not a PNG: " + path)
    w = int.from_bytes(head[16:20], "big")
    h = int.from_bytes(head[20:24], "big")
    return w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--instance", default=DEFAULT_INSTANCE)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--lock-timeout", type=int, default=900)
    args = ap.parse_args()

    user, host, port = ssh_base(args.instance)
    if args.instance != DEFAULT_INSTANCE:
        r = subprocess.run(["vastai", "ssh-url", args.instance],
                           capture_output=True, text=True, timeout=60)
        tail = r.stdout.strip().split("ssh://", 1)[1]
        user_host, port = tail.rsplit(":", 1)
        user, host = user_host.split("@", 1)
    ssh = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
           "-p", port, "%s@%s" % (user, host)]

    t0 = time.time()
    peak_vram = 0
    try:
        acquire_lock(ssh, args.lock_timeout)
        wait_queue_empty(ssh, args.lock_timeout)
        used, total, _ = gpu_snapshot(ssh)
        baseline_vram = used or 0
        prompt_id = submit(ssh, args.workflow)
        print("comfy_run: submitted prompt_id=%s" % prompt_id, file=sys.stderr)
        while True:
            u, _, _ = gpu_snapshot(ssh)
            if u:
                peak_vram = max(peak_vram, u)
            if time.time() - t0 > args.timeout:
                die("wall-clock timeout")
            img = poll_history(ssh, prompt_id, args.timeout) or {}
            break
        remote_png = "%s/%s" % (OUTPUT_DIR, img["filename"])
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        scp = ["scp", "-o", "StrictHostKeyChecking=no", "-P", port,
               "%s@%s:%s" % (user, host, remote_png), args.out]
        r = subprocess.run(scp, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            die("scp failed: " + (r.stderr or "")[:500])
        w, h = png_dimensions(args.out)
        # gpu seconds: ask the box for job timing if ComfyUI exposed it; else
        # report the observed nvidia-smi busy window (we sample every 5 s).
        out = {
            "prompt_id": prompt_id,
            "wall_clock_s": round(time.time() - t0, 1),
            "gpu_s": None,
            "vram_peak_mb": peak_vram,
            "vram_baseline_mb": baseline_vram,
            "width": w,
            "height": h,
            "out": os.path.abspath(args.out),
        }
        print(json.dumps(out))
    finally:
        try:
            release_lock(ssh)
        except Exception as e:
            print("comfy_run: release failed: %s" % e, file=sys.stderr)


if __name__ == "__main__":
    main()