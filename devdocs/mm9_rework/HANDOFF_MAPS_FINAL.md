# Handoff: finishing the MM9 maps (2026-11-05)

For the next session picking up the MM9 map work (from openyamm-30). Read with the task log
[REGIONS_FINISH.md](REGIONS_FINISH.md), whose "Final plan" section is the user's current instruction, and
AGENTS.md/CLAUDE.md. Nothing below is committed; the user reviews and commits (never `git add/commit/stash/reset`).

## The user's plan (2026-11-05)

1. Engine door work: done (below).
2. **Final reconversion of every MM9 map, once, for good**: complete props, complete NPCs and monsters (the new 3D
   ones), complete lighting **with lightmaps** (MM9's own, transferred; adapted where weak).
3. **Install**: remove every old MM9 map import from `assets_dev`, keep only the rebuilt ones; MM6-MM8 regression.
4. **Consolidate**: move everything from the MM9 review roots into `assets_dev`; one playable place afterwards.

**Steps 3 and 4 done 2026-11-06** ([FINAL_REBUILD_WORK.md](FINAL_REBUILD_WORK.md) P1): `assets_dev/worlds/mm9` holds
only the 44 rebuilt BLVs; the old import's 45 ODMs and their sidecars are gone (copies in
`output/mm9_rework/promotion_backup_20261106/`). Play from the default asset root. The converters still install into
the review roots: a map reconverted later is promoted again (see P1).

Before step 2 the user wants to see the transferred lightmaps on two maps (Yanmir's Fort and Sturmford City) in game.

## Blocker right now: reboot

The NVIDIA kernel driver (595.91.07) no longer matches the updated user libraries (595.99.02): the game finds no GPU
(`GPU: vendor=0x0 device=0x0` in game.log) and renders in software (~0.5 fps). A reboot fixes it; the user decides
when. After a reboot `/tmp` and the scratchpad are gone and `kernel.perf_event_paranoid` is back to 4
(`./tools/profile_game.sh --enable-user-perf` sets 2 again).

## Where things are

| What | Where |
| --- | --- |
| All 44 rebuilt maps (since 2026-11-06) | `assets_dev/worlds/mm9` (the default asset root) |
| Rebuilt cities, dungeons, Wizard's Lab (review root, where conversions install) | `output/mm9_rework/assets_dev` (play: `--assets output/mm9_rework/assets_dev`) |
| Rebuilt regions + Afterworld (review root, where conversions install) | `output/mm9_rework/isleofashes_blv_root` |
| Map converters | `level_generation/projects/mm9r_<map>/convert.py`; shared code `level_generation/projects/mm9r_common/` (`dungeon/`, `city/`, `outdoor_blv.py`, `review_root.py`) |
| Region scripts | `level_generation/projects/mm9r_<region>_blv/regionlua.py` + `work/scr_spec.md` (all 11 regions) |
| Wizard's Lab | `level_generation/projects/mm9r_wizardslab/` (converted; no props yet) |
| Task log, map state | [REGIONS_FINISH.md](REGIONS_FINISH.md), [OUTDOOR_BLV_ALL.md](OUTDOOR_BLV_ALL.md), [DECORATIONS_AND_GRASS.md](DECORATIONS_AND_GRASS.md) |
| Lightmap transfer | [MM9_LIGHTMAP_TRANSFER.md](MM9_LIGHTMAP_TRANSFER.md) ("Layout-only base" at the end), [MM9_LIGHTING_DECISION.md](MM9_LIGHTING_DECISION.md) |
| MM9 door behaviour (RE) | [MM9_DOOR_OPEN_RE.md](MM9_DOOR_OPEN_RE.md) |

Run a map (repository root):

```sh
./tools/run_game.sh --isolated sturmford --assets output/mm9_rework/isleofashes_blv_root --world mm9 --map sturmford.blv --visible --seconds 0
./tools/run_game.sh --isolated sturmfordcity --assets output/mm9_rework/assets_dev --world mm9 --map sturmfordcity.blv --visible --seconds 0
```

Console helpers: `destructible <id> destroy|damage <n>`, `event <id>`, `effect spawn <id> x y z [scale]`.

## Done in this session (all built; unit tests pass: 474 indoor/path/door, 70+ others)

Engine (shared, MM6-MM8 benefit too):
- **BLV destructibles** ([../INDOOR_DESTRUCTIBLES.md](../INDOOR_DESTRUCTIBLES.md)): scene `destructibles`, damage by
  party/event missiles and melee (faces and decorations), invisible MM9 RayHit boxes hittable while standing
  (`IndoorMapData::destructibleFaceMask`), Lua `evt.DamageDestructible/DestroyDestructible/SetDestructibleDamage/
  IsDestructibleDestroyed`, debris effects `openyamm:fx/destructible/{stone,wood,glass,metal}`, saved state.
- **Pulsing lights** ([../INDOOR_PULSING_LIGHTS.md](../INDOOR_PULSING_LIGHTS.md)), **ambient sounds**
  ([../AMBIENT_SOUNDS.md](../AMBIENT_SOUNDS.md)), **lava volumes burn**, **skinned flipbooks** (animated creature skins),
  **indoor MM9 FoundPlayer greetings**, sky preset `night_stars`.
- **Performance** (region-sized BLVs): broken props no longer re-light the map; destroyed faces update in place in the
  renderer (`IndoorRenderer::updateFaceAttributeChanges`, 345 ms -> 1.5 ms); door clicks no longer invalidate all
  runtime geometry; `PathMap::rebuildSpatialGrid` built from one sorted list, facets over 4096 cells kept out of the
  cells; the monsters' path map rebuilt off the main thread (`IndoorWorldRuntime::m_pendingPathMap`, adopted at the
  next AI update). Door settle on Sturmford 300-400 ms -> ~40-65 ms (remaining: monsters re-planning).

