# Gait rollout package h03: MM6 BArcher, BLich, Cleric, Druidess, Sorcerer (2026-10-31)

Brief: [../README.md](../README.md). One new in-place locomotion clip, `Jog`, appended to each of the five installed
MM6 sources (`assets_source/worlds/mm6/models/`; pre-gait copies and rollback `work/mm6_<m>_pre_gait.glb`, SHA-256 in
`work/pre_gait.sha256`). Every existing clip, mesh, skin and material is unchanged (`scripts/prefix_check.py`: the
input's binary chunk is a byte-identical prefix of the export, only the animation is appended). No Meshy credits or
other spending; sources are local library loops (`work/sources/`, library-derived, never commit). All five are
**installed** (`tools/install_model.py --world mm6`); `actors.yml` is not edited here: [bindings.yml](bindings.yml) is
for the coordinator.

| Model | Jog: legs source, length, bound stride, authored speed (model units/s) | Garment |
|---|---|---|
| BArcher A-C (`mm6_arc1`, bow, arrow) | humanoid set 2Hand-Bow-Run-Forward, 0.74 s, 2.1358, 2.84 | none |
| BLich A-C (`mm6_lch`, skeleton, tatters) | Unarmed-Run-Forward, 0.70 s, 2.5016, 3.57 | skinned tatters |
| Cleric A-C (`mm6_cle`, staff, Meshy rig) | Unarmed-Run-Forward, 0.64 s, 2.1277, 3.28 | 13 cloak chains, skinned split tunic |
| Druidess A-C (`mm6_dru1`) | Unarmed-Run-Forward, 0.70 s, 2.2475, 3.29 | 15 hooded-cloak chains |
| Sorcerer A-C (`mm6_sor1`, staff) | Unarmed-Run-Forward, 0.66 s, 2.6955, 4.09 | 16 closed robe chains to the floor |

Bound strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree).

## Why (targets: `gait_gate.py` without a candidate)

