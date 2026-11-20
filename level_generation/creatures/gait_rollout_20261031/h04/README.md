# Gait rollout package h04: MM6 peasants (2026-10-31)

Five MM6 peasant bodies whose chase (Wimps fleeing at 2x Spd, the same in both rulesets) played their walk at
x1.68-2.02, and the MM6 elder (PeasantM3), whose shuffling walk and run also played outside the window and whose MAW
chase (B/C: 7.4-7.8 model units/s) needed a sprint. New in-place clips are appended to the installed sources; every
existing clip, mesh, skin and material is unchanged (`identity_check.py`: the input's binary chunk is a byte-identical
prefix, JSON equal outside animations/accessors/bufferViews). No Meshy credits, no paid actions; sources are local
library loops (`work/sources/*.npz`, copied from the pilot and pirates projects; library-derived, never commit).
All five are installed (`tools/install_model.py`); bindings for the coordinator are in `bindings.yml`.

| Model | Clips added (source, length, stride) | Binding |
|---|---|---|
| PeasantM1 A-C `mm6_pman_v2` | `Jog` (Mixamo Running (5), 0.76 s, 2.03) | run Jog, run_stride_length 2.03 |
| PeasantF2 A-C `mm6_fmp` | `Jog` (Mixamo Running (5), 0.68 s, 1.60) | run Jog, run_stride_length 1.6 |
| PeasantF1 A-C `mm6_pfem` | `Jog` (Mixamo Running (5), 0.66 s, 1.54) | run Jog, run_stride_length 1.54 |
| PeasantM2 A-C `mm6_pmn2` | `Jog` (Mixamo Running (5), 0.74 s, 1.87) | run Jog, run_stride_length 1.87 |
| PeasantM3 A-C `mm6_mep` | `Walk2` (humanoid set Relax-Walk-Forward, 0.90 s, 1.374), `Jog` (Unarmed-Run-Forward, 0.72 s, 2.205), `Sprint` (Unarmed-Sprint, 0.60 s, 4.098) | walking Walk2, stride_length 1.374, run Jog, run_stride_length 2.205, sprint Sprint, sprint_stride_length 4.098 |

