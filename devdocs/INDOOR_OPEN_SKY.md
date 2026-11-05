# Indoor maps open to the sky

An indoor map (BLV) can open to the sky: an MM9 city converted to a BLV (`level_generation/projects/mm9r_common/
CITY_PLAYBOOK.md`), whose streets lie under MM9's sky shell. Opt-in per map, by its scene; every other map, and every
MM6–MM8 BLV, draws exactly as before.

```yaml
sky: {mode: open, sky_texture: plansky3}     # sky_texture and preset are optional
```

- **What it does.** The map's sky faces (faces with `IndoorSky`, 0x00400000, usually set by the scene's
  `initial_state.face_attribute_overrides`) are left out of the drawn faces (`IndoorRenderer::rebuildAllTexturedBatches`,
  `indoorFaceShowsOpenSky`), and after the opaque scene (faces, decorations, creatures) the Enhanced outdoor sky
  (`level_generation/lighting/SKY_RENDERING.md`, `SkyRenderer`) is drawn at the far plane with the depth test
  (`IndoorRenderer::renderOpenSky`), so it shades only the pixels the scene left uncovered: where the sky faces are.
  It follows the game's time of day (`IndoorWorldRuntime::gameMinutes`): sun, moon, stars and the preset's day cycle.
- **Keys.** `mode: open` (the only mode). `sky_texture`: an original sky texture whose `legacy_<name>` preset the sky
  takes (`sky.yml` aliases; the old MM9 imports name `plansky3`), as an outdoor map's sky texture does; empty for the
  default. `preset`: a named preset that overrides the automatic choice. Unknown keys are refused.
- **What stays.** The sky faces remain faces: collision, missiles, picking and the bake (`bake_indoor.py` reads the BLV)
  are unchanged. The indoor fog, billboards and effects keep their flat fog (`u_skyFog` is reset after the sky pass).
  Without the block, sky faces keep the projected indoor sky (MM6–MM8 behaviour).
- **Fog.** The sky stays clear unless the scene's fog has `sky` (0..1): then that share of the sky is drawn in the
  fog colour, as MM9 draws its fogged sky box (Frosgard City; [INDOOR_FOG.md](INDOOR_FOG.md) "The sky in fog").
- **Weather** (opt-in `weather`, below "Weather"). **Not covered yet** (specified in the city playbook): outdoor-only
  rules asking "open to the sky".
- **Cost.** One full-screen triangle per frame behind the scene, shading only the uncovered pixels (the outdoor sky's
  cost); the sky renderer and its textures are created only for a map that opens to the sky.

Code: `game/indoor/IndoorOpenSky.h`, `game/maps/IndoorSceneYml.cpp` (`parseOpenSkyNode`), `IndoorMapData::openSky`,
`IndoorRenderer::renderOpenSky`. Tests: `tests/IndoorOpenSkyTests.cpp`.

## Outdoor view

`view: outdoor` (opt-in, 2026-11-01; the MM9 cities, with `preset: cloudy`): the map is seen as an outdoor map is.
Without the key (or `view: scene`) nothing changes; every MM6-MM8 BLV and every map without an open sky draws as before.

```yaml
sky: {mode: open, preset: cloudy, view: outdoor, view_distance_scale: 1.0}   # scale optional, (0, 16]
```

