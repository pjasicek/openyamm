# MM6 MMMerge Delta Inventory

This replaces the stale MM6 Lua runtime inventory. It tracks MM6-specific MMMerge deltas that are not safely owned by
the generated MM6 EVT/scene exports.

## Ownership Rules

- Do not edit generated map scripts such as `assets_dev/worlds/mm6/events/maps/6d07.lua`.
- Put event/script parity fixes in supplemental Lua overlays named `assets_dev/worlds/mm6/events/maps/*_mmmerge.lua`.
- Do not edit generated scene files such as `assets_dev/worlds/mm6/maps/6d08.scene.yml`.
- Put static map-state or geometry/face fixes in supplemental scene overlays named
  `assets_dev/worlds/mm6/maps/*_1.scene.yml` or the next sorted overlay suffix.
- If a fix needs shared engine support, implement the narrow runtime API first, then call it from the overlay.
- Keep generated files reproducible from source assets. Any hand-authored MMerge parity belongs in overlay files.

## Sources Audited

- `reference/mmmerge/Scripts/Maps/*.lua`
- `reference/mmerge_data_forus/Scripts/Maps/*.lua`
- `assets_dev/worlds/mm6/events/maps/*`
- `assets_dev/worlds/mm6/maps/*`
- `assets_dev/worlds/mm6/_legacy/map_delta/*`

The binary MM6 map delta payload is present: every `.ddm`/`.dlv` from
`reference/mmerge_data_forus/Data/mm6.games.lod` exists under `assets_dev/worlds/mm6/_legacy/map_delta`.

## Active Overlay Coverage

These MM6 supplemental Lua overlays already exist.

| Map | Overlay | Current coverage |
| --- | --- | --- |
| `6d02` | `6d02_mmmerge.lua` | Angela Dowson rescue follower state. |
| `6d03` | `6d03_mmmerge.lua` | Sharry Carnegie rescue follower state. |
| `6t3` | `6t3_mmmerge.lua` | Sherell Ivanoveh rescue follower state. |
| `6t8` | `6t8_mmmerge.lua` | Emmanuel rescue follower state. |
| `6t7` | `6t7_mmmerge.lua` | Superior Temple of Baa door 1 current-player Perception/damage behavior. |
| `6d07` | `6d07_mmmerge.lua` | Silver Helm Outpost Gharik key/chest event 16 branch. |
| `6d08` | `6d08_mmmerge.lua` | Shadow Guild password doors 61-64 alternate answers. |
| `6d13` | `6d13_mmmerge.lua` | Temple of the Moon evil altar Cleric/Druid reward and texture changes. |
| `6t6` | `6t6_mmmerge.lua` | Supreme Temple of Baa memory crystal pickup suppresses generated SetMessage-to-dialog behavior. |
| `sewer` | `sewer_mmmerge.lua` | Prince of Thieves follower state. |
| `sci-fi` | `sci-fi_mmmerge.lua` | Control Center event 61 teaches Blaster skill to party members missing it. |
| `cd1` | `cd1_mmmerge.lua` | Castle Alamos event 69 answer-specific teleport/status behavior. |
| `cd2` | `cd2_mmmerge.lua` | Castle Darkmoor sarcophagus prompt, reward, map var, and reputation behavior. |
| `cd3` | `cd3_mmmerge.lua` | Castle Kriegspire Guardian and Curator prompt/payment behavior. |
| `outb1` | `outb1_mmmerge.lua` | King's Highway transport entry; Loretta handling is shared house runtime. |
| `outb2` | `outb2_mmmerge.lua` | Blackshire town portal bit, guard hostility, local relations, Kilburn shield chest, dragon tower state. |
| `hive` | `hive_mmmerge.lua` | Reactor/queen ending flow, good/bad movies, reactor physical damage rule, post-reactor summons, leave-map ending, exit behavior. Death-movie suppression is a no-op because OpenYAMM has no separate death-movie runtime path. |
| `outb3` | `outb3_mmmerge.lua` | Dragonsand Dimension Door event 105 and Shrine of the Gods per-character/refill state. |
| `outc1` | `outc1_mmmerge.lua` | Frozen Highlands town portal bit, guards, winter/weather, dragon tower state. |
| `outc2` | `outc2_mmmerge.lua` | Free Haven town portal bit, Silvertongue, Stone Temple, inn redirect, dragon tower state. |
| `outc3` | `outc3_mmmerge.lua` | Darkmoor transport entry; Loretta handling is shared house runtime. |
| `outd1` | `outd1_mmmerge.lua` | Silver Cove town portal bit, local relations, dragon tower state. |
| `outd3` | `outd3_mmmerge.lua` | Castle Ironfist transport, Archibald library, throne/Nicolai, bandit prompts. |
| `oute2` | `oute2_mmmerge.lua` | Mist town portal bit, local relations, dragon tower state. |
| `oute3` | `oute3_mmmerge.lua` | New Sorpigal town portal bit, Dimension Door, volcano, dragon tower state. |
| `pyramid` | `pyramid_mmmerge.lua` | VARN code entry variables, Captain code gate, book pickup variables, and control-room entry gate. |

