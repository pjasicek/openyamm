# MM9 Native 3D Actor Implementation Goal

Goal: implement MM9 actors, monsters, NPCs, scripted creatures, and model-backed interactive objects as native 3D
animated models, while keeping the work largely independent from ongoing `Mm9DatWorld` integration until the renderer
and animation asset path are proven.

This is the operational checklist for future `/goal` work. Research and design context lives in:

- `docs/mm9/MM9_3D_ACTOR_RENDERING_IMPLEMENTATION_NOTES.md`
- `docs/mm9/MM9_SCRIPTED_BILLBOARD_ACTOR_GOAL.md`
- `docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`
- `docs/mm9/MM9_IMPORT_TOOLCHAIN.md`

## Current Implementation Status

- [x] Added generic GLB animated-model asset loading in `game/render/AnimatedModelAsset.*`.
- [x] Added MM9 `.model.yml` sidecar parsing and merge logic in `game/mm9/Mm9AnimatedModelSidecar.*`.
- [x] Added deterministic pose sampling for translation, rotation, scale, hierarchy, skinning matrices, and sockets.
- [x] Added focused real-asset tests in `tests/AnimatedModelAssetTests.cpp`.
- [x] Wired the new model loader, MM9 sidecar parser, and tests into CMake.
- [x] Added a model resolver for MM9 `Filename`/`Skin` registry lookup in
      `game/mm9/Mm9AnimatedModelResolver.*`.
- [x] Added `mm9_animated_model_probe` for quick model/sidecar/clip/socket validation.
- [x] Added MM9 sidecar animation event merge, event interval queries, controller time bookkeeping, and blended
      transition pose sampling.
- [x] Added MM9 animated actor visual binding state in `game/mm9/Mm9AnimatedActorVisual.*`.
- [x] Retain skinned GLB vertex/index payloads in `AnimatedModelPrimitive` for future GPU upload.
- [x] Compute model and primitive local-space bounds from retained vertex positions.
- [x] Retain MM9 sidecar LOD exported index and source distances in `AnimatedModelAsset`.
- [x] Added render-prep draw items with remapped per-draw bone palettes and explicit palette-limit rejection.
- [x] MM9 animated actor visuals now cache render-prep draw items/counters with resolved material overrides.
- [x] MM9 animated actor visuals now cache model-to-world transforms, world bounds, and world-space sockets.
- [x] Validator now rejects invalid node hierarchy refs, non-finite node/animation transforms, invalid clip durations,
      invalid key times, non-monotonic key times, and non-finite inverse bind matrices.
- [x] Representative banshee, bigfoot, and dragon actor clips/sockets are covered by finite-pose acceptance tests.
- [x] Added a bgfx skinned-model renderer resource/submit layer in `game/render/AnimatedModelRenderer.*`.
- [x] Added and compiled skinned animated-model shaders through `openyamm_runtime_shaders`.
- [x] Added `mm9_animated_model_render_smoke` to load/sample/render-prep/submit representative animated models without
      MM9 map loading.
- [x] Render smoke resolves, decodes, uploads, and binds referenced MM9 DTX material textures from
      `assets_dev/worlds/mm9/source`.
- [x] Expanded isolated validation/render-prep coverage to humanoid/NPC, static prop, and spell/projectile
      representatives: `guard`, `props/barrel`, `spells/firebolt`, and `projectiles/magicarrow`.
- [x] Added `Mm9AnimatedActorBinding` to convert `Mm9ScriptedObject` state into native animated actor visual sources,
      including visibility, ray-hit, solidity, movement semantic, collision volume, and pick identity.
- [x] Added native scripted-object resolution coverage proving visible Guberland actor-like objects resolve through
      `model_registry.yml` without generated billboard sidecars.
- [x] Guberland visible resolved actors now initialize native animated visual state with nonempty render-prep draw
      items in headless tests.
- [x] `OutdoorGameView` now builds MM9 scripted objects independently of generated billboard sidecars and owns
      resolved native animated actor visual/cache instances for MM9 maps.
- [x] `OutdoorRenderer` now initializes native animated-model bgfx resources, updates MM9 animated actor visuals each
      frame, resolves source DTX material textures from `assets_dev/worlds/mm9/source`, and submits native MM9 actor
      draw items in the outdoor main world pass.
