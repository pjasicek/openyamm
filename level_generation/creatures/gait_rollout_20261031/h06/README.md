# Gait rollout package h06: MM6 Demon, Guard, BGoblin, Skeleton, LizardArch, ElemEarth (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the six installed MM6 sources
(`assets_source/worlds/mm6/models/`; pre-gait copies `work/mm6_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending; the sources are local library
loops (`work/sources/`, copied from `../h21/work/sources/`; library-derived, never commit). All six are **installed**
(`tools/install_model.py --world mm6`, `work/exports.sha256` = the installed sources); `actors.yml` is not edited
here: [bindings.yml](bindings.yml) is for the coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Demon A-C (`mm6_demon`, Mixamo rig, digitigrade, tail) | Walk2: humanoid set Armed-Walk, 0.72 s, 1.4660, 2.04 · Jog: Unarmed-Run-Forward, 0.66 s, 2.7038, 4.10 · Sprint: Unarmed-Sprint, 0.52 s, 3.7585, 7.23 |
| Guard A-C (`mm6_gua`, Meshy rig, one-handed halberd) | Jog: Unarmed-Run-Forward, 0.76 s, 2.4734, 3.25 · Sprint: Unarmed-Sprint, 0.56 s, 3.4673, 6.19 |
| BGoblin A-C (`mm6_gob2`, scimitar) | Sprint: Unarmed-Sprint, 0.54 s, 3.7148, 6.88 |
| Skeleton A-C (`mm6_ske`, Mixamo rig, sword) | Walk2: Armed-Walk, 0.92 s, 1.5398, 1.67 · Jog: Unarmed-Run-Forward, 0.76 s, 2.5469, 3.35 · Sprint: Unarmed-Sprint, 0.62 s, 3.6026, 5.81 |
| LizardArch A-C (`mm6_lzd`, bow, tail, loin flap) | Walk2: Armed-Walk, 0.90 s, 1.2426, 1.38 · Jog: Mixamo Running (5), 0.83 s, 2.2999, 2.77 |
| ElemEarth A-C (`mm6_ert`, 2.4 m stone giant) | Walk2: Mixamo Mutant Walking (its Walking's own source), 1.05 s, 2.7522, 2.62 · Run: Unarmed-Run-Forward, 0.74 s, 4.0206, 5.43 · Sprint: Unarmed-Sprint, 0.62 s, 5.5509, 8.95 |

Strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree; planted soles per side within 1 %,
`review/<m>_probes.txt`). No longer bound for locomotion but kept: the Demon's and Skeleton's `Running`, the Guard's
`Running`, the LizardArch's `Walking`/`Running`; the Demon's, Skeleton's, LizardArch's and ElemEarth's `Walking`.

## Why these clips (`review/mm6_<m>_targets.txt`, `review/mm6_<m>_gate_installed.txt`)

- **Demon** (hip 0.81 m): wandering 1.91-2.50 played its slow stalk (1.19 u/s) at x1.60-2.10; MAW's chase (7.51-7.63)
  Running at the cap. Its `Running` stride is not trusted (vertices 2.647 / feet 1.779 against the bound 2.325, gate
  FAIL), so the Standard chase (3.81-5.01) gets a Jog too.
- **Guard** (hip 0.78): A-C chased (3.14-3.77) on a fast Running (4.44 u/s) at x0.71-0.85: a Jog. MAW's chase
  (6.29-6.60) played Running at x1.42-1.49, at the edge; it gets a Sprint (binding Running as the sprint would also
  pass).
- **BGoblin** (hip 0.76): only MAW's chase (6.96-7.83) failed (Running at the cap): a Sprint.
- **Skeleton** (hip 0.81): its Walking is a 0.71 u/s shamble, so it wandered (1.76-1.78) on Running at x0.79 and chased
  (3.52-3.56) at x1.57 with an untrusted stride (1.534 / 1.002); MAW's chase (5.54-6.63) at the cap. Walk2, Jog, Sprint.
- **LizardArch** (ranged; MAW keeps its speed; hip 0.88): A walked as it ran (walk-as-run, made at pursuit 1.75) and
  now chases at 2.65 (Walking x1.55, Froude 0.81: a run pace). B/C chased on `Running`, whose feet barely travel
  (stride measured 0.24 / 0.14 against the bound 2.117: an almost in-place shuffle). `Walking` plants its feet at
  different speeds (left 0.99, right 1.45 per loop, the gate: 1.042 / 1.197, binding 1.366 FAIL), so no walk binding
  stops both feet sliding. Walk2 and Jog for every tier.
- **ElemEarth** (hip 1.18, Spd high): walk-as-run on its Mutant walk (1.89 u/s): wandering 2.67-3.16 played it at
  x1.42-1.68, the chase (5.35-6.32, Froude 2.5-3.5) at the cap with x1.4-1.7 slide, MAW's chase (9.97-10.45) with
  x2.6-2.8 slide. Walk2 (the same Mutant walk at a brisker cadence), Run and Sprint.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor)

```
Demon      standard A wander Walk2 x0.94  chase Jog x0.93 | maw A chase Sprint x1.06
           standard B wander Walk2 x1.09  chase Jog x1.09 | maw B chase Sprint x1.05
           standard C wander Walk2 x1.23  chase Jog x1.22 | maw C chase Sprint x1.04
Guard      standard A wander Walking x1.24  chase Jog x0.97 | maw A chase Sprint x1.02
           standard B wander Walking x1.36  chase Jog x1.06 | maw B chase Sprint x1.04
           standard C wander Walking x1.49  chase Jog x1.16 | maw C chase Sprint x1.07
BGoblin    standard A wander Walking x0.88  chase Running x0.92 | maw A chase Sprint x1.14
           standard B wander Walking x0.87  chase Running x0.91 | maw B chase Sprint x1.07
           standard C wander Walking x0.86  chase Running x0.89 | maw C chase Sprint x1.01
Skeleton   standard A wander Walk2 x1.06  chase Jog x1.06 | maw A chase Sprint x1.14
           standard B wander Walk2 x1.06  chase Jog x1.06 | maw B chase Sprint x1.04
           standard C wander Walk2 x1.05  chase Jog x1.05 | maw C chase Sprint x0.95
LizardArch standard/maw A wander Walk2 x0.96  chase Jog x0.96
           standard/maw B wander Walk2 x1.03  chase Jog x1.03
           standard/maw C wander Walk2 x1.10  chase Jog x1.09
ElemEarth  standard A wander Walk2 x1.02  chase Run x0.98 | maw A chase Sprint x1.11
           standard B wander Walk2 x1.11  chase Run x1.07 | maw B chase Sprint x1.14
           standard C wander Walk2 x1.21  chase Run x1.16 | maw C chase Sprint x1.17
```

MAW's wander rows (hostile speed, not judged): Demon Jog x0.92-0.93, Guard Jog x0.97-1.01, BGoblin Running
x0.97-1.09, Skeleton A/B Jog x0.99 / x0.90 but **C on Walk2 at x1.65**, ElemEarth Run x0.92-0.96. The Guard's tier C
Standard wander (Walking x1.49) is the installed walk, unchanged.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h21/scripts/compose_gait.py` (h16's composer with h02/h04 `raise_arms`, h07 `arm_raise_deg`, h01
`even_bob`, h19 `track_out`) with h19's `follow_thighs` (`gain`, `rest_relative`) and one addition: `foot_toe_out_deg`
may be `{L, R}` (below). Legs, pelvis and trunk rhythm from the library loop, two-bone IK, `lock_stance` planted soles
on jogs, runs and sprints, the integral plant and per-frame grounding on walks, `foot_smooth`, `even_bob` +
`symmetric_drop`; arms, hands, props, tails, wings and spikes from the model's own clip (`base`: Running, or Walking
for walks and for the ElemEarth, which has no run), phase-aligned. The Mixamo rigs (Demon, Skeleton) are composed on a
B_* renamed copy (`scripts/rename_mixamo.py`, h04's; the round trip is byte-identical) and renamed back; the Guard's
Meshy rig is aliased in memory (`gaitlib.alias_nodes`). Per model:

- **Demon**: Walk2 `bob` 2.5 with trunk weights 0.5 (per-frame grounding flattened the walk's bob to 2 %; full trunk
  weights left `uneven` 0.4), cadence 0.72 s (short thighs/calves on long digitigrade feet: the library walk's stride
  at 0.9 s was 1.6x its natural scaled stride). `foot_weight` 0.5 on all three: the library foot roll on the long
  digitigrade foot lifted the claws (planted only 11-22 % of the walk's loop; now 42-50 %, jog/sprint 20-24 %).
  Sprint trunk weights 0.7.
- **Guard**: halberd cleared as a prop (`clear_props`). Sprint `swing_height` 0.75: the kicked heel met the halberd's
  rear shaft (15 % / 35 mm; 0.85 still 3 % / 6 mm), `side_gain` L 1.1 (1.3 stretched the free elbow to 3.03x).
- **BGoblin**: Sprint lean 5-8 deg on its hunched carry, trunk weights 0.7 (`uneven` 0.33 at full weight, now 0.25).
- **Skeleton**: Walk2 `bob` 1.35; all three keep the sword arm from its own clips (0 contacts).
- **LizardArch**: the slower Mixamo Running (5) for the Jog (the humanoid-set run at this speed ran in place with high
  knees and kicked the heels under the tail); `arm_clearance` off (the skin-normal clearance turned the bow arm 25 deg
  and made it deeper); `loincloth` on `LoinFlap` (offset 8, max 60: Walk2 41-66 deg, Jog 54-68 deg, 0 % inside the
  legs). **Feet**: the rig's foot->toe joint line is 41-46 deg off the foot mesh, so `stance_foot: Standing` with 5 deg
  toe-out turned the visible feet 30 deg out; both clips keep the base clip's planted foot instead (no `stance_foot`),
  matching the accepted clips (mesh toe-out +16-17 against Walking/Running +15-16).
- **ElemEarth**: no run clip, so arms from Walking with `arm_gain` 1.4 / 1.6 and elbows 20 deg forward (as h15's MM8
  Earth Elemental); `swing_height` 0.85 / 0.9; Walk2 `bob` 0.25 (the Mutant walk's lurch gave 13 % at 1.0).
  `foot_toe_out_deg` {L 7, R 17}: the right boulder foot's joint line is 14 deg off its mesh, and a uniform 5 deg
  turned it 13 deg in (mesh); now the planted feet read +2-3.5 deg on the mesh like Walking's +2-4.

## Phase

Every new clip puts the left foot forward-most at the model's `Walking` phase (`align: Walking`): Demon 0.18 (installed
Running 0.25), Guard 0.17 (Running 0.21), BGoblin 0.75 (Running 0.90), Skeleton 0.24 (Running 0.24), LizardArch 0.75
(Running 0.75), ElemEarth 0.25-0.26 (no Running). No installed walk/run pair here is half a loop apart.

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all six (`review/<m>_winding.txt`). `prefix_check.py` ok on all six.
- Foot heading (`foot_heading_probe.py`, joints, toe-out from +Z, planted L / R; `foot_mesh_heading_probe.py` on the
  foot mesh where the joint line misleads):
  - Demon Walk2 +4.8 / +5.0, Jog +5.0 / +5.0, Sprint +5.1 / +5.0; installed Walking +17.2 / +17.7, Running +23.1 / +18.2
  - Guard Jog +5.0 / +4.9 (swing -5.2..+7.4), Sprint +5.1 / +4.9 (-6.2..+6.5); Walking +8.8 / +10.2, Running +13.2 / +8.2
  - BGoblin Sprint +5.1 / +4.9 (-6.2..+6.4); Walking +2.3 / +2.8, Running +5.7 / +2.8
  - Skeleton Walk2 +4.8 / +5.0, Jog +5.0 / +4.9, Sprint +5.1 / +4.9; Walking +2.6 / +3.8
  - LizardArch (mesh) Walk2 +16.3 / +17.2, Jog +16.6 / +17.2; Walking +15.3 / +15.9, Running +15.3 / +15.7
  - ElemEarth (mesh) Walk2 +2.3 / +2.1, Run +2.7 / +3.0, Sprint +2.8 / +3.5; Walking +1.8 / +3.8
- Head bob (bob_audit's measure, `bob_probe.py`; `uneven`): Demon Walk2 4.3 % (0.08), Jog 4.1 % (0.09), Sprint 5.2 %
  (0.09); Guard Jog 4.0 % (0.02), Sprint 4.5 % (0.02); BGoblin Sprint 5.8 % (0.25); Skeleton Walk2 3.8 % (0.05), Jog
  5.4 % (0.10), Sprint 5.1 % (0.06); LizardArch Walk2 4.1 % (0.08), Jog 4.6 % (0.14); ElemEarth Walk2 4.6 % (0.14), Run
  5.7 % (0.07), Sprint 5.9 % (0.15).
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/finger/prop inside legs or trunk): 0 % in every new clip
  (props: halberd, scimitar, skeleton sword, bow) except the LizardArch Jog's left forearm-twist 8 % / 35 mm against the
  belt, the same two vertices as its accepted Running (45 % / 32 mm). Wrist maxima equal the base clips'. Arm skin
  stretch p99 within 0.05 of the base clips' (Guard Sprint left 1.54 / max 2.83 against Running 1.49 / 2.53).
- Loin flap (`cloth_probe.py`, LizardArch): 0 % inside the legs in Walk2 and Jog.
- Lowest skin: within 0.1 cm of the floor in every new clip (none below -1 cm; the Demon's tail stays above it).
- Playback (`tools/run_creature_review.py check` and `playback`: no console errors, every clip switch, normal and half
  speed; looked at): viewers in `../../mm6_<m>_gait_h06_claude/review/` (the wrapper needs a direct child of
  `creatures/`), sheets `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/`.
- Headless actor regressions on the installed GLBs with the current (unapplied) bindings, all PASS
  (`scripts/regressions.sh`, `review/regression_*.log`): `mm6_demon_actor_models_keep_simulation_and_death_rules`,
  `mm6_demon_actor_models_variants_share_asset_and_native_stats`, `mm6_demon_actor_models_sorpigal_crowd`,
  `mm6_demon_actor_models_indoor_binding`, `mm6_demon_actor_models_hive_placed_actors`,
  `mm6_gua_actor_models_bind_new_sorpigal_guards`, `mm6_gob_actor_models_bind_sorpigal_goblins`,
  `mm6_skeleton_actor_fidget_clip_plays_past_the_native_fidget`,
  `mm6_skeleton_actor_model_tiers_follow_the_native_frame_scales`,
  `mm6_lizard_archer_actor_model_tiers_follow_sprite_scales`, `mm6_ert_actor_model_tiers_clips_and_sockets`,
  `mm6_mm7_mm8_actor_models_build_every_binding`.

## Doubtful / left open

- New clips plant at 5 deg toe-out (joints) while the accepted Demon (17-23 deg) and Guard runs (8-13 deg) plant wider:
  the heading changes at walk/run switches, as on earlier packages.
- The Demon's digitigrade feet: the composer's two-bone IK treats thigh + calf as the leg (0.65 m against a 0.81 m
  hip), so its library strides are long for that leg; the cadences are short (Walk2 0.72 s, 167 steps a minute) to
  keep the steps natural. `foot_weight` 0.5 keeps the claws down but makes the foot roll flatter than the source's.
- Skeleton MAW tier C wanders (not judged) on Walk2 at x1.65; the Jog keeps the library run's high knees (forward
  scale 0.77).
- LizardArch Jog: a Mixamo run with a lower pelvis (0.75 m against Standing's 0.88: knees bent, a lizard crouch).
- ElemEarth Walk2 and Run/Sprint switch from the Mutant walk's stomp to a humanoid-set run at the chase (as h15's MM8
  Earth Elemental). The Sprint (8.95 u/s, a 5.55 m loop) is a long-striding dash for MAW's 10 u/s chase.
- `assets_dev/worlds/mm6/models/sorpigal_demon_crowd.yml` (a regression crowd file) carries its own BGoblin bindings
  (`run: Running`, `stride_length: 1.5`); `apply_bindings.py` does not touch it, and nothing here needed it changed.

## Shared tools

No problem found in `claude_shared/` tools. Note for the rollout: `foot_heading_probe.py` (the foot->toe joint line)
misreads rigs whose toe joint is off the foot's long axis (LizardArch: 41-46 deg; ElemEarth right foot: 14 deg), and
`stance_foot: Standing` with `foot_toe_out_deg` then turns the visible feet by that offset; `scripts/foot_mesh_heading_probe.py`
measures the foot mesh instead. `gait_gate.py` takes about 2 minutes per model.

## Rebuild

`scripts/rebuild.sh [demon gua gob2 ske lzd ert]` composes the exports from `work/mm6_<m>_pre_gait.glb` and `jobs/`
(Demon and Skeleton through the B_* rename and back), then runs `gait_gate.py` and `check_winding.py`. The library
loops in `work/sources/` were copied from `../h21/work/sources/` (humanoid set via `scripts/extract_source.py`;
`Running__5.npz` and `Mutant_Walking.npz` are Mixamo). Probes: `scripts/probes.sh <m> <export or B_* copy> <old
clips> <new clips> [node=prop.glb]` (set `PREFIX_GLB=<export>` for a renamed copy), `scripts/foot_mesh_heading_probe.py`,
`scripts/cloth_probe.py`; filmstrips `scripts/render_review.sh`; viewers `scripts/build_viewers.py <m> <export> <title>
<old> <new> [node=prop.glb]`, then `python3 tools/run_creature_review.py --project
level_generation/creatures/mm6_<m>_gait_h06_claude playback` and `scripts/playback_sheet.py <m> <clips>`; regressions
`scripts/regressions.sh`. Install: `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h06/export/mm6_<m>.glb --world mm6 --name mm6_<m>.glb`. Rollback:
install `work/mm6_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD repair, head-bob or reduction rerun on
these models must re-graft the clips (copy the new source over the pre-gait copy and rebuild).
