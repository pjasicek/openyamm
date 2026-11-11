# Shared model, animation and effect system: implementation plan

Status: initial rigid-model and one-shot-effect scope implemented, 2026-09-22. The acceptance evidence, measured
budgets, full-suite caveat, and remaining fidelity limits are recorded in `IMPLEMENTATION_CONTRACT.md` and
`VALIDATION_REPORT.md`. Repository-relative paths refer to OpenYAMM unless noted.

## Intended outcome and agreed scope

Introduce reusable GLB/glTF model assets, model instances and node animation, then a shared
effect player that uses those facilities. Effects spawn at a world position with optional
orientation and scale. The same model foundation must support later static, animated or
script-controlled props and eventual 3D monsters without replacing the asset/instance API.

Initial delivery includes static and rigidly animated models, invisible animated attachment
nodes, sprite/particle effects and sound. It does **not** include mesh skinning, monster visual
replacement, actor animation state machines, animated collision or new MM9 spell mechanics.
Future monster support is an extension milestone, not a hidden requirement of this work.

Runtime asset decisions:

- GLB preferred; glTF with package-relative buffers/images also supported within a documented subset.
- PNG for textures. DTX is an offline import source only; no DTX runtime dependency.
- Retain SPR frame lists and FXF recipes where useful. The investigated recipe is `SPELLS.fxf`;
  the user's mention of “sfx” is interpreted as these effect definitions, not a newly identified format.
- WAV for sound. No ABC runtime dependency and no SCR interpreter.
- MM9 assets and compatibility behavior remain world/mod-scoped. Generic models/effects may
  be owned by base content or any mounted world/mod through normal namespaced asset identifiers.

The existing browser viewer remains a research tool and regression aid. Its playback is not
an original-game visual-parity oracle. Read [the investigation](README.md) and
[the integration assessment](OPENYAMM_INTEGRATION_ASSESSMENT.md) for evidence and remaining uncertainties.

## Existing foundations and reuse boundaries

| Existing code/data | How it informs this implementation |
| --- | --- |
| `engine/AssetFileSystem.*`, `ImageAssetLoader.*`, bgfx context, audio mixer | Shared packaged/development asset reads, PNG loading, rendering and audio foundations |
| `game/fx/WorldFxSystem.*`, `ParticleRenderer.*`, `WorldFxRenderResources.*` | Shared world-FX lifecycle and rendering insertion points; preserve current recipes and behavior |
| `game/gameplay/GameplayFxService.*` | Existing gameplay-facing FX requests; connect named effects without a second gameplay FX owner |
| `game/indoor/IndoorRenderer.cpp`, `game/outdoor/OutdoorRenderer.cpp` | World-specific visibility/light inputs and submission hooks; shared model/effect logic stays outside them |
| `editor/import/ObjModelImport.cpp` | Existing cgltf dependency and static bmodel import; this is not an animated-model runtime |
| `tools/mm9_import_discovery/convert_abc_model.py` | Existing OpenYAMM converter to extend, rather than create another competing converter |
| OpenMM9 `tools/import/convert_abc_model.py` | Closely related converter with native scale and different texture-alpha policy; review differences deliberately |
| OpenMM9 `game/render/AnimatedModelAsset.*`, `AnimatedModelRenderer.*`, `AbcModelAsset.*` | Behavioral/structural reference for animation, node attachment and rendering; implement new OpenYAMM code |
| OpenMM9 `artifacts/model_exports/models/spells/{bugpath,wormpath,tube}.glb` | Useful existing samples, not automatically accepted canonical runtime exports |

OpenMM9's active runtime favors native ABC/DTX, while this plan deliberately uses imported assets.
Do not carry its DAT dependencies, source-file access or native-only assumptions into shared code.
Existing MM9 model documentation currently calls DTX the runtime texture source: revise that
contract for migrated model assets when implementing the import milestone. Do not silently
change unrelated world-texture pipelines or hand-edit generated sidecars.

## Ownership and proposed source layout

Names are proposed responsibilities, not a requirement to introduce one wrapper per row.

