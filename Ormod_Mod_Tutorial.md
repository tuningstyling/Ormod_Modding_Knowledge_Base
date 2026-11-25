# Ormod Mod Tutorial: how the code works and why it is written that way

This tutorial walks through the code of the Heechee mods for **ORMOD: Directive Playtest** (a Unity game), one new idea at a time. Every snippet is copied verbatim from a mod that exists in this repository, so you can open the file and see it in context. Under each snippet you will find the same five things:

1. **What the code is** (where it lives)
2. **Purpose in the game**
3. **How it works, statement by statement**
4. **What the player sees or what the game does differently**
5. **Background concepts** you need to understand it

The tutorial assumes you know a little programming but nothing about Unity. Words in *italics* are defined the first time they appear and again in chapter 0.

> **Status legend** used across this knowledge base: **[IN-GAME]** = the author reported it works in the game; **[TESTED]** = checked against the game's source files and run in a test harness, not yet confirmed in the game; **[FAILED]** = tried and did not work; **[ASSUMED]** = reasoned from the source but unverified. Chapters say which applies.

---

## Chapter 0: concepts you need first

**Unity** is the engine the game is made with. A Unity game is a tree of *GameObjects* (things in the world: a player, a crate, a tree). A GameObject does nothing by itself; you attach *components* (scripts) to it. A script that can be attached is a *MonoBehaviour*. Unity calls special methods on it at set moments: `Awake` (once, when it is created), `Update` (every frame), `OnGUI` (when the old immediate-mode UI draws), `OnDestroy` (when it is removed).

**Analogy:** a GameObject is an empty actor; components are the skills you hand it ("can be picked up", "plays sound", "holds ammo"). Unity is the stage manager who tells each skill when to act.

**Mono and `Assembly-CSharp.dll`.** The game's own code is compiled into one file called `Assembly-CSharp.dll`. Because the game uses Unity's *Mono* runtime, that file keeps names and structure, so a mod can read it and call it. The mod's own code becomes a second DLL.

**BepInEx** is a loader. You drop your DLL into a folder, and BepInEx starts it when the game starts. A BepInEx *plugin* is a class that derives from `BaseUnityPlugin` and has a `[BepInPlugin(...)]` attribute. This knowledge base uses **BepInEx 6** for Unity Mono (build `BE788`), target framework `netstandard2.1`.

**Harmony** (a library inside BepInEx) lets a mod *patch* a game method without editing the game files. You say "run my code before/after that method" and Harmony rewrites the method in memory when the game starts. The patch disappears when the mod is removed, so the game returns to normal.

- A **Prefix** runs *before* the original. If it returns `false`, the original is skipped.
- A **Postfix** runs *after* the original. It can read or change the result.
- A **Finalizer** runs even when the original throws an exception, and it can swallow the error.

**Reflection** means looking up a class member by *name* at run time instead of at compile time. You need it for `private` fields: normal code cannot touch them, reflection can. Harmony's `AccessTools.Field(type, "name")` is the convenient version. Reflection is a bit slower and it fails silently if the name is wrong, so always check for `null` and say so in the log.

**Prefab vs instance.** A *prefab* is the template of an object ("the ammo crate"). Each crate you see in the world is an *instance* cloned from the prefab. If you change a number on the prefab only, existing instances keep the old value; if you change instances only, new clones are born with the old value. Good data mods handle both.

**Server and client.** In multiplayer, one game (the host or a dedicated server) owns the truth, and clients display it. A mod that changes a number only on your computer may be overruled by the host. Each chapter says where the code takes effect.

**Why 0.001 and never 0.** Games often divide by a time (`progress / totalTime`). Dividing by 0 gives `NaN` (not a number) or infinity, which breaks progress bars. A tiny positive number behaves like "instant" without that risk. You will see `0.001` repeatedly.

---

## Chapter 1: the smallest plugin


*Source: `Heechee_InstantPacking/src/Heechee_InstantPackingPlugin.cs`*

```csharp
[BepInPlugin(PluginGuid, PluginName, PluginVersion)]
public sealed class Heechee_InstantPackingPlugin : BaseUnityPlugin
{
    public const string PluginGuid = "Heechee_InstantPacking";
    public const string PluginName = "Heechee Instant Packing";
    public const string PluginVersion = "1.0.0";
    internal static ManualLogSource Log;
    private Harmony _harmony;

    private void Awake()
    {
        Log = Logger;
        _harmony = new Harmony(PluginGuid);
        _harmony.PatchAll();
        Log.LogInfo(PluginName + " " + PluginVersion + " loaded: packing with the Crafting Kit is instant. Crafting at workbenches is not changed yet.");
    }

    private void OnDestroy()
    {
        if (_harmony != null) { _harmony.UnpatchSelf(); _harmony = null; }
```


**1. What it is.** The entry point of the "Instant Packing" mod. Every plugin in this repository has this same shape.

**2. Purpose.** To tell BepInEx "this DLL is a plugin", give it an identity, and install the Harmony patches in the same assembly when the game starts.

**3. How it works.**
- `[BepInPlugin(PluginGuid, PluginName, PluginVersion)]` is an *attribute*, a label read by BepInEx. The GUID must be unique among all mods; the version is shown in logs.
- `public sealed class ... : BaseUnityPlugin` makes the class a plugin and, because `BaseUnityPlugin` is a `MonoBehaviour`, Unity will call `Awake` and `OnDestroy` for you.
- `internal static ManualLogSource Log;` holds the plugin's logger so other classes in the mod can write to the BepInEx console and `LogOutput.log`. `Logger` is provided by the base class; copying it into a static field lets other classes use it.
- `new Harmony(PluginGuid)` creates a Harmony instance named after the plugin. `PatchAll()` scans the assembly for classes marked `[HarmonyPatch(...)]` and installs each one.
- `OnDestroy` calls `UnpatchSelf()` so the patches are removed if the plugin object is destroyed.

**4. Effect.** On start the console prints a line such as `Heechee Instant Packing 1.0.0 loaded: ...`. That line is the first thing to look for when a mod "does nothing": no line means BepInEx did not load the plugin (see the CS0436 story in the Notes, chapter A3).

**5. Background.** The three `const string` values are the plugin's identity; the `.csproj` carries the same version number, and a validator test checks that the two agree.

---

## Chapter 2: the project file (`.csproj`)


*Source: `Heechee_InstantCraftingX/Heechee_InstantCraftingX.csproj`*

```csharp
<Compile Remove="reference\**\*.cs" />
<Compile Remove="tests\**\*.cs" />
```


*Source: `Heechee_InstantCraftingX/Heechee_InstantCraftingX.csproj`*

```csharp
<Reference Include="Assembly-CSharp"><HintPath>$(GameManagedDir)\Assembly-CSharp.dll</HintPath><Private>false</Private></Reference>
<!-- CraftingManager derives from Mirror.NetworkBehaviour; the compiler needs the assembly to resolve it. -->
```


**1. What it is.** Two excerpts from the build file that tells the .NET compiler what to compile and what to link against.

**2. Purpose.** The first excerpt keeps *test and reference files out of the plugin DLL*. The second links the mod against the game's own code so the mod can name game classes such as `CraftingManager`.

**3. How it works.**
- The .NET SDK compiles every `.cs` file under the project folder by default. `<Compile Remove="reference\**\*.cs" />` and `tests\**\*.cs` remove two folders from that rule. `reference` holds copies of game source files (for reading only). `tests` holds fake game classes (*stubs*).
- `<Reference Include="Assembly-CSharp">` with a `HintPath` points at the game's DLL on your computer. `<Private>false</Private>` means "do not copy it next to my DLL": the game already has it.

**4. Effect.** **[IN-GAME]** The first plugin (Instant Crafting X 1.0.0) did not load at all because `tests\stubs.cs` was compiled into the DLL. That file defined its own `BepInPlugin` and `BaseUnityPlugin`, so BepInEx did not recognise the plugin as its own, and the build printed CS0436 warnings ("type conflicts with an imported type"). The `Compile Remove` line fixed it. Every project now has a validator check that this line exists.

**5. Background.** *Stub*: a stand-in class with the same name and members as a game class, used only by tests. *Warning CS0436*: the compiler telling you that your code defines a type that also exists in a referenced DLL. Treat it as an error.

---

## Chapter 3: changing game data safely (Ammo Crate X, Magazine X)

Many mods are "make this number bigger". It sounds trivial, but the way to do it correctly is the most reusable lesson in this repository.

### 3.1 Scale from the vanilla value, never from the current value


*Source: `Heechee_MagazineX/src/MagazineService.cs`*

```csharp
internal static class MagazineService
{
    internal static readonly int[] SupportedPercents = { 15, 30, 50, 75, 100, 200 };

    private static readonly object Gate = new object();
    private static readonly Dictionary<string, int> VanillaMaxAmmo = new Dictionary<string, int>();
    private static readonly HashSet<string> Logged = new HashSet<string>();

    // new = round(old * (100 + percent) / 100), half away from zero, clamped to int.MaxValue.
    internal static int Scale(int vanilla, int percent)
    {
        long scaled = ((long)vanilla * (100 + percent) + 50) / 100;
        return (int)Math.Min(Math.Max(scaled, vanilla), int.MaxValue);
    }

    // Safe to call any number of times for any item; non-matching items return immediately.
    internal static void Apply(WeaponAttatchment item, WeaponAttatchment.MagazineData data)
```


