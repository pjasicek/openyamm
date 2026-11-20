# MM9 PeasantF7 (`mm9_peasantf7`, Peasant Elf FemaleB / FemaleC) reduction: candidate f r45 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk, relaxed
keep set), ledger row 11 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf7` (owner
peasantf7-reduce-20261104); the creature's own `mm9:peasantf7` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantf7.glb` (r37, sha256 43d0cff97cce), copied to `before/` (the rollback source). No Meshy,
no credits, no repaint. **Not installed.** `../mm9_peasantf7_claude/` was only read.

| | LOD0 | body set `PeasantF7_A` | head set `PeasantF7Head` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 14,770 | 8,736 | 6,034 | 7,373 | 2,653 | 883 |
| **f r45 (`export/mm9_peasantf7.glb`, sha256 e18c2d45c421)** | **10,246 (-30.6 %)** | 5,196 | 5,050 | 5,111 | 1,837 | 609 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (11), skin, nodes, materials, region mask + ramps, `KHR_materials_variants` (carried to every LOD and shadow
primitive), doubleSided head materials and all 8 images are byte-identical (`same_clips.py`). The whole head shell (face, eyes,
lids, nose, mouth, scalp, neck and the neck seam) is the installed triangles: the face diff sheets are black on face and neck in
both tiers and every view.

Per part (installed -> f r45): head shell 2,825 -> 2,825 (exact); hair shell 1,578 -> 1,344 (rim lining 341 and the 259 faces in
front of it exact, hairline exact, the rest at 0.75); braids 1,631 -> 881 (0.5; faces within 6 mm of the head exact); dress +
sleeves + skirt outer 3,594 -> 1,890 (sleeves 0.6, the rest at the ladder ratio 0.45; neck seam exact); MPFB arms + hands 3,590 ->
1,928 (hands 0.5 with every finger, forearm 0.55, the upper arm hidden in the sleeve 0.4, skin under and beside the bracelets
exact); legs 760 -> 586 (soles and the shin tops inside the skirt exact, rest 0.4); exact: bracelets 384, skirt inner hem wall and
shin floor 306, the zero-UV caps 102.

