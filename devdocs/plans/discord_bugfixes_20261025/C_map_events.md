# C: map/event bug fix plan (read-only investigation, 2026-10-25)

Line references were re-read against the current tree. All fixes are shared engine or content code: none is
specific to MAW. Survey scripts: `scratchpad/survey.py`, `scratchpad/newrule.py` (TextTable),
`scratchpad/animfaces.py` (BLV animated faces).

---

## 1. TextTable quote handling (Red Dwarf Mines scroll 1528 and four other scrolls)

**Cause.** `engine/TextTable.cpp:45-66`: a `"` at the start of a cell opens quoted mode, and a tab or newline inside
quotes is cell content. `english/scroll.txt` has item-name cells cut off as `"Journal Entry, 2nd Janua` with no
closing quote. The open quote swallows the next record (`\n1527\t" Journal...`). As a result, readable scrolls
**1521, 1522, 1525, 1527 and 1528** never reach `ReadableScrollTable`, and `InventoryItemUseRuntime.cpp:1316-1321`
returns the "cannot be used" failure.

**Survey of every `.txt` under `assets_dev/engine` and `assets_dev/worlds`** (Python port of the parser):

| table | quoted cells | multiline | quoted span with a TAB |
|---|---|---|---|
| npc_topic_text.txt | 1466 | 1055 | 0 |
| npc_greet.txt | 408 | 255 | 0 |
| npc_topic.txt | 12 | 3 | 0 |
| english/mm7_history.txt / history.txt | 31 / 18 | 27 / 18 | 0 |
| english/class.txt, Global.txt | 48 / 17 | 1 / 1 | 0 |
| mm9 readable_items.txt, quests_overlay.txt | 85 / 143 | 84 / 143 | 0 |
| **english/scroll.txt** (and `_legacy` copy) | 156 | 8 | **5 = exactly the broken spans** |

Legitimate quoted cells, multiline ones included, never contain a TAB.

**Minimal rule.** A leading `"` opens a quoted cell only if a closing quote (one not doubled as `""`) is reached
before the next TAB. Otherwise the `"` is a literal character and the cell stays unquoted.

```cpp
// engine/TextTable.cpp, inside parseTabSeparated, branch `else if (currentCell.empty())`
else if (currentCell.empty())
{
    if (hasClosingQuoteBeforeTab(contents, index + 1))
    {
        isInsideQuotes = true;
    }
    else
    {
        currentCell.push_back(character);   // dangling quote of a truncated cell: keep it literal
    }
}

// anonymous namespace
bool hasClosingQuoteBeforeTab(const std::string &contents, size_t begin)
{
    for (size_t index = begin; index < contents.size(); ++index)
    {
        if (contents[index] == '\t')
        {
            return false;
        }

        if (contents[index] == '"')
        {
            if (index + 1 < contents.size() && contents[index + 1] == '"')
            {
                ++index;
                continue;
            }

            return true;
        }
    }

    return false;
}
```

- **Checked:** a simulation of this rule over every table gives identical rows for all tables except `scroll.txt`.
  In `scroll.txt`, rows 1520–1536 change and all five missing ids appear. Item-name cells such as
  `"Journal Entry, 2nd Janua` keep a literal leading quote. The game uses `ItemDefinition::name` first, so this is
  cosmetic. Optionally, strip one unmatched leading quote.
- **Cost:** the look-ahead scans forward to the next quote or tab for each leading quote, which stays linear in
  practice. It runs only when a table is loaded.
- **Risk:** a future table with a real TAB inside a quoted cell. None exist today. Note the rule in a comment.
- **Data fix (optional; the parser fix makes it unnecessary):** close the five quotes in `english/scroll.txt`. Do not
  edit `_legacy`.
