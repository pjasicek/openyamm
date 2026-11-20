# MM9 rework: Beethoven (`beethoven.blv`)

MM9's Beethoven, the sewers under Sturmford City, converted from its DAT world into a native indoor map (BLV: sectors,
portals, rotating and linear movers, ladders, lights, exit volumes) on the shared dungeon converter
([`../mm9r_common/dungeon`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_beethoven_claude/README.md)). Status 2026-10-30: geometry, rooms, swinging doors,
six ladders, lights, three exits, 111 decorations, 11 chests, 84 monsters, MM9's scripts (coffins and mummies, the great
door, Ludwig's manuscript, the floating bottle) and baked lighting. No textures x4: that is the project's last step.

## Build and review

```sh
python3 level_generation/projects/mm9r_beethoven/analyse.py           # DAT survey: work/analysis*.json
python3 level_generation/projects/mm9r_beethoven/convert.py --plan    # rooms only: work/rooms_<storey>.png (90 s)
python3 level_generation/projects/mm9r_beethoven/convert.py           # build, compile, install (3 min)
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_beethoven/bake.py   # bake
python3 level_generation/projects/mm9r_beethoven/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_beethoven/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_beethoven
python3 level_generation/projects/mm9r_beethoven/make_tour.py v04 [--original]     # 78 eye-level views
python3 level_generation/projects/mm9r_beethoven/make_tour.py lighting_v05 [--original]   # 23 lighting views
level_generation/projects/mm9r_beethoven/work/relight/run_lighting.sh lighting_v05 baked   # also _original original,
python3 level_generation/projects/mm9r_beethoven/work/relight/pages.py                     # _unbaked unbaked
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_beethoven
./tools/run_game.sh --isolated bthv --world mm9 --map beethoven.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position -9805 543 533 --yaw-radians 0 --pitch-degrees 0 --warmup 3 --seconds 270 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_beethoven/review_tour_v04.yml
./tools/run_game.sh --isolated bthvo --world mm9 --map beethoven.odm --assets "$PWD/output/mm9_rework/assets_original" \
    ... --set video.view_distance=unlimited --set debug.screenshot_tour_path=.../review_tour_v04_original.yml
python3 level_generation/projects/mm9r_beethoven/pages.py v04 v04_original         # review/pages_v04_NN.jpg
```

Helpers: `section.py` (vertical sections of the DAT, `work/section_*.png`), `diagnose_cut.py` (why a cut does not separate
two rooms), `calib.py` (brightness and hue of a tour against MM9), `bake.py` (the bake), `work/relight/` (the re-light's
fit, measurements and lighting tour runner).

Review: [`review/v04_compare.jpg`](review/v04_compare.jpg) and `review/pages_v04_01-07.jpg` (78 eye-level views: every
room both ways, the arrivals, shaft, baths, well, great door and manuscript; MM9's bmodel_world map left, the native BLV
right), `review/swing_sheet.jpg` (doors open), `review/bottle_sheet.jpg`. Every view inspected: no holes, no missing
walls; geometry, textures and props match MM9 apart from the Deviations. The original's green checker in the hub, its dark
blobs at corridor ends and its missing water edges are the old map's, not MM9's.

## Files

- `overrides.yml`: every DAT world model's rule, 25 archway cuts, 6 ladders, exits, seed exclusions; `convert.py`: the
  polygon edits (water), the population and the scripted objects (a `dungeon.Hooks` subclass).
