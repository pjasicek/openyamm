# Hesper: Starport Reach (`hes_out1.odm`)

The first outdoor map of Hesper, built from its design
([STARPORT_REACH.md](../../../design/kreegan_world/zone1/STARPORT_REACH.md)) into the shared
[Hesper stage](../hesper_stage/README.md). The design is the one source: the terrain functions in
`design/kreegan_world/zone1/starport_terrain.py` (which also draw the detailed map) and the roads, places and
decoration groups of `make_starport_detail.py`.

## Build

```sh
level_generation/projects/hesper_out1/build.sh
```

1. `build_out1.py`: heights (the design's relative heights as 800 + 1500 h, roads graded, pads levelled), one tile
   per cell (the tile names key the plants), the material weights (7 weighted layers and the slope layer, written
   from the design's materials, no MM tiles), the plant rules, the Ancient buildings as BModels (`bmodels.py` kit, OBJ), the model buildings with their
   invisible collision boxes (`building`, the `colliders` BModel), the decorations,
   9 chests, the three log cores (ground items), the party start at the Crew Ramp door, the events, then the ODM
   through the editor's writer (`--headless-build-map`, the stage as asset root), verified against the sources. Writes `source/` and
   `runtime/worlds/hesper/`.
2. `build_minimap_blender.py` and `finish_minimap.py`: the minimap with the approved recipe's light direction,
   strength and grade; the ground in the design's colours. Hesper's deviation: a neutral sun and grey fill (the
   recipe's warm sun and blue sky turn the violet ash brown).
3. D0 again (its surface door leads to this map's arrival, read from `out1_build.json`), then the stage.

## Check

- `make_tour.py <name>` writes a tour of every place and an aerial view; run it with `--set
  debug.screenshot_tour_path=...` (see the stage README for the launch). Latest: `review/build01_sheet.jpg`.
- `crew_ramp_round_trip.yml`: D0's surface door to the arrival here and the Crew Ramp door back (passes).
- `building_collision.yml` (written by `make_collision_scenario.py` from the built map): walks out through the
  Hesperian palisade and into an Ashrunner hull home; both stop at the invisible boxes (passes). Run both from
  `output/hesper_stage/scenario_run` (its `settings.ini` points at the stage).
- `hostile_spawns.yml` (written by `make_spawns_scenario.py`): the hostile monsters on load and the Ashrunners after
  S1 (passes; see [Hostile monsters](#hostile-monsters-2026-10-22)).
- `camp_and_homes.yml`: the camp's edge shout (S1 given), the stolen crawler's console (S1 done), Garrow's reward and
  M12, Kesh's stall and Venn's shop with their keepers, the camp folk and Dace's lesson, a home's resident and a street
  person's news (passes; see [The camp, the shops and the homes](#the-camp-the-shops-and-the-homes-2026-10-23)).
- `landfall_keepers.yml` (2026-10-24): Landfall's houses 1-4 (events 51-54) with their keepers and topics: Brask in
  Salvage & Arms (9201), Ysel in the Emitters (9202), Mother Ama in Provisions (vendor 9450, her Food before and
  after S10), Lorn in the Last Lamp (an MM tavern, house 9451: its packs filled for 22 gold; his Rumors give S5,
  100225). The keepers, the inn and the shop are `hesper_stage/npcs_landfall.yml`'s; events 53 and 54 enter them
  (passes).
- `arrival.yml`: the new game by the wreck, the Pilot's M1, the town left alone for a minute, the East Gate guard,
  the Warden closing M1 and giving M2, the black box given, the Pilot's core handed over (M4 given), and after M2 the
  guard's, Sergeant Ost's and the North Gate guard's topics (passes; see [The arrival](#the-arrival-2026-10-22)).

## Status (2026-10-20)

Built and playable: terrain, ground materials, plants, sky, all buildings of the design as first-pass BModels, the
3D decorations, chests, signposts, tablets, the statue and relay post, the D0 round trip, the minimap.
The hostile monsters are placed (2026-10-22: [Hostile monsters](#hostile-monsters-2026-10-22)). The arrival is built
(2026-10-22: [The arrival](#the-arrival-2026-10-22): the wreck, the start, the Pilot, the gate guard, the Warden).
Not yet: the other townsfolk's talk, the D1, D2 and D10 entrances lead nowhere (their maps are not built), the Lift Head.
Lighting bake (2026-10-22, `review/engine_bake/`): `../hesper_stage/bake.sh` bakes [`bake_profile.json`](bake_profile.json)
(the MM recipe's 315°/45° sun, 64 samples) from the stage into `output/hesper_stage/bakes`; `stage.py` installs it
only while it matches the built map, so **re-bake after every map build** (about six minutes).
Creep veins (2026-10-22, `review/engine_creep/`): the stage's `creep_resin` has a library `emissive` entry; its
orange veins glow by day and night.
Rust brine (2026-10-22, `review/engine_brine/`): the canyon stream and the pools at F5, D6 and C6 (moved to the
crater's east foot) are the MM8 water tiles (the fourth tile set is now 126; glass moved to `rkse`), drawn as the
stage's `rust_brine` and waded through. `brine_tiles()` picks the shore tiles from where the brine lies (MM8's own
pairing), the brine and shore corners sink to the brine's level, pools lie wholly level, and the wild dressing is
dropped from brine and shore cells after its scatter (so the scatter's draws are unchanged).
Ash fall (2026-10-22): the engine's new ash weather, a 65 % daily chance from the stage's `weather.yml`
(`review/engine_ash/`, tour `review_tour_engine_ash.yml`; `weather ash heavy` in the console forces it).
Debris ring and orbital lights (2026-10-22, `review/engine_sky/`): the `hesper_ash` preset's `orbit_ring`
(`design/kreegan_world/zone1/sky_preset.yml`) arches along the moon's path with five lights crossing in it.
Second pass on the buildings (2026-10-20, `review/pass2_sheet.jpg`): the Terminal's front is a gold-trimmed portal
with the arched glass doors (`hodoorgl`), light strips and steps, between curved curtain walls of bright glass
(`hoglassl`) on mullions; the Pumping Station is set into a canyon-rock cliff raised round it, its round vault hatch
(`hohatch`) in a brass rim under brass pipes and an outflow; the scrapyard's fence is 16 Meshy resin ribs
(`hes_resin_rib`), with gaps at the west gate and the drag path.

Third pass (2026-10-21, after the user's review of the build; `review/pass3/`, `pass3b/`, `pass3c/`):

- **Z-fighting.** The game draws BModel faces without back-face culling, so the two-sided shells (`both`) were two
  faces in one plane; the back face now sits 4 units behind the front. The container's end bands, the brazier's
  coals and the baggage cart's posts were flush with other faces and stand proud now.
- **Hangars.** Whole roofs in six bays, two or three bays torn out, a rib over every bay joint.
- **Texture density.** `TEXTURE_SCALE` gives the textures whose detail read too small at one texel per unit a
  larger repeat (the corrugation 2.5 times, the plates 3 times); posts, rims, jambs and pipes use plain gold
  (`hogold`, design/kreegan_world/art/textures_out1/make_derived.py) instead of the trim's striped band.
- **Model buildings.** The Ashrunner camp (three crawler-hull homes, two hull-section homes, the trader's stall, the
  watchtower), the Hesperian encampment round the Lift Head (a palisade ring, a gate where the road from the apron and
  the track to the crater cross it, the escape-pod home, three shelters, the water still, braziers and goods), the
  scrapyard crane and the forward outpost with its alarm pylon are Meshy models
  (`level_generation/props/hesper_decorations`), replacing the box homes, the lean-to, the slab crane and the
  prism outpost. The minimap draws them (`work/minimap_models.json`).
- **Roads.** The service road runs on past the map's edge to the north and the east (`run_on`).
- **The colonial locker** is larger, with a lid, gold posts, a keypad and a status light.
- The crater floor under the roof hatch is levelled so the grille lies whole.

The Hesperian village (2026-10-21, `review/village2/sheet.jpg`): the encampment became a village round the Lift Head,
now a Meshy model (`hes_lift_head`, its glass cage facing the road in from the apron). A palisade 2 000 from the
lift with a gate on that road and one on the track to the crater, a watchtower inside each gate, ten homes 1 400 out
(crawler hulls, hull sections, the escape pod, three shelters, one of them Venn's, and a market stall), spaced along
the ring by their own widths and clear of the two streets, salvage behind them, and in the plaza the water still,
benches and four braziers. The lift no longer waits for power (Lowhold has its own): its guards keep strangers off
it until D1 (the story change is in design/kreegan_world, D1's boss room is now Drone Control). The guards themselves
wait for Hesper NPCs. All model buildings had stood with their backs to where they should face: `FRONT_YAW` is 270
for a model whose guide front is glTF +z (`review/facing/`).

House kit (2026-10-21, `review/houses/sheet.jpg`, `review/houses_obj/`): the village's homes and the Lift Head are
simple BModels again, in the manner of MM6-8 (`houses.py`: salvage house with a gable or lean-to roof, crawler-hull
house, Ancient hab module, market stall, the Lift Head tower), each 40-120 faces with a texture per part from the
round-3 house set (design/kreegan_world/art/textures_out1, `hh*`): the door one fitted face, recessed, in a white
ceramic frame so it reads against the wall. `render_bmodels.py` renders single house OBJs for review. The Ashrunner
camp still has the Meshy homes until the kit is approved.

The editor measured every imported face's UVs against 256 x 256 whenever a texture was not a legacy
`Data/bitmaps` image, so every Hesper texture of another size tiled at the wrong scale (a 128 x 32 trim 2 x 8 too
dense: the "planks" on the roof hatch). It now asks the engine for the texture's logical size the way the game
resolves it (`Engine::findSurfaceTextureLogicalSize`), and `TEXTURE_SCALE` was retuned for the correct scale.

The Hesperian village, second pass (2026-10-21, `review/village3/sheet.jpg`): the user asked for the area round the lift
to be nicer than the Ashrunners' salvage. The scrap palisade is now a ring wall of colony prefab panels on lit posts
(`houses.prefab_wall`, the round-4 `hh*` prefab set) 2 400 from the lift, with gate towers and a lintel sign on the
apron road (run back 900 so it crosses the wall) and on the crater track. Inside, seven homes in the prefab skin
(`SKINS`) and Ancient hab modules, the market a prefab shop. The village's drums, crates and braziers are the clean colony props (`hes_drum_clean`, `hes_crate_clean`,
`hes_brazier_clean`).

Landfall (2026-10-21, `review/landfall02/sheet.jpg`): the user moved the Hesperians' town to the map's south-west
corner and made it Harmondale-sized, then asked for it bigger, against cliffs, in more kinds of house. The village at E5 is gone. `build_out1.py` builds Landfall from
`design/kreegan_world/zone1/landfall_plan.json` (its one source, `landfall_plan.py`):

- **Version 2** (`review/landfall03/sheet.jpg`, the first build; `review/landfall09/sheet.jpg`, with the streets, the second review's fixes and the dressing):
  bigger (11 000 × 8 200), cliffs west and south, the wall north and east only, six house kinds in two finishes,
  cliff homes, paved and gravel streets.
- **The wall:** `houses.town_wall` along the plan's open line (`inside` gives the town side), rampart panels
  (`hhwallpf`: the house panel's vents read as rows of objects along a 9 000-long wall) 640 high and 200 thick, two
  gates with lintels and signs, square towers at the gates, the corner and the two ends. Its ends run into the cliffs.
- **The cliffs:** after the town's pad is levelled, the terrain west and south of the town floor rises 1 800 over
  1 700, steepest at the foot (`cliff_rise`), and runs on 900 past the wall's ends. Only points the cliff raises
  change (an earlier `maximum` with the town level flattened the canyon).
- **The houses:** 27 (with the Cybernetics teachers' 16 and 17 since CR-INT-1, 2026-10-23: cut into the south cliff on
  South Lane, events 66 and 67, houses 9219 and 9220 of `hesper_stage/skills.yml`), by the plan's `style` and `finish`
  (`prefab` or `prefab_dark`): `shop_house` for the gable and lean-to shops with their `hfsign*` signs,
  `salvage_house` for gable and lean-to homes, `hab_house`, `tall_house` (two storeys, a balcony, a flat roof),
  `cliff_house` and `hall_house` (the crawler shed). Events are 50 + the plan's number; their texts name the house and
  the teacher until the house tables and teacher topics are in the engine.
- **The cliff homes:** `cliff_house`, a cut rock face 760 high with its sides flaring back, 1 200 deep so the cliff
  rises through its top and buries its back; the front `hhcliffdt`. `hhrockt` and `hhcliffdt` are hhrock and
  hhcliffdr toned to the terrain's cliffs as the game draws them (`textures_out1/make_derived.py`).
- **The streets:** `street_masks` paints Main Street and North Street with the plating layer and the lanes with the
  scree layer (the ground's eight material layers are all in use). Painted door paths missed the doors and blotted
  the paving where they met it; the doors have steps instead (`houses.door_steps`: two treads to a plinth door, one
  to a hab module's).
- **The second review** (2026-10-21): plain panels on every house and tower (`hhwallpf`, `hhwalldk`: the house panel's
  vents repeated on every tile), balcony and awning posts down to the ground, the wall's end caps left out inside the
  gate towers (they z-fought with the towers' faces), the ground in front of each cliff home levelled to the town
  floor (the cliff's first triangles climbed over the threshold), and the inn the first house in from the East Gate.
- **The third review** (2026-10-22): the crater (`starport_terrain.CRATER`, now C6 0.85, 0.75, radius 0.55) moved
  off the north-east corner (its rim stood over the corner tower; `landfall_plan.py` checks the rim); a paved road
  from the East Gate to the Crew Ramp door and both North Gate roads arriving square (`make_starport_detail`
  `gate_out`); `roads_under_buildings` fails the build if a road or track passes over a building's pad except at
  its ends (it ran under the Terminal, the gantries' end and the hangar ruins); the cliff homes 250 out from the
  foot with the door on a 40 sill and two treads (the smoothed ground still rose over the threshold); nothing
  placed in the 700 x 900 in front of a door; the two-storey shops' signs on the balcony railing and hanging under
  it (the inn had none); open stat barrels with an inside, MM-style, empty when drunk.
- **Corner signs** (the user, 2026-10-22: MM6-8's houses carry their sign "sticking out"): `houses.blade_sign`, a
  framed square board fixed at the front corner and standing straight out from the front, the trade's icon on both
  faces (`hhsq<name>`: the icon half of `hfsign<name>`, re-framed by `textures_out1/make_derived.py`), the board's
  sides being the icon faces themselves (an icon laid over them z-fought). Only the services carry signs (the user:
  teachers have none); the gable and lean-to services under the eaves, the two-storey ones on the upper storey's
  corner above the balcony; the board over the door (and the railing board) stays. The teachers live in plain
  houses, as in MM6-8. The Ashrunner trader keeps its market board only.
- **Decoration events:** `decoration(event=, cog=)` writes the click event to `event_id_secondary`, which the engine
  reads outdoors as indoors, and the `evt.SetSprite` key to `event_id_primary`. Before, the chests, the Landfall
  Stone, the signposts and the log tablets had their events in the primary slot and could not be clicked; and
  `openedChestIds` listed every event from 40 up (the houses too) instead of the nine chests.
- **The fountain and the stat barrels:** `hes_fountain` (event 80, +25 hit points) and a red and a green
  `hes_stat_barrel_*` (81, 82: +2 Might, +2 Endurance once, map vars 1 and 2, then `hes_stat_barrel_empty`, restored
  on load by event 83). Headless scenarios cannot click outdoor model decorations (the keyboard picker skips a
  decoration without a sprite frame unless its model is loaded), so these are checked in the game.
- **Dressing** (`STARPORT_REACH.md#dressing`, from the MM towns' decoration counts): fungus trees, clump beds and
  rings, planters, condensers and carts in the town; glass trees, wire thickets and ash-stone pillars across the zone
  (`scatter`, off the roads, the buildings and steep ground).
- **The square:** the Lift Head (event 14, to the Undervault after M2) facing Main Street, the Landfall Stone
  (event 50; 60 was house 10's), stalls, two braziers; a light post on each street. These are the outdoor variants
  (`hes_brazier_out`, `hes_light_post_out`: radius 320, softer colour). Outdoor decoration lights burn at full
  strength by day, and the dungeons' radii (600–1 000) blew the houses out to plain white.
- **The yards:** the fungus beds (`hofungus`) and the crawler yard (two prefab-skinned crawlers, a gantry, fuel tanks).
- **The turrets:** 4 Gate Bastions on the gate towers, 7 Ward Turrets on the corner and end towers and the
  wall-walk: each a mount decoration (`hes_*_mount`) with a Stationary turret actor on it (below).
- **The roads:** the apron road and the Ashrunner track end at the North Gate, and a track runs from the East Gate
  to the Crew Ramp door, on the crater's south-west rim facing the town.
- **Tests:** `building_collision.yml` walks into the north wall (blocked) and through the North Gate (open).

## Landfall's people (2026-10-22)

`build_out1.py` places 35 actors of the Hesper monster rows the stage installs
([`hesper_stage/monsters.yml`](../hesper_stage/monsters.yml)) in the scene's initial actors, all friendly (their ids
lie past the relation table), in groups 20 (turrets), 21 (guards), 22 (villagers) for later scripting. Every ground
actor's spot is checked: off the houses, the Lift Head's cage and arrival, the fungus beds, the decorations'
collision and the other actors, and off each door's way in (700 out and 900 wide for a posted actor, the first 350
for a wanderer); a taken spot moves to the nearest free one (the build prints `population`).

**How MM7 and MM8 populate their towns** (`town_density.py`, from the shipped scenes and ODMs; the box is the
houses' bounding box, BModels with a clickable face; plots in `review/density/`, green peasants, red guards):

| Town | Box (units) | Peasants | Guards (kind) | Peasants / 10⁶ | Guards / 10⁶ |
|---|---|---:|---:|---:|---:|
| MM7 Emerald Island | 14 712 × 9 504 | 25 | 2 (Guard) | 0.18 | 0.014 |
| MM7 Harmondale | 12 008 × 12 136 | 25 | 4 (Guard; 3 more at the west approach) | 0.17 | 0.027 |
| MM7 Tularean Forest (Pierpont) | 12 408 × 12 928 | 25 | 4 (Elven Defender) | 0.16 | 0.025 |
| MM7 Deyja | 6 488 × 6 008 | 7 | 0 | 0.18 | 0 |
| MM7 Tatalia | 8 552 × 5 954 | 9 | 4 (Bowman; 2 more on the south bridge) | 0.18 | 0.079 |
| MM7 Avlee | 9 588 × 10 248 | 23 | 6 (Elven Defender) | 0.23 | 0.061 |
| MM8 Dagger Wound | 19 288 × 15 088 | 39 | 8 (Lizardman Sergeant) | 0.13 | 0.027 |
| MM8 Ravenshore | 15 064 × 18 970 | 34 | 18 (Dark Elven Defender; 10 in pairs) | 0.12 | 0.063 |
| MM8 Alvar | 13 648 × 9 628 | 9 | 0 | 0.07 | 0 |
| MM8 Ironsand (Rust) | 16 496 × 11 728 | 27 | 5 (Troll Warrior) | 0.14 | 0.026 |
| MM8 Shadowspire | 19 416 × 8 688 | 16 | 7 (Necromancer) | 0.09 | 0.041 |
| **Landfall** | 11 796 × 9 108 | **16** | **8** | **0.15** | **0.074** |

- Peasants: 0.07-0.23 per million square units, about 0.16 typical, spread evenly along the streets and between the
  houses, never in groups. Guards: none to one per four peasants in the open towns; the guarded ones (Tatalia,
  Avlee, Ravenshore, Shadowspire) have 0.04-0.08 per million, about one guard to two peasants. They stand singly on
  the streets and at the town's edge or approach (a bridge, the road in); Ravenshore posts them in pairs at doors and
  bridges. No MM town keeps guards on a wall.
- Town people are all placed actors (the map's initial actors, kept in the map's state). The spawn points are the
  map's random encounters: each spawns, per visit and refill, a group from one of the map's three encounter slots
  (1-5, by `map_stats`), and they lie outside the towns (none in a town box but two at Rust's edge and the Dagger
  Wound village's beach).

**Landfall** (88 million: houses 10 800 × 8 150): 16 villagers at the typical density and 8 guards, the guarded towns'
ratio (one to two):

| Who | Monster | Count | Where | Moves |
|---|---|---:|---|---|
| Gate Bastion | 10066 | 4 | the four gate towers, on their mounts, facing out | turret (75°/s), faces out when idle |
| Ward Turret | 10065 | 7 | the corner and end towers, four on the wall-walk | turret (120°/s), faces out when idle |
| Landfall Guard | 10067 | 4 | two outside each gate's opening (the East Gate and the North Gate, one opening each), either side of the road, facing the way in; the East Gate's south guard is the arrival's contact | post (leash 1 536) |
| Guard Sergeant | 10068 | 2 | either side of the Lift Head's cage, on the square | post (leash 1 536) |
| Warden's Guard | 10069 | 1 | beside the Warden's Post's door | post (leash 1 536) |
| Landfall Guard | 10067 | 1 | patrol on Main Street | wanders (Med) |
| Landfall Villager | 10073-10078 | 16 | three on the square, three on Main Street, two each on North Street, Stone Lane, Cliff Lane and South Lane, one on Hab Lane, one by the fountain; male and female A/B/C in turn | wander (Med) |

The wall-walk has the turrets only (no MM town keeps guards on its walls; the first placement's four wall guards and
the North Street and South Lane patrols are gone).

Models: the turrets are `hes_turrets_claude`'s actors; the villagers are the reduced `hes_villager_m_reduce_claude`
and `hes_villager_f_reduce_claude` exports; the guard is the reduced `hes_guard_reduce_claude` model **before its
corpse floor fix** (`work/floor_fix_base/hes_guard.glb`): the fixed `export/hes_guard.glb` has two Death keys at
2.1 s on `B_Pelvis` translation and the engine refuses the model. Switch `monsters.yml` back when it is re-exported.

Review: `make_tour.py people` (`review/people_sheet.jpg`: the gates from outside, the East Gate guard, Main Street,
the square, the Lift Head, the Warden's Post, the North Gate, the walls and turrets, the lanes, from above and top
down); `review/density/sheet.png` (Landfall beside the MM towns at one scale). Guards and villagers stand on the
ground, the turrets sit on their mounts, the ranks read by their colours; after a minute the villagers have moved
and the posts hold (`review/people_later/06-square_above_after_60s.png`, first placement). `building_collision.yml`
and `crew_ramp_round_trip.yml` pass.

**Landfall's defenders** (2026-10-22, engine tactics: `devdocs/ACTOR_SCRIPTING_INVESTIGATION.md`, Tactics; data in
[`hesper_stage/monsters.yml`](../hesper_stage/monsters.yml) `tactics`, staged as `worlds/hesper/behaviors.yml`). The
user's review: the turrets turned away after a shot, the guards did not move at all, and the guards should fight at
range. The causes: the posts are placed `immobile` (`build_out1.py`), which the engine took as "never moves", even in
a fight; idle posts turned to the party now and then (MM8's background facing and fidget turns) and a turret's
Standing clip is a ±25° scan, so between shots its guns swung off the target; and the native ranged choice walks
ranged monsters in to melee at short range. MM's own town guards are free actors with a Short or Med wander radius;
Landfall keeps its posts, so the posts got a tactic instead of the native wander:

- **Posts** (the gate pairs, the Lift Head sergeants, the Warden's guard): stand at their spot facing their placement
  and never wander; once a fight starts they leave the spot to fight, at most 1 536 from it, and walk back and turn to
  their facing when it ends. The patrol (placed free) wanders like MM's guards.
- **Rifle band** (every guard): they shoot from 768–2 304 (edge distance), back off facing the target when it comes
  closer, close in beyond and circle the target between shots. The design's 25 % rifle butt (attack 2) is kept and is
  used only against an adjacent target.
- **Turrets:** turn to their target at 120°/s (Ward) and 75°/s (Bastion), fire only within 5° of it, keep tracking it
  between shots (slightly ahead of it), hold their last aim a few seconds once it is gone and then ease back into an
  idle scan around facing out (since 2026-10-23: tactics `scan`, `hes_turrets_claude/README.md`, Behaviour). `B_Barrel` pitches toward the target
  (−20…+45°, a little yaw lead) and Attack's first frame replaces the scan while they track
  (`hes_turrets_claude/integration/actors.yml`, `look: {target: combat, ..., hold_clip: Attack}`).
- They still fight only what turns on them: the party, once it strikes one (its group and its kin within 4 096 join
  in, as in MM). Kreegans need the relation work below.

Check: `landfall_defenders.yml` (headless, passes; from `output/hesper_stage/scenario_run`): the posts hold spot and
facing for 20 s, a struck gate guard steps out within its leash and keeps 600+ from the party, backs off when the party
closes in, and the struck Gate Bastion faces the party within 6°; idle, the Bastion scans within 41° of facing out,
and after the party leaves it holds its aim, then returns to the scan. Without the tactics it fails (a Lift Head sergeant
turns 6° off its post). Captures: `review/landfall_defenders/` (minimized engine tour `tour.yml`: the posts and the
scanning turrets at peace, every turret facing the party once struck, the guards backing into the gate).

**Engine work these need** (not done; content only):

- **Hesperian versus Kreegan relations.** Done (2026-10-23): the stage's `relations.yml` (engine add-on,
  `devdocs/ENERGY_SHIELDS_AND_RELATIONS.md`): defenders against Kreegans at the short range (2 560), Kreegans against
  the town at the close range (1 024), the Ashrunners against the town until S1, glassbacks against everything; the
  guards and villagers are kin (attacking one turns the town on the party). See [Shields and relations](#shields-and-relations-2026-10-23).
- **Energy shields.** Done (2026-10-23) for the guards' and turrets' Light and Standard shields; the guards' "Cover"
  reaction is not read (the fall-back reaction is for hostile monsters); still open: the rule flags
  `FleesWhenAttacked`, `ReputationOnKill`.
- **Patrol routes.** The patrol wanders round its start (Med, 2 560: a few hundred units a minute, like MM's street
  guards); walking a route along the streets and the wall-walk needs waypoints.
- **Talk.** Done for the East Gate guard (NPC 9003), Sergeant Ost (9521, the first Lift Head sergeant) and the North
  Gate guard (9522, the first North Gate guard) ([The arrival](#the-arrival-2026-10-22)); the villagers' news (block 5)
  and the other guards need their own NPC rows (`hesper_stage/npcs.yml`).
- **Glow.** The turrets' sensor lenses and the rifles' emitters are emissive, with no bloom.
- Every actor binding must have `stride_length` and `upper_body_root`, even a Stationary turret's (the stage supplies
  them); exempting Stationary bindings is optional.


## Hostile monsters (2026-10-22)

[`spawns.py`](spawns.py) places [`spawns.yml`](spawns.yml) (one hook in `build_out1.py`, after Landfall's people):
the map's **encounter spawn points** (scene `spawns`, written into the ODM) and the **placed squads** (initial
actors), each on free ground (an occupancy grid of the BModels' upright faces and their closed insides, the
decorations' collision, level ground below the dune walls, out of the brine for walkers, spawn points 500 off the
roads), moved outward in rings when the spot is taken; and the map's load event (84; since 2026-10-23 only the M2
gate: their hostility is the stage's `relations.yml`). It
writes `work/spawns_plan.json` (what stands where, what moved).

**How MM6-MM8 populate their outdoor maps** ([`spawn_density.py`](spawn_density.py): the shipped scenes, ODMs, event
scripts and map_stats rows; plots at one scale in `review/spawn_density/`, `sheet.png`: red circles the groups by
size, orange squares chests, purple triangles dungeon entrances, blue dots ground items, green the town). Expected
= hostile monsters on the first visit (spawn points at the mean of their slot's count, plus placed hostile actors;
invisible actors waiting for an event left out). Ramp = hostile monsters per million square units of land at
0-6 000 / 6-12 000 / 12-20 000 / 20 000+ from the town. Quiet = from the town's box to the nearest group. Guarded =
share of chests, dungeon entrances and ground items with a group within 2 500 (5 s of walking).

| Map | Spawn points | Group | Placed hostile | Expected | Land (10⁶) | Per 10⁶ | Ramp | Quiet | Spacing | Chests guarded | Entrances guarded | Items guarded | On road | Near edge |
|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| New Sorpigal | 56 | 3-5 | 5 | 229 | 845 | 0.27 | 0.04 / 0.12 / 0.52 / 0.33 | 0 | 910 | 0.78 | 0.67 | 0.43 | 0.11 | 0.13 |
| Castle Ironfist | 80 | 3-6 | 11 | 377 | 1403 | 0.27 | 0.12 / 0.21 / 0.24 / 0.29 | 0 | 1 719 | 0.33 | 1.00 | 0.54 | 0.30 | 0.08 |
| Bootleg Bay | 37 | 3-6 | 0 | 172 | 675 | 0.26 | 0.16 / 0.42 / 0.00 / 0.31 | 0 | 1 042 | 0.80 | 0.75 | 0.60 | 0.11 | 0.35 |
| Blackshire | 43 | 2-5 | 8 | 142 | 1934 | 0.07 | 0.05 / 0.03 / 0.06 / 0.09 | 0 | 3 009 | 0.67 | 1.00 | 1.00 | 0.14 | 0.20 |
| Frozen Highlands | 71 | 3-6 | 0 | 305 | 1906 | 0.16 | 0.07 / 0.07 / 0.14 / 0.20 | 929 | 2 501 | 1.00 | 1.00 | 0.00 | 0.15 | 0.23 |
| Emerald Island | 11 | 2-5 | 0 | 38 | 261 | 0.15 | 0.00 / 0.00 / 0.32 / - | 11 148 | 1 009 | 0.83 | 0.00 | 0.22 | 0.09 | 0.00 |
| Harmondale | 43 | 2-5 | 4 | 154 | 1922 | 0.08 | 0.00 / 0.00 / 0.05 / 0.12 | 9 163 | 1 909 | 0.33 | 0.50 | 0.06 | 0.21 | 0.09 |
| Erathia | 48 | 1-3 | 0 | 96 | 1679 | 0.06 | 0.00 / 0.00 / 0.04 / 0.09 | 6 480 | 1 052 | 0.64 | 0.00 | 0.62 | 0.08 | 0.31 |
| Tatalia | 43 | 1-3 | 6 | 92 | 1437 | 0.06 | 0.05 / 0.05 / 0.12 / 0.04 | 0 | 972 | 0.00 | 0.40 | 0.35 | 0.08 | 0.15 |
| Avlee | 53 | 1-3 | 0 | 106 | 1133 | 0.09 | 0.00 / 0.00 / 0.06 / 0.16 | 10 656 | 1 492 | 1.00 | 0.67 | 0.61 | 0.00 | 0.23 |
| Dagger Wound | 36 | 1-3 | 3 | 75 | 730 | 0.10 | 0.00 / 0.16 / 0.14 / 0.09 | 4 664 | 951 | 0.24 | 0.20 | 0.40 | 0.00 | 0.13 |
| Ravenshore | 59 | 1-3 | 0 | 118 | 1464 | 0.08 | 0.00 / 0.00 / 0.03 / 0.12 | 12 160 | 365 | 0.46 | 0.14 | 0.32 | 0.00 | 0.08 |
| Alvar | 61 | 1-3 | 0 | 122 | 1777 | 0.07 | 0.00 / 0.06 / 0.02 / 0.10 | 2 560 | 1 397 | 0.50 | 0.75 | 0.42 | 0.15 | 0.36 |
| Ironsand | 70 | 1-3 | 0 | 140 | 2030 | 0.07 | 0.00 / 0.03 / 0.09 / 0.08 | 7 983 | 1 715 | 0.82 | 0.60 | 0.53 | 0.00 | 0.24 |
| Garrote Gorge | 73 | 1-5 | 1 | 183 | 1869 | 0.10 | 0.05 / 0.08 / 0.09 / 0.11 | 96 | 1 528 | 0.75 | 0.75 | 0.50 | 0.08 | 0.08 |
| **Starport Reach** | 46 | 1-4 | 30 | 150 | 2025 | 0.07 | 0.00 / 0.03 / 0.03 / 0.09 | 3 928 | 1 630 | 0.90 | 1.00 | 0.57 | 0.13 | 0.22 |

- **Density.** MM6 is dense (0.16-0.27 per million square units of land, groups of 3-6; Blackshire 0.07). MM7 and
  MM8 settle at **0.06-0.10** (Harmondale 0.08, Dagger Wound 0.10, Ravenshore 0.08, Alvar and Ironsand 0.07), 75-180
  hostile monsters on the first visit, from **36-73 spawn points of 1-3** and almost no placed hostiles (Harmondale's
  91 and Ravenshore's 78 placed ones are invisible until their events).
- **Clusters.** Spawn points come in clusters: the median distance to the next group is 1 000-1 700 (Ravenshore 365),
  so an area holds two to four points and the open land between is empty.
- **The ramp.** MM7 and MM8 keep their towns quiet: no group within 2 500-12 000 of the town (Dagger Wound 4 700,
  Harmondale 9 200, Ravenshore 12 200), the first band near zero, and the density rising toward the far side (0.08-0.16
  beyond 20 000). MM6 puts monsters at its towns' edges.
- **Features.** Most chests have a group nearby (MM8 0.24-0.82, MM6 0.33-1.0); dungeon entrances often (0.14-1.0,
  MM6 nearly always); ground items about half (0.2-0.6). Groups avoid the roads (0-30 % within 1 000 of a road tile)
  and a quarter stand near the map's edge.

**Starport Reach** follows MM7/MM8 at the design's anchors (`STARPORT_REACH.md` "Monsters",
`make_starport_detail.py`'s groups), with the extra points of each area MM clusters round them:

| Family | How | Count | Where |
|---|---|---:|---|
| Drones (slot 1) | 32 random spawn points (Seekers, 2-4) + 2 fixed-B points (Hunters, 2-4) | ~102 | 21 areas: the apron and the Terminal doors (D1), the pass road, the north flats, Landfall's walls (B6), the crater rim, the hangar ruins and old hangars, the gantries, the service road bend, the canyon, its wreck, mouth and the Pumping Station hatch (D2), the south dunes, the east flats, the Archive dome (D10); Hunters at the Spinefall Pass mouth and on the road to the Scour |
| Drone Hunters | placed beside the design's Seeker groups | 4 | apron (1), pass road (2), canyon (1) |
| Glassbacks (slot 2) | 4 fixed-tier nest points (A, B) + 8 random (difficulty 2, 1-2) | ~18 | the glassfields F1-H3: the G2 and H1 nests, the H3 pups, the H2 locker |
| Glassback Bull | placed | 1 | the H1 nest |
| Ashrunners | placed, groups 30-32 | 14 | the camp (4 Scav, 3 Raider, 1 Gunner round the fire, facing out), the north dunes (3 Scav), the west dunes by the B5 locker (2 Scav, 1 Raider) |
| Kreegan Troopers | placed, groups 40-41 | 11 | the scrapyard fire team (6, a staggered line facing the Terminal), the forward outpost (5 in a ring round the alarm pylon) |
| **All** | 46 spawn points, 30 placed | **150** | 0.074 per 10⁶ of land (MM7/MM8: 0.06-0.10) |

- **Encounter slots** (stage `maps.yml` `slots`, map_stats Mon1-Mon2): slot 1 the Drones (difficulty 0: every random
  point spawns Seekers, 2-4), slot 2 the Glassbacks (difficulty 2: 70 % Pup, 20 % Glassback, 10 % Bull, 1-2). An
  encounter slot finds its tiers by "<picture> A/B/C", so the stage gives these rows the pictures `hes_drone A/B` and
  `hes_glassback A/B/C` (`monsters.yml` `picture`; the design table's `hes_seeker_drone` style has no family). The
  Hunters are fixed-tier B points at the far north and east (index 7) and placed Hunters beside the design's Seeker
  groups; the nests are fixed-tier points (A and B) and the H1 Bull is placed.
- **Quiet:** nothing within 5 000 of the Crew Ramp door (the arrival's scripted drones are the arrival's) or 2 500 of
  Landfall's wall; the B6 "hunts along the walls" stand 4 000+ north of it (group 50, hidden once M2 is done).
- **Guards:** every chest has a group within 2 500 (the scrapyard and outpost pods their Troopers, the camp crate the
  Ashrunners, the H2 locker a nest), the Terminal's doors (D1) and the Pumping Station's hatch (D2) two points each,
  the Archive dome (D10) three points round it.
- **Ramp:** Seekers near the start, Hunters and the Bull toward the north and east, the Kreegans at the far east end.

**Hostility** (since 2026-10-23 world data: [`hesper_stage/relations.yml`](../hesper_stage/relations.yml), staged as
`worlds/hesper/relations.yml`; engine: `devdocs/ENERGY_SHIELDS_AND_RELATIONS.md`). The Kreegans (the Drones, the
Troopers) and the glassbacks are hostile to the party; the Ashrunners while S1's QBit is clear (the rule switches off
when it is set, at once and for good: no event re-applies it). S1's QBit is **100101** (S1 Salvage Rights done, by
P4's formula S*n* done = 100100 + *n*: `design/kreegan_world/quests/QBITS.md`). Landfall's turrets and guards engage Kreegans within
2 560 and the Kreegans answer only within 1 024, so the B6 and crater-rim groups leave the walls alone. Event 84 now
only hides group 50 once M2 is done (`spawns.yml` `hide_after_qbit`); the old `hostile` / `until_qbit` lists and their
`evt.SetMonsterRelation` calls are gone. Saves made before 2026-10-23 still carry those per-map overrides; start a new
game on the stage.

Check: `hostile_spawns.yml` (written by `make_spawns_scenario.py` from the build; run from
`output/hesper_stage/scenario_run`): the Trooper, the Ashrunners, a Hunter, the Bull and the first spawned drone are
hostile at their spots on load, a guard and a villager friendly, and with S1's QBit set the Ashrunners are friendly
on the next load. Tour: `make_spawns_tour.py <dir>` (`review_tour_monsters.yml`, every group and three aerials).

**Engine needs** (content only here):

- Per-world relations: done (2026-10-23, above). The Glassbacks are hostile to everything; one that senses the party
  still keeps the party as its target (the native target choice), drones engage it either way.
- The Ashrunners "hold position and warn first" before S1 (STARPORT_REACH.md): no warning behaviour; they are plain
  hostile Med wanderers.
- The outpost's alarm pylon calling drop pods and the Troopers' shield link (FireTeam) are not read by the engine;
  the energy shields are (2026-10-23, [Shields and relations](#shields-and-relations-2026-10-23)). The Troopers keep range with the guards' `ranged_band` tactic.
- Spawn points cannot carry the Aggressor bit (their attributes are 16-bit), so a spawn's hostility comes only from
  relations.

## The arrival (2026-10-22)

Every party starts at its crash (design: [STORY](../../../design/kreegan_world/STORY.md#arrival-all-three),
[STARPORT_REACH](../../../design/kreegan_world/zone1/STARPORT_REACH.md#how-the-zone-plays) step 1-2). The world's
start map is now `hes_out1.odm` (`hesper_stage/stage.py` `world.yml`); D0's Crew Ramp door and its surface arrival are
unchanged (`out1_build.json` `arrival`, `crew_ramp_round_trip.yml` passes). Review: `review/arrival/sheet.jpg`
(minimized engine tour `review_tour_arrival.yml` from `make_tour.py arrival`, plus two timed single shots: `20-` the
drones coming down 39 s after the load, `21-` the town quiet a minute on).

- **The wreck.** The lander ploughed the crater from the north-east and slewed up its south-west wall; its hull rests
  on a shelf it cut (`flatten`, along the wall, at the wall's height at 0.9 crater radii, direction -142 degrees from
  the centre), its nose toward the Crew Ramp door (cracked by the crash), its open hatch toward the rim. Models
  (Meshy Smart Topology from Codex HD masters, Codex-painted and baked:
  `level_generation/props/hesper_decorations`, designs `hes_lander_wreck` (from the lander in concept 01), `hes_lander_wing`,
  `hes_lander_engine`; 15 credits): the hull 1 200 long with an invisible collision box (`building`), the torn-off
  wing on the floor, the engine nacelle (radius 110). The debris trail from the first impact past the roof hatch
  to the hull: three plate heaps, the wing, the nacelle, a container, crates, drums, luggage; the native `smoke`
  emitter (decoration 23) on the hull (three) and on the wing and the nacelle. The rim's glass and the wild dressing
  are dropped within 900 of the hull after their scatter.
- **The start.** The Party Start stands on the rim above the hull's nose (direction -134 degrees, 1.02 radii),
  facing the East Gate: Landfall's north-east corner tower and wall stand just west of the rim. The entity's facing is
  in yaw units (2048 a turn), as the engine reads a Party Start (it was written in degrees until 2026-10-23);
  `out1_build.json` `party_start` keeps degrees.
- **The Pilot** (NPC 9001, `hesper_stage/npcs.yml`, P4's dialogue/ARRIVAL.md since 2026-10-23): a click on the hull
  (event 85) is `evt.SpeakNPC(9001)` until he gives the party his core; then "The wreck's console is dark. The Pilot
  rides in your pack." (M4 given, 100204) and from M4 done (100004) "... The Pilot is aboard the lander in Hangar Nine
  now." (he speaks from D0's events 19 and 34). Topics: Planetfall (M1), Black box (100232), The stash, Drones (until
  M2), Log cores (one Lander Log Core 11486 read per use; the third closes the black box, 100233), Below the rim (gives
  the Pilot's Core 11489, M4 given), The repair list, The Harvester (M8), Re-entry (M12). **The stash** is the colonial
  locker under the hatch (chest 9, event 49, 150 gold), in every state. The three log cores (2026-10-23, P4's
  `quests/ITEM_PLACEMENT.md`) lie on the floors of the small debris craters C5, D6, D7 (their centres, the design's
  `log` places): ground items, the scene's sprite objects (`out1_build.json` `log_cores`), drawn with the stand-in
  Topaz model while their own icon is P4's (`hesper_stage/items.yml` `ground`).
- **The drones.** Four Seeker Drones (10050, actors 35-38, group 70) wait invisible (Invisible and Aggressor bits)
  1 100-1 340 over the crater's north-east floor. Event 87, a map timer of 900 game seconds (30 s), shows them the
  first time (map var 21); they come at the party (`20-`). Event 86 (on load) says so on the first arrival (map var
  20). Landfall's turrets and guards against the drones (2 560 one way, 1 024 the other: the B6 and crater-rim groups
  do not march on the town) were set here per monster id until 2026-10-23; they are now `hesper_stage/relations.yml`.
- **The East Gate's south guard** (actor 11) carries NPC 9003: Strangers ("You came down in that? ... The Warden will
  want a word", QBit 100700, a P4 dialogue flag: CR-P4-01; until M1), Landfall and The walls (after M2).
- **Venn** (NPC 9513), her home's door (house 15, event 65): since 2026-10-23 her shop, vendor 9460 (below). **D1's relay post** (event 38, P4's `relay_out1_d01`): dead before M2, Aster's call to the
  Chapel after it, "I am with you" after M3. The shopkeepers Brask, Ysel, Mother Ama and Lorn wait until Landfall's
  houses 1-4 are real houses (9201, 9202, 9450, 9451).
- **The Warden** (NPC 9002), the Warden's Post's door (event 55, `evt.SpeakNPC(9002)`): Report (shown until M1 is
  done: closes M1, QBit 100001, clears 100201, 1 500 experience, autonotes 10011 and 10012), Hesper, Kreegans, Dead
  Terminal (shown after M1: gives M2, QBit 100202; after M2 the lift is theirs), Hacking, The Undervault (after M2).
  The captain's name clashes with the
  D7 boss, The Warden (10107): kept as the design has it, to be renamed.

QBits of the arrival: 100001 M1 done, 100002 M2 done (D1), 100201 M1 given, 100202 M2 given, 100700 the gate guard
has spoken (100203 is M3 given, set at D1's relay; 100101 is S1 done, read by spawns.yml). Portraits: `design/kreegan_world/art/portraits` (`hes_pilot`,
and new `hes_warden`, `hes_gate_guard`, `CODEX_BRIEF_ARRIVAL.md`), installed as `npc9001-9003.png`.

**Not checked headless / needs engine or tool work:**

- The headless runtime does not run outdoor map timers (`advance_runtime` updates the world, not the scene's
  timers) and engine tours hold game time still, so the drones' appearance is checked only in a timed single
  screenshot (`20-`). Whether the wall turrets shoot an arrival drone that chases the party to the gate is not
  checked: it needs a moving party in the game (a minimized timed run cannot move it).
- The scenario's actor activation builds a hit without the actor's NPC id, so `arrival.yml` speaks to the guard
  with `speak_npc 9003` (the game's own click carries it); outdoor model decorations cannot be clicked headless
  (the hull's event 85).
- The rule and patrol work listed under Landfall's people (relations and shields: done 2026-10-23).

## Shields and relations (2026-10-23)

Engine: [`devdocs/ENERGY_SHIELDS_AND_RELATIONS.md`](../../../devdocs/ENERGY_SHIELDS_AND_RELATIONS.md). Data:
[`hesper_stage/shields.yml`](../hesper_stage/shields.yml) (the rate table as grades, colours, placeholder sounds) plus
the design's `monster_hesper.txt` for the staged monsters (stage.py writes `worlds/hesper/shields.yml`), and
[`hesper_stage/relations.yml`](../hesper_stage/relations.yml) (factions: kreegans, defenders, villagers, ashrunners,
wild).

On this map: the gate guards and sergeants (Light 1 000-1 400), the Warden's guard (Standard 1 800), the Ward
Turrets (Light 800), the Gate Bastions (Standard 2 200), the Troopers (Light 1 000) and the Ashrunner Gunner (Light
500) carry shields; drones, glassbacks, the Scav, the Raider and the villagers have none (their bodies take energy at
x1.5). The shells are pink by grade.

Check: [`shields_relations.yml`](shields_relations.yml) (headless, passes; from `output/hesper_stage/scenario_run`):
the Trooper's shield against spells, physical and Kreegan energy, the break, the exposed body, the 4 s delay and the
regeneration; a drone by the East Gate engaged and killed by the guard and the gate's turrets; a drone hitting the
Glassback Bull; S1 set mid-visit turning the Ashrunners friendly at once, still after 30 s and after a save and load.
`landfall_defenders.yml`, `arrival.yml`, `hostile_spawns.yml`, `building_collision.yml`, `crew_ramp_round_trip.yml` and
the stage's `tech_skills_landfall.yml` pass with the relations as data.

Captures: `review/shields_20261023/` (minimized, slow motion `debug.time_scale=0.25`, tours beside them): a spawned
Starport Turret's shell, a hit, the break flash, swell and shatter, the shield down, back up and in the inspect
portrait (`01-12`), the same without bloom (`nobloom_`), Hangar Nine's turrets indoors with a break and the rise
(`d00_`), the scrapyard fire team's shells (`troopers_shells_idle`), and the MM6 before/after checks
(`mm_before_after/`: identical but for the creatures' own motion between spawn and capture).

### Follow-ups (2026-10-23, later)

Engine: the same devdoc, "Follow-ups". On this map: the Glassbacks' bodies ignore energy weapons (the drones' shots
included: a Bull now kills a drone without a scratch); the scrapyard Trooper and the Ashrunner Gunner fall back while
their shields are down; the staged Grip Gauntlets (`item give 11108`) carry a personal shield of 100 and the Shield Cell
(11300), Shield Burst Cell (11301) and EMP Grenade (11303) work from the inventory (dropped on the paperdoll). The
shells are subtler (Light 0.7, Standard 0.8, Noble 0.95).

Check: [`shield_followups.yml`](shield_followups.yml) (headless, passes; from `output/hesper_stage/scenario_run`): a
spawned Glassback untouched by 400 Kreegan energy and 400 blaster damage; a spawned Trooper engaging within its band,
falling back past 2 700 once its shield breaks and returning within 2 600 after it is back up.
[`shields_relations.yml`](shields_relations.yml)'s Glassback step now expects the Bull at full HP and the drone hurt.

Captures: `review/shields_followups_20261023/` (minimized, bloom, `tour_hes_main.yml`): the Grip Gauntlets' cyan rim
on the inventory screen and the HUD (02, 03, `rim_zoom_*`), an absorbed hit's blue number (04), the rim under the
turret's fire (05, 05b), an EMP grenade (06-08; `actor shield last` logged 325 before and 200 after, half of the
regenerated pool), the shells before and after the intensity change (`shell_*`, `shell_cmp_*`) and the MM6/MM7
before/after set (`mm_before_after/`: inventories identical, the outdoor and indoor views differ only in creature
animation timing).

### Projectiles (2026-10-23)

Every Hesper gun fires its own missile (design: `design/kreegan_world/PROJECTILES.md`; staged from
`hesper_stage/projectiles.yml`): the Ward and Starport Turrets the Ancient blue bolt, the Gate Bastion the heavy twin
bolt, the guards a slim rifle bolt, the drones Kreegan orange darts, the Trooper and the Ashrunner Gunner Kreegan plasma,
the Scav and Raider the Ashrunners' yellow and cyan salvage blaster, the crawlers green acid. Captures:
`review/projectiles_20261023/` (`strip.jpg`, `mm_before_after/`).

### True aim (2026-10-23)

Engine: [MONSTER_MODIFIERS](../../../devdocs/MONSTER_MODIFIERS.md) (a world's `modifiers.yml`). The staged turrets
(the Starport Turret 10054, Landfall's Ward Turret 10065 and Gate Bastion 10066) have `true_aim` (720 degrees a second
for 3 s) and `never_staggers`, from the design's `TrueAim` and `NeverStaggers` flags: their lasers turn after a party
that steps aside and stop only at cover.

Check: [`true_aim.yml`](true_aim.yml) (headless, passes; from `output/hesper_stage/scenario_run`), by the crew ramp,
where no monster spawns: a spawned Starport Turret's shot at the party, which steps behind the ramp, turns after it and
ends against the ramp, the party unhurt; a fresh turret's shot at the party strafing in the open turns onto it and hits.

Captures: `review/true_aim_20261023/` (minimized, `debug.time_scale=0.25`, `tour_hes_true_aim.yml`): the turret, its
laser bending onto the strafing party (02, 03), and the MM6 before/after set (`mm_before_after/`, a build with this
work's runtime hooks undone against the current one: New Sorpigal's gate and Agar's Laboratory with spawned archers and
an Archmage firing; the differences equal those between two runs of the same build, the spawned creatures' own motion).

### Charge (2026-10-23)

Engine: the `charge` modifier ([MONSTER_MODIFIERS](../../../devdocs/MONSTER_MODIFIERS.md)), from the design's `Charges`
flag: the Glassback Bull (10082) on this map, the Drudge Brute (10001) and the Lancers (10020-10022) where they are
placed. A charger with the party in sight 384-1 280 away (the Bull 1 536) winds up, then dashes along that line; it hits
once and throws the party back, or misses and stumbles.

Check: [`charge.yml`](charge.yml) (headless, passes; from `output/hesper_stage/scenario_run`), west of the wreck where
no monster spawns: a spawned Bull charges on its own and hits the party; a second Bull's charge misses a party that
steps aside during the wind-up and ends against the glass tree up the lane. The lane east of it is closed by the glass
tree at (-9 704, -11 895), which stops a charge as any decoration does.

Captures: `review/charge_20261023/glassback_bull_charge.jpg` (minimized, `debug.time_scale=0.5`, the input tour
`tour_charge.yml`): the spawned Bull, its wind-up, the dash and the contact.

## The camp, the shops and the homes (2026-10-23)

The integrator's follow-ups 24, 36, 37 (the tablets), 39-41 and 35's relay check (`design/kreegan_world/WORK_PACKAGES/
requests/P4.md`), P4's texts (`quests/dialogue/ASHRUNNERS.md`, `LANDFALL.md`, `NPCS.md`, QUESTS S1). The people, houses
and shops are [`hesper_stage/npcs_landfall.yml`](../hesper_stage/npcs_landfall.yml); Dace is a teacher row of
`hesper_stage/skills.yml`, the news items 9771-9790 are `npcs.yml`'s.

- **S1.** Round the camp a ring of invisible pressure plates (BModel `camp_edge`, 144 triangles 10 above the ground,
  an ellipse 2 350 x 2 150 out from the fire, 300 wide; event 27): the sentry's shout ("Turn round, lamp-folk! ...")
  as a message, once a visit (map var 22, cleared on load), sets 100221 until S1 is done. The stolen crawler stands in
  the scrapyard (BModel `scrapyard_crawler`, a hull with its door to the yard's west gate); its door is the console
  (event 26): 100101, 100221 cleared, autonote 10413, P4's message (ASHRUNNERS, "The crawler's console": the painted
  HOME, "You press it ..."). It then rolls home: the faces of the scrapyard's crawler (cog 9201) and the camp's (cog
  9202, on the south track's end, built Invisible and Untouchable) swap by `evt.SetFacetBit`, and the load event (83)
  repeats the swap from 100101. She stands on a low plating slab, the bay (BModel `scrapyard_bay`, its top event 28
  "The crawler bay"): once she has gone its click shows P4's after line, "Track marks lead north-west, toward the
  Ashrunners' camp." (a status line; event 26 says the same if reached).
- **The camp folk** (P4's row 10262, staged in `hesper_stage/monsters.yml` on the Ashrunner Scav's binding, pistol
  included; faction `ashrunner_folk`, friendly, in `relations.yml`): Garrow 9507 (before the largest hull: The Foundry
  M12, The crawler S1's Engram and 100113, The derelict, Ashrunners), Dace 9224 (before his workbench hull: Holding a
  field, Grandmaster Shield Tech from M12), Old Ketter 9581 (the watchtower's foot), Juna 9582 (by the camp's crawler)
  and Teg 9580 (the south-east edge), actors 69-73 in group 33, posted, Invisible until S1 (the console and the load
  event show the group). They follow every other actor, so the earlier indices the scenarios name hold;
  `hostile_spawns.yml` takes its indices from the built scene (`make_spawns_scenario.py`, now run by `build.sh`;
  its first spawned actor is 74). In the game the group shows on the next load of the map; a console `event 83`
  showed the crawler swap at once but the folk only after `reload map` (the click's own path was not captured).
- **Shops** (the engine's deterministic vendor stock, MM9's vendor tables, as the world's `vendors` contributions):
  Venn's home (event 65) is vendor 9460 (Shield Cells, Stims, Hesper Rations; the Ash Cloak waits for its paperdoll
  art), Venn living in it; Kesh's stall (event 25, from S1) is vendor 9458 (Breach Charges, EMP Grenades, Shield
  Cells; the Arc Coupler I is an implant, not staged), Kesh in it.
- **Landfall's people:** the cliff homes 18-24 and the family homes 25-27 (events 68-77) enter houses 9461-9470, one
  resident each (Brin 9523 ... Kalla 9532; a home with one resident opens on him or her, as MM's do); six villagers
  are the street people Lune, Merrit, Nessa, Kito, Pria and Quill (9533-9538, actors 20, 23, 26, 27, 30, 33:
  `STREET_PEOPLE`). Each has two News items (one opening 9771-9774, one later 9775-9790, all sixteen later items
  dealt once) and the street pool's face, and one short greeting from P4 (LANDFALL, "Street people and home
  residents: greetings").
- **The founder statue** (event 34, cog 34; CR-P3-11, follow-up 40): carrying the Founder's Head (11511) the party
  sets it back: the item taken, 100301, autonote 10020, the model swapped to `hes_founder_intact` (`evt.SetSprite`,
  repeated on load), once (100730) reputation -5 (`AddValue(ReputationInCurrentLocation, -5)`, the reputation the
  shops read), the CR's message; without it "The head is gone; the neck is broken clean."
- **The tablets** I-III (11360-11362, readables) lie on their plinths (events 35-37) as ground items. The second
  plinth is at B6 (`make_starport_detail.py`), not E7 as ITEMS, ITEM_PLACEMENT and STARPORT_REACH's text say.
- **D1's relay post** (event 38): dead again after Tear it out (100034).

Captures (minimized engine tours): `review/camp_20261023/`. Not done here: the crawler shed's Wick (9520, house 9471) and Landfall houses 1-4's keepers; the minimap was not
re-rendered for the two crawler hulls.

## The Archive's door and the crossings (2026-10-23, the integrator)

- **D10, the Colony Archive:** event 13 on the dome's hatch enters `hes_d10.blv` at its semantic `dome_stair` once
  two shards are restored (100022); before, "Sealed. Four crystal sockets ring the hatch." The four sockets (cogs
  91-94) light when Aster's shard n is restored (100017 + n): the load event (83) swaps them to
  `hes_crystal_socket_lit` (the socket model with a light; `hesper_stage/decorations.yml`). D10's exit reads
  `out1_build.json` `archive_arrival` ([x, y, z, degrees]: 500 south of the hatch's face, facing it).
- **The crossings' paving:** the old road's pavers are dusted toward the east (the Scour) and north (the Brood Spires'
  pass) edges, 85 % at the edge and gone 4 800 in (ash, east with a little canyon red), so they meet the Scour's
  dulled pavers without a hard change of tone. Captures: `review/crossings_20261023/`; checks: the stage's
  `rebuild_all.sh --scenarios-only`.

## R5 Gloamling canyon den — 2026-10-26

`spawns.yml` adds five Gloamlings (10320, group 90) near the Pumping Station entrance at G6, away from the arrival
path and Landfall walls. Their indices 74–78 follow the existing Ashrunner folk, preserving all earlier actor
indices and the hostile-spawn scenario's encounter boundary. No existing spawn is removed or replaced.

The local build adds a 62-face canyon-rock overhang after ground placement, whose 2D wall mask cannot represent
a roof. Continuous inner/outer shells make a thick mouth and terrain-buried rear walls; the native terrain remains
the floor. Eight roof samples around each actor's radius verify at least 458 units of headroom for 140-unit
Gloamlings. Lighting and the minimap are regenerated for the final geometry.

`out1_gloamers.yml` advances a minute from a distant observer: all five stay near the den, at full HP and with
no target. Existing outdoor scenarios are rerun after the final shell revision. The direct minimized NVIDIA OpenGL tour succeeds, with the matching bake installed;
[cave mouth](review/gloamers/01-canyon_cave.png) and [interior](review/gloamers/02-canyon_den.png) were inspected.
Three additional Blender views were reviewed. Evidence:
[creature project](../../creatures/hes_gloamer_codex/README.md).
