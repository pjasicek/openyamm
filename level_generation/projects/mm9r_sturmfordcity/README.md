# MM9 rework: Sturmford City (`sturmfordcity.blv`), the city pilot

MM9's Sturmford City (the docks, the palace district with the Jarl's hall, the temple square, the north town with
the market; 37 walk-in shops, houses and halls; reached from the Sturmford wilderness, the Beethoven sewers and by
Town Portal) converted from its DAT world into a native **indoor map (BLV) open to the sky**, the first of MM9's seven
cities (user decision 2026-10-31: cities as BLV + sky for performance; [PLAN.md](../../../devdocs/mm9_rework/PLAN.md),
Cities row). Built on the shared dungeon converter ([DUNGEON_PLAYBOOK.md](../mm9r_common/DUNGEON_PLAYBOOK.md)) and its
new city extension ([CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md), `../mm9r_common/city/`), installed in the
review root `output/mm9_rework/assets_dev`. Props: [`../../props/mm9_sturmfordcity_claude/`](../../props/mm9_sturmfordcity_claude/README.md).

Status 2026-10-31 (pilot, unattended): **the city works as a BLV.** Geometry, 63 sectors with a street/roof
structure, Enhanced outdoor sky with time of day behind the sky faces (engine, opt-in), MM9's painted city map as the
minimap (no outlines), 48 townsfolk and the guard with their RUDE dialogues (walk-in shops open by real clicks), 9 posed
talking props, 439 decorations, the doors, two treasure bags, every gameplay-relevant script as native Lua, the six
exits and six starts. Classic lighting (no bake: [MM9_LIGHTING_DECISION.md](../../../devdocs/mm9_rework/MM9_LIGHTING_DECISION.md)).

## Build and review

```sh
python3 level_generation/projects/mm9r_sturmfordcity/convert.py --plan     # rooms only: work/rooms*.png (6-8 min, 1.9 GB)
python3 level_generation/projects/mm9r_sturmfordcity/convert.py            # build, compile, install (8-10 min)
python3 level_generation/projects/mm9r_sturmfordcity/make_scenarios.py
for s in doors_exits shops chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_sturmfordcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_sturmfordcity/make_tour.py v03 [--original]
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city_sturm_3 --world mm9 --map sturmfordcity.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 2089 -973 19723 --yaw-radians 1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 170 --set logging.performance_trace=true --set logging.indoor_visibility=true \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_sturmfordcity/review_tour_v03.yml
# the original: --map sturmfordcity.odm --assets "$PWD/output/mm9_rework/sturmfordcity_original_root" \
#     --set video.view_distance=unlimited, tour review_tour_v03_original.yml (a private hard-linked copy of
#     assets_original whose worlds/mm6-8 actors.yml are the committed ones: other sessions' unfinished tables stop it)
python3 level_generation/projects/mm9r_common/dungeon/sheet.py level_generation/projects/mm9r_sturmfordcity/review/v03 \
    level_generation/projects/mm9r_sturmfordcity/review/v03_original
python3 level_generation/projects/mm9r_sturmfordcity/work/perf/counts.py work/perf/blv_v03.log ...   # performance counts
```

Play: `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city --visible --world mm9 --map sturmfordcity.blv
--assets "$PWD/output/mm9_rework/assets_dev" --seconds 3600`.

## Numbers and limits

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame, transitions and the painted map's bounds
  stay valid). Extent x -5 773..16 294, y -1 541..20 145, z 17 746..21 873: **inside ±32 767**.
- 9 954 source polygons -> 9 452 merged -> 11 072 native polygons -> **12 926 compiled faces, 21 148 vertices** (12 810 and 20 992, with 225 portal faces, since the merged top
  portals of 2026-11-01; BLV
  indices are 16-bit: **32 % of 65 535**; no widening needed), 343 portal faces, 105 doors (movers), 151 BLV lights,
  **0 outlines** (painted minimap; the 7 000-outline save limit no longer applies), 59 sky faces, 69 translucent faces
  (window panes; under the 1 500 warning).
- Faces per sector: **max 997, median 119** (MM6-MM8 dungeons: ≤ 300; MM9 dungeons up to 4 800; the per-sector face
  grid of 2026-10-31 removes that cost: [BLV_GEOMETRY_COSTS.md](../../../devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md)).
