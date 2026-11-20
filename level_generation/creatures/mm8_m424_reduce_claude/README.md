# MM8 male Dark Elf peasant (`m424`, Dark Elf Pesant Male A/B/C) reduction (2026-10-18)

User: "pick 5 more to do" (after the MM8 Dragon, Wyvern, Phoenix, Necromancer, Nightmare and Cyclops reductions).
Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons. No retexture,
no Meshy credits. Not installed; awaiting user review.

Source: the installed `assets_source/worlds/mm8/models/mm8_m424.glb`, identical to `mm8_m424_claude/export/`
(running-arm correction, 2026-10-16), copied to `work/mm8_m424_source_pre_reduce.glb` (rollback source). One
material (`M424_A`, three tier variants), merged head/body 2080x1024 atlas, node `M424`, 4 influences, rig with an
identity transform. The dagger (`mm8_m424_dagger.glb`, 102 triangles, own rigid attachment) is unchanged. The project
has no shared-gate config. Scripts start from `mm8_m492_reduce_claude/` (parent-transform fix, exact source weights);
`dump_faces.py` and `viewer_variants.py` come from the Necromancer, `dark_slivers.py` from the Cyclops.

## Regions (`make_groups.py`)

The mesh is mostly head and hands: head-set skin 3,121 faces, hair 1,107 (a separate piece), each hand 1,500, torso,
trousers, boots and sleeves 3,801. No coincident seam vertices (the lips are not split).

| label | faces | picked ratio |
|---|---:|---|
| 1 face and ear skin (head set, not hair) | 3,121 | 70 % |
| 2 hair | 1,107 | kept exactly |
| 3 left hand, 4 right hand (dagger grip) | 1,481 / 1,495 | 55 % each |
| 0 rest | 3,801 | remaining budget |

Kept exactly (`work/keep_e.npy`, 2,107 faces): eyes (129 + 127), teeth (23), the four sleeve attachment rings,
the white tunic trims with one ring of neighbours (`trim_faces.py`, 367: V-neck band, hem, shoulder-flap stripes),
one drift-lock round around non-hair dark slivers, and the hair.

## Ladder (limits for the 1.7 m height: p99 5.1 mm, max 25.5 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: right hand kept, left 50 %, hair 60 % | 70 % | 8,105 | 4.05 / 21.7 | 0.992 | 0.995 | pass |
| a | 65 % | 7,527 | 5.37 / 32.9 | 0.987 | 0.992 | fail: torso and legs starve |
| b: both hands 55 %, hair 60 % | 65 % | 7,525 | 4.04 / 21.7 | 0.992 | 0.995 | pass; shoulder-flap stripes and the V-neck trim notch |
| c = b + trims kept | 65 / 62 % | 7,525 / 7,177 | 4.21 / 18.1, 5.09 / 23.3 | 0.990 / 0.987 | 0.996 / 0.994 | pass; 62 % has a dark slash on the left thigh |
| d = c + one drift lock (dark slivers off the hair) | 65 % | 7,525 | 4.27 / 21.5 | 0.990 | 0.996 | pass; hair strand tips part and streak on the right side |
| e = d + hair kept | 66 % | 7,643 | 4.94 / 23.3 | 0.988 | 0.995 | pass; the thigh slash returns |
| **e** | **68 %** | **7,873** | 4.21 / 21.5 | 0.990 | 0.996 | **picked** |

- **Hands at 55 %** keep the fist and the dagger grip (Standing and the Fidget catch; `review/close/sheet_b_hands.png`),
  so the right hand needs no exact keep; keeping it starves the torso (config a).
- **Face at 70 %**: eyes, lips, nose and pointed ears match the source (`review/close/sheet_b_face.png`).
- **Trims**: the white bands are thin painted lines; under the collapse they notched at the V-neck top and the
  shoulder-flap stripes broke up. `trim_faces.py` finds them by base colour (bright, unsaturated, beside the tunic
  mask) and keeps them with one ring of neighbours (`review/close/sheet_c.png`).
- **Hair**: at 60 % the strand cards parted at the tips and showed light streaks on the right side
  (`review/glbclose/sheet_hair_ear_r.png`, from the GLBs); kept exactly it matches (`review/close/sheet_e.png`).
- **Dark slivers** (`dark_slivers.py`): at 68 %, 15 faces flagged; 11 are hair (the strand texture has dark gaps by
  design) and 4 at the cuffs and the back of the knee render the same as the source
  (`review/close/sheet_e_slivers.png`). Texture drift: 2 faces over 40.
