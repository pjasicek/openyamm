# MM8 Lizardman Warrior (`m404`): new Walking (2026-10-19)

User: "revisit lizardman warrior walking animation - it looks like his upper body is like static and he does this
tip-tap-tip-tap with his legs, like doesnt really move with his entire body."

Staged only: not installed, `actors.yml` and the ledger untouched. Source: the installed
`assets_source/worlds/mm8/models/mm8_m404.glb` (the reduction from `../mm8_m404_reduce_claude/`, installed
2026-10-19 09:24), copied to `work/mm8_m404_source_pre_walk.glb` (rollback); sword copy
`work/mm8_m404_sword_source_pre_walk.glb` (unchanged, not re-exported).

## Cause

The installed Walking is the humanoid-set `2HandSwordWalk` (`../mm8_m404/3d_claude/HANDOFF.md`), deliberately damped
by the build:

- `posture_timing.py`: spine chain at 35 % and pelvis rotation and clavicles at 30 % of the source.
- `fit_feet.py`: foot paths halved about the hips (`T.x = hip.x + .5 * ...`), pelvis bob at 15 %, soles forced flat
  for the whole cycle (the sole plane fit), lift rescaled to 10 cm.
- `actors.yml` binds `stride_length: 0.7696` (and `run_stride_length` the same). The game drives the walk phase by
  distance (`WorldFxSystem.cpp`: one cycle per `stride_length * scale`), so with the m404 speeds (155 / 175 / 195
  units/s, doubled while pursuing) the cycle runs 1.9-2.5 times a second when wandering and 3.8-5 times while chasing:
  7-10 short flat-footed steps a second.

Measured (`review/diag_installed.json`, `work/installed.npz`): pelvis bob 2.7 cm, no sway; hips turn 8.9 deg, the chest
turns *with* them (no counter-rotation); foot pitch 0 deg in every frame (tip-tap); fore-aft foot travel 36-39 cm; the
planted feet also slide 10-27 cm per contact (`review/check_installed.json`), because the lift phase was moved without
moving the horizontal paths. The source walk moves the hips 30 deg, counter-turns the chest about 18 deg, bobs 6 cm
and rolls each foot through 77 deg.

## What was built (`scripts/author_walk.py`)

Authored on the installed GLB in Blender and written **in place** into the GLB's Walking accessors (same 193 keys,
same 0.8 s; the actor regression pins the duration). Procedural legs on the source walk's upper body, chosen over a
fresh library retarget because the library walk's legs had to be refitted anyway (the source plan exceeds this
rig's leg reach at full stride, which is why the build halved it), while its upper-body motion is already in the
installed clip and can be restored exactly. No paid actions; no library clip used beyond what the build stored.

- **Upper body.** The damping of `posture_timing.py` is undone with quaternion powers on the oscillation about each
  bone's cycle mean (pelvis to 80 % of the source, spine to 85 %); the mean lean is raised only 1.3x, so the sword
  stays at the native guard height. Hips now turn 24 deg and roll 7 deg; the chest counter-turns 16 deg.
- **Arms and grip.** Clavicles, arms, hands and fingers keep their installed locals, so the two-hand grip is exactly
  the installed one (left-to-right hand transform unchanged to 2e-6, socket-to-hand to 2e-7); the arms ride on the
  turning chest, plus a 2 deg common bounce about the shoulder line after each contact. The warrior holds the sword
  in both hands, so there is no free arm to swing.
- **Head.** Stabilised 70 % toward its cycle mean, 1.5 deg nod after each contact (yaw range 3 deg).
- **Pelvis.** 3 cm crouch, two bobs per cycle (5.8 cm range, lowest just after each contact), 1.8 cm sway toward the
  stance foot, 0.8 cm surge; lowered further (up to 2.2 cm, smoothed) only where a leg would overreach.
- **Legs.** Source timing (left contact at 0.79, right at 0.29 of the cycle, duty 0.62), stride **1.45 m** per cycle.
  The toes are skinned to the foot bone (Toe0 has no skin), so the sole is rigid: heel strike at 9 deg toe-up pivoting
  on the rearmost sole point, flat stance, heel-off roll to 20 deg on the toe tips; the pitch axis is perpendicular
  to the sole's heel-toe line (keeps the gates' foot heading), and the foot is lifted wherever a sole point would go
  under the floor. Swing: Hermite fore-aft path whose end slopes equal the ground speed (no skid at toe-off or
  landing), toe-off pitch held while the toes clear, quick pick-up and soft landing (4.5 cm lift peaking early).
  Two-bone IK, knees forward.
- **Tail.** Installed sway plus a lagging counter-swing to the stronger hip turn (tip 48 cm sideways).
- **Loincloth.** The build's leading-thigh rule (`finish_walk.py`).

## Checks

| | installed | new |
|---|---:|---:|
| pelvis bob / sway | 2.7 / 0.1 cm | 5.8 / 3.6 cm |
| hips yaw / roll, chest yaw | 8.9 / 2.7, 7.2 deg (with hips) | 23.8 / 7.1, 16.3 deg (counter) |
| foot pitch range | 0 deg | 27-29 deg |
| planted-foot slip per contact | 101-268 mm | 0.9-4.7 mm |
| lowest body point | 2.0 mm | 1.4 mm |
| peak bone speed | 907 deg/s (left calf) | 431 deg/s |

