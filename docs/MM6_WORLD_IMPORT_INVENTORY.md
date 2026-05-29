# MM6 World Import Inventory

This inventory tracks the first MM6 world-package import. MMerge is reference material only. The target is normal
OpenYAMM content under `assets_dev/worlds/mm6`, with MM8/OpenYAMM engine systems providing HUD, menus, character
creation, inventory, spells, and shared mechanics.

## Target Shape

```text
assets_dev/worlds/mm6/
  world.yml
  audio/
  data_tables/
  data_tables/english/
  events/maps/
  icons/
  maps/
  music/
  rendering/
  rendering/sprite_frames/monsters/
  sprites/
  textures/
  videos/
  _legacy/
  _legacy/bin_tables/
  _legacy/events/
  _legacy/map_delta/
  _legacy/tables/
  _legacy/tile_tables/
```

Runtime-facing files should eventually live in the normal folders. `_legacy` is import evidence and source material,
not a runtime dependency to grow around.

## Source Roots

Short source labels in this table:

- `games`: `reference/mmerge_data_forus/Data/mm6.games.lod`
- `text`: `reference/mmerge_data_forus/Data/mmmerge.T.lod`
- `events`: `reference/mmerge_data_forus/Data/mm6.T.lod`
- `tables`: `reference/mmerge_data_forus/Data/Tables`
- `files`: `reference/mmerge_data_forus/DataFiles`

| Source | First-pass target | Notes |
| --- | --- | --- |
| `games/*.odm` | `maps/` | Raw outdoor map geometry. |
| `games/*.blv` | `maps/` | Raw indoor map geometry. |
| `games/*.ddm` | `_legacy/map_delta/` | Source delta for outdoor scene export. |
| `games/*.dlv` | `_legacy/map_delta/` | Source delta for indoor scene export. |
| `events/*.EVT` | `_legacy/events/` | Source event bytecode for exporter. |
| `text/*.STR` | `_legacy/events/` | Source event strings for exporter. |
| `Data/mm6.D.lod/*.wav` | `audio/` | MM6 sound assets. Runtime use depends on `sounds.txt`. |
| `Data/mm6.bitmaps.lod/*` | `textures/` | Terrain, dungeon, sky, palette, and bitmap assets. |
| `Data/mm6.icons.lod/*` | `icons/` | MM6 icon/UI source assets. |
| `Data/mm6.sprites.lod/*` | `sprites/` | MM6 world sprite source assets. |
| `Data/mmmerge.sprites.lod/*` | `sprites/` | Merged/custom monster sprite source assets. |
| `files/*.bin` | `_legacy/bin_tables/` | Binary table inputs for canonical exporters. |
| `files/dtile*.bin` | `_legacy/tile_tables/` | Tile binary table inputs for terrain exporter. |
| `tables/*.txt` | `_legacy/tables/` | MMerge generated tables and base references. |
| `text/*.txt` | `_legacy/tables/` | Merged text/gameplay tables used as import sources. |

## Canonical MM6 Tables To Produce

These files should be produced under `data_tables/` or `data_tables/english/` in our existing formats:

