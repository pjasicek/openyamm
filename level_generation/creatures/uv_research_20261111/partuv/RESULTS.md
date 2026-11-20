# Candidate 1: PartUV (zero Meshy credits)

Research for [the UV study brief](../BRIEF.md), 2026-11-11. No Meshy job was submitted and no file outside
`uv_research_20261111/` was changed. Subjects: the Magreeb (pilot, read-only copy of its v8 inputs), then
`mm8:m620` (Bedraggled Human, body set + head set) and `mm6:hyd` (BHydra, body set + five head tiles), as the
coordinator asked.

## Verdict

**Yes, a PartUV layout is worth a paid Meshy paint, on every subject.** Packed with our own xatlas packer at
2048 / 2 px, PartUV charts beat a fresh `uv_atlas.py` run on the same mesh on atlas use (+1.7 to +9.4 points) and
seam length (10-31 % shorter), and they keep stretch at about 1.1-1.25. `uv_atlas.py`'s SLIM merges reach 2.0-2.1 on
the humanoid. Fragments come out lower on three sets (Magreeb, m620 head, Hydra heads) and higher on two: the m620
body (2.4 against 0.2 %) and the Hydra body (3.0 against 2.1 %), both within the 3 % target.

| Subject / set | Baseline: fresh `uv_atlas.py` (atlas / fragments / stretch p90 / islands) | Best PartUV (same measures) | Candidate upload |
|---|---|---|---|
| Magreeb body | 54.0 % / 2.1 % / 1.17 / 261 (installed v8) | **57.2 % / 0.9 % / 1.14 / 168** (t1.25) | `magreeb/upload/magreeb_body_upload_partuv_t1.25.glb` |
| m620 body | 57.8 % / 0.2 % / **2.11** / 139 | **67.2 % / 2.4 % / 1.10 / 172** (t1.1) | `mm8_m620/upload/m620_body_upload_partuv_t1.1.glb` |
| m620 head set | 52.5 % / 31.7 % / **2.04** / 879 | **54.2 % / 29.5 % / 1.24 / 780** (t1.5) | `mm8_m620/upload/m620_head_upload_partuv_t1.5.glb` |
| Hydra body | 57.0 % / 2.1 % / 1.14 / 150 | **62.6 % / 3.0 % / 1.12 / 132** (t1.5) | `mm6_hyd/upload/hyd_body_upload_partuv_t1.5.glb` |
| Hydra heads (5 tiles of 512) | 42.3 % / 5.5 % / 1.58 / 302 | **46.4 % / 4.2 % / 1.62 / 201** (t1.25 + merge) | `mm6_hyd/upload/hyd_head_tile{0,1,3,4,5}_upload_hybrid_t1.25.glb` |

Installed layouts for reference: m620 33.7 % atlas over its 4128 x 2048 image (fragments 9.9 %, stretch 2.19);
Hydra body 50.6 % / 1.1 % / 1.75; Hydra heads 42.9 % / 24.5 % / 1.72.

What PartUV changes, and what it does not:
- **Charts follow parts.** The charts are larger and rounder. Against `uv_atlas.py` on the same mesh: Magreeb 168
  against 261 islands, Hydra body 132 against 150, Hydra heads 201-247 against 302; the m620 body's best layout has
  more islands (172 against 139) but packs 9 points better. They pack better everywhere, at the same margin and
  packer.
- **Stretch is the clearest gain.** Every PartUV layout has a stretch p90 of 1.07-1.28. `uv_atlas.py` merges small
  charts and flattens them again with SLIM, and that leaves density gradients: the m620 shin, at 2.11, is visible in
  `mm8_m620/heat/views_uv_atlas_body.png`.
- **Within-chart area distortion grows with the threshold.** The density spread goes from 1.09 at t1.1 to
  1.28 at t2. Use t1.1-1.5. Higher thresholds buy little atlas.
- **It does not fix geometric fragments.** The m620 head set is a scalp of open hair cards (2,778 boundary edges)
  and the Hydra heads have teeth and fins as separate pieces. Every method leaves 29-34 % (m620 head) and 4-8 %
  (Hydra heads) of the surface on islands under 8 triangles. That is a mesh problem, not a layout problem.
- **Uploads are ready, but the Meshy noise floor (candidate 6) is not measured yet.** Confirm a paint gain against
  it before adopting.

Recommendation: paint **m620 body t1.1** first. It is the largest layout gain (+9.4 atlas points over a fresh
`uv_atlas.py`, +16.6 over the installed body tile, stretch 2.11 -> 1.10), and the m620 is a real b9 subject.

