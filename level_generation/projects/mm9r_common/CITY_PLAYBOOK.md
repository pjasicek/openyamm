# MM9 city to native BLV: playbook

Status: Sturmford City pilot built (2026-10-31/11-01); the recipe for the other six cities (Arslegard, Drangheim,
Frosgard, Guberland, Thjorgard, Thronheim City).

The user's decision (2026-10-31, [PLAN.md](../../../devdocs/mm9_rework/PLAN.md), Cities row): MM9's cities become
**BLVs open to the sky** instead of ODMs, for performance (the walk-in houses are sectors behind door and window
portals). A city is converted exactly like a dungeon ([DUNGEON_PLAYBOOK.md](DUNGEON_PLAYBOOK.md): read it first; every
step and gotcha there applies) plus the pieces below. Worked example: [`../mm9r_sturmfordcity/`](../mm9r_sturmfordcity/README.md).

## What differs from a dungeon

| Topic | Dungeon | City |
| --- | --- | --- |
| Hooks | `dungeon.Hooks` | `city.hooks.CityHooks` (`city/`), which adds the open air's portals, the sky faces and the open sky |
| Open air | rooms behind doorways and archway cuts | the districts' open air divided automatically (`city/structure.py`): a roof line, street cuts, top portals |
| Sky | skymarker faces drawn with a sky texture or the projected indoor sky | skymarker faces get `IndoorSky` and the scene opens to the sky: our Enhanced outdoor sky with the time of day behind them ([INDOOR_OPEN_SKY.md](../../../devdocs/INDOOR_OPEN_SKY.md)) |
| Minimap | MM9's painted map, or the line map by the Map style setting (2026-11-09) | MM9's painted city map only: no outline pass, `map: {painted_minimap: true}` |
| People | monsters from MM9 rows; a few NPCs | 30-60 townsfolk from the old import's NPC records with MM9 bodies; RUDEProps as posed decorations whose click opens their dialogue |
| Lighting | Cycles bake (deferred: classic lighting) | classic lighting (no bake), as the dungeons now ([MM9_LIGHTING_DECISION.md](../../../devdocs/mm9_rework/MM9_LIGHTING_DECISION.md)) |

## Steps

```sh
python3 level_generation/projects/mm9r_common/dungeon/survey.py <CITY>.dat --rules     # model rules draft
# overrides.yml: map (painted_minimap: true, monster_classes = the NPC classes), models, glass (tuning only, below),
#   textures (skymarker -> sky04, soundonly -> invisible), skip_user_portals (gates out of the city), seeds (shafts),
#   city: {street_top_lt, sky_texture, extra_cuts, half_steps: true}
python3 level_generation/projects/mm9r_<city>/convert.py --plan     # 6-8 minutes, 2 GB: work/rooms_*.png
# props: level_generation/props/mm9_<city>_claude/ (the Drangheim route; RUDEProps come out as kind: npc)
python3 level_generation/projects/mm9r_<city>/convert.py            # 8-10 minutes; installs into the review root
python3 level_generation/projects/mm9r_<city>/make_tour.py v01 [--original]   # then the tours, as the dungeons
python3 level_generation/projects/mm9r_<city>/make_scenarios.py     # doors, exits, shops, chests, scripted
```

