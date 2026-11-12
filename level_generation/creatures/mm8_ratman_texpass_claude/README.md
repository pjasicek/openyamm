# Wererat Ratman texture quality pass (MM8 `mm8_ratman`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md):
the Troll's route for a body | head atlas, as on the Ogre ([mm8_m436_texpass_claude](../mm8_m436_texpass_claude/README.md)).

Only UVs, vertex splits and images changed. Unchanged: mesh, rig, clips (including h21 Sprint), materials, ramps,
variants, `actors.yml` and the sword attachment. No clips changed, so the arm and hand gate does not apply.

- Projects: [mm8_m448_claude](../mm8_m448_claude/README.md) (production) and
  [mm8_ratman_reduce_claude](../mm8_ratman_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_ratman.glb`.
- Lease: `mm8:ratman`.
- **Meshy: 20 credits.** Two 4K retextures: the body from the full-body HD masters, and the head only from the
  production head masters (`references_head/`: front, three-quarter, left, back).

## Route

The generic toolkit in `scripts/` runs from `texpass.json`:
- `head_uv_split 0.5`: the approved head set, with the head ×1.8 and the hands ×1.3.
- Detail limiter 1.3.
- Paid layout **`work/uv_fine.npz`**. Its 2 zero-area UV triangles are 3D slivers of area 1e-8.
- One 2048 atlas replaces the 2080×1024 one. The normal map is 2048², with tilt ×0.27 to match the approved p90.
- LOD1 is projected. LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `Ratman_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 22.6 % | **56.8 %** |
| Equivalent px | 990 | 1,543 |
| Density p10 / p50 / p90 | 224 / 333 / 901 | 1,012 / 1,050 / 1,879 (body ×3.2) |
| Spread | 4.01 | 1.86 (head ×1.8 by design) |
| Islands / fragments | 1,043 / 16.1 % | 434 / 2.6 % |
| Stretch p90 | 1.79 | 1.20 |

**Tone** (sRGB, approved → pass):
- trousers: (43.0, 65.2, 34.3) → (43.1, 65.2, 34.4). Luminance sd 2.4 → 2.7, so the levelled trousers stay level.
- fur and skin: (115.6, 91.4, 71.0) → (115.5, 91.4, 71.0).

**LOD colour error** (mean / p99, before → after):
- LOD1: 1.7 / 25.7 → 1.3 / 19.0;
- LOD2: 2.8 / 21.2 → 3.6 / 20.7;
- LOD3: 4.7 / 29.6 → 4.5 / 26.0.

**Face** ([review/cmp_face_a.png](review/cmp_face_a.png), front and three-quarter):
- The fur reads as fine directional strands instead of soft patches.
- The beady dark eyes, nose and ears are kept.
- The relief is slightly softer than the installed one, because of the normal tilt match.

## Checks

- `glb_diff`: OK.
- Winding: 0.
- Flat shading: 0.01.
- Viewer check: 6 models × 9 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Wererat Ratman*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_ratman.png](review/texpass_sheet_ratman.png). It shows head front, head 3/4, top,
side and whole body for each tier, installed against pass.

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_ratman.glb`.
