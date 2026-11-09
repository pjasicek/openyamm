# MM6 Jackalman / jak1 — review handoff

Round 4 staff reduction is ready. Accepted body unchanged; checks pass. **40/100 credits spent.**

## Review round 4 (staff reduction)

The user accepted the entire Jackalman on 2026-10-13. **Only the staff changes.** Its LOD0 falls from
2,018 to **866 triangles (57.09% fewer)**; lower LODs are **472 / 214 / 86**, strictly decreasing.
Body geometry, all body LODs, skin/cloth colours, rig, animation clips, timings and actor bindings are preserved.
The delivered body GLB and packed body master are byte-identical to round 3.

[Staff close-ups](review/round4/staff_closeup.png) · [staff at melee size](review/round4/staff_ingame.png) ·
[700-pixel full actor](review/round4/lod0_comparison.png) · [current viewer](review/viewer/index.html).
Comparisons use identical cameras and lighting. They are offline renders, not native game captures.

### Fixed target and visual comparison

| LOD | Actor height px | Staff triangles | Fraction of new LOD0 | Pooled actor IoU, 8 views | Minimum bbox SSIM |
|---|---:|---:|---:|---:|---:|
| 0 | 700 | 2018 → **866** | 100.00% | 0.997633 | 0.988748 |
| 1 | 550 | 1108 → **472** | 54.50% | 0.995854 | 0.984981 |
| 2 | 220 | 503 → **214** | 24.71% | 0.985602 | 0.959147 |
| 3 | 88 | 472 → **86** | 9.93% | 0.980745 | 0.978394 |

One fixed topology target, without a target search. The 250-triangle accepted hook topology is retained at LOD0;
a ten-sided shaft replaces nested cylinders and raised wraps. Bands, incisions and wraps are baked from the
accepted staff into base colour, material response and OpenGL tangent normals. Neck and grip surfaces were
fitted without adding triangles. Both hand animations, attachment node, grip origin and **StaffTip** stay fixed.

LOD0 minimum eight-view full-actor IoU is **0.996664**. Lower LODs pass the
0.97 pooled threshold at their switch sizes, compared with the previously accepted matching LOD.
These scores include the unchanged body. Staff-only silhouette IoU at 700-pixel actor scale is **0.9390 front /
0.9662 quarter**: baking the raised wraps removes small edge bumps. Close-ups expose those differences;
the agent's in-game-size comparison finds the hook, pole, bands and grip appearance retained.
[Full numeric receipt](review/round4/visual_metrics.json), [550px](review/round4/lod1_comparison.png),
[220px](review/round4/lod2_comparison.png), [88px](review/round4/lod3_comparison.png).
The accepted body's historical round-2 LOD3 limitation is outside this staff-only revision.

All staff LODs and tiers share **one 1024×1024 three-map set** in `textures/round4_staff/`.
There are 26 UV islands, **20.48px border padding**, and no overlap between their 16px dilations.
Average surface texel density is **655.6 texels/m**, versus
601.9 before. Source maps were 576×1024; the square atlas provides the
required gutters. [Texture audit](review/round4/texture_audit.json). Staff GLB size is 903,352 bytes,
versus 1,392,640 before. Skin, gold, cloth and all body maps remain unchanged.

### Files and hashes

| File | Status | SHA-256 |
|---|---|---|
| `export/mm6_jak1_staff.glb` | changed/new | `ce5cfcd2cc10c6ee3c3c989dbebe5ba635b8213c6fc121ce58c1eeb5b54e83cd` |
| `export/mm6_jak1.glb` | byte-identical | `b69d880fdcd362d19330371d8ad931416fc94cbac7303249449bb5edbba5aa83` |
| `source/mm6_jak1_staff.blend` | changed/new | `2ed1f3e6fc4d9cd04976722d32e3d7a607029603d409780dbfa784e7d8d4c121` |
| `integration/actors.yml` | byte-identical | `03e633e977a5b5810fdcb97ba6525c6f31e440d050d66d7c9b4e91051d1352df` |

Body colour/shadow triangles remain **7480 / 4113 / 1816 / 595**. Combined review counts become
**8346 / 4585 / 2030 / 681**. The updated `export/mm6_jak1_combined.glb`, `mm6_jak1_lods.glb`,
`mm6_jak1_runtime_lod0.glb`, and three viewer GLBs carry only the new staff; original body attributes,
nodes, skin and animation data are retained. [All file hashes](review/round4/files.json) ·
[body/socket invariance](review/round4/invariance.json).

