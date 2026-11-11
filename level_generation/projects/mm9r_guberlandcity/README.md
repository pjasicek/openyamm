# MM9 rework: Guberland City (`guberlandcity.blv`)

MM9's Guberland City is converted from its DAT world into a native **indoor map (BLV) open to the sky**. It is the
seventh of MM9's cities, after the [Sturmford City pilot](../mm9r_sturmfordcity/README.md).

- **The city:** an oval wooden wall round four walled quarters (north-west, north-east, south-east, south-west), each
  entered from the central cross through two sliding gates. The cross holds the north avenue from the city gate, the
  palace plaza with Markel the Great's palace and the well, the east and west arms, and the south avenue to the
  training square. Walk-in buildings: the tavern with the Guberland Players' stage, the temple, the palace and its
  throne room, the bank, the magic shop, the smithy and the weapon shop, the apothecary hall with the book shop, the
  town portal house, Nurtigan's sickroom and a few houses.
- **Recipe:** the shared converter ([DUNGEON_PLAYBOOK.md](../mm9r_common/DUNGEON_PLAYBOOK.md)) and its city extension
  ([CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md)). **Brief:** [CITIES_ROLLOUT.md](../../../devdocs/mm9_rework/CITIES_ROLLOUT.md).
- **Install:** the review root `output/mm9_rework/assets_dev`.
- **Props:** [`../../props/mm9_guberlandcity_claude/`](../../props/mm9_guberlandcity_claude/README.md).

**Status 2026-10-31 (wave 2, unattended): the city works as a BLV.** Built and installed:

- **Geometry:** 49 sectors: the streets of each district divided under a roof line, 23 walk-in interiors.
- **Sky and minimap:** our Enhanced outdoor sky with the time of day behind the sky faces; MM9's painted city map as
  the minimap.
- **People:** 46 actors (43 townsfolk and shopkeepers with RUDE dialogues, 3 guards). Walk-in shops open by real clicks.
- **Decorations and doors:** 258 decorations; 76 movers (the eight quarter gates open as the party walks up to them).
- **Scripts and links:** every gameplay script as native Lua; the exit to the Guberland wilderness and both starts.
- **Lighting:** classic, no bake. Daylight and fog are another agent's work (brief: "Shared findings").

Every scenario passes. No converter or engine change.

## Build and review

```sh
python3 level_generation/projects/mm9r_guberlandcity/convert.py --plan     # rooms only: work/rooms*.png (1 min)
python3 level_generation/projects/mm9r_guberlandcity/convert.py            # build, compile, install (70 s, 0.8 GB)
python3 level_generation/projects/mm9r_guberlandcity/make_scenarios.py
for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_guberlandcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_guberlandcity/make_tour.py v02 [--original]    # sky01 --sky: the sky sheet
bash level_generation/projects/mm9r_guberlandcity/work/perf/tours_v02.sh             # both tours, with the traces
python3 level_generation/projects/mm9r_common/dungeon/sheet.py level_generation/projects/mm9r_guberlandcity/review/v02 \
    level_generation/projects/mm9r_guberlandcity/review/v02_original
python3 level_generation/projects/mm9r_guberlandcity/work/perf/counts.py work/perf/blv_v02_game.log work/perf/odm_v02_game.log
bash level_generation/projects/mm9r_guberlandcity/work/perf/loads.sh                   # map load, 3 x 2 runs
```

`output/mm9_rework/guberlandcity_original_root` is a private hard-linked copy of `assets_original` for the old map's
tours, made as Sturmford's: its `worlds/mm6-8/models/actors.yml` are the committed ones, and the old scene allows
saving.

City structure experiments: `work/city/cache_voxels.py` caches the voxel pass (30 s), `work/city/try_structure.py
<roof line>` tries a roof line (`streets_<H>.png`), `work/city/heights.py` plots street heights and clearance,
`work/city/street_views.py` picks open street views. `work/floors/floor_check.py` lists the floor check per polygon,
`work/probes/floors_near.py` and `faces_near.py` list floors (DAT) and compiled faces round a point.

