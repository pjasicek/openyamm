# Gait rollout package h07: MM7 Fighter Chain, Fighter Leather, Fighter Plate, Swordsman (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the four installed MM7 sword fighters,
all four **installed** (`tools/install_model.py --world mm7`). Existing clips, meshes, skins and materials are
untouched (`scripts/prefix_check.py`: the input's binary chunk is a byte-identical prefix, every input accessor, buffer
view, node, mesh, skin, material and animation unchanged, only animations appended). No Meshy credits or other
spending; sources are humanoid-set library loops (`anim_library/`, never committed). `actors.yml` is not edited here:
the bindings are in [bindings.yml](bindings.yml) for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Fighter Chain A-C (`mm7_m222`) | Walk2: humanoid set Armed-Walk, 0.88 s, 1.8373, 2.09 · Jog: Unarmed-Run-Forward, 0.72 s, 3.3105, 4.60 · Sprint: Unarmed-Sprint, 0.58 s, 4.3626, 7.52 |
| Fighter Leather A-C (`mm7_m226`) | Jog: Unarmed-Run-Forward, 0.74 s, 3.129, 4.23 · Sprint: Unarmed-Sprint, 0.56 s, 4.1051, 7.33 (walk unchanged) |
| Fighter Plate A-C (`mm7_m230`) | Walk2: Armed-Walk, 0.80 s, 1.8664, 2.33 · Jog: Unarmed-Run-Forward, 0.70 s, 3.2987, 4.71 · Sprint: Unarmed-Sprint, 0.58 s, 4.3344, 7.47 |
| Swordsman A-C (`mm7_m406`) | Jog: Unarmed-Run-Forward, 0.74 s, 2.9094, 3.93 · Sprint: Unarmed-Sprint, 0.60 s, 4.0482, 6.75 (walk unchanged) |

Strides are the gate's trusted measurement (vertices and foot joints agree). The installed `Running` (Mixamo Standard
Run + run fit, stride binding 1.8 against a measured 2.08-2.43 that the gate no longer trusted) is no longer bound for
locomotion but stays in the GLB; the Chain and Plate Fighters' `Walking` likewise.

## Why these clips

`gait_gate.py` targets (no candidate): Chain wander 2.29-2.71 / chase 4.58-5.42 / MAW 8.54-8.96 u/s; Leather
2.02-2.42 / 4.04-4.85 / 8.08-8.48; Plate 2.39-3.34 / 4.77-6.68 / 8.11-9.06; Swordsman 1.85-2.35 / 3.70-4.71 /
6.89-7.39. Every chase played `Running` at x1.5-2.0 and every MAW chase at the 2x cap (feet sliding).
The Chain Fighter's `Walking` (Mixamo Female Walk, 1.48 u/s) played Standard A's wander at x1.54, and B/C already
wandered on `Running`; the Plate Fighter's `Walking` (1.71 u/s) would play its C wander at x1.95 once the run is a real
jog. Both get a `Walk2` with a longer stride at a brisk cadence, at the low end of their walk range so tier A does not
crawl. The Leather Fighter's and Swordsman's walks fit (x1.08-1.48) and stay.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Fighter Chain    standard A wander Walk2 x1.10  chase Jog x1.00 | maw A chase Sprint x1.14
                 standard B wander Walk2 x1.20  chase Jog x1.09 | maw B chase Sprint x1.16
                 standard C wander Walk2 x1.30  chase Jog x1.18 | maw C chase Sprint x1.19
Fighter Leather  standard A wander Walking x1.23  chase Jog x0.96 | maw A chase Sprint x1.10
                 standard B wander Walking x1.36  chase Jog x1.05 | maw B chase Sprint x1.13
                 standard C wander Walking x1.48  chase Jog x1.15 | maw C chase Sprint x1.16
Fighter Plate    standard A wander Walk2 x1.02  chase Jog x1.01    | maw A chase Sprint x1.09
                 standard B wander Walk2 x1.23  chase Jog x1.21    | maw B chase Sprint x1.15
                 standard C wander Walk2 x1.43  chase Sprint x0.89 | maw C chase Sprint x1.21