**`integration/actors.yml` did not change.** The new editable staff is `source/mm6_jak1_staff.blend`.
The accepted `source/mm6_jak1.blend` is deliberately unchanged and still embeds its historical staff preview.
Use the separate staff source and current combined GLBs for this revision.

### Final checks

- Mandatory shared runner at **48 Hz**: **6,602 PASS, 0 FAIL, 0 UNVERIFIED** (128 INFO, 56 N/A),
  covering G4–G6, elbow/twist, palms, contact, posture, feet and smoothness across all clips/LODs.
  Worst grip gap **2.851 mm**, penetration **2.551 mm**.
  [Final report](review/round4/shared_gates/gates.md).
- Grip surface selectors now cover the full pole, because the long reduced triangles cross the old narrow
  selector bounds. Contact tolerance remains **3 mm**. LOD3 ratio limit tightened from 24% to 10%.
  Intermediate fitting failures are superseded by the hash-bound final report.
- `check_bindings.py` and `check_weights.py`: **no BAD line**, worst weight error **0.000000**.
  [Bindings](review/round4/check_bindings.txt) · [weights](review/round4/check_weights.txt).
- Split/export equivalence passes. Browser viewer **24/24**, normal/quarter-speed playback **16/16**, no errors.
  [Export receipt](review/round4/export_validation.json) · [viewer](review/round4/viewer_check.json) ·
  [playback](review/round4/playback_check.json).
- Refreshed and inspected staff comparisons, tier viewer, and clip sheets:
  [front](review/round4/clips_front.jpg), [side](review/round4/clips_left.jpg),
  [three-quarter](review/round4/clips_three_quarter.jpg).

**Orchestrator next step:** install only `export/mm6_jak1_staff.glb` with
`python3 tools/install_model.py level_generation/creatures/mm6_jak1_codex/export/mm6_jak1_staff.glb --world mm6`.
Keep the accepted body and actor entries. Native lighting/integration review remains with the orchestrator.
No game launches, builds, installs or commits were performed. One background Blender process at a time,
four threads. Additional credits **0**, total **40/100**. Lease and own viewer processes released at handoff.

## Review round 3 (skin tone)

The user accepted the mesh and animations and requested dark skin again, slightly lighter than round 1.
This round changes **only the second, skin colour ramp** to a monotone 16-stop curve. The pooled exposed-skin
mean and 95th-percentile highlight are **30.0000%** of the way from round 1 toward round 2. The current user
instruction supersedes the earlier native-brightness target. No geometry, rig, clip, timing, LOD or prop edits.

[Three-way tier-A front comparison](review/round3/skin_comparison.png) ·
[interactive comparison](review/round3/viewer/index.html) · [current tier viewer](review/viewer/index.html).
The first comparison panel is the actual historical round-1 body export (staff omitted); the last two panels
use the same accepted mesh and staff. All use Standing at 0 seconds, the same front camera and unchanged viewer
lights, ACES tone mapping and exposure 1.15. Geometry differences in the historical panel are not round-3 edits.

### Skin luminance per tier

Linear Rec.709 luminance encoded to sRGB on 0–255, measured over **443,139 valid exposed-skin source-UV texels**
from body and head together; unused UV pixels, cloth, gold and eyes excluded. Each cell is **mean / p95**.
These are albedo values, not lit screenshot values. Tiers intentionally share the same skin ramp and sample set.

| Tier | Round 1 | Round 2 | Round 3 |
|---|---:|---:|---:|
| A — blue | 43.68 / 62.86 | 75.34 / 188.00 | **53.18 / 100.40** |
| B — purple | 43.68 / 62.86 | 75.34 / 188.00 | **53.18 / 100.40** |
| C — red | 43.68 / 62.86 | 75.34 / 188.00 | **53.18 / 100.40** |

[Full numeric receipt](review/round3/skin_luminance.json) includes body/head breakdowns, exact ramp values and
binary parity hashes. The smooth, strictly increasing transfer retains shading order and muscle highlights.
The first cloth ramp, all masks and every embedded base/normal/ORM texture are unchanged. All six tier/material
previews retain every unmasked non-skin pixel exactly: [pixel parity](review/round3/preview_parity.json).

### Changed files, hashes and unchanged triangle counts

