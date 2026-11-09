# MM9 PeasantM2d (`mm9_peasantm2d`, the young elf townsman) reduction: candidate h r70 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 22 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm2d` (owner
peasantm2d-reduce-20261104); the creature's own `mm9:peasantm2d` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm2d.glb` (sha256 af2bba9bb57b, identical to `../mm9_peasantm2d_claude/export/`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm2d_claude/` was only
read (its final master `work/final_v2.blend` opened read-only for part labels, its gate scripts run in place).

**Family note:** PeasantM2d is PeasantM2's body (`mm9_peasantm2.glb`, ledger row 45) plus elf ears, a closed mouth and an upper-tunic
lining, but it is built and installed as its own GLB (own rebuild chain, own paints). Only `mm9_peasantm2d.glb` was reduced here;
PeasantM2 can reuse this project's scripts (same part labels, same linings minus the upper-tunic one).

| | LOD0 | limbs (hands, forearm stubs, trousers, boots) | torso (tunic, skirt, belt, linings) | head (face shell, ears, hair + lining) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 13,599 | 3,519 | 3,620 | 6,460 | 6,798 | 2,445 | 814 |
| **h r70 (`export/mm9_peasantm2d.glb`, sha256 e685f22736e4)** | **11,099 (-18.4 %)** | 2,123 | 3,112 | 5,864 | 5,548 | 1,995 | 663 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (10), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 11 images: byte-identical
(`review/gates_h70/same_clips.txt`). Face shell (face, scalp, neck, eyes, mouth: 3,584) and elf ears (588): every installed triangle
present exactly (position + UV + normal + joints + weights per corner, `scripts/exact_parts.py`), so the face renders
pixel-identical in both tiers (`review/sheet_face_diff_h70.png`: face black in all five views of D and C; only the hair shell and
the tunic shading differ).

## Measured first: protected share
Part labels from the creature's final master (`scripts/dump_final_parts.py` -> `work/final_parts.npz`, matched to the GLB faces by
rest centroid at 1e-7 m, `scripts/glb_parts.py`). Face shell + ears are 31 % of LOD0. Every lining face (skirt + bell-cuff 3 mm,
upper tunic 3 mm, hair 2 mm) was matched to the outer face it was copied from (2,562 of 2,576; 14 centre-seam faces unmatched and
kept with their neighbourhood; 7 ambiguous twin vertices kept), so cut cloth gets its lining re-emitted from the installed twin
vertices (the hair lining keeps the hair's own UVs per GLB vertex). Final set h keeps 43.4 % (+ the linings of kept faces = 49.6 %).

Keep set (`scripts/make_sets_pm2d.py h`, EXTRA `work/keep_h.npy`): face shell and ears whole; the hairline (hair within 12 mm of the
hair shell's open rim); the collar (tunic within 1 cm of the face shell: the neck seam); the bell cuffs (tunic within 4 cm of the cuff
rim, with the two-sided hem); belt strap and buckle whole; skirt cap; soles; pieces up to 80 faces; the shoulder/upper-sleeve cloth
(every face touching a vertex dominated by a Clavicle or UpperArm joint: the jitter gate's shoulder-skin sample); the Meshy forearm
stubs inside the sleeves (part 4, 176); the corpse's hip contact (trousers, skirt and skirt-lining faces within 6 cm of three
points at the right hip and their mirrors: the installed front faces that cover the Dead/Death see-through sliver at the belt; e r70
without them raised that hole 51 -> 75 px).
Groups: hands + fingers 0.6 (seam slides, every finger kept), MPFB forearm skin 0.45, hair 0.7, skirt 0.7, boots 0.55, trousers 0.5,
tunic at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)
PeasantF3's copy (Thrall/Highwayman lineage) with: node PeasantM2d; texture guard over both tiers (torso: tone x region ramps per
tier + region mask; head: each tier's image; limbs: one image), `scripts/tex_extract.py`; the Mummy chart guard (`MP_CHART=1`, 12
subdivisions); **the audit's own chart test inside each collapse** (`MP_AUDIT=1`: `reduction_uv_audit.Charts` of each source
primitive at its image size, any sample off -> refused; without it step a r60 left 1 limbs face at 2.2 % off, colour error 4);
texture weight 4 (`MP_W5`); linings re-emitted from glb_parts.py's face pairs and per-vertex twins. Scored over 201 poses (every clip
at 10 Hz) plus a position+UV rest quadric.

