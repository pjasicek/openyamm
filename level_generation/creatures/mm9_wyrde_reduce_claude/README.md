# MM9 Wyrdes Morgan and Verdandi (`mm9_wyrde`, tiers wy_young / wy_mature) reduction: candidate c55 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (relaxed keep set, face exact;
prio-3 unique, reduced on the user's "do all" of 2026-11-05), ledger row 10 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:wyrde` (owner wyrde-reduce-20261105); the creature's own `mm9:wyrde` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_wyrde.glb` (r16, sha256 f56f8f2407e6, = `../mm9_wyrde_claude/export/`), copied to `before/`
(the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_wyrde_claude/` was only read (its gate scripts
are called read-only).

| | LOD0 | mantle | gown + sleeves | skirt | legs | hands | jewel | linings + rims (body) | head prim (face set exact) | head linings | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 14,932 | 1,699 | 2,597 | 1,028 | 600 | 1,470 | 899 | 776 | 5,032 | 831 | 7,460 | 2,670 | 879 |
| **c55 (`export/mm9_wyrde.glb` = `export/mm9_wyrde_c55.glb`, sha256 d1d47ed5e5c5)** | **12,384 (-17.1 %)** | 1,359 | 1,825 | 624 | 484 | 910 | 899 | 742 | 4,774 | 767 | 6,185 | 2,212 | 724 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers change). Clips (8), skin, nodes, materials, region ramps/mask, `KHR_materials_variants`, all 9 images: byte-identical
(`same_clips.py`). The face set is present triangle for triangle (`scripts/face_exact.py`: 4,247 of 4,247 kept head faces, 2,997
of 2,997 kept body faces), so both faces render pixel-identical (`review/diff_face_c55.png`: face black in every view).

## Protected share measured first (Igrid came out `kept` at 80 %)
Part labels: `scripts/glb_parts.py` matches every GLB face to the creature's last mesh (`../mm9_wyrde_claude/work/uv_tex4.npz`,
14,932 faces, distance 0; linings by UV + position + normal); head sub-labels from `seg_wy.py`'s labels and, because the seg
'hair' label also covers the neck and throat, from colour (`scripts/head_colour.py`: Verdandi paints hair and hood in her green
mantle colour, so every head face that is not green in her tier is face, neck, lips, circlet or jewel; checked in
`work/diag/head_col_sheet.png`). Unlike Igrid, the relaxed set leaves enough: set a kept 43.5 %, set c 48.5 % (+ the re-emitted
linings, 8.9 %).

Keep set (`scripts/make_sets_wy.py`, set c: `ARMC=1 THROAT=0.02,0.60`): the face (every non-green head face, seg face skin, eyes,
plus hair/hood within 8 mm), the throat (head cloth within 2 cm of the face set below y 0.60: a60's see-through head hole grew
6 -> 8 px at the neck side), the collar (body faces within 1 cm of a head vertex: the head-set seam and the hair lying on the
mantle), hand-in-sleeve (the MPFB forearm stub and sleeve faces within 2 cm of a hand vertex: the closed cuff caps), the whole
jewellery and cloth within 6 mm of it, region-mask border faces (mantle/gown/damask/cord/gold), arm contact (cloth faces an arm
comes within 2 cm of in any clip, `scripts/arm_contact.py`: a60 let the sleeve elbow 3.6 cm into the cut mantle in Walking), soles,
pieces up to 80 faces, rim strips, the 8 outer faces with a doubled or unreversed lining.
Groups: hands + fingers 0.6 (every finger, seam slides), head cloth 0.7, head cloth lined 0.75, lined body cloth 0.7 (guards
stopped at 269 of 212), skirt 0.6, shoes 0.6, hidden shins 0.85, mantle 0.6, gown at the ladder ratio.
Linings: `linings_wy.py`'s twins (outer face reversed, 2 mm behind, same UVs and weights) are re-emitted from the surviving outer
faces (1,327 twins matched, 0 twin-key clashes); rims kept exactly.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantF8's copy)
Texture guard over each tier's baked body colour, both tier head images and the region mask (RGB + the cord alpha as a fourth
image, `scripts/tex_extract.py`); chart guard (`MP_CHART=1`, sampled at 12) **and the audit's own chart test inside every collapse**
(`MP_AUDIT=1`, `reduction_uv_audit.Charts.test` at zero tolerance on the outer face and its lining twin); texture weight 4; scored
over 133 poses (every clip at 10 Hz) plus a position+UV rest quadric.

## Ladders (limits for 1.765 m: p99 <= 5.30 mm, max <= 26.5 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| a | a | r60 / r50 | 12,160 / 12,004 | 4.41 / 23.6 (Death:36), 6.03 / 41.6 | .996 / .996 | r60 pass, built a60: **rejected**: arm/hand gate forearm-in-body 0 -> 3.6 cm (Walking R, sleeve elbow inside the cut mantle), see-through head 6 -> 8 px |
| b | a + arm contact | r60 / r55 | 12,306 / 12,224 | 4.17 / 23.6, 4.87 / 23.6 | .996 / .996 | pass; arm/hand forearm back to 0.0 everywhere (LOD0 swaps) |
| **c** | **b + throat** | r60 / **r55** | 12,466 / **12,384** | 4.18 / 23.6, **4.87 / 23.6 (Death:36)** | **.9957 / .9958** | **PASS, picked** |

