# MM8 Triton texture quality pass (`mm8_m576`, Triton A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm8:m576` (token in `work/token.txt`). Production [mm8_m576_claude](../mm8_m576_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 4096x2048 body | head atlas at 24.6 % (685 islands, 6.6 % fragments, stretch p90 2.12, spread 2.30).
The creature cook caps colour at 2048, so in game this was a 2048x1024 atlas: about 1,000 px equivalent.

**Route.** Head set = old atlas u > 0.5 (10.5 % of the surface) x1.8, hands x1.3. Layout **`work/uv_fine_fixed.npz`**
(fast packer, 52.5 %, 0.4 % fragments, no overlap; `uv_v2` with cut_closed gave 51.5 %). Retextures with the
production masters (body `references_hd/01`–`04`; head `references_head/01_front, 03_left, 02_back, 00_three_quarter`
as the production head job), meshy-7, 4K: **20 credits**. Approved relief normal kept (a rebake) plus the paint's
detail x0.5 (`tp_normal_check.py`: p50 0.9°, p90 3.8°). **Eyes**: the head paint drew paler green eyes; the approved
yellow-green eyes are kept (`keep_eyes` with `rule "(R>80)&(G>100)&(B<0.6*G)"` on the approved colour, radius + 3 mm,
two groups of 186/166 texels, 9–10 mm). Tone per region with mean pinning.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 24.6 % of 4096x2048 (cooked 2048x1024) | **52.5 %** of 2048² |
| Equivalent square (in game) | about 1,016 px | 1,484 px |
| Islands / fragments | 685 / 6.6 % | 176 / 0.4 % |
| Stretch p90 | 2.12 | 1.17 |
| Spread | 2.30 | 1.38 (head x1.8) |

Tiers within 1 level per region (A skin 41.8/88.6/80.3 -> 42.2/89.4/80.9). LOD1 colour error mean 12.9 -> 6.7, p99
107 -> 66.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Triton A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheets:
[review/texpass_head_sheet.png](review/texpass_head_sheet.png) (front, 3/4, eye close-up: eyes as installed, scales
crisper), [review/texpass_body_sheet.png](review/texpass_body_sheet.png).

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m576.glb`.
