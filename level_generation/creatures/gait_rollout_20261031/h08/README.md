# Gait rollout package h08: MM7 Thief, Troglodyte, Vampire, Monk (2026-10-31)

Brief: [../README.md](../README.md). New in-place locomotion clips appended to the four installed MM7 GLBs, all four
**installed** (`tools/install_model.py --world mm7`). Existing clips, meshes, skins and materials are untouched:
`claude_shared/graft_byte_check.py` OK on every export (old binary chunk a byte prefix, old JSON entries unchanged).
No Meshy credits or other spending. `actors.yml` is not edited: the bindings are in [bindings.yml](bindings.yml).
Rollback sources (the installed GLBs before this work): `work/mm7_<m>_pre_gait.glb`.

| Model | New clips: source, length, binding stride, authored speed (model units/s) |
|---|---|
| Thief A-C (`mm7_m410`) | Jog: humanoid set Unarmed-Run-Forward, 0.74 s, 3.2109, 4.34 · Sprint: Unarmed-Sprint, 0.60 s, 4.3333, 7.22 |
| Troglodyte A-C (`mm7_m418`) | Lope (bound as `walking`): Mixamo Mutant Run (the model's own Running source, now planted), 0.867 s, 2.5003, 2.88 · Jog: Unarmed-Run-Forward, 0.72 s, 4.1344, 5.74 · Sprint: Unarmed-Sprint, 0.60 s, 4.9948, 8.32 |
| Vampire A-C (`mm7_m422`) | Jog: humanoid set Armed-Run-Forward, 0.80 s, 2.6121, 3.27 · Sprint: Unarmed-Sprint, 0.60 s, 3.2033, 5.34 (coat skirt and cape simulated on both) |
| Monk A-C (`mm7_m290`) | Jog: Armed-Run-Forward, 0.80 s, 2.6533, 3.32 · Sprint: Unarmed-Sprint, 0.60 s, 3.4373, 5.73 (robe simulated on both; arms stay folded) |

Strides are the gate's trusted measurements (vertices and foot joints agree on every new clip).

## Choices per body

- **Thief** (lean human, dagger sheathed at the left hip): plain run and sprint as the pilot's KnightPlate; arms and
  the sheathed dagger's node from his own `Running`. The `Dagger` node (child of `B_Pelvis`) is re-keyed to follow
  its sheath (`follow_skin`: rigid fit of the 365 sheath vertices weighted 0.75 pelvis / 0.25 left thigh): copying
  `Running`'s dagger track over the new legs left it up to 6.5 cm off the sheath; now the sheath vertices stay within
  0.7 cm (median) of the dagger frame (max 5.9 cm at the sheath tip, the sheath's own bending; `Running` 1.6).
- **Troglodyte** (hunched, wide-hipped mutant, hips 0.59 m apart, legs 0.89 / 0.87 m): its wander (2.80-3.31 u/s,
  1.5 body heights per second) is a run pace, not a walk: the installed `Walking` (1.66 u/s) never fit and Standard
  wandering already played the unfitted `Running`. So three new clips fill three slots: `Lope` (the Mutant Run
  planted, Froude ~1) for wandering, `Jog` for Standard's chase, `Sprint` for MAW's 10.4-10.9 u/s chase. `Walking`
  and `Running` stay in the GLB, unbound for locomotion. `track_out` widens the run track 7-9 cm per side (the human
  sources put the feet under the centre line, which read narrow on this squat body); `elbow_flex_deg` L 30 / R 15 on
  the jog lifts the hanging claws off the swinging toes (they touched them by 34 mm); `contact_equal` (both feet's
  stance trimmed to the shorter one) removes a once-per-loop pelvis dip (limp) from the asymmetric source stance;
  the Lope keeps a foot within 1 cm of the floor (the floor audit's walking rule: `lock_extend` 3, extension 0.90)
  and has a gentler foot roll (`foot_weight` 0.3) so the swing foot does not flare.
- **Vampire** (long coat to 0.30 m with chain skirt, cape sheet): a robe-safe run: slower clips (3.3 and 5.3 u/s,
  played x1.13-1.35), a low swing (`lift_scale` 0.4: less knee lift and heel kick), arms from his `Walking` with a
  stronger swing (`arm_gain` 1.8 / 2.4) and bent elbows (`elbow_flex_deg` 55 / 70). The coat skirt and the cape are
  simulated on the new motion (below), with wider leg capsules than the walk (thigh 0.13 m) and a final collision pass.
- **Monk** (closed robe, arms folded in the sleeves with the hands shrunk to 3 %): same robe-safe run; the arms keep
  `Walking`'s fold (the hand scale channels come with it, so no hands appear), the robe is simulated.

## Cloth on new clips (`scripts/cloth_sim.py`)

A numpy port of the robed projects' Blender `robe_sim.py` (`../../mm7_m422_claude/scripts/robe_sim.py`, the Monk's
copy is the same without the m422 flags) on the composer's world matrices: verlet chain points pulled toward the
yaw-only rest bell, rigid bones, neighbour spacing, one-sided capsule collisions, floor, three loops simulated and the
last kept, temporal smoothing, the m422 flags (bend smoothing, midpoint collisions, bend limit, final neighbour pass),
bones aimed at the simulated joints. Chain definitions come from the projects' masters (`scripts/dump_chains.py` on
`../../mm7_<m>_claude/work/rig_v6.blend` into `work/<m>_chains.json`). Check: re-simulating the installed Vampire
`Walking` reproduces its skirt within median 0.0 / p95 0.3 / max 3.2 cm and its cape within 0.4 cm
(`scripts/cloth_check.py`, `review/cloth_port_check.txt`). The Monk's `Walking` matches at the median but differs at
p95 11 / max 26.5 cm at the hem; not traced (a candidate: body changes after its robe was baked, such as the
floor and head-bob fixes, with the robe keys left as they were). Same code and constants as the Vampire's, which match. Added for runs: `final_collide` (the bend limit and the last
neighbour pass ran after the hard collision pass and let the knee back through the coat front: 6 cm pokes in 44 % of
the jog before it, none after) and larger leg capsules (`leg_r` 2.0, `leg_floor` 0.12, `margin` 0.02).

