# Gait rollout package h17: MM8 pirates, Human Mercenary, Bedraggled Human (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM8 sources
(`assets_source/worlds/mm8/models/`; pre-gait copies `work/mm8_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`,
the git HEAD versions). Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the
input's binary chunk is a byte-identical prefix, only animations appended). No Meshy credits or other spending; the
sources are local library loops (`work/sources/`, copied from `../h06/work/sources/` and
`../../mm8_pirates_gait_claude/work/sources/`; library-derived, never commit). All five are **installed**
(`tools/install_model.py --world mm8`; `work/exports.sha256` = the installed sources). `actors.yml` is not edited
here: [bindings.yml](bindings.yml) is for the coordinator; it binds per descriptor group (tiers differ).

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Pirate Warrior (`mm8_m412`, cutlass + hook) | Sprint: humanoid set Unarmed-Sprint, 0.62 s, 3.5194, 5.68 |
| Pirate Crossbowman (`mm8_m416`, crossbow, quiver) | Sprint: Unarmed-Sprint, 0.65 s, 3.9377, 6.06 · Jog2: Unarmed-Run-Forward, 0.90 s, 2.2534, 2.50 |
| Pirate Mage (`mm8_m420`, peg leg R, open coat, staff) | WalkSlow: Staff-Walk-Slow-WithStaff (his Walk2's source), 1.80 s, 1.0729, 0.60 · Walk3: the same source, 1.25 s, 1.4342, 1.15 |
| Bedraggled Human (`mm8_m620`, unarmed civilian) | Walk2: Relax-Walk-Forward, 1.15 s, 1.2096, 1.05 |
| Human Mercenary (`mm8_m656`, raised sword, scabbard) | Sprint: Unarmed-Sprint, 0.58 s, 4.3848, 7.56 |

Strides are `gait_gate.py`'s trusted measurements (vertices and feet agree; planted soles per side within 2 %,
`review/<m>_probes.txt`).

## Why, per model (targets: `review/mm8_<m>_gate_installed.txt`)

The walk-as-run decision is applied per tier with the brief's rule (walk while the hurried speed is a walking pace,
Froude v^2 / (g * hip height) <= 0.65; hip heights 0.905 / 1.047 / 0.871 / 0.894 / 0.853 m).

- **Pirate Warrior**: Standard chase 2.22-4.00, MAW chase 5.39-6.29 (all six, Wimps included, are fast melee).
  A walked as it ran at 3.15 (Walking x1.84, Froude 1.12) and Wimpy C at 2.79 (x1.63, 0.88): they and Wimpy B (2.50,
  0.70, Walking x1.46) take the installed `Jog` like B/C. Wimpy A (2.22, 0.56) keeps `Walking`. A `Sprint` for MAW.
- **Crossbowman**: MAW chase 5.99-6.15 for A/B/C and Wimpy C: a `Sprint`. Standard chase B/C (2.68 / 2.84, Froude
  0.70 / 0.79) is a run pace: a new `Jog2`, not the installed `Jog` (it limps, bob `uneven` 1.19, and plants the left
  foot 22 deg out on the mesh). A and Wimpy C (2.52, 0.62) keep `Walking`. Wimpy A fled on `Walk2` at x1.61: bound to
  `Walking` (x0.78). Wimpy B unchanged.
- **Pirate Mage** (ranged; MAW keeps his speeds): wandering spans 0.50-1.26 and chasing 1.01-2.51 over the six tiers,
  more than two clips can cover (the pirates pass left A and Wimpy C outside). Two more walks of his own Walk2 source:
  `WalkSlow` for A's wandering (Walk2 becomes A's chase), `Walk3` for B/C's chase (Walk2 x1.72 on B) and Wimpy C's
  wandering (Walk2 x1.61). Wimpy A/B unchanged.
- **Bedraggled Human** (flees at 2.19, Froude 0.55: keeps `Walking` as its run): wandered (1.10) on its 1.64 u/s
  `Walking` at x0.67: a slower `Walk2`.
- **Human Mercenary**: only MAW C's chase failed (Running x1.52 at 8.02): a `Sprint`.

