# MM9 rework: Arslegard City (`arslegardcity.blv`)

MM9's Arslegard City (the walled city of the gods' heroes: the Great Gate with Hanndl the Gatekeeper, the bank, tavern,
magic shop, temple, library, weapon and armour shops, two general stores, the training hall, Njam the Meddler's house,
the park on the west terrace, the fountain court by the Hall of the Gods' gate and a canal through the middle; reached
from the Bath House, the Thousand Terrors and the Hall of the Gods, and in MM9 by dying) converted from its DAT world
into a native **indoor map (BLV) open to the sky**, wave 2 of the city rollout
([CITIES_ROLLOUT.md](../../../devdocs/mm9_rework/CITIES_ROLLOUT.md), [CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md)).
Built on the shared converter and its city module, installed in the review root `output/mm9_rework/assets_dev`. Props:
[`../../props/mm9_arslegardcity_claude/`](../../props/mm9_arslegardcity_claude/README.md).

Status 2026-10-31 (unattended): **the city works as a BLV.** 63 sectors with the street/roof structure, our Enhanced
sky with time of day behind the sky faces, MM9's painted city map as the minimap, 36 people (34 with RUDE dialogues:
walk-in shops open by real clicks), Njam the Meddler, 419 decorations, the 30 doors, the Great Gate scene's outcomes
(FateMan.scr, WritMan.scr), Njam's chase, Sven, Hanndl, the letters and Njam's Struggle as native Lua, six exits and
four starts. Classic lighting, no bake ([MM9_LIGHTING_DECISION.md](../../../devdocs/mm9_rework/MM9_LIGHTING_DECISION.md)).
No converter or engine change: everything Arslegard needed is in this project's `convert.py`.

## Build and review

```sh
python3 level_generation/projects/mm9r_arslegardcity/convert.py --plan     # rooms only: work/rooms*.png (5 min, 2.9 GB)
python3 level_generation/projects/mm9r_arslegardcity/convert.py            # build, compile, install (10 min)
python3 level_generation/projects/mm9r_arslegardcity/make_scenarios.py
for s in doors_exits shops scripted ladders; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_arslegardcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_arslegardcity/make_tour.py v05 [--original]     # sky02: four times of day
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city_arslegard_blv --world mm9 --map arslegardcity.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 14400 2387 -491 --yaw-radians -1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 170 --set logging.performance_trace=true --set logging.indoor_visibility=true \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_arslegardcity/review_tour_v05.yml
# the original: --map arslegardcity.odm --assets "$PWD/output/mm9_rework/arslegardcity_original_root"
#     --position 14400 -17613 -491 --set video.view_distance=unlimited, tour review_tour_v05_original.yml (a private
#     hard-linked copy of assets_original whose worlds/mm6-8 actors.yml are the committed ones and whose old scene
#     allows saving)
cd level_generation/projects/mm9r_common && python3 -m dungeon.sheet ../mm9r_arslegardcity/review/v05 \
    ../mm9r_arslegardcity/review/v05_original && cd -
python3 level_generation/projects/mm9r_arslegardcity/work/perf/counts.py work/perf/blv_v05.log work/perf/odm_v05.log
bash level_generation/projects/mm9r_arslegardcity/work/perf/loads.sh                     # map load, 3 x 2
```

The BLV tours set key 98 in their first shot (`qbit set 90098`): without it FateMan.scr's cinematic `gate_fate`
("Cinematics" below) starts about 3 s after the arrival and moves the party to the Dark Passageway 71 s later. Diagnostics: `tools/leak.py` (seeds whose air touches the
grid border), `tools/leak_path.py X Y Z` (the voxel path from a point to the border), `work/probes/` (forward walks).

## Numbers and limits

