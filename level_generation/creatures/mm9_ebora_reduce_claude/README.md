# MM9 Ebora / Concubine (`mm9_ebora.glb`) reduction, 2026-11-04

**Status: ready for review (fix pass, chart guard, UV audit 0)**: 15,299 -> **12,869** (−15.9 %), `export/mm9_ebora.glb` (sha
d8fec1775720). Round 2 (12,580, MeshLab cut) was installed and rolled back by the orchestrator: the UV audit found 94 LOD0 faces
off the painted charts (broken leg flowers, dark hip slivers; `review/uv_audit/closeups.png`). Rounds 1-2 below for the record.

Brief: `devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md` (no-retexture branch of the retopology playbook). Lease
`mm9reduce:ebora`. Source and rollback copy: `before/mm9_ebora.glb` (sha 5a8a356830dd, = installed). **Nothing installed.**

## Round 1 (strict keep set): kept (no useful gain)

## Why no gain
LOD0 15,299: head set 6,177 (face, hair and its 733 back copies, horns, eyes: untouchable), wings 2,304, hands and fingers
1,350, neck ring 184, soles 258, small pieces (shoulder spikes, claws) 316. That leaves 4,710 free faces (torso and arms
3,276, legs 1,434), and Ebora's own build had already cut the body to 10.4k (`step1_clean.py`), so it is lean.
- **Wing membranes cannot be cut:** the pleat helpers weight 1,336 of their 1,464 faces; at 50 % the fold moved 63 mm
  (AttackMelee, `XPleatA1`), ladder `c` failed at every step.
- **Printed motifs warp first:** in the shared cut the skull cups distort at 85 % (13,003) and the knee medallions and stud
  columns at 85-80 % (`review/close/crop_torso_front.png`, `crop_legs_front.png`, `crop_f85.png`).
- **Protecting the motifs moves the cut onto the plain body:** with cups and leg panels kept (`g`), the lowest passing step is
  86 % = 13,157 (−14.0 %), and arms, knees and thighs already read faceted in clay (`review/close/sheet_g86.png`).
  Keeping every motif (`e`) or cutting them on their own (`d`) fails at every step (p99 8-30 mm).

## Ladders (limits for 1.92 m: p99 5.76 mm, max 28.8 mm; open edges 987 everywhere)
| run | kept / grouped | step | tris | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| a | head, wings, hands, neck, soles, small | 80 | 12,239 | 5.69 / 20.8 | .986 | .992 | pass (nearest-vertex weights) |
| b | same, interpolated weights | 88 / 85 / 80 | 13,463 / 13,003 / 12,239 | 3.12/13.7, 3.83/19.2, 5.59/21.3 | .994/.993/.987 | .995/.995/.992 | pass; skull cups warp at 85, knee at 80 |
| c | b + membranes at 50 % | 82-74 | 12,545-11,321 | max 63 (pleat) | | | fail |
| d | b + motifs at 85 % own cut | 88 | 13,461 | 6.06 / 22.3 | .988 | .994 | fail |
| e | b + every motif kept | 88 | 13,463 | 8.05 / 30.7 | .985 | .993 | fail |
| f | b + skull cups kept | 85 | 13,003 | 4.87 / 16.5 | .988 | .994 | pass; knee medallions warp |
| g | f + leg motif panels kept | 86 / 85 | 13,157 / 13,003 | 5.34/20.9, 6.26/21.7 | .990/.989 | .994/.993 | 86 pass (−14 %, faceted arms/legs), 85 fail |

## Scripts (reusable for the queue)
`import_source.py` (weld identical weights only), `dump_mesh.py` (material, hand weights, dense weights), `regions.py` (keep
sets), `pattern_faces.py` (printed motifs by paint), `decimate_tex.py`, `interp_weights.py` (new: piece-aware barycentric
weights from the closest source triangle; the nearest-vertex piece weights left 13-20 mm at the half-joint hips and shoulders),
`reduce_ladder.py` (`REA_WEIGHTS=interp`), `compare_ladder.py`, `run_ladder.sh`, `build_pick.sh` (export, swap, then
`fix_normals.py`: installed normals on source vertices, Ebora's `build_glb.py` rule for new ones, head and wing primitives
copied byte for byte; `kept_identical.py` verifies), `close_glb.py` + `close_sheet.py` (textured and clay close-ups from GLBs),
`texture_drift.py` (per-material images), `probe_max.py`, `probe_rest.py` (rest vs posed error).
Gates, viewer and LOD build were not run: no step qualified.

## Round 2: relaxed keep set for prio-1 monsters (orchestrator, 2026-11-04)

Brief section "Prio-1 monsters: relaxed keep set". No credits.