- **View distance.** The player's `view_distance` setting as outdoor maps resolve it (default 16 192) times
  `view_distance_scale` is the far plane of the main view and the picking rays (`cameraFarClipDistance`) and the portal
  walk's reach: a portal whose nearest visible point lies deeper is not entered (`IndoorPortalVisibilityInput::
  maxDistance`, trace reason `beyond_view_distance`), so the sectors, decorations and creatures behind it are not drawn.
- **Haze instead of the scene fog.** The scene's `fog` block is ignored. The fog is the outdoor maps' in clear weather:
  its own fade over the last eighth of the view distance into the sky's flat fog colour, plus the sky's aerial haze
  through the middle distance and the full fade into the sky between 55 % and 100 % of the view distance, each pixel
  taking the sky's colour in its direction (`sky_common.sh` `skyFogRatio`, `skyFogDisplayColor` from `u_skyFog`). The
  faces' fog programs (`fs_indoor_textured_lit.sc`), the 3D models (`fs_model.sc`, `ModelRenderLighting::skyFog`) and
  billboards share it; with `u_skyFog` zero (every other map) those calls return the flat fog unchanged. The sky state is
  the last drawn frame's, as the daylight tint's.
- **The cities** take `view_distance_scale: 0.5` (8 096 units at the default setting; the user's choice). Thjorgard's
  street views (shared test machine, still camera): 6-13 sectors instead of 6-17, 236-398 draw calls instead of
  248-442, most poses 1.1-1.3 times faster (s01 644 -> 813 FPS, s03 853 -> 1 109). At 6 000 they were 1.1-1.8 times
  faster (s22 853 -> 1 567), with the street ends noticeably hazed.
- **Water** fogs as the faces do each frame (`WaterRenderer::setIndoorFog` from the frame's fog). It used to keep the fog
  of the frame it was built in, before the sky's haze existed, and drew the Isle of Ashes' whole sea black under the
  outdoor view (2026-11-02).
- **Sky.** `preset` picks one of the outdoor maps' Enhanced presets (`cloudy`, `fair`, ...) with its day and night
  cycle (sun, moon, stars); it does not change with the daily weather.

Code: `IndoorOpenSky::outdoorView`, `IndoorRenderer` (`m_outdoorViewDistance`, `updateFrameDaylightAndFog`,
`cameraFarClipDistance`), `IndoorPortalVisibility.cpp`. Converter: `city: {sky_preset, outdoor_view}` (`city/hooks.py`).
Tests: `tests/IndoorOpenSkyTests.cpp` ("block parsing").

## Daylight

Sun and sky light on the sectors open to the sky, by the same game time as the sky (2026-10-31). Opt-in per map; a map
without the block (every MM6–MM8 map, every MM9 dungeon) renders exactly as before.

```yaml
daylight:
  ambient_rgb: [80, 80, 80]          # the open air in shade at noon (MM9 WorldInfo AmbientLight)
  sun_rgb: [255, 255, 255]           # the sun (MM9 StaticSunLight InnerColor x BrightScale)
  day_scale_rgb: [255, 255, 255]     # optional, 255: scale of both at noon (MM9 WorldProperties LightScale)
  night_scale_rgb: [134, 143, 168]   # optional, 255: at midnight (MM9 NightLightScale)
  sun_direction: [-0.433, -0.25, 0.866]   # optional: toward the sun, native axes (MM9's StaticSunLight); none = the sky's sun
  sun_gain: 4                        # optional, 1: how steeply faces take the sun, min(1, gain x N.L)
