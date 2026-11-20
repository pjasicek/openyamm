# MM9 Horde Soldier (`mm9_clansoldier`, Grunt / Warrior / Leader) LOD0 reduction: fix pass h45 ready for review (2026-11-04)

## Fix pass (2026-11-04 evening): chart-guarded h45, current candidate
The d72 candidate below was installed and **rolled back**: 66 of its LOD0 faces (torso 54: right chest front, chest centre, left
upper arm front and back, left shoulder back, right back hip; limbs 12) had UV triangles leaving the painted charts
(`review/uv_audit/audit.txt`, `closeups.png`). MeshLab's collapse places new vertices and cannot be guarded per collapse, so this pass
uses the pose-aware half-edge collapse with the chart guard (`scripts/mpqem.py`, the Dwarf's copy: `MP_CHART=1`, every sample of a
new face's UV triangle must lie on the installed charts; texture guard on the three tiers' base colours from the installed GLB,
`tex_extract.py`; texture weight `MP_W5=4`; `ClanWeapon_A` kept whole). Every output corner is an installed vertex, so positions,
UVs, normals, joints and weights are exact. The linings are not cut: mpqem.py re-emits them as the reversed twins of the surviving
lined faces (`glb_sets.py`: 870 lining faces matched one to one, twin residual 0.00 mm), so the skirt lining stays the installed bytes.

Keep set (`scripts/glb_sets.py g`): the d72 set (face/neck/eyes, sleeve-end rings, graft junction, grip contact, 2nd/3rd phalanges,
soles, waist lap, small pieces, weapons) plus two contact sets the first guarded steps showed were needed:
- `scripts/hand_contact.py` (460 faces): body faces within 3 cm of a posed forearm/hand vertex in any frame of any clip, mirrored.
  Without it the arm/hand gate rose (Fidget2 R 0.9 -> 2.7 cm, Standing L 0 -> 1.0 cm, DeadStatic L 49 frames over 1 cm).
- `scripts/skirt_contact.py` (338 faces): outer skirt faces within 3 cm of a thigh/calf vertex in Death, Death2, Dead*, Running,
  Cower. Any cut skirt (0.5-0.7) raised skirt_gate's Death 7.5 -> 8.2 cm; the skirt kept whole restored it but cost 650 triangles.
Group ratios: hands 0.6, helmet 0.45, skirt rest 0.7, boots 0.7, pants 0.55; coat/sash at the ladder ratio.

| step (`run_mp.sh`, limits p99 6.24 / max 31.2 mm) | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---:|---|---|---|
| a r50 (d72 set, no contact sets) | 9,797 | 4.24 / 17.0 | .997 / .998 | pass; r40 7.31 / 25.3 fail |
| b r45 (mp45) | 9,665 | 5.02 / 17.0 | .995 / .998 | pass; arm/hand gate up (above) |
| c r45 (+ hand contact) | 9,907 | 5.16 / 16.7 | .995 / .997 | pass; arm gate as installed; r40 fail (guards stop the cut) |
| d r45 (hands .6, helmet .45, skirt .5, pants .55) | 9,613 | 5.55 / 18.7 | .995 / .997 | pass; skirt Death 8.2 cm |
| f r45 (skirt kept whole) | 10,261 | 5.37 / 18.7 | | skirt gate as installed |
| g r45 (+ skirt contact, rest .55) | 9,981 | 5.66 / 28.6 (Death:12, back skirt panels) | .995 / .997 | pass, small margin |
| **h r45 (+ skirt contact, rest .7)** | **10,077 (-21.7 %)** | **5.39 / 18.7** | **.995 / .997** | **picked** |

Candidate `export_mp/mm9_clansoldier.glb` (sha256 79abc5b0be33; `scripts/build_mp.sh mp_h_r45`): LODs 10,077 / 5,037 / 1,811 / 603
(installed 12,869 / 6,432 / 2,312 / 770), built by `scripts/build_lods.py` (`tools/build_actor_lods.py`, 4 influences) with the
snap fix: soles, helmet top and the Dead contact protected, each point snapped to the imported vertex (12 of 12 mapped).
**UV audit (`review/uv_audit.json`, `review/uv_audit.txt`): 0 escaping LOD0 faces in every primitive.** LOD1-3 escapes come from
Blender's decimate as in the installed file (LOD1 limbs 108 vs 86, torso 101 vs 81, head 61 vs 59; LOD2/3 at or below the installed
counts except head LOD2 90 vs 88). Face/neck/eyes: all 3,612 triangles identical to the installed bytes (max difference 0.0,
`face_identity.py`); clips, skin, nodes, materials, images, variants = installed bytes (`same_clips.py`).

