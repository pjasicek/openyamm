# MM9 PeasantM8d (`mm9_peasantm8d`, the old elf commoner, row 85) reduction: candidate c r60 ready for review (2026-11-05; lease released)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 85 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm8d` (owner
peasantm8d-reduce-20261105); the creature's own `mm9:peasantm8d` lease was free (no lease file). Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm8d.glb` (sha256 d2fecd852909, identical to `../mm9_peasantm8d_claude/v2/export/mm9_pm8d.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm8d_claude/` was only read
(its `v2/scripts/arm_hand_gate.py`, `jitter_gate.py`, `shrink_shadow_lods.py` and `v2/work/mm9_pm8d_clips.glb` run in place; its
`scripts/see_through_gate.py` and `sleeve_poke_gate.py` copied). Scripts started from `../mm9_peasantm7d_reduce_claude/scripts/`.

**Family note:** PeasantM8d is Forad Darre's body (`mm9_forad.glb`, row 69, deferred) with elf ears and its own paint. PeasantM8
(`mm9_peasantm8.glb`, row 93) and PeasantM4 (row 92, torso reshaped) are built on the same Forad body (their creature READMEs), each as
its own GLB with its own head shell (M8 has no ponytail or necklace). Only `mm9_peasantm8d.glb` was reduced here; the sets
(`make_sets_m8d.py`) and the route fit them with their own head classes, but this cut is not carried over.

| | LOD0 | body prim (tunic, sleeves, breeches, boots: one welded piece, 187 linings) | head prim (head shell, ponytail, ties, hands) | LOD1 | LOD2 | LOD3 | shadow LOD0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 7,834 | 3,677 | 4,157 | 3,916 | 1,408 | 465 | 7,834 |
| **c r60 (`export/mm9_peasantm8d.glb` = `export/mm9_peasantm8d_c60.glb`, sha256 0cf8dc5f7623)** | **6,640 (-15.2 %)** | 3,227 | 3,413 | 3,317 | 1,191 | 393 | 6,640 |

Per group (free faces cut): hands 1,201 -> 721 (0.6, every finger kept; 197 graft faces exact), ponytail 530 -> 370 (0.7), scalp hair
345 -> 241 (0.7), breeches/boots 1,215 -> 899, tunic free 642 -> 508 (the guards stop it); linings 187 -> 187 (138 installed, 49
re-emitted). Every vertex of the candidate is an installed vertex (only index buffers changed). Clips (10), skin, nodes, materials,
all 6 images identical (`same_clips.py`). Exact head shell (1,748 faces: face skin, ears, neck, brows, moustache, forelock and sideburns,
the hairline ring, the collar band in the head material) and the two ponytail ties (136): present exactly (`scripts/exact_head.py`).

## Measured first: protected share
Parts (`scripts/analyze.py`, `scripts/head_classes.py`, `review/uv_PeasantM8dHead.png`): body prim = one welded piece (3,677, 260
one-texel faces: 187 paired linings, rim strips); head prim = one shell (2,093: by head-texture colour 1,281 skin, 600 hair, 212 tunic
collar band), the ponytail (530), two ponytail ties (70 / 66), two MPFB hands (699 / 699). Keep set a: 2,886 faces (36.8 %); about
15-24 % looked reachable from hands, hair and cloth, so the run went ahead. Final set cs: 3,901 protected (49.8 %).

Set cs (`scripts/make_sets_m8d.py cs`, env `SHOULDER=1 PANEL=1 DEV=75 DEV_RING=0 FRONT_Z=0.05 BACK_Z=-0.02 BACK_Y=1.66 HANDS=hand_contact_0.04.npy`):
exact shell = every skin face + every hair face in front of z 0.05 + one ring of hair round them (skin-coloured texels inside the
back scalp hair above y 1.66 count as hair); ties; collar (body faces within 1 cm of the head prim); cuffs and graft (within 4 / 1.5 cm
of a hand vertex); soles; rim strips, loose linings and their halo; hand contact (`hand_contact_dm2.py`, 4 cm, every clip); shoulder
cloth (body faces with a Clavicle/UpperArm dominated vertex: 768); the tunic front panel (|x| < 0.16, 1.02 < y < 1.40, z > 0.04:
both lapels and the panel between, 279 more); fold faces (corner normal more than 75 deg off the face normal, 21 more).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM7d's copy)
Chart guard `MP_CHART=1`, texture guard on the single tier (`scripts/tex_extract.py`: each primitive's base colour as A = B = M),
texture weight 4, seam slides on the hands, scored over every clip at 10 Hz, distance guard 4 mm on every group, linings re-emitted
from `work/twins.npz`.

## Ladders (limits for 1.758 m: p99 <= 5.27 mm, max <= 26.4 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a, hands .6, ponytail .7, scalp .7, legs .6, tunic r60/r50 (identical), distance guard 5 mm (7 on tunic and legs) | 5,946 (-24.1 %) | 5.44 / 18.6 (Walking:15) | .992 / .992 | fail (p99 over 5.27; errors > 5 mm on upper arms, belt and calves) |
| b | a with a 4 mm guard everywhere, legs .65; r60 = r70 | 6,340 (-19.1 %) | 3.20 / 12.9 (Cower:12) | .995 / .994 | ladder pass; built b60: UV audit 0, see-through equal, LODs fine, but (1) a dark shading blob on the lower corner of the model's left lapel above the belt (`review/crop_front_hip_b60.png`, close-up c13 in `review/close_b60_4.png`), (2) a new jitter fail: AttackMelee R shoulder skin excess 1.32 -> 4.97 mm/f2 (limit 2.0; p95 over fewer shoulder vertices, max 187.21 -> 187.76) |
| **c** | **b + shoulder cloth, tunic front panel, fold faces kept (set cs)** | **6,640 (-15.2 %)** | **2.99 / 9.9 (AttackMelee:12)** | **.996 / .995** | **PASS, picked; every gate equal** |

## Gates, installed -> c r60 (`scripts/gates.sh` with the creature's own gate scripts; `review/gates_before/`, `review/gates_c60/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_c60.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 escapes come from the LOD tool's decimate, near the installed file's own (body/head LOD1 155/152, LOD2 139/168, LOD3 57/85;
  installed LOD1 129/109, LOD2 151/158, LOD3 66/101).
