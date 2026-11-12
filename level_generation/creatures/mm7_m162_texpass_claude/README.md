# Behemoth texture quality pass (MM7 `mm7_m162`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md),
on the Troll's route for a body | head atlas.

Only UVs, vertex splits and images changed. These are unchanged:
- the mesh and rig;
- the clips, including the h10 Sprint and the head-bob Running;
- materials, ramps, variants and `actors.yml`.

No clip changed, so the arm and hand gate does not apply. The known Attack floor sink (audit) is a clip issue and is
outside this pass.

- Projects: [mm7_m162_claude](../mm7_m162_claude/README.md) and
  [mm7_m162_reduce_claude](../mm7_m162_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m162.glb`.
- Lease: `mm7:m162`.
- **Meshy: 20 credits.** One 4K retexture of the body, with the full-body HD masters, and one of the head only, with
  the production head masters.

## Route

The generic toolkit in `scripts/`, with these settings in `texpass.json`:
- `head_uv_split 0.5`;
- head ×1.8, hands ×1.3;
- region: the mane and beard;
- detail limiter 1.3.

Mask and metal/roughness are now 2048 (they were 2080×1024).

The paid layout is **`work/uv_cut_s25.npz`** (`cut_closed=1 max_stretch=2.5 retry_stretch=4`). The mane is about
270 shingles: closed pieces of 12–20 triangles that cover 28 % of the surface. Opened, they stretch, so many fall back
to xatlas pieces:
- `max_stretch=1.8` gave 19.2 % fragments at stretch 1.16;
- the paid run gives 15.8 % at 1.42.

LOD1 is projected; the LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `M162_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 31.7 % | **54.8 %** |
| Equivalent px | 1,172 | 1,516 |
| Density p10 / p50 / p90 | 183 / 248 / 441 | 456 / 476 / 697 (×1.9) |
| Islands / fragments | 1,648 / 50.9 % | 681 / 15.8 % (5 % target missed: the mane shingles, see above) |
| Stretch p90 | 2.58 | 1.42 |

**Tone** (sRGB, approved → pass):
- mane: (50.7, 70.1, 38.1) → (50.8, 70.1, 38.1);
- skin and the rest: (110.3, 95.3, 81.9) → (110.2, 95.4, 81.8).

**LOD colour error** (mean / p99, before → after):

| LOD | Before | After |
|---|---|---|
| LOD1 | 4.7 / 36.3 | 2.4 / 21.2 |
| LOD2 | 5.4 / 28.3 | 4.8 / 19.9 |
| LOD3 | 8.5 / 37.5 | 6.1 / 23.7 |

**Face.** Crops: [review/cmp_face_a.png](review/cmp_face_a.png) and [review/cmp_nose.png](review/cmp_nose.png).
- The brow plates, skin cracks and wrinkles are crisp.
- The orange eyes are kept.
- The installed nose was shattered into flat shards; the pass gives clean nostrils.
- Remaining: faint straight chart seams through the nostril area, much milder than the shards before.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 9 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Behemoth*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m162.png](review/texpass_sheet_m162.png). It shows every tier, installed against
pass.

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m162.glb`.
