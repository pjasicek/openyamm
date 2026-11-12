# MM8 Cleric (mm8_m460): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1. Jog from
[package h18](../gait_rollout_20261031/h18/README.md). Before: `work/before_anim/mm8_m460.glb` (SHA-256 7da7b6d1…, the
h18 export byte for byte) and `work/before_anim/actors_mm8.yml`.

## Jog: the closed robe stretched

**Audit:** cloth bad Jog 23.2 (Standing 1.2). **Fix** (h18 composer, `cloak.py` preset `m460`): Jog `swing_height`
0.4 kept, stride 1.8 m in 0.62 s (was 2.2 m in 0.72 s); `run_stride_length` 2.216 -> 1.805. Lower knees (0.25–0.3)
measured lower cloth (12.6–14.8) but the left sole then barely lifted (planted stride L 0.37–0.56 against R 1.86) and
the hem dipped 1.3 cm under the floor; rejected. Re-simulating the installed Walking's robe (17.7) made it worse (20.3);
Walking stays.

| Clip | Cloth bad (Standing 1.2) | Leg | Robe poke |
|---|---|---|---|
| Jog | 23.2 -> 16.1 (14.9 beyond Standing) | 10.8 -> 9.3 | 0 % -> 0 % |

Checks (`review/finish.txt`, `review/m460_probes.txt`): gate PASSED (chase Jog x0.99–1.24); winding 0; only Jog
changed; bob 4.6 %; planted stride 1.803 / 1.815; arm and staff contacts 0 %; lowest 0.0 cm; floor and gait audits
clean; regression PASS; viewer clean. Sheet `review/jog_viewer_before_after.png` (top installed).

Rebuild: `python3 scripts/compose_gait.py work/mm8_m460_pre_gait.glb export/mm8_m460.glb jobs/m460_jog.json`.
