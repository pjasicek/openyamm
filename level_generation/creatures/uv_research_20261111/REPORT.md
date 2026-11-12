# UV unwrap and Meshy preparation: report (2026-11-11/12)

Research only: nothing installed. Brief: `BRIEF.md`; subjects: `SUBJECTS.md`; credits: `LEDGER.md` (75 of 100 spent,
backup account 580 -> 505). Earlier trial tables: `partuv/RESULTS.md` (PartUV with PartField and the bone tree) and
`layout/RESULTS.md` (gutter/margin, hidden seams, packing); they stand unchanged.

## Question

What is the most effective way to UV unwrap and prepare a reduced creature mesh for a Meshy retexture (meshy-7,
`enable_original_uv`, multiview HD masters), compared with the current `claude_shared/uv_atlas.py` route? Targets:
atlas 70 % (55-60 % realistic), density spread <= 1.3, fragments <= 3 % (hair cards excepted), stretch p90 <= 1.5.

## Verdicts

| Question | Verdict |
|---|---|
| Unwrap | **PartUV with the skin-weight part tree at threshold 1.25, then the seam pass, then sparrow.** Licence-clean (no PartField; PartUV itself is Apache-2.0). Against xatlas + seam pass + sparrow: atlas better or equal on 4 of 5 sets (+7.9 points on the BHydra body), stretch lower on 4 of 5, visible seam about equal. Elsewhere the xatlas route is within 1-3 points and is the fallback if the 8 GB PartUV venv is unwanted. PartUV without the seam pass leaves 26-48 % more visible seam: never use it alone. |
| Seams | Seam pass at p90 stretch <= 1.25, 6 rounds. Painted seam step x visible length falls from **110 to 60** (m620 body), and both paints of the winning upload agree (59.8, 59.6), so the gain survives Meshy's noise. The seam step (8.2-8.9 levels) is below the paint's own change over 1.5 texels (12.2-12.4). |
| Packer | sparrow (free, MIT): 69.7-74.7 % on the chosen charts, 4-texel gap, exactly one scale. xatlas brute force: 56.5 % on the m620 body. |
| Gutter | Keep the 2 px margin (xatlas padding 2 leaves >= 4 empty texels). Re-fill gutters with the nearest island texel as the last step on every map (colour, mask, normal, roughness). Meshy's returns are already filled; MM9 grading and the hydra's installed paint darken them. |
| 4K vs 8K | 8K costs 15 credits and returns only base colour at 8192 (other maps 4096). It has real detail above 4K, about 2x the energy in 4K's finest octave; after the single 2K downsample that is +6 % fine band and -10 % blotch, against an 8 % difference between two 4K draws. **4K stays the default**; 8K for hero models only. |
| Noise floor | Identical-camera differences (2K, mean of 8 views): two layouts 12.6 levels; **same upload twice 12.0**; two layouts 9.7. Layout effects on the look do not exceed Meshy's noise; only the layout numbers and the seam step separate layouts. |
| Drift | Fresh paints change designs. m620: the mossy vest becomes pebbled scale on all four body paints; the head paint is a different, younger face with an olive neck. BHydra body keeps its designed pattern and is much sharper. Painting all five BHydra heads in one job from whole-creature masters turned the blue head olive-green. |

## Method

- One prepared mesh per set for every variant (`scripts/layout/uv_seam_trial.py`): rest pose, visibility from 72
  game-like cameras on the whole creature, set subset, m620 head welded at 1e-5 m (4,144 -> 3,133 vertices), material
  cleared.
- `scripts/combo/run_subject.sh`: export, `partuv_run.py bones 1.1 1.25 1.5`, variants through
  `scripts/uv_atlas_seam.py` (`charts_npz=`, `packer=none`): p0 = plain PartUV charts, p1 = PartUV + small-chart merge
  at `max_stretch` 1.25 + seam pass; then sparrow (4-texel gap, continuous rotation, 5 x 60 s), `apply_layout.py`,
  `glb_add_material.py`, `texture_quality.py`. `pack_eval.py` confirms gap >= 4.0 texels, one scale, no overlap.
- Paints (`scripts/combo/paint_eval.py`): Lanczos 4K -> 2K once, nearest-texel gutter fill, texture-space DoG bands
  (speckle G1-G4, blotch G4-G16), seam step against a 1.5-texel control, identical-camera renders
  (`paint_views.py`, cameras from bone centroids so every layout of a set shares exact cameras), pairwise mean /
  low-pass / high-pass differences against the installed paint. Every returned GLB kept its upload layout.

## Combined layouts

Atlas % / fragments % / stretch p90 / visible seam. Per-set tables: `combo/table_<set>.md`.