- [x] Added native animated actor runtime performance diagnostics for visible models, evaluated skeletons/nodes,
      submitted draw items, triangles, bone matrices, material switches, texture uploads/failures, skipped draws, and
      CPU animation time.
- [x] `mm9_animated_model_render_smoke --require-pixels` now rejects bgfx `Noop` as insufficient pixel evidence, and
      `OPENYAMM_BGFX_RENDERER` can force renderer selection when a real offscreen backend is available.
- [x] Added `Mm9AnimatedModelSidecarTests.cpp` coverage for parsing sidecar materials, sockets, animation events, LOD
      metadata, merge-time material refs, invalid material refs, invalid socket refs, and missing sidecar material
      entries.
- [x] MM9 animated actor binding now emits object-context diagnostics when scripted object `Filename`/`Skin`
      resolution fails, with focused coverage for missing model and missing skin cases.
- [x] `mm9_animated_model_probe` now supports `--dump-clips`, `--dump-sockets`, and
      `--dump-material-overrides`; verified representative banshee, registry-resolved bigfoot, and dragon probe runs.
- [x] `mm9_animated_model_probe --json` now emits machine-readable model, material, clip, socket, diagnostics, and
      render-prep data for future automated validation.
- [x] Added a source-boundary regression test that keeps native MM9 animated actors scoped to MM9 maps, verifies
      registry-driven runtime binding, and rejects accidental `Mm9DatWorld` dependencies in the native actor path.
- [x] MM9 model sidecars now parse source skeleton node metadata, including source indices, parent links, flags, and
      children, and merge validation rejects invalid skeleton references.
- [x] Native animated actor shaders now consume outdoor world fog parameters and apply depth-based fog in the skinned
      model fragment path.
- [x] MM9 scripted object runtime now preserves DAT-generated sidecar provenance (`source_kind`, `source_ref`, and
      `model_asset`) and tests verify Guberland DAT object model assets match native model registry resolution.
- [x] Added a real Afterworld visible stationary dialogue actor smoke test: `Skraelos0` initializes as a native
      animated actor visual from generated scene/events data, then opens generated MM9 dialogue through world-hit
      activation.
- [x] Added regression coverage proving native MM9 animated actors remain world-gated and do not replace classic
      MM6-MM8 actor billboard rendering or indoor actor runtime paths.
- [x] Added `mm9_animated_model_viewer`, an interactive bgfx/ImGui model viewer independent of map loading and
      `Mm9DatWorld`, with clip playback/scrubbing, current clip/time display, diagnostics, bounds, skeleton, and
      socket-axis/name overlays.
- [x] Add pixel-backed runtime/viewer verification after the runtime-map submit path is wired. The headless smoke can
      render either direct model/sidecar inputs or a real MM9 scripted-object runtime binding through bgfx OpenGL/X11
      with render-target readback.

Current local verification note:

- [x] Runtime now parses generated `model_skin_binding` and resolves authoritative DAT/generated `model_asset`
      directly before falling back to raw `Filename`/`Skin`. This preserves import-tool class/type-picture resolution
      for cases where raw `Filename` is not enough, such as `OldHag` using `models/hag.glb` even though the raw
      `Filename` is `models\PeasantM2.ABC`.
- [x] `mm9_animated_model_probe` verifies DAT-native `model_asset`/`model_skin_binding` resolution independently of
      unit-test relink; OldHag resolves to `models/hag.glb`, `hag_hag`, and `skins/hag.dtx`.
- [x] Guberland DAT-backed model asset unit coverage now passes against generated `model_asset` data.
- [x] Added guardrail tests for initial implementation non-goals: no generated billboard dependency in the native
      animated actor binding/visual path, no runtime ABC/LTB/LithTech/FEAR parser in the generic animated model
      loader/renderer, and no silent static fallback when required animation data is missing.
- [x] Added a source-boundary guardrail proving `Mm9DatWorld` does not own native animated actor loading, model
      registry resolution, GLB assets, bgfx submission, or animated actor visuals.
- [x] `SDL_VIDEODRIVER=dummy ./build/tools/mm9_animated_model_viewer --frames 3` verifies viewer load, animation
      sampling, render-prep, skinned submit, ImGui setup, and overlay code for `banshee`, `bigfoot`, and `dragon`.
      These runs use bgfx `Noop`, so they do not prove visible pixels.
