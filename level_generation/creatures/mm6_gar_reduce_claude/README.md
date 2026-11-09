# MM6 Gargoyle (`gar`, BGargoyle A/B/C): body/rubble swap (installed 2026-10-14) and a staged reduction

## Installed: the living body and the rubble swap

The model has two skinned meshes: `Gargoyle` (living body, 7,249 triangles) and `Rubble` (36 stone pieces, 6,545
triangles, for the death collapse). Codex v6 hid the unused one by scaling its bones to 1e-5, which the renderer still
drew, skinned and shadowed: every living gargoyle cost 13,794 triangles at LOD0.

User (2026-10-14): swap the living and the dying/dead body so there is no extra overhead; keep the current 7k body.
`tools/model_hide_collapsed_meshes.py` keys each mesh node's scale to 0 (STEP) wherever all its bones are collapsed;
the renderer skips a mesh whose node matrix is singular (`Engine::modelMatrixVisible`). Geometry, textures, variants,
LODs and the authored bone animation are unchanged.

| clip | Gargoyle | Rubble |
|---|---|---|
| Flight, Attack, Hit | drawn | hidden |
| Death (0.95 s) | drawn until 0.100 s | drawn from 0.092 s |
| Dead | hidden | drawn |

A living gargoyle now draws 7,249 triangles instead of 13,794.

- Input: `mm6_gar_codex/export/mm6_gar.glb` (accepted v6, back-face pass already applied and marked); keyed copy
  `export/mm6_gar.glb`, installed with `tools/install_model.py` (source and runtime copy).
- The previous `assets_source/worlds/mm6/models/mm6_gar.glb` was stale (an older single-material 14,497 + 6,541
  model); it is replaced by the keyed v6.
- Rollback: `work/pre_swap/mm6_gar_runtime_v6.glb` (previous runtime copy, identical to the Codex export) and
  `work/pre_swap/mm6_gar_source_stale.glb` (previous source).
- `mm6_gargoyle_actor_model_tiers_clips_and_rubble` now also asserts the swap at seven clip times (body/rubble node
  matrices visible or singular as in the table): passes.

Other MM6 models (scan of every `assets_dev/worlds/mm6/models` creature, 2026-10-14): no other mesh swap. The Wyrm's
remains prop sits on a socket scaled to exactly 0 while alive (already skipped); burning deaths stop drawing the
body once the burn ends; the elementals, Robot, Sea Serpent and Water Elemental foam shrink away on death but leave
no corpse, so their models leave with the actor.

## Staged, not adopted: texture-aware reduction

RETOPOLOGY_PLAYBOOK.md default route, no Meshy. Kept for reference; the user chose to keep the 7k body.

Body ladder (`work/selection.json`, `review/ladder_sheet.png`), limits scaled to 2.94 m (p99 8.8 mm, max 44 mm):

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| r70 | 5,071 | 2.8 / 8.9 | 0.997 | 0.996 | pass |
| r55 | 3,985 | 3.9 / 19.2 | 0.993 | 0.996 | pass |
| r45 | 3,261 | 5.8 / 28.3 | 0.990 | 0.995 | pass, visual pick |
| r35 | 2,535 | 8.1 / 29.6 | 0.982 | 0.993 | pass, auto-pick; snout and jaw blocky |
| r30 | 2,173 | 9.3 / 34.8 | 0.971 | 0.991 | fail |

Head close-ups `review/close/sheet4_head.png` (rows r100 / r55 / r45 / r35). Rubble ladder in `rubble/`: no step
passes the automatic gate (the silhouette IoU of 36 small stones drops quickly) while all 36 pieces survive; r30
(1,961) matches the source in `review/close/sheet_death.png`. Built result (no swap keys):
`export/mm6_gar_reduced_r45_r30.glb`, body 3,261 / 1,628 / 584 / 194, rubble 1,961 / 977 / 330 / 199; viewer
`review/viewer/` (installed vs r45, 30 loads pass `check_viewer.mjs`).
