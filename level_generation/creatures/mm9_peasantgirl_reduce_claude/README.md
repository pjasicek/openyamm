# MM9 peasant girls (`mm9_peasantgirl` = Girl2 / Girl3, `mm9_peasantgirl1e` = Girl1e) reduction: candidate b r60 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: the relaxed
prio-1 keep set, face exact; one agent per GLB family, the shared body reduced once and the variants re-derived from that cut), ledger
rows 15 (elf) and 20 (human) of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantgirl` (owner
peasantgirl-reduce-20261104); the creature's own `mm9:peasantgirl` lease was free. Sources: the installed
`assets_source/worlds/mm9/models/mm9_peasantgirl.glb` (sha256 5ec5cbd18214) and `mm9_peasantgirl1e.glb` (sha256 86cecd0218ec), both
identical to `../mm9_peasantgirl_claude/export/`, copied to `before/` (the rollback sources). No Meshy, no credits, no repaint.
**Not installed.** `../mm9_peasantgirl_claude/` was only read.

## What the two files share (measured, `scripts/derive_human.py` asserts it)
- **Body primitive** (`PeasantGirl_G2` / `PeasantGirl_G1E`; dress, skirt + apron, lining, hands, legs, buttons): byte-identical in the
  two files (positions, normals, UVs, joints, weights, indices; 7,160 faces, 5,406 vertices). Only the material (ramps) differs.
- **Head primitive** (`PeasantGirlHead`): the human head's 3,613 vertices are the elf head's first 3,613 (all attributes equal) and its
  6,590 faces are the elf faces in the same order without the 588 elf-ear faces (the ears are a separate piece on vertices 3,613+).
  The head images differ per girl (g2 / g3 in the human file, g1e in the elf file); the head UVs are the same.
- Clips, skeleton, node TRS: identical (hash of samplers and nodes).

So the family is one mesh: the elf file is the superset. **One cut** (`scripts/mpqem.py` on `before/mm9_peasantgirl1e.glb`, ears kept)
gives the elf candidate as is and the human candidate by dropping the (untouched) ear faces and renaming the body material
(`derive_human.py`). The two candidates' body index buffers are identical; their head buffers differ only by the ear faces. Each file's
LOD1-3 are then built from its own LOD0, as the creature project built them.

| | LOD0 | head skin + eyes | ears | hair | dress | skirt + apron | lining | hands | legs | buttons | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed human | 13,750 | 5,296 | - | 1,294 | 1,964 | 1,444 | 1,636 | 1,464 | 560 | 92 | 6,867 | 2,468 | 820 |
| **b r60 human (`export/cand_b60/mm9_peasantgirl.glb`, sha256 eb97a2d05c1a)** | **10,658 (-22.5 %)** | 5,042 | - | 966 | 1,284 | 868 | 1,060 | 910 | 436 | 92 | 5,323 | 1,914 | 633 |
| installed elf | 14,338 | 5,296 | 588 | 1,294 | 1,964 | 1,444 | 1,636 | 1,464 | 560 | 92 | 7,161 | 2,574 | 855 |
| **b r60 elf (`export/cand_b60/mm9_peasantgirl1e.glb`, sha256 5e73685ae92f)** | **11,246 (-21.6 %)** | 5,042 | 588 | 966 | 1,284 | 868 | 1,060 | 910 | 436 | 92 | 5,617 | 2,020 | 669 |

(Head skin 5,296 -> 5,042: only the scalp under the hair, 508 -> 254; every face-skin, eye, neck and ear triangle is the installed one.)

Every vertex of both candidates is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (9), skin, nodes, materials, region ramps, `KHR_materials_variants`, all images: byte-identical
(`same_clips.py`, both files).

## Keep set (`scripts/make_sets_pg.py`, set b with `SCALP=0.025`)
Part labels per face from the creature's last mesh before the GLB (`../mm9_peasantgirl_claude/work/uv_tex2.npz`, `scripts/glb_parts.py`;
exact centroid match, mirrored x). Protected share before the cut: 45.5 % of the elf LOD0.
- Exact: the whole head part except the scalp under the hair (face skin, eyes, lids, brows, nose, mouth, ears' root, jaw, chin, neck down
  to the level neck seam), the elf ears, the buttons, pieces up to 40 faces.
- Exact: the collar (dress faces within 1 cm of a head vertex: the neck seam), the bell cuffs and their caps (dress faces within 2.5 cm of
  a hand vertex), the hand-graft junction (hand faces within 1.2 cm of a dress vertex plus the Forearm-dominated MPFB stub), the soles
  (leg faces within 1.2 cm of the floor), the hairline (hair faces within 1.5 cm of the hair shell's open edges: tweak_pg's sunk band) and
  the hair round the elf ears (within 1.2 cm of an ear vertex).
- Exact: the lining's rim strips (hem, apron edge) and the waist cap (196 faces), and the 4 skirt faces without a lining twin.
- **Scalp under the hair** (`scripts/scalp_dist.py`): head-shell faces whose normal ray meets the hair within 4 cm and that lie more than
  2.5 cm from the hair's open edges (508 faces): group 5 at 0.5. Vertex removal only takes surface chords, so the scalp moves inward
  under the hair, never out through it.
- Groups: 1 hands + fingers 0.6 (seam slides, every finger segment keeps faces: smallest R pinky middle 18 -> 7), 2 hair 0.65, 3 skirt +
  apron 0.6 (lining re-emitted), 4 shoes 0.7, 5 scalp 0.5, 7 hidden shins 0.7; 0 = dress (bodice, vest, sleeves) at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, from PeasantF3's copy)
Scored over 182 poses (every clip at 10 Hz) plus the position+UV rest quadric, texture weight 4 (`MP_W5`), the chart guard sampled at 12
(`MP_CHART=1`), seam slides on the hands. Changes for this family:
- **Texture guard over every tier of both files** (`scripts/tex_extract.py`): body = the shared tone with each tier's region ramps (g2,
  g3 from the human file, g1e from the elf file) plus the region mask; head = the three girls' head images. A collapse is refused if any
  tier would show colours the source does not have there (the gold-blend vest ramps of g3 / g1e included).
- **Skirt lining re-emitted from the cut skirt** (`scripts/lining_twins.py`): assemble_pg's lining is a 4 mm inner copy of the skirt with
  reversed faces; 1,440 of 1,444 skirt faces matched their lining face topologically (seeded by the 4 mm prediction, propagated over
  faces; residual median 0.1 mm). The lining has its own UV seams (120 classes where the skirt has none), so each re-emitted lining face
  takes the lining vertex copies on ONE lining chart (`Lining.face`), and a collapse is refused when a re-emitted face would have no
  common chart, flip its UV triangle or leave the charts. Lining 1,440 -> 864 twins (+ 196 kept rim / cap faces).

## Ladders (limits for 1.294 m: p99 <= 3.88 mm, max <= 19.4 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / groups | step | elf LOD0 | human LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---:|---|---|---|
| a | a: hands .6, hair .7, skirt .7, shoes .7, shins .85 | r60 | 11,858 | 11,270 | 2.52 / 18.47 (Cower:21) | .9957 / .9940 | pass |
| a | | r50 / r45 | 11,744 | 11,156 | 3.71 / 24.23 (Cower:18) | .9904 / .9922 | fail (the dress saturates at 904 of 1,698 free faces: guards) |
| **b** | **b: a + scalp .5, hair .65, skirt .6, shins .7** | **r60** | **11,246** | **10,658** | **2.84 / 18.47 (Cower:21)** | **.9955 / .9939** | **PASS, picked** |
| b | | r55 | 11,162 | 10,574 | 3.37 / 22.66 (Hit:21) | .9943 / .9931 | fail |

## Gates, installed -> b r60 (the girls' own scripts, `scripts/gates.sh`; `review/gates_before_{h,e}/`, `review/gates_b60_{h,e}/`)
Body and clips are identical in the two files, so the body gates agree between them (run on both; numbers below hold for both unless
marked).
- **UV chart audit (hard gate, `claude_shared/reduction_uv_audit.py`)**: LOD0 **0 escaping faces in every node, both files**
  (`review/uv_audit_human.json`, `review/uv_audit_elf.json`). LOD1-3 (the tool's LODs, not gated): body 203 / 141 / 51 escaping
  (installed LODs 154 / 155 / 92), head human 20 / 38 / 36 (installed 20 / 40 / 33), elf 18 / 44 / 35 (installed 20 / 40 / 31).
- Collapse (face-frames) lower in every clip (Hit 2,864 -> 2,577, Death 1,688 -> 980, Cower 1,613 -> 954, Fidget 521 -> 122).
- Arm/hand (`--outer-only --exact`): 0 frames > 1 cm in every clip, both; hand depth equal (Hit L 0.8, Cower L 0.7 cm); forearm Hit L
  0.0 -> 0.2 cm, Talk R 0.6 -> 0.5 cm; finger stretch maxima equal.
- Sleeve poke (this project's copy, labels by vertex key; identical output on the installed file to the creature's script): equal in
  every clip (Hit L 2.6 mm, 16 frames, 2 vertices; all others 0).
- Robe: the nearest-plane gate flags more frames (Talk 10 -> 69, Hit 13 -> 30 at 2.0 -> 2.3 cm, Death 18 -> 36 at 1.8 -> 3.8 cm); the
  creature's ray re-check (`robe_ray_check.py`, the README's reliable test for the deep folds) finds **0 really outside in every living
  clip** (installed 0), Death 2 -> 4 vertex-frames at the same 1.8 cm (the shin knee ends under the gathered corpse skirt during the
  fall), Dead 0.
- Lining through the skirt (`scripts/lining_gate.py`, waist-cap interior left out): largest outward distance equal or lower in every clip
  except Dead 2.93 -> 3.66 mm; frames equal, vertices out equal or fewer.
- Jitter vs the creature's `ref_half_{h,e}.glb`: 1 fail both before and after (Death shoulder skin 50.14 -> 50.15 mm/f2, the installed
  model's own).
- See-through (`scripts/see_through.sh`, the girls' `see_through_gate.py`, every clip, 16 views; hole max px level / 20 deg): living clips
  at most 8 px both (Walking torso 4 -> 6, collar 0 -> 3); party 20 deg at most 8 px both; corpse seen from the feet at floor level (the
  installed hollow-dress construction: the same thin arc of the bodice inside the fallen skirt, `review/see_sleeveL_compare_b60.png`):
  Death sleeve L 41 -> 62, collar 30 -> 38, torso 19 -> 11; Dead sleeve L 5 -> 17, collar 29 -> 31.
  The elf file gives the same numbers in every clip and zone (`review/gates_{before,b60}_e/see_through.json`).
- Detached parts: the same 4 (shins and shoes, free inside the skirt by design), same worst distances. Flat shading body 0.01 both; head human 0.00 -> 0.01, elf
  0.01 both. Winding 0 both. Bone lengths: same report. Texture quality: body stretch p90 1.06 -> 1.08, head 1.63 (elf 1.69 -> 1.68).
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{inst,b60}_{h,e}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5 / 0.18 / 0.06, 4 influences; soles, crown and corpse contact protected, 55 points, each snapped to the imported
  vertex): height 1.2942 m at every LOD (installed LOD3 1.2913); every clip's lowest point at LOD1-3 equal to LOD0 within 0.1 cm except
  Running (LOD0 +0.60 cm in the air at its lowest; LOD1 +0.72, LOD2 +1.23, LOD3 +0.71; installed LOD2 +0.63, LOD3 +1.50); LOD3 Death
  -0.05 cm (installed -0.25), Dead 0 (installed +0.03); stretched faces LOD0 2 (both), LOD2 1 (installed 0).

## Review
Viewer (installed and reduced, all three tiers (Girl2, Girl3 from `mm9_peasantgirl`, Girl1e from `mm9_peasantgirl1e`), all 9 clips;
`run_creature_review.py check`: 54 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantgirl_reduce_claude/review/viewer/  (models `inst_g2` / `red_g2`, `inst_g3` /
`red_g3`, `inst_g1e` / `red_g1e`; ramps baked per tier by `scripts/viewer_tiers.py` from each file's own materials).
Sheets read: `review/sheet_face_b60.png` (front close-up, 3/4, true profile, low 3/4, party; all three girls) and
`review/sheet_face_diff_b60.png` (face skin black in all 15 views; differences only on the hair beside the neck, the hair outline and the
bodice below the neckline), `review/sheet_body_b60_{g2,g3,g1e}.png` (Standing front / 3-4 / back, Walking, Talk, Death),
`review/close_b60_<tier>_vest.png` (vest front, 3/4, bodice back: the gold embroidery, lacing, trims and belt identical in every tier; the
plain cloth's faceted shading slightly rearranged), `review/close_b60_<tier>_hands.png` (both hands outside, R hand front, L cuff),
`review/close_b60_<tier>_1.png` (arms 3/4, skirt front / back, Running skirt, skirt cloth), `review/close_b60_<tier>_2.png` (feet, Talk,
shoulders from behind, Hit, hair from behind and from above), `review/ladder_sheet_{a,b}.png`, `review/see_sleeveL_compare_b60.png`.
Look at: the fingertips and knuckles in close-up (hands at 0.6: a little more angular, every finger kept), the bodice side panels' shading
in 3/4 (vest pattern unchanged), the hair strands beside the neck in the front close-up.

## Not checked
In game (not installed; binding regression and floor audit run after install, by the orchestrator); motion at normal speed by eye
(frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face
triangles are the installed ones and the five-view face diff is black); the hem close-up (c14) framed the skirt cloth above the hem.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantgirl_reduce_claude/before/mm9_peasantgirl1e.glb REA_NODE=PeasantGirl $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/lining_twins.py; $G scripts/scalp_dist.py
SCALP=0.025 $G scripts/make_sets_pg.py b
MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=b MP_GROUPS=1:0.6,2:0.65,3:0.6,4:0.7,5:0.5,7:0.7 scripts/run_mp.sh b 0.6,0.55
scripts/build_mp.sh mp_b_r60 b60   # derive_human -> per file: swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/cand_b60/mm9_peasantgirl.glb before/mm9_peasantgirl.glb --json review/uv_audit_human.json
$G ../claude_shared/reduction_uv_audit.py export/cand_b60/mm9_peasantgirl1e.glb before/mm9_peasantgirl1e.glb --json review/uv_audit_elf.json
scripts/gates.sh export/cand_b60/mm9_peasantgirl.glb b60_h h; scripts/gates.sh export/cand_b60/mm9_peasantgirl1e.glb b60_e e
$G scripts/lining_gate.py export/cand_b60/mm9_peasantgirl.glb review/gates_b60_h/lining.json; scripts/blender_queue.sh b60  # see-through + LOD checks
for x in "before/mm9_peasantgirl.glb inst" "before/mm9_peasantgirl1e.glb inst" "export/cand_b60/mm9_peasantgirl.glb red" "export/cand_b60/mm9_peasantgirl1e.glb red"; do $G scripts/viewer_tiers.py $x; done
$G scripts/make_viewer_manifest.py b60 inst_g2=..=work/viewer_inst_pg_g2.glb red_g2=..=work/viewer_red_pg_g2.glb ... (g3, g1e)
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py b60; $G scripts/face_diff_sheet.py b60; $G scripts/close_sheet.py ...
```
Install (orchestrator, on the OK; both files together so the family stays consistent): `check_winding.py` (0 both),
`tools/install_model.py export/cand_b60/mm9_peasantgirl.glb --world mm9` and the same for `mm9_peasantgirl1e.glb`, the
`mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantgirl_claude/README.md`: "LOD0 reduced post-install on
<date> by `mm9_peasantgirl_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_peasantgirl.glb`,
`before/mm9_peasantgirl1e.glb`.
