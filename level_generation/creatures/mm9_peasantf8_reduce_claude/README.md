# MM9 PeasantF8 (`mm9_peasantf8`, the elf townswoman) reduction: candidate c50 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk: the relaxed
keep set, face exact), ledger row 41 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf8` (owner
peasantf8-reduce-20261105); the creature's own `mm9:peasantf8` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantf8.glb` (sha256 72983df1fdc6, identical to `../mm9_peasantf8_claude/export/`), copied
to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantf8_claude/` was only read.

**Body:** PeasantF8 is its own body (the first female townsfolk body; F1/F5 copied its scripts, F3/F4 sit on F1, F6 on F5). No other
reduced female shares its mesh, so no keep set was carried over; the scripts are PeasantF1's reduction (F1 was built from F8's
scripts: same GLB layout, same skirt-lining construction) with an F8 keep set.

| | LOD0 | head prim (face/neck/eyes/teeth 3,204 + elf ears 588) | dress | hands | scarf | skirt | lining | legs | cuffs | band | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,406 | 3,792 | 1,798 | 1,470 | 948 | 1,398 | 1,586 | 638 | 518 | 258 | 6,140 | 2,209 | 735 |
| **c50 (`export/mm9_peasantf8.glb` = `export/mm9_peasantf8_c50.glb`, sha256 9ea79fcc52af)** | **9,900 (-20.2 %)** | 3,792 (exact) | 1,234 | 908 | 748 | 856 | 1,044 (856 + rim 188) | 542 | 518 (exact) | 258 (exact) | 4,890 | 1,760 | 649 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). The head primitive keeps every installed vertex and triangle, so face and ears render pixel-identical in both tiers
(`scripts/face_exact.py`: 3,792 of 3,792 head faces and 2,270 of 2,270 kept body faces present). Clips (11), skin, nodes, materials,
region ramps/mask, `KHR_materials_variants`, all 8 images: byte-identical (`same_clips.py`).

## Keep set (`scripts/make_sets_pf8.py`, set c: `MASKB=1 HEMBAND=0.02`)
Parts from the creature's last pre-GLB mesh (`../mm9_peasantf8_claude/work/uv_tex2.npz`, `scripts/glb_parts.py`, every face matched
at distance 0): 0 head, 1 scarf, 2 dress, 3 cuffs, 4 band, 5 skirt, 6 legs, 7 hands, 8 ears, 9 lining.
Exact: head + ears (whole head primitive), scarf edge within 8 mm of the face (254) and 12 mm of the ears (30), collar within 1 cm of
the head (174), sleeve ends within 12 mm of the cuffs (76), the cuffs (518, the MPFB hand stub sits inside), the waistband (258), the
forearm-weighted hand stub (66), soles (156), the lining hem rim (188), **the dress faces whose UV triangle spans two region-mask
classes** (bodice / sleeves / unmasked embroidery and trims, 354 more) and **the skirt's hem band** (196 skirt faces next to the rim,
with their lining twins). 6,062 faces (48.9 %) exact; the lining (1,398 twin faces) follows the skirt.
Groups: hands + fingers 0.6 (every finger, seam slides), scarf 0.7, skirt 0.55 (lining re-emitted from the cut skirt as its exact
reversed twin per lining UV island, 0 twin-key clashes), shoes 0.6 (guards stopped at 248 of 320), hidden calves 0.85, dress at the
ladder ratio 0.5.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantF1's copy)
Texture guard over each tier's baked body colour, each tier's head image and the region mask (`scripts/tex_extract.py`); chart guard
(`MP_CHART=1`, sampled at 12); texture weight 4 (`MP_W5`); seam slides on the hands; scored over every clip at 10 Hz plus a
position+UV rest quadric.

## Ladders (limits for 1.762 m: p99 <= 5.29 mm, max <= 26.4 mm, IoU >= .98, SSIM >= .93)
| ladder | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| a | set a, texture guard 100/45 | r50 / r40 | 9,512 / 9,370 | 3.32 / 16.7 (Conv1), 5.84 / 35.3 (Hit) | .996 / .995 | r50 pass, built a50; **rejected**: dark bodice wedges pulled onto the sleeve at both armholes (`review/crop_chest_c0_a50.png`) and the kept hem rim's lining corners 6.6 mm outside the coarser skirt at rest, 35 mm in Death, 29 mm in Dead (`lining_gate.py`, `scripts/lining_probe.py`); r40 fail |
| b | a + mask-border dress faces kept, texture guard 70/30 | r50 | 9,724 | (not laddered: superseded by c before its ladder ran) | | `work/mp_b_r50.npz` |
| **c** | **b + skirt hem band kept** | **r50** | **9,900** | **4.62 / 26.2 (Conv1:45)** | **.995 / .995** | **PASS, picked**: armhole wedges gone, lining back to the installed numbers |

UV audit (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_c50.json`): **0 LOD0 faces leave the charts** in both primitives.
LOD1 (tool-built): body 189 / head 28 escaping (installed LOD1: 151 / 29).

