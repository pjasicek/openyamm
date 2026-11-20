# MM9 Imp (`mm9_imp`, Imply / Imp / Imp Elder) reduction: candidate p80, -13.3 % (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 79 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:imp` (owner imp-reduce-20261104); the creature's
own `mm9:imp` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_imp.glb` (sha256 82117ae94fca, identical
to `../mm9_imp_claude/export/mm9_imp.glb`), copied to `before/` (the rollback source). The attachments (`mm9_imp_trident`,
`_wrapl`, `_wrapr`, `_tongue`) are not touched. No Meshy, no credits, no repaint. **Not installed.** `../mm9_imp_claude/` (approved,
frozen) was only read: its gate scripts run from there.

**Below the brief's ~15 % bar.** With every keep rule met (face, the whole fist round the shaft, the skin under the wraps, the
claws, the tail) and every new UV triangle on the installed charts, the best passing step saves 13.3 %. The orchestrator may
record the row `kept (no useful gain)` instead; the candidate is complete in case a 1,078-triangle cut per imp is wanted.

| | LOD0 | body (Imp_A) | head (ImpHead_A) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,080 | 4,817 | 3,263 | 4,037 | 1,452 | 473 |
| **p80 (`export/mm9_imp.glb` = `export/mm9_imp_p80.glb`, sha256 2f504bd696c0)** | **7,002 (-13.3 %)** | 3,807 | 3,195 | 3,498 | 1,258 | 407 |

Every vertex of the candidate is an installed vertex: positions, normals, UVs, joints and weights are the installed bytes (only
index buffers changed). Clips (17), skin, nodes (every socket and helper bone: `Yweaponbase`, `Yweapon`, `Xwrap L/R`, `Xtongue`,
`Xpiv`), materials (region masks, ramps, eye emission), `KHR_materials_variants` and all 9 images: byte-identical
(`scripts/same_clips.py`). Faces leaving the installed UV charts (`scripts/uv_escape.py`, the Mummy's check): **0** (h72: 103).

## Measured first: protected share 55 %
The body was already cut per part at the build (Smart Topology 15,695 -> 8,080, `../mm9_imp_claude/scripts/reduce_body.py`) and
the head set is mostly face. `CLAW_RING=0 scripts/imp_sets.py p grip wrap shaft` (`review/classes_g.png` shows set g: grey exact,
red grip/wrap contact):
- **Exact, head (3,068 of 3,263):** the separate pieces (eyes, teeth, gums: 708), the face (every shell face that is not cranium),
  the ears (582 with 2 rings), horns, brows and mouth cavity (head mask no-region, grown 2 rings), the neck seam.
- **Exact, body:** the belt, buckle, flap and wrist bands (separate pieces, 396), the neck seam, soles, the claws (body mask G),
  the hand/forearm junction, the tail (its spade tip moved 32 mm at 0.6, and a 0.6 cut of the rest failed the max: ladder g), and
  from `scripts/contact_keep.py` (attachments posed on their joints at 24 fps over every clip): the fist round the trident (right-hand
  faces within 2.5 cm of the shaft axis or the trident surface, about 1.5 cm from the 1 cm shaft: 308), the skin under the shin
  wraps (within 1.5 cm of the posed wraps: 147) and the left-hand faces within 7 cm of the shaft (22, below).
- **Cut:** cranium (top/back of the skull, 195 faces) 0.65; left hand 0.6 and the rest of the right hand 0.6 (every finger kept);
  feet 0.65; the rest of the body (trunk, arms, legs: 1,401) at the ladder ratio 0.8.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Bigfoot/Lesser Demon copy)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices. Texture guard per collapse:
A = region mask, B = shared base colour, C = metal/roughness (studs and belt metal; `scripts/tex_extract.py`). Two additions:
- **Seam slides on every cut group** (`MP_SEAM_GROUPS=0,1,3,4,5`): the body's UV seams locked the cheap collapses; with slides
  the same count dropped p99 from 3.82 to 3.06 mm (ladder b vs e).
- **Chart guard** (`MP_CHART=1`, ported from `mm9_mummy_reduce_claude`, sampled on the same 12-step grid as `uv_escape.py`): h72
  had 103 faces whose UV triangles reached into gutters or other islands, mostly from seam slides; with the guard 0.

## Ladders (height 1.176 m: p99 <= 3.53 mm, max <= 17.6 mm; `work/selection_<label>.json`, `review/ladder_sheet_<label>.png`)
Groups: hand L / hand R / feet / cranium / tail; all from e on with seam slides.
| set | change | step | LOD0 | p99 / max mm (worst) | |
|---|---|---|---:|---|---|
| a | .65/.7/.7/.7/.6, claw ring 1 | r60 / r50 / r45 | 6,856 / 6,716 / 6,646 | 5.88/32.1 (tail tip), 8.66, 13.6 | fail |
| b | .6/.65/.7/.7/kept | r75 ... r60 | 7,044 ... 6,832 | 3.82/14.0 ... 5.66 | fail |
| c | .5/.55/.6/.6/kept | r90 / r80 | 7,148 / 7,008 | 4.48, 4.64 | fail (hands stop at 383/385) |
| e | b + seam slides | r75 / r65 | 7,044 / 6,902 | 3.06/10.5, 3.87 | pass / fail |
| f | .5/.55/.65/.65 | r75 / r70 | 6,884 / 6,812 | 3.30, 3.63 | pass / fail (hands below the brief's 0.6) |
| g | .6/.6/.65/.65/.6 (tip kept) | r75 / r72 / r70 | 6,934 / 6,898 / 6,862 | 3.50/18.6 (tail), 3.64, 3.90 | fail |
| h | .6/.6/.65/.65/kept | r72 / r70 | 6,948 / 6,912 | 3.34/10.5, 3.59 | pass / fail; h72 built: 103 faces off the charts |
| i | h + chart guard | r75 / r72 / r70 | 6,984 / 6,948 / 6,912 | 3.65, 3.83, 4.03 | fail |
| j / k | i, hands .5/.55 / .6 | r80 / r78 | 6,954 / 7,018 | 3.69 / 3.45 | fail / pass |
| m / n | k, claw ring 0 (chart grid 8 / 12) | r78 / r80 | 6,868 / 6,904 | 3.51 / 3.45 | pass; m78 1 face off the charts; n80 built: trident gate Hit2 0.4 -> 6.0 cm |
| **p** | **n + full fist grip (308) + left fingers by the shaft (22)** | **r80** / r78 | **7,002** / 6,966 | **3.50 / 10.5 (Fidget:15)**, 3.63 | **PASS, picked** / fail |

n80 (6,904, -14.6 %) had the fist cut except 59 faces (the first grip check sampled the trident's vertices, which sit at the
shaft's ends) and gave the trident gate a 6 cm reading in Hit2 frames 28-31 next to the left fingers. That reading is the gate's
nearest-face sign test: the shaft passes 3.8-5.1 cm from the left-hand vertices in both files and the winding number of every
shaft point near the hand is 0.01 for both (`scripts/probe_hit2.py`), so nothing is inside; p keeps those 22 finger faces and the
whole fist anyway, and the gate is identical to the installed model.

## Gates, installed -> p80 (the Imp's own gate scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_p80/`, `review/gates_compare_p80.txt`)
- Arm/hand (`--outer-only --exact`, 48 fps): no clip worse on any side; hand and forearm 0.0 cm inside the body everywhere (Fidget2
  and Hit2 L 0.1 -> 0.0), 0 frames over 1 cm; wrists identical; finger stretch p99 lower (1.85 -> 1.72 Standing L), max equal.