## Numbers and limits

- **Frame:** `native = (LT.x, LT.z, LT.y) * 2.56`, no offset, which is the old map's frame. Extent x -9 175..7 864,
  y -19 661..1 311, z -164..1 638: **inside ±32 767**.
- **Polygons:** 8 908 source polygons -> 8 559 merged -> 12 755 native polygons -> **15 326 compiled faces**.
- **Vertices: 19 823** (19 019 since the merged top portals, 2026-11-01). BLV indices are 16-bit, so this is **30 % of 65 535**. No widening is needed.
- **Other counts:** 631 portal faces (271 since the merged top portals), 76 movers, 51 BLV lights (at most 3 per floor point), 403 sky faces, 0 outlines
  (painted minimap), 37 translucent faces (window panes, the bank's bars, the fish tank), 1 liquid face (the fish tank).
- **Faces per sector: max 1 632, median 138.** The max is a street sector (the north-east quarter's streets, one room:
  every cut there is a loop round a house). Sturmford 997 / 119, Thjorgard 3 579 / 95.
- **Voxels:** 16 LT, 420 x 48 x 516 = 10 M cells, 4.9 M air. The geometry pass takes 30 s; peak 0.8 GB.

## Structure: sectors and portals

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors (tavern rooms, temple, palace and throne room, bank, shops, the apothecary hall, houses) | 23 rooms | 13 MM9 UserPortals (5 doorways, 8 quarter gates) and 19 door-leaf portals; 30 glass (window) portals |
| Street rooms (the air under the roof line at 192 LT) | 21 | 29 street-cut portals (42 found automatically, 13 dropped as loops); no hand cuts |
| Roof rooms (the air over the roofs, one per district: the four quarters and the central cross) | 5 | joined to the streets by **180 merged top portals** (convex polygons over walls and roofs, `merged_top_portals`, 2026-11-01; were 540 roof-line rectangles, 20 blind) |

How the open air is divided (`../mm9r_common/city/structure.py`, plan `work/rooms_street.png`, `work/city/streets_192.png`):
the streets lie at 0-16 LT and the houses' eaves start about 224 LT, so the roof line is at **192 LT** (176 over the
streets; the gates reach 160). The eight quarter gates (MM9 UserPortals Gate1-8portal, linear Door pairs) already
separate the five districts. The quarters are open yards round free-standing houses, so most automatic cuts are loops
and are dropped; the north-east quarter's streets stay one room. Per view the renderer draws a median of **6 sectors**
(max 14).

**Merged top portals (2026-11-01, `merged_top_portals: true`; CITY_PLAYBOOK "The open air" step 3,
[CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md) "Result of proposal 3").** The 540 rectangles
become 180 convex top portals (at most 8 corners; rebuilt with the final converter on 2026-11-01 evening; the afternoon build predated the sky-face rule): **631 -> 271 portal faces, 15 326 -> 14 966 faces,
19 823 -> 19 019 vertices**; only the portal faces change. On the 24 street poses of the v02 tour (before: the
2026-10-31 build, `output/mm9_rework/portals_1101/guberland/before_oldtex`; after: `.../after`): traversal nodes median
29 -> 22, max 101 -> 45 (no cap hit before or after); portal link tests median 1 301 -> 451, max 11 721 -> 1 734.
Sectors drawn equal except s14 (6 -> 7). All 38 before/after images compared in 16 x 16 blocks: no hole, only the new
x4 textures. Scenarios doors_exits, shops, scripted pass.

### Map-local fixes (`convert.py`)

From Thjorgard City and Thronheim City (brief), all map-local:

- **Glass only on MM9's translucent panes** (flag 0x8): the 89 facade windows painted with `window_frame_trans` in
  PhysicsBSP (flags 0x1081) stay opaque faces.
