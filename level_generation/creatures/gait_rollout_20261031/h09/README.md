# Gait rollout package h09: MM7 Skeleton Warrior, Wight, Lich, Ghoul, Zombie (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM7 sources
(`assets_source/worlds/mm7/models/`; pre-gait copies `work/mm7_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending; sources are local library loops
(`work/sources/`, library-derived, never commit). All five are **installed** (`tools/install_model.py --world mm7`);
`actors.yml` is not edited here: [bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Skeleton Warrior A-C (`mm7_m398`, sword, arrows) | Jog: humanoid set Unarmed-Run-Forward, 0.74 s, 2.7115, 3.66 · Sprint: Unarmed-Sprint, 0.60 s, 3.7857, 6.31 |
| Wight A-C (`mm7_m430`, floor-length robe, dagger) | Jog: Unarmed-Run-Forward, 0.70 s, 2.399, 3.43 · Sprint: Unarmed-Sprint, 0.56 s, 3.795, 6.78; installed Walking rebound at 1.82 (was 1.366) |
| Lich A-C (`mm7_m270`, chain skirt, staff in the left hand) | Walk2: Mixamo Walk (its own walk's source), 1.10 s, 1.7572, 1.60 · Jog: humanoid set Staff-Run-Forward, 0.70 s, 2.2601, 3.23 |
| Ghoul A-C (`mm7_m470`, unarmed) | Sprint: Unarmed-Sprint, 0.60 s, 3.9194, 6.53 |
| Zombie A-C (`mm7_m438`, right stump, held forearm) | Walk2: Mixamo Orc Walk, 1.20 s, 1.6091, 1.34 · Jog: Unarmed-Run-Forward, 0.80 s, 2.2022, 2.75 · Sprint: Unarmed-Sprint, 0.60 s, 3.5625, 5.94 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree), except the Wight (below).

## Why these clips (targets from `gait_gate.py`, model units/s; `review/<m>_targets.txt`)

- **Skeleton Warrior**: wander 1.84-2.01 fits Walking (x1.11-1.21); Standard chase 3.68-4.02 played Running (2.45) at
  x1.50-1.64, MAW chase 6.31-6.86 at the 2x cap. Jog + Sprint.
- **Wight**: Standard chase 3.23-3.95 played Running at x1.32-1.61, MAW chase 7.01-7.37 at the cap. Jog + Sprint. The
  gate also failed its installed Walking binding (1.366: the hem's vertex stride 0.43 and the foot joints' 1.82 both
  disagree with it); rebound at the foot-joint stride, so the wander plays Walking at x0.89-1.09.
- **Lich**: wander 1.54-1.88 played Walking (2.12) at x0.73-0.89 (tier A below the window); chase 3.08-3.76 (Froude
  ~1.1: a run) Running at x1.26-1.53. MAW leaves the speeds unchanged (no sprint). Walk2 + Jog.
- **Ghoul**: Standard fits (Walking x0.80-1.00, Running x1.14-1.42); MAW chase 6.64-6.99 at the cap. Sprint only.
- **Zombie**: wander 1.28-1.60 played its 0.82 u/s stagger (Walking (5)) at x1.56-1.95; Standard chase 2.56-3.20
  Running at x1.31-1.64; MAW chase 6.08-6.39 at the cap. Walk2 + Jog + Sprint.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Skeleton W.  standard A wander Walking x1.11  chase Jog x1.00   | maw A chase Sprint x1.09
             standard B wander Walking x1.17  chase Jog x1.05   | maw B chase Sprint x1.04
             standard C wander Walking x1.21  chase Jog x1.10   | maw C chase Sprint x1.00
Wight        standard A wander Walking x0.89  chase Jog x0.94   | maw A chase Sprint x1.03
             standard B wander Walking x0.99  chase Jog x1.05   | maw B chase Sprint x1.06
             standard C wander Walking x1.09  chase Jog x1.15   | maw C chase Sprint x1.09
Lich         standard/maw A wander Walk2 x0.96  chase Jog x0.95
             standard/maw B wander Walk2 x1.07  chase Jog x1.06
             standard/maw C wander Walk2 x1.18  chase Jog x1.17
Ghoul        standard A wander Walking x0.80  chase Running x1.14 | maw A chase Sprint x1.02
             standard B wander Walking x0.90  chase Running x1.28 | maw B chase Sprint x1.04
             standard C wander Walking x1.00  chase Running x1.42 | maw C chase Sprint x1.07
Zombie       standard A wander Walk2 x0.95  chase Jog x0.93     | maw A chase Sprint x1.02
             standard B wander Walk2 x1.07  chase Jog x1.05     | maw B chase Sprint x1.05
             standard C wander Walk2 x1.19  chase Jog x1.16     | maw C chase Sprint x1.08
```

MAW's wander rows (not judged): Skeleton Jog x0.86-0.94, Wight Jog x1.02-1.07, Ghoul Running x1.35-1.42, Zombie Jog
x1.10-1.16.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h21/scripts/compose_gait.py` (h16's composer with h02's `raise_arms`, h07's `arm_raise_deg` window,
h01's `even_bob`, h19's `track_out`). Legs, pelvis and trunk rhythm from the library loop, two-bone IK, `lock_stance`
planted soles on jogs and sprints, the integral plant on walks, `stance_foot: Standing` with `foot_toe_out_deg: 5`,
`foot_smooth`, floor lift; arms, hands, props from the model's own clip (`base`: Running for jogs and sprints, Walking
for walks), phase-aligned to Walking. Additions here (all opt-in job keys):

- **`soles_feet_only`** (Lich Walk2): the floor and plant passes took every vertex below 6 cm in Standing for a sole,
  which on the Lich is the chain-skirt hem; the integral plant then drove the ankles back and forth (the gate measured
  1.34 for a 1.76 stride). Now only vertices dominated by foot or toe joints (`"plant"`: only for the plant pass).
- **`ground_all`** (Lich Walk2): the floor fix's ground-loop on the new clip: everything under `B_Pelvis` shifted per
  sample so the lowest vertex is on the floor. The Lich's skinned skirt hem dips 2-6 cm under the floor at heel strike
  (85 % leg weights); its accepted Walking keeps the hem on the floor with the shoes up to 5 cm above it, as now.
  `ground_all: "lift"` (Wight) only lifts where something is under the floor, alike on both steps, smoothed
  (`ground_all_sigma` 4), so runs keep their flight.
- **`sole_joints`** (Wight): the Wight has no foot geometry (a closed robe to the floor over hidden legs); virtual
  soles are the ankle and toe joints lowered by their Standing heights, so the hidden feet are planted and slide at
  stride / length, which is what the gate's foot-joint measurement reads.
- Per model: Skeleton Jog lifts the sword arm 18 deg around phase 0.47 (`arm_raise_window` [0.47, 0.25], `arm_out_deg`
  R 6; the blade met the right thigh by 26 mm); Lich Jog `swing_height` 0.5 (a robe-safe low knee: at 1.0 the chain
  skirt split between the legs), staff arm out 8 deg (the staff foot touched the hem), Walk2 `bob` 0.3, staff arm out 3;
  Wight Jog/Sprint right arm out 5 / 9 deg (its sleeve met the robe flank by 25 mm); Zombie Walk2 carry arm out 6 deg (the
  Orc Walk's knee met the held forearm by 38 mm), Jog lean 4-8 deg; Ghoul Sprint: the composer's skin-normal arm
  clearance (9.5 / 12 deg).

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase: Skeleton 0.17 (installed Running
0.23), Wight 0.17 (0.23), Lich 0.67 (Running 0.73), Ghoul 0.18 (0.23), Zombie 0.36 (Running 0.23).

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all five (`review/<m>_winding.txt`). `prefix_check.py` ok
  (`review/<m>_probes.txt`).
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R, swing range):
  - Skeleton Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5); installed Walking +18.8 / +14.5, Running
    +17.6 / +36.4
  - Wight (hidden feet) Jog +5.0 / +4.9, Sprint +5.1 / +4.9; Walking +3.9 / -1.0, Running +6.5 / +23.2
  - Lich Walk2 +2.4 / +3.9 (+0.3..+15.8), Jog +5.0 / +4.9 (-5.7..+6.5); Walking -2.3 / +4.4, Running +21.4 / +6.0
  - Ghoul Sprint +5.1 / +4.9 (-4.3..+6.5); Walking +15.5 / +10.3, Running +17.0 / +32.9
  - Zombie Walk2 +4.3 / +2.2 (swing +6.7..+19.5), Jog +5.0 / +4.9, Sprint +5.1 / +4.9; Walking +10.5 / +4.3, Running
    +12.4 / +35.5
- Head bob (bob_audit's measure; `uneven`): Skeleton Jog 4.2 % (0.04), Sprint 4.9 % (0.04); Wight Jog 4.0 % (0.03),
  Sprint 6.3 % (0.23); Lich Walk2 4.4 % (0.10), Jog 5.6 % (0.11); Ghoul Sprint 4.3 % (0.05); Zombie Walk2 3.9 % (0.33),
  Jog 5.5 % (0.03), Sprint 4.2 % (0.05).
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/finger/prop inside legs or trunk): 0 % in every new clip
  except Ghoul Sprint 3 % / 4 mm and 3 % / 2 mm (its Running 4 % / 6 mm), Zombie Sprint carry arm 3 % / 2 mm (Running
  2 % / 2 mm), Wight free (left) sleeve 21-24 % / 31-37 mm against the robe flank, as its accepted Running (24 % /
  33 mm; Walking 75 % / 39 mm: an open skinned robe, proximity). Props: sword, staff, dagger, held forearm 0 %. The
  Skeleton's arrows are stuck in the body by design (49 / 32 %, Running 76 %). Wrist maxima equal the base clips'. Arm
  skin stretch p99 within 0.04 of the base clip's (the Wight's robe armpit 9-10x max as Running's 9.6x).
- Lowest skin within 0.2 cm of the floor in every new clip (none below -1 cm).
- Planted stride per side (`stride_probe.py`) within 1 % of the binding except the Lich Walk2's right shoe (1.636 vs
  1.757; the shoes are lifted under the grounded hem) and the Wight (no sole geometry; the gate's foot-joint strides
  are bound).
- Playback (`tools/run_creature_review.py check` and `playback`: no console errors, normal and half speed, looked at):
  viewers in `../../mm7_<m>_gait_h09_claude/review/` (the wrapper needs a direct child of `creatures/`), sheets
  `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/`.
- Headless actor regression on the installed GLBs (current bindings; the suite has no MM7 case for these five):
  `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models, 0 failed;
  `review/regression_*.log`). Rerun after `apply_bindings.py`.

