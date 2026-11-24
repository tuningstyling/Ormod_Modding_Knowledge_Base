# Heechee mod standards

Rules for every current and future Heechee BepInEx project (Bag/Clothing/AmmoCrate/Magazine X, Slot Guard and what follows).
They come from problems already hit in the game; each rule says where it came from.

## 1. Project layout
`<Name>.csproj`, `src/`, `presets/`, `scripts/build.ps1`, `tests/`, `docs/` (`PROJECT_STATUS.md`, `TEST_PLAN.md`, `NEXUS_DESCRIPTION.txt`), `workshop/` (Steam Workshop option, section 8), `reference/` (game sources and asset dumps the
mod relies on), `README.md`, `CHECKSUMS.sha256`. Plugin GUID, assembly and namespace all equal the project name. BepInEx 6, `netstandard2.1`, Harmony patches only,
no game files modified. Startup always logs one line: name, version and the settings in effect.
`tests/` may contain C# stand-ins (`stubs.cs`). Every `.csproj` therefore excludes them and the reference sources from the plugin build with `<Compile Remove="reference\**\*.cs" />` and `<Compile Remove="tests\**\*.cs" />`, and the static validator asserts both lines. Reason: the SDK compiles `.cs` files recursively, so `stubs.cs` (which defines its own `BepInPlugin` and `BaseUnityPlugin`) ended up inside the plugin DLL, BepInEx 6 did not recognise the plugin and never loaded it (Instant Crafting X 1.0.0; the build showed CS0436 warnings).

## 2. Changing item data (capacity, size, stats)
- **Scale from the remembered vanilla value per item ID, never from the current value.** Item instances are cloned from prefabs that were already changed, so
  "current x multiplier" compounds. (AmmoCrateX / MagazineX.)
- **Cover prefabs and instances.** Server code often reads `entity.EntityPrefab`, the UI reads instances. Use several routes together: a postfix on `Initialize`
  (never inlined), a postfix on the getter (the JIT may inline it) and a periodic scan of loaded objects.
- **Log each change once** (`item: old -> new`), so a first run shows what actually happened. Make it configurable.
- Clamp to `int.MaxValue`; never decrease a value unless the mod is meant to.

## 3. Changing container layouts (bags, clothing, anything that edits `ContainerVolume`)
Items are saved by absolute grid position (`StoragePosition`), so moving or removing a cell strands whatever is stored there.
- **Layouts must be stable between releases.** Pin every known layout x setting in a fixed rules table, plus a layout revision number. A planner is only the fallback
  for layouts that have no rule. Never change an existing rule's cell positions in a later version.
- **Only grow.** A new layout must contain every cell of the vanilla layout, except where a hard limit (such as the 5-column cap) forces otherwise; list those cases in the README.
- **Cache the transformed layout** per signature and setting, and return fresh objects on every call.
- **Install the companion:** `Heechee_SlotGuard` must be recommended in the README, and the plugin declares it as a soft dependency and calls
  `SlotGuardCheck.WarnIfMissing` (see `snippets/SlotGuardCheck.cs`). If a release changes any layout, the release notes say so and tell players to empty affected containers first.

## 4. Companion plugin: Heechee_SlotGuard
One copy protects every mod, present and future, because it patches the game rather than any mod:
- `InventoryItem.Refresh`: an item stored in a cell that does not exist no longer throws. It is hidden for that refresh (or dropped with `DropOrphans = true`) and logged once with item, container, container type, grid and position.
- `InventoryItem.Initialize`: clearing an old grid that has gaps no longer throws when the grid is rebuilt for a new size.
Coverage: every container the game builds with `InventoryItem` - bags (BagSizeX), clothing (ClothingSizeX), lockers, loot and nearby containers.
Mods that do not touch grids (AmmoCrateX, MagazineX) need nothing from it.

