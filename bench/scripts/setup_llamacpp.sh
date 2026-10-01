#!/usr/bin/env bash
# Fetch and pin the llama.cpp runtime used by the harness.
#
#   scripts/setup_llamacpp.sh --variant cuda-12.8      # RTX 3090 (Ampere, sm_86)
#   scripts/setup_llamacpp.sh --variant cpu            # CPU-only fallback / CI
#
# Downloads the *prebuilt* release binaries (no compilation) for the pinned tag,
# plus the bundled CUDA runtime when the variant needs it. Idempotent: re-running
# with the files present is a no-op unless --force is given.
set -euo pipefail

TAG="${LLAMACPP_TAG:-b11316}"          # pinned in VERSIONS.json
VARIANT="cuda-12.8"
RUNTIME_DIR="$(cd "$(dirname "$0")/.." && pwd)/runtime"
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --variant)   VARIANT="$2"; shift 2 ;;
    --tag)       TAG="$2"; shift 2 ;;
    --dir)       RUNTIME_DIR="$2"; shift 2 ;;
    --force)     FORCE=1; shift ;;
    -h|--help)   sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

case "$VARIANT" in
  cuda-12.8) ASSET="llama-${TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz";   CUDART="cudart-llama-${TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz" ;;
  cuda-13.4) ASSET="llama-${TAG}-bin-ubuntu-cuda-13.4-x64.tar.gz";   CUDART="cudart-llama-${TAG}-bin-ubuntu-cuda-13.4-x64.tar.gz" ;;
  cpu)       ASSET="llama-${TAG}-bin-ubuntu-x64.tar.gz";             CUDART="" ;;
  *) echo "unknown variant: $VARIANT (cuda-12.8|cuda-13.4|cpu)" >&2; exit 2 ;;
esac

BASE="https://github.com/ggml-org/llama.cpp/releases/download/${TAG}"
mkdir -p "$RUNTIME_DIR"
cd "$RUNTIME_DIR"

fetch() {
  local name="$1"
  if [ -f "$name" ] && [ "$FORCE" -eq 0 ]; then
    echo "present: $name"
    return
  fi
  echo "downloading $name"
  curl -fL --retry 3 --retry-delay 5 -o "$name" "${BASE}/${name}"
}

# ---- verify the files (sha256) BEFORE consuming them ------------------------ #
# The release index carries no per-asset hashes, so we record what we got in
# runtime/<tag>/SHA256SUMS and verify on every later run. A mismatch is fatal.
VERIFY_DIR="$RUNTIME_DIR/llama-${TAG}"
mkdir -p "$VERIFY_DIR"
SUMS="$VERIFY_DIR/SHA256SUMS"

check_or_record() {
  local name="$1"
  local sum
  sum="$(sha256sum "$name" | awk '{print $1}')"
  if [ -f "$SUMS" ] && grep -q " $name\$" "$SUMS"; then
    local want
    want="$(grep " $name\$" "$SUMS" | awk '{print $1}')"
    if [ "$want" != "$sum" ]; then
      echo "SHA256 MISMATCH for $name: expected $want, got $sum" >&2
      exit 3
    fi
    echo "verified: $name"
  else
    echo "$sum  $name" >> "$SUMS"
    echo "recorded: $name ($sum)"
  fi
}

[ -n "$CUDART" ] && fetch "$CUDART"
fetch "$ASSET"
[ -n "$CUDART" ] && check_or_record "$CUDART"
check_or_record "$ASSET"

echo "extracting..."
tar xzf "$ASSET"
[ -n "$CUDART" ] && tar xzf "$CUDART"

echo
echo "runtime dir : $VERIFY_DIR"
echo "cudart dir  : $VERIFY_DIR/cudart-llama-${TAG}-bin-ubuntu-${VARIANT}-x64"
echo
echo "smoke check:"
LD_LIBRARY_PATH="$VERIFY_DIR/cudart-llama-${TAG}-bin-ubuntu-${VARIANT}-x64:${LD_LIBRARY_PATH:-}" \
  "$VERIFY_DIR/llama-server" --list-devices
