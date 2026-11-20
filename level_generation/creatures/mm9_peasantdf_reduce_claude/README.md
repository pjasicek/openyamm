# MM9 dwarf townswomen PeasantDF1-4 (`mm9_peasantdf1..4`) reduction: candidate f55 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: the
relaxed keep set, face exact; one agent per GLB family, the shared body reduced once), ledger rows 17, 23, 24, 25 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantdf` (owner peasantdf-reduce-20261104); the creature's own
`mm9:peasantdf` lease was free. Sources: the installed `assets_source/worlds/mm9/models/mm9_peasantdf{1,2,3,4}.glb` (sha256
427a0e944504, 14931a12370d, c59945aa9daf, 60c6bcd2dd83; identical to `../mm9_peasantdf_claude/export/`), copied to `before/`
(the rollback sources). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantdf_claude/` was only read.

## What the four GLBs share and why DF3 is heavier
`scripts/design_map.py` (exact byte keys of position, UV, normal, joints, weights) and `scripts/df_parts.py`:
- **Body primitive** (PeasantDF_A, DF2 PeasantDF_B; 6,311 triangles): byte-identical in all four designs apart from one
  one-texel face (row 6310) whose three corners carry per-design UVs (a paint touch). Same rig, same clips.
- **Head primitive** (7,165): head skin with face and neck seam (2,081), two modelled ears (2 x 832), the two MPFB hands (2 x 700)
  are byte-identical in all four; the hair/hood shell and its back-side twin (2 x 1,010) have per-design positions
  (`headwear.py`) and per-design weights near the ears (job 7).
- **DF3 = +408 triangles**: the two plaited braids (2 x 204, on the LF/RF_tail chains), head primitive 7,573. Nothing else differs.
- Back-side twins (`twin_faces.py` of the creature: reversed copies 1.5-2 mm behind skirt, apron, stockings, puffed sleeves,
  wrist rings, boot tops, hair): 2,112 body twin faces pair exactly with an outer face (same UVs reversed, same weights); 46
  skirt twins and the hair twins are not cut.

## One cut, four designs
The cut is made once on DF1 (`scripts/mpqem_df.py`, the body primitive and the hands) and applied to every design by the exact
vertex map (`scripts/swap_df.py`): body triangles mapped byte for byte (DF2-4 body faces = DF1's 4,818 of 4,819 + their own
row 6310), head primitive = each design's own installed rows (face, ears, neck, hair/hood + twin, DF3 braids: all exact) + DF1's
reduced hand triangles mapped onto the design's hand vertices. Every vertex of every candidate is an installed vertex
(`scripts/exact_check.py`: 0 new; every installed non-hand head face present). Clips, skin, nodes, materials, region ramps,
`KHR_materials_variants`, all 8 images byte-identical (`same_clips.py`).

