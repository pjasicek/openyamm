# MM9 Banshee (`mm9_banshee.glb`) triangle reduction, 2026-11-04

Batch row 5 of the MM9 reduction ([brief](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md),
[ledger](../REDUCTION_LEDGER.md)). No-retexture branch of the [retopology playbook](../RETOPOLOGY_PLAYBOOK.md): textures,
tiers, variants, clips, skin and nodes are the installed file's bytes; only geometry changes. No credits.
Lease `mm9reduce:banshee` (owner banshee-reduce-20261104), released at hand-off. **Status: ready for review, not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed (lining counted) | 14,994 | 7,481 | 2,681 | 908 |
| candidate `export/mm9_banshee.glb` | **11,378** (-24.1 %) | 5,673 | 2,664 | 894 |

Alternative kept for the reviewer: `export/mm9_banshee_r45H.glb`, the ladder's uniform r45 pick (sleeves at 47 %), 11,190 / 5,580 / 2,666 / 894; gates in `review/gates_r45/` (same LOD0).

Rollback source: `before/mm9_banshee.glb` (sha256 bfc3ff44291c..., identical to `mm9_banshee_claude/export/mm9_banshee.glb`).
Viewer (installed and reduced for each tier; switching keeps clip time and camera):
http://127.0.0.1:8912/level_generation/creatures/mm9_banshee_reduce_claude/review/viewer/

## What was reduced and what was kept

Per primitive, LOD0 outer triangles (the dress and cloak also carry a lining, the same triangles reversed, so their savings count twice):

| primitive | installed | candidate | |
|---|---:|---:|---|
| Torso (`Banshee`) | 1,100 | 492 | 45 %, 4 zero-area triangles dropped |
| Skirt | 1,584 | 712 | 45 % |
| ArmL / ArmR | 1,531 / 1,531 | 1,429 / 1,429 | sleeve 72 %; hands, claws and 4.5 cm of cuff kept |
| Cape / WingL / WingR | 318 / 322 / 320 | 142 / 144 / 144 | 45 % |
| Head, Neck, HairL, HairR | 4,188 / 359 / 602 / 595 | same | byte-identical on every LOD |

Kept exactly: the whole head primitive (face, mouth bag, teeth, eyes), the neck (gap tuck, colour fade), both hair
primitives, hands with fingers and claws (dominant `Zhand*`/`Zfing*`), the sleeve within 4.5 cm of the wrist rim (the
wrist sits inside the cuff; the printed cuff), every open boundary (hem, waist, primitive borders, tatter edges) and every
UV or normal seam. The head, neck and hair primitives of LOD1-3 are also copied from the installed file (`splice.py`):
Blender's LOD decimation is not bit-reproducible (a rebuild moved about 1 % of a LOD head's vertices).

## Why a pose-aware collapse instead of the MeshLab ladder

The dress and cloak are lattice cloth on MM9's chains that bends, flaps and turns over in every clip. The playbook's
MeshLab ladder (rest-pose quadric, `run_ladder.sh`, keep set as above) failed at the first step:

| MeshLab ladder (`selection_base.json`) | LOD0 outer | p99 / max mm | |
|---|---:|---|---|
| r80 (cloak 92 %) | 11,886 | 2.77 / **61.4** AttackRanged | fail: wings |
| r70 | 11,404 | 5.51 / 61.4 | fail |
| cloak kept, r70 (`selection_nocloak.json`) | 11,596 | 2.34 / **39.3** Death | fail: dress back in Death |

