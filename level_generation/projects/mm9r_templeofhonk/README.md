# MM9 rework: Temple of Honk (`templeofhonk.blv`)

MM9's Temple of Honk (reached from Guberland) converted from its DAT world into a native indoor map (BLV: sectors,
portals, linear movers, lights, exit volume) on the shared dungeon converter
([`../mm9r_common/dungeon/`](../mm9r_common/dungeon/), route and gates in
[`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). The first map built on the package after
the Anskram Keep pilot. Built into the isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written
only by the props project (models and the MM9 world's decoration rows).

Status 2026-10-30: built and reviewed: geometry, 22 rooms with portals, 13 rotating double doors, the HONK puzzle's 9
movers and secret door, 130 lights, the exit, 154 decorations (32 new props), 5 chests, 18 Honks, MM9's scripts (the
quest door, the accountant's key, the HONK buttons and treasury, the Golden Honk, Honk hostility) and baked lighting.
Honk creature art does not exist yet: the 18 Honks are untextured placeholders.

Update 2026-10-31 (floor holes: the shared converter's `dungeon/floors.py`,
[`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md), Thousand Terrors section): 4 `honkfloor4`
floor tiles (3 at 515, 1 at 1129) that the voxel pass dropped are restored beside their kept neighbour tiles; each was a
21-unit-deep hole in the installed floor. 5 789 faces, 326 dropped. Rebuilt and rebaked (`bake_slot.sh`); the four
scenarios pass; the walkability audit is unchanged.

## Build and review

```sh
python3 level_generation/projects/mm9r_common/dungeon/survey.py TEMPLEOFHONK.dat   # what the DAT holds
# The props (once, or after a model change): ../../props/mm9_templeofhonk_claude/README.md
python3 level_generation/projects/mm9r_common/review_root.py                       # link new models and rows
python3 level_generation/projects/mm9r_templeofhonk/convert.py --plan              # rooms: work/rooms*.png (13 s)
python3 level_generation/projects/mm9r_templeofhonk/convert.py                     # build, compile, install (20 s)
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_templeofhonk
python3 level_generation/projects/mm9r_templeofhonk/make_scenarios.py
for s in doors_exits chests scripted hostility swim; do ./build/game/openyamm \
    --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario \
    level_generation/projects/mm9r_templeofhonk/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_templeofhonk/make_tour.py v01 --original     # 30 views of the old map
python3 level_generation/projects/mm9r_templeofhonk/make_tour.py v02               # the same views of the BLV
#   (review_tour_v02_unbaked.yml / _baked3.yml: the v02 shots into review/v02_unbaked, review/v02_baked3)
./tools/run_game.sh --isolated honk --world mm9 --map templeofhonk.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position -3011 7654 -521 --yaw-radians -1.5708 --pitch-degrees 0 --warmup 3 --seconds 170 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_templeofhonk/review_tour_v02_baked3.yml
#   unbaked: the same with review_tour_v02_unbaked.yml and --set video.lightmaps=false
./tools/run_game.sh --isolated honkorig --world mm9 --map templeofhonk.odm \
    --assets "$PWD/output/mm9_rework/assets_original" ... review_tour_v01_original.yml
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_templeofhonk  # bake
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v02_baked3 <project>/review/v01_original
# The re-light (2026-10-31): fit, recompose, measure, lighting tour, sheet
python3 level_generation/projects/mm9r_common/relight_fit.py level_generation/projects/mm9r_templeofhonk --grid --max 1
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_templeofhonk --recompose
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_templeofhonk
for m in original unbaked baked; do python3 level_generation/projects/mm9r_common/relight_tour.py \
    level_generation/projects/mm9r_templeofhonk level_generation/projects/mm9r_templeofhonk/review_tour_v02.yml lighting_v03 $m; done
python3 level_generation/projects/mm9r_common/relight_views.py level_generation/projects/mm9r_templeofhonk lighting_v03 \
    --old lighting_v02_after
```

## Files

