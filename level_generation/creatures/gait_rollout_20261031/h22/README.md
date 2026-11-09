# Gait rollout package h22: MM8 Crystal Walker, Plane Guardian (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the two installed MM8 sources
(`assets_source/worlds/mm8/models/`; pre-gait copies `work/mm8_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending. Both are **installed**
(`tools/install_model.py --world mm8`, `work/exports.sha256` = the installed sources); `actors.yml` is not edited here:
[bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Crystal Walker A-C (`mm8_m596`, own 20-bone rig, no toe joints) | Sprint: procedural, the project's own gait author, 0.5625 s, 3.6977, 6.57 |
| Plane Guardian A-C, Wimpy Plane Guardian A-C (`mm8_m592`, B_* rig, long three-toed feet) | Walk2: its own `Walking` retimed and lengthened, 0.70 s, 1.0813, 1.54 · Jog: its own `Running` retimed, 0.62 s, 1.9098, 3.08 · Sprint: humanoid set Unarmed-Sprint, 0.52 s, 3.2502, 6.25 |

Strides are `gait_gate.py`'s trusted measurements (vertices and feet agree). No longer bound for locomotion but kept:
the Guardian's `Walking` and `Running`.

## Why these clips

- **Crystal Walker**: only MAW's tier A chase (8.65 u/s) failed, `Run2` at x1.83. Gate target for a sprint 5.77-7.62.
- **Plane Guardian**: the six descriptors span 1.29-4.29 u/s in Standard (the Chaos, "Wimpy", tiers flee at 2x and
  wander at 2.15) and 5.15-8.58 in MAW's chase. With three clips the only allocation that fits every tier is a walk
  for 1.29 and 2.15 (authored 1.43-1.72), a run for 2.58 and 4.29 (2.86-3.43) and a sprint for 5.15 and 8.58
  (5.72-6.87). The installed `Walking` (1.17) cannot cover the Chaos wander, the installed `Running` (2.24) played the
  Chaos chase at x1.92 and MAW's at the 2x cap. Hip 0.82 m: the chase at 2.6-4.3 u/s is a run pace (Froude 0.8-2.3),
  so no walk-as-run question arises.

## Gate window sections (`review/<m>_gait_gate.txt`, both PASSED, floor ok on every descriptor)

```
Crystal Walker  standard A wander Walk2 x1.19  chase Run2 x1.17 | maw A chase Sprint x1.32
                standard B wander Walk2 x0.91  chase Run2 x0.90 | maw B chase Sprint x1.01
                standard C wander Walk2 x0.87  chase Run2 x0.86 | maw C chase Run2 x1.21
Plane Guardian  standard A-C        wander Walk2 x0.83  chase Jog x0.84 | maw A-C chase Sprint x0.82
                standard Wimpy A-C  wander Walk2 x1.39  chase Jog x1.39 | maw Wimpy A-C chase Sprint x1.37
```

MAW's wander rows (hostile speed, not judged): Crystal Walker A Run2 x0.92, B Walk2 x1.43, C Walk2 x1.23; Plane
Guardian A-C **Walk2 x1.67** (the engine's walk preference while not hurrying; Jog would play it at x0.84, the
coordinator's open engine question), Wimpy A-C Jog x1.39.

## Method

**Crystal Walker** (`scripts/walker_sprint.py`): the walker's accepted `Walk2`/`Run2` were keyed procedurally in
Blender by `../../mm8_m596_v2_claude/scripts/anim_gait2.py` (planted flat soles by two-bone IK, pelvis drop, lean,
arm pump). Its rig has no toe joints and an angular crystal body, so the library composer does not fit; the sprint is
a copy of that script with one gait on the same clip master (`work/anim_gait2.blend`, read only): 27 keys at 48 fps
(0.5625 s, a closed loop), authored 3.72 m per loop, duty 0.22, lowest at mid-stance (-19 cm) and highest in flight
(-9 cm), trunk lean 8/6/7 deg (hips/waist/chest) with the head pulled up, heel lift 0.40, toe pitch 30, arms 34 deg
with elbows 45-60 deg. Appended with the project's unchanged `add_clips.py` (rest transforms compared first). It strikes
with the left foot in front at phase 0 like `Walk2` and `Run2`.

**Plane Guardian** (`scripts/compose_gait.py`, jobs in `jobs/`): a copy of `../h13/scripts/compose_gait.py` with three
additions for this body, whose long three-toed feet put its ankles 0.45 m behind its hips and whose knees point about
56 deg out (bow-legged) in `Standing`, `Walking` and `Running`:

- `source_stride`: the planted-sole stride of a source loop whose ankle does not travel with the ground while low
  (the Guardian's raised heel rolls over the toes; the composer read its `Running` as 0.85 m a loop, not 1.87).
- `ankle_z`: the ankle targets' mean fore-aft place behind the hips ("base" or metres), instead of a human source's
  under-the-hip place, which drove the knees up in front of the belly (thigh flexion to 70-90 deg).
- `knee_out_deg`: the source's knee direction turned outward about the vertical (bow-legged knees).

Library human loops on this body (first tries in `review/iter/m592_v1_*`, `_v3_*`) gave a crouching, high-kneed
run, so the walk and jog take the legs from the Guardian's own accepted clips (`scripts/glb_source.py`, from h03):
- **Walk2**: `Walking` at 0.70 s (0.80) and 1.17x its stride, ankles centred 0.38 m behind the hips (the rear reach is
  at the leg's limit; centred at the walk's 0.45 the pelvis fell 33 cm), `bob` 1.6.
- **Jog**: `Running` at 0.62 s (0.83), stride x1.04, `lock_stance` off (on: the long contacts sank the hips 22 cm and
  flexed the thighs to 83 deg), `reach` 1.0, trunk weights 0.6-0.2 (the full weights left `uneven` 0.47), and the right
  arm raised 10 deg around phase 0.04 (`arm_raise_deg` window 0.25): the claws dipped 2.9 cm under the floor there.
- **Sprint**: the Guardian's `Running` has no flight phase and cannot stretch to 3.25 m (the hips collapsed), so the
  humanoid set's Unarmed-Sprint with `ankle_z` -0.30, `knee_out_deg` 30, `swing_height` 0.75, `bob` 0.25,
  `lock_stance` on: a low bounding sprint with the legs tucked in flight.
All three: `stance_foot: Standing` with 5 deg toe-out (the feet turned 33 deg in from the accepted 38), arms, hands,
claws and jaw from the base clip (`Walking` / `Running`), `even_bob`, `symmetric_drop`, `align: Walking`.

## Phase

Crystal Walker: Sprint left foot forward-most at 0.96 (Walk2 0.00, Run2 0.00). Plane Guardian: the installed
`Walking` and `Running` are half a loop apart (left foot forward-most 0.75 / 0.28); every new clip follows the walk
(Walk2 0.75, Jog 0.76, Sprint 0.76).

## Checks (`review/`)

- `check_winding.py` 0 inverted closed parts on both; `prefix_check.py` ok on both.
- Foot heading, planted L / R (toe-out from +Z):
  - Crystal Walker (mesh, `foot_mesh_heading_probe.py`; no toe joints): Sprint +20.1 / +9.2 against Walk2
    +20.5 / +9.2 and Run2 +20.2 / +9.2 and Standing +20.2 / +9.1 (the prism feet keep the rest heading in every clip;
    the mesh axis of the faceted prism is not a toe line).
  - Plane Guardian (joints): Walk2 +5.0 / +5.0 (swing +1.6..+4.9), Jog +5.0 / +5.0 (+3.0..+4.9), Sprint +5.1 / +5.0
    (-6.3..+6.4); mesh +1.7..+2.5 / +4.3..+5.0. Accepted Walking/Running +38 / +38 (mesh +35..+39).
- Head bob (`bob_probe.py`, `uneven`): Crystal Walker Sprint 6.2 % (0.00; Walk2 4.9, Run2 5.4). Plane Guardian Walk2
  3.2 % (0.02), Jog 6.0 % (0.24), Sprint 6.4 % (0.03); Walking 2.1, Running 7.5 (0.17).
- Arm and hand gate (`contact_probe.py`, 60 Hz): Plane Guardian 0 % in every clip (claws included). Crystal Walker
  left arm 24 % / 24 mm against Walk2 and Run2's 29 % / 31-35 mm (the skin fault below), right 0 %.
- Arm skin stretch p99 / max: Plane Guardian equal to its accepted clips (Sprint L 1.19 / 1.64, Running 1.19 / 1.65).
  Crystal Walker L 4.17 / 15.5 against Run2 3.57 / 11.1 (the skin fault below; R 1.71 / 3.01 against 1.42 / 2.47).
- Lowest skin: Walker Sprint -0.03 cm; Guardian Walk2 +0.03, Jog -0.64 (a claw tip), Sprint +0.05 cm.
- Planted stride per side: Walker Sprint 3.697 / 3.684; Guardian Walk2 1.089 / 1.020 (its `Walking` 0.945 / 1.225),
  Jog 1.923 / 2.029 (`Running` 1.860 / 1.955), Sprint 3.251 / 3.249.
- Playback (`tools/run_creature_review.py check` and `playback`: no console errors, every clip switch, normal and half
  speed; looked at): viewers in `../../mm8_<m>_gait_h22_claude/review/` (the wrapper needs a direct child of
  `creatures/`), sheets `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/` (`m592_final_*`,
  `m596_v1_Sprint`).
- Headless actor regressions on the installed GLBs with the current (unapplied) bindings, all PASS
  (`scripts/regressions.sh`, `review/regression_*.log`): `mm8_plane_guardian_actor_models_keep_tiers_scale_and_claw_roles`,
  `mm8_crystal_walker_actor_models_keep_native_tiers_and_skinning`, `mm6_mm7_mm8_actor_models_build_every_binding`.
  Both model cases look clips up by name (`findClip`) with fixed durations and no clip count; the kept clips are
  unchanged, so the new clips and bindings do not break them.

## Doubtful / left open

- **Crystal Walker skin fault (pre-existing)**: 159 LOD0 vertices mix arm and leg weights; claw-tip vertices hanging
  by the knee (for example 2311 / 4465: `LeftHand` 0.71 + `LeftShin` 0.29 and the reverse) stretch into a thin strand
  from the forward claw to the rear shin when the arm and leg swing apart: +21 cm in the accepted Walk2, +30 cm in
  Run2, +43 cm in the Sprint (`review/iter/m596_big_Sprint.png`, `m596_big_Run2.png`). It is visible close up. A fix
  is a weight edit in `../../mm8_m596_v2_claude/` (no leg weight on claw vertices); meshes are not changed here.
- **Plane Guardian crotch**: the inner-thigh skin stretches more than in the accepted clips (`crotch_stretch_probe.py`,
  edge ratio p99 Walking 7.2, Running 9.4; Walk2 11.3, Jog 12.2, Sprint 20.0); in the sprint's long strides a light
  grey web shows between the thighs from the front (`review/iter/m592_big_front.png`; the accepted Running shows a
  smaller one). A weight or mesh fix belongs in the Guardian project.
- Plane Guardian feet: the new clips plant at 5 deg toe-out while `Standing` (and the unbound `Walking`/`Running`) keep
  38 deg; the heading changes at idle/locomotion switches.
- Plane Guardian Walk2 is brisk (0.70 s loop, 171 steps a minute) and its strides per side differ 7 % (from its own
  `Walking`, which differs 26 %); the Jog is a quickened `Running` (0.62 s against 0.83 s).
- Plane Guardian under MAW wanders on Walk2 at x1.67 (not judged; the engine's walk preference).
- Not run: in-game captures (bindings not applied yet). After `apply_bindings.py`, rerun the three regressions above.
- A far-LOD repair, head-bob or reduction rerun on either model must re-graft these clips: copy the new source over
  `work/mm8_<m>_pre_gait.glb` and run `scripts/rebuild.sh`.

## Shared tools

No problem found in `claude_shared/` tools. Notes: `foot_heading_probe.py` and `foot_mesh_heading_probe.py` need toe
joints (the h22 copy of the mesh probe accepts their absence, and `gaitlib.alias_nodes` reads the walker's own joint
names); the composer's source-stride measurement (low-ankle speed) misreads digitigrade-style feet (`source_stride`).

## Rebuild

`scripts/rebuild.sh [m596] [m592]` composes both exports from `work/mm8_<m>_pre_gait.glb` (the walker through Blender
and the project's `add_clips.py`), then runs `gait_gate.py` and `check_winding.py`; it reproduces
`work/exports.sha256` byte for byte. `work/sources/RPG_Character_Unarmed_Sprint.npz` is library-derived (copied from
`../h13/work/sources/`; never commit); the Guardian's own `m592_*.npz` are regenerated by the script. Probes:
`HEADING_PROBE=foot_mesh_heading_probe.py scripts/probes.sh m596 export/mm8_m596.glb Walk2,Run2 Sprint`,
`scripts/probes.sh m592 export/mm8_m592.glb Walking,Running Walk2,Jog,Sprint`, `scripts/crotch_stretch_probe.py`;
filmstrips `blender -b --python scripts/render_clip.py -- <glb> <prefix> <clips>` then `scripts/sheet.py`; viewers
`scripts/build_viewers.py <m> <export> <title> <old> <new>`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_<m>_gait_h22_claude playback` and `scripts/playback_sheet.py <m> <clips>`; regressions
`scripts/regressions.sh`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h22/export/mm8_<m>.glb --world mm8 --name mm8_<m>.glb`. Rollback:
install `work/mm8_<m>_pre_gait.glb` the same way and drop the bindings. Trial jobs are in `jobs/try/` and
`work/var_*.json` (`work/variant.sh`).