Flat at rest is not flat in pose. `scripts/mpqem.py` is a half-edge collapse (every output vertex is a source GLB
vertex, so positions, UVs, normals, joints and weights stay the source's: no weight transfer at all), scored per collapse
over 236 poses (every clip at 10 Hz) as mean + 0.1 x max of per-pose plane quadrics, plus a 5-D rest quadric of position
and UV against texture sliding. Checks: link condition, no normal flip at rest (dot >= 0.5) or in any pose (>= 0.2), no UV
flip, triangle quality not below min(0.2, old). The same Blender ladder (`reduce_ladder.py`, exact weights,
`compare_ladder.py`, limits for 1.843 m: p99 5.53, max 27.6 mm) measures it:

| pose-aware ladder (`selection_mp2.json`, `selection_mp3.json`) | LOD0 incl. lining | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| r60 | 12,220 | 2.53 / 22.9 | 0.9986 | 0.997 | pass |
| r50 | 11,528 | 3.98 / 22.9 | 0.9975 | 0.996 | pass |
| r45 | 11,190 | 5.46 / 26.5 | 0.9958 | 0.994 | pass (lowest) |
| r40 | 10,866 | 9.07 / 39.6 | 0.9942 | 0.992 | fail |
| **r45, sleeves 72 % (picked)** | **11,378** | 4.81 / 26.5 | 0.9960 | 0.994 | pass |

The ladder picks r45, at the knee (p99 5.46 of 5.53 mm). Its sleeves are past theirs: the left sleeve stopped at 173 free triangles with no allowed collapse left (target 164) and its worst collapse cost rose from 0.92 to 2.24 (r50 -> r45; the log prints it as "rms mm", it is the square root of an area-weighted quadric, not a distance), where MM9 bends the elbows 115 deg. The sleeves save little, so they take 72 % (`BansheeArmL:1.6,BansheeArmR:1.6`): +188 triangles, p99 5.46 -> 4.81 mm, max unchanged (26.5 mm, the cloak in Death). The Fidget2 elbow close-up (`detail_a.png` row 6) differs from the installed in the same way at 47 % and 72 % sleeves, so that difference comes from the reduced wing in front of the arm and the blended layering, not from the sleeve.

## Build (reproducible)

```sh
cd level_generation/creatures/mm9_banshee_reduce_claude
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_NODE=Banshee REA_GLB=level_generation/creatures/mm9_banshee_claude/export/mm9_banshee_runtime_lod0.glb $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/faces_info.py
scripts/run_mp.sh mp3 0.45 BansheeArmL:1.6,BansheeArmR:1.6      # mpqem -> ladder -> compare
cp work/mp_r45.npz work/mp_r45s.npz; scripts/build_cand.sh r45s; cp export/mm9_banshee_r45s.glb export/mm9_banshee.glb
```

`build_cand.sh` swaps the index buffers into the Banshee's own pre-mirror runtime LOD0 (`swap_mp.py`; the
`mm9_banshee_claude/export/mm9_banshee_runtime_lod0.glb` geometry equals the installed LOD0 mirrored, lining removed,
checked triangle by triangle), then runs the Banshee's runtime tail exactly as `build_runtime.sh`: LODs
(`build_lods.py`, see below), `shrink_shadow_lods.py`, `banshee_variants.py`, eye glow, `floor_fix.py`, `mirror_glb.py`,
`finish_blend.py` (lining, hand-first order), then `splice.py` puts the meshes into the installed GLB and reports anything
else that differs: nothing (materials, images, variants, skin, nodes, all 14 clips byte-identical). Checked: the same chain
fed the unreduced index buffers (`r100`) reproduces all four installed meshes byte for byte.

LODs: `tools/build_actor_lods.py` (as the model was built, 0.5 / 0.18 / 0.06, 4 influences) with per-material ratios
(`lod_ratios.py`: LOD2/3 of a primitive never coarser than the installed one) and the dress hem's bottom loop as protected
points. With plain ratios LOD3 lost the hem's lowest 8-16 mm and the torso's shoulders (38 triangles), and LOD3 height fell
to 1.746 m. Now every LOD keeps the installed bounds: height 1.7665 / 1.7665 / 1.7659 / 1.7618 m (installed LOD3 1.7620),
lowest point per clip equal to LOD0 at every LOD, no LOD face stretched over 20 x in any clip beyond the installed ones
(`work/lod_floor_r45s.log`, `work/lod_floor_installed.log`).

## Gates (installed -> candidate; `review/gates_installed/`, `review/gates_r45s/`)

Run with the Banshee's own scripts (`scripts/gates.sh`, outputs only in this project).

