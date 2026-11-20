# Gait rollout package h16: MM8 Lizardman Peasant, Dragon Hunter, Triton, Lizardman Warrior (2026-10-31)

Brief: [../README.md](../README.md). Each model gets two new in-place locomotion clips appended to its installed source
(`assets_source/worlds/mm8/models/`, the pre-gait copies are `work/mm8_<m>_pre_gait.glb` = assets_source commit
`d4c87ca`): a run for Standard's chase (Wimps: flight) and a `Sprint` for MAW's chase. Existing clips, meshes, skins and
materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a byte-identical prefix, every input
accessor, buffer view, node, mesh, skin, material and animation is unchanged, only animations are appended). No Meshy
credits, no paid actions: the sources are humanoid-set library loops (`anim_library/`, never committed).
All four are installed (`tools/install_model.py --world mm8`); `actors.yml` is not edited here:
[bindings.yml](bindings.yml) is for the coordinator.

| Model | Run clip: source, length, stride, speed | Sprint: source, length, stride, speed |
|---|---|---|
| Lizardmen Male (Peasant) A/B/C, `mm8_lizardman_peasant.glb` (Meshy rig) | `Run`: Relax-Run-Forward, 0.74 s, 2.7555, 3.72 u/s | Unarmed-Sprint, 0.60 s, 4.2454, 7.08 u/s |
| Dragon Hunter A/B/C, `mm8_m456.glb` | `Jog`: Unarmed-Run-Forward, 0.72 s, 3.2029, 4.45 u/s | Unarmed-Sprint, 0.60 s, 4.2567, 7.09 u/s |
| Triton A/B/C, `mm8_m576.glb` | `Jog`: Unarmed-Run-Forward, 0.74 s, 2.7566, 3.73 u/s | Unarmed-Sprint, 0.62 s, 3.7540, 6.05 u/s |
| Lizardmen Warrior A/B/C, `mm8_m404.glb` | `Jog`: Unarmed-Run-Forward, 0.80 s, 2.6519, 3.31 u/s | Unarmed-Sprint, 0.62 s, 4.4893, 7.24 u/s |

Strides are `gait_gate.py`'s trusted measurement (planted soles agree: `review/<m>_probes.txt`). Walks stay. The
Dragon Hunter's and Triton's `Running` and the Warrior's walk-as-run are no longer bound for locomotion (kept in the GLB).
The Peasant is a fleeing Wimp: its Standard flight (3.47-3.99 u/s) was played by `Walk` at x2.5-2.9, not a walking
pace, so it gets a plain civilian run (the walk-as-run decision covers bodies whose hurried speed is a walking pace).

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Lizardman Peasant  standard A wander Walk x1.26  chase Run x0.93 | maw A chase Sprint x0.98
                   standard B wander Walk x1.35  chase Run x1.00 | maw B chase Sprint x1.00
                   standard C wander Walk x1.44  chase Run x1.07 | maw C chase Sprint x1.02
Dragon Hunter      standard A wander Walking x1.17  chase Jog x0.91 | maw A chase Sprint x1.01
                   standard B wander Walking x1.29  chase Jog x1.00 | maw B chase Sprint x1.04
                   standard C wander Walking x1.42  chase Jog x1.10 | maw C chase Sprint x1.07
Triton             standard A wander Walking x1.26  chase Jog x1.00 | maw A chase Sprint x1.05
                   standard B wander Walking x1.21  chase Jog x0.96 | maw B chase Sprint x0.98
                   standard C wander Walking x1.30  chase Jog x1.03 | maw C chase Sprint x0.95
Lizardman Warrior  standard A wander Walking x0.81  chase Jog x0.89 | maw A chase Sprint x0.99
                   standard B wander Walking x0.92  chase Jog x1.00 | maw B chase Sprint x1.02
                   standard C wander Walking x1.02  chase Jog x1.12 | maw C chase Sprint x1.04