UV audit (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_c55.json`): **0 LOD0 faces leave the charts** in both
primitives. LOD1-3 (tool-built) body 156 / 159 / 73, head 53 / 117 / 93 (installed 104 / 160 / 110, 58 / 123 / 98).

## Gates, installed -> c55 (`review/gates_before/`, `review/gates_c55/`; the Wyrdes' own gate scripts via `scripts/gates.sh`)
- Arm/hand (`--outer-only --exact`): identical to installed in every clip (hands 0.4 / 0.7 cm, 0 frames > 1 cm, forearm 0.0, finger
  stretch maxima equal, minima up 0.01-0.16). Robe (legs through the skirt): 0 in every clip (installed Death 1/45 at 0.8 cm).
- Collapse face-frames lower in every clip but Standing (125 = 125) and Dead (1,023 =): Walking 732 -> 630, Hit 1,837 -> 1,690,
  Death 2,522 -> 2,212, Cower 1,140 -> 946; single-face worst-region rises: Walking armpit R 0 -> 1, Running waist 0 -> 1, Cower
  elbow R 0 -> 2.
- Linings through their cloth (`scripts/lining_gate.py`, new, every clip at 10 Hz): largest outward distance equal or lower in every
  clip (body Hit 5.13 -> 4.89 mm; head equal, Death 4.87); lining vertices > 0.5 mm out in the worst frame 9-22 as installed, +4 in
  Walking, -8 in Death (head).
- See-through (`scripts/see_through.sh`, every clip, 16 views; level / 20 deg max px): torso 26/26 = 26/26, collar 6/2 = 6/2,
  sleeve L 7/2 = 7/2, sleeve R 4/2 -> 2/2, head 6/5 -> 7/5 (Hit 39 side view, the throat edge; the creature's record "every zone
  <= 7 px except Death torso" still holds), boots 0; frames with any hole pixel collar 83 -> 91, sleeve L 71 -> 80 (1-2 px specks).
- Jitter: 2 fails both (Death shoulder skin 42.7 mm/f2, the installed model's own). Detached parts: the same 2 (the free legs, by
  design). Flat 0.01 / 0.00. Winding 0. Bone lengths 14, 0 stretching. Texture quality: body stretch p90 1.14 -> 1.16, head 1.15 -> 1.16.
- Sleeve poke: the Wyrdes' project did not run it (`sleeve_poke_pf1.py` needs F1's asm hem); the arm/hand forearm metric and the
  see-through sleeve zones cover the sleeves here.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/lod_summary.py installed c55`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; 68 sole/crown/corpse points protected and snapped): height 1.765 m at every LOD
  (installed LOD3 1.759); every clip's lowest point at LOD1-3 within 0.24 cm of LOD0 (installed LOD3 floated up to 0.52 cm);
  stretched faces equal except LOD2 Running 0 -> 1.

## Review
Viewer (installed and reduced, both tiers, all 8 clips; `run_creature_review.py check`: 32 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_wyrde_reduce_claude/review/viewer/ (revision r2-c55-20261105)
Sheets read (full size): `review/sheet_face_c55.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers),
`review/diff_face_c55.png` (face black; hood rim and back-of-neck shading differ), `review/sheet_body_c55_{a,b}.png` (Standing
front/3-4/back, Walking, Fidget, Death), `review/crop_torso_c55.png`, `review/close_c55_{a,b}_hands.png`, `review/close_c55_{a,b}_1.png`
(arms, Fidget arms, mantle from behind, Hit), `review/close_c55_{a,b}_2.png` (gown front, mantle back, Running, underskirt hem, hood
top); a60 (same cut minus the arm/throat keeps): `review/sheet_face_a60.png`, `review/close_a60_*`, `review/crop_torso_a60.png`.
Look at: the fingertips (hands 0.6: slightly more angular tips, as PF8/PF3), the mantle's shoulder fold from behind (faint shading
change), the hood rim silhouette in profile.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_wyrde_reduce_claude/before/mm9_wyrde.glb REA_NODE=Wyrde $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/head_colour.py; $G scripts/arm_contact.py 0.02
THROAT=0.02,0.60 ARMC=1 $G scripts/make_sets_wy.py c
MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.6,2:0.7,3:0.75,4:0.7,5:0.6,6:0.6,7:0.85,8:0.6,9:1.0 scripts/mp_only.sh c 0.6,0.55
SKIP_MP=1 scripts/run_mp.sh c 0.6,0.55            # reduce_ladder + compare_ladder
scripts/build_mp.sh mp_c_r55 export/mm9_wyrde_c55.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_wyrde_c55.glb before/mm9_wyrde.glb --json review/uv_audit_c55.json
$G scripts/face_exact.py export/mm9_wyrde_c55.glb c; scripts/gates.sh export/mm9_wyrde_c55.glb c55
$G scripts/lining_gate.py export/mm9_wyrde_c55.glb review/gates_c55/lining.json; scripts/see_through.sh export/mm9_wyrde_c55.glb c55
REA_NODE=Wyrde $BL -P scripts/lod_check.py -- $PWD/export/mm9_wyrde_c55.glb c55; python3 scripts/lod_summary.py installed c55
$G scripts/viewer_tiers.py export/mm9_wyrde_c55.glb redc55   # installed: viewer_tiers.py before/mm9_wyrde.glb inst
$G scripts/make_viewer_manifest.py <rev> inst_a=..=work/viewer_inst_th_young.glb red_a=..=work/viewer_redc55_th_young.glb inst_b=.. red_b=..
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py c55; $G scripts/close_sheet.py c55 <a|b> <shots> <out>
```

Install (orchestrator, on the OK): `check_winding.py export/mm9_wyrde.glb` (0), `tools/install_model.py export/mm9_wyrde.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_wyrde_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_wyrde_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_wyrde.glb`.

## Not checked
In game (not installed; binding regression and floor audit after install are the orchestrator's); motion at normal speed by eye
(viewer stills at Standing, Walking, Fidget, Hit, Running, Death and the numeric gates only); LOD1-3 and shadow meshes by eye
(numbers only); Cower and Dead in close-up (gates only).
