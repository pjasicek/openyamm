# F: Abandoned Temple cages and temple healing price

This is a read-only triage: nothing in the repo was edited or built. My scratch parsers are
`scratchpad/blv.py` (BLV decorations and face params, reusing `tools/export_indoor_scene_yml.py`),
`scratchpad/faceloc.py` and `scratchpad/lodx.py`.

---

## Bug 1a: "Room behind Angela Dawson is missing 4 cages to loot"

**Verdict: CONFIRMED.** Six of the room's eight cage decorations draw nothing. The report says four. Two cages
(the middle bone cages) are visible, so the reporter may have miscounted, or may remember a layout we cannot check.

### Facts
- The map is `6d02.blv` ("Abandoned Temple", `map_stats.txt` row 153). The cage room spans x 7232..8384,
  y 9600..10528, floor z -1880, ceiling -1368. Its only entrance is door 6 (faces 1900/2836 at y 9568/9600).
  Angela's event-14 faces are elsewhere, at about (2800, 5000).
- The original event script, `reference/mmext-scripts/Decompiled_Scripts/mm6/txt/D02.txt` (same in `mm6orig/txt/D02.txt`),
  has eight events with `Hint = "Cage"`: 16..23. Events 16..21 give a Ring, Amulet or Weapon at strength 1 or 2.
  Events 22 and 23 give a scroll and then cast the fireball (see 1b).
- Decorations in the BLV (decoration index → event):

  | decoration | name | DecList id | position | event |
  |---|---|---|---|---|
  | 106 | `Bonecage` | 148 | (7744,10464,-1880) | 22 |
  | 118 | `Bonecage` | 148 | (7872,10464,-1880) | 23 |
  | 107 | **`""`** | 13 | (7296,10368,-1768) | 18 |
  | 108 | **`""`** | 13 | (7296,10048,-1768) | 17 |
  | 109 | **`""`** | 13 | (7296, 9728,-1768) | 16 |
  | 110 | **`""`** | 13 | (8320,10368,-1768) | 21 |
  | 111 | **`""`** | 13 | (8320,10048,-1768) | 20 |
  | 112 | **`""`** | 13 | (8320, 9728,-1768) | 19 |

  The six wall cages sit 64 units from the side walls, three per side, 112 units above the floor. They have
  **empty names**. The OpenYAMM BLV is byte-identical to the MMerge one in `mmerge_data_forus` and in
  `mmerge_datapatch/Data/mm6.games.lod`, so the loss happened upstream, during MMerge's MM6 conversion.
  DecList id 13 is `pending` in the merged list (`reference/mmerge_data_forus/Data/Tables/DecList.txt` row 13).
- `game/tables/SpriteTables.cpp:571-574` (`DecorationTable::resolveMapDecoration`): an empty name returns id 0
  (`null`, sprite 0). It does this before the raw id or the MapAliases column is tried. `game/maps/MapAssetLoader.cpp:2109`
  then skips billboards with `spriteId == 0`, so these six get no sprite and no model. OpenEnroth behaves the same way:
  `DecorationList::GetDecorIdByName("")` returns `DECORATION_NULL`
  (`reference/OpenEnroth-git/src/Engine/Objects/DecorationList.cpp:16-18`, called at `CompositeSnapshots.cpp:250`).
- Clickability: `IndoorRenderer::inspectAtCursor` (`game/indoor/IndoorRenderer.cpp:12485-12537`) still tests every entity
  against a 48x48x64 box. The six events are therefore probably triggerable by clicking empty air at those spots.
  To the player they look missing. In the original engine, null decorations are not rendered, so they cannot be picked
  either.