```

(MAW's wander rows are its hostile speed, not judged: Dragon Hunter A x2.00 and Triton B/C x1.94-2.00 on Walking.)

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../../mm6_sprint_humanoids_claude/scripts/compose_gait.py` (legs, pelvis and trunk rhythm from the library
loop, two-bone IK, `lock_stance` planted soles, `stance_foot: Standing` with `foot_toe_out_deg: 5`, `foot_smooth`,
`align` to the model's walk, floor lift). Every clip strikes with the same foot at the same phase as the model's walk
(left foot forward-most at 0.17 / 0.17 / 0.19 / 0.76 like Walking / Walk); the Dragon Hunter's and Triton's installed
`Running` were already within 0.06 of their walks. Additions in this package:

- **Meshy rig** (`gaitlib.alias_nodes`): the Peasant's `Hips`, `LeftUpLeg`, ... joints are read under `B_*` names in
  memory and restored before writing; the probes read them the same way.
- **`arms_from_source`** (Peasant): its only locomotion clip is a walk with straight swinging arms, so the arms come from
  the library loop: upper arm along the source's shoulder-elbow direction (least rotation from Standing), forearm
  hinged from where the upper arm carries it, Standing's wrist, fingers from Walk. `elbow_extra_deg` (Run 40, Sprint 20)
  bends the elbow further and `abduct_deg` (L 20, R 32) turns the swing out: the long lizard arms otherwise carried the
  hands into the tunic at the hips or the thumb into the chest. `gain` 0.8 / 0.9 calms the swing.
- **`symmetric_drop`** (Peasant run and sprint, Dragon Hunter sprint): the pelvis is lowered alike on both steps where
  a leg would overreach. The asymmetric sources lowered only one step: head bob `uneven` 0.95 / 0.69, now 0.11 / 0.10.
- **`grip_lift`** (Warrior): the two-handed guard of the accepted Walking sat where a run's knee rises. Both upper arms
  turn by one constant angle about the line through both shoulder joints (Jog 7.8 deg, Sprint 10.6 deg), so arms and
  sword move as one rigid piece and the grip is exactly the walk's. With **`swing_height`** (0.8 / 0.75: a lower foot
  recovery, the knee rises less) the guard only needs that small lift; without it 27-37 deg (a raised-sword run).
