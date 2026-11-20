# MM6 Cockatrice texture quality pass (`mm6_ckt`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:ckt` (token in `work/token.txt`). Production [mm6_ckt_claude](../mm6_ckt_claude/README.md). Kit:
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** A 1K body set (Meshy 2K downsampled) at 22.0 % (752 islands, 14.4 % fragments, stretch 1.91) beside a
separate 1K head set (59.5 %, 21.9 % fragments).

**Route.** Body (primitive 0) and head (primitive 1, `head_prims`, x1.8) in one 2048 atlas: **`work/uv_v2_fixed.npz`**
(`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`; collapsed slivers re-laid by
`tp_fix_collapsed.py`; uploads written by `tp_upload.py`), 61.6 %, no overlap. Retextures with the production masters,
body (`references_hd/01`–`04`) and head (`references_head/00_front, 02_left, 03_back, 04_right`), meshy-7, 4K:
**20 credits**. The head material keeps no region mask (the head is the same in every tier); both materials now read
the one atlas. Tone per class with mean pinning, paint normals at the approved strength (p90 tilt 0.15), LOD1
projected, LOD2/LOD3 maps refilled per primitive.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | body 22.0 % of 1K + head 59.5 % of 1K | **61.6 %** of one 2048² (body and head) |
| Equivalent square | body 480 px, head 790 px | 1,607 px |
| Density p50 (body) | 654 | 1,999 (head x1.8) |
| Fragments | 14.4 % / 21.9 % | 5.1 % (1.3 % on separate pieces under 8 triangles: spikes) |
| Stretch p90 | 1.91 / 1.42 | 1.19 |

Tiers within 2 levels for the membrane and wing regions (B 6.2/155.6/109.1 -> 8.2/155.8/109.9), the untiered feathers
within 3.3 levels (158.0 -> 154.7 red), head unchanged (199.7/119.8/86.4 -> 199.5/119.8/86.4). LOD1 colour error body
mean 12.7 -> 12.0, head 3.7 -> 2.0.

## Checks

`tp_diff.py` OK; winding 0; flat 0.01/0.00; viewer check 0 console errors; floor audit Cockatrice A/B/C ok; motion
audit re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet
[review/texpass_sheet.png](review/texpass_sheet.png): membrane scales and the neck's quill feathers sharper, red eyes
and beak unchanged.

Installed 2026-11-11. Rollback `work/before_texpass/mm6_ckt.glb`.
