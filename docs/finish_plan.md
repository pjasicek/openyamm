# Finish Delta Plan

Date: 2026-03-30

Scope:
- Remaining systems and parity gaps needed to move OpenYAMM toward a feature-complete MM8 gameplay loop.
- OE and OpenMM8 are reference inputs only.
- This document is intended to be executable by follow-up Codex sessions.

Primary references:
- OpenYAMM current runtime:
  - `game/party/Party.h`
  - `game/party/Party.cpp`
  - `game/tables/ItemTable.h`
  - `game/tables/ItemTable.cpp`
  - `game/gameplay/HouseInteraction.cpp`
  - `game/gameplay/HouseServiceRuntime.cpp`
  - `game/events/EventRuntime.h`
  - `game/events/EventRuntime.cpp`
  - `game/outdoor/OutdoorWorldRuntime.cpp`
  - `game/outdoor/OutdoorGameView.cpp`
  - `game/tables/MapStats.h`
  - `game/tables/MapStats.cpp`
  - `game/tables/HouseTable.h`
  - `game/tables/HouseTable.cpp`
- MM8/OpenYAMM data:
  - `assets_dev/Data/EnglishT/ITEMS.txt`
  - `assets_dev/Data/EnglishT/rnditems.txt`
  - `assets_dev/Data/EnglishT/STDITEMS.TXT`
  - `assets_dev/Data/EnglishT/SPCITEMS.TXT`
  - `assets_dev/Data/HOUSE_DATA.txt`
  - `assets_dev/Data/HOUSE_ANIMATIONS.txt`
  - `assets_dev/Data/NPC_TOPIC_TEXT.txt`
  - `assets_dev/Data/ui/gameplay.yml`
  - `assets_dev/Data/ui/dialogue.yml`
- OE references:
  - `reference/OpenEnroth-git/src/Engine/Objects/Item.cpp`
  - `reference/OpenEnroth-git/src/Engine/Objects/ItemEnums.h`
  - `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp`
  - `reference/OpenEnroth-git/src/Engine/PriceCalculator.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/UIPopup.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Houses/Shops.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Houses/Temple.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Houses/Transport.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Houses/Tavern.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Houses/Bank.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/UIRest.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Books/MapBook.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Books/QuestBook.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/Books/AutonotesBook.cpp`
  - `reference/OpenEnroth-git/src/Arcomage/Arcomage.cpp`
  - `reference/OpenEnroth-git/src/Arcomage/Arcomage.h`
  - `reference/OpenEnroth-git/src/Engine/SaveLoad.cpp`
  - `reference/OpenEnroth-git/src/GUI/UI/UIGameOver.cpp`
- OpenMM8 references:
  - `/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/Items/Item.cs`
  - `/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/Items/ItemEnchant.cs`
  - `/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/Items/ItemGenerator.cs`

## Global Priorities

Recommended implementation order:
1. Standard / special enchant application.
2. Shared random item generation migration.
3. Artifacts / relics / special items / equip restrictions.
4. Consumable inventory interactions.
5. Transport and map transitions.
6. Save/load.
7. UI books and rest/menu/game-over flows.
8. Rendering environment polish.
9. Arcomage.
10. Adventurer's Inn and MM8-specific systems.

Rationale:
- A large part of the remaining gameplay now depends on completing the already-landed item-state foundation.
- Save/load should land before too many stateful systems accumulate.
- Rendering polish should not block systems that change gameplay state.

## 1. Broken / Unidentified Item State, Inspect, Repair, Identify

### Current OpenYAMM
- `InventoryItem` in `game/party/Party.h` already has:
  - `identified`
  - `broken`
  - `stolen`
  - `standardEnchantId`
  - `specialEnchantId`
  - `artifactId`
- Direct inspect-driven identify/repair is implemented for:
  - inventory items
  - equipped items
  - world-ground items
- Shop `Identify` and `Repair` are implemented in `game/gameplay/HouseServiceRuntime.cpp`.
- Broken equipped items already behave as non-functional in gameplay stat/combat resolution.
- Broken/unidentified tint behavior is partially implemented in `game/outdoor/OutdoorGameView.cpp`:
  - no tint in normal inventory
  - held/equipped items tint by state
  - shop identify/repair overlays tint only relevant targets