- Trident vs skin (`scripts/blade_gate_split.py`: the installed blade gate with the trident posed from its attachment GLB):
  identical in every clip (AttackMelee 1.3 cm on 1 frame at the head, the rest 0.5 cm or less).
- Jitter against MM9's raw clips (main `../mm9_imp_claude/work/mm9_imp_clips.glb`, dropped clips `work/extra_raw.glb`): no new fail;
  the installed Death2 shoulder-skin fail stays (L 4.76 -> 4.66, R 5.24 -> 5.00 mm/f2). Shoulder-skin excess rose under the 2.0
  limit in AttackMelee L 0.09 -> 0.97 and AttackRanged L 0.13 -> 1.12. Clips are byte-identical and every kept vertex skins as
  installed, so it is the p95 over a smaller vertex set (155 -> 133 per side): `scripts/shoulder_subset.py`
  (`review/shoulder_subset_p80.txt`) gives raw p95 within 0.2 mm/f2 and the vertex maximum never higher.
- Stretch (`gates.py`): edge-ratio max equal in every clip, p99 equal or lower (Death2 +0.001), min equal or higher. Lowest point
  per clip equal except Walking and Backpedal -0.85 -> -0.72 cm (less below the floor).
- Detached parts (48 fps): the same flap (Xpiv) in Hit2, 4.1 -> 2.3 cm.
- Bone lengths 0 stretching; winding 0 inverted; flat shading 0.00 / 0.00; texture quality: atlas 52.6 -> 52.5 %, density equal,
  body stretch p90 1.11 -> 1.12.
