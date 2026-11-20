# MM6 Sorcerer (mm6_sor1): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1. Production:
[mm6_sor1_codex](../mm6_sor1_codex/); Jog from [package h03](../gait_rollout_20261031/h03/README.md). Before:
`work/before_anim/mm6_sor1.glb` (SHA-256 6f0b51ad…, the h03 export byte for byte) and `work/before_anim/actors_mm6.yml`.

## Jog and Walking: the floor-length robe stretched

**Audit:** cloth bad Jog 37.5, Walking 21.9 (Standing 0.7); mostly stretch (s1 > 1.6) between the 16 robe chains.
**Causes:** the Jog's high knee and long stride (`swing_height` 0.5, 2.7 m in 0.66 s) pushed the chains apart (the sim
keeps the legs inside the robe); the installed Walking's robe was the Codex project's bake with its later contact
passes, which leave the chains splayed at mid-step.

**Fix** (h03 composer and its numpy robe sim `cloak.py` preset `sor1`, copied to `scripts/`):
- Jog recomposed: `swing_height` 0.3, stride 2.0 m in 0.56 s (job `jobs/sor1_jog.json`); `run_stride_length` 2.6955
  -> 2.0 in `actors.yml`.
- Walking: only the robe chains re-simulated over the installed Walking body with the same sim
  (`../audit_mm678_20261111/fixes/anim_tools/resim_cloak.py`, `leg_pad` 0.03 as the Jog); body, arms and staff
  unchanged.

| Clip | Cloth bad (Standing 0.7) | Legs through robe (`skirt_poke_probe.py`) | Loop pop |
|---|---|---|---|
| Walking | 21.9 -> 11.1 | 0 % -> 0 % | 0.0165 -> 0 H |
| Jog | 37.5 -> 14.0 | 0 % -> 0 % | |

Checks: `gait_gate.py` PASSED (Walking x1.06–1.27, Jog x1.06–1.27, both rulesets); winding 0; only Walking and Jog
samplers changed (`glb_diff.py`); probes (`review/sor1_probes.txt`): bob Walking 4.0 %, Jog 4.7 %, toe-out 5°, arm and
staff contacts 0 %, wrist max 45° (as Walking), lowest skin 0.0 cm, planted stride 2.007/2.009; `floor_audit.py` and
`gait_audit.py` clean; regressions `mm6_mm7_mm8_actor_models_build_every_binding`,
`mm6_sorcerer_actor_model_tiers_share_the_native_height` PASS; viewer `check` no errors. Sheet
`review/walk_jog_viewer.png` (viewer tier A: TOP the fix, bottom installed).

Rebuild: `python3 scripts/compose_gait.py work/mm6_sor1_pre_gait.glb work/jog_only.glb jobs/sor1_jog.json`, then
`python3 ../audit_mm678_20261111/fixes/anim_tools/resim_cloak.py work/jog_only.glb export/mm6_sor1.glb Walking
'{"chains": "work/sor1_robe_chains.json", "preset": "sor1", "leg_pad": 0.03}'`.
