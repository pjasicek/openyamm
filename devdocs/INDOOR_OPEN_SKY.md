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
- **Weather** (opt-in `weather`, below "Weather"). **Spells** follow the outdoor rules only on a map the world
  declares open (below "Spells"); the scene's sky alone changes no gameplay rule.
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
  lights and the dynamic lights on top; no shadows. Every other face gets zeros, which add nothing. Lightmapped faces
  take none: their lightmap's daylight page (a version 2 bake, [INDOOR_BAKED_LIGHTING.md](INDOOR_BAKED_LIGHTING.md)
  "Daylight pages", 2026-11-06) holds MM9's ambient and sun with its shadows, scaled by the same light now over at
  noon, while its lamps stay; a version 1 bake keeps noon light at every hour.
- **Open-air lights** (2026-11-07, user play-test: Ravensford at 03:00 drew its grass and cliffs as at noon). MM9 lit
  its regions' vertex-lit terrain and cliffs, and a few city squares, with huge white or sun-coloured Light objects
  high over the land (radius 750 LT and up, 1 920-14 080 native units: Ravensford 10 of 5 120, Sturmford 8 of 14 080,
  Thjorgard 21 sun-coloured); its lamps reach at most 700 LT (1 792; survey of the 12 regions and 7 cities). As static
  lights they baked into the vertex light at full strength at every hour (the terrain at night took about 1.0 under
  the 0.31 night ambient). On a map with daylight a map light at least `IndoorOpenAirLightMinRadius` (1 900) wide is
  the open air's (`indoorOpenAirLights`): the vertex bake keeps its share of each vertex's light in the colour's alpha
  (255 less the share; 255 on every other map), and the faces scale that share by `indoorOpenAirLightScale` (the
  sun's luminance now over at noon: 1 at noon, 0 once the sun has set; `u_indoorDaylight[0].w`,
  `indoorVertexLight` in the shader), on every face it reaches. Noon draws as before. The lighting frame scales the
  same lights by the same factor (`IndoorLightingFrameInput::openAirLightScale`, 2026-11-07), so the sprites,
  decorations and creatures that sample them darken too: before, Mountain Pass's and Sturmford's trees and monsters
  stayed noon-bright at midnight (`output/mm9_rework/last_two_20261107/compare_*.png`). The lightmaps' daylight split
  counts the same lights (MM9 `LightRadius` >= 750) as the open air's light, not lamps
  (`lightmap_transfer.py` `OPEN_AIR_LIGHT_RADIUS_LT`), so lightmapped structures under them darken too once their
  transfer is re-run. At 03:00 the regions now read about as dark as MM6 New Sorpigal (centre luma: Ravensford
  125 -> 39, Sturmford 55 -> 33, New Sorpigal 41); captures in `output/mm9_rework/region_night_20261107/`.
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
(`parseDaylightNode`), `IndoorRenderer` (`updateFrameDaylightAndFog`, `applyDaylightToLightingFrame`, `setFaceDaylight`,
`encodeBakedLightAbgr`), `IndoorStaticLighting` (`BakedStaticLightSource::openAir`).
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
- **Who.** Every MM9 map the dungeon converter builds (`dungeon/build.py` `scene_file`), except the outdoor regions
  (`outdoor_blv.py` writes `sides: both`, 2026-11-06): on their terrain the per-face cut lit the facets of a cliff
  tilted toward a light over its top and none of their neighbours (light and dark triangles, Isle of Ashes); MM9 lit
  those vertex-lit polygons by distance, and the regions' structures take MM9's lightmaps. No MM6-MM8 scene sets it.
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
- **Depth pre-pass** (2026-11-10, `IndoorRenderer::submitMainViewFaces`, `fs_indoor_textured_depth`): the main view
  takes the terrain draws' depth first (colour masked), then shades them testing that depth without writing it. An
  open-air BLV is often one sector, so portals cull none of it, and BLV faces have no back-face culling: Sturmford's
  terrain was shaded 1.73 times per pixel (the seabed under the shore, hills behind hills, their back faces), now
  once, and the clip plane's `discard` no longer turns off the early depth test. Water reflections keep the single
  pass. Same image. Sturmford (`_PERF_4`), 1600×900, frame GPU p50: Medium 986 → 737 µs, High 1590 → 1186 µs.