## Gates (outputs in `review/`)

`gait_gate.py` PASSED on all four (`review/<m>_gait_gate.txt`). Window sections:

```
Thief
  standard Thief A          wander: Walking x1.19  chase: Jog x1.03
  standard Thief B          wander: Walking x1.24  chase: Jog x1.07
  standard Thief C          wander: Walking x1.29  chase: Jog x1.11
  maw      Thief A          wander: Jog x0.87      chase: Sprint x1.05
  maw      Thief B          wander: Jog x0.88      chase: Sprint x1.06
  maw      Thief C          wander: Jog x0.89      chase: Sprint x1.07
Troglodyte
  standard Troglodyte A     wander: Lope x0.97     chase: Jog x0.97
  standard Troglodyte B     wander: Lope x1.06     chase: Jog x1.06
  standard Troglodyte C     wander: Lope x1.15     chase: Jog x1.15
  maw      Troglodyte A     wander: Jog x0.91      chase: Sprint x1.25
  maw      Troglodyte B     wander: Jog x0.93      chase: Sprint x1.28
  maw      Troglodyte C     wander: Jog x0.95      chase: Sprint x1.31
Vampire
  standard Vampire A        wander: Walking x1.00  chase: Jog x1.13
  standard Vampire B        wander: Walking x1.09  chase: Jog x1.23
  standard Vampire C        wander: Walking x1.18  chase: Jog x1.33
  maw      Vampire A        wander: Jog x1.05      chase: Sprint x1.29
  maw      Vampire B        wander: Jog x1.08      chase: Sprint x1.32
  maw      Vampire C        wander: Jog x1.10      chase: Sprint x1.35
Monk
  standard Monk A           wander: Walking x0.98  chase: Jog x1.10
  standard Monk B           wander: Walking x1.08  chase: Jog x1.21
  standard Monk C           wander: Walking x1.18  chase: Jog x1.32
  maw      Monk A           wander: Jog x1.10      chase: Sprint x1.27
  maw      Monk B           wander: Jog x1.13      chase: Sprint x1.31
  maw      Monk C           wander: Jog x1.16      chase: Sprint x1.34
```

Floor: ok on every descriptor. `check_winding.py`: 0 inverted on all four. Probes per model: `review/<m>_probes.txt`
(`scripts/probes.sh`).

| | Thief Jog / Sprint | Troglodyte Lope / Jog / Sprint | Vampire Jog / Sprint | Monk Jog / Sprint |
|---|---|---|---|---|
| head bob (bob_audit measure) | 4.8 / 6.5 % | 5.8 / 5.2 / 5.5 % | 6.2 / 5.0 % | 7.0 / 5.4 % |
| planted toe-out L / R (deg) | +5.0 / +4.9, +5.1 / +5.0 | +5.4 / +5.0, +5.0 / +4.9, +5.1 / +5.0 | +5.0 / +5.4, +5.1 / +5.0 | +5.0 / +5.5, +5.1 / +5.0 |
| swing heading range (deg) | -5.2..+7.4, -6.4..+6.5 | +3.3..+10.1, -5.3..+7.3, -6.4..+6.4 | +2.1..+9.4, -6.4..+6.4 | +2.1..+9.4, -6.4..+6.4 |
| forearm/hand inside legs or trunk | 0 / 0 | 0 / 0 / 0 | 0 / 6 mm (3 %) | 21 mm (35 %) / 3 mm (3 %) |
| lowest skin | 0.0 cm | 0.0 cm | 0.0 cm | 0.0 cm |

