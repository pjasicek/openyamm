# MM6 BArcher arc1 — batch handoff

## Review round 6

**Scoped review complete. Attack and Cast play at 1.5x speed: 1.733333 s -> 1.155556 s; release 1.200 s -> 0.800 s.** Cast remains the exact 189-channel Attack copy under its distinct name. Every keyed pose is unchanged; only input clocks changed. The arrow becomes hidden at 0.822222 s. No thresholds were relaxed.

Walking, Standing and Fidget already had identical first/last keys, so their animation data was retained. Running binds Walking on all tiers. The exported GLB evaluator compared all 63 joints, local TRS and world matrices at exact endpoints: maximum position difference **0 mm**, maximum rotation difference **0 degrees**, matrix/component difference **0**. Zero-scale hidden-arrow matrices and local quaternion keys also match exactly.

| Clip | First / last time (s) | Max bone position / rotation difference | Left heel / toe at both ends (mm) | Right heel / toe at both ends (mm) |
|---|---|---|---|---|
| Walking | 0 / 0.800000012 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |
| Running (Walking alias) | 0 / 0.800000012 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |
| Standing | 0 / 2 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |
| Fidget | 0 / 2 | 0 mm / 0 degrees | 3.494 / 4.483 | 3.142 / 4.412 |

These are near-LOD deformed surface samples using the shared runner's heel/toe selection. Lowest sole points at both endpoints: left 1.698 mm, right 1.894 mm. Every colour/shadow LOD is recorded in [loop_endpoints.json](review/round6/loop_endpoints.json). At the final 48 Hz sample before Walking wraps (0.791667 s), left heel/toe are 3.267 / 4.379 mm and right 5.037 / 6.219 mm. This final recovery movement stays within the 10 mm contact gate; the exact final frame matches frame zero. Retaining the duplicate boundary key preserves interpolation to the floor pose.

[Loop comparison](review/round6/loop_comparison.jpg) · [Attack timing](review/round6/attack_timing_comparison.jpg) · [Attack soles at release](review/round6/browser_attack_feet.png) · [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).

### Files and integration

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
| [mm6_arc1.glb](export/mm6_arc1.glb) | 9531 / 5223 / 1904 / 620 | 6354256 | deb0919f5cbed33dacb5cdded736ad77c9edb5d88d600aedd23cfdae283669eb |
| [mm6_arc1_bow.glb](export/mm6_arc1_bow.glb) | 2108 / 1150 / 420 / 193 | 1527148 | dfeed065c007944c520815c3fdbd86a1763434f353d9dad620710928ea416c14 |
| [mm6_arc1_arrow.glb](export/mm6_arc1_arrow.glb) | 92 / 40 / 5 / 4 | 310540 | 97b3e4812fcb1ea1903d51801de5da82593d307c65798ec05794525eea6130cc |

Only the body runtime GLB changed; bow/arrow files and all triangle counts are unchanged. Body size: 6353884 -> 6354256 bytes. All meshes, normals, UVs, skin weights, materials, skeleton nodes and embedded PNG bytes equal R5. Texture memory remains **53.125 MiB**, ten shared images, 16 px dilated margins. Both bracers, carry pose, grip, all LODs, flat feet and other clips remain accepted-as-is.

**integration/actors.yml changed**, SHA-256 **e8ed0382c918813e002d7cf75ac1bf9d5b81b5febd5207f493116e879d834bfc**. Its only edit is nine impact values changing from 1.2 to 0.8 across melee/ranged/cast on all three tiers. IDs 475/476/477, scale/yaw/stride, run alias and Socket_Arrow_Release remain. Updated timing prose in integration/regression.md and integration/playbook_notes.md.

Editable masters retimed: work/rig_equipped.blend, work/rig_textured.blend, work/round2/lod0.blend through lod3.blend; runtime_authoring.blend rebuilt from the final viewer export. Rebuilt three viewer GLBs and manifest, Attack/Cast sheets, release hand-sheet timestamps and loop comparison sheets. [Full hashes/sizes](review/round6/artifact_manifest.json). R5 exports, integration, scripts and editable masters retained under review/round6/baseline/.

### Validation and open findings

Shared runner rerun on all clips, colour/shadow LODs and props: **FAIL**, {'PASS': 6507, 'INFO': 132, 'FAIL': 363, 'N/A': 72}. [Report](review/round6/shared_final/gates.md), [comparison](review/round6/shared_comparison.json). This is not an all-gates acceptance claim.

Attack/Cast feet pass on all visible LODs: heel/toe <= 5.180381 mm, sole tilt <= 0.933210 degrees, floor penetration 0. Pre-existing far shadow sole tilt and other accepted-as-is findings remain recorded.

