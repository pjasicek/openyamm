# Hydra texture quality pass (MM7 `mm7_m266`), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream (texpass-2,
[TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)), following the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and [handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs,
vertex splits and images changed. Mesh, rig, clips (including q3 Run2), materials, ramps, variants and `actors.yml`
are unchanged.

- Projects: [mm7_m266_claude](../mm7_m266_claude/README.md) and
  [mm7_m266_reduce_claude](../mm7_m266_reduce_claude/README.md). The far LODs come from `lod_repair_claude`.
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m266.glb`.
- Lease: `mm7:m266`.
- **Meshy: 10 credits.** One 4K retexture of the whole creature with the production HD masters.

## The two sets are merged into one atlas

The installed LOD0 mesh `M266` has two primitives:
- the body (`Hydra_*`): a 2K set at 34.8 % atlas, 16.7 % fragments;
- the five grafted heads (`HydraHeads_*`): a 1536×1024 set of five 512 tiles, one per head, each from its own Meshy
  head model. It was the worst set: 18.9 % atlas, 48.8 % fragments, median density 444 against the body's 829.

The pass lays both primitives out in one 2048 atlas (`texpass.json merge_sets`) and paints them with one full-creature
retexture.
- The `HydraHeads_*` materials keep their names, ramps and normal scale.
- Their textures now point at the body set's images.
- The four head-set images are dropped: 24 → 20 images, and the runtime memory falls by one 1536×1024 set.

The heads get density ×0.8. Uniform density would have cost the body 5 % (829 → 786). At ×0.8 both improve:
- body 829 → 949 texels per creature size;
- heads 444 → about 760.

## Toolkit changes made here

These are in `scripts/` and copied forward:
- `tp.part_images` and per-primitive sources in `resample.py`.
- Tone classes per primitive × region in `compose.py`.
- `apply.py` handles meshes with several primitives:
  - shadow meshes that hold all the primitives in one;
  - per-primitive LOD projection or transfer;
  - shadows of LODs whose UVs did not change are left untouched;
  - the set merge with image pruning.
- `glb_diff.py` reports a changed image count instead of failing on it.
- `dump.py` `weld_split_normals` was tried here and is off: the fins are not double-sided.

## Layout

The paid layout is **`work/uv_h08_loose.npz`**: `max_density_ratio=4 max_edge_stretch=4`, heads ×0.8.

| Layout run | Atlas | Fragments | Stretch p90 | Body density p50 |
|---|---|---|---|---|
| `uv_fine` (heads ×1.3) | 55.8 % | 11.0 % | 1.22 | 786 (below installed) |
| `uv_h08` (heads ×0.8) | 58.9 % | 11.0 % | 1.22 | 949 |
| **`uv_h08_loose`** | **59.2 %** | **10.0 %** | 1.25 | 951 |
| `uv_h08_abf` (angle-based) | 59.6 % | 13.2 % | 1.12 | 956 |

**Fragments miss the 5 % target.** The fragment surface sits on the connected surface of the squeezed spiky fins and
the heads' spikes, not on separate pieces. 153 of the merged charts there flip under SLIM and fall back to their xatlas
pieces. It is still well below the installed 16.7 % (body) and 48.8 % (heads).

## Results (`texture_quality.py`, LOD0 `Hydra_A`, now body and heads together)

| | Before: body set | Before: head set | After: one set |
|---|---|---|---|
| Image | 2048² | 1536×1024 | 2048² |
| Atlas | 34.8 % | 18.9 % | **59.2 %** |
| Density p50 | 829 | 444 | 1,029 overall: body 951, heads about 760 |
| Islands / fragments | 734 / 16.7 % | 2,195 / 48.8 % | 1,129 / 10.0 % |
| Stretch p90 | 1.42 | 1.88 | 1.25 |

**Tone** (sRGB means, approved → pass):

| Region | Approved | Pass |
|---|---|---|
| Body hide | (57.0, 54.2, 67.0) | (58.2, 55.2, 67.3) |
| Body rest | (159.7, 142.7, 118.9) | (157.0, 140.5, 118.3) |
| Head hide | (45.4, 48.5, 76.1) | (45.7, 48.6, 75.6) |
| Head rest | (133.9, 72.9, 59.7) | (133.3, 72.8, 59.9) |

The detail limiter is 1.3.

**LOD colour error** (body primitive, mean / p99, before → after):
- LOD1: 10.8 / 79.5 → 6.6 / 49.5;
- LOD2: 8.5 / 54.2 → 7.4 / 37.3;
- LOD3: 12.7 / 72.2 → 9.5 / 46.5.

## Checks

- `glb_diff`: OK. Only UVs, splits and images differ, and the image count drops 24 → 20.
- Winding: 0. Flat shading: 0.00 for both primitives.
- Viewer check: 6 models × 9 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`*Hydra*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m266.png](review/texpass_sheet_m266.png). It shows head front, head 3/4, top, side
and whole body for each tier, installed against pass. Head close-up: [review/cmp_head_a.png](review/cmp_head_a.png).
- Scales are sharper on the heads, neck and body.
- Eyes, teeth and tongue are kept.
- The olive, blue-grey and red tiers hold.
- The fifth head is red in every tier both before and after; that is unchanged.

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m266.glb`.
