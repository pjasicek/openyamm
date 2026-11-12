# MM6 Skeleton texture quality pass (`mm6_ske`, Skeleton A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:ske` (token in `work/token.txt`). Production [mm6_ske_claude](../mm6_ske_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | skull atlas (two 1K sets) at 33.1 % with 1,571 islands, 42.5 % of the surface on
fragments (the body is 110 separate bone pieces), stretch p90 1.87, density spread 5.43.

**Route.** Skull set = old atlas u > 0.5 (12.5 % of the surface) x1.8, hands x1.3. Layout **`work/uv_v2_fixed.npz`**
(`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`: 55.8 %, 4.5 % fragments, no
overlap). Retextures with the production masters (body `references_hd/01`–`04`; skull `references_head/01_front,
02_left, 00_three_quarter`: the production head job also named `03_back` and `04_right`, which are no longer in
`mm6_ske_claude/references_head/`), meshy-7, 4K: **20 credits**. One bone region (tiered); the red eye glow is outside
the mask and was pinned back to its approved colour. Paint normals at the approved strength.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 33.1 % of 2080x1024 | **55.8 %** of 2048² |
| Equivalent square | 1,197 px | 1,530 px |
| Density p50 | 720 | 2,155 (skull x1.8) |
| Islands / fragments | 1,571 / 42.5 % | 554 / 4.5 % |
| Stretch p90 | 1.87 | 1.33 |
| Spread | 5.43 | 1.81 |

Tiers: bone within 2 levels in A/B/C, eye glow within 3. LOD1 colour error mean 6.9 -> 8.3.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Skeleton A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet
[review/texpass_sheet.png](review/texpass_sheet.png): skull, teeth and bones as installed with finer pores; red eyes
unchanged.

Installed 2026-11-11. Rollback `work/before_texpass/mm6_ske.glb`.
