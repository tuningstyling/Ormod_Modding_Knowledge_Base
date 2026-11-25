# Ormod Modding Knowledge Base

Notes, a tutorial and an AI-agent guide for making **BepInEx 6 / Unity** mods for **ORMOD: Directive Playtest**, written from the work on twelve real mods. It is modelled on the structure of the [Windrose UE4SS Modding Notes](https://github.com/dgomiller/Windrose-UE4SS-Modding-Notes) (a README index, a numbered notes file, an engine-internals file, recorded dead ends), with two additions: a teaching tutorial that explains every code snippet, and the AI prompts and working rules used to produce the mods.

> **How reliable is it?** Every finding carries a status: **[IN-GAME]** (the author saw it work or fail), **[TESTED]** (checked against the game's source files and a test harness, not yet reported from the game), **[FAILED]**, **[ASSUMED]**. The mods were written without access to the game or the .NET SDK; only the author's game sessions can promote a finding to [IN-GAME]. Where a guess was wrong, the notes say so.

## What is here

| File | What it is | Read it when |
|---|---|---|
| [`Ormod_Mod_Tutorial.md`](Ormod_Mod_Tutorial.md) | Eleven chapters (the last one is worked examples). Each code snippet (copied verbatim from a real mod) is followed by *what it is, purpose, how it works, effect in the game, background concepts* | you are new to Unity or to this game |
| [`Ormod_Modding_Notes.md`](Ormod_Modding_Notes.md) | Numbered findings in parts A to H: setup, Harmony patterns, game systems, audio and IMGUI, testing, dead ends, releasing, open questions | you hit a problem or start a new mod |
| [`Ormod_Game_Internals_Notes.md`](Ormod_Game_Internals_Notes.md) | A reference of the game's classes, fields and facts the mods rely on, plus "which files to ask for" per kind of mod | you need an exact member name |
| [`Ormod_AI_Agent_Knowledge.md`](Ormod_AI_Agent_Knowledge.md) | The standing rules, the working procedure, prompt templates, habits, and the agent prompts embedded verbatim | you brief an AI assistant |
| [`UPDATING.md`](UPDATING.md), [`CHANGELOG.md`](CHANGELOG.md), [`tools/`](tools/) | how to keep this repository current with every new mod and finding; what changed; the snippet and verify scripts | you finish a mod or find something out |
| [`ai_prompts/`](ai_prompts/) | The master prompt (`AGENTS.md`), adapters for each AI tool, the review-role addendum, the mod standards, the directive check script | you set up a repository or an agent |

## The mods behind the notes

| Mod | What it does | Where to read about it |
|---|---|---|
| Bag Size X | bag grid x2 to x10 and carry capacity (source held by the author) | Notes C2 |
| Clothing Size X | clothing grids and layouts | Notes C1, C2; Tutorial ch. 4 |
| Ammo Crate X | crate capacity per caliber; fixes a vanilla inspect-menu bug | Tutorial ch. 3; Notes C3 |
| Magazine X | magazine capacity by percent | Tutorial ch. 3; Notes C4 |
| Slot Guard | stops an orphan item from breaking the inventory | Tutorial ch. 4; Notes C1 |
| Sort X | F6 sorts bags and clothing | Tutorial ch. 4 |
| Workshop Loader | loads Steam Workshop items into BepInEx (Nexus only) | Notes G2 |
| Instant Crafting X | recipe times | Tutorial ch. 5; Notes C5 |
| Instant Harvesting X | trees, ore, scrap, bushes, water filling, fire lighting | Tutorial ch. 5; Notes C6, C7 |
| Instant Packing | packing with the Crafting Kit | Tutorial ch. 5; Notes C7, C9 |
| Instant Workbenches | workbench production (powered and unpowered) | Tutorial ch. 6; Notes C8 |
| Extra Music | your own `.ogg` music in the game's rotation, title screen and pause menu, with an in-game player | Tutorial ch. 7 to 8; Notes C10 to C12, D |

## Using it

1. Read **Tutorial chapter 0** if Unity, BepInEx or Harmony are new to you.
2. Start a project from the layout in Notes A5 and the `.csproj` lines in Tutorial chapter 2.
3. Before you patch a game method, find it in `Ormod_Game_Internals_Notes.md`; if it is not listed, **get the source file first**.
4. Build the validator and stand-ins before the mod (Notes part E), so the first failure you see is a test, not a crash.
5. For AI help, give the assistant `ai_prompts/AGENTS.md` and the standards, and use the templates in `Ormod_AI_Agent_Knowledge.md`.

## Provenance and credits

- The findings come from the real build and test sessions of the Heechee mods (BepInEx 6 BE788, Unity 2022.3.21). The code quoted in the tutorial is copied from those mods by a script, not retyped.
- Structure and spirit: *Windrose UE4SS Modding Notes* by dgomiller. The README and the notes file were read online (the notes file only in part, because of a fetch limit); the companion *Windrose Unreal SDK Notes* were then supplied as a file and read, which added the preface, the four milestones, the process rules and the worked examples.
- **License:** not set. The author should choose one (the Windrose notes use CC0). Game names and assets belong to their owners; the notes contain no game assets, only class and member names and short quotations needed for explanation.
