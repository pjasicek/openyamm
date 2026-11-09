# MM9 Skeleton (`mm9_skeleton`, tiers skel_a / skel_r) LOD0 reduction (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 40 of
"MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md), prio 1 (monster, relaxed keep set). Lease `mm9reduce:skeleton`
(skeleton-reduce-20261104). Route: [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) no-retexture branch, reorganised for a body
of separate rigid bone pieces (memory "separate-bone skeleton route"). No Meshy, no credits. `../mm9_skeleton_claude/` was only read.
**First-pass status: `export_h85` was installed and rolled back (UV audit); superseded by the fix pass below.**

Source: the installed `assets_source/worlds/mm9/models/mm9_skeleton.glb` (= `../mm9_skeleton_claude/export/mm9_skeleton.glb`,
sha256 cf916007ce3a), copied to `before/mm9_skeleton.glb` (the rollback source). Candidate sha256 977cb220dbf7.

## Fix pass (2026-11-04): chart-guarded pose-aware collapse, UV audit 0 — candidate `export_c77/mm9_skeleton.glb`

The first candidate (h85 below, -20.6 %) was installed and **rolled back**: `reduction_uv_audit.py` found 75 LOD0 body faces and
1 dome face whose UV triangles left the painted charts (MeshLab's texture-aware collapse moves wedge UVs; texture wedges at the
ankle bands, waist rope, sacrum, sternum, upper back and shins: `review/uv_audit_h85.json`). Lease `mm9reduce:skeleton` re-claimed
(skeleton-reduce-fix-20261104); `mm9:skeleton` free; the installed source is `before/` again (cmp identical).
**Status: `export_c77/mm9_skeleton.glb` (sha256 5cd4e943d4ec) ready for review (fix pass, chart guard, UV audit 0), not installed.**

| | LOD0 | Skel (body) | of it linings | SkelHead | Dagger | LOD1 | LOD2 | LOD3 (not in chain) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,438 | 8,822 | 575 | 3,316 | 300 | 5,925 | 2,071 | 587 |
| **c77** | **10,508 (-15.5 %)** | 7,072 | 459 | 3,136 | 300 | 5,019 | 1,741 | 595 |

Route (`scripts/glb_sets.py` -> `tex_extract.py` -> `mp_pieces.py` -> `mp_plan.py` / `run_mp.sh` -> `build_mp.sh`):
- the Imp's `mpqem.py` (half-edge collapse, every output vertex an installed vertex: positions, normals, UVs, joints, weights
  are the installed bytes; scored over every clip at 10 Hz, 293 poses, plus a position+UV rest quadric with texture weight
  `MP_W5=4`; texture guard on both tiers' base colours, skel_a paint and skel_r with its ramps baked; seam slides) run **per bone
  piece** (one Prim per piece, the same groups as before), each piece measured at 0.9 .. 0.3 at rest (two-way max/mean, volume,
  rest gap to each neighbouring piece);
- **chart guard `MP_CHART=1`** plus, new here, **`MP_AUDIT=1`: `reduction_uv_audit.Charts.test` on every new face inside the
  collapse, zero tolerance**. With the coverage guard alone a build still had 16 'cross' escapes (UV samples on another island);
  with the audit's own test none;
- joint contacts locked: every vertex within 7 mm of a neighbouring piece (`MP_CONTACT=0.007`), gap growth <= 1 mm, volume >= 80 %;
- kept exactly as before (skull face, mandible, eyes, teeth, neck, dagger, pieces of 30 faces or fewer, the five small sheets and
  their linings); floors: hands >= 0.6 (got 0.6-0.8), dome and both ropes >= 0.7, back panel >= 0.4 (its lining re-emitted as the
  reversed lining twins of the surviving outer faces: 192 -> 76); both tali kept exactly (b76 had cut them to 0.7 and the
  detached-parts audit then found them parted from the calf in 61 and 277 of 659 poses, 10.4 mm). Picks: pelvis 0.8, ribcage
  0.9, long bones 0.6-0.9, feet 0.6-0.9, vertebrae and rib groups 0.7-1.0.

Ladder (`work/selection_<label>.json`; limits p99 <= 5.19, max <= 25.9 mm, IoU >= 0.98):

