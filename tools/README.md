# Tools

Two small Python 3 scripts, no dependencies.

- `snippet.py` prints a verbatim, correctly formatted code snippet from a mod's source file, ready to paste into the tutorial. Quoting by tool, not by hand, is what keeps the tutorial true.
- `verify_snippets.py` re-checks every quoted snippet against the current source. Run it after any code change; a failure means a snippet (and its explanation) needs updating.

`--root` is the folder that holds the `Heechee_*` project folders (for example `D:\Heechee\Git\Ormod-Directive`). See `../UPDATING.md` for when to use them.
