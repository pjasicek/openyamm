# Troll texture quality pass (MM8 `mm8_m476`), 2026-11-11

This is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md),
using the Troll Peasant's route for a body | head atlas.

Only UVs, vertex splits and images changed. These are unchanged:
- mesh, rig and clips, including the h20 Walk2/Jog/Sprint and the head-bob Running;
- materials, ramps and variants;
- `actors.yml`;
- the skull club, which is a separate GLB.

The animation stream still owns the Hit fix for this model. It should start from the GLB installed here.

- Projects: [mm8_m476_claude](../mm8_m476_claude/README.md) and
  [mm8_m476_reduce_claude](../mm8_m476_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m476.glb`.
- Lease: `mm8:m476`.
- **Meshy: 20 credits.** Two 4K retextures: one of the body, from the full-body HD masters, and one of the head only,
  from the production head masters in `references_head/`.

## Route

The generic toolkit in `scripts/`, with these settings in `texpass.json`:
- `head_uv_split 0.5`;
- head ×1.8, hands ×1.3;
- region: the cloth trims;
- detail limiter 1.3.

The paid layout is **`work/uv_cut_s.npz`**, made with `cut_closed=1 max_stretch=1.8 retry_stretch=3.0`. The other
runs missed a target:

| Layout run | Atlas | Fragments | Stretch p90 |
|---|---|---|---|
| `uv_fine` (plain) | 58.1 % | 5.9 % | 1.14 |
| `uv_cut` (`cut_closed`) | 59.0 % | 1.4 % | 2.21 |
| **`uv_cut_s`** | **57.8 %** | **4.8 %** | **1.15** |

The single 2048 atlas replaces the 2080×1024 one. LOD1 is projected; the LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `Troll_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 23.9 % | **57.8 %** |
| Equivalent px | 1,016 | 1,557 |
| Density p10 / p50 / p90 | 354 / 512 / 593 | 842 / 882 / 1,575 (body ×1.7, face ×1.8 more) |
| Islands / fragments | 762 / 21.3 % | 264 / 4.8 % |
| Stretch p90 | 1.66 | 1.15 |

**Tone**, in sRGB, approved → pass:
- skin, leather and mail: (85.0, 67.2, 39.5) → (84.7, 67.3, 39.5);
- cloth trims (4 % of the surface): (30.3, 131.4, 14.8) → (36.8, 130.5, 17.0). After the ramps, the green, blue and
  pink tier trims match in the sheet.

**LOD colour error** (mean / p99, before → after):
- LOD1: 3.0 / 39.7 → 1.3 / 13.9;
- LOD2: 3.6 / 28.4 → 3.2 / 15.8;
- LOD3: 6.4 / 46.4 → 4.6 / 26.1.

**Face** ([review/cmp_face_a.png](review/cmp_face_a.png), front and three-quarter):
- the brow wrinkles, pores and spots are crisp;
- the eyes and teeth are kept;
- there are no new blotches.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 11 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Troll [ABC]`): 3 bindings, 0 problems.

The first floor run used the glob `Troll*`. It also matched the Troll Peasant (`mm8_m480`, not this model), which
reports "Hit sinks to -3.3". That is pre-existing and not touched here.

**Sheet:** [review/texpass_sheet_troll.png](review/texpass_sheet_troll.png). It shows head front, head 3/4, top,
side and whole body for each tier, installed against pass.

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_m476.glb`.
