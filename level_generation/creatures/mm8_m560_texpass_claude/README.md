# Wyvern texture quality pass (MM8 `mm8_m560` + MM7 `mm7_m434`), 2026-11-11

This is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

The MM7 Wyvern `mm7_m434` has the same binary chunk as `mm8_m560`; only its material ramps differ. Both were claimed:
`mm7:m434` through [mm7_m434_texpass_claude](../mm7_m434_texpass_claude/README.md). `apply.py` ran on each installed
GLB, and the two exports again share one binary chunk byte for byte, each with its own ramps.

Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, ramps, variants and `actors.yml` (both
worlds) are unchanged.

- Projects: [mm8_m560_claude](../mm8_m560_claude/README.md), [mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md)
  and [mm7_m434_claude](../mm7_m434_claude/README.md).
- Starting point: the installed GLBs, backed up as `work/before_texpass/mm8_m560.glb` and `mm7_m434.glb`.
- **Meshy: 10 credits** for both worlds: one 4K retexture with the production HD masters.

## Route

The generic toolkit in `scripts/`, configured by `texpass.json`:
- Head and jaw ×1.5; regions are the membrane and the body.
- Paid layout: **`work/uv_fine.npz`**.
- LOD1 is projected. The LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `Wyvern_A`, the same in both worlds)

| | Before | After |
|---|---|---|
| Atlas | 24.6 % | **52.0 %** |
| Equivalent px | 1,016 | 1,477 |
| Density p10 / p50 / p90 | 1,472 / 1,632 / 1,678 | 2,373 / 2,437 / 2,507 (×1.5) |
| Islands / fragments | 944 / 5.2 % | 370 / 0.9 % |
| Stretch p90 | 1.31 | 1.10 |

**Tone** (sRGB means, approved → pass):

| Region | Approved | Pass |
|---|---|---|
| Membrane | (134.5, 109.5, 40.0) | (134.2, 109.5, 40.1) |
| Body | (98.7, 104.0, 61.6) | (98.8, 104.0, 61.6) |
| Rest | (182.8, 167.2, 142.3) | (183.3, 167.6, 142.5) |

**LOD colour error** (mean / p99, before → after):

| LOD | Before | After |
|---|---|---|
| LOD1 | 5.6 / 43.3 | 3.6 / 49.9 |
| LOD2 | 6.8 / 38.6 | 11.4 / 48.1 |
| LOD3 | 13.0 / 63.1 | 14.0 / 56.0 |

The LOD2 rise is the sharper LOD0 scale pattern, which the 512 map cannot hold.

## Checks

- `glb_diff`: OK, both worlds.
- Winding: 0. Flat shading: 0.01.
- Viewer check: 12 models × 5 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor: `Wyvern*` (MM8) and `AWyvern*` (MM7), 3 + 3 bindings, 0 problems.

## Sheets

The sheets use identical cameras and show every tier, installed against pass:
- [review/texpass_sheet_m560.png](review/texpass_sheet_m560.png) (MM8)
- [review/texpass_sheet_m434.png](review/texpass_sheet_m434.png) (MM7)

The automatic head-front camera frames this flying pose too far away. The 3/4 head crops in
[review/cmp_head.png](review/cmp_head.png) cover the head: scales are sharper, and the red eyes and the teeth are
kept.

Installed 2026-11-11 in MM8 and MM7. To roll back, install the two `work/before_texpass/` GLBs.
