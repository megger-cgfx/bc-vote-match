#!/usr/bin/env bash
# deploy-pages.sh — the single deploy command: static export -> Cloudflare Pages.
#
#   build command : npm run build            (Next.js static export)
#   output dir    : out/
#   deploy command: bash scripts/deploy-pages.sh
#
# Direct upload via wrangler; no wrangler.toml and no secrets in this repo.
# Credentials come from the environment AT DEPLOY TIME and are never committed:
#   CLOUDFLARE_API_TOKEN   API token scoped to Account / Cloudflare Pages: Edit
#                          (create at dash.cloudflare.com/profile/api-tokens;
#                          keep it in the operator secret store, see
#                          docs/05-LAUNCH.md)
#   CLOUDFLARE_ACCOUNT_ID  the Cloudflare account id
#
# The launch preflight gate must pass before anything is uploaded. Set
# BCVM_SKIP_PREFLIGHT=1 only to re-upload a build that a previous gate run
# already judged GO. Optional overrides: BCVM_PAGES_PROJECT, BCVM_PAGES_BRANCH.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/out}"
PROJECT="${BCVM_PAGES_PROJECT:-bc-vote-match}"
BRANCH="${BCVM_PAGES_BRANCH:-main}"

: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is not set — export the Cloudflare API token at deploy time (docs/05-LAUNCH.md); it is never stored in git}"
: "${CLOUDFLARE_ACCOUNT_ID:?CLOUDFLARE_ACCOUNT_ID is not set — export the Cloudflare account id at deploy time}"

if [ ! -f "$OUT/index.html" ]; then
  echo "deploy-pages: $OUT/index.html is missing — run 'npm run build' first" >&2
  exit 1
fi

if [ "${BCVM_SKIP_PREFLIGHT:-0}" != "1" ]; then
  echo "deploy-pages: launch preflight (scripts/launch-preflight.py --no-build --strict)"
  python3 "$ROOT/scripts/launch-preflight.py" --root "$ROOT" --no-build --strict
fi

echo "deploy-pages: uploading $OUT -> Cloudflare Pages project '$PROJECT' (branch $BRANCH)"
exec npx --yes wrangler@4 pages deploy "$OUT" --project-name="$PROJECT" --branch="$BRANCH"
