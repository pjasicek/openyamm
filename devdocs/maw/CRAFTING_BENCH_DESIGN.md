# Workbench: crafting and alchemy in one bench

Status: design proposal (2026-10-22), no code then. Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Inputs: [CRAFTING.md](CRAFTING.md) (what MAW does, with numbers),
[data/crafting_items.yml](data/crafting_items.yml) (the data draft),
[SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md) §5 (MAW alchemy), the Android touch contract in
`level_generation/ui/android_controls_audit_20260929/README.md`, and the alchemy bench as it is today.

## 1. Summary

- Rename the alchemy bench to the **Workbench** and give it two tabs, **Alchemy** and **Crafting**, in one frame.
  The Alchemy tab is today's bench, unchanged in layout. The Crafting tab reuses its geometry: an item list where the
  recipe list is, item + material + result slots where the potion slots are, a materials grid where the ingredient
  grid is, and a before/after panel where the status text is.
- One rules function, `CraftingRuntime::evaluate`, produces the result on a copy. The preview shows that copy; Apply
  re-runs the same function and commits the copy. Randomness comes from a per-item seed, so the preview is exact
  for every operation, including the ones MAW leaves random.
- Gem upgrades get batch apply ("Apply ×N", with a cheapest-tier option) and "Combine 3 → 1" with counts, replacing
  the U key.
- Crafting is ruleset data: the tab appears when the ruleset declares crafting operations. MAW declares 30 crafting
  items and five enchanting potions. Standard can optionally declare its vanilla item-target potions (Harden,
  weapon coatings, wand recharge) and gain a touch-friendly, previewed path for them.
- MAW alchemy needs a data swap plus four small features in the Alchemy tab: all recipes known, a power-requirement
  outcome, charges, and the effect at the brewed power.

## 2. The bench today

| Part | Where | What it does |
|---|---|---|
| Rules | `game/items/AlchemyBenchRuntime.{h,cpp}` | `resolveAlchemist` (:207), `collectIngredients` (:223), `buildBook` (:366), `preview` (:505), `mix` (:589), `AlchemyChainPlanner` (:871 `tryRecipe`) |
| Model | `game/ui/GameplayAlchemyBenchView.{h,cpp}` | `buildModel` (:115) rebuilds the frame's model from the party; caches chain counts by a hash (:17-70) |
| Renderer | `game/ui/GameplayAlchemyBenchRenderer.cpp` | `BenchPainter` (:34-237, anonymous namespace): wells, frames, chips, buttons, item icons, wrapped paragraphs; `render` (:376) |
| Input | `game/gameplay/GameplayAlchemyBenchInputController.cpp` | `handleInput` (:485): Escape leaves search then closes (:496), E closes the character screen (:522), click/drag between grid and slots, wheel and scrollbar drags |
| Service | `game/gameplay/GameplayItemService.cpp` | `mixAlchemyBench` (:846), `brewAlchemyChain` (:1016): perform mixes, sounds, status bar, bottle overflow to the cursor (:888-899) |
| State | `game/ui/GameplayUiController.h:381-416` | `AlchemyBenchState`: slots by item id, filters, search, scroll, last brew; lives in `CharacterScreenState::alchemyBench` (:433) |
| Pointer targets | `game/ui/GameplayOverlayTypes.h:409-434`, latches :723-732 | |
| Layout | `assets_dev/engine/ui/gameplay/alchemy_bench.yml` | 640×480 root, 640×365 Obsidian panel above the party bar; Fondamento headers `#d9b97a`, Lucida 0.55 body `#e5dcc7`/`#b7ab95`, `obsidian_button_tab_*` buttons 75×26 |
| Entry | `character.yml:95` `CharacterAlchemyButton`; `GameplayPartyOverlayInputController.cpp:2822-2840` | refuses while an item is held; resets slots; keeps filters and search |
| Dispatch | `GameplayPartyOverlayInputController.cpp:1693-1698`; render `GameplayUiOverlayOrchestrator.cpp:204` | |

Properties the Workbench keeps:

- **Preview is a dry run of the apply function.** `AlchemyBenchRuntime::preview` copies the target and calls the same
  `mixItems` that `mix` uses (`simulateMix`, :69 and :540). Crafting must follow the same rule; that is the fix for
  MAW's drift (CRAFTING.md §7.3).