Strides: the bound value is the planted stride (sole vertices within 1 cm of the floor, `stride_probe.py`, which the
composer's plant correction targets). The gate's own measurement (2.2 cm band) agrees on mep (lock_stance, all three
equal to 3 decimals), fmp (1.597) and pfem (1.496, 3 % lower); on pman_v2 it reads 1.883 (trusted, 7 % lower than
the planted 2.03, still within the gate's 10 % tolerance) because the long Mixamo heel-strike and toe-roll samples sit
in its band; on pmn2 its two measurements disagree (vertices 1.815, feet 1.267) and 1.87 is planted. Planted per side:
pman_v2 2.027 / 2.007, fmp 1.606 / 1.606, pfem 1.538 / 1.546, pmn2 1.883 / 1.862, mep Walk2 1.387 / 1.378,
Jog 2.204 / 2.203, Sprint 4.101 / 4.099.

Walk-as-run: these peasants walked when they chased in Standard. Their hurried speed (2.5-2.7 units/s, fleeing) is not
a walking pace (the walk played at x1.7-2.0), so they jog in both rulesets; MAW leaves their speed unchanged, so only
the elder (whose MAW B/C speed changes) gets a sprint.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
pman_v2  standard/maw PeasantM1 A-C   wander: Walking x0.84  chase: Jog x1.00
fmp      standard/maw PeasantF2 A-C   wander: Walking x1.32  chase: Jog x1.13
pfem     standard/maw PeasantF1/f1 A-C wander: Walking x0.86  chase: Jog x1.08
pmn2     standard/maw PeasantM2 A-C   wander: Walking x1.01  chase: Jog x1.05
mep      standard PeasantM3 A          wander: Walk2 x0.89    chase: Jog x0.89
         standard PeasantM3 B          wander: Walk2 x1.02    chase: Jog x1.01
         standard PeasantM3 C          wander: Walk2 x1.27    chase: Jog x1.27
         maw      PeasantM3 A          wander: Walk2 x0.89    chase: Jog x0.89
         maw      PeasantM3 B          wander: Jog x1.20      chase: Sprint x1.08
         maw      PeasantM3 C          wander: Jog x1.27      chase: Sprint x1.14
```

## Other gates (`review/<m>_probes.txt`)

- `check_winding.py`: 0 inverted closed parts on all five exports.
- Phase (left foot forward-most): every new clip aligned to its model's Walking: pman_v2 0.21 (Walking 0.21), fmp 0.76
  (0.75), pfem 0.16 (0.17), pmn2 0.16 (0.17), mep 0.00 (0.00). fmp's accepted `Run` is half a loop from its Walking
  (0.27 vs 0.75); the new Jog follows the walk. pmn2's Running is 0.08 off its walk.
- Foot heading, toe-out from +Z planted L / R (swing range): pman_v2 Jog +3.2 / +4.1 (-8.9..+14.2; Walking +9.0 /
  +10.6); fmp +3.7 / +4.5 (-8.8..+14.1; Walking +13.5 / +13.8); pfem +3.1 / +4.2 (-8.7..+14.1; Walking +4.1 / +3.3);
  pmn2 +2.9 / +4.1 (-8.9..+14.2; Walking +15.0 / +9.7); mep Walk2 +4.8 / +4.8, Jog +5.1 / +4.9, Sprint +5.1 / +5.0
  (swing -6.4..+7.4; Walking -1.5 / +4.9). Planted feet are Standing's flat foot turned to 5 deg toe-out.
- Head bob (bob_audit's measure): pman_v2 Jog 6.1 %, fmp 5.6 %, pfem 5.7 %, pmn2 6.3 %, mep Walk2 2.8 % (its Walking
  2.9 %), Jog 5.0 %, Sprint 6.7 %.
- Lowest skin: every new clip within 0.14 cm of the floor (none below -1 cm).
- Arm and hand gate (contact_probe, 60 Hz): no forearm, hand or prop inside the legs or trunk in pman_v2, fmp, pfem,
  pmn2 Jog (the staff: 0 %). pfem's hands against the skirt (PROBE_TARGET=Skirt_): Jog 15 % max 13 mm, her accepted
  Walking 46 % max 39 mm. mep's left hand rests inside his open coat (thigh-weighted coat flap) in his accepted clips
  (Standing 100 %, Walking 92 %, 39 mm), so his clips run without arm clearance (like the Pirate Mage's coat) and read
  the same (Walk2 70 %, Jog 18 %, Sprint 16 %, all max 38-39 mm); his staff touches nothing. Wrist maxima equal the base
  clips'. Arm skin stretch p99 1.20-1.48 (base clips 1.04-1.45); maxima grow on pmn2's left elbow (2.93 vs Running
  2.66), pman_v2 (3.73 vs Walking 3.28) and mep's Sprint right elbow (5.59 vs Running 6.00).
- Staff foot (`prop_low_probe.py`): pmn2 Jog -0.3 cm (Walking -2.2, Running +1.3); mep Walk2 +1.5, Jog +11.5, Sprint
  +7.6 cm (his accepted Running -5.0, Walking -1.5).
- Skirts: fmp's legs through the dress (`skirt_probe.py`) Jog 39 % max 35 mm vs its accepted Run 92 % max 32 mm. pfem
  (`skirt_capsule_probe.py`, skirt inside the leg capsules) Jog 8 % max 18 mm vs her accepted Walking 90 % max 54 mm.
- Playback: `python3 tools/run_creature_review.py --project level_generation/creatures/mm6_<m>_gait_h04_claude
  check|playback` (viewers built by `scripts/build_viewers.py`; all switches, no console errors); half-speed sheets
  `review/<m>_playback_sheet.png`, Blender filmstrips in `review/iter_*`.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

h02's copy of the pilot composer (`../../mm6_sprint_humanoids_claude/`), with these h04 additions:

- `rename_mixamo.py`: the female peasant and the mage have Mixamo rigs; they are composed on a B_-renamed copy and
  renamed back (names only; the probes read the renamed copy).
- `elbow_forward_deg` / `arm_out_deg` (as h02's, with `raise_arms` returning and the arm clearance keeping the bend):
  the peasants without a run take their arms from Walking, so the jog's carried forearm is bent from it (pman_v2 70,
  pfem 60 deg) and turned slightly out (pman_v2 L 14 / R 4, pfem 6 / 6 deg: his tunic flare, her skirt).
- `clear_extra_targets: [Skirt_]`: pfem's hands are cleared from the skirt too.
- `skirt_follow` (pfem): the walk's skirt chains turned with the jog's thighs where they swing further than the walk's
  (gain 0.9, max 29 deg) and `skirt_clear`: chains pushed out of leg capsules (lower thigh, knee to ankle, radii 0.06 /
  0.055 m) with a share to the neighbouring chain. Without them her knee showed through the skirt front.
- `prop_floor` (mep): the staff arm turns up where the staff foot would go under the floor (Walk2 13.6 deg); the Jog
  and Sprint bend the staff elbow forward instead (30 / 50 deg), which keeps the staff clear of the floor and legs.
- `gain_skirt` (`skirt_gain`): unused in the final jobs (tried on fmp).
- fmp: the jog stands taller (`stance_extension` 0.995, `reach` 0.997) because the dress, fitted to the bouncy Run's
  high pelvis, went 4 cm under the floor on a lower jog.

## Doubts

- mep (an elder with a staff) sprints at MAW B/C speed (7.4-7.8 units/s) with the staff held forward like a pike; his
  left hand stays in his coat as in his accepted clips; his Jog keeps the humanoid set's high knee lift (swing_lift
  0.6). A red sash end shows between his legs in the run poses (also in his accepted Running).
- pfem: a small skin spot can still show at the right knee for a frame or two (phase ~0.3); the skirt swings more than
  in her walk.
- pman_v2's gate stride reads 7 % below the bound planted stride (above).
- fmp's dress hem touches the floor at one phase (-0.01 cm).
- Not run: in-game captures and headless actor regressions (the bindings are not applied yet).

## Rebuild

`scripts/rebuild.sh [model ...]` composes every export from the pre-gait copies in `work/mm6_<m>_pre_gait.glb` (the
sources as installed before this package, also the rollback) and runs `scripts/gates.sh` (gait gate with the bindings,
winding, identity, probes); it reproduces the installed exports byte for byte. Install:
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h04/export/mm6_<m>.glb --world mm6
--name mm6_<m>.glb`. A far-LOD repair rerun of these models must re-graft these clips (or rerun this package on the
repaired source).