- **`split_at_walls`:** big floors cut at the walls standing on them (Thronheim's rule: foot at most 16 LT over the
  floor), big ceilings at the walls under them, big walls at the partitions whose ends meet them. **New here:** sloped
  ceilings are cut at every partition with two corners on their plane. The tavern's three side rooms share one sloped
  ceiling (`wood-ruf`); the south room drew the sky through a triangle by the north-west corner (review v02, found in
  `i14_tavern_side_room`, `work/probes/hole/`). 2 075 extra pieces in all.
- **The faster portal-crossing test** (Thjorgard's cached `crossing_portals`): the full build takes 70 s.
- **The DOORS table keys every leaf as a string.**
- **Peaceful relations for NPCs on monster-family rows:** Markel's row 579, the guards' 9107 and the wizards' 439 take a
  peasant family's relations (`ally`), so they talk instead of refusing the click.

Guberland's own:

- **The bank's counter bars** (`WorldObject1`, MetalBar in an Invisible shell, MM9 solid): the shell is dropped and the
  bars become an untouchable two-sided cut-out (The Arena's route), so the banker behind them takes the click.
- **The fish tank** (`BlueWater0`, MM9's Water115flowing.spr at SurfaceAlpha 0.7, in the magic shop): its top face is
  a liquid face, drawn see-through by the liquid shader (`liquids.py`, Water115 at 0.7).
- **The stage step** (`STAGE_STEP_LT`): the Guberland Players' stage stands 32 LT (82 native) over the tavern floor,
  which MM9's player climbs and the party (50) does not. One invisible step (41 native, 20 LT deep) along its front;
  probe `work/probes/stage.yml`: the party walks from the audience onto the stage (+82); the bar counter beside it
  still stops it.
- **The quarter gates' quirk:** Gate8R names `Gate1portal` and `Gate1L` as its portal and pair (a source copy-paste);
  it is paired with Gate8L on `Gate8portal`.

## Sky, fog and minimap

- **Sky:** the 18 `skymarker` polygons (the lid at 640 LT) and the 218 sky-flagged `greenscreen` polygons (the shell's
  walls and the partitions above the district walls) are sky faces with `IndoorSky`; the scene opens to the sky with
  `plansky3` (the old import's sky). `review/sky01_sheet.jpg`: 06:30, 12:00, 19:30 and 23:30 from three views: dawn,
  noon, dusk, stars and moon.
- **Fog:** none (WorldProperties `EnableFog 0`).
- **Minimap:** MM9's painted `ui/maps/guberlandcity.pcx` (catalog entry kept). No outlines.

## Content

- **People (46 actors, all friendly).** The old import's 40 NPC records (names, rows, RUDE ids) with MM9's bodies;
  the three town guards (row 9107, no dialogue), the tavern keeper (NPC141, RUDE 141) and the two half-orc women
  (RUDE 428) the old import left out. They stand where MM9 placed them (MM9's wander rails, the guards' wall patrols
  are not carried; the players' show is, below). The old import's "dog0" was an ambient dog sound: not placed.
- **Walk-in shops** (RUDE rows that open a shop): Siln Threki (weapons, 134) and Skallagrim Hrafnssen (135) in the
  two shops of the smithy block, Trian A'Lyrae (the magic shop, 137), Egil the Booknose (books, 146) and Skarphedinn
  Njalssen (the apothecary, 142) in the apothecary hall; Ottar Gizurssen keeps the bank (140). A click opens the
  dialogue and its service row the shop (scenario: Skallagrim and Trian). Shops close from 20:00 to 06:00 (key 5017).
- **Decorations:** 258 placements (226 props, 32 chandeliers and wall candles) from the props project, which built 5
  models (`prize`, `suitofarmor02aged`, `tapestry_banner7`, `weaponscabinet02ns`, `seamonster`) and reused 87. The
  little sea monster stands in the fish tank (static: MM9's swims its `seapath` markers).
- **Doors:** 76 movers. MM9's swing doors (`rotate`, pairs open together); 32 linear `Door`s that are Locked with
  MoveDist 0 (facades; 3 with a room behind them) and the two locked smithy doors: a click says they are locked;
  Nurtigan's sickroom door (locked until the apothecary's potion); the eight quarter gates (linear pairs, 120 LT); the
  tavern's bar flap and the stage curtain (a click toggles them).
- **Chests: none.** MM9 places no TreasureChest or TreasureBag in Guberland City.
- **Exit** (`map_transitions.txt`): ExitTrigger0 (185) at the city gate to the Guberland wilderness (GuberlandCityExit);
  the wilderness's ExitTriggerGuberland arrives at StartPoint0. **Starts:** StartPoint0 (the gate) and TownPortal (the
  portal house), on their floors, facing 90 - ry.

### Scripted objects (`citylua.py`; read from `mm9/extracted/SCRIPTS/SCRIPTS/*.scr`)

| Script | Native |
| --- | --- |
| ForadWorld.scr "Guberland" | location key 1028 (1024-1033 cleared), shop hours 5017 |
| Gate1-8trigger (Trigger, toggle the gate, then off) | a 0.25 s poll opens a shut gate pair when the party stands in its box (re-armed when it leaves); a click toggles a gate too |
| NPC127.scr (Markel the Great, the Jarl, RUDE 127; United.inc) | click: the five clans (82, 38, 51, 34, 74 -> 178). Exit: Book of Rules 61 -> 167 (10 000 xp, 3 000 gold, item 391 taken); Ivan 62 -> 165 (26 000, 3 000, item 400); the Dook 66 -> 168 (40 000, 3 000); the clans united 83 -> 179 (26 500, 6 000). Hidden on 40 unless 108 |
| BankOrb.scr (Ottar Gizurssen, RUDE 140: nKey 332, nKey2 326) | the Orb of Linking: 330 on a click with the orb after 322; the exit places it (326); six orbs: 337, 20 000 xp, 15 000 gold |
| NPC128.scr (Tjolnir the Super-neat, RUDE 128) | Initiate to Healer: 206 once his promotion row was asked (code key 2083) and a member is eligible (`MM9.canPromote("Healer")`, not MM9's keys 437-440, which nothing sets; 2026-11-06 audit G2); Nurtigan cured 212 -> 213, 24 500 xp, 1 000 gold, the promotion |
| NPC129.scr (Gray Slemnir, RUDE 129) | Healer to Priest: 250, 251, 252 once his promotion row was asked (code key 2084) and a member is eligible (`MM9.canPromote("Priest")`, not keys 441-444); 260 -> 261, 63 000 xp, 5 000 gold, items 241 and 430 taken, the promotion |
| NPC141.scr (the tavern keeper, RUDE 141) | the keg sold 304 -> 306, 5 000 xp, 500 gold, item 249 taken |
| NPC142.scr (Skarphedinn Njalssen, the apothecary, RUDE 142) | click: item 240 and 206 -> 207. Exit: 208 takes item 240 and gives 209 two game hours later (the poll); 210 -> item 558, 373, the sickroom unlocked |
| NPC131.scr (Nutty Nurtigan, RUDE 131) | cured (211) with the potion (558): the potion is taken and his door opens; on load with 211 the door stands open (MM9 walks him out to wander) |
| NPC378.scr (Thorolf, two copies) | as Sturmford: the other copy removed on talk; vanishes on 84/107; the dialogue reopens on 83/106 |
| Retainer.scr (Alberik 457, Ehwaz 459) | hidden while hired |
| TownPortal.scr "Guberland" | cleansing the altar: key 5014 (the dirty altar hides and its clean twin `mm9_portalclean` at its place shows, also on load: `../mm9r_common/dungeon/town_portal.py`) |
| BookLetter.scr (Prop1 569, Sign4 578, Prop5 459, Prop6 460, Prop7 461) | the letters: the Players' bill, Markel's awards, two love letters, the Dook's proclamation |
| Book.scr, PropAnim.scr, Shopkeeper.scr, Narrator/Abriel/Trislan/Wilam/Ralof/Leffery.scr | cosmetic; see below |
| WellMMIX (Well0) | MM9's well class (not traced, as Thjorgard): a click answers, no bonus |

**The Guberland Players' show** ("The Death of Emperor Trislan", Narrator.scr at 14:30 and 16:30): the curtain
opens, the 28 lines of THEPLAY.scr play at their speakers (`citylua.play_lines`), and since 2026-11-11 the players act
it (`citylua.play_cues`, map timer 263, arrival events 270-275): Narrator.scr's and the five actors' walks to their
markers (`evt.MoveActorTo`, the arrival faces whom MM9 targets), each speaker's conv clip looping while his line
plays, Abriel's slap of Ralof and Ralof's of Trislan (attack, hit, FleshHit03/04), Trislan's play_death and
play_getup, the cast lined up facing the hall for the bow (Ralof has no bow clip) and their walk off before the
curtain closes. MM9 chains these on animation keys and walk arrivals; here they are cues at the same offsets on the
lines' timeline. A load during a show puts the players back at their places (`playersHome`). Checked headless (walks,
clips, slaps, death, bows) and in desktop captures (`output/held_items_check/guberlandcity/wide2/`, `close2/`;
a capture tour must set the time to 14:27 or earlier: the show starts on the minute 14:30 itself). Not carried: the
blacksmith's and bell sounds (Trigger0/1,
Bell triggers), the ocean sound (OceanTrigger), MM9's ambient sounds; 9 PerceptionBrushes (door hints); the
breakable windows; Nurtigan's walk; the sea monster's swim; voices.

## Quality gates

1. **Every DAT world model has a rule** (overrides.yml). Skipped, with reasons: the sky box and the TOD star shell, 11
   AIBarriers (MM9's AI only), the fish tank's water volume (its top is a face), VisBSP, the 9 PerceptionBrushes and
   the 297 AI rails.
2. **Sealed air:** `leaked_to_border` false, 2 seeded air components (4.9 M voxels). 171 faces without air in front
   dropped (`work/dropped_faces.json`): sky faces facing out, faces between brushes, invisible lids' sides.
3. **Every portal joins two rooms:** `portals_without_two_rooms` 0. 29 facade `Door`s were tried as doorways and have no
   air behind them: plain movers.
4. **No holes.**
   - The 38-view sheet `review/v02_compare.jpg` shows none (v02 found the tavern side room's ceiling triangle, fixed
     above).
   - Floor holes 0, cracks 0.
   - Floor check 273 461 LT²: 244 800 are sloped roofs straddling the roof line (nobody stands there); 28 700 at
     ground level are 16 LT strips along the street cuts and gate sills, 1-4 % of each floor polygon
     (`work/floors/floor_check.json`). No view shows a wrong sector.
5. **Review sheet:** MM9 original (the old ODM import, view distance unlimited) | native BLV, **38 eye-level views**
   (24 streets, plazas, gates and quarters; 14 interiors: the tavern hall, bar, stage and a side room, the temple, the
   palace hall and throne room, the bank, the magic shop, the smithy, the weapon shop, the apothecary hall, the book
   shop, the portal house). Same geometry and props everywhere. Differences:
   - Ours is darker in the streets (classic light against the old import's lightmaps).
   - The original shows the green hover outline and Thorolf (ours hides him until keys 83/106, NPC378.scr).
   - The tops of the wall towers at the south square's corners stand behind MM9's sky-flagged `greenscreen` partitions
     over the district walls, in the next quarter's air: the original drew them, ours shows the sky there (MM9 draws
     its sky faces over what lies behind them).
   - The opaque facade windows (`window_frame_trans`, flags 0x1081) draw black; the original shows faint glass shards.
6. **Walkability** (`work/audit.log`): 1 step (the stage step), 0 flights, 12 unreachable regions, 0 pits, 32 mover
   notes (door frames' recesses and lips), 0 actor notes. **The 12 regions** need nothing but the stage: the tavern's
   bar counters (36 and 48 LT), the smithy's counter (48 LT) and quench tub (24 LT rim), the apothecary hall's counters
   and work tables (36 LT, 6 regions), and the stage (32 LT, standable: the step, probed). `half_steps: true` made no
   step: no 50-66 rise here is standable.
7. **Scenarios pass** (headless, real clicks where the engine picks):
   - **`scenario_doors_exits` (23 steps).** The bank's double door stops the party, opens on its click and the party
     walks in. A facade door says locked and stays shut. Gate6 opens when the party walks into its box and the party
     walks through into the east quarter. ExitTrigger0 raises its transition.
   - **`scenario_shops` (26).** Skallagrim's (RUDE 135) and Trian's (RUDE 137) dialogues open by `press_interact`, and
     their service rows open the shops.
   - **`scenario_scripted` (73):** keys 1028 and 5017 (at night, cleared by day); the altar (5014); a letter; Markel's
     clans (178) by his click and the Dook reward (168) on the close; the bank orb (326); the keg (306); the sickroom
     door locked, the potion's two-hour wait (209), the potion (373) and the door opening.
   - No chest scenario: the city has none.
8. **Starts:** two, on their floors (`build_report.json` `starts`). The tour's first view is the gate start.
9. **Compiler:** unchanged, no new tests; the build used the existing `mm9_compile_indoor_source`.
10. **Lights:** 51 BLV lights, at most 3 per floor point (`content.json` `light_coverage`).

## Performance (counts; frame rate needs a single-session run)

Same 38 views (`review_tour_v02.yml` / `v02_original`), with `logging.performance_trace` and
`logging.indoor_visibility`, in minimized isolated desktop runs on a shared machine (`work/perf/`).

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Textured batches |
| --- | --: | --: | --: | --: |
| **Guberland City, native BLV** | **162 / 278** | **22 200 / 80 600** | 6 / 14 | 70 / 157 |
| Guberland City, old ODM import | 816 / 1 050 | 65 800 / 148 500 | – | – |
| (Sturmford City, native BLV) | 218 / 385 | 30 600 / 70 800 | 5 / 12 | 96 / 238 |

- **Map load** (median of 3, `OPENYAMM_MAP_LOAD_TIMING=1`, `work/perf/load_*.log`): BLV **1.27 s** (asset load
  0.40 s), against the old ODM's 1.87 s (0.64 s).

## Converter and engine changes

None. No shared converter code was changed and no C++ was built. Map-local only: `convert.py`, `citylua.py`,
`overrides.yml`.

## Open items

- **Daylight and street lights done (2026-10-31):** `city: {daylight: true}` (MM9's ambient 80 and its StaticSunLight
  by the time of day), `map: {fog: lithtech}` (no fog in MM9 here: nothing written) and `map: {bright_scale_lights:
  true}` (37 of 51 lights at colour x 0.6-0.8). Noon streets now as bright as the old import, interiors unchanged,
  nights dark: `review/dl2_compare_1200.jpg`, `_2330.jpg` (old ODM | before | after; most "before" shots ended in the
  death video of a long tour, see below). Scenarios rerun: doors_exits, shops, scripted pass.
- **Long screenshot tours ended in a death video** on the BLV (seen here at the sixth view). Fixed 2026-11-01: the
  cause was the tour's clock (the indoor clock ran during the tour's hold, so a repeated `time:` jumped a day; four
  days without rest killed the party), not the city (`../mm9r_common/CITY_PLAYBOOK.md` "Daylight and fog").
- **Facade windows** draw black where MM9 shows faint shards (texture alpha under the opaque faces' alpha test).
- **Not carried:** Perception hints, breakable windows, the well's bonus,
  MM9's wander rails and the guards' patrols, ambient sounds, the sea monster's swim.
- **Townsfolk** draw as stand-in peasants until the MM9 town NPC models exist (another session).
