# MM9 rework: Thjorgard City (`thjorgardcity.blv`)

MM9's Thjorgard City is converted from its DAT world into a native **indoor map (BLV) open to the sky**. This is
the second of MM9's seven cities, after the [Sturmford City pilot](../mm9r_sturmfordcity/README.md).

- **The city:** the walled town of shops, halls and houses; the docks gate in the south; the west gate to the
  Thjorgard wilderness; the east gate to the Arena; and north of the town wall, the hillside up to Sven Forkbeard's
  palace terrace.
- **Recipe:** the shared converter ([DUNGEON_PLAYBOOK.md](../mm9r_common/DUNGEON_PLAYBOOK.md)) and its city extension
  ([CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md)).
- **Brief:** [CITIES_ROLLOUT.md](../../../devdocs/mm9_rework/CITIES_ROLLOUT.md).
- **Install:** the review root `output/mm9_rework/assets_dev`.
- **Props:** [`../../props/mm9_thjorgardcity_claude/`](../../props/mm9_thjorgardcity_claude/README.md).

**Status 2026-10-31: the city works as a BLV.** Built and installed:

- **Geometry:** 89 sectors, with the town's streets divided under a roof line, and the hillside and terrace as their
  own open-air room.
- **Sky and minimap:** our Enhanced outdoor sky with the time of day behind the sky faces; MM9's painted city map as
  the minimap.
- **People:** 60 townsfolk with their RUDE dialogues. Walk-in shops open by real clicks.
- **Decorations and doors:** 730 decorations; 145 doors and movers.
- **Scripts and links:** every gameplay script as native Lua; the 3 exits and 4 starts.
- **Lighting:** classic, no bake.

Every scenario passes.

## Build and review

```sh
python3 level_generation/projects/mm9r_thjorgardcity/convert.py --plan     # rooms only: work/rooms*.png (~6 min)
python3 level_generation/projects/mm9r_thjorgardcity/convert.py            # build, compile, install (~12 min, 2 GB)
python3 level_generation/projects/mm9r_thjorgardcity/make_scenarios.py
for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_thjorgardcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_thjorgardcity/make_tour.py v03 [--original]    # sky01 --sky: the sky sheet
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city_thjorgard_v03 --world mm9 --map thjorgardcity.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 655 0 200 --yaw-radians 1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 200 --set logging.performance_trace=true --set logging.indoor_visibility=true \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_thjorgardcity/review_tour_v03.yml
# the original: --map thjorgardcity.odm --assets "$PWD/output/mm9_rework/thjorgardcity_original_root"
#     --set video.view_distance=unlimited, tour review_tour_v02_original.yml (the same views)
python3 level_generation/projects/mm9r_common/dungeon/sheet.py level_generation/projects/mm9r_thjorgardcity/review/v03 \
    level_generation/projects/mm9r_thjorgardcity/review/v02_original
python3 level_generation/projects/mm9r_thjorgardcity/work/perf/counts.py work/perf/blv_v03_game.log work/perf/odm_v02_game.log
bash level_generation/projects/mm9r_thjorgardcity/work/perf/loads.sh                   # map load, 3 x 2 runs
```

`output/mm9_rework/thjorgardcity_original_root` is a private hard-linked copy of `assets_original`, made the same way
as Sturmford's: its `worlds/mm6-8/models/actors.yml` are the committed ones, and the old scene allows saving.

## Numbers and limits

- **Frame:** `native = (LT.x, LT.z, LT.y) * 2.56`, no offset, which is the old map's frame. Extent x -9 011..10 322,
  y -4 260..27 034, z -225..4 751: **inside ±32 767**.
- **Polygons:** 15 593 source polygons -> 14 976 merged -> 23 857 kept after the splits -> **27 911 compiled faces** (26 678 since the merged top portals, 2026-11-01).
- **Vertices: 37 979** (34 479, 53 %, since the merged top portals). BLV indices are 16-bit, so this is **58 % of 65 535**. No widening is needed. The `--plan`
  estimate before the props and scripts work was 34 000 vertices.
