# Ormod Modding Notes

Hard-won findings from building twelve BepInEx 6 mods for **ORMOD: Directive Playtest** (Unity 2022.3.21, Mono, `netstandard2.1`). The structure follows the Windrose UE4SS notes that inspired this repository: numbered findings, grouped into parts; each says what happens, what the rule is, and what the failure *looks like* in a log, so you can recognise it. Dead ends are recorded on purpose.

**Status labels:** **[IN-GAME]** the author reported it working or failing in the game. **[TESTED]** verified against the game's source files and in a test harness; not yet reported from the game. **[FAILED]** tried and did not work. **[ASSUMED]** reasoned, not verified.

**Why this exists.** A mod author who is new to a game spends most of the time not on the code but on finding out *which* number, field or method matters, who reads it, and why the first attempt does not work. These notes keep that knowledge so it is paid for once.

**Generalization rule** (borrowed from the Windrose notes). A class or field name in an example is a worked example of a *technique*, not a project-specific detail. "Make the crafting time 0.001" teaches "find who divides by the time and give it a safe tiny number" and applies to any timer in any Unity game.

**How to search.** These files are plain markdown; search for a heading's exact wording (for example `A3.` or `D9.`) to jump to it. Findings keep their numbers when new ones are added, so references stay valid.

**Four milestones, kept separate.** A mod can (1) *load* (a log line from `Awake`), (2) *patch* (Harmony installs and the patched method runs), (3) *behave* (the game does the new thing), (4) *feel right* (no side effects, correct in multiplayer, nice UI). Progress through them is not a smooth slope; each has its own diagnostic and its own test. Many entries below say which milestone failed.

**Honesty note.** The environment these mods were written in has no game, no Unity editor and no .NET SDK. Almost everything marked [TESTED] was verified with source files, stand-in classes and a compile-and-run harness. Only the author's own testing in the game can promote an item to [IN-GAME]. Where the author reported a problem, the fix and its cause are written down here.

## Contents

- **Part A. Project setup and build** (A1 to A8)
- **Part B. Harmony and reflection patterns** (B1 to B9)
- **Part C. Game systems** (C1 to C12)
- **Part D. Audio and in-game UI (IMGUI)** (D1 to D12)
- **Part E. Testing without the game** (E1 to E6)
- **Part F. Dead ends and corrected beliefs**
- **Part G. Releasing and delivering changes** (G1 to G8)
- **Part H. Open questions**
- **Part I. Process rules** (flat rules from real mistakes)

---

# Part A. Project setup and build

