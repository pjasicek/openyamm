# MM9 PeasantM2 (`mm9_peasantm2`, the old townsman) reduction: candidate h r70 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 45 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm2` (owner
peasantm2-reduce-20261105); the creature's own `mm9:peasantm2` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm2.glb` (sha256 fc3e623f4d1d, identical to `../mm9_peasantm2_claude/export/`), copied to
`before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm2_claude/` was only read (its
final master `work/final_v1.blend` opened read-only for part labels, its gate scripts run in place).

**Family / consistency with PeasantM2d:** PeasantM2d (`mm9_peasantm2d.glb`, row 22) is this body plus elf ears, a closed mouth and an
upper-tunic lining, built and installed as its own GLB (own chain, own paints), so it is not a tier of this file and is not re-derived
from this cut. Its reduction (`../mm9_peasantm2d_reduce_claude/`, read only, nothing written there) was copied as the starting point
and its picked recipe re-used unchanged, so the two bodies are cut the same way: set h (face shell exact, hairline, collar, cuffs, belt
and buckle, skirt cap, soles, small pieces, shoulder cloth, forearm stubs, corpse-belt hip faces), groups hands 0.6 (every finger),
hair 0.7, skirt 0.7, boots 0.55, MPFB forearm skin 0.45, trousers 0.5, tunic at the ladder ratio 0.7, texture weight 4, chart guard and
the audit's own chart test inside each collapse. The hip faces are M2d's own keep set mapped onto this mesh by rest centroid (140 of
140 at 0.0 mm, `scripts/extra_keeps.py`).

| | LOD0 | limbs (hands, forearm stubs, trousers, boots) | torso (tunic, skirt, belt, linings) | head (face shell, hair + lining) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,039 | 3,519 | 2,650 | 5,870 | 6,018 | 2,164 | 720 |
| **h r70 (`export/mm9_peasantm2.glb`, sha256 9f8d734fd16f)** | **9,705 (-19.4 %)** | 2,123 | 2,308 | 5,274 | 4,850 | 1,745 | 581 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (13), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 12 images: byte-identical
(`review/gates_h70/same_clips.txt`). Face shell (face, scalp, neck, eyes, mouth: 3,582 triangles; the tier-A beard is paint on it):
every installed triangle present exactly (position + UV + normal + joints + weights per corner, `review/exact_parts_h70.txt`), so the
face and beard render pixel-identical in both tiers (`review/sheet_face_diff_h70.png`: face black in all five views of A and B; only
the hair shell's shading differs). The collar (tunic within 1 cm of the face shell) is kept, so the beard/neck contact with the tunic
is the installed one.

## Measured first: protected share
Part labels from the creature's final master (`scripts/dump_final_parts.py` -> `work/final_parts.npz`, matched by rest centroid at
1e-7 m, `scripts/glb_parts.py`). The face shell is 29.8 % of LOD0. Linings matched to their outer faces: skirt + bell-cuff (3 mm) 456 of
462 (6 centre-seam faces unmatched, kept with their 1 cm neighbourhood; 7 ambiguous twin vertices kept), hair (2 mm) 1,140 of 1,144.
Set h keeps 44.0 % (+ the linings of kept faces = 46.8 %); 5,145 faces free, 1,596 lining faces re-emitted from the cut cloth.

## Ladder (limits for 1.797 m: p99 <= 5.39 mm, max <= 26.96 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_h.png`)
One ladder (of the three allowed): set h, tunic ratio 0.7 / 0.6 / 0.5 (`work/selection_h.json`).

| step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---:|---|---|---|
| **r70** | **9,705** | **3.18 / 20.35 (Conv1:9)** | .9952 / .9957 | **PASS, picked** |
| r60 | 9,619 | 3.69 / 35.08 (Cower:12) | .995 / .9953 | fail (max) |
| r50 | 9,569 | 5.06 / 45.76 (Cower:12) | .9878 / .9938 | fail |

