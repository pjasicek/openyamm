# MM9 Guard (`mm9_guard`, Guard / Sergeant / Captain) LOD0 reduction: candidate e55 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 48 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:guard` (owner guard-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_guard.glb` (sha256 f061fec71854, identical to
`../mm9_guard_claude/export/mm9_guard.glb`), copied to `before/` with the four attachments (the rollback source). No Meshy, no
credits, no repaint. **Not installed.** `../mm9_guard_claude/` was only read.

| | LOD0 | Guard_A (body) | GuardHead_A (face, helmet, badge) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 11,486 | 8,680 | 2,806 | 5,742 | 2,062 | 681 |
| **e55 (`export/mm9_guard.glb`, sha256 0810fe772256)** | **9,028 (-21.4 %)** | 6,408 | 2,620 | 4,511 | 1,618 | 534 |

Attachments unchanged: halberd 418 / halberd2 418 and the plates 323 / 456 (the plates are what they need to be: cheek returns and
eye mask; the halberd is already a 418-triangle procedural lathe). Every vertex of the candidate is an installed vertex: positions,
normals, UVs, joints and weights are the installed bytes (only index buffers changed). Clips, skin, nodes, materials,
`KHR_materials_variants`, all 16 images: byte-identical (`same_clips.py`). Face/neck skin: all 1,510 triangles present with the
installed indices, so every tier's face renders pixel-identical (`review/sheet_face_diff_e55.png`: face and neck black).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Highwayman's copy)
Each collapse is scored over 296 poses (every clip at 10 Hz) plus a position+UV quadric, a texture guard over all three tiers of
both texture sets refuses collapses that would show colours the source does not have there (100 max / 45 mean), and only
vertices are removed. finish_guard's linings (2 rings at the tunic rims, helmet, gauntlet cuffs, elbow fins) are re-emitted as
the reversed faces of each surviving lined outer face's 3 mm twins (`lining 1,146 -> 882`); eight centre-seam lining faces with
no exact outer partner are kept as they are (`scripts/lining_match.py`; without that the first ladder had 10 new open edges).
Open edges equal to the installed model (1,004) at every LOD0 step used.

Keep set (`scripts/make_sets.py`, `SMALL=80 GAUNTLET=1`), 42.6 % of the faces:
- exact: face/neck skin (1,510), helmet rim within 1.2 cm of the face skin, helmet under the plate attachments (within 1.2 cm, so
  the plates keep their 7 mm clearance), shoulder fans, soles, hand-graft junction (2 rings), grip contact (78 faces within
  1.5 cm of the halberd), right hand 2nd/3rd phalanges (wrap), belt, buckle, badge, brooches, fins, bits (pieces up to 80
  faces), gauntlets and the sleeve within 2.5 cm of them, and the body faces under the resting hands / beside the halberd
  (`scripts/contact.py`: tunic, skirt, pants, helmet within 4 cm of a hand in the hand-rest clips, 3 cm of the halberd in any
  clip, mirrored);
- own ratios: hands 0.65 (every finger kept), helmet 0.6, boots 0.55, pants 0.6, skirt whole (1.0);
- shared cut (tunic and the rest): ladder ratio 0.55.

## Ladders (1.882 m: p99 <= 5.65 mm, max <= 28.2 mm, IoU >= .98, SSIM >= .93, open edges <= 1,004)
| config | change | step | LOD0 | p99 / max mm | IoU / SSIM | verdict |
|---|---|---|---:|---|---|---|
| a | first keep set | r60 / r50 / r40 | 8,706 / 8,354 / 8,314 | 3.59/11.6, 5.67/18.3, 6.8/32.0 | .995/.995 | fail (10 lost lining faces) |
| b | a + orphan linings kept | r60 / **r55** / r50 | 8,714 / 8,532 / 8,362 | 3.59/11.6, 4.23/12.6, 5.67/18.3 | .994/.995 | b55 built: gates found gauntlets 1.7 cm off the sleeve, buckle cut to a detached piece, Death/Dead L hand 0.3 -> 1.4 cm, CowerLoop R fist into the cut helmet, halberd in the shoulder in Sleep 4 -> 12 frames |
| c | b + buckle, contact set, gauntlets 0.8 | r55 / r50 | 8,938 / 8,808 | 4.32/13.1, 6.24/26.0 | | fail: one new open edge at the skirt's front centre |
| d | c, skirt whole, boots 0.55, pants 0.6 | r55 / r52 | 8,870 / 8,788 | 4.84/13.1, 5.41/17.7 | .991/.994 | pass; d55 built: gauntlets still 0.9-1.1 cm off in 5-10 poses |
| **e** | d + gauntlets and the sleeve beside them exact | **r55** / r52 | **9,028** / 8,960 | **4.87/14.4** (AttackMelee:9), 5.91/19.1 | **.992/.994** | **r55 PASS, picked**; r52 fail |