- Party-wide: ingredients are counted across all packs, every bag of each (DEVIATIONS 131); the best conscious
  alchemist mixes.
- Every visit starts with empty slots; filters and search persist.
- No item is consumed by a plain drag; consuming actions are buttons.

What crafting needs that alchemy does not: alchemy slots hold **item ids** and use the strongest carried instance
(`findStrongestItem`, AlchemyBenchRuntime.cpp:18-60). Crafting targets one **specific item**, possibly worn, so the
crafting state holds item references.

## 3. Why one Workbench with tabs

| Option | Against | For |
|---|---|---|
| Separate crafting screen | A second frame, state struct, painter copy and button in the already full bottom-right panel of the character screen | Independent layout |
| Crafting section in the item inspect overlay | Inspect is read-only and held-RMB on desktop; the Android audit asks to keep Inspect dedicated to inspection; no room for a material picker or a compare panel | Close to the item |
| Keep MAW's item-on-item right-click | No preview without ALT, needs the right-button edge that Android cannot produce reliably, consumes items on a drop | Fast for experts |
| **Workbench with Alchemy and Crafting tabs** | A tab strip in the title row; one rename | One button, one frame, shared painter, slots, grids, scrollbars, search and status panel; same muscle memory |

Chosen: the Workbench. The item-on-item gesture stays as an accelerator (§5.1): dropping or right-clicking a held
crafting item onto equipment opens the Workbench on the Crafting tab with both slots filled. It never consumes
anything by itself.

## 4. Layout

### 4.1 Crafting tab

Proportional mockup of the 640×365 panel: one column = 6 units, one row = 13 units. Real coordinates are in §4.3.