## Ladders (limits for 1.797 m: p99 <= 5.39 mm, max <= 26.96 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / change | step | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | a (face/ears/hairline/collar/cuffs/belt kept), no audit test | r60 / r50 / r40 | 10,421 / 10,169 / 10,153 | 3.72/16.8, 6.2/40.6 (Cower), 6.9/50.6 | pass / fail / fail; r60 had 1 UV-audit face |
| b | a + audit chart test | r60 / r55 | 10,421 / 10,293 | 3.72/16.8, 4.48/41.2 (Cower) | pass / fail. b60 built (`export/mm9_peasantm2d_b60.glb`): UV audit 0, but jitter shoulder-skin AttackMelee L 0.31 -> 3.39 mm/f2 FAIL (p95 over a thinner vertex sample) and a new root-lift flag on the cut L forearm stub |
| c | b + shoulder cloth kept | r60 | 10,811 | not run to the end | jitter 0 fails; forearm-stub root lift remained |
| d | c + forearm stubs kept | r60 | 10,899 | 3.96 / 40.5 (Cower:12) | fail (tunic cut concentrated on fewer faces) |
| e | d, tunic gentler | r75 / r70 | 11,123 / 11,051 | 2.92/15.2, 3.03/16.8 (AttackMelee:12) | pass / pass; e70 built (`export/mm9_peasantm2d_e70.glb`): every gate equal except see-through torso Dead 51 -> 75 px, Death 88 -> 92 px (the trousers/skirt cut at the hip uncovered more of the installed belt sliver) |
| f | d + skirt kept | r70 | 11,163 | Dead/Death see-through only | Dead still 75 px: not the skirt |
| **h** | **d + hip contact kept (see keep set)** | **r70** | **11,099** | **2.97 / 16.8 (AttackMelee:12)** | **PASS, picked** (IoU .9952, SSIM .9961); probe (`scripts/st_probe.py`) Dead az315 el20 holes 61 (installed) / 86 (e70) / 66 |

## Gates, installed -> h r70 (PeasantM2d's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_h70/`)
- Collapse face-frames equal or lower in every clip (Standing 777 = 777, Talk 1,741 -> 1,682, Cower 3,896 -> 3,003, Hit 374 -> 332).
- Skirt (thighs through the tunic skirt): equal in every clip; AttackMelee 1 frame 19.9 cm -> 0.
- Arm/hand (`--outer-only --exact`): hand depths and frames equal (Fidget R 5.3 -> 5.2 cm, 15 f, MM9's forehead rub as installed;
  Talk L 1.1 cm, 1 f); forearm maxima equal or lower; finger stretch maxima equal, p99 up 0.01-0.08 on a few clips (Fidget L
  1.38 -> 1.46, over a thinner edge sample); 19 chains per hand.
- Sleeve poke (`--skin-mat PeasantM2d --cloth-mat Pm2dTorso_D`): identical in every clip (the installed reads 20 mm on 3 forearm-stub
  vertices in every frame including rest: a gate artefact of the bell sleeve, kept as installed). With those vertices excluded
  (`scripts/sleeve_poke_common.py --only`, run for b60) the installed and the cut sleeves give the same 0.7-1.5 mm pokes.
- Jitter vs the creature's `work/pm2d_ref_h.glb`: 0 fails = 0 (b60, which cut the shoulder cloth, failed AttackMelee L shoulder skin on
  the thinner p95 sample; the shoulder cloth is kept since c).