| Target table | Source candidate | Import path |
| --- | --- | --- |
| `data_tables/map_stats.txt` | `mmmerge.T.lod/MapStats.txt` | Filter/split MM6 rows, preserve local map ids. |
| `data_tables/map_navigation.txt` | `tables/Outdoor travels.txt` | Convert travel rows to navigation format. |
| `data_tables/chest_data.txt` | `DataFiles/dchest.bin`, `Data/Tables/Chest.txt` | Export canonical UI grid columns. |
| `data_tables/decoration_data.txt` | `files/ddeclist.bin`, `tables/DecList.txt` | Export descriptor columns. |
| `data_tables/house_animations.txt` | MMerge house/movie tables | Derive after house table import. |
| `data_tables/house_data.txt` | `mmmerge.T.lod/2DEvents.txt`, house tables | Convert to current house schema. |
| `data_tables/mon_list.txt` | `files/dmonlist.bin`, `tables/MonList.txt` | Export monster list rows. |
| `data_tables/monster_data.txt` | `mmmerge.T.lod/MONSTERS.txt` | Filter/split MM6 monsters. |
| `data_tables/monster_descriptors.txt` | `DataFiles/dmonlist.bin` | Export canonical descriptor rows. |
| `data_tables/monster_relation_data.txt` | `mmmerge.T.lod/Hostile.txt` | Convert to current relation format. |
| `data_tables/monster_projectiles.txt` | Monster/spell references | Derive only if MM6 needs overrides. |
| `data_tables/monster_death_drops.txt` | MM6/MMerge monster data | Derive after monster table import. |
| `data_tables/npc.txt` | `mmmerge.T.lod/NPCData.txt` | Convert to current NPC schema. |
| `data_tables/npc_greet.txt` | `mmmerge.T.lod/NPCGreet.txt` | Convert or copy if schema matches. |
| `data_tables/npc_news.txt` | `mmmerge.T.lod/NPCNews.txt` | Convert or copy if schema matches. |
| `data_tables/npc_topic.txt` | `mmmerge.T.lod/NPCTopic.txt` | Convert or copy if schema matches. |
| `data_tables/npc_topic_text.txt` | `mmmerge.T.lod/NPCText.txt` | Convert or copy if schema matches. |
| `data_tables/roster.txt` | `mmmerge.T.lod/roster.txt` | Convert/filter MM6 roster entries. |
| `data_tables/sounds.txt` | `DataFiles/dsounds.bin`, `Data/Tables/Sounds.txt` | Integrate into the flat merged sound catalog. |
| `data_tables/terrain_tile_data*.txt` | `DataFiles/dtile*.bin`, `Data/Tables/Tile*.txt` | Export canonical tile data. |
| `data_tables/texture_frame_data.txt` | `files/dtft.bin`, `tables/TFT.txt` | Export texture frames. |
| `data_tables/town_portal_switch.txt` | `Data/Tables/TownPortalSwitch.txt` | Shared MMerge Town Portal source; active runtime table for MM6/MM7/MM8 continent-aware portal UI. |
| `data_tables/house_rules.txt`, `data_tables/transport_locations.txt` | Transport tables, travels | Active MMerge stable/boat route source. |
| `data_tables/english/autonote.txt` | `mmmerge.T.lod/Autonote.txt` | Filter/split MM6 rows. |
| `data_tables/english/awards.txt` | `mmmerge.T.lod/Awards.txt` | Filter/split MM6 rows. |
| `data_tables/english/history.txt` | `mmmerge.T.lod/history.txt` | Filter/split MM6 rows. |
| `data_tables/english/npc_group.txt` | `mmmerge.T.lod/NPCGroup.txt` | Convert or copy if schema matches. |
| `data_tables/english/place_mon.txt` | `mmmerge.T.lod/Placemon.txt` | Filter/split MM6 rows. |
| `data_tables/english/quest.txt` | MM6 quest text sources | Derive if current engine still needs singular file. |
| `data_tables/english/quests.txt` | `mmmerge.T.lod/Quests.txt` | Filter/split MM6 rows. |
| `data_tables/english/trans.txt` | `mmmerge.T.lod/Trans.txt` | World-specific transition text. |

## Exporter Checks

The first exporter pass should use New Sorpigal:

```text
oute3.odm
oute3.ddm
```

Required checks:

1. Run `tools/export_outdoor_scene_yml.py` on `oute3` and keep the generated `maps/oute3.scene.yml` only if it
   validates against the current loader.
2. Run `tools/export_indoor_scene_yml.py` on one simple MM6 indoor map, preferably `6d01`, and keep the generated
   `maps/6d01.scene.yml` only if it validates against the current loader.
3. Run table exporters after they accept explicit source and target paths. Current hardcoded MM8 paths must not be used
   for MM6 output.
4. Run `event_asset_export_main` with an MM6 config that points at flat `engine/data_tables/*` registries and
   `worlds/mm6/_legacy/events`.

## Current First-pass Status

Imported as-is:

- raw MM6 `*.odm` and `*.blv` map geometry into `maps/`;
- raw MM6 `*.ddm` and `*.dlv` map delta files into `_legacy/map_delta/`;
- MM6 EVT programs and matching STR files into `_legacy/events/`;
- MM6 WAV files into `audio/`;
- MM6 bitmap, icon, sprite, and merged sprite BMP/ACT files into `textures/`, `icons/`, and `sprites/`;
- MMerge generated text tables and merged text/gameplay tables into `_legacy/tables/`;
- generated binary table files into `_legacy/bin_tables/` and tile binaries into `_legacy/tile_tables/`.

Generated with current exporters:

- `maps/oute3.scene.yml` from `oute3.odm` and `oute3.ddm`;
- `maps/6d01.scene.yml` from `6d01.blv` and `6d01.dlv`;
- `maps/*.scene.yml` for all 15 MM6 outdoor maps and all 51 MM6 indoor maps from the imported DDM/DLV map delta
  sources;
