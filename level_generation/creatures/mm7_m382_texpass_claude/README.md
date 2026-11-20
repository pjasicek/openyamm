# Rat texture quality pass (MM7 `mm7_m382`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, phase B. It was done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)) and follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. These are unchanged:
- mesh, rig and clips, including Walk2, Run2, Sprint and Walk3;
- materials, ramps and variants;
- `actors.yml`.

The Rat and zrat descriptors bind this same GLB.

- **Projects:** [mm7_m382_claude](../mm7_m382_claude/README.md) and
  [mm7_m382_reduce_claude](../mm7_m382_reduce_claude/README.md).
- **Starting point:** the installed GLB, backed up as `work/before_texpass/mm7_m382.glb`.
- **Lease:** `mm7:m382`.
- **Meshy:** 10 credits, for one 4K retexture with the production HD masters.

## Route

This uses the generic toolkit in `scripts/` (see [mm7_m186_texpass_claude](../mm7_m186_texpass_claude/README.md)):
- head ×1.5;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`);
- default compose (sigma 4, detail 0.9, detail limit 1.3);
- LOD1 projected, LOD2/3 maps transferred again.

## Results (`texture_quality.py`, `M382_A`)

| | Before | After |
|---|---|---|
| Atlas | 26.6 % | **57.5 %** |
| Equivalent px | 1,055 | 1,543 |
| Density p10 / p50 / p90 | 793 / 880 / 929 | 1,254 / 1,295 / 1,326 (×1.5) |
| Islands / fragments | 1,339 / 9.5 % | 331 / 0.9 % |
| Stretch p90 | 1.41 | 1.13 |

**Tone:** the main regions hold within 1 sRGB level. The tiny eye region (0.06 % of the surface) is slightly lighter,
(24, 19, 17) → (30, 24, 20), which is not visible.

**LOD colour error**, mean / p99, before → after:
- LOD1: 3.7 / 36.0 → 2.2 / 33.5;
- LOD2: 8.3 / 38.0 → 10.3 / 40.7;
- LOD3: 12.4 → 11.6 mean.

**Faces:** [review/cmp_face.png](review/cmp_face.png) (tiers A and C).
- The black (A) and red (C) eyes are kept.
- Fur, ears and claws are crisper.

## Checks

- `glb_diff`: OK.
- Winding: 0.
- Viewer check: 6 models × 12 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor: 0 problems. The glob `*at [abcABC]` matched 12 bindings, Rat and zrat together with the Bats.

**Sheet:** [review/texpass_sheet_m382.png](review/texpass_sheet_m382.png).

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m382.glb`.
