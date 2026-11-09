# MM7 Medusa (`m282`, Medusa / Queen Medusa / Empress Medusa) reduction (2026-10-20)

User: "do the tri reduction on all 5" (batch I; this project is m282 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), **no-retexture branch, 0 Meshy credits** (75 available, none
needed): the texture-aware MeshLab ladder keeps the UVs, so the merged body+head atlas, the region mask, the three
tier variants (`KHR_materials_variants` m282_a/b/c) and the ramps stay valid. **Not installed** (batch I).

Scripts are copied from `../mm7_m414_reduce_claude/scripts/` (humanoid route: keep sets, kept normals, LOD and viewer
tools) with `uv_weights.py`, `dark_slivers.py` and `glb_stretch.py` from `../mm7_m278_reduce_claude/` and
`shrink_shadow_lods.py` from `../mm7_m282_claude/`; medusa-specific: `dump_pieces.py`, `m282_pieces.py`,
`m282_sets.py`, `belly_faces.py`, `head_check.py`, `gates_glb.py`, `build_lods.py`, `build_reduced.sh`,
`viewer_attach.py`.

## Source

`../mm7_m282_claude/export/mm7_m282.glb` (sha256 `92a1a58c...8ae6`, the export after both head reviews), copied to
`work/mm7_m282_source_pre_reduce.glb` (rollback source). One merged material per tier (`M282_A/B/C`, 2080x1024,
head set at u > 0.51), node `M282`, 122 joints, 4 influences at LOD0 (8 at LOD1-3), shadow LODs, 8 clips,
`Socket_Arrow_Release`. The source is smooth-shaded (the batch I faceting fix); the reduced export stays
smooth-shaded and keeps the source GLB's own normals on every kept face (`kept_normals.py`).
Weld: 11,122 -> 240 open edges (unchanged by every step), 15,494 triangles in and out, 8 coincident vertices with
other weights kept apart.