- `data_tables/decoration_data.txt` from `ddeclist.bin` plus `DecList.txt` labels;
- `data_tables/map_stats.txt` filtered to MM6 map files while preserving MMerge map ids;
- `data_tables/map_navigation.txt` from `Outdoor travels.txt`;
- `data_tables/mon_list.txt` from `MonList.txt`;
- `data_tables/object_list.txt` from `ObjList.txt` plus `dobjlist.bin`, so MM6 event object payload ids resolve against
  MM6 objects instead of the engine/MM8 object table;
- `data_tables/sounds.txt` from the lowercase MMerge `sounds.txt`, integrated into the flat merged sound catalog;
- source-backed journal, NPC, roster, town portal, and transition tables from `_legacy/tables`;
- `data_tables/house_animations.txt` from `house_data.txt`, `_legacy/tables/House Movies.txt`, and NPC house ids;
- direct MMerge transport routes from `_legacy/tables/House rules.txt` and `Transport Locations.txt`;
- `data_tables/texture_frame_data.txt` from `dtft.bin`;
- `data_tables/terrain_tile_data*.txt` from `dtile*.bin`;
- `rendering/sprite_frame_data_common.yml` and monster family YAML from `dsft.bin`;
- eight MM7 terrain bitmap dependencies referenced by the merged MM6 tile tables:
  `7drsrnw2`, `7drsrne2`, `7drsrne1`, `7drsrnw1`, `7drsrcros3`, `7drsrcros4`, `7drsrcros2`, and
  `7drsrcros1`;
- `events/maps/*.lua` for all 66 MM6 maps using `tools/lua_event_export.mm6.ini`.

Current boot checks:

- `./build/game/openyamm --world mm6 --map oute3.odm --headless-profile-map-load-full oute3.odm` completes and loads
  New Sorpigal;
- `./build/game/openyamm --world mm6 --map 6d01.blv --headless-profile-map-load-full 6d01.blv` completes and loads
  Goblinwatch;
- New Sorpigal and Goblinwatch actor diagnostics report zero missing actor textures after the sprite texture-name
  resolver fix for MM6 directional base names.
- Full MM6 map-load sweep across 66 maps completes with zero failures and zero missing terrain/actor diagnostics.

Known gaps after first boot:

- generated house animation tables and direct MMerge transport route loading now remove the missing-table diagnostics, but
  house videos, house sound banks, and transport route behavior still need in-game validation;
- New Sorpigal's known missing terrain dependencies are imported, and the first full map-load sweep reports no missing
  terrain diagnostics;
- the merged QBit journal registry is now global engine data and validated for malformed/duplicate QBit ids, but NPC,
  roster, autonote, award, history, and related story tables are still MMerge merged tables promoted as a bootstrapping
  step and need continent filtering/splitting;
- MM6 decoration sounds include ids above signed 16-bit range in source text, while the current decoration table stores
  sound ids as signed 16-bit values;
- exported event scripts need targeted gameplay validation beyond map-load success.

## First-pass Rules

- Do not copy MMerge Lua hooks into runtime content.
- Do not reproduce MMerge's memory-hook runtime architecture.
- Keep MM6 as a world package mounted under the existing engine.
- Keep MMerge tables in `_legacy/tables` until converted into OpenYAMM formats.
- Prefer a small New Sorpigal boot slice over a mass runtime import.

## Remaining Work Inventory

This is the actionable backlog from the current bootable first pass. A task is done only when its target files are
generated repeatably from the listed sources and the validation check passes.

### Event Scripts

- MM6 event export config:
  target `tools/lua_event_export.mm6.ini` or equivalent. Source is `tools/lua_event_export.example.ini`.
  Generated first-pass config points at MM6 world paths via the active `--world mm6` asset mount.
- Map scripts:
  target `assets_dev/worlds/mm6/events/maps/*.lua`. Sources are `_legacy/events/*.EVT` and `_legacy/events/*.STR`.
  Generated for all 66 MM6 `map_stats.txt` rows.
- Global script:
  target `assets_dev/worlds/mm6/events/Global.lua` if MM6 global events exist.
  Source is `_legacy/events/Global.*` if present, otherwise none.
  No `Global.lua` was emitted in the first full export; keep this explicit if a global MM6 source appears later.
- Event dumps:
  target a transient or checked-in diagnostic location, not runtime. Source is exporter EVT/IR dumps.
  Done when unsupported opcodes are reviewed and noisy dumps are kept out of runtime packages.
- Script runtime validation:
  no extra target file. Sources are exported scripts plus `oute3` and `6d01`.
  Headless map-load passes for all 66 maps with scripts present; targeted interactions still need validation.

Notes:

- `_legacy/events/` currently contains raw EVT/STR import material, including some merged non-MM6 STR files.
  The exporter should export only maps present in `data_tables/map_stats.txt`.
