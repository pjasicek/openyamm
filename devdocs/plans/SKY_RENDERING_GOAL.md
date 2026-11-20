# Enhanced Outdoor Sky Goal

Status: done 2026-10-09. Phase 8 (indoor sky faces) is deferred as optional. The physical-phone check was waived by the user in favour of the emulator evidence. Plan written 2026-10-08. See the
**Progress log** at the end for evidence and the remaining notes.

## Goal

Replace the outdoor MM8-style projected cloud quad with a data-driven **Enhanced sky** for MM6–MM8 (and MM9 maps
that use the same path):

- a procedural atmosphere gradient with a visible sun, moon and stars;
- density-only cloud layers lit by the sun, plus a distant horizon cloud ring;
- colours keyed by time of day and weather presets in YAML, blending smoothly instead of swapping textures;
- **all outdoor fog sampling the same sky colour function**, so distant terrain dissolves into the sky;
- 3D-model reflections and water lighting driven by the same sky state.

Keep the current renderer as an explicit **Classic** sky option. It must remain pixel-identical to today.

### Done when

All of these are true and recorded in the Progress log:

1. `video.sky_style = enhanced|classic` exists in settings, the settings menu and all three `settings*.ini` files.
   Enhanced is the default in `settings.ini`, `settings_release.ini` and `android/settings.ini`.
2. Every phase's exit check below has passed (Phase 8 is optional).
3. `cmake --build build --target openyamm -j25` and `cmake --build build --target openyamm_unit_tests -j25` succeed.
   `./build/tests/openyamm_unit_tests --test-case='*sky*'` passes, and the existing fog, sunlight, water,
   model-environment and weather tests still pass. Run `openyamm_runtime_tests` for the weather suite.
4. The final review gallery `output/sky_review/final/` exists for MM6, MM7 and MM8 across the time and weather
   matrix in **Verification**, together with a side-by-side Classic vs Enhanced contact sheet. The images have been
   inspected, and no shot shows a grey horizon band, hard sky texture pops, cloud smearing at the horizon or
   terrain and sky colour mismatches.
5. The Classic sky capture matches the Phase 0 baseline (same pose, time and weather).
6. The release APK builds (`android/build_release_apk.sh`), so the ESSL `300_es` shaders compile, and the Android
   emulator check in **Verification** passes (acceptance criterion chosen by the user on 2026-10-09).
7. The performance budget in **Verification** is met and the measured numbers are recorded.

## Rules for this run

- Follow `AGENTS.md`. Write new code and do not copy OpenMW code: OpenMW (`/home/pjasicek/github/openmw`) is a
  behavioural reference only.
- Do not run Vulkan builds. Do not commit unless the user asks.
- Gameplay rules are out of scope and must not change: fog **distances and opacities** (visibility), weather rolls,
  rain/snow and event semantics. Enhanced changes only colours and the sky picture.
- Keep shared logic shared. The sky state is computed once per frame and consumed by terrain, bmodels, billboards,
  decorations, water, models and reflections. Do not fork indoor/outdoor logic beyond the world hooks.
- Do not add per-map hacks in C++. Special environments are presets selected by existing data (scene flags, merged
  sky names, event overrides).
- The working tree already holds unrelated uncommitted changes. Do not revert or reformat files outside this goal.

## Current state (verified 2026-10-08)

- **Sky draw:** `OutdoorRenderer::renderOutdoorSky` (`game/outdoor/OutdoorRenderer.cpp:5754`) draws one
  screen-space quad in `SkyViewId 0` with no depth. `computeOutdoorSkyVertex` (`:464`) projects one texture on a flat
  plane. A 39 px solid band (`SkyFogHorizonPixels`) fills the area below the sky.
  - The same function draws each water reflection's sky view (`:4176`). The reflection target clears to `0x405060ff`
    (`game/render/WaterRenderer.cpp:351`).
- **Colour:** each sky texture has its blue sky painted in. Time of day is a grey multiplier,
  `computeOutdoorSkyTintAbgr` (`:397`) → `outdoorClearDistanceFogBrightness` (`game/outdoor/OutdoorFogProfile.h:72`).
  - Clear-weather fog uses that same grey. This causes the grey horizon band and the colour mismatch.
- **Sky choice:** `OutdoorWorldRuntime::refreshAtmosphereState` (`game/outdoor/OutdoorWorldRuntime.cpp:7909`) picks
  the texture in this order:
  1. the merged MMerge weather sky (`mergedSkyTextureNameForProfile`, `:1165`);
  2. the source sky, adjusted by the clock (`resolveRenderedSkyTextureName`, `:1083`: `sunsetclouds` at 05–06 and
     20–21, `sky6pm` at night);
  3. Dagger Wound forced to `sunsetclouds` (`:8069`);
  4. the event `SetOutdoorSky` override (`:8074`).
- **Sun:** 05:00–21:00 only, `(cos θ, 0, sin θ)` with θ = (min − 300)·π/960 (`:8117`). It rises at +X, sets at −X,
  and points straight up at night. No sun disc, moon, stars or lightning exist.
- **Fog formula** (`getFogRatio`, `game/shaders/outdoor_lighting.sh:4-42`): one flat `u_fogColor` per draw. The
  colour is computed in four places:
  - `buildOutdoorWorldFogParameters` (`OutdoorRenderer.cpp:849`);
  - `buildOutdoorSkyFogParameters` (`:923`);
  - billboard duplicates `computeClearDistanceFogColorAbgr` / `computeBillboardFogColorAbgr`
    (`OutdoorBillboardRenderer.cpp:239/245`);
  - models through `u_modelFog` (`engine/render/ModelRenderer.cpp:1242`, filled from
    `OutdoorRenderer::modelSceneLighting`, `:4032`).
- **Shaders that apply fog:** `outdoor_textured_fog.sh`, `outdoor_bmodel_lightmap.sh` (its own copy of the formula),
  `fs_water.sc`, `billboard_lit.sh` (planar `v_depth`), `fs_sprite_outline.sc`, `fs_spell_area_preview.sc`,
  `fs_model.sc` and `fs_outdoor_force_perspective.sc`.
- **3D models:** reflections come from the cloud plane via `prepareModelSkyEnvironment`
  (`engine/render/ModelEnvironment.cpp:82`). This is a synchronous CPU GGX pass over a 128² cube with 8 mips,
  rebuilt whenever the sky texture name changes (`ModelRenderer::prepareEnvironment`, `:2040`).