- Voxels: 16 LT, 543 x 105 x 534 = 30 M cells, 3.9 M air, 1.9 GB peak, 110 s for the geometry pass (dungeon defaults
  work at city size).

## Structure: sectors and portals

**63 rooms** (sectors 1-63) and **343 portal faces**:

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors (shops, houses, halls, the palace) | 37 rooms | behind 14 MM9 UserPortals and 25 door-leaf portals; their windows are **37 glass portals** (MM9's panes, translucent faces) |
| Street rooms (open air under the roof line) | 24 | divided by **23 street cuts** (21 found automatically, 2 by hand; 5 dropped as loops); 5 cuts that crossed junctions were split into one portal per pair of rooms |
| Roof rooms (open air over the roofs, one per district) | 3 | joined to the streets by **116 merged top portals** (convex polygons over walls and roofs, `merged_top_portals`, 2026-11-01; were 244 roof-line rectangles, 5 blind) |
| Sewer pieces, the well shaft | rest | the sewer hatches and the well need no portal (an invisible plate seals each shaft; the well is part of its street) |

How the open air is divided (`../mm9r_common/city/structure.py`, CITY_PLAYBOOK "The open air"): MM9's DAT gives
districts walled off from each other (the docks and palace district, the temple square, the north town) under sky
shells; its `VisBSP` holds 2 057 BSP leaves with a precomputed PVS (437 KB of leaf lists) and 18 UserPortals (doors),
but no portal graph for the streets, so the streets are divided from the air voxels: a horizontal roof line at 7 968 LT
(256 over the streets, under the lowest eaves), street cuts at narrow corridor places every ~1 280 LT, and top portals
from each street room into its district's roof room. Plan: `work/rooms_street.png`; per view the renderer draws a
median of **5 sectors** (max 12).

**Merged top portals (2026-11-01, `merged_top_portals: true`; CITY_PLAYBOOK "The open air" step 3,
[CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md) "Result of proposal 3").** The 244 rectangles
become 116 convex top portals (at most 8 corners; rebuilt with the final converter on 2026-11-01 evening; the afternoon build predated the sky-face rule): **343 -> 215 portal faces, 12 928 -> 12 800 faces,
21 154 -> 20 965 vertices**; only the portal faces change. On the 20 street poses of the v03 tour (before: the
2026-10-31 build, `output/mm9_rework/portals_1101/sturmford/before_oldtex`; after: `.../after`): traversal nodes median
28 -> 17, max 66 -> 38 (no cap hit before or after); portal link tests median 1 489 -> 485, max 4 099 -> 1 133. Sectors
drawn equal at every pose. All 32 images compared in 16 x 16 blocks: no hole, only the new x4 textures. Scenarios
chests, doors_exits, scripted, shops pass.

## Sky and minimap

- **Sky**: MM9's 57 `skymarker` polygons (a lid 500-800 LT over the streets, walls, "sky floors" outside the city
  walls) are faces with `IndoorSky`; the scene opens to the sky (`sky: {mode: open, sky_texture: plansky3}`), so the
  engine leaves them undrawn and draws our **Enhanced outdoor sky with the game's time of day** behind the scene
  (engine feature built in this pilot: [INDOOR_OPEN_SKY.md](../../../devdocs/INDOOR_OPEN_SKY.md)). `plansky3` is the
  old import's sky (`legacy_plansky3` preset). Review: `review/sky01_sheet.jpg` (06:30, 12:00, 19:30, 23:30: sun,
  dusk, stars).
- **Daylight (2026-10-31)**: `city: {daylight: true}`: the streets open to the sky take MM9's ambient 70 and its
  StaticSunLight by the time of day (interiors unchanged); MM9 has no fog here (`map: {fog: lithtech}` is set for when
  it does). Reinstalled (BLV unchanged); sheets `review/dl_compare_<time>.jpg`. See CITY_PLAYBOOK "Daylight and
  fog".
- **Night on the lightmaps (2026-11-06)**: the transferred MM9 lightmaps held noon at every hour (street pose s04:
  centre luma 85 at noon, 72 at midnight). The transfer now writes daylight pages (version 2 sidecar,
  devdocs/INDOOR_BAKED_LIGHTING.md "Daylight pages"): s04 85.0 / 35.5, s10 49 / 21, the tavern 43.5 at both hours;
  MM8 Ravenshore 79 / 35 for comparison. Installed in the review root only (`lightmap_transfer.py <project> --install`).