## Gates, installed -> c50 (`review/gates_before/`, `review/gates_c50/`; F8's own gate scripts via `scripts/gates.sh`)
- Collapse face-frames lower in every clip but Standing (equal 1,910): Walking 619 -> 488, Fidget 3,462 -> 3,417, Conv1 2,611 -> 2,421,
  Hit 4,663 -> 4,501, Death 1,939 -> 1,777, Cower 2,843 -> 2,519; worst-frame regions equal or lower except single-face rises (Fidget
  armpit R 21 -> 22, Cower armpit R 20 -> 21, Hit armpit L 4 -> 5; Hit armpit R 41 -> 34).
- Robe (legs through the skirt): 0 in every clip, both. Arm/hand (`--outer-only --exact`): 0 frames > 1 cm in every clip, both hands;
  hand depth 0.2 cm both; finger-stretch maxima identical (Fidget R 2.36), minima up 0.02-0.17.
- Skirt lining (`scripts/lining_gate.py`): every clip's largest outward distance identical to the installed model (Death/Dead 7.93 mm)
  except Walking 4.84 -> 7.68 and Running 5.08 -> 7.88 mm: one hem-corner rim vertex (rest -0.237, -0.847, -0.181) that is already
  2.6 mm outside the skirt at rest in the installed model and is its worst vertex there too.
- Jitter vs the creature's `ref_half.glb`: 2 fails both (Death shoulder skin, the installed model's own). Detached parts: the same 2
  (the free legs, by design). Flat shading 0.00. Winding 0. Bone lengths 14, 0 stretching. Texture quality unchanged (body stretch
  p90 1.08 -> 1.09).
- See-through (`scripts/see_through.sh`, every clip, 16 views; `scripts/see_summary.py`, hole max px level / 20 deg): torso 1322/26 ->
  1148/26, sleeve L 1875/6 -> 1831/12, head 361 = 361, boot R 4 -> 3; rises: collar 936 -> 1057 (Death from the feet at ground level,
  same frame as the installed worst: up the open skirt), sleeve R 9/8 -> 19/19 (Hit frame 36, a hairline sliver at the back of the R
  shoulder silhouette; `review/close_hit_shoulder_c50_b.png` shows no opening), boot L 8 -> 13 (Running 12).
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/lod_summary.py`), built by `scripts/build_lods.py` (tool defaults
  0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected and snapped, one coincident point with two weight sets dropped,
  PeasantF6's fix): height 1.761/1.760/1.756/1.753 m; every clip's lowest point at LOD1-3 within 0.5 cm of LOD0 (installed LOD3
  floated up to 0.23 cm); stretched faces LOD1 5 -> 7, LOD2 7 -> 6, LOD3 5 = 5.

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf8_reduce_claude/review/viewer/ (revision r2-c50-20261105)
Sheets read (full size): `review/sheet_face_c50.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers),
`review/sheet_face_diff_c50.png` (face and ears black; only scarf shading and the bodice in the party view differ),
`review/sheet_body_c50_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_c50_{a,b}_hands.png`,
`review/close_c50_{a,b}_1.png` (arms, apron front, skirt back, Running), `review/close_c50_b_2.png` (hem/feet, Talk, shoulders and scarf
from behind, Hit, scarf top), `review/crop_chest_c0_c50.png` (armholes and embroidery, both tiers), `review/crop_apron_c50.png` (apron
edge), `review/close_hit_shoulder_c50_b.png`; rejected a50: `review/crop_chest_c0_a50.png`, `review/crop_scarf_f2_a50_b.png`.
Look at: the fingertips (hands 0.6: very slightly more angular tips), bodice shading at the sides of the chest (same paint), the
skirt hem in Walking/Running (one hem-corner lining vertex 3 mm further out).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantf8_reduce_claude/before/mm9_peasantf8.glb REA_NODE=PeasantF8 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
MASKB=1 HEMBAND=0.02 $G scripts/make_sets_pf8.py c
MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.6,2:0.7,3:0.55,4:0.6,7:0.85 MP_TEX_MAX=70 MP_TEX_MEAN=30 REA_HEIGHT_M=1.762 scripts/run_mp.sh c 0.5
scripts/build_mp.sh mp_c_r50 export/mm9_peasantf8_c50.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantf8_c50.glb before/mm9_peasantf8.glb --json review/uv_audit_c50.json
scripts/gates.sh export/mm9_peasantf8_c50.glb c50; $G scripts/lining_gate.py export/mm9_peasantf8_c50.glb review/gates_c50/lining.json
scripts/see_through.sh export/mm9_peasantf8_c50.glb c50; REA_NODE=PeasantF8 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantf8_c50.glb c50
$G scripts/face_exact.py export/mm9_peasantf8_c50.glb c
$G scripts/viewer_tiers.py export/mm9_peasantf8_c50.glb redc50   # installed: viewer_tiers.py before/mm9_peasantf8.glb inst
$G scripts/make_viewer_manifest.py <rev> inst_b=..=work/viewer_inst_th_b.glb red_b=..=work/viewer_redc50_th_b.glb inst_a=.. red_a=..
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py c50; $G scripts/face_diff_sheet.py c50
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantf8.glb` (0), `tools/install_model.py export/mm9_peasantf8.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantf8_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantf8_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantf8.glb`.

Other builds in `export/`: a50 (rejected, kept for reference). Shots of a50 in `review/shots_a50/`, `review/shots_close_a50/`.

## Not checked
In game (not installed; binding regression and floor audit after install are the orchestrator's); motion at normal speed by eye
(frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); tier A close-ups of hem/shoulders (tier B read,
geometry identical).