- [x] Pixel verification was retried with `SDL_VIDEODRIVER=offscreen` plus `OPENYAMM_BGFX_RENDERER=opengl` and
      `vulkan`; both fail `bgfx::init` locally, so the pixel-backed checklist items remain open.
- [x] Added regression coverage proving native visual state preserves original-source semantics needed by scripts:
      source clip names, head-follow/breath-attack animation event keys, RangeAttack/Jaw sockets, LOD distances,
      skin bindings, source model/skin strings, object identity, and script-facing socket/pick behavior.

## Principles

- [x] Native 3D is the authoritative MM9 actor visual path.
- [x] Do not add new runtime dependence on generated MM9 billboard frames.
- [x] Keep pure animated-model loading, animation sampling, sockets, validation, and skinning reusable.
- [x] Keep MM9-specific model registry, `.model.yml`, DTX, `Filename`, `Skin`, and script identity handling in MM9 code.
- [x] Do not make `Mm9DatWorld` own the animated model implementation.
- [x] Integrate with `Mm9DatWorld` only after model loading, animation sampling, and debug rendering are independently
      testable.
- [x] Preserve original MM9/LithTech semantics where practical: source clip names, sockets, skins, LOD metadata,
      animation events, object identity, and script-facing model behavior.
- [x] Fail loudly for missing/corrupt model, skin, skeleton, animation, socket, or material data.

## Ownership Split

### Generic Animated Model Core

Suggested location: `game/render/animated_model/` or `engine/model/`, depending on dependency needs.

The generic core should not know about MM9 maps, RUDE scripts, DAT worlds, `Filename`, `Skin`, or MM9 object classes.

- [x] `AnimatedModelAsset`
  - [x] source path/id;
  - [x] meshes/primitives;
  - [x] materials;
  - [x] texture refs or abstract texture slots;
  - [x] skeleton nodes;
  - [x] parent indices;
  - [x] inverse bind matrices;
  - [x] animation clips;
  - [x] animation events as opaque strings;
  - [x] sockets as named node-local transforms;
  - [x] bounds;
  - [x] optional LOD metadata.
- [x] `AnimatedModelClip`
  - [x] name;
  - [x] duration;
  - [x] node translation channels;
  - [x] node rotation channels;
  - [x] interpolation mode;
  - [x] events.
- [x] `AnimatedModelPose`
  - [x] local node transforms;
  - [x] global node transforms;
  - [x] render skinning matrices;
  - [x] dirty/evaluated state is not needed for the current eager pose-cache/update design.
- [x] `AnimatedModelController`
  - [x] current clip;
  - [x] previous clip for transitions;
  - [x] current time;
  - [x] loop/nonloop mode;
  - [x] rate;
  - [x] transition duration and elapsed time.
- [x] `AnimatedModelDiagnostics`
  - [x] load errors;
  - [x] validation warnings;
  - [x] missing material/texture refs;
  - [x] invalid animation targets;
  - [x] invalid socket nodes;
  - [x] matrix/NaN checks.

### MM9 Adapter Layer

Suggested location: `game/mm9/`.

The MM9 layer binds source content to the generic core.

- [x] `Mm9AnimatedModelSidecar`
  - [x] parse `openyamm.model3d.v1`;
  - [x] read original ABC provenance;
  - [x] read material runtime DTX refs;
  - [x] read sidecar skeleton metadata;
  - [x] read sockets;
  - [x] read animation event metadata;
  - [x] read LOD distances.
- [x] `Mm9AnimatedModelResolver`
  - [x] resolve source `Filename` to model asset path;
  - [x] resolve source `Skin` to material overrides;
  - [x] use `assets_dev/worlds/mm9/models/model_registry.yml` where applicable;
  - [x] preserve exact source model/skin strings for diagnostics;
  - [x] emit explicit unresolved diagnostics.
- [x] `Mm9AnimatedActorVisual`
  - [x] source object identity;
  - [x] model asset id;
  - [x] sidecar path;
  - [x] material overrides;
  - [x] current clip name;
  - [x] semantic state;
  - [x] animation controller;
  - [x] skeleton pose cache;
  - [x] socket cache;
  - [x] model-to-world transform;
  - [x] world-space bounds;
  - [x] render-prep draw item cache;
  - [x] visible/hidden state;
  - [x] collision radius/height.
