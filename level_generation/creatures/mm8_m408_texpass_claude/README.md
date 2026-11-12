# MM8 Couatl texture quality pass (`mm8_m408`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm8:m408` (token in `work/token.txt`). Production [mm8_m408_claude](../mm8_m408_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** One 2K set at 33.5 % (731 islands, 6.5 % fragments, stretch p90 1.49).

**Route.** Head, crest and jaw x1.8 (24.4 % of the surface). Layout **`work/uv_v2_fixed.npz`** (`cut_closed=1
max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`, collapsed slivers re-laid, upload by `tp_upload.py`:
58.6 %, 0.4 % fragments, stretch 1.14, no overlap). Retexture with the production masters (`references_hd/01`–`04`),
meshy-7, 4K: **10 credits**; no head paint (no head masters). Tone per region (four ramps) with mean pinning; paint
normals at the approved strength. The cartoon eyes came through unchanged.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 33.5 % | **58.6 %** |
| Equivalent square | 1,186 px | 1,567 px |
| Density p50 | 1,077 | 1,329 (head x1.8: p90 2,382) |
| Islands / fragments | 731 / 6.5 % | 184 / 0.4 % |
| Stretch p90 | 1.49 | 1.14 |

Tiers within 2 levels per region in A/B/C. LOD1 colour error mean 6.4 -> 5.1.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Couatl A/B/C ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
head scales and feather barbs crisper, the rainbow bands and eyes as installed.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m408.glb`.
