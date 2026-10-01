#!/usr/bin/env python3
"""test-launch.py — self-test for the one-command launch path (scripts/launch.sh).

A launch command is only safe to run if it can be shown to say GO on a complete
dataset, to refuse on each way the repo can be wrong, and to actually publish
what it says it published. This builds throwaway repo roots in a temp dir and
exercises the launcher against them:

    verify    a complete dataset -> exit 0 (GO)
    refuse    unfrozen questions / unarchived source / missing route -> exit 1
    package   dist/*.zip + dist/MANIFEST.json, every out/ file inside the zip
    publish   no credentials -> exit 2 and nothing deployed
    publish   stub deploy target -> exit 0, and it runs the deploy it was given
    verify    a live site that does not match the build -> exit 5
    wiring    the launcher runs the gate's own self-test when asked

Everything runs offline against 127.0.0.1; no real host is ever touched and the
temp roots are deleted unless --keep is passed.

    python3 scripts/test-launch.py           # run all cases
    python3 scripts/test-launch.py --keep    # keep the temp roots

Exit codes: 0 every case behaved as expected · 1 at least one case failed ·
3 could not run (missing scripts).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

SITE_URL = "https://bcvotematch.ca"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class StaticServer:
    """Serves a directory over http://127.0.0.1:<port> so the launcher's live
    verification can be exercised without a real host."""

    def __init__(self, directory: str):
        self.directory = directory
        self.port = free_port()
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(self.port),
             "--bind", "127.0.0.1", "--directory", directory],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/", timeout=2):
                    return
            except urllib.error.HTTPError:
                return
            except Exception:  # noqa: BLE001 - keep waiting for the socket
                time.sleep(0.2)
        raise RuntimeError("local static server did not come up")

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def build_fixture(root: str, green_builder, origin: str = SITE_URL) -> None:
    """A complete, sourced, buildable repo — the 'everything is done' case.

    `origin` is what the fixture thinks it is published at: the default is the
    real domain, and the live-verification cases point it at a local server so
    the publish path can be exercised without touching a real host.
    """
    green_builder(root)
    for name in ("launch.py", "launch.sh", "test-launch-preflight.py"):
        shutil.copy(os.path.join(HERE, name), os.path.join(root, "scripts", name))
    site = os.path.join(root, "src", "lib")
    os.makedirs(site, exist_ok=True)
    with open(os.path.join(site, "site.ts"), "w", encoding="utf-8") as fh:
        fh.write(
            "export const SITE = {\n"
            '  name: "BC Vote Match",\n'
            f'  url: "{origin}",\n'
            "} as const;\n"
        )
    if origin != SITE_URL:
        for dirpath, _dirnames, filenames in os.walk(os.path.join(root, "out")):
            for name in filenames:
                if not name.endswith((".html", ".xml", ".txt", ".json")):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                if SITE_URL in text:
                    write(path, text.replace(SITE_URL, origin))


def launch(root: str, *args: str, env: dict | None = None, timeout: int = 900):
    cmd = ["bash", os.path.join(root, "scripts", "launch.sh"), "--root", root, *args]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                          env=env, timeout=timeout)
    report = None
    if "--json" in args:
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            report = None
    return proc.returncode, proc.stdout, proc.stderr, report


def phase_status(report: dict | None, name: str) -> str | None:
    for p in (report or {}).get("phases", []):
        if p["name"] == name:
            return p["status"]
    return None


def phase_detail(report: dict | None, name: str) -> str:
    for p in (report or {}).get("phases", []):
        if p["name"] == name:
            return p.get("detail", "")
    return ""


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def write_json(path: str, obj) -> None:
    write(path, json.dumps(obj, indent=2))


def mutate_unfrozen(root: str) -> None:
    path = os.path.join(root, "data", "questions", "questions.json")
    rows = json.load(open(path))
    rows[1]["status"] = "candidate"
    write_json(path, rows)


def mutate_no_archive(root: str) -> None:
    path = os.path.join(root, "data", "raw", "cpb", "sources.json")
    rows = json.load(open(path))
    rows[0]["archive_url"] = None
    write_json(path, rows)


def mutate_missing_route(root: str) -> None:
    os.remove(os.path.join(root, "out", "questions", "index.html"))


BASE_ARGS = ("--check", "--no-build", "--no-typecheck", "--skip-selftest",
             "--offline", "--json")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Self-test for scripts/launch.sh")
    ap.add_argument("--keep", action="store_true", help="keep the temp roots")
    args = ap.parse_args(argv)

    for script in ("launch.py", "launch.sh", "test-launch-preflight.py",
                   "validate-dataset.py", "launch-preflight.py"):
        if not os.path.exists(os.path.join(HERE, script)):
            print(f"cannot run: scripts/{script} missing", file=sys.stderr)
            return 3

    preflight_test = load_module("bcvm_preflight_test", os.path.join(HERE, "test-launch-preflight.py"))
    results: list[tuple[str, bool, str]] = []
    keep_dirs: list[str] = []

    def new_root(origin: str = SITE_URL) -> str:
        root = tempfile.mkdtemp(prefix="bcvm-launch-")
        keep_dirs.append(root)
        build_fixture(root, preflight_test.build_green, origin)
        return root

    def case(label: str, ok: bool, detail: str) -> None:
        results.append((label, ok, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {label}: {detail}")

    # 1. A complete repo says GO.
    root = new_root()
    rc, out, err, report = launch(root, *BASE_ARGS, "--no-package")
    case("complete dataset -> GO",
         rc == 0 and report is not None and report.get("verdict") == "GO",
         f"exit {rc}, verdict={(report or {}).get('verdict')}"
         + ("" if rc == 0 else f", stderr={err.strip().splitlines()[-1:] }"))

    # 2. Each way the repo can be wrong is refused, with the right reason.
    for label, mutate, expect_phase, expect_detail in [
        ("unfrozen question set -> NO-GO", mutate_unfrozen, "launch gate", "frozen"),
        ("unarchived source -> NO-GO", mutate_no_archive, "launch gate", "archive_url"),
        ("missing route in out/ -> NO-GO", mutate_missing_route, "launch gate", "route"),
    ]:
        root = new_root()
        mutate(root)
        rc, out, err, report = launch(root, *BASE_ARGS, "--no-package")
        got = phase_status(report, expect_phase)
        detail = phase_detail(report, expect_phase)
        case(label,
             rc == 1 and got == "FAIL" and expect_detail in detail,
             f"exit {rc}; {expect_phase}={got} ({detail[:70]})")

    # 3. Packaging produces a self-describing artifact.
    root = new_root()
    rc, out, err, report = launch(root, *BASE_ARGS)
    manifest_path = os.path.join(root, "dist", "MANIFEST.json")
    ok = rc == 0 and os.path.exists(manifest_path)
    detail = f"exit {rc}"
    if ok:
        manifest = json.load(open(manifest_path))
        zip_path = os.path.join(root, manifest["artifact"]["path"])
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        out_files = {
            os.path.relpath(os.path.join(dp, f), os.path.join(root, "out"))
            for dp, _dn, fns in os.walk(os.path.join(root, "out")) for f in fns
        }
        ok = (
            manifest["artifact"]["sha256"] == sha256_file(zip_path)
            and out_files.issubset(names)
            and "MANIFEST.json" in names
            and manifest["export"]["files"] == len(out_files)
            and manifest["dataset"]["sources"] == 5
            and manifest["dataset"]["questions"] == 2
            and manifest["site_url"] == SITE_URL
        )
        detail = (f"exit {rc}, {manifest['export']['files']} files, "
                  f"sha256 {manifest['artifact']['sha256'][:12]}, "
                  f"{len(names)} zip entries")
    case("packaging writes a verifiable artifact", ok, detail)

    # 4. --publish with no credentials stops and says what is missing.
    root = new_root()
    env = {k: v for k, v in os.environ.items()
           if k not in ("BCVM_DEPLOY_CMD", "CLOUDFLARE_API_TOKEN", "CF_API_TOKEN",
                        "CLOUDFLARE_ACCOUNT_ID", "CF_ACCOUNT_ID")}
    rc, out, err, report = launch(root, *BASE_ARGS, "--publish", "--yes", env=env)
    deployed = os.path.exists(os.path.join(root, "out", ".deployed"))
    detail = phase_detail(report, "deploy")
    case("publish without credentials -> human step (exit 2)",
         rc == 2 and "CLOUDFLARE_API_TOKEN" in detail and not deployed,
         f"exit {rc}; deploy: {detail[:80]}")

    # 5. --publish with a stub deploy target actually runs it, then verifies the
    #    published site byte-for-byte against out/. The deploy goes to a local
    #    static server and --verify-at points the verification there, so the whole
    #    publish path is exercised offline (the fixture still claims the real
    #    domain, which is what the gate checks).
    serve = tempfile.mkdtemp(prefix="bcvm-serve-")
    keep_dirs.append(serve)
    server = StaticServer(serve)
    try:
        env = dict(os.environ)
        env.pop("CLOUDFLARE_API_TOKEN", None)
        env.pop("CLOUDFLARE_ACCOUNT_ID", None)
        env["BCVM_DEPLOY_CMD"] = 'cp -a "$OUT/." "$BCVM_SERVE/"'
        env["BCVM_SERVE"] = serve
        root5 = new_root()
        rc, out, err, report = launch(root5, *BASE_ARGS, "--publish", "--yes",
                                      "--verify-at", server.url, env=env)
        detail = phase_detail(report, "deploy")
        live = (report or {}).get("live") or []
        live_fail = [c for c in live if c["status"] == "FAIL"]
        case("stub publish runs the deploy and verifies the live site",
             rc == 0 and phase_status(report, "deploy") == "PASS" and not live_fail
             and len(live) >= 5,
             f"exit {rc}; deploy: {detail[:60]}; live checks: {len(live)}, "
             f"failures: {len(live_fail)}"
             + (f" ({live_fail[0]['name']}: {live_fail[0]['detail'][:60]})" if live_fail else ""))

        # 6. A live site that does not match the build is caught.
        serve2 = tempfile.mkdtemp(prefix="bcvm-serve-")
        keep_dirs.append(serve2)
        server2 = StaticServer(serve2)
        try:
            env = dict(os.environ)
            env.pop("CLOUDFLARE_API_TOKEN", None)
            env.pop("CLOUDFLARE_ACCOUNT_ID", None)
            # deploy a tampered build: the home page loses its privacy line
            env["BCVM_DEPLOY_CMD"] = (
                'cp -a "$OUT/." "$BCVM_SERVE/" && '
                'sed -i "s/no personal data/NO PERSONAL DATA REMOVED/" "$BCVM_SERVE/index.html"'
            )
            env["BCVM_SERVE"] = serve2
            root6 = new_root()
            rc, out, err, report = launch(root6, *BASE_ARGS, "--publish", "--yes",
                                          "--verify-at", server2.url, env=env)
            live = (report or {}).get("live") or []
            live_fail = [c for c in live if c["status"] == "FAIL"]
            case("live site that does not match the build -> exit 5",
                 rc == 5 and bool(live_fail) and any("matches the build" in c["name"] for c in live_fail),
                 f"exit {rc}; {len(live_fail)} live failure(s): "
                 f"{live_fail[0]['name'] if live_fail else 'none'}")
        finally:
            server2.stop()

        # 7. Standalone --verify-live against the same server.
        rc, out, err, report = launch(root5, "--verify-live", server.url, "--root", root5, "--json")
        case("--verify-live passes on a matching site",
             rc == 0 and phase_status(report, "live: / matches the build") == "PASS",
             f"exit {rc}; / matches the build={phase_status(report, 'live: / matches the build')}")
    finally:
        server.stop()

    # 8. The launcher runs the gate's own self-test when not skipped.
    root = new_root()
    rc, out, err, report = launch(root, "--check", "--no-build", "--no-typecheck",
                                  "--no-package", "--offline", "--json")
    detail = phase_detail(report, "gate self-test")
    case("launcher runs the gate self-test",
         phase_status(report, "gate self-test") == "PASS",
         f"{phase_status(report, 'gate self-test')}: {detail[:60]}")

    # 9. Bad root is refused without touching anything.
    proc = subprocess.run(
        ["bash", os.path.join(HERE, "launch.sh"), "--root", tempfile.mkdtemp(prefix="bcvm-notrepo-"),
         "--check", "--offline", "--json"],
        capture_output=True, text=True, timeout=120)
    case("non-repo root -> exit 3", proc.returncode == 3, f"exit {proc.returncode}")

    if args.keep:
        print("\ntemp roots kept:")
        for d in keep_dirs:
            print("  " + d)
    else:
        for d in keep_dirs:
            shutil.rmtree(d, ignore_errors=True)

    failures = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failures)}/{len(results)} cases behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
