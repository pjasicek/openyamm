# MM7 Cleric Sun (mm7_m174): casting arm through the sun mantle (follow-up 2, 2026-11-12)

Follow-up to the [attack of 2026-11-11](../mm7_m174_attacks_claude/README.md) (MM9 MONK `AttackRanged2`), under the
rules of the [audit fixes](../audit_mm678_20261111/fixes/COMMON.md) (lease `mm7:m174`). Before:
`work/before_followup2/mm7_m174.glb` (the 2026-11-11 install, SHA-256 3c1db1a9…); `actors.yml` is unchanged (impact
0.6, release `palm_right`).

## Problem

The user, in the [compare viewer](../audit_mm678_20261111/compare_viewer/?role=attack_melee#mm7_m174), asked "warped or
broken hand?". From about 0.45 s to 0.85 s the right upper arm disappeared inside the big yellow mantle, and the
forearm came out of the chest and went sideways. That reads as a broken arm (`review/cmp_grid.png`,
`review/cur_att_3q_strip.png`).

## Cause

The 2026-11-11 job swung the right upper arm 25° inward and 15° down (`extra.pre`, without `chain`) to bring the
donor's diagonal thrust in front of the chest. The forearm kept the donor's world direction. In the chest frame the
upper arm then pointed straight forward (0.97 of it along +Z), and the forearm pointed straight out to the right.
The mantle's front panels are skinned to the spine, so they stay put, while its sides ride on the arm bones. An upper
arm swung forward therefore runs under the front panel, and the forearm leaves through the gap between the panels.
`scripts/arm_info.py` prints these directions per time.

## Fix: the arm re-aimed in the chest frame (`scripts/arm_aim.py`, job `jobs/attack_arm.json`)

Native `m174ae0` (front) holds the elbow out to the side, with the forearm folded in and the palm open in front of
the right chest. `ae2` (side) shows the forearm reaching forward out of the mantle. The right arm of the installed
Attack is re-aimed through direction keys in the chest frame, blended in from 0.30–0.50 s and out from 0.98–1.08 s.
Body, trunk turn, left arm, robe chains and timing are unchanged.

- 0.42 s: the wind-up as before, arm out to the side.
- 0.56–0.74 s (impact 0.6): upper arm out to the side and a little forward (-0.85, -0.13, 0.5), elbow bent about 73°,
  forearm forward and slightly up and in. The palm faces forward with the fingers up (a palm-out cast in front of
  the right chest). The upper arm stays out through the mantle's side, which lifts with it, and never passes under
  the front panel.
- 0.87–1.0 s: the arm comes down along the side to Standing, not forward under the mantle.
- The hand's orientation is set in the chest frame, and the forearm takes its roll, so the wrist does not twist. The
  forearm twist bone blends to its Standing local.

## Numbers and checks (`review/finish.txt`)

| | 11-11 install | Now |
|---|---|---|
| Right upper arm at impact (chest frame) | (-0.11, 0.21, 0.97), straight forward | (-0.85, -0.13, 0.51), to the side |
| R wrist swing / twist max, twist step (48 fps) | 17° / 70°, 8.2° | 54° / 48°, 8.2° |
| Hand in body, forearm in body (R) | 0, 0 | 0, 0 |
| Motion ratio, peak speed | 0.52, 1.87 | 0.52, 1.63 |
| Deformation beyond Standing (worst) | spine (mantle) 8.5 | spine 8.3, hand 1.6 |

- `glb_diff.py`: only Attack samplers changed (upper arm, forearm, hand and forearm-twist rotations of the right arm).
- Winding 0. `floor_audit.py` 0 problems (Cleric Sun A/B/C).
- The arm-and-hand gate (`mm9_guard_claude/scripts/arm_hand_gate.py`, `review/gate.json`): hand and forearm out of
  the body; finger stretch 1.02–1.1. The left arm is unchanged.
- Regression, the whole actors suite (`work/regression_actors_rerun.log`): 191 passed, 2 failed. The every-binding
  case and the Cleric cases pass. The two failures are unrelated: 42 MM9 maps without models, and
  `out05_event_clearance`. The first run (`work/regression_actors.log`) failed 66 cases on one mm6 texture that
  another agent's install re-cooked at 10:18, mid-run.
- Viewer: `review/viewer/` with no console errors (60 switches). Every tier: `review/f_tiers.png` (A, B, C front at
  0.6; in each pair, left is the 11-11 install and right is the fix). The motion strip (three-quarter, 0.3–0.92 s) is
  `review/f_3q_strip.png`, and the hand close-up is `review/t8_hand_closeup.png`.
- Compare viewer (left HEAD, right installed): `review/final_sheet.png`, `final_attack_{front,3q,side}_t0.55.png`.

Revert: `python3 tools/install_model.py level_generation/creatures/mm7_m174_followup2_claude/work/before_followup2/mm7_m174.glb --world mm7`
(the 11-11 attack). For the state before the attack, use `../mm7_m174_attacks_claude/work/before_attacks/mm7_m174.glb`
plus that folder's `actors_entries.yml` (impact 0.483).