**Windows exactly as MM9 has them (the user, 2026-11-07).** A window is see-through only where MM9 draws it
translucent: the face's surface has the Translucent flag (0x8), blended at its texture's alpha times the brush's
`Alpha`. A window MM9 draws opaque is opaque in ours, with no glass face or portal behind it (its texture alpha no
cut-out: the scene's `opaque_faces`). The converter decides this per face from MM9's data (`dungeon/rooms.py Glass`);
`overrides.yml glass` only tunes the flagged faces of a texture (opacity, tint, two_sided) and makes no face glass. The
see-through window boxes of 2026-11-01 (`boxes`) are withdrawn: Sturmford City's locked, empty houses showed their
clipped interiors through them. Details: [translucent faces](../../../devdocs/INDOOR_TRANSLUCENT_FACES.md).

The old ODM import needs a private hard-linked copy of `output/mm9_rework/assets_original` for its tours while other
sessions have unfinished actor tables (`cp -al`, then replace the broken `worlds/*/models/actors.yml` links with their
`git show HEAD:` text; Sturmford: `output/mm9_rework/sturmfordcity_original_root`).

## The open air (`city/structure.py`)

MM9 builds a city as walled districts (Sturmford: the docks and palace district, the temple square, the north town)
under sky shells (`skymarker` faces: a lid 500-800 LT over the streets, walls, and up-facing "sky floors" outside the
walls). The voxel air flood works unchanged at 16 LT (Sturmford: 8 620 x 1 612 x 8 471 LT, 29 M voxels, 1.9 GB, 110 s)
and the gates' and doors' portals already separate the districts and every walk-in interior. What is left is each
district's open air as one room. It is divided in three steps:

1. **The roof line** (`city: {street_top_lt}`): a horizontal barrier just under the lowest eaves along the streets
   (Sturmford 7 968 LT, 256 over the streets). Below it the street air, above it one "roof" room per district (roofs,
   upper walls, sky faces). A straight sight line from one street to another cannot pass through the roof room (it
   would cross the line's plane twice), so streets see each other only through the street cuts.
2. **Street cuts**, found automatically on the street air's plan at the roof line: on lines every `cut_spacing_lt`
   (1 280) along x and z, moved up to `cut_search_lt` (320) to the narrowest place, a cut where the street is a plain
   corridor (walls straight for `corridor_lt`, 128, on both sides) between `min_cut_width_lt` and `max_cut_width_lt`
   (48-768). Plazas and junctions are never cut. A cut is the street's cross-section from the ground to the roof line.
   Cuts whose sides stay one room (a loop cut once) are dropped; a cut that crosses other cuts or a junction is split
   into one portal per run with one pair of rooms (or the minor pair shares a barrier with no portal face: a hole,
   drawn as sky). `extra_cuts` add cuts by hand (Sturmford: 2), `no_cuts` keep the search off a place.
   Each cut's face is grown by a voxel at its open ends, down into the floor and up to the roof line's plane
   (`grow_cut_faces`): the walls it runs between stand up to a voxel past its air, and the strip left showed sky beside
   house corners (Thjorgard 2026-11-01).
   `street_box_lt: [[x0, z0], [x1, z1]]` (opt-in, Thjorgard City 2026-10-31) keeps the roof line and the streets
   to a plan box: open air outside it (a hillside rising through the roof line up to a castle) stays one room with
   the air over the roofs. Without it Thjorgard's slope cut the roof line into 1 300 rectangles; put the box edge in
   the town wall and a hand cut in each gate that crosses it below the roof line.
3. **Top portals**: each street room's footprint at the roof line, the portals up into the roof room. The plain cover
   is greedy rectangles (Sturmford 244); a rectangle with no air above it (a covered strip) stays a barrier but is no
   portal. Along diagonal streets that is a staircase of thin rectangles (Thjorgard 1 373, Thronheim 890, Drangheim
   679, Guberland 540), each a link of the roof room, and the renderer enters the roof room once per visible rectangle:
   Thjorgard hit the 256-node traversal cap at 3 of 12 street poses
   ([CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md)). **Set `merged_top_portals: true`** (all
   seven cities since 2026-11-01; opt-in, Lich Lab `--plan --scratch` byte-identical): each street room's rectangles
   are merged into few convex polygons (hulls of two pieces at a time, cheapest first), which may run on over cells
   solid at the roof line (walls, roofs, eaves; at most `top_portal_extension`, 0.5, times their own area more) and
   never over another room's air at layers h-1..h+2 (another street, a house reaching the roof line: the compiler
   makes the top portals "floor portals" of the roof room, so a house point over one would land in the roof room), a
   covered strip (eaves, arcades) where a sky face covers it (sky faces are not drawn, so the roof room would show
   through; over a drawn ceiling it may run on), cells outside `street_box_lt` or another top portal. Faces: convex, planar, at most 24 corners,
   expanded to whole native units so the rounded face still covers its polygon. The barrier stays the footprint (the
   rooms do not change; a street room with no open cell keeps its footprint as a barrier), and faces crossing the roof
   line are split exactly as with the plain cover (`split_boxes`, `rooms.crossing_portals`; a map-local cached copy of
   `crossing_portals` must honour them too, as Thjorgard's and Guberland's do), so **only the portal faces change**:
   check with a before/after tour (`devdocs/mm9_rework/city_street_cost/portal_counts.py`): no hole, the sectors
   drawn the same except where the plain cover hit the 256-node cap or reached a house's air (Arslegard's library).
   Results in CITY_STREET_COST.md "Result of proposal 3".

   The room over a roof-line cell is the air's at h + 2, or at h + 1 where eaves or an arcade leave air only there
   (2026-11-08: such a pocket opened nothing, and its ceiling, the roof room's, was missing from the street under it).
   `stats.uncovered_barrier_voxels` must be 0 (DUNGEON_PLAYBOOK "Package change: portal clipping").

4. **Half steps** for raised floors the party cannot step onto: see "Raised floors" below.

The street rooms, cut and top portals are in `build_report.json` `city`; `work/rooms_street.png` (overrides.yml
`plan_levels`) shows them. Faces crossing the roof line are split there (`split_minor_rooms`), so a facade is two faces.

## Raised floors

Settled on Sturmford City (2026-10-31). City agents: set `half_steps: true` in overrides.yml's `city` block, read the
audit's unreachable regions as below, and probe what is left.

**Step rules (native units).**

| Who | Steps up | Where |
| --- | --- | --- |
| Our party | **50**: a floor at most 50 over the feet, found under the centre or 37 ahead (the radius); a wall whose top is at most 50 over the feet is no obstacle | `game/indoor/IndoorMovementController.cpp` `MaximumRise` (OpenYAMM's own rule) |
| Our monsters | one move 50 (same controller); the path planner 40 per 40-unit step | `IndoorWorldRuntime.cpp` `stepHeight` |
| Original MM8 party | about 40: a lower collision sphere of radius 37 at the feet, the floor query from the feet + 40, a floor more than 128 up refused | `MM8-Rel.exe` 0x473a15-0x473a3c |
| MM9's player | 40-48 LT = 102-123 | (the dungeon audits) |

**What a city's "raised floors" are.** The audit (`dungeon/audit.py`) lists every floor monsters cannot climb onto as
unreachable; it does not know whether anyone can stand there. Sturmford's 18 were, one by one (`faces` and `floors`
near each, then forward walks):

- **Building plinths** (6): the base box under a house, 41 (16 LT) or 61 (24 LT) over the street, with the house's
  walls standing on its edge or 11-51 units behind it (the "41 plaza platforms" and the "61 strips" of the two
  north streets). Its top polygon runs on under the house, which is where the region's area comes
  from. Nobody stands there, in MM9 either. Walking into such a front, the party stops at the riser (61) or steps
  onto the ledge and bobs 10 units against the wall (41).
- **The inside of a solid block** (2: the keep, the "61 strips" along the palace ring's west side): walls on every
  side.
- **Counters** 103-113 and the tavern's back bar (112): stay unclimbable.
- **Table hulls** (the tavern's "booths"): MM9's invisible boxes of 48 and then 39; the party climbs them, as MM9's
  player does.
- **A fountain basin** (49): water inside a rim 52 over the street.

None needs a step. **A raised floor needs a fix only when the party can stand on it**: a terrace, a stage, a
sidewalk with no wall at its edge.

**The fix: invisible half steps** (`city/hooks.py` `half_steps`, `city: {half_steps: true}`). For each edge of a flat
floor of at least 20 000 LT² that stands 50-66 over the floor beside it (not 41: the party steps that): an invisible
top at half the rise, 20 LT (51) deep, and its riser. The party climbs 30 + 31; the tread is longer than a monster
path step (40), so the planner can also climb it (not proven: no such floor in Sturmford). Only where the party can
stand: the raised floor goes on 32 LT (82) behind the edge, no wall crosses that way (one standing on the edge
counts) and none stands within 16 LT (41) of that point. No step where another floor of the same height lies beyond
the edge (a riser inside a building's floor). Sturmford: 1 step (2 faces, beside the top of a stair at (9874, 3203),
which the stair reaches anyway); without the standing test the same pass made 29 steps in front of plinths, which
would lift the party 30 against every house front.

- Proof: `tests/IndoorMovementRecoveryTests.cpp` "the party climbs a 61-unit terrace only over the city converter's
  invisible half step" (the same geometry: without it the party stops on the street, with it it walks onto the
  terrace at 61). On the map: with the standing test switched off, the north plinth's step lifts the party 30 and the
  house wall on the plinth's edge stops it (`../mm9r_sturmfordcity/work/probes/half_step_proof.yml`, scratch build only).
- After a build: `build_report.json` `stats.city_half_steps` lists each step (centre, length, native). Probe each one
  with a forward walk from the street and look at `walk_z_distance`.
- Forward-walk probes: `movement_segment` with `expect_stop` at the same yaw as `start`, or the camera turns during
  the walk (the pilot's first `step61.yml` probes turned 180 degrees and proved nothing), `loose_tolerance: true`, and
  read `walk_xy_distance` and `walk_z_distance` (`../mm9r_sturmfordcity/work/probes/raised_floors.yml`).
- A standable raised floor 67-127 over its street (MM9's player climbs up to 102-123) gets no automatic step: add an
  invisible ramp or steps by hand (DUNGEON_PLAYBOOK "invisible ramps") and probe it.
- Not chosen: a per-map party step in the scene. MM9's own step (102-123) would put the party on counters and table
  tops, and an engine change for the plinths gains nothing.

## Engine features

Built (opt-in per map, MM6-MM8 unchanged; unit tests 2 429 of 2 429; daylight and MM9's fog: "Daylight and fog"
below):

- **Open sky behind sky faces** (`sky: {mode: open, sky_texture}` in the scene, written by `CityHooks`): the sky faces
  are left out of the drawn faces and the Enhanced outdoor sky is drawn behind the scene with the game's time of day
  ([INDOOR_OPEN_SKY.md](../../../devdocs/INDOOR_OPEN_SKY.md)). It also suits the dungeons' sky faces (Dragon Stadium,
  Hall of the Gods, Lindisfarne, Chasm): add the block to their scenes when the user wants it.
- **Sky faces by the sky flag, not only by texture** (2026-11-08, `dungeon/source.py` `Source.sky_flagged_as_sky`, every
  map with a skymarker alias in overrides.yml `textures`). MM9 draws its sky box through any visible polygon with
  LithTech's sky flag (0x10), whatever its texture. The shared build gives those polygons the skymarker's texture
  before the hooks run, so they become sky faces (stat `sky_flagged_retextured`). Found when a player reported Thjorgard
  City's hillside: its box has sky on three sides, but the north side is one 5 000-unit `thjorcolumn` polygon
  carrying the flag, and it showed as a huge wall. The same rule covers Frosgard City's sky floor (`frosmountain3`),
  Dark Passageway's 4 small pieces and the regions' grass and terrain lids. Wizard's Lab's `Default` tower top and the
  regions' rule in `outdoor_blv.py` were earlier per-map copies of it. Inventa Storca and Yanmir's Fort carry flagged
  polygons (shaft walls, ice strips) but have no sky alias, so they keep their textures.
- **Painted minimap**: already in the engine (`IndoorWorldRuntime`: an indoor map with a catalog entry draws it
  instead of the line map). Every map keeps its entry (2026-11-09, DUNGEON_PLAYBOOK.md "Painted maps"); the
  converter's `map: {painted_minimap: true}` turns the compiler's outline pass off (`generate_outlines: false`), so
  the 7 000-outline save bitset no longer limits a city and the Map style setting cannot pick a line map there.

To build (specified, not in the pilot):

- **Weather in open-sky sectors.** A sector is open to the sky when it holds sky faces or reaches one through portals
  without a roof (precompute per sector at load: a sector with an `IndoorSky` face, plus the street rooms under the
  roof room by their top portals). Rain and snow particles spawn only over those sectors' floors (the outdoor weather's
  emitter, clipped to the sectors' footprints), never inside a house; the sky follows the weather ladder
  (`SkyInputs.raining/snowing`) and wet surfaces only on faces of open sectors. Scene opt-in: `sky: {weather: <map's
  weather table>}`.
- **"Open to the sky" for outdoor-only rules.** Rules that ask "is this an outdoor map" (Meteor Shower, Starburst, Fly
  and Fleet Foot, Town Portal's outdoor checks) should ask "is the party's sector open to the sky" on an open-sky BLV.
- **Vertex indices over 65 535.** Not needed for Sturmford (21 234 vertices); if a bigger city needs it: widen
  `IndoorMapData` indices to 32 bits in memory and add an extended BLV variant written only by our compiler.

## Daylight and fog

Settled 2026-10-31 on Thjorgard and Sturmford City (proof: each project's `review/dl_compare_<time>.jpg`, old ODM |
BLV before | BLV after at 06:30, 12:00, 19:30, 23:30; Frosgard City too); rolled out to Frosgard, Thronheim and
Guberland City the same night with the street-light and sky-fog opt-ins below (`review/dl2_compare_<time>.jpg`).
**City agents: set these and rerun `convert.py` (the BLV's geometry does not change; its light colours and the scene
do):**

```yaml
map:
  fog: lithtech              # MM9's own fog model, and the WeatherMan's night fog where MM9 has one
  bright_scale_lights: true  # BLV light colour x MM9's BrightScale, as MM9's lightmaps ("Street lights" below)
  sky_fog: true              # only where MM9's fog covers its sky box (Frosgard City; see the table in INDOOR_FOG.md)
city:
  daylight: true             # sun and sky light on the sectors open to the sky, from MM9's data
```

What was wrong, and what these do:

- **Dark streets.** A BLV street had only the sector ambient (level 20, 0.35) and lamps. MM9's city lightmaps hold its
  WorldInfo AmbientLight in shade (Thjorgard 82, Sturmford 66; ~0.3, so our ambient was right) and **saturate at 255 on
  nearly every unshadowed face turned toward its StaticSunLight** (a fixed sun about 60 degrees up). Half the street
  was missing its sun. Sturmford looked closer only because its BLV street lights were written at full strength (MM9's
  `BrightScale` 0.2-0.75 ignored): its lamp-lit facades glared yellow-white (fixed: "Street lights and BrightScale").
- **Daylight** (`daylight` scene block, [INDOOR_OPEN_SKY.md](../../../devdocs/INDOOR_OPEN_SKY.md) "Daylight"): the
  sectors open to the sky (the sky shell's rooms and the street rooms under the roof line; houses stay closed, also with
  a skylight) take MM9's ambient plus its sun from the StaticSunLight's direction with a steep response (gain 4), at most
  1, by the time of day (noon full, dusk dimmer and warm, night at MM9's NightLightScale tint, blue-grey ~0.18). Models,
  decorations and townsfolk in the open take the same light. Interiors are unchanged (tavern, library: identical before
  and after at every hour). No shadows: a sunlit face is lit even where a house would shade it.
- **Haze.** Thjorgard's grey `Fog0` (25-4 500 LT) is MM9's own daytime fog, and the units were right (LT x 2.56).
  It read far denser because the dark streets made the grey fog brighter than the scene. MM9 fogs by view depth and in
  two passes (texture to the fog colour, lightmap to a second colour, so the world fades to ~63 grey, not 127):
  `model: lithtech`. With daylight it reads as a light haze. MM9 switches to black `Fog1` at night (WeatherMan
  `TurnOffAtNight`): the scene's `night` state, mixed in around 21:00-21:40.
- **Frosgard City is that foggy in MM9** (EnableFog, grey 1-2 000 LT, FarZ 2 500, no night switch). It has no
  StaticSunLight: daylight takes the sky's sun.
- **The sky in fog** (`map: {sky_fog: true}`, 2026-10-31; [INDOOR_FOG.md](../../../devdocs/INDOOR_FOG.md) "The sky in
  fog"). Our clear blue sky behind Frosgard's dark-grey fogged houses read wrong. MM9 fogs its sky box whenever its fog
  is on, from the fog state's `SkyFogNearZ`; the box (128 LT, the sky camera within 10 % of its centre) is always deeper
  than that in Frosgard (48), so MM9 draws the whole sky in the fog colour, 127 grey, day and night. (The
  WorldProperties `SkyFog` flag is read by nothing; MM9's client also copies SkyFogNearZ into SkyFogFarZ.) The scene's
  fog gets `sky: 1` per state where that holds, and the open sky is drawn in the fog colour by that share (an engine
  opt-in; the sky state lerps its gradient and clouds to the colour and fades sun, moon, stars and cloud layers).
  **Which cities by their DAT:** Frosgard (set); Thjorgard and Drangheim City would be grey by day under `Fog0`
  (SkyFogNearZ 0) and clear at night under `Fog1` (99 999): not set, the orchestrator's call (it changes their accepted
  noon look); Thronheim only under its scripted `Foggy` weather (not carried); Sturmford, Guberland, Arslegard none.
- **Night fog by the daylight** (scene fog `follow_daylight`, 2026-11-01; INDOOR_FOG.md "Fog by the daylight"). MM9
  holds its light and its fog at every hour, our daylight darkens the streets at night, so Frosgard's 127 grey fog and
  sky stood light over dark streets. The converter now adds `follow_daylight: true` to the fog of every city with
  `city: {daylight: true}` and fog (`city/hooks.py`; nothing to set): the fog colour, and so a fogged sky, is scaled per
  channel by the open air's light over its noon light (1 at noon; Frosgard at 23:30 (27, 29, 39)). Thjorgard and
  Drangheim keep their black night fog; only their grey evening fog darkens. Rebuilt: Frosgard, Thjorgard, Drangheim
  (`review/fog_night_1101_compare.jpg` in Frosgard and Thjorgard: noon identical, night dark).
- **MM9's world fog is the distance from the eye** (found on the way; INDOOR_FOG.md "Correction"): `d3d.ren`'s
  view-depth fog function is the sky's; the world uses range fog unless the `TableFog` cvar is on (default off). Our
  `model: lithtech` uses the view depth; not changed (an engine decision; small: the screen's edges fog a little less
  than MM9's).

Check after the rebuild: the scene has `daylight` (with `sun_direction` when the DAT has a StaticSunLight) and, where
MM9 has fog, `fog.model: lithtech`; a day/night sheet (`time:` per tour shot) shows lit streets at noon, unchanged
interiors and dark streets at 23:30. `daylight_fog_20261031/compare_tour.py` writes such tours from a city's existing
one, runs them one view per game run (`--folder` for before / after) and makes the old ODM | before | after sheet
(`write`, `run`, `sheet`). One view per run is no longer needed (below).

**Long tours no longer end in the death video (fixed 2026-11-01).** Tours of 8+ views on the city BLVs (Frosgard,
Thronheim, Guberland, Thjorgard, Sturmford) ended in the party-defeat video, at full HP. The cause was the tour, not the
cities: the indoor renderer ran its own simulation step (game clock, timers, face triggers, MM9 positioned transitions)
while the tour held gameplay, so the clock crept past each shot's `time:` during its settle (half a game minute per
second), and the next shot at the same time moved the clock forward a whole day. After four such days without rest, the
ordinary days-without-rest rule (`Party::updateDaysWithoutRest`, as in MM6-MM8) killed the party (Dead with full HP: no
member can act, so the defeat video plays). The old ODM imports have no such step, so their clocks stayed put. A player
cannot get there: real days pass only by playing, resting resets the count, and the debug clock is the tour's and the
console's. Fix (engine, debug path only): the tour holds the indoor clock too (`IndoorRenderer::setWorldTimeHeld`: doors
and lifts keep moving, as in turn-based mode), and a tour's clock jump does not count as days without rest
(tools/RUN_GAME.md). The hold should also end the reported drift "into another map" (a positioned transition firing
under a held pose; not reproduced). Proof: Frosgard 16 views and 32 views (8 views x 06:30/12:00/19:30/23:30, eight
dawns) and Thronheim 16 views end alive with the new binary; the old binary plays the death video on the same tours
(ledger "2026-11-01").

## Street lights and BrightScale

Settled 2026-10-31 (`map: {bright_scale_lights: true}`, `dungeon/lights.py`; opt-in, Lich Lab scratch build
byte-identical with it off). Set in all seven cities (Drangheim and Arslegard City last, rebuilt 2026-11-01).

- **What BrightScale is.** A `Light`'s strength in MM9's *lightmap bake*: the preprocessor reads it (`Processor.exe`,
  both Lith21 and Lith22 tools) and lights the lightmaps with `LightColor x BrightScale` (LithTech `LightMapMaker`:
  `m_InnerColor * m_BrightScale`; a negative one subtracts). The runtime never reads it (absent from `lithtech.exe`,
  `d3d.ren`, `cshell.dll`): models get the full colour (MM9_RENDER_LIGHTING_RE.md).
- **Measured on MM9's own lightmaps** (`daylight_fog_20261031/brightscale_lightmaps.py`, output in
  `brightscale_lightmaps.txt`): for every Light whose reach no other Light shares, its texels' rise over the ambient
  divided by colour x N.L x (1 - d/r) follows BrightScale: Bathhouse 0.33 / 0.50 / 0.72 / 0.89 / 0.97 at BrightScale
  0.3 / 0.4 / 0.5 / 0.7 / 0.75; Verhoffin 0.34 / 0.54 / 1.16 at 0.3 / 0.5 / 0.8; Sturmford City 0.33 / 1.05 / 1.92 at
  0.3 / 0.75 / 1.0 (correlation 0.8; the absolute gain depends on the assumed falloff, the proportion does not).
- **The fix.** A BLV light lights our faces as the lightmap lit MM9's, so the opt-in writes the BLV colour as
  `LightColor x BrightScale` (rounded, 0..255). Cities: Sturmford 123 of 151 kept lights change (x 0.2-0.85), Thjorgard
  59 of 160 (x 0.6-0.8), Frosgard 26 of 38, Thronheim 29 of 48, Guberland 37 of 51, Drangheim 47 of 54 (x 0.3-0.8,
  median 0.6), Arslegard 29 of 55 (x 0.6-0.8).
- **Result.** Sturmford's palace front and north lane lose the yellow-white glare and read like the old import, at
  noon and at night (`../mm9r_sturmfordcity/review/bs_compare_<time>.jpg`, old ODM | before | after); the palace
  ring north keeps a warmer wash on its west wall (its lights are BrightScale 0.85-1.0: what is left is our falloff,
  not the scale). Thjorgard barely changes (most of its lights are 1.0).
- **Models.** Under classic lighting the same BLV lights also light decorations and actors, which MM9 lit at full
  colour; with `model_lighting` a map sets `light_scale` to about 1 / its typical BrightScale (INDOOR_MODEL_LIGHTING.md).

**The MM9 dungeons use the same light writer; they were not rebuilt.** Twelve maps write their lights through it without
a BrightScale step of their own; the other twelve already multiply BrightScale in their `convert.py` (Ruined Temple,
Bathhouse, Thjorad Mine, Yanmir's Fort, Beethoven, Dark Passageway, Dragon Stadium, Connecting Tunnels, Dungeon of
Secrets, Tasar Academy, Training Hall, Thousand Terrors) and must **not** opt in (it would apply twice). With the opt-in
the twelve would change 1 342 of 1 377 kept lights:

| Dungeon (shared writer only) | Kept lights | Changed | Median colour factor | Range |
| --- | --: | --: | --: | --- |
| Anskram Keep | 112 | 112 | 0.30 | 0.25-0.50 |
| Chasm of the Dead (model lighting) | 89 | 89 | 0.60 | 0.30-0.60 |
| Dook's Castle (baked) | 156 | 156 | 0.70 | 0.20-0.80 |
| Drangheim Prison (model lighting) | 125 | 125 | 0.40 | 0.20-0.80 |
| Hall of the Gods | 34 | 30 | 0.75 | 0.33-1.00 |
| Inventa Storca | 71 | 71 | 0.30 | 0.20-1.22 (2 lights at BrightScale 2, clamped at 255) |
| Klusos House | 36 | 33 | 0.60 | 0.60-1.00 |
| Lich Lab (model lighting) | 417 | 391 | 0.60 | 0.30-1.00 |
| Lindisfarne Monastery | 106 | 106 | 0.40 | 0.11-0.70 |
| Temple of Honk | 130 | 130 | 0.70 | 0.20-0.80 |
| The Arena (model lighting) | 16 | 16 | 0.60 | 0.30-0.60 |
| Verhoffin Ruins | 85 | 83 | 0.33 | 0.30-1.00 |

So their lamp light would fall to about a third (Anskram, Inventa Storca, Verhoffin) to three quarters. Caution before
adopting it there: Klusos House's real-MM9 shots matched the old path (full colour) within 0.96-1.02 in brightness
(INDOOR_MODEL_LIGHTING.md "Klusos House trial"), because our vertex lighting's falloff and the four-per-point light cap
differ from MM9's bake. A dungeon that opts in should compare its real-shot or old-import views first; Great Gate and
Isle of Ashes have no lights.

## Known limits and choices (pilot)

- Townsfolk stand where MM9 placed them (no wander rails, schedules or following); animals wander. Sturmford City
  (2026-11-07) lets the townsfolk on NPCBase.inc's own aimless wander walk and chat (`convert.py` `wanders()`);
  the other cities still place every townsperson immobile.
- RUDEProps (posed people: innkeeper, Ludwig, Bjarni) are decorations: their dialogue opens on a click and their
  scripts' exit parts run on the next map poll (the world does not run while a dialogue is open). Sturmford City
  (2026-11-07) makes them actors looping their MM9 pose through the shared `rude_props.py` (row by model and skin,
  pose by script, `evt.PlayActorClip` and `evt.FaceActorTo` in the load handler, use and exit hooks); the other maps
  should move to it.
- MM9's breakable windows and the hire keys (Tesar 451, Ake 454) are not wired (no native breakable glass; MM9's hire
  service grants the keys implicitly).
- Missing audio (cinema voices, town portal vanish sounds) is noted in the city's README.
