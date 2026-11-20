# MM6 LizardArch texture quality pass (`mm6_lzd`, LizardArch A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md) and
[texpass_mm678/HANDOFF.md](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, images and texture references
changed. Lease `mm6:lzd` (token in `work/LEASE.txt`). Production: [mm6_lzd_codex](../mm6_lzd_codex/README.md),
reduction [mm6_lzd_reduce_claude](../mm6_lzd_reduce_claude/README.md), gait h06, lod_repair_claude. Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md) (`tp_*.py`, `texpass.json`).

## Texture quality pass (2026-11-11)

**Cause.** Body set 2048x1351 (body | head atlas, Codex rebake) at 17.2 % (726 islands, 13.7 % fragments, stretch
1.78); the skinned bowstring/arrow (`LizardBow_A`, 208 triangles) on its own 1K colour, mr, normal and mask images at
1.9 %.

**Route.**
1. Body (primitive 0) and bowstring/arrow (primitive 1) in one 2048 atlas (`atlas_prims [0, 1]`): the bow's own four
   1K images are dropped; its tier materials keep their own ramps and read the bow texels' carried mask.
   Head = B_Head, B_Neck (8.9 %) x1.8, hands x1.3. Layout **`work/uv_v2.npz`** (`cut_closed=1 max_stretch=1.8
   retry_stretch=3.0 merge_below=20 fine=250 steps=0`: 52.0 %, 2.3 % fragments; the fast packer `uv_fine` gave
   52.4 % with 3.1 %). Thin straps, quiver and bow pieces keep this under the 55 % aim.
2. Retextures with the production masters: body (`references_hd/01`–`04`) and head (`references_head/head_*`, the
   head turnaround the Meshy head was built from), meshy-7, 4K, our UVs: **20 credits**. Both kept the layout.
3. Approved relief normal carried onto the layout (p90 tilt 1.41, a Codex rebake) plus the paint's detail x0.5
   (`tp_normal_check.py` against the installed model: p50 0.7°, p90 3.0°, p99 6.7°).
4. **Eyes**: the head paint drew a dimmer brown iris at a slightly different place; the approved orange slit eyes
   are kept (`keep_eyes` in `texpass.json`: approved orange texels on head faces, grouped in 3D, approved colour within
   each eye's radius + 4 mm, feathered 4 mm; radii 13 and 21 mm). Close-ups in the head sheet, row `ec`.
5. Tone per class: tunic region 0 (the only ramp; the mask is RGB, so channels without a ramp are not regions — the
   kit now ignores them), the rest, and the bow primitive. LOD1 projected, LOD2/LOD3 maps refilled per primitive.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas, body | 17.2 % of 2048x1351 | **52.0 %** of 2048² (body and bowstring/arrow) |
| Bow set | own 1K set at 1.9 %, 83 % fragments | merged |
| Equivalent square | 850 px | 1,477 px |
| Density p50 | 440 | 1,262 |
| Islands / fragments | 726 / 13.7 % | 248 / 2.3 % |
| Stretch p90 | 1.78 | 1.19 |

Tiers (`tp_tier_tone.py`): tunic A/B/C within 0.3 levels (B 161.8/2.6/59.8 -> 161.8/2.5/59.7), skin and leather
84.1/80.6/46.0 -> 84.2/80.6/46.0, bow within 1 level. LOD1 colour error body mean 5.7 -> 6.0.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00 (both materials); viewer check 0 console errors; floor audit LizardArch A/B/C
  ok; motion audit re-run (`audit_after/`); `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install.
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (front, 3/4, eye close-up; eyes as
  installed, scales sharper, teeth now ivory from the paint instead of pinkish), [review/texpass_body_sheet.png](review/texpass_body_sheet.png).
- Not changed: clips (the Attack/Cast single clip belongs to the animation stream).

Installed 2026-11-11. Rollback: `work/before_texpass/mm6_lzd.glb` (actors.yml unchanged; copy in
`work/before_texpass/actors_entries.yml`).
