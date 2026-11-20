# MM9 PeasantM1d (`mm9_pm1d`, the elf townsman) reduction: candidate d r70 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 82 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:pm1d` (owner
pm1d-reduce-20261105, released); the creature's own `mm9:peasantm1d` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_pm1d.glb` (sha256 9e4828dd48e1, identical to `../mm9_peasantm1d_claude/v2/export/`), copied to
`before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm1d_claude/` was only read (its
gate scripts and LOD-chain helpers run in place, nothing written there).

**Family note:** PeasantM1 (`mm9_peasantm1.glb`, ledger row 89, `../mm9_peasantm1_claude/`) is a separate build: own Meshy Smart
Topology, own paints and head sets (skins A/B), a 3,191-triangle body against this one's 2,824. It shares the PeasantMale skeleton
and clip library, not the mesh, so it is not re-derived from this cut; only `mm9_pm1d.glb` was reduced. Its reduction can reuse these
scripts (`glb_parts.py` labels pieces from the GLB alone).

| | LOD0 | body prim `PM1d_C` (shirt, breeches, boots, belt, laces) | head prim `PM1dHead_C` (face shell, eyes/mouth, hair cards, MPFB hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 7,999 | 2,824 | 5,175 | 3,999 | 1,438 | 478 |
| **d r70 (`export/mm9_pm1d.glb` = `export/mm9_pm1d_d70.glb`, sha256 695064c17d2a)** | **6,623 (-17.2 %)** | 2,380 | 4,243 | 3,310 | 1,189 | 394 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (13), skin, nodes, materials, region ramps, `KHR_materials_variants` (pm1d_c, pm1d_d), all 8 images:
byte-identical (`review/gates_d70/same_clips.txt`). Face shell (face, elf ears, scalp, neck: 1,758) and the eye/mouth pieces (362):
every installed triangle present exactly (`scripts/exact_parts.py`: 0 missing of every kept face), so the face renders pixel-identical
in both tiers (`review/sheet_face_diff_d70.png`: face black in all five views of D and C; only hair cards and clothing shading
differ). No linings exist on this model and none were added (the user's open decision on see-through gaps).

## Measured first: protected share
Part labels from the GLB alone (`scripts/glb_parts.py`: pieces welded by position, dominant joint, head region mask R = hair):
1 shirt shell 1,334, 5 breeches 502, 6 boots 577, 8 boot cuffs 211, 9 small pieces 200 (belt buckle 64, front laces 78, boot
buckles 58), 0 MPFB hands 1,399, 20 face shell 1,758, 22 eyes/mouth 362, 21 hair cards 1,656 (12 pieces). Face exact = 26.5 % of
LOD0. Keep set (`scripts/make_sets_pm1d.py`, env below): face shell + eyes/mouth whole; the hairline (hair within 12 mm of the hair-card
rim vertices that lie on the skin, 352); collar (shirt within 1 cm of the face shell, 57); cuffs (shirt within 4 cm of the sleeve rim
over the hands, 89); soles (121); small pieces (200). Set c adds the openings the see-through gate looks into (`RIM=0.03`: faces within
3 cm of the open rims of shirt hem, breeches, boots and boot cuffs, 493); set d adds the shirt skirt under the belt and the shirt beside
the front laces (`scripts/extra_keeps.py` -> `work/keep_d.npy`, 338; from `scripts/st_probe.py` on the views where c60 raised holes).
Set d keeps 3,692 faces (46.2 %). Groups: hands + fingers 0.6 (seam slides, every finger kept), MPFB forearm skin 0.45, hair 0.7,
boots 0.75, breeches 0.75, shirt at the ladder ratio. No shoulder-cloth keep was needed (jitter equal, below).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)
PeasantM2d's copy (`../mm9_peasantm2d_reduce_claude/`) on node PM1d: scored over every clip at 10 Hz plus a position+UV rest quadric
(texture weight 4); texture guard over both tiers (`scripts/tex_extract.py`: each prim's tone image with each tier's region ramps, plus
the region mask); the Mummy chart guard (12 samples) and the audit's own chart test inside each collapse (`MP_AUDIT=1`).

## Ladders (limits for 1.777 m: p99 <= 5.33 mm, max <= 26.66 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b,c,d,d7}.png`)
| ladder | set / groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| a | a, boots 0.55, breeches 0.5 | r70 / r60 / r50 | 6,193 / 6,073 / 5,955 | 7.92 / 40.0 (Running:0) | .979 / .992 | fail: L thigh/calf = breeches and boots (`scripts/probe_err.py`) |
| b | a, boots/breeches 0.75 | r70 | 6,417 (-19.8 %) | 4.71 / 18.4 (Cower:3) | .991 / .995 | pass; built (`export/mm9_pm1d_b70.glb`): every gate equal except see-through (boot L +7-17 px, trousers L Dead 9 -> 37, torso Dead 920 -> 981, Fidget 232 -> 280) |
| b | | r60 / r50 | 6,295 / 6,177 | 5.97 / 25.9, 8.9 / 28.4 | | fail |
| c | c (+ openings) | r70 / r60 | 6,545 / 6,437 (-19.5 %) | 3.98 / 23.7, 5.30 / 25.9 (Cower:12) | .992 / .994 | pass / pass; c60 built (`export/mm9_pm1d_c60.glb`): boots and trousers back to installed; torso Dead 982, Fidget 290 |
| d | d (+ skirt, placket) | r60 / r50 | 6,541 / 6,459 | 5.68 / 25.9, 9.72 / 49.7 | | fail |
| **d** | **d** | **r70** | **6,623 (-17.2 %)** | **4.02 / 23.7 (Death:15)** | **.9923 / .9954** | **PASS, picked**: Fidget torso back to 225 (installed 232) |

Four ladders (the orchestrator capped the run there). d r70 is picked over b70/c60 because it is the only cut whose see-through
numbers are equal to the installed's apart from the items listed below.

## Gates, installed -> d r70 (`scripts/gates.sh`; `review/gates_before/`, `review/gates_d70/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_d70.json` / `.txt`): **0 LOD0 escaping faces** (PM1d_C 2,380,
  PM1dHead_C 4,243). LOD1-3 (Blender decimate, as installed): body 101/115/52, head 142/169/88 vs installed 99/107/56, 125/148/125.