- **Frame: offset.** The DAT spans native y -34 488..-5 734 (LT z -13 472..-2 240), over int16, so the frame is shifted:
  native = (LT.x, LT.z, LT.y) x 2.56 - (0, -20 000, 0), y -14 488..14 266 (Connecting Tunnels' route). The shared
  writers keep the old map's frame, so `convert.py` moves by the same offset: props.json (the props project writes the
  old frame; `work/props_native.json` is the shifted copy), the transition rows (`offset_transitions`: this map's exit
  volumes and the arrivals into it). The painted minimap's world bounds in the catalog (y -14 488..14 266) are moved
  by the shared catalog writer (`dungeon/tables.py`, every project with an offset). `make_tour.py --original` adds the offset back for the old map.
- 7 473 source polygons -> 6 815 merged -> 10 547 native polygons -> **11 830 compiled faces, 16 017 vertices** (BLV
  indices are 16-bit: **24 % of 65 535**; 11 792 faces and 16 261 vertices since the merged top portals, 2026-11-01),
  224 portal faces (213 since), 30 doors (movers), 55 BLV lights (at most 4 per floor
  point), **0 outlines** (painted minimap), 402 sky faces, 24 translucent faces (the bank's bars).
- Faces per sector: **max 1 998**, **median 26** (Sturmford 997 / 119, Thronheim 1 460 / 142).
- Voxels: 16 LT, 20.3 M air voxels (MM9's sky lid sits 1 470 LT over the streets), 2.9 GB peak.

## Structure: sectors and portals

**64 rooms** (sectors 1-63 after the compile) and **213 portal faces** (224 before the merged top portals):

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors (tavern, bank, magic shop, temple, library, weapon and armour shops, the general stores, the training hall, Njam's house, the gate towers) | 15 rooms | behind 11 MM9 UserPortals and 3 door-leaf portals |
| Street rooms (open air under the roof line, the canal) | 48 | divided by **41 street cuts** (automatic, a denser search: `cut_spacing_lt` 640, `max_cut_width_lt` 1 024, `corridor_lt` 96; 8 dropped as loops); the canal splits the city into a west and an east half joined by two bridges |
| Roof room (the air over the roofs) | 1 | joined to the streets by **158 merged top portals** (convex polygons over walls and roofs, `merged_top_portals`, 2026-11-01; were 169 rectangles grown over solid) |

- **The roof line** at LT 192 (384 over the streets at -192, under the eaves at 208-240).
- **Top portals over solid** (`convert.py` `city_portals_through_solid`, until 2026-11-01; now the shared merged top
  portals below). The shared cover keeps each top rectangle
  inside its street's air; along Arslegard's 45-degree streets that broke every footprint into staircases of thin
  rectangles: 1 024 top portals, and the indoor visibility build tested ~90 000 portal candidates and took 4-16 ms on a
  sector change (Sturmford: 0.3 ms). Here a rectangle grows on over cells with no air at the roof line (walls, roofs,
  the floorless insides of MM9's hollow houses) and no other room's: 169 top portals, visibility builds at most
  1.1 ms. Its barrier cells stay the street's own (the shared code takes them from the footprint); every footprint cell
  is kept as a barrier (`roof_line_cells_kept`: the cells of rooms whose rectangles all came out blind).
- **Merged top portals** (2026-11-01, `merged_top_portals: true`; CITY_PLAYBOOK "The open air" step 3,
  [CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md) "Result of proposal 3") replace this file's
  cover: the shared plain cover's 1 020 rectangles become **158 convex top portals** (at most 9 corners), which never
  run over a house's air or a strip covered by a sky face. **224 -> 213 portal faces, 11 830 -> 11 792 faces,
  16 017 -> 16 261 vertices** (the only city whose non-portal faces changed too: the barrier cells now come from the
  shared code; not traced further). On the 20 street poses of the v05 tour (before: the 2026-10-31 build,
  `output/mm9_rework/portals_1101/arslegard/before_oldtex`; after: `.../after`): traversal nodes median 14 -> 17, max
  76 -> 69; portal link tests median 1 658 -> 2 084, max 9 872 -> 8 001: about even, the grown rectangles were already
  few. **The library (i05) and Njam lane (s19) no longer reach the air over the roofs:** the grown rectangles ran over
  the library's high hall, so its sector counted as open to the sky, took the daylight and drew the roof room behind
  its solid ceiling. Now it is an interior lit by its own lights, darker than before (mean brightness 135 -> 105 at
  i05). The first merged build (2026-11-01 afternoon, before the sky-face rule) had 405 top portals and 460 portal
  faces; this one was rebuilt the same evening. All 32 images compared in 16 x 16 blocks: no hole, only the new x4
  textures and the library's light. Scenarios doors_exits, ladders, scripted, shops pass.
- **The air flood leaked** (48 M voxels to the grid border) through a 32 LT Invisible.dtx strip between a hollow house's
  stucco and its roof (LT 4608..4864, 208..240, -13216) into the house's floorless inside and under the whole city
  (`tools/leak_path.py`). Invisible vertical strips above LT 150 (7) are solid for the flood only (`edit_polygons`,
  restored before the faces are assigned).
- **Floors and ceilings cut at the walls on them** (`split_at_walls`, as Thjorgard's and Thronheim's): MM9 lays one
  polygon over a block (the armour shop, Njam's house and the street between them share a 651 762 LT² floor; the
  weapon shop's ceiling ran on over its neighbours and showed the sky in review v03). Every horizontal face of
  8 000 LT² or more is cut by each vertical wall standing on it or reaching up to it, any direction (2 402 extra
  pieces); the largest face left mixed between rooms is 50 039 LT² (a wood ceiling, 3 samples of 11 in a second room).
- Plan: `work/rooms_street.png`; per view the renderer draws a median of **4 sectors** (max 15).

## Sky and minimap

- **Sky**: MM9's 402 `skymarker` faces (the lid at LT 1 280, the walls of the shell, the floors outside the city
  walls) carry `IndoorSky`; the scene opens to the sky (`sky: {mode: open, sky_texture: plansky3}`, the old import's
  sky): our Enhanced outdoor sky with the game's time of day. MM9 itself shows its Arslegaard sky box here (the cube
  the Hall of the Gods draws on its six sky faces) with no time of day (no TOD_Sky in this DAT). Review:
  `review/sky02_sheet.jpg` (06:30, 12:00, 19:30, 23:30: dawn, noon, dusk, stars over the temple square and the park).
- **Minimap**: MM9's painted city map (`ui/maps/arslegardcity.pcx`, catalog entry kept, bounds moved by the offset).
- **Daylight** (2026-10-31, CITY_PLAYBOOK "Daylight and fog"): `city: {daylight: true}` (MM9's StaticSunLight on the open
  sectors) and `map: {fog: lithtech}` (no effect: Arslegard has no fog in MM9). Review: `review/dl_1031/` (the gate
  start and the north street at 12:00 and 23:30, `review_tour_dl_1031.yml`): lit streets at noon, dark at 23:30.
- **Street lights** (2026-11-01, CITY_PLAYBOOK "Street lights and BrightScale"): `map: {bright_scale_lights: true}`,
  rebuilt: 29 of 55 kept lights take colour x BrightScale (x 0.6-0.8). No fog, so no `follow_daylight`; the scene is
  unchanged. Review: `review/bs_1101_sheet.jpg` (the same two views at 12:00 and 23:30). All four scenarios pass.
- **Ladders** (2026-10-31, `overrides.yml` `ladders`): the temple front's Ladder6 and Ladder7, upright, on the inner face
  of the front wall in the two towers, from the towers' upper floors (LT 176) to the gallery over the door (288). Those
  floors are reached from the temple's balcony (the ramps inside the temple climb to it) through a doorway in each
  tower's back wall; the bays under them open on the porch (LT 32). `scenario_ladders`: from the balcony, each ladder
  climbed to its top exit. Walking on from the top exit runs off the gallery's edge back down the shaft (as in MM9's
  open gallery). Two outside portals at 512 (10859, 10863) reach 41-82 units into the south tower: a pose set on its
  upper floor lands on the porch below (walking in is fine); not fixed here.

## Content

- **People** (36 actors): 34 townsfolk and shopkeepers from the old import's NPC records (names, rows, RUDE ids) with
  MM9's bodies, standing where MM9 placed them; Hanndl twice (the talking gatekeeper Hanndl1 by the start, RUDE 334, and
  the cinema's Hanndl behind the gate's peephole); Sven Forkbeard (RUDE 3, shown with key 102 until 104); Njam the
  Meddler (row 9261, not hostile until his chase). Every friendly actor takes a peasant family's relations (`ally`):
  Hanndl's picture row (555 Guard C) refused to talk otherwise (the Hall of the Gods' lesson).
