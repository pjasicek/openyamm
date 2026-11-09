# MM9 Troglodyte (`mm9_troglodyte`, Troglodyte / Wren / Gnoll) reduction: candidate d55 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 46 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:troglodyte` (owner troglodyte-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_troglodyte.glb` (sha256 40b9d4b824d7, identical to
`../mm9_troglodyte_claude/export/mm9_troglodyte.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no
repaint. **Not installed.** `../mm9_troglodyte_claude/` was only read.

| | LOD0 | body (Trog) | head (TrogHead) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 12,010 | 6,252 | 5,758 | 5,996 | 2,157 | 879 |
| **d55 (`export/mm9_troglodyte.glb`, sha256 ad0a8ab44292)** | **9,926 (-17.4 %)** | 4,168 | 5,758 | 4,955 | 1,783 | 830 |

The head primitive (face skin, eyes, mouth, palate, tongue, teeth, neck strip) is byte-identical on LOD0: same accessors. Every
body vertex is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index buffers changed).
Clips, skin, nodes, sockets, materials, region masks, ramps, `KHR_materials_variants`, all 12 images: byte-identical (`same_clips.py`).

## Measured first: protected share
The head primitive is 48 % of LOD0 and stays exact, so the cut can only come from the body (6,252, already reduced at the
build). Kept exactly on the body (`scripts/trog_sets.py`, `scripts/pierce_keep.py`): the neck seam (body faces within 3 cm of
a head vertex), soles (1.5 cm), claws (region-mask blue: 238 faces, fingers and toes), the six calf spines (pieces of 15 faces),
and (set d) 604 faces where the head or jaw passes through the torso in the installed clips (3 cm round each pierce point,
mirrored) plus the head-weighted skin of the neck band. Protected share 58.4 %. Hands (every finger kept) are their own group
at 0.7; below that the collapse is refused (texture guard / flip checks: asking 0.6 still gave 767).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Highwayman's copy)
Scored over 280 poses (every clip at 10 Hz) plus a position+UV rest quadric; only removes vertices. The texture guard reads,
per tier, tier A's region mask (ribs, claws: a moved rib/claw edge is refused), the B colour and the C colour
(`scripts/tex_extract.py`). No linings on this body.

## Ladder (height 1.2 m: p99 <= 3.6 mm, max <= 18 mm; `review/ladder_sheet_{a,b,c,d}.png`)
| set | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | base keep set, hands 0.7 | r65 / **r55** / r45 | 10,142 / 9,702 / 9,262 | 2.28/9.3, 3.19/12.0, 5.19/19.3 (Death) | .996/.997, .994/.995, .990/.991 | pass / pass / fail |
| b | a, hands 0.6 | r52 / r48 | 9,570 / 9,393 | 3.60/13.8, 4.35/21.3 | | fail (limit) / fail |
| c | a + every body face within 1 cm of the head in any pose (832) | r50 / r45 | 9,824 / 9,652 | 4.61/21.3, 11.1/47.7 | | fail / fail |
| **d** | a + head/jaw pierce faces (604) | **r55** / r50 | **9,926** / 9,732 | **3.23/12.0 (Dead:0)**, 4.14/21.3 | **.994/.995** | **PASS, picked** / fail |

a55 (-19.2 %) passed the ladder but raised the jaw into the torso in AttackMelee2 (1.3 -> 2.5 cm) and the leg into the tail in
Death; d55 brings those back to the installed values for 224 triangles (gates `review/gates_a55/`).

## Gates, installed -> d55 (`scripts/gates.sh`: the Troglodyte's own scripts; `review/gates_before/`, `review/gates_d55/`)
- Collapse (bind reference): face-frames 39,051 -> 35,370; no region's worst-frame count rises in any clip (knees 5-11 -> 2-5).
  The open-mouth-reference collapse gate cannot run: `../mm9_troglodyte_claude/work/head_ref.npz` has 5,798 head faces, the
  installed head 5,758 (stale since the chest fix), on the installed file too; the head is byte-identical anyway.
- Arm/hand (`--outer-only --exact`): every value equal or lower (AttackMelee2 L hand 3.1 / forearm 3.3 cm as installed; Hit2 R
  hand 0.3 -> 0.1 cm); finger stretch p99/max equal or lower.
- Pierce: tail/leg pairs equal or lower (Walking leg-in-tail 22 -> 11 frames, Death 4.5 -> 3.2 cm); jaw in torso equal.
  **Head in torso slightly worse:** Fidget2 0.6 cm 0 f -> 1.2 cm 5 f, AttackMelee 0.0 -> 0.8 cm (0 f > 1 cm), AttackMelee2 0.3 ->
  0.5 cm, Fidget 8 -> 9 frames (2.5 cm both); the installed model's worst stays worst (AttackRanged 6.1 cm, Hit2 5.5 cm).
- Jitter vs MM9's raw keys: 1 fail both (Death L shoulder skin 10.31 -> 10.14 mm/f2).
- Detached 0 (43 components), bone length 0 stretching, winding 0, flat shading 0.03 -> 0.00, texture quality: body atlas 56.9 %
  unchanged, stretch p90 1.22 -> 1.25, head unchanged.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,d55}.json`), built by
  `scripts/build_lods.py` (tools/build_actor_lods.py defaults with protected points: soles, the top of the back, the corpse contact
  of Death/Dead, the claw tips of every finger and toe and the rest-pose extremes). Rest bounds identical at every LOD (installed
  LOD3 lost 3.5 cm of finger width each side; without the tip points the first build lost 9 cm of right claws on LOD3); lowest
  point per clip equal to LOD0 at every LOD (installed LOD3 Death -1.0 cm); faces stretched > 20x: LOD0 as installed, LOD3
  AttackMelee2 3 (installed 2), Hit2/AttackRanged 1 (installed 0). Death2 ends with the head 15 cm under the floor in the
  installed clip (not ground-fixed by its build; clips unchanged here).

