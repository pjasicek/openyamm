# MM6 PeasantF3 / mfp — batch handoff

## Review round 3 (death timing)

The user accepted Cutpurse otherwise. The requested **Death-only timing change is complete and verified**.
Updated 2026-10-13T06:07:48.046671+00:00. [Accepted round-2 handoff](work/round3/before/HANDOFF.md) preserves earlier production details.

Death: **2.979166667 s → 2.144444444 s**. Source frames 100–143 at 48 fps run at 1.5×;
the complete result then runs at 1.25×. The old frame-100 pose now occurs at **1.666666667 s**.
The last segment lasts **0.477777778 s**. Effective speed is 1.25× before the boundary and 1.875× after it.
The exact endpoint is 102.933333 audit frames at 48 fps; it is intentionally not rounded to an integer frame.

### Scope and preservation

- All 716 dense Death pose samples are retained; only timestamps change. Sparse exporter-compressed tracks gain
  an interpolated boundary key to preserve their original path. No pose smoothing or spatial edits.
- Shared-sampler comparison at 1431 corresponding times: maximum node position discrepancy
  **0.000360019 mm**, from float32 timing/interpolation. Final corpse matrix difference **0**.
- **Dead and every other clip are unchanged**, including key data and durations. All seven shared-sampler comparisons are exactly zero.
- Original binary payload is retained byte-for-byte: mesh topology, vertices, normals, UVs, weights and embedded textures.
  Knife export is unchanged. No triangle reduction, no texture work and no additional paid generation.
- Packed authoring and new editable checkpoints **work/round3/lod0.blend … lod3.blend** carry the retimed Death action.
  Canonical textures remain **work/round2/textures/**. Prior checkpoints stay preserved.

[Timing and file-change receipt](review/round3/retime_receipt.json), [shared-sampler preservation](review/round3/motion_preservation.json),
[authoring receipt](review/round3/authoring.json), [Death sheet](review/round3/Death.png).

### Delivery and integration

| File | SHA-256 |
|---|---|
| [export/mm6_mfp.glb](export/mm6_mfp.glb) | `d52d216f660066857b4040b2b772ffb104cc7b39cd92b28f720e36c21f354bdd` |
| [export/mm6_mfp_knife.glb](export/mm6_mfp_knife.glb) | `a4832de680de045ac54508fc98853ac7055a542cc9fa2acfcc83d3007330c7a7` |
| [export/mm6_mfp.blend](export/mm6_mfp.blend) | `eb6fa4c068a418d8220286da0d268ad3c6e6f4fd0d3efb70d895594f5b0ba54b` |
| [integration/actors.yml](integration/actors.yml) | `67857a0d7c7ac8f2582600a493df2052454f908764000e81509b4bf029d37fb9` |

**integration/actors.yml changed: no, byte-identical.** Death has no impact event or descriptor duration to update.
Attack remains 1.125 s; melee/ranged/cast impacts remain 0.656250 s. IDs 601–603, scale 107.495710585,
yaw −π/2, skins mfp_a/b/c and strides remain unchanged.

The orchestrator installs the revised body with **tools/install_model.py --world mm6** and runs runtime checks.
The already-installed knife and actor descriptors need no replacement. This session did not install, launch a game,
build or commit. Meshy spending remains **55/100 credits** (0 this round).

| LOD | Body triangles | Knife triangles | Total |
|---|---:|---:|---:|
| 0 | 10,183 | 2,344 | 12,527 |
| 1 | 5,513 | 1,289 | 6,802 |
| 2 | 2,278 | 543 | 2,821 |
| 3 | 1,235 | 303 | 1,538 |

Colour and shadow counts are unchanged. 121 joints and eight clips. No geometry or material changes.

### Verification

- Shared runner: **PASS — 6,288 PASS, 136 INFO, 72 N/A**. Same gates.json and thresholds.
- Death floor penetration maximum **0.901704 mm**, arm stretch max **2.290938**, arm stretch P99 **1.770072**,
  hand stretch max **1.000345**; all pass existing limits across all LODs/shadows.
- Death angular acceleration max **12198.866 degrees/s²**, largest 48 Hz rotation step **14.021697 degrees**; no new pops.
- Bindings/weights: **no BAD line**. Shared viewer: **24/24** switches, no console errors or failed switches.
- Refreshed front/side/three-quarter Death sheet inspected. Final corpse and floor contact match the accepted poses.
  Other review sheets remain unchanged. Browser captures use software WebGL, not game GPU evidence.

[Full gates](review/round3/shared_gates/gates.md), [JSON/hashes](review/round3/shared_gates/gates.json),
[bindings](review/round3/bindings.txt), [viewer](review/round3/viewer_check.json), [review index](review/round3/README.md).
All 19 canonical texture files and 240 native/library receipts still match their prior hashes.
No known new fault. The batch rules leave installation/game verification to the orchestrator.

### Re-exported GLBs

| File | New SHA-256 |
|---|---|
| `export/mm6_mfp.glb` | `d52d216f660066857b4040b2b772ffb104cc7b39cd92b28f720e36c21f354bdd` |
| `export/mm6_mfp_level0.glb` | `a469119761448c692daade306e73b34261830111e85c123b6dda0b26b0bd4913` |
| `export/mm6_mfp_lods.glb` | `d7d53df2eda61fddbc3cede1392f19765199e13800edd3953b67d1d8e2cf292f` |
| `review/viewer/mm6_mfp_a.glb` | `5a583ab4bcd12f3dd8a57aaffc393b22bcb9bdf8e85ebbe476ee8b8fd42f4fca` |
| `review/viewer/mm6_mfp_b.glb` | `ec5a940a5e81ffba56cab79ccf27425880768909109350052f0a364d5513596b` |
| `review/viewer/mm6_mfp_c.glb` | `493f4f1c13555227b486ce56c715e293f41ea844d7eba14232c60160ea262b73` |
| `work/final_check_lod0.glb` | `d7d53df2eda61fddbc3cede1392f19765199e13800edd3953b67d1d8e2cf292f` |
| `work/final_check_lod1.glb` | `858938d20929b7be0bc49b43110b46181fb02800d899e12d28c166124ec85284` |
| `work/final_check_lod2.glb` | `29a2c45ad14da4e54fe2f5e77d2fd38071f805a877b447b2160467c62d102931` |
| `work/final_check_lod3.glb` | `c12b2bcf4427d1eb3579aa285a0718279c568ef9189e4dc18cefaecf286f7a05` |

[Complete current manifest](export/manifest.json) includes editable checkpoints, review evidence and scripts.
Production scripts: scripts/round3_retime.py, round3_authoring.py, round3_review.py, round3_finalize.py.
Reproduce the timing patch from the accepted round-2 snapshot; do not rerun the historical round-2 full exporter over this delivery.
Historical round-2 LOD viewer assets are retained as historical evidence, not current animated delivery.

## Texture size (orchestrator, 2026-10-13)

Oversized embedded maps were scaled down (largest side capped at 2048, Lanczos) with no visible difference at close range;
the previous export is kept as `export/mm6_mfp_prelarge_backup.glb`. Geometry, rig, clips and materials are unchanged.