- `convert.py`: the map's hooks on the shared converter (population, actors, the map Lua, the pool's water face).
- `overrides.yml`: the `map` settings and every DAT world model's rule, the 9 archway cuts, texture substitutes.
- `props.json`: 154 placements (props project `../../props/mm9_templeofhonk_claude/`, each fitted against the old
  map's baked BModel: median 0.50, worst 0.92 units).
- `make_scenarios.py`, `scenario_{doors_exits,chests,scripted,hostility,swim}.yml`, `make_tour.py`, `review_tour_v0*.yml`,
  `review/`.
- `source/` (the indoor source package), `work/` (`build_report.json` with numbers, portals, transitions, starts and
  the floor check; `doors.json`, `lights.json`, `content.json`, `population.json`, `walkability.json`,
  `dropped_faces.json`, `mixed_faces.json`, `rooms*.png`, `runtime/`).

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) × 2.56`, no offset (the old map's frame; int16 fits) |
| Geometry | 5 527 DAT polygons (PhysicsBSP + 26 static world models) → 5 348 merged → **5 789 native faces** (116 polygons triangulated), 10 062 vertices; 326 faces with no air in front dropped (4 floor tiles restored, 2026-10-31) (carpet undersides, the sealed skylight tops, faces between brushes) |
| Air | one sealed component (367 803 voxels of 16 LT), no leak |
| Rooms | **22 rooms + sector 0** (sector ambient 14), median 170 faces, largest 1 056 (the entrance hall with its amphitheatre) |
| Portals | **24 portal faces**: 13 MM9 UserPortals (double doors), 1 from the secret door's slab, 10 from 9 archway cuts; every portal joins two rooms |
| Floor check | 628 LT² of floor under another room's air (door sills); `split_minor_rooms` on |
| Movers | **35**: 13 double doors (`rotate`, one mover per leaf: 26 leaves, MM9's swing, 90° at 70°/s, sine, open away, reopen on contact, auto-close after 7 s), 4 HONK buttons (MM9 `Door`, 4 LT in), 4 corner stones (MM9 `Door`, 48 LT up at 15 LT/s), the secret door (`slide`) |
| Lights | MM9's 133 `Light` objects → **130 BLV lights** (dropped: the 1 280–1 792 fill lights `Light6`, `Light33`, `Light34`, each over a floor point already under four); at most 4 per floor point |
| Decorations | **154**: 46 braziers, 3 hanging bowls, 11 wall torches, 22 tapestries, benches, bookcases, desks, chairs, the harp, the key, the Golden Honk, 5 chests (32 new models, 8 reused rows) |
| Chests | **5** (`CollectionChest` chest3, 4 × chest1/chest2): loot from the shared MM9 item sources (treasure level 5, trap level 20) |
| Actors | **18 Honks** (rows 9186 `MM9 Honk Female A`, 9216 `MM9 Honk A`, 9187 `MM9 Honk B` for the Elder Honk), friends of the party (group 1); the two `Goose` objects have no MM9 monster row and are left out |
| Pads | 1 (`UnlockDoorTrig`, inside the treasury) |
| Exit | `ExitTrigger0` (DAT object 282) to Guberland, MM9's volume; the arrival from Guberland faces south into the hall (270°) |

## What the conversion does

The shared route (playbook) with these map choices:

- **Doors.** The 13 double doors (`DoubleDoorL/R<n>`) swing as in MM9 (rotating movers, 2026-10-30, [movers](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md));
  a click toggles each pair (events 101–112). `DoubleDoor13`, from the north-west corridor onto the gallery over the
  entrance hall, is the temple's inner door: `Honk.scr` locks it unless the party carries key 343 (the Golden Honk
  quest, QBit 90343): event 130 says "The door is locked." otherwise.
- **The HONK puzzle** (`HonkSecretDoor.scr`, `HonkKey.scr`). The four buttons on the parapet south of the pool are
  locked until the party has the accountant's key (key 7000). Each press pushes its button in and raises its corner
  stone out of the pool (MM9's `Door` motion). When the fourth stone has risen: in the order H, O, N, K the secret
  door slides aside (MM9 pushes the slab back 7 LT, then 78 LT aside with `SecretDoorMover`; here one diagonal slide),
  shuts after 10 s (MM9's `CloseWaitTime`), and everything resets 20 s after it opened; in any other order the stones
  and buttons sink back. Inside the treasury the `UnlockDoorTrig` pad opens the door again for 10 s.
- **The accountant's key** (`key0` on his desk, `HonkKey.scr`): a click gives item 445 (`Accountant's Key`) and key
  7000 and hides the key; if the accountant is alive and within 200 LT of it (he stands there), the Honks turn hostile.