(That excerpt ends at the start of `Apply`; the full method is below.)


*Source: `Heechee_MagazineX/src/MagazineService.cs`*

```csharp
internal static void Apply(WeaponAttatchment item, WeaponAttatchment.MagazineData data)
{
    if (item == null || data == null) return;
    if (!Heechee_MagazineXPlugin.IsTargetCategory(item.Catagory)) return;
    string id = item.ID;
    if (string.IsNullOrEmpty(id) || Heechee_MagazineXPlugin.IsExcluded(id)) return;

    lock (Gate)
    {
        int vanilla;
        if (!VanillaMaxAmmo.TryGetValue(id, out vanilla))
        {
            // The first MagazineData seen for an ID cannot have been changed by this plugin yet.
            if (data.MaxAmmo <= 0) return;
            vanilla = data.MaxAmmo;
            VanillaMaxAmmo[id] = vanilla;
        }

        int percent = Heechee_MagazineXPlugin.Percent;
        int target = Scale(vanilla, percent);
        if (data.MaxAmmo == target) return;

        int before = data.MaxAmmo;
        data.MaxAmmo = target;
        if (Heechee_MagazineXPlugin.LogChanges.Value && Logged.Add(id + ":" + before))
```


**1. What it is.** The core of "Magazine X": raise the capacity (`MaxAmmo`) of every magazine item by a percentage.

**2. Purpose.** To make the result *the same no matter how often or in what order the code runs*. This property is called **idempotence**: applying the change twice must not raise the value twice.

