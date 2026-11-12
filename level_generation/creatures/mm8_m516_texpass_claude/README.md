# MM8 Thunder Lizard texture quality pass (`mm8_m516`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm8:m516` (token in `work/token.txt`). Production [mm8_m516_claude](../mm8_m516_claude/README.md), reduction
[mm8_m516_reduce_claude](../mm8_m516_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas at 31.9 % (1,570 islands, 18.7 % fragments, stretch 1.76). LOD2 and LOD3
draw with the body material and their own UVs into that atlas.

**Route.** Head set = old atlas u > 0.5 (head, neck and frill, 26.2 % of the surface) x1.8. Layout
**`work/uv_fine_fixed.npz`** (fast packer: 55.6 %, 1.6 % fragments, stretch 1.19, no overlap). LOD2 and LOD3 are
`uv_followers` (remapped through the old layout). Retextures with the production masters (body `references_hd/01`–`04`;
head `references_head/front, left, back, right`), meshy-7, 4K: **20 credits**. **Eyes**: the head paint put the pupils
off-centre; the approved eyes are kept with `keep_eyes` rule `M3>0.5` (the eye region of the tier mask; kit option:
rules may now read the mask channels M0–M3). Tone per region with mean pinning; paint normals at the approved strength.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 31.9 % of 2080x1024 | **55.6 %** of 2048² |
| Equivalent square | 1,175 px | 1,527 px |
| Density p50 | 1,100 | 1,793 (head x1.8: p90 3,211) |
| Islands / fragments | 1,570 / 18.7 % | 346 / 1.6 % |
| Stretch p90 | 1.76 | 1.19 |

Tiers within 1.6 levels on body, belly and frill; the eye region 7 levels in green before the eye keep (kept as
installed now). Colour error against LOD0: LOD1 6.6 -> 5.7, LOD2 12.3 -> 17.6, LOD3 16.8 -> 21.8 (followers through
the coarse far triangles; far LODs only).

## Checks

`tp_diff.py` OK; winding 0; viewer check 0 console errors; floor audit Thunder Lizard A/B/C ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
head scales and frill crisper, eyes as installed.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m516.glb`.

## Far-LOD follow-up (2026-11-11, same day)

LOD2 and LOD3 reinstalled with `uv_followers` in the new `3d` mode (projected from the new LOD0 charts in bind space,
as LOD1) instead of the UV remap: colour error against LOD0 LOD2 17.6 -> **12.0** (installed before the pass: 12.3),
LOD3 21.8 -> **16.3** (16.8). LOD0/LOD1 unchanged; `tp_diff.py` OK, winding 0, regression PASS, floor ok. The
pre-follow-up install is `work/installed_r1.glb`.
