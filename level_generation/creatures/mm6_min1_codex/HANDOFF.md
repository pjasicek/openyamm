# MM6 BMinotaur — staged handoff

## Review round 3 (closed hips)

**Scoped hip repair exported and visually checked; full shared technical gates still FAIL.**
Budget **30/100 credits total; 0 this round**. No install, build, game launch or commit.

The old `trim_hidden_body.py` deleted skin that later showed through the ragged hem. Closed the waist and both
upper-thigh cut loops with one connected, pelvis/thigh-weighted fur surface at every colour LOD; regenerated all
shadow LODs. The legacy deletion script now fails explicitly instead of recreating the defect.
Also remapped **20/14/15/8** existing cut-rim triangles whose UVs sampled empty bake texels to opaque brown fur
already present in the atlas. The added surfaces use that same fur. No texture image or palette changed.
Kilt materials retain `doubleSided: true`; rear/front and moving-hip inspections no longer show the reported voids.

| LOD (colour and shadow) | Unintended skin edges below belt | All below-belt edges, including intended openings | Body triangles |
|---|---:|---:|---:|
| 0 | 63 → 0 | 254 → 191 | 7876 → 7995 |
| 1 | 37 → 0 | 124 → 87 | 1674 → 1743 |
| 2 | 37 → 0 | 121 → 84 | 1591 → 1660 |
| 3 | 22 → 0 | 73 → 51 | 735 → 781 |

Remaining below-belt edges are the **kilt hem/waistband and belt-jewel back**, itemized by native piece in
[geometry_receipt.json](review/round3/geometry_receipt.json). The full mesh's open-edge counts are
504→441, 254→217, 243→206, 147→125; upper mane/ornament boundaries remain outside this hip repair.
There are zero non-manifold edges after position welding. Colour and corresponding shadow counts agree.

The necessary closure adds **119/69/69/46** triangles. This exceeds the previous installed triangle caps;
the unchanged shared runner reports those eight colour/shadow cap failures. No unrelated reduction was performed.
The resulting LOD ratios are 21.80%, 20.76%, 9.77%; the chain still decreases strictly.
Axe triangles remain **1854/389/343/127**, with the entire axe GLB byte-identical.

**integration/actors.yml changed: NO.** All **2,214 animation channels** (including Attack, Death, Dead, axe motion
and cloth), embedded texture payloads and the standalone axe are byte-identical to the accepted round-2 export.
Original body vertex positions and weights are retained; only the added pelvis vertices receive new weights.
Attack impact remains **0.947917 s**, Cast **1.516667 s**; melee/ranged Attack, distinct Cast and sockets unchanged.

| File | SHA-256 |
|---|---|
| export/mm6_min1.glb | 2a93e0e8e8c81388090abdc6db3639a1b23ac2d5dfd51720657ca085296065f3 |
| export/mm6_min1_axe.glb | de14feab01d4fc3439d80e8cff27fd05a97928fd4f37cc2d1f5968a46f6538ef |
| work/production_master.blend | 981ceaca0ef936e9ceafc597488ad2bed95f47c93224f7c0405ca447bda9cfa0 |
| work/round1_lod1.blend | 6b5bbad456267f68789fc1dbe62990d6a03b22d6127074bb8e7d725719baae93 |
| work/round1_lod2.blend | 418fceca0a074c27821d27036f53a5cb1210f8e61f551f62ab22de9d06867a25 |
| work/round1_lod3.blend | 84cee2027996ea87ce9b55f16eb2f3be79118be8bc936cce513081a081446ae8 |
| integration/actors.yml | 3fa3809ccfb8afcf7a7b63d0972697a3a61790bc5c6e33c68f6fc92297ba3a8a |

Also updated: `work/runtime_master.blend`, the export intermediates, all three `review/viewer/mm6_min1_*.glb`
and its manifest, nine clip sheets, 72 all-LOD hip renders, browser close-ups, export/weight/binding reports,
README, progress and [artifact manifest](artifact_manifest.json). Repair/export/review scripts live in `scripts/round3_*`;
`finish_export.py`, `round1_pack_maps.py` and `validate_exports.py` now target round-3 evidence.
Accepted round-2 native files and exports are preserved in `review/round3/before/`.

### Verification and remaining findings

- [Geometry and preservation receipt](review/round3/geometry_receipt.json): zero unintended skin openings on
  all four colour and four shadow meshes; unchanged accepted animations, axe, image payloads and bindings.
- [Bindings](review/bindings_check.txt): **no BAD line**. [Loader/weights](review/export_validation.json): pass,
  maximum weight-sum error **1.382e-7**. These checks do not override the motion report.
- [Shared viewer check](review/viewer_check.json): **27/27**, zero console errors; Chrome closed after checking.
- [Shared gates](review/round3/shared_gates/gates.md): **FAIL**, **{'PASS': 6713, 'FAIL': 1195, 'UNVERIFIED': 38, 'INFO': 144, 'N/A': 32}**. All nine clips and all LODs sampled.
  [Comparison and cloth values](review/round3/GATE_COMPARISON.md) explicitly retain the old cloth/arm/grip/gait findings,
  six newly failing Death head-penetration rows, triangle-cap failures and the existing coverage limitations.
  **This is not an all-gates-passing or automatic-install handoff.** Accepted animation was not changed to chase them.

Review: [closed hips in the viewer](review/round3/closed_hips_viewer.png),
[all LODs standing](review/round3/hips_lods_Standing.png), [all LODs attacking](review/round3/hips_lods_Attack.png),
[Attack sheet](review/sheets/Attack.png), [Death sheet](review/sheets/Death.png), [viewer](review/viewer/index.html).
Original feedback images are in `review/round3/before/user_74.png` and `user_75.png`.

Next owner: **batch orchestrator** for review of the listed findings/count increase and integration of this staged export.
Do not copy these files to assets_dev directly; the orchestrator owns installation through the model installer.
Lease released at handoff. The sprite-restore source `../mm6_min1/` was read-only throughout.

## Review round 2

[Exact archived round-2 handoff](review/round3/before/HANDOFF.md) records the accepted attack/death changes and old hashes.

## Review round 1

[Exact archived round-1 handoff](review/round2/before/HANDOFF.md) and
[original reduction curve](review/round1/reduction/README.md) remain available. That curve predates this required closure.
