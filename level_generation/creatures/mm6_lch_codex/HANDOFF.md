# MM6 BLich / lch — review round 2

**PARTIAL — not ready for integration.** LOD0 passes close-up visual thresholds; the complete round-2 done criteria are not met. This staged package is for review and is not installed.
Budget: **30/100 credits consumed; 0 new; 70 remaining**. No commits, builds, game launches, shared-file edits or writes to assets_dev.

## Triangle reduction (rebake)

| LOD | Accepted before | Round 1 | Round 2 | % LOD0 | Actor px | Pooled IoU | Min IoU | Min SSIM, all tiers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 16,274 | 7,824 | 6,290 | 100.0% | 700 | 0.992919 | 0.991397 | 0.972880 |
| 1 | 8,135 | 7,787 | 3,466 | 55.1% | 550 | 0.973773 | 0.970297 | 0.883467 |
| 2 | 2,907 | 6,916 | 2,907 | 46.2% | 220 | 0.943076 | 0.939496 | 0.895645 |
| 3 | 897 | 6,710 | 897 | 14.3% | 88 | 0.841303 | 0.816976 | 0.750558 |


The chain is **6,290 / 3,466 / 2,907 / 897**. LOD0 is **61.3% smaller** than the accepted master and 19.6% smaller than round 1. Its minimum 700px IoU is **0.991397** and minimum SSIM across all three tiers **0.972880**. LOD1 passes silhouette but fails textured comparison. LOD2/3 fail the new silhouette and ratio targets. No far LOD exceeds its previous count.

[700px tier pairs](review/triangle_rebake/tier_comparison_700px.png), [LOD0 eight views](review/triangle_rebake/eight_views_lod0.png), [550px](review/triangle_rebake/eight_views_lod1.png), [220px](review/triangle_rebake/eight_views_lod2.png), [88px](review/triangle_rebake/eight_views_lod3.png).
[Curve CSV](review/triangle_rebake/reduction_curve.csv), [per-view metrics](review/triangle_rebake/packaged_metrics.json), [preservation](review/triangle_rebake/preservation.json).

The reference at every switch size is the unreduced accepted 16,274-triangle LOD0. Eight yaw views at 45-degree intervals; orthographic actor heights 700 / 550 / 220 / 88 px. Final comparisons import the packaged GLBs, use the exact engine linear-luminance tier ramps, and render base color, ORM and tangent normals under identical Cycles lighting (24 samples, fixed seed, no denoising). SSIM uses the joint object crop plus eight pixels. No cheaper reference or subjective override turns a failing measurement into a pass.

The close-up search collapses in approximately 10% steps with weighted face, fingers, joint ends and eight-view outlines, retaining original leg/tatter contact pieces. LOD0 stops at 6,290; the next 5,660 step has minimum IoU 0.987633 and is rejected. All bone weights and clips remain unchanged. There is no held weapon, staff or shield. The attached crown is included in body reduction, silhouette checks, rebakes and the head review.

Base color, region mask, ORM (R specular class, G roughness, B zero) and tangent +Y normals were projected from the accepted source onto every selected LOD. Corresponding parts are exploded for LOD0; corresponding rigid bone groups for LOD1-3. A white ray-hit bake supplies padding coverage. Each LOD occupies a padded rectangle in the same shared 1024x1024 body and 1024x1024 head sets; full 1K individual bakes remain in textures/round2/lod0..3/. Runtime has four 2080x1024 atlases and the unchanged three variant materials. Effective texels per set are 752x1008 / 224x480 / 224x224 / 224x224; this allocation limits distant texture fidelity and is not claimed lossless. UVs retain their parameterization for baking, then receive an affine atlas mapping.

Weighted/direct collapse, piece allocation, surface/bounds fitting and voxel-union trials did not produce acceptable cheap far silhouettes. LOD2/3 therefore retain the previous accepted geometry at 2,907 / 897; positions, normals, weights and index bytes are verified unchanged. Their new 25% / 10% ratios and pooled IoU >=0.97 are NOT achieved. LOD1 passes pooled silhouette, but its textured SSIM is only about 0.883. No distant LOD was made denser. A rest-normal-transfer trial did not improve LOD1 and was reverted.


G4/G5 and whole-mesh edge preservation pass on every clip at 48 Hz; the final exported source-relative rotation trace has no flags. Rig nodes, 54 joints including both sockets, inverse binds and every animation sample byte are identical to the accepted export. Palm directions, elbow planes and forearm roll remain unchanged; maximum forearm roll is 12.402 degrees.

