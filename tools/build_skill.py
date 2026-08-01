"""Assemble SKILL.md from SKILL.src.md by resolving snippet includes.

SKILL.md is a generated artifact. Rule text that also appears on the docs site
lives once in `rules/`, and both consumers pull it in with the same
`--8<-- "path"` syntax: mkdocs via pymdownx.snippets, SKILL.md via this script.

    mise run skill          # regenerate SKILL.md
    mise run skill-check    # fail if SKILL.md is stale
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "SKILL.src.md"
TARGET = ROOT / "SKILL.md"

INCLUDE = re.compile(r'^(?P<indent>[ \t]*)--8<--\s+"(?P<path>[^"]+)"\s*$')


def expand(path: Path, seen: tuple[Path, ...] = ()) -> str:
    """Return the text of `path` with every include line resolved."""
    if path in seen:
        chain = " -> ".join(p.relative_to(ROOT).as_posix() for p in (*seen, path))
        raise RecursionError(f"circular include: {chain}")

    out: list[str] = []
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        match = INCLUDE.match(line)
        if match is None:
            out.append(line)
            continue

        target = ROOT / match["path"]
        if not target.is_file():
            where = f"{path.relative_to(ROOT).as_posix()}:{lineno}"
            raise FileNotFoundError(f"{where}: no such include {match['path']}")

        indent = match["indent"]
        included = expand(target, (*seen, path))
        out.extend(indent + part if part else part for part in included.splitlines())

    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if SKILL.md differs from the assembled output",
    )
    args = parser.parse_args()

    built = expand(SOURCE)

    if not args.check:
        TARGET.write_text(built)
        print(f"wrote {TARGET.relative_to(ROOT)} ({len(built.splitlines())} lines)")
        return 0

    current = TARGET.read_text() if TARGET.is_file() else ""
    if current == built:
        print("SKILL.md is up to date")
        return 0

    print(
        "SKILL.md is stale — it is generated from SKILL.src.md.\n"
        "Edit SKILL.src.md (or the fragments in rules/), then run: mise run skill",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