- Arm/hand (the creature's `arm_hand_gate.py --outer-only --exact`): hand depths, frames and forearms identical to installed in every
  clip (Conv1 L 3.1 cm 31 f, Conv5 L 1.8 cm 13 f: MM9's chin gestures); finger stretch maxima equal or lower (Walking/Running R 1.62 ->
  1.36, Talk R 2.34 -> 2.05, Hit R 2.02 -> 1.81); 19 chains per hand.
- Jitter (the creature's `jitter_gate.py` vs its MM9-clip reference `v2/work/mm9_pm1d_clips.glb`): **4 fails = 4** (Walking and Death
  shoulder skin both sides, the installed's own; 8.52 -> 8.47, 9.78 -> 9.80 mm/f2); every other clip passes; largest rise AttackMelee
  L shoulder skin 0.29 -> 0.78 mm/f2 (limit 2.0; p95 over a thinner vertex sample, the vertices' motion is identical).
- Sleeve poke (PeasantM2d family `sleeve_poke_gate.py --skin-mat PM1dHead_C --cloth-mat PM1d_C`): identical depths and frames in every
  clip; candidate vertices 92/110 -> 77/95.
- Collapse face-frames lower in every clip (Standing 467 -> 175, Cower 2,580 -> 1,955, Conv5 5,090 -> 2,954).
- Detached 0 (same shallow flags), flat shading 0.00 both, winding 0, bone lengths 12 / 0 stretching, texture quality equal (head
  fragments 1.5 -> 1.9 %).
- **See-through** (the family `see_through_gate.py`, 16 views, `review/see_through_compare_d70.txt`; all four GLBs in
  `review/see_through_compare_all.txt`; step 9 for 12 clips + Conv5 at step 45, both GLBs the same way: the step-3 pass took ~5 h per
  GLB). The installed already shows holes in every clip (torso up to 1,340 px, boots 450). Zone maxima summed 13,503 -> 13,540. Equal or
  lower: boots, trousers (except Running L 209 -> 211, Death L 75 -> 77, AttackMelee +1), Fidget torso 232 -> 225, Walking/Standing/Cower
  torso. **Higher: torso Dead 920 -> 980 px** (the corpse's own hem/skirt opening seen from floor level, az045 el00; same shape,
  `review/st_pair_torso_Dead_0_az045.png`; the skirt keep did not move it), **head (hair cards at 0.7) +2..+8 px in 9 clips** (Standing
  63 -> 69, Fidget 71 -> 79, Talk 98 -> 103, Running 45 -> 50), torso +3..+10 px in Conv1/Conv4/Hit/Death, sleeves +1..+6 px (Dead L
  94 -> 100), collar +1 px.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,d70}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected and snapped, 59 points), the creature's
  `shrink_shadow_lods.py` and `fix_winding.py`: every clip's lowest point at LOD1-3 equal to LOD0 (Walking LOD2/3 -0.12 vs -0.23 cm;
  installed LOD2/3 floated up to +1.2 / +1.65 cm and LOD3 sank -0.98 cm in Death); 0 stretched faces at LOD1-3 (LOD0 as installed);
  heights LOD0-2 1.7897 (installed 1.790-1.793), **LOD3 1.8061 (+1.6 cm above the crown: one decimated vertex; installed LOD3
  +0.5 cm)**.

