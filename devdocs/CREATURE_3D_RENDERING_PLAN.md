# Shared 3D creature rendering plan

Status: all three renderer passes implemented and native desktop acceptance completed, 2026-10-05.
The three-demon gameplay integration is working.
This document defines the renderer scope, review milestones, and acceptance criteria. Completion of each
pass requires the evidence below; the presence of implementation code alone does not establish acceptance.

The [2026-10-06 performance investigation](../output/performance/demon_renderer_budget_20261006/REPORT.md)
measures the corrected animation path and identifies dormant death-effect processing and precise picking as
the first crowd costs to fix. Its isolated diagnostics establish FPS budgets before LOD implementation;
they are not production changes or new visual acceptance of this plan.
The subsequent [production CPU fixes](../output/performance/demon_cpu_fix_20261006/REPORT.md) implement the
first two findings, including bounded batched death particles. The subsequent
[LOD and shadow-budget implementation](../output/performance/demon_lod_shadow_20261006/REPORT.md) adds four reviewed
geometry levels, independent merged shadow geometry, configurable sunlight quality and retained scene resources.
These are performance follow-ups to the accepted material/lighting passes, with their own native review and measurements.

## Intended result

Make GLB creatures feel physically present in OpenYAMM through proper scene lighting, distinct material
responses, animated mesh shadows, and stable texture detail. The improvement must be obvious from the
same camera used to review the MM6 demon. Implement the techniques in the existing shared bgfx renderer
with original code, using the local OpenMW checkout as a design reference.

The demon is the first visual acceptance asset. The resulting material and lighting path must also work
for future GLB creatures through their authored maps and factors, without a special shader per monster.

| Visible outcome | Acceptance expectation |
| --- | --- |
| Skin with depth | Directional light reveals muscles, face structure, and normal-map detail. Dark skin remains rough, with broad, restrained highlights. |
| Distinct materials | The green harness reads as matte leather. Teeth, spikes, and claws read as ivory bone. Red eyes retain black pupils and gain small glossy highlights. |
| Scene lighting | Daylight provides directional shape; shade reduces direct illumination; torches and spells cast coloured light. Indoor illumination comes from room lights. |
| Convincing shadows | The animated body casts a silhouette onto the ground. Ears, brows, spikes, and limbs self-shadow under sunlight. |
| Stable motion | Textures, normal detail, and highlights remain coherent during walking, attacks, turns, and distance changes, with reduced shimmering. |
| Shared support | Material maps drive appearance across GLB assets; ordinary gameplay still owns creature behaviour and timing. |

The existing mesh and texture artwork remain the visual foundation. No new Meshy generation, remodelling,
or animation authoring is required for this plan. Material corrections are appropriate if inspection finds
incorrect roughness or metallic values in the authored asset; record those edits separately from shader changes.

## Delivery sequence

| Stage | Reviewable result | Dependency |
| --- | --- | --- |
| Phase 0 | Retained comparison state, material audit, sun/sky data contract, and performance baseline. | Existing three-demon trial. |
| Pass 1 | Directional scene lighting, distinct skin/leather/bone/eye response, correct colour, and stable filtered textures. | Phase 0; shared glTF material data and world-light selection. |
| Pass 2 | Animated outdoor ground silhouettes and sunlight self-shadowing. | Pass 1; the same evaluated pose and direct-light contract. |
| Pass 3 | Roughness-filtered sky reflections and a subdued indoor response. | Pass 1 material response; review together with Pass 2 occlusion. |

Review each pass from the retained close-up and wide camera before proceeding. Keep the captures and measured
costs with the pass record so its appearance and performance can be assessed independently.

## Starting baseline and diagnosed gaps

The following describes the three-demon renderer before these upgrades. Use the progress record and retained
validation evidence to track implementation; do not treat this baseline as a live description of unfinished edits.

See [MM6 demon trial](../assets_dev/worlds/mm6/models/README.md) for the completed integration, asset provenance,
animation bindings, native capture, and existing validation. Its opt-in descriptor is `Demon A`; merged monster
id `502` is **Devil Spawn**, with ordinary Demon-kind data and `NoCorpse` behaviour. The trial spawns three
actors in New Sorpigal (`mm6`, `oute3.odm`).

