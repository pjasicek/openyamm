# MM6 Merchant mer1 — handoff

## Review round 3

**QA HOLD — revised exports and review evidence staged; technical completion remains false.**
The face/hands and apparent shoulder flaps are repaired. Every shared arm/hand stretch row and sleeve-cuff
containment row passes across the eight clips and all four colour/shadow LODs.
The full shared result is **10354 PASS / 110 FAIL /
0 UNVERIFIED**, plus 140 INFO and 80 N/A.
Rows include repeated colour/shadow evidence; they are not distinct defects. Remaining contact/motion and reduction
findings below prevent an all-gates-passing handoff. No artistic acceptance is recorded.

### What changed

- **Geometry:** LOD0 preserves **4,946 head** and **3,010 hand** triangles. Only the clothing/body was reduced
  and rebaked to **6,998 triangles**, for **14,954 total**. Fingers retain the source segments and volume.
  The higher near count follows the user's explicit round-3 body-only reduction instruction; far levels still
  stay below their previous counts. A small accidental five-edge hole above the right eye was filled with three
  triangles, using adjacent head UVs; eye rims sit behind the eyelids. No shoulder patches or detached sleeve roots.
- **Separate skin sets:** fresh Meshy head retexture from the retained HD head views, and a hand-only retexture
  with clean skin, crease/nail detail and no clothing colour. Head PBR maps are **1024²**, hand PBR maps **512²**,
  clothing maps **2048²**. They remain separate materials and share the same images across every LOD.
  No face or hand projection through the clothing rebake. UV carry-over errors are recorded in
  [uv_transfer.json](review/round3/uv_transfer.json).
- **Skin grading:** linear exposure and gentle chroma matching replaced the rank-based native-luminance remap
  that amplified pores into blotches. Head exposure is 1.30, hand exposure 1.92. Covered skin texels meet native
  mean/p90/p95 floors; face and hands use the same fair skin family. The hand comparison isolates the exported
  hand/cuff only, because the relaxed palm faces the thigh and is occluded from that camera in the complete model.
- **Shoulders/waist:** fresh bone-heat garment weights use anatomically fitted temporary bone tails, then smooth
  four-influence shoulder fitting against 81 samples of the retained library motions. The original source-frame
  rig and action choices remain. A lower-LOD shoulder fit clears the last reduced stretch failure.
  The apparently detached green ovals in the PBR previews were traced to exaggerated baked tangent normals:
  the same exported vertex poses rendered continuously without that map. The final shared clothing normal map
  keeps subtle detail with 0.15 XY strength and a positive unit Z component. No extra rebake or geometry wedge.
- **Cloth/boots:** tucked pelvis-weighted waist, matched cuff openings and preserved closed geometry. Covered
  trouser shafts were tapered within the robe, retaining all faces and the visible boots. Far sole patches
  were refitted to the unchanged planted Standing pose. These changes reduce some contact faults but do not
  certify the remaining robe/club/hand interaction.
- **Preserved:** the accepted club GLB is byte-identical, the **Club** node/belt loop and Attack draw remain,
  and Running remains **Jogging** (0.8 s, 1.302 m stride), never RelaxRunForward. All eight library-derived roles,
  Cast alias, scale, impact timing and source-frame rig are retained. No new animation purchase.

### Review and checks

- [Face before/after](review/round3/face_before_after.jpg): front, side, three-quarter.
- [Hand before/after](review/round3/hand_before_after.jpg): isolated exported palm/back, identical pose.
- [Shoulders in Standing, Attack and Death](review/round3/shoulder_closeups.jpg),
  [body turnaround](review/round3/body_turnaround.jpg), [all clip sheets](review/round3/).
- [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_mer1_codex/review/viewer/index.html):
  **24/24 tier/clip switches**, no console errors or failed switches; browser closed by the shared checker.
- [check_bindings.py output](review/bindings_check.txt): **no BAD line**. Final skin-weight sum error is
  **1.1920928955078125e-7**; material extension/opaque-shadow checks and the static geometry/weight identity pass.
