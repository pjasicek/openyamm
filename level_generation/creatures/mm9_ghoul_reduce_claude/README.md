# MM9 Ghoul (`mm9_ghoul`, Ghast / Ghoul / Revenant) LOD0 reduction: candidate g60 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 60 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:ghoul` (owner ghoul-reduce-20261104;
`mm9:ghoul` was free). Source: the installed `assets_source/worlds/mm9/models/mm9_ghoul.glb` (sha256 4d4f30b80e06, identical to
`../mm9_ghoul_claude/export/mm9_ghoul.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no repaint.
**Not installed.** `../mm9_ghoul_claude/` was only read (its gates run from there on our GLBs; output written here).

| | LOD0 | body set (Ghoul_A) | head set (GhoulHead_A) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 9,988 | 5,304 | 4,684 | 4,983 | 1,774 | 813 |
| **g60 (`export/mm9_ghoul.glb` = `export/mm9_ghoul_g60.glb`, sha256 26f5094f2bc5)** | **8,448 (-15.4 %)** | 3,990 | 4,458 | 4,213 | 1,497 | 779 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips, skin, nodes, materials, `KHR_materials_variants` and all 8 images are byte-identical (`same_clips.py`).
`scripts/face_identity.py`: every exact face (face skin 2,912, teeth 668, eyes 122, skull plug 80, and the 1,886 exact body faces) is in
the candidate with byte-identical corner attributes.

## Measured first: protected share
Labels (`scripts/ghoul_labels.py`) from the creature's own pre-export face dump (`../mm9_ghoul_claude/work/faces.npz`, centroid match
to 1.5e-6 m); the faces export_ghoul.py added later are lining/rim (body) and the skull plug (head). Head set: face skin 2,912 (the whole
head-only shell: eyes' lids, brows, nose, mouth, lips, ears, jaw, chin; only 18 of its faces lie under the hair, `scalp_cover.py`, so
there is no hidden scalp to cut), hair 902, teeth 668, eyes 122, plug 80. Body set: skin 4,588 (hands 936), front/back flap 266 plus
their lining and rim 450. The body skin was already decimated to budget at the build (`reduce_ghoul.py`: 3,300 skin + 1,300 hands).
Exact share in the picked set: 56.7 %. A real cut can only come from the body skin, hands and hair, so ~15 % is about the limit here.

## What is kept and what is cut (set g, `scripts/ghoul_sets.py g flapc collf`)
- **Exact:** face skin, teeth, eyes, skull plug; both flaps with lining and rim (helper-driven, already low grids); the neck seam (body
  faces within 3 cm of a head-set vertex: the neck tube under the jaw); soles (1.2 cm); the claws (hand faces outside the hide region of
  the region mask: `finish_tex.py` painted them black); the skin the flaps ride on (`flap_keep.py`: skin faces within 2.5 cm of a flap
  vertex in any pose, mirrored; 314 faces) and the skin round faces that collapsed on candidate f60 (`collapse_keep.py`: Walking/Running
  left ankle, Fidget left wrist and one body face, 2.5 cm, mirrored; 146 faces).
- **Cut:** body skin at the ladder ratio 0.6 (2,884 -> 1,730 free faces), hands 0.7 with every finger and claw (534 -> 374), hair 0.75
  (902 -> 676).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Troglodyte's copy of the Highwayman's)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices; texture guard on the region mask (A) and the
shared base colour (B, C: every Ghoul tier is ramps over one base colour), per texture set. Here the head primitive is cut too (only the
hair group); `KEPT_PRIMS` is empty. LODs: `scripts/build_lods.py` (tools/build_actor_lods.py ratios 0.5/0.18/0.06, 4 influences, as the
Ghoul was built) with protected points snapped to the imported vertices (the brief's Lesser Demon lesson; here the import re-bases the
mesh by 1.109 m): soles, top, corpse contact of Death/Death2/Dead, claw tips per digit chain and toe, rest extremes. Then the Ghoul's own
`shrink_shadow_lods.py`, `carry_variants.py`, the Ghoul's `fix_winding.py` (flips 4 collapsed shadow-LOD parts, as in its build).

## Ladder (`scripts/run_mp.sh`; 1.98 m: p99 <= 5.94 mm, max <= 29.7 mm; `review/ladder_sheet_{a..g}.png`)
| set | change | step | LOD0 | p99 / max mm | IoU / SSIM | verdict |
|---|---|---|---:|---|---|---|
| a | base keep set, hands 0.7, hair 0.7 | **r60** / r50 | 8,236 / 7,910 | 5.84/18.7, 8.09/23.4 | .991/.997 | r60 pass; built: **front flap 4 mm into the cut thigh/belly skin** in Walking 8 f, Running 13, Dead 49/49, Death 13 -> 47 (installed 0 / 0 / 0 / 13) |
| b | a, hair 0.85 | r55 / r50 | 8,208 / 8,046 | 6.47, 7.86 | | fail |
| c | a + flap contact skin, hands 0.65 | r60 / r55 | 8,332 / 8,184 | 6.16, 7.36 | | fail (the kept flap skin was cheap to cut; the 40 % now came from elsewhere) |
| d | c, MP_MAXW 1.0, hands 0.7, hair 0.75 | r60 / r57 | 8,408 / 8,318 | 6.19/14.9, 6.81 | | fail |
| e | d, hands 0.6, hair 0.65, body 0.65 | r65 / r62 | 8,404 / 8,316 | 6.18, 6.76 | | fail (pooled-error attribution `err_pool.py`: hands and hair carried it) |
| f | c, hands 0.7, hair 0.75 | r63 / **r60** | 8,496 / 8,408 | 5.33, 5.93/20.8 | .987/.996 | pass; built: flaps identical to installed; collapse +1 face at L ankle (Walking, Running), L wrist and body (Fidget); Death2 L hand 2 -> 3 frames > 1 cm |
| **g** | f + collapse spots of f60 | **r60** / r58 | **8,448** / 8,390 | **5.87 / 20.8** (Death2), 6.06 | **.987 / .996** | **r60 PASS, picked** |

## Gates, installed -> g60 (`scripts/gates.sh`: the Ghoul's own gates; `review/gates_before/`, `review/gates_g60/`)
| Gate | installed | g60 |
|---|---|---|
| Collapse (`collapse_gate.py`, 30 fps) | 10,638 face-frames | **7,599**; no region's worst-frame count higher in any clip (Standing 647 -> 204, Fidget 2,651 -> ~1,640) |
| Arm/hand (`--outer-only --exact`) | Death L 1.0 cm 1 f; Death2 L 4.9 cm 2 f, forearm 5.3; R 1.2 cm | no value worse; finger max Running 3.11/3.09 -> lower; finger p99 within +-0.01 |
| Flaps (`flap_gate.py`, 48 fps) | Fidget 60/194, Death 13/73, Death2 3/73 at 1.1 cm, else 0 | **identical** |
| Jitter, like-for-like (`ref_swap.py`: the same mesh with `ghoul_clips1.glb`'s clips; `review/gates_jref/`) | 3 fails (Death L, Death2 L+R) | 4: the same plus **Death R shoulder skin 1.90 -> 2.06 mm/f2 (limit 2.0)**. Clips and vertices are the installed ones; the term is the 95th percentile over the shoulder vertices left in the mesh, so a smaller vertex set moves it. The raw gate against the old mesh reads 7 (Taunt L 2.68, AttackMelee L 6.21: the same population effect, both pass like-for-like) |
| Detached | 39 components, 0 detached | 39, 0 |
| Bone lengths, winding | 0 stretching / 0 inverted | same |
| Flat shading | body 0.01, head 0.00 | same |
| Texture quality | body atlas 58.6 %, stretch p90 1.11; head 61.0 %, 1.18 | 58.6 %, 1.13; 61.0 %, 1.19 |
| LODs (`lod_check.py`, every frame) | heights 2.054 / 2.053 / 2.056 / 2.050; LOD2/3 lost 3 cm of claw width; LOD3 Dead +1.8 cm, Death +1.7 cm over LOD0 | rest bounds = LOD0 at every LOD; lowest point per clip = LOD0 at every LOD; 0 stretched faces |

The LOD0 Death low point (-1.8 cm) and Walking (-0.8 cm) are the installed clips' (unchanged).

## Review
- Viewer (installed and g60 per tier, all 16 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_ghoul_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 96 switches, 0 failed, 0 console errors).
- Sheets read (all `review/`): `sheet_face_g60.png` (front close-up, 3/4, profile, low 3/4, party; every tier), `sheet_face_diff_g60.png`
  (|difference| x4: the face black in every view and tier; only hair, shoulders and chest differ), `crop_hair_profile_a.png`,
  `sheet_upper_g60_a.png` (Standing front/3-4/back, AttackMelee, Hit2, Fidget back), `crop_upper_u1_c.png`, `crop_upper_u3_a.png`,
  `sheet_body_g60_a.png`, `sheet_close_g60_a.png` (arms/claws, back, feet, AttackMelee, Hit chest, Dead, Running), `ladder_sheet_a.png`.
  `sheet_upper_g60_c.png`. Written, not read: `sheet_body_g60_{b,c}.png`, `sheet_close_g60_{b,c}.png`.
- What to look at: the hair mass in profile and from behind (0.75; outline unchanged, a few larger facets inside the strands), the
  elbow outline in the 3/4 (slightly more angular), the shoulders and chest in Hit/Hit2.

## Install (not run; on the user's OK)
`check_winding.py export/mm9_ghoul.glb` (0), `tools/install_model.py export/mm9_ghoul.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9`, then add to `../mm9_ghoul_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_ghoul_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_ghoul.glb`.

## Reproduce (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_ghoul_reduce_claude/before/mm9_ghoul.glb REA_NODE=Ghoul $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/ghoul_labels.py; $G scripts/flap_keep.py 0.025
$G scripts/collapse_keep.py export/mm9_ghoul_f60.glb collf Walking:ankle_L Running:ankle_L Fidget:wrist_L Fidget:body
$G scripts/ghoul_sets.py g flapc collf
SETS=g MP_GROUPS=1:0.7,2:0.75 scripts/run_mp.sh g 0.6,0.58      # mpqem -> reduce_ladder (error over every clip) -> compare
scripts/build_mp.sh mp_g_r60 export/mm9_ghoul_g60.glb             # swap_mp -> build_lods -> shrink_shadow_lods -> carry_variants -> fix_winding
scripts/gates.sh export/mm9_ghoul_g60.glb g60; REA_NODE=Ghoul $BL -P scripts/lod_check.py -- $PWD/export/mm9_ghoul_g60.glb g60
$G scripts/face_identity.py export/mm9_ghoul_g60.glb g; $G scripts/ref_swap.py export/mm9_ghoul_g60.glb work/jref_g60.glb
$G scripts/viewer_tiers.py export/mm9_ghoul_g60.glb red; python3 scripts/make_viewer_manifest.py ...; scripts/shots_queue.sh
scripts/upper_shots.sh; $G scripts/shot_sheets.py g60
```
(`collapse_keep.py` reads the f60 candidate: `SETS=f MP_GROUPS=1:0.7,2:0.75 scripts/run_mp.sh f 0.63,0.6` and `build_mp.sh mp_f_r60`.)
Many scripts in `scripts/` are copies from `mm9_troglodyte_reduce_claude/` that this route did not use (MeshLab ladder tools,
`pierce_keep.py`, `head_contact.py`, `trog`-era helpers).

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates and viewer stills
only); LOD1-3 and shadow meshes by eye (numbers only); tier B and C body/close sheets by eye (face sheet of every tier read; tier C upper
crop read); indoor light; Android.
