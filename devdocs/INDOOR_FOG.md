# Indoor fog (BLV)

A native indoor map may fade every world pixel into one colour between two distances from the eye. It is opt-in per map
through the scene file: a map without the block (every MM6–MM8 dungeon, Hesper's) renders exactly as before and pays
nothing. First user: MM9's Anskram Keep, whose `WorldProperties` set a black fog from 1 to 5000 LT.

## What MM9 has (all 45 DAT worlds)

| Source | What it is | Where | OpenYAMM |
| --- | --- | --- | --- |
| `WorldProperties` `EnableFog`, `FogColor`, `FogNearZ/FarZ` | fog for the whole map | 8 maps; indoors only Anskram Keep (black, 1–5000) | scene `fog` |
| `Fog` objects | **point controllers, not volumes**: no brush, just a fog state a `WeatherMan` fires (`FogOn`, `FogOff`, `TransitionTime`). `StartOn 1` makes one the map's fog from the start | 24 objects in 11 maps, list in [MM9 visual properties](mm9_rework/MM9_VISUAL_PROPERTIES.md) table C; `StartOn` in 6 | scene `fog` takes the `StartOn` state; a starting `WeatherMan` with `TurnOffAtNight` becomes the scene's `night` state (opt-in, `map: {fog: lithtech}`) |
| Water volumes' `FogEnable` | fog while the camera is in the volume: the only real regions | 15 volumes | none: the party cannot dive indoors yet |
| `VFog` volumetric fog | a height band | 0 maps | none |

The Lich Lab has none of these. Its "white mist" was our own view-distance fade in the reference shots
(MM9 visual properties, "Correction").

## Data: the scene's `fog`

```yaml
fog:
  color_rgb: [0, 0, 0]     # display colour, 0..255
  near_distance: 2.56      # native units from the eye: clear up to here
  far_distance: 12800      # all fog from here on
```

Top level of `<map>.scene.yml` (`IndoorSceneYml`: `parseIndoorSceneFog`); a scene overlay's `fog` replaces the base's;
the editor's scene writer round-trips it. A missing key, a colour outside 0–255 or anything but `0 <= near < far` fails
the scene's load. The names are those of the outdoor authored fog (`weather.authored_fog`). The map keeps it as
`IndoorMapData::fog` (`game/indoor/IndoorFog.h`), map data, never saved.

**Regions.** The block is a map so that a later `regions:` key can sit beside the map-wide values, each with a box or
sector list and its own colour and distances. It is not built: the `Fog` objects turned out not to be regions, and the
one true region (water fog) waits for diving. What it would need: one per-frame choice of the fog at the eye in
`IndoorRenderer`, since every draw below reads `m_fog`; the programs would load for any map that has regions.

**Day and night** (`night`, opt-in): the fog after dark, mixed in from the day's as the sky's night falls
(`indoorFogAt` with `skyNightAmount`: the sun from 1 degree above to 7 below the horizon, about 21:00-21:40). MM9's
WeatherMan with `TurnOffAtNight 1` switches its FogOn state (by day) to its FogOff state at night: Thjorgard City grey
`Fog0` by day, black `Fog1` at night (Drangheim City the same). Other switching (weather sequences, scripted `FogOn`)
is a Lua call changing the same values ("Fog from Lua" below).

## Fog from Lua (2026-11-06)

`evt.SetFog(r, g, b, near, far [, seconds [, sky]])` replaces the fog an indoor map draws (its scene fog, its night
mix, or an outdoor view's haze) with a script's: colour 0..255, distances native from the eye, `sky` 0..1 of an open
sky in the fog colour; it fades in from the fog shown over `seconds` (real time). `evt.ClearFog([seconds])` fades back
to the scene's. The state is `EventRuntimeState::scriptedFog` (each call raises its revision), not saved: the map's Lua
sets it again on load. `IndoorRenderer::applyScriptedFog` mixes it in each frame (`indoorFogBlend`: colours, distances
and sky cover; a disabled end counts as the other's colour out of sight); under water a volume's fog still wins. It
needs the fog programs, so it shows on a map with a scene fog, an outdoor view or a water volume's fog; elsewhere the
call is kept and nothing is drawn. Outdoor (ODM) maps have their own `evt.SetOutdoorFog`.

MM9 user: the WeatherMan a touch Trigger switches (Frosgard's pass, Trigger1-4: On fades to the thick Fog0 in 1 s,
Off to Fog1, whose fog begins past its far clip, so clear, in 8 s). `dungeon/objects.py` `weather_triggers` /
`weather_lines` (every converted map, a 4 Hz poll, event 905; map variable `Weather<index>`, set again without the
fade on load); `fog_state_lua` writes a Fog state as `evt.SetFog` (sky 1 when its SkyFogNearZ is inside the sky box)
or `evt.ClearFog`. The other WeatherMen either start on (the scene fog and its `night`) or are switched by nothing in
the DAT (Thronheim City's Clear/Foggy, Lindisfarne's and the monastery's). Tests: `tests/IndoorFogTests.cpp` "a
script's fog fades in ..."; `mm9r_frosgard_blv/scenario_fog.yml` (the `scripted_fog` assert).

## MM9's fog model (`model: lithtech`, opt-in)

```yaml
fog: {color_rgb: [127, 127, 127], near_distance: 64, far_distance: 11520, model: lithtech,
      night: {color_rgb: [0, 0, 0], near_distance: 64, far_distance: 11520}}
```

What MM9 does (`d3d.ren`, Rizin/objdump 2026-10-31):

- **Linear in view depth, LT units.** Fog on sets `D3DRENDERSTATE_FOGTABLEMODE` (0x23) to LINEAR (`0x10017319`), and
  the fog factor is computed per vertex (`0x100092b0`): 255 before `FogNearZ`, 0 past `FogFarZ`, linear between, from
  the vertex's camera-space z (`[ecx+8]`), scale 255 / (far - near) (`0x10011486`). No range fog (state 0x30 is never
  set). Our distances are LT x 2.56, so the units were right; only the distance differs (view depth, not the distance
  from the eye: at the screen's edge ours fogged up to 1.2-1.4 times more).
- **Two passes, two fog colours.** The texture pass fades into the fog colour; the lightmap pass (multiplied onto it)
  fades into a second colour from a table, 255 x sqrt(i / 512) for the fog byte i (`0x10009660`, used at
  `0x100638d6` and `0x1003fd3a`): 127 stays 127, white becomes 179. So a fully fogged world face shows
  colour x that (127 -> 63, a darker grey), and a shaded face (lightmap 0.3) fogs toward grey far less than the lit
  colour does. The table makes colour x colour' = colour only under `Saturate` (x2 blend), which MM9 never sets.
  Inferred from code, not from a real screenshot (no real city shots yet).
- **Faces**: `mix(colour / light, fog, a) x mix(light, fog', a)`, `light` the face's light (static, daylight and dynamic;
  the room light for surface-material faces), `a` from the view depth (`u_indoorFogMode`, `u_indoorFogLight`, set by
  `setFaceFog`). Billboards already use the view depth; models keep the distance from the eye and one fade (MM9 draws
  models in one pass).
- **Correction (2026-10-31, the sky-fog investigation): MM9's default world fog is the distance from the eye, not the
  view depth.** `0x100092b0` reads the *sky* fog variables (`SkyFogNearZ` 0x10094f08, `SkyFogFarZ` 0x10094f04, by the
  cvar registration at `0x10006998`/`0x100069c4`; its scale at `0x10011486` is 255 / (SkyFogFarZ - SkyFogNearZ)) and
  is called only from the sky pass (`0x100169a1`). The world's vertex fog is `0x10009220`, chosen at `0x10011528`: the
  Euclidean distance from the eye (`0x10094054`..`5c`) against `FogNearZ`/`FogFarZ` (0x10094f0c, 0x100902b8), scale at
  `0x100114bd`. The hardware table fog (FOGTABLEMODE LINEAR at `0x10017319`, view depth) replaces it only with the
  `TableFog` cvar (0x10094e44, default 0, not set in `autoexec.cfg`). So `model: lithtech`'s view depth (x of
  `u_indoorFogMode`) is not MM9's default; the plain distance from the eye is. Not changed here (an engine decision for
  the orchestrator); the two-pass colours above are unaffected.

**Why Thjorgard City looked hazy.** Its `Fog0` (grey, 25-4 500 LT) is MM9's own daytime fog, carried correctly; the haze
read strong because the streets were lit at 0.35 (no sun), so the grey fog was brighter than the scene and lifted
every distant face toward it. With daylight and MM9's model (faces fade to 63, light and texture apart) it reads as
MM9's light haze. **Frosgard City** really is that dense in MM9: WorldProperties `EnableFog 1`, grey 1-2 000 LT, FarZ
2 500 (MM9 draws nothing further), its sky wholly in the fog colour (below), a WeatherMan holding the same state day
and night.

## The sky in fog (scene fog `sky`, opt-in)

```yaml
fog: {color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120, sky: 1, model: lithtech}
```

What MM9 does (Rizin 2026-10-31; `d3d.ren`, `cshell.dll`, `object.lto`, `lithtech.exe`):

- **The sky pass is fogged whenever the fog is on**, with its own distances: the sky draw sets FOGSTART/FOGEND to the
  renderer's `SkyFogNearZ`/`SkyFogFarZ` (`d3d.ren` `0x10016d0c`-`0x10016d45`, LithTech's `d3d_drawsky.cpp`), and each
  sky vertex gets its fog byte from its camera-space depth in sky space against them (`0x100092b0`, called from the sky
  loop at `0x100169a1`). The fog colour is the world's (`FogR/G/B`).