- **Walk-in shops**: the shopkeepers stand in their shops; a click opens their RUDE dialogue and its service row opens
  the shop (scenario: the weaponsmith Talik the Fist and the armourer Grim Olfassen). Shop hours are not scripted in
  this DAT (no ForadWorld ScriptObject).
- **Decorations**: 419 (props project); no chests: the DAT has no TreasureChest or TreasureBag.
- **The bank's bars** (`thjorbars` in an invisible shell): the shell is dropped and the bars are an untouchable two-sided
  cut-out (The Arena's route), so the teller behind them takes clicks; the counter keeps the party out.
- **Doors**: 30 movers: MM9's swing doors (`rotate`, pairs open together); the Thousand Terrors' double door and Njam's
  back door locked (a click says so); Njam's front door opens with Njam's Key (item 576, Doorlock.scr); Njam's own door
  unlocks with his chase; the Great Gate (RotatingDoor0/1, Speed 5) unlocks with WritMan.scr; the peephole (Door0) and
  the library's counter flap.
- **Exits** (`map_transitions.txt`, rows moved by the offset): ExitTrigger0 to the Bath House (reached down to the top
  step: `exits: bottom_lt -160`, MM9's volume ended 1 unit over it), ExitTriggerHall to the Hall of the Gods,
  ExitTrigger1 to the Thousand Terrors (in front of the locked double door), ExitTrigger4 to Thjorgard (inside the
  Great Gate), ExitTrigger2 to the Dark Passageway (high outside the gate, out of reach: FateMan.scr fires it),
  ExitTrigger3 to Thjorgard (MM9's catch volume in the chasm through the city, whose floor is sky at LT -320: a party
  that falls in lands in Thjorgard; the old import made no row for it, this map adds `mm9:transition/arslegardcity/638`,
  a copy of ExitTrigger4's destination with its own volume reached down to the chasm floor: `convert.py`
  `add_catch_row`).
  **Starts**: the old map's four (BathHouseExit, StartPoint0 the default, HallOfTheGodsExit, 1000TerrorsExit), on their
  floors, facing MM9's 90 - ry.
- **Transitions, both ways**: from the Bath House (Bathhouseexit), the Thousand Terrors (1000TerrorsExit) and the Hall of
  the Gods (HallOfTheGodsExit) into this map. **Great Gate**: no
  transition row names `greatgate` (that DAT is an unused cinema copy; its scene lives here, below), so no row needed a
  BLV target. Thjorgard's own exits do not lead here (MM9 sends a dead party to Arslegard). Town Portal: MM9 has no
  Arslegard portal location (StartPoint0 is the default arrival).

### Scripted objects (`citylua.py`)

| Script | Native |
| --- | --- |
| FateMan.scr (Fateman, Fateman0: the Great Gate cinema on the first arrival) | about 3 s after an arrival without key 98 the cinematic `gate_fate` ("Cinematics"): key 98, the peephole, Hanndl09-15 with the party's lines, 46 000 experience (as capped by the quest XP profile), then `trigger ExitTrigger2`: the move to the Dark Passageway (its row's arrival) |
| WritMan.scr | with the Writ shown (key 100) and not 9515 the cinematic `gate_writ`: key 9515, the peephole, Hanndl16/17b, 170 000 experience (capped), the gate's Hanndl removed, the Great Gate unlocked and opened (it closes after MM9's CloseWaitTime, a click reopens it); on later loads Hanndl stays removed |
| LoseCam1-3.scr, Hanndl.scr | the two cinematics' cameras and Hanndl's speech ("Cinematics") |
| LoseMan.scr | the "turned away" scene, pre-rendered as LoseGame.bik: MM9's game over (cshell.dll game.cpp 0x100a4e50) for a defeat before Chapter III (keys 97, 29) or between Hanndl's refusal (98) and the Writ (100); no `Lose` message reaches the script. Carried by the engine: world.yml `partyDeath` `when`/`otherwise` (the movie, then the autosave); the other defeats wake at StartPoint0 without a movie |
| NjamChase.scr (Njam, Trigger0 in his house) | the pad (or a hit on Njam) with key 108 and not 470: Njamdoor unlocked, key 470, 226 000 experience, the quest sound, Njam hostile (group bit) and his behaviour told "Chase" (`evt.TriggerActor`: njam.lua's njamchase.scr mode hunts the party; 2026-11-06 audit); removed on load once done |
| NPC334.scr (Hanndl1) | the click: Gungnir's errand (353) with Gungnir (item 189) gives 354; the exit: 356 without 357 takes Gungnir, 40 000 gold, 5 000 experience (357) |
| NPC3.scr, United.inc (Sven, "Arslegard") | shown with 102 until 104; the click: the five clans (82, 38, 51, 63, 74) give 178; the exit: GoGetEm 486, Thjorad 163 (12 000, 6 000, item 197 taken), Refinery 177 (68 004, 3 000), United 179 (26 500, 6 000), Lifesaver 235 (5 000, 10 000) |
| Doorlock.scr 576 (NjamDoor0/1) | Njam's Key opens them; without it they are locked |
| GiveTake.scr 575 1 (Prop8) | Njam's Struggle (a letter), a world item (`dungeon/pickups.py`) |
| BookLetter.scr (Prop84, Prop85, Prop87) | the Bill of Sale (479), the Letter to Rocnir (481), Wanted Winemakers (482) |
| Book.scr (Books0-4), PropAnim.scr (the pickaxes `onside`: posed decorations) | cosmetic |

Left out, written down: MM9's ambient sounds; townsfolk wander rails and schedules.

## Cinematics

The Great Gate scenes are in-engine camera cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md), built by
`gate_cinematics.py` (`scenes()`), whose Lua `citylua.map_script` appends (the shared `cutscenes.lua_block`) and whose
`arslegardcity.cinematics.yml` `convert.py` installs after a conversion. The arrival poll's third tick (about 3 s,
MM9's `wait 1 .1 OnLose`, fade, `wait 1 2 OnStart`) calls `MM9Cinematic.start(...)`; each cinematic begins at MM9's
:OnStart, from black.

