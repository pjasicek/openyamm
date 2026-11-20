# MM9 Skeleton Warrior / Master (`mm9_skelwar`, tiers skelwar_b / skelwar_c) LOD0 reduction (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 56 of
"MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md), prio 1 (monster, relaxed keep set). Lease `mm9reduce:skelwar`
(skelwar-reduce-20261104). Route: [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) no-retexture branch, organised per rigid
piece as `../mm9_skeleton_reduce_claude/` (whose scripts this project copies). No Meshy, no credits. `../mm9_skeletonwarrior_claude/`
(approved, frozen) was only read. **Status: candidate `export_d95/mm9_skelwar.glb` ready for review, not installed.**

Source: the installed `assets_source/worlds/mm9/models/mm9_skelwar.glb` (= `../mm9_skeletonwarrior_claude/export/mm9_skelwar.glb`,
sha256 56ac1e125ce8), copied to `before/mm9_skelwar.glb` (the rollback source). Candidate sha256 7bf3592bb1a2.

## Result

| | LOD0 | body outer (+ linings) | head set outer (+ linings) | scimitar | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 10,484 | 5,475 (+1,106) | 3,169 (+468) | 266 | 4,428 | 1,623 | 578 |
| **d95** | **8,838 (-15.7 %)** | 4,023 (+1,026) | 3,101 (+422) | 266 (byte-identical) | 3,668 | 1,350 | 578 (the installed one) |

Images, materials, textures, samplers, nodes, skin and inverse binds, all 21 clips (with the skirt-plate keys and the floor
passes), the root `KHR_materials_variants`, the LOD0 variant mappings and the mesh extras are byte for byte the installed file's
(`scripts/same_parts.py`: ALL SAME). Only geometry changed; the variants are carried to every LOD and shadow primitive.

**Why only ~16 %:** the body was already cut per part to fixed targets at assembly (`../mm9_skeletonwarrior_claude/scripts/sym_parts.py`),
so most pieces show 5-10 mm of error after their first 20-40 % of faces; the skirt plates are 20-54 faces each with torn hems;
and the skull face set (visible cranium 1,010, mandible 520, eyes 256, teeth ~400, neck 130), the scimitar, the grip faces of the
right fist, the three horns, the brow insignia and every piece of 30 faces or fewer stay exact (3,355 of 8,644 outer faces).
The brief's prop rebuild with a projection bake does not fit here: armour and boots share the 2K body atlas with the bones
(mirrored limbs share texels), so a rebuilt piece would need new texels in an image that must stay byte-identical; the scimitar
(own image) is already 266 triangles, a rebuild would save about 150.

## What was cut (`make_groups.py`, `face_flags.py`, plan `work/plan_d95.json`)

Each connected piece is its own decimation group (MeshLab texture-aware quadric, UVs kept, texture weight 4, boundaries kept so
hems and rims stay), measured alone at 0.9 .. 0.3 against its source piece (`sweep_groups.py`): closed stays closed, no new
self-intersection, volume 80-120 %, no face turned more than 70 deg from the source surface (FOLD_COS 0.34: config b stood a
2 x 8 cm face upright on a back skirt plate), rest-gap growth to every touching piece at most 1 mm; then each group takes the fewest
faces within max 9.5 mm / mean 1.5 mm (`plan_from_sweep.py`, 1.945 m creature).
- **kept exactly:** skull face = every cranium face that rays leave without hitting the head set (`face_flags.py`), mandible,
  eyes, teeth, the neck piece; right-hand faces within 5 mm of the scimitar in the solved fist + one ring (274); the three horns
  (cut at 0.5 they opened 2-3 mm off the helmet, `head_contacts.py`); brow insignia and the back helmet guard (fold check); every
  piece of <= 30 faces (small skirt plates, small guards); five pauldron sheets and two skirt plates (no passing step); scimitar.
- **cut:** cuirass 0.6 (inflated back to volume), spine column 0.7, boots 0.7, bracers 0.7, femurs and tibia stubs 0.6, humeri
  0.6, gauntlets 0.6 (right, grip excluded) / 0.7 (left; 0.6 failed the self-intersection check), cuffs, belt and hip bars 0.8,
  nine skirt plates 0.7-0.9, helmet shell 0.8, cheek guards 0.8, cranium faces hidden under the helmet 0.8.
- **linings** (`strip_lining.py` before the ladder, `export_cand.py` on export): reversed copies of every lined face, kept or
  reduced, on each set's own dark texel with the same weights: 1,106 -> 1,026 body, 468 -> 422 head.
- Weights: source vertices keep their source weights; new vertices take the nearest vertex of their own source piece (posed
  deviation from the installed surface at most 7.7 mm in Standing/Walking, `pose_dev.py`). Normals: vertices used only by kept
  faces take the installed normals (`keep_normals.py`), the rest smooth (installed flat-shading 0.01).
