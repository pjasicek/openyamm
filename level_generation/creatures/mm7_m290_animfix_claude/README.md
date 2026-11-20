# MM7 Monk (mm7_m290): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1. Jog and Sprint from
[package h08](../gait_rollout_20261031/h08/README.md). Before: `work/before_anim/mm7_m290.glb` (SHA-256 af614b64…, the
h08 export byte for byte) and `work/before_anim/actors_mm7.yml`.

## Jog and Sprint: the closed robe belled out and stretched

**Audit:** cloth bad Jog 33.2, Sprint 33.7 (Standing 1.7). **Cause:** h08's robe sim (`scripts/cloth_sim.py`) keeps
the legs inside the robe with leg capsules at twice the leg radius (`leg_r` 2.0); with the long strides (Jog 2.64 m,
Sprint 3.4 m) the chains splay into a bell and the panels between them stretch.

**Fix** (h08 composer copied to `scripts/`; it reproduces the installed export byte for byte):
- Jog: stride 2.2 m in 0.72 s (was 2.64 in 0.80), robe `leg_r` 1.2.
- Sprint: stride 2.7 m in 0.52 s (was 3.4 in 0.60), robe `leg_r` 1.2.
Experiments in `work/exp/` (`../audit_mm678_20261111/fixes/anim_tools/exp_job.py`; lower lift, margin, bend limits and
trajectory smoothing changed little; the leg radius and the stride did).

| Clip | Cloth bad (Standing 1.7) | Notes |
|---|---|---|
| Jog | 33.2 -> 15.4 | |
| Sprint | 33.7 -> 18.0 | 16.3 beyond Standing (target 15); a wider leg radius brings the bell back (leg_r 2.0: 25.3) |

Trade-off: with the narrower capsules the trailing calf comes out under the back hem in the sprint (seen in the
viewer from behind) instead of lifting the robe into a bell; `skirt_poke_probe.py` reads Jog 52 -> 95 %, Sprint 68 -> 75 %
of samples, but this probe reads 80 % / 257 mm on the accepted Walking too, so it overcounts on this robe.

Bindings: `run_stride_length` 2.6533 -> 2.2145, `sprint_stride_length` 3.4373 -> 2.6915. Checks: `gait_gate.py` PASSED
(Standard chase Jog x1.19–1.42; MAW chase Sprint x1.41–1.48, near the 1.5 top); winding 0; only Jog/Sprint samplers
changed; probes (`review/m290_probes.txt`): bob Jog 5.6 % (was 7.0, uneven 0.34 was 0.47), Sprint 5.1 %, toe-out 5°,
lowest 0.0 cm; folded-arm contacts Jog 41 % / 35 mm (installed 35 % / 21 mm; accepted Walking 100 % / 40 mm), Sprint
3 % / 3 mm as before; `floor_audit.py`, `gait_audit.py` (both rulesets) clean; regression
`mm6_mm7_mm8_actor_models_build_every_binding` PASS; viewer `check` no errors. Sheet:
`review/jog_sprint_viewer_before_after.png` (top installed, bottom fixed; rear and side views).

Rebuild: `python3 scripts/compose_gait.py work/mm7_m290_pre_gait.glb export/mm7_m290.glb jobs/m290_jog.json
jobs/m290_sprint.json`.

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.6** (`scale_keys.py --joints '*' --factor 0.6 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 0.0, 'arm': 11.9, 'head': 2.2, 'spine': 31.5, 'leg': 0.0, 'cloth': 1.4} -> {'hand': 0.0, 'arm': 8.5, 'head': 0.3, 'spine': 19.7, 'leg': 0.0, 'cloth': 1.4} {'peak_speed': (2.83, 1.9), 'amp_p90': (0.2248, 0.1422), 'body_share': (0.449, 0.336)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check (see finish.txt: not all clean); arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
