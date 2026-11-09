# MM9 Gezzampt (`mm9_gezzampt`, Gezzamptling / Gezzampt / Gezzampt Elder) reduction: candidate f57 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 57 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:gezzampt` (owner gezzampt-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_gezzampt.glb` (sha256 ecfc476765d1, identical to
`../mm9_gezzampt_claude/export/mm9_gezzampt.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no
repaint. **Not installed.** `../mm9_gezzampt_claude/` was only read (its gates and textures are used from there).

| | LOD0 | body (Gezzampt_A) | head (GezzamptHead_A) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 10,152 | 6,346 | 3,806 | 5,076 | 1,826 | 605 |
| **f57 (`export/mm9_gezzampt.glb`, sha256 d2bd14885264)** | **7,992 (-21.3 %)** | 4,418 | 3,574 | 3,995 | 1,597 | 595 |

Every vertex of the candidate is an installed vertex: positions, normals, UVs, joints and weights are the installed bytes (only
index buffers changed). Clips (17), skin, nodes, sockets, materials, region masks, ramps, `KHR_materials_variants`, all 8 images:
byte-identical (`same_clips.py`). The face skin, eyes, teeth, tusks, mouth carve, ears, horns and the neck seam are the installed
triangles, so every tier's face renders identically (`review/sheet_face_diff_f57.png`: face and neck black in every view; only the
chest, shoulders, crown of the mane and the caption differ).

## Measured first: protected share
42.3 % of LOD0 is exact (`scripts/gezz_sets.py f foot hock`, `review/classes_c.png` shows the head split). Head: separate pieces
(eyes, 17 teeth/tusk pieces: 860), ears (Ponytail-weighted > 0.5 + 1 ring: 635), horns (head region mask G + 1 ring: 357),
non-hide faces (mouth, plug: 244), neck seam (260) and the face skin (in front of z 0.13 below the hairline y 2.33, plus
everything below y 2.13 in front of z -0.02, grown 2 rings: 1,871). Body: neck seam (200), soles (213), hand-graft junction at
the wrist zip (2 rings, 342), and every face a `Foot_h` (175) or `HorseLink_h` (333) helper weights >= 0.4 (see ladders e, f).
Free: mane (crown, back of skull, nape) 771 at 0.7, fists 1,693 at 0.7 (every finger kept: the collapse only removes vertices),
hooves above the soles (region mask G) 302 at 0.7, the rest of the body 3,088 at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Troglodyte's copy of the Highwayman's)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices. Texture guard per collapse on the region
mask (tier A image: hide / hoof, horn) and the shared base colour (100 max / 45 mean). No linings on this body. Changes for the
Gezzampt: the head primitive is cut by its sets (not kept whole); the GLB-to-Blender vertex match tolerance is 2e-4 m (the
importer's re-base leaves 4e-5 m float error; distinct vertices are >= 0.9 mm apart).

## Ladders (height 2.537 m: p99 <= 7.61 mm, max <= 38 mm; `review/ladder_sheet_{c,d,e,f}.png`)
| set | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| c | hands 0.65, mane/hooves 0.7 | r55 / r50 / r45 | 7,622 / 7,444 / 7,266 | 7.83/24.6, 9.13/26.3, 10.4/29.6 | .994/.996 | fail (p99) |
| d | hands 0.7 | r65 / r60 / r57 | 8,064 / 7,886 / 7,778 | 6.14/15.5, 6.97/24.6, 7.28/24.6 (Running, left fetlock `Foot_h`) | .994/.996 | pass |
| e | d + `Foot_h` faces | r60 / r57 / r54 | 7,952 / 7,848 / 7,746 | 6.85/18.9, 7.15/18.9 (Walking, right hock `HorseLink_h`), 7.64 | .995/.996 | pass / pass / fail; e57 built: collapse hock 0 -> 2 in Walking/Backpedal |
| **f** | e + `HorseLink_h` faces | **r57** / r54 | **7,992** / 7,900 | **7.18/17.7 (Death:18)**, 7.77/26.3 | **.995/.997** | **PASS, picked** / fail |

## Gates, installed -> f57 (the Gezzampt's own gates, `scripts/gates.sh`; `review/gates_before/`, `review/gates_f57/`)
- Collapse (`collapse_gate.py`, `scripts/collapse_compare.py f57`): face-frames 7,598 -> 6,442, lower or equal in every clip but Hit
  (218 -> 223). Worst-frame region counts up by one face: shoulder_R 5 -> 6 (Running), 9 -> 10 (AttackMelee2/AttackRanged), torso
  1 -> 2 (Hit), hip_R 0 -> 1 (Death2); hocks equal (they rose 0/1 -> 2 in e57, fixed by set f). Taunt/Aware "exposed head 2 -> 9"
  is a change of the clip's worst frame (0.5 -> 0.23 s); at 0.23 s both files have 13 collapsed and 9 flipped head faces.
- Arm/hand (`NOCLOTH=1 --outer-only --exact`): 0.0 cm, 0 frames over 1 cm in every clip, both files; finger stretch p99 max
  1.18 -> 1.22, max 1.50 both.
- Jitter (vs `gezz_clips0.glb`): 12 -> 13 fails (AttackMelee L 1.89 -> 3.09, R 1.37 -> 3.00 mm/f2; Hit R 3.98 -> 4.70; Hit L
  2.60 -> 1.03 now passes). Clips are byte-identical and every kept vertex skins exactly as installed: the gate's statistic is the
  95th percentile over the shoulder vertices, and the reduced set is a subset (311 -> 207 left). `scripts/shoulder_subset.py`:
  over the clip the p95 maximum drops (AttackMelee L 353.1 -> 339.2, R 529.1 -> 523.6 mm/f2) and the vertex maximum cannot rise
  (396.6 -> 392.8, 565.8 -> 565.8). A sample-set change, not new motion.
- Detached 0 (19 components), bone lengths 0 stretching, winding 0, flat shading 0.00, texture quality: atlas unchanged, stretch
  p90 body 1.11 -> 1.13, head 1.13 -> 1.14, body fragments 0.0 -> 0.1 %.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,f57}.json`), built by `scripts/build_lods.py`
  (tools/build_actor_lods.py, ratios 0.5 / 0.2 / 0.075 so LOD3 stays at the installed count; protected: soles, crown, corpse contact
  of Death/Death2/Dead within 4 cm, ear tips, hoof extremes and both primitives' rest extremes). Rest bounds equal at every LOD
  (installed LOD3 lost 1.6 cm of width); floor per clip: Standing +0.0 / +0.03 / +0.11 / +0.08 cm (installed -0.01 at LOD3),
  Running better at LOD2/3; **corpse sinks more at LOD2/3**: Death/Dead -0.65 / -1.97 cm at LOD2 / LOD3 (installed -0.75 / -0.66);
  the LOD3 low point is a right hoof heel vertex whose LOD weight transfer made it pure `Foot` (protected position, not weights).
  Faces stretched > 20x: 6 / 0 / 0 at LOD1-3 as installed.
- Viewer: `run_creature_review.py check` 102 switches, 0 failed, 0 console errors.

## Review
Viewer (installed and reduced per tier, 17 clips):
http://127.0.0.1:8912/level_generation/creatures/mm9_gezzampt_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_f57.png` (front close-up, 3/4, profile, low 3/4, party; every tier), `review/sheet_face_diff_f57.png`,
`review/sheet_body_f57_a.png`, `review/close_f57_a_{1,3,4}.png`, `review/upper_f57_a_{1,2,3}.png` (mane from behind, side-back, above,
AttackMelee and Taunt nape; chest, back, shoulder profile; fists), `review/upper_f57_c_2.png`, `review/ladder_sheet_e.png`,
`review/classes_{a,b,c}.png`. No visible change found. Look at: the chest and shoulders up close (larger triangles interpolate the
fur normal map a little differently: patchy in the difference image, not visible side by side), the crown of the mane from behind
(0.7), the fists (0.7). The viewer's own focus framings (`head`, `shoulders`) sit low on this 2.5 m body, so `scripts/upper_shots.sh`
frames the upper body on bones instead.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_gezzampt_reduce_claude/before/mm9_gezzampt.glb REA_NODE=Gezzampt $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py
$G scripts/bone_keep.py foot 'Foot_h$' 0.4; $G scripts/bone_keep.py hock 'HorseLink_h$' 0.4
HAIR_Y=2.33 FACE_Z=0.13 BROW_Y=2.13 CHIN_Z=-0.02 EARW=0.5 EAR_RING=1 $G scripts/gezz_sets.py f foot hock; $G scripts/class_view.py f
SETS=f MP_GROUPS=1:0.7,2:0.7,3:0.7 scripts/run_mp.sh f 0.57,0.54        # mpqem -> reduce_ladder (error over every clip) -> compare
LIE=0.04 LOD_RATIOS=0.5,0.2,0.075 SOLE=0.012 scripts/build_mp.sh mp_f_r57 export/mm9_gezzampt.glb
scripts/gates.sh export/mm9_gezzampt.glb f57; python3 scripts/collapse_compare.py f57
REA_NODE=Gezzampt $BL -P scripts/lod_check.py -- $PWD/export/mm9_gezzampt.glb f57
$G scripts/viewer_tiers.py before/mm9_gezzampt.glb inst; $G scripts/viewer_tiers.py export/mm9_gezzampt.glb red   # then make_viewer_manifest.py
scripts/shots.sh; python3 scripts/shot_sheets.py f57; scripts/close_shots.sh; scripts/upper_shots.sh   # pair_sheet.py for the pairs
```
Install (on the user's OK only): `check_winding.py export/mm9_gezzampt.glb` (0), `tools/install_model.py export/mm9_gezzampt.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9`, and add to
`../mm9_gezzampt_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_gezzampt_reduce_claude`; a rebuild from this project
must re-run that reduction". Rollback: `before/mm9_gezzampt.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); tier B beyond the face and body sheets; the orient and
handedness gates (they read only the clips, which are byte-identical); indoor light; Android. `export/mm9_gezzampt_e57.glb` and
`_e57n.glb` are superseded candidates (e57: gates in `review/gates_e57/`). Many scripts in `scripts/` are copies from the Troglodyte
and Highwayman projects that this route did not use.
