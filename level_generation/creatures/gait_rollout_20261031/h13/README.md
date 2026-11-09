# Gait rollout package h13: MM7 dwarf and elf peasants (2026-10-31)

Brief: [../README.md](../README.md). One new in-place locomotion clip (`Jog`) appended to each of the four installed
MM7 peasant sources (`assets_source/worlds/mm7/models/`; pre-gait copies and rollback `work/mm7_<m>_pre_gait.glb`,
SHA-256 in `work/pre_gait.sha256`). Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`:
the input's binary chunk is a byte-identical prefix, only the animation is appended). No Meshy credits or other
spending; the sources are library loops (`work/sources/`, copied from `../h05`, `../h04`, `../h12`; library-derived,
never commit). All four are **installed** (`tools/install_model.py --world mm7`; `work/exports.sha256` = the installed
sources). `actors.yml` is not edited here: [bindings.yml](bindings.yml) is for the coordinator (`--dry-run`: 144 diff
lines, 36 descriptors x run + run_stride_length).

| Model (9 descriptors each, one speed for all tiers) | New clip: source, length, bound stride, authored speed (model units/s) |
|---|---|
| Peasant Dwarf Male A A-C C (`mm7_m302`, club attachment on `Sword` in the right fist) | Jog: humanoid set Unarmed-Run-Forward, 0.70 s, 2.2249, 3.18 |
| Peasant Dwarf Female A A-C C (`mm7_m312`, floor-length dress on 12 x 4 robe chains, apron) | Jog: Unarmed-Run-Forward, 0.62 s, 2.395 (planted), 3.86 |
| Peasant Elf Female A A-C C (`mm7_m322`, staff attachment on `Sword` in the left fist, carried upright) | Jog: Unarmed-Run-Forward, 0.76 s, 2.4487, 3.22 |
| Peasant Elf Male A A-C C (`mm7_m332`, tights, sheathed belt dagger skinned to the body) | Jog: Unarmed-Run-Forward, 0.76 s, 2.5024, 3.29 |

Bound strides are `gait_gate.py`'s trusted measurements, except the Dwarf Female's: the gate's vertex measurement
(2.492) and foot joints (2.349) bracket the planted soles (`stride_probe.py` L 2.412 / R 2.381), so the planted mean
2.395 is bound (gate PASSED with it, `--set run_stride_length=2.395`).

## Why (targets, `review/mm7_<m>_gate_before.txt`)

Wimps: they flee at 2x Spd, and MAW leaves their speed unchanged (no sprint). Every tier of a model has one scale, so
one speed: wander / flight 1.56 / 3.13 (m302), 1.91 / 3.82 (m312), 1.60 / 3.21 (m322), 1.64 / 3.28 (m332). The flight
played the walk (bound as `run: Walking`) at x1.81-2.64 (held at the 2x cap: sliding feet). As the MM6 peasants (h04)
and MM7 goblin peasants (h15): a plain civilian Jog for the flight; walks unchanged (they fit the wander at
x0.90-1.32).

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor, both rulesets)

```
m302 Dwarf Male    standard/maw A A .. C C   wander: Walking x1.32  chase: Jog x0.98
m312 Dwarf Female  standard/maw A A .. C C   wander: Walking x0.96  chase: Jog x0.99
m322 Elf Female    standard/maw A A .. C C   wander: Walking x0.90  chase: Jog x1.00
m332 Elf Male      standard/maw A A .. C C   wander: Walking x0.96  chase: Jog x1.00
```

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h12/scripts/compose_gait.py` (h16 lineage with h02/h04 `raise_arms`, h07 `arm_raise_deg`, h01
`even_bob`, h19 `track_out`/`follow_thighs`, h08 `cloth`, h12 `hand_props`), `render_clip.py` from `../h05` (back
view). Legs, pelvis and trunk rhythm from the humanoid set's Unarmed-Run-Forward (Mixamo Running (5) without
`lock_stance` left the elf's planted strides 9 % apart, L 2.55 / R 2.34), `lock_stance` planted soles, two-bone IK,
`stance_foot: Standing` with 5 deg toe-out, `even_bob` + `symmetric_drop`, `swing_height` lowered for a plain civilian
run; arms, hands and props from the model's `Walking` (none has a run) with a forward elbow bend, phase-aligned to
`Walking`. One addition:

