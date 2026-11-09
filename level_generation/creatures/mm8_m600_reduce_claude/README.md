# MM8 Nightmare (`m600`, Fear / Terror / Nightmare) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant (scripts copied from
[`mm8_m492_reduce_claude`](../mm8_m492_reduce_claude/README.md)). No Meshy credits. Not installed.

Source: the installed `assets_source/worlds/mm8/models/mm8_m600.glb`, identical to `mm8_m600_claude/export/`
(subtle-attack revision), copied to `work/mm8_m600_source_pre_reduce.glb` (rollback source). One material
(`NightmareSkin_A`, double-sided, A/B/C as `KHR_materials_variants` with region ramps), mesh node `Nightmare`,
58 bones, 4 influences, 7 clips. Weld 6,034 -> 37 open edges; no coincident vertex pairs (no split mouth seam).

## Problems and fixes

1. **Every candidate failed (p99 33 mm, IoU 0.84) although the geometry matched (max 3.7 mm at rest).**
   `reduce_ladder.py` set the candidate's `matrix_world` before assigning the parent and the source's parent inverse.
   The Nightmare mesh has a non-identity parent inverse, so every candidate sat 4 cm off. Fixed: parent, parent
   inverse, then the source's `matrix_basis`. (The dragon's parent inverse was identity, so it was unaffected.)
2. **Skin weights through UVs** (`uv_weights.py`, `REA_WEIGHTS=component`): the slime lumps interpenetrate, so a
   nearest-face transfer can take weights from a neighbouring lump. Each new vertex takes barycentric weights from
   the source triangle containing its UV (the texture-aware collapse keeps UVs on their chart), within 1 cm in 3D,
   else the nearest source vertex with a similar normal; source vertices keep exact weights. Slightly better than
   the nearest/piece transfer (r70 max 10.1 vs 13.4 mm).
3. **Kept exactly** (`work/keep_eyes_small.npy`, 3,550 faces): the rigid eye faces the creature's own LOD pass
   protects for the iris UVs (`eye_faces.py`, 2,124) and the separate teeth pieces (`small_pieces.py`, 1,426).
4. **Floor:** collapses placed new base vertices up to 1.1 mm below the flat slime base; `REA_FLOOR_Z=0` in
   `decimate_tex.py` projects them back onto the floor plane.
5. **LOD ratios:** the creature's own LOD pass (`build_lods.py`, a copy of `mm8_m600_claude/scripts/build_lods.py`:
   bent stalks, rigid eyes protected) at its 0.55 / 0.34 / 0.22 on the smaller LOD0 left LOD3 almost no body budget
   beside the 2,124 protected eye triangles: it lost half its length. 0.62 / 0.40 / 0.33 lost the teeth and streaked
   the base at LOD2/3. 0.65 / 0.50 / 0.40 matches the installed LOD2/LOD3 at distance (`review/lods/sheet.png`).

6. **Normals: plain smooth (normal transfer withdrawn).** A first build copied "custom sculpt normals" from
   `work/source.blend` (`REA_NORMALS=transfer`). That file is welded by `import_source.py`, and Blender stores custom
   normals relative to the default normals, so the weld scrambles them: the transfer copied noise. Ground truth
   straight from the GLBs (`glb_close.py`, `review/glbclose/sheet.png`: installed / transfer / smooth; `glb_normals.py`):
   the installed GLB's normals are plain smooth (median 4.7 deg from a smooth recompute, p99 25 deg at the split eye and
   teeth edges); the transfer build was 7.4 / 74.9 deg; the smooth rebuild 5.2 / 29.8 deg, like the source. The build
   now uses smooth normals; the transfer build is kept in `work/v1_transfer/`.
7. **Chart-border fleck:** one reduced face at the left stalk junction (r55 face 7508) had a UV corner moved onto its
   chart border and sampled mouth-red texels: a red (A) / orange (B) fleck the base-colour drift check (per-face
   median) does not see. `lock_faces.py` keeps the 38 source faces within 3 cm of it (`work/keep_fleck.npy`, 3,588
   faces kept in all); the fleck is gone in every tier (`review/retex/sheet_junctions.png`).

## Ladder (`uvfl`: UV weights, eyes, teeth and the fleck patch kept, floor clamp, smooth normals)

Limits for the 1.0 m model: p99 3 mm, max 15 mm.

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 15,986 | | | | |
| 70 % | 11,190 | 2.66 / 10.05 | 0.995 | 0.994 | pass (auto-pick) |
| **55 %** | **8,792** | 4.07 / 14.15 | 0.992 | 0.985 | **visual pick** (p99) |
| 45 % | 7,192 | 5.91 / 14.15 | 0.987 | 0.975 | fail |

55 % misses only the p99 gate; close-ups of all three mouths at the attack gape, the eyes, the lump field from
back and side, the corpse and mid-death match the source (`review/close/sheet_uv_a.png`, `sheet_uv_b.png`,
`sheet_uv_clay.png`). 45 % facets the front mouth's lip and shows a red fleck beside it. Texture drift at 55 %: 2
faces over 40, both floor-facing.

