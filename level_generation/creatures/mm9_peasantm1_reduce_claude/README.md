# MM9 PeasantM1 (`mm9_peasantm1`, the human townsman) reduction: candidate e r75 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 89 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm1` (owner
peasantm1-reduce-20261105, released); the creature's own `mm9:peasantm1` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm1.glb` (sha256 f673e8a0a768, identical to `../mm9_peasantm1_claude/export/mm9_pm1.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm1_claude/` (gate
scripts, clip reference, shadow-LOD helper) and `../mm9_peasantm1d_claude/scripts/fix_winding.py` were only read. Scripts are copies
of `../mm9_pm1d_reduce_claude/` (PeasantM1d, -17.2 %), adapted to this mesh.

| | LOD0 | body prim `PeasantM1_A` (jacket, shirt front, trousers, boots, laces, buckles) | head prim `PeasantM1Head` (face shell, hair shell, MPFB hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 7,354 | 3,191 | 4,163 | 3,676 | 1,321 | 437 |
| **e r75 (`export/mm9_peasantm1.glb` = `export/mm9_peasantm1_e75.glb`, sha256 c3457c3fec6b)** | **6,200 (-15.7 %)** | 2,789 | 3,411 | 3,099 | 1,112 | 367 |

Every vertex of the candidate is an installed vertex (only index buffers changed). Clips (13), skin, nodes, materials, region ramps,
`KHR_materials_variants` (pm1_a, pm1_b), all 9 images: byte-identical (`review/gates_e75/same_clips.txt`). Face shell (face with the
painted beard, ears, scalp, neck: 1,904) and every kept face present exactly (`scripts/exact_parts.py`: 0 missing), so the face renders
pixel-identical in both tiers (`review/sheet_face_diff_e75.png`: face black in all five views; only the hair shell's shading and
clothing edges differ). No linings exist on this model and none were added (the user's open decision on see-through gaps).

## Protected share (measured first)
Parts from the GLB alone (`scripts/glb_parts.py`): 1 jacket 1,431, 3 shirt front in the jacket opening 167, 5 trousers 620, 8 boots +
boot cuffs 805, 9 small (laces 78, boot buckles 90) 168, 0 MPFB hands 1,398 (1,272 hand/fingers, 126 forearm skin), 20 face shell
1,904, 21 hair shell 861 (no eye pieces: dropped at the creature's export; the head set has no region mask, tier B has its own head
image). Face exact = 25.9 % of LOD0. Set c (pm1d's recipe: face whole, hairline 53, collar 104, cuffs 69, soles 81, small, openings
within 3 cm of the open rims of jacket, shirt, trousers and boots 975) keeps 45.3 %; -15 % needs 27 % of the free part, so the run went
ahead. Set d = c + the whole shirt front (46.1 %). Set e = d + the body faces within 4 cm of every face the see-through gate's new hole
pixels hit (st_probe.py, six clip/frame/views, installed and d70) + the forearm skin (`scripts/extra_keeps_pm1.py`; 49.9 %, 3,682 free).
Groups: hands + fingers 0.6 (seam slides, every finger kept), forearm skin 0.45 (set d), hair shell 0.7, boots 0.75, trousers 0.75,
jacket at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM1d's copy)
Scored over every clip at 10 Hz plus a position+UV rest quadric (texture weight 4); texture guard over both tiers (`scripts/tex_extract.py`:
body tone with each tier's ramps + region mask; head: each tier's own image); the Mummy chart guard and the audit's chart test inside
each collapse (`MP_CHART=1 MP_AUDIT=1`).

## Ladders (limits for 1.766 m: p99 <= 5.30 mm, max <= 26.5 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{d,e,e8}.png`)
| ladder | set | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| d | d | r70 | 6,100 (-17.1 %) | 4.17 / 23.2 (Running:0) | .996 / .995 | pass; built (`export/mm9_peasantm1_d70.glb`), every gate equal or better except see-through 6,142 -> 6,211 (sleeves +1..+6 px) |
| d | d | r60 | 6,014 | 5.12 / 29.4 (Bow:24) | | fail |
| e | e | r70 / r60 | 6,164 / 6,094 | 4.48 / 30.3 (Bow:27), 5.95 / 33.2 | | fail |
| **e8** | **e** | **r75** | **6,200 (-15.7 %)** | **3.93 / 26.42 (Fidget:36)** | **.9964 / .9946** | **PASS, picked** |
| e8 | e | r80 | 6,236 (-15.2 %) | 3.71 / 23.2 | .996 / .995 | pass; built (`export/mm9_peasantm1_e80.glb`), see-through 6,186 (same as e75), gates equal |

Three ladders (the cap). e r75 is the lowest passing step of the last ladder; e80 gives the same see-through numbers for 36 more
triangles (its max error has more margin: 23.2 vs 26.42 mm, limit 26.5).

## Gates, installed -> e r75 (`scripts/gates.sh`; `review/gates_before/`, `review/gates_e75/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_e75.json` / `.txt`): **0 LOD0 escaping faces** (PeasantM1_A
  2,789, PeasantM1Head 3,411). LOD1-3 (Blender decimate, as installed): body 104/129/58, head 101/127/78 vs installed 98/111/66, 84/117/76.
- Arm/hand (the creature's `arm_hand_gate.py --outer-only --exact`): hand depths and frames identical in every clip (Conv5 L 2.2 cm 15 f,
  Bow R 3.8 cm 9 f, Bow L 1.5 cm 1 f, the installed's own); forearms equal or lower (Standing L 0.9 -> 0.7, Conv4 L 3.1 -> 2.5 cm).
- Jitter (the creature's `jitter_gate.py` vs `../mm9_peasantm1_claude/work/mm9_pm1_clips.glb`): **8 shoulder-skin flags = 8**, the
  installed's own (Walking/Death both sides, Talk R, Conv4 R, Conv5 L, Bow); Talk R 3.07 -> 2.33, Conv4 R 3.12 -> 2.73, Conv5 L 6.22 -> 6.36
  mm/f2 (upper-arm excess identical, 3.44 deg/f from the creature's hand-rest push).
- Sleeve poke (`sleeve_poke_gate.py --skin-mat PeasantM1Head --cloth-mat PeasantM1_A`): identical depths and frames in every clip.
- Collapse face-frames lower or equal in every clip (Standing 922 -> 740, Cower 3,788 -> 3,450, Conv5 5,948 -> 5,480, Dead 403 = 403).
- Detached 0 (same shallow flags), flat shading 0.00 both, winding 0, bone lengths 12 / 1 stretching (L Thigh, the installed's own),
  texture quality equal (body identical; head fragments 1.9 -> 2.6 %).
- **See-through** (`scripts/see_through_gate.py`, 16 views; step 9 for 12 clips + Conv5 at step 45, every GLB the same way;
  `review/see_through_compare_all.txt` = installed / d70 / e75 / e80). The installed already shows holes in every clip (torso up to 501 px).
  Zone maxima summed **6,142 -> 6,187 (+0.7 %)**; d70 had 6,211. Equal or lower: Conv5 (all), Dead, Death torso/collar/sleeves, Walking,
  Talk torso (437 -> 425), every left sleeve except Conv4 +2, Dead +0, Cower +1, Hit +0. **Still higher by a few pixels on holes the
  installed has**: torso Standing 139 -> 146, Hit 353 -> 358, Running/Bow +3, AttackMelee/Fidget/Cower +1..+2; boot L Death 12 -> 19,
  Bow/Standing/Conv4/Cower/Hit +1..+2; collar Cower 9 -> 12, Talk 8 -> 10, Running/Fidget +1; sleeve R +1..+5 (Fidget 84 -> 89); head
  (hair shell) Hit 4 -> 6. The probes (`work/probe/*.json`) hit the same installed faces in both GLBs (kept exactly); the extra pixels
  presumably come from changed geometry behind those faces (trousers, hands, not kept by set e; not probed further). Strictly "no worse" is not met; the rises are
  single-digit pixels at 3 mm/px on existing gaps.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,e75}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected and snapped, 32 points), the creature's
  `shrink_shadow_lods.py`, `carry_variants.py`, `fix_winding.py`: every LOD's lowest point in every clip within 0.3 cm of LOD0 (installed
  LOD3 floated up to +1.6 cm, Cower); 0 stretched faces at every LOD; heights LOD0-3 all 1.7938 m (installed LOD3 1.7921).

## Review
Viewer (installed and reduced e r75, both tiers, all 13 clips; `run_creature_review.py check`: 52 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm1_reduce_claude/review/viewer/
Sheets read (e75): `review/sheet_face_e75.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/sheet_face_diff_e75.png`,
`review/sheet_body_e75_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_e75_b_hands.png` (both hands),
`review/close_e75_a_1.png` (arms, jacket front/back, Running hem, boots). Read for d70 (same cut on the parts that changed): its face,
body, hands, `close_d70_{a,b}_{1,2}.png` (shoulders and hair from behind, sleeve, chest laces) and `close_d70_b_hair_profile.png`.
No visible difference found. Also built: `review/close_e75_{a,b}_2.png`, `close_e75_a_hands.png`, `close_e75_b_1.png` (not read).
Look at: the jacket front edge from 3/4 behind (Standing torso +7 px), the left boot top in Death, the hair shell's facets from behind.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm1_reduce_claude/before/mm9_peasantm1.glb REA_NODE=PeasantM1 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
$G -c "import numpy as np; g=np.load('work/glb_parts.npz'); np.save('work/keep_shirtfront.npy', g['part']==3)"
RIM=0.03 EXTRA=work/keep_shirtfront.npy $G scripts/make_sets_pm1.py d
$G scripts/extra_keeps_pm1.py      # needs work/probe/*.json (st_probe.py runs) and work/glb_sets_d.npz
RIM=0.03 EXTRA=work/keep_shirtfront.npy,work/keep_e.npy $G scripts/make_sets_pm1.py e
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=e MP_GROUPS=1:0.6,2:0.7,4:0.75,5:0.45,6:0.75 scripts/run_mp.sh e8 0.8,0.75
scripts/build_mp.sh mp_e8_r75 export/mm9_peasantm1_e75.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm1_e75.glb before/mm9_peasantm1.glb --json review/uv_audit_e75.json
$G scripts/exact_parts.py export/mm9_peasantm1_e75.glb e; scripts/gates.sh export/mm9_peasantm1_e75.glb e75
work/queue_st2.sh; REA_NODE=PeasantM1 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantm1_e75.glb e75
$G scripts/viewer_tiers.py export/mm9_peasantm1.glb red; $G scripts/make_viewer_manifest.py e75 inst_a=..=work/viewer_inst_th_a.glb red_a=.. inst_b=.. red_b=..
HEADUP=0,0.08,0.05 scripts/shots.sh red_a; scripts/close_shots.sh; scripts/hand_shots.sh; $G scripts/shot_sheets.py e75; $G scripts/face_diff_sheet.py e75
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm1.glb` (0), `tools/install_model.py export/mm9_peasantm1.glb
--world mm9 --name mm9_peasantm1.glb`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantm1_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_peasantm1_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_peasantm1.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates and viewer stills
only); LOD1-3 and shadow meshes by eye (numbers only); see-through at the gate's full step-3 density; the e75 close-ups listed above as not
read (d70's equivalents were read; e75 differs from d70 only by keeping more jacket, boot and forearm faces).
