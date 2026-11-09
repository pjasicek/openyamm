# MM9 Njam the Meddler (`mm9_njam`) reduction: candidate b r50 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (relaxed keep set, face exact;
prio-3 unique, user 2026-11-05 "do all"), ledger row 52 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:njam`
(owner njam-reduce-20261105); the creature's own `mm9:njam` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_njam.glb` (sha256 82618f64547f, identical to `../mm9_njam_claude/export/mm9_njam.glb`), copied
to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_njam_claude/` was only read (its
`final_v1.blend` opened read-only for the part/lining labels; its gate scripts run in place).

**Skins:** the GLB has one skin and no `KHR_materials_variants`. The freeze skins NJAM1-7 and the statue skin NJAMSCULPT were never
built (creature README, "Script events"; the statue is the separate decoration `mm9_deco_njamstatue`, not touched), so there is no
tier to carry; all 9 images, the 3 materials and the 49 clips (incl. the scripted WinGame/NjamPose/Twitch/Frozen/Statue) are identical.

| | LOD0 | limbs (Njam: hands, hose, boots) | torso (NjTorso: coat, skirt + lining, belt, buckles) | head (NjHead: skin, hair, lip) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 11,053 | 3,385 | 3,150 | 4,518 | 5,525 | 1,987 | 663 |
| **b r50 (`export/mm9_njam.glb` = `export/mm9_njam_b50.glb`, sha256 9e76b6e76145)** | **8,839 (-20.0 %)** | 2,235 | 2,488 | 4,116 | 4,418 | 1,587 | 528 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Exact (`scripts/exact_face.py`, 0 missing): the whole head skin (part 20: face, ears, scalp, neck tube; 2,742),
the hair lip (23: the rolled rim's underside, 288), belt (42) and buckle/brooch pieces (168), and every face of the keep set; the face
renders pixel-identical (`review/sheet_face_diff_b50.png`: face black in all five views; only the hair shell and the coat/fur below
the collar differ).

## Measured first: protected share
Part labels from `../mm9_njam_claude/work/final_v1.blend` (`scripts/dump_final_parts.py`, `glb_parts.py`, centroid match 6e-8 m):
0 MPFB hands 1,519, 1 coat 2,016, 5 hose 734, 6 boots 1,132, 7 skirt 924 (446 outer + finish_nj's 446 lining + 32 cap), 9 belt 42,
10 buckles 168, 20 head skin 2,742, 21 hair helmet 1,488, 23 hair lip 288. Head skin + lip + belt + buckles + cap = 30 %; a 15 % cut
was in reach, so the ladder ran.

Keep set b (`scripts/make_sets_nj.py b`, 46 % exact): head skin, lip, hairline (hair faces within 15 mm of a lip vertex), belt,
buckles, cap, soles (boot faces within 12 mm of the floor), the hand-graft junction (2 rings), the neck seam (body faces within 15 mm of
the head set), shoulder skin (faces with a Clavicle/UpperArm-dominated vertex, the jitter gate's term), **the skirt whole** (a cut skirt
let a crotch vertex read 6.5 cm through it in CowerLoop: skirt gate 0.6 -> 6.5 cm at a50; 315 of the 446 skirt faces come within 3 cm of
a leg in some pose, `scripts/skirt_contact.py`), **fingertips** (faces wholly on a distal finger bone, `scripts/fingertips.py`: a50 lost
the painted nail ends), the Pray palm contact (faces within 2 cm of the other hand at 48 fps: a50 L hand 0 -> 1.7 cm into the R hand).
Groups: hands 0.65 (every finger), hair 0.7 (hairline exact), boots 0.6, hose 0.5, coat at the ladder ratio. Linings: finish_nj's
skirt lining is re-emitted as the reversed twins of the surviving skirt faces (twin residual 0.00 mm); with the skirt kept it equals the
installed lining.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)
PeasantM3's `Prim` (chart guard `MP_CHART=1` at 12 subdivisions, the audit's own chart test `MP_AUDIT=1`, seam slides, texture weight
`MP_W5=4`, texture guard over each primitive's own base colour at 100 / 45) with the Nobleman/Highwayman main (three primitives,
the Highwayman's lining twins: finish_nj.py is finish_hw.py's lining). Scored over 1,444 poses (all 49 clips at 10 Hz) plus a
position+UV rest quadric.

## Ladders (limits for 1.82 m: p99 <= 5.46 mm, max <= 27.3 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / change | step | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | base + shoulder skin | r60 / r50 / r45 | 8,599 / 8,465 / 8,399 | 3.53, 4.44 / 22.35 (PlayGetup:39), 6.68 / 26.65 | pass / pass / fail. a50 built: skirt gate Cower 0.6 -> 6.5 cm, fingertip nails lost, Pray L hand 0 -> 1.7 cm |
| **b** | **a + skirt whole + fingertips + Pray contact** | r55 / **r50** | 8,907 / **8,839** | 3.67, **4.39 / 22.35 (PlayGetup:39)** | **PASS, picked** (IoU .9950, SSIM .9962) |
| c | b + installed faces under b50's collapsing cut faces (`scripts/collapse_keep.py`, 173) | r55 / r50 | 8,985 / 8,923 | 4.59, 5.57 / 33.83 (PlayGetup:18) | fail: the hose (0.5) had to take costlier collapses (worst 1.7 -> 3.5 mm rms). Third ladder: stop. |

## UV chart audit (hard gate)
`review/uv_audit_b50.json`: **0 escaping LOD0 faces in all three primitives**. LOD1-3 (Blender decimate, as installed) limbs 124 / 122 /
65, torso 76 / 84 / 39, head 80 / 92 / 38 against installed 112 / 100 / 77, 62 / 98 / 48, 76 / 98 / 53.

## Gates, installed -> b r50 (`scripts/gates.sh`: Njam's own scripts, read in place; `review/gates_before/`, `review/gates_b50/`, `review/gates_compare_b50.txt`)
- Skirt (hose through the outer skirt): equal or better in every clip (Cast 29 f 1.3 -> 24 f 1.2 cm, BarFidget 70 -> 56 f at 2.0 cm,
  PlayGetup 46 -> 37 f at 10.2 cm, every other clip 0-0.4 -> 0-0.3 cm; partly fewer hose vertices measured).
- Arm/hand (`--outer-only --exact`, 48 fps) and skin-only: equal or better except Conv1 L hand 3.2 -> 3.4 cm (frames over 1 cm equal) and
  Bow R frames over 1 cm 35 -> 36 (depth 5.3 -> 5.2). Better: AttackMelee R 1.0 cm 1 f -> 0.8 cm 0 f, Cast R forearm 5.0 -> 4.5, Fidget8 L
  forearm 4.1 -> 3.1. Finger stretch maxima equal or lower; p99 up 0.04-0.12 in Fidget L/R, BarDrink L, BarStand L, Fidget4 L.
- Collapse face-frames 86,149 -> 80,834: lower in 41 clips, equal in 7, higher only in PlayGetup (3,687 -> 3,694). **Worst-frame region
  counts up**: knees 0 -> 1-3 in 12 clips (Running, AttackRanged, Kick, AttackMelee2, Run2, Fidget5, PlayGetup, Bow, Hit2, Cower x3),
  torso +1/+2 in 9 clips (Cast 5 -> 6, Pray 4 -> 6), SpellAttack elbow/shoulder R +1, AttackMelee hip L 2 -> 3, PlayGetup hip R / groin
  +1. Seen-from-any-camera totals lower or equal in most of them (Cast 52 -> 38, Cower 29 -> 22; up: Running 13 -> 14, Kick 28 -> 32).
  The knee faces are the hose end inside the boot's fur cuff: `review/close_b50_knees.png` (Running front/side, Fidget5, Kick at the
  gate's worst frames) shows no difference. Ladder c tried to keep them and failed the error limits.
- Jitter vs `../mm9_njam_claude/work/nj_clips0.glb`: 12 fails both (the installed export's own, after floor_fix; identical output).
- Orient, same_clips: identical. Lining through the skirt: equal or lower (Fidget 37.2 -> 26.8 mm, Bow 34.7 -> 26.7 mm max out).
- Detached 0 both (11 components; root lifts lower). Flat shading 0.00/0.01/0.00. Winding 0. Bone lengths 0 of 12 stretching.
  Texture quality: unchanged (limbs stretch p90 1.27 -> 1.29, torso 1.09 -> 1.10).
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,b50}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and the Death/Dead/PlayDeath floor contact protected, snapped): height
  1.801 m at every LOD; Standing and Dead lowest point 0.0 at every LOD (installed LOD3 floated +0.9 cm standing, +2.0 cm in Dead);
  0 stretched faces at LOD1-3 (LOD0 4 both).

## Review
Viewer (installed and reduced, all 49 clips; `run_creature_review.py check`: 98 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_njam_reduce_claude/review/viewer/
Sheets read (full size): `review/sheet_face_b50.png` (front close-up, 3/4, profile, low 3/4, party), `review/sheet_face_diff_b50.png`,
`review/sheet_body_b50_nj.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/close_b50_hands.png` (both hands outside,
R hand front: every finger, nail ends back), `review/close_b50_arms.png`, `review/close_b50_skirt.png`, `review/close_b50_feet.png`,
`review/close_b50_hair.png` (back and profile), `review/close_b50_knees.png`, crops `work/crop_throat_b50.png`, `work/crop_yoke_b50.png`;
for a50 `review/close_a50_*.png`, `work/crop_c9_hem_a50.png`, `work/crop_chest_f{0,3}_a50.png`.
Look at: the fur collar and the round chest medallion (paint on the coat: shading of the larger chest faces differs a little), the back
fur yoke's lower edge (slightly straighter), the knuckles (hands 0.65), the hair helmet from behind (0.7, hairline exact).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_njam_reduce_claude/before/mm9_njam.glb REA_NODE=Njam $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/dump_final_parts.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/fingertips.py
HAIRLINE=0.015 SHOULDER=1 $G scripts/make_sets_nj.py a        # glb_sets_a also feeds lining_gate.py (installed lining faces)
HAIRLINE=0.015 SHOULDER=1 SKIRT=0 CONTACT=1 CLIPS=Pray R=0.02 FPS=48 EXTRA=work/fingertips.npy $G scripts/make_sets_nj.py b
SETS=b MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 MP_GROUPS=1:0.65,2:0.7,3:0.7,4:0.6,5:0.5 scripts/run_mp.sh b 0.55,0.5
scripts/build_mp.sh mp_b_r50 export/mm9_njam_b50.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_njam_b50.glb before/mm9_njam.glb --json review/uv_audit_b50.json
SET=b $G scripts/exact_face.py export/mm9_njam_b50.glb; scripts/gates.sh export/mm9_njam_b50.glb b50; python3 scripts/gate_compare.py b50
REA_NODE=Njam $BL -P scripts/lod_check.py -- $PWD/export/mm9_njam_b50.glb b50
python3 scripts/make_viewer_manifest.py b50 "inst_nj=Installed (11,053)=before/mm9_njam.glb" "red_nj=Reduced b50 (8,839)=export/mm9_njam_b50.glb"
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py b50; $G scripts/face_diff_sheet.py b50   # + close_sheet.py per group
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_njam.glb` (0), `tools/install_model.py export/mm9_njam.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, floor audit, and add
to `../mm9_njam_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_njam_reduce_claude`; a rebuild from this project must
re-run that reduction". Rollback: `before/mm9_njam.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates and viewer
only); LOD1-3 and shadow meshes by eye (numbers only); the script clips other than Cower/Kick/Fidget5/PlayGetup by eye (gates only); the
eye/mouth close-ups at the user's zoom (the face triangles are the installed ones and the five-view face diff is black).
