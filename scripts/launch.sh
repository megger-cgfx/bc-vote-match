#!/usr/bin/env bash
# launch.sh — the M5 launch command. See `bash scripts/launch.sh --help`.
#
# One command, from repo to published site:
#
#     bash scripts/launch.sh                 # verify + build + package, stop short of publishing
#     bash scripts/launch.sh --publish       # ... and publish (asks you to confirm)
#     bash scripts/launch.sh --check         # verify the existing out/ only
#     bash scripts/launch.sh --verify-live https://bcvotematch.ca
#
# The logic lives in scripts/launch.py; this file only finds a Python 3 and
# hands over, so the entry point stays the one command people expect.
#
# Exit codes: 0 GO/done · 1 NO-GO (gate failed) · 2 GO but a human step is
# needed (confirm or credentials) · 3 could not run · 4 deploy failed ·
# 5 deployed but the live site does not match the artifact.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

py=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    py="$candidate"
    break
  fi
done
if [ -z "$py" ]; then
  echo "launch: python3 is required and was not found on PATH" >&2
  exit 3
fi

exec "$py" "$here/launch.py" "$@"