| Owner | Responsibility |
| --- | --- |
| `engine/models/ModelAsset.*`, `GltfModelLoader.*` | Immutable model data: primitives/materials, hierarchy, clips, named attachment nodes, bounds |
| `engine/models/ModelInstance.*`, `ModelAnimation.*` | Root transform, independent playback/pose, visibility, generation-checked instance handles, evaluated node transforms |
| `engine/render/ModelRenderer.*` | Shared model GPU resources and draw submission, usable by gameplay and editor |
| `game/fx/EffectDefinition.*`, `EffectSystem.*` | Definition lookup, effect instance lifecycle, timeline/component simulation, emitter/particle ownership |
| `game/fx/EffectRenderer.*` or a focused extension of existing rendering | Render evaluated effect quads/material state without the old particle renderer's automatic fades/tuning |
| `game/fx/import/` | Bounded SPR/FXF parsing and compilation into shared effect definitions; no MM9 gameplay logic |
| `game/mm9/` and MM9 content descriptors | Native property/opcode interpretation and compatibility profile selection |
| Existing gameplay FX service, scene runtimes and editor | Calls and world inputs into the shared services; no duplicate model loader or animation player |

Engine services must not depend on gameplay, MM9 tables, DAT objects, or Lua event state.
Gameplay effect instances use the engine animation service for GLB paths. They do not maintain
an independent copy of model animation sampling. Their audio requests use the existing game
audio service, which owns mixer playback. Model and effect resources have one owner each.

Keep CPU asset data and GPU residency separate so headless validation does not need a renderer.
Use the mounted filesystem for GLB buffers and textures, including ZIP packages; do not depend
on `resolvePhysicalPath()` succeeding. Define one cgltf implementation translation unit and
update the existing editor consumer/linking so there are no duplicate implementation symbols.
Reuse or move only the shader-loading support required by shared model rendering; avoid an
engine-to-game dependency and avoid duplicating shader loaders.

## Public behavior contract

Illustrative API, to adapt to repository naming and handle conventions:

```cpp
EffectSpawnParams params;
params.position = {x, y, z};
params.rotation = identityRotation();
params.scale = 1.0f;
EffectHandle effect = effectSystem.spawn("mm9:column_of_fire", params);

effectSystem.setTransform(effect, position, rotation);
effectSystem.stop(effect, EffectStopMode::Drain);

ModelInstanceHandle prop = modelInstances.create("example:rotating_prop", transform);
modelInstances.play(prop, "rotate", PlaybackMode::Loop);
```

Contracts to implement and document:

- Default rotation means the authored orientation: Column of Fire stands vertically in OpenYAMM.
  Store rotations as quaternions; optional yaw/pitch helpers specify radians and their axis convention.
- Effect scale is uniform initially. Models support local TRS; handle nonuniform scale, normal
  transforms and reflected winding correctly within the supported subset.
- A moved emitter leaves already emitted world-space particles behind. Local-space particles,
  following components and fixed components are explicit definition semantics.
- World anchors and optional model-node anchors use stable handles. Resolve names when binding;
  do not search strings across skeletons per particle or frame. Duplicate/missing node names
  are diagnosed; absence of a requested body node is not silently replaced with the origin.
- Immediate stop removes components and sound handles. Drain stops emission and follows the
  definition's particle/sound shutdown rules. Native parent-clearing behavior is a compatibility rule.
- Destruction, map unload, pause and world unmount have defined teardown behavior. No dangling
  actor/model pointers, playing orphan sounds or stale resources after an asset mount changes.
- Multiple instances share immutable assets/textures but have independent clocks, transforms and seeds.
- Transient effects are not added to saves initially. Persistent scripted props use authored IDs;
  persistent playback/save behavior is a later explicit feature, never serialized raw handles.

## Asset pipeline and format contract

### Modern model import

Extend the existing converter with explicit export modes: full reference export, rigid/static
model export when valid, and **animation-path export**. Path mode preserves required nodes,
ancestors, names and clips, omitting helper mesh geometry and skin declarations. Keep full source
exports available for future skinning; do not flatten away information in authoritative sources.

For each imported asset record source path/hash, converter/schema version, selected LOD/clip
policy, coordinate/unit conversion, material bindings and conversion warnings. Regeneration
must be deterministic. Fail unsupported data with an actionable diagnostic instead of fabricating
geometry, normalizing invalid values silently or treating every skinned mesh as rigid.