- Why the original must have shown sprites: all eight carry `Hint = "Cage"`. Hidden event decorations in MM6 have no
  hint, for example 6d02 event 35 on torch 140, and 6d03 decoration 41 (event 26, no hint). The fix is real, but **which
  sprite the original used cannot be determined from the data we have**. No original MM6 `games.lod` is present (`data/Data`
  is MM7). Candidates in the merged table: `hngncge2` ("hanging cage", id 151, has the model
  `mm6_deco_hngncge2.glb` in `indoor_decorations.yml:261`), `Bonecage` (148) or `empty` ("empty cage", radius 64, height
  128; the 64-unit wall offset matches its radius). I recommend `hngncge2`, because the cages float 112 units up and a
  hanging cage fills the space to the ceiling. **This needs the user's confirmation against an MM6 screenshot or
  install.**
- Same-pattern audit, for a separate decision: empty-named decorations with id 13 also exist in `6d03` (1, event 26,
  no hint: intentionally hidden), `6d04` (5), `6d10` (1), `6d17` (7), `6t5` (1), `6t7` (2), `cd1` (21), `cd3` (1),
  `zddb08` (3) and `znwc` (1). Only 6d02's six carry a visible hint.

### Scope
This is world content in MM6 map 6d02, so it applies to both Standard and MAW. No ruleset ships a 6d02 map override.

### Fix (explicit map overlay, no general fallback)
Do **not** make `resolveMapDecoration` guess for empty names. That would be a broad fallback that also wakes the
intentional hidden markers. Instead, add an explicit per-entity decoration override to the indoor scene overlay and
author one overlay for 6d02.

1. `game/maps/IndoorSceneYml.h`: add a struct and a vector in `IndoorSceneInitialState` (`:70-81`).
   ```cpp
   struct IndoorSceneEntityOverride
   {
       size_t entityIndex = 0;
       std::string decorationName;
   };
   // in IndoorSceneInitialState:
   std::vector<IndoorSceneEntityOverride> entityOverrides;
   ```
2. `game/maps/IndoorSceneYml.cpp`:
   - Parse `initial_state.entity_overrides` (a sequence of `{entity_index, decoration}`), both in `loadFromText`
     (next to `face_attribute_overrides`, about `:952`) and in `applyOverlayFromText` (next to `:1523`).
     In the overlay, replace an existing entry with the same index, or append a new one.
   - Apply them in `buildIndoorMapStateFromScene` (`:1550`), next to the face overrides (`:1633`):
     ```cpp
     for (const IndoorSceneEntityOverride &entityOverride : sceneData.initialState.entityOverrides)
     {
         if (entityOverride.entityIndex >= indoorMapData.entities.size())
         {
             errorMessage = "scene entity override index is out of bounds";
             return false;
         }

         indoorMapData.entities[entityOverride.entityIndex].name = entityOverride.decorationName;
     }
     ```
   - Unknown keys stay errors, consistent with the loader. Keep a non-empty `decoration` required.
3. New overlay `assets_dev/worlds/mm6/maps/6d02_1.scene.yml`, picked up by
   `buildSceneOverlayPathCandidates` (`MapAssetLoader.cpp:3857`):
   ```yaml
   format_version: 1
   kind: "indoor_scene_overlay"
   source:
     geometry_file: "6d02.blv"
   initial_state:
     # MMerge's MM6 conversion lost these six "Cage" decorations' names (events 16-21).
     entity_overrides:
       - {entity_index: 107, decoration: "hngncge2"}
       - {entity_index: 108, decoration: "hngncge2"}
       - {entity_index: 109, decoration: "hngncge2"}
       - {entity_index: 110, decoration: "hngncge2"}
       - {entity_index: 111, decoration: "hngncge2"}
       - {entity_index: 112, decoration: "hngncge2"}
   ```
   The billboard set is built after the scene (`MapAssetLoader.cpp:4866` comes after `:4815`), so the new name drives the
   sprite or model, collision (`shouldSkipDecorationCollision`), lighting and picking.
4. Check whether the editor writes indoor scene overlays. If it does, round-trip the new key; otherwise add nothing.
5. Do **not** touch `6d02.lua`. Events 16..23 are already correct (see 1b).

