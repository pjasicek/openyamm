# ADragon texture quality pass, head set only (MM7 `mm7_m182`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

The model has three 2048 sets: body and wings (the MM6 `cdr1` body), and the grafted MM7 head. Only the head set was
the group A problem: atlas 28.8 %, fragments 36.1 %, stretch p90 3.43, and density 808 against the body's 1,597.
The pass lays out and repaints **the head primitive only**, using `texpass.json layout_prims`. The body and wings
sets, their UVs and their LODs are untouched. Only the head's UVs, vertex splits and images changed; the mesh, rig,
clips, materials, ramps, variants and `actors.yml` are unchanged.

- Projects: [mm7_m182_claude](../mm7_m182_claude/README.md) (v3b).
- Lease: the stale October lease (`m182-reduce-20261021`) was released with its own token, as COMMON.md allows, and
  `mm7:m182` was claimed here.
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m182.glb`.
- **Meshy: 10 credits.** One 4K head-only retexture, with the whole-dragon v3 masters, as the production v3 head
  paint was made.

## Toolkit additions

- **`layout_prims`**: lay out a subset of a mesh's primitives. `apply.py` keeps the other primitives' UVs in the
  shared shadow mesh and in the LODs.
- **`openyamm_burn_map`** is carried as kind `burn`.
- **Mask and metal/roughness keep their installed size**, at most 2048. Here that is 2048, not 1024.
- **`keep_approved_grow`** (4 texels): the kept eye region (r2) also takes the dark slit pupil that the region mask
  does not cover.
- **`scripts/normal_carry.py`** carries the approved normal map onto the new layout. Per triangle, it rotates XY from
  the old UV frame to the new one, after `mm9_eye_claude/restore_pebbles.py`. Of the two v-axis conventions, it keeps
  the one with the stronger measured relief.

## The look: the old pattern is kept

On the default settings (sigma 4, detail 0.9) the 4K paint drew a high-contrast crackle network. That replaced the
approved pebbled and spotted hide on the snout, and the hide no longer matched the neck, which is in the unchanged
body set. The eye slit also blurred.

The installed paint is therefore composed as on the MM9 Eye:
- `compose.py textures/tp 1.0 0.4`: the approved colour carries down to pebble scale, and the paint adds only its
  finest band at ×0.4;
- the eyes come from the approved paint;
- `normal_carry.py textures/tp 1.5 0.3`: the approved relief, plus 0.3 of the 4K normal's fine band.

The result keeps the installed look in every tier, including the spots and the slit pupils
([review/cmp_head.png](review/cmp_head.png)). The gain is the layout: no stretched or smeared charts, fewer
fragments, ×1.5 density. It is not new paint detail.

## Results (`texture_quality.py`, `DragonHead_A`)

| | Before | After |
|---|---|---|
| Atlas | 28.8 % | **62.4 %** |
| Equivalent px | 1,098 | 1,618 |
| Density p10 / p50 / p90 | 609 / 808 / 889 | 1,157 / 1,202 / 1,239 (×1.5) |
| Islands / fragments | 293 / 36.1 % | 142 / 11.8 % |
| Stretch p90 | 3.43 | 1.34 |

**Fragments miss the 5 % target.** The head is 15 connected pieces with no pieces under 8 triangles. The fragments sit
on horns, teeth and frills, where the merged charts revert. Two other runs were tried:

| Run | Fragments | Stretch |
|---|---|---|
| `uv_fine` | 18.2 % | 1.25 |
| `uv_cut_loose` | 12.5 % | 1.36 |

The paid layout is **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`).

The body set (32.4 % / 8.6 %) and wings set (29.6 % / 5.0 %) are unchanged.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 9 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`ADragon*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m182.png](review/texpass_sheet_m182.png) (every tier, installed against pass).

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m182.glb`.