## Gates, installed -> e55 (the Guard project's own gates, `scripts/gates.sh`; `review/gates_before/`, `review/gates_e55/`, `review/gates_compare_e55.txt`)
- Skirt (`skirt_gate.py`): identical in every clip (Cower 36/125 1.2 cm, CowerLoop 44/44 1.3 cm as installed).
- Arm/hand (`--outer-only --exact`): no value worse in any clip; better: Fidget L frames over 1 cm 19 -> 16, Fidget2 51 -> 50,
  Hit2 4 -> 3, Death2 L 1.3 -> 1.1 cm, AttackMelee2 R forearm 0.5 -> 0.4 cm. Finger stretch maxima equal or lower.
- Grip (halberd merged back, `merge_halberd.py`): finger skin inside the shaft 0.1 -> 0.0 cm in every clip but Running (0.5 both);
  wrap min 90 / median 150 deg both, mean 142.4 -> 140.6 (one 15-deg bin less on Index or Middle in some clips: fewer sampled
  vertices on the cut palms and proximal phalanges).
- Blade (halberd against the body): identical except Sleep frames over 1 cm 4 -> 3.
- Jitter: 0 fails both; worst shoulder-skin excess 1.79 both.
- Collapse face-frames 13,706 -> 8,110; worst-frame region counts up by one or two faces in some clips (armpit L 0 -> 1 in
  Standing/Walking/Fidget, Fidget2 armpit L 0 -> 2, AttackMelee2 hand L 6 -> 7, Hit2 elbow L 2 -> 3, Sleep armpit R 2 -> 3),
  down almost everywhere else (AttackMelee2 armpit R 49 -> 25, Cower armpit L 25 -> 11).
- Detached parts: 0 both. Bone lengths: same 2 stretching thighs (clips). Winding 0. Flat shading 0.00. Texture quality: equal
  (atlas 57.4 / 57.8 %, stretch p90 1.11 -> 1.13 / 1.12).
- LODs (`lod_check.py`, every frame of every clip; `work/lod_check_{installed,e55}.json`, `scripts/lod_summary.py`): height
  1.8811 m at every LOD; Standing lowest point LOD2 +0.63 cm (installed -0.17), LOD3 +2.29 (installed +2.68); Death LOD3 -1.46 cm
  (installed -0.53), Dead LOD3 -0.69 (installed +0.36); faces stretched > 20x: 3 / 1 / 1 / 1 (installed 3 / 3 / 1 / 1).
- Viewer: `run_creature_review.py check` 126 switches, 0 failed, 0 console errors.

## Review
Viewer (installed and reduced per tier with halberd and plate attached, all 21 clips):
http://127.0.0.1:8912/level_generation/creatures/mm9_guard_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_e55.png` (front close-up, 3/4, profile, low 3/4, party; every tier), `review/sheet_face_diff_e55.png`,
`review/sheet_body_e55_{a,b,c}.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/close_e55_{a,c}.png` (arms,
skirt front/back, Running skirt, feet, AttackMelee2 arms, shoulders from behind, Cower, head 3/4 and back), `review/ladder_sheet_{a,b}.png`.
Earlier candidates' sheets: `review/sheet_*_{b55,d55}.png`, `review/close_b55_*.png`.
Look at: the helmet crown and sides at 0.6 (the projected helmet paint; the face and the plates' surroundings are exact), the
shoulders and the tunic's quilting at 3/4, the left fist (hands at 0.65).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
$BL -P scripts/dump_final_parts.py                       # part/lining/head/hand/pole labels of ../mm9_guard_claude/work/final_v1.blend
REA_GLB=level_generation/creatures/mm9_guard_reduce_claude/before/mm9_guard.glb REA_NODE=Guard $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
$G scripts/merge_halberd.py before/mm9_guard.glb before/mm9_guard_halberd.glb work/gate_before.glb
$G scripts/grip_contact.py; $G scripts/contact.py
GAUNTLET=1 SMALL=80 $G scripts/make_sets.py e; $G scripts/glb_sets.py e; $G scripts/lining_match.py e --write
SETS=e MP_GROUPS=1:0.65,2:0.6,3:1.0,4:0.55,5:0.6 scripts/run_mp.sh e 0.55,0.52     # mpqem -> reduce_ladder (error, renders) -> compare
scripts/build_mp.sh mp_e_r55 export/mm9_guard.glb       # swap_mp -> build_lods (soles, crown, corpse contact) -> shrink_shadow_lods -> carry_variants -> check_winding
scripts/gates.sh export/mm9_guard.glb e55; python3 scripts/gate_compare.py e55
$G scripts/viewer_tiers.py export/mm9_guard.glb red; scripts/shots.sh; python3 scripts/shot_sheets.py e55; scripts/close_shots.sh
```
Install (on the user's OK only): `check_winding.py export/mm9_guard.glb` (0), `tools/install_model.py export/mm9_guard.glb --world mm9`
(the attachments are unchanged and need no install), the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_guard_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_guard_reduce_claude`; a rebuild from this project must
re-run that reduction". Rollback: `before/mm9_guard.glb`.

## Not checked
In game; motion at normal speed by eye (frames, gates and viewer stills only); the fists in a close-up (grip gate numbers and
distance-framed viewer shots only); LOD1-3 and shadow meshes by eye (numbers only); tier B in close-ups (face and body sheets only).
Many scripts in `scripts/` are copies from `mm9_highwayman_reduce_claude/` that this route did not use (MeshLab ladder tools).
