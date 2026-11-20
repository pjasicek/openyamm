# MSAA plan

Status (2026-10-16): phases 0, 2, 3 and 4 are implemented for grass and model foliage; phase 1 is deferred; phases 5
and 6 are open. See "Implementation status" at the end.

Goal: stop distant objects and textures flickering as the camera moves, without a large performance cost. The fix is
multisample anti-aliasing (MSAA) on the 3D world plus alpha-to-coverage for cut-out foliage, and mipmaps for the
sprites that still lack them. TAA, FXAA and SMAA are out of scope: TAA needs motion vectors from every renderer and
blurs; FXAA and SMAA work on single frames and barely reduce flicker.

## 1. Where flicker comes from today

| Cause | Where | Fix |
|---|---|---|
| Geometry edges crawl (roofs, fences, trunks, creature outlines) | Everything: no anti-aliasing at all. Model draws set `BGFX_STATE_MSAA` (`engine/render/ModelRenderer.cpp`), but no target is multisampled, so it does nothing | MSAA |
| Cut-out foliage shimmers and pops (grass cards, leaves, railings) | Alpha-tested draws that write depth: terrain decorations (`TerrainDecorationRenderer.cpp`), model cut-out materials (`fs_model.sc`, depth prepass), BModel cut-outs (`outdoor_bmodel_lightmap.sh`, `fs_indoor_textured_lit.sc`) | Alpha-to-coverage under MSAA |
| Distant sprites sparkle | Sprites uploaded with `TextureFilterProfile::Billboard` have no mipmaps (`TextureFiltering.cpp` `profileUsesMipmaps`); used by `OutdoorBillboardRenderer` and `IndoorRenderer` for sprites outside the creature atlases | Mipmaps (phase 1) |

Already fine: terrain, BModel/indoor surfaces, sky and model textures have mipmaps (terrain and BModels anisotropic);
cooked model textures keep cut-out coverage across mips (`engine/ImageMipmaps.cpp` `preserveBgraCutoutCoverage`);
creature sprite atlases have mips.

## 2. Design

- **Only the world is multisampled.** The backbuffer stays single-sampled, so the UI, screenshots
  (`requestScreenShot` on the backbuffer), the loading-transition background and the loading readback blit are
  unchanged.
- **The world target lives in `CinematicGrading`**, which already owns the world post-processing target and its
  presentation pass (view `WorldGradingView`). With MSAA on, its colour and depth attachments are created with
  `BGFX_TEXTURE_RT_MSAA_X2`/`_X4`. The presentation pass samples the colour attachment, which bgfx resolves. That pass
  then runs whenever grading, sharpening, AO **or MSAA** is on (the same rule sharpening added).
- **Views are unchanged:** world views 0 and 1, `WorldTransparentView` after AO, then presentation, then UI from view 2.
  `worldRenderViewOrder` needs no new views.
- **Off-world targets stay single-sampled:** water reflections, sky image, shadow maps, actor portrait previews.
- **Capability check:** use MSAA only when `caps.formats[RGBA8]` and the depth format both report
  `BGFX_CAPS_FORMAT_TEXTURE_FRAMEBUFFER_MSAA`. Otherwise drop to 2× or off, with one log line (as AO does).
- **Setting:** `video.antialiasing` = `off` | `2x` | `4x`. Settings → Video → Display, as a select. Changing it
  recreates the world target (the existing `resize` path, keyed also on the sample count).

## 3. Phases

### Phase 0: spike (half a day, before writing feature code)

These answers decide phase 3 and the Android default:

1. On desktop OpenGL, confirm that sampling an MSAA colour attachment of a `CinematicGrading` framebuffer gives the
   resolved image (render one frame, capture, compare edges).
2. Check whether bgfx resolves an MSAA **depth** attachment so that it can be sampled (AO reads depth). Our shaders are
   GLSL 120 and ESSL 300, so `sampler2DMS` is not available without raising the shader profile.
3. Confirm that `BGFX_STATE_BLEND_ALPHA_TO_COVERAGE` works on OpenGL and OpenGL ES in our bgfx version.
4. Record the MSAA caps on the dev GPU and on the Android test device.

### Phase 1: sprite mipmaps (independent; can land first)

- Generate mipmaps for the `Billboard` profile, with cut-out coverage preserved like model textures. Keep the
  transparent-edge bleed so mips don't pick up dark fringes.
- Check: distant decorations at 0 % and 100 % camera motion, outdoors and indoors. Measure memory against the sprite
  texture budget (+33 % on these textures).

### Phase 2: setting and MSAA world target

