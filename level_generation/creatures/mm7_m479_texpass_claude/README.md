# MM7 Treant texture quality pass (`mm7_m479`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm7:m479` (token in `work/token.txt`). Production [mm7_m479_claude](../mm7_m479_claude/README.md), reduction
[mm7_m479_reduce_claude](../mm7_m479_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** One 2K set at 33.0 % (1,479 islands, 20.4 % fragments, stretch p90 2.38, spread 2.51). No tiers (all three
share the palette); LOD2 and LOD3 have their own maps.

**Route.** Mouth, jaw, teeth and eye bones x1.8 (3.3 % of the surface). Layout **`work/uv_v2_fixed.npz`**
(`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`: 49.2 %, 1.7 % fragments, stretch
1.26, no overlap; the fast packer alone gave 48.3 %). 121 separate pieces (branches, roots) keep the atlas under 50 %.
Retexture with the production masters (`references_hd/01`–`04`), meshy-7, 4K: **10 credits**. Tone with mean pinning;
paint normals at the approved strength. New kit option `keep_bones: ["^Eye_"]`: the two eye knots keep their approved
colour and relief (8,003 texels); they still read as smoother ovals beside the now sharper bark (they were smooth in the
approved paint too, hidden by the blur around them). The kit's viewer script now handles GLBs without tier variants.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 33.0 % | **49.2 %** |
| Equivalent square | 1,177 px | 1,436 px |
| Density p50 | 511 | 712 |
| Islands / fragments | 1,479 / 20.4 % | 478 / 1.7 % |
| Stretch p90 | 2.38 | 1.26 |
| Spread | 2.51 | 1.09 |

Mean colour pinned to the approved (81.2/64.1/46.4). LOD1 colour error mean 10.4 -> 9.7. Shaded normals p50 2.4°, p90
6.1° from the installed ones (the paint's bark relief).

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Treant A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheets
[review/texpass_sheet.png](review/texpass_sheet.png) (eye level, 3/4, back), [review/texpass_face_sheet.png](review/texpass_face_sheet.png)
(mouth): bark grooves and moss crisp where the installed bark was smeared.

Installed 2026-11-11. Rollback `work/before_texpass/mm7_m479.glb`.
