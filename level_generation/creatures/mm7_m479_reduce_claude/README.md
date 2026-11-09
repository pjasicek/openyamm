# MM7 Treant (`m479`, Treant A / B / C) reduction (2026-10-20)

User: "do the tri reduction on all 5" (batch I; this project is the Treant only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the UVs,
so the batch I atlas (one material `M479`, palette 530 for every tier, no region mask or ramps) stays valid. No Meshy
credits. **Not installed**; nothing written to `assets_dev/`, `assets_source/` or `../mm7_m479_claude/` (except the
"Reduced version" note in its README).

Scripts start from `../mm7_m278_reduce_claude/scripts/` (ladder, groups, error and spot locks, drift and dark-sliver
checks, swap/LOD build) with the lease-wrapper runners (`bl.sh`, `run_ladder.sh`, `cand_glb.sh`), `decimate_tex.py`,
`export_cand.py`, `kept_normals.py`, `compare_glb.py`, `visibility.py` and `sliver_probe.py` from
`../mm7_7m452_reduce_claude/scripts/`. Treant-specific: `master_pieces.py`, `make_groups.py`, `tip_faces.py`,
`close_treant.py`, `glb_close.py`, `gates_glb.py`, `err_split.py` / `err_where.py` / `err_groups.py`, `viewer_manifest.py`;
`shrink_shadow_lods.py` is the production project's own.

## Source

`../mm7_m479_claude/export/mm7_m479.glb`, copied byte for byte to `work/mm7_m479_source_pre_reduce.glb` (rollback
source): mesh node `M479`, 30 bones, `Socket_Mouth`, clips Standing / Attack / Hit / Death / Dead, shadow LODs.
Smooth-shaded. Weld (identical weights only): 12,749 -> 389 open edges, no coincident vertices with other weights,
13,591 triangles in and out. 121 connected pieces: trunk skin, ~100 loose bark strands / limb ropes / root tendrils,
19 peg teeth (78 faces each), two eye almonds (168 each). Labels (`part` teeth/eyes, `piece` 15 = lower lip) come from
the production master `../mm7_m479_claude/work/anim_v1.blend` (`master_pieces.py`, read only; nearest rest vertex, max
0.001 mm). Ladder limits scaled to the 4.0 m height (`REA_HEIGHT_M=4.0`): p99 12 mm, max 60 mm; IoU >= 0.98,
SSIM >= 0.93.

## Where the error comes from

Per-region probes (`err_split.py`, `err_where.py`, `err_groups.py`; MeshLab on each group alone):
- The error is geometric (rest pose = posed), not weights: the strands keep moving together.
- **Root skirt:** the production build already halved it (Blender collapse); even a 5 % cut shortened tendrils by
  31-49 mm and 15 % by up to 18 cm (`ladder a`). Kept exactly.
- **Face front** (mouth and eye zone): p99 20 mm at 80 %; 90 % is clean.
- **Trunk:** p99 12 mm at 85 %, 20 mm at 75 %.
- **Crown** (six limb sectors above 1.85 m): the most reducible, p99 15 mm at 65 %.
- **Teeth** (pegs, own group): max 7 mm at 60 %, 13 mm at 50 %. **Eyes** kept.
- A strand-tip lock (`tip_faces.py`: geodesic maxima per piece, 8 cm) did not help: the crown kept the same error and
  the cut moved onto the strand middles (`ladder b`). Not used in the pick.

## Budgets per region (`scripts/make_groups.py`, set `f`, pick ratios)

| region | faces | treatment | out |
|---|---:|---|---:|
| root skirt (faces below 0.35 m) | 3,020 | kept exactly | 3,020 |
| mouth: lips, Jaw/UpperLip-weighted bark, 3 cm ring; 4 cm ring around the eyes | 605 | kept exactly | 605 |
| eyes | 336 | kept exactly | 336 |
| floor contact (any vertex below 1 cm), small pieces up to 60 faces touching the above | (in the rows above) | kept | |
| face front (rest of the mouth/eye zone) | 1,148 | 90 % | 1,032 |
| teeth (19 pegs) | 1,482 | 55 % | 814 |
| crown | 4,174 | 55 % | 2,294 |
| other small pieces (twig ends, <= 60 faces) | 320 | 70 % | 224 |
| trunk (free) | 2,527 | 80 % | 2,021 |
| **total** | **13,591** | | **10,325 (76 %)** |

The eye ring was added after `ladder e`: a decimated socket vertex took eye weights and moved 51 mm when the eyes sink
in Standing.

## Ladder

| config | steps | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 13,591 | | | | |
| a: mouth, teeth, eyes, small kept; face 80 %, roots 60 %, rest free | r73-r58 | 10,027-8,015 | 27.6-41.5 / 179.9 | 0.976-0.950 | 0.983-0.965 | fail (root tendrils shortened) |
| b: a + strand tips | r77-r63 | 10,475-8,667 | 29.3-60.4 / 122.5-244.9 | 0.969-0.936 | | fail |
| c: b, roots 85 % | r74-r61 | 10,173-8,365 | 24.0-158.3 / 105.7-439.9 | 0.979-0.825 | | fail (whole strands vanish below 50 % free) |
| d: roots kept, teeth 60 %, face 90 %, crown 65 % | r81 / r79 / r77 | 11,035 / 10,781 / 10,529 | 8.8 / 11.1 / 14.8, max 50.8 | 0.993-0.992 | 0.991-0.987 | pass / pass / fail |
| e: d + crown 60 %, small pieces 75 % | r78 / r77 | 10,619 / 10,493 | 10.5 / 11.6, max 50.8 | 0.991 | 0.989-0.988 | pass |
| f: e + eye ring | r77 / r76 | 10,499 / 10,373 | 11.5 / 12.9, max 49.5 | 0.991 | 0.988 | pass / fail |
| g: f + error lock (Cand_75, 20 mm, 3 cm) | r77-r75 | 10,527-10,219 | 23.6-43.8 / 81.9-154.4 | | | fail (the cut moved onto the trunk; one round only) |
| **hp: f, teeth 55 %, crown 55 %, small 70 %, trunk 80 %; piece weights** | **r76** | **10,325** | **11.25 / 49.5** | **0.990** | **0.989** | **pick** |
| i: crown 50 % | r75 | 10,243 | 11.5 / 52.2 | 0.989 | 0.989 | pass; 82 triangles less for a thinner crown, not taken |

The 49.5 mm maximum is an interior trunk vertex (inside the trunk radius) in the Death burst (frame 12); in the rest pose
every source vertex is within 27.4 mm of the reduced surface (p99 12.3 mm, `err_where.py`).

**Weights.** Ladders a-h used UV weights (`uv_weights.py`, `REA_WEIGHTS=component`). Its fallback (nearest source vertex
with a similar normal) gave reduced lower-tooth vertices upper-tooth (TeethU) weights: a 12x edge stretch in every
clip where the mouth opens. The pick uses the default nearest-face transfer with **piece weights** (each reduced piece
takes weights only from its own source piece) and exact weights on every source vertex: every tooth stays rigid on its
own bone, and the strands keep the production weight field (a smooth function of position).

## Texture and topology checks (`h76` = the pick's mesh)

- **Drift** (`texture_drift.py`): 25 faces over 40 (all 40-50, bark pattern shifts on large trunk and crown faces;
  23 seen in 3+ of 42 views). **Dark slivers** (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`): 7 faces (6 seen,
  26-187 cm²). Textured close-ups at the six seen dark slivers and three of the largest drift faces (`review/close/sheet_spots_h76_tex.png`, `close_treant.py` with
  `CLOSE_POINTS`) show no change, so no drift lock was run.
- **Slivers** (`sliver_probe.py`): no new slivers; 55 new long faces (34 seen), on the trunk strands.
- Open edges 389 = source.

## Close-ups

- From the ladder blend (`close_treant.py`): `review/close/sheet_h76_tex.png`, `sheet_h76_clay.png` (face front and
  three-quarter, open mouth front and three-quarter, open eyes, crown top / three-quarter / back / both sides, spire,
  roots front / back / top, trunk back, Attack, Death, Dead).
- Straight from the GLBs (own normals): `review/glbclose/sheet_glb_tex.png`, `sheet_glb_clay.png`.
- Face, lips, teeth, eyes, crown silhouette and root skirt match the source; teeth at 55 % keep their peg shape.

## Build

`TOKEN=<lease> scripts/build_reduced.sh export/mm7_m479.glb`: `kept_normals.py` (the source GLB's normals on unchanged
faces) -> `export_cand.py` (Cand_76 of `work/ladder_hp.blend`) -> `swap_lod0.py` (onto the rollback source: material,
images, clips, nodes, `Socket_Mouth` byte for byte; `work/pick_lod0.glb`) -> `build_lods.py` (`tools/build_actor_lods.py`,
ratios 0.5 / 0.22 / 0.072, 117 protected points: bounding extremes within 5 mm and Death/Dead floor contact within 6 mm)
-> `shrink_shadow_lods.py` (the production project's step). One material and no variants: no `carry_variants` step.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| batch I | 13,591 | 6,794 | 2,420 | 728 | 9.63 MB |
| reduced | **10,325** | **5,159** | **2,241** | **660** | **8.53 MB** |

`compare_glb.py`: nodes and transforms, skin, inverse binds, material and extras (`openyamm_specular`), images,
textures, samplers, all five clips and the mesh extras identical; the only difference is that the rebuilt LOD1-3 and
shadow LODs carry 4 influences (`JOINTS_0`/`WEIGHTS_0`) where the batch I LODs carried 8. LOD renders:
`review/lods/sheet_lods.png` (Standing three-quarter and Attack per LOD, source and reduced). LOD3 is a shard
silhouette in both (the LOD builder on a strand soup), the reduced one about as sparse as the source's.

## Gates (every frame of every clip, 30 fps)

`gates_glb.py` runs the production `gates.py` measures on the exported LOD0 (`work/gates_src.json`, `work/gates_red.json`):

| clip | floor min z | max edge stretch (source) | limb clearance margin | coincident split vertices |
|---|---|---|---|---|
| Standing | -0.0039 m | 1.83 (1.83) Trunk1, closed lip | +0.124 m (same) | 0.0 mm apart |
| Attack | -0.0039 m | 1.83 (1.83) | +0.105 m (same) | 0.0 mm |
| Hit | -0.0039 m | 1.83 (1.83) | +0.125 m (same) | 0.0 mm |
| Death | -0.0039 m | 2.36 (2.36) Limb1_1, intended burst | not gated | 0.0 mm |
| Dead | -0.0039 m | 1.97 (1.84) Trunk2, stump flattening | not gated | 0.0 mm |

- **Closed mouth** (Standing): lower-lip top 0.040 m above the lowest upper-tooth tip (source 0.040), teeth 0.237 m
  behind the lip front (source 0.238).
- **Branch interpenetration:** the production gate measures bone segments of different crown sectors; rig and clips
  are unchanged, so the margins are identical (above). The mesh-level check: all 9,564 coincident vertex pairs (UV
  seams, touching split pieces) stay together in every frame (0.0 mm), and the ladder's two-way surface error is
  under the limits over every 3rd frame of every clip.
- **`lod_check.py`** (every LOD, every frame): bounds 3.73 x 3.64 x 4.00 m kept at every LOD (the batch I LOD3
  lost 16 cm of height and 23 cm of width), lowest point -3.9 mm at every LOD (source LOD2 -12.6 mm), no face over 20x its rest
  area in any clip.
- **`check_winding.py`:** 0 inverted closed parts.
- **Viewer:** `run_creature_review.py check`: 10 switches (2 models x 5 clips), no console errors, failed [].

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m479_reduce_claude/review/viewer/index.html`: batch I (13,591) and
reduced (10,325), opening on the reduced model; native reference frames from `../mm7_m479/trimmed_2x/`. Shots:
`review/viewer_shots.png` (Standing, Attack impact, Hit; both models).

## For the user to review

- The cut is moderate (-24 %): the root skirt (3,020 faces, already halved in production), mouth, eyes and teeth hold
  well over a third of the mesh, and every strand cut beyond these ratios shortened twig and root ends.
- Teeth at 55 % (78 -> about 43 faces per peg) in the open mouth (Attack, Hit, Dead).
- Dead stump: edge stretch 1.97 against 1.84 (the trunk's flattening zone on larger faces); not visible in the
  close-ups.
- LOD3 (660) is shardy like the batch I LOD3 (728).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m479_reduce_claude/export/mm7_m479.glb --world mm7
```

The `actors.yml` binding in `../mm7_m479_claude/README.md` is unchanged (same file name, node, clips, socket), then a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: `work/mm7_m479_source_pre_reduce.glb`.

## Reproduce (repository root for the wrapper; scripts run from the project directory)

Blender scripts run through `scripts/bl.sh` (`TOKEN=<lease>`, `tools/run_creature_blender.sh`); the MeshLab venv path
is in `run_ladder.sh`.
1. `REA_NODE=M479 REA_GLB=level_generation/creatures/mm7_m479_reduce_claude/work/mm7_m479_source_pre_reduce.glb bl.sh import_source.py`;
   `bl.sh dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `master_pieces.py`;
2. `ROOTS_KEEP=1 TEETH_GROUP=1 SMALL_GROUP=1 python3 scripts/make_groups.py f 60`;
3. `TOKEN=<lease> scripts/run_ladder.sh hp f "1:0.9,3:0.55,5:0.55,6:0.7" 0.8,0.75` (default `REA_HEIGHT_M=4.0`;
   earlier ladders with `REA_WEIGHTS=component`);
4. `bl.sh close_treant.py ladder_hp.blend Cand_76`, `pair_sheet.py`; `extract_basecolor.py`, `texture_drift.py h76`,
   `dark_slivers.py h76`, `sliver_probe.py`, `REA_PIX=0.004 visibility.py -1 5`;
5. `scripts/build_reduced.sh export/mm7_m479.glb`;
6. `REA_NODE=M479 bl.sh lod_check.py <glb> <label>`, `bl.sh gates_glb.py <glb> <label>`, `compare_glb.py`,
   `check_winding.py`, `LOD_SCALE=4.8 LOD_CZ=2.0 LOD_ATTACK_F=16 bl.sh lod_views.py src,red`,
   `bl.sh glb_close.py "source=...,reduced=export/mm7_m479.glb"`, `viewer_manifest.py`,
   `run_creature_review.py ... check`.
