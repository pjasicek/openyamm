# MM7 zBlasterGuy (m475): attack with an authored recoil (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). The `Attack` (humanoid set 1Hand Pistol
Attack R1, aimed forward: an arm-only aim and shot, motion ratio 0.30) is replaced in place by the same aimed shot
followed by an **authored whole-body recoil**, built with the attacks tools
(`../audit_mm678_20261111/fixes/attack_tools/donor_attack.py`, job `job_attack.json`, the model's own clip as donor).

## Why no MM9 or LoMM donor

The suggested LoMM player clips are recoil twitches: `Wattack_wand1` (0.2 s) and `Wattack_Crossbow1` (0.25 s) move
the hands 5–10 % of the body height and the pelvis not at all (measured on `PLAYER/BASE.abc`; `taunt1-3` and
`Wattack_throw` are the only large LoMM player motions and are not shots). MM9 has no gunman. The playbook's other
route was used: keep the accepted aimed shot (its grip, blaster and fingers pass through unchanged) and author the
blow on top of it.

## Intent

Native `m475a` (8 frames x 125 ms, contact frame 5 = 0.625 s; `review/native_attack.png`): he aims, the muzzle
flashes, the recoil throws the blaster up above his head as he turns and leans back with the cloak flaring, then
lowers it.

## Settings

- Aim and shot as before up to 0.62 s (the muzzle is fully forward at 0.6 s); the rest of the donor stretched to
  1.35 s for the recoil.
- Recoil (eased in over 0.06–0.08 s, held, eased out by 1.2–1.28 s): chest thrown back 34° (B_Spine1 22° + B_Spine2
  12°, carrying the arms), hips 25 cm back and 10 cm down over planted feet (IK miss 0), hips turned 45° to the right,
  the gun arm flung up 25° and out 35° on top of the chest lean, head 8° forward and 10° tilted.
- Two earlier variants were rejected: turning left hid the blaster behind the head and collar from the front, and a
  higher arm lift laid the forearm across the top of the head.
- Coat: 12 robe chains (h12 `m475_chains.json`) re-simulated toward the Standing shape; `hem_floor` 3 mm.

## Results (installed 2026-11-11)

| | Before | After |
|---|---|---|
| Motion ratio | 0.30 | **0.80** |
| p90 reach / moving share / peak speed | 0.116 / 0.320 / 1.33 | 0.236 / 0.952 / 4.12 |
| Deformation beyond Standing (worst) | arm 6.5, spine 6.2 | arm 6.3, spine 6.1, cloth 2.1 |
| Wrist swing / twist | | L 22°/21°, R 28°/19° |
| Hand or forearm in body | L forearm in its sleeve | R 0; L forearm 6.0 cm in its sleeve (Standing 5.6) |
| Floor | -0.1 cm | -1.8 .. +0.3 cm (floor audit ok) |

Bindings unchanged: the shot stays at `impact` 0.62 (`release: muzzle`). Checks (`review/finish.txt`): winding 0,
glb_diff only the Attack channels, floor audit 0 problems, every-binding regression PASS, viewer no console errors.
Shots: `review/attack_viewer_sheet.png`. Rollback: `work/before_attacks/`. Credits: 0.
