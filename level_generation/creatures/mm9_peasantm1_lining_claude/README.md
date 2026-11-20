# MM9 PeasantM1 (`mm9_peasantm1`, the human townsman) see-through linings: candidate ready for review (2026-11-05)

Brief: [LINING_BRIEF_20261105.md](../../../devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md) (user approval 2026-11-05, PeasantM1 row).
Lease `mm9lining:peasantm1` (owner peasantm1-lining-20261105, released); `mm9:peasantm1` and `mm9reduce:peasantm1` were free. Source: the installed
(reduced e80, ledger row 89) `assets_source/worlds/mm9/models/mm9_peasantm1.glb`, sha256 cbbe883e31bf (= `../mm9_peasantm1_reduce_claude/export/mm9_peasantm1_e80.glb`),
copied to `before/` (rollback). No Meshy, no repaint, no new texture. **Not installed.** `../mm9_peasantm1_claude/`, `../mm9_peasantm1_reduce_claude/`,
`../mm9_peasantm1d_claude/` (fix_winding) and `../mm9_peasantm2d_claude/` (sleeve poke) were only read; their gate scripts run in place.
Scripts are copies of PeasantM1d's lining (`../mm9_pm1d_lining_claude/scripts/`), adapted (names, maskless head set, the additions below).

**Candidate: `export/mm9_peasantm1.glb`** (= `export/mm9_peasantm1_v7.glb`, sha256 23b3cc2263ba), linings list `export/mm9_peasantm1_lining.npz`,
ops `scripts/ops_final.json`.

| | LOD0 | LOD1 | LOD2 | LOD3 | shadow 0/1/2/3 |
|---|---:|---:|---:|---:|---|
| installed | 6,236 | 3,117 | 1,117 | 370 | 6,236 / 3,117 / 1,117 / 370 |
| lined | **7,641 (+1,405)** | 3,811 | 1,367 | 453 | 6,608 / 3,355 / 1,137 / 366 (one-texel linings dropped) |

+1,405 = body +1,387 (jacket linings 821 + rim strips 198, jacket patches 175, shirt-front backing 167, neck cap 26), head set +18 (hair backs).
Above the brief's "about a thousand" (as PeasantM1d's +1,351): the open jacket's front edges and hem form one 70-vertex loop and the
holes reach 13 cm into the flaps (see "Open choices").

## Openings lined (`scripts/line.py`, GLB level)
Every installed LOD0 vertex row (position, normal, UV, joints, weights) and every installed triangle is byte-identical; new rows and
triangles are appended (`scripts/same_lod0.py`: LOD0 EXACT + APPENDED). Clips, skin, nodes, materials, variants and the 9 images are the
installed bytes (`same_clips.py`). New vertices copy the joints/weights of the vertex they line. Band depths come from the gate's hole map
(`scripts/hole_depth.py`: per loop, hole-weighted depth of the faces with hole pixels).

| op | what | faces |
|---|---|---:|
| hem | jacket front edges + hem (one 70-vertex loop), band 13 cm deep (hole depth p99 0.127 m), twins 1 mm behind, reversed, collision cap 40 %, inner-layer (Meshy fold) faces 0.5 mm in their own paint (170), + rim strip | 700 + 140 |
| collar | the jacket's neckline (62-vertex loop), 9 cm, the hem's texel, + rim strip | 40 + 18 |
| cuffL / cuffR | sleeve bands 13 cm from the cuffs in the sleeve's own (region G) dark texel, + strips; 10 sleeve faces left out (below) | 42 + 22 / 39 + 18 |
| patch | jacket faces that still showed holes after the bands (v5 run, >= 3 px, one ring grown, `scripts/line.py` backface + `texel_from`): shoulders and upper chest seen down the collar and through the open front, 1 mm behind, the hem's texel | 175 |
| shirt | the shirt-front sheet in the jacket opening (single-sided): reversed copy of all 167 faces in its own paint, 1 mm behind | 167 |
| neck | cap over the face shell's neck tube (head prim loop), placed in the body prim on the jacket's dark texel | 26 |
| hair | reversed copies (own UVs) of the hair-shell faces with >= 3 hole px (hair seen from below) | 18 |

