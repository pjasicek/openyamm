# MM8 Phoenix (`m572`, Fire Bird / Phoenix / Grand Phoenix) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant, with the scripts of
[mm8_m492_reduce_claude](../mm8_m492_reduce_claude/README.md) (coincident-vertex separation, exact source weights,
mouth keep). No Meshy credits.

Source: installed `assets_source/worlds/mm8/models/mm8_m572.glb` (identical to `mm8_m572_claude/export/`,
attack-v3), copied to `work/mm8_m572_source_pre_reduce.glb` (rollback source). One body material (`Phoenix_A`,
variants B/C), a separate `PhoenixFlames` node (288 triangles, own LOD1-3) left untouched, 4 influences.

## Ladder

Weld 20,842 -> 1,515 open edges (detached feather sheets), 389 coincident vertices with other weights kept apart;
5 duplicate faces with identical weights merge on import (14,872 -> 14,867; the material is double-sided, so no
reversed copies are needed). Limits scaled to the 0.82 m wing span (p99 2.46 mm, max 12.3 mm).

The uniform ladder bridged the split beak seam (lower bill on Jaw): 21 faces at 70 % and 10 at 55 % stretched
over 20x in Attack (`scripts/stretch_check.py`). `mouth_keep.py` (`REA_MOUTH_Y=-0.17 REA_MOUTH_R=0.008
REA_MOUTH_TEETH=0`) keeps 858 faces around the beak seam exactly; afterwards only the source's own single stretched
chest face remains at every step.

| step (beak kept) | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 14,872 | | | | |
| 70 % | 10,405 | 1.10 / 4.34 | 0.993 | 0.983 | pass |
| 65 % | 9,663 | 1.42 / 8.17 | 0.989 | 0.982 | pass |
| **60 %** | **8,919** | 1.78 / 8.31 | 0.982 | 0.982 | **auto-pick** |
| 55 % | 8,175 | 2.27 / 10.12 | 0.973 | 0.980 | fail (IoU) |
| 45 % | 6,689 | 3.36 / 11.59 | 0.955 | 0.974 | fail |

55 % fails on the front view only: small gaps open between the primary feather tips seen edge-on
(`review/iou_front_crops.png`). Close-ups (`review/close/sheet_a.png`, `sheet_b.png` for 70/55/45,
`sheet_r60.png`): beak open and closed, face, talons, tail fan and both wing surfaces match at 60 %. Texture drift
at 60 %: 12 faces over 40, 0.6 cm2 (70 %: 0.4 cm2); no drift lock.

## Build

