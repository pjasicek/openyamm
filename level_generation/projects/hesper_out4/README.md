# Hesper: the Crown (`hes_out4.odm`, map 9130)

The Kreegan capital and Hesper's last outdoor map, built from its design
([THE_CROWN.md](../../../design/kreegan_world/zone4/THE_CROWN.md), BUILD-READY) into the shared
[Hesper stage](../hesper_stage/README.md). The design is the one source: the terrain functions of
`design/kreegan_world/zone4/crown_terrain.py` and every place, road, footprint, cover piece, decoration group, chest,
monster group, pylon, relay, hatch and the plaza lift of `crown_detail.json` (`make_crown_detail.py`). Starport
Reach's kit is reused (`../hesper_out1/bmodels.py`, `houses.py`, `spawns.Ground`).

## Build

```sh
level_generation/projects/hesper_out4/build.sh            # sky layers, map, minimap, stage (under the stage lock)
flock output/hesper_stage/locks/bake.lock level_generation/projects/hesper_stage/bake.sh hesper_out4   # after every build
```

1. `make_sky_out4.py`: the horizon band (`hesper_crown_horizon`) and the night sky with the aurora composited
   (`hesper_lattice_night`) into `design/kreegan_world/art/sky/hes_out4/runtime/`; the stage merges the zone's
   `sky_preset.yml` (`hesper_lattice`, theme `hesper_crown`) and cooks them.