```

- **Which sectors.** Computed at load (`indoorOpenSkySectors`, `IndoorMapData.cpp`): a sector whose `IndoorSky` faces
  cover a quarter of its floor area or 10 M square units (the sky shell over a city's air), and every sector below one
  of them through a horizontal portal (the street rooms under the roof line). Doorways and windows are vertical, so the
  rooms behind them stay closed; a house with a skylight (Thjorgard City's library, 0.83 M) or a sliver of the shell stays
  closed. Thjorgard City 25 of 89 sectors, Sturmford City 28 of 63, Frosgard City its one open-air room.
- **The light** (`evaluateIndoorDaylight`, `IndoorDaylight.cpp`). Day weight `w` = the outdoor maps' ambient curve
  (1 at noon, 0 at midnight, 0.5 at 06:00 and 18:00). Scale = night scale to day scale by `w`. Ambient = `ambient_rgb` x
  scale, never under the darkest classic room (0.18). Sun = `sun_rgb` x scale x `w`, fading out as the sky's sun sets
  (`skyNightAmount`, the sky's own night measure). The sky's hue tints both as it tints the outdoor bake (half the sun
  disc colour, the ambient tint; last frame's sky).
- **Faces** (`fs_indoor_textured_lit.sc`, `u_indoorDaylight[3]`, `IndoorRenderer::setFaceDaylight`). An open sector's
  vertex bake leaves out the room ambient (`min_ambient_light_level`) and its faces take
  `min(ambient + sun x clamp(gain x N.L, 0, 1), 1)` (MM9's lightmaps clamp at 255) with the vertex bake of the static
  lights and the dynamic lights on top; no shadows. Every other face gets zeros, which add nothing; lightmapped faces
  get none.
- **Sprites** in an open sector take `luminance(ambient) + 0.5 x luminance(sun)` (at most 1) as their room light
  (`applyDaylightToLightingFrame`); a sprite takes its own sector's light out of its two samples instead of the
  frame's darkest.
- **Models** (decorations and creatures) in an open sector take the sun by direction (2026-11-04; before, the same
  single room light, which left the regions' trees flat and lime green): their own light keeps the ambient share
  (`indoorDaylightModelAmbient`; a decoration's sprite light less half the sun, its nearby lights kept) and the sun
  comes from the daylight's direction and colour with N.L and the leaves' translucency (`applyDaylightSun`: the batch
  sun of the decorations; a creature's own lighting), at exposure 1 like the faces: the decorations' exposure (1.8,
  which matches a model to its sprite in a dark room) pushed sunlit greens to lime in daylight. A decoration's light alpha (its sun) is 1
  only in an open sector, so models under a roof take none. No sun shadows indoors.
- **Why a fixed sun and a gain** (MM9 data). MM9's city lightmaps hold exactly the AmbientLight on every face turned away
  from the StaticSunLight (Thjorgard 82, Sturmford 66) and saturate at 255 on nearly every unshadowed face turned toward
  it, already from N.L 0.05-0.2. The Enhanced sky's sun passes almost through the zenith at noon, so it lit floors only
  and left every facade at the ambient; MM9's sun (60 degrees up) lights the facades. The converter writes the
  StaticSunLight's direction and gain 4; a map without a StaticSunLight (Frosgard City) takes the sky's sun.
- **MM9 itself does not change with the hour**: `d3d.ren` turns LightScale into an identity table
  (`MM9_RENDER_LIGHTING_RE.md`), so its lightmaps show noon light at midnight. Our nights use the authored night tint.
- **Fog by the daylight** (scene fog `follow_daylight: true`, 2026-11-01; [INDOOR_FOG.md](INDOOR_FOG.md)): the fog
  colour, and so a fogged sky, darkens with the open air's light (1 at noon), so a city's day fog no longer stands
  light grey over its dark night streets.
- **Cost.** One more vec4[3] uniform per face batch; per pixel one dot, clamp and min (zero on other maps).

Code: `game/indoor/IndoorDaylight.h/.cpp`, `IndoorMapData.cpp` (`indoorOpenSkySectors`), `IndoorSceneYml.cpp`
(`parseDaylightNode`), `IndoorRenderer` (`updateFrameDaylightAndFog`, `applyDaylightToLightingFrame`, `setFaceDaylight`).
Tests: `tests/IndoorOpenSkyTests.cpp` ("indoor daylight"). Converter: `dungeon/source.py` `Source.daylight`, written by
`city/hooks.py` with `city: {daylight: true}`. Review: CITY_PLAYBOOK "Daylight and fog".

## Static lights

```yaml
static_lights: {sides: front}   # default both: MM6-MM8's angle-free static light
```

- **Why** (2026-11-04, user: a lit patch on Thjorgard City's street wall at night with no lamp near). A static light
  bakes into the faces of the sectors it reaches (its own and those behind portals within its radius,
  `IndoorLightReach`), by distance only. A house's room lights reach its outer walls through its doorway, so the
  street side of the wall took the light of the room behind it. MM9 baked its lights with shadows, so they never did.
- **Front only.** A static light adds nothing to a face it stands more than `IndoorStaticLightBehindTolerance` (24
  units) behind (the face's plane, `computeFaceNormal`), at the vertex bake (`buildFaceTexturedMesh`'s per-face
  sources) and when the bake is refreshed (`refreshBakedStaticLighting`, per face of each batch). The tolerance keeps
  a lamp whose light is set just into the wall it hangs on. Not shadows: a light in front of a wall around a corner
  still reaches it. Dynamic lights already ignore faces turned away (`indoorFaceFacing`).
- **Who.** Every MM9 map the dungeon converter builds (`dungeon/build.py` `scene_file`). No MM6-MM8 scene sets it.
- **Lamp lights** (converter): a lamp, lantern or brazier with no MM9 Light of its own (props.json `light: null`;
  Thjorgard City's 39, Thronheim City's 35, Arslegard City's 29) gets a native light at its flame (`dungeon/content.py`
  `lamp_light`: the centre of the model's `Fire` cards, radius 512, warm (255, 230, 160)). MM9 lit these with the
  CandleProp's own dynamic light only (its warm spot around the lantern).

Code: `IndoorMapData::staticLightsFrontOnly`, `IndoorSceneYml.cpp` (`parseStaticLightsNode`), `IndoorRenderer.cpp`
(`staticLightFacePlane`, `staticLightBehindFace`). Test: `tests/IndoorOpenSkyTests.cpp` ("indoor static lights").

## Terrain

The ground of an open-air BLV (an outdoor MM9 region rebuilt as a BLV) is drawn like an outdoor map's terrain: blended
library ground materials (level_generation/terrain/materials/README.md) instead of MM9's textures (2026-11-02). MM9
mapped each terrain polygon on its own (a third of the Isle of Ashes cliff edges break the pattern), lit them flat
and never blended two textures; its blurry 1x art hid it, sharp textures show every seam.

```yaml
terrain:
  materials: isleofashes_blv.yml           # worlds/<world>/terrain_materials/, the outdoor material file format
  textures: [ashc08t3g2, ashro4zhnj, ...]  # the faces drawn as terrain
