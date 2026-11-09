# Dropped MM9 clips, group C (run2-clips-groupC, 2026-10-31): DONE

Bodies, in order: dfly, greaterdemon, dagrell, eye, icky, cow, wolf, magreeb, pig, wingedmutant, basilisk, crow, lobber
(+ lobberpod), terror, hen, nagate, goat, ram, seamon, sheep, cat, dragonking, rooster, dog, goose. All 26 models installed with
their MM9 clips; nothing else about the bodies changed (meshes, LODs, variants, accepted clips byte for byte: graft_byte_check OK
on every export). Not touched: imp, lich, skeletonwarrior, yrsa, annud, forad and the other groups' bodies.
Credits: 0 (no Meshy, no Codex).

## Route (all 26 are Blender-route bodies: their clips are built in Blender by each project's clips_mm9.py)
- `scripts/extra_clips.json` per project -> `claude_shared/make_extra_clips.py` writes `scripts/extra_clips_blend.py` (shim over
  `claude_shared/mm9_extra_clips_blend.py`) and `scripts/extra_clips.sh` (dfly, greaterdemon, dagrell, eye, icky, cow, wolf and ram
  have hand-written `extra_clips.sh`; the lobber project has a second set `extra_clips_pod.*` for the pod).
  Rebuild a body: claim its lease, `TOK=<token> scripts/extra_clips.sh` from the project, then install + bind as below.
- The shim opens the source blend the project's build_export.py opens, builds the missing MM9 clips with the project's OWN
  clips_mm9.py (build_role_clips with a role table where the copy takes one; else its read_keys/close_seam/stitch/write_action),
  runs the project's build_export.py post steps where it has them (pig ear helpers; cat REST_OFFSET, hind_ik, fore_stance, knee
  helpers, 3.12 cm rest shift; dog REST_OFFSET, neck_spread; seamon's sprawl death on Death2), and exports the armature.
- `extra_clips.sh`: graft into a copy of the accepted export (`work/pre_clips_export.glb`), the floor passes build_runtime.sh gives
  accepted clips of the same kind, `Ctl_*` controls (accepted clips rebuilt the same way) compared with the installed ones by
  `claude_shared/compare_clips.py`, then `graft_clips.py` of only the new clips onto the accepted export and
  `claude_shared/graft_byte_check.py`. Controls: 0.0000 deg / 0.0000 cm on every body, except cow and goat floors (Findings).
- Duplicates: `claude_shared/extra_clip_gates.py --dupes-only`. An MM9 clip that carries another clip's keys is bound to that
  clip instead of grafted twice (eye Flap = Fly, dagrell Taunt = RAttack1, wolf RAttack1 = aware and backpedalrun = backpedal,
  magreeb Jumping = walk, nagate aware = taunt and Hattack2 = Rattack1).
- Bindings: `claude_shared/bind_script_clips.py <model> role=Clip ... [--replace]` (flock, re-read, temp + rename), every
  descriptor of the model.
- Gates and strips: `claude_shared/extra_clip_gates.py` -> `review/gates_extra/` (`extra_gates.json`, `strip_new_*.png`;
  lobberpod `review/gates_extra_pod/`). Census: `claude_shared/mm9_clip_census.py <ABC> <glb>`.
