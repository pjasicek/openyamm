# MM6 Hydra (`hyd`, BHydra A/B/C) reduction (installed 2026-10-14)

User: "do hydra" (next candidate after the triangle survey). RETOPOLOGY_PLAYBOOK.md default route, no-rebuild branch:
`../reduce_installed.sh hyd Hydra "MM6 Hydra"` on the installed `assets_source/worlds/mm6/models/mm6_hyd.glb`
(source matches the runtime copy apart from the install back-face pass). No Meshy.

## Ladder

Limits scaled to the 1.28 m model (p99 3.8 mm, max 19.2 mm). The weld leaves 325 open edges (48 separate pieces:
teeth, horns, spines); every step keeps all 48, the smallest becoming 4-triangle points.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| r70 | 12,328 | 3.0 / 18.2 | 0.994 | 0.993 | pass (auto-pick) |
| r55 | 9,686 | 4.2 / 21.2 | 0.990 | 0.990 | fail (narrowly) |
| **r45** | **7,926** | 5.4 / 21.4 | 0.985 | 0.987 | fail, **picked (visual)** |
| r40 | 7,044 | 5.9 / 24.4 | 0.983 | 0.985 | fail |
| r35 | 6,164 | 7.0 / 57.3 | 0.980 | 0.981 | fail; blue head crest jagged |

Head close-ups (`scripts/head_views.py`, Standing frame 0): `review/close/heads_side.png` and `heads_q34.png`, rows
r100 / r55 / r45 / r40 / r35, columns heads 1-5. r55 matches the source; r45 keeps every face, tooth row and horn
with small shading changes (purple nostrils, blue head spines); r35 roughens the blue head's crest. The white specks on
the red and blue heads are in the source too.

## Result

`export/mm6_hyd.glb`: LODs **7,926 / 3,951 / 1,398 / 476** (installed 17,614 / 8,801 / 3,151 / 1,022). Textures,
variants (carried to every LOD/shadow primitive), clips and sockets unchanged; no collapsed meshes
(`tools/model_hide_collapsed_meshes.py`). Viewer `review/viewer/` (installed vs r45, A/B/C, all clips):
`check_viewer.mjs` 42 loads, no errors.

## Installed

User accepted r45 (2026-10-14). Previous source backed up to `work/mm6_hyd_source_pre_reduce.glb`; installed with
`tools/install_model.py` (runtime back-face pass: 475 back copies). `mm6_hydra_actor_model_tiers_follow_sprite_scales`
passes. Ledger row added.