Converters:
- Every region: people (`npcs()`, incl. script-id people), shared doors with clicks, locked doors (MM9 `Locked`, no
  key, no unlock trigger), keyed doors, `BARRED_DOORS` (Yorwick's gate, Sturmford's drawbridge chains), ForadWorld,
  region scripts, destructibles, ambient sounds. All 11 reconverted and load without Lua errors.
- `dungeon/destructibles.py` (brushes incl. invisible RayHit boxes and **breakable glass**, props), `dungeon/ambient.py`,
  `dungeon/lights.py` `pulsing_lights` and unique names for MM9's reused light names, Bootcamp's dock exit
  (`tables.relayed_exits`).
- **NPC rows**: `dungeon/content.py` `Content.actor` places MM9's 118 townsfolk/uniques/town animals
  (`tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`) on 9000 + row (their 3D models) instead of MM6-MM8 stand-ins.
- **Lighting, layout-only base**: `dungeon/lighting.py --layout-only [--root]` + `tools/lighting/bake_indoor.py
  --layout-only --units-per-texel --skip-textures`, and `lightmap_transfer.py` (vertex-lit MM9 surfaces stay
  vertex-lit, per-sector actor ambient recomputed). 45 min -> under a minute per map. Results (dry runs, nothing
  installed): Yanmir's Fort 98.8 % MM9 texels, 6.5 MB; Sturmford City 98.6 %; Yorwick 92 %, 1.2 MB.
  Yanmir's old (stale, never installed) Cycles passes are in `output/mm9_rework/bakes/yanmirsfort_cycles`.

## State at 2026-11-05 20:15: the final rebuild is done

