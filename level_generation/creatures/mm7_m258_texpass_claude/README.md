# Griffin texture quality pass (MM7 `mm7_m258`), 2026-11-11

This is part of the MM6–MM8 audit fixes: the texpass stream, phase B, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, ramps, variants and `actors.yml` are
unchanged.

- Projects: [mm7_m258_claude](../mm7_m258_claude/README.md) and
  [mm7_m258_reduce_claude](../mm7_m258_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m258.glb`.
- Lease: `mm7:m258`.
- **Meshy: 10 credits**, for one 4K retexture with the production HD masters.

## Route

The generic toolkit in `scripts/`, with these settings:
- head ×1.5;
- three tier regions;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`);
- default compose;
- LOD1 projected, LOD2/3 maps transferred again.

## Results (`texture_quality.py`, `M258_A`)

| | Before | After |
|---|---|---|
| Atlas | 31.5 % | **56.1 %** |
| Equivalent px | 1,150 | 1,534 |
| Density p10 / p50 / p90 | 912 / 1,025 / 1,102 | 1,353 / 1,419 / 1,498 (×1.4) |
| Islands / fragments | 1,077 / 8.8 % | 179 / 0.1 % |
| Stretch p90 | 1.49 | 1.23 |

**Tone:** all three regions keep their approved means within 0.3 sRGB levels.

**LOD colour error** (mean / p99, before → after):

| LOD | Before | After |
|---|---|---|
| LOD1 | 5.0 / 34.0 | 5.3 / 35.3 |
| LOD2 | 9.3 / 45.8 | 10.0 / 45.0 |
| LOD3 | 12.3 / 58.6 | 13.2 / 52.5 |

**Head:** the feathers are crisper. The beak and the orange eyes are kept, in every tier.

## Checks

- `glb_diff`: OK.
- Winding: 0.
- Flat shading: 0.00.
- Viewer check: 6 models × 5 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Griffin*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m258.png](review/texpass_sheet_m258.png).

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m258.glb`.