- **Other counts:** 1 470 portal faces (237 since the merged top portals), 145 doors (movers), 160 BLV lights, 959 sky faces, 0 outlines (painted
  minimap), 4 liquid faces (the palace's basins).
- **Faces per sector: max 3 579, median 95.** The max is the open air over the town's roofs (sector 86). Before the cut
  over the north wall, that room also held the hillside and the palace exterior: 5 327 faces. Sturmford's max is 997;
  MM9 dungeons reach 4 800. The per-sector face grid of 2026-10-31 carries it
  ([BLV_GEOMETRY_COSTS.md](../../../devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md)).
- **Voxels:** 16 LT, 476 x 126 x 769 = 46 M cells, 13.4 M air. The geometry pass takes 40 s; peak about 2 GB.

## Structure: sectors and portals

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors (shops, halls, the bank, the library, the temple, the palace) | 67 rooms | 49 doorway portals (23 MM9 UserPortals, 26 leaf rectangles), 31 glass (window) portals |
| Street rooms (the town's air under the roof line at 224 LT) | 20 | 18 street cuts (17 automatic, 1 by hand in the north gate); 2 dropped as loops |
| Air over the town's roofs | 1 | joined to the streets by **139 merged top portals** (convex polygons over walls and roofs, `merged_top_portals`, 2026-11-01; were 1 373 rectangles) |
| Hillside and palace terrace (north of the town wall) | 1 | joined to the roof air by one archway cut over the wall (`north_wall_sky`), and to the town through the gate's street cut |

### The city's own settings (overrides.yml `city`)

- **`street_box_lt` (new, opt-in, shared converter).** The roof line and the streets cover only the walled town; the
  hillside stays one room.
  - Without it, the slope through the roof line cut the line into 1 300 rectangles.
  - The first plan pass also ran over 30 minutes; see "Converter changes".
- **Roof line at 224 LT, not Sturmford's 256.** The gatehouse's side passages (floor 240) would otherwise have joined
  the hillside to the streets through 16-LT slots.
- **One hand cut in the north gate.** The gate is the wall's only opening below the line.
- **The plain cover's 1 373 rectangles came from the diagonal streets** (their 16-LT staircase edges; Sturmford has
  244). They cost the portal traversal: up to 256 nodes and 148 544 portal link tests per visibility build, the cap hit
  at 3 of 12 street poses ([CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md)).
- **Merged top portals (`merged_top_portals: true`, 2026-11-01; CITY_PLAYBOOK "The open air" step 3).** 139 convex
  top portals (at most 9 corners; rebuilt with the final converter on 2026-11-01 evening; the afternoon build predated the sky-face rule) instead: **1 470 -> 237 portal faces, 27 911 -> 26 678 faces,
  37 979 -> 34 479 vertices**; only the portal faces change. On the 22 street poses of the v03 tour (before: the
  2026-10-31 build, `output/mm9_rework/portals_1101/thjorgard/before_oldtex`; after: `.../after`): traversal nodes median
  73 -> 32, max 256 -> 60 (**cap hits 3 -> 0**); portal link tests median 24 218 -> 1 339, max 148 544 -> 3 066. Sectors
  drawn equal except s03 (10 -> 11) and s05 (5 -> 7), both at the cap before. All 36 views compared in 16 x 16 blocks:
  no hole, only the new x4 textures (`devdocs/mm9_rework/city_street_cost/portal_counts.py`). Scenarios doors_exits,
  shops, scripted pass. With the merged face draws (INDOOR_FACE_DRAW_GROUPS.md) the street views draw 108-157 world
  draws for 159-440 batches (CITY_STREET_COST.md "Proposal 2: result").

### Map-local geometry fixes (`convert.py`)

- **Glass only on MM9's translucent panes.** Glass applies to flag 0x8 only: `thjorwindow2/4` and `thjorbars` also
  paint 64 opaque facade windows.
- **`greenscreen`:**
  - the 7 sky-flagged polygons are the library's skylight and its upper windows' backs, and become sky faces;
  - the 5 solid ones stand behind facade doors that never open, and take a wall texture.
- **`split_at_walls`:** Klusos House's route, for any wall direction; 5 726 extra pieces. Big floors and ceilings are
  cut at the walls standing on or under them, and big walls at the partitions whose ends meet them. It fixed two
  holes found in review v01:
  - The street drew the sky through a floor strip in front of a facade. MM9 lays the street floor on under the
    houses, and that floor had gone to the house's room.
  - The tavern's back corridor drew the sky. The tavern's west wall runs behind a storeroom, a corridor and a
    kitchen, and had gone to the storeroom.
  - Floor area under another room's air: 90 259 -> 65 815 LT².
- **Doors with MoveDir 0.** Door14, 16, 17, 18 and 20 (MoveDir 0, MoveDist 0) get a direction; their NaN direction
  stopped the compile.
- **The DOORS table keys every leaf as a string**, because two leaves are named `Armor-Forge0` and `Weapon-Forge0`.
- **Sven's relations.** His picture row 520 (BDwarf A) is a hostile family, so the click was refused. He takes a
  peasant family's relations (Hall of the Gods' `ally` route).