Relative to R5, six head-contact rows now fail (10.289 mm versus 10 mm at 0.270833 s; colour0/1 and shadow0 in Attack/Cast), and four arrow-contact rows now pass. Retiming shifts the fixed 48 Hz sample phases; keyed poses are identical. No geometry or pose changes were made to chase these inherited contacts.

[check_bindings.py / skin weights](review/round6/check_bindings.log): exit 0, no BAD line. [Viewer](review/round6/check_viewer.log): all 24 tier/clip switches pass, no console errors; eight browser captures. Comparison sheets and release soles visually checked. All 71 native source files unchanged.

Decisions: kept already exact loop boundaries; interpreted Running using its Walking alias; directly retimed animation accessors to preserve accepted mesh/maps, and retimed editable masters. Budget: **0 additional credits, 40 / 100 total**. Lease released at handoff. No game launches, builds, installs, assets_dev writes or commits. Runtime regression and game captures remain the orchestrator's responsibility.

Reproduction with a reclaimed lease: scripts/round6_retime.py (reads R5 baseline), scripts/round5_viewer.py, scripts/round6_audit.py via the four-thread Blender wrapper, scripts/round6_check_viewer.py, scripts/round6_validate.py, scripts/round6_sheets.py, scripts/round6_record.py. Historical generators predate this timing pass; final exports and R6 scripts are authoritative.

## Review round 5

Carried bow corrected to the native bitmap: **front tip +18 degrees, azimuth 0, 72 degrees from vertical; string above/toward the arm, limbs below**. Wrist/grip forward offsets are 5.86% / 7.94% of body height. The closed fist stays beside the thigh in front projection. Standing bow-to-leg clearance: 48.78 mm.

Attack and its exact Cast copy use fixed flat ankle anchors, with pelvis height adjusted only where the source sway exceeds leg reach. Every visible LOD passes: heel/toe height <= 5.180 mm, sole tilt <= 0.940 degrees, no floor penetration. Accepted Standing/Fidget feet and free arm remain.

**Technical acceptance remains pending: shared gates FAIL, {'PASS': 6509, 'INFO': 132, 'FAIL': 361, 'N/A': 72}.** This delivers the scoped review correction with explicit open findings, not an all-gates PASS.

[Native comparison](review/round5/native_rest_comparison.jpg) · [Attack feet in viewer](review/round5/browser_attack_feet.png) · [Texture comparison](review/round5/texture_comparison/comparison.jpg) · [Shared audit](review/round5/SHARED_AUDIT.md) · [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).

### Files and integration

| File | LOD0 / 1 / 2 / 3 triangles | Bytes | SHA-256 |
|---|---|---:|---|
| [mm6_arc1.glb](export/mm6_arc1.glb) | 9531 / 5223 / 1904 / 620 | 6353884 | 8cb0a08e1e03660a4e9b385b95db59417d4f91def511c757ecbb7b1618c8da72 |
| [mm6_arc1_bow.glb](export/mm6_arc1_bow.glb) | 2108 / 1150 / 420 / 193 | 1527148 | dfeed065c007944c520815c3fdbd86a1763434f353d9dad620710928ea416c14 |
| [mm6_arc1_arrow.glb](export/mm6_arc1_arrow.glb) | 92 / 40 / 5 / 4 | 310540 | 97b3e4812fcb1ea1903d51801de5da82593d307c65798ec05794525eea6130cc |

All three runtime files changed. Every colour/shadow LOD retains R4 geometry, indices, normals and skin weights. UV/maps change for memory; body animation changes for carry/feet. Body shadows have the same counts as colour LODs. The 24-triangle moving string, 63 joints, eight clips, both bracers and all tier ramps remain.

**integration/actors.yml is unchanged**, SHA-256 3066be3ca5ce53eebfb9fcbd13a544b8566650edd40a751832fad521f1f01677.
IDs 475/476/477 and scale/yaw/stride are unchanged. Cast exactly copies Attack under the distinct Cast name (189 channels). Events remain **1.200 s / Socket_Arrow_Release**, no palm_right.

Updated masters: work/rig_equipped.blend, rig_textured.blend, runtime_authoring.blend, and work/round2/lod0.blend through lod3.blend. Fitted masters retain source UV maps; runtime_authoring imports the final packed tier-A GLB. [Artifact hashes](review/round5/artifact_manifest.json) cover scripts, config, exports, viewer, sheets and masters. [Previous R4 handoff](review/round5/baseline/HANDOFF.md).

### Native measurements

