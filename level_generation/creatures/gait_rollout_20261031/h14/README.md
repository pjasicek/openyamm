# Gait rollout package h14: MM7 human peasants (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the four installed MM7 human peasant
sources (`assets_source/worlds/mm7/models/mm7_m3[4-7]2.glb`); existing clips, meshes, skins and materials are
untouched (`scripts/prefix_check.py`: the input's binary chunk is a byte prefix of the export's, old JSON entries
unchanged, only animations appended). All four are **installed** (`tools/install_model.py --world mm7`). No Meshy
credits or other spending; sources are local library loops (`work/sources/`, copied from `../h12/work/sources/`;
library-derived, never commit). `actors.yml` is not edited: [bindings.yml](bindings.yml) is for the coordinator.
Rollback sources (the installed GLBs before this package): `work/mm7_<m>_pre_gait.glb`.

| Model (9 descriptors each) | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Peasant Human1 Female (`mm7_m342`, floor-length skirt + petticoat on 14 x 4 robe chains) | Walk2: humanoid set Relax-Walk-Forward (the installed Walking's source), 1.00 s, 1.4322, 1.43 · Jog: Mixamo Running (5), 0.80 s, 2.1609, 2.70 |
| Peasant Human1 Male (`mm7_m352`, tunic) | Jog: Mixamo Running (5), 0.72 s, 1.8302, 2.54 |
| Peasant Human2 Male (`mm7_m362`, doublet, rapier scabbard) | Jog: Mixamo Running (5), 0.72 s, 2.0639, 2.87 |
| Peasant Human2 Female (`mm7_m372`, gown on 14 x 4 robe chains, bell sleeves) | Walk2: Relax-Walk-Forward, 1.00 s, 1.3861, 1.39 · Jog: Running (5), 0.80 s, 1.9958, 2.49 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree).

## Why

All tiers of each model share one speed (Spd 140 scaled), and MAW leaves Wimps alone, so one binding per model serves
every descriptor in both rulesets.

- Men: the flight (2x Spd: 2.73 / 3.07 u/s) played `Walking` (bound as the run, walk-as-run) at x1.62 / x1.89. A flight
  at Froude about 1 is a run pace, so a plain civilian Jog as for the MM6 (h04) and MM7 goblin (h15) peasants; the
  walk stays (wander x0.81 / x0.95).
- Women: their short dress walk (Relax Walk Forward at 0.8 s, 2.09 / 2.04 u/s) played at x0.70 / x0.68 while wandering
  (1.47 / 1.40 u/s): a `Walk2` from the same source slowed to a 1.0 s loop. Their flight (2.94 / 2.79 u/s) played
  `Walking` at x1.41 / x1.37, inside the window, but it is a run pace (brief: peasants jog in both rulesets), and with
  `Walk2` bound as the walk the flight needs its own clip anyway: a Jog.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
