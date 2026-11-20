# OpenMW-inspired water for OpenYAMM

Status: proposed implementation plan, 2026-09-21. No water implementation or asset import is included in this document.

## Goal and scope

Give OpenYAMM water approximately OpenMW's visual quality and behavior, adapted to MM6–MM8 geography and art.
Use OpenMW's wave normal texture and rendering techniques as the starting point, with a new bgfx implementation.
Preserve water placement, shoreline shapes, collision, swimming/water-walking rules, and map/save compatibility.

This work targets current main and does not depend on `f/materials-shaders`. It does not introduce a general PBR
material system, replace the sky renderer, add global dynamic shadows, or import OpenSceneGraph.
The first release covers outdoor MM6–MM8 terrain water. Indoor water, model-face liquids, waterfalls, and MM9 water
are later consumers of the same shading code, not reasons to expand the first milestone.
Existing unsupported liquid surfaces retain their existing rendering explicitly.

Use one shared wave asset and shader across worlds. Geography may override shallow/deep color, absorption,
wave scale/strength, and flow through mounted presentation data; do not hardcode three continent-specific shaders.
Retain original textures for an explicit Classic mode, not as the visible base of Enhanced water.
Do not simply add shiny highlights over the original painted ripples.

## Source anchors and adaptation requirements

OpenMW reference checkout: `/home/pjasicek/github/openmw`, inspected at `ce8a52117c`.

| Reference | Reuse or adaptation |
| --- | --- |
| `files/data/textures/omw/water_nm.png` | Reuse the 128×128 wave normal map; it is not a diffuse water texture. |
| `files/shaders/compatibility/water.frag` | Reference for layered normals, Fresnel, sun highlights and depth handling. |
| `files/shaders/lib/water/fresnel.glsl` | Reference for air/water Fresnel behavior. |
| `apps/openmw/mwrender/water.cpp` | Reference for reflection camera, clipping and resource lifecycle. |
| `files/shaders/lib/water/rain_ripples.glsl`, `apps/openmw/mwrender/ripplesimulation.cpp` | Later rain/object ripples. |

Texture reuse is approved by the user. Record the asset's upstream path, revision, hash, authorship and applicable
license/notice when importing it. Do not assume that texture and source-code notices are interchangeable.
Generate our integration and shader code; literal upstream code reuse would require a separate license review.
The local OpenYAMM README currently declares no project license.

Relevant current OpenYAMM code:

- `game/maps/MapAssetLoader.cpp` composites shoreline overlays over animated water frames today.
- `game/maps/MapAssetLoader.h` stores terrain-region water and transition flags.
- `game/outdoor/OutdoorRenderer.cpp` builds heightmap triangles, marks pure water, updates animated textures,
  and submits terrain and water together.
- `game/shaders/outdoor_textured_fog.sh` distorts tiled diffuse UVs; transition overlays are excluded from this path.
- `game/tables/SurfaceMaterialTable.*` already supplies liquid semantics without the materials branch.
- `game/outdoor/OutdoorSunlight.h` suppresses its normal direct-sun uniform when lighting data is present.
- `game/render/CinematicGrading.cpp` owns an optional scene-color target with write-only D24S8 depth.
  It is not currently a reusable sampleable opaque-scene/depth source.

The major difference is geometry: OpenMW's water plane cannot replace our terrain and mixed shoreline tiles directly.
Also, scene depth cannot supply a seabed that the map does not contain. Resolve these two issues before promising
transparent shallows everywhere.

## Phase 0 — Lock down coverage and comparisons

1. Preserve the existing baseline captures before new tour runs overwrite them. Use separate baseline and candidate
   output directories, with the same settings, save, resolution, time of day and weather.
2. Audit water classification and shoreline composition in New Sorpigal, Emerald Island and Ravenshore.
   Identify flat/sloped water triangles, transition masks, elevations, and whether underwater geometry exists.
3. Trace base/overlay orientation and alpha before compositing. Define an explicit water-coverage convention
   (`0 = land`, `1 = water`) and preserve it in asset loading; never infer it from blue pixel colors.
4. Inventory exceptional liquid semantics so lava, tar and other animated surfaces are not accidentally upgraded.
5. Record baseline frame time, draw calls, GPU identity/backend, resolution, target allocations and map-load cost.
   Screenshot output alone is not performance evidence.

Exit: documented surface/coverage contract, retained baselines, and reproducible comparison settings.

## Phase 1 — First visible upgrade: normals, Fresnel and lighting

This is the first independently reviewable implementation and the recommended starting scope.

### Assets and ownership

