#!/usr/bin/env python3
"""Sanitization gate: fail if the tree contains local-machine or operational leakage.

Run before every commit. Exits non-zero and lists offenders if anything is found.

Usage: python3 scripts/sanitize-check.py [--all]
       (default checks tracked files; --all walks the working tree)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_SUFFIXES = {
    ".py", ".sh", ".mjs", ".js", ".ts", ".tsx", ".json", ".jsonl", ".md",
    ".css", ".html", ".yml", ".yaml", ".txt", ".cfg", ".toml", ".gitignore",
}

# (label, compiled pattern)
RULES = [
    ("absolute home path", re.compile(r"(/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/|/mnt/[a-z]/)")),
    ("windows user path", re.compile(r"C:\\\\?Users\\\\?", re.I)),
    ("agent runtime path", re.compile(r"~/\.hermes|/\.hermes/")),
    ("internal task board", re.compile(r"kan" + "ban", re.I)),
    ("vast.ai host or endpoint", re.compile(r"ssh://[^\s]*vast\.ai|ssh[0-9]+\.vast\.ai", re.I)),
    ("vast.ai instance id", re.compile(r"vast\.ai[^\n]{0,20}\b\d{8}\b", re.I)),
    ("local commit identity", re.compile(r"bcvotematch\.local", re.I)),
    ("credential path", re.compile(r"secrets/(github\.token|git-credentials)", re.I)),
    ("github token shape", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("openai-style key", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
    ("private key block", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
    ("task identifier", re.compile(r"\b(t_[0-9a-f]{8}|deleg_[0-9a-f]{8,})\b")),
]

# Paths that must not be tracked at all.
FORBIDDEN_PATH = re.compile(
    r"(^|/)(\.venv|venv|node_modules|attic|\.next|out|dist|__pycache__)(/|$)"
    r"|(^|/)data/tmp/"
    r"|(^|/)bench/eval/"
    r"|\.pyc$|\.tsbuildinfo$"
)

# Under data/raw/ the provenance manifests are tracked; the bulk captures are not.
CAPTURE_SUFFIX = re.compile(r"\.(html|txt|pdf|zip|geojson|png|bak)$", re.I)


def tracked_files():
    out = subprocess.run(
        ["git", "-C", ROOT, "ls-files", "-z"], capture_output=True, check=True
    ).stdout.decode()
    return [f for f in out.split("\0") if f]


def walk_files():
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in names:
            yield os.path.relpath(os.path.join(base, n), ROOT)


def main():
    use_all = "--all" in sys.argv
    files = walk_files() if use_all else tracked_files()
    problems = []

    for rel in files:
        if FORBIDDEN_PATH.search(rel) or (
            rel.startswith("data/raw/") and CAPTURE_SUFFIX.search(rel)
        ):
            problems.append((rel, 0, "tracked build/artifact path", rel))
            continue
        ext = os.path.splitext(rel)[1]
        if ext not in TEXT_SUFFIXES and os.path.basename(rel) != ".gitignore":
            continue
        # this file necessarily contains the rule patterns themselves
        if rel == "scripts/sanitize-check.py":
            continue
        path = os.path.join(ROOT, rel)
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines, 1):
            for label, pat in RULES:
                m = pat.search(line)
                if m:
                    problems.append((rel, i, label, m.group(0)[:80]))

    if problems:
        print(f"sanitize-check: {len(problems)} problem(s)\n", file=sys.stderr)
        for rel, line, label, frag in problems:
            print(f"  {rel}:{line}: {label}: {frag}", file=sys.stderr)
        return 1
    print("sanitize-check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())