# MM9 Monk (`mm9_monk`) reduction: fix pass f36 ready for review (chart guard, UV audit 0; 2026-11-04)

## Fix pass (2026-11-04, after the rollback): `export/mm9_monk.glb` = mpqem f r36, sha256 fb0391629483
The first candidate (e75, below) was installed and rolled back: 10 LOD0 faces left the painted UV charts
(`review/uv_audit_e75_old.json`; belt edge, shoulder, back yoke, two hand faces). Lease `mm9reduce:monk` reclaimed
(owner monk-reduce-fix-20261104); `assets_source/worlds/mm9/models/mm9_monk.glb` = `before/mm9_monk.glb` (cmp).
Route: the pose-aware half-edge collapse with the chart guard (`scripts/mpqem.py`, Dwarf copy: MP_CHART=1, per-tier texture
guard on the three Monk_A tier base colours from `tex_extract.py`, guard 100/45; `run_mp.sh`). Every vertex is an installed
vertex (positions, normals, UVs, joints, weights are the installed bytes; only index buffers change); `MonkHead` kept whole.
Sets (`glb_sets.py` from the first pass's keep set e0.02, plus the whole belt): face/head set, linings + one ring, cords, shoes,
shins, hand-contact robe, belt exact; knots and hands 70 %; the robe shell (5,473 faces) takes the ladder ratio.

| ladder (limits p99 5.61 / max 28.05 mm) | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---:|---|---|---|
| m1 (belt 70 %) | r55 / r48 / r42 / r36 | 11,113 / 10,729 / 10,401 / 10,073 | 2.41/10.0, 2.90/13.4, 3.48/13.6, 4.99/24.0 (Pray:0) | .998-.993 / .997-.995 | all pass |
| **f (belt exact)** | **r36** / r33 | **10,145** / 9,981 | **4.94 / 24.0 (Pray:0)**, 6.27 / 30.1 | **.993 / .995** | **pass, picked** / fail |

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,285 | 7,127 | 2,564 | 854 |
| **f r36** | **10,145 (-29.0 %)** | 5,059 | 1,819 | 602 |

- **UV audit** (`claude_shared/reduction_uv_audit.py`, `review/uv_audit.json`): **LOD0 0 escaping faces** (Monk_A 0, MonkHead 0).
  LOD1-3 Monk_A 154 / 170 / 103 against the installed LODs' own 101 / 167 / 155 (Blender decimate); MonkHead LODs as installed.
- **LODs** (`build_lods.py`, Lesser Demon snap fix: soles, hood tip, corpse contact protected, 71/71 points mapped): rest height
  and the lowest point in Standing, Death and Dead identical at every LOD (installed LOD3: rest bottom 2.4 mm higher, Standing
  +2.4 mm, Death -2.7 mm, Dead -3.8 mm against its LOD0); faces
  stretched over 20x 10 / 9 / 2 / 1 (installed 12 / 9 / 2 / 1).
- **Gates** (`review/gates_f36/`, `review/gates_compare_f36.txt`): collapse face-frames 67,935 -> 37,880, no clip and no region
  higher at its worst frame; arm/hand hand and forearm depth unchanged everywhere (Fidget R one frame fewer over 1 cm); finger
  stretch max unchanged, p99 worst 2.00 -> 2.28 (70 % hands); robe: legs 0 in all clips, cords under the robe Pray 4.3 -> 3.6 cm,
  Cower/CowerEnd 2.6 -> 2.5, **Dead 1.3 -> 1.7 cm** (25 frames both); detached parts the same 2 soles; bone length the same 2 Calf
  entries; winding 0; flat 0.00 / 0.04; texture stretch p90 1.25 -> 1.28; clips, skin, nodes, materials, variants, images identical.
- **Sheets read:** `review/closeups_oldspots_f36/closeups.png` (the six spots where e75 escaped, source vs reduced per tier;
  outlines are e75's: the f36 belt matches the source, a 1-2 mm notch in the robe edge under the belt front, a slightly darker
  shading patch below the back yoke), `review/sheet_close_f36.png` (shoulders, arms, skirt, back, tiers A and C),
  `review/sheet_face.png` + `review/crop_chin_f36_mk_a.png` (face box identical, max 34 grey levels only on the collar V below
  the chin), `review/sheet_body_mk_{a,b,c}.png`. Viewer check 210 switches, 0 failed, 0 console errors.
- Build: `MP_GROUPS=2:0.7,3:0.7,4:0.7 SETS=f scripts/run_mp.sh f 0.36,0.33` -> `scripts/build_mp.sh mp_f_r36 export/mm9_monk.glb`
  -> `reduction_uv_audit.py` -> `scripts/gates.sh export/mm9_monk.glb f36`.

# First pass (superseded): candidate e75 (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 16 (prio 1
monster). Lease `mm9reduce:monk` (owner monk-reduce-20261104). No-retexture branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
on the installed r13 (`assets_source/worlds/mm9/models/mm9_monk.glb`, sha256 7cebbf7eb13c, identical to
`../mm9_monk_claude/export/mm9_monk.glb`; copied to `before/`, the rollback source). No Meshy, no credits. **Not installed.**
The creature project `../mm9_monk_claude/` was only read.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,285 (body 10,485 + head 3,800) | 7,127 | 2,564 | 854 |
| **e75 (candidate, `export/mm9_monk.glb`)** | **10,715** (body 6,915 + head 3,800), **-25.0 %** | 5,345 | 1,922 | 637 |
| c72 (alternative, `work/final_C_r72.glb`) | 10,289, -28.0 % | 5,131 | 1,846 | 613 |
| b76 (hands exact, `work/final_B_r76.glb`) | 10,859, -24.0 % | 5,417 | 1,948 | 647 |

## What is kept and what is cut (`scripts/make_sets.py`, `scripts/hand_contact.py`)
Part labels from the creature's own `work/uv_tex.npz`, matched to the GLB faces by UV triple (`scripts/glb_parts.py`; tweak.py moved
the waist after the UVs, so centroids do not match). Protected share measured first: 53.7 % with the brief's full keep set, 42.4 %
with the prio-1 relaxed set used here.
- **Exact:** the whole head set (face, beard, eyes, neck: the `MonkHead` primitive is restored byte for byte, so every tier's face
  is the installed one), cords (thin tubes), shins, whole shoes (a 60 % shoe upper lost 48 mm of the raised left shoe in Death2),
  the robe's inner faces (hood lining, sleeve cups, hem cap: 726) plus one face ring of the outer shell around them, small pieces,
  and the robe/belt faces within 2 cm of a resting hand in any frame of 12 clips (mirrored; 366 faces: without them the hand
  depth grew 0.1-0.4 cm in Fidget2, SweepFidget, Hit, Hit2).
- **Own ratio:** hands 70 % (MPFB, every finger kept; relaxed prio-1 rule), belt 70 %, knots 70 %.
- **Cut:** the robe's outer shell (5,707 -> about 2,800 faces), texture-aware MeshLab collapse, source vertices keep their exact
  4-influence analytic weights, new vertices the nearest source vertex's (no blending, so still 4 influences).
- Normals: installed normals on every source vertex, the Monk's own `build_glb.py` rule (area-weighted, merged by position, robe
  smoothed 3 rounds) on new vertices (`scripts/fix_normals.py`; the rule reproduces the installed normals to 0.02 deg).

## Ladders (`scripts/run_ladder.sh`; limits for 1.87 m: p99 <= 5.61 mm, max <= 28.05 mm, IoU >= 0.98, SSIM >= 0.93)
| ladder | set | step | LOD0 (welded) | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| A | hands exact, shoes 60 % | r88..r72 | 12,545..10,265 | 1.8..4.39 / 48.0 (Death2:15, left shoe) | 0.998..0.994 | fail (shoe) |
| B | hands, shoes exact | r76 | 10,835 | 3.22 / 26.98 | 0.995 / 0.996 | pass |
| B | | r72 | 10,265 | 4.39 / 29.4 (Running:0) | 0.993 / 0.995 | fail (max) |
| C | hands 70 % | r72 | 10,265 | 3.44 / 27.01 | 0.995 / 0.996 | pass |
| C | | r70 / r68 | 9,979 / 9,693 | 3.7 / 29.0, 4.64 / 30.3 | | fail (max) |
| D | C + error lock (3 cm round the worst misses) | r72 | 10,265 | 4.42 / 20.85 | | pass, but p99 worse: the lock moves the error |
| E | C + hand contact | **r75** | 10,691 | 3.29 / 26.98 (AttackRanged2:6, elbow) | 0.995 / 0.996 | **pass, picked** |
| E | | r73 / r72 | 10,405 / 10,263 | 3.62 / 28.98, 3.95 / 29.4 (Running:0, front midline) | | fail (max) |

The robe stops near 10.3-10.7k: below that the front/back centre lines of the lower robe (XF/XB chains, Running) and the
elbows (AttackRanged2) miss by 29-40 mm. Sheets: `review/ladder_sheet_{A,B,C,D,E}.png`.

