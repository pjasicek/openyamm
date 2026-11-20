# Outdoor weather plan

Status: implemented (2026-10-09), except the baked roof map (TODO below). See [Implementation](#implementation) for
where each part lives and how it was checked. Covers rain, snow, wind, thunder, surface response, audio and settings
for outdoor MM6-MM8 ODM maps. MM6-MM8 BLV maps stay weatherless. MM9's open-air BLVs (regions, the Afterworld, the
Isle of Ashes, the cities) reuse these parts over their open sky, with a roof map that keeps rain and snow out of
houses and tunnels: [Indoor open sky, "Weather"](../../devdocs/INDOOR_OPEN_SKY.md#weather). The baked roof occlusion
map for ODM maps is still deferred (see TODO).

## Why

Current behaviour (audited 2026-10-09):

- Precipitation is one deterministic roll per map per day at 03:00 (`mergedPrecipitationRoll`,
  `OutdoorWorldRuntime.cpp`), with hardcoded 20% rain / 15% snow chances (`GameDataLoader.cpp`). It snaps fully on
  or off; intensity is constant all day. The sky ladder state is rolled independently (midnight, hourly), so a storm
  sky can be dry and rain can fall under a clear ladder entry.
- Rain and snow are CPU particles in `OutdoorSpatialFxRuntime::syncWeatherParticles`, sharing the global 4096-slot
  `ParticleSystem` pool with spells and decorations. Snow (about 3400 flakes plus an 1800-flake prewarm) starves
  other effects.
- Rain spawns only in a box 320-2170 units in front of the camera (none around or behind the party), peaks at about
  145 streaks, and is clamped to intensity 3.0 so Heavy and VeryHeavy look identical. Its slant follows the camera's
  forward vector instead of a world wind.
- Weather particles get no fog and no lighting. There are no splashes, wet surfaces, rain rings on water, rain, wind or
  thunder audio, world lightning flash or player settings. Lightning only brightens the sky pass.

OpenMW (`/home/pjasicek/github/openmw`) was studied as a behavioural reference only:

- Worth adopting: weather transitions with a precipitation threshold (the old precipitation fades to zero before
  the new one fades in), random-walk wind driving the drop tilt, camera-relative wrap-around precipitation volumes,
  procedural rain rings in the water shader, and thunder flashes added to the ambient, sun and fog colours.
- Worth improving on: OpenMW simulates rain on the CPU and scales only alpha with intensity. It has no splashes or
  wetness, and its per-frame top-down occlusion pass is experimental and off by default.

## Target design

### Weather model (pure logic, unit tested)

New `game/outdoor/WeatherModel.{h,cpp}`, owned by `OutdoorWorldRuntime`, replacing the ad hoc precipitation fields
in `AtmosphereState`:

```text
WeatherSample {
    precipitation: none | rain | snow
    intensity: 0..1         // normalised; drives count, alpha, sound, wetness, ripples
    cloudCover: 0..1        // drives the sky ladder position
    wind: vec2 world xy     // units/s, direction and speed
    storm: bool             // thunder allowed
    wetness: 0..1           // accumulates during rain, dries afterwards
}
```

- **Deterministic from game time.** The daily roll stays, keyed on (map, day). It now produces an envelope, not a
  flag: start hour, build-up, peak intensity, plateau, ease-off. `sample(gameMinutes)` is a pure function, so
  save/load, rest and travel are consistent without persisting transient state. Wetness integrates over the previous
  few game hours of the same envelopes.
- **Unify the sky and the precipitation.** Precipitation is authoritative. Cloud cover rises about one game hour
  before rain starts and lingers after it, and the MMerge ladder position is derived from cloud cover. On dry days the
  existing MMerge ladder roll still picks clear/fair/cloudy/overcast. "Storm" sky and thunder occur only above a
  storm intensity threshold. Both rolls use the same day boundary.
- **Data.** Chances, envelope ranges, intensity presets, wind ranges and storm threshold move to
  `assets_dev/engine/rendering/weather/weather.yml`. MMerge `bolster_maps.txt` keeps deciding which maps have
  weather and whether they can snow.
- **Rain and snow chance** (decided 2026-10-09):
  - Global base chances in `weather.yml` (start from today's 20% rain / 15% snow).
  - Per-month multipliers, so snow-capable maps snow mostly in winter and rain peaks in spring and autumn. This
    follows the seasonal offset MMerge already applies to the sky ladder.
  - Optional per-map overrides in the same file, keyed by map file name, for maps that should be wetter, drier or
    always snowy. All weather tuning stays in one file instead of being spread over 54 scene YMLs.
  - Event `SetRain`/`SetSnow` (for example Frozen Highlands) still overrides everything.
- **Intensity presets** map the old names onto 0..1: Light 0.25, Medium 0.5, Heavy 0.8, VeryHeavy 1.0.
- **Overrides.** Event `SetRain`/`SetSnow` (saved with the game, as now) override the envelope with a fixed target.
  Debug overrides are session-only and no longer saved.
- **Smoothing.** The rendered sample approaches the model sample at a bounded real-time rate (a full ramp takes at
  least about 40 s), with a precipitation threshold for rain↔snow changes. Map load, clock jumps over 30 game minutes
  and console commands snap, matching the existing sky rule.
- **Wind.** A per-day base direction and speed come from the roll; a slow random walk adds gusts (OpenMW-style,
  bounded to 0.5x-2x of the base). The same wind feeds rain tilt, snow drift and the existing foliage sway uniform in
  `model_static.sh`.

### GPU precipitation renderer

New `game/render/WeatherRenderer.{h,cpp}` with `vs_weather.sc` / `fs_weather.sc`, drawn in the outdoor
transparent pass after water. It replaces the rain and snow branches of `syncWeatherParticles` entirely. Weather
leaves the shared `ParticleSystem` pool.

- **Static buffers, no CPU simulation.** A static vertex buffer is built once; each drop is a quad whose vertices
  carry a random seed and a corner index. The vertex shader computes the position from `u_time`, gravity, wind and the
  camera, wrapped modulo a camera-centred box (`p = cam + (fract((seed*box - vel*t - cam)/box) - 0.5)*box`). The
  volume always surrounds the party, moving the camera needs no leading-edge spawning, and snow never pops in.
  Time is wrapped on the CPU to keep float precision.
- **Intensity scales the number of drops.** The seeds are pre-shuffled, so drawing the first `N(intensity)` quads
  thins or fills the volume uniformly. Alpha is only a secondary trim.
- **Rain streaks** use the velocity relative to the camera (drop velocity minus party velocity), so running into
  rain slants the streaks. They are screen-aligned in width and stretched along the projected velocity, with a fade
  near the box faces and near the lens.
- **Snow flakes** are soft six-lobed flakes with a per-flake sine sway and rotation computed in the shader. Wind
  leans them by at most about one flake width, so they never smear into streaks; intensity sets the flake count.
- **Two layers.**
  - Near: a dense volume about 20-25 m around the camera.
  - Far: a sparser, larger volume for snow. For rain, a camera-centred "rain curtain" cylinder at about 30-50 m with
    a scrolling streak texture, plus a rain haze term in `skyFogRatio()`, gives distant density at fixed cost.
- **Lighting and fog.** Particle colour is multiplied by the sky environment / ambient tint, uses the shared
  `skyFogDisplayColor()` from `sky_common.sh`, and adds the lightning flash. At night rain becomes dim, faint streaks
  instead of bright lines.
- **Disabled** when the camera is underwater, indoors, or when `weather_quality=off`.
- **Ground.** Depth testing already hides drops below terrain and inside solid geometry. Drops under bmodel roofs and
  bridges remain visible until the roof map exists (TODO).

### Atmosphere coupling

- Sky preset selection reads `cloudCover` and `intensity` instead of raw flags. Rain and snow presets cross-fade with
  the model, and painted legacy skies keep the `PrecipitationHaze` path, scaled by intensity.
- Fog: rain and snow shorten the effective fog and haze distances in proportion to intensity, in Enhanced and Classic
  alike, via the existing fog distance path.
- **Thunder.** Strike events come from one place (extend the existing `SkyState` lightning, gated by `storm`).
  - A strike has a distance class. Its flash raises the ambient tint path that already reaches baked terrain, bmodel
    and model lighting (`skyEnvironmentTint` / `AmbientTint`), not only the sky.
  - The thunder sound plays after a delay proportional to distance, and closer strikes are brighter and louder.
- **Water.** Retune the `fs_water.sc` wave boost to the normalised intensity (today it is `0.15 * I` with I up to 5.35).

### Surface response

- **Rain rings on water.** A procedural hashed-grid ring layer in `fs_water.sc`, written for OpenYAMM and not
  copied. It is scaled by intensity and ramps in and out with it. Quality: off / 1 layer / 2 layers.
- **Wet surfaces.** A global `wetness` uniform darkens albedo on terrain, bmodels and 3D models (about 0.7x at full)
  and adds a mild sun specular sheen on upward-facing surfaces, less on walls. It dries over a few game hours. Snow
  gives no wetness; a snow cover tint is a later, separate idea.
- **Splashes.** A small GPU billboard pool (not the shared particle pool) spawned within about 12 m of the party at
  an intensity-scaled rate.
  - Heights come from the CPU outdoor floor query from above the camera. Under a roof the query finds the roof top,
    so splashes land there, which is correct.
  - Over water, splashes are replaced by the ring layer.

### Audio

- Two rain loops (light, heavy) are cross-faded by intensity, a strong-wind loop rises with wind speed, and thunder
  picks one of four variants per strike distance (near cracks, middle booms, distant rumbles).
- Sounds are the Might and Magic IX ambient recordings, copied unchanged into `assets_dev/engine/audio/weather/`
  (sources in its `SOURCES.md`) and levelled by per-sound volumes in `weather.yml`.
- Candidates compared on 2026-10-09 (measured, not listened to):
  - MM9: seamless 8-10 s mono rain loops, 13 thunder recordings, many wind loops; about 15 MB decoded in use.
  - CC0 (OpenGameArt, used first): long stereo loops but about 45 MB decoded, and a dull "near" thunder.
  - Morrowind: all rain and thunder records are in base `Morrowind.esm` (`Rain` = `Fx\envrn\rain.wav`,
    `rain heavy` = `rainHVY.wav`, `Thunder0-3` = `thndr_cls3`, `_Thunder0`, `_Thunder1`, `thndr_far2`); short
    4.7-6.8 s rain loops, and Bethesda's files cannot be redistributed. OpenMW ships no sounds.
- Loops start, stop and fade with the smoothed sample, through `GameAudioSystem::playSoundInstance(..., loop)` and the
  ambient group. They stop on entering BLV maps and under water.

### Settings

| Key | Values | Desktop default | Android default |
| --- | --- | --- | --- |
| `video.weather_quality` | off, low, medium, high | high | medium |
| `video.rain_ripples` | true, false | true | true |
| `video.wet_surfaces` | true, false | true | true |

Quality sets the drop budgets: near rain 1800 / 4500 / 9000 drops, far rain 1200 / 2500 / 5000, near snow
3000 / 7000 / 12000 flakes, far snow 0 / 1800 / 4000, one or two curtain rings, and no / 180 / 360 splashes; high
also draws two ring layers on water. The far rain box (70 m) overlaps the near one (26 m) with long edge fades, and
splashes thin out toward 15 m, so rain never visibly stops around the party (2026-10-09 fix).
Splashes follow the quality instead of a separate setting. Off hides falling rain and snow only; the weather, sky, fog,
wetness, rings and sound continue. All three keys are in the Video settings (`settings_catalog.yml`,
`settings_video.yml`) and `android/settings.ini`. Profile the Android release APK before raising its default.

### Debug console

The `weather` command replaces `sky rain`. Its overrides are session-only and are never saved.

- `weather` or `weather status`
- `weather rain|snow <0-1|light|medium|heavy|very_heavy>`
- `weather clear`, `weather auto`
- `weather wind <degrees> <speed>|auto`
- `weather storm on|off|auto`
- `weather strike [near|middle|far]`
- `weather forecast [hours]`, which lists the rolled weather hour by hour (the planned time-lapse)

## Phases

Each phase builds (`cmake --build build --target openyamm -j25`) and leaves the game shippable.

1. **Weather model and data.**
   - Add `WeatherModel` and `weather.yml`, and route `AtmosphereState` precipitation, sky ladder and fog through it.
   - Remove the 3.0 clamp, replace the camera-forward slant with the world wind, and replace the `sky rain` console
     command with `weather`.
   - Stop saving `rainIntensityPreset` and the debug overrides. Add an explicit snapshot migration that reads and
     discards the old field, and delete the uncalled `cycleRainIntensityPreset`.
   - The old CPU particles keep rendering, driven by normalised intensity.
   - Tests: doctest for envelope determinism, continuity of `sample()` across day boundaries, preset mapping,
     override precedence and sky/precipitation agreement; extend `SkyStateTests.cpp`.
2. **GPU precipitation renderer.**
   - Add `WeatherRenderer`, the near volume, the far layers, fog/lighting and the quality setting.
   - Delete the rain and snow code from `OutdoorSpatialFxRuntime` and its constants.
   - Checks: screenshot tour on a rainy and a snowy map (day, dusk, night, fog, moving camera, looking up and down),
     and a CPU/GPU profile on desktop plus an Android release APK at medium quality.
3. **Atmosphere coupling and thunder.** Smoothed sky and fog response, world lightning flash, strike events. Check
   with a screenshot tour during a storm, using `weather strike`.
4. **Surface response.** Water rain rings, wetness on terrain/bmodels/models, splashes and their settings. Check with
   tour captures over water and on a road, before, during and after rain.
5. **Audio.** Rain and wind loops plus delayed thunder, once assets exist. Check by listening on a desktop run.

### TODO: baked roof occlusion map (deferred)

- Bake a per-map top-down "highest blocking surface" grid from ODM bmodels (0.5-1 m cells) next to the existing
  `*.bake.json` outputs.
- At runtime the weather shader samples it to discard drops under roofs, bridges and overhangs, at no extra
  render pass (cheaper than OpenMW's per-frame depth camera, because ODM geometry is static).
- The same grid would mask wetness and splashes and muffle rain audio under cover.
- Destructible bmodels would need a runtime patch or a conservative bake.

## Ash fall (2026-10-22)

A third falling kind, added on top of rain and snow for Hesper's Starport Reach and inert on every map that does not
ask for it (no MM6-MM8 map does):

- **Where.** Ash falls only on maps whose `weather.yml` `maps` entry gives an `ash` chance (`hes_out1.odm: {ash: 65}`),
  with or without a `bolster_maps.txt` row; bolster rows still decide rain and snow. It has no month multiplier.
  Hesper's entry is a stage input (`level_generation/projects/hesper_stage/weather.yml`), merged into the stage's
  copy of `weather.yml`.
- **Rolls.** The ash roll is drawn after every older roll of the day and comes after snow and rain, so a map without
  ash rolls exactly the weather it always did (`WeatherModelTests`). Spell shape `ash:`, wind `wind.ash` (dust
  winds: the wind loop follows the wind speed). No storms, no wetness, no rain rings or splashes; it does not move the
  MMerge sky ladder to its rain entries or thicken the ladder fog.
- **Look.** `flakes:` in `weather.yml` gives each flake kind its colour, fall speed, near/far size and alpha, sway and
  sway rate; the snow entry restates the values snow was drawn with before they were data (the code defaults are the
  same, checked by a unit test). Ash is drawn by the snow shader with its own two layers: grey, slow, swirling.
- **Haze.** `flakes.ash.haze: [weak, strong]` closes the fog to those distances at full strength, faded in from
  16384/32768 at a trace. It lives in `AtmosphereState::hazeWeakDistance/hazeStrongDistance` (not saved) and reaches
  the renderers through `AtmosphereState::shownFog()`, which returns the map's own fog unchanged when there is no haze.
- **Console.** `weather ash <0-1|light|medium|heavy|very_heavy>`; status and forecast name ash.
- **Checks.** `review` captures in the Hesper stage (`hes_out1`, apron and Landfall street, clear, medium and very
  heavy ash, dusk, night, looking up). MM6 `oute3`, MM7 `7out01` and MM8 `out01` regression tours (coast, hilltop,
  forced rain, forced snow, dusk, night) differ from the pre-change captures only by the run-to-run animation (water,
  foliage, clouds, actors, drop seeds), at the same level as two pre-change runs against each other.

## Open-sky fog days (2026-11-09)

Indoor maps with an open sky and weather (MM9's regions and cities as BLVs) roll a daily fog from weather.yml's
per-map `fog` chances and `open_sky_fog` distances; outdoor maps ignore both. See
[INDOOR_OPEN_SKY.md](../../devdocs/INDOOR_OPEN_SKY.md) "Weather", "Fog days".

## Decisions

- MM9: out of scope (2026-10-09).
- Sounds: none in OpenMW; CC0 recordings were used first, then replaced by the MM9 recordings at the user's request
  (2026-10-09).
- Rain chance: global chances, seasonal multipliers and optional per-map overrides, all in `weather.yml`
  (2026-10-09).

## Implementation

| Part | Location |
| --- | --- |
| Rules, day rolls, wetness, ladder fog, flake looks, ash haze | `game/outdoor/WeatherModel.{h,cpp}`, `engine/rendering/weather/weather.yml` |
| Overrides and atmosphere state | `OutdoorWorldRuntime::currentWeatherSample`, `applyMergedWeatherProfile` |
| Real-time fades, gusts, lightning | `game/outdoor/WeatherPresentation.{h,cpp}`, `OutdoorRenderer::updateWeather` |
| Rain, snow, curtain and splashes | `game/render/WeatherRenderer.{h,cpp}`, `vs_weather.sc`, `fs_weather.sc` |
| Wet terrain and buildings | `game/shaders/weather_wetness.sh` (`u_wetness`) |
| Rain rings | `rainRingSlope` in `game/shaders/fs_water.sc` (`u_waterRain`) |
| Sky and lighting | `SkyInputs::precipitation`, `lightningFlash`; `applyOutdoorWeatherLighting` (rain-cloud dimming) |
| Sound | `game/outdoor/WeatherAudio.{h,cpp}`; files and sources in `assets_dev/engine/audio/weather/` |

Notes:

- Rolls use a splitmix64 hash of (map, day), not `std::` distributions, so they match across platforms.
- MMerge's ladder fog (`8192 / state`, `16192 / state`) is kept from `Scripts/General/Weather.lua`, but it now follows a
  continuous ladder position, so fog thickens smoothly as the rain builds.
- Lightning moved from `SkyState` to the weather. Sky presets mark storm skies with `storm: true`, which replaces the
  old `lightning` block.
- Saves from before version 85 drop their retired rain-intensity override when loaded.
- Checked with `WeatherModelTests.cpp` and `SkyStateTests.cpp`, the `weather` headless regression suite, and screenshot
  tours on `oute3.odm` (rain from light to storm, day, dusk and night, looking up, snow and blizzard, wet road,
  splashes, overview). The full unit suite passes.
- Not yet done: an Android release-APK profile at medium quality, and a listening pass on a desktop run (the
  `weather.yml` sound volumes are set from measured loudness).