- **`loincloth`** (Warrior): the walk's leading-thigh rule (`../../mm8_m404/3d_claude/scripts/finish_walk.py`,
  reproduced to 0.0004 deg on the installed Walking), clamp 60 + 8 deg (the walk's 80 put the flap horizontal).
- **`clear_sides`** (Dragon Hunter: R only): the sword forearm rests 39 mm into the belt in the accepted Standing, so
  turning it out (41 deg) only spoiled the accepted carry; the free arm is cleared as before.
- **Triton sprint lean**: the trident points forward-down from the left hand; the pilot's chest lean (Spine2 16 deg)
  drove its tines 8.6 cm into the floor. Spine1/Spine2 lean 9 / 6 deg keeps them 6.9 cm above it (Running 22.7 cm).
- Warrior trunk: spine weights 0.6 of the source (the source's shoulder counter-rotation swung the two-handed sword).

## Checks (`review/`)

- `<m>_gait_gate.txt` PASSED; `<m>_winding.txt` 0 inverted closed parts on all four.
- Foot heading (`foot_heading_probe.py`, toe-out from +Z): planted L / R, swing range
  - Peasant Run +5.1 / +5.1 (swing -2.3..+8.4), Sprint +5.1 / +4.9 (-6.4..+6.5); its Walk +13.2 / +12.4 (swing to +38.7)
  - Dragon Hunter Jog +5.0 / +4.9 (-5.3..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5); Walking +2.3 / -1.9
  - Triton Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5); Walking +8.1 / -7.0
  - Warrior Jog +5.0 / +5.0 (-5.2..+7.4), Sprint +5.2 / +5.0 (-6.4..+6.5); Walking -6.9 / +4.1
- Head bob (bob_audit's measure, `bob_probe.py`): Peasant Run 4.2 % / Sprint 6.4 %; Dragon Hunter 6.3 / 6.3; Triton
  5.0 / 4.8; Warrior 5.0 / 5.7 (target 4-7).
- Arm and hand gate: no forearm, hand, finger or prop inside legs or trunk in any new clip except where the accepted
  clips already are (contact probe, 60 Hz, per side): Dragon Hunter's sword forearm on the belt (Jog 38 mm 61 %,
  Sprint 29 mm 59 %; Running 30 mm 58 %, Standing 39 mm 100 %), Peasant Sprint one 2 mm brush (3 %). Wrist maxima equal
  the base clips' (105 / 77 / 96 deg); Peasant 44 deg (Walk 38). Arm skin stretch equal to the base clips' except the
  Peasant (below). Two-hand grip of the Warrior unchanged by construction.
- Props: Dragon Hunter sword lowest 63 cm, Triton trident 6.9 cm, Warrior sword 89 cm above the floor
  (`prop_low_probe.py`). Warrior loincloth inside the legs: Jog 15 % 19 mm, Sprint 5 % 5 mm (Walking 85 % 19 mm).
- Lowest skin: 0.00 cm on every new clip (the Warrior's first jog drove the tail tip 2 cm under; fixed with the swing).
- Phase: `review/<m>_probes.txt`; planted stride per side within 1 % of the binding (Peasant Run L 2.784 / R 2.752).
- Playback review with `tools/run_creature_review.py` (check: no console errors; playback at normal and half speed),
  viewers in `../../mm8_<m>_gait_h16_claude/review/` (the wrapper needs a direct child of `creatures/`), sheets
  `review/<m>_playback_sheet.png`; filmstrips `review/iter/`.
- Actor regressions on the installed GLBs (current bindings): `mm8_dragon_hunter_actor_models_keep_native_roles`,
  `mm8_lizardman_peasant_actor_model_keeps_native_roles`,
  `mm8_lizardman_warrior_actor_models_keep_tiers_sword_and_native_roles`,
  `mm8_triton_actor_models_keep_tiers_trident_and_simulation` pass (`review/regression_*.log`).

## Doubtful / left open

- Peasant arm stretch: p99 1.55-1.63 (Walk 1.43), max 4.84x on a 4.5 mm armpit edge weighted to `LeftArm` and
  `LeftShoulder` and 4.8x on back edges weighted to spine, pelvis and clavicle (Walk 2.59x). Bent running elbows and the
  sprint lean on a Meshy rig that never bent them; inside the tunic and armpit, not seen at game distance.
- Peasant arms are a generic library run (hands pumping at chest height, claws open), not the walk's style.
- The Dragon Hunter's sword forearm keeps its accepted belt contact (above).
- The Warrior's guard is raised by 8-11 deg in the run and sprint (constant, no pumping); its jog and sprint feet
  recover lower than the source's (`swing_height`).
- Not run: in-game captures (bindings not applied yet). After `apply_bindings.py`, rerun the four regressions above.
- `lod_repair_claude` (the Peasant was its pilot) and `head_bob_claude` (Dragon Hunter) rebuilt these sources before;
  a rerun of either must re-graft the clips: rebuild from the new source with `scripts/rebuild.sh` after copying it
  over `work/mm8_<m>_pre_gait.glb`.

## Rebuild

`scripts/rebuild.sh [--sources] [model ...]` composes the exports from `work/mm8_<m>_pre_gait.glb` (or assets_source
commit `d4c87ca`) and `jobs/`, then runs `gait_gate.py` and `check_winding.py`; it reproduces the installed exports byte
for byte. `--sources` extracts the three library loops with Blender (`scripts/extract_source.py`) into `work/sources/`.
Probes: `scripts/probes.sh <m> <export> <old clips> <new clips> [node=prop.glb]`, `cloth_probe.py`, `prop_low_probe.py`;
filmstrips `scripts/render_review.sh`; viewers `scripts/build_viewers.py`, then `python3 tools/run_creature_review.py
--project level_generation/creatures/mm8_<m>_gait_h16_claude playback` and `scripts/playback_sheet.py`.
Install: `python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h16/export/mm8_<m>.glb
--world mm8`. Rollback: install `work/mm8_<m>_pre_gait.glb` the same way and drop the bindings.
