# Agent directives: which tool reads which file

`AGENTS.md` is the top directive (the Ormod:Directive Modding master prompt with the standards' working rules merged in). Edit only that file.

| Tool | Reads | How |
|---|---|---|
| Codex, Cursor, GitHub Copilot, Windsurf, JetBrains Junie, Zed, Aider and other AGENTS.md-aware tools | `AGENTS.md` | Natively, from the repository root |
| Claude Code | `CLAUDE.md` | The file is one line, `@AGENTS.md`, which imports `AGENTS.md` |
| Gemini CLI / Antigravity | `.gemini/settings.json` | `context.fileName` lists `AGENTS.md` (the tool reads `GEMINI.md` by default) |
| JetBrains AI Assistant | `.aiassistant/rules/ormod-directive.md` | Generated copy of `AGENTS.md`; no import is available |

Sources: the agents.md convention and third-party guides to agent configuration files (searched 2026-10-18). Those guides disagree in places and tools change, so verify each tool once in your own setup.

## Adopting it in a project
1. Copy the contents of this pack into the project root, merging folders. If the project already has a `CLAUDE.md`, replace it: the four guidelines it carried are now inside `AGENTS.md` (Notes).
2. Run `.\scripts\check-agent-directives.ps1 -Fix`, then `.\scripts\check-agent-directives.ps1`: it must print `OK`.
3. Commit `AGENTS.md`, `CLAUDE.md`, `.gemini/`, `.aiassistant/`, `scripts/check-agent-directives.ps1` and `docs/`.

## Changing the directive
Edit `AGENTS.md`, run the script with `-Fix`, run it again without, commit. Never edit the generated copy.

## Not covered
Cline, Continue, Roo and similar tools: I could not confirm which file they read, so no adapter exists for them. Add one to the check script when needed rather than copying by hand.
Not tested inside any of these tools; the check script itself was tested (edited copy, missing import, wrong Gemini setting and CRLF line endings are all handled).
