# Content provenance

Status: investigation (2026-10-22). Part of the [vanilla mode investigation](README.md). Counts come from byte
comparisons against MMerge's extracted data and the original MM8 LODs, and from diffs of GrayFace's decompiled
event scripts.

## Maps

All shipped `.odm`/`.blv` maps and `.dlv`/`.ddm` deltas come from MMerge's extracted LODs in
`reference/mmerge_data_forus/Data/{mm6,mm7,mm8}.games.lod/`, not from the original games.

| World | Maps identical to MMerge | Deltas (`_legacy/map_delta`) |
|---|---|---|
| mm6 | 59 of 66; 7 edited by us in commit `856f27d96` (HD work: `outc2`, `outd1`-`outd3`, `oute1`-`oute3`) | 66 of 66 identical to MMerge |
| mm7 | 76 of 76 | 76 of 76 identical to MMerge |
| mm8 | 61 of 61 | 61 of 61 are **vanilla MM8**; 16 differ from MMerge |

- **MM8 maps against the original game.** Compared with GOG MM8 plus GrayFace's patch, 47 are identical and MMerge
  edited 14: `d07`, `d12`, `d16`, `d17`, `d19`, `d41`, `elemf`, `out01`, `out02`, `out04`, `out05`, `out06`, `out07`,
  `out13`.
- **Latent mismatch.** The MM8 deltas were never updated after the switch to MMerge, so those 14 MMerge maps load
  against vanilla deltas (`game/maps/MapAssetLoader.cpp:4977`).
- **No map import tool or receipt exists.** The maps came in bulk with commit `a601e26a6` (2026-05-02). The tools
  `remap_mm8_outdoor_tile_lookups_to_mmerge.py` and `remap_mm8_scene_decorations_to_mmerge.py` converted earlier
  vanilla MM8 scenes to MMerge numbering.

### MMerge map names

MMerge renamed clashing maps; everything else keeps its original name.

| Game | Renamed | Unchanged |
|---|---|---|
| MM6 | `D01`-`D20` to `6d01`-`6d20`; `T1`-`T8` to `6t1`-`6t8` | `outa1`-`oute3`, `zddb*`, `zdtl*`, `zdwj*`, `znwc`, `cd1`-`cd3`, `hive`, `oracle`, `pyramid`, `sci-fi`, `sewer`, `zarena` |
| MM7 | `D05`-`D37` to `7d05`-`7d37`; `OUT01`-`06`, `13`, `15` to `7out*`; `NWC` to `7nwc` | `d01`-`d04`, `out09`-`out12`, `out14`, `mdk*`, `mdr*`, `mdt*`, `t01`-`t04` |
| MM8 | none | all |

## Events

- **The pipeline.** `tools/regenerate_lua_events.sh` runs `openyamm_event_asset_export` once for the global script
  (MM8 config), then once per world with `--skip-global`. The configs (`tools/lua_event_export.mm{6,7,8}.ini`) read:
  - EVT/STR from each world's `_legacy/events`;
  - lookups from the merged `engine/data_tables`, including `quests.txt`;
  - only titles and summon object types from GrayFace's decompiled scripts
    (`tools/event_asset_export_main.cpp:1500-1710, 2224-2233`).
  - `version = 6/7/8` drives per-game remaps of damage types, skills and spells (`tools/LegacyLuaExport.cpp:1041-1130`).
- **Every input EVT is an MMerge file:**

  | World | From the MMerge game LOD | From `mmmerge.T.lod` | Other |
  |---|---|---|---|
  | mm6 | 71 | 208 | — |
  | mm7 | 76 | 209 | — |
  | mm8 | — | 269 | 2 vanilla-only STRs |

- **The global script.** `engine/events/Global.lua` comes from MMerge's merged `Global.EVT`, not vanilla MM8's.
- **MMerge's MM8 events differ from vanilla.** 56 of 125 MM8 EVT/STR files differ, mostly through id
  renumbering.
- **Hard-coded fixes.** The exporter forces Town Portal QBits for 6 MM7 and 6 MM8 maps
  (`tools/event_asset_export_main.cpp:2059-2111`).
- **Overlays:**

  | World | Map scripts | `*_mmmerge.lua` overlays | Other overlays | Global overlays |
  |---|---|---|---|---|
  | mm6 | 99 | 26 | 6 (`outb2_1`, `outd1_1`, `outd3_1`, `oute2_1`, `oute3_1`, `oute3_intro`) | `Global_mm6_mmmerge.lua` |
  | mm7 | 101 | 25 | — | `Global_mm7_mmmerge.lua` |
  | mm8 | 76 | 14 | `out01_intro` | `Global_mm8_promotions.lua` |

  The engine adds `Global_learned_effects`, `Global_mm6_gold_bags`, `Global_mmmerge_crystals` and
  `common/cross_continents_common.lua`.

### What MMerge changed in the events

GrayFace's decompiled sets in `reference/mmext-scripts/Decompiled_Scripts/`:
- `mm6orig`, `mm7orig` and `mm8orig` are the retail events.
- `mm6`, `mm7` and `mm8` are his patched, still non-MMerge events. They differ from retail in 34 of 82, 26 of 77 and
  14 of 62 files.