- Do not import MMerge Lua hook scripts; use them only as behavior reference when a converted EVT needs a missing engine
  operation.

### House And Transport Tables

- House animations:
  target `data_tables/house_animations.txt`.
  Sources are `_legacy/tables/House Movies.txt`, `house_data.txt`, and NPC rows. MMerge loads this via
  `Scripts/General/DataTables.lua` and `DataTables.HouseMovies`, with `RemoveHouseMoviesLimit.lua` extending the
  original fixed array.
  Table generation is done; full validation still needs house video, room sound, and resident NPC checks in game.
- Transport schedules:
  active targets `data_tables/house_rules.txt` and `data_tables/transport_locations.txt`.
  Sources are `_legacy/tables/House rules.txt` and `_legacy/tables/Transport Locations.txt`.
  MMerge disables the original `Transport Index.txt` path when `House rules.txt` is present; the final route slots come
  from the `Stables` and `Boats` sections in `House rules.txt`.
  Direct runtime consumption is done; full validation still needs route availability, price, destination, heading, and qbit
  checks.
- House data cleanup:
  target `data_tables/house_data.txt`. Sources are `_legacy/tables/2DEvents.txt` and house rule tables.
  Done when skill offers, hours, services, prices, and enter text match MM6/MMerge behavior.
- House video/audio assets:
  targets `videos/Houses/*`, `audio/*`, and the flat `engine/data_tables/sounds.txt` registry.
  Sources are MM6/MMerge media and sound tables.
  Done when opening a house resolves video, room sound, and enter sound against the active world's audio assets.

Notes:

- `reference/mmmerge` and `reference/mmerge_datapatch` contain identical final `House Movies.txt`,
  `Transport Index.txt`, and `Transport Locations.txt` table files.
- The active MMerge transport implementation uses `House rules.txt` for route slots and `Transport Locations.txt` for
  actual destination data; `Transport Index.txt` is retained as reference material but is not authoritative there.
- The current `house_data.txt` is source-backed but not fully normalized to OpenYAMM's richer MM8-style house schema.

### Visual Asset Resolution

- Missing New Sorpigal terrain textures:
  target `textures/` and/or `terrain_tile_data*.txt`. Sources are MM6 bitmap LODs, `Tile*.txt`, and `dtile*.bin`.
  New Sorpigal is resolved by importing eight MM7 bitmap dependencies referenced by the MMerge tile tables; wider map
  validation still needs a full terrain sweep.
- Actor sprite coverage:
  targets `sprites/`, `rendering/sprite_frames/monsters/*.yml`, and `sprite_frame_data_common.yml`.
  Sources are MM6/MMerge sprites, `dsft.bin`, `SFT.txt`, and monster tables.
  The boot-slice actor diagnostics are resolved by fixing directional base texture resolution, for example `pfemsta`
  now resolves to `pfemsta0` instead of a nonexistent unsuffixed bitmap.
- Monster descriptor correctness:
  targets `monster_descriptors.txt`, `mon_list.txt`, and monster frame YAML.
  Sources are `dmonlist.bin`, `MonList.txt`, and `MONSTERS.txt`.
  Done when scene YAML monster ids resolve to names, stats, frames, and sounds.
- Decoration sound ids:
  target `decoration_data.txt` and/or C++ field type.
  Sources are `ddeclist.bin`, `DecList.txt`, and `sounds.txt`.
  Done when large MM6 decoration sound ids are not truncated or dropped.
- Icon/UI asset references:
  targets `icons/` and `data_tables/*`. Sources are MM6 icon LODs and engine UI tables.
  Done when character, inventory, item, and spell icons resolve without accidental MM8-only dependency.

Current known probe output:

- `oute3` terrain atlas reports zero missing bitmaps after importing the eight referenced MM7 terrain bitmaps.
- `oute3` actor diagnostics report `textured=99 missing=0`.
- `6d01` actor diagnostics report `textured=51 missing=0`.

### Data Ownership Cleanup

- Journal/QBit ownership:
  target `assets_dev/engine/data_tables/english/quests.txt` for the merged global QBit journal registry.
  Sources are MMerge merged quest rows and MM6/MM7/MM8/custom world declarations.
  Runtime and exporter validation now reject malformed and duplicate QBit ids. Custom worlds and mods should reserve
  explicit ranges starting at `10000+`; exporter validation warns when custom-range QBits referenced by EVT scripts do
  not have visible quest rows. No world package should own a private `english/quests.txt` table.
