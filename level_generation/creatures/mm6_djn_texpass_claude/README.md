# MM6 BGenie texture quality pass (`mm6_djn`, Genie A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:djn` (token in `work/token.txt`). Production [mm6_djn_claude](../mm6_djn_claude/README.md), reduction and
body retexture [mm6_djn_reduce_claude](../mm6_djn_reduce_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas (two 1K sets) at 26.9 % (970 islands, 10.4 % fragments, stretch p90 4.61).
The user accepted the left-forearm bracer (`GoldBracer`) texture "for now" at install (blotchy, low resolution); the
brief asks to fix it here.

**Route.** Head set = old atlas u > 0.5 (5.1 % of the surface) x1.8, hands and gold jewellery x1.3. Layout
**`work/uv_fine_fixed.npz`** (fast packer, 52.6 %, 0.1 % fragments, no overlap). Retextures with the production
masters (body `references_hd/01`–`04`; head `references_head/00_front, 01_three_quarter, 03_back, 02_left`), meshy-7,
4K: **20 credits**.

Compose, with two new kit options:
- **`fresh_bones: ["^GoldBracer$"]`**: texels of faces weighted to the bracer bone keep the new paint after the tone
  curves, without the approved low-frequency colour, so the rejected bracer paint is replaced by the 4K paint's
  engraved gold and gems (108k texels). Close-ups in the head sheet, rows `br` and `bo`.
- **`keep_eyes`** with `rule "(R>G+10)&(G>B+5)&(R>50)"`, `max_texels 3000`: the head paint drew grey-blue irises and
  a silver ear stud; the approved brown eyes and gold earrings are kept (seven groups: two eyes, a lid corner, four
  earrings; the brown topknot group of 9,420 texels is excluded by max_texels).
Paint normals at the approved strength (p90 tilt 0.20; shaded normals p50 1.4°, p90 7.4°: the bracer's new relief).

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 26.9 % of 2080x1024 | **52.6 %** of 2048² |
| Equivalent square | 1,080 px | 1,485 px |
| Density p50 | 523 | 1,189 (head x1.8) |
| Islands / fragments | 970 / 10.4 % | 186 / 0.1 % |
| Stretch p90 | 4.61 | 1.18 |

Tiers: skin within 0.2 levels in A/B/C, the dark region (beard/brows) within 1.4, the rest (gold, vortex, hair) 1.5
darker. LOD1 colour error mean 6.2 -> 7.1, p99 57 -> 80 (the bracer's new high-contrast engraving at LOD1).

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit BGenie A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheets:
[review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4 with eyes and earrings as installed;
bracer front and outside), [review/texpass_body_sheet.png](review/texpass_body_sheet.png). The beard reads slightly
blue-black in tier A (paint detail tinted by the dark region); the right-wrist bracelet that floats off the hand in
Death is a clip/weight issue, not changed here.

Installed 2026-11-11. Rollback `work/before_texpass/mm6_djn.glb`.
