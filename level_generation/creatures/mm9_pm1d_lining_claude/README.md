# MM9 PeasantM1d (`mm9_pm1d`, the elf townsman) see-through linings: candidate ready for review (2026-11-05)

Brief: [LINING_BRIEF_20261105.md](../../../devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md) (user approval 2026-11-05).
Lease `mm9lining:pm1d` (owner pm1d-lining-20261105, released); `mm9:peasantm1d` and `mm9reduce:pm1d` were free. Source: the installed
(reduced, 2026-11-04) `assets_source/worlds/mm9/models/mm9_pm1d.glb`, sha256 695064c17d2a (= `../mm9_pm1d_reduce_claude/export/mm9_pm1d.glb`),
copied to `before/` (rollback). No Meshy, no repaint, no new texture. **Not installed.** `../mm9_peasantm1d_claude/` and
`../mm9_pm1d_reduce_claude/` were only read (their gate scripts run in place).

**Candidate: `export/mm9_pm1d.glb`** (= `export/mm9_pm1d_v6.glb`, sha256 d095df7471e1), linings list `export/mm9_pm1d_lining.npz`,
ops `scripts/ops_final.json`.

| | LOD0 | LOD1 | LOD2 | LOD3 | shadow 0/1/2/3 |
|---|---:|---:|---:|---:|---|
| installed | 6,623 | 3,310 | 1,189 | 394 | 6,623 / 3,310 / 1,189 / 394 |
| lined | **7,974 (+1,351)** | 3,808 | 1,369 | 452 | 7,014 / 3,426 / 1,223 / 396 (one-texel linings dropped) |

+1,351 = body +996 (linings, rim strips, caps, armpit patch), head set +355 (backs of the hair cards). That is above the brief's
"about a thousand": the hair backs alone are 355 (see "Open choices").

## Variants on this body
`actors.yml` binds only `mm9_pm1d.glb` (rows 22 Commoner `pm1d_c` and 28 Prisoner `pm1d_d`: tiers of the same file, both lined
here). `mm9_peasantm1.glb` (PeasantM1) is a separate build with its own mesh; it is not lined. Its own sweep row shows openings
of the same kind (torso 255, sleeve R 152, collar 95, head 63 px).

## Openings lined (`scripts/line.py`, GLB level)
Every installed LOD0 vertex row (position, normal, UV, joints, weights) and every installed triangle is byte-identical; new rows
and triangles are appended after them (`scripts/same_lod0.py`: LOD0 EXACT + APPENDED). Clips, skin, nodes, materials,
variants and the 8 images are the installed bytes (`same_clips.py`). New vertices copy the joints/weights of the vertex they line.
The faces that showed holes were found first: the gate copy records the hole pixels per face (`see_through_faces.npz`,
`scripts/hole_faces.py`), so each band only goes as deep as the holes.

| op | what | faces |
|---|---|---:|
| hem | tunic skirt band 20 cm up from the hem (DM2 `rim_lining.py` rule: twin 1 mm behind along the area-weighted normal, reversed, collision cap 40 %, inner-layer faces 0.5 mm with their own paint) + rim strip | 175 + 90 |
| cuffL / cuffR | sleeve bands 45 cm from the cuffs (the AttackMelee view looks 37 cm up the left sleeve) + strips | 124 + 20 / 130 + 24 |
| bootcuffL / R | the turned-down boot cuffs, both rims, whole piece (inner-layer twins in own paint 8 / 14) + strips | 106 + 60 / 105 + 62 |
| bootL / R, trouserL / R, waist | fans over the boot-shaft tops, the trouser bottoms and the breeches' waist top (neck_cap.py technique; the views from the feet ran up the trouser legs into the chest) | 15, 12, 13, 14, 21 |
| buckle | fan over the belt buckle's open back | 16 |
| armpitR | a real 9-edge hole in the tunic at the right armpit (geo_fix remnant), filled in the tunic's own paint (rim UVs per face) | 9 |
| hair | reversed copies (own UVs) of the hair-card faces with >= 20 hole px in the installed run (hair seen from below/behind) | 355 |

Lining texels (darkest uniform 13x13 patch of the garment's own paint, region-clean mask, so the tier ramps recolour it: tier D
lines the jacket dark green): tunic (0.092, 0.311) RGB 0.26/0.11/0.00, boots/belt (0.923, 0.427) 0.19/0.09/0.04, breeches (0.204, 0.068)
0.22/0.09/0.09. Tried and dropped: back faces of the collar lapel sheets (the arm/hand gate then read Conv1 L 5.9 cm / Conv5 L 5.9
cm, reversed faces at the chin), 3 mm twins (sleeve lining up to 2.8 mm out of the cloth at the elbow in Conv1; 1 mm keeps every
twin within 1.0 mm), sleeve bands of 8/15/30 cm (sleeve L 40/39/39 px in AttackMelee).

## See-through (PeasantDM2's gate at the sweep's settings: step 4, 4 mm px, 16 views, every clip; `review/st_before/`, `review/st_final/`, `review/st_compare_final.txt`)
Worst frame per zone, installed -> lined (px). "head" = hair/ears on the head material (the sweep's DM2 classes count these as
collar: collar 68 -> 16 in those classes).

| zone | installed (worst) | lined |
|---|---|---|
| torso | 772 (Death 28 az000) | 19 (Conv5 460) |
| boot L / R | 271 / 257 (Running) | 0 / 1 |
| trousers L / R | 125 / 106 | 0 / 0 |
| sleeve L / R | 68 / 54 (Death) | 6 / 9 |
| head (hair) | 68 (Hit 4) | 16 (Death 24) |
| collar | 23 (Death 4) | 15 (Death 28) |