Installed feet for comparison: Thief `Running` +14 / +32 deg toe-out, Troglodyte `Running` -0 / -0 (swing to +31),
Vampire `Walking` +9 / +9, Monk `Walking` +13 / +7. Phase: every new clip puts the left foot forward-most at the
model's `Walking` phase (Thief 0.18, Troglodyte 0.25, Vampire and Monk 0.75; the Thief's and Troglodyte's installed
`Walking` and `Running` agree). Wrist maxima equal the base clips' (Thief 45 deg, Vampire 17, Troglodyte 102 and Monk
117 inherited from `Running` / the folded `Walking`). Arm skin stretch p99 within 0.06 of the base clip's.
Legs through the skirt (`scripts/skirt_poke_probe.py`, horizontal rays from the pelvis axis): Vampire `Walking`
front 0 %, back 80 % up to 17 cm (its known back vent); Jog front 0, back 16 % / 2 cm; Sprint front 0, back 32 % /
25 cm (the trailing calf leaves under the back hem, under the cape). Monk `Walking` front 36 % / 20 cm, back 80 %;
Jog front 8 %, back 52 %; Sprint front 0, back 68 % (the same probe reads the installed walk as worse).

Playback: `tools/run_creature_review.py check` and `playback` on `../../mm7_<m>_gait_h08_claude/` (no console errors;
recordings at normal and half speed in their `review/playback/`), sheets `review/<m>_playback_sheet.png`, viewer
shots per clip and view `review/<m>_<clip>_{left,quarter,front,rear}.png`, looked at.

## Doubts

- Troglodyte: `Lope` is a run bound to the walking slot (its wander speed is a run pace for its body); `Walking` is
  no longer played. The sprint is crouched and long (5.6 leg lengths per stride) to reach 8.3 u/s. The jog's left
  upper arm is turned out up to 23 deg to clear the toes.
- Vampire: the sprint's bent arms rise to chin height at times (Walking's swing x2.4); the trailing leg shows below
  the back hem behind the cape (25 cm by the probe) where the walk shows 17 cm through its vent.
- Monk: running with folded arms (kept: unfolding would show the 3 % hands); the robe bells out widely in the jog
  (the larger leg capsules); jog bob 7.0 % is at the top of the 4-7 % range.
- Thief: the sheath tip bends up to 5.9 cm away from the dagger frame at the deepest knee lift (sheath skinning).
- MAW wandering (hostile speed) is not judged by the gate; all four play a run there inside the window anyway.
- Not run: in-game captures and the headless actor regressions (bindings not applied yet).

## Shared tools and pilot

Copied from `../../mm6_sprint_humanoids_claude/scripts/` (unchanged there): `compose_gait.py` here adds
`follow_skin`, `cloth`, `track_out`, `lift_scale`, `contact_equal`, `clear_iterations`; `gaitlib.py` and the probes
take this directory's depth (`ROOT`). Problems found: `gait_gate.py` floor-judges the walking-role clip with the
walking rule (a foot always within tolerance), which a lope bound as `walking` has to meet; that is intended, noted
for other run-paced wanderers.

## Rebuild

`scripts/rebuild.sh [m410 m418 m422 m290]`: composes every export from `work/mm7_<m>_pre_gait.glb` and `jobs/`, runs
the byte check, `gait_gate.py` and `check_winding.py`. Library loops in `work/sources/` (copied from the pilot's and
the pirates' `work/sources/`, library-derived: never commit). Cloth chains: `scripts/dump_chains.py` (Blender).
Probes: `scripts/probes.sh <m> <old clips> <new clips> [skirt]`; viewer: `scripts/build_viewer.py`, then
`python3 tools/run_creature_review.py --project level_generation/creatures/mm7_<m>_gait_h08_claude playback`,
`scripts/playback_sheet.py`, `scripts/shots.sh`. Install: `tools/install_model.py export/mm7_<m>.glb --world mm7`.
A far-LOD repair rerun or any re-export of these models must re-graft the new clips (rerun this rebuild on the new
source, or graft them with `claude_shared/graft_clips.py`).