- `props.json`: 103 placements (from the props project's `placements.py`).
- `make_scenarios.py`, `scenario_*.yml`, `make_tour.py`, `review_tour_*.yml`, `review/`.
- `source/`, `work/`: `build_report.json`, `doors.json`, `lights.json`, `content.json`, `population.json`,
  `walkability.json`, `dropped_faces.json`, `mixed_faces.json`, `rooms_<storey>.png`, `runtime/`.
- `tools/lighting/baked_indoors/profiles/mm9_beethoven.yml`: the bake.

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) × 2.56`, no offset (the old map's frame: x -18 186..5 524, y -30 966..18 831, z -3 891..1 679) |
| Storeys | sewers (bed 0, walkways 32, planks 208), catacombs and baths (floor -736, -672), lower sewers (bed -1216, walkways -1200), maze hall (floor -1392) |
| Geometry | 7 737 polygons (PhysicsBSP + static world models) → 6 637 merged → **7 317 native faces** (42 of them portals), 12 802 vertices; 135 polygons triangulated; 524 faces without air dropped (between brushes, grate shells, the invisible sides of the rung plates) |
| Air | sealed, no leak; 5.15 M voxels of 16 LT |
| Rooms | **39 rooms + sector 0**, median 103 faces, largest 1 080 (the baths) |
| Portals | **42**: 15 MM9 UserPortals (the double doors, the sewer door, the great door), 25 archway cuts, 2 horizontal (`BHportal`, `Ladder1Hole`); every portal joins two rooms |
| Floor check | 12 953 LT² on paper: all of it one 16 LT line of samples lying exactly in a cut's voxel slice (`-3304`, `904`, ...), none a floor really under another room |
| Movers | **34**: 30 rotating (13 double doors, 26 leaves; `RotatingDoor18`; `HedgeDoor1-3`, MM9's own hinge, angle, speed, auto-close and open-away), 4 linear (`SDoor11/12`, `Lever5/6`) |
| Ladders | **6** (`Ladder0/1/2/4/7/8`) |
| Lights | 115 `Light` → **112 BLV lights** (`Light40`, `Light9`, `Light136` over four per floor point); those 3 and the 21 `DirLight`s (spots) are bake-only; at most 4 per floor point |
| Decorations | **111**: 103 from `props.json`, 8 rubble heaps (hidden until a coffin breaks) |
| Chests | **11**: 5 `Chest1`, 6 coffins (`CoffinRaised`): MM9's loot records from the shared item sources |
| Actors | **84**: 37 Bone Thrashers, 16 Lobbers, 11 Rotters (8 hidden Petrified Mummies among them), 10 Skeletons, 8 Airborne Ickies, 2 Lobber Pods |
| Pads | 12: 8 coffin triggers, 4 bottle triggers |
| Translucent faces | 216 (bake: grate and rung textures' mean alpha 0.19–0.44): 153 web faces (0.7 × texture alpha), 63 rungs, grates and chain at texture alpha |
| Water | 73 slime and 31 water faces drawn by the liquid shader (`slime_mm9`, `water_mm9`) |
| Exits | `ExitS` (683), `ExitW` (684), `ExitE` (691) to Sturmford City; arrivals `SewerS/W/E` and `Sewergrate` |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` only for its UserPortals |
| `LeftDoor/RightDoor2,3,5,9,10,12,14,15,16,18,19,21,22` | MM9's own swing (90°, 40–60°/s, away from the opener, closing after 3 s, reversing off bodies); one click event a pair |
| `RotatingDoor18` | the door before ExitE: swing, auto-close 5 s |
| `HedgeDoor1-3` | the maze's stone doors (they look like its walls): swing, a click each |
| `Door` `SDoor11/12` | the great door to the maze: halves part 130 up and down at 50, for good |
| `Door` `Lever5/6` | the two levers beside it (8 down); either opens the door |
| `WaterTop1`, `WaterTop10` | dropped: rebuilt as the channel beds raised to the surface (below) |
| `WorldObject10/11` + `12/13` | the two shallow pools' surface and invisible floor (as MM9) |
| `WorldObject6`, `InvisibleBrush*` | invisible collision (the lake's floor, the firethrough rails) |
| `WorldObject14-70` (webs), `Grates*`, `WorldObject0,1,5,7,8,20` (rungs), `WorldObject32` (chain) | translucent faces (Translucent surfaces at texture alpha × brush `Alpha`) |
| `WorldObject2/3` | the bars and grate of the tunnel from the cavern to the lower sewers |
| `frigidarium water`, `Caldarium water`, `BlueWater1/2/4/5` | water surfaces: the top of each volume, non-solid; the party wades |
| `GrandEntrance Water` | the flooded cavern's surface as a solid face (Deviations) |
| `AIBarrier*`, `PortalZone0`, `AIRail`, `AmbientSound`, `OutsideDef`, `Marker*` | not built (AI helpers, sound: later pass; the markers are in the bottle's path) |
| `Light` (115), `DirLight` (21) | above |
| `Prop`, `WallTorch`, `CandleProp`, `BonePile`, `DestructableProp`, `WellMMIX` | 3D decorations |
| `TreasureChest` | chests (`Treasurechest<k>` anchored `Chest<k>`: names differ only by case) |
| monster classes + `LobberPodA/B` | placed actors on the floor under them; Airborne Ickies at their height; Lobbers on the floor (their model grows upward) |
| `Skeleton4` | MM9 stores it in the rock over the maze and drops it with MoveToFloor: on the maze floor below |
| `Ladder*` | ladders, below |
| `ExitTrigger`, `StartPoint` | MM9 positioned transition volumes; start points on the floor |

## Scripted objects (`worlds/mm9/events/maps/beethoven.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **The bottle**: `BottleNW/NE/SW/SE` (BottleFollow.scr, ListTraverseNONAI.inc), `TriggerBottle*`, `Marker*`, `MarkerLower*` | on arrival at a start (position at load, or that start's pad, event 170 + k) the start's bottle bobs six seconds, drifts along the channels to the hub at 40 LT/s, then along `MarkerLower0-8` under the catacombs to the manuscript, and starts again; the other three never appear. One looping model (`engine/models/mm9_bottlefloat.glb`, `evt.SpawnWorldModel`) |
| **Ludwig's manuscript**: `Manuscript` (Ludwigsmanuscript.scr) | a world item (`dungeon/pickups.py`, item 248), floating flat on the lower sewers' slime (`overrides.yml pickups`: MM9 sank it 24 units under the 0.8-opacity surface, where it could hardly be seen; 2026-11-09), hidden with key 16 or 110; its pickup (event 90) gives key 16 if the party has spoken to Ludwig (key 14), else key 110, and a quest sound |
| **The coffins**: `CoffinRaised3-9,15` (CoffinRaise.scr), `PetrifiedMummy0-7` (CoffinMummy.scr), `Trigger0-7` | a pad round each coffin (150 + k): MM9's stone groan; 2 s later (the lid's `open` clip) the coffin breaks into rubble and its mummy, hidden until then (group 80 + k), stands hostile. Saved in `Coffin<k>` |
| **The great door**: `Lever6`, `SDoor11` (`OpenTriggerTarget`, `lock`), `Lever5` (double door of `Lever6`) | either lever (91): both levers go down, both halves part, stays open (`GreatDoor`) |
| `TreasureChest0/1` (PropAnim.scr `ns`) | no effect (a no-op anim name) |

## MM9 visual properties ([list](../../../devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md))

| Property (count in the DAT) | Here |
| --- | --- |
| Translucent surfaces (291) | webs, rungs, grates, chain: 216 translucent faces; water: liquid shader |
| Brush `Alpha` < 1 (58: 54 webs at 0.7, 4 water brushes at 0.8) | webs `opacity` 0.7; water opaque (shader) |
| `.spr` surfaces (153: `slime`, `water125`) | liquid shader |
| Surface `Pan` (16, `WaterTop`) | the shader's waves; no scroll of its own |
| `LIGHTDEFS` (0), `Transparent` props (0), fog (0), `GlowingLight` (0), skymarker (0) | nothing to carry |
| `Chromakey` props (1, the hanging bowl) | glTF cut-out |
| Prop `Scale` (19: coffins 1.2, bowl 1.5, bottles 1.3) | a decoration row per scale |
| `DirLight` (21) | bake-only lights (their FOV 210 is omnidirectional against a wall), except `Light54`, a 90-degree spot up out of the well, left out |
| Binary alpha grates | translucent faces at texture alpha; a BLV face only discards alpha 0, soft edges need the blend |

## Water

MM9: `WaterTop1/10` are one quad over each storey at Alpha 0.8, drawn `slime.spr`, panning; `slime_0000` beds under them. The
native surface is each bed polygon raised to the surface (12, -1191) and grown 26 LT up the ramps either side, so it
stops at the channels' walls; bed strips narrower than 24 LT draw the water themselves (no air above them for a surface). Slime and water go to the liquid
shader (`slime_mm9`, `water_mm9`, `engine/liquids/liquids.yml` of the review root, this world only, `depth: shallow`,
`convert.install_liquids`): animated, rippling and reflecting where MM9 animates and pans a texture; a gain and a
replacement. Move the two entries to `assets_dev` when the map is accepted. The shader is opaque; MM9's alpha 0.7–0.8 over
a 12 LT bed reads the same.

2026-10-31 audit (shared liquid helper `../mm9r_common/liquids.py`, not used here): the 71 `slime_0000` faces
(`SLIM423FQX`) are the channels' beds under the surfaces and stay bitmaps; the 63 `water125_0000` faces (`WATENZD35K`)
are invisible volume faces. Nothing to change.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the scene hook now also calls the shared helper. The sewers' slime quads
  (`WaterTop1/10`: Alpha 0.8 x slime.spr (no alpha), `lqslmo80`, 70 faces) and the baths' water125 tops (0.7 x
  water125.spr 0.25 = 0.17, `lqw125o17`, 6 faces; `WorldObject10/11` 0.8 x 0.25 = 0.2, `lqw125o20`) are see-through
  over their beds; the `slime_0000` and water125 beds, `GrandEntrance Water` (no floor under it) and the opaque
  PhysicsBSP faces keep `slime_mm9`/`water_mm9`. Sheets `review/liquid/see_through_p*.jpg`.

