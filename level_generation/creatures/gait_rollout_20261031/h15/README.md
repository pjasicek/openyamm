# Gait rollout package h15: MM7 goblin peasants, Earth Elemental and Gog (MM7 and MM8) (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the four installed sources; existing
clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a byte
prefix of the export's, every old JSON entry unchanged, only animations appended). All four are **installed**
(`tools/install_model.py`). No Meshy credits or other spending; the sources are local library loops
(`work/sources/`, copied from `../h08` and `../h16`; library-derived, never commit). `actors.yml` is not edited:
[bindings.yml](bindings.yml) is for the coordinator, plus [bindings_agog_c.yml](bindings_agog_c.yml) (below).
Rollback sources (the installed GLBs before this package): `work/<name>_pre_gait.glb`.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Peasant Goblin Male (`mm7_7m452`, 9 descriptors) | Jog: Mixamo Running (5), 0.72 s, 1.7791, 2.47 |
| Peasant Goblin female (`mm7_m442`, 9 descriptors) | Jog: Mixamo Running (5), 0.70 s, 1.5766, 2.25 |
| Earth Elemental (`mm8_m504`, MM7 Elemental Earth A-C, MM8 Earth Elemental A-C) | Walk2: humanoid set Armed-Walk-Slow, 1.50 s, 1.4426, 0.96 · Jog: humanoid set Unarmed-Run-Forward, 0.82 s, 2.4246, 2.96 · Run: Unarmed-Run-Forward, 0.74 s, 3.1334, 4.23 |
| Gog (`mm8_m612`, MM7 AGog A-C, MM8 Gog A-C) | Walk2: humanoid set Armed-Walk (its Walking's source), 0.95 s, 1.3858, 1.46 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree; planted per side within 1 %).

## Choices per model

- **Goblin peasants** (Wimps: they flee at 2x Spd, the same in both rulesets): the flight (2.60 / 2.36 u/s) played
  the walk at x1.55 / x1.75. Like the MM6 peasants (h04) they get a plain civilian Jog for the flight; walks stay. Arms
  from their Walking with a forward elbow (male 70, female 60 deg) and abduction (male L 18 / R 10: his left hand
  brushed the tunic at 8 deg; female 8 / 8).
- **Earth Elemental** (heavy stone giant, hip 1.07, boulder feet). The two worlds need different clips, so they bind
  differently (bindings are per world and per descriptor):
  - MM7 (scales 87-145): wandering 1.8-2.5 u/s fits the installed Walking; the chase (3.6-5.1) played it at
    x1.96-2.76, so a `Run` (MM7's run).
  - MM8 (all tiers scale 145, Spd 110-200): A/B wander at 0.76 / 0.90 u/s (Walking x0.41 / x0.49): a slow heavy `Walk2`
    (window for A-C wandering only 0.92-1.01 u/s authored). A/B chase on the installed Walking as now (x0.83 / x0.98).
    C chases at 2.77 (Walking x1.51) and MAW's C at 5.53: C gets `Jog` (Standard chase) and `Run` bound as its sprint.
  - Jog and Run come from the same humanoid-set run (a switch keeps the style), with a lower swing foot
    (`swing_height` 0.75 / 0.85), elbows bent 20 deg (30-40 stretched the left elbow skin to 3.6-3.9x), arm swing x1.3
    / x1.5. Mixamo jogs (Slow Jog, Running (5), Mutant Run, Unarmed Run Forward) all crouched this body to 70-80 deg
    stance knees (Slow Jog broke: pelvis drop 0.59 m); rejected.
  - Every clip copies Walking's rubble hide keys (Rubble bones at scale 1e-4, `Rubble` node scale 0).
- **Gog**: by the user's choice it walks at every Standard speed (`run: Walking`). Gogs attack with fire (ranged), so
  MAW leaves their speed unchanged: MAW's chase is Standard's, and any run or sprint bound would also play in Standard,
  against that choice. So no chase clip is bound; only MM7 AGog C (the large Magog, wander 1.43 u/s, Walking at
  x0.62 in slow motion) gets a slower `Walk2`, its chase staying on Walking (x1.25). See "Left open".

Phase: every new clip puts the left foot forward-most at its model's Walking phase (male 0.20 / Walking 0.21,
female 0.21 / 0.20, Elemental 0.25 / 0.25, Gog 0.75 / 0.75). The Gog's installed Running is half a loop from its
Walking (0.25 vs 0.75); it is unbound.

## Gate window sections (`review/*_gait_gate.txt`)

```
Goblin male    standard/maw A A .. C C   wander: Walking x0.77  chase: Jog x1.05      PASSED
Goblin female  standard/maw A A .. C C   wander: Walking x0.88  chase: Jog x1.05      PASSED
Earth Elem MM7 standard/maw A            wander: Walking x1.38  chase: Run x1.20      PASSED (run=Run)
               standard/maw B            wander: Walking x1.13  chase: Run x0.98
               standard/maw C            wander: Walking x0.98  chase: Run x0.85
Earth Elem MM8 standard/maw A            wander: Walk2 x0.79    chase: Walking x0.83  PASSED (A/B: walking=Walk2)
               standard/maw B            wander: Walk2 x0.94    chase: Walking x0.98
               standard C                wander: Walk2 x1.44    chase: Jog x0.94      PASSED (C: walking=Walk2,
               maw C                     wander: Jog x0.94      chase: Run x1.31        run=Jog, sprint=Run)
Gog MM7        standard/maw AGog C       wander: Walk2 x0.98    chase: Walking x1.25  PASSED (walking=Walk2)
               standard/maw AGog A / B   wander: Walking x1.04 / x1.13  chase: Walking x2.00 slide 1.04 / 1.13  FAIL
Gog MM8        standard/maw Gog A/B/C    wander: Walking x1.35 / 1.21 / 1.01  chase: Walking x2.00 slide 1.35 / 1.21 / 1.01  FAIL
```

The Gog FAIL rows are the unchanged user-chosen walk-as-run (not altered by this package). Subsets gated with
`../q2/scripts/gate_only.py`. Floor: ok on every descriptor (the MM8 C sprint included).

## Other gates (`review/<name>_probes.txt`, `scripts/probes.sh`)

- `check_winding.py`: 0 inverted closed parts on all four exports.
- Foot heading (toe-out from +Z, planted L / R, swing range): male Jog +2.9 / +4.0 (-8.8..+14.2; Walking +17.7 /
  +17.2); female Jog +2.8 / +4.1 (-8.8..+14.0; Walking -1.2 / +9.1); Elemental Walk2 +4.7 / +5.0 (+4.1..+15.0), Jog and
  Run +5.0 / +4.9 (-5.2..+7.4) (Walking +28.3 / +23.8: its wide stomp); Gog Walk2 +4.6 / +5.0 (+3.2..+15.0; Walking
  +6.4 / +6.3).
- Head bob (bob_audit's measure, `bob_probe.py`): male Jog 6.0 %, female Jog 6.1 %; Elemental Walk2 3.3 %, Jog 5.5 %,
  Run 5.6 % (Walking 4.6 %); Gog Walk2 3.4 % (uneven 0.27, the Armed Walk's own asymmetry; Walking 5.0 %).
- Arm and hand gate (contact probe, 60 Hz, forearm/hand inside legs or trunk): male Jog 5 % / 9 mm left (Walking 14 %
  / 12 mm), female Jog right 26 % / 21 mm (Walking 37 % / 29 mm, the wide sleeve at the hip), Elemental and Gog 0 in
  every new clip (Elemental Walking 26 % / 17 mm). Wrist maxima equal Walking's (81 / 107 / 44 / 9 deg).
- Arm skin stretch p99 within 0.13 of Walking's; maxima: male 2.57 (Walking 2.12), female 2.42 (2.05), Elemental
  Jog / Run 3.29 / 3.32 on the left elbow (Walking 2.39), Gog Walk2 equal to Walking.
- Lowest skin: 0.0 to +0.1 cm in every new clip. Pelvis and stance knee (`scripts/pelvis_probe.py`): Elemental Walk2 /
  Jog / Run pelvis 1.14 / 1.16 / 1.14 m (Walking 1.09), stance knee 36-51 deg (Walking 42-47).
- Playback in the browser (`tools/run_creature_review.py check` and `playback`, no console errors, all clip switches;
  normal and half speed recordings) on `../../<name>_gait_h15_claude/review/` viewers (`scripts/build_viewers.py`);
  half-speed sheets `review/<name>_playback_sheet.png`, Blender filmstrips in `review/iter/`. Looked at.

## Left open / doubts

- **Gog chase (not fixed, the user's choice).** MM7 AGog A/B chase at 4.77 / 5.16 u/s and MM8 Gog A/B/C at
  6.16 / 5.52 / 4.65 on Walking (2.29 u/s): x2.08-2.70, held at the 2x playback cap, so the feet slide by x1.04-1.35.
  The walk-as-run choice was made at pursuit 1.75x (x1.4-2.4 then). A chase this fast is a run pace for its 0.90 m
  hip (Froude 2.4-4.3); a walk cannot cover it. A run for 4.65-6.16 u/s would need an authored 4.1-6.2 u/s (the
  installed Running is 1.99 u/s). If the user changes the decision, a Jog/Run can be composed like the Elemental's.
  The brief's "give MAW's chase a sprint" does not apply: Gogs are ranged attackers, MAW keeps their speed.
- `apply_bindings.py` cannot change `walking` on MM7 AGog C: its `clips:` is a one-line flow mapping (the tool's
  `section()` returns None and `apply_entry` raises a TypeError). The entry is in `bindings_agog_c.yml`: apply by hand
  (`clips.walking: Walk2`, `animation.stride_length: 1.3858`) or after the tool learns flow mappings.
- Earth Elemental MM8 C wanders on Walk2 at x1.44 (the window allows only 0.92-1.01 u/s authored for all three MM8
  tiers' wandering).
- Earth Elemental left elbow skin stretches to 3.3x in Jog/Run (Walking 2.4x), inside stone at the elbow.
- Earth Elemental planted feet now point along travel (+5 deg) in the new clips while its Walking stomps at +24-28 deg:
  the walk/run switch changes the foot heading (as on h02's Dwarf and Minotaur).
- The goblin jogs keep Mixamo Running (5)'s carried forearms (from Walking, bent forward), not a library arm swing.
- Not run: in-game captures and the headless actor regressions (bindings not applied yet). After applying, run
  `mm8_gog_actor_models_keep_native_tiers_and_palm_fire` (the only `runCase` covering these models; it checks the
  Gog's nine original clips and durations, which are unchanged).

## Rebuild

`scripts/rebuild.sh [mm7_7m452 mm7_m442 mm8_m504 mm8_m612]` composes every export from `work/<name>_pre_gait.glb`
and `jobs/`, runs the gates (both worlds, per tier group) and `check_winding.py`. Probes: `scripts/probes.sh <name>
export/<name>.glb <installed clips> <new clips>`, `scripts/pelvis_probe.py`; viewers `scripts/build_viewers.py
<name> <export> <title> <installed> <new>`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/<name>_gait_h15_claude playback` and `scripts/playback_sheet.py`. The composer is
`../h07`'s copy (h16's plus h02/h04's `raise_arms`). Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h15/export/<name>.glb --world <mm7|mm8> --name <name>.glb`.
A far-LOD repair rerun or any re-export of these models must re-graft these clips (rerun this rebuild on the new
source copied over `work/<name>_pre_gait.glb`).