| ladder | sweep | piece budget (max / mean mm) | LOD0 | p99 / max mm | IoU | |
|---|---|---|---:|---|---|---|
| m2 r80 | coverage guard, 4 mm contacts | 9 / 1.35 | 10,578 | 5.09 / 8.8 | 0.990 | pass; built (m80): UV audit 16 'cross' faces |
| a1 r80 / r85 | + audit guard, 4 mm | 9 / 1.35, 10 / 1.5 | 10,678 / 10,546 | 5.09, 5.25 | 0.990 | pass / fail; a80 built, audit 0, -14.2 % |
| b1 r80 / r85 / r90 | + 7 mm contacts | 9 / 1.35 ... 11 / 1.6 | 10,560 / 10,418 / 10,132 | 5.22, 5.68, 6.58 | | all fail |
| b2 r74 / r76 / r78 | 7 mm | 8 / 1.2, 9 / 1.2, 8 / 1.35 | 10,650 / 10,578 / 10,632 | 4.76, 5.12, 4.89 | 0.990 | pass; b76 built: audit 0, tali parted (above) |
| c1 r76 | + tali kept | 9 / 1.2 | 10,610 | 5.03 | 0.990 | pass |
| **c1 r77** | **+ tali kept** | **9.5 / 1.25** | **10,508 (-15.5 %)** | **5.12 / 9.41** | **0.989** | **pass, lowest passing: picked** |
| c1 r79 / r81 | | 10 / 1.2, 10 / 1.35 | 10,484 / 10,466 | 5.26, 5.31 | | fail |

UV audit (`review/uv_audit.json`): **LOD0 0 escaping faces in Skel_A, SkelHead_A and Dagger**. LOD1/LOD2 (Blender's decimate, as
the model was built) escape about as the installed LODs do: Skel_A 332 / 267 (installed 295 / 292), SkelHead_A 133 / 149
(137 / 149). Clips, images, materials, variants, skin, nodes and mesh extras byte-identical (`same_parts.py`: ALL SAME).

Gates installed -> c77 (`review/gates_before/`, `review/gates_c77/`):
- collapse gate body and head: identical; scrap gate: identical (Resurrect 6/313, 2.0 cm);
- hands/forearms in bones: identical or lower (AttackMelee/Ranged R fore 0.3 -> 0.0, Resurrect L hand 0.8 -> 0.7);
- `arm_hand_gate` (noisy here): equal or lower (Fidget2 L 4.5 -> 1.4 cm, AttackMelee R 5.9 -> 5.7, Hit2 L forearm 2.8 -> 2.1)
  except Resurrect L 20 -> 21 frames at the same 5.7 cm and forearm depths within 0.2 cm (Fidget3 R 5.8 -> 6.0);
- detached parts (24 fps): the installed four and no new one: L talus 10.1 mm / 36 poses -> 9.3 mm / 26, mandible 6.4 mm 5 -> 4
  poses, L carpal 4.3 mm 1 pose, part 65 4.1 mm 17 -> 11 poses; 68 -> 71 'only just attached';
- winding 0; flat shading 0.00 / 0.00 / 0.00; texture quality body atlas 61.1 -> 60.4 %, stretch p90 1.24 -> 1.28, spread 1.49
  -> 1.77 (fragments 3.1 -> 5.9 %: islands of fewer than 8 triangles); head unchanged;
- LOD heights 1.7934 m at LOD0/1/2 (installed 1.7934 / 1.7938 / 1.7932), lowest point per clip at every LOD equal to LOD0
  (Death -0.51 cm, Walking -0.65 cm), 0 faces stretched over 20x.

Sheets read: `review/sheet_escape1_c77.png`, `review/sheet_escape2_c77.png` (close-ups of the h85 escape areas: ankle bands,
shins, waist rope front, sacrum, upper back, sternum; installed | c77 | diff | clay; the h85 versions beside them for comparison),
`review/sheet_face_c77.png`, `review/sheet_body1_c77.png`, `review/sheet_body2_c77.png`, `review/sheet_hands_c77.png`,
`review/sheet_viewer_face_skel_{a,r}_c77.png`, `review/sheet_viewer_body_skel_{a,r}_c77.png`. The skull face is black in every
diff in both tiers; the escape areas show no wedges.
Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_skeleton_reduce_claude/review/viewer/ (installed and c77 per tier;
`run_creature_review.py check` 60 switches, 0 failed, no console errors).

