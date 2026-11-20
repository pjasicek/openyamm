# MM6 BMonk (mnk1) — technical handoff

**Review round 4 complete for batch handoff.** The accepted round-3 appearance and motion are preserved in a reduced, rebaked export. New artistic acceptance and native integration remain with the orchestrator. **20/100 Meshy credits total; zero new credits.** No install, shared-file edit, build, game launch or commit.

## Review round 4

Re-exported the body and all LODs, rebaked the shared textures, refreshed all tier viewers, clip sheets and browser playback. **integration/actors.yml changed: no**; SHA256 `38dc7ac1bda1153fe09c6a5c38df09458fff831c4b8f81e23e51ed36d8eff92e`. IDs, scale, yaw, sockets, releases, tier ramps and all nine animation sample streams are unchanged. The frozen accepted source is [review/round4/before/](review/round4/before/).

Changed assets: runtime and editable exports, `work/animation_finish.blend`, four shared texture maps, three viewer GLBs/manifests, and review evidence. The reduction/bake/LOD/gate scripts are under `scripts/review4_*.py`; export and manifest helpers are retained. The [receipt](review/round4/receipt.json) gives the selected file hashes and script inventory.

Runtime: **11,322,920 bytes**, **118 joints**, up to eight influences, nine clips sampled at 60 fps. Colour and shadow triangle chains are both **7047 / 3804 / 1690 / 701**. No props were added or changed: this is the accepted unarmed monk.

## Triangle reduction (rebake)

LOD0 falls from **12,364 to 7,047 triangles (43.0% fewer)**. Freeze the accepted mesh's actual render tessellation before collapse; this prevents a different triangulation of cloth quads from changing its shading. Protect hands, deformation/contact regions and silhouette samples, then unwrap the reduced surface and rebake from the unreduced accepted surface. The bake transfers base colour, region mask, ORM and high-surface tangent normals, preserving the runtime +Y-up normal convention. Supersample at 4K, pad islands and resolve to the existing **2K base + 1K normal/ORM/mask**, with the same three tier ramps. The accepted hollow hood has no separate face/head texture set to replace.

[Eight-view side-by-side](review/round4/comparison.png) · [24 tier/view metrics](review/round4/visual_metrics.json) · [bake record](review/round4/rebaked/bake.json) · [curve](review/round4/reduction_curve.json).

| Triangles | Minimum 8-view IoU | Full-frame SSIM | Decision |
|---:|---:|---:|---|
| 12364 | 1.000000 | 1.000000 | Accepted round 3 source |
| 7912 | 0.994237 | 0.968785 | Pass; reduced further |
| 7047 | 0.990979 | 0.956173 | Selected; all rig/cloth gates pass |
| 6800 | 0.988781 | — | Rejected before rebake: side silhouette IoU < .99 |
| 6182 | 0.981300 | — | Rejected before rebake: side silhouette IoU < .99 |

The comparison uses fixed 800×800 frames with approximately 700-pixel actors and actual tier materials. Minimum full-frame SSIM is **0.956173**. The separately reported foreground-only minimum is **0.750704**, below .95: fine weave sampling shifts in the rebake. Agent side-by-side inspection found the same silhouette, colours, cloth folds and weave scale; the report does not claim foreground SSIM passes. The supplied images retain the evidence for artistic review.

| LOD | Round 3 triangles | New triangles | % of LOD0 | Actor px | IoU |
|---|---:|---:|---:|---:|---:|
| 0 | 12364 | 7047 | 100.00% | 700 | 0.990979 |
| 1 | 9272 | 3804 | 53.98% | 550 | 0.997289 |
| 2 | 8654 | 1690 | 23.98% | 220 | 0.983726 |
| 3 | 8035 | 701 | 9.95% | 88 | 0.971609 |

LOD0 reports the minimum view; distant LODs report pooled eight-view IoU. All distant levels pass **.97**, strictly decrease, satisfy **55/25/10%** and stay below the installed **6212/2235/744** caps. [LOD1 pairs](review/round4/lod1_comparison.png) · [LOD2 pairs](review/round4/lod2_comparison.png) · [LOD3 pairs](review/round4/lod3_comparison.png) · [metrics](review/round4/lod_metrics.json).

LOD3 allocates more vertices to the Standing outline and lowers its always-covered shoe roof to 4.5 cm, preventing a coarse Death hem crossing. This is confined to the lowest LOD; all accepted rig, cuff and leg-driven robe animation remains unchanged. Two degenerate triangles disappear during LOD3 glTF export (703 authoring / 701 rendered).

## Gates

All nine clips pass LOD0 G4/G5/G6: arm p99 max **1.941734**, hand edge max **2.680344**, contact **0 mm**. Both elbows pass at 48 Hz, max out-of-plane **0.296487°**. Runtime export parity max **0.042812 mm**, rotation trace **0 flags**. Joint hierarchy, rest transforms, inverse binds and animation bytes match round 3, including palm frames and releases: [preservation](review/round4/preservation.json).

All four colour LODs pass signed-distance cloth containment on every clip at 48 Hz (endpoints included), **0 invalid vertices**, tolerance .01 mm. Hands may leave only beyond their animated cuff opening; folded hands may be inside either sleeve. Boots may exit only through/below the local hem. Labelled LOD masters match the exported geometry; LOD packing checks joint remapping and inverse binds.