- Ground item drop/pickup already preserves broken/unidentified state.

### OE / OpenMM8 Findings
- OE item flags include `identified`, `broken`, and `stolen`.
- OE broken items:
  - stay equipped
  - occupy the slot
  - behave as non-functional
  - broken weapons effectively act like not equipped
- OE popup:
  - broken items are red-tinted
  - title shows `Broken`
  - unidentified items use `unidentifiedName`
  - active-character inspect can auto-identify/auto-repair if skill allows
- OE identify/repair success test:
  - mastery multiplier `1 / 2 / 3 / 5`
  - compared against item `identifyAndRepairDifficulty`
  - GM always succeeds
- OE shop identify/repair:
  - use shop-family compatibility similar to sell
  - price is derived from item value, merchant skill, and house multiplier
  - identify success sets identified
  - repair success clears broken and sets identified
- OpenMM8 confirms the right item-state shape:
  - `IsIdentified`
  - `IsBroken`
  - `Enchant`

### Data
- `ITEMS.txt`
  - includes `unidentifiedName`
  - identify/repair difficulty is already parsed into `ItemDefinition::identifyRepairDifficulty`
- Speech/reaction data should stay data-driven through existing sound/speech tables.

### Implementation Notes
1. Keep the landed item state shape stable and reuse it as the base for enchants/artifacts/save data.
2. Extend `ItemDefinition` further with:
   - item rarity classification
   - more explicit effect metadata needed by later points
3. Continue centralizing item state helpers:
   - `isFunctional()`
   - `isIdentifiedForDisplay()`
   - `canCharacterIdentify(...)`
   - `canCharacterRepair(...)`
4. Remaining delta for inspect/UI parity:
   - exact OE popup/title/body wording for broken/unidentified
   - final broken-item label parity
   - audit all tint cases against OE
5. Remaining delta for direct character-side use:
   - confirm all identify/repair reactions/sounds/text parity paths
   - keep failure speech mapping data-driven
6. Add any missing data-driven speech mapping for failure:
   - `I can't do that`
   - `I don't know`

### Good To Know
- This foundation is already in place.
- The next dependent systems are points 3, 4, 5, 6, and save/load.

## 2. Shop Item Quality / Location Tier Parity

### Current OpenYAMM
- Shop quality is now partially data-driven.
- `HouseEntry` already carries:
  - `standardStockTier`
  - `specialStockTier`
- `HouseServiceRuntime.cpp` now derives stock quality from `HOUSE_DATA.txt` columns:
  - `Val` -> standard stock tier
  - `A` -> special stock tier lift
  - `C` -> refresh interval
- Standard/special/guild stock generation is no longer using the old rounded-`priceMultiplier` heuristic.
- Remaining delta is tuning and parity, not basic house-tier wiring.

### OE / OpenMM8 Findings
- OE uses per-house variation tables for standard/special stock, not just price multiplier.
- Shop generation is house-quality driven and low-tier houses do not roll high-tier stock.
- MM8 house data likely exposes this through `A / B / C` columns in `HOUSE_DATA.txt`, but current OpenYAMM does not decode them into shop-quality semantics yet.

### Data
- `HOUSE_DATA.txt`
  - investigate columns `A`, `B`, `C` as shop treasure-quality drivers
- If insufficient, add supplemental TSV:
  - `HOUSE_SHOP_RULES.txt`

### Implementation Notes
1. Keep `HOUSE_DATA.txt` as the primary source:
   - `Val` -> standard tier
   - `A` -> special tier lift
   - `C` -> refresh
2. Continue tuning the selection rule to match believable MM8 stock by house type:
   - standard stock ceiling
   - special stock bias
   - low-tier duplicate policy where shelves must stay visually full
3. If MM8 parity still needs more house-specific nuance, add a supplemental rules table keyed by house id/type.
4. Keep stock persistent and seeded per party so fresh starts vary.