Every zone is lower or equal in every clip (none Conv4 1 -> 1).

## Other gates (installed numbers: `../mm9_pm1d_reduce_claude/review/gates_d70/`, the same file; lined: `review/gates_final/`)
- Lining poke, render (`scripts/see_through_gate.py lining=`: a visible lining/cap pixel whose ray then meets a front face within 2 cm;
  rim strips, hair backs and the armpit patch excluded, they are meant to show): 3-15 px per clip, single specks at the boot-cuff top
  rims from behind (worst Death 16 az225, `review/st_final/see_through_poke_Death_16_az225_el20.png`). Geometric
  (`scripts/lining_gate.py`, 10 fps): every twin within 1.0 mm of its cloth (worst cuffL 0.89, bootcuffL 0.97 mm, <= 6 vertices).
- UV audit `reduction_uv_audit.py`: **0 LOD0 escaping faces** (both prims). Winding 0. Bones 12 / 0. Detached 0 (= installed).
- LODs (`scripts/lod_check.py`, every frame): rest heights 1.7897 / 1.7897 / 1.7897 / 1.8061 and every clip's lowest point at
  LOD0-3 equal to installed by number (`review/lod_compare_final.txt`); stretched-face counts equal.
- Arm/hand (`arm_hand_gate.py --outer-only --exact`): hand and forearm depths and frames identical in every clip (Conv1 L 3.1 cm 31 f,
  Conv5 L 1.8 cm 13 f). Finger-stretch maxima rise (e.g. Conv5 L 1.38 -> 1.49): the 131 new hand-weighted cuff-strip edges join the
  sample; the MPFB fingers (head prim) are unchanged bytes.
- Sleeve poke: identical (Death R 4.9 -> 4.7 mm).
- Jitter: 6 fails vs installed 4: the installed Walking/Death pair plus **AttackMelee shoulder skin L 5.37 / R 4.74 mm/f2** (was
  0.78 / 0.52). Not motion: the clips are byte-identical and every twin's acceleration stays within 1.05 mm/f2 of its source vertex
  (`scripts/twin_motion.py`, `review/twin_motion_final.txt`); the sleeve twins near the shoulder join the gate's p95 sample
  (original vertices 344.0 -> with linings 354.6). Hanndl's lined GLB showed the same artifact.
- Texture quality: atlas equal; body density p10 0 / huge spread from the one-texel linings (as Hanndl/DM2). Flat 0.01 (caps).
- Viewer `run_creature_review.py check --port 8941`: 52 switches, 0 failed, 0 console errors.

## Sheets read (viewer, both tiers)
`review/sheet_close_c_{1..4}.png`, `review/sheet_close_d_{1..4}.png` (armpit, boot fronts/backs, buckle, collar, cuffs low/out,
hair front/side/back/low/party, hem front/back/low, Running knees), `review/sheet_face_{c,d}_1.png` (face skin black in the diff; only
hair-card outlines change), `review/sheet_body_{c,d}_1.png` (Standing front/3-4/back/party, Walking, Talk, Death),
`review/sheet_worst_c_{1,2}.png` (the installed worst view of every zone), `review/sheet_poke_c_1.png` (elbow in Conv1/Conv5, cuff
AttackMelee, boot cuffs Dead/Cower). Installed | lined | |diff| x4 per row.

## Look at
The boot cuffs and knees in Running/Cower/Dead (dark interiors where the background showed), the hem from below on the corpse, a thin
dark crease line at the left elbow fold in Conv1/Conv5 (`sheet_poke_c_1.png`), the hair from below/behind (hair backs).

## Open choices for the orchestrator
- Sleeve depth 45 cm costs the jitter-sample artifact above; `cuff* depth 0.15` (ops_v3 setting) keeps jitter at 4 fails but leaves
  sleeve L 39 px in one AttackMelee view.
- Hair backs (355 faces) take the head zone 68 -> 16; without them LOD0 is +996.

## Build
```sh
scripts/build.sh scripts/ops_final.json v6     # line.py -> build_lods.py -> shrink_shadow_lods_dm2.py -> carry_variants -> fix_winding -> check_winding
cp export/mm9_pm1d_v6.glb export/mm9_pm1d.glb; cp export/mm9_pm1d_v6_lining.npz export/mm9_pm1d_lining.npz
scripts/st.sh before/mm9_pm1d.glb before; scripts/st.sh export/mm9_pm1d.glb final lining=$PWD/export/mm9_pm1d_lining.npz
python3 scripts/st_table.py before final; scripts/gates.sh export/mm9_pm1d.glb final
../claude_shared/gltf_venv/bin/python scripts/lining_gate.py export/mm9_pm1d.glb export/mm9_pm1d_lining.npz review/lining_gate_final.json 10
REA_NODE=PM1d blender -b -P scripts/lod_check.py -- export/mm9_pm1d.glb final
../claude_shared/gltf_venv/bin/python scripts/viewer_tiers.py export/mm9_pm1d.glb fin; scripts/make_viewer_manifest.py ...; scripts/shots.sh close|worst|body <ids>; scripts/pair_sheet.py
```
Install (orchestrator): `check_winding.py export/mm9_pm1d.glb`, `tools/install_model.py export/mm9_pm1d.glb --world mm9`, the binding
regression, and a note in `../mm9_peasantm1d_claude/README.md`. Rollback: `before/mm9_pm1d.glb`. A rebuild from the creature project
must re-run the reduction and then these linings (`line.py` on the reduced GLB).

## Not checked
In game (not installed; binding regression and floor audit after install); motion at normal speed by eye; LOD1-3 and shadow meshes by
eye (numbers only); the gate's full step-3 density; the poke specks at the boot-cuff top rims in Death were not looked at in a
textured close-up of that exact frame.
