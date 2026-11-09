# MM9 Lizard-Orc (`mm9_lizardorc`) reduction: fix-pass candidate f70 ready for review (2026-11-04)

**Status (fix pass): candidate `export/mm9_lizardorc_f70.glb` (11,829, -14.8 %), chart-guarded, `reduction_uv_audit.py` LOD0 0
escaping faces; ready for review, not installed (the orchestrator installs).** r85m below (MeshLab route, 11,801) was installed and
rolled back: the UV audit found 67 LOD0 faces off the painted charts (bracer seams, a cut cuff rivet, the crotch plate;
`review/uv_audit/closeups.png`). The installed file is `before/` again (sha256 9a8b9244cbb7).

## Fix pass: pose-aware half-edge collapse with the chart guard
Route of `mm9_imp_reduce_claude/` (`scripts/mpqem.py`, `run_mp.sh`, `build_mp.sh`, `swap_mp.py`, `tex_extract.py`, copied and set
to node LizardOrc): only removes vertices, every output corner is an installed GLB vertex (positions, normals, UVs, joints, weights
exact), cost over every clip at 10 Hz plus a position+UV rest quadric, texture guard on the base colour, region mask and
metal/roughness of both body pages, UV seams locked except slides on the cut groups (`MP_SEAM_GROUPS=0,7,8,9`), **chart guard on**
(`MP_CHART=1`). LizHead_A and LizWeapon are kept whole: their accessors are the installed bytes (checked).
Sets (`scripts/glb_sets.py` maps the mesh_in sets to GLB faces): `work/keep_b.npy` = the r85m keep set without the err-lock
patches (wrist junctions, grip contact, neck band, soles 2 cm, chest shell, hip plates, small pieces) plus the elbow patches;
groups: left hand 0.6, right hand 0.65, pauldron lames (parts 18-22, 24; 440 faces) 0.7, the rest at the ladder ratio.

| set | step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---:|---|---|---|
| a (hands .6/.75, lames kept) | r75 / r70 / r69 / r68 / r66 | 12,253 / 11,997 / 11,945 / 11,897 / 11,793 | 3.96, 5.12, 5.47, 5.65, 6.64 | | pass, pass, pass, fail, fail |
| b (+ lames .7, right hand .65) | r71 / **r70** / r69 | 11,881 / **11,829** / 11,777 | 5.20, **5.44 / 20.8** (Death:18), 5.72 | .994 / .990 | pass / **PASS, picked** / fail |

Candidate f70: LOD0 11,829 (Liz 3,610, LizB 2,504, head 4,920, cutlass 795); LODs 5,894 / 2,106 / 692 (r18 6,922 / 2,480 / 816).
**UV audit** (`export/mm9_lizardorc_f70_uv_audit.json`): LOD0 0 / 0 / 0 / 0. LOD1-3 come from tools/build_actor_lods.py as before:
LOD1 Liz 140 (installed LOD1 138), LizB 179 (127); LOD2-3 at or below the installed baseline except LOD2 Liz 225 (209).
LOD check: LOD0 lowest point identical in every clip, 32 stretched (the neck strip, as r18); LOD1-3 0 stretched, LOD3 8.5 mm under
LOD0 at worst (r18 9.7).

Gates r18 -> f70 (`review/gates_before/`, `review/gates_f70/`):
- Arm/hand: equal or better; Death2 L hand 3.6 -> 3.3 cm, forearm 3.5 -> 2.6; AttackMelee2 R forearm 0.7 (equal).
- Plates: Running inner 2.0 -> 0.7 cm (6 -> 2 f), AttackMelee inner 15 -> 8 f, Death flap 18 -> 10 f, Death2 inner 2.8 -> 2.6;
  Death2 flap 4.1 -> 4.3 cm (same frames); every other clip identical. The r85m plate regressions are gone.
- Detached: strap 1.93 cm in 63/528 poses (= r18), chest shell 0.98 cm, L pauldron half 0.49 cm in 1 pose.
- Grip: 0.0 cm inside every clip; Finger3 wrap 195 -> 180 deg (fewer finger vertices sampled). Blade, bones, flat, winding 0,
  stride, orient: identical. Collapse face-frames 21,881 -> 20,981.
