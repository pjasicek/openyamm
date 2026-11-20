# MM9 PeasantM4 (`mm9_peasantm4`, the old prisoner, row 92) reduction: candidate c r50 (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 92 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm4` (owner
peasantm4-reduce-20261105); the creature's own `mm9:peasantm4` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm4.glb` (sha256 647521a7d859, identical to `../mm9_peasantm4_claude/v2/export/mm9_pm4.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm4_claude/` was only
read (its `v2/scripts/arm_hand_gate.py`, `jitter_gate.py`, `shrink_shadow_lods.py` and `v2/work/mm9_pm4_clips.glb` run in place).
Scripts: PeasantM7's reduction copies (`../mm9_peasantm7_reduce_claude/`, from PeasantM7d's) with names `PeasantM4` / `PeasantM4Head`
and one tier; keep sets from `../mm9_peasantm8d_reduce_claude/scripts/make_sets_m8d.py` + `head_classes.py` (copied, only read there:
same Forad/PeasantM8 body and head layout) with a FOOT option added.

**Family note:** PeasantM4 is PeasantM8's mesh (`mm9_peasantm8.glb`, row 93, queued; PeasantM8d row 85 is being reduced by its own
agent) with the torso reshaped (positions only, same topology, UVs and weights) and its own paint. Only `mm9_peasantm4.glb` was cut
here; the same keep set and route would carry to PeasantM8, but its positions differ, so it needs its own run.

| | LOD0 | body prim (shirt, vest, trousers, boots, cuffs, linings) | head prim (head shell, hands) | LOD1 | LOD2 | LOD3 | shadow LOD0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 7,168 | 3,677 | 3,491 | 3,582 | 1,288 | 427 | 7,168 |
| a r60 (superseded: belly texture slide, export kept for the record) | 5,892 (-17.8 %) | 2,881 | 3,011 | 2,943 | 1,057 | 351 | |
| **c r50 (`export/mm9_peasantm4.glb` = `export/mm9_peasantm4_c50.glb`, sha256 f1fcf5ff62dd)** | **5,990 (-16.4 %)** | 2,979 | 3,011 | 2,991 | 1,076 | 356 | 5,990 |

Per group (free faces cut): hands 1,201 -> 721 (0.6, every finger kept; 197 graft/cuff faces exact), trousers and boots 1,229 -> 755
(0.55 asked, the guards stop at 0.61), shirt/vest 649 -> 425 (0.5 asked, guards stop), body linings 104 (re-emitted: 103 installed
faces kept, 1 re-emitted). Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the
installed bytes; only index buffers changed). Clips (11), skin, nodes, materials, all 6 images identical (`same_clips.py`). The whole
head shell (face, ears, neck, bald scalp and its painted white fringe, 2,093) and every kept face present exactly (`scripts/exact_head.py`,
`review/exact_c50.txt`).

