# MM9 Colloidal Warrior (`mm9_colloidalwarrior`) reduction: candidate g2 r80 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster,
relaxed keep set), ledger row 38. Lease `mm9reduce:colloidalwarrior` (owner colloidalwarrior-reduce-20261104). No-retexture
branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) on the installed r9
(`assets_source/worlds/mm9/models/mm9_colloidalwarrior.glb`, sha256 2b8f5899ef80, = `../mm9_colloidalwarrior_claude/export/`),
copied to `before/` (the rollback source). The creature project `../mm9_colloidalwarrior_claude/` was only read. **Not
installed.** No Meshy, no credits.

| | LOD0 | body set | head set | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed r9 | 12,520 | 7,994 | 4,526 | 6,258 | 2,251 | 749 |
| **g2 r80 (`export/mm9_colloidalwarrior.glb`, sha256 579eb37c04f1)** | **10,014 (-20.0 %)** | 5,930 | 4,084 | 5,007 | 1,802 | 600 |

Clips, images, materials, `KHR_materials_variants`, nodes, skins and inverse bind matrices are byte-identical to the
installed file (`scripts/same_parts.py`). Every installed face/seam triangle of the head set (3,467) is present unchanged with
the same positions, UVs, normals and weights.

## Keep set (protected share measured first: 32.5 % with the relaxed set, 42 % in the final one)
The body is one closed skin (no armour, no held prop, no cloth). The creature's own build had already cut it once
(`reduce_cw.py`). Face per `scripts/head_classes.py` (`review/head_classes/sheet.png`).
- **exact:** the head set's face (everything in front of y = -0.24 in rest mesh space: crest ridges, brows, eyes, nose, grin,
  teeth, chin and throat rolls, plus one face ring) and the neck seam (head faces touching the body plus 2 rings); the
  hand-graft junction (faces with a Forearm weight, or not wholly on the hand); soles (4 cm); shoulder skin (any vertex
  dominated by a Clavicle or UpperArm: the jitter gate's shoulder term, AttackMelee R 6.5 mm/f2 over the installed model when
  cut); forearms (AttackMelee2 R forearm depth 0.4 -> 1.0 cm when cut); belly faces within 3 cm of a forearm/hand in any frame
  (`arm_contact.py`); two error-lock rounds (`err_lock.py`, 20 mm, 3 cm patches: the belly-front Spine vertex, the Head_h chest
  band, the flank and thigh-back points).
- **own ratio:** hood dome 0.6 (top and back of the head set behind the face; the brief's "hood shell"), hands 0.6 (palm,
  back, every finger; distal phalanges in the cut too: fingers still read in the close-ups).
- **shared cut:** trunk, thighs, calves, flipper feet, upper-arm undersides (texture-aware MeshLab collapse, interpolated
  piece-aware weights, source vertices keep exact weights).

## Ladder (height 2.013 m: p99 <= 6.04 mm, max <= 30.2 mm)
| run | keep | step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | face, seam, graft, soles; hood, hands 0.7 | r85 | 10,640 | 3.81 / 36.1 (Death2) | .998 / .994 | fail: belly-front Spine vertex |
| b | a + error lock 1 | r80 | 10,014 | 5.07 / 25.7 | .996 / .991 | pass |
| c | b, hood and hands 0.6 | r78 | 9,764 | 5.23 / 25.7 | .996 / .991 | pass |
| d | c + error lock 2 | r78 | 9,764 | 5.22 / 20.4 | .996 / .991 | pass; jitter vs installed: AttackMelee R shoulder skin 6.5, Running R 3.5, Hit2 R 3.1 mm/f2 |
| e | d + shoulder skin | r79 | 9,888 | 5.41 / 19.6 | .996 / .991 | pass; arm/hand AttackMelee2 R forearm 0.4 -> 1.0 cm |
| f | e + arm contact | r80 | 10,014 | 5.16 / 19.6 | .996 / .992 | pass; forearm still 1.0 cm |
| **g2** | **f + forearms** | **r80** | **10,014** | **5.17 / 19.6** | **.997 / .992** | **pass, picked**; r79 fails (51.6 mm, Hit) |

The stop is the posed error (rest error at r75 was only 9.5 mm): steep helper weights (head band, armpit flank) leave single
source vertices that the collapse cannot follow. A third lock round moved the error elsewhere (playbook). Not tried:
`mm9_banshee_reduce_claude/scripts/mpqem.py` (pose-aware collapse); it could reach below r79 on this skin and is the next
step if the reviewer wants more.

## Export chain (`scripts/build_pick.sh g2 r80 final`)
`export_cand.py` (smooth, no floor lift: soles kept) -> `swap_lod0.py` -> `copy_kept_normals.py` (installed normals on every
source vertex, Blender smooth normals on new ones as `export_cw.py` made them) -> `tools/build_actor_lods.py` (default ratios,
4 influences, as `rebuild.sh`) -> the creature's `shrink_shadow_lods.py` -> `carry_variants.py` -> the creature's
`fix_winding.py` (0 flipped) -> `compact.py`. Clips stay the installed floor-fixed ones.