### Edge cases
- Model height: `hngncge2` has two models (`indoor_decorations.yml:261` height 321, `:267` height 1159). Check which one
  binds for this map, and that a 321-tall cage starting 112 above the floor fits under the ceiling (512 above the floor).
  It does: 433 < 512.
- `decoration_flags` for entities 107..112 in `6d02.scene.yml` stay as they are (just the visible bit).
- Old saves: the overlay is static map data, so no migration is needed. The cleared state of an already looted cage
  lives in its MapVars, not in the decoration.
- Collision: the cages become solid (radius 29). Check that the side aisles, 320 units wide, stay walkable.

### Verification
- Doctest in `tests/GameplayRuleRegressionTests.cpp`, modelled on `"mm6 Temple of the Fist switch face uses
  scene-specific switch texture"` (`:2499`): load `6d02.blv`, check that entities 107..112 have empty names, apply
  `6d02.scene.yml` plus `6d02_1.scene.yml` through `buildIndoorMapStateFromScene`, then check that the names are `hngncge2`
  and their `eventIdPrimary` values are 18,17,16,21,20,19.
  Add a loader test for an out-of-bounds `entity_index`, and one for an unknown key.
- Visual check: `./tools/run_game.sh --isolated cages6d02 --world mm6 --map 6d02.blv --position 7808 9700 -1880
  --yaw-radians 1.57 --pitch-degrees 0 --set debug.screenshot_path=/abs/cages.png --set debug.screenshot_delay_seconds=4`.

---

## Bug 1b: "Looting the 2 middle cages doesn't trigger a fireball trap"

**Verdict: CANNOT DETERMINE from static reading.** The original trap exists, and OpenYAMM's script and spell
path both look correct, so the cause is at runtime and needs a headless reproduction.

### Original behaviour
`D02.txt` events 22 and 23 (the two `Bonecage` floor decorations): if MapVar6/7 is unset, set it, then
`GiveItem{Strength=2, Scroll}` and
`CastSpell{Spell=6 (Fireball), Novice, Skill=8, From=(7808,8960,-1768), To=(0,0,0)}`.
`To=(0,0,0)` means "aim at the party" (`OpenEnroth src/Engine/Spells/Spells.cpp:526-531`).
MMerge has no replacement for these events: `reference/mmmerge/Scripts/Maps/6d02.lua` replaces only event 14.

### OpenYAMM
- `assets_dev/worlds/mm6/events/maps/6d02.lua:133-145` (generated): `evt.CastSpell(6, 8, 1, 7808, 8960, -1768, 0, 0, 0)`
  after `evt.GiveItem(2, ItemType.Scroll_)`, guarded by `MapVar(8)` and `MapVar(9)`. The exporter's MapVar shift of +2
  is consistent across the whole file (MapVar1 → MapVar(3) in both events 17 and 26). The override `6d02_mmmerge.lua`
  touches only event 14. **The script is correct.**
- `luaCastSpell` (`game/events/EventRuntime.cpp:6530`) passes (spell, skill, mastery) to
  `IndoorWorldRuntime::castEventSpell` (`game/indoor/IndoorWorldRuntime.cpp:12363-12520`). That function targets the
  party when `to == 0` (`:12442-12447`), resolves the source sector and spawns an Event-source projectile. Spell 6 is
  Fireball in `spells.txt`. The impact AoE radius is 512 (`GameplayProjectileService.cpp:31`), and
  `canHitParty` is set (`IndoorWorldRuntime.cpp:6489`).
- Geometry: the source point is inside the corridor south of door 6 (floor z -1880 at y 8832..9088, ceiling -1569),
  so the sector should resolve. The flight north along x≈7808 passes **door 6** (y 9568..9600) and the centre
  brazier, decoration 117 at (7808,10112,-1680).

