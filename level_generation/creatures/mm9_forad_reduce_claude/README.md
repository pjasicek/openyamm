# MM9 Forad Darre (`mm9_forad`, row 69) reduction: candidate c60 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact; user
2026-11-05 "do all": prio-3 uniques reduced too), ledger row 69 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:forad`: first owner forad-reduce-20261105 (session died during the a60 see-through gate), released after checking no
process worked on it and claimed again by forad-reduce2-20261105, which continued from these files (ladders a and b were not redone).
The creature's own `mm9:forad` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_forad.glb` (sha256
6a9d241b01dc), copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_forad_claude/`
was only read (its `arm_hand_gate.py`, `jitter_gate.py`, `shrink_shadow_lods.py`, `v2/work/mm9_forad_clips.glb`, `extra_raw.glb` run
in place; its `sleeve_gate.py` and the PeasantDM2 `see_through_gate.py` copied here so they run under this lease).

**Family note:** the scripts come from the PeasantM8d reduction (`../mm9_peasantm8d_reduce_claude/`, installed), whose body Forad
shares in topology (ledger row 85). Forad adds the necklace (33 beads in the body primitive, 6 in the head primitive, kept exact).

**Orchestrator decision (2026-11-05):** b60 (-15.3 %) failed the pre-screen for visibly pointed fingertips (R index in
`close_b60_fingers` f1, thumb in f8, index in `close_b60_thumb_2` h4; installed tips are rounded, Hanndl's d7 defect). c60 (fingertips
exact, -13.6 %) is accepted for this unique NPC (Hanndl went in at -14.8 %).

| | LOD0 | body prim (vest, breeches/boots, linings, beads) | head prim (face shell, scalp hair, ponytail, ties, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,654 | 4,357 | 4,297 | 4,319 | 1,516 | 476 |
| a60 (`export/mm9_forad_a60.glb`) | 7,312 (-15.5 %) | 3,857 | 3,455 | 3,648 | 1,275 | 394 |
| b60 (`export/mm9_forad_b60.glb`, rejected: pointed fingertips) | 7,326 (-15.3 %) | 3,871 | 3,455 | 3,654 | 1,277 | 395 |
| **c60 (`export/mm9_forad.glb` = `export/mm9_forad_c60.glb`, sha256 c18218e3f12b)** | **7,474 (-13.6 %)** | 3,871 | 3,603 | 3,728 | 1,303 | 405 |

Per group in c60 (free faces cut): hands 1,398 -> 1,094 (286 fingertip faces with all three corners on a distal finger/thumb joint and
197 graft/contact faces exact; the other 915 -> 611 at ratio 0.5, guard-limited), ponytail 530 -> 318 (0.6), scalp hair under the
hairline 445 -> 267 (0.6), breeches/boots 1,185 -> 817 (guard-limited), vest free 601 -> 483 (guard-limited), linings 187 re-emitted
from the cut outer faces (138 installed, 49 re-emitted). Every vertex of the candidate is an installed vertex (positions, normals, UVs,
joints, weights are the installed bytes; only index buffers changed). `scripts/exact_head.py` (`review/exact_c60.txt`): 1,648 exact
head-shell faces and every kept face present (all 286 fingertip faces checked separately). Clips (16), skin, nodes, materials, all 6
images identical (`review/gates_c60/same_clips.txt`).

## Measured first: protected share
`scripts/make_sets_forad.py` (PeasantM8d's set logic + beads). Exact: the face shell's skin (face, ears, neck), brows, goatee,
moustache, forelock and sideburns, one ring of hair round the skin (hairline), the collar band in the head material (neck seam),
the ponytail ties, all 39 beads, cuffs/bracers and the hand-graft junction, collar, soles, rim strips and loose linings with a 6 mm
halo, hand-contact faces, shoulder cloth (SHOULDER=1), the vest front panel (PANEL=1) and its fold faces; set e2 adds the fingertips
(TIPS=2). Protected share: set a 41.9 %, cs 53.5 %, d 54.2 %, **e2 57.5 %**.

## Route
PeasantM8d's pose-aware half-edge collapse (`scripts/mpqem.py`, 429 poses over all 16 clips), texture guard, Mummy chart guard
`MP_CHART=1` plus the audit's own chart test per collapse (`MP_AUDIT=1`), texture weight 4, seam slides on the hands, distance
guard 4 mm (breeches/boots 5 mm), linings re-emitted from their twins. `scripts/build_mp.sh`: swap_mp -> snap-fixed `build_lods.py`
(34 of 34 protected points mapped) -> the creature's `shrink_shadow_lods.py` -> carry_variants (one tier) -> fix_winding ->
restore_materials -> check_winding.

## Ladders (limits for 1.758 m: p99 <= 5.27 mm, max <= 26.37 mm, IoU >= .98, SSIM >= .93)
| ladder | change | LOD0 | result |
|---|---|---:|---|
| a | set cs, groups hands 0.6, ponytail 0.65, legs 0.6, scalp 0.6; steps 0.6 / 0.5 (equal: the vest and breeches are guard-limited) | 7,312 (-15.5 %) | p99 3.13 / max 10.49 mm (Running:12), IoU .9962, SSIM .9939. Arm/hand: ArgumentSpeak20 R hand 0.9 -> 1.5 cm (1 frame > 1 cm), Agree R 0 -> 0.9 cm |
| b | set d = cs + every face a hand comes within 2 cm of (posed centroid within R + circumradius, `scripts/hand_contact_forad.py`, 48 fps; 61 more faces) | 7,326 (-15.3 %) | p99 3.13 / max 10.49 mm, IoU .9964, SSIM .994. Arm/hand readings as a60: `scripts/probe_hand_depth.py` shows both are the R hand behind one cut face of the **L thumb tip**. Rejected in the pre-screen: pointed fingertips |
| **c** | set e2 = d + every hand face with all three corners on a distal finger/thumb joint exact (Hanndl's TIPS=2); hands' free part 0.5, ponytail 0.6 (`work/run_c.sh`) | **7,474 (-13.6 %)** | p99 3.02 / max 10.49 mm, IoU .9967, SSIM .9941; the hand guards stop at 611 of 915 free faces (target 458). **Picked** (orchestrator) |
Three ladders, the brief's limit; no fourth.

## Gates, installed -> c60 (`scripts/gates.sh`, `scripts/see_through.sh`, `work/eval_c.sh`; `review/gates_before/`, `review/gates_c60/`)
- **UV audit** (`review/uv_audit_c60.json`, `.txt`): **0 escaping LOD0 faces in both primitives.** LOD1-3 (Blender decimate) body
  130 / 133 / 46, head 139 / 144 / 82 vs installed 111 / 149 / 52, 104 / 145 / 96.
- Arm and hand (`--outer-only --exact`, 48 fps, all 16 clips, `review/gates_c60/arm_hand.txt`): **equal or better in every clip**
  (ArgumentSpeak20 L 0.7 -> 0.6 cm, R 0.9 -> 0.8 cm; Agree R 0 both; Talk L 3.5 cm both, 40 -> 39 frames; Bow L 1.0 -> 0.9 cm, 1 -> 0
  frames; Applause L 76 -> 72 frames); the b60 thumb-tip reading is gone. Finger stretch maxima equal or lower, minima within +0.05.
- Jitter (vs `../mm9_forad_claude/v2/work/mm9_forad_clips.glb` and `extra_raw.glb`): output identical to installed.
- Sleeve poke: identical (rest 0 mm both sides). Linings (`scripts/lining_gate.py`): every clip identical to installed.
- Detached parts: 0 detached both; the two shallow hand notes unchanged. Flat shading 0.00 both. Winding 0. Bone lengths 12, 0
  stretching. Texture quality: body atlas 53.5 % both, stretch p90 1.09 -> 1.10; head atlas 43.9 % both, islands 190 -> 183,
  fragments 2.8 -> 3.2 %, stretch p90 1.24 -> 1.23.
- See-through (`scripts/see_compare.py c60`, every clip, 16 views): worst per zone unchanged (sleeve R 11 px Running, sleeve L 2 px
  Talk, every other zone 0); within that, ArgumentSpeak6 sleeve R 6 -> 10 px, ArgumentSpeak20 sleeve R 9 -> 8, Applause sleeve L 1 -> 2.
- Forad's sleeve (bracer) gate (48 fps, every clip): worst px equal or lower in every view and side (R above34 42 Death, R q34 22, R
  front 11, L 5 / 5 / 2), frames over 0 fewer in every view (R above34 69 -> 56, R q34 67 -> 62, L q34 21 -> 5); poke 0 both.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,c60}.json`): height 1.7872 m at every LOD; the
  lowest point of LOD1-3 equals LOD0 in every clip (installed LOD2 up to 1.05 cm, LOD3 1.33 cm off); 0 stretched faces at any LOD.

