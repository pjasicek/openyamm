# MM6 Hydra texture pass from the UV study (`mm6_hyd`, BHydra A/B/C) — 2026-11-12

The user approved (2026-11-12) adopting the [UV study](../uv_research_20261111/REPORT.md)'s BHydra results onto the
installed hydra ("Adoption notes for openyamm-b9"). Stream: texpass ([audit fixes](../audit_mm678_20261111/fixes/COMMON.md),
recipe [TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)). Only UVs, images and texture references
changed; mesh, rig, weights, clips, sockets, materials, ramps, variants and `actors.yml` are the installed ones. Lease
`mm6:hyd` (token in `work/LEASE.txt`). Production history: [mm6_hyd_claude](../mm6_hyd_claude/README.md) (body, five
grafted heads), [mm6_hyd_reduce_claude](../mm6_hyd_reduce_claude/README.md) (r45 reduction).

## Texture pass from the UV study (2026-11-12)

**Layouts.** The study's chosen layouts (PartUV with the skin-weight part tree at t1.25, small-chart merge, seam pass,
sparrow packing; uploads `../uv_research_20261111/paint/uploads/hyd_{body,heads}_winner_p1t125_upload.glb`), made on
a copy of this same installed GLB (sha256 `debde2d2...` both). `scripts/hyd_import_layout.py` matches every installed
LOD0 triangle to the upload (corners within 1e-5 m: 3,289/3,289 body, 4,637/4,637 heads, none missing) and checks the
Meshy returns against the uploads after Meshy's bounding-box normalisation (UVs identical, max difference 0.0); it
writes the kit layouts `work/uv_study_body.npz` and `work/uv_study_heads.npz`. The texture sets stay two: body set
(prims 0, 1: `Hydra*`, `HydraB*`) and heads set (prims 2-4: `HeadsA/B/C*`), configs `texpass.json` and
`texpass_heads.json` (tag `_heads`). The heads image becomes one 2048 square instead of 1536x1024.

**Body: study job 5a** (`meshy/j5a_body/`, a copy of `../uv_research_20261111/meshy/j5_hyd_body_winner_4k`, paid by
the study). `tp_compose.py`: 4K -> 2K once (Lanczos), gentle grade with a new AO bake (`tp_bake_ao.py`, reach
0.035), quantile tone match per region class, then island by island the approved low band (sigma 4 texels) with the
paint's luminance detail x0.9 on top: this puts the approved colours back on the diamonds and the neck stubs that 5a
had made yellower and recoloured. Approved relief normal kept (p90 tilt 0.55) plus the paint's fine detail x0.5.

**Heads: repainted per head from their own masters.** Job 5b was not used. Every head drifted in its low band against
the approved paint at the same texels (mean |low-pass difference| 31 / 34 / 40 / 43 / 38 levels, heads 1-5,
`work/drift_5b.json`), so no head of 5b was clearly "matching" (head 3 drifted more than heads 1 and 2), and 5b's raw
heads showed the olive head 5 and dull head 4 the study reported. All five heads were repainted (5 x 10 credits):
- `scripts/hyd_head_uploads.py`: head k's triangles only, with the study's heads-layout UVs, turned into the frame
  Meshy painted that head in for production (snout +Z, up +Y; `mm6_hyd_claude/texturing/head<k>_st_upload.glb`):
  the Head<k> bone axis onto +Z, then a similarity ICP of the rigid skull onto the production Smart Topology upload
  (heads 1, 3, 5: 8-10 deg correction, skull fit p50 1.7-2.3 mm; head 2 with the scale held at the start estimate,
  33.7 deg, p50 3.2 mm; head 4's squeezed fins pull the ICP off, so the bone frame plus the mean 8 deg pitch of heads
  1/3/5). Checked in front, left and top views against the production uploads (`work/frames_all.png`, `work/frame_h*.png`).
- `requests/head<k>_retexture_v1.json`: meshy-7, 4K, `enable_original_uv`, masters
  `references_heads/h<k>/01_front, 03_left, 02_back, 04_right` (copies of `mm6_hyd_claude/references_heads/h<k>/`, the
  production order). Every return kept its layout (UV max difference 0.0) and its identity colours
  (`work/head_thumbs.png`: olive with orange spikes, purple with ivory horns, green, red with tan fins, blue).
