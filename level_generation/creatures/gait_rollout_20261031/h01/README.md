# Gait rollout package h01: MM6 BThief, Barbarian, FighterLeath, FighterChain (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to four installed MM6 humanoids
(`assets_source/worlds/mm6/models/`; the pre-gait copies are `work/mm6_<m>_pre_gait.glb` = assets_source commit
`a762c96`). Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary
chunk is a byte-identical prefix, every input accessor, buffer view, node, mesh, skin, material and animation is
unchanged, only animations are appended). No Meshy credits or other spending: the sources are local library loops
(`anim_library/`, never committed). All four are installed (`tools/install_model.py --world mm6`); `actors.yml` is not
edited here: [bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| BThief A/B/C, `mm6_thf.glb` (Meshy rig, 17 cloak chains) | `Walk2`: Mixamo Walk, 0.78 s, 1.5152, 1.94 · `Jog`: humanoid set Unarmed-Run-Forward, 0.64 s, 2.8184, 4.40 · `Sprint`: Unarmed-Sprint, 0.52 s, 3.4402, 6.62 |
| Barbarian A/B/C, `mm6_bar1.glb` | `Jog`: Unarmed-Run-Forward, 0.68 s, 3.2856, 4.83 · `Sprint`: Unarmed-Sprint, 0.56 s, 4.2974, 7.67 (walk unchanged) |
| FighterLeath A/B/C, `mm6_fgt.glb` | `Sprint`: Unarmed-Sprint, 0.57 s, 3.7784, 6.63 (walk and walk-as-run unchanged) |
| FighterChain A/B/C, `mm6_figc.glb` | `Jog`: Unarmed-Run-Forward, 0.78 s, 3.0072, 3.86 · `Sprint`: Unarmed-Sprint, 0.60 s, 3.7980, 6.33 (walk unchanged) |

Strides are `gait_gate.py`'s trusted measurement (planted soles agree within 1 %: `review/<m>_probes.txt`). No longer
bound for locomotion but kept in the GLBs: the Thief's `Walking` and `Running`, the Barbarian's and FighterChain's
`Running` (the FighterChain's walk-as-run binding is replaced by `Jog`).

## Why these clips

`gait_gate.py` targets (no candidate): the Thief wanders 2.30-2.48 u/s, chases 4.60-4.97 and MAW-chases 7.82-8.01 on a
0.69 m leg (1.58 m tall); its Meshy walk (1.27 u/s) played x1.80-1.88 and its jog-like run (2.88) x1.60-1.73. The
Barbarian chases 5.26-6.07 / 8.70-9.10 (run 2.18: x2.40-2.78). FighterChain chases 3.49-4.13 / 6.51-6.82 on its walk
(x1.57-1.85), a running pace (Froude about 1.4), so it gets a jog; FighterLeath likewise but by the user's choice walks
at every Standard speed, so only MAW's chase gets a sprint.

Short legs take quicker, not longer, steps: the Thief's first version (Walk2 1.75 / 0.90 s, Jog 3.1 / 0.70 s, Sprint
3.7 / 0.56 s) carried its hips 7-10 cm below its accepted walk and run (a crouched gait, and the cloak hem dragged
3.7-5.7 cm into the floor); the final cadences (0.78 / 0.64 / 0.52 s) keep the library's natural scaled stride
(forward scale 0.94-1.00) and the hips 1-3.5 cm above that version. The Barbarian's jog and sprint and FighterLeath's
sprint are 5-10 % longer than the source's scaled stride (forward scale 1.05-1.10), the FighterChain's jog 10 % shorter
(a heavier step).

## Gate window sections (`review/<m>_gait_gate.txt`; floor ok on every descriptor)

```
BThief        standard A wander Walk2 x1.18  chase Jog x1.04 | maw A chase Sprint x1.18     PASSED
              standard B wander Walk2 x1.23  chase Jog x1.09 | maw B chase Sprint x1.20
              standard C wander Walk2 x1.28  chase Jog x1.13 | maw C chase Sprint x1.21
Barbarian     standard A wander Walking x1.27  chase Jog x1.09 | maw A chase Sprint x1.13   PASSED
              standard B wander Walking x1.37  chase Jog x1.17 | maw B chase Sprint x1.16
              standard C wander Walking x1.47  chase Jog x1.26 | maw C chase Sprint x1.19
FighterChain  standard A wander Walking x0.78  chase Jog x0.91 | maw A chase Sprint x1.03   PASSED
              standard B wander Walking x0.85  chase Jog x0.99 | maw B chase Sprint x1.05
              standard C wander Walking x0.93  chase Jog x1.07 | maw C chase Sprint x1.08
FighterLeath  standard A wander Walking x0.81  chase Walking x1.63 | maw A chase Sprint x0.98  FAILED (window):
              standard B wander Walking x0.89  chase Walking x1.79 | maw B chase Sprint x1.01  Standard chase only,
              standard C wander Walking x0.98  chase Walking x1.95 | maw C chase Sprint x1.03  the user's choice
```

FighterLeath's three Standard chase rows are the user's standing decision (walk at every Standard speed, `run:
Walking`); the engine keeps the walk there (the sprint would play at x0.52-0.62), and MAW's chase sprints. MAW's
wander rows (hostile speed, not judged): Thief and Barbarian on `Jog` x0.88-0.95, FighterChain on `Walking` x1.46-1.53,
FighterLeath on `Walking` x1.63-1.71. The Barbarian's tier C wander (Walking x1.47) is the installed walk, unchanged.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of package h16's composer (`../h16/scripts/`: the sprint pilot's legs, pelvis and trunk rhythm from the library
loop, two-bone IK, `lock_stance` planted soles on runs and sprints, the integral plant on the walk, `stance_foot:
Standing` with `foot_toe_out_deg: 5`, `foot_smooth`, `symmetric_drop`, `swing_height`, `align` to the walk; Meshy joint
aliases for the Thief). Arms, hands, fingers, twist bones and props come from the model's own `Running` (`Walking` for
the Thief's Walk2), phase-aligned. Additions in this package:

- **`even_bob`**: the source's hip bob made alike on both steps (mean of the signal and itself half a loop later); with
  `symmetric_drop` the limp is gone (FighterLeath's sprint read `uneven` 0.42 with the drop alone). Its trunk
  rotations at 0.7 of the source's (0.31 at full weight: the source's spine sway lifts the head once per loop).
- **`cloak`** (`scripts/cloak.py`): the Thief's 17 cloak chains are simulated over each new clip, a numpy port of its
  project's Blender bake (`../../mm6_thf_claude/scripts/cloak_sim.py`: same constants, capsules, radii, one-sided
  collisions, neighbour spacing, three loops kept last). Chain rest points from the rig blend
  (`scripts/dump_cloak_chains.py`, matching the GLB's bind pose exactly). Against the installed clips the port lands
  within 6 mm (Walking, mean; max 58 mm) and 26 mm (Running, mean; max 115 mm) of the Blender bake, the difference
  being 24 fps keys against 120 Hz samples on chaotic cloth. Two options the bake did not need: `cloak_floor` (chain
  points at least 6.5 cm, Sprint 9.5 cm above the floor instead of 2.5: the lower hips of a fast gait put the hem on
  the floor and the hem skin hangs up to 11 cm below its chain points) and `cloak_leg_pad` (3 cm more on the leg and
  foot capsules: the kicked heel came through the back hem).
- Thief: `arm_clearance` off. Its accepted clips already read arm skin "inside" the jerkin hem (Standing R 89 % 18 mm,
  Walking 27-29 % to 36 mm, Running 32-37 % to 31 mm: forearms against the flared jerkin under the cloak); the
  clearance turned the arms 43-50 deg out to chase that. `swing_height` 0.7 on Jog and Sprint (lower heel recovery
  under the long cloak; the source's high knees lifted its front).

## Checks (`review/`)

- `<m>_gait_gate.txt` as above; `<m>_winding.txt` 0 inverted closed parts on all four.
- Phase: every new clip strikes with the left foot forward-most at its walk's phase (Thief 0.16-0.17 like `Walking`
  0.17; the others 0.74-0.75 like `Walking` 0.75). The installed walks and runs disagree on three models: Barbarian
  `Running` 0.17 and FighterChain 0.12 against their walks' 0.75 (half a loop apart), FighterLeath `Running` 0.92; the
  new clips follow the walks. The Thief's `Running` (0.26) was within 0.1 of its walk.
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R, swing range):
  - BThief Walk2 +2.9 / +3.9 (swing +0.3..+15.8), Jog +5.1 / +4.9 (-5.2..+7.4), Sprint +5.1 / +4.9 (-6.3..+6.4);
    its Walking +9.8 / +12.1 (swing to +35.6), Running +13.6 / +11.3
  - Barbarian Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +4.9 (-6.2..+6.5); Walking -0.1 / +1.7, Running +3.7 / -8.6
  - FighterChain Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5); Walking -0.4 / +1.6
  - FighterLeath Sprint +5.1 / +4.9 (-6.3..+6.5); Walking +6.7 / +6.7
