# Gait rollout package h21: MM8 Wererats, Vampire, Dark Dwarf, Skeleton Archer (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM8 sources
(`assets_source/worlds/mm8/models/`; pre-gait copies `work/mm8_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending; sources are local library loops
(`work/sources/`, library-derived, never commit). All five are **installed** (`tools/install_model.py --world mm8`);
`actors.yml` is not edited here: [bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Wererat Ratman Form A-C (`mm8_ratman`, sword, tail) | Sprint: humanoid set Unarmed-Sprint, 0.58 s, 4.3509, 7.50 |
| Wererat Human Form A-C (`mm8_m444`, Smuggler, sword) | Walk2: Mixamo Walk (its own walk's family), 0.86 s, 1.9284, 2.24 · Jog: Unarmed-Run-Forward, 0.70 s, 3.4034, 4.86 · Sprint: Unarmed-Sprint, 0.58 s, 4.5328, 7.82 |
| Vampire (monster) A-C (`mm8_m468`) | Walk2: Mixamo Mutant Walking (its own walk's family), 0.90 s, 1.7799, 1.98 · Jog: Unarmed-Run-Forward, 0.76 s, 3.0055, 3.95 · Sprint: Unarmed-Sprint, 0.60 s, 4.1083, 6.85 |
| Dark Dwarf A-C (`mm8_m632`, two-hand crossbow) | Walk2: humanoid set 2Hand-Crossbow-Walk (its own walk's family), 0.76 s, 1.4009, 1.84 · Sprint: Unarmed-Sprint, 0.53 s, 3.1509, 5.95 |
| Skeletons Archer A-C (`mm8_m628`, skinned longbow) | Walk2: 2Hand-Bow-Walk-Slow, 1.15 s, 1.2501, 1.09 · WalkFast (bound as `run`): 2Hand-Bow-Walk (its own walk's source), 0.84 s, 1.8966, 2.26 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree; planted soles within 1 % except the
archer's right boot, below).

## Why these clips (targets from `gait_gate.py`, model units/s)

- **Ratman** (0.85 m leg): wander 2.62-2.91, chase 5.24-5.82 fit the installed Walking (2.33) and Running (4.30) at
  x1.12-1.35; only MAW's chase (8.44-8.73) played Running at the 2x cap. One Sprint.
- **Wererat human form** (Smuggler, 0.79 m leg): the installed Running is a short Mixamo run (1.98 m, 2.70 u/s) whose
  stride the gate no longer trusts (vertices 2.13 / feet 1.27); chase 4.86-5.63 played it at x1.80-2.00 and B/C
  wandered on it. Walking (1.77) would play C's wander at x1.59. Walk2 (longer stride, brisk cadence), Jog, Sprint.
- **Vampire** (0.80 m leg): its Mutant-walk stalk (1.27 u/s) played wandering (1.92-2.27) at x1.51-1.79; MAW's chase
  (7.16-7.51) Running at x1.86-1.95. The gate also fails the installed Running's stride (measured 0.59 / feet 1.30
  against the bound 2.82: not trusted), so the Standard chase (3.84-4.54, Froude 2-2.1: a run) gets a Jog too.
- **Dark Dwarf** (0.57 m leg): C's wander (2.36) played Walking (1.51) at x1.57; MAW's chase (7.09-7.42) Running at
  x1.79-1.88. The installed Running (3.95) still fits Standard's chase (x1.03-1.20) and stays.
- **Skeleton Archer** (0.98 m leg; tier C is scaled 117 against A/B's 140, so it moves faster in model units): the
  installed Walking (2.81 u/s) was bound as both walk and run (walk-as-run); wander 0.99-1.36 played it at x0.35-0.49,
  A's chase (1.99) at x0.71. MAW leaves the speeds unchanged (no sprint). Walk2 is a slow walk for wandering; the chase
  (Froude 0.40-0.46 on A/B: a walking pace) keeps the walk-as-run decision with a shorter-stride brisk walk, `WalkFast`.
  Tier C's chase (2.73) is Froude 0.75, just above the 0.65 walking limit; one run-slot clip serves all three tiers
  (A x0.88 .. C x1.21), and a walk was kept (doubt below).

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Ratman       standard A wander Walking x1.12  chase Running x1.22 | maw A chase Sprint x1.12
             standard B wander Walking x1.21  chase Running x1.31 | maw B chase Sprint x1.15
             standard C wander Walking x1.25  chase Running x1.35 | maw C chase Sprint x1.16
Wererat hum. standard A wander Walk2 x1.08    chase Jog x1.00     | maw A chase Sprint x1.06
             standard B wander Walk2 x1.17    chase Jog x1.08     | maw B chase Sprint x1.08
             standard C wander Walk2 x1.26    chase Jog x1.16     | maw C chase Sprint x1.11
Vampire      standard A wander Walk2 x0.97    chase Jog x0.97     | maw A chase Sprint x1.05
             standard B wander Walk2 x1.06    chase Jog x1.06     | maw B chase Sprint x1.07
             standard C wander Walk2 x1.15    chase Jog x1.15     | maw C chase Sprint x1.10
Dark Dwarf   standard A wander Walk2 x1.10    chase Running x1.03 | maw A chase Sprint x1.19
             standard B wander Walk2 x1.19    chase Running x1.11 | maw B chase Sprint x1.22
             standard C wander Walk2 x1.28    chase Running x1.20 | maw C chase Sprint x1.25
Skel. Archer standard/maw A wander Walk2 x0.91  chase WalkFast x0.88
             standard/maw B wander Walk2 x0.98  chase WalkFast x0.94
             standard/maw C wander Walk2 x1.25  chase WalkFast x1.21
```

MAW's wander rows (hostile speed, not judged): Ratman Running x0.98-1.02, Vampire Jog x0.91-0.95, Dark Dwarf Running
x0.90-0.94, Wererat human form B/C Jog x0.87-0.89 but **A on Walk2 at x1.84** (4.13 u/s sits between Walk2 and Jog).

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h07/scripts/compose_gait.py` (h16's composer plus h02's `raise_arms` and h07's `arm_raise_deg`
window) with h01's `even_bob` and h19's `track_out` merged in. Legs, pelvis and trunk rhythm from the library loop,
two-bone IK, `lock_stance` planted soles on jogs and sprints, the integral plant on walks, `stance_foot: Standing` with
`foot_toe_out_deg: 5`, `foot_smooth`, floor lift; arms, hands, props and the ratman's tail from the model's own clip
(`base`: Running for jogs and sprints, Walking for walks), phase-aligned. Per model:

- **Ratman Sprint**: `even_bob`; the sword arm lifted 12 deg forward only around phase 0.17 (`arm_raise_window`
  [0.17, 0.2]): the sprint's knee drive met the right forearm (24 mm, 3 % of the loop); free left arm turned out 9 deg
  (`arm_out_deg`; the pilot's skin-normal clearance had turned it 6 deg for a 23 mm contact).
- **Wererat human form**: Jog and Sprint `even_bob` + `symmetric_drop`, sword prop cleared, free left arm cleared by
  the composer's clearance (`clear_sides: L`); Walk2 `bob` 0.75 (5.9 % at 1.0).
- **Vampire**: Walk2 `bob` 0.2 (the Mutant walk's hip bob gave 8.7 % at 0.5); Jog and Sprint `even_bob` +
  `symmetric_drop`, arm gain 1.3 on the sprint. No cloth (the open vest is skinned to the trunk; no cape).
- **Dark Dwarf**: Walk2 `swing_height` 1.6 (the scaled crossbow walk shuffled: stance 0.96 / 0.85, now 0.77 / 0.66);
  Sprint `arms_raise_deg` 5 (both arms and the crossbow as one rigid piece, the grip unchanged), `swing_height` 1.15.
- **Skeleton Archer**: both walks `even_bob`, `ground_sigma` 1.5 (the default per-frame grounding let both feet rise
  1.9 cm at A/B's scale for one key, which the floor audit's walking rule fails); the skinned bow, string and arrow
  channels come from `Walking`.

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase (`align: Walking`): Ratman 0.75
(installed Running 0.88), Wererat human form 0.17 (Running 0.23), Vampire 0.26 (Running 0.23), Dark Dwarf 0.75, Skeleton
Archer 0.75. **The Dark Dwarf's installed Walking and Running are half a loop apart** (left foot forward-most 0.75 vs
0.23); new clips follow the walk, so its Walk2/Sprint and its kept Running still disagree by half a loop.

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all five (`review/<m>_winding.txt`). `prefix_check.py` ok.
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R, swing range):
  - Ratman Sprint +5.1 / +5.0 (-4.3..+6.5); installed Walking +2.3 / +1.8, Running +5.6 / +2.4
  - Wererat human form Walk2 +3.0 / +4.7 (+0.2..+15.9), Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5);
    Walking +4.9 / +0.3, Running +7.0 / +23.4
  - Vampire Walk2 +4.4 / +4.5 (+4.8..+24.2, the Mutant walk's toe-off roll), Jog +5.0 / +4.9, Sprint +5.1 / +4.9;
    Walking +23.4 / +19.3, Running +19.5 / +18.8
  - Dark Dwarf Walk2 +3.9 / +4.5 (+3.7..+13.2), Sprint +5.1 / +5.0 (-6.4..+6.5); Walking +7.2 / +8.2, Running +23.2 / +14.0
  - Skeleton Archer Walk2 +4.0 / +4.5 (+3.7..+12.8), WalkFast +4.0 / +4.5; Walking +1.8 / +2.6
- Head bob (bob_audit's measure, `bob_probe.py`; `uneven`): Ratman Sprint 5.7 % (0.39; its accepted Running 0.86,
  the remainder is Running's neck/head channel, `scripts/uneven_probe.py`: pelvis k1 0.1 cm, head k1 1.2 cm); Wererat
  human Walk2 4.6 % (0.29), Jog 6.1 % (0.03), Sprint 6.2 % (0.05); Vampire Walk2 4.3 % (0.26), Jog 4.3 % (0.03), Sprint
  5.0 % (0.04); Dark Dwarf Walk2 3.1 % (0.28), Sprint 5.9 % (0.07); Skeleton Archer Walk2 3.9 % (0.62), WalkFast
  3.5 % (0.87; its accepted Walking 3.2 %, 0.69: a boot on one leg and a bare bone foot on the other ground unevenly).
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/finger/prop inside legs or trunk): 0 % in every new clip
  except Dark Dwarf Sprint left forearm-twist 3 % / 7 mm against the belt (its accepted Running 2 % / 4 mm). Props:
  ratman and wererat swords, crossbow 0 %. Wrist maxima equal the base clips'. Arm skin stretch p99 within 0.02 of
  the base clip's (Wererat human Sprint left max 2.39x vs Running 2.15x; Vampire Sprint right max 1.98x vs 1.83x).
- Lowest skin: within 0.2 cm of the floor in every new clip (none below -1 cm).
- Planted stride per side (`stride_probe.py`): within 1 % of the binding except the Skeleton Archer's right boot
  (Walk2 1.329 vs 1.250, WalkFast 1.966 vs 1.897; its few planted sole vertices, 467-645 samples).
- Playback (`tools/run_creature_review.py check` and `playback`: no console errors, normal and half speed, looked at):
  viewers in `../../mm8_<m>_gait_h21_claude/review/` (the wrapper needs a direct child of `creatures/`), sheets
  `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/`.
- Headless actor regressions on the installed GLBs (current bindings, `review/regression_*.log`), all PASS:
  `mm8_ratman_actor_models_keep_native_roles`, `mm8_smuggler_human_actor_models_keep_tiers_roles_and_palm_cast`,
  `mm8_dark_dwarf_actor_models_keep_tiers_crossbow_and_native_roles`,
  `mm8_skeleton_archer_actor_models_keep_tiers_and_arrow_release`, `mm6_mm7_mm8_actor_models_build_every_binding`
  (the only suite case that covers the Vampire `mm8_m468`). Unit tests `*Vampire*`, `*Smuggler*`, `*Ratman*`,
  `*Dark Dwarf*`, `*Skeleton Archer*`: 5 cases pass.

## Doubtful / left open

- Skeleton Archer tier C chases at Froude 0.75 on a walk (`WalkFast` x1.21), just above the brief's 0.65 walking limit;
  A/B are 0.40-0.46. A per-tier slow jog for C alone would be the alternative; kept the walk-as-run decision because
  one clip covers all tiers in the window and archers read as stalking undead. Its right boot's planted stride reads
  3-6 % long (a small sole patch), and the gate's own measurement (trusted) is bound.
- Wererat human form A's MAW wander (not judged) plays Walk2 at x1.84.
- Dark Dwarf: Walking/Running half a loop apart (above); its Sprint re-touches the right toe briefly after lift-off
  (phase 0.47-0.54, the humanoid-set sprint's toe on a short leg, as h02's BDwarf).
- New clips plant at 5 deg toe-out while the accepted Vampire and Dark Dwarf runs plant at 14-23 deg; the heading
  changes at walk/run switches.
- The Ratman Sprint leans hard (trunk 16 deg on top of its hunched carry): a rat-like dash; the sword hand rides 12 deg
  higher for a fifth of the loop.

## Shared tools

No problem found in `claude_shared/` tools. Note: `contact_probe.py` (package copy) reports forearm-twist hits that
`inside_where.py` does not list (it scans at the same times; the dwarf's 7 mm hit was located with an inline copy of
the probe's loop). `gait_gate.py` takes ~2 min per model.

## Rebuild

`scripts/rebuild.sh [--sources] [ratman m444 m468 m628 m632]` composes the exports from `work/mm8_<m>_pre_gait.glb`
and `jobs/`, then runs `gait_gate.py` and `check_winding.py`; it reproduces the installed exports
(`work/exports.sha256`). `--sources` extracts the humanoid-set loops with Blender (`scripts/extract_source.py`);
`Walk.npz` and `Mutant_Walking.npz` (Mixamo) are copied from `../h19/work/sources/`. Probes:
`scripts/probes.sh <m> <export> <old clips> <new clips> [node=prop.glb]`, `scripts/uneven_probe.py`; filmstrips
`scripts/render_review.sh`; viewers `scripts/build_viewers.py <m> <export> <title> <old> <new> [node=prop.glb]`, then
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_<m>_gait_h21_claude playback` and
`scripts/playback_sheet.py <m> <clips>`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h21/export/mm8_<m>.glb --world mm8 --name mm8_<m>.glb`. Rollback:
install `work/mm8_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or reduction rerun
on these models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
