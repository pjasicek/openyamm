# MM6 Demon (non-flying) reduction numbers (2026-10-13)

Numbers only, nothing installed, no Meshy. Source: installed `assets_source/worlds/mm6/models/mm6_demon.glb`
(Demon A/B/C share it), 1.69 m tall. The 624-triangle ash-remains mesh is excluded; the user will replace that
effect with a lizard-style death effect coloured per variant.

Scripts are the Fire Lizard pilot's (`../mm6_drag_reduce_claude/`) plus `import_source.py`: the GLB import is welded
(glTF splits vertices at every UV seam: 18,672 open edges -> 48 real ones; without the weld MeshLab cannot collapse
across seams and every step stalls at 13,976). `compare_ladder.py` scales its limits by `REA_HEIGHT_M=1.69`
(p99 5.1 mm, max 25.4 mm). Whole ladder: ~31 s.

| step | total | body | claws | iris+pupil | p99 / max mm | IoU min | SSIM | |
|---|---:|---:|---:|---:|---|---|---|---|
| source | 16,474 | 13,474 | 2,718 | 282 | | | | |
| 70 % | 11,530 | 9,387 | 1,957 | 186 | 1.8 / 13.2 | 0.995 | 0.994 | pass |
| **55 %** | **9,060** | 7,422 | 1,492 | 146 | 2.7 / 14.6 | 0.990 | 0.991 | **auto-pick** |
| 45 % | 7,412 | 6,069 | 1,213 | 130 | 3.4 / 19.3 | 0.979 | 0.987 | fail (IoU) |
| 40 % | 6,588 | 5,388 | 1,090 | 110 | 3.9 / 22.1 | 0.976 | 0.985 | fail (IoU) |
| 35 % | 5,764 | 4,733 | 931 | 100 | 4.4 / 22.1 | 0.973 | 0.983 | fail (IoU) |
| 30 % | 4,942 | 4,078 | 780 | 84 | 5.0 / 23.6 | 0.971 | 0.981 | fail (IoU) |
| 25 % | 4,118 | 3,393 | 645 | 80 | 5.9 / 23.6 | 0.965 | 0.977 | fail (IoU) |

45-30 % pass the surface limits; the silhouette check fails on the thin tail (`review/sil_diff.png`,
`review/tail_crop.png`): the inner corner of its bend fills in slightly. Claws are 2,718 triangles in the source,
the fix-small-parts candidate (simple cones, as the lizard's teeth).

## Auto-pick build (user: "just do auto-pick")

55 % (9,060 triangles) with the installed textures, variants, region ramps, clips, sockets and ash mesh unchanged:
no part rebuilt, so no retexture (UVs preserved by the texture-aware reduction), no Meshy.
`scripts/export_cand.py` (candidate + rig, 4 influences) -> `scripts/swap_lod0.py` (replaces the LOD0 primitives by
material name, checks bind space and node transform, drops old LOD/shadow meshes, compacts the buffer) ->
`tools/build_actor_lods.py --mesh-node Demon_Native_Mesh` -> `export/mm6_demon.glb`: LODs 9,060 / 4,512 / 1,623 / 552
(installed: 16,474 / 8,237 / 2,980 / 1,019); 20.2 MB vs 23.0 MB. About 10 s.
Viewer (`review/viewer/`, `scripts/viewer_variants.py` bakes each variant): installed vs 55 % for A/B/C, 60 loads
pass `check_viewer.mjs`. Close renders `review/close/sheet_*.png`: no visible difference. Not installed yet.

## Installed (2026-10-13)

User: "basically the same, install it". `scripts/carry_variants.py` restores the variant mappings on the rebuilt LOD
and shadow primitives (first install failed `mm6_demon_actor_models_variants_share_asset_and_native_stats`: lower
LODs had lost the per-variant iris). Installed from `export/mm6_demon.glb`; the previous source is kept at
`../mm6_demon_meshy_reference_20261004/pre_reduce/mm6_demon_source_pre_reduce.glb`. All five
`mm6_demon_actor_models*` regression cases pass. The ash-remains mesh is still in the model until its replacement.

## 25 % slower death (2026-10-13)

User: "make the disintegration / death anim ... 25% slower" for both demons. Burn `end` 0.75 -> 0.9375 s (gone at
~1.2 s); Death key times x1.25 (`../mm6_wdm_reduce_claude/scripts/hold_death.py export/mm6_demon_burn.glb
export/mm6_demon_burn_slow.glb 1.25 --time-scale 1.25`), installed as `mm6_demon.glb`. Demon regressions 5/5 pass.

## Gait rollout (2026-10-31)

Package [h06 of the gait rollout](../gait_rollout_20261031/h06/README.md) appended new locomotion clips (Walk2, Jog, Sprint) to
the installed `assets_source/worlds/mm6/models/mm6_demon.glb` (existing clips, meshes, skins and materials unchanged)
and installed it; the bindings are in `../gait_rollout_20261031/h06/bindings.yml`. Rebuild from the pre-gait copy:
`level_generation/creatures/gait_rollout_20261031/h06/scripts/rebuild.sh demon`. A far-LOD repair, head-bob or
reduction rerun on this model must re-graft these clips: copy the new source over
`../gait_rollout_20261031/h06/work/mm6_demon_pre_gait.glb`, rerun that rebuild and install its export.