## Review
Viewer (installed and reduced c60, every clip; one tier):
http://127.0.0.1:8912/level_generation/creatures/mm9_forad_reduce_claude/review/viewer/ (`run_creature_review.py check`: 32
switches, 0 failed, no console errors, `review/viewer_check.txt`). The shared review server on 8912 was down; the shots and the check
ran on a private `python3 -m http.server 8923` (stopped afterwards); the shot scripts take `VPORT`. Installed shots (`inst_a`) are
the a60-session captures with the same cameras; b60's reduced shots are kept in `review/shots*/red_a_b60/`.
Sheets read at full size (installed left/above, c60 right/below; crops in `review/crops_c60/`): `review/sheet_face_c60.png`,
`review/sheet_face_diff_c60.png` (front close-up, 3/4, profile, low 3/4, party: face skin, goatee, scar, eyes, ears and neck black in
all five; only the scalp-hair shading and outline differ), `review/sheet_body_c60_a.png`, `review/close_c60_{1..4}.png`,
`review/close_c60_f1.png`, `review/close_c60_f2.png`, `review/close_c60_fingers.png`, `review/close_c60_thumb_{1,2}.png`, and
`review/tips_zoom_c60.png` (installed | b60 | c60 at 2x on the flagged tips: f1 index and little finger, f8 thumb, h3/h4 Agree):
c60's tips match installed; b60's were the pointed ones.
Look at: the fingers' middle joints at very close range (a few facets where the cut middle phalanx meets the exact tip, as Hanndl
d7); the R boot shaft above the cuff (`close_c60_4.png` c14, a slightly different highlight); the hair from behind (0.6, outline the
same).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_forad_reduce_claude/before/mm9_forad.glb REA_NODE=Forad $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_classes_forad.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
R=0.02 OUT=hand_contact_surf_0.02.npy FPS=48 $G scripts/hand_contact_forad.py   # then work/hand_contact_u02.npy = 0.04 | surf_0.02
TIPS=2 SHOULDER=1 PANEL=1 DEV=75 DEV_RING=0 FRONT_Z=0.05 BACK_Z=-0.02 BACK_Y=1.66 HANDS=hand_contact_u02.npy $G scripts/make_sets_forad.py e2
REA_HEIGHT_M=1.758 MP_DMAX_MM=4 MP_DMAX_GROUPS=3:5 MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=e2 \
  MP_GROUPS=1:0.5,2:0.6,3:0.6,6:0.6 scripts/run_mp.sh c 0.6     # work/run_c.sh  (b: SETS=d, 1:0.6,2:0.65; a: SETS=cs)
