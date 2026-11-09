# MM9 Yanmir (`mm9_yanmir`, frost giant king, boss of Yanmir's Fort) reduction: candidate c r60 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact; prio-3
unique reduced on the user's 2026-11-05 "do all"), ledger row 13 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:yanmir` (owner yanmir-reduce-20261105); the creature's own `mm9:yanmir` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_yanmir.glb` (sha256 415329e5de92, = `../mm9_yanmir_claude/export/mm9_yanmir.glb` r5), copied to
`before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_yanmir_claude/` was only read.

| | LOD0 | body prim (skin, mantle, armour, MPFB hands) | head prim (face, hair, beard, eyes) | acc prim (staff, crown) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 14,514 | 7,700 | 4,222 | 2,592 | 7,238 | 2,603 | 866 |
| **c r60 (`export/mm9_yanmir.glb`, sha256 6635f04028a6)** | **11,382 (-21.6 %)** | 5,384 | 3,624 | 2,374 | 5,673 | 2,041 | 677 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (23), skin, nodes (incl. the `Ystafftop` cast socket), materials, all 9 images: identical (`same_clips.py`).
No emissive or glow parts on this model.

## Kept exactly (`scripts/make_sets_yan.py c`, `RFIST=1 CONTACT=Death2:0.8:2.0 KEEPCLS=24`; 42 % of LOD0)
Checked face by face against the installed file (`scripts/kept_check.py`: 0 missing): face skin with the mustache, the upper beard
next to the mouth, both ears and the forehead under the crown (1,540), eyes (150), the head's neck-seam ring (540) and the body's
(384, incl. the Head/Ponytail-weighted throat under the beard); wrist graft (86, any Forearm weight), the grip pads (148, R finger faces
within 6 mm of the staff) and the **whole right fist's fingers** (767); soles (152); body faces the hands/forearms touch in Death2
0.8-2.0 s (180); the staff head (cup, four knotwork petals, ring, gem: 1,192), the shaft within 3 cm of the fist (76), the staff foot
(160), the crown band (512) and its 12 ice spikes (216). Class renders: `review/classes_b/` (face/hair/beard split read at full size).
Cut (half-edge, pose-aware): body rest at the ladder ratio, hands (left hand, right palm/back) 0.65 with seam slides and every finger
kept, hair shell (back and side locks behind the ears, top under the crown) 0.7, lower beard 0.7, staff shaft 0.5.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantF3's copy)
Scored over 399 poses (every clip at 10 Hz); chart guard `MP_CHART=1` (12 subdivisions), texture guard over each primitive's base
colour (no tiers, so A = B = M = base colour; `scripts/tex_extract.py`), texture weight `MP_W5=4`, seam slides on the hands.
Yanmir change: `MP_NOQ_GROUPS` skips the triangle-quality test for the rigid shaft (its 12.6 x 1.4 cm sliver quads refused every
collapse in ladder a). The staff was not rebuilt: shaft 436 -> 218 by collapse keeps its UVs and paint, the rest of it is detailed
(knotwork petals) and kept.

## Ladders (limits for 2.86 m: p99 <= 8.58 mm, max <= 42.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b,c}.png`)
| ladder | change | step | LOD0 (GLB) | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | set b: groups hands .65, hair .7, beard .7, crown band .6, shaft .5 (shaft blocked by the quality test) | r60 / r50 / r45 | 11,072 / 10,628 / 10,628 | 6.73/37.1 (Fall:6); 16.06/51.9 (Death2) | pass / fail / fail (body saturates at 50 %) |
| b | a + shaft without the quality test | **r60** / r55 | 10,854 / 10,624 | 6.76/37.1; 9.49/38.6 | pass / fail. Built b60: crown band knotwork medallions slid along the band (`review/crop_crown_b60.png`) -> band spliced back exact = c60 pre (11,042, `scripts/splice_keep.py`) |
| **c** | b + crown band, right fist fingers, Death2 arm contact kept | **r60** / r57 | **11,382** / 11,250 | **6.89 / 37.1** (IoU .9947, SSIM .9933) / 8.39/38.6 | **PASS, picked** / pass (taken r60: r57 sits at the p99 limit for 0.9 %) |

Why ladder c: on the pre-c build (11,042) the staff gate's finger-wrap medians fell 15-30 deg on index/middle/ring in most clips and the
arm/hand gate's Death2 left hand went 4 -> 7 frames over 1 cm (forearm 2.9 -> 3.2 cm). Both are back to the installed values in c r60.

