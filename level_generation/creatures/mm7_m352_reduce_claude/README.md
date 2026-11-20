# MM7 Peasant Human1 Male (`m352`, descriptors 358-366) reduction (2026-10-20)

User: "do tris reduction on all 5" (the five MM7 batch-K peasants; this project is m352 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine colour looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy credits.
Scripts from batch J's male peasant, [`../mm7_m302_reduce_claude/`](../mm7_m302_reduce_claude/README.md) (paths, shells,
height, names and keep sets adapted). **Not installed** (batch K: the user installs later; no REDUCTION_LEDGER row yet).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m352_reduce_claude/review/viewer/) (source vs
reduced, all nine looks, six clips) · close-ups [head/torso](review/sheet_f.png), [ladders c/d](review/sheet_a.png),
[legs/clips c/d](review/sheet_b.png) · [viewer shots](review/shots_sheet.png)

## Source

`../mm7_m352_claude/export/mm7_m352.glb` (after the 2026-10-20 walk fix: Standard Walk, constant foot roll, even bob),
copied byte for byte to `work/mm7_m352_source_pre_reduce.glb` (rollback source; sha256 3e7571acd700a3b4...). One merged
body + head atlas material per look (`M352_AA`...`M352_CC`, 2080x1024, head half u > 0.51), node `M352`, 56 joints,
shadow LODs, clips Standing, Walking, Hit, Death, Dead, Fidget. Height 1.70 m (ladder limits p99 5.1 mm, max 25.5 mm;
IoU, SSIM as the shared ladder). Weld (identical weights only): 5,579 -> 365 open edges, no coincident vertices with other
weights, 9,045 triangles in and out (4,827 vertices, the build master's).

The source was already reduced once in its build (14,941 -> 9,045 with head and hands protected).

## Where the triangles are (`scripts/source_pieces.py` + `m352_pieces.py`, shells of the build's Smart Topology return)

| shell | faces | |
|---|---:|---|
| 0 tunic (painted belt, ragged hem) | 1,305 | belt 128 kept |
| 1 trouser legs | 641 | |
| 2 head and neck | 1,935 | face front 912 kept |
| 3/4 hands with the forearms inside the sleeves | 2,804 | every finger face (2,306) kept |
| 5 long hair | 650 | |
| 6/7 shoes | 314 | kept |
| 8 buckle, 9 strap end | 224 | buckle kept |
| 10/11 eyes | 286 | visible 70 kept, the backs cut with the hidden head set |
| 12-68 brass studs (57 pieces of ~16 faces) | 886 | kept (small pieces taper into points at any cut) |

1,184 faces are never seen from any view (`visibility.py`): scalp under the hair, eye backs, inner tunic and trousers.

## Keep set (`scripts/m352_sets.py`, pick = set `f`)

Kept exactly (4,886 faces): every finger face (any vertex with finger weight > 0.05; the playbook's dwarf: fingers in a
cut come back as jagged points); the studs and the buckle; the shoes (`c`: the shoe uppers had p99 9.4 mm at a light
cut); the visible eye faces; the face front (head skin within 7.5 cm of the face centre); the painted belt (tunic faces
of leather colour between 0.97 and 1.09 m); 3 cm patches (mirrored, `work/patch_b.npy`) at the max-error spots of the
first ladders: tunic sides under the arms, sleeve undersides, the hem at the crotch and the thighs under the hem.
Groups at the pick: visible head set (hair, ears, face rest) 65 %, hidden head set 55 %, palms and backs of the hands
60 %, strap end 60 %, hidden body faces 80 %, **tunic 92 %**; the trousers and the rest take the shared ladder cut.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 9,045 | | | | |
| a: hidden 60 %, head 80 %, palms 80 %, shared 80-50 % | r88-r82 | 7,961-7,443 | 4.29-10.17 / 45.4 | 0.995-0.982 | 0.997-0.988 | fail (max: tunic side under the arm, Fidget/Death) |
| b: a + 10 patches | r88-r83 | 8,017-7,531 | 4.21-10.68 / 102.9 | | | fail (a hidden-back vertex 96 mm in Death; tunic p99 6-15, shoes 9) |
| c: b + shoes kept, hidden 80 %, groups 75 %, shared 95-80 % | r91 / r90 / r89 | 8,237 / 8,163 / 8,087 | 2.61 / 3.09 / 3.57, max 22.3 | 0.997-0.994 | 0.998-0.996 | pass |
| d: c's sets, head 60 %, hidden head 55 %, palms 60 %, shared 90-75 % | r86 / r85 / r84 | 7,843 / 7,693 / 7,619 | 3.37 / 4.10 / 4.53, max 22.3 | 0.996-0.993 | 0.997-0.995 | pass, but slivers (below) |
| e: d + sliver locks (4 cm around 88 flagged faces) | r90-r87 | 8,143-7,951 | 4.21-6.41 / 42.2 | | | fail (the scattered locks fragmented the free surface) |
| **f: d's groups + tunic on its own at 92 %** | **r87** | **7,871** | **3.35 / 22.31** | **0.9956** | **0.9974** | **pick** |

**Slivers** (`scripts/sliver_check.py`, the playbook's "UV corner pushed onto a chart border" case that the per-face median
of `texture_drift.py` misses: 40 samples per face, flagged when 2+ samples differ from the source colour at the same
rest point by over 60): d's r84 and c's r89 showed brown/yellow flecks on the tunic chest and back in the textured
close-ups (51 / 37 flagged faces, 620 / 461 cm²), from large tunic faces whose UVs span the belt and stud charts.
f keeps the tunic on its own gentle cut: 31 flagged faces (260 cm², hair edges and the hidden backs), no fleck in any
close-up. `texture_drift.py` on d's r84: 1 visible face over 40.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh f Cand_87 kn` (source normals on unchanged faces and kept smooth vertices) ->
`work/f87_lod0.glb` -> `tip_points.py f_r87` (head top, hair tip, beard tip) and `floor_points.py` (`REA_FLOOR_MM=30`,
24 Death/Dead floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, ratios 0.5 / 0.2 / 0.062, 33 protected
points) -> `shrink_shadow_lods.py` -> `carry_variants.py` (in place) -> `check_winding.py` (0 inverted closed parts):
`export/mm7_m352.glb`, 6.91 MB (source 7.11 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 9,045 | 4,521 | 1,570 | 484 |
| reduced body | 7,871 | 3,934 | 1,518 | 431 |

## Checks

- `compare_glb.py` (`work/compare_glb.log`): nodes, skin, materials and extras, images, all six clips and the variants
  extension identical to the source; `KHR_materials_variants` on all eight colour/shadow primitives; only the mesh
  geometry differs.
- `grip_check.py` with `GRIP_FINGERS_ONLY=1` (`work/grip_check.log`): all 1,688 LOD0 vertices with finger weight > 0.05
  keep their bind positions (max 0.0004 mm) and weights exactly. The palms and backs were cut on purpose (unarmed).
- `lod_check.py` (source and pick): the top is 1.7005 m at every LOD (source 1.7001-1.7010), the lowest point per clip
  equals the source's, Dead lies on the floor at every LOD (LOD3 −2.8 mm, as the source LOD3), no face stretches over 20x
  at any LOD (the source LOD3 had one).
- Close-ups straight from the GLBs, source vs picks, textured and clay (`glb_close.py`, `glb_sheet.py`): face, hair from
  the side and back, torso, back, right hand, tunic front and side, walk, legs and shoes, fidget, death.
- Viewer: `review/viewer/` (source vs pick, all nine looks); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m352_reduce_claude check`: 108 switches, no console errors. Shots of look `bb` (source and
  pick, body, head, walk) in `review/shots_sheet.png`.

## Open points for review

- The saving is modest (13 % at LOD0): over half the mesh is kept exactly (2,306 finger faces, 886 stud faces, face, eyes,
  belt, shoes, patches) and the cloth was already reduced in the build; harder cuts on the tunic bring texture flecks.
- Seen in the source and unchanged here: a few neckline studs stay green on the non-green tunic looks (Meshy painted those
  stud texels green; the studs are outside the tunic region).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m352_reduce_claude/export/mm7_m352.glb --world mm7
```

then the binding from `../mm7_m352_claude/integration/actors.yml` (nine descriptors, scale 102.6, unchanged by this
reduction) and a [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m352_source_pre_reduce.glb`.

## Reproduce

`REA_GLB=<abs path of work/mm7_m352_source_pre_reduce.glb> REA_NODE=M352 import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m352_source_pre_reduce.glb`, `facecol.py` -> `source_pieces.py` ->
`m352_pieces.py` -> `visibility.py -0.01 1.71` (copy to `work/visible_all.npy`) -> `REA_PATCH_R=0.03 patch_keep.py -
work/patch_b.npy 0.151,0.028,1.085 0.099,0.116,1.160 -0.312,0.064,1.156 -0.295,0.093,1.162 0.0,0.093,0.819
-0.049,-0.071,0.767 -0.070,-0.093,0.870 -0.093,0.096,0.780 0.173,-0.010,1.128 0.149,-0.003,1.192` -> `M352_FACE_R=0.075
M352_EXTRA_KEEP=work/patch_b.npy m352_sets.py b`, then shoes added to the keep (pieces 6/7) as set `d` = `f` ->
`TOKEN=<lease> run_ladder.sh f f "1:0.65,2:0.55,3:0.6,4:0.92,7:0.6,8:0.8" 0.9,0.85,0.8` -> `region_error.py`,
`probe_max.py`, `texture_drift.py`, `SLIVER_N=2 sliver_check.py f_r87` -> `REA_KEPT_NORMALS=1 cand_glb.sh f Cand_87 kn`
(copy to `work/f87_lod0.glb`) -> `tip_points.py f_r87`, `REA_NODE=M352 REA_FLOOR_MM=30 REA_FLOOR_N=24 floor_points.py` ->
build as above -> `compare_glb.py`, `GRIP_FINGERS_ONLY=1 grip_check.py <src> <glb> M352`, `REA_NODE=M352 lod_check.py`,
`glb_close.py`, `viewer_variants.py` (r100 and r87), `viewer_manifest.py "MM7 Peasant Human1 Male" r87 9045 7871`.
Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`). The MeshLab step uses the pymeshlab venv named in
`run_ladder.sh` (another session's scratchpad; recreate it with `pip install pymeshlab` if it is gone).

## Installed 2026-10-20

`tools/install_model.py export/mm7_m352.glb --world mm7` (winding check 0 inverted closed parts first); the
nine bindings from `../mm7_m352_claude/integration/actors.yml` appended to `assets_dev/worlds/mm7/models/actors.yml`
(explicit scale, no `scale_reference`); ledger row in `../REDUCTION_LEDGER.md`. Boot check on Harmondale with two looks
spawned: no load errors, no missing models (`output/batchK_boot/`). Rollback: reinstall
`work/mm7_m352_source_pre_reduce.glb` (the batch export) the same way.

## Gait rollout (2026-10-31, package h14)

The installed source (`assets_source/worlds/mm7/models/mm7_m352.glb`) gained new in-place locomotion clips appended by
[`../gait_rollout_20261031/h14/`](../gait_rollout_20261031/h14/README.md): Jog (Mixamo Running (5), 0.72 s, stride 1.8302; arms from Walking with a forward elbow). Existing clips, meshes, skins and
materials are byte-identical (prefix check). Bindings for all nine descriptors (for the coordinator,
`h14/bindings.yml`): run: Jog, run_stride_length 1.8302. Rollback: reinstall `../gait_rollout_20261031/h14/work/mm7_m352_pre_gait.glb`.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h14/scripts/rebuild.sh m352`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h14/export/mm7_m352.glb --world mm7
--name mm7_m352.glb`. A far-LOD repair rerun, a head-bob fix or any re-export of this model must re-graft these clips
(copy the new source over the pre-gait copy and rerun the rebuild).