- Soft joint-offset line: none of these 26 clips_mm9.py copies has the 4 mm cut (the cat's 0.004 values are key data).

## Per body (source = MM9 clips without bind poses; installed counts include our Dead and derived clips)
| Body | Source | Installed before -> after | Added (role -> clip <- MM9 source) |
|---|---|---|---|
| dfly | 20 | 9 -> 18 | aware<-AwareAir, fidget2<-FidgetAir2, glide, flap_old<-oldFlap, search<-SearchAir, taunt<-TauntAir, attack_melee2<-HAttackair2, hit2<-WinceAir2, death2<-DieAir2+fall2+FallDown2 |
| greaterdemon | 18 | 9 -> 19 | spawn, taunt, fidget2, block, attack_melee2<-Hattack2, dodge_left, dodge_right, hit2<-wince2, backpedal, backpedal_run |
| dagrell | 17 | 9 -> 18 | crouched_aware, crouch, crouch_fidget, return_to_crouch, walk2<-Walk1, search, attack_melee2<-HAttack2, jump, hit2<-Wince2; taunt: AttackRanged |
| eye | 17 | 9 -> 14 | taunt, search, attack_melee2<-HattackAir2, hit2<-winceAir2, death2<-DieAir2+fall2+FallDown2; flap: Walking |
| icky | 18 | 10 -> 16 | hang, hang_fidget, launch, attack_ranged2<-attackair2, hit2<-winceair2, death2<-dieair2+fall2+FallDown2 |
| cow | 14 | 7 -> 15 | fidget2, fidget3, tipover<-Tipover1, standup<-Standup1, tipover2, standup2, hit2<-Wince2, death2<-Die2 |
| wolf | 16 | 9 -> 15 | aware, taunt, fidget2, hit2<-wince2, death2<-die2, backpedal; attack_ranged2: Aware, backpedal_run: Backpedal |
| magreeb | 15 | 9 -> 15 | fidget2, hit2<-wince2, death2<-die2, backpedal, backpedal_run, taunt; jump: Walking |
| pig | 13 | 7 -> 14 | fidget2<-Fidget1, lie_down<-Standdown, roll, rest, stand_up<-Standup, hit2<-Wince2, death2<-Die2 |
| wingedmutant | 15 | 9 -> 13 | taunt<-TauntAir, attack_melee2<-HattackAir2, hit2<-WinceAir2, death2<-dieair2+fall2+falldown2 |
| basilisk | 14 | 9 -> 15 | aware, fidget2, search, taunt, hit2<-Wince2, death2<-Die2 |
| crow | 13 | 8 -> 12 | perch<-stand, perch_fidget<-fidget1, hit2<-winceair2, death2<-dieair2+fall2+falldown2 |
| lobber | 11 | 7 -> 10 | fidget2<-FidgetAir2, aware<-AwareAir, hit2<-winceAir1. LEFT OUT fall1, falldown1 (below) |
| lobberpod | 14 | 9 -> 15 | projectile, land, taunt, hit2<-wince2, backpedal, backpedal_run<-BackpedalRun |
| terror | 14 | 9 -> 15 | fidget2, hit2<-wince2, death2<-die2, taunt, backpedal, backpedal_run |
| hen | 12 | 8 -> 13 | sit, fidget2, fidget3, hit2<-Wince2, death2<-Die2 |
| nagate | 13 | 9 -> 12 | taunt, fidget2, hit2<-wince2; aware: Taunt, attack_melee2: AttackRanged |
| goat | 11 | 8 -> 12 | fidget2, run_attack<-RunAttack, hit2<-Wince2, death2<-Die2 |
| ram | 0 own (plays SHEEP's) | 8 -> 12 | fidget2, attack_melee2<-Hattack2, hit2<-wince2, death2<-die2 (the sheep's, from ../mm9_sheep_claude/work/extra_raw.glb) |
| seamon | 11 | 8 -> 12 | fidget2<-fidgetwater2, hit2<-wincewater2, death2<-diewater1 (+ the accepted Death's sprawl treatment), jump |
| sheep | 11 | 8 -> 12 | fidget2, attack_melee2<-Hattack2, hit2<-wince2, death2<-die2 |
| cat | 10 | 8 -> 14 | fidget2, lie_down<-down, get_up<-up, lie<-standdown, lie_fidget<-fidgetdown1, lie_fidget2<-fidgetdown2 |
| dragonking | 14 | 12 -> 16 | fidget2, spit_across<-spitacross, breath2<-Rattack2, hit2<-wince2 |
| rooster | 10 | 8 -> 11 | fidget2, hit2<-Wince2, death2<-Die2 |
| dog | 9 | 8 -> 12 | walk_sniff, walk_bark, run_away<-run(away), sit<-sitting |
| goose | 8 | 8 -> 9 | fidget2<-fidget1 (the accepted Fidget plays fidget2) |

Left out, with why:
- lobber `fall1`, `falldown1`: MM9's drop from the ceiling. Our Lobber grows upright from the floor (project README), so the
  fall would rise; its Death is DieAir1 then a wilt, as accepted.
- seamon `diewater2` as a clip of its own: it is the accepted Death's source (its convulsion, then the sprawl the project added
  because the sinking end hangs head-up and stands on its tail on a floor). diewater1 got the same treatment as Death2.
- Fall segments (`fall*`, `FallDown*`) of fliers stay inside the stitched deaths, as accepted.

## Findings
- cow and goat: the installed Fidget and Hit are not what today's build_runtime.sh floor pass gives (raw clips 0.9-1.9 cm up,
  installed on the floor). `floor_fix.py --ground-loop` (+ 0.08 s smooth) reproduces them within 0.04-0.56 cm (cow) and 0.1 cm
  (goat), so the new living clips of both take that; deaths match exactly.