- `GameSettings` (`antialiasing`, parse, save, clamp to known values), `MenuSettingsModel`, `settings_catalog.yml`
  (select), a new row in `assets_dev/engine/ui/gameplay/settings_video.yml`, and the key in `settings.ini`,
  `settings_release.ini` and `android/settings.ini`.
- When inserting the layout row, shift the later rows with exact four-decimal offsets. The sharpening row showed that
  Python's `'g'` formatting truncates them.
- `CinematicGrading::begin` takes the sample count. It creates MSAA attachments, falls back by caps and logs once.
  `GameApplication`'s three `begin` call sites pass the setting.
- Tests: settings default, round trip and invalid values; the menu catalog/layout test; the existing parity test (which
  also needs `creature_outlines` added to `settings_release.ini`, already missing).

### Phase 3: ambient occlusion with MSAA

AO reads world depth twice: the half-resolution linear-depth pass and the depth-aware composite. Choose by the
phase 0 result:

- **If bgfx resolves sampled MSAA depth:** no shader change. The resolved depth is one sample per pixel, which is fine
  for half-resolution AO. The composite multiplies into the MSAA colour target, which is per pixel and acceptable.
- **If not:** first version disables AO while MSAA is on, with one log line and the AO settings greyed out via
  `depends`. A later option is to write linear depth during the opaque pass instead (a larger change to every opaque
  shader). AO is off by default, so MSAA takes priority.

### Phase 4: alpha-to-coverage for cut-outs

- Only when MSAA is active: set `BGFX_STATE_BLEND_ALPHA_TO_COVERAGE` on the cut-out draws listed in section 1 and pass
  a uniform flag to their shaders.
- **Shaders with the flag:** instead of `discard`, output an alpha sharpened around the cutoff:
  `alpha = saturate((a - cutoff) / max(fwidth(a), 0.0001) + 0.5)`. This keeps leaf edges crisp instead of dithered.
  `fwidth` is available in GLSL 120 and ESSL 300. Without the flag, the current `discard` path is unchanged.
- **Model depth prepass:** the prepass writes per-sample depth through alpha-to-coverage, and the shaded pass keeps its
  equal-depth test. The LOD crossfade dither stays `discard`-based.
- **Leave alone:** alpha-blended draws (sprites, particles, water) and the terrain-edge coverage dissolve in
  `outdoor_textured_fog.sh`.

### Phase 5: measurement and defaults

- **GPU time:** use the frame timing already collected in `GameApplication` from bgfx stats (`gpuTimeBegin`/`End`)
  through the performance trace. Scenes: the New Sorpigal street and garden poses (oute3) and the Darkmoor ogre crowd
  (`saves/save10.oysav`), each at off, 2× and 4×.
- **Flicker check:** a screenshot tour turning the camera in small yaw steps. Compare frame-to-frame differences in
  distant regions, before and after.
- **Defaults:** desktop 4× if it costs ≤ ~20 % GPU time in those scenes, otherwise 2×. Android: release APK on the test
  device. 4× is often cheap on tile-based GPUs, but bgfx's GLES resolve path decides that; measure, then default to
  4×, 2× or off.
- **Memory:** 4× RGBA8 plus D24S8 is about 66 MB at 1080p and about 265 MB at 4K. Note this beside the setting.
- **Vulkan:** verifying the Vulkan renderer needs an explicit go-ahead for a Vulkan build.

### Phase 6: docs

Add a short section on anti-aliasing to this file, or move it into a rendering doc: what is multisampled, the
alpha-to-coverage rule for new cut-out shaders (use the flag; never a bare `discard` on depth-writing foliage), and
the measured costs.

## 4. Risks

- **bgfx MSAA depth resolve** differs by backend (phase 0 decides phase 3).
- **Fill-rate-heavy scenes** (dense grass, many sprites) pay the most. Grass is the main beneficiary too, so measure
  there first.
- **Sharpening on top of MSAA** works unchanged: it runs on the resolved image.

## 5. Estimate

| Phase | Effort |
|---|---|
| 0 Spike | ½ day |
| 1 Sprite mipmaps | ½ day |
| 2 Setting and MSAA target | 1 day |
| 3 AO with MSAA | ½–2 days |
| 4 Alpha-to-coverage | 1 day |
| 5 Measurement and defaults (incl. Android) | 1 day |
| 6 Docs | short |
| **Total** | **about 4½–6½ days** |

## 6. Implementation status (2026-10-16)

**Off costs nothing.** With `video.antialiasing=off` (the default everywhere) the world target, views, draw states,
shader programs and memory are exactly as before: `CinematicGrading::begin` still renders straight to the backbuffer
when grading, sharpening and AO are off, and the alpha-to-coverage programs are never loaded.

