# Gait rollout package h20: MM8 Troll, Troll Peasant, Minotaur, Minotaur Peasant (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the four installed MM8 sources
(`assets_source/worlds/mm8/models/`; pre-gait copies `work/mm8_<m>_pre_gait.glb` = assets_source commit `d4c87ca`,
SHA-256 m476 `ac65e6c1…`, m480 `aac48c8c…`, m484 `3f0fc5fc…`, m488 `31c05c0e…`). Existing clips, meshes, skins and
materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a byte prefix, only animations
appended). No Meshy credits or other spending; sources are humanoid-set library loops (`work/sources/`, never
committed). All four are **installed** (`tools/install_model.py --world mm8`); `actors.yml` is not edited:
[bindings.yml](bindings.yml) is for the coordinator (`apply_bindings.py --dry-run`: 90 diff lines, applies cleanly).

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Troll A-C (`mm8_m476`, club in the left hand) | Walk2: humanoid set Armed-Walk (its Walking's family), 0.90 s, 1.3097, 1.46 · Jog: Unarmed-Run-Forward, 0.76 s, 2.244, 2.95 · Sprint: Unarmed-Sprint, 0.64 s, 3.5221, 5.50 |
| Troll Peasant A-C (`mm8_m480`, Wimp, bone club) | Walk2: Armed-Walk (its Walking's family), 1.15 s, 1.1977, 1.04 |
| Minotaur A-C (`mm8_m484`, two-handed axe, mail kilt) | Walk2: Armed-Walk, 0.92 s, 1.361, 1.48 · Jog: Unarmed-Run-Forward, 0.76 s, 2.2942, 3.02 · Sprint: Unarmed-Sprint, 0.64 s, 3.062, 4.78 |
| Minotaur Peasant A-C (`mm8_m488`, short wrap) | Jog: Armed-Run-Forward, 0.74 s, 3.5602, 4.81 · Sprint: Unarmed-Sprint, 0.60 s, 4.9617, 8.27 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree; planted soles per side within 1 %
of the binding except Troll Sprint R 3.411 vs 3.522, -3 %). The replaced `Walking` and `Running` clips stay in the
GLBs, unbound for locomotion (the Troll Peasant keeps `Walking` for its walk-as-run flight).

## Why these clips (targets from `gait_gate.py` without `--candidate`)

- **Troll** (0.71 m leg, 0.78 m hip, the MM8 Ogre Warrior's size): wander 1.35-1.76, chase 2.70-3.51, MAW chase
  5.40-5.81 u/s. `Walking` (1.86 u/s by binding, 2.01 by the trusted stride) played A's wander at x0.73 and `Running`
  (3.67) A's chase at x0.74, MAW B/C at x1.51/1.58. A slower walk at a heavy cadence, a jog at Froude 1-1.6 and a
  sprint like h19's Ogre Warrior (5.3 u/s at 0.64 s).
- **Troll Peasant** (hip 0.85 m): wanders at 1.09 u/s (`Walking` x0.58) and flees at 2.18 (Froude 0.57 on the hip, a
  walking pace): the walk-as-run decision holds (as h19's Ogre Peasant), so only a slow `Walk2` (1.04 u/s); flight keeps
  `run: Walking` (x1.17). MAW leaves its speeds unchanged.
- **Minotaur** (0.75 m leg): wander 1.44-1.73 (`Walking` x0.68-0.82), chase 2.89-3.46 (Running x0.95-1.13, inside),
  MAW 4.91-5.19 (x1.61-1.70). It gets Walk2 and Sprint, and a Jog too: the installed `Running` is half a loop from
  `Walking` (left foot forward-most 0.23 vs 0.75), its stride was untrusted (vertices 2.48, feet 1.77, binding 2.24)
  and its right foot plants at +39 deg. With a Jog every locomotion switch (walk, run, sprint) stays in phase.
- **Minotaur Peasant** (0.89 m leg, 1.07 m hip, the MM7 Troglodyte's legs): chase 4.50-5.72 (`Running` x1.65-2.0,
  stride check failing: vertices 2.48 / feet 1.81), MAW 8.38-8.99 (at the 2x cap, sliding). Jog at Froude 2-3 and a
  real sprint (h08's Troglodyte: 8.3 u/s at 0.60 s). MAW treats it as a fast melee monster (its MAW chase changes), so
  it sprints there; the gate's Standard chase rows are its flight.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Troll             standard A wander Walk2 x0.93  chase Jog x0.92 | maw A chase Sprint x0.98
                  standard B wander Walk2 x1.02  chase Jog x1.01 | maw B chase Sprint x1.01
                  standard C wander Walk2 x1.21  chase Jog x1.19 | maw C chase Sprint x1.06
Troll Peasant     standard/maw A-C wander Walk2 x1.05  flee Walking x1.17 (MAW leaves the speeds unchanged)
Minotaur          standard A wander Walk2 x0.98  chase Jog x0.96 | maw A chase Sprint x1.03
                  standard B wander Walk2 x1.01  chase Jog x0.99 | maw B chase Sprint x1.04
                  standard C wander Walk2 x1.17  chase Jog x1.15 | maw C chase Sprint x1.09
Minotaur Peasant  standard A wander Walking x1.05  chase Jog x0.93 | maw A chase Sprint x1.01
                  standard B wander Walking x1.19  chase Jog x1.06 | maw B chase Sprint x1.05
                  standard C wander Walking x1.33  chase Jog x1.19 | maw C chase Sprint x1.09
```

MAW's wander rows (hostile speed, not judged): Troll Jog x0.92-0.98, Minotaur Walk2 x1.66-1.76, Minotaur Peasant Jog
x0.87-0.93.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h07/scripts/compose_gait.py` (the pilot composer with h16's and h02's additions, h07's arm raise) with
h19's `track_out` and loincloth `gain`/`rest_relative`, and two garment solvers added here:

- **`kilt_solve`** (`scripts/kilt_solve.py`, Minotaur): the mail kilt hangs from twelve translation-only `Skirt_*`
  controls that the project fitted per frame against the closed body (`../../mm8_m484_claude/scripts/solve_cloth.py`).
  A numpy version on the composed pose: kilt samples (vertices below 0.89 m, triangle centroids, edge midpoints) inside
  the body (nearest body triangle, by its normal) pull the controls by regularised least squares toward the surface +
  1 cm. `from_base`: it starts from the base clip's phase-aligned offsets and adds a correction capped at 0.12 m.
  Port check (`scripts/kilt_check.py`, `review/m484_kilt_port_check.txt`): re-solving the installed `Walking` from
  zero lands within 6 mm (median, p95 3.2 cm) of the installed controls and leaves 0 kilt samples inside.
- **`wrap_solve`** (`scripts/wrap_solve.py`, Minotaur Peasant): the wrap is a 48-control surface cage (`Wrap_<row>_<col>`)
  the project fitted per frame to a thigh-following target and then pushed out of the skin
  (`../../mm8_m488_claude/scripts/wrap_motion.py`, `wrap_cage.py`). `target: thighs` reproduces that target (four
  waist pivots turning the cloth with the thighs, weighted by height and side) and fits the cage to it by least
  squares; port check (`scripts/wrap_rule_check.py`, `review/m488_wrap_rule_check.txt`): Standing within 7 mm, Walking
  median 8 mm / p95 2.5 cm of the installed wrap (the rest is the project's skin push). Then the project's projection:
  inside = nearest skin face facing away and an odd parity-ray count; each control moves along its outward radial by
  its vertices' need (exit distance + 0.05 m margin, the project's Running margin), 20 passes, (1, 2, 1) / 4 loop
  smoothing, projection again. Added here: a weak-vertex floor on the share's denominator (0.3) and a 0.25 m cap on
  the added move per control (without them one upper-row control was pushed 2-3 m along a raised thigh). Copying
  `Running`'s cage offsets instead left 82-100 % of samples with the wrap inside the legs: `Running` keeps both thighs
  forward (+19..+77 deg) and the new clips swing them back too.

Per-model choices:

- **Troll**: arms and club from its own `Running` (Armed run, mirrored), clearance with the club as a probe (0 deg
  needed); Walk2 from `Walking`'s arms. h19's Ogre jobs scaled to its pace, Jog `bob` 0.26.
- **Troll Peasant**: Walk2 `swing_height` 1.5 (the scaled slow walk kept the foot within 1.5 cm of the floor for 94 %
  of the loop: a shuffle; now stance 0.61-0.66 like `Walking`'s 0.67). Loincloth bones come from `Walking`
  (phase-aligned); legs through the loincloth (`skirt_poke_probe.py`, LoinFront/LoinBack): Walk2 3 % / 6 mm, Walking
  4 % / 7 mm.
- **Minotaur**: arms and axe from `Running` with h02's rigid two-handed `arms_raise_deg` (Jog 8, Sprint 12) so the haft
  clears the knee drive (contacts 0 %); spine weights 0.4-0.5 (h02's MM6 Minotaur); `symmetric_drop`;
  `swing_height` 0.7 on Jog and Sprint (less heel kick into the kilt's back panel); kilt re-solved on all three clips.
- **Minotaur Peasant**: a skirt-safe run. The humanoid-set Unarmed run drove the thighs to +124-131 deg (knee 1.15 m,
  above the hip) through the wrap; the Jog is the Armed run (knee flex 68 deg, the Vampire's robe-safe source) at
  `swing_height` 0.6 and `stance_extension` 0.9 (thighs -18..+80 deg, like `Running`'s +77; head bob 10.8 % -> 4.9 %
  with the lower stance), the Sprint the Unarmed sprint at `swing_height` 0.6 without extra arm gain (with 1.3 the
  forearms went through the flared wrap); arms from `Running`.

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase (`align: Walking`): Troll 0.30 (Walking
0.29; its Running 0.38), Troll Peasant 0.75, Minotaur 0.75, Minotaur Peasant 0.17. The Troll Peasant's and the
Minotaur's installed `Walking` and `Running` are half a loop apart (0.75 vs 0.28 / 0.23); the new clips follow the walk.

## Checks (`review/`)

- `<m>_gait_gate.txt` PASSED; `<m>_winding.txt` 0 inverted closed parts on all four; `<m>_probes.txt` (phase, foot
  heading, bob, planted stride, motion, arm stretch, contacts, lowest skin, prefix).
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R; swing range):
  - Troll Walk2 +4.8 / +5.0 (+4.8..+15.0), Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +4.9 (-6.3..+6.5);
    installed Walking +7.5 / +8.0, Running +6.5 / +9.5
  - Troll Peasant Walk2 +4.8 / +5.0 (+4.8..+15.0); Walking +0.0 / +1.1
  - Minotaur Walk2 +4.7 / +5.0 (+4.8..+15.0), Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.3..+6.5);
    Walking +10.7 / +10.4, Running +2.3 / +39.0
  - Minotaur Peasant Jog +5.0 / +5.4 (+2.1..+9.4), Sprint +5.1 / +5.0 (-6.4..+6.5); Walking +12.0 / +3.1,
    Running +18.5 / +31.4
- Head bob (bob_audit's measure): Troll Walk2 3.9 %, Jog 5.0 %, Sprint 6.3 %; Troll Peasant Walk2 3.3 %; Minotaur
  Walk2 4.4 %, Jog 4.8 %, Sprint 5.9 %; Minotaur Peasant Jog 4.9 %, Sprint 6.1 %. `uneven` 0.06-0.19.
- Arm and hand gate (`contact_probe.py`, 60 Hz; forearm/hand/finger/prop inside legs and trunk): 0 % in every new
  clip, club and axe included (accepted: Minotaur Running left 2 % / 8 mm, Troll Peasant Running club 2 % / 9 mm).
  Wrist maxima equal the base clips' (Troll 9 / 34, Peasant 72, Minotaur 89 / 112, Minotaur Peasant 45 deg). Arm
  stretch p99 within 0.03 of the base clip's; maxima: Troll Jog/Sprint right 11.6 / 12.3x on the edge that reads 11.7x
  in its accepted `Running`; Minotaur at or below `Running`'s.
- Lowest skin 0.0 cm on every new clip (sprints included); no key below -1 cm.
- Garments: Minotaur kilt samples deeper than 1 cm inside the body (`kilt_depth_probe.py`, `review/m484_kilt_probe.txt`):
  Walking 0 %, Running (accepted) 16 % / 100 mm, Walk2 0 %, Jog 52 % / 54 mm, Sprint 39 % / 99 mm (before the solve
  91 % / 105 mm and 79 % / 120 mm). Minotaur Peasant wrap inside the skin (`wrap_check.py` with face samples,
  `review/m488_wrap_probe.txt`): Walking 0 %, Running 0 %, Jog 0 %, Sprint 17 % (at most 6 samples, 16 mm).
- Playback (`tools/run_creature_review.py check`: no console errors; `playback` at normal and half speed, looked at):
  viewers in `../../mm8_<m>_gait_h20_claude/review/`, sheets `review/<m>_playback_sheet.png`; Blender filmstrips
  `review/iter/` (hip close-ups `m484hip4_*`).
- Actor regressions on the installed GLBs (current bindings), `review/regression_*.log`, all pass:
  `mm8_troll_actor_models_keep_native_tiers_and_club`, `mm8_troll_peasant_actor_models_keep_native_tiers_and_bone_club`,
  `mm8_minotaur_actor_models_keep_native_roles`, `mm8_minotaur_peasant_actor_models_keep_native_roles`,
  `mm6_mm7_mm8_actor_models_build_every_binding` (`OPENYAMM_REGRESSION_FILTER=<case> ./build/game/openyamm --world mm8
  --headless-run-regression-suite actors`). Rerun them after `apply_bindings.py`.

## Doubtful / left open

- **Minotaur kilt.** The translation-only kilt cannot follow the jog's and sprint's knee drive and heel kick fully:
  shallow intersections remain in about half the jog and 40 % of the sprint (most under 2 cm; the sprint's heel kick
  reaches 10 cm into the back panel for a few frames, like the accepted `Running`'s 10 cm at the right thigh). Hip
  close-ups show the panels following the thighs without tears; worth a look in game.
- **Minotaur Peasant sprint**: the front wrap touches the raised thigh (16 mm, 17 % of the loop) at the top of the
  knee drive. The Jog is the Armed run family (a lower knee) and the Sprint the Unarmed sprint: they read a little
  differently.
- The Minotaur's `Running` is no longer bound (half a loop off the walk, untrusted stride, +39 deg right foot): a
  deliberate change beyond the listed failures, so walk/run/sprint switches stay in phase.
- Walk-to-run switches change the toe-out (new clips plant at 5 deg; accepted walks at 0-12 deg, the Minotaur's and
  Minotaur Peasant's `Running` at up to +39 deg).
- Troll Peasant flight stays on `Walking` at x1.17 (walk-as-run, Froude 0.57).
- The pending texture pass of the Troll Peasant (`../../mm8_m480_texpass_claude/scripts/merge_install.sh`) layers onto
  the currently installed source and keeps every clip, so it can run now.
- Not run: in-game captures (bindings not applied yet).

## Rebuild

`scripts/rebuild.sh [--sources] [m476 m480 m484 m488]` composes the exports from `work/mm8_<m>_pre_gait.glb` (or
assets_source commit `d4c87ca`) and `jobs/`, then runs `gait_gate.py` and `check_winding.py`; it reproduces the
installed exports byte for byte (`work/exports.sha256`). `--sources` extracts the four humanoid-set loops with Blender.
Probes: `scripts/probes.sh <m> export/mm8_<m>.glb <old clips> <new clips> [node=prop.glb]`, `kilt_depth_probe.py`,
`wrap_check.py`, `thigh_probe.py`, `skirt_poke_probe.py`; filmstrips `scripts/render_review.sh`; viewers
`scripts/build_viewers.py`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_<m>_gait_h20_claude playback` and `scripts/playback_sheet.py`. Install:
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h20/export/mm8_<m>.glb --world mm8`.
Rollback: install `work/mm8_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob,
reduction or texture rerun that rebuilds these sources must keep or re-graft the clips (copy the new source over the
pre-gait copy and rebuild).