- **Water lighting:** hardcoded sun and sky colours (`OutdoorRenderer.cpp:5182-5195`).
- **Rendering pipeline:** no HDR target. World shaders work in display space; models shade linearly and encode to
  sRGB before fog.
- **View order** (`game/render/WaterMath.h:152`): shadows → reflections → sky 0 → main 1 → AO → grading.

## Target design

### Ownership

| Piece | Location | Responsibility |
| --- | --- | --- |
| Presets and aliases | `assets_dev/engine/rendering/sky/sky.yml` | Colour keyframes, cloud layers, celestial settings, legacy name aliases |
| Sky textures | `assets_dev/engine/rendering/sky/*.png` | Cloud density layers, horizon ring, star field, moon disc, optional panoramas |
| `SkyPresetLibrary` | `game/render/SkyPresets.{h,cpp}` | yaml-cpp loader and validation (pattern: `SurfaceMaterialTable::loadFromYaml`) |
| `SkyStateModel` | `game/render/SkyState.{h,cpp}` | Pure logic: atmosphere + clock + preset → `SkyFrameState`; transitions; sun and moon directions |
| `SkyRenderer` | `game/render/SkyRenderer.{h,cpp}` | Owns the Enhanced program, textures and uniforms; draws the main and reflection sky views; packs fog uniforms |
| Shared GLSL | `game/shaders/sky_common.sh` | `skyGradient(dir)`, `skyFogColor(dir)` and the uniform declarations used by every fog shader |
| Sky program | `game/shaders/vs_sky.sc`, `fs_sky.sc` | Full-screen sky pass |

`OutdoorRenderer` keeps the Classic path (`renderOutdoorSky`) unchanged and calls `SkyRenderer` when Enhanced is
active. `OutdoorGameView` owns one `SkyStateModel` and one `SkyRenderer` per outdoor runtime. They live under
`game/render/` because indoor sky faces (Phase 8) and reflections reuse them.

### Sky state (CPU, once per frame)

`SkyFrameState` is plain data in linear RGB:

- `zenith`, `horizon`, `horizonExponent`
- `sunGlow` (colour, exponent, strength)
- `fog` (colour, `skyMix`)
- `sunDisc` (colour, angular size, visibility)
- `moon` (direction, phase, visibility)
- `stars` (visibility, rotation)
- `cloudLit`, `cloudShadow`, per-layer coverage and opacity
- `horizonRingTint`, `ambientTint`, `waterSunColor`, `waterSkyColor`
- `lightningFlash`
- `belowHorizon` mode: `fog`, `sky` (Plane of Air) or `flat`

Inputs: `AtmosphereState` (weather flags, fog flags and distances, authored fog colour and tint, red fog,
underwater, alwaysDark/alwaysLight, sun direction), the game minutes, the resolved **weather sky name** (see
Phase 1), real-time `dt` and the `sky_style` setting.

### Preset selection

1. Underwater → preset `underwater`. Fog only, no sky draw, `skyMix = 0`.
2. Event or Lua `SetOutdoorSky` override → alias lookup.
3. `red_fog` (MM8 `elemf`) → `plane_fire`. `always_light` + `no_terrain` (`elema`) → `plane_air`. `always_dark`
   (`d06`, `7out15`) → `always_dark`.
4. Otherwise the weather sky name goes through `aliases` (e.g. `sky05` → `clear`, `stormclds` → `storm`,
   `sunsetclouds` → `ember`, `sky04` → `winter_overcast`).
5. When the foggy weather flag is set, blend toward the preset's `fog` keys using the existing `fogDensity` and fog
   distances. Fog distances keep their current values.
6. Authored data wins over presets: `hasAuthoredFogColor` / `hasFogTint` set the fog colour exactly as today and
   force `skyMix` down (`fog_tint_sky_mix` per preset, default 0.25), so `out04_1` and the MM9 fog maps keep
   their authored look.

An unknown alias logs one `[AssetLoadWarning] kind=sky_preset` and falls back to `clear`. Unit tests make sure every
known name has an alias (Phase 1).

### Time keyframes

Colours are keyed by game time (`HH:MM`) and interpolated in linear RGB with smoothstep between keys, wrapping
across midnight. The default key set follows the existing sun and fog windows (night before 05:00 and from 21:00;
dawn and dusk transitions 05:00–06:00 and 20:00–21:00):

`02:00 night`, `04:40 pre-dawn`, `05:20 sunrise`, `06:15 morning`, `12:00 noon`, `17:30 afternoon`,
`19:50 golden`, `20:35 sunset`, `21:10 dusk`, `22:00 night`.

Presets may give fewer keys. Missing values inherit from the `base` preset.

### Weather transitions

When the resolved preset changes, `SkyStateModel` cross-fades the evaluated states over `transition_seconds`
(default 45 real seconds; clouds cross-fade layer opacity). Map load, teleport and save load **snap** with no blend.
Lightning: in presets with `lightning.enabled`, a seeded timer produces flashes (0.15–0.4 s) that add to sky, fog,
cloud and ambient tint. Thunder audio is optional (Phase 7).

### Shader contract

`sky_common.sh` declares the uniforms below. `SkyRenderer::fogUniforms()` packs them, and they are set wherever
`applyOutdoorFogUniforms` or the billboard and model fog setters run today.

```
uniform vec4 u_skyFog[6];
// 0: zenith.rgb,  horizonExponent
// 1: horizon.rgb, skyMix              (0 = legacy flat u_fogColor, 1 = sky-coloured fog)
// 2: sunGlow.rgb, glowExponent
// 3: sunDir.xyz,  glowStrength
// 4: fogFlat.rgb, displaySpace        (1 = output display-space colour for world shaders)
// 5: lightningFlash, belowHorizonMode, reserved, reserved
```

- `skyFogColor(dir)` evaluates the gradient at `vec3(dir.xy, max(dir.z, 0.0))`, adds the sun-glow lobe, then mixes
  with `fogFlat` by `skyMix`.
- The fog **ratio** (`getFogRatio`) is unchanged. Only the colour changes.
- World shaders fog in display space, models in linear space. Pick the conversion per shader with `displaySpace` or
  a define, not with a second set of uniforms.