## Sky, fog and minimap

- **Sky:** the skymarker faces (and the library's greenscreen sky faces) get `IndoorSky`, and the scene opens to the
  sky with `plansky3`. Review: `review/sky01_sheet.jpg` shows 06:30, 12:00, 19:30 and 23:30 from three views: dawn,
  noon sun, dusk, stars and moon.
- **Fog and daylight (2026-10-31):** grey `Fog0` (64-11 520 native) by day, black `Fog1` at night, in MM9's own fog
  model (`map: {fog: lithtech}`), and daylight on the streets (`city: {daylight: true}`): MM9's ambient 80 and its
  StaticSunLight, by the time of day. Reinstalled with both (BLV unchanged); sheets `review/dl_compare_<time>.jpg`
  (old ODM | before | after at 06:30, 12:00, 19:30, 23:30). See CITY_PLAYBOOK "Daylight and fog".
- **Street lights x BrightScale (2026-10-31):** `map: {bright_scale_lights: true}`: 59 of 160 lights at colour x
  0.6-0.8 (101 are at 1.0). Rebuilt; the street views barely change (`review/bs_compare_1200.jpg`, `_2330.jpg`: old
  ODM | before | after). Scenarios rerun: doors_exits, shops, scripted pass.
- **Sky in fog (not set):** by MM9's data this city's sky is grey by day (`Fog0` SkyFogNearZ 0 covers the sky box)
  and clear at night (`Fog1`); `map: {sky_fog: true}` would carry it (devdocs/INDOOR_FOG.md "The sky in fog"). Left
  off: it would change the accepted noon look; the orchestrator's call.
- **Fog by the daylight (2026-11-01):** the rebuild writes scene fog `follow_daylight: true` (shared converter, cities
  with daylight and fog; devdocs/INDOOR_FOG.md "Fog by the daylight"). The grey day fog now darkens with the daylight
  through the evening; at 23:30 MM9's black `Fog1` rules as before. BLV byte-identical; 12:00 and 23:30 old binary |
  new on three views: noon identical, 23:30 within 1-2 % of pixels (people, stars):
  `review/fog_night_1101_compare.jpg`. Scenarios rerun: doors_exits, shops, scripted pass.
- **Minimap:** MM9's painted `ui/maps/thjorgardcity.pcx` (catalog entry kept). No outlines.

## Content

- **People (60 actors, all friendly).** The old import's NPC records (names, rows, RUDE ids) with MM9's bodies; they
  stand where MM9 placed them.
  - Sven Forkbeard (RUDE 3) stands in the palace.
  - Shopkeepers stand in their shops. Shops close from 20:00 to 06:00 (key 5017).
- **Decorations:** 730 placements (588 props, 142 torches and candles) from the props project, which built 20 models
  and reused 114. Street lamps carry no light (MM9 lights the streets with its sun only).
- **Doors:** 145 movers.
  - MM9's swing doors (`rotate`; pairs open together).
  - 69 linear `Door`s that are Locked with MoveDist 0: facade and upper-room doors that never open; a click says they
    are locked.
- **Chests: none.** MM9 places no TreasureChest or TreasureBag in Thjorgard City.
- **Exits** (`map_transitions.txt`):
  - Thjorgarddocks (690) and Thjorgardcityexit (689) to the Thjorgard wilderness;
  - Arenaexit (685) to the Arena.
- **Starts**, the old map's four, on their floors facing 90 - ry: ArenaExit, StartPoint0 (docks), StartPointTerrain
  (west gate), TownPortal (palace).

### Scripted objects (`citylua.py`; read from `mm9/extracted/SCRIPTS/SCRIPTS/*.scr`)

| Script | Native |
| --- | --- |
| ForadWorld.scr "Thjorgard" | location key 1025 (1024-1033 cleared), shop hours 5017 |
| BankOrb.scr (Ragnar Gjalpssen, RUDE 13) | the Orb of Linking: key 330 on a click with the orb after 322; the exit places it (323); six orbs: 337, 20 000 xp, 15 000 gold |
| NPC3.scr (Sven Forkbeard, RUDE 3; United.inc) | click: the five clans (82, 38, 51, 63, 74 -> 178). Exit: the battle 104 -> 486; Thjorad Mine 32 -> 163, 12 000 xp, 6 000 gold, item 197 taken; refinery 33 -> 177, 68 004 xp, 3 000 gold; clans united 83 -> 179; lifesaver 234 -> 235. Hidden on 40 unless 108 |
| NPC4.scr (Johannes Bem, RUDE 4) | Scholar to Mage: 293 -> items 242/244, key 288; 493 -> 294, 63 000 xp, 5 000 gold, promotion of keys 429-432 |
| NPC161.scr (Tymon the Nord, RUDE 161) | Initiate to Scholar: 201 once "We are seeking promotion to Scholar" was asked (its code key 2081) and a member is eligible (`MM9.canPromote("Scholar")`, not MM9's per-character keys 425-428, which nothing sets; 2026-11-06 audit G2); 203 or 204 -> 205 (24 500 / 11 000 xp, 1 000 gold), the promotion |
| NPC5.scr (Gunnar Thjorsmith, RUDE 5) | click: ore items 359-361 -> keys 395-398. Exit: ore paid after 464 (700 / 1 500 / 3 000 gold), keys cleared; refinery 9513 -> 9514, item 398 -> 399 |
| NPC7.scr (Hjarrand Fixer, RUDE 7) | the machine payment: 360 (1 000 gold) or 361 (2 000) -> 362 (else 363); he leaves once paid (hidden on 362) |
| NPC416.scr (Harris Willington) | killed: key 233 (the prize quest; monster killed hook) |
| NPC378.scr (Thorolf, two copies) | as Sturmford: the other copy removed on talk; vanishes on 84/107; dialogue reopens on 83/106 |
| Retainer.scr (Hrolf 450, Arienh 452), RandverRetainer.scr (453) | hidden while hired |
| TownPortal.scr "Thjorgard" | cleansing the altar: key 5011 (the dirty altar hides and its clean twin `mm9_portalclean` at its place shows, also on load: `../mm9r_common/dungeon/town_portal.py`) |
| GreatBookKey.scr (BookKey) | shown only with key 375, which nothing in MM9 grants: hidden. Click with item 243 -> items 560, 244, 347, key 374 |
| BookLetter.scr (Prop3-Prop7) | letters 424, 425, 427, 428, 429 |
| Book.scr, PropAnim.scr, Shopkeeper.scr, OrbTrigger.scr | cosmetic. OrbTrigger messages an object `Orb` that the DAT lacks. PropAnim poses are baked into the props |
| WellMMIX0 | MM9's well class (Stat 2, StatType 2, BonusAmt 5, 4 doses a day; inside `object.lto`, not traced): a click answers, no bonus |

**Left out:**
- 24 PerceptionBrushes (the green and red door hints in the original);
- the breakable windows;
- NPC7's walk to the refinery (other map);
- Sven's MoveToPos (he already stands there);
- voices;
- ambient sounds.

## Quality gates

1. **Every DAT world model has a rule** (model_patterns plus rules). Skipped, with reasons:
   - the sky box and the TOD star shell;
   - 7 AIBarriers (MM9's AI only);
   - 9 PortalZones (MM9's renderer zones), whose 8 window UserPortals are skipped too;
   - VisBSP, the PerceptionBrushes and the AI tracks.
2. **Sealed air:** `leaked_to_border` false, 2 seeded air components. 508 faces without air in front were dropped
   (`work/dropped_faces.json`): faces between brushes, and pieces under walls from the wall splits.
3. **Every portal joins two rooms:** `portals_without_two_rooms` 0. The Bembridge garden gate is a plain mover, with
   open air on both sides.
4. **No holes.**
   - The 36-view sheet `review/v03_compare.jpg` shows none (v01 showed the two fixed above).
   - Floor holes 0, cracks 0.
   - Floor check 65 815 LT²: strips along the street cuts and pieces under the house walls. No view shows a wrong
     sector.
5. **Review sheet:** MM9 original (the old ODM import, view distance unlimited) | native BLV.
   - **36 eye-level views:** 22 streets, plazas, gates and the hill; 14 interiors (tavern, temple, town hall, magic
     shop, general store, apothecary, library, bank, forge, armor and weapon shops, training hall, university, the
     palace hall).
   - Same geometry and props everywhere.
   - Ours is darker in the streets (classic light against the old lightmaps) and hazier (MM9's fog).
   - The original's green Perception glow on door frames is not there.
   - The forge's quench trough draws as the shared water125 liquid (flat teal).
6. **Walkability** (`work/audit.log`): 209 steps, 58 flights, 19 unreachable regions, 1 pit, 15 mover notes,
   2 actor notes.
   - **The 19 regions** are counters (92-123 over the floor: bar, armor, weapon, general store, magic shop,
     apothecary, bank), the temple altar (103), and upper-floor furniture and platforms (81-122). Sector 4's
     5.9 M units² is the 32-LT plinths under the southwest's diagonal houses, whose walls stand on the edges.
   - **The pit** (82) is a nook between a house and the east town wall, walled on all four sides
     (`work/probes/regions.yml`): nobody gets in.
   - **Raised floors:** `half_steps: true` (CITY_PLAYBOOK "Raised floors") made 5 steps.
     - Four are beside stair tops onto the upper floors. Probed (`work/probes/half_steps.yml`), the party climbs each
       one: 52, 62, 52 and 51 up.
     - The fifth (palace hall, 246 long) lies inside the throne dais' stair block, where the hall floor runs under
       it. Its probe starts in the stair and walks 0; nobody stands there.
7. **Scenarios pass** (headless, real clicks where the engine picks):
   - **`scenario_doors_exits` (24 steps).** The general store's double door stops the party, opens on its click and
     the party walks in. A facade door says locked and stays shut. The three exits raise their transitions.
   - **`scenario_shops` (26).** Geirrod A'Ghrie's (RUDE 12) and Sitheag A'Mor's (RUDE 10) dialogues open by
     `press_interact`, and "Let us see what you have." opens each shop.
   - **`scenario_scripted` (45):**
     - keys 1025 and 5017 (at 21:00, cleared at 09:00);
     - the altar (5011) and a letter;
     - Sven's clans (178) by his click, and his Thjorad reward (163) on the dialogue's close;
     - the bank orb (323);
     - Harris killed (233).
   - No chest scenario: the city has none.
8. **Starts:** four, on their floors (`build_report.json` `starts`). The tour's first view is the docks start.
9. **Compiler:** unchanged, so no new tests. The build used the existing `mm9_compile_indoor_source`.
10. **Lights:** 160 BLV lights; MM9's fills over the four-per-point cap are bake-only and unused without a bake.

## Performance (counts; frame rate needs a single-session run)

Same 36 views (`review_tour_v03.yml` / `v02_original`), with `logging.performance_trace` and
`logging.indoor_visibility`, in minimized isolated desktop runs on a shared machine.

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Textured batches |
| --- | --: | --: | --: | --: |
| **Thjorgard City, native BLV** | **218 / 669** | **36 900 / 119 900** | 4 / 16 | 124 / 440 |
| Thjorgard City, old ODM import | 1 458 / 2 294 | 89 500 / 249 900 | – | – |
| (Sturmford City, native BLV) | 218 / 385 | 30 600 / 70 800 | 5 / 12 | 96 / 238 |

- **Map load** (median of 3, `OPENYAMM_MAP_LOAD_TIMING=1`, `work/perf/load_*.log`): BLV **1.69 s** (asset load
  0.58 s), against the old ODM's 3.46 s (1.29 s).

## Converter and engine changes

- **Engine:** none. No engine build was made.
- **Shared converter, under `locks/converter_edit.d`:** `city/structure.py` `street_box_lt` (opt-in; the default
  covers everywhere, and its code paths are identities).
  - Lich Lab `--plan --scratch` and Sturmford City `--plan --scratch`, before and after: logs and every output
    byte-identical (`work/proof/`).
  - Documented in CITY_PLAYBOOK "The open air".
- **Map-local** (`convert.py`):
  - glass on translucent panes only;
  - greenscreen;
  - `split_at_walls`;
  - a cached, vectorised `crossing_portals` that returns the same portals in the same order. The shared one took
    over 30 minutes on 15 000 polygons x 600+ portals; with this one the plan pass takes about 5 minutes. Proposed
    for the shared `rooms.py` after a byte-identical check.

## Open items

- **Night fog:** stays grey (MM9 switches to black fog at night).
- **Static light** does not follow the time of day (CITY_PLAYBOOK "Engine features").
- **Not carried:** Perception hints, breakable windows, the well's bonus (its class is not traced), MM9's NPC wander
  rails and schedules. Townsfolk on MM9's own wander without a script walk (2026-11-07,
  `mm9_ai_placement.townsperson_walks`, as Sturmford City); the rest stand.
- **Townsfolk** draw as stand-in peasants until the MM9 town NPC models exist (another session).
- **Portal count:** done 2026-11-01 (merged top portals, 139 instead of 1 373 rectangles; see "Structure").

## Randver's sitting (2026-11-11)

`randverretainer.scr :Init` loops `sitting` while he is not hired, but his MM9 body (PeasantMale.abc in the DAT;
the dwarf PeasantDM bodies too) has no such clip and no chair stands at his place (the nearest, Chair5, is 369 away),
so MM9 shows him standing. Nothing changed: he stands, as in MM9.