### Good To Know
- This is now partially landed and should share the same generator with point 4.

## 3. Standard / Special Enchants

### Current OpenYAMM
- Loader groundwork exists:
  - `game/items/ItemEnchantTables.cpp`
  - `assets_dev/Data/EnglishT/STDITEMS.TXT`
  - `assets_dev/Data/EnglishT/SPCITEMS.TXT`
- Runtime `InventoryItem` already has enchant/artifact ids.
- What is still missing is actual enchant application:
  - suffix naming
  - stat/resist/skill effects
  - inspect descriptions
  - generation-time assignment

### OE / OpenMM8 Findings
- OE loads standard and special enchantment tables and applies them during treasure generation and `Enchant Item`.
- OpenMM8 has a clean split:
  - `ItemEnchant`
  - generator logic
  - application logic for stat and special effects
- Special enchant eligibility is correlated with treasure level.
- Standard enchants and special enchants use different chance tables and rarity gating.

### Data
- `STDITEMS.TXT`
- `SPCITEMS.TXT`
- `rnditems.txt`
- `ITEMS.txt`

### Implementation Notes
1. Add loaders:
   - `StandardItemEnchantTable`
   - `SpecialItemEnchantTable`
2. Represent enchant state in `InventoryItem`.
3. Implement shared effect application:
   - direct stat bonuses
   - resist bonuses
   - skill bonuses
   - attack-side effects
   - special monster-family multipliers
4. Add generated name formatting:
   - base item name + suffix/prefix as defined by enchant data
5. Update inspect popup:
   - identified items show enchant description/effect
6. Integrate enchant generation into shared item generator:
   - standard enchant chance
   - special enchant chance
   - treasure-level gating
7. Keep effect semantics in code, but keep mappings and text data-driven.

### Good To Know
- Standard stat-only enchants are easy and should land first.
- Special combat-side enchants should be phased in by effect family.

## 4. Shared Random Item Generation For Chests / Monsters / Shops

### Current OpenYAMM
- Some item generation exists and the new skeleton is present:
  - `game/items/ItemGenerator.cpp`
  - `game/items/ItemRuntime.cpp`
- `rnditems.txt` is already loaded.
- Shops already use the new generator for purchased items.
- Chest/monster/shop generation is still not fully centralized under one generator policy.

### OE / OpenMM8 Findings
- OE uses a shared item-generation pipeline:
  - treasure level remap against map treasure level
  - weighted roulette over `rnditems`
  - optional enchant/artifact handling layered after base item selection
- OpenMM8 confirms the same roulette-style generation.

### Data
- `rnditems.txt`
- `MapStats` treasure level
- monster treasure level
- chest treasure level
- house quality from point 2

### Implementation Notes
1. Create a single generator service:
   - `ItemGenerator`
2. Inputs:
   - source kind: chest / monster / shop / event
   - source treasure level
   - map treasure level
   - optional family constraints
3. Outputs:
   - fully populated `InventoryItem`
4. Migrate:
   - chest generation
   - monster corpse loot
   - shop stock generation
   - event random-item rewards
5. Layer in:
   - enchant generation
   - artifact/special generation

### Good To Know
- Without this generator, shop parity and chest parity will continue to drift separately.

## 5. Artifacts / Relics / Special Items / Equip Restrictions

### Current OpenYAMM
- Artifact/relic/class/race restrictions are not enforced yet.
- Runtime `InventoryItem` already has `artifactId`, so the data shape is ready.

### OE / OpenMM8 Findings
- OE treats artifacts/relics/special items separately from normal enchant items.
- OE keeps artifact spawn tracking so unique items are not generated repeatedly.
- OpenMM8 has MM8-specific restrictions for some items:
  - race restriction
  - class restriction
- Some item effects are handled directly in code.

### Data
- MM8 artifact and special item semantics likely need a new supplemental table if `ITEMS.txt` is not sufficient.
- OpenMM8 C# code is the best MM8-specific effect reference.

### Implementation Notes
1. Add rarity classification to `ItemDefinition` and `InventoryItem`.
2. Add persistent artifact-found state to `Party` save data.
3. Add equip restriction fields:
   - race
   - class
   - doll type already partially exists