- **The Golden Honk** (`PickupItem Honk` on the altar, `Honk.scr`): a click gives item 369 and key 344 on the quest
  (key 343) or 345 without it, hides it, and turns the Honks hostile. Map load keeps taken objects hidden.
- **Honk hostility** (`HonkHostility.inc`): all 18 Honks are the party's friends (hostility 0, no aggressor bit, group
  1) until the party hurts or kills one (monster damage/killed hooks 96/97) or steals: then group 1 turns hostile
  (`HonksHostile`).
- **The pool.** MM9's `BlueWater0` (`ShowSurface 1`, `Water115.spr` at 0.9 alpha) is drawn as one untouchable face
  over the 8 LT deep channel, drawn by the liquid shader (Deviations); the party wades through it.
- **Swimming (2026-11-06, the shared water rule, `dungeon/water.py` `swimming`).** `BlueWater0` is the scene's water
  volume (one piece, surface -517, brush bottom -573; the channel bed -532: 15 units of water, so the party wades and its
  eye never goes under, as in MM9). Its top is the shared rule's non-solid surface (`drawn_surfaces`; the hook's own
  face only without swimming). The six fish are swimmers bound to it (`convert.py` `swim_fish`): feet 2 over the bed
  (the engine sets a placed flyer whose feet are on the floor onto it) and a 22-unit collision body, so the box centre
  starts 1.5 under the surface, where the engine binds a swimmer; the models keep MM9's DAT Scale 0.4-0.7
  (`draw_scale`), riding at the surface as MM9's float 10 LT over it. Deviation: MM9's body at that scale is 33-57
  tall (the shared swimmer rule's 82 would leave the centre over this shallow water, a walker that climbs the rims).
  `water_room_mismatches` 0, `water_bed_holes` 0. `scenario_swim.yml`: the party walks over the rim into the pool and
  wades 20 s (breath full, no drowning); after it each fish is still in the pool with its feet over the bed (a walker
  stands on it; the runner has `min_z` but no `max_z`, so the actor reports show the clamp).
- **Skylights.** MM9 draws its sky box through 20 `skymarker` faces around the four skylights; they draw MM9's
  `Clouds1` sky texture. The window glass (`window_03`, no alpha in the converted bitmap) is opaque.

## Checks

- Scenarios (all pass): `scenario_doors_exits.yml` (DoubleDoor9 stops the party, opens on event 112, the party walks
  through; DoubleDoor13 stays shut without QBit 90343 and opens with it; the exit raises `mm9_exit_trigger:282`),
  `scenario_chests.yml` (the 5 chests: 3 by interact from in front of their models, the 2 treasury chests by their
  events), `scenario_scripted.yml` (buttons locked without the key; the key by interact from beside the desk: item
  10445 in hand, QBit 97000, Honks hostile; a wrong order sinks the stones; H-O-N-K opens the secret door, which shuts
  after 10 s; reset; the treasury pad reopens it; the Golden Honk by interact on the altar: item 10369 in hand, QBit
  90344), `scenario_hostility.yml` (Honks friendly; hurting Honk0 turns Honk3 hostile), `scenario_swim.yml` (2026-11-06:
  wading in the pool, the fish bound to it, all six still in the pool at feet -529.1 after 20 s). All six pass after
  the 2026-11-06 reconversion; `take` falls back to ignoring the density pass's Elder Honk copies round the altar.
- Walkability (`work/walkability.json`): 67 steps and 7 flights, all MM9 stairs and furniture: the altar dais and the
  altar hall's side terraces are 16 LT (41) steps the party climbs; the amphitheatre's seat tiers (33–48) lie under
  MM9's invisible ramps (kept as invisible collision faces); the 61–123 edges and the 107 "flight" are the benches,
  the pulpit and the altar block, not walkways. 1 unreachable ledge (0.02 M units², a bench top). 16 mover notes (the
  corner stones and buttons stand in the pool and parapet, the secret door in its wall). 1 actor note: the Elder Honk
  stands at the dais edge, as MM9 places him.
- Start: StartPoint0 on the hall floor at the north end, facing south down the pool (view `01-entrance`).
- Compiler unit tests (`build/tools/openyamm_indoor_source_tests`): 20/20 pass.
- Review: `review/v02_compare.jpg` (30 eye-level views of every room type: the entrance hall, pool, amphitheatre and
  skylight, the treasury, the gallery and door 13, corridors, the west wing, side rooms, the main hall with its pews
  and skylight, the basement, the altar hall, the accountant's room, the upper rooms; MM9 original left, native BLV
  baked right) and `review/lighting_compare.jpg` (MM9 original | unbaked | baked). Every view inspected: no holes, no
  missing walls; geometry, textures and props match MM9 apart from the door leaves (Deviations). `review/v01*` is the
  first geometry pass, taken with a game binary that still drew MM9's 1× textures 4× too dense (playbook gotchas).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: lightmap-matched (re-lit 2026-10-31, the user's decision of 2026-10-30: dungeon lighting follows MM9's DAT
lightmaps for brightness and hue; MM9 draws walls as texture x lightmap x1, `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`).**
`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_templeofhonk.yml`: 128 samples,
3 bounces, **`direct_scale` 0.3, `bounce_scale` 6, `ambient_scale` 0.62, `sky_scale` 0.8, `max_lighting` 1** (MM9
clips at x1), `dirlights: true`; the sky (`CLOUVKSJD0`) and skylight panes (`WIND41JATM`) as area lights drawn at
1.1; MM9's three fill lights over the four-per-point cap (`Light6`, `Light33`, `Light34`) bake-only. Sector minimum
light 14 (unchanged). One 4096 x 585 page, passes in `output/mm9_rework/bakes/templeofhonk`; the re-light was a
`--recompose` of the saved passes through `../mm9r_common/bake_slot.sh` (no Cycles run). `tools/lighting/stale_bakes.py
--assets output/mm9_rework/assets_dev --check` does not list the map. Bake again after every `convert.py` that changes
the BLV.

