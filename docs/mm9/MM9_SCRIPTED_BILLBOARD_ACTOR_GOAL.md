# MM9 Native 3D Actor Goal

This document supersedes the earlier scripted-billboard milestone. The filename is kept to avoid breaking existing
references, but the active MM9 actor visual target is native 3D animated models, in line with the original LithTech/MM9
runtime.

Do not implement MM9 actors or monsters as generated 2D billboards. The billboard pipeline may remain useful as a
historical diagnostic or temporary comparison tool, but it is not the final runtime path.

Implementation details and LithTech references are captured in:

- `docs/mm9/MM9_3D_ACTOR_RENDERING_IMPLEMENTATION_NOTES.md`
- `docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`
- `docs/mm9/MM9_DIALOGUE_RUNTIME_PIPELINE_CHECKLIST.md`
- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`

## Goal

Render MM9 actors, monsters, NPCs, scripted creatures, and model-backed interactive objects as the original game did:
source-shaped 3D animated models with skins, clip names, sockets, LOD, object identity, script state, and interaction
metadata preserved.

The first playable target remains Guberland, but the milestone is now:

- load the MM9 map;
- resolve placed/scripted actor objects to converted GLB model assets and skins;
- render visible actors as animated 3D models;
- pick/use them through their MM9 scripted object identity;
- keep enough original model/script state to support later MM9 behavior without a compatibility corner.

MM9 scripts and content can depend on 3D model semantics that billboards cannot represent well, such as facing, turning,
head/jaw/hand/socket-based effects, clip names, animation events, and actor-specific model state. The runtime should
therefore stay as close as practical to the original 3D model design instead of flattening actors into sprite frames.

## Active Direction

- [ ] Add native runtime support for MM9 animated GLB actor models.
- [ ] Use the converted MM9 model assets under `assets_dev/worlds/mm9/models/` as the primary visual source.
- [ ] Use `.model.yml` sidecars for provenance, materials, skeleton metadata, sockets, animation events, and LOD data.
- [ ] Bind map/scripted object `Filename` and `Skin` properties to model assets and material overrides.
- [ ] Preserve actor/script identity from generated MM9 sidecars.
- [ ] Drive animation by MM9 source clip names and semantic state, not by MM6-MM8 actor animation enums.
- [ ] Render with GPU skinning as the normal path.
- [ ] Implement sockets early; they are required for attacks, effects, attachments, and script-facing visual behavior.
- [ ] Add model/skeleton/socket debug rendering before optimizing.
- [ ] Add asset validation and headless smoke coverage before replacing current visual experiments.

## Architectural Guardrails

- [x] Keep the existing MM6-MM8 actor runtime unchanged.
- [x] Keep MM9 actor/monster support behind MM9 world/content capability checks.
- [x] Preserve MM9 scripted object identity separately from MM6-MM8 actors.
- [x] Do not widen MM6-MM8 actor animation enums for MM9.
- [ ] Do not convert MM9 placed objects into normal MM6-MM8 actors unless behavior mapping is explicit and lossless.
- [ ] Keep MM9 clip/action state string-based.
- [ ] Keep MM9-specific behavior in an MM9 runtime layer until there is a proven shared gameplay abstraction.
- [ ] Reuse shared renderer primitives only when they are genuinely generic:
  - fog and depth state;
  - texture loading/caching;
  - bgfx shader/program management;
  - picking/debug draw helpers;
  - collision query helpers.
- [ ] Do not add silent fallbacks that hide missing model, skin, skeleton, or animation state.

## Source Data To Preserve

For each MM9 placed/scripted actor object, preserve at least:

- map id;
- source object index;
- source object id;
- source class;
- source name / `Name`;
- `Filename`;
- `Skin`;
- `ScriptName`;
- `ScriptParams`;
- `Visible`;
- `Solid`;
- `RayHit` / `Rayhit`;
- `NeedsTick`;
- `NonSolidUse` when present;
- raw source property refs;
- normalized runtime/event sidecar refs.

Current relevant code paths:

- `game/mm9/Mm9ScriptedObjectRuntime.*`
- `game/mm9/Mm9InteractionRouting.*`
- `game/mm9/Mm9DialogueRuntime.*`
- `tools/mm9_import_discovery/generate_mm9_events.py`
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml`
- `assets_dev/worlds/mm9/maps/*.events.yml`

The visual runtime should add or preserve:

- resolved model asset id;
- resolved source GLB path;
- resolved sidecar path;
- resolved skin/material override set;
- current clip name;
- current semantic action;
- current animation time;
- visible/hidden state;
- world transform;
- collision radius/height;
- picking/interactability;
- debug diagnostics for unresolved or invalid asset state.

## Model Asset Contract

The active runtime asset should read GLB plus `.model.yml` sidecar into a dedicated animated model representation. Do
not reuse editor static model import structures as the authoritative runtime actor model.

Minimum asset fields:

```text
AnimatedModelAsset
  id
  sourceGlbPath
  sourceSidecarPath
  meshes/primitives
  materials
  texture refs
  skeleton nodes
  inverse bind matrices
  animations
  animation events
  sockets
  LOD metadata
  bounds
```

Required validation:

- GLB parses successfully.
- Sidecar schema is recognized.
- Sidecar `model` points at the loaded GLB.
- Skin joint count matches inverse bind matrix count.
- Skeleton node indices referenced by sockets are valid.
- Animation channel node targets are valid.
- Materials resolve to known texture refs or emit explicit diagnostics.
- Source `Skin` overrides resolve deterministically.

Relevant model conversion code:

- `tools/mm9_import_discovery/convert_abc_model.py`
- `tools/mm9_import_discovery/batch_convert_actor_models.py`
- `tools/mm9_import_discovery/generate_model_registry.py`
- `assets_dev/worlds/mm9/models/model_registry.yml`
- `assets_dev/worlds/mm9/models/*.model.yml`

## Runtime Visual Contract

MM9 actors should have a native 3D visual component, for example:

```text
Mm9AnimatedActorVisual
  modelAssetId
  sourceModel
  sourceSkin
  materialOverrides
  currentClipName
  semanticState
  animationController
  skeletonPoseCache
  socketCache
  hiddenPieces
  worldTransform
  visible
```

Runtime update order:

1. Load MM9 scripted objects from source/generated sidecars.
2. Resolve `Filename`/`Skin` to model asset and material overrides.
3. Update behavior/script/dialogue state.
4. Select current source clip name or semantic fallback.
5. Advance animation controllers from frame delta.
6. Evaluate visible skeleton poses.
7. Submit skinned model draw items.
8. Use socket transforms for effects, attacks, attachments, and debug overlays.

## Animation Contract

Preserve LithTech-style animation concepts:

- current and previous animation references;
- current and previous frame references;
- interpolation percent;
- loop/nonloop state;
- transition time;
- animation rate;
- keyframe string events;
- optional layered/additive blends later if required by source behavior.

OpenYAMM should evaluate:

```text
nodeLocal = lerp/slerp(previousFrameTransform, currentFrameTransform, framePercent)
nodeGlobal = parentGlobal * nodeLocal
renderMatrix = animatedGlobal * inverseBindGlobal
```

Use quaternion slerp for rotations and linear interpolation for translations. Keep animation names case-insensitively
resolvable but preserve source spellings for diagnostics.

Clip selection should support:

- exact source clip name;
- semantic fallback such as idle/walk/run/fly/attack/pain/death;
- explicit missing-clip diagnostics;
- no invisible silent fallback.

## Sockets And 3D Script Semantics

Sockets and node transforms are required runtime behavior. They are not polish.

Required APIs:

```text
getNodeTransform(actor, nodeNameOrIndex, worldSpace)
getSocketTransform(actor, socketNameOrIndex, worldSpace)
```

Use them for:

- `RangeAttack` projectile/effect origins;
- hand attachment points such as `LHand1` and `RHand1`;
- jaw/head effects where source models expose them;
- debug visualization;
- future script commands that turn, face, look, or pose parts of the model.

If a script or content command references head turning, facing, attachment points, or animation events, prefer adding
the native 3D behavior over introducing a compatibility approximation.

## Rendering Contract

Use GPU skinning as the normal path.

Minimum vertex attributes:

```text
POSITION
NORMAL
TEXCOORD_0
JOINTS_0
WEIGHTS_0
```

Minimum render behavior:

- opaque skinned model pass;
- alpha-mask/cutout support where sidecars specify it;
- transparent handling in the correct pass if needed;
- fog/depth behavior consistent with current world rendering;
- texture/material override support;
- per-frame debug counters.

Initial implementation may evaluate the full skeleton for every visible animated actor. Add LithTech-style used-node
evaluation only after profiling shows it matters.