- Classic sets `skyMix = 0` and `fogFlat` = today's colour, which reproduces current output exactly.

The sky program has its own extra uniforms (`u_skyDisc`, `u_skyMoon`, `u_skyStars`, `u_skyClouds[4]`,
`u_skyInvViewRot`) and samplers `s_skyCloudA`, `s_skyCloudB`, `s_skyRing`, `s_skyStars`, `s_skyMoon`.

### Sky pass

- Full-screen triangle in `SkyViewId 0` (and each reflection `skyView`), no depth, as today. The view direction
  comes from `u_skyInvViewRot`, which is the inverse view rotation times the inverse projection; the reflection pass
  gets the reflected camera's matrices instead of the current Y-flip hack.
- Layer order inside `fs_sky.sc`:
  1. gradient + sun glow;
  2. stars rotated about a celestial pole (fade by `stars.visibility`, hidden under clouds);
  3. moon disc with a shader-computed terminator;
  4. sun disc with a soft limb;
  5. horizon ring (cylindrical UV `atan2(dir.y, dir.x)` and elevation, alpha-blended, tinted, fades into fog);
  6. two cloud layers;
  7. below-horizon handling per `belowHorizon`.
- **Clouds.** Map the direction to plane UV with `uv = dir.xy / (dir.z + curvature) * scale + wind * time`
  (`curvature` ≈ 0.12 avoids the horizon singularity and gives a domed look).
  - Textures are density only (R = coverage density, G = a second octave or thickness).
  - Coverage remaps density with `smoothstep(1 - coverage, 1 - coverage + softness, d)`, so one texture serves
    fair, cloudy and overcast.
  - Lighting: `mix(cloudShadow, cloudLit, thickness)`, plus a Henyey–Greenstein forward-scatter rim toward the sun
    and darkening with density.
  - Fade to `skyFogColor(dir)` as `dir.z → 0`.
- **Sun direction:** exactly `AtmosphereState::sunDirection` while it is defined (05:00–21:00), so the disc, shadows
  and baked lighting agree. Disc visibility comes from keyframes and goes to zero below the horizon.
- **Moon direction:** the antipodal arc (rises at −X near 21:00, sets at +X near 05:00) with a small tilt. Phase
  comes from game days (28-day month, the `debugCivilTimeFromGameMinutes` calendar).

## Phases

Each phase ends with a build, the focused tests and a capture review. Record results in the Progress log.

### Phase 0 — Tooling and baselines

1. **Debug console `time set HH:MM`** (`GameApplication.cpp:3620`): advance forward to the next occurrence of the
   target time with `m_gameplayController.advanceGameMinutes(delta)` + `synchronizeSessionFromRuntime()`, so timers
   and the 03:00 weather rollover stay consistent. Add it to the console help (`DebugConsole.cpp:1735`).
2. **Debug console `sky ...`** (runtime-only, not saved):
   - `sky weather <0..6|auto>` forces the merged weather state used by `mergedSkyTextureNameForProfile`.
   - `sky name <texture|auto>` forces the weather sky name.
   - `sky style <enhanced|classic>` switches the style for A/B checks.
   - `sky preset <name|auto>` is added in Phase 2.
3. **Screenshot tour fields** (`game/debug/ScreenshotTour.{h,cpp}`): optional per-shot `time: "HH:MM"`,
   `sky_weather`, `sky_name` and `sky_style`, applied before settling through the same code as the console commands.
   Tour YAML parsing has unit coverage.
4. **Tour files** under `tools/screenshot_tours/sky/`:
   - `mm6_oute3.yml`: New Sorpigal, coast + open sea + town;
   - `mm7_7out01.yml`: Emerald Island;
   - `mm8_out02.yml`: Ravenshore;
   - `mm8_specials.yml`: one shot each on `elemf`, `elema`, `out04_1`, `out15` and `out01`/Dagger Wound. This needs
     one run per map; add a small loop script if useful.

   Each world shot list covers three views (horizon, 35° up, high vantage looking across the map edge) × the time
   matrix (`05:30`, `09:00`, `13:00`, `20:00`, `20:45`, `23:30`) × weather (`clear`, `overcast`, `storm`, `fog`).
   Reuse the positions from `tools/screenshot_tours/mm*_water.yml`.
5. Capture the **Classic baseline** into `output/sky_review/baseline/` (do not overwrite it later). Add a contact
   sheet script `tools/sky/contact_sheet.py` (Pillow) that writes labelled grids, and side-by-side pairs when given
   two directories.
6. **Performance baseline:** run `debug.effect_stats_delay_seconds` GPU timestamps (see `tools/RUN_GAME.md`) on
   `mm8 out02` at the horizon pose. Record the sky view and main view times, GPU identity and resolution.

Exit: the console commands work in a desktop run, tours capture the time/weather matrix, and baseline images and
numbers are recorded.

### Phase 1 — Sky data and state model (pure logic)

1. Split the sky name resolution in `refreshAtmosphereState`:
   - **Weather sky name:** merged sky, else the source sky, then the Dagger Wound rule, then the event override.
     This is the existing order minus the clock adjustment.
   - **Classic rendered name:** today's `skyTextureName`, with `resolveRenderedSkyTextureName` still applied.

   Store the weather sky name in `AtmosphereState` as a new **derived** field. Check the save path
   (`SaveGame.cpp:3417` serialises the whole AtmosphereState): either keep it out of serialisation and recompute it
   on load, or add it with an explicit version step. Old saves must load unchanged.
2. Write `assets_dev/engine/rendering/sky/sky.yml` (schema below), with presets `base`, `clear`, `fair`, `cloudy`,
   `overcast`, `rain`, `storm`, `fog`, `winter_overcast`, `ember` (Dagger Wound / Plane of Fire style sunset
   clouds), `plane_fire`, `plane_air`, `always_dark` and `underwater`.
   - Starting colours: derive the clear-day horizon and zenith from the restored sky textures (median of the sky
     pixels) so Enhanced reads as the same world. Use physically plausible sunset ramps and deep blue-violet nights.