**Method.** `../mm9r_common/relight_fit.py` composes the saved passes per zone for any scales without Blender
(`work/relight/fit_after.txt`); its `--grid` fits (direct, ambient, sky) to the zones' mean, B/R and G/R and to the
map-wide texel quantiles (MM9's p10/p50/p90 0.32 / 0.42 / 0.78: the temple is evenly lit, a high neutral floor and
soft pools). Zones: `hue_zones.py`, eight boxes from `../mm9r_common/relight_zones.py` (a k-d split of MM9's
lightmapped polygons by area; the temple has one storey band). MM9 is neutral to slightly warm everywhere (B/R 0.91-0.94,
G/R 1.00).

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`../mm9r_common/hue_vs_lightmaps.py`,
`work/relight/hue_before.txt`, `hue_after.txt`, table by `../mm9r_common/relight_table.py`):

| Zone | MM9 luma | before | after | ratio before -> after | B/R MM9 / after | G/R MM9 / after |
| --- | --- | --- | --- | --- | --- | --- |
| z1_west_south | 0.448 | 0.771 | 0.404 | 1.72 -> **0.90** | 0.91 / 0.91 | 1.00 / 0.99 |
| z2_west_north | 0.485 | 0.854 | 0.472 | 1.76 -> **0.97** | 0.93 / 0.96 | 1.00 / 1.00 |
| z3_midwest_north | 0.553 | 0.953 | 0.563 | 1.72 -> **1.02** | 0.94 / 0.98 | 1.00 / 1.01 |
| z4_midwest_south | 0.450 | 0.928 | 0.481 | 2.06 -> **1.07** | 0.91 / 0.90 | 1.00 / 0.98 |
| z5_mideast_south | 0.475 | 0.872 | 0.480 | 1.83 -> **1.01** | 0.92 / 0.94 | 1.00 / 1.00 |
| z6_mideast_north | 0.480 | 0.952 | 0.489 | 1.98 -> **1.02** | 0.91 / 0.90 | 1.00 / 0.98 |
| z7_east_south | 0.478 | 0.858 | 0.497 | 1.79 -> **1.04** | 0.91 / 0.96 | 1.00 / 1.01 |
| z8_east_north | 0.495 | 0.838 | 0.460 | 1.69 -> **0.93** | 0.92 / 0.93 | 1.00 / 1.00 |

