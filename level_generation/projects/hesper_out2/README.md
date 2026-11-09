# Hesper: the Scour (`hes_out2.odm`, map 9110)

The second outdoor map of Hesper, the Kreegans' strip mines, built from its design
([THE_SCOUR.md](../../../design/kreegan_world/zone2/THE_SCOUR.md), BUILD-READY) into the shared
[Hesper stage](../hesper_stage/README.md). The design's data scripts are the one source: the terrain functions of
`design/kreegan_world/zone2/scour_terrain.py`, the roads, conveyor, places, spawn points and decoration groups of
`make_scour_detail.py`, and the five work camps of `work_camps_plan.json`. Modelled on
[Starport Reach](../hesper_out1/README.md), whose BModel kit it shares (`hesper_out1/bmodels.py`, `houses.py`).

## Build

```sh
level_generation/projects/hesper_out2/build.sh          # the map, its minimap, the stage (under its lock)
```

1. `build_out2.py`: heights (the design's world heights, 3 x 3 samples round each vertex so the pit's 430-wide ramps
   read on the 512 grid; the pit never graded), the building pads, the roads graded (the mine road 700 and the Kreegan
   Road 640 at 0.18, the haul roads and the Rim Road 600 at 0.3, the tracks), the camps' yards (camp 4's upper
   shanties and perch a 280 step up), the Pens' yard level at 880 to its walls, the tunnel portal and Thrix's cave set
   into rock raised behind them, then the edge contracts (below); one tile per cell (ash tufts on the ash, the
   molten slag on the MM8 lava tiles with their `lvdr*` shores, its cells burning), the material weights (seven
   layers and the slope layer); the BModels (`scour_kit.py`); the decorations, chests, items, people and monsters;
   the events; the ODM through the editor's writer, verified against the sources. Writes `source/`,
   `runtime/worlds/hesper/` and `out2_build.json` (every arrival, door pose, camp, actor group and the Harvester's and
   the garrison's actor indices: D3, D4, D8 and the Undervault read their arrivals here).
2. `build_minimap_blender.py`, `finish_minimap.py`: Starport Reach's minimap recipe (neutral sun, grey fill).
3. The props: `level_generation/props/hesper_decorations/scripts/build_scour_props.py` (Blender, hard surface; see
   [Decorations](#decorations)). Rebuild them before the stage when they change.
4. After the Scour's arrivals change, rebuild D3, D4, D8 and the Undervault (`build_d03.py`, `build_d04.py`,
   `build_d08.py`, `build_undervault.py`; `rebuild_all.sh` does it).

Lighting bake (about six minutes; the stage installs it only while it matches the built map, so re-bake after every
map build): `bake_profile.json` with the stage's `bake.sh` route (see [Status](#status-2026-10-23)).

## Check

- `make_tour.py build01` writes `review_tour_build01.yml` (BUILD-READY's named shots: the signature view from the
  pit's south-west gate, the west arrival, the scout's camp, the tunnel mouth, Thrix's cave, the wreck, D3's gate
  and its mesa, the five camps, the Pens from the rim and D4's door, the depot, the Slag Gate, the slag river, the
  Kreegan Road's cut and the north edge, under the conveyor, the pit floor, four aerials and a top-down over the pit);
  `make_tour.py edges_out1` / `edges_out4` the crossings seen from Starport Reach and the Crown. Run a tour minimized
  (the command is in `make_tour.py`), then `make_sheet.py build01` writes `review/build01/sheet.jpg`.
- `make_scenarios.py` writes the scenarios from `out2_build.json` (run them from `output/hesper_stage/scenario_run`):

| Scenario | What it checks |
|---|---|
| `scour_edges.yml` | The west edge to Starport Reach and back from its east edge; the north edge to the Crown and back from its south edge (the stage's `edges.yml`) |
| `scour_exits.yml` | D3's Outer Gate, D4's Pit Stairs door and D8's Slag Gate in, each dungeon's exit (its event 50) back to the Scour's arrival; the tunnel after S2 to the Undervault's Water Works (100420) |
| `scour_camps.yml` | Camp 1 freed at its collar node (Hacking Novice: 100115, its Kept friendly, the freed pair shown), camp 2 freed by its Overseer's death (100116); after a save and a load both camps' Kept stay friendly, camp 3's hostile |
| `scour_depot.yml`, `scour_depot_hacked.yml` | A fight by the depot's garrison raises the alarm (100405, wave 1, the second-wave count back to 0 after 20 s); with the pylon hacked first (100400) no alarm |
| `scour_harvester.yml` | The Harvester killed: 100404; its death message closed, the body finishes dying and the Energy Core is looted from its corpse |
| `scour_tablets.yml` | Each tablet plinth gives its tablet (IV-VI) to the hand and records it (map variables 20-22) |
| `scour_collision.yml` | Through camp 3's gate (open), under the conveyor (open), into the derelict's hull (blocked) |

## The map

| Part | Built as |
|---|---|
| The Great Pit | The design's terrain (rim 2 300, benches 1 640 and 980, floor 320, the three ramps), never graded; the Rim Road round it at 1.06 cells |
| The conveyor line | 24 resin-wrapped Ancient piers (`hompier`, `hokspine` collars, `hmgantry` cross heads) every 0.3 cells along `CONVEYOR`, the belt deck (`hmbelt`, `hmbeltsd`, `hmgantry`) at world 2 900, climbing to 760 over the ground where the spoil hills rise toward it (south of the pit, the north leg), at most 300 a span; the central hopper tower on the pit floor and the south loading hopper; the deck enters the Foundry's west wall at its intake |
| The Foundry | `scour_kit.foundry`: a 5 200 x 2 400 shed hall (`homshed`, a `homroof` gable, `hokwall` buttresses), its east annex, the Slag Gate (`hmgate`, D8, event 53) in a resin frame; five stacks (`homstack`, tops 5 000-6 000, smoke emitters on top) |
| The slag river and pond | The design's molten cells (14 tiles) on the MM8 lava tiles: the stage's `molten_slag` liquid, the cells burning (attribute 0x01) |
| D3's fort | A ring of 12 resin wall segments on the mesa (radius about 2 180), two watch spines, the Outer Gate (`hkblast` in an `hkrib` frame, event 50) facing east down the ramp; the forecourt levelled at 2 750 with pylon P1 (event 81, cog 187) |
| D4's Pens | The yard level at 880, the Pit Stairs door bay in its south wall (the door one fitted `hkdoor` face, 320 x 640 like its 1:2 texture, event 51, recessed 40; a `hokspine` spine either side and one fitted `hktrim` band, 640 x 160, over the opening), two fire bowls before it, two cage rows (`hkcage`) |
| The camps | `work_camps_plan.json`: the Kept shanties (`hhkeptw`, `hhkeptrf`, `hhkeptdr`, no events) on their rings, the camp gates (two `hokspine` spines and an `hkrib` lintel), the collar node (events 71-75, cogs 171-175), the perch with its Overseer, two fire bowls at its foot (cogs 176-180), the freed camp's brazier (cogs 181-185, hidden until freed); camp 1's wreck plates, camp 2's slag heap and sledges, camp 3's ore carts and dead Kept, camp 4's terrace, camp 5's duelling ring of eight bone posts |
| The depot | Two works sheds with open fronts (the salvage crates inside), the alarm pylon (event 80, cog 186), six closed drop pods on the pad (cogs 140-145) |
| The west | Thrix's stall (house 9300, event 300) before his cave (an `hhrock` face with a dark mouth, rock raised behind it), Tarro's lean-to (house 9301, event 301), the tunnel portal (`hoterm`, `hctrim`, `hcshutter`, event 52) in the canyon's west wall |
| The wreck | `hes_derelict_hull_a` and `_b` along a line through the wreck's centre, half buried, with invisible collision boxes and four rib columns |

**Events** are the design's (section 17): the load event (1: the camps' group bits and fixtures, the Pens' yard,
the Harvester's behaviour and carried Energy Core, the pylons, the pods; Ansel), the first visit's autonote (2), the
depot's watch (timer 4, every 30 game seconds: a living garrison actor within 3 000 and the enemy detector red for
three seconds raises the alarm, 156; the second wave 20 s later, 157), the signposts (10-13), Aster's relay posts
(20-22, dead before M3 and after Tear it out), the tablet plinths (23-25), the chests (30-39; 35 needs Hacking
Expert), the caches (45, 46), the doors (50-53), the collar nodes (71-75), the pylons (80, 81), the Harvester's
death (hook 150), the camps' Overseers' deaths (151-155) and the first collared Kept's death (160), the houses (300,
301). Freeing a camp (`FreeCamp`): its S6 bit (100115-100119), its Kept friendly by their group bit, the node and the
perch's bowls dark, the brazier lit, the freed pair shown (camp 5: Ansel too), map variable 10 + n (the camp's other
Kept are hidden on the next load), reputation -2 once (100721-100725), S6 done and autonote 10105 with the fifth.

**The Harvester** (`harvester.lua`, `hesper/bosses/harvester` in `behaviors.yml`): grinds for 32 s behind a
700-radius projectile ward and sprays a Fireball on a party within 900 every 6 s, then stops for 8 s to dig (the ward
down, no spray), as the design's built fallback for its armoured front and its dig stops. Its post (leash 2 400) and
40 degrees a second are its tactics.

**People** (the stage's `npcs_scour.yml`, P4's dialogue/SCOUR.md): Thrix (row 10263) outside his cave, Tarro (10264)
outside his lean-to, the ten freed Kept (10260/10261, hidden until their camp is freed), Ansel (9221, the stage's
`skills.yml` teacher, hidden until camp 5 is freed). Thrix's token trade: P4's question is three topics (9721-9723)
shown once he has asked (P1's 100406), until the token is traded (100407).

**Monsters** (section 7): 108 placed actors (the 12 groups, the hidden pod waves, the freed people) and 32 encounter
spawn points (slot 1 the Drudges, 2 the Troopers, 3 the Overseers; `maps.yml`). Every actor stands on free ground
(Starport Reach's `spawns.Ground` test), hostile ones outside the design's quiet rings.

## Edges

| Crossing | Built |
|---|---|
| West (Starport Reach) | The vertices within 1 550 of the edge, y -6 192 to +708, levelled to Starport Reach's built east edge (`edges/hes_out1_built_edges.json` `in_0`); checked within 32 by the build. Arrival (-22 406, -2 592, 1 088) facing east |
| North (the Crown) | The gap's vertices x 1 536-4 096 (the 512 grid's nearest to the contract's 1 880-3 880 floor) level at 1 200 for 1 555 in, the walls rising from x 1 024 and 4 608. Built rows: `source/hes_out2.terrain.yml` (`out2_build.json` `arrivals.north`: (2 880, 22 406, 1 216) facing south) |

## Decorations

Meshy models (the decorations project's organic route, `designs.json`: a Codex HD master from the zone 2 concept,
Smart Topology, Codex-painted views baked to PBR maps; 20 credits, 2026-10-23, the user's review): the collar node
(concept z2_07; its dark state `hes_collar_node_off` is the same model with the lenses dimmed by
`scripts/derive_dark_variant.py`), the Overseer's perch (z2_07; its deck at 905, where the Overseer stands) and the
derelict's two hull halves (z2_08; collision boxes sized from the models). New hard-surface models
(`level_generation/props/hesper_decorations/scripts/build_scour_props.py`, the shared kit, K5/K6/K8 textures;
`review/scour_v2/sheet.jpg` in the decorations project): the outdoor fire bowl and its cold state, the ground vent,
the survey marker, the conveyor parts, the Kreegan salvage crate (chest), the duelling post, the wreck plates and the
spoil heap. All 0 inverted closed parts. Existing stand-ins (other builds' rows): `hes_slag_heap`, `hes_ore_cart`,
`hes_ore_sledge`, `hes_drop_pod`, `hes_drop_pod_open`, `hes_corpse_kept`, `hes_alarm_pylon_off`.

Besides the design's DECOR groups, the build dresses the open ground (the user's review of build01: "too empty"): a
group of two or three pieces beside every road about every 1 500 (sides alternating, 700-1 150 off the line), 28
round the pit rim, and one on a jittered 3 000 grid over the rest, each off the roads, the buildings and camps, the
lava, the conveyor piers and the arrivals. Its kind follows the ground: slag heaps, vents and plates on the slag; spoil
heaps, survey markers, conveyor parts and wreck plates round the rim; ore crates, carts, salvage and sledges near a
camp; wire thickets on the ash; a mix on the haul ground. About 470 pieces (690 entities in all). The ash tufts
(plant rule on `voltyl`) are at density 0.65; spoil, slag and plating stay bare of plants (K13).

## Notes for builders

- **Literal `evt.SetSprite` only.** The lighting bake reads a map's sprite swaps statically
  (`tools/lighting/bake_decorations.py`: `evt.SetSprite(<literal cog>, 0|1, "<literal name>")`) and fails on a computed
  cog such as `170 + n`; the build writes each camp's swaps as literal functions (`CAMP_FIXTURES`, `OpenPods`).
- **A modal message pauses the world.** `evt.SimpleMessage` in a MonsterKilled hook (the Harvester's death, a camp
  freed) opens a box that stops the world: a dying actor stays "dying" (hp 0, not dead, its carried item not dropped)
  until it is closed. A scenario closes it (`press_action: cancel_dialog`) before it waits for the body. The depot's
  alarm, mid-fight, is a status text for the same reason.
- **Event items go to the hand.** A plinth's tablet (`AddValue(InventoryItem(...))`) lands in the held slot first;
  a scenario asserts `held_item`, with an empty hand (the Harvester's core from its corpse occupies it).
- **The 512 grid and things set into rock.** A face standing in raised terrain is buried by the terrain triangle
  between the last level vertex and the first raised one; keep the floor level to the first vertex behind the face
  (the tunnel portal, Thrix's cave) and raise the rock behind that.

## Status (2026-10-23)

Built, staged and baked (`bake_profile.json`, installed by the stage while it matches the map). All eight scenarios
pass; the review sheet is `review/build01/sheet.jpg` (27 shots, baked), the crossings from the neighbours'
side `review/edges_out1/`, `review/edges_out4/`. The builder's report, the stand-ins, the changes from the document
and the open questions: `design/kreegan_world/WORK_PACKAGES/requests/P1.md`, "Builder's report: the Scour".

## R5 Ashkites (2026-10-26)

Two placed Ashkite flocks of five (row 10310) now circle opposite Great Pit spoil rims, groups 150/151.
They are appended at actor indices 108–117; the 108 existing actors are preserved. Build with `build_out2.py`,
then `make_scenarios.py`. Terrain, decorations, minimap and lighting were not changed for these actors.