## Gates, installed -> e75 (`scripts/gates.sh`, `scripts/gate_compare.py`, `review/gates_compare_e75.txt`)
- Clips, skin, nodes, sockets, materials, variants, images byte-identical to the installed file (`same_clips.py`), so jitter,
  orient and bone length are unchanged (bone length re-run: the same 2 Calf entries, MM9's keyed knee).
- Robe gate: legs through robe 0 frames in all 35 clips (as before); cords under robe Pray 5 frames 4.3 -> 4.2 cm, Dead 25
  frames 1.3 -> 1.5 cm.
- Arm/hand: hand depth unchanged except Pray R 1.9 -> 2.2 cm (script clip, palms pressed together: the 70 % hands) and Fidget2 L
  10 -> 11 frames over 1 cm (depth 1.5 unchanged); fewer frames over 1 cm in Fidget, Taunt, CowerStart, Hit2. Forearm unchanged.
  Finger stretch: max unchanged (3.63 fist); the p99 rises with the 70 % hands (AttackMelee 1.65 -> 2.03, Hoe R 1.74 -> 2.48).
- Collapse: face-frames 67,935 -> 43,332; elbow and armpit worst counts drop everywhere (Standing elbow 7/6 -> 2/1, armpit 4/3 -> 0/0).
  Up by a few faces: robe Pray 28 -> 33, Walking/Backpedal 15 -> 16, robe 0 -> 2 in AttackRanged, AttackRanged2, SweepFidget;
  armpit R Death 5 -> 8, Death2 3 -> 4; finger AttackRanged 6 -> 7. Looked at in clay (`review/close_e75_collapse_clay.png`): no
  visible change.
- Detached parts: the same 2 soles in Death/Death2 as before (7.9 / 6.4 cm), nothing new. Winding 0 inverted. Flat shading 0.00 / 0.04.
- Texture quality: body atlas 61.8 -> 61.4 %, fragments 0.3 -> 0.5 %, stretch p90 1.25 -> 1.27; head unchanged.
- LODs (`scripts/lod_check.py`, every frame of every clip): heights within 1 mm of LOD0 (LOD3 top +1.4 mm), lowest points as the
  installed LODs, faces stretched over 20x at most 10/9/2/1 (installed 12/9/2/1).

## Review
Viewer (installed and e75 per tier): http://127.0.0.1:8912/level_generation/creatures/mm9_monk_reduce_claude/review/viewer/
(`run_creature_review.py check`: 210 switches, 0 failed, 0 console errors). Sheets read: `review/sheet_body_mk_{a,b,c}.png`
(front, 3/4, back Standing, Walking, AttackRanged3, Death), `review/sheet_face.png` (front, 3/4, both profiles, every tier;
face boxes differ by at most 1 grey level in the front view), `review/close_b76_*.png`, `review/close_c72_*.png` (GLB close-ups,
clay and textured: chest, mantle, back, sleeves, hem, hands, fist, Pray, cast, run, Death2), `review/close_e75_collapse_clay.png`.

## Build
`scripts/import_source.py` (weld identical weights only: 0 coincident pairs; the 28 degenerate faces vanish, 4 body + 24 head)
-> `dump_mesh.py` -> `glb_parts.py` -> `make_sets.py` (`HANDS=group RINGS=1`) -> `hand_contact.py` (R=0.02) -> `run_ladder.sh E`
with `REA_GROUP_RATIOS=2:0.7,3:0.7,4:0.7` -> `build_pick.sh E r75 final` (export_cand with the source's lowest point as floor
-> swap_lod0 -> fix_normals -> `tools/build_actor_lods.py` default ratios, 4 influences -> skeleton warrior's shrink_shadow_lods ->
carry_variants -> the Monk's LOD fix_winding -> check_winding). Viewer: `viewer_tiers.py`, `make_viewer_manifest.py`, `shot_sheets.py`.
On install: `tools/install_model.py export/mm9_monk.glb --world mm9`, the binding regression, and the line in
`../mm9_monk_claude/README.md` that a rebuild must re-run this reduction.

## Not checked
In game; motion at normal speed (frames and gates only); LOD1-3 close up by eye (numbers only); the shadow meshes by eye;
a low 3/4 face view (the viewer wrapper has none; the face primitive is the installed bytes).

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_Hoe`, `Socket_Broom`, `Socket_Hammer`, `Socket_Cloth`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