### A1. A mod is a BepInEx 6 plugin DLL **[IN-GAME]**
The game folder (`...\Signal Decay Playtest\`) contains the game `.exe`, `ORMOD Directive Playtest_Data\` (with `Managed\` holding the game's DLLs) and `BepInEx\`. A mod is one DLL (plus optional content) in `BepInEx\plugins\<ModName>\`. Target `netstandard2.1`, language `latest`, nullable off. BepInEx is BE build 788 (Nexus mod page 6 for this game).

### A2. The references a plugin needs **[TESTED]**
`BepInEx.Core`, `BepInEx.Unity.Mono`, `0Harmony` (from `BepInEx\core`), `Assembly-CSharp`, `Mirror` (the multiplayer library; needed as soon as you name a class derived from `NetworkBehaviour`, such as `WeatherController`) and the Unity modules you use. Mark every reference `<Private>false</Private>`. For audio and UI the modules are `UnityEngine.CoreModule`, `AudioModule`, `IMGUIModule`, `InputLegacyModule`, `UnityWebRequestModule` and `UnityWebRequestAudioModule`; all of them exist in the game's `Managed` folder (check the folder listing before assuming). A mod that only needs two member names (Instant Workbenches) uses reflection and **references no game DLL at all**.

### A3. Never compile test files into the plugin **[IN-GAME]**
**What happened:** Instant Crafting X 1.0.0 did not load. `tests\stubs.cs` (fake `BepInPlugin`, `BaseUnityPlugin`) was swept into the DLL by the SDK's "compile every .cs under the folder" rule, so BepInEx did not recognise the plugin as its own. **Diagnostic signature:** no "loaded" line in the console, and build warnings `CS0436: type conflicts with imported type`.
**Rule:** every `.csproj` contains `<Compile Remove="reference\**\*.cs" />` and `<Compile Remove="tests\**\*.cs" />`, and the static validator asserts both lines. Build with `dotnet build .\X.csproj --no-restore` and treat CS0436 as an error.

### A4. One version, three places **[TESTED]**
The version lives in the `.csproj` `<Version>`, in the plugin's `PluginVersion` constant, and in the README header. A patch bumps all three. The Workshop manifest reads the csproj.

### A5. Folder layout per project **[TESTED]**
`src/`, `tests/`, `docs/` (README, PROJECT_STATUS, TEST_PLAN, Nexus text, the standards, agent directives), `reference/` (read-only copies of the game files the mod depends on), `scripts/` (build, directive check), `workshop/`, `CHECKSUMS.sha256`, and `AGENTS.md`/`CLAUDE.md` at the root.

### A6. Content next to the DLL **[IN-GAME]**
Find the plugin's own folder with `Path.GetDirectoryName(Info.Location)` (a property of `BaseUnityPlugin`). Extra Music keeps its files in `Ogg Music Files\` there. A post-build target in the csproj stages the DLL and the empty content folder into `dist\<Mod>\`.

### A7. Config entries are state, too **[TESTED]**
`Config.Bind(section, key, default, description)` creates an entry in `BepInEx\config\<guid>.cfg`. Use it for choices and for remembered state (the window size, volume). Keep the number of settings small; the standing rule is "no settings beyond what was asked", and anything extra is flagged in the README as an addition.

### A8. Identify a "did my mod load?" quickly **[IN-GAME]**
Print one `LogInfo` line from `Awake` with name, version and what it does. If that line is missing, nothing else matters yet.

---

# Part B. Harmony and reflection patterns

### B1. Prefix, Postfix, Finalizer **[IN-GAME]**
Prefix runs before and can skip the original by returning `false`; Postfix runs after; Finalizer runs even when the original threw, receives `Exception __exception` and may return `null` to swallow it (return it unchanged otherwise). `__instance` is the object; `__state` carries a value from Prefix to Finalizer; `ref` parameters let you change arguments or results.

### B2. Patch virtual or large methods, not tiny getters **[TESTED]**
The JIT may inline small methods, so a patch on them may never run for some callers. Magazine X patches `WeaponAttatchment.Initialize` (virtual) and adds a periodic scan as a backstop.

### B3. Private members through `AccessTools.Field` **[IN-GAME]**
Cache the `FieldInfo` in a `static readonly` field. Null-check it. If missing, log **once** ("X not found; the Y is unchanged") and do nothing. Silent failure is the enemy.

### B4. Scale from the remembered vanilla value **[TESTED]**
Instances are cloned from prefabs that may already be changed. "new = scale(current)" compounds; "new = scale(vanilla of this id)" is idempotent. Keep a dictionary (or `ConditionalWeakTable` for objects) of originals.

### B5. Prefab **and** instances **[TESTED]**
The server reads prefabs; the UI reads instances. Cover both: patch `Initialize`, scan periodically, and handle the data table (Ammo Crate X multiplies `ItemDatabase._ammoCrateTypes[].Max`).

### B6. The Sync pattern **[TESTED]**
For anything you add to a game list: compute a *signature*, return if unchanged, remove your own earlier entries *by reference*, add the wanted ones, remember them. Used by `RotationInjector` (game music list), `MenuInjector` (title music lists) and the Slot Guard bookkeeping. It makes reload, scene change and setting change safe.

### B7. Never write 0 where the game divides **[TESTED]**
Use `0.001` for "instant" (`BaseCraftingTime`, `_maxHarvestTime`, `_pickupTime`). Zero gives NaN progress bars or division by zero. For machine durations the safe floor is higher (A job end time is `DateTime.Now.AddSeconds(d)`; see C8).

### B8. Wrap every patch body in `try/catch` **[TESTED]**
A bug in a mod must never break the game's method. Catch, log one warning with the exception, and let the original run.

### B9. Idempotent and quiet **[TESTED]**
Log a line the first time something happens (`HashSet.Add` returns true once). A thousand identical lines hide the one that matters.

---

# Part C. Game systems

### C1. Inventory grids and orphans **[IN-GAME]**
Items store `StoragePosition` (`x,y,z`) in data tags. A container's UI has `_slots[x,y]`; a cell in a gap is `null`. If a clothing layout changes between mod versions an item can be stranded in a cell that no longer exists (an *orphan*). `InventoryItem.Refresh` then throws `NullReferenceException` and aborts `RefreshAllContainers` for every later container. **Diagnostic signature:** the inventory UI breaks; the log shows the NRE from `InventoryItem.Refresh`. **Fix:** Slot Guard (hide or drop orphans for the duration of one call). **Rule:** never change a published clothing layout silently, and never rebuild a project from older sources than the ones players run (Clothing Size X 1.0.4 layout differs from the 1.0.0 in this repository, on purpose left as is).

### C2. Bag and clothing grids have a 5-cell width cap **[TESTED]**
Bag Size X widens grids 2x/3x/5x/7x/10x and carry capacity; it uses 11 pinned layouts plus a fallback planner and caps width at 5 cells; two vanilla 6-wide layouts are narrowed to 5 columns. The source of Bag Size X is held by the author, not in this repository's output folders.

### C3. Ammo crates: a table, not an item **[IN-GAME]**
`ItemDatabase._ammoCrateTypes[]` holds capacity per caliber (`Max`): .45 240, 9x19 240, 5.7x28 240, 5.45x39 180, 9x39 180, 7.62x51 120, 7.62x54 60, 12ga 40. The item `ammo_crate` has `Magazine.MaxAmmo` too; a loaded crate displays its caliber's `Max`. Vanilla bug: a crate with rounds but no `CurrentBullet` tag makes `InventoryInspectMenu.SetActiveButtons` throw `KeyNotFoundException: 'CurrentBullet'`.

### C4. Magazines **[TESTED]**
`_catagory` (sic) equals `"Magazine"` for magazines; `MagazineData.MaxAmmo` is a public int. Exclude ammo crates. Allowed boosts 15/30/50/75/100/200 percent.

### C5. Recipe times **[IN-GAME for inventory combine]**
`CraftingManager.Start` builds a per-player `Recipes` list; set `BaseCraftingTime = 0.001` and `CraftingTimeIncrease = 0`. The wait is a client timer in `InventoryUIController.WaitCraft`; `CraftServer`/`CraftItem` never read it. `CraftButton` is a spinning marker only; `CraftableItem.CraftItem` crafts at once.

### C6. Harvesting **[TESTED]**
`HarvestingManager.DoTick` owns `_maxHarvestTime` and `_currentHarvestTime` (shared with crafting). `HarvestableType` = Tree, Ore, Scrap, Bush. Swing-based harvests subtract about `3.6 * damage / 100` per swing. Public `IsHarvesting` and `IsCrafting` separate the two uses.

### C7. One shared timer for packing, filling and fire **[TESTED]**
`PlayerInventory.GetInput` sets `_isPackingWorkbench = true` at four start sites (packing twice, water fill, fire lighting) and counts `_pickupTime` down from `_currentMaxPickupTime`. The *completion* code decides which action ran by the equipped item: ID contains `empty`/`unpurified` = fill; `ItemName == "Crafting Kit"` = pack (`PackEntity`/`PackWorkbench`); else = fire. Two mods that share the timer must classify the same way.

### C8. Workbench production is a server rule **[TESTED]**
All 16 workbench production classes call `MachineController.Instance.StartProduction(id, callback, duration, type, ...)` with `duration = time * modifier / ServerSettings.Settings.<Powered|Unpowered>MachineProductionRate`. Jobs complete on the machine tick (`MachineTickRate`, 0.2 s default). `ProductionObject.completeTime = DateTime.Now.AddSeconds(time)` and `GetProductionProgress` divides by `completeTime - startTime`. Fuel burn is `_currentBurnTime`, not rate-divided. The water catcher passes duration 0 already. `ServerSettings.Settings` is a public static field replaced by `Load()`; the rates are only in `SerializedServerSettings`, so they are not saved and not sent to clients.

### C9. Unpacking is an interaction **[TESTED]**
`WorkbenchUnpack` (an `InteractableItem`) calls `ItemPlacer.Unpack*` immediately in `InteractClientSide()`; the hold time is the prefab's serialized `_interactTime` (`InteractTime`), counted down in the generic interactable branch of `GetInput` with `_isPackingWorkbench` false. Not changed by any mod yet.

### C10. Day, night, biomes **[TESTED]**
`WeatherController.Instance.IsNight` (derived from `_sunRotation`). `BiomeController.Instance.GetWeightedChanceSubBiome(position)` returns the sub-biome; its `Temperature` is the centre of its type on a 0-to-1 axis computed by `GetTemperaturePosition(type, total)` where `total = 0.12*TundraSize + 0.15*ColdSize + 0.26*TemperateSize + 0.15*WarmSize + 0.12*DesertSize` (server settings sizes).

### C11. Music systems **[IN-GAME for the in-world rotation]**
`SoundController._musicTracks` (`Music`: `Song`, `SongLength`, `IsNight`, `AvaliableInTemperatures` = (max, min)); `PlayMusic` every 600 to 1200 s; the source is `_music`; `_mixer` holds the `AudioMixer`. The main menu uses `OfflineSceneController._titleDayMusic/_titleNightMusic` (night when the current time state's `Rotatation < 0`), the AudioSource `_music`, mixer group `TitleMusic`. Mixer groups: Master, Voices, Machinery, TitleMusic, Effects, UI, Voicechat, IngameMusic, Ambient. There is no FMOD/Wwise plugin: Unity's own audio.

### C12. Player states **[TESTED]**
`PlayerStateMachine.Instance.CurrentState` (`State`: Locked, Standing, Crouching, Prone, Sitting, Placing, Inventory, Building, Trading, WeaponModifying, **Paused**, Chatting, Dead, Console) and `CurrentStateType` (`Movement`, `Override`, `Overlay`). `Paused` is an Overlay state with a free cursor and is the in-game pause menu. It is assumed (not verified) that the settings screen of a world keeps this state.

---

# Part D. Audio and in-game UI (IMGUI)

### D1. Destroyed Unity objects **[IN-GAME]**
`NullReferenceException` from `AudioSource.Stop()` means the C# variable still points at a destroyed object. Unity's `== null` returns true for it. Check before every use, recreate if needed, and put your components on an object that lives as long as your plugin (the plugin's own `gameObject`).

### D2. Loading `.ogg` at run time **[IN-GAME]**
`UnityWebRequestMultimedia.GetAudioClip(uri, AudioType.OGGVORBIS)` in a coroutine. Set `streamAudio = false` **before** `compressed = true`. Wait while `clip.loadState == Loading`. **Diagnostic signatures:** `Audio compression is not valid as streamAudio is set to true` (wrong order); `Cannot create FMOD::Sound instance for clip "" (FMOD error: Unsupported file or audio format.)` (the file is Ogg Opus/FLAC, not Vorbis).

### D3. A device change silences all audio **[IN-GAME report; fix partly known]**
The game's `SoundController.OnAudioConfigChanged(bool deviceWasChanged)` calls `AudioSettings.Reset(...)` and restarts only wind, grass, rain and birds. After a real device change every other source (the game's music, the mod's player) stays silent. If the device keeps changing, Unity logs "OnAudioConfigurationChanged is being called recursively and therefore the calls have been aborted after two recursions". **That message is the game's.** A mod can subscribe to `AudioSettings.OnAudioConfigurationChanged` and resume its own player, but the game's handler runs after the mod's (it subscribes later), so a resume must be **deferred** a frame or two. The 1.3.1 fix was written by another AI agent; its player code was not seen.

### D4. IMGUI has no text input that is safe **[ASSUMED]**
Typed characters are expected to also reach the game's key bindings (reasoned from the engine, not observed); the window avoids the question by having no text boxes. Offer buttons only. Add files by pasting from the clipboard (`GUIUtility.systemCopyBuffer`), which accepts Explorer's "Copy as path".

### D5. Do not change the control count during a frame **[TESTED]**
Run list-changing actions from `Update` via a deferred action. Otherwise: "Getting control N's position in a group with only N-1 controls".

### D6. Resizing **[IN-GAME]**
Draw a grip; capture the mouse with `GUIUtility.hotControl`; compute size from screen-space mouse movement divided by the GUI scale; clamp; apply it after `GUILayout.Window` returns (it returns the old rect); save to the config on MouseUp.

### D7. Scale the GUI for high resolution **[TESTED]**
`GUI.matrix = Matrix4x4.Scale(new Vector3(s, s, 1))` with `s = max(1, Screen.height / 1080)`. Work in "virtual 1080p units".

### D8. Columns: one set of widths for header and rows **[IN-GAME]**
Explicit widths for every column in both. Letting one column expand separately in the header and in the rows misaligns them.

### D9. Filling the remaining height **[FAILED then TESTED]**
`ExpandHeight(true)` on a scroll view (and fixing the other labels) did **not** make the list grow in a `GUILayout.Window` of forced height. Compute it: measure `GUILayoutUtility.GetLastRect().yMax` in the Repaint event, subtract the list's own height to get the other controls' height, and set `Height = window - others - padding`.

### D10. Tooltips and legends **[IN-GAME for the legend; tooltips unverified]**
`new GUIContent(text, tooltip)` and `GUI.tooltip` (read after drawing the controls) give hover text; abbreviations need a visible legend (Tu = Tundra, Co = Cold, ...). Place the legend where it does not move when the window is resized (under the list).

### D11. Close button and dragging **[drawn in-game; the click itself not reported]**
Draw an `X` with `GUI.Button` at the top-right of the window **before** `GUI.DragWindow`; the button gets the click first.

### D12. Input leaks while the window is open **[OPEN]**
User report: with the player window open the camera still turns and clicks in the window act on the player. Known so far: the game's `PlayerStateMachine` has an Overlay state `Paused` that frees the cursor, which may block camera and clicks if the code that reads them checks the state; using it from a mod would also trigger the pause-menu music path and possibly the game's own pause UI (subscribers of `StateChange` unknown). The camera and click handling sources have not been seen. See Part H.

---

# Part E. Testing without the game

### E1. Four layers **[TESTED]**
Static validator (Python) against `reference/` sources; stand-in classes; compile check (Roslyn) of the real sources against the stand-ins; compile-and-run logic tests (PowerShell 7 `Add-Type`).

### E2. Put decisions in pure classes **[TESTED]**
`SortPlanner`, `MusicLibrary`, `PlaylistOrder`, `BiomeBands`, `WindowLayout` use no game types, so they are fully tested. The thin classes that touch the game are tested against stand-ins.

### E3. Make stand-ins behave like Unity **[TESTED]**
Destroyed objects compare equal to null and throw on native calls; a `Time` with a settable `unscaledDeltaTime`; a coroutine "pump" that runs nested enumerators as Unity does.

### E4. Prove a test with the old code **[TESTED]**
After every bug fix, run the new tests against the old sources. They must fail in exactly the reported way.

### E5. Culture-independent tests **[IN-GAME]**
Format numbers with `CultureInfo.InvariantCulture`. The author's machine uses a decimal comma and needed `en-US` for the old assertions.

### E6. Honest limits **[TESTED]**
These layers cannot test real IMGUI layout, real audio, real mouse capture or the game's timing. Every project's `TEST_PLAN.md` lists what only the game can answer.

---

# Part F. Dead ends and corrected beliefs

1. **`ExpandHeight(true)` makes the list fill the window** (1.4.1) **[FAILED]**: wrong; see D9.
2. **"Stretching labels" caused the gap under the status line** **[FAILED]**: a guess from one screenshot; non-stretching labels did not help. Do not trust a layout theory without a screenshot of the next version.
3. **Rate 1,000,000 for workbenches** (1.0.0) **[CORRECTED]**: a bigger rate gains nothing (the machine tick) and risks zero-length durations. 1000 is enough.
4. **Recreating the AudioSource only** **[PARTIAL]**: it recovers, but the root cause was putting the source on a separate GameObject. Attach to the plugin's own object.
5. **Building Clothing Size X from the 1.0.0 sources** **[REJECTED]**: strands stored items; keep the author's 1.0.4.
6. **A split of "Instant Crafting" into three mods** **[DONE]**: packing, water fill and fire lighting share one timer; the classifier by equipped item is what makes two mods coexist.
7. **"Menu" means the pause menu** **[CORRECTED]**: the game's only menu music is the title screen. In-game pause music had to be built, using `State.Paused`.
8. **Assuming a convention for a missing source** **[RULE]**: when a class is not in the supplied files, ask for it. Every wrong guess in this project came from a missing file.

---

# Part G. Releasing and delivering changes

### G1. Nexus description **[IN-GAME]**
Four sections in order: Description, Installation instructions, Main features, Requirements. Body in `[size=3][color=#D4D4D8]`. Game name "ORMOD: Directive Playtest". BepInEx link `[url=https://www.nexusmods.com/ormoddirective/mods/6]BepInEx 6 BE788[/url]`. A fixed footer follows (shout-out, Ko-fi, do-not-reupload). Close tags in reverse order (`[/color][/size][/b]`).

### G2. Steam Workshop **[ASSUMED]**
The game has no Workshop; the developer would have to enable it. Placeholders (`REPLACE_WITH_GAME_APP_ID`, `REPLACE_WITH_LOADER_LINK`) mark what is missing. The loader copies subscribed items into `BepInEx\plugins\HeecheeWorkshop\<guid>\` and **removes that folder on unsubscribe**; Extra Music's music folder would be deleted, so users must back it up.

### G3. Checksums and zips **[TESTED]**
`CHECKSUMS.sha256` per project, regenerated at the end. After zipping, extract and run `sha256sum -c` against the extracted copy. (A stale preview image was once found in a zip this way.)

### G4. Released projects are never re-packed **[RULE]**
Deliver only changed files and a patch. Keep a baseline copy before editing so the diff is exact.

### G5. Verify a patch three ways **[TESTED]**
`patch --dry-run`; apply to the previous tree and `diff -r` with the new tree; `git apply --check` in a scratch repo. Generate patches with `a/` and `b/` directory prefixes and no extra flags in the header line.

### G6. Patches fail where the user's files differ **[IN-GAME]**
The README was edited locally; the whole patch failed on it. Provide a patch without the README plus the README edits as text, or a patch made against the user's own uploaded file.

### G7. Tests in a separate patch **[RULE]**
When another agent has changed the test files, a combined patch fails. Ship `..._tests.patch` separately.

### G8. Sandbox habits **[RULE]**
The working directory of the build environment can be wiped between turns. Only the output folder persists: keep deliverables and baselines there, and reinstall tools (PowerShell 7 from GitHub) when a tool is gone. The shell is POSIX `sh`, so `<(...)` process substitution does not work.

---

# Part H. Open questions

1. **Input blocking for the player window.** Camera and clicks leak. Needs: which script reads mouse look and clicks, and whether it respects `PlayerStateMachine` or `Cursor.lockState`. Candidates: switch to an Overlay state while the window is open (must avoid the pause-menu music and UI), or patch the camera and click readers to return early while the window is open.
2. **Does the in-game settings screen keep `State.Paused`?** Needed for the pause-menu music; test plan item.
3. **After an audio device change, resume the game's own music, too?** A small addition to the same handler; not built.
4. **Does a dedicated server apply the production rates through the same settings object?** The code suggests so.
5. **Coal and branches as harvestables** are not named in the supplied code; they are covered only if the game implements them as ore or bush.
6. **Unpack hold time** is prefab data (`_interactTime`); making unpacking instant needs a `WorkbenchUnpack` check after the interact start.

---

# Part I. Process rules

Flat rules, each from a mistake that cost real time in this project (the style is borrowed from the Windrose SDK notes' "cook once, edit once").

### I1. Snapshot a baseline before every edit
Copy the project before changing it, then diff against the copy. A patch made against a baseline you only remember fails on the user's machine. The edited working copy becomes the next baseline.

### I2. Never rebuild a released project from older sources
Clothing Size X: rebuilding from the 1.0.0 sources would have changed stored layouts and stranded players' items. When the author's current source is not in the conversation, ask for it.

### I3. Verify by script, then verify again after the last edit
Every delivery ends with: validator, compile check, logic tests, checksum regeneration, zip, **extract the zip and check its checksums**, patch applied to the previous tree and compared with the new tree. The last two steps caught a stale image and would catch a stale file. Re-run the whole list after *any* late edit, even a documentation edit (checksums change).

### I4. Run new tests against the old code
A test that has never failed has proven nothing. After a bug fix, run the new test against the unfixed sources and see the exact reported failure.

### I5. One change, one explanation, one number
Bump the version once per change set; say in one sentence what changed; keep a status entry per version. A multi-purpose release is hard to bisect when a player reports a problem.

### I6. A theory is not a fix until the next screenshot or log says so
The window-height story: an explanation from one screenshot was shipped as a fix, failed, and was replaced by a measured solution. Label the delivery "untested in the game" and ask for the next screenshot.

### I7. Do not touch what was not asked
Extra toggles, saved settings and refactors are flagged in the README as additions or left out. Unrelated dead code is mentioned, not deleted.

### I8. Ask for the missing file
Every wrong guess in Part F had a missing source file behind it. The cheapest step in the whole process is asking for the file.

### I9. After a confirmed finding, write it down
New knowledge goes into this repository in the same change set as the code: a Notes entry (with a diagnostic signature), an Internals row, a Tutorial snippet if the code teaches something new, and a changelog line. See `UPDATING.md`.
