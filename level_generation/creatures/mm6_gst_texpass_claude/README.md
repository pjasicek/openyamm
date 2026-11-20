# MM6 Ghost texture quality pass (`mm6_gst`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:gst` (token in `work/token.txt`). Production [mm6_gst_codex](../mm6_gst_codex/README.md), reduction
[mm6_gst_reduce_claude](../mm6_gst_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas at 32.4 % (985 islands, 8.2 % fragments, stretch p90 3.98, spread 3.41). The
material is unlit with shading baked into the colour; the eye domes are procedural.

**Route.** Head set = old atlas u > 0.5 (skull and hood, 15.8 %) x1.8, hands x1.3. Layout
**`work/uv_fine_fixed.npz`** (fast packer, collapsed charts re-laid: 52.9 %, 0.6 % fragments, stretch 1.15, no overlap;
uploads by `tp_upload.py`). Retextures with the production masters (body `references_hd/01`–`04`; head
`references_head/00_front, 01_three_quarter, 03_back, 02_left`), meshy-7, 4K: **20 credits**. The tone match keeps the
approved colour below 4 texels, so the baked shading holds; the procedural eye glow (region 2) is unchanged.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 32.4 % of 2080x1024 | **52.9 %** of 2048² |
| Equivalent square | 1,184 px | 1,489 px |
| Density p50 | 519 | 1,099 (head x1.8) |
| Islands / fragments | 985 / 8.2 % | 281 / 0.6 % |
| Stretch p90 | 3.98 | 1.15 |
| Spread | 3.41 | 1.82 |

Tiers within 0.3 levels. LOD1 colour error mean 3.7 -> 3.1.

## Checks

`tp_diff.py` OK; winding 0; flat 0.01; viewer check 0 console errors; floor audit ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
skull teeth and cracks, hood weave and stains crisper; eye glow and robe tiers as installed.

Installed 2026-11-11. Rollback `work/before_texpass/mm6_gst.glb`.