**Kept exactly:** face skin piece (incl. scalp), eyes, mouth, horns, fringe and side locks with their back copies, neck ring
(2 cm), soles, small pieces (≤ 80 faces), wings (spars and membranes), skull cups (motif kept for the breast silhouette), forearms
(Death L forearm in the wing went 1.3 -> 5.0 cm when cut), shoulder skin (Clavicle+UpperArm > 0.5: the jitter gate's shoulder
skin failed AttackRanged R 2.3 mm/f2 against the installed mesh when cut), and one shoulder drift-lock round
(`shoulder_lock.py`: dark flecks pulled from the strap edge onto the shoulder skin).
**Cut:** hair shell 1,428 -> 998 (70 %) with its 529 back copies dropped and rebuilt on the reduced shell (406,
`hair_backs_regen.py`: reversed copy 0.5 mm inward wherever the nearest original shell face had one, front vertex weights);
hands 70 % keeping every finger (claws are small pieces, kept); torso and legs in the shared cut.
**Wing membranes left whole:** cutting the faces not weighted > 0.5 to the pleat helpers moved the membrane 36.7 mm at rest
and 48 mm in Fall (limit 28.8 mm), ladder `rm`.

| run | change | step | tris | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| r | relaxed set | 74 | 11,356 | 5.46 / 21.3 | .986 | .992 | pass; breasts flatten, shoulder flecks |
| rm | r + membranes (pleat > 0.5 kept) at 60 % | 76 / 74 | 11,660 / 11,354 | max 48.4 (Fall) | | | fail |
| rf | r + skull cups | 78 | 11,968 | 5.06 / 17.4 | .986 | .993 | pass; shoulder flecks |
| rfl | rf + shoulder drift lock | 78 | 11,968 | 5.59 / 21.3 | .985 | .992 | pass; Death L forearm 5.0 cm |
| rflf | rfl + forearms | 80 | 12,274 | 5.10 / 21.3 | .987 | .993 | pass; jitter AttackRanged R vs installed 2.3 |
| **rflfs** | rflf + shoulder skin | **82** | **12,580** | 4.83 / 21.3 | .988 | .994 | **picked** |

Open edges 990 against 987: the rebuilt hair back copies are open patches (3 more rim edges), `REA_OPEN_SLACK=3`.

