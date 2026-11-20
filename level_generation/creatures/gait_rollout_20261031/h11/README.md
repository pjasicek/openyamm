# Gait rollout package h11: MM7 Cleric Moon, Cleric Sun, Mage, Warlock, Necromancer (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the five installed MM7 sources
(`assets_source/worlds/mm7/models/`; pre-gait copies `work/mm7_<m>_pre_gait.glb`, SHA-256 in `work/pre_gait.sha256`).
Existing clips, meshes, skins and materials are untouched (`scripts/prefix_check.py`: the input's binary chunk is a
byte-identical prefix, only animations appended). No Meshy credits or other spending; the sources are local humanoid-set
loops (`work/sources/`, copied from `../h09/work/sources/`, library-derived: never commit). All five are **installed**
(`tools/install_model.py --world mm7`); `actors.yml` is not edited here: [bindings.yml](bindings.yml) is for the
coordinator.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Mage A-C (`mm7_m274`, robe + cape sheet, staff in the left hand) | Jog: humanoid set Armed-Run-Forward, 0.72 s, 2.7427, 3.81 |
| Warlock A-C (`mm7_m426`, floor-length gown, bare feet, wand in the left hand) | Jog: Armed-Run-Forward, 0.72 s, 2.7032, 3.75 |
| Necromancer A-C (`mm7_m294`, ragged split cape, heeled boots) | Jog: Armed-Run-Forward, 0.74 s, 2.5554, 3.45 |
| Cleric Moon A-C (`mm7_m170`, legless floor-length robe, banners) | Walk2: Relax-Walk-Forward, 1.00 s, 1.417, 1.42 · Jog: Armed-Run-Forward, 0.80 s, 2.143, 2.68 |
| Cleric Sun A-C (`mm7_m174`, legless floor-length robe) | Walk2: Relax-Walk-Forward, 1.10 s, 1.319, 1.20 · Jog (B/C only): Armed-Run-Forward, 0.80 s, 2.043, 2.55 |

Mage, Warlock and Necromancer strides are `gait_gate.py`'s trusted measurements (vertices and foot joints agree). The
Clerics have no leg geometry (the legs were removed under the robe, `strip_legs.py`; the leg bones only drive the robe's
leg capsules), so the gate cannot trust any of their clips' vertex strides (the installed `Walking` is untrusted too:
vertices 0.03 / feet 1.37): their strides are the foot-joint measurements, set explicitly (`--set`), as h09's Wight.

## Why these clips (targets from `gait_gate.py`, `review/<m>_targets.txt`; MAW leaves every speed unchanged: casters)

All five had only `Walking`, bound as the run too (walk-as-run).

- **Mage** (hip 0.88 m): wander 1.84-2.21 fits `Walking` (x0.99-1.19); the chase 3.68-4.42 (Froude 1.6-2.3: a run
  pace, not a walk) played `Walking` at x1.98-2.38. A Jog.
- **Warlock** (hip 0.87 m): the same speeds and the same reasoning: a Jog.
- **Necromancer** (hip 0.87 m): chase 3.33-4.00 (Froude 1.3-1.9) played `Walking` at x1.86-2.24. A Jog.
- **Cleric Moon** (hip 0.77 m): A's wander (1.27) played `Walking` at x0.74; the chase 2.54-3.18 (Froude 0.86-1.34: a
  run pace) at x1.48-1.86. A slower Walk2 and a Jog for every tier.
- **Cleric Sun** (hip 0.79 m): wander 1.08-1.35 played `Walking` at x0.62-0.78; the chase 2.16 / 2.43 / 2.70 (Froude
  0.60 / 0.76 / 0.94). A slower Walk2 for every tier; tier A keeps the walk-as-run decision (Froude 0.60, `Walking` at
  x1.24), B and C jog.

## Gate window sections (`review/<m>_gait_gate.txt`, all PASSED, floor ok on every descriptor; standard = maw rows)

