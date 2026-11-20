# Gorgon texture quality pass (MM8 `mm8_m564`), 2026-11-11

This is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the recipe
([TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)) and the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, vertex splits and images changed. The mesh, rig, the
11 clips (including the q3 gait clips), ramps, materials, variants and `actors.yml` are unchanged.

- Production projects: [mm8_m564_claude](../mm8_m564_claude/README.md) and
  [mm8_m564_reduce_claude](../mm8_m564_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m564.glb`.
- Lease: `mm8:m564`.
- **Meshy: 10 credits.** One 4K body retexture with the production HD masters.

## Route

This uses the generic toolkit from [mm7_m186_texpass_claude](../mm7_m186_texpass_claude/README.md), with the Bat's
additions ([mm7_m158_texpass_claude](../mm7_m158_texpass_claude/README.md)). Settings in `texpass.json`:
- head ×1.5;
- regions plates / copper / horns / eyes;
- AO reach 0.02 m;
- detail limiter 1.3.

**Paid layout: `work/uv_fine.npz`.** LOD1 is projected per chart. The LOD2/3 512/256 maps are transferred again from
the new LOD0.

Toolkit changes made on this model:
- `keep_approved_regions` (`eyes` here) keeps the approved eye colour as it was. Before this, the 4K paint shrank and
  darkened the red glow: eye mean (136.9, 24.5, 14.2) → (119.7, 33.3, 20.2). With the option it holds at
  (136.7, 26.0, 15.1). See [review/cmp_eyes.png](review/cmp_eyes.png).
- Shadow copies of LOD1–3 are shrunk by up to 7.5 mm here. The apply check now accepts up to 1.5 % of the model
  extent, provided the triangles are the same.
- `emissive` and `occlusion` maps are carried over when a material has them (the Gorgon has neither).

## Results (`texture_quality.py`, `Gorgon_A`)

| | Before | After |
|---|---|---|
| Atlas | 15.6 % | **54.1 %** |
| Equivalent px | 808 | 1,507 |
| Density p10 / p50 / p90 | 667 / 820 / 1,252 | 1,548 / 1,596 / 2,266 (×1.95 median) |
| Spread | 1.88 | 1.46 (head ×1.5) |
| Islands / fragments | 1,611 / 26.8 % | 200 / 0.4 % |
| Stretch p90 | 1.94 | 1.20 |

**Tone** (sRGB means, approved → pass):
- plates: (84.7, 89.5, 51.1) → (83.9, 88.4, 50.1);
- copper: (72.2, 52.8, 24.5) → (72.8, 54.0, 25.9);
- horns: (170.6, 154.3, 124.0) → (169.9, 153.2, 122.0).

The ramps are unchanged.

**LOD colour error** (mean / p99, before → after):
- LOD1: 7.2 / 60.2 → 5.2 / 38.8;
- LOD2: 4.7 / 35.3 → 6.4 / 29.6;
- LOD3: 9.1 / 53.2 → 8.7 / 38.4.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 8 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor audit (`*Gorgon*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_gorgon.png](review/texpass_sheet_gorgon.png). It shows head front, head 3/4, top,
side and whole body for every tier, installed against pass, with identical cameras. Close-up:
[review/cmp_close.png](review/cmp_close.png).
- The armour plates show crisp pitting and edges.
- Horn grain is sharper.
- The brass/green, violet and gold/green tiers hold.

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_m564.glb`.