## 5. Validation and honesty
- Copy the game sources and asset dumps the mod depends on into `reference/`; `tests/` checks the mod's assumptions against them (names, signatures, the exact lines being relied on).
- Never claim a mod is tested in-game unless it has been. State "not compiled / not run in-game" in the README until it has, and keep `docs/TEST_PLAN.md` as the gate.
- Report unknowns plainly (which game class was not supplied, which hook is inferred) and say what log line or file would settle each.
- Tests must not depend on the machine's culture (decimal separator): format numbers with the invariant culture. When a .NET SDK is available, run `dotnet build --no-restore` and treat CS0436 and other warnings as findings.

## 6. Release hygiene
Bump the version in `.csproj` and the plugin attribute together. Regenerate `CHECKSUMS.sha256`. Keep presets for every supported setting. Do not rebuild a project from
older source than the one players are running; ask for the current `src/` first.

## 7. Nexus Mods description
Every project carries `docs/NEXUS_DESCRIPTION.txt`: BBCode for the Nexus editor with exactly four sections (Description, Installation instructions, Main features, Requirements),
each heading as `[size=4][b]...[/b][/size]` and each body wrapped in `[size=3][color=#D4D4D8]...[/color][/size]`. Lists use `[list]` / `[list=1]` (Nexus has no tables).
It describes only what is true of the release being uploaded, names every companion mod under Requirements and never claims testing that has not been done.
A copy is kept outside the repo as `<Name>_Nexus_Description.txt`. Update it with each release that changes features, settings or requirements.

