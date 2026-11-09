# Gait rollout package h19: MM8 Ogre Warrior, Cyclops, Ogre Mage, Ogre Peasant (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the four installed MM8 sources
(`assets_source/worlds/mm8/models/`; pre-gait copies `work/mm8_<m>_pre_gait.glb` = assets_source commit `d4c87ca`,
SHA-256 m440 `c2d055ec…`, m520 `007b9676…`, m540 `9d140fbb…`, m436 `cb8a3e29…`). Existing clips, meshes, skins and
materials are untouched (`scripts/prefix_check.py`: input binary chunk a byte prefix, only animations appended). No
Meshy credits or other spending; sources are local library loops (`work/sources/`, never committed). All four are
**installed** (`tools/install_model.py --world mm8`); `actors.yml` is not edited: [bindings.yml](bindings.yml).

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Ogre Warrior A-C (`mm8_m440`, club) | Jog: humanoid set Unarmed-Run-Forward, 0.74 s, 2.7509, 3.72 · Sprint: Unarmed-Sprint, 0.63 s, 3.5983, 5.71 |
| Cyclops A-C (`mm8_m520`) | Jog: Unarmed-Run-Forward, 0.84 s, 3.7053, 4.41 · Sprint: Unarmed-Sprint, 0.70 s, 4.8166, 6.88 |
| Ogre Mage A-C (`mm8_m540`, wand, cape, tunic) | Walk2: Armed-Walk, 0.98 s, 1.3252, 1.35 · Jog: Unarmed-Run-Forward, 0.78 s, 2.2798, 2.92 · Sprint: Unarmed-Sprint, 0.62 s, 3.3136, 5.34 |
| Ogre Peasant A-C (`mm8_m436`, Wimp) | Walk2: Mixamo Orc Walk (1) (its own Walking's family), 1.2 s, 1.2383, 1.03 |

Strides are `gait_gate.py`'s trusted measurements (planted soles agree within 1 %: `review/<m>_probes.txt`).

## Choices per body

- **Ogre Warrior**: heavy run and low powerful sprint as the pilot's MM6 Ogre (same jobs scaled to its 0.71 m leg:
  jog 3.9 and sprint 5.1 leg lengths per stride); arms and club from its own `Running`. Its `Walking` stays for wandering
  (x1.32-1.46, inside the window). `Running` (stride untrusted, 0.73 s) is no longer bound for locomotion.
- **Cyclops** (1.0 m leg): the same family at the same Froude-scaled pace (jog x0.96-1.07, sprint x0.99-1.03); arms
  from its slow `Running` (the boulder is hidden in locomotion clips). `Walking` stays.
- **Ogre Mage**: its chase (2.6-3.2 u/s on a 0.86 m hip, Froude 0.8-1.2) is a run pace, so it jogs in Standard (the
  walk-as-run binding of tier A ends; all tiers now share one binding). `Walking` (1.99 u/s) played wandering at x0.66,
  so `Walk2` is a shorter-stride walk (1.33 at 0.98 s). The installed `Walking` and `Running` are half a loop apart (left
  foot forward-most 0.75 vs 0.28): every new clip follows the walk (0.75). Jog and sprint: lower swing
  (`swing_height` 0.8), mild lean; the tunic's `LoinFront` flap is re-keyed by the project's own rule (leading thigh
  angle from bind x 1.20 + 12 deg, `../../mm8_m540_claude/scripts/finish_pilots.py`; capped at 100 deg). It
  reproduces the installed `Walking` flap (median 0.0 deg, max 4.2), `Running` within median 5.9 deg (that clip was
  re-solved by the head-bob pass after its flap was keyed). The cape comes from `Running`, phase-aligned.
- **Ogre Peasant** (Wimp, flees at 2.10 u/s, Froude 0.52 on its 0.86 m hip): a walking pace, so the user's walk-as-run
  decision for the Ogre peasant holds: flight keeps `run: Walking` (x1.49). Only the wander (1.05 u/s, `Walking`
  x0.74) needed a clip: `Walk2`, the same Orc Walk family at a shorter stride, `track_out` 0.11 m per side (the scaled
  source's ankles were 0.15 m out against the accepted walk's broad 0.26 m: knees knocked), a higher swing
  (`swing_height` 1.7: the Orc walk's low clearance scraped the toes), right-arm clearance (3.3 deg outward; the
  wider legs met the hanging right hand).

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Ogre Warrior  standard A wander Walking x1.32  chase Jog x0.98 | maw A chase Sprint x1.00
              standard B wander Walking x1.41  chase Jog x1.05 | maw B chase Sprint x1.02
              standard C wander Walking x1.46  chase Jog x1.08 | maw C chase Sprint x1.03
Cyclops       standard A wander Walking x0.96  chase Jog x0.96 | maw A chase Sprint x0.99
              standard B wander Walking x1.00  chase Jog x1.00 | maw B chase Sprint x1.00
              standard C wander Walking x1.07  chase Jog x1.07 | maw C chase Sprint x1.03
Ogre Mage     standard A wander Walk2 x0.97    chase Jog x0.90 | maw A chase Sprint x0.99
              standard B wander Walk2 x1.07    chase Jog x0.99 | maw B chase Sprint x1.01
              standard C wander Walk2 x1.17    chase Jog x1.08 | maw C chase Sprint x1.04