- **Jitter, shoulder skin: standard gate 9 fails on the left side (AttackMelee 3.56, Hit2 3.90, BackpedalRun 2.91 ... mm/f2;
  r18 0); same-mesh gate 1 fail (AttackMelee L 2.18, r18 1.65).** Every remaining vertex is an installed vertex with its exact
  weights, so this is the 95th percentile over a smaller vertex set (608 -> 499 per side): `scripts/shoulder_subset.py`
  (`review/shoulder_subset_f70.txt`) gives the vertex maximum never higher in any clip and p95 within 0.3 mm/f2 except Hit2 L
  82.3 -> 89.1 and AttackRanged L 304 -> 310. Keeping the shoulder population exactly costs about 1,100 faces (hide 660,
  pauldrons 510), more than the margin to 15 %; not done.

Close-ups (read, every tier, installed vs f70): the 12 worst rolled-back escape clusters re-rendered at rest
(`review/fix_audit_spots_1.png`, `_2.png`: crotch plate, bracer seams and rivets, greave cuffs, chest mail): identical;
`review/fix_close1_a.png` (bracers, crotch front/back), `review/fix_close2_c.png` (hip, hips, both pauldrons, pauldron top);
viewer shots `review/fix_viewer_face_b.png` (identical), `review/fix_viewer_body_a.png`. Written, not read: `fix_close1_b/c`,
`fix_close2_a/b`, `fix_viewer_face_a/c`, `fix_viewer_body_b/c`.
Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_lizardorc_reduce_claude/review/viewer/ (installed and f70, tiers
A/B/C, 16 clips; 96 switches, 0 failed).

Build: `$G scripts/tex_extract.py; EXTRA=work/extra_elbow.npy $G scripts/glb_sets.py b work/keep_b.npy work/groups_b.npy;
MP_CHART=1 MP_SEAM_GROUPS=0,7,8,9 SETS=b MP_GROUPS=7:0.6,8:0.65,9:0.7 scripts/run_mp.sh b2 0.71,0.70;
scripts/build_mp.sh mp_b2_r70 export/mm9_lizardorc_f70.glb` (runs the UV audit); gates `scripts/gates.sh export/mm9_lizardorc_f70.glb f70`.

## First pass (MeshLab route; installed as r85m and rolled back)


Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 18. Lease `mm9reduce:lizardorc` (owner lizardorc-reduce-20261104). No-retexture branch of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) on the installed r18 (`assets_source/worlds/mm9/models/mm9_lizardorc.glb`,
sha256 9a8b9244cbb7, copied to `before/`, the rollback source). **Nothing installed**; `../mm9_lizardorc_claude/` was only read.

| | installed r18 | candidate r85m |
|---|---:|---:|
| LOD0 | 13,881 | **11,801 (-15.0 %)** |
| LOD1 / 2 / 3 | 6,922 / 2,480 / 816 | 5,881 / 2,103 / 689 |
| body pages Liz / LizB | 4,820 / 3,346 | 3,590 / 2,496 |
| head LizHead, cutlass LizWeapon | 4,920 / 795 | same primitives, installed bytes |

Candidate: `export/mm9_lizardorc_r85m.glb` (sha256 5838e29e4a4c). Viewer (installed and reduced, tiers A/B/C, all 16 clips):
http://127.0.0.1:8912/level_generation/creatures/mm9_lizardorc_reduce_claude/review/viewer/ (`check_viewer.mjs`: 96 switches, 0 failed).

## Protected share (measured first)
Part labels from the creature's final rest mesh (`../mm9_lizardorc_claude/work/final.npz`, matched to the GLB faces exactly,
`scripts/glb_parts.py`). The full keep set (head primitive, both hands, soles, neck band, chest shell, small pieces, cutlass)
was 63-66 % of the mesh, and the hide/armour already reduced at assembly: a uniform cut of the rest failed the stop rule at
-13 % (ladder U r87 p99 5.72 mm, max 38.7 mm). The prio-1 relaxed set brought it to 56 %:

- **Exact** (`scripts/make_sets.py`, `REA_KEEP_FACES=work/keep_Lm.npy`, 7,827 of 13,845 welded faces): the whole head primitive
  (face, helm, teeth, tongue, neck strip with its chin-crease and ring normals; restored byte for byte on export), the cutlass
  (thin blade went wavy at 0.6, the Dwarf lesson), the wrist junctions (hand and forearm weight both > 0.1), the right hand's grip
  contact (faces within 2.5 cm of the cutlass at 6 times of every clip, `scripts/grip_contact.py`: 277), body faces within 4 cm of the
  neck ring, soles (lowest 2 cm), the chest shell (part 11) and every piece of up to 90 faces (pauldron lames, thigh straps, flap,
  hip plates: all of `plate_gate.py`'s shell points), plus err-lock patches round 16 source points missed by > 18 mm
  (`scripts/err_lock.py`, 2 cm) and a 5 cm patch at each elbow (the r85c right elbow went 2.4 cm into the chest in AttackMelee2).
- **Hands as groups:** left (empty, cast) hand 0.6, right hand outside the grip contact 0.75 (`REA_GROUP_RATIOS=7:0.6,8:0.75`).
  Every finger kept; clay close-ups show slightly more faceted finger joints at full-screen size, not at party distance.
- Everything else (hide, tail, pauldron domes, bracers, greaves, belt skirt) in one shared texture-aware cut. Separate group
  ratios for the armour did worse (ladder G1 r86 p99 7.06 vs the shared cut's 5.4), as on the MM6 Dwarf.

## Ladder (`scripts/run_ladder.sh`; limits for 1.83 m: p99 <= 5.49 mm, max <= 27.45 mm; IoU >= .98, SSIM >= .93)

| config | step | LOD0 (welded) | p99 / max mm | IoU / SSIM | |
|---|---|---:|---|---|---|
| U (full keep set, uniform) | r90 / r87 / r85 | 12,459 / 12,045 / 11,767 | 4.18/30.3, 5.72/38.7, 6.76/38.7 | .994/.990 ... | fail |
| He (left hand 0.7, blade 0.6, err-lock) | r86 / r85 | 11,905 / 11,767 | 5.43/18.6 PASS, 5.96 fail | .991/.987 | |
| Je (+ right hand 0.75, blade 0.6) | r85 / r84 | 11,765 / 11,627 | 5.43/18.6 PASS, 5.84 fail | .990/.987 | blade wavy: dropped |
| Lc (cutlass kept, hands 0.6/0.75) | r85 | 11,767 | 5.44/18.6 | .991/.987 | PASS |
| **Lm** (Lc + elbow patches) | **r85** | **11,767** | **5.47/18.6** (Death:9) | **.991/.987** | **PASS, picked** |
| Ls (Lm + hide within 7 cm of the thigh straps) | r85 | 11,767 | 5.60 | | fail |

Final LOD0 11,801 = 11,767 + the 34 degenerate head/cutlass triangles Blender drops and the restored primitives keep.
Weights: UV-barycentric (`REA_WEIGHTS=component`, `uv_weights.py`); piece weights gave max 47 mm (IeP).
`texture_drift.py`/`dark_slivers.py` (made multi-material) flag large pauldron/greave faces; rendered at rest from their normals
(`review/sheet_drift_spots.png`) they are identical to the installed model: false positives from the stacked armour shells. No drift lock.

## Export (`scripts/build_export.sh Cand_85 mm9_lizardorc_r85m`, `REA_BLEND=ladder_Lm.blend`)
export_cand (floor = source's lowest point, 0 lifted) -> `swap_lod0.py` (joints written as u16 like the installed primitives) ->
`fix_normals.py` (source vertices keep the installed normals, new ones take build_glb's rule: area-weighted, merged by rounded
position over all primitives; head and cutlass primitives restored byte for byte) -> `tools/build_actor_lods.py` (4 influences)
-> `shrink_shadow_lods.py` -> `carry_variants.py` (13 primitives) -> the creature's `fix_winding.py` (0 flipped) -> check_winding 0.
Clips, sockets, materials, variants, images: unchanged (swap into the installed file).

## Gates, installed r18 -> r85m (`scripts/gates.sh`: the creature's own gates, run from its project; `review/gates_before/`, `review/gates_r85m/`)

| Gate | r18 | r85m |
|---|---|---|
| Arm/hand (48 fps) | Death2 L hand 3.6 cm 1 f, forearm 3.5; AttackRanged L forearm 2.0; AttackMelee2 R forearm 0.7 | identical in every clip |
| Grip | 0.0 cm inside, wrap 60/150/150/195 | identical |
| Blade | AttackMelee2 1.3 cm 1 f | identical |
| Collapse (face-frames, all clips) | 21,881 | 20,552; per region equal or lower except +1 face: Running hip L/R 4/3 -> 5/4, Death hip L 4 -> 5, Dead shoulder L 1 -> 2 and torso 0 -> 1, head (neck band, kept faces next to cut body faces) +1 in Hit2, Death, Death2 |
| Plates (flap / inner / tasset) | Running 2.5/2.0/1.9, Death 1.0/2.3/3.4 (tasset 23 f), Dead -/0.4/0 | **Running inner 3.3 cm** (6 f, as before), **Death tasset 41 f** (3.2 cm), **Dead tasset 0.4 cm** 49 f; AttackMelee2 tasset 4.7 -> 3.5, flap counts lower |
| Skirt (older measure, 9 cm cap) | max 5.6-9.0 cm | 4.4-9.0 cm; leg population 1010 -> 821 vertices, so frame counts are not comparable (fewer); Walking 8.1 -> 9.0, AttackMelee 8.3 -> 8.8 |
| Jitter (vs `ref_half.glb`) | 0 fails | **1 fail: AttackMelee2 L shoulder skin 2.33 mm/f2** (limit 2.0; r18 0.22) |
| Jitter, same mesh (`ref_swap.py`: the reduced mesh with the reference clips) | 0 fails (max 1.65) | **1 fail: Hit L shoulder skin 2.62** (r18 1.54) |
| Shoulder skin, area-weighted p95 (`skin_jitter_area.py`) | Hit L excess 4.96, AttackMelee L 6.19, Death2 L 3.17 | 4.69, 7.26, 2.75 (peaks within 2 % of r18) |
| Detached | R thigh strap 1.93 cm (63/528 poses), chest shell 0.95 | strap 1.93 cm (**219/528 poses**), chest shell 1.03, **L pauldron half 0.91 cm in 4 poses** (new; reads attached in `review/sheet_detached_r85m.png`) |
| Bones, flat, winding, stride, orient | 0 of 20, 0.00, 0, -, - | identical |
| Texture quality | LizB atlas 49.8 %, fragments 0.2 % | 47.8 %, 1.5 % (decimated UV islands); head and cutlass unchanged |
| LODs (`lod_check.py`) | LOD0 height 1.8709 m, 32 stretched (neck strip) | LOD0 identical min z in every clip, 32 stretched; LOD2 1 face over 20x in Hit; LOD3 dips 10.9 mm under LOD0 (r18 9.7) |

The shoulder-skin term is a 95th percentile over the vertices dominated by the clavicle and upper-arm joints, pauldrons
included: a decimated mesh has a different population, and the two gate variants fail on different clips (r85c, same cut
without the elbow patches: standard AttackMelee2 L 2.40, same-mesh 0 fails). Weighted by area, the excess stays as it was.
Not fixed: keeping the shoulder skin exactly costs 1,134 faces, more than the margin to 15 %.

## Sheets (read)
`review/sheet_viewer_face_a.png`, `_b`, `_c` (viewer: front close-up, 3/4, profile, low 3/4, party; identical),
`review/sheet_viewer_body_a.png`, `_b`, `_c` (Standing front/3-4/back, Walking, AttackMelee), `review/sheet_face_tex.png`,
`review/sheet_full_tex.png`, `review/sheet_hands_tex.png`, `review/sheet_hands_clay.png` (r85, blade 0.6),
`review/sheet_hands_clay_b.png`, `review/sheet_hands_tex_b.png` (hands 0.6/0.65, rejected for the right fist),
`review/sheet_body_tex_r85c.png`, `review/sheet_body_clay_r85c.png`, `review/sheet_motion_tex_r85c.png`,
`review/sheet_drift_spots.png`, `review/sheet_detached_r85m.png`, `review/ladder_sheet.png`.

## Not checked
In game; binding regression (no install); motion at normal speed; the R thigh strap close-up (the camera framed the hip plates,
not the strap); tiers B and C in Blender close-ups (only in viewer shots).
