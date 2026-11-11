# MM9 rework: Drangheim City (`drangheimcity.blv`)

MM9's Drangheim City (the low town round the temple, the inn and the town hall inside its walls; the hill district
west and south with the warehouse, the spell shop and Klusos House; 16 walk-in shops, houses and halls; reached from the
Drangheim wilderness, from Klusos House by its door and its window, and by Town Portal) converted from its DAT world into
a native **indoor map (BLV) open to the sky**, the second of MM9's seven cities after the Sturmford City pilot
([CITIES_ROLLOUT.md](../../../devdocs/mm9_rework/CITIES_ROLLOUT.md)). Built on the shared converter
([DUNGEON_PLAYBOOK.md](../mm9r_common/DUNGEON_PLAYBOOK.md), [CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md)) with
no change to it; installed in the review root `output/mm9_rework/assets_dev`. Props:
[`../../props/mm9_drangheimcity_claude/`](../../props/mm9_drangheimcity_claude/README.md).

Status 2026-10-31 (unattended): **the city works as a BLV.** Geometry (terrain, walls, 19 walk-in interiors behind door and window portals), the Enhanced sky with the time of day behind MM9's sky box, MM9's painted city map as the minimap, 39 townsfolk with their RUDE dialogues (walk-in shops open by real clicks), 201 decorations, 33 doors, the scripted objects as native Lua, the three exits and four starts, transitions both ways (Drangheim wilderness, Klusos House), the half steps of the settled raised-floor rule, the three ladders (the leaning one to the north wall's walkway climbed
along its line since 2026-10-31, up and down). Classic lighting (no bake).

## Build and review

```sh
python3 level_generation/projects/mm9r_drangheimcity/convert.py --plan     # rooms only: work/rooms*.png (9 min, 2 GB)
python3 level_generation/projects/mm9r_drangheimcity/convert.py            # build, compile, install (10 min)
python3 level_generation/projects/mm9r_drangheimcity/make_scenarios.py
for s in doors_exits shops scripted ladders half_steps; do ./build/game/openyamm \
    --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_drangheimcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_drangheimcity/make_tour.py v11 [--original]
level_generation/projects/mm9r_drangheimcity/work/perf/tour.sh v11 blv     # and `odm`: tours with performance traces
python3 level_generation/projects/mm9r_common/dungeon/sheet.py level_generation/projects/mm9r_drangheimcity/review/v11 \
    level_generation/projects/mm9r_drangheimcity/review/v11_original
python3 level_generation/projects/mm9r_drangheimcity/work/perf/counts.py work/perf/blv_v11.log work/perf/odm_v11.log
bash level_generation/projects/mm9r_drangheimcity/work/perf/loads.sh                # map load, 3 x BLV and ODM
python3 level_generation/projects/mm9r_drangheimcity/work/sector_stats.py           # faces, sectors, faces per sector
```

