# MM9 rework: Lich Lab (`lichlab.blv`)

MM9's Lich Lab (reached from Yorwick) converted from its DAT world into a native indoor map (BLV: sectors, portals,
rotating and linear movers, lights, exit volume) on the shared dungeon converter
([`../mm9r_common/dungeon`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_lichlab_claude/README.md)). Status 2026-10-30: geometry, rooms, glass, doors,
lights, exit, 185 decorations, 8 chests, 147 monsters and every MM9 scripted object of the lab as native events.

Update 2026-10-31 (floor holes: the shared converter's `dungeon/floors.py`,
[`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md), Thousand Terrors section): 3
`refinerysolidrusta` grate pieces at 102 (80 LT² each, at (-3930, 7956), (489, 4495) and (489, 4844), by the tables'
feet) are restored; each was a 10-unit-deep hole in the installed floor. With the rule off the build is byte-identical
to before. 12 459 faces. The floor-hole check still lists two `pr_metal` faces at (476, 4500, 2560 and 2642): no kept
neighbour of their model shares an edge, a 10-unit pocket. Rebuilt and rebaked (`bake_slot.sh`); the three scenarios
pass; the walkability audit is unchanged.

## Build and review

```sh
cmake --build build --target mm9_compile_indoor_source -j25          # (inside locks/cmake_build.lock)
python3 level_generation/projects/mm9r_lichlab/analyse.py             # DAT survey: work/analysis.json, work/plan_*.png
python3 level_generation/projects/mm9r_lichlab/convert.py --plan      # rooms only: work/rooms_<storey>.png (45 s)
python3 level_generation/projects/mm9r_lichlab/convert.py             # build, compile, install (90 s)
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_lichlab   # bake
python3 level_generation/projects/mm9r_lichlab/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_lichlab/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_lichlab
python3 level_generation/projects/mm9r_lichlab/make_tour.py v02 [--original]       # 40 eye-level views
./tools/run_game.sh --isolated mm9lich --world mm9 --map lichlab.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position -1311 -4326 1312 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds 160 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_lichlab/review_tour_v02.yml
./tools/run_game.sh --isolated mm9licho --world mm9 --map lichlab.odm --assets "$PWD/output/mm9_rework/assets_original" \
    ... --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_lichlab/review_tour_v02_original.yml
cd level_generation/projects/mm9r_common && python3 -m dungeon.sheet ../mm9r_lichlab/review/v02 ../mm9r_lichlab/review/v02_original
```

Review: [`review/v02_compare.jpg`](review/v02_compare.jpg) (40 views: MM9's bmodel_world map left, the native BLV
right: the entrance, grand stair, lobby, offices, storeroom, library, the ring round the atrium and its windows, the
shooting range, wings, stair towers, the transformer rooms, kitchen, the engine crown, the cross hall over the engine
pit, corridors, labs, throne room, explosion lab, south-west hall, ramp, the engine hall and its pods, the ghost pools
and the column room); lighting [`review/lighting_v01_compare.jpg`](review/lighting_v01_compare.jpg) (MM9 original |
unbaked | baked, 12 views). The in-game map is the engine's BLV line map (the painted MM9 map is no longer listed in the
review root's `worlds/mm9/ui/maps/catalog.yml`).

## Files

- `overrides.yml`: every DAT world model's rule, the archway cuts, glass, seeds, texture substitute; `convert.py`: the
  population and the scripted objects (a `dungeon.Hooks` subclass); `analyse.py`: the phase-A survey;
  `make_scenarios.py`, `make_tour.py`, `scenario_*.yml`, `review_tour_*.yml`, `review/`.
- `props.json`: every prop, chest, barrel and bone pile placement (from the props project's `placements.py`).
- `work/`: `analysis.json` (all DAT objects by kind), `rooms_<storey>.png`, `build_report.json` (numbers, every portal,
  the floor check, the scripted positions), `doors.json`, `lights.json`, `content.json`, `population.json`,
  `walkability.json`, `dropped_faces.json`, `mixed_faces.json`, `runtime/`.

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame: x -9503..7864, y -5284..12452, z
  -1229..3768 fit int16; the transition rows and the start keep their coordinates). Four storeys: basement -256 LT
  (engine hall, ghost pools, column room), ground 0 (cross hall over the engine pit, ring, labs; north corridor 128),
  upper 512 (entrance, lobby, ring round the atrium, wings), top 928 (kitchen, transformer, offices, engine crown).
- 9 878 source polygons (PhysicsBSP and the static world models) -> **12 459 native faces** (3 grate pieces restored, 2026-10-31), 20 472 vertices (245
  polygons triangulated where integer coordinates break planarity); 528 faces with no air in front dropped (between
  brushes, the sky box behind the skylight, the sealed pods).
- **65 rooms** (+ sector 0), sealed (one air component, no leak), median 108 faces, largest 2 181 (the engine hall:
  one open space from the basement floor through the cross hall's bridges to the atrium's crown).
- **145 portal faces**: 66 MM9 UserPortals (every RotatingDoor leaf has its own), 9 from door leaves (RotatingDoor195,
  the peasant doors, the transformer chambers, the four cage fronts), 26 archway cuts (`overrides.yml portals`: corridor
  segments between arch beams, stair feet, the lobby, the entrance hall's arches, the ramp), **44 glass portals** (the
  Lichwindow panes: below). Every portal joins two rooms.
- **94 movers**: 74 rotating (the 66 UserPortal leaves, RotatingDoor195 and the two peasant doors, the 4 switches and
  the engine lever; 69 swing through a second room), 9 MM9 linear Doors (pod 1's lid and glass, the transformers' glass
  doors), 11 sinking plugs (four cage fronts with their glass, three straw targets); 5 of the 94 are the invisible collision shells of the pod glass,
  the transformer doors and the cage windows, and the glass of pod 1, the transformer doors and the cage windows is
  a translucent part of its own (the transformer doors' glass adds two movers; shared converter changes below).
- **417 lights**: MM9's `Light` objects as BLV point lights (radius x 2.56, colour as authored), smallest first while no
  floor point is under more than four; 74 left out. With the cook pot's own fire light no floor point is under more
  than four (`content.json light_coverage`).
- **185 decorations** (181 props, chests, barrels and bone piles from `props.json`; the four cage fires), **9 pads**,
  **8 chests**, **147 actors** (82 drawn untextured in this build: Lich, Power Lich, Lich King, Skeleton Master,
  Dagrell, Oculus, Eye and Flying Icky have no MM9 art yet: humanoids wait for their own route; placeholders as
  expected).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` only for its 66 UserPortals |
| `RotatingDoor` leaves `RotatingDoor128-203` (66, each its own UserPortal), `RotatingDoor0`, `RotatingDoor195`, `peasant door/0` | rotating doors, MM9's swing ([movers](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md)): 90° at 50°/s, open-away, reopen on contact, auto-close after 5 s (the peasant doors 75°/s, sine, 2–2.5 s), a click each |
| `Door` `skeletondoora/0` (transformer chambers' glass doors) | MM9's motion (down 128 / 96); authored hanging open, built shut and starting open (`authored_open`); opened by the switches only |
| `Door` `Enginedoor1` + `Engineglass1` (pod 1) | one mover group, MM9's motion (down 96 at 25); the lich switch lowers it |
| `Door` `Enginedoor2-4`, `Engineglass2-4` (pods 2-4) | static, shut (MM9 has no way to open them) |
| `Switch` `TransformSwitch0-3` | rotating switches (MM9's 90° swing), click events |
| `RotatingDoor1` (lever at the engine) | rotating lever (MM9's 90° swing), toggles on a click (MM9: engine start/finish animation) |
| `RotatingDoor58` | left out: MM9 opens it at start and it never closes (StartOpen, Sticky, no trigger) |
| `DestructableBrush` `DB1/DB2` + `breakwindow1/2`, `RotatingDoor167/168` | the explosion lab's four cage fronts: sinking plugs with doorway portals |
| `DestructableBrush6/16/19` | the shooting range's straw targets: sink when their book's bolts break them |
| `WorldObject*`, `DestructableBrush17/18/20/21`, `MutateWindow0/1`, `Carpet*` | static (windows, rails, carpets) |
| `InvisibleBrush*` | invisible collision (rails, gaps beside doors, the invisible ramps over the engine hall's stair feet) |
| `AIBarrier*`, `AITrk*`, `PromoVol1`, `BlueWater0-3`, `SkyBox0`, `TOD_Sky0` | not built (AI helpers; the pod volume is read by the script; the pools' liquid volumes keep their basins) |
| `Light` (491) | 417 BLV point lights; `DirLight` (36) bake-only spots; `GlowingLight Glow1`, `Lightning0` scripted (below) |
| `Prop`, `TreasureChest`, `Barrel`, `BonePile` | 3D decorations (props project) |
| `Fire` `Fire0` | the cook pot's flames and light; `ExplodeSmoke0-3`: flame decorations shown when the cages break |
| `ExitTrigger0` | MM9 positioned transition volume to Yorwick (`map_transitions.txt` row of this map, review root) |
| `StartPoint0` | start 0, facing into the entrance hall (90 - ry) |
| 12 monster classes, 147 objects | placed actors, MM9 monster rows (`MM9 <Family> A|B|C`), on the floor under them (the Flying Ickies under the ceiling where they hang) |
| `Trigger` (11) | 9 pressure pads (TriggerLich, TriggerExplodeL/R, six bat triggers); TriggerUnlock/0 are relays the transformers' script now does itself |
| `ScriptObject` (8), `Shooter` (9), `Marker` | scripted below; markers and AI rails not built |

## Scripted objects (`worlds/mm9/events/maps/lichlab.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Transmutation Engine**: `lichswitch` (Switch.scr "Engineglass1 toggle"), `Enginedoor1/Engineglass1`, `PromoTrigger` (ILSHealerRoom.scr), `PromoVol1`, `Lightning0`, `Lichengine` (LichEngineProp.scr) | the lich switch (event 200) lowers pod 1; 3 s later the engine strikes (an arc beam down the shaft onto the engine, MM9's projectile sound) and, with the party in PromoVol1's box and the Lich Instructions (key 296), each member who carries an Elixir of Defedation and is a Wizard (MM9's Scholar) or a Necromancer (the classes one promotion from Lich; user decision 2026-10-30) loses the elixir and becomes a Lich (`evt.ApplyLichTransformation`); the first transmutation gives MM9's 63 000 experience and key 299 (journal "Become a Lich" done); 2 s later the pod rises |
| **The elixir**: herb bags `Prop9-15` (Givetake.scr 378), jars `Prop4-7` (Givetake.scr 358), `Prop18` cook pot (ElixirCook.scr), `Prop17` burner (GiveElixir.scr) | the bags (Elixir Ingredients) and jars (a Jar) are world items (`dungeon/pickups.py`), picked up as any ground item; the cook pot (222) turns ingredients into Elixir Fluid; the burner (223) turns fluid and jar into the Elixir of Defedation |
| **Letters**: `Prop16`, `Prop19`, `Prop20` (BookLetter.scr 496, 497, 592) | a click (224-226) shows MM9's text ("The Skeleton Transformer", "Scrap of Diary", "Elixir Instructions") |
| **Skeleton transformers**: `TransformSwitch0-3`, `skeletondoora/0`, `SkeletonTransformer/0` (Converter.scr), `ShooterTransform0-5`, `TriggerUnlock/0`, `MarkerSpawn/0`, `peasant door/0` | a switch (202-205) locks both switches and lowers the chamber's glass door; with it down (4.3 s, its OpenTrigger `create`) a Commoner (9050, Converter.scr p0) appears at the closet's marker (p3), walks to the chamber's centre 2 s later (PeasantTransformee.scr, `evt.MoveActorTo`, arrival event 262/265), cowers (Cower clip, wizardeyeloop.wav) and winces; then the three shooters strike (arc beams) and a Skeleton (9135) stands where he stood (2026-11-06; MM9's TransformCreature removes him only behind an unset `hDummy` and spawns the Skeleton at the marker: the intent is carried); 1 s later the door rises and the switches unlock. A conscript who never arrives is turned after 20 s |
| **Shooting range**: `firebook2-4` (ILSshootingbook.scr), `shootfire1`, `fireball1/2`, `DestructableBrush19/16/6` | a book (206-208) starts its shooter: a fire bolt at its straw target every 1.5 s; ten bolts (50 HP, FireBolt 5) break the target, which sinks, and the book is done |
| **Summoner**: `LichSummoner` (Summoner.scr), `SpawnMgr`, `GhostPool0-3` (SpawnLoc.scr), `TriggerLich` | the pad at the ramp foot (230) wakes it: a Specter (9140) rises from each ghost pool; each time one dies another rises from a random pool, while the summoner lives, up to ten dead (monster-killed hook 95) |
| **Explosion lab**: `ExplodeGhast`, `ExplodeRevenant`, `ExplodeDagrell0/1` (KingKong.scr), `TriggerExplodeL/R`, `ExplodeSmoke0-3` | either pad (231/232) sinks the four cage fronts and lights the fires; the critters come out |
| **Hanging ickies**: `FlyingIcky` x24 (LL_FlyingCreature.scr), six bat triggers | the ickies hang peaceful under the ceiling (groups 60-62) until a wing's pad (233-238) turns them hostile |
| `SkeletonMaster52` (AutoResurrect.Scr) | placed hidden: it waits under the floor for a resurrection nothing in the lab sends |
| `Book0` (book.scr: page-turning animation), `Givetake`-less props | decorations only |

Map variables keep the state (`PodClosed`, `Transmuted`, `SkeletonDoorA`, `firebook2`, `Summoner`, `GhostKills`,
`CagesBroken`...; saved with the map). One-shot timers are armed by a variable (the map's timers run
from load, playbook gotchas).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: lightmap-matched (re-lit 2026-10-31, the user's decision of 2026-10-30: dungeon lighting follows MM9's DAT
lightmaps for brightness and hue; MM9 draws walls as texture x lightmap x1, `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`).**
`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_lichlab.yml`: the 417 BLV lights,
the 74 over the four-per-point cap, the 36 `DirLight`s as spots, the ice glass's `LIGHTDEFS` per polygon at 0.33, 64
samples, 3 bounces, **`direct_scale` 1.65, `bounce_scale` 6, `ambient_scale` 0.655, `sky_scale` 0.05, `max_lighting` 1**;
emitters and glass floors as before (display 0.35 / 0.45). Sector minimum light 20 (unchanged). Passes in
`output/mm9_rework/bakes/lichlab`; the re-light was a `--recompose` through `../mm9r_common/bake_slot.sh` (no Cycles run).
`tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map. Bake again after any
`convert.py` that changes the BLV.

**Method.** `../mm9r_common/relight_fit.py --grid --max 1` (the saved passes composed per zone and room without Blender,
fitted to the zones' mean, B/R, G/R and MM9's map-wide texel quantiles). MM9's lightmaps here are a flat neutral floor of
57/255 (p10 = p50 = 0.224: AmbientLight 60) with bright pools (p90 0.61); the old bake had a higher floor and weaker
lamps (p10 0.33, p90 0.54). The fit lowers the floor (ambient 0.95 -> 0.655, x the sector floor 0.345 = 0.226) and
nearly doubles the lamps (direct 0.9 -> 1.65); the sky term goes to about nothing (MM9's lightmaps hold no sky light).
Zones: `hue_zones.py`, ten k-d boxes (`../mm9r_common/relight_zones.py`).

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`../mm9r_common/hue_vs_lightmaps.py`,
`work/relight/hue_before.txt`, `hue_after.txt`):

| Zone | MM9 luma | before | after | ratio before -> after | B/R MM9 / after | G/R MM9 / after |
| --- | --- | --- | --- | --- | --- | --- |
| z01_low_west_s | 0.335 | 0.388 | 0.315 | 1.16 -> **0.94** | 0.95 / 0.88 | 1.02 / 0.96 |
| z02_low_west_mid | 0.413 | 0.395 | 0.322 | 0.96 -> **0.78** | 1.15 / 0.98 | 1.21 / 1.05 |
| z03_low_west_n | 0.336 | 0.371 | 0.297 | 1.11 -> **0.88** | 0.95 / 0.89 | 1.03 / 0.96 |
| z04_low_east_s | 0.307 | 0.386 | 0.317 | 1.26 -> **1.04** | 0.97 / 0.92 | 1.03 / 1.00 |
| z05_low_east_mid | 0.314 | 0.401 | 0.331 | 1.28 -> **1.05** | 0.94 / 0.87 | 1.01 / 0.95 |
| z06_low_east_n | 0.321 | 0.378 | 0.303 | 1.18 -> **0.94** | 0.97 / 0.89 | 1.03 / 0.96 |
| z07_up_west_s | 0.314 | 0.401 | 0.338 | 1.28 -> **1.07** | 0.97 / 0.90 | 1.04 / 0.98 |
| z08_up_west_n | 0.336 | 0.417 | 0.344 | 1.24 -> **1.02** | 1.08 / 0.94 | 1.13 / 1.01 |
| z09_up_east_s | 0.320 | 0.408 | 0.348 | 1.28 -> **1.09** | 0.96 / 0.89 | 1.03 / 0.98 |
| z10_up_east_n | 0.323 | 0.411 | 0.348 | 1.27 -> **1.08** | 0.98 / 0.91 | 1.04 / 0.99 |

**Still off:** the lamps are warmer than MM9's (B/R 0.87-0.94 against 0.94-1.08; before 0.91-0.95): stronger direct
light brings more of their colour. A blue-tinted floor (`ambient_colour` 0.92 / 1 / 1.1) would match the means but tint
the unlit walls, which MM9 has neutral, so it was not used; the lights' colours themselves (BrightScale) are the place
to fix it, which needs a rebuild and a Cycles bake. The teal pods (z02) stay x0.78 and too neutral: their `LIGHTDEFS`
lights sit in the direct pass with the lamps and cannot be raised alone by a recompose (`texture_lights.scale` 0.33 ->
about 0.5 and a bake would).

**Screen brightness** (the 40 v02 views, `work/relight/views.txt`, centre crop luma): capture 34.4 (information only;
the full-view reference), unbaked 43.2, old bake 33.5, **lightmap bake 29.8 (x0.87)**. Darkest baked views: the east wing
16.6, the storeroom 17.5, the west room 17.8, the west stair tower 18.2: none under luma 12, so no player-light floor.
No real MM9 screenshot of this map exists.

**Props: `model_lighting: true`** (`overrides.yml`; the scene's block: AmbientLight 60, ModelAdd 30). Same bake both
ways (`../mm9r_common/relight_props.py`, `work/relight/model_lighting_props.txt`): relative brightness of the props to
their view, capture 0.97, old path 0.54, **model lighting 0.99**; views with props under x0.6 of their view: **old 14,
model 1** (the old path draws the library's shelves, the throne room, the south-west hall and the labs' furniture near
black and the engine hall's and cross hall's lamps at x4.5). The 74 capped lights do not reach the models. The rebuild
left the BLV byte-identical (the scene gained the block); the three scenarios (chests, doors_exits, scripted) pass.

Sheets (looked at): `review/lighting_v05_compare.jpg`, `review/lighting_v05_p01-p07.jpg` (capture | unbaked | old bake |
lightmap bake with model lighting); `review/lighting_v05_baked` holds the same bake with the old prop path. Close to the
old bake's look, with darker floors between brighter lamps.

**Documented alternative: the capture-matched bake** (installed until 2026-10-31): `work/profile_capture_matched.yml`
(direct 0.9, bounce 6, ambient 0.95, sky 0.75, no ceiling): lightmap ratios 0.96-1.28, screen mean 33.5. To switch back:
copy it over the profile, `model_lighting: false` in `overrides.yml`, `convert.py`, then `--recompose` as above and the
scenarios.

### History: calibration against the full-view capture (2026-10-30)

`../mm9r_common/dungeon/lighting.py` bakes `lichlab.lighting` / `.bake.json` (profile
`tools/lighting/baked_indoors/profiles/mm9_lichlab.yml`: 64 samples, 3 bounces, direct 0.9, bounce 6, ambient 0.95;
passes in `output/mm9_rework/bakes/lichlab`, installed through `review_root`). Bake again after any `convert.py` that
changes the BLV (the game ignores a stale bake).

**There is no mist.** Until 2026-10-30 this map was calibrated against a "white mist" in the cross hall and engine hall
(about 100 of 255) that MM9 does not have: `LICHLAB` sets `EnableFog 0`, `SkyFog 0`, `VFog 0`, and the white was our
outdoor renderer's view fade in the reference shots (`view_distance_scale: 0.4`: far clip 6477 native, fading into the
Enhanced sky from 3562). With `--set video.view_distance=unlimited` the halls measure 34 and show the bronze walls
(`review/mist_probe_farclip_compare.jpg`; [survey](../../../devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md), "Correction").
The true mean of the 40 views is 31.9, not 39.1; 18 of them moved. Reference: `review/reference_fullview/`.

**What the bake holds now (2026-10-30, `review/lighting_v04/`).** The 417 BLV lights; the 74 MM9 lights over the
four-per-point cap; the 36 `DirLight`s as spots (`dirlights: true`: rotation 4.71 aims up, so the teal `DirLight4-7`
light the bridges' undersides and not the pod lamps, 1024 LT from them with radius 700); the teal `LIGHTDEFS` of the ice
glass as one light per polygon, 37 in front of the glass at 0.33 of full strength (`texture_lights`: a light at a pod's
centre never got out); the 5 sky faces and 2 outward panes as emitters.

Removed or lowered because they only chased the mist: `sky_scale` 8 → 0.75; emitter `display` 1.1 → 0.35; glass floor
`display` 1.0 → 0.45. The earlier `ambient_scale` cut (1.8 → 1.35) was right, against the dark rooms, and not enough:
0.95 now, with the bake's new lights.

Mean brightness (centre crop), MM9 full view / before (glass v03) / after:

| View | MM9 | Before | After |
| --- | ---: | ---: | ---: |
| 10 atrium windows | 26.6 | 32.6 | 24.4 |
| 16 ring at the atrium | 50.3 | 77.0 | 48.7 |
| 17 kitchen | 47.1 | 40.3 | 31.4 |
| 18 engine crown | 42.2 | 76.8 | 44.0 |
| 23 cross hall | 33.8 | 41.6 | 31.2 |
| 24 cross hall east | 33.4 | 41.7 | 31.2 |
| 37 engine hall | 33.6 | 38.8 | 29.2 |
| 38 pods | 42.9 | 35.9 | 33.8 |
| all 40 views | 31.9 | 42.8 | 31.6 |

Mean absolute difference over the 40 views: 10.9 before, 3.0 after. Sheets `review/lighting_v04_focus.jpg` (MM9 | before |
after) and `review/lighting_v04_compare.jpg`. Still not matched: the kitchen (-16: its floor and walls are lit more in
MM9; no light in the bake explains it yet); the pods' panels and floor are less green than MM9's (-9), though the teal
is there now; the crown's glass frame reads pale where MM9's is teal; the entrance is 4-8 dark and the shooting range 9
bright. The reference is our renderer with this map's `.lighting`, not footage of MM9.

## Checks

- `scenario_doors_exits.yml` passes: the exit volume beside the start raises ExitTrigger0 (DAT object 1201) to Yorwick;
  RotatingDoor176 (upper) and RotatingDoor157 (ground) stop the party shut, open on their click events, the party
  walks through; the party climbs from the engine hall floor up the stair onto the cross hall's bridge.
- `scenario_chests.yml` passes: all 8 chests open by interact from in front of their models.
- `scenario_scripted.yml` passes: the world items give their items; cook pot and burner make fluid and elixir; a letter
  opens; the pod closes, strikes and rises without key 296 (no change), then with key 296 a Wizard carrying the elixir
  becomes a Lich (Transmuted 1, QBit 90299 set); TransformSwitch0 locks the switches, lowers the chamber door, makes a
  Skeleton and releases it; firebook2's ten bolts sink its target; TriggerLich raises four Specters; TriggerExplodeL
  opens the cages; LobbyBatTrigger1 turns the lobby's ickies hostile.
- Walkability (`work/walkability.json`): 187 steps and 11 flights, all explained: the sides of MM9's free-standing
  stairs (the grand stair, the engine hall's two stairs, the east lab's two, the engine crown's), the lips of the
  stair feet at the north corridor (16 wide, beside the walls), the ghost pools' basins (93-128) and window ledges; 25
  mover notes (the cage plugs and targets sink below the floor, lever recesses); 17 actor notes (Oculi, Eyes and ickies
  float near walls; skeleton masters in narrow aisles). The audit's 3 "cut-off" regions (the cross hall's bridges,
  7.1 M units²) are reached by the engine hall's stairs, whose foot MM9 covers with invisible ramps the audit does not
  follow: the doors scenario walks the party up one. 5 small unreachable ledges: four alcoves along the east lab's
  east wall, 41 above its floor (0.06 M units² each), and the east stair's top step beside the wall (0.03 M).
- Floor check: 2 760 LT² of floor under another room's air: the stair-foot sills of the north corridor (1 264), a
  wall-top ledge in the entrance hall (658), the ramp's foot (432), door sills.
- Compiler unit tests (`openyamm_indoor_source_tests`): 20 cases pass, including the new double-precision plane case.
- Load: 147 actors (82 untextured placeholders), no Lua errors.

## Deviations from MM9 and why

- **Glass** (2026-10-30, [translucent indoor faces](../../../devdocs/INDOOR_TRANSLUCENT_FACES.md); before: clear
  portals with an invisible collision face). MM9 blends its glass at texture alpha × brush `Alpha`; the native map
  draws the same as translucent faces (scene `translucent_faces`, 78 faces in six entries): the pale blue Lichwindow
  (the atrium and observation windows, the transformer and mutation windows, the cages, the transformer doors: brush
  Alpha 0.7, 0.8 or 1) and the blue ice glass of the engine's pods and crown (`yanmirsolidice1`, Alpha 0.5, 0.6, 1),
  two-sided (MM9's panes are often single quads seen from both rooms). A pane between two rooms is still a portal; the
  pane itself is a solid face that blocks sight and missiles as MM9's solid glass does (before, monsters saw and shot
  through the invisible collision face). 11 glass faces with nothing built behind them stay opaque (the void would
  draw black); the 2 outward ones are the bake's window lights. 9 skylight faces have no air in front and are not
  built (as before).
- The pod and transformer doors keep MM9's linear motion; every RotatingDoor and Switch swings as MM9's since
  2026-10-30 (monsters do not open them yet: [movers](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md), "Monsters and doors").
- **The Transmutation Engine works.** In MM9 it never runs: ILSHealerRoom.scr waits for a "Fix" message nothing sends,
  and the per-member keys 433-436 it checks are never given. Here key 296 (the Lich Instructions from the Chasm of the
  Dead) stands for the fix, and carrying one's own elixir stands for the keys, as the instructions describe. The
  experience comes once, with the first transmutation (MM9 would give it every time until someone changed).
- The engine's spin, the pods' glow (`Glow1`) and the sky lightning (`Lightning0`) are an arc beam during the strike;
  the engine model is static.
- The transformers' conscript (a peasant who walks from the closet into the chamber, cowers and turns) is not there:
  the Skeleton appears in the shut chamber; the peasant doors open on a click.
- The hanging ickies wait peaceful instead of hanging animated, and do not fly MM9's marker paths.
- MM9's touch volumes are pressure pads (they fire when the party stands on them).
- `Oculus10` stands inside the east lab's wall in MM9 (a sealed cavity): hidden. `SkeletonMaster52` hidden (above).
- Ambient sounds, the specimen tanks' animated texture (`thjoradtank.spr`: its first frame), the sky box: not built.
- No barrel drinks or bone-pile searches (decorations only), as Anskram Keep.

## Shared converter changes (Lich Lab)

- `rooms.build_voxels`: `seed_exclude` (objects of a seed class outside the built air).
- `rooms.leaf_points`: doorway rectangles of `authored_open` leaves from their shut pose (the transformer doors hang
  over an open gap; their rectangle from the authored pose did not cover it).
- `rooms.glass_portals` + `overrides.yml glass`: see-through glass between rooms (above); portal faces may carry a
  `ring` (the pane's own shape). 2026-10-30: `rooms.Glass` (per texture opacity/tint/two_sided × brush Alpha),
  `glass_backed`, glass faces as `STATIC_glass<k>_<room>` nodes and mover parts `<node>_GLASS<k>`, the scene's
  `translucent_faces` from the compiler's `faces.yml` and the doors (`build.translucent_faces`); `dungeon/lighting.py`
  adds the `LIGHTDEFS` texture lights (one per brush) to the bake.
- `movers.build_movers`: a mover's invisible faces (Invisible.dtx shells round glass) become a second mechanism
  `<node>_INV` with the same motion, flagged invisible (they drew the "invisible" texture before).
- Engine (compiler only): `editor/import/IndoorDerivedGeometry.cpp` builds the derived-geometry planes from a Newell
  normal summed in double precision; the shared float normal put long thin triangles far from the origin (the ramp's
  sides at y 7 900) 0.3 units off their own plane and the compile failed. Test: `tests/IndoorSourceGeometryCompilerTests.cpp`
  "indoor derived data keeps long thin triangles far from the origin planar".

## Open items

- MM9 art for the lab's monsters (Liches, Skeleton Masters, Dagrells, Oculi, Eyes, ickies): creature work.
- The engine's 2 181-face sector: MM9's engine hall is one open space; a split would need horizontal portals.
- The ghost pools' basins draw MM9's coal texture on their faces; no liquid surface (Temple of Honk's water face is the
  option if wanted).
- A density and pack pass (PLAN.md: later). The Lich promotion's class rule is settled (2026-10-30): any member one promotion from Lich (Wizard, Necromancer).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:57:20 (convert.py from the current shared converter, end 15:02:40): 46 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 12405 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
Blocker probes: 8 walks into helper brushes resting on the floor stop short of them, 8 identical before and after (their sides still block).
