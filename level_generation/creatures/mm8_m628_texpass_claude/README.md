# MM8 Skeleton Archer texture quality pass (`mm8_m628`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references of the
body changed; the bow set (`SkeletonArcherBow_A`, own 1K set) is unchanged. Lease `mm8:m628` (token in
`work/token.txt`). Production [mm8_m628](../mm8_m628/README.md), reduction [mm8_m628_reduce_claude](../mm8_m628_reduce_claude/README.md).
Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas at 37.2 % (1,233 islands, 25.4 % fragments, stretch p90 2.17, spread 3.54).

**Route.** Head set = old atlas u > 0.5 (skull and hood, 12.1 %) x1.8, hands x1.3. Layout **`work/uv_v2_fixed.npz`**
(`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`: 57.6 %, 5.1 % fragments, stretch
1.31; 171 separate pieces: bones, straps, buckles). Retexture with the production masters (`mm8_m628/references_hd/01`–`04`),
meshy-7, 4K: **10 credits**; no head paint.

Compose: the body paint speckled the skull with dark pits; the head set uses two new kit options, **`head_sigma: 1.0`**
(the approved head colour is kept down to 1 texel, so the skull's cracks stay) and **`head_detail: 0.4`** (the
paint's fine detail at 0.4 on the head). The rest of the body (leather, cloth, bones) takes the new paint's detail.
The approved normal (material scale 0.7) is carried through the scale correctly.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 37.2 % of 2080x1024 | **57.6 %** of 2048² |
| Equivalent square | 1,268 px | 1,554 px |
| Density p50 | 624 | 1,307 (head x1.8) |
| Islands / fragments | 1,233 / 25.4 % | 778 / 5.1 % |
| Stretch p90 | 2.17 | 1.31 |
| Spread | 3.54 | 1.83 |

Tiers within 0.5 levels. LOD1 colour error mean 6.7 -> 5.9.

## Checks

`tp_diff.py` OK; winding 0; viewer check 0 console errors; floor audit Skeletons Archer A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
skull and hood as installed, vest, straps, trousers and bones crisper.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m628.glb`.