- Arm and hand (`--outer-only --exact`, 48 fps): equal in every clip (Talk L 3.5 cm 40 frames, MM9's hand on the heart, as installed;
  Fidget R forearm 1.2 cm as installed); finger stretch maxima equal, minima within 0.07; wrists equal; 19 chains per hand.
- Jitter vs MM9's untouched clips: identical text both (5 fails, the creature's accepted ones: Walking L/R, Talk L, Death L/R shoulder skin).
- Sleeve poke: identical per clip (candidate vertices L 89 -> 88). Linings (`lining_gate.py`): identical per clip.
- See-through (creature's gate, every 3rd 30 fps frame, 16 views): identical (sleeve R 10 px Running 6, sleeve L 4 px Talk 33, every
  other zone 0, both).
- Detached parts 0 both (6 components); flat shading 0.00 both; winding 0; bone lengths 12 checked, 0 stretching. Texture quality:
  body atlas 53.3 % both, stretch p90 1.09 -> 1.10; head 45.1 -> 45.0 %, stretch 1.23 -> 1.22, fragments 2.4 -> 3.6 %.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: ratios 0.5/0.18/0.06, 4 influences, soles/crown/
  corpse contact protected and snapped, 38 of 38 mapped): height 1.7872 m at every LOD; lowest point at LOD1-3 equal to LOD0 in every
  clip (installed LOD2 floated up to 0.7 cm, LOD3 up to 1.1 cm: Standing 0.97, Dead 1.1); 0 stretched faces at every LOD, both.
  Logs `work/lod_check_{installed,c60}.log`.

## Review
Viewer (installed and reduced, the one tier, all 10 clips; `run_creature_review.py check`: 20 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm8d_reduce_claude/review/viewer/
Sheets read (installed left/above, c60 right/below): `review/sheet_face_c60.png` and `review/sheet_face_diff_c60.png` (front close-up,
3/4, profile, low 3/4, party: face skin, ears, brows, moustache and neck black in all five diffs; only the scalp hair behind the
hairline and the ponytail differ), `review/sheet_body_c60_a.png` (Standing front/3-4/back, Walking, Fidget, Death),
`review/close_c60_{1,2,3,4}.png` (arms, tunic front/back, Running, boots, Talk arms, shoulders and ponytail from behind, Hit, L/R hands
and cuffs, hair from behind above, sleeve, lacing, lapels and belt buckle, boot cuffs), `review/close_c60_fingers.png` (R hand and
fingers close), `review/crop_boot_cuff_c60.png`; for b60: `review/sheet_face_b60.png`, `review/sheet_body_b60_a.png`,
`review/close_b60_{1,2,3,4}.png`, `review/crop_front_hip_b60.png` (the lapel blob); `review/ladder_sheet_a.png`, `review/sets_a_{head,body}.png`.
Look at: the scalp hair and ponytail in profile (0.7: hair-texture strands at slightly different angles in the diff, outline and
hairline the same), the hand backs (0.6: a few flatter planes at the knuckles), the R boot cuff's top rim (a slightly darker corner
in `review/crop_boot_cuff_c60.png`, the only shading change found on the body).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm8d_reduce_claude/before/mm9_peasantm8d.glb REA_NODE=PeasantM8d $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_classes.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
SHOULDER=1 PANEL=1 DEV=75 DEV_RING=0 FRONT_Z=0.05 BACK_Z=-0.02 BACK_Y=1.66 HANDS=hand_contact_0.04.npy $G scripts/make_sets_m8d.py cs
REA_HEIGHT_M=1.758 MP_DMAX_MM=4 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=cs MP_GROUPS=1:0.6,2:0.7,3:0.65,6:0.7 scripts/run_mp.sh c 0.6
scripts/build_mp.sh mp_c_r60 export/mm9_peasantm8d_c60.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants (none) -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm8d_c60.glb before/mm9_peasantm8d.glb --json review/uv_audit_c60.json
$G scripts/exact_head.py export/mm9_peasantm8d_c60.glb cs
work/queue_c60.sh   # gates.sh, see_through.sh, lod_check.py (installed: work/queue_b60.sh)
python3 scripts/make_viewer_manifest.py c60 "inst_a=installed 7,834=before/mm9_peasantm8d.glb" "red_a=reduced c r60 6,640=export/mm9_peasantm8d_c60.glb"
HEADUP=0,0.08,0.05 scripts/shots.sh "inst_a red_a"; scripts/close_shots.sh "inst_a red_a"; $G scripts/shot_sheets.py c60; $G scripts/face_diff_sheet.py c60
$G scripts/close_sheet.py c60 a c0,c1,c2,c3 review/close_c60_1.png   # ... _2 .. _4
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm8d.glb` (0), `tools/install_model.py export/mm9_peasantm8d.glb
--world mm9 --name mm9_peasantm8d.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantm8d_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantm8d_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantm8d.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); a close-up of the left hand's fingertips (the L hand appears at
medium range in c0, c1, c5, c9).