- `scripts/hyd_merge_heads.py` -> `meshy/heads_merged/`: each texel of head k's charts from head k's job (gutters from
  the nearest chart's head).
- Compose as the body, plus `keep_mask` (`scripts/hyd_heads_keep_mask.py`, `work/heads_keep_mask.png`, 24.6 % of the
  heads texels): texels without a region (raw colour in every tier: mouths, teeth, eyes, small ivory) and the red
  mouths inside ramped regions (filled, grown 3 texels over the lip edge) keep the approved colour. Reason: the
  approved low band at sigma 4 tinted the repaints' small teeth from the gums (red teeth on head 3, a blotchy blue
  mouth on head 5, `review/shots` of the first compose). Large pale pieces (horns, throat plates) take the new paint.
  `keep_normal`: the approved head normals (baked from the 15k Smart Topology heads, p90 tilt 0.125, against the
  paint's 0.052) kept, plus the paint's fine detail x0.5.

**Rest.** `tp_apply.py` per set (body, then heads on its output): LOD0 vertices split at the new seams, LOD1 projected
per chart from LOD0, the LOD0/LOD1 shadow meshes take their triangles' new UVs, new images for the six body and nine
head materials (each set's region mask is one image now: the per-primitive masks resampled into the new layout, so
every material keeps its own channel meaning and ramps), LOD2/LOD3 keep geometry and UVs and their maps are refilled
from the new LOD0 at the installed sizes (512/256, 256/128, 128/64). Last step on every map:
`scripts/hyd_gutter_fill.py` (the study's finding), which gathers the triangles of every primitive that samples an
image and applies the shared `claude_shared/gutter_fill.py` (`coverage` at 4x supersampling, `pad`): every texel
outside the islands takes the nearest island texel (colour, mask, metal/roughness, normal; LOD0-LOD3, 48 images,
`work/gutter.log`). A first install used the same fill with texel-centre coverage; it was replaced on the same day
by the shared tool's coverage once that landed (coordinator, 2026-11-12) and reinstalled.

## Results (`texture_quality.py`, LOD0; `audit_before/`, `audit_after/quality.json`)

| | Body set before | after | Heads set before | after |
|---|---|---|---|---|
| Image | 2048² | 2048² | 1536x1024 | 2048² |
| Atlas use | 50.6 % | **74.7 %** | 42.9 % | **71.1 %** |
| Equivalent square | 1,457 px | 1,770 px | 1,006 px | 1,727 px |
| Density p10/p50/p90 | 765/1,156/1,429 | 1,327/**1,417**/1,507 | 713/884/1,098 | 1,785/**1,909**/2,028 |
| Spread p90/p10 | 1.87 | 1.14 | 1.54 | 1.14 |
| Islands / fragments | 83 / 1.1 % | 84 / 1.9 % | 955 / 24.5 % | 200 / **3.8 %** |
| Stretch p90 | 1.75 | 1.18 | 1.72 | 1.23 |

Tier colours (`tp_tier_tone.py`, same surface points, every region class of A/B/C): body within 1.2 sRGB levels of
the approved means, heads within 2.8. LOD1 against LOD0 colour error (`tp_lod1_check.py`): body 14.5/13.8 ->
14.9/16.7, heads 8.4/8.0/7.2 -> 10.5/10.9/11.9 (mean); the sharper paint raises point differences between the
reduced LOD1 surface and LOD0 (the projection's worst corners are 37-54 mm on reduced spines and teeth), not visible
at LOD1 distance; left as is.

## Checks

- `tp_diff.py` against the installed GLB: OK (only UVs, vertex splits, images and texture references differ).
- `check_winding.py` 0 inverted closed parts; `flat_shading_check.py` flat 0.00 on every LOD0 material.
- Viewer `review/viewer/` (installed and pass, tiers A/B/C, ramps baked by `tp_viewer_variants.py`):
  `run_creature_review.py check` 0 console errors, 42 switches.
- Floor audit BHydra A/B/C ok; motion audit `audit_after/` (UV-only change).
- Regressions after the final install (25 s after it): `mm6_mm7_mm8_actor_models_build_every_binding` PASS
  (647 descriptors on 185 models, 0 failed); the whole `actors` suite 191 passed, 2 failed, neither the hydra:
  `every_map_loads_and_builds_its_actor_models` (42 MM9 maps with actors without models, other sessions' MM9 work) and
  `out05_event_clearance_completes_from_monster_killed_hook` (fails alone too; a known MM8 quest case, other READMEs).
  `mm6_hydra_actor_model_tiers_follow_sprite_scales` PASS. Logs `work/regression_*.log`.
- Sheets (review-viewer shots at identical cameras, installed vs pass, every tier):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (every head, 3/4 front, and the heads front),
  [review/texpass_head_side_sheet.png](review/texpass_head_side_sheet.png) (every head in profile),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png) (full 3/4, front, back, neck bases, back close-up,
  flank), [review/texpass_closeups.png](review/texpass_closeups.png) (mouths, faces at full resolution).
- Drift: none in identity. Scales on every head and the neck net read sharper; eyes, mouths, teeth and small ivory are
  the approved paint; horns keep the approved colour with the repaints' detail.

Installed 2026-11-12 with `tools/install_model.py export/mm6_hyd.glb --world mm6`. Rollback:
`python3 tools/install_model.py level_generation/creatures/mm6_hyd_texpass_claude/work/before_texpass/mm6_hyd.glb --world mm6`
(actors.yml entries unchanged; copy in `work/before_texpass/actors_entries.yml`).

Credits: 50 (five head retextures, backup account 505 -> 455); the body paint is the study's job 5a (10, charged to
the study).

## Scripts (`scripts/`)

Kit copy from `mm6_mfp_texpass_claude/scripts/` (tp_compose.py with `keep_mask`, `detail_guard`), plus:
`hyd_import_layout.py` (study layout -> kit layout, exact-match checks), `hyd_heads.py` (head index per triangle),
`hyd_head_drift.py` (per-head drift against the approved paint), `hyd_head_uploads.py` (per-head uploads in the
production head frames), `hyd_quick_view.py` (frame check renders), `hyd_wait_heads.sh`, `hyd_merge_heads.py`,
`hyd_heads_keep_mask.py`, `hyd_gutter_fill.py` (per-image driver of `claude_shared/gutter_fill.py`, last step).

Rebuild, from `scripts/`:
`tp_dump.py` (both configs) -> `hyd_import_layout.py` (both) -> `tp_resample.py <layout> ../textures/approved/<set> 2048 1024`
-> `tp_bake_ao.py` (Blender) -> `tp_compose.py ... pass_body j5a_body -` and `hyd_merge_heads.py heads_merged`,
`hyd_heads_keep_mask.py`, `TP_CONFIG=texpass_heads.json tp_compose.py ... pass_heads heads_merged -` -> `tp_apply.py`
(body, then heads) -> `hyd_gutter_fill.py ../work/stage_heads.glb ../export/mm6_hyd.glb`.
