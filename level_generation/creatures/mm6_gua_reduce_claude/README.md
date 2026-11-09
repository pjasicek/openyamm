# MM6 Guard (Guard A/B/C) reduction (2026-10-13)

User: optimise the New Sorpigal goblin, female/male peasant, guard and mage. `../reduce_installed.sh gua Guard "<title>"`
(texture-aware reduction of the installed `assets_source/worlds/mm6/models/mm6_gua.glb`, no retexture). Limits scaled to
the model's height: p99 4.72 mm, max 23.58 mm. Pick r55: auto-pick.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 8,769 | | | | |
| 70 % | 6,137 | 2.7 / 14.29 | 0.9941 | 0.9955 | pass |
| 55 % | 4,821 | 4.14 / 14.82 | 0.9902 | 0.9915 | **pick** |
| 45 % | 3,945 | 5.73 / 20.3 | 0.9864 | 0.9873 | fail |
| 40 % | 3,507 | 6.51 / 20.3 | 0.982 | 0.9845 | fail |
| 35 % | 3,069 | 7.48 / 25.09 | 0.9798 | 0.981 | fail |
| 30 % | 2,629 | 9.17 / 27.86 | 0.9752 | 0.9764 | fail |
| 25 % | 2,191 | 10.87 / 45.4 | 0.9672 | 0.9694 | fail |

`export/mm6_gua.glb`: LODs 4,821 / 2,410 / 865 / 288, variants carried to every LOD and shadow mesh.
Viewer `review/viewer/` (installed vs pick, every variant and clip; passes `check_viewer.mjs`), close renders
`review/close/sheet_*.png`. Not installed yet.

## Installed (2026-10-13)

User: "ok". Installed `export/` model; previous source in `work/` (`*_source_pre_reduce.glb`). The model's
`*_actor_models_bind_*` regression fails with the same message on the pre-reduction model (verified by reinstalling
it temporarily), so the failure predates this change; the material/variant lists are identical before and after.

## Floor fix — 2026-10-21

`--ground-loop Walking`. Before, in world units at tier A: walking lifts every foot by +4.0.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_gua.glb`), written to `export/mm6_gua_floor.glb` and installed as `mm6_gua.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31)

Package [h06 of the gait rollout](../gait_rollout_20261031/h06/README.md) appended new locomotion clips (Jog, Sprint) to
the installed `assets_source/worlds/mm6/models/mm6_gua.glb` (existing clips, meshes, skins and materials unchanged)
and installed it; the bindings are in `../gait_rollout_20261031/h06/bindings.yml`. Rebuild from the pre-gait copy:
`level_generation/creatures/gait_rollout_20261031/h06/scripts/rebuild.sh gua`. A far-LOD repair, head-bob or
reduction rerun on this model must re-graft these clips: copy the new source over
`../gait_rollout_20261031/h06/work/mm6_gua_pre_gait.glb`, rerun that rebuild and install its export.
