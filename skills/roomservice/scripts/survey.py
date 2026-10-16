#!/usr/bin/env python3
"""Survey a git repo for roomservice: size, clutter, orphans, duplicates, map drift.

Usage: python3 -I survey.py [repo] [--warn 400] [--split 700] [--out before.json]
       python3 -I survey.py --compare before.json after.json

Read-only. Uses `git ls-files`, so gitignored and untracked-but-ignored files
never show up. Prints JSON; the agent decides what to do with it.
"""
import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

CODE = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".swift", ".go", ".rs", ".java",
        ".kt", ".rb", ".php", ".c", ".h", ".cpp", ".cs", ".vue", ".svelte", ".sh"}
# Entry points and config that nothing imports by name but that still belong.
ENTRY = re.compile(r"(^|/)(index|main|app|server|cli|__init__|__main__|setup|conftest|"
                   r"[^/]*\.config|[^/]*\.test|[^/]*\.spec|test_[^/]*|[^/]*_test|page|layout|route)\.[^/]+$")
ROOT_OK = re.compile(r"^(\.|readme|license|changelog|contributing|security|code_of_conduct|"
                     r"claude|agents|map|roadmap|next-tasks|makefile|dockerfile|package|tsconfig|"
                     r"pyproject|requirements|cargo|go\.|gemfile|pnpm-|turbo|vercel|netlify|[^/]*\.config\.|[^/]*lock|"
                     r"[^/]*\.(ya?ml|toml)$)", re.I)
MAP_PATH = re.compile(r"`([\w./@\[\]-]+/?)`")


def git_files(repo):
    out = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, check=True)
    return [p for p in out.stdout.decode().split("\0") if p and (repo / p).is_file()]


def read(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def survey(repo, warn, split):
    files = git_files(repo)
    lines, hashes, by_dir = {}, defaultdict(list), Counter()
    texts = {}
    for f in files:
        p = repo / f
        if p.stat().st_size > 2_000_000:  # binaries and dumps: count, don't read
            by_dir[f.split("/")[0] if "/" in f else "."] += 1
            continue
        t = read(p)
        texts[f] = t
        lines[f] = t.count("\n") + (not t.endswith("\n") and bool(t))
        hashes[hashlib.sha1(t.encode()).hexdigest()].append(f)
        by_dir[f.split("/")[0] if "/" in f else "."] += 1

    code = [f for f in lines if Path(f).suffix in CODE]
    corpus = "\n".join(texts.values())
    # A code file is an orphan candidate if its stem appears nowhere else in the repo.
    orphans = []
    for f in code:
        stem = Path(f).stem
        if ENTRY.search(f) or len(stem) < 3:
            continue
        if corpus.count(stem) <= texts[f].count(stem):
            orphans.append(f)

    map_file = next((m for m in ("MAP.md", "docs/MAP.md") if (repo / m).exists()), None)
    stale = []
    if map_file:
        for ref in set(MAP_PATH.findall(texts.get(map_file, ""))):
            if "/" in ref or "." in ref:
                if not (repo / ref.rstrip("/")).exists():
                    stale.append(ref)
    mapped_dirs = set(MAP_PATH.findall(texts.get(map_file, ""))) if map_file else set()
    unmapped = sorted(d for d in by_dir if d != "." and not any(m.strip("/").startswith(d) for m in mapped_dirs))

    big = sorted(((f, n) for f, n in lines.items() if f in code and n >= warn), key=lambda x: -x[1])
    per_folder = Counter(str(Path(f).parent) for f in files)
    result = {
        "repo": str(repo),
        "files": len(files),
        "code_files": len(code),
        "code_lines": sum(lines[f] for f in code),
        "files_per_top_dir": dict(by_dir.most_common()),
        "too_big": [{"file": f, "lines": n, "action": "split" if n >= split else "watch"} for f, n in big],
        "root_clutter": sorted(f for f in files if "/" not in f and not ROOT_OK.match(f)),
        "orphan_candidates": sorted(orphans),
        "duplicates": [g for g in hashes.values() if len(g) > 1 and lines.get(g[0], 0) > 3],
        "map": {"file": map_file, "stale_paths": sorted(stale), "unmapped_top_dirs": unmapped},
        "agent_docs": [f for f in ("CLAUDE.md", "AGENTS.md", "README.md") if (repo / f).exists()],
        "crowded_folders": dict((d, n) for d, n in per_folder.most_common(5) if n > 20),
        "max_file_lines": max((lines[f] for f in code), default=0),
        "max_folder_files": max(per_folder.values(), default=0),
    }
    result["chaos"] = chaos(result, lines, split)
    return result


def chaos(r, lines, split):
    """0 = tidy, 100 = chaos. Each part is a 0..1 penalty times its weight."""
    code_lines = r["code_lines"] or 1
    code_files = r["code_files"] or 1
    oversized = sum(b["lines"] for b in r["too_big"] if b["lines"] >= split) / code_lines
    m = r["map"]
    map_pen = 1.0 if not m["file"] else min(1.0, (len(m["stale_paths"]) + len(m["unmapped_top_dirs"])) / 5)
    parts = {  # name: (penalty, weight)
        "oversized_code_share": (min(1.0, oversized * 2), 25),
        "biggest_file": (min(1.0, max(0, r["max_file_lines"] - 400) / 1600), 10),
        "crowded_folder": (min(1.0, max(0, r["max_folder_files"] - 20) / 80), 10),
        "root_clutter": (min(1.0, len(r["root_clutter"]) / 10), 10),
        "orphans": (min(1.0, len(r["orphan_candidates"]) / code_files * 5), 15),
        "duplicates": (min(1.0, sum(len(g) for g in r["duplicates"]) / 10), 10),
        "map_missing_or_stale": (map_pen, 20),
    }
    return {"score": round(sum(p * w for p, w in parts.values())),
            "parts": {k: round(p * w, 1) for k, (p, w) in parts.items()}}


def compare(before, after):
    """Markdown table of the raw numbers and the chaos score, before vs after."""
    rows = [("Chaos score (0 tidy, 100 chaos)", before["chaos"]["score"], after["chaos"]["score"])]
    for key, label in (("files", "Files"), ("code_lines", "Code lines"), ("max_file_lines", "Biggest code file (lines)"),
                       ("max_folder_files", "Most files in one folder")):
        rows.append((label, before[key], after[key]))
    for key, label in (("too_big", "Files over the warn limit"), ("root_clutter", "Stray root files"),
                       ("orphan_candidates", "Orphan candidates"), ("duplicates", "Duplicate groups")):
        rows.append((label, len(before[key]), len(after[key])))
    rows.append(("MAP.md", before["map"]["file"] or "missing", after["map"]["file"] or "missing"))
    out = ["| Metric | Before | After |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    out += ["", "| Chaos part | Before | After |", "|---|---|---|"]
    out += [f"| {k} | {before['chaos']['parts'][k]} | {after['chaos']['parts'][k]} |" for k in before["chaos"]["parts"]]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".", type=Path)
    ap.add_argument("--warn", type=int, default=400)
    ap.add_argument("--split", type=int, default=700)
    ap.add_argument("--out", type=Path, help="also save the survey here")
    ap.add_argument("--compare", nargs=2, type=Path, metavar=("BEFORE", "AFTER"))
    a = ap.parse_args()
    if a.compare:
        print(compare(*(json.loads(p.read_text()) for p in a.compare)))
        return
    out = json.dumps(survey(a.repo.resolve(), a.warn, a.split), indent=1)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(out)
    print(out)


if __name__ == "__main__":
    main()