- World story table split:
  targets `english/autonote.txt`, `english/awards.txt`, and `english/history.txt`.
  Sources are MMerge merged tables and MM6 map/event references.
  Done when MM6 world has only MM6-owned story rows plus explicit shared rows.
- NPC split:
  targets `npc*.txt`, `english/npc_group.txt`, and `roster.txt`.
  Sources are MMerge merged NPC tables, MM6 maps/events, and houses.
  Done when MM6 maps and houses resolve NPCs without Jadame/Antagarich-only bootstrap rows.
- Monster split:
  targets `monster_data.txt`, `monster_relation_data.txt`, and `monster_death_drops.txt`.
  Sources are MMerge monster tables and MM6 map actor ids.
  Done when MM6 keeps all referenced monsters while avoiding unrelated world-only data.
- Placed monster names:
  target `english/place_mon.txt`. Sources are `Placemon.txt` and scene YAML placed monsters.
  Done when unique actor names resolve for MM6 maps only.
- Sounds:
  targets the flat `engine/data_tables/sounds.txt` catalog and world-local `audio/` assets. Sources are lowercase
  MMerge `sounds.txt`, MM6 `*.wav`, and `dsounds.bin`.
  Done when duplicate ids are resolved in the merged catalog and active-world audio assets are found by name.

Notes:

- Several current runtime tables are promoted from merged MMerge data to get the first boot. They are acceptable
  bootstrap data, not final ownership.
- Filtering should be reference-driven: retain rows referenced by MM6 maps, events, houses, monsters, and travel tables.
  Do not delete rows merely because their text looks non-MM6 without proving they are unreferenced.

### Map And Scene Export Coverage

- Outdoor scene YAML for all MM6 ODM maps:
  target `maps/*.scene.yml`. Sources are `maps/*.odm` and `_legacy/map_delta/*.ddm`.
  Done for all 15 outdoor maps; full sweep loads them headlessly without missing terrain/actor diagnostics.
- Indoor scene YAML for all MM6 BLV maps:
  target `maps/*.scene.yml`. Sources are `maps/*.blv` and `_legacy/map_delta/*.dlv`.
  Done for all 51 indoor maps; full sweep loads them headlessly without missing actor diagnostics.
- Map start/transition coverage:
  targets `world.yml`, `map_stats.txt`, `map_navigation.txt`, and `trans.txt`.
  Sources are `MapStats.txt`, `Outdoor travels.txt`, `Trans.txt`, and events.
  Done when new game and map transitions select the intended MM6 maps and coordinates.
- Chest data:
  target `chest_data.txt` and scene chest YAML. Sources are `dchest.bin`, `Chest.txt`, and DLV/DDM chests.
  Done when chests open with correct dimensions, traps, and item placement.

Current status:

- Scene YAML was generated for all 66 MM6 maps.
- Full headless load sweep result: `maps=66 failures=0 warnings=0`.

### Engine Gaps Exposed By MM6

- Initial map should come from world manifest:
  location `GameDataLoader` and `GameApplication`. MM6 map ids do not include MM8 id `1`.
  Done when `--world mm6` loads the `world.yml` start map.
- Optional table diagnostics:
  location `GameDataLoader::loadHouseTable`. Missing optional tables are expected during partial imports.
  First-pass resolved by generating `house_animations.txt` and loading MMerge transport routes directly for MM6.
- Event opcodes not supported by converter/runtime:
  location event exporter and `EventRuntime`. MM6 EVT may use operations not covered by the MM8 path.
  First-pass export reports no unsupported opcodes for all 66 MM6 map scripts. Large readable event expansions now fall
  back to compact step-machine Lua when they would exceed Lua parser limits, and failed readable prompt attempts no
  longer leak partial Lua into fallback output.
- Active-world audio asset resolution:
  location gameplay/audio call sites. House, monster, and world-local audio files should resolve for the active world
  while using the flat merged sound catalog.
  Done when MM6 monster/house sounds play without id collisions or missing asset paths.

### Validation Gates

Before considering the MM6 world import complete enough to start gameplay work, run these checks:

```text
python3 -m py_compile tools/export_mm6_world_tables.py
python3 tools/export_mm6_world_tables.py --world-dir assets_dev/worlds/mm6
cmake --build build --target openyamm_event_asset_export -j25
./build/tools/openyamm_event_asset_export --world mm6 --lua-export-config tools/lua_event_export.mm6.ini
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests
./build/game/openyamm --world mm6 --map oute3.odm --headless-profile-map-load-full oute3.odm
./build/game/openyamm --world mm6 --map 6d01.blv --headless-profile-map-load-full 6d01.blv
```

Add a broader map-load sweep once scene YAML and scripts are exported for more than the boot slice.