| Cinematic | Events | Length | Shots | Steps (map events, once; also on a skip) | Cues |
| --- | --- | --: | --- | --- | --- |
| `gate_fate` (FateMan.scr) | done 36000, steps 36001-36005 | 71.2 s | Losecam4 still 0.2 s, then to CameraMarker0 at 100 (8.0 s); Losecam2 to CameraMarker2 at 150 (5.0 s); Losecam3 at the peephole | key 98 (0 s), Door0 open (14.1 s) and shut (69.2 s), 46 000 experience and ExitTrigger2's move (71.2 s) | fades, the drawer sounds, Hanndl's clips Sc4Hanndl09-15 with Hanndl09-15.wav at their Speak keys, the party's lines 01-04 and 06, quest.wav |
| `gate_writ` (WritMan.scr) | done 36050, steps 36051-36055 | 27.9 s | Losecam1 still 0.2 s, then to CameraMarker0 at 100 (7.7 s); Losecam2 (5.0 s); Losecam3 (7.2 s); Losecam5 still 3 s, then to Losecam6 at 100 (7 s); 1 s of the party's view fading in | key 9515 (0 s), Door0 open (13.7 s) and shut (18.9 s), 170 000 experience (19.9 s), Hanndl removed and RotatingDoor0/1 opened (20.9 s) | fades, letterbox, the drawer sounds, Sc5Hanndl16/17 with Hanndl16 and Hanndl17b.wav, the party's line 01, quest.wav |