```
+---------------------------------------------------------------------------------------------------------+
|  [ Alchemy  ] [*Crafting*]                   Workbench                                                  |
|  Equipment             38 items     Gem: raise the weaker enchant              +----------------------+ |
|  (Worn) (Packs) (All)               Brakus, main hand, needs L85: ok           | Before -> After      | |
|  [ search...                    ]   +---------+    +---------+    +---------+  | Damage 31-52      =  | |
|                                     | item    |    | material|    | result  |  | Might +103 -> +106   | |
|  +------------------------------+   |         |    |         |    |         |  |   T17 cap 106 (1H)   | |
|  | WORN - BRAKUS                |   |         | +  |         | =  |         |  | HP    +88 (78/106)   | |
|  | >Ancient Longsword    L95    |   |         |    |         |    |         |  | Infernos          =  | |
|  |  Primordial Chain Mail L90   |   |         |    |         |    |         |  | Quality +14%      =  | |
|  |  Rare Helm             L60   |   +---------+    +---------+    +---------+  | Item level 475    =  | |
|  | WORN - ILSA                  |   Longsword      T17 x7         +3 Might     | Value 91k -> 93k     | |
|  |  Epic Ring             L85   |                                              +----------------------+ |
|  |  Legendary Staff       L99   |   [  Apply   ] [ Apply x2 ] [ Combine  ] [  Clear   ]  [  Close   ]   |
|  | PACKS                        |                                                                       |
|  |  Common Battle Axe     L70   |   Materials    whole party, counts, tap or drag to place              |
|  |  Uncommon Boots        L40   |  (All) (Gems) (Special) (Potions) (Maps)                              |
|  |  Dim. Map Temple 3/4  L210   |                                                                       |
|  |  ...                         |  +------------------------------------------------------------------+ |
|  |                              |  | +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+  | |
|  |                              |  | |T14  | |T15  | |T16  | |*T17 | |Eye  | |Hour | |Pand | |Cube |  | |
|  |                              |  | |x9   | |x4   | |x6   | |x7   | |x1   | |x2   | |x3   | |x5   |  | |
|  |                              |  | +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+  | |
|  |                              |  | +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+  | |
|  |                              |  | |Pearl| |Orb  | |Endl | |Ench | |LElem| |     | |     | |     |  | |
|  |                              |  | |x1   | |aff19| |+25  | |p120 | |p48  | |     | |     | |     |  | |
|  |                              |  | +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+ +-----+  | |
|  +------------------------------+  +------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

- **Left: Equipment list** (the recipe list's well, 196×273). Rows of 17 units, grouped under 10-unit headers
  ("WORN - <name>" per member, "PACKS", later "STASH"). Each row: the item name in its rarity colour, right-aligned
  item level ("L95"). Chips filter Worn / Packs / All; the search box filters by name. The selected row has the blue
  selected border; rows the chosen material cannot act on are drawn in `DisabledTextColor`, and hovering one shows
  the reason in the status panel.
- **Centre: three slots** at the alchemy slot positions: item, material, result. The header names the operation
  ("Gem: raise the weaker enchant", "Hourglass: add a second enchantment"). The line below names the owner, where
  the item is, and the level check. Under each slot: the item's short name, the material count, and the result's
  headline change.
- **Right: Before → After panel** (138×136, the alchemy status box grown upward to y = 24). One line per stat
  (§6.4); unchanged lines end in "=", changed values are green or red, new lines gold, removed lines struck in grey.
- **Button row** at y = 166: five 75×26 Obsidian tab buttons. The set depends on the slots (§6.5).
- **Bottom right: Materials grid** (the ingredient grid, 402×121, 44×56 cells, 8 columns, 2 visible rows, scroll).
  A cell shows the icon, a tag (gem tier "T17", orb affix "aff19", Endless "+25", potion power "p120") and the count
  "x7". Identical gems stack into one cell; stateful items (charged orbs, Endless Potions of different strength,
  potions of different power, maps) get one cell per distinct state. Chips: All, Gems, Special, Potions, Maps.

### 4.2 Alchemy tab

Today's bench with the title row replaced by the tab strip. Only the status panel grows (y 24 instead of 56) to make
room for the effect preview (§9).

```
+---------------------------------------------------------------------------------------------------------+
|  [ Alchemy  ] [ Crafting ]                   Workbench                                                  |
|  Recipes               87 known     Regeneration (Expert)                      +----------------------+ |
|  (Can brew) (All known)             Ilsa, Alchemy GM 30, all known             | Regeneration, p60    | |
|  [ search...                    ]   +---------+    +---------+    +---------+  | Heals 41 HP / s      | |
|                                     | Blue    |    | Green   |    | result  |  | for 6 h 0 min        | |
|  +------------------------------+   |         |    |         |    |         |  | 5 charges            | |
|  | BOTTLE + REAGENT             |   |         | +  |         | =  |         |  | No power needed      | |
|  |  Cure Wounds      p62   9    |   |         |    |         |    |         |  | Brew 1 now, +2 by    | |
|  | NORMAL                       |   |         |    |         |    |         |  |   chaining           | |
|  |  Hexbane          p58   3    |   +---------+    +---------+    +---------+  | Stronger than your   | |
|  | EXPERT                       |   power 58       power 62       p60, 5 uses  |   Regeneration aura  | |
|  | >Regeneration     p60 1+2    |                                              +----------------------+ |
|  |  Enchant Item     p60   2    |   [   Mix    ] [ Mix All  ]  [  Clear   ]              [  Close   ]   |
|  | MASTER                       |                                                                       |
|  |  Darkness    p<100 !  1      |   Ingredients  whole party, click or drag to place                    |
|  |  Pure Power  step 2 -> 3     |  (All) (Potions) (Reagents)                                           |
|  |  ...                         |                                                                       |
|  |                              |  +------------------------------------------------------------------+ |
|  |                              |  |                    (ingredient grid as today)                    | |
|  +------------------------------+  +------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

The tab strip occupies the empty left part of the title row; the "Workbench" title stays centred. Under Standard
without crafting data the strip is hidden and the title reads "Alchemy Bench", so Standard looks as it does now.

### 4.3 New layout elements

All in the 640×365 panel coordinates of `alchemy_bench.yml`; same fonts, colours and button assets.

