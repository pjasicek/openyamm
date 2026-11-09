# MM9 Highwayman (`mm9_highwayman`, Cutpurse / Burglar / Bandit) reduction: candidate m4 r57 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 28 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:highwayman` (owner highwayman-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_highwayman.glb` (sha256 1923e3d405f8, identical to
`../mm9_highwayman_claude/export/mm9_highwayman.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no
repaint. **Not installed.** `../mm9_highwayman_claude/` was only read.

| | LOD0 | limbs set | torso set | head set | weapons | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 13,094 | 4,856 | 3,650 | 3,928 | 660 | 6,544 | 2,353 | 781 |
| **m4 r57 (`export/mm9_highwayman.glb`, sha256 2034c3caf80f)** | **9,916 (-24.3 %)** | 3,334 | 2,430 | 3,492 | 660 | 4,954 | 1,781 | 588 |

Every vertex of the candidate is an installed vertex: positions, normals, UVs, joints and weights are the installed bytes (only
index buffers changed). Clips, skin, nodes, sockets, materials, `KHR_materials_variants`, all 21 images: byte-identical
(`same_clips.py`). Face skin, neck and eyes: the installed triangles, so every tier's face renders pixel-identical
(`review/sheet_face_diff_m4r57.png`: face and neck black in all five views of tiers A and C).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, from `mm9_banshee_reduce_claude`)
The MeshLab texture-aware ladder (playbook default) was tried first and stopped at about -21 %: with the linings dropped and
rebuilt (ladder a) r72 10,308 passed (p99 3.19, max 14.1 mm); r68 failed on the groin in Death2 (34.6 mm, `Thigh_h` half-joint
vertices); keeping every face the twelve `*_h` helpers weight >= 0.5 (ladder b) only moved the error (r69 p99 5.96 fail).
`mpqem.py` scores each collapse over 298 poses (every clip at 10 Hz) plus a position+UV quadric and only removes vertices.
Changes for the Highwayman:
- sets per GLB face from `make_sets.py` -> `glb_sets.py`; each primitive cut per group on its own (group borders stay);
- **linings** (finish_hw's 3 mm inner copies: skirt, yoke rim, boot flares, sleeve ends; 1,120 faces) are not cut: the border
  of the lined outer region is locked, and the lining is re-emitted as the reversed faces of each surviving lined outer face's
  twin vertices (twin = the lining vertex at outer - 3 mm x the lined faces' area-weighted normal, finish_hw's own rule;
  predicts every lining vertex to 0.00003 mm). Lining 1,120 -> 868; open edges equal to the installed (1,826);
- **texture guard** (`tex_ok`): a collapse is refused when its new faces sample a blurred base colour (any of the three tiers)
  that differs from the source at the same rest point by > 100 at one sample or > 45 on average. Without it (ladder m2) a
  merged face put a dark wedge on the right bracer (`review/close_a_2.png`, red_a c5) and stepped the belt's lower gold edge.

Keep set (`scripts/make_sets.py`, prio-1 relaxed): exact face skin (part 20), neck (2, the seam), eyes (22), both weapons (660,
already lean procedural pieces), soles (boot faces within 3 cm of the floor), the hand-graft junction (two face rings from the
MPFB wrist opening), the grip contact (597 hand faces within 1.5 cm of a weapon at 6 times of every clip, `grip_contact.py`),
the hairline (hair faces within 6 mm of face skin), the belt (thin painted gold trims) and pieces of up to 60 faces.
Groups: hands 0.65 (every finger kept), hair shell 0.65, skirt outer shell 0.7 (on the eight `Skirt_*` hinges), boots above
the soles 0.6; the rest (tunic, pants, yoke, flares, straps) takes the ladder ratio.

## Ladders (limits for 1.855 m: p99 <= 5.57 mm, max <= 27.8 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a (MeshLab, relined) | hands/hair .7, skirt .75, boots .7 | r72 / r68 / r64 | 10,308 / 9,751 / 9,164 | 3.19/14.1, 4.03/34.6 (Death2), 5.99/42.9 | .995/.996 ... | pass / fail / fail |
| b (MeshLab) | a + helper faces kept | r72 / r69 | 10,222 / 9,782 | 4.14/16.1, 5.96/25.2 | | pass / fail |
| m1 (mpqem) | groups as a | r60 / r50 | 10,148 / 9,746 | 3.43/14.3, 10.8/45.7 | .996/.996 | pass / fail |
| m2 (mpqem) | hands/hair .65, skirt .7, boots .6 | r57 | 9,788 | 4.54/19.2 | .994/.995 | pass; bracer wedge, belt steps |
| m3 | m2 + 2 cm drift lock | r50-r40 | 10,124 | 9.4/45.4 | | stuck, fail |
| **m4** | m2 + texture guard + belt kept | **r57** / r54 / r51 | **9,916** / 9,808 / 9,740 | **4.74/25.5 (Dead:0, armpit)**, 5.96/27.0, 8.07/45.4 | **.994/.995** | **PASS, picked** / fail / fail |

## Gates, installed -> m4 r57 (the Highwayman's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_m4r57/`, `review/gates_compare_m4r57.txt`)
- Collapse face-frames 26,046 -> 17,972, lower in every clip; worst-frame counts lower almost everywhere (Death armpit L 43 -> 18,
  AttackRanged armpit L 25 -> 3); up by one face: Running knee_R 1 -> 2, Death groin_R 0 -> 1, armpit_R 2 -> 3 in Walking/Backpedal.