| Gate | Installed | Candidate |
|---|---|---|
| `check_winding.py` | 0 inverted | 0 inverted |
| `flat_shading_check.py` | torso/arms 0.00, skirt 0.02, cape/wings 0.16/0.12/0.10 | torso/arms/skirt 0.00, cape/wings 0.04/0.05/0.03 |
| `arm_hand_gate.py --exact --outer-only`, hands | Fidget2 L 2.9 cm 47 f; Taunt R 5.9 cm 2 f; AttackRanged 2.4/3.2 cm; Death 1.5/1.7 cm | same, Taunt R **3.1 cm 1 f** |
| same, forearm column | worst 5.7 cm (Fidget2) | worst 5.6 cm; Walking L 0.7 -> 5.0, Taunt L 1.9 -> 3.7, AttackRanged2 L 2.4 -> 4.5, others lower (AttackRanged L 4.7 -> 1.6, Death L 5.6 -> 1.9). `forearm_probe.py`: in both files the forearm lies 3.9-4.1 cm behind the cloak wing that hangs from it, nothing else over 0.5 cm; the gate's outer-surface filter just classifies the coarser wing differently |
| `jitter_gate.py` | 0 fails | 0 fails (clips identical) |
| `collapse_gate.py`, face-frames | 1,877 / 4,263 / 2,716 / 8,082 / 1,365 / 1,598 / 1,162 / 1,366 / 593 / 857 / 10,516 / 5,270 | 1,877 / 2,139 / 2,716 / 5,038 / 1,059 / 1,578 / 934 / 932 / 593 / 853 / 5,682 / 2,604 (Standing, Walking, Fidget, Fidget2, Taunt, AttackMelee, AttackRanged, AttackRanged2, Hit, Hit2, Death, Dead) |
| `fold_gate.py`, creases past 110 deg (worst frame) | Skirt 21 (Dead), WingL 21 (Fidget2), Cape 4 | Skirt 15, WingL 10, Cape 2; one clip worse: AttackRanged/Transition Skirt 8 -> 9 |
| `order_gate.py`, all clips | WingL/ArmL 19.6 %, WingR/ArmR 16.9 %, Skirt/ArmR 18.3 %, Cape/Torso 7.8 %, Neck/Torso 13.6 % | 20.7 %, 18.3 %, 11.2 %, 11.5 %, 10.2 %; head pairs 0 in both. Rest centres (bounding boxes) unchanged, so the engine's primitive order is the same |
| `cheek_gate.py` | | identical (head untouched) |
| `neck_gap_gate.py` | 8.3 mm | 8.3 mm |
| `bag_gate.py` | worst 4 | worst 4 |
| `detached_parts_audit.py --fps 24` | 75 components, 0 detached | 75 components, 0 detached |
| floor and LOD heights (`lod_floor.py`) | lowest point per clip, LOD0 | identical per clip at LOD0; LOD1-3 within 3 mm of the installed LOD; faces stretched over 20 x: LOD1 4 (AttackMelee) as installed, LOD2 0 (installed 2) |
| triangle quality (outer cloth, q < 0.2) | 0 cloth slivers; torso 99, arms 39 (pre-existing, locked) | 0; torso 88, arms 39 |

## Sheets (viewer shots, installed | reduced | |difference| x 4; read at full size by the builder)

- `review/sheets/face_{a,b,c}.png`: front close-up, 3/4, true profile, low 3/4, party distance, AttackMelee jaw. Face,
  mouth, teeth, eyes, hair: no difference in any tier; the only difference pixels are the shoulders at the frame edge.
- `review/sheets/body_{a,b,c}.png`: Standing front, 3/4, back; Walking 3/4 and back; AttackMelee; Fidget2 back; Death.
- `review/sheets/detail_{a,c}.png`: bodice and belt front, back of cloak and dress, chest trims, sleeves and wings in
  AttackMelee and Fidget2, Walking and Fidget2 cloak, Death and Dead dress.
- `review/ladder_sheet_mp2.png`, `review/ladder_sheet_mp3.png`: Blender ladder renders (opaque, untinted).

Viewer check (`tools/run_creature_review.py check`): 84 model/clip switches, 0 failed, no console errors.

## What to look at

The cloak and dress in motion (Walking, Fidget2, Death): the sheets are a third of their triangles and bend over fewer
rows; the silhouette edges, hem and tatters are the installed ones. The bodice trims and belt (torso at 45 %). The
elbows in Fidget2 and AttackMelee.

## Not checked

In game (not installed; the binding regression runs after install), Android, indoors, LOD switching distances in game,
the triangle order inside the reduced blended primitives against the installed one beyond the order gate.