## Code, licence, install

- Code: <https://github.com/EricWang12/PartUV> (official, SIGGRAPH Asia 2025; commit `46bad07`, 2026-07-18), cloned
  into `src/PartUV` (git-ignored). Prebuilt wheel `partuv==0.1.2` from PyPI (cp39-cp313, manylinux x86_64), which
  holds the C++ pipeline (`_core`), the PartField inference code and the preprocessing. Paper arXiv 2511.16659,
  project page zhaoningwang.com/PartUV.
- **Licences.** PartUV is Apache-2.0. **PartField** (its default part tree, `nv-tlabs/PartField`) is under the
  **NVIDIA License, non-commercial use only** ("The Work and any derivative works thereof only may be used or
  intended for use non-commercially"). Its checkpoint is `model_objaverse.ckpt` (1.2 GB) from the Hugging Face mirror
  `mikaelaangel/partfield-ckpt`, the URL in PartUV's README. Whether running a non-commercial tool to make UVs for a
  GPL game is acceptable is the user's decision. **The bone-tree variant below removes PartField completely**, leaving
  only Apache-2.0 code.
- Packing in PartUV: `pack/pack_blender.py` (Blender `pack_islands(margin=0.001)`) or UVPackMaster (paid add-on,
  needed for its part-grouped and multi-atlas packing; not tried).
- Dependencies: Python 3.11 venv (`venv/`, uv), torch 2.7.1+cu128, torch-scatter 2.1.2, the repo's
  `requirements.txt` (lightning 2.2, trimesh 4.9.0, open3d, libigl ...), plus scikit-learn, pytz, networkx and
  matplotlib, which the requirements omit. The GPU (RTX 3060 Ti 8 GB, shared with the desktop) was enough.
  PartField inference takes 1.4-2.8 s on 4-6k triangles. PAMO, the GPU simplifier PartUV uses inside its distortion
  check, also needs CUDA (`unwrap.pamo: false` for CPU only).
- **Safety.** The checkpoint is a pickle. Its globals were listed with `pickletools` (OrderedDict,
  `_rebuild_tensor_v2`, FloatStorage, `yacs` CfgNode, `set`: nothing executable). It was loaded with
  `torch.load(weights_only=True)` and saved as a plain state dict (`weights/partfield_state_dict.pt`), which is what
  the pipeline loads. Every run is `python -I` from an unrelated directory against the installed wheel, never the
  clone. The setup scripts were read before installing. No network access at run time.
- Runtime per set: PartField 1.4-2.8 s, the PartUV unwrap 0.2-1.8 s per threshold, then our xatlas pack 4-6 min at
  2048 (4 s at 512). A fresh `uv_atlas.py` takes 3-8 min.

## Method

Every unwrapper sees the same welded, triangulated bind-pose mesh: the Magreeb's `roots_v7.blend` Body, or the LOD0
of the installed GLB split into one object per texture set with `scripts/partuv_split_sets.py`. Vertices are welded
at 1e-6, because the glTF importer splits them at every old UV seam. Scripts, all in `../scripts/partuv_*`:

1. `partuv_export_mesh.py` (Blender): positions, triangles, head flag, current UVs, skin weights -> npz.
2. `partuv_run.py` (venv): non-manifold edges split as seams (PartUV's own preprocessing, face order kept),
   PartField tree once, then `partuv.pipeline_numpy` at thresholds 1.1 / 1.25 / 1.5 / 2.0. PartUV reorders faces;
   each output face is matched back to its input triangle by corner positions, and charts are the UV-connected
   pieces.
3. `partuv_scale_pack.py`: each chart is scaled to one texel density (head x1.8 on the Magreeb with its `uv_atlas_v8`
   head groups; 1.0 on the subjects' single-part sets), then packed by `partuv_xatlas_charts.py`. That script is an
   unchanged copy of `claude_shared/xatlas_charts.py`, run in `claude_shared/xatlas_venv` with the same defaults
   (brute force, 10 steps, 2048, 2 px), so only the charts differ from `uv_atlas.py`.
4. `partuv_apply_uv.py` (Blender): UVs onto the mesh, a skinned measurement GLB (one blank image per set, at the
   set's real size: 1536 x 1024 for the Hydra heads), and a neutral static upload GLB in the format of the Magreeb's
   `uv_atlas_v8.py` (mesh only, no skin, materials or attributes; checked against `magreeb_body_upload_v2.glb`).
5. Measures: `claude_shared/texture_quality.py --by-bone --heatmap --json`, plus `partuv_layout_stats.py` (seam
   length in units of sqrt(surface area), zero-area and flipped triangles) and `partuv_gap.py` (texels with another
   island within 1-3 texels: 0 within 2 on every winner, so the 2 px margin holds).
6. Baseline: `partuv_uv_atlas_baseline.py` runs `claude_shared/uv_atlas.py` (imported read-only, defaults) on the
   same set object. On the Magreeb the baseline is the installed v8 layout, re-measured through the same path:
   54.0 %, matching its README exactly.

Multi-set bodies: each texture set is its own object and its own square, and each set is one Meshy job. The Hydra
heads stay in their production arrangement: one 512 tile per head in a 3 x 2 grid of 1536 x 1024, five heads, so
83.3 % is the ceiling. Each head is unwrapped and packed into its own square (`scripts/partuv_compose_tiles.py` puts
the tiles back for measuring). The m620 head set is the right half of its 4128 x 2048 atlas, unwrapped on its own
square.

## Results

Columns are `texture_quality.py` (LOD0, at the set's image size) and `partuv_layout_stats.py`. Seam length is in
units of sqrt(surface area): lower means fewer cuts to hide. Runtime is the xatlas pack (the PartUV unwrap adds
under 5 s), or the whole run for `uv_atlas.py`. "Hybrid" means PartUV charts fed into `uv_atlas.py`'s small-chart
merge, SLIM and pack (`scripts/partuv_uv_atlas_hybrid.py`, a copy with a `charts_npz` option). "Bone tree" means
PartUV with a skin-weight part tree instead of PartField (below).

### Magreeb (6,002 triangles, head x1.8)

| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Zero-area | Seam length | Runtime |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline `uv_atlas` v8 (installed) | 54.0 | 1506 | 2020 | 1.12 | 261 | 2.1 | 1.17 | 12 | 36.5 | ~480 s |
| PartUV t1.1 | 57.0 | 1546 | 2072 | 1.09 | 280 | 2.5 | 1.09 | 0 | 37.8 | 524 s |
| **PartUV t1.25** | **57.2** | 1550 | 2078 | 1.19 | **168** | **0.9** | 1.14 | 0 | **29.1** | 328 s |
| PartUV t1.5 | 57.2 | 1549 | 2077 | 1.27 | 146 | 0.9 | 1.16 | 0 | 26.9 | 323 s |
| PartUV t2 | 59.5 | 1580 | 2118 | 1.28 | 132 | 0.7 | 1.17 | 0 | 26.3 | 333 s |
| hybrid t1.1 (merge + SLIM) | 59.2 | 1576 | 2112 | 1.11 | 215 | 1.0 | 1.13 | 0 | 35.0 | 373 s |
| bone tree t1.25 | 58.7 | 1569 | 2104 | 1.19 | 195 | 2.4 | 1.13 | 0 | 32.0 | 274 s |
| bone tree t1.1 | 58.7 | 1569 | 2104 | 1.11 | 296 | 4.2 | 1.10 | 0 | 38.6 | 323 s |
| PartUV t1.25, PartUV's own Blender pack (no head factor) | 61.7 | 1608 | 2305 | 1.13 | 167 | 0.9 | 1.14 | 0 | 29.1 | - |
| PartUV t1.25 + xatlas, no head factor (same comparison) | 58.7 | - | - | - | 168 | - | - | - | - | 250 s |
| PartUV t1.25 + Blender pack, head x1.8 | 56.8 | 1544 | 2070 | 1.19 | 168 | 0.9 | 1.14 | 0 | 29.1 | - |
| baseline v8 charts + Blender pack | 51.1 | 1465 | 1966 | 1.12 | 261 | 2.1 | 1.17 | 12 | 36.5 | - |

The hybrid t1.1 is a close second, with 2 more atlas points and an even density, but 47 more islands and 20 % more
seams. t1.25 was chosen as the upload for its cleaner layout.

### m620 Bedraggled Human, body set (5,172 triangles)

| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Zero-area | Seam length | Runtime |
|---|---|---|---|---|---|---|---|---|---|---|
| current (installed body tile, mapped to 0..1) | 50.6 | 1457 | 1186 | 1.74 | 345 | 6.9 | 2.10 | 1 | 36.8 | - |
| fresh `uv_atlas` | 57.8 | 1557 | 1379 | 1.13 | 139 | 0.2 | **2.11** | 0 | 23.9 | 413 s |
| **PartUV t1.1** | **67.2** | **1679** | 1487 | 1.08 | 172 | 2.4 | **1.10** | 1 | 21.5 | 335 s |
| PartUV t1.25 | 59.5 | 1580 | 1401 | 1.10 | 110 | 0.5 | 1.12 | 1 | 18.1 | 348 s |
| PartUV t1.5 | 61.9 | 1612 | 1429 | 1.11 | 99 | 0.4 | 1.13 | 1 | 17.7 | 357 s |
| PartUV t2 | 61.9 | 1612 | 1429 | 1.11 | 98 | 0.4 | 1.13 | 1 | 17.7 | 362 s |
| hybrid t1.1 (merge + SLIM) | 63.8 | 1636 | 1447 | 1.09 | 135 | 0.2 | 1.99 | 1 | 19.7 | 205 s |
| bone tree t1.25 | 60.2 | 1589 | 1405 | 1.14 | 110 | 0.8 | 1.14 | 1 | 18.3 | 286 s |
| bone tree t1.1 | 59.8 | 1584 | 1403 | 1.08 | 168 | 1.8 | 1.10 | 1 | 23.9 | 313 s |

The "1" zero-area triangle is degenerate in 3D in the installed mesh, so every layout has it. The xatlas packer's
atlas use is not monotonic in the chart set (t1.1 > t1.5 > t1.25), so try two or three thresholds. If fragments
must stay under 1 %, t1.5 (61.9 %) is the alternative.

### m620 head set (3,828 triangles: face, scalp volume, hair cards)

| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Zero-area | Seam length | Runtime |
|---|---|---|---|---|---|---|---|---|---|---|
| current (installed head tile, approx.) | 16.6 | 835 | 402 | 6.49 | 1600 | 45.7 | 7.86 | 0 | 50.8 | - |
| fresh `uv_atlas` | 52.5 | 1484 | 745 | 1.08 | 879 | 31.7 | 2.04 | 0 | 23.7 | 191 s |
| PartUV t1.1 | 52.3 | 1481 | 744 | 1.07 | 856 | 34.3 | 1.07 | 0 | 23.4 | 265 s |
| PartUV t1.25 | 53.4 | 1497 | 753 | 1.14 | 814 | 32.0 | 1.12 | 0 | 20.3 | 282 s |
| **PartUV t1.5** | **54.2** | 1508 | 760 | 1.21 | 780 | **29.5** | 1.24 | 0 | 17.5 | 253 s |
| PartUV t2 | 55.0 | 1518 | 766 | 1.23 | 767 | 28.9 | 1.28 | 0 | 16.1 | 276 s |

The "current" row maps the right half of the 4128 px image (u 0.5-1) to a square. The real head tile starts at
2080 px, so treat that row as approximate. The fragments are hair cards: one 2,808-triangle component carries
2,778 open edges. Fixing that needs a hair-card-aware chart rule (one chart per card strip) or a closed hair volume,
not a different unwrapper.

### BHydra body set (3,289 triangles, 23 non-manifold edges)

| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Zero-area | Seam length | Runtime |
|---|---|---|---|---|---|---|---|---|---|---|
| current (installed) | 50.6 | 1457 | 1156 | 1.87 | 83 | 1.1 | 1.75 | 1 | 18.5 | - |
| fresh `uv_atlas` | 57.0 | 1546 | 1237 | 1.08 | 150 | 2.1 | 1.14 | 0 | 25.6 | 492 s |
| PartUV t1.1 | 65.1 | 1652 | 1325 | 1.08 | 180 | 4.6 | 1.08 | 0 | 22.7 | 334 s |
| PartUV t1.25 | 61.2 | 1602 | 1286 | 1.14 | 140 | 3.3 | 1.11 | 0 | 18.8 | 273 s |
| **PartUV t1.5** | **62.6** | 1621 | 1300 | 1.16 | 132 | **3.0** | 1.12 | 0 | 17.6 | 270 s |
| PartUV t2 | 62.6 | 1621 | 1299 | 1.16 | 130 | 3.2 | 1.12 | 0 | 17.3 | 254 s |
| hybrid t1.1 (merge + SLIM) | 64.2 | 1641 | 1316 | 1.08 | 168 | 4.2 | 1.15 | 0 | 21.8 | 383 s |
| bone tree t1.25 | **69.5** | 1707 | 1369 | 1.24 | 132 | 4.4 | 1.12 | 0 | 17.8 | 239 s |
| bone tree t1.1 | 64.6 | 1646 | 1320 | 1.09 | 158 | 4.9 | 1.09 | 0 | 21.8 | 266 s |

PartUV leaves 3-5 % of the Hydra body on fragments: spikes and the non-manifold seams it cuts open. Only t1.5 / t2
stay within 3 %. The bone tree reaches 69.5 %, the 70 % ideal, but with 4.4 % fragments.

### BHydra heads set (4,637 triangles, five heads in 512 tiles of 1536 x 1024; ceiling 83.3 %)

| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Zero-area | Seam length | Runtime |
|---|---|---|---|---|---|---|---|---|---|---|
| current (installed) | 42.9 | 1006 | 884 | 1.54 | 955 | 24.5 | 1.72 | 0 | 59.1 | - |
| fresh `uv_atlas` per tile | 42.3 | 999 | 927 | 1.24 | 302 | 5.5 | 1.58 | 0 | 31.4 | 13 s |
| PartUV t1.1 per tile | 44.3 | 1022 | 925 | 1.28 | 327 | 9.7 | 1.14 | 0 | 34.6 | 20 s |
| PartUV t1.25 per tile | **47.5** | 1059 | 947 | 1.32 | 247 | 7.7 | **1.22** | 0 | 28.1 | 20 s |
| PartUV t1.5 per tile | 46.2 | 1044 | 930 | 1.35 | 226 | 7.1 | 1.23 | 0 | 26.7 | 20 s |
| PartUV t2 per tile | 45.3 | 1034 | 923 | 1.37 | 202 | 6.7 | 1.25 | 0 | 25.2 | 20 s |
| **hybrid t1.25 per tile** | 46.4 | 1046 | 940 | 1.32 | **201** | **4.2** | 1.62 | 0 | 24.8 | 15 s |

The spread here includes the scale differences between heads (one square each). Neither PartUV row meets every
target. Plain t1.25 keeps stretch at 1.22 but has 7.7 % fragments. The hybrid trades stretch (1.62, a visible
gradient in tile 3 of `mm6_hyd/uv_layout_compare_heads.png`) for 4.2 % fragments. The hybrid was prepared as the
upload because fragments are what Meshy paints as blotches. Use plain t1.25 if stretch should win.

## Further findings

- **A bone-weight part tree instead of PartField works, under a clean licence.** `partuv_run.py <npz> <out> bones`
  builds the hierarchy that PartUV expects: Ward agglomerative clustering over edge-adjacent faces, as PartField's
  tree uses, on per-face skin weights plus 0.5 x normalised position. No PartField, no NVIDIA licence and no 1.2 GB
  checkpoint (PAMO still uses CUDA unless disabled). Its results are close to PartField's, a little above it in atlas
  and a little worse on fragments: Magreeb 58.7 % / 2.4 %, m620 60.2 % / 0.8 %, Hydra 69.5 % / 4.4 %. Every creature
  has a rig, so this is the version to adopt if PartField's licence is a concern.
- **The SLIM merge (`uv_atlas.py` step 2) causes the stretch.** On PartUV charts it lowers fragments
  (m620 2.4 -> 0.2 %, Hydra heads 7.7 -> 4.2 %), but stretch p90 returns to 1.6-2.0 on two of the four sets. Merging
  should keep a per-chart stretch limit (`max_stretch=1.5`, an existing option) when it is applied to PartUV charts.
- **Packing (for candidate 4).** Blender 5.3's `pack_islands` on PartUV charts packs as well as the xatlas brute force
  (56.8 vs 57.2 % with the head factor; 61.7 vs 58.7 % without), in seconds instead of 4-6 minutes. On the old v8
  xatlas charts it falls to 51.1 %, so the packer's ranking depends on the charts. Blender's packer must run on a mesh
  whose material has no non-square image: the m620 sets still referenced the 4128 x 2048 texture, and the packer's
  aspect correction squashed every island (stretch 4+). Those runs are discarded.
- **PartUV's own packing** (`pack_islands(margin=0.001)` on the unpacked charts) reached 61.7 % on the Magreeb.
  PartUV's charts come out at one common scale, so `average_islands_scale` changes nothing. It has no head factor and
  no exact pixel margin, so it is not a drop-in replacement.

## Images (looked at)

- `magreeb/heat/uv_layout_compare.png`: UV-space density, baseline v8 against PartUV t1.25, on one scale (green =
  baseline median 2020, red = head x1.8). PartUV has fewer, larger part-shaped islands and slight density mottling
  inside charts. Its packed square leaves a free right column of about 4 %.
- `magreeb/uv_layout_compare_hybrid.png`: baseline against the hybrid t1.1.
- `magreeb/heat/views_baseline_v8.png`, `magreeb/heat/views_partuv_t1.25.png`: density on the model (front, 3/4,
  side, back). Both are even, the head is red as designed, and PartUV shows faint mottling on the carapace.
- `mm8_m620/heat/uv_layout_compare_body.png`, `views_uv_atlas_body.png`, `views_partuv_body_t1.1.png`,
  `views_current_body.png` (reference = fresh `uv_atlas` median 1379). The `uv_atlas` layout has a blue-to-red
  gradient along the shins: a SLIM-merged leg strip, the source of its stretch of 2.11. The PartUV layout is uniformly
  green.
- `mm6_hyd/uv_layout_compare_body.png`, `mm6_hyd/uv_layout_compare_heads.png`.
- Per-layout UV-space density and stretch maps: `*/measure/*_density.png`, `*_stretch.png`.

## Candidate uploads (neutral static, nothing submitted)

All are in the format of the baseline upload: mesh only, Y up, `TEXCOORD_0`, no skin, materials or attributes.
Each blend next to an upload holds the UVs on the rigged object for the later map rebuild.

- Magreeb: `magreeb/upload/magreeb_body_upload_partuv_t1.25.glb` (6,002 triangles, 57.2 %, 168 islands), with
  `uv_partuv_t1.25.blend`. Drop-in for `requests/retexture_v2.json` (same HD masters).
- m620 body: `mm8_m620/upload/m620_body_upload_partuv_t1.1.glb` (5,172 triangles, 67.2 %), with
  `uv_partuv_body_t1.1.blend`.
- m620 head: `mm8_m620/upload/m620_head_upload_partuv_t1.5.glb` (3,828 triangles, 54.2 %), with
  `uv_partuv_head_t1.5.blend`.
- Hydra body: `mm6_hyd/upload/hyd_body_upload_partuv_t1.5.glb` (3,289 triangles, 62.6 %), with
  `uv_partuv_body_t1.5.blend`.
- Hydra heads: `mm6_hyd/upload/hyd_head_tile{0,1,3,4,5}_upload_hybrid_t1.25.glb` (one per head, each filling its own
  square), UVs in `mm6_hyd/hybrid/hybrid_tile*_t1.25.blend`. Caveats: tile k = column + 3 x row of the current heads
  image (Blender v); which head each tile is still has to be matched to `requests/head<k>_*`. The heads are in their
  body position, not in the head-fit frame the production route uploaded (`texturing/head<k>_st_upload.glb`), so
  check what the Meshy multiview camera expects before painting.
- **Never re-run the packs** for these uploads (TEXTURE_QUALITY_PASS: xatlas packs differently per run). The packed
  npz files in `*/packed/` are the record.

## Proposed change (not applied)

1. Add `charts='partuv'` to `claude_shared/uv_atlas.py`. It would take the charts from a PartUV run in its own venv
   (as `xatlas_charts.py` does), with the part tree from skin weights by default (licence-clean) and PartField as an
   option. It would skip the SLIM merge by default, or keep it under `max_stretch=1.5`, then apply the existing density
   step and xatlas pack. Run thresholds 1.1, 1.25 and 1.5, and keep the best that meets the targets (packing is not
   monotonic). `scripts/partuv_run.py`, `partuv_scale_pack.py` and `partuv_uv_atlas_hybrid.py` are the working
   prototype.
2. In TEXTURE_QUALITY_PASS.md: mention per-set unwrapping for multi-set bodies (one square per Meshy job; the Hydra
   heads as one square per head), and the hair-card limitation.
3. Before adopting, one paired paint (baseline upload against PartUV upload, same masters) together with candidate
   6's noise-floor pair.

## Process notes

- **Leases.** `SUBJECTS.md`'s claim command (`--project .../uv_research_20261111/<model>`) is refused: "Claim the
  top-level creature project; select its branch through --state". The working form is `--project
  level_generation/creatures/uv_research_20261111 --state partuv/<model>/creature_3d_progress.json`. That lease
  covers the whole research folder: while it is held, `tools/run_creature_blender.sh` works only with its token, for
  every researcher, and only one identity can be held at a time. I held `mm8:m620`, then `mm6:hyd`, then `mm8:m620`
  again for short windows, and released all of them (none active now).
- Disk: `venv/` 8.1 GB and `weights/` 1.6 GB, both git-ignored. Delete them when the study closes, unless the
  prototype is adopted.