- **Shared gates** (`gates.json` = the build's `delivery.gates.json`, prop path to the sword copy;
  `review/gates_installed/`, `review/gates_new/`, `scripts/gate_diff.py`): no new FAIL. Walking lift 82-85 mm
  (80-120), swing knee 58-59 deg (40-60), floor penetration 0, foot heading 0.5 / 1.1 deg, sword-body, arm-body,
  head and cloth penetration 0, grip gaps unchanged. One already failing row got worse: `foot_yaw_deg` L on
  `shadow3` (the coarsest shadow proxy, never drawn), 12.1 -> 17.6 deg, an artefact of its coarse sole patches tilting
  with the heel roll.
- **Arm and hand gate rows** (stretch, elbow, forearm roll, wrist, palm grip, finger curl, rotation step and
  acceleration): all PASS, values as installed apart from rotation steps (up to 2.5 deg per 48 Hz frame, limit 14-16).
- **`compare_glb.py`** (`review/compare_installed.json`): JSON identical apart from Walking accessors' min/max, buffer
  size identical, no accessor outside Walking's samplers changed. Changed channels: pelvis rotation and translation,
  spine, head, arms (bounce), legs, toes, loincloth, tail.
- **`lod_check.py`**: every LOD keeps its bounds; Walking minimum 1.0-1.5 mm above the floor; no stretched faces.
- **`check_winding.py`**: 0 inverted closed parts.
- **`check_walk.py`**: tail to legs at least 56 mm (installed 90 mm), sword to torso/legs at least 162 mm.
- **Viewer**: `python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m404_walk_claude check`:
  48 switches, no console errors.

Review files: `review/walk_plot.png` (pelvis, chest and head height and yaw, sole heights; installed dashed, new
solid), `review/walk/filmstrip_side.png` and `filmstrip_front.png` (one cycle, installed above, new below), viewer
`review/viewer/` (installed / new walk per tier, sword attached; rebuilt by `scripts/viewer_build.py`).

## Needed with the install: binding change

The new clip covers 1.45 m per cycle. All three `mm8_m404.glb` entries in `assets_dev/worlds/mm8/models/actors.yml`
need `stride_length: 1.45` (and `run_stride_length: 1.45` while `run: Walking`); with the old 0.7696 the feet would
slide backward by about half a stride every cycle. Cadence then becomes about 1.0-1.3 cycles/s wandering and
2.0-2.7 while chasing (was 1.9-2.5 and 3.8-5). The chase speed (2.95-3.7 m/s) is above the engine's run threshold
(2.4 m/s), so a dedicated `Running` clip would suit pursuit better; that is separate work.

## Status

Installed 2026-10-19 after user review ("ok accepted") with `tools/install_model.py --world mm8`; `stride_length` and `run_stride_length` set to 1.45 on all three `mm8_m404.glb` entries in `assets_dev/worlds/mm8/models/actors.yml` (was 0.7695523202419281); actor regression `mm8_lizardman_warrior_actor_models_keep_tiers_sword_and_native_roles` passes (`review/regression.log`). Rollback also needs the stride restored to 0.7695523202419281. Commands used (repository root):

```
python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m404_walk_claude/export/mm8_m404.glb
OPENYAMM_REGRESSION_FILTER=mm8_lizardman_warrior_actor_models ./build/game/openyamm --headless-run-regression-suite actors
```

Rollback: `python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m404_walk_claude/work/mm8_m404_source_pre_walk.glb`
and restore `stride_length` / `run_stride_length` to 0.7695523202419281.

A re-export from `../mm8_m404/3d_claude/` brings the old walk back; rerun
`blender -b -P scripts/author_walk.py -- <export.glb> <out.glb>` on it (it reads the damped Walking it replaces).

Reproduce: `author_walk.py -- work/mm8_m404_source_pre_walk.glb export/mm8_m404.glb work/author_final.json`
(defaults are the chosen parameters; `WALK_*` environment variables override them) -> `sample_clips.py`, `diag.py`,
`plot_walk.py`, `check_walk.py`, `render_strip.py` + `compose_strip.py`, gates, `lod_check.py` (`REA_NODE=M404`),
`compare_glb.py`, `viewer_build.py`.

## Gait rollout (2026-10-31)

Package h16 of the [gait rollout](../gait_rollout_20261031/h16/README.md) appended two clips to the installed source
for Lizardmen Warrior A/B/C: `Jog` (library Unarmed-Run-Forward legs and trunk on this Walking's two-handed guard,
0.80 s) and `Sprint` (Unarmed-Sprint, 0.62 s); the guard is raised rigidly about the shoulder line by 8-11 deg so the
knees clear it, and the loincloth follows the leading thigh as in Walking. Existing clips, meshes and skins are
unchanged (binary prefix identical). Installed 2026-10-31 with `tools/install_model.py --world mm8`; bindings for the
coordinator (../gait_rollout_20261031/h16/bindings.yml): run: Jog, run_stride_length: 2.6519, sprint: Sprint,
sprint_stride_length: 4.4893 (the walk-as-run `run: Walking` ends). `gait_gate.py` passed for every tier under
Standard and MAW (`../gait_rollout_20261031/h16/review/m404_gait_gate.txt`). Rebuild:
`../gait_rollout_20261031/h16/scripts/rebuild.sh m404` (from the pre-gait copy
`../gait_rollout_20261031/h16/work/mm8_m404_pre_gait.glb`). A far-LOD repair rerun, or a re-export from
`../mm8_m404/3d_claude/` replaces the source without these clips: copy the new source over that pre-gait copy and
rerun the rebuild before installing. Rollback: install the pre-gait copy and drop the bindings.