## Review
Viewer (installed and reduced d r70, both tiers, all 13 clips; `run_creature_review.py check`: 52 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_pm1d_reduce_claude/review/viewer/
Sheets read (d70): `review/sheet_face_d70.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/sheet_face_diff_d70.png`,
`review/sheet_body_d70_{d,c}.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_d70_d_handsclose.png` (both hands
outside and front), `review/close_d70_c_details.png` (hair from behind above, sleeve, chest laces and buckle), `review/close_d70_d_1.png`
(arms, boots, Running hem), `review/close_d70_d_2.png` (Talk, shoulders from behind, Hit). The same set for b70 (`review/*b70*`).
No visible difference found.
Look at: the corpse's hem from floor level (see-through +60 px), the hair cards from behind, the fingertips (hands 0.6), LOD3's crown.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_pm1d_reduce_claude/before/mm9_pm1d.glb REA_NODE=PM1d $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/extra_keeps.py
RIM=0.03 EXTRA=work/keep_d.npy $G scripts/make_sets_pm1d.py d
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=d MP_GROUPS=1:0.6,2:0.7,4:0.75,5:0.45,6:0.75 scripts/run_mp.sh d7 0.7
scripts/build_mp.sh mp_d7_r70 export/mm9_pm1d_d70.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_pm1d_d70.glb before/mm9_pm1d.glb --json review/uv_audit_d70.json
$G scripts/exact_parts.py export/mm9_pm1d_d70.glb d; work/queue_d70.sh   # gates.sh, see_through.sh st_main/st_conv5, lod_check.py
python3 scripts/st_compare.py before d70
$G scripts/viewer_tiers.py export/mm9_pm1d.glb red   # installed: viewer_tiers.py before/mm9_pm1d.glb inst
$G scripts/make_viewer_manifest.py <rev> inst_c=..=work/viewer_inst_th_c.glb red_c=.. inst_d=.. red_d=..
HEADUP=0,0.08,0.05 scripts/shots.sh; scripts/close_shots.sh; scripts/hand_shots.sh; $G scripts/shot_sheets.py d70; $G scripts/face_diff_sheet.py d70
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_pm1d.glb` (0), `tools/install_model.py export/mm9_pm1d.glb --world mm9`,
the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantm1d_claude/README.md`: "LOD0 reduced post-install on
<date> by `mm9_pm1d_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_pm1d.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates and viewer stills
only); LOD1-3 and shadow meshes by eye (numbers only); see-through at the gate's full step-3 density; C-tier hand close-ups (same
geometry as D, seen in the body and face sheets).