- Head bob (bob_audit's measure, `bob_probe.py`; run range 4-7 %): Thief Walk2 4.5 % / Jog 5.6 / Sprint 4.4 (Walking
  4.5, Running 7.0 uneven 0.40); Barbarian Jog 6.0 / Sprint 5.9 (Running 4.4); FighterChain Jog 4.6 / Sprint 5.5
  (Running 1.9); FighterLeath Sprint 5.4 (Running 16.7, why it walks). `uneven` 0.01-0.23 on every new clip.
- Arm and hand gate (contact probe, 60 Hz): Barbarian, FighterChain and FighterLeath: no forearm, hand, finger or prop
  (sword, axe, shield, mace) inside legs or trunk in any new clip. Thief: as its accepted clips (above): Walk2 L 28 % /
  39 mm, R 57 % / 26 mm; Jog 44 % / 26 mm, 64 % / 39 mm; Sprint 44 % / 37 mm, 75 % / 37 mm (Running 32 % / 21 mm,
  37 % / 31 mm). Wrist maxima equal the base clips' (Thief 35, Barbarian 46, FighterChain 50, FighterLeath 34 deg).
  Arm skin stretch (max edge ratio) about the base clips': Barbarian Sprint 2.14 (Running 2.03), FighterChain Jog 2.09
  (Running 1.91, Walking 2.07), FighterLeath Sprint 3.52 (Running 3.45); Thief Sprint 2.08 on the left (Running 1.78:
  the stronger sprint swing, `side_gain` 1.2), p99 1.41 (1.33).
