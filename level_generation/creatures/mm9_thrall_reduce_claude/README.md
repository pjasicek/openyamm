# MM9 Thrall (`mm9_thrall`, Field Thrall / Thrall / Thrall Master) reduction: candidate h65 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 63 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:thrall` (owner thrall-reduce-20261104); the
creature's own `mm9:thrall` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_thrall.glb` (sha256
f01a6779a95f, identical to `../mm9_thrall_claude/export/mm9_thrall.glb`), copied to `before/` (the rollback source). No Meshy, no
credits, no repaint. **Not installed.** `../mm9_thrall_claude/` was only read.

| | LOD0 | limbs (Thrall_A) | torso (ThrallTorso) | head (ThrallHead) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 9,517 | 3,990 | 1,969 | 3,558 | 4,757 | 1,708 | 564 |
| **h65 (`export/mm9_thrall.glb`, sha256 dd3e173be7ba)** | **7,741 (-18.7 %)** | 2,634 | 1,631 | 3,476 | 3,869 | 1,386 | 470 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (15), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 18 images: byte-identical
(`same_clips.py`). Face skin, eyes and the head-set skin bridge are the installed triangles: every tier's face renders
pixel-identical (`review/sheet_face_diff_h65.png`: face black in all five views of all three tiers; only hair sides, collar edge
and shoulders differ).

## Measured first: protected share
Part labels from the finished master `../mm9_thrall_claude/work/uv_v3.blend` (`scripts/dump_final_parts.py` -> `glb_parts.py`,
mapped to the Nobleman codes make_sets uses). The head set is 2,777 face skin (face, ears, jaw, neck down to the bridge), 120 eyes,
640 hair shell, 21 bridge: the face alone is 29 % of LOD0. Set a (40.3 % kept): face skin, eyes, bridge, belt + knot + rope ends
(360, thin painted rope), sandal soles (185), the hand-graft junction (204), the hairline (171 hair faces within 8 mm of face skin),
pieces of up to 60 faces. Set c (final, 48.4 %) adds the shoulder skin (667 faces with a Clavicle/UpperArm-dominated vertex: b75
without it raised the jitter shoulder term R AttackMelee 0.5 -> 3.83, AttackMelee3 2.25 -> 6.05, Hit2 5.08 -> 9.77 mm/f2) and the
hand contact of Fidget2 and Hit2 (97 more faces: hair under the L hand in Fidget2, `scripts/gate_keeps.py`, R 3 cm).
Groups: hands 0.5 (every finger, seam slides), hair 0.8, skirt 0.7 (eight `Skirt_*` hinges), sandals 0.6 above the soles; body skin,
tunic/pelt torso and collar take the ladder ratio. No linings, no weapon (the knife is thrown, nothing in the hand).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)
The Lesser Demon's copy (seam slides, `MP_SEAM_GROUPS=1` on the hands) with the Nobleman/Highwayman texture guard over all three tiers
(limbs: the shared image; torso and head: each tier's colour; refuse at > 100 any sample / > 45 mean). Scored over every clip at
10 Hz plus a position+UV rest quadric. Without seam slides the MPFB hands stopped at 694 of 1,324 free faces (finger UV seams).

## Ladder (height 1.795 m: p99 <= 5.38 mm, max <= 26.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / groups (hands, hair, skirt, sandals) | step | LOD0 | p99 / max mm (worst) | |
|---|---|---|---:|---|---|
| a | a / .65 .65 .7 .6 | r60 / r50 | 7,455 / 7,173 | 6.19/20.4 (Running, L knee), 11.4/40.6 | fail / fail |
| b | a / .5 .6 .6 .6 | r75 / r70 / r65 | 7,617 / 7,471 / 7,329 | 5.27/14.9, 5.59, 6.03 | pass / fail / fail |
| (b75 built) | | | 7,617 | gates: jitter shoulder R worse (above), hair 0.6 left a dark sliver on the bald crown (tier A) | rejected |
| c | c / .5 .8 .7 .6 | r70 / r65 | 7,871 / 7,773 | 4.95/17.7, 5.45 | pass / fail |
| d | c + error lock (21 vertices > 12 mm, 2 cm) | r65 / r60 | 7,875 / 7,783 | 5.14, 6.11 | pass / fail (lock only moves the error) |
| f | c + seam slides, hands .35 | r70 / r65 | 7,639 / **7,541** | 4.65, 5.15 | pass / pass; built as `work/alt_f65.glb`: fingers visibly faceted in close-up (`review/close_f65_a_hands.png`), rejected |
| g | f, hands .25 | r65 / r62 | 7,409 / 7,353 | 5.79, 6.09 | fail |
| **h** | c + seam slides, hands .5 | r68 / **r65** | 7,797 / **7,741** | 4.78, **5.06/20.4 (Running:21)** | pass / **PASS, picked** (IoU .9935, SSIM .9957) |

The body (limbs and torso skin) was already cut at the build (`reduce_thrall.py`); its error spreads evenly over calves, spine and
upper arms and fails at about 0.65 whatever is locked. The rest of the saving comes from the dense MPFB hands (1,324 -> 662 free).

## Gates, installed -> h65 (the Thrall's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_h65/`, `review/gates_compare_h65.txt`)
- Collapse face-frames 6,176 -> 5,737, equal or lower in every clip; worst-frame counts lower almost everywhere (knees 0, body down);
  up: groin_R 0 -> 1 in Hit2 and Death.
- Jitter vs MM9's untouched clips: output identical, 13 fails both (the installed model's own, measured on the runtime GLB; the
  creature README's 0 was measured on `thrall_final_clips.glb`).
- Arm/hand (outer and skin-only): identical except Walking R hand into a skirt flap 1.6 -> 0.9 cm (3 -> 0 frames over 1 cm);
  finger stretch maxima equal or lower.
- Skirt (`skirt_gate2.py`): small changes, all under 1 cm: AttackMelee3 0 -> 4/98 frames 0.7 cm, AttackRanged 0.1 -> 0.6 cm (3 f),
  AttackMelee 0.3 -> 0.4 cm (4 f), Death 0.2 -> 0.4 cm, Fidget 0.0 -> 0.1; better: Fidget2/Taunt 12 -> 1 frames (0.6 -> 0.7 cm),
  Hit2 3.0 -> 2.8 cm, Death2 15.1 -> 14.2 cm.
- Bone lengths identical; winding 0; flat shading 0.00; detached 0 (19 components; skirt root lift p90 9.0 -> 9.8 cm, AttackMelee).
  Texture quality: limbs stretch p90 1.07 -> 1.10, fragments 0.2 -> 0.4 %; torso 1.17 -> 1.19; head 1.14 -> 1.15.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,h65}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected, each point snapped to the imported vertex):
  height 1.794 m at every LOD (installed LOD2/3 1.801); every clip's lowest point equal to LOD0 at every LOD (Standing -0.1 cm,
  Dead 0, Death -0.48, Death2 -0.53 cm; installed LOD3 floated +0.4 cm standing and +1.8 cm dead); stretched faces 1/0/0/0 (as installed).