| Set | Fresh `uv_atlas.py` | xatlas + seam + sparrow | p0 t1.25 | p1 t1.1 | **p1 t1.25 (chosen)** |
|---|---|---|---|---|---|
| m620 body | 56.5 / 0.1 / 1.17 / 17.26 | 69.5 / 0.0 / 1.24 / 11.96 | 71.8 / 0.8 / 1.14 / 15.48 | 71.3 / 0.3 / 1.21 / 13.39 | 69.8 / 0.2 / 1.18 / 12.88 |
| m620 head | 53.6 / 31.7 / 1.16 / 11.0 | 70.6 / 30.0 / 1.18 / 10.26 | 70.9 / 30.3 / 1.09 / 10.83 | 68.6 / 29.2 / 1.19 / 10.37 | 69.7 / 28.8 (hair) / 1.18 / 10.23 |
| BHydra body | 53.5 / 2.1 / 1.14 / 17.79 | 66.8 / 1.4 / 1.21 / 9.44 | 78.5 / 4.4 / 1.12 / 12.45 | 74.3 / 1.8 / 1.20 / 9.51 | **74.7 / 1.9 / 1.18 / 8.75** |
| BHydra heads | 54.8 / 5.6 / 1.20 / 12.08 | 70.4 / 3.1 / 1.25 / 9.38 | 72.7 / 6.3 / 1.21 / 9.98 | 72.6 / 4.7 / 1.20 / 8.99 | 71.1 / 3.8 / 1.23 / 8.74 |
| Magreeb | 53.7 / 2.1 / 1.21 / 14.59 | 70.5 / 0.8 / 1.26 / 8.97 | 71.3 / 2.4 / 1.13 / 13.22 | 70.5 / 0.7 / 1.17 / 8.94 | **72.9 / 0.4 / 1.19 / 9.29** |

The Magreeb head stays denser (density p50 about 4,200 against 2,339 overall). The BHydra heads miss the 3 % fragment
target on both routes (teeth and fins are loose pieces). Final layouts, never re-run:
`paint/uploads/m620_body_baseline_upload.glb` and `paint/uploads/<set>_winner_p1t125_upload.glb`
(records `combo/<set>/p1_t1.25_sparrow.npz`, UVs on the rigged set in `final/p1_t1.25.blend`). The Magreeb upload
was not painted.

## Paid jobs (75 credits)

| Job | Credits | Purpose |
|---|---|---|
| 1 | 10 | m620 body, fresh `uv_atlas.py` baseline layout, 4K |
| 2 | 10 | m620 body, chosen layout, 4K |
| 3 | 10 | job 2 again: noise floor |
| 4 | 15 | m620 body, chosen layout, 8K |
| 6 | 10 | m620 head, chosen layout, 4K, production head masters (`references_head/00-03`) |
| 5a | 10 | BHydra body, chosen layout, 4K |
| 5b | 10 | BHydra heads, chosen layout, 4K, whole-creature masters |

All except job 6 used `references_hd/01, 03, 02, 04` as production did.