## Remaining Missing Or Incomplete MM6 Deltas

No active missing MM6 MMMerge delta remains from this inventory.

| Map | MMMerge delta | Status |
| --- | --- | --- |
| `oracle` | Reference script only contains commented-out light code. | No-op with source evidence; no runtime behavior to port. |

## Static Scene Delta Status

| Map | MMMerge/static behavior | Overlay status |
| --- | --- | --- |
| `6d08` | Face 373 polygon type changed to fix spike trap. | Done in `assets_dev/worlds/mm6/maps/6d08_1.scene.yml`. |
| `outa2` | Tile 0 footstep sound override. | Done in `assets_dev/worlds/mm6/maps/outa2_1.scene.yml`. |
| `outa3` | Tile 0 and tile 6 footstep sound overrides. | Done in `assets_dev/worlds/mm6/maps/outa3_1.scene.yml`. |
| `outb3` | Tile 6 footstep sound override found during Dragonsand audit. | Done in `assets_dev/worlds/mm6/maps/outb3_1.scene.yml`. |

Add any future static deltas to a sorted overlay file, not to the generated `*.scene.yml`.

## Runtime/API Gaps To Check Before Implementation

| Need | Existing support | Action |
| --- | --- | --- |
| Replace generated map events | `ReplaceMapEvent`, `AppendMapEvent`, `RegisterMapOnLoadEvent`. | Use from `*_mmmerge.lua`. |
| Multi-answer prompts | `AskQuestionWithAnswerSteps` exists. | Used by `6d08`, `cd1`, `cd2`, and `cd3` overlays. |
| Dimension Door from map script | `evt.OpenDimensionDoor()` exists. | Used by `outb3_mmmerge.lua` event 105. |
| Learn Blaster skill | Event value APIs support `BlasterSkill`. | Covered by scripted regression test for `sci-fi_mmmerge.lua`. |
| Hive monster death/damage hooks | Added `MonsterKilled` and `MonsterDamage` Lua hook support with damage override context. | Used by `hive_mmmerge.lua`; covered by scripted regression tests. |
| Tile footstep sounds | Outdoor scene overlays support `terrain.footstep_sound_overrides`. | Used by `outa2_1.scene.yml`, `outa3_1.scene.yml`, and `outb3_1.scene.yml`; covered by scene overlay regression tests. |

## Verification Targets

Implemented coverage:

- `tests/ScriptedMapRegressionTests.cpp`: `outb3`, `pyramid`, and `hive` overlay behavior, including the new monster
  damage/death hooks.
- `tests/GameplayRuleRegressionTests.cpp`: MM6 outdoor scene overlay footstep sound overrides for `outa2`, `outa3`,
  and `outb3`.

## Completion Criteria

This inventory is complete only when every row in "Missing Or Incomplete MM6 Deltas" is either implemented in an overlay,
explicitly covered by shared runtime/data with a test reference, or marked no-op with source evidence.
