#!/usr/bin/env bash
# Drive the harness on the rented RTX 3090 over SSH.
#
#   scripts/run_on_3090.sh 'bash scripts/run_smoke.sh --ngl 99'
#   scripts/run_on_3090.sh --pull-only
#
# What it does:
#   1. resolves the instance's ssh endpoint with the vastai CLI
#   2. tars bench/ (code only: no models/, runtime/, results/) into the remote dir
#   3. runs the given command on the instance
#   4. copies results/ back into the local bench/
#
# The instance is a shared, long-lived box: the script never installs anything and
# never touches supervisor-managed services. Freeing VRAM for full-size runs is a
# deliberate act:  ssh ... 'supervisorctl stop comfyui'  (see README).
set -euo pipefail

INSTANCE="${VINSTANCE:-<instance-id>}"
REMOTE_DIR="${REMOTE_DIR:-/workspace/bench}"
KEY="${VAST_SSH_KEY:-$HOME/.ssh/id_ed25519}"
PULL_ONLY=0
export PATH="$HOME/.local/bin:$PATH"

while [ $# -gt 0 ]; do
  case "$1" in
    --instance) INSTANCE="$2"; shift 2 ;;
    --remote-dir) REMOTE_DIR="$2"; shift 2 ;;
    --pull-only) PULL_ONLY=1; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) break ;;
  esac
done
CMD="${*:-bash scripts/run_smoke.sh}"

HERE="$(cd "$(dirname "$0")" && pwd)"
BENCH="$(cd "$HERE/.." && pwd)"
cd "$BENCH"

URL="$(vastai ssh-url "$INSTANCE")"          # ssh://root@HOST:PORT
HOSTPORT="${URL#ssh://root@}"
HOST="${HOSTPORT%%:*}"
PORT="${HOSTPORT##*:}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -p "$PORT" "root@$HOST")

echo "instance $INSTANCE -> $HOST:$PORT  (remote dir $REMOTE_DIR)"

if [ "$PULL_ONLY" -eq 0 ]; then
  echo "== syncing code =="
  "${SSH[@]}" "mkdir -p '$REMOTE_DIR'"
  tar czf - \
    --exclude='__pycache__' --exclude='*.pyc' \
    harness scripts eval requirements.txt VERSIONS.json README.md .gitignore \
    | "${SSH[@]}" "tar xzf - -C '$REMOTE_DIR'"

  echo "== running on the 3090 =="
  set +e
  "${SSH[@]}" "cd '$REMOTE_DIR' && $CMD"
  rc=$?
  set -e
  echo "remote exit code: $rc"
else
  rc=0
fi

echo "== pulling results =="
mkdir -p results
"${SSH[@]}" "cd '$REMOTE_DIR' && tar czf - results 2>/dev/null || true" | tar xzf - -C . 2>/dev/null || true
echo "results in $(pwd)/results"
exit "$rc"