- No decompiled MMerge set exists; the comparison used our own EVT dumps.

**The event structure is barely touched:**

| World | Maps with the same event ids | Events with a changed step count |
|---|---|---|
| mm6 | 62 of 67 (1 event added, 4 removed) | 73 of 2,581 |
| mm7 | 74 of 76 | 24 of 3,370 |
| mm8 | 61 of 61 | 1 of 5,437 |

**Ids are renumbered throughout:**

| Origin | QBits | NPCs | Houses |
|---|---|---|---|
| MM6 | +1024 (427 of 439 references) | +785 (14 of 15) | irregular (+168, +21, +47, +68, +1504, ...) |
| MM7 | +512 (471 of 538) | +339 (59 of 59) | irregular (+638, +636, +132, ...) |
| MM8 | +0 | a few small shifts (-4, -13, -188) | renumbered too (+222, +623, +219 most common; house 224 "Hiss' Hut" is 761) |

- **Exit targets** use the renamed maps (`d06.blv` becomes `7d06.blv`).
- **No EVT contains a cross-world exit.** Cross-continent travel lives only in MMerge's Lua, in our overlays and common
  scripts (13 overlays call `MoveToMap`), and in the tables (`outdoor_travels`, `transport_*`, `continent_settings`,
  `town_portal_switch`).

**For vanilla mode:** the MMerge events are the original events with merged ids. Keeping them, dropping the overlays,
and auditing the ~100 structurally changed events gets close to vanilla without re-importing anything.

## Tables

- **`assets_dev/engine/data_tables/`** is derived from MMerge with local edits.
  - Byte-identical to MMerge: `quests.txt`, autonotes, awards, `npc_greet`, `roster`, `npc_group` and `npc_news`.
  - Mostly shared: `npc` 1,050 of 1,226 lines, `items` 1,880 of 2,205, `house_data` 1,600 of 1,609, `map_stats`
    659 of 784, `monster_data` 520 of 659.
- **`worlds/mm6/_legacy/tables`** (83 files) are pure MMerge copies, not original MM6. There is no
  `mm7/_legacy/tables`.
- **`worlds/mm6/_legacy/bin_tables` and `tile_tables`** match MMerge.
- **`worlds/mm8/_legacy/bin_tables` and `tile_tables`** are vanilla MM8 from before the merge (commit `44259aea2`);
  `dift`, `dobjlist`, `dsounds`, `dtft` and `dtile*` differ from MMerge.

## Original data available locally

| Game | What we have |
|---|---|
| MM6 | Only GrayFace's decompiled events (`Decompiled_Scripts/mm6orig`, `mm6`, `mm6orig/v1.0`) with their strings. **No LODs, EVT binaries or tables.** |
| MM7 | Only GrayFace's decompiled events (`mm7orig`, `mm7`), plus OpenEnroth (`reference/OpenEnroth-git/`) as a rules reference with some hard-coded MM7 tables (spells, class skills). **No LODs or tables.** |
| MM8 | Everything, in three places (below). |

**MM8 sources:**
1. **`re_mm8/mm8_orig/`**, a GOG install with GrayFace's patch 2.5.7.
   - `games.lod` (61 maps plus 61 deltas) and `00 patch.games.lod`.
   - `EnglishT.lod` (62 EVT, 63 STR, 41 tables) and `00 patch.T.lod`.
   - `EnglishD.lod`, `bitmaps`, `icons` and `sprites` LODs, and `new.lod` (new-game template).
   - `DataFiles/*.bin` and `Data/Tables/*.txt` (MMExtension table dumps).
2. **`data/Data/*.lod/`** (gitignored), an extracted unpatched MM8.
3. **Commit `6bb16f623`** (2026-05-01), our own full vanilla MM8 build from just before the merge: 120 EVT/STR
   files, 61 generated map scripts, a vanilla `Global.lua`, 49 converted tables and the maps.

**LOD format.** `EnglishT`, `EnglishD` and `00 patch.T.lod` are `MMVIII` LODs: a 256-byte header and 76-byte
directory entries with 64-byte names. `games.lod` (`GameMMVI`), `bitmaps`, `icons` and `sprites` (`MMVI`) and
`new.lod` (`MMVII`) use 32-byte entries with 16-byte names. Compressed entries have a header (`0x16741`, `"mvii"`,
packed size, unpacked size) and zlib data.

## Id numbering at runtime

| Registry | Rows | Layout |
|---|---|---|
| QBits (`quests.txt`) | 1,719 | MM8 1-511, MM7 513-1023, MM6 1025-~1600, MMerge extras ~1600-1719 |
| NPCs (`npc.txt`) | 1,224 | MM8 1-339, MM7 340-784, MM6 785+ |
| Houses | 1,607 | merged, irregular |
| Items | 2,201 | merged blocks per game plus extras |

Original events would clash with this space:
- Original MM6 and MM7 events use small QBit and NPC ids that would point at MM8 entries.
- House ids differ for all three games.
- Original MM8 events match on QBits and nearly on NPCs, but still need a house remap.

This is the main reason the [recommended approach](README.md#recommended-approach) keeps the merged ids.