r60 would save only 86 more triangles and fails the max deviation in Cower (the same spot M2d's ladders failed on), so r70 is the step.

## Gates, installed -> h r70 (`scripts/gates.sh`; `review/gates_before/`, `review/gates_h70/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_peasantm2.json` / `.txt`): **0 LOD0 escaping faces in every
  primitive** (limbs 2,123, torso 2,308, head 5,274). LOD1-3 (Blender decimate, as installed) limbs 128/117/51, torso 66/61/37, head
  107/141/92 vs installed 96/125/98, 70/73/40, 76/131/106.
- Collapse face-frames equal or lower in every clip (Standing and Walking equal; Running 493 -> 465, Cower 3,711 -> 3,113, Bow
  3,165 -> 2,959, Dead 775 -> 713); worst single-frame exposed counts differ by at most 1 (Cower groin 6 -> 7, head 7 -> 8, strip 3 -> 4;
  Running torso 4 -> 5).
- Skirt (thighs through the tunic skirt): equal in every clip except AttackMelee 1 frame 19.9 cm -> 0 and Bow 11 -> 10 frames (10.8 cm).
- Arm/hand (`--outer-only --exact`): hand depths and frames equal (Fidget R 5.3 -> 5.2 cm 15 f and Conv1 L 6.0 cm 63 -> 62 f, both MM9's
  own gestures as installed; Talk L 1.1 cm 1 f) except **Bow R 0.7 -> 1.0 cm, 0 -> 1 frame over 1 cm** (one frame at the threshold);
  forearm maxima equal or lower (Standing L 4.0 -> 3.7, Conv3 R 3.2 -> 2.7); finger stretch maxima equal, p99 up 0.01-0.08 on a few clips
  (Fidget L 1.38 -> 1.46, Dead R 1.21 -> 1.28, as M2d), AttackMelee R max 1.76 -> 1.30.
- Jitter vs the creature's `work/pm2_ref_h.glb`: output identical, **0 fails**.
- Sleeve poke (`--skin-mat PeasantM2 --cloth-mat Pm2Torso_A`, M2d's gate script read in place): identical (3 forearm-stub vertices at
  20 mm in every frame including rest, a gate artefact of the bell sleeve, as installed; candidates 146/145 -> 132/136).
- Detached: 0, 23 components both; same root-lift flags (hair shell Bow 0.040 -> 0.048, flagged before too), the installed's shallow L-hand
  flag gone, no new flag. Flat shading equal (0.00/0.01/0.01 -> 0.00/0.01/0.00). Winding 0. Bone lengths 12, 0 stretching. Texture
  quality equal (limbs atlas 59.0 -> 58.9 %, fragments 0.0 -> 0.1 %, stretch 1.26 -> 1.27; torso, head equal).
- See-through (`scripts/see_through.sh`, M2d's copy of the creature-family gate, every clip, 16 views; hole max px, `review/see_through_compare_h70.txt`):
  equal in 13 of 13 clips for boots and trousers (0); lower in Conv3/Hit/Death sleeve L, Fidget sleeve R and torso; up by 1-5 px in
  AttackMelee sleeve L 13 -> 14, Bow head 18 -> 20, Talk sleeve R 14 -> 16 and torso 5 -> 6, Dead sleeve L 49 -> 50, sleeve R 9 -> 10,
  torso 51 -> 55, Death torso 359 -> 364 (the installed's own view down into the falling tunic, az000 el20; frames with holes 241 -> 244).
  With the hip contact kept, Dead torso rises 4 px, not the 24 px M2d measured without it.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,h70}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected, snapped to the imported vertices, 40 points;
  `review/lod_check_compare_h70.txt`): height 1.7871 m at every LOD (installed LOD0 1.7883, LOD3 1.7848; LOD0 lost 1.2 mm at the hair
  crown, as M2d); every clip's lowest point at LOD1-3 equal to LOD0 except Running LOD2/3 -0.08 vs -0.21 cm (installed LOD2 floated up
  to +0.28 cm and LOD3 up to +1.33 cm, rest floor +0.95 cm); 0 stretched faces at every LOD.

## Review
Viewer (installed and reduced, both tiers, all 13 clips; `run_creature_review.py check`: 52 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm2_reduce_claude/review/viewer/
Sheets read (full size): `review/sheet_face_h70.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers),
`review/sheet_face_diff_h70.png`, `review/sheet_body_h70_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/close_h70_a_hands.png` (L/R hand outside, R hand front), `review/close_h70_{a,b}_details.png` (hair from behind above, bell cuff,
chest and buckle), `review/close_h70_{a,b}_1.png` (arms, skirt front/back, Running skirt), `review/close_h70_a_2.png` (boots, Talk arms,
shoulders from behind, Hit). Nothing differs visibly; the face and beard are pixel-identical.
Look at: the hair shell silhouette in profile and from behind (0.7, hairline exact), the fingertips (hands 0.6), the boot lacing.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_peasantm2_reduce_claude/before/mm9_peasantm2.glb REA_NODE=PeasantM2 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/dump_final_parts.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
$G scripts/extra_keeps.py                                   # keep_h = shoulder cloth | forearm stubs (part 4) | M2d's hip contact
EXTRA=work/keep_h.npy $G scripts/make_sets_pm2.py h
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=h MP_GROUPS=1:0.6,2:0.7,3:0.7,4:0.55,5:0.45,6:0.5 scripts/run_mp.sh h 0.7,0.6,0.5
scripts/build_mp.sh mp_h_r70 export/mm9_peasantm2.glb      # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm2.glb before/mm9_peasantm2.glb --json review/uv_audit_peasantm2.json
$G scripts/exact_parts.py export/mm9_peasantm2.glb h; scripts/gates.sh export/mm9_peasantm2.glb h70
work/blender_queue.sh                                       # see-through and lod_check, installed and h70, one Blender at a time
$G scripts/viewer_tiers.py export/mm9_peasantm2.glb red    # installed: viewer_tiers.py before/mm9_peasantm2.glb inst
$G scripts/make_viewer_manifest.py h70-20261105 inst_a=..=work/viewer_inst_th_a.glb red_a=..=work/viewer_red_th_a.glb inst_b=.. red_b=..
HEADUP=0,0.08,0.05 scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py h70; $G scripts/face_diff_sheet.py h70
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm2.glb` (0), `tools/install_model.py export/mm9_peasantm2.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantm2_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantm2_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantm2.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and viewer
stills only); LOD1-3 and shadow meshes by eye (numbers only); orient/handedness gates (geometry orientation unchanged, every vertex an
installed one); tier B hand close-ups (same geometry as A, limbs have one image); the eye/mouth close-ups at the user's zoom (the face
triangles are the installed ones and the five-view face diff is black).
