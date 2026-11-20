# MM9 rework: Training Hall (`traininghall.blv`)

MM9's Training Hall (off Thjorgard; Lizard-Orcs, Trellborgs and Ghouls, levels 22-60) converted from its DAT world into a
native indoor map (BLV: sectors, portals, linear and rotating movers, ladders, lights, exit volumes) on the shared
dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated
review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop
models ([props project](../../props/mm9_traininghall_claude/README.md)). Status 2026-10-30 (overnight run): geometry, 13
rooms, every mover, 2 lobby double doors and the dragon door, 46 ladder strips, every scripted object, lights, both
exits, 53 decorations, 5 chests, 22 actors, baked lighting matched to MM9's DAT lightmaps. One engine change
(opt-in ladder grab in the air, below); no shared converter change.

The hall: the party arrives in a small room on the roof (StartPoint0, beside the painted door back to Thjorgard,
ExitTrigger1). A wheel chandelier hangs in the lobby below from a beam through a hole in the roof room's floor: the party
drops onto it (or climbs down the beam), the wood creaks and cracks, and the chandelier falls 432 LT into the lobby's
shallow pool with the party on it. From the lobby: two crow's nests up steel ladders (a chest in the west one); north,
up a stair and through the dragon door, the pole room (iron poles and beams over deep water, three beams sliding to and
fro, a chest on the top ledge); east and west, corridors to the archery range (four targets with ring prizes, skylights)
and the crate room (the Blackbox chest inside a boarded crate); down the stairs, the joust hall (two horse lanes with
their levers; the Mean Trellborg launches the first horse; the second breaks the wooden wall at the lanes' end) and,
behind that wall, the debris room and two caves (Ghouls, two chests). Above the joust hall the training room (the
Lizard-Orc students, their commander on his podium) ends at a barred door: breaking the bar is the end of the training
(key 301, +5 Might, +5 Intellect, 20 000 experience) and makes the door an exit to Thjorgard (ExitTrigger0, StartPoint1).

## Build and review

```sh
python3 level_generation/projects/mm9r_traininghall/analyse.py           # DAT survey: work/analysis.json, dat_objects.json
python3 level_generation/projects/mm9r_traininghall/convert.py --plan    # rooms only (10 s)
python3 level_generation/projects/mm9r_traininghall/convert.py           # build, compile, install (30 s)
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_traininghall                          # bake (2.5 min, 64 samples)
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_traininghall   # zones
python3 level_generation/projects/mm9r_traininghall/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_traininghall/scenario_$s.yml --scenario-no-color; done
./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_traininghall/work/reach_monsters.yml --scenario-no-color
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_traininghall
python3 level_generation/projects/mm9r_traininghall/make_tour.py v02 [--original]   # 37 eye-level views
bash level_generation/projects/mm9r_traininghall/work/run_tours.sh v02 [--set video.lightmaps=false]   # SDL_AUDIODRIVER=dummy
bash level_generation/projects/mm9r_traininghall/work/run_tour_original.sh v02     # view_distance=unlimited
cd level_generation/projects/mm9r_common && python3 -m dungeon.sheet ../mm9r_traininghall/review/v02 ../mm9r_traininghall/review/v02_original
python3 level_generation/projects/mm9r_traininghall/tools/views.py review/v02_original review/v02_unbaked review/v02
```

Review: [`review/v02_compare.jpg`](review/v02_compare.jpg) (37 views, MM9 original | native baked),
[`review/lighting_v02_compare.jpg`](review/lighting_v02_compare.jpg) (MM9 original | native unbaked | native baked),
[`review/v01_compare.jpg`](review/v01_compare.jpg) (the first build, unbaked), flames from the side
[`review/flames01_sheet.jpg`](review/flames01_sheet.jpg).

## Files

- `overrides.yml`: every DAT world model's rule, 9 archway cuts, `seed_exclude`, the skylight shafts' seeds, glass,
  sky and water textures, `thin_walls`; `convert.py`: the population, the Fire flames, the perception hints, the water
  surfaces, the ladders, the ring shells, the light colours and zone gains, every script (a `dungeon.Hooks` subclass);
  `analyse.py`, `make_scenarios.py`, `make_tour.py`, `hue_zones.py`, `tools/` (`leak.py`, `probe.py`, `views.py`),
  `scenario_*.yml`, `review_tour_*.yml`, `review/`.
- `props.json`: 45 placements from the props project; `work/`: `build_report.json`, `doors.json`, `lights.json`,
  `content.json`, `walkability.json`, `rooms_<level>.png`, `runtime/`, `reach_monsters.yml`, `hue.txt`,
  `hue_summary.txt`, `brightness_v02.txt`, scenario logs, `run_tours.sh`, `run_tour_original.sh`.

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) x 2.56`, no offset (the old map's frame) |
| Geometry | 4 404 source polygons -> 4 040 merged -> **6 697 native faces**, 9 633 vertices; 217 faces with no air in front dropped (undersides, backs against walls, the sealed pool bed of the pole room) |
| Air | sealed (`leaked_to_border` 0) once the eight relay triggers MM9 parks outside the walls or under the floors (Trigger2/3/6/7/8/9, TriggerHorseGo, crateopentrigger) and Light52 (in the rock) are out of the seeds; 2 seeded components (the map; the four skylight shafts over the range, seeded at DirLight2-5) |
| Rooms | **13 + sector 0**: roof room and lobby (one room through the hole), pole room, east and west corridors, stairs and lower cross corridor, joust hall, training room, archery range, skylight shafts, crate room, debris room, south cave, east cave; faces per sector median 277, largest 1 548 |
| Portals | **17 faces**: 3 UserPortals (doorportal0/1, portal0), 9 archway cuts, 4 skylight glass portals (both rooms, the pane a translucent face) |
| Movers | **54 mechanisms**: the chandelier, 2 horses with wheels, the second horse's guide, 2 levers, 4 reset levers, 4 targets and their 16 ring shells, 6 lobby/dragon door leaves, 3 pole room beams (the chandelier's bar, 7 crate boards, the end door's bar and 5 wall pieces became 14 scene destructibles, 18 with the skylights: 2026-11-06); invisible parts (`_INV`) and glass parts (`_GLASS`) of some |
| Lights | 71 `Light` -> **52 BLV lights** (colour x BrightScale x zone gain, below); 14 over the four-per-point cap and 4 raised 'lava lights' bake only; 16 `DirLight`s as bake spots; at most 4 per floor point |
| Decorations | **53**: 11 wall torches, 5 braziers, 6 hanging fire bowls, 8 Fire flames (gate fire cards at a third), 2 training mounts, 4 straw dummies, 4 spin dummies, 6 lumber heaps, 2 barrels, 5 chests |
| Actors | **22**: Lizard-Orc 8, Lizard-Orc Warrior 2, Trellborg 4, Ghoul 8, at MM9's body size (ABC extents x Scale x 2.56) |
| Ladders | **46 strips**: the chandelier's beam (4 sides), the lobby's two steel ladders (diagonal), the 11 poles (4 sides each, `grab_in_air`) |
| Translucent faces | 647: 596 ring shell faces (opacity 0), skylight glass, ladder rungs and bars, perception hints (0.5), the two water surfaces |
| Exits | `ExitTrigger1` (object 224, the roof room's door) and `ExitTrigger0` (221, the end door, gated by the bar); arrivals StartPoint0 (roof, facing south) and StartPoint1 (the training room before the end door, facing north) |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` only for its 3 UserPortals |
| `drop` (Door, the wheel chandelier, 432 LT down at 750), `DestructableBrush6` (its bar), `Chain Ladder` (the beam) | the chandelier a linear mover with an invisible floor over its wheel (the native party falls between the spokes MM9's party box stands on), the bar a scene destructible (100 HP, `motion: break`, no click: its death opens `drop`), the beam static with four ladder strips |
| `dummy2door`, `d2w1-4`, `d2lever` | the first horse (MM9's 1190 LT at 1250, back at 200) with its wheels and its lever (rotate, a click) |
| `dummy4door`, `dummy4guide`, `d4w1-4`, `d4lever0`, `upperbreak1/2`, `lowerbreak1/2`, `woodexplosion`, `WorldObject3/4` | the second horse (2000 LT) and its guide; the wooden wall's pieces are TriggerDestroyOnly scene destructibles (`motion: break`) the horse's crash destroys; the frame and the wrecked horse beyond it static |
| `target1-4` (RotatingDoor 90 about x), `Rank*` (16 invisible WorldObjects, TH_TargetRing.scr) | rotating targets; the rings are MM9's invisible hit shells over the painted rings: here ordinary faces drawn at opacity 0 (native missiles pass Invisible faces), riding their target's swing, with a click and a missile (TriggerByObject) event each |
| `resetlever1-4` (Locked) | rotate movers; a click says the lever is locked |
| `DestructableBrush0-5`, `DestructableBrush8` (the crate's boards) | scene destructibles (`motion: break`, 2026-11-06; 25 HP, the back board 100): weapons break them; a click on a board (the shared killing blow, event 38000 + index) or a click or missile on its visible perception hint (events 210-216) still does |
| `DestructableBrush12` (TrainingEnter.scr) | the bar on the end door, a scene destructible (1 HP, `motion: break`) with an invisible slab across the door's recess that breaks with it (the gate of ExitTrigger0) |
| `DestructableBrush7/9/10/11` (trainingglass) | static skylight panes, translucent, glass portals to the shafts over them; scene destructibles 44-47 (75 HP, glass: the shared converter's static brushes) that missiles and blows break |
| `Pusher0-2` (Door, Looping) | linear movers looped by a map timer (MM9's MoveDelay, OpenWaitTime, CloseWaitTime) |
| `RotatingDoor0-3`, `dragonroomdoorL/R` | rotating double doors (MM9's swing, open-away, auto-close), doorway portals |
| `BlueWater1` (lobby pool, Ocean4.spr, SurfaceAlpha 0.5) | a non-solid surface at 0.5 over the pool's 10 LT deep bed: the party wades in it |
| `BlueWater0` (pole room, 104 LT deep, SurfaceAlpha 0.9) | a non-solid surface over the built bed, drawn translucent at 0.9 (water123): the party swims and dives in it (the shared water rule, 2026-11-06; scene `water_volumes`) and climbs out on the poles |
| `Ladder0/1`, `WorldObject1/2` | the lobby's steel ladders (rungs on a diagonal face): ladder strips to the crow's nests (432 LT) |
| `Ladder4-14`, `WorldObject8-18` (Iron poles in invisible octagonal prisms) | the poles static, each with 4 ladder strips at the prism's faces, `grab_in_air: true`; a climber steps off on the beam or platform each pole hangs from |
| `InvisibleBrush0/1` (Firethrough.dtx counters), `InvisibleBrush2`, `WO_GhoulPlatform`, `WorldObject*` | static (invisible collision where MM9 has it) |
| `PerceptionBrush0-8` | untouchable translucent faces at 0.5 with a cog each, shown at MM9's PerceptionValue (12: the chandelier's bar, the wooden wall; 17: the crate's boards) until MM9's wiring switches them off; the board hints carry their board's click |
| `Light`, `DirLight`, `ObjectLight` | BLV lights (Light), bake spots (DirLight); ObjectLights light only MM9's models: not built |
| `Prop`, `WallTorch`, `Brazier`, `Torch` (hanging bowls), `Barrel`, `TreasureChest`, `Fire` | 3D decorations (props project); the Fire objects as the gate fire's flame cards (`mm9_gatefire_x33`, unlit: their Lights light them) |
| `ExitTrigger0/1`, `StartPoint0/1` | MM9 positioned transition volumes and starts (ExitTrigger1's box grown 24 LT into the room: below) |
| `AIBarrier0`, `SkyBox0`, `TOD_Sky0`, `AITrk`, `AIRail`, `Marker`, `AmbientSound` (19), `Fog`/`WeatherMan` | not built (AI helpers, sky; the map's `Fog0` StartOn state is the scene's fog) |

## Scripted objects (`worlds/mm9/events/maps/traininghall.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **The chandelier**: `dropsequence`, `cracktrigger1-5`, `droptrigger`, `DestructableBrush6`, Door `drop` (OpenTrigger "drop perception" off) | the party on the chandelier (the polled box reaches down to the wheel and covers it: the native party does not reach MM9's 544 LT box) hears the wood creak, then crack; 1.2 s later droptrigger destroys the bar (DestructableBrush6), whose death (event 221; also 100 HP of weapon damage) drops the chandelier with the party; PerceptionBrush0 goes off |
| **The lobby ghouls**: `TH_LobbyGhouls.scr`, `TriggerLobbyGhouls`, `TriggerGhoulsAttack`, `TriggerShutDoor`, 'dragonroom door' | TriggerLobbyGhouls (on the chain and the chandelier) sends both ghouls to their last marker, the perch over the pole room's entrance (MM9 runs them there along Ghoul*Marker0-2: here they are set there), and opens the dragon door; TriggerGhoulsAttack in its corridor drops them onto the water in front of the party and shuts the door; TriggerShutDoor (in the pole room) shuts it again |
| **The joust**: `d2lever`, `Trigger2/3`, `dummy2door`, `TH_MeanTrellborg.scr`, `TriggerTrellborgOn0/1`, `Off0/1` | a click on the lever sends the horse down its lane, a second brings it back; with the party on the stairs down (On), the Mean Trellborg launches it every ~10 s (4 s of taunting, the ride, the return at 200 LT/s) until the party goes back up (Off) or he dies (monster killed hook) |
| **The second horse**: `d4lever0`, `dummy4door`, `dummy4guide`, `Trigger6/7/8/9`, `upperbreak1/2`, `lowerbreak1/2`, `woodexplosion`, `PerceptionBrush1` | a click on the lever sends the horse through the wooden wall: 1.1 s later the wall's pieces break (`evt.DestroyDestructible`: the debris room and the caves open) and the hint goes off; the lever toggles its guide after that, the horse stays (MM9's lock) |
| **The archery range**: `TH_TargetMgr.scr` ("target 1 4"), `TH_TargetRing.scr` (16 rings "<target> <prize>"), `TriggerTargetsOn/Off` | the targets stand at load; past TriggerTargetsOff they lie flat, back past TriggerTargetsOn they stand (each re-arms the other); a ring struck by a missile (or clicked) rings the bell and pays its prize in gold once per target (key 7009 + target), and its target lies flat for good |
| **The crate**: `DestructableBrush0-5`, `DestructableBrush8`, `crateopentrigger`, `PerceptionBrush2-8` | weapons (or a click) break a board; its death (events 210-216) turns off its hint; the Blackbox inside opens once the back board is gone |
| **The end of the training**: `TrainingEnter.scr` ("TrainingHall") on `TrainingTrigger`, `DestructableBrush12`, `ExitTrigger0` (StartOn 0), `TrainingHallExit.scr` | breaking the bar (a weapon or a click; its death runs event 220) gives key 301, +5 Might, +5 Intellect (GiveAttribute 0 5 1, 1 5 1: the active member, as the Ruined Temple reads GiveAttribute), 20 000 experience and the quest sound, and opens the door's recess (the slab goes with the bar), so ExitTrigger0 takes the party to Thjorgard; with key 301 the map loads with the bar gone (:Init). TrainingHallExit.scr's reward code is dead in MM9 (an `exit` before it; Patch 1.3 moved it to TrainingEnter.scr) |
| **The pole room's beams**: `Pusher0-2` (Looping Doors) | out, wait, back, wait, from the map's load, at MM9's speeds and waits (a 0.25 s timer) |
| `resetlever1-4` | locked (MM9 Locked; nothing unlocks them) |
| **Unmatched** (the clip loops and walks since 2026-11-11: "Training scenes" below): `TH_TrainingOrcs.scr`, `TH_TrainingOrcObserver.scr`, `TH_TrainingOrcCommander.scr`, `TH_OrcsGossip.scr`, `TH_JoustTrellborg.scr`, `TH_LookOutTrellborg.scr` and their triggers (`TriggerOrcTraining`, `TriggerOrcsStop`, `TriggerGossipOn/Off`, `TriggerBoxOrcsOn/Off`), `TriggerHorseGo` | idle animation loops (drills, gossip, taunts, the witness and the lookout walking between markers) of monsters that turn hostile on sight (TrainingHostility.inc); the actors stand at their DAT positions and fight with the native AI. TriggerHorseGo only stops the wheels' spin (wheels do not spin natively) |
| `TH_Bullseye.scr`, `TH_Chandelier.scr` | in MM9's scripts but used by no object of this map |

All MM9 Trigger volumes are boxes polled four times a second (any part of the party: the box grows by its 37-unit
radius); one-shot ones fire once, the paired on/off ones whenever their state allows and the party has left the box.

## The pole room and the engine change

MM9's pole room is a jumping course: 11 iron poles hang over deep water from beams and platforms; the party climbs a
pole, steps onto a beam, jumps to the next pole, and the three sliding beams (Pusher0-2) sweep it off. Native ladders took
hold only of a standing party, so past the first pole nothing could be reached. **Engine change (2026-10-30, built by the
orchestrator, 2391/2391 unit tests and the indoor suite passed)**: a ladder's opt-in `grab_in_air` (scene key; `IndoorLadder::grabInAir`,
`indoorLadderGrabAllowed` in `game/indoor/IndoorMovers.*`, `IndoorPartyRuntime::stepOnLadder`; unit test in
`tests/IndoorMoversTests.cpp`) lets a jumping or falling party take hold. Off by default: MM6-MM8 have no ladders, other
MM9 maps' ladders do not set it. The poles carry it; each pole has four strips (its invisible prism's faces), each ending
a party height under the beam or platform it hangs from, where the climber steps off.

Checked headless: the lowest pole from the water up onto its beam; a party falling past Ladder9's pole takes hold, climbs
and steps off on the 736 LT platform. **Not checked**: a full run of the course with real jumps (the scenario steps have
no jump input); the gaps (beam to next pole about 136 LT) are within a running jump's reach on paper.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_traininghall.yml`: 64 samples,
3 bounces, **direct 0.9, bounce 6, ambient 0.6, sky_scale 0.4**, `dirlights: true` (16 DirLights), `max_lighting: 1`
(MM9 clips at x1), the sky faces (`CLOUVKSJD0`: the roof room's openings and the skylight shafts) emitters. 18 bake-only
lights: the 14 over the cap and the four 'lava light' DirLights, which point up from under the pole room's water (MM9 lights the
room blue through it; our solid wading surface blocked them), raised as point lights just over the surface. One
4096 x 693 page, 2.5 minutes of Cycles. `stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the
map.

Light colours (`convert.py` `scale_lights`): MM9 colour x BrightScale (0.15-0.9 here; the Ruined Temple lesson), the
bake-only lights the same (the shared bake would weigh them by BrightScale / the median kept light, which made the crate
and training rooms' big 0.5 fills 25 % too bright), and **zone gains fitted to MM9's DAT lightmaps** (`LIGHT_GAINS`): the
joust hall x2.0/1.9/1.7 (RGB), the lower cross corridor x1.65/1.6/1.5 (their big 0.4-0.5 fills came out at 0.67-0.71
of the lightmaps and too neutral), the pole room's blue x1.35.

**Brightness and hue: calibrated to MM9's DAT lightmaps (the brief's rule: walls are texture x lightmap x1).**
Per zone (`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`, `work/hue.txt`), green-channel level ours / MM9 and hue
(B/R ours vs MM9):

| Zone | Level | B/R ours / MM9 |
| --- | --- | --- |
| roof room | 1.04 | 0.98 / 0.97 |
| lobby | 0.92 | 0.83 / 0.84 |
| pole room | 1.09 (blue 1.06) | 2.85 / 2.91 |
| east corridor | 1.08 | 0.64 / 0.65 |
| crate room | 1.05 | 0.75 / 0.76 |
| training room | 0.96 | 0.66 / 0.62 |
| archery range | 1.11 | 0.92 / 0.82 (too neutral: the white skylight DirLights) |
| joust hall | 1.00 | 0.69 / 0.69 |
| lower cross corridor | 0.95 | 0.67 / 0.69 |
| caves | 0.91 | 1.11 / 1.09 |

No real MM9 screenshot of this map exists (`devdocs/mm9_rework/overnight/real_mm9/`). Screen means against the "MM9
original" capture (information only, `work/brightness_v02.txt`, 37 views, centre crop): capture 47.5, native unbaked
50.9, **native baked 42.0 (x0.88)**; the capture is the old import in our outdoor renderer, brighter and greyer than MM9.
Views under x0.8 of the capture: r03 roof hole (0.63, looking down into the dark lobby), c04 east stair (0.78),
p05 top ledge (0.79). MM9's dark rooms stay dark: the caves at 20-24, the dragon door's corridor 18.

## Checks

- `scenario_doors_exits.yml` **passes** (43 steps): ExitTrigger1 from the roof room raises `mm9_exit_trigger:224`; the
  party walks off the hole's edge, lands on the chandelier, which creaks and falls (DropDone, the chandelier and its bar
  open); LobbyDoorE stops the party shut, opens on a **click**, the party walks into the east corridor; Ladder0 climbs to
  its crow's nest; the lowest pole from the water onto its beam; a falling party takes hold of Ladder9's pole and steps
  off on the platform (`grab_in_air`); the end door: the party stops short of ExitTrigger0 (the bar's slab), a **click**
  breaks the bar (BarBroken, QBit 90301), the party walks into the door and `mm9_exit_trigger:221` is raised.
- `scenario_swim_check.yml` **passes** (2026-11-06, written from the installed map by
  `../mm9r_common/dungeon/swim_check.py`): on the pole room's bed the party's eye is under water (state bed); Fly Up brings it to
  the surface, eye out, breath full. Rebuilt 2026-11-06 19:51 with the shared water rule: water_volumes 2, room
  mismatches 0, bed holes 0; chests, doors_exits, scripted pass.
- `scenario_chests.yml` **passes** (28 steps): the crate's back board breaks on a **click**, the Blackbox opens (its event:
  headless picking does not follow a moved board, playbook); the crow's nest chest, the pole room's top ledge chest and the
  two cave chests open by interact from in front of their models.
- `scenario_scripted.yml` **passes** (107 steps): the pole room's beams loop (Pusher0 opening, open, closing at MM9's
  times); the chain up from the chandelier to the roof (the chandelier falls behind, the lobby ghouls go up); the hints
  at Perception 1 (none), 12 (the bar and the wall) and 17 (the boards); TriggerGhoulsAttack drops the ghouls and shuts
  the dragon door; d2lever by **click** sends and brings back the horse; TriggerTrellborgOn0 starts the Mean Trellborg,
  who launches the horse 4 s later; TriggerTrellborgOff0 stops him; d4lever0 by **click**: the horse breaks the wooden
  wall (all five pieces gone, the hint off); the targets lie down past TriggerTargetsOff and stand past TriggerTargetsOn;
  the bullseye of target 1 pays 8000 once and lays it flat for good (its event: below); a crate board breaks by a **click
  on its visible hint**; a locked reset lever stays shut.
- Monster reach (`work/reach_monsters.yml`, passes): see below.
- Walkability (`work/walkability.json`): 19 steps, 5 flights, 3 unreachable, 0 pits, 46 mover notes, 0 actor notes.
  Steps: the training room's commander podium (3 x 41: MM9's 16 LT risers), the crate room's crates (edges of the
  boxes, 47-94, 8 long), the lobby's north steps (41). Flights: the lobby's stair to the dragon door and the east stair's
  foot (41 against the audit's 40-unit monster step; the party's step is 50). Unreachable: (1) 45.5 M units² holding
  every actor but one, cut off from **the party start**: the start is the roof room, reached from the lobby only by the
  chain (a ladder) and left by the fall; monsters do not climb (MM9's do not either): **false** as a cut-off, true as a
  description; (2) the commander's podium (0.05 M, actor 11): **false**, tested below; (3) a crate's top in the crate room
  (0.01 M, no monster).
- Thin walls: `thin_walls: true` keeps the 4 LT poles', the 2 LT fire stands' and rails' far faces (dropped faces 437 ->
  264 -> 217 with the shafts seeded); the remaining dropped faces are undersides, backs against walls and the sealed pool
  bed (`work/dropped_faces.json`).
- Floor check: 604 LT² of floor under another room's air: the cave_east cut's strip (542, a cut through an open cave) and
  the two stair tops' sills (31 each).
- Mixed faces: 47 with a minority over 20 % (door jambs in doorway planes, the lobby's ring over the roof room's hole).
  Every review view inspected: no holes.
- Flames in game (`review/flames01/`, sheet `review/flames01_sheet.jpg`): see Flames.
- Starts: StartPoint0 on the roof room's floor facing south over the hole (view r01); StartPoint1 before the end door
  facing north into the training room. Arrivals from Thjorgard (ExitTrigger3 -> StartPoint0, ExitTrigger6 ->
  StartPoint1) land on these floors (`build_report.json` transitions).
- Compiler unit tests: not rerun by me (no compiler change); the orchestrator's indoor suite passed after the ladder change.

## Can the monsters reach the party

Bodies carry MM9's sizes (ABC AnimBinding extents x MONSTERS.txt Scale x object Scale x 2.56): Ghoul 36 / 189,
Lizard-Orc 38 / 164 (42 / 180 at Scale 1.1), Lizard-Orc Warrior 38 / 164, Trellborg 51 / 220 (56 / 242 at 1.1). The
audit's one real candidate, the commander's podium, tested in game (`work/reach_monsters.yml`, passes): control
OrcStudent0 on the plain floor closes on a party 420 in front of it (to about 340); out of its sight, TrainingCommander
walks off the podium on its own within 10 s (z 124 -> 0): the region is **not** cut off; in its sight it targets the
party and stays within 550 (the engine's AI circles at 400-500, as Drangheim Prison's probes found). Ghoul4 stands on a
seam of the cave floor's triangles: it is placed 8 LT east, on the floor.

## Deviations from MM9 and why

- **The chandelier**: an invisible floor rides its wheel (the native party falls between the spokes); its trigger boxes
  cover the whole wheel. The fall (432 LT) hurts a little (the native fall damage starts at 512 units); MM9 lands it in
  the pool.
- **Water** (swimming since 2026-11-06, the shared water rule `dungeon/water.py`, opt-out `map: {swim: false}`): both
  volumes are scene `water_volumes`; the pole room's surface is non-solid and its bed (sealed and dropped before) is
  built, so the party sinks to the bed (266 under the surface at its deepest), swims up and takes a pole from the
  water; the lobby pool stays a wading pool (10 LT). The lobby ghouls dropped onto the water now sink to the bed.
  Before: the pole room's water was a solid surface (no swimming; reversible: `edit_polygons`), drawn since 2026-10-31
  by the liquid shader (water123, `water123_mm9`; the lobby pool's Ocean4 was liquid already and is no longer covered by
  its 0.5 translucent entry; both opaque, `depth: shallow`; [shared helper](../mm9r_common/liquids.py), sheet
  `review/liquid/before_after_p1.jpg`); the 'lava light'
  DirLights under it are raised over it for the bake.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the lobby pool (`BlueWater1`: 0.5 x Ocean4.spr (no alpha) = 0.5, `lqoc4o50`)
  and the pole room (`BlueWater0`: 0.9 x Ocean.spr = 0.9, `lqw123o90`, coloured as MM9's Ocean.spr rather than
  water123, which MM9 never draws there: the volume is invisible) are see-through. Sheet
  `review/liquid/see_through.jpg`.
- **The rings** are drawn fully transparent hit faces instead of MM9's invisible ones (native missiles pass Invisible
  faces); a click counts as a hit (MM9: any damage).
- **The lobby ghouls** are set on their perch and set down in front of the party instead of running and dropping.
- **ExitTrigger1** reaches 24 LT further into the roof room (`convert.py` `EXIT_GROW_LT`): the party's centre could not
  reach MM9's box against the painted door.
- **ExitTrigger0** is gated by an invisible slab that leaves with the bar (no switchable exit volumes natively).
- **The crate boards and the end bar also break on a click** (MM9: weapons only, which work too since 2026-11-06).
- **Idle animations** (training drills, gossip, jousting walks) are not carried; the wheels do not spin.
- **Light colours**: x BrightScale, and zone gains fitted to MM9's lightmaps (Baked lighting).
- **InvisibleBrush2**, `AIBarrier0` and the sky boxes: see the object table.

## Flames

`review/flames01/` (sheet `review/flames01_sheet.jpg`, the map's own views): a wall torch from the front (the flame cards
on its head, Anskram's torch, checked from the side in Anskram Keep); a brazier on its stand from the side (the flame in
its bowl); the lobby's wall fire bowls from the crow's nest above (MM9's FireScale 1 fires: small flames in the bowls); a
hanging bowl from below (its flame cards stand on the rim, inside: not seen from under it). The side view of a wall
torch (`f01`) ended behind the training horse: not usable.

## Open items

- MM9 art for the Lizard-Orcs, Trellborgs and Ghouls: in the review root no actor draws (borrowed MM6-MM8 sprite atlases
  fail: "requires cooked schema 2"); the actors are present (headless reports, scenarios).
- `AmbientSound` (19), idle animations.
- MM6-MM8 density (PLAN.md: later). No x4 textures.

## Not checked

- Actors drawn (above); a desktop playthrough with real input: the pole course with real jumps, the chandelier ride, the
  ghouls' drop, a real arrow or spell on a ring (the scenario cannot aim a missile at a point: the ring's event was run),
  a missile on a board or the bar; save/load after the training (the load handler removes the bar with key 301);
  arrivals seen in Thjorgard; Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:02:50 (convert.py from the current shared converter, end 15:03:41): 1 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 6696 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.

**Pole room beams' timing (fixed 2026-10-31, engine).** `scenario_scripted.yml` always passed, but its step 8 logged
`ASSERT fail ... expected=closing actual=open` with a "transient state" warning (the runner tolerates a wrong
opening/closing state), already in the build night's log; the rebuild script counted that line as a failed assert.
The warning was real: Pusher0 waited about 4 s out instead of MM9's OpenWaitTime 3 s. The beams' handler (timer 402)
restarts itself every quarter second and counts the ticks as its clock, and the engine applied that `evt.StartTimer`
a frame late and counted it from that frame, so each tick took about 0.3 s headless. Fixed in the shared timer code
(`updateScriptedEventTimers`: a handler's restart of its own timer counts from the alarm that ran it; tests in
`tests/ScriptedEventTimerTests.cpp`). Probed every 0.25 s: out 2.0-5.25 s, waits 3 s, back 8.25-11.5 s, out again at
13.5 s (MM9's 11.5 s cycle). No map change. `work/reach_monsters.yml` passes too.

## Training scenes (2026-11-11)

The scripts of line 118's "Unmatched" row now run as scene routines (`convert.py` `SCENES`, `training_routines`): the
four students' drill (Taunt, then HAttack1/2 R L R R L R L L), the commanders' Stand, Fidget2, Stand, Taunt, the
observers pacing MarkerA/B and facing the commander, the gossips' six ScriptParams clips, the jousters at their
JoustMarkers with their four clips, the lookout pacing and watching, and the Mean Trellborg's Stand, Fidget3, Fidget1,
Taunt before each launch (routines `launch`/`reset`; the joust timer pulls the lever after them). Each scene starts
and stops on MM9's trigger volumes (`TriggerOrcTraining`/`TriggerOrcsStop`, `TriggerGossipOn/Off`,
`TriggerBoxOrcsOn/Off`, the Trellborg triggers; map vars `OrcTraining`, `Gossip`, `BoxOrcs`, `Jousting`, applied again
on load). They are still hostile on sight (TrainingHostility.inc): an orc that sees the party drops its routine and
fights, and the gossips see the party at TriggerOrcTraining. Checked headless (the scripted clips cycle) and in desktop
captures with the party invisible (`output/held_items_check/traininghall/`): the drill, the gossips facing each other,
the jousters and the horse, the Mean Trellborg, the box room's observer. Scenarios: chests, scripted, spin, swim_check
pass; `scenario_doors_exits.yml` fails at step 8 (the chandelier drop) with HEAD's scene and Lua too, so not from this
change.