Choose one documented glTF coordinate/unit convention and one conversion at the OpenYAMM
placement boundary. Respect glTF's Y-up/metre convention for newly canonical exports; explicitly
calibrate MM9 source units before assigning metre values. Audit existing exports rather than
assuming they already use metres. OpenYAMM's existing MM9 conversion uses scale 2.56 and an
X/Z/Y mapping, while OpenMM9 uses native scale 1.0. The axis swap changes handedness. Test
positions, rotations, winding, normals, emitter offsets/velocities/radii and audio distances
together against existing map placement. No independent sprite-size correction or double scaling.

### Texture conversion

Convert DTX to PNG without changing decoded RGB or alpha. Keep color-space intent, alpha usage,
filtering/wrapping and relevant source flags in explicit texture/material metadata. Do not apply
the model converter's blanket opaque-alpha repair to sprite textures. Do not infer additive
blending from filenames, destroy RGB under zero alpha, or premultiply on import implicitly.

Record every source mip and conversion decision. Initial runtime can use generated mipmaps
under an explicit policy, with the fidelity difference documented. Preserve original decoded
mips as import artifacts so future exact-mip upload or KTX2 packaging requires no new RE.
PNG is the initial runtime format; KTX2/GPU compression is a separate optional optimization.
Do not ship unsupported texture flags as if they were implemented rendering behavior.

### Retaining SPR and FXF

SPR/FXF records still refer to `.dtx` and `.abc` paths. Generate a versioned **explicit binding
manifest** from those source references to namespaced PNG/GLB/WAV resources and frame lists.
Keep original recipes immutable; the runtime reader resolves through the engine content's
manifest and compiles them into typed effect definitions. Do not implement extension guessing
or absolute external-asset fallbacks. Preserve original source references in diagnostics.

Implemented engine/base package layout:

```text
assets_dev/engine/effects/mm9/
  library.yml                     # declarations, compatibility profile and capabilities
  capabilities.yml
  resource_bindings.yml           # exact legacy reference -> packaged resource mapping
  source/spells.fxf
  sprites/*.yml
  textures/*.png
  audio/*.wav
  models/*.glb
  import/                         # hashes, decoded source mips, and conversion reports
```

The package is engine-owned so all worlds may spawn the promoted effects; `mm9:` ids retain source provenance. Model
`.model.yml` sidecars may preserve
material/clip metadata that glTF does not express; one authoritative field owns each setting.
For newly authored effects use a small versioned YAML definition compiling into the same runtime
types. There is one simulator, not a native-FXF player plus a separate custom-effects player.

## Runtime capabilities and fidelity boundaries

### GLB/glTF first supported subset

Support triangle meshes, indexed and non-indexed primitives, embedded or package-relative PNG,
node hierarchy, static matrices, animated TRS, multiple named clips, and STEP/LINEAR animation.
Support nodes without meshes and multiple instances of a mesh. Evaluate hierarchies in dependency
order, regardless of JSON node order. Use correct quaternion interpolation and clip end/loop rules.
Bounds must account for instance transforms and animated rigid node movement.

Reject unsupported required extensions, cubic animation, morph targets and visible skinned
meshes explicitly at first; allow animation-only imports to omit skin/mesh payload deliberately.
Do not accept unsupported interpolation as linear. Future feature additions extend this contract.
Support a documented simple textured/unlit material subset plus explicit alpha mask/blend and
double-sided behavior. Do not claim full glTF PBR rendering or apply its default material model
blindly to legacy FX. Basic opaque models must retain usable lighting/normals for later props.

### Effect components

Start with SpriteSystem, Sprite, Null/transform, animation-path nodes and timed sound. Add optional
rigid model components using the same general model renderer. An effect that requires a visible
deforming mesh remains unsupported or has an explicitly named authored approximation.

The supplied FXF contains 48 groups and 176 keys, with only five component classes. 38 groups
contain no Model key, but some request actor bones. Track capabilities per recipe: supported,
missing asset, needs body anchors, needs mesh deformation, or unresolved native behavior. Do not
equate “parsed all 48” with “reproduced all 48”. Ghost/Blobby have known missing source assets.

