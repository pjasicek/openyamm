# Gait rollout package h10: MM7 Behemoth, Dwarf, Golem, Troll, Minotaur (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM7 sources
(`assets_source/worlds/mm7/models/`; pre-gait copies `work/mm7_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending; the sources are humanoid-set
library loops (`work/sources/`, copied from `../h21/work/sources/`; library-derived, never commit). All five are
**installed** (`tools/install_model.py --world mm7`, `work/exports.sha256` = the installed sources); `actors.yml` is not
edited here: [bindings.yml](bindings.yml) is for the coordinator (`apply_bindings.py --dry-run`: 128 diff lines, applies
cleanly).

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Behemoth A-C (`mm7_m162`, hunched ape, Mixamo mutant clips, rigid claws) | Sprint: Unarmed-Sprint, 0.62 s, 4.0863, 6.59 |
| Dwarf A-C (`mm7_m190`, one-handed axe) | Walk2: Armed-Walk, 0.76 s, 1.1715, 1.54 · Sprint: Unarmed-Sprint, 0.48 s, 2.9071, 6.06 |
| Golem A-C (`mm7_m254`, bronze pharaoh statue) | Walk2: Armed-Walk, 1.10 s, 1.1923, 1.08 · Sprint: Unarmed-Sprint, 0.68 s, 3.1567, 4.64 |
| ATroll A-C (`mm7_m461`, the MM8 Troll Peasant's body, bone club, loincloth) | Walk2: Armed-Walk (h20's `m480_walk2` job), 1.15 s, 1.1977, 1.04 · Run: Unarmed-Run-Forward, 0.76 s, 2.5072, 3.30 |
| AMinotaur A-C (`mm7_m286`, one-handed axe, fur kilt) | Sprint: Unarmed-Sprint, 0.64 s, 2.9964, 4.68 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree). No longer bound for locomotion but
kept: the Dwarf's, Golem's and Troll's `Walking` as a walk (the Golem and Troll A/B keep it as their walk-as-run), the
Troll's `Running`.

## Why these clips (`review/mm7_<m>_targets.txt`, `review/mm7_<m>_gate_installed.txt`)

- **Behemoth** (hip 0.86): only MAW's chase (6.00-7.08) failed, `Running` at the 2x cap. Standard's chase on
  `Running` (x1.21-1.28) stays: its stride is untrusted (vertices 3.49 / feet 2.58) but the binding 2.83 is within
  tolerance.
- **Dwarf** (hip 0.57, leg 0.47): `Walking` (1.08 u/s, stride untrusted: 0.47 / 1.21) played B/C's wandering at
  x1.52/1.61; MAW's chase 6.95-7.26 at the cap. `Running` stays for Standard's chase (x0.88-1.00).
- **Golem** (hip 0.83): its walk-as-run `Walking` (1.68 u/s) played the wandering (1.05-1.18) at x0.63-0.70 and MAW's
  chase (4.99-5.12) at the cap. Standard's chase (2.10-2.36, Froude 0.54-0.68) stays on `Walking` as before (x1.25-1.41):
  a heavy statue at a walking pace. Its unbound `Running` (planted stride 2.2, 3.0 u/s) would play MAW's chase at x1.66.
- **ATroll** (hip 0.85): wandering 1.04-1.35 played `Walking` (1.87) at x0.56-0.61; tier C was bound to `Running` with
  stride 1.108 against the measured 1.93 (feet) / 3.94 (vertices) (stride FAIL; its wandering played `Running`); MAW's
  chase 4.15-4.46 at the cap. A/B chase at 2.08/2.28 (Froude 0.52/0.62): walk-as-run kept. C chases at 2.70 (Froude
  0.87, a run pace): the new `Run`. One `Run` (3.30 u/s) serves C's chase (x0.82) and every tier's MAW chase as `sprint`
  (x1.26-1.35), so the Troll needs no third clip. Tier-split bindings, gated with `../q2/scripts/gate_only.py`.
- **AMinotaur** (hip 0.92): MAW's chase (A 5.64, B 4.89) on `Running` at x1.95/1.70; tier C chased on `Walking`
  (x1.59 at 2.66, Froude 0.78: a run pace) and MAW-chased at the cap. C now binds `Running` like A/B (x0.92) and every
  tier gets a Sprint.

## Gate window sections (`review/m<m>_gait_gate*.txt`)

```
Behemoth   standard A wander Walking x1.16  chase Running x1.28 | maw A chase Sprint x1.07
           standard B wander Walking x1.10  chase Running x1.21 | maw B chase Sprint x0.99
           standard C wander Walking x1.11  chase Running x1.22 | maw C chase Sprint x0.91
Dwarf      standard A wander Walk2 x0.99  chase Running x0.88 | maw A chase Sprint x1.20
           standard B wander Walk2 x1.06  chase Running x0.94 | maw B chase Sprint x1.17
           standard C wander Walk2 x1.13  chase Running x1.00 | maw C chase Sprint x1.15
Golem      standard A wander Walk2 x0.97  chase Walking x1.25 | maw A chase Sprint x1.08
           standard B wander Walk2 x1.03  chase Walking x1.33 | maw B chase Sprint x1.09
           standard C wander Walk2 x1.09  chase Walking x1.41 | maw C chase Sprint x1.10
ATroll     standard A wander Walk2 x1.00  chase Walking x1.11 | maw A chase Run x1.26
           standard B wander Walk2 x1.10  chase Walking x1.22 | maw B chase Run x1.29
           standard C wander Walk2 x1.30  chase Run x0.82     | maw C chase Run x1.35
AMinotaur  standard A wander Walking x0.99  chase Running x1.15 | maw A chase Sprint x1.21
           standard B wander Walking x0.89  chase Running x1.03 | maw B chase Sprint x1.05
           standard C wander Walking x0.79  chase Running x0.92 | maw C chase Running x1.38
```

Stride and window PASSED on all five, floor ok on Dwarf, Golem, Troll and Minotaur. **Behemoth: the gate prints
FAILED: floor for the installed `Attack`** (the left claws strike 16.6-20.8 world units into the floor at the blow), the
same before this work; `../../mm7_m162_reduce_claude/README.md` left it open for the user (raising the root would hop
the body). Not a locomotion clip and not changeable here (existing clips stay byte-identical); the new Sprint is
floor-clean (lowest +0.1 cm).

MAW's wander rows (hostile speed, not judged): Behemoth `Running` x0.92-1.08, Dwarf `Running` x1.00-1.05, Golem
`Walking` x1.49-1.53, Troll A/B `Walking` x1.11-1.14 but **Troll C on Walk2 at x2.00 (slide 1.07)**: C has no walking
clip near 2.2 u/s once its run is the Run (the recurring walk-preference question in STATUS.md), Minotaur A `Running`
x0.98, B/C `Walking` x1.46/x1.19.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h06/scripts/compose_gait.py` (h16's composer with h02/h04 `raise_arms`, h07 `arm_raise_deg`, h01
`even_bob`, h19 `track_out` and `follow_thighs`, h06's per-side toe-out), unchanged. `scripts/render_clip.py` takes
`ortho=` and `cz=` (camera size and height: the Behemoth is wider and the Dwarf shorter than the default frame). Legs,
pelvis and trunk rhythm from the library loop, two-bone IK, `lock_stance` planted soles on runs and sprints, the
integral plant and per-frame grounding on walks, `stance_foot: Standing` with 5 deg toe-out, `foot_smooth`,
`even_bob` + `symmetric_drop`; arms, hands, props from the model's own `Running` (`Walking` for walks), phase-aligned.
All five are `B_*` rigs. Per model:

- **Behemoth**: the hunched rest pose is kept (`lean` 1 = the base run's mean posture) with only 3 deg extra lean on
  Spine1/Spine2 and no arm gain: the pilot's trunk lean (4-7 deg per bone) put the right claws 4.8 cm into the floor.
- **Dwarf**: Walk2 from h02's MM6 Dwarf job (`swing_height` 1.4 against the scaled walk's shuffle). Sprint: h02's
  sprint at a quicker, shorter stride (0.48 s / 2.75 instead of 0.52 s / 3.1): the long stride drove the short legs
  into splits and stretched an armpit-belly edge 8.2x (below).
- **Golem**: a heavy slow Walk2 (1.1 s, `swing_height` 1.3); Sprint low (`stance_extension` 0.93), spine weights 0.6,
  `swing_height` 0.85, arms from its unbound `Running` with gain 1.2.
- **ATroll**: Walk2 = h20's Troll Peasant job on this copy of the same body. Run: h20's MM8 Troll jog job at 3.3 u/s
  with the club as a clearance probe, and `loincloth` on `LoinFront` with the project's rule
  (`../../mm8_m480_claude/scripts/author_motion.py`: forward thigh angle from rest x 1.10 + 5 deg; clamp 90): `Running`'s
  phase-aligned flap let the raised knee through by 21 cm (39 % of the loop); now 22 % / 52 mm at one vertex
  (accepted `Running` 12 % / 41 mm, one vertex). `LoinBack` stays the base clip's (0 % back pokes).
- **AMinotaur**: the axe arm raised 12 deg forward (`arm_raise_deg` R with `arm_raise_window` [0.62, 0.25], the right
  knee's drive) and turned out 5 deg, `arm_clearance` off; free arm gain 1.3; spine weights 0.5.

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase (`align: Walking`): Behemoth 0.26
(Running 0.23), Dwarf 0.18-0.19 (Running 0.22), Golem 0.18-0.19 (Running 0.23), Troll 0.75 (its `Running` is half a
loop off at 0.28; the new clips follow the walk), Minotaur 0.24 (Running 0.23).

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all five (`review/m<m>_winding.txt`). `prefix_check.py` ok on all five.
- Foot heading (`foot_heading_probe.py`, joints, toe-out from +Z, planted L / R; the joint line matches the foot on
  these rigs):
  - Behemoth Sprint +5.1 / +5.0 (swing -6.4..+6.5); Walking +1.2 / +9.2, Running +2.3 / -8.3
  - Dwarf Walk2 +4.7 / +5.0, Sprint +5.1 / +5.0; Walking +16.1 / +19.1, Running +13.6 / +21.0
  - Golem Walk2 +4.8 / +5.0, Sprint +5.1 / +5.0; Walking +9.0 / +6.1
  - Troll Walk2 +4.8 / +5.0, Run +5.0 / +4.9; Walking +0.0 / +1.1
  - Minotaur Sprint +5.1 / +4.9; Walking +32.0 / +24.3, Running +5.8 / +8.7
- Head bob (bob_audit's measure, `bob_probe.py`; `uneven`): Behemoth Sprint 6.3 % (0.01); Dwarf Walk2 3.1 % (0.08),
  Sprint 6.2 % (0.07); Golem Walk2 3.4 % (0.09), Sprint 5.4 % (0.01); Troll Walk2 3.3 % (0.07), Run 6.2 % (0.21);
  Minotaur Sprint 5.2 % (0.01).
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/finger/prop inside legs or trunk), new vs accepted:
  Behemoth Sprint armL 13 % / 22 mm (Running 19 % / 32 mm); Dwarf Walk2 0 %, Sprint armL 7 % / 20 mm, axe 0 % (Running
  armL 7 % / 15 mm); Golem 0 % (Walking armL 8 % / 37 mm); Troll Walk2 and Run 0 %, club 0 % (Running club 6 % / 10 mm);
  Minotaur Sprint armR 3 % / 7 mm (the axe fist at the right thigh), axe 0 % (Running armR 40 % / 39 mm, axe 13 % /
  30 mm). Wrist maxima equal the base clips'.
- Arm skin stretch (p99 / max): within 0.05 of the base clips' p99 everywhere; maxima Behemoth 2.26 (Running 2.20),
  Dwarf Sprint 3.85 (Running 3.80), Golem Sprint 4.63 (Running 4.38), Troll Run 2.15-2.23 (Running 2.20-2.34), Minotaur
  Sprint L 4.29 (Running 3.63; 3.97 even without the arm gain: the lean).
- Lowest skin: 0.0 to +0.15 cm on every new clip, no key below -1 cm.
- Planted stride per side at 1 cm (`stride_probe.py`): within 3 % of the binding except the Behemoth's few-vertex claw
  soles (L 4.46 on 23 vertices, R 4.02 on 44; gate trusted 4.086 / feet 3.83).
- Playback (`tools/run_creature_review.py check`: no console errors on all five; `playback` at normal and half speed,
  looked at): viewers in `../../mm7_<m>_gait_h10_claude/review/`, sheets `review/<m>_playback_sheet.png`; Blender
  filmstrips `review/iter/`.
- Headless actor regressions: no case names these five MM7 models (`grep runCase(` in
  `game/outdoor/HeadlessOutdoorDiagnostics.cpp`); `mm6_mm7_mm8_actor_models_build_every_binding` covers them and passes
  on the installed GLBs with the current bindings (`scripts/regressions.sh`, `review/regression_*.log`: 647 descriptors
  on 185 models, 0 failed). Rerun it after `apply_bindings.py`.

## Doubtful / left open

- **Behemoth Attack floor** (above): the gate stays FAILED on floor until the user decides on that clip.
- **Dwarf weighting**: 138 belly/armpit vertices at 0.67-0.78 m carry both clavicle and thigh weight (a rig fault of
  the model); a long sprint thigh swing stretched one 14 mm edge 8.2x (`Death` already 6.9x). The quicker shorter
  sprint keeps it at 3.85x, like `Running`. Hidden under the beard and arm.
- **Troll C MAW wandering** on Walk2 at x2.00 (not judged; see above). Keeping C's run on `Walking` (x1.44) would
  avoid it but chase at a run pace on a walk.
- The Troll's Run front flap still meets the raised knee at one vertex (52 mm, 22 % of the loop), like `Running`.
- Minotaur Sprint free-arm stretch max 4.29x (Running 3.63x) on a small armpit edge; p99 equal.
- New clips plant at 5 deg toe-out; the accepted Dwarf (16-21 deg) and Minotaur Walking (24-32 deg) plant wider, so the
  heading changes at walk/run switches, as on earlier packages.
- `mm7_m461` texture pass (`../../mm8_m480_texpass_claude/scripts/merge_install.sh`) was waiting for this package; it
  layers onto the currently installed source and keeps every clip, so it can run now.

## Shared tools

No problem found in `claude_shared/` tools. Notes: `gait_gate.py`'s floor check judges every living clip, so a model
with a pre-existing non-locomotion floor fault (Behemoth `Attack`) cannot reach PASSED in this rollout; and its `--set`
applies to every descriptor, so tier-split bindings (Troll) need `../q2/scripts/gate_only.py`.

## Rebuild

`scripts/rebuild.sh [m162 m190 m254 m461 m286]` composes the exports from `work/mm7_<m>_pre_gait.glb` and `jobs/`, then
runs `gait_gate.py` (the Troll per tier group) and `check_winding.py`; it reproduces the installed exports byte for
byte. The library loops in `work/sources/` were copied from `../h21/work/sources/`. Probes: `scripts/probes.sh <m>
export/mm7_<m>.glb <old clips> <new clips> [node=prop.glb]`, `SKIRT_BONES=LoinFront,LoinBack scripts/skirt_poke_probe.py`;
filmstrips `scripts/render_review.sh <glb> <prefix> <clips> [node=prop.glb] -- ortho=.. cz=..`; viewers
`scripts/build_viewers.py <m> <export> <title> <old> <new> [node=prop.glb]`, then `python3 tools/run_creature_review.py
--project level_generation/creatures/mm7_<m>_gait_h10_claude playback` and `scripts/playback_sheet.py <m> <clips>`;
regressions `scripts/regressions.sh`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h10/export/mm7_<m>.glb --world mm7 --name mm7_<m>.glb`. Rollback:
install `work/mm7_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds these sources must keep or re-graft the clips (copy the new source over the pre-gait copy
and rebuild).