- **`upright_props`** {node: hand bone}: the Elf Female's staff is keyed upright in the world in her accepted clips
  (`CARRY_FRAME=world`; its axis is constant over `Walking`). Copying `Walking`'s staff keys onto the new arm tilted
  it up to about 15 deg; now its world orientation is `Walking`'s mean and its origin rides at `Walking`'s grip point
  in the hand (grip spread 0).

Per model:
- **Elf Male**: elbows forward 60 deg, arms out L 12 / R 8 (at 8 the left thumb brushed the thigh: 13 % / 18 mm),
  `swing_height` 0.75, `bob` 0.3.
- **Dwarf Male**: left elbow 60 deg, the club arm only 30 deg (at 60 the club swung up across the face), arms out 10 /
  10, `swing_height` 0.75. Natural fit: the source's scaled stride is 2.16 for 2.19 asked.
- **Elf Female**: right elbow 60, staff arm 20 deg with arm out 20 (at 8 / 14 the staff forearm met the belly front:
  48 % / 34 mm, 30 % / 13 mm; her accepted `Walking` has it 100 % / 38 mm), the staff upright (above), `swing_height`
  0.75.
- **Dwarf Female** (dress): a short, low, quick run (0.62 s, forward scale about 0.75 of the source's stride,
  `swing_height` 0.25: at 1.0-0.4 the kicked shoe came out behind and through the back hem). The dress is simulated
  on the new motion with h08's numpy port of the robed projects' `robe_sim.py` (chains dumped from
  `../../mm7_m312_claude/work/rig_v6.blend`, `work/m312_chains.json`). The port re-simulated on her `Walking` with the
  bake's settings (`LEG_R` 1.3, `leg_capsule_floor` 0.06) matches the installed robe keys within median 0.1 / p95 0.3 /
  max 1.1 cm (`scripts/cloth_check.py`). The Jog uses m422's run options (`leg_r` 2.0, `margin` 0.02, `mid_collide`,
  `final_collide`, `bend_smooth` 3, `bend_max` 15, `nb_final`).

## Phase

Every Jog puts the left foot forward-most at its model's `Walking` phase (`align: Walking`): m302 0.18 (Walking 0.19),
m312 0.74 (0.75), m322 0.20 (0.21), m332 0.20 (0.21). None has an installed run.

## Checks (`review/<m>_probes.txt`, `scripts/probes.sh`)

- `check_winding.py`: 0 inverted closed parts on all four. `prefix_check.py` ok on all four.
- Foot heading (toe-out from +Z, planted L / R, swing range): every Jog +5.0..+5.1 / +4.9..+5.0 (swing -5.2..+7.4).
  Installed walks: m302 +22.8 / +18.3, m312 +4.8 / +5.5, m322 +10.6 / +12.9, m332 +13.7 / +15.8.
- Head bob (bob_audit's measure; `uneven`): m302 Jog 5.9 % (0.01), m312 6.0 % (0.01), m322 5.2 % (0.01), m332 5.1 %
  (0.01). Walks: 4.9, 3.9, 5.5, 5.5 %.
- Planted stride per side (`stride_probe.py`): m302 2.284 / 2.200 (gate 2.225; 4 % apart, the largest here), m312
  2.412 / 2.381, m322 2.451 / 2.454, m332 2.520 / 2.475.
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/finger/prop inside legs or trunk): m302 arms and club 0 %,
  m322 arms and staff 0 %, m332 0 %; m312 L 24 % / 22 mm, R 18 % / 16 mm (open hands brushing the apron/hip front, 2-3
  mm deep at the probed phases; her accepted `Walking` 63 % / 19 mm and 47 % / 27 mm). Wrist maxima equal `Walking`'s
  (78 / 17 / 32 / 25 deg).