- **Where the distances come from.** WorldProperties and every `Fog` object set the server variables `SkyFogNearZ` /
  `SkyFogFarZ` (`object.lto` `0x100da6e8`, `0x10083edf`); the client copies them into the renderer
  (`cshell.dll` `0x10083100`-`0x10083482`, "%s %f") but reads `SkyFogNearZ` twice, so the renderer's far value is the
  near one (`0x10083433`: a bug; it makes the ramp a step). WorldProperties' `SkyFog` flag is copied into a console
  variable no binary reads (`d3d.ren` and `lithtech.exe` have no `SkyFog` variable), so it changes nothing.
- **The sky box is far beyond those distances.** The sky is a `DemoSkyWorldModel` box, `SkyDims` 128 x 128 x 128 LT,
  the sky camera within `InnerPercent` 0.1 of its centre (every city), so every sky vertex is at least 115 sky units
  deep. A fog state with `SkyFogNearZ` under that (Frosgard City 48, Thjorgard and Drangheim City's day `Fog0` 0,
  Thronheim's scripted `FoggyDay`/`FogDay` 0) draws the whole sky in the fog colour; one past it (the night states'
  99 999) leaves it clear. The sky is one pass, so it takes the fog colour itself (127 grey), not the darker grey a
  fully fogged two-pass face shows.