### Phase 0 findings (bgfx a73c12db8, read from source)

- **Depth for AO:** bgfx's `isFrameBufferValid` rejects a sampled multisampled depth attachment unless it is
  `BGFX_TEXTURE_MSAA_SAMPLE` (`sampler2DMS`, unavailable in the GLSL 120 / ESSL 300 shaders), although the GL backend
  resolves it with a depth blit (`FrameBufferGL::resolve`). `cmake/patches/bgfx-gl-msaa-depth-resolve.patch` lifts the
  check for OpenGL and OpenGL ES, so AO keeps working under MSAA there (phase 3, first option; the blit keeps one
  sample per pixel, enough for half-resolution AO). Vulkan resolves colour only: there AO is off while MSAA is on,
  with one log line. A custom `sampler2DMS` resolve pass would cover Vulkan later.
- **Colour:** a multisampled colour attachment is resolved when its view ends, so the presentation pass samples one
  value per pixel. Vulkan is not verified at runtime (no Vulkan build for this task); its SPIR-V shader variants are
  also unchecked.
- **Alpha to coverage:** bgfx reports `BGFX_CAPS_ALPHA_TO_COVERAGE` from `ARB_multisample`, which it never marks on
  GLES. Android therefore gets geometry MSAA with cut-outs still alpha tested (discard).
- **Caps:** MSAA needs `BGFX_CAPS_FORMAT_TEXTURE_FRAMEBUFFER_MSAA` on RGBA8 and on the depth format (D24S8, or D32F
  with AO); otherwise anti-aliasing stays off with one log line. GL silently clamps the sample count to
  `GL_MAX_SAMPLES`.
  The active mode is logged once: `Anti-aliasing: 4x MSAA, alpha to coverage on.`

### What was built

- Setting `video.antialiasing` = `off` | `2x` | `4x` (`GameSettings::antialiasing` as samples), the menu row in
  Settings → Video → Display, the three INI profiles and a unit test.
- `CinematicGrading`: multisampled colour and depth attachments keyed by the sample count; the presentation pass runs
  when MSAA is on; `alphaToCoverage()` for the world renderers.
- **`BGFX_STATE_MSAA` on every world draw.** On desktop OpenGL bgfx enables `GL_MULTISAMPLE` per draw from this flag;
  a draw without it rasterises single-sampled even into the multisampled target (no edge smoothing, and alpha to
  coverage does nothing). Only the model draws had it, so terrain, BModels, grass, sprites, water, sky, blood splats,
  effects and particles now set it too. The backbuffer is single-sampled, so with MSAA off the flag changes nothing.
  **Rule for new world draws: include `BGFX_STATE_MSAA`.**
- Alpha to coverage, as compile-time `ALPHA_TO_COVERAGE=1` variants loaded on first use:
  - **Grass** (`fs_terrain_decoration[_baked][_shadow]_coverage`): the blade cutoff becomes coverage sharpened to a
    pixel (`(a - cutoff) / fwidth(a) + 0.5`); stones keep their dissolve.
  - **Model foliage** (`fs_model_coverage`): only the depth prepass of alpha-tested static materials (decorations and
    terrain bushes, outdoors and indoors) writes coverage; the equal-depth shaded pass then fills exactly the covered
    samples, so the shading program is unchanged.
- **Not covered:** BModel and indoor face cut-outs (rare fences and bars; about ten more program variants), alpha-tested
  creature materials (creature depth prepass), and water reflections, which stay single-sampled.

### First measurement (desktop, NVIDIA, OpenGL, 1600×900, cinematic grading on in both runs)

New Sorpigal meadow pose with grass (`--position -5500 -5085 1200 --yaw-radians 1.222`): GPU p50 754 µs off, 967 µs
at 4× (+0.21 ms, +28 %). Captures show smoothed grass blades, tree cut-outs, BModel and terrain silhouettes.

With AO on (OpenGL depth resolve): the same meadow pose 1073 → 1496 µs (+0.42 ms); the 6d01.blv start 332 → 580 µs
(+0.25 ms). The extra over MSAA alone is the D32F depth resolve and the additional colour resolve around the AO
composite. AO contact shading matches the single-sampled image; canopy mean brightness is unchanged (MSAA only
averages away bright aliased leaf speckles).

### Still open

- Phase 1 (sprite mipmaps) is deferred: it is not behind the setting, so it would cost memory and load time with MSAA
  off, and its main target (decoration sprites) has become 3D models.
- Phase 5: GPU timings at off, 2× and 4×, the flicker tour, and the desktop and Android defaults.
- Phase 6: move this into a rendering doc once the defaults are measured.
