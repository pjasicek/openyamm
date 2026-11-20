# DemonFly texture quality pass (MM6 `mm6_wdm`), 2026-11-11

This is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, ramps, variants and `actors.yml` are
unchanged.

- Projects: [mm6_wdm_claude](../mm6_wdm_claude/README.md) and
  [mm6_wdm_reduce_claude](../mm6_wdm_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm6_wdm.glb`.
- Lease: `mm6:wdm`.
- **Meshy: 20 credits.** Two 4K retextures:
  - the whole body, with the HD masters in `references_hd/` (raised wings, as in the bind pose);
  - the grafted head only, with its turnaround masters in `references_head/`.

## Two 1K sets merged into one 2048 atlas

The installed LOD0 has two primitives:
- the body (`Demon_*`): a 1K set at 38.6 %;
- the grafted head (`DemonHead_*`): a 1K set at 39.2 %, with fragments 58.1 % and stretch 3.07.

Each set has its own burn map. With `merge_sets` both primitives are laid out in one 2048 atlas:
- the head is ×1.8, via `head_parts [1]` (a new `dump.py` option: head by primitive);
- the head materials keep their names, ramps and normal scale;
- their textures point at the merged images, including a merged burn map;
- five head-set images are dropped (26 → 21 images).

Because the sets are merged, the mask and metal/roughness are 2048 (twice the installed 1K).

LOD1 is projected; the LOD2/3 maps of both primitives are transferred again. `viewer.py` now takes clip names and
durations from the installed GLB, because the production viewer's manifest predates later clip changes.

The paid layout is **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`).

## Results (`texture_quality.py`)

| | Before: body set (1K) | Before: head set (1K) | After: one 2048 set |
|---|---|---|---|
| Atlas | 38.6 % | 39.2 % | **48.1 %** |
| Equivalent px | 636 | 641 | 1,421 |
| Density p50 | 721 | 409 | 1,398 (body ×1.9; head ×1.8 of body, about ×3.4 of before) |
| Islands / fragments | 982 / 16.8 % | 1,348 / 58.1 % | 364 / 0.7 % |
| Stretch p90 | 1.88 | 3.07 | 1.22 |

**Tone** (sRGB, approved → pass):
- body tier region (91.3, 47.8, 67.4) against approved (90.7, 46.9, 66.9);
- body rest (83.4, 73.3, 63.9) against (83.9, 74.0, 64.4);
- head tier region (98.3, 40.4, 57.3) against (98.3, 39.5, 57.2).

**LOD colour error** (body, mean / p99, before → after):
- LOD1: 6.2 / 44.2 → 6.8 / 46.3;
- LOD2: 4.4 / 28.2 → 7.8 / 35.3;
- LOD3: 8.4 / 47.2 → 9.4 / 43.6.

The rise comes from the sharper LOD0 detail, which the 512 and 256 maps cannot hold.

**Face** ([review/cmp_face.png](review/cmp_face.png), front and three-quarter, tiers A and C):
- the brow ridges, scales, horns and teeth are crisper;
- the cyan eyes are kept, with a slightly smaller glow.

## Checks

- `glb_diff`: OK, and the image count goes 26 → 21.
- Winding: 0.
- Flat shading: 0.00.
- Viewer check: 6 models × 6 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`DemonFly*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_wdm.png](review/texpass_sheet_wdm.png), every tier, installed against pass.

Installed 2026-11-11 (MM6). To roll back, install `work/before_texpass/mm6_wdm.glb`.