Gates (`review/gates_before/` vs `review/gates_mph45/`):
- arm/hand (and the skin-only variant): identical in every clip except Fidget2 R forearm 1.0 -> 0.6 cm and Aware R forearm 0.2 -> 0;
  finger stretch max 1.94 / 1.80 both.
- skirt: every clip identical (Running 4.0, Death 7.5, Death2 6.3, Dead 2.1 cm).
- grip: inside 0.0 both, wrap min 105 / median 150 both (mean 144.4 -> 142.9), rigid lock identical.
- blades: sword identical (Cower 26 -> 25 frames), shield Running 0.7 -> 0.4, Death 4 -> 3 frames.
- jitter: 3 fails both (shoulder skin Walking L 2.43 -> 2.38, Death L 2.13 -> 2.42, Death R 2.62 -> 2.88 mm/f2). Same mesh
  (`ref_swap.py`): 2.41 / 2.10 / 2.57, all below installed; area-weighted excess (`skin_jitter_area.py`) Walking L 4.86 -> 4.83,
  R 2.90 -> 2.97, Death L 6.62 -> 4.98, R 4.22 -> 4.37.
- collapse face-frames 31,474 -> 22,574; single faces new in a few region maxima (armpit L in Walking/Backpedal/Sleep 0 -> 1,
  Running groin/knee 0 -> 1, AttackMelee2 armpit R 0 -> 1).
- detached 0 both (R hand root lift 2.9 -> 2.4 cm); orient, handedness identical; bone lengths 0; winding 0; flat 0.00;
  texture quality now exactly the installed (atlas 57.3 / 69.1 / 61.1 %, same islands).
- LODs (`lod_check.py`): every LOD 2.073 m tall, lowest point in every clip as LOD0 (Dead 0.0 at every LOD; installed LOD1-3 0.1 cm);
  stretched faces LOD0 92 -> 65, LOD1-3 3/0/0 -> 39/39/39: the pants' back centre-seam sliver (installed LOD0 has it: 3 mm2 at rest,
  299 mm2 in Death) carried into LOD1-3 by the Dead-contact protection (634 mm2 in Death). Without that protection LOD1-3 lay
  1.5 cm above the floor in Dead (the seam is the only corpse contact).

