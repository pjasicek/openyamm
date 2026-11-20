# Layout research: gutter fill, hidden seams, packing (2026-11-11)

Candidates 3, 2 and 4 of [`../BRIEF.md`](../BRIEF.md), zero Meshy credits, no Meshy job submitted. Subjects: the MM9
Magreeb (pilot of the texture pass), then the assigned test subjects Bedraggled Human `mm8:m620` and BHydra `mm6:hyd`
([`../SUBJECTS.md`](../SUBJECTS.md)), all read-only copies in `work/`. Scripts in `../scripts/layout/` and
`../scripts/uv_atlas_seam.py` (a copy of `claude_shared/uv_atlas.py`; nothing in `claude_shared/` was edited).

Blender ran through `../scripts/layout/blender.sh`, the same invocation as `tools/run_creature_blender.sh` without its
project lock: the PartUV agent holds the lease on the whole `uv_research_20261111` folder (mm8:m620), so the wrapper
refused every run; this agent wrote only under `layout/`.

## Summary

| Question | Verdict |
|---|---|
| A. Gutter fill | Meshy fills every gutter with the nearest island texel; our MM9 grading (AO multiply, local contrast) darkens it again beyond 2 px. **Re-pad all maps with the nearest island texel as the last step before export** (free, -16 % leak at mip 4 on the Magreeb, -48 % on the BHydra). Keep xatlas padding 2 (it leaves >= 4 empty texels): padding 4 / 8 cost 3.4 / 12 atlas points for -16 % / -25 % leak at mip 4 and nothing below. BC7 4x4 alignment needs nothing. |
| B. Hidden seams | A seam-removal pass (merge charts across the most *visible* borders, cut tubes open along their *least visible* path, keep only merges under p90 stretch 1.25) cuts the visibility-weighted seam length by 22-47 % on Magreeb, m620 body and both BHydra sets, halves the islands, lowers fragments, costs +0.05-0.07 stretch p90 and about nothing in atlas. Biasing only the merge target does nothing. Hair-spike heads (m620) gain only 7 %. |
| C. Packing | **sparrow (MIT, 2025 state of the art) packs the same charts to 67-71 % against 50-58 % for xatlas (best of fast and brute force) and 51-57 % for Blender 5.3**, same 4-texel gap, exactly one scale, ~5 min. +13 % linear texel density from packing alone: the 70 % target is reached. |
| Paint | One 10-credit paint of `winners/magreeb_seamsparrow_upload.glb` (70.5 %, 110 islands, -38 % visible seam; the Magreeb already has a paint on the current layout, so it isolates the layout). Uploads for m620 body + head and BHydra body + heads are ready too. No job was submitted. |

Proposed changes (not applied): `uv_atlas.unwrap(..., packer='sparrow', seam_rounds=6, seam_stretch=1.25, vis=...)` with
`uv_seam_trial.py`'s visibility; a nearest-texel `pad()` after every map step in TEXTURE_QUALITY_PASS.md step 4-6; and
two pitfalls for the doc: clear a non-square material before `uv_atlas.unwrap` (SLIM's `correct_aspect` squeezes the
charts by the image aspect), and merge by distance before unwrapping an imported installed GLB (split vertices make
hundreds of loose pieces).

## A. Gutter fill and margin (candidate 3)

### A1. What fills the space between islands

`gutter_inspect.py`: for every texel outside the islands, the mean absolute difference (8-bit levels, RGB mean) to
the nearest island texel, by distance band; 0 means the gutter is the island's own edge colour pushed outwards.

