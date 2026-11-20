# Shared model and MM9 effect validation report

Status: initial rigid-model and one-shot-effect scope accepted with the explicit fidelity and environment limits below,
2026-09-22. This report validates the implementation described by `IMPLEMENTATION_CONTRACT.md`; it does not claim
native MM9 visual parity, skinning, deforming meshes, actor anchors, or continuous native loop behavior.

## Acceptance result

The shared model loader, animation instances, renderer, named-effect player, MM9 import pipeline, Lua requests,
audio ownership, scene teardown, and indoor/outdoor hooks are implemented. The engine-owned MM9-derived FX package
exposes all 36 currently supportable one-shot recipes in every world. Its generated capability report keeps the
remaining 12 recipes explicit and unsupported rather than silently omitting or partially compiling them.

Two validation boundaries remain visible rather than being hidden:

- The original Column of Fire evidence was captured in an indoor-looking MM9 ODM scene because the imported MM9 map
  set contains 44 `.odm` maps and no `.blv` map. The promoted engine package can now be exercised directly in an
  MM6–MM8 BLV; the existing evidence still covers the shared-model BLV renderer, focused lifecycle tests, and
  MM6–MM8 outdoor/indoor/outdoor scenarios.
- A full repository unit run has three unrelated failures in the current dirty asset tree: the Darkmoor actor-preview
  test reports 50 missing creature textures, after which two terrain-decoration cases encounter the retained PHYSFS
  initialization. The run passed 1,263 of 1,266 cases and 241,638 of 241,688 assertions. Every model/FX-focused test
  listed below passes.

## Deterministic asset and CPU-runtime checks