### Hypotheses to separate with a run (most likely first)
1. Door 6 is shut at the moment of casting, so the fireball explodes on the door, about 800 units away, outside the
   512 AoE. That would be faithful behaviour; check the door state in OpenYAMM after the party walks in.
2. The projectile spawn is rejected, or the sector is -1 (`spawnEffects.accepted == false` → `castEventSpell` returns false
   silently).
3. The projectile hits the centre brazier or some face and the AoE party check fails, or event-source party damage is
   filtered (`damageInput.eventSource`).
4. `evt.GiveItem` raises or yields when the hand or inventory is full, so `CastSpell` never runs. Check what
   `luaGiveItem` does when it has nowhere to put the item.

### Scope
Shared runtime (indoor event spells), so both Standard and MAW are affected.

### Verification (do this first; it decides the fix)
New headless scenario `tests/scenarios/mm6/abandoned_temple_cage_trap.yml`, copied from
`tests/scenarios/mm6/map_fixes_lava_wall_sarcophagus.yml` (`load_map` + `execute_event`). Use the `party_health` assert
the way `tests/scenarios/rulesets/maw_doom_items.yml` does:
```yaml
id: mm6.abandoned_temple_cage_trap
title: "Abandoned Temple: looting a middle bone cage fires the corridor fireball at the party"
world: mm6
mode: faithful
tags: [mm6, content]
steps:
  - new_game_flow: {start_map: oute3.odm}
  - load_map: {map: 6d02.blv}
  - execute_event: {id: 6}            # open door 6
  - advance_runtime: {seconds: 3}
  - set_pose: {x: 7808, y: 10380, z: -1880, yaw_degrees: 270}
  - execute_event: {id: 22}
  - advance_runtime: {seconds: 3}
  - assert:
      party_health: {full: false}
```
Run it with `OPENYAMM_INDOOR_PROJECTILE_DEBUG=1` (`IndoorWorldRuntime.cpp:976-982`). The `IndoorProjectileSpawn` line
shows `accepted`, `source` and `target`; the collision traces show what the fireball hit. Repeat without opening door 6
to confirm hypothesis 1. Fix whichever path fails in shared code: the projectile service or world collision, never the
map script.

---

## Bug 2: "Healing costs the same in temple for unconscious and wounded chars"

**Verdict: CONFIRMED.** There are two causes. (A) OpenYAMM never records when Unconscious or Dead is inflicted by HP
loss, so their time multiplier is always 1. (B) The multiplier formula follows OpenEnroth's guess, not the original
executables.

### Original behaviour (checked in all three executables with objdump)
- MM6 `MM6.exe` (fe3adb9e, `reference/Misc-MM8Patch-2.5.7/MMPatches/Install/MM6patch/Files/`), temple price at
  **0x49e910**, called from the temple dialogue at 0x49dd76 with the house `Val` from `[0x52d550+house*0x30]`.
- MM7 `mm7.exe` (673c9805), price at **0x4b7fdf**, multiplier helper at **0x4b7fa3**.
- MM8 `mm8.exe` (97be86a7, the build MMerge runs), price at **0x4b660b**, helper at **0x4b65cf**. It is called from
  0x4b586d with `Val` from `[0x5a5748+house*0x34]`.
- All three compute the same thing:
  ```
  major = GetMajorCondition()                      // priority Eradicated, Petrified, Dead, Zombie, Unconscious, ...
  if major in {Dead(14), Petrified(15)}: base = 5,  mult = dayMult(major)
  elif major == Eradicated(16):          base = 10, mult = dayMult(major)
  else:                                  base = 1,  mult = max(dayMult(c) for c in 0..13), or 1 if that is 0
  price = max(1, int(mult * base * houseVal))      // no 10000 cap in the originals
  dayMult(c) = (floor(conditionTimestamp[c] * 30/128 / 3600 / 24) % 7) + 1   // 0.234375 = 30/128
  ```
  So the multiplier is **(the absolute game day on which the condition was inflicted, mod 7) + 1**: anything from 1 to
  7, not "days since it was inflicted". An unset condition has timestamp 0, which gives 1. In the originals, Unconscious
  therefore costs 1..7 times the "wounded" price (wounded means no condition, multiplier 1). It costs the same only when
  it happened on a day number that is a multiple of 7, such as the first game day.
