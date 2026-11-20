# MM9 Lesser Demon (`mm9_lesserdemon`, MM9 Demon A) reduction: candidate j r66 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster, relaxed
keep set), ledger row 44 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:lesserdemon` (owner
lesserdemon-reduce-20261104). Source: the installed `assets_source/worlds/mm9/models/mm9_lesserdemon.glb` (r10 of
`../mm9_stage1demon_claude/`, sha256 416e255ad769, approved by the user 2026-11-01), copied to `before/` (the rollback source).
The creature project's `export/mm9_lesserdemon.glb` is the dropped, never-installed neck pass (2026-11-01) and was not used.
No Meshy, no credits, no repaint. **Not installed.** `../mm9_stage1demon_claude/` was only read.

| | LOD0 | body set | head set | LOD1 | LOD2 | LOD3 | top at every LOD |
|---|---:|---:|---:|---:|---:|---:|---|
| installed r10 | 12,295 | 7,519 | 4,776 | 6,080 | 2,125 | 926 | 2.659 / 2.658 / **2.533 / 2.535** m (LOD2/3 lost the back spike) |
| **j r66 (`export/mm9_lesserdemon.glb`, sha256 f4ac3dd9d705)** | **10,099 (-17.9 %)** | 5,797 | 4,302 | 4,977 | 1,725 | 1,013 | 2.659 m at every LOD |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights; only index buffers changed).
Clips, skin, nodes, materials (with their extras) and all 6 images are byte-identical (`scripts/same_clips.py`). One skin, no
tiers. Face (snout, brows, eyes, lips, mouth cavity, teeth, tongue, horn roots) is the installed triangles: black in every face
diff (`review/sheet_face_j66.png`).

## Keep set and groups (`scripts/make_sets.py`, `head_classes.py`, `contact_lock.py`; labels from the creature's `work/faces.npz` matched by UV)
Measured first: the face/teeth/eyes/tongue/horn roots, neck band, soles, pieces of up to 60 faces and piece contacts were 35.5 %
of LOD0; with the gate keeps 42.9 %.
- **Exact:** head faces in front of z 0.66 and within 3 cm of teeth/tongue/eyes (class 1), horn roots (3 cm band), teeth, eyes,
  tongue; the neck seam (head-shell and body faces within 3 cm of each other); soles (below 5 cm); body pieces of up to 60 faces
  (skirt shards, back spikes); each piece's contact faces (within 1.5 cm of another piece: talon roots in the gauntlet flange,
  shard roots, the tail's two pieces); the gauntlet hands; the tail and the pieces over 60 faces (bracers: cutting them gave
  35-100 mm errors at the tail root and forearms, ladders a/b); **shoulder skin** (every body face touching a Clavicle/UpperArm
  vertex: the jitter gate's shoulder set; build i68 failed AttackMelee L 2.27 mm/f2 without it) and the body faces within 5 cm
  of a hand/forearm at every frame where the arm/hand gate reports the arm inside the body.
- **Cut:** skin and armour plates at the ladder ratio (0.66); talons 0.45 (`mpqem.py` change below); cranium (back of head) 0.7;
  horn shafts 0.8 (tips and outer curl kept in the LODs).

## Route: `scripts/mpqem.py` (Highwayman copy), one change
Pose-aware half-edge collapse over 262 poses (every clip at 10 Hz) with the texture guard. **New: seam slides**
(`MP_SEAM_GROUPS=1`, talons only): a UV-seam vertex with two GLB copies may collapse along its seam onto the next seam vertex
when both charts agree (each copy goes to the same chart's copy of the target; the 5-D quadric is evaluated per face against its
own chart). The talons are six-sided tubes whose seam line locked every ring: without slides they stopped at 896 of 1,248 with a
4.15 mm worst collapse; with slides 550 at 0.50 mm.

## Ladders (limits for 2.41 m: p99 <= 7.23 mm, max <= 36.15 mm; `work/selection_<label>.json`, `review/ladder_sheet_<label>.png`)
| ladder | groups (talons/hands/pieces+tail/cranium/horns) | step | LOD0 | p99 / max mm | |
|---|---|---|---:|---|---|
| a | .6/.7/.7/.7/.75 | r60 / r45 | 9,617 / 9,015 | 11.7/101 (tail root, bracers) | fail |
| b | pieces kept | r60 / r50 | 9,827 / 9,425 | 10.2/35.6, 13.7/39.7 | fail (skin too lean for 0.6) |
| c | b | r80 / **r75** / r70 | 10,627 / 10,427 / 10,227 | 6.58, **7.15**, 7.64 | pass / pass / fail |
| d | hands kept | r75 / r70 | 10,461 / 10,261 | 6.91 / 7.41 | pass / fail |
| e / f | horns kept / cranium kept | r70 | 10,435 / 10,595 | 7.05 / 7.31 | pass / fail (horns carry the head error) |
| g | e + talon seam slides .55 | r70 / r65 | 10,211 / 10,011 | 6.34 / 7.26 | pass / fail |
| h | talons .45 | r68 / r65 | 10,009 / 9,889 | 6.67 / 7.27 | pass / fail |
| i | h + horns .8 | **r68** / r66 | **9,869** / 9,789 | 6.82/24.3, 7.24 | built: gates found the jitter fail above |
| **j** | i + shoulder and arm-contact keeps | **r66** / r62 | **10,099** / 9,975 | **6.81 / 35.6**, 7.95 | **picked** / fail |

## Gates, installed -> j66 (the demon's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_j66/`, `review/gates_compare_j66.txt`)
- Collapse face-frames 47,334 -> 40,089, equal or lower in every clip (Standing 783 both).
- Jitter: the same 3 fails with the same values (Fidget L 3.64, AttackMelee2 L 10.07, DodgeLeft R 2.6 mm/f2).
- Arm/hand (`--outer-only --exact`): DodgeRight R 4.6 -> 0.8 cm, Block R 1.3 -> 1.2, AttackMelee L 0.3 -> 0, Dead R 0.7 -> 0.4;
  Death L 3.9 (frame 120) unchanged there but the clip's max reads **4.5 cm at frame 96**, Death R 1.6 -> **2.0 cm at frame 83**
  (frames over 1 cm 9 -> 5). Both new readings are a talon of one hand against the other hand's (reduced) talon in the dying pose,
  where the gate takes the depth behind the nearest face; the generalised winding number of every hand vertex against the other
  hand's closed talons is 0.036 / 0.016 for both models (`scripts/talon_inside.py`, `scripts/hand_probe.py`): not inside.
  Finger-stretch maxima unchanged (p99 is higher: fewer talon vertices).