| Element | x, y, w, h | Notes |
|---|---|---|
| `WorkbenchTabAlchemy`, `WorkbenchTabCrafting` | 16, 4, 75, 20 / 95, 4, 75, 20 | `obsidian_button_tab_*`, `selected` state for the active tab; Fondamento 0.4 |
| `CraftingBenchItemHeader`, `...ItemCount` | 20, 24, 80, 14 / 70, 27, 140, 12 | as `AlchemyBenchRecipeHeader/Count` |
| `CraftingBenchItemFilterWorn/Packs/All` | 18, 40, 46, 13 / 67, 40, 46, 13 / 116, 40, 34, 13 | chips |
| `CraftingBenchItemSearch` | 16, 57, 196, 16 | managed text input, as the recipe search |
| `CraftingBenchItemList` | 16, 77, 196, 273 | rows 17, headers 10 |
| `CraftingBenchOperationHeader`, `...OwnerLabel` | 226, 24, 250, 14 / 226, 40, 250, 12 | |
| `CraftingBenchItemSlot`, `...MaterialSlot`, `...ResultSlot` | 230/318/406, 56, 64, 80 | with "+" and "=" labels as alchemy |
| `CraftingBenchCompare` | 484, 24, 138, 136 | Lucida 0.55, about 14 lines |
| `CraftingBenchApply`, `...ApplyMany`, `...Combine`, `...Clear`, `...Close` | 226/304/382/460/547, 166, 75, 26 | |
| `CraftingBenchMaterialHeader`, `...Hint` | 226, 198, 90, 14 / 300, 201, 322, 12 | |
| `CraftingBenchMaterialFilter*` | 224, 214, … 13 high | All 34, Gems 40, Special 52, Potions 52, Maps 40 wide |
| `CraftingBenchMaterialGrid` | 222, 229, 402, 121 | 44×56 cells, 3-unit gaps |
| `CraftingBenchConfirm` (overlay of the button row) | 226, 166, 396, 26 | "Remove Lich's from the Staff? [Confirm] [Cancel]" (§6.6) |

The Alchemy tab's `AlchemyBenchStatus` moves to 484, 24, 138, 136. Everything else in `alchemy_bench.yml` stays.

## 5. Opening, selection and gestures

### 5.1 Ways in

1. The character screen button (`CharacterAlchemyButton`, label "Workbench" when the ruleset has crafting). It opens
   the tab used last in this session.
2. Holding a crafting material or an item-target potion and dropping it on (or right-clicking) an item in the pack or
   on the doll: the Workbench opens on the Crafting tab with that item and that material in the slots. The held item
   goes back where it came from first, exactly as `CharacterAlchemyButton` requires an empty cursor today. Nothing is
   consumed. On Android this replaces the right-button edge the audit flags as unreliable.
3. Optionally a keybind (unbound by default) "Open Workbench".

### 5.2 Selecting

- Click a list row: it becomes the item. Click a material cell: it becomes the material. Click a filled slot: it
  empties. Drag works between list, grid and slots as in the alchemy bench.
- With a material and no item, the list highlights valid targets and greys the rest; with an item and no material,
  the grid dims materials that cannot act on it. This answers "what can I do with this?" without trial and error.
- Selecting a gem material with no item shows the gem's cap table (all slot classes) in the compare panel: the
  information MAW's gem tooltip shows.
- Map items appear in the list only when a map-capable material is chosen (or under the Maps filter); potions only
  for the Endless Potion.

## 6. Crafting behaviour

### 6.1 Rules function

```cpp
// game/items/CraftingRuntime.h (new). Pure rules over copies; no UI, no audio.
struct PartyItemRef
{
    size_t memberIndex = 0;
    PartyItemContainer container = PartyItemContainer::Pack;   // Pack, Equipped, later Stash
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    EquipmentSlot slot = EquipmentSlot::None;
};

struct CraftRequest
{
    PartyItemRef target;
    CraftMaterialKey material;      // item id plus state (orb affix, Endless strength, potion power)
    uint32_t applications = 1;      // Apply ×N
    bool cheapestGems = false;      // batch gems from the lowest useful tier
};

struct CraftEvaluation
{
    CraftStatus status = CraftStatus::Invalid;   // Ok, Invalid, NeedsConfirmation
    std::string reason;                          // shown when not Ok
    InventoryItem before;
    InventoryItem after;                         // the target after the operation
    std::optional<InventoryItem> producedItem;   // Mirror copy, charged orb
    std::vector<CraftMaterialUse> consumed;      // which material instances, how many
    uint32_t applicationsDone = 0;
    uint64_t evaluationHash = 0;                 // of inputs and outputs, checked at commit
};

class CraftingRuntime
{
public:
    static std::vector<CraftTargetEntry> collectTargets(const Party &party, const CraftContext &context);
    static std::vector<CraftMaterialEntry> collectMaterials(const Party &party, const CraftContext &context);
    static CraftEvaluation evaluate(const Party &party, const CraftRequest &request, const CraftContext &context);
    // Re-evaluates; commits only if the hash matches the one the player saw.
    static CraftEvaluation apply(Party &party, const CraftRequest &request, uint64_t expectedHash,
        const CraftContext &context);
    static GemCombinePlan planCombine(const Party &party, uint32_t tier, bool all, const CraftContext &context);
    static bool combine(Party &party, const GemCombinePlan &plan, const CraftContext &context);
};
```