The following commands passed from the repository root:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*ModelAnimation*'
./build/tests/openyamm_unit_tests --test-case='*EffectDefinitionLoader*'
./build/tests/openyamm_unit_tests --test-case='*EffectLibrary*'
./build/tests/openyamm_unit_tests --test-case='*EffectSystem*'
./build/tests/openyamm_unit_tests --test-case='*world effects and rigid models*'
./build/tests/openyamm_unit_tests --test-case='*settings debug startup options*'
python3 tools/mm9_import_discovery/test_effect_asset_pipeline.py
```

Results:

| Coverage | Cases | Assertions | Result |
| --- | ---: | ---: | --- |
| ModelAnimation/loading/fixtures | 7 | 84 | pass |
| Effect definition loading | 2 | 72 | pass |
| Effect library validation | 1 | 2 | pass |
| Effect simulation/lifecycle/rate policies | 10 | 96 | pass |
| Lua world-effect/model queues | 1 | 13 | pass |
| Launch-only diagnostic settings | 1 | 38 | pass |
| DTX/SPR deterministic pipeline script | fixture hashes, RGBA/mips, 34 SPR descriptors, 11 oriented layers | — | pass |

The checked-in model fixture covers one opaque textured primitive, one transparent/double-sided primitive, an
out-of-order hierarchy, a static matrix, an animated empty attachment node, and two clips. Temporary test fixtures
cover package-mounted external buffers and explicit CUBICSPLINE rejection. Other unsupported/malformed cases are
rejected in loader validation rather than partially loaded.

Bugpath and Wormpath validation compares node names, hierarchy, every source key, and every midpoint after placement.
The maximum position/rotation-matrix errors are `1.526e-5`/`1.173e-7` for Bugpath and `6.178e-5`/`0` for Wormpath,
inside the recorded `1e-4`/`1e-5` tolerances. Stable source and output hashes are in the implementation contract and
the per-asset import reports.

## Scene lifecycle and cross-world checks

These final-binary scenarios passed:

```sh
./build/game/openyamm --headless-run-scenario tests/scenarios/shared_fx/mm6_map_lifecycle.yml
./build/game/openyamm --headless-run-scenario tests/scenarios/shared_fx/mm7_map_lifecycle.yml
./build/game/openyamm --headless-run-scenario tests/scenarios/shared_fx/mm8_map_lifecycle.yml
```

They exercise MM6 `oute3.odm -> 6d07.blv -> oute3.odm`, MM7
`7out01.odm -> 7d29.blv -> 7out01.odm`, and MM8 `out01.odm -> d31.blv -> out01.odm`. Each scene loads the small shared
definition/resource-descriptor set, so an `mm9:*` effect can be spawned regardless of the active world. Textures and
sounds remain lazy until an effect uses them, inactive frames perform no named-effect traversal, and no future-skinning
buffers are allocated. The EffectSystem teardown test verifies that clear removes model, particle, fixed-sprite and
sound ownership, including an emitted stop event. Repeated map scenarios exercise scene destruction and recreation
without retained handles.

## Desktop rendering evidence

All captures use engine-native bgfx readback at 1600x900 on the ordinary OpenGL 3.3 desktop path. They are retained
under `output/mm9_vfx/`:

- `shared-model-outdoor.png` and `shared-model-indoor-review.png`: textured opaque and transparent fixture rendering
  through the shared outdoor and BLV indoor hooks.
- `shared-model-markers.png`: final RGB axes on visible and invisible animated nodes. Markers intentionally ignore
  scene depth for inspection.
- `column-of-fire.png`: one imported Column of Fire with the original four emitter components and scheduled sound.
- `firefly.png`: Bugpath-driven linked effect using the shared GLB node animation service.
- `column-of-fire-32.png`: deliberate overlapping stress capture, not a recommended authored scene.

The marker recapture caught and fixed a bgfx state-rebinding defect that had rendered only the first axis. The final
image shows X, Y and Z axes on both fixture nodes. These images establish OpenYAMM runtime behavior only. A controlled
native MM9 executable/camera/detail capture was not available, so no pixel-parity or original-performance claim is
made.

## Measured cost and initial budgets

The measurements used the same Bootcamp camera, 1600x900 OpenGL 3.3, VSync off, four-second warmup, deterministic
seeds, and a 0.75-second peak snapshot. All effects overlapped at `(25269, -6710, 1413)`, making overdraw deliberately
severe. `world_quad_area` is a controlled-camera world-space proxy, not pixel-perfect screen overdraw. Texture and
transient values are estimates/capacity usage rather than a heap-profiler allocation trace.

| Concurrent Columns | Effects | Quads | Effect draws / switches | Effect textures | Effect texture bytes | Effect transient bytes | World quad area | Frame draws | GPU time |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 562 | 0.585 ms |
| 8 | 8 | 752 | 669 / 669 | 22 | 480,590 | 297,872 | 7,425,180 | 1,231 | 0.635 ms |
| 32 | 32 | 3,008 | 2,651 / 2,651 | 22 | 480,590 | 1,191,488 | 29,700,700 | 3,213 | 2.147 ms |

The first active one-second samples were 1,009 frames for eight instances and 422 frames for 32, versus approximately
1,330–1,500 frames/s around the baseline. Later launcher medians are not meaningful for these one-shots because the
effects expire during the interval.

Initial authoring/review budgets on this host are therefore:

- Target at most eight simultaneous Column-equivalent effects in one view.
- Review any view above 800 visible named-effect quads, 700 named-effect submissions, 0.35 MiB transient effect
  storage, or 8 million world-quad-area units at the controlled camera.
- Treat 32 overlapping Columns as the stress ceiling, not shipping content. It remains stable but exposes the strict
  transparent-ordering submission cost.
- Retain exact transparent depth ordering. Future batching optimization must be measured separately and must not
  reorder incompatible alpha draws.

These are measured review thresholds, not global hard caps: different recipes, camera distances, blend modes and
hardware can move the limit. The runtime count setting allows up to 256 solely for diagnostics.

## Remaining fidelity limits

- Native texture-stage details, exact spatial attenuation, parent rotation/body anchors, and continuous FXF loop keys
  are not fully recovered.
- Runtime mipmaps are generated from imported level zero; source mips are retained as provenance for later exact-mip
  upload.
- Linked positions use model-node translation. Visible deforming models, skinning and morphs remain unsupported.
- No MM9 spell/gameplay mechanics were inferred from visual recipes. Lua hooks spawn transient cosmetics or rigid
  props and serialize no handles.
- The debug inspector was implemented in the existing gameplay console rather than adding a second editor-specific
  model runtime. Editor consumers can use the engine-owned loader/instance/renderer API when a model tool is added.