Where the triangles were (pieces from the batch I master's `piece` attribute, `dump_pieces.py` -> `m282_pieces.py`):
17 hair snakes 6,823 (44 %), skin 6,379 (head set 1,254, torso/arms, serpent), hands 1,044, scale-mail cups 418,
collar and arm rings 316, quiver 136, eyes, studs, quiver arrows and the bow string 378.

## Budgets per region (`m282_sets.py f`)

| region | source faces | pick | rule |
|---|---:|---:|---|
| **kept exactly** | 3,956 | 3,956 | whole head texture set (face, scalp, neck top, 1,319) + eyes + 2 rings of neck skin (the jaw seam blend); both hands with every finger (hand/finger weight > 0.3); collar, arm rings, bow string; pieces up to 80 faces (studs, quiver arrows, 3 small hair curls); the visible belly scutes plus one ring (620, `belly_faces.py`); 4 x 6 cm patches at the front S-bend fold (169, `patch_keep.py`); the top 12 mm (23: the highest snakes, model top 1.800 m) |
| 1 hair snakes (14 large) | 6,662 | 2,996 | 45 % |
| 2 scale-mail cups | 418 | 334 | 80 % |
| 3 quiver | 136 | 94 | 70 % |
| 4 serpent skin | 2,564 | 1,410 | 55 % |
| 0 torso and arm skin | 1,758 | 966 | free (55 %) |

Weights: `REA_WEIGHTS=component` (`uv_weights.py`: each new vertex takes the weights of the source triangle that
contains its UV, **only from its own source piece**; source vertices keep theirs exactly). Two medusa fixes:
- nearest-vertex weights (`piece_weights`) and UV weights without the piece rule both left the front S-bend coil
  43.8 / 54.6 mm off in Death: a fold that collapsed triangles cannot follow, fixed by the fold patches;
- the UV fallback (nearest vertex) gave a hanging hair snake beside the right arm ring the ring's forearm weights
  (20x edge stretch in Attack); restricted to the vertex's own source piece, the stretch equals the source in every clip.

## Ladder (limits for 1.80 m: p99 5.4 mm, max 27 mm; IoU >= 0.98, SSIM >= 0.93; all 8 clips, every 3rd frame)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 15,494 | | | | |
| a: hair 65 %, serpent 50 %, nearest-vertex weights | r67 | 10,494 | 5.16 / 43.8 | 0.991 | 0.993 | fail (S-bend fold, Death) |
| b: a with UV weights | r67 | 10,494 | 4.95 / 54.6 | 0.992 | 0.993 | fail (same fold) |
| c: + fold patches | r69 | 10,758 | 4.85 / 23.7 | 0.991 | 0.994 | pass |
| d: hair 55 %, serpent 60 % | r67 | 10,400 | 4.24 / 23.7 | 0.994 | 0.995 | pass |
| e: hair 45 %, serpent 60 % | r62 | 9,732 | 4.59 / 24.3 | 0.993 | 0.995 | pass; **belly plate lines jog** (`review/sheet_de_body.png`, column) |
| **f: e + belly scutes and top kept, serpent 55 %, piece-restricted UV weights** | **r62** | **9,756** | **4.95 / 19.2** | **0.994** | **0.994** | **pick** |
| g: hair 38 %, serpent 50 % | r58 | 9,060 | 5.95 / 30.7 | 0.991 | 0.993 | fail |
| h: f + one drift-lock round | r63 | 9,776 | 5.80 / 24.0 | 0.992 | 0.993 | fail (the lock moved the cut: playbook warning) |

Texture checks on the pick (merged 2K base colour):
- **Drift** (`texture_drift.py f_r62`): 24 faces over 40, 739 cm2 in all, all large faces on the scale-pattern
  serpent back/sides and two on the cup side panels (`review/drift_f62.png`). Textured close-ups at those spots
  (`review/sheet_drift_spots.png`) show no blotch or seam: the high-frequency scale net shifts by a few texels
  inside long faces. The one lock round (h) failed p99 and was dropped.
- **Dark slivers** (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`): 36 faces of 2-8 cm2, on hair snakes and at the
  cup band; no change visible in the close-ups.

## Build

`TOKEN=<lease> scripts/build_reduced.sh`: `kept_normals.py` -> `export_cand.py` (Cand_62 of `work/ladder_f.blend`) ->
`swap_lod0.py` (onto the rollback source; materials, images, variants, nodes, skin, clips, socket byte for byte) ->
`floor_points.py` (40 Death/Dead floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, ratios
0.5 / 0.27 / 0.094, 8 influences, 128 protected points: bounding extremes within 5 mm + floor contacts) ->
`shrink_shadow_lods.py` -> `carry_variants.py` (7 primitives). Bow and arrow: byte-identical copies.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| batch I body | 15,494 | 7,746 | 2,782 | 918 | 8.82 MB |
| **reduced body** (`export/mm7_m282.glb`) | **9,756** | **4,878** | **2,629** | **907** | **8.02 MB** |
| bow (`export/mm7_m282_bow.glb`, copy) | 764 | 382 | 136 | 44 | 0.17 MB |
| arrow (`export/mm7_m282_arrow.glb`, copy) | 296 | 148 | 53 | 22 | 0.14 MB |

Most of the file is the 2080x1024 texture set (unchanged). Shadow LODs match the colour LODs.

## Checks and gates

- **Face and hands unchanged** (`head_check.py`): all 1,319 head-set triangles and all 802 hand triangles of the
  source exist in the reduced LOD0 with the same positions (max 0.0004 mm), UVs (identical) and normals (max
  difference 0.00014): the accepted face geometry, its smooth shading and its texture are the accepted ones.
  `grip_check.py`: the 1,025 hand/finger vertices keep their bind positions and weights exactly (the bow grip).
  Render diff of face front and both three-quarters (`review/face_diff.png`): no face pixel changes; only the
  decimated snakes in front of it shade slightly differently.
- **Structure** (`compare_glb.py`): nodes, skin, inverse binds, materials, images, textures, samplers, all 8 clips,
  mesh names/extras and variants identical ("DIFFERENCES none"); variants on all 8 primitives.
  `check_winding.py`: 0 inverted closed parts.
- **Bounds and floor** (`lod_check.py`, every frame of every clip, every LOD): rest bounds equal the source LOD0 at
  every LOD (top 1.800 m, 0.997 x 3.06 m); lowest point 0 in every standing clip, -8.1 mm in Death/Dead (source
  -8.8 mm); the tail never leaves the floor; no face stretches over 20x at any LOD.
- **Edge stretch** (`glb_stretch.py`): identical to the source in every clip (max 7.87 Death, 6.81 Attack: the
  source's own armpit-web vertices, kept exactly).
- **Humanoid gates** (`gates_glb.py`, the batch I `gates.py` measured on both GLBs the same way; `work/gates_src.json`,
  `work/gates_red.json`, `_surface` for contacts):

| clip | arms p99/max src -> red | hands | serpent | hair | contacts cm (surface) src -> red | floor skin / hair / hands cm |
|---|---|---|---|---|---|---|
| Standing | 1.37/1.88 -> 1.29/1.85 | 1.44/1.79 = | 1.36/1.95 -> 1.41/1.95 | 1.12/1.32 -> 1.12/1.46 | none = | 0 / 114.9 / 94.3 = |
| Walking | 1.38/1.95 -> 1.34/1.87 | 1.44/1.82 = | 1.68/3.19 -> 1.74/3.19 | 1.12/1.30 -> 1.12/1.43 | none = | 0 = |
| Running | 1.41/2.01 -> 1.39/1.90 | 1.40/1.88 = | 1.78/3.77 -> 1.89/3.77 | 1.11/1.30 -> 1.11/1.44 | R hand 0.6 -> 0.5 | 0 = |
| Attack | 1.91/3.01 -> 1.86/2.93 | 1.83/3.62 = | 1.44/2.07 -> 1.45/2.07 | 1.25/1.74 -> 1.25/1.78 | R hand 4.6 =, L forearm 1.7 -> 2.4, R forearm 3.0 -> 3.3 | 0 = |
| Hit | 1.37/1.86 -> 1.38/1.71 | 1.68/2.60 = | 1.33/1.88 -> 1.39/1.88 | 1.12/1.30 -> 1.12/1.44 | none = | 0 = |
| Fidget | 1.40/1.88 -> 1.31/1.84 | 1.43/1.77 = | 1.35/1.92 -> 1.40/1.92 | 1.17/1.43 -> 1.16/1.55 | none = | 0 = |
| Death | 1.74/3.55 -> 1.68/2.78 | 1.43/2.22 = | 2.40/5.85 -> 2.60/5.85 | 1.56/2.03 -> 1.50/2.30 | R hand 2.8 =, R forearm 0.4 -> 0 | -0.9 -> -0.8 / 0.8 -> 0.7 / 0.4 = |
| Dead | 1.66/3.07 -> 1.55/2.48 | 1.39/2.18 = | 2.40/4.77 -> 2.60/4.77 | 1.55/2.01 -> 1.47/2.25 | R forearm 0.3 -> 0 | -0.9 -> -0.8 / 1.1 -> 1.0 / 5.2 = |

  The source values match the batch I README. Contacts use the nearest skin surface point (`REA_SURFACE=1`); the
  batch I vertex-plane rule reads the right forearm 4-5 cm "inside" the decimated belly in every reduced clip
  (Standing included), an artefact of the sparser belly vertices, not visible in any close-up. The rattle region's
  highest point reads 18.0 cm instead of 17.6 (a 4 mm higher decimated tail top before the gold band).
- **Close-ups** straight from the GLBs, source vs reduced, textured and clay (`glb_close.py`, `glb_sheet.py`):
  `review/sheet_head.png` (face front, both three-quarters, side, back, hair from above, wide, side),
  `review/sheet_body.png` (torso, back and quiver, both bust sides, both hands, Attack draw hand, column belly, front
  coil, lower back, flank, tail from above, rattle, Death, corpse belly and coil, Walking),
  `review/sheet_f_serpent.png` and `review/sheet_de_*.png` (the rejected e62 belly jog vs the pick).
- **LODs**: `review/lods/sheet.png`, `review/lods/sheet_src_vs_red.png` (head and Attack per LOD, source vs reduced:
  same character; LOD2/3 are as coarse as the batch I LODs).
- **Viewer**: `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m282_reduce_claude
  --token <lease> check`: 48 switches (6 models x 8 clips), no console errors, failed []. Shots:
  `review/viewer_shots.png` (Standing and Attack, source | reduced).

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m282_reduce_claude/review/viewer/index.html`: batch I source
and reduced for tiers A, B and C (ramps baked by `viewer_variants.py`), bow and arrow added on their joints for review
only (`viewer_attach.py`), native reference frames and clip notes from the batch I manifest; opens on reduced tier A.

## For the user to review

- **Face front and both three-quarters:** geometry, normals and texture are the accepted ones exactly
  (`review/sheet_head.png`, `review/face_diff.png`).
- **Hair snakes at 45 %:** all 17 kept, same silhouette and paint; their shading is a little smoother in places.
  55 % (config d, 10,400 triangles) is the fallback if they read too simple.
- **Serpent** at 55 % with the visible belly scutes kept exactly; the front coil keeps its fold patches. The tail
  top/sides have long faces whose scale net shifts by a few texels (drift check), not visible in the close-ups.
- Reduction 15,494 -> 9,756 (-37 %); a quarter of LOD0 (head set, hands, rings, belly) is kept exactly.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m282_reduce_claude/export/mm7_m282.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m282_reduce_claude/export/mm7_m282_bow.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m282_reduce_claude/export/mm7_m282_arrow.glb --world mm7
```

The `actors.yml` binding in `../mm7_m282_claude/README.md` is unchanged (same file names, node `M282`, clips, socket
`Socket_Arrow_Release`, scale 88.4: the rest height is still 1.800 m). Then a [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md)
row. Rollback: `work/mm7_m282_source_pre_reduce.glb` (= the batch I export).

## Reproduce

Blender scripts run through `scripts/bl.sh` (`TOKEN=<lease>`, wraps `tools/run_creature_blender.sh`); python3 scripts
run from the project directory; `run_ladder.sh` uses a pymeshlab venv (path at its top).
1. `REA_NODE=M282 REA_GLB=level_generation/creatures/mm7_m282_reduce_claude/work/mm7_m282_source_pre_reduce.glb bl.sh import_source.py`;
   `bl.sh dump_mesh.py`, `bl.sh dump_groups.py`, `extract_basecolor.py work/mm7_m282_source_pre_reduce.glb`;
2. `bl.sh dump_pieces.py`, `m282_pieces.py`, `belly_faces.py`; belly keep = belly faces above 5 cm plus one vertex
   ring (`work/belly_keep.npy`); top keep = faces within 12 mm of the top (`work/top_keep.npy`);
   `REA_PATCH_R=0.06 patch_keep.py - work/patch_c.npy 0.094,-0.174,0.317 -0.157,-0.229,0.141 -0.186,-0.217,0.180 0.146,-0.339,0.324`;
3. `M282_EXTRA_KEEP=work/patch_c.npy,work/belly_keep.npy,work/top_keep.npy m282_sets.py f`;
4. `REA_WEIGHTS=component run_ladder.sh f f "1:0.45,2:0.8,3:0.7,4:0.55" 0.65,0.55` (pick r62);
5. `texture_drift.py f_r62`, `dark_slivers.py f_r62`, `rest_error.py`, `region_error.py`, `probe_max.py`;
6. `build_reduced.sh`; checks `head_check.py`, `compare_glb.py`, `grip_check.py ... M282`, `check_winding.py`,
   `REA_NODE=M282 bl.sh lod_check.py <glb> <label>`, `bl.sh glb_stretch.py <glb> M282`, `[REA_SURFACE=1] bl.sh
   gates_glb.py <glb> <label>`, `bl.sh lod_views.py <label>`, `bl.sh glb_close.py src=...,red=...`, `glb_sheet.py`;
7. viewer: `viewer_variants.py <glb> r100|r62`, `viewer_attach.py <viewer glb> <a|b|c> export/mm7_m282_bow.glb Bow`
   (and `..._arrow.glb Arrow`), `viewer_manifest.py "MM7 Medusa" r62 15494 9756` (clip notes and anchors then copied
   from the batch I manifest), `run_creature_review.py ... check`.
