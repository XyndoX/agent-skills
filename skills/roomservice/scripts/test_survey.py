"""Run: python3 -I scripts/test_survey.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import survey  # noqa: E402


def test():
    r = Path(tempfile.mkdtemp())
    files = {
        "README.md": "# x\n",
        "MAP.md": "- `src/` code\n- `src/gone.py` removed long ago\n",
        "notes-old.txt": "scratch\n",
        "src/main.py": "from util import helper\nhelper()\n",
        "src/util.py": "def helper():\n    pass\n",
        "src/lonely.py": "def nobody_calls_me():\n    pass\n",
        "src/huge.py": "x = 1\n" * 800,
        "lib/a.js": "same\ncontent\nin\nboth\nfiles\n",
        "lib/b.js": "same\ncontent\nin\nboth\nfiles\n",
        "ignored.log": "secret\n",
    }
    for f, t in files.items():
        (r / f).parent.mkdir(parents=True, exist_ok=True)
        (r / f).write_text(t)
    (r / ".gitignore").write_text("*.log\n")
    subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)

    d = survey.survey(r, warn=400, split=700)
    assert "ignored.log" not in str(d), "gitignored files must not appear"
    assert d["too_big"] == [{"file": "src/huge.py", "lines": 800, "action": "split"}], d["too_big"]
    assert d["root_clutter"] == ["notes-old.txt"], d["root_clutter"]
    assert "src/lonely.py" in d["orphan_candidates"] and "src/util.py" not in d["orphan_candidates"]
    assert "src/main.py" not in d["orphan_candidates"], "entry points are never orphans"
    assert d["duplicates"] == [["lib/a.js", "lib/b.js"]], d["duplicates"]
    assert d["map"]["stale_paths"] == ["src/gone.py"], d["map"]
    assert d["map"]["unmapped_top_dirs"] == ["lib"], d["map"]
    assert d["max_file_lines"] == 800 and d["chaos"]["parts"]["map_missing_or_stale"] > 0

    # Tidy up: drop the stray file, the orphan, the duplicate, fix the map. Chaos must fall.
    for f in ("notes-old.txt", "src/lonely.py", "lib/b.js"):
        (r / f).unlink()
    (r / "MAP.md").write_text("- `src/` code\n- `lib/a.js` lib\n")
    subprocess.run(["git", "-C", str(r), "add", "-A"], check=True)
    after = survey.survey(r, warn=400, split=700)
    assert after["chaos"]["score"] < d["chaos"]["score"], (d["chaos"], after["chaos"])
    table = survey.compare(d, after)
    assert "| Stray root files | 1 | 0 |" in table, table
    print("ok")


if __name__ == "__main__":
    test()
