# Discord bug reports, 2026-10-25: fix plan

The working plan for the Standard MMerge bugs that players reported on Discord (24–25 October 2026), plus two later
reports from the user. These are generic MMerge and engine fixes that also apply to MAW; none is MAW-specific.
Everything below comes from reading the code against `main` at 2476b1e90. No fix has been built or run yet.

**Status: plan only. Change no code until the user says to start.**

The detailed plans are next to this index. Each gives the files and functions, a pseudo-diff, edge cases and tests:

| Plan | Area |
|---|---|
| [A_inn_rest.md](A_inn_rest.md) | Inn rest indoors, tavern food amount, weekday on the rest screen |
| [B_shops_guilds.md](B_shops_guilds.md) | House entry audio, alchemist stock, magic guild membership, MM6 light/dark path, dismiss sound |
| [C_map_events.md](C_map_events.md) | TextTable quotes, decoration collision and visibility, Evenmorn treasure, Haunted Mansion face, campfires |
| [D_combat_spells.md](D_combat_spells.md) | Spell targeting and range, attack-spell fallback, clubs, incapacitated speech, Ooze collision |
| [E_ai_tb_arcomage.md](E_ai_tb_arcomage.md) | Turn-based doors, Arena groups, turn-based monster speed, Arcomage AI, outdoor slopes |
| [F_temple.md](F_temple.md) | Abandoned Temple cages and fireball trap, temple healing price |

Line numbers in the plans may have moved, so re-read the code before each edit.

## Working rules for this pass

- Never `git add`, commit, stash or reset. Edits stay unstaged.
- `game/indoor/IndoorSceneRuntime.cpp`, `game/gameplay/InteractiveDecorationRules.*` and the `*SceneRuntime` files
  contain the user's uncommitted `int64_t` stat-snapshot edits. Keep them intact (see E1).
- Don't edit generated Lua event files; use overlays such as `Global_mm6_mmmerge.lua` or the `*_mmmerge.lua` map files.
- Fix shared gameplay code, not `IndoorGameView`/`OutdoorGameView`. Several bugs exist only because logic lives in one
  view.
- After each batch:
  - build with `cmake --build build --target openyamm openyamm_unit_tests -j25`;
  - run the focused tests with `./build/tests/openyamm_unit_tests --test-case='*pattern*'`;
  - run the full unit suite before calling the pass done.
- Headless scenarios: `./build/game/openyamm --headless-run-scenario <yml>`.

## Defaults taken (2026-10-25, user approved fixing 1–22 plus A3; the user may still override)

1. E3: keep the 1.75 pursue factor and add the turn-based ×5/3 multiplier.
2. F2: the faithful weekday formula (all three executables agree), with the infliction time recorded.
3. F1a: `hngncge2` for the six cages, marked unconfirmed in the overlay comment.
4. C5: MMerge's name list, with an explicit save migration for the decoration state indices.
5. B4: port the reference script as it is; keep the current class 47 display name.
6. B2: remove duplicate recipe scrolls by name.
7. A3 (weekday on the rest screen) is included.
8. D5 (Ooze) and E5 (outdoor slopes) are excluded.
9. The `int64_t` working-tree edits mentioned below are no longer present; the tree was clean at e704b6659.

## Decisions needed before or during the work

1. **Turn-based monster speed (E3).**
   - Default: keep the user's 1.75 pursue factor (2026-10-22) and add the original ×5/3 turn-based multiplier. That gives a goblin
     about 233 units per turn; the original gives 267 and the current build 140.
   - Alternative: a separate pursue factor of 2.0 in turn-based mode to match the original exactly.
2. **Temple healing formula (F2).**
   - Faithful: the price multiplier is the weekday the condition was inflicted plus one (1–7), with no 10000 cap.
     This is verified in all three executables, but it looks random to players.
   - Alternative: OpenEnroth's days elapsed since infliction, plus one.
   - Either way, the time of infliction must start being recorded. That part is the actual bug fix.