The scene key `sky` (0..1, in the fog block and in its `night` state, mixed with the fog's day-night blend) is how much
of an open sky ([INDOOR_OPEN_SKY.md](INDOOR_OPEN_SKY.md)) is drawn in the fog colour. `IndoorRenderer::renderOpenSky`
passes it to the sky state (`SkyInputs::fogCover`, `fogCoverDisplay`), which lerps the gradient and the cloud colours
toward it and fades the sun disc and glow, moon, stars, horizon ring and cloud layers by the same share
(`SkyStateModel::update`). The sun's colour and the ambient tint, which indoor daylight reads, are left alone. Without
the key (every other map, every outdoor map) the sky state is unchanged (`fogCover` 0; unit test "sky state draws an
indoor fog cover").

Converter: `overrides.yml` `map: {sky_fog: true}` (opt-in) makes `Source.fog` write `sky: 1` for each fog state whose
`SkyFogNearZ` is nearer than the map's sky box (`Source.sky_fogged`). Cities by their DAT values:

| City | Fog at the start | Sky with `sky_fog` |
| --- | --- | --- |
| Frosgard City | WorldProperties + `Fog0` (WeatherMan, no night switch): grey 1-2 000 LT, SkyFogNearZ 48 | grey day and night (set) |
| Thjorgard City, Drangheim City | `Fog0` by day (SkyFogNearZ 0), `Fog1` at night (99 999) | grey by day, clear at night (not set: the orchestrator's call) |
| Thronheim City | none at the start (its `Foggy` weather and day/night fogs are scripted) | clear |
| Sturmford, Guberland, Arslegard City | none (`EnableFog 0`, no starting `Fog`) | clear |

The MM9 converter writes the block itself: `dungeon/source.py` `Source.fog` reads `WorldProperties`, else a `StartOn`
`Fog` object, LT × 2.56, and `dungeon/build.py` puts it in the scene. `overrides.yml` `map: {fog: false}` leaves it out;
`map: {fog: lithtech}` adds `model: lithtech` and the WeatherMan's `night` state (`Source.night_fog`).

## Fog by the daylight (scene fog `follow_daylight`, opt-in)

```yaml
fog: {color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120, sky: 1, model: lithtech,
      follow_daylight: true}
```

MM9 never changes its light with the hour, and its fog stays the same day and night unless a WeatherMan switches it.
Our indoor daylight ([INDOOR_OPEN_SKY.md](INDOOR_OPEN_SKY.md) "Daylight") darkens the open streets at night, so a fog
held at its day colour stood light grey over dark streets: Frosgard City's 127 grey fog and fogged sky at 23:30
(2026-11-01). With `follow_daylight: true` the frame's fog colour (after the day-night mix of `night`) is multiplied
per channel by `indoorDaylightFogScale`: the open air's light at this game time over its light at noon, the light
being the daylight's room-light measure (ambient plus half the sun, at most 1; `IndoorDaylight.cpp`). It is exactly 1
at 12:00, so noon is unchanged; at midnight it is the night scale's share of the ambient. Frosgard City: x (0.21,
0.23, 0.31) at 23:30, fog and sky (27, 29, 39) instead of 127 grey. A fogged sky (`sky`) takes the darker colour, and
MM9's lightmap-pass colour (`model: lithtech`) follows it. Thjorgard and Drangheim City switch to their black night
fog anyway; the key only darkens their grey day fog through the evening, before the 21:00-21:40 switch.

Needs the scene's `daylight` block (without one the key does nothing). The MM9 converter writes it where a city has
both `city: {daylight: true}` and fog (`city/hooks.py`: Thjorgard, Drangheim, Frosgard City); no MM6-MM8 map or MM9
dungeon has it. Code: `IndoorRenderer::updateFrameDaylightAndFog`. Unit tests: "indoor fog: following the daylight is
opt-in", "indoor daylight: the fog colour's scale follows the open air's light, 1 at noon".

## Rendering

The fog is linear in the distance from the eye, `clamp((d - near) / (far - near))`, mixed in display space as the last
step of each shader, the same fade everywhere:

| Drawn | How |
| --- | --- |
| Faces (vertex-lit, baked, surface materials, each opaque and translucent) | `INDOOR_FOG` variants of `fs_indoor_textured_lit.sc`, six programs loaded only for a map with fog; uniforms `u_fogColor`, `u_fogDistances` per draw |
| Sky faces (`IndoorSky`) | stay clear when drawn as faces; an open sky behind them takes the fog colour by the fog's `sky` (above) |
| Blood splats | the same vertex-lit fog program |
| Indoor water, lava, tar | `INDOOR_FOG` variants of `fs_indoor_water.sc` (`WaterRenderer::setIndoorFog`) |
| Decorations, actors, items, spell sprites as billboards | their shader's existing linear fog (`u_fogDensities.w` 1), `IndoorRenderer::setBillboardFog` |
| 3D models (creatures, decorations, items, projectiles) | the model shader's existing linear fog, `ModelRenderLighting` fog fields |

`IndoorFog.h` packs the uniforms; disabled, they are the constants those draws always passed, so the billboard and model
paths are unchanged on every other map.

**Cost with fog off.** No program, no uniform, one `bool` tested per face batch. With fog on: one `length` and `mix` per
pixel in the face shaders, no extra pass.

**Not fogged.** Particles and effect sprites, ribbons and shield domes (no fog term in those shaders outdoors either, and
glow reads through fog); the hover outline overlay. Billboards use view depth where faces and models use the distance
from the eye, so a sprite at the screen's edge is fogged a little less than the wall behind it; at Anskram's 12 800 range
the difference is small.

## Baked lighting

The bake ignores fog: it is applied at draw time, so changing it needs no rebake. A map calibrated without fog gets
darker with it; compare with a reference that shows the fog, or tune with it on.

## Tests

`./build/tests/openyamm_unit_tests --test-case='*indoor fog*'`: the disabled defaults equal the old constants, the linear
ramp, parsing and every refusal; the `model` and `night` keys, the day-night mix and MM9's lightmap-pass colour table
(2026-10-31); the `sky` key and its night mix (`*indoor fog*`), and the sky state's cover (`*sky state draws an indoor
fog cover*`). MM7 `7d06` and MM8 `d06` captures before and after; the 2026-10-31 change was checked with the old
binary against the new on MM6 `6d02`, MM7 `7d06`, MM8 `d06`, Anskram Keep and the Lich Lab (only moving creatures and
flames differ, as between two runs of one binary).
