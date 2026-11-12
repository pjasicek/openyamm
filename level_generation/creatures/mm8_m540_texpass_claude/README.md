# Ogre Mage texture quality pass (MM8 `mm8_m540`), 2026-11-11

This pass belongs to the MM6–MM8 audit fixes, texpass stream, phase B (texpass-2,
[TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md),
using the Troll's route for a body | head atlas.

Only UVs, vertex splits and images changed. These are unchanged:
- the mesh and rig;
- the clips, including attacks-1's new Attack and Cast and the h19 Walk2/Jog/Sprint;
- materials, ramps, variants, `actors.yml` and the wand GLB.

Because no clip changed, the arm and hand gate does not apply.

- Projects: [mm8_m540_claude](../mm8_m540_claude/README.md),
  [mm8_m540_reduce_claude](../mm8_m540_reduce_claude/README.md) and
  [mm8_m540_attacks_claude](../mm8_m540_attacks_claude/).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m540.glb`.
- Lease: `mm8:m540`.
- **Meshy: 20 credits.** One 4K retexture of the body with the full-body HD masters, and one of the head only with
  the production head masters (`references_head/`).

## Route

The generic toolkit in `scripts/`. Settings in `texpass.json`:
- `head_uv_split 0.5`, head ×1.8, hands ×1.3;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`);
- default compose (sigma 4, detail 0.9, detail limit 1.3);
- **`keep_approved_near`** on the two glowing orange eyes, found from the brightest saturated orange texels
  (bind pose x −0.055 and 0.02, y 1.475, z 0.185; radius 2 cm, 65 triangles).

Without the eye keep, the paint dimmed the glow and softened the slit pupils.

LOD1 is projected. The LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `OgreMage_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 28.1 % | **61.1 %** |
| Equivalent px | 1,103 | 1,600 |
| Density p10 / p50 / p90 | 331 / 452 / 943 | 1,055 / 1,089 / 1,192 (×2.4) |
| Islands / fragments | 1,756 / 8.4 % | 771 / 1.5 % |
| Stretch p90 | 2.06 | 1.17 |

**Tone** (sRGB, approved → pass):
- robe tier region: (50.6, 115.4, 40.9) → (50.6, 115.3, 40.9);
- the rest holds within about 1 level.

**LOD colour error** (mean / p99, before → after):

| LOD | Before | After |
|---|---|---|
| LOD1 | 5.1 / 46.7 | 2.3 / 27.5 |
| LOD2 | 8.8 / 63.3 | 5.1 / 49.8 |
| LOD3 | 11.6 / 86.0 | 7.4 / 65.9 |

**Face** ([review/cmp_face.png](review/cmp_face.png), [review/cmp_eyes.png](review/cmp_eyes.png); tiers A and C):
- The brow wrinkles and lips are crisper.
- The installed face had shards under the eyes, which are gone.
- The tusks and eyes match the installed ones.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 12 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Ogre Mage*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m540.png](review/texpass_sheet_m540.png).

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_m540.glb`.