## Review
Viewer (installed and reduced, every tier, 18 clips; `run_creature_review.py check`: 108 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_troglodyte_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_d55.png` (front close-up, 3/4, profile, low 3/4, party; every tier),
`review/sheet_face_diff_d55.png` (|difference| x4: the head black in every view and tier, only body pixels differ),
`review/sheet_body_d55_c.png`, `review/sheet_close_d55_a.png` (arms, back, feet, AttackMelee2, Hit chest, Dead, Running),
`review/sheet_close_d55_{b,c}.png` (back and Hit chest of B, back and AttackMelee2 of C, `work/crop_close_d55_bc.png`), and of the
first candidate a55 `review/sheet_body_a55_a.png`, `review/sheet_close_a55_{a,b,c}.png`, `review/ladder_sheet_a.png`. No visible change found. Look at: the shoulder hump in profile and the chest under the jaw in Hit
(larger triangles shade a little differently), the claws (kept exactly).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_troglodyte_reduce_claude/before/mm9_troglodyte.glb REA_NODE=Troglodyte $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/pierce_keep.py 0.03
SOLE=0.015 $G scripts/trog_sets.py d pierce
SETS=d MP_GROUPS=1:0.7 scripts/run_mp.sh d 0.55,0.5            # mpqem -> reduce_ladder (error over every clip) -> compare
scripts/build_mp.sh mp_d_r55 export/mm9_troglodyte.glb          # swap_mp -> build_lods (protected) -> shrink_shadow_lods -> carry_variants -> fix_winding
scripts/gates.sh export/mm9_troglodyte.glb d55; REA_NODE=Troglodyte $BL -P scripts/lod_check.py -- $PWD/export/mm9_troglodyte.glb d55
$G scripts/viewer_tiers.py export/mm9_troglodyte.glb d55; scripts/shots.sh; $G scripts/shot_sheets.py d55
```
Install (on the user's OK only): `check_winding.py export/mm9_troglodyte.glb` (0), `tools/install_model.py
export/mm9_troglodyte.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_troglodyte_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_troglodyte_reduce_claude`; a rebuild from
this project must re-run that reduction". Rollback: `before/mm9_troglodyte.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the body sheets of tiers A and B for d55 and the rest of the d55 close rows of B and C (written, read for a55);
indoor light; Android.