- Skirt gate: identical in every clip. Arm/hand (outer and skin-only): Fidget2 R 0.7 -> 0.5, JumpingDown L 1.0 -> 0.9, Death L
  0.0 -> 0.1, Backpedal forearm L 0.0 -> 0.1 cm; finger stretch p99 max equal or lower except Dead L 1.20 -> 1.22.
- Grip: inside the grip at most 0.3 cm both (same); wrap per finger min 150 / median 195 deg both (single-finger samples drop one
  15-deg bin with fewer finger vertices). Blades: sword unchanged; dagger Fidget2 1.4 cm (3 f) -> 1.3 (2 f), Dead 0.8 -> 0.7.
- Jitter 7 fails before and after (clips identical). Bone lengths 0 stretching. Winding 0. Flat shading 0.00. Detached parts 0
  (36 components). Texture quality: limbs stretch p90 1.16 -> 1.19, torso/head/weapons unchanged.
- LODs (`lod_check.py`, every frame of every clip; `work/lod_check_{installed,lodp2}.json`): built with the floor contact, crown and
  corpse contact as protected points (`scripts/build_lods.py`). Height 1.8544 m at every LOD (installed 1.8547 / 1.8547 / 1.8536
  / 1.853); Standing lowest point 0 at every LOD (installed LOD2/3 +0.2/+0.35 cm); Dead 0 at every LOD (installed LOD3 -1.5 cm);
  Death -1.7 / -1.7 / -1.3 / -1.3 cm (installed -1.7 / -1.7 / -1.9 / -2.0); faces stretched > 20x: 3 / 1 / 2 / 1 (installed 3/1/1/1).

## Review
Viewer (installed and reduced, every tier, all 23 clips; `run_creature_review.py check`: 138 switches, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_highwayman_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_m4r57.png` (front close-up, 3/4, profile, low 3/4, party; every tier), `review/sheet_face_diff_m4r57.png`,
`review/sheet_body_m4r57_{a,b,c}.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/close_m4r57_{a,c}_{1,2}.png`
(fists, skirt front/back, Running skirt, boots, AttackRanged arms, shoulders from behind, Cower), `review/crop_bracer_belt_m4r57_{a,c}.png`,
`review/ladder_sheet_m4.png`. Look at: the bracers up close (pattern reads slightly softer: larger triangles interpolate the
normal-map tangent frame differently), fists (hands at 65 %), hair at the nape.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$BL -P scripts/dump_final_parts.py                       # part/lining labels of ../mm9_highwayman_claude/work/final_v1.blend
REA_GLB=level_generation/creatures/mm9_highwayman_reduce_claude/before/mm9_highwayman.glb REA_NODE=Highwayman $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; G=../claude_shared/gltf_venv/bin/python
$G scripts/glb_parts.py; scripts/cap.sh $G scripts/grip_contact.py; HAIRLINE=0.006 $G scripts/make_sets.py a
$G scripts/tex_extract.py; python3 scripts/make_set_e.py; python3 scripts/glb_sets.py e
SETS=e scripts/run_mp.sh m4 0.57,0.54,0.51               # mpqem (MP_GROUPS 1:0.65,2:0.65,3:0.7,4:0.6; guard 100/45) -> ladder -> compare
SOLE=0.012 scripts/build_mp.sh mp_m4_r57 export/mm9_highwayman.glb   # swap_mp -> build_lods (protected) -> shrink_shadow_lods -> carry_variants -> fix_winding
scripts/gates.sh export/mm9_highwayman.glb m4r57; python3 scripts/gate_compare.py m4r57
```
Install (on the user's OK only): `check_winding.py export/mm9_highwayman.glb` (0), `tools/install_model.py
export/mm9_highwayman.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_highwayman_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_highwayman_reduce_claude`; a rebuild from
this project must re-run that reduction". Rollback: `before/mm9_highwayman.glb`.

## Not checked
In game; motion at normal speed by eye (frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only);
the Burglar tier in close-ups (body and face sheets only); weapons not rebuilt (660 triangles, already low-poly procedural
lathes and facets; a rebuild would save at most ~300).