3. **Abandoned Temple cage sprite (F1a).** Six cages have empty decoration names upstream, so we can't tell which sprite
   the original used. The proposal is `hngncge2` (hanging cage); `Bonecage` or `empty` are possible. Confirm against MM6.
4. **Campfire list (C5).**
   - Matching MMerge's names adds the MM6 fires.
   - MM8 `dec04` then stops giving food, as in MMerge.
   - The change shifts the saved decoration state indices in maps players have already visited, so it needs an explicit
     save migration with a version bump. Is that acceptable, or should the work stop at adding names without shifting
     the indices?
5. **MM6 light/dark promotion (B4).** Port `reference/mmmerge/Scripts/Global/Quest_EnrothDarkArts.lua` as it is
   (Paradise Valley for dark). The player remembered Frozen Highlands, which may be a newer Rodril build. Class 47 is
   "Master Necromancer" in `class.txt` but hardcoded as "Dark ArchMage" (`SkillData.cpp:264`). Which name?
6. **MAW interactions (for the MAW owner, not blocking).**
   - A tavern fill of up to 60 days can exceed the Insanity food cap until the next map change (A2).
   - MAW's gem replacement can swap out the new alchemist bottles (B2).
7. **Ooze collision (D5).** Proposed radius 80 and height 64, instead of MMerge's 47 and 120. Check in game before
   changing it, and record the deviation.
8. **Alchemist recipe block (B2).** Items 700–731 and 1542–1573 are duplicate recipe sets. Pick the MM7 or the MM8 set
   per shop, or remove duplicates by name.

## Work order

Batches are grouped by the code they touch. Sizes: T trivial, S small, M medium.

### Batch 1: indoor/outdoor parity in shared code

- [x] **A1 Inn rest indoors.** Must fix; covers Stone City, Celeste, The Pit, and the calendar report. S.
  - Shared `innRestDurationMinutes` in `HouseInteraction`, with merged ids 243/246/248.
  - `startInnRest(houseId)` called from `GameplayScreenRuntime::executeActiveDialogAction`.
  - Delete the outdoor copies.
  - Check `applyMapReentryReset()` indoors.
  - Done as planned. Scenario `tests/scenarios/mm7/stone_city_inn_rest.yml` with a new `assert: {game_hour: N}`.
    Indoors the reset doesn't re-arm legacy timers (outdoors it does); left as it was.
- [x] **B1 House entry greeting and door sounds indoors.** Should fix. S.
  - Move the entry audio into `GameplayScreenRuntime::updateHouseEntryAudio`; both views call it.
  - Took the dedupe: one `GameplayScreenRuntime::updateHouseDialoguePresentation` (video and audio) replaces both
    view functions. House 17's elf greeting is not changed.
  - Side check: the Stone City weapon shop (house 17) greets with an elf line (data).
- [x] **E1 Doors in turn-based mode.** Must fix. S.
  - Split out `IndoorSceneRuntime::advanceMechanisms`.
  - `IndoorRenderer.cpp:3800` runs only that part in turn-based mode.
  - Extend `tests/IndoorMovingFloorRuntimeTests.cpp`.

### Batch 2: small rule fixes

- [x] **A2 Tavern food** equals the house `Val` (`priceMultiplier`) instead of a hardcoded 14. Must fix. T.
- [x] **D3 Clubs** exempt from the learned-skill requirement (`GameMechanics.cpp` `requiresLearnedSkillToEquip`).
  Must fix. T.
- [x] **E2 Arena opponents** get `group = 1` (MM8 `0x4bc74f`, OpenEnroth). Extend `tests/ArenaRuntimeTests.cpp`.
  Should fix. T.
- [x] **E3 Turn-based ×5/3 speed** in `GameplayActorAiSystem::updateActors` during the wait stage, capped at 1000.
  Optionally re-plan idle actors at the start of the wait stage. Should fix. T–S. Decision 1.
  - Re-plan included: entering the wait stage clears the stand timers of standing, unstunned actors (both worlds).