## Gates (`scripts/gates.sh`, the creature's own gate scripts; `review/gates_before/` vs `review/gates_g2r80/`)
| gate | installed | g2 r80 |
|---|---|---|
| jitter vs MM9 reference clips | 18 fails (runtime file) | the same 18, values within +-0.3 mm/f2 |
| jitter vs installed | - | 0 fails |
| arm/hand (`--outer-only --exact`) | Death2 R 6.0 cm (7 f), AttackMelee2 R forearm 0.4 | same; AttackMelee2 L hand 0.0 -> 0.1, Death2 L 0.8 -> 0.7 cm |
| finger stretch max | AttackRanged R 3.59 | 2.23 (lower everywhere) |
| collapse face-frames (sum over clips) | 58,272 | 37,562; worst-frame counts lower in every clip except ankle_L 3 -> 4 (Fidget2, Taunt), AttackRanged knee_L 0 -> 1, ankle_R 2 -> 3 |
| detached / bone length / handedness / winding | 0 / 0 stretching / right / 0 | same |
| flat shading body / head | 0.00 / 0.00 | 0.00 / 0.00 |
| texture quality body atlas, stretch p90 | 51.4 %, 1.15 | 51.1 %, 1.18 (head unchanged) |
| LOD heights 0-3 (m) | 2.0133 / 2.0131 / 2.0139 / 1.9991 | 2.0135 / 2.0138 / 2.0182 / 1.9989 |
| faces stretched over 20x (all LODs, all clips) | 35 / 1 / 1 / 0 | 1 / 0 / 0 / 0 |
| lowest point over clips; Dead | -3.6 cm (Running); Dead 0.0, LOD3 -1.05 | -3.6 cm; Dead +0.05, LOD3 +0.3 cm |
| viewer check | | 96 switches, 0 failed, 0 console errors |

## Sheets (read)
- Viewer, every tier, installed | reduced | diff x4: `review/sheet_faces_viewer.png` (front close-up, 3/4, profile, low 3/4,
  party: face pixels identical, differences only on the hood dome and body), `review/sheet_body_viewer.png` (Standing
  front/3-4/back, Walking 3/4, AttackMelee 3/4, AttackRanged front). Shots in `review/shots/<tier>_{inst,red}/`.
- Blender GLB close-ups, tier B, textured and clay: `review/close/sheet_head_g80.png`, `sheet_body_g80.png`,
  `sheet_motion_g80.png` (armpit in the attack, cast, run hips, Hit2 shoulder, hands, fist, Death, Death2),
  `sheet_face_diff_g80.png`; earlier candidates `sheet_*_e79.png`, `sheet_{head,body,hands,motion}.png` (c78).
- Ladder: `review/ladder_sheet_g2.png` (and per run).
Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_colloidalwarrior_reduce_claude/review/viewer/
(models a/b/c_inst and a/b/c_red, revision reduce-g2r80-20261104).

## Install (on the user's OK)
`check_winding.py export/mm9_colloidalwarrior.glb` (0), `python3 tools/install_model.py
level_generation/creatures/mm9_colloidalwarrior_reduce_claude/export/mm9_colloidalwarrior.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9`, the ledger row, and the line in
`../mm9_colloidalwarrior_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_colloidalwarrior_reduce_claude`; a
rebuild from this project must re-run that reduction". Rollback: `before/mm9_colloidalwarrior.glb`.

## Reproduce (project folder)
`REA_GLB=level_generation/creatures/mm9_colloidalwarrior_reduce_claude/before/mm9_colloidalwarrior.glb REA_NODE=Colloidal`:
`find_doubles.py` (0), `import_source.py` (weld identical weights only: 0 coincident pairs), `dump_mesh.py`, `dump_faces.py`,
`dump_weights.py`, `head_mask.py`, `head_classes.py`, `HOOD_RATIO=0.6 HAND_RATIO=0.6 make_groups.py`; keep sets
`err_lock.py` (ladder_a Cand_80 -> `keep_err80.npy`; ladder_c Cand_76 -> `keep_err_c76.npy`), `shoulder_keep.py`
(-> `keep_e.npy` with the locks), `arm_contact.py` (-> `keep_f.npy`), `forearm_keep.py` (-> `keep_g.npy`);
`REA_HEIGHT_M=2.013 REA_KEEP_FACES=work/keep_g.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=5:0.6,6:0.6 run_ladder.sh g2
0.80,0.79,0.78`, `build_pick.sh g2 r80 final`, `gates.sh`, `lod_check.py`, `same_parts.py`, `viewer_tiers.py`,
`make_viewer_manifest.py`, `shots.sh`, `viewer_sheets.py`, `close_glb.py` + `close_sheet.py`.

## Not checked
In game; motion at normal speed (frames and gates only); LOD1-3 by eye (numbers only; LOD2/3 come from the default
`build_actor_lods.py` as the installed ones did, and the creature README already notes LOD3 shards at the throat rolls);
shadow meshes by eye; the binding regression and `floor_audit.py` (they read the installed file: after install).