- Arm skin stretch p99 within 0.14 of `Walking`'s (m302 L 1.41 vs 1.29, max 2.64 vs 2.44; m312 1.27 vs 1.13; m322 and
  m332 within 0.05).
- Lowest skin: every Jog within 0.06 cm of the floor (none below -1 cm). Props (`prop_low_probe.py`): club lowest
  +21.7 cm (Walking +5.4), staff +8.8 cm (Walking -6.4: its accepted walk dips the staff foot into the floor).
- Dress (`skirt_poke_probe.py`, horizontal rays from the pelvis axis; it reads the accepted walk as 100 % / 207 mm
  because her legs are painted dress-coloured tubes under the hem): Jog front 0 %, back 68 % / 210 mm; looked at in
  back and side filmstrips (`review/iter/m312_d*`): the shoes stay at or under the hem as in `Walking`.
- Playback in the browser (`tools/run_creature_review.py check` and `playback`: no console errors, every clip
  switch, normal and half speed; looked at) on `../../mm7_<m>_gait_h13_claude/review/` viewers
  (`scripts/build_viewers.py`), sheets `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/`.
- Headless actor regressions on the installed GLBs with the current (unapplied) bindings (`scripts/regressions.sh`,
  `review/regression_*.log`): no `runCase` names these four models; the generic
  `mm6_mm7_mm8_actor_models_build_every_binding` and `every_map_loads_and_builds_its_actor_models` cover them; both
  PASS on the installed files (passed=1 failed=0 each). Rerun after `apply_bindings.py`.
  `game/outdoor/HeadlessOutdoorDiagnostics.cpp` names none of their clips or clip counts.

## Doubts / left open

- Dwarf Female: a quick, short-stepped run (0.62 s loop) with a low swing so the shoes stay under the floor-length
  dress; from behind, the dress-coloured calf shows at the hem as in her accepted walk. The swing foot grazes the floor
  briefly late in the swing (phase probe: a second touch 0.83-0.86), a heel-toe blip of the low swing.
- Dwarf Male: planted strides per side 4 % apart (2.28 / 2.20); the gate's 2.225 is bound.
- New clips plant at 5 deg toe-out while the Dwarf Male's and Elves' walks plant at 11-23 deg: the heading changes at
  the walk/jog switch, as in earlier packages.
- Elf Female: the staff arm is turned out 20 deg in the Jog (her accepted walk keeps the forearm against the belly).
- Not run: in-game captures (bindings not applied yet).

## Rebuild

`scripts/rebuild.sh [m302 m312 m322 m332]` composes the exports from `work/mm7_<m>_pre_gait.glb`, `jobs/` and
`work/sources/` (plus `work/m312_chains.json`), then runs `gait_gate.py` and `check_winding.py`; it reproduces
`work/exports.sha256`. Probes: `scripts/probes.sh <m> <export> Walking Jog [Sword=<prop.glb>]`,
`scripts/skirt_poke_probe.py`, `scripts/prop_low_probe.py`, `scripts/inside_where.py`; filmstrips
`scripts/render_review.sh <export> <prefix> <clips> [Sword=<prop.glb>] -- views=side,front,back`; viewers
`scripts/build_viewers.py <m> <export> <title> Walking Jog [Sword=<prop.glb>]`, then `python3
tools/run_creature_review.py --project level_generation/creatures/mm7_<m>_gait_h13_claude playback` and
`scripts/playback_sheet.py <m> Walking,Jog`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h13/export/mm7_<m>.glb --world mm7 --name mm7_<m>.glb`. Rollback:
install `work/mm7_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or reduction rerun
on these models must re-graft the Jog (copy the new source over the pre-gait copy and rebuild).