- LODs: `tools/build_actor_lods.py` (4 influences) at 0.5 / 0.18 / 0.075 with the soles, the spike top and the horn tips
  protected (`build_lods.py`), `shrink_shadow_lods.py`, `fix_lod_winding.py`, `carry_variants.py`; then **LOD3 and its shadow are
  the installed ones** (`keep_lod3.py`): every LOD3 rebuilt from the reduced LOD0 (0.06 and 0.075) lost the thighs and forearms,
  which the installed 578-triangle LOD3 keeps.

## Configurations (ladder over every clip, REA_HEIGHT_M 1.945: p99 <= 5.84 mm, max <= 29.2 mm, IoU >= 0.98)

| config | change | LOD0 | p99 / max mm | IoU | verdict |
|---|---|---:|---|---|---|
| a r70 / r80 / r95 | budgets 7/1.2, 8/1.35, 9.5/1.5; texture weight 1 | 8,994 / 8,688 / 8,506 | 3.97 / 4.60 / 5.19, max 14.45 | 0.991 / 0.989 / 0.988 | pass; LOD3 lost legs (fixed for all) |
| b r95 | texture weight 4 (brief update: Trellborg) | 8,650 | 5.20 / 14.45 | 0.990 | pass; textured close-ups 12 % nearer the installed; one skirt face folded upright, which the skirt gate read as the left femur 11.6 cm "through" a back plate in Walking/Backpedal |
| c r95 | + fold check (> 70 deg) | 8,772 | 4.98 / 14.45 | 0.991 | pass; horns cut at 0.5 sat 2-3 mm off the reduced helmet |
| **d r95** | **+ horns kept** | **8,838** | **4.97 / 14.45** | **0.992** | **pass, picked** |

The ladder's textured renders show every candidate black (the imported material multiplies the source's white `COLOR_0`, which
the candidates lack), as in the skeleton reduction; the textured comparison is the GLB close-ups and viewer shots below.
The max (14.45 mm, Resurrect frame 51) is the same at every step.

## Gates (installed -> d95; `scripts/gates.sh` = the creature's own gate scripts copied here; `review/gates_before/`, `review/gates_d95/`)

