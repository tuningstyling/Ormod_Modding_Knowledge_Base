# Ormod Game Internals Notes

A reference of the game classes, fields and facts the mods rely on, in the style of an "SDK notes" file. Everything here was read from game source files that the author supplied (decompiled or exported C#), from JSON exports of game assets, or from listings. Nothing here comes from running a debugger on the game. **If a class is not listed, the source was never supplied; do not guess, ask for it.**

Labels: **[SRC]** read from a supplied source file; **[JSON]** read from an asset export; **[LIST]** read from a file listing; **[INFER]** reasoned from usage, not read.

## 1. The game and its folders **[LIST]**

- Game: **ORMOD: Directive Playtest** (folder name `Signal Decay Playtest`). Unity **2022.3.21**, Mono, `netstandard2.1` plugins.
- `<game>\ORMOD Directive Playtest.exe`, `<game>\ORMOD Directive Playtest_Data\`, `<game>\ORMOD Directive Playtest_Data\Managed\` (the game's DLLs, `Assembly-CSharp.dll`, `Mirror.dll`, `UnityEngine.*Module.dll`), `<game>\BepInEx\`.
- A full asset export (AssetRipper style) lists 38,826 files; 617 `AudioClip` files, all `.ogg`; no FMOD or Wwise plugin among the native plugins, so audio is Unity's own.
- **Data tools used:** *UABEA* (exports MonoBehaviour and asset data as JSON; for example `ItemDatabase-level1-8291.json`), *AssetRipper* (a project-style export of all assets and scripts, giving the file list). The scenes are not in the AssetRipper export, so per-scene serialized values need a UABEA dump.

## 2. Inventory and items **[SRC]**

| Class | Member | What it is | Used by |
|---|---|---|---|
| `InventoryItem` | `Refresh()` | redraws one container; throws NRE for an item stored in a missing grid cell | Slot Guard |
| `InventoryItem` | `Initialize`, `_slots`, `_container`, `_containerSize` (private) | grid of slot objects; gaps are `null` | Slot Guard |
| `InventoryItem` | `SortContainer()` | exists but is empty in the shipped game | Sort X |
| `InventoryUIController` | `TickUI()` | runs every frame while the inventory UI is open | Sort X (key hook) |
| `InventoryUIController` | `WaitCraft` | counts up to `recipe.BaseCraftingTime` | Instant Crafting |
| `InventoryUIController` | `RefreshAllContainers` | aborted by one container's exception | Slot Guard |
| `ClientSideEntityController` | `SetEntityInContainer` | the game's own move call, accepted by the server | Sort X |
| `ClientSideEntityController` | `entity.EntityPrefab.Magazine.MaxAmmo` | server reads capacity from the prefab | Magazine X |
| `ItemDatabase` | `_ammoCrateTypes[]` (private list) with `Max` | capacity per caliber | Ammo Crate X |
| `WeaponAttatchment` | `Initialize` (virtual), `MagazineData.MaxAmmo` (public int), `_catagory` (sic) | magazine data | Magazine X |
| `InventoryInspectMenu` | `SetActiveButtons` | throws `KeyNotFoundException: 'CurrentBullet'` for a crate with rounds but no bullet tag | Ammo Crate X |
| item data tags | `StoragePosition` = `x,y,z` | where an item sits in a grid | Slot Guard, Sort X |

Vanilla ammo crate capacities **[JSON]**: .45 240, 9x19 240, 5.7x28 240, 5.45x39 180, 9x39 180, 7.62x51 120, 7.62x54 60, 12ga 40.

Clothing layouts **[JSON]**: the NBC pants layout at 2x in the author's release 1.0.4 is `[0,0,2,4|2,0,2,4|0,4,4,2|4,0,1,4]` (x, y, width, height per segment) and differs from the 1.0.0 in this repository (pocket at (4,4)).

## 3. Crafting, harvesting and packing **[SRC]**

| Class | Member | Facts |
|---|---|---|
| `CraftingManager` | `Start()`, `Recipes` (`List<CraftingRecipe>`) | per-player copy; public floats `BaseCraftingTime`, `CraftingTimeIncrease`; world-crafting time = `(Base + Increase*(quality-1)) * tool modifier` |
| `CraftButton` | | a spinning visual marker only |
| `CraftableItem` | `CraftItem()` | crafts immediately |
| `CraftServer`, `CraftItem` | | never read the crafting time |
| `HarvestingManager` | `DoTick()`, `_maxHarvestTime`, `_currentHarvestTime`, `_swingBasedHarvesting`, `IsHarvesting`, `IsCrafting` | harvest and craft share the two floats; ore without a mattock starts at `5f * modifier` |
| `HarvestableType` | Tree = 0, Ore = 1, Scrap = 2, Bush = 3 | "coal" and "branches" are not named |
| `PlayerInventory` | `GetInput(Vector2)`, `_isPackingWorkbench`, `IsPackingWorkbench`, `_pickupTime`, `_currentMaxPickupTime`, `_animationController` | one timer for pack (x2), fill, fire; four start sites; completion branch classifies by equipped item |
| `PlayerAnimationStateController` | `CurrentlyEquippedWeapon` (`EquippableItem`: `ID`, `ItemName`) | used by the classifier |
| `InteractableItem` | `_interactTime` (serialized float), `InteractTime` | hold time of an interaction, set per prefab |
| `WorkbenchUnpack` | `InteractClientSide()` | calls `ItemPlacer.UnpackEntity/UnpackFurnature/UnpackWorkbench` at once; no delay |
| `HeavyManager` | | placed workbenches ("heavy" items); `PackWorkbench` |

## 4. Machines and server settings **[SRC]**

- **Workbench classes (16 use a rate):** powered: `PoweredTailorWorkbench`, `PoweredWeaponWorkbench`, `PoweredMuitionsWorkbench` (sic), `PoweredFabricator`, `PoweredProductionWorkbench`, `PoweredAngleSaw`, `PoweredGeneric`, `PoweredGenericSingleOutput`, `PoweredWaterPurifier`; unpowered: `UnpoweredTailoringBench`, `UnpoweredWeaponWorkbench`, `UnpoweredMutionsWorkbench` (sic), `UnpoweredFabricator`, `UnpoweredProductionWorkbench`, `UnpoweredAngleSaw`, `UnpoweredGeneric`. `UnpoweredWatercatcher` passes duration 0. `PoweredBattery`, `PoweredHeavyItem`, `UnpoweredHeavyItem` and `WeaponWorkbenchInteract` have no production timer.
- Eight of them use the powered rate and ten the unpowered rate (some powered classes use the unpowered rate: generic, production, weapon).
- `MachineController.StartProduction(uint serializeID, Action callback, float time, NetworkEntityAttatcher.AttatchmentType type, List<uint> ingredients, ...)`: `completeTime = DateTime.Now.AddSeconds(time)`; `TickMachines` runs through `InvokeRepeating("TickMachines", ServerSettings.Settings.MachineTickRate, ...)`; progress is `elapsed / (completeTime - startTime)`.
- `ServerSettings.Settings` is `public static SerializedServerSettings Settings = new SerializedServerSettings();` (a **field**), replaced in `Load()`; `SerializedServerSettings` has public floats `PoweredMachineProductionRate = 1f`, `UnpoweredMachineProductionRate = 1f`, `MachineTickRate = 0.2f`, the five biome sizes `TundraSize`...`DesertSize = 1f` and more. `PartialServerSettings` (saved) and `ClientServerSettings` (sent to clients) do **not** contain the production rates.

## 5. Sound, weather, biomes, scenes **[SRC]**

| Class | Member | Facts |
|---|---|---|
| `SoundController : MonoBehaviour` | `_musicTracks` (`List<Music>`), `_music` (`AudioSource`), `_mixer` (`AudioMixer`) | private; one per player |
| `SoundController.Music` | `Song`, `SongLength`, `AvaliableInTemperatures` (Vector2, x = upper), `IsNight` | public fields |
| `SoundController` | `PlayMusic()` | every 600 to 1200 s: random matching entry; `CheckAlloweInBiome` |
| `SoundController` | `OnAudioConfigChanged(bool deviceWasChanged)` (line ~730) | calls `AudioSettings.Reset(AudioSettings.GetConfiguration())` and restarts wind, grass, rain, birds |
| `SoundController` | `_mixer.SetFloat("TitleMusicVolume", ...)`, `"IngameMusicVolume"` | set from `KeybindController.Instance.TitleScreenMusicVolume` / `IngameMusicVolume` |
| `OfflineSceneController : MonoBehaviour` | `_titleDayMusic`, `_titleNightMusic` (`List<AudioClip>`), `_music`, `_timeStates` | title screen music; night when the current state's `Rotatation < 0` |
| `WeatherController : NetworkBehaviour` | `Instance`, `IsNight` | `IsNight` from `_sunRotation` |
| `BiomeController` | `Instance`, `GetWeightedChanceSubBiome`, `GetTemperaturePosition`, `GetTemperatureSize`, `SubBiome.TemperatureType` (Tundra 0, Cold 1, Temperate 2, Warm 3, Desert 4) | temperature axis 0..1 |
| `PlayerStateMachine` | `Instance`, `CurrentState`, `CurrentStateType`, `SetCurrentState`, `StateChange` event | state matrix of allowed switches |
| `State` | Locked 0, Standing 1, Crouching 2, Prone 3, Sitting 4, Placing 5, Inventory 6, Building 7, Trading 8, WeaponModifying 9, **Paused 10**, Chatting 11, Dead 12, Console 13 | |
| `StateType` | Movement 0, Override 1, Overlay 2 | `Paused` is Overlay with a free cursor |
| `PlayerUIController` | `CurrentUI` (a tag string of the open UI component) | in-game tabs; has no music |

Mixer groups **[SRC: AudioMixer.mixer]**: Master, Voices, Machinery, **TitleMusic**, Effects, UI, Voicechat, **IngameMusic**, Ambient.

## 6. What has not been seen (ask for it before relying on it)

- The camera script that reads the mouse and the class that reads clicks (needed to block input while a window is open).
- `ItemPlacer`, `PlayerControl`/movement scripts, any "pause menu" UI script, `UIOptionManager`'s in-game use.
- Per-scene serialized values such as the vanilla `_musicTracks` entries (which clips, which day/night/temperature).
- The Steam Workshop plumbing of the game (it has none).

## 7. Which files to ask for, by kind of mod

| Idea | Ask for |
|---|---|
| Change an item or recipe number | the item/database JSON (UABEA), the class that reads it, the server class that applies it |
| Make something instant | the manager that owns the timer, the UI controller that shows it, the server handler that completes it |
| New hotkey action in the inventory | `InventoryUIController`, `InventoryItem`, the entity move function |
| Workbenches / machines | the workbench classes, `MachineController`, `ServerSettings` |
| Music and audio | `SoundController`, `OfflineSceneController`, the `AudioMixer` asset, `KeybindController`, the Managed folder listing (to confirm Unity modules) |
| A menu or UI integration | `PlayerStateMachine`, `State`, `StateType`, `PlayerUIController`, `PlayerUIComponent` |
| A window that blocks game input | the camera and click-reading scripts |