- [ModelMaterial](../engine/models/ModelAsset.h) and [GltfModelLoader](../engine/models/GltfModelLoader.cpp) initially
  retained base colour, normal maps, emissive factors, alpha mode, and unlit flags. They did not retain the GLB's
  metallic/roughness factors or texture binding for shading.
- [ModelRenderer](../engine/render/ModelRenderer.cpp) initially uploaded base image levels and bound base colour and normal
  textures. It had no material-dependent specular response, environment lighting, or mesh-shadow pass.
- [Model fragment shader](../game/shaders/fs_model.sc) initially used diffuse lighting plus a scalar ambient term, normal
  mapping, emission, and fog. It mixed linear glTF colour factors with display-colour textures/output.
- [Outdoor sunlight helper](../game/outdoor/OutdoorSunlight.h) returns zero direct sun and full ambient when a map
  has lighting data. That convention suits the existing surface path, but the model path does not consume the
  baked lighting that replaces it. Normalizing its zero direction is also undefined and must be avoided.
- [IndoorRenderer](../game/indoor/IndoorRenderer.cpp) initially passed a fixed light direction and fixed ambient/direct
  values to models instead of the room's lighting frame.
- [Outdoor probes](../game/outdoor/OutdoorLightingData.h) provide separate sun and sky RGB samples. Their exact
  radiometric meaning must be checked before using them as directional model lighting or shadow visibility.
- Existing model poses already contain CPU skinning, all eight supported influence slots, morph deformation,
  native animation-clock sampling, and posed bounds. Shadow rendering must consume the same evaluated pose.

Source GLB: `level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/mm6_demon_textured.glb`.
Runtime GLB: `assets_dev/worlds/mm6/models/mm6_demon.glb`.
Retained native baseline: [three demons](../output/demon_3d_review/three-demons.png).

## Techniques and references

OpenMW reference checkout: `/home/pjasicek/github/openmw`, inspected at revision `ce8a52117c`.
Its core object lighting is Blinn–Phong with optional normal/specular/environment maps and shadows.
GGX metallic/roughness shading below is our adaptation for glTF assets, not a claim about OpenMW's core shader.

| Priority | Technique | Reference and adaptation |
| --- | --- | --- |
| 1 | Per-pixel sunlight and coloured local lights | [OpenMW lighting](../../openmw/files/shaders/lib/core/lighting_fragment_impl.glsl) combines sun and point-light diffuse/specular responses. Feed our existing world-light data to the shared model shader. |
| 1 | Separate diffuse and specular responses | [OpenMW object materials](../../openmw/files/shaders/compatibility/objects.frag) demonstrate the separation. Use GGX and existing glTF metallic/roughness maps in our implementation. |
| 2 | Mesh shadow casting and receiving | [OpenMW shadow setup](../../openmw/components/sceneutil/shadow.cpp) uses cascaded maps; [shadow sampling](../../openmw/files/shaders/compatibility/shadows_fragment.glsl) handles coverage and distance fading. Start with bounded outdoor sunlight shadows. |
| 2 | Environment reflections | [OpenMW object materials](../../openmw/files/shaders/compatibility/objects.frag) use normal-driven reflections. Use a shared sky environment outdoors with roughness-dependent filtering. |
| 1 | Mipmaps and anisotropic filtering | [OpenMW texture filtering](../../openmw/components/resource/scenemanager.cpp) applies consistent model filtering. Reuse our mip/filtering helpers with colour-space and normal-map handling. |

[OpenMW tangent-space normals](../../openmw/files/shaders/compatibility/normals.glsl) and
[animated tangents](../../openmw/components/sceneutil/riggeometry.cpp) are additional quality references.
Retain our derivative-based normal mapping initially; add authored/generated tangent data only if mirrored-UV
and animated-pose checks expose a mismatch with the baked maps.

Keep the existing OpenYAMM render architecture and bounded light selection described in
[rendering comparison](../re_mm8/OPENYAMM_RENDERING_COMPARISON.md) and
[lighting comparison](../re_mm8/OPENYAMM_LIGHTING_COMPARISON.md). Those are historical investigations;
the current sources above determine implementation details. This work does not import OpenSceneGraph or
OpenMW's actor/animation systems.

## Ownership and integration contract

- Extend `engine/models/` for glTF material data and `engine/render/ModelRenderer.*` for shared GPU resources
  and draws. Material evaluation lives in the shared model shaders under `game/shaders/`.