## Build

`export_cand.py` (Cand_55, node `Nightmare`) -> `swap_lod0.py` -> `build_lods.py` -> `shrink_shadow_lods.py` (the
creature's own) -> `carry_variants.py`: `export/mm8_m600.glb`.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 15,986 | 8,792 | 5,427 | 3,472 |
| reduced | 8,792 | 5,714 | 4,379 | 3,473 |

`work/lod_check_{src,r55}.json` (`lod_check.py`, `REA_NODE=Nightmare`): every LOD keeps the source bounds (LOD3
height 0.994 m, installed 0.991), no LOD goes below the floor in any frame, and no face stretches in any clip.

Viewer: `review/viewer/` (installed vs 55 %, runtime GLBs: tier A appearance; B/C are engine ramps).
`tools/run_creature_review.py --project level_generation/creatures/mm8_m600_reduce_claude check`: 14 switches, no
console errors.

## Install (after user review)

```
python3 tools/install_model.py level_generation/creatures/mm8_m600_reduce_claude/export/mm8_m600.glb --world mm8
./build/tests/openyamm_unit_tests --test-case='mm8 Nightmare slime actor bindings*'
```

Then add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install
`work/mm8_m600_source_pre_reduce.glb` the same way.

Reproduce: `import_source.py` (REA_NODE=Nightmare) -> `REA_PROTECT=EmbeddedEye,_Tip dump_mesh.py` -> `eye_faces.py`,
`small_pieces.py` (union saved as `work/keep_eyes_small.npy`) -> `dump_weights.py` ->
`REA_FLOOR_Z=0 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_eyes_small.npy run_ladder.sh uvfs 0.70,0.55,0.45` ->
`lock_faces.py work/keep_eyes_small.npy work/keep_fleck.npy r55 7508` -> the same ladder with `REA_KEEP_FACES=work/keep_fleck.npy`
(label `uvfl`, 0.55) ->
`close_ladder.py`, `close_sheet.py`, `texture_drift.py` -> build as above -> `lod_check.py`, `lod_views.py`.

## Retexture check (2026-10-18)

Verdict: **no retexture needed**, no Meshy credits spent. One optional local touch-up (teeth), not applied.

- **Texture set:** one shared set for the whole creature, `NightmareSkin_A/B/C` with 2048 base colour and 1024 normal,
  ORM and region mask (R skin, G iris); the tiers are engine ramps. There is no separate head set, so no head/body seam
  is possible. The reduction keeps the images byte-identical and the UVs valid
  (`scripts/retex_regions.py`, `work/retex_regions.json`). UV range is [0, 1]. No face is off the source charts and
  none has zero UV area. Texel density is 965 px/m (source 979).
- **Drift at 55 %:** 2 faces over 40 (6.1 cm², floor-facing). Per-region median and p99:

  | region | median | p99 |
  |---|---:|---:|
  | eyes | 0 | 14–27 |
  | front mouth | 0 | 20 |
  | mouth stalks | 6–7 | 28–29 |
  | lumps | 8 | 27 |
  | base | 12 | 28 |

  The eyes, teeth and front lip are mostly kept exactly. The base-colour drift check missed the one visible
  chart-border fleck; it is fixed above.
- **Colour consistency** (`scripts/retex_colour.py`, `work/retex_colour.json`; skin texels per region in each tier
  bake):
  - Hue spread across regions is 3 deg or less in every tier: A 123, B 303, C 24–27.
  - Luminance runs from the body lumps (median 0.063 in A) through the mouth stalks (0.093) to the eye stalks (0.134).
    The junction renders show this as a smooth painted gradient with no seam (`review/retex/sheet_body.png`, rows
    `junctionL` and `junctionR`).
- **Existing texture quality** (11 close-ups × 3 tiers, installed against reduced: `review/retex/sheet_mouths_eyes.png`,
  `sheet_body.png`, `sheet_junctions.png`):
  - Crisp scales, clean eyes (sclera, iris, veins), ivory teeth, dark-red mouth interiors and a clean base.
  - Near-black skin texels are 0.35 % of the eye-stalk samples and none elsewhere. They are dark pattern pockets on
    two upper eye stalks, not visible gaps.
  - Reduced matches installed everywhere.
- **Optional:** 16.6 % of the teeth texels carry an olive/green stain. The region mask never covers teeth, so the stain
  stays green on the B and C tiers too. `scripts/teeth_ivory_preview.py` repaints them ivory at their own luminance
  (`work/teeth_ivory_basecolor.png`; renders `review/retex/sheet_teeth_fix.png`). At game scale the difference is
  hardly visible, and one small lower front tooth stays stained, so this is a cosmetic touch-up for the creature
  project's `compose.py`, not a reason to retexture.

## Installed (2026-10-18)

User accepted the viewer ("ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py export/mm8_m600.glb --world mm8`; recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Regression: `./build/tests/openyamm_unit_tests --test-case='mm8 Nightmare slime actor bindings*' passes (41 assertions)`. Rollback: install `work/mm8_m600_source_pre_reduce.glb` the same way.
