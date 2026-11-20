# MM8 Dire Wolf (`mm8_wolf`, Dire Wolf A/B/C) reduction (2026-10-18)

User: "OK do those 5" (MM8 reduction batch: ratman, m436, m584, wolf, m540). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant (UVs kept, so the shared textures, three
material variants and region ramps stay valid). No Meshy credits. Scripts copied from
[mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md) (m492 coincident-vertex separation, exact source
weights, stretch check), with `glb_close.py` from [mm8_m492_reduce_claude](../mm8_m492_reduce_claude/README.md).

Source: installed `assets_source/worlds/mm8/models/mm8_wolf.glb`, identical (sha1) to `mm8_m512_claude/export/`;
the `assets_dev` copy is its cooked runtime (same clips and durations). Copied to
`work/mm8_wolf_source_pre_reduce.glb` (rollback source). One material `Wolf_A` (B/C are variants; the three tiers
share colouring and differ in size), mesh node `Wolf`, 24 bones, 4 influences.

## Ladder

Weld 12,911 -> 657 open edges (unchanged by every step; the fur shells are open sheets); 12 coincident vertices with
other weights, no split lip seam: no face stretches over 20x its rest area in any frame of any clip, in the source
or any candidate (`stretch_check.py`). 17 small pieces of up to 160 faces (teeth, eyes, nose, tail tufts; 1,260
faces) kept exactly (`REA_SMALL=160 small_pieces.py`). Limits scaled to the 1.035 m bound (p99 3.1 mm, max 15.5 mm).

| ladder | step | triangles | p99 / max mm | IoU min | SSIM | drift > 40 | |
|---|---|---:|---|---|---|---|---|
| uniform | 70 % | 9,939 | 1.81 / 13.95 | 0.994 | 0.995 | 2 faces | pass |
| **uniform** | **55 %** | **7,809** | 2.79 / 16.07 | 0.988 | 0.990 | 5 faces, 3.7 cm2 | **visual pick** (max) |
| uniform | 50 % | 7,099 | 3.31 / 15.86 | 0.987 | 0.988 | 4 faces | fail (p99, max) |
| uniform | 45 % | 6,389 | 3.88 / 16.81 | 0.984 | 0.985 | 7 faces | fail |
| head 80 % | 55 % | 7,809 | 4.09 / 15.55 | 0.982 | 0.984 | | fail |
| head 80 % | 50 % | 7,099 | 5.15 / 24.88 | 0.974 | 0.979 | | fail |

Head and jaw are a third of the mesh (4,934 faces with Head/Jaw weights); protecting them at 80 % pushed the cut
onto the hackle and elbow fur shells and doubled the error, so the teeth and eyes are kept as small pieces instead
and the rest is cut uniformly. The 55 % max (16 mm, Attack frame 6) is the jagged fur fringe at the left elbow, whose
tips round off slightly (`review/close/` armpit rows); the 70 % step already has a 14 mm point on the left thigh fold
in Walking. Teeth, eyes, nose, ears, hackle spikes, paw claws (four plus dewclaw), tail tufts, belly and corpse match.

Shading was judged only from GLB-direct renders (`glb_close.py`, the file's own normals): the welded
`work/source.blend` changes custom normals and shows wrinkles the installed model does not have, so the source
columns of `review/close/sheet_uni.png` look rougher than the real model. `review/glbclose/sheet_{tex,clay}.png`
(installed / reduced, 12 spots) shows no visible difference.

## Build

`export_cand.py` (Cand_55 of `work/ladder_uni.blend`, `REA_NODE=Wolf`) -> `swap_lod0.py` -> `build_lods.py` (the
installed ratios 0.5 / 0.25 / 0.125, 4 influences) -> `carry_variants.py`: `export/mm8_wolf.glb`, 8.27 MB
(installed 9.64 MB), 8 clips, 3 variants on all 8 colour/shadow meshes.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,201 | 7,100 | 3,550 | 1,767 |
| reduced | 7,809 | 3,904 | 1,947 | 964 |

`work/lod_check_{src,r55}.json`: every LOD keeps the source bounds (0.52 x 1.06 x 0.654 m; LOD3 tail tip and flank
within 5 mm), no stretched faces, floor as the source (Death dips 7-9 mm below zero in the source too, the rest stays
above 0). `review/lods/sheet.png` compares all LODs standing and at the bite impact; the new LOD3 (964) has thinner
hackles than the installed LOD3 (1,767) but keeps the silhouette, eyes and tail.

Viewer `review/viewer/` (installed vs reduced for each tier, ramps baked by `viewer_tiers.py` from the m512 project's
textures; native anchors from `mm8_m512_claude/native/`): `tools/run_creature_review.py --project
level_generation/creatures/mm8_wolf_reduce_claude check`, 48 clip switches, no console errors.

## Attack v2 (leaping bite)

User: "please re-do the attack animation, check original, he jumps much farther up in the wind-up to the air, then
bites like mid-jump-down before he falls down." The native attack (`mm8_m512_claude/native/attack_view_*_sheet.png`,
frames a-g) is a crouch, a rear-up on planted hind legs, a leap with the paws about 41-44 native px (0.35-0.37 m)
clear of the floor, a bite on the way down and a front-first landing with the rear and tail high. The v1 clip only
hopped about 6 cm.