- **Timing**: speech-timed as MM9: PlayAnim ends from the HANNDL.abc lengths (`Done`, `Close`, OnSpeak14), voices at
  the animations' SpeakN keys, the party's lines and Hanndl14/16/17b by their wav lengths (MM9 VOICES/CINEMA, now
  imported as `worlds/mm9/audio/voices/cinema/`); camera arrivals = distance / speed. Cameras keep their DAT rotations
  (MM9's Target does not aim), fov 73.7.
- **MM9's bug kept**: FateMan.scr :OnDone sends counter 5 to OnPC6, so the party's line 05 never plays.
- **The party's voice**: MM9 picks one of 18 cinema voice sets by the first PC (getPCVoice); our party has MM6-MM8
  voices with no such set and a cinematic's timeline is fixed, so it is one set, `PARTY_VOICE_SET` 11 (AssertiveMale).
- **No subtitles**: MM9 has no text of these lines (only Hanndl.scr's abridged comments).
- The status-line stand-in (FATE_LINES) and its exit prompt are gone; the exit now moves at once (MoveToMap picture 0).
- **Test without a conversion**: `python3 level_generation/projects/mm9r_arslegardcity/cinematics_pilot.py` writes the
  yml and the installed map Lua as the converter now writes it into `output/mm9_rework/cinematics_pilot_root`; then
  from `output/mm9_rework/cinematics_pilot_run`: `build/game/openyamm --world mm9 --headless-run-scenario
  <project>/cinematic_gate_{fate,writ}_{play,skip}.yml` (all four pass, 2026-11-06; `scenario_scripted.yml` too).
  Captures: `output/mm9_rework/cinematics_pilot_run/captures_gate_fate/`, `captures_gate_writ/` (tours
  `tour_gate_fate.yml`, `tour_gate_writ.yml`; `sheet.jpg` each).

## Quality gates

1. **Every DAT world model has a rule** (83 + PhysicsBSP); skipped with reasons: the sky box, 4 AI barriers, the 4
   fountain water volumes (their surfaces are WorldObject7/8; since the shared water rule, 2026-11-06, the four are
   scene `water_volumes`, 61-92 deep: decorative fountains the party wades, `scenario_swim_check.yml` passes), VisBSP, the 2 ladder volumes (Ladder6/7: built as scene
   ladders, "Ladders" above; their feet stand on the towers' upper floors at LT 176, not over the porch), AI tracks.
2. **Sealed air**: `leaked_to_border` false (after the wall-strip seal), 1 air component (20.3 M voxels).
   248 faces without air in front dropped (`work/dropped_faces.json`: walls between brushes, the hollow houses'
   insides, facing out).
3. **Every portal joins two rooms**: `portals_without_two_rooms` 0.
4. **No holes**: the 32-view sheet (`review/v05_compare.jpg`) shows none. v03 showed the weapon shop's ceiling open to
   the sky (fixed: `split_at_walls`); two v03 views stood inside MM9's hollow houses (moved). Floor holes 0; 2 cracks of
   10 units (4 x 4 LT pieces at the library counter's step corners, room 26). Floor check 16 499 LT².
5. **Review sheet**: old ODM import (view distance unlimited) | native BLV, **32 eye-level views** (20 streets,
   squares, the park, the gate path; 12 interiors): same geometry and textures; ours draws the lamps brighter (classic
   vertex light) and the stand-in townsfolk.
6. **Walkability** (`work/audit.log`): 370 steps and 28 flights (MM9's stairs and step ramps over the monsters' 40-unit
   path step), 8 unreachable regions (building plinths and terraces 41-111 over the street, the counters), 14 mover
   notes (door frames and sills), 0 actor notes, 4 pits for monsters: the west half's streets (the chasm's bridges are
   barred to MM9's AI by its AIBarriers too; the bridge decks climb 158), the park (hills inside the lawn; its edge is
   flush with the street, 1-10 units along LT z -12 720..-8 720) and the terrace and court before the
   Hall of the Gods' gate. The party: the ramp to the Hall court (LT x 6 432-6 624, rising south
   from LT 0 at z -12 288 to 128 at z -12 800, 14 degrees) climbs +328 at its west edge, middle and east edge
   (`work/probes/hall_ramp.yml`, yaw 270); a first probe that walked east into the ramp's side wall (MM9's
   Lightstone4 triangle at x 6 432) read as two blocked ramps: there is one ramp and nothing to fix, into and out of the park, across the north bridge (`pits.yml`). The 7 half
   steps (`stats.city_half_steps`): a forward walk climbs 46-64 onto each (`work/probes/half_steps.yml`).
7. **Scenarios pass** (headless, real clicks where the engine picks): `scenario_doors_exits` (37 steps: the tavern's
   double door stops the party, opens on its click and the party walks in; the Thousand Terrors' door stays locked;
   the party walks into ExitTrigger0, ExitTriggerHall, ExitTrigger1 and ExitTrigger4 and falls into the chasm:
   ExitTrigger3), `scenario_shops` (27 steps: the weaponsmith's and the armourer's dialogues by press_interact,
   their service rows open the shops), `scenario_scripted` (65 steps; FateMan: key 98 at 3-4.5 s, gate_fate playing, the
   move to the Dark Passageway at its end; WritMan: 9515, gate_writ playing, the gate opening at its FadeOut2; Njam's chase: 470, Njam hostile, his door; Njam's front door locked, then
   opened with the key; Hanndl's dialogue
   (interact_actor: his 3D-model row takes no headless click); Sven by key 102; a letter; Njam's Struggle into the
   packs), `scenario_ladders` (Ladder6 and Ladder7 climbed to the gallery). No chest scenario: no chests.
8. **Starts**: four, each on its floor (`build_report.json` `starts`); the first view of the tour is StartPoint0.
9. **Compiler unit tests**: not rebuilt (no compiler change).
10. **Lights**: 55 BLV lights, no floor point under more than 4.

## Performance (counts; frame rate needs a single-session run)

Same 32 views, `logging.performance_trace` + `logging.indoor_visibility`, minimized isolated desktop runs on a shared
machine.

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Visibility build, max |
| --- | --: | --: | --: | --: |
| **Arslegard City, native BLV** | **212 / 467** | **30 500 / 89 500** | 4 / 15 | 0.9 ms |
| Arslegard City, old ODM import | 737 / 1 002 | 80 200 / 156 000 | – | – |
| Arslegard City, BLV before the top-portal change (v03) | 202 / 400 | 28 700 / 89 400 | 4 / 11 | 15.6 ms |

- **Map load** (median of 3, `OPENYAMM_MAP_LOAD_TIMING=1`, a loaded shared machine): BLV **1.56 s** (asset load 0.55 s)
  against the old ODM 5.03 s (1.69 s). Logs `work/perf/load_*.log`.
- Textured batches drawn: median 120, max 306. Logs `work/perf/blv_v05.log`, `odm_v05.log`.

## Converter and engine

No change. Map-local in `convert.py`: the frame offset wrappers, the chasm's catch row, the wall-strip seal, top
portals over solid, the
floor and ceiling splits, the bank's bars, peaceful relations.

## Open items

- FateMan's move to the Dark Passageway happens on any first arrival here (MM9's own rule: its arrival is death); a
  game that lets a living party walk in from the Bath House first would send it on. No death-to-Arslegard flow exists in
  OpenYAMM yet, so how the party first reaches Arslegard is a game-flow question for the user.
- Townsfolk are stand-in peasants until the MM9 town NPC bodies exist; no ambient sound.
- The sky is our time-of-day sky with plansky3, not MM9's fixed Arslegaard cube (the Hall of the Gods shows that cube).