Batch/sort draw items by:

- render phase;
- shader/program;
- material;
- texture handles;
- mesh/primitive;
- light/fog state if applicable.

## Collision And Picking

Do not use animated mesh triangles as gameplay collision in the first implementation. Preserve MM9 scripted object
volumes and use them for interaction and blocking.

Required behavior:

- collision radius/height remains stable across animation frames;
- picking returns MM9 scripted object identity;
- debug draw shows collision volume and visual model bounds;
- projectile targeting can use the scripted object/world-impact volume;
- future mesh or OBB hit tests are additive and explicit, not a replacement for object identity.

Pick/use metadata should expose:

- MM9 object id;
- source object index;
- source class;
- source name;
- source model;
- source skin;
- script name;
- script params;
- current clip/action.

## First Native 3D Milestone

- [ ] Load Guberland in MM9 mode.
- [ ] Resolve all visible actor/NPC/scripted creature model assets from `Filename`/`Skin`.
- [ ] Render resolved actors as 3D animated models.
- [ ] No resolved actor is invisible.
- [ ] Unresolved actors use an obvious 3D/debug placeholder and emit diagnostics.
- [ ] Idle clips play deterministically.
- [ ] Walk/run/fly/attack clip selection works by source clip name or explicit semantic fallback.
- [ ] Pick/use an MM9 NPC and log complete MM9 object/script/model information.
- [ ] Dialogue smoke for stationary talk NPCs still works.
- [ ] MM6-MM8 maps still render existing actors unchanged.
- [ ] Debug overlay can show skeleton, sockets, model bounds, and collision volume.
- [ ] Headless validation checks model/skin/skeleton/socket/animation consistency for all Guberland actors.

## Regression Guardrails

- [x] MM6-MM8 map loading must not require MM9 visual definitions.
- [ ] MM6-MM8 actor save/load schema must not change for MM9 3D actor work.
- [ ] MM6-MM8 actor AI and animation enums must remain unchanged.
- [ ] Shared renderer changes must be covered by at least one MM6/MM7/MM8 map smoke test and one MM9 map smoke test.
- [ ] MM9 runtime code paths must be enabled only by MM9 content/world capability.
- [ ] Missing MM9 models/skins/animations must produce explicit diagnostics.
- [ ] Generated Lua/RUDE/dialogue data must still be regenerated through the pipeline, not hand-edited.

## Later Quality And Performance Pass

- [ ] Import or regenerate lower model LODs if needed.
- [ ] Add per-actor LOD selection based on camera distance.
- [ ] Add used-node/path transform evaluation if skeleton evaluation becomes measurable.
- [ ] Add animation blend layers or weight sets if required by original behavior.
- [ ] Add model lighting improvements as MM9 baked/dynamic lighting support matures.
- [ ] Add screenshots or deterministic visual smoke tests for representative monsters.
- [ ] Add dense-scene perf budgets for animation update, skinning submission, and draw calls.
- [ ] Add tooling to compare OpenYAMM model poses against Blender/import previews.

## Deprecated Billboard Work

The previous version of this file described generated animated 2D billboard visuals under:

```text
assets_dev/worlds/mm9/rendering/scripted_billboards/
```

That work proved useful for model registry coverage, clip discovery, collision defaults, map-object binding, and
diagnostics. It should now be treated as historical/diagnostic data only. Do not add new MM9 runtime requirements that
depend on generated billboard frames, billboard angle selection, billboard visual ids, or PNG frame verification.

If old billboard code remains temporarily in the tree, it should be clearly guarded as non-authoritative and removable
once native 3D actor rendering is in place.

## Related Files

- `docs/mm9/MM9_3D_ACTOR_RENDERING_IMPLEMENTATION_NOTES.md`
- `docs/mm9/MM9_IMPORT_TOOLCHAIN.md`
- `docs/mm9/MM9_EVENTS_IMPLEMENTATION_GOAL.md`
- `docs/mm9/MM9_DIALOGUE_RUNTIME_PIPELINE_CHECKLIST.md`
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml`
- `assets_dev/worlds/mm9/maps/*.events.yml`
- `assets_dev/worlds/mm9/models/model_registry.yml`
- `assets_dev/worlds/mm9/models/*.model.yml`
- `game/mm9/Mm9ScriptedObjectRuntime.*`
- `game/mm9/Mm9InteractionRouting.*`
- `game/mm9/Mm9DialogueRuntime.*`