- OpenEnroth (`src/Engine/PriceCalculator.cpp:102-131`) uses `GetConditionDaysPassed` =
  `(now - inflicted).days() + 1` (`src/Engine/Objects/Character.cpp:313-325`, which carries its own "PS - CHECK ??"
  comment) and adds a 10000 cap. That differs from MM6, MM7 and MM8.
- MMerge and MAW add no temple-price hooks. `npc.lua:316` hooks only CanTempleHealPlayer, and the MAW
  `MiscTweaks.lua:748` temple block changes only the skills taught.

### Root cause in OpenYAMM
- A: `game/party/Party.cpp:1205-1238` `updateMemberIncapacitatedCondition` sets Unconscious or Dead and writes
  `conditionStartGameMinutes[...] = 0.0f` (`:1219-1222`, `:1229-1233`). Every HP-driven knockout (`damageMember` at
  `:3059`, and the heal and adjust paths at `:6875` and `:6891`) records no time.
  `Party::applyMemberCondition(..., float gameMinutes = 0.0f)` (`Party.h:708`) also defaults to 0. The Eradicated and
  Zombie calls (`Party.cpp:2995`, `PartySpellSystem.cpp:2759`) pass no time.
- `game/items/PriceCalculator.cpp:44-61` `conditionDaysPassed` returns 1 when the start is `<= 0`. Unconscious therefore
  always gets multiplier 1, the same as wounded, and HP death always costs exactly 5 × Val.
- B: `PriceCalculator.cpp:56-60` computes elapsed days + 1, the OpenEnroth guess; the originals use
  `(inflictedDay % 7) + 1`. `:366` clamps to 10000; the originals clamp only to a minimum of 1.
- The structure is otherwise right: the priority order Eradicated > Petrified > Dead, then minor conditions 0..13
  (`:341-360`), base 5 and 10, and `* houseEntry.priceMultiplier`.

### Scope
Shared gameplay code (`PriceCalculator`, `Party`), so both Standard and MAW are affected, along with all MM6, MM7 and
MM8 temples. No ruleset overrides temple pricing.

### Fix
1. Give Party the current clock. Recording the time at infliction is the authoritative fix; no price fallback.
   - `game/party/Party.h`: add `void setGameMinutes(float gameMinutes);` and `float m_gameMinutes = 0.0f;`.
   - Call it wherever a world runtime moves its clock: `IndoorWorldRuntime::advanceGameMinutes`
     (`IndoorWorldRuntime.cpp:10293-10305`, next to `updateDaysWithoutRest`), the outdoor equivalent
     (`OutdoorWorldRuntime.cpp:8884`), the snapshot or clock restores (`OutdoorWorldRuntime.cpp:8451` and the indoor
     counterpart), and the place where a runtime binds the party.
   - `updateMemberIncapacitatedCondition(Character &member, bool preservationActive, float gameMinutes)`: when
     Unconscious or Dead is newly set, store `std::max(0.0f, gameMinutes)` instead of `0.0f`. Clearing still writes 0.
     ```cpp
     if (!member.conditions.test(unconsciousIndex))
     {
         member.conditionStartGameMinutes[unconsciousIndex] = std::max(0.0f, gameMinutes);
     }
     ```
     Pass `m_gameMinutes` from the three callers (`:3059`, `:6875`, `:6891`).
   - Drop the `= 0.0f` default from `applyMemberCondition` and pass `m_gameMinutes` from callers that have no time, such
     as `Party.cpp:2995` (Eradicated) and `PartySpellSystem.cpp:2759` (Zombie). The alternative is an overload that uses
     `m_gameMinutes`; avoid it if it would hide missing clocks.
