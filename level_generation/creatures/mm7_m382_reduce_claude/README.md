# MM7 Rat (`m382`, Giant / Lightning / Fire Rat) reduction (2026-10-20)

User request after accepting batch E: "do tris reduction now". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the textures,
region mask and tier ramps stay valid. No Meshy credits. Scripts are copied from `mm8_m452_reduce_claude/` (itself a
rat; parent fix, exact source weights, UV-based weights, error lock) and `mm8_m492_reduce_claude/` (`carry_variants.py`,
`probe_max.py`); `make_groups.py`, `close_rat.py`, `glb_close.py`, `build_lods.py`, `viewer_tiers.py` and
`glb_stretch.py` are adapted to this rat. Batch E rules apply: nothing installed, nothing under `assets_dev/` or
`assets_source/`.

Source: the batch E project export `../mm7_m382_claude/export/mm7_m382.glb`, copied byte for byte to
`work/mm7_m382_source_pre_reduce.glb` (rollback source). One material (`M382_A`; tiers B and C are
`KHR_materials_variants` materials sharing every image), one `M382` node, 24 bones plus `Socket_Mouth`, 4 influences.

Pieces (connected components after the weld): five body pieces (head, neck, front legs and fur in one 6,929-face
piece; hind legs and tail; the left hind foot; two fur shells of 335 and 188 faces) and 71 small pieces: 16 claws
(100-126 faces each), 7 whiskers (100-118), about 27 teeth (38-78), the spiky fur-ridge cards (17-89) and a few 1-6
face slivers.

## Ladder

Weld 44,009 -> 950 open edges (unchanged by every step); 50 coincident vertices with other weights kept apart.
Limits are scaled to the 1.4 m body length without the tail (`REA_HEIGHT_M=1.4`): p99 4.2 mm, max 21 mm.