- Outdoor/indoor renderers supply world-specific lighting, visibility, fog, and receiving-surface information.
  They use the same material equations and model rendering implementation.
- Reuse [OutdoorLightingRuntime](../game/outdoor/OutdoorLightingRuntime.h),
  [IndoorLightingRuntime](../game/indoor/IndoorLightingRuntime.h),
  [WorldFxSystem](../game/fx/WorldFxSystem.h), and [texture filtering](../game/render/TextureFiltering.h).
  Move reusable texture preparation to engine scope if needed; avoid duplicated mip generators or engine-to-game
  dependencies. Keep existing CPU FX clustering and bounded light budgets.
- Extend the current renderer data structures directly. Add no forwarding layer, second model owner, or
  parallel lighting system solely for creatures.
- Keep descriptor bindings, table stats, AI, pathfinding, combat timing, collision cylinders, sound ids,
  turn mode, animation clocks, shrink behaviour, picking, outlines, health bars, save/load, and death rules intact.
- Models remain derived presentation instances. Rendering and shadow passes do not advance gameplay or animation.
- Existing unlit, emissive, alpha-mask/blend, fog, and outline behaviour must remain valid. Hidden or collapsed
  death geometry must not become visible or cast unintended shadows.
- Keep resources shared by asset or scene rather than allocating shadow maps or environments per creature.
  Allocate no creature-only shadow/environment resources when the feature has no consumers.

## Phase 0 — Establish repeatable comparisons and data contracts

- [x] Preserve the native baseline and user close-up in `output/creature_3d_rendering_review/baseline/`.
  Use distinct output directories for each candidate pass.
- [x] Record the exact save/state, actor positions, animation phase, game clock/weather, camera, resolution,
  render settings, GPU/backend, and asset/binary hashes used for comparisons. The launcher is a starting point;
  freely moving hostile actors alone do not make a repeatable shading comparison.
- [x] Audit every demon material, including the separate iris/pupil/claw materials. Confirm metallic/roughness
  channel packing, factors, sampler behaviour, UV set, image orientation, and normal conventions.
- [x] Trace the existing sun/sky probe bake and runtime schema. Check
  [outdoor bake](../tools/lighting/bake_outdoor.py) and `OutdoorLightingData.*` for stored direction, normalization,
  exposure, and static visibility. Do not infer a sun direction or visibility mask from arbitrary baked RGB.
- [x] Record baseline CPU/GPU frame times, model skinning/synchronization time, draw calls, transient bytes,
  texture memory, startup/map-load cost, and behaviour with models disabled.
  The retained prototype has CPU timing but no historical GPU timer record. The final enabled/disabled
  comparison conservatively includes the entire GLB rendering cost; the memory comparison separately records
  the known pre-existing image allocation floor. Do not label either as an exact historical prototype delta.

Exit: retained baselines and a documented light-data contract, including any explicit metadata/rebake required
for directional lighting on baked maps. Implementation decisions and performance limits must be recorded here
before judging candidate performance; there are no measured improvement claims yet.

## Pass 1 — Colour, materials, scene lighting, and filtering

### Material and colour pipeline

- [x] Load metallic and roughness factors, the metallic/roughness texture binding, and its supported UV/sampler
  semantics. Respect glTF defaults and channel packing: roughness in G, metallic in B. Validate finite factors
  and bindings; reject unsupported required material features explicitly.
- [x] Treat base-colour texture RGB as sRGB and glTF colour factors as linear. Normal and metallic/roughness maps
  are linear data; alpha is not gamma transformed. Account for images used by more than one texture semantic.
- [x] Evaluate diffuse/specular/emission in linear space using GGX, Fresnel, and energy-conserving diffuse weighting.
  Keep the roughness floor and grazing-angle denominators numerically stable. Preserve explicit unlit materials.
- [x] Define the output contract for our existing display-referred SDR world target: encode the shaded model
  result once, match the existing fog-colour space, and apply cinematic grading once with the rest of the scene.
  Do not change the global backbuffer colour convention and unintentionally reinterpret sprites or HUD textures.
  Record how HDR values are compressed into SDR so highlights retain shape rather than clipping into large patches.
- [x] Tune using authored materials: rough dark skin, matte leather, restrained ivory/bone highlights, and glossy
  eyes. Metallic response belongs to metallic surfaces. Fix inappropriate asset values through material data,
  not shader branches keyed to demon names. Preserve the requested red iris and black pupil colours.

