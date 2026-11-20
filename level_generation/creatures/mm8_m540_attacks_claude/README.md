# MM8 Ogre Mage (m540): attack and a real Cast from MM9 donors (attacks stream, 2026-11-11)

Parts 3 and 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md): the attack and the cast were one
clip (humanoid set ArmedCastRAttack1 with an authored waist charge, motion ratio 0.28, 1.53 s, impact 1.03). Both are
replaced in place, with tools of the [Warlock pilot](../mm7_m426_attacks_claude/README.md) (`job_attack.json`, then
`job_cast.json` on its result; no Blender):

| Clip | Donor | Role | Ratio before -> after |
|---|---|---|---|
| `Attack` | **MM9 NOSFERATU `AttackMelee`** | melee: the right (wand) arm rises overhead and bashes down at the target, the left arm follows | 0.28 -> **0.76** |
| `Cast` | **MM9 LICH `AttackRanged`**, mirrored | spell and ranged attack: the wand rises high and the spell is flung forward | 0.28 -> **0.77** |

`attack_ranged` now plays `Cast` (a spell), `attack_melee` plays `Attack`. Native `m541a` (9 frames x 125 ms,
contact frame 6 = 0.75 s; attack and attack2 identical): a crouched charge of the wand at the belly, then the wand
rises and the orb flares. Strip: `review/native_attack.png`.

## Route and decisions

- Tried first and rejected: MM9 GIANT `AttackMelee` (two-handed ground smash: the back stretched 20 % beyond
  Standing, and with less trunk the short arms contorted instead) and MM9 LICHKING `AttackMelee` (the overhead
  two-handed raise crowded the big head; legs still).
- Facing by model axis (+Z): the Nosferatu idles with its hips turned 30°; a facing from the hips aimed the first
  install's bash 27° to the side. Rebuilt and reinstalled the same day.
- Attack: trunk yaw soft-limited at 65° (the donor spins 98° and tore the back; spine now 8.7 % beyond Standing,
  above the playbook's ~45° because the bash needs the turn to reach 0.75); right upper arm 36° forward and 44° out
  over 0.6–1.13 s (the fist went 6 cm into the wide right thigh on the return swing); wrist twist soft-limited 75°
  (the donor's left palm rolls 135° in its second claw); timing 1.15 s, donor claw 0.333 s mapped to 0.63 s.
- Cast: timing 1.35 s, donor release 0.447 s mapped to 0.65 s.
- Cape: its lower two bones (`Cape1`, `Cape2`, chain `work/cape_chain.json`) simulated with the h11 numpy sim toward
  the Standing shape, `Cape0` rigid on the spine (simulating all three sheared the upper back). Loincloth rigid.
- Releases measured from `Socket_WandOrb` (95 % of its travel): Attack 0.65 s, Cast 0.65 s (native 0.75 s).

## Results (installed 2026-11-11)

| | Attack | Cast |
|---|---|---|
| p90 reach / moving share / peak speed | 0.300 / 0.783 / 3.36 (was 0.122 / 0.265 / 1.10) | 0.259 / 0.864 / 3.64 |
| Deformation beyond Standing (worst) | spine 8.7, head 8.5 | arm 7.0, head 7.5 |
| Wrist swing / twist (L, R) | 57°/71°, 57°/39° | –, 45°/29° |
| Hand or forearm in body | 0 | 0 |
| Floor | -0.15 cm (= Standing) | -0.16 cm |

Bindings (Ogre Mage A/B/C): `clips.attack_ranged` Attack -> Cast; `events.attack_melee.impact` 1.029 -> 0.65;
`attack_ranged` and `cast` impact 1.029/1.043 -> 0.65 (glow and release sockets unchanged). Checks
(`review/finish.txt`): winding 0, glb_diff only Attack and Cast channels, floor audit 0 problems, every-binding
regression PASS, viewer no console errors. Shots: `review/attack_cast_viewer_sheet.png`.
Rollback: `work/before_attacks/`. Credits: 0.

## Regression test updated (regress-fix, 2026-11-11 evening)

`mm8_ogre_mage_actor_models_keep_tiers_roles_and_wand_cast` failed "clip missing or retimed: Attack": it pinned
Attack and Cast to the old shared 46-frame clip (1.533 s). Both clips exist and are bound as intended (Attack 1.15 s,
Cast 1.35 s, after texpass-2 as well), so only the expected lengths were stale; the test now expects 1.15 / 1.35 s.
Its wand, tiers, roles and wand-orb launch checks pass unchanged. No asset change.