| File | Round-3 status | SHA-256 | Colour LOD triangles |
|---|---|---|---|
| `export/mm6_jak1.glb` | changed | `b69d880fdcd362d19330371d8ad931416fc94cbac7303249449bb5edbba5aa83` | 7480 / 4113 / 1816 / 595 |
| `export/mm6_jak1_combined.glb` | changed | `ad93a66feeb5329fb71422b620920a157eaf2469c4f3492b0a2b900fad3ca228` | 9498 / 5221 / 2319 / 1067 |
| `export/mm6_jak1_body_unmerged.glb` | changed | `31e33365419a91d1aa85dff3e1bc37548959500d3ec77d398723f27efc900e14` | 7480 / 4113 / 1816 / 595 |
| `textures/jak1_ramps.json` | changed | `3ee67015fd0870ac34dda2ea39a87b4e8eadfdb9e34acf353480024cb7278766` | — |
| `textures/jak1_ramps_runtime.json` | changed | `29c86dfb8d49e225454a3b86004c99f79bb4f46ccfc7a4f6a6ded4d6eac1d0cd` | — |
| `export/mm6_jak1_staff.glb` | byte-identical | `9bea79e7a7cb7087676e3a6daefcf2729bd1e1d873473512fbe3e2e6db47512f` | 2018 / 1108 / 503 / 472 |
| `integration/actors.yml` | byte-identical | `03e633e977a5b5810fdcb97ba6525c6f31e440d050d66d7c9b4e91051d1352df` | — |
| `source/mm6_jak1.blend` | byte-identical | `58075768ad99453a0fcb8ef7141a7eaf8b93f46e94efeb1586f0489496e89ad4` | — |

The three changed GLBs retain their **entire binary chunks byte-for-byte**. Every JSON field outside the skin
ramp is identical too, including all geometry, animation, rig, LOD, socket and material/texture references.
**`integration/actors.yml` did not change.** Staff and packed editable master are byte-identical. The master and
canonical unpaletted exports retain their existing intensity-carrier textures; final colour comes from the
external runtime ramp configuration. Review GLBs bake that same ramp for three.js, which has no region shader.

### Validation and review

- Re-ran all shared G4–G6, elbow/twist, palm, grip/contact, posture, feet and smoothness gates at **48 Hz**:
  **6,602 PASS, 0 FAIL, 0 UNVERIFIED** (128 INFO, 56 N/A). [Report](review/round3/shared_gates/gates.md).
- Re-ran the actual outer-panel cloth gate on all four colour LODs and eight clips: **32/32 pass**, worst
  crossing **0.628489 mm**. [Receipt](review/round3/outer_panel_gate.json).
- `check_weights.py` and `check_bindings.py`: **no BAD line**, worst weight-sum error **0.000000**.
  [Weights](review/round3/check_weights.txt) · [bindings](review/round3/check_bindings.txt).
- Export split/animation equivalence passes. Viewer **24/24**, normal/quarter-speed playback **16/16**, no
  browser errors. [Export](review/round3/export_validation.json) · [viewer](review/round3/viewer_check.json) ·
  [playback](review/round3/playback_check.json).
- Refreshed and inspected the browser skin comparison and front/side/three-quarter clip sheets.
  [Front](review/round3/clips_front.jpg) · [side](review/round3/clips_left.jpg) ·
  [three-quarter](review/round3/clips_three_quarter.jpg). Muscle highlights remain legible with darker charcoal skin.

The prior round-2 LOD3 full-detail IoU limitation remains recorded below. It was not altered or retested visually:
the user accepted the mesh and explicitly required this round to leave all LOD geometry unchanged. New skin
artistic acceptance and native lighting verification remain with the user/orchestrator.

**Orchestrator next step:** install only `export/mm6_jak1.glb` through
`python3 tools/install_model.py level_generation/creatures/mm6_jak1_codex/export/mm6_jak1.glb --world mm6`.
The source/runtime installation tool owns the asset copies. Keep the already installed staff and actor entries.
Then review the darkened skin under native lighting. This session did not install assets, launch games, build or
commit. Blender ran one background process at a time with four threads. Additional credits **0**, total **40/100**.
The workspace lease, comparison HTTP server and session Chrome processes are released/closed at handoff.

## Review round 2

- Corrected hand rest roll and retargeting: staff-side palm faces the body, thumb points up the shaft;
  the free hand faces the thigh with relaxed curled fingers. Anatomical elbows and distributed twist replace the
  Fidget candy-wrapper. Palm directions are checked on every clip.