- **Normals**: plain smooth. Rendered straight from the GLBs (`scripts/glb_close.py`, `review/glbclose/sheet.png`),
  the installed model shades smooth and the reduction matches it. `close_human.py` clears the welded
  `source.blend`'s custom normals before rendering the source column.

## Build

`export_cand.py` (Cand_68 of `work/ladder_e.blend`) -> `swap_lod0.py` -> `build_lods.py` (the creature's own LOD
settings: `build_actor_lods` defaults 0.5 / 0.18 / 0.06, 4 influences; protected points: LOD0 vertices within 1 cm of
the floor in any Death/Dead frame and the top 5 mm of the crown, 101 points) ->
`mm8_m424_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py`: `export/mm8_m424.glb`, 6.4 MB (installed
6.9 MB). check_winding: 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,585 | 5,791 | 2,084 | 693 |
| reduced | 7,873 | 3,936 | 1,416 | 472 |

`lod_check.py` (REA_NODE=M424): every LOD keeps the 1.700 m height and the width; the lowest point is 3 mm in Death
at every LOD and 2.3-4.4 mm in Running (installed: 3 / 8.3 mm, LOD3 Death 7.3 mm). No face stretches in any clip at any
LOD (installed LOD3 has one). Unlocked, LOD3 went 15 mm under the floor in Death and lost 1.3 cm at the crown. LOD3
fingertips are 1.6 cm shorter on the right hand.

## Retexture check

- **Texture set**: one 2080x1024 atlas (body 1K, head 1K side by side); base colour, metal-rough, normal and region
  mask are byte-identical to the installed ones, and the reduction keeps UVs.
- **Head vs body skin**: linear luminance median 0.099 face, 0.109 / 0.106 hands; no unify step needed.
- **Existing faults**: a small grey diamond and a grey band on the back hair. Clay renders show the diamond is a hair
  card sticking out of the source geometry and the band reads as a hair tie; a gap fill from nearby hair
  (`hair_fill.py`) changed nothing visible and was reverted.
- **Verdict**: no retexture for either half; no local texture fix applied. No credits spent.

## Review

Viewer `review/viewer/` (installed vs reduced for each tier; body only, the dagger is unchanged). Tiers are baked by
`viewer_variants.py` (three.js has no region ramps). `tools/run_creature_review.py ... check`: 42 clip switches, no
console errors.

## Status

Not installed. To install: `python3 tools/install_model.py
level_generation/creatures/mm8_m424_reduce_claude/export/mm8_m424.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_dark_elf_peasant ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_dark_elf_peasant_actor_models_keep_native_roles`: dagger bone and three reduced LODs, no triangle counts).
Rollback: install `work/mm8_m424_source_pre_reduce.glb` the same way.

Reproduce: `import_source.py` (REA_NODE=M424, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py` ->
`make_groups.py` -> `trim_faces.py work/keep_b.npy work/keep_c.npy` -> `REA_KEEP_FACES=work/keep_c.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.6,3:0.55,4:0.55 run_ladder.sh c 0.65` -> `dark_slivers.py r65`
(hair faces zeroed) -> `REA_LOCK_R=0.02 drift_lock.py work/keep_c.npy work/keep_d.npy r65` -> keep_e = keep_d + hair
-> `REA_KEEP_FACES=work/keep_e.npy REA_GROUP_RATIOS=1:0.7,3:0.55,4:0.55 run_ladder.sh e 0.68` -> build as above.


## Installed (2026-10-18)

User accepted the viewer ("ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py export/mm8_m424.glb --world mm8`; regression `mm8_dark_elf_peasant_actor_models_keep_native_roles` passes. Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m424_source_pre_reduce.glb` the same way.

## Gait rollout (2026-10-31, package h18)

New in-place locomotion clips appended to the installed source (every existing clip, mesh, skin and material
byte-identical): `Walk2` (Relax-Walk-Forward, 1.05 s, stride 1.2616: his 1.22 u/s wandering played `Walking` at x0.68). Arms, hands and props come from this model's own fitted clips. Built, gated and installed in
[../gait_rollout_20261031/h18/](../gait_rollout_20261031/h18/README.md); bindings for the coordinator in its
`bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h18/scripts/rebuild.sh m424`; rollback:
install `../gait_rollout_20261031/h18/work/mm8_m424_pre_gait.glb`. A far-LOD repair, head-bob, floor-fix or reduction
rerun on this model must re-graft these clips (copy the new source over the pre-gait copy and rebuild).