```

- **Materials** (`TerrainMaterialSet`, shared with `OutdoorTerrainMaterials`): the material file's library layers,
  weights over the 65 536-unit map frame (an outdoor map's: the BLV is in the same frame), macro noise and layer
  uniforms. `terrain_material_layers.sh` holds the blend both draw with (the two strongest layers by height, the slope
  layer on steep ground with side projections, the fringe noise across each transition).
- **Faces** (`fs_indoor_textured_lit`, `INDOOR_TERRAIN`; `IndoorRenderer::applyTerrainVertices`): a terrain face keeps
  its batch, visibility and vertex bake of the static lights but takes no lightmap; its vertices carry the smooth
  ground normal (in `gradientU`) and the slope layer's steepness. The daylight and the dynamic lights use that normal,
  so the light runs on across polygon edges. A face whose pixels can read one ground layer only (the outdoor mesh's
  test: one layer with weight in the weight texels its bounds reach, two more for the mips, and its vertices too
  gentle for the slope layer even with the macro noise) batches apart and draws with the `SINGLE_MATERIAL` programs
  (`IndoorRenderer::markSingleMaterialTerrainFaces`). Isle of Ashes, 1600×900, frame GPU time with the trilinear
  normal array (terrain README): 819 → 672 µs at the default camera over the cliff, 570 → 468 µs facing the sea.
- **Grass** (`terrain: {grass: <decoration file>}`, 2026-11-04; the terrain decorations setting): tufts of an outdoor
  map's plant library (outdoor_blv/terrain_blend.py default: New Sorpigal's `worlds/mm6/terrain_decorations/oute3.yml`,
  its first grass rule and families file) over the terrain faces, at the density of the grass layers (the material
  file's layers with a `meadow` strength, times it: grass 1.0, grass_patches 0.8) read from the weight images
  (`TerrainDecorationData::scatterTerrainDecorationsOnSurface`, unit-tested). The rank quadtree LOD and the renderer
  are the outdoor maps' (TerrainDecorationRenderer); lit by the open sky's daylight as one brightness, the scene's fog
  or sky haze, no effect lights. Built once on first draw. No stones, verges, undergrowth, meadow moisture or bushes
  (they read MM6-MM8 tiles), no far foliage tint on the ground. Sturmford: 603 000 tufts (nearly the whole region is
  grass; MM6-MM8 outdoor maps carry 97 000-150 000), about 5 % of the frame at the start view.
- **Smooth surface** (`IndoorTerrainSurface`): a point's normal averages the terrain triangles within 96 units with a
  falloff (the same on both sides of an edge), leaving creases over about 70 degrees; steepness averages over 192.
- **Data** (`level_generation/projects/mm9r_common/terrain_blend.py`, run by the project's `convert.py` after the
  install): `overrides.yml terrain: {materials: {<MM9 texture stem>: <world material>}, slope: <material>}`; it
  rasterises those faces from above (the topmost wins) into weights softened over the world's `edge_softness`, and
  each material's tint is the mean colour of the MM9 textures it replaces against the library material's (no channel
  lifted above the brightness ratio: a blue lift turned the grass's soil lilac). World materials:
  `mm9r_common/terrain_materials_world.yml` (`cliff_layered`: MM9's layered sandstone).
- Not yet: the meadow field (dry crests, lush hollows), grass decorations, specular highlights and sun shadows on the
  terrain faces; the Isle of Ashes seabed (`ashfloorsea`) stays textured under the water.

## Weather

`sky: {mode: open, weather: rain | snow | rain_and_snow}` (2026-11-04; MM9's outdoor regions as BLVs,
devdocs/mm9_rework/OUTDOOR_BLV_ALL.md): the outdoor maps' weather over the open sky, from the same parts
(level_generation/lighting/WEATHER_PLAN.md): `GameDataLoader::applyOpenSkyWeatherToSelectedMap` gives the map a weather
profile (weather.yml's rules; its chances by map file, `maps: {<stem>.blv: ...}`, else the global ones; the scene says
which of rain and snow it can roll), and `IndoorOpenSkyWeather` (owned by IndoorRenderer) samples the rolls at the game
time (`sampleRolledWeather`, wetness once per game minute), fades them (`WeatherPresentation`, snapping on a clock jump
of over 30 minutes), drives the sky (`SkyInputs` raining, snowing, precipitation, lightning), the rain rings on water,
the rain and thunder sounds (`WeatherAudio`) and the rain and snow (`WeatherRenderer`, translucent view).

- **Where.** The sectors open to the sky are those holding sky faces (an outdoor region's open-air room). The weather is
  drawn and heard while the camera is in one and out of the water; the sky follows the weather everywhere.
- **Not yet:** splashes (no indoor floor query is handed to the renderer), the ladder fog and wet faces (the outdoor
  maps' `u_wetness` is not in the indoor face shaders), particles kept out of covered parts of an open sector (the
  outdoor maps have no roof map either).
- Without `weather` nothing is created; MM6-MM8 BLVs never have it. A scene `preset` with weather would fix the sky
  against it: outdoor_blv.py drops the preset when it writes `weather`.

## Footsteps

`footstep_sounds` (opt-in, 2026-11-02; MM9 open-air maps): the walking and running sound by the texture of the floor
the party stands on, as outdoor maps choose theirs by terrain tile. Without the block, or on a texture it does not
list, every floor keeps the stone hall sound (every MM6-MM8 BLV).

```yaml
footstep_sounds:
  - {texture_names: [ashro4zhnj, mainakfoki], walk_sound_id: 93, run_sound_id: 54}   # grass (game SoundIds)
  - {texture_names: [ashw5wt0xi], walk_sound_id: 103, run_sound_id: 64}              # wood
