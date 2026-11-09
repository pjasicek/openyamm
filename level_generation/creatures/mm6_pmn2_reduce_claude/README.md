# MM6 Mage (PeasantM2 A/B/C, boss tier D) reduction (2026-10-13)

User: optimise the New Sorpigal goblin, female/male peasant, guard and mage. `../reduce_installed.sh pmn2 Mage "<title>"`
(texture-aware reduction of the installed `assets_source/worlds/mm6/models/mm6_pmn2.glb`, no retexture). Limits scaled to
the model's height: p99 5.08 mm, max 25.39 mm. Pick r55: auto-pick.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 10,403 | | | | |
| 70 % | 7,281 | 3.29 / 15.33 | 0.9963 | 0.9965 | pass |
| 55 % | 5,721 | 4.7 / 16.99 | 0.9933 | 0.9946 | **pick** |
| 45 % | 4,681 | 6.13 / 20.25 | 0.9899 | 0.9925 | fail |
| 40 % | 4,161 | 7.05 / 28.81 | 0.9878 | 0.9909 | fail |
| 35 % | 3,641 | 8.36 / 28.31 | 0.9853 | 0.9887 | fail |
| 30 % | 3,119 | 9.63 / 37.32 | 0.9829 | 0.9862 | fail |
| 25 % | 2,599 | 11.6 / 36.5 | 0.978 | 0.9826 | fail |

`export/mm6_pmn2.glb`: LODs 5,721 / 2,860 / 1,027 / 339, variants carried to every LOD and shadow mesh.
Viewer `review/viewer/` (installed vs pick, every variant and clip; passes `check_viewer.mjs`), close renders
`review/close/sheet_*.png`. Not installed yet.

## Installed (2026-10-13)

User: "ok". Installed `export/` model; previous source in `work/` (`*_source_pre_reduce.glb`). The model's
`*_actor_models_bind_*` regression fails with the same message on the pre-reduction model (verified by reinstalling
it temporarily), so the failure predates this change; the material/variant lists are identical before and after.

## Floor fix — 2026-10-21

`--ground-loop Walking`. Before, in world units at tier A: walking lifts every foot by +4.4.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_pmn2.glb`), written to `export/mm6_pmn2_floor.glb` and installed as `mm6_pmn2.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31)

`mm6_pmn2.glb` gained a `Jog` (Mixamo Running (5) legs, staff carry and arms from Running) for the fleeing chase
(2.65 units/s), which played the walk at x2.02. Binding: `run: Jog`, `run_stride_length: 1.87`. Details, gates and
rebuild: [package h04](../gait_rollout_20261031/h04/README.md) (`scripts/rebuild.sh pmn2`). A re-export, floor fix or
far-LOD repair rerun must re-graft this clip (rerun the h04 rebuild on the new source).
