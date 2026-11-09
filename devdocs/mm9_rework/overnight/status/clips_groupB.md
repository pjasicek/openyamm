# Dropped MM9 clips, group B (run2-clips-groupB, 2026-10-31): DONE

Bodies: zombie, troglodyte, gezzampt, highwayman, nobleman (known drops); nosferatu, trellborg, ghost, guard (verify).
Leases claimed for the six changed bodies and released at the end. Nosferatu, trellborg, ghost: read only, no lease.
Credits: 0 (no Meshy, no Codex).

## Counts (ABC read with `convert_abc_model.read_abc`, linked child ABCs followed; bind poses excluded; installed without Dead)
| Body | ABC | Source | Installed before | Installed after | Added (role -> clip) |
|---|---|---|---|---|---|
| zombie | ZOMBIE | 17 | 15 (Running = walk x1.5) | 18 | death2 -> Death2 (die2), wakeup2 -> Wakeup2, coffin_idle -> Coffin2 |
| troglodyte | TROGLODYTE | 17 | 15 | 17 | backpedal -> Backpedal, backpedal_run -> BackpedalRun |
| gezzampt | GEZZAMPT | 16 | 14 | 16 | backpedal -> Backpedal, backpedal_run -> BackpedalRun |
| highwayman | HIGHWAYMAN 9 + FIGHTERBASE 12 | 21 | 19 (all 21 used; cower phases only stitched in Cower) | 22 | cower_start -> CowerStart, cower_loop -> CowerLoop, cower_end -> CowerEnd |
| nobleman | NOBLEMAN | 15 | 13 (same) | 16 | cower_start, cower_loop, cower_end |
| guard | GUARD | 19 | 19 (cower hold only inside Cower) | 20 | cower_loop -> CowerLoop |
| nosferatu | NOSFERATU | 16 | 16 | 16 | none missing |
| trellborg | TRELLBORG | 17 | 17 | 17 | none missing |
| ghost | GHOST | 11 | 11 + our Death | 12 | none missing (MM9 has no ghost death) |
Left out: none.

