# Gait rollout package h12: MM7 Devil, Elf Archer, Elf Spearman, Goblin, Blaster Guy (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM7 sources
(`assets_source/worlds/mm7/models/`; pre-gait copies `work/mm7_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending; the sources are library loops
(`work/sources/`, copied from `../h21/work/sources/`; library-derived, never commit). All five are **installed**
(`tools/install_model.py --world mm7`, `work/exports.sha256` = the installed sources); `actors.yml` is not edited here:
[bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Devil A-C (`mm7_m178`, hunched, long claws, 8-bone tail) | Walk2: Mixamo Mutant Walking (its `Walking`'s source), 1.00 s, 2.1506, 2.15 · Jog: humanoid set Unarmed-Run-Forward, 0.68 s, 2.9536, 4.34 |
| Elf Archer A-C (`mm7_m214`, bow in the left hand) | Walk2: Relax-Walk-Forward, 1.04 s, 1.4323, 1.38 · Jog: Unarmed-Run-Forward, 0.80 s, 2.4562, 3.07 |
| Elf Spearman A-C (`mm7_m218`, 2 m spear on a pelvis-child bone) | Walk2: 2Hand-Bow-Walk, 0.80 s, 1.9505, 2.44 · Jog: Unarmed-Run-Forward, 0.72 s, 3.4574, 4.80 · Sprint: Unarmed-Sprint, 0.56 s, 4.4418, 7.93 |
| Goblin A-C (`mm7_m246`, broadsword) | Jog: Unarmed-Run-Forward, 0.76 s, 2.3131, 3.04 · Sprint: Unarmed-Sprint, 0.54 s, 3.7404, 6.93 |
| zBlasterGuy A-C (`mm7_m475`, 12-chain cape, pistol) | Jog: Unarmed-Run-Forward, 0.72 s, 3.2072, 4.45 (walk unchanged) |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree; planted soles per side within 1 %,
`review/<m>_probes.txt`). No longer bound for locomotion but kept: the Devil's, Archer's and Spearman's `Walking` and
`Running`, the Goblin's `Running`.

## Why these clips (`review/mm7_<m>_targets.txt`, `review/mm7_<m>_gate_installed.txt`)

- **Devil** (MAW leaves its speed): wandering 1.85-2.78 played its Mutant walk (1.31 u/s, stride untrusted: vertices
  1.959 / feet 3.841) at x1.41 and B/C wandered on `Running`; the chase (3.71-5.56) played `Running` (1.98 u/s) at
  x1.87 and at the cap. Walk2 at the target 2.15 and a Jog at 4.34.
- **Elf Archer** (ranged): Walking (1.82 u/s) played the slow wander (1.34-1.51) at x0.72-0.81; tier A walked as it
  chased (walk-as-run, x1.44) though 2.68 u/s is a run pace (Froude about 0.8), B/C chased on `Running` with an
  untrusted stride (1.993 / 1.696 against the bound 2.13). A slower Walk2 and a Jog for every tier.
- **Elf Spearman**: the chase (4.73-5.52) played `Running` at x1.64-1.91 (stride FAIL: bound 2.121 against 1.921 /
  1.676), MAW's chase (8.28-8.67) at the cap. Jog and Sprint; Walk2 because with a real Jog tier C's wander (2.76)
  would play `Walking` at x1.61 (the installed bindings had it on `Running` at x0.95).
- **Goblin**: MAW's chase (6.91-7.09) played `Running` at the cap; `Running`'s bound stride 1.8 failed the stride check
  (measured 2.114 / feet 1.545, untrusted), so the Standard chase (2.91-3.27) gets a Jog too. Walk unchanged.
- **Blaster Guy** (ranged, one speed for all tiers): walk-as-run; the chase at 4.52 u/s (Froude about 2.3, a run)
  played `Walking` at the cap with x1.10 slide. A Jog; the walk stays (x1.10).

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Devil         standard/maw A wander Walk2 x0.86  chase Jog x0.85
              standard/maw B wander Walk2 x1.08  chase Jog x1.07
              standard/maw C wander Walk2 x1.29  chase Jog x1.28
Elf Archer    standard/maw A wander Walk2 x0.97  chase Jog x0.87
              standard/maw B wander Walk2 x1.03  chase Jog x0.93
              standard/maw C wander Walk2 x1.09  chase Jog x0.98
Elf Spearman  standard A wander Walk2 x0.97  chase Jog x0.98 | maw A chase Sprint x1.04
              standard B wander Walk2 x1.05  chase Jog x1.07 | maw B chase Sprint x1.07
              standard C wander Walk2 x1.13  chase Jog x1.15 | maw C chase Sprint x1.09
Goblin        standard A wander Walking x0.83  chase Jog x0.96 | maw A chase Sprint x1.00
              standard B wander Walking x0.88  chase Jog x1.02 | maw B chase Sprint x1.01
              standard C wander Walking x0.94  chase Jog x1.08 | maw C chase Sprint x1.02
zBlasterGuy   standard/maw A-C wander Walking x1.10  chase Jog x1.01
```

MAW's wander rows (hostile speed, not judged): Elf Spearman A on Walk2 at **x1.70**, B/C Jog x0.88-0.90; Goblin Jog
x1.14-1.16.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h06/scripts/compose_gait.py` (h16's composer with h02/h04 `raise_arms`, h07 `arm_raise_deg`, h01
`even_bob`, h19 `track_out` and `follow_thighs`, h06's per-side toe-out) with h08's `cloth` (its `cloth_sim.py`) wired
into `main`, and one addition:

- **`hand_props`** {node: hand bone}: the Elf Spearman's `Spear` is a world-keyed child of `B_Pelvis` held in the left
  fist (constant grip in the accepted clips, spread 0.1-1.6 mm); the composer would have carried it with the new
  pelvis. It is now keyed per frame as the left hand's world times the base clip's grip (`node_track.py`: the grip is
  exact in every new clip).

All rigs are `B_*` (no renaming). Legs, pelvis and trunk rhythm from the library loop, two-bone IK, `lock_stance`
planted soles on jogs and sprints, integral plant and per-frame grounding on walks, `stance_foot: Standing` with 5 deg
toe-out, `foot_smooth`, `even_bob` + `symmetric_drop`; arms, hands, props and tails from the model's own clip (`base`:
Running, Walking for the walks and for the Blaster Guy, which has no run), phase-aligned. Per model:

- **Devil**: Walk2 from its own Mutant walk at a 1.0 s loop (forward scale 1.15), trunk weights 0.5 and `bob` 0.1
  (full trunk weights gave 14.5 % head bob), `ground_sigma` 2.5 (6 left both feet 2.6 cm up at the heel strike: floor
  FAIL). Jog `arm_out_deg` L 6 / R 12 and `swing_height` 0.9: the long right claws met the left foot's swing (10 % /
  34 mm; accepted `Running` 13 % / 33 mm), now 0.
- **Elf Archer**: Walk2 from the Relax walk (natural fit, forward scale 1.01). The bow's rear limb touches the quiver
  bottom and the left buttock in the Jog (37 % / 27 mm) as in the accepted `Running` (29 % / 25 mm); `arm_out_deg` and
  `side_gain` on the bow arm did not change it (it is the accepted carry).
- **Elf Spearman**: Walk2 legs from 2Hand-Bow-Walk (the library walk with the longest natural stride; Armed-Walk
  needed forward scale 1.48), `bob` 0.5, `arm_out_deg` R 5 (the free forearm met the right thigh 20 % / 16 mm). The
  run's trunk lean put the spear tip 18.5 cm **under** the floor in the Sprint and 1.6 cm above it in the Jog:
  `arm_raise_deg` L 8 (Jog) / 20 (Sprint, with `arm_out_deg` L 10) turns the spear arm forward-up about the shoulder
  line; tip lowest Walk2 6.7 cm, Jog 15.0, Sprint 22.3 (Walking 10.6, Running 25.3).
- **Goblin**: h07's sword-arm raise (`arm_raise_deg` R 25 around phase 0.45 / 0.5, half width 0.25) and `arm_out_deg`
  R 6 / 8: the rising right thigh met the blade (Jog 22 % / 37 mm, Sprint 12 % / 35 mm, plus the hand at the hip),
  now 0.
- **Blaster Guy**: arms and pistol from `Walking` with `arm_gain` 1.5, `elbow_forward_deg` L 35 / R 25,
  `arm_out_deg` R 7 (the blaster brushed the right hip 11 % / 23 mm, now 5 % / 4 mm). Cape: h08's numpy port of the
  robed projects' `robe_sim.py` (the Blaster Guy's own `robe_sim.py` has the same constants), chains dumped from
  `../../mm7_m475_claude/export/mm7_m475.blend` (`work/m475_chains.json`) with m422's options (`mid_collide`,
  `final_collide`, `bend_smooth` 3, `bend_max` 15, `nb_final`), `leg_r` 2.5 and `swing_height` 0.6: with the
  bake's `leg_r` 1.3 the kicked heel came out through the back of the cape (64 % of samples, up to 48 cm), now 0
  (`skirt_poke_probe.py`; `Walking` 68 % / 75 mm). The port re-simulated on `Walking` matches its baked chains at
  the median (0.1 cm) but differs at p95 15.7 / max 27.5 cm (`cloth_check.py`), as h08 found on the Monk.

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase (`align: Walking`): Devil 0.25
(installed Running 0.24), Archer 0.18 (Running 0.23), Spearman 0.18 (Running 0.23), Goblin 0.18 (Running 0.23),
Blaster Guy 0.75 (no Running). No installed walk/run pair here is half a loop apart.

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all five (`review/<m>_winding.txt`). `prefix_check.py` ok on all five.
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R):
  - Devil Walk2 +4.1 / +4.8, Jog +5.0 / +4.9; installed Walking +14.1 / +25.5, Running +17.2 / +22.1
  - Elf Archer Walk2 +4.8 / +4.8, Jog +5.0 / +4.9; Walking +11.3 / +3.0, Running +27.7 / +7.8
  - Elf Spearman Walk2 +3.9 / +4.3, Jog +5.0 / +4.9, Sprint +5.1 / +4.9; Walking +14.0 / +10.3, Running +15.2 / +34.1
  - Goblin Jog +5.0 / +4.9, Sprint +5.1 / +4.9; Walking +13.9 / +9.6, Running +19.4 / +36.0
  - Blaster Guy Jog +5.0 / +4.9; Walking +7.7 / +4.1
- Head bob (bob_audit's measure, `bob_probe.py`; `uneven`): Devil Walk2 5.5 % (0.25), Jog 6.8 % (0.10); Archer Walk2
  4.3 % (0.07), Jog 5.2 % (0.03); Spearman Walk2 4.8 % (0.01), Jog 6.0 % (0.04), Sprint 5.0 % (0.07); Goblin Jog 5.3 %
  (0.03), Sprint 5.4 % (0.02); Blaster Guy Jog 5.0 % (0.01). (Accepted walks: Devil 6.9 %, Archer 5.7 %, Spearman 5.0 %.)
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/finger/prop inside legs or trunk): 0 % arms in every new
  clip of the Devil, Archer, Spearman and Goblin; sword 0 %. At the accepted clips' level: Archer bow (above), Spearman
  spear 32 % / 19-26 mm in Jog/Sprint against the slung back shaft and hip pouch (Running 27 % / 29 mm, Walking 65 % /
  27 mm; Walk2 61 % / 27 mm), Blaster Guy arms 41 % / 38 mm and 34 % / 32 mm against the cape shell and fused puffed
  sleeve (Walking 43 % / 35 mm and 47 % / 35 mm). Arm skin stretch p99 within 0.03 of the base clips' except the
  Blaster Guy's left (p99 1.34 / max 2.53 against Walking's 1.18 / 1.89; the project's accepted maximum is 2.84).
- Lowest skin: within 0.04 cm of the floor in every new clip (none below -1 cm).
- Playback (`tools/run_creature_review.py check` and `playback`: no console errors, every clip switch, normal and half
  speed; looked at): viewers in `../../mm7_<m>_gait_h12_claude/review/` (the wrapper needs a direct child of
  `creatures/`), sheets `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/`.
- Headless actor regressions on the installed GLBs with the current (unapplied) bindings (`scripts/regressions.sh`,
  `review/regression_*.log`): no case names these five models (`runCase("mm7_` has only
  `mm7_decoration_models_outdoor_maps`); the generic `mm6_mm7_mm8_actor_models_build_every_binding` and
  `every_map_loads_and_builds_its_actor_models` cover them; both PASS on the installed files. `game/outdoor/HeadlessOutdoorDiagnostics.cpp` names none
  of their walk or run clips.

## Doubtful / left open

- New clips plant at 5 deg toe-out while the accepted walks and runs plant at 3-36 deg: the heading changes at
  walk/run switches, as on earlier packages.
- Elf Archer tier A no longer walks as it chases (its 2.68 u/s chase is a run pace now); MAW leaves archers alone.
- Elf Spearman MAW tier A wanders (not judged) on Walk2 at x1.70. The spear arm rides 8 / 20 deg higher in the Jog /
  Sprint than in `Running`.
- Devil Walk2 keeps the Mutant walk's lurch (uneven 0.25); its Jog is a humanoid run under the Mutant run's arms and
  tail (the Devil's `Running` is a Mutant run).
- Blaster Guy: the cape port differs from the baked `Walking` at the hem (above); `swing_height` 0.6 makes a low jog
  so the kicked heel stays under the cape.

## Shared tools

No problem found in `claude_shared/` tools. `gait_gate.py` takes about 2 minutes per model.

## Rebuild

`scripts/rebuild.sh [m178 m214 m218 m246 m475]` composes the exports from `work/mm7_<m>_pre_gait.glb` and `jobs/`, then
runs `gait_gate.py` and `check_winding.py`; it reproduces the installed sources byte for byte (checked). Inputs: the
library loops in `work/sources/` (copied from `../h21/work/sources/`) and `work/m475_chains.json` (`/snap/bin/blender
--background --factory-startup --python scripts/dump_chains.py -- ../../mm7_m475_claude/export/mm7_m475.blend
work/m475_chains.json`). Probes: `scripts/probes.sh <m> export/mm7_<m>.glb <old clips> <new clips> [node=prop.glb]`,
`prop_low_probe.py`, `skirt_poke_probe.py`, `floor_series.py` (lowest point per key, as `floor_audit.py`),
`node_track.py` (a prop bone against a hand); filmstrips `scripts/render_review.sh`; viewers `scripts/build_viewers.py
<m> <export> <title> <old> <new> [node=prop.glb]`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm7_<m>_gait_h12_claude playback` and `scripts/playback_sheet.py <m> <clips>`; regressions
`scripts/regressions.sh`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h12/export/mm7_<m>.glb --world mm7 --name mm7_<m>.glb`. Rollback:
install `work/mm7_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, floor fix or re-export of
these models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