- **Street lights x BrightScale (2026-10-31, late)**: the yellow-white glare on some facades was the BLV street lights
  at full strength; MM9 baked its lightmaps with LightColor x BrightScale. `map: {bright_scale_lights: true}`: 123 of
  151 lights at colour x 0.2-0.85. Rebuilt; the palace front (06) and north lane (14) read like the old import at noon
  and night, the palace ring north (08) keeps a warmer wash on its west wall (lights at 0.85-1.0)
  (`review/bs_compare_1200.jpg`, `_2330.jpg`: old ODM | before | after). Scenarios rerun: doors_exits, shops, chests,
  scripted pass. See CITY_PLAYBOOK "Street lights and BrightScale".
- **Minimap**: MM9's painted city map (`ui/maps/sturmfordcity.pcx`, catalog entry kept by `map: {painted_minimap:
  true}`); the indoor minimap already draws a catalog map instead of lines. No outlines are compiled.

## Content

- **People** (48 actors, all friendly): 44 with RUDE dialogues, from the old import's NPC records (names, rows), with
  MM9's bodies (each object's model's initial dims x its Scale, `mm9_monster_bodies`); the prison guard (row 9107,
  MM9's PoorTownGuard1) gets dialogue 425 as his script does; 2 dogs (row 469) and 2 cats (MM9's 9294) wander;
  the 24 townsfolk on NPCBase.inc's own aimless wander (no script of their own, `convert.py` `wanders()`) walk the
  streets, meet and chat with Conv clips (monster_ai/MM9_AMBIENT_ANIMATION.md sections 2.2-2.3; 2026-11-07, before
  that every townsperson was placed immobile); the others stand where MM9 placed them, including Hatlati, whose path
  walk waits for NPC48.scr's Wander message (MM9's daily schedule is not carried; its schedule markers are missing from
  the DAT anyway).
- **Walk-in shops**: the shopkeepers stand in their shops; a click opens their RUDE dialogue and its service row opens
  the shop (scenario: the armourer and the magic shop). Shops close from 20:00 to 06:00 (key 5017, ForadWorld.scr).
- **Posed talking props** (9 RUDEProps: the innkeeper Kenneth Wartooth, Ludwig Van, Jarl Bjarni, Tryygva, Halfdan
  Doorsbane, Ake, two drinkers, Ercc): MM9 poses them as props whose script loops one animation. Since 2026-11-07
  they are actors on the HD townsfolk bodies (`../mm9r_common/rude_props.py`: row by model and skin, passive,
  immobile, never hurt) looping that clip (innkeeper2, ludwig_writing, listen, sitting, sitting2, Bjarni's sit) from
  the load handler (`evt.PlayActorClip`, `evt.FaceActorTo`: no turn or head look in a dialogue). Their use hooks play
  the script's voice line and open the dialogue, Bjarni's and Ludwig's exit hooks pay their rewards; Ludwig looks up
  when used, Tryggva talks on his bark, Ercc drinks and passes out on his (ercc01a-c, then ercc02, then ercc_out
  loops the slumped pose). **Ercc's cup (2026-11-11):** his scene `held_items` hang `mm9_item_erccup.glb` (Cup1 of
  MM9's Ercc.ABC) on the townsman's `Socket_Cup`, and the townsman's right hand is closed round its stem in every
  clip that holds it (`../../props/mm9_held_items_claude/scripts/grip_clips.py`); he loops `ercc_sitting` (Ercc.ABC's
  own `sitting`: the cup at his chest, not PeasantSeated's hands in the lap; `rude_props.MODEL_CLIP_ROLES`). He is
  the only seated drinker MM9 gives a cup: the tavern's other sitters (Tryggva, Halfdan, the two drinkers, all
  PeasantMS2/PeasantSeated, no cup piece) get none from their scripts; their mugs stand on the tables
  (Cup/Cup0-3 decorations). Captures: `output/held_items_check/sturmfordcity/grip_front/`, `grip_sitting/`. The cat on the counter (`Cat2`, PropAnim standdown) stays a posed
  decoration (the HD cat has no standdown).
- **Doors**: 105 movers: MM9's swing doors (`rotate`, pairs open together), 43 locked doors (34 facade doors that never
  open, MoveDist 0, and 9 locked swing doors: a click says so), the jail door (the guard opens and locks it), two sewer
  hatches, the grate to Beethoven, the bar's flap.
- **Chests**: the two treasure bags at the bottom of the well (MM9: under 200 LT of water, reached by diving; here the
  water is not solid and the well's rope reaches the bottom: `Ladder7`, extended in `convert.py`).
- **Exits** (`map_transitions.txt`): ExitDock and ExitN to the Sturmford wilderness, ExitS, ExitW, ExitE and GrateExit
  to Beethoven; ExitDock reaches down to the dock's planks (`exits: bottom_lt 7690`). **Starts**: the six of the old map
  (docks, three sewer mouths, the north gate, Town Portal), on their floors, facing MM9's 90 - ry.
- **Letters**: the five BookLetter scrolls show their texts (BOOK AND SCROLL TEXT.csv 449-453); Book.scr's books have
  no text in MM9.

### Scripted objects (`citylua.py`; behaviour spec of every script: `work/scr_spec.md`)

| Script | Native |
| --- | --- |
| Bankorb.scr (Herdis) | the Orb of Linking: key 330 on a click with the orb, the exit places it (324), six orbs: 337, 20 000 xp, 15 000 gold |
| Beathag.scr (the healer) | the exit takes 700 gold for a broken temple window (5002 + 5003); the windows themselves are not breakable here |
| Bjarni.scr (the Jarl) | the click: 215 (Basilisk Skin), 178 (five clans); the exit (poll): Ivsar 117, love letter 150 + item 247, 151, Anskram 149, the clans 179; hidden on 40 unless 108 |
| LudwigVan.scr | the exit (poll): 116, 12 000 xp, 2 000 gold, the manuscript taken |
| SpiesLikeUs.scr, Randverrun.scr | 471 / 2 000 xp / 500 gold; 495 / 800 xp and Randver vanishes (gone on 15) |
| NPC61.scr (the clerk) | 215; the Gladiator promotion (221, 63 000 xp, 5 000 gold, keys 409-412); Kira's Shield taken |
| Sturmguard.scr (the prison guard) | dialogue 425; the jail door (5018 open, 5019 close and lock); Hatlati's arrest (154 -> in the cell, 5009) |
| NPC48 / NPC49 / NPC90 / NPC378 | Hatlati jailed on 154; Itlor at the magic shop on 157; Ivsar visible on 242, at the throne on 117, his exit 196; Thorolf's two copies by 83/84/106/107, the twin removed, the dialogue reopened, the vanish |
| AkeRetainer.scr, Retainer.scr | hidden while hired (454, 451) |
| ForadWorld.scr | location key 1026 (1024-1033 cleared), shop hours 5017 |
| TownPortal.scr | cleansing the altar: key 5012 (the dirty altar hides and its clean twin `mm9_portalclean` at its place shows, also on load: `../mm9r_common/dungeon/town_portal.py`) |
| BookLetter.scr | the five letters |
| Book.scr, PropAnim.scr, NPC50, Shopkeeper.scr, TryggvaSpeech, ErccSpeech | cosmetic (animations, voices); not carried |

Left out, written down: MM9's 11 breakable temple windows (no native breakable glass; the healer's payment branch
stays for completeness); the hire keys 451/454 (MM9's hire service grants them implicitly; ours does not); keys 409-412
(who is a Mercenary: MM9 sets them on the class side); Ivsar's 5006 (Drangheim Prison's alarm key, a source quirk);
Thorolf's and Randver's walks and town-portal effect (they vanish at once); the cinema voices (Tryygva, Ercc) and the
vanish sounds (not imported); the 24 PerceptionBrushes (red hints on gates and locked doors; not built, as no
gameplay hangs on them here); MM9's ambient sounds.

Added, not MM9's (the user, 2026-11-09): Chedian's **dimensional travel pedestal**, as on the other continents. MAW's
teleporter (the `ped06` pedestal under the `dec57` orb, engine indoor bindings) stands on the lawn east of the south
sewer hatch (`convert.py` `PEDESTAL`); a click or Use on either runs event 250, which opens the
four portals (`evt.OpenDimensionDoor()`; no quest gate since Verdant's removal, 2026-11-09). A Dimension Door
to Chedian lands the party 224 units east of it, facing it, once the Isle of Ashes is left (key 28); before that at
Ravensford's new-game start (`resolveDimensionDoorLanding`, GameplayPartyOverlayInputController.cpp). The rebuild
changed only the BLV's decorations, so the lightmap transfer carried the bake over unchanged
(`lightmap_transfer.py ... --install`, `carried_over: true`).

## Quality gates

1. **Every DAT world model has a rule** (195 + PhysicsBSP); skipped with reasons: the sky box and the TOD star shell,
   2 AI barriers, the well's water volume (its top is a face), the tavern's PortalZone, VisBSP, the 6 ladder volumes,
   24 PerceptionBrushes, AI tracks.
2. **Sealed air**: `leaked_to_border` false, 1 air component (3.9 M voxels); seeds added under the hatches and the grate.
   278 faces without air in front dropped (`work/dropped_faces.json`).
3. **Every portal joins two rooms**: `portals_without_two_rooms` 0 (gates out of the city and hatches have none).
4. **No holes**: the 32-view sheet (`review/v03_compare.jpg`) shows no hole; v01 showed two (a cut joining three pairs
   of rooms drew sky through the minor pair: fixed by splitting cuts per pair; one view stood in a sealed, unseeded
   building and was moved). Floor holes 0, cracks 0. Floor check 150 535 LT²: cut strips and wall tops ("Open items").
5. **Review sheet**: MM9 original (the old ODM import, view distance unlimited) | native BLV, **32 eye-level views**
   (20 streets and plazas, 12 interiors): `review/v03_compare.jpg`; looked at: same geometry and textures in every
   view; ours draws the palace front brighter (classic vertex light near its lamps) and lacks the original's green
   perception glow on two gates. Time of day: `review/sky01_sheet.jpg`.
6. **Walkability** (`work/audit.log`, `work/walkability.json`): 42 steps (the half step closed one), 29 flights, 1 pit,
   18 regions monsters cannot reach, 70 mover notes, 3 actor notes. The pit is the hatch recess over ExitW (0.02 M
   units²: the party drops onto the invisible plate in the exit volume, as in MM9). The 18 regions need nothing
   (checked one by one, CITY_PLAYBOOK "Raised floors"): 6 building plinths (the four 41 "plaza platforms" and the 61
   "strips" of the two north streets: the house walls stand on the plinth's edge or 11-51 behind it), the inside of
   the keep's solid block (2, the 61 "strips" along the palace ring's west side), the counters (103-113, 6), the
   tavern's back bar (112), two table hulls (48 + 39, the party climbs them) and the fountain basin (49). Forward walks
   (`work/probes/raised_floors.yml`): the 61 plinth fronts stop the party on the street, the 41 ones let it onto the
   ledge against the wall, the table hull lifts it 48 and 86.
7. **Scenarios pass** (headless, real clicks where the engine picks): `scenario_doors_exits` (23 steps: the general
   store's double door stops the party, opens on its click, the party walks in; a facade door stays locked; ExitDock
   and the hatch over ExitS raise their transitions), `scenario_shops` (32: the armourer's and the magic shop's
   dialogues by press_interact, their service rows open the shops; the innkeeper by his click event), `scenario_chests`
   (the two bags; the climb out of the well), `scenario_scripted` (30: 1026, 5017 at 21:00 and not at 09:00, Ludwig's
   reward on the poll, a letter, the guard jails Hatlati).
8. **Starts**: six, each on its floor (`build_report.json` `starts`); the first view of the tour is the docks' start.
9. **Compiler unit tests**: `openyamm_indoor_source_tests` 21 of 21.
10. **Lights**: 151 BLV lights; 26 MM9 fill lights over the four-per-point cap are bake-only and unused without a bake.

## Performance (counts; frame rate needs a single-session run)

Same 32 views (`review_tour_v03*.yml`), `logging.performance_trace` + `logging.indoor_visibility`, minimized isolated
desktop runs on a shared machine. MM8 comparison: Ravenshore (`out02.odm`), 8 points x 4 yaws round its town centre.

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Textured batches |
| --- | --: | --: | --: | --: |
| **Sturmford City, native BLV** | **218 / 385** | **30 600 / 70 800** | 5 / 12 | 96 / 238 (of 805) |
| Sturmford City, old ODM import | 1 347 / 1 879 | 57 500 / 156 500 | – | – |
| MM8 Ravenshore town (ODM) | 262 / 313 | 195 400 / 346 800 | – | – |

- **Map load** (median of 3, `OPENYAMM_MAP_LOAD_TIMING=1`): BLV **1.46 s** (asset load 0.47 s) against the old ODM
  2.73 s (0.89 s). Logs `work/perf/load_*.log`.
- **Monster AI cost** (the geometry audit's benchmark, `work/perf/bench/`: 16 hostile goblins beside the party in the
  temple square, 40 game seconds, with minus without, CPU user + sys, 2 repeats): **1.5-1.7 ms per goblin per game
  second**, with the forced pathfinding log; MM9 dungeons 0.7-1.4 ms and MM8 `d13` 0.4 ms after the per-sector grid
  (BLV_GEOMETRY_COSTS.md). The goblins here mostly pressed against a fence (blocked moves logged).

## Engine and converter changes

- **Engine** (opt-in, MM6-MM8 untouched): the scene's `sky` block opens an indoor map to the sky
  ([INDOOR_OPEN_SKY.md](../../../devdocs/INDOOR_OPEN_SKY.md); `game/indoor/IndoorOpenSky.h`, `IndoorSceneYml.cpp`,
  `IndoorMapData::openSky`, `IndoorRenderer::renderOpenSky`; `tests/IndoorOpenSkyTests.cpp`, 3 cases).
  Unit tests **2 429 of 2 429**; `openyamm_runtime_tests` **54 of 55** (the New Sorpigal braziers case, which failed
  before); `indoor` regression suite **173 of 174** (`mm6_ogr_actor_models_bind_all_tiers`, another session's ogre model).
- **Build fix**: `tools/CMakeLists.txt` lacked `game/indoor/IndoorSectorFaceGrid.cpp` in `openyamm_indoor_source`
  (from the 2026-10-31 per-sector grid), so `mm9_compile_indoor_source` no longer linked; added.
- **Converter** (under `locks/converter_edit.d`, both off by default; Lich Lab `--plan --scratch` before and after:
  identical): `Hooks.extra_portals` (a map's extra portals with barrier cells, before the rooms are labelled) and
  `map: {painted_minimap: true}` (keep the catalog entry, `generate_outlines: false`). New module
  `../mm9r_common/city/` (structure.py, hooks.py).
- **Half steps made to work** (2026-10-31, under the converter lock, still opt-in; Lich Lab `--plan --scratch` before and
  after: identical): `city/hooks.py` `half_steps` steps only rises the party can stand on (floor 32 LT on behind the
  edge, no wall across or on the edge, none within 16 LT), no step at a riser between two floors of one height, treads
  20 LT deep; `build_report.json` `stats.city_half_steps` lists them. Unit test in
  `tests/IndoorMovementRecoveryTests.cpp` (the 61 terrace, with and without the step). `city: {half_steps: true}` here.
  Scenarios after the rebuild: doors/exits, shops, chests, scripted all pass; `work/probes/raised_floors.yml` passes.

## Open items

- **Floor check** (gate 4 wants door sills only): 150 535 LT² of floor under another room's air. Checked against fresh
  voxel labels (`work/city/floor_rooms.py`): the bulk is the 16 LT strips along the street cuts (a barrier voxel takes
  a neighbour's label: the Chasm of the Dead's "canyons cut whole" note), plus wall tops and invisible blockers just
  over the roof line (rooms 22/27/28/30/33/34 -> the roof room 21) where nobody stands. No review view shows a wrong
  sector.
- **Raised floors: settled** (2026-10-31, CITY_PLAYBOOK "Raised floors"). The party steps 50 (MM8's party about 40,
  MM9's player 102-123). No raised floor here is one the party could stand on (gate 6). `city: {half_steps: true}` is
  on: the pass now steps only standable 50-66 rises and makes one step here, beside a stair top at (9874, 3203) that
  the stair reaches anyway. The party bobs about 10 units when pressed into a house front on a 41 plinth (it steps
  onto the 11-unit ledge and slides back): an engine matter, not fixed.
- No Perception hints, no breakable windows, no MM9 schedule.
- Townsfolk need the 38 MM9 town NPC bodies (another session's work): they draw as stand-in peasants.

2026-11-06 (the user's report: fell into the well and could not climb out): the review root's build (20:29, the shared
water rule) has the well as water (Wellwater in `water_volumes`: top 18 330, 655 deep, fog; its surface the converter's
own face, `own_water_surfaces`), and Ladder7 (the chain) reaching the bed. `scenario_well.yml` (hand-written): the party
falls into the shaft, is under, rises to the surface, swims into the chain, climbs it and steps off dry at the street
(z 19 784): pass. The promoted assets_dev build predates this.
