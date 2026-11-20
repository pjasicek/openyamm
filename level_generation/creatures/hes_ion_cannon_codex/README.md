# The great ion cannon — Hesper

**Seven static states accepted in the viewer; POSITION bounds corrected for staging (2026-10-23).**
[Exports](export/README.md) · [Viewer](review/viewer/index.html) · [CPU charging-state sheet](review/charging_states.png) ·
[Final artifact checks](review/final_checks.json) · [Final LOD switch scores](review/final_lod_audit/scores.tsv).
Meshy spend **15 / 40 credits**: geometry 5, retexture 10; both SUCCEEDED. No further jobs are queued.
The integrator accepted all seven states in the viewer. Native review and the Crown binding remain with its builder; no rows staged here.

Scope: Round 2 of [CREATURE_BUILDS.md](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md),
row 10059 and the Crown decoration. The latest
[integrator note](../../../design/kreegan_world/WORK_PACKAGES/requests/P3.md#integrator-note-ion-cannon-retexture-2026-10-23)
requests the seven exports, LODs and viewer, then hands the decoration switch to the Crown builder.
The runtime files have no rig, skin or animation. No motion-library or humanoid animation gates apply.

## Frozen references

[00_three_quarter.png](references_hd/00_three_quarter.png) is byte-identical to approved drafts/00_three_quarter_v1.png:
`824d72d9d9c7fac46ff34e8a09f1131e7fe29939736e48962d8d311ccbb50776`.
The approved image overrides the older brief: **two near-side capacitor pods, upper/lower, four barrel rings and
the muzzle crown**. The long slab head, six backswept fins, side core, yoke and mount remain. V2 remains rejected.

| Master | View |
|---|---|
| [00_three_quarter.png](references_hd/00_three_quarter.png) | Frozen primary; sole Smart Topology input |
| [01_front.png](references_hd/01_front.png) | Axial front; pods on viewer-left |
| [03_left.png](references_hd/03_left.png) | Opposite flank, muzzle left; no duplicated pods |
| [02_back.png](references_hd/02_back.png) | Rear; pod caps on viewer-right, closed rear plate |
| [04_right.png](references_hd/04_right.png) | Pod-bearing flank, muzzle right |

All are unresized 1536×1024 RGBA imagegen returns with true alpha and complete silhouettes.
[Reference sheet](references_hd/selected_views_review.png); prompts, hashes and candidate selection are retained in
references_hd/generation_runs.json. Hidden rear/opposite surfaces are conservative reconstructions; the generated
views are near-orthographic references, not measured CAD. The integrator accepted the finished model in all seven viewer states (P3, 2026-10-23).

## Meshy jobs for the integrator

**Both jobs SUCCEEDED; do not resubmit.** The backup account was used through tools/creature_meshy.py.
Keep the recorded receipts and raw downloads unchanged. Actual spend is 15; unused reserve is 25 credits.

| Job | Recorded settings and inputs | Return | Credits |
|---|---|---|---:|
| ion_cannon_geometry_v1 | image-to-3d; meshy-t2; smart-topology; target_polycount 12000; should_texture false; glb; no pose_mode; references_hd/00_three_quarter.png | meshy/ion_cannon_geometry_v1/model_urls_glb.glb | 5 |
| ion_cannon_retexture_v1 | retexture; meshy-7; enable_original_uv true; enable_pbr true; 2k; glb; work/ion_cannon_neutral_upload.glb; masters front, left, back, right in that order | meshy/ion_cannon_retexture_v1/model_urls_glb.glb and texture_urls_0_* maps | 10 |

Exact request bodies remain in requests/. No rigging or animation job is needed.
Raw geometry SHA-256: `98b798a4f2d4daf4f71a049558a1ee3bc7ad43687e49d7f7bc1d783105977abd`.
Frozen upload SHA-256: `b273355734aa1593f053e1f8085638c5879f86ffa9e93df69bff9fc7a1c04e6e`.
Raw retexture GLB SHA-256: `1b8c1533f64720347a0f628dce361bf3344a98a43aa5d45e45dbce4e4cc5820d`.

## Geometry, scale and integration

COMBAT's dimensions are a **5,000-unit head / 2,000-unit yoke**; authoring metres at runtime scale 100.
Blender forward −Y / up +Z; glTF forward +Z / up +Y. Origin is the bottom mount's centre, minimum Z=0.
Bounds are **50.05 m along the barrel, 30.99 m across the bastion and 24.70 m high**; outer yoke pivots about 19.2 m apart.

The old Crown muzzle anchor `(0, -38, 12)` m does not match this model. The measured front-axis marker is
**Blender `(0.048917, -31.889364, 11.505241)` m**, glTF `(0.048917, 11.505241, 31.889364)` m.
At scale 100 this is map-local **`(4.9, -3188.9, 1150.5)` units** before the decoration's rotation/translation.
The Crown builder must align the shot origin when replacing the decoration. Keep the approved proportions.
No map, event, binding, actor height or runtime stage was edited here; integration/actors.yml remains empty.

Prior geometry preparation corrected Meshy's mirrored far-flank pod pair and two broad jaws to the approved
near-side upper/lower pair and three narrower prongs. A recessed 220-triangle resin liner closes exposed barrel
interiors. The six fins, core, collars, yoke and mount remain. Source-component and zone face attributes survive
in the editable master. The opaque reduction study selected ratio 0.6; ratio 0.4 damaged fins, collars and cables.
712 shared glow-boundary vertices stayed fixed (error 0). One duplicate triangle was removed before UV preparation.
LOD0's positions, normals, UVs and indices are byte-identical to that checked zone master.

| Material | LOD0 triangles |
|---|---:|
| Opaque | 6,883 |
| GC_breech | 231 |
| GC_pods | 99 |
| GC_ring1 / GC_ring2 / GC_ring3 / GC_ring4 | 123 / 120 / 127 / 96 |
| GC_muzzle | 237 |
| Body total | **7,916** |

The ~5K rigid-machine target is exceeded for this large silhouette and seven retained glow patches, below the
15K ceiling. [Geometry study/checks](review/geometry/geometry_uv_checks.json),
[seams/scale checks](review/geometry/uv_blender_checks.json), [selected clay](review/geometry/reduction_60_quarter.png).

## Textures and charging states

The retexture return has the same 7,916 triangles and exact UV correspondence after its normalization is reversed:
maximum positional error **0.001925 mm**, UV error **0 texels**. Its external maps were applied to the checked master;
its normalized mesh did not replace our geometry. [Correspondence/material record](review/texture_return.json).

One approved ivory/gold/violet palette and one shared image set per LOD; no baked per-state colours.
LOD0 base colour is 2K, normal/ORM 1K. Source normal-Y correlation −0.998834 required flipping green to glTF +Y.
The retained material-class mask distinguishes ceramic/gold/resin (IDs 5/9/11). Roughness floors are .56/.42/.64,
metallic is .85 for gold and zero elsewhere, and ORM.R is the explicit specular mask (.55/.85/.30), not AO.
No extra AO grade was applied to the already painted base colour. Only opaque materials set
openyamm_specular_mask, and every such material has a metallicRoughnessTexture; glow never sets the flag.

Seven untextured material regions provide the four functional glow systems: core, paired pods, four rings, muzzle.
Only emissiveFactor and KHR_materials_emissive_strength change. No emissive textures or new bastion glow.
Dim violet uses factor (.24,.08,.46), strength 2; lit (.82,.68,1), strength 10; hot (1,.95,1), strength 16.

| Export | Bright zones; remaining zones dim |
|---|---|
| [hes_great_cannon.glb](export/hes_great_cannon.glb) | Rest: none bright |
| [hes_great_cannon_c1.glb](export/hes_great_cannon_c1.glb) | Core |
| [hes_great_cannon_c2.glb](export/hes_great_cannon_c2.glb) | Core + pods |
| [hes_great_cannon_c3.glb](export/hes_great_cannon_c3.glb) | Core + pods + first two rings |
| [hes_great_cannon_c4.glb](export/hes_great_cannon_c4.glb) | Core + pods + all four rings |
| [hes_great_cannon_c5.glb](export/hes_great_cannon_c5.glb) | All; white-hot muzzle and three tip-to-tip arcs |
| [hes_great_cannon_dark.glb](export/hes_great_cannon_dark.glb) | All emission zero |

The five charging swaps retain the Crown's half-second steps. Three static arcs reproduce the Crown stand-in's
c5 feature, fitted to the measured three-prong tips. The GC_Arcs node has a mesh only in c5; merely removing a
scene reference would not hide it in the native loader. Other states retain the empty node. Body/texture bytes
are identical across all seven files; all files include the same arc payload, but only c5 draws it.
[Arc anchors/counts](review/crown_arcs.json). Dark retains purple resin/base colour while emission is zero.

## UVs and LODs

LOD0's shared atlas has 2,859 islands, 35.28% coverage, 8.601-pixel minimum gutter at 2K and uniform island density
(13.397–13.415 texels/metre). Open armour plates/hard-edge seams account for the fragmentation. No sharp edge lacks
a seam. Lower LODs are separately unwrapped and reprojected from LOD0, with base/normal/ORM at 1K / 512 / 256.
Continuous triangle checks found one folded LOD2 face: its own padded planar chart and rebake remove all three
overlap pairs without changing geometry. **Every textured LOD now has zero interior UV overlaps**, finite UVs in
[0,1], positive UV/3D area and finite unit normals. [UV repair](review/lod_uv_repair.json).

| LOD | Body triangles | c5 arc triangles | c5 total |
|---|---:|---:|---:|
| 0 | 7,916 | 180 | 8,096 |
| 1 | 3,939 | 108 | 4,047 |
| 2 | 3,148 | 84 | 3,232 |
| 3 | 1,955 | 60 | 2,015 |

Far LODs use the shared lod_repair_claude pipeline in a local static-node adaptation, with the full ratio ladder
retained in work/lod_repair/work/ion_cannon/result.json. The first passing pair was **0.40 / 0.25 of LOD0**:
smaller far levels broke the fin/mount silhouettes at their switch sizes. This departs from ~50% per level for a
measured visual reason. Body and arcs have separate valid LOD chains; four reduced body shadow meshes are included.
Final rest/c5 CPU switch comparisons are in review/final_lod_audit/ and measured at 450 / 180 / 72 pixels.
LOD2 gates: outline ≤6%, colour ≤max(16, LOD1 colour+3); LOD3: outline ≤13%, colour ≤19.5.
All seven delivered GLBs report **zero inverted closed parts**. Open armour panels still need native visual review.

Final worst-view scores (outline % / colour difference):

| State | LOD1 | LOD2 | LOD3 |
|---|---|---|---|
| rest | 2.1 / 10.0 | 2.0 / 8.6 | 7.6 / 16.6 |
| c5 | 2.1 / 12.6 | 2.1 / 9.9 | 7.1 / 18.3 |

## Viewer and review boundary

[Viewer URL](http://127.0.0.1:8912/level_generation/creatures/hes_ion_cannon_codex/review/viewer/) once served by the
existing creature-review wrapper. Seven state choices preserve the camera; front/quarter/side/back and cannon-sized
focus controls are prepared, with five HD references and model hashes. Viewer copies alone contain an empty-node
one-second Standing hold to satisfy the shared UI. Runtime exports remain wholly static.

Integrator commands (rule 9; not executed by this sandbox):

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_ion_cannon_codex --tier rest check
python3 tools/run_creature_review.py --project level_generation/creatures/hes_ion_cannon_codex --tier c5 check
```

Repeat for c1, c2, c3, c4 and dark. Final artifacts, viewer hashes/dependencies, JS syntax, LOD chains, material
loader contracts and state factors pass local checks. Offline CPU renders show the seven states; they are not
browser/native captures. Three.js does not reproduce the engine's custom specular mask or final bloom. The integrator accepted all seven viewer states.
Real-GPU material/shot-origin checks, Crown binding/staging and scenarios remain integrator/map-owner work.
No engine changes/builds, assets_dev writes, Vulkan, performance runs or git staging were performed.

## Editable artifacts and reproduction

- work/ion_cannon_textured.blend: packed textured **LOD0** with original zone/source face attributes and c5 arcs
  hidden by default. Far LODs are in the GLBs, not this editable scene.
- work/ion_cannon_ready.glb: canonical final body, shared maps, LODs/shadow meshes and arc chain before state factors.
- work/ion_cannon_uv.blend, ion_cannon_zones.glb, ion_cannon_uv_triangles.npz: frozen geometry/UV/provenance inputs.
- work/ion_cannon_neutral_upload.glb and its .blend: completed Meshy upload; do not submit again.
- textures/: final LOD0 base/normal/ORM and material-class mask. Raw Meshy maps stay in meshy/.

Every project mutation runs under tools/creature_workspace.py run with a current lease. Every one-shot Blender
invocation is bounded by timeout --kill-after=15s and exits with flushed stdout/stderr plus os._exit(0).
Use /snap/blender/current/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1;
the Snap launcher cannot start here. CPU Cycles diagnostics deliberately avoid the GPU/browser.

The existing geometry scripts prepare the checked input. Returned-texture sequence: scripts/compose_textures.py,
scripts/initial_lods.py, scripts/repair_lods.py ion_cannon, scripts/repair_lod_uv.py, scripts/finish_states.py,
scripts/prepare_viewer.py, then scripts/check_finished.py. LOD work uses LOD_REPAIR_PYTHON pointing to the installed
LOD-repair environment; no dependency was added. scripts/repair_lod_uv.py intentionally asserts this selected
LOD2's known chart/face layout rather than silently repairing a different mesh. Re-evaluate it if geometry changes.
Use scripts/save_master.py through bounded Blender for the packed editable scene, and scripts/audit_lods.sh with
an output directory followed by the rest/c5 exports for CPU switch evidence. scripts/check_export_states.py is the
small exporter fixture test; review/final_checks.json covers the actual delivered files.

## POSITION bounds correction (2026-10-23)

The integrator accepted all seven states in the viewer, then reported missing min/max on mesh 4
IonCannon_Shadow's POSITION accessor 33 (13,578 vertices). Final assembly now computes bounds for **every POSITION
accessor**, including shadow and arc LODs. The actual-file gate checks each bound against the stored vertices.
It failed on the original defect and passes on all seven regenerated exports, with **40 POSITION accessors each**.

The canonical work/ion_cannon_ready.glb, all seven runtime exports, viewer copies and hashes are refreshed.
Only POSITION min/max metadata changed: accessor 33 gained bounds, and lower-shadow extrema were rounded to
match their stored float32 vertices exactly. All binary payloads and other JSON fields are unchanged; accepted
appearance and prior LOD switch evidence still apply. The stage's exact glb_extent and check_model_rules pass
all seven exports and the canonical master; decoration height is 2470 at scale 100. State fixture, actual geometry,
UV, winding, material and viewer checks pass. Details and before/after hashes are in creature_3d_progress.json's
corrections record and review/final_checks.json. No new Meshy spend (still 15/40), rerenders or staging here.
The Crown builder can now switch the seven exports and use the already supplied muzzle anchor.