Reproduce (project folder): `glb_sets.py`, `tex_extract.py` (after `viewer_tiers.py before/mm9_skeleton.glb inst`),
`MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAMS=1 MP_CONTACT=0.007 SFX=_a7 mp_pieces.py` (meshlab venv, about 2.5 min),
`KEEP_GROUPS=42,103 SFX=_a7 run_mp.sh c1 76:9:1.2,77:9.5:1.25,79:10:1.2,81:10:1.35`, `build_mp.sh mp_c1_r77 export_c77`,
`reduction_uv_audit.py export_c77/mm9_skeleton.glb before/mm9_skeleton.glb --json review/uv_audit.json`, `gates.sh`, `lod_check.py`,
`glb_close.py`, `pair_sheet.py`, `viewer_tiers.py`, `viewer_manifest_skel.py`, `shot_sheet.py`.
Install (on the OK): `check_winding.py export_c77/mm9_skeleton.glb` (0), `tools/install_model.py export_c77/mm9_skeleton.glb
--world mm9`, the binding regression; rollback `before/mm9_skeleton.glb`.

---

# First pass (rolled back)

## Result

| | LOD0 | Skel (body) | of it linings | SkelHead | Dagger | LOD1 | LOD2 | LOD3 (not in chain) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,438 | 8,822 | 575 | 3,316 | 300 | 5,925 | 2,071 | 587 |
| **h85** | **9,876 (-20.6 %)** | 6,440 | 479 | 3,136 | 300 | 4,692 | 1,619 | 592 |

Images, materials, textures, samplers, nodes, skin and inverse binds, all 17 clips, the root `KHR_materials_variants`, the LOD0
variant mappings and the mesh extras (chain stops at LOD2, as installed) are byte for byte the installed file's
(`scripts/same_parts.py`: ALL SAME). Only geometry changed. The reduced primitives carry no `COLOR_0` (constant white in the
installed file) and no `COLOR_1` (the engine reads neither for these materials); the kept dagger drops both too, so the merged
shadow meshes see matching attributes.

Why only ~21 %: the Meshy pieces were already cut per part at assembly (`../mm9_skeleton_claude/scripts/sym_skel.py` TARGET), so
most pieces show 5-8 mm of error after the first 10-20 % of their faces; and 3,891 faces (33 %) are kept by rule (skull face,
mandible, teeth, eyes, neck, dagger, pieces of 30 faces or fewer, five sheets).

## Why per piece, and what was cut

The body is 145 closed rigid bone pieces plus six open sheets (vest flanks, back panel, straps) and eight hip strips, each sheet
with a lining that is an exact reversed copy on one dark texel (575 faces at the end of the Skel primitive). The pooled quadric of
the reference projects eats small pieces first; here every piece is its own group
(`make_groups.py` -> `sweep_groups.py` -> `plan_from_sweep.py` -> `decimate_pieces.py`):
- each piece was decimated alone at 0.9 .. 0.3 (MeshLab texture-aware quadric, UVs kept) and measured at rest: two-way
  point-to-surface max and mean, and the growth of its rest gap to every neighbouring piece (the dagger and kept pieces included).
  A step is allowed only if a closed piece stays closed, gains no self-intersections, turns no face over against the source and
  keeps its volume within 80-120 %;
- thin pieces lose cross-section under any collapse (rib groups fell to 40-60 % volume at 0.5); `inflate()` pushes a reduced piece
  out along its normals by the one offset that restores the source volume (capped 4 mm), used per piece when it lowers the error
  (74 of the cut pieces);
- each piece then takes the fewest faces whose rest error stays within the step's budget (h85: max 8.5 mm, mean 1.35 mm, joint
  gap growth at most 1 mm);
- **kept exactly:** the skull face (sockets, brow, cheekbones, nasal opening, upper teeth: every cranium face in front of the
  temples and below the upper forehead), mandible, eyes, the 20 teeth, the neck pieces, the dagger, the rope collar, every piece of
  30 faces or fewer (distal phalanges, small tarsals, toe tips, hip strips) and five of the six sheets (their torn hems are most of
  their faces: a 0.7 cut moved the flank panels 5 mm on average);
- **cut:** cranium dome (behind the temples and above the forehead) 0.7, hands 0.6-0.8 (every finger kept: each phalanx is its own
  piece), long bones 0.3-0.8, feet 0.3-0.9, ribcage 0.8, pelvis and waist rope 0.7, vertebrae and rib groups 0.5-0.9, back panel 0.5;