- wolf Death2: the project's tail lift (`--lift-joints`) spun the tail 125-147 deg in one frame while the wolf lies on its back
  (die2 0.9 s); Death2 skips the lift and `--ground-death` keeps the tail on the floor. Jitter 2068 -> 705 mm/f2 (accepted Hit 529).
- seamon diewater1 is a sinking death like diewater2: without the sprawl it ended standing on its tail. Death2 now ends lying.
- cat: MM9's cat idles sitting; down/up/standdown are lying down, getting back up and the lying idle (named so).
- MM9-authored joint offsets that stretch: cow Fidget3 Xneckbase x2.6 (the neck reaches down to graze), wolf die2 Bone09 x1.6 at
  the end, crow stand/fidget1 wing mid joint x2.76 (folded wing). Kept as MM9 has them.
- terror wince2: 61.7 deg in 34 ms on a tentacle in MM9's own keys (accepted wince1 66.6 deg in 67 ms): jitter 2111 mm/f2.
- crow Perch: the folded wings sink into the flanks (958 crossing pairs vs 187 in flight); reads as tucked wings in the strip.
- dog RunAway: MM9 tucks the tail between the hind legs; our bushy tail passes into the rump (134 pairs vs 56), floor -1.7 cm.

## Bindings and regression
Every descriptor of each model (`bind_script_clips.py`, flock). Installed with `tools/install_model.py --world mm9` after
`check_winding.py` (0 inverted on all 26). `review_root.py` run (links current).
Regression `mm9_actor_models_build_every_binding` (`--world mm9`): PASS 147 descriptors on 58 models, 0 failed after eye, after
goat, after goose and (final) after the cat's clip rename (mm6-8 case 647 on 185, 0 failed each time). The rest of the actors
suite was stopped after these cases (my PIDs). All leases released; no Chrome, gate or game process of this run left.