| | LOD0 | body prim | head prim (hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed DF1 / DF2 / DF4 | 13,476 | 6,311 | 7,165 (1,400) | 6,736-6,737 | 2,423 | 806-807 |
| installed DF3 | 13,884 | 6,311 | 7,573 (1,400) | 6,941 | 2,498 | 831 |
| **f55 DF1 / DF2 / DF4** | **11,424 (-15.2 %)** | 4,819 | 6,605 (840) | 5,710-5,711 | 2,054 | 683-684 |
| **f55 DF3** | **11,832 (-14.8 %)** | 4,819 | 7,013 (840) | 5,915 | 2,128 | 707 |

Candidates: `export/mm9_peasantdf{1,2,3,4}.glb` (sha256 af2f8589d9d0, b059495c478d, df5ddacf9954, a2ad79f5b656).

## Keep set (`scripts/make_sets_df.py`, set b: SHOULDER=0.3 NECKW=0.3)
Protected share 50.2 %: the whole head primitive but the hands (5,765), the neck/collar (body faces within 3 cm of a head-skin
vertex: the r6/job 7 neck paint field and seam), under the headwear (body faces within 2 cm of a hair/hood/braid vertex of ANY
design), the hand-graft junction (forearm faces within 1.5 cm of a hand vertex), soles (1.2 cm), pieces up to 80 faces, row 6310,
the 46 unpaired skirt twins and the outer faces within 1.5 cm of them. Groups: hands 0.6 (seam slides, every finger kept),
shoulders (UpperArm + Clavicle weight > 0.3) 0.8, neck-weighted upper back/chest 0.75, skirt 0.66, boots 0.75, hidden
stockings 0.85, forearms 0.75, rest of the dress at the ladder ratio. Twins re-emitted as reversed copies of the surviving lined
outer faces through the exact outer -> twin vertex map; a lined-border vertex may collapse when every lined face it leaves keeps
twin-mapped corners (`MP_LINEDSLIDE=1`).

## Route: pose-aware half-edge collapse (`scripts/mpqem_df.py`, from PeasantF3's mpqem.py)
Scored over every clip at 10 Hz plus the position+UV rest quadric (texture weight 4); texture guard over all seven tiers of the
four designs plus their region masks (`scripts/tex_extract_df.py`; refuse > 100 any sample / > 45 mean); chart guard sampled at 12.

## Ladders (limits for 1.176 m: p99 <= 3.53 mm, max <= 17.6 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm | result |
|---|---|---:|---|---|
| a | hands .6, skirt .6, boots .7, stockings .85, forearms .5, dress r55-35 (lined borders locked) | 11,112 (dress stalls) | 5.73 / 30.9 (AttackMelee shoulder) | fail |
| b | + seam and lined-border slides; dress r80 / r70 / r60, skirt .75, hands .65 | 11,848 / 11,670 / 11,486 | 2.53, 3.03 / 17.2, 4.03 / 24.7 | pass / pass (-13.4 %) / fail |
| c | dress only r60-40 | 12,797-12,601 | 3.24 / 24.7 (shoulder) | fail |
| d | set b: shoulders .8, neck-weighted .75, skirt .7, forearms .75 | 11,578 | 3.33 / 16.58 | pass (-14.1 %) |
| e | d, skirt .6, hands .6 | 11,297 | 3.75 / 16.58 | fail |
| **f** | **d, skirt .66, hands .6** | **11,424** | **3.52 / 16.58 (Walking:12)** | **PASS, picked** (IoU .9966, SSIM .9944) |
| g / h | f, boots .6 + stockings .7 / stockings .75 | 11,241 / 11,356 | 3.73, 3.63 | fail |
| xf | f with forearms whole (fallback, `work/mp_xf_r55.npz`, built to `work/alt_xf/`) | 11,478 (-14.8 %) | not run (fewer cuts than f) | |
The numpy check of step a (`scripts/err_parts.py`) put the worst deviations at the right shoulder/armpit (UpperArm/Clavicle
weights, AttackMelee, Hit), the upper back (Neck weights) and the front skirt: hence the shoulder and neck groups.

## Gates, installed -> f55 (the creature's own scripts, `scripts/gates_df.sh` per design; `review/gates_before/d<n>/`, `review/gates_f55/d<n>/`, summary `scripts/gate_summary.py f55`)
Identical in all four designs unless noted:
- **UV chart audit (hard gate)**: 0 LOD0 faces leave the charts in every node of all four (`review/uv_audit_df<n>.json`); LOD1-3
  at the installed baseline (body LOD1 170 vs 164, LOD2 121 vs 176, LOD3 52 vs 75; head LODs within a few faces of the source).
- Arm/hand (`--outer-only`): 0 frames > 1 cm in every clip, both hands; forearm max 0.6 cm (AttackMelee R, as installed);
  finger stretch max 1.97 both; 19 joints per hand. Jitter: 0 fails both. Sleeve poke: 0 mm in every clip, both sides.
- Detached: 0 in any pose (24 components, DF3 26), both. Flat 0.00. Winding 0 (all LODs and shadows). Bones: 12 checked, the
  same 2 (thighs hang from the Scene Root, as installed). Texture quality: body atlas 61.2 -> 61.1 %, stretch p90 1.08 -> 1.09;
  head set unchanged (41.3 -> 41.2 %, DF3 49.3 %). Clips/skin/nodes/materials/images byte-identical (`same_clips.py`).
- Ear poke and headwear: the head primitive (ears, hair/hood shells, braids) is the installed rows of each design, so the job 7
  ear-poke results (0.0 mm) hold unchanged; not re-run.
- Robe (legs through skirt; the creature README records it as a numeric fail that does not fit this skirt): every frame "fails"
  in both; maxima Standing 1.2 -> 0.8, Talk 2.8 -> 5.7, Fidget 3.3 -> 5.8, Hit 4.3 -> 7.0, AttackMelee 5.6 -> 6.9 cm. The
  worst vertices (`scripts/robe_gate_where.py`) are stocking tops 25 cm up at the centre under the skirt, 8 cm inside the
  cloth, measured against inner skirt faces; the textured lower-body shots of those frames (`review/sheet_legs_skirt_f55.png`:
  Hit, AttackMelee, Talk, Fidget, Running, Walking) show no leg or boot through the skirt, installed and reduced alike.
- See-through (`scripts/see_through_df.sh`, the creature's gate, every clip, 16 views, 3 mm px; installed = the job 7 runs;
  `scripts/see_compare.py f55`), worst hole px installed -> f55, d1 / d2 / d3 / d4: head and hair 0 -> 0 all; skirt 43/42/43/43
  -> 44/43/43/44; collar 18/14/13/13 -> 17/13/14/14; torso max 17/18/17/19 -> 17/17/17/17 (frames with a hole 8-10 -> 13-17);
  boots L 9/8/8/7 -> 12/9/9/8, R 13/8/9/15 -> 13/8/9/17; **sleeves L 27/27/27/25 -> 33/32/32/29, R 47/45/49/45 -> 50/47/51/51**,
  at the same wrist-band spot and worst frame as installed (`review/sheet_see_sleeves_f55.png`: AttackMelee 6 and Death 9).
- **Fallback xf (forearms whole, `work/alt_xf/mm9_peasantdf<n>.glb`)**: the sleeve increase comes from the forearm cut (the
  wrist-ring twins): with group 5 kept, DF1 see-through sleeve L 33 -> 27 (installed 27), R 50 -> 49 (installed 47), every other
  zone as f55. LOD0 11,478 (-14.8 %), DF3 11,886 (-14.4 %); LODs 5,737-5,738 / 2,062 / 687-688 (DF3 5,942 / 2,136 / 711); UV audit
  0 LOD0 escaping on all four (`review/uv_audit_xf_df<n>.json`), every vertex installed (`CAND=work/alt_xf exact_check.py`).
  Not run on xf: the numeric gates, see-through d2-d4, viewer, sheets (the only geometry difference to f55 is 54 forearm faces
  and their twins kept as installed).
- LODs (`scripts/lod_numbers.py`, every 30 fps frame; `review/lod_numbers_d234.txt`): height at every LOD = LOD0 (DF1 1.174,
  DF2 1.172, DF3 1.192, DF4 1.222 m; installed LOD3 lost 0.3-1.0 cm); LOD1-2 lowest point within 0.13 cm of LOD0 in every clip;
  LOD3 0.00 in Standing (installed +0.88 cm) and Dead 0.00 (installed +1.5 to +2.8 cm), worst Running +0.80 (installed +0.87).

## Review
Viewer (installed and reduced side by side, all seven tiers, every clip; `run_creature_review.py check`: 154 switches, 0 failed,
0 console errors): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdf_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_f55_<tier>.png` (front close-up, 3/4, true profile, low 3/4, party; installed / f55 / diff x4;
the face box 0.00 % changed pixels in front, profile and low 3/4 for every tier, 3/4 0.26-0.41 % from the shoulder in frame),
`review/sheet_face_f55_rest.png`, `review/sheet_body_f55_<tier>.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/sheet_close_f55_<tier>.png` (arms, skirt front/back, Running skirt, feet, Talk arms, Hit, both hands outside, R hand front,
hem from below), `review/sheet_chest_f55.png` (DF1/3/4 chest front, 3/4, upper back: brooches, lacing, pendant, chains),
`review/sheet_legs_skirt_f55.png`, `review/sheet_see_sleeves_f55.png`, `review/ladder_sheet_f.png`.
Look at: the hands (0.6, every finger kept: slightly smoother knuckles), the bodice shading under the brooches and chains (same paint,
the cut chest faces shade a little differently), the wrist bands from the front in AttackMelee (see-through +3-6 px).

## Not checked
In game (not installed; binding regression and floor audit after install); motion at normal speed by eye (gates, stills and the
viewer only); LOD1-3 and shadow meshes by eye (numbers only); the ear-poke gate (head rows exact, not re-run); the faces at the
user's eye/mouth zoom (installed triangles, diff black).


## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantdf_reduce_claude/before/mm9_peasantdf1.glb REA_NODE=PeasantDF $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/design_map.py; $G scripts/df_parts.py 1; $G scripts/tex_extract_df.py
$G scripts/make_sets_df.py a; SHOULDER=0.3 NECKW=0.3 $G scripts/make_sets_df.py b
MP_GROUPS=1:0.6,2:0.66,3:0.75,4:0.85,5:0.75,6:0.8,7:0.75 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=0,1,2,3,4,5,6,7 MP_LINEDSLIDE=1 SETS=b scripts/run_mp_df.sh f 0.55
scripts/build_df.sh mp_f_r55          # swap_df -> build_lods (protected, snapped) -> creature's shrink_shadow_lods -> carry_variants -> check_winding
for n in 1 2 3 4; do $G ../claude_shared/reduction_uv_audit.py export/mm9_peasantdf$n.glb before/mm9_peasantdf$n.glb --json review/uv_audit_df$n.json; $G scripts/exact_check.py $n; done
scripts/gate_queue.sh; scripts/see_through_df.sh f55; python3 scripts/see_compare.py f55; $G scripts/lod_numbers.py export/mm9_peasantdf1.glb
for n in 1 2 3 4; do for s in inst red; do $G scripts/viewer_tiers_df.py $([ $s = inst ] && echo before || echo export)/mm9_peasantdf$n.glb $n $s; done; done
python3 scripts/make_viewer_manifest.py f55-20261104 inst_d1a=..=work/viewer_inst_d1a.glb red_d1a=..=work/viewer_red_d1a.glb ...
scripts/shots_df.sh <models>; $G scripts/sheets_df.py f55
```
Install (orchestrator, on the OK): for each n `check_winding.py export/mm9_peasantdf$n.glb` (0), `tools/install_model.py
export/mm9_peasantdf$n.glb --world mm9`, then the `mm9_actor_models_build_every_binding` regression and the floor audit, and add to
`../mm9_peasantdf_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantdf_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantdf{1,2,3,4}.glb`.