## Measured first: protected share
Parts (`scripts/analyze.py`): body prim = one welded piece (3,677: shirt and vest with sleeves, trousers, boots and boot cuffs; 260
zero-UV faces = 103 lining pairs + 157 rim strips/loose linings, `twins.py`); head prim = the head shell (2,093: face, ears, neck,
bald scalp; `head_classes.py`: 1,644 skin, 371 painted white hair, 78 collar band) and two MPFB hands (699 / 699). Keep set a
(`make_sets_m8d.py`, `FRONT_Z=-9` keeps the whole shell: the hair is paint on the bald head, not a shell of its own): shell, collar,
graft junction and cuffs (Forad's bracer sleeves: 484 cuff + 560 graft faces), soles, rim strips, loose linings and their halo, shoulder
cloth (768), hand contact (71) = **3,845 faces (53.6 %)**, free 3,323; 15 % needed 32 % of the free part, so the run went ahead.
Set c = a + the front panel between belt line and chest (`PANEL=1`, |x| < 0.16 m, 1.02-1.40 m, z > 0.04: 281 faces) = 4,089 (57.0 %),
free 3,079. Set b (c + both boot feet below 10 cm + one ring, PeasantM7d's streak fix) probed at 6,146 (-14.3 %): under 15 %, and the
a60 boots read the same as installed at close range (`review/crop_boot_R_a60.png`), so not used.

## Route
PeasantM7d's pose-aware half-edge collapse (`scripts/mpqem.py`): chart guard, texture guard on each material's colour image (one tier,
no region masks: `scripts/tex_extract.py` writes the image as A, B and M), texture weight 4, seam slides on the hands, every clip (11)
at 10 Hz, distance guard 5 mm (7 mm on shirt/vest and legs), linings re-emitted from `work/twins.npz`.

## Ladders (limits for 1.787 m: p99 <= 5.36 mm, max <= 26.8 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,c}.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a, hands .6, legs .6, shirt/vest r60 (r50 identical) | 5,892 (-17.8 %) | 4.72 / 12.8 (Running:0) | .995 / .994 | ladder pass; built a60: UV audit 0, numeric gates equal, but the belly close-up (c13) showed a diagonal crease and a smeared, slid cream texture on the shirt panel below the lacing (`review/crop_belly_a60.png`). Superseded |
| **c** | **a + front panel exact, legs .55, shirt/vest r50** | **5,990 (-16.4 %)** | **4.58 / 12.8 (Running:0)** | **.995 / .994** | **PASS, picked; belly = installed (`review/crop_c13_inst_a60_c50.png`: installed, a60, c50)** |
(b, the probe with the feet kept: 6,146, -14.3 %, mpqem only.) Two ladders.

## Gates, installed -> c r50 (`scripts/gates.sh` with the creature's own arm/hand (`--outer-only --exact`) and jitter scripts; `review/gates_before/`, `review/gates_c50/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_c50.json`): **0 escaping LOD0 faces in both primitives**
  (a60 also 0). LOD1-3 escapes come from the LOD tool's decimate, near the installed file's own (body/head: LOD1 127/123 vs installed
  111/101, LOD2 116/122 vs 125/120, LOD3 48/71 vs 64/82).
- Arm and hand (48 fps): equal in every clip (Talk L 3.4 cm 38 frames both: MM9's hand on the heart; forearm Fidget R 2.3 -> 1.6 cm,
  Fidget L 0.7 both); finger stretch maxima equal, minima within 0.11; wrists equal.
- Jitter vs MM9's untouched clips: identical output (the creature's accepted 5 fails unchanged). Sleeve poke: identical per clip and side
  (rest 0; Forad's bracer bends: Hit R 24.3, Talk L 16.3, Death L 10.8 mm as installed). Linings (`lining_gate.py`): identical per clip.
- See-through (`scripts/see_through_gate.py`, every 3rd 30 fps frame of all 11 clips, 16 views; worst px installed -> c50): head,
  torso, boots, trousers 0 -> 0; sleeve L 4 -> 4 (3 frames both), sleeve R 12 -> 12 (4 -> 5 frames): Forad's one-pixel cuff-rim slivers.
- Detached parts: 0 both (the same two shallow hand notes). Flat shading 0.00 both. Winding 0. Bone lengths 0 stretching. Texture
  quality: body atlas 53.3 % both, stretch p90 1.42 -> 1.40; head 44.0 % both, stretch 1.24 -> 1.23, fragments 2.7 -> 4.2 % (the cut
  hands' small islands).
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`, 36 of 36 protected points mapped): height 1.7872 m at
  every LOD; lowest point at LOD1-3 equal to LOD0 in every clip (installed LOD2 +0.28..+1.05 cm and LOD3 +0.75..+1.3 cm above LOD0,
  installed LOD3 height 1.7839); 0 stretched faces at every LOD, both.

## Review
Viewer (installed and reduced, all 11 clips; `run_creature_review.py check`: 22 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm4_reduce_claude/review/viewer/
Sheets read (installed left/above, reduced right/below): `review/sheet_face_a60.png`, `review/sheet_face_diff_a60.png`,
`review/sheet_face_diff_c50.png` (front close-up, 3/4, profile, low 3/4, party: the head black in every diff; the party view differs only
on the shoulders), `review/sheet_body_a60_a.png`, `review/sheet_body_c50_a.png` (Standing front/3-4/back, Walking, Fidget, Death),
`review/close_a60_a_{1,2,3,4}.png` and `review/close_c50_a_{1,2,3,4}.png` (arms, vest front/back, Running, boots, Talk arms, shoulders
from behind, Hit, L/R hands and cuffs, scalp from behind above, sleeve, belly below the lacing, boot cuffs), `review/crop_belly_a60.png`,
`review/crop_c13_inst_a60_c50.png`, `review/crop_boot_R_a60.png`, `review/sets_a_body.png`. Generated, not opened: `review/sheet_face_c50.png`
(the shell is exact; its diff was read), `review/crop_c4_inst_a60_c50.png`, `review/sets_{a,b,c}_{head,hands}.png`, `review/ladder_sheet_{a,c}.png`.
Look at: the belly below the lacing (fixed in c), the hand backs (0.6), the boots (cut at 0.61; the feet are not kept exact here).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm4_reduce_claude/before/mm9_peasantm4.glb REA_NODE=PeasantM4 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_classes.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
PANEL=1 FRONT_Z=-9 SHOULDER=1 HANDS=hand_contact_0.04.npy $G scripts/make_sets_m8d.py c
REA_HEIGHT_M=1.787 MP_DMAX_MM=5 MP_DMAX_GROUPS=0:7,3:7 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.6,3:0.55 scripts/run_mp.sh c 0.5
work/queue_c.sh   # build_mp.sh mp_c_r50 -> UV audit, exact_head.py, gates.sh, see_through.sh, lod_check.py (installed: work/queue_a60.sh)
python3 scripts/make_viewer_manifest.py c50 "inst_a=installed=before/mm9_peasantm4.glb" "red_a=reduced c50=export/mm9_peasantm4_c50.glb"
HEADUP=0,0.08,0.05 scripts/shots.sh "inst_a red_a"; scripts/close_shots.sh "inst_a red_a"; $G scripts/shot_sheets.py c50; $G scripts/face_diff_sheet.py c50
```
(a: `FRONT_Z=-9 SHOULDER=1 HANDS=hand_contact_0.04.npy make_sets_m8d.py a`, `SETS=a MP_GROUPS=1:0.6,3:0.6 run_mp.sh a 0.6,0.5`; its shots
are in `review/shots_a60/`, `review/shots_close_a60/`.)
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm4.glb` (0), `tools/install_model.py export/mm9_peasantm4.glb
--world mm9 --name mm9_peasantm4.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantm4_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantm4_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantm4.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); orient/handedness gates (geometry orientation unchanged, every
vertex an installed one); the see-through of a60 (stopped: superseded by c).