`CraftContext` holds the item table, the special enchant table, the crafting table, the ruleset's item rules and the
save's crafting seed. `evaluate` dispatches on the material's operation from `crafting_items.yml` (about 15
operations, CRAFTING.md and the data draft). The enchant mathematics (gem caps, slot multipliers, enchant type roll,
special pools, Hourglass strength, Celestial rescale, rarity) are **the same functions the MAW loot generator uses**
(ITEMS.md §8, "one item-roll function"), not a crafting copy. Worn items are converted with
`makeInventoryItem(…, runtimeState)` (`Party.cpp:1539`) and written back with `copyItemToEquippedRuntimeState`
(`Party.cpp:1670`).

### 6.2 Deterministic randomness

- Each item gets `craftSeed` (u32) when it is generated, and `craftCount` (u16), both saved with the item
  (ENGINE_INTEGRATION.md §3.6 lists the item-struct work). Assigning the seed at generation, not lazily at the first
  preview, keeps previews free of writes.
- A craft's random stream is `hash(saveCraftSeed, item.craftSeed, item.craftCount, operationId, applicationIndex)`.
  Preview reads it; apply uses the same values and then increments `craftCount`.
- This keeps MAW's promises (fixed before you commit, unchanged by reloading, different after any other craft on the
  item) and extends them to the element potions (the Pearl rolls nothing: the player picks, §6.4). It also removes MAW's seed collisions and identical
  outcomes for Mirror copies (the copy gets a fresh `craftSeed`).
- No global random state is touched, so crafting cannot perturb loot rolls.

### 6.3 Commit

`GameplayItemService::applyCraft(runtime, request, expectedHash)` (new) calls `CraftingRuntime::apply`. If the hash
differs (the party changed the item between preview and click, for example by equipping), it applies nothing,
refreshes the preview and says "The item changed; check the new result". On success it removes consumed materials,
writes the target back, places a produced item in the owner's pack (or on the cursor if no pack has room, as the
bottle overflow does at `GameplayItemService.cpp:888-899`), plays the craft sound, and starts a short glow on the
result slot and on the item's row.

### 6.4 Before → After panel

Lines come from one shared "item stat lines" builder that the item inspect overlay also uses (for MAW, the tooltip
structure in ITEMS.md §8.1 item 3): base stat (damage or armour), attack speed, quality, enchant 1, enchant 2,
special, legendary affix, Celestial, item level, level required, value. Lines are keyed by stat so the diff is
per stat, not per text line. Extra lines the operation adds:

- Gems: each base enchant with its cap at this tier ("Might +103 / 106"), the chosen one marked; for batches the gems
  used per tier.
- Hourglass, Eye, Enchant Item, element potions: the exact rolled result (§6.2), not a range.
- Pearl: with two or more enchantments, "Remove which enchantment?" and one clickable row per enchantment (base
  enchantments with their strength, then the special), the first picked by default; the panel shows the item
  without the picked one. Picking another drops a pending confirmation, so Confirm names the current pick.
- Crafting Cube and Pandora's Cube: the cap and how many more uses reach it.
- Emerald: the new base name and the level requirement change.
- Orbs: what moves where ("Affix 'Cheat Death' moves into the orb"). Overwrites need confirmation (§6.6).
- Maps: affix unlocked, monster level change (Emerald +50), destination map (Cube).
- Materials consumed: "Uses 1 × Ascended Solarstone (6 left)".

### 6.5 Buttons and batches

| Slots | Buttons |
|---|---|
| Item + material | Apply · Apply ×N · Clear · Close (Combine disabled) |
| Gem material only | Combine 3 → 1 (×k) · Combine all · Clear · Close |
| Nothing or item only | Clear · Close (others disabled) |

