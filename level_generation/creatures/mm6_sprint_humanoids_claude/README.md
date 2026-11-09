# MM6 Ogre and KnightPlate: Jog and Sprint (2026-10-31)

Pilot for the engine's optional third locomotion clip (`animation.sprint` + `sprint_stride_length`, chosen by
`actorModelGait`, default playback-rate ceiling 2x). Two in-place clips are appended to each installed GLB: `Jog`
(the new run, for Standard chasing) and `Sprint` (for MAW chasing at Spd/2+300, doubled while pursuing). Every
existing clip is untouched: the old animations sample identically and the binary chunk of the input is a byte-identical
prefix of the export. No Meshy credits, no paid actions; sources are local library loops. `actors.yml` is not edited
here (bindings below are for the coordinator).

| Model | Jog: source, length, stride, speed | Sprint: source, length, stride, speed |
|---|---|---|
| Ogre A/B/C (`mm6_ogr.glb`) | humanoid set Unarmed-Run-Forward, 0.72 s, 2.9936, 4.16 u/s | humanoid set Unarmed-Sprint, 0.62 s, 4.2108, 6.79 u/s |
| KnightPlate A/B/C (`mm6_kni.glb`) | humanoid set Unarmed-Run-Forward, 0.74 s, 3.3738, 4.56 u/s | humanoid set Unarmed-Sprint, 0.60 s, 4.1581, 6.93 u/s |

Bindings that passed `gait_gate.py` (every descriptor of the model; strides are the gate's own trusted measurement,
vertices and foot joints agree):

- Ogre A/B/C: `run: Jog`, `run_stride_length: 2.9936`, `sprint: Sprint`, `sprint_stride_length: 4.2108`
- KnightPlate A/B/C: `run: Jog`, `run_stride_length: 3.3738`, `sprint: Sprint`, `sprint_stride_length: 4.1581`

Walk bindings stay (`Walking`, 1.68 / 1.767). `Running` is no longer bound for locomotion but is kept in the GLB.

## Biomechanics (why these numbers)

A sprint is faster by a longer stride, not a quicker one: Ogre jog to sprint is +40 % stride and +16 % cadence
(0.72 s to 0.62 s per loop), KnightPlate +23 % stride and +23 % cadence (0.74 to 0.60 s). The sprint has a longer
flight (stance per foot 0.20-0.25 of the loop), a forward trunk lean (Ogre 22.6 deg, KnightPlate 15.2 deg vs
9.6 / 7.3 deg in the jog; measured pelvis-to-neck) and a stronger free-arm drive (left arm swing x1.35 about its mean;
the sword arm keeps its accepted swing). The Ogre's sprint is lower than its jog (pelvis 0.886 vs 0.965 m): a heavy,
powerful stride. Both jog and sprint come from the same humanoid-set family so a switch keeps the same style.
Rejected: Mixamo Running (4) for the jog (the KnightPlate's arms then entered the tassets by 34 mm, 24 deg clearance
needed, and the Ogre ran bent-kneed), Mixamo Sprint for the Ogre (its natural stride is 1.37x short of the target:
the pelvis dropped 57 cm).

## Phase

The engine shares one gait phase across walk, run and sprint. The accepted `Walking` and `Running` of both models are
half a loop apart (left foot forward-most at 0.75 vs 0.28), so a walk/run switch scissored the legs before this work.
The new clips are aligned with `Walking` (left foot forward-most at 0.75, right at 0.26-0.29, `align` in the jobs),
so walk, jog and sprint switch in phase.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

Adapted from `../mm8_pirates_gait_claude/` (same `B_*` skeleton): legs, pelvis and trunk rhythm from the library loop
retargeted with the leg-length ratio and analytic two-bone IK; arms, hands, fingers, twist bones and the sword's node
from the model's own `Running`, phase-aligned on the left foot; floor grounding; arm clearance. Additions:

- `align`: the loop starts so the left foot is forward-most at the reference clip's phase (`Walking`).
- `lock_stance`: over each source contact the ankle slides back at exactly stride/length through its mid-contact
  point, at Standing's ankle height, with Standing's flat foot (6-sample smoothstep in/out). The pirates' integral
  plant correction could not settle the sprint's short contacts (right sole 4.8 vs 4.2) and the Ogre's few-vertex
  claw soles (`plant_min_vertices: 1`); with the lock both sides plant at the binding stride (`final_probes.txt`).