```

An overlay's block replaces the base scene's. The converter writes it from the MM9 source texture behind each face
alias (`level_generation/projects/mm9r_common/footsteps.py`: grass, rough ground on terrain rock and cliffs, dirt,
wood, stone, water). Code: `IndoorMapData` `footstepSounds`, `findIndoorFootstepSound`; `IndoorSceneYml.cpp`
`parseFootstepSoundsNode`; `IndoorGameView::updateFootstepAudio` (running from `IndoorPartyRuntime::runningMovement`).
Tests: `tests/IndoorOpenSkyTests.cpp` ("indoor footstep sounds").

## Party movement

`party_movement: {steep_slopes: block}` (opt-in, 2026-11-02; MM9 open-air maps): the party climbs no floor steeper
than a monster can (normal z under 0.708, about 45 degrees): such a face is a wall to it and it slides off, as the
monsters do. Without the block (`climb`, every MM6-MM8 BLV) the party keeps the original rule and climbs any slope
(re_mm8/PARTY_SLOPE_CLIMBING.md, the Ogre Fortress' 64-degree ramp). MM9's terrain needs the block: its cliffs rise
over floors that run on under them, and the climbing party went up a cliff's plane and through the hill. The limit is
MM9's own (`devdocs/mm9_rework/MM9_PLAYER_SLOPE_RE.md`, 2026-11-02): its player walks up faces whose normal is at
least 0.7071 (45 degrees) and is stopped by steeper ones, slid down past 55.9 degrees; ours is 0.7077 (45.04 degrees),
so no per-map limit was added. MM9's step-up is 16.5 LT (42 native) against our 50. Code:
`IndoorMapData` `partySteepSlopesBlock`, `IndoorPartyRuntime` (the slope rule). Tests: "indoor party movement".

Three movement fixes for terrain converted to floors (MM9 open-air maps), shared by every BLV and covered by
`tests/IndoorMovementRecoveryTests.cpp`; the MM6-MM8 regressions (unit tests, the indoor suite,
`tests/scenarios/mm8_party_slopes.yml`) pass unchanged:

- **A floor edge the sweep meets is stepped onto at the face's height there**, not at its first vertex's: on a sloped
  face that vertex can lie 40 over the contact, and the party rose and fell back at seams ("walking over sloped
  terrain faces").
- **Early stepping onto the face ahead is for treads only** (both faces flat): on slopes the face ahead's height a
  radius away made a 3-5 unit sawtooth at every seam, seen as a rapid up-down ("crossing a crease").
- **A body under a steep face's surface collides with it**: the sweep's exemption for a body standing on a steep
  slope (cave floors) excused a body inside the face's outline below its surface too, which walked through cliffs
  ("under a steep slope's plane").

## Monster barriers

`actor_barriers: {faces: [face ids]}` (opt-in, 2026-11-02; MM9 open-air maps): walls for the monsters only. The listed
faces are invisible and untouchable, so the party, projectiles, line of sight, floor and ceiling queries, picking and
the path map ignore them as they ignore every untouchable face; the monsters' movement controller
(`IndoorWorldRuntime::actorMovementController`, `setBlockedByActorBarriers`) collides with them as walls. A scene
without the key (every MM6-MM8 BLV) builds no mask, and untouchable faces stay inert to everything.

The monsters' path map (`IndoorPathfindingBuilder`) takes the listed faces as solid walls too, so a monster plans
round a barrier instead of pressing against it; an unlisted untouchable face still blocks no path.

They are MM9's AIBarrier brushes, which MM9 places along bridges, ledges, pits and shores to keep its AI off the edges
(294 in 24 maps; the shared converter carries them into every converted map:
`level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md` "Monster barriers"). Without them skeletons crowding the party on
the Isle of Ashes' bridges were pushed off into the sea, where the steep shore kept them. A monster that is already
in the water (knocked back, spawned there) still cannot climb out. Code: `IndoorMapData` `actorBarrierFaceIds`,
`IndoorFaceSweepOptions::pActorBarrierFaceMask`. Tests: "indoor actor barriers", "monster-only walls", "indoor pathfinding builder blocks at the scene's monster-only
walls".

## Monster drops

`actor_movement: {drops: follow}` (opt-in, 2026-11-02; every converted MM9 map): monsters walk off ledges of any height
after their target and plan paths down them, as MM9's do: they keep their walk or run animation, fall and take no
damage, and never jump or climb up (`devdocs/mm9_rework/MM9_MONSTER_JUMP_RE.md`). MM9's designers kept them back with
AIBarrier brushes, the scene's monster barriers above. Without the key (`drops: guard`, every MM6-MM8 map) a monster
refuses any drop over 100 units (`IndoorActorMaxDropHeight`). Code: `IndoorMapData` `actorDropsFollow`, the path
object's drop height and the ledge guard in `IndoorWorldRuntime`. Tests: "indoor actor movement".


## Monster wakes

`actor_detection: {wakes: none}` (opt-out, 2026-11-05; every MM9 outdoor region converted by
`level_generation/projects/mm9r_common/outdoor_blv.py`): a monster that notices the party, or is hit by it, wakes none
of its neighbours. Without the key (`wakes: neighbours`, every MM6-MM8 map and MM9's dungeons) it wakes every unaware
hostile monster within 1024 that it can see (re_mm8/INDOOR_EXPLORATION_AND_ACTIVATION.md, "OpenYAMM detection by
sight, hearing and neighbours"). Sight detection and faction alerts are unchanged. Code: `IndoorMapData`
`actorNeighbourWakes` and `IndoorWorldRuntime::wakeIndoorActorNeighbours`. Tests: "indoor actor detection" and
"indoor wakes stay off".

## Swimming

`water_volumes` (opt-in, 2026-11-02; MM9 maps converted with `swim: true`, Verhoffin Ruins first): MM9's deep water,
swum and dived in as MM9 does. Without the block (every MM6-MM8 map, MAW, every MM9 map not converted again) no water
state, breath or swim step runs. The design, MM9's numbers and the deviations are in
[MM9_WATER_SWIMMING_DESIGN.md](mm9_rework/MM9_WATER_SWIMMING_DESIGN.md) ("Status"), the MM9 behaviour with addresses in
[MM9_WATER_SWIMMING_RE.md](mm9_rework/MM9_WATER_SWIMMING_RE.md).

```yaml
water_volumes:
  - id: BlueWater0                     # the DAT object
    liquid: water                      # water | lava
    pieces:                            # vertical prisms (native units): footprint, bed side and surface
      - {polygon: [[x, y], [x, y], [x, y], ...], bottom: -820, top: -453}
    tint: [0.0, 0.5, 0.7]              # optional: MM9's light scale (BlueWater by default)
    fog: {color_rgb: [0, 0, 0], near_distance: 1280, far_distance: 5120}   # optional: MM9 FogEnable
    current: [0, 0, 0]                 # optional, units per second
    mover_door_id: 12                  # optional: the door whose travel moves every piece's top
