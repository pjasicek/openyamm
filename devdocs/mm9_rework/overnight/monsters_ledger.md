# Overnight monsters ledger

## Second run (started 2026-10-31 afternoon, user's word)
The user ordered: no dropped clips on any body; finish lizardorc, bigfoot, dookmilitia and dwarf; then the 7 unstarted bodies.
The head audit is done (user: "should be fixed already"). Budget: backup balance at the start of this run 4075. The ceiling is still
<= 3785 (1,000 for both runs), so 290 credits are left, at most 40 per body. Max 6 agents at once.
- Wave 1: finish-lizardorc, finish-bigfoot, finish-dookmilitia, finish-dwarf, clips-A (honkmale, honkfemale, clansoldier, mummy,
  banshee, skeleton; verify thrall, evilsorcerer, ghoul, monk), clips-B (zombie, troglodyte, gezzampt, highwayman, nobleman;
  verify nosferatu, trellborg, ghost, guard; read-only count on the approved and animal bodies).
- Clips go on with `claude_shared/graft_clips.py`, so meshes, LODs, variants and accepted clips stay byte-for-byte.
- Wave 1 started (6 agents): af2f481e492bc0d6c lizardorc, aaea55dd64a5dd099 bigfoot, a77f2fa885257d6c2 dookmilitia,
  a3c3aadb1ea295ecd dwarf, ae2fcd6ab31439f75 clips-A, a0641ba85e55cc502 clips-B. Shared agent rules: RUN2_COMMON.md.
- clips-B done: 14 clips on zombie (3), troglodyte (2), gezzampt (2), highwayman (3), nobleman (3), guard (1); nosferatu,
  trellborg, ghost complete. Regression 147 descriptors / 58 models, 0 failed; 0 credits. Strips read by the orchestrator (guard
  cower, zombie Death2/Wakeup2/Coffin2): clean. Details status/clips_groupB.md. Its census found drops on the older bodies too.
- clips-C started (aaaeda4ebc69fb783): the 26 older animal and monster bodies, from the census.
- Asked the user: approved imp (7), skelwar (8), lich (3), and annud/forad (53/40, the shared PeasantMale town-NPC library).
- clips-A done: honkmale/honkfemale +11 each (20/20), clansoldier +2 corpses, mummy +4, skeleton +2, banshee `fly: Walking`
  (MM9 Fly = WalkAir keys); thrall, evilsorcerer, ghoul, monk complete. Regression 147/58, 0 failed; 0 credits. Orchestrator read
  honk female cower close-up and mummy strip: clean. Open: Honk Fidget2 upper-arm jitter +1.3-1.8 deg/f (hands pushed out of the
  hips). Details status/clips_groupA.md.
- giant started (aab67b084190c650a), cap 30 credits.
- dookmilitia r12 installed, 0 credits: detached 0, weapon vs body Cower 5.6 -> 0.6 cm, arm/hand all < 1 cm, floor -4.5 -> -1.1
  (-1.85 between keys), skirt thighs/torso clear, jitter 0, regression 147 PASS, in game at Dook's Castle. Taunt2 added (all ABC
  clips carried). Open: collapse counts unchanged from r9 (Sleep neck 58/head 66, Death neck 63...), cheek patch under the bars.
  Orchestrator read cower and head sheets. Sent back for a second pass on collapse + cheek repaint (max 10 credits).
- bigfoot r7 installed, 0 credits: arm/hand 0 frames > 1 cm (worst 0.8), all 18 MM9 clips + Dead (5 new script clips), saddle and
  Yeti patch soft ellipses, regression PASS. Jitter as written 22 flags (21 from the accepted 12 deg arm abduction; 1 own, Death2
  R). Collapse not worked. Orchestrator read hands and tier sheets: good. Sent back for collapse, unread sheets, neck band/specks.
  Note: the actors suite has 2 failures outside the MM9 bodies (MM6 ogre Hit blend, out05 gameplay data), not ours.
- lizardorc r16 installed, 0 credits (30/40 total): breastplate trimmed V with leather trim, flecks/neck streak/chin crease
  fixed, floor 0 flagged (worst -1.9), jitter 0, blade 0 except AttackMelee2 1.3 cm 1 frame, fist/tasset 0. FAILED after two tries:
  plates in thighs (Running 3.3, AttackMelee2 5.2, Death2 4.2 cm...). Death2 L hand 3.6 cm 1 frame (jitter trade-off). Collapse
  not worked (head 104, torso 56). Orchestrator read tiers (good) and close-ups (knee/groin Death/Dead shot from inside the mesh).
  Sent back: reframe close-ups, collapse attempt.
- clips-C done: 137 clips on 26 models (dfly, greaterdemon, dagrell, eye, icky, cow, wolf, magreeb, pig, wingedmutant, basilisk,
  crow, lobber, lobberpod, terror, hen, nagate, goat, sheep, ram, seamon, cat, dragonking, rooster, dog, goose), byte check
  passed, regression 147/58 + MM6-8 647/185 green, 0 credits. Left out: lobber fall1/falldown1 (ceiling drop on an upright
  body), seamon diewater2 (already the Death). Look at: crow perch wings sink into flanks; dog run_away tail into the rump,
  -1.7 cm floor. Orchestrator read greaterdemon and dog strips. Details status/clips_groupC.md.
- yanmir started (ac5e0433651c0c920), cap 30 credits.
- User, 2026-10-31: (1) add the missing clips to the approved imp (7), skelwar (8) and lich (3) by graft, byte-for-byte;
  (2) annud and forad carry only the PeasantMale clips their MM9 scripts/dialogue use. Queued as clips-D, takes the next free
  slot ahead of the remaining new bodies.
- dwarf r17 installed, 0 credits (20/40): skirt roll gone (bunching 34/94 -> 1/2 faces), thighs through skirt 0 except Death2
  2.1 cm (4 frames), arm/hand 0 on bound clips, jitter 0, axe Fidget 0, helmet rim < 1 cm (new rim_gate.py), all 16 clips,
  regression PASS. In game standing only (tour no longer takes `steps`). Orchestrator read skirt and hand sheets: skirt good;
  dark jagged wedge between glove and cuff at hard wrist bends (hands AttackMelee_0, AttackRanged_0). Wrist pass queued next.
- clips-D started (a01fc756da97bf4bb): imp, skelwar, lich by graft; annud/forad only clips their scripts play.
- clips-D done, 0 credits: imp 9->16, skelwar 12->20, lich 15->18 (all MM9 clips), annud 8->14 and forad 9->15 (only clips
  their scripts play; lists in READMEs). Byte check passed on all five; regression 149 descriptors / 59 models PASS. Look at:
  forad's seated clips crouch in the air (need the Thronheim seat; right foot 7 cm above left); annud Conv1 hand at chin 3 cm and
  jitter 1.25 deg/f; skelwar Death2 hands on hilt 6 cm (as accepted Death). Orchestrator read forad strip and skelwar Death2.
- dwarf sent back for the glove/cuff wedge (same agent).
- dookmilitia r17 installed, 0 Meshy, 3 Codex edits: cheek patch repainted from one source per tier (read: clean); weight
  smoothing at neck/hood seam/belly/collarbones: neck 58-63 -> 1-7, head 66 -> 7-24, AM3 torso 54 -> 12. FAILED after two
  passes: collapse on the shoulder pad (Sleep 35/28, Death/Dead 48, Hit R 44, Fidget3 31) and head 24 in Death/Dead; a full
  shoulder zone opened a dark gap at the pad hem, so dropped. Orchestrator read heads and shoulders (AM3 pad strips splay).
  Sent back for verification only: hood back hem (moved up to 12 cm), B/C strips, r17 sheets, in game.
- lizardorc r17 installed, 0 credits: close-ups reframed from outside (closeups2.py); collapse counts were all neck, not
  mouth/skull: wider neck weight ramps cut Death torso 56 -> 5, Dead head 49 -> 20, AttackMelee head 46 -> 22 (Death head
  still 96, the neck ring at 85 deg); AM R shoulder 5 -> 12. Thigh plates FAILED (recorded). Orchestrator read close-ups (ok)
  and neck sheet: under-jaw paint defects (pale octagon fan, smears, yellow slivers) visible in Hit2/Death2/Dead. Sent back
  for one focused throat repaint, max 10 credits.
- dwarf r18 installed, 0 credits (20/40): glove/cuff wedge fixed by weights (cuff mouth opening 1.75 -> 0.74 cm worst, all
  clips < 1 cm); jitter, grip, axe, arm/hand unchanged. Orchestrator read sheet_wrists: wedge gone, thin dark rim at the
  hardest bends, small fold in Search. DONE for this run; open gate: thigh through skirt Death2 2.1 cm, 4 frames. In-game
  attack/hit/death still unseen (no flat empty map found for a staged fight).
- lichking started (a37b046ac566cdea0), cap 30 credits.
- giant r10 installed and bound (Plain A, Forest B), 20 credits (backup 3985): built at 0.3 x MM9 scale, binding 333.333;
  per-tier head images (deviation, MM9 has two heads); all 15 distinct clips. Gates: arm/hand < 1 cm except AttackMelee L 5.2
  (19 f) / R 1.5; mallet into body AttackMelee 8.0, Death 4.5; left fingers in shaft 1.3-2.6 in Taunt/Aware/attacks; jitter
  Death2 1.1/1.0; mallet UV stretch 23.7. Orchestrator read mm9_vs_ours and heads: very good. Sent back for a second pass
  (max 10 more credits).
- dookmilitia r19 installed: hood back hem had lifted with the bowed head on r17 (gap, inside showing); original weights
  restored there, hem hangs as on r12. Cost: neck collapse back up at the hem (Death 67, Dead 54, AM3 49/torso 45). B/C strips,
  close-ups, hands, tiers read on r19: clean; in game at Dook's Castle ok. DONE for this run; collapse FAILED (shoulder pad, hood
  hem). Orchestrator read sheet_hood_back_a: nape shows under the hood when bowed (as r12), small jagged hem bits in Sleep.
- colloidalwarrior started (abe0049c98223b8b1), cap 30 credits.
- yanmir r4 installed (MM9 206, scale 333.333), 20 credits (backup 3970): all 20 clips; Death/Death2 retargeted from MM9's
  Giant (his own Die ends standing on a trap floor; trap clips kept as script clips); staff and crown built in code. FAILED:
  jitter 7 flags left arm (second try traded it for a hand 9.6 cm in Death); Death2 hands 3.5/6.0 cm. Collapse not zero
  (Death2 hips 72, head 85). Orchestrator read mm9_vs_ours and heads: very good, but the staff is a thin silver rod (MM9: thick
  speckled pole, cage head) and the head reads as a smooth column from behind. Sent back: staff, thumb, head back, disks.
- lizardorc r18 installed, 0 credits: jaw underside/throat repainted from one Codex source (below + front views), jaw-tip fan
  and neck-ring strip given their own UV space, 148 folded neck-ring triangles rebuilt flat. Orchestrator read sheet_throat_a:
  continuous belly scales, defects gone; pale stretch band low on the throat in Hit2 from below remains. DONE for this run;
  thigh plates FAILED (recorded). Not reshot on r18: strips, close-ups, in game.