Swordsman        standard A wander Walking x1.08  chase Jog x0.94 | maw A chase Sprint x1.02
                 standard B wander Walking x1.22  chase Jog x1.07 | maw B chase Sprint x1.06
                 standard C wander Walking x1.37  chase Jog x1.20 | maw C chase Sprint x1.10
```

MAW's wander rows (hostile speed, not judged) play a Jog at x0.88-1.00, except Fighter Plate A on Walk2 at x1.74.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h16/scripts/compose_gait.py` (the pilot's composer: legs, pelvis and trunk rhythm from the library loop,
two-bone IK, `lock_stance` planted soles on runs and sprints, the integral plant on walks, `stance_foot: Standing` with
`foot_toe_out_deg: 5`, `foot_smooth`, floor lift, `symmetric_drop`), with h02's `raise_arms` (`arm_out_deg`) and one
addition:

- **`arm_raise_deg` + `arm_raise_window`** (all four Jogs and Sprints, R 25 deg around phase 0.5 / 0.47, half width
  0.25, cosine eased; plus `arm_out_deg` R 6): the four share one sword carry from their `Running` (blade forward and
  down from the hand at the hip while the right arm swings back), and the library run's higher knee drive put the
  rising right thigh into the blade's middle (18-20 % of the loop, 31-37 mm deep on the Chain Fighter, 13 % / 30 mm on
  the Swordsman). The pilot's `clear_arms` (abduction along the skin normal) turned the arm 12-17 deg and left the
  contact at 35 mm, a constant abduction of 10 deg or a constant 12 deg raise still left 30-36 mm; the sword arm is now
  lifted forward and up about the shoulder line only in the half of the loop where the right knee comes through, so it
  keeps its swing elsewhere. Window phases are those of the written (aligned) clip.
- Fighter Plate: its bulky thigh plates take the hands of its `Walking` (33 % / 34 mm left, 13 % / 36 mm right, the
  project's `arm_clear.py` turned the walk out by up to 7 deg). Walk2 uses `arm_out_deg` L 7 / R 6 (0 % after; 22 % /
  28 mm without); the Sprint's free left hand brushed the left thigh plate (3 %, 18 mm) and takes `arm_out_deg` L 6.
- Head bob scaled per clip to the playbook ranges (`bob` 0.15-0.25 for runs, 1.0-1.5 on Walk2); the Chain Fighter's
  Jog uses `symmetric_drop` (its `uneven` read 0.30 without).
- Leather Fighter sprint: 4.1 m at 0.56 s, not 4.3 at 0.58: the shorter legs (k 0.58) dropped the pelvis 11.6 cm to
  reach 4.3 (now 7.8 cm) and showed a toe re-touch after lift-off.

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase (`align: Walking`): Chain 0.20,
Leather 0.17, Plate 0.17, Swordsman 0.18. The installed `Walking` and `Running` already agreed within 0.03-0.06
(`Running` 0.23) on all four.

## Checks (`review/`)

- `<m>_gait_gate.txt` PASSED; `<m>_winding.txt` 0 inverted closed parts on all four.
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R; swing range):
  - Chain Walk2 +4.7 / +5.0 (+5.3..+15.0), Jog +5.0 / +4.9 (-5.3..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5);
    installed Walking +0.6 / +12.1, Running +9.9 / +31.6
  - Leather Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +4.9 (-6.2..+6.5); Walking +9.1 / +6.1, Running +11.6 / +30.9
  - Plate Walk2 +4.8 / +5.0 (+4.8..+15.0), Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5);
    Walking +17.7 / +14.6, Running +20.6 / +37.1
  - Swordsman Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +5.0 (-6.4..+6.5); Walking +9.4 / +9.9, Running +13.0 / +36.0