- **Apply ×N** repeats the operation while it changes the item and materials last: gems until the chosen enchant
  pair reaches its caps or gems run out, the Crafting Cube to the level cap, Pandora's Cube to 20 %. N is shown on the
  button ("Apply ×7") and the panel shows the end state. Single-use operations (Eye, Hourglass, Mirror, Emerald,
  Pearl, orbs, potions) hide it.
- **Cheapest gems** (a chip in the material filter row, on by default under MAW): a gem batch uses, for each step,
  the lowest tier whose cap is above the current strength, so high tiers are spent only where needed (CRAFTING.md
  §3.3: 45 gems take a 1H enchant from 0 to 125, of which 9 need tiers 17-20).
- **Combine 3 → 1** merges three gems of the material's tier into one of the next, from anywhere the party keeps
  items (all members, packs and stash). "×k" shows how many merges are possible. **Combine all** runs the cascade
  from the lowest tier upward and lists the result ("12 × T5 → 4 × T6 → 1 × T7, 1 × T6 left") before confirming.
- Apply and Combine default to Enter; Apply ×N to Shift+Enter.

### 6.6 Confirmations

Irreversible operations that destroy something the player may want ask once, in place of the button row (no modal
popup, visible Cancel as the touch contract asks): the Pearl ("removes <enchant>"), an orb imprint over an existing
legendary affix, extracting Celestial status, the Emerald when it raises the level requirement above the owner's
level, and Combine all. Everything else applies on the first click; the preview is the confirmation.

### 6.7 Error states

