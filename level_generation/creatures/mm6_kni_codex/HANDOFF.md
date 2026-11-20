# MM6 KnightPlate handoff

**Review round 3 exported, 2026-10-12.** Body LOD0 **11,100 -> 8,403 triangles (-24.30% this round;
-34.43% from the accepted unreduced 12,815)**. Sword remains exactly 1,985 triangles.
Combined LOD0 is **13,085 -> 10,388 (-20.61%)**. Skeleton, clips, tier ramps, props and bindings are preserved.

**The full absolute checklist is not all-pass:** LOD0–2 use the allowed perceptual SSIM alternative, and the
accepted Attack elbow-plane/LOD3 G4 findings remain. Exact scores, visual judgment and baseline evidence are below.
Authorized reduction work is complete; this is not a claim of new user artistic acceptance.

## Review round 3

Only body/colour-shadow geometry, rebaked body maps, lower-LOD normal materials and review assets changed.
**Replace only `export/mm6_kni.glb`** relative to the orchestrator's installed round 2.
The sword and **integration/actors.yml are byte-identical**. No descriptor, attachment, launch, grip or timing edit
is required. All 58 joints, inverse binds and eight original clip arrays remain exact.
Existing `cast: Attack` aliases and Sword/SwordTip nodes are preserved.

Meshy **30/100 credits total, zero this round, 70 remaining**. No commits, game launches/builds,
runtime installs, shared-source changes or writes to the sprite-restore project. Lease released at handoff.

### Triangle reduction (rebake)

| LOD | Body round 1 | Body round 2 | Body now | Sword unchanged | Combined now | Min IoU | Min SSIM |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 12,815 | 11,100 | 8,403 | 1,985 | 10,388 | 0.990771 | 0.940053 |
| 1 | 6,467 | 5,980 | 5,172 | 1,131 | 6,303 | 0.990655 | 0.896411 |
| 2 | 2,314 | 2,314 | 2,110 | 451 | 2,561 | 0.990698 | 0.916842 |
| 3 | 754 | 697 | 697 | 180 | 877 | 0.997856 | 0.972225 |

Body shadow LODs have the same triangle counts as colour LODs. Combined counts are
**10,388 / 6,303 / 2,561 / 877**, previously **13,085 / 7,111 / 2,765 / 877**. No shield.

Protected ~10% reduction sweeps preserve helmet/face, hands/fingers, deformation regions, silhouette and grip.
The next 7,564-triangle LOD0 step fails IoU .988316. An outline-preserving ~6.1k attempt lost interior armour form
after rebaking and was rejected. Lower LODs were measured at switch sizes, not fixed half-count ratios.
LOD3 stays at its round-2 697 because the 678 candidate worsened an existing G4 finding.

LOD0 is judged at ~700 px actor height. LOD1–3 are ~485/195/78 px. Each lower LOD uses its own accepted unreduced
round-1 mesh as reference, preserving the existing distant appearance; this is not comparison of every coarse LOD
against full LOD0. All three tiers/eight views are measured.

**Numerical SSIM does not pass .95 for LOD0–2** (minima .940053/.896411/.916842).
The agent selected them under the rule's side-by-side perceptual alternative: silhouette, ornaments, tier identity
and overall armour appearance remain intact at the intended sizes. Small local highlight/texture differences
remain under close scrutiny. This judgment is explicitly recorded, not represented as pixel equality.
LOD3 passes .972225 after rejecting a visibly wrong projected normal and retaining its accepted normal detail.

- [Side-by-side gallery and full method](review/round3/README.md), including every tier/LOD/eight-view sheet.
- LOD0 [A](review/round3/comparison_l0_a.jpg), [B](review/round3/comparison_l0_b.jpg),
  [C](review/round3/comparison_l0_c.jpg); [native-size front pair](review/round3/comparison_l0_a_0.png).
- [Reduction plot](review/round3/reduction_curve.png), [curve CSV](review/round3/reduction_curve.csv),
  [per-view IoU/SSIM](review/round3/visual_metrics.csv), [visual assessment](review/round3/visual_review.json).
- Updated clips: [front](review/clips_front.jpg), [side](review/clips_side.jpg),
  [three-quarter](review/clips_three_quarter.jpg); hands [Standing](review/round3/hands_Standing.jpg),
  [Attack](review/round3/hands_Attack.jpg), [Death](review/round3/hands_Death.jpg).
- Viewer captures [A](review/round3/viewer_a.png), [B](review/round3/viewer_b.png), [C](review/round3/viewer_c.png).

