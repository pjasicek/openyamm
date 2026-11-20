# MM9 rework: Frosgard City (`frosgardcity.blv`)

MM9's Frosgard City is converted from its DAT world into a native **indoor map (BLV) open to the sky**, wave 2 of the
cities rollout ([CITIES_ROLLOUT.md](../../../devdocs/mm9_rework/CITIES_ROLLOUT.md)), after the
[Sturmford City pilot](../mm9r_sturmfordcity/README.md).

- **The city:** a harbour town on a frozen bay. Free-standing houses on one snow field (no town wall, no street
  between continuous facades), Jarl Tryggva's long hall, the temple, the tavern, the shops; the docks and a pier on
  the bay's ice; the north gate road to the Frosgard wilderness; mountains all round and an ice "tooth" floating over
  the bay.
- **Recipe:** the shared converter ([DUNGEON_PLAYBOOK.md](../mm9r_common/DUNGEON_PLAYBOOK.md)) and its city extension
  ([CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md)).
- **Install:** the review root `output/mm9_rework/assets_dev`.
- **Props:** [`../../props/mm9_frosgardcity_claude/`](../../props/mm9_frosgardcity_claude/README.md).

**Status 2026-10-31: the city works as a BLV.** Built and installed:

- **Geometry:** 12 sectors: the open air (town, harbour, gate road and the scenery round them) and 11 walk-in
  interiors behind their doors and window panes. The voxel pass covers a box round the playable town and harbour;
  the mountains and the bay beyond it are scenery of the open-air sector (below).
- **Sky and minimap:** our Enhanced outdoor sky with the time of day behind the sky faces; MM9's painted city map.
- **People:** 50 actors (47 townsfolk with their RUDE dialogues, Jarl Tryggva, Tamur Leng, Forad Darre). Walk-in
  shops open by real clicks.