## Ladders

Real ladders since the rotating-movers work landed (`overrides.yml ladders`):

- `Ladder4` (walkway → planks), `Ladder2` (planks → `ExitS`), `Ladder8`, `Ladder7` (the same at the west arrival): against
  a wall, as designed. `exits: bottom_lt 340` lets a climber meet the exit volume on the way up.
- `Ladder0` (the shaft under the hub) and `Ladder1` (the hole from the catacombs to the lower sewers) stand in holes: no
  floor in front of the rungs. `convert.py LADDER_LIPS` gives them `reach` 300 and a `top` above the lip: a party on
  the lip, facing the rungs, takes the ladder with forward and drifts to them while it rises a little; back climbs
  down. The party has to jump onto the shaft's rim (36 LT), as in MM9.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: lightmap-matched (re-lit 2026-10-30, the user's decision: dungeon lighting follows MM9's DAT lightmaps for
brightness as well as hue; dark rooms stay dark so Torch Light matters).** `bake.py` (the shared
`../mm9r_common/dungeon/lighting.py`, run through `../mm9r_common/bake_slot.sh`) with
`tools/lighting/baked_indoors/profiles/mm9_beethoven.yml`: 64 samples, 3 bounces, **`direct_scale` 0.7, `bounce_scale` 6,
`ambient_scale` 0.88, `max_lighting` 1** (MM9 clips at x1), **`dirlights: true`**; one 4096 × 2838 page, 11.6 M texels,
5 145 charts, a 22 MB sidecar, about 7 min of Cycles; passes in `output/mm9_rework/bakes/beethoven`. From the 112 BLV
lights and 24 bake-only lights: the 3 over the four-per-point cap (`Light136`, the octagon's great brazier, at 0.45) and
MM9's 21 `DirLight`s as the spots MM9 baked them with (aim from `Rotation`, FOV 210 / 90, the preprocessor's cone term;
`bake.py` drops the plain point-light copies `convert.py` lists among `work/lights.json`'s capped lights; `Light54`, the
well's upward spot, is now in). No `LIGHTDEFS`, no sky, no emitters. 224 mover faces are lightmapped.
**Sector minimum light 31** (`overrides.yml` `map.ambient`, was 20; the rebuild changed only the 39 sectors' light level,
the three scenarios pass): the engine subtracts the frame ambient of level 20 (0.345) from a decoration's baked room light,
which in a dark bake would draw decorations far from BLV lights black (Inventa Storca's tables). The bake's floor is
`ambient_scale` × 0.18 at level 31 (0.16, the neutral floor MM9's own lightmaps show). `tools/lighting/stale_bakes.py
--assets output/mm9_rework/assets_dev --check` does not list the map. Bake again after any `convert.py` that changes the BLV.

**Method.** `work/relight/fit.py` reads the saved Cycles passes and composes them per zone (`hue_zones.py`, ten boxes) for
any scales, without Blender; `--grid` searches (direct, ambient) for the least squared log luminance and hue error over
the zones. Fitting each zone alone gave the same ambient everywhere (MM9 has a neutral floor of about 0.16) and a direct
scale of 0.35 in the sewers against 0.8–1.9 below: the sewers' 20 DirLights, baked as omnidirectional point lights,
were too strong. As spots they lit the sewers about 30 % less, and the installed scales are the grid's optimum for that
bake (no recompose needed).

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`../mm9r_common/hue_vs_lightmaps.py`,
`work/relight/hue_after.txt`, `ratio_after.txt`; before: `hue_before.txt`):

| Zone | MM9 luma | old bake | new bake | ratio old → new | B/R MM9 / new | G/R MM9 / new |
| --- | --- | --- | --- | --- | --- | --- |
| sewers | 0.218 | 1.044 | 0.231 | 4.79 → **1.06** | 0.86 / 0.81 | 0.96 / 0.99 |
| sewers, west arm | 0.181 | 0.981 | 0.213 | 5.41 → **1.17** | 0.92 / 0.86 | 0.97 / 0.99 |
| south arrival | 0.232 | – | 0.287 | → **1.24** | 0.85 / 0.74 | 0.97 / 1.00 |
| catacombs | 0.215 | 0.938 | 0.209 | 4.35 → **0.97** | 1.60 / 1.49 | 1.28 / 1.31 |
| baths | 0.212 | 0.908 | 0.195 | 4.29 → **0.92** | 1.78 / 1.46 | 1.36 / 1.28 |
| lower sewers (green) | 0.224 | 0.882 | 0.183 | 3.93 → **0.82** | 1.04 / 1.01 | 1.43 / 1.16 |
| lower storey, east | 0.182 | – | 0.167 | → **0.92** | 1.04 / 1.01 | 1.15 / 1.06 |
| south corridors | 0.225 | – | 0.234 | → **1.04** | 1.98 / 1.95 | 1.45 / 1.56 |
| maze hall | 0.217 | 0.960 | 0.222 | 4.42 → **1.02** | 1.76 / 1.66 | 1.36 / 1.39 |
| flooded cavern | 0.197 | – | 0.214 | → **1.09** | 1.57 / 1.64 | 1.25 / 1.43 |

Hue: the catacombs, maze hall, corridors and cavern match (hue_vs_lightmaps "matches", B/R within 0.1); the baths are a
little less blue (B/R 1.46 against 1.78), the sewers a little warmer (0.81 against 0.86). **The lower sewers stay too
neutral and a little dark** (G/R 1.16 against 1.43, x0.82): their six green lights (40, 208, 53) are weaker against the
neutral floor than in MM9, and the global scales cannot raise one zone; a map-local bake-only boost of those lights
(Inventa Storca's cave lights) is the next step if wanted. The south arrival's tunnel is x1.24 (its torch and DirLight
sit close).

**Screen brightness** (lighting tour `lighting_v05`, 23 views: every arrival and every zone; centre crop luma,
`work/relight/views.py`, `work/relight/views.txt`): capture 94.4, unbaked 30.4, old bake 79.0, **new bake 21.5**
(x0.23 of the capture; Verhoffin Ruins and Klusos House came out x0.42, Beethoven's lightmaps are darker). Per view
13–38: the well (38) and the great door (38) brightest, the catacomb corridor r03 (13) and the lower sewers (14–17)
darkest. The south arrival measures 27, RGB (27, 28, 15), against the real MM9 frame's 6.8, RGB (3, 9, 0)
(`devdocs/mm9_rework/overnight/mm9_real_beethoven_start_youtube.png`, same crop). That frame's place is not certain: it
looks up a dark earthen-looking slope, not the vaulted tunnel of any of the four starts (`SewerS` and `SewerW` on the
planks facing east, `SewerE` facing west at the door, `Sewergrate` facing north in the channel); it is a YouTube capture
whose blacks are crushed (blue 0 everywhere), so it says "nearly black, green", which the new bake is, not a number.

Sheets (looked at): `review/lighting_v05_compare.jpg` and `review/lighting_v05_p01-p04.jpg` (MM9 capture | unbaked |
old bake | lightmap bake, 6 views a page). The rooms read as MM9's lightmaps say: blue catacombs, baths and maze hall,
green-lit lower sewers, the sewers warm-olive and dim between their torches. **Decorations** are not darker than the walls
round them (the pots in r02 and r17, the coffin slab in r17 as dark as their walls; the well brighter, lit by its BLV
lights). **Water**: the baths' water is drawn brighter than its room (the liquid shader takes the sector ambient and its
own tint, not the lightmap), the sewers' slime reads as dark olive water with reflections.

**Documented alternative: the capture-matched bake** (the installed one until 2026-10-30): `work/profile_capture_matched.yml`
(direct 1.5, bounce 6, ambient 2.4, no ceiling, no `dirlights`, the DirLights as point lights), over sector minimum light
20. Mean of the 78 v04 views (`calib.py`, `work/calib_v04.txt`): MM9 capture 86.6, baked 74.5; 23 lighting views 79.0;
lightmap ratios 3.9–5.4 and hue too neutral. Its sidecar is kept in `output/mm9_rework/bakes/beethoven_capture_matched/`. The 78-view review `review/v04_compare.jpg` and
`pages_v04_*` were taken with it.
To switch back: `ambient: 20` in overrides.yml and `convert.py`, the profile copied over the installed one, and a full
bake with `lighting.py` (not `bake.py`).

## Checks

- `scenario_doors_exits.yml` passes: Door3 stops the party shut, its click swings both leaves, the party walks through, the
  leaves shut themselves after MM9's 3 s; Ladder4 from the walkway to the planks; Ladder2 and Ladder7 up the manholes
  into `ExitS` (683) and `ExitW` (684); `RotatingDoor18` stops the party, opens, `ExitE` (691) lies behind; the party
  wades past the shaft's wall and up the sill into the catacombs; Ladder0 up the whole shaft to its lip, taken again
  from the lip; Ladder1 from the lower sewers to the catacombs.
- `scenario_chests.yml` passes: all 11 chests open by interact from in front of their models.
- `scenario_scripted.yml` passes: Trigger0 groans, 2 s later the mummy is visible and hostile and the coffin rubble; the
  great door parts and stays; the manuscript clicked between the bars of its grate gives item 10248 and key 110, a
  second click nothing; the bottle's start is taken once.
- The bottle: `review/bottle_sheet.jpg` (it floats and turns at the start, then drifts off down the channel).
- Doors: `review/swing_sheet.jpg` (temporary script opening them): hinges on the outer edges, 90 degrees, doorways
  clear; the other leaves shut by their timers before the shot.
- Walkability (`work/walkability.json`): 26 steps, all MM9's: the baths' terraces (16 LT, 41) and furniture (62-63), the
  cavern's sills (41, the wading floor to the corridors), the shaft's rim (78-102: jump, as MM9). 0 flights. "Unreachable"
  regions: every region reads unreachable because the audit's start is the south arrival's planks, a ladder away from
  everything. The catacombs (76 M units²), the lower sewers (24 M) and the sewers are ladder routes
  (`scenario_doors_exits` walks them); the Caldarium's dais (0.36 M) stands on two 41 risers, 1 over the audit's step,
  and a Skeleton walks up and down them. 5 ledges of 0.05-0.24 M (seat steps round the maze hall's
  pools, 43-118 above their floors), no route needs them. The pit is the wading floor. 1 mover note (the lever's recess),
  6 actor notes (Lobbers and Pods at channel edges, as MM9).
- **The catacombs and the south half (corridors, maze hall: 134 M) are really cut for monsters, as in MM9.** The only link
  is the beam across the tall room between Door21 and Door22 (x -6226..-6144, 82 wide): a gap at y -5816..-5740, 76 wide
  and 1 229 deep, which is in MM9's DAT. Probes in `work/reach/` (`make_probe.py`, `run_probes.sh`; Bone Thrasher, Skeleton
  and Rotter, both ways, in and out of sight): monsters stop at the edge (y -5678, y -5878) and do not fall, where the
  plain-floor controls reach the party. The engine's ledge guard stops them (no ground actor walks a drop over 100; the
  Chasm's slots are 82 deep). The party walks over at floor height both ways. MM9's own `AIRail` graph has the same four
  components as the audit's four big regions (rails on the matching region: 228/229, 137/139, 26/34, 34/34), with no
  rail link over the gap, so the map keeps it. Monsters on the beam still reach across the gap: melee reach is about 360.
- Floor check: Numbers above.
- Load: no Lua errors, 84 actors; 58 draw untextured (open items).
- Compiler tests (`openyamm_indoor_source_tests`): 201 of 202 assertions; the failing case is `floor portal`, new from the
  rotating-movers work, not this map.
- Sealed air, every world model ruled, every portal joins two rooms, at most 4 lights per floor point.
- Shared converter: `mm9r_lichlab/convert.py --plan` runs unchanged after `edit_polygons`.

## Deviations from MM9 and why

- **The Grand Entrance cannot be swum.** MM9 floods the cavern under the hub from -1152 to -784; Ladder0 ends under
  the surface and the party swims under the shaft's walls and out to the corridors' sills (-768). No swimming yet
  (PLAN.md): the surface is a solid face the party wades on, and the shaft's walls, which hang to -830, stop at -696 so
  the party passes under them (`convert.py SHAFT_BOX`: a geometry edit, the only one in the map). The cavern's floor,
  the tunnel, its grate and bars are built but out of reach, as in MM9 (the grate stops swimmers too). Revert both
  when diving lands.
- **Double doors** open by the party only; 13 pairs and the hedge doors are `AITriggerable` in MM9 (monsters opening
  doors: STATUS.md queue).
- **The coffins' animation.** Decorations do not play clips: no rising lid, the coffin breaks after the 2 s the lid took;
  the mummies do not play `wakeup2` (no art yet), they appear standing.
- **The bottle** drifts 8 LT above MM9's markers (MM9's water is translucent, the shader's opaque) and turns only while it
  bobs, as in MM9. It does not survive a save as such: the load handler starts it again at a start's position only.
- **Water** is the liquid shader, not `slime.spr` (above). `Current` and `Viscosity` of the volumes are not carried.
- **No ambient sound** (193 `AmbientSound`): a later pass for all maps. MM9's door and lever sounds: the map's.
- No barrel or bone-pile searches (decorations only), as Anskram Keep. Monsters carry no MM9 treasure overrides.
- `WellMMIX0` is a decoration: no MM9 script names the class.
- MM9 touch volumes are pressure pads (they fire when the party stands on them); a pad does not fire for a party that
  arrives on it, so arrival at a start is checked by position at load.

## Rotating objects

All 30 `RotatingDoor`s are real rotating movers (`motion: rotate`, MM9's `RotationPoint`, `RotationAngles`, `Speed`,
`CloseWaitTime`, `OpenAway`, `ReopenOnContact`). Swing checked in `review/swing_sheet.jpg`: leaves hinge at the outer
edges of their frames and clear the doorway; the double doors shut themselves after MM9's 3 s; a door reverses off a
party in its way (`scenario_doors_exits`: the party has to clear the swing). No levers rotate here: `Lever5/6` are linear
`Door`s in the DAT.

## Shared converter changes (Beethoven)

- `build.Hooks.edit_polygons(build, polygons)`: a map's edits of the merged polygons before voxels and rooms (default: none).
  `mm9r_lichlab/convert.py --plan` still runs unchanged (65 rooms, no leak, no failing portal).

## Open items

- Art for the map's monsters: Bone Thrashers, Skeletons and Rotters (58 actors) draw untextured until the humanoid batch;
  Lobbers, Pods and Ickies have their models.
- Diving (the Grand Entrance's swim, the tunnel).
- Move the two liquid entries to `assets_dev` with the map. Textures x4, last.
- A density and pack pass (PLAN.md: later).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:11:19 (convert.py from the current shared converter, end 15:14:07): 39 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 7278 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