## Review
Viewer (installed and reduced, every tier, all 15 clips; `run_creature_review.py check`: 90 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_thrall_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_h65.png` (front close-up, 3/4, profile, low 3/4, party; every tier), `review/sheet_face_diff_h65.png`,
`review/crop_headband_h65_b.png` (tier B's painted headband on the hair shell, full size), `review/sheet_body_h65_{a,b}.png`,
`review/close_h65_{a,c}_hands.png` (R hand outside, L hand outside, R hand front), `review/close_h65_{a,c}_1.png` (arms, skirt
front/back, Running skirt), `review/close_h65_c_2.png` (sandals, AttackMelee2 arms, shoulders from behind, Hit2, hair from behind),
crown crops `work/_crown.png` (b75, dark sliver) and `work/_crown_f65.png` (hair 0.8: clean). Look at: the L hand fingertips in
close-up (c9: a slightly more angular middle fingertip), the bald crown of tier A (hair shell at 0.8), the skirt hem in AttackMelee3.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
$BL -P scripts/dump_final_parts.py                    # part labels of ../mm9_thrall_claude/work/uv_v3.blend
REA_GLB=level_generation/creatures/mm9_thrall_reduce_claude/before/mm9_thrall.glb REA_NODE=Thrall $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
HAIRLINE=0.008 SOLE=0.012 $G scripts/make_sets.py a; $G scripts/glb_sets.py a
SHOULDER=1 CONTACT=1 CLIPS=Fidget2,Hit2 R=0.03 $G scripts/gate_keeps.py a c
MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.5,2:0.8,3:0.7,4:0.6 scripts/run_mp.sh h 0.68,0.65
SOLE=0.012 scripts/build_mp.sh mp_h_r65 export/mm9_thrall.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
scripts/gates.sh export/mm9_thrall.glb h65; $G scripts/gate_compare.py h65
REA_NODE=Thrall $BL -P scripts/lod_check.py -- $PWD/export/mm9_thrall.glb h65
$G scripts/viewer_tiers.py export/mm9_thrall.glb h65   # ramps baked for three.js
scripts/shots.sh; $G scripts/shot_sheets.py h65; $G scripts/face_diff_sheet.py h65; scripts/close_shots.sh; $G scripts/close_sheet.py h65 a c8,c9,c10 review/close_h65_a_hands.png 520
```
Install (on the user's OK only): `check_winding.py export/mm9_thrall.glb` (0), `tools/install_model.py export/mm9_thrall.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_thrall_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_thrall_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_thrall.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); tier B close-ups other than the head (face and body sheets
only); the knife release from `throw_hand` (sockets and clips are byte-identical).
