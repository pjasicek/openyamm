# MM8 Minotaur Peasant (`m488`, Minotaur A/B/C) reduction (2026-10-19)

User: "Pick these for next reduction batch" (MM8 batch 2 of openyamm-f6: m556, m632, m488, m608, m496). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the installed
textures, the three palette variants (`KHR_materials_variants`: green, purple and red wraps) and the region ramps stay
valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m488.glb`, byte-identical to
`../mm8_m488_claude/export/mm8_m488.glb` (accepted 2026-10-18), copied to `work/mm8_m488_source_pre_reduce.glb`
(rollback source). One material per tier (`Minotaur_A/B/C`, merged 2080x1024 body/head atlas), node `Minotaur`
(extras `m488_wrap_margin_applied` kept), 108 bones (48 wrap skirt controls), 4 influences, 8 clips. No held prop
and no attachment binding. No `gates.json` in the creature project, so no shared gate run.
Scripts start from `../mm8_m412_reduce_claude/scripts/` (its `reduce_ladder.py` has the parent-before-transform fix
of the m624 copy).

## Keep sets and regions (`make_groups.py`, `eye_keep.py`)

Weld 5,710 -> 201 open edges; no coincident vertices with other weights (no split seam). Five pieces: body 7,797
(head included), wrap skirt 799, rope belt 449, two wrist bands 220 each.

| label | faces | ratio |
|---|---:|---|
| 1 head (`B_Head` dominant: muzzle, nostrils, ears, horns, neck hump; 37 % of the mesh) | 3,488 | 50 % |
| 2 palms (`B_*_Hand`) | 869 | 50 % |
| 3 fingers (`B_*_Finger*`) | 1,531 | 70 % |
| 4 wrap skirt | 799 | 70 % |
| 0 rest: torso, arms, legs, hooves (already lean: ~1,800 faces) | 1,801 | remaining budget |

Kept exactly (`work/keep_lock.npy`, 1,654 faces):
- the rope belt (449; painted twist lines) and the wrist bands (small pieces up to 220 faces, 440);
- the soles (faces below 6 cm, 108);
- **both eye zones** (`eye_keep.py`, 4.5 cm around each iris, 333 faces). The eyes are part of the head surface.
  The iris centre is found from the texture: head faces sampling the orange iris (hue 0.05-0.13, saturation > 0.55)
  in front of the face (y < -0.12 m, z 1.85-1.98 m), because the horns and muzzle share the hue. Centres
  (±0.079, -0.161, 1.91). Without them the head cut streaked the iris and left a white shard in the black eye patch
  (`review/sheet_head_ab.png`, a75 / b70 / b66);
- one drift-lock round (324 faces, from ladder c at 68 %).

For openyamm-f9's m484 Minotaur (separate model, possibly a related head): the same iris-texture eye search and a
4.5 cm zone, the head at 50 % on its own and the horn/ear tips protected in the LODs were enough here.

## Ladder (limits for the 2.11 m height: p99 6.33 mm, max 31.65 mm)

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 9,485 | | | |
| a: head 60, palms 60, fingers 75, wrap 75 | 75 % | 7,111 | 3.20 / 30.0 | 0.998 | pass; eye shape soft |
| a | 70 % | 6,637 | 6.26 / 30.2 | 0.992 | pass (rest at 71 % doubles p99) |
| a | 65 % | 6,163 | 9.87 / 45.3 | 0.982 | fail |
| b: head 50, palms 50, fingers 70, wrap 70 | 70 % | 6,605 | 3.95 / 31.2 | 0.997 | pass; eye streaks, eye-patch shard |
| b | 66 % | 6,259 | 5.35 / 31.2 | 0.993 | pass; same eye fault |
| c = b + eye zones | 70 % | 6,637 | 4.45 / 31.2 | 0.995 | pass |
| c | 68 % | 6,447 | 5.34 / 31.2 | 0.993 | pass; drift 19 faces / 100 cm² (leg spots) |
| d = c, wrap 85 | 68 % | 6,447 | 5.71 / 30.2 | 0.992 | pass, worse p99 (rest starved) |
| cL = c + drift lock | 68 % | 6,449 | 6.30 / 31.2 | 0.992 | pass, at the limit |
| **cL** | **70 %** | **6,639** | 5.15 / 31.2 | 0.994 | **pick**; drift 10 faces / 13 cm² |

The max (31.2 mm, `Running:6`) is one wrap hem vertex at the back right (`Wrap_9_09`), the same in every
step with the wrap cut; it stays under the limit. Close-ups from the GLBs themselves (`glb_close.py`, each file's own
normals): `review/sheet_head_ab.png`, `review/sheet_c_head.png`, `review/sheet_c_body.png`, `review/sheet_cL.png`
(installed / candidates: face, eyes, muzzle, horns from above, ears, hands, fist, torso, wrap, back, legs front and back,
hooves, Running knee, raised arm). At the pick nothing visible changes. Normals are plain smooth (no
`REA_NORMALS=transfer`).

**Covered skin (batch-1 lesson, m412 temple hole):** `hidden_skin.py` renders the body with every piece but the body
removed (wrap, belt, bands) on magenta, at the waist (front, back, side, below, Running), the wrists (standing and
Attack) and the head (top and under), for the installed model and every reduced LOD (`review/hidden/sheet_lod0.png`,
`sheet_lods.png`). The hidden pelvis, thighs and wrists are closed in all of them; nothing to repair.

## Build

`export_cand.py` (cL, Cand_70) -> `swap_lod0.py` -> `build_lods.py` (the creature's ratios 0.5 / 0.25 / 0.125,
4 influences; horn and ear tips protected, `work/horn_tips.npy`) -> `../mm8_m488_claude/scripts/shrink_shadow_lods.py`
(shadow LOD1-3 tucked inside the surface, as installed) -> `carry_variants.py` (variants on all 7 LOD and shadow
primitives) -> `check_winding.py` (0 inverted closed parts): `work/mm8_m488_r70_pre_walk.glb` (then the walk fix below: `export/mm8_m488.glb`), 6.7 MB (installed 7.2 MB), 8 clips.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,486 | 4,740 | 2,369 | 1,183 |
| reduced | 6,639 | 3,319 | 1,659 | 828 |

`work/lod_check_{src,r70}.json`: every LOD keeps the 2.10 m height (LOD0 2.099: the top horn vertex moved 1 mm); no
face stretches over 20x in any frame of any clip. Lowest points (Death): 14.0 / 12.0 / 12.6 / 12.6 mm below the floor
against the installed 10.4 / 10.6 / 12.2 / 11.1 mm (the creature's floor tolerance is 2 cm). `review/sheet_lods_close.png`:
installed LOD0 and LOD3 against reduced LOD1-3. Reduced LOD2-3 show a small white fleck on top of the head, the white
blaze sliding over a UV seam in Blender's LOD decimation (clay has no hole, `review/lod_headtop_check.png`); the
installed LOD3 has the same kind of breakup on the face.

Viewer: `review/viewer/` (installed vs 70 %, three tiers); `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m488_reduce_claude check`: 48 switches, no console errors. Tier bakes checked
(`review/sheet_tiers.png`).

## Source-animation scan (`clip_scan.py`, `series.py`; viewer frame = time x 48)

Findings in the installed clips (the reduction itself changes no clip):
- **Walking: a hitch twice per cycle**, fixed below. The pelvis (and head) rises, dips and rises again: frames 16-18
  (111.8 -> 110.2 -> 109.3 cm) and frames 38-40 (109.7 -> 109.2 -> 107.1 cm, a 2.1 cm drop in one frame against a
  median step of 0.9 cm). Smaller than the m412 jump (3.9 cm) but the same kind.
- Attack: no dead start. A slow 0.7 s wind-up (hands 0.3 m/s from frame 1), the strike from frame 34, the left
  punch peaks at frame 49 (the 1.0 s impact). The pelvis does not translate in Attack. Hands stay clear of the body
  (`review/sheet_attack.png`, frames 50-62).
- Hit: a fast recoil (4.5 cm head step at frame 3 of a 0.5 s clip), intended. Death: a large fall (13.9 cm/frame at
  frame 40) after the creature's own neck smoothing; no single-frame pops. Standing and Fidget are calm.

## Walk hitch fix (round 2, 2026-10-19)

Requested by the coordinator before review (the user accepted the same fix on the m412 Pirate). `scripts/
smooth_walk_bob.py` is the m412 script unchanged (same bone names: `B_Pelvis`, `B_{L,R}_{Thigh,Calf,Foot}`), run on the
staged 70 % export (`work/mm8_m488_r70_pre_walk.glb` -> `export/mm8_m488.glb`) with **sigma 2**: the m488 Walking is keyed
at 30 Hz (31 keys), not 120 Hz like the pirate, so the pirate's sigma 7-8 (0.06 s there) spans 0.23 s here and
flattened the bob to 1 cm (`work/walk_s6.glb`, `walk_s8.glb`, rejected). The pelvis curve is smoothed periodically and
lowered locally where both ankles would be out of reach; both legs are re-solved in their original knee planes, so every
ankle keeps its original path (0.000 mm) and every foot its original rotation. Only the pelvis translation and the
thigh, calf and foot rotations of Walking change; every other clip and channel is byte-identical.

| | head / pelvis range | largest 48 fps step | extrema per cycle | lowest sole |
|---|---|---|---|---|
| installed | 9.7 cm | 2.09 cm (frame 40) | 7 (hitches at 16-18, 38-40) | -7.5 mm |
| sigma 1.5 | 7.1 cm | 0.97 cm | 3 | |
| **sigma 2 (staged)** | **6.5 cm** | **0.90 cm** | **3: two even bobs** | **-7.8 mm** |
| sigma 2.5 | 5.8 cm | 0.78 cm | 3 | |

Plot: `review/walk_bob_plot.png` (head and pelvis per viewer frame, grey installed, blue staged; lower panel: feet
unchanged). Filmstrip: `review/walk/filmstrip_f12_22.png` (side view, frames 12-22, installed above, staged below, red
line at frame 12's head height). Front and back at frames 22-40 (`review/walk/poke_check.png`): the legs stay under the
wrap. `wrap_poke.py` (thigh/pelvis vertices below 1.0 m outside the wrap surface) counts 6-10 per frame installed and
4-28 staged, the extra ones on the inner thighs under the skirt, not visible from any side.
Checks on the new export: winding 0 inverted closed parts; `work/lod_check_r70w.json` unchanged except Walking's lowest
point (-7.8 / -7.5 / -9.5 / -9.5 mm per LOD, installed -7.5 / -6.9 / -9.2 / -9.2); no stretched faces; viewer GLBs rebuilt
(manifest `reduce-2`, sha256 and `?v=` updated), viewer check 48 switches, no console errors.

**Re-exports:** the creature's build project (`../mm8_m488_claude/`, `scripts/build_runtime.sh`) still has the old
Walking. A re-export from it brings the hitch back unless `smooth_walk_bob.py <in.glb> <out.glb> 2` is run on the
export again (and the reduction re-applied).

## Status

Round 2 (70 % + walk fix) installed 2026-10-19 after user review ("mino pesant ok") with `tools/install_model.py --world mm8`; actor regression `mm8_minotaur_peasant_actor_models_keep_native_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install (from the repository root):
`python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m488_reduce_claude/export/mm8_m488.glb`,
then `OPENYAMM_REGRESSION_FILTER=mm8_minotaur_peasant_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_minotaur_peasant_actor_models_keep_native_roles`)
and add the ledger row.
Rollback: `python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m488_reduce_claude/work/mm8_m488_source_pre_reduce.glb`.

