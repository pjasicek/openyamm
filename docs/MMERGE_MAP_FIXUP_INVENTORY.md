# MMMerge Map Fixup Inventory

Source scanned: `reference/mmerge_data_forus/Scripts/Maps/*.lua`.

This inventory tracks MMMerge per-map Lua overlays that are not part of the original BLV/ODM EVT export. These are
reference behavior only; do not copy the scripts into OpenYAMM verbatim. Translate the behavior into map data,
generated Lua overlays, or runtime systems as appropriate.

## Summary

- MMMerge has 73 map overlay scripts in `Scripts/Maps`.
- All original MM6/MM7/MM8 overlay names already have same-named generated OpenYAMM map scripts under `assets_dev`;
  the generated files are not equivalent to the MMMerge overlays.
- Missing scripts are MMMerge custom CrossContinents maps only: `BrAlvar.lua`, `BrBase.lua`, `Breach.lua`.
- `7d06.lua` is the only pure `events.LoadMap` mechanism initial-state correction found. It is already baked into the
  MM7 Temple of the Moon scene YML and the indoor scene exporter.
- Supplemental map Lua overlays are supported by the common event support layer via `RemoveMapEvent`,
  `ReplaceMapEvent`, `RegisterMapOnLoadEvent`, and related helpers.
- Supplemental scene overlays are supported as sorted `basename_*.scene.yml` files applied after the generated
  `basename.scene.yml` DLV/DDM export.
- MM6 MMMerge map/script/scene delta ownership is tracked in `MM6_MMERGE_DELTA_INVENTORY.md`.
- MM8/Jadame-specific MMMerge map/global fixups are tracked in `MM8_MMERGE_FIXUP_INVENTORY.md`.
- Most remaining overlays are runtime quest/event fixes. They should be implemented as OpenYAMM overlay Lua or shared
  runtime systems, not as static BLV/ODM data patches.

## Static Or Data Fixup Candidates

These are the closest matches to the `7d06` case.

| Map | World | MMMerge behavior | OpenYAMM target | Status |
| --- | --- | --- | --- | --- |
| `7d06` | MM7 | On map load, doors 5-8 are forced closed and doors 9-10 forced open. | `*.scene.yml` `mechanisms.initial_state`, plus exporter rule. | Done. |
| `6d08` | MM6 | Facet 373 polygon type is changed to fix a spike trap. | `6d08_1.scene.yml` `face_attribute_overrides.facet_type`. | Done. |
| `7d23` | MM7 | Monster group 56 is made non-hostile and invisible at script load. | Supplemental `7d23_mmmerge.lua` map-load event. | Done. |
| `7d05` | MM7 | NPC 639 event routing is changed; all arena doors are silent/no-sound; saving and Lloyd's Beacon are blocked in arena. | NPC table/event metadata plus `7d05_1.scene.yml` `runtime_restrictions`; door no-sound is already represented in generated scene attributes. | Done. |
| `out06` | MM8 | A local tile-bin override swaps dirt terrain texture to `gdtyl`, with matching tile sound. | Terrain descriptor remap plus `out06_1.scene.yml` `terrain.footstep_sound_overrides`. | Done. |

## Original-World Runtime Overlays In OpenYAMM

These are local supplemental Lua overlays that now load on top of the generated original-world map scripts.

| Map | World | Implemented overlay behavior | Remaining MMMerge behavior |
| --- | --- | --- | --- |
| `outb1` | MM6 | Ports Loretta price check for King's Highway. | Other MMMerge behavior on this map still needs inventory if needed. |
| `outb2` | MM6 | Sets Blackshire Town Portal QBit 310 on load, clears group-39 guard hostility, applies local monster relations, and ports Loretta plus dragon tower timer/disable/texture state. | Kilburn shield chest refill. |
| `outc1` | MM6 | Sets White Cap Town Portal QBit 315 on load, clears group-39 guard hostility, ports winter/weather state, and ports Loretta plus dragon tower timer/disable/texture state. | No known remaining MM6 outdoor systemic overlay in the current first-pass slice. |
| `outc2` | MM6 | Sets Free Haven Town Portal QBit 311 on load and ports Loretta, Silvertongue treason, Stone Temple repair, Adventurer's Inn override, plus dragon tower timer/disable/texture state. | No known remaining MM6 outdoor systemic overlay in the current first-pass slice. |
| `outc3` | MM6 | Ports Loretta price check for Darkmoor Travel. | Other MMMerge behavior on this map still needs inventory if needed. |
| `outd1` | MM6 | Sets Silver Cove Town Portal QBit 314 on load, applies local monster relations, and ports Loretta plus dragon tower timer/disable/texture state. | No known remaining MM6 outdoor systemic overlay in the current first-pass slice. |
| `outd3` | MM6 | Ports Loretta price check for Royal Lines. | Other MMMerge behavior on this map still needs inventory if needed. |
| `oute2` | MM6 | Sets Mist Town Portal QBit 312 on load, applies local monster relations, and ports the dragon tower timer/disable/texture state. | No known remaining MM6 outdoor systemic overlay in the current first-pass slice. |
| `oute3` | MM6 | Sets New Sorpigal Town Portal QBit 313 on load, applies local monster relations, and ports Loretta, Dimension Door, volcano spell sequence, plus dragon tower timer/disable/texture state. | No known remaining MM6 outdoor systemic overlay in the current first-pass slice. |

