# MM9 PeasantF4 (`mm9_peasantf4`, hooded townswoman, tiers pf4_a / pf4_b) reduction: candidate m7 r50 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk, relaxed keep
set), ledger row 8 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf4` (owner peasantf4-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_peasantf4.glb` (r41, sha256 bccd88d7a334, = `../mm9_peasantf4_claude/export/`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantf4_claude/` was only read
(its scripts are called read-only by the gates and viewer tools here). Fre (`mm9_fre_claude`, `mm9_fre.glb`) was not touched.

| | LOD0 | body prim | head prim | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed r41 | 14,948 | 9,406 | 5,542 | 7,343 | 2,640 | 880 |
| **m7 r50 (`export/mm9_peasantf4.glb`, sha256 cd25c84528fb)** | **12,312 (-17.6 %)** | 7,178 | 5,134 | 6,032 | 2,170 | 988 |

Every LOD0 vertex is an installed vertex (positions, normals, UVs, joints, weights byte-identical; only index buffers change). Clips,
skin, nodes, materials, `KHR_materials_variants` and all 8 images are the installed bytes (`same_clips.py`). LOD0 faces leaving the
UV charts: 0 (`claude_shared/reduction_uv_audit.py`, `review/uv_audit_final.json`; `scripts/uv_escape.py` also 0). The LOD1-3 counts of
escaping faces are those of the LOD builder, about as installed (116/83, 130/93, 10/20 vs 106/77, 137/95, 96/13).

## What is kept exactly (protected share 43 % + the rebuilt linings)
The whole head comp (face skin, eyes, ears, neck seam and the hidden skull: 3,612), F1's hidden old hood ('scarf', 378), the hood and
sleeve-tube rim strips and the sleeve caps (the job-8 fixes: no new holes, rings untouched where they close), the job-8 bodice hole fills,
the bodice's front placket column (|x| < 5 cm), the bright painted bodice trims + one ring (the apron band across the back, the collar
embroidery; tone luminance > 120), F1's short sleeves as `sleeve_poke_pf1.py` sees them (dress faces with |x| > 0.15 m), F1's hidden
skirt lining, the soles (shoe faces within 3 cm of the floor) and pieces of up to 60 faces.
Linings: the hood and sleeve-tube linings are not cut; they are re-emitted from the surviving lined outer faces through the asm's exact
twin map (`f4_twin_v`: hood lining 436 -> 324, sleeve lining 240 -> 158), so every lining face is the reversed copy of its outer face.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Highwayman's copy)
Scored over 291 poses (every clip at 10 Hz) + a position/UV quadric, only removes vertices, texture guard on the body tone + region
mask (body) and both tier face/hood colours (head), max 100 / mean 45. Groups (`scripts/make_sets_pf4.py f`): hands 0.6 (every finger
kept: collapses refuse to flip in any pose), hood outer shell 0.7, skirt 0.7, sleeve tube outer 0.8, legs above the soles 0.6, shoulders
0.7, MPFB arm 0.75, the rest of the bodice 0.5.

| config | change | LOD0 | ladder p99 / max mm (limits 5.23 / 26.2) | result |
|---|---|---:|---|---|
| m1 r50 | first groups, F1 skirt lining 0.6 | 11,194 | 3.58 / 15.4, IoU .998 SSIM .996 | light patch on the placket close up; Conv3 hand 5.8 cm (gate reads the cut hidden lining as outer); sleeve poke Conv1 R 0.7 mm |
| m3 r50 | placket kept, lining kept, shoulder group | 11,548 | 2.98 / 15.1 | sleeve tube cut 0.75: arm through the tube 1.3 cm in 4 clips; old hood out in Dead (hood 0.65) |
| m4 r50 | short sleeves kept, hood 0.7, tube 0.8 | 11,902 | 2.78 / 12.3 | apron band (back) and collar shading differ close up |
| m5 r50 | + painted trims kept | 12,130 | 2.79 / 17.0 | see-through sleeve R 2 -> 6 px (32 frames) at the armpit |
| m6 r50 | + shoulders exact | 12,194 | | sleeve R still 6 px (not the shoulders) |
| **m7 r50** | m5 + MPFB arm 0.75 | **12,312** | (m5 + 182 arm faces) | **sleeve R 2 px: picked** |

## Gates, installed -> m7 r50 (`review/gates_before/`, `review/gates_m7r50/`, `review/gates_compare_m7r50.txt`)
Jitter not re-run: clips byte-identical. `gate_pf4.py` runs as `scripts/gate_rt.py` on the runtime GLBs (same measure, labels
through the installed vertices), so before/after are read the same way.
- Collapse face-frames 27,518 -> 23,957, lower in every clip; single-face rises: Standing waist 0 -> 2, Walking armpit R 1 -> 2, Running
  armpit R 3 -> 4 and waist 2 -> 3, Fidget elbow R 0 -> 2, Dead waist 0 -> 1.
- Arm/hand (outer, exact): unchanged in every clip except finger-stretch p99 up by at most 0.07 (max 1.33 -> 1.36; worst-case 3.3 = 3.3).
  Robe gate identical. F1 short-sleeve poke identical (m1/m3 had Conv1 R 0.7 mm: fixed by keeping the short sleeves).
- Hood / sleeve tube / old hood (`gate_rt.py`): 0 frames over 1 cm before and after; hood rest-relative max 0.09-0.69 cm (installed
  0.16-0.86), arm under the tube 0.57-0.58 cm in Fidget/Talk/Conv1/Conv3 (installed 0.43-0.50), the rest equal or lower; the 5 known
  old-hood jaw vertices (max 0.47-0.81 cm, as installed) out in 108 / 85 / 73 frames of Standing / Fidget / Hit (installed 97 / 77 / 64),
  fewer in Walking / Running.
- See-through (every clip, 16 views): sleeve R 2 -> 2 px (12 -> 15 frames), sleeve L 2003 -> 1947, torso 1596 -> 1521, head 157 = 157,
  boots 0 = 0; collar 907 -> 949 px (Death/Dead from the feet at ground level up the hollow dress, as F1; 13 = 13 px from the party's
  20 deg). Back faces magenta (Blender, Standing / Fidget / Hit, back, low back, elbows from behind, chest): none in either model.
- Flat 0.00 / 0.01, bone lengths 0 stretching, winding 0, detached parts as installed (the 2 legs), texture quality equal (body stretch
  p90 1.08 -> 1.09).
- LODs (`lod_check.py`, every frame of every clip): top 0.814 m at every LOD (installed LOD3 0.774: lost 4 cm of hood), Standing -0.2 cm,
  Dead 0.0 and Death -1.6 cm at every LOD (installed LOD3 Standing +0.24, Death -1.7); faces stretched > 20x per LOD 23 / 12 / 10 / 10
  (installed 31 / 14 / 14 / 14).

## Review
Viewer (installed vs reduced, both tiers, 11 clips; `run_creature_review.py check` 44 switches, 0 failed, 0 console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf4_reduce_claude/review/viewer/
Sheets (installed above reduced): `review/sheet_face_m7r50.png` (front close-up, 3/4, both profiles, low 3/4, party; both tiers),
`review/diff_face_m7r50.png`, `review/sheet_body_m7r50_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/sheet_back_m7r50[_Fidget|_Hit|_Walking]_{a,b}.png` (back, low back, elbows from behind, back 3/4 both sides, hem from behind),
`review/sheet_arms_m7r50[_Fidget|_Hit|_Walking]_{a,b}.png` (arms 3/4 both sides, low 3/4 both sides, torso front, torso 3/4),
`review/diag_backfaces/sheet_m7r50_{Standing0,Fidget1.0,Hit0.7}.png` (Blender, back faces magenta: none in either).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantf4_reduce_claude/before/mm9_peasantf4.glb REA_NODE=PeasantF4 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/label_glb.py; $G scripts/tex_extract.py
PLACKET=0.05 SLEEVEX=0.15 TRIM=120 $G scripts/make_sets_pf4.py f
SETS=f MP_GROUPS=1:0.6,2:0.7,3:0.7,4:0.8,5:1.0,6:0.6,7:0.7,8:0.75 scripts/cap.sh $G scripts/mpqem.py before/mm9_peasantf4.glb 0.5
cp work/mp_r50.npz work/mp_m7_r50.npz; LIE=0.018 scripts/build_mp.sh mp_m7_r50 export/mm9_peasantf4.glb
scripts/gates.sh export/mm9_peasantf4.glb review/gates_<tag> --see; python3 scripts/gate_compare.py <tag>
scripts/shots.sh; python3 scripts/shot_sheets.py <tag>; scripts/diag_backfaces.sh export/mm9_peasantf4.glb <tag>
```
LODs: `scripts/build_lods.py` (tools/build_actor_lods.py, default ratios) with protected points snapped to the imported vertices (the
LOD-protection snap trap): floor contact, crown, corpse contact within LIE = 1.8 cm of the floor at the end of Death and in Dead; points
shared by coincident vertices with other weights are left out (the tool refuses them). LIE 1 cm let LOD3 sink 8 mm in Dead; 3 cm gave
LOD3 1,311 triangles.

Install (on the orchestrator's / user's OK only): `check_winding.py export/mm9_peasantf4.glb` (0), `tools/install_model.py
export/mm9_peasantf4.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantf4_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_peasantf4_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_peasantf4.glb`.

## Not checked
In game; motion at normal speed by eye (viewer stills at Standing, Walking, Fidget, Hit, Talk, Death and numeric gates only); LOD1-3
and shadow meshes by eye (numbers only); the Cower/Conv clips in close-up (gates only).