- [x] MM9 socket conventions
  - [x] `RangeAttack`;
  - [x] `LHand1`;
  - [x] `RHand1`;
  - [x] `Jaw`;
  - [x] unknown sockets preserved and exposed.
- [x] MM9 clip fallback rules
  - [x] exact source clip;
  - [x] idle/stand;
  - [x] original-style idle/walk/run/fly variants such as `stand1`, `walk3`, `standwater`, and `swim`;
  - [x] melee/ranged attack;
  - [x] pain/wince;
  - [x] death;
  - [x] explicit unresolved state when no suitable clip exists.

### DAT World Integration

This is a later consumer, not the owner of model animation.

- [x] Read placed/scripted object source identity from existing MM9 generated sidecars.
- [x] Pass `Filename`, `Skin`, generated `model_asset`, `model_skin_binding`, transform, visibility, and script
      metadata to `Mm9AnimatedModelResolver`.
- [x] Use the same visual component for sidecar-backed and DAT-backed MM9 scripted actors.
- [x] Keep DAT geometry, collision, and world loading work independent from animated model correctness.

## Milestone 1: Asset Loader And Validator

Purpose: prove that converted MM9 GLB + `.model.yml` assets can be loaded and validated without map loading.

- [x] Add a runtime GLB animated model loader.
- [x] Load vertex attributes:
  - [x] `POSITION` data and presence/count validation;
  - [x] `NORMAL` data and presence validation;
  - [x] `TEXCOORD_0` data and presence validation;
  - [x] `JOINTS_0` data and presence validation;
  - [x] `WEIGHTS_0` data and presence validation;
  - [x] indices data and count validation.
- [x] Load glTF skins and inverse bind matrices.
- [x] Load glTF animation clips.
- [x] Load glTF node hierarchy.
- [x] Load material/texture slots.
- [x] Load `.model.yml` sidecar.
- [x] Merge sidecar sockets/events/material runtime refs into the asset diagnostics.
- [x] Validate representative assets:
  - [x] `assets_dev/worlds/mm9/models/banshee.glb`;
  - [x] `assets_dev/worlds/mm9/models/bigfoot.glb`;
  - [x] `assets_dev/worlds/mm9/models/dragon.glb`;
  - [x] `assets_dev/worlds/mm9/models/guard.glb` as a human/NPC representative;
  - [x] `assets_dev/worlds/mm9/models/props/barrel.glb` as a static prop with model sidecar;
  - [x] `assets_dev/worlds/mm9/models/spells/firebolt.glb` and
        `assets_dev/worlds/mm9/models/projectiles/magicarrow.glb` as spell/projectile representatives.

Acceptance:

- [x] Loader can parse representative assets without map/DAT world code. Covered examples include banshee, bigfoot,
      dragon, guard, props/barrel, spells/firebolt, and projectiles/magicarrow.
- [x] Validation reports node, mesh, skin, clip, socket, material, and LOD counts.
- [x] Invalid or missing refs produce explicit diagnostics.
- [x] No NaN/Inf transforms or inverse bind matrices pass validation.

## Milestone 2: Animation Sampling

Purpose: prove that animation can run deterministically without rendering.

- [x] Implement clip lookup by name.
- [x] Implement case-insensitive lookup while preserving source spelling.
- [x] Sample node local transforms at arbitrary time.
- [x] Sample looped clips.
- [x] Sample nonloop clips.
- [x] Compute global node transforms.
- [x] Compute skinning matrices:

```text
renderMatrix[node] = animatedGlobal[node] * inverseBindGlobal[node]
```

- [x] Compute socket transforms in local and world space. Core pose sampling computes model-space socket transforms;
      `Mm9AnimatedActorVisual` composes and caches world-space socket transforms.
- [x] Add event query for animation string keys in a time interval.
- [x] Add controller update with rate and loop mode.
- [x] Add simple transition support.

Acceptance:

- [x] Sampling `banshee` `standAir`, `Fly`, and `HattackAir1` gives valid matrices.
- [x] Sampling `bigfoot` `stand`, `walk`, `run`, and `Rattack1` gives valid matrices.
- [x] Sampling `dragon` `fly`, `stand`, and `rAttack1` gives valid matrices.
- [x] Socket transforms for `RangeAttack`, `LHand1`, `RHand1`, and `Jaw` are valid when present.
- [x] Loop endpoint sampling does not generate discontinuity or NaN output.