## Gates, installed -> c r60 (Yanmir's own scripts via `scripts/gates.sh`; `review/gates_before/`, `review/gates_final/`)
- **UV audit** (`claude_shared/reduction_uv_audit.py`, `review/uv_audit_c60f.json`): **LOD0 0 escaping faces** in Yanmir, YanmirHead,
  YanmirAcc. LOD1-3 (the builder's decimate): body 263 / 281 / 98 (installed LOD 150 / 260 / 174), head 111 / 101 / 69 (88 / 118 / 88),
  acc 2 / 7 / 1 (0 / 4 / 0).
- Collapse face-frames lower in every clip (Standing 1,157 -> 992, Wipe 8,495 -> 6,479, Death2 7,265 -> 5,390).
- Jitter (vs `../mm9_yanmir_claude/work/yan_ref_clips.glb`): 17 -> 17 fails strict, 14 -> 14 relative (on the runtime GLB; the
  creature README's 7 were on its pre-LOD clips file).
- Arm/hand (`--outer-only --exact`): identical in every clip (Death2 L hand 3.5 cm 4 f, R forearm 6.0 cm, the installed values);
  finger stretch p99 up to +0.25, maxima equal (7.13).
- Staff (`staff_gate.py`): staff in body equal in every clip (AttackMeleeSave 6.0 cm, installed); grip inside equal (Death 1.98 vs 1.96,
  Death2 1.87 vs 1.9); finger wrap medians equal or higher in most clips, a few single fingers -15 deg (Running middle 127 -> 112, Fall and
  AttackRanged2 pinky 105 -> 90, Death2 middle 165 -> 135) with the finger faces byte-exact (sampling of the palm vertices).
- Beard (`staff_gate.py` Ponytail1): identical. Detached: the same 4 held staff parts, equal or fewer poses. Flat 0.00, winding 0,
  bones 0 of 12 stretching, texture quality body stretch p90 1.17 -> 1.19, head 1.64 -> 1.63.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/lod_summary.py inst final`): height 2.858 m at every LOD (installed
  LOD3 2.856); 0 stretched faces at every LOD; LOD0-1 lowest points equal to installed in every clip, LOD2 and LOD3 now follow LOD0 in
  Running/AttackMelee and Dead (installed LOD3 Dead floated 0.75 cm); **LOD3 dips 2.0 cm in Death and 1.2 cm in Death2** mid-fall
  (installed 0.15 / 0.78). Built by `scripts/build_lods.py` (0.5/0.18/0.06, 4 influences; soles, crown top, corpse + staff floor contact
  protected, each point snapped to the imported vertex: 65 of 65).

## Review
Viewer (installed and reduced, all 23 clips; `run_creature_review.py check`: 46 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_yanmir_reduce_claude/review/viewer/
Sheets read at full size: `review/sheet_face_c60.png` (front close-up, 3/4, true profile, low 3/4, party) and
`review/sheet_face_diff_c60.png` (face skin, eyes, ears, crown black; only the lower beard, back hair rim and mantle shading differ),
`review/sheet_body_c60_a.png` (Standing front/3-4/back, Walking, AttackRanged, Death), `review/close_c60_hands.png` (R fist outside and
front, L hand outside and front), `review/close_c60_torso.png` (chest plaque and necklace disks, belt and loincloth, back of the mantle,
shoulder band), `review/close_c60_legs_staff.png` (greaves, staff head, crown from above, back of the legs), `review/close_c60_motion.png`
(Running, Hit), `review/crop_beard_b60.png`, `review/crop_crown_b60.png` (the rejected b60 band), `review/ladder_sheet_c.png`.
Look at: the fingertips of the left hand (very slightly more angular), the lower beard and the back hair rim (cut at 0.7), the mantle fur.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_yanmir_reduce_claude/before/mm9_yanmir.glb REA_NODE=Yanmir $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py
RFIST=1 CONTACT=Death2:0.8:2.0 KEEPCLS=24 $G scripts/make_sets_yan.py c
SETS=c MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 MP_NOQ_GROUPS=4 MP_GROUPS=1:0.65,2:0.7,3:0.7,4:0.5,5:0.6 scripts/run_mp.sh c 0.6,0.57
scripts/build_mp.sh mp_c_r60 export/mm9_yanmir.glb   # swap_mp -> build_lods (protected, snapped) -> Yanmir's shrink_shadow_lods + fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_yanmir.glb before/mm9_yanmir.glb --json review/uv_audit_c60f.json
$G scripts/kept_check.py export/mm9_yanmir.glb c; scripts/gates.sh export/mm9_yanmir.glb final
REA_NODE=Yanmir $BL -P scripts/lod_check.py -- $PWD/export/mm9_yanmir.glb final; python3 scripts/lod_summary.py inst final
python3 scripts/make_viewer_manifest.py c60 inst_a=Installed=before/mm9_yanmir.glb red_a=Reduced_c60=export/mm9_yanmir.glb
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py c60; $G scripts/face_diff_sheet.py c60
```
Other files: `export/cand_a60.glb` (ladder a r60, 11,072) and `export/cand_c60.glb` (b r60 + crown band, 11,042) are superseded
intermediates, not candidates.

Install (orchestrator, on the OK): `check_winding.py export/mm9_yanmir.glb` (0), `tools/install_model.py export/mm9_yanmir.glb --world mm9`,
the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_yanmir_claude/README.md`: "LOD0 reduced post-install on <date>
by `mm9_yanmir_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_yanmir.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and viewer
stills only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face triangles are the
installed ones and the five-view diff is black there); the scripted trap clips (StartDie, Fall, Die) only through the gates.
