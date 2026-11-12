# Wasp Warrior texture quality pass (MM8 `mm8_m556`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. These are unchanged:
- the mesh and rig;
- the clips, including the clip fixes that exist only in the installed reduce export;
- materials, ramps, variants and `actors.yml`;
- the sword and buckler GLB.

**Projects.** [mm8_m556_claude](../mm8_m556_claude/README.md) and
[mm8_m556_reduce_claude](../mm8_m556_reduce_claude/README.md).

**Starting point.** The installed GLB, backed up as `work/before_texpass/mm8_m556.glb`.

**Lease.** `mm8:m556`.

**Meshy.** 10 credits: one 4K retexture with the production HD masters.

## Route

The generic toolkit in `scripts/`, configured by `texpass.json`:
- head and mandibles ×1.5, wings ×0.7;
- region: the tier band;
- detail limiter 1.3;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`).

The layout has 32 zero-area UV triangles. They are 3D slivers, each at most 0.6 % of the median triangle area.

LOD1 is projected. The LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `WaspBody_A`)

| | Before | After |
|---|---|---|
| Atlas | 35.4 % | **64.8 %** |
| Equivalent px | 1,219 | 1,648 |
| Density p10 / p50 / p90 | 1,006 / 1,275 / 1,333 | 1,382 / 1,965 / 2,220 (×1.5) |
| Islands / fragments | 2,347 / 45.4 % | 183 / **0.0 %** |
| Stretch p90 | 1.75 | 1.15 |

**Tone** (sRGB, approved → pass):
- tier band: (19.9, 128.2, 57.6) → (21.2, 128.1, 57.3);
- yellow and black body: (152.2, 105.4, 20.0) → (152.1, 105.5, 20.1).

**LOD colour error** (mean / p99, before → after):
- LOD1: 5.1 / 53.5 → 3.8 / 53.2;
- LOD2: 6.5 / 36.2 → 9.3 / 38.2;
- LOD3: 12.9 / 60.2 → 12.7 / 47.2.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 7 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Wasp Warrior*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_wasp.png](review/texpass_sheet_wasp.png) shows every tier, installed against pass.
- The yellow and black pattern, the wing veins and the compound eyes are crisper.
- The green, violet and crimson tier eyes and bands hold.

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_m556.glb`.