- [x] **C5 Campfire name list** set to MMerge's `ckfyr00, cmpfyr00, fire01, 7dec02, dec24, dec25`. Should fix.
  T, or M with the migration. Decision 4.
  - Delete the dead duplicate classifier in `OutdoorGameView.cpp:592-812` and its enum.
  - Migration is lazy: the shift is real (MM6 outdoor and indoor maps with `ckfyr00`/`cmpfyr00`, MM7 `fire01`
    dungeons, MM6 and MM8 maps with `dec04`), but renumbering needs the map's entities, which BLV maps only have
    once loaded. Save version 129 marks every older map state (`EventRuntimeState::legacyCampFireDecorVars`, saved);
    entering the map renumbers its decorVars and MAW's used stat decorations, then clears the mark.

### Batch 3: tables and map data

- [x] **C1 TextTable quotes.** Must fix.
  - A leading `"` opens a quoted cell only if its closing quote comes before the next tab.
  - Restores scrolls 1521, 1522, 1525, 1527 and 1528, including the Red Dwarf Mines scroll.
  - The plan surveyed every TXT table: none of them changes except `scroll.txt`. Extend `tests/TextTableTests.cpp`.
  - Done as planned. Re-checked all 237 engine/world tables: cell contents identical except `scroll.txt` and its
    `_legacy` copy. Truncated item names keep their literal leading quote (cosmetic).
- [x] **C4 Haunted Mansion portrait.** Should fix. S.
  - Read the stored texture index at face `+0x3A`.
  - Resolve animated faces through the texture frame table before the liquid check.
  - Only 7d37 face 1844 is affected.
  - Deviation: the stored index is used only when the face name is no frame-table sequence and the indexed sequence
    is not a liquid. Trying names before liquids, as planned, would have moved animated water (`7hdwtr000`) off the
    liquid shader. `IndoorFace::textureFrameTableIndex` now holds face +0x3A (the dead +0x10 read is gone).
- [ ] **F1a Abandoned Temple cages.** Should fix. S. Decision 3.
  - Dropped by the user (2026-10-25): the lost cage names come from MMerge's conversion; leave them.
  - A new indoor overlay key `initial_state.entity_overrides`.
  - A new `assets_dev/worlds/mm6/maps/6d02_1.scene.yml` naming entities 107–112.
- [x] **F1b Abandoned Temple fireball trap.** Should fix.
  - No game bug found; no runtime change. The trap fires and hits the party through the open door 6, also when the
    cage is looted with the interact key. With door 6 shut the fireball bursts on the door, 800 units from the cages
    and out of its 512 reach; OpenEnroth collides event spells with door faces the same way. The party can only reach
    the cages through door 6, so in play the trap hits.
  - The headless runs had shown no damage because scenarios took the Immortal cheat from the local `settings.ini`.
    `ScenarioRuntimeDriver` now turns it off for scenarios.
  - Scenario `tests/scenarios/mm6/abandoned_temple_cage_trap.yml`: door shut, no damage; door open, damage.

### Batch 4: outdoor decoration visibility and collision

- [x] **C2 Hidden decorations stop colliding outdoors.** Should fix. S.
  - A shared hidden predicate and a per-frame hidden mask, passed to party and actor movement.
  - Drop the load-time skip of invisible decorations.
  - Indoors already does this.
  - Done with shared `isDecorationHidden`/`hiddenDecorationEntities` (indoor collision uses it too); the clear rules
    ride on `OutdoorDecorationCollisionSet`. The mask is rebuilt every frame like indoors (no revision counter).
- [x] **C3 Map-file invisible flag and the Evenmorn treasure.** Must fix (exploit). M.
  - Done; `OutdoorInteractionController::isDecorationEntityHidden` also covers decoration models, lights and the
    Wizard Eye markers. Only `flower07` and the three statuette shrines (`dec94`–`dec96`, shown by event 452) carry
    the flag outdoors, plus the MM6 Party Start markers; none should be visible by default.
  - Event overrides take precedence; otherwise the map's invisible flag decides draw and click, in the shared
    `resolveDecorationBillboardSpriteId`.
  - Rewrite `MM7.UpdateEvenmornObeliskTreasure`:
    - `evt.SetSprite(20, ...)`;
    - shown when QBits 676–689 are all set and the hour is 0;
    - `IsAtLeast` tests for equality;
    - run it on map load and from a 30-minute timer.
  - Other invisible outdoor decorations (`dec94`–`dec96` in 7out06, 7out13 and out14) are fixed by the same change.

