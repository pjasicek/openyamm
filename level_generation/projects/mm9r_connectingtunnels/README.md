# MM9 rework: Connecting Tunnels (`connectingtunnels.blv`)

MM9's Connecting Tunnels (the mine tunnels under the mountains between Thronheim and Yorwick: long winding lantern-lit
galleries, a blue-lit hall with a grave between two glowing pillars, a rock fall closing the climb to Yorwick's upper
exit) converted from its DAT world into a native indoor map (BLV: sectors, portals, rotating and linear movers, lights,
three exit volumes) on the shared dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)).
Built into the isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's
decoration rows and the prop models ([props project](../../props/mm9_connectingtunnels_claude/README.md)). No x4
textures yet.

Status 2026-10-31 (overnight run): geometry (31 rooms from 32 archway cuts found automatically along the tunnels), 4
movers, 76 BLV lights plus 7 bake-only fills and 8 LIGHTDEFS lights, 3 exits, 119 decorations, 2 chests, 38 actors with
MM9's bodies, the DAT's object wiring (the coffin, the rock fall), MM9's model lighting, baked lighting calibrated to
MM9's DAT lightmaps with its blue world ambient, the player-light stand-in for the darkest tunnels.

## Build and review

```sh
python3 level_generation/projects/mm9r_connectingtunnels/work/cuts/tunnel_cuts.py      # archway cuts from the air voxels
python3 level_generation/projects/mm9r_connectingtunnels/work/cuts/apply_cuts.py       # into overrides.yml (minus drop.txt)
python3 level_generation/projects/mm9r_connectingtunnels/convert.py --plan             # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_connectingtunnels/convert.py                    # build, compile, install (2.5 min)
python3 level_generation/projects/mm9r_connectingtunnels/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_connectingtunnels/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_connectingtunnels
python3 level_generation/projects/mm9r_connectingtunnels/work/reach/make_probes.py     # + probe_flights.yml
python3 level_generation/projects/mm9r_connectingtunnels/make_tour.py v02 [--original] # lighting<n>: the lighting subset
bash level_generation/projects/mm9r_connectingtunnels/work/run_tours.sh v02 [--set video.lightmaps=false]
bash level_generation/projects/mm9r_connectingtunnels/work/run_tour_original.sh v02    # view_distance=unlimited, x + 17000
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v02 <project>/review/v02_original
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_connectingtunnels --samples 128
python3 level_generation/projects/mm9r_connectingtunnels/calib_lightmaps.py 0.45 0.3 1.2   # recompose + zones
python3 level_generation/projects/mm9r_connectingtunnels/work/view_luma.py <review folders>  # per-view luma
```

## Numbers