- LODs (`scripts/lod_check.py`, every frame of every clip; `review/lod_table_p80.txt`), built by `scripts/build_lods.py`
  (tools/build_actor_lods.py at the build's ratios 0.5 / 0.18 / 0.06, 4 influences; protected: soles, the top, corpse contact,
  axis extremes and, new, every claw tip (14), both horn tips and the tail's spade tip from `scripts/lod_tips.py`; each point
  snapped to the nearest imported vertex first: 68 of 68 mapped, worst offset 4.9e-6 m). Stretched faces 0 at every LOD (as
  installed). Top 1.205 m at every LOD (installed LOD3 1.201). Installed LOD3 floated 0.4-1.8 cm (Standing +0.51, Running +1.79,
  Dead +1.24 cm); now LOD1-3 sit at LOD0's lowest point in most clips and at most 0.45 cm above it.

## Review
Viewer (installed and reduced, every tier with its attachments: trident on all, shin wraps on B, tongue on C; 17 clips):
http://127.0.0.1:8912/level_generation/creatures/mm9_imp_reduce_claude/review/viewer/
`run_creature_review.py check`: 102 switches (6 models x 17 clips), 0 failed, 0 console errors.
Sheets read (full size): `review/sheet_face_p80.png` (front close-up, 3/4, true profile, low 3/4, party; every tier, installed over
reduced), `review/sheet_face_diff_p80.png` (|installed - reduced| x4: face, eyes, ears, horns, teeth, tongue black in every tier;
only the shoulders, the hands, the chest and the cranium outline differ), `review/sheet_body_p80_c.png` (and the h72 rows of a and
b: Standing front/3-4/back, Walking, AttackMelee, Death), `review/upper_p80_a.png`, `review/upper_p80_b.png` (cranium and horns from
behind, side-back and above; torso front/back/side; AttackMelee and Taunt backs; both hands incl. the trident fist; foot claws;
shin with tier B's wraps; tail), `review/close_h72_a.png`, `review/classes_g.png`, `review/head_mask_view.png`,
`review/ladder_sheet_h.png`. No visible change found. Look at: the right fist round the shaft (`r0`, `r1`), the left hand
(0.6), the skull top and back (cranium 0.65) and B's wraps on the shins.
Pre-existing, not caused by the reduction: a small dark notch on the lower back right of the spine (both files, `t1`, `n0`).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_imp_reduce_claude/before/mm9_imp.glb REA_NODE=Imp $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/contact_keep.py
CLAW_RING=0 $G scripts/imp_sets.py p grip wrap shaft; $G scripts/head_mask_view.py
MP_CHART=1 MP_SEAM_GROUPS=0,1,3,4,5 SETS=p MP_GROUPS=1:0.6,5:0.6,3:0.65,4:0.65,6:1.0 scripts/run_mp.sh p 0.8,0.775
$G scripts/lod_tips.py before/mm9_imp.glb       # claw, horn and tail tips for the LOD protection
LIE=0.01 SOLE=0.006 scripts/build_mp.sh mp_p_r80 export/mm9_imp_p80.glb; cp export/mm9_imp_p80.glb export/mm9_imp.glb
$G scripts/uv_escape.py before/mm9_imp.glb export/mm9_imp.glb
scripts/gates.sh export/mm9_imp.glb p80; python3 scripts/gate_compare.py p80
REA_NODE=Imp $BL -P scripts/lod_check.py -- $PWD/export/mm9_imp.glb p80; python3 scripts/lod_table.py installed p80
$G scripts/viewer_tiers.py before/mm9_imp.glb inst; $G scripts/viewer_tiers.py export/mm9_imp.glb red   # then make_viewer_manifest.py
scripts/shots.sh; scripts/upper_shots.sh; python3 scripts/shot_sheets.py p80; python3 scripts/face_diff_sheet.py p80
```
Install (on the user's OK only): `check_winding.py export/mm9_imp.glb` (0), `tools/install_model.py export/mm9_imp.glb --world mm9`
(the body only; the four attachment GLBs stay as installed), the `mm9_actor_models_build_every_binding` regression,
`floor_audit.py --world mm9 --match 'MM9 Imp*'`, and add to `../mm9_imp_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_imp_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_imp.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); tier C's upper sheet `review/upper_p80_c.png` (written, not
read; C was read on the face sheet and the body row); the stride/orientation gates (they read only the clips, which are
byte-identical). `export/mm9_imp_h72.glb`, `_m78.glb` and `_n80.glb` are superseded candidates (gates in `review/gates_h72/`,
`review/gates_n80/`); `review/sheet_*_h72*` and `close_h72_*` show h72, not p80. Several scripts in `scripts/` are Bigfoot copies
this route did not use (`bf_sets.py`, `bf_gate_compare.py`, `glb_parts.py`, `grip_contact.py`, ...).