4. Add artifact/special effect dispatcher.
5. Integrate artifact generation into shared item generator with uniqueness rules.

### Good To Know
- Implement restrictions before finalizing Adventurer's Inn roster inspection, because recruitable characters may carry restricted items.

## 6. Inventory Item Use On Portrait / Doll

### Current OpenYAMM
- Equipping through hold-item + click exists.
- Special inventory interactions are not implemented yet.

### OE / OpenMM8 Findings
- Spell scrolls cast and are consumed.
- Spell books teach a spell if eligible and are consumed on success.
- Potions apply their effect.
- Message scrolls open a text window and are not consumed.
- Horseshoes add 2 skill points and are consumed.
- These behaviors are driven by item type and data, not by ad hoc UI logic.

### Data
- `ITEMS.txt`
- readable scroll text table:
  - use MM8 data source equivalent of `SCROLL.txt`
  - if absent, identify the MM8 table used for readable scroll text

### Implementation Notes
1. Add item-use action classification:
   - equip
   - cast scroll
   - learn spell
   - consume potion
   - read message scroll
   - use horseshoe
2. Route hold-item + portrait click through one shared item-use dispatcher.
3. Reuse spell backend for:
   - spell scrolls
   - spell books when they grant spells
4. Add a readable-scroll inspect window:
   - separate from item inspect
   - data-driven text
5. Add correct consume / non-consume behavior.

### Good To Know
- This depends on point 1 for identified state and on spell backend already being present.

## 7. Adventurer's Inn

### Current OpenYAMM
- Not implemented as a real service UI.
- Diagnostics and constants already acknowledge the Adventurer's Inn as a future house mode.

### OE / OpenMM8 Findings
- No OE reference.
- This is MM8-specific and must be designed in OpenYAMM.
- MM8 quest/NPC flows imply displaced characters can be sent to the Inn.

### Data
- likely house row in `HOUSE_DATA.txt`
- recruitable roster data from party/NPC definitions
- new UI YAML required

### Implementation Notes
1. Add new YAML layout.
2. Add house backend mode:
   - show resident roster
   - inspect candidate
   - invite if party has room
3. Support:
   - level
   - class
   - key skills/stats
   - current equipment summary if desired
4. Decide if Adventurer's Inn is party-persistent only or shared-world-persistent.

### Good To Know
- Do not block the rest of service houses on this.
- Treat it as an MM8-specific feature after common systems stabilize.

## 8. Event System Completeness

### Current OpenYAMM
- Event runtime already exists and is substantial.
- Missing pieces are parity/audit items, not total absence.

### OE / OpenMM8 Findings
- MM event system includes:
  - click triggers
  - mouse-over triggers
  - move-over / collision-like triggers
  - map leave/reload/timer triggers
  - texture swaps, doors, chests, stateful decorations, transitions
- User specifically wants:
  - clickable textures / faces
  - move-over party-capsule interaction

### Data
- map EVT sources
- bmodel/facet metadata
- door/face attributes already parsed in map assets

### Implementation Notes
1. Build a parity matrix:
   - supported opcode
   - unsupported opcode
   - partially supported semantics
2. Audit face and decoration trigger routing:
   - click
   - mouse-over
   - move-over/capsule
3. Add any missing event opcodes and missing target resolution.
4. Add tests for each event family.

### Good To Know
- This is a cross-cutting audit point and should be attacked incrementally, not as one giant patch.

## 9. Arcomage

### Current OpenYAMM
- Tavern submenu exists.
- Rules and victory-condition text plumbing exists.
- Gameplay is still not implemented.

### OE / OpenMM8 Findings
- OE has a full Arcomage engine and UI.
- Victory conditions differ by tavern.
- For MM8/OpenYAMM, tavern-specific victory conditions can be parsed from `NPC_TOPIC_TEXT.txt`:
  - generic rules: topic `136`
  - tavern-specific conditions: topics `137..149`

### Data
- `NPC_TOPIC_TEXT.txt`
- tavern house ids
- tavern-to-rules mapping

