# MM8 Necromancer texture quality pass (`mm8_m472`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed
(clips, including the animation stream's robe fixes, are the installed ones). Lease `mm8:m472` (token in
`work/token.txt`). Production [mm8_m472_claude](../mm8_m472_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas at 29.9 % with 1,627 islands, 19.2 % fragments, stretch p90 2.70, density
spread 6.93.

**Route.** Head set = old atlas u > 0.5 (12.8 %) x1.8, hands x1.3. Layout **`work/uv_fine_fixed.npz`** (fast packer:
55.1 %, 0.5 % fragments, stretch 1.17, no overlap). Retextures with the production masters (body `references_hd/01`–`04`;
head `references_head/01_front, 00_three_quarter, 03_left, 02_back`), meshy-7, 4K: **20 credits**.

Compose options: **`head_detail: 0.3`** (new kit option): the head paint drew a scaly crackle over the pale undead
face that the installed face does not have, so the paint's fine detail is scaled to 0.3 on the head set (the hair
keeps most of its new strand detail through the approved low-frequency colour); **`keep_eyes`** with
`rule "(G>R+40)&(G>100)"` (the green base of the tiered eye glow; 500 and 469 texels): the glow had smeared onto the
lids. Paint normals at the approved strength (p90 0.08).

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 29.9 % of 2080x1024 | **55.1 %** of 2048² |
| Equivalent square | 1,136 px | 1,520 px |
| Density p50 | 589 | 1,327 (head x1.8) |
| Islands / fragments | 1,627 / 19.2 % | 226 / 0.5 % |
| Stretch p90 | 2.70 | 1.17 |
| Spread | 6.93 | 1.79 |

Tiers: glow region within 1.4 levels, the rest (robe, skin, hair) 2 levels lighter. LOD1 colour error mean 6.8 -> 5.3.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Necromancer A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
face and eyes as installed (a faint skin texture from the paint's normal remains), hair strands, chest plate and robe
sigils crisper.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m472.glb`.