- [Shared gates](review/gates/gates.md), [exact open findings](review/round3/open_findings.json).
  Stretch and cuff containment pass on every clip/LOD. The runner has no dedicated shoulder-volume or hem-vertex
  acceleration test; these are not claimed as independently certified. Existing Death cloth rotation-step checks
  pass, with worst **36.108814 degrees/sample**.

Skin values below are native / final linear luminance on covered UV skin texels, excluding padding:

| Region | Mean | P90 | P95 |
|---|---:|---:|---:|
| face | 0.361210 / 0.514023 | 0.582562 / 0.613936 | 0.603574 / 0.623468 |
| hands | 0.444972 / 0.603372 | 0.723013 / 0.724793 | 0.723013 / 0.746915 |

### Files, hashes and triangles

| File | Bytes | SHA-256 |
|---|---:|---|
| [export/mm6_mer1.glb](export/mm6_mer1.glb) | 10797284 | `cc687d18d9d7b66bac95eeb251be23644e364a28b0edad35f2d4b77003027a58` |
| [export/mm6_mer1_club.glb](export/mm6_mer1_club.glb) | 5751320 | `90d8d0ca129dbb046aeaf2d1eceae8ff0921e4cbc77208fe0752fe792d612b26` |
| [export/mm6_mer1.blend](export/mm6_mer1.blend) | 21764501 | `a666abd7d076ca6c17f19209cc6980486522a420f8c87ad17a2c3f15f105a87d` |
| [export/mm6_mer1_portable_a.glb](export/mm6_mer1_portable_a.glb) | 10711988 | `85cd3a006994f84fdd35617a2a75d8e21f3ce00057afca00cc038c15d1d6ee87` |
| [export/mm6_mer1_portable_b.glb](export/mm6_mer1_portable_b.glb) | 10675184 | `505d08248c93275c0090fc94c3e54a768c8bedfaeef5ac2d4a4ca9332ae7c484` |
| [export/mm6_mer1_portable_c.glb](export/mm6_mer1_portable_c.glb) | 10416412 | `94c7cf5ddefbe50d204fdb046565517b190928be6b6a0c9b2190ac4dc55e4805` |

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body including protected head/hands | 14954 | 2399 | 1727 | 682 |
| Unchanged club | 1122 | 290 | 252 | 200 |

All LODs share the three body material sets. The sole clothing rebake keeps >=16 px dilated margins
(34.816 px packing gap); the independent hand atlas has a 33+ px gap. Head UVs are retained from the dedicated
head set and background is dilated. [Texture resource receipt](review/round3/shared_textures.json).

### Reduction evidence and remaining findings

The explicit round-3 density requirement supersedes the old total-body ~7k count. The clothing-only reduction
is one rebake; head/hands bypass that bake. Far counts are below 2400 / 1730 / 685.
Actual tier materials were compared in eight views per tier at 700 / 550 / 220 / 88 px actor heights:

| LOD | Body triangles | Min IoU | Pooled IoU | Min SSIM | Numeric visual threshold |
|---|---:|---:|---:|---:|---|
| 0 | 14954 | 0.997335 | 0.998742 | 0.955452 | PASS |
| 1 | 2399 | 0.968946 | 0.972074 | 0.688446 | PASS |
| 2 | 1727 | 0.967976 | 0.971360 | 0.757460 | PASS |
| 3 | 682 | 0.930328 | 0.937557 | 0.746825 | FAIL |

[Reduction sheets and curve](review/round3/reduction/README.md). No blanket perceptual exception is claimed.
A numeric or visual failure remains a failure, even when a separate binding/viewer check passes.