| gate | installed | d95 |
|---|---|---|
| winding | 0 | 0 |
| flat shading body / head / scimitar | 0.01 / 0.01 / 0.27 | 0.01 / 0.01 / 0.27 |
| texture quality body: atlas, fragments, stretch p90 | 67.3 %, 0.4 %, 1.13 | 66.8 %, 1.9 %, 1.19 (head 64.4 % -> 63.9 %, stretch 1.10 -> 1.12) |
| skirt gate (thigh through plates, frames / deepest cm) | Walking 0, Backpedal 0, AttackMelee 16/7.6, AttackMelee2 29/4.1, AttackRanged 11/1.9, Hit 19/2.3, Death 20/9.6, Resurrect 44/19.6, AttackMeleeOld 14/4.1, AttackRangedOld 2/0.7, Death2 11/0.9, BackpedalRun 4/3.9 | Walking 0, Backpedal 0, AttackMelee 15/7.7, AttackMelee2 29/4.1, AttackRanged 10/1.6, Hit 15/2.3, Death 18/8.5, Resurrect 44/19.7, AttackMeleeOld 12/4.2, AttackRangedOld 0, Death2 11/1.0, BackpedalRun 4/3.8 |
| arm/hand (`--outer-only --exact`), changes only | | AttackMelee2 L hand 0 -> 4.5 cm (1 frame: the left fist at a skirt plate's edge, the same contact in both files, `review/sheet_am2_left_hand_b95.png`); Hit L 2 -> 3 frames, L forearm 0 -> 4.1 cm (bracer at the side plates, same in both, `review/sheet_hit_left_arm_c95.png`); ResurrectSpell L 2 -> 3 frames; the rest equal within 0.3 cm |
| finger stretch p99/max L, R, throw | 1.19/1.37, 1.33/1.78, 3.63 | 1.20/1.61, 1.35/1.78, 2.75 |
| detached parts (24 fps, 701 poses) | 13 flagged: 9 helmet guards "lifted" off the cuirass (12.9-156.5 mm; the creature README's known false positives: rigid on Bip01 Head with the shell) and 4 skirt plates (24-114 mm, 1-2 frames each, "base lifted" against bind neighbours) | 12 flagged: 9 helmet guards (8.5-62 mm), the kept horn on the -x side "parted" 20.8 mm (26 poses; it is rigid on Bip01 Head with the shell, its rest gap 7.9 -> 6.0 mm), 2 skirt plates (96 mm Skirt_front_R in 2 Walking frames, 117.5 mm Skirt_front in 1 Dead2 frame); the Walking frame rendered identical (`review/sheet_walk_plates_d95.png`); no bone, limb or hand piece flagged |
| LOD heights LOD0-3, faces stretched > 20x | 2.0286 / 2.0286 / 2.0286 / 2.0002 m; 0 | 2.0286 / 2.0286 / 2.0286 / 2.0002 m; 0 |
| lowest point Standing / Dead / Dead2, all clips | 0 / +0.94 / 0 cm, -1.54 cm (Running) | identical at LOD0; LOD1/2 Standing +0.6 / +0.4 cm |
| jitter, bone lengths, handedness, floor audit | | not rerun: clips and skin byte-identical (floor audit and binding regression run after install) |

Gate notes: the skirt gate labels vertices by the nearest master vertex, so this copy votes one label per connected piece (the
installed file relabels 0); `SKIRT_K` widens its nearest-face search (both files equal at 96). The sweep's joint-gap rule
compares each cut piece with its uncut neighbours; `pair_gaps.py` measures the rest gaps between touching pieces after the whole
cut (vertex to face): boots/tibia stubs and gauntlets/bracers close (0.86 -> 0, 0.06 -> 0 mm), the helmet pieces grow at most
0.45 mm, the spine column/belt 1.1 mm, and the lowest pauldron strip (kept) sits 2.6 -> 6.6 mm (R) and 0.4 -> 3.9 mm (L) off the
cut cuirass; the chest, back and shoulder close-ups do not show it (sampled surfaces still touch: 0.01 -> 0.26 mm). A sweep that
also finds neighbours through large faces (`GAP_SEARCH=0.03`, `sweep_e.json`) plans the same except two skirt/tibia groups.

## Review

- Viewer, installed and reduced per tier (clip time and camera kept on switching, all 21 clips):
  http://127.0.0.1:8912/level_generation/creatures/mm9_skelwar_reduce_claude/review/viewer/ (`run_creature_review.py check`:
  84 switches, 0 failed, no console errors).
- Sheets (read): `review/sheet_face_{c,b}_d95.png` (viewer: face front, 3/4, profile, rear; installed | d95 | diff x4: the skull
  face is black in every diff), `review/sheet_body_{c,b}_d95.png` (Standing front/3-4/back, Walking, Running, AttackMelee, arms,
  shoulders, skirt, feet), `review/sheet_glb_face_d95.png` (GLB close-ups: face front, 3/4, profile, low 3/4, party, back of
  head; tex and clay), `review/sheet_glb_body_d95.png`, `review/sheet_glb_hands_d95.png` (both fists, the grip, arm, attack,
  death), `review/sheet_gate_frames_d95.png` (the gate frames: Walking/Backpedal skirt from behind and the side, AttackMelee2 and
  Hit left hand), `review/sheet_lods_d95.png` (LOD0-3: 3/4, attack, head, hand). Earlier steps: `review/sheet_*_a95.png`,
  `*_b95.png`, `*_c95.png`, `review/ladder_sheet_{a,b,c,d}.png`.

## Install (not run; on the user's OK)
`check_winding.py export_d95/mm9_skelwar.glb` (0), `tools/install_model.py export_d95/mm9_skelwar.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py --match 'MM9 Skeleton Warrior*'`, then add to
`../mm9_skeletonwarrior_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_skelwar_reduce_claude`; a rebuild from
this project must re-run that reduction". Rollback: `before/mm9_skelwar.glb`.

## Reproduce (project folder; PYTHON = `../claude_shared/gltf_venv/bin/python -I`, MESHLAB = `../claude_shared/meshlab_venv/bin/python -I`)
`lining_pairs.py before/mm9_skelwar.glb 0|1 work/lining_p{0,1}.npy`, `strip_lining.py before/mm9_skelwar.glb work/source_nolining.glb
work/lining_p0.npy work/lining_p1.npy`; `REA_GLB=level_generation/creatures/mm9_skelwar_reduce_claude/work/source_nolining.glb
REA_NODE=SkelWar` Blender `import_source.py`, `dump_mesh.py`, `dump_weights.py`; `face_flags.py`, `make_groups.py`;
`TEXW=4 FOLD_COS=0.34 GAP_SEARCH=0.03 SWEEP_OUT=sweep_e.json sweep_groups.py` (MESHLAB; d95 was planned from the identical sweep
without GAP_SEARCH, `sweep_c.json`), `FIXED=43:0.8,37:1.0,42:1.0,44:1.0 SWEEP=sweep_c.json plan_from_sweep.py 9.5 1.5 work/plan_95.json`,
`TEXW=4 FOLD_COS=0.34 REA_HEIGHT_M=1.945 run_ladder.sh d 95`, `LADDER=d EXPORT=export_d95 build_export.sh 95`, `viewer_tiers.py`,
`viewer_manifest_skelwar.py`, `glb_close.py`, `pair_sheet.py`, `shot_sheet.py`, `lod_check.py`, `lod_views.py`, `gates.sh`,
`same_parts.py`, `head_contacts.py`, `pair_gaps.py 95`, `flip_check.py`, `pose_dev.py`.
`work/mesh_r95.npz` and `work/keep_r95.npy` hold d (each config overwrote them).

## Not checked
In game (not installed; the binding regression and floor audit run after install); the viewer's playback at normal speed (shots
and GLB frames only); LOD1/LOD2 only in the four LOD views; the Warrior tier only in viewer shots (GLB close-ups are the Master
tier); 30 body and 2 head faces whose normal is 90-95 deg from the single nearest installed face (`flip_check.py`; thin bracer
rims, tibia stubs, finger sides and hip bars, where the nearest face is the opposite wall; the decimation's 3-face check passed them).
