#!/usr/bin/env python3
"""Check that every quoted snippet in the knowledge base still matches the real source file.

Usage:
  python tools/verify_snippets.py --root D:\\Heechee\\Git\\Ormod-Directive Ormod_Mod_Tutorial.md [more .md files]

A snippet is a block that follows a line  *Source: `Heechee_X/src/File.cs`*  and is fenced as csharp. Each line of the snippet must appear
in the source file, in order (indentation ignored). Exit code 1 and a list of problems if a snippet no longer matches (the code changed:
update the snippet and its explanation), also if a markdown file has unbalanced code fences.
"""
import argparse
import re
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("files", nargs="+")
    a = p.parse_args()
    problems, checked = [], 0
    for name in a.files:
        text = Path(name).read_text(encoding="utf-8").replace("\r", "")
        if text.count("```") % 2:
            problems.append(f"{name}: unbalanced code fences")
        for m in re.finditer(r"\*Source: `([^`]+)`\*\n\n```csharp\n(.*?)\n```", text, re.S):
            rel, body = m.group(1), m.group(2)
            path = Path(a.root) / rel
            if not path.exists():
                problems.append(f"{name}: source file not found: {rel}")
                continue
            src = [l.strip() for l in path.read_text(encoding="utf-8-sig").replace("\r", "").split("\n")]
            pos = 0
            for line in (l.strip() for l in body.split("\n")):
                try:
                    pos = src.index(line, pos) + 1
                except ValueError:
                    problems.append(f"{name}: {rel}: line not found or out of order: {line[:70]}")
                    break
            checked += 1
    print(f"snippets checked: {checked}")
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("all snippets match the source")


if __name__ == "__main__":
    main()