## Measured, new clips (installed GLB, 30 fps, LOD0; `review/gates_extra*/extra_gates.json`)
Floor: lowest visible point (fliers hover by design; deaths end at 0). Jitter: p99 vertex second difference, worst frame, with
the body's accepted clips' worst in brackets (wing and tentacle bodies are high by nature). Bone: worst posed/rest joint offset
ratio over every non-root joint (MM9 animates translations on wings, fins and some necks; accepted clips have the same). Body-in-
body: triangle pairs crossing between parts more than two joints apart, worst frame (accepted worst in brackets; eyes, teeth and
folded wings cross at rest). Strips read (all bodies; sheep only through the ram's identical clips on the same body):
`level_generation/creatures/mm9_<body>_claude/review/gates_extra/strip_new_*.png` (side + 3/4, untextured, floor line).

| Body | Clip | Floor min..max (end) cm | Jitter p99 mm/f2 (accepted max) | Bone worst ratio | Body-in-body pairs (accepted max) |
|---|---|---|---|---|---|
| dfly | Aware | 19.5..52.8 (26.2) | 328.89 (1080.18) | 1.181 XwingA | 12 (58) |
| dfly | Fidget2 | 0.0..30.1 (27.4) | 141.88 (1080.18) | 1.185 XwingA | 10 (58) |
| dfly | Glide | 65.4..73.7 (71.7) | 41.45 (1080.18) | 1.101 Xjawpiv | 11 (58) |
| dfly | FlapOld | 55.2..79.0 (78.2) | 393.43 (1080.18) | 1.313 XwingA | 11 (58) |
| dfly | Search | 3.1..70.7 (26.2) | 148.5 (1080.18) | 1.186 XwingA | 75 (58) |
| dfly | Taunt | 12.3..60.0 (20.3) | 303.36 (1080.18) | 1.32 XwingA03 | 10 (58) |
| dfly | AttackMelee2 | 9.5..78.5 (26.2) | 459.74 (1080.18) | 1.319 XwingA03 | 10 (58) |
| dfly | Hit2 | 23.0..79.1 (26.2) | 163.92 (1080.18) | 1.324 XwingA03 | 68 (58) |
| dfly | Death2 | -0.0..81.9 (-0.0) | 299.77 (1080.18) | 1.197 XwingA | 78 (58) |
| greaterdemon | Spawn | -0.1..177.0 (0.0) | 874.57 (727.78) | 1.86 XwarmApiv | 1012 (809) |
| greaterdemon | Taunt | -0.0..0.8 (0.0) | 283.53 (727.78) | 1.177 XwarmApiv01 | 550 (809) |
| greaterdemon | Fidget2 | -0.0..0.0 (0.0) | 214.33 (727.78) | 1.148 XwarmApiv | 481 (809) |
| greaterdemon | Block | -0.1..0.3 (0.0) | 301.24 (727.78) | 1.209 Xltoe01 | 470 (809) |
| greaterdemon | AttackMelee2 | -0.1..0.5 (0.0) | 465.28 (727.78) | 1.148 XwarmApiv | 477 (809) |
| greaterdemon | DodgeLeft | -0.0..74.6 (0.0) | 752.42 (727.78) | 1.622 XwarmApiv01 | 485 (809) |
| greaterdemon | DodgeRight | -0.0..55.2 (0.0) | 695.32 (727.78) | 1.223 XwarmApiv | 458 (809) |
| greaterdemon | Hit2 | -0.1..0.8 (0.0) | 481.61 (727.78) | 1.447 XwarmApiv01 | 566 (809) |
| greaterdemon | Backpedal | -0.0..0.1 (-0.0) | 92.87 (727.78) | 1.254 XwarmApiv01 | 499 (809) |
| greaterdemon | BackpedalRun | -0.0..2.4 (-0.0) | 166.67 (727.78) | 1.254 XwarmApiv01 | 490 (809) |
| dagrell | CrouchedAware | -0.0..0.0 (0.0) | 227.85 (405.92) | 1.074 XtailA | 72 (72) |
| dagrell | Crouch | 0.0..0.0 (0.0) | 0.61 (405.92) | 1.049 Xfin02 | 0 (72) |
| dagrell | CrouchFidget | -0.0..0.0 (0.0) | 33.01 (405.92) | 1.298 Xfin02 | 0 (72) |
| dagrell | ReturnToCrouch | -0.0..0.0 (0.0) | 41.46 (405.92) | 1.016 Xfmid | 0 (72) |
| dagrell | Walk2 | -0.1..0.0 (0.0) | 92.68 (405.92) | 1.018 Xfmid05 | 31 (72) |
| dagrell | Search | -0.0..0.0 (-0.0) | 33.68 (405.92) | 1.023 Xfin03 | 0 (72) |
| dagrell | AttackMelee2 | -0.0..0.0 (0.0) | 336.74 (405.92) | 1.027 XtailA | 0 (72) |
| dagrell | Jump | -0.0..66.8 (0.0) | 334.8 (405.92) | 1.021 Xfmid | 0 (72) |
| dagrell | Hit2 | -0.0..0.0 (-0.0) | 405.92 (405.92) | 1.021 Xfmid05 | 0 (72) |
| eye | Taunt | 43.0..73.7 (73.7) | 37.85 (778.33) | 1.405 Box70 | 65 (133) |
| eye | Search | 43.0..73.7 (73.7) | 16.75 (778.33) | 1.412 Box70 | 69 (133) |
| eye | AttackMelee2 | 38.8..115.5 (73.7) | 476.96 (778.33) | 1.0 Box06 | 45 (133) |
| eye | Hit2 | 53.7..147.9 (73.7) | 119.99 (778.33) | 1.548 Box70 | 191 (133) |
| eye | Death2 | -0.0..89.7 (0.0) | 678.47 (778.33) | 1.0 Box69 | 107 (133) |
| icky | Hang | 50.7..51.2 (51.2) | 0.63 (265.73) | 1.27 XwpivE | 1159 (3185) |
| icky | HangFidget | 34.2..51.2 (51.2) | 9.64 (265.73) | 1.27 XwpivE | 1162 (3185) |
| icky | Launch | 6.6..61.9 (61.6) | 247.25 (265.73) | 1.27 XwpivE | 364 (3185) |
| icky | AttackRanged2 | 0.0..16.1 (16.1) | 16.61 (265.73) | 1.561 XwpivE01 | 304 (3185) |
| icky | Hit2 | 2.0..62.3 (61.6) | 237.0 (265.73) | 1.143 Xjawpiv01 | 2142 (3185) |
| icky | Death2 | -0.0..61.6 (-0.0) | 205.11 (265.73) | 1.129 Xjawpiv04 | 578 (3185) |
| cow | Fidget2 | -0.0..0.1 (-0.0) | 64.92 (291.57) | 1.022 Xheadpiv | 34 (70) |
| cow | Fidget3 | -0.1..0.9 (-0.0) | 46.25 (291.57) | 2.595 Xneckbase | 45 (70) |
| cow | Tipover | -0.8..12.1 (-0.0) | 227.7 (291.57) | 1.189 Xblegmid | 38 (70) |
| cow | Standup | -1.7..12.3 (0.0) | 107.11 (291.57) | 1.074 Xheadpiv | 67 (70) |
| cow | Tipover2 | -0.3..7.7 (-0.0) | 284.99 (291.57) | 1.097 Xblegpiv | 78 (70) |
| cow | Standup2 | -1.7..10.1 (-0.0) | 89.05 (291.57) | 1.075 Xheadpiv | 165 (70) |
| cow | Hit2 | -0.2..0.7 (-0.0) | 127.67 (291.57) | 1.317 Xfleg01 | 33 (70) |
| cow | Death2 | -0.0..12.1 (-0.0) | 134.2 (291.57) | 1.115 Xblegpiv01 | 48 (70) |
| wolf | Aware | -0.0..0.0 (-0.0) | 165.11 (528.78) | 1.004 Bone32 | 0 (130) |
| wolf | Taunt | -0.0..0.0 (0.0) | 221.72 (528.78) | 1.005 Bone09 | 19 (130) |
| wolf | Fidget2 | -0.0..0.0 (0.0) | 51.7 (528.78) | 1.001 Bone19 | 0 (130) |
| wolf | Hit2 | -0.0..0.0 (0.0) | 334.95 (528.78) | 1.0 Bone30 | 0 (130) |
| wolf | Death2 | -0.0..10.1 (0.0) | 704.77 (528.78) | 1.61 Bone09 | 356 (130) |
| wolf | Backpedal | -0.0..0.0 (0.0) | 284.9 (528.78) | 1.002 Bone32 | 0 (130) |
| magreeb | Fidget2 | -0.0..0.0 (0.0) | 73.2 (300.67) | 1.016 Bone114 | 112 (179) |
| magreeb | Hit2 | -0.0..0.0 (-0.0) | 169.63 (300.67) | 1.052 Bone61 | 85 (179) |
| magreeb | Death2 | -0.0..0.0 (-0.0) | 164.22 (300.67) | 1.099 Bone114 | 145 (179) |
| magreeb | Backpedal | -0.0..0.0 (0.0) | 313.24 (300.67) | 1.022 Bone114 | 121 (179) |
| magreeb | BackpedalRun | -0.0..0.0 (0.0) | 324.13 (300.67) | 1.02 Bone114 | 168 (179) |
| magreeb | Taunt | -0.0..0.0 (0.0) | 239.56 (300.67) | 1.016 Bone114 | 116 (179) |
| pig | Fidget2 | -0.2..0.5 (0.0) | 8.4 (66.59) | 1.231 Xftfoot01 | 27 (83) |
| pig | LieDown | -0.7..2.4 (-0.0) | 52.5 (66.59) | 1.064 XtailC | 46 (83) |
| pig | Roll | -0.2..1.8 (-0.0) | 27.72 (66.59) | 1.059 XtailC | 64 (83) |
| pig | Rest | -0.0..0.1 (-0.0) | 1.61 (66.59) | 1.059 XtailC | 28 (83) |
| pig | StandUp | -0.4..4.0 (0.0) | 63.73 (66.59) | 1.059 XtailC | 46 (83) |
| pig | Hit2 | -0.0..0.8 (-0.0) | 34.9 (66.59) | 1.044 Xbkpivot | 65 (83) |
| pig | Death2 | -0.1..3.5 (-0.0) | 64.77 (66.59) | 1.253 XtailC | 79 (83) |
| wingedmutant | Taunt | 22.2..54.2 (40.1) | 1484.04 (1388.27) | 1.628 Xtoe01 | 1506 (2221) |
| wingedmutant | AttackMelee2 | 18.8..66.8 (40.1) | 1152.95 (1388.27) | 1.628 Xtoe | 1680 (2221) |
| wingedmutant | Hit2 | 0.0..64.0 (25.2) | 817.4 (1388.27) | 1.628 Xtoe01 | 1763 (2221) |
| wingedmutant | Death2 | 0.0..125.1 (0.0) | 292.12 (1388.27) | 1.628 Xtoe01 | 1891 (2221) |
| basilisk | Aware | -0.0..0.0 (-0.0) | 84.7 (204.23) | 1.318 XfinA | 683 (1172) |
| basilisk | Fidget2 | -0.0..0.0 (-0.0) | 12.14 (204.23) | 1.32 XfinA | 1222 (1172) |
| basilisk | Search | -0.0..0.0 (-0.0) | 23.69 (204.23) | 1.268 XfinA01 | 1093 (1172) |
| basilisk | Taunt | -0.0..0.0 (-0.0) | 33.33 (204.23) | 1.268 XfinA01 | 1010 (1172) |
| basilisk | Hit2 | -0.0..0.0 (-0.0) | 231.35 (204.23) | 1.268 XfinA01 | 1068 (1172) |
| basilisk | Death2 | -0.0..0.3 (-0.0) | 238.71 (204.23) | 1.268 XfinA01 | 575 (1172) |
| crow | Perch | -0.0..0.0 (0.0) | 0.43 (199.96) | 2.756 Xwmid | 958 (187) |
| crow | PerchFidget | -0.0..0.0 (-0.0) | 34.71 (199.96) | 2.756 Xwmid | 954 (187) |
| crow | Hit2 | 4.4..34.2 (34.2) | 127.26 (199.96) | 1.528 Xfoot | 117 (187) |
| crow | Death2 | -0.0..34.2 (-0.0) | 92.08 (199.96) | 1.528 Xfoot | 172 (187) |
| lobber | Fidget2 | 0.0..0.0 (0.0) | 24.48 (530.14) | 1.002 XApivot01 | 240 (288) |
| lobber | Aware | 0.0..0.0 (0.0) | 123.86 (530.14) | 1.002 XApivot01 | 215 (288) |
| lobber | Hit2 | 0.0..0.0 (0.0) | 454.53 (530.14) | 1.003 XApivot01 | 464 (288) |
| lobberpod | Projectile | 6.0..17.4 (12.6) | 312.52 (214.34) | 1.0 Xblegpiv | 467 (771) |
| lobberpod | Land | -0.1..0.0 (-0.0) | 115.76 (214.34) | 1.0 Xjawpiv | 29 (771) |
| lobberpod | Taunt | -0.1..1.1 (0.3) | 71.63 (214.34) | 1.0 Xhead | 11 (771) |
| lobberpod | Hit2 | -0.0..2.4 (0.3) | 233.24 (214.34) | 1.0 Xhead | 14 (771) |
| lobberpod | Backpedal | -0.0..0.0 (0.0) | 99.57 (214.34) | 1.0 Xbarm | 795 (771) |
| lobberpod | BackpedalRun | -0.0..0.0 (0.0) | 214.34 (214.34) | 1.0 Xbarm | 775 (771) |
| terror | Fidget2 | -0.0..0.0 (-0.0) | 177.08 (1128.68) | 1.0 Bone35 | 67 (115) |
| terror | Hit2 | -0.0..0.0 (-0.0) | 2111.04 (1128.68) | 1.011 Bip01 R Clavicle | 58 (115) |
| terror | Death2 | -0.0..0.0 (-0.0) | 1037.85 (1128.68) | 1.004 Bip01 L Thigh | 185 (115) |
| terror | Taunt | -0.0..0.0 (-0.0) | 164.15 (1128.68) | 1.0 Bone35 | 59 (115) |
| terror | Backpedal | -0.0..0.0 (-0.0) | 315.25 (1128.68) | 1.0 Bone14 | 38 (115) |
| terror | BackpedalRun | -0.0..0.0 (-0.0) | 375.61 (1128.68) | 1.0 Bip01 Spine | 34 (115) |
| hen | Sit | 0.0..0.0 (0.0) | 0.86 (99.43) | 1.007 XneckB | 67 (46) |
| hen | Fidget2 | -0.0..0.0 (-0.0) | 47.4 (99.43) | 1.036 XneckB | 17 (46) |
| hen | Fidget3 | -0.0..0.1 (0.0) | 80.44 (99.43) | 1.034 XneckB | 30 (46) |
| hen | Hit2 | -0.0..0.8 (0.2) | 59.34 (99.43) | 1.037 XneckB | 18 (46) |
| hen | Death2 | -0.4..21.6 (-0.0) | 102.78 (99.43) | 1.037 XneckB | 21 (46) |
| nagate | Taunt | -0.0..0.0 (-0.0) | 48.75 (408.52) | 1.111 Xbcontrol05 | 8 (38) |
| nagate | Fidget2 | -0.1..0.0 (-0.0) | 9.73 (408.52) | 1.022 Xbcontrol04 | 3 (38) |
| nagate | Hit2 | -0.1..6.9 (-0.0) | 71.58 (408.52) | 1.006 Xbcontrol05 | 15 (38) |
| goat | Fidget2 | -0.0..0.0 (-0.0) | 23.43 (87.36) | 1.001 Xblegpiv | 36 (34) |
| goat | RunAttack | -1.4..3.8 (0.0) | 126.16 (87.36) | 1.017 Xblegpiv | 48 (34) |
| goat | Hit2 | -0.0..0.2 (0.0) | 81.86 (87.36) | 1.011 Xffoot01 | 32 (34) |
| goat | Death2 | -0.0..6.4 (-0.0) | 98.94 (87.36) | 1.051 Xfankle01 | 66 (34) |
| ram | Fidget2 | -0.0..0.0 (-0.0) | 19.76 (172.65) | 1.139 Xbfoot | 26 (114) |
| ram | AttackMelee2 | -0.4..4.8 (1.5) | 250.34 (172.65) | 1.085 Xear | 31 (114) |
| ram | Hit2 | -0.0..0.0 (-0.0) | 221.55 (172.65) | 1.094 Xtail | 123 (114) |
| ram | Death2 | -0.8..18.8 (0.0) | 195.51 (172.65) | 1.085 Xear | 85 (114) |
| seamon | Fidget2 | -0.0..0.0 (0.0) | 345.93 (861.0) | 1.0 Bone38 | 5 (212) |
| seamon | Hit2 | -0.0..0.0 (-0.0) | 1156.81 (861.0) | 1.028 Bone37 | 80 (212) |
| seamon | Death2 | -0.0..0.0 (0.0) | 1089.71 (861.0) | 1.007 Bone37 | 182 (212) |
| seamon | Jump | -0.0..0.0 (-0.0) | 1663.46 (861.0) | 1.0 Bone03 | 343 (212) |
| sheep | Fidget2 | -0.0..0.0 (-0.0) | 21.36 (175.79) | 1.139 Xbfoot | 26 (69) |
| sheep | AttackMelee2 | -0.4..4.8 (1.5) | 259.95 (175.79) | 1.085 Xear | 31 (69) |
| sheep | Hit2 | -0.0..0.0 (-0.0) | 222.36 (175.79) | 1.094 Xtail | 28 (69) |
| sheep | Death2 | -0.8..6.0 (-0.0) | 195.89 (175.79) | 1.085 Xear | 25 (69) |
| cat | Fidget2 | -0.0..0.0 (-0.0) | 1.71 (40.6) | 1.161 XbackB | 434 (719) |
| cat | LieDown | -0.1..0.5 (-0.0) | 6.56 (40.6) | 1.751 Xblegpiv01 | 678 (719) |
| cat | GetUp | -0.1..0.5 (-0.0) | 6.56 (40.6) | 1.751 Xblegpiv01 | 671 (719) |
| cat | Lie | -0.0..0.0 (0.0) | 0.24 (40.6) | 1.751 Xblegpiv01 | 673 (719) |
| cat | LieFidget | -0.0..0.1 (-0.0) | 3.17 (40.6) | 1.751 Xblegpiv01 | 691 (719) |
| cat | LieFidget2 | -0.0..0.0 (-0.0) | 2.33 (40.6) | 1.751 Xblegpiv01 | 734 (719) |
| dragonking | Fidget2 | -0.0..2.1 (-0.0) | 1064.98 (1721.18) | 1.722 Ybbase01 | 752 (1538) |
| dragonking | SpitAcross | -0.0..0.3 (0.0) | 1348.14 (1721.18) | 1.737 Ybbase01 | 1378 (1538) |
| dragonking | Breath2 | -0.1..2.9 (-0.0) | 1387.55 (1721.18) | 1.722 Ybbase01 | 1027 (1538) |
| dragonking | Hit2 | -0.0..0.0 (-0.0) | 1518.53 (1721.18) | 1.843 Ybbase | 500 (1538) |
| rooster | Fidget2 | 0.0..0.0 (0.0) | 6.83 (103.3) | 1.06 XtailE | 21 (39) |
| rooster | Hit2 | -0.2..6.5 (0.0) | 67.3 (103.3) | 1.055 XneckB | 17 (39) |
| rooster | Death2 | -1.1..22.2 (0.0) | 110.29 (103.3) | 1.238 XtailE | 32 (39) |
| dog | WalkSniff | -0.8..0.6 (0.4) | 77.92 (487.32) | 1.105 XneckC | 31 (56) |
| dog | WalkBark | -1.3..0.7 (0.7) | 131.55 (487.32) | 1.118 XneckC | 8 (56) |
| dog | RunAway | -1.7..8.2 (3.6) | 494.56 (487.32) | 1.175 XneckC | 134 (56) |
| dog | Sit | -0.0..0.0 (0.0) | 1.08 (487.32) | 1.667 XbackB | 7 (56) |
| goose | Fidget2 | -0.0..0.4 (-0.0) | 21.41 (151.45) | 1.059 Xfoot01 | 0 (0) |

## Not checked
No viewer (textured) shots, no playback at normal speed, no in-game run of any new clip: nothing drives them yet. Collapse/fold
gates, detached-parts audit and LOD1-3 not run on the new clips (LOD0 only). Ranged/spell events of the new attack clips (Breath2,
SpitAcross, AttackRanged2) are not bound to sockets (script clips only). The sheep's own strip was not read separately.

