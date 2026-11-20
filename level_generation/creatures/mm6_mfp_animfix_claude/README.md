# MM6 PeasantF3 (mm6_mfp): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1 (skirts in the gait clips).
Production: [mm6_mfp_reduce_claude](../mm6_mfp_reduce_claude/README.md); gait clips from
[package h05](../gait_rollout_20261031/h05/README.md). Before: `work/before_anim/mm6_mfp.glb` (SHA-256 380a3689…, the
h05 export byte for byte) and `work/before_anim/actors_mm6.yml`; together they revert this change.

## Jog and Sprint: the wrap skirt ballooned into an egg

**Audit:** cloth region bad 47.6 % (Jog), 59.6 % (Sprint) against 0.0 in Standing; the accepted Walking 8.2, Running
19.7. **Cause:** the h05 jog and sprint lift the knee high (`swing_height` 0.65) over a long stride, and her five-ring
skirt cage (`scripts/ring_skirt.py`) holds every leg vertex: `posed_band` rings 1–2 and `knee_out` wrapped the raised
knee, and 30 push-out passes inflated the hem around both legs. Thigh separation peaks at 89° (Jog) and 99° (Sprint)
against Running's 65°.

**Fix:** the h05 composer (copied to `scripts/`, path depths adjusted; it reproduces the installed export byte for
byte from `work/mm6_mfp_pre_gait.glb`), new jobs in `jobs/` (Walk2 unchanged):
- Jog: `swing_height` 0.30, stride 2.05 m over 0.58 s (was 2.4 over 0.63), no posed band, no knee push.
- Sprint: `swing_height` 0.25, stride 2.6 over 0.46 s (was 3.4 over 0.56), no posed band or knee push, 3 push-out
  passes, rings widen at most 1.4x (`max_scale`, new in `ring_skirt.py`).
A plain, shorter-stepped civilian run: the low knee keeps the cloth, the cadence keeps the speed. Experiments in
`work/exp/` (`run.sh`/`runs.sh`; 20 variants: capping alone, or a lower mid-line follow, did not help; the push-out
and the knee height did).

| Clip | Cloth bad (Standing 0) | Legs through the skirt (`skirt_probe.py`) | Stride / length | Peak speed |
|---|---|---|---|---|
| Jog | 47.6 -> 13.4 | 82 % 31 mm -> 54 % 18 mm | 2.41/0.63 -> 2.05/0.58 | 3.02 -> 2.09 |
| Sprint | 59.6 -> 11.1 | 79 % 34 mm -> 82 % 33 mm | 3.41/0.56 -> 2.6/0.46 | 4.23 -> 3.33 |

Bindings (`actors.yml`, PeasantF3 A–C, written by `../audit_mm678_20261111/fixes/anim_tools/binding_set.py`):
`run_stride_length` 2.41 -> 2.05, `sprint_stride_length` 3.41 -> 2.6.

Checks: `gait_gate.py` PASSED (Standard chase Jog x1.05–1.26, MAW wander Jog x1.05–1.11, MAW chase Sprint x1.32–1.38;
measured strides 2.058 / 2.588); `check_winding.py` 0 inverted; identity: the pre-gait prefix is byte-identical, only
Jog and Sprint samplers changed (`glb_diff.py`); probes (`review/mfp_probes.txt`): head bob Jog 4.4 %, Sprint 4.0 %,
toe-out 5°, lowest skin +0.01 cm, arm/hand/knife contacts 0 %, wrist max 58° (base Running 58°), arm stretch p99 as
Running; `floor_audit.py` 0 problems; `gait_audit.py` 0 flagged in both rulesets; regressions
`mm6_mm7_mm8_actor_models_build_every_binding` and `mm6_peasant_f3_actor_model_tiers_share_the_native_height` PASS;
viewer `check` no console errors (66 switches). Other nine clips unchanged (`audit_export/`).
Sheet: `review/jog_sprint_viewer_before_after.png` (viewer, tier A; top installed, bottom fixed).

Rebuild: `python3 scripts/compose_gait.py work/mm6_mfp_pre_gait.glb export/mm6_mfp.glb jobs/mfp_walk2.json
jobs/mfp_jog.json jobs/mfp_sprint.json`, then `bash scripts/gates.sh mfp Walking,Running Walk2,Jog,Sprint 107.5
Knife=mm6_mfp_knife.glb --set walking=Walk2 --set stride_length=1.6 --set run=Jog --set run_stride_length=2.05 --set
sprint=Sprint --set sprint_stride_length=2.6`.
