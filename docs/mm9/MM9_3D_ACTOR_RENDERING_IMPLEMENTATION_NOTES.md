# MM9 3D Actor Rendering Implementation Notes

This document records local findings from the MM9 LithTech source tree and the current OpenYAMM MM9 asset pipeline for
implementing MM9 actors and monsters as real 3D animated models. The target for MM9 is native 3D rendering, not runtime
billboards.

Use the LithTech code as a behavioral and architectural reference only. Do not copy LithTech/OpenEnroth/mm_mapview2 code
into OpenYAMM.

## Summary

MM9/LithTech actors are normal 3D model instances:

- model pieces with skins/materials and per-piece LODs;
- skeleton nodes with bind/global/inverse-bind transforms;
- animation trackers with current/previous animation frame state;
- quaternion/translation interpolation;
- optional layered/additive animation blending through weight sets;
- sockets for hands, ranged attacks, jaws, and attachments;
- per-instance hidden pieces, skins, scale, and transform cache;
- render queues sorted by render style/material, textures, render object, render priority, lights, and close-view state.

OpenYAMM already has the right source asset shape. MM9 ABC models are converted to GLB plus `.model.yml` sidecars with
meshes, skins, skeletons, animations, sockets, materials, and LOD metadata. The robust implementation path is therefore
an OpenYAMM-native bgfx animated model renderer that consumes the converted GLBs and sidecars while preserving LithTech
animation/socket/LOD semantics.

## Current OpenYAMM Asset State

The converted MM9 model tree under `assets_dev/worlds/mm9/models/` currently contains:

- `844` `.glb` files;
- `844` files with meshes;
- `844` files with skins;
- `843` files with animations;
- `.model.yml` sidecars with original ABC provenance, materials, skeleton nodes, sockets, animations, animation events,
  pieces, and LOD distances.

Example sidecars:

- `assets_dev/worlds/mm9/models/banshee.model.yml`
  - source: `mm9/extracted/MODELS/MODELS/BANSHEE.abc`
  - pieces: `6`
  - skeleton nodes: `135`
  - sockets: `3`
  - animations: `17`
  - sample animations: `bansetup`, `standAir`, `Fly`, `WalkAir`, `tauntAir`, `HattackAir1`, `RattackAir1`
- `assets_dev/worlds/mm9/models/bigfoot.model.yml`
  - pieces: `1`
  - skeleton nodes: `27`
  - sockets: `3`
  - animations: `19`
  - sample animations: `static_model`, `stand`, `walk`, `run`, `Hattack1`, `Rattack1`
- `assets_dev/worlds/mm9/models/dragon.model.yml`
  - pieces: `2`
  - skeleton nodes: `113`
  - sockets: `6`
  - animations: `15`
  - sample sockets: `RangeAttack`, `LHand1`, `RHand1`, `Jaw`

The ABC-to-GLB conversion code is in:

- `tools/mm9_import_discovery/convert_abc_model.py`
  - ABC reader: `read_abc`, `read_node`, `read_animation`, `read_socket`
  - skin output: `add_skin`
  - mesh output with `JOINTS_0`/`WEIGHTS_0`: `add_meshes`
  - animation output: `add_animations`
  - sidecar output: `write_sidecars`

Important exporter behavior:

- One glTF skin is emitted with all skeleton nodes as joints.
- Each model piece becomes a glTF mesh primitive with `POSITION`, `NORMAL`, `TEXCOORD_0`, `JOINTS_0`, and `WEIGHTS_0`.
- Vertex weights are trimmed to four joints and normalized.
- Animations are emitted as glTF translation and rotation channels for each node.
- Sidecars preserve LithTech socket definitions and animation string-key events.
- Sidecars preserve original LOD distances, but the current conversion exports one LOD index into a given GLB.

## LithTech Reference Map

Primary model/animation files:

- `mm9/lithtech/runtime/model/src/model.h`
  - model constants such as `MAX_GVP_ANIMS`, `MAX_CHILD_MODELS`, `MAX_PIECE_TEXTURES`, `MAX_PIECES_PER_MODEL`;
  - model nodes, animations, pieces, skins, sockets, weight sets, and render object abstraction;
  - channel compression concepts for position/quaternion data.
- `mm9/lithtech/runtime/model/src/model_load.cpp`
  - LTB model loading;
  - `ModelPiece::Load`, including piece LODs, texture slots, render style index, render priority, render object type,
    and used-node list;
  - `Model::LoadSockets`;
  - `Model::LoadWeightSets`;
  - animation binding dimensions/translations.
- `mm9/lithtech/runtime/model/src/animtracker.h`
- `mm9/lithtech/runtime/model/src/animtracker.cpp`
  - `trk_Init`;
  - `trk_Update`;
  - `trk_SetCurAnim`;
  - `trk_SetCurTime`;
  - `trk_ScanToKeyFrame`;
  - keyframe callback processing;
  - loop/nonloop behavior and interpolation percentage calculation.