3. Aliases for **every** known name:
   - `plansky1`, `plansky3`, `6plansky1`, `7plansky3`;
   - `sky01`–`sky06`, `sky12`, `sky19`, `6sky02`, `6sky03`, `6sky04`, `6sky06`, `6sky12`, `6sky19`;
   - `7sky01`, `7sky02`, `7sky04`;
   - `stormclds`, `sunsetclouds`, `sky6pm`, `cloudsabove`, `skycity01`;
   - MM6 `sky20`, `sky21`, `sky_clo1`, `sky_nit1`, `sky_nit2`, `sky_sns1`;
   - MM7 `sky07`–`sky19`.

   Continent weather ladders (clear → storm) map to `clear`, `fair`, `cloudy`, `overcast`, `rain` and `storm` in
   order.
4. Implement `SkyPresetLibrary` and `SkyStateModel` (see **Target design**). Load once per outdoor view with
   `readTextFile("engine/rendering/sky/sky.yml")`.
5. Unit tests in `tests/SkyStateTests.cpp`, named `"sky ..."`:
   - preset parsing and validation errors;
   - keyframe interpolation (including wrap at midnight);
   - inheritance from `base`;
   - **alias coverage** (parse `assets_dev/engine/data_tables/continent_settings.txt`, `bolster_maps.txt` and the
     hardcoded fallback names, and assert each resolves to a non-fallback preset);
   - selection precedence (underwater > event > special flags > weather name);
   - authored fog colour wins;
   - transition blend and snap;
   - sun disc hidden at night;
   - moon phase over a month;
   - Classic packing gives `skyMix = 0` with today's fog colour.

Exit: unit tests pass, no render change yet, and old saves load (run the existing save/load tests).

### Phase 2 — Enhanced sky pass (gradient, sun, below horizon)

1. Add `vs_sky.sc`, `fs_sky.sc` and `sky_common.sh`. Register them in `cmake/BgfxRuntime.cmake`: the compile calls
   in `openyamm_configure_runtime_shaders`, `runtimeShaderNames` (which feeds the Android shader list), and add
   `sky_common.sh` to the hardcoded include-dependency list at `:93-107`.
2. Add the `SkyRenderer` main and reflection draws. Gate them on `m_renderLayers.sky` in both the main pass and
   reflections, which also fixes the reflection call ignoring the toggle. Set the reflection sky view clear colour
   to the fog colour.
3. Add the setting `video.sky_style` (enum pattern of `MonsterProjectileVisuals`):
   - `GameSettings.{h,cpp}` parse and save;
   - `assets_dev/engine/ui/menu/settings_catalog.yml` select entry next to the water settings;
   - `MenuSettingsModel.cpp` get/set;
   - the three `settings*.ini` files (default `classic` until Phase 9);
   - the `sky style` console command.
4. Add the `sky preset <name|auto>` console and tour override.

Exit: Enhanced shows a gradient sky with a sun disc that tracks the shadow direction at every time in the matrix.
Reflections show the same sky. Classic is unchanged against the baseline. ESSL compiles (desktop build plus
`cmake` Android shader target, or the release APK if quicker).

### Phase 3 — Sky-coloured fog everywhere

1. Include `sky_common.sh` in `outdoor_lighting.sh`, `outdoor_bmodel_lightmap.sh`, `fs_water.sc`, `billboard_lit.sh`,
   `fs_sprite_outline.sc`, `fs_spell_area_preview.sc` and `fs_model.sc`. Replace `u_fogColor.rgb` with
   `skyFogColor(normalize(worldPos - u_cameraPosition.xyz))`.
   - Billboards use planar `v_depth`; pass a world-space view direction (or world position) from
     `vs_outdoor_billboard_lit.sc` without changing the fog ratio.
   - Remove `outdoor_bmodel_lightmap.sh`'s duplicate fog formula in favour of the shared include, keeping identical
     maths.
2. Single source of fog colour: delete the billboard duplicates (`OutdoorBillboardRenderer.cpp:239/245`) and the
   separate sky fog colour paths. Everything reads `SkyFrameState::fog` through `SkyRenderer::fogUniforms()`.
   `ModelRenderLighting` gets the same packed `u_skyFog` data; indoor scenes pass `skyMix = 0`.
3. Remove the Classic grey band only in Enhanced. With fog matching the horizon, the far-clip ring, the map edge and
   water edge should fade into the sky. If a visible seam remains at the far-clip ring, tune
   `belowHorizon = fog` brightness first, then raise the Enhanced fog `strongOpacity` near the far clip only.
   Keep visibility distances unchanged.
4. Particles currently have no fog. Leave them alone unless they visibly pop against the new fog. If so, add the
   shared fog to `fs_particle.sc` as a separate, reviewed step.

Exit: every capture shows terrain, bmodels, trees, billboards, water and 3D models fading into the sky colour in
the view direction (including the warm sun side at sunset). Classic still matches the baseline. Run the existing
`WaterRenderingTests`, `OutdoorSunlightTests` and `ModelAnimationTests`.

### Phase 4 — Cloud and ring assets

Assets go in `assets_dev/engine/rendering/sky/`, lowercase, 0644, with a `README.md` recording provenance (tool,
prompt, seed, sha256) for each file.

1. **Cloud density layers** from a deterministic offline generator, `tools/sky/generate_cloud_layers.py`
   (numpy + Pillow; tileable Worley–fBm via periodic noise, guaranteed seamless), RG8 PNG, 1024² (2048² only if
   the review shows softness):
   - `clouds_cumulus.png` (puffy, broken);
   - `clouds_stratus.png` (broad overcast sheets);
   - `clouds_cirrus.png` (high wisps; anisotropic stretch);
   - `clouds_storm.png` (dense, dark-core towers in the G channel).
2. **Codex-painted art** (image generation; no fine tiling needed):
   - `horizon_ring.png`: 4096×512 RGBA, distant cumulus banks and haze, neutral grey (luminance carries the form,
     alpha carries coverage), clear sky in the upper half and opaque toward the bottom edge. Wraps horizontally.
   - `night_sky.png`: 4096×2048 equirect, Milky Way band and nebula dust on black; individual stars stay
     procedural in the shader.
   - `moon.png`: 512² RGBA disc, neutral grey surface detail, true alpha.
   - Optional `plane_fire_panorama.png` / `plane_air_panorama.png` (4096×2048 equirect, used by those presets'
     `panorama` layer) if the review shows the procedural presets are not distinctive enough.

   Write `assets_dev/engine/rendering/sky/codex/CODEX_BRIEF.md` (scope: image generation only, write only into
   that folder; deliverables, sizes, neutral-grey-for-tinting rule, "no sun, no ground, no birds, no text"
   do-not list, per-image checks, `generation_runs.json` records). Run Codex in the background as in
   `level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md`:
   ```
   codex exec "Follow the brief in assets_dev/engine/rendering/sky/codex/CODEX_BRIEF.md exactly. Produce the images \
   with your built-in image generation tool and save them as specified." \
     -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
     -o assets_dev/engine/rendering/sky/codex/codex_last_message.md \
     < /dev/null > assets_dev/engine/rendering/sky/codex/codex_run.log 2>&1
   ```
   If `codex` or image generation fails, continue with procedural stand-ins (a generated ring from the cloud
   generator; stars only) and record it. Do not block the goal on art.