| Clip | 48 Hz samples | Sleeve mm LOD0/1/2/3 | Robe mm LOD0/1/2/3 | G4 L/R |
|---|---:|---|---|---|
| Attack | 62 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.925 / 1.913 |
| Cast | 49 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.942 / 1.879 |
| Dead | 49 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.455 / 1.625 |
| Death | 97 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.457 / 1.626 |
| Fidget | 97 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.457 / 1.625 |
| Hit | 25 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.457 / 1.625 |
| Running | 40 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.457 / 1.625 |
| Standing | 97 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.457 / 1.625 |
| Walking | 40 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 1.457 / 1.625 |

[All-LOD penetration](review/round4/penetration_summary.json) · [dense rig](review/round4/gates_dense.json) · [contacts](review/round4/g6_contacts.json) · [elbows](review/round4/elbows.json) · [gait](review/round4/locomotion.json) · [export trace](review/round4/export_trace.json).

Standing has **zero visible hand vertices**, 121 samples at 60 Hz × 26 views on the actual runtime; level error **2.428 mm**. Walking/Running swing clearance remains **8.55–8.58 cm**. Sleeve/torso density ratio **0.9753**, sRGB luminance ratio **1.0033**, sleeve UV anisotropy p95 **1.5812**; [cloth metrics](review/round4/cloth_metrics.json). UVs have no zero-area triangles. Maximum runtime weight-sum error **1.19e-07**, all LODs and shadows. [Bindings check](review/round4/bindings.txt) prints **no BAD line**.

Viewer check: **27/27**, zero failures/console errors. [Record](review/round4/viewer_check.json). Playback: nine clips × normal/half speed, 18 runs and 90 captures. [Front clips](review/clips_front.png) · [side clips](review/clips_left.png) · [three-quarter clips](review/clips_three_quarter.png) · [tiers](review/tier_comparison.png) · [normal playback](review/playback_normal.png) · [half-speed](review/playback_slow.png) · [close-ups](review/round4/closeups.png).

## Selected file hashes

| File | SHA256 |
|---|---|
| [export/mm6_mnk1.glb](export/mm6_mnk1.glb) | f9bae7487780316c3ce7ba3563d3047e3c02e7133bf61ca78fa27e02d2d0c554 |
| [export/mm6_mnk1.blend](export/mm6_mnk1.blend) | 050d1324d45cf814c5ab438fdd1bcd505a014d1d9c314210e415790c1dc0d471 |
| [export/mm6_mnk1_lod0.glb](export/mm6_mnk1_lod0.glb) | 10d136c4b0726991cc24ae32e05c99f41e3c1ada042c69b39ec93589f97c58aa |
| [work/animation_finish.blend](work/animation_finish.blend) | b80daf3fbceef09abb001d70fe3f4f40a7fde2b4971d1eac359c214591390329 |
| [review/viewer/mm6_mnk1_a.glb](review/viewer/mm6_mnk1_a.glb) | ca5d67fc8b104bb54d1042bbc0d27c31e245d6c7b85f2df4917af04b1ff4ca61 |
| [review/viewer/mm6_mnk1_b.glb](review/viewer/mm6_mnk1_b.glb) | af4fa2b0f6b394f65d8ecb908a2116f6293758b45a9f938e8eb3ff2e7907c987 |
| [review/viewer/mm6_mnk1_c.glb](review/viewer/mm6_mnk1_c.glb) | 3c706be6db3243ff093be25799a7daea9e963901a305409641a88efd8d04d5b6 |
| [textures/mnk1_basecolor_2k.png](textures/mnk1_basecolor_2k.png) | 461bfcd5767f8ef0fa437b509ab037e32cec5c63a1c78d786c7f43ac46179693 |
| [textures/mnk1_region_mask.png](textures/mnk1_region_mask.png) | ac32013f35fcc994f6f68e01d6e2eb9d7621f65db9f589f6f1a6770a9e39a1a2 |
| [textures/mnk1_orm_1k.png](textures/mnk1_orm_1k.png) | 66e13f5201bf005e9a9a13722eca7597824fef8cd2f218fdb710486718d4138e |
| [textures/mnk1_normal_1k.png](textures/mnk1_normal_1k.png) | b9ffdbe37209f12f96ea506a6246155727216a1871471b30ed1f508cfda1ecdb |
| [textures/mnk1_ramps.json](textures/mnk1_ramps.json) | f25664c18ecba401941b9385b4b9d65a65aedf10926fa8510b87d6da2df726c0 |
| [integration/actors.yml](integration/actors.yml) | 38dc7ac1bda1153fe09c6a5c38df09458fff831c4b8f81e23e51ed36d8eff92e |

Animation SHA256: `4778daf998c0f97bd0211cad54e72cd652aae9913b6190fefb9f7612f34efc99`.

## Integration and remaining work

The orchestrator installs [export/mm6_mnk1.glb](export/mm6_mnk1.glb), retains [integration/actors.yml](integration/actors.yml), then runs [integration/regression.md](integration/regression.md) and indoor/outdoor captures. No selected-asset numeric gate remains failing. Native lighting, LOD switching/performance and artistic acceptance remain integration/review work; this is not a game-run certificate.

BMonk A/B/C IDs **583/584/585**, scale **105.142549**, yaw **−1.570796327**, stride **1.57**, run→Walking. Sockets: Socket_Palm_Left/Right. Releases: **Attack 0.716667 s**, **Cast 0.450000 s**. The original sprite-restore project remains read-only.

## Earlier reviews

[Round 3 handoff and accepted source](review/round4/before/HANDOFF.md) records the forearm-following retracting cuffs and leg-driven hem fixes. [Round 2](review/round3/before/HANDOFF.md) established distinct tapered sleeves and matching weave; [round 1](review/round2/before/HANDOFF.md) established covered, level hands. Their old reduction thresholds/counts are superseded by this round.