### Batch 5: combat and spells

- [x] **D1 Spell actor targeting.** Must fix (range exploit); should fix (no valid target).
  - Drop `hasDetectedParty` from the three quick-target lists.
  - Add a shared `PartySpellSystem::isUsableSpellActorTarget` with a 5120 range. Use it for quick, hovered, preset and
    pending targets.
  - Leave `setMapActorHostileToParty` unchanged (see the plan).
  - Keep scripted casts unlimited.
  - Done; the pending click check is range only (`isActorWithinSpellTargetRange`), so corpses stay targetable. An
    attack's preset target travels as `TargetQueries::preferredActorIndex`. No quick-cast scenario step exists and
    headless runs have no view lists, so `lifedrain_reach.yml` became unit tests; the attack path's reach is in
    `tests/scenarios/rulesets/attack_spell_no_target.yml`.
- [x] **D2 Attack spell with no target swings the weapon.** Should fix. S.
  - A `NoTarget` result from `tryBeginAttackCast`.
  - **Update `tests/scenarios/rulesets/maw_assassin_attack_spell.yml`**: Blades is now really cast.
  - Done as planned; the scenario now checks the attack's cast spent the points (the next attack swings), then
    resets them to 5 for the direct `cast_spell`.
- [x] **D4 No speech from incapacitated members.** Should fix. S.
  - Add `canMemberSpeak` in `GameplaySpeechRules`, with exceptions for Dying, CheatedDeath and Awaken.
  - Dying plays only when health drops from above 0.
  - Falling plays only if the member could act before the hit.
  - Done as planned (`playSpeechReaction` checks `canMemberSpeak`, so the face animation is skipped too).

### Batch 6: houses and economy

- [x] **F2 Temple healing price.** Should fix. S–M. Decision 2.
  - `Party` gets the current game time and records it when Unconscious, Dead, Eradicated or Zombie is inflicted.
  - Then the multiplier formula.
  - Update the expectation in the existing test at `HouseDialogueRegressionTests.cpp:3991`.
  - Done. Handing the time to every damage, heal and condition call (about 50, including Party's own regeneration and
    fall damage and the MAW rules) was not practical, so the world runtimes publish every clock change
    (`Party::setGameMinutes` on bind, advance and snapshot restore); `applyMemberCondition` without a time uses it.
    Weekday multiplier, no 10000 cap; `templeHealPrice` lost its time parameter.
- [x] **B2 Alchemist stock.** Should fix. S. Decision 8.
  - Standard stock: six empty bottles (item 220) in the top row.
  - Special stock: six recipe scrolls in the top row.
  - The other rows stay random.
  - Done; recipes are `Mscroll` items named "... Recipe", first id per name (so 700-731 at MM8 prices everywhere).
    MAW's gem swap now skips the alchemist's empty bottles; recipe scrolls stay swappable, as in MAW.
- [x] **B3 Magic guild membership.** Should fix. S–M.
  - Map house type to guild type 5–15.
  - Gate MM6 and MM7 only; on MM7 exempt the Light and Dark guilds.
  - Play the members-only sound.
  - Existing guild tests and scenarios may need membership set first.
  - Done as planned (`houseEntrySoundType` drives the entry greeting). Only the "dwi guild skill learning" test
    needed membership: its house 139 is MM6 Free Haven's Air guild. No scenario buys from a guild without joining.

### Batch 7: content ports

