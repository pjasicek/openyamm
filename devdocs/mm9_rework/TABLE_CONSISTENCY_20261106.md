# MM9 table consistency sweep (2026-11-06)

A report only: nothing under `assets_dev/`, `assets_editor_dev/` or `output/mm9_rework/` was written. I regenerated
every generator into a scratch directory (`/tmp/claude-1000/.../scratchpad/table_sweep/`) and compared the result
byte for byte with the file on disk. `assets_dev/worlds/mm9/` is git-ignored, so "checked in" means the file on disk.
The sweep ran while the final 44-map rebuild was converting (root A at `lichlab`, root B at `afterworld`).

## Summary

- **Generated runtime tables: all CURRENT.** Items, vendors, monsters, hirelings, modifiers, relations, the quest
  overlay, quest interactions, skill trainers, teacher schedules and the `map_stats` encounter columns all regenerate
  byte-identical, or differ only in a provenance path.
- **The real inconsistency is in the old import's map inputs.** P1 deleted the newest old-import sidecars from
  `assets_dev/worlds/mm9/maps`. The only copies left are in `output/mm9_rework/promotion_backup_20261106/`. The
  `assets_editor_dev` mirror that today's repointed defaults read holds older copies from 2026-09-17:
  - every `*.events.yml` (45 maps) is older;
  - the whole sidecar set of bootcamp, lindisfarne, thjoradmine, wizardslab and yorwick is older.

  This causes the `quest_interactions --check` failure and the teacher-schedule failure. It also means this rebuild
  reads older `material_aliases` for bootcamp, lindisfarne, wizardslab and yorwick.
- **Converter-owned `map_transitions.txt` is wrong for the 11 outdoor BLVs.** Their exit volumes (about 45 rows) and
  arrivals (42 rows) are still in the old ODM frame, not shifted by the map's `overrides.yml` offset. Transport
  routes are correct.
- **Three scripts are now unsafe:** `regenerate_mm9_maps.sh`, `regenerate_mm9_all.sh` and
  `run_mm9_transitions_transport_skills_gate.sh`. They would overwrite converter-owned tables and Lua (details below).

## Table

Status words: **CURRENT**: regenerates identically · **STALE**: inputs or generator newer than the file ·
**HAND_EDITED**: contains rows the generator cannot produce · **ORPHAN**: no generator (hand-authored by design
where noted) · **BROKEN**: the generator fails or gives a wrong result with its defaults.

Abbreviations:

- `T` = `tools/mm9_import_discovery`
- `W` = `assets_dev/worlds/mm9`
- `E` = `assets_editor_dev/worlds/mm9`
- `BK` = `output/mm9_rework/promotion_backup_20261106/worlds/mm9/maps`
- `RT` = read by the runtime (`world.yml` `tableContributions`, `Mm9QuestMarkers`, actor behaviours)