- `mm9/lithtech/runtime/model/src/transformmaker.cpp`
  - `SetupTransforms`;
  - `SetupTransformsWithPath`;
  - `InitTransform`;
  - `BlendTransform`;
  - `Recurse`;
  - `RecurseWithPath`.

Primary model instance/cache/socket files:

- `mm9/lithtech/runtime/shared/src/objectmgr.cpp`
  - `ModelInstance::ClientUpdate`;
  - `ModelInstance::ServerUpdate`;
  - `ModelInstance::GetNodeTransform`;
  - `ModelInstance::GetSocketTransform`;
  - `ModelInstance::ForceUpdateCachedTransforms`;
  - `ModelInstance::GetCachedTransform`;
  - `ModelInstance::GetRenderingTransforms`;
  - `ModelInstance::ResetCachedTransformNodeStates`;
  - `ModelInstance::UpdateCachedTransformsWithPath`;
  - `ModelInstance::SetupNodePath`;
  - `ModelInstance::SetupLODNodePath`.
- `mm9/lithtech/runtime/world/src/de_objects.h`
  - `ModelInstance` fields and transform-cache flags.

Primary render files:

- `mm9/lithtech/runtime/render_a/src/sys/d3d/setupmodel.cpp`
  - model queueing;
  - model hook data;
  - root model lighting;
  - attachment lighting inheritance;
  - per-piece LOD selection;
  - `SetupLODNodePath`;
  - queueing renderable pieces.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/rendermodelpiecelist.cpp`
  - queued model piece structure;
  - sorting by close-view flag, render priority, render style, texture list, render object, and lights;
  - skeletal, rigid, and vertex-animated render dispatch;
  - texture/render-style/light state minimization.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/drawmodel.cpp`
  - solid/translucent model queue flow and render-list flushing.

Game-level references that can help interpret actor states, but should not be copied:

- `mm9/lithtech/NOLF/ObjectDLL/AnimationMgr*`
- `mm9/lithtech/NOLF/ObjectDLL/Animator*`
- `mm9/lithtech/NOLF/ObjectDLL/AIAnimal*`
- `mm9/lithtech/NOLF/ObjectDLL/ModelButeMgr*`

Later LithTech/FEAR animation trees are more advanced and should not be the first MM9 implementation model. MM9-era
tracker semantics are enough for a robust first implementation.

## LithTech Behavior To Preserve

### Animation Tracker Semantics

LithTech keeps current and previous animation frame references in each tracker. Rendering interpolates between those
references using a percent value computed from keyframe times.

Preserve:

- string animation names from source models;
- clip duration in milliseconds;
- loop/nonloop clip mode;
- animation rate modifier;
- transition-from-previous-animation behavior;
- keyframe string events from sidecars;
- current/previous frame and interpolation percent semantics;
- deterministic update from frame delta, independent of render submission order.

Recommended OpenYAMM shape:

```text
AnimatedClip
  name
  durationMs
  keyframes/events
  node channels

AnimatedModelController
  currentClip
  previousClip
  currentTimeMs
  previousTimeMs
  transitionElapsedMs
  transitionDurationMs
  loopMode
  rate
```

### Skeleton Evaluation

LithTech evaluates local node animation as:

```text
nodeLocal = lerp/slerp(previousFrameTransform, currentFrameTransform, framePercent)
nodeGlobal = parentGlobal * nodeLocal
```

For rendering, LithTech computes a matrix equivalent to:

```text
renderMatrix[node] = animatedGlobal[node] * inverseBindGlobal[node]
```

Preserve this exact conceptual contract. It maps directly to normal GPU skinning.

Implementation details:

- Use quaternion slerp for rotation.
- Use linear interpolation for translation.
- Normalize quaternions after interpolation/load if needed.
- Keep bind pose and inverse bind pose from the GLB/sidecar authoritative.
- Do not mix gameplay collision with visual mesh geometry for the first implementation.
- Compute socket transforms from animated node transform plus socket local transform.

### Transform Cache And Used-Node Optimization

LithTech has a lazy transform cache:

- every animation update marks nodes as unevaluated;
- `GetNodeTransform` marks the path from requested node to root and evaluates it;
- rendering marks node paths needed by the selected LOD;
- only evaluated nodes get render matrices for the frame.

This is a good optimization, but it is not required for the first correct implementation. MM9 actor skeletons are small
enough that full visible-skeleton evaluation is likely acceptable initially.

Recommended order:

1. Implement full skeleton evaluation for visible animated models.
2. Add profiling counters:
   - visible animated model count;
   - evaluated skeleton count;
   - evaluated node count;
   - skinning draw count;
   - submitted triangles.
