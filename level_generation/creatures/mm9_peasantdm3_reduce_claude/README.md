# MM9 PeasantDM3 (`mm9_peasantdm3`, dwarf with long hair, rows 11/12) reduction: candidate d r55 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk, face exact), ledger
row 54 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantdm3` (owner peasantdm3-reduce-20261105); the creature's
`mm9:peasantdm3` lease was free. Source: installed `assets_source/worlds/mm9/models/mm9_peasantdm3.glb` (sha256 561040214e77, identical to
`../mm9_peasantdm3_claude/export/mm9_pdm3.glb`), copied to `before/` (rollback). No Meshy, no credits, no repaint. **Not installed.**
`../mm9_peasantdm3_claude/` was only read.

Family: DM3 is a reshaped variant of DM1's body (`mm9_peasantdm1_claude`, ledger row 86, queued); DM2 and DM4 have their own bodies, so
nothing is shared with the DM2/DM4 reductions running in parallel. DM3 uses DM2's lining tools (`neck_cap.py`, `rim_lining.py`), so
DM2's reduction scripts (`../mm9_peasantdm2_reduce_claude/`, read only) were copied here: second-pass lining twins, the lining-texel
guard in `mpqem.py`, the head-shell split in `make_sets`. Start: the Dwarf boy's finished chain (`../mm9_peasantdboy_reduce_claude/`).

| | LOD0 | body prim (tunic, legs, buckle, linings) | head prim (head shell, hair + twin, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 10,656 | 6,367 | 4,289 | 5,291 | 1,904 | 633 |
| **d r55 (`export/mm9_peasantdm3.glb`, sha256 f7dc5ca6210b)** | **9,032 (-15.2 %)** | 5,818 | 3,214 | 4,508 | 1,622 | 553 |

Per group (free faces cut): hands 1,314 -> 816 (0.6, every finger), hair shell 1,021 -> 663 (0.65) and its 2 mm twin 483 -> 329
(re-emitted), hair-painted head-shell faces (sideburns) 230 -> 172 and beard 47 -> 41 (0.75), tunic 972 -> 842 and legs 1,140 -> 894
(the distance guard stops both early), body linings 1,671 -> 1,497. Every vertex is an installed vertex; clips, skin, nodes, materials,
variants and all 8 images identical (`same_clips.py`).

## Protected share (measured first)
Head prim: head shell 1,342 (face, beard, neck, flattened ears), hair shell 1,060 + its twin 483, two MPFB hands 1,399. Body: 2,425 of
6,367 faces are one-texel linings (collar, belt, boots, sleeves to the shoulder; `rim_lining.py` clamps offsets, so 735 lining faces
have no face twin). Keep set d (`scripts/make_sets_dm3.py d`): head shell face window + every shell face the head region mask does not
paint as hair (face skin) + ear box + neck/beard faces within 2 cm of the body; collar, graft junction (1.5 cm), cuff (2 cm), soles,
rim strips, unpaired linings and outer faces within 6 mm of them, inner-layer UV twins, buckle; hand-contact faces (`hand_contact_dm3.py`,
4 cm in any clip); two hole zones (below). Protected: 4,792 faces (45.0 %).

## Route
`scripts/mpqem.py` (pose-aware half-edge collapse, DM2/Dwarf boy copy): chart guard `MP_CHART=1`, texture guard over both tiers and
the region masks (`tex_extract.py`: body and head both ramped), `MP_W5=4`, distance guard 3.5 mm, seam slides on the hands.
Changes here: `twins.py` also pairs painted twins by identical UV (the hair twin: 294 -> 483 of 483 pairs found); `mpqem.py` re-emits
painted twins straight from the corner map (one-texel linings keep DM2's shared-texel rule) and fills lining holes with dropped
installed faces (`fill_holes`); set d drops the second-pass lining roles in two 3 cm zones (right elbow lining, hair twin border at
the left temple) where the re-emitted lining left a one-triangle hole (open edges 570 -> 572 in a/b/c).

| run | change | LOD0 (Blender) | p99 / max mm | IoU / SSIM | open edges (src 570) | result |
|---|---|---:|---|---|---:|---|
| a | set a, tunic r55/r45 | 8,976 | 2.42 / 9.82 | .9975 / .9962 | 572 | fail (lining holes) |
| b | + hand contact, hole faces kept | 8,984 | 2.44 / 9.82 | .9974 / .9962 | 574 | fail |
| c | b + `fill_holes` | 8,986 | 2.44 / 9.82 | .9974 / .9962 | 571 | fail |
| **d** | **set d (hole zones exact)** | **9,023 (GLB 9,032)** | **2.38 / 9.82** | **.9975 / .9963** | **567** | **PASS, picked** |

Limits for 1.211 m: p99 3.63, max 18.2 mm. r45 = r55: the guards, not the ratio, stop the tunic.

## Gates, installed -> d r55 (`review/gates_before/`, `review/gates_d55/`)
- **UV audit** (`review/uv_audit_d55.json`): **0 escaping LOD0 faces in both primitives**. LOD1-3 escapes from the LOD tool at the
  installed level (LOD1 146/148 vs 140/115, LOD2 155/128 vs 158/120, LOD3 32/77 vs 22/86).
- Arm and hand (`--outer-only`): identical maxima (Talk L 1.4 cm 3 f as installed, all else 0); finger stretch minima equal or higher.
- Jitter vs MM9's clips: 0 fails both. Sleeve poke: identical (R 60.3 mm on 2 vertices, the creature's known lining artifact).
- See-through (16 views, every clip): worst px equal in every zone (collar 44 -> 43, sleeve R 41 = 41, torso 93 = 93, boots 0, trousers
  1 = 1); sleeve L 0 -> 1 px in one AttackMelee frame; frames with holes 94 -> 96 (sleeve R), 132 -> 129 (torso).
- Beard (`hair_beard_gate.py`, SEL=beard: stretch, elongation, gap/approach to the posed body surface): **identical in every clip**.
- Hair (SEL=hair, shell + twin below 1.0 m): stretch over edges >= 5 mm identical in every clip; surface contact gap/approach equal
  within 0.13 cm (Running gap 0.42 -> 0.55, Standing 1.10 -> 0.87); the all-edge ratio, which sits on 1.6 mm edges at the hair's weight
  blend near the left cheek in both models, 2.54 -> 2.73 (Death), 1.51 -> 1.65 (Hit), 1.42 -> 1.50 (Running), better in Walking/Dead;
  largest elongation 8.2 -> 11.4 mm (longer edges after the cut). The older vertex-distance version (`beard_gate.py`) is also kept
  (`beard.txt`, `hair.txt`); its contact numbers move only because the reduced body has fewer vertices.
- Linings (`lining_gate.py`): vertices > 0.5 mm outside equal (body) or fewer (hair 77 -> 56); largest body excursion better in
  Running/AttackMelee/Hit/Death, worse in Fidget 3.96 -> 6.29 mm and Standing/Fidget2 by 0.3-0.4 mm (inward-facing lining faces).
- Detached 0 = 0, winding 0, bones 12 checked 0 stretching, flat 0.00, texture quality body 53.1 % both, head 41.5 -> 41.4 %.
- LODs (`scripts/lod_check.py`): height 1.211 m at every LOD; LOD1 floor equal to LOD0 in every clip; LOD3 within 0.5 cm except Running
  +4.1 cm (installed LOD3 floated 16-21 cm in every living clip: it had lost the feet); LOD0 stretched faces 0-1 per clip (installed 0-2).

## Review
Viewer (installed and reduced, both tiers, 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm3_reduce_claude/review/viewer/
Sheets read (installed left/above): `review/sheet_face_d55.png`, `review/sheet_face_diff_d55.png` (face skin and beard black in all ten;
differences on the hair shading and the collar beads), `review/sheet_body_d55_b.png`, `review/close_d55_b_hands.png` (wrists, cuffs,
beard on the collar), `review/close_d55_b_fingers.png`, `review/close_d55_a_hair.png` (hair from behind, above and level),
`review/close_d55_a_hem.png`, `review/close_d55_b_motion.png` (Fidget, AttackMelee, Talk, Death), `review/ladder_sheet_a.png`.
Generated, not opened: `review/sheet_body_d55_a.png`, `review/close_d55_{a_hands,a_motion,b_hair,b_hem}.png`.
Look at: knuckles at the closest zoom (hands 0.6: slightly more angular, a darker crease between two fingers in c17), the hair outline
from above.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantdm3_reduce_claude/before/mm9_peasantdm3.glb REA_NODE=PeasantDM3 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_parts.py; $G scripts/hand_contact_dm3.py
HOLES="-0.505,0.735,-0.02,0.03;0.085,1.02,-0.04,0.03" HANDS=hand_contact.npy CUFF=0.02 TW2=1 $G scripts/make_sets_dm3.py d
work/run_d.sh            # MP_DMAX_MM=3.5 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=d MP_GROUPS=1:0.6,2:0.65,3:0.55,6:0.75,7:0.75; run_mp.sh d 0.55
scripts/build_mp.sh mp_d_r55 export/mm9_peasantdm3.glb
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantdm3.glb before/mm9_peasantdm3.glb --json review/uv_audit_d55.json
scripts/gates.sh export/mm9_peasantdm3.glb d55; SEL=hair $G scripts/hair_beard_gate.py export/mm9_peasantdm3.glb review/gates_d55/hair2.json export/mm9_peasantdm3.glb
work/blender_queue.sh    # see-through before/d55, lod_check installed/d55
$G scripts/viewer_tiers.py export/mm9_peasantdm3.glb red; scripts/shots.sh; scripts/close_shots_dm3.sh; $G scripts/shot_sheets.py d55
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantdm3.glb` (0), `tools/install_model.py export/mm9_peasantdm3.glb
--world mm9 --name mm9_peasantdm3.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantdm3_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantdm3_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantdm3.glb`.

## Not checked
In game (not installed; binding regression and floor audit after install); motion at speed by eye (frames, gates, stills only); LOD1-3
and shadow meshes by eye (numbers only); fingertips only at two rest-pose close-ups (tier B).