| File | Generator (inputs) | Status | Cause / detail | Readers | Fix |
|---|---|---|---|---|---|
| `W/data_tables/items, random_items, readable_items, item_effects, item_sets, item_aliases, object_descriptors.txt`; `W/state/item_ids, item_import_report, item_icon_manifest, item_script_reference_report, world_item_sprite_manifest.yml`; `W/rendering/sprite_frame_data_world_items.yml`; `W/icons_x2/mm9_item_*`; `W/sprites/mm9wi*` | `T/import_mm9_items.py` (MASTERITEMLIST, `mm9_item_*.yml`, generated art, engine `object_list`/`items`) | CURRENT | all byte-identical | RT; vendors generator; converters (`dungeon/content.py`, 1000terrors, klusoshouse read `item_ids` and the script report) | none |
| `W/data_tables/vendors, vendor_aliases, vendor_stock, vendor_concat_mappings, service_venues, service_venue_aliases.txt`; `W/state/vendor_stock_audit.yml` | `T/generate_mm9_vendors.py` (MMIXSHOPS, CONCAT, RUDE, MM9 and engine items) | CURRENT | | RT (concat mappings: audit only) | none |
| `W/data_tables/monster_data, monster_descriptors.txt`, `monster_conversion_audit.tsv` | `T/generate_mm9_monster_tables.py` (MONSTERS.txt, replacements, families, bodies, engine monster tables) | CURRENT | | RT; converters (`dungeon/content.py`, thearena, hallofthegods, 1000terrors, anskramkeep, wizardslab, drangheimprison, thjoradmine) | none |
| `E/data_tables/*` (items 09-17, monster tables 10-29) | mirror copies made by `regenerate_mm9_maps.sh` | STALE | old mirror; differs from `W` | not mounted by the game (the editor root is only created); no converter reads it | `python3 T/generate_mm9_monster_tables.py --output-dir E/data_tables`, or delete the mirror copies |
| `W/data_tables/hirelings.txt` | `T/generate_mm9_hirelings.py` | CURRENT | | RT; `actor_completeness.py` | none |
| `W/modifiers.yml`, `W/relations.yml` | `T/generate_mm9_monster_modifiers.py` (writes `relations.yml` beside `--output`) | CURRENT | | RT | none |
| `W/behaviors.yml`, `W/behaviors/*.lua` | none | ORPHAN (hand-authored) | its 6 monster ids match `monster_data` | RT | none |
| `W/data_tables/english/quests_overlay.txt` | `T/generate_mm9_quest_overlay.py --check` | CURRENT | | RT (journal) | none |
| `W/data_tables/complex_item_pictures.txt`, `W/icons_x2` paperdolls | `T/install_mm9_item_art_x2.py` (`level_generation/ui/mm9_item_icons_20261104/paperdoll/runtime`) | CURRENT | table and 488 doll files match the project | RT | none |
| `W/state/item_body_equipment_visuals.yml`, `W/state/armor_foot_exclusions/` | `T/generate_mm9_equipment_variants.py --promote` | BROKEN (art pipeline) | refuses to run: "engine icon tree changed after the MM9 equipment snapshot" (engine icons moved to `icons_x2` and were archived 2026-09-26) | equipment tools | refresh the authored-art snapshot hash (art pipeline task) |
| `T/mm9_item_equipment_visuals.yml` (tool input) | `T/generate_mm9_item_equipment_visuals.py` (stdout) | HAND_EDITED | items 56–60 (spears, `Weapon1or2`) are not in the generator's equip set; the other 92 entries match | `import_mm9_items.py` | add `Weapon1or2` to the generator, or mark the 5 entries manual |
| `W/data_tables/decoration_data.txt` | per-map `level_generation/props/mm9_*_claude/scripts/tables.py` (append) | CURRENT (integrity) | 812 rows, 2001–2812, inside world range 2001–2999, no duplicate ids/names, no clash with engine rows | RT; `dungeon/content.py`, isleofashes | none |
| `assets_dev/engine/data_tables/map_stats.txt` (MM9 rows) | encounter columns: `T/generate_mm9_map_stats_encounters.py`; map file names: converters (`dungeon/tables.py`, P1 merge) | CURRENT | encounter pass changes 0 rows; the 44 rows that differ from `original_tables` differ only in `.odm`→`.blv`; greatgate row removed (P1) | RT; converters | none |
| `assets_dev/engine/data_tables/character_data.txt` rows 9001–9024 | `level_generation/ui/hud_inventory/mm9_pc_dolls/install.py` | HAND_EDITED | all 20 rows: `World` set to `mm9` by hand; the installer copies the donor's `mm7`/`mm8` | RT | make `install.py` write `World = mm9` |
| `engine/data_tables/bolster_maps, continent_settings, town_portal_switch, doll_types.txt`, `character_selection.yml`, `W/world.yml` | none | ORPHAN (hand-authored; MM9 start continent work) | not checked against a generator | RT | none |
| `engine/data_tables/texture_frame_data.txt`, `engine/liquids/liquids.yml`, `W/ui/maps/catalog.yml` | converters + P1 merge | converter-owned | not regenerable outside the rebuild | RT | (rebuild) |
| `W/data_tables/map_transitions.txt` | converters (`dungeon/tables.py transitions_text` over `mm9r_common/original_tables/map_transitions.txt`); the old `T/generate_mm9_transitions.py` produces only the frozen original | STALE (converter rows) | 45 exit volumes and 42 arrivals of the 11 outdoor BLVs (afterworld, drangheim, frosgard, guberland, isleofashes, lindisfarne, mountainpass, sturmford, thjorgard, thronheim, yorwick) are in the old ODM frame. The arrival differs from the scene start by exactly −offset (e.g. thronheim `ConnectingTunnelsExit`: row −17439, scene 16168; offset −33607). Root B's table was last written 2026-11-04 21:44. Today's afterworld build at 16:31 reported unshifted centres. `dungeon/tables.py` was changed at 16:54, during the rebuild. The 45 other arrivals whose start is named in the scene match it. 18 rows name a start the scene does not list (e.g. `Bathhouseexit`, `SewerS`); they arrive by coordinates, and I did not judge them. | RT (`Mm9MapTransition`); converters (`transitions_text` starts from the review root's current rows; `make_scenarios.py`) | after the rebuild, run the checker below on both roots. If rows are still unshifted, fix the outdoor path, then reconvert afterworld (converted before 16:54) and any others it lists |
| `T/generate_mm9_transitions.py` → `original_tables/map_transitions.txt`, `W/import/map_transition_audit.yml` | maps-dir `E/maps` | CURRENT vs the frozen original | same output from `E` or `BK` | — | **change its default `--output` away from `W/data_tables`** (see hazards) |
| `W/data_tables/transport_routes.txt` | converters (`outdoor_blv.rewrite_transport`, P1) | CURRENT | all 47 arrivals equal the destination scene's start | RT; frosgardcity `transport.py`, isleofashes story | none |
| `T/generate_mm9_transport_routes.py` → `original_tables/transport_routes.txt`, `W/import/transport_route_audit.yml` | | CURRENT vs the frozen original | | — | same hazard as transitions |
| `W/data_tables/skill_trainers.txt`, `W/import/skill_trainer_audit.yml` | `T/generate_mm9_skill_trainers.py` (RUDE, `E/maps`, SCR) | CURRENT (content) | only the `ActorSources` provenance path changes (`assets_dev/...maps` → `assets_editor_dev/...`). The runtime does not read it. With the stale `E` maps the audit also loses yorwick/lindisfarne actor sources. | RT | after the restore: `python3 T/generate_mm9_skill_trainers.py` (optional, provenance only) |
| `W/data_tables/teacher_schedules.txt`, `W/import/teacher_schedule_audit.yml` | `T/generate_mm9_teacher_schedules.py` (trainer audit, SCR, `E/maps`) | CURRENT with `BK`; BROKEN with defaults | with `E/maps`: "structural errors", 13 × "RUDE 323/327/...: scene actor ... missing" (stale `E` scenes of the 5 maps). The table is header-only (0 resolved schedules). | RT | restore `E` (step 1) |
| `W/state/quest_interactions.yml`, `quest_interaction_coverage.yml` | `T/generate_mm9_quest_interactions.py` (RUDE, `--maps-root` scenes, `--raw-maps-root` raw objects, `--events-root` `*.events.yml`, SCR) | CURRENT; BROKEN with defaults | `--maps-root BK --events-root BK` reproduces both files byte for byte. All 170 bindings `(map, source_object_index, rude)` exist in the rebuilt BLV scenes, and the runtime binds on map + `source_object_index` only. See "Quest interactions" below. | RT (`Mm9QuestMarkers`) | step 1, then make the scene parser read JSON scenes or default `--maps-root` to `E/maps` |
| `E/maps/*.events.yml` (45) | `T/generate_mm9_events.py` (raw objects, SCR) | STALE | made 09-17 by an older generator. The current generator over `E` raw objects reproduces `BK` for 41 maps. bootcamp, lindisfarne, wizardslab and yorwick differ because their `E` inputs are older too. 5 city maps lack `dialogue_callbacks` entirely. | quest-interactions generator | restore from `BK` (step 1) |
| `E/maps/{bootcamp,lindisfarne,thjoradmine,wizardslab,yorwick}.{odm,mm9.yml,scene.yml,nav,nav.yml,render,render.yml,material_aliases.yml}`, `{bootcamp,yorwick}.raw_objects.yml` | old import (`transcode_mm9_dat_to_odm.py`) | STALE | `BK` (deleted by P1) is newer. In raw objects, `E` has float-bit values (`1086324736` where `BK` has `6`). In material aliases, `E` lacks the props liquid/barrel skins (bootcamp, wizardslab: 8 entries) and has other entry differences in lindisfarne/yorwick. 26 `.lighting` files differ and 3 are missing (not read by the converters). | converters: `dungeon/source.py` aliases, `terrain_textures.py`, `terrain_blend.py` (aliases), `cutscenes.py`, `actor_completeness.py` (raw objects); generators: transitions, transport, trainers, teacher, quest, events, destructible inventory | restore from `BK` (step 1); reconvert `mm9r_bootcamp_blv`, `mm9r_lindisfarne_blv`, `mm9r_wizardslab`, `mm9r_yorwick_blv` |
| `W/events/common/world_common.lua` | `T/generate_mm9_events.py` | CURRENT | | RT | none |
| `W/events/maps/1000terrors.lua` | `mm9r_1000terrors/convert.py` | STALE (promoted copy) | `MoveToMap(..., "hallofthegods.odm")`; the rebuild's copy already says `.blv` | RT | promotion |
| `devdocs/mm9/MM9_DESTRUCTIBLE_BRUSH_INVENTORY.md` | `T/generate_mm9_destructible_brush_inventory.py --check` | CURRENT | | docs | none |

## Quest interactions: why `--check` fails

The error names 9 ids: arslegardcity 113/152, frosgardcity 560/562, guberlandcity 811/813/814, hallofthegods 126 and
sturmfordcity 830. These SCR candidates come from `dialogue_callbacks` in `*.events.yml`. The `E` copies of
arslegardcity, frosgardcity, guberlandcity, hallofthegods and sturmfordcity predate `dialogue_callbacks`.

This failure is not pre-existing. Before P1 the default `--events-root` was `assets_dev/.../maps`, which held the
newer files, and the check passed. P1 deleted those files, and the repoint now reads the 09-17 mirror. With
`--events-root BK` (or the regenerated events), all 9 ids resolve.

`--maps-root assets_dev` is BROKEN on its own as well. `scene_actor_bindings` is a line parser that expects block
YAML (`actors:` / `mm9_rude_id:`). The rebuilt BLV scenes are JSON with the actors under `initial_state.actors`, so
it finds 0 bindings: 0 interactions and 170 exclusions. `--maps-root E/maps` works and gives the same interactions.
After step 1 it reproduces both files.

## Hazards (do not run until fixed)

- **`T/regenerate_mm9_maps.sh` and `T/regenerate_mm9_all.sh`** would do all of the following:
  - write old ODM maps and Lua into `W/maps` and `W/events/maps`;
  - run `generate_mm9_events` with its default `--events-root W/events/maps`, overwriting rebuilt map Lua;
  - write the frozen-original `map_transitions`/`transport_routes` (`.odm` names, ODM frame) over the
    converter-owned tables, after which the game refuses both tables;
  - run quest interactions with `--maps-root W/maps`, which yields an empty result (see above).
- **`T/run_mm9_transitions_transport_skills_gate.sh`** runs `generate_mm9_transitions.py` and
  `generate_mm9_transport_routes.py` with their default outputs (the same overwrite). It also runs the teacher
  generator, which fails until step 1.
- **`generate_mm9_events.py`** with its defaults writes Lua into `W/events/maps` and `events.yml` into `E/maps`. Use
  scratch roots, or `--check-idempotent`.

## Test baselines (`python3 -m pytest -q tools/mm9_import_discovery`: 5 failed, 23 errors)

| Test | Verdict |
|---|---|
| `test_generate_mm9_quest_interactions::test_checked_in_inventory_matches_the_source_audit_baseline` | **Baseline stale** (pre-existing: fails with the HEAD tools too). The report has had 125 interactions and 66 exclusions since the 09-17 regeneration; the test expects 119/71. The table is correct: it regenerates identically. Update to 125/66. |
| `test_import_mm9_items::test_mm9_item_import_emits_stable_rows_and_readable_text` | **Baseline stale**: 5 assertions, and the test passes once they are updated (checked on a copy). (1) `10579[11] == "77"` → `"20579"`: a Quest Item gets its dedicated WorldItem sprite; the same rule is at HEAD, so this one is pre-existing. (2) `10086[29:31]` `["3","4"]` → `["3","3"]`; (3) report `equip_x/equip_y` 20/139 → 14/136; (4) `equipment_visual.reference_item_id` 4 → 3. Assertions 2–4 follow the uncommitted x2 icon/anchor change, which updated the neighbouring assertions but not these. The tables are correct. |
| `test_audit_mm9_armor_pose_pairs` (2), `test_generate_mm9_equipment_variants` (21 errors) | Art pipeline: the authored-art manifest's `engine_icons_tree_sha256` no longer matches `assets_dev/engine/icons_x2` (snapshot stale). |
| `test_mm9_equipment_legacy_base_mappings::test_every_reference_has_all_equippable_doll_variants` | Art pipeline: looks for `v1`–`v5a` dolls under the retired `assets_dev/engine/icons` (archived under `assets_legacy/icons_20260926`). Stale path. |
| `test_model_registry_layout` (collection) | Orphan test: imports `mm9_generate_actor_billboards`, which no longer exists (only a stale `.pyc` in `tools/__pycache__`). |
| `test_dat_bsp_parser` (collection) | `pygltflib` not installed (ignored). |

## Fix order (after the rebuild finishes)

1. Restore the old-import inputs into the editor root:
   ```
   B=output/mm9_rework/promotion_backup_20261106/worlds/mm9/maps; E=assets_editor_dev/worlds/mm9/maps
   cp -p $B/*.events.yml $E/
   for m in bootcamp lindisfarne thjoradmine wizardslab yorwick; do
     for s in odm mm9.yml scene.yml raw_objects.yml material_aliases.yml nav nav.yml render render.yml; do cp -p $B/$m.$s $E/; done
   done
   ```
2. Reconvert the maps that read the older editor aliases in this rebuild: `mm9r_bootcamp_blv`, `mm9r_lindisfarne_blv`,
   `mm9r_wizardslab`, `mm9r_yorwick_blv`. Also reconvert `mm9r_afterworld_blv` (converted before the 16:54
   `tables.py` change). Then run the transition checker on both roots and on `assets_dev` after promotion.
3. Quest interactions: fix `scene_actor_bindings` to load the JSON scenes, or default `--maps-root` to `E/maps`. Then
   run `python3 T/generate_mm9_quest_interactions.py --maps-root assets_editor_dev/worlds/mm9/maps --check`
   (expected: current).
4. Teacher schedules: regenerate into scratch to confirm, e.g.
   `python3 T/generate_mm9_teacher_schedules.py --output /tmp/t.txt --audit-output /tmp/a.yml` (expected: no
   errors, identical files).
5. Optional: `python3 T/generate_mm9_skill_trainers.py` (provenance paths only).
6. Repoint the default `--output`/`--audit` of `generate_mm9_transitions.py` and `generate_mm9_transport_routes.py`
   to `level_generation/projects/mm9r_common/original_tables/` (or retire them). Drop them, and the old map
   conversion, from `regenerate_mm9_maps.sh`, `regenerate_mm9_all.sh` and the gate script.
7. Update the two test baselines above, `mm9_pc_dolls/install.py` (`World = mm9`), and the equipment-visual
   generator (`Weapon1or2`). Refresh the editor `data_tables` mirror or delete it.

## Appendix: transition frame checker

Saved as `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/5f3ee9b7-b9a0-4f16-90b8-d435706c6a63/scratchpad/table_sweep/check_transition_frames.py`.
Run it from the repository root: `python3 <path> [assets root]`, default `assets_dev`. For every
`map_transitions`/`transport_routes` row it checks two things:

- the arrival matches the destination scene's `party_start_points` entry of the same name;
- for maps with a non-zero offset, the exit volume equals the frozen original minus the offset.

On today's `assets_dev` it prints: 46 exit volumes and 42 arrivals off (the bootcamp relay exit is counted among the
46 and is likely a false positive).

