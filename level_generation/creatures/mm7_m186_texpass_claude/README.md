# Dragonfly texture quality pass (MM7 `mm7_m186`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, agent texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [MM6–MM8 handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images changed. Mesh, rig, weights, clips, ramps, materials, variants and `actors.yml`
are the installed ones.

Production projects: [mm7_m186_claude](../mm7_m186_claude/README.md) and
[mm7_m186_reduce_claude](../mm7_m186_reduce_claude/README.md). The installed GLB, the reduced export, is the
starting point; its copy is `work/before_texpass/mm7_m186.glb` and the `actors.yml` entries are in
`work/before_texpass/actors_entries.yml`. Lease `mm7:m186`; the token is in `work/LEASE.txt`.

**Meshy: 10 credits.** One 4K body retexture (`meshy/body_retexture_v2`) on the paid layout, with the production
HD masters (front, left, back, right). There was no head-only paint: an insect head has no face, and the close-ups
read well.

## Cause

The Smart UV layout used 9.0 % of the 2048 atlas. It had 1,785 islands, mostly tiny specks inside large painted
pads, and 31.8 % of the surface was on fragments. The four wings (a separate mesh, `DragonflyWings`) share the same
images.

## Route: generic toolkit in `scripts/`, driven by `texpass.json`

These scripts generalise the Troll's (`mm8_m480_texpass_claude`). They read `texpass.json`:
- `layout_meshes`: the LOD0 body first, then LOD-less meshes that sample the same images (here the wings);
- `head_bones` and `head_factor`, `group_factors`, `regions`, `no_ao_meshes`, `ao_reach`;
- masters, tiers, viewer focuses and shots.

The steps:
1. `dump.py`: the layout meshes of the installed GLB into `work/lod0_before.npz`.
2. `uv.py` (Blender) runs `uv_atlas.py`. The Head bone is ×1.5 and the wings ×0.6: the wings are 46 % of the
   surface, translucent, and carry only veins. The fast packer sweep (`fine=250 steps=0`) produced
   **`work/uv_fine.npz`, the paid layout; never re-run it.** A trial with the wings at ×0.45
   (`work/uv_fine_w45.npz`, unused) gained only 3 % body density.
3. `resample.py`: the approved colour, region mask, metal/roughness and normal carried onto the layout at the same
   surface points.
4. `bake_ao.py` (Blender): reach 0.02 m.
5. `compose.py` builds the maps:
   - 4K → 2K once;
   - the gentle grade (no AO on the wings);
   - a tone curve per region and per mesh rest;
   - island by island, the approved colour below 4 texels plus the paint's luminance detail ×0.9;
   - normal convention measured (the Meshy map is +y down, so it is flipped), tilt scaled to the approved p90 (×0.59),
     at the installed 1K;
   - mask and metal/roughness: the approved ones.
6. `apply.py` writes the GLB:
   - new UVs on LOD0, the wings and the LOD0 shadow;
   - LOD1–3 share the LOD0 images, so their UVs are projected per chart from LOD0. Their shadow copies take the same
     UVs; they are the same triangles, shrunk by up to 1 mm.
7. Checks:
   - `glb_diff.py` (from the Troll project);
   - `lod_check.py`, `layout_check.py`;
   - `viewer.py` (review viewer with installed and pass versions per tier);
   - `shots.py` (identical-camera viewer shots and the sheet).

To reuse the toolkit on another model, copy `scripts/` and write that model's `texpass.json`.

## Results (`texture_quality.py`, installed LOD0 base colour)

| | Before | After |
|---|---|---|
| Atlas (body mesh, as the audit counts it) | 9.0 % | **44.5 %** |
| Atlas (whole image: body and wings) | about 10 % | **54.2 %** |
| Equivalent px | 614 | 1,366 |
| Density p10 / p50 / p90 | 391 / 476 / 1,178 | 1,348 / 1,399 / 2,099 (×2.9 median) |
| Spread | 3.02 | 1.56 (head ×1.5 by design) |
| Islands / fragments | 1,785 / 31.8 % | 324 / 1.2 % |
| Stretch p90 | 1.71 | 1.20 |
| Meshy source | 2K | 4K on the final layout, downsampled once |

`texture_quality.py` counts only the first mesh that uses an image, so it leaves out the wings sharing the atlas. The
body-only figure (44.5 %) is below the stream's 48 % target. The image itself is 54.2 % used; giving the wings less
space was tried and gained little.

**Tone** (`textures/tp_tone.json`, area-weighted sRGB means, approved → pass):
- crest: (10.3, 162.6, 2.3) → (11.5, 161.9, 2.5);
- body: (115.6, 70.8, 28.1) → (115.2, 71.0, 28.0);
- wings: (228.2, 193.2, 160.8) → (228.1, 193.2, 160.8).

Luminance sd rises with the new detail: body 34.3 → 38.6, crest 29.9 → 31.9, wings 49.4 → 51.4. There is no colour
drift; the ramps are unchanged.

**LOD colour error against LOD0** (`lod_check.py`, mean / p99, before → after):
- LOD1: 7.3 / 53.8 → 7.1 / 59.9;
- LOD2: 12.5 / 65.2 → 13.4 / 76.7;
- LOD3: 16.9 / 77.5 → 18.6 / 88.1.

The far LODs rise slightly, partly from the sharper texture itself. At the bq (whole-body) distance they look the same.

## Checks

- `glb_diff.py`: OK. Only UVs, vertex splits (body 10,235 → 11,288, wings 765 → 821) and images differ.
- `check_winding.py`: 0 inverted closed parts. `flat_shading_check.py`: flat 0.00.
- Detached parts: positions and weights are identical per corner (`glb_diff`), so the result is unchanged.
- Motion: clips are identical (`glb_diff`), so it was not re-measured.
- Floor audit (MM7 `*Dragonfly*`): 3 bindings, 0 problems.
- Viewer check: 6 models × 6 clips, no console errors. The viewer is `review/viewer/` (serve with
  `claude_shared/serve_review.py`).
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS (647 descriptors on 185 models).

**Sheet:** [review/texpass_sheet_m186.png](review/texpass_sheet_m186.png). It shows head front, head 3/4, top, side
and whole body for tiers A/B/C, installed against pass. Close-up crop: [review/cmp_hq_a.png](review/cmp_hq_a.png).
- The chitin rings, abdomen grain, mandibles and bristles are crisp.
- The compound eyes keep their orange-red facets, with no pupils or shards.
- The crest keeps its tier colours (green, blue, red).

Installed 2026-11-11 with `tools/install_model.py export/mm7_m186.glb --world mm7`. To roll back, install
`work/before_texpass/mm7_m186.glb`.