- Planted actual heel/toe surfaces through ankle/leg IK. Standing and Fidget retain their body motion; the floor
  correction is in the legs. Walking has visible 8.5–8.6 cm foot clearance and about 59° knee flexion.
- Replaced procedural Attack, Cast and Death with local **StaffAttack2**, **StaffCastLAttack1** and **StaffDeath1**.
  Attack uses two fixed shaft grips, a step, weight transfer and follow-through. Cast steps and thrusts the staff
  toward the target while the free hand gestures. Death uses the library fall with a released, grounded staff.
  A periodic elbow path also removes the Walking loop seam jerk. See [animation study](ANIMATION_STUDY.md).
- Matched the skin luminance distribution to native frames, with a documented 1.30 linear albedo gain for lighting.
  Blue/purple/red cloth, gold and the shared dull-grey staff retain their tier roles.
- Reduced and rebaked LOD0, including OpenGL tangent normals, and fitted lower LODs. Additional lower-LOD palm
  geometry and contact corrections keep the staff grip valid throughout the new clips.
- **`integration/actors.yml` changed for all three tiers:** new impact, Cast launch, stride and scale values below.
  Ranged still aliases **Attack**, with no launch socket; the table spell has its distinct **Cast** clip.

### Files and hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `export/mm6_jak1.glb` | 10,258,464 | `b91917e268cf91b2b14a82084b34bbb68c2e68309bd65b54d012c058423b1acf` |
| `export/mm6_jak1_staff.glb` | 1,392,640 | `9bea79e7a7cb7087676e3a6daefcf2729bd1e1d873473512fbe3e2e6db47512f` |
| `source/mm6_jak1.blend` | 12,787,654 | `58075768ad99453a0fcb8ef7141a7eaf8b93f46e94efeb1586f0489496e89ad4` |
| `integration/actors.yml` | 2,341 | `03e633e977a5b5810fdcb97ba6525c6f31e440d050d66d7c9b4e91051d1352df` |
| `review/viewer/manifest.json` | 16,460 | `4dc1372595d05d765629480b8da05aa5496efcf78786b4253ff12c412bba88dd` |

| Colour LOD | Body | Staff | Combined | Fraction of combined LOD0 |
|---|---:|---:|---:|---:|
| 0 | 7,480 | 2,018 | 9,498 | 100.00% |
| 1 | 4,113 | 1,108 | 5,221 | 54.97% |
| 2 | 1,816 | 503 | 2,319 | 24.42% |
| 3 | 595 | 472 | 1,067 | 11.23% |

Body shadow counts match each colour LOD. All chains strictly decrease and stay below the previously installed counts.
The thin staff retains 472 triangles at LOD3 (23.39% of its LOD0); the combined actor is 11.23%, approximately the 10%
LOD3 guidance. One texture set is shared across all LODs and tiers. Rebake dilation is 16 pixels at 1024² per source
material; the merged body/head runtime atlases are 2080×1024. Staff has no colour-region extras. All shadow materials
are OPAQUE; unsupported glTF material extensions and non-normalized skin weights are absent.

### Integration values

The orchestrator replaces both runtime GLBs and merges [the exact actor blocks](integration/actors.yml).
Descriptors **Jackalman A/B/C**, merged monster ids **562/563/564**, skins **jak1_a/b/c**.
Scale **109.233628**, yaw **−1.570796327**, stride **1.253289580 m**.
Melee and unused ranged alias impact: **0.989583333 s**.
Psychic Shock Cast launch: **0.927083333 s**, socket **StaffTip**. Staff attachment node: **Staff**.
`run: Walking`; `cast: Cast` is distinct from both attack roles. Proposed native checks are in
[integration/regression.md](integration/regression.md). This session did not copy anything to `assets_dev`.

### Validation

Shared final-runtime audit: **6,602 PASS, 0 FAIL, 0 UNVERIFIED**, every mesh and clip at 48 Hz.
The project wrapper raises the shared runner's adaptive 24 Hz base to 48 Hz. The split wrap uses the separate
outer-panel test described below; it is not claimed as a closed-volume garment pass.

