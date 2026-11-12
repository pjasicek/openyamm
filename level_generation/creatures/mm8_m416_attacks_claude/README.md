# MM8 Pirate Crossbowman (Female) (m416): attack with an authored recoil (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). The `Attack` (authored raise / aim /
fire / rearm, 1.7 s, motion ratio 0.26, shot at 1.0 s) is replaced in place by the same action with its wind-up
compressed and an **authored whole-body recoil**, built with the attacks tools
(`../audit_mm678_20261111/fixes/attack_tools/donor_attack.py`, job `job_attack.json`, her own clip as donor). Bound
to all six descriptors (Pirate Crossbowman (Female) A–C and the Wimpy A–C tiers).

## Why no LoMM donor

The suggested LoMM player `Wattack_Crossbow1` is a 0.25 s twitch: the hands move 5 % of the body height and the
pelvis not at all (`PLAYER/BASE.abc`, read directly with the new ABC donor support; copied to `work/donor/`);
`Reload_crossbow` is a 2.5 s crank. MM9 has no crossbow. The playbook's other route was used: keep her accepted grip
(both hands on the stock; fingers, crossbow, strings, bolt and quiver pass through unchanged) and author the blow on top.

## Intent

Native `m417a`–`m419a` (8 frames x 125 ms, contact frame 4 = 0.5 s; strip `review/native_attack_shooters.png`,
bottom rows): the crossbow comes up to the shoulder, fires, and kicks up steeply as she rocks back.

## Settings

- Wind-up compressed: the donor's shot at 1.0 s now at 0.5 s (native 0.5 s); the rearm plays over 0.5–1.2 s.
- Recoil from the chest, so both hands and the crossbow move rigidly (rotating each arm would pull the hands about
  12 cm apart): B_Spine1 14° + B_Spine2 20° back (carrying the arms), head 8° forward; hips 16 cm back and 8 cm down
  over planted feet (IK miss 0) and turned 25°; eased in over 0.06 s from the shot, out by 1.0–1.1 s.
- Wrist limiter off: her accepted grip angles stay (left twist 128° and right swing 91° are the accepted clip's own,
  138° and 91° before; not made worse).

## Results (installed 2026-11-11)

| | Before | After |
|---|---|---|
| Motion ratio | 0.26 | **0.76** |
| p90 reach / moving share / peak speed | 0.096 / 0.355 / 0.60 | 0.210 / 0.924 / 4.03 |
| Deformation beyond Standing (worst) | | arm 6.0, leg 2.6, spine 3.2 |
| Hand or forearm in body | R forearm 4.6 cm (accepted) | 0 |
| Floor | 0.0 cm | 0.0 cm (all six tiers ok) |

Bindings (six descriptors): `events.attack_melee.impact` 1.0 -> 0.5, `attack_ranged` `{impact: 0.5, release:
bolt_tip}`. Checks (`review/finish.txt`): winding 0, glb_diff only the Attack channels, floor audit 0 problems (both
tier globs), every-binding regression PASS, viewer no console errors. Shots: `review/attack_viewer_sheet.png`.
Rollback: `work/before_attacks/`. Credits: 0.

## Bolt visibility restored (regress-fix, 2026-11-11 evening)

The full actors suite failed `mm8_female_crossbow_pirate_actor_models_keep_tiers_equipment_and_release`: the
re-timed `Attack` above never hid the bolt. `donor_attack.py` wrote every passthrough node's scale from Standing frame
0, so the donor clip's zero-scale keys on `Bolt` (hidden 1.0–1.56 s in the old clip) and the strings' small stretch
were dropped; the bolt stayed on the crossbow through the shot while the projectile left from `bolt_tip`. A real bug,
not a stale test.

- Tool fix (`../audit_mm678_20261111/fixes/attack_tools/donor_attack.py`): passthrough nodes are now written with the
  donor clip's own locals (translation, rotation and scale). Every other channel comes out identical (rotation sign
  flips only on `B_L_Finger0`, same rotation; scales differ by <= 2e-7). No other attacks-stream install lost a scale
  key (scanned every `*_attack(s)_claude` before/after pair for Attack and Cast).
- Re-ran `job_attack.json` unchanged (same report): `Bolt` hidden 0.5 s (the shot, with `attack_ranged.impact` 0.5)
  to 1.067 s (reloaded), `StringL`/`StringR` stretch back. Winding 0; installed with `tools/install_model.py --world
  mm8`; viewer check 0 console errors. Bindings unchanged.
- Test: its sample times (0.7 / 1.1 / 1.65 s on the old 1.7 s clip) moved to 0.3 / 0.7 / 1.15 s on the 1.2 s clip
  (visible before the shot, hidden after the release, back after the reload).
- Rollback of this step: `work/before_regressfix/mm8_m416.glb` (the attacks-1 install).