## Milestone 3: Tests

Add focused tests before renderer integration.

- [x] `AnimatedModelAssetTests.cpp`
  - [x] GLB parse smoke;
  - [x] skin/joint/inverse-bind consistency;
  - [x] animation target validation;
  - [x] material ref diagnostics.
  - [x] retained vertex/index payload consistency;
  - [x] local bounds validity;
  - [x] sidecar LOD metadata merge.
  - [x] MM9 sidecar animation event merge and interval query;
  - [x] controller update, looping events, nonloop finish, and transition bookkeeping.
  - [x] controller transition pose blending.
- [x] `AnimatedModelPoseTests.cpp` or equivalent dedicated pose coverage
  - [x] sample known clips at `0ms`;
  - [x] sample known clips at midpoint;
  - [x] sample loop endpoint;
  - [x] no NaN matrices;
  - [x] parent-child global transform consistency.
- [x] `AnimatedModelSocketTests.cpp` or equivalent dedicated socket coverage
  - [x] valid named socket lookup;
  - [x] missing socket diagnostic;
  - [x] socket transform follows animated node.
- [x] `Mm9AnimatedModelSidecarTests.cpp`
  - [x] parse `.model.yml`;
  - [x] validate sockets/events/materials;
  - [x] resolve runtime DTX texture refs.
- [x] `Mm9AnimatedModelResolverTests.cpp`
  - [x] resolve `Filename`;
  - [x] resolve `Skin`;
  - [x] exact model+skin registry lookup;
  - [x] unresolved model diagnostic;
  - [x] unresolved skin diagnostic.
- [x] `Mm9AnimatedActorVisualTests.cpp`
  - [x] bind resolved model/skin identity into visual state;
  - [x] bind scripted object visibility, solid/ray-hit state, movement semantic, collision volume, and pick identity;
  - [x] resolve scripted object `Filename`/`Skin` to native animated model paths without billboard metadata;
  - [x] resolve visible Guberland scripted actor-like objects through the native model registry;
  - [x] initialize native visual render-prep for visible Guberland resolved actors;
  - [x] initialize a real visible stationary dialogue actor as a native visual and verify generated MM9 dialogue
        activation still opens from the same object identity;
  - [x] preserve classic MM6-MM8 actor billboard rendering by keeping native animated actors MM9-gated;
  - [x] cache controller pose and sockets;
  - [x] cache model-to-world transform, world bounds, and world-space sockets;
  - [x] cache render-prep draw items/counters with resolved material overrides;
  - [x] preserve visibility and collision state;
  - [x] update animation events through the visual component;
  - [x] resolve semantic clip fallbacks and unresolved diagnostics.
- [x] `AnimatedModelRendererTests.cpp`
  - [x] convert draw items to GPU skinned vertices;
  - [x] define bgfx vertex layout for position, normal, UV, joint indices, and weights;
  - [x] select opaque, alpha-blended, and culling render states.
  - [x] verify default no-fog parameters for non-outdoor submit paths.

Test data policy:

- [x] Prefer real MM9 dev assets when already present under `assets_dev/worlds/mm9/models/`.
- [x] For small pure logic tests, use generated/minimal in-test data if it keeps the test stable.
- [x] Do not require `Mm9DatWorld` or map loading for core model tests.

## Milestone 4: Probe Binary

Purpose: enable quick command-line validation of model assets and sampled animation state.

Suggested target:

```text
mm9_animated_model_probe
```

Suggested command:

```sh
./build/tools/mm9_animated_model_probe \
  --model assets_dev/worlds/mm9/models/banshee.glb \
  --sidecar assets_dev/worlds/mm9/models/banshee.model.yml \
  --clip Fly \
  --time-ms 500 \
  --socket RangeAttack
```

Registry-resolved command:

```sh
./build/tools/mm9_animated_model_probe \
  --registry assets_dev/worlds/mm9/models/model_registry.yml \
  --filename MODELS\\BIGFOOT.ABC \
  --skin SKINS\\BIGFOOT3.DTX \
  --clip run \
  --time-ms 750 \
  --socket RHand1
```

DAT/generated-model-asset command:

```sh
./build/tools/mm9_animated_model_probe \
  --registry assets_dev/worlds/mm9/models/model_registry.yml \
  --model-asset models/hag.glb \
  --model-skin-binding hag_hag \
  --filename models\\PeasantM2.ABC \
  --clip stand \
  --time-ms 250 \
  --json
```

