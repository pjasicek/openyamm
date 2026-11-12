# MM8 Minotaur (mm8_m484): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1 (cloth in the gait clips).
Production: [mm8_m484_reduce_claude](../mm8_m484_reduce_claude/README.md); gait clips from
[package h20](../gait_rollout_20261031/h20/README.md). Before: `work/before_anim/mm8_m484.glb` (SHA-256 a91bcb77…, the h20
export byte for byte) and `work/before_anim/actors_mm8.yml`.

## Jog and Sprint: holes in the mail kilt

**Audit:** cloth bad Jog 43.4, Sprint 42.4, (unbound) Running 45.9 against Standing 3.5. **Cause:** the kilt hangs
from twelve translation-only controls (`Skirt_<F|B|L|R>_<pelvis|thigh>`) that h20's `kilt_solve` fitted per frame
against the body, starting from the accepted `Running`'s offsets (`from_base`) with a 1 cm margin. The controls of one
panel (pelvis, left-thigh and right-thigh parents) moved apart by up to 12 cm, which tore the panels; the high knee
(`swing_height` 0.7) needed the largest pushes. With every control at rest the Jog measures 16.9 but the kilt is
inside the thighs on every frame (up to 10 cm), so the controls are needed.

**Fix** (h20 composer copied to `scripts/`, path depths adjusted; reproduces the installed export byte for byte from
`work/mm8_m484_pre_gait.glb`):
- `scripts/kilt_solve.py` gains `couple`: a Laplacian over the controls of one panel side, so a panel moves as one
  piece.
- Jog and Sprint jobs: `swing_height` 0.45 (was 0.7), `kilt_solve` solved from zero (`from_base` off), `couple` 5,
  `reg` 0.1, `gap` -0.01, `margin` 0 (only points over 1 cm inside are pushed, to the surface). Strides unchanged.
Experiments in `work/exp/` (`run.sh`, 20 variants; lower knee alone, a smaller cap or no solve each left 30–45 %).

| Clip | Cloth bad (Standing 3.5) | Kilt inside the body > 1 cm (`kilt_depth_probe.py`) | Spine |
|---|---|---|---|
| Jog | 43.4 -> 17.1 | 52 % of samples, 54 mm -> 0 % | 27.6 -> 18.6 |
| Sprint | 42.4 -> 19.7 | 39 % / 99 mm -> 0 % | 27.1 -> 21.3 |

Sprint stays 16.2 points over Standing (target 15): the rest is the left pelvis side panel stretched by the sprint's
hip extension (independent of the solve: 18.6–19.7 in every variant; a 0.9 stride shortening reached 18.5); the
viewer shows no hole. Bindings: `run_stride_length` 2.2942 -> 2.266, `sprint_stride_length` 3.062 -> 3.065 (the new
clips' measured strides; `binding_set.py`).

Checks: `gait_gate.py` PASSED (Standard chase Jog x0.97–1.16, MAW chase Sprint x1.02–1.08; MAW wander Walk2
x1.66–1.76 is pre-existing and unjudged, h20); `check_winding.py` 0; prefix byte-identical, only Jog and Sprint samplers
changed; probes (`review/m484_probes.txt`): bob Jog 4.8 %, Sprint 5.9 %, toe-out 5°, lowest skin 0.0 cm, arm and axe
contacts 0 %, wrist max = base Running's (112°), arm stretch at or below Running's; `floor_audit.py` 0 problems;
regressions `mm6_mm7_mm8_actor_models_build_every_binding`, `mm8_minotaur_actor_models_keep_native_roles` PASS; viewer
`check` no errors (72 switches). Sheet: `review/jog_sprint_viewer_before_after.png` (top installed, bottom fixed).
`Running` (45.9 %) is not bound since h20 and was left.

Rebuild: `python3 scripts/compose_gait.py work/mm8_m484_pre_gait.glb export/mm8_m484.glb jobs/m484_walk2.json
jobs/m484_jog.json jobs/m484_sprint.json`.
