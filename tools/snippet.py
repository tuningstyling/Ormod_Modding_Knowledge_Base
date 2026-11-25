#!/usr/bin/env python3
"""Print a verbatim code snippet from a mod's source file, formatted for the tutorial.

Usage (from the knowledge base folder):
  python tools/snippet.py --root D:\\Heechee\\Git\\Ormod-Directive --file Heechee_ExtraMusic/src/MusicWindow.cs --start "internal void Tick()" --lines 22
  python tools/snippet.py --root ... --file ... --start "private bool EnsureSource()" --end "return true;"

--root   the folder that contains the Heechee_* project folders
--start  text of the first line of the snippet (first line that contains it)
--lines  number of lines to take, or --end: the text of the last line (first later line that contains it)
The output is the markdown to paste into Ormod_Mod_Tutorial.md. Indentation is removed evenly; nothing else is changed.
"""
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--file", required=True, help="path relative to --root, with forward slashes")
    p.add_argument("--start", required=True)
    p.add_argument("--lines", type=int)
    p.add_argument("--end")
    a = p.parse_args()
    if (a.lines is None) == (a.end is None):
        p.error("give exactly one of --lines and --end")
    lines = (Path(a.root) / a.file).read_text(encoding="utf-8-sig").replace("\r", "").split("\n")
    i = next((k for k, l in enumerate(lines) if a.start in l), None)
    if i is None:
        raise SystemExit(f"start text not found in {a.file}")
    if a.end is not None:
        j = next((k for k in range(i, len(lines)) if a.end in lines[k]), None)
        if j is None:
            raise SystemExit("end text not found after the start line")
        chunk = lines[i:j + 1]
    else:
        chunk = lines[i:i + a.lines]
    pad = min((len(l) - len(l.lstrip()) for l in chunk if l.strip()), default=0)
    body = "\n".join(l[pad:] for l in chunk).rstrip()
    print(f"*Source: `{a.file}`*\n\n```csharp\n{body}\n```")


if __name__ == "__main__":
    main()