`export_cand.py` (Cand_60) -> `swap_lod0.py` (now keeps other nodes' LOD meshes: the flame LODs) ->
`build_lods.py` (0.5 / 0.25 / 0.125, 4 influences, as the m572 project) with the Death/Dead floor contacts
protected (`floor_contacts.py`, 72 points) -> `carry_variants.py` (now tolerates the flame mesh without shadow LODs):
`export/mm8_m572.glb`, 11.8 MB (installed 13.6 MB), 9 clips, 3 variants on all 15 primitives.

| | LOD0 | LOD1 | LOD2 | LOD3 | flames |
|---|---:|---:|---:|---:|---|
| installed | 14,872 | 7,430 | 3,712 | 1,836 | 288 / 216 / 144 / 72 |
| reduced | 8,919 | 4,454 | 2,206 | 1,079 | unchanged |

`work/lod_check_{src,r60}.json`: every LOD keeps the source bounds; Death/Dead stay above the floor at every LOD
(lowest 1.7 mm, source 1.7 mm). Without the protected contacts LOD3 Death went 3.7 mm below the floor. Flight
clips dip below the actor origin by design (wing strokes, as the source). `review/lods/sheet.png`: LOD2/3 wings look a
little sparser than the installed LOD2/3 in the Dead pose (feather sheets thin out at those budgets).

Viewer: `review/viewer/` (three tiers, installed vs 60 %; region ramps baked with alpha kept for the plumes,
identical to the m572 project's tier bakes). `tools/run_creature_review.py ... check`: 54 clip switches, no errors.

## Status

Not installed. Install: `python3 tools/install_model.py
level_generation/creatures/mm8_m572_reduce_claude/export/mm8_m572.glb --world mm8`; regression:
`OPENYAMM_REGRESSION_FILTER=mm8_phoenix_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_phoenix_actor_models_keep_native_tiers_and_simulation`). Rollback: install
`work/mm8_m572_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=rollback source) -> `dump_mesh.py` -> `small_pieces.py` ->
`mouth_keep.py - work/keep_mouth.npy` (env above) -> `REA_KEEP_FACES=work/keep_mouth.npy run_ladder.sh m60
0.65,0.60` -> `stretch_check.py`, `close_ladder.py`, `close_sheet.py`, `texture_drift.py` -> build as above ->
`lod_check.py`, `lod_views.py`, `viewer_variants.py`.

## Retexture check (2026-10-18)

Verdict: body plumage, wings, legs, tail: **no retexture needed**. Head: **local fix, applied** (not Meshy, not installed).
No credits.

- Texture set: one material per tier (Phoenix_A/B/C) sharing a 2048² base colour, 1K normal/metal-rough/region
  mask, three tier ramps; flames separate (unchanged). No separate head set. All six images are byte-identical in the
  reduced export, so the UVs stay valid.
- Texel density (`scripts/retex_stats.py`, `review/retexture/stats.json`): head 2,216 texels/m, the rest 980-1,000.
- Drift at 60 % by region (faces over 40 / cm²): head 1 / 0.16, wing 1 / 0.01, leg 9 / 0.33, others 0-1; nothing
  visible.
- Normals: the installed GLB shades smooth; clay renders of the source GLB and the reduced export (direct imports)
  match, including the source's own dark facets on the feather cards. No normal transfer needed.
- **Head colour**: the HD masters gave the bird a brown golden-eagle head and Meshy followed them. On the plumage ramp
  (mask 0) the head reads linear luminance 0.048 / 0.076 / 0.133 (p10/50/90) against the neck's 0.174 / 0.378 /
  0.551 and the body's 0.095 / 0.315 / 0.516, so the head maps to the dark end of every ramp: dark brown on gold,
  pink-white and red tiers alike. 43 % of the head texels are outside every mask (beak, brown brow/cere, eyes, mouth),
  so the brow stays brown in every tier. The native sprites colour the head like the body in all three tiers.
  A Meshy retexture from the same HD masters would paint the brown head again, so it would also need new masters.
- **Head fix applied (local, no Meshy)**: `scripts/unify_head.py work/mm8_m572_r60_pre_headfix.glb
  export/mm8_m572.glb` (texel positions from `scripts/head_texels.py`). The head plumage is quantile-matched to the
  neck (mask-0 luminance 0.046 / 0.076 / 0.124 -> 0.161 / 0.349 / 0.528; neck 0.176 / 0.384 / 0.553). 7,557 brown
  brow, lores and eye-surround texels that touch the plumage region join mask 0. The face stays a little darker,
  as in the native frames: up to 45 % around the eyes, 30 % on the lores. The beak (yellow keratin and grey hook), a
  1.5 mm cere band, iris, pupils and mouth keep their paint, and the original mask's beak and gape texels are
  cleared (2,397 at 1K): no tier tint on the beak. Only the base colour and region mask images change. Materials,
  variants, all LODs and shadow meshes reference them unchanged; the export is 12.0 MB (11.8 before). The pre-fix
  reduced export is kept as `work/mm8_m572_r60_pre_headfix.glb`.
- Viewer tiers rebuilt from the fixed export (`viewer_variants.py export/mm8_m572.glb r60`; labels "+ head fix"),
  `tools/run_creature_review.py ... check`: 54 clip switches, no console errors.
- Head sheet: `review/retexture/sheet_head_fix.png` (per tier: native frames, installed vs fixed side, three-quarter
  and front). Earlier previews: `sheet_head_unify_preview.png`.
- Sheets: `review/retexture/sheet_head.png`, `sheet_body.png` (clay + tiers, source vs reduced), `sheet_glb_normals.png`.

## Installed (2026-10-18)

User accepted the viewer ("ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py export/mm8_m572.glb --world mm8`; recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Regression: `OPENYAMM_REGRESSION_FILTER=mm8_phoenix_actor_models ./build/game/openyamm --headless-run-regression-suite actors: mm8_phoenix_actor_models_keep_native_tiers_and_simulation passes`. Rollback: install `work/mm8_m572_source_pre_reduce.glb` the same way.

## Floor fix — 2026-10-21

`--hover 0.288783 Death Dead`: the wing strokes cut 0.289 m (162 world units) under the floor. Every living clip is raised so the lowest stroke meets the floor; Death eases it out. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m572.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
