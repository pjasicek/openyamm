# MM6 Cobra texture quality pass (`mm6_cob`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:cob` (token in `work/token.txt`). Production [mm6_cob_claude](../mm6_cob_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** The 2K Meshy paint baked onto a smart-project unwrap: 33.9 %, 1,474 islands, 14.8 % fragments.

**Route.** Head x1.8 (15.8 %). Layout **`work/uv_fine_fixed.npz`** (fast packer: 50.7 %, 0.2 % fragments, stretch
1.25, no overlap; the cut_closed variant gave 48.8 %). The one-piece, long thin body keeps the atlas near 50 %.
Retexture with the production masters (`references_hd/01`–`04`), meshy-7, 4K: **10 credits**.

**Compose at sigma 2, detail 0.6** (instead of 4 / 0.9): at the default the new paint's scale outlines drowned the
bold black hood spots of the approved paint; with the approved colour kept down to 2 texels and less paint detail the
spots stay and the scales gain relief (head sheet). The approved normal (p90 tilt 0.29) is replaced by the paint's
at full strength (scale 1.0, below the relief threshold).

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 33.9 % | **50.7 %** |
| Equivalent square | 1,192 px | 1,458 px |
| Density p50 | 2,384 | 2,548 (head x1.8: p90 4,537) |
| Islands / fragments | 1,474 / 14.8 % | 244 / 0.2 % |
| Stretch p90 | 1.18 | 1.25 |

Tiers within 1.5 levels on body and hood; the pale belly region (1.8 %) 6 levels darker. LOD1 colour error 5.9 -> 5.6.

## Checks

`tp_diff.py` OK; winding 0; viewer check 0 console errors; floor audit ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png).

Installed 2026-11-11. Rollback `work/before_texpass/mm6_cob.glb`.