- stage1demon started (aafbf8378ae7809e4), cap 30 credits.
- yanmir r5 installed, 0 more credits (20 total): staff rebuilt thick with a petal-cup head and Codex speckled pole paint,
  thumb closed (15 -> 90 deg), back hair widened and contrasted (head stretch 1.64 vs 1.5 target), disks dark silver.
  Orchestrator read r5 mm9_vs_ours: staff now matches MM9. DONE for this run; FAILED: left-arm jitter 7 flags, Death2 hands
  (Giant's kneel puts both arms under the torso, IK fix found no solution). Not redone on r5: close-ups, in game, strips 1/3.
- njam started (ad926a8a8e128bec8), cap 30 credits.
- lichking r1 installed and bound (row 209, scale 135), 15/30 credits, regression green (152/62). Orchestrator read sheet_mm9_vs_ours: matches MM9 well.
  FAILED gates: Running coat/tabard through thighs (16 and 13 of 21 frames, 7.7 cm); Death2 coat stands up like a tent (47/64 frames); shoulder collapse with arms raised (43-55).
  Also: Standing staff leans 13 deg across the body; staff skull is pale, MM9's is yellow-green.
  Sent back (0 credits) for a second serious try on all five.
- bigfoot second pass: the agent stalled with r9 done (final shots, regression 191/2 with the known outside failures). Woken to read its sheets and report.
- ebora started (ab18a176aa8815937), cap 25 credits; Concubine rows become tiers if they share the model. Backup balance 3900 at start.
- bigfoot r9 installed, 0 credits (20 total), regression green (147/58, whole suite 191/2 with the known outside failures).
  Collapse roughly halved: WalkFidget head 44 -> 11, Hit2 42 -> 21, Death 36 -> 19, AttackMelee shoulders 24/12 -> 14/11.
  Changes: the head-twist soft cap (WalkFidget turn 96 -> 74 deg, a deviation from MM9), the head pivot moved 8 cm forward, throat and armpit-wall weights.
  Texture: mask fur channel = 1 (the red belly band and the warm Yeti rim are gone); neck_rim.py removes the pale collar specks.
  Orchestrator read sheet_collapse_r7_r9 and sheet_tier_heads_r9: the neck is clean in WalkFidget, the tiers read right, and there is a slight facet under the jaw.
  DONE for this run; FAILED: collapse (folds remain where the chin presses into the chest or shoulder, plus JumpingDown's R shoulder 13 and the gait knuckles); jitter 22 flags as written (21 from the accepted 12 deg abduction).
  Not done: normal-speed playback; B strip 3 and C strips 2/3 after the last colour pass; a thin pale line on the Yeti chest in Dead.
- colloidalwarrior r1 installed and bound (MM9 Colloidal A/B/C, scale 150/175/200), 20/30 credits, regression green (155/63).
  FAILED: jitter (3 clips strict, 1 relative); collapse (Death2 head 116, Hit2 89, AttackMelee R shoulder 70); script-clip hands in the body (Death2 R 6.0 cm, BackpedalRun L 5.8 cm).
  Orchestrator read mm9_vs_ours_tiers and closeups_b: the face matches; the tiers are too light and saturated (lime vs MM9 dark olive, pink tan, bright rust); the AttackMelee armpit has a dark torn notch; a smooth untextured blob in Death (cbde5); the body is smaller and toad-like vs MM9's slab.
  Sent back (0 credits) for tone, armpit, collapse, cbde5, script-clip hands, and bulk if it is cheap.
- giant r16 installed, 0 more credits (20 total), regression green (155/63), floor and viewer ok. The second pass fixed:
  - the mallet between the thighs;
  - the left fingers in the shaft (except 3 windup frames);
  - the mallet UVs (stretch 23.7 -> 1.02, hand layout; uv_atlas fragmented the 260-tri mallet);
  - the collar wedges;
  - Death2 jitter;
  - a full-body in-game frame of both tiers at a Guberland jetty.
  The AttackMelee grip is held only at the start and end (MM9's swing is one-handed).
  Orchestrator read ingame2/g07 (the giants read well) and sheet_hands2: the LEFT hand in Standing, Walking and Aware is an open palm under the shaft, not a closed fist; the right fingers drape.
  DONE for this run (two serious passes); FAILED: jitter 3 (AttackMelee L upper arm 2.55, R forearm 1.08, AttackRanged L shoulder skin 2.21); AttackMelee fists meet (R 4.6 cm, 3 frames), shaft into the L palm heel 3.2 cm, 4 frames; the left-hand grip reads open; mallet atlas 51 %.
  Not read on r16: tier B strips, closeups_a, heads, fists.
- stage1demon r5 installed and bound (MM9 Demon A, row 241, mm9_lesserdemon.glb), 30/30 credits, regression green (155/63).
  FAILED: detached 32/144 (skirt shards up to 7.2 cm, tongue, tail); floor (walk feet lift +7.9 cm); jitter 3; Death L hand 3.0 cm (9 frames). No in-game frame.
  Orchestrator read sheet_mm9_vs_ours and close_joints: the poses and head are good. Ours is bright red with pale silver, against MM9's dark red-black with gunmetal plates; dark smudged knee patches; the horns are smaller.
  Sent back (0 credits) for tone, detached, floor, knees, Death hand, an in-game frame, and the horns if cheap.
- All five running agents (lichking, colloidalwarrior and stage1demon on second passes; njam and ebora) stopped on the 5-hour usage limit. The limit reset at 20:30, and all five were resumed from their saved transcripts.
- lichking r13 installed, 0 more credits (15 total), regression green (158/65).
  - Cloth gate corrected: it now counts only outside hits, and r7 was re-measured with it.
  - Running coat 16 -> 7 of 21 frames (4.9 cm); tabard 0.
  - Death2 coat 40 -> 15 of 64 frames; Death/Death3 17 -> 5.
  - Staff matches MM9 within 0.6 deg; staff skull yellow-green.
  - Torso collapse 55/43/44 -> 51/25/25; atlas 55.3 %.
  - Detached parts: 8 of 91 loose, worst 1.33 cm.
  - New deviation for the user: in AttackMelee the head ducks 30 deg for 0.25 s so the left hand clears our taller crown.
  Orchestrator read strips_r13_run_death2 and the attackmelee duck sheet: Running reads clean. In Death2 the back coat still stands up like a wall mid-fall, and in Dead2 the coat lies bunched high.
  DONE for this run (two serious passes); FAILED: Running coat (7 frames), the Death2 tent and coat folds 113, AttackMelee torso collapse 51. No in-game check this pass.
- ebora r12 installed and bound (MM9 301 Ebora skin eb, MM9 302 Concubine skin s1; siren2-4 as ramps, unbound), 25/25 credits, regression green (158/65).
  - The wings are built procedurally on MM9's wing bones.
  - Separate Ebora and siren paints (a recorded deviation: two designs on one mesh).
  - Detached 0, jitter 0.
  FAILED: wing collapse ~150/wing when folded (inherent to MM9's fan close; partial pleat kept); forearms 4.7-5.9 cm into the wing in Death/Dead.
  Orchestrator read sheet_mm9_vs_ours and sheet_tiers: the look and poses match. The spread wings render dark maroon for every siren tier (MM9: orange, and blue for s4), while the folded wings are correct.
  Sent back (0 credits) for the spread-wing colour, Death forearms, Concubine tone, and reshoots plus an in-game frame on the final build (the current ones are r3/r4 and r8).
- njam r11 installed and bound (MM9 261 Njam the Meddler, scale 150), 20/30 credits, regression green (158).
  - All 47 clips carried (41 from PeasantMale.abc).
  - Jitter 0. Collapse: Kick 6456 -> 3912, AttackRanged 3045 -> 1707.
  - In game at his own spot in arslegardcity.blv.
  FAILED after two attempts each: AttackMelee L hand 6.0 cm (43 frames, rests on the belly); Cast R 5.9 cm (12 frames); AttackRanged R 4.7 cm (7 frames); torso atlas 53.7 %.
  Orchestrator read sheet_mm9_vs_ours and sheet_head_full: the body and poses match MM9 well. The face is poor (gaunt, droopy, smeared nose, tired eyes), with a dark fringe band, pale cheek strips at the hairline, and helmet hair.
  Sent back for a head-only pass (up to 10 more credits, only if Codex plus projection is not enough) and r11 reshoots.
- stage1demon r10 installed, 0 more credits (30 total), regression green (158/65).
  - Tone graded by region mask: dark maroon hide, gunmetal plates.
  - Detached 32 -> 11 (each piece now takes weights from the point it rests on).
  - Floor ok: toes and tail bend out of the floor per frame, and the root keeps MM9's motion.
  - Knees darkened into plates; horns 1.4x.
  - In game on Isle of Ashes open grass: full body, friendly and hostile, ranged attack firing.
  Orchestrator read sheet_mm9_vs_ours_samelight (MM9 loaded in the same viewer light: the tone now matches, ours slightly darker) and ingame_sheet_p2.
  DONE for this run (two serious passes); FAILED: detached 11 (tail tip flag, 5 groin shards up to 3.6 cm, talons 5.6 mm, chest shards); Death L hand 5.9 cm (51 frames, worse than pass 1); jitter 3; collapse at the mouth corners and the Death throat.
- ebora second pass installed (sha 8c1fc6165863), 0 more credits (25 total), regression green (158/65).
  - Spread wings: the membrane normals now tilt along the wing's up axis (the down-facing layer got no ambient). Tier colours now show in flight and were checked in game.
  - Corpse arm: lifted 18 deg (arm_lay.py); Dead 0 crossings; fall 4.7 -> 1.3 cm.
  - Siren1 skin and lips now match MM9.
  - Wing flat shading 0.21 -> 0.00.
  Orchestrator read the reshot sheet_tiers: the spread wings are red, orange and blue as in MM9.
  DONE for this run; FAILED: wing collapse ~155/wing when folded (MM9's own fold); fall arm 1.3 cm briefly; AttackRanged R 1.4 cm (2 frames); Land L 1.6 cm (script clip).
  Not checked: the bathhouse map, siren3/4 in game, wing lighting indoors.
- njam r14 installed, 0 more credits (20 total), regression green (158/65).
  - Head repainted from a Codex HD close front view, placed by 15 landmarks (one paint source per feature).
  - Hair underside carries the hair paint; the cheek strips and the dark fringe band are gone.
  - Pageboy roll on the hair rim.
  Orchestrator read sheet_head_full r14: young, smug, clear green-blue eyes, a one-sided smirk. A clear improvement.
  DONE for this run; FAILED (recorded): three arm-hand contacts (AttackMelee L 6.0, Cast R 5.9, AttackRanged R 4.7 cm); torso atlas 53.7 %.
  Remaining softness is from Meshy's head geometry; a tonal step on the cheek side, a small nick on the right cheek, and a thin pale hairline.
  Not done: the face up close in game; strips and close-ups not reshot on r14.
- Overview page: the 7 new bodies were added (yanmir, giant, lichking, colloidalwarrior, lesser demon, njam, ebora) as status open with what to look at. Second-run rework notes were added to dwarf, half-orc, lizard-orc and bigfoot (already user-approved). The JS parses. Colloidal will be updated after its second pass.
- USER REVIEW 2026-11-01 of the new bodies:
  - njam "ok i guess"; yanmir "good"; lich king "good". Marked ok on the overview page.
  - giant: "the hammer isnt properly held by the hands ... like its not in tha palms but like intersects"; "the hammer itself needs better texture/model or you can generate it by meshy". Resumed the giant agent: grip rebuilt to the Lich King's grip gate, plus a new mallet (cap 25 credits).
  - ebora/concubine: "needs better head texture". Resumed the ebora agent: Codex close-view face repaint, as for njam (cap 10 credits).
  - lesser demon: "check the neck" (a dark featureless bulge under the jaw, a hard crease into the chest). Its agent was stopped by the user and cannot be resumed; the fix waits for the user's word to start a new agent.
  - The user also stopped the lizardorc and bigfoot agents; both had already reported, so nothing was lost.
  - The colloidal agent had stalled since 20:39 with its r6 rebuild done, and was woken.
- colloidalwarrior r9 installed, 0 more credits (20 total), regression green (158/65).
  - Tone: under the same viewer light, MM9 was lighter than the Blender renders suggested. Saturation x0.88 (now matches); Soldier value 0.80; specular 0.4.
  - Armpit-wall weights: AttackMelee R shoulder 70 -> 55; the notch is now a closed crease.
  - Head soft cap 35/50 (a deviation): Hit2 89 -> 41, Death2 116 -> 93.
  - cbde5 was a camera 10 cm from a fingertip.
  - BackpedalRun hand cleared; bulk tried and not kept (a deviation).
  Orchestrator read tone_cmp and ingame_sheet: the tones match MM9 well.
  DONE for this run; FAILED: Death2 R hand 6.0 cm (7 frames); jitter 5 clips strict (2 relative); atlas 51-52 %.
  Overview entry updated (open).
- USER 2026-11-01: "colloidal warrior ok" (r9). Marked ok on the overview page.
- USER 2026-11-01: "ok" to a new agent for the lesser demon neck. Started ab478c81c1baf6376 (cap 10 credits).
- ebora head pass installed (sha ac7581618509, 0 credits): Codex face repaint on clay renders, 15 landmarks, 2K head texture, the forehead strand folded up, and the siren tiers carry the new face. Gates and regression unchanged.
  Orchestrator read sheet_head_full: a clear step up. Sent back (0 credits) to fix the dark rectangular stub at the hairline centre, the bright nose-bridge streak, and the flat pale ear cards.
- giant r21 installed (user-review pass): palm grip with the fingers wrapped (R wrap 185, L 209 deg). New Meshy mallet from a Codex HD master of MM9's mallet (15 credits; 35 total); texture gate passes (67 % atlas).
  REGRESSIONS: Fidget L hand 6 cm (58 frames); corpse mallet in the thigh 4.2 cm; jitter 3 -> 5.
  Orchestrator read grip_std (frame 24 wraps well) and sheet_mallet (much better). Standing frame 0 (h3_M_grip) still shows the open left fingers; tier B steel reads as grey wood.
  Sent back (0 credits) for frame-0 and loop wrap, Fidget release, corpse, jitter smoothing, and the tier B metal look.
- STOP (user, 2026-11-01, 99 % quota): giant, ebora and lesser-demon-neck agents stopped by the orchestrator; leases released. Handoff: MONSTERS_HANDOFF_RUN2.md.
- Wave 2, as slots free up: giant, yanmir, lichking, colloidalwarrior, stage1demon, njam, ebora (queue order).

## After the report (2026-10-31 10:40)
User answers are in MONSTERS_HANDOFF.md section 4. Engine: ModelRenderer anchorJoint sort built, binding regression passes; not looked at in game. Zombie graft and banshee graft passes running.

## Morning report (final, 2026-10-31 10:20)
Stopped by the user at 91 % of the weekly limit, with all work in progress finished. **Start with [the handoff](MONSTERS_HANDOFF.md).**
Review page: http://127.0.0.1:8912/level_generation/creatures/claude_shared/mm9_overview/index.html

- **Built:** 23 of 30 bodies installed and bound. Binding regression: 143 descriptors on 58 models, 0 failed. Credits 710 of 1,000 (backup balance 4,075).
- **Accepted (11):** skeleton, banshee, thrall, evilsorcerer, ghoul, nosferatu, gezzampt, monk, mummy, ghost, honk male.
- **Re-check after your feedback (6):** guard, troglodyte, highwayman, clansoldier, nobleman, honk female.
- **Not reviewed yet (5), cleanest first:** dwarf, trellborg, dookmilitia, bigfoot, lizardorc. The last three failed gates and are not finished.
- **Zombie:** good, head graft fix queued.
- **Not started (7):** giant, yanmir, lichking, colloidalwarrior, stage1demon, njam, ebora.
- **Broken along the way, repaired:** 14 leaked Chromes took the load past 300; the Half-Orc agent stalled for 1 h 45 min and was replaced; the monk agent killed the nosferatu agent's job.

## Links
User, 2026-10-30: everything goes in the composite overview, http://127.0.0.1:8912/level_generation/creatures/claude_shared/mm9_overview/index.html. No viewer-by-viewer links in any report to the user, including the morning report.

## Budget
- Backup balance at start: **4785** (primary 2). Stop new Meshy work when the backup balance is **<= 3785** (1,000 spent) or < 500.

## Queue
| # | Body | Project | State | Agent | Credits | Notes |
|---|---|---|---|---|---|---|
| 0 | honkmale + honkfemale | mm9_honkmale_claude, mm9_honkfemale_claude | both ACCEPTED by the user 2026-10-31 | a8a6f60b83a796f17 | 10
| 1 | skeleton | mm9_skeleton_claude | ACCEPTED by the user 2026-10-31 | af8fcce2961d78094 | 40
| 2 | zombie | mm9_zombie_claude | ACCEPTED by the user 2026-10-31 | a6781217e4cc2d357 | 40
| 3 | mummy | mm9_mummy_claude | ACCEPTED by the user 2026-10-31 | aa560097a414a2350 | 40
| 4 | guard | mm9_guard_claude | ACCEPTED by the user 2026-10-31 | a8181cb534fbc70ec | 35
| 5 | ghost | mm9_ghost_claude | ACCEPTED by the user 2026-10-31 | ad6049203f9de225c | 40
| 6 | banshee | mm9_banshee_claude | ACCEPTED by the user 2026-10-31 | a34ff23799b9cfea4 | see-through |
| 7 | thrall | mm9_thrall_claude | ACCEPTED by the user 2026-10-31 | a161bdaaa1cfe3d4e | 40 | |
| 8 | troglodyte | mm9_troglodyte_claude | ACCEPTED by the user 2026-10-31 | a64e804535c7dbae9 | | |
| 9 | highwayman | mm9_highwayman_claude | ACCEPTED by the user 2026-10-31 | acf13ae33ea7ba87d | 40 | |
| 10 | evilsorcerer | mm9_evilsorcerer_claude | ACCEPTED by the user 2026-10-31 | ad851e1ecf16528b7 | | |
| 11 | ghoul | mm9_ghoul_claude | ACCEPTED by the user 2026-10-31 | ae15af0cc6e807520 | 30 | |
| 12 | nosferatu | mm9_nosferatu_claude | accepted by the user | a78f3764d189057c2 | 20 | |
| 13 | gezzampt | mm9_gezzampt_claude | ACCEPTED by the user 2026-10-31 | a2ac10c9d7aed5be3 | 20 | |
| 14 | monk | mm9_monk_claude | ACCEPTED by the user 2026-10-31 | ae59339a56950bd13 | 20 | |
| 15 | dookmilitia (Half-Orc) | mm9_dookmilitia_claude | ACCEPTED by the user 2026-10-31, open gates recorded | aee86dbac6eeee17b | 40 | stalled 06:34-08:19, stopped and resumed from files |
| 16 | clansoldier | mm9_clansoldier_claude | ACCEPTED by the user 2026-10-31 | ad725fd37e8f4f39b | 40 | |
| 17 | dwarf | mm9_dwarf_claude | accepted by the user | a30c602d1566278aa | 20 | |
| 18 | nobleman | mm9_nobleman_claude | ACCEPTED by the user 2026-10-31 | a3a0c4f8d0842c8d0 | 40 | |
| 19 | trellborg | mm9_trellborg_claude | accepted by the user (r10 cuffs) | af22c91b62668c41f | 40 | |
| 20 | lizardorc | mm9_lizardorc_claude | accepted by the user (r15) | ab7823f451ebce3c0 | 30 | |
| 21 | bigfoot | mm9_bigfoot_claude | ACCEPTED by the user 2026-10-31, open gates recorded | a2e8508f6ba61db82 | 20 | |
| 22 | giant | | queued | | | |
| 23 | yanmir | | queued | | | |
| 24 | lichking | | queued | | | |
| 25 | colloidalwarrior | | queued | | | |
| 26 | stage1demon | | queued | | | |
| 27 | njam | | queued | | | |
| 28 | ebora | | queued | | | |

## Rework queue (takes the next free slot, ahead of new bodies)
- STOP (user, 2026-10-31, weekly limit at 91 %): no new work. Running agents finish; giant, yanmir, lichking, colloidalwarrior, stage1demon, njam and ebora are not started and stay queued. The map follow-up for sleeping guards also waits.

## Open decisions for the user
- 22:55: zombie, mummy and guard chose per-tier body images (tier designs differ), against "no per-tier baked base colours". Paints were already committed on mummy and guard. Told all three to keep colour-only differences in ramps, record the deviation with its memory cost, and confirm per-tier binding. Review at the end.

- Guard: per-tier images upload for every tier even when only one is on a map (+40.8 MB GPU memory). This is the real cost of per-tier images, on guard, mummy and zombie alike.
- Guard: Town Guard rows 107 and 109 use guard.abc but have no descriptors. Bind them?
- Ghost: user asked whether the flying head is intended (review/user_feedback_head_gap_20261031.png). It is MM9's: Xhead hangs on the scene root and clips move it up to 49 cm. Our resting gap looks larger than MM9's; not measured.
- Banshee: the head is now opaque to fix self-order faults, losing MM9's 8-19 % see-through there; it may also cast a shadow alone. Keep it? The Ghost has the same head fault at lesser scale.
- Banshee rows are canFly N although Banshee.scr uses FlyRange.inc, so she stays on the ground. Table owner to decide.
- Banshee melee decay needs a runtime skin switch (engine work); the decay became the tiers.
- Hip sliding may be partly MM9's own: the Gezzampt's raw ABC slides its thighs 14 %. Not checked per body. Hip sliding on bodies built with mirror_source.py: Thrall 2.6-3.4 cm, Guard 1.8-2.5, Skeleton 3.1, Skeleton Warrior 2.3-4.8 (approved), Mummy 1.9. Limb lengths are fine on those. Honk male Calf 0.436-0.519 m and Lich limb joints (Resurrect) change by over 10 % by another cause, not traced. Rebuild or accept?
- Nosferatu accepted as built: no legs or feet, puffier sleeves.
- Clan Soldier rows carry MM9Axe at 100 % but the body has no throw clip: ranged plays Hattack2 from the sword. Data decision.
- Sleep: GUARD.abc has a `sleep` clip, dropped on install, and it is going back in on the third pass as a script clip. Only the Guard and Clan Soldier have one among the bodies checked. It plays only if a script asks for it. Kluso's House needs it: KlusosSleeper.scr loops `sleep` on 8 guards (UpperSleep0-7) from map start, waking when the Blackheart is taken or on damage; it is not tied to the window entry. The map has them `dormant`, with no sleep clip hooked up. Follow-up once the guard is in: a small actor behaviour in the map project looping the `sleep` script clip until woken. That is outside tonight's rules (no map projects, no game/ or engine/), so it waits for the user's word.
- Later polish on the Banshee (user accepted her, 2026-10-31): the head graft under the jaw, review/user_feedback_head_graft_20261031.png.
- Dropped clips (user, 2026-10-31: clips are basically free, and they are: all clips are 0.8-5 MB of a 17-63 MB GLB). Source vs installed counts: honk male and female 21/10, clansoldier 23/19, banshee 17/14, mummy 22/18, skeleton 17/15, zombie 18/16, troglodyte 18/16, gezzampt 17/15, highwayman 21/20, nobleman 15/14 (counts include a bind pose, and the installed count includes an added Dead). Follow-up after the quota resets: add the rest as script clips, no gate polish needed on clips nothing drives.
- 00:30: Ghost renderer limits. Blended limbs stay in their rest layer (arms wrong in 6-12 % of overlaps, worst 42 %; head 50-90 % when it flies low). A fix needs per-frame primitive centres or a blended depth prepass in the engine, which this run may not touch. Banshee and Spectre Dagrell are affected too. Blended geometry also casts no shadow.

## Finished bodies
(body, credits, gate numbers, sheet paths, viewer URL, what is unsure)

### mummy (23:50, 40 credits) — installed, bound, in overview, not called finished
- Gates: viewer 54 switches 0 errors; winding 0; flat 0.00; floor 3/3; regression 87 descriptors 0 failed; texture atlas 55.8/58.7 %, fragments 0.1/0.3 %, body spread 1.55 (over 1.3); arm/hand 0 over 1 cm in main clips; thigh through band 0 in Standing/Walking/Running.
- Open: collapse counts knee/hip/shoulder/strip Walking 3/4/2/8, Running 7/8/9/12, AttackMelee 2/5/22/35, Death 8/13/8/66, Wakeup hip 34 shoulder 43, Resurrect hip 80. Jitter 5 fails on corrected clips, up to 3.3 deg/f. Detached: 5-tri head island 6.8 mm in 4 of 920 poses.
- Per-tier images: 35.4 MB cooked (23.4 extra). Runtime binding confirmed.
- Orchestrator read the sheets (mm9_vs_ours, tiers, closeups 1+2, strips, ingame). Silhouette, clips, tier designs good. Seen: the thigh strip stands off as a stiff white sliver in sit, crouch and dead poses. `sheet_closeups.png` crops several subjects off; `sheet_closeups2.png` frames them properly. Strips are tier A only.
- Not checked: normal-speed playback, LOD1-3, Chasm itself, melee/cast FX, head and foot orientation per frame, tiers B/C strips, band against torso skin.
- Sheets: level_generation/creatures/mm9_mummy_claude/review/. Viewer: review/viewer/.

### guard (00:03, 35 credits) — installed, bound, in overview, not called finished
- Gates: thighs through skirt Walking 0/49, Running 0/25, Cower 49/125 at 1.9 cm; handedness true right; detached 0; flat 0.00; winding 0; floor 3/3; viewer 42 switches 0 errors; regression PASS 87 descriptors; atlas 57.4/57.8 %, stretch 1.11.
- Open: collapse armpit up to 58, fist 18-27 in every clip, groin/hem up to 21, head 15, knee 9, elbow 12. Arm/hand left 6.0 cm Death/Dead, 4.7 cm AttackMelee2. Halberd in body 5.9 cm Death, 1.6 cm AttackMelee. Jitter 2 fails in Death (shoulder 2.18 vs 2.0 mm/f2). LOD0 12,488 tris, no reduction tried.
- Per-tier images: 30.6 MB cooked vs 13.1 (Skeleton Warrior). Runtime binding confirmed. 10 credits wasted on a two-head upload that crossed the heads.
- Orchestrator read the sheets (mm9_vs_ours, tiers, closeups A, close_hands, strips A). Tiers and designs read well, faces good. Seen: fingers through the shaft (close_hands hB_1), hand lying beside the shaft rather than round it, tier A far brighter orange than MM9.
- Not checked: normal-speed playback, LOD1-3, tier B strips, Drangheim itself (save_game preparation fails on drangheim.odm), variant upload with one tier on a map, sounds, Town Guard rows 107/109 (same guard.abc, no descriptors).
- Full actors suite not finished on the final build. Last complete run one build earlier: 191 passed, 2 failed (out05_event_clearance_completes_from_monster_killed_hook, not a guard case; the other unidentified). To recheck at the end.

### honkmale + honkfemale (00:15, 10 credits tonight, 70 pair total) — installed, bound, in overview
- Gates male / female: boots through robe 0 / 0 in all ten clips; jitter 0 / 0; winding 0 / 0; flat 0.02 / 0.02; floor OK / OK; sleeve see-through 26 / 48 px of 160x160; forearm poke 0 / 0. Regression PASS 95 descriptors.
- Open: hands in body male Fidget L 5.8, Hit L 5.8, Death 3.5/4.5 cm; female Death R 5.3, Dead R 3.1, Hit L 2.2 cm. Finger stretch 3.67 / 4.97. Male atlas 50.1 % (target 55), head fragments 4.5 % (target 3). Symmetry p95 12.7 / 16.5 mm vs MM9 0.4 / 2.9. Collapse male Fidget elbow 27, armpit 23, neck 19, head 17; female Death elbow 28, Hit elbows 24, 20, robe 0. Detached audit flags both boots, by design.
- Orchestrator read compare, tiers, joints (both), male in-game. Silhouette and clips match MM9, in-game reads well. Seen on the female: hand through a gap in the robe at the waist in Dead, braid tip shards, ragged neckline. Seen on the male: corpse interior with a streaked cap, reddish Elder face. Strips, cuffs and per-tier close sheets not read by me.
- Not checked: playback by eye, egg release frame, foot sliding in game, LOD1-3, outdoor light (save_game preparation failed outdoors), hat assignment and Cast clip are a reading of the data.
- Sheets: each project's review/. Rebuild: v2/scripts/master_v3.sh.

### ghost (00:27, 40 credits) — installed, bound, in overview, short pass queued
- Gates: winding 0; jitter 0; arm/hand 0 frames over 1 cm; hand to sleeve within 5 mm; floor 3/3, hover 0.175 m; atlas 54.9/66.8 %, spread 1.04, stretch 1.06/1.10; flat 0.00/0.07 (robe grid); regression 95 descriptors 0 failed; viewer 39 switches 0 errors; in game isle and Verhoffin Ruins.
- Open: collapse Standing 20 and Fidget 20 robe_front (front tip doubled by the lining, sampled alpha 0), Fidget2 13 and AttackMelee 14 shoulder. Detached audit flags head (by design), both hands and a cuff: not confirmed either way. Numeric gates not rerun on the last two rebuilds.
- Orchestrator read mm9_vs_ours, in-game, see-through, close-ups, tier B, clips. See-through and motion good. Seen: hair not in MM9, blunt neck cap with smears, jaw scraps. Tiers A and C sheets not read closely.
- Not checked: LOD1-3 close up, playback, tier A/C strips, Specter's Dark Grasp and charge glow in game, finger blend order, water fog, Android, saves.

### zombie (00:30, 40 credits) — installed, bound, in overview, second pass running
- Gates: thighs through cloth Walking 0/53, Running 0/36; detached 0; flat 0.00-0.01; winding 0; floor 3 ok; regression PASS 95; viewer 0 errors; atlas body 40.5 % (unused torso charts, 56.9 % with them), head 60.0, torso 63.4.
- FAILED: arm/hand AttackMelee R 5.9 cm, L 3.4, AttackMelee2 L 3.1, AttackRanged L 1.3. Jitter 12 clips flagged, AttackMelee upper arm 6.6 deg/f from hand_rest.py.
- Open: collapse neck/head 28 Hit2, 19 Death, armpits 12, Wakeup groin 42 body 68. Wakeup thighs 20 cm (no behaviour drives it).
- Tiers: one torso part per tier, 6.3 MB of 18.7 MB cooked. Binding confirmed in the GLB and in game.
- Orchestrator read mm9_vs_ours, tiers, close-ups, mouth, strip_1, in-game. Faces and mouth good. Seen: tiger-stripe banding, pale knee blobs, Dripper hair as a paper collar, a stick mark on the chest in Hit. strip_2 and strip_3 not read by me.
- Not checked: LOD1-3, playback, Dripper and Zombie strips, throw_hand launch, Beethoven and Chasm placement, bloom, fullbrite in skins, ZOMBIEARM.abc use.

### mummy second pass (00:57, 0 credits) — closed after two serious attempts
- Fixed: thigh strip and arm spike lie on the skin, bending with the limb; detached 1 -> 0; soles 10 deg -> 0-2.6 mean; collapse AttackMelee shoulder 22/19 -> 7/16, strip 35 -> 6, Death strip 66 -> 13, Running knees and hips about 0, Walking knees 0. Exposed at worst frame AttackMelee 51 -> 20, Death 54 -> 24.
- Still failing: jitter 5 fails (upper arm 1.48, forearm 2.24 vs 1.0 deg/f). Arm gate worse in attacks: L 2.2 cm 4 frames, R 2.4 cm 2 frames (price of the softer correction). Band through torso AttackMelee 7/42 at 5.9 cm, AttackMelee2 5/37 at 9.4 cm. Resurrect hip 98 (script clip, nothing drives it). Head max 35.8 deg vs MM9 in AttackMelee2, attributed to easing, not isolated.
- Orchestrator read closeups2 and sheet_playback. Sliver gone, strips lie on the leg. A small dark tip remains at the thigh in crouch_knees. Band in strip_run hangs cleanly.
- Sheets also: sheet_strips_b/c, playback/*.webm. Not checked: motion by eye, Chasm itself, FX, sounds, LOD1-3, band loop seam, Android.

### skeleton (01:00, 40 credits) — installed, bound, in overview, ready for review, no second pass
- Gates: collapse body 0 in 15 clips, head 0 except Resurrect; thigh through cloth 0 in every bound clip; hands in bones Hit L 2.0 cm 1 frame, others under 1.1; winding 0; flat 0.00; floor ok on 5 bindings; regression PASS 95; viewer 60 switches 0 errors; atlas 57-61 %, head 68.6 %, stretch 1.24, fragments 3.1 % (target 3); handedness true, dagger in right hand.
- Open: jitter FAIL on shoulder excess against raw MM9 keys, same cause as the approved Skeleton Warrior (thin_keys), Running 20 mm/f2; hand acceleration near MM9 (AttackMelee R 224/187, Hit L 279/243, Death L 140/121). Detached: 4 of 173 flagged, L talus 10.1 mm, mandible 6.4, carpal 4.3, strip 4.1. No LOD3 (it lost the legs).
- Decision: no second pass. Its gates are the cleanest tonight, and its only failure matches the approved Skeleton Warrior.
- Rows 135, 192 scale 100, 184 scale 50 on skel_a; 183, 185 scale 50 on skel_r.
- Orchestrator read mm9_vs_ours, both tier sheets, poses close-ups, all-clip strip. Skull, teeth, ribs and joints look very good.
- Not checked: playback, red tier and row 192 in game, thrown axe and skull at the socket, melee timing, Fidget2/3, Taunt, Resurrect close-ups, LOD2 close, FPS with 37 Thrashers, foot slide.

Brief updated 01:02 with tonight's lessons, for bodies from thrall on.

### zombie second pass (01:45, 0 credits) — closed after two serious attempts
- Fixed: hands 0 frames over 1 cm in every bound clip (was R 5.9); jitter clips 12 -> 5, upper arm 6.6 -> 1.9 deg/f; armpits 12 -> 2; atlas 40.5 -> 57.5 %, density +19 %. The chest stick was MM9's stitched gash drawn long by Codex: painted out. Neck ring 16 -> 11.7 cm.
- Still failing: collapse neck/head 20 in Death (all exposed), body 20 in AttackMelee (was 9; 8 exposed). Jitter 5 clips (AttackMelee, AttackRanged2 R upper arm 1.9; Death, Resurrect, Wakeup flag floor raises). Cloth 0.2 cm over 7 frames in AttackMelee. Wakeup untreated (hand 5.8, thigh 19.9 cm, groin 42; script clip).
- Orchestrator read mm9_vs_ours, tiers, Beethoven in-game. Olive now reads closer. Bands and knees still strong in the viewer. Dripper keeps some neck flap. Beethoven is very dark, so it shows little of the model.
- Checked in game: placed Rotter fought in Beethoven; throw_hand release 1.3 cm from the fingers. Not checked: motion by eye, LOD1-3, Chasm, projectile flight, some B/C strips, bloom, fullbrite.

### ghost short pass (0 credits) — closed
- Corrected finding: MM9 DOES have hair on all three skins. My "hair not in MM9" note was wrong; the low-poly render reads bald because 256 texels blur it. Hair recoloured to MM9's values.
- Jaw scrap was blend order, not paint: reduced 256 -> 119 of 20,078 rays out of order. Neck is now a dark bowl. Detached flags on hands are audit confusion, confirmed on a welded test copy (review/gates/detached_welded.txt).
- Gates on the final build: winding 0, jitter 0, arm/hand 0 over 1 cm, floor 3/3, regression PASS 95, viewer 39 switches 0 errors, body atlas 54.4 % (target 55), head 66.8 %. Collapse unchanged: robe_front 20, shoulder 13-14.
- Orchestrator read tier A and close-ups. Collar reads well. Seen: pale flat shard at Shadow's wrist near the hip, cause unknown, in the overview for the user.
- Not checked: LOD1-3, Dark Grasp and charge glow in game, finger blend order, other blended effects, Android, saves.

### guard second pass (0 credits, total 35) — closed after two serious attempts
- Fixed: fist wraps the shaft (finger skin in shaft 0.1 cm in 13 clips, 0.5 Running); left hand Death/Dead 6.0 -> 1.0/0.3 cm; halberd in body Death/Dead 0; jitter 0 fails; fist folds 18-27 -> 3-11; groin 21 -> 7; head 15 -> 7; Cower armpits 51/35 -> 25/8; white fleck was a 19-edge hole, closed; tier A tunic (142,59,14) -> (102,42,10), MM9 (71,29,16); LOD0 12,488 -> 11,904.
- Still failing: AttackMelee2 L hand 4.0 cm in right forearm 3 frames; AttackMelee L hand 3.2 cm in hip 10 frames (worse than 2.6); armpits AttackMelee L 51, AttackMelee2 R 49 (2-3 exposed); Fidget2 L 2.4 cm; Cower thighs 36/125 at 1.2 cm.
- Regression: full actors suite 192 passed, 1 failed: out05_event_clearance, an MM8 case that cannot load under --world mm9, not this body. The second failure seen earlier is gone.
- Orchestrator read close_hands, tiers, in-game. Tier tone and in-game read well. Seen: fingers still read straight across the shaft in ahA_0 and chA_0, despite the wrap gate. Left for the user's eye after two attempts.
- Not checked: LOD1-3, webm by eye, indoors and Drangheim itself, tier B close-ups, neck close-ups in Cower and Dead, sustained combat.

### banshee (03:10, 35 credits) — installed, bound, in overview, second pass running
- Gates: winding 0; detached 0 visible; jitter 0 fails on 10 clips; regression PASS 98; floor 3/3 (Banshee added to HOVERERS in the shared floor_audit.py, one line); atlas body 57.5, head 69.2 %, fragments 0 / 1.6 %; LOD0 14,994.
- Open: Taunt R hand 5.9 cm 2 frames; with head Fidget2 3.9 cm 44 frames, AttackRanged 2.4/3.3, Death 1.5/1.7. Collapse wing 240 (doubled by lining), cape 100, neck 36, head 32, jaw 16, arms 1-11; true creases 21 of 456 edges. Blend order Skirt/Arm 9-18 %, Wing/Arm 17-19 %, Hair/Head 17-20 %, Death up to 82 %.
- Orchestrator read compare, in-game, head A, arms close-up, tier C strip. Silhouette and motion very good. Seen: mouth stretched in AttackRanged and AttackMelee, shard across the cheek in Hit, dark slashes in profile, saw-tooth throat seam, leopard-like sleeves.
- Not checked: indoors, fog, night, LOD1-3, corpse from above, loot drop, Android.

### honk second pass (0 credits, tonight 10, pair 70) — closed after two serious attempts
- Fixed: female Death R 5.3 -> 0, Dead R 3.1 -> 0 (cuff was buried in the belly; two constant arm leans); braid shards were paint, painted out; braids through robe 0 in Standing, Walking, AttackMelee, Dead; neckline repainted; cap plain; Elder R/G 1.65 -> 1.51 (MM9 1.39). Regression 101 descriptors, 0 failed.
- Still failing: braids Running 5/25, Fidget 43/193, Hit 11/44, AttackRanged and Cast 7/29, Death 26/73. Male hands Fidget L 5.8, Hit L 5.8, Death 3.5/4.5 cm. Collapse male Fidget elbow 27, female Death elbow 28, AttackRanged waist 27 (was 2). Symmetry; male atlas 50.1 %, fragments 4.5 %.
- Orchestrator read female joints and male in-game. The waist hole is gone. Seen: small dark specks on male robes in game, cause unconfirmed.
- Also seen in the male in-game sheet, right panel: a large flat grey disc at head height, probably the egg in flight (the agent reports one egg in that frame). In the overview for the user.
- Not checked: motion by eye, egg release in game, foot sliding, LOD1-3, outdoor light (save_game preparation fails outdoors).

### Machine load (04:20; 33 by 04:40 after the fix)
Load reached 312 on 32 cores. Cause: 14 orphaned headless Chromes from viewer_shots.mjs (parent gone, reparented to systemd --user), each rendering the viewer on the CPU, about 2,000 % in total. They leak when a wrapper's timeout kills node before its finally runs, and heavy load causes more timeouts. I verified each by its /tmp/openyamm-viewer-shots-* profile and its page URL, and stopped 11 by literal root PID: 7 on mummy and honk (agents finished, leases released) and 4 banshee ones 1h35 old. I left 3 banshee ones (11-13 min old), at first, then stopped those too once I confirmed their parent was systemd, so no script could still be driving them (my first check for leftovers had a bad pattern and wrongly showed none). 14 in all. Fix: viewer_shots.mjs now kills Chrome on SIGTERM/SIGINT/SIGHUP. Brief: at most 2 shot scripts at once, and no Chrome left behind.

### banshee second pass (0 credits, total 35) — closed after two serious attempts
- Fixed: jaw one hinge, 34 -> 23.6 deg; jaw edges AttackMelee p99 18.9 -> 3.44, max 29 -> 7.15; head opaque (the cheek shard and profile slashes were blend order, not paint, as on the Ghost); throat stripes were degenerate UVs on the stitch strip, rebuilt, neck is its own blended primitive; sleeves softened toward MM9's gold-brown; Fidget2 by one smooth rotation.
- Still failing: stretch max 7.15x at the jaw angle vs MM9 1.83; outer cheek p95 2.05 vs 1.66. Hands Taunt 5.9 cm (hand past hand, MM9's gesture, 15-19 cm clear of the torso), Fidget2 2.9 cm 47 frames, AttackRanged 2.4/3.2, Death 1.5/1.7. Blend Wing/Arm 17-20 %, Skirt/Arm 9-18 %, Death up to 82 %. Collapse Hit neck 36, AttackMelee head 28.
- Regression PASS 107 descriptors, 0 refused; floor 3/3; detached 0; jitter 0.
- Orchestrator read head A and arms. The mouth now reads as a real scream, and the head is clean. Sleeves are much closer to MM9. Seen: black curves beside the neck and a black mark at the throat in Taunt.
- Not checked: indoors, fog, night, LOD1-3, point-blank camera, corpse from above, loot, Android, head shadow at a low sun.

### thrall (04:40, 40 credits) — installed, bound, in overview, ready for review; second attempt done by the agent itself
- Gates: thighs through skirt Walking 0/66, Running 0/50, AttackMelee 0.3 cm 3 frames, Death 0.2 cm 1 frame; hands against skin 0 over 1 cm in bound clips; jitter 0; detached 0; winding 0; flat 0.00; floor 3 ok; soles under 1.2 deg; head mean under 2.4 deg; atlas 60.8/56.2/63.3 %; regression PASS 107; full suite 192 passed, out05 failed (not thrall).
- Failed: hands through loose skirt flaps Walking R 1.6 cm, Hit L 4.6, Hit R 2.3, Death R 2.0. Collapse knee 2-4, armpit 5-13, neck/head 33 (AttackMelee2, Death2, 18 exposed).
- Script clips: Fidget2 L 5.8 cm, Death2 L 6.0 cm, thighs Hit2 3.0, Death2 15.1 cm. Not traced whether anything plays them.
- Orchestrator read tiers vs MM9, closeups B, strips A1. A very close match to MM9, with clean joints. Skirt points read as shards up close in the corpse.
- Not checked: Sturmford, Drangheim, Lindisfarne, indoor light, knife leaving the hand, melee timing, sounds, LOD1-3, motion by eye, Android.

### Shared bugs found by the Evil Sorcerer agent (05:20)
- mirror_source.py breaks limb lengths on an asymmetric bind. New tool claude_shared/bone_length_audit.py measured installed GLBs: Highwayman is bad (Foot 0.28-0.53 m, Calf 0.32-0.50 m): its agent told to fix at the source. Hips slide on others (see open decisions). Evil Sorcerer, Zombie, Imp, Troglodyte, Honk female: 0 joints over 10 %. Banshee and Ghost not measured.
- The cat's and mummy's collapse_gate.py read only primitive 0. I reran the Mummy with the all-primitive gate on the final GLB: the numbers match its report, so they stand. Nosferatu was told; the others already read every primitive.

### evilsorcerer (05:15, 30 credits) — installed, bound, in overview, ready for review
- Gates: legs through panels Walking 0/58, Running 0/34; arm gate 0 in Standing, Walking, Running, Fidget, Taunt, AttackMelee, Hit, Dead; jitter 0; winding 0; flat 0.01; floor 3 ok; atlas 58.5/55.7/60.3 %; detached 1 flag (1 cm, 1 of 861 poses); regression PASS 110; viewer 54 switches 0 errors. GPU about 20.3 MB estimated vs 29.4 for three full paints.
- Failed after two passes: Fidget2 L 4.9, R 4.0 cm (about 50 frames); AttackRanged2 and ResurrectSpell L 4.3; Death R 2.6, forearm 3.4; AttackRanged L 2.0; Backpedal L 5.7 (1 frame). Death panels 4.2 cm through legs 6/58. Collapse armpits up to 30/21 in Death.
- Orchestrator read compare, tiers, joints B. A very strong result. Seen: trim and red brighter than MM9, red bleeding on the grey calf, pale groin patches.
- Not checked: motion by eye, LOD1-3, indoors, placing maps, corpse in game, dots FX, sounds, Android, saves.

### troglodyte (05:20, 40 credits) — installed, bound, in overview, ready for review
- Gates: collapse knees up to 11, groin 2, elbows 0-2; jitter only Death; detached 0; floor 3/3; winding 0; flat 0.03; regression PASS 110; atlas 56.9/66.5 %.
- Failed after two attempts: AttackMelee2 L hand 3.1 cm 1 frame, forearm 3.3; AttackMelee L 2.2, R forearm 2.4; AttackRanged R forearm 2.0; armpit Hit 31 (18 seen); neck up to 96 (56 seen); head into chest 5.0 cm. Leg in tail root 4.0-4.8 cm, 1-3 vertices. Body spread 1.47.
- Orchestrator read tiers, MM9 vs ours B, close-ups B. Mouth and head excellent. Seen: strong arm netting, heavier chin.
- Not checked: motion by eye, mines light, missile FX, script clips in game, head and foot orientation gate, LOD1-3, Android.

### highwayman (05:35, 40 credits) — installed, bound, in overview, ready for review
- Bone audit fixed at the source: mirror_glb.py + rerest.py, 0 of 12 stretching (was 4). HIGHWAYMAN.abc has 9 clips, the other 12 are in child FIGHTERBASE.abc, merged; DOOKMILITIA.abc and PHANTOM.abc link it too.
- Gates: thighs Walking 0/53, Running 0/20; arm/hand under 1 cm; jitter 0; grip inside 0.3 cm max, wrap 150 min / 195 median deg; blades under 1 cm; detached 0; flat 0.00; winding 0; atlas 58.7/57.6/65.1 %; viewer 60 switches 0 errors.
- Failed: floor Running -2.7 vs tolerance 2.5. Binding regression red only on MM9 Ghoul B (no cast clip, ghoul agent told). JumpingDown 13 cm thighs (script clip). Collapse armpit 43, neck/head 45 in Death and Dead (24 exposed).
- Orchestrator read compare, hands, heads. Grips are real, faces strong. Best held weapon tonight. Seen: ragged cuff edge, busy bracers.
- Not checked: LOD1-3, motion by eye, thrown dagger in game, placing map, full suite, tier B close-ups, Android. A magenta fleck on the ground in game is unidentified.

### ghoul (06:35, 30 credits) — installed, bound, in overview, ready for review
- Gates: cloth Walking 0/53, Running 0/33; bone audit 0 of 12; detached 0; winding 0; flat 0.01; atlas 58.6/61.0 %, fragments 0.2/2.9 %; regression PASS r16; validator 119 descriptors 0 refused; viewer 48 switches 0 errors; arms only Death L 1.0 cm 1 frame; collapse knees 2, elbows 5, armpits 15.
- Failed after a second attempt: cloth Fidget 1.1 cm 60/194, Death 1.1 cm 13/73. Jitter Death L, Death2 L/R, up to 1.65 deg/f. Collapse Running back flap 24, thumb roots 20 (37 exposed), Death hair 71 (1 exposed).
- One shared texture set, no per-tier images: the first tonight to meet the rule in full.
- Found clips_mm9.py stretching a moved hip by 19 %: this may explain the hip sliding on other bodies. ORBIT in its copy fixes it. Added to the brief.
- Orchestrator read compare, close-ups A. Joints very clean. Tone much lighter and yellower than MM9.
- Not checked: LOD1-3, a real map, projectile flight, bloom, Android, motion by eye. Spawned actors killed in game vanish and leave a bag, also on the Zombie, so corpses were not seen in game.

### gezzampt (06:56, 20 credits) — installed, bound, in overview, ready for review
- Gates: hands 0.0 cm in 15 clips; jitter 0; bone length 0 (raw ABC slides its thighs 14 %, joints held fixed); handedness true; detached 0; flat 0.00; winding 0; floor 3 ok on r11; atlas 61.3/60.0 %, fragments 0; regression passed on r10, 119 descriptors. 10,152 tris. Cooked 11.6 MB, one shared set.
- Not clean: collapse Death2 head 93, AttackMelee head 32, shoulder 18, Fidget2 head 34, shoulder 21; at most 32 exposed. Collapse, hands, jitter, orientation last run on r9; r10 and r11 changed tier C ramps and the Walking floor only. Regression not rerun on r11.
- Orchestrator read tiers vs MM9 and mouth/neck. Faces very strong. Seen: brighter and more saturated than MM9. mm9_vs_ours_tiers crops our head off the top.
- Not checked: placing maps, indoor light, motion by eye, melee contact, sounds, LOD1-3, full suite, Android.

### nosferatu (08:05, 20 credits) — installed, bound, in overview, ready for review
- Gates: through cloth 0 for hands and sleeves; jitter 0; bone audit 0; detached 0; flat 0.02; winding 0; floor 3 ok; regression PASS 125 on r10; viewer 51 switches 0 errors; atlas 62.1/55.1 %; cooked 8.2 MB. Mouth rigid, 0.0 % stretch.
- Failed: collapse AttackRanged shoulder 25/25 (22 exposed), Dead robe 141 (70 exposed, flat on the floor), Death2 neck 44. Hands AttackRanged L 2.1, R forearm 4.9 cm, Fidget L 1.2, Taunt L 1.4.
- Monk's kill of strips.sh c repaired: rerun on r12.
- Orchestrator read compare and heads. Very strong. Seen: puffy sleeves against MM9's flared cuffs.
- Not checked: motion by eye, LOD1-3, placing maps, indoor light, projectile, FPS at 110 joints, FX, tier B close-ups on r12, Android.

### dookmilitia stall (08:20)
The first agent stopped working at 06:34 (no file changes, no processes, no answer to a message for 20 minutes) though it showed as running. I stopped it and started a fresh agent on the same project and lease, 0 more credits. Nothing was installed yet.

### monk (08:20, 20 credits) — installed, bound, in overview, ready for review
- Gates: legs through robe 0 in all 35 clips; jitter 0; hands 0 in Walking, Running, Backpedal, Dead; winding 0; flat 0.00; floor 3 ok; atlas 61.8/61.6 %; regression PASS 125 at r9; suite 192 passed, out05 failed (known); viewer 105 switches 0 errors. 14,285 tris, 116 joints, GPU about 17.7 MB (estimate).
- Not clean: AttackRanged3 L 2.2 cm 3 frames, Pray 2.0 cm (palms); cords through robe Pray 4.3, Cower 2.6, Dead 1.3 cm; finger stretch 3.63; collapse neck 42 Death2, 62 SweepFidget, robe 35 corpse; detached flags both soles up to 7.9 cm (legs hang free, as in MM9).
- Bone audit reads Calf 0.37-0.51 m: MM9 has no thigh bone, this is its keyed Spine-to-knee distance, not a stretch of ours.
- Rule break: it killed the Nosferatu agent's strips.sh c. Repaired by that agent. Rule now in the brief.
- Orchestrator read compare, joints A. Joints clean, faces strong. Seen: bulkier shoulders, smaller hood, harsher faces.
- Not checked: motion by eye, attacks and corpse in game, LOD1-3, Lindisfarne, indoor light, sounds, FX, Android, saves. Strips are from r11, chin fix r13 seen only in sheet_chin.

### clansoldier (08:30, 40 credits) — installed, bound, in overview, ready for review
- Gates: bone audit 0; handedness true; thighs Walking 0/44, Running 0/25, Dead 0; jitter 0; grip 0.0 cm, wrap 105-195 deg; detached 0; flat 0.00-0.01; winding 0; floor 0 of 3 flagged; viewer 57 switches 0 errors; regression PASS 125.
- Misses: skirt Death 9.7 cm 30 frames, Death2 6.5, Cower 12; Sleep R hand 5.0, sword into head Sleep 4.2, Cower 6.0 (script clips); shield Death 4.0 cm into the thigh. Collapse elbow 35, armpit 12, groin 16, neck 73 (Death).
- Orchestrator read compare and heads. Rich costumes, strong faces. Seen: nasal plate.
- Not checked: motion by eye, LOD1-3, missile flight, sounds, placing map, full suite, Android, Leader's thigh patch from behind. Most sheets are r16 (nasal paint differs on r18).

### nobleman (40 credits) — installed, bound, in overview, ready for review
- Gates: bone audit 0; thigh through skirt 0 in all 14 clips; detached 0; flat 0.00; winding 0; floor ok; atlas 57.0/56.4/56.7 %; validator 131 descriptors 0 refused; binding regression passed; collapse knees and hips at most 2, Walking 113 face-frames (was 1,874).
- Open: Hit2 R hand 3.7 cm (script clip); jitter 3 flags; shoulders 76 Death2, 38 Death, 33 AttackMelee, mostly visible; groin up to 29 in the attacks; finger stretch 3.52. MM9's raw thighs slide 10-13 %, so that is native. Thighs hang from Spine, not Pelvis, on this body.
- Orchestrator read the full-size heads sheet only (quota).
- Not checked: LOD1-3, placing map, variant upload, motion by eye, corpse in game, melee timing, sounds, Android.

### honk third pass (0 credits) — hands, both bodies
- Cause: the hand graft was short and bent at the wrist in the bind, the forearm tube thin and short, the cuff off line. Pass-2 leans were not the cause.
- Female: hand 12.7 -> 16.5 cm (MM9 16.8), Standing wrist 22.4/20.8 -> 4.7/9.1 (MM9 5.0/9.3). Hands clear in every clip except Fidget L 0.9. Sleeve gate 21 -> 29 px.
- Male: hand 16.2 -> 18.5 (MM9 17.9). Arm gate worse: Standing L 2.7, R 2.5 cm (maybe false), Fidget L 5.4, Hit L 4.0, Death R 4.8. Sleeve 26 -> 55 px. Left cuff offset 0.6 -> 3.9 cm. Fix to try: constant upper-arm lean. Stopped at one gate run on instruction.
- Both: jitter 0, robe gate 0, regression passes, winding 0. Dark lines on robes: lining edges cross the wall, when they began is not checked.
- Not checked: forearm-to-hand join close up, floor audit, standard sheets, viewer check, in-game.

### gezzampt head fix (0 credits)
Cause: the projection fitted each Codex view to the clay by silhouette box, moving features about 4 cm above the real eyes and teeth, which eyes.py then painted again. Fix: front view placed by measured landmarks. r12 installed, regression 140 descriptors 0 failed, winding 0, bone 0. Most sheets are stale; use review/sheet_head_r12.png.

### dwarf (09:45, 20 credits) — installed, bound, in overview, ready for review
- Gates: thighs Walking 0/50, Running 0/31; hands at most 1.1 cm in bound clips; jitter 0; grip 0.3 cm; bone audit 0; detached 0; winding 0; floor ok; atlas 57/55/64 %; binding regression PASS.
- Open: axe in upper arm 6 cm+ in Fidget, helmet rim in shoulders up to 6 cm+, collapse elbows 41, shoulders 46, neck 45. Script clips Fidget2 3.5, Search 4.2 cm, Death2 thighs 5.0.
- Rule break: rm with a wildcard on its own review/ingame screenshots (regenerated); rebuild.sh inherits an rm with a variable.
- Quota: it stopped polishing on the 91 % message; clip gates are r10, head and ramps later. In game ran on r8.
- Orchestrator read sheet_faces_front only.

### trellborg (40 credits) — installed, bound, in overview, ready for review
- Gates: arm/hand 0 except Fidget2; club 0 except Fidget2 5.7 cm; jitter 0 (before helpers); bone 0; detached 0; flat 0.00; winding 0; floor 3 ok; atlas 59.8/55.8 %; validator 0 refused; binding regression PASS; faces one of each, front on.
- Open: Fidget2 L 6.0, R 2.0, forearm 4.0 cm (script clip); collapse shoulder 12-25, wrist 11, head 12; wrist stretch 4.03. Club position drifts maybe 20 cm against MM9, not measured.
- Not checked: tone vs MM9 by tier, tier B close-ups, playback, LOD1-3, real maps, ranged release, sounds, Android, cooked size, most strips.
- Orchestrator read sheet_heads_front only.

### dookmilitia (Half-Orc, 40 credits) — installed, bound, in overview, ready for review, not finished
- Gates: bone 0; handedness true; jitter 0; cloth Walking 0/53, Running 0/20; grip 0.5 cm, wrap 150-225 deg; flat 0.00-0.01; winding 0; viewer 63 switches 0 errors; binding regression PASS 140. Heads checked: one nose, one beard.
- Failed: detached right cheek bar 5.0 cm in 29/706 poses; Cower hilt through the head 5.6 cm, cloth 1.1 cm; arm Cower R 2.5, Sleep R 1.6, Death L 1.6, Dead L 1.5; floor Running -4.5 vs 2.5. Collapse neck and head 45-65, shoulders 53.
- Not checked: in game at all, strips, final close-ups, hands sheet, playback, LOD1-3.
- Orchestrator read mm9_vs_ours only.

### clansoldier fix (0 credits, r22)
Shield inner plate was wound wrongly; waist gap closed by lapping the sash over the skirt; skirt hangs, hinge lift capped at 45 deg, lit lining per tier. Trade: thighs through skirt Walking 1.4 cm 18/44, Running 4.0 cm 18/25, Backpedal 1.4, Cower 5.0, Death 7.5, Death2 6.3, Dead 2.1. Regression PASS 140. Other gates and older sheets not rerun on r22.

### lizardorc (30 credits) — installed, bound, in overview, NOT finished
- Passed: validator 143 descriptors 0 refused; bone 0 of 20; winding 0; flat 0.00; grip 0.0 cm; jitter only Death; atlas 58.7/61.8 %; viewer 0 failed on r6.
- Failed: plates in legs every frame, Walking flap 2.2, inner 5.9, tassets 5.0 cm; Running 3.4, 7.0, 6.1; skirt gate Walking 3.6, Running 8.9. Floor AttackMelee -9.5 vs 2.5, cause not traced. Arms Fidget2 3.5, Death2 forearm 3.7; thumb wrap 15 deg; neck sliver; 7 pauldron spikes detached up to 4.6 cm in 2/528; collapse head 93 Death, torso 55.
- Stopped on the 91 % message. Gates are r5-r6, only the neck ring moved after.
- Not checked: playback, LOD1-3, placing maps, corpse, attack contact, missile, sounds, full suite, Android, strips, tier compare by eye.
- Orchestrator read mm9_vs_ours only.

### guard third pass (0 credits, total 35)
Cause confirmed: project_heads.py had no occlusion, and its helmet mask was hole-filled; the mesh has one slot where MM9 has a T opening with an eye mask. Layered paint with a z-buffer; eye mask and cheek returns are real plates (mm9_guard_plate_a.glb 323 tris, _c.glb 456). Six clips added to script_clips including sleep. Skirt Walking 0/49, Running 0/25; jitter 0; detached 0; floor 3/3; winding 0; viewer 60 switches 0 errors; full suite 192 passed, out05 failed (known). The missing .oytex seen by the troglodyte agent was the guard mid-rebuild.
Open: eye-window corners on B/C, cheek plate streaks, painted outline on steel cheek, chin patch; fist not refined (wrap 135-195 deg); AttackMelee2 4.0, AttackMelee 3.2 cm. Regression and strips ran before the last texture and plate rebuild.

### nobleman head fix (0 credits, r16)
Cause: silhouette box fit, chin error 23/70/50 px. Front view placed by landmarks with a thin-plate warp, face from the front view only, neck plain, head normals rebuilt. Validator 143 descriptors 0 refused, binding PASS, winding 0. New marks: forehead crease, jaw corner nicks. Not repeated: in-game, strips, viewer check.

### bigfoot (20 credits) — installed, bound, in overview, NOT finished
- Passed: detached 0, flat 0.00, winding 0, bone 0 of 12 (raw and final), handedness true, floor 3 ok, binding PASS on r5, viewer 0 failed on r6, faces one of each.
- Failed: arm Fidget R 3 cm 77 f, Fidget2 L 6 cm 59 f, Taunt 6 cm 8 f, AttackMelee 6 cm 2 f, AttackMelee2/Ranged 6 cm 13 f, Hit2 R 6 cm 9 f, Death2 R 5.9 cm 8 f; jitter 19 flags in 10 clips, worst 21.09 mm/f2; collapse Hit2 head 40, AttackMelee shoulder 22. Atlas 53.9/49.8 %.
- Orchestrator read mm9_vs_ours_tiers only.

## Follow-up session (2026-11-01 evening, user review)
- lichking r19 (staff in the palm; user: "the staff placement needs maybe to be put better to the palm?"): staff seated 2.15 cm into the hand, fist solved on the skin, thumb across the shaft's front, Hit head turn 20 deg. Palm gap 2.06 -> 0.44 cm, fingertips 72 -> 129 deg round the shaft. Regression PASS (158/65). 0 credits. **User: "lich king ok" (r19).** Overview updated.
- giant (user: pinky not holding the hammer on either hand): cause = the MPFB pinky rests curled with its skin inside the shaft and the solves could only close joints, so the one clear pose threw it past the shaft. fist_giant.py pad solve (joints may open), grip_gate.py per-finger pad gaps. In progress (r23).
- ebora (user: mouth too thin, nose too tall/thin; ear paint on the hair): worker stopped by the API limit mid-iteration, nothing installed (17:14 build live, regression PASS on it). Lease kept for resume.
- giant r23 installed (pinky grip): worst pad gap R 1.72 -> 0.28 cm, L 1.45 -> 0.27 cm; fingertips 127-173 deg round the shaft; Fidget L hand out of the body; jitter 6 -> 5. Regression binding PASS 158/65 (suite: only out05, known). 0 credits. Lease released. Open: corpse mallet 4.2 cm, AttackMelee windup L fingers, tier B steel.
- User, 2026-11-01 ~20:40: 15 more actors, max 5 agents at a time: 10 peasant bodies (M2, M1, M1d, F8, M7, HOM1, F1, F5, DM1, DM2) + Kira, Bjarni, Tryggva, Sven, Markel. **Meshy budget for the batch: 1000 credits** (backup 3740 -> floor 2740), max 60 per body. Brief: TOWNSFOLK_BRIEF.md. Scheduled to start 22:27 after the API limit reset, with the Ebora resume (4 townsfolk + Ebora, then 5).
- **User: "OK giant ok, lesser demon aswell i think"** (2026-11-01 evening): giant approved at r23; Lesser Demon approved as installed (r10). The unfinished neck pass (`mm9_stage1demon_claude/scripts/neck_pass.sh`, work/uv_v4.blend, never installed) is dropped. Overview updated.
- 20:5x: the 22:27 schedule was cancelled; the Ebora agent resumed fine and wave 1 started at once (peasantm2, peasantm1, peasantm1d, peasantf8 + ebora = 5). peasantm7 starts when the first one finishes.
- ebora Head fixes 3 installed (sha f141099bc209): face_shape.py (mouth 2x wider, fuller lips, nose broader/shorter), side locks relabelled hair, red paint refused on hair; gates identical to baseline, regression PASS 158/65; 0 credits. Orchestrator read sheet_face_compare and sheet_head_sides: clear step towards the master, no skin on the hair. Seen: s1 neck seam, s1/s2 hairline notch. peasantm7 started in the freed slot.
- **Townsfolk: PeasantM1d done** (`mm9_peasantm1d_claude`, rows 22/28): installed, descriptors `MM9 22 Commoner` / `MM9 28 Prisoner`,
  25 credits, gates green except MM9's own hand-on-chin contacts (Conv1 L 3.1 cm, Conv5 L 1.8 cm), binding test PASS. Not visible in
  game: the maps still place the legacy stand-ins (340/342) via `transcode_mm9_dat_to_odm.py`; one transcoder switch + map
  regeneration for every townsfolk row (and Annud's 54) is left for after the batch. Orchestrator read sheet_mm9_vs_ours, sheet_tiers,
  face_closeup: jagged pale band under the fringe on both tiers. Brief gained "Lessons from wave 1" (placement is orchestrator's;
  fringe edge check); running wave-1 agents were told. Overview card added (open). Backup balance 3585 after wave 1 so far.
  PeasantHOM1 (wave 2, half-orc skeleton) started in the freed slot.
- **Townsfolk: PeasantF8 done** (`mm9_peasantf8_claude`, rows 15/16/21): installed, `MM9 15/16 Commoner`, `MM9 21 Prisoner`, 35 credits,
  all gates clean (legs free inside the skirt by design), binding test PASS; peasantfemale retarget reusable (`ALL=1 scripts/pf_roles.py`).
  Orchestrator read sheet_mm9_vs_ours, sheet_tiers, shots/f9a_hf: close match; greyish chin shadow on both faces, flat procedural
  ears, yellow inner scarf band. Overview card added (open). PeasantF1 started (told to start from F8's retarget).
- **Townsfolk: PeasantM1 done** (`mm9_peasantm1_claude`, rows 43/56/296): installed, 35 credits (second head paint for the blond
  prisoner tier), binding test PASS. Flags: four upper-arm jitter flags from the hand push (Conv5 L +3.44 deg/f), Conv5 L hand 1.9 cm,
  Fidget forearm 6 cm behind jacket flap. Orchestrator read sheet_mm9_vs_ours, sheet_heads, sheet_faces_closeup: good match; squinty
  eyes with a dark socket band close up. Overview card added (open). PeasantF5 started.
- **Townsfolk: PeasantM7 done** (`mm9_peasantm7_claude`, rows 51/53): installed, 25 credits, binding test PASS; fringe band found and
  fixed (`scripts/fringe_fix.py`). Flags: Conv1/Conv5 left hand under the tunic skirt (5.9/5.6 cm) and narrow jitter fails (1.41/1.19).
  Orchestrator read sheet_mm9_vs_ours, sheet_heads: close match; row 53 keeps row 51's face. Overview card added (open).
  PeasantDM1 started (dwarf skeleton; DM2 waits for its retarget).
- **Ebora accepted** by the user ("ebora - accepted", Head fixes 3). Same note: the Concubine (s1, pale skin, copper hair) "has ugly
  face + there are some spaces in the hair? like holes?" (screenshots in `mm9_ebora_claude/review/user_notes/`). A fix agent started
  (lease owner concubine-face-fix, max 15 credits): close the hair holes/loose strands/dark slivers, repaint the s1 face calm and
  symmetric, fix the neck seam; Ebora's own look must stay unchanged. Overview card stays open until the Concubine is done.
- **PeasantM1 user note:** "looks like he has 2 eyebrows? and like weird eye area?". Orchestrator read review/brow_fix.png: the light
  band between brows and eyes is outlined like a second brow pair, eyes sunken slits (B red-rimmed), flat skin panel under the jaw.
  Sent back to the PeasantM1 agent (resumed with its context; lease budget 10, prefer 0 credits).
- **PeasantM7 user note:** "hands sticking through the sleeves" (screenshot `mm9_peasantm7_claude/review/user_notes/wrist_pokethrough.png`):
  skin wedges through the sleeve above both cuffs; also blotchy hands, dark nails. Sent back to the PeasantM7 agent (budget 10).
- **Townsfolk: PeasantM2 done** (`mm9_peasantm2_claude`, rows 44/50): installed, 35 credits (head paint per tier), jitter 0 fails,
  binding test PASS. Flags: Fidget R fingers 5.3 cm in hair, Conv1 L 6.0 cm on belly (kept, jitter). Orchestrator read
  sheet_mm9_vs_ours, sheet_heads, sheet_hands: strong match, good faces. Overview card added (open).
  Kira (wave 3, unique, shield) started; DM2 waits for DM1's dwarf retarget.
- **PeasantM7 sleeves fixed** (0 credits, rollback `work/rollback_v1/`): forearm stub tucked inside the sleeve (`sleeve_tuck.py`),
  skin paint on the cuff cloth repainted, hands one clean skin colour; new `sleeve_poke_gate.py` 0 mm in all 13 clips; other gates
  unchanged, binding test PASS. Orchestrator read sheet_wrist_before_after_R and sheet_hands_closeup_viewer: clean.
- **Townsfolk: PeasantHOM1 done** (`mm9_peasanthom1_claude`, rows 57/58/60): installed on MM9's half-orc skeleton (11 clips, all used),
  25 credits, all gates pass, binding test PASS. Orchestrator read sheet_mm9_vs_ours, face_closeup, cuff_fix: strong match; the cuff
  skin flare is the same fault the user flagged on M7, so the agent was sent M7's sleeve_tuck/paint/gate scripts (budget 5).
  Overview card added (open). Backup balance 3430.
- **PeasantM1 eyes fixed** (r16, 0 credits, one Codex run, rollback r7): Meshy's recessed eye plate smoothed (`eye_relax.py`), eye area
  repainted by Codex and projected back. Orchestrator read sheet_facefix_blender/viewer: one brow pair, open eyes, good. neck_facefix
  still shows a straight head/body seam with a tone step and a hard-edged skin bib: sent back for the neck (0 credits).
- **Townsfolk: PeasantF1 built** (`mm9_peasantf1_claude`, rows 29/33): installed, 35 credits, all gates clean (incl. sleeve gate),
  binding test PASS. Orchestrator read sheet_mm9_vs_ours and sheet_faces: body and tiers good, faces not acceptable (swollen
  too-wide pout, staring eyes, shopkeeper not elderly vs MM9's broad smiles): sent back for a Codex face repaint (0 credits).
  Overview card added (open, rework pending).
- **PeasantM1 neck fixed** (r17, 0 credits, rollback r16): body-texture neck/chest paint continues the head's neck skin
  (`fix_seam.py`, own skin region per tier), lower neck tone-matched. Orchestrator read sheet_neckfix: continuous skin, rust patch gone.
  Full actors suite not re-run on r17 (binding test PASS).
- **Townsfolk: PeasantDM1 done** (`mm9_peasantdm1_claude`, rows 8/13/14): dwarf townsfolk skeleton retargeted (reusable), 35 credits,
  gates pass except a few sleeve-gate vertices in hard wrist bends (renders clean), binding test PASS. Orchestrator read
  sheet_mm9_vs_ours, sheet_heads, poke_check: strong match, good faces, clean wrists. Overview card added (open). PeasantDM2 started.
- **Townsfolk: PeasantF5 built** (`mm9_peasantf5_claude`, rows 34/36/41; only 36 is placed, 6x): 35 credits, all gates clean,
  binding test PASS. Orchestrator read sheet_mm9_vs_ours, faces_final: body good, faces not acceptable (pout, angry brows, glare):
  sent back for mouth flatten + Codex repaint (0 credits). Overview card added (open, rework pending).
- **PeasantHOM1 sleeves fixed** (0 credits, rollback `work/rollback_v1/`): cuff rims trimmed (`cuff_fix.py`), M7's sleeve_tuck/paint
  fix/hand_clean applied, four Meshy sleeve holes filled (`sleeve_holes.py`); sleeve gate max 0.2 mm; full actors suite 192/1 (out05).
  Orchestrator read sheet_wrist_before_after_R, sleeve_marks_before_after: flare gone, holes closed; rims still a little jagged.
- **Unique: Kira done** (`mm9_kira_claude`, row 251): own skeleton, all script clips + a built Death, metal PBR, 25 credits, gates
  pass, binding test PASS. No shield: KIRASHIELD is the quest item lying in Thronheim (decoration mm9_kirashield), never attached
  in MM9 (agent's call, reasonable). Orchestrator read sheet_mm9_vs_ours, sheet_head: close match; face paler/more neutral than
  MM9's. Overview card added (open). Markel (last body) started.
- **Concubine fixed** (`mm9_ebora_claude`, 0 Meshy credits, one Codex run, rollback `work/installed_hf3.glb`): back faces on every
  visible single-sided hair face (`hair_backs.py`, +733 tris), s1 face repainted calm/symmetric, chin patch and neck seam cleaned;
  Ebora's face pixel-identical. Orchestrator read sheet_cf_s1_before_after and sheet_cf_sirens: holes gone, face much better; faint
  neck zigzag, chin wedge from below, s2 olive jaw remain. Overview card updated (open for the Concubine review).
- **PeasantF1 faces repainted** (r21, 0 Meshy credits, rollback r12): Codex repaint per woman, lips/chin smoothed, cheek holes closed,
  collar edge cleaned. Orchestrator read sheet_faces_before_after: pout gone, warm closed smiles; shopkeeper still slimmer than MM9's,
  faint pale streak on B's left cheek. Ready for user review.
- **PeasantF5 faces redone** (r17, 0 Meshy credits, one Codex run, rollback r13): lips flush, creases/nostrils softened, Codex repaint.
  Orchestrator read sheet_faces_after: pout and glare gone; dark spot under the nose and slightly wide eyes remain. Ready for review.
- **Unique: Bjarni done** (`mm9_bjarni_claude`, row 246): PeasantMale skeleton + his own Argument cutscene clips, 25 credits, gates
  pass (Fidget R 2.9 cm into the beard, Applause hands meet), full suite 192/1. Orchestrator read sheet_mm9_vs_ours,
  sheet_face_closeup: close match, good face. Notes for later: the two "Kira0" corpse props (Afterworld, Yorwick) use bjarni.abc;
  the sitting props are the existing low-poly decoration `mm9_bjarnisitting`. Overview card added (open).
- **Unique: Tryggva done** (`mm9_tryggva_claude`, row 250): PeasantMale skeleton + Sit/Agree/Applause/corpse from his file, 25 credits,
  gates pass except Applause hands 2 cm and body atlas 50.9 % (soft target 55), full suite 192/1. Orchestrator read
  sheet_mm9_vs_ours, sheet_face_final: good body; face fine at party distance, nostril hook and crooked mouth close up. Overview card
  added (open). Backup balance 3295.
- **Unique: Sven done** (`mm9_sven_claude`, row 249; SVEN_ARG covered by its clips): 25 credits, Codex face repaint, all gates pass,
  full suite 192/1. Orchestrator read sheet_mm9_vs_ours, sheet_face4: close match, warm face. Overview card added (open).
- **Townsfolk: PeasantDM2 built** (`mm9_peasantdm2_claude`, row 9): DM1's retarget reused, 35 credits, all gates pass, full suite
  192/1. Orchestrator read sheet_mm9_vs_ours, sheet_faces_vs_mm9: body good; face reads as a mask (ruddy face vs pale scalp), small
  frowning eyes, near-white hands: sent back (0 credits). Overview card added (open, rework pending).
- **Unique: Markel built** (`mm9_markel_claude`, row 248): PeasantMale skeleton + his cutscene clips, 25 credits, gates pass except
  capped cutscene hand contacts, full suite 192/1. Orchestrator read sheet_mm9_vs_ours, sheet_face_mm9_vs_ours: face good; back hair
  a big lump vs MM9's nape-length: sent back to reshape (0 credits). Overview card added (open, rework pending).
  All 15 bodies of the batch are now built; open reworks: PeasantDM2 face, Markel back hair.
- **PeasantDM2 face redone** (0 Meshy credits, one Codex run, rollback r4): one skin tone across face/scalp, smiling eyes, hands
  matched. Orchestrator read sheet_faces_before_after: mask edge gone, kinder eyes. Ready for review.
- **Markel back hair reshaped** (r3, 0 credits, rollback r2): tail cut at the nape, hair pulled to the skull, reweighted to head/neck;
  head stretch 1.63 (target 1.5) left. Orchestrator read sheet_hair_body_before_after: matches MM9's silhouette.
- **Batch complete:** all 15 bodies installed and bound as MM9 descriptors; 445 of 1000 credits (backup 3295). Open for the user:
  review on the overview page; the map-placement switch (transcoder emits 9000+row for rows in mm9_npc_actor_rows.tsv, plus Annud's
  54) and MM9 map regeneration await the user's go-ahead.

- 2026-11-02 — User review notes, round 1: PeasantF1 nose/lip doubled paint, PeasantDM1 ear texture, PeasantF5 nose, Kira (Fidget1 jaw shear, claw hands, right wrist graft hole), PeasantDM2 see-through cuffs and boot tops. Agents started on each (0 credits). **PeasantDM1 fixed (r3)**: Meshy painted the Codex references' braid bead onto tier A's ears; `fix_ear_pdm1.py` gives the ear islands B's ear paint in A's skin tone and removes the beard-edge net; binding PASS. Ear sweep (`claude_shared/mm9_overview/ear_sweep_20261102.png`) found DM2 (same fault, added to the DM2 agent), Tryggva ear patches, PeasantM2 white net, HOM1 sideburn outline, plus M1d throat / Ebora throat checks: one agent on those.
- 2026-11-02 — PeasantF1 r22 / PeasantF5 r18 installed (0 credits, binding PASS): painted nose was 6 mm longer than the geometry's (doubled nostrils), mouth cavity plate showed as a pink inner lip; nose warped onto the geometry, underside repainted, cavity closed smooth, centre-line faces flattened. Orchestrator read both sheets and sent a second pass back before showing the user: F1 pale crescents under the lower lids (eye-plate fault as PeasantM1), F1 hood-edge cheek patch, F5 nostrils still a brown blotch.
- 2026-11-02 — Ear-sweep fixes installed (0 credits, binding PASS, mesh/clips unchanged except M1d): Tryggva r3 (fringe_fix had painted hair over the hair-mesh ears; `fix_ear_try.py`), PeasantM2 r4 (Meshy white net, `fix_net_pm2.py`), PeasantHOM1 v16 (hairline_fix darkened the sideburn border, `fix_sideburn_phom1.py`), PeasantM1d v8 (1.2 cm neck hole left by geo_fix, `neck_hole.py`), Ebora cf10 (s2 olive throat from a clipped ramp; the low-view wing patch is the wings behind the neck, not a hole). Orchestrator read all five sheets and the throat proof.
- 2026-11-02 — Kira r8 installed (0 credits, binding PASS, all README gates pass): lower face rigid to the head (`face_rigid.py`; was neck-weighted, 50-83 mm shear), `finger_pose.py` (curl-only, from MM9's mitten), `wrist_fill.py` (glove fills the vambrace rim + cap), `subdiv_fingers.py` (+3.4k tris, LOD0 16,160), chin UV slivers/folds/paint fixed. Orchestrator read the jaw, hands and wrist sheets. Left: lip V notch, streaky finger paint.
- 2026-11-02 — PeasantF1 r23 / PeasantF5 r19 (second pass, 0 credits, binding PASS): F1 lower-lid ledge normals smoothed + socket fill (pale crescent gone), brow spikes smoothed, ear plate smoothed; F5 nostrils smaller cool shadow, tip smoothed. Orchestrator read both sheets; accepted for the user's review (F1 lid edge slightly stepped at extreme close-up; F5 soft shadow under the tip).
- 2026-11-02 — **User: "ok besides that every other is ok i guess"** (besides PeasantDM2, still in work): PeasantM1d, F8, M1, M7, M2, HOM1, F1, DM1, F5, Kira, Bjarni, Tryggva, Sven, Markel and Ebora/Concubine approved; overview cards set ok. Still open: PeasantDM2 (holes + ears, agent running), DM1 tier B braid beads (keep, unless the user says otherwise), the map-placement switch.
- 2026-11-02 — PeasantDM2 r7 installed (0 credits, binding PASS): rim linings (`linings.sh`, `rim_lining.py`, `neck_cap.py`) close the see-through cuffs/boot tops/collar/belt; new `see_through_gate.py` (sleeves 431/391 -> 4/4 px, boots 241/181 -> 0); LOD0 8,650 -> 11,942; ears rebuilt from temple skin (`fix_ear_pdm2.py`). Orchestrator read the holes, ears and sweep sheets. Sweep (`claude_shared/mm9_overview/holes_sweep_20261102.png`): see-through openings on approved bodies, worst Bjarni (tunic 2542 px in Death, collar 810, sleeves ~640), Sven (tunic 2529 Death), Tryggva (sleeves 590/502), PeasantM1d (tunic 762 Death, boots ~260), M1 255, M2 200, DM1 sleeves 164, HOM1/M7/Markel mild. Asked the user before changing approved bodies.
- 2026-11-02 — **User: build the shared-mesh variants** (mesh comparison: HOM2 = HOM1, M7d = M7 + elf ears, M8d = Forad + elf ears, Hanndl = Annud's PeasantM6, Boy1/Boy2/Boy1e and Girl2/Girl3/Girl1e one body each, Wyrde Unknown = Knowing; Hag = Yrsa body + new head, F3 = F1 body + new headwear). Brief `devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md` (no duplicated bodies; approved models frozen; caps 20 credits per variant, 60 per new family; same 1000-credit budget, 555 left, floor 2740). Wave 1, five agents: HOM2+M7d, M8d+Hanndl, Hag+F3, boy family, girl family. Wave 2 when a slot frees: the Wyrde family (wyrd_young + wyrd_mature).
- 2026-11-02 — Variants: Old Hag (`mm9_hag.glb`, `MM9 245 Old Hag`) and PeasantF3 (`mm9_peasantf3.glb`, `MM9 40 Shopkeeper`, `MM9 35 Prisoner`) installed on Yrsa's / PeasantF1's bodies, 40 credits (backup 3085 after; other agents spending too), binding PASS 198 descriptors. Yrsa and F1 proven unchanged (sha256 of installed GLBs and project files). Orchestrator read the before/after, face, ears and close sheets. Hag accepted for the user's review (notes: flat yellow earring plates, olive hood lump by the right jaw from Yrsa, hands a bit darker than face, see-through inherited from Yrsa). **PeasantF3 sent back** (queued for the next free agent slot): blocky low-res square patch on both cheeks where F1's ears are flattened, hard-edged block on the chin, ledge on the hood, LOD0 17,494 > 15k, braid/veil body intersections 2-3 cm. Wave 2 started: Wyrde family agent (`mm9_wyrde_claude`).
- 2026-11-02 — **User: "old hag ok"**: Old Hag approved; overview card added (group Variants, new).
- 2026-11-02 — Variants: PeasantHOM2 = new tier `phom2_a` in `mm9_phom1.glb` (`MM9 59 Shopkeeper`; own body + head paint, 20 credits; HOM1 tiers proven byte-identical, rollback in `mm9_peasanthom2_claude/work/rollback/`) and PeasantM7d = own GLB `mm9_peasantm7d.glb` on M7's body with procedural elf ears (`MM9 25 Town` pm7d_d, `MM9 27 Shopkeeper` pm7d_c; 20 credits; boot/belt linings; M7 sha256 unchanged). Binding PASS. Orchestrator read both MM9-vs-ours and face sheets: accepted for the user's review. HOM2 inherits HOM1's see-through openings (knees 125 px Running) — part of the open lining question. PeasantF3 send-back started (resumed the Hag/F3 agent).
- 2026-11-02 — **User: "peasantdm2 - ok, peasanthom2 - ok, peasantm7d - ok"**: PeasantDM2 (r7), PeasantHOM2 (tier phom2_a) and PeasantM7d approved; overview cards set ok. All 15 townsfolk/unique bodies of the 2026-11-01 batch are now approved.
- 2026-11-02 — **User: "spin 3 more agents, make it max 8 parallel"** (agent cap raised from 5 to 8). Placement counts of the unbuilt bodies (rebuilt maps, legacy stand-in ids): PeasantM8 30, M3 16, M2d 14, F6 12, DM4 11, F7 10, F4 7, M4 7, DF1 6, F2 6. Started the top three: PeasantM8 (row 55; Forad variant route, ~1 cm except trousers; cap 20, 60 if a new body), PeasantM3 (rows 45/52; new body unless a built one is within ~1.5 cm; cap 50), PeasantM2d (rows 24/26, elf; close to M2 at p90 ~2.6 cm: warp M2 + elf ears preferred, cap 20, 50 new body). Backup 3050 at launch (310 above the 2740 floor).
- 2026-11-02 — Boy family installed (`mm9_peasantboy.glb` tiers pboy_a/b/e + `mm9_peasantboy_elfears.glb`; `MM9 69/70/73`; 45 credits; binding PASS; see-through belt slit open). Orchestrator read MM9-vs-ours, faces and ears sheets. **Sent back** (0 credits expected): hair split down the back of the head with a skin slit crown to nape, dark smudge down the side of the nose, A/B lips parted/swollen, hands pale grey-white vs faces, belt see-through band, b/e trousers should be plain brown (check pattern now), b's open vest + cream shirt panel if paintable; descriptor heights are the stand-ins' (160/160/106) — noted for the orchestrator.
- 2026-11-02 — Girl family installed (`mm9_peasantgirl.glb` tiers pg_g2/pg_g3 + `mm9_peasantgirl1e.glb` pg_g1e; `MM9 71/72/74`; 45 credits; binding PASS 201). The orchestrator's boy-family checklist was applied (closed hair back, nose, lips, hands, waist cap and filled vest slits). Orchestrator read face 128 px, face fix, back of head and tier sheets. **Sent back** (0 credits): waxy glossy skin and hair, dotted line across the neck, hairline ridge band (g3), pointed faceted chin, lip specks, dark eye sockets at party view, legs through skirt 1.3-2.5 cm; plus an MM9-vs-ours sheet. Correct descriptor height recorded: 130 units, radius 21 (tables carry the stand-in's 151/51).
- 2026-11-02 — Boy family pass 2 reinstalled (0 credits): back of head confirmed closed (the earlier "slit" was two side views meeting on the sheet), hands toned per tier, b/e plain trousers, b open vest + cream panel, waist tube (belt slit 95 -> 21 px level / 4 party). Orchestrator read the before/after, back-of-head and tiers sheets. **Sent back (pass 3)**: new closed mouths read as a pinched pout (all tiers); tiers sheet shows elf ears on a and b (verify only `MM9 73` attaches them); b nose-bridge stripe. MM9 heights: 133 / radius 26 for 9069/9070/9073.
- 2026-11-02 — PeasantF3 r17 (second pass, 0 credits, binding PASS 204): ear-front cheek patch and chin block fixed (`skin_harmonize_pf3.py`, chin crease smoothed), veil flush on the hood, LOD0 14,978, braid/veil contacts reduced (veil still 2.9 cm in Talk/Conv1/Cower). F1 unchanged (sha256). Orchestrator read face before/after and ears sheets (faint cheek spot remains): accepted for the user's review; overview card added.
- 2026-11-02 — Boy family pass 3 reinstalled (0 credits): `mouth_relax.py` settles Meshy's proud lips and a wide closed smile is painted; elf-ear binding confirmed only on `MM9 73` (the a/b ears were the preview renderer). Nose-bridge stripe on b is mesh shading (left). Orchestrator read faces p3 and tiers: accepted for the user's review; overview card added.
- 2026-11-02 — Backup 2975 (235 above the floor). Not starting more paid bodies (F6, DM4 next) until the running Wyrde/M8/M3/M2d settle: their caps could use ~180. Started a 0-credit binding agent: the unbound rows of built models (PeasantM6 47, Dook militia 303, clan soldier 132-134/292, plus any others it finds) and the child descriptor heights (boys 133/26, girls 130/21) without touching other rows.
- 2026-11-02 — **User, PeasantF3: "has giga strange face geometry there? like check the profile"** (screenshots in `mm9_peasantf3_claude/review/user_notes/`): receding chin into a flat swollen under-chin slab, lips jutting, drooping dark nose tip, jagged veil teeth over the hair, temple blotches. Sent back (pass 3, 0 credits): rebuild chin/jaw against MM9 F3 and F1 profiles. Lesson: profile and low 3/4 views go on every face sheet.
- 2026-11-02 — **User, boy: "look at his mouth"** (`mm9_peasantboy_claude/review/user_notes/mouth_front_tiera.png`, viewer front, tier a): pass-3 mouth is a thin painted smile line over a pale lumpy lip bulge (two mouths, pale lips, teeth specks at the centre); also a bright stripe down the nose bridge with a dark diamond at its top, red eye rims. Queued for the next free slot (8 agents running).
- 2026-11-02 — Boy pass 4 started (user mouth note, all tiers; nose-bridge midline repair; red rims; sheet in the viewer's lighting).
- 2026-11-02 — Binding agent (0 changes): every monster row is bound; the six unbound rows of built models have no matching tier: 47 (PeasantM6a = mustard recolour of Annud's M6b, needs a colour tier on `mm9_annud`), 132/133/134/292 (ClanSoldier1/6/9 and Tamur Leng: different armour art and heads from `clan_a/b/c`; row 110 precedent binds a chainmail skin to clan_b), 303 Phantom Fighter (dookmilitia, no skin, not placed or spawned). Heights: `mm9_monster_bodies.py --write-overrides` would change 48 descriptor rows (stale override file since 42 NPC rows were added: townsfolk 100-120 -> 174, dwarves 85 -> 118, half-orcs 131 -> 215, uniques 174, Wyrdes 154) and its rule is wrong for the children and Sven (axis); stopped. Both need the user's decision.
- 2026-11-02 — **User decisions: heights "Refresh all", unbound rows "Nearest + recolour"**. Binding agent resumed: full `mm9_monster_bodies.py` refresh with script exceptions for the children (boys 133/26, girls 130/21) and Sven (measured), any other wrong-axis rows reported; 303 -> dook_a, 132-134/292 -> nearest clan tier (row 110 precedent), 47 -> new mustard colour tier appended to the frozen `mm9_annud.glb` (existing tier byte-identical, rollback, Hanndl checked).
- 2026-11-02 — Variants: PeasantM8d (`mm9_peasantm8d.glb`, `MM9 23 Commoner`; Forad body, ears drawn into elf points, 20 credits) and Hanndl (`mm9_hanndl.glb`, `MM9 260`; Annud body with the bell cuffs narrowed — MM9's "arm piece" is Annud's cuff, not Hanndl's — linings, 17 cinema clips, 20 credits). Forad and Annud unchanged (sha256). Binding PASS 204, full suite 192 + known out05. Orchestrator read MM9-vs-ours and face sheets (incl. profiles): accepted for the user's review; overview cards added.
- 2026-11-02 — Wyrde family installed (`mm9_wyrde.glb`, tiers Morgan/Verdandi, `MM9 264`/`MM9 265`; 35 credits; LOD0 14,931; see-through ≤7 px except Death 26; binding PASS; the agent saw 2 extra suite failures from another session's `assets_dev/worlds/mm9/modifiers.yml` `taunt_seconds` edit rejected by the current build). Orchestrator read faces vs MM9, r4 face and body sheets. **Sent back**: Verdandi forehead pearl still there, dirty nose undersides, staring eyes (MM9 calm / smiling squint), Morgan bald tan scalp under the tiara, lipstick red, mirrored damask blotches on the mantle back; profiles + low 3/4 added to the face sheet.
- 2026-11-02 — PeasantM2d installed (`mm9_peasantm2d.glb`, `MM9 24 Town` pm2d_c, `MM9 26 Shopkeeper` pm2d_d; variant of the approved M2: MM9 M2d = M2 mesh shifted 2.6 cm + elf ears; 20 credits; M2 sha256 unchanged; binding PASS 206). Orchestrator read MM9-vs-ours, faces and ears/profile sheets: accepted for the user's review; card added.
- 2026-11-02 — **User: "peasantm8d good"**: PeasantM8d approved; card set ok.
- 2026-11-02 — **User: "hanndl ok"**: Hanndl approved; card set ok.
- 2026-11-02 — **User: "peasantm2d ok"**: PeasantM2d approved; card set ok.
- 2026-11-02 — PeasantM8 installed (`mm9_peasantm8.glb`, `MM9 55 Shopkeeper`; Forad variant, ponytail/beads/eyeballs removed, Conv2/Conv3 for Narrator.scr; 20 credits; Forad unchanged; binding PASS 202, suite 192 + out05). Open: sleeve poke up to 24 mm in Hit (Forad bracer), cuff slivers 22 px Conv2. Orchestrator read MM9-vs-ours and face/profile sheets: accepted for the user's review; card added.
- 2026-11-02 — Started PeasantF6 (rows 17/19, elf woman; close to the approved F5 — legs 0.5, torso/arms 1.9, head 2.3 cm: F5 variant + elf ears preferred, cap 20/50) and PeasantDM4 (row 10 dwarf; 2-5 cm from DM1/DM2: new body unless a rigid shift explains it, cap 50). Backup 2975 at launch; worst case leaves ~2825. Face sheets now require true profile, low 3/4 and viewer lighting.
- 2026-11-02 — Girl family r14 (0 credits): roughness floor, neck blobs, hairline sink, chin, eye sockets, shins narrowed (ray check: 2 vertex-frames truly outside), MM9-vs-ours sheet good. Orchestrator read the before/after: **sent back** — a black line across the neck at the head/body seam and translucent triangular flaps beside the neck in the after rows, lip specks; final check to be rendered in the viewer.
- 2026-11-02 — Boy pass 4 (0 credits): the "two mouths" were three loose Meshy lip pieces floating over the face (deleted; one mouth painted on the face lip line); 11 midline welds removed the nose diamond/stripe; red rims softened. Orchestrator read sheet_faces_p4 zoomed: mouth is now a flat uniform pink stripe with no lips in profile — **pass 5**: sculpt subtle lips + shaped lip paint, glabella smudge.
- 2026-11-02 — Wyrde r5 (0 credits): pearl gone, nostrils clean, lids lowered, Morgan scalp blonde, mantle damask non-mirrored, profiles OK. Orchestrator read sheet_faces_before_after_r5: **pass 6** — both mouths now read as a swollen pursed pout (MM9 Verdandi smiles wide, Morgan calm thin lips); nose underside dark V from below.
- 2026-11-02 — Bindings + heights done (actors suite 192 + known out05; binding PASS 214 on 92 models). Bound: `MM9 47 Shopkeeper` -> new `mm9_annud` tier `pm6_a` (mustard tunic ramp, appended; Annud and Hanndl proven byte-identical, rollback in `mm9_annud_claude/tier_m6a/work/rollback/`), 132/133/134 -> `clan_b`, 292 Tamur Leng -> `clan_c` (no dragon sword model), 303 -> `dook_a`. Heights: `mm9_monster_bodies.py` exceptions for children (boys 133/26, girls 130/21) and Sven (218/38 from his standing clip); overrides rewritten, 50 rows' Height/Radius changed (townsfolk/uniques 174/31, dwarves 118/31, half-orcs 215-220/38, Wyrdes 154/31) + 6 new rows. Orchestrator read the pm6_a sheet (ochre, slightly browner than MM9). The review root's hard-linked old tables are not relinked (map step).
- 2026-11-02 — Boy pass 5 reinstalled (0 credits): `lip_sculpt.py` (lips sculpted into the face surface), shaped lip paint, glabella cleaned. Orchestrator read sheet_faces_p5 zoomed: one shaped mouth, lips visible in profile; back to the user.
- 2026-11-02 — **User: "peasant boys ok"**: boy family (69/70/73) approved; card set ok.
- 2026-11-02 — Girl family r15 (0 credits): neck line/ghost flaps were an uninstalled 13:14 render (installed r14/r15 clean); lip specks were hole patches textured from skin (now lip colour, islands dilated). Orchestrator read the viewer face sheet r15: accepted for the user's review; card added.
- 2026-11-02 — PeasantF3 pass 3 (r21, 0 credits): chin/jaw rebuilt (pass-2 smoothing and normal relax removed; chin point 12 mm forward, under-chin angle restored; neck seam gap 4.6 mm closed), nose tip lifted and repainted, veil front edge `hood_edge_pf3.py`, temples skin. F1 unchanged. Orchestrator read pass3/profile_sheet: chin good; a white zigzag streak on the cheek in front of the ear still shows in profile (F1 approved has the same mark) — small fix sent.
- 2026-11-02 — Wyrde r14 (0 credits): pout was Meshy's 1.9 cm painted lips (no loose lip pieces); thin painted lips, Verdandi corners up in paint (shared mesh), normals relaxed over mouth/nose base. Orchestrator read the r14 sheet: no pout now, but lips thin/pale; shown to the user with that caveat (cutscene-only NPCs); card added.
- 2026-11-02 — PeasantM3 installed (new body: torso 3.9-5.7 cm from every built male; `mm9_peasantm3.glb` tiers pm3_a row 52 / pm3_b row 45; 35 credits; see-through 317 -> 9 px; binding PASS 214, suite 192 + out05). Orchestrator read MM9-vs-ours, faces and face_a: tier B good; **tier A sent back** — glaring squint, pale band between the lips, hard beard edge and jagged neck band under the jaw.
- 2026-11-02 — **User, Wyrde: "mouth + nose needs work? ... decide off the bat if the mouth can be fixed or if it needs remesh or some model adaptations"** (`mm9_wyrde_claude/review/user_notes/morgan_mouth_nose_front.png`): nose without nostrils/alae, mouth a thin painted line on a flat lower face. Decision: geometry adaptation of the shared head (undo r14 normal relax; sculpt nose base and lips, local subdivision if needed; Codex face repaint projected), no new body; 4K head retexture only as a fallback.
- 2026-11-02 — **User, Verdandi: "this also strange"** (`user_notes/verdandi_nose_mouth_front.png`): flat nose bridge with a smear, alae as two separate blobs with no nostrils, thin flat mouth band. Same rebuild.
- 2026-11-02 — **User, girl: "1) the neck seam + body on the graft area has clear line 2) the leftover nose skin there like next to the normal nose"** (`mm9_peasantgirl_claude/review/user_notes/neck_seam_nose_front_g2.png`). Orchestrator also sees dark wedges under the lower lids, dark lip outline/corners, a dark chin dot. Sent back.
- 2026-11-02 — Wyrde r16 (0 credits): the flat nose/mouth were the agent's own r9-r14 steps (geometry relax, normal relax, flattened normal map, flat repaint) over a good Meshy nose and lips; all undone, Meshy nose/lip paint restored and toned. Orchestrator read sheet_faces_r14_vs_r16: noses and lips have form again; back to the user. Lesson: do not smooth/flatten Meshy face forms to hide paint faults — fix the paint.
- 2026-11-02 — PC rebooted mid-batch: restarted the review HTTP server on 8912 (`python3 -m http.server 8912 --bind 127.0.0.1` from the repo root) and resumed the five interrupted agents (girl neck/nose, F3 cheek streak, M3 tier A face, F6, DM4) with instructions to check for half-written files, verify installed GLB hashes, re-claim leases and never resubmit a Meshy job without checking its status. Backup 2930.
- 2026-11-02 — **OOM at ~110 GB killed the session**: caused by the orchestrator's mesh-comparison batch (unbounded surface sampling). Rebuilt the comparison tool durably as `level_generation/creatures/claude_shared/mm9_meshcmp.py` (bounded samples, ~75 MB; adds skeleton match and rigid-shift residual) and run it under `systemd-run --user --scope -p MemoryMax=3G`. VARIANTS_BRIEF gained a "Memory" section (all Blender/heavy jobs under MemoryMax=12G, one Blender per agent) and a "Face lessons" section. User: "dont let it happen again".
- 2026-11-02 — **User: "raise the limit by another 1000"**: new floor 1740 (backup 2930). Remaining 20 models compared: variants likely — DF1~DF3 1.9 / DF2~DF4 2.7 (one dwarf-woman family), F4 = F1 body (head 2.8), DM3 ~ DM1 2.4, M5 ~ Markel 3.5 (torso), M4 ~ PeasantM8/Forad (torso 4.1-4.9); new bodies — F2, F7, HOF1, HOF2, dwarf boy, Wyrd_old (torso 6.9 from Hag), Fre, Green Man, Krohn, Scholar, Sigmund, Skraelos. Resumed the five interrupted agents with the memory rule; started DF family (cap 80), PeasantF4 on F1 (cap 30), PeasantDM3 on DM1 (cap 25).
- 2026-11-02 — PeasantF3 pass 4 (r34, 0 credits): cheek streak = Meshy cheek hole collapsed to a point by F1's tweak_pf1.py (folded wedges catch light); capped properly in F3. F1 (approved) has the same streak — offered the user the same 0-credit fix. Orchestrator read pass4 profile and cheek sheets: streak gone; back to the user.
- 2026-11-02 — **User, PeasantF3 tier A front: "eyes, what are these black things... nose - is that supposed to be a nose? ... texture splotches next to the nose... black stuff on her upper lip?"** (`user_notes/face_front_tiera_eyes_nose_lip.png`). Decision: stop patching the projected Codex face; repaint the face fresh on the current geometry (Meshy 4K head retexture per tier, up to +20 credits), then F1's proven face fixes, judged in the viewer at the user's zoom.
- 2026-11-02 — Girl r23 (0 credits): brow diamond lighter; chin V and neck specks remain. Orchestrator read r23 zoom: nose base brown smear, dark lip outline + slit specks, midline mirror seam, under-eye lines — same class as the user's F3 note. Decision: fresh Meshy head retexture per girl on the current mesh (up to +30), then F1 face fixes, judged in the viewer at the user's zoom.
- 2026-11-02 — **User: "wyrde ok, peasantm8 ok"**: Wyrde pair (r16) and PeasantM8 approved; cards set ok.
- 2026-11-02 — **User, girls: "please just fix the stuff on her nostrils (unless the agent is already doing it)"** (`user_notes/nostrils_from_below_g1e.png`, low view): scope narrowed — cancel the full face repaint, fix only the nostril smear (all three girls).
- 2026-11-02 — **User: "if you think repaint meshy is better do that!"** — back to the full Meshy face repaint for the girls (up to +30 credits), with the user's low-view nostril shot as the bar.
- 2026-11-02 — PeasantM3 face r2 (0 credits): loose 40-vertex Meshy lip piece deleted, mouth openings capped, A brows/eyes repainted calm, beard fades to neck, collar line, ears skin. Orchestrator read sheet_faces_r2: B good; A still pale painted brows, pursed lips, dark nostril blob — fresh Meshy head retexture for A (10 credits).
- 2026-11-02 — PeasantF6 installed (F5 variant: identical skeleton, coif removed, hair bob + braid + elf ears; `mm9_peasantf6.glb` pf6_a row 17 / pf6_b row 19; 20 credits; F5 unchanged; binding PASS 216). Orchestrator read MM9-vs-ours and faces_r9: faces close; **sent back** — the hair is a huge flared bell standing off the skull with a hard rim and a skin gap at the nape (MM9: pulled back close to the head, braid); nostrils slightly dark.
- 2026-11-02 — All eight agents stopped at the 5-hour API limit; resumed after the reset (told to check Meshy/Codex job status before any resubmission). Backup 2815.
- 2026-11-02 — PeasantM3 head repaint r3 (tier A, 10 credits; total 45): fresh Meshy head, mouth closed by vertices, beard fade/collar/ears re-applied. Orchestrator read sheet_faces_r3: A calm now, B good; card added for the user's review.
- 2026-11-02 — Started PeasantM4 + PeasantM5 (one agent, sequential; M4 ~ Forad/PeasantM8 body with a different torso, M5 ~ Markel torso 3.5 cm; variant route preferred, caps 25 each / 50 new body).
- 2026-11-02 — PeasantF6 hair r13 (0 credits): cap pulled close to the skull. Orchestrator read hair-vs-MM9: my earlier note over-corrected — MM9's hair is a rounded bob slightly wider than the skull; ours is now too thin and the elf ears too large/high. Sent back to fit MM9's silhouette by overlay, ears smaller/lower, lip specks.
- 2026-11-02 — PeasantF6 r15 (0 credits): hair fitted to MM9's outline as a rounded bob, ears 11.6 -> 7.7 cm at MM9's position, lip backing plate. Orchestrator read hair-vs-MM9 r15 and faces r15: close to MM9; card added for the user's review.
- 2026-11-02 — Started PeasantF2 + F7 (one agent; F2 new body, F7 as an F2 variant if close, caps 50 + 25/50). Backup 2765.
- 2026-11-02 — PeasantDM4 installed (new body on the dwarf skeleton; `mm9_peasantdm4.glb`, `MM9 10 Town`; 25 credits; binding PASS 217). Orchestrator read MM9-vs-ours and the face sheet: face/beard/clothes good. Sent back: see-through not passed (sleeve 110, torso 97, boots 14-18, head 28 px), cap reads as a domed metal helmet vs MM9's tall soft skullcap, dark stub at the left wrist.
- 2026-11-02 — PeasantF3 pass 5 (20 credits, total 40): fresh Meshy head per tier; eye wedges = downward eyeball faces (normals), lip glint = 293 slit slivers (single texel), splotches repainted, gutter fill. F1/Yrsa/Hag unchanged. Orchestrator read the front zoom and head before/after: clean; back to the user (small red nostril dots, pixel ticks on the nose ridge remain).
- 2026-11-02 — Girls r24 (30 credits, family 75): one-piece head UVs, fresh Meshy head paint per girl, nostrils on the mesh openings. Orchestrator read the r24 sheets: smears gone but faces paler/blanker with pale forehead-midline marks, inner-eye lines, pursed dark mouth corners, earlobe specks — short 0-credit paint pass sent.
- 2026-11-02 — PeasantDM3 installed (DM1 variant: longer hair and beard, no medallion; `mm9_peasantdm3.glb` pdm3_b row 11 / pdm3_a row 12; 20 credits; DM1 unchanged; suite 192 + out05). Orchestrator read MM9-vs-ours and faces: accepted for the user's review; card added (shared face, bolder stripes).
- 2026-11-02 — Dwarf women installed (one Meshy body, four GLBs `mm9_peasantdf1..4.glb`, seven rows `MM9 1-7`; 75 credits; heights 118/31 via mm9_monster_bodies.py which also filled rows 10/17/19). Orchestrator read MM9-vs-ours and faces: **sent back** — pdf3_b white mask band over the lower face, one egg-shaped headwear shell for all (MM9: bob / kerchief / pointed hoods with braids), stern dark faces vs MM9 warm smiles, B dresses too dark. Cap raised to 110.
- 2026-11-02 — PeasantDM4 r11 (0 credits): cap reshaped to MM9's tall flat skullcap, wrist lining, see-through mostly ≤ 12 px (left sleeve 17, head 18). Orchestrator read cap before/after: accepted for the user's review; card added.
- 2026-11-02 — Started dwarf boy (rows 67/68) + Sigmund (row 247) in one agent, caps 50 each. Backup 2660.
- 2026-11-02 — **User, PeasantDM4: "the talk animation like weirdly twists his clothing? like on breast/collarbones mainly?"** Sent back: re-weight chest/vest/collarbone toward the spine (compare DM1/DM2), Talk before/after strip.
- 2026-11-02 — **User: "peasantdm3 ok"**: PeasantDM3 approved; card set ok.
- 2026-11-02 — Girls r25 (0 credits): forehead marks were midline shading facets (normals), blush + rosier lips, relaxed corners, earlobe triangles tucked, nostril underside normals tilted. Orchestrator read r24 vs r25: cleaner and warmer; back to the user.
- 2026-11-02 — **User, PeasantF6: "isnt it a double nose or something? like on the skin + the nose itself?"** (`user_notes/double_nose_front_a.png`): painted nose wider/lower than the geometry nose (ghost nose), dark brown nostril blob, notched upper lip and a chin V. Sent back.
- 2026-11-02 — **User, PeasantM3: "part of lip missing?"** (`user_notes/lip_missing_front_a.png`, tier A front): lower lip ends short on the right with a pale beard-coloured patch, dark slit, pale band under the lower lip; also dark nostril blob and a light triangle under the left eye. Sent back.
- 2026-11-02 — **User, girls: "whats wrong with the mouth?"** (`user_notes/mouth_front_g2_r25.png`, g2 r25 front): a lighter oval halo around the mouth, pursed pucker shape with dark wedge corners, dark dot under the lip; also jagged hair teeth at the top of the forehead. Sent back.
- 2026-11-02 — **User: "peasantf3 - ok now"**: PeasantF3 (pass 5) approved; card set ok.
- 2026-11-02 — PeasantF6 r17 (0 credits): double nose = Codex-projected nose twice as wide; area repainted as skin so only the modelled nose shows; lip gap gold streak (44 faces on hair texels) fixed. Orchestrator read nose before/after: one nose; back to the user.
- 2026-11-02 — PeasantF4 installed (F1 body + new rounded hood + bell-sleeve tubes; `mm9_peasantf4.glb` pf4_a rows 30/37, pf4_b row 42; 20 credits; F1 unchanged; binding PASS 229). Orchestrator read face and body sheets: **sent back** — worried pale faces with staring eyes and dark nostril blob (MM9 A smiles warmly), F1's puffed lace-banded sleeves vs MM9 plain bell sleeves, clean cream apron vs MM9 dirty grey (B torn, teal underskirt).
- 2026-11-02 — PeasantM3 r4 (0 credits): lower lip whole again (r3 close had pushed half the lip inside). Orchestrator read r4 zoom: A still lopsided/red-smeared, B gained a red smudge under the moustache — paint made for the old open mouth. Plan: finalise mouth geometry, then fresh Meshy head retexture per tier (cap 70), no geometry moves after paint.
- 2026-11-02 — PeasantM3 r5 (20 credits, total 65/70): mouth geometry finalised, then fresh head paint per tier. Orchestrator read r5 zoom: mouths clean on both; A's eyes still a little intense; back to the user.
- 2026-11-02 — PeasantDM4 r14 (0 credits): Talk twist = vest/collar weighted to the hair bone (Talk swings it 49°) and upper arms onto the sternum; re-weighted like DM2 (Talk 5.6 -> 2.2 cm). Orchestrator read the before/after: twist fixed, but the area under the beard now shows a blurry smear when the head turns — sent back to continue the collar band and shirt texture there.
- 2026-11-02 — Dwarf women r4 (0 credits): face out of hair ramps, per-design headwear (hood points, DF3a braids, kerchief band), warmer faces with lifted corners, B colours from MM9 texels. Orchestrator read r4 face sheets: much better; last pass for DF3b flat black braids + ginger fringe and oversized DF3/DF4 hoods.
- 2026-11-02 — PeasantDM4 r15 (0 credits): under-beard area textured from real collar/shirt/vest patches. Orchestrator read the before/after: clothing now; back to the user.
- 2026-11-02 — Girls r26 (0 credits): halo was Meshy paint (blended out), pursed lower lip sculpted into the face, chin notch smoothed, hairline gradient. Orchestrator read mouth zoom: slit specks, corner ticks, jagged line remain (paint made for the old mouth). Plan as on PeasantM3: finalise mouth geometry, fresh Meshy head repaint per girl (cap 105), no geometry moves after paint.
- 2026-11-02 — PeasantM4 (PeasantM8/Forad reshaped, row 49, 20 credits) and PeasantM5 (Markel variant, rows 46/48, 20 credits) installed; sources unchanged; binding PASS 234. Orchestrator read the viewer-lit face sheets: both good; cards added for the user's review.
- 2026-11-02 — Started Igrid (wyrd_old, row 263; Wyrde variant if the skeleton matches) + Scholars (rows 274/275) in one agent. VARIANTS_BRIEF face rule "geometry before paint" passed in the brief text.
- 2026-11-02 — Dwarf women r5 (0 credits): DF3b dark plaits + fringe, DF3/DF4 hoods narrowed with clearer points. Orchestrator read r5 DF3/DF4 sheet: good; card added for the user's review.
- 2026-11-02 — Girls r27 (30 credits, family 105/105): mouth geometry finalised, then fresh head paint per girl. Orchestrator read mouth zoom and before/after: one clean rosy closed mouth, no corner ticks or specks; faint smudge under the lower lip, g1e heavy lashes. Back to the user.
- 2026-11-02 — **User, girls: "fix this patch please - on the upper lip"** (`user_notes/upper_lip_patch_g2_r27.png`): a pale, blurry rectangular patch over the upper lip/philtrum spanning the mouth width with hard side edges. Sent back (paint only).
- 2026-11-02 — **User (via session openyamm-2d), PeasantM5: "isnt there a disparity between the body size and head size?"** Silhouette overlay confirms Markel's body is wider than MM9 M5 (torso, arms, hem, thighs), head matches. Sent back: fit the body to M5 by an offset field from MM9's own meshes, head unchanged.
- 2026-11-02 — **User (relayed via session openyamm-2d): "peasantm4 ok", "peasantdm4 ok", "peasantf6 ok"** — cards set ok. Also: "dwarf woman — head graft obviously wrong since it cuts off the pendant? + the head itself isnt like anatomic? its like missing some stuff near temples?" — sent back.
- 2026-11-02 — **User (relayed via openyamm-2d), PeasantM3: "some artifacts here?"** — torn gold/skin shards round the neck at the collar (graft/neck-cap/lining z-fighting). Sent back.
- 2026-11-02 — **User: "do not start any new npcs, we want to finish work on the existing ones"** — no new agents/models. Not started and on hold: Fre, Green Man, Krohn, Skraelos. In-progress builds already running (F2/F7, half-orc women, dwarf boy + Sigmund, Igrid + Scholars) continue to finish; fixes on existing models take priority.
- 2026-11-02 — Girls r28 (0 credits): upper-lip patch = r27 clean-up aimed at the old mouth texels; remapped to the final head. Orchestrator read r27 vs r28: one rosy upper lip, no patch; back to the user.
- 2026-11-02 — PeasantF4 r31 (0 credits): warmer faces, lids rotated over the eyeballs, plain bodice/sleeves (paint, normal map and AO lacing flattened), dirty grey apron, B torn hem. F1 unchanged. Orchestrator read face and body sheets: close enough to show; card added. (Agent noted it once used pkill -f on its own grep; matched only its own process.)
- 2026-11-02 — Seven agents stopped at the 5-hour API limit (9:40pm reset); all resumed with "check job status before resubmitting". Backup 2450.
- 2026-11-02 — PeasantF2 (rows 31/32/38/39, new body, 35 credits) and PeasantF7 (rows 18/20, new body, 35 credits) installed and bound; head materials double-sided instead of rim linings (kept). Orchestrator read face and body sheets: bodies good; faces sent back (F2 hair flap behind ear, jagged hair side flaps, flat face; F7 nose-base speck/notch geometry, wide eyes, parting notch); fresh head paint allowed after geometry.
- 2026-11-02 — Half-orc women installed (one Meshy body; `mm9_peasanthof1.glb` tiers rows 61/62/63, `mm9_peasanthof2.glb` row 64 as a reshaped variant; 55 credits; binding PASS 246; heights 195/38). HOF2 fails sleeve poke and wrist see-through. Orchestrator read face and body sheets: sent back — HOF2 gates, HOF1 hair reads as a dark leather helmet (MM9 copper bob + braids), pale doughy faces, pink ears, Death skirt.
- 2026-11-02 — Dwarf boy (rows 67/68, own skeleton, 35 credits) and Sigmund (row 247, own skeleton + SIGMUND_CHILD clips + PeasantMale retargets, 25 credits) installed; binding PASS 246. Orchestrator read face and body sheets: both close to MM9; cards added for the user's review.
- 2026-11-02 — Dwarf women r6 (0 credits): head/body seam moved under the jaw (pendant whole), temples/cheeks widened to MM9 width. Orchestrator read r6 zoom: pendant continuous, faces fuller; back to the user.
- 2026-11-02 — PeasantM3 r7 (0 credits): neckline curve + even throat skin, but the head faces below it were painted as a blotchy gold bib (worse). Sent back: move those faces to the body material with UVs transferred from the collar so the brocade continues (or the body undershirt), no collar paint in the head texture.
- 2026-11-02 — PeasantM3 r8 (0 credits): faces below the neckline moved to the body material as a closed velvet shirt front. Orchestrator read neck r8: clean neckline and shirt front (small stretched streak at the 3/4 edge); back to the user.
- 2026-11-02 — PeasantM5 r16 (0 credits): body fitted to MM9 M5 surface (torso 0.2/1.8 cm, thighs 0.4/1.5), armpits still 2-4 cm wide. Orchestrator read before/after + silhouette: proportions now match; back to the user.
- 2026-11-02 — Igrid (`mm9_wyrdold.glb`, row 263, new body on Yrsa-like stooped skeleton, 25 credits) and Scholars (`mm9_scholar.glb`, rows 274/275, 35 credits) installed and bound. Orchestrator read face and body sheets: robes match MM9; sent back — Igrid grey skull-cap coif, painted wrinkle net, Death gates failing; Scholar B dark gaps at jaw/beard join, stern downturned mouth, legs through robe, Fidget hand.
- 2026-11-02 — F2/F7 face pass 2 (fresh head paint per tier on final geometry, +20 each; F2 r12, F7 r21). Orchestrator read before/after: F2 good (card added); F7 small pass for a pale midline strip down the bridge, dark nostrils on both, parting line.
- 2026-11-02 — F7 r25 / F2 r15 (0 credits): bridge paint line and seam normals, nostrils on the real openings, parting line. Orchestrator read pass3 before/after: clean; F7 card added for the user's review.