- **Tests:**
  - Extend `tests/TextTableTests.cpp` with a TEST_CASE such as "TextTable treats a leading quote with no close
    before the next tab as literal". Input: `"1\ttext\t\"Journal Entry, 2nd Janua\n2\t\" body ...\"\tLoc\tName\n"`.
    Expect 2 rows, `row(1).at(3) == "\"Journal Entry, 2nd Janua"` and `row(2).at(1) == " body ..."`. The existing
    multiline TEST_CASE must still pass.
  - Add a data check in `tests/TableRegressionTests.cpp`: after a headless load,
    `readableScrollTable().get(id)` is non-null with non-empty text for ids 1521, 1522, 1525, 1527 and 1528.

---

## 2. Outdoor decoration collision ignores hidden decorations (MM7 campfire stays solid)

**Cause.** `MapAssetLoader.cpp:2207-2259` builds `OutdoorDecorationCollisionSet` once. The only filter is
`shouldSkipDecorationCollision` (`:416-441`), which checks the invisible flag in the map file. The set is copied
into `OutdoorMovementController::m_decorationColliders` (`OutdoorMovementController.cpp:3689-3704`, member at
`.h:248`). `collideOutdoorWithDecorations` (`:914-1006`, called at `:2283` for the party and `:3132`) has no runtime
visibility check. The same stale list feeds the actor movement controller (`OutdoorWorldRuntime.cpp:5091-5096`) and
blink colliders (`:4996-4999`, `:7666`).

**Indoor is already correct.** `IndoorWorldRuntime::decorationMovementColliders()` (`IndoorWorldRuntime.cpp:18862-18910`)
rebuilds the list each call. It drops entities with `LevelDecorationInvisible` in `MapDeltaData::decorationFlags` or
`hiddenIndoorDecorationEntities(...)` (`InteractiveDecorationRules.cpp:694-726`: sprite-override hidden plus
cleared interactive decorations), and `IndoorRenderer.cpp:13874` pushes it every frame. This is covered by
`tests/IndoorDecorationInteractionTests.cpp:104` (gold bags). No indoor change is needed.

**Change: mirror the indoor approach.**

1. `game/gameplay/InteractiveDecorationRules.{h,cpp}`: add Outdoor overloads of `indoorDecorationClearRules` and
   `hiddenIndoorDecorationEntities`. Better: turn both bodies into one function template over the entity type, because
   `OutdoorEntity` has the same `scriptEventId()`, `decorationListId`, `name` and `spriteOverrideKey(i)`. Rename them
   to `decorationClearRules` and `hiddenDecorationEntities`. Take the map flags into account in the same pass:
   ```cpp
   template<typename Entity>
   std::vector<bool> hiddenDecorationEntities(std::span<const Entity> entities,
       std::span<const DecorationClearRule> rules, const std::vector<uint16_t> *pDecorationFlags,
       const EventRuntimeState &state)
   {
       // per entity: an override decides when present (SetSprite visible/hidden),
       // else the map flag LevelDecorationInvisible; OR the cleared-interactive rule.
   }
   ```
   Use the same rule (an override wins, otherwise the map flag) for drawing and clicking in fix 3.
2. `OutdoorWorldRuntime`: build `m_decorationClearRules` where the map is bound, as Indoor does at
   `IndoorWorldRuntime.cpp:3954/4079`. This needs a `DecorationTable` reference: pass it in from `MapAssetInfo`
   (`outdoorDecorationBillboardSet->decorationTable`) next to the collision set at the `OutdoorWorldRuntime.cpp:5091`
   call site. Add `std::vector<bool> hiddenDecorationEntities() const`.
3. `OutdoorMovementController`: add
   `void setHiddenDecorationEntities(const std::vector<bool> &hiddenEntities)` storing `m_hiddenDecorationEntities`.
   In `collideOutdoorWithDecorations`, pass the mask and add one check:
   ```cpp
   if (collider.entityIndex < hiddenEntities.size() && hiddenEntities[collider.entityIndex])
   {
       continue;
   }
   ```
   Forward it through `OutdoorMovementDriver` and `OutdoorPartyRuntime`, as `setActorColliders` is forwarded
   (`OutdoorPartyRuntime.cpp:95-98`, `OutdoorMovementDriver.cpp:936-939`).
4. `OutdoorSceneRuntime::advanceFrame` (`game/scene/OutdoorSceneRuntime.cpp:341`): next to
   `setActorColliders(...)`, call
   `m_pPartyRuntime->setHiddenDecorationEntities(m_pWorldRuntime->hiddenDecorationEntities())`. Also apply it to the
   world's own `m_outdoorMovementController` before actor movement, and filter `m_blinkDecorationColliders` at use
   (`:7666`).
5. `MapAssetLoader.cpp:418-421`: drop the load-time `LevelDecorationInvisible` skip in
   `shouldSkipDecorationCollision`. It is now handled at runtime, and `SetSprite(visible)` can re-enable a decoration
   that starts invisible. Keep the `MoveThrough`/`DontDraw`/radius checks.

- **Cost:** the mask is about one bool per entity, a few thousand at most. Recompute it only when visibility can have
  changed: add a `uint32_t decorationVisibilityRevision` to `EventRuntimeState`, bumped in `luaSetSprite`
  (`EventRuntime.cpp:6359`, which already bumps `indoorLightRevision`), at the decor-var write
  (`EventRuntime.cpp:7877`) and on state load. Cache the mask in `OutdoorWorldRuntime` keyed by that revision.
- **Risk:**
  - The decor-var index order must match `OutdoorInteractionController.cpp:1125-1153` and
    `initializeMapInteractiveDecorations`; all three must share the same skip (`scriptEventId() != 0`) and the same
    `MaxDecorationVarCount` cap.
  - MM6 "Party Start" entities carry `0x20` but have no sprite and no collider, so they are unaffected.
- **Test:** add a TEST_CASE to `tests/IndoorDecorationInteractionTests.cpp` (it already has the map, party and scene
  harness), "MM7 outdoor campfire clears its collision after taking the food". Load `7out01.odm` (two
  `7dec02`/`dec24`/`dec25` campfires) in MM7. Find the CampFire entity and check that the world's hidden mask is false
  and the collider is present. Activate 285 with the `ActiveDecorationContext` exactly as the gold-bag test does
  (`:170-178`). Then check that `hiddenDecorationEntities()[entity]` is true and that a movement sweep through the
  campfire's centre is not stopped. Also extend the headless regression case `campfire_global_event_adds_food_and_hides_on_clear`
  (`game/outdoor/HeadlessOutdoorDiagnostics.cpp:24896`) to check the mask.

---

## 3. Outdoor invisible map flag plus the Evenmorn obelisk treasure

**Cause (drawing and clicking).** Outdoor billboards are built whatever the invisible flag says
(`MapAssetLoader.cpp:2093-2129`). Visibility checks only look at `spriteOverrides` and cleared interactive state:
- `OutdoorInteractionController::resolveDecorationBillboardSpriteId` (`OutdoorInteractionController.cpp:1046-1100`)
- local copies of the same lambda at `OutdoorBillboardRenderer.cpp:2090` and `:2468` and
  `OutdoorInteractionController.cpp:3728`
- `isInteractiveDecorationHidden` (`:1168`) callers at `OutdoorBillboardRenderer.cpp:1155, 2167, 2846`,
  `OutdoorRenderer.cpp:3229`, `OutdoorSpatialFxRuntime.cpp:332` and `OutdoorInteractionController.cpp:3666, 3789`

As a result, `flower07` (out09 entity 2, `initial_decoration_flag: 32`, link number 20, event 170) is always drawn
and clickable. So are `dec94`, `dec95` and `dec96` in 7out06, 7out13 and out14.

**Change, drawing and clicking.**
- In `resolveDecorationBillboardSpriteId`, set the default `hidden` from the map flag before the override lookup:
  ```cpp
  hidden = isDecorationFlaggedInvisible(view, billboard.entityIndex);   // MapDeltaData::decorationFlags & 0x20
  ...
  if (overrideIterator != pEventRuntimeState->spriteOverrides.end())
  {
      hidden = overrideIterator->second.hidden;                           // an event override wins either way
  }
  ```
  `isDecorationFlaggedInvisible` reads `view.m_pOutdoorWorldRuntime->mapDeltaData()->decorationFlags`
  (filled from `initial_decoration_flag` at `OutdoorSceneYml.cpp:3355-3365`), falling back to
  `entity.aiAttributes`.
- Replace the three local lambda copies with calls to the shared function. This removes duplicated logic and avoids
  fixing it three times.
- In the coarse pick for entities without a decoration (`OutdoorInteractionController.cpp:3660-3670`), skip entities
  whose map flag is invisible and that have no visible override.
- Better: route both through one `OutdoorInteractionController::isDecorationEntityHidden(view, entityIndex)` built on
  the shared `hiddenDecorationEntities` predicate from fix 2, so drawing, clicking and collision use one rule.
- **Original behaviour:** OpenEnroth skips `LEVEL_DECORATION_INVISIBLE` at runtime
  (`Collisions.cpp:372`), and MM `evt.SetSprite` sets or clears that bit. The rule "an override wins, otherwise the
  map flag" is the same thing.

**Change, Lua: rewrite `MM7.UpdateEvenmornObeliskTreasure`** (`assets_dev/worlds/mm7/events/common/mm7_common.lua:561-575`,
hand-written, not generated).
- Reference: MMerge `reference/mmmerge/Scripts/Maps/out09.lua:1-24` finds the sprite with `Event == 170`. When QBits
  676–689 are all set, it runs a half-hour timer with `Treasure.Invisible = Game.Hour ~= 0`.
- **How to target the flower:** `evt.SetSprite` keys on the link number, which is
  `OutdoorEntity::spriteOverrideKey` = `eventIdPrimary` (`OutdoorMapData.h:101-104`). That is **20** for the flower,
  and it is unique in out09. The current code passes 170 (the click event), so it changes nothing.
- **Hour semantics:** `IsAtLeast(Hour, n)` tests for **equality** (`EventRuntime.cpp:10249-10254`), and the hour runs
  0–23 (`EventRuntime.cpp:1959`). The current `IsAtLeast(Hour, 1)` therefore means "hour is exactly 1" and never shows
  the treasure.
```lua
local EvenmornTreasureCog = 20 -- flower07 at (-2008, -13448); click event 170 opens the obelisk chest

