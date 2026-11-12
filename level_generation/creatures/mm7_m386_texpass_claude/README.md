# Robot texture quality pass (MM7 `mm7_m386`), 2026-11-11

This is the texpass stream of the MM6–MM8 audit fixes, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. Everything else is unchanged:
- the mesh and rig;
- the clips, including the attacks stream's new attack and Walk2/Run2;
- materials, ramps, variants and `actors.yml`.

- Projects: [mm7_m386_v2_claude](../mm7_m386_v2_claude/README.md) (production; its "texture fix" had already gone
  from 3,340 Smart UV islands to 844 hard-surface charts).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m386.glb`.
- Lease: `mm7:m386`.
- **Meshy: 10 credits** for one 4K retexture with the production HD masters.

## Route

This uses the generic toolkit in `scripts/` with `texpass.json`. Head, jaw and gun are ×1.5, as the production layout
gave them 2×.

The paid layout is **`work/uv_cut_s25.npz`** (`cut_closed=1 max_stretch=2.5 retry_stretch=4`). This is a hard-surface
mesh of 226 pieces:
- 5.2 % of its surface is on pieces under 8 triangles, which can only be fragments;
- pieces of 8–20 triangles carry another 17 %.

A run with `max_stretch=1.8` reached 25.3 % fragments at stretch 1.36. Fragments here are mostly whole flat plate faces,
not paint specks.

Toolkit change: `tp.prim_images` takes the union of the images of a primitive's variant materials. Tier A has no
region mask while B and C do; before the change, the mask was not carried. LOD1 is projected; the LOD2/3 maps are
transferred again. The B/C far-LOD masks keep their unchanged LOD UVs and approved content.

## Results (`texture_quality.py`, `Robot_A`)

| | Before | After |
|---|---|---|
| Atlas | 26.9 % | **60.8 %** |
| Equivalent px | 1,063 | 1,597 |
| Density p10 / p50 / p90 | 655 / 781 / 1,533 | 1,237 / 1,290 / 1,926 (×1.65) |
| Islands / fragments | 866 / 36.1 % | 769 / 23.0 % (inherent floor 5.2 %; 5 % target missed, see above) |
| Stretch p90 | 1.69 | 1.46 |

- **Tone.** The rest of the robot is 99 % of the surface and keeps the approved mean. The two small tier regions
  (0.2 % and 0.5 %) hold their tier tints in the sheet.
- **LOD colour error** (mean / p99, before → after):

  | LOD | Before | After |
  |---|---|---|
  | LOD1 | 14.1 / 89.4 | 14.3 / 87.9 |
  | LOD2 | 11.7 / 65.3 | 14.3 / 60.4 |
  | LOD3 | 17.8 / 78.6 | 16.8 / 64.7 |

  The high LOD error is pre-existing: the reduced hard-surface LODs merge plates.
- **Spotted brass.** The production README calls the spotted brass Meshy paint. The approved broad colour is kept
  below 4 texels, so the spots still set the colour. The new paint's engraving and rivets now read on top: the plates
  look engraved instead of blotchy. See [review/cmp_head_a.png](review/cmp_head_a.png). Removing the spots completely
  would mean dropping the approved broad colour, which this pass does not do.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 9 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Robot*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m386.png](review/texpass_sheet_m386.png). It shows every tier, installed against
pass.

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m386.glb`.