Ogre Peasant  standard A-C wander Walk2 x1.02  flee Walking x1.49 | maw: same speeds (MAW leaves them unchanged)
```

MAW's wander rows (hostile speed, not judged): Ogre Warrior plays `Walking` at the 2x ceiling (slides 1.03-1.07),
Cyclops `Walking` x1.55-1.60, Ogre Mage `Jog` x0.90-0.95.

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all four (`review/<m>_winding.txt`).
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R, swing range):
  - Ogre Warrior Jog +5.0 / +4.9 (-5.2..+7.4), Sprint +5.1 / +4.9 (-6.4..+6.5); installed Walking +18.0 / +23.7
  - Cyclops Jog +5.0 / +4.9 (-5.3..+7.4), Sprint +5.1 / +4.9 (-6.4..+6.6); Walking +9.4 / +18.0
  - Ogre Mage Walk2 +4.6 / +5.0 (+3.7..+15.0), Jog +5.0 / +4.9, Sprint +5.1 / +5.0; Walking +1.5 / +5.6
  - Ogre Peasant Walk2 +3.6 / +2.8 (-4.6..+10.2); Walking +33.0 / +16.3 (its Orc walk's duck feet)
- Head bob (bob_audit's measure, `bob_probe.py`): Ogre Warrior Jog 4.2 % / Sprint 6.3 %; Cyclops 4.6 / 5.6; Ogre Mage
  Walk2 3.5, Jog 3.9, Sprint 5.8; Ogre Peasant Walk2 4.4. `uneven` 0.06-0.31.
- Arm and hand gate (contact probe, 60 Hz, forearm/hand/finger/prop inside legs or trunk): 0 % in every new clip
  except Ogre Peasant Walk2 left hand 1 % / 6 mm (its accepted Walking: right 3 % / 9 mm). Club and wand 0 %. Wrist
  maxima equal the base clips' (134 / 82 / 47 / 45 deg). Arm skin stretch p99 within 0.1 of the base clip's (Ogre
  Warrior Sprint left max 8.8x on the armpit edge that reads 7.8x in its accepted `Running`).
- Mage tunic (`skirt_poke_probe.py`, env `SKIRT_BONES=LoinFront`): Walk2 0 %, Jog 8 % (67 mm), Sprint 5 % (10 mm);
  the hits are the raised knee in front of the lifted flap's side edge (hip close-ups `review/iter/m540hip_*.png` show
  no cloth through the thigh). Before the flap rule: Jog 33 % / 114 mm.
- Lowest skin 0.0 cm on every new clip (sprints included). Phase: every new clip puts the left foot forward-most at the
  model's `Walking` phase (0.25; Mage 0.75).
- Playback with `tools/run_creature_review.py` (`check`: no console errors; `playback` at normal and half speed),
  viewers in `../../mm8_<m>_gait_h19_claude/review/`, sheets `review/<m>_playback_sheet.png`; Blender filmstrips
  `review/iter/`.

## Doubtful / left open

- The Ogre Warrior's wander plays `Walking` at x1.32-1.46 (inside the window, near its top), and MAW's hostile wander
  slides at the 2x ceiling. A brisker Walk2 would centre both; not made (not a gate failure).
- The Ogre Peasant flees on `Walking` at x1.49, just inside the window (the walk-as-run decision; Froude 0.52). The
  rollout README's "peasants jog" note is for MM6 peasants at 2.5-2.7 u/s; this one is slower for its size. A brisk
  walk or civilian jog for the flight would be the next step if x1.49 reads hurried in game.
- Ogre Peasant Walk2: the left toe brushes within 1.5 cm of the floor just after lift-off (phase 0.99-0.06, the Orc
  walk's low clearance); no penetration. Walk2 to Walking switches change the toe-out (5 deg vs the accepted 33 / 16).
- Ogre Mage Jog head bob 3.9 % is just under the 4-7 % run target (bob_audit's run range 3-8.5).
- New clips plant at 5 deg toe-out while the accepted Walkings plant at 9-33 deg (Cyclops, Warrior, Peasant): the foot
  heading changes at walk-to-run switches.
- Not run: in-game captures and the headless actor regressions (bindings not applied yet). After `apply_bindings.py`,
  run `mm8_cyclops_actor_models_keep_tiers_and_boulder_release` and
  `mm8_ogre_mage_actor_models_keep_tiers_roles_and_wand_cast` (no suite case covers m440 or m436; their unit tests
  `*Ogre peasant*`, `*Ogre keeps club*`, `*Ogre actor bindings*` only check clips present and the bindings' model,
  skin, scale and club).

## Composer changes (`scripts/compose_gait.py`, a copy of h16's)

- `loincloth` (h16's leading-thigh flap) takes `gain` and `rest_relative` (thigh angle from its bind direction).
- `track_out` (from h08): each ankle further out.
- `scripts/render_clip.py`: `hip` and `hipq` close-up views (env `HIP_Z`); `scripts/skirt_poke_probe.py` (h08's)
  takes `SKIRT_BONES`.

## Rebuild

`scripts/rebuild.sh [--sources] [m440 m520 m540 m436]` composes the exports from `work/mm8_<m>_pre_gait.glb` (or
assets_source commit `d4c87ca`) and `jobs/`, then runs `gait_gate.py` and `check_winding.py`; it reproduces the
installed exports byte for byte (`work/exports.sha256`). `--sources` extracts the four library loops with Blender.
Probes: `scripts/probes.sh <m> <export> <old clips> <new clips> [node=prop.glb]`; filmstrips `scripts/render_review.sh`;
viewers `scripts/build_viewers.py`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_<m>_gait_h19_claude playback` and `scripts/playback_sheet.py`. Install:
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h19/export/mm8_<m>.glb --world mm8`.
Rollback: install `work/mm8_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or
reduction rerun on these models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