The old ODM import runs from a private hard-linked copy, `output/mm9_rework/drangheimcity_original_root` (its
`worlds/mm6-8/models/actors.yml` are the committed ones: other sessions' unfinished tables stop the game). When another
session's map Lua in the review root is broken (`thjorgardcity.lua` at 19:27 stopped every game start), `tour.sh`
takes `BLV_ROOT=<a private hard-linked copy without that file>`.

Play: `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city --visible --world mm9 --map drangheimcity.blv
--assets "$PWD/output/mm9_rework/assets_dev" --seconds 3600`.

## Numbers and limits

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame: transitions, the painted map's bounds and
  the props' fit stay valid). Extent x 5 898..22 610, y -13 107..5 898, z -778..3 727: **inside ±32 767**.
- 8 428 source polygons (PhysicsBSP 6 470 with the terrain's 1 637 and the world objects) -> 7 676 merged ->
  8 887 native polygons -> **11 258 compiled faces, 16 202 vertices** (10 731 and 14 882, with 217 portal faces, since the merged top
  portals of 2026-11-01) (BLV indices are 16-bit: **25 % of 65 535**;
  no widening), 744 portal faces, 33 doors (movers), 54 BLV lights (13 MM9 fill lights over the four-per-point cap
  are bake-only and unused without a bake), **0 outlines** (painted minimap), 50 sky faces, 42 translucent faces (the
  window panes; under the 1 500 warning).
- **37 sectors**; faces per sector **max 5 455, median 55**. The largest is the air over the roofs, which here
  also holds the whole hill district (below).
- Voxels: 16 LT, 412 x 114 x 468 = 22 M cells, 17.3 M air before the underground was taken out (below), 2 GB peak, 60 s
  for the geometry pass; a full build 8-10 minutes, of which the city structure's labelling is most.

## Structure: sectors and portals

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors (inn and tavern, temple, town hall, bank, blacksmith, training hall, the settlers' houses, the warehouse, the spell shop, the small houses, the mayor's upper floor, Klusos House's window room) | 19 rooms | behind 10 MM9 UserPortals, 8 door-leaf portals and one rect portal (the town hall, below); their windows are **27 glass portals** |
| The low town's street air (under the roof line) | 1 room | one plaza round its buildings: no corridor for an automatic street cut |
| The air over the roofs, with the hill district | 1 room | joined to the low town by **141 merged top portals** (convex polygons over walls and roofs, `merged_top_portals`, 2026-11-01; were 679 roof-line rectangles) |
| The tower's shaft (open at its top) and pieces of the void outside the walls | 16 rooms | 13 street cuts, all but one in the narrow gaps between the terrain's edge and MM9's sky box (harmless, never seen) |

**The roof line** sits at 400 LT, under the low town's eaves (streets 144-250, roofs 468-596). The hill district west and
south (ground 340-900, the warehouse, the spell shop, Klusos House, the small houses) rises through it into the air over
the roofs. `street_box_lt` (Thjorgard's) was tried (v04) and does not fit: the low town runs up the hill with no wall or
gate between them, and its streets joined the air over the roofs round the box's edge (3 street rooms, 417 blind
rectangles). So the structure here is mostly the interiors behind their doors; per view the renderer draws a median of
**4 sectors** (max 12).

**Merged top portals (2026-11-01, `merged_top_portals: true`; CITY_PLAYBOOK "The open air" step 3,
[CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md) "Result of proposal 3").** The 679 rectangles
become 141 convex top portals (at most 13 corners; rebuilt with the final converter on 2026-11-01 evening; the afternoon build predated the sky-face rule): **744 -> 206 portal faces, 11 258 -> 10 720 faces,
16 202 -> 14 840 vertices**; only the portal faces change. On the 20 street and hill poses of the v11 tour (before: the
2026-10-31 build, `output/mm9_rework/portals_1101/drangheim/before_oldtex`; after: `.../after`): traversal nodes median
108 -> 37, max 256 -> 87 (**cap hits 1 -> 0**); portal link tests median 49 800 -> 4 534, max 96 913 -> 9 195. Sectors
drawn equal except s19 (6 -> 9, at the cap before). All 32 images compared in 16 x 16 blocks: no hole, only the new x4
textures. Scenarios doors_exits, half_steps, ladders, scripted, shops pass.

**Map-local geometry fixes** (`convert.py`, `terrain.py`; the shared converter is unchanged):

- **The air under the terrain** (`terrain.py`). MM9's sky box is one L-shaped box from LT y -304 to 1 456; the terrain
  (`Terrain0`, built as static, Lindisfarne's route) does not reach its walls, and north-east and west of the town walls
  there is no terrain at all (a void down to the box's floor). The air flood ran from over the walls into the void and
  under the whole terrain (4.7 M voxels, a third of the air). `prune_underground` (in `Hooks.extra_portals`, after the
  flood) takes out every air voxel under the terrain surface of its column and keeps only the seeded components
  (0.55 M more voxels of pockets under paved streets and floors). Two DAT lights stood under the terrain (Light12,
  Light26; MM9 hid them in the hill). A slope-dependent margin was tried (v02) and gave white seams at every wall's foot.
- **The town hall's door** (overrides `rect_portals`, `skip_user_portals`): MM9's portal (top 416 LT), which the converter
  shifts to the leaves' hall side, lay in the arched recess over the door (open to 502 LT); the hall leaked round it into
  the street and was cut by a street cut and the roof line. A rect portal at the doorway's narrow street side instead;
  the pair is clicked by its own event (`citylua.TOGGLE_GROUPS`).
- **Interior faces given to the open air** (`interior_faces`, a wrapper of `assign_faces` for this run): thin walls under a
  voxel, where the shared nearest-voxel assignment gave an interior's faces to the open air outside: sky through the
  blacksmith's chimney and the town hall's upper walls in v03. After the assignment, a face in an open-air room whose air
  straight ahead (1-2 voxels along its normal) is an interior in 60 % of its samples goes to that interior (49 faces), and
  a wall that sees an interior below a height and the open air above (the tower's outer wall rising out of the town hall)
  is split there (45 cuts faces; `work/interior_faces_moved.json`).
- **Burning logs** lifted onto their hearths (MM9 sinks them 15-31 units; sunk they did not draw).

`work/rooms_street.png` and `work/rooms_upper.png` show the rooms; `work/city/` holds the analysis scripts (`ground.py`,
`roofs.py`, `leak_path.py`, `leak_portals.py`) and `work/raycast.py` finds the BLV faces behind a pixel of a tour shot.

## Sky and minimap

- **Sky**: MM9's 10 `skymarker` polygons (the walls, lid and floor of the sky box) are faces with `IndoorSky`; the scene
  opens to the sky (`sky: {mode: open, sky_texture: plansky3}`, the old import's sky) and the Enhanced outdoor sky with the
  game's time of day draws behind them. Review: `review/sky01_sheet.jpg` (06:30, 12:00, 19:30, 23:30). MM9's map fog
  (WorldProperties) comes over automatically (scene `fog`): far walls read hazier than the old import's capture.
- **Daylight and fog** (2026-10-31, CITY_PLAYBOOK "Daylight and fog"): `map: {fog: lithtech}` (MM9's fog model) and
  `city: {daylight: true}` (MM9's StaticSunLight on the open sectors). Review: `review/dl_1031/` (the west gate and
  TowerLadder1's slot at 12:00 and 23:30, `review_tour_dl_1031.yml`): lit streets at noon, dark at 23:30; the
  half-timbered house wall by the west gate stays about as bright at night as at noon (not investigated).
- **Street lights and night fog** (2026-11-01, CITY_PLAYBOOK "Street lights and BrightScale"):
  `map: {bright_scale_lights: true}`, rebuilt: 47 of 54 kept lights take colour x BrightScale (x 0.3-0.8, median
  0.6). The rebuild also writes `fog: {follow_daylight: true}` (`city/hooks.py`, devdocs/INDOOR_FOG.md "Fog by the
  daylight"): the grey day fog darkens with the daylight through the evening; at 23:30 MM9's black night fog rules as
  before, and noon is unchanged. Review: `review/bs_1101_sheet.jpg` (the same two views at 12:00 and 23:30); the
  west gate's house wall still reads bright at 23:30. All five scenarios pass.
- **Minimap**: MM9's painted city map (`map: {painted_minimap: true}`); no outlines are compiled.

## Content

- **People** (39 actors, all friendly, all with RUDE dialogues): the old import's NPC records (names, rows, RUDE ids) with
  MM9's bodies (each object's model's initial dims x Scale); its actor for the AmbientSound "Dog0" was an importer slip and
  is not carried. Townsfolk stand where MM9 placed them (no wander rails, no `MM_DrangheimCity.scr` schedule: it is not
  referenced by the DAT). Sigmund (row 403, Swordsman) and Guaire (9101, Bandit) take a peasant family's relations so a
  click talks to them.
- **Walk-in shops**: the armourer Fintan A'Dlinn (97), Rannveig Olafsdotir (98), the spell shop's Daonai A'Norta (99), the
  bank (100), the innkeeper Thorkatla (101), the healer Louhi (102), the training hall's Skuli (105); a click opens the
  dialogue and its service row opens the shop. Shops close from 20:00 to 06:00 (key 5017).
- **Doors**: 33 movers (MM9's swing doors, `rotate`, pairs together); 5 locked groups that never open (Klusos House's
  front door, a locked house, the smith's shack, the stair door, the tavern's back door): a click says so.
- **Chests**: none (no TreasureChest or TreasureBag in the DAT).
- **Ladders** (scene `ladders`): the tower's (TowerLadder, 169-1206 LT to its top platform), the small house's (HouseLadder,
  to its loft; diagonal, `convert.py DIAGONAL_LADDERS`) and the leaning ladder to the north wall's walkway (TowerLadder1,
  2026-10-31). TowerLadder1 leans 170 LT over its 374 LT rise through a slot in the walkway, its foot under the walkway's
  landing: climbed straight up, the party's head met the landing's underside 72 LT under the walkway, and no vertical
  line in the slot clears the rails and the walkway's edges. The scene keeps MM9's leaning line (bottom and top from the
  rung face, `DIAGONAL_LADDERS`) and the engine climbs a ladder whose top is not above its bottom along that line
  ([leaning ladders](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md)): the party clears the landing about a
  third of the way up. Its top exit is on the walkway beside the top (LT 6768, 922, -3258), and `grab_at_top` lets a
  party walking from there toward the top take the ladder and climb down: the way to the street for one arriving by
  Klusos House's window.
- **Exits** (`map_transitions.txt`): ExitTrigger0 at the west gate to the Drangheim wilderness, ExitTrigger2 in front of
  Klusos House's locked door (MM9's way in) and ExitTrigger1 in Klusos House's window at the end of the north wall's
  walkway (its box reaches 48 LT onto the walkway and down to its planks: the window frame keeps the party's centre out of
  MM9's 16 LT box; `grow_exits`, `exits: bottom_lt`). **Starts**: the four of the old map (Klusos House's window and
  door, Town Portal, the west gate), on their floors, facing MM9's 90 - ry.
- **Transitions both ways**: the wilderness's ExitTrigger0 arrives at StartPoint0 on its floor; Klusos House's two exits
  arrive at KlusoDoorExit and KlusoWindowExit (both BLVs); the city's exits name `klusoshouse.blv` and `drangheim.odm`.
  **Drangheim Prison has no exit into the city** (its two exits and their two arrivals are the wilderness's): its rows
  are untouched and consistent. **Town Portal**: map_stats row 9005 names the BLV and the TownPortal start stands on its
  floor; MM9 has no Town Portal destination table in the engine yet (PLAN phase 4).
- **Letters**: the four BookLetter scrolls show their texts (rows 454, 455, 457, 458); the book (Book.scr) has no text.
- **Decorations**: 201 (props project), 0 pads.

### Scripted objects (`citylua.py`)

| Script | Native |
| --- | --- |
| BankOrb.scr (Hlif Ingimundssen, RUDE 100) | the Orb of Linking: key 330 on a click with the orb (after 322), the exit places it (334 -> 325), six orbs: 337, 20 000 xp, 15 000 gold |
| NPC87.scr (Sigmund the Stressed, Jarl, RUDE 87) | the click: the five other clans' keys give 178 (United.inc); the exit: 489 + item 596 (44), the gossip 300 (55: 5 000 xp and gold), Fort Stenig 171 (49), Crona Kiga 170 (50, item 390 taken), the clans united 179 (83); away while 40 unless 108. **Deviation** (the user, 2026-11-08): the exit also gives 50 to a party that took the Kiga before the task (169), said "We've already retrieved that." (46) and carries it; MM9's rows give 50 only on the 48 path, so such a party could never report the Kiga or get Drangheim's pledge |
| NPC88.scr (Atli the Quick, RUDE 88) | the Assassin's trial (226): 227, 63 000 xp, 5 000 gold, characters holding 405-408 promoted to Assassin |
| NPC89.scr (Keith Bloodaxe, RUDE 89) | 137 (136): 24 500 xp, 5 000 gold, characters holding 413-416 promoted to Crusader |
| NPC95.scr (Guaire A'Velsi, a Bandit) | hidden until Atli's task (222), 300 hit points; his death gives 225 (kill hook) and he is gone for good |
| NPC110.scr / NPC109.scr (Hrolf and Alfrigg) | Hrolf's FoundPlayer starts their quarrel, the cinematic `dwarves_and_humans` (key 5010), then they fight; Hrolf at HrolfMarker on later loads ("Cinematics") |
| NPC378.scr (Thorolf, two copies) | as in Sturmford: talking to one removes the other; the message (84) or summons (107) vanish him; 83/106 reopen the dialogue |
| NPC414.scr (Nicolai Ironfist) | gone to Guberland on key 121 |
| Retainer.scr (Edina A'Mor 456, Beagan A'Ghrie 455) | hidden while hired |
| ForadWorld.scr | location key 1027 (1024-1033 cleared), shop hours 5017 |
| TownPortal.scr "Drangheim" | cleansing the altar: key 5013 (the dirty altar hides and its clean twin `mm9_portalclean` at its place shows, also on load: `../mm9r_common/dungeon/town_portal.py`) |
| BookLetter.scr | the four letters |
| NPC96, shopkeeper.scr, Book.scr, PropAnim.scr | cosmetic (voices, animations); not carried |

Left out, written down: MM9's 17 PerceptionBrushes (red hints on doors; no gameplay hangs on them here); the drinkable Barrels (no native MM9 barrel event
yet); NPC voices on a click; ambient sounds.

### Cinematics

`dwarves_and_humans` (`drangheimcity.cinematics.yml`, built by `citylua.scenes()`, installed by `convert.py`): Hrolf
and Alfrigg's quarrel (NPC110.scr :OnStart..:Trigger8, NPC109.scr), an **ambient** cinematic (no camera, letterbox or
input lock, as MM9 plays it on the street). Hrolf's FoundPlayer event (56326 = 56000 + his DAT index, raised when he
first perceives the party) starts it without key 5010; it replaces the old 1-second proximity poll (which also moved
Hrolf to his marker at once; MM9 moves him there only on a later load, :Init).

- Timing: the scripts' fixed waits (not the wav lengths): Hrolf 01 at 0, Alfrigg 02 at 5.5, 03 12.8, 04c 26.1, 05
  29.3, 06 33.8, 07 34.8, :Trigger8 at 37.8 s. Cues: the seven voices (`voices\cinema\dwarvesandhumans\*.wav`),
  each speaker's Loopanim conv clip (conv1/2/4/5) and :OnStop's `stand`, both facing each other (`target`). No
  subtitles (MM9 has no text for the lines).
- Steps (events 36001-36002, done 36000): `key` (5010) at 0; `fight` at 37.8 s: the two monster rows' relations
  (9051 Hrolf's row, 9008 Alfrigg's: MM9's AddEnemy by class, close range). The kill hook 36020 resets both relations
  when either dies (:OnTargetDead RemoveEnemy). The relations are by row, so until then any 9051 and 9008 within
  1024 units fight (Krej, Seiggfreid, Fisk); MM9 also makes every CommonerDwarfMaleA Hrolf's enemy and every
  CommonerHuman2MaleB Alfrigg's, so only Krej versus the other two dwarves differs.
- Test without a conversion: `python3 cinematics_pilot.py` (scratch root `output/mm9_rework/cinematics_pilot_root`),
  then from `output/mm9_rework/cinematics_pilot_run`: `build/game/openyamm --world mm9 --headless-run-scenario
  <abs>/cinematic_dwarves_and_humans_play.yml` and `..._skip.yml`. Captures: `captures_dwarves_and_humans/sheet.jpg`
  there (`tour_dwarves_and_humans.yml`).

## Quality gates

1. **Every DAT world model has a rule** (75 + PhysicsBSP); skipped with reasons: the sky box and the star shell, the AI
   barrier, the tavern's PortalZone, VisBSP, the 3 ladder volumes, 17 PerceptionBrushes, 222 AI tracks.
2. **Sealed air**: `leaked_to_border` false; the underground taken out (above); 342 faces without air in front dropped
   (`work/dropped_faces.json`: undersides of walls and floors on the ground, wall feet under the terrain, the sealed
   courtyard south of the temple).
3. **Every portal joins two rooms**: `portals_without_two_rooms` 0.
4. **No holes**: the 32-view sheet (`review/v11_compare.jpg`) shows none. Found and fixed on the way: the town hall's
   leak (v01), a cliff face and the courtyard view (v01: the courtyard is a sealed, unseeded pocket nobody reaches; the
   view moved), white seams (v02, reverted), sky through the blacksmith's and the town hall's upper walls (v03-v10).
   Floor holes 0, cracks 0. Floor check 24 276 LT²: the tower's floor under its shaft's air (the tower's base polygon
   runs on under the hall, 12 300), the street under the roof room along the roof line (8 190) and door sills.
5. **Review sheet**: MM9 original (the old ODM import, view distance unlimited) | native BLV, **32 eye-level views**
   (20 streets, plazas and the walkway, 12 interiors): `review/v11_compare.jpg`; looked at: same geometry and textures;
   ours draws MM9's fog (far walls hazier), lacks the old import's green Perception glow on doors, and its fireplaces
   burn (the old import baked unlit logs).
6. **Walkability** (`work/audit.log`): 120 steps (60 of them 65-127 high: MM9's porch and plinth steps,
   the half steps above), 9 flights, 40 mover notes (door tops below or above the floor round them: sills and frames),
   2 actor notes (a wall within an NPC's radius), 3 regions: the low town as a whole (129 M units²) "cannot walk to the
   party start", because start 0 is Klusos House's window arrival on the walkway, reached only by TowerLadder1, which
   the audit's walk does not follow (monsters do not climb; the party does, both ways: `scenario_ladders`); a 42-unit floor by the warehouse and
   a 113-unit one in the inn (0.09 M and 0.11 M units²: a plinth and a counter-high platform) monsters do not path onto.
7. **Scenarios pass** (headless, real clicks where the engine picks): `scenario_doors_exits` (23 steps: the inn's double
   door stops the party, opens on its click, the party walks in; Klusos House's locked door stays shut; the west gate's
   exit, the exit in front of Klusos House's door and the window exit raise their transitions), `scenario_shops` (33:
   Fintan's and Daonai's dialogues by press_interact, their service rows open the shops; the innkeeper's by a click),
   `scenario_scripted` (48: 1027, 5017 at night and not by day, Sigmund's reward on closing his dialogue (a real
   click), a letter, the altar's 5013, Atli's 227, Guaire hidden, shown by 222, his death's 225, Hrolf's 5010 on
   approach), `scenario_ladders` (17 steps: the tower's and the small house's climbs; TowerLadder1 from the street onto
   the walkway, from the window arrival along the walkway to its top exit, and taken there back down to the street),
   `scenario_half_steps` (probes, below).
8. **Starts**: four, each on its floor (`build_report.json` `starts`).
9. **Engine tests** (2026-10-31, the leaning-ladder change): `openyamm_unit_tests` 2440/2440 (four new ladder cases),
   `openyamm_runtime_tests` 54/55 (the braziers case fails already), the other maps' ladder scenarios unchanged.
10. **Lights**: 54 BLV lights, no floor point under more than four.

**Raised floors** (CITY_PLAYBOOK "Raised floors", `half_steps: true`): the pass made 7 steps (14 faces,
`stats.city_half_steps`). Probes (`scenario_half_steps.yml`, forward walks from the street): the temple's east side
step lifts the party onto its raised floor (+62); three stop after the half step (+20/+31) against a wall standing on
the raised floor (a plinth's edge: nobody stands there); three on the far west hill (x ~2 950 LT, outside the town wall)
have no axis-aligned 50-66 rise for the probe and are out of reach anyway.

## Performance (counts; frame rate needs a single-session run)

Same 32 views (`review_tour_v11*.yml`), `logging.performance_trace` + `logging.indoor_visibility`, minimized isolated
desktop runs on a shared machine (`work/perf/tour.sh`, `counts.py`; logs `work/perf/blv_v11.log`, `odm_v11.log`).

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Textured batches |
| --- | --: | --: | --: | --: |
| **Drangheim City, native BLV** | **264 / 432** | **51 700 / 102 900** | 4 / 12 | 155 / 221 |
| Drangheim City, old ODM import | 644 / 779 | 51 400 / 97 200 | - | - |

- **Map load** (median of 3, `OPENYAMM_MAP_LOAD_TIMING=1`, `work/perf/loads.sh`): BLV **2.37 s** (asset load 0.83 s)
  against the old ODM 3.05 s (1.13 s). Logs `work/perf/load_*.log`; the machine ran other sessions' builds meanwhile.
- Triangles stay at the old import's level: the air over the roofs (5 455 faces, the hill district and every roof) is
  in view from every street. Draw calls fall to 41 %.

## Engine and converter changes

- **None.** The shared converter and the engine are unchanged; everything is in this project (`convert.py`,
  `terrain.py`, `citylua.py`, `overrides.yml`). No engine build, so no test runs were needed.

## Open items

- Perception hints, drinkable barrels, NPC voices, MM9's schedule: not carried.
- The air over the roofs holds the whole hill district (5 455 faces): the low town and the hill are one slope with no wall
  between them for a second roof line or a street box.
- Townsfolk draw as stand-in peasants until the MM9 town NPC bodies exist (another session's work).

## Sigmund back by his fire (2026-11-11)

`NPC87.scr :Vanish` with key 108 (he is back): `LoopAnim Sit`. `citylua.py` plays his `sit` clip, looped, facing as
placed (the fire), on the load and on the poll once 108 is held. MM9 places no chair or seat there (no DAT object or
polygon within 250 LT but the fireplace, a bed and the town portal), so he sits on air, as the script has him; captures
`output/held_items_check/b3_drang/side2_close.png`. **Open:** a stool under him would be our addition (user's call).