Compile numeric selectors, typed properties and full color/scale/motion curves once. Preserve
distinct group, key, particle and sprite clocks. Recovered MM9 behavior includes cached emission
samples, unnormalized wind, inverted transparency, detail scaling, once-per-update emission,
per-update rotation, early expiry and the short-lifetime color quirk. Keep them explicit in the
MM9 compatibility profile. Generic authored effects use documented predictable time-based rules.

Choose a named MM9 reference update rate, initially 60 Hz for reproducible previews, and retain
30/120 Hz diagnostic modes. This is a presentation policy, not a claim that original MM9 was
fixed at 60 Hz. Keep native no-catch-up emission within each compatibility tick; specify engine
accumulation limits and interpolation separately. The existing MM6–MM8 30 Hz particle update
and its tuning remain unchanged. Finish native loop/continuous-key behavior before declaring
looping MM9 recipes supported; the browser's whole-effect replay is not that behavior.

Use material state to choose sprite lighting, alpha operations, blend/depth behavior and fog.
Sort transparent submissions appropriately; batching must not reorder incompatible alpha draws.
Normal and additive materials need independent validation. The native texture-stage details
are not completely recovered: represent verified state, document approximations, and avoid
inventing per-spell brightness/size corrections to hide incomplete renderer semantics.

Audio uses instance handles and honors start, stop, loop and volume. Extend existing playback
options for pitch and inner/outer radii with defaults preserving current callers. Source-data
parameters must survive import even where the exact native attenuation curve remains unverified.
Do not automatically make all sounds follow moving emitters; use the native component's actual
position-update semantics where established. Add scheduling/cleanup checks at pause and teardown.

## Milestones and completion gates

### M0 — Contract, fixtures and baseline

- [x] Record representative original assets/hashes and current MM6–MM8 behavior/performance baselines.
- [x] Lock supported glTF subset, coordinate/unit policy, alpha/mip policy and content bindings.
- [x] Prepare tiny authored fixtures: textured rigid mesh, out-of-order hierarchy, animated empty
  node, two clips, valid static matrix, transparent material and explicit unsupported features.
- [x] Select MM9 fixtures: Column of Fire, a standalone Sprite, multiple emission shapes and Bugpath.

Gate: authoritative contracts and fixture expectations exist; no engine behavior changes.

### M1 — Deterministic imported assets

- [x] Extend the existing converter with path-only output and explicit unsupported rigid/deformed cases.
- [x] Add pixel-preserving DTX-to-PNG effect conversion and exact SPR/FXF resource bindings.
- [x] Update relevant model export documentation/sidecars without changing unrelated imports.
- [x] Validate hierarchy/clip preservation, PNG channels, frame order and deterministic regeneration.
- [x] Compare converted Bugpath/Wormpath node trajectories with source ABC evaluation at keys and
  between keys; verify names and coordinate transforms. Retain all warnings in an import report.

Gate: the first effects resolve entirely from packaged modern textures/models plus SPR/FXF/WAV;
runtime paths reference neither ABC/DTX nor the external OpenMM9 checkout.

### M2 — Shared model asset loading and node animation

- [x] Implement asset loading through AssetFileSystem, immutable caches and independent instances.
- [x] Implement validated hierarchy evaluation, named clips, STEP/LINEAR sampling and node handles.
- [x] Wire cgltf ownership/build dependencies once; cover GLB and external-buffer glTF from ZIP.
- [x] Reject unsupported features and malformed assets without partial, misleading success.

Gate: headless tests demonstrate correct transforms, independent instances, loop/end boundaries,
package lookup and teardown. No skinning state is allocated for rigid or node-only assets.

### M3 — Shared model rendering and inspection

- [x] Add bgfx buffers/textures/materials, transformed bounds, opaque/masked/transparent submissions.
- [x] Integrate small indoor/outdoor draw hooks using shared renderer and explicit world lighting inputs.
- [x] Add a model inspector in existing debug/editor infrastructure using the same runtime services:
  orbit camera, clip selection, play/pause/scrub, axes/node markers and diagnostics.
- [x] Exercise an ordinary authored prop and an invisible animated node with a visible marker.

Gate: one ordinary rigid model and one animated prop work in both map types, with correct depth,
orientation and materials. Editor and gameplay use the same asset and animation implementation.

### M4 — Named effect player and Column of Fire