3. **Post-process**, `tools/sky/prepare_sky_art.py`:
   - wrap-seam crossfade for the ring (verify by tiling twice);
   - equirect pole/seam check for the night sky;
   - alpha clean-up for the moon;
   - convert to the final channel layout.

Exit: the assets exist with recorded provenance, and a tiled 2×2 preview of each cloud layer and the ring shows no
seams.

### Phase 5 — Clouds, horizon ring, night sky

1. Implement the cloud, ring, star, moon and optional panorama layers in `fs_sky.sc`, driven by preset layer
   definitions:
   - `texture`, `scale`, `speed`, `direction_deg`, `coverage`, `softness`, `opacity`, `altitude` (curvature);
   - two layers maximum per preset;
   - per-preset ring opacity;
   - star density and brightness.
2. Weather cross-fade blends layer opacity and coverage, not just texture swaps.
3. Use the existing `TextureFilterProfile::Sky` sampling, with repeat addressing and mips for the cloud layers.
   Load through `AssetFileSystem` (engine scope, world overrides allowed), and let a missing texture degrade to
   gradient-only with one warning.

Exit: the full matrix captures show:

- no cloud smearing or stretching at the horizon;
- no visible tiling at the default scale;
- sun-lit cloud rims at sunrise and sunset;
- storm and overcast reading as heavy;
- stars and moon visible on clear nights and hidden under overcast;
- seamless 05:00–06:00 and 20:00–21:00 transitions. Record a time-lapse strip: 13 captures from 19:30 to 22:30
  every 15 min.

### Phase 6 — Lighting coupling

1. **Water:** replace the hardcoded `sunColor` / `skyColor` (`OutdoorRenderer.cpp:5182-5195`) with
   `SkyFrameState::waterSunColor` / `waterSkyColor`. Keep their intensity curves. Check that the sun glint lines up
   with the sun disc in a reflection capture.
2. **3D-model environment:**
   - In Enhanced, build the model environment source from the procedural sky (gradient, sun glow and cloud average,
     evaluated on the CPU from `SkyFrameState`) instead of the cloud-plane bitmap.
   - Rebuild when the preset changes or the clock crosses a 30-game-minute bucket. Use a 32² base cube; this
     low-frequency source does not need 128².
   - Measure `prepareModelSkyEnvironment`. If a rebuild exceeds 2 ms on the main thread, move it to a background
     job and swap the result when ready.
   - Keep the current bitmap path for Classic.
3. **Ambient and sun tint:**
   - Apply `SkyFrameState::ambientTint` as a colour multiplier only where the outdoor sunlight and baked colours are
     combined (`OutdoorSunlight.h`, `outdoorBakedLightingColors`).
   - Do not change brightness curves. Tints are near-white by day, warm at sunset and cool at night.
   - Gate this on Enhanced and review it against baked lightmaps (`lightmaps` on and off).

Exit: models, water and terrain lighting agree with the sky colour at sunset and night captures. Classic still
matches the baseline.

### Phase 7 — Weather polish and special environments

1. **Lightning** for `storm` (and `rain` at low chance):
   - flash in the sky, fog and ambient tint;
   - optional thunder audio, delayed by a random distance. MM9 has `assets_dev/worlds/mm9/audio/ambient/thunder/*`;
     to use it for MM6–MM8, copy chosen files into `assets_dev/engine/audio/ambient/thunder/` with provenance
     rather than reaching into the MM9 world. Skip audio if that copy is undesirable and note it.
2. **Rain and snow darkening:** while precipitation is active, bias the preset toward `rain`, `storm` or
   `winter_overcast` coverage and colours, so the event `SetRain` / `SetSnow` and Frozen Highlands winter (`sky04`)
   look right.
3. **Special presets reviewed in place:**
   - `elemf` Plane of Fire: red fog;
   - `elema` Plane of Air: `belowHorizon = sky`, no ground fog band;
   - `elemw`, `out15`, `7out15_1` underwater: sky not drawn; fog unchanged;
   - `d06`, `7out15` always dark;
   - `out04_1` authored fog tint;
   - Dagger Wound `ember` sunset;
   - Shadowspire `stormclds`;
   - MM9 `plansky3` cities and the MM9 authored-fog maps (check them for MM9 regressions per `AGENTS.md`).

Exit: the special-maps tour passes visual review, and each preset is listed in the README with a capture.

### Phase 8 — Optional: indoor sky faces

Indoor faces flagged `FaceAttribute::IndoorSky` (`game/indoor/IndoorRenderer.cpp:2243-2295`) scroll a sky texture.
Optionally render them with `fs_sky.sc` (screen-space view direction) using the map's preset. This is not required
for **Done when**; record it as follow-up if skipped.

### Phase 9 — Default flip and hand-off

1. Set `sky_style = enhanced` in `settings.ini`, `settings_release.ini` and `android/settings.ini`, and update the
   settings tests (pattern: `tests/WaterRenderingTests.cpp:360`).
2. Final capture gallery `output/sky_review/final/` plus Classic/Enhanced side-by-side sheets. Inspect every sheet.
3. Run the performance measurement again (below) and build the release APK.
4. Write `level_generation/lighting/SKY_RENDERING.md` (or extend an existing lighting doc). Cover:
   - preset schema and aliases;
   - how to add a preset or world override;
   - console and tour commands;
   - asset provenance;
   - known limits.

   Add one line to `AGENTS.md` under Workflow pointing to it.

## `sky.yml` schema (version 1)