| Measurement | Native | Round 5 | Unit |
|---|---:|---:|---|
| Wrist lateral / height | 5.469 | 7.192 | % |
| Wrist forward / height | 5.859 | 5.859 | % |
| Grip lateral / height | 7.031 | 7.390 | % |
| Grip forward / height | 7.812 | 7.944 | % |
| Upper arm: front | 0.000 | 8.365 | deg |
| Forearm: front | 5.356 | 8.365 | deg |
| Upper arm: side (+ forward) | 3.366 | 3.583 | deg |
| Forearm: side (+ forward) | 24.567 | 28.803 | deg |
| Elbow bend: side | 21.201 | 25.220 | deg |
| Bow from vertical | 72.224 | 72.000 | deg |
| Bow azimuth from forward | 0.000 | 0.000 | deg |
| Front tip pitch (+ upward) | 17.776 | 18.000 | deg |

Native visible landmarks have +/-2 px uncertainty; inferred hip +/-6 px at 256 px height. Azimuth is inferred from the end-on front view. Front-projection wrist mirror error is 21.91 mm (lateral mismatch alone 3.81 mm). The 25-degree elbow bend places the fist slightly higher than the open free hand while attaining the forward target. Differences remain visible in the table.

Near grip across all clips: gap <= 2.408 mm; penetration <= 0.807 mm. Bow/body penetration is zero throughout. Hit keeps the bow orientation steady while carrying outward; forearm axial rotation distributes strain without changing the held hand frame.

### Texture memory

| Asset | Shared images | Final dimensions per map | Linear density factor |
|---|---:|---|---:|
| mm6_arc1.glb | 4 | 1568 x 1376 | 0.75 |
| mm6_arc1_bow.glb | 3 | 896 x 1120 | 0.875 |
| mm6_arc1_arrow.glb | 3 | 768 x 992 | 1.0 |

**10 images before and after**, one shared set per asset across all LODs. RGBA8 base-level decoded memory: **89.546875 -> 53.125000 MiB**, below R3's 53.5 MiB. Full mip chains are approximately 4/3 of these figures. Total GLB bytes: **9,697,760 -> 8,191,572**.

The explicit R5 memory cap takes priority over the older exact-density requirement. Tighter polygon packing alone could not fit full-density charts plus padding. Body maps use .75x linear resolution, bow .875x, arrow unchanged. Colour/normal/material maps use Lanczos; the region mask uses nearest sampling. Every map has **16 px dilated margins**, packed by conservative polygon occupancy on a four-pixel grid. UV triangle shape is preserved at the stated density. This is a documented density tradeoff.

Eight matched views at approximately 700 actor pixels: **minimum textured SSIM 0.98489 >= .95**, silhouette IoU 1.0. [Metrics](review/round5/texture_comparison/metrics.json) · [Packing](review/round5/texture_sets.json).

### Validation and retained faults

check_bindings.py **PASS, no BAD line**, including skin weights/materials. Viewer **24/24 switches, zero errors, eight captures**. All 71 read-only native hashes match. Exact Attack/Cast equality, rest boundaries, triangle caps and geometry preservation pass. Release direction remains 1.947 degrees from forward; socket/string timing is retained. [Delivery checks](review/delivery_validation.json).

Shared gates remain FAIL: distant grip gaps, inherited palm cone, action elbow/roll/cloth, drawn-arrow/head findings, and the farthest shadow sole remain. Intended body-opening classification is UNVERIFIED. Newly activated Attack/Cast rest-palm/yaw checks are preserved in the raw report. [Every gate](review/round5/shared_final/gates.md) · [R4 changes](review/round5/shared_comparison.json).

Triangle counts stay fixed as requested. The historical [near reduction curve](review/round2/reduction/curve.png) records body IoU .99461 / SSIM .96445; the next 8,555-triangle candidate failed at .9447 SSIM. Current equipped switch-size silhouettes:

| LOD | Clip | Pooled IoU | >= .97 |
|---|---|---:|---|
| 1 | Standing | 0.98705 | True |
| 1 | Attack | 0.98533 | True |
| 2 | Standing | 0.97462 | True |
| 2 | Attack | 0.96710 | False |
| 3 | Standing | 0.96230 | False |
| 3 | Attack | 0.93129 | False |

[Distance sheet](review/round5/reduction/distance_sheet.jpg). No triangles were added to hide these failures.

### Reproduction and scope

Use the project lease and tools/run_creature_blender.sh, one background Blender with --threads 4. round5_motion.py authors and exports; snapshot the three runtime GLBs to work/round5/runtime_unpadded, then run round5_textures.py, round5_arrow_export.py and round5_viewer.py. round5_render.py runs gates and refreshes sheets/measurements. round5_final_audit.py refreshes the packed master and release/Hit evidence. Finish with round5_check_viewer.py, round5_validate.py, round5_sheets.py and round5_records.py. CPU Cycles avoids the host's Workbench crash.

Budget **40/100 credits, zero this round**. No game launch, build, installation, assets_dev/assets_source copy or commit. Installation/game checks belong to the orchestrator. Lease released at handoff.