## Measured first: protected share
Part labels come from the creature's own build mesh (`scripts/pf7_parts.py` matches every GLB face to
`../mm9_peasantf7_claude/work/uv_lined.npz`: head, dress, skirt, hair, legs, hands, bracelets, braids, `inner` linings/caps; every
face within 1 mm except 150 hair faces (up to 2 mm) and the braids, which the build moved ~5 mm after that file). Keep set f (`scripts/make_sets_pf7.py`) is
35.4 % (5,232 faces): head shell, caps, hair lining + lined faces, skirt inner wall, bracelets, soles (leg faces within 1.2 cm of the
floor), the bracelet skin (1.2 cm), the neck seam (non-head faces within 1.5 cm of the head shell's open border), the hairline
(hair/braid faces within 6 mm of the head shell) and the shin tops (leg faces above y -0.71, inside the skirt: without them the
detached audit found the right shin floating free of the skirt in 11 poses, up to 1.25 cm, in d45). So ~30 % was reachable.

## Route: pose-aware half-edge collapse (`scripts/mpqem_chart.py`, the Mummy's copy of the Lesser Demon's `mpqem.py`)
Scored over every clip at 10 Hz (291 poses) plus a position+UV rest quadric with texture weight 4 (`MP_W5`); only removes vertices;
texture guard 70/30 on the body base colour + region mask and both head tiers; seam slides on hands, hair and braids; **chart guard**
(`MP_CHART=1`: new UV triangles stay on the source charts) and stretch guard (`MP_ANISO=1.6`). The first ladders (a, c) used the
Honk copy without the chart guard: a r50 had 24 faces leaving the charts (8 on the fingers, 16 on hair crown and braids, from
seam slides); with the guard, d, e and f have 0 (`uv_escape.py`, threshold 2 % of a face's samples; worst 1.1 % on one head face in d).

## Ladders (height 1.758 m: p99 <= 5.27 mm, max <= 26.4 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | groups (hand, hair, braids, legs, forearm, upper arm, sleeve) | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | .7 .7 .7 .5 .65 .5 .75, no chart guard | r60 / r50 | 11,472 / 11,232 | 2.80/22.3, 3.75/22.3 | .997/.991 at r50 | pass; 24 faces off the UV charts |
| c | .5 .6 .5 .4 .55 .4 .6, no chart guard | r45 / r40 | 10,020 / 9,900 | 4.81/22.3, 5.71/22.5 (Death) | .995/.990, .993/.989 | pass / fail |
| d | c + chart/stretch guards, W5 4 | r50 / r45 | 10,142 / 10,020 | 4.14/22.3, 4.77/22.3 | .994/.990 at r45 | pass; built d45: crown silhouette stepped (hair .6), right shin detached |
| e | d, hair .75 | r45 | 10,160 | 4.73/22.3 | .994/.990 | pass; crown back to the installed outline |
| **f** | e + shin tops kept | **r45** | **10,246** | **4.45 / 21.7 (Running)** | **.994 / .990** | **PASS, picked** |
The 22 mm maximum is the same single point in every ladder (also at r60) and at 0.6-0.45 of the cloth.

## Gates, installed -> f r45 (`scripts/gates.sh`, the creature's own gate scripts; `review/gates_before/`, `review/gates_f45/`, `review/gates_compare_f45.txt`)
- Collapse face-frames 10,877 -> 8,853, lower or equal in every clip except Running 202 -> 209 (torso 1 -> 2 faces at its worst
  frame); single-face rises: Conv1 scarf 2 -> 3, Conv3 waist 3 -> 4, Cower armpit_L 0 -> 1 and head 2 -> 3; the rest lower
  (Cower 2,429 -> 1,707, Hit armpit_R 43 -> 33, Death skirt 18 -> 9).
- Robe (legs through the skirt, cords): 0 in every clip, identical. Sleeve poke (MPFB upper arm through the short sleeve): 0.0 mm
  in every clip both sides, identical.
- Arm/hand (`--outer-only --exact`): hand and forearm in body 0.0 cm, 0 frames over 1 cm, every clip, both sides (identical);
  finger-stretch p99 max L 1.32 -> 1.37, R 1.23 -> 1.32 (hands at 50 %: fewer finger vertices), maxima equal or lower (L 2.53 -> 2.52,
  R 3.30 -> 3.30).
- Jitter (against the creature's `work/ref_half.glb`): 2 fails before and after (the runtime clips: the creature's README ran it on
  its pre-runtime `half.glb`, 0 fails); clips are byte-identical.
- Detached parts: identical findings (left shin free inside the closed skirt by design, as installed). Bone lengths 0 stretching.
  Winding 0 (the creature's `fix_winding.py` reversed 2 thin closed pieces in LOD3 shadow, as its own build does). Flat shading 0.00 /
  0.00. Texture quality: body stretch p90 1.13 -> 1.15, head 1.07 -> 1.08; atlas, density, islands unchanged. UV escape 0 / 0.
- See-through (`double=1`, 8 az x 0/20 deg, step 6): worst hole per zone equal or lower in most clips (torso worst 48 -> 47 px in Death, Dead 40 -> 36, Hit sleeve R 3 -> 0); single-frame rises of 1-3 px: Hit collar 0 -> 3 px (1 frame), Conv3 sleeve R 0 -> 1, Death sleeve L 0 -> 1, Fidget sleeve R 0 -> 1, Talk sleeve R 0 -> 1, Running torso 16 -> 17; head 0 -> 0 holes (the gate's `inside` view into the Running left sleeve opening 1 -> 15 px, not a hole). Per clip and zone in `review/gates_compare_f45.txt`
- LODs (`lod_check.py`, every frame of every clip; `work/lod_check_{before,f45}.json`), built by `scripts/build_lods.py` with the soles,
  the crown and the floor contact of Death and Dead every 0.1 s as protected points (snapped to the imported vertices: 131 of 131
  mapped): height 1.7559 m at every LOD (installed LOD3 1.7532); every LOD's lowest point equals LOD0's in every clip (installed LOD2
  stood up to 0.5 cm and LOD3 up to 0.9 cm off the floor in Walking/Running/Standing). Faces stretched over 20x: LOD0 as installed
  (Dead 1, Death 2, Running 2, Walking 2), LOD1/LOD2 0, **LOD3 1 in Death, Hit, Running and Walking** (installed LOD3 0).

## Deviations from the brief (for the pre-screen)
- **Hands at 0.5** (the relaxed set says 0.6-0.75): the MPFB hands are very dense (2,556 faces); every collapse down to 0.5 cost at
  most 0.04 mm rms over all 291 poses, arm/hand gates are identical, finger-stretch p99 rose slightly. The fingertips read a little
  more pointed in the close-ups (`review/close_f45_b_1.png` c0). Fallback: hands 0.7 adds ~500 faces (a r50 had them at 0.7).
- **Braids at 0.5** (the brief's full keep set kept braids exactly; the relaxed list names only hair/hood/beard shells): the
  procedural plait tubes cost at most 0.03 mm rms; the braid faces within 6 mm of the head stay exact; the plaits read the same in the
  face sheets and chest close-ups. Fallback: braids 0.7 adds ~300 faces.

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf7_reduce_claude/review/viewer/
(models `inst_a/b`, `red_a/b`; ramps baked into the viewer copies by `scripts/viewer_tiers.py` from the creature's `pf_ramps.json`).
Sheets read: `review/sheet_face_diff_f45.png` (front close-up, 3/4, true profile, low 3/4, party; installed | reduced | diff x4;
both tiers), `review/crop_f0_f45_{a,b}.png` (crown and face full size), `review/sheet_body_f45_b.png` (Standing front/3-4/back,
Walking, Conv3, Death; tier A for d45: `review/sheet_body_d45_a.png`), `review/close_f45_{a,b}_{1,2}.png` (both hands, Conv3 hand, crown from above, hair from behind, dress back,
chest/lacing/necklace, left sleeve and bracelet from below, hem in Walking, Death, braids on the chest, Fidget hair fling),
`review/ladder_sheet_a.png` (written, not read: `ladder_sheet_{c,d,e,f}.png`), and for the rejected d45 `review/sheet_face_diff_d45.png`, `review/close_d45_{a,b}_{1,2}.png`,
`work/crown_cmp.png` (installed | d45 | e45 crown). Written, not read: `review/sheet_face_f45.png`, `review/sheet_body_f45_a.png`.
Look at: the fingertips up close (hands at 50 %: the index and thumb tips read a little more pointed), the crown outline from the
front (hair at 75 %), the braid tufts on the chest, tier B's laced corset (texture guard kept the motifs; cloth at 45 %).

## Build
`scripts/reproduce.sh` (import_source -> dump_mesh -> tex_extract -> pf7_parts -> make_sets_pf7 a -> leg-top keep -> make_sets_pf7 f
-> mpqem_chart f 0.45 + ladder -> build_mp.sh: swap_mp -> doubleSided off -> build_lods.py -> the creature chain's
shrink_shadow_lods (skeletonwarrior) -> doubleSided restored -> carry_variants -> the creature's fix_winding -> check_winding).
`tools/build_actor_lods.py` refuses merged shadow geometry across different face culling, so the doubleSided flags are cleared for
the LOD build and restored by material name from the installed file (the creature's chain sets them after its LODs,
`double_head.py`). Gates: `scripts/gates.sh <glb> <tag> noblender`, then `scripts/blender_gates.sh` (LOD check; see-through with
`ST_ARGS=step=6`; `scripts/see_through_gate.py` is the creature's gate with a re-render when a PNG reads back empty), and
`gate_compare.py <tag>`. Viewer: `viewer_tiers.py`, `make_viewer_manifest.py`, `shots.sh`, `close_shots.sh`, `shot_sheets.py`,
`face_diff_sheet.py`, `pair_sheet.py`.

Install (on the OK only): `check_winding.py export/mm9_peasantf7.glb` (0), `python3 tools/install_model.py
level_generation/creatures/mm9_peasantf7_reduce_claude/export/mm9_peasantf7.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, `floor_audit.py --world mm9` for MM9 18 / MM9 20, the ledger row, and the line in `../mm9_peasantf7_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_peasantf7_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_peasantf7.glb`.

## Not checked
In game (not installed; no map places rows 18/20 yet); motion at normal speed (frames, gates and viewer stills only); LOD1-3 and
shadow meshes by eye (numbers only); the LOD3 stretched face by eye; the collapse gate's single-face rises by eye; floor audit and
binding regression (they read the installed file).