| Check | Worst result |
|---|---|
| G4 arm stretch p99 / G5 hand edge stretch | 1.784943× / 3.655922× |
| Arm/body contact | 0.000 mm |
| Staff/body contact, all LODs | 1.377 mm; dense LOD0 surface check 1.210 mm |
| Actual outer wrap panel crossing | 0.628 mm, all LODs and clips |
| Head contact | 6.122 mm, within the playbook's 10 mm limit |
| Palm/digit-to-shaft gap / hand/shaft penetration | 2.995548 / 2.897406 mm |
| Fixed off-hand frame during the swing | 0° relative rotation; <0.049 mm off-axis |
| Rest heel/toe height, all LODs | 4.880 mm; full LOD0 sole tilt ≤2.224° |
| Walking foot lift / knee flexion | 85.56–86.00 mm / 59.14–59.81° on LOD0 |
| Elbow plane error / hyperextension | ≤0.055817° / none |
| Main/helper arm twist | Upper arm ≤58.345°; forearm ≤60.001°; helper cap 85° |
| Angular acceleration within clips | 16933.55°/s², below 20,000 |
| Across looping clip seams | 7085.40°/s², below 20,000 |
| Attack tip speed / signed edge lead | 9.087852 m/s / 0.836175 |
| Death → Dead | <0.001 mm joint difference, 0° rotation difference |
| Final weights/materials and bindings | `check_weights.py` and `check_bindings.py`: no BAD line |
| Viewer / normal and quarter-speed playback | 24/24 combinations / 16/16 samples; zero console errors |

Gate calibration is explicit in [gates.json](gates.json). The shared palm cone is 65° (measured 61.902°) because its
wrist/knuckle-centre axis differs from the direct palm-to-shaft normal; the direct gate requires dot >0.8 and passes.
The native resting stance permits toe-out; Standing/Fidget use 36°. Walking uses 12° for coarse sole-patch estimates
(worst 11.418°), while the LOD0 bone-axis audit stays within 5.003°. LOD3 reaches −0.845 mm during Walking, within
2 mm floor tolerance. These are reported values, not claims of exact zero or a strict 10° mesh-patch yaw.

The wrap is split, overlapping and has a non-planar hem. Artificially capping it produced false Death crossings;
that rejected attempt is retained in [shared_volume_probe](review/round2/shared_volume_probe/).
[The replacement gate](scripts/final_panel_gate.py) requires an actual inward ray crossing of an outward fabric panel,
checks initially covered skin, and respects overlapping coverage and exits around the real hem. It checks nonempty
regions on all four colour LODs at 48 Hz; shadow geometry is identical. A 1.5 mm LOD2 skin correction reduced the actual
maximum crossing to 0.628 mm. No shared tool was edited.

### Reduction curve and remaining limit

LOD0 comparison: actor height 700 px, all three actual tier materials, eight views. Minimum IoU ≥0.99 and SSIM ≥0.95.
The next smaller step fails SSIM, so step 3 was retained and passed the full rig audit.

| Step | Combined triangles | Minimum IoU | Minimum SSIM | Result |
|---|---:|---:|---:|---|
| 1 | 11,725 | 0.998869 | 0.989104 | Visual pass |
| 2 | 10,552 | 0.997717 | 0.976018 | Visual pass |
| 3 | 9,498 | 0.996401 | 0.963067 | Selected; rig gates pass |
| 4 | 8,547 | 0.993852 | 0.947590 | Rejected: SSIM |

[Curve](review/round2/reduction/curve.png) · [blue side-by-side](review/round2/reduction/comparison_a.jpg) ·
[purple](review/round2/reduction/comparison_b.jpg) · [red](review/round2/reduction/comparison_c.jpg).
The 24 original full-resolution comparisons and rejected reduction trials remain in the same directory.

LOD1 at 550 px: pooled IoU **0.992997** against LOD0.
LOD2 at 220 px: **0.971264** against LOD0.
**LOD3 silhouette IoU against LOD0 is 0.932402, below 0.97. It passes only against the corrected incoming LOD3 (0.976920); the strict full-detail comparison remains open under the old 600-body-triangle cap.** The incoming-LOD convention follows the Knight reference, but it does not prove the stricter
full-detail criterion. More LOD3 silhouette fitting is required before claiming every batch done criterion is met.
No threshold was lowered to turn this image comparison into a pass.

### Skin comparison

sRGB luminance on 0–255; each cell is mean / 95th percentile. Native samples use four front Standing/Walking frames,
achromatic exposed-skin regions, alpha rejection and exclusion of near-black silhouette pixels. Gold/cloth are excluded.

| Region | Previous texture | Native pixels | Revised albedo |
|---|---:|---:|---:|
| body | 48.54 / 83.97 | 69.69 / 185.21 | 79.36 / 208.23 |
| head | 36.41 / 52.23 | 61.07 / 149.00 | 69.67 / 167.83 |