All five had one locomotion clip (`run: Walking`), and all chase at a run pace: Froude v^2 / (g L) at the chase
speeds is 0.90-1.18 (Archer, leg 0.78 m), 1.08-1.69 (Druidess), 1.19-1.86 (Cleric), 1.35-2.0 (Lich), 1.73-2.48
(Sorcerer), above the walk-as-run limit 0.65, so the chase gets a run (as h08's Monk and Vampire). They are casters and
an archer: MAW leaves their speeds unchanged (no sprint). Wandering already fits `Walking`. Chase at Standard and MAW
before: Archer x2.44-2.78, Cleric x2.12-2.66, Sorcerer x2.12-2.54, Druidess x1.63-2.04, Lich x1.63-1.99 (held at the
2x ceiling with sliding feet above it). One jog per model covers the three tiers.

## Gate window sections (`review/<m>_gait_gate.txt`; all PASSED, stride trusted, floor ok on every descriptor)

```
BArcher   standard/maw A  wander Walking x1.22  chase Jog x0.91
          standard/maw B  wander Walking x1.30  chase Jog x0.98
          standard/maw C  wander Walking x1.39  chase Jog x1.04
BLich     standard/maw A  wander Walking x0.81  chase Jog x0.90
          standard/maw B  wander Walking x0.90  chase Jog x1.00
          standard/maw C  wander Walking x0.99  chase Jog x1.10
Cleric    standard/maw A  wander Walking x1.06  chase Jog x0.88
          standard/maw B  wander Walking x1.19  chase Jog x0.98
          standard/maw C  wander Walking x1.33  chase Jog x1.09
Druidess  standard/maw A  wander Walking x0.82  chase Jog x0.90
          standard/maw B  wander Walking x0.92  chase Jog x1.02
          standard/maw C  wander Walking x1.02  chase Jog x1.13
Sorcerer  standard/maw A  wander Walking x1.06  chase Jog x0.92
          standard/maw B  wander Walking x1.16  chase Jog x1.02
          standard/maw C  wander Walking x1.27  chase Jog x1.11
```

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h09/scripts/compose_gait.py` (h21 / h16 lineage: library legs, pelvis and trunk rhythm, two-bone IK,
`lock_stance`, `stance_foot: Standing` with `foot_toe_out_deg: 5`, `foot_smooth`, `even_bob`, `symmetric_drop`,
h02/h04 `raise_arms`, h09 `soles_feet_only`) with h01's `cloak` hook. Arms, hands and props come from each model's own
`Walking` (`base: Walking`; only the Cleric has an unbound `Running`, whose elbow and heel went through the cloak),
phase-aligned to `Walking`. Additions here:

- **`cloak`** generalised (`scripts/cloak.py`): h01's numpy port of the MM6 Thief's Blender bake now takes a preset
  per model, each the constants of that model's own bake (all three descend from the Thief's): `cle`
  (`../../mm6_cle_claude/scripts/cloak_sim.py`: MARGIN 0.035, wide leg capsules), `dru1`
  (`../../mm6_dru1_claude/scripts/cloak_sim.py`: DAMP 0.94, STIFF 0.09, NARROW 0.4, neck and heel capsules, trajectory
  smoothing), `sor1` (`../../mm6_sor1_codex/scripts/robe_sim.py`: chains from `B_Pelvis`, closed ring, FLOOR 0.10, wide
  foot and heel capsules). Options `leg_pad`, `floor`, `lift_deg`, `smooth_s`. Chain rest points: dumped from the rigs
  (`scripts/dump_cloak_chains.py <out> <blend> <scene key> <rig>`; `scripts/chains_check.py` finds them identical to
  the GLB bind heads, 0.0 mm) or, for the Sorcerer (rig blend not kept), built from the GLB
  (`chains_check.py --from-glb Robe_`). Port check against each installed `Walking` (`scripts/cloak_check.py`, chain
  joints 1-3): Cleric median 0.4 / p95 1.6 / max 4.1 cm, Druidess 0.9 / 3.2 / 5.0 cm, Sorcerer 1.5 / 4.1 / 11.1 cm
  (its robe had later contact passes in the Codex project).
- **`soles_feet_only: "no_cloth"`**: low vertices dominated by `Cloak_` / `Robe_` chain bones are not soles (they are
  posed by the base clip until the cloth is simulated; with them the Druidess's plant pass dragged the right foot and
  the gate found no trusted stride), while boot vertices on the calf stay soles (h09's foot-only rule let them sink
  1.7 cm). Used on the Druidess and Sorcerer.
- `scripts/glb_source.py`: a model's own clip as a library-style source (tried on the Cleric's `Running`: its natural
  stride 1.80 is too short for the chase, the hips dropped 8.6 cm; not used).

Per model:
- **BArcher**: legs from the bow run; `swing_height` 0.7; arms out 8 deg each (`arm_out_deg`): the bow's limb met the
  left thigh by 37 mm at phase 0.16-0.29 and the right hand the right thigh by 39 mm; raising the bow arm forward
  instead tipped the rear limb down into the thigh. Right arm swing x1.6 (`side_gain`).
- **BLich**: `swing_height` 0.6 (the big boots' heel kick met the hanging hands at hip height), arms out 5 deg, elbows
  bent forward 20 deg (a running carriage instead of the walk's hanging arms), swing x1.6.
- **Cleric**: a robe-safe jog: `swing_height` 0.45, short quick strides (2.1 in 0.64 s), arm swing as `Walking`,
  cloak `leg_pad` 0.05 (legs behind the hips uncovered by the cloak: the cloak poke probe reads the same as the
  accepted `Walking`, below).
- **Druidess**: `swing_height` 0.6, swing x1.3, spine rhythm at 0.3 weight (the full library torso turn stretched the
  shoulder skin to 2.17x), cloak `leg_pad` 0.08 and `floor` 0.035 (the boots kicked out behind the hem at 0.0).
- **Sorcerer**: `swing_height` 0.5, spine weight 0.3, robe `leg_pad` 0.03 (without it the knees and heels came through
  the robe: 25 % of samples, 55 mm; now 0 %).

## Checks (`review/`)

- `gait_gate.py` PASSED on all five; `check_winding.py` 0 inverted closed parts (`review/<m>_winding.txt`);
  `prefix_check.py` ok (`review/<m>_probes.txt`).
- Phase (left foot forward-most): Archer 0.75 (Walking 0.75), Lich 0.75 (0.75), Cleric 0.19 (Walking 0.20, its unbound
  Running 0.21), Druidess 0.77 (0.78), Sorcerer 0.75 (0.75).
- Foot heading (`foot_heading_probe.py`, toe-out from +Z, planted L / R; swing range): every Jog +4.8..+5.1 (swing
  within -7.9..+8.1). Installed walks: Archer +21.0 / +12.7 (rigid, Standing's), Lich +1.1 / +0.3, Cleric +10.6 /
  +13.5, Druidess +3.9 / +6.0, Sorcerer +7.1 / +6.1.
- Head bob (bob_audit's measure; `uneven`): Archer 4.6 % (0.00), Lich 4.7 % (0.02), Cleric 4.4 % (0.01), Druidess
  4.6 % (0.01), Sorcerer 5.5 % (0.01).
- Planted stride per side (`stride_probe.py`): Archer 2.111 / 2.162, Lich 2.500 / 2.500, Cleric 2.130 / 2.159,
  Druidess 2.302 / 2.318, Sorcerer 2.694 / 2.698.
- Arm and hand gate (`contact_probe.py`, 60 Hz; forearm, hand, finger and props inside legs or trunk): Archer 0 % (bow
  and both arms; its Walking right hand 29 % / 29 mm), Lich 0 %, Sorcerer 0 % (staff too), Cleric as `Walking` (left
  arm 62 % / 22 mm vs 63 % / 20 mm, right 21 % / 14 mm vs 21 % / 16 mm: the hands resting on the tunic; staff 0 %),
  Druidess left arm 12 % / 19 mm at the hip, 1-3 vertices (Walking 4 % / 20 mm). Wrist maxima equal `Walking`'s.
  Arm skin stretch p99 within 0.03 of `Walking`'s; max edge Archer 1.54 (Walking 1.07, 5 edges above 1.5x), Druidess
  1.63 (1.52), Cleric and Sorcerer as `Walking`.
- Garments: cloak poke (`cloak_poke_probe.py`: leg vertices behind the hips with no cloak behind them, share / mean /
  max): Cleric Jog 65 % / 7.0 / 22 (Walking 78 % / 6.8 / 27), Druidess Jog 74 % / 5.5 / 26 (Walking 74 % / 11.7 / 33).
  Sorcerer robe (`skirt_poke_probe.py`): 0 % (Walking 0 %).
- Lowest skin: every Jog within 0.2 cm of the floor (`low_probe.py`; none below -1 cm).
- Playback: `python3 tools/run_creature_review.py --project level_generation/creatures/mm6_<m>_gait_h03_claude check`
  and `playback` (no console errors; normal and half speed), looked at; sheets `review/<m>_playback_sheet.png`;
  Blender filmstrips `review/iter/` (`*_pre_Walking.png` the accepted walks).
- Actor regressions on the installed GLBs with the current (old) bindings, `scripts/regressions.sh`, all pass
  (`review/regression_*.log`): `mm6_cleric_actor_model_tiers_share_the_native_height`,
  `mm6_cleric_actor_spell_charge_glows_at_right_palm`, `mm6_cleric_actor_marked_attack_fits_the_action_and_follows_through`,
  `mm6_cleric_actor_ranged_attack_launches_from_staff_head`, `mm6_cleric_actor_air_attack_lights_the_staff_head`,
  `mm6_cleric_actor_head_turns_toward_the_party`, `mm6_lich_actor_model_tiers_share_the_native_height`,
  `mm6_sorcerer_actor_model_tiers_share_the_native_height`, `mm6_archer_actor_model_tiers_share_the_native_height`,
  `mm6_druidess_actor_model_tiers_share_one_size`, `mm6_mm7_mm8_actor_models_build_every_binding`. None of the MM6 cases
  in `game/outdoor/HeadlessOutdoorDiagnostics.cpp` names these models' walk or run clip. Rerun after `apply_bindings.py`.

## Doubts

- **Cleric tunic**: the front panel is skinned to both thighs (left half to the left, right half to the right), so
  when the legs scissor it parts over the right thigh and the black trousers show through a notch about 4-7 cm across
  at phase 0.0-0.15 (visible at viewer distance). The accepted `Walking` shows the same notch, smaller. Lower knees,
  shorter strides, a wider or narrower track and other sources did not remove it (it follows the thigh scissor of any
  run); fixing it needs the panel's weights changed in the Cleric project, outside this package. The cloak's dark
  inner shell shows in small patches at the back as in the accepted clips, and the right sleeve touches the cloak at
  the shoulder as in `Walking`.
- **Sorcerer**: the robe bells out widely in the jog (the robe sim's wide leg capsules); 4.1 u/s is a real run for a
  robed caster, but the chase speed asks for it (Froude 1.7-2.5).
- **Druidess**: the stiff, spread arm carriage of her accepted walk is kept (only its swing is stronger).
- **BArcher**: the bow is held low across the front as in `Walking`; arms turned out 8 deg to clear the thighs; 5 arm
  skin edges stretch 1.5x (max 1.54) at the shoulder from the trunk lean.
- New clips plant at 5 deg toe-out while the Archer's and Cleric's accepted walks plant at 11-21 deg; the heading
  changes at the walk/jog switch.
- MAW's wander rows are equal to Standard's (MAW leaves these speeds unchanged).

## Shared tools

No problem found in `claude_shared/` tools. Package-local fixes: `cloak_poke_probe.py` now reads Meshy and `B_*` rigs
alike (`gaitlib.open_glb`) and takes `CLOAK_PREFIX`; `render_clip.py` hid `Lich_LOD0` (any mesh name containing `LOD`;
now only LOD1-3 and shadows) and has back and close views.

## Rebuild

`scripts/rebuild.sh [--sources] [arc1 lch cle dru1 sor1]` composes every export from `work/mm6_<m>_pre_gait.glb`,
`jobs/<m>_jog.json`, `work/sources/` and the chain files, then runs `gait_gate.py --set run=Jog` and
`check_winding.py`; it reproduces the installed exports (`work/exports.sha256`). `--sources` extracts the two library
loops and the cloak chains. Probes: `scripts/probes.sh <m> export/mm6_<m>.glb <old clips> Jog [node=prop.glb]`,
`cloak_poke_probe.py`, `skirt_poke_probe.py`, `thigh_probe.py`, `cloak_check.py`; filmstrips `scripts/render_review.sh`;
viewers `scripts/build_viewers.py <m> <export> <title> <old> Jog [node=prop.glb]`, then
`python3 tools/run_creature_review.py --project level_generation/creatures/mm6_<m>_gait_h03_claude playback` and
`scripts/playback_sheet.py <m> Walking,Jog`. Regressions: `scripts/regressions.sh`. Install:
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h03/export/mm6_<m>.glb --world mm6
--name mm6_<m>.glb`. Rollback: install `work/mm6_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD
repair, floor-fix or head-bob rerun on these models must re-graft `Jog` (copy the new source over the pre-gait copy and
rebuild).