Absolute rig criteria still fail. Accepted Attack hyperextension is 14.657 degrees left / 9.643 right against a 5-degree limit. LOD0 cloth crossings match the accepted baseline exactly, up to 17.615 mm against 2 mm. The old cheap far geometry also fails contacts: LOD2 Attack right hand 48.131 mm and LOD3 Walking cloth 32.612 mm. These failures are not waived. The contact test samples nearest faces and edge crossings on open tatters at 48 Hz, not continuous collision. Whole-mesh lowest points across clips are -0.517 / -6.936 / -1.345 / -5.944 mm for LOD0-3. Frozen accepted clips were not silently reposed to repair the inherited elbow failure.

| Clip | Max G4 | Max G5 | Max head mm | Cloth mm LOD0 / 1 / 2 / 3 | Other failure |
|---|---:|---:|---:|---|---|
| Standing | 1.000019 | 1.000018 | 0.000 | 2.469 / 0.000 / 1.263 / 0.000 | none |
| Walking | 1.000018 | 1.000019 | 0.000 | 15.577 / 11.818 / 18.410 / 32.612 | none |
| Attack | 1.000026 | 1.000025 | 0.000 | 6.167 / 0.000 / 4.104 / 0.000 | LOD2 right hand 48.131 mm |
| Cast | 1.000029 | 1.000035 | 0.000 | 6.367 / 0.000 / 7.460 / 0.000 | none |
| Hit | 1.000019 | 1.000018 | 0.000 | 2.445 / 0.000 / 0.000 / 0.000 | none |
| Death | 1.000021 | 1.000021 | 7.812 | 17.615 / 15.363 / 9.659 / 0.000 | none |
| Dead | 1.000011 | 1.000011 | 0.000 | 7.003 / 6.275 / 3.517 / 0.000 | none |
| Fidget | 1.000021 | 1.000024 | 0.000 | 3.302 / 0.000 / 1.617 / 0.000 | none |


## Review round 2

Changed project files: runtime/intermediate GLBs below; selected LOD geometry; base-color, mask, ORM and normal rebakes in textures/round2/; atlas UV layout; tier viewer GLBs and manifest; comparison/clip/head/hand sheets; project-local scripts, validation, progress, README and this handoff. The runtime is **9,371,356 bytes**, 54 joints, eight unchanged clips, three unchanged tier definitions, four color LODs and four shadow LODs.

**integration/actors.yml did not change. No integration file or assets_dev file was changed.** Sockets, scales, impacts, clip bindings and accepted props are unchanged. Exact animation/bind/material preservation and atlas bounds are asserted in preservation.json.