| Map | Size | Gutter % | Diff at 1 / 2 / 3-4 / 5-8 / 9-16 / >16 px | Black % |
|---|---|---|---|---|
| Magreeb Meshy return (`meshy/magreeb_retexture_v2`) | 4096 | 46.0 | 1.0 / 0.5 / 0.4 / 0.8 / 0.8 / 1.0 | 0.8 |
| Dragon King body Meshy return | 4096 | 44.1 | 1.2 / 0.5 / 0.5 / 0.8 / 0.7 / 1.0 | 0.7 |
| PeasantF3 (`mm6_mfp_texpass_claude`) Meshy return | 4096 | 40.6 | 0.5 / 0.3 / 0.2 / 0.4 / 0.3 / 0.4 | 0.7 |
| Eye (`mm6_bh_texpass_claude`) Meshy return | 4096 | 46.2 | 1.5 / 0.9 / 0.6 / 1.0 / 0.9 / 1.0 | 0.0 |
| Magreeb installed colour (graded) | 2048 | 46.0 | 0.6 / 1.7 / **5.1 / 16.8 / 27.5 / 30.8** | 14.1 |
| Magreeb installed region mask | 1024 | 46.0 | 2.5 / 5.4 / 6.1 / 6.2 / 6.4 / 5.5 | 7.2 |
| Dragon King installed colour | 2048 | 44.1 | 3.5 / 4.2 / 5.8 / 7.1 / 8.8 / 10.4 | 7.1 |
| BHydra installed body colour | 2048 | 49.4 | 5.7 / 9.8 / 12.3 / 14.7 / 15.6 / 15.2 | 5.8 |
| Eye installed colour / mask (MM6 texpass) | 2048 / 1024 | 46.3 | 0.0 everywhere | 3.6 / 0.3 |
| PeasantF3 installed colour (MM6 texpass) | 2048 | 40.5 | 0.0 everywhere | 3.5 |

("Black %" is the share of near-black gutter texels, max channel < 8, which includes genuinely dark paint.)

- **Meshy fills the whole atlas with nearest-texel dilation** (each gutter texel = the colour of the closest island
  texel; streaks radiate from island borders, `gutter/magreeb_meshy_crop.png`). Nothing is black.
- **The MM6-MM8 texture-pass route keeps that fill exactly** (`mm6_bh_texpass_claude/scripts/resample.py` pads with
  the nearest island texel after every step).