### Lighting

- [x] Supply explicit direct-light direction, intensity, and colour, separately from ambient/indirect illumination.
  Do not normalize a zero light vector or discard intensity by normalizing an intensity-scaled vector.
- [x] On unbaked outdoor maps, use the existing atmosphere's sunlight, day/night, weather, and sky inputs.
- [x] On baked maps, combine authoritative sun/sky information with normal-dependent model lighting. If probes
  contain pre-integrated irradiance, add the metadata needed to recover a correct lighting contract rather than
  interpreting it as incident radiance. Version/regenerate affected lighting data explicitly if required.
- [x] Reuse bounded local-light selection against posed model bounds. Initially retain existing outdoor/indoor
  budgets (8/12); evaluate selected lights per fragment with the normal map. Preserve receiving-sector rules,
  event-driven light state, stable selection, existing falloff, and coloured-light settings.
- [x] Feed indoor models the room lighting frame, including eligible static, decoration, torch, and FX sources.
  Models do not have the world geometry's baked vertex illumination; do not omit static lights because that
  geometry excludes already-baked sources from its dynamic draw list. Avoid counting a source twice.

### Texture quality and normal fidelity

- [x] Upload complete mip chains and use consistent filtering/sampler settings. Never declare mip levels while
  supplying only the base-level bytes. Reuse existing preparation instead of adding a second uploader.
- [x] Generate colour mips in the correct space, retain alpha-mask coverage where needed, and handle normal-map
  vector averaging/normalization. Check roughness minification for distracting highlight shimmer.
- [x] Validate mirrored UVs, grazing views, and animated normal-map orientation. Add tangent attributes and skin
  them consistently with the model only if the existing derivative path fails those checks.

Exit: the fixed-camera close-up visibly has directional shape and distinct materials; camera/light movement changes
highlights; daytime, shade, night, torchlight, spells, and indoor lighting behave coherently. Textures remain stable
at distance. There are no flat-colour eyes, uniformly oily skin, gamma fringes, or shader NaNs.

## Pass 2 — Animated outdoor sunlight shadows

- [x] Add shared, limited-distance cascaded sunlight shadow maps. Start with two cascades; set resolution and
  coverage from the close-up/mid-distance review and recorded GPU budget. Use filtered comparisons, bias,
  distance fading, and stable light-space placement to control acne, detached shadows, and camera shimmer.
- [x] Render the same evaluated skinned/morphed pose into the shadow pass and colour pass. Evaluate poses once;
  avoid one skinning/animation update per cascade. Respect hidden geometry, alpha masking, culling, and valid bounds.
- [x] Make the model receive shadows on direct diffuse and direct specular terms; do not suppress ambient sky fill
  or emission as if they were direct sunlight.
- [x] Make terrain and relevant world surfaces receive animated actor shadows through their existing render paths.
  Retain static geometry batching. A ground blob alone does not satisfy silhouette or self-shadow acceptance.
- [x] Define caster/receiver ownership on baked maps: baked static occlusion remains authoritative; moving actors
  add dynamic occlusion. Do not multiply the same static shadow into a sun term twice. For unbaked maps, include
  relevant nearby static casters if needed to meet world-shadow acceptance.
- [x] Register explicit bgfx view ordering before world colour rendering, accounting for water reflection views
  and grading. Respect backend depth-range/origin conventions; never sample a depth target still being written.
  Keep one owner for shadow resources and their resize/map-transition/teardown lifecycle.
- [x] Verify walking, attacks, hit reactions, fidget, and death. The plume's visibility and `NoCorpse` disappearance
  must remain synchronized with ordinary actor state. Skip translucent effects as opaque casters unless explicitly
  supported by their material contract.

Exit: sunlight produces attached ground silhouettes and useful self-shadowing on brows, ears, spikes, and limbs.
Moving actors and camera turns do not cause obvious flicker, cascade seams, detached silhouettes, or doubled static
darkening. Night disables direct-sun shadows. Models-disabled scenes do not acquire creature-shadow pass costs.

The first release covers outdoor directional sunlight shadows. Indoor torches and spells illuminate models in
Pass 1; shadows cast by individual point lights are a later extension.

## Pass 3 — Environment reflections

