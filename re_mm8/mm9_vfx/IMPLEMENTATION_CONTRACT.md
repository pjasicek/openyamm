# Shared model and MM9 effect implementation contract

Status: implemented initial rigid-model and one-shot-effect scope, 2026-09-22. This document is the acceptance and
authoring contract for `MODEL_AND_FX_IMPLEMENTATION_PLAN.md`; it does not claim full MM9 visual parity.

## Runtime ownership and scope

- `engine/models/` owns immutable glTF assets, animation sampling, evaluated poses, bounds, instances, and
  generation-checked handles. `engine/render/ModelRenderer.*` owns model GPU residency and submission.
- `game/fx/EffectSystem.*` owns typed effect definitions, clocks, particles/components, model attachments, and
  generation-checked effect handles. `WorldFxSystem` owns scene lifetime, model/effect resources, and effect audio.
- The same services are used by ordinary rigid props, authored effects, imported MM9 effects, indoor maps, outdoor
  maps, debug inspection, and Lua requests. There is no native ABC/DTX runtime path in these services.
- Initial scope is rigid/static meshes, rigid node animation, invisible attachment nodes, sprites/particles, fixed
  sprites, Null transform keys, rigid model components, and scheduled sound. Skinning, morph targets, deforming model
  effects, actor animation graphs, animated collision, and persistent-prop saves remain outside this scope.

## Model format contract

The supported glTF 2.0 subset is triangle primitives, indexed or non-indexed geometry, position/normal/UV attributes,
embedded or package-relative PNG images, multiple mesh instances, arbitrary node ordering, static TRS or matrices,
empty nodes, multiple named clips, and STEP/LINEAR translation/rotation/scale channels. Asset reads, external buffers,
and external images go through `AssetFileSystem`, including ZIP mounts.

The loader rejects malformed hierarchies, cycles, invalid/non-finite accessors, CUBICSPLINE, morph targets, visible
skinned meshes, unsupported required extensions, non-triangle primitives, and invalid buffer/image references. A
deliberate animation-path import may omit source mesh and skin payload. CPU asset data and GPU residency are separate;
headless loading and animation allocate no skinning state or renderer resources.

Canonical modern assets retain glTF's right-handed Y-up metre convention. Placement performs one explicit boundary
conversion into OpenYAMM's right-handed Z-up world:

```text
glTF position (x, y, z) -> OpenYAMM position (x, z, y)
```

The swap reflects handedness, so renderer winding is selected from the evaluated transform determinant. Normals use
the inverse-transpose transform. MM9 ABC animation-path import preserves local axes, applies the calibrated `2.56`
source scale once, then uses the same placement conversion. Effect positions, node offsets, velocities, radii, model
roots, and audio distances share OpenYAMM world units; there is no independent sprite-size conversion.

Models support opaque, alpha-mask, and sorted alpha-blend materials, double-sided state, base-color PNGs, an explicit
unlit flag, and basic directional/ambient lighting. This is not a full glTF PBR implementation.

## Texture and binding contract

Migrated model/effect textures are PNG RGBA8 at runtime. DTX is an offline source only. Conversion preserves decoded
RGB and alpha, including RGB below zero alpha; it never repairs opacity or premultiplies implicitly. Import reports
record source hashes, DTX flags, color-space intent, alpha usage, sampler policy, and every decoded source mip. Runtime
currently generates mipmaps from level zero; exact original mip upload is a recorded fidelity difference.

`assets_dev/engine/effects/mm9/resource_bindings.yml` is the only legacy-reference resolver for imported effects.
Lookup is exact after ASCII lowercase and slash normalization. Extension guessing and external fallbacks are disabled.
SPR frame order/timing, FXF recipes, source references, WAV bindings, and import provenance remain explicit. Runtime
descriptors refer only to package-relative GLB/PNG/YAML/WAV resources.

Bindings record whether a resource came from `SPELLS.fxf` or from the separately verified hardcoded melee-contact
path. The latter contributes `mm9:melee_blood`: the original one-frame flash plus one ten-particle spray at a resolved
contact point. The recovered 0.1/1.0-second lifetimes, normal offset, count and outward speed are preserved. Native
spread/gravity constants remain an approximation as bounded by `MELEE_HIT_EFFECTS.md`; no persistent wound is added.