- **Decorations and doors:** 177 decorations; 72 movers (the doors, the bank's hatch, 37 ice floes).
- **Scripts and links:** every gameplay script as native Lua, including the ice-breaking quest and the Battle of
  Frosgard; 1 exit, 4 starts, 3 boat routes into the docks.
- **Lighting:** classic, no bake.

Every scenario passes.

## Build and review

```sh
python3 level_generation/projects/mm9r_frosgardcity/convert.py --plan     # rooms only: work/rooms*.png (3.5 min, 2.5 GB)
python3 level_generation/projects/mm9r_frosgardcity/convert.py            # build, compile, install (9 min, 2.5 GB);
                                                                           # then rewrites the boat routes (transport.py)
python3 level_generation/projects/mm9r_frosgardcity/make_scenarios.py
for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_frosgardcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_frosgardcity/make_tour.py v03 [--original]    # sky01 --sky: the sky sheet
level_generation/projects/mm9r_frosgardcity/work/perf/tour.sh v03 blv               # and `odm`: tours with traces
python3 level_generation/projects/mm9r_common/dungeon/sheet.py level_generation/projects/mm9r_frosgardcity/review/v03 \
    level_generation/projects/mm9r_frosgardcity/review/v03_original
python3 level_generation/projects/mm9r_frosgardcity/work/perf/counts.py work/perf/blv_v03_game.log work/perf/odm_v03_game.log
bash level_generation/projects/mm9r_frosgardcity/work/perf/loads.sh                  # map load, 3 x BLV and ODM
python3 level_generation/projects/mm9r_frosgardcity/work/sector_stats.py             # faces, sectors, faces per sector
```

`output/mm9_rework/frosgardcity_original_root` is a private hard-linked copy of `assets_original` (its
`worlds/mm6-8/models/actors.yml` are the committed ones; its old scene allows saving). `work/tour/where.py x,z` lists
the floors and sectors under a point (how the interior views were placed: a floor query over 151 LT lands on roofs).

## Numbers and limits

- **Frame:** `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame: transitions, boat routes and the
  painted map's bounds stay valid). MM9's sky shell spreads 31 232 LT over the bay (x -12 800..18 432 LT: past the BLV's
  int16 frame at 12 799 LT): geometry past |x|, |z| = 12 700 LT is clipped (the bay's far ocean, the shell). Extent
  x -31 457..32 512, y -29 491..13 763, z -1 352..12 347: **inside ±32 767**.
- **Polygons:** 11 271 source polygons -> 10 245 merged -> 9 912 near the town plus 1 975 far scenery -> 11 854 kept
  after the splits -> **13 986 compiled faces**.
- **Vertices: 15 352**, 23 % of the 16-bit index range. No widening is needed.
- **Other counts:** 12 portal faces (10 door portals, 2 window panes), 72 movers (13 swing doors, the bank's hatch, 21
  locked facade doors, 37 ice floes), 38 BLV lights, 11 sky faces, 2 translucent faces (the magic shop's panes), 317
  ocean faces (the liquid shader), 0 outlines (painted minimap).
- **Faces per sector: max 11 787, median 232.** The max is the one open-air sector: the town's exteriors, the
  harbour, the gate road, Terrain0's mountains and the ocean. The 11 interiors hold 32-383 faces each. The per-sector
  face grid of 2026-10-31 carries a big sector ([BLV_GEOMETRY_COSTS.md](../../../devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md));
  the counts below show no cost from it.
- **Voxels:** 16 LT over the near box only: 40.6 M air voxels, the plan pass 3.5 min, the build 9 min, peak 2.5 GB.

## Structure: sectors and portals

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors | 11 rooms | Tryggva's hall, the tavern, the temple, the training hall, the shop by the apothecary door, the weapons and armour shop, the magic shop, three houses (Door7, Door13, RDoor0), the banker's room behind the counter hatch (no portal: MM9's hatch is an invisible slab; a real click from the street reaches the banker through it, `work/probes/bank.yml`); 10 door portals (9 MM9 UserPortals, the magic shop's leaf rectangle), 2 glass portals (the magic shop's panes) |
| Open air | 1 room | the town, the docks and the bay inside its fence, the north gate road and the scenery round them |

**No street structure (convert.py `FrosgardCity.extra_portals`).** Frosgard is no walled town of streets between
facades: its houses stand free on one snow field that runs on into the shore, the harbour and the gate road. The
first plan pass (roof line at 200 LT, street box over the town) found no corridor for a street cut and divided
nothing: the street air joins the open air all round. So the open air is one room; what a BLV gains here is the
interiors behind their doors (a median of 2 sectors drawn per view, max 6).

**The near box and the far scenery** (convert.py docstring). A 16-LT voxel pass over MM9's whole shell would be
845 M voxels. MM9 draws only 2 500 LT far (WorldProperties FarZ; grey fog from 1 to 2 000 LT), so:

- the voxel pass, the rooms and the face assignment cover only `NEAR_BOX` (x -5 200..9 000, y -176..800,
  z -6 500..5 440 LT): the town, the gate road, the harbour inside its fence (InvisibleBrush1) and the air over every
  roof. Polygons are clipped at the box and the grid's outer layer is solid, so the air ends there (`leaked_to_border`
  false);
- the rest is far scenery, given whole to the open-air room: 1 975 polygons (the mountains above 800 LT and beyond the
  box, the far ocean), clipped to |x|, |z| <= 12 700 LT. Dropped: 930 far polygons under the ocean surface (the sea
  bed), 92 far sky-shell faces (the sky is drawn behind the scene), 27 far invisible faces (the fence's top), 35 wholly
  past the int16 frame;
- **the ocean** (the Ocean brush, Ocean4.spr, Alpha 0.8, non-solid over the BlueWater volume), in 1 024 LT tiles (one
  face would span 36 000 native), drawn by the liquid shader (Ocean4's alias already has an MM9 liquid entry, Dook's
  Castle's). Inside the near box the party swims and dives in it (2026-11-08, "Swimming" below); the far sea past the
  box is a solid surface with no bed under it, out of reach behind the fence.

### Map-local fixes (`convert.py`, `transport.py`)

- **Glass only on MM9's translucent panes** (Thjorgard City's rule): `frosgardwindow2` also paints 12 opaque windows.
- **`split_at_walls`** (Thjorgard City's, copied to `convert_walls.py`): 1 191 cuts; floor under another room's air
  263 LT².
- **The 10 solid `greenscreen` polygons** (two small boxes on the western mountain, MM9's renderer zones) are dropped.
- **Light0** (MM9's white fill over the bay: radius 15 000 LT = 38 400 native, a stand-in sun) is left out: a BLV
  light's radius is 16-bit (the first compile failed on it); daylight in open-sky cities is the sky pass's work.
- **Boat routes** (`transport.py`, run by convert.py after each install, under the review tables lock): three
  `transport_routes.txt` rows sail to Frosgard City's docks (Sea's Fang, The Flying Bird, NPC 257's ship) and named
  `frosgardcity.odm`, which the install removes: the game refused the whole table at every start in the review root
  (found on the first tour, fixed within minutes). They now name `frosgardcity.blv`, arriving at StartPoint0 on the
  pier. Frosgard City is the first converted city that is a boat destination.
- **Yanmir's Fort's fall** (`../mm9r_yanmirsfort/convert.py` `city_arrival`, rebuilt): its trap throws the party to
  Frosgard City with `evt.MoveToMap(..., "frosgardcity.odm")` at MM9's drop height (6 554 native, outside every sector
  of the BLV); now `frosgardcity.blv` at FallingStart as built (on the ice under MM9's drop point, facing 37 degrees).
- **The bank's hatch** has only invisible faces (its mover is `Bankdoor_INV`): the Lua drives the group's leaves.

## Sky, fog and minimap

- **Sky:** the skymarker faces get `IndoorSky`, and the scene opens to the sky with `plansky3`. Review:
  `review/sky01_sheet.jpg`: 06:30, 12:00, 19:30, 23:30 from the pier, over the bay and in the gate road: dawn, noon,
  dusk sun, stars.
- **Fog, sky and daylight (2026-10-31):** MM9's WorldProperties fog, grey from 1 to 2 000 LT, in MM9's own model
  (`map: {fog: lithtech}`; no night state: MM9's WeatherMan holds it day and night). **The sky is the fog colour**
  (`map: {sky_fog: true}`, scene fog `sky: 1`): MM9 fogs its sky box from SkyFogNearZ 48, nearer than the box, so its
  whole sky is 127 grey; our clear blue sky behind the dark-grey fogged houses read wrong (devdocs/INDOOR_FOG.md
  "The sky in fog"). Daylight on the open air (`city: {daylight: true}`): MM9's ambient 100 and the sky's sun (no
  StaticSunLight here). Street lights at colour x BrightScale (`map: {bright_scale_lights: true}`: 26 of 38 lights,
  x 0.5-0.8). Reinstalled; sheets `review/dl2_compare_1200.jpg` and `_2330.jpg` (old ODM | before | after; the before
  column takes the daylight session's `dl_before` where this session's long tour ended in the death video).
- **Night fog and sky (2026-11-01):** the fog follows the daylight (scene fog `follow_daylight: true`, written by the
  shared converter where a city has daylight and fog; devdocs/INDOOR_FOG.md "Fog by the daylight"). At 23:30 the fog
  and the fogged sky are (27, 29, 39) instead of 127 grey, over the dark night streets; noon is unchanged (the same
  views old binary | new: identical but for moving people). Rebuilt (the BLV byte-identical, only the scene key);
  `review/fog_night_1101_compare.jpg` (before | after at 12:00 and 23:30, three views). Scenarios pass.
- **Minimap:** MM9's painted `ui/maps/frosgardcity.pcx` (catalog entry kept). No outlines.

## Content

- **People (50 actors, all friendly at the start).** The old import's NPC records (names, rows, RUDE ids) with MM9's
  bodies; they stand where MM9 placed them. Jarl Tryggva (RUDE 180) sits in her hall; Tamur Leng (309) and Forad Darre
  (2) are hidden until the Battle of Frosgard. Hostile-family picture rows (Tamur, Forad, Tryggva) take a peasant
  family's relations (Hall of the Gods' route). The old import's three "Dog" actors were two posed dog props and an
  ambient sound: here two sitting dogs (decorations) and nothing.
- **Shops:** the shopkeepers stand in their shops; shops close from 20:00 to 06:00 (key 5017).
- **Decorations:** 177 placements from the props project (8 models built, 63 reused, rows 2623-2636).
- **Doors:** 72 movers: MM9's swing doors (`rotate`, pairs open together), 21 locked facade doors (MoveDist 0, a click
  says locked), the bank's counter hatch (a click opens it and the banker's dialogue), the 37 ice floes.
- **Chests: none** (MM9 places no TreasureChest or TreasureBag here).
- **Exits and starts:** ExitTrigger0 (the north gate road to the Frosgard wilderness, row frosgardcity/46); starts
  FallingStart (from Yanmir's Fort), FrosgardCityStart (from the wilderness), StartPoint0 (the pier: the boats),
  TownPortal, each on its floor facing 90 - ry.

### Scripted objects (`citylua.py`; every script read: `work/scr_spec.md`)

| Script | Native |
| --- | --- |
| ForadWorld.scr "Frosgard" | location key 1029 (1024-1033 cleared), shop hours 5017 |
| NPC180.scr (Jarl Tryggva, RUDE 180; United.inc) | click: the five other clans (UNITED.inc :TryygvaInit: 82, 38, 51, 63, 34 -> 178; until 2026-11-08 Sven's list with 74, Tryygva's own pledge, in place of Sven's 34: fixed in `citylua.py` CLAN_KEYS, playthrough segment 37 and `tests/scenarios/mm9/tryygva_united_keys.yml`). Exit: Yanmir's Fort 70 -> 172 (58 000 xp, 10 000 gold), the ice 73 -> 175 (30 000, 3 000), clans united 83 -> 179. Away on 104 or 40 unless 108 |
| BreakIce.scr, FrosgardShooter.scr, NPC215.scr | the ice quest: Tryggva gives 71, the powder seller's delivery (1022) puts a powder barrel on the ice; its click or its breaking (MM9: its destruction starts the cannon and the cinema) starts the cinematic `break_ice` (below), whose steps break the 37 floes in MM9's waves, each dropping under the ocean surface; 72 + 8 000 xp (with 71), else 174. Load with 72 or 174: no ice |
| NPC214.scr, NPC213.scr (Douglas, Robert) | their banter, the cinematic `bob_and_doug` (below), when the party comes within Douglas's sight; key 111 |
| NPC209.scr (the dockmaster) | with 72: the dock schedule (item 562), key 378 |
| NPC206.scr + BankOrb.inc (the banker) | the hatch opens his dialogue 206 (322 + item 252 -> 330); the exit shuts the hatch; 330 with 333: item 252 taken, 327; 331-336 -> 337 (20 000 xp, 15 000 gold) |
| NPC181.scr | item 184 -> 241 on the click; 248 -> 249 (63 000 xp, 5 000 gold), the Ranger promotion of 417-420 |
| NPC183, 184, 188 | 295 -> item 245; the brewmaster's keg (302 -> 303 + item 249; 307 -> 308; 309 -> 310); the ritual (257 -> 258, item 430) |
| NPC190.scr, ChangeModel.scr | the maypole: 267 + 500 gold -> 268, and the new maypole stands (two decorations, cogs) |
| PLEDGE.inc (NPC190/191/193/195/196/197/199, Pledge.scr 217, 218) | each one's dialogue exit: with 265 and at most one of the pledges 269-274 missing, key 277, 5 000 xp, the quest sound (the Green Man's last row then shows; 2026-11-06 audit G3) |
| HideModel.scr "278 UnHide" | the runestone shown with 278 |
| BattleMan.scr, NPC309.scr, Forad.scr | the Battle of Frosgard: entering on 104 (once, 377): Forad and Tamur appear, the Horde (MM9 Horde A/B/C rows) at four markers, clan soldiers (the town guard row) set against them, and the Horde against every townsperson's row (HateNPC.scr AddEnemy NPC, one way, 2026-11-06); Trigger0 (a pad across the square) a second wave. Tamur's exit with 106: 190, 412 000 xp, he leaves and Thorolf appears. Forad: first click 480 + 800 xp; his dialogue's close during the battle turns him hostile; else 368 + 4 000 xp, gone on 29 |
| NPC378.scr (Thorolf, three copies) | as Sturmford City; the third comes after Tamur and stays (also over a load) until his summons gives 107 (Deviation, below) |
| Retainer.scr (238) | hidden while hired (460) |
| TownPortal.scr "Frosgard" | cleansing the altar: 5015 (the dirty altar hides and its clean twin `mm9_portalclean` at its place shows, also on load: `../mm9r_common/dungeon/town_portal.py`) |
| BookLetter.scr (Prop6-9), Book.scr | letters 462-465; the book's pages |
| WellMMIX0 | a click answers, no bonus (MM9's class not traced) |

**Left out:** the cannon's night test (NPC215 22:00-04:00) and the test barrel; AddNPC (Tamur joining the party); the spike pit's damage in Tryggva's fire pit; 11 PerceptionBrushes
(door hints); the breakable windows; MM9's snow (31 `Snow` volumes: weather in open-sky sectors is specified, not
built); ambient sounds. (The battle has no camera: BattleMan.scr's Camera3 lines are commented out.)

### Cinematics (2026-11-06; devdocs/mm9_rework/MM9_CUTSCENES.md)

`citylua.scenes(actors)` builds both (`mm9r_common/cutscenes.py`); `map_script` appends their Lua block (steps as map
events, each once; the done event runs any left) and `convert.py` installs
`worlds/mm9/maps/frosgardcity.cinematics.yml`.

- **`break_ice`** (BreakIce.scr :OnStart..:Done, IceCam1.scr; events 36000 done, 36001-36015 steps; 16.3 s). Started
  by the barrel's click (232) or its death (30607, chained after the shared explosion: DeathTriggerTarget Shooter0
  Start); the cannon volley (T_CANNON) stays on its timer. Timing from the script's waits and Camera1's MoveToPos
  arrival (576 LT at 150 LT/s = 3.84 s): the party's view 3 s (fade out at 2), Camera0 3-7 s, Camera1's move to
  IceMarker2 7-10.84 s, Camera2 10.84-15.34 s, the party's view fading in 15.34-16.34 s; letterbox from 3 to 15.34.
  Steps: Shooter1-4's bolts (4, 6, 6.2, 6.3 s; each a FireMissile straight down) and their floes 0.4 s later (27, 17,
  18, 6), floes 15, 26, 25 (7.7, 8.5, 9), :Group1-3 (11.94-11.96 s; DestructableBrush16 here: no shooter over it),
  :GivePoints at 13.84 s (every floe down, 72 or 174, 8 000 xp). Cues: fades, letterbox, the six iceimpact.wav. A skip
  fires the remaining bolts at once over the sunken floes (harmless). Camera gate (`mm9r_common/camera_gate.py`, run by
  the pilot and the install): Camera1's path is moved 400 units west of MM9's, beside the pier at MM9's height
  (`CAMERA1_SHIFT`: under the pier it crossed the rebuilt T-head; the gate's 128-unit lift put the eye on the deck with
  the floes hidden); Camera2 (shot 4) is accepted by the `cinematics_gate:` entry in `overrides.yml` (it hangs over
  the harbour at the map's edge and looks inward). Check: `captures_break_ice/regate/sheet.jpg`.
- **`bob_and_doug`** (NPC214.scr :OnStart..:OnSpeak9 and NPC213.scr; events 36050 done, 36051 the key; 35.1 s). No
  cameras: an ambient cinematic (`ambient: true`: no shots, letterbox or fades, no input lock, the HUD stays). Started
  by the 1 s poll once Douglas sees the party (`evt.ActorSeesParty`, his SightDistance 600 LT = 1 536 units, line of
  sight: they stand in a house) without 111 (MM9: his OnFoundPlayer). Step: key 111 at 0. Cues: the two turn to each
  other (0.3 s), then nine lines on MM9's fixed waits (2, 3, 7.8, 3.8, 6.5, 2, 3, 4, 3 s; the wavs are 1.6-7.2 s and end
  inside them): each a voice (`voices\cinema\bobanddoug\NN.wav`) and the speaker's looping conv clip (Douglas
  conv2/conv5/conv4, Robert conv1), the other back to `stand`. MM9 has no text for the lines: no subtitles. Saving waits
  until it ends (the scenario checks it).
- **Test without a conversion:** `cinematics_pilot.py` writes the yml and the installed Lua with the changed parts
  (its replacements) into `output/mm9_rework/cinematics_pilot_root`; from `output/mm9_rework/cinematics_pilot_run`
  `build/game/openyamm --world mm9 --headless-run-scenario <abs>/cinematic_<id>_play.yml` and `_skip.yml` (both
  ids pass, and `scenario_scripted`, `scenario_shops`, `scenario_doors_exits` there). `scenario_scripted` now waits
  17 s for the ice. Captures: `output/mm9_rework/cinematics_pilot_run/captures_break_ice/sheet.jpg`, `sheet2.jpg`,
  `captures_bob_and_doug/`.

## Quality gates

1. **Every DAT world model has a rule** (rules plus `model_patterns`). Skipped, with reasons: the sky box and the TOD
   star shell, 14 AIBarriers (MM9's AI only), 31 Snow volumes (weather), the BlueWater volume (its top is the Ocean
   brush), VisBSP, the PerceptionBrushes and the AI tracks.
2. **Sealed air:** `leaked_to_border` false (the near box's sealed grid), 2 seeded air components. 322 faces without air
   in front dropped (`work/dropped_faces.json`): faces between brushes, under the ocean surface, under the walls.
3. **Every portal joins two rooms:** `portals_without_two_rooms` 0.
4. **No holes:** the 28-view sheet `review/v03_compare.jpg` shows none (v01's bad views were tour positions on roofs
   and in walls, moved). Floor holes 0, cracks 0. Floor check 263 LT².
5. **Review sheet:** MM9 original (the old ODM import, view distance unlimited) | native BLV, **28 eye-level views**
   (18 docks, pier, bay, square, streets, gate road; 10 interiors: hall, tavern, temple, training hall, two shops,
   magic shop, three houses): `review/v03_compare.jpg`. Same geometry, props and people; ours is far hazier (MM9's
   fog), the bay reads grey under it; the old import shows Forad Darre in the square (hidden until the battle here)
   and MM9's tooth in colour (fogged here).
6. **Walkability** (`work/audit.log`): 210 steps, 9 flights, 8 unreachable regions, 5 pits, 1 actor note. The regions
   are the counters (102 over the floor: the tavern's bar and three shops), the ice floes (38 over the ocean, which the party climbs: 15 LT),
   the pier (116 over the ocean, which monsters cannot climb; the boats land the party on it; the walk from the pier to the shore was not probed) and the north mountain ledge (155). The pits: the fire
   pit in Tryggva's hall (102 deep, MM9's burning logs over its spike pit), a corner of the bay and three pockets of the
   snow field under the north slopes (way out 0: the audit's monster rule, not a trap for the party). **Half steps** (6, in
   `work/probes/half_step_<k>.yml`): steps 0-2 lie in the invisible wall behind the north exit (the walk stops at the
   wall after 112 units; the exit fires before it), 3 and 4 on roofs 630-645 LT up (nobody gets there), 5 on the shore
   (walked over: 476 units, 20 up).
7. **Scenarios pass** (headless, real clicks where the engine picks):
   - **`scenario_doors_exits` (22 steps):** the tavern's door stops the party, opens on its click, the party walks in
     (up its 44-unit doorstep); a facade door says locked and stays shut; the bank's hatch opens with dialogue 206;
     the north gate's exit raises its transition (object 46).
   - **`scenario_shops` (26):** Tryggva Ironhands' (RUDE 201) and Thora the Skull-toucher's (203) dialogues open by
     `press_interact`, and their service rows open the shops.
   - **`scenario_scripted` (55):** 1029; 5017 at night and not by day; a letter; the altar (5015); the maypole (268);
     the powder barrel breaks the ice (72; the first and last floes down); the dockmaster's schedule (378); Tryggva's
     ice reward (175); the battle starts on 104 (377).
   - No chest scenario: none in MM9.
8. **Starts:** four, on their floors (`build_report.json` `starts`); the tour's first view is the pier start.
9. **Compiler:** unchanged; the existing `mm9_compile_indoor_source`.
10. **Lights:** 38 BLV lights; Light0 left out (above).

## Performance (counts; frame rate needs a single-session run)

Same 28 views (`review_tour_v03.yml` / `v03_original`), `logging.performance_trace` + `logging.indoor_visibility`,
minimized isolated desktop runs on a shared machine.

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Textured batches |
| --- | --: | --: | --: | --: |
| **Frosgard City, native BLV** | **157 / 289** | **41 900 / 111 200** | 2 / 6 | 76 / 113 |
| Frosgard City, old ODM import | 591 / 861 | 48 100 / 112 300 | – | – |
| (Sturmford City, native BLV) | 218 / 385 | 30 600 / 70 800 | 5 / 12 | 96 / 238 |

- Triangles are close to the old import's: the open air is one sector, so every exterior and the mountains are drawn
  from anywhere outside; draw calls fall to a quarter.
- **Map load** (`OPENYAMM_MAP_LOAD_TIMING=1`, `work/perf/load_*.log`, 3 each, other agents running): BLV 2.33 / 3.97 /
  4.21 s (median 3.97, asset load 1.38), old ODM 2.67 / 5.59 / 5.98 s (median 5.59, asset load 2.35).

## Converter and engine changes

- **Engine:** none for the conversion; the sky in fog (scene fog `sky`, 2026-10-31) and the fog by the daylight
  (scene fog `follow_daylight`, 2026-11-01) were built for this city (devdocs/INDOOR_FOG.md). The tour fix of
  2026-11-01 (below) is engine debug code.
- **Shared converter:** none (the converter lock was not taken). Everything is map-local: `convert.py` (the near box:
  a sealed `build_voxels` and the far scenery after `assign_faces`, both wrapped in this project; glass; the cached
  `crossing_portals`; greenscreen; the ocean tiles), `convert_walls.py`, `transport.py`.
- **Other projects:** `../mm9r_yanmirsfort/convert.py` `city_arrival` and the map name of its fall (rebuilt; its
  scenarios pass).

## Open items

- **Night (done 2026-11-01):** the grey fog and sky stood light over the dark night streets; they now follow the
  daylight (above).
- **Long screenshot tours ended in the death video (fixed 2026-11-01).** Found with a repro tour (`hp show`, `time`
  per shot; `work/tour_death/`) and a breakpoint on the cutscene screen: `processPendingPartyDefeat`, the one member
  Dead at full HP, set by `Party::updateDaysWithoutRest` from `setDebugClockMinute`. The indoor renderer ran the game
  clock during the tour's hold, so each repeated `time:` moved the clock a day; after four days without rest the
  ordinary rule killed the party. Not a city fault and not reachable in play. Fix and proof: CITY_PLAYBOOK "Daylight
  and fog"; `review/tour_alive_1101_sheet.jpg`; the 16-view `dl2` tour and a 32-shot one (8 views x 4 times) end
  alive on day 1 and day 9 (the old binary: death video on both).
- **One open-air sector** of 11 787 faces: the town has no streets to cut. If a frame-rate run shows a cost, the next
  step is splitting the far scenery off behind portals at the near box's faces (a converter feature).
- **Not carried:** the cannon's test, Tamur joining the party, Perception hints, breakable windows, MM9's
  snowfall and ambient sounds.
- **Townsfolk** draw as stand-in peasants until the MM9 town NPC models exist (another session).

Test of the pledge drive (PLEDGE.inc, 2026-11-06): `scenario_pledges.yml`.

Rebuilt 2026-11-06 21:35 (the shared water rule, HateNPC): MM9's one volume, BlueWater0 (the harbour and the sea, top
-366, 986 deep), is the scene's water, but its 123 sea surface faces stay solid wading floors
(`swim_surfaces_kept_no_bed`): the converter builds no seabed under the open sea (152 743 bed-hole samples in
build_report.json `water`), so a non-solid sea would drop the party out of the map. To swim it, the seabed (DAT
Terrain under the harbour) and the walls down to it must be built, as outdoor_blv.py `swimmable_sea` does for the
regions. The ice (FROSPPGKGO) is not a liquid face and stays solid. Scenarios scripted, doors/exits, pledges, shops
pass.

### Swimming (2026-11-08)

The harbour is swum and dived as in MM9 (user: "it needs to be divable"). The near box (convert.py NEAR_BOX) now reaches
from -560 LT, under the harbour's bed: MM9's world floor (PhysicsBSP) at -528 under the whole bay, Terrain0's slopes up
to the shore, the sunken frosgardwood crib (top -192) under the floes south of the pier. With the bed built, the shared
water rule makes all 123 sea tiles in the box non-solid (`swim_wading_surfaces_nonsolid` 123); bed holes 152 743 ->
767, all on the box's own edge lines (x 9 000, z -6 500) outside the fence. The fence (InvisibleBrush1, down to -512)
keeps a swimmer in the harbour, so outdoor_blv.py's SeaEdge walls are not needed. Air 40.6 M -> 55.2 M voxels; faces
15 185 -> 15 227; rooms, portals and starts unchanged (start 0 under FallingStart stays dry on the ice, z -328).

The broken ice floes (overrides.yml) now sink to rest on what lies under each (the highest floor under its footprint,
9 x 9 samples, + 2 LT): 364-382 LT onto the bed, 314 for DestructableBrush21 over the slope, 46 for 27, 34 and 35
onto the crib, instead of 120 under an opaque surface a diver now sees through.

`scenario_swim_check.yml` (swim_check.py, its point moved by hand: the script picked the far sea, which has no bed):
the party on the bed at LT (6 000, -1 800), 986 under the top with its eye under, then Fly Up to the surface; passes
with the other four scenarios. Lighting: layout-only bake + lightmap_transfer.py again (coverage_core 0.949, 76 charts
vertex-lit). Captures: the surface, under water and looking up at the surface from below.

## Approach talks (2026-11-07)

- **Forad Darre** (FORAD.scr): BattleMan.scr's `Appear` runs his :OnAppear, `OnFoundPlayer OnTarget 256` ->
  `OnTargetWithinDist 16 Talk` (DoRude 2): once the battle has shown him he opens his dialogue himself when the party
  comes near, and its close with key 104 turns him on the party. Before, only a click did.
- **Thorolf Ratatoskssen** (NPC378.scr, Thorolf0/1 with key 83, Thorolf2 after Tamur Leng): `OnFoundPlayer :OnFound`
  -> `RunTo <player> 16 Talk`: he runs up to the party he sees and talks (DoRude 378, his voice), the other copy goes.
  The same in Sturmford, Thronheim, Drangheim, Guberland and Thjorgard City (their citylua.py call
  `lua.thorolf_approaches`; they take it at their next conversion).
- Shared: `../mm9r_common/dungeon/lua.py` `approach_talk` (a 4 Hz poll, event 906: the talk fires when the party's
  feet are within his radius + the party's + 16 LT, MM9's gap between the bodies; `run` follows the party once he
  sees it within his SightDistance; once per visit). Engine: `evt.OpenMm9Rude(rude, actor)` /
  `MM9.openRude(rude, actor)` name the speaker, so a talk opened from a timer still runs his OnRudeExit event.
- Checks: `scenario_scripted.yml` (make_scenarios.py): after the battle starts, no talk 500 away; at 110 the
  dialogue opens without a click (RUDE 2) and its close turns him hostile; with key 83 Thorolf0 runs over from 700
  and talks (RUDE 378), Thorolf1 removed.

## Update 2026-11-08: a load during the battle (MM9 playthrough)

The map load hid Forad Darre and Tamur Leng on every load (`show(0/1, false)`), and the battle shows them only once
(key 377), so a save and load in the city during the battle, before Tamur joined (key 106), hid Tamur for good: a
story soft-lock (Krohn needs Thorolf's 107, which comes after Tamur). Checked headless before the fix: Tamur visible
after the arrival, hidden after `save_game`/`load_game`. In MM9, `NPC309.scr :Main` and `Forad.scr :Main` hide them
once, when the object is made (`Gosub Vanish`; no `OnPostSaveLoad`), and a save keeps their flags, so `citylua.py`
now hides them at a load only before the battle (`not has(377)`). Map Lua only (`convert.py --scratch`: the runtime
Lua differs by these two lines; installed into `assets_dev` and the review root).

**Deviation:** Thorolf2 (the summons after Tamur) is shown at a load with 106 and without 107. MM9's `NPC378.scr
:Init` runs on every save load (`OnPostSaveLoad Init`) and hides the Frosgard copy, which strands a party that saved
between Tamur and the summons; here he stays until his talk. Verified headless (playthrough prep `tamur_reload.yml`):
Tamur shown after a mid-battle load and talked into the party, Thorolf2 shown after a load between 106 and 107 and
talked to, both hidden after a load with 107.

## Forad's bow (2026-11-11)

`Forad.scr :OnUse` turns him to the party (`FaceObject`) and plays `bow` once; `citylua.py` does the same on his click
(`evt.FaceActorTo`, `evt.PlayActorClip(0, "bow")`), and clears that presentation when the battle's talk turns him on
the party. Checked headless (the click turns him -19 degrees to the party and plays `bow`). `scenario_scripted.yml`
fails at its Thorolf step (step 80: Forad's dialogue 2 is the last started, not Thorolf's 378) with the Lua before this
change too: an older failure, not from the bow.

## Forad talks once (2026-11-11)

`scenario_scripted.yml`'s Thorolf step failed because Forad's approach talk fired again: the map loaded with the party
beside the hostile Forad, his dialogue opened by itself a second time and the open dialogue held the world still, so
Thorolf never ran over (his `evt.MoveActorTo` stayed pending). In MM9, `Forad.scr :Talk` and `:OnUse` set `bTalking`,
which only `:Forad` (the close without key 104) clears, and `:OnTarget` exits while it is set: after the battle's talk
he never talks by himself again, on later visits too (MM9 keeps a script's variables in the save). `citylua.py` now
sets the map variable `ForadTalked` in his dialogue's close with 104 and arms his approach talk only without it (the
shared approach talks stay once per visit: Thorolf's `:OnRude` clears his `bTalking`). Map Lua only (`convert.py
--scratch`: the runtime Lua differs by these lines; installed into `assets_dev` and the review root);
`scenario_scripted.yml` passes.