Output should include:

- [x] model id/path;
- [x] sidecar path;
- [x] mesh/piece count;
- [x] material count;
- [x] texture refs;
- [x] node count;
- [x] skin joint count;
- [x] animation count;
- [x] selected clip duration;
- [x] sampled frame/time;
- [x] socket transform if requested;
- [x] validation warnings/errors;
- [x] nonzero exit code on hard validation failure.

Optional output:

- [x] JSON mode;
- [x] DAT/generated `model_asset` + `model_skin_binding` registry mode;
- [x] dump all clips;
- [x] dump all sockets;
- [x] dump material/skin override resolution.

## Milestone 5: Debug Viewer

Purpose: visually inspect one model and one clip before integrating with game maps.

Suggested target:

```text
mm9_animated_model_viewer
```

Headless submit-smoke target:

```text
mm9_animated_model_render_smoke
```

Features:

- [x] load one GLB + sidecar in submit-smoke mode;
- [x] select clip by name in submit-smoke mode;
- [x] play/pause/scrub time in interactive viewer mode;
- [x] submit skinned mesh through bgfx in submit-smoke mode;
- [x] apply sidecar material DTX refs in submit-smoke mode;
- [x] submit-smoke validated representative humanoid/NPC (`guard`), static prop (`props/barrel`), and projectile
      (`projectiles/magicarrow`) assets. `spells/firebolt` submits, but currently has no runtime texture ref in its
      sidecar.
- [x] show skeleton overlay;
- [x] show socket axes/names;
- [x] show model bounds;
- [x] show current clip/time;
- [x] show validation diagnostics.

The viewer may use existing game/editor bgfx setup if practical, but it should not require loading a map or
`Mm9DatWorld`.

## Milestone 6: GPU Skinning Renderer

Purpose: render animated models through bgfx as normal 3D draw items.

- [x] Define skinned vertex layout.
- [x] Add skinned shader program.
- [x] Upload bone matrix palette.
- [x] Handle backend bone uniform limits.
- [x] Split or reject meshes that exceed palette limits with explicit diagnostics. Current implementation rejects
      over-limit primitives; splitting can be added later if needed.
- [x] Render opaque skinned model through a reusable bgfx submit path.
- [x] Render alpha-mask/cutout materials where sidecar specifies them.
- [x] Submit MM9 native animated actor draw items from the outdoor map renderer with cached DTX material textures.
- [x] Apply fog/depth behavior matching current world rendering.
- [x] Add debug counters:
  - [x] visible animated models;
  - [x] evaluated skeletons;
  - [x] evaluated nodes;
  - [x] uploaded bone matrices;
  - [x] skinned draw calls;
  - [x] skinned triangles;
  - [x] material/texture switches;
  - [x] CPU animation time.

Acceptance:

- [x] Viewer renders `banshee`, `bigfoot`, and `dragon` with animated clips in dummy-frame smoke mode.
- [x] Socket overlay follows animated pose.
- [x] No blank render, exploding mesh, or invalid matrix output. OpenGL/X11 render-target readback validates nonblank
      pixels for representative `banshee`, `bigfoot`, `dragon`, and a Guberland runtime-bound `hag` actor.
- [x] Renderer path does not require MM9 map loading.
- [x] Outdoor MM9 map renderer owns and submits native animated actor draw items without using generated billboard
      sidecars.

## Milestone 7: MM9 Runtime Binding

Purpose: connect model assets to MM9 scripted objects after the isolated path is stable.

- [x] Add MM9 animated actor visual component.
- [x] Resolve model/skin from scripted object `Filename`/`Skin`.
- [x] Use source object transform.
- [x] Use source visibility/solid/rayhit state.
- [x] Select idle clip for stationary objects.
- [x] Select walk/run/fly/attack clips from behavior/script state when available.
- [x] Expose socket transforms to effects/projectiles through the visual component cache.
- [x] Use scripted-object collision volume for picking and blocking.
- [x] Pick/use returns MM9 scripted object identity.

Acceptance:

- [x] Guberland visible actors resolve to native 3D model assets.
- [x] Resolved actors are submitted as 3D model draw items by the outdoor renderer. Pixel-backed visible-output
      verification remains open.