- [x] Add a scene-shared sky environment outdoors, driven by the existing atmosphere. Filter reflected radiance
  by roughness and combine it with Fresnel/material response. Use a correct diffuse/specular energy split.
- [x] Prefer an existing suitable environment resource/generator; otherwise prepare one bounded shared environment
  and its filtered mip levels. Update only when its atmosphere inputs change; do not capture a cube per creature.
- [x] Keep reflection brightness consistent with time, weather, shade, and ambient visibility. Rough skin receives
  broad, faint response; glossy eyes and smoother surfaces receive clearer highlights.
- [x] Define a subdued indoor environment treatment using room illumination. Do not show a bright exterior sky
  through enclosed-room materials. Local reflection probes are deferred.
- [x] State the coverage accurately: a shared sky environment reflects sky lighting, not nearby buildings, other
  actors, or the creature itself. Scene-local reflections would require additional authored/captured probes.
- [x] Validate resource sharing, mip transitions, resize, map changes, and day/night updates alongside fog/grading.

Exit: glossy surfaces have natural view-dependent response beyond direct-light glints. The body is not uniformly
shiny, dark rooms/night do not produce glowing reflections, and reflection detail remains stable in motion.

## Validation and completion criteria

Use native GPU captures, inspect the images, and retain logs/settings. A screenshot proves appearance; it does
not establish frame-time cost. Use separate baseline/pass directories under `output/creature_3d_rendering_review/`.

| Check | Required evidence |
| --- | --- |
| Fixed close-up | Same camera/state before and after; visible facial shape, skin/leather/bone separation, correct iris/pupil colour. |
| Camera orbit | Front/profile/three-quarter views; highlights and reflections move naturally without texture-space seams. |
| Lighting changes | Daylight, shade, night, torchlight, coloured spell light, and an indoor room; no full-ambient model shortcut. |
| Animation | Walk, attack, hit, fidget, death, and reset; shadows follow the evaluated pose and disappear with the actor. |
| Distance | Close, mid-distance, and distant views; reduced texture crawl and no distracting specular/cascade popping. |
| Gameplay parity | Three normal table actors retain AI, pathfinding, combat timing, turn mode, picking, shrink, sounds, save/load, and `NoCorpse`. |
| Renderer regression | Existing sprite creatures, shared model fixture, unlit/emissive/alpha materials, fog, outlines, HUD, grading, and water ordering retain valid rendering. Include affected MM6/MM7/MM8 consumers. |
| Lifecycle | Map transitions, restore/reset, resize/fullscreen, feature changes, and shutdown release/recreate resources correctly. |
| Performance | Paired native CPU/GPU timings, p50/p95 frame times, draw calls, texture/transient/target memory, and startup/map-load cost. Measure models enabled and disabled. |

Initial incremental budget for upgrading the existing GLB prototype on the retained NVIDIA/OpenGL desktop:
GPU p50 +2 ms, GPU p95 +4 ms, and GPU memory +128 MiB. Record the exact
hardware/resolution with each paired run.
Acceptance requires the completed passes to fit that recorded budget and models-disabled overhead to remain within
measurement noise. The prototype's earlier 1.8–1.9 ms model synchronization observation is a baseline clue, not a
GPU budget or crowd-performance guarantee. Measure an additional modest crowd for scaling; optimize only a demonstrated
bottleneck. Current work remains the normal desktop build; do not start a Vulkan rebuild.

For pure material parsing, colour/mip preparation, and shadow math, add focused doctest coverage for meaningful
edge cases. GPU captures are required for actual shading and shadows. Reuse runtime actor checks for simulation parity:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*ModelAnimation*,*actor AI*,*launch directives*'
OPENYAMM_REGRESSION_FILTER=mm6_demon_actor_models \
  ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
```

Add focused filters for the material/lighting/mip/shadow tests introduced during implementation; the commands above
cover the existing model/gameplay baseline, not future shader acceptance.

Native interactive review:

```sh
./tools/run_demon_3d_test.sh
```

Timed native capture from the established trial camera:

```sh
./tools/run_demon_3d_test.sh --warmup 5 --seconds 20 \
  --set debug.screenshot_path=/home/pjasicek/github/OpenYAMM/output/creature_3d_rendering_review/pass1.png \
  --set debug.screenshot_delay_seconds=4