| Situation | Shown | Apply |
|---|---|---|
| Material cannot act on this item class | grey row; panel: "Pandora's Cube refines weapon damage or armour" | disabled |
| Item unidentified | panel: "Identify the item first" (a preview would reveal it) | disabled |
| Level requirement not met | owner line in red: "Needs level 85; Brakus is 80" (owner, not the open page's character) | disabled |
| At cap | "Might 106/106 and HP 106/106: a tier 18 gem raises the cap to 113" | disabled |
| Nothing to remove / no affix to extract / no upgrade | one line naming why | disabled |
| Material state wrong (empty orb on a non-legendary item) | "The orb is empty: choose a legendary item to extract from" | disabled |
| No room for a produced item | "No room for the copy; it will be placed on the cursor" | enabled |
| Item changed since preview | refreshed preview, status line | refused once |
| Broken item | allowed (MAW does not check); the panel notes "broken" | enabled |
| Item worn by an unconscious or dead member | allowed; crafting is not a character action | enabled |

MAW's silent failures (CRAFTING.md §3.15) all become one of these explanations.

## 7. Input

- **Mouse**: as the alchemy bench (click, drag with the 6-unit threshold, wheel, scrollbar drag). Right-click on a
  list row or cell opens the normal item inspect overlay.
- **Keyboard**: Escape leaves the search, then closes (existing). E closes the character screen (existing). Tab and
  Shift+Tab switch Workbench tabs (the bench has no other use for Tab; the search field captures text only while
  active). Up/Down move in the item list, Left/Right in the material grid, Enter applies or mixes, Shift+Enter
  applies ×N or mixes all, Delete clears the slots. All listed in the keyboard settings screen.
- **Controller**: the engine has no gamepad input today. The layout has a linear focus order (tabs, list, slots,
  grid, buttons) and every hover-only text is also shown for the focused element, so a later gamepad layer can map
  the D-pad to focus moves, A to activate and B to back out.
- **Android**: tap selects, drag is optional. Cells (44×56) and rows (17) match the alchemy bench, which the Android
  layout already accepts. The search uses managed text input, so the keyboard appears. Inspect stays the
  separate Inspect control. The open-from-drop path (§5.1) replaces right-click crafting. Android Back should map to
  the Escape path once the audit's Back routing lands.

## 8. Storage and routing

- **Phase 1, no new container.** Materials are ordinary items in packs; the Workbench counts them party-wide like
  ingredients. MAW's crafting bag (Shift+B) and alchemy player (E) become one setting, "Send crafting materials to
  <member>", applied on pickup and by the Sort button, with the destination shown as a small badge on that member's
  inventory. The K pull becomes a keybind.
- **Phase 2, with a party stash** (README §5.1 proposes one). A "Materials" stash tab stores crafting items as
  counted stacks rather than grid cells (a stack per id and state). Pickup routing can target the stash when the
  party is at an inn or always when solo, as MAW's bags allow. The Workbench lists stash items under "STASH" and uses
  stash materials first.
- Gems use one inventory cell each in MAW; stacking them only in the stash avoids changing the inventory model.

## 9. MAW alchemy in the Alchemy tab

| Need | Change | Where |
|---|---|---|
| MAW recipe matrix, notes, names, potion settings | data overlay: `potion.txt`, `potnotes.txt`, `potion_settings.txt`, item rows 221-263 | ruleset tables |
| No explosions | nothing: the matrix has no explosion cells, so `KnownExplosive` never occurs | — |
| All recipes known | ruleset flag `alchemy.all_recipes_known`; `isPotionRecipeKnown` returns true and `buildBook` lists every entry | `AlchemyBenchRuntime.cpp:122`, `:366` |
| Reagent power from the reagent's item level and Alchemy mastery, cap 255 with overflow | ruleset formula used by `ingredientPower`, `InventoryItemMixingRuntime::reagentPower` and the planner's `tryRecipe` | `InventoryItemMixingRuntime.cpp:222`, `AlchemyBenchRuntime.cpp:871` |
| Power requirement | new outcome `BelowPowerRequirement`: brewable, amber, "Power 48: Greater Element needs 55 to work"; the chain planner prefers stronger ingredients when a requirement exists | `AlchemyPreviewOutcome`, `AlchemyChainPlanner` |
| Charges | result slot and panel show "5 uses"; potions keep `currentCharges` (field exists in `InventoryItem`) | `Party.h:45`, mix result |
| Effect at power | panel shows the potion's effect at the brewed power from `potion_effects.yml` ("Heals 312 HP", "+11 % attack speed for 6 h") | needs potion effects as data (README §4.3) |
| Black potions | per member: "Pure Power step 3: Ilsa +20 Might/Accuracy, Brakus already at step 3" | uses the same per-character ladder as drinking |
| Aura competition | "Weaker than Brakus's Haste aura" when a potion buff would be overridden | buff rework |
| Item-target potions | Enchant Item, element potions, Swiftness, Darkness appear as materials in the Crafting tab | crafting data `potion_operations` |
| Hard-coded vanilla potion ids | 233, 236, 246-250, 263 move from constants into ruleset data, or MAW's Regeneration recharges wands | `InventoryItemMixingRuntime.cpp:19-26` (CRAFTING.md §9.4) |

## 10. Code changes

### 10.1 New

| File | Purpose |
|---|---|
| `game/items/CraftingRuntime.{h,cpp}` | rules (§6.1); no UI |
| `game/tables/CraftingItemTable.{h,cpp}` | loads `crafting_items.yml` from the active ruleset: operations, parameters, preconditions, messages, item-target potions |
| `game/ui/GameplayCraftingBenchView.{h,cpp}` | model for the tab: targets, materials, rows, cells, evaluation, cached by a hash of party item versions and slot keys, as `cachedChainCounts` does |
| `game/ui/GameplayCraftingBenchRenderer.cpp` | draws the tab with the shared painter |
| `game/gameplay/GameplayCraftingBenchInputController.cpp` | pointer, drag, keyboard for the tab |
| `game/ui/GameplayBenchPainter.h` | `BenchPainter` moved out of the alchemy renderer's anonymous namespace so both tabs use it |
| `assets_dev/engine/ui/gameplay/crafting_bench.yml` | §4.3 elements (same root as `alchemy_bench.yml`) |
| `assets_dev/engine/rulesets/maw/crafting_items.yml` | from `devdocs/maw/data/crafting_items.yml` |
| `tests/CraftingRuntimeTests.cpp` | gem caps against CRAFTING.md §3.3 tables, every precondition and message, batch and combine plans, preview hash equals apply result, worn-item write-back |

### 10.2 Changed

| File | Change |
|---|---|
| `GameplayUiController.h:381-433` | `CharacterScreenState::workbench { bool active; WorkbenchTab tab; AlchemyBenchState alchemy; CraftingBenchState crafting; }` replaces `alchemyBench` (23 references in 12 files) |
| `GameplayOverlayTypes.h:409-434, 723-732` | `GameplayCraftingBenchPointerTarget`; tab targets; latches shared by both tabs |
| `GameplayAlchemyBenchRenderer.cpp:376` | draws the frame and tab strip, then the active tab; status panel geometry |
| `GameplayAlchemyBenchInputController.cpp:485` | tab switching and Tab key; dispatches to the crafting controller |
| `GameplayAlchemyBenchView.cpp`, `AlchemyBenchRuntime.cpp` | MAW alchemy items in §9 |
| `GameplayPartyOverlayInputController.cpp:1693-1698, 2822-2840` | open on the remembered tab; open prefilled from a held crafting item |
| `GameplayItemService.{h,cpp}` | `applyCraft`, `combineGems`; route crafting-material drops on items to the Workbench |
| `InventoryItemMixingRuntime.cpp:19-26, 118-205` | item-target potions read from crafting data; the vanilla behaviour becomes Standard's data |
| `character.yml:95` | label "Workbench" when crafting exists |
| `alchemy_bench.yml` | tab buttons, title text, status box geometry |
| `Party.h:45`, `CharacterState.h:128`, save code | `craftSeed`, `craftCount` with the other MAW item fields (ENGINE_INTEGRATION.md §3.6) |

### 10.3 Not needed

No new screen id, no Lua hook (crafting is rules, not content), no global RNG changes, no ALT tooltip mode.

## 11. Ruleset gating

| Feature | Standard | MAW |
|---|---|---|
| Workbench frame, tab strip | strip hidden unless Standard declares item-target operations | yes |
| Crafting tab with 30 crafting items | no | yes |
| Gem merge, batches, cheapest gems | no | yes |
| Item-target potions in the Crafting tab | optional: Harden, Flaming/Freezing/Noxious/Shocking/Swift/Slaying coatings, wand recharge with preview ("Fire 30 min × power 40 = 20 h") | Enchant Item, Lesser/Greater Element, Swiftness, Darkness |
| Open-from-drop instead of right-click mixing | yes for item-target potions (fixes the Android gap) | yes |
| Effect-at-power preview in Alchemy | yes, once `potion_effects.yml` exists (Standard effects are today a C++ switch) | yes |
| Recipe tree grouped by tier with power column | yes (cheap: the book already has tiers) | yes |
| "Brew to a power target" (planner prefers ingredients that reach a power) | useful for Standard's power-scaled potions | needed for power requirements |
| All recipes known | no (Standard discovers recipes) | yes |
| Power requirement outcome, charges, black-potion ladder, aura comparison | no | yes |
| Materials routing setting, K pull keybind | routing useful for reagents in Standard | yes |

## 12. Deviations from MAW to record

From CRAFTING.md §10, the design fixes: the Hourglass preview drift and the Eye preview gate (one function);
the Pearl's random pick (the player picks) and unseeded element potions (seeded); tooltip-performed crafting and its shop/chest reach (explicit apply on
party items only); table-dependent slot multipliers (2H axes always ×2); Pandora's Cube on rings and amulets
(refused); silent orb overwrite (confirmation); the Mirror's lost identified flag (kept); the Emerald closing house
screens (no); U limits (Combine across all storage, choice of tier); level checks against the owner; silent failures
(explained); the orb cooldown (not needed). Decisions left to the user: whether the Mirror may copy artifacts (code)
or not (README); Doom's caps from exact arithmetic (138) or MAW's float result (139); whether the Emerald becomes
sellable; whether more alchemists stock crafting items; the dimension-map affix-count bug.

## 13. Phasing

| Step | Content | Depends on |
|---|---|---|
| 1 | Workbench rename, tab strip, painter extraction, state rename; Alchemy unchanged | — |
| 2 | Standard item-target potions as data and in the Crafting tab, open-from-drop (Android benefit) | step 1 |
| 3 | MAW alchemy data swap, all-known, power requirement, charges | ruleset overlay (README §4.5 phase 1) |
| 4 | `CraftingRuntime` with MAW operations, seeds, compare panel, batches, Combine | MAW item model and enchant rules (README phase 4) |
| 5 | Effect-at-power preview | `potion_effects.yml` |
| 6 | Materials routing; stash tab | party stash |

Open questions: should the Workbench also be reachable from houses (an alchemist's or smith's counter) as a themed
entry; should crafting take game time; should Apply ×N stop at the first change of which enchant rises (players may
want to see each step).