[FINAL_REBUILD_WORK.md](FINAL_REBUILD_WORK.md) is the checklist and log. Done: the engine deltas (E1-E6), shared data
and Lua (D1 promotions as corrected by the user, D2 separate skills, D3 the ending), the shared converter items
(C1-C7, C9, C10; C8 swimming/breakables by damage left: per-map geometry work), the map items M1-M10. All 44 maps
reconverted with lightmap transfer into the review roots (18:35-19:52); all load headless without Lua errors; 111 of
125 map scenarios passed at once, the 14 others (door timing under the new linear mover rules, a few actor checks)
are being triaged. Open: M11 (Sturmford City's magic shop ceiling: the street air leaks into the shop, reconvert that
map alone), M12 (Blaster and racial-ability trainers: MMerge has them in MM7/MM8; user decision), C8.
MM6-MM8 regression: unit tests 2 618 of 2 621 (the 3 failures are other sessions' pending item/icon/Hesper work),
tests/scenarios 8 of 9 (mm8_right_click_portrait_item: Cure Wounds refused on the inventory page, potion UI work).

## Next steps, in order (written before the rebuild)

**Before the final reconversion read [FINAL_REBUILD_GAPS.md](FINAL_REBUILD_GAPS.md)** (2026-11-05: the sweep of every
map against MM9's DATs and scripts): what is still missing, what needs the rebuild and what does not.


1. **After the reboot: lightmap check on two maps.** For each of `mm9r_yanmirsfort` (root
   `output/mm9_rework/assets_dev`) and `mm9r_sturmfordcity`:
   ```sh
   P=level_generation/projects/mm9r_yanmirsfort
   python3 level_generation/projects/mm9r_common/dungeon/lighting.py $P --layout-only --no-install
   python3 level_generation/projects/mm9r_common/lightmap_transfer.py $P --install      # backs up first
   python3 level_generation/projects/mm9r_common/lightmap_rollout.py capture yanmirsfort transfer
   python3 level_generation/projects/mm9r_common/lightmap_rollout.py sheet yanmirsfort  # real | before | transfer
   ```
   **2026-11-05 11:00, still before the reboot: the first two commands are done for both maps** (installed in
   `output/mm9_rework/assets_dev`; coverage Yanmir's Fort 99.1 %, Sturmford City 98.8 %; backups and REVERT.md in each
   project's `work/lighting_before_transfer/`). Only `capture` and `sheet` remain. Headless loads are clean; Yanmir's
   `scenario_doors_exits.yml` fails at step 4 (exit trigger 777 to Iver's Estate records no transition), unrelated to
   the lighting and not yet investigated.
   **11:40, after the reboot: captured and sheeted** (`<project>/review/lmroll_real.jpg`, `lmroll_review_pNN.jpg`;
   luma in `work/lightmap_transfer/luma.json`). Yanmir's Fort is 0.81-1.01x the real MM9 shots' luma (Cycles bake
   1.19-1.45x), no view under DARK; darkest the spiral stair (25) and the key room (28). Sturmford City: 32 views, no
   dark views, no patches seen. The `before` root (`lightmap_rollout_before`) no longer loads with the current binary
   (`worlds/mm7/models/actors.yml: actor animation clip not found: Jog`, the 2026-11-04 gait clips); the Yanmir before
   shots on the sheets are the 2026-10-31 ones (same Cycles bake). Sturmford City's magic shop (`i11_magic_shop`) shows
   the sky where its ceiling should be: geometry, not lighting; not investigated. Waiting for the user's verdict.
   Show the user the sheets (real MM9 screenshots exist for Yanmir's Fort, Boot Camp, Klusos House, Dungeon of
   Secrets: `devdocs/mm9_rework/overnight/real_mm9/`). Check: no dark or grey patches, terrain unchanged, actors' ambient sane, FPS.
   Regions/open-air maps take `--root output/mm9_rework/isleofashes_blv_root` on both tools.
2. **Wizard's Lab props** and a walk-through of its teleporters and the summoning ritual: **done 2026-11-05**
   (level_generation/props/mm9_wizardslab_claude/README.md, the map README's status; both scenarios pass).
   **Then the region props gaps** (user, 2026-11-05: now, before the reconversion), from the props audit
   (devdocs/mm9_rework/checks/props_audit_20261105.md): the regions' inventory.py placed only Prop and CandleProp, so
   19 region chests had no decoration (unopenable), and bone piles, 7 stat barrels, Afterworld's 6 braziers, Mountain
   Pass's burning logs, Lindisfarne's well and clover, 8 cauldrons and 8 cook pots were dropped. inventory.py's CLASSES and
   placements.py's CLASS_KIND (TreasureChest -> chest, Torch -> torch) now include them: all eleven region props.json
   rewritten (work/placements_20261105.log), Mountain Pass reconverted and its chest opened by a click from every side;
   the other ten regions take it at the final reconversion. Beethoven's rubble binding added (worlds/mm9/models/
   indoor_decorations.yml).
   **Done 2026-11-05 13:40** (mm9_outdoor_regions_claude/README.md "Added 2026-11-05"): the stat stones (four colour
   variants of the isle's orb stone, their timed bonus in outdoor_blv.py `stat_stones`, event 390 + k; Sturmford's
   proved headless: bonus once while it lasts), the battle witch axes (tilted), Boot Camp's rune stone, and the posed
   figures as our 3D models (scripts/pose_bake.py: Afterworld's fallen and seated heroes, Boot Camp's nine museum
   creatures). Yorwick's battlefield set (70 objects) is left out: MM9 shows it only in the battlefield cutscene,
   which the map does not carry. Boot Camp, Afterworld and Sturmford reconverted and seen in game
   (the other regions at the final reconversion). The Arena's 11 seated spectators (MM9's seated meshes: no seated
   3D peasant exists) were handed to a background agent on the Sturmford City route; the Arena needs a
   reconversion after it: done 13:36 (spectators seen seated on the stands). Also built: Frosgard's Green Man's
   tree (MM9's mesh) and the whack-a-honky geese at rest in their holes (the game itself stays an open item).
3. **Tell openyamm-cf** (MM9 creatures session) before the reconversion: it drops to 3-4 agents for memory. Its
   models are done; only triangle reductions still run (they do not affect conversion or lighting).
4. **Final reconversion, one map at a time** (all 44: 7 cities, 24 dungeons, 11 regions, Afterworld, Wizard's Lab;
   Great Gate is skipped). First the props pass's letter fix (user, 2026-11-05: part of the reconversion): one shared
   flat letter posed by scroll-open's `down` animation, chosen in every props table for `BookLetter.scr` objects whose
   third script parameter (`bDown`) is 1, replacing Thjorgard City's `LAID_FLAT` guess (details under "Letters standing
   upright" below). Then per map: `convert.py`, then `lighting.py --layout-only` + `lightmap_transfer.py --install`, then a
   desktop load check (game.log: no `Lua event error`, `could not parse`). Gate every heavy job:
   `pgrep -f "^(timeout [0-9]+ )?cmake --build build"` and `pgrep -f "^(timeout [0-9]+ )?python3 level_generation/
   projects/mm9r_.*/convert.py"`. Never a build beside a conversion (out of memory, 2026-11-04). Refresh the review
   roots first (`review_root.refresh()`; the isle root with ASSETS/OWNED set as in `regions_pass4`-style scripts).
5. **Install** into `assets_dev` (step 3 of the plan) and run the MM6-MM8 regression (unit tests, scenarios in
   `tests/scenarios/`), save/load, map travel; then **consolidate** the review roots into `assets_dev` (step 4).
   Done 2026-11-06 (FINAL_REBUILD_WORK.md P1; save/load and map travel by hand not yet checked).
   Mind the hard links: `assets_dev` files share inodes with `output/` mirrors; never edit in place (temp + rename).
6. Before a commit: `tools/lighting/stale_bakes.py` (lighting sidecars must match their BLVs).

## Open items (not blocking the plan)

- **Letters standing upright (scheduled: step 4, the reconversion's props pass).** `BookLetter.scr`'s third parameter is
  `bDown`; `:Init` then plays `LoopAnim Down`: scroll-open's `down` animation turns the root so the sheet lies flat
  (binding extents 8x10x2 -> 8x2x10). The props tables ignore it and place the upright `Static_Model` (`scroll`, 46.6
  units tall): 40 letters with `bDown` 1 in 17 DATs (Sturmford City Prop0/Prop3/Prop7, e.g. letter 452 by the desk
  at 9632, 8037), all upright in our maps except Thjorgard City's four, laid flat there by the `LAID_FLAT` placement
  guess (whose note "a BookLetter letter on a counter keeps standing in MM9" is wrong). Letters without `bDown` stand
  in MM9 too and are right. Note `scrollp90` (pitch 90 on the static pose) lies on the other face than MM9's `down`
  (a half turn about the sheet's cross axis); a variant posed by the `down` animation is the faithful one.

- **Sturmford**: verify the drawbridge chains break with a real arrow (aim from inside the gatehouse); the user saw
  the gate lower when jumping on the closed drawbridge: cause not found (stepping on a door does not fire its click;
  ask the user for exact steps).
- **TouchToOpen** not supported: 1000 Terrors' 14 WeightedLifts (built static) and Bathhouse Door3/4 (open on click)
  need linear-door auto close and wall-touch triggers (`FaceAttribute::TriggerByTouch` is not handled anywhere).
- **Region quests**: Thjorgard's adult Magreeb not placed (blocks the Scholar promotion; MM9's flees, check hostility
  before adding the class); Afterworld's ExitTrigger1 always open (MM9 only at key 390); ForadDarre0 not placed;
  whack-a-honky, the stones game squares, cutscenes, followers, walking NPCs (after the NPC work).
- **Runtime skin swaps / node hiding** (MM9_VISUAL_PROPERTIES gap 3: Banshee decay, Ebora's sirens): needs a save
  format bump and a per-actor variant; not started.
- Ambient sounds cannot be switched by Lua (40 MM9 StartOn 0 sounds stay silent); missiles do not hit props.

## Gotchas learned

- `pgrep -f "<text>"` in a wait loop matches its own shell (`until ! pgrep -f ...`): anchor with `^` or wait on a PID.
- Other sessions build in the same tree: a header layout change compiled half by another build crashes
  (`~GameApplication`); touch the changed headers and rebuild.
- Another session's work-in-progress can break the build (`OutdoorWorldRuntime.cpp`); retry later, do not edit it.
- `assets_dev/engine/effects/authored/library.yml` and other `assets_dev` files are hard-linked into `output/` mirrors.
