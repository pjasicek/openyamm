# MM6 Flying Drake (`drg1`, BDragonFly A/B/C) head unify + reduction (installed 2026-10-14)

User: "move on to the tris reduction for the flying drake ... but first, check the head graft vs body color ... unify it
before doing the reduction step."

## Head colour
The three texture sets share the hide ramps, but the grafted head's base colour in the hide region was darker and
more contrasty: linear luminance p10/50/90 0.011 / 0.036 / 0.106 against the body's 0.025 / 0.054 / 0.094, so every
tier's head and upper neck read deeper (blackish green / navy / maroon). `scripts/unify_head.py` quantile-matches the
head hide luminance to the body hide (after: 0.025 / 0.054 / 0.094), scaling each texel by matched/original
luminance weighted by its hide mask (hue and scale detail kept). Gold, ivory, eyes and the wings are unchanged.
`export/mm6_drg1_unified.glb`; close-ups `review/neck/sheet_compare.png` (rows: installed / unified per tier).

## Reduction
Same no-retexture route as the demons (`scripts/` copies, `REA_NODE=Body`), on the unified model. Weld 14,846 -> 675
open edges; limits scaled to the 2.78 m wingspan (p99 8.3 mm, max 41.7 mm).

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 14,488 | | | | |
| 70 % | 10,140 | 2.2 / 16.3 | 0.994 | 0.999 | pass |
| **55 %** | **7,968** | 3.5 / 16.3 | 0.987 | 0.999 | **auto-pick** |
| 45 % | 6,518 | 4.6 / 18.0 | 0.979 | 0.998 | fail (IoU) |
| 35 % | 5,070 | 6.5 / 22.5 | 0.968 | 0.997 | fail |

Build: export_cand -> swap_lod0 -> build_actor_lods -> `scripts/preserve_wing_lods.py` (every LOD keeps the LOD0 wing
membranes, as the original project does) -> the project's shrink_shadow_lods -> carry_variants: `export/mm6_drg1.glb`,
LODs 7,968 / 4,638 / 2,510 / 1,785 (installed 14,488 / 8,182 / 4,083 / 2,560), burn maps on all 9 materials.
Viewer `review/viewer/` (installed / unified / 55 % per tier, 81 loads pass); `review/neck/sheet_r55.png`,
`review/close/sheet_whole.png`. Installed 2026-10-14 with `tools/install_model.py`; previous source backed up to
`work/mm6_drg1_source_pre_reduce.glb` (rollback: install that file). Regressions
`mm6_flying_drake_actor_model_tiers_and_clips` and `mm6_drake_and_dragon_actor_model_burn_death` pass.