### Implementation Notes
1. Parse rules text into structured `ArcomageRules`:
   - destroy tower
   - reach tower height
   - reach resource threshold
2. Implement rule parser once, then cache structured rules.
3. Recreate gameplay state machine:
   - decks
   - card effects
   - turn flow
   - AI
   - win/loss persistence
4. Add dedicated Arcomage UI state.

### Good To Know
- This is one of the largest missing standalone systems.
- Leave it late unless taverns are a current blocker.

## 10. Rest Screen UI

### Current OpenYAMM
- No dedicated rest screen UI yet.
- Some rest/time logic already exists in gameplay and taverns.

### OE Findings
- OE has a dedicated rest screen with:
  - rest 8 hours
  - wait until morning
  - wait 1 hour
  - wait 5 minutes
  - food requirements
  - time/day display

### Data
- new YAML layout needed

### Implementation Notes
1. Add dedicated rest screen state and YAML.
2. Reuse party recovery and time advance backend.
3. Add food-cost logic and rest interruption hooks.

## 11. Full Map UI, Notes UI, Quest UI

### Current OpenYAMM
- No full-screen book UIs yet.
- Gameplay HUD already has top buttons and compass/minimap scaffolding.

### OE Findings
- OE has:
  - Map Book
  - Quest Book
  - Autonotes / Notes / Quick Reference
- Map book supports zoom and hover hints.

### Data
- existing quest / autotnote data
- learned teacher markers likely need supplemental runtime data

### Implementation Notes
1. Add separate YAML/layout for each book UI.
2. Reuse top-bar/button conventions.
3. Add learned-location markers for teachers as an OpenYAMM extension.

## 12. Compass

### Current OpenYAMM
- HUD art exists in `gameplay.yml`.
- Need runtime audit of actual yaw-driven rendering.

### OE Findings
- OE scrolls/positions compass art from party yaw.

### Implementation Notes
1. Audit current compass runtime.
2. If incomplete, wire party yaw to compass render.

## 13. Save / Load

### Current OpenYAMM
- No full gameplay save/load backend yet.
- Current runtime now has more persistent state than the original plan snapshot:
  - house stock state
  - item broken/unidentified state
  - portrait state
  - event mutations
  - bank gold
  - buff state
- This raises the priority of save/load relative to UI polish.

### OE Findings
- OE serializes full savegame state and has quick save/load plus UI slot selection.

### Implementation Notes
1. Define persistent save schema:
   - party
   - maps/world state
   - containers/chests
   - houses stock state
   - artifact found state
   - EVT mutable state
   - quest bits / autonotes
2. Add save directory and slot metadata.
3. Add load/save UI later under point 23.

### Good To Know
- Do this before too many more persistent systems land.

## 14. Buff Skull / Body Inspect Windows

### Current OpenYAMM
- Buff icons render.
- No inspect overlay on skull/body icons yet.

### OE Findings
- OE exposes buff information in UI, but this exact inspect-window behavior is an OpenYAMM extension.

### Implementation Notes
1. Add RMB/LMB inspect on skull/body icons.
2. Use new YAML popup.
3. Show active buffs and durations.

## 15. RMB Character Detail Inspect Window

### Current OpenYAMM
- Character screen exists.
- No gameplay RMB compact character detail popup yet.

### Implementation Notes
1. Add new YAML popup.
2. Show:
   - current conditions
   - character-targeted buffs
   - maybe HP/SP/resist summary

## 16. Map Transition Logic By Boat / Stables

### Current OpenYAMM
- Stables and boats are recognized house types.
- No real transport backend yet.

### OE Findings
- OE uses transport route/schedule tables:
  - destination
  - weekdays
  - travel time
  - qbit gates
  - arrival location / yaw
- Travel cost is separate from route schedule.

### Data
- If MM8 does not already provide explicit schedule rows, add supplemental table:
  - `TRANSPORT_SCHEDULES.txt`

### Implementation Notes
1. Parse or author explicit schedule data.
2. Add current-day filtering.
3. Add qbit gating.
4. Perform map transition and time advance.