The UV skin distribution is matched before the 1.30 linear gain; the final albedo is intentionally slightly brighter
than the native image. This is a texture-space comparison, not a claim that every lit game pixel has the same value.
Source skin mottling and highlight contrast, plus the busy collar ornament, remain visible artistic-review items.
[Numeric receipt](textures/skin_luminance.json).

### Review and ownership

[Viewer](review/viewer/index.html) · [corrections sheet](review/round2/corrections.jpg) ·
[front clips](review/clips_front.jpg) · [side clips](review/clips_left.jpg) ·
[three-quarter clips](review/clips_three_quarter.jpg) · [blue browser view](review/viewer_a.png) ·
[purple](review/viewer_b.png) · [red](review/viewer_c.png).
Hands, floor, Fidget shoulder, two-handed impact and Death hem have individual closeups under `review/round2/`.
The staff [design](review/staff_design.png), [hook](review/staff_hook.png) and [grip](review/staff_grip.png) remain available.

Machine-readable evidence: [round-2 receipt](review/round2/validation.json),
[all-LOD gates](review/round2/shared_gates/gates.md), [panel gate](review/round2/outer_panel_gate.json),
[loop seam audit](review/round2/loop_acceleration.json), [export audit](review/export_validation.json),
[bindings check](review/bindings_check.txt), [viewer check](review/viewer_check.json).

Workspace lease is released at handoff. Writes stayed in this project plus the ownership ledger. The sprite-restore
project and shared/runtime files remained read-only. Blender ran one process at a time with `--threads 4`.
This session's browser and HTTP server are closed at handoff. Native game checks remain the orchestrator's work.

## Review round 1

The orchestrator found two installation failures: empty staff colour ramps and Cast reused as the ranged attack.
Both are corrected in the project exports. No user artistic review was supplied.

- Removed the non-recolouring staff from `textures/jak1_ramps.json` and its generator, `scripts/compose_textures.py`.
  All three staff skin slots now share the native-colour material with neither `openyamm_region_mask` nor
  `openyamm_region_ramps`; the unused mask is absent from the exported GLB. Its geometry, UVs, normals and three
  texture maps are unchanged. The body export and editable master are byte-for-byte unchanged.
- **`integration/actors.yml` changed for all three tiers.** `clips.attack_ranged: Attack` and
  `animation.events.attack_ranged: {impact: 0.677083333}` have no launch socket. `animation.cast: Cast` remains
  distinct from both attack roles, with its 0.733333333 impact and StaffTip socket. The package generator preserves
  these bindings. `scripts/verify_exports.py` now checks both contracts and runs the updated shared loader-rule check.

| File | SHA-256 | Colour LOD triangles |
|---|---|---|
| `export/mm6_jak1.glb` | `9a1fc4620fd61684bf6dd3b1b0c602fe20cd1d7745cec8ab70be5eb8554abd7b` | 10105 / 5052 / 1816 / 600 |
| `export/mm6_jak1_staff.glb` | `9bf1a3d94dbbeeded785f9556270dd1464ee304766e93c5740ae7adc7cdfbd0c` | 2924 / 1462 / 526 / 526 |
| `integration/actors.yml` | `294fb50fc85593381bb3df5a95437985fdfb7ff4b50422d744730b8cce5c872e` | — |

`check_weights.py` reports **no BAD lines** and weight error **0.000000** for both final GLBs. G4/G5/G6, posture,
anatomical elbows, soles, grip/floor, hook edge/blow and motion trace were rerun and pass. The viewer passes
**24/24** combinations; normal/quarter-speed playback passes **16/16**. Front, side and three-quarter clip sheets,
LOD renders and browser captures were refreshed and reviewed. Counts remain 10,105 body + 2,924 staff triangles at LOD0.

Evidence: [round-1 receipt](review/round1/validation.json), [validator output](review/round1/weights_check.txt),
[export checks](review/export_validation.json), [viewer checks](review/viewer_check.json),
[front sheet](review/clips_front.jpg), [side sheet](review/clips_left.jpg),
[three-quarter sheet](review/clips_three_quarter.jpg). The original rejected exports are retained in `review/round1/`.

**Orchestrator next step:** replace the installed staff with this revision and restore the corrected descriptor
entries, then repeat native registry/integration checks. This session did not modify `assets_dev`, launch the game,
build or commit. Additional credits: **0**; project total: **40/100**. Artistic acceptance and native verification
remain pending with the orchestrator/user.