The complete imported set is promoted base content under `assets_dev/engine/effects/mm9/`, not geography owned by the
MM9 world. This keeps its recipe, runtime assets, audio, path models, and provenance together while making the effects
available to every mounted world. The `mm9:` resource and effect ids record source provenance; they do not restrict
which world may spawn them.

## Effect behavior contract

An effect spawns at an OpenYAMM world position with quaternion rotation and positive uniform scale. Identity rotation
preserves authored orientation; Column of Fire is upright. Existing particles stay in world space when an emitter root
moves. Fixed, following, linked-model-node, and Null transform semantics are typed component behavior.

Sprite orientation is also typed behavior. Camera-facing layers use the current view basis. A nonzero native `Facing`
value compiles into an explicit world-plane right/up basis derived from `Normal`, `PlaneDir`, or `FacingDir` according
to the distinct native Sprite and SpriteSystem rules. The basis is converted from MM9 Y-up to OpenYAMM Z-up and
rotated by the effect transform. The imported library currently contains 11 such layers across eight effects; Spell
Reaver's expanding ring and ring emitter therefore lie horizontally on the impact plane.

The MM9 profile runs reproducible compatibility ticks at 60 Hz; 30 Hz and 120 Hz are diagnostic policies. It retains
the recovered cached emission samples, numeric emission opcodes, unnormalized wind, inverted transparency, native
detail scaling, once-per-update/no-catch-up emission, per-update rotation, early expiry, and short-lifetime terminal
color quirk. These rules do not change the existing MM6-MM8 particle system's 30 Hz update or tuning.

Immediate stop removes all components and stops owned audio. Drain disables new emission and lets drainable particles
finish. Pause freezes effect clocks and sound transitions. Scene reset stops named sounds, clears effect/model handles,
resources, particles, and caches. Multiple instances share immutable resources but own independent clocks, transforms,
and deterministic random state. Transient effects and Lua-spawned props are not serialized.

`assets_dev/engine/effects/mm9/capabilities.yml` is the generated per-recipe truth source. The current import contains
48 FXF recipes/176 keys: all 36 currently supportable one-shot effects are packaged and the remaining 12 are
unsupported. The hardcoded melee-blood recipe is supplemental and is not counted as an FXF capability.
All looping recipes remain explicitly unsupported until native continuous-key semantics are resolved. Six body-anchor
recipes and six deforming-mesh recipes fail capability classification explicitly; two source assets are missing.
Linked positions currently cover model-node translation. Native parent-rotation/body-anchor semantics and the exact
legacy texture-stage and spatial-audio attenuation rules remain known differences.

## Authoring and gameplay hooks

New effects use versioned YAML definitions compiled into the same `EffectDefinition` types as FXF imports. Use
namespaced ids, package-relative resources, explicit material/blend semantics, finite tracks in non-decreasing time,
and declared compatibility policy. Do not add a second simulator or filename-based behavior.

Map Lua can request transient cosmetic content without receiving or serializing handles:

```lua
evt.SpawnWorldEffect("mm9:column_of_fire", x, y, z, scale, yawRadians)
evt.SpawnWorldModel("worlds/mm9/models/props/example.glb", x, y, z, scale, yawRadians, "clip")
```

Scale and yaw are optional (`1` and `0`); the model clip is optional and loops when supplied. Requests are consumed by
`GameplayFxService` into the active scene's shared `WorldFxSystem`. Invalid transforms, unknown effects, missing
assets, and missing clips fail without leaving partial instances. Generated EVT Lua remains immutable.

Shared party melee combat may enqueue `mm9:melee_blood` on a resolved actor hit when
`[gameplay] melee_hit_blood_effects=true` and the target's merged monster record has `Blood=1`. MM6 did not provide
the later games' blood-splat metadata, so its merged rows define explicit material defaults: biological creatures and
humanoids use blood, while elementals, constructs, robots, spectral or skeletal undead, oozes, reactors and plants do
not. Contact feedback does not require the target to accept damage, so protected flesh NPCs retain impact feedback
without becoming damageable. The option defaults off, so importing MM9 content does not alter MM6–MM8 combat
presentation unless explicitly enabled. Direct picks use the resolved actor hit point; fallback melee targets use the
actor-facing collision-radius point. This is hit-time work only and introduces no per-frame search.

