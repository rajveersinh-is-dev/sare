"""Count lines of code in the tracked SARE repository.

Writes:
  results/loc_count.json   - per-language line counts + total + timestamp
  results/loc_badge.svg    - shields.io-style SVG badge (total LOC)

This is run by .github/workflows/loc.yml on every push so the README badge
reflects the latest committed state. It is NOT second-by-second real time: a
static README cannot be. It is updated on each push via CI.

Counting rule: physical lines in tracked source files (all extensions),
including blank and comment lines, because a "lines changed" metric is most
transparent when it measures every tracked byte. Tests, benchmarks, docs, and
results are included; build artifacts and caches are excluded (.gitignore).
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
COUNT_PATH = RESULTS_DIR / "loc_count.json"
BADGE_PATH = RESULTS_DIR / "loc_badge.svg"

# Extensions we treat as source / documentation worth counting.
INCLUDE_EXT = {
    ".py", ".rs", ".tex", ".md", ".toml", ".yaml", ".yml", ".json", ".bib",
    ".cff", "Makefile", ".cfg", ".ini",
}
EXCLUDE_NAMES = {
    "CACHEDIR.TAG", ".rustc_info.json",
}
EXCLUDE_DIRS = {
    ".git", "target", "__pycache__", ".pytest_cache", ".venv", "node_modules",
}


def tracked_files() -> list[Path]:
    """List files tracked by git (respects .gitignore)."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {out.stderr}")
    return [REPO_ROOT / line for line in out.stdout.splitlines() if line]


def count_lines(path: Path) -> int:
    try:
        with open(path, "rb") as f:
            return f.read().count(b"\n") + (1 if f.read(1) else 0)
    except OSError:
        return 0


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    by_lang: dict[str, int] = {}
    total = 0
    n_files = 0

    for path in tracked_files():
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDE_NAMES:
            continue
        ext = path.suffix.lower() or path.name
        if ext not in INCLUDE_EXT:
            continue
        lines = count_lines(path)
        by_lang[ext] = by_lang.get(ext, 0) + lines
        total += lines
        n_files += 1

    by_lang = dict(sorted(by_lang.items(), key=lambda kv: -kv[1]))
    stamp = dt.datetime.now(dt.UTC).isoformat()

    data = {
        "generated_at_utc": stamp,
        "total_lines": total,
        "files": n_files,
        "by_extension": by_lang,
        "note": "Physical lines in git-tracked source/docs; updated on push by CI.",
    }
    COUNT_PATH.write_text(json.dumps(data, indent=2) + "\n")

    # Simple shields.io-style badge.
    label = "lines of code"
    color = "#4c1" if total >= 1000 else "#97CA00" if total >= 500 else "#e05d44"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{90 + len(str(total))*7}" '
        f'height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" '
        f'stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<g clip-path="url(#a)"><rect width="{100 + len(str(total))*7}" height="20" fill="#555"/><rect x="100" '
        f'width="{len(str(total))*7 + 30}" height="20" fill="{color}"/><rect width="{100 + len(str(total))*7}" '
        f'height="20" fill="url(#b)"/></g><g fill="#fff" text-anchor="middle" font-family="Verdana" '
        f'font-size="11"><text x="50" y="15">{label}</text><text x="{110 + len(str(total))*7}" y="15">{total}</text></g>'
        f'<defs><clipPath id="a"><rect width="{100 + len(str(total))*7}" height="20" rx="3" fill="#fff"/></clipPath></defs></svg>'
    )
    BADGE_PATH.write_text(svg)
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