**3. How it works.**
- `VanillaMaxAmmo` is a dictionary remembering the *original* capacity of each item ID. The first time an ID is seen, its current `MaxAmmo` must still be the original (this plugin has not touched it yet), so it is stored.
- `Scale(vanilla, percent)` computes `round(vanilla * (100 + percent) / 100)` using `long` arithmetic so a large number cannot overflow an `int`, then clamps the answer so it never falls below the vanilla value.
- `target = Scale(vanilla, percent)` is always derived from the *vanilla* value. If a clone of an already-raised prefab arrives, the code computes the same `target`, sees `data.MaxAmmo == target`, and returns.
- `lock (Gate)` makes the dictionary safe if two threads run it at once.
- Items whose `_catagory` is not "Magazine" (the game's own spelling) and IDs on the exclude list return immediately, so the method is cheap to call for every item.
- `Logged.Add(...)` returns `true` only the first time, so the log gets one line per item instead of thousands.

**4. Effect.** Magazines hold 15 to 200 percent more rounds (the setting is a choice in the config file). The in-game inventory and the server code both read the same prefab value, so both agree.

**5. Background.** *Prefab and instance*: see chapter 0. In this game the **server reads the capacity from the prefab** and the inventory UI reads it from instances cloned from that prefab, so both must converge on one number. The rule "new = scale(vanilla)" guarantees that.

### 3.2 Hooking the moment an item appears


*Source: `Heechee_MagazineX/src/MagazineService.cs`*

```csharp
[HarmonyPatch(typeof(WeaponAttatchment), nameof(WeaponAttatchment.Initialize))]
internal static class MagazineInitializePatch
{
    private static void Postfix(WeaponAttatchment __instance)
    {
        try { MagazineService.Apply(__instance, __instance.Magazine); }
        catch (Exception ex) { Heechee_MagazineXPlugin.Log.LogError("Magazine apply failed: " + ex); }
    }
}

[HarmonyPatch(typeof(WeaponAttatchment), nameof(WeaponAttatchment.Magazine), MethodType.Getter)]
internal static class MagazineGetterPatch
{
    private static void Postfix(WeaponAttatchment __instance, WeaponAttatchment.MagazineData __result)
```


**1. What it is.** A Harmony *Postfix* on the game's `WeaponAttatchment.Initialize`.

**2. Purpose.** To apply the scaling to every item the moment it is created, so nothing is missed.

**3. How it works.** `[HarmonyPatch(typeof(X), nameof(X.Method))]` says which method to patch. A method named `Postfix` is called after the original with `__instance` (two underscores) set to the object the original ran on. The comment in the file explains why `Initialize` and not a property getter: a *virtual* method is never inlined by the compiler, so the patch always fires; tiny getters can be inlined and silently skip Harmony.

**4. Effect.** Newly created magazines already have the new capacity. A periodic scan in the plugin (every few seconds) catches anything that existed before the plugin ran.

**5. Background.** *Inlining*: the compiler may paste a very small method's body into its caller. A Harmony patch on the original then never runs for that caller. Patch methods that are big or virtual.

### 3.3 Ammo crates: a table instead of an item


*Source: `Heechee_AmmoCrateX/src/AmmoCrateService.cs`*

```csharp
internal static void ApplyAll(ItemDatabase database)
{
    if (database == null) return;
    if (ListField == null)
    {
        Heechee_AmmoCrateXPlugin.Log.LogError("ItemDatabase._ammoCrateTypes was not found; nothing changed.");
        return;
    }
    List<ItemDatabase.AmmoCrateType> list = ListField.GetValue(database) as List<ItemDatabase.AmmoCrateType>;
    if (list == null) return;
    foreach (ItemDatabase.AmmoCrateType entry in list) Apply(entry);
}

internal static void Apply(ItemDatabase.AmmoCrateType entry)
{
    if (entry == null) return;
    lock (Gate)
    {
        OriginalCapacity original;
        if (!Originals.TryGetValue(entry, out original))
        {
            original = new OriginalCapacity { Value = entry.Max };
            Originals.Add(entry, original);
        }
        if (original.Value <= 0) return;

        int multiplier = Heechee_AmmoCrateXPlugin.Multiplier;
        int target = (int)Math.Min((long)original.Value * multiplier, int.MaxValue);
        if (entry.Max != target)
        {
            int before = entry.Max;
            entry.Max = target;
            if (Heechee_AmmoCrateXPlugin.LogChanges.Value)
            {
                Heechee_AmmoCrateXPlugin.Log.LogInfo("Ammo crate [" + entry.ID + "] " + entry.TextName +
                    " (box '" + entry.BoxName + "') " + multiplier + "x: " +
                    before.ToString(CultureInfo.InvariantCulture) + " -> " + target.ToString(CultureInfo.InvariantCulture));
            }
        }
        if (entry.ID != null) CaliberMax[entry.ID] = entry.Max;
    }
}

// The bullet type a crate currently holds (its CurrentBullet data tag, e.g. ".45"), or null when empty.
private static string CurrentBullet(WeaponAttatchment item)
```


**1. What it is.** The part of "Ammo Crate X" that multiplies the capacity of ammo crates per caliber.

**2. Purpose.** In this game a crate's capacity is not one number on one item: the database keeps a *list of crate types* (one per caliber, for example 240 rounds for .45) in a private field `_ammoCrateTypes`. The mod multiplies each entry's `Max`.

**3. How it works.**
- `AccessTools.Field(typeof(ItemDatabase), "_ammoCrateTypes")` (declared once as `ListField`) reads the private list by name through reflection.
- A `ConditionalWeakTable<AmmoCrateType, OriginalCapacity>` remembers the original `Max` of every entry. It is *weak*: when the game discards an entry, the memory note disappears with it.
- `Apply(entry)` multiplies the *remembered original* by the configured multiplier (2, 3, 5, 7 or 10), not the current value, for the same idempotence reason as 3.1.

**4. Effect.** **[IN-GAME]** Crates hold 2x to 10x the rounds. Loaded crates show their caliber's new maximum; the display refreshes every 0.25 s.

**5. Background.** The vanilla capacities (.45 = 240, 9x19 = 240, 5.7x28 = 240, 5.45x39 = 180, 9x39 = 180, 7.62x51 = 120, 7.62x54 = 60, 12ga = 40) came from a JSON export of the game data made with a tool called UABEA. See Game Internals, section "Data tools".

### 3.4 A bug the game already had: fix it with a Finalizer


*Source: `Heechee_AmmoCrateX/src/Heechee_AmmoCrateXPlugin.cs`*

```csharp
private static void InspectMenuPrefix(PickupableItem item, ref bool __state)
{
    __state = false;
    try
    {
        if (item == null || !IsCrateItem(item.ID)) return;
        var tags = item.DataTags;
        if (tags == null || !tags.ContainsKey("CommodityItem") || tags.ContainsKey("CurrentBullet")) return;
        tags["CurrentBullet"] = tags["CommodityItem"];
        __state = true;
    }
    catch (Exception ex) { Log.LogWarning("Empty-crate fix prefix failed: " + ex.Message); }
}

private static Exception InspectMenuFinalizer(Exception __exception, PickupableItem item, bool __state)
{
    if (__state)
    {
        try { item.DataTags.Remove("CurrentBullet"); }
        catch (Exception ex) { Log.LogWarning("Empty-crate fix cleanup failed: " + ex.Message); }
    }
    if (__exception is KeyNotFoundException && item != null && IsCrateItem(item.ID) &&
        __exception.Message != null && __exception.Message.Contains("CurrentBullet")) return null;
    return __exception;
```


**1. What it is.** A Prefix and a Finalizer on `InventoryInspectMenu.SetActiveButtons`, the game method that builds the buttons of the inspect menu.

**2. Purpose.** In the unmodified game, inspecting a crate that holds rounds but has no `CurrentBullet` tag throws `KeyNotFoundException: 'CurrentBullet'` and the menu fails. A bigger crate makes that situation easier to reach, so the mod repairs it.

**3. How it works.**
- The **Prefix** runs before the game method. If the item is one of the crate IDs, has a `CommodityItem` tag and lacks `CurrentBullet`, it temporarily adds `CurrentBullet` as a copy of `CommodityItem`, and sets `__state = true`. `__state` is a value Harmony carries from the Prefix to the Finalizer of the same call.
- The **Finalizer** runs after the game method *even if it threw*. If `__state` is true it removes the temporary tag again, so the item's saved data is not changed. Then it looks at `__exception`: if it is the known `KeyNotFoundException` mentioning `CurrentBullet` for a crate, it returns `null`, which tells Harmony "handled, carry on". Any other exception is returned unchanged, so real problems are never hidden.
- Everything is wrapped in `try/catch` that only logs a warning: a bug in the fix must never break the game.

**4. Effect.** **[IN-GAME]** The inspect menu opens instead of erroring. Players notice nothing except that the bug is gone.

**5. Background.** *Swallowing exceptions is dangerous.* The code only swallows one specific, understood error. Copy that discipline whenever you fix a vanilla bug: narrow condition, one log line, original behaviour otherwise.


---

## Chapter 4: inventory grids (Slot Guard, Sort X)

### 4.1 Background: how the inventory stores items

Each container (a backpack, a pair of pants) has a *grid*. An item stored in it keeps its position in a *data tag* called `StoragePosition` with three numbers `x,y,z` (z = rotated). The container's UI keeps a 2-D array of slot objects (`_slots[x, y]`), and a cell that does not exist (a gap in an irregular layout) is `null`. When a mod such as Clothing Size X changes a garment's layout between versions, an item can be left stored at a cell that no longer exists. That is called an *orphan*.

### 4.2 Slot Guard: stop one bad item from breaking every container


*Source: `Heechee_SlotGuard/src/RefreshGuard.cs`*

```csharp
[HarmonyPatch(typeof(InventoryItem), nameof(InventoryItem.Refresh))]
internal static class InventoryItemRefreshPatch
{
    internal static readonly FieldInfo SlotsField = AccessTools.Field(typeof(InventoryItem), "_slots");
    private static readonly FieldInfo ContainerField = AccessTools.Field(typeof(InventoryItem), "_container");
    private static readonly FieldInfo SizeField = AccessTools.Field(typeof(InventoryItem), "_containerSize");
    private static readonly HashSet<string> Reported = new HashSet<string>();
    private static bool _reportedDiagnostics;

    private static void Prefix(InventoryItem __instance, PlayerInventory inventory, PickupableItem draggingItem, ref List<Action> __state)
    {
        __state = null;
        try
        {
            if (SlotsField == null || ContainerField == null || SizeField == null) return;
            SerializableEntity container = ContainerField.GetValue(__instance) as SerializableEntity;
            Vector2 size = (Vector2)SizeField.GetValue(__instance);
            if (container == null || size == Vector2.zero) return;
            Transform[,] slots = SlotsField.GetValue(__instance) as Transform[,];

            Transform slotParent = container.ContainerSlots[0].transform;
            var children = new List<Transform>();
            foreach (Transform child in slotParent) children.Add(child);

            foreach (Transform child in children)
            {
                PickupableItem item = child == null ? null : child.GetComponent<PickupableItem>();
                if (item == null || item == draggingItem) continue;
                var tags = item.DataTags;
                if (tags == null || !tags.ContainsKey("StoragePosition")) continue;

                string[] position = tags["StoragePosition"].ToArray;
                int x, y, z;
                if (position == null || position.Length < 3 || !int.TryParse(position[0], out x) ||
                    !int.TryParse(position[1], out y) || !int.TryParse(position[2], out z)) continue;

                Vector2 volume = item.GetCurrentVolume(z == 1);
                if (x + volume.x > size.x || y + volume.y > size.y) continue; // the game drops these itself

                bool missing = slots == null || x < 0 || y < 0 || x >= slots.GetLength(0) || y >= slots.GetLength(1) || slots[x, y] == null;
                if (!missing) continue;

                Report(container, size, item, x, y, z, volume);
                if (Heechee_SlotGuardPlugin.DropOrphans.Value && inventory != null)
                {
                    inventory.DropItem(item); // unparents synchronously, unless the game refuses to drop it
                    if (item == null || item.transform.parent != slotParent) continue;
                }

                // Hide for this refresh only: the tag is put back by the finalizer.
                var tag = tags["StoragePosition"];
                tags.Remove("StoragePosition");
                if (__state == null) __state = new List<Action>();
                __state.Add(() => tags["StoragePosition"] = tag);
```


*(Shortened for the page: the closing braces and the `catch` block are omitted.)*


*Source: `Heechee_SlotGuard/src/RefreshGuard.cs`*

```csharp
private static Exception Finalizer(Exception __exception, InventoryItem __instance, List<Action> __state)
{
    if (__state != null)
    {
        foreach (Action restore in __state)
        {
            try { restore(); }
            catch (Exception ex) { Heechee_SlotGuardPlugin.Log.LogWarning("Could not restore a StoragePosition tag: " + ex.Message); }
        }
    }
    if (__exception is NullReferenceException && !_reportedDiagnostics)
    {
        _reportedDiagnostics = true;
        try { Heechee_SlotGuardPlugin.Log.LogWarning("InventoryItem.Refresh still threw after the guard ran:\n" + Describe(__instance)); }
        catch (Exception ex) { Heechee_SlotGuardPlugin.Log.LogWarning("Could not describe the container: " + ex.Message); }
    }
    return __exception;
```


**1. What it is.** A Prefix and a Finalizer on `InventoryItem.Refresh`, the method that redraws one container's items.

**2. Purpose.** **[IN-GAME]** Without the guard, one orphan item makes `Refresh` throw a `NullReferenceException`, which also aborts `InventoryUIController.RefreshAllContainers` for every container after it. The player sees a broken inventory.

**3. How it works.**
- `ref List<Action> __state` is the carrier between Prefix and Finalizer. The Prefix fills it with small "undo" actions.
- The Prefix reads three private fields by reflection (`_slots`, `_container`, `_containerSize`) and walks every child object of the container's first slot parent. For each stored item it parses `StoragePosition`, works out whether the cell is missing (`slots[x, y] == null` or outside the array), and skips items the game already handles itself (those that overflow the bounding box).
- For an orphan it logs one warning (`Report`, once per item), then either drops the item (`inventory.DropItem`, only when the option `DropOrphans` is on) or *hides* it: the tag is removed for the duration of the call, because the game skips items without a `StoragePosition` tag.
- The Finalizer runs the undo actions, so the tag is back afterwards and the item is not lost. If a `NullReferenceException` still happens, it logs a one-time diagnostic describing the container, and returns the exception unchanged.

**4. Effect.** The orphan item is simply not drawn (or is dropped) and all other containers refresh normally. Nothing is deleted by default.

**5. Background.** *Defensive patching*: wrap your own logic in `try/catch` and let the original method run if your check fails ("the original refresh still runs"). A guard must never make things worse.

### 4.3 Sort X: sort the inventory with a key


*Source: `Heechee_SortX/src/Heechee_SortXPlugin.cs`*

```csharp
    // TickUI runs every frame while the inventory UI is open, so the key only works there.
    [HarmonyPatch(typeof(InventoryUIController), "TickUI")]
    internal static class InventoryTickUiPatch
    {
        private static void Postfix(InventoryUIController __instance)
        {
            if (Input.GetKeyDown(Heechee_SortXPlugin.SortKey.Value)) SortRunner.SortAll(__instance);
        }
    }

    // The game ships an empty InventoryItem.SortContainer(); if a button in its UI calls it, it now sorts that container.
    [HarmonyPatch(typeof(InventoryItem), nameof(InventoryItem.SortContainer))]
    internal static class SortContainerPatch
    {
        private static bool Prefix(InventoryItem __instance)
        {
            SortRunner.SortOne(__instance);
            return false;
        }
    }
}
```


**1. What it is.** Two hooks: one watches for the sort key while the inventory is open, the other fills in a method the game left empty.

**2. Purpose.** Press **F6** to sort your bags and clothing by category and name. **[IN-GAME]** Confirmed working.

**3. How it works.**
- `InventoryUIController.TickUI` runs *every frame while the inventory window is open*. A Postfix on it that tests `Input.GetKeyDown(key)` therefore only reacts when the inventory is visible, which is exactly when sorting makes sense. No `Update` loop of our own is needed.
- `InventoryItem.SortContainer` exists in the game but its body is empty. The Prefix calls our own sorting for that container and returns `false` to skip the (empty) original.
- The sorting itself lives in `SortPlanner`, a class with no Unity or game types, so it can be tested on any computer.

**4. Effect.** One key press rearranges items; the moves go through the game's own function `ClientSideEntityController.SetEntityInContainer`, so the server agrees.

**5. Background.** *Pure logic in its own class* is the single most useful structuring habit: the part that decides (the planner) is separate from the part that touches the game (the runner), so the decision can be unit-tested.


*Source: `Heechee_SortX/src/SortPlanner.cs`*

```csharp
// Tries three orders and returns the first that fits every item, or null (the container is then left untouched).
//   0: category, name            (the order the player asked for)
//   1: category, larger first, name   (same groups, tighter packing)
//   2: larger first, category, name   (first-fit decreasing, last resort)
internal static SortPlacement[] Plan(IList<SortItem> items, IList<SortSegment> segments, int gridWidth, int gridHeight,
    IList<string> categoryOrder, out int strategy)
{
    for (int s = 0; s < StrategyCount; s++)
    {
        SortPlacement[] result = TryPlace(Order(items, categoryOrder, s), items.Count, segments, gridWidth, gridHeight);
        if (result != null) { strategy = s; return result; }
    }
    strategy = -1;
    return null;
}
```


**1. What it is.** The planner's entry point.

**2. Purpose.** Place every item in the container without overlap, in the order the player asked for, and *never leave a half-sorted mess*.

**3. How it works.** The planner tries three orderings in turn: strategy 0 is "category, then name" (what the player asked for); strategy 1 keeps the groups but puts larger items first inside each group (tighter packing); strategy 2 puts the largest items first, then category, then name (*first-fit decreasing*, a classic bin-packing heuristic, used as the last resort). The first strategy that fits **every** item wins. If none fits, `Plan` returns `null` and the container is left untouched. The ordering code ends with extra tie-breakers (item id, serial number, original index) so the result is *deterministic*: the same inventory always sorts the same way.

**4. Effect.** Sorting is safe: either all items are placed or nothing moves.

**5. Background.** *Determinism* matters because tests compare exact results. *First-fit decreasing* is a standard approximation for the "packing boxes" problem.

---

## Chapter 5: timers (Instant Crafting, Harvesting, Packing)

### 5.1 Where the waiting lives

Waiting in this game is *data*: a number on a recipe, a field in a manager, a hold-time on an object. Make the number tiny and the wait is gone. The skill is finding which number and who reads it.

### 5.2 Instant Crafting X: recipe times


*Source: `Heechee_InstantCraftingX/src/Heechee_InstantCraftingXPlugin.cs`*

```csharp
[HarmonyPatch(typeof(CraftingManager), nameof(CraftingManager.Start))]
internal static class CraftingManagerStartPatch
{
    private static void Postfix(CraftingManager __instance)
    {
        try { InstantCraftingService.Apply(__instance); }
        catch (Exception ex) { Heechee_InstantCraftingXPlugin.Log.LogError("Could not set crafting times: " + ex); }
    }
}
```


*Source: `Heechee_InstantCraftingX/src/InstantCraftingService.cs`*

```csharp
internal const float InstantSeconds = 0.001f;

private static bool _reported;

internal static void Apply(CraftingManager manager)
{
    if (manager == null) return;
    List<CraftingManager.CraftingRecipe> recipes = manager.Recipes;
    if (recipes == null) return;

    int changed = 0;
    float slowest = 0f;
    foreach (CraftingManager.CraftingRecipe recipe in recipes)
    {
        if (recipe == null) continue;
        if (recipe.BaseCraftingTime > slowest) slowest = recipe.BaseCraftingTime;
        if (recipe.BaseCraftingTime == InstantSeconds && recipe.CraftingTimeIncrease == 0f) continue;
        recipe.BaseCraftingTime = InstantSeconds;
        recipe.CraftingTimeIncrease = 0f;
        changed++;
    }

    if (!_reported && recipes.Count > 0)
    {
        _reported = true;
```


**1. What it is.** A Postfix on `CraftingManager.Start` and the service it calls.

**2. Purpose.** Make recipe crafting finish immediately. **[IN-GAME]** Inventory combining works.

**3. How it works.**
- `CraftingManager` is a per-player component whose `Start` runs once. Every instance holds its own list `Recipes`, a `List<CraftingRecipe>` of simple objects with public float fields. The Postfix visits each recipe and sets `BaseCraftingTime` to `0.001` and `CraftingTimeIncrease` to `0`.
- Two comparisons keep the code idempotent and quiet: recipes already at the target are skipped, and `_reported` makes the summary line appear only once, with a count and the slowest vanilla time (useful when you want to know what you changed).
- The wait itself is a client-side timer: `InventoryUIController.WaitCraft` counts up to `recipe.BaseCraftingTime`. The server code (`CraftServer`, `CraftItem`) never reads the time, so the result is accepted as usual.

**4. Effect.** Combine two items and the product appears at once. A 0.3 s cooldown after crafting and the rule "release the mouse button before the next swing" were deliberately left alone.

**5. Background.** *Where does a mod take effect in multiplayer?* The timer is on your own game, so the mod works on any server. That is the safest kind of change.

### 5.3 One timer, three actions (Instant Harvesting and Instant Packing)

Packing a workbench, filling a container with water and lighting a fire all run on **one shared timer** in `PlayerInventory.GetInput`: a flag `_isPackingWorkbench`, a countdown `_pickupTime` and a maximum `_currentMaxPickupTime`. The game tells the three actions apart only *at completion*, by looking at the equipped item. Two mods share the timer, so each must classify the action the same way the game does.


*Source: `Heechee_InstantHarvestingX/src/TimedActionClassifier.cs`*

```csharp
        internal static TimedAction Classify(PlayerInventory inventory)
        {
            if (inventory == null || !inventory.IsPackingWorkbench || AnimationControllerField == null) return TimedAction.None;
            PlayerAnimationStateController controller = AnimationControllerField.GetValue(inventory) as PlayerAnimationStateController;
            EquippableItem weapon = controller == null ? null : controller.CurrentlyEquippedWeapon;
            if (weapon == null) return TimedAction.None;
            string id = weapon.ID ?? "";
            if (id.Contains("empty") || id.Contains("unpurified")) return TimedAction.Fill;
            if (weapon.ItemName == "Crafting Kit") return TimedAction.Pack;
            return TimedAction.Fire;
        }
    }
}
```


*Source: `Heechee_InstantHarvestingX/src/ActionTimerShrinker.cs`*

```csharp
        internal static void Shrink(PlayerInventory inventory)
        {
            if (TimeField == null || MaxField == null)
            {
                if (!_reportedMissing)
                {
                    _reportedMissing = true;
                    Heechee_InstantHarvestingXPlugin.Log.LogError("PlayerInventory._pickupTime / _currentMaxPickupTime not found; the action timer is unchanged.");
                }
                return;
            }
            float instant = InstantTime.Seconds;
            // The maximum stays above 0 because the game divides by it.
            if ((float)MaxField.GetValue(inventory) > instant) MaxField.SetValue(inventory, instant);
            if ((float)TimeField.GetValue(inventory) > instant) TimeField.SetValue(inventory, instant);
        }
    }
}
```


*Source: `Heechee_InstantHarvestingX/src/Heechee_InstantHarvestingXPlugin.cs`*

```csharp
// Water filling and fire lighting share the timer in PlayerInventory.GetInput; packing (Crafting Kit) belongs to Heechee_InstantPacking.
[HarmonyPatch(typeof(PlayerInventory), nameof(PlayerInventory.GetInput))]
internal static class PlayerInventoryGetInputPatch
{
    private static void Postfix(PlayerInventory __instance)
    {
        try
        {
            TimedAction action = TimedActionClassifier.Classify(__instance);
            if (action == TimedAction.Fill || action == TimedAction.Fire) ActionTimerShrinker.Shrink(__instance);
        }
        catch (Exception ex) { Heechee_InstantHarvestingXPlugin.Log.LogError("Could not shorten the action timer: " + ex); }
    }
}
```


**1. What it is.** A classifier, a timer shrinker, and the Postfix on `PlayerInventory.GetInput` that connects them (the same three files exist in Instant Packing, apart from the namespace).

**2. Purpose.** Shrink the shared timer, but only for the actions this mod owns: water filling and fire lighting here, packing in the other mod.

**3. How it works.**
- `Classify` returns `None` unless the flag `IsPackingWorkbench` is true (a timed action is running). It reads the equipped item through a private field: an item whose ID contains `empty` or `unpurified` means *Fill*; an item named `Crafting Kit` means *Pack*; anything else is *Fire*. This is the same test, in the same order, as the game's completion code, which the validator checks against the supplied source.
- `Shrink` sets `_currentMaxPickupTime` and `_pickupTime` to `0.001`, but only if they are larger; it never raises a value. The maximum stays above zero because the game divides by it for the progress circle.
- The Postfix runs after every `GetInput` call. Frames when no timed action runs do almost nothing: `Classify` returns `None` at once.

**4. Effect.** Hold the button for a moment and the action completes on the next frame, with the game's own sounds, animations and rewards.

**5. Background.** The same logic had to be *split in two mods* when the user asked for it. Two copies of three small files were kept byte-identical (apart from the namespace), which a script verified before each delivery. See Notes, chapter F (project split).

### 5.4 Resource harvesting


*Source: `Heechee_InstantHarvestingX/src/HarvestTimerService.cs`*

```csharp
        internal static void Apply(HarvestingManager manager)
        {
            // Crafting shares the two fields; it has its own mod (Heechee_InstantCraftingX).
            if (manager == null || !manager.IsHarvesting || manager.IsCrafting) return;
            if (MaxField == null || CurrentField == null)
            {
                if (!_reportedMissing)
                {
                    _reportedMissing = true;
                    Heechee_InstantHarvestingXPlugin.Log.LogError("HarvestingManager._maxHarvestTime / _currentHarvestTime not found; the harvest timer is unchanged.");
                }
                return;
            }
            float instant = InstantTime.Seconds;
            // The maximum stays above 0 because the game divides by it.
            if ((float)MaxField.GetValue(manager) > instant) MaxField.SetValue(manager, instant);
            if ((float)CurrentField.GetValue(manager) > instant) CurrentField.SetValue(manager, instant);
        }
    }
}
```


**1. What it is.** The Postfix target for `HarvestingManager.DoTick`.

**2. Purpose.** Make trees, ore, scrap, bushes and robot parts harvest at once.

**3. How it works.** Harvesting and crafting share the manager's two private floats `_maxHarvestTime` and `_currentHarvestTime`. When you start on a new target the game sets both (for example 5 s for ore without a mattock, otherwise a base time times your skill modifier). A hold-based harvest subtracts the frame time from the current value; a swing-based harvest (tree, ore, bush with a tool) subtracts a fixed amount per swing. Both finish at zero. The mod shrinks both fields right after the start, so one frame or one swing is enough. `!manager.IsHarvesting || manager.IsCrafting` keeps it from touching crafting, which uses the same fields.

**4. Effect.** **[TESTED]** (not yet reported from the game) One swing fells a tree; yield, tool requirements and experience are unchanged.

**5. Background.** `IsHarvesting` and `IsCrafting` are public properties on the manager; reading *public* state to decide whether to act is much more robust than guessing from private state.

---

## Chapter 6: changing a server rule (Instant Workbenches)


*Source: `Heechee_InstantWorkbenches/src/ProductionRateService.cs`*

```csharp
    // Not larger: a finished job is only processed on the next machine tick (MachineTickRate, 0.2 s by default), so a bigger rate gains nothing.
    // A duration of time / 1000 stays at or above a millisecond for recipes of a second or more; much smaller durations would round to zero
    // (DateTime.AddSeconds) and make MachineController.GetProductionProgress divide by zero.
    internal const float InstantRate = 1000f;
    internal static readonly string[] RateNames = { "PoweredMachineProductionRate", "UnpoweredMachineProductionRate" };

    private static readonly HashSet<string> Reported = new HashSet<string>();

    // Returns how many rates this call raised.
    internal static int Apply()
    {
        object settings = FindSettings();
        if (settings == null)
        {
            ReportOnce("ServerSettings.Settings was not found yet; the production rates are unchanged. Will keep trying.");
            return 0;
        }
        int changed = 0;
        foreach (string name in RateNames) if (Raise(settings, name)) changed++;
        return changed;
    }

    private static object FindSettings()
    {
        Type type = AccessTools.TypeByName("ServerSettings");
        if (type == null) return null;
        const BindingFlags flags = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
        FieldInfo field = type.GetField("Settings", flags);
        if (field != null) return field.GetValue(null);
        PropertyInfo property = type.GetProperty("Settings", flags);
        return property == null ? null : property.GetValue(null, null);
    }

    private static bool Raise(object settings, string name)
    {
        const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        Type type = settings.GetType();
        FieldInfo field = type.GetField(name, flags);
        PropertyInfo property = field == null ? type.GetProperty(name, flags) : null;
        if (field == null && (property == null || !property.CanRead || !property.CanWrite))
        {
            ReportOnce("ServerSettings." + name + " was not found as a writable field or property; it is unchanged.");
            return false;
        }
        Type valueType = field != null ? field.FieldType : property.PropertyType;
        object current = field != null ? field.GetValue(settings) : property.GetValue(settings, null);
        double before = Convert.ToDouble(current, CultureInfo.InvariantCulture);
        if (before >= InstantRate) return false;

        object value = Convert.ChangeType(InstantRate, valueType, CultureInfo.InvariantCulture);
        if (field != null) field.SetValue(settings, value); else property.SetValue(settings, value, null);
        ReportOnce("ServerSettings." + name + " " + before.ToString(CultureInfo.InvariantCulture) + " -> " + InstantRate.ToString(CultureInfo.InvariantCulture) + ".");
        return true;
    }

    private static void ReportOnce(string message)
    {
        if (Reported.Add(message)) Heechee_InstantWorkbenchesPlugin.Log.LogInfo(message);
    }
}
```


**1. What it is.** The whole engine of "Instant Workbenches": find the game's settings object and raise two numbers.

**2. Purpose.** Sixteen workbench classes (powered and unpowered: tailor, weapon, munitions, fabricator, production, angle saw, generic, water purifier) all compute a job's duration as `recipeTime * modifier / ServerSettings.Settings.PoweredMachineProductionRate` (or the *Unpowered* one), and the animations divide by the same rates. One change instead of sixteen patches.

**3. How it works.**
- `FindSettings` looks up the class `ServerSettings` by name (`AccessTools.TypeByName`) and reads its static member `Settings`, trying a field first and a property second. This makes the plugin independent of the game DLL, so it keeps loading even if a game update renames something; it just logs "not found".
- `Raise` reads the current value as a `double` (works for `float`, `int` or `double` fields), returns if it is already high enough (it never lowers a value), converts `InstantRate` to the field's own type with `Convert.ChangeType` and writes it.
- The plugin calls `Apply` once at start, on every scene load and every 5 seconds. The repetition is required: `ServerSettings.Load()` replaces `Settings` with a freshly built object, and the production rates are not part of the saved settings, so each loaded world starts at 1.
- **Why 1000 and not 1,000,000.** A finished job is only processed on the machine's next tick (`MachineTickRate`, 0.2 s by default), so a bigger rate gains nothing. A job's end time is `DateTime.Now.AddSeconds(duration)` and the progress is `elapsed / (end - start)`; a duration so small that it rounds to zero would divide by zero.
- Fuel burn is not divided by a rate, so fuel lasts as long as before.

**4. Effect.** **[TESTED]** Jobs complete on the machine's next tick. Nothing is written to disk; remove the DLL and restart to restore vanilla.

**5. Background.** *Where it runs:* the machines are run by the host or dedicated server, so there the mod must be installed. *Reflection on purpose:* when the sources of a class are not needed beyond two member names, reflection beats a compile-time reference.

---

## Chapter 7: adding music (Extra Music)

### 7.1 How the game picks music

The game's `SoundController` holds a private list `_musicTracks` of small `Music` records (`Song`, `SongLength`, `IsNight`, `AvaliableInTemperatures`). Every 600 to 1200 seconds it picks a random record whose `IsNight` matches the world's time of day and whose temperature pair allows the current biome. The mod does not replace any of that: it **adds records to the list**, and the game then treats them like its own.

The temperature test is `y < temperature < x` (the *first* number is the upper limit), and a pair with both numbers at 0 or below means "anywhere". A sub-biome's temperature is the centre of its type on a 0-to-1 axis (Tundra 0, Cold, Temperate, Warm, Desert 1), so a band of +-0.02 around a centre selects exactly one biome type.


*Source: `Heechee_ExtraMusic/src/RotationInjector.cs`*

```csharp
internal bool Sync(SoundController controller, IList<TrackSettings> tracks, Func<string, AudioClip> clipOf, bool enabled)
{
    if (controller == null || TracksField == null)
    {
        _controller = null;      // a destroyed controller takes its list, and our entries, with it
        _ours.Clear();
        _signature = "";
        return false;
    }
    var list = TracksField.GetValue(controller) as List<SoundController.Music>;
    if (list == null) return false;

    float[] centres = Centres();
    string signature = Signature(controller, tracks, clipOf, enabled, centres != null);
    if (ReferenceEquals(controller, _controller) && signature == _signature) return false;

    if (ReferenceEquals(controller, _controller)) foreach (SoundController.Music entry in _ours) list.Remove(entry);
    _ours.Clear();
    _controller = controller;
    if (enabled)
    {
        foreach (TrackSettings track in tracks)
        {
            if (!track.Enabled || track.Use == TrackUse.Menu) continue;
            bool specificBiomes = track.Biomes > 0 && track.Biomes < BiomeFlags.All;
            if (specificBiomes && centres == null) continue;    // the biome positions are not known yet; never play it everywhere by mistake
            AudioClip clip = clipOf(track.File);
            if (clip == null) continue;
            foreach (TempBand band in BiomeBands.For(track.Biomes, centres))
            {
                foreach (bool night in NightFlags(track.Time))
                {
                    var entry = new SoundController.Music
                    {
                        Song = clip,
                        SongLength = clip.length,
                        IsNight = night,
                        AvaliableInTemperatures = new Vector2(band.Max, band.Min)
                    };
                    list.Add(entry);
                    _ours.Add(entry);
                }
            }
        }
    }
    _signature = signature;
    return true;
}

private static IEnumerable<bool> NightFlags(TimeOfDay time)
{
    if (time != TimeOfDay.Night) yield return false;
    if (time != TimeOfDay.Day) yield return true;
}

// The centre of each temperature type on the 0..1 axis, computed the way BiomeController.ComputeBiomeStats does; null until the game has set up.
internal static float[] Centres()
{
    BiomeController biome = BiomeController.Instance;
    if (biome == null || ServerSettings.Settings == null) return null;
    var s = ServerSettings.Settings;
    float total = 0.12f * s.TundraSize + 0.15f * s.ColdSize + 0.26f * s.TemperateSize + 0.15f * s.WarmSize + 0.12f * s.DesertSize;
```


**1. What it is.** The "sync" routine that makes the game's list contain exactly the entries for the current settings.

**2. Purpose.** Let the player choose which of their own `.ogg` tracks join the day, night and biome rotation, and change the choice at any time without a restart.

**3. How it works.**
- *Signature*: a string built from the controller id, the on/off option, and per-track settings plus clip ids. If it equals the last one, nothing changed and the method returns at once, so calling it every second is free.
- *Track your own entries*: `_ours` remembers the exact `Music` objects it added. To change the list it removes those objects by reference and adds new ones; the game's own entries are never touched.
- *Time of day*: a track set to *Any* gets two entries (day and night); *Day* or *Night* gets one (`NightFlags`).
- *Biomes*: each ticked biome becomes one entry with `new Vector2(band.Max, band.Min)`; tracks tied to biomes are held back until the game's biome controller exists, so they are never played "everywhere" by mistake.
- *Scene changes*: if the controller object is a new one (a new world), the old list is gone with it, so the bookkeeping resets.

**4. Effect.** The game plays the player's tracks at its usual pace (a new track every 10 to 20 minutes). To hear one at once there is a player window (chapter 8).

**5. Background.** This is the **Sync pattern** and it is worth memorising: *compute a signature, skip if unchanged, remove what you added, add what is wanted, remember what you added*. It makes a mod safe against repeated calls, reloads and settings changes.

### 7.2 The title screen and the pause menu

The main menu has its own private clip lists in `OfflineSceneController` (`_titleDayMusic`, `_titleNightMusic`), and the same Sync pattern fills them (`MenuInjector`). The in-game pause menu has no music of its own, so the mod plays tracks on its own `AudioSource` while the player's state is `State.Paused`:


*Source: `Heechee_ExtraMusic/src/MusicPlayerService.cs`*

```csharp
private void UpdateMenuMode()
{
    if (_menuWanted && !_menuMode)
    {
        if (Current == null && _pending == null) StartMenuMusic();
    }
    else if (_menuMode)
    {
        _menuFade = Mathf.MoveTowards(_menuFade, _menuWanted ? 1f : 0f, Time.unscaledDeltaTime / MenuFadeSeconds);
        if (!_menuWanted && _menuFade <= 0f) Stop();
    }
}

private void StartMenuMusic()
{
    var loaded = MenuTracks().Where(f => _loader.Get(f) != null).ToList();
    if (loaded.Count == 0) return;
    _menuMode = true;
    _menuFade = 0f;
    ApplyGroup();
    PlayFile(loaded[_random.Next(loaded.Count)]);
    if (Current == null) LeaveMenuMode();      // the clip could not be started
}

// Enabled tracks for the menu (Plays in = Menu or Both), by the world's time of day when they are set to Day or Night.
private List<string> MenuTracks()
{
    bool night = WeatherController.Instance != null && WeatherController.Instance.IsNight;
    return _library.Tracks.Where(t => t.Enabled && t.Use != TrackUse.Game && (t.Time == TimeOfDay.Any || (t.Time == TimeOfDay.Night) == night))
                          .Select(t => t.File).ToList();
}

internal void Release()
{
```


**1. What it is.** The small state machine that starts and ends "menu mode" in the player.

**2. Purpose.** Play a Menu or Both track while the pause or settings menu is open, fade it in and out, and never interrupt something the user started.

**3. How it works.**
- `_menuWanted` is set every frame by the plugin: true while `PlayerStateMachine.Instance.CurrentState == State.Paused` and the option is on.
- If the menu is wanted but not yet running and nothing is playing, `StartMenuMusic` picks a random enabled Menu/Both track allowed by the time of day, routes the source to the game's `TitleMusic` mixer group (so the title-screen volume slider applies) and starts it with the volume at zero.
- While running, `_menuFade` moves toward 1 (menu open) or 0 (closed) at `1 / 0.6` per second using `Time.unscaledDeltaTime`; the source volume is `Volume * _menuFade`. When the menu closes and the fade reaches 0, `Stop()` ends menu mode, puts the source back on the in-world music group and un-mutes the game's music.
- Any user control (Play, Next, Pause, Stop) calls `LeaveMenuMode`, so the user is always in charge.

**4. Effect.** **[TESTED]** Open the pause menu and a track fades in; close it and the world's music returns.

**5. Background.** *Unscaled time*: `Time.deltaTime` is multiplied by the game's time scale and can be zero while paused; `unscaledDeltaTime` keeps running.

### 7.3 Loading audio files from disk


*Source: `Heechee_ExtraMusic/src/ClipLoader.cs`*

```csharp
private IEnumerator Load(string file)
{
    string path = _library.PathOf(file);
    var entry = new Entry { Stamp = StampOf(file) };
    if (!File.Exists(path))
    {
        entry.Error = "file not found";
    }
    else
    {
        using (UnityWebRequest request = UnityWebRequestMultimedia.GetAudioClip(new Uri(path).AbsoluteUri, AudioType.OGGVORBIS))
        {
            var handler = (DownloadHandlerAudioClip)request.downloadHandler;
            handler.streamAudio = false;      // first: "compressed" is not valid while streamAudio is on, and Unity warns
            handler.compressed = true;
            yield return request.SendWebRequest();
            if (request.result != UnityWebRequest.Result.Success)
            {
                entry.Error = request.error;
            }
            else
            {
                AudioClip clip = DownloadHandlerAudioClip.GetContent(request);
                float waited = 0f;
                while (clip != null && clip.loadState == AudioDataLoadState.Loading && waited < 10f) { waited += Time.unscaledDeltaTime; yield return null; }
                if (clip == null || clip.loadState == AudioDataLoadState.Failed || clip.length <= 0f)
                {
                    if (clip != null) UnityEngine.Object.Destroy(clip);
                    entry.Error = "Unity could not decode the file (it must be Ogg Vorbis; Ogg Opus is not supported)";
                }
                else { clip.name = Path.GetFileNameWithoutExtension(file); entry.Clip = clip; }
            }
        }
    }
    Entry old;
    if (_entries.TryGetValue(file, out old) && old.Clip != null) UnityEngine.Object.Destroy(old.Clip);
    _entries[file] = entry;
}

private DateTime StampOf(string file)
```


**1. What it is.** A *coroutine* that loads one `.ogg` file as an `AudioClip`.

**2. Purpose.** Let players drop their own files into a folder.

**3. How it works.**
- A coroutine is a method that can pause with `yield return` and resume on a later frame. `yield return request.SendWebRequest()` waits for the file read without freezing the game.
- `UnityWebRequestMultimedia.GetAudioClip(uri, AudioType.OGGVORBIS)` reads the file; the `file://` URI is built with `new Uri(path).AbsoluteUri` so spaces and special characters are encoded.
- `handler.streamAudio = false;` **must come before** `handler.compressed = true;` because Unity warns "Audio compression is not valid as streamAudio is set to true" if the order is reversed. **[IN-GAME]** That warning appeared in the first version.
- After `GetContent`, the code waits (up to 10 s) while `clip.loadState` is `Loading`, then rejects clips that are `Failed` or have zero length, with the message that the file must be **Ogg Vorbis**. **[IN-GAME]** One error in the first log, "Cannot create FMOD::Sound instance ... Unsupported file or audio format", is the typical sign of an Ogg file that holds Opus or FLAC instead of Vorbis.

**4. Effect.** Valid files become playable clips; broken ones show "error" in the window, and the rest keep working.

**5. Background.** `yield return null` waits one frame. Always dispose a `UnityWebRequest` (here with `using`), and always expect the file to be missing, damaged or in the wrong format.

### 7.4 Unity objects can be destroyed under you


*Source: `Heechee_ExtraMusic/src/MusicPlayerService.cs`*

```csharp
private bool EnsureSource()
{
    if (_source != null) return true;
    if (_released) return false;
    if (_recreations >= 5)
    {
        Message = "The player's audio object keeps being destroyed by something else; the player is off.";
        return false;
    }
    _recreations++;
    if (_host == null)
    {
        _host = new GameObject("Heechee_ExtraMusic_Player");
        UnityEngine.Object.DontDestroyOnLoad(_host);
    }
    CreateSource();
    if (Current != null) { _pending = Current; Current = null; Paused = false; }   // resume once the new source is ready
    Heechee_ExtraMusicPlugin.Log.LogInfo("The player's AudioSource had been destroyed; a new one was created (" + _recreations + ").");
    return true;
}

internal bool IsPlaying { get { return Current != null && !Paused; } }
internal float Position { get { return Current == null || _source == null || _source.clip == null ? 0f : _source.time; } }
internal float Length { get { return Current == null || _source == null || _source.clip == null ? 0f : _source.clip.length; } }
internal bool Loading { get { return _pending != null; } }
internal bool InMenuMode { get { return _menuMode; } }
```


**1. What it is.** A guard that every public method of the player calls first.

**2. Purpose.** **[IN-GAME]** In the first version the Play button threw `NullReferenceException` from `AudioSource.Stop()`. The player's `AudioSource` (or the separate object it was attached to) had been destroyed by something else, and the C# variable still pointed at it.

**3. How it works.** Unity overloads `== null` for its objects: a destroyed object compares equal to `null` even though the C# reference is not null. So `if (_source != null) return true;` correctly detects the dead source. If it is gone, the method makes a new one (creating the host object too if needed), remembers the track that was wanted so it resumes, and gives up after 5 recreations rather than creating objects forever. The better fix is in the plugin: the source now lives on the *plugin's own* GameObject, which exists for as long as the plugin's `Update` runs.

**4. Effect.** The player recovers instead of throwing; the log says when it did.

**5. Background.** Calling a native Unity method on a destroyed object throws `NullReferenceException`, not a helpful message. Never hold a Unity object across scene changes without checking it.

---

## Chapter 8: an in-game window with IMGUI

Unity has an old, simple, code-only UI called **IMGUI** (immediate-mode GUI). You draw the whole window again every time `OnGUI` runs, and a button is just an `if (GUILayout.Button(...))`. It is perfect for mods because it needs no assets.

### 8.1 The rules that cost time

- **No text boxes.** A typed letter also reaches the game's key bindings (W moves, E opens the inventory). The window offers buttons only; files are added by pasting paths from the clipboard.
- **Never change the number of controls while IMGUI is laying out a frame**, or Unity throws "Getting control N's position in a group with only N-1 controls". Button clicks therefore *set a deferred action*, and the action runs in `Update`:


*Source: `Heechee_ExtraMusic/src/MusicWindow.cs`*

```csharp
internal void Tick()
{
    if (_deferred != null)
    {
        Action action = _deferred;
        _deferred = null;
        try { action(); }
        catch (Exception ex)
        {
            _message = "That action failed: " + ex.Message;
            Heechee_ExtraMusicPlugin.Log.LogError("Window action failed: " + ex);
        }
    }
    if (!_open) return;
    Cursor.lockState = CursorLockMode.None;      // the game's camera may still follow the mouse: see the README
    Cursor.visible = true;
    _worldTimer -= Time.unscaledDeltaTime;
    if (_worldTimer <= 0f) { _worldTimer = 1f; _worldText = DescribeWorld(); _countsText = DescribeCounts(); }
}

internal void Draw()
{
```


**1. What it is.** The per-frame method that runs the deferred action and keeps the cursor free while the window is open.

**2. Purpose.** Make all list changes (add, remove, rescan, play) happen between frames.

**3. How it works.** A button sets `_deferred = () => ...`. `Tick` (called from the plugin's `Update`) takes the action, clears the field first (so an action that throws cannot run twice), runs it inside `try/catch`, and shows the error in the window. While open it also sets `Cursor.lockState = None; Cursor.visible = true`.

**4. Effect.** Clicks never break the layout, and a failing action shows a message instead of an endless error log.

**5. Background.** *Immediate mode* means the UI has no objects to update; your variables are the UI. Keep them in fields and change them outside `OnGUI`.

### 8.2 Resizing a window

IMGUI windows do not resize. The mod draws a small grip and handles the mouse itself:


*Source: `Heechee_ExtraMusic/src/MusicWindow.cs`*

```csharp
private void DrawResizeGrip()
{
    Rect grip = new Rect(_rect.width - 22f, _rect.height - 22f, 20f, 20f);
    GUI.Box(grip, new GUIContent("//", "Drag to resize the window"));
    int id = GUIUtility.GetControlID(FocusType.Passive);
    Event e = Event.current;
    switch (e.GetTypeForControl(id))
    {
        case EventType.MouseDown:
            if (grip.Contains(e.mousePosition))
            {
                GUIUtility.hotControl = id;
                _resizeStartMouse = GUIUtility.GUIToScreenPoint(e.mousePosition);
                _resizeStartSize = new Vector2(_rect.width, _rect.height);
                e.Use();
            }
            break;
        case EventType.MouseDrag:
            if (GUIUtility.hotControl == id)
            {
                Vector2 now = GUIUtility.GUIToScreenPoint(e.mousePosition);
                float scale = Mathf.Max(1f, Screen.height / 1080f);
                float w, h;
                WindowLayout.Resize(_resizeStartSize.x, _resizeStartSize.y, now.x - _resizeStartMouse.x, now.y - _resizeStartMouse.y, scale,
                    Screen.width / scale, Screen.height / scale, out w, out h);
                _pendingSize = new Vector2(w, h);
                _hasPendingSize = true;
                e.Use();
            }
            break;
        case EventType.MouseUp:
            if (GUIUtility.hotControl == id)
            {
                GUIUtility.hotControl = 0;
                _windowWidth.Value = _rect.width;        // remembered for the next start
                _windowHeight.Value = _rect.height;
                e.Use();
            }
            break;
    }
}
```


**1. What it is.** A grip in the bottom-right corner that resizes the window.

**2. Purpose.** The user asked for a resizable window.

**3. How it works.**
- `GUIUtility.GetControlID` gives the grip a unique id; `Event.current.GetTypeForControl(id)` returns the event as seen by that control.
- *MouseDown* on the grip captures the mouse with `GUIUtility.hotControl = id` and stores the start size and start mouse position (in screen pixels, via `GUIToScreenPoint`, so the result does not depend on the window's own coordinates).
- *MouseDrag* computes the new size with `WindowLayout.Resize`, which divides the pixel movement by the GUI scale and clamps to 900 x 520 minimum and the screen size. Because `GUILayout.Window` returns the *old* rectangle, the new size is stored in `_pendingSize` and applied after the window call returns.
- *MouseUp* releases the capture and saves the size to the config file.

**4. Effect.** **[IN-GAME]** The window follows the mouse and keeps its size. (The *track list* did not yet grow with it in versions up to 1.4.1, see 8.3.)

**5. Background.** *Hot control* is IMGUI's way of saying "this control owns the mouse until the button is released", which lets a drag continue outside the grip.

### 8.3 Making a list fill the window (a lesson in a failed idea)


*Source: `Heechee_ExtraMusic/src/WindowLayout.cs`*

```csharp
internal static float ListHeight(float windowHeight, float contentEnd, float listHeight, float bottomPadding)
{
    return Math.Max(MinListHeight, windowHeight - (contentEnd - listHeight) - bottomPadding);
}
```


*Source: `Heechee_ExtraMusic/src/MusicWindow.cs`*

```csharp
if (Event.current.type == EventType.Repaint) _listRectHeight = GUILayoutUtility.GetLastRect().height;
if (changed) _deferred = () => { _library.Save(); _changed(); };
```


**1. What it is.** The formula and the call that give the track list the height the rest of the window leaves.

**2. Purpose.** Show more tracks when the window is taller.

**3. How it works.** `GetLastRect().yMax` is the bottom of the last drawn control. Subtracting the list's own height gives the height of *everything else*, so the list is `window height - everything else - padding`, never below 120. The value is measured in the repaint and used from the next frame on, as a fixed `GUILayout.Height`.

**4. Effect.** **[FAILED] then [TESTED]**. Version 1.4.1 tried the "natural" way (`ExpandHeight(true)` on the scroll view plus non-stretching labels) and the list stayed at five rows in a tall window, as the user's screenshots proved. Version 1.4.2 computes the height instead. The new version still needs a screenshot check.

**5. Background.** *Auto-layout stretching in a window of forced height did not work as documented here.* When a layout trick fails, measure and compute. Record the dead end (Notes, chapter F) so nobody tries it a third time.

### 8.4 Columns that line up

Header cells and row cells must use the same explicit widths (`WindowLayout.ColOn`, `ColLength`, ...), with empty headings for columns that have none. Letting the name column "expand" separately in the header and the rows made the headings drift by about 130 pixels, because the header had no Play and Remove columns to eat the extra width.

---

## Chapter 9: testing without the game

The author builds and tests in an environment that has **no game and no .NET SDK**. That sounds impossible, and it is the reason this repository has strong habits. Every mod has four layers of checks:

1. **Static validator (Python)** reads the *copies of the game's source files* in `reference/` and asserts every assumption the mod makes: a field exists, a method is public, a string appears in the original code. When the game updates, the validator tells you which assumption broke.
2. **Stand-ins (`tests/stubs.cs`)**: tiny fake versions of the game and Unity classes the mod uses, with only the members the mod calls.
3. **Compile check:** the real plugin sources are compiled against the stand-ins. A typo in an API name fails here.
4. **Logic tests (PowerShell, `tests/test-*.ps1`)**: the pure logic is compiled and *run*, with expected results written as assertions.

A snippet from the stand-ins shows the idea; it imitates how Unity treats destroyed objects:


*Source: `Heechee_ExtraMusic/tests/stubs.cs`*

```csharp
// Like Unity: a destroyed object compares equal to null, and its native methods throw NullReferenceException.
public class Object
{
    public string name;
    public bool destroyed;
    public int GetInstanceID() { return System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(this); }
    public static void Destroy(Object o)
    {
        if (ReferenceEquals(o, null)) return;
        o.destroyed = true;
        var go = o as GameObject;
        if (go != null) foreach (Component c in go.Components) c.destroyed = true;
    }
    public static void DontDestroyOnLoad(Object o) { }
    public static T FindObjectOfType<T>() where T : Object { return null; }
    private static bool IsNull(Object o) { return ReferenceEquals(o, null) || o.destroyed; }
    public static bool operator ==(Object a, Object b)
    {
        bool an = IsNull(a), bn = IsNull(b);
        if (an && bn) return true;
        if (an || bn) return false;
        return ReferenceEquals(a, b);
    }
    public static bool operator !=(Object a, Object b) { return !(a == b); }
    public override bool Equals(object other) { return ReferenceEquals(this, other); }
    public override int GetHashCode() { return GetInstanceID(); }
    protected void ThrowIfDestroyed() { if (destroyed) throw new NullReferenceException(); }
}
```


**1. What it is.** A fake `UnityEngine.Object` used only in tests.

**2. Purpose.** Reproduce the *exact* failure from the game log (a destroyed `AudioSource` throwing `NullReferenceException`) in a place where the game is not available.

**3. How it works.** `destroyed` is a flag; `Destroy` sets it (and destroys child components); the `==` operator treats a destroyed object as null, exactly like Unity; native-style methods call `ThrowIfDestroyed()` to throw.

**4. Effect.** The new test fails against the old code and passes against the fix, which is the proof that the test is meaningful. This "run the new tests against the old sources" step is done for every bug fix.

**5. Background.** A test that has never failed has not proven anything. Culture matters too: tests format numbers with the *invariant* culture, because the author's Windows uses a decimal comma and `"0.001"` would otherwise become `"0,001"`.

---

## Chapter 10: shipping a mod

- **Nexus description:** four BBCode sections in order (Description, Installation instructions, Main features, Requirements), the body wrapped in `[size=3][color=#D4D4D8]`, then a fixed footer. A script checks that tags are balanced.
- **Steam Workshop:** the game has no Workshop, so the repository prepares a `workshop/` folder per mod (manifest, Steam-markup description, packaging script) and a loader mod. A warning applies to Extra Music: the loader deletes the mod's folder when you unsubscribe, which would delete the player's music.
- **Integrity:** a `CHECKSUMS.sha256` per project; the zip is extracted and verified with `sha256sum -c` before delivery.
- **Changes after release:** only the changed files and a `git apply`-compatible patch are delivered, never the whole project. A patch is verified three ways: `patch --dry-run`, applying it to the previous tree and comparing the result with the new tree, and `git apply --check`.

---

## Chapter 11: worked examples (from request to result, including a failure)

The earlier chapters explain code. This chapter shows the *method*: how a request became a patch, how a theory failed, and how to read a log. Specific class names are examples of techniques, not trivia.

### 11.1 From a request to a patch: "play the menu tracks while the pause menu is open"

1. **The request.** The user wanted tracks flagged "Menu" to play in-game while the pause and settings menus are open.
2. **Find out what the game already does.** The game's `SoundController` has no menu logic. The title screen's own controller, `OfflineSceneController`, plays music from two private lists, so *menu music means the title screen* in the vanilla game. That is a finding in itself: the in-game pause menu has no music to extend.
3. **Find the trigger.** Which code knows that the pause menu is open? The player's state machine: `PlayerStateMachine.Instance.CurrentState == State.Paused`. That class was **not** in the supplied files, so the assistant *asked for it* instead of guessing (Process rule I8). The enum showed `Paused = 10`, an *Overlay* state with a free cursor.
4. **Find the output route.** Music volume sliders are mixer parameters (`TitleMusicVolume`, `IngameMusicVolume`) applied to *mixer groups*. To make the title-screen volume slider control the pause music, the mod's `AudioSource` must output to the group named `TitleMusic`, which the mod finds through the sound controller's private `_mixer` field.
5. **Design the smallest thing.** One new per-track value (Game, Menu, Both), one new option (on by default), a small state machine in the player (fade in, fade out, never interrupt the user).
6. **Write the checks first.** Pure rules (which tracks are eligible by time of day) and the state machine are run in a compiled harness with stand-ins: opening the menu starts a Menu track on the title group and mutes the game's music; by day only day or any-time tracks play; closing fades and restores; a user's own playback is never interrupted; with no eligible track nothing starts.
7. **Deliver as a change set** (changed files plus patches, verified three ways) and say what only the game can confirm: *does the settings screen keep the `Paused` state?*

**What to copy from this:** find the *trigger*, the *route to the output*, and the *smallest state machine*; write the test list before the code; list the unknowns in the test plan.

### 11.2 A failure: making a list fill a window

1. **The symptom** (a screenshot): the window was resized taller, but the track list stayed five rows high and there was empty space at the bottom.
2. **First theory** (version 1.4.1): text lines also stretch vertically and steal the free height, so make them non-stretching and let the list expand. It sounded right and explained the odd gaps.
3. **The next screenshot proved it wrong:** the headings now aligned (a separate fix that did work), but the list still did not grow.
4. **Second approach** (version 1.4.2): stop relying on the layout engine. In every repaint, measure where the last control ends, subtract the list's own height to get the height of everything else, and give the list `window height - everything else - padding`.
5. **Lesson:** a layout theory is not a fix until a screenshot says so (Process rule I6). When the engine's automatic behaviour does not do what the documentation suggests, measure and compute, and write the dead end in the Notes so nobody tries it again.

### 11.3 Reading a log: three messages and what they meant

| Log line | Meaning | Fix |
|---|---|---|
| `NullReferenceException` from `UnityEngine.AudioSource.Stop ()` | the C# variable points at a Unity object that was destroyed | check `== null` (Unity's overload), recreate, attach to an object that lives as long as the plugin |
| `Audio compression is not valid as streamAudio is set to true` | set `compressed = true` while `streamAudio` was still on | set `streamAudio = false` first |
| `Cannot create FMOD::Sound instance for clip "" (FMOD error: Unsupported file or audio format.)` | the file is Ogg Opus or FLAC, not Ogg Vorbis, or damaged | convert to Ogg Vorbis; check `loadState` and report the reason in the UI |
| `OnAudioConfigurationChanged is being called recursively ...` | the **game's** own handler resets audio again and again because the device keeps changing | not the mod's bug; a mod can resume its own player after a real device change, deferred a frame or two |

Always find the *first* error in the log and the lines before it; later errors are often consequences.

### 11.4 The recipe for "make the waiting go away"

1. **Find the wait on screen.** A progress bar or a hold-to-act prompt. Note the exact action.
2. **Search the game code for who counts time:** `Time.deltaTime` subtractions, `Invoke(...)`, coroutines with `WaitForSeconds`, `DateTime`. Follow the number back to where it is *set* (the start site) and forward to where it is *compared* (the completion).
3. **Find every reader of the same number**, including the progress display. Anything that *divides* by it needs a value above zero.
4. **Decide where it lives:** data on a prefab or recipe (change the data, scaled from vanilla), a field on a manager (shrink it right after the start site with a Postfix), or a server rule (change the setting the server divides by).
5. **Check who needs the mod** (your own client, or the host).
6. **Choose the smallest patch** (Postfix after the start site, not a rewrite) and write the logic as a pure function you can test.
7. **List what you deliberately did not change** (cooldowns, animations, skills, yields) in the README, so players are not surprised.
