# MM8 Phoenix texture quality pass (`mm8_m572`, Phoenix A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references of the
body changed; the flame cards (`PhoenixFlames`), mesh, rig and clips are the installed ones. Lease `mm8:m572` (token in
`work/LEASE.txt`). Production [mm8_m572_claude](../mm8_m572_claude/README.md), reduction
[mm8_m572_reduce_claude](../mm8_m572_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** One 2K body set at 19.9 % with 3,405 islands and 39.1 % of the surface on fragments (spiky feather plumage;
xatlas starts from 1,400 charts on this mesh).

**Layouts tried** (`tp_uv.py`, `tp_layout_stats.py`):

| Run | Options | Atlas | Fragments | Stretch p90 | Overlap |
|---|---|---|---|---|---|
| uv_v2 | cut_closed, max_stretch 1.8, merge_below 20 | 52.4 % | 13.1 % | 1.17 | none |
| **uv_v3** | + max_stretch 2.5, retry 4, merge_below 30, max_cost 4 | 52.6 % | 10.2 % | 1.31 | none |
| uv_v4 | max_cost 8, roundness 0.2, max_edge_stretch 5 | 59.8 % | 7.9 % | 1.52 | **10.6 %** |
| uv_v5 | v4 without max_edge_stretch | 52.5 % | 8.9 % | 1.34 | 1.0 % |

**uv_v4 was painted first (10 credits, job `body_retexture_v1`) and rejected**: one chart (island 532) lies over
114 others (uv sum 70.4 % against a 59.8 % union), so two surfaces would share paint. `tp_layout_stats.py` now
prints uv sum against union; never upload a layout where they differ. **`work/uv_v3_fixed.npz`** is the paid layout
(23 sliver triangles of under 0.1 mm² left at zero UV area re-laid by `tp_fix_collapsed.py`). Its 10.2 % fragments are
above the 5 % target: they sit on the wing and chest plumage (no separate pieces), and the larger-chart settings that
lower them overlap; accepted against 39.1 % before.

Retexture `body_retexture_v2` (production masters `references_hd/01`–`04`, meshy-7, 4K, our UVs). **20 credits for
the model** (10 wasted on uv_v4). No head paint (head 4 % of the surface, no head masters). The approved normal (p90
tilt 0.81, a rebake) is carried onto the layout plus the paint's detail x0.5 (`tp_normal_check.py`: p50 0.3°, p90
1.3°, p99 5.2°). Tone per region (three ramps: body, flight feathers, tail/edges). LOD1 projected, LOD2/LOD3 refilled.

## Results (`texture_quality.py`, LOD0 body)

| | Before | After |
|---|---|---|
| Atlas | 19.9 % | **52.6 %** |
| Equivalent square | 914 px | 1,486 px |
| Density p50 | 938 | 1,500 |
| Islands / fragments | 3,405 / 39.1 % | 835 / 10.2 % |
| Stretch p90 | 1.19 | 1.31 |

Tiers within 1.2 sRGB levels per region (A body 205.5/143.9/31.0 -> 204.5/143.2/30.8; C tail 36.8/1.2/4.2 ->
36.3/1.2/4.1). LOD1 colour error mean 7.5 -> 6.2, p99 60.3 -> 51.1.

## Checks

`tp_diff.py` OK (flame mesh and its plume untouched); winding 0; flat 0.00; viewer check 0 console errors; floor
audit Phoenix A/B/C ok; motion audit re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install.
Sheet [review/texpass_sheet.png](review/texpass_sheet.png) (head 3/4 and front, body, top; the flame cards stand in
front of the head in the viewer, which draws them opaque): head feathers read sharper, tiers unchanged.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_m572.glb`.