`scripts/attack_v2.py` re-authors Attack on the production rig (`mm8_m512_claude/work/anim_v1.blend`, read only) with
the production posing helpers and floor rule; front and hind legs blend between planted IK and free FK on their own.
Same 1.125 s and impact 0.875 s, so `actors.yml` is unchanged. Keys follow the native frame times (a 0, b .16, c .32,
d .48, e .64, f .80, g .96 s): crouch, rise, rear up (hind feet planted, 1.6 cm), airborne from 0.54 s, peak 0.40 m
clearance at 0.67 s (hips +0.31 m), jaws wide at 0.80 s and closing at 0.875 s 13 cm above the floor, landing at
0.96 s, recovered at 1.125 s. `scripts/graft_attack.py` swaps the Attack channels of `export/mm8_wolf.glb` for the
Blender export (`work/attack_v2.glb`, joints matched by name, rest TRS asserted equal); the pre-graft file is
`work/mm8_wolf_r55_attack_v1.glb`.

Review round 2 (user: "frames 0-5 should not be in the air though, no? he is crouching waiting to leap there"): the
first crouch dropped the chest so far that the forelegs folded back under it with the paws off the floor. The crouch
and rise keys are now shallower with the front paws planted: all four paws stay on the floor through frame 6, the
front paws ease up 1-2 cm at frames 7-8 and the rear-up starts at frame 9 (`paw_tips_FL_FR_HL_HR` in
`work/attack_v2_report.json`; browser captures `review/shots/attack_v3_viewer.png`). Viewer without cached files:
`review/viewer_attack3/`.

Checks: `review/attack_v2/sheet.png` (side and front at the native times; v1 for comparison in `Attack_v1_*`),
`work/attack_v2_report.json` (clearance per frame), `work/lod_check_r55_attack3.json` (no stretched faces at any LOD;
lowest point -2.7 mm in Attack, Death already dips 9 mm), viewer rebuilt (`viewer_tiers.py`; the r100
models keep the installed v1 Attack for comparison), `run_creature_review.py ... check`: 48 switches, no errors.

## Status

Installed 2026-10-18 (user: "ok wolf ok") with `tools/install_model.py --world mm8` after `compact_glb.py` (drops the replaced Attack data; LOD check identical); `mm8_wolf_actor_models_keep_native_sizes_and_roles` passes. Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Commands used:
`python3 tools/install_model.py level_generation/creatures/mm8_wolf_reduce_claude/export/mm8_wolf.glb --world mm8`,
then `OPENYAMM_REGRESSION_FILTER=mm8_wolf_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_wolf_actor_models_keep_native_sizes_and_roles`) and add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_wolf_source_pre_reduce.glb` the same way.

Reproduce: `import_source.py` (REA_NODE=Wolf, REA_GLB=the rollback source) -> `dump_mesh.py` -> `REA_SMALL=160
small_pieces.py` -> `REA_HEIGHT_M=1.035 REA_KEEP_FACES=work/keep_small.npy run_ladder.sh uni 0.70,0.55,0.50,0.45`
-> `stretch_check.py`, `texture_drift.py`, `close_ladder.py`, `close_sheet.py`, `probe_max.py` -> build as above ->
`REA_NODE=Wolf lod_check.py`, `lod_views.py`, `glb_close.py`, `viewer_tiers.py`.

## Floor fix — 2026-10-21

`--ground-death Death Dead`: the landing went up to 9 mm under the floor (2.9 world units at tier C); the corpse is lowered 3 mm. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_wolf.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.

## Gait rollout (2026-10-31): Walk2, Run2 and Sprint

Gait rollout package q2 ([`../gait_rollout_20261031/q2/README.md`](../gait_rollout_20261031/q2/README.md)) added
three gaits for the game's speeds. Walking (0.34) and Running (0.77) had played ×1.5 wandering and ×2-3 chasing.
- Clips:
  - `Walk2`: a trot (front L and hind R at 0, as Walking), 0.45 s, stride 0.4545 m, duty 0.56.
  - `Run2`: a flying trot, 0.35 s, stride 0.7035 m, duty 0.38.
  - `Sprint`: a rotary gallop (hind R at 0) for MAW's chase, 0.4167 s, stride 1.275 m, duty 0.22.
- The wolf's walk carriage is kept: the body pitched 7° front-down and the tail lowered. The neck steadies the head
  (head bob 3.4 / 6.0 / 11.7 %, against Walking's 10.9 %).
- Grafted onto the installed `mm8_wolf.glb` (append only, after the 2026-10-21 floor fix; 0 inverted) and installed.
- Binding for Dire Wolf A-C:
  - `walking: Walk2`, `stride_length: 0.4545`;
  - `run: Run2`, `run_stride_length: 0.7035`;
  - `sprint: Sprint`, `sprint_stride_length: 1.275`.
- Result: Standard ×0.97-1.15 wandering and ×0.98-1.15 chasing; MAW chase Sprint ×0.93-1.20.
- Made by `../gait_rollout_20261031/q2/scripts/quad_gait.py wolf` from `../mm8_m512_claude/work/anim_v1.blend`
  (read only).
- Viewer revision `wolf-gait-1` (page copied from the MM7 rat's; tier GLBs by `scripts/viewer_tiers.py <export> gait`).
  The previous manifest is `manifest_reduce-1-attack-v3.json`. Shots `review/shots/{s,r,w}*.png`, playback
  `review/playback/{Walk2,Run2,Sprint}-*`.
- A later re-export, floor fix or LOD rerun must re-graft these clips.
