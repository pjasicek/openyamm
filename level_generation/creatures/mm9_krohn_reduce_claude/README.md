# MM9 Krohn (`mm9_krohn`, row 255, the god-king of the Hall of the Gods) reduction: candidate d r70 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact; prio-3
unique reduced on the user's 2026-11-05 "do all"), ledger row 42 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:krohn` (owner krohn-reduce-20261105); the creature's own `mm9:krohn` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_krohn.glb` (sha256 7cbdb15c12b6, = `../mm9_krohn_claude/export/mm9_kr.glb`), copied to `before/`
(the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_krohn_claude/` was only read.

| | LOD0 | body prim (skin, mail, scale skirt, fur, cape, belt, plates, rim linings) | head prim (face, hair, beard, crown, MPFB hands) | props (glaive, sword) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,320 | 6,645 | 4,399 | 1,276 | 6,158 | 2,216 | 720 |
| **d r70 (`export/mm9_krohn.glb`, sha256 d1c4e3aa0dcc)** | **10,532 (-14.5 %)** | 5,343 | 3,969 | 1,220 | 5,264 | 1,893 | 625 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (15), skin, nodes, materials (extras), all 9 images: identical (`same_clips.py`). No tiers, no emissive parts.
**-14.5 % is just under the brief's ~15 %**: what the protected set leaves is about 5,100 of 12,320 faces, and the body cannot go below
~r70 inside the stop rule (ladder a r60 failed). The orchestrator may prefer "kept (no useful gain)"; the candidate saves 1,788 faces.

## Kept exactly (`scripts/make_sets_kr.py d`, `KEEPCLS=9,22`; 6,387 faces = 52 %, `scripts/kept_check.py`: 0 missing)
Labels: the master's face attributes (`lined`, `hand`, graft) from `../mm9_krohn_claude/work/grip_props_cape.blend` matched to the GLB by
centroid (`scripts/dump_master.py`, `scripts/glb_labels.py`; mirrored x, floor lift 1.39 m, max 0 mm head / 2.4 cm on 3 body faces);
head UV chart 32 = the face (one island by `relayout_head_k.py`). Class renders: `review/classes_a/` (read at full size).
- Head: face chart + both ears (box round each ear, all faces: the ears show through the hair) 819, hairline (one ring of hair round the
  face skin/ears) 300, eyes 108, head neck seam 285, crown band + spikes 558 (painted knotwork and diamonds).
- Hands: every finger face 990, wrist graft (Forearm weight / graft blend) 225, the bracer faces within 4 cm of each hand's open end 11.
- Body: rim strips of the rim linings 398, soles 90, body neck seam 156, small loose parts (shoulder medallion, baldric strap and buckle,
  knee discs) and the ram buckle 652, belt band with its disc medallions 437, greaves + bracers 222 (painted relief plates; cut at 0.8 in
  c r70 the lion motifs slid: `review/crop_greaves_c70.png`).
- Props: glaive head (guard disc, socket) 296, sword (scabbard spiral, wrapped grip) 480, whole shaft 360 (its raised gold collars
  flattened at 0.5 in c r70: `review/crop_shaft_c70.png`).
- Cut (pose-aware half-edge, `scripts/mpqem.py`): body rest + lined bands at r70 (3,851 -> 2,695), hair + beard 0.6 (929 -> 557), palm/back
  0.65 with seam slides (185 -> 127), glaive blade 0.6 (140 -> 84).
- Rim linings rebuilt: `scripts/lining_pairs.py` pairs every lining face with its band face (828/828, corner residual <= 4.0 mm, the
  rim_lining offsets) and gives each band vertex its lining twin; a surviving band face that is unchanged takes its installed lining face,
  a changed one the reversed twins of its corners (828 -> 682: 524 installed faces, 158 from twins). The rim strips stay exact.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, Yanmir's copy)
