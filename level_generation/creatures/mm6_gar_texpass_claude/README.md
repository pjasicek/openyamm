# MM6 BGargoyle texture quality pass (`mm6_gar`, Gargoyle A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:gar` (token in `work/token.txt`). Production [mm6_gar_codex](../mm6_gar_codex/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** Three 1K part sets (4K Meshy returns reduced to 1K): body 28.7 % (15.7 % fragments), head 31.9 % (13.3 %,
stretch 1.88), wings 41.8 % (28.7 % fragments).

**Route.** All three LOD0 primitives (body, head `head_prims` x1.8, wings) in one 2048 atlas, **`work/uv_fine_fixed.npz`**
(fast packer: 53.7 %, 0.4 % fragments, stretch 1.16, no overlap). One 2K replaces three 1K sets with about three times
the texels. Retextures with the production masters (body+wings `references_hd/01`–`04`, head `references_head/01`–`04`),
meshy-7, 4K: **20 credits**. Head and wings materials point at the atlas; each keeps its own ramps and reads its own
mask carried onto the layout.

**The Rubble (death remains) shares the body/head/wings materials** (and `Rubble_LOD1`–`3` the head material) with
their own UVs into the old sets. New kit option `uv_followers`: each Rubble triangle takes the old-layout LOD0 triangle
under its UV centroid and maps its corners through that triangle's old -> new UV affine map, so it samples the same
paint in the new atlas (6,545 + 1,370 triangles). The other Rubble LOD materials keep the old images (they are still
used), so the GLB keeps those three 1K sets.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | body 28.7 %, head 31.9 %, wings 41.8 % of three 1K sets | **53.7 %** of one 2048² |
| Equivalent square | 549 / 578 / 662 px | 1,501 px |
| Density p50 (body) | 669 | 1,727 (head x1.8) |
| Fragments | 15.7 / 13.3 / 28.7 % | 0.4 % |
| Stretch p90 | 1.39 / 1.88 / 1.40 | 1.16 |

Tiers within 1.4 levels per class in A/B/C. LOD1 colour error body 3.0 -> 2.5, head 9.9 -> 4.0, wings 15.8 -> 15.3.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit BGargoyle A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet
[review/texpass_sheet.png](review/texpass_sheet.png): head front/3/4 (stone cracks and pits crisper, eyes unchanged),
body, back, and the Dead pose with the Rubble (same look as installed).

Installed 2026-11-11. Rollback `work/before_texpass/mm6_gar.glb`.