| File | SHA-256 |
|---|---|
| [export/mm6_lch.glb](export/mm6_lch.glb) | `045ab49c0782ee13944b36d427a409cdd3f5965d678ad8d0c1de40b7aaa4f4bb` |
| [export/mm6_lch_runtime_lod0.glb](export/mm6_lch_runtime_lod0.glb) | `3ca49bb1cd3cf975d4f429f96fbd5e72b595abce0995c09dc062e6c2b7173fe7` |
| [export/mm6_lch_lods.glb](export/mm6_lch_lods.glb) | `d302b9390b9a00a11d2526643207adf0f074955513c3423259f45252039bd625` |
| [export/mm6_lch_lods_shadowfix.glb](export/mm6_lch_lods_shadowfix.glb) | `c2101c557d24eec8b22abdecaaabf8f2fb28809277fd4c5f55c62e668447e6df` |
| [review/viewer/manifest.json](review/viewer/manifest.json) | `0548a0abbce198bea4658471f8f9f52cf3c127184f8d7f48c3db6b4e55192f2e` |
| [review/viewer/mm6_lch_a.glb](review/viewer/mm6_lch_a.glb) | `c569a320c1623f7dd38a9bfea8562236648c514e3a94fb9ca519d6a2f0c3ed61` |
| [review/viewer/mm6_lch_b.glb](review/viewer/mm6_lch_b.glb) | `fe690c462b370c60326bec71ce8b673e10261aa559c8af01b0c28df073ab432e` |
| [review/viewer/mm6_lch_c.glb](review/viewer/mm6_lch_c.glb) | `a46dd2dc2e012a8701cffdf5ce4292ccee35499eeb7e147f932c39b920806692` |
| [integration/actors.yml](integration/actors.yml) | `2033f4e7f77885b834410020a6492003f919b27f983f5c31ecf1812eba9d3b8d` |
| [work/round2/lod0_selected.blend](work/round2/lod0_selected.blend) | `713d336cdc6c2d5338ac01e83f6351161302c996dbc3a9fd1258938e05692ea4` |
| [work/round2/ceiling1_0.1.blend](work/round2/ceiling1_0.1.blend) | `47d20954ad5a531330ff80e5d39dcb8f3b5bff7cf33d22db14298daeb6ef8186` |
| [work/round2/lod2_accepted.blend](work/round2/lod2_accepted.blend) | `9828a86b9ab87c7c8665cdc26bc43dca61ff860c0b0142151d08d3d87b6b37c7` |
| [work/round2/lod3_accepted.blend](work/round2/lod3_accepted.blend) | `4ae57318946096c2adb31ad9c43e45972043b0f6f256d6e0f9f9041cc82f499e` |
| [textures/round2/lch_basecolor_1k.png](textures/round2/lch_basecolor_1k.png) | `071210aef4106b341066f5b6b2ba9806a01783c37b68b734137f9f4bf62e632c` |
| [textures/round2/lch_head_basecolor_1k.png](textures/round2/lch_head_basecolor_1k.png) | `f317d4cf241b98120a013adcf52234003da28653647db0d25474eebe63fd5608` |
| [textures/round2/lch_head_metal_rough_1k.png](textures/round2/lch_head_metal_rough_1k.png) | `d3b883c204a45a0680e2974f650cbec4247aeac1e5bc49fb66c4bea07d3da89a` |
| [textures/round2/lch_head_normal_1k.png](textures/round2/lch_head_normal_1k.png) | `30149945d6dba7f77ed2e0f646962193c197e0d7b412a60cad88fccb1f38aa22` |
| [textures/round2/lch_head_region_mask.png](textures/round2/lch_head_region_mask.png) | `59141e9a74fea7b8e5ccee9078846a0efaaab2e3628f0fd0f6c472b4c1ca8322` |
| [textures/round2/lch_metal_rough_1k.png](textures/round2/lch_metal_rough_1k.png) | `50ccce173ef1faf539c5847cd170a89ef1edf9802e5f714a116bbf932d8c0a7f` |
| [textures/round2/lch_normal_1k.png](textures/round2/lch_normal_1k.png) | `90064a3c7c61398f3acb8eb647e6eadd723a980d40f0e1a012b2038c14f3ebae` |
| [textures/round2/lch_region_mask.png](textures/round2/lch_region_mask.png) | `0fc4121e965548a5b2073009b498f6ee7f1b47dcd2ea3c9d3b22c9c1fb90bf9c` |


[All hashes JSON](review/triangle_rebake/artifact_hashes.json). Previous round-1 runtime: `d2b1010b8f16f37b7a31cf8d0f9b39b90c869d9452d79bbed62128bf4d1c6d75`. Accepted source runtime: `4bdedce0ec3f051cbc01e9d27ebad9c2dd4bbc4bf440846a48da622ef8dbcee9`.

## Checks and remaining work

- [Bindings](review/check_bindings.log): return 0, no BAD line, worst weight-sum error 0.
- [Viewer](review/check_viewer.log): 24 tier/clip switches pass, no console errors; four browser captures; checker-owned Chrome processes closed.
- [Structural validation](export/validation.json), [48Hz gates](review/triangle_rebake/gate_summary.json), [rotation trace](work/trace_export.json), [trace hash](work/trace_source.json).
- Updated [front](review/clips_front.png), [side](review/clips_left.png), [three-quarter](review/clips_three_quarter.png), [tiers](review/tiers.png), [head/crown](review/head.png), [hands](review/hands.png).
- Further far-LOD geometry/material refinement is required. Absolute elbow/cloth gates also remain unmet for the frozen accepted clips. Do not treat this candidate as satisfying the full batch done criteria.
- No native game checks or builds: the batch rules reserve regression and indoor/outdoor captures for the orchestrator.


## Integration contract

Keep integration/actors.yml: BLich A/B/C IDs 568/569/570, tiers lch_a/b/c, scale 111.6, yaw -pi/2, stride 1.284 m, Running aliases Walking. Attack release 0.729 s from right palm; Cast 0.625 s from left palm; Hit 0.733 s. The [local viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_lch_codex/review/viewer/) shows the staged close-up; it is not evidence that far LODs pass.

## Review round 1

[Archived handoff](review/triangle_rebake/round1_archive/HANDOFF.md) and [round-1 measurements](review/triangle_reduction/README.md) are historical. Its 7,824 / 7,787 / 6,916 / 6,710 chain is superseded and must not be integrated.

Workspace lease: released after final receipt/link checks. The final runtime and review hashes were cross-checked; no checker-owned Blender or Chrome process remains.
