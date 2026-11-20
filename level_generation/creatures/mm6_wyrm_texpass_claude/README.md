# MM6 Wyrm texture quality pass (`mm6_wyrm`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:wyrm` (token in `work/token.txt`). Production [mm6_drr1_claude](../mm6_drr1_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2K body set at 36.6 % (8.0 % fragments) beside a 1K head set at 48.0 % (22.8 % fragments), each with a
burn map.

**Route.** Body (primitive 0) and head (primitive 1, x1.8) in one 2048 atlas, **`work/uv_fine_fixed.npz`** (fast
packer: 53.7 %, 1.3 % fragments, stretch 1.18, no overlap); the 1K head set is dropped and both materials keep their
own ramps. The two burn maps are carried into one new burn map on the atlas. Retextures: body with the production
masters (`references_hd/01`–`04`), head with `image_style_url references_hd/head_close.png` as the production head job,
meshy-7, 4K: **20 credits**. Tone with mean pinning; paint normals at the approved strength.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | body 36.6 % of 2K, head 48.0 % of 1K | **53.7 %** of one 2048² |
| Equivalent square | body 1,239 px, head 710 px | 1,500 px |
| Density p50 (body) | 2,122 | 2,442 |
| Fragments | 8.0 % / 22.8 % | 1.3 % |
| Stretch p90 | 1.40 / 1.46 | 1.18 |

Tiers within 1 level. LOD1 colour error body 6.2 -> 5.2, head 4.6 -> 3.9.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png).

Installed 2026-11-11. Rollback `work/before_texpass/mm6_wyrm.glb`.