## Runtime Overlay Families

These should remain runtime logic because they depend on QBits, timers, party inventory, NPC followers, current time,
monster state, or spell hooks.

| Family | Maps | Notes |
| --- | --- | --- |
| Event replacements via `Game.MapEvtLines:RemoveEvent` and `evt.map`/`evt.Map` | `6d02`, `6d03`, `6d07`, `6d08`, `6d13`, `6t7`, `7d23`, `7d24`, `7d27`, `7d29`, `7d30`, `7d36`, `7d37`, `7nwc`, `7out02`, `7out04`, `cd1`, `cd2`, `cd3`, `d03`, `d06`, `d07`, `d19`, `d34`, `d42`, `hive`, `out02`, `out07`, `out11`, `out12`, `out13`, `outb1`, `outb2`, `outb3`, `outc1`, `outc2`, `outc3`, `outd1`, `outd3`, `oute2`, `oute3`, `pbp`, `pyramid` | Needs an OpenYAMM-supported overlay model for replacing generated EVT handlers without stale duplicate handlers. |
| Town Portal / Dimension Door hooks | `out01`, `out02`, `out07`, `out09`, `outb3`, `oute3`, `7out04`, `d42`, `BrAlvar`, `BrBase`, `Breach` | Some are now covered by our continent-aware Town Portal table/UI. `oute3` Dimension Door is ported through a runtime overlay request; remaining entries are non-MM6 or later-sweep hooks. |
| MM6 outdoor systemic fixes | `outb1`, `outb2`, `outb3`, `outc1`, `outc2`, `outc3`, `outd1`, `outd3`, `oute2`, `oute3` | Dragon tower state, Loretta price checks, local hostile relation overrides, outc1 weather, outc2 local quest fixes, and oute3 Dimension Door/volcano are ported. Remaining work is Kilburn shield and weather/tile sounds. |
| MM7 Harmondale/CrossContinents/faction fixes | `7d24`, `7d29`, `7d30`, `7out02`, `7out03`, `7out04`, `7out05`, `7out15`, `d03`, `out02`, `hive` | Contains global MMerge progression and CrossContinents state. Do this after base MM6/MM7/MM8 map correctness. |
| MM8 quest/event corrections | `d06`, `d07`, `d19`, `d24`, `d34`, `d38`, `d39`, `d42`, `out01`, `out02`, `out05`, `out07`, `out09`, `out11`, `out12`, `out13`, `out14`, `pbp`, `pyramid` | Mostly original MM8 bug fixes and MMerge continuity changes. |
| Custom CrossContinents maps | `BrAlvar`, `BrBase`, `Breach` | Not original MM6/MM7/MM8 maps. Import later as custom content, not as base map fixups. |

## Explicit LoadMap / AfterLoadMap Cases

| Map | Hook | Behavior class |
| --- | --- | --- |
| `7d06` | `events.LoadMap` | Static mechanism state fixup. Done. |
| `7d29` | `events.LoadMap`, `events.LeaveMap` | Harmondale invasion and CrossContinents progression. Runtime quest overlay. |
| `7d30` | `events.LoadMap` | CrossContinents completion marker. Runtime quest overlay. |
| `7out02` | `events.LoadMap` | Harmondale rebuild/judge messenger/invasion timing. Runtime quest overlay. |
| `7out04` | `events.LoadMap` | Artifact messenger and Tularean Forest battle state. Runtime quest overlay. |
| `7out15` | `events.LoadMap`, `events.LeaveMap`, `events.Tick` | Character face override and map-action restrictions. Runtime overlay. |
| `d03` | `events.LoadMap` | CrossContinents completion marker. Runtime quest overlay. |
| `d24` | `events.LoadMap` | Hides group-0 tritons after QBit 23. Runtime conditional monster-state overlay. |
| `out01` | `events.LoadMap` | Sets MM8 Town Portal unlock bit. Covered conceptually by Town Portal table/start state; verify runtime. |
| `out02` | `events.LoadMap` | CrossContinents marker plus crystal access rewrite. Runtime quest overlay. |
| `outc1` | `events.LoadMap` | MM6 Town Portal unlock, winter/weather state, dragon tower/loretta/guard fixes. Runtime overlay. Done. |

## Recommended Sweep Order

1. Port the original-world MM6/MM7/MM8 runtime overlays in small groups, starting with non-CrossContinents bug fixes.
2. Implement or map shared helper APIs used by many overlays. Local hostility overrides, dragon tower, Loretta,
   outc1/outc2 medium fixes, and the `oute3` Dimension Door hook are done; next is Kilburn shield.
3. Defer `BrAlvar`, `BrBase`, and `Breach` until custom CrossContinents content is mounted as content packages.
