# MM8 Ether Knight texture quality pass (`mm8_m604`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm8:m604` (token in `work/token.txt`). Production [mm8_m604_claude](../mm8_m604_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas at 30.5 % (874 islands, 9.4 % fragments, stretch p90 3.92, spread 3.69).

**Route.** Head set = old atlas u > 0.5 (8.2 %) x1.8, hands x1.3. Layout **`work/uv_fine_fixed.npz`** (fast packer:
56.5 %, 3.9 % fragments, stretch 1.20, no overlap). Retextures with the production masters (body
`references_hd/01`–`04`; head `references_hd/head_front, head_three_quarter, head_left, head_back`), meshy-7, 4K:
**20 credits**. Tone per region with mean pinning; paint normals at the approved strength (p90 0.10). The pale eyes
came through unchanged, no eye keep needed.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 30.5 % of 2080x1024 | **56.5 %** of 2048² |
| Equivalent square | 1,148 px | 1,539 px |
| Density p50 | 509 | 1,287 (head x1.8) |
| Islands / fragments | 874 / 9.4 % | 504 / 3.9 % |
| Stretch p90 | 3.92 | 1.20 |
| Spread | 3.69 | 1.42 |

Tiers within 2.5 levels per region in A/B/C. LOD1 colour error mean 10.3 -> 8.0.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Ether Knight A/B/C ok; motion
audit re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet
[review/texpass_sheet.png](review/texpass_sheet.png): the rotting face reads its wrinkles, sockets and teeth; cape,
belt and leg wraps crisper; tiers unchanged.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m604.glb`.