work/eval_c.sh   # build_mp.sh mp_c_r60 export/mm9_forad_c60.glb, UV audit, exact_head, gates.sh, see_through.sh, lod_check
python3 scripts/make_viewer_manifest.py c60 "inst_a=installed 8,654=before/mm9_forad.glb" "red_a=reduced c r60 7,474=export/mm9_forad_c60.glb"
HEADUP=0,0.08,0.05 scripts/shots.sh red_a; scripts/close_shots.sh red_a; scripts/close_shots_forad.sh red_a   # + the h0-h4 thumb cameras
$G scripts/shot_sheets.py c60; $G scripts/face_diff_sheet.py c60; $G scripts/close_sheet.py c60 a c0,c1,c2,c3 review/close_c60_1.png  # ...
cp export/mm9_forad_c60.glb export/mm9_forad.glb
```
Install (orchestrator, on the OK): `level_generation/creatures/claude_shared/install_reduced.sh forad mm9_forad export/mm9_forad.glb
level_generation/creatures/mm9_forad_claude` (checks `before/`, UV audit, winding, `tools/install_model.py`, ledger, creature README
note), then the `mm9_actor_models_build_every_binding` regression. Rollback: `before/mm9_forad.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and viewer
stills only); LOD1-3 and shadow meshes by eye (numbers only); close-ups of the scene clips other than Applause, Sit, ArgumentSpeak6/20,
Agree and Bow (the gates cover all 16 clips); the a60 see-through and LOD checks (a60 superseded).