## 17. Shop Open / Close Hours

### Current OpenYAMM
- `HouseEntry` already stores `openHour` and `closeHour`.
- There is already open-time gating logic in `HouseInteraction.cpp`.

### Remaining Delta
- Audit every service-door interaction path for parity.
- Ensure outside-hours interaction is rejected before entering house mode.
- Make house-specific closed texts/sounds consistent.

## 18. Per-Map Background Music

### Current OpenYAMM
- `MapStatsEntry` already loads `redbookTrack`.
- No full background music playback system is clearly wired yet.

### OE Findings
- OE map stats already drive music track selection.

### Implementation Notes
1. Use `MapStats.redbookTrack` first before adding new table.
2. Add per-map music start/stop/fade in game state transitions.

## 19. Sky Rendering / Per-Map Sky

### Current OpenYAMM
- No full sky parity yet.
- `MapStatsEntry` already has `environmentName`.

### OE Findings
- OE uses environment/map data to derive sky and atmosphere.

### Implementation Notes
1. Investigate if `environmentName` is enough to resolve sky art.
2. Add supplemental table only if needed.
3. Render sky dome/quad before world.

## 20. Water Edge Rendering

### Current OpenYAMM
- User reports water edges render as flat blue.

### Implementation Notes
1. Audit terrain material assignment at water boundaries.
2. Ensure edges sample water texture/material, not debug fill.

## 21. Water And Sky Motion

### Current OpenYAMM
- Static look.

### OE Findings
- OE animates sky and water by texture motion / frame drift.

### Implementation Notes
1. Add slow UV shift for water.
2. Add gentle sky UV drift independent of camera yaw.

## 22. Time-Of-Day Lighting / Vision / Sky Brightness

### Current OpenYAMM
- Likely partial at best.

### OE Findings
- OE darkens outdoor lighting and visibility by time of day.

### Implementation Notes
1. Add time-of-day brightness curve.
2. Modulate:
   - sky
   - fog distance
   - world ambient light
3. Keep it simple and maintainable.

## 23. Main Menu / New Game / In-Game Menu / Save-Load UI

### Current OpenYAMM
- No complete menu flow yet.

### Implementation Notes
1. Main menu YAML:
   - new game
   - load game
2. Character creation YAML:
   - new-game party seed path
3. In-game pause/menu YAML:
   - save
   - load
   - exit
4. Load/save slot selector UI.

### Dependencies
- Depends on point 13 save/load backend.

## 24. Party Wipe / Death Video / Respawn

### Current OpenYAMM
- No full game-over video state yet.

### OE Findings
- OE has a dedicated game-over flow and video/window state.

### Implementation Notes
1. Detect all-party-dead condition.
2. Open full-screen OGV playback state.
3. Exit on video finish or `Esc`.
4. After exit:
   - restore HP/SP
   - clear bad conditions
   - set gold to `0`
   - teleport to DWI starting position

## Cross-Cutting Missing Foundations

These should be watched during every implementation slice:
- persistence:
  - do not add new gameplay state without adding save/load representation plan
- data-driven first:
  - prefer TSV/TXT supplemental tables over C++ literals when the mapping belongs to game content
- tests:
  - every system slice should add headless regression coverage where possible
- no OE code copying:
  - only behavior reference and formulas

## Suggested Execution Slices

### Slice A
- point 3
- point 4
- point 5 foundation

### Slice B
- point 5
- point 6
- point 16

### Slice C
- point 17 audit
- point 13 foundation

### Slice D
- point 23 basic menu/load/save shell
- point 24

### Slice E
- point 10
- point 11
- point 14
- point 15
- point 12 audit/fix

### Slice F
- point 18
- point 19
- point 20
- point 21
- point 22

### Slice G
- point 9
- point 7
- remaining MM8-specific systems

## Immediate Next Best Task

Best next implementation task:
- point 3, enchant application

Why:
- the item-state foundation is already landed
- it unlocks meaningful loot/shop progression
- it unblocks artifacts/relics and enchant-aware inspect
- it is the missing layer before point 4 can be finished cleanly