2. `build_out4.py`: heights (800 + 1 500 h with the design's relief, roads graded, pads levelled, the slabs, the
   pit's passage and the node causeways out past their doors at the floor's 1 088, the hatches at their first
   build's levels, cut-off pits smoothed open, the notches flat at 1 200 for 1 600 inside both crossings: built
   **1 216**, the nearest height step; the arrivals other maps read are asserted unchanged, `PINNED_ARRIVAL_Z`), one tile per cell, the eight material layers
   (`terrain_materials.yml`'s targets as tints; roads and tracks painted crisp), no plants, the BModels
   (`bmodels_out4.py`), decorations, chests, ground items, actors, spawn points, the events, then the ODM through the
   editor's writer, verified against the sources. Writes `source/`, `runtime/worlds/hesper/` and `out4_build.json`
   (arrivals, door poses, actor groups: D6 and D12 read their exits from it).
3. `build_minimap_blender.py`, `finish_minimap.py`: the approved minimap recipe (as Starport Reach's).
4. `prepare_resin_paving.py` (once): the `resin_paving` terrain material from Poly Haven `slate_floor` (CC0, 2.29 m,
   `assets_source/engine/terrain_materials/sources.yml`), its slabs turned violet-black and its joints painted violet
   into the albedo (the engine-safe alternative of P3's R3 review: no terrain emissive). Library row in
   `hesper_stage/terrain_library.yml`.

## Check

`check_relief.py` (read-only; the stage's `check_walkability.py` reads BLVs only): every arrival, door pose, grounded
actor, spawn point, chest and item on a walkable terrain tile of the open floor (the engine's 512 span rule), no
cut-off pit, the roads' grades (2026-10-24: 97 places, 0 pits, paving at most 12.5 %, tracks 6 %).

From `output/hesper_stage/scenario_run` (`make_scenarios.py` writes them from the build; all four pass, and the
stage's `rebuild_all.sh --scenarios-only` sweep 73/73, 2026-10-23):

- `crown_entrances.yml`: the three blast doors in and back out (D6, D7, D16; a node not staged says "not yet open");
  the three hatches sealed before their node bits, D6's open after M10; the Spire Gate and the pad lift refused
  without 100603, into D12 with it (100603 set on load from the three node bits), up D12's pad lift back to the plaza.
- `crown_market.yml`: the Kept hostile while collared; the collar node (Hacking Novice) sets 100601 and 100726 and
  turns Labourers and Enforcers friendly; after a reload Vesk's stall (house 9400) opens on Vesk; with M7 (100007)
  Sorrel's stall (house 9401) opens on Sorrel.
- `crown_edges.yml`: the west road to the Brood Spires and back, the Kreegan Road to the Scour and back (map edge
  travel from `hesper_stage/edges.yml`).
- `crown_ring.yml`: the Blooding Ring: in through the gate, Huntmaster Vreth (actor 47) hostile on his dais, his
  charge started and hit, his death (his line, event 151) sets 100609, which holds after a reload.

**Checked in the game** (headless cannot: no outdoor map timers, no clicks on model decorations), minimized,
`review_input_checks.yml` → `review/game_checks/`: the test emplacement fighting (04, 05), the plaza at night and dusk
(07, 08), the city with the three nodes down (09), the lander on the pad with 100607 and its boarding (10-12:
`qbit 100016=true`). The great cannon (2026-10-23, `review/cannon_final/sheet.jpg` from `review/cannon_stages8/`):
from (-9 500, -4 000) at night, the game trace's `event_set_sprite` for cog 9311 runs c1, c2, c3, c4, c5, dark,
then rest 6 s later, twice; the captures show each stage, the muzzle flash, the pulse's bead trail and the blast.
The Blooding Ring (`review_input_ring.yml` → `review/ring_checks/`, stills `make_tour.py ring01 ...` →
`review/ring01/`): the blind wall hides the floor from the ring road's patrol and the track; inside the gate
Vreth's first line shows (event 150 fired) and the console reports autonote 10304 set; the fight with the immortal
party. Seen there: his charge is not held by the post's leash (he dashed out through the gate into the passage at the
party; the blind wall stops him, and he walks back), an engine matter for the leash.
**Not verified:** the air raid (event 4) needs a party with a real Fly cast (a debug `start_flying` party is dropped
to the ground).

The scripts call `isFlying()`, not `IsFlying()`: `engine/scripts/common/event_support.lua` exports `support.varTag`
into the globals (line 1682) after it defines `IsFlying` (line 1644), so `IsFlying` is the number 0xF0 and every call
throws; a map timer's Lua error is silent (`session.lastError`, never logged). Until the cannon timer used
`isFlying()`, it never locked.

Review: `make_tour.py build01` → `review/build01/sheet.jpg` (BUILD-READY 8's named shots, aerials, a top-down,
both edges from this side); `make_sheet.py <folder>` makes a sheet.

## Status (2026-10-23, build 1; one great cannon and the enlarged Crownspire, then the Blooding Ring, the same day)

Built: the crater, rim and both notches; the Crownspire (an 8 640 square, walls 3 200 high, the gatehouse and
Spire Gate, the dome to 8 000 with a 1 500 tower on its crown carrying the great cannon), the four bastions (radius
1 100, 3 600 high) with a Crown Sentinel (10057) on each, the three node blockhouses with their blast doors, masts
and conduit runs, the seven cover slabs and the crawler wreck, the landing plaza and pad lift, the West Ward's spines,
the five roosts, the five sheds, the Kept market (five pens, plinth with the collar node, pavilion), both stalls, the
colony ruins, the three service hatches in their outcrops, the test plinth and blast wall; 278 decorations (every DECOR
group placed: fire bowls, gilded fire bowls, grafting frames, banners, pods, crates, spools, dead pylons, trophies,
shards, boulders, debris), 9 chests, the three S9 tablets, four gold piles, three scouts' caches; 43 placed actors
(door posts, roosts, district masters, the market, Anni and Tor, the test emplacement, the hidden raid) and 24 spawn
points (10 Drudge Hulk gangs and 7 Overseer flights at tier C, 7 Noble patrols); every event of section 17; the bake.

The great cannon: one cannon on the dome's crown (cog 9311, pivot at 11 565). A map timer every
half second (event 3) locks it on a party within 11 400 of the centre (16 000 flying) and in its sight, a ray from the
pivot against the slabs', the wreck's, the blockhouses', the conduits', the fortress's and the bastions' shapes; one
lock at a time. Over the 3 s lock its decoration steps through the wind-up states (`hes_great_cannon_c1`..`_c5`: the
core, the pods, the first two rings, four rings, the full charge with a white-hot muzzle and three arcs), its head
turns to the party at 120° a second (`evt.AimDecoration`, about its origin from the rest facing south) and a red lock
beam joins the turned muzzle to the party (`evt.BeamToParty`, `crown_effects.py` `hesper:fx/beam/crown_lock`, tapering
to a thread at the party's eye). Then the release: the beam stops, the muzzle flash at the bore's mouth, the ion pulse
(the CrownIon missile, `evt.FireMissile`: 0.15 s to the party; its flight and blast are
`hesper_stage/projectile_effects.py` `crown_ion`: sphere, ground shock ring, arcs, debris, smoke) whose blast gives
every actor within 600 the strike's 1 500 Energy, the head's 350 recoil (`evt.RecoilDecoration`), 1 500 Energy at
every character (`evt.DamagePlayer`), the cannon dark for the 6 s recharge, then back to rest. The model is the ion
cannon project's
(`level_generation/creatures/hes_ion_cannon_codex/export/`, seven states, four LODs, `check_winding` clean; ahead of
`hard_surface` in the stage's `source_dirs`, over the Blender stand-in), height 2 470; the shot leaves its measured
muzzle, (+4.9, -3 188.9, +1 150.5) from the mount's base (`MUZZLE_*`), turned with the head. Its wind-up from the plain
and three side stills: `review/cannon_model/` (`windup_crop.jpg`, `sheet.jpg`, `stills.jpg`; tour
`review_input_cannon.yml`, an input tour, since a screenshot tour holds the map timers); `crown_cannon.yml` checks the
strike and the splash headless. The test emplacement does the same at 2 500 with 15D10 while its actor stands. The
Jammer and the alarm pylons' 20 s are not modelled (the pylons are hackable dressing, as the design says).

**The Blooding Ring** (a follow-up: THE_CROWN.md section 7, `design/kreegan_world/HARROWERS.md`): the Harrowers' pit
against the east rim at (17 700, 9 400), 300 east of the design's centre so its pad (radius 1 500, flat at the floor's 1
100) cuts into the rim's foot and the cliff rises behind its east side. The floor 2 400 across is the resin paving to
the wall, scored with blade cuts (strokes a texel wide of the grey ash layer at most 0.6, most in pairs; a separate
random stream, so the map's other placements stay put). `bmodels_out4.blooding_ring`: a ring wall of black resin
(`hoaresin`, `hnresin` coping) 400 high and 150 thick in 32 sides, its gate the two west sides, cheek walls lining the
gate 250 past the wall with a gate post (`horoost`) at each, and a **blind wall** 800 before the gate (1 950 long, a
deviation): without it every point of the ring road saw up to 37 % of the floor through the gate, and the design says
the patrols do not see in. The build checks it (`ring_sight_from_road`: every 100 of the ring road within 8 000, eye and
target under the walls; 0 %). The passage round the blind wall is about 550 wide; a scree track runs from the ring road
to the blind wall, where the glyph plate (event 21) stands; two fire bowls against the blind wall's inner face light the
passage (it lay in both walls' shadow). Inside: the low bone dais (`hokspine`, an `hptrim` top, 90 high), six fire bowls
on the wall's foot, five trophy piles between them, two banners by the gate's cheeks. **Huntmaster Vreth (10147)** on
the dais facing the gate: placed immobile (group 91) with `post: {leash: 1300}` (`hesper_stage/monsters.yml`; a posted
actor of a wandering monster still moves and charges in its leash), his charge and blink from the world's
`modifiers.yml` (the design's rows), in the kreegans faction (`relations.yml`). His behaviour `hesper/huntmaster`
(`huntmaster.lua`, `behaviors.yml`; the build copies it into the runtime tree): no flee, at half health his line and a 1
s roar (`perform` clip `frenzy` with `vreth_roar` and the ember effect, until the engine's `frenzy`), his death line
(the lines P4's: `quests/dialogue/CROWN.md`). Events: **150** a timer every half second, once per visit (`ring_seen`,
cleared on load) when the party is inside the ring: his first line and, the first time (MapVar 5), autonote 10304
(`hesper_stage/npcs_crown.yml`); **151** his death (`RegisterMonsterKilledHook`, group 91 dead) sets 100609; the load
event hides him once 100609 is set, else gives him the **Striking Lattice** (11227, staged in `hesper_stage/items.yml`
with its approved icon), which drops with his body (the map Lua cannot read where he fell). Stand-in body: the Kreegan
Trooper C at ×1.35 without the carbine and buckler (`vreth_standin.yml`; height 294, radius 81) until
`hes_harrower_codex` stages his model. Not done (engine): the frenzy, the afterimage effect on his blink, his own sounds
(`vreth_roar` and the Harrowers' set).

**The relief** (2026-10-24, the user: "the Crown is basically almost all flat, feels wrong"; `crown_terrain.py`
"The relief", P3.md "Builder's report: the Crown's terrain relief"): heights 32-5 920 (were 1 056-4 736). The table
round the Crownspire, the W, E and N causeways out to the node doors and on to the ring, the ring road's band, the
plaza, the districts' cores, the pit and its passage, the hatches and both crossings stay at their levels; the
killing ground falls from the table in three terraces into three basins (about 930 deep; knolls of rock on their
floors) and climbs back in two banks to the ring; the gate road comes down a spine and up a cut in the table's edge;
outside the ring two terraces climb to a higher, broken rim with buttress spurs and ridges of black glass, opened
into ravines along the ring road, the tracks, the hatches and the pit. The cannon's sight ray also tests the ground
(the map's height bytes in its Lua). The slope layer starts at 0.22 (was 0.32), so terrace and ridge faces read as
rock. Review: `review/relief_20261024/` (`make_relief_tour.py`, `make_hillshade.py`, `make_relief_sheet.py`); the
previous design and build files are in `work/before_relief_20261024/`.

**Stand-ins and deviations:** the Court Overseer on D5's Overseer stand-in, the Kept Enforcer and Labourers on the
villager body, the test emplacement on the Ward Turret, the plain fire bowl on the brazier (as everywhere), the
lander on Starport Reach's wrecked-lander model. Sounds (zone 4's ElevenLabs batch, `design/kreegan_world/AUDIO.md`):
the cannon's charge, `cannon_charge_1` to `_5`, one stage a tick through the lock's wind-up (by its progress, never one
twice; nothing more once it breaks), `cannon_pulse` and `cannon_blast` at the party on the release (event 3),
`market_crowd` at the plinth every 5 s while collared and the party within 6 000 (event 6, until the engine's ambience
loop), `vreth_roar` at the dais with his first line (event 150) and in his half-health roar; the Lattice hum waits for
the ambience loop. The plaza pad is 20-sided (an ODM face has at most 20 vertices; the design's 32 would break its
single fitted `hoplaza` face). The slope layer is `rock_ground` (the design's red-brown `rock_cliff` read salmon under
the violet light) and the rim's glass a milder tint (obsidian's target/mean tint turned its facets pink). The pens are
open on their plinth side so the Kept are seen. No dry lightning (an engine need): no weather entry.

## R5 Ashkites (2026-10-26)

Two placed Storm Kite flocks of four (10312), groups 150/151, occupy B2 and G7 over the grafting yards.
Actor indices 48–55 are appended before encounter-spawn generation; original actors are preserved. Their centres
are (-16000, 15500) and (16500, -16000), outside the great cannon's 16000-unit flying target range and clear of
the test emplacement. `build_out4.py` and `check_relief.py` were rerun; relief and cross-map height checks passed.
Terrain, minimap and lighting were not changed for these actors.