Lining texels (darkest uniform 13x13 patch of the garment's own paint, region-clean, so the tier ramps recolour them): jacket (0.136, 0.257)
RGB 0.08/0.05/0.01 (region R: tier A dark olive-brown, tier B dark red), sleeves (0.028, 0.407) 0.19/0.12/0.02 (region G: tier B's cream
sleeves line in a darker cream).

Tried and dropped:
- Coincident reversed shirt copy (0 mm): `arm_hand_gate.py` read hands resting on the shirt as 5.9 cm inside (Conv5 L, Bow R, nearest-face
  tie); 1 mm behind fixes it (`scripts/hand_contact_faces.py` lists the faces a hand reads as inside of).
- Cuff faces that fold through the forearm axis: their twins sat on the other side of the axis and `sleeve_poke_gate.py` read the visible
  hand past the cuff as skin through the sleeve (Conv4 R 15.8 -> 24.2 mm, Fidget/Talk R +1 mm). `scripts/axis_faces.py` finds them (sampled
  face points within 6 mm of the posed forearm axis in any clip at 24 fps): L 1297, 1619, 1620, 1960, 2116, 2119, 2135, R 1325, 1326, plus L
  rim face 1545 (Running L +0.3 mm, `scripts/sleeve_poke_why.py`), excluded from the cuff bands. Sleeve poke is now identical to installed.
- A fill of the 5-edge hole in the jacket at the left hip (as PeasantM1d's armpit): own-paint fans streaked (rim faces on different UV islands),
  a uniform texel, a recessed dark backing and mirrored UVs all read as a patch from outside, while the installed hole shows the jacket's own
  inner layer there. Left open (`hipL` view unchanged, black diff).
- Bands at 7 cm (v2/v3): torso still 134-211 px (flaps just past 7 cm); boot-cuff/buckle/boot linings: boot L is 15 px at most, below the target.

## See-through (PeasantDM2's gate at the sweep's settings: step 4, 4 mm px, 16 views, every clip; `review/st_before/`, `review/st_v7/`)
Worst frame per zone, installed -> lined (px; `review/st_compare_final.txt` per clip). The sweep's DM2 classes give the same numbers here
(the head set's Head-bone faces are the hair shell and face shell, counted as head in both).

| zone | installed (worst) | lined (worst) |
|---|---|---|
| torso | 263 (Death 28 az315) | **9** (Dead 0 az045 el20) |
| sleeve R / L | 150 (Death 28) / 66 (Bow 48) | **2 / 2** |
| collar | 92 (Death 28) | **2** |
| head (hair/neck) | 63 (Death 24) | **2** |
| boot L / R | 15 (Bow 40) / 1 | 15 / 1 (not lined: below the target) |
| trousers | 0 | 0 |

No zone is worse in any clip. Torso per clip: Talk 252 -> 2, Bow 244 -> 3, Hit 212 -> 3, Dead 201 -> 9, Conv5 183 -> 2, Running 134 -> 2.

## Other gates (installed numbers: `../mm9_peasantm1_reduce_claude/review/gates_e80/`, the same file; lined: `review/gates_v7/`)
- Lining poke, render (`see_through_gate.py lining= poke_kinds=band,cap,sheet`: a visible lining pixel whose ray then meets a front face within
  2 cm; rim strips and hair backs excluded): 3-50 px per clip (AttackMelee 50 at 16 az045 el20, Cower 41
  at 0 az000 el20, Hit 26, the rest <= 20): thin lines at the jacket's front edges where the ray grazes the flap edge into the gap over the shirt,
  and in Cower the inside of the swung-out right flap. Read in textured close-ups of those exact frames (`review/sheet_poke_a_1.png`): no dark
  specks on the outside of the cloth; the front edges look as installed; in Cower the inside of the flap now reads dark where the installed
  model showed through it (culled back faces) to the jacket's far side.
  Geometric (`scripts/lining_gate.py`, 10 fps, every clip; nearest-face search widened from 8 to 32 faces, 8 missed the own face under large
  shoulder triangles and read the collar fold 8.5 mm away): every twin within 1.0 mm of its cloth (hem 1.0, collar 0.5, cuffs 1.0, patch 1.0 mm,
  at most 7 vertices at once). `scripts/twin_motion.py`: every twin's acceleration within 1.0 mm/f2 of its source vertex in every clip.
- UV audit `reduction_uv_audit.py`: **0 LOD0 escaping faces** (both prims). Winding 0. Flat shading 0.00. Bones 12 / 1 stretching (L Thigh, the
  installed's own). Detached 0 (= installed).
- Arm/hand (`arm_hand_gate.py --outer-only --exact`): hand depths and frames identical in every clip (Conv5 L 2.2 cm 15 f, Bow R 3.8 cm 10 f) except
  Bow L 1.5 -> 0.7 cm; forearm depths equal or lower (Fidget L 5.6 -> 1.1, R 6.0 -> 3.3, Talk L 2.1 -> 1.0, Conv5 L 3.1 -> 2.2 cm). The forearm drops
  are the gate's outer-surface classification (new faces change which jacket faces count as outer), not geometry: the arm vertices are the
  installed bytes. Finger-stretch p99 within 0.04 of installed (new hand-weighted cuff-strip edges join the sample).
- Sleeve poke (`sleeve_poke_gate.py --skin-mat PeasantM1Head --cloth-mat PeasantM1_A`): **identical** to installed in every clip.
- Jitter (`jitter_gate.py` vs `../mm9_peasantm1_claude/work/mm9_pm1_clips.glb`): 8 fails = the installed 8 (Walking L/R, Talk R, Death L/R, Conv4 R,
  Conv5 L, Bow R); shoulder-skin p95 values move by -0.7..+0.45 mm/f2 (Conv5 L 6.29 -> 6.74) because the twins join the gate's vertex sample.
- Texture quality: atlas equal (body 59.1 %, head 33.0 %); body density p10 0 / huge spread from the one-texel linings (as Hanndl/DM2/PeasantM1d).
- LODs (`scripts/lod_check.py`, every frame of every clip, `review/lod_compare_final.txt`), rebuilt by the reduction's snap-fixed `build_lods.py`
  (protected soles, crown and corpse contact), DM2's `shrink_shadow_lods.py`, `carry_variants.py`, PeasantM1d's `fix_winding.py`: rest height
  1.7938 m at every LOD (= installed); every clip's lowest point equal to installed at LOD0 and LOD1, and at LOD2/3 in every clip but Death
  (LOD2 -0.25 -> +0.11 cm, LOD3 -0.20 -> +0.11 cm: now nearer LOD0's +0.01 cm); 0 stretched faces at every LOD (= installed).
- Viewer `run_creature_review.py check --port 8957`: 52 switches, 0 failed, 0 console errors.

## Sheets read (viewer, both tiers; installed | lined | |diff| x4 per row)
`review/sheet_close_{a,b}_{1..4}.png` (collar back/front/side/top, cuffs out/low, jacket front edges 3/4 both sides, hair front/back/low/party,
hem front/back/low, left-hip hole, shirt front/side), `review/sheet_face_{a,b}_1.png` (face black in the diff; only the collar/shirt edge pixels
change), `review/sheet_body_{a,b}_1.png` (Standing front/3-4/back/party, Walking, Talk, Death), `review/sheet_worst_{a,b}_{1,2}.png` (the installed
worst view of every zone), `review/sheet_poke_a_1.png` (the poke gate's worst frames: AttackMelee 16, Cower 0, Hit 20). Earlier: `review/sheet_close_v5_a_*.png`, `review/sheet_worst_v5_a_*.png`, `review/poke_v3.png`, `review/st_before_worst.png`.

## Look at
The cuffs from below (dark interior where the background showed; tier B's sleeves line in darker cream), the gap between the shirt and the
right jacket flap from 3/4 (now the dark lining instead of the background), the corpse's chest from the feet (Death/Dead), the hair from
below, and the thin dark lines at the jacket's front edges that the poke gate reports.

## Open choices for the orchestrator
- Hem depth: 13 cm (700 faces) covers 99 % of the hem holes; at 7 cm (506 faces, v3) the torso still read 134-211 px. A 10 cm band (610 faces)
  was not built.
- The jacket patches (175 faces) take Death's falling frame (torso 65 / sleeve R 96 px in v5) down; without them LOD0 is +1,230.
- Left-hip hole left open (see above).

## Build
```sh
scripts/build.sh scripts/ops_final.json v7     # line.py -> build_lods.py -> shrink_shadow_lods_dm2.py -> carry_variants -> fix_winding -> check_winding
cp export/mm9_peasantm1_v7.glb export/mm9_peasantm1.glb; cp export/mm9_peasantm1_v7_lining.npz export/mm9_peasantm1_lining.npz
scripts/st.sh before/mm9_peasantm1.glb before; scripts/st.sh export/mm9_peasantm1.glb v7 lining=$PWD/export/mm9_peasantm1_lining.npz poke_kinds=band,cap,sheet
../claude_shared/gltf_venv/bin/python scripts/st_table.py before v7; scripts/gates.sh export/mm9_peasantm1.glb v7
../claude_shared/gltf_venv/bin/python scripts/lining_gate.py export/mm9_peasantm1.glb export/mm9_peasantm1_lining.npz review/lining_gate_v7.json 10
../claude_shared/gltf_venv/bin/python scripts/twin_motion.py export/mm9_peasantm1.glb export/mm9_peasantm1_lining.npz
REA_NODE=PeasantM1 blender -b -P scripts/lod_check.py -- export/mm9_peasantm1.glb v7
../claude_shared/gltf_venv/bin/python scripts/viewer_tiers.py export/mm9_peasantm1.glb fin; scripts/make_viewer_manifest.py v7 inst_a=..=work/viewer_inst_th_a.glb fin_a=.. inst_b=.. fin_b=..
scripts/shots.sh close|worst|body inst_a fin_a inst_b fin_b; scripts/pair_sheet.py close inst_a fin_a sheet_close_a 5
```
The patch op reads `work/v5_holes_inst.npz` (the v5 run's hole pixels per installed face); `scripts/hole_faces.py` + the v5 GLB regenerate it.
Install (orchestrator): `check_winding.py export/mm9_peasantm1.glb`, `tools/install_model.py export/mm9_peasantm1.glb --world mm9 --name mm9_peasantm1.glb`,
the binding regression, and a note in `../mm9_peasantm1_claude/README.md`. Rollback: `before/mm9_peasantm1.glb`. A rebuild from the creature project
must re-run the reduction (`../mm9_peasantm1_reduce_claude/`, e80) and then these linings (`line.py` on the reduced GLB).

## Not checked
In game (not installed; binding regression and floor audit after install); motion at normal speed by eye; LOD1-3 and shadow meshes by eye
(numbers only); the gate's full step-3 density; the poke pixels were looked at in the gate's flat renders and textured stills, not frame by frame.