Scored over 517 poses (every clip at 10 Hz); chart guard `MP_CHART=1`, the audit's own chart test in every collapse `MP_AUDIT=1`
(Skeleton's), texture guard over each primitive's base colour, texture weight `MP_W5=4`, seam slides on the palms, no quality test on the
rigid prop groups. Krohn change: a collapse in a lined band is refused when the lining face it re-emits would leave the charts (twins of
Meshy's inner layer keep their own UVs, the others sit on one dark texel; b r70 had 11 such lining faces off the charts).

## Ladders (limits for 2.78 m: p99 <= 8.34 mm, max <= 41.7 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b,c,d}.png`)
| ladder | change | step | LOD0 | p99 / max mm | result |
|---|---|---|---:|---|---|
| a | body r60..r50, hands .65, hair .7, plates .75, props exact | r60 / r55 / r50 | 10,196 / 9,992 / 9,904 | 10.78/49.8; 14.1/60.3; 20.8/61.7 | fail (body rest error everywhere: the body was already cut 15.2k -> 9.4k at assembly) |
| b | body r80..r70, hair .6, plates .8, shaft .5, blade .6 | r80 / r75 / r70 | 10,734 / 10,516 / 10,308 | 5.73/26.6; 6.65/26.6; 7.67/26.6 | pass; b r70 built: 11 LOD0 lining faces off the charts |
| c | b + the lining chart test in the collapse | r72 / **r70** | 10,404 / 10,320 | 7.17/26.6; 7.63/26.6 | pass, UV audit 0; close-ups: greave motifs slid, shaft collars flattened |
| d | fix pass of c r70 (same step): greaves/bracers and shaft exact | **r70** | **10,532** | **7.32 / 26.1** (IoU .9952, SSIM .9960) | **PASS, picked** |

## Gates, installed -> d r70 (Krohn's own gates via `scripts/gates.sh` + `scripts/blender_queue.sh`; `review/gates_before/`, `review/gates_d70/`)
- **UV audit** (`review/uv_audit_d70.json`/`.txt`): **LOD0 0 escaping faces** in Krohn, KrohnHead, KrohnProps. LOD1-3 (builder decimate):
  body 219 / 172 / 75 (installed 180 / 183 / 94), head 151 / 157 / 120 (139 / 142 / 118), props 4 / 7 / 1 (2 / 6 / 1).
- Arm/hand (`--outer-only`, excl. weapon bones): 0 frames over 1 cm, both hands and forearms, every clip (= installed); R finger stretch
  p10 +0.01 in four clips, maxima equal.
- Glaive vs body: equal or better (Krohn03 1.4 -> 1.4, Krohn05 2.2 cm 3 f, Running 0.0 -> 0.1 cm); sword vs body better (Death 0.2 -> 0.1,
  Krohn05 0.3 -> 0.1); sleeve poke identical (Dead L 1.0 mm 3 v).
- Collapse face-frames lower in every clip (total 70,949 -> 62,879).
- **Jitter: 0 -> 1 fail, a sampling artifact**: AttackMelee L shoulder skin 0.54 -> 2.99 mm/f2 over MM9. The statistic is a 95th percentile
  over the vertices weighted to the clavicle/upper arm; the cut removed 57 of 262 of them. On the installed file restricted to the
  candidate's vertices it gives exactly the candidate's value, and the per-vertex maximum is equal (315.46 / 441.18 mm/f2):
  `review/gates_d70/skin_acc_check.txt` (`scripts/skin_acc_check.py`). Every kept vertex moves exactly as installed.
- See-through (7 clips, step 5, 4.5 mm px): same clips and frames with holes in every zone; worst-frame size torso 129 -> 151 px (the
  installed sliver along the cape's side, slightly longer: `review/st_torso_fid_pair.png`), sleeve R 62 -> 82 (the installed slit at the
  right shoulder, at another Death frame: `review/st_sleeveR_death_pair.png`), head 4 -> 6, collar 73 -> 42, trousers R 1 -> 0.
- Detached: part 17 (back flap) 18 -> 1 pose; R knee disc 1 -> 4 poses (5.2 cm, Krohn05); L knee disc now listed (1.4 cm, 3 Running
  poses) although its contact with the leg stays within 4.3 mm (installed 3.4; `scripts/disc_gap.py`); shaft 0.6 cm in 2 poses.
- Flat 0.00 / 0.00 / 0.07, winding 0, bones 0 of 12 stretching, texture quality unchanged (stretch p90 1.11 -> 1.12 body).
- LODs (`scripts/lod_check.py` every frame of every clip, `scripts/lod_summary.py inst d70`): height 2.779 m at every LOD; 0 stretched faces;
  LOD0 lowest point equal in every clip; LOD1/2 Walking and LOD2 Running and LOD3 Death closer to the floor than installed; **LOD3 Walking
  -1.45 cm (installed -0.96)**. Built by `scripts/build_lods.py` (0.5/0.18/0.06, 4 influences; soles, crown top and corpse contact
  protected, 45 of 45 points snapped), then Krohn's `shrink_shadow_lods.py`, `drop_lod_slivers.py` and Yanmir's `fix_winding.py`.

## Review
Viewer (installed and reduced, all 15 clips; `run_creature_review.py check`: 30 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_krohn_reduce_claude/review/viewer/
Sheets read at full size: `review/sheet_face_d70.png` with `review/pair_f1_c70.png`, `review/pair_f2_c70.png` (head identical in c and d),
`review/sheet_face_diff_d70.png` (face skin, eyes, ears, crown black; hair top, beard tips and mantle shading differ),
`review/sheet_body_d70_a.png` (Standing front/3-4/back, Walking, AttackMelee, Death), close pairs `review/shots_close/pair_c0..c17.png`
(R fist and shaft, L hand, chest medallion and baldric, ram buckle and blade, back/cape/scabbard, knees and greaves, both bracers and the
belt, crown from above, Running, Hit, back of the legs, ankle bands front/back, glaive head, shaft collars), `review/crop_greaves_c70.png`,
`review/crop_shaft_c70.png` (the rejected c r70 details), `review/ladder_sheet_d.png`, `review/classes_a/`.
Look at: the hair top and back (cut at 0.6: slightly more angular in profile), the fingertips are exact but the palms are cut, the beard
tips, the cape side edge (see-through sliver).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_krohn_reduce_claude/before/mm9_krohn.glb REA_NODE=Krohn $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $BL -P scripts/dump_master.py; $G scripts/glb_labels.py; $G scripts/lining_pairs.py
$G work/an_charts.py   # work/head_charts.npy (head UV charts)
KEEPCLS=9,22 $G scripts/make_sets_kr.py d
SETS=d MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 MP_NOQ_GROUPS=4,5 MP_GROUPS=1:0.65,2:0.6,3:0.8,4:0.5,5:0.6 scripts/run_mp.sh d 0.7
scripts/build_mp.sh mp_d_r70 export/mm9_krohn.glb
$G ../claude_shared/reduction_uv_audit.py export/mm9_krohn.glb before/mm9_krohn.glb --json review/uv_audit_d70.json
$G scripts/kept_check.py export/mm9_krohn.glb d; scripts/gates.sh export/mm9_krohn.glb d70; scripts/blender_queue.sh export/mm9_krohn.glb d70
python3 scripts/lod_summary.py inst d70
python3 scripts/make_viewer_manifest.py d70 inst_a=Installed=before/mm9_krohn.glb red_a=Reduced_d70=export/mm9_krohn.glb
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py d70; $G scripts/face_diff_sheet.py d70
```
`scripts/viewer_shots.mjs` is mm8_m424's with a 180 s ready wait (the shared machine was under load).

Install (orchestrator, on the OK): `check_winding.py export/mm9_krohn.glb` (0), `tools/install_model.py export/mm9_krohn.glb --world mm9
--name mm9_krohn.glb`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_krohn_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_krohn_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_krohn.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates and stills only);
the cutscene clips (Krohn01-05, SC7_22_Krohn, Statue) only through the gates and the ladder error; LOD1-3 and shadow meshes by eye
(numbers only); the see-through gate on the scripted clips; the eye/mouth close-ups at the user's zoom (the face triangles are the
installed ones and the diff is black there).
