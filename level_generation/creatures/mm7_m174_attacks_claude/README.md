# MM7 Cleric Sun (m174): attack from an MM9 donor (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). The `Attack` (humanoid set Unarmed Cast
R Attack 1, motion ratio 0.32 against the MM9 median of the audit's "other" bodies: this robe has its legs stripped)
is replaced in place by a clip retargeted from **MM9 MONK `AttackRanged2`** (route and tools as the
[Warlock pilot](../mm7_m426_attacks_claude/README.md); job `job_attack.json`).

## Intent: a restrained cast (gate exception)

Native `m175a` (7 frames x 125 ms, contact frame 5 = 0.625 s) is a planted one-palm cast: the right arm swings out to
the side, sweeps in and the palm flares in front of the chest; the body barely moves in any of the seven frames
(`review/native_attack.png`). The motion-ratio gate of 0.75 is waived for this model as the brief allows; the result
is **0.52** (from 0.32). Adding trunk motion the sprite does not show was rejected, and the mantle limits it anyway.

## Settings

- The Monk is a robe body without pelvis or thighs: our pelvis follows its `Bip01 Spine` root, the spine its
  Spine2/Spine3, the feet stay planted by IK (`feet: planted`); facing from the clavicles (turn 2°).
- Off (left) arm at 0.6 of the donor: at full strength it swung back and stretched the sun mantle 16 % (8.5 % now).
- Right upper arm swung 25° inward and 15° down over 0.3–1.0 s: the donor's thrust went diagonally out to the right
  at mask height; the palm now finishes in front of the chest as native `ae`.
- Timing 1.1 s (donor 0.9 s), donor release 0.45 s mapped to 0.55 s; robe (14 chains) re-simulated toward the
  Standing shape (settle offset 0), `hem_floor` 3 mm (the hem dipped 2.2 cm); no leg vertices to floor.
- Impact 0.6 s: the palm reaches the chest centre then (95 % of its forward travel is at 0.50 s, mid-sweep); native
  contact 0.625 s.

## Results (installed 2026-11-11)

| | Before | After |
|---|---|---|
| Motion ratio ("other" reference) | 0.32 | **0.52** (restrained native) |
| p90 reach / moving share / peak speed | 0.091 / 0.306 / 2.03 | 0.154 / 0.742 / 1.87 |
| Deformation beyond Standing (worst) | spine 11.6 | spine (mantle) 8.5 |
| Wrist swing / twist | | L 39°/35°, R 17°/70° |
| Hand in body | 0 | 0 (the left forearm reads 4.5 cm in its sleeve, as in Standing) |

Bindings (Cleric Sun A/B/C): `events.attack_melee.impact` and `attack_ranged.impact` 0.483 -> 0.6 (release
`palm_right` unchanged). Checks (`review/finish.txt`): winding 0, glb_diff only the Attack channels, floor audit 0
problems, every-binding regression PASS, viewer no console errors. Shots: `review/attack_viewer_sheet.png`.
Known and unchanged: the robe's front split (Smart Topology fold) opens a little with the trunk turn.
Rollback: `work/before_attacks/`. Credits: 0.