- Head bob (bob_audit's measure, `bob_probe.py`): Chain Walk2 4.1 %, Jog 6.3 %, Sprint 6.5 %; Leather Jog 5.6 %,
  Sprint 6.0 %; Plate Walk2 4.5 %, Jog 6.2 %, Sprint 6.2 %; Swordsman Jog 4.8 %, Sprint 6.5 %. `uneven` ≤ 0.12 on all.
- Arm and hand gate (`contact_probe.py`, 60 Hz, sword as a probe): 0 % for arms and sword in every new clip. Accepted
  clips for comparison: Chain Walking R 3 % / 23 mm, Leather Walking L 20 % / 29 mm, Plate Walking L 33 % / 34 mm.
  Wrist maxima within the base clips' (45-48 deg; Running 45-49). Arm skin stretch p99 within 0.03 of `Running`'s
  (the Chain Sprint's left max 2.37x equals Running's; Plate Running 4.20x on the right, Sprint 4.00x).
- Lowest skin: 0.0 cm on every new clip. Planted stride per side within 1 % of the binding except Plate Sprint L 4.479
  vs 4.334 (+3 %).
- Playback (`tools/run_creature_review.py check` and `playback`, no console errors; normal and half speed, looked at):
  viewers in `../../mm7_<m>_gait_h07_claude/` (the wrapper needs a direct child of `creatures/`), sheets
  `review/<m>_playback_sheet.png`; Blender filmstrips in `review/iter/`.
- Actor regressions: no model-specific case covers these four (`runCase("mm7_` only has
  `mm7_decoration_models_outdoor_maps`); the generic `mm6_mm7_mm8_actor_models_build_every_binding` and
  `every_map_loads_and_builds_its_actor_models` cover their bindings. Not run here (bindings not applied).

## Doubtful / left open

- The sword arm's raise is a deliberate change to the accepted carry: in the half of the loop where the right knee
  comes forward the sword hand rides up to 25 deg higher (eased), so the blade passes above the thigh.
- Fighter Leather C wanders on its unchanged `Walking` at x1.48, inside the window but at its edge.
- Fighter Plate A's MAW wander (hostile speed, not judged) plays Walk2 at x1.74.
- The jogs and sprints are the humanoid-set run family, not the installed Mixamo Standard Run's style (arms and sword
  are still `Running`'s); jog and sprint read alike from the side, the sprint longer and leaning more.
- Walk-to-run switches change the foot heading (installed walks plant at +6..+18 deg, new clips at 5 deg).
- Not run: in-game captures and the headless regressions (bindings not applied yet).

## Rebuild

`scripts/rebuild.sh [--sources] [m222 m226 m230 m406]` composes the exports from `work/mm7_<m>_pre_gait.glb` and `jobs/`,
then runs `gait_gate.py` and `check_winding.py`; it reproduces the installed sources byte for byte. `--sources`
re-extracts the library loops with Blender (`scripts/extract_source.py`) into `work/sources/` (library-derived, never
commit). Pre-gait sources (rollback: install these with `tools/install_model.py ... --world mm7 --name mm7_<m>.glb` and
drop the bindings), SHA-256: `mm7_m222` 7d5482f8…d204f, `mm7_m226` 0d497cd9…ed80, `mm7_m230` 9a93d02b…db1e,
`mm7_m406` e104ba95…39a5.
Probes: `scripts/probes.sh <m> export/mm7_<m>.glb Walking,Running <new clips> Sword=<assets_source sword glb>`;
filmstrips `scripts/render_review.sh`; viewers `scripts/build_viewers.py <m> <export> <title> Walking,Running <new>
Sword=<sword glb>`, then `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_<m>_gait_h07_claude
playback` and `scripts/playback_sheet.py <m> <clips>`.
Install: `python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h07/export/mm7_<m>.glb --world mm7
--name mm7_<m>.glb`. A far-LOD repair rerun or any re-export of these models must re-graft the new clips (copy the new
source over `work/mm7_<m>_pre_gait.glb` and rerun this rebuild, or graft them with `claude_shared/graft_clips.py`).