Viewer (installed and h45 per tier, 21 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_clansoldier_reduce_claude/review/viewer/
(`run_creature_review.py check`: 126 switches, 0 failed, 0 console errors).
Sheets read (installed | reduced per tier): `review/sheet_escapes_h45.png` (the six d72 escape clusters, bind pose, along their
normals, tiers A/B/C), `review/sheet_faces_h45.png` (face front, 3/4, profile, low 3/4, helmet top; tiers A/B/C),
`review/sheet_body_h45.png` (full front, 3/4, back, Walking, Death; tiers A/B/C), `review/sheet_skirt_h45.png` (skirt back and
side, Running, sword fist; tiers A/B/C), `review/sheet_viewer_all_h45.png` (viewer shots, face and body, every tier),
`review/sheet_fix_tex1.png`, `review/sheet_fix_tex2.png` (c45/d45 steps). All pairs look the same.

Reproduce: `glb_parts.py`, `make_sets.py` (DISTAL=1 d), `hand_contact.py work/keep_d.npy work/keep_e.npy`,
`skirt_contact.py work/keep_e.npy work/keep_g.npy`, `cp groups_e groups_g`, `glb_sets.py g g`, `tex_extract.py`,
`SETS=g MP_GROUPS=1:0.6,2:0.45,3:0.7,5:0.7,6:0.55 MP_W5=4 run_mp.sh h 0.45`, `build_mp.sh mp_h_r45`, then the audit, `gates.sh`,
`lod_check.py`, `viewer_tiers.py`, `glb_close.py` (SPOTS incl. esc0-5), `shots.sh`. Install on OK: `check_winding.py`, then
`tools/install_model.py export_mp/mm9_clansoldier.glb --world mm9`, the binding regression, and the README line in the creature project.

Not checked: in game; motion at normal speed; shadow meshes by eye; LOD1-3 close up by eye (numbers and the escape counts only).

## First pass (superseded, rolled back): d72

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 34 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:clansoldier` (owner
clansoldier-reduce-20261104). No-retexture branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) on the installed r22 +
dropped-clip pass (`assets_source/worlds/mm9/models/mm9_clansoldier.glb`, sha256 487e28a9084b, identical to
`../mm9_clansoldier_claude/export/mm9_clansoldier.glb`; copied to `before/`, the rollback source). No Meshy, no credits.
**Not installed.** The creature project `../mm9_clansoldier_claude/` was only read.

| | LOD0 | limbs set | torso set | head set | weapons | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,869 | 3,009 | 4,438 | 4,728 | 694 | 6,432 | 2,312 | 770 |
| d72 (was `export/mm9_clansoldier.glb`, sha256 9ea6cc372c76; deleted after the rollback) | **9,635 (-25.1 %)** | 2,365 | 2,352 | 4,224 | 694 | 4,813 | 1,729 | 576 |

Clips, skin, nodes, sockets, materials, `KHR_materials_variants`, all 31 images: byte-identical to the installed file
(`scripts/same_clips.py`). Face skin: every one of the 3,612 face/neck/eye triangles is in the candidate with the same positions,
UVs, normals and weights (max difference 2.4e-7, float32; `scripts/face_identity.py`).

## Protected share (measured first)
Part labels from the creature's final rest mesh (`../mm9_clansoldier_claude/work/final_v1.blend`, `scripts/dump_final.py` ->
`scripts/glb_parts.py`, exact face match): hands 1,279, pants 1,088, boots 642, coat 2,636 (sleeve-end linings 188), skirt
1,364 (lining 682), sash 438, face/neck skin 3,428, helmet 1,116, eyes 184, sword 322, shield 372. Only 202 face/neck faces are
hidden (under the helmet brim or the collar; `scripts/head_cover.py`), so the whole face/neck skin stays. With the relaxed set the
kept share is 44.7 % (5,748 faces) plus the 682 dropped skirt-lining faces.

## What is kept and what is cut (`scripts/make_sets.py d`, `DISTAL=1`)
- **Exact:** face/neck skin and eyes (3,612); the sleeve-end linings with the outer rings they line (380); the hand-graft junction
  (0 < graft_s < 1, or Hand/Finger and Forearm weight both > 0.02) and the faces within 1.5 cm of a grip at rest (weapons are rigid
  to the fists); the 2nd/3rd phalanges, the pads round the grips (735; the Giant's pass-2 rule); soles (lowest 2 cm); the
  sash/skirt waist lap (2 cm each side); every piece of up to 100 faces (finger pieces, struts); the sword and shield (kept as the
  installed `ClanWeapon_A` primitive, byte for byte).
- **Dropped and rebuilt:** the skirt lining. It is dropped before the cut and rebuilt on export from the reduced skirt exactly as
  `finish_clan.py` made it: inner copy 3 mm in along the area-weighted normal, flipped, same weights, on the torso set's dark texel
  (`scripts/export_cand.py`, `REA_RELINE`). 682 -> 374.
- **Own ratios:** hands outside the exact sets 0.65 (palm, back, proximal phalanges), helmet 0.55, skirt outer 0.55, boots 0.75,
  pants 0.65 (`REA_GROUP_RATIOS=1:0.65,2:0.55,3:0.55,5:0.75,6:0.65`).
- **Shared cut:** coat and sash take the rest of the ladder budget. Texture-aware MeshLab collapse, source vertices keep exact
  weights, new ones UV-barycentric (`REA_WEIGHTS=component`).
- Normals: the installed normals are Blender's angle-weighted smooth normals over the welded topology (`scripts/normal_rule_test.py`:
  0 of 8,388 body/head vertices over 1 deg), so source vertices keep the installed normal and new vertices keep Blender's export
  normal (`scripts/fix_normals.py`, `RULE=export`). Joints written as unsigned byte like the installed primitives (`swap_lod0.py`).

## Ladder (`scripts/run_ladder.sh`; 2.08 m: p99 <= 6.24 mm, max <= 31.2 mm, IoU >= .98, SSIM >= .93; LOD0 = ladder + relined skirt)

| config | change | step | ladder tris | p99 / max mm | IoU / SSIM | verdict |
|---|---|---|---:|---|---|---|
| a | hands .7, helmet .65, skirt .6, boots .8, pants .7 | r80 / r76 / r73 / r70 | 10,291 / 9,775 / 9,389 / 9,003 | 2.99/14.0, 3.03/14.0, 3.67/15.3, 5.59/27.4 | .994/.995 at r70 | all pass; r70 has a pale fleck on the right chest side (coat at ~34 %) |
| b | a + drift lock (3 cm / 1.2 cm) | r73..r67 | | 44 / 121; 6.5 / 37.9 | | fail: the lock starves the coat |
| c | hands .65, helmet .55, skirt .55, boots .75, pants .65 | r73 / r72 / r71 / r70 / r68 / r66 | 9,391 .. 8,489 | 3.52/13.4 .. 4.26/18.1, 5.6/27.4, 9.04/47.3 | .996/.996 at r70 | r70 passes and looks clean, but the grip wraps dropped (fingers at .65) |
| **d** | c + 2nd/3rd phalanges exact | r73 / **r72** / r71 / r70 | 9,391 / **9,261** / 9,133 / 9,005 | 4.19/15.3, **4.44/18.1** (Death:12), 5.01/18.1, 5.62/27.4 | **.996 / .996** | all pass; **r72 picked** |

The coat is at its limit around r70: below it the error jumps (c r66 p99 9.0 mm) and a70 showed texture drift. d72 rather than
d71 (also clean in close-ups) for margin. Ladder sheets: `review/ladder_sheet.png` (last run, d).

## Gates, installed -> d72 (`scripts/gates.sh`: the creature project's own gates, run from it on the runtime GLBs; `review/gates_before/`, `review/gates_d72/`)

| Gate | installed | d72 |
|---|---|---|
| Arm/hand (`--outer-only --exact`, 48 fps) | Sleep R 2.5 cm (3 f), Death L 1.1 cm (1 f), Fidget2 R 0.9 / forearm 1.0, Hit L forearm 0.3 | Sleep R 2.6 cm (3 f, script clip), Death L 0.6 (0 f), Fidget2 R 0.4 / 0.5, Hit L 0; finger stretch max 1.94 / 1.80 -> 1.94 / 1.62 |
| Jitter (vs `clan_clips0.glb`) | 3 fails: Walking L 2.43, Death L 2.13, Death R 2.62 mm/f2 shoulder skin | 3 fails: Walking L 2.41, Death L 2.69, Death R 2.05 |
| Jitter, same mesh (`ref_swap.py`) | the same 3: 2.43 / 2.13 / 2.62 | 2.41 / 2.39 / 2.23 (worst lower) |
| Shoulder skin, area-weighted excess (`skin_jitter_area.py`) | Walking L/R 4.86 / 2.90, Death L/R 6.62 / 4.22 | 4.86 / 2.80, 6.39 / 3.73 |
| Grip (both hands, every clip) | inside 0.0 cm; wrap min 105, median 150, mean 144 deg; rigid 0.0/0.1 (AttackMelee2 R 21.5 as installed) | inside 0.0 cm; wrap min 105, **median 142.5, mean 141** (single fingers one 15 deg bin lower: vertex sampling of the cut proximal phalanges); rigid identical |
| Skirt (`skirt_gate.py`) | Running 4.0 cm 18/25 f, Cower 5.0, Death 7.5, Death2 6.3, Dead 2.1 | Running 3.8 13/25, Cower 5.0, **Death 7.6** (38/58 f, was 44), Death2 5.2, Dead 1.2; every other clip within 0.1 cm. Fewer outer-skirt faces (630 -> 328), so frame counts are not strictly comparable |
| Blade, sword | Cower 6.0 cm 26 f (script clip) | Cower 6.0 cm 27 f; all else identical |
| Blade, shield | Running 0.7, AttackMelee 0.9, Death 4.0 (4 f) | 0.5, 0.8, 3.9 (4 f) |
| Collapse (face-frames, all clips) | 31,474 | 21,381; no region's worst count higher in any clip |
| Detached | 0 detached; R hand root lift 2.9 cm (AttackMelee) | 0 detached; R hand piece root lift 90th pct 5.4 cm off the forearm in Death frame 14 (informational line of the audit) |
| Orient, handedness, bone lengths, winding | as recorded | identical; 0 stretching; 0 inverted |
| Flat shading | 0.00 / 0.01 / 0.00 / 0.09 | 0.00 / 0.00 / 0.00 / 0.09 |
| Texture quality | limbs 57.3 %, torso 69.1 % stretch 1.17, head 61.1 % | limbs 56.7 %, torso 67.3 % stretch 1.31, head 61.0 % |
| LODs (`lod_check.py`, every frame of every clip) | heights 2.073/2.073/2.073/2.072 m; stretched faces 92/3/0/0 | 2.073/2.073/2.073/2.077 m; 92/0/0/0; LOD0 lowest points identical in every clip; LOD3 Death 4 mm lower (-1.4 cm) |

## Review
- Viewer (installed and d72 per tier, all 21 clips):
  http://127.0.0.1:8912/level_generation/creatures/mm9_clansoldier_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 126 switches, 0 failed, 0 console errors).
- Sheets read: `review/sheet_face_a.png` (GLB face front, 3/4, profile, low 3/4, helmet top/back; a73/a70), `review/sheet_c_tex.png`,
  `review/sheet_d_tex.png` (chest, back, shoulders, skirt back, sword fist: installed / d72 / d71), `review/sheet_body1_tex.png`,
  `review/sheet_body1_clay.png`, `review/sheet_body2_tex.png`, `review/sheet_body2_clay.png`, `review/sheet_motion_tex.png`,
  `review/sheet_c70_clay.png`, `review/sheet_c70_tex2.png`, `review/sheet_lods_d72.png`, viewer shots `review/sheet_viewer_face_{a,b,c}.png`,
  `review/sheet_viewer_body_{a,b,c}.png`.
- What to look at: the coat front/back pattern (diamond grid, eye discs) and the helmet dome at 0.55 in the standard 3/4; the
  skirt hem in Running; both fists.

## Install (not run; on the user's OK)
`check_winding.py export/mm9_clansoldier.glb` (0), `tools/install_model.py export/mm9_clansoldier.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, then add to `../mm9_clansoldier_claude/README.md`: "LOD0 reduced post-install on
<date> by `mm9_clansoldier_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_clansoldier.glb`.

## Reproduce (project folder)
`REA_GLB=level_generation/creatures/mm9_clansoldier_reduce_claude/before/mm9_clansoldier.glb REA_NODE=ClanSoldier` blender
`import_source.py` (weld identical weights: 0 coincident pairs) -> `dump_mesh.py` -> `dump_weights.py` -> `dump_final.py` ->
`glb_parts.py` -> `DISTAL=1 make_sets.py d` -> `REA_HEIGHT_M=2.08 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_d.npy
REA_DROP_FACES=work/drop_d.npy REA_GROUPS=work/groups_d.npy REA_GROUP_RATIOS=1:0.65,2:0.55,3:0.55,5:0.75,6:0.65 run_ladder.sh d
0.73,0.72,0.71,0.70` -> `REA_BLEND=ladder_d.blend REA_RELINE=work/drop_d.npy build_export.sh Cand_72 clan_d72` (export_cand with the
source's lowest point as floor and the relined skirt -> swap_lod0 -> fix_normals with `KEEP_PRIMS=ClanWeapon_A` ->
`tools/build_actor_lods.py` 4 influences -> the creature's shrink_shadow_lods -> carry_variants -> fix_winding -> check_winding);
`viewer_tiers.py`, `make_viewer_manifest.py`, `shots.sh`, `shot_sheet.py`, `gates.sh`, `lod_check.py`, `lod_views.py`.

## Not checked / not done
- In game; motion at normal speed (frames and gates only); the shadow meshes by eye.
- Weapons not rebuilt: sword 322 and shield 372 are already procedural low-poly builds; a rebuild with a projection bake of the
  three tiers' weapon maps would save roughly 300 more triangles (about 2 %).
- Tier B and C only in viewer shots, not in Blender close-ups.