- [x] **B4 MM6 Path of Light / Path of Dark.** Should fix. M. Decision 5.
  - Topics 10001 and 10002 in `Global_mm6_mmmerge.lua` plus `npc_topic.txt` rows.
  - Attach them to slot 4 of NPCs 1030, 1040, 1057, 1031 and 795.
  - Add the engine Lua functions `GetPlayerSkill`, `SetPlayerSkill` and `ForgetPlayerSpell`.
  - Done; OpenYAMM class ids equal MMerge's `const.Class`, so the script's tables are used as they are. The double
    confirmation is kept: MMerge's "two clicks within 2 s" (no clock in our Lua) became "the first click of a
    conversation shows the advert, the next click asks", then the typed "yes". `SetPlayerSkill` shares the
    `evt.Set` skill code. Scenario `tests/scenarios/mm6/path_of_light_dark.yml`.

### Batch 8: Arcomage

- [x] **E4 Arcomage AI.** Should fix. S.
  - Score the effect set the card's condition actually selects (make `evaluateCondition` public).
  - A field of 99 scores as the other side's value minus your own.
  - Explicit scores for Shift and Flood Water.
  - Extend `tests/ArcomageRegressionTests.cpp`.
  - Done: `ArcomageAi` scores the selected bundle, with 99 read in the rules' order. Shift and Flood Water come from
    `ArcomageRules::specialCardEffect`, which the rules also apply. A card whose effects change nothing scores 0, so
    the AI discards it rather than spend resources. The kill check includes building damage past the wall. Tests
    cover masteries 1 and 2.

### Batch 9: later user reports

- [x] **G1 Horseshoes glitter on the ground in every world.** Done the user's way: value 0 for 656, 1448 and 2083 in
  `items.txt`. The MM6 one's material also goes from `Special` to `0`, so all three get the same quest-item sparkle
  and follow the same rules everywhere. Shops now refuse to buy horseshoes. The C++ change and the test below were not needed.
  - Cause: the ground sparkle (`worldItemSparkle`, `game/items/WorldItemShape.cpp`) keys on rarity and value. The MM6 horseshoe
    (2083) has material `Special` in MMerge's ITEMS.txt, so it gets the artifact sparkle. The MM8 one (656, material `0`)
    and the MM7 one (1448, material `5`) are Common and worth 100, so they get none.
  - Fix: give every horseshoe the MM6 sparkle by item type (the same rule `InventoryItemUseRuntime` uses to recognise a
    horseshoe), not by editing the merged table's material.
  - Test: a doctest on `worldItemSparkle` for 656, 1448 and 2083.

### Optional (only if the user asks)

- [x] A3 Weekday on the rest screen (feature request; the original shows none).
  - `{weekday}` placeholder on its own `RestWeekdayText` row above the time ("Monday 9:03 am" did not fit one
    row); the date block rows are respaced 24 units apart. No shared calendar helper.
- [ ] D5 Ooze collision values. Decision 7.
- [ ] E5 Remaining outdoor slope differences: steep 3D-model faces slide with 4 × gravity, and faces up to 128 high
  count as walkable steps where the original allows 32.
- [ ] Dismiss sound: MM7 plays nothing. MM8 party members need a Rizin check of the MM8 binary first.

## Not fixed in this pass (for the bug thread)

- **Fixed on main, not released yet:**
  - sleep portraits while resting (ddcf6696d);
  - indoor and steep-terrain slopes, including the Alvar Ogre Fortress (ddcf6696d).
- **Already fixed in v1.11:** "Eating Halberd". It was Labyrinth Grapple, whose unidentified name is "Halberd", matching
  "apple" (7fdb25667).
- **Not bugs:**
  - Joining a guild does take gold (100, covered by a unit test); probably confusion caused by B3.
  - The rest screen already shows the date, as in the original.
  - The New Sorpigal goblin-camp fire has its own ambush event and gives no food, as in MMerge.
  - No version of the scripts ever gives rings from fires.
  - Spear in the left hand: withdrawn by the reporter.
- **3D model reports** (hands, shoulders, beards and faces of MM6/MM7 humanoids, troll walk, Fire Elemental): a
  separate art backlog, outside this pass.