```yaml
version: 1
transition_seconds: 45
keys_default: ["02:00", "04:40", "05:20", "06:15", "12:00", "17:30", "19:50", "20:35", "21:10", "22:00"]

aliases:            # legacy / merged sky texture name -> preset
  sky05: clear
  plansky3: fair
  stormclds: storm
  # ... every known name, see Phase 1

presets:
  base:             # every field has a value here; other presets override
    keys:
      - time: "12:00"
        zenith: [0.20, 0.38, 0.72]       # linear RGB
        horizon: [0.62, 0.74, 0.88]
        horizon_exponent: 3.0
        sun_glow: [1.00, 0.85, 0.60]
        sun_glow_exponent: 8.0
        sun_glow_strength: 0.35
        fog: [0.62, 0.74, 0.88]          # foggy-weather colour (used when the fog flag is set)
        sky_mix: 1.0
        sun_disc: [1.00, 0.97, 0.90]
        sun_disc_visibility: 1.0
        cloud_lit: [1.00, 0.98, 0.95]
        cloud_shadow: [0.55, 0.60, 0.70]
        ambient_tint: [1.0, 1.0, 1.0]
        water_sun: [1.0, 0.94, 0.82]
        water_sky: [0.34, 0.46, 0.56]
        stars: 0.0
        moon_visibility: 0.0
      # ... remaining default keys
    sun_disc_degrees: 1.6
    moon_disc_degrees: 2.2
    below_horizon: fog                    # fog | sky | flat
    fog_tint_sky_mix: 0.25
    horizon_ring: { texture: horizon_ring, opacity: 0.7, height: 0.08 }
    stars: { texture: night_sky, density: 0.6, brightness: 1.0, pole_elevation_deg: 55 }
    clouds:
      - { texture: clouds_cirrus,  scale: 0.25, speed: 0.004, direction_deg: 30, coverage: 0.3, softness: 0.25, opacity: 0.6, curvature: 0.10 }
      - { texture: clouds_cumulus, scale: 0.45, speed: 0.008, direction_deg: 40, coverage: 0.4, softness: 0.20, opacity: 1.0, curvature: 0.12 }
    lightning: { enabled: false }
  clear:
    inherits: base
  storm:
    inherits: base
    keys: [ ... darker, desaturated ... ]
    clouds: [ { texture: clouds_storm, coverage: 0.85, ... }, { texture: clouds_stratus, coverage: 0.9, ... } ]
    lightning: { enabled: true, min_interval_seconds: 6, max_interval_seconds: 25 }
  plane_air:
    inherits: clear
    below_horizon: sky
```

The loader rejects unknown keys, bad times, colours outside [0, 4] and missing textures referenced by presets
(report them, then degrade gracefully at runtime). Times are game-clock `HH:MM`.

## Verification

- **Unit:** `./build/tests/openyamm_unit_tests --test-case='*sky*'` plus the existing fog, sunlight, water,
  model-environment, screenshot-tour and settings tests. Run the runtime weather suite (`openyamm_runtime_tests`,
  `HeadlessOutdoorDiagnostics` weather cases) after Phase 1 and Phase 7.
- **Visual matrix:** worlds × views × times × weathers from Phase 0, captured for Classic (baseline) and Enhanced
  each phase into `output/sky_review/<phase>/`, with contact sheets. Inspect them, especially:
  - the horizon line;
  - the map edge and far-clip ring;
  - sunrise/sunset direction (glow on the east at 05:30, west at 20:30);
  - the sun disc matching shadow direction;
  - cloud scale against the native look;
  - night readability (not pitch black: the world must stay playable at the current night brightness).
- **Classic regression:** Classic captures must match the baseline (pixel diff ≤ 1 LSB mean, no structural
  differences). Use a small diff in `tools/sky/contact_sheet.py --diff`.
- **Performance** (Phase 0 method; same GPU, resolution, pose):
  - Enhanced sky view ≤ 0.35 ms at 1920×1080 on the desktop GPU.
  - Main-view cost from sky-coloured fog ≤ +0.15 ms.
  - No model-environment rebuild above 2 ms on the main thread.
  - Record the numbers in the log.
- **Android:** `android/build_release_apk.sh` succeeds. On the `openyamm_api35` emulator, run one release capture of
  `mm8 out02` at 20:45 and check the frame time is not worse than Classic by more than 1 ms.

## Out of scope

- Physically based scattering (Bruneton/Hillaire LUTs), volumetric clouds, HDR and bloom. The `SkyFrameState`
  outputs are designed so a physical model can replace the keyframe evaluator later.
- Changing fog distances, weather probability, rain/snow particles or any gameplay rule.
- An infinite ocean plane beyond the map edge (separate follow-up; note findings from the Phase 3 map-edge review).
- Vulkan builds.

## Risks and decisions

- **Night brightness:** MM worlds are lit very low at night. The sky must not become brighter than the world can
  match. Tune the night presets against the existing ambient and the darkness behaviour, not in isolation.
- **Saved state:** `AtmosphereState` is saved wholesale. Any new field must be derived or versioned (Phase 1). The
  event sky and fog overrides are not saved today; keep that behaviour and do not fix it here.
- **Fog in two colour spaces:** world shaders fog in display space, models in linear space. Each shader must
  convert the shared colour correctly. Verify a model and a bmodel at the same distance against the same horizon.
- **Merged weather order:** keep `mergedWeatherStateForProfile` and the hourly cache untouched. Presets only
  consume the name it produces.

## Progress log