### Rebake and material tradeoff

The accepted unreduced mesh supplies component-isolated base colour, region mask, MR and tangent normal detail.
The accepted UV chart layout is retained, with new pixels projected onto it. Base is 2K; mask/MR/main normal 1K.
MR keeps the engine's red specular/green roughness/blue metallic packing. No occlusion data overwrites specular red.
The original closed helmet had no separate head set; no new head atlas or resolution reduction was introduced.

All texture sets remain shared by the three tiers, using their unchanged ramps. Base/mask/MR also remain shared
across LODs. Normal-only maps at 1K/512/256 serve lower LODs; LOD1/2 are rebaked and unchanged LOD3 uses the accepted
normal filtered/renormalized to 256. Reusing LOD0's normal on different tangent frames visibly shifted highlights.
Nine lower-LOD material clones change only normal index/name. Seven images, twelve materials total.

**Cost:** additional normal storage is 5.25 MiB RGBA8 before mips (~7 MiB with full mip chains).
The body GLB grows from 10,008,296 to **11,373,020 bytes**. This optimizes triangles, not texture memory.
No runtime GPU speed or memory benchmark is claimed. [Bake receipts and details](review/round3/README.md#texture-rebake-and-cost).

### Gates and immutable baseline findings

All eight clips/four LODs checked at 48 Hz, 576 samples per body LOD. Body/head/cloth, actual blade and
hand-furniture penetration: **0 mm**. Maximum hidden grip/cuff overlap **.359136 mm**, below 2 mm.
Both palm matrices remain exact, grip anchor <.000415 mm, motion trace flags zero.
Blow is unchanged: .71875 s, 31.451575 m/s, target dot .861332, signed edge +.654087, edge share .661776.

G4 p99/max by LOD: **1.81/3.08, 1.91/3.36, 1.74/2.36, 2.89/3.11**.
G5 maximum **2.722825 / 1.522875 / 1.310609 / 1.151729**, all below 4.5.
Two absolute findings remain exactly as accepted: Attack elbow-plane deviation **13.735° L / 26.146° R**
(8/73 L and 30/73 R samples >5°), and coarse LOD3 G4 p99 **2.89x**, above the approximate 2x guideline.
The baseline elbow report is identical. Correcting it would violate the explicit keep-clips instruction.
No new rig failure was accepted; technical-complete remains false with authorized reduction work complete.

[Gate summary](review/round3/gate_summary.json), [body](review/round3/body_gate_summary.json),
[elbows](review/round3/anatomy.json), [baseline](review/round3/anatomy_baseline.json),
[palms](review/round3/palms.json), [blade](review/round3/blade_gate.json).
[check_bindings.py](review/round3/check_bindings.txt): **no BAD line**.
[Viewer check](review/round3/viewer_check.json): **24/24**, no browser errors.
[Export audit](review/round3/export_validation.json): exact nodes/clip arrays/inverse binds/ramps, finite data,
unit normals and worst weight sum error **1.192093e-7**. Sword and actors unchanged.

### Changed files and hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `export/mm6_kni.glb` | 11,373,020 | `ffdfd4859b23676faa1193c91b778049f3d0c21308db21954fffdf17686d283c` |
| `export/mm6_kni_sword.glb` | 2,174,220 | `8bcefd5c301f63a2189408045fb2de25a16da5e994861163c52717bc8114afab` |
| `review/viewer/mm6_kni_a.glb` | 14,536,960 | `dda699159bb9f8747daf46eb310572f5435a42b2c7844bea225d88a17fd82b66` |
| `review/viewer/mm6_kni_b.glb` | 14,883,972 | `184c628987421aff98dd7829d56e30e85287d253cca3f7773beb8cd3f3701cdf` |
| `review/viewer/mm6_kni_c.glb` | 14,972,596 | `52f9194d12a9a9e4e641d5463ed53809da6e1b780f66980c630045687b3a238a` |
| `integration/actors.yml` (unchanged) | 2,383 | `b90f394ff49ae59099b9b5d9287b909a0512447acfcca93b3ac2b4f57983812a` |

[Complete artifact hashes](review/round3/files.json) cover maps, scripts, review evidence, documents and selected
Blender sources. Editable body: `work/round3/rebaked_l0.blend` through `rebaked_l3.blend`.
Accepted original masters and round-start snapshots remain preserved. New maps: `textures/round3/knight_*.png`.
[Measurement README](review/round3/README.md#reproduction-and-review-assets) lists the reproduction scripts.

Orchestrator next: review the disclosed visual/material tradeoff and immutable findings, integrate the body export,
then perform native material/contact/distance and regression checks. No assets_dev copy was made here.
Blender used one process with --threads 4; temporary HTTP server and review browser are stopped at handoff.

---

The following round-2/round-1 sections are historical. Their counts, hashes and integration instructions
are superseded by round 3 above.

## Review round 2

Only body/sword geometry, associated interpolated UVs/skin weights, LOD/shadow geometry and review assets changed.
The 58-joint skeleton, inverse binds, every original animation sample/channel/time, attachment nodes, grip frames,
blade tip, three tier materials, embedded images and region ramps are preserved. `integration/actors.yml` is
**unchanged byte-for-byte**, including the orchestrator's existing `cast: Attack` aliases. No attachment/event or
binding edits are required. The user accepted the appearance before this triangle-only round.

**Staged integration:** both `export/mm6_kni.glb` and `export/mm6_kni_sword.glb` replace their installed counterparts,
subject to orchestrator review of the unchanged strict-gate findings. The files have not been copied to assets_dev.
The round 1 instruction to replace only the sword is historical and superseded by this section.

### Triangle reduction

| Component | LOD | Before | After | Saved | Minimum IoU | Minimum SSIM |
|---|---:|---:|---:|---:|---:|---:|
| Body | 0 | 12,815 | 11,100 | 1,715 | 0.998676 | 0.980508 |
| Body | 1 | 6,467 | 5,980 | 487 | 0.997712 | 0.984377 |
| Body | 2 | 2,314 | 2,314 | 0 | 1.000000 | 1.000000 |
| Body | 3 | 754 | 697 | 57 | 0.997847 | 0.982288 |
| Sword | 0 | 2,292 | 1,985 | 307 | 0.995591 | 0.983036 |
| Sword | 1 | 1,146 | 1,131 | 15 | 0.998946 | 0.999799 |
| Sword | 2 | 457 | 451 | 6 | 1.000000 | 0.980061 |
| Sword | 3 | 180 | 180 | 0 | 1.000000 | 1.000000 |

Body shadow LODs use the same counts as their colour LODs: **11,100 / 5,980 / 2,314 / 697**. Reduced shadow
positions are tucked inward using the existing 2/4/7 mm margins, capped at 15 mm. Combined colour+prop counts are
**13,085 / 7,111 / 2,765 / 877**, versus **15,107 / 7,613 / 2,771 / 934**. No shield is present.

Eight fixed views enforce **IoU ≥.995, SSIM ≥.98** independently for body and sword. LOD0 uses 800 projected body
diagonal pixels; LOD1–3 use **550/220/88**, including runtime switch hysteresis. Every accepted LOD is compared to
its own unreduced round-1 baseline at its switch size, preserving the accepted distant look. This is not a claim
that the old coarse LODs meet those thresholds against full LOD0. Full method and limitations:
[measurement README](review/round2/README.md).

Planar dissolve plus protected collapse carries UVs/normals/weights and keeps face/head, fingers/hands, joint loops,
silhouette and prop contact regions weighted against collapse. Main 10% steps stop at visual failure, then three
bisection probes refine the interval. Body LOD0 at 10,955 triangles fails SSIM (.978180); 11,100 passes (.980508).
The sword at 1,959 fails IoU (.986066); 1,985 passes (.995591). Body LOD2 and sword LOD3 retain their original
geometry because even the smallest tested 1.25% cuts fail SSIM. No fixed half-count LOD ratios were used this round.

- [Curve plot](review/round2/reduction_curve.png), [CSV including gate status](review/round2/reduction_curve.csv),
  [body curve](review/round2/reduction_curve.json), [sword curve](review/round2/sword_reduction_curve.json),
  [selected meshes and full-precision minima](review/round2/selection.json).
- Eight-view comparisons: [body](review/round2/body_before_after.jpg), [sword](review/round2/sword_before_after.jpg).
- Updated clip sheets: [front](review/clips_front.jpg), [side](review/clips_side.jpg),
  [three-quarter](review/clips_three_quarter.jpg); eight roles, five times each.
- Updated hand sheets: [Standing](review/round2/hands_Standing.jpg), [Attack at blow](review/round2/hands_Attack.jpg),
  [Death at contact](review/round2/hands_Death.jpg). Tier captures:
  [A](review/round2/viewer_a.png), [B](review/round2/viewer_b.png), [C](review/round2/viewer_c.png).
- Round 1 accepted [weapon design](review/round1/sword_design.png) and [detailed close-up](review/round1/sword_closeup.png)
  remain the design reference; the round 2 sword comparison shows the reduced geometry.

### Gates and unchanged baseline findings

Every clip is sampled at **48 Hz**, 576 poses per body LOD. G4 p99/max by LOD: **1.86/3.24, 1.95/3.36,
1.80/2.36, 2.89/3.11×**. G5 worst by LOD: **2.722825, 1.522875, 1.310609, 1.151729×**, all below 4.5×.
Confirmed body/head/cloth penetration is **0 mm** on all four LODs. Actual blade and hand-furniture penetration
is **0 mm** on every clip at every LOD. The accepted hidden grip/cuff contact in Death is **1.717193 mm**, below 2 mm.

Both palm frame matrices equal the accepted frame on all 576 samples (zero matrix delta); grip anchor error is
**0.000415 mm** at worst. Trace flags: **0**. Posture is remeasured for all eight clips. Blade impact remains
**0.71875 s**, **31.451575 m/s**, target dot **.861332**, signed edge lead **+.654087**, edge share **.661776**.

**Strict baseline findings, not regressions or silently waived passes:**

1. Attack's anatomical plane deviation is **13.735° left / 26.146° right**, beyond the 5° audit tolerance on
   **8/73 left and 30/73 right** samples. The exact same per-clip report is produced from the unreduced baseline.
   Flexion stays forward (overall minimum .1065°) and roll stays within ±90° (maximum absolute 24.532°); all seven
   other clips pass the plane check. Fixing Attack would violate this round's explicit instruction to keep clips exact.
2. Body LOD3 G4 p99 **2.89×** is above the approximate 2× guideline. Unreduced accepted Attack also measures
   **2.89× p99 / 3.11× max**, unchanged by reduction. The coarser candidate is retained as a baseline-preserving
   reduction, with this finding recorded rather than presented as an absolute gate pass.

Body-contact diagnostics were corrected for open armour: nearest-face normals require closed-volume ray confirmation.
Cloth nearest points on actual open panel boundaries are excluded; internal panel faces remain tested. The raw
LOD1 33.704 mm report was on an exposed boundary in both meshes, not a cloth intersection. Details and retained
baseline diagnostics are linked from the measurement README.

[Gate summary](review/round2/gate_summary.json), [body](review/round2/body_gate_summary.json),
[elbows](review/round2/anatomy.json), [baseline elbows](review/round2/anatomy_baseline.json),
[palms](review/round2/palms.json), [posture](review/round2/posture.json), [blade](review/round2/blade_gate.json).
The handoff records `technical_complete: false` for the full stricter checklist and completed authorized reduction
work separately; it does not assert all gates pass.

### Files, validation and handoff boundary

| File | Bytes | SHA-256 |
|---|---:|---|
| `export/mm6_kni.glb` | 10,008,296 | `e6f495a89d406cecf72f98eac3eee2476dcf06dd32b52a49db5a625380ff5fe8` |
| `export/mm6_kni_sword.glb` | 2,174,220 | `8bcefd5c301f63a2189408045fb2de25a16da5e994861163c52717bc8114afab` |
| `review/viewer/mm6_kni_a.glb` | 10,228,104 | `4c4b00b3b2ea4278bac2f42d48ec216f8bbcebb93a7f2e00db0decf71dd38bfd` |
| `review/viewer/mm6_kni_b.glb` | 10,530,232 | `0dfc310d4ae94c3bd5288cdc441f78d844334b2d5628efb3d6b56578c87c6748` |
| `review/viewer/mm6_kni_c.glb` | 10,611,372 | `3daa2cdd94366adad172c6b79929311e8a3c2f13d53d65bbfe4226e28e36221d` |
| `integration/actors.yml` — unchanged | 2,383 | `b90f394ff49ae59099b9b5d9287b909a0512447acfcca93b3ac2b4f57983812a` |

[Export validation](review/round2/export_validation.json) proves exact original skeleton/clip/material/image data.
All eight body colour/shadow meshes have normalized weights: worst sum error **1.192093e-7**, below 1e-4.
The [binding validator](review/round2/check_bindings.txt) prints **no BAD line**. The shared
[viewer check](review/round2/viewer_check.json) passes **24/24** tier/clip switches, zero browser errors.
The weapon tip differs from its original marker by less than **1.17e-7 m**; no timing/socket adjustment is needed.

Editable selected meshes: `work/round2/selected_body_l0.blend` through `selected_body_l3.blend`, and
`selected_sword_l0.blend` through `selected_sword_l3.blend`. The original authoring masters remain unchanged.
Reproduction: `scripts/reduce_round2.py`, `refine_reduction_round2.py`, `reduce_sword_round2.py`,
`prepare_selected_round2.py`, `package_round2.py`, `verify_round2.py` and the round-2 gate/render scripts.
[Artifact hashes](review/round2/files.json) cover the exports, viewer data, current sheets, reports and project scripts.
The round-start baseline is [recorded here](review/round2/baseline.json); snapshots are under `work/round2/baseline_*`.

Integration, native material/contact/distance checks, game regression and any separate decision about accepted
baseline animation findings remain with the orchestrator. No engine build/game launch or assets_dev write occurred.
All Blender work used one process at a time with `--threads 4`; the local server and review browser are stopped.

---

## Review round 1

The user's request was a better weapon with real form and texture. The replacement follows the native curved blade
and a new standalone Codex image-generation design: bevelled cutting edge, recessed fullers on both faces, three
root teeth, a shaped guard with rivet bosses, raised spiral leather wrap, steel collars and a faceted pommel.
Meshy retexture adds steel wear, edge highlights, leather grain, normal detail and material-specific roughness.
Steel stays neutral dull grey on all tiers. The generated near-tip barb was omitted to retain the original tip
and swept silhouette; the compact guard and grip fit the existing grasp. No body or animation correction was made.

- **Design:** [review/round1/sword_design.png](review/round1/sword_design.png), also
  [references_hd/sword_round1/design.png](references_hd/sword_round1/design.png).
  [Prompt](references_hd/sword_round1/prompt.txt), [generation provenance](references_hd/sword_round1/generation.json).
- **New sword close-up:** [three-quarter](review/round1/sword_closeup.png),
  [side](review/round1/sword_side.png), [grip/guard/pommel](review/round1/sword_grip_closeup.png).
- **Updated clip sheets:** [front](review/clips_front.jpg), [side](review/clips_side.jpg),
  [three-quarter](review/clips_three_quarter.jpg), eight roles and five poses per role in each sheet.
- **Grasp review:** [Standing](review/round1/hands_Standing.jpg), [Attack at blow](review/round1/hands_Attack.jpg),
  [Death at measured cuff contact](review/round1/hands_Death.jpg).
- **Three tiers:** [A](review/round1/viewer_a.png), [B](review/round1/viewer_b.png), [C](review/round1/viewer_c.png).
  [Interactive viewer](review/viewer/index.html); serving instructions in [README.md](README.md).

### Changed files and integration

**Replace only `export/mm6_kni_sword.glb` in the orchestrator's installed model set.**
`export/mm6_kni.glb` and **`integration/actors.yml` are unchanged byte-for-byte**. All 58 joints, eight clips,
body LODs and tier colours remain unchanged. Semantic comparison also proves the three viewer bodies retain identical
geometry, weights, animations, materials and texture image bytes after removing the old sword.

| File | Change | SHA-256 |
|---|---|---|
| `export/mm6_kni_sword.glb` | New sword, 2,181,924 bytes | `1d724cff0a0d9a2b28019894494644ab961b90088181b6189ef8e85fd47aaed4` |
| `export/mm6_kni.glb` | Unchanged, 11,236,688 bytes | `bf5b02be6bcb64deb0fcdabb5fed0253df80e1051cf3dcb48498777afc08e1fa` |
| `integration/actors.yml` | Unchanged, 2,383 bytes | `b90f394ff49ae59099b9b5d9287b909a0512447acfcca93b3ac2b4f57983812a` |
| `references_hd/sword_round1/design.png` | New standalone design | `2b56b5f8ac7c00b625e41188fd4457833851e1e1c0061b35b2a90ee89a6d798f` |
| `review/round1/sword_closeup.png` | New final close-up | `45a712a934ff5d859869fd8709fa22ddd4b4328d9db7abd1e3ef5d873348c423` |

Sword LOD0–3 triangles: **2,292 / 1,146 / 457 / 180**, replacing **390 / 122 / 44 / 4**.
Body colour/shadow LODs remain **12,815 / 6,467 / 2,314 / 754**. The sword has one material, three shared 1K maps
(base colour, normal, MR with red specular mask), and `kni_a/b/c` variants selecting the same neutral steel/leather.
Final glTF LOD3 drops two degenerate triangles from Blender's 182-triangle source.

Editable sword source: `work/round1/sword_textured.blend`; maps: `textures/sword_round1/`;
geometry: `scripts/build_sword_round1.py`; export assembly: `scripts/package_sword_round1.py`.
Updated review models: `review/viewer/mm6_kni_a.glb`, `_b.glb`, `_c.glb`, and `manifest.json`.
[Full artifact hash inventory](review/round1/files.json) covers textures, review models, sheets and authoring source.
The original `work/runtime_master.blend` remains preserved and contains the previous sword;
use the new sword master with the unchanged exported body for this revision.

Bindings remain: `Sword` attachment, `SwordTip` launch, impact **0.71875 s**, stride **1.35 m**,
A scale **106.671451**, B/C scale reference **KnightPlate A**, yaw **−1.570796327**; IDs **565/566/567**.
[integration/actors.yml](integration/actors.yml) requires no merge changes for this round.

### Final gates

| Gate | Result | Evidence under `review/round1/` |
|---|---|---|
| G4 | 364 poses, all eight clips; arm p99 ≤1.82×, maximum edge 3.94× | `g4_round1.json` |
| G5 | Both hands, all eight clips; maximum 2.722341× <4.5× | `g5_final.json` |
| G6 body | All eight clips; no reported scoped body/head/fauld contacts | `g6_contacts.json`, `g6_fauld.json`, `final_gate_log.txt` |
| G6 actual blade | Eight clips at 48 Hz; **0** blade penetration | `g6_blade_only.json` |
| G6 hand/weapon | **0** blade/guard/pommel penetration into gripping hand; grip/cuff **1.717 mm <2 mm** in Death | `g6_hand_furniture.json`, `g6_sword.json` |
| G6 motion | Eight clips at 48 Hz; **0** source-relative trace flags | `g6_trace.json` |
| Blade/blow | 0.71875 s, 31.4516 m/s; target dot 0.86133, signed edge +0.65409, share 0.66178 | `blade_gate.json` |
| Posture | Every clip sampled; live trunk lean max 19.244°; Death/Dead lie down | `posture.json` |
| Export | Finite attributes, unit normals, four LODs, three variants; body/binding invariance | `export_validation.json` |
| UV/texture | 0 collapsed faces, 0 overlap texels at 1K; Meshy UVs identical per corner; normal +Y-up correlation +0.97275 | `uv_gate.json`, `texture_validation.json`, `export_validation.json` |
| Viewer | Shared checker ready, **24/24** tier/clip switches, no console errors or failures | `viewer_check.json` |

The actual new blade tip matches the original `SwordTip` position within **1.17e−7 m**. Grip centre, axes and
blade roll remain unchanged. MR red is preserved exactly, metallic factor remains zero for the engine specular path.
The agent inspected the final sword renders, all tier viewer captures, all three clip sheets and hand close-ups.
[Gate summary](review/round1/gate_summary.json) collects the final evidence. Earlier sword reports are historical.

### Costs, limits and next action

Round 1 Meshy task `01a12efb-473d-7222-8b0e-a34d8cab8a91`: retexture, 10 credits.
Original topology/rig/body texture: 5 + 5 + 10. Total **30**, remaining **70**; no paid animations.
Requests and receipts are in `creature_3d_progress.json` and `requests/sword_retexture_round1.json`.

No failing technical gates remain. The hidden grip/cuff overlap is below the playbook's 2 mm limit; it is recorded
rather than changing the accepted rig. Contact tests cover the stated sampled regions, not arbitrary procedural
head offsets. The accepted body's original dark-palette ambiguity remains unchanged.

The orchestrator already installed the previous export. It should now replace only the sword, inspect native
materials, attack/grasp clearance and distance LOD silhouettes, and obtain weapon artistic acceptance.
[integration/regression.md](integration/regression.md) and [playbook notes](integration/playbook_notes.md) retain the
integration context. No game, build, runtime copy or commit was performed; the workspace lease is released at handoff.

### Initial handoff history

The superseded sword was 71,404 bytes with SHA-256
`c20f2559f51b9a3117c94da04db18b7554b8c8072f553c62a5a0e70f2c8d8d07`.
[Original handoff](review/round1/initial_HANDOFF.md) and [original README](review/round1/initial_README.md) are historical
snapshots; the old sword and viewer GLBs are retained under `work/round1/` for the invariance audit.