- [x] Implement shared definitions, instance handles, transform updates, stop/drain and component clocks.
- [x] Implement sprite resources, emission/tracks, deterministic seeds and MM9 timing profile.
- [x] Connect audio instance lifecycle, material evaluation and sorted quad submission.
- [x] Add debug commands/inspector to list, spawn, pause, scrub, replay and stop effects.
- [x] Spawn Column at arbitrary positions, default upright orientation, rotated orientation and scale.

Gate: original four emitters and sound execute as a complete in-engine sequence with no model
dependency. Verify recorded particle/timing expectations and captured views in indoor/outdoor maps.
Changing FPS policy demonstrates the expected differences without modifying MM6–MM8 effects.

Validation note: the original Column capture used an indoor-looking MM9 ODM scene because the MM9 map package has no
BLV maps. The promoted engine library can now be spawned directly in an MM6–MM8 BLV without a cross-world fallback;
the shared indoor hook is also covered by teardown tests and MM6–MM8 BLV lifecycle scenarios.

### M5 — Paths, supported library coverage and gameplay hooks

- [x] Attach emitters/sprites to GLB nodes using shared animation instances; validate Firefly/Bugpath.
- [x] Expand supported recipes and publish a per-effect capability/known-difference report.
- [x] Verify moving roots, linked parents, explicit missing-body-anchor handling and native shutdown.
- [x] Resolve continuous-loop semantics for supported looping recipes or label them unsupported.
- [x] Add shared scene/gameplay spawn hooks and minimal existing-Lua API bindings for cosmetic effects
  and rigid props. Keep generated events immutable; change the responsible exporter/overlay for
  any selected MM9 trigger. No general SCR runtime or implicit MM9 spell system.
- [x] Make the inspector usable with newly authored non-MM9 effects and models.

Gate: representative imported and authored content uses the same services; supported recipes
are distinguishable from partial/unsupported ones; actor removal/map changes leave no live remnants.

### M6 — Regression, resource budgets and fidelity review

- [x] Validate MM6/MM7/MM8 indoor/outdoor gameplay and existing FX/audio paths after shared changes.
- [x] Compare native MM9 captures at controlled camera/FPS/detail where available; keep playback
  correctness and original visual fidelity as separate acceptance claims.
- [x] Measure simultaneous effects, particle counts, draw calls, texture switches, overdraw, CPU/GPU
  time, allocations and memory on representative maps. Derive budgets from measurements.
- [x] Verify the shared library adds no per-frame traversal without live instances, keeps texture/audio GPU/runtime
  work lazy, and performs no global preallocation of large future-skinning buffers. Check unload and repeated reload
  resource stability.
- [x] Document supported capabilities, authoring, import regeneration, controls and remaining limits.

Gate: initial scope is complete and reviewable, with no material MM6–MM8 regressions and no
claim of full native parity for unresolved model/material/audio behavior.

### Later, separately authorized extensions

GPU skinning, additional animation interpolation, morphs, full material extensions, animation
blending/state machines, monster visual integration, gameplay animation events, persistent prop
save state, collision/picking for animated props and optional KTX2 packaging. Reuse the existing
model asset/instance/clip/node contract. Actor AI/combat/collision remain in shared gameplay;
rendering a 3D monster does not by itself supply those behaviors.

## Validation and implementation discipline

Use small pure-logic doctests for parsers, animation, transforms, curves, random selection and
timing. Add meaningful cases for the known alpha, emission and wind errors, not tests that merely
repeat implementation. Integration tests cover package mounting, resource lifetimes, sound
handles, pause/drain, invalid anchors and repeated map changes. Treat the old browser output as
a secondary regression reference; use original-game evidence for authenticity conclusions.

During implementation, use the normal build and focused tests:

```bash
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*ModelAnimation*'
./build/tests/openyamm_unit_tests --test-case='*EffectSystem*'
```

Test-case names above are proposed for new coverage. Add focused headless scenarios only for
lifecycle/map behavior that unit tests cannot cover. Use the authorized desktop launcher and
engine-native screenshots for actual rendering checks. No Vulkan builds unless separately
requested. Do not build merely to validate this planning document.

Keep implementation increments reviewable: asset contract/import, model CPU runtime, model
rendering, effect simulation, integration and fidelity fixes. Preserve original assets and unrelated
working-tree changes. Initial delivery ends after M6; future capabilities do not extend that gate.
