# MM6 SeaSerpent texture quality pass (`mm6_seas`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references of the
serpent changed; the foam ring card is untouched. Lease `mm6:seas` (token in `work/token.txt`). Production
[mm6_seas_claude](../mm6_seas_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** The 2K Meshy paint baked onto a fresh unwrap with 1,712 islands: 29.1 % atlas, 30.9 % of the surface on
fragments, stretch p90 1.75.

**Layouts** (head bone x1.8, 16 % of the surface): `uv_fine` (fast packer) 57.5 %, 7.1 % fragments, stretch 1.90;
`uv_v2` (cut_closed, max_stretch 1.8, merge_below 20) 57.3 %, 9.4 %, 1.31; **`uv_v3_fixed`** (max_stretch 2.2,
retry 3.5, merge_below 40, max_cost 3) 57.7 %, 8.0 %, 1.36: **the paid layout**. The remaining fragments sit on the
dense dorsal spikes and fins of the one-piece mesh; accepted over the 5 % target against 30.9 % before.

Retexture with the production masters (`references_hd/01`–`04`), meshy-7, 4K: **10 credits**. No head paint (no head
masters). The approved normal (p90 tilt 0.59, a bake) kept plus the paint's detail x0.5 (shaded normals p50 0.6°,
p90 1.9°). Tone per region with mean pinning.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 29.1 % | **57.7 %** |
| Equivalent square | 1,105 px | 1,556 px |
| Density p50 | 1,064 | 1,248 (head x1.8: p90 2,232) |
| Islands / fragments | 1,712 / 30.9 % | 575 / 8.0 % |
| Stretch p90 | 1.75 | 1.36 |

Tiers within 1.5 levels for the three regions in A/B/C; the unmasked bright parts (teeth, spikes, 7.6 %) 4.4 levels
darker in red. LOD1 colour error mean 7.0 -> 9.3 (sharper paint against the coarser LOD1).

## Checks

`tp_diff.py` OK; winding 0; viewer check 0 console errors; floor audit SeaSerpent A/B/C ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheets [review/texpass_sheet.png](review/texpass_sheet.png),
[review/texpass_face_sheet.png](review/texpass_face_sheet.png) (A and C head close-ups): scales crisp; the dark mottling
is softer than the old paint's blotches.

Installed 2026-11-11. Rollback `work/before_texpass/mm6_seas.glb`.