- Seam step x visible length, jobs 1 / 2 / 3 / 4: 110.2 / 59.8 / 59.6 / 85.9 (control step 12.2 / 12.4 / 12.4 / 16.3;
  job 4's higher values come from its sharper paint).
- Detail bands in shot space, blotch / speckle: job 1 7.41 / 6.77, job 2 7.19 / 7.08, job 3 7.88 / 7.06,
  job 4 7.58 / 8.30; installed 6.18 / 4.74.
- Sheets: `paint/eval/m620_body_sheet.png`, `m620_body_8k_sheet.png`, `m620_body_crops.png`, `m620_head_sheet.png`,
  `hyd_body_sheet.png`, `hyd_heads_sheet.png`.

## Proposed changes (applied on 2026-11-12, see "Adoption" below)

`claude_shared/uv_atlas.py`:

1. `packer='sparrow'` as default, xatlas as fallback: port `scripts/layout/sparrow_pack.py` (separation = 2 x margin,
   continuous rotation, 5 x 60 s, start scale from a 66 % fill) with a `claude_shared/sparrow_venv`.
2. Seam pass on by default (`seam_rounds=6`, `seam_stretch=1.25`) with the 72-camera visibility computed inside
   `unwrap`; drop `vis_target`, which gained nothing.
3. Optional `charts='partuv'`: skin-weight tree at t1.25 in its own venv, then the small-chart merge with
   `max_stretch=1.25`, then the seam pass.
4. Guard the installed-GLB traps: `correct_aspect=False` (or clear the material: a non-square image such as m620's
   4128x2048 squeezes SLIM charts to stretch 2.2) and weld at 1e-5 m (split head vertices).
5. Return the seam measures in the report.

`claude_shared/TEXTURE_QUALITY_PASS.md`:

1. New defaults; about 70 % atlas as the target.
2. 4K stays the default; 8K only for hero models.
3. One paint is one random draw: judge layouts by their numbers. Where faces or designed patterns matter, budget a
   second draw or keep the approved colour (`keep_head`, `match_tone`).
4. Paint each head of a multi-head creature from its own masters.
5. Nearest-texel re-fill as the last step on every map.
6. Add the seam-step and identical-camera checks.
7. Pitfalls: non-square material image, split vertices, Blender's exporter dropping the material on imported
   creatures, Meshy calls sharing the lease's write lock with Blender runs.

## Adoption notes for openyamm-b9

- **m620 body (jobs 2, 3, 4)**: usable if the new look is accepted. All crisp; all turn the mossy vest into pebbled
  scale. Job 4 has the best hands, job 3 the cleanest back. Rebuild: re-join the body set (split at u < 0.5, not
  welded) with the head set as two 2K materials instead of the 4128x2048 atlas, tone-match the vest to the approved
  paint, rebuild regions/ramps and LODs, gutter re-fill last.
- **m620 head (job 6)**: hair only; face and neck drift. The head was welded, so rebuild the runtime head from
  `combo/m620_head/final/p1_t1.25.blend` and check shading at the welded seams. Keep the approved face colour on the
  new layout and take only the hair detail from job 6.
- **BHydra body (job 5a)**: adoptable; keeps the design and is sharper. Re-join with the heads set; tone diamonds and
  neck stubs to the approved colours.
- **BHydra heads (job 5b)**: not adoptable as a whole (blue head olive-green, red head dull). Repaint each head from
  its own masters (`references_heads/h<k>/`, 10 credits each) or keep heads 1-3 and repaint 4 and 5. The heads
  texture becomes one 2048 square instead of 1536x1024 (density p50 1,909 against 884).

## Files

- Scripts: `scripts/combo/` (`run_subject.sh`, `paint_views.py`, `paint_eval.py`, `combo_table.py`); research copies
  `scripts/uv_atlas_seam.py`, `scripts/layout/{uv_seam_trial,apply_layout,sparrow_pack}.py`.
- Outputs: `combo/<set>/`, `paint/{requests,refs,uploads,installed,specs,views,eval}/`, `meshy/<job>/` (592 MB).
- Environments: `sparrow_venv/` moved to `claude_shared/sparrow_venv/` on 2026-11-12 (adopted). Delete when the
  study closes:
  `partuv/venv/` (8.1 GB), `partuv/weights/` (1.6 GB, PartField: non-commercial licence, research only).

## Adoption (2026-11-12)

The user approved the method with one change: **PartUV with the skin-weight tree is the default chart method**, xatlas
the fallback. Ported to `claude_shared/` (no research imports):

- `uv_atlas.py`: new defaults `charts='partuv'` (threshold 1.25) -> merge (`max_stretch='auto'`: 1.25 on PartUV
  charts) -> seam pass (`seam_rounds=6, seam_stretch=1.25`, 72-camera visibility inside `unwrap`, `vis_objects` for
  occluders) -> density/head -> `packer='sparrow'` (2 x margin, continuous rotation, 5 x 60 s, 66 % start fill);
  `weld=1e-5` (refused if a face would collapse or the face order would change) and `correct_aspect=False`. Automatic
  fallbacks to xatlas charts and to the xatlas packer, printed and listed in `fallbacks`; report adds `charts_used`,
  `packer_used`, `seams`, `weld`. `charts='xatlas', packer='xatlas', seam_rounds=0` is the old code path.
- `partuv_charts.py` (in `claude_shared/partuv_venv`, 449 MB: partuv 0.1.2 + scikit-learn, no torch; loads only the
  compiled `_core`, never PartField), `sparrow_pack.py` (in `claude_shared/sparrow_venv`, moved here),
  `gutter_fill.py` (nearest-texel re-fill, CLI + `coverage()`/`pad()`).

Verification on copies of this study's prepared meshes (`verify/`, `scripts/combo/verify_port.py`,
`verify_queue.sh`):

| Run | Charts used / packer | Atlas % | Equiv. px | Spread | Islands | Fragments % | Stretch p90 | Reference |
|---|---|---|---|---|---|---|---|---|
| m620 body, defaults | partuv / sparrow | 69.8 | 1711 | 1.14 | 72 | 0.2 | 1.18 | research p1 t1.25: identical |
| m620 body, `charts='xatlas', packer='xatlas', seam_rounds=0` | xatlas / xatlas | 56.5 | 1539 | 1.10 | 131 | 0.1 | 1.17 | research `base_default`: identical |
| m620 body, PartUV missing (simulated) | xatlas / sparrow | 68.8 | 1698 | 1.10 | 60 | 0.0 | 1.24 | research xatlas + seam + sparrow 69.5 % |
| m620 body, sparrow missing (simulated) | partuv / xatlas | 57.2 | 1549 | 1.14 | 72 | 0.2 | 1.18 | same charts, xatlas brute pack |
| BHydra body, defaults | partuv / sparrow | 72.9 | 1749 | 1.13 | 84 | 1.9 | 1.18 | research 74.7 %: same 78 charts, sparrow run-to-run |

Both fallbacks printed `UV_ATLAS FALLBACK ...` and were listed in the report. `partuv_charts.py` gives UVs identical
to the research run (max difference 2e-16). Seam lengths in `unwrap()`'s report are in the set's own size, so they
read about 15 % higher on the m620 body than the research trial's (which divided by the whole creature with its
head). The BHydra check ran under the research folder's m620 lease: `mm6:hyd` was held by b9's adoption session
(`mm6_hyd_texpass_claude`), and only research copies were read and written. Layout images:
`verify/m620_layouts.png` (defaults, old flags, both fallbacks), `verify/*_heat_density.png`.