```
Mage          A wander Walking x0.99  chase Jog x0.97
              B wander Walking x1.09  chase Jog x1.06
              C wander Walking x1.19  chase Jog x1.16
Warlock       A wander Walking x0.97  chase Jog x0.98
              B wander Walking x1.06  chase Jog x1.08
              C wander Walking x1.16  chase Jog x1.17
Necromancer   A wander Walking x0.93  chase Jog x0.97
              B wander Walking x1.02  chase Jog x1.06
              C wander Walking x1.12  chase Jog x1.16
Cleric Moon   A wander Walk2 x0.90    chase Jog x0.95
              B wander Walk2 x1.01    chase Jog x1.07
              C wander Walk2 x1.12    chase Jog x1.19
Cleric Sun    A wander Walk2 x0.90    chase Walking x1.24   (review/m174_gait_gate_tier_a.txt)
              B wander Walk2 x1.01    chase Jog x0.95
              C wander Walk2 x1.13    chase Jog x1.06
```

Cleric Sun's tiers are gated separately (`scripts/gate_only.py`, a copy of `../q2/scripts/gate_only.py`), since A keeps
`run: Walking` while B/C bind `Jog`.

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

A copy of `../h12/scripts/compose_gait.py` (h16's composer with h02's `raise_arms`, h07's arm raise, h01's
`even_bob`, h19's `track_out`, h12's `hand_props` and h08's `cloth`) with h09's `soles_feet_only`, `sole_joints` and
`ground_all` ported in. Legs, pelvis and trunk rhythm from the library loop, two-bone IK, `lock_stance` planted soles,
`stance_foot: Standing` with `foot_toe_out_deg: 5`, `foot_smooth`, floor lift; arms, hands and props from the model's
own `Walking` (none has a run), phase-aligned to `Walking` (left foot forward-most at 0.75 on every model, as Walking).
A robe-safe jog for all: the gentle Armed-Run-Forward (knee 68 deg) with `swing_height` 0.4-0.6 (low heel kick), a
2 deg lean per trunk bone, arm swing x1.1-1.3 with a 10-15 deg extra elbow bend. Walk2 uses the model's own walk source
(Relax-Walk-Forward) at a slower cadence and shorter stride with the integral plant on the virtual soles. Additions:

- **`prop_upright`** (Mage staff, Warlock wand): the accepted Walking holds the staff at one world lean (Mage 4 deg
  forward at every key); the same arm on a jogging trunk tipped it from -3 to 19 deg. Per sample the hand (fist and
  prop with it) turns about the wrist by 0.75 of the least rotation to the walk's mean axis (Mage tipped 6 deg forward,
  a running carry). Staff now 6..12 deg forward, wand 32..38 (Walking 34..36). Wrist maxima do not exceed Walking's.
- **`prop_floor`** with a post hook (Mage): h04's `lift_prop` (the staff arm's upper arm turned so the staff foot rises
  where it would dip under the floor, smoothed), measured after the upright turn; the jog's lower hand had put the
  staff foot 2.4 cm under the floor; lift up to 12.4 deg, staff lowest -0.0 cm (Walking -0.2).