## Doubtful / left open

- **Wight**: no foot geometry, so its strides are the foot-joint measurements, set explicitly (`--set`); the gate
  cannot trust the hem's vertex measurement on any of its clips. Rebinding its installed Walking (1.366 -> 1.82) slows
  the walk's playback by a quarter; it plays x0.89-1.09 now. The robe-hidden sprint reads as a forward-leaning glide
  with the hem lifting briefly in flight.
- **Ghoul**: only MAW's chase was out of the window; its installed Running's stride is not trusted by the gate (vertices
  1.86 / feet 1.63 against the bound 1.8) and Standard C's chase plays it at x1.42, near the top. A Jog would settle
  both; not added since the gate passes.
- **Zombie**: the new walk is a lumbering Orc Walk rather than the installed drunk stagger (Walking (5) as a source
  at the wander pace broke the pelvis: 44 % bob); Walk2 `uneven` 0.33 is slightly above the 0.3 guide. The jog and
  sprint are plain library runs leaned forward (the Mixamo Zombie Run/Running are crouched with a 20 cm pelvis drop
  on this body). Its installed Walking and Running are 0.13 of a loop apart (left foot forward-most 0.36 vs 0.23); new
  clips follow the walk.
- **Lich**: Walk2's shoes lift under the grounded hem like the accepted Walking; the Jog's knee is kept low for the
  skirt (`swing_height` 0.5).