- Detached: the same 11 pieces with the same distances. Bone lengths 0 stretching; winding 0; flat shading 0.00 / 0.00.
- Texture quality: body stretch p90 1.19 -> 1.20, head 1.34 -> 1.38 (horns and cranium); atlas unchanged.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/lod_table.py before j66`): protected points (soles, the top,
  outer horn curl and horn tops, talon tips, tail tip, the corpse contact) keep the height at 2.659 m on every LOD (installed LOD2/3
  lost 12.5 cm) and the feet on the floor (Standing LOD2/3 -0.1/-0.2 cm, installed +0.9/+1.7; Dead 0 at every LOD); stretched
  faces 15/10/10/4 (installed 15/12/10/5). LOD3 is 1,013 (installed 926) because of those points.
  **Trap:** Blender's import puts this mesh's vertices up to 1.3e-5 m off the GLB values, and `build_actor_lods.py` matches
  protected points to 1e-5: plain (x, -z, y) points matched nothing and LOD3 stood 8 cm up; `build_lods.py` now maps each point
  to the imported vertex nearest to it first.

## Review
Viewer (installed and reduced, all 19 clips; `run_creature_review.py check`: 38 switches, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_lesserdemon_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_j66.png` (front close-up, 3/4, profile, low 3/4, party, open mouth; diff x4: face black),
`review/sheet_body_j66.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/sheet_close_j66.png` (talons 3/4 and
in AttackMelee, horns from behind and above), `review/horn_pair_i68.png`, `review/ladder_sheet_h.png`, `review/head_classes.png`,
`review/sets_a.png`. Look at: the horn outlines (slightly coarser shading at 0.8), the talons (six-sided tubes with fewer rings),
the chest plate and back-of-head cranium (cut at 0.66 / 0.7).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
$G scripts/glb_parts.py; $G scripts/comp_stats.py > work/comp_stats.txt; $G scripts/head_classes.py
REA_GLB=level_generation/creatures/mm9_lesserdemon_reduce_claude/before/mm9_lesserdemon.glb REA_NODE=LesserDemon $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py
$G scripts/contact_lock.py x 0.05 before i68; EXTRA=work/keep_extra_x.npy $G scripts/make_sets.py x
MP_SEAM_GROUPS=1 SETS=x MP_GROUPS=1:0.45,2:1.0,3:1.0,4:0.7,5:0.8 scripts/run_mp.sh j 0.66,0.62,0.58
scripts/build_mp.sh mp_j_r66 export/mm9_lesserdemon.glb      # swap_mp -> build_lods (protected) -> shrink_shadow_lods -> fix_winding
scripts/gates.sh export/mm9_lesserdemon.glb j66; python3 scripts/gate_compare.py j66
```
(`contact_lock.py` reads `review/gates_i68/arm_hand.json`, the gate of the first build, for its worst frames.)
Install (on the user's OK only): `check_winding.py export/mm9_lesserdemon.glb` (0), `tools/install_model.py
export/mm9_lesserdemon.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9
--match 'MM9 Demon A'`, and add to `../mm9_stage1demon_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_lesserdemon_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_lesserdemon.glb`.

## Not checked
In game; motion at normal speed by eye (frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only);
the binding regression and floor audit (they read the installed file: after install).
