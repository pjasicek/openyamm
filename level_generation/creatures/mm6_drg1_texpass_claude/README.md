# MM6 BDragonFly (Drake) texture quality pass (`mm6_drg1`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm6:drg1` (token in `work/LEASE.txt`). Production [mm6_drg1_claude](../mm6_drg1_claude/README.md), reduction
[mm6_drg1_reduce_claude](../mm6_drg1_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md),
here with one config per texture set (`texpass_body.json`, `texpass_head.json`, `texpass_wings.json`, `TP_CONFIG=...`,
each with its own `tag` and `work/lod0_before<tag>.npz`).

## Texture quality pass (2026-11-11)

**Cause.** Three separate 2K sets (body, head, wings) at 28.6 / 20.7 / 34.1 % atlas use, 18.8 / 19.9 / 7.7 %
fragments, stretch 1.94 / 1.78 / 1.47. Merging them into one 2K atlas would have cut the body and wing texels, so each
set keeps its own 2048 atlas and gets its own layout and 4K paint.

**Route.** Layouts (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`; wings the plain
fast packer `uv_wings2`, which beat it on stretch 1.62 -> 1.19): **`work/uv_body_fixed.npz`, `uv_head_fixed.npz`,
`uv_wings2.npz` are the paid layouts.** Retextures (meshy-7, 4K, our UVs): body and wings with the production HD
masters `references_hd/01`–`04`, head with the head masters `references_head/01`–`04`: **30 credits**. Per set:
resample (now at the installed map sizes: 2K masks and metal/roughness stay 2K), AO, compose, then `tp_apply.py`
chained body -> head -> wings (`work/stage_*.glb`). New this model: `tp_compose.py` pins each class's area-weighted
mean to the approved one after the detail transfer (the small wing-arm region drifted 4–9 levels darker in its ramps
before the pin, 1–2 after). The approved normal maps were Meshy-scale (p90 tilt about 0.1), so the paint's normals
replace them at the approved strength (shaded normals p50 0.9–1.4°, p90 3.7–5.0° from the installed ones).

## Results (`texture_quality.py`, LOD0)

| Set | Atlas | Equivalent | Density p50 | Fragments | Stretch p90 |
|---|---|---|---|---|---|
| Body | 28.6 -> **59.0 %** | 1,095 -> 1,574 px | 2,022 -> 2,798 | 18.8 -> 3.3 % | 1.94 -> 1.26 |
| Head | 20.7 -> **50.0 %** | 932 -> 1,449 px | 660 -> 957 | 19.9 -> 1.9 % | 1.78 -> 1.17 |
| Wings | 34.1 -> **54.2 %** | 1,196 -> 1,508 px | 2,765 -> 3,473 | 7.7 -> 1.4 % | 1.47 -> 1.19 |

Tiers (ramps applied, same surface points): body, head and wing membrane within 1 level in A/B/C; wing arm (3.5 % of
the wings) within 2.3 levels after the pin. LOD1 colour error: body mean 9.7 -> 7.2, head 8.2 -> 5.6, wings 0.9 -> 1.2.

## Checks

`tp_diff.py` OK (only UVs, vertex splits, images, texture references); winding 0; flat 0.00/0.00/0.01; burn maps
resampled per set (1K as installed); viewer check 0 console errors; floor audit BDragonFly A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install.
Sheets: [review/texpass_sheet.png](review/texpass_sheet.png) (head 3/4 and front, body, back with wings),
[review/texpass_wing_sheet.png](review/texpass_wing_sheet.png) (wing close-ups: membrane veins and the arm's scales
finer; the arm's dark mottling is lighter than before, the one visible change).

Installed 2026-11-11. Rollback `work/before_texpass/mm6_drg1.glb`.