## Inspection controls

The existing debug console operates on the live shared runtime:

```text
model list
model spawn <path> <x> <y> <z> [scale] [yaw-radians]
model play <index> <clip> [once]
model pause <index> [off]
model scrub <index> <seconds>
model visible <index> [off]
model markers <index> [off]
model nodes <index> [name-filter]
model orbit <index> <azimuth-radians> <elevation-radians> <distance>
model stop <index|all>

effect list
effect stats
effect rate [30|60|120]
effect spawn <id> <x> <y> <z> [scale] [yaw-radians]
effect pause <index> [off]
effect scrub <index> <seconds>
effect replay <index>
effect stop <index|all>
```

Node markers draw local X/Y/Z axes for every evaluated node and deliberately ignore scene depth so invisible or
occluded attachment nodes remain inspectable. Orbit positions the gameplay camera around evaluated world bounds.

For automated desktop captures, launch-only `[debug]` settings support `effect_spawn_*`, `model_spawn_*`,
`effect_spawn_count` (maximum 256), `effect_stats_delay_seconds`, `model_spawn_clip`, and `model_spawn_markers`; like
screenshot directives, they are read but never persisted. `effect stats` and the delayed log report live quads, draws,
texture switches, estimated texture/transient bytes, and world-space quad area as a controlled-camera overdraw proxy.

## Deterministic regeneration

Generate the authored model fixture:

```bash
python3 tools/generate_model_fixtures.py
```

Regenerate the complete supported imported library and its assets with:

```bash
python3 tools/mm9_import_discovery/import_mm9_effect_assets.py --all-supported
```

The checked-in library was generated in one invocation for the 36 FXF effect names recorded in
`assets_dev/engine/effects/mm9/import/asset_import_report.yml`, plus the supplemental hardcoded melee-blood recipe.
The importer copies the authoritative FXF, converts bound DTX/SPR/WAV resources, exports animation-path GLBs,
compiles the library, then regenerates the capability report.
Per-texture provenance and decoded source mips live below `assets_dev/engine/effects/mm9/import/textures/`; path model
trajectory reports live below `assets_dev/engine/effects/mm9/models/spells/import/`.

Representative stable hashes:

| Asset | SHA-256 |
| --- | --- |
| Original `SPELLS.fxf` / packaged copy | `468cbe2265fac31539b30c09f203517cca2900f4be6ad9dcea548019d02879bf` |
| Original `BUGPATH.abc` | `167a7557b3b0608f3250d0caaaaf24b8b48559e5f5ed244ea3d2ec714387e342` |
| Original `WORMPATH.abc` | `52f5c1fad7e6020fd7dbf2dccdf14271e433050b3156321d2be4e81db9c3ccab` |
| Imported `bugpath.glb` | `141486647650b117cc11a6e288fecefbc9df5d3c9e00b981f005317d90354d68` |
| Imported `wormpath.glb` | `af1f38119c5aab9052a6a9daa02e9112455e50395902ea532489098e027283ad` |
| Authored fixture GLB | `29110d31dd4fb435127190133bd265a770661a0aae3e912f8430c0fefad6e2fb` |
| Authored checker PNG | `b29dfd6008ebc2007576e1e4e88defd22e5205f6ffd9d5c1c8948aba02da0823` |

Bugpath and Wormpath reports compare exact names/hierarchy plus every source key and midpoint after OpenYAMM placement.
Bugpath's maximum position/rotation-matrix errors are `1.526e-5`/`1.173e-7`; Wormpath's are `6.178e-5`/`0`, within
the recorded `1e-4`/`1e-5` tolerances.

## Review evidence and remaining claims

Engine-native captures under `output/mm9_vfx/` exercise the authored textured/transparent rigid model indoors and
outdoors, the animated empty-node marker, Column of Fire, and Firefly. They establish OpenYAMM runtime behavior, not
native MM9 parity. Native-controlled camera/FPS/detail comparisons remain unavailable, so original fidelity is still
bounded by the documented material, mip, loop, parent-rotation, body-anchor, deforming-mesh, and audio differences.

The acceptance record, measured budgets, regression commands, and current gate result are maintained in
`VALIDATION_REPORT.md`.