| Gate / region | Rows | Worst | Limit | Clip / LOD / seconds |
|---|---:|---:|---:|---|
| arm_body_penetration_mm / L | 2 | 3.3844 | <= 2.0 | Running / Merchant/colour0 / 0.375 |
| cloth_penetration_mm / coat hem | 56 | 87.4117 | <= 2.0 | Death / Merchant/colour0 / 0.9791666666666666 |
| finger_curl_min_deg / R | 8 | -5.1219 | >= 10.0 | Attack / Merchant/colour0 / 0.375 |
| floor_penetration_mm / L | 2 | 2.7816 | <= 2.0 | Death / Merchant/colour1 / 0.9166666666666666 |
| grip_gap_mm / club R index | 2 | 27.5132 | <= 3.0 | Attack / Merchant/colour3 / 0.8125 |
| grip_gap_mm / club R middle | 6 | 23.8423 | <= 3.0 | Attack / Merchant/colour3 / 0.8125 |
| grip_gap_mm / club R ring | 6 | 9.1764 | <= 3.0 | Attack / Merchant/colour3 / 0.8125 |
| grip_gap_mm / club R thumb | 8 | 75.2545 | <= 3.0 | Attack / Merchant/colour3 / 0.8125 |
| grip_penetration_mm / club R | 6 | 5.4369 | <= 3.0 | Attack / Merchant/colour0 / 0.7708333333333334 |
| prop_body_penetration_mm / club | 14 | 63.6051 | <= 2.0 | Death / Merchant/colour0 / 0.0 |


**Cloth-check limitation:** 27/28 saved colour-LOD coat findings have their nearest point on the
checker's synthetic opening cap. The worst 87.412 mm Death sample is a boot exiting below the raised rear hem,
not a boot puncturing the cloth at that location; see [marked side](review/round3/cloth_fault_left.png),
[marked rear](review/round3/cloth_fault_back.png) and [per-finding localization](review/round3/cloth_findings.json).
A folded hem is not planar. This diagnosis does **not** waive the shared failures or claim that every remaining
cloth/contact sample is harmless. The shared runner was not modified and no replacement gate was introduced.
Club/body contact, coarse-LOD grip contact and any remaining gait/finger rows still need repair or an explicit
orchestrator review of the checker evidence. This candidate is not certified for final installation.

### Integration, budget and ownership

**integration/actors.yml changed only its review comment. Descriptor semantics are unchanged** from round 2:
scale 103.944653064, yaw -1.570796327, z offset -0.103944653, walk/run strides 0.84 / 1.302,
impact 0.8125, ids 577/578/579, Cast=Attack and Club attachment names retained.
[Staged descriptors](integration/actors.yml); the orchestrator owns installation/regression/game captures.

**20 credits spent this round; 80/100 total; 20 remain.** Head task
`01a133e8-f805-76c9-a51f-1376f2aee5e5` and hand task `01a133e8-9909-73d8-a291-1086543609c5`
cost 10 each. The first head request was rejected before task creation (mutually exclusive text/multiview
parameters), costing 0. No pending jobs. Requests/receipts are under work/round3 and meshy/.

Selected authoring state: work/round3/master.blend, work/round3/body_lod0..3.blend,
work/round3/shared_textures and review/reduction/selection.json. The final export pipeline is
round3_export_selected.py (Blender, --threads 4), round3_package.py and round3_viewer.py (system Python),
then portable copies, export_identity.py, round3_configure_gates.py, the shared run_gates.py, and review scripts.
Do not rerun round3_reduce.py: the single clothing rebake is already complete. Weight/cloth experiments and
old round-2 scripts are historical, not the selected pipeline.

README and creature_3d_progress.json identify the same revision. Lease is released at handoff.
No assets_dev/source installation, game launch, build or commit was performed. Native mm6_mer1 was read-only.

---

## Historical review round 2 (regenerated body)

The previous handoff, including its superseded hashes and findings, is preserved at
[work/round3/HANDOFF.md](work/round3/HANDOFF.md). Current exports are exclusively those listed above.

## Texture size (orchestrator, 2026-10-13)

Oversized embedded maps were scaled down (largest side capped at 1024, Lanczos) with no visible difference at close range;
the previous export is kept as `export/mm6_mer1_club_prelarge_backup.glb`. Geometry, rig, clips and materials are unchanged.