- **linings** are rebuilt on export (`export_cand.py`, `REA_TAG`) as reversed copies of every sheet face, kept or reduced, on the
  installed dark texel with the same weights: 575 -> 479 (the back panel's 192 -> 96).

Weights: source vertices keep their source weights exactly; new vertices take the nearest vertex of their own source piece
(`reduce_ladder.py` piece weights). Normals: vertices used only by kept faces take the installed normals (`keep_normals.py`), the
rest are smooth (the installed file is smooth everywhere: flat-shading 0.00).

## Ladder (REA_HEIGHT_M 1.729: p99 <= 5.19 mm, max <= 25.9 mm, IoU >= 0.98)

| ladder | piece budget (max / mean mm) | LOD0 outer (+ linings) | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| a | fixed ratios 0.4-0.7 per class | 8,501 | 7.06 / 17.4 | 0.960 | fail: thin pieces and sheets |
| c r70 / r80 | 7 / 1.0, 8 / 1.2 | 9,391 / 9,061 | 4.31 / 7.3, 4.87 / 7.9 | 0.983, 0.979 | c70 built: the dome at 0.4 showed corners on the skull's back outline in the viewer profile |
| d r80 | dome >= 0.7 | 9,239 | 4.87 / 7.9 | 0.980 | rope collar outline faceted at 0.5 (chest close-up) |
| f r80 | + ropes >= 0.7 | 9,313 (+479) | 4.86 / 7.9 | 0.981 | built and gated: the detached-parts audit found both index-finger middle phalanges 5.8 mm off their knuckle in the bind pose |
| g r80 / r90 / r95 | + joint gap growth <= 1 mm: 8 / 1.2, 9 / 1.5, 10 / 1.8 | 9,553 / 9,119 / 8,927 | 4.77, 5.56, 5.82 | 0.982, 0.975, 0.973 | r80 pass, r90 and r95 fail |
| h r83 | 8 / 1.5 | 9,289 | 5.36 / 7.9 | 0.978 | fail |
| **h r85** | **8.5 / 1.35** | **9,397 (+479 = 9,876)** | **5.16 / 8.05** | **0.980** | **pass, lowest passing: picked** |
| h r87 | 9 / 1.2 | 9,485 | 4.92 / 8.6 | 0.983 | pass |

The ladder's SSIM says nothing here: its textured renders show every candidate black (the imported source material multiplies by
the source's white `COLOR_0`, which the ladder candidates lack), so it sits at 0.95 at every step. The textured comparison is the
GLB close-ups and viewer shots below, both from the exported files. Ladder renders: `review/ladder_sheet_h.png`; per-piece errors:
`work/sweep.txt`.

## Gates (installed -> h85; `scripts/gates.sh`, the skeleton's own gate scripts copied here; `review/gates_before/`, `review/gates_h85/`)

| gate | installed | h85 |
|---|---|---|
| collapse gate, body / head | 0 face-frames in every clip / Resurrect neck 11 frames (1 face) | identical |
| scrap gate (femur through strips and vest, 48 fps) | 0 in every bound clip; Resurrect 6/313, 2.0 cm | 0 in every bound clip; Resurrect 6/313, 2.1 cm |
| hands/forearms in closed bones | 0 frames > 1 cm except Hit L 2.0 cm 1 f; AttackMelee/Ranged R 0.7, Resurrect L 0.8, forearms 0.3-0.7 | 0 frames > 1 cm except Hit L 2.0 cm 1 f; AttackMelee/Ranged R 0.8, Resurrect L 0.8, forearms 0.0-0.6 |
| `arm_hand_gate.py --outer-only --exact` (noise on this body, see the creature README) | Walking L 3.8 (1 f), Fidget2 L 4.5 (5 f), AttackMelee R 5.9 (2 f), Resurrect L 5.7 (20 f), Hit L 1 f | Walking L 0, Fidget2 L 1.4 (3 f), AttackMelee R 0.8 (0 f), Resurrect L 5.9 (24 f), Hit L 2 f; the rest within 0.1 cm |
| detached parts (24 fps, 659 poses) | 4 flagged: L talus 10.1 mm (36 poses, Walking), mandible 6.4 mm (5), L carpal 4.3 mm (1, Resurrect), part 65 4.1 mm (17); 68 only just attached | 5 flagged: L talus **4.2 mm (2, Resurrect only)**, mandible 6.4 mm (10), L carpal 4.9 mm (5, Resurrect only), a second L carpal 4.3 mm (2, Resurrect only; new), part 65 4.1 mm (10); 71 only just attached. The first f80 had both index middle phalanges 5.8 mm off in the bind pose: fixed by the gap rule |
| winding | 0 | 0 |
| flat shading body / head / dagger | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| texture quality body: atlas, density spread, stretch p90 | 61.1 %, 1.49, 1.24 | 58.0 %, 1.77, 1.45 (inflation and the collapse; "fragments" 3.1 -> 11.9 % counts islands under 8 triangles, which reduced pieces now are; UV area unchanged). Head 68.6 % -> 68.4 % |
| LOD heights LOD0/1/2, faces stretched > 20x | 1.7934 / 1.7938 / 1.7932 m; 0 | 1.7944 m at every LOD (dome top +1 mm); 0 |
| lowest point Standing / Walking / Death / Dead | 0 / -0.65 / -0.51 / 0 cm | identical at LOD0; LOD1/2 Dead -0.01 cm (installed LOD2 -0.07) |
| jitter, bone lengths, handedness | | not rerun: clips and skin byte-identical |

The scrap and hand-bone gates label each vertex by the nearest vertex of the creature's master; on the reduced mesh that put a few
vertices of one piece on its neighbour (a false 3.0 cm "R hand in pelvis"), so both copies here take one label per connected piece
by majority (`piece_vote`; the installed file relabels 0 vertices). `review/gates_before/*_vote.txt` are the installed runs with it.

## Review

- Viewer, installed and reduced per tier (clip time and camera kept on switching):
  http://127.0.0.1:8912/level_generation/creatures/mm9_skeleton_reduce_claude/review/viewer/ (`run_creature_review.py check`:
  60 switches, 0 failed, no console errors).