- Cloak poke-through (`cloak_poke_probe.py`, leg and boot vertices behind the hips with no cloak behind them, mean per
  sample): Walk2 13.6 (Walking 14.9), Jog 40.8 (Running 46.7), Sprint 79.6 (max 141).
- Lowest skin (all primitives): Thief Walk2 -0.89 cm (a cloak hem corner), Sprint -0.14 cm; every other new clip
  0.0-0.3 cm. Planted stride per side within 1 % of the binding.
- Playback review with `tools/run_creature_review.py` (normal and half speed, looked at): viewers in
  `../../mm6_<m>_gait_h01_claude/review/` (the wrapper needs a direct child of `creatures/`), sheets
  `review/<m>_playback_sheet.png`, Thief close shots `review/thf_shots.png`; Blender filmstrips in `review/iter/`.
- Actor regressions on the installed GLBs (current bindings): `mm6_thief_actor_model_tiers_share_the_native_height`,
  `mm6_barbarian_actor_model_tiers_share_one_size`, `mm6_fighter_chain_actor_model_tiers_share_the_native_height`,
  `mm6_thug_actor_model_tiers_and_mace` (FighterLeath) pass (`review/regression_*.log`).

## Doubtful / left open

- **FighterLeath** stays outside the window in Standard's chase (Walking x1.63-1.95) by the user's choice; a brisker walk
  bound as the run would fix it without running, if wanted.
- **Thief cloak in the sprint**: the kicked heel still shows through the back hem in most samples (79.6 poking vertices
  per sample against the accepted Running's 46.7), and the known 6-10 cm openings between chains show at the back.
  MAW-only clip; a lower swing (0.6) did not help.
- Thief Walk2 is brisk (0.78 s loop, 154 steps a minute, 0.77 m steps): MM6's Rogue wanders at a near-running speed for
  his size (Froude 0.67).
- Thief arm contacts above (the jerkin hem against the forearms) are the model's, slightly more frequent in the faster
  clips.
- FighterLeath: a strap down the back (skinned rigidly to `B_Spine2`) swings out behind the shoulders when the trunk
  leans, as in its accepted `Running`; the sprint leans more.
- FighterChain: the tabard panels follow the thighs (weights), as in its `Running`; they stretch with the longer stride.
- Barbarian jog bob 6.0 % against its Running's 4.4 % (head-bob pass target 4.5 %), inside the 4-7 % range.
- Not run: in-game captures (bindings not applied yet). After `apply_bindings.py`, rerun the four regressions above.
- A rerun of `lod_repair_claude` (Barbarian was in it) or `head_bob_claude` (Barbarian `Running`) must re-graft these
  clips: copy the new source over `work/mm6_<m>_pre_gait.glb` and run `scripts/rebuild.sh <m>`.

## Rebuild

`scripts/rebuild.sh [--sources] [model ...]` composes the exports from `work/mm6_<m>_pre_gait.glb` (or assets_source
commit `a762c96`), `jobs/`, `work/sources/` and `work/thf_cloak_chains.json`, then runs `gait_gate.py` and
`check_winding.py`; it reproduces the installed exports byte for byte. `--sources` extracts the three library loops with
Blender (`scripts/extract_source.py`). Probes: `scripts/probes.sh <m> <export> <old clips> <new clips> [node=prop.glb]`
and `scripts/cloak_poke_probe.py`; filmstrips `scripts/render_review.sh`; viewers `scripts/build_viewers.py`, then
`python3 tools/run_creature_review.py --project level_generation/creatures/mm6_<m>_gait_h01_claude playback` and
`scripts/playback_sheet.py`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h01/export/mm6_<m>.glb --world mm6 --name mm6_<m>.glb`. Rollback:
install `work/mm6_<m>_pre_gait.glb` the same way and drop the bindings.