function MM7.UpdateEvenmornObeliskTreasure()
    local allObelisksFound = true

    for qbitId = 676, 689 do
        allObelisksFound = allObelisksFound and IsQBitSet(QBit(qbitId))
    end

    -- Shown only during the midnight hour once every obelisk is read (MMerge out09.lua).
    evt.SetSprite(EvenmornTreasureCog, (allObelisksFound and IsAtLeast(Hour, 0)) and 1 or 0)
end
```
- **When it runs** (`assets_dev/worlds/mm7/events/maps/out09_mmmerge.lua`, a hand-written supplement):
  - keep `RegisterMapOnLoadEvent(65009, ...)`
  - add `RegisterMapTimerEvent(65011, 1800, function() MM7.UpdateEvenmornObeliskTreasure() end, "MMMerge Evenmorn obelisk treasure clock")`.
    1800 "seconds" equals 30 game minutes (`event_support.lua:1073-1088`), the same as MMerge's `const.Hour/2`.
- **Edge cases:**
  - Check whether relative timers catch up after resting or waiting on the map. If not, the treasure appears up to
    30 minutes late, as in MMerge.
  - The override is saved in `spriteOverrides`, and both the on-load event and the timer recompute it.
  - Event 170 keeps its own QBit-690 guard, as in the original.
  - Nothing reads the MM6 obelisk QBits (1384–1398) here, so there is no collision.
- **Tests:**
  - Add to `tests/ScriptedMapRegressionTests.cpp`, next to the "mm7 rescued dwarf and Haunted Mansion portrait..." case
    (`:5795`), which uses `loadMm7MapOverlayProgram(..., "out09", "out09_mmmerge", ...)`. Name it "mm7 Evenmorn
    obelisk treasure shows only at midnight after every obelisk". Run 65009 with a QBit missing, then at hour 5, then
    at hour 0 with QBits 676–689 set (set `runtimeState.variables[EvtVariable::Hour]` or the game minutes). Check
    `spriteOverrides[20].hidden` is true, true, false.
  - Draw and click: an outdoor case in `tests/IndoorDecorationInteractionTests.cpp` that loads `out09.odm` and checks
    `isDecorationEntityHidden(entity 2)` is initially true and false after `SetSprite(20, 1)`.

---

## 4. Haunted Mansion animated portrait (face 1844 shown as water)

**Cause.** In `7d37.blv` (identical to MMerge's), face 1844 has the animated flag (`0x4000`). Its name slot holds the
leftover name `hdwtr010`, and the stored texture index at **face +0x3A** is 13, which is `cleric_0` (the glowing-eye
cleric group: `texture_frame_data.txt:15`, MMerge `TFT.txt` index 13). The MM engines use that stored index for
animated faces; MMerge's `MiscTweaks.lua:414-427` sets `Facet.BitmapId = TFT index`. In OpenYAMM:
- `resolveSurfaceAnimation` (`MapAssetLoader.cpp:1217-1250`) checks liquids first, and `hdwtr010` matches the
  `water_mm8` prefix `hdwtr` (`assets_dev/engine/liquids/liquids.yml`).
- Its index fallback reads `IndoorFace::textureFrameTableIndex`, taken from offset `+0x10` of the face's extra data
  (`IndoorMapData.cpp:617`). That field is 0 in every BLV, so the fallback is dead code.
- `collectIndoorFaceTextures` (`:3772-3805`) also registers the face as a liquid (`:3801-3804`).

**Change.**
- `game/indoor/IndoorMapData.h:32`: replace the dead `textureFrameTableIndex` with `int16_t animationFrameIndex = -1;`.
  In `IndoorMapData.cpp:~555`, read `reader.readInt16(faceStructOffset + 0x3a, face.animationFrameIndex)` (the
  `bitmapId` field of OpenEnroth's `BLVFace_MM7`). Drop the read at `:617` and the write-back at `:1108`; keep `+0x10`
  round-tripped as raw data if the writer must preserve bytes. Check the users in
  `game/maps/IndoorSceneYml.cpp:478-629`, which use `textureFrameTableCog`; only rename what is actually the frame
  index.
- `resolveSurfaceAnimation`: animated faces resolve through the frame table before liquids.
  ```cpp
  const bool isAnimatedFace = (faceAttributes & static_cast<uint32_t>(FaceAttribute::Animated)) != 0;

  if (!isTerrain && isAnimatedFace && pTextureFrameTable != nullptr)
  {
      if (const std::optional<SurfaceAnimationSequence> animation =
              pTextureFrameTable->findAnimationSequenceByName(textureName))
      {
          return *animation;
      }

      if (frameTableIndex && *frameTableIndex >= 0)
      {
          if (const std::optional<SurfaceAnimationSequence> animation =
                  pTextureFrameTable->findAnimationSequenceByIndex(static_cast<size_t>(*frameTableIndex)))
          {
              return *animation;
          }
      }
  }

  if (pLiquidTable != nullptr && pLiquidTable->findMatch(textureName, faceAttributes, isTerrain) != nullptr)
  {
      return staticSurfaceAnimation(textureName);
  }
  // existing non-animated name lookup, then static
  ```
- In `collectIndoorFaceTextures`, register `liquidTextures` only when the result is not an animation from the frame
  table. Doing so for an animated face would make the water shader claim the `hdwtr010` key.
- **Animation key collision:** bindings are keyed by the face's texture name (`appendTextureAnimationBindingIfMissing`).
  If a map ever had a real `hdwtr010` water face and this portrait together, they would collide. Either key animated
  faces by name plus index, or accept it: no map has both today.
- **Survey of all BLVs (`animfaces.py`):** the only animated face whose name fails frame-table lookup, or that matches
  a liquid, is **7d37 face 1844**. Also, mm8 `d40.blv` faces 948 and 950 (`hhr1b`) have index -1 and no frame-table
  entry; they stay static, as in OpenEnroth, which turns off animation when lookup fails. Outdoor BModel faces were
  not surveyed. `OutdoorBModelFace::bitmapIndex` exists (`OutdoorMapData.h:45`) and outdoor animation comes from
  scene `surface_animations`; re-run the survey on ODMs only if a report appears.
- **Test:** add to `tests/ScriptedMapRegressionTests.cpp`, next to the water-binding checks around `:9150`
  (`findSurfaceAnimationBinding`), "MM7 Haunted Mansion cleric portrait animates instead of drawing water". Load
  `7d37.blv`, then check `indoorTextureSet->animationBindings` for `hdwtr010` has `cleric_0` ... `cleric_20` frames
  and that the face is not classified as a liquid. Also extend `tests/WaterRenderingTests.cpp:31` ("face liquid
  classification...") with an animated face named like water.

---

## 5. MM6 campfires (ckfyr00 and cmpfyr00 give no food) and the duplicate classifier

**Cause.** `InteractiveDecorationRules.cpp:408-411` matches CampFire by the keys `campfire`, `camp fire`, `dec24` and
`dec25` across hint, internal name and instance name. The MM6 fires `ckfyr00` (19 placed; cookpot) and `cmpfyr00` (3)
have the hint "fire", and `fire01` has "large fire". None of them matches. Meanwhile MM8 `dec04` (hint "campfire")
does match, although MMerge deliberately leaves it out.
- MMerge list: `{"ckfyr00","cmpfyr00","fire01","7dec02","dec24","dec25"} -- "dec04"`
  (`reference/mmmerge/Scripts/Structs/After/GlobalEventsNewHandler.lua:212`). It matches on internal name (`DecName`),
  gives 1–4 food and sets `Invisible`.

**Change.**
```cpp
// InteractiveDecorationRules.cpp classifyInteractiveDecorationFamily: match MMerge's DecName list only
if (decorationMatchesAnyKey(keys, {"ckfyr00", "cmpfyr00", "fire01", "7dec02", "dec24", "dec25"}))
{
    return InteractiveDecorationFamily::CampFire;
}
```
Drop the hint keys `campfire` and `camp fire`. MM7 `7dec02` is now matched by name. MM8 `dec04` (sprite 173, light
radius 128) stops being consumable, as in MMerge.

**Risk: decor-var indices shift in existing saves.**
- Indices are assigned in entity order across all interactive decorations: `initializeMapInteractiveDecorations`
  (`InteractiveDecorationRules.cpp:~567-600`), `OutdoorInteractionController.cpp:1125-1153` and
  `indoorDecorationClearRules`. Adding the MM6 fires and removing `dec04` shifts every later decoration's index in
  already-visited maps.
- `initializeMapDecorations` initialises only when all vars are zero, so saved states keep their old layout. Barrels
  and other decorations could take the wrong state.
- Per AGENTS.md, add an **explicit save migration**: bump the save version and, for each stored outdoor and indoor
  map state, remap `decorVars` from the old classifier's index list to the new one. Keep the old key list in the
  migration code only, give the new fires an initial state of 0 (fresh), and drop `dec04`'s slot.
- The NS goblin-camp fire (oute3 entity 387) carries its own event 222 (ambush), so it is skipped
  (`scriptEventId() != 0`), as in MMerge (`InitSprite`, `:585-590`). It stays foodless by design. Document this in
  the bug reply.
- "Rings" are not reproducible: neither MMerge nor global events 285/286 (`Global.lua:4052-4084`) give items.

**Duplicate logic.** `game/outdoor/OutdoorGameView.cpp:592-812` (`normalizeDecorationKey`, `decorationMatchesAnyKey`,
`classifyInteractiveDecorationFamily`, `interactiveDecorationBaseEventId/EventCount/HidesWhenCleared`,
`makeInteractiveDecorationSeed`, `initialInteractiveDecorationState`) is dead: each function appears only at its
definition. Its key lists are also stale (`dec32`, `dec01`, `dec21` as barrels, trash heaps and casks). Delete the
whole block together with the enum `OutdoorGameView::InteractiveDecorationFamily` (`OutdoorGameView.h:599-608`), which
nothing outside that block uses. Keep `InteractiveDecorationBinding`. Everything live already goes through
`resolveInteractiveDecorationBindingSpec` (`OutdoorInteractionController.cpp:1137`).

**Tests.**
- Extend `tests/GameplayRuleRegressionTests.cpp` "interactive decoration rules cover MM6 and MM7 indoor loot
  decorations" (`:7012`) with `makeDecoration("ckfyr00","fire")`, `("cmpfyr00","fire")`, `("fire01","large fire")`
  and `("7dec02","campfire")`. Each must give `CampFire`, base 285, count 2 and `hideWhenCleared`.
  `("dec04","campfire")` must give no spec.
- Add a migration TEST_CASE beside the existing save-version tests: a pre-migration `oute3` state with a barrel after a
  `ckfyr00` keeps its contents.
- Headless (optional): copy `tests/scenarios/mm6/smoke_faithful_potbello.yml` to click a New Sorpigal `ckfyr00` that
  has no event and assert that food increases.