```

- **Party** (`IndoorPartyRuntime::stepInWater`, pure step in `game/indoor/IndoorWater.h`): the eye point (eye − 25.6,
  MM9's 10 LT) under water → swimming: gravity off, the velocity set from the keys each step (forward along the look
  direction with its pitch, Jump or Fly Up up, Fly Down down, 384 u/s; no key: sinks at 102 u/s). Eye out, body in, having
  been under → held at the surface (eye point 1 over the water); looking down while moving forward or Fly Down dives;
  Jump leaps out (704 u/s up, party gravity, air control 384/192). Feet on a floor → walking (wading, or on the bed with
  the eye under: Jump/Fly Up rises off it). Falling in is an ordinary fall until the eye goes under; landing in water
  takes no fall damage. Ladders are taken from the water.
- **Breath**: 15 s with the eye under, then every 2 s each member loses 1/6 of its maximum HP ("You are drowning!",
  `drown01/02.wav`); out of the water it refills at once; runtime only (full after a load). HUD: a thin bar above the
  party basebar while the eye is under (`GameplayUiRenderer`). Splash, out-of-water and MM9's `player/unwater2.wav` loop
  (`IndoorGameView::updateWaterAudio`).
- **Screen**: the frame times `mix(1, tint, 0.6)` while the eye is in a volume (`IndoorRenderer::renderWaterTint`); a
  volume with `fog` replaces the frame's fog (`updateFrameDaylightAndFog`). Bows, crossbows and thrown weapons are not
  fired with the eye under water (melee instead).
- **Monsters**: a monster whose Fly cell holds `S` (MM9's AISwimFly: Sea Monsters, the Spores, Fish) and that starts
  inside a volume flies in it and never leaves it (`refreshActorWaterVolumes`, the binding after its flying move);
  walkers in water move at half speed under the liquid's gravity 512 and sink at most 102 u/s, walking the bed.
- **Android**: the flight arrows show while swimming (`partySwimming`).

- **Reflections of the sky**: a map open to the sky draws its sky into each water reflection capture before the
  reflected faces (`IndoorRenderer::renderWaterReflections`). Without it the capture kept its black clear wherever
  the reflected view met no face, and the Isle of Ashes' sea turned black below the mirrored cliffs. Maps without an
  open sky (MM6-MM8) are unchanged.

Code: `game/indoor/IndoorWater.h/.cpp`, `IndoorSceneYml.cpp` (`parseWaterVolumesNode`), `IndoorMapData::waterVolumes`,
`IndoorPartyRuntime`, `IndoorRenderer`, `IndoorWorldRuntime`. Tests: `tests/IndoorWaterTests.cpp` ("indoor water"),
the scenario `water` assert (`tests/scenarios/README.md`), Verhoffin's `scenario_swim.yml`. Converter:
`level_generation/projects/mm9r_common/dungeon/water.py` (DUNGEON_PLAYBOOK "Water volumes and swimming").
