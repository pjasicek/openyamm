# MM7 Mage (m274): attack from an MM9 donor (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). The Mage's `Attack` (humanoid set
Unarmed Cast R Attack 1: a planted right-palm push, motion ratio 0.39) is replaced in place by a clip retargeted from
**MM9 LICH `AttackRanged`**, mirrored. Route and tools as the [Warlock pilot](../mm7_m426_attacks_claude/README.md)
(`../audit_mm678_20261111/fixes/attack_tools/donor_attack.py`, job `job_attack.json`, no Blender).

## Intent and the staff

Native `m275a` (8 frames x 125 ms, contact frame 5 = 0.625 s): the staff is raised, swung toward the target and the
spell bursts, with a lean and the free arm thrown back. The lich raises one arm high and flings it forward and down
with a hunch while the other arm swings back. Retargeted onto the staff arm, the orb ended up by the face and the
butt pointed at the target: our grip runs the staff up along the hanging forearm (150° to it), so any forward arm
thrust swings the orb backward, and pointing it forward would need a ~120° wrist bend. The clip is therefore
**mirrored**: the lich's casting arm drives the free right hand (the previous attack also released from `palm_right`),
and the staff arm keeps half of the lich's off-arm motion (`gain_bone` 0.3–0.6), so the staff stays upright and tips
its orb ~25° toward the target at the release.

## Settings

Timing 1.3 s (donor 1.2 s), donor release 0.447 s mapped to 0.6 s; robe (12 chains) and cape sheet (5 chains)
simulated as on the Warlock (Standing rest, chain floor 0.8 cm, `hem_floor` 3 mm; settle offset 0 cm); floor lift
1.3 cm from leg-weighted vertices near the floor (a calf-weighted hem vertex dipped 1.5 cm in the lunge); wrist limit
not reached beyond 51°. Release measured: `Socket_Palm_R` at 95 % of its 1.46 m back-to-front travel at **0.583 s**
(native 0.625 s).

## Results (installed 2026-11-11)

| | Before | After |
|---|---|---|
| Motion ratio | 0.39 | **0.90** |
| p90 reach / moving share / peak speed | 0.104 / 0.498 / 1.98 | 0.356 / 0.951 / 3.86 |
| Deformation beyond Standing (worst) | spine 5.6 | arm 5.7, cloth 4.4 |
| Wrist swing / twist | | L 19°/8°, R 50°/20° |
| Hand in body | 0 | 0 (the right forearm reads 5.8 cm "inside" its wide sleeve, as Standing reads 5.3) |
| Floor | -0.7 cm | -0.5 cm |

Bindings (Mage A/B/C): `events.attack_melee.impact` and `attack_ranged.impact` 0.498 -> 0.583 (release
`palm_right`, glow `palm_right` + `staff_head` unchanged). Checks in `review/finish.txt`: winding 0, glb_diff only the
Attack channels, floor audit 0 problems, every-binding regression PASS, viewer no console errors. Shots:
`review/attack_viewer_sheet.png`; native strip `review/native_attack.png`. Rollback: `work/before_attacks/`.
Credits: 0.