| Date | Phase | Result | Evidence |
| --- | --- | --- | --- |
| 2026-10-08 | Plan | Written | This file |
| 2026-10-09 | 0 | `time set HH:MM`; `sky weather/name/fog/rain/style/preset/clear` console overrides (runtime-only `OutdoorWorldRuntime::DebugSkyOverrides`); tour `time:` and `commands:` fields with unit coverage; `tools/sky/sky_review.py` capture/sheet/compare. Classic baseline captured (MM6/7/8 × 30 shots + 6 special maps). | `output/sky_review/baseline/` |
| 2026-10-09 | 0 note | MM6 `oute3` tour exits abort in `~GameApplication` (`free(): invalid pointer`) only on MM6, while concurrent decoration-model work changes `mm6_deco_*.glb` / `oute3.lighting`; MM7/MM8 exit cleanly with the same tour. Not caused by the sky work; captures complete before the abort. | `output/sky_review/baseline/tours/mm6.log` |
| 2026-10-09 | 1 | `game/render/SkyPresets`, `SkyState`, `SkyClock`; `assets_dev/engine/rendering/sky/sky.yml` (14 presets, weather ladder, aliases for every data-selectable name). Derived, unsaved `AtmosphereState::weatherSkyTextureName` / `mergedWeatherState(Count)`; save format unchanged. `tests/SkyStateTests.cpp` (12 cases incl. alias coverage from `continent_settings.txt` and `bolster_maps.txt`). | `openyamm_unit_tests --test-case='*sky*'` passes |
| 2026-10-09 | 2 | `SkyRenderer`, `vs_sky`/`fs_sky`, `sky_common.sh`; `video.sky_style` (settings, catalog, menu model, three ini files, default classic). Main and reflection sky views use real view/projection matrices. | `output/sky_review/phase2/` |
| 2026-10-09 | 3 | Every outdoor fog blend (terrain, bmodels, decorations, water, billboards, outlines, spell preview, models) uses `skyFogDisplayColor`; Enhanced adds aerial haze and a map-edge fade (`skyFogRatio`). Indoor billboards and models zero `u_skyFog`. Classic regression vs baseline: 60 MM7/MM8 shots, mean abs diff median 0.023, max 0.708 (storm rain/animated water) — within 1 LSB. | `output/sky_review/classic_check_compare/report.txt` |
| 2026-10-09 | 4–5 (clouds) | `tools/sky/generate_cloud_layers.py`: seamless spectral-fBm/Worley RG layers (cumulus, stratus, cirrus, storm), provenance in `cloud_layers.json`. Clouds lit by preset colours with sun-rim scatter; scale/softness/speed tuned in review. | `output/sky_review/phase4/mm7/` |
| 2026-10-09 | Perf | RTX 3060 Ti, OpenGL 3.3, 1600×900, MM8 out02 horizon: sky view 35 µs Classic → 74–89 µs Enhanced; main view 105 → 118–137 µs. Within budget (≤0.35 ms sky, ≤+0.15 ms main). | `[GpuViewPerf]` logs |
| 2026-10-09 | Perf (follow-up) | User-reported drop at New Sorpigal start pose (MM6 `oute3` (-9728, -11319, 161), yaw 90°, pitch -8.6°): Enhanced cost about +100 µs GPU (view 0 +33, view 1 +75). Fixed without visual change: fog colour is evaluated only for fogged fragments, the map-edge fade exits early inside the guaranteed-clear radius, and the sky pass returns the fog colour directly well below the horizon. Now GPU p50 about 504 µs Enhanced vs about 460 µs Classic (3 alternating runs each); median 1577–1640 fps vs 1666–1677 fps. | `[FramePerf]`, `[GpuViewPerf]` logs |
| 2026-10-09 | Original skies | User review: generic presets lost each place's look (Dagger Wound had no fiery sky). `tools/sky/derive_legacy_skies.py` now derives a `legacy_<name>` preset per data-selectable original sky (25): its painting as a colour cloud layer (`mode: color`, background keyed out for open skies, opaque for painted ones), original sky-plane scale and drift, daytime colours from the painting blended into the shared dawn/dusk/night ramps; `sunsetclouds` is fixed all day. Selection now prefers the resolved texture name (continent ladders keep their own skies); fog washes paintings toward the horizon and rain hazes them instead of replacing them. | `output/sky_review/legacy/`, `output/sky_review/final/` |
| 2026-10-09 | ESSL | All sky/fog shaders compile with `openyamm_shaderc --platform android -p 300_es`. | — |
| 2026-10-09 | 4–5 (art) | Codex art from `level_generation/lighting/sky_art/codex/CODEX_BRIEF.md` (ring, night sky, moon; attempts in `generation_runs.json` there, kept out of the runtime package), processed by `tools/sky/prepare_sky_art.py` (ring wrap blend + alpha, night pole fade, moon crop). Stars, moon phase, sun disc, horizon ring, below-horizon modes and storm/overcast fog colours tuned in review. | `output/sky_review/phase5*/` |
| 2026-10-09 | 6 | Water glint/sky-fill from preset; 3D-model reflections from a neutral cumulus environment coloured per frame (`skyEnvironmentTint`, no per-time rebuild); baked sun/sky light hue-tinted by the sky (`applyOutdoorBakedLightingTint`, luminance preserved, unit-tested). All gated on Enhanced. | `tests/OutdoorSunlightTests.cpp` |
| 2026-10-09 | 7 | Lightning flashes (storm presets); rain/snow presets; special maps reviewed: Plane of Fire red haze, Plane of Air open sky below, underwater/always-dark keep flat fog, Dagger Wound ember sky, MM9 Thjorgard authored fog. Thunder audio not added (MM9-owned sounds; copying them into the engine scope is a separate decision). | `output/sky_review/final/mm*-*/` |
| 2026-10-09 | 8 | Skipped (optional): indoor `IndoorSky` faces keep the scrolling texture. | — |
| 2026-10-09 | 9 | `sky_style=enhanced` is the code default and in `settings.ini`, `settings_release.ini`, `android/settings.ini`; Sky select in the video settings layout. Docs: `level_generation/lighting/SKY_RENDERING.md`, AGENTS.md pointer. Final gallery `output/sky_review/final/` with Classic/Enhanced sheets in `final/classic_vs_enhanced/`. Classic re-check: 36 clear shots, mean abs diff median 0.004, max 0.013. | `output/sky_review/classic_final_compare/report.txt` |
| 2026-10-09 | Android | `android/repack_runtime_assets.sh` then `./gradlew :app:assembleRelease` (the steps `build_release_apk.sh --repack-assets` runs) succeed for arm64-v8a; the release APK contains `essl/fs_sky.bin`, `vs_sky.bin` and every `engine/rendering/sky/*` asset. It was signed with a throwaway key because the release keystore password is a CI secret (the signed upload build needs that password); the original build output was restored. | `app-release.apk` listing |
| 2026-10-09 | Signed APK | `android/build_release_apk.sh --repack-assets` with the real release keystore: exit 0, `android/app-release.apk` SHA256 `3b64ad94…8fa823`. `apksigner` certificate SHA-256 `1e4c39b7…dbd15492` matches `keystores/openyamm-release.jks`; the APK contains `essl/fs_sky.bin`, `vs_sky.bin`, `fs_sky_upscale.bin` and all `engine/rendering/sky/*` assets. | `apksigner verify --print-certs` |
| 2026-10-09 | Android emulator | `android/run_release_emulator.sh` (debug-key x86_64 release APK) on AVD `openyamm_api35`, booted `-read-only`, with a pushed MM8 `out02` save and screenshot tour: Enhanced renders through ESSL with all sky assets (`output/sky_review/android/`). Software-GL emulator exposed the sky pass as the dominant cost (Classic 16.5 fps, Enhanced 8.3 fps); added `video.sky_resolution_scale` (Android profile 0.5, offscreen view 238 + upscale, visually identical on desktop: `output/sky_review/halfres/`) and cheaper per-pixel branches (Enhanced 11.9 fps in software GL). Plan check on the host GPU (`-gpu host`, vsync off, MM8 `out02` 20:45): Enhanced 247.0 / 252.7 fps vs Classic 242.2 fps, i.e. not slower than Classic. | `output/sky_review/android/host_gpu_2045_enhanced.png` |
| 2026-10-09 | Android acceptance | No physical phone was available (`adb devices` empty). The user accepted the emulator run as the Android acceptance (the plan's step allows "a device or emulator"): Enhanced renders through ESSL with all sky assets, and on the host GPU it is not slower than Classic (247/253 vs 242 fps at MM8 `out02` 20:45). Physical-phone check waived by the user. | `output/sky_review/android/` |
| 2026-10-09 | Tests | `openyamm_unit_tests`: 1555/1555 pass. Headless `weather` suite 13/13 (two cases now request the atmosphere-driven sunlight path explicitly). At the user's request, the 10 asset-layout tests that already failed on HEAD `1d7c42c49` were updated to the current authoritative layout: NPC/minimap/background icons in the `icons_x2` tiers (backgrounds re-pinned to the committed x2 PNG sizes and hashes; the unreferenced, archived `6outside` icon dropped), spell/object billboards resolving through restored `engine/decorations_x2/<name>_p<palette>.png`, actor previews accepting cooked `sprites_new` atlases, the `shp1` expectation removed because the New Sorpigal scene places no ship, and `settings_release.ini` keys synced with code defaults. | — |
| 2026-10-09 | Menu | Settings → Video → World detail shows "Sky" with an Enhanced/Classic chooser in the native menu. | `output/sky_review/menu/` |
| 2026-10-09 | Map themes | User review: maps need their own feel (Ironsand a hot red desert, Shadowspire necromantic). Added `themes`/`maps` to `sky.yml` (15 themes over 25 MM6–MM8 maps), derived from map names, `map_stats.txt` notes, terrain tile sets and original fog tints; `sky theme` console override. Untinted fog weather now leans on the original grey fog, and snow over painted skies hazes white. Misty Islands (`oute2`) not captured: its baked lighting is stale from separate MM6 decoration work. | `output/sky_review/themes2/`, `themes3/`, `themes4/` |
| 2026-10-09 | Night clouds, pixelation | User review: grey clouds at midnight; speckled cloud edges. Night cloud light now follows moon height, phase and visibility (30% under a new moon). Legacy layers are regenerated at 2× with dither softening, a smoothed alpha key and edge colour bleed. | New Sorpigal 00:11 / 06:36 captures |
| 2026-10-09 | Tests | `openyamm_unit_tests`: 1558/1558 pass (theme parsing/selection/application, themed maps exist in `map_stats.txt`, moonlit night clouds). | — |
| 2026-10-09 | HD masters | User review: Ravenshore clouds smeared. Cause 1: `sky06` keyed its grey cloud-edge tone as open sky (fixed: bluest sizeable cluster plus neighbouring shades). Cause 2: low-res 8-bit originals magnified ~10–20× overhead. All 25 skies repainted by Codex from the native bitmaps (`tools/sky/prepare_hd_sky_job.py`, jobs in `level_generation/lighting/sky_art/hd_skies/`), reviewed and installed in `sky_art/hd_masters/` with `masters.json`; layers are now built from them at 1024² with edge matching (seam ratio ≤ 0.32). Cloud-layer cache capped (unused layers released beyond four). In-game: Ravenshore `sky06` and Dagger Wound `sunsetclouds` checked; the full review matrix is blocked because the concurrent weather work's 11:59 build freezes after the first frame. | `output/sky_review/hd/` (pending) |
| 2026-10-09 | Horizon gap | User review (RS_2 save, flying over Ravenshore's south coast): pale band between sea and sky. The water hazed out at the view distance and the terrain square's edge, leaving fog where the original showed water up to the map edge. Added the distant sea: per-side border water share, sea level and water colour measured at map load; the sky pass draws a distance-hazed sea below the horizon past sea sides, and below-horizon fog fades into it (no ghosted far ships). Clouds now reach about 1° above the horizon. Fog weather, night, land sides, Dagger Wound and New Sorpigal checked; New Sorpigal start pose stays level with Classic (noisy host). | RS_2 captures |
| 2026-10-09 | Distance haze | User review: Ravenshore town washed out a few thousand units away in clear weather. The first-pass aerial haze reached 90% from 40% of the view distance (6.5k of 16.2k). Now at most 35% of the preset haze between 30% and 90% of the view distance; the world fog keeps the final fade. Town, land and sea views re-checked against Classic. | — |
| 2026-10-09 | Water edge | User review (DWI_1 save, flying): a curved cut where the water ended. With the gentler haze, water kept its own dark colour until its last 2k of fade at the view distance, against the brighter red-lit sea past it. Water on sea-facing views now fades into the distant sea over 40–97% of the view distance (`skyWaterFogRatio`); land keeps the gentle haze. DWI_1 and both Ravenshore views re-checked. | — |
| 2026-10-09 | View-distance end | User review (flying over Ravenshore): land ended in a hard cut. The world fog's clear-weather fade covers only the last eighth of the view distance, which is a few pixels when the terrain end is seen from the air. All geometry now also fades completely into the sky from 55% to 100% of the view distance (steep smoothstep), on top of the gentle depth cue; water on sea-facing views keeps its longer fade into the distant sea. Ground town view, high land views, Ravenshore sea and DWI_1 re-checked in clear weather. | — |