2. Use the original multiplier in `PriceCalculator.cpp`:
   ```cpp
   // MM6 0x49e910, MM7 0x4b7fa3, MM8 0x4b65cf: the weekday on which the condition was inflicted, plus one.
   int conditionDayMultiplier(const Character &member, CharacterCondition condition)
   {
       const size_t conditionIndex = static_cast<size_t>(condition);

       if (!member.conditions.test(conditionIndex))
       {
           return 0;
       }

       const float startGameMinutes = std::max(0.0f, member.conditionStartGameMinutes[conditionIndex]);
       return static_cast<int>(std::floor(startGameMinutes / MinutesPerDay)) % 7 + 1;
   }
   ```
   Rename `highestMinorConditionDaysPassed` to match. `templeHealPrice` no longer needs `gameMinutes`: remove the
   parameter from `PriceCalculator.h:80` and from `templeHealCost` (`HouseInteraction.cpp:784`, callers `:1217`
   and `:1704`). Replace `std::clamp(result, 1, 10000)` with `std::max(result, 1)`, matching the originals.
   **Decision for the user:** if exact OpenEnroth-style elapsed days are preferred, skip step 2 and keep only step 1.
   Step 1 alone fixes the reported symptom once at least a day has passed. Step 2 is the faithful version.

### Edge cases
- First game day (start 540 min → day 0): multiplier 1 under both formulas, so unconscious equals wounded that day. That
  is faithful; say so in the tests and the reply.
- Existing saves: members already unconscious or dead with start 0 keep multiplier 1 until healed and knocked out again.
  The infliction time cannot be recovered, so no migration.
- A knockout from Preservation keeps Unconscious while HP stays below zero; its time is set only on the first
  transition (`!test` guard).
- Float precision: `gameMinutes` is a float; at ten game years it is about 5.3M minutes, which stays exact to a minute.
- `conditionStartGameMinutes` is saved (`SaveGame.cpp:1347/1435`), so the format does not change.
- Day-of-week semantics: a later infliction can be cheaper, for example day 6 gives 7 and day 7 gives 1. That is
  faithful but surprising; mention it in the reply.

### Verification
Doctests in `tests/HouseDialogueRegressionTests.cpp`, next to `"temple healing price uses condition age and house
multiplier"` (`:3991`):
- That existing test encodes elapsed days ("Dead 2 days ago" → `Heal 150 gold`). With step 2, now = 540 + 10 days and
  start = now - 2 days, which is day 8 → 8%7+1 = 2 → 2×5×10 = **`Heal 100 gold`**. Update the expectation and the title.
  This assumes the harness clock starts at 540 min; check its initial `gameMinutes()` before fixing the number.
- New test, "unconscious from damage records its start time": advance the harness clock several days (to day 3), set
  health above 0, call `party.damageMember(...)` until HP < 0 but HP+End ≥ 1. Check Unconscious, check
  `conditionStartGameMinutes[Unconscious] == worldRuntime().gameMinutes()`, and check that the heal label is
  `(3%7+1)×1×Val`. A full-HP member with HP below max (wounded) gets `1×Val`.
- New test for Dead from damage: base 5 × the day multiplier.
- New pure test for `PriceCalculator::templeHealPrice`, using a `Character` with Unconscious started at day 0, 6 and 7
  (multipliers 1, 7 and 1). Add it to the same file or to `tests/GameplayRuleRegressionTests.cpp` next to the
  `playerMerchant` checks (`:10731`).
- Check that `"event-applied conditions use absolute game time for temple healing price"` (`:4039`) still holds: Weak
  at one year (day 336, 336%7=0) → 1 → `Heal 10 gold`, unchanged.
- Build `openyamm_unit_tests`, then run `--test-case='*temple*'`.