- **Frame: `native = (LT.x, LT.z, LT.y) * 2.56 - (17000, 0, 0)`.** The DAT spans LT x -1 184..14 512 (native -3 031..
  37 151), over int16, so this is the first converted map with an offset: native x -20 031..20 151, y -15 565..12 001, z
  -1 925..7 352. The shared table writer keeps the old map's frame for transition rows; `convert.py`
  `offset_transitions` moves this map's three exit volumes and the three arrivals into it (Thronheim's ExitTrigger6,
  Yorwick's ExitTrigger7/8) by the offset and lands each arrival on the floor. `props.json` is in the old frame
  (the props project's placement check against the old bake needs it); `populate` shifts it (`work/props_native.json`).
  `make_tour.py --original` adds the offset back for the old map.
- DAT: 3 849 source polygons (PhysicsBSP), 3 488 merged; 336 dropped as having no air in front (the backs of the
  mine's support beams against the rock, 278 woodgrain02; the outer shell's dirt and cliff backs; the walls behind the
  rock fall).
- BLV: **4 254 faces**, 3 664 vertices, **32 sectors** (31 rooms), **32 portal faces** (32 archway cuts), **4 movers**,
  **76 lights**, faces per sector max 836 / median 88, 16 translucent faces. The outline limit was not hit.
- Content: 119 decorations (34 in the busiest room, the coffin hall's 28 candles), 2 chests, 38 actors: 10 Skeleton
  Warriors, 5 Skeleton Masters, 6 Spectre Dagrells, 5 Venomous Dagrells, 5 Annelids, 4 Bloodsuckers, 3 Vampirs (rows
  9136/9137, 9148/9149, 9195-9197). No pads, no touch triggers in the DAT. 12 of the 38 actors draw without texture
  (missing MM9 monster art: another session builds it).
- Lights: 83 MM9 `Light` objects: 45 lantern lights (255/215/132, BrightScale 0.35), 28 candle lights (47/47/255,
  0.8, radius 115 LT), 2 cyan (151/255/255, 1.0), 8 blue fills (0/73/147 and 0/0/255, 0.12-0.35). 76 in the BLV; the
  coffin hall's 7 big fills are over the four-per-point cap and bake-only. No DirLights, no fog (`EnableFog 0`).

## Rooms: automatic cuts along the tunnels

The map is one long tunnel network (one air component, 1.09 M voxels) with almost no chambers, so Thjorad Mine's
chamber-mouth cuts do not apply. `work/cuts/tunnel_cuts.py` takes the top view of the air and the geodesic distance over
it from StartPoint0; every 1 400 LT of that distance, each connected piece of the distance band that is a plain tunnel
there (one piece 320 LT before and one after it, joined through it: no junction, no tunnel end) and narrower than
640 LT gets a cut across the tunnel through the middle of its air column (a column with two air runs, where the spiral
to Thronheim passes over itself, is skipped). 34 cuts came out; t05 and t08 (in the north-east chamber and its tunnel)
left both sides one room and are dropped (`work/cuts/drop.txt`); 32 cuts give 31 rooms, 0 portals without two rooms
(`work/cuts/cuts.png`, `work/rooms_large.png`). The floor check lists 42 266 LT² of floor under another room's air
(38 entries, largest 5 684 LT²): 16 LT strips along the cuts across 250-400 LT wide tunnels (Chasm of the Dead's
note: harmless).

## What each DAT object became

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world (`VisBSP` has no UserPortals) |
| `coffin door left`, `coffin door right` (RotatingDoor pair, Sticky, PushOpen, `RotationAngles` ±30° about the outer edges) | two `rotate` movers, the grave's lids flush in the coffin hall's floor; a click swings both (event 60) |
| `DestructableBrush0` (HitPoints 10, DeathTriggerTarget `DestructableBrush1` Destroy), `DestructableBrush1` | the rock fall in the tunnel north of the west junction: scene destructibles 127 (10 hp) and 669 (TriggerDestroyOnly), static faces with cogs 20127/20669 (`motion: break`, 2026-11-06); weapons break 127, a click on either rock deals 127 a killing blow (event 38127); 127's death (event 61) breaks 669 (stonecrumble.wav, stone dust, mm9:smoke) |
| `TreasureChest0` (Chest3), `TreasureChest1` (BlackChest x0.95, Locked 1, in the grave) | chests 1 and 0 (events 42, 41); the grave's chest opens only while the lids are open |
| `Light` x83 | BLV point lights (colour x BrightScale / 0.35, below), 7 capped fills bake-only |
| `Prop` x77, `CandleProp` x28, `BonePile` x9, `Barrel` x3 | 3D decorations (props project); 12 MM9 props pitched or rolled 4-10° are tilted model variants |
| `SkeletonWarrior`, `SkeletonMaster`, `SpectreDagrell`, `VenomousDagrell`, `Annelid`, `Bloodsucker`, `Vampir` (38) | actors at their DAT positions, facing 90 − ry, MM9 bodies (ABC extents x Scale x 2.56: skeletonwarrior.abc 38/189, dagrell.abc 64/148, nosferatu.abc 31/169, the Vampirs at Scale 1.2 37/203) |
| `StartPoint0/1/2` | starts 0 (from Thronheim, east end, facing north), 1 (Yorwick's lower exit, west end), 2 (Yorwick's upper exit, north-west) |
| `ExitTrigger0/1/2` | MM9 positioned transition volumes to Yorwick (`YorwickExit1`), Thronheim (`ConnectingTunnelsExit`), Yorwick (`YorwickExit2`) |
| Lichwindow pillars (8 polygons), yanmirsolidice1 caps (8) | translucent faces (`glass`, two-sided, opacity x texture alpha 43-138 and 191); the ice's LIGHTDEFS teal (16/128/128, r 640) as 8 bake-only lights, one per polygon at 0.25 |
| `AIRail` x346 (`AITrack*` models), `AmbientSound` x73, `OutsideDef0`, `WorldProperties0` | not built (AI helpers; ambient sound later) |

## Scripted objects (`worlds/mm9/events/maps/connectingtunnels.lua`, written by `convert.py`)

The DAT has no `.scr` scripts (no object has a `ScriptName`); its only logic is object wiring:

| MM9 wiring | Objects | Native |
| --- | --- | --- |
| `coffin door right` OpenTriggerTarget0 `TreasureChest1` `unlock`, CloseTriggerTarget0 `lock` | the grave's lids, the black chest | a click swings both lids and toggles map variable `CoffinOpen` (event 60); the chest's event opens it only with `CoffinOpen` 1, else locked_door01.wav and "The chest is locked." |
| `DestructableBrush0` DeathTriggerTarget `DestructableBrush1` `Destroy` | the rock fall | weapons (or a click, event 38127) break DestructableBrush0; its destroyed event 61 sets `RockFall` and `evt.DestroyDestructible(669)` |

Unmatched: none (no scripts); the MM9 AI rails (`AITrack*`) and ambient sounds are not built.

## Baked lighting


Profile `tools/lighting/baked_indoors/profiles/mm9_connectingtunnels.yml`: 128 samples, 3 bounces, `direct_scale` 0.45,
`bounce_scale` 1.2, `ambient_scale` 0.3, `ambient_colour` (0.64, 1.06, 1.48), `max_lighting` 1, `texture_lights`
per polygon at 0.25 (the ice caps). Bake-only: the 7 capped coffin-hall fills (BrightScale / 0.35) and 8 LIGHTDEFS
lights. Sector minimum light 20 (13 rooms lower: the player-light stand-in, below); `map: {model_lighting: true}`.
Bake about 15 min through `bake_slot.sh`; `stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list
the map.

**Light colours.** MM9 weights each Light by its BrightScale; `convert.py` `scale_lights` writes colour x min(1,
BrightScale / 0.35) into the BLV (Thjorad Mine's route): the lanterns as authored (model lighting `light_scale` 1),
the fills at their share, matching the shared bake's weight for the capped ones. The candles (0.8) and cyan lights
(1.0) cannot go over 255, so they bake at 0.44 and 0.35 of MM9's weight relative to the lanterns (the candles' radius
is 115 LT: a small effect).

**MM9's blue world ambient (shared tool change).** MM9's lightmaps are a warm pool under each lantern on a blue floor:
WorldInfo `AmbientLight` 15/25/35 shows wherever no light reaches (the tunnels' B/R 1.0-1.65, the coffin hall and
north-east chamber 6-7). The bake's ambient floor was grey: matching the level left the tunnels orange (B/R 0.6-0.75),
matching the hue doubled the level. `tools/lighting/bake_indoor.py` now takes an opt-in profile key `ambient_colour`
(an RGB factor on the ambient floor and the fallback actor ambient; default white, so every other profile bakes as
before; documented in `devdocs/INDOOR_BAKED_LIGHTING.md`). Here MM9's colour normalised to luminance 1.

Calibration (AGENT_BRIEF, Brightness: against MM9's own DAT lightmaps; `calib_lightmaps.py` recomposes and runs
`../mm9r_common/hue_vs_lightmaps.py` over `hue_zones.py`; `work/calib_lightmaps_final.txt`). Lightmap luminance ours /
MM9's per zone and hue (B/R, G/R MM9 / ours): coffin hall 0.84 (7.20/3.77, 4.52/2.36), south tunnels 1.09
(1.35/1.49, 1.27/1.28), centre 1.38 (1.65/1.68, 1.47/1.37), north-east 1.36 (6.33/3.30, 4.01/2.16), east spiral to
Thronheim 0.98 (0.93/1.00, 1.04/1.06), south-west 1.02 (1.02/1.12, 1.09/1.11), north-west 1.14 (1.21/1.30, 1.19/1.19).
The centre and north-east carry most of the player-light floors (above), which raise them over MM9 by design. The two
blue halls (coffin hall, north-east chamber) stay half as blue as MM9's (B/R 3.3-3.8 against 6.3-7.2): their blue
fills are BrightScale 0.12-0.3 against the lanterns' 0.35 as in MM9, but our falloff spends less of a 1 500-2 500 LT
radius than MM9's; they read clearly blue on screen (lighting_v02 a05-a07, r01, r22). The first draft (Thjorad's
scales, grey floor) was 1.2-2.7 times MM9 and orange (B/R 0.6-0.75 in the tunnels). No real MM9 screenshot of this map
exists (`overnight/real_mm9/`).

**The player light's stand-in** (AGENT_BRIEF "No pitch-black rooms"). MM9 carries a player light (WorldProperties
`PlayerLightOn 1`) the engine lacks; matched to the lightmaps, the tunnels far from any lantern drew at screen luma
8.7-9.9 (review b01: r02, r03, r18-r21, r24, r28, and the rock fall's junction). `convert.py` `ROOM_LEVELS` gives
those 9 rooms sector minimum light level 14 (an ambient floor about 1.55 times the map's) and 4 rooms at 11-12 level
17 (about 1.27 times); the bake's ambient floor follows. Level 10/15 (review v02 first pass) made them 15-16.5, as bright
as the lit tunnels, and was lowered. Revert: `ROOM_LEVELS = []`, rebuild and rebake.

Screen means (information only: the capture is the old import in our outdoor renderer, not MM9):
`work/brightness_v02.txt` (39 views, centre crop): capture 19.4, native unbaked 64.6, native baked
16.9; darkest baked view 13.0 (r02). Views off by more than 10 % (baked / capture): a01 0.59 (the capture's bright wooden arch), a02
0.79, a04 rock fall 1.49, a05-a07 coffin hall 0.61-0.63 (the capture's flat bright blue), a08 1.13, r01 0.64, r04 0.63,
r05 0.79, r06 0.64, r07 0.83, r09 0.83, r10 0.70, r11 0.87, r12 0.89, r14 0.74, r17 0.74, r23 0.77, r25 0.76, r31 0.71
(lantern tunnels: the capture's grey brightening), and the stand-in rooms r02, r03, r18-r21, r24 1.34-1.51, r27, r28
1.27-1.28 (capture 8.7-10.7).

**Model lighting against the old path.** The coffin hall's 7 fills are over the four-per-point cap, so both paths
were compared (Thjorad Mine's method): the same bake, the scene with and without its `model_lighting` block
(`work/ml_compare.py`, `work/scene_old_path.yml`, `review/model_lighting_compare.jpg`, `work/model_lighting_props.txt`).
Prop crops against the capture: the coffin hall's skeleton x0.53 old path / x0.77 model lighting, crates in r26 x0.76 /
x1.37, a crate in r27 x0.00 (black) / x1.61, TreasureChest0 x1.33 / x1.69, an Annelid (actor) x0.74 either way. The old
path draws props black or dark wherever the bake carries the light (the frame-ambient subtraction); model lighting
keeps every prop visible, a little brighter than the walls as MM9's ModelAdd makes them, so the map keeps
`model_lighting: true` (ambient 15/25/35 from the DAT's `AmbientLight`, ModelAdd 30).

## Checks

1. Every DAT world model has a rule (the build stops otherwise): PhysicsBSP static, 346 `AITrack*` skipped (AIRail),
   VisBSP skipped, the four movers.
2. Sealed air: `leaked_to_border` false, one seeded air component (1 090 483 voxels), no `seed_exclude` needed. Dropped
   faces (336): beam and wall backs against the rock, the outer shell's backs; no partition among them (`thin_walls:
   true` on anyway).
3. Portals: 32, each joins two rooms (`portals_without_two_rooms` 0; t05, t08 dropped).
4. No holes: every view of v01 and v02 (39 views, three columns) looked at; geometry matches the old import in every
   view. Floor check: 42 266 LT² under another room's air, the strips along the cuts. Mixed faces: 105 with a minority
   over 20 %, rock walls and floors running across cut planes (largest a woodgrain beam split 83/26 between rooms 11
   and 15).
5. Review sheets: `review/lighting_v02.jpg` (39 views, capture | native unbaked | native baked: looked at, every view),
   `review/v02_compare.jpg` (capture | baked, the same shots), `review/v01_compare.jpg` (37 views, the unbaked pass: looked at),
   `review/model_lighting_compare.jpg`, `../../props/mm9_connectingtunnels_claude/review/props_sheet.png`.
6. Walkability (`work/walkability.json`, `work/audit.log`): **0 unreachable regions, 0 pits**; 43 steps (7 of 37-39:
   rock lips; 36 of 43-125: the coffin hall's grave edges and pillar plinths in sector 1 (32), rock ledges in sectors
   2, 3, 10, 21, none on a way that has no other), 17 flights (sector 2's ramp, 15, and sector 21, 2: 40-41 per 40-unit
   path step); `work/reach/probe_flights.yml` walks up and down sector 2's ramp (724 and 761 units, 63 and 34 up) and up
   sector 21's (454 units, 80 up): not stopped. 4 mover notes (the grave lids' tops 97 over the grave floor: they lie
   in the floor around it). 3 actor notes ("a ceiling 1 above it": Skeleton Master #10, Annelid #3, Skeleton Warrior
   #17): **false**; the DAT ceiling over each is 190 LT up, and in game each chases a party standing 450-600 units away
   in sight exactly as the plain-floor control (#0) does (`work/reach/probe_actors.yml`: each closes 260 units in the
   first 2 s, then holds about 340 off, the engine's in-sight stop).
7. Scenarios: `scenario_doors_exits.yml` **pass** (the three exits raise their transitions from walks out of their
   starts; the rock fall stops a walk north 40 short of its face, 9 damage (console) leave it standing, a real click breaks both, the party walks 900 through; 2026-11-06),
   `scenario_chests.yml` **pass** (TreasureChest0 by interact), `scenario_scripted.yml` **pass** (the grave's chest stays
   shut while the lids are closed; a real click swings both lids and sets `CoffinOpen`; the chest opens by its event:
   headless picking does not follow the lids' swing, the playbook's gotcha; closing the lids, from out of their reach,
   locks it again).
8. Starts: StartPoint0 on the floor at the Thronheim end facing north into the tunnel (the first view of every tour);
   StartPoint1/2 likewise (views a02, a03); the three arrivals on the floor in the shifted frame.
9. Compiler unit tests: not rerun (no engine or compiler change).
10. Lights: no floor point under more than 4 (`content.json` `light_coverage`); bake current.

## Deviations from MM9 and why

- **The frame offset** (x 17 000): the DAT is wider than int16 (above). Transition rows are shifted by `convert.py`.
- **The rock fall also breaks on a click** (a killing blow on DestructableBrush0): MM9 breaks it by weapons only (10 hit
  points), which work too since it became a scene destructible (2026-11-06; before, a click mover).
- **The player-light stand-in** in 13 rooms (above).
- **No AI rails**: MM9's monsters patrol `AIRail`s; ours stand at their DAT positions and chase on sight.

## Shared changes

- `tools/lighting/bake_indoor.py`: opt-in profile key `ambient_colour` (default white: no change for any other map).
- None in the shared converter (`dungeon/`); the frame offset's transition shift is in this map's `convert.py`
  (`offset_transitions`): the shared `tables.transitions_text` writes rows in the old map's frame and would need the
  same shift for any other map with an offset.

## Open items

- Not checked: a desktop playthrough with real input (the rock fall and the grave by a real click on the desktop,
  where picking follows the lids), save/load, the arrivals from Thronheim and Yorwick (outdoor maps, not rebuilt), the
  candles' flames in game from the side (the props project checked the GLB and Tasar's renders), Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:05:42 (convert.py from the current shared converter, end 15:08:21): 0 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV is byte-identical to before (no face of this map met the rule) and its baked lighting stays installed (not stale); it has 4254 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
