# MM6 PeasantF3 (mfp): attack from an MM9 donor (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). The `Attack` (Mixamo "Stabbing (1)", a
planted right-hand stab, motion ratio 0.32, 1.3 s; also played for ranged and cast) is replaced in place by a clip
retargeted from **MM9 NOSFERATU `AttackMelee`**, its first claw only. Tools as the
[Warlock pilot](../mm7_m426_attacks_claude/README.md) (`job_attack.json`; no Blender).

## Intent

Native `mfpatta` (6 frames x 125 ms, contact frame 3 = 0.375 s): the dagger is raised overhead, then driven down and
forward with a strong forward bend and the braid flying, and she recovers (`review/native_attack.png`). The MM9 female
peasants have no attack clip (theirs is bound to Fidget) and the half-orc's is a two-handed shove; the Nosferatu's
first claw (right arm overhead, then down-forward) is the dagger stab with the knife hand.

## Settings

- Donor cut at 0.62 s (before its second, left-hand claw); claw 0.333 s mapped to 0.40 s; 1.0 s with a 0.4 s ease
  back to Standing.
- Knife arm (upper arm and forearm) takes the donor's **world bone directions** over 0.02–0.8 s (new
  `arm_direction`): the Nosferatu idles with its claws forward and her arms hang, so copied rotation changes swung her
  raised arm out sideways instead of overhead. Roll stays from the change.
- Left arm at 0.4 of the donor; forward bend 26° (B_Spine1) + 14° (B_Spine2) at the stab (native `ac`); pelvis
  travel x2 and drop x2.5 over planted feet (IK miss 0.7 cm), so the hips drive the stab; trunk yaw soft-limited 45°.
- Knife arm 12° forward and 10° out on the return (the hand touched the skirt front for one frame).
- Skirt: the five-ring cage fitted per sample with the anim stream's `ring_skirt.py` (imported unchanged from
  `../mm6_mfp_animfix_claude/scripts/`), eased in and out over 0.15/0.25 s so the clip starts and ends on Standing's
  cage. Braid: `Braid_0..2` simulated as a chain from the head (h11 numpy sim, Standing rest).
- Release measured: `Socket_Knife_Tip` at 95 % of its 1.2 m back-to-front travel at **0.35 s** (native 0.375 s).

## Results (installed 2026-11-11)

| | Before | After |
|---|---|---|
| Motion ratio | 0.32 | **0.78** |
| p90 reach / moving share / peak speed | 0.140 / 0.305 / 1.32 | 0.231 / 0.954 / 3.70 |
| Deformation beyond Standing (worst) | arm 11.2, spine 8.0 | arm 5.0, spine 3.7, cloth 0.0 |
| Wrist swing / twist | | R 49°/60°, L 9°/6° |
| Hand in body | 0 | 0 |
| Floor | +0.2 cm | 0.0 .. +1.3 cm (first/last = Standing) |

Bindings (PeasantF3 A/B/C): `events.attack_melee`, `attack_ranged`, `cast` impact 0.929 -> 0.35. Checks
(`review/finish.txt`): winding 0, glb_diff only the Attack channels, floor audit 0 problems, every-binding regression
PASS, viewer no console errors. Shots: `review/attack_viewer_sheet.png` (the vertical band on the skirt is the wrap
slit in the texture; the flat render shows the cloth intact). Rollback: `work/before_attacks/`. Credits: 0.

## Knife restored (2026-11-12, coordinator)

The user saw no knife in the re-animated Attack. The `donor_attack.py` pass-through bug (fixed 2026-11-11 for m416)
had written the `Knife` node's Standing transform into Attack: scale 0.001, the parked knife, so the `mm6_mfp_knife.glb`
attachment was hidden. The donor also held the right hand open. `scripts/restore_knife.py` puts back the original
Attack's constant Knife transform (the grip, a child of `B_R_Hand`) and the 15 right-finger rotations (the fist),
leaving every other channel of the new Attack. Checked in the compare viewer (knife in the fist through the stab),
winding 0, every_binding and `mm6_peasant_f3_actor_model_tiers_share_the_native_height` pass. A scan of every
re-animated clip found no other prop whose visibility changed. Revert:
`python3 tools/install_model.py level_generation/creatures/mm6_mfp_attacks_claude/work/before_knife/mm6_mfp.glb --world mm6`.