- Import the OpenMW normal map into shared engine presentation assets, proposed location
  `assets_dev/engine/liquids/water_nm.png`, with provenance/notice alongside it and package inclusion.
- Sample normals as linear data, with repeat addressing and mip filtering. Verify image orientation and normal
  channel signs with a directional-light test; do not apply diffuse-texture gamma conversion.
- Add a small shared water profile, loaded through the normal mounted-asset system. Start with one tuned default;
  add map overrides only when the three-world visual review demonstrates a need.
- Keep water GPU resources under one renderer owner. Put reusable shading/resource code in `game/render/` and
  ODM-specific surface extraction in `game/outdoor/`. Avoid a general material framework or forwarding layers.

### Geometry and shores

- Split enhanced water draw ranges from ordinary land while preserving existing terrain positions and topology.
  Keep batching/chunk bounds; do not create a draw call per tile.
- Preserve uncomposited shore artwork and water coverage when loading transition tiles. Shade the water portion
  with the same world-space waves as open water, then combine the land portion without animated blue fringes.
- Define depth-write/coverage behavior explicitly for mixed tiles, so docks and land occlude water correctly.
  Avoid duplicate coplanar full-tile surfaces and z-fighting. This coverage contract must also work in Phase 2.
- Keep gameplay geometry unchanged. Do not flatten sloped liquid tiles into a global ocean plane.

### Shading

- Implement a dedicated water shader using world-space wave coordinates, continuous across tile boundaries.
  Start with two or three differently scaled/scrolled normal samples. OpenMW uses six; add more only if the
  motion review justifies their cost. Tune scale in our world units, not OpenMW's constants.
- Blend water body color and an environment reflection using Fresnel, with normal-driven sun highlights.
  For this phase, use a reflected-direction sky-color approximation driven by the existing atmosphere.
  Label it correctly: it is not yet a reflection of clouds, boats, buildings or terrain.
- Define water sun direction/intensity explicitly. On unbaked maps use atmosphere lighting. On baked maps resolve
  the bake's sun direction through authoritative lighting metadata, with current daylight/weather intensity.
  Do not reuse the zeroed direct-sun uniform or infer shadow visibility from baked RGB radiance.
  If bake direction is absent from runtime data, add explicit metadata rather than a hardcoded guess.
- Do not multiply specular/reflection by a second diffuse-lightmap term. Document color-space handling, apply fog
  consistently, and ensure cinematic grading affects the finished water once.
- No displacement, refraction targets or reflection scene pass yet. No claim of dynamic sun-shadow parity.
- Provide explicit Classic and Enhanced settings. Preserve Classic visuals. Allocate enhanced-only resources
  only when needed; unsupported backend capabilities must be reported, not hidden behind stale-data fallbacks.

Exit: all three reference views visibly improve, shores remain intact, waves move naturally, and night/fog do not
produce glowing water. No tile seams, distracting specular shimmer, or gameplay changes. Review this before Phase 2.

## Phase 2 — Depth-aware shores and refraction

This is a render-target/pass change, not just another water shader parameter.

1. Establish one owner for world scene targets, independent of whether cinematic grading is enabled.
   Integrate grading as a consumer; do not maintain competing owners or two copies of the same scene pipeline.
2. Render opaque geometry, including applicable alpha-tested surfaces, into scene color/depth without water.
   Retain an immutable sampleable opaque color/depth source for water. Choose formats/copy paths after checking
   bgfx backend capabilities, multisampling behavior and depth sampling support.
3. Composite water into a distinct destination. Never sample an image currently bound for writing.
   Set bgfx view order explicitly; submission call order alone is not the pass-order contract.
4. Reconstruct view-space depth using the active projection and bgfx depth/origin conventions. Reject distorted
   samples in front of the water and out of bounds, and suppress distortion at shallow intersections.
5. Add depth-based absorption and controlled shallow/deep color. Where no seabed exists, use the explicit deep-water
   treatment. A coverage/distance-based shore fade may soften the edge but must not be called physical depth.
   Authored seabeds, if wanted later, are a separate content decision with no automatic collision changes.
6. Define transparent-object ordering deliberately: handle submerged effects separately from above-water effects
   as required, then grading and HUD. Keep HUD out of refraction. Test sprites crossing the waterline.
7. Validate resize, fullscreen changes, map transitions, grading on/off, resource teardown, and underwater views.
   Do not double-apply existing underwater tint/fog or silently replace MM7 underwater-map behavior.

Target pass dependency:

`opaque scene → stable color/depth inputs → water composition → remaining transparency → grading → HUD`

Exit: believable shoreline/contact behavior and refraction where geometry supports it, without halos, missing
land, feedback artifacts, underwater regressions or unnecessary targets on dry/Classic maps.