Reproduce: `REA_GLB=<rollback source> REA_NODE=Minotaur blender -b -P scripts/import_source.py` -> `dump_mesh.py`,
`dump_faces.py`, `dump_groups.py` -> `make_groups.py` -> `REA_EYE_R=0.045 eye_keep.py work/keep_base.npy
work/keep_eye.npy` -> `REA_HEIGHT_M=2.11 REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.5,2:0.5,3:0.7,4:0.7
REA_KEEP_FACES=work/keep_eye.npy run_ladder.sh c 0.70,0.68` -> `texture_drift.py r68` -> `drift_lock.py
work/keep_eye.npy work/keep_lock.npy r68` -> the same ladder with `work/keep_lock.npy` (`cL`) -> `quick_glb.sh`,
`glb_close.py`, `hidden_skin.py` -> build as above -> `lod_check.py` (REA_NODE=Minotaur), `lod_glbs.py`,
`viewer_variants.py`, `viewer_manifest.py`; then `smooth_walk_bob.py work/mm8_m488_r70_pre_walk.glb
export/mm8_m488.glb 2`, `walk_heights.py`, `plot_bob.py`, `walk_filmstrip.py`, `wrap_poke.py`, `lod_check.py` and the viewer again.

## Gait rollout (2026-10-31)

New locomotion clips: `Jog` (humanoid set Armed-Run-Forward, 0.74 s, 3.5602; replaces `Running`) and `Sprint`
(Unarmed-Sprint, 0.60 s, 4.9617); the 48-control wrap cage is re-fitted on each new clip with the project's
thigh-following target and skin projection (`h20/scripts/wrap_solve.py`, after
`../mm8_m488_claude/scripts/wrap_motion.py` and `wrap_cage.py`). Package [h20](../gait_rollout_20261031/h20/README.md)
appended them to the installed source (`assets_source/worlds/mm8/models/mm8_m488.glb`; existing clips, meshes, skins and
materials byte-identical; pre-gait copy `../gait_rollout_20261031/h20/work/mm8_m488_pre_gait.glb`) and installed it; the
bindings are in `../gait_rollout_20261031/h20/bindings.yml` for the rollout coordinator. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h20/scripts/rebuild.sh m488`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).
