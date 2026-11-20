# MM6 female peasant — new 3D project

**2026-10-13: this replacement is not selected or installed.** The user requested restoring the
[original Claude model for review](http://127.0.0.1:8901/level_generation/creatures/mm6_pfem_claude/review/viewer/). This project is preserved separately;
the installation and verification details below describe its earlier delivery.

New Sorpigal `pfem`, descriptors **595 / PeasantF1 A**, **596 / PeasantF1 B**, **597 / Peasantf1 C**.
Created under the shared Claude humanoid NPC playbook. The previous installed geometry was replaced with a new
Smart Topology body, separately generated face detail and five-digit hands. Existing native/HD references and
an owned skeleton's joint estimates were reused; weights and fitted animation are local to this project.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm6_pfem_codex/review/viewer/)
· [Runtime source GLB](export/mm6_pfem.glb)
· [Packed Blender master](export/mm6_pfem_master.blend)
· [Canonical production record](creature_3d_progress.json)

## Delivered content

| Clip | Seconds | Behavior |
|---|---:|---|
| Standing | 2 | Quiet clasped-hands loop |
| Walking | 0.8 | Ordinary walk; runtime speed follows travelled distance |
| Hit | 0.5 | Standing recoil and recovery |
| Death | 2.366667 | Forward fall into prone remains |
| Dead | 1 | Held final Death pose |
| Fidget | 3 | Small glance and breathing loop |

**No Attack, Cast, weapon or combat sockets.** The native civilian AI remains unchanged.
Walking also fills the runtime run role. Hit recovers to Standing; game state transitions own outgoing blends.

- Source LOD triangles: **9,123 / 4,560 / 1,640 / 539**.
- **128 bones**, at most four vertex influences. This includes 72 skirt controls and two braid controls;
  two unused toe end bones were removed. Feet remain rigid and independently grounded.
- Separate 1K body/head texture sets are merged into shared **2080×1024** atlases with a gutter.
  Each visible LOD uses one material primitive.
- One runtime texture set, region mask and native palette ramps: green 786, brown 787, teal 788.
  Only the bodice and two skirt hem bands recolour. Viewer-only GLBs bake the tiers for three.js.
- Model height is calibrated to the native 175.7-unit standing height: scale **107.227194**.
  Measured walking stride **1.131602 m**, ground offset zero.
- **60 / 100 Meshy credits**: body 5, head 30, hands 5, body texture 10, head texture 10.
  The rejected automatic rig request consumed zero. All animations use stored/local clips or local authoring.

## Sources and corrections

The stored `source/motion_spec.json` describes native sprite evidence, not the final preset timings.
The selected production motion is recorded in `creature_3d_progress.json → motion_plan`.
Standing and Walking use the local Relax humanoid set; Hit uses UnarmedGetHitF1. Death uses local
`Standing Death Forward 02.fbx`, with fitted entry, restrained leg flex, extended prone legs, foot anchoring,
floor contact and a separate skirt drape. Fidget is authored from Standing.

The body was weighted before reduction. The skirt has dedicated controls rather than thigh weights.
Repairs include a generated cloth puncture, neckline overlap/weight matching, coincident cloth seam weights,
fixed-length arm clearance, braid controls, and removal of permanently covered upper-leg surfaces.
Body Meshy UVs were transferred by face correspondence; a single repaired cloth triangle needed a local shared-edge
UV extension. Head UV correspondence was exact. A clean head-model bake replaces the poor returned mouth shading.
Skin regions, including the exposed upper-back panel within the garment mesh, are corrected explicitly.
Normal maps are converted to the glTF convention; ORM red carries specular, green roughness, blue remains zero.

## Verification and review

- `work/roundtrip_gate.json`: reimported GLB sampled at every frame and half frame, all six clips;
  maximum authored/export surface difference under 0.12 mm, lowest surface remains above the floor.
- `work/surface_crossings.json`: no arm/dress or braid/neck triangle-edge crossings at frame/half-frame samples.
  `work/reduced_cloth_contacts.json` records leg/skirt containment.
- `work/texture_only_parity.json`: the final texture correction preserved geometry, bind, weights and animation bytes.
- Browser: all 18 tier/clip combinations load without console errors. Actual playback was exercised at 1× and ¼×,
  with time-stamped captures and loop/end checks. Selected detail captures are under `review/final/`.
- `review/ingame/`: all three tiers compared with native sprites outdoors in New Sorpigal and indoors in 6d19,
  using the native screenshot path on NVIDIA/OpenGL.
- Normal development build passed. Focused actor regression
  `OPENYAMM_REGRESSION_FILTER=mm6_pfem ./build/game/openyamm --world mm6 --headless-run-regression-suite actors`
  passed, including native A/B/C binding, shared asset, six timings, absent combat clips and LODs.

This is technical production completion; user artistic acceptance is recorded separately.

## Authoritative files and rebuilding

`work/textured_uv.blend` is the authoring checkpoint with semantic attributes and separate body/head UVs.
`export/mm6_pfem_master.blend` is the packed, normal Blender handoff. Both contain the final rig and motion.
Quarter-frame contact keys are preserved by a 120 fps GLB export; authoring time remains 30 fps.

Claim this project's `mm6:pfem` lease before edits. With that token, the export sequence is:

1. Run `scripts/export_runtime.py` through `tools/run_creature_blender.sh`.
2. Guarded `tools/prepare_actor_glb.py export/mm6_pfem_lod0.glb export/mm6_pfem_runtime_lod0.glb`.
3. Run `scripts/roundtrip_gate.py` when geometry or animation changes.
4. Run `scripts/build_lods.py`.
5. Guarded shared `region_variants.py` from `export/mm6_pfem_lods.glb` to `export/mm6_pfem.glb`,
   using `textures/pfem_ramps.json` and Peasant extras `openyamm_specular=1`,
   `openyamm_specular_mask=true`, `pbr.metallicFactor=0`.
6. Guarded `tools/merge_head_material.py export/mm6_pfem.glb export/mm6_pfem.glb`.
7. `tools/install_model.py export/mm6_pfem.glb --world mm6 --name mm6_pfem.glb`.
8. Guarded `scripts/viewer_tiers.py`, then refresh viewer manifest hashes and relevant review evidence.

Paths above are relative to this project except repository tools. Do not rerun one-time pose-fitting scripts on the
final checkpoint: arm abduction corrections are additive. Earlier work files and scripts retain intermediate
experiments; the selected final checkpoint and canonical record are authoritative. The two cloth-clearance
passes were Walking+Death at 16 mm, followed by Death at 36 mm before UV production.

The installer writes `assets_source/worlds/mm6/models/mm6_pfem.glb` and preprocesses its runtime copy at
`assets_dev/worlds/mm6/models/mm6_pfem.glb`. Never copy the runtime-preprocessed model back over the export.
No raw library animations are intended for version control.