- New clips plant at 5 deg toe-out while the accepted runs plant at 12-36 deg; the heading changes at walk/run switches.

## Shared tools

No problem found in `claude_shared/` tools. Notes: `gait_gate.py` cannot bind a body without foot geometry from a
trusted measurement (the Wight: `--set` needed; the floor-length robe's hem is what touches the floor). The package
composer's sole selection (vertices below 6 cm in Standing) picks up skirt hems; see `soles_feet_only` above.

## Rebuild

`scripts/rebuild.sh [--sources] [m398 m430 m270 m470 m438]` composes the exports from `work/mm7_<m>_pre_gait.glb`
and `jobs/`, then runs `gait_gate.py` (with the Wight's explicit strides) and `check_winding.py`; it reproduces the
installed exports (`work/exports.sha256`). `--sources` extracts the library loops with Blender
(`scripts/extract_source.py`); the other loops were copied from `../h21/work/sources/`. Probes:
`scripts/probes.sh <m> <export> <old clips> <new clips> [node=prop.glb]`, `scripts/gate_probe.py` (the gate's stride
and floor measurements for quick iterations), `scripts/prop_where.py` (when and where a prop or forearm is inside);
filmstrips `scripts/render_review.sh`; viewers `scripts/build_viewers.py <m> <export> <title> <old> <new>
[node=prop.glb]`, then `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_<m>_gait_h09_claude
playback` and `scripts/playback_sheet.py <m> <clips>`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h09/export/mm7_<m>.glb --world mm7 --name mm7_<m>.glb`. Rollback:
install `work/mm7_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or reduction rerun
on these models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
