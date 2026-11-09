# Gait rollout package h18: MM8 Dark Elf peasants and warrior, Ether Knight, Cleric (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM8 sources
(`assets_source/worlds/mm8/models/`; pre-gait copies and rollback `work/mm8_<m>_pre_gait.glb`, SHA-256 in
`work/pre_gait.sha256`). Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the
input's binary chunk is a byte-identical prefix, only animations appended). No Meshy credits or other spending; the
sources are humanoid-set library loops (`work/sources/`, library-derived, never commit). All five are **installed**
(`tools/install_model.py --world mm8`; `work/exports.sha256` = the installed sources). `actors.yml` is not edited
here: [bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Dark Elf Peasant Male (`mm8_m424`, dagger) | Walk2: Relax-Walk-Forward (his Walking's source), 1.05 s, 1.2616, 1.20 |
| Dark Elf Peasant Female (`mm8_m428`, dagger, 16-chain dress) | Walk2: Relax-Walk-Forward, 1.05 s, 1.2143, 1.16 (dress simulated) |
| Dark Elf Warrior (`mm8_m432`, two-handed sword) | Walk2: Armed-Walk, 0.92 s, 1.9152, 2.08 · Jog: Unarmed-Run-Forward, 0.65 s, 2.6637, 4.10 · its `Running` bound as sprint (3.509, 5.85) |
| Ether Knight (`mm8_m604`, right-hand sword) | Walk2: Relax-Walk-Forward, 1.00 s, 1.6253, 1.63 · Jog: Unarmed-Run-Forward, 0.73 s, 2.3136, 3.17 · Sprint: Unarmed-Sprint, 0.62 s, 3.5859, 5.78 |
| Cleric (`mm8_m460`, staff, 16-chain closed robe) | Jog: Unarmed-Run-Forward, 0.72 s, 2.2160, 3.08 (robe simulated, staff lifted off the floor) |

Strides are `gait_gate.py`'s trusted measurements (vertices and feet agree; planted soles per side within 2 %,
`review/<m>_probes.txt`).

## Why, per model (targets: `review/mm8_<m>_gate_installed.txt`)

Froude v^2 / (g x thigh-joint height) decides walk-as-run (thigh heights 0.897 / 0.929 / - / 0.978 / 0.937 m).

- **Peasant Male**: wandered at 1.22 on the 1.78 u/s `Walking` (x0.68): a slower `Walk2`. He flees at 2.43 on his
  `Running` (x0.89, unchanged). MAW leaves the speeds unchanged.
- **Peasant Female**: wandered at 1.18 on `Walking` (x0.61): a slower `Walk2`. She flees at 2.36 (Froude 0.61): the
  post-process walk-as-run decision holds, `Walking` stays her run (x1.21). Her unbound `Running` is not used.
- **Warrior**: Standard chase 3.99-4.65 played the 5.85 u/s `Running` at x0.68-0.80 and C wandered at 2.33 on the
  1.53 u/s `Walking` (x1.52): a `Walk2` (2.08) and a `Jog` (4.10). MAW chases at 6.98-7.31, which the installed
  `Running` covers at x1.19-1.25: bound as `sprint` (the brief's "run bound as sprint") instead of a new clip.
- **Ether Knight**: A/B wandered on the 2.24 u/s `Walking` at x0.66/0.72 and C chased on `Running` at x0.67: `Walk2`
  and `Jog`. With `Jog` as the run, MAW's chase (5.48-5.88) needs a sprint: the installed `Running` cannot serve (its
  stride is unmeasurable: vertices 5.18, feet 2.59, stance 3-14 %, bob 11.5 %; `gait_gate.py` FAILED it as sprint),
  so a new `Sprint`.
- **Cleric** (caster; MAW unchanged): chased on `Walking` (run aliased to it) at x1.52-1.90; chase 2.89-3.62 is a run
  pace (Froude 0.91-1.43): a robe-safe `Jog`, as h03's MM6 Sorcerer and Cleric.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Peasant Male     standard/maw A-C  wander Walk2 x1.01  chase Running x0.89
Peasant Female   standard/maw A-C  wander Walk2 x1.02  chase Walking x1.21
Dark Elf Warrior standard A wander Walk2 x0.96  chase Jog x0.97 | maw A chase Running (sprint) x1.19
                 standard B wander Walk2 x1.04  chase Jog x1.05 | maw B chase Running (sprint) x1.22
                 standard C wander Walk2 x1.12  chase Jog x1.14 | maw C chase Running (sprint) x1.25
Ether Knight     standard A wander Walk2 x0.90  chase Jog x0.93 | maw A chase Sprint x0.95
                 standard B wander Walk2 x0.99  chase Jog x1.01 | maw B chase Sprint x0.97
                 standard C wander Walk2 x1.15  chase Jog x1.18 | maw C chase Sprint x1.02
Cleric           standard/maw A wander Walking x0.76  chase Jog x0.94
                 standard/maw B wander Walking x0.85  chase Jog x1.06
                 standard/maw C wander Walking x0.95  chase Jog x1.18
```

MAW's wander rows (hostile speed, not judged): Warrior A/B on Walk2 x1.68-1.72 (C on Jog x0.89), Ether Knight A on
Walk2 x1.69 (B/C Jog x0.89-0.93).

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h03/scripts/compose_gait.py` (h09/h21/h16 lineage: library legs, pelvis and trunk rhythm, two-bone IK,
`lock_stance`, `stance_foot: Standing`, `foot_smooth`, `even_bob`, `symmetric_drop`, `soles_feet_only`, h03's `cloak`
hook) with h06's per-side `foot_toe_out_deg` and h04's `prop_floor` (`lift_prop`, copied unchanged). Arms, hands and
props come from the model's own `Walking` (walks, Cleric jog) or `Running` (Warrior and Knight jog and sprint),
phase-aligned; every new clip is aligned to the model's `Walking` (left foot forward-most at 0.75; the Warrior 0.24).
Additions here:

- `cloak.py` presets **`m460`** (the MM8 Cleric's `robe_sim.py`: the MM6 Sorcerer's bake with MARGIN 0.022, FLOOR
  0.025) and **`m428`** (her `dress_sim.py`, the same bake on `Dress_` chains; its other changes are Death-only).
  Chain rest points dumped from the rig blends (`mm8_m428_claude/work/rig_sim.blend`,
  `mm8_m460_claude/work/motion_final.blend`), identical to the GLB bind heads (0.0 mm, `chains_check.py`). Port check
  against the installed bakes (`cloak_check.py`, chain joints): Cleric Walking median 0.4 / p95 1.1 / max 3.5 cm;
  Female Running 1.5 / 3.4 / 5.5 cm, Walking 1.6 / 8.6 / 11.7 cm (her Walking's arms were re-solved after its bake).
- `soles_feet_only: "no_cloth"` also skips `Dress_` chain vertices.
- `scripts/robe_spread_probe.py`: hem chain ends' distance from the pelvis axis (how far a robe bells out).

Per model: walks use the integral plant with per-frame grounding (`ground_every_frame`), `bob` 1.5-1.7; Warrior
`Walk2` from Armed-Walk (his `Walking`'s Great Sword walk legs and the 2Hand-Sword walks limp under the composer:
uneven 0.37-0.62); Knight `Walk2` from Relax-Walk (Armed-Walk planted 1.43 / 1.63 per side). Feet are planted at 5 deg
toe-out on the foot mesh (`foot_mesh_heading_probe.py`): joint-line values per side Male {3.0, 4.0}, Female {0.2,
-2.6}, Warrior Walk2 {7.5, 2.3} / Jog {7.2, 3.3}, Knight {-1, -2}, Cleric {-1.6, 11.8}. Cleric Jog: `swing_height`
0.4, spine weight 0.3, robe `leg_pad` 0.02 (0: knees through the back 86 % of samples, 20 mm), staff `prop_floor`
(the walking-staff carry put its foot 5.8 cm under the floor; the staff arm turns up by up to 31 deg).

## Checks (`review/`)

- `check_winding.py` 0 inverted closed parts on all five (`<m>_winding.txt`); `prefix_check.py` ok.
- Foot heading on the mesh, planted L / R (deg toe-out): Male Walk2 +5.4 / +4.9 (Walking +3.8 / +1.6); Female Walk2
  +5.0 / +5.0 (Walking +4.3 / +7.4); Warrior Walk2 +4.8 / +5.1, Jog +4.7 / +5.1 (Walking -16.4 / +41.9 and Running
  -6.4 / +23.9: his guard stance); Knight Walk2 +4.7 / +5.0, Jog +5.1 / +5.2, Sprint +5.2 / +5.5 (Walking +5.1 / +8.4);
  Cleric Jog +5.2 / +4.4 (Walking +6.9 / -5.6). Swing feet within -8.5..+11.7 deg on the joints.
- Head bob (bob_audit's measure; `uneven`): Male Walk2 4.0 % (0.08); Female Walk2 3.8 % (0.06); Warrior Walk2 4.4 %
  (0.04), Jog 6.1 % (0.14); Knight Walk2 3.4 % (0.08), Jog 5.1 % (0.04), Sprint 5.6 % (0.03); Cleric Jog 4.8 % (0.01).
- Arm and hand gate (`contact_probe.py`, 60 Hz, props as probes): 0 % for arms and props in every new clip, except
  where the accepted walks already are: Male left hand at the hip (Walk2 52 % / 16 mm; Walking 47 % / 14 mm), Female
  hands on the dress (Walk2 L 59 % / 22 mm, R 40 % / 10 mm; Walking 55 % / 19 mm, 39 % / 12 mm). Wrist maxima equal the
  base clips'; arm skin stretch p99 equal to the base clips' (Warrior Jog L max 2.53 vs Running 2.37).
- Garments: Female dress poke (`skirt_poke_probe.py`, SKIRT_BONES=Dress_) Walk2 0 % (Walking 0 %, Running 35 %);
  Cleric robe Jog 0 % (Walking 20 % / 6 mm). Cleric hem spread p95 0.44 m (Walking 0.39), back 0.47 (0.40).
- Props lowest: Warrior sword 75.7 / 104.4 cm (Walking 67.5); Knight sword 52.3-97.1 cm (Walking 52.0); Cleric staff
  foot +2.7 cm (Walking +0.6). Lowest skin within 0.25 cm of the floor (none below -1 cm).
- Playback (`tools/run_creature_review.py check` / `playback` / `shots`: no console errors, every clip switch, normal
  and half speed; looked at): viewers in `../../mm8_<m>_gait_h18_claude/review/`, sheets
  `review/<m>_playback_sheet.png`, side/front shots `review/<m>_*shots.png`.
- Actor regressions on the installed GLBs with the current (unapplied) bindings (`scripts/regressions.sh`,
  `review/regression_*.log`), all pass: `mm8_dark_elf_peasant_actor_models_keep_native_roles`,
  `mm8_dark_elf_female_peasant_actor_models_keep_native_roles`, `mm8_dark_elf_warrior_actor_models_keep_native_roles`,
  `mm8_ether_knight_actor_models_keep_tiers_sword_and_simulation`, `mm8_cleric_actor_models_keep_tiers_roles_and_staff_cast`,
  `mm6_mm7_mm8_actor_models_build_every_binding`, `every_map_loads_and_builds_its_actor_models`. None checks a clip
  count; they check that the installed clips exist with their lengths (and that the female has no Attack/Cast), which
  the new names do not touch.

## Doubtful / left open

- Warrior: his installed `Running`, now bound as the MAW sprint, limps (bob 7.8 %, `uneven` 0.68) and plants the right
  foot 24 deg out; accepted clip, not changed. A new Sprint near 6.7 u/s would play x1.04-1.09 instead of x1.19-1.25.
  His new clips plant both feet at 5 deg where his walk and run keep a guard stance (right foot 24-42 deg out): the
  foot heading changes at the walk/run switch.
- Cleric: the robe bells out more in the jog than in the walk (hem p95 +5 cm) and the knee pushes the front panel
  forward visibly; a floor-length robe at a run pace, as h03's Sorcerer. The staff is carried off the floor in the jog
  (the walk plants it like a walking staff).
- Female: the dress bake port differs from her installed Walking more than the others (p95 8.6 cm; her Running 3.4 cm),
  likely because her arms were re-solved after the bake; Walk2 is simulated fresh and pokes nothing.
- Ether Knight and both peasants: `Running` is half a loop out of phase with `Walking` (installed; left as it is). The
  new clips follow `Walking`; the Male's run switch keeps that installed half-loop jump.

## Shared tools

No problem found in `claude_shared/`. `gait_gate.py` correctly failed the Ether Knight's `Running` as a sprint
(untrusted stride).

## Rebuild

`scripts/rebuild.sh [--sources] [m424 m428 m432 m604 m460]` composes the exports from `work/mm8_<m>_pre_gait.glb`,
`jobs/` and `work/sources/` (copies of `../h17/work/sources/` plus the 2Hand-Sword walks extracted with `--sources`)
and the chain files, then runs `gait_gate.py` with the bindings.yml values, `check_winding.py` and `prefix_check.py`;
it reproduces the installed sources byte for byte (`work/exports.sha256`). Probes: `scripts/probes.sh <m>
export/mm8_<m>.glb <old clips> <new clips> [node=prop.glb ...]`, `foot_mesh_heading_probe.py`, `prop_low_probe.py`,
`skirt_poke_probe.py`, `robe_spread_probe.py`, `cloak_check.py`; viewers `scripts/build_viewers.py <m> <export>
<title> <old> <new> [node=prop.glb ...]`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_<m>_gait_h18_claude playback`, `scripts/playback_sheet.py`, `scripts/shots_strip.py`;
regressions `scripts/regressions.sh`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h18/export/mm8_<m>.glb --world mm8 --name mm8_<m>.glb`. Rollback:
install `work/mm8_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or reduction rerun
on these models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