3. Add LithTech-style used-node/path evaluation only if profiling shows skeleton evaluation is a real cost.

### Sockets

Sockets are part of the actor rendering contract, not a later cosmetic feature. Sidecars already preserve them.

Required runtime API:

```text
bool getNodeTransform(modelInstance, nodeNameOrIndex, worldSpace)
bool getSocketTransform(modelInstance, socketNameOrIndex, worldSpace)
```

Use cases:

- hand-held attachments;
- ranged attack origins such as `RangeAttack`;
- jaw/head effects;
- projectile/effect spawning;
- debug rendering and validation.

### LOD

LithTech stores per-piece LOD distances and chooses the LOD from camera distance before queueing each piece. The
selected LOD also determines which skeleton nodes need evaluation.

OpenYAMM sidecars currently preserve LOD distances but each GLB is exported at one `lod.exportedIndex`. For robust 3D
actors, decide explicitly between:

- regenerate/import all LODs as separate GLBs or primitives;
- extend the converter to write all LODs into one asset with sidecar metadata;
- keep LOD0 initially and add lower LODs after correctness.

The simplest correct first path is LOD0 only with a clear TODO and perf counters. Do not silently pretend full LOD
support exists if only one LOD is loaded.

### Skins And Materials

LithTech pieces can reference up to `MAX_PIECE_TEXTURES == 4` texture slots and instances can override skins. OpenYAMM
sidecars preserve material texture paths and runtime DTX texture references.

Required behavior:

- load material texture references from `.model.yml`;
- support source `Skin` overrides from MM9 placed/scripted objects;
- preserve alpha mask/cutout material hints;
- submit opaque and alpha-tested/transparent pieces in the correct render phase;
- keep texture identity stable enough for batching.

### Rendering And Batching

LithTech queues model pieces and sorts them to reduce state churn. The exact D3D9 render-style system should not be
ported, but the batching idea is still valid.

OpenYAMM/bgfx target:

- one shader path for opaque skinned textured actors;
- one shader path for alpha-tested/cutout skinned actors if needed;
- transparent pieces handled in the existing transparent pass/order;
- batch/sort model draw items by:
  - render phase;
  - shader/program;
  - material;
  - texture handles;
  - mesh/primitive;
  - light/fog state if applicable.

Prefer GPU skinning:

- vertex attributes: position, normal, texcoord, joint indices, joint weights;
- uniform matrix palette for small skeletons;
- split mesh or use a texture/storage-buffer palette if a backend uniform limit is exceeded;
- CPU skinning only as a debug/fallback path, not the main design.

### Lighting

LithTech builds a relevant light list for the root model and lets attached child models inherit it. MM9 lighting is
documented separately in `docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`.

For the actor renderer:

- integrate with OpenYAMM's current world fog and lighting path first;
- apply world ambient and directional/dynamic lighting as supported by current renderer;
- keep model lighting data isolated enough to improve later when MM9 baked/dynamic lighting is decoded more fully;
- do not block 3D actor rendering on perfect LithTech light-grid parity.

## Recommended OpenYAMM Architecture

### Asset Layer

Add a runtime asset type that reads the current GLB plus `.model.yml` sidecar:

```text
AnimatedModelAsset
  id
  sourceGlbPath
  sourceSidecarPath
  meshes/primitives
  materials
  textures
  skeleton nodes
  inverse bind matrices
  animations
  sockets
  LOD metadata
  bounds
```

Use `cgltf` if extending the existing C++ GLB import path is practical. Existing GLB import code is in
`editor/import/ObjModelImport.cpp`, but it currently targets imported static/editor geometry, not runtime animated
actors.

Important: do not make the editor static import representation the runtime actor model representation. Animated models
need their own runtime resource/instance data.

### Instance Layer

Add an MM9 runtime visual component for placed/scripted actor objects:

```text
Mm9AnimatedActorVisual
  modelAssetId
  sourceModel
  sourceSkin
  currentClipName
  semanticState
  worldTransform
  visible
  hiddenPieces
  materialOverrides
  animationController
  skeletonPoseCache
  socketCache
```

The runtime object identity remains the MM9 scripted object identity:

- map id;
- source object index;
- source object id;
- class/name;
- `Filename`;
- `Skin`;
- `ScriptName`;
- `ScriptParams`;
- collision radius/height;
- current behavior/action.

Do not convert MM9 actors into MM6-MM8 actor animation enums. MM9 clips should be addressed by source clip names and
semantic categories.

### Renderer Layer

Add a renderer-owned queue item:

```text
AnimatedModelDrawItem
  asset
  instance
  meshPrimitive
  material
  texture handles
  matrix palette handle/range
  model transform
  render phase
  depth/sort key
```

Suggested per-frame flow:

1. MM9 runtime updates actor behavior and selected clip names.
2. Animation controllers advance from frame delta.
3. Visible animated actors update skeleton pose caches.
4. Renderer builds draw items from model pieces/primitives.
5. Opaque draw items are sorted/batched and submitted.
6. Alpha/transparent draw items are submitted in the correct pass.
7. Debug overlays can draw skeletons, sockets, bounds, and collision.

### Skinning Shader

Minimum shader inputs:

```text
POSITION
NORMAL
TEXCOORD_0
JOINTS_0
WEIGHTS_0
```

Minimum uniforms:

```text
u_model
u_viewProj or current renderer equivalent
u_boneMatrices[MAX_BONES]
u_baseTexture
u_fog/light uniforms as needed
```

Vertex shader operation:

```text
skinnedPosition =
  weight0 * bone[joint0] * position +
  weight1 * bone[joint1] * position +
  weight2 * bone[joint2] * position +
  weight3 * bone[joint3] * position
```

Normals should use the rotational part of the same blended matrix or an appropriate normal matrix. Handle scaled actors
carefully; LithTech normalized normals when instances were scaled.

## Validation Plan

Build correctness before optimizing heavily.

Required asset validation:

- GLB can be loaded;
- sidecar schema and model path match;
- skeleton node count matches skin joint count;
- inverse bind matrix count matches joint count;
- animation channels target valid nodes;
- sockets target valid nodes;
- materials reference existing texture assets or explicit unresolved diagnostics;
- source `Skin` overrides resolve to expected runtime textures.

Required runtime validation:

- actor model appears at source object position with correct scale and orientation;
- idle/walk/run/attack/death clips advance deterministically;
- nonloop clips stop or transition as expected;
- loop clips wrap without pose jumps;
- sockets follow animated nodes;
- ranged attack effect spawns from `RangeAttack`;
- picking returns the MM9 scripted object identity;
- collision remains stable and does not depend on animated mesh triangles;
- hidden/visible/scripted state affects rendering correctly.

Required visual/debug tools:

- draw skeleton overlay;
- draw socket axes/names;
- draw model bounds;
- draw collision capsule/cylinder;
- show current clip/time/frame;
- show source model/skin and resolved material overrides;
- show draw item count and skeleton node count.

Required performance counters:

- visible MM9 animated actors;
- animated actors updated;
- skeletons evaluated;
- nodes evaluated;
- bone matrices uploaded;
- skinned draw calls;
- skinned triangles;
- material/texture switches;
- CPU animation time;
- bgfx submit time if available.

## Implementation Milestones

1. Runtime GLB animated model loader
   - load meshes, materials, textures, skin joints, inverse binds, animations, sockets, and sidecar metadata;
   - fail loudly on incomplete animated model data.

2. CPU pose evaluation plus debug viewer
   - evaluate one clip on one model;
   - draw skeleton/socket debug overlay;
   - verify bind pose and a few named clips.

3. GPU skinned rendering
   - render one actor with base texture and fog/depth;
   - support alpha mask where sidecar says `alphaMode: MASK`;
   - validate orientation/scale against Blender/import previews.

4. MM9 runtime integration
   - bind `Filename`/`Skin` from map/scripted objects to `AnimatedModelAsset`;
   - render all visible Guberland actors as 3D;
   - current action selects source clip name or semantic fallback.

5. Sockets and effects
   - expose socket transforms;
   - use `RangeAttack`/hand sockets for effects/projectiles;
   - add socket debug overlay.

6. LOD/material/lighting polish
   - support lower LODs if imported;
   - improve batching;
   - integrate better MM9 lighting as decoded.

7. Regression and performance gates
   - headless asset validation;
   - deterministic animation tests;
   - screenshot/visual smoke tests for representative actors;
   - perf budget checks on dense actor scenes.

## Explicit Non-Goals

- Do not render MM9 actors as billboards in the final MM9 runtime path.
- Do not port the LithTech D3D9 renderer or render-style system directly.
- Do not parse original LithTech ABC/LTB files at runtime unless the GLB pipeline is proven lossy for required data.
- Do not map MM9 animation states into MM6-MM8 actor animation enums.
- Do not make mesh collision the gameplay collision source for the first implementation.
- Do not add silent fallback paths that hide missing/corrupt actor assets. Missing model, skin, skeleton, or animation
  data should produce explicit diagnostics.

## Relationship To Older Billboard Work

`docs/mm9/MM9_SCRIPTED_BILLBOARD_ACTOR_GOAL.md` describes an earlier playable milestone based on generated billboards.
The current MM9 actor visual target is native 3D rendering. Existing billboard generation data may still be useful as a
temporary diagnostic/reference for model-to-map binding, clip naming, semantic fallback choices, and generated collision
defaults, but it should not define the final MM9 rendering architecture.