- Sheets (read): `review/sheet_viewer_face_skel_{a,r}_h85.png` and `review/sheet_viewer_body_skel_{a,r}_h85.png` (viewer: face
  front/3-4/profile, arms; Standing front/3-4/back, Walking, Running, AttackMelee, legs and feet; installed | h85 | diff x4: the
  skull face is black in every diff, the dome faint); `review/sheet_face_h85.png` (GLB close-ups: face front, 3/4, profile,
  low 3/4, party, back of head; tex and clay), `review/sheet_body1_h85.png` (chest, ribcage 3/4, back panel, pelvis, legs),
  `review/sheet_body2_h85.png` (ankle and foot, both fists and the grip, arm, attack, corpse, whole), `review/sheet_hands_h85.png`;
  `review/crop_dome_inst_c70_f80.png` (dome outline at 0.4 and 0.7). Rejected steps: `review/sheet_*_c70.png`, `*_c90.png`,
  `*_d80.png`, `*_f80.png`.

## Install (not run; on the user's OK)
`check_winding.py export_h85/mm9_skeleton.glb` (0), `tools/install_model.py export_h85/mm9_skeleton.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py` for the five descriptors, then add to
`../mm9_skeleton_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_skeleton_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_skeleton.glb`.

## Reproduce (project folder)
`lining_pairs.py before/mm9_skeleton.glb work/lining.npy`, `strip_lining.py before/mm9_skeleton.glb work/lining.npy
work/source_nolining.glb`, `REA_GLB=level_generation/creatures/mm9_skeleton_reduce_claude/work/source_nolining.glb REA_NODE=Skel`
`import_source.py`, `dump_mesh.py`, `dump_weights.py` (Blender), `make_groups.py`, `sweep_groups.py` (meshlab venv; Hausdorff
sampling makes its numbers vary by about 0.1 mm between runs), `plan_from_sweep.py 8.5 1.35 work/plan_85.json` (dome and ropes
>= 0.7, hands >= 0.6, gap growth <= 1 mm), `run_ladder.sh h 83,85,87`, `LADDER=h EXPORT=export_h85 build_export.sh 85`,
`viewer_tiers.py`, `viewer_manifest_skel.py`, `glb_close.py`, `pair_sheet.py`, `shot_sheet.py`, `lod_check.py`, `gates.sh`,
`same_parts.py`.

## Not checked
In game (not installed; the binding regression and floor audit run after install); LOD1/LOD2 by eye (numbers only); Fidget2/3,
Taunt, Hit, Resurrect in the viewer (GLB renders of AttackMelee and Death only); 49 vertices where the texture-aware collapse left
two wedge UVs within 0.002 of each other (a sub-texel split, not seen in any sheet).