- Detached: 0, 26 components both; the installed's shallow L-hand flag is gone, no new flag. Flat shading equal (0.00/0.01/0.07).
  Winding 0. Bone lengths 12, 0 stretching. Texture quality equal (limbs fragments 0.0 -> 0.2 %).
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_peasantm2d.json`): **0 LOD0 escaping faces in every
  primitive**; LOD1-3 (Blender decimate) limbs 129/120/55, torso 66/70/37, head 70/155/95 vs installed 96/125/98, 70/72/40, 63/150/97.
- See-through (`scripts/see_through.sh`, the creature's `see_through_gate.py`, every clip, 16 views; hole max px):
  torso 88 -> 92 (Death 18 az315 level, same frame and view; at 20 deg 57 -> 59; Dead 51 -> 55), head 9 -> 10, sleeve L 28 -> 26,
  sleeve R 20 -> 19, boots/trousers 0; frames with holes equal (torso 158 -> 159). The torso worst is the installed belt sliver of the
  corpse (`review/st_pair_torso_Dead_0_az315_el20.png`); e70 had raised it to 75 px, the hip-contact keep brought it back.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,h70}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected, snapped to the imported vertices): height
  1.7871 m at every LOD (installed LOD0 1.7883, LOD3 1.7774; LOD0 lost 1.2 mm at the hair crown); every clip's lowest point at
  LOD1-3 equal to LOD0 except Running LOD2/3 -0.08 vs -0.21 cm (installed LOD2/3 floated up to +1.33 cm); 0 stretched faces.

## Review
Viewer (installed and reduced, both tiers, all 10 clips; `run_creature_review.py check`: 40 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm2d_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_h70.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/sheet_face_diff_h70.png`,
`review/sheet_body_h70_{d,c}.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_h70_d_hands.png` (L/R hand outside,
R hand front), `review/close_h70_d_details.png` (bell cuff, chest trim and buckle, hair from behind above), `review/close_h70_d_1.png`
(arms, skirt front/back, Running), `review/close_h70_d_2.png` and `review/close_h70_c_2.png` (boots, Talk arms, shoulders from behind,
Hit), `review/crop_hair_f2_d.png` (hair profile at full size; same hair cut), and the same sets for e70 (`review/*e70*`); see-through
shots `review/st_pair_torso_Dead_0_az315_el20.png` (installed | e70, the sliver that set h fixes).
Look at: the hair shell silhouette in profile and from above (0.7, hairline exact), the fingertips (hands 0.6), the boot lacing.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm2d_reduce_claude/before/mm9_peasantm2d.glb REA_NODE=PeasantM2d $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/dump_final_parts.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
EXTRA=work/keep_h.npy $G scripts/make_sets_pm2d.py h      # keep_h = keep_shoulder.npy | part 4 | hip contact (see the keep set)
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=h MP_GROUPS=1:0.6,2:0.7,3:0.7,4:0.55,5:0.45,6:0.5 scripts/run_mp.sh h 0.7
scripts/build_mp.sh mp_h_r70 export/mm9_peasantm2d.glb    # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm2d.glb before/mm9_peasantm2d.glb --json review/uv_audit_peasantm2d.json
$G scripts/exact_parts.py export/mm9_peasantm2d.glb h; scripts/gates.sh export/mm9_peasantm2d.glb h70
REA_NODE=PeasantM2d $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantm2d.glb h70; scripts/see_through.sh export/mm9_peasantm2d.glb h70
$G scripts/viewer_tiers.py export/mm9_peasantm2d.glb red   # installed: viewer_tiers.py before/mm9_peasantm2d.glb inst
$G scripts/make_viewer_manifest.py <rev> inst_d=..=work/viewer_inst_th_d.glb red_d=..=work/viewer_red_th_d.glb inst_c=.. red_c=..
HEADUP=0,0.08,0.05 scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py h70; $G scripts/face_diff_sheet.py h70
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm2d.glb` (0), `tools/install_model.py export/mm9_peasantm2d.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantm2d_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantm2d_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantm2d.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); orient/handedness gates (geometry orientation unchanged, every
vertex an installed one); the eye/mouth close-ups at the user's zoom (the face triangles are the installed ones and the five-view face
diff is black).
