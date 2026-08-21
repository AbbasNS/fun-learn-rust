#!/usr/bin/env python3
"""Generate the numbered README table of contents from mdBook's SUMMARY.md."""

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIPS = ROOT / "tips"
SUMMARY = TIPS / "SUMMARY.md"
README = ROOT / "README.md"

START = "<!-- BEGIN GENERATED TABLE OF CONTENTS -->"
END = "<!-- END GENERATED TABLE OF CONTENTS -->"
CHAPTER = re.compile(r"^- \[([^]]+)\]\(\./([^)]+\.md)\)$")
DISCUSSION = re.compile(r"^  - \[Follow-up\]\(\./([^)]+\.md)\)$")


def read_chapters():
    chapters = []
    referenced = set()

    for number, line in enumerate(
        SUMMARY.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line or line == "# Summary":
            continue

        match = CHAPTER.fullmatch(line)
        if match:
            title, path = match.groups()
            if path in referenced:
                raise ValueError(f"{SUMMARY}:{number}: duplicate path {path}")
            referenced.add(path)
            chapters.append([title, path, None])
            continue

        match = DISCUSSION.fullmatch(line)
        if match:
            if not chapters:
                raise ValueError(f"{SUMMARY}:{number}: discussion has no chapter")
            path = match.group(1)
            if path in referenced:
                raise ValueError(f"{SUMMARY}:{number}: duplicate path {path}")
            if chapters[-1][2] is not None:
                raise ValueError(f"{SUMMARY}:{number}: duplicate discussion")
            referenced.add(path)
            chapters[-1][2] = path
            continue

        raise ValueError(f"{SUMMARY}:{number}: unsupported entry: {line}")

    on_disk = {
        path.relative_to(TIPS).as_posix()
        for path in TIPS.rglob("*.md")
        if path != SUMMARY
    }
    unlisted = sorted(on_disk - referenced)
    missing = sorted(referenced - on_disk)
    if unlisted or missing:
        details = []
        if unlisted:
            details.append(f"unlisted: {', '.join(unlisted)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise ValueError("; ".join(details))

    return chapters


def render(readme, chapters):
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError("README must contain exactly one generated TOC marker pair")

    before, remainder = readme.split(START, 1)
    _, after = remainder.split(END, 1)
    lines = []
    for number, (title, path, discussion) in enumerate(chapters, start=1):
        line = f"{number}. [{title}](tips/{path})"
        if discussion:
            line += f" · [discussion](tips/{discussion})"
        lines.append(line)

    toc = "\n".join(lines)
    return f"{before}{START}\n{toc}\n{END}{after}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    check = parser.parse_args().check

    try:
        chapters = read_chapters()
        current = README.read_text(encoding="utf-8")
        expected = render(current, chapters)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    discussions = sum(discussion is not None for _, _, discussion in chapters)
    status = f"{len(chapters)} tips and {discussions} discussions"
    if check:
        if current != expected:
            print(
                "README table of contents is stale; "
                "run ./scripts/sync_readme_toc.py",
                file=sys.stderr,
            )
            return 1
        print(f"README table of contents is current: {status}")
    else:
        README.write_text(expected, encoding="utf-8")
        print(f"Updated README table of contents: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
