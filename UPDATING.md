# Updating this knowledge base

This repository is only useful while it stays true and grows with every mod. **Every change set that adds a mod, a game fact or a fixed bug also updates the knowledge base**, in the same commit. This file is the procedure. (It is also section 14 of `ai_prompts/HEECHEE_MOD_STANDARDS.md`, so assistants that follow the standards follow this.)

## 1. When to update

| Event | What to add |
|---|---|
| A **new mod** is built | a tutorial chapter (or a section in an existing chapter), the mod in the README table, Notes entries for anything learned, Internals rows for every game member it touches, a changelog line |
| A **bug** is found and fixed | a Notes entry with its *diagnostic signature* (what the log or screen showed), the cause, the rule; a Dead-ends item if a first theory was wrong |
| A **new game source file** is supplied | Internals rows (class, member, what it is, used by); remove the item from "not seen yet" |
| A finding is **confirmed or refuted in the game** | change its label ([TESTED] to [IN-GAME] or [FAILED]) |
| The **game updates** | run each mod's static validator against the new reference files; update Internals rows that changed; note it in the changelog |
| A **process** problem happens twice | a Process rule (Part I) |
| A **new AI prompt, template or habit** proves useful | `Ormod_AI_Agent_Knowledge.md` and, if it is a standing rule, `ai_prompts/` |

## 2. Labels (be honest)

- **[IN-GAME]** the author saw it in the game (say what was seen). **[TESTED]** checked against the game's source files and a test harness, not yet seen in the game. **[FAILED]** tried, did not work (keep it: dead ends save time). **[ASSUMED]** reasoned only. **[OPEN]** a question with a named missing file or test.
- Never promote a label without evidence from the game. A screenshot or a log line is evidence; a successful build is not.
- Specific class names are worked examples of techniques (the *generalization rule*): write the lesson so it applies to any Unity game.

## 3. Entry templates

**Notes entry** (`Ormod_Modding_Notes.md`, next free number in its part; **never renumber**):

```markdown
### C13. Short title **[TESTED]**
What the game does, in two or three sentences, with the exact class and member names.
**Diagnostic signature:** the log line or on-screen sign that tells you this is the problem.
**Rule:** what to do about it.
```

**Internals row** (`Ormod_Game_Internals_Notes.md`): `| Class | member | what it is, with numbers | used by |` and a label **[SRC]**, **[JSON]**, **[LIST]** or **[INFER]**. If a source file was not supplied, say so in section 6 instead of guessing.

**Tutorial snippet** (`Ormod_Mod_Tutorial.md`): create the quote with the tool, never by hand:

```
python tools/snippet.py --root <folder with the Heechee_* projects> --file Heechee_X/src/File.cs --start "first line text" --lines 20
```

then add the five parts under it: **1. What it is. 2. Purpose. 3. How it works** (statement by statement; define every term the first time). **4. Effect** (what the player or the game does differently, with its label). **5. Background** (concepts, an analogy). Write for someone new to Unity.

**Changelog line** (`CHANGELOG.md`): date, knowledge-base version, what changed, which mod versions it covers.

## 4. The checklist before you deliver an update

1. The new snippets were created with `tools/snippet.py`.
2. `python tools/verify_snippets.py --root <folder> Ormod_Mod_Tutorial.md` prints "all snippets match the source".
3. Every new claim has a label and, if it came from a log or screenshot, says so.
4. The README table and the contents lists mention the new mod or part.
5. Version and date in `CHANGELOG.md`; `CHECKSUMS.sha256` regenerated **last**.
6. Delivered as **changed files plus a patch** (`git apply --check` passes), not as a new zip.

## 5. A prompt block to give an AI assistant

> After the code change is done, update the Ormod knowledge base as described in `UPDATING.md`: add or change the Notes entries (with diagnostic signatures and honest status labels), the Internals rows for every game member used, a tutorial section with verbatim snippets made by `tools/snippet.py` and the five-part explanation, the README table, and a changelog line. Run `tools/verify_snippets.py`. Do not change a status label without evidence from the game. Deliver changed files and a patch.
