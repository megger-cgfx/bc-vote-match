#!/usr/bin/env python3
"""launch.py — BC Vote Match: repo to published site in one command.

This is the M5 launch path. One command runs the whole mechanical chain and
either puts the site live or stops with the exact reason it could not:

    bash scripts/launch.sh                       # verify + build + package, stop
    bash scripts/launch.sh --publish             # ... and publish (asks first)
    bash scripts/launch.sh --publish --yes       # ... and publish, no prompt
    bash scripts/launch.sh --check               # verify the existing out/ only
    bash scripts/launch.sh --verify-live URL     # check a published site
    bash scripts/launch.sh --json                # machine-readable report

The chain, in order:

    env       python3, node/npm, repo layout, git
    test      scripts/test-launch-preflight.py  — does the gate still work?
    type      npm run typecheck
    build     npm run build                     — regenerate out/
    gate      scripts/launch-preflight.py --strict --online
    package   dist/bcvm-<sha>.zip + dist/MANIFEST.json
    deploy    --publish only: wrangler (Cloudflare Pages) or $BCVM_DEPLOY_CMD
    live      after a deploy: is the published site what we built?

Nothing is published unless the gate says GO, and never without an explicit
--publish plus a typed confirmation (or --yes). Publishing is the one
irreversible step in this project, so this script makes it the one step that
cannot happen by accident.

The deploy target is deliberately not hard-coded: see `--help` and
docs/05-LAUNCH.md §4. Set `BCVM_DEPLOY_CMD` to any command that copies `out/`
somewhere ($OUT, $ROOT and $ARTIFACT are exported to it), or set
`CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` to deploy to Cloudflare Pages
with wrangler. Publishing needs credentials this repo does not hold (Martin's
accounts), so with none configured the script stops with exit 2 and prints the
exact command for each supported host.

Exit codes
    0  GO and the requested work completed (checked / packaged / published)
    1  NO-GO — a mechanical gate failed; nothing was built or published
    2  GO, but publishing needs a human step (confirmation or credentials)
    3  could not run (missing tooling, bad repo root, bad arguments)
    4  the deploy command ran and failed
    5  deployed, but the live site does not match the artifact we built
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field

EXIT_OK = 0
EXIT_NO_GO = 1
EXIT_HUMAN = 2
EXIT_ENV = 3
EXIT_DEPLOY_FAILED = 4
EXIT_LIVE_MISMATCH = 5

PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]

# Routes checked on a live site: (url path, local file under out/, cache-bust?).
LIVE_ROUTES = [
    ("", "index.html", True),
    ("questions/", "questions/index.html", True),
    ("results/", "results/index.html", True),
    ("parties/", "parties/index.html", True),
    ("methodology/", "methodology/index.html", True),
    ("coding-table/", "coding-table/index.html", True),
    ("about/", "about/index.html", True),
    ("robots.txt", "robots.txt", False),
    ("sitemap.xml", "sitemap.xml", True),
    ("og.png", "og.png", False),
]

# Copy that must be present on the published home page.
LIVE_REQUIRED_COPY = [
    "not affiliated with",
    "does not tell you how to vote",
    "no personal data",
]

FORBIDDEN_MARKERS = [
    "PLACEHOLDER DATA",
    "Sample data",
    "example.invalid",
    "v0-fixture",
    "not a real quote",
]

SECRET_ENV = [
    "BCVM_DEPLOY_CMD",
    "CLOUDFLARE_API_TOKEN",
    "CF_API_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
]


# --------------------------------------------------------------------------- #
# plumbing
# --------------------------------------------------------------------------- #

def redact(text: str) -> str:
    for key in SECRET_ENV:
        value = os.environ.get(key)
        if value and len(value) >= 6:
            text = text.replace(value, "***")
    return text


@dataclass
class Phase:
    name: str
    status: str  # PASS | FAIL | WARN | SKIP
    detail: str = ""


@dataclass
class Ctx:
    root: str
    args: argparse.Namespace
    phases: list[Phase] = field(default_factory=list)
    gate: dict = field(default_factory=dict)
    artifact: dict = field(default_factory=dict)
    live: list[dict] = field(default_factory=list)
    deploy: dict = field(default_factory=dict)
    started: float = field(default_factory=time.time)

    def add(self, name: str, status: str | bool, detail: str = "") -> None:
        if isinstance(status, bool):
            status = "PASS" if status else "FAIL"
        self.phases.append(Phase(name, status, detail))

    def phase(self, name: str) -> Phase | None:
        for p in reversed(self.phases):
            if p.name == name:
                return p
        return None

    @property
    def failures(self) -> list[Phase]:
        return [p for p in self.phases if p.status == "FAIL"]

    @property
    def warnings(self) -> list[Phase]:
        return [p for p in self.phases if p.status == "WARN"]

    def to_dict(self) -> dict:
        return {
            "tool": "scripts/launch.py",
            "root": self.root,
            "verdict": "NO-GO" if self.failures else "GO",
            "phases": [
                {"name": p.name, "status": p.status, "detail": p.detail} for p in self.phases
            ],
            "blockers": [f"{p.name}: {p.detail}" for p in self.failures],
            "warnings": [f"{p.name}: {p.detail}" for p in self.warnings],
            "gate": self.gate,
            "artifact": self.artifact,
            "deploy": self.deploy,
            "live": self.live,
            "elapsed_s": round(time.time() - self.started, 1),
        }


def run(cmd: list[str], cwd: str, timeout: int = 1800, env: dict | None = None) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    except FileNotFoundError as exc:
        return 127, "", f"{cmd[0]}: {exc}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s: {' '.join(cmd)}"
    return proc.returncode, redact(proc.stdout or ""), redact(proc.stderr or "")


def tail(text: str, lines: int = 25) -> str:
    rows = [ln for ln in (text or "").strip().splitlines() if ln.strip()]
    return "\n".join(rows[-lines:])


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(root: str) -> dict:
    info: dict[str, object] = {"sha": None, "short": None, "branch": None, "dirty": None}
    rc, out, _ = run(["git", "rev-parse", "HEAD"], root, timeout=30)
    if rc == 0:
        info["sha"] = out.strip()
        info["short"] = out.strip()[:12]
    rc, out, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root, timeout=30)
    if rc == 0:
        info["branch"] = out.strip()
    rc, out, _ = run(["git", "status", "--porcelain"], root, timeout=60)
    if rc == 0:
        info["dirty"] = bool(out.strip())
    return info


def read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def dataset_counts(root: str) -> dict:
    data = os.path.join(root, "data")
    counts: dict = {}
    parties = read_json(os.path.join(data, "parties.json"))
    if isinstance(parties, list):
        counts["parties"] = len(parties)
    questions = read_json(os.path.join(data, "questions", "questions.json"))
    if isinstance(questions, list):
        counts["questions"] = len(questions)
        counts["questions_frozen"] = len(
            [q for q in questions if isinstance(q, dict) and q.get("status") == "frozen"]
        )
    rows = 0
    aggregate = read_json(os.path.join(data, "codings", "codings.json"))
    if isinstance(aggregate, list) and aggregate:
        rows = len(aggregate)  # the published table is authoritative
    else:
        for slug in PARTY_SLUGS:
            got = read_json(os.path.join(data, "codings", f"{slug}.json"))
            if isinstance(got, list):
                rows += len(got)
    counts["coding_rows"] = rows
    sources = 0
    archived = 0
    for slug in PARTY_SLUGS:
        got = read_json(os.path.join(data, "raw", slug, "sources.json"))
        if isinstance(got, list):
            sources += len(got)
            archived += len([s for s in got if isinstance(s, dict) and s.get("archive_url")])
    counts["sources"] = sources
    counts["sources_archived"] = archived
    return counts


def site_url(root: str) -> str:
    """Read SITE.url out of src/lib/site.ts without importing TypeScript."""
    path = os.path.join(root, "src", "lib", "site.ts")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return ""
    m = re.search(r"""^\s*url:\s*["'](https?://[^"']+)["']""", text, re.MULTILINE)
    return m.group(1).rstrip("/") if m else ""


# --------------------------------------------------------------------------- #
# phases
# --------------------------------------------------------------------------- #

def phase_env(ctx: Ctx) -> None:
    ctx.add("running from a repo root", os.path.isdir(os.path.join(ctx.root, "data")),
            ctx.root if os.path.isdir(os.path.join(ctx.root, "data")) else "no data/ directory")
    action_phases = {
        "test": os.path.join(ctx.root, "scripts", "test-launch-preflight.py"),
        "gate": os.path.join(ctx.root, "scripts", "launch-preflight.py"),
    }
    missing = [n for n, p in action_phases.items() if not os.path.exists(p)]
    ctx.add("launcher's gates are present", not missing, ", ".join(missing) or "preflight + selftest")

    needs_node = os.path.exists(os.path.join(ctx.root, "package.json")) and not ctx.args.no_build
    if needs_node:
        node = shutil.which("node")
        npm = shutil.which("npm")
        ctx.add("node + npm available", bool(node and npm),
                f"node={node or 'MISSING'} npm={npm or 'MISSING'}")
    else:
        ctx.add("node + npm available", "SKIP", "no package.json or --no-build")

    info = git_info(ctx.root)
    if info["sha"]:
        dirty = "dirty" if info["dirty"] else "clean"
        ctx.add("git revision identified", "WARN" if info["dirty"] else "PASS",
                f"{info['short']} on {info['branch']} ({dirty})")
    else:
        ctx.add("git revision identified", "WARN", "not a git work tree")


def phase_selftest(ctx: Ctx) -> None:
    if ctx.args.skip_selftest:
        ctx.add("gate self-test", "SKIP", "--skip-selftest")
        return
    script = os.path.join(ctx.root, "scripts", "test-launch-preflight.py")
    if not os.path.exists(script):
        ctx.add("gate self-test", "FAIL", "scripts/test-launch-preflight.py missing")
        return
    rc, out, err = run([sys.executable, script], ctx.root, timeout=900)
    last = tail(out, 1)
    ctx.add("gate self-test", rc == 0, last or tail(err, 1) or f"exit {rc}")
    if rc != 0:
        print(tail(out + "\n" + err, 30), file=sys.stderr)


def phase_typecheck(ctx: Ctx) -> None:
    if ctx.args.no_typecheck:
        ctx.add("typecheck (tsc --noEmit)", "SKIP", "--no-typecheck")
        return
    if not os.path.exists(os.path.join(ctx.root, "package.json")):
        ctx.add("typecheck (tsc --noEmit)", "SKIP", "no package.json")
        return
    if not os.path.isdir(os.path.join(ctx.root, "node_modules")):
        ctx.add("typecheck (tsc --noEmit)", "SKIP", "no node_modules (run npm ci)")
        return
    rc, out, err = run(["npm", "run", "typecheck"], ctx.root, timeout=900)
    ctx.add("typecheck (tsc --noEmit)", rc == 0, "exit 0" if rc == 0 else f"exit {rc}")
    if rc != 0:
        print(tail(out + "\n" + err, 30), file=sys.stderr)


def phase_build(ctx: Ctx) -> None:
    if ctx.args.check:
        ctx.add("next build", "SKIP", "--check: verifying the existing out/")
        return
    if ctx.args.no_build:
        ctx.add("next build", "SKIP", "--no-build")
        return
    if not os.path.exists(os.path.join(ctx.root, "package.json")):
        ctx.add("next build", "SKIP", "no package.json")
        return
    rc, out, err = run(["npm", "run", "build"], ctx.root, timeout=1800)
    ctx.add("next build", rc == 0, "exit 0" if rc == 0 else f"exit {rc}")
    if rc != 0:
        print(tail(out + "\n" + err, 40), file=sys.stderr)


def phase_gate(ctx: Ctx) -> None:
    script = os.path.join(ctx.root, "scripts", "launch-preflight.py")
    # --no-build: launch.py owns the build (phase_build above); the gate judges
    # the out/ this run produced, it must not rebuild behind our back.
    cmd = [sys.executable, script, "--root", ctx.root, "--json", "--strict", "--no-build"]
    if not ctx.args.offline:
        cmd.append("--online")
    rc, out, err = run(cmd, ctx.root, timeout=900)
    try:
        report = json.loads(out)
    except json.JSONDecodeError:
        ctx.add("launch gate", "FAIL", f"could not read the gate report (exit {rc}): {tail(out + err, 1)}")
        return
    ctx.gate = report
    fails = [c for c in report.get("checks", []) if c.get("status") == "FAIL"]
    warns = [c for c in report.get("checks", []) if c.get("status") == "WARN"]
    if rc == 0:
        ctx.add("launch gate", "PASS", f"{len(report.get('checks', []))} checks, all pass")
    elif fails:
        names = "; ".join(f"{c['name']} ({c['detail'][:70]})" for c in fails[:4])
        more = f" +{len(fails) - 4} more" if len(fails) > 4 else ""
        ctx.add("launch gate", "FAIL", f"{len(fails)} failure(s): {names}{more}")
    else:
        names = "; ".join(f"{c['name']} ({c['detail'][:70]})" for c in warns[:4])
        ctx.add("launch gate", "FAIL", f"{len(warns)} warning(s) under --strict: {names}")


def phase_package(ctx: Ctx) -> None:
    if ctx.args.no_package:
        ctx.add("launch artifact", "SKIP", "--no-package")
        return
    out_dir = os.path.join(ctx.root, "out")
    if not os.path.isdir(out_dir):
        ctx.add("launch artifact", "FAIL", "out/ is missing")
        return
    dist = os.path.join(ctx.root, "dist")
    os.makedirs(dist, exist_ok=True)

    info = git_info(ctx.root)
    tag = (info["short"] or "nogit") + ("-dirty" if info["dirty"] else "")
    zip_path = os.path.join(dist, f"bcvm-{tag}.zip")

    files: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(out_dir):
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, out_dir)
            files.append({"path": rel, "bytes": os.path.getsize(path), "sha256": sha256_file(path)})

    manifest = {
        "project": "bc-vote-match",
        "artifact": {"path": os.path.relpath(zip_path, ctx.root), "sha256": None,
                     "note": "self-hash recorded in dist/MANIFEST.json beside the archive"},
        "git": info,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "site_url": site_url(ctx.root),
        "gate": {"verdict": ctx.gate.get("verdict"), "failures": ctx.gate.get("failures"),
                 "warnings": ctx.gate.get("warnings")},
        "dataset": dataset_counts(ctx.root),
        "export": {"files": len(files), "bytes": sum(f["bytes"] for f in files)},
        "contents": files,
    }

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(files, key=lambda f: f["path"]):
            zf.write(os.path.join(out_dir, path["path"]), path["path"])
        zf.writestr("MANIFEST.json", json.dumps(manifest, indent=2))

    manifest["artifact"]["sha256"] = sha256_file(zip_path)
    manifest["artifact"]["bytes"] = os.path.getsize(zip_path)
    with open(os.path.join(dist, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    ctx.artifact = manifest["artifact"] | {"files": len(files), "manifest": "dist/MANIFEST.json"}
    ctx.add("launch artifact", "PASS",
            f"{os.path.relpath(zip_path, ctx.root)} "
            f"({manifest['artifact']['bytes'] / 1024:.0f} KiB, {len(files)} files)")


def deploy_env(ctx: Ctx) -> dict:
    """Environment for the deploy command: $OUT, $ROOT and $ARTIFACT are set so a
    custom command does not have to guess the paths."""
    env = dict(os.environ)
    env["OUT"] = os.path.join(ctx.root, "out")
    env["ROOT"] = ctx.root
    if ctx.artifact.get("path"):
        env["ARTIFACT"] = os.path.join(ctx.root, ctx.artifact["path"])
    return env


def deploy_target(ctx: Ctx) -> tuple[str, str, str]:
    """(kind, shell command, human note)."""
    out_dir = os.path.join(ctx.root, "out")
    custom = os.environ.get("BCVM_DEPLOY_CMD")
    if custom:
        return "custom", custom, "BCVM_DEPLOY_CMD"
    token = os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CF_ACCOUNT_ID")
    project = os.environ.get("BCVM_PAGES_PROJECT", "bc-vote-match")
    if token and account:
        cmd = (
            f'npx --yes wrangler@4 pages deploy "{out_dir}" '
            f'--project-name="{project}" --branch=main'
        )
        return "cloudflare", cmd, f"Cloudflare Pages project {project}"
    missing = []
    if not token:
        missing.append("CLOUDFLARE_API_TOKEN")
    if not account:
        missing.append("CLOUDFLARE_ACCOUNT_ID")
    return "missing", "", "missing " + ", ".join(missing)


def phase_deploy(ctx: Ctx) -> None:
    if not ctx.args.publish:
        ctx.add("deploy", "SKIP", "no --publish: artifact is staged, nothing is live")
        return

    kind, cmd, note = deploy_target(ctx)
    if kind == "missing":
        ctx.add("deploy", "FAIL", f"no deploy target configured ({note})")
        ctx.deploy = {"kind": "missing", "reason": note}
        return

    if not ctx.args.yes:
        if not sys.stdin.isatty():
            ctx.add("deploy", "FAIL", "confirmation required: rerun with --yes (no TTY here)")
            return
        print(f"\nAbout to publish {ctx.root}/out -> {note}")
        print(f"  {cmd}\n")
        answer = input('Type "publish" to deploy, anything else to stop: ').strip()
        if answer != "publish":
            ctx.add("deploy", "FAIL", "not confirmed: nothing was published")
            return

    rc, out, err = run(["bash", "-lc", cmd], ctx.root, timeout=1800, env=deploy_env(ctx))
    ctx.deploy = {"kind": kind, "command": cmd, "exit": rc, "detail": note}
    ctx.add("deploy", rc == 0, f"{note} exit {rc}" if rc else f"published via {note}")
    if rc != 0:
        print(tail(out + "\n" + err, 40), file=sys.stderr)


# --------------------------------------------------------------------------- #
# live verification
# --------------------------------------------------------------------------- #

def fetch(url: str, timeout: int = 30) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "bcvm-launch-verify"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), ""
    except urllib.error.HTTPError as exc:
        return exc.code, b"", f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - a network failure must not crash the run
        return 0, b"", f"{type(exc).__name__}: {exc}"


def verify_live(ctx: Ctx, url: str) -> int:
    base = url.rstrip("/")
    out_dir = os.path.join(ctx.root, "out")
    bust = int(time.time())
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    mismatches = 0
    for path, local, cache_bust in LIVE_ROUTES:
        target = f"{base}/{path}"
        if cache_bust and path.endswith(("/", ".xml")):
            target += f"?v={bust}"
        status, body, err = fetch(target)
        label = f"/{path}" if path else "/"
        if status != 200:
            add(f"{label} serves 200", False, err or f"status {status}")
            mismatches += 1
            continue
        local_path = os.path.join(out_dir, local)
        if os.path.exists(local_path):
            want = sha256_file(local_path)
            got = hashlib.sha256(body).hexdigest()
            ok = want == got
            add(f"{label} matches the build", ok,
                "byte-identical to out/" + local if ok
                else f"live bytes differ from out/{local} (cached or wrong deploy?)")
            mismatches += 0 if ok else 1
        else:
            add(f"{label} serves 200", True, f"{len(body)} bytes")

    status, body, err = fetch(f"{base}/?v={bust}")
    if status == 200:
        text = body.decode("utf-8", "replace")
        missing = [c for c in LIVE_REQUIRED_COPY if c.lower() not in text.lower()]
        add("live home page carries the disclaimers", not missing,
            ", ".join(missing) or "independence + how-to-vote + privacy copy present")
        bad = [m for m in FORBIDDEN_MARKERS if m in text]
        add("live home page has no placeholder content", not bad, ", ".join(bad) or "clean")
        canonical = site_url(ctx.root)
        if canonical:
            ok = f'href="{canonical}/"' in text or f'href="{canonical}"' in text
            add("live canonical points at the published origin", ok, canonical)
    else:
        add("live home page reachable", False, err or f"status {status}")

    ctx.live = checks
    for c in checks:
        ctx.add(f"live: {c['name']}", c["status"], c["detail"])
    failed = [c for c in checks if c["status"] == "FAIL"]
    return EXIT_OK if not failed else EXIT_LIVE_MISMATCH


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #

def print_report(ctx: Ctx) -> None:
    width = max((len(p.name) for p in ctx.phases), default=0)
    for p in ctx.phases:
        print(f"[{p.status:4}] {p.name.ljust(width)}  {p.detail}")
    verdict = "NO-GO" if ctx.failures else "GO"
    print(f"\n{verdict}: {len(ctx.failures)} blocker(s), {len(ctx.warnings)} warning(s)")
    if ctx.failures:
        print("Stopped because:")
        for p in ctx.failures:
            print(f"  - {p.name}: {p.detail}")
    if ctx.gate:
        bad = [c for c in ctx.gate.get("checks", []) if c.get("status") in ("FAIL", "WARN")]
        if any(c["status"] == "FAIL" for c in bad):
            print("\nGate detail (scripts/launch-preflight.py --strict --online), untruncated:")
            for c in bad:
                print(f"  [{c['status']:4}] {c['name']}: {c['detail']}")


def print_next_steps(ctx: Ctx) -> None:
    if ctx.failures:
        print("\nNothing was published. Fix the blockers above and run this again.")
        return
    print("\nEverything mechanical passed. Nothing is live yet unless you passed --publish.")
    print(f"  artifact           {ctx.artifact.get('path', '(not packaged)')}")
    print(f"  publish (Cloudflare Pages, needs your token):")
    print(f"    bash scripts/launch.sh --publish")
    print(f"  or upload the zip by hand in the Cloudflare Pages dashboard")
    print(f"  after publishing, verify what is actually live:")
    print(f"    bash scripts/launch.sh --verify-live {site_url(ctx.root) or 'https://<host>'}")


# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.abspath(os.path.join(here, ".."))

    ap = argparse.ArgumentParser(
        prog="launch.sh",
        description="BC Vote Match — verify, build, package and (optionally) publish in one command.",
    )
    ap.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    ap.add_argument("--check", action="store_true", help="verify the existing out/ only; no build")
    ap.add_argument("--no-build", action="store_true", help="never run `npm run build`")
    ap.add_argument("--no-typecheck", action="store_true", help="skip `tsc --noEmit`")
    ap.add_argument("--no-package", action="store_true", help="skip dist/ packaging")
    ap.add_argument("--skip-selftest", action="store_true", help="skip the gate's own self-test")
    ap.add_argument("--publish", action="store_true", help="deploy after a GO (asks to confirm)")
    ap.add_argument("--yes", action="store_true", help="with --publish: do not prompt")
    ap.add_argument("--offline", action="store_true", help="skip the --online domain check")
    ap.add_argument("--verify-live", metavar="URL", default=None,
                    help="check a published site against this build and exit")
    ap.add_argument("--verify-at", metavar="URL", default=None,
                    help="verify the deploy at this URL (default: SITE.url). Use it for "
                         "a *.pages.dev preview before the custom domain is live")
    ap.add_argument("--json", action="store_true", help="machine-readable report on stdout")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root) if args.root else default_root
    if not os.path.isdir(os.path.join(root, "data")):
        print(f"launch: {root} does not look like the repo root (no data/)", file=sys.stderr)
        return EXIT_ENV

    ctx = Ctx(root=root, args=args)

    if args.verify_live:
        code = verify_live(ctx, args.verify_live)
        if args.json:
            print(json.dumps(ctx.to_dict(), indent=2))
        else:
            print_report(ctx)
        return code

    phase_env(ctx)
    if ctx.failures:
        if args.json:
            print(json.dumps(ctx.to_dict(), indent=2))
        else:
            print_report(ctx)
        return EXIT_ENV

    phase_selftest(ctx)
    phase_typecheck(ctx)
    phase_build(ctx)
    # The gate must be the last thing before packaging: it judges the out/ that
    # the build just produced, not an earlier one.
    phase_gate(ctx)

    if ctx.failures:
        ctx.add("launch artifact", "SKIP", "gate is NO-GO")
        ctx.add("deploy", "SKIP", "gate is NO-GO")
        if args.json:
            print(json.dumps(ctx.to_dict(), indent=2))
        else:
            print_report(ctx)
            print_next_steps(ctx)
        return EXIT_NO_GO

    phase_package(ctx)
    if ctx.failures:
        if args.json:
            print(json.dumps(ctx.to_dict(), indent=2))
        else:
            print_report(ctx)
        return EXIT_NO_GO

    phase_deploy(ctx)
    if args.publish and not ctx.failures:
        canonical = args.verify_at or site_url(root)
        if canonical:
            code = verify_live(ctx, canonical)
        else:
            ctx.add("live: published site", "WARN", "could not read SITE.url; verify by hand")
            code = EXIT_OK
        if args.json:
            print(json.dumps(ctx.to_dict(), indent=2))
        else:
            print_report(ctx)
        return code
    if ctx.args.publish and ctx.failures:
        code = EXIT_HUMAN if any("no deploy target" in p.detail or "confirmation" in p.detail
                                 for p in ctx.failures) else EXIT_DEPLOY_FAILED
        if args.json:
            print(json.dumps(ctx.to_dict(), indent=2))
        else:
            print_report(ctx)
            _print_deploy_help(ctx)
        return code

    if args.json:
        print(json.dumps(ctx.to_dict(), indent=2))
    else:
        print_report(ctx)
        print_next_steps(ctx)
    return EXIT_OK


def _print_deploy_help(ctx: Ctx) -> None:
    kind, _cmd, note = deploy_target(ctx)
    print("\nNothing was published.")
    if kind == "missing":
        print(f"  deploy target: not configured ({note})")
        print("  pick one and run the same command again:")
        print("    export CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=...")
        print("      -> npx wrangler@4 pages deploy out --project-name bc-vote-match --branch main")
        print("    export BCVM_DEPLOY_CMD='rsync -a --delete out/ you@host:/srv/bcvotematch/'")
        print("      -> anything that copies out/ where the web server can see it")
        print(f"  or upload {ctx.artifact.get('path', 'dist/*.zip')} by hand (no credentials needed)")
    else:
        print(f"  last deploy attempt ({note}) did not complete; see the log above.")


if __name__ == "__main__":
    sys.exit(main())
