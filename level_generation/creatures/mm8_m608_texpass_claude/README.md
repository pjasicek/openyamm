# MM8 Juggernaut texture quality pass (`mm8_m608`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm8:m608` (token in `work/token.txt`). Production [mm8_m608_codex](../mm8_m608_codex/README.md), reduction
[mm8_m608_reduce_claude](../mm8_m608_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas at 30.7 % (801 islands, 11.6 % fragments, stretch 1.57).

**Structure.** The body's LOD2 and LOD3 and the death debris (`BandShard` with `Rubble_LOD1`–`3`) all draw with the
body material and their own UVs into the old atlas. All six are `uv_followers`: each triangle is mapped through the
old-layout LOD0 triangle under its UV centroid into the new layout. `tp_apply.py` now skips the far-LOD map refill when
a far LOD shares the atlas material (it would have overwritten the LOD0 images). The eyes and flash are untextured
and unchanged.

**Route.** Head set = old atlas u > 0.5 (8.6 %) x1.8. Layout **`work/uv_fine_fixed.npz`** (fast packer: 61.8 %, 1.1 %
fragments, stretch 1.19, no overlap). Retexture with the production masters (`mm8_m608_codex/references_hd/01`–`04`),
meshy-7, 4K: **10 credits**; no head paint (the stone head reads from the body paint at x1.8; only front and back head
views exist). Tone per region with mean pinning; paint normals at the approved strength.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 30.7 % of 2080x1024 | **61.8 %** of 2048² |
| Equivalent square | 1,153 px | 1,610 px |
| Density p50 | 371 | 908 |
| Islands / fragments | 801 / 11.6 % | 208 / 1.1 % |
| Stretch p90 | 1.57 | 1.19 |

Tiers within 0.5 levels. Colour error against LOD0 at the same surface points: LOD1 mean 10.4 -> 10.1, LOD2 15.7 ->
18.6, LOD3 18.9 -> 21.0 (`tp_lodn_check.py`; the followers sample the sharper paint through the coarse triangles).

## Checks

`tp_diff.py` OK; winding 0; viewer check 0 console errors; floor audit Juggernaut A/B/C ok; motion audit re-run;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png)
(head, body, back, the Dead pose with debris): stone cracks crisper; the rollers' tile cracks are softer than before.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m608.glb`.

## Far-LOD follow-up (2026-11-11, same day)

LOD2 and LOD3 reinstalled with `uv_followers` in the new `3d` mode (projected from the new LOD0 charts, as LOD1); the
debris meshes keep the UV remap (they are displaced pieces, not in bind space). Colour error against LOD0: LOD2 18.6 ->
**15.3** (before the pass 15.7), LOD3 21.0 -> **18.4** (18.9). `tp_diff.py` OK, winding 0, regression PASS, floor ok.
The pre-follow-up install is `work/installed_r1.glb`.