- **Grass** (`terrain: {grass: <decoration file>}`, 2026-11-04; New Sorpigal's whole meadow 2026-11-06; the terrain
  decorations setting): tufts of an outdoor map's plant library over the terrain faces, at the density of the grass
  layers (the material file's layers with a `meadow` strength, times it: grass 1.0, grass_patches 0.8; rock, snow,
  sand, dirt and cliffs grow none) read from the weight images. terrain_blend.py writes each region's file,
  `worlds/mm9/terrain_decorations/<stem>_blv.yml`: New Sorpigal's `oute3.yml` (seed, density, patches, tall grass,
  LOD, its first rule's meadow family) with the families file by its virtual path
  (`worlds/mm6/terrain_decorations/families_v2.yml`: atlas, flowers, verges, undergrowth, clumps, bushes, meadow) and
  the rule's tint from `mm9r_common/grass_tints.yml`, which `mm9r_common/grass_tint.py` fits from grass on/off
  captures so the mats stand to the ground as New Sorpigal's do (1.06 x its brightness; MEADOW.md: mats that do not
  match their ground read as dashes, and on MM9's grounds New Sorpigal's tint measured 0.57-0.87, rows of dark small
  bushes; the tint bound is 2.0). `TerrainDecorationData::scatterTerrainDecorationsOnSurface` (unit-tested) grows it as
  the tiles do: a 32-unit grid of the topmost terrain and of the clearance to every other drawn face (walls,
  buildings, docks, rocks) and the decorations; tall patches, wildflowers, verges (uncut grass beside the obstacles and
  where the grass ends at rock, paving or water), ferns round the trees (`mm9v_*tree*` rows), the low bushes
  (`TerrainBushSet`, drawn with the decorations' open-sky light), no plants under a water volume's surface (the
  seabeds). The meadow field (`buildTerrainSurfaceMeadow`: the outdoor maps' dry crests and lush hollows and shores,
  from the terrain's heights at the grid corners and the water volumes) tints the terrain's grass layers and the
  grass. The terrain faces take the grass's far colour and the shade under it from its foliage map
  (`terrainFoliageAlbedo` in terrain_material_layers.sh, shared with the outdoor terrain). No stones; no overhead fade
  (no flying). The rank quadtree LOD and the renderer are the outdoor maps'; the scene's fog or sky haze, no effect
  lights. Built once on first draw. A region whose theme has no meadow sets `terrain: {grass: none}` in its
  overrides.yml: the scene gets no `grass` and terrain_blend.py removes the region's file, so the map grows no
  plants whatever the setting (the Isle of Ashes, 2026-11-09).
- **Grass light** (`IndoorRenderer::renderTerrainGrass`, 2026-11-09): one brightness that follows the flat terrain
  through the day, the outdoor grass's noon light (0.85, the outdoor shader's cap) times the terrain's light now over
  its light at noon. The terrain's light is the faces' daylight with the normal up and the terrain faces' mean vertex
  light (`m_terrainLampLight`, `m_terrainOpenAirLight`, from `rebuildAllTexturedBatches`) with its open-air share by
  the hour. It goes in as the grass shader's ambient with no sun direction. Before, the sun went through the outdoor
  shader's sun term with the gain multiplying the sun's strength, so the grass sat at the cap until dusk while the
  ground darkened through the afternoon (user, Sturmford at 18:10: the grass three times the ground, about 1.5 at
  noon). The fixed-pose sweep at Sturmford now holds 1.42-1.47 from 07:00 to 18:10 (1.69 at 20:00). The grass is one
  brightness map-wide, so a place whose ground has less of MM9's open-air light than the mean reads brighter grass
  than its ground at every hour; per-tuft light would need the grass instances to carry it.
- **Smooth surface** (`IndoorTerrainSurface`): a point's normal averages the terrain triangles within 96 units with a
  falloff (the same on both sides of an edge), leaving creases over about 70 degrees; steepness averages over 192.
- **Data** (`level_generation/projects/mm9r_common/terrain_blend.py`, run by the project's `convert.py` after the
  install): `overrides.yml terrain: {materials: {<MM9 texture stem>: <world material>}, slope: <material>}`; it
  rasterises those faces from above (the topmost wins) into weights softened over the world's `edge_softness`, and
  each material's tint is the mean colour of the MM9 textures it replaces against the library material's (no channel
  lifted above the brightness ratio: a blue lift turned the grass's soil lilac). World materials:
  `mm9r_common/terrain_materials_world.yml` (`cliff_layered`: MM9's layered sandstone).
- **Faces under the terrain** (`terrain: {exclude_faces: [...]}`, 2026-11-06): a floor face with a terrain texture
  128 units or more under the terrain over it, on a polygon MM9 lightmapped (a tunnel's floor strip, the Isle of
  Ashes' ashdirt3 seams under the mountain), draws as an ordinary face: its texture and its lightmap
  (`dungeon/lighting.py` charts it with `bake_indoor.py --keep-faces`). As terrain it took the mountain top's rock
  from the weights and the open sky's daylight. `terrain_blend.py` `covered_faces`, `lightmapped_in_mm9`.
- Not yet: specular highlights and sun shadows on the terrain faces; the Isle of Ashes seabed (`ashfloorsea`) stays textured under the water.

## Weather

`sky: {mode: open, weather: rain | snow | rain_and_snow}` (2026-11-04; MM9's outdoor regions as BLVs,
devdocs/mm9_rework/OUTDOOR_BLV_ALL.md): the outdoor maps' weather over the open sky, from the same parts
(level_generation/lighting/WEATHER_PLAN.md): `GameDataLoader::applyOpenSkyWeatherToSelectedMap` gives the map a weather
profile (weather.yml's rules; its chances by map file, `maps: {<stem>.blv: ...}`, else the global ones; the scene says
which of rain and snow it can roll), and `IndoorOpenSkyWeather` (owned by IndoorRenderer) samples the rolls at the game
time (`sampleRolledWeather`, wetness once per game minute), fades them (`WeatherPresentation`, snapping on a clock jump
of over 30 minutes), drives the sky (`SkyInputs` raining, snowing, precipitation, lightning), the rain rings on water,
the rain and thunder sounds (`WeatherAudio`) and the rain and snow (`WeatherRenderer`, translucent view).

- **Where it falls: the roof map** (2026-11-06). At load the map's drawn surfaces seen from the sky (every face but
  its sky faces, portals and invisible faces) are rasterised into a grid of 64-unit cells (at most 1024 a side: a BLV's
  int16 frame), each holding the height of the highest surface over it (`buildIndoorWeatherRoofMap`,
  `game/render/WeatherRoofMap`). `WeatherRenderer::setRoofMap` uploads it as an R32F texture and the weather vertex
  shader drops every drop or flake below it: rain stops at roofs, bridges and the ground over tunnels, and is seen
  through doors and windows but never inside. Outdoor maps pass no roof map and are unchanged. A GPU that cannot read
  an R32F texture in the vertex shader falls back to the old rule (weather only with the camera in a sector holding
  sky faces). Not covered: 3D models (market awnings, trees) do not shelter.
- **Light in fog** (2026-11-10). The drops and flakes take the outdoor maps' light (the sky's brightness, dimmed by
  cloud), but in a scene's fog they are seen through its colour, which MM9 keeps brighter than its sky and which does
  not dim with cloud: Frosgard City's snow fell as dark specks through its grey fog at every hour and Sturmford's rain
  as dark streaks. `IndoorOpenSkyWeather::render` takes the frame's fog colour and lifts the light to at least 1.3
  times it (`HazeLight`, so the default rain colour is about as bright as the haze, snow brighter and ash darker);
  lightning adds on top. Without fog the light is unchanged.
- **Sound.** The camera under the roof map (more than 16 units below it: a house, a tunnel) hears the storm muffled
  (`CoveredWeatherAudibility`, 0.3 of the rain and wind loops, thunder at its square root), fading over 0.35 s as it
  walks through a door; under water nothing; under cover the distant rain curtain is not drawn either.
- **Thunder only in a rainstorm.** Strikes come only from rain at the storm threshold (weather.yml, `WeatherPresentation`);
  the console's forced rain sets the storm the same way. MM9's own placed thunder recordings (AmbientSound objects:
  Sturmford 13, Thjorgard 14, the Afterworld 7, short waits) used to play in any weather, which was the "thunder
  without rain" (2026-11-06); the converter now leaves them out of a scene with weather
  (`city/hooks.py apply_weather`), the storms playing the same recordings with their lightning.
- **MM9's own weather.** MM9's WeatherMan objects (12, in 11 maps) switch only fog (their Rain, Snow, Lightning, Clouds
  and AmbientSound properties are empty in every map). Its precipitation is the Rain and Snow VolumeBrush classes
  (object.lto strings `Rain`, `Snow`, `RainProperties`, `Rate`, `Velocity`, `ViewDist`; cshell `RainRate`,
  `SnowRate`), on from the start and never switched: Sturmford's one Rain brush covers the region (Rate 256),
  Frosgard's four Snow brushes its valley (Rate 100), Frosgard City's 31 its streets between the houses (Rate 200).
  So MM9 kept snow out of houses by where it placed the brushes, not by a roof test. weather.yml's `always` gives
  those three maps that weather all the time; MM9 rains or snows nowhere else, and the rest roll (the user's decision:
  weather on every region, the Afterworld, the Isle of Ashes and the cities, `city: {weather}` in each city's
  overrides.yml).
- **Fog days** (2026-11-09, the user's choice: often in Sturmford and Drangheim, never in Guberland, seldom
  elsewhere). weather.yml `maps: {<stem>.blv: {fog: [small, average, dense]}}` gives the daily chances (percent) and
  `open_sky_fog` each level's linear fade `[near, far]`. `rollDailyFog` rolls a fog day from 3 am (as the outdoor
  maps' daily fog) on its own random stream, so it never changes the rain; `sampleOpenSkyFog` blends the new day's fog
  in over the hour after 3 am. `IndoorOpenSkyWeather` samples it with the weather, `updateFrameDaylightAndFog` pulls
  the outdoor view's fade in to it (never farther than the clear fade) and `applyToSky` hazes the sky
  (`SkyInputs::foggy`, `fogStrongDistance` = the far distance, as an outdoor fog day). Only outdoor-view skies take
  the closer fade; Frosgard City keeps MM9's own fog and lists no chances. Chances: Sturmford, Drangheim and their
  cities 20/15/10, Guberland and its city none, every other open-sky MM9 map 8/4/2.
- **Not yet:** splashes (no indoor floor query is handed to the renderer), the ladder fog and wet faces (the outdoor
  maps' `u_wetness` is not in the indoor face shaders).
- Without `weather` nothing is created; MM6-MM8 BLVs never have it. A scene `preset` with weather would fix the sky
  against it: the converter drops the preset when it writes `weather`.
- Console on such a map: `weather status` (rolled and shown weather, storm, the camera's cover and the sound's
  share, the fog), `weather rain|snow <0-1>`, `clear`, `auto`, `strike [near|middle|far]`,
  `fog none|small|average|dense|auto`. Tests: `tests/WeatherModelTests.cpp` ("always weather", "fog days",
  "weather roof map").

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
wood, stone, water), for the open country and, since 2026-11-08, the seven cities (`city/hooks.py` `CityHooks.scene`;
before that every city floor sounded as a stone hall). The surface is MM9's own surface type of the texture where it
has one (`dtx_surface_flag` in the map's material aliases: 10/11 wood, 12 stone, 13 earth, 14 grass, 16 liquid, 19
cloth, 21 snow; metal and glass as stone), else the file name's word; the name alone heard wooden floors and roofs as
stone. A city takes its block when it is next converted. Code: `IndoorMapData` `footstepSounds`, `findIndoorFootstepSound`; `IndoorSceneYml.cpp`
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

## Portals beside the camera

`portal_visibility: {near_reach: 96}` (opt-in, 2026-11-08; every converted MM9 map): a portal of the camera's sector
within this distance of the camera (of its plane and its bounds) that the view would drop, facing away or clipped off,
still opens the whole view into the sector behind it; a portal of a sector further in, within the same distance (a
camera at a corner where two portals meet sees the second edge-on), passes on the view that sector was entered with. The camera's sector is the one of the floor under it, and a
converter's rooms are voxels (MM9's: 41 units), so near a doorway a floor strip, a jamb or a wall may be the room's
across it: a party standing on it was taken for one in that room, and the room it stood in vanished (the MM9 portal
sweep, `tools/indoor_portal_sweep.py`, `level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md` "Package change:
portal clipping"). It only draws more: one room beside the camera. Without the key (every MM6-MM8 map) only MM8's rule
holds: 9 units of the plane, 16 of the bounds. Code: `IndoorMapData::portalNearReach`,
`IndoorPortalVisibilityInput::nearPortalReach`. Tests: "indoor portal visibility opens the whole view through a dropped
portal beside the camera". The debug console's `portals culling off` draws every sector with the whole view, for a
reference render of what culling hides.


## Spells

A world lists its BLVs that lie open to the sky in `world.yml` (`openAirMaps: [isleofashes.blv, ...]`, MM9's regions
and cities, 2026-11-09); every other BLV, and every MM6-MM8 map, keeps the indoor rules. On a listed map the spells
follow the outdoor rules: Meteor Shower, Starburst, Death Blossom, Sunray and Armageddon work, Inferno and Prismatic
Light do not ("Can't cast Inferno outdoors!"), and every monster keeps its Meteor Shower (indoors only an
`indoor_meteor_shower` one does). Fly stays out: it needs an outdoor map's flight (MM9 casts Fleet Foot in its slot).

- **How they fall.** Meteor Shower's and Starburst's shots come down on their landing points, each from as high up to
  its own height as the room leaves clear above where it lands (`IndoorWorldRuntime::spawnIndoorFallingShots`, shared
  with the monsters' Meteor Shower); under a low sky lid they start just under it. Death Blossom bursts into its falling
  shards where it strikes, as outdoors (`spawnIndoorDeathBlossomFallout`).
- **Armageddon.** The shared spell (`game/gameplay/ArmageddonSpell.h`, also the outdoor maps'): meteors around the party
  on the floor under each, a strike on each nearby actor, then every monster on the map and the party take the damage.
  Indoors the quake is the shared camera shake (`CameraShake`), and there is no red flash (the indoor view has no
  screen overlay). Its state is saved with the indoor map (save version 170).

Code: `WorldManifest::openAirMaps`, `MapStats::applyOpenAirMaps`, `MapStatsEntry::openAir`,
`IGameplayWorldRuntime::isOpenAirMap` (outdoor: not enclosed), `PartySpellSystem.cpp` `spellWorldAvailabilityFailure`.
Tests: "party spell backend gives a map open to the sky the outdoor spell gates".

## Monster wakes

`actor_detection: {wakes: none}` (opt-out, 2026-11-05; every MM9 outdoor region converted by
`level_generation/projects/mm9r_common/outdoor_blv.py`): a monster that notices the party, or is hit by it, wakes none
of its neighbours. Without the key (`wakes: neighbours`, every MM6-MM8 map and MM9's dungeons) it wakes every unaware
hostile monster within 128 that it can see (re_mm8/INDOOR_EXPLORATION_AND_ACTIVATION.md, "OpenYAMM detection by
sight, hearing and neighbours"). Sight detection and faction alerts are unchanged. Code: `IndoorMapData`
`actorNeighbourWakes` and `IndoorWorldRuntime::wakeIndoorActorNeighbours`. Tests: "indoor actor detection" and
"indoor wakes stay off". These wakes concern MM6-MM8's detection; MM9 loop monsters ignore them. Theirs is the provoke
radius: `actor_detection: {provoke_radius: N}` sets this map's distance within which a provoking party hit on an MM9
monster provokes its awake friends, instead of the world's `actorAwareness` `mm9Provoke` radius
([MM9 monster AI plan](mm9_rework/MM9_MONSTER_AI_PLAN.md), "Awareness of the party").

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
