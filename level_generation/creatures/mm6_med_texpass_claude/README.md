# MM6 Medusa texture quality pass (`mm6_med`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:med` (token in `work/token.txt`). Production [mm6_med_claude](../mm6_med_claude/README.md), reduction
[mm6_med_reduce_claude](../mm6_med_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas (two 1K sets) at 25.9 % with 1,860 islands, 20.0 % fragments, stretch 1.99,
density spread 4.13.

**Route.** Head set = old atlas u > 0.5 (face and snake hair, 27.9 % of the surface) x1.8, hands x1.3. Layout
**`work/uv_fine_fixed.npz`** (fast packer: 56.0 %, 0.5 % fragments, stretch 1.10, no overlap). Retextures with the
production masters (body `references_hd/01`–`04`; head `references_head/00_front, 01_three_quarter, 03_back, 02_left`),
meshy-7, 4K: **20 credits**. Tone per region with mean pinning; paint normals at the approved strength (p90 0.08).
The yellow eyes came through the tone match unchanged (checked close up), so no eye keep was needed.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 25.9 % of 2080x1024 | **56.0 %** of 2048² |
| Equivalent square | 1,059 px | 1,532 px |
| Density p50 | 559 | 1,393 (head x1.8: p90 2,487) |
| Islands / fragments | 1,860 / 20.0 % | 314 / 0.5 % |
| Stretch p90 | 1.99 | 1.10 |
| Spread | 4.13 | 1.90 |

Tiers within 0.6 levels per region in A/B/C. LOD1 colour error mean 4.8 -> 2.7, p99 52.8 -> 28.3.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
face (eyes, lips, cheek scales) as installed and sharper, snake heads crisper, tail pattern unchanged.

Installed 2026-11-11. Rollback `work/before_texpass/mm6_med.glb`.