**Build** (`build_pick.sh rflfs r82 final`): LOD0 swap, `fix_normals.py` (installed normals on source vertices, Ebora's
`build_glb.py` rule elsewhere, wing primitive copied byte for byte, encodings unified for the shadow merge),
`build_actor_lods.py` (Ebora's ratios, 4 influences), `shrink_shadow_lods.py`, `carry_variants.py`, Ebora's `fix_winding.py`.
Images, clips, materials, variants, nodes and bind matrices identical to the installed file; wings byte-identical.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 15,299 | 7,649 | 2,751 | 906 |
| reduced | 12,580 | 6,289 | 2,263 | 744 |
Per material LOD0: torso 5,126 -> 3,828, head 6,177 -> 5,624, legs 1,692 -> 824, wing 2,304.

**Gates** (`review/gates_before/` installed, `review/gates_after3/` candidate; Ebora's own set):
| Gate | Installed | Reduced |
|---|---|---|
| winding / bone length | 0 / 0 stretching | 0 / 0 stretching |
| detached | 0 (38 components) | 0 (46: rebuilt hair back patches) |
| flat shading | 0.00 / 0.01 / 0.00 / 0.00 | same |
| jitter vs MM9 reference (`ref_half.glb`) | 9 fails | the same 9 clip sides |
| jitter vs installed | – | 0 fails |
| arm/hand | AttackRanged L 0.5 cm, R 1.4 (2 f); Death L forearm 1.3, R 6.0; Land L 1.6 (4 f) | L 0.8 (0 f > 1 cm), R 1.3 (2 f); Death 1.3 / 6.0; Land L 1.4 (4 f); finger stretch max 3.92 FallDown both |
| collapse (sum of worst-frame faces / exposed) | 5,787 / 2,322 | 5,447 / 2,187 (Running hips 18/15 -> 4/4); single +1 torso faces in several clips, Taunt wrist_L 2 -> 3, AttackMelee exposed wing 70/55 -> 77/59 (wing unchanged; body occlusion) |
| LODs (`lod_check.py`) | min z over clips −0.1382..−0.1399, 8 stretched faces (FallDown) | identical; LOD3 rest bottom 8 mm higher (min over clips the same) |
| texture quality torso / legs stretch p90 | 1.06 / 1.07 | 1.28 / 1.53 (reduced faces span more texels) |
| viewer check | | 220 switches, 0 failed, 0 console errors |

**Sheets** (read): `review/sheet_faces_eb_s1.png`, `review/sheet_faces_s2_s3_s4.png` (front close-up, 3/4, profile, low 3/4,
party per tier, installed | reduced | diff x4: face pixels identical, differences on the hair silhouette and body),
`review/sheet_body_eb_s1.png`, `review/sheet_body_s2_s3_s4.png` (Standing front/3-4/back, Walking, AttackMelee), and the
Blender close-ups `review/close/sheet_rel_head.png`, `sheet_rel_hands.png`, `sheet_rel_body.png`, `sheet_rf78.png`,
`sheet_rfl78.png`, `sheet_rfl78b.png` (steps before the forearm/shoulder keeps). Viewer:
http://127.0.0.1:8912/level_generation/creatures/mm9_ebora_reduce_claude/review/viewer/ (revision reduce3-20261104, every
tier installed and reduced).

Not checked: in-game, the actor regression (only after install), playback at normal speed, Android, `floor_audit.py` (reads
the installed file only; `lod_check.py` min z is identical), see-through/sleeve gates (Ebora's project ran none).
On install: `tools/install_model.py export/mm9_ebora.glb --world mm9` (winding checked), regression, ledger, and the line in
`mm9_ebora_claude/README.md`.

## Fix pass: pose-aware collapse with the chart guard (2026-11-04)

Round 2's MeshLab cut slid seam vertices so that 94 new faces reached off their UV charts (Torso 51, Legs 39, Head 4). Per the
Giant's fix pass, locking around escapes only moves them, so the cut now runs on the pose-aware half-edge collapse
(`scripts/mpqem.py`, from `mm9_giant_reduce_claude`): every output corner is an installed GLB vertex (position, normal, UV,
joints, weights exact), UV seams locked, cost over 330 poses of every clip, **chart guard** (MP_CHART=1), texture guard on the
eb and siren1 base colours and the s2-s4 region masks (`work/tex_list.json`). Wings kept whole.
- Sets (`ebora_sets.py` maps round 2's masks onto GLB faces): round 2's keep set, plus the 2nd/3rd phalanges and finger tips
  exactly (with them cut, the left thumb read 5.9 cm inside the right index fingertip in AttackRanged at 0.125 s, palms
  together; installed 0.3-0.5 cm). Hair shell 0.6, palms/backs/proximal phalanges 0.6, torso and legs at the ladder ratio.
- Hair back copies: treated as the Highwayman's linings (not cut; the lined region's border locked; each surviving shell face
  re-emits its reversed copy from the existing copy vertices). The twin is matched per GLB vertex by position and UV (by
  position alone, back faces took corners from another chart: 128 escapes in the first audit). 529 -> 381 copies.

| step (body ratio) | LOD0 | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| f r60 (hair 0.7, hands 0.7) | 13,037 | 3.54 / 17.1 | .994 | .995 | pass, −14.8 % |
| g r60 (hair, hands 0.6) | 12,749 | 4.02 / 17.1 | .994 | .995 | pass; AttackRanged L thumb 5.9 cm (fingertips cut) |
| i r60 (+ distal phalanges kept) | 12,969 | 4.17 / 17.1 | .993 | .995 | pass |
| **i r57** | **12,869** | 5.19 / 22.6 | .992 | .995 | **picked** (−15.9 %) |
| f/g r55, r50 | 12,613-12,829 | 5.4-8.1 / 44.5 | | | fail (the torso floor: guards stop near 1,060 faces) |

Build `scripts/build_mp.sh mp_i_r57`: swap_mp (installed attributes byte for byte), build_actor_lods (4 influences),
shrink_shadow_lods, carry_variants, fix_winding, compact, check_winding 0, bone length 0 stretching.
LODs 12,869 / 6,433 / 2,314 / 763 (installed 15,299 / 7,649 / 2,751 / 906); lowest point over every clip identical at every
LOD, stretched faces as installed (8 / 6 / 6 / 6, FallDown).
**UV audit** (`review/uv_audit_fix/audit_mp_i_r57.txt`): LOD0 Torso 0, Head 0, Legs 0, Wing 0 escaping. LOD1-3 (Blender's
decimate in build_actor_lods) at the installed LODs' own baseline: LOD1 153/70/71/0 vs 155/67/67/0, LOD2 155/141/54/40 vs
122/129/54/41, LOD3 71/88/32/43 vs 67/95/33/43.

Gates (`review/gates_fix2/` vs `review/gates_before/`): winding 0, bones 0, detached 0 (38 components, as installed), flat
shading as installed; jitter vs MM9 reference the same 9 clip sides; arm/hand equal or better everywhere (AttackRanged L 0.5 ->
0.3 cm, R 1.4 -> 1.2 cm; Land R hand 0.4 -> 0.5 cm, under 1 cm); collapse sums 5,787 -> 5,607 worst-frame faces, 2,322 ->
2,251 exposed (20 single counts up by one; exposed wing faces in AttackMelee 70/55 -> 77/59 with the wing unchanged:
body occlusion); texture quality: torso stretch p90 1.06 -> 1.1, spread 1.10 -> 1.12, fragments 0.2 % as installed.
Viewer revision fix2-20261104 (every tier installed and fix pass): 220 switches, 0 failed, 0 console errors.

Sheets (read): `review/fix_closeups_eb_s1.png`, `review/fix_closeups_s2_s3_s4.png` (thighs with the leg flowers front and 3/4,
knees with the medallions front and 3/4, hips back both sides and front, breast cups; installed | fix pass per tier),
`review/fix_eb_zoom.png` (Ebora full-size: flowers, knee medallions, hip back), `review/sheet_faces_eb_s1.png`,
`review/sheet_faces_s2_s3_s4.png` (face pixels identical; hair edge and body differ), `review/sheet_body_*.png`.
Not checked: in game, the actor regression (after install), playback at normal speed.