Region budgets (`make_groups.py`):
- **Kept exactly:** the fur-ridge cards and slivers (the MM6 rat's crest flattened under any cut), the eye faces from
  the region mask (G channel, plus one ring, so the eye ramp stays on the eye: 145 faces), and the faces within 3 cm
  of the source's worst edge-stretch spots (inner left hock, thigh/tail-root border: 99 faces).
- **Head** (Head-dominated faces of the body) 60 %, **paws** 45 %, **tail** 80 %, **fur shells** 70 %,
  **claws** 45 %, **whiskers** 45 %, **teeth** 60 %; the rest of the body fills the step's budget.

| step | locks | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| g1 | base | 8,845 (60 %) | 3.54 / 58.4 | 0.993 | 0.991 | fail (max) |
| g1 | base | 7,371 (50 %) | 8.16 / 69.9 | 0.990 | 0.989 | fail |
| e1 | + error lock | 8,907 (60 %) | 2.19 / 13.0 | 0.995 | 0.996 | pass |
| **e1b** | + error lock | **8,613 (58 %)** | **2.61 / 13.1** | **0.994** | **0.995** | **picked** |
| e1b | + error lock | 8,317 (56 %) | 3.44 / 19.7 | 0.993 | 0.995 | pass (near the limit) |
| e1 | + error lock | 8,171 (55 %) | 3.93 / 21.3 | 0.993 | 0.995 | fail (max) |
| e1 | + error lock | 7,433 (50 %) | 23.2 / 45.6 | 0.983 | 0.990 | fail |

- **Error lock** (`err_lock.py`, Cand_55 of g1, over 10 mm, 2 cm radius): the large g1 errors were source
  vertices of the fur body with odd weights (Thigh_L/Spine2/UpperArm weights on the back and flanks) that move apart
  from their neighbours in Death, Running and Walking. 125 vertices, 628 more faces kept (949 -> 1,577). One round
  only.
- **Pick:** 58 % (`Cand_57` in `work/ladder_e1b.blend`; the label rounds 0.58 down). Below it p99 and max rise
  quickly (56 %: max 19.7 mm on the left shin in Running; 55 % fails). 56 % passed but sits at the limit, so the
  conservative step was picked.

Close-ups of the pick against the source (`close_rat.py`, sizes x2.2 of the MM8 rat): face front, three-quarter and
side, ears from above, the Attack bite and open mouth, front and hind paws with claws, tail root and tip, back, flank,
belly, Death, Running and soles: `review/close/sheet_r57_tex.png` and `sheet_r57_clay.png`. Teeth, whiskers, claws,
ears, eyes and the fur ridge read the same.

Texture checks on the pick:
- **Drift (`texture_drift.py`):** 10 faces over 40 (16.7 cm² in all on a 2 m model), on the fur body.
- **Slivers (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`):** 30 faces, each under 6.5 cm², on dark fur, at the
  lips and paw soles. The textured close-ups and the viewer show no change; no drift lock was run.

## Shading

The source export is **flat shaded**: every triangle has its own three vertices with the face normal (44,035
vertices for 14,751 triangles; `M382_A` relies on the normal map). The reduced mesh shades **smooth** (10,014
vertices for 8,613 triangles). Straight from the GLBs (`glb_close.py`, `review/glbclose/sheet_tex.png`:
source | smooth | flat), the three read almost the same textured; smooth is slightly softer and drops the blocky
specular patches on the fur flank, flat with fewer triangles shows larger facets. Smooth is the pick (and a quarter of
the vertex data); a flat export is one switch (`REA_FLAT=1 export_cand.py`) if the faceted look is wanted.

## Build

`export_cand.py` (Cand_57 of `work/ladder_e1b.blend`, `REA_NODE=M382`) -> `swap_lod0.py ... M382` ->
`build_lods.py` -> `shrink_shadow_lods.py` (the creature's own, from `mm7_m382_claude/scripts/`) ->
`carry_variants.py` (7 LOD and shadow primitives get the A/B/C variant mappings): `export/mm7_m382.glb`, 7.0 MB
(source 14.4 MB: the flat-shaded vertex buffers were most of it). Textures, materials, variants, clips and
`Socket_Mouth` are unchanged.

`build_lods.py`: ratios 0.5 / 0.25 / 0.1 of LOD0 (about 50 % per level, LOD3 near the source's 837), 270 protected
points (bounding extremes: nose, tail tip, top, both sides, 5 mm; LOD0 vertices within 4 mm of the floor in any
Death/Dead frame).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 14,751 | 7,374 | 2,634 | 837 |
| reduced | **8,613** | 4,304 | 2,117 | 813 |

## Gates

- **`lod_check.py`** on every LOD: bounds kept (0.85 x 2.0 x 0.79 m at every LOD); no face stretches over 20x in
  any clip; lowest point per clip the same as the source LOD0 at LOD0-2 (Death -3.6 cm during the fall, as in the
  source; Dead +1.2 cm). LOD3 dips to -2.7 cm in Attack (source LOD0 -0.8 cm); far LOD only.
- **Edge stretch** (`glb_stretch.py`, the project's `outliers.py` on the GLB, every frame): identical to the source
  in every clip because the stretch spots are kept exactly: Running 12.2x, Walking 9.3x, Death 8.7x, Attack 7.8x,
  Dead 5.4x, Standing/Hit/Fidget <= 3.2x (the source's known inner-hock patch; 11.8x in the original project's
  30 fps sampling).
- **`check_winding.py`:** 0 inverted closed parts.
- **Viewer:** `review/viewer/` source / reduced for tiers A, B and C (tier colours baked as in the original viewer),
  opening on reduced A; `run_creature_review.py check`: 48 switches, no console errors. `review/tiers_reduced.png`:
  source A, reduced A, B, C in the Attack bite.

## For the user to review

- Smooth instead of flat shading (above).
- The reduced pick in the viewer: http://127.0.0.1:8912/level_generation/creatures/mm7_m382_reduce_claude/review/viewer/index.html

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m382_reduce_claude/export/mm7_m382.glb --world mm7
```

The `actors.yml` binding in `../mm7_m382_claude/README.md` is unchanged (same node, bones, clips, sockets and scale).
Rollback: `work/mm7_m382_source_pre_reduce.glb`.

Reproduce:
1. `REA_NODE=M382 REA_GLB=<rollback source> blender -b -P import_source.py`;
2. `REA_PROTECT=Head dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `make_groups.py`;
3. `REA_HEIGHT_M=1.4 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy
   REA_GROUP_RATIOS=1:0.6,2:0.45,3:0.8,4:0.7,5:0.45,6:0.45,7:0.6 run_ladder.sh g1 0.6,0.55,0.5`;
4. `REA_CAND=Cand_55 REA_ERR_MM=10 REA_LOCK_R=0.02 err_lock.py -- work/keep_base.npy work/keep_e1.npy` (on g1);
5. the same ladder with `REA_KEEP_FACES=work/keep_e1.npy`, labels e1 (0.6,0.55,0.5) and e1b (0.58,0.56);
6. `close_rat.py -- ladder_e1b.blend Cand_57`, `pair_sheet.py`, `texture_drift.py r57`, `dark_slivers.py r57`;
7. build as above; `lod_check.py`, `glb_stretch.py`, `glb_close.py`, `viewer_tiers.py` (source and reduced).

## Gait pass (2026-10-21)

`export/mm7_m382_gait.glb` is `export/mm7_m382.glb` with `Walk2` (lope) and `Run2` (bound) grafted on; it is installed
as `mm7_m382.glb`. The clips come from `../mm7_m382_claude/scripts/gait2_rat7.py` (see
[its README](../mm7_m382_claude/README.md#gait-pass-walk2-lope-and-run2-bound-2026-10-21)).
- Meshes, LODs, variants and the old clips are unchanged.
- Binding: `walking: Walk2`, `run: Run2`, `stride_length: 1.0453`, `run_stride_length: 2.0907`.
- `check_winding.py`: 0 inverted.
- The viewer is now revision `gait-1`: tier A/B/C with the old and the new clips; the previous manifest is
  `review/viewer/manifest_reduce-1.json`.
- Recordings: `review/playback/` and `review/shots/`.

## Sprint (2026-10-31)

`export/mm7_m382_sprint.glb` is the installed `mm7_m382.glb` (as of the 2026-10-22 LOD repair) with `Sprint` grafted
on. Its clip comes from `../mm7_m382_claude/scripts/sprint_rat7.py` (see
[its README](../mm7_m382_claude/README.md#sprint-maw-chase-2026-10-31)). It is installed as `mm7_m382.glb` with
`install_model.py --world mm7 --name mm7_m382.glb`.
- Meshes, LODs, variants and every earlier clip are unchanged (append only).
- `check_winding.py`: 0 inverted.
- Binding for Rat A/B/C only: `sprint: Sprint`, `sprint_stride_length: 3.3`. The zrat descriptors stay on walk/run.
- Rollback: the assets_source submodule's HEAD copy of `worlds/mm7/models/mm7_m382.glb`.
- The viewer is now revision `sprint-1`, with tier A/B/C GLBs from the sprint export; the gait-1 manifest is
  `review/viewer/manifest_gait-1.json`. The page (`index.html`, `review.js`) is a copy of `mm9_bigfoot_claude`'s viewer,
  because this project's page was missing. `run_creature_review.py check`: 33 switches, no console errors.
- Review:
  - side-view phase shots of Run2 and Sprint: `review/shots/run2_*.png`, `sprint_*.png`, and the 8-phase sheet
    `review/shots/run2_vs_sprint_left.png`;
  - playback recordings: `review/playback/Sprint-1.webm`, `Sprint-0.5.webm` (and `Run2-*`).

## Gait rollout (2026-10-31): Walk3 for the zrats

Gait rollout package q2 ([`../gait_rollout_20261031/q2/README.md`](../gait_rollout_20261031/q2/README.md)) added
`Walk3`, a slower rotary lope for the arena zrats (zrat a-c). It is 0.2667 s long with a 0.7733 m stride (authored
2.90), the same phases as Walk2, duty 0.52 and no suspension. The zrats wander at 2.80 model units/s, where Walk2
played ×0.63.
- Grafted onto the installed `mm7_m382.glb` (append only, `graft_byte_check.py` OK; 0 inverted) and installed.
- Binding for zrat a-c only: `walking: Walk3`, `stride_length: 0.7733`, `run: Walk2`, `run_stride_length: 1.0453`
  (chase ×1.25). Rat A-C are unchanged.
- The clip comes from `../gait_rollout_20261031/q2/scripts/quad_gait.py m382`.
- Viewer revision `zrat-walk3-1` (the sprint-1 manifest is kept as `manifest_sprint-1.json`); shots
  `review/shots/w3_*.png`, playback `review/playback/Walk3-*`.
- Rebuild: see the q2 README. A far-LOD repair rerun must re-graft `Walk3` (and the earlier Walk2, Run2 and Sprint).