- [x] No resolved actor is invisible.
- [x] Missing models/skins emit diagnostics.
- [x] Dialogue smoke for stationary talk NPCs still works.
- [x] MM6-MM8 actor rendering is unchanged.

## Milestone 8: DAT World Consumer

Purpose: use native 3D actor rendering with DAT-backed MM9 world loading.

- [x] Consume DAT/generated sidecar placed object data through the MM9 scripted object runtime.
- [x] Do not duplicate model resolution in `Mm9DatWorld`.
- [x] Keep DAT geometry and animated model rendering separate.
- [x] Add smoke coverage for at least one DAT-backed map.

Acceptance:

- [x] `Mm9DatWorld` supplies placement and source metadata only.
- [x] Animated model loader/tests still pass without `Mm9DatWorld`.
- [x] DAT-backed actor visuals use the same model asset path as sidecar-backed actors.

## Non-Goals For Initial Implementation

- [x] No generated runtime billboards for MM9 actors.
- [x] No direct LithTech renderer port.
- [x] No runtime ABC/LTB parsing unless the GLB pipeline is proven lossy for required behavior.
- [x] No mesh-triangle gameplay collision as the first collision source.
- [x] No FEAR-style animation graph in the first implementation.
- [x] No silent fallback to an idle/static/invisible actor when required data is missing.

## Useful Commands To Add Later

```sh
cmake --build build --target openyamm_unit_tests -j25
cmake --build build --target openyamm_runtime_shaders -j25
cmake --build build --target mm9_animated_model_render_smoke -j25
cmake --build build --target mm9_animated_model_viewer -j25
./build/tests/openyamm_unit_tests --test-case="animated model renderer*"
./build/tests/openyamm_unit_tests --test-case=Mm9AnimatedModel*
./build/tools/mm9_animated_model_probe --model ... --sidecar ... --clip ... --time-ms ... --socket ...
./build/tools/mm9_animated_model_probe --registry ... --filename ... --skin ... --clip ... --time-ms ...
./build/tools/mm9_animated_model_probe --registry ... --model-asset ... --model-skin-binding ... --clip ... --json
./build/tools/mm9_animated_model_probe --model ... --sidecar ... --dump-clips --dump-sockets
./build/tools/mm9_animated_model_probe --registry ... --filename ... --skin ... --dump-material-overrides
./build/tools/mm9_animated_model_probe --registry ... --filename ... --skin ... --clip ... --json
./build/tools/mm9_animated_model_render_smoke --model ... --sidecar ... --texture-root ... --clip ... --time-ms ...
OPENYAMM_BGFX_RENDERER=opengles ./build/tools/mm9_animated_model_render_smoke --model ... --sidecar ... \
  --texture-root ... --clip ... --time-ms ... --require-pixels
OPENYAMM_BGFX_RENDERER=opengl SDL_VIDEODRIVER=x11 ./build/tools/mm9_animated_model_render_smoke \
  --scene assets_dev/worlds/mm9/maps/guberland.scene.yml \
  --events assets_dev/worlds/mm9/maps/guberland.events.yml \
  --registry assets_dev/worlds/mm9/models/model_registry.yml \
  --map-id guberland --object-index 20 --time-ms 500 --require-pixels
./build/tools/mm9_animated_model_viewer --model ... --sidecar ...
SDL_VIDEODRIVER=dummy ./build/tools/mm9_animated_model_viewer --model ... --sidecar ... --clip ... --frames 3
```

## Completion Definition

This goal is complete when:

- [x] generic animated GLB loading and pose sampling are covered by tests;
- [x] MM9 sidecar/model/skin resolution is covered by tests;
- [x] a probe binary can validate and sample representative MM9 actor models;
- [x] a viewer or headless render smoke can display animated representative models. Pixel-backed OpenGL/X11 readback
      validates banshee, bigfoot, and dragon; dummy-frame viewer smoke also exercises the independent viewer path;
- [x] Guberland actors render as native 3D models through MM9 runtime binding. Pixel-backed OpenGL/X11 readback
      validates `mm9:guberland:object:20` through scene/events/registry-driven runtime binding;
- [x] Guberland MM9 map-load path owns native animated actor visual/cache instances independent of billboard sidecars;
- [x] MM6-MM8 actor behavior/rendering remains unchanged;
- [x] the implementation does not depend on `Mm9DatWorld` internals except as a later source of placement metadata.