- **`sole_joints`** (Clerics, h09's): virtual soles from the hidden ankle and toe joints.
- Cloth (`scripts/cloth_sim.py`, h08's port of the robed projects' `robe_sim.py`) on every new clip, chains from the
  projects' masters (`scripts/dump_chains.py` on `../../mm7_<m>_claude/work/rig_v6.blend`, now also `banner_chains`):
  robe (all), the Mage's cape sheet (root B_Spine2), the Moon Cleric's banners (root B_Spine2). Run settings as h08's
  (`mid_collide`, `final_collide`, bend smoothing and limit, `nb_final`, leg capsules x1.6 on the legged three).
  Two additions here: `floor` (a higher chain floor, 4-6 cm) and **`hem_floor`**: per sample the last bone of each
  chain turns about its head by the least smoothed angle that lifts its deepest dominated skinned vertex to 3 mm. A
  floor-length gown on the jog's lower pelvis folds its last bones and the hem vertices beside their axis swung under
  the floor (Warlock -2.9 cm in the gate; the Clerics -2 to -3 cm); hem lowest now 0.0 cm or above on every clip.
  Folding outward (tried as `floor_out`) made it worse (-13 cm): the gown surface lies outside the chain axis.

Cloth port check (`scripts/cloth_check.py`: re-simulating each installed `Walking`): median 0.0-0.1 cm everywhere;
p95 / max Cleric Sun 0.1 / 0.4, Mage robe 0.9 / 13.8 and cape 0.1 / 0.3, Moon banners 0.1 / 0.1, but Moon robe
6.5 / 25.9, Warlock 8.5 / 27.8, Necromancer 22.7 / 44.2 cm. Likely cause (not proven): the 2026-10-21 floor fix
(`mm7_<m>_reduce_claude/README.md`) re-keyed robe bones after the bake (`--lift-only 'Robe_*'`; on the Necromancer also a
ground-loop of `Walking`), so those installed walks are no longer the raw simulation; the code and constants are the
same as for the matching ones. `work/cloth/<m>.json` holds the configs of that check.

## Checks (`review/`)

- `check_winding.py`: 0 inverted closed parts on all five (`review/<m>_winding.txt`). Prefix check ok
  (`review/<m>_probes.txt`). `scripts/rebuild.sh` reproduces the installed GLBs byte for byte (`work/exports.sha256`).
- Foot heading (`foot_heading_probe.py`, toe-out, planted L / R, swing range):
  - Mage Jog +5.0 / +5.4 (+2.1..+9.4); Walking +5.5 / +6.0
  - Warlock Jog +5.0 / +5.4 (+2.1..+9.4); Walking +5.1 / +3.0
  - Necromancer Jog +5.0 / +5.4 (+2.1..+9.4); Walking +10.5 / +8.4
  - Cleric Moon (hidden feet) Walk2 +4.8 / +4.8, Jog +5.0 / +5.5; Walking +1.0 / +0.3
  - Cleric Sun (hidden feet) Walk2 +4.8 / +4.8, Jog +5.0 / +5.5; Walking +1.1 / +0.3
- Head bob (bob_audit's measure, `bob_probe.py`; `uneven`): Mage Jog 6.6 % (0.03); Warlock Jog 4.5 % (0.05);
  Necromancer Jog 6.5 % (0.02); Cleric Moon Walk2 3.5 % (0.04), Jog 5.5 % (0.03); Cleric Sun Walk2 3.1 % (0.03), Jog
  4.9 % (0.03). Walkings 3.0-3.3 %.
- Arm and hand gate (`contact_probe.py`, 60 Hz, forearm/hand/prop inside legs or trunk): Mage, Warlock 0 % (staff and
  wand 0 %); Necromancer free arms L 0 % / R 49 % 37 mm (Walking 14 % 23 mm / 57 % 37 mm: the hand inside the open
  hanging cape panel, the accepted proximity); Clerics' claws in the robe as their accepted walks (Moon Jog L 88 % 33 mm
  / R 71 % 17 mm, Walking 94 % 29 mm / 80 % 22 mm; Sun Jog 76 % 36 mm / 65 % 39 mm, Walking 59 % 38 mm / 55 % 37 mm).
  Walk2 equals its Walking. Wrist maxima equal or below the base clip's.
- Arm skin stretch p99 (L / R; Walking in brackets): Mage 1.15 / 1.23 (1.09 / 1.14), Warlock 1.14 / 1.20
  (1.09 / 1.13), Necromancer 1.16 / 1.15 (1.14 / 1.12), Cleric Moon Jog 1.22 / 1.20 (1.15 / 1.13), Cleric Sun Jog
  1.14 / 1.12 (1.10 / 1.10). Above h08's 0.06 guide on the Mage's right and the Moon Cleric's left: armpit and
  bell-sleeve edges (upper arm against forearm twist, upper arm against spine); the stretch stays with the arm gain at
  1.0, so it comes from the jog's trunk rhythm under the walk's arms, inside the sleeves.
- Lowest skin: every new clip within 0.7 cm of the floor (none below -1 cm).
- Skirt poke (`skirt_poke_probe.py`, approximate): the open-fronted Mage robe and Warlock gown show the trailing leg
  behind the hem as their walks do (Mage Walking 64 % / Jog 77 %, Warlock 80 / 86 %, Necromancer 100 / 100 %:
  the split cape never covers the legs).
- Playback (`tools/run_creature_review.py check` and `playback`: no console errors, normal and half speed, looked at):
  viewers in `../../mm7_<m>_gait_h11_claude/review/` (the wrapper needs a direct child of `creatures/`), sheets
  `review/<m>_playback_sheet.png`; Blender filmstrips `review/iter/`.
- Headless actor regressions on the installed GLBs (current bindings; the suite has no case naming these five models):
  `mm6_mm7_mm8_actor_models_build_every_binding` and `every_map_loads_and_builds_its_actor_models` PASS
  (`review/regression_*.log`, `scripts/regressions.sh`). Rerun after `apply_bindings.py`. No headless diagnostic names
  these models' walk or run clips.

## Doubtful / left open

- **Clerics**: legless robes, so Walk2 and Jog are seen only through the robe, banners and upper body (a hurried glide
  for the jog). Their strides are foot-joint measurements, not trusted by the gate (set explicitly). Cleric Sun A
  chases on `Walking` (walk-as-run) while B/C jog: tier-dependent, as the brief's rule asks.
- **Mage**: the staff arm is lifted up to 12 deg around the low step to keep the staff foot off the floor; the right
  arm's bell-sleeve stretch is p99 1.23 against Walking's 1.14 (inside the sleeve).
- **Warlock**: the gown hem's last bones are turned by `hem_floor` (up to 15 deg) at the low steps.
- **Necromancer**: the trailing boot shows between the cape strips (as in Walking); the jog plants at 5 deg toe-out
  while her walk plants at 8-11 deg.
- The cloth port differs from three installed walks at p95 (above); the new clips' cloth was judged by eye.
- MAW wandering (hostile speed) is not judged by the gate; MAW leaves these casters' speeds unchanged anyway.

## Shared tools

No problem found in `claude_shared/` tools. Notes: `gait_gate.py` cannot bind a legless robe from a trusted measurement
(`--set` needed, as h09's Wight); `--set` applies to every descriptor of a model (tier-dependent bindings need
`gate_only.py`).

## Rebuild

`scripts/rebuild.sh [m274 m426 m294 m170 m174]` composes the exports from `work/mm7_<m>_pre_gait.glb` and `jobs/`,
then runs `gait_gate.py` (explicit strides for the Clerics; Cleric Sun per tier group) and `check_winding.py`; it
reproduces the installed exports (`work/exports.sha256`). Cloth chains: `scripts/dump_chains.py` (Blender) into
`work/<m>_chains.json`. Probes: `scripts/probes.sh <m> <export> <old clips> <new clips> [node=prop.glb]`,
`skirt_poke_probe.py`, `prop_low_probe.py`, `cloth_check.py`; filmstrips `scripts/render_review.sh`; viewers
`scripts/build_viewers.py <m> <export> <title> <old> <new> [node=prop.glb]`, then `python3 tools/run_creature_review.py
--project level_generation/creatures/mm7_<m>_gait_h11_claude playback` and `scripts/playback_sheet.py <m> <clips>`.
Install: `python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h11/export/mm7_<m>.glb --world
mm7 --name mm7_<m>.glb`. Rollback: install `work/mm7_<m>_pre_gait.glb` the same way and drop the bindings. A far-LOD
repair, head-bob or reduction rerun on these models must re-graft the clips (copy the new source over the pre-gait copy
and rebuild).