## Applied (2026-11-06, ~17:30)

- The old import's newest inputs restored into `assets_editor_dev/worlds/mm9/maps` from
  `output/mm9_rework/promotion_backup_20261106/worlds/mm9/maps` (116 files: all `*.events.yml`, the `.lighting` files,
  the full sidecar sets of bootcamp, lindisfarne, thjoradmine, wizardslab and yorwick); every backup file now matches.
- The shared exits writer (`mm9r_common/dungeon/tables.py`) applies overrides.yml `offset`; the Arslegard City and
  Connecting Tunnels wrappers no longer re-offset from assets_dev. Old-import originals are read from
  `mm9r_common/original_tables/` (map_stats, map_transitions, transport_routes, catalog).
- Generators: eight `tools/mm9_import_discovery` map-input defaults read `assets_editor_dev`
  (quest interactions too: `--check` is current again); `generate_mm9_transitions.py` and
  `generate_mm9_transport_routes.py` default to `original_tables/`; `regenerate_mm9_maps.sh` (and so
  `regenerate_mm9_all.sh`) refuses to run unless `MM9_OLD_IMPORT=1`.
- Test baselines updated: quest interactions (125 interactions, 66 exclusions), item import (five assertions).
  Remaining failures are the equipment-art pipeline's (icon snapshot, retired icons path), the orphan
  `test_model_registry_layout` and the missing `pygltflib`.
- Every map is reconverted in R3 after the audit fixes, so no map keeps rows or inputs from before these changes.
- (~17:55) Every converter's old-import scene read (`OLD_SCENE` in 12 city/dungeon converters, the Anskram legacy
  converter, `outdoor_blv.py`'s placement `old_path`, `dungeon/tables.py` `install_original_comparison`,
  `density_anchors.py`, the Isle's `story.py`) pointed at `assets_dev/worlds/mm9/maps`, which since P1 holds the
  rework's own scenes; all now read `assets_editor_dev/worlds/mm9/maps`. The comparison mirror
  `output/mm9_rework/assets_original` received rework scenes for maps converted after P1; each map's next conversion
  rewrites its copy from the old import.