m342  standard/maw Peasant Human1 FemaleA A .. FemaleC C   wander: Walk2 x1.03    chase: Jog x1.09
m352  standard/maw Peasant Human1 MaleA A .. MaleC C       wander: Walking x0.81  chase: Jog x1.07
m362  standard/maw Peasant Human2 MaleA A .. MaleC C       wander: Walking x0.95  chase: Jog x1.07
m372  standard/maw Peasant Human2 FemaleA A .. FemaleC C   wander: Walk2 x1.01    chase: Jog x1.12
```

## Other gates (`review/<m>_probes.txt`, `scripts/probes.sh`)

- `check_winding.py`: 0 inverted closed parts on all four (`review/<m>_winding.txt`). Prefix check ok on all four.
- Phase (left foot forward-most; for the women by the ankle joints, `scripts/joint_phase_probe.py`, because the
  vertex probe reads the floor-length hem as a sole): every new clip at its Walking's phase: m342 0.75 / R 0.25
  (Walking 0.75 / 0.25), m352 and m362 0.20 (Walking 0.21), m372 0.75 / R 0.24-0.25 (Walking 0.75 / 0.25).
- Foot heading (toe-out from +Z, planted L / R, swing range): Walk2 +4.8 / +4.8 (swing +2.3..+4.9) on both women;
  every Jog +2.8..+3.0 / +4.0 (swing -9.0..+14.2, Running (5)'s own foot roll, as h04/h15). Installed Walking: m342
  +5.4 / +5.2, m352 +13.2 / +12.5, m362 +11.4 / +14.9, m372 +8.6 / +9.5.
- Head bob (bob_audit's measure, `bob_probe.py`; uneven): m342 Walk2 2.8 % (0.05), Jog 6.6 % (0.11); m352 Jog 6.3 %
  (0.08); m362 Jog 6.0 % (0.08); m372 Walk2 2.8 % (0.07), Jog 6.9 % (0.15). The women's accepted Walking is 2.2-2.3 %
  (their project evened the bob); Walk2 stays close to it.
- Planted stride per side (`stride_probe.py`, men): m352 1.878 / 1.859, m362 2.081 / 2.075 (gate 1.830 / 2.064: the
  Mixamo heel-strike and toe-roll samples, as h04 found). Women: the probe's soles include the hem; Walk2 1.476 /
  1.466 (m342), 1.395 / 1.395 (m372).
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand inside legs or trunk): m352 Jog L 18 % / 27 mm, R 0
  (Walking 43 % / 39 mm: the left forearm on the tunic skirt); m362 Jog L 39 % / 37 mm, R 25 % / 28 mm (Walking 86 %
  / 37 mm and 51 % / 34 mm: puffed sleeves and doublet skirt); m342 Walk2 78 % / 36 mm, 52 % / 25 mm (Walking 84 % /
  36 mm, 43 % / 25 mm: the hands in the wide skirt, a known limit of the project), Jog 27 % / 38 mm, 14 % / 26 mm;
  m372 0 in every clip. Wrist maxima equal Walking's. Arm skin stretch p99 within 0.25 of Walking's (m342 Jog L 1.47
  vs 1.22, max 2.28; m352 Jog L max 2.64 vs 2.34).
- Lowest skin: men's Jog +0.1 cm; Walk2 -0.0 / -0.1 cm; m342 Jog -0.15 cm; m372 Jog -2.4 cm at the gown hem (Robe
  chain vertices; its accepted Walking -1.9 cm at the shoe). The gate's floor audit is ok on every descriptor.
- Skirts (`skirt_poke_probe.py`, legs through the skirt; front / back): m342 Walking 4 % 7 mm / 100 % 227 mm, Walk2
  0 / 100 % 145 mm, Jog 0 / 84 % 47 mm; m372 Walking 0 / 80 % 147 mm, Walk2 0 / 43 % 83 mm, Jog 4 % 19 mm / 24 %
  131 mm. (The probe's back reading is high on the accepted walks too.)
- Playback in the browser (`tools/run_creature_review.py check` and `playback`: every clip switch, no console
  errors; looked at) on `../../mm7_<m>_gait_h14_claude/review/` viewers (`scripts/build_viewers.py`); half-speed sheets
  `review/<m>_playback_sheet.png`; Blender filmstrips (side, front, back) `review/iter/`.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h12/scripts/compose_gait.py` (h16's composer with h02/h04 `raise_arms`, h07 `arm_raise_deg`, h01
`even_bob`, h19 `track_out`/`follow_thighs`, h06 per-side toe-out, h08's `cloth`) with h09's `soles_feet_only`, plus
`sole_bones` (here `["Foot", "Toe", "Calf"]`: the women's shoe heels are calf-dominated, and Foot/Toe alone let the
Walk2 heel sink 3 cm). Legs, pelvis and trunk rhythm from the library loop, two-bone IK, `stance_foot: Standing` with
5 deg toe-out, `foot_smooth`, `symmetric_drop`; arms and hands from the model's own `Walking`, phase-aligned. Per model:

- Men: h15's goblin-peasant Jog (Running (5), `lock_stance` off, `bob` 0.55, small lean), forearms bent forward 70 deg,
  arms out L 18 / R 10 (m352: the left forearm met the tunic skirt 34 % / 38 mm at L 10) and L / R 10 (m362).
- Women: skirt and petticoat (m342) and gown (m372) re-simulated on every new clip with h08's numpy port of the
  robed projects' `robe_sim.py` (the projects' `robe_sim.py` is the Monk's, unchanged). Chains dumped from
  `../../mm7_<m>_claude/work/rig_v6.blend` (`scripts/dump_chains.py`, `work/<m>_chains.json`). Port check
  (`scripts/cloth_check.py` with the projects' `LEG_R` 1.3 and `leg_capsule_floor` 0.06, `review/cloth_port_check.txt`):
  re-simulating the installed Walking reproduces its chains within median 0.1 / p95 0.2 / max 1.9 cm (m342) and
  0.0 / 0.7 / 3.5 cm (m372). New clips use wider leg capsules (`leg_r` 1.6, `leg_floor` 0.08; the bake's 1.3 / 0.06
  let the knee show through the gown front in 12-37 % of Walk2 samples, up to 93 mm); the Jog adds `mid_collide` and
  `final_collide`. Walk2: `even_bob`, `symmetric_drop` (without it the slowed source limped: uneven 0.38), `bob` 1.0,
  grounding every frame. Jog: `swing_height` 0.7 (a lower knee under the skirt), elbows 60 deg forward and arms out 8
  (m342); m372 30 / 4 deg: her bell sleeves are rigid on the forearm (the project simulates them only in Death), and
  at 60 deg they stood out horizontally.

## Doubts

- The new clips plant at about 5 deg toe-out while the men's accepted Walking plants at 11-15 deg: the heading changes
  at the walk/jog switch (as in earlier packages).
- The Jog keeps Running (5)'s foot roll in the swing (-9..+14 deg) and carries the forearms from Walking bent
  forward, not a library arm swing (as h04/h15).
- m372's gown hem dips 2.4 cm under the floor at one jog phase (gate floor ok; its Walking's shoes reach -1.9 cm).
- m342's hands stay in the wide skirt during Walk2 as in her accepted Walking.
- `Walking` stays bound for `attack_melee` / `attack_ranged` (the native attack reuses the walk); the bindings do not
  touch it. The women's `Walking` is no longer played for locomotion.
- Not run: in-game captures, and the actor regressions with the new bindings (applied by the coordinator).

## Actor regressions

No `runCase` names these four models (`runCase("mm7_` has only `mm7_decoration_models_outdoor_maps`), and
`game/outdoor/HeadlessOutdoorDiagnostics.cpp` checks none of their clip names or counts (the only `clips.size() != N`
check is the MM8 Bedraggled Human's). The generic cases cover them: `mm6_mm7_mm8_actor_models_build_every_binding` and
`every_map_loads_and_builds_its_actor_models` (`scripts/regressions.sh`, `review/regression_*.log`): both PASS on the installed
GLBs with the current (unapplied) bindings (248 maps, 9474 actors, 0 problems). Rerun them after `apply_bindings.py h14/bindings.yml`.

## Rebuild

`scripts/rebuild.sh [m342 m352 m362 m372]` composes every export from `work/mm7_<m>_pre_gait.glb`, `jobs/`,
`work/sources/` and `work/<m>_chains.json` (dumped again from the project master when missing), then runs
`gait_gate.py` with the bindings and `check_winding.py`; the installed files are its outputs. Probes:
`scripts/probes.sh <m> export/mm7_<m>.glb Walking <new clips>`, `skirt_poke_probe.py`, `joint_phase_probe.py`,
`cloth_check.py`; filmstrips `scripts/render_review.sh <glb> <prefix> <clips> -- views=side,front,back`; viewers
`scripts/build_viewers.py <m> <export> <title> Walking <new clips>`, then `python3 tools/run_creature_review.py
--project level_generation/creatures/mm7_<m>_gait_h14_claude playback` and `scripts/playback_sheet.py`. Natural
gait of library loops scaled to these bodies: `scripts/source_gait.py`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h14/export/mm7_<m>.glb --world mm7 --name mm7_<m>.glb`. A far-LOD
repair rerun or any re-export of these models must re-graft these clips (copy the new source over the pre-gait copy
and rerun this rebuild).
