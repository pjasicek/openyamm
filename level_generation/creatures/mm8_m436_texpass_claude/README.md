# Ogre Peasant Male texture quality pass (MM8 `mm8_m436`), 2026-11-11

This is part of the MM6–MM8 audit fixes, texpass stream, by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md),
using the Troll's route for a body | head atlas.

Only UVs, vertex splits and images changed. Mesh, rig, clips (including h19 Walk2), materials, ramps, variants and
`actors.yml` are unchanged. Because no clip changed, the arm and hand gate does not apply.

- Projects: [mm8_m436_claude](../mm8_m436_claude/README.md) and
  [mm8_m436_reduce_claude](../mm8_m436_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m436.glb`.
- Lease: `mm8:m436`.
- **Meshy: 20 credits.** Two 4K retextures on the paid layout:
  - the body, from the full-body HD masters;
  - the head only, from the production head masters in `references_head/` (front, left, back, quarter).

## Route

This is the generic toolkit in `scripts/`. Settings in `texpass.json`:

- **Head set.** The installed 2080×1024 atlas has the 1K body set on the left and the 1K head set on the right.
  `head_uv_split 0.5` takes the head from the approved head-set faces (3,016 triangles). The head has ×1.8 density
  and the hands ×1.3, as on the Troll. The single 2048 atlas replaces the 2080×1024 one, keeping the same
  image and material names.
- **Head paint.** The head-only paint is crossfaded into the body paint at the neck.
- **`weld_tol` 1e-4** was added to `dump.py`. On this model it merged only one vertex: the separately generated head
  is really 344 separate shell pieces.
- **Layout.** The first layout (`uv_fine`) had 18 % fragments. **`work/uv_cut.npz` (paid; `cut_closed=1`)** brings it
  to 9.6 %. The floor is 4.7 %: that much surface is on 3D pieces with fewer than 8 triangles, which can only be
  fragments.
- **Normal map.** 2048² (it was 2080×1024), its tilt scaled ×0.52 to the approved p90.
- **LODs.** LOD1 is projected; the LOD2/3 512/256 maps are transferred again.

## Results (`texture_quality.py`, `M436_A`)

| | Before (2080×1024 body \| head) | After (2048²) |
|---|---|---|
| Atlas | 20.4 % | **54.9 %** |
| Equivalent px | 941 | 1,518 |
| Density p10 / p50 / p90 | 262 / 329 / 502 | 702 / 739 / 1,331 (×2.2 body, ×2.7 face) |
| Islands / fragments | 1,340 / 23.9 % | 650 / 9.6 % (5 % target missed; the floor is 4.7 %, from tiny head pieces) |
| Stretch p90 | 1.71 | 1.39 |

**Tone** (sRGB, approved → pass):
- clothes region: (102.0, 117.8, 40.1) → (102.2, 117.2, 40.2);
- skin, hair and leather: (130.1, 94.7, 58.9) → (130.1, 94.8, 58.8).

Luminance sd is unchanged (33.7 → 33.8). The detail limiter is 1.3.

**LOD colour error** (mean / p99, before → after):
- LOD1: 3.1 / 25.5 → 2.2 / 23.8;
- LOD2: 2.8 / 22.8 → 3.3 / 22.6;
- LOD3: 4.9 / 31.3 → 4.5 / 29.3.

## Faces and eyes

The face and eyes were checked close up, front and three-quarter, in tiers A and C. The tiers recolour only the
clothes. Crops: [review/cmp_face_a.png](review/cmp_face_a.png) and [review/cmp_eyes.png](review/cmp_eyes.png).

- The face gains brow wrinkles, nasolabial folds and lip definition.
- The eyes now read as reddish eyeballs under shaded lids. The installed light shard under the eye is gone.
- New: fine dark under-eye wrinkle lines from the head paint. They fit the ogre and are not blotches. If the user
  finds them too strong, the fix is a local damp of the head paint.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.02.
- Viewer check: 6 models × 8 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Ogre Pesant Male*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m436.png](review/texpass_sheet_m436.png) shows head front, head 3/4, top, side and
whole body for each tier, installed against pass.

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_m436.glb`.