## Gate window sections (all PASSED, floor ok on every descriptor)

Gated per binding group with `scripts/gate_only.py` (q2's; `gait_gate.py` unchanged with its descriptor list limited):

```
Pirate Warrior   (review/m412_gait_gate.txt: run Jog + sprint on all six; Wimpy A: m412_gait_gate_wimpy_a.txt)
  standard A wander Walk2 x1.10  chase Jog x1.11      | maw A chase Sprint x1.03
  standard B wander Walk2 x1.25  chase Jog x1.26      | maw B chase Sprint x1.07
  standard C wander Walk2 x1.40  chase Jog x1.41      | maw C chase Sprint x1.11
  standard Wimpy A wander Walk2 x0.78  chase Walking x1.30 | maw Wimpy A chase Sprint x0.95
  standard Wimpy B wander Walk2 x0.88  chase Jog x0.88     | maw Wimpy B chase Sprint x0.97
  standard Wimpy C wander Walk2 x0.98  chase Jog x0.99     | maw Wimpy C chase Sprint x1.00
Crossbowman      (m416_gait_gate_bc.txt, _a_wc.txt, _wa_wb.txt)
  standard A wander Walk2 x1.17  chase Walking x1.14  | maw A chase Sprint x0.99
  standard B wander Walk2 x1.25  chase Jog2 x1.07     | maw B chase Sprint x1.00
  standard C wander Walk2 x1.32  chase Jog2 x1.13     | maw C chase Sprint x1.02
  standard Wimpy A wander Walk2 x0.81  chase Walking x0.78  (maw the same)
  standard Wimpy B wander Walk2 x0.95  chase Walking x0.93  (maw the same)
  standard Wimpy C wander Walk2 x1.17  chase Walking x1.14  | maw Wimpy C chase Sprint x0.99
Pirate Mage      (m420_gait_gate_a.txt, _bc.txt, _wc.txt, _wa_wb.txt; MAW rows equal Standard's)
  A wander WalkSlow x0.84  chase Walk2 x1.29
  B wander Walk2 x0.86     chase Walk3 x1.17
  C wander Walk2 x0.97     chase Walk3 x1.31
  Wimpy A wander Walk2 x1.18  chase Walking x1.01
  Wimpy B wander Walk2 x1.40  chase Walking x1.20
  Wimpy C wander Walk3 x1.10  chase Walking x1.38
Bedraggled Human (m620_gait_gate.txt) A-C wander Walk2 x1.04  chase Walking x1.34 (both rulesets)
Human Mercenary  (m656_gait_gate.txt)
  standard A wander Walking x1.32  chase Running x0.90 | maw A chase Sprint x1.02
  standard B wander Walking x1.42  chase Running x0.96 | maw B chase Sprint x1.04
  standard C wander Walking x1.50  chase Running x1.01 | maw C chase Sprint x1.06
```

MAW's wander rows (hostile speed, not judged): Mercenary A-C on Walking at the 2x cap (slide 1.08-1.12), Pirate
Wimpy A on Walk2 x1.89, Crossbowman B/C Jog2 x1.21-1.23, A / Wimpy C Walking x1.35, Pirate A-C and Wimpy B/C Jog
x0.95-1.11.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h06/scripts/compose_gait.py` (h16's composer with h02/h04 `raise_arms`, h07 `arm_raise_deg`, h01
`even_bob`, h19 `track_out`/`follow_thighs`, h06 per-side `foot_toe_out_deg`): legs, pelvis and trunk rhythm from the
library loop, two-bone IK, `lock_stance` planted soles on the sprints and Jog2, the integral plant and per-frame
grounding on walks, `stance_foot: Standing`, `foot_smooth`, `even_bob` + `symmetric_drop`; arms, hands, props (cutlass,
crossbow with strings and bolt, quiver, staff, sword, scabbard) from the model's own `Running` (sprints, Jog2) or
`Walking` (walks), phase-aligned. One addition here:

- **`even_ground`** (+ `even_ground_tolerance`, default 5 mm), Mage walks: the per-frame grounding shift made alike on
  both steps. The peg's support sits at another height than the shoe's sole, so plain grounding made a once-per-loop
  limp (`uneven` 0.48-0.51); it is lowered back toward the per-frame grounding only where both supports would leave
  the floor (the floor audit's walking rule). Now `uneven` 0.09-0.10. `rigid_foot: [R]` keeps the peg as the pirates
  pass did.

Per model: **feet** are planted at 5 deg toe-out on the foot *mesh* (`foot_mesh_heading_probe.py`): on these rigs the
foot->toe joint line is 2-10 deg off the mesh, so `foot_toe_out_deg` is per side (Warrior {14.8, 8.5}, Crossbowman
{7.2, 9.0}, Mage L 6.2, Bedraggled {2.4, 8.4}, Mercenary {5.4, 2.1}). Crossbowman Sprint `swing_height` 0.85 (the right
thigh rose 25 mm into the hip quiver at 0.85 m knee drive) and Jog2 0.8. Mage walks `bob` 1.8 / 2.0, Bedraggled Walk2
2.4 (per-frame grounding flattens the bob). Jog2 is the humanoid run at 0.90 s / 2.25 (forward scale 0.66): Mixamo
Jogging dropped the hips 20 cm under `lock_stance`, Relax-Run read 1.5 % bob.

## Phase

Every new clip puts the left foot forward-most at the phase of the model's bound walk (`align`): Warrior and
Crossbowman `Walk2` (0.17-0.19), Mage `Walk2` (0.68), Bedraggled and Mercenary `Walking` (0.20 / 0.17). Installed
pairs already half a loop apart (left as they are): the Crossbowman's `Walking` (0.75) against its `Walk2` (0.17)
(A and Wimpy A/C walk on Walk2 and run on Walking), and the Mage's `Walking` (0.17) against `Walk2` (0.68) (Wimpy A-C:
their walk/run switch, Wimpy C now Walk3 -> Walking).

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all five (`<m>_winding.txt`). `prefix_check.py` ok on all five.
- Foot heading on the mesh, planted L / R (deg toe-out): Warrior Sprint +5.2 / +5.1 (Walk2 +11.8 / -5.4, Jog +27.8 /
  +3.5); Crossbowman Sprint +5.1 / +5.2, Jog2 +5.0 / +4.9 (Walk2 +3.4 / +1.2, Jog +21.7 / +8.3); Mage WalkSlow and
  Walk3 L +4.8 (peg R; Walk2 +2.4); Bedraggled Walk2 +4.9 / +5.0 (Walking +13.2 / +8.0); Mercenary Sprint +5.0 / +5.2
  (Walking +4.3 / +2.6). Joint-line values are in the probes.
- Head bob (bob_audit's measure; `uneven`): Warrior Sprint 5.9 % (0.03); Crossbowman Sprint 6.1 % (0.04), Jog2 5.2 %
  (0.04); Mage WalkSlow 2.3 % (0.10), Walk3 2.5 % (0.09) (his accepted Walk2 1.6 %); Bedraggled Walk2 4.8 % (0.03);
  Mercenary Sprint 6.8 % (0.05).
- Arm and hand gate (`contact_probe.py`, 60 Hz, props as probes): 0 % for arms and props in every new clip, except
  where the accepted clips already are: the Mage's free left hand inside his open coat (WalkSlow 42 %, Walk3 41 %,
  39-40 mm; Walk2 43 %, Walking 52 %, 40 mm), his staff brushing it in WalkSlow (1 %, 5 mm), the Bedraggled's left
  hand at the hip (Walk2 4 % / 19 mm; Walking 4 % / 28 mm). Quiver 0 % in Sprint and Jog2 (Running 4 % / 3 mm).
  Wrist maxima equal the base clips'; arm skin stretch p99 within 0.02 of the base clips'.
- Lowest skin: within 0.03 cm of the floor in every new clip (none below -1 cm). Mage staff foot 54 cm above the floor
  (Walk2 53).
- Playback (`tools/run_creature_review.py check`, `playback`, `shots`: no console errors, every clip switch, normal
  and half speed; looked at): viewers in `../../mm8_<m>_gait_h17_claude/review/`, sheets `review/<m>_playback_sheet.png`,
  side/front shots `review/<m>_*_shots.png`.
- Actor regressions on the installed GLBs with the current (unapplied) bindings (`scripts/regressions.sh`,
  `review/regression_*.log`): `mm8_pirate_actor_models_keep_native_roles`,
  `mm8_female_crossbow_pirate_actor_models_keep_tiers_equipment_and_release`,
  `mm8_pirate_mage_actor_models_keep_palettes_staff_cast_and_simulation`,
  `mm8_mercenary_actor_models_keep_tiers_equipment_and_simulation`, `mm6_mm7_mm8_actor_models_build_every_binding`,
  `every_map_loads_and_builds_its_actor_models` pass (the last one ran before the Crossbowman's reinstall with Jog2;
  its crossbow case was rerun after it). **`mm8_bedraggled_human_actor_models_keep_civilian_roles` fails**:
  it requires exactly six clips (`pBody->clips.size() != 6`, `game/outdoor/HeadlessOutdoorDiagnostics.cpp` near line
  13393); with `Walk2` the body has seven. The diagnostic needs `!= 7` (and may check `findClip("Walk2")`); not edited
  here (engine code). No diagnostic names a walk/run that changes binding: the others only check that `Walking` and
  `Running` exist with their lengths, which they do.

## Doubtful / left open

- Pirate Warrior: the installed `Jog` (pirates pass), now also A's and Wimpy B/C's run, reads 8.3 % head bob and plants
  its left foot 28 deg out on the mesh; its Walk2 plants the right foot 5 deg in. Accepted clips, not changed here.
- Crossbowman Jog2 has a short, quick stride for her long legs (forward scale 0.66 of the library run: knees lift high).
  A and Wimpy C keep walking at 2.52 (Froude 0.62, at the rule's edge).
- Pirate Mage: Wimpy C flees at 2.51 (Froude 0.74) on his brisk `Walking` at x1.38: by the rule a run pace, but his
  only run, the pirates pass's `Jog` (1.59 u/s), would play x1.58, and a faster peg-legged jog in an open coat was left
  out. WalkSlow and Walk3 bob 2.3-2.5 % (below the 3-5 % walk guide; his accepted Walk2 is 1.6 %).
- Human Mercenary C wanders on its unchanged `Walking` at x1.50 (the window's edge); MAW's hostile wandering plays it
  at the 2x cap (not judged; a Walk2 near 2.4 u/s would cover both).
- Walk/run switches change the foot heading where the installed clips plant wider (Warrior Jog, Crossbowman Jog).

## Shared tools

No problem found in `claude_shared/`. `gait_gate.py --set` applies to every descriptor; tiers with different bindings
were gated with `scripts/gate_only.py` (copied from `../q2/scripts/`).

## Rebuild

`scripts/rebuild.sh [m412 m416 m420 m620 m656]` composes the exports from `work/mm8_<m>_pre_gait.glb` and `jobs/` and
checks winding and prefix; it reproduces the installed sources byte for byte (`work/exports.sha256`). Gates: the
`gate_only.py` / `gait_gate.py` lines whose outputs are in `review/` (the `--set` values are in each file's last
line). Probes: `scripts/probes.sh <m> export/mm8_<m>.glb <old clips> <new clips> [node=prop.glb ...]`,
`scripts/foot_mesh_heading_probe.py`, `scripts/prop_low_probe.py`, `scripts/uneven_probe.py`; viewers
`scripts/build_viewers.py <m> <export> <title> <old> <new> [node=prop.glb ...]`, then `python3 tools/run_creature_review.py
--project level_generation/creatures/mm8_<m>_gait_h17_claude playback`, `scripts/playback_sheet.py`, `scripts/shots_strip.py`;
regressions `scripts/regressions.sh`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h17/export/mm8_<m>.glb --world mm8 --name mm8_<m>.glb`. Rollback: install
`work/mm8_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or reduction rerun on these
models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
