# MM8 School of Fish (`m636`, School of Fish A/B/C) reduction (2026-10-19)

Triangle reduction of the installed school, following [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
(texture-aware ladder, keep UVs and textures, LOD rebuild, viewer review), no-retexture branch: the installed
textures, the three palette variants and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m636.glb`, byte-identical to `../mm8_m636_claude/export/`,
copied to `work/mm8_m636_source_pre_reduce.glb` (rollback source). One `School` node, one skin (61 joints: Root plus
Body/FinL/FinR/Tail1/Tail2 per fish), one material with three variants, LOD1-3 meshes that also serve as the shadow
chain. No separate attachment GLBs.

## How the school is built, and the route

The twelve fish of every LOD are exact similarity copies of `Fish00`: same vertex order, triangles, UVs and weights,
joints offset by 5 per fish, scales 1.0 down to 0.308 (`scripts/fish_dump.py` asserts this to 1e-5 m). So the
reduction works on one template fish and copies the result to all twelve, which keeps every fish identical and lets
the small fish carry exactly the same detail as the large ones.

Fish00 (650 triangles, 0.765 m long) is seven closed pieces: the body with the dorsal spines, tail, pelvic and anal
fins (468), two pectoral fins (28 / 26), two gill covers (37 / 35) and two eyes (28 each). Its UV layout has 86
charts, many of 1-8 triangles.

- `fish_dump.py`: Fish00 of LOD0 and each fish's similarity transform -> `work/fish.npz`; welded MeshLab input
  `work/mesh_in.npz`.
- `make_groups.py`: regions by piece (eyes, pectoral fins as two groups, gill covers).
- `decimate_tex.py` (the m604 copy plus `REA_IN`/`REA_OUT`, a minimum target of 8 and `REA_OPEN_GROUPS`).
- `fish_build.py`: template -> glTF vertices -> twelve fish -> the four LOD primitives of a copy of the source GLB.
  Everything else in the file (rig, clips, materials, variants, LOD and shadow references) is unchanged; unreferenced
  buffer data is dropped. An identity run (the unreduced template) reproduces the source vertices exactly (normals
  within 0.03 degrees, weights within 6e-8).

**Normals and weights.** The source has custom normals (median 11 degrees from smooth, 60-80 degrees on the fins),
continuous across its UV seams (no hard edges). The reduced vertices take normal and skin weights from the closest
source surface point that faces the same way (so a thin fin never takes the other side), interpolated from the
source's welded vertices; every wedge copy of a vertex gets the same values and kept vertices their exact source
values. A first version looked them up by UV chart: the tiny charts put some collapsed vertices on a chart 1 cm away
and showed faceted shading in clay renders, so it was replaced. 3 influences, as the source.

## Ladder

One fish; ratios of its 650 triangles. Eyes kept exactly at every step, pectoral fins at 70 %.

| step | tris / fish | school | rest p99 / max mm (Fish00, two-way) | posed p99 / max mm per fish | posed p99 / max mm world | IoU min (school) | SSIM mean | |
|---|---:|---:|---|---|---|---|---|---|
| source | 650 | 7,800 | | | | | | |
| 75 % | 486 | 5,832 | 4.9 / 11.2 | 4.85 / 11.18 | 2.36 / 5.45 | 0.955 (0.989) | 0.975 | spines, fins, gills as source |
| **68 %, gill covers kept** | **440** | **5,280** | 7.7 / 20.9 | 6.66 / 20.94 | 3.24 / 10.2 | 0.942 (0.980) | 0.962 | **pick** |
| 65 % | 420 | 5,040 | 7.8 / 20.9 | 6.66 / 20.94 | 3.24 / 10.2 | 0.938 (0.980) | 0.960 | gill covers notched |
| 60 % | 388 | 4,656 | 13.6 / 34.1 | 10.64 / 34.13 | 5.18 / 16.63 | 0.935 (0.955) | 0.948 | rear spines merge |
| 55 % | 356 | 4,272 | 19.6 / 45.7 | 15.54 / 45.73 | 7.57 / 22.28 | 0.900 (0.900) | 0.934 | spines merge, mouth |

Errors (`pose_error.py`, every 3rd frame at 24 Hz of Swim, Death and Dead, exact point-to-triangle distance both
ways, each fish against its own copy):
- **per fish** in Fish00 units (divided by the fish's scale), limits from Fish00's 0.765 m: p99 2.3 mm, max 11.5 mm;
- **world** with the school as one actor (2.0 m bound), limits p99 6 mm, max 30 mm.

Every step down to 60 % passes the world limits. No step passes the per-fish ones, 75 % included (posed p99
4.85 mm). The template is already lean (650 triangles for a 0.77 m fish), so any collapse moves the outline by
millimetres, mostly at the spine tips, the pectoral fin edges and the gill cover rims. The 20.9 mm maximum is on the
thin parts (spines, fin edges) of the 0.49-scale Fish11, 10.2 mm in the world.

IoU and SSIM (`view_scores.py`) are on `fish_views.py` close-ups of Fish00 (side, top, front, three-quarter rear,
head and fins), the small Fish03 and the whole school. No step passes IoU 0.98 in every view: the front and top
close-ups see the spines and fins edge-on, where one-pixel flips dominate, as the dragon's wing membranes did. The
whole-school view passes at 75 % (0.989) and at the pick (0.980).

The **visual pick** is 68 % with the gill covers kept exactly (`work/keep_gill.npy`: eyes plus gill covers, 128
faces). In the close-ups (`review/close/ladder_tex.png`, `ladder_clay.png`, and `src_*` against `gk680_*`), the
spines, tail and pectoral fins match the source. At plain 65 % the gill cover rims lost their round outline in clay;
below that the dorsal spines merge (60 %), and then the mouth and head change (55 %). A separate budget for the thin
parts of the body (`make_groups.py` THIN_GROUP: spines, tail, fins under 1.5 cm thick) pinned the body to their cut
edges and did worse; it stays off.

## LODs

The LODs are rebuilt from the picked template with the same route (eyes, pectoral fins and gill covers decimated as
their own open groups). The body keeps most of each budget, as in the installed LODs (installed LOD3: body 66 of 77).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed (school) | 7,800 | 3,888 | 1,908 | 924 |
| reduced (school) | **5,280** | 2,604 | 1,452 | 924 |
| reduced per fish | 440 | 217 | 121 | 77 |

LOD3 keeps the installed count: at 50 body triangles the fish keeps its 0.74 m length and its dorsal fin outline.
The installed LOD2-3 had dropped the dorsal fin (`review/lods/sheet.png`: source and reduced LOD0-3, textured and
clay). MeshLab flattens a thin closed pectoral fin into an inside-out shell at 6-8 triangles in LOD1-3;
`fish_build.py` reverses closed pieces with negative volume (one per LOD, logged).

`lod_check.py` (`REA_NODE=School`, `work/lod_check_{src,r68}.json`):
- LOD0 has the source's exact bounds, and LOD1-3 stay within 2.5 cm of them (closer than the installed LODs at the
  top: 0.950 m against 0.912 / 0.898 / 0.828 m);
- no face stretches in any clip at any LOD;
- the lowest points per clip follow the source (Dead and Death 0.055 m at LOD0, as the source).

`check_winding.py`: 0 inverted closed parts (source 0).

## Textures

Not changed. All three tiers render as the installed ones (`review/close/tiers.png`: per tier, installed and reduced
side by side). UV drift on the picked LOD0 (UV against the source UV at the same surface point): p99 15 px, max
56 px on the 2K map, at collapsed vertices along small chart borders. The renders show no smear.

Pre-existing in the installed model, left alone: one dorsal-membrane panel behind the fourth spine is pale fin
texture without the spine stripes, so it reads as a small white patch on the top of every fish. A local texture
edit could paint stripes there. Neither a geometry nor a mask fault, and no retexture is needed.

## Viewer

`review/viewer/` (`viewer_build.py`): per tier, the creature project's installed viewer file and the same file with
the reduced LOD0-3 swapped in (`*_r68.glb`). It uses the creature project's page, clips and native anchors and opens
on the reduced purple school. `tools/run_creature_review.py --project
level_generation/creatures/mm8_m636_reduce_claude check`: 18 switches, no console errors.

## Status

Installed 2026-10-19 (user: "school of fish ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_fish_school ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_fish_school_actor_models_keep_palettes_swimming_and_native_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m636_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

## Reproduce

```sh
V=<venv with pymeshlab>/bin/python
python3 scripts/fish_dump.py work/mm8_m636_source_pre_reduce.glb
python3 scripts/make_groups.py      # then work/keep_gill.npy = keep | (groups == 2)
REA_OUT=gk REA_KEEP_FACES=work/keep_gill.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,5:0.7 $V -I scripts/decimate_tex.py work 0.68
python3 scripts/make_groups.py gk_r680
for spec in 0.5:1:0.5,5:0.5,2:0.5,4:0.5 0.28:1:0.34,5:0.34,2:0.25,4:0.2 0.168:1:0.34,5:0.34,2:0.1,4:0.07; do
  REA_OPEN_GROUPS=1,2,4,5 REA_IN=gk_r680 REA_OUT=lod_gk680 REA_GROUPS=work/gk_r680_groups.npy \
    REA_GROUP_RATIOS=${spec#*:} $V -I scripts/decimate_tex.py work ${spec%%:*}
done
L="work/gk_r680.npz work/lod_gk680_r500.npz work/lod_gk680_r280.npz work/lod_gk680_r168.npz"
python3 scripts/fish_build.py work/mm8_m636_source_pre_reduce.glb export/mm8_m636.glb $L
python3 scripts/viewer_build.py $L
```

Checks:
- `blender -b -P scripts/pose_dump.py -- <glb> <label>` + `pose_error.py src <label>`;
- `fish_views.py` + `view_scores.py`;
- `REA_NODE=School blender -b -P scripts/lod_check.py -- export/mm8_m636.glb r68`;
- `lod_glbs.py` for LOD renders;
- `piece_report.py` for inside-out pieces.

The plain ladder steps (`work/mesh_r{750,650,600,550}.npz`) come from `decimate_tex.py work 0.75,0.65,0.6,0.55` with
`REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.7` (gill covers group 2 at the
time). Candidate GLBs are in `work/cand/`.
