# MM7 Cleric Moon (mm7_m170): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1. Walk2 and Jog from
[package h11](../gait_rollout_20261031/h11/README.md). Before: `work/before_anim/mm7_m170.glb` (SHA-256 91555d05…, the
h11 export byte for byte) and `work/before_anim/actors_mm7.yml`. Set up by
`../audit_mm678_20261111/fixes/anim_tools/setup_from_package.sh mm7 m170 h11 m170`.

## Jog and Walk2: the floor-length robe stretched

**Audit:** cloth bad Jog 27.2, Walk2 19.6 (Standing 3.0). Legless robe (hidden feet), so the hidden legs' lift and
stride drive the robe chains through h11's cloth sim. **Fix** (h11 composer): Jog `swing_height` 0.3, 1.8 m in 0.70 s
(was 0.5, 2.14 m in 0.80 s); Walk2 `swing_height` 0.6 (was the composer default). Bindings: `stride_length` 1.417 ->
1.343 (Walk2's measured foot-joint stride after the change), `run_stride_length` 2.143 -> 1.8.

| Clip | Cloth bad (Standing 3.0) | Peak speed |
|---|---|---|
| Walk2 | 19.6 -> 13.8 | 2.54 -> 0.82 |
| Jog | 27.2 -> 12.2 | 3.94 -> 1.61 |

Checks (`review/finish.txt`, `review/m170_probes.txt`, `review/m170_gait_gate.txt`): gate PASSED with explicit strides
as h11 (hidden feet; wander Walk2 x0.95–1.18, chase Jog x0.99–1.24, both rulesets); winding 0; only Walk2/Jog samplers
changed; bob Walk2 2.9 %, Jog 4.8 %; toe-out 5°; lowest hem -0.1 / +0.4 cm; claws in the robe as the accepted Walking
(Jog L 86 % / 32 mm; Walking 94 % / 29 mm); floor and gait audits clean; every-binding regression PASS; viewer check
clean. Sheet `review/viewer_before_after.png` (top installed).

Rebuild: `python3 scripts/compose_gait.py work/mm7_m170_pre_gait.glb export/mm7_m170.glb jobs/m170_walk2.json
jobs/m170_jog.json`.
