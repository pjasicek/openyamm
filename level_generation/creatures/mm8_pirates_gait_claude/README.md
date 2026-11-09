# MM8 pirates: Walk2 and Jog (2026-10-21)

New in-place locomotion clips for the three installed MM8 pirates, so every tier's walk and chase play near their
authored speed (gait window 0.75–1.5×; the engine advances a clip by distance, `ActorModelPresentation.h`). The old
runs were full sprints (authored ≈5.3 m/s) that crawled, so chasers walked at up to 2×. Existing clips are untouched
(binary prefix of each GLB identical); `Walk2` and `Jog` are appended. No Meshy credits, no paid actions; sources
are local library clips (Mixamo, humanoid set). `actors.yml` is not edited here (bindings below are for the
coordinator).

| Model | Walk2 source, length, gate stride | Jog source, length, gate stride |
|---|---|---|
| m412 Warrior | Mixamo Walk (the installed walk's source), 1.05 s, 1.4998 | Mixamo Running (5), 0.833 s, 2.3583 |
| m416 Crossbowman | Mixamo Walking (4), 1.233 s, 1.3276 | Mixamo Jogging (first loop, 0.848 s), 0.85 s, 1.8976 |
| m420 Mage | humanoid set Staff-Walk-Slow-WithStaff, 1.6 s, 1.2486 | Mixamo Jogging, 0.85 s, 1.3514 |

Bindings that passed `gait_gate.py` (every descriptor of the model): `walking: Walk2`, `run: Jog`,
`stride_length` / `run_stride_length` = m412 1.4998 / 2.3583, m416 1.3276 / 1.8976, m420 1.2486 / 1.3514.
Gate outputs: `review/<model>_gait_gate.txt`. m412 and m416 PASS; m420 fails the window only on two tiers the two
clips cannot cover (wander speeds span 0.50–1.26 m/s): Pirate Mage A wandering ×0.64 and Wimpy Pirate Mage C
wandering ×1.61 / chasing ×1.58 (before: ×0.28–1.20).

## Method (`scripts/compose_gait.py`, jobs in `jobs/`)

Authored on the installed GLB in numpy (no Blender re-export); the clip is appended with `glb_pose` accessors at
120 Hz. Legs, pelvis and trunk rhythm come from the library loop; arms, hands, fingers, twist bones and props
(cutlass/hook, crossbow carry with strings, bolt and quiver, cobra staff) are the pirate's own accepted
`Walking` (for Walk2) or `Running` (for Jog), phase-aligned on the left foot's forward-most point, so grips, finger
solves and prop clearances are the accepted ones.

- `extract_source.py` (Blender) dumps a library clip; `gaitlib.Cycle` cuts one loop (fractional period for
  multi-loop clips), removes seam drift/root travel, and faces it along the planted feet's slide (the toe-tail
  heuristic was 7° off on Walking (4) and 52° on Slow Jog; Slow Jog was dropped).
- Treadmill mapping: positions × leg-length ratio k, forward × c so planted feet slide at stride/length. Pelvis
  height from a stance-extension target (walk 0.98, jog 0.95), lowered smoothly where a leg would overreach; source
  bob scaled (`bob`). Trunk: the source's world rotation change about its loop mean on our mean posture (`lean`
  blends the base clip's mean toward Standing: m412 jog 0.6, m420 jog 0.55 — the sprint lean read as hunched);
  neck 0.5, head 0.3 (stabilised).
- Legs: analytic two-bone IK, knee in the source leg plane, hinge axes measured on the base clip; foot rotation =
  source change about its stance mean on the base clip's stance foot; toes as Standing; the Mage's peg (`rigid_foot`)
  keeps Standing's foot-to-calf rotation.
- Floor: LOD0 soles (below 6 cm in Standing) set on the floor in the source stance, lifted where they would go
  under; walks are grounded every frame (whole-body shift, σ 6 keys) so a foot is always down.
- Planted soles: per side, the integrated speed error of sole vertices within 6 mm of the floor corrects the ankle's
  forward path (carried linearly across the swing, no pop). The peg touched down while still swinging forward; there
  the peg is kept just off the floor (`lift_skids`).
- Arm clearance (`clear_arms`): where a forearm/hand enters the legs or trunk skin, the upper arm turns about the
  shoulder along that skin's normal by the least smoothed angle (m416 Jog: left arm ≤ 7.5°, it brushed the left thigh
  27 mm deep). Off for the Mage: his coat is an open shell, so the inside test is meaningless there (his accepted
  Walking already "touches" it 52 % of the time).

## Checks (`review/`)

- `final_probes.txt`: per-side planted stride (`stride_probe.py`, 1 cm band, also reads the peg), jerk/bob/wrist
  (`motion_probe.py`), forearm/hand and prop contacts (`contact_probe.py`; legs+trunk, and lower legs only).
  Walk2 pelvis step per 1/48 s: m412 0.97 cm (installed Walking 1.25), m416 0.64, m420 0.31. No arm or prop inside
  the legs/trunk in any new clip except the Mage staff brushing his open coat (2 % of samples, 9 mm) and his hand on
  the coat, as in his accepted clips. Wrist maxima equal the base clips' (arms are the base clips').
- `check_winding.py`: 0 inverted closed parts on all three exports. Floor audit of the installed pirates: 0 problems.
- Focused actor regressions pass after install: `mm8_pirate_actor_models_keep_native_roles`,
  `mm8_female_crossbow_pirate_actor_models_keep_tiers_equipment_and_release`,
  `mm8_pirate_mage_actor_models_keep_palettes_staff_cast_and_simulation`.
- Renders: `review/final/<model>_<clip>.png` (Blender Workbench, props baked flat by `review_glb.py`).
- Browser playback (normal and half speed, `tools/run_creature_review.py`): `../mm8_m412_gait_claude/`,
  `../mm8_m416_gait_claude/`, `../mm8_m420_gait_claude/` (`review/playback/`, `review/playback_sheet.png`); the
  wrapper wants a direct child of `creatures/` per viewer and the clip lengths differ per model, hence three dirs.

## Doubtful / left open

- m416 Jog keeps bent knees (pelvis lowered up to 7 cm where the stride overreaches): a low, grounded jog.
- m420 Jog: the peg's planted speed reads 1.17 vs the binding 1.35 at 1 cm (the gate counts only foot-skinned
  vertices, the shoe: 1.35); the peg skids a little at touch-down and lift-off.
- The gate's vertex stride counts toe-off/landing vertices within its 2.2 cm band; on runs it reads up to ~10 %
  above the truly planted speed, so the bound run strides were chosen from the gate's own measurement.

## Rebuild

From this directory: `python3 scripts/compose_gait.py ../mm8_<m>_reduce_claude/work/mm8_<m>_pre_gait.glb
../mm8_<m>_reduce_claude/export/mm8_<m>.glb jobs/<m>_jog.json jobs/<m>_walk.json`, then `check_winding.py`,
`gait_gate.py --candidate ... --set walking=Walk2 --set run=Jog`, `tools/install_model.py <export> --world mm8`.
Sources: `extract_source.py` (Blender) into `work/sources/` (library-derived, never commit).