## 7. Nexus Mods description (new projects from now on)
Every new project ships a Nexus Mods description as BBCode in `docs/NEXUS_DESCRIPTION.txt`, included in the project zip and git repo, plus a standalone copy
`<Project>_Nexus_Description.txt` delivered next to the zip. Exactly four sections, in this form:

    [size=4][b]Description[/b][/size]
    [size=3][color=#D4D4D8]...[/color][/size]

Sections: Description, Installation instructions, Main features, Requirements. Body text sits in the `[size=3][color=#D4D4D8]` wrapper; lists use `[list]` / `[list=1]` with `[*]`
(Nexus BBCode has no tables). Installation covers BepInEx 6 (Unity Mono), linked as `[url=https://www.nexusmods.com/ormoddirective/mods/6]BepInEx 6 BE788[/url]`, the `BepInEx\plugins\<Name>` folder, the generated `.cfg` and uninstalling. The game is named "ORMOD: Directive Playtest". Describe only what the mod is known to do, mention
known limits and recommended companions (for grid mods: Heechee_SlotGuard), and leave out version numbers. Existing projects were done offline and are not repacked.

### Footer (appended verbatim to the bottom of every Nexus description)
After the Requirements section, every description ends with the block below (a blank line between it and the section above). It is the author's text; the only change is the
closing order of the last paragraph, which was `[/size][/b][/color]` for tags opened as `[b][size=3][color=#ff7700]` and is now `[/color][/size][/b]`. Tags must always close in the reverse order they were opened.
Generated descriptions are checked for balanced and correctly nested `b`, `size`, `color`, `url`, `center`, `img` and `list` tags before delivery.

    [color=#00ffff][size=4][b]Shout out to DDrX for all the help and support :)[/b][/size][/color]

    [color=#555555]────────────────────────────────────────[/color]

    [color=#00ff00][size=3]And if you would like this mod to be tested fully for self and dedicated server implementation, or if you just like this mod, buy me a coffee - that will enable me to get a server for testing and motivate me to make more :)[/size][/color]

    [b][color=#00ff00][size=3]Buy me a coffee link:[/size][/color][/b]
    [center][url=https://ko-fi.com/D1D41Y3XDS][size=5][color=#00ff00]https://ko-fi.com/D1D41Y3XDS[/color][/size][/url][/center]
    [center][url=https://ko-fi.com/D1D41Y3XDS][img]https://i.imgur.com/K14I4E0.png[/img][/url][/center]

    [color=#555555]────────────────────────────────────────[/color]

    [b][size=3][color=#ff7700]Do not reupload, redistribute, or claim this work as your own.

    Respect the time and effort that went into making it (because it was a stupid amount).

    Modders are like "Scrubbing Bubbles" - We work hard so you don't have to.

    Our work is a passion project. We invest a proverbial TON of time and heartbreak, stress, and frustration into this.

    So please don't be a jackass and steal our work.[/color][/size][/b]

## 8. Steam Workshop option (every project, current and future)
Every mod must be convertible into a Steam Workshop item without touching its code: the Workshop item carries the same plugin DLL as the Nexus download.
The game has no Workshop today (only its developer can enable one), so the option is prepared and tested locally and published when the Workshop exists. Background: `STEAM_WORKSHOP_PLAN.md`.

**Conversion rule (BepInEx plugin -> Workshop item).** The item's content folder is exactly `plugins\<Name>.dll` plus `heechee-mod.json` (schema, guid, name, version, dll, requires, recommends).
That is also the layout `BepInEx.MultiFolderLoader` expects. BepInEx itself cannot be delivered through the Workshop, so players still install BepInEx 6 manually.

**Every project has a `workshop/` folder** (copy of the template, one per project, same scripts everywhere):
- `workshop.json` - name, guid (equal to the DLL name), title, `appId` (placeholder `REPLACE_WITH_GAME_APP_ID` until the Workshop exists), visibility (first upload hidden = 2), `requires`, `recommends`, `tags`. No credentials, ever.
- `WORKSHOP_DESCRIPTION.txt` - Steam markup (`[h1]`, `[b]`, `[list]`/`[olist]`, `[url]`, `[hr][/hr]`; no `size`/`color`), generated from the same content as the Nexus description, with the Workshop install steps (BepInEx, Heechee Workshop Loader, subscribe, start twice) and the footer. Placeholders start with `REPLACE_`.
- `preview.png` - under 1 MB; a generated placeholder until real art exists.
- `package-workshop.ps1` - reads the version from the `.csproj`, builds (unless `-SkipBuild`), validates, stages `staging\content\plugins\<Name>.dll` + `heechee-mod.json` + preview; `-InstallToWorkshopFolder` installs a `local-<Name>` copy for testing without a Workshop.
- `upload-workshop.ps1` - writes the SteamCMD VDF (absolute forward-slash paths, escaped text) and runs `steamcmd +login <user> +workshop_build_item`; refuses placeholders and a non-numeric App ID unless `-DryRun`; saves the new item ID to `PublishedFileId.txt` (committed) so later runs update the same item.
- `README.md`, `.gitignore` (`staging/`).
The VDF cannot set tags or required items: set them on the item page after the first upload (required items: Heechee Workshop Loader, and Heechee Slot Guard where `recommends` lists it).

**Loader.** Workshop downloads land in `steamapps\workshop\content\<AppID>\<ItemId>\`, which BepInEx does not read. `Heechee_WorkshopLoader` (separate project, Nexus-only, exempt from having its own `workshop/` folder because it must already be installed) copies each subscribed Heechee mod to `BepInEx\plugins\HeecheeWorkshop\<guid>\`, skips a mod that already exists elsewhere in `BepInEx\plugins`, removes it on unsubscribe, and needs one restart after a change. Alternative: `BepInEx.MultiFolderLoader` (documented for BepInEx 5.3+, unverified on BepInEx 6).

**Rules.** The plugin guid, project name and DLL name are identical. Version numbers live only in the `.csproj` and the plugin attribute (the scripts read the `.csproj`). Descriptions never ship with a `REPLACE_` placeholder. Mods that change item or grid data repeat "same version for everyone" for multiplayer. Existing projects adopt the option by copying the `workshop/` folder from the prep zip.

**New-project checklist (in addition to sections 1-7):** `workshop/` generated and dry-run tested (`package-workshop.ps1 -SkipBuild`, `upload-workshop.ps1 -DryRun`); Steam description checked for balanced tags; preview present; `recommends` filled (grid mods recommend Slot Guard); both descriptions (Nexus and Workshop) delivered with the project.

## 9. Working rules for coding work (from the user's CLAUDE.md)
These guidelines bias toward caution over speed; for trivial tasks use judgment. They apply to every project, current and future.

1. **Think before coding.** State assumptions explicitly; if uncertain, ask. If several interpretations exist, present them instead of picking silently. If a simpler approach exists, say so and push back when warranted. If something is unclear, stop, name what is confusing and ask.
2. **Simplicity first.** Write the minimum code that solves the problem. No features beyond what was asked, no abstractions for single-use code, no configurability that was not requested, no error handling for impossible scenarios. If 200 lines could be 50, rewrite.
3. **Surgical changes.** Touch only what the request needs. Do not improve adjacent code, comments or formatting; do not refactor what is not broken; match the existing style. Mention unrelated dead code instead of deleting it. Remove only the imports, variables and functions that your own change made unused. Every changed line must trace to the request.
4. **Goal-driven execution.** Turn each task into verifiable goals ("add validation" becomes "write tests for invalid inputs, then make them pass"; "fix the bug" becomes "reproduce it in a test, then make it pass"). For multi-step tasks, state a short plan with a check per step: `1. [step] -> verify: [check]`.

How this meets sections 1-8: optional settings, extra hooks and extra files are proposed first and added only when asked; projects the user maintains offline are not repacked or edited unless asked; and a task is reported done only with the check that was actually run, saying plainly what could not be checked.

## 10. Mod-making expert role and code review procedure
Used for both modes of work on Ormod Directive mod projects: **authoring** (new mods and changes) and **review** (an existing script or project).

**Role.** You are an expert C# mod developer with extensive experience in Unity and in making mods for it (here: BepInEx 6 plugins with Harmony patches). Make and review mod code thoroughly and constructively, looking for improvements in design, performance, readability, maintainability, adherence to best practices, Unity conventions and mod making.

**Feedback includes**
- an explanation of any issues or potential bugs;
- suggestions to improve code structure and organization;
- recommendations for optimizing performance within Unity's environment;
- best practices specific to C# and Unity (naming conventions, component usage, memory management and so on);
- any security or scalability considerations.

**Reasoning first.** Before giving conclusions, reason through each part of the code and explain the thought process. Offer examples or code snippets where they help.

**Steps**
1. Read and understand the Unity C# script or project provided.
2. Identify code smells, inefficiencies and common anti-patterns.
3. Evaluate naming conventions, style consistency and readability.
4. Assess performance implications in the Unity context.
5. Suggest improvements and best practices, citing the reasoning.
6. Summarize key takeaways and actionable points.

**Output format (review).** A structured document with: an overview or summary; detailed comments organized by code section or file; concrete examples or corrected snippets; final recommendations as bullet points. Tone: professional, constructive and educational, aimed at improving the developer's Unity C# mod-making code quality.

**How this combines with sections 1-9**
- Section 9 still governs. A review is a document: findings and suggested snippets, with no edits to the code under review unless the user asks (surgical changes). In authoring mode, write the minimum code that solves the request and give short reasoning notes: assumptions, alternatives considered, the check that was run.
- The review categories map to what this mod family has already hit; look for these first:
  - *Design and structure:* patch classes stay thin; logic that needs no game types lives in its own file so it can be tested (`SortPlanner`, `WorkshopSync`); settings are bound once in the plugin class.
  - *Performance (Unity):* no allocations or scans in per-frame paths or in postfixes on frequently read getters; cache `FieldInfo`/`MethodInfo` in `static readonly` fields; throttle scans (every 3 s at start, then every 15 s) and avoid `FindObjectsOfType` in `Update`; spread bulk work across frames (`MovesPerFrame`); remember that the JIT can inline small getters, so a getter patch is a best-effort route and needs a second route (`Initialize` postfix, periodic scan).
  - *Memory management:* bounded caches; `ConditionalWeakTable` for per-object state; unpatch in `OnDestroy`; no static references to scene objects; use `== null` (Unity's overload) on `UnityEngine.Object`, not `?.`.
  - *Correctness of data changes:* scale from the remembered vanilla value (section 2); containers only grow (section 3); patches never break the original method (`try/catch`, log once, finalizers restore state).
  - *Naming and conventions:* PascalCase types and methods, `_camelCase` private fields (the game's style), `internal` by default, namespace equal to the project name, Harmony conventions (`Prefix`/`Postfix`/`Finalizer`, `__instance`, `__result`, `__state`, parameter names that match the target).
  - *Security and scalability:* validate any external string used in a path (the loader's GUID pattern), no network calls or credentials, same settings for host and clients in multiplayer, and watch nested loops over large inventories.

## 11. Agent directives: the master prompt as top directive in git (every project, current and future)
The Ormod:Directive Modding master prompt (with the section 9 and 10 rules merged in) is the top-level directive for every AI agent and IDE assistant that works in a project. It lives in git, in the project root, and takes precedence over any other instruction file.

- `AGENTS.md` - the master prompt, the only file edited by hand. Read natively by Codex, Cursor, GitHub Copilot, Windsurf, JetBrains Junie, Zed, Aider and others that follow the AGENTS.md convention.
- `CLAUDE.md` - one line, `@AGENTS.md` (Claude Code imports it). Replace an older `CLAUDE.md`; its guidelines are already inside `AGENTS.md`.
- `.gemini/settings.json` - `context.fileName` includes `AGENTS.md` (Gemini CLI reads `GEMINI.md` by default).
- `.aiassistant/rules/ormod-directive.md` - a generated copy for JetBrains AI Assistant, which has no import. It is the only duplicate and is produced by the script, never edited.
- `scripts/check-agent-directives.ps1` - verifies all of the above (ignoring line endings); `-Fix` regenerates the copy. Run it after every edit of `AGENTS.md`, before committing.
- `docs/HEECHEE_MOD_STANDARDS.md` and `docs/AGENT_DIRECTIVES.md` - the standards the prompt refers to, and which tool reads which file.

Rules: a new project is not done until these files are in its root and the check script prints OK; no other tool-specific copy of the prompt is added without a reason (duplicated instructions load twice and drift); when a tool needs its own file, add it to the check script instead of copying by hand. Tool support changes: re-verify the table in `docs/AGENT_DIRECTIVES.md` when adding a tool.

## 12. Splitting a mod
When a project is split into several mods: the original is version-bumped and loses the moved code together with its reference sources, tests, documentation and Nexus/Workshop text; each new project is a complete project (sections 1-11) at 1.0.0; helper files shared by the new mods are kept byte-identical apart from the namespace and are named in both READMEs; each description points to its companion mods; and the split is recorded in each project's status file. A split never changes behaviour silently: the README says which mod now carries which behaviour.

## 13. Delivering changes to released projects
Every project delivered so far is already released in the user's local git, so a change is delivered as a change set, not as a re-packed project.
- **Change set:** only the files that changed (full contents, repository paths preserved) and one unified diff per project (`<Project>_<old>_to_<new>.patch`, `git apply` compatible, deletions included) against the last version delivered. Unchanged files are not delivered.
- **What counts as changed:** everything the change touched, including derived files: the version in the `.csproj` and the plugin, README, status and test plan, the Nexus and Workshop descriptions, and `CHECKSUMS.sha256` (regenerated, delivered as a changed file). Binary files such as `preview.png` are delivered as files, not diffs.
- **Full zips** are only for new projects and mods (sections 1-11 apply to them in full).
- **Exactness:** a baseline copy of the project is taken before editing so the diff is exact; the working copy then becomes the new baseline. If the user's local git differs from the last delivered version (offline edits), the changed files are the safe route and the user says what differs.
- **Old zips** of a project that has since changed are stale; they are not re-issued.