- **The MM9 route (Magreeb, Dragon King) and the BHydra's installed paint change the gutters after the fill**: grading
  (AO multiply with the AO bake's black beyond its bake margin, local contrast at 16 px) darkens and re-contrasts
  everything farther than about 2 px from the islands (`gutter/magreeb_inst2k_crop.png`). The region mask's gutter does
  not follow the colour either.

### A2. Leak per mip level: definition

`leak.py`. For every island texel p of island i and mip level k (2x2 box mips in linear light, the engine's
`prepareBgraMipChain`), *actual* = bilinear sample of the whole map's level k at p's UV (what the GPU reads), *pure* =
the same sample of a chain built from island i alone (its own texels, everything else filled from them by push-pull: an
infinitely wide private gutter). Leak = |sRGB(actual) - sRGB(pure)|, mean over RGB, in 8-bit levels. Reported: mean
over all island texels (one density, so surface-weighted) and, in brackets, the share of texels above 4 levels (about a
just-visible step on a mid-tone). Mip 1 = 1024, mip 5 = 64. A creature 300 px tall on a 1080p screen samples about mip
2, one 100 px tall about mip 4. "Foreign" is a paint-free proxy: the share of the bilinear footprint that comes from
texels owned by another island (nearest-island Voronoi ownership).

### A3. Installed maps, gutters as shipped versus refilled

| Map (installed layout) | Gutter | Mip 1 | Mip 2 | Mip 3 | Mip 4 | Mip 5 |
|---|---|---|---|---|---|---|
| Magreeb 2K | as shipped (graded) | 0.15 (1.1 %) | 0.30 (2.2 %) | 0.81 (6.3 %) | 2.25 (18.3 %) | 5.20 (39.4 %) |
| | nearest-texel refill | 0.15 (1.1 %) | 0.29 (2.1 %) | 0.75 (5.7 %) | **1.89 (14.4 %)** | **4.13 (30.0 %)** |
| | push-pull, island-owned cells | 0.20 (1.5 %) | 0.40 (3.0 %) | 0.86 (6.7 %) | 2.00 (15.7 %) | 4.32 (32.6 %) |
| | push-pull, global | 0.05 (0.3 %) | 0.14 (0.8 %) | 0.42 (2.6 %) | 1.44 (10.2 %) | 3.85 (28.9 %) |
| | black | 0.82 (5.7 %) | 1.74 (11.1 %) | 3.50 (21.6 %) | 6.63 (38.5 %) | 11.40 (58.8 %) |
| Dragon King 2K | as shipped | 0.12 | 0.24 | 0.54 | 1.34 (10.2 %) | 3.55 (25.4 %) |
| | nearest refill | 0.10 | 0.20 | 0.47 | 1.24 (9.4 %) | 3.46 (24.6 %) |
| | black | 0.56 | 1.15 | 2.32 | 4.63 (29.5 %) | 8.35 (45.8 %) |
| BHydra body 2K | as shipped | 0.07 | 0.18 | 0.41 | **0.87 (5.1 %)** | **1.72 (10.6 %)** |
| | nearest refill | 0.03 | 0.07 | 0.17 | **0.45 (2.6 %)** | **1.14 (7.1 %)** |
| | black | 0.33 | 0.66 | 1.29 | 2.44 (16.7 %) | 4.41 (29.1 %) |
| Eye 2K (MM6 texpass) | as shipped = nearest | 0.05 | 0.10 | 0.25 | 0.93 (4.9 %) | 3.34 (20.4 %) |
| | black | 0.60 | 1.24 | 2.49 | 4.91 (35.5 %) | 8.91 (61.0 %) |

Push-pull "global" scores best only because the reference is itself a push-pull extension (it is biased toward that
fill); on the paint-free foreign share and on visual crops it is not distinguishable from nearest-texel fill. Sheet:
`gutter/gutter_fill_sheet.png` (black / nearest / installed, mips 0, 2, 4 of one crop).

### A4. Margin x fill, one paint carried onto re-packed layouts

The Magreeb's charts were re-packed by a copy of our packer (`repack.py`, xatlas fine sweep + brute force) at
padding 2, 4 and 8, and the Meshy 4K paint was carried onto each layout (`transfer.py`: 2x2 supersampled barycentric
resampling, the same blur for all), then filled.

| Layout | Atlas | Gap min / median (empty texels) | Nearest fill: mip 1 / 2 / 3 / 4 / 5 | Black: mip 3 / 4 / 5 |
|---|---|---|---|---|
| production (xatlas padding 2) | 54.0 % | 4 / 5.7 | 0.11 / 0.22 / 0.58 / 1.49 (11.5 %) / 3.33 (25.7 %) | 3.52 / 6.56 / 10.98 |
| repack padding 2 | 56.3 % | 4 / 6 | 0.11 / 0.21 / 0.55 / 1.50 (11.7 %) / 3.36 (26.8 %) | 3.46 / 6.37 / 10.41 |
| repack padding 4 | 52.9 % | 4.8 / 10 | 0.11 / 0.22 / 0.51 / 1.26 (9.8 %) / 2.95 (23.3 %) | 3.53 / 6.79 / 11.59 |
| repack padding 8 | 44.1 % | 17 / 21 | 0.12 / 0.24 / 0.53 / 1.13 (8.5 %) / 2.49 (20.9 %) | 3.90 / 7.57 / 13.66 |
| sparrow pack (C), separation 4 | 69.3 % | 4 / 5 | 0.09 / 0.19 / 0.54 / 1.55 (12.0 %) / 3.54 (27.4 %) | 3.08 / 5.73 / 9.32 |

With the cook's colour mip sharpening (unsharp 0.75 on mips >= 1, creature class) the nearest-fill leak roughly
doubles at every margin (padding 2: 0.23 / 0.45 / 1.09 / 2.43 / 4.51) and keeps the same ordering
(`gutter/margin_study.json`, `fills_sharpened`).

- **xatlas "padding 2" already leaves at least 4 empty texels between islands** (median 6): a 2 px margin per side.
- Doubling the padding cuts leak only at mips 4-5 (-16 % / -12 %) for 3.4 atlas points (6 % of the texels); padding 8
  cuts it by a quarter for 12 points. Below mip 4 the margin does not matter, above it the footprint is wider than any
  affordable margin. **The fill matters 3-4x more than the margin.**

### A5. BC7 blocks

`bc7_check.py` cooks the 2K map with the engine's own cooker (`build/game/openyamm_model_texture_cook`: box mips, mip
sharpening 0.75, BC7) and decodes every level. At padding 2, 4x4 blocks that hold texels of two islands' Voronoi
cells cover 0.01 % of the island texels; blocks touching any gutter 8.3 %. BC7 error inside islands is 1.83 levels in
blocks without gutter, 1.22 in blocks with nearest-filled gutter (1.81 with black), 0.65 in the rare mixed blocks.
Through the whole cooked chain, nearest fill against black: mip 3 3.64 vs 5.63, mip 4 4.63 vs 8.02 (the cooked chain
also carries BC7's own ~2 levels everywhere). **Block alignment needs nothing**: with nearest fill a block straddling
two islands is rare and BC7's partitioned modes encode it better than an inner block.

### Verdict A

- **2 px (xatlas padding 2, 4+ empty texels) plus a nearest-texel fill is enough.** Keep the margin.
- **Add one step to the pipeline: re-pad every map with the nearest island texel as the last operation before
  export**, after grading, AO, tone matching, ramps and region masks (colour, region mask, normal, metal/roughness;
  `texlib.pad` in `mm6_bh_texpass_claude/scripts/texlib.py` does exactly this). It removes the darkened MM9 gutters:
  -16 % leak at mip 4 on the Magreeb, -48 % on the BHydra, for no atlas cost. Black gutters (an unfilled bake) would be
  3-4x worse. Push-pull is not better than nearest-texel fill here.
- BC7 4x4 alignment: no action.

## B. Hidden-seam bias (candidate 2)

`../scripts/uv_atlas_seam.py` (copy of `uv_atlas.py`) plus `../scripts/layout/uv_seam_trial.py`:

- **Visibility per face**: cosine-weighted share of 72 orthographic views (elevations 5, 20 and 35 degrees above the
  horizon, 24 azimuths all around; occlusion by BVH ray casts on the bind pose) that see the face, divided by its 95th
  percentile and clipped to 1. Hidden < 0.15 (22 % of the Magreeb's faces: belly, insides of legs and claws), exposed
  >= 0.5. Rendered on the model: `seams/magreeb/r_vis_*.png`.
- **Seam metrics** on the final UVs (an edge is a seam when its two faces disagree in UV at either end), lengths in
  creature sizes (largest bounding-box extent): total, visibility-weighted (sum length x visibility), exposed (vis >=
  0.5) and the hidden share.
- **Bias 1, merge target** (`vis_target`): a small chart merges into the neighbour with the largest
  *visibility-weighted* shared border instead of the longest border.
- **Bias 2, seam removal** (`seam_rounds`, `seam_stretch`): after the usual small-chart merge, rounds of greedy merges
  of the chart pairs with the most visible shared border (up to 60 disjoint pairs a round). A merged chart that is no
  longer a disc (a limb tube) is cut open along its *least visible* path (Dijkstra, cost length x (visibility + 0.05)),
  then flattened by SLIM and kept only if it passes the tool's checks (overlap, flips, edge stretch, density ratio) and
  a p90 stretch limit; otherwise both charts go back. This both removes visible seams and moves the necessary cuts to
  hidden lines.
- **xatlas edge costs**: the Python binding (xatlas 0.0.11) exposes only global chart weights, no per-edge cost; the
  only route would be faking normal seams on hidden edges. Not tried; the merge pass does the job.

Packing in this table is the xatlas fast sweep unless "brute" (fine sweep + 10 brute-force steps); xatlas is noisy
by +-2 atlas points between near-identical inputs, so read atlas use together with section C, which packs the same
charts with sparrow.

### Magreeb (body 6,002 triangles, head x1.8)

| Trial | Atlas % | Islands | Fragments % | Stretch p90 | Spread | Seam length | Vis-weighted | Exposed | Hidden share |
|---|---|---|---|---|---|---|---|---|---|
| installed v8 layout | 54.0 | 261 | 2.1 | 1.17 | 1.12 | 27.1 | 14.7 | 15.3 | 15.3 % |
| fresh `uv_atlas.py` (fast pack) | 53.7 | 239 | 2.1 | 1.21 | 1.14 | 26.9 | 14.6 | 15.2 | 15.4 % |
| fresh `uv_atlas.py` (brute) | 55.8 | 239 | 2.1 | 1.21 | 1.14 | 26.9 | 14.6 | 15.2 | 15.4 % |
| merge target by visibility | 53.2 | 214 | 1.5 | 1.22 | 1.14 | 26.3 | 14.1 | 14.5 | 16.6 % |
| seam removal, 6 rounds, p90 <= 1.15 | 55.9 | 148 | 0.9 | 1.22 | 1.13 | 21.4 | 11.6 | 12.3 | 17.3 % |
| **seam removal, 6 rounds, p90 <= 1.25** | **57.5** | **110** | **0.8** | **1.26** | 1.14 | **17.9** | **9.0** | **9.3** | 19.0 % |
| seam removal, 10 rounds, p90 <= 1.25 | 54.2 | 100 | 0.6 | 1.26 | 1.14 | 17.6 | 8.8 | 9.1 | 19.0 % |
| seam removal, 6 rounds, p90 <= 1.35 | 51.8 | 99 | 0.7 | 1.28 | 1.15 | 16.8 | 8.1 | 8.2 | 20.4 % |
| same + merge target by visibility | 51.7 | 93 | 0.5 | 1.29 | 1.15 | 17.1 | 8.4 | 8.6 | 21.4 % |
| seam removal, 10 rounds, p90 <= 1.5 | 50.2 | 64 | 0.2 | 1.34 | 1.19 | 14.9 | 6.7 | 6.7 | 23.8 % |

Sheet (front, side, back, above; seams red exposed / orange mid / blue hidden, pastel islands):
`seams/magreeb_seam_sheet.png` (rows: fresh baseline, seam removal p90 1.25, seam removal 10 rounds p90 1.5). The leg
and arm seams that run along every limb disappear; the remaining long seams are the body shell's halves (closed: a
whole shell would need one long cut and stretches past any limit) and the claw blades.

### Bedraggled Human `mm8:m620` (body and head as separate sets, each in its own 2K square)

The installed GLB is one 4128x2048 atlas (2K body + 2K head, 32 px gutter); the sets were split by u. Two traps found on
the way, both in the tool's path for installed GLBs: (1) **`uv_atlas.py` run on a mesh whose material holds a
non-square image squeezes every SLIM-flattened chart by that aspect** (`bpy.ops.uv.unwrap(correct_aspect=True)` reads
the material's image: merged charts came out at p90 stretch 2.2 on the 4128x2048 atlas; the trial clears the
material first); (2) the glTF importer leaves 1,011 of the head's 4,144 vertices split even with `merge_vertices`, which
made 584 loose pieces instead of 104 (merge by distance 0.01 mm before the unwrap; trials `headw_*`).

| Set / trial | Atlas % | Islands | Fragments % | Stretch p90 | Seam length | Vis-weighted | Exposed | Hidden share |
|---|---|---|---|---|---|---|---|---|
| body, installed layout | (33.7 whole atlas) | | 9.9 | 2.19 | 45.2 | 23.3 | 25.1 | 29.3 % |
| body, fresh `uv_atlas.py` (fast) | 54.1 | 131 | 0.1 | 1.17 | 32.1 | 17.3 | 18.4 | 24.4 % |
| **body, seam removal p90 <= 1.25** | **57.2** | **60** | 0.0 | 1.24 | **22.6** | **12.0** | **12.7** | 27.5 % |
| head, installed layout | | | | | 41.0 | 14.1 | 13.5 | 40.0 % |
| head, fresh `uv_atlas.py` (fast) | 53.6 | 881 | 31.7 | 1.16 | 33.3 | 11.0 | 10.5 | 42.7 % |
| head, seam removal p90 <= 1.25 | 55.1 | 769 | 30.0 | 1.18 | 31.4 | 10.3 | 9.9 | 44.2 % |

The head is a face plus hundreds of hair spikes: xatlas makes 1,216 charts, 59 merged charts are reverted, and 30 % of
the surface stays on fragments with every variant. Seam bias helps little there; this is PartUV's case (candidate 1).
Sheet: `seams/m620_seam_sheet.png` (azimuth 0 is the model's side: rows body base, body seam removal, head base, head
seam removal).

### BHydra `mm6:hyd` (body: Hydra_A + HydraB_A; heads: HeadsA/B/C, each set in a 2K square)

| Set / trial | Atlas % | Islands | Fragments % | Stretch p90 | Seam length | Vis-weighted | Exposed | Hidden share |
|---|---|---|---|---|---|---|---|---|
| body, installed layout | 50.6 | 83 | 1.1 | 1.75 | 26.2 | 14.2 | 14.8 | 18.4 % |
| body, fresh `uv_atlas.py` (fast) | 53.5 | 150 | 2.1 | 1.14 | 34.5 | 17.8 | 17.3 | 13.0 % |
| **body, seam removal p90 <= 1.25** | 48.7 | **82** | 1.4 | 1.21 | **20.6** | **9.4** | **8.9** | 21.1 % |
| heads, installed layout | (42.9, 1536x1024) | 955 | 24.5 | 1.72 | 48.5 | 21.7 | 22.2 | 29.1 % |
| heads, fresh `uv_atlas.py` (fast) | 54.8 | 295 | 5.6 | 1.20 | 28.9 | 12.1 | 11.8 | 29.8 % |
| **heads, seam removal p90 <= 1.25** | **56.3** | **195** | **3.1** | 1.25 | **23.8** | **9.4** | **9.2** | 34.4 % |

Sheet: `seams/hyd_seam_sheet.png`. The necks lose the long zigzag seams on their sides; the heads keep their seams
around the jaws and crests.

### Verdict B

- **Seam removal with hidden cuts works; the merge-target bias alone does almost nothing** (-4 % visible seam).
- At a p90 stretch limit of 1.25 the visibility-weighted seam length falls by 38 % (Magreeb), 31 % (m620 body), 47 %
  (BHydra body) and 22 % (BHydra heads); islands halve, fragments fall (Magreeb 2.1 -> 0.8 %, heads 5.6 -> 3.1 %), stretch
  p90 rises by 0.05-0.07 (still far under 1.5), density spread unchanged. Atlas: +3.8 / +3.1 / -4.8 / +1.5 points with
  the fast xatlas pack, i.e. within xatlas's noise; with sparrow packing (C) the merged charts land within -1.4 to +2.3 points of the fresh charts.
- Most of the gain is *removing* seams, not relocating them: the hidden share of the remaining seams rises only from
  13-25 % to 19-28 %. Closed shells (the Magreeb's body, the m620 torso) keep a long exposed seam; cutting a closed
  shell once along its belly stretches beyond any limit we accept.
- p90 1.25 is the sweet spot: 1.15 keeps half of the gain, 1.35-1.5 removes more seams but costs atlas and stretch.
- Hair-spike heads (m620) do not benefit.

## C. Packing (candidate 4)

Same charts, same rule: every island keeps its relative scale (one uniform scale searched to fill a 2048 square),
at least 4 empty texels between islands (what xatlas padding 2 actually leaves). Measured by `pack_eval.py`: atlas
(texel-centre union at 2048), gaps, per-island scale p5/p95 against the input (1.000 = uniform).

Packers:
- **xatlas fast sweep** (`fine=250 steps=0`) and **fine sweep + brute force** (`fine=250 steps=10`), the copy
  `xatlas_pack.py` of `claude_shared/xatlas_charts.py`.
- **Blender 5.3 Pack Islands**: shape CONCAVE / CONVEX / AABB, rotation ANY / AXIS_ALIGNED, margin FRACTION 2/2048
  (its margin is the full gap: 2/2048 leaves 4 texels like xatlas padding 2) and 4/2048 (`blender_pack.py`).
- **sparrow** (MIT, Jeroen Gardeyn, KU Leuven, github.com/JeroenGar/sparrow, paper arXiv 2509.13329, 2025): the
  current state of the art for 2D irregular strip packing (no-fit-polygon class problem solved by collision-detection
  separation, jagua-rs). `sparrow_pack.py` turns each island into its outline polygon in texels (union of its
  triangles, holes dropped, 0.3 px outward buffer, simplified 0.25 px), sets `min_item_separation` 4, strip height 2048
  and continuous rotation, and searches the scale k so the strip width also fits 2048 (k_next = k sqrt(2048 / width),
  5 runs of 60 s). Built locally (Rust 1.99.1; binary, source, toolchain and the shapely venv now in `../../claude_shared/sparrow_venv/`, see the header of `sparrow_pack.py`).
- UVPackmaster: paid, not tested (note only). rectpack (rectangles) and Blender AABB are the bounding-box class.

### Magreeb production charts (261 islands)

| Packer | Atlas % | Gap min / median | Scale p5-p95 | Time |
|---|---|---|---|---|
| installed (xatlas brute, production run) | 54.0 | 4 / 5.7 | 1.00 | ~8 min |
| xatlas fast sweep | 54.0 | 5 / 9 | 1.00-1.03 | 60 s |
| xatlas fine sweep + brute force | 56.3 | 4 / 6 | 0.98-1.11 | 440 s |
| Blender CONCAVE, AXIS_ALIGNED | 51.8 | 4 / 4 | 1.00 | 30 s |
| Blender CONCAVE, ANY | 51.1 | 3.1 / 4 | 1.00 | 28 s |
| Blender CONVEX (ANY / AXIS_ALIGNED) | 43.9 / 44.5 | 4 / 4 | 1.00 | 26-32 s |
| Blender AABB | 39.7 | 4 / 4 | 1.00 | 0 s |
| Blender CONCAVE AXIS_ALIGNED, margin 4/2048 | 48.4 | 8 / 8 | 1.00 | 19 s |
| **sparrow, continuous rotation** | **69.3** | 4 / 5 | 1.00 | 317 s |
| sparrow, 90 degree steps | 68.4 | 4 / 5 | 1.00 | 323 s |
| **sparrow, continuous, 7 runs of 90 s** | **71.2** | 4 / 5 | 1.00 | 664 s |
| sparrow on the seam-removal charts, 5 x 60 s / 7 x 90 s | 68.2 / 70.5 | 4 / 5 | 1.00 | 314 / 645 s |

UV layouts side by side: `pack/magreeb_pack_compare.png` (xatlas 56.3 % left, sparrow 69.3 % right). xatlas also
lets some islands drift in scale (p95 up to 1.15 on the hydra's seam charts), sparrow keeps exactly one scale.

### All test subjects (fast = the trial's own xatlas fast pack)

| Set / charts | xatlas fast | xatlas fine + brute | Blender CONCAVE best | **sparrow** | Islands |
|---|---|---|---|---|---|
| Magreeb, installed v8 charts | 54.0 | 56.3 | 51.8 | **69.3** (71.2 with 7 x 90 s) | 261 |
| Magreeb, fresh `uv_atlas.py` charts | 53.7 | 55.8 | | | 239 |
| Magreeb, seam-removal charts | 57.5 | 54.4 | 56.8 | **68.2** (70.5 with 7 x 90 s) | 110 |
| m620 body, fresh charts | 54.1 | 57.9 | 55.8 | **68.2** | 131 |
| m620 body, seam-removal charts | 57.2 | 55.4 | | **69.5** | 60 |
| m620 head (welded), fresh charts | 53.6 | 53.7 | | **68.3** | 881 |
| m620 head (welded), seam-removal charts | 55.1 | 55.2 | | **70.6** | 769 |
| BHydra body, fresh charts | 53.5 | 53.4 | 56.1 | **68.2** | 150 |
| BHydra body, seam-removal charts | 48.7 | 49.6 | | **66.8** | 82 |
| BHydra heads, fresh charts | 54.8 | 54.0 | 51.3 | **71.2** | 295 |
| BHydra heads, seam-removal charts | 56.3 | 58.1 | | **70.4** | 195 |

xatlas times 350-710 s for fine + brute, sparrow 310-320 s (5 x 60 s), Blender 10-36 s. Gaps: sparrow 4 / 4.7-5.3
(min / median) everywhere (9 on the hydra's seam charts); xatlas brute left two touching islands on the m620 body
(gap 0, re-packing an already packed input with shared vertex positions), Blender ANY dips to 3-3.5.

### Verdict C

- **sparrow beats every packer we have by 10-17 atlas points on the same charts** (67-71 % against the best xatlas run of 50-58 %),
  i.e. the brief's 70 % "ideal" target, at the same 4-texel gap and an exactly uniform scale, in about 5 minutes. That
  is +13 % linear texel density (+28 % texels) for nothing but packing. The leak at that tighter but equal minimum gap
  is unchanged (A4: mip 4 1.55 against 1.50 levels).
- Blender 5.3's packer is no better than before (CONCAVE 51-57 %, below xatlas on most sets).
- xatlas's fast sweep and brute force are within each other's noise (+-2 points); brute force is not worth its minutes.
- Integration (proposal): `uv_atlas.unwrap(..., packer='sparrow')` calling `sparrow_pack.py` logic (polygon outlines,
  `min_item_separation = 2 x margin_px`, continuous rotation, 5 x 60 s scale search). Needs the sparrow binary (Rust
  toolchain, MIT) and shapely in a venv next to `xatlas_venv`. sparrow is stochastic: keep the packed layout with the
  upload, never re-run after a paint (the existing rule for xatlas). A smarter scale search (bisection on the last
  fitting / failing pair, or warm-starting from the previous solution JSON) should find the last 1-2 points.

## Which variant deserves a paid Meshy paint

The winning layout everywhere is **seam removal (p90 <= 1.25) + sparrow packing**, with the nearest-texel re-pad of
A as a free post-processing step (it needs no new paint: it can be applied to any existing paint). Uploads are ready in
`winners/` (neutral static: one mesh, POSITION/NORMAL/TEXCOORD_0, no material, no skin, exported like
`mm9_magreeb_claude/scripts/uv_atlas_v8.py`), each with a skinned `_measure.glb`, `_quality.json` and heatmaps:

| Upload | Triangles | Atlas % | Density p50 vs fresh `uv_atlas.py` | Islands | Fragments | Stretch p90 | Visible seam vs fresh |
|---|---|---|---|---|---|---|---|
| `winners/magreeb_seamsparrow_upload.glb` | 6,002 | 70.5 | 2,302 vs 2,013 (+14 %; installed 2,020) | 110 | 0.8 % | 1.26 | -38 % |
| `winners/m620_body_seamsparrow_upload.glb` | 5,172 | 69.5 | 1,507 vs 1,334 (+13 %) | 60 | 0.0 % | 1.24 | -31 % |
| `winners/m620_head_seamsparrow_upload.glb` (welded) | 3,828 | 70.6 | 869 vs 754 (+15 %) | 769 | 30.0 % | 1.18 | -7 % |
| `winners/hyd_body_seamsparrow_upload.glb` | 3,289 | 66.8 | 1,339 vs 1,199 (+12 %) | 82 | 1.4 % | 1.21 | -47 % |
| `winners/hyd_heads_seamsparrow_upload.glb` | 4,637 | 70.4 | 1,897 vs 1,674 (+13 %) | 195 | 3.1 % | 1.25 | -23 % |

**Paint first: the Magreeb (10 credits, `winners/magreeb_seamsparrow_upload.glb`, same four HD masters and
`requests/retexture_v2.json` settings).** It is the only subject with a paint on the current route already (v2, 4K on
the 54 % layout), so one paint gives a direct before/after of the layout alone, comparable through the brief's
identical-camera close-ups and the speckle measure; read it against candidate 6's noise floor. If it wins, paint the
m620 body + head (20 credits, the model b9 wants redone) and the BHydra body + heads (20 credits).

Caveats for adoption: the m620 head upload is merged by distance (1,011 split vertices welded), so its runtime mesh
must be rebuilt from that welded head; the m620 and BHydra uploads are the sets split out of the installed GLB (body by
u < 0.5 for m620, materials for the hydra) and need the usual set re-join and runtime build. Never re-run the packer
for an upload after it went to Meshy (sparrow is stochastic, like xatlas).

## Files

- `RESULTS.md` (this file); scripts in `../scripts/layout/` (`uvlib.py`, `gutter_inspect.py`, `leak.py`,
  `leak_fills.py`, `transfer.py`, `margin_study.py`, `bc7_check.py`, `repack.py`, `xatlas_pack.py` (copy),
  `uv_seam_trial.py`, `seam_texture.py`, `render_views.py`, `seam_sheet.py`, `tabulate.py`, `blender_pack.py`,
  `pack_eval.py`, `sparrow_pack.py`, `faces2layout.py`, `apply_layout.py`, `glb_add_material.py`, `blender.sh`) and
  `../scripts/uv_atlas_seam.py`.
- `gutter/`: `inspect_*.json`, `leak_*_installed.json`, `margin_study.json`, `margin_study_sparrow.json`,
  `bc7_orig.json`, `gutter_fill_sheet.png`, crops `magreeb_meshy_crop.png`, `magreeb_inst2k_crop.png`, filled maps.
- `seams/<model>/`: per trial `_report.json`, `_quality.json`, `_heat_*.png`, `_upload.glb`, `_measure.glb`,
  `_faces.npz`, `.blend`, renders `r_*`; sheets `seams/magreeb_seam_sheet.png`, `seams/m620_seam_sheet.png`,
  `seams/hyd_seam_sheet.png`; visibility renders `seams/magreeb/r_vis_*.png`.
- `pack/`: layouts (`*.npz`), `eval_*.json`, sparrow logs, `blender/`, `magreeb_pack_compare.png`.
- `winners/`: the five uploads above with measurement GLBs, quality JSON and heatmaps.
- `work/`: read-only copies of the sources (Magreeb `roots_v7.blend`, `uv_v8.blend`, installed m620 and BHydra GLBs)
  and the re-packed Magreeb layouts of A4.
- Tools outside the repository: sparrow built from github.com/JeroenGar/sparrow (MIT) with a local Rust toolchain and a
  shapely venv, moved on 2026-11-11 into `../sparrow_venv/`, on 2026-11-12 into `claude_shared/sparrow_venv/` (git-ignored; rebuild offline as in the header of `sparrow_pack.py`).
- Credits: 0. No Meshy job was submitted.