- `stance_foot: Standing` + `foot_toe_out_deg: 5`: the planted foot is Standing's (flat) instead of the base run's,
  turned about the vertical so its toe points 5 deg out from the travel direction (+Z). Standing's feet are turned out
  about 27 deg (and yawed 4-7 deg off +Z as a pair), which the first install copied onto every planted foot: duck feet
  in game (fixed 2026-10-31, see "Foot heading" below). The swing foot is the source's roll about this flat foot, so
  it follows: no outward flare in flight. The accepted `Walking` plants along +Z (toe-out 0-6 deg).
- `bend_toes`: where a toe-dominated vertex would go under the floor at toe-off, the toe dorsiflexes by the least
  smoothed angle (the Ogre's claws pointed 3.6 cm into the floor in an earlier jog with a Mixamo source; 0 deg in the
  installed clips; harmless on the KnightPlate's rigid sabaton, which has no toe-dominated skin).
- `foot_smooth`: periodic quaternion blur of the foot roll (the humanoid-set sprint snaps its feet: 25.6/21.5 deg per
  1/48 s step/second difference in the source; ours 25.9/12.9 and 31.9/15.9 on the Ogre).
- `side_gain`, `lean_deg`: free-arm swing gain about its loop mean (clavicle half of it) and an extra world-space
  forward pitch per trunk bone, neck and head counter-pitched so the head looks ahead (head pitch -0.5 / +3.6 deg).
- `clear_props`: the sword is a probe in the arm clearance; the Ogre's accepted `Running` already puts the sword's
  guard 17 mm into its chest (6 % of samples), so the jog and sprint turn the right upper arm out by up to 9 deg there.
- `bob` 0.2-0.3: the humanoid-set loops bob 10-15 % of head height; scaled to the playbook's run range.

## Foot heading (fix after the first in-game look, 2026-10-31)

The user saw the Ogre's sprint feet "broken to the sides". Toe-out in degrees from the travel direction +Z
(`scripts/foot_heading_probe.py`: the foot's own pitch axis, defined in the swing too; planted = foot joint in its
lowest 25 %):

| Clip | Ogre before: planted L / R, swing | Ogre after | Knight before | Knight after |
|---|---|---|---|---|
| Walking (accepted) | +0.1 / +1.2 | | +5.0 / +6.4 | |
| Jog | +22.7 / +30.2, swing -19.5..+30.2 | +5.0 / +4.9, swing -5.3..+7.4 | +21.1 / +34.1, swing -21.7..+34.1 | +5.0 / +4.9, swing -5.2..+7.4 |
| Sprint | +22.8 / +30.3, swing -25.1..+29.9 | +5.1 / +5.0, swing -6.4..+6.5 | +21.2 / +34.2, swing -28.5..+33.7 | +5.1 / +5.0, swing -6.4..+6.5 |

The coordinator's `foot_yaw.py` (foot->toe against Standing's foot bisector, which is itself 4 deg (Ogre) and 7 deg
(Knight) off +Z) reads the same feet as Ogre Jog -9.0 / +1.4, Sprint -9.4 / +1.4 (before -27.1 / +27.9, -27.6 / +28.0)
and Knight Jog -11.8 / -1.4, Sprint -12.1 / -1.2 (before -28.3 / +28.9, -28.9 / +29.7): the same 5 deg toe-out per
foot about +Z, offset by that bisector; its Walking reads -4.6 / -1.8 and -7.2 / -4.6 for the same reason. Front
filmstrips: `review/feet/<m>_before_Sprint.png`, `review/feet/<m>_after_{Jog,Sprint}.png`. Strides, phases, bob, arm
and contact probes are unchanged (a constant yaw of the flat foot; the ankle paths are the same).

## Gates (all on the installed exports; outputs in `review/`)

`gait_gate.py` PASSED for both (`review/ogr_gait_gate.txt`, `review/kni_gait_gate.txt`). Window section:

```
Ogre
  standard Ogre A          wander: Walking x0.99  chase: Jog x1.00
  standard Ogre B          wander: Walking x1.07  chase: Jog x1.08
  standard Ogre C          wander: Walking x1.16  chase: Jog x1.17
  maw      Ogre A          wander: Walking x1.73  chase: Sprint x1.07
  maw      Ogre B          wander: Jog x0.90      chase: Sprint x1.10
  maw      Ogre C          wander: Jog x0.92      chase: Sprint x1.12
KnightPlate
  standard KnightPlate A   wander: Walking x1.06  chase: Jog x1.03
  standard KnightPlate B   wander: Walking x1.13  chase: Jog x1.10
  standard KnightPlate C   wander: Walking x1.13  chase: Jog x1.10
  maw      KnightPlate A   wander: Jog x0.87      chase: Sprint x1.15
  maw      KnightPlate B   wander: Walking x1.70  chase: Sprint x1.08
  maw      KnightPlate C   wander: Walking x1.54  chase: Sprint x0.98
```

(MAW's wander rows are its hostile speed, which the gate does not judge; calm wandering keeps Spd.)
Stride: trusted on all clips. Floor: ok on every descriptor.

- `check_winding.py`: 0 inverted closed parts on both exports (`review/*_winding.txt`).
- Head bob (bob_audit's measure applied to the candidate, `scripts/bob_probe.py`): Ogre Jog 6.0 %, Sprint 6.7 %;
  KnightPlate Jog 5.4 %, Sprint 6.4 % (run range 4-7 %, the installed Runnings 6.5 %).
- Arm and hand gate (`review/final_probes.txt`): no forearm, hand, finger or sword inside the legs/trunk in any new
  clip (contact_probe, 60 Hz); wrist maxima equal the base clip's (45 / 11 deg); arm skin stretch (new
  `arm_stretch_probe.py`) Ogre max 1.63 (Running 1.52); feet steps and second differences at or below the source's;
  lowest skin +0.08 / -0.00 cm (Sprint too, which `gait_gate.py` does not floor-check).
- Planted stride per side at 1 cm: Ogre Jog 3.001 / 3.001, Sprint 4.210 / 4.191; KnightPlate Jog 3.374 / 3.371,
  Sprint 4.161 / 4.157.
- Renders and playback: `review/<m>_shots_*.png` (viewer shots, cropped), `review/<m>_playback_sheet.png`, iteration
  filmstrips in `review/iter/`; browser recordings at normal and half speed in
  `../mm6_ogr_sprint_claude/review/playback/` and `../mm6_kni_sprint_claude/review/playback/` (`*.webm`).

## Doubtful / left open

- KnightPlate arm stretch: one 14 mm armpit edge weighted to both `B_L_UpperArm` and `B_Spine` stretches 3.61x in the
  accepted `Running` (2.04x in `Walking`) and 4.01x in `Sprint` (lower arm gain or an even spine lean only reached
  3.93x). A rig weighting fault of the model (spine weight in the armpit), slightly worsened, inside black plate.
- The jog and sprint keep the Ogre's `Running` arm carry: the sword sweeps diagonally across the chest at a forward
  arm swing (in front of the body, not inside it after clearance). The KnightPlate's sword likewise swings horizontally
  across the hips as in its `Running`.
- The KnightPlate's jog and sprint read alike from the side (same source family; the sprint is longer and leans more).
- KnightPlate Sprint, right foot: after the heading fix the sabaton tip dips back within 1.5 cm of the floor for
  0.05 of the loop just after lift-off (phase 0.47-0.51); no floor penetration, stride unchanged.
- MAW Ogre A and KnightPlate B/C wander (hostile speed) on `Walking` at x1.5-1.7: outside the window, not gated.
- `gait_gate.py` does not floor-check the sprint clip (`floor_audit.audit` collects `run` and `cast` but not `sprint`
  as living clips); checked here with `scripts/low_probe.py`.
- Not run: in-game captures and the headless actor regressions (bindings are not applied yet).

## Rebuild

`scripts/rebuild.sh [--sources]` (from anywhere): extracts the pre-sprint GLBs from `assets_source` commit `d4c87ca`,
composes both exports from `jobs/`, runs `gait_gate.py` and `check_winding.py` (it reproduces the installed exports
byte for byte). `--sources` re-extracts the two library loops with Blender (`scripts/extract_source.py`) into
`work/sources/` (library-derived, never commit). Probes: `review/final_probes.txt` lists the commands' outputs;
viewers: `scripts/build_viewers.py`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm6_<m>_sprint_claude playback`, `scripts/playback_sheet.py`, `scripts/shots_sheet.py`.
Install: `tools/install_model.py export/mm6_<m>.glb --world mm6`.