## Route (per project `scripts/extra_clips.sh`, reproducible: troglodyte rerun gave the same hash)
Project clip route with the soft joint-offset line (now in each of the six `clips_mm9.py`), the project's per-clip post steps,
graft into a copy of the installed export, `floor_fix.py` on the new clips only (ops as the accepted clips of the same kind),
then graft only the new clips onto the accepted export. Byte check: old buffer prefix, old JSON, accessors and animations
unchanged (all six OK). Rest poses matched (graft_clips' 1e-4 check passed everywhere, no mirror or rerest needed).
- zombie: `arm_bump.py` Coffin2/Wakeup2 L and R (thumbs 4-6 cm in the thighs while lying), ground-death Death2 on a temporary Dead.
- troglodyte, gezzampt: half keys; floor --ground-loop Backpedal / --raise BackpedalRun, smoothing 0.06 / 0.05 s.
- highwayman: finger keys, arm_out of the accepted Cower split over the phases, half keys, skirt keys (CowerLoop a loop, skirt
  kept up at the crouched ends; `skirt_keys.py` edited for the three names), raise + smooth like Cower.
- nobleman: arm_const, half keys, skirt keys (same edit), raise + smooth like Cower.
- guard: finger, helper, skirt keys (CowerLoop added to LOOPS), hand_rest (Cower's line), dead_hold, helper keys; then
  `match_loop.py` (seats the loop on the accepted CowerStart end / CowerEnd start, joins 10.6 deg -> 0.3 deg) and a second
  hand_rest push faded in and out over the loop by `blend_window.py`.
Soft line side effect: joints with a constant MM9 offset sit up to 0.4 cm per axis (0.57 cm) off the accepted clips' pose
(troglodyte spine); the transition crossfade covers it.

## Measured, new clips (installed GLB, 48 fps)
| Clip | Floor lowest min..max cm | Hands in body (worst, frames > 1 cm) | Jitter gate | Bones |
|---|---|---|---|---|
| zombie Death2 | 0.0..5.5, corpse 0 | L 0.1, R 0.0, 0 f | arm joints 0 excess; shoulder skin 27.4 mm/f2 FAIL (floor settle; accepted Death 25.6) | 0 stretching |
| zombie Wakeup2 | -0.1..0.2 | L 0.0, R 0.1 (were 4.8 / 5.8), 0 f; R forearm 2.7 cm @ frame 3 | upper arm 0.08 deg/f; shoulder skin 13.1 FAIL (per-key floor raise; accepted Wakeup 11.1) | 0 |
| zombie Coffin2 | 0.0 | 0.0 (were 3.8 / 4.0, 97 f) | 0 | 0 |
| troglodyte Backpedal | -1.7..0.7 (Walking -1.8..0.8) | 0 | pass, shoulder skin 1.2 | 0 |
| troglodyte BackpedalRun | -1.7..1.5 | 0 | pass | 0 |
| gezzampt Backpedal | -2.0..1.6 | 0 | pass (13.4 mm/f2 before smoothing) | 0 |
| gezzampt BackpedalRun | -1.4..3.8 (airborne phase) | 0 | pass | 0 |
| highwayman CowerStart / Loop / End | -0.4..0.2 / 0 / -0.5..0 | 0 / 0 / 0 | pass | 0 |
| nobleman CowerStart / Loop / End | -0.9..0.6 / 0 / -0.8..0.4 | 0 / 0 / 0 (finger stretch max 2.16, as accepted Cower) | pass | 0 |
| guard CowerLoop | -0.3..0 | R 1.0 cm, 0 f (3.2 cm, 28 f before the faded push) | pass (forearm +0.68 deg/f) | 0 new (2 old: Thigh in Hit/Sleep) |
Strips read (numpy raster, untextured, floor drawn): `level_generation/creatures/mm9_<body>_claude/review/gates_extra/strip_new.png`;
zombie close-ups `coffin_lhand.png`, `coffin_hands_top.png`. Gate files in the same folder.
Finding: MM9's troglodyte backpedal and backpedalRun carry the forward walk's keys (BackpedalRun = walk at 0.8 s), so they step forward.

## Bindings and regression
`actors.yml` script_clips under the flock, every descriptor of each model (zombie 3, troglodyte 3, gezzampt 3, highwayman 3,
nobleman 3, guard 5 incl. Town Guards 107/109); each project's `bind_actors.py` carries the same lines.
Installed with `tools/install_model.py --world mm9` after `check_winding.py` (0 inverted on all six). `review_root.py` run.
Regression `mm9_actor_models_build_every_binding` (`--world mm9`): **PASS, 147 descriptors on 58 models, 0 failed**
(mm6-8 case: 647 on 185, 0 failed). The rest of the actors suite was stopped after these cases (my PID).

## Not checked
No viewer (textured) shots, no playback, no in-game run of any new clip; nothing drives them yet. Collapse and cloth/skirt
gates not run on the new clips. Guard halberd and highwayman/nobleman weapons not gated separately in the new clips
(poses match the accepted Cower hold). LOD1-3 not looked at (LOD0 only).

## Read-only census: every other installed MM9 model
"Dropped" uses the project's roles JSON where one exists (source clips not used by any installed role); bodies without a
roles JSON (animals and early monsters, mapped inside their scripts) show only source minus installed, a lower bound
because installed counts include derived clips (Running = walk x1.5). Annud and Forad link PeasantMale.abc (43 shared
peasant clips: conversations, work loops, Njam scenes), so most of their source list is the town NPC library.
Clansoldier's static_die1/2 are held death poses, counted with the bind poses here.

| Model | ABC (+ linked) | Source clips | Installed (no Dead) | Dropped |
|---|---|---|---|---|
| annud | PEASANTM6 | 61 | 8 | 53: MP_6a, run2, lean, leanfidget, bardrink, barfig, barstand, bless, pray, bow, conv, conv1, conv3, conv4, conv5, fidget1, fidget2, fidget3, fidget5, fidget8, hattack1, wince2, backpedal, backpedalrun, cowerstart, cower, cowerend, ----------, Sc07_shot1, play_death, play_getup, Njam_kick, Njam_Hattack1, Njam_Hattack2, Njam_Spell1, Njam_Spell2, hammerwait, hammer, hammerfig, countwait, count, countfidget1, countfidget2, sweepwait, sweep, sweepfidget, shovelwait, shovel, shovelfidget, innkeeper1, innkeeper2, innkeeperfidget, innkeeperfidget2 |
| banshee (other agent, in progress) | BANSHEE | 16 | 13 | 1: Fly |
| basilisk | BASILISK | 14 | 8 | at least 6 (no role map to check; source: Stand, Aware, Fidget1, Fidget2, Walk, Run, Search, Taunt, RAttack1, HAttack1, Wince1, Wince2, Die1, Die2) |
| bigfoot (other agent, in progress) | BIGFOOT | 18 | 13 | 5: walkfidget, Backpedal, BackpedalRun, JumpingDown, LyingDown |
| cat | CAT | 10 | 7 | at least 3 (no role map to check; source: stand1, fidget1, fidget2, down, up, standdown, fidgetdown2, fidgetdown1, walk, run) |
| clansoldier (other agent, in progress) | CLANSOLDIER | 20 | 20 | 0 |
| cow | COW | 14 | 6 | at least 8 (no role map to check; source: Stand, Fidget1, Fidget2, Fidget3, Walk, Run, Tipover1, Standup1, Tipover2, Standup2, Wince1, Wince2, Die1, Die2) |
| crow | CROW | 13 | 7 | at least 6 (no role map to check; source: stand, fidget1, fly, fidgetAir1, HattackAir1, winceair1, winceair2, dieair1, fall1, falldown1, dieair2, fall2, falldown2) |
| dagrell | DAGRELL | 17 | 8 | at least 9 (no role map to check; source: CrouchedAware, Stand, Fidget1, returntocrouch, crouch, crouchfidget, Walk, Walk1, Run, Taunt, Search, HAttack2, HAttack1, Jump, Wince1, Wince2, RAttack1) |
| dfly | DRAGONFLY | 20 | 8 | at least 12 (no role map to check; source: StandAir, AwareAir, FidgetAir1, FidgetAir2, Flap, Glide, oldFlap, SearchAir, TauntAir, HAttackair1, HAttackair2, Rattack1, WinceAir1, WinceAir2, DieAir1, fall1, FallDOwn1, DieAir2, fall2, FallDown2) |
| dog | DOG | 9 | 7 | at least 2 (no role map to check; source: stand, fidget1, Bark, walk, walksniff, walkbark, run, run(away), sitting) |
| dookmilitia (other agent, in progress) | DOOKMILITIA | 23 | 20 | 1: tauntSAVE |
| dragonking | DRAGON | 14 | 11 | at least 3 (no role map to check; source: fly, land, stand, taunt, fidget1, fidget2, spitacross, rAttack1, Rattack2, Rattack3, WingAttack, wince1, wince2, die1) |
| dwarf (other agent, in progress) | DWARF | 16 | 16 | 0 |
| evilsorcerer (other agent, in progress) | EVILSORCERER | 17 | 17 | 0 |
| eye | EVILEYETERROR | 17 | 8 | at least 9 (no role map to check; source: standair, Flap, tauntair, fidgetair1, searchair, HattackAir1, HattackAir2, Rattack1, winceAir1, winceAir2, Fly, DieAir1, fall1, FallDown1, DieAir2, fall2, FallDown2) |
| fish | FISH | 1 | 6 | at least 0 (no role map to check; source: swim) |
| forad | FORADDARRE | 49 | 9 | 40: ForadDarre, Sc2_Forad6, Sc2_forad26, Agree, Applause, sit, run2, lean, leanfidget, bardrink, barfig, barstand, bless, pray, conv, conv2, conv3, conv4, conv5, fidget2, fidget3, fidget4, fidget5, fidget8, hattack2, wince2, backpedal, backpedalrun, cowerstart, cower, cowerend, ----------, Sc07_shot1, play_death, play_getup, Njam_kick, Njam_Hattack1, Njam_Hattack2, Njam_Spell1, Njam_Spell2 |
| ghoul (other agent, in progress) | GHOUL | 15 | 15 | 0 |
| goat | GOAT | 11 | 7 | at least 4 (no role map to check; source: Stand, Fidget1, Fidget2, Walk, Run, HAttack1, RunAttack, Wince1, Wince2, Die1, Die2) |
| goose | GOOSE | 8 | 7 | at least 1 (no role map to check; source: stand, fidget1, fidget2, Hattack1, walk, run, wince1, die1) |
| greaterdemon | STAGE2DEMON | 18 | 8 | at least 10 (no role map to check; source: spawn, stand, taunt, fidget1, fidget2, walk, run, block, Hattack1, Hattack2, Rattack1, dodgeleft, dodgeright, wince1, wince2, die1, Backpedal, Backpedalrun) |
| hen | HEN | 12 | 7 | at least 5 (no role map to check; source: Stand, Sit, Fidget1, Fidget2, Fidget3, Walk, Run, HAttack1, Wince1, Wince2, Die1, Die2) |
| honkf (other agent, in progress) | HONKFEMALE | 20 | 9 | at least 11 (no role map to check; source: prop-stand, prop-fidget1, prop-fidget2, stand, fidget1, fidget2, cowerstart, cower, cowerend, walk, run, Hattack1, Hattack2, Rattack1, wince1, wince2, die1, die2, Backpedal, Backpedalrun) |
| honkm (other agent, in progress) | HONKMALE | 20 | 9 | at least 11 (no role map to check; source: prop-stand, prop-fidget1, prop-fidget2, stand, fidget1, fidget2, cowerstart, cower, cowerend, walk, run, Hattack1, Hattack2, Rattack1, wince1, wince2, die1, die2, Backpedal, Backpedalrun) |
| icky | FLYINGICKY | 18 | 9 | at least 9 (no role map to check; source: StandAir, hang, hangfidget, launch, taunt, Flap, fidgetair1, Hattackair1, startattackair2, attackair2, winceair1, winceair2, DieAir1, fall1, FallDown1, dieair2, fall2, FallDown2) |
| imp | IMP | 16 | 9 | 7: fidget2, aware, Hattack1, wince2, die2, Backpedal, BackpedalRun |
| jelly | JELLYSPORE | 8 | 8 | at least 0 (no role map to check; source: standwater, awarewater, fidgetwater, swim, hattackwater1, Hattackwater2, wincewater1, wincewater2) |
| lich | LICH | 18 | 15 | 3: die2, Backpedal, BackpedalRun |
| lizardorc (other agent, in progress) | LIZARDORC | 15 | 15 | 0 |
| lobber | LOBBER | 11 | 6 | at least 5 (no role map to check; source: StandAir, FidgetAir1, FidgetAir2, AwareAir, LaunchPod, Rattack1, winceAir1, winceAir2, DieAir1, fall1, falldown1) |
| lobberpod | LOBBERPOD | 14 | 8 | at least 6 (no role map to check; source: projectile, land, stand, taunt, fidget, walk, run, Hattack1, Rattack1, wince1, wince2, die1, Backpedal, BackpedalRun) |
| magreeb | MAGREEB | 15 | 8 | at least 7 (no role map to check; source: stand, walk, run, fidget1, fidget2, Hattack1, Hattack2, wince1, wince2, die1, die2, Backpedal, Backpedalrun, Taunt, Jumping) |
| monk (other agent, in progress) | MONK | 34 | 34 | 0 |
| mouse | MOUSE | 3 | 6 | at least 0 (no role map to check; source: stand, run, die) |
| mummy (other agent, in progress) | MUMMY | 21 | 22 | 0 |
| nagate | NAGATE | 13 | 8 | at least 5 (no role map to check; source: stand, aware, taunt, fidget1, fidget2, walk, run, Hattack1, Hattack2, Rattack1, wince1, wince2, die1) |
| pig | PIG | 13 | 6 | at least 7 (no role map to check; source: Stand, Fidget1, Fidget2, Standdown, Roll, Rest, Standup, Walk, Run, Wince1, Wince2, Die1, Die2) |
| ram | RAM | 11 | 7 | at least 4 (no role map to check; source: stand, fidget1, fidget2, walk, run, Hattack1, Hattack2, wince1, wince2, die1, die2) |
| rooster | ROOSTER | 10 | 7 | at least 3 (no role map to check; source: Stand, Fidget1, Fidget2, Walk, Run, HAttack1, Wince1, Wince2, Die1, Die2) |
| seamon | SEAMONSTER | 11 | 7 | at least 4 (no role map to check; source: standwater, swim, fidgetwater1, fidgetwater2, Hattackwater1, Hattackwater2, wincewater1, wincewater2, diewater1, diewater2, Jump) |
| sheep | SHEEP | 11 | 7 | at least 4 (no role map to check; source: stand, fidget1, fidget2, walk, run, Hattack1, Hattack2, wince1, wince2, die1, die2) |
| skeleton (other agent, in progress) | SKELETON | 16 | 16 | 0 |
| skelwar | SKELETONWARRIOR | 20 | 12 | 8: search, fidget2, Hattack1OLD, RAttack1OLD, wince2, die2, BackPedal, BackPedalRun |
| terror | TERROR | 14 | 8 | at least 6 (no role map to check; source: stand, walk, run, fidget1, fidget2, Hattack1, Hattack2, wince1, wince2, die1, die2, Taunt, Backpedal, BackpedalRun) |
| thrall (other agent, in progress) | THRALL | 14 | 14 | 0 |
| wingedmutant | WINGEDMUTANT | 15 | 8 | at least 7 (no role map to check; source: StandAir, FidgetAir1, TauntAir, Flap, HAttackAir1, HattackAir2, RAttack1, WinceAir1, WinceAir2, dieair1, fall1, falldown1, dieair2, fall2, falldown2) |
| wolf | WOLF | 16 | 8 | at least 8 (no role map to check; source: stand, walk, run, aware, taunt, fidget1, fidget2, Hattack1, Hattack2, wince1, wince2, die1, die2, backpedal, backpedalrun, RAttack1) |
| yrsa | YRSA | 5 | 6 | 0 |