## Phase 3 — Selective planar scene reflections

- Add an opt-in higher-quality mode after Phase 2 is accepted. Reflect sky plus selected opaque world geometry
  across a validated water plane, using a clipped mirrored camera and correct winding/culling.
- Group compatible coplanar water surfaces. Initially render at most one selected visible plane per frame;
  other elevations and nonplanar liquid surfaces use the established sky-reflection approximation.
- Start with a half-width/half-height target. Exclude water itself, HUD and expensive transparent FX to prevent
  recursion and keep costs bounded. Add reflection content categories only when visually useful.
- Reuse scene rendering with an explicit camera/pass context. Do not copy the entire outdoor renderer or advance
  simulation twice. Camera-dependent culling, sprite facing and light selection must use the reflection camera.
- Skip the pass when no eligible water is visible. Any reduced update rate needs explicit camera/scene invalidation
  and motion testing; stale reflections are not an acceptable default optimization.
- Account for actual water elevation; never assume OpenMW's local zero-height convention fits our maps.

Exit: boats, harbor structures and coastline reflect correctly in the three views, without below-plane leaks,
wrong-facing sprites or unacceptable frame-time cost. Keep this tier optional if target hardware cannot afford it.

## Phase 4 — Weather and interaction polish

- Drive wave strength and procedural rain rings from the existing weather state; keep dry-weather work minimal.
- Add bounded object/party-impact ripples only through existing simulation events and verified water contact.
  Start with a capped analytic ripple list; adopt a simulation texture only if its visual benefit warrants it.
- Optionally add local-light specular using the existing selected lights, without introducing clustered lighting.
- Extend the shared shader to indoor/model water after defining those surfaces' coverage, normals and elevations.
- Review optional foam carefully; do not add continuous white foam to every shoreline by default.

## Verification and acceptance

Use the existing native capture tours and inspect the PNGs, not just their existence:

| World/map | Tour | Visual focus |
| --- | --- | --- |
| MM6 / New Sorpigal / `oute3.odm` | `tools/screenshot_tours/mm6_water.yml` | Replace bright painted ripples; preserve bay edges. |
| MM7 / Emerald Island / `7out01.odm` | `tools/screenshot_tours/mm7_water.yml` | Dock/boat contact, shore masks, view-angle response. |
| MM8 / Ravenshore / `out02.odm` | `tools/screenshot_tours/mm8_water.yml` | Reduce repetition; harbor color and highlights. |

Retain those exact supplied poses. Add grazing-angle, close-shore and moving-camera checks, plus day/night,
rain/fog, lightmaps on/off, grading on/off, Classic/Enhanced, a dry map, and lava/other-liquid regression views.
For phase-sensitive stills add a narrow render-time override if necessary; a camera tour alone does not freeze
shader animation time. Also inspect motion because stills cannot reveal shimmering, scrolling seams or lag.

Build normally with `cmake --build build --target openyamm -j25`. Add focused doctests for classification,
coverage/orientation, profile validation, plane grouping and any pure projection/depth helpers. Build
`openyamm_unit_tests` and run the corresponding focused cases. Use real desktop runs through
`./tools/run_game.sh`; see `tools/RUN_GAME.md`. Do not run Vulkan builds without fresh user authorization.
If Android code/assets are affected, validate a release APK before claiming mobile support.

Measure each phase separately at fixed resolution/settings with warmed-up, repeated runs and VSync/frame caps
disabled for timing. Record median and tail CPU/GPU frame times where available, draw counts and render-target
memory; identify the actual device/backend. Report milliseconds, not just FPS. Do not invent a universal budget
before measuring target hardware. Phase 1 adds no scene rerender; Phase 2 adds bandwidth/targets; Phase 3 adds
another scene view. Dry maps and Classic mode should acquire no meaningful water-specific runtime cost.

## Delivery sequence

1. Coverage audit, retained baselines, approved texture/provenance and profile loading.
2. Enhanced normal/Fresnel/sun shading with correct mixed shoreline coverage and Classic toggle.
3. Three-world visual/motion/performance review and tuning; first usable water upgrade.
4. Shared scene-target ownership, depth-aware refraction and shoreline/contact review.
5. Optional planar reflections with their own quality/performance acceptance.
6. Weather/interaction polish and later surface-type expansion.

Each implementation slice should include its focused tests and comparison evidence. Phases 0–1 are the first
implementation request; the remaining phases describe the route toward broader OpenMW-like water behavior.
Success means convincing water in our worlds at a measured cost, not pixel-identical Morrowind screenshots.