```

For exact comparisons, use the captured-state/tour procedure established in Phase 0; hostile actors can move in the
interactive launcher. [Desktop runs and native tours](../tools/RUN_GAME.md) describe isolated saves, pose units, one-shot
capture settings, and retained run receipts. Record live animation separately from tours that hold simulation.

Completion requires all three pass exit criteria, inspected comparison captures, passing focused tests and runtime
checks, documented performance results, and a reusable material path with no demon-specific shader logic. A build
or successful GLB load alone is not completion.

## Deferred work

GPU clustered lighting, SSAO, bloom, GPU skinning, per-point-light shadows, local reflection probes, and a global HDR
world-pipeline conversion are separate follow-ups. Existing CPU light clustering remains in use. Add these features
only for a demonstrated visual or performance need; they are not prerequisites for the three passes above.

## Progress record

- [x] Existing MM6 demon gameplay/model integration and native review baseline.
- [x] Local OpenMW technique comparison and this implementation plan.
- [x] Phase 0: reproducible comparisons, material/probe contracts, and numeric performance budget.
- [x] Pass 1: colour, materials, scene lighting, filtering, and visual/regression evidence.
- [x] Pass 2: animated sunlight mesh shadows and visual/regression evidence.
- [x] Pass 3: shared environment reflections and visual/regression evidence.
- [x] Final completion evidence and runtime documentation update.

### Implementation evidence — 2026-10-05

- Shared glTF material factors/samplers, linear-colour GGX, bounded outdoor/indoor point lights, and semantic
  mip preparation are implemented. The pass 1/2 focused unit run passed 104 cases and 4,963 assertions.
- The lighting producer writes v5 explicit sun direction, direct response, measured visibility, indirect-sun
  probes, and separate direct-only sunlight surface pages. All 42 installed paired-source MM6/MM7/MM8 bakes
  were migrated using their exact profiles. Existing total sun/sky surface pages and sprite probe samples are
  byte-identical to their original v3 data. Direct pages remain compressed in CPU memory until used by a shadow
  receiver. See [direct migration report](../output/creature_3d_rendering_review/sun_direct_migration/batch-report.json),
  [preservation audit](../output/creature_3d_rendering_review/sun_direct_migration_preservation.json), and
  [lighting contract](../tools/lighting/baked_outdoors/FORMAT.md).
- Body metallic and eye roughness were corrected in material data. Geometry, animation, base colour and normal
  images are unchanged; see [tuning record](../output/creature_3d_rendering_review/material_tuning/record.json).
- Inspected native OpenGL captures: [baseline profile](../output/creature_3d_rendering_review/baseline/tour/02-closeup.png),
  [first material pass](../output/creature_3d_rendering_review/pass1/tour/02-closeup.png), and
  [tuned front view](../output/creature_3d_rendering_review/pass1_tuned/tour/03-front.png). Native run receipts are
  retained beside each capture set. The additional front camera has no historical paired capture yet.
- The two existing demon simulation/death and indoor-binding regressions pass with the tuned asset and v5 data.
- Two stable, 2048-pixel sunlight cascades cover 1,024/4,096 world-unit radii. They use the same evaluated pose
  and one shared transient vertex upload per deformed primitive across shadow and colour draws. Filtered shadow
  comparisons affect direct illumination only. The two colour/depth targets use 48 MiB and are released when
  sunlight is disabled or no visible opaque/masked model caster remains.
- Terrain, buildings and ground vegetation receive actor shadows. Baked receivers subtract occluded direct-only
  sunlight while preserving existing sky and bounced illumination. Unbaked terrain/building draws attenuate their
  direct sunlight without suppressing local lights. Current installed classic outdoor maps use their authoritative
  baked static occlusion; additional static casting for newly authored unbaked scenes is not implemented.
- Inspected [normal ground-shadow capture](../output/creature_3d_rendering_review/pass2_ground/detail/01-ground-front.png)
  and [matching disabled capture](../output/creature_3d_rendering_review/pass2_ground_disabled/detail/01-ground-front.png).
  A temporary visibility-only shader confirmed detailed body/ear/spike/claw silhouettes and was removed before
  the final build. Short standing-pose measurements confirmed target allocation and shared pose uploads; they
  do not replace controlled final performance or animated-shadow acceptance.
- Pass 3 reuses the retained sky image as a repeating cloud plane, prepares one scene-shared 128-pixel linear
  RGBA16F cube with eight GGX-filtered mip levels, and integrates the GGX/Smith Fresnel response into a 64-pixel
  BRDF lookup. Sky identity changes rebuild the cube; clock/probe/weather tint changes use per-draw illumination.
  This is sky-only lighting, with faint lower-hemisphere fill, not reflection of nearby buildings or actors.
  Cloud drift stays fixed in the filtered environment. Indoor models use room ambient illumination and a constant
  environment instead of an exterior image. All environment textures are released when no rendered model remains.
- Environment colour/orientation/mip and integrated-energy checks pass. Inspected native NVIDIA OpenGL captures
  include the [combined front](../output/creature_3d_rendering_review/pass3/tour/03-front.png),
  [eye/face detail](../output/creature_3d_rendering_review/head_detail/tour/01-head-front.png),
  [quarter view](../output/creature_3d_rendering_review/head_detail/tour/02-head-quarter.png), and
  [orbit/distance series](../output/creature_3d_rendering_review/orbit/captures/front.png). The red iris/black pupil
  retains small white glints; skin and leather remain rough. The derivative normal path shows no obvious
  inversion at the inspected grazing views or animated poses; authored tangents were not needed.
- Scene-light checks include [baked shade](../output/creature_3d_rendering_review/shade/tour/01-shade-front.png),
  [night](../output/creature_3d_rendering_review/night/tour/03-front.png),
  [Torch Light](../output/creature_3d_rendering_review/actor_lights/captures/torchlight.png), and an actual
  [Fire Bolt passing an ordinary actor](../output/creature_3d_rendering_review/actor_lights/captures/firebolt-middle.png).
  The bolt produces moving orange light on the skin. Devil Spawn's native fire immunity still applies.
  [Silver Helm Outpost](../output/creature_3d_rendering_review/indoor/tour/02-room-close.png) uses room illumination
  without an exterior reflection image or sunlight shadow targets. The
  [unbaked-lighting check](../output/creature_3d_rendering_review/unbaked/tour/03-front.png) also renders successfully.
- Paused native-clock captures cover Standing, two walking phases, Attack, Hit, Fidget, death start/plume and
  removal in [animation review](../output/creature_3d_rendering_review/animation_review/captures/attack.png).
  Shadow geometry follows the evaluated pose. Stopping the last model releases 48 MiB of shadow targets and
  the direct-receiver/environment textures. The plume is not treated as an opaque caster.
- The [shared fixture](../output/creature_3d_rendering_review/orbit/captures/shared-fixture.png) checks animation,
  unlit blend and shared materials; the
  [masked/emissive fixture](../output/creature_3d_rendering_review/map_lifecycle/captures/masked-emissive.png)
  checks cutouts and emission. Native transitions through MM6 interiors, MM7 Harmondale and MM8 Dagger Wound
  recreate the appropriate renderer resources. The fixture's deliberately placed world coordinates are a
  rendering check, not an actor floor-placement test.
- The latest focused doctest run passes 152 cases and 68,446 assertions. One additional Ravenshore stairs test
  cannot load its map after a concurrent dimension-travel event edit invalidated its lighting dependency.
  That unrelated case was excluded from the focused renderer run; dependency validation remains enabled and
  the event edit was not reverted. The two demon simulation/death and indoor-binding regressions pass.
- Controlled sequential, VSync-off, 1600×900 NVIDIA RTX 3060 Ti/OpenGL runs compare the same held camera and
  ordinary table-actor formation. The [performance report](../output/creature_3d_rendering_review/performance/report.json)
  retains all sampled windows and resource counts. Values below are medians of one-second window percentiles,
  excluding startup, events and capture windows; they are not global run percentiles.

  | Scene | CPU p50 / p95 | GPU p50 / p95 | Draws | Transient vertices |
  | --- | --- | --- | --- | --- |
  | Three sprite actors | 0.352 / 0.379 ms | 0.323 / 0.363 ms | 263 | 0.112 MiB |
  | Three GLB actors | 2.039 / 2.213 ms | 1.471 / 1.712 ms | 352 | 2.667 MiB |
  | Six GLB actors | 4.109 / 4.254 ms | 2.479 / 3.012 ms | 444 | 5.223 MiB |

  The full three-model path costs +1.149 ms GPU p50 / +1.349 ms p95 versus sprites, already within the
  renderer-upgrade targets. Three and six models share identical texture/target allocations. CPU skinning
  scales with actor count and remains the existing crowd ceiling; six fit the current transient buffer.
  The complete GLB comparison adds 164.8 MiB versus sprites. The old uploader already owned at least 80 MiB
  for the same five embedded 2048² RGBA8 images, so the renderer upgrade's conservative memory upper bound
  is 84.8 MiB, within 128 MiB. This is an allocation bound, not an invented historical GPU measurement.
  Historical prototype GPU timers were not retained; the old CPU observation alone cannot supply them.
  Scene startup was 5.41 / 5.51 / 5.61 seconds for sprites / three / six. First-use GLB/mip/environment
  preparation still produces an approximately one-second hitch; these steady-state numbers exclude it.
- Native live combat retains table-driven movement, ranged fire attacks, picking/health bars and
  [turn mode](../output/creature_3d_rendering_review/live/captures/turn-mode.png), then returns to
  [real time](../output/creature_3d_rendering_review/live/captures/realtime.png). Walking and attacks render the same
  moving shadow pose; spell lights move across the model without changing its ordinary gameplay identity.
- The native display tour exercises 1600×900 → 1280×720, Fullscreen, then Windowed at 1280×960.
  Inspected [resized](../output/creature_3d_rendering_review/lifecycle_ui/captures/resized-game.png) and
  [returned-window captures](../output/creature_3d_rendering_review/lifecycle_ui/captures/restored-game.png)
  retain materials, mesh shadows, sky, grading and HUD. These are private launcher settings, not changes to
  the user's normal display configuration. A separate 1600×900 run retains explicit
  [Fullscreen settings](../output/creature_3d_rendering_review/fullscreen_lifecycle/captures/fullscreen-settings.png),
  [Windowed settings](../output/creature_3d_rendering_review/fullscreen_lifecycle/captures/windowed-settings.png),
  and their corresponding game captures after confirmation.
- The final lifecycle run hides/shows the last model, enters Silver Helm Outpost, returns to New Sorpigal,
  respawns and stops the model. Inspected [map return](../output/creature_3d_rendering_review/final_lifecycle/captures/outdoor-return.png)
  and [removal](../output/creature_3d_rendering_review/final_lifecycle/captures/removed.png) are valid. The
  [resource record](../output/creature_3d_rendering_review/final_lifecycle/resources.json) shows target storage falling
  from 63,948,800 to 13,617,152 bytes when hidden/removed, then returning on show; direct-receiver/environment
  textures release another 10,629,104 bytes. Indoor target storage remains 11,520,000 bytes without the CSM.
  Whole-scene texture totals also include the existing world/sprite caches; these differences identify the
  creature-only resources, not a promise to flush every cached map texture.
- Normal desktop build and scoped diff checks pass. The reusable trial launcher enables sunlight shadows and
  retains the opt-in actor-model setting. No Vulkan rebuild or runtime package repack was performed.

### Accepted scope and known limits

The three passes meet the native desktop visual, gameplay, lifecycle and recorded steady-state budget checks.
The unrelated Ravenshore event/bake dependency failure above remains a separate content-maintenance issue;
the renderer does not bypass it. Historical GPU baseline timing was unavailable, so the conservative comparison
basis is explicit. CPU skinning and first-use preparation remain measured limits, not a large-crowd guarantee.

This release has outdoor sunlight mesh shadows and sky-only reflections. Point-light shadows, local probes,
animated cloud drift in reflections, extra static casters for new unbaked maps, and the other deferred features
remain outside this implementation. Installed classic maps keep their authoritative baked static occlusion.

### Empty-scene performance correction, 2026-10-05

The user's stationary New Sorpigal camera exposed a regression missed by the earlier creature-versus-sprite
acceptance comparison: both sides of that comparison already carried mesh-shadow receiver code and bindings.
Ordinary world programs now compile without receivers and select matching shadow variants only with active
casters. Inactive/duplicate world bindings are skipped; empty model rendering skips uniform setup.
Repeated native comparisons recover 7–11% FPS at the reported view while keeping enabled shadow shaders
byte-identical. See the [regression report](../output/performance/sorpigal_mesh_receiver_20261005/REPORT.md)
for measurements, limitations and runnable shader verification.