Hue matches in every zone (hue_vs_lightmaps "matches" or "MM9 neutral ... matches"). Per room (`relight_fit.py
--rooms`) the brazier-lit side rooms (sectors 9, 19) stay x1.4 and the north-west corridor (17) x0.75.

**Screen brightness** (the 30 v02 views, `work/relight/views.txt`, centre crop luma): capture 124.6 (information only:
the old import drawn nearly unlit), unbaked 120.9, old bake 127.0, **lightmap bake 73.2 (x0.59 of the capture)**.
Darkest baked views: the north-west corridor south 44.2, the west wing hall 46.0, the vault door 46.3; brightest the main
hall skylight 128 and the entrance skylight 114. No room is near black (MM9's darkest lightmap texels here are 0.3), so
no player-light floor is needed. No real MM9 screenshot of this map exists (`devdocs/mm9_rework/overnight/real_mm9/`).

**Props: the old path stays** (sector minimum light 14, `model_lighting: false` in `overrides.yml`). Compared on the
same bake (`../mm9r_common/relight_props.py`, `work/relight/model_lighting_props.txt`, the pixels that differ between
the two runs, relative to their own view): capture 0.80, **old path 1.15**, model lighting (AmbientLight 80, ModelAdd
30) 0.74; views with props under x0.6 of their view: old 2, model 6. MM9 draws props at ambient 110/255 plus its
lights against walls at about 0.45, so as bright as the walls or brighter: the old path is closer. Model lighting misses
the three capped fill lights (they reach neither the BLV nor the models). By eye (`review/lighting_v03_props_compare.jpg`,
`_compare2.jpg`: capture | old | model) the old path draws the west wing's tables nearly black (view 12) and the west
room's desks a little washed out (14); the model path is more even but darker. The rebuild with the block and back left
BLV and scene byte-identical; the four scenarios pass after it.

Sheets (looked at): `review/lighting_v03_compare.jpg`, `review/lighting_v03_p01-p05.jpg` (capture | unbaked | old bake |
lightmap bake, 6 views a page). The temple keeps its pale stone and blue floors, the braziers' warm pools and the
skylights' cool light, about half the old brightness.

**Documented alternative: the capture-matched bake** (installed until 2026-10-31): `work/profile_capture_matched.yml`
(direct 0.65, bounce 6, ambient 1.15, sky 0.35, no ceiling): lightmap ratios 1.7-2.1, screen mean 127 against the
capture's 125. To switch back: copy it over the profile and run `../mm9r_common/bake_slot.sh python3
level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_templeofhonk --recompose`.

History: the capture-matched bake of 2026-10-30 (doors, skylights, fill lights) is in `review/lighting_v02_*`: mean of
the 30 views MM9 capture 122.9, after 123.9.

## Deviations from MM9 and why

- The secret door slides diagonally in one motion (a linear mover). Double doors swing as MM9's since 2026-10-30.
- **Door textures**: the indoor renderer recomputes every mover face's UVs at MM6–MM8's one texel per unit, so the door
  leaves draw their texture about twice as dense as MM9 (an engine item, open; Anskram's doors too).
  (Superseded 2026-10-30: rigid door faces keep their stored texels, DUNGEON_PLAYBOOK "Mover face texels".)
- **The ceremony (2026-11-11)** runs on scene routines (`mm9_ai.routines`) the ceremony timer (map timer 154, every
  3 s) switches from the game hour (`convert.py` `routines`, `ceremony_lines`): at 6:15 and 18:15 the bell rings and
  the followers (`HonkFollower.scr`) walk their `CeremonyMarker` lists to the pulpit (`go`), face it and loop hattack1,
  fidget1 or fidget2 at random (`worship`); from the first arrival the leader (`HonkLeader.scr`) paces between the
  platform markers, faces the hall and plays prop-fidget1/2, fidget1 or prop-stand, a thunder at him every other
  check (`preach`); between ceremonies he loops prop-stand (`idle_clip`). The end is 7:15 and 19:15, 30 minutes later
  than MM9's 6:45/18:45: the walk from the entrance hall takes about 80 s (40 game minutes), so at MM9's end none
  would have arrived. The followers then walk their lists back (`home`) and wander (aimless, MM9's WanderON with no
  path). At 7:00 and 19:00 the accountant (`HonkAccountant.scr`) walks PathMarker0-13, plays prop-fidget1 at the far
  end and walks back (`trip`). Routines are runtime only: the timer sets them again after a load (a follower within
  400 of its pulpit marker worships at once). Not while the Honks are hostile. Checked headless (followers arrive
  6:55, worship clips, leader `prop_fidget*`, home at 7:15; the accountant's round 19:00-20:26) and in desktop captures
  (`output/held_items_check/templeofhonk/`: the followers in two groups at the pulpit, facing it, the leader at the
  pulpit; the hall empty again from 7:20).
- Four Honks chase two big geese in MM9: the geese (`Goose`, MM9 row 293) have no runtime monster row and are left
  out.
- MM9's `TriggerStartCeremony0–2` remove `HONK_CEREMONY`, which no MM9 script listens to: not built.
- The pool's water is the engine's liquid shader (2026-10-31: `water115_mm9`, [shared helper](../mm9r_common/liquids.py); MM9
  animates Water115 at 0.9 alpha); the six `Fish` swim in it since 2026-11-06 (MM9 floats their centres 10 LT over
  the surface; ours are kept in the water, which the engine's swimmer binding needs). MM9's `BlueWater0` is 8 LT deep (surface -517,
  channel floor -532 native, 2 LT under the rim): the party walks into it and wades, MM9 never swims there. User decision
  2026-10-31: wadeable as in the original, `depth: shallow`, MM9's geometry kept (the untouchable surface over the
  channel floor). Sheet: `review/liquid/before_after_p1.jpg`.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the pool is see-through (`BlueWater0`: 0.9 x Water115.spr 0.42 = 0.37,
  `lqw115o37`): the fluted channel bed shows under rippling, reflecting water. Sheet `review/liquid/see_through.jpg`.
- The skylights show a static cloud texture instead of MM9's sky box; the glass is opaque (lit as a window, 2026-10-30).
- The secret door opens by the HONK puzzle only (MM9 also flags it `PushOpen`; the puzzle is its intended opening).
- Monsters carry no MM9 treasure overrides (`actor_loot_overrides` of the item sources: 26), as in Anskram.

## What remains

The Honk creature art (MM9 Honk family: 3D creature work); the door-texture engine item; the goose chase as native AI
behaviour if wanted; animated water; `fish.scr`'s surface jump (FISH.abc has no Jump clip).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:52:25 (convert.py from the current shared converter, end 14:53:21): 38 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 5751 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_hostility.yml` pass, `scenario_scripted.yml` pass.
Stair probes (`scenario_stair_probes.yml`, `../mm9r_common/stair_probes.py`): 12 walks up the ramps over dropped bottoms, before / after (xy, z native): [282.64, 21.678] / [282.64, 21.678]; [1329.013, 121.034] / [1329.013, 121.034]; [279.17, 19.0] / [279.17, 19.0]; [1371.011, 121.154] / [1371.011, 121.154]; [279.57, 21.678] / [279.57, 21.678]; [1023.0, 0.0] / [1023.0, 0.0]; [278.564, 19.0] / [278.564, 19.0]; [1024.0, 0.0] / [1024.0, 0.0]; [278.317, 19.0] / [278.317, 19.0]; [805.008, 64.0] / [1282.43, 255.715]; [277.792, 19.0] / [277.792, 19.0]; [983.428, 0.0] / [983.428, 0.0]; 1 walk farther after the rebuild.
The texture session's stair repro (`level_generation/textures_x4/audit/mm9_shots/honk_stairs/`): the party at (-3497, 6556, -458) heading 225 walked 0 before and climbs 817 units / +304 now; the four starts below it climb 893-1123 / +338-370 (before 96-347 / +34-64); `scenario_stairs.yml` passes (record: `work/honk_stairs_1031.txt`).
