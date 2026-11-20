# MM9 monster animation: audit against MM9's animator

Audit date 2026-11-04, after phases 0-5 of the [MM9 monster AI plan](MM9_MONSTER_AI_PLAN.md). The question: do the
3D models of MM9 monsters blend and move the way MM9's animator does, now that the AI moves them while they attack,
strafe, backpedal, swoop and wake? References:

- [MM9 animation blending RE](MM9_ACTOR_ANIMATION_BLENDING_RE.md) (the `Top` track, SetState, Update, BaseMelee);
- [MM9 native AI RE](monster_ai/MM9_AI_NATIVE_RE.md) §4.2 (per-state think, walk/run rate), §7.2.1 (interrupted
  attacks, the animator's exit rules), §7.3 and §8 (wince);
- the plan's animation notes (phases 2, 3, 4a, 4b).

Evidence lives in `output/mm9_rework/anim_audit/` (ignored): trace logs of every arena before and after the fixes
(`traces/before/`, `traces/after/`), the per-arena counts (`traces/compare.txt`) and frame bursts with contact sheets.

## How to look (tools added for this audit)

- **Animation trace.** An arena with `trace_animation: true` (or the console's `arena anim on`) writes `event=anim`
  lines: the main and layer clip, the playback rate over the last 0.1 s, the body's speed and every crossfade or cut
  (`blend=`). Headless runs then pose the models after each runtime step; in the window, every frame. Format and
  cost: [the arena README](../../tests/scenarios/mm9/ai/README.md) "Decision trace". Without the key the presentation
  never calls the trace (one null pointer test per actor and frame).
- **Flicker assertion.** `ai_trace: {..., max_in_window: {count, seconds}}` fails when more than `count` matching lines
  fall within any span of `seconds` (`{event: anim, detail: "blend=", max_in_window: {count: 3, seconds: 0.3}}`).
- **Frame bursts.** `debug.screenshot_burst_count` and `debug.screenshot_burst_interval_ms` capture a series of frames
  from `screenshot_path` ([Desktop game runs](../../tools/RUN_GAME.md)); with an arena, each capture's log line carries
  the trace clock, so frames line up with `anim` lines. `debug.time_scale` slows the game for them.

A crossfade that starts again within 0.15 s of the previous one is counted below as a *rapid pair*: the pose has not
settled when it is frozen again, which reads as a stutter.

## Summary

Before the fixes the 28 arenas and two audit views logged 2 462 crossfades, 678 rapid pairs, 242 A-B-A flips within
0.3 s and 142 lines of gaits played backwards; after them 1 749, 100, 0 and 7. Most of it came from four
presentation causes, all fixed here for MM9 actors only:

1. an attack's legs following the body's motion of every frame, while MM9's loops run and stop an attacker every AI
   tick (full-body attack and run-with-attack-layer alternating 3-10 times a second);
2. the backpedal clip and the reversed gait chosen from the angle between the body's motion and the model's lagging
   facing, rather than from what the AI is doing (MM9's Backpedal state versus its Strafe state);
3. one-step stands (a target switch, the arrival check before a strike) blending out of the gait and back in;
4. the walk/run choice following the speed of each step, while MM9 takes it from the AI's command.

These fixes first applied to MM9 actors only (behind a `mm9Animator` flag). The follow-ups below made them the shared
presentation of every 3D monster, MM6-MM8 included, and carried out the proposals P1-P7 ("Follow-ups done").

## Findings

Severity: **high** visible in every fight; **medium** visible regularly; **low** occasional or cosmetic.

Arena traces cited as `before/<arena>` and `after/<arena>` are `output/mm9_rework/anim_audit/traces/`. Times are
trace seconds. The three audit views (`view_fight`, `view_bird`, `view_wince`) are in
`output/mm9_rework/anim_audit/arenas/`: a Town Guard and a Horde Grunt fighting beside the party, a Bird passing a party
ally, a wounded guard struck until it winces.

### A1. An attack's legs flicker between the attack and the gait (high, fixed)

- **Where.** Every walker that strikes on the move: skirmishers, crawlers, guards, the Lobber's pods (`skirmisher`,
  `crawler`, `guards`, `civilians_monster`, `lobber`, `necromancer`, `summoner`, `view_fight`).
- **Ours.** The model chose the attack's legs from each frame's motion: moving, the gait under the attack layer;
  still, the whole-body attack. MM9's loops call RunTo and Stop on alternate ticks during a swing (BaseMelee's attack
  tick, the speed throttle), so the legs switched back and forth, each time starting a new 0.12 s crossfade from a
  frozen pose. Example: Town Guard `before/view_fight` 2.602 run+layer, 2.727 full body, 2.898 run+layer, 3.008 full
  body, 3.227 run+layer; Lobber pods 38 such A-B-A flips in 30 s (`before/lobber`).
- **MM9.** SetState (`0x1001ee50`) decides at the attack's start whether the main tracker joins the attack (actor
  still) or keeps the locomotion clip; later locomotion requests change only the main tracker and an idle request
  re-enters the attack (blending RE, "SetState"). The script ticks run at 0.2 s; the legs never change per frame.
- **Evidence.** `fight_before_sheet_2.55-3.30.png` against `fight_after_sheet_2.55-3.30.png` (the guard's legs
  alternate between the lunge stance and running before, run through the swing after); `traces/compare.txt`.
- **Fix.** The legs follow the motion at the attack's start, then change only after the other motion has held
  0.25 s (`advanceActorModelAttackLegs`, `ActorModelAttackLegsHoldSeconds`); every 3D monster since the follow-ups.

### A2. Backpedal and reversed gaits chosen from the angle of the motion (high, fixed)

- **Where.** Skirmishers' circles and chase starts, fliers' back-offs, swimmers, bosses (`skirmisher`, `view_fight`,
  `bird`, `banshee`, `dormant` (Icky), `summoner` (Specters), `yanmir`, `jellyspore`, `dragon_king` (Winged Mutant)).
- **Ours.** Backing away was decided by the angle between the velocity and the model's current facing, which lags the
  AI's by up to 540°/s: a monster turning to chase showed its BackpedalRun for 0.1 s (`before/alarm` 0.062,
  `before/patrol` wolf at every wander start, 7.633, 11.961, 16.766); a circle 65° off a moving target crossed the
  threshold and flipped between BackpedalRun and Running (`before/view_fight` grunt 3.328-3.461); fliers backing off
  played their flight clip reversed (`before/bird` 14 lines, `before/banshee` 31, `before/view_bird`
  46, Icky `before/dormant` 27), and Yanmir ran reversed (`before/yanmir` 3.031, 4.227, 4.961).
- **MM9.** Backpedal is a state the scripts ask for (DoEvade's first half, the 0.3 s AttackBackpedal: `Backpedal` and
  `BackpedalRun` clips, states 0x38/0x39); every other footwork is `Strafe ..., run` facing the target (blending RE,
  "BaseMelee combat loop"); a flier backs off with Strafe and faces its target. No clip plays backwards.
- **Fix.** The world reports the skirmisher's phase (`GameplayRuntimeActorState::footwork`, `backpedalling`,
  `skirmishBackpedals`): the backpedal clip plays exactly while the AI backpedals, every other move plays its gait
  forwards. Since the follow-ups for every actor whose AI runs skirmish footwork, in any world (MM6-MM8 data has none
  today); a requested backpedal without a backpedal clip plays the gait reversed (the Oculus), nothing else does.

### A3. Footwork turned the model to its motion (medium, fixed)

- **Ours.** A walking model faces where it moves when that is within ~100° of the AI's yaw
  (`actorModelFacesMovement`), so a circling or strafing skirmisher (animation state Walking) turned its body 65° away
  from its target while the AI faced it.
- **MM9.** Strafe keeps the facing (`FaceObject`, `Target ..., TRUE`); the legs run sideways.
- **Fix.** MM9 footwork keeps the AI's facing (`state.footwork`).

### A4. One-step stands blend out and back in (medium, fixed)

- **Ours.** A stand of one AI step (a target switch, the arrival or throttle check before a strike) started a
  crossfade to the stand and another out of it within 0.03-0.1 s: `before/holder` 21.398 Running, 21.430 Standing,
  21.461 AttackMelee, 21.492 run+layer; `before/view_fight` grunt 2.695 Standing, 2.727 Walking.
- **MM9.** Monsters update every 0.1 s (native RE §4.1); a stop shorter than an update does not exist.
- **Fix.** A 3D actor that stands within 0.15 s of walking keeps its gait, still (`ActorModelStandGraceSeconds`; MM9
  actors only until the follow-ups); a stand that lasts blends as before. After an attack the legs blend to the stand
  at once (no second blend).

### A5. Walk and run flicker; strikes on the move switch to the walk clip (medium, fixed)

- **Ours.** The gait was chosen from each frame's speed: a fleeing Bandit near the walk/run boundary switched every
  30-60 ms (`before/flee` 5.359-5.594, 261-453 units/s); blocked frames re-chose it from the hindered speed
  (`before/flee` 3.133 Running, 3.195 Walking at speed 0, 3.227 Running); a strike's speed throttle (0.95 x the
  target, half speed in a strafe attack) dropped the legs to the walk clip under the swing (`before/archer`
  8.859-9.000).
- **MM9.** WalkTo or RunTo picks the state; the clip's rate follows the speed (`0x1000e726`, rate = speed / velocity).
  During a swing the attack tick calls RunTo: the legs run.
- **Fix.** A strike counts as hurrying, the gait changes only while the body moves, and a new gait takes over after
  holding 0.3 s (`holdActorModelGait`, `ActorModelGaitHoldSeconds`), except when the body starts moving or stops
  backpedalling. MM9 actors only until the follow-ups, every 3D monster since.

### A6. The wind-up of a blow plays at a third to a half of its speed (medium, proposal P1, done)

- **Ours.** MM9 monsters have no sprite contact frames, so the AI applies a blow when the attack clip ends
  (`attackImpactLeadSecondsForAbility`). The model's marked action stretches the clip's wind-up (0 to its impact key)
  over that time: the Skeletoid (impact 0.40 s of a 0.80 s clip) swings at 0.37-0.56x (`before/skirmisher` 6.094,
  8.961, 10.695), then snaps through the follow-through at 1x.
- **MM9.** The clip plays at rate 1 and the hit lands at its `Attack` key (`0x1000ed00`, native RE §7.3); recovery
  counts from the clip's end (§7.2.1).
- **Proposal P1** below: hits (and the recovery they arm) at the key. Done: the Skeletoid's blow lands at 0.398 s (its
  key 0.40) and its swing plays at 1.02 ("Follow-ups done"). Before it, the blow landed at 0.49 s, the contact frame of
  the row's stand-in sprite (MM6's `ske1at`), not at the clip's end as stated above, and the wind-up played at 0.81.

### A7. Upper-body masks against MM9's `Top` weight sets (medium for fliers, proposal P2, done)

Comparison of every MM9 binding's `upper_body_root` subtree with the ABC's `Top` set:
`output/mm9_rework/anim_audit/top_weight_sets_vs_upper_body_root.txt`.

- **Bipeds** (Guard, Skeleton, Skeleton Warrior, Evil Sorcerer, Clan Soldier, Mummy, Lich, demons, Ebora): the same
  nodes, except that MM9's `Top` leaves `Bip01 Head` on the main track for most of them (Skeleton, Skeleton Warrior,
  Highwayman, Clan Soldier, Mummy, Lich and others: the head follows the gait); Bigfoot, Colloidal Warrior, Trellborg
  and Gezzampt use Spine2, which leaves Spine1 out. Low.
- **Whole-body `Top`**: Wolf, Dragonfly, Banshee, Flying Icky, Winged Mutant, Ghost, Sea Monster and the Evil Eye
  Terror give `Top` weight 1 on every node, so MM9 plays their attacks with the whole body even while they move. Ours
  layer a subtree: the Dragonfly's attack moves only its wings (`Xwingbase`) while its head and body keep the flight
  clip, the Banshee's `Xspine1` leaves out the dress and centre, the Icky's `XbackC` its legs and tail, the Winged
  Mutant's Spine1 its legs and claws, the Ghost's `Xspine1` covers only 18 of its 58 nodes. The Eye's and the Sea
  Monster's roots cover all but the root nodes.
- **No `Top`**: Crow (Bird), Lobber, Lobber Pod, Dragon King, Yanmir, Njam, Bjarni and the peasants use MM9's plain
  animator: no layer, the attack is the whole body. Ours give them a mask and layer the attack over the gait.
- **The Wolf** (BaseCrawl) is the visible case of "crawlers move while they strike": MM9's BaseCrawl also runs to a
  moving target during the swing (`BASECRAWL.inc` AttackTick), with the whole body biting while it slides. Ours run
  with the head and neck biting. Recommended to keep ours.

### A8. Walk and run rate against MM9's (low, by design; P5 done for the Evil Apprentice)

MM9 plays walk and run at speed / `WalkVelocity` or `RunVelocity` (native RE §4.2 step 9), 1.0 at the table speed
whatever the clip covers; ours follow the stride, so the feet stay planted. At MM9's speeds (units of 2.56 per LT):

| Monster | MM9 walk / run | Clip walk / run (stride / length) | Our rate walk / run | MM9's |
| --- | --- | --- | --- | --- |
| Skeletoid (9183) | 128 / 384 | 84 / 255 | 1.52 / 1.51 | 1.00 |
| Grey Wolf (9114) | 358 / 742 | 87 / 418 | 2.00 (cap) / 1.78 | 1.00 |
| Bandit (9101) | 192 / 640 | 145 / 800 | 1.32 / 0.80 | 1.00 |
| Town Guard (9107) | 192 / 640 | 130 / 680 | 1.48 / 0.94 | 1.00 |
| Horde Grunt (9129) | 192 / 512 | 200 / 580 | 0.96 / 0.88 | 1.00 |
| Evil Apprentice (9156) | 192 / 448 | 75 / 194 | 2.00 (cap) / 2.00 (cap) | 1.00 |
| Canopic Mummy (9144) | 192 / 448 | 109 / 280 | 1.76 / 1.60 | 1.00 |
| Skeleton Warrior (9136) | 192 / 512 | 153 / 510 | 1.26 / 1.00 | 1.00 |
| Commoner (9015) | 192 / 384 | 111 / 209 | 1.73 / 1.84 | 1.00 |
| Lesser Demon (9241) | 192 / 512 | 217 / 362 | 0.88 / 1.42 | 1.00 |
| Greater Demon (9242) | 192 / 512 | 222 / 803 | 0.87 / 0.64 | 1.00 |
| Lich (9207) | 192 / 512 | 98 / 456 | 1.40 (cap) / 1.12 | 1.00 |

OpenYAMM's wander is half the pursuit speed, not `WalkVelocity`, and the gait chooser plays the run when the walk would
pass its cap (the wolf trots its run at 371). MM9's rule slides the feet of every model whose clip covers less or more
ground than its velocity, most of all the scaled ones (Skeletoid `Scale` 0.5, Wolf 0.4). Keep ours. The Evil
Apprentice's walk and run and the Wolf's walk reach the 2.0 cap and slide in ours too: longer strides or new clips
(model work, P5).

**Superseded for the clip choice (2026-11-07, user report: Sturmford's children "very slowly" and a villager "running
very slowly for no reason").** MM9 wanders at `WalkVelocity` (the rows' `mm9_ai` `walk_speed`), and the speed chooser
then played the run for every townsperson whose walk is short-strided: the women jogged their run at 0.92x, the
children at 0.95x, the dwarves ran at the 2.0 cap. MM9's actors.yml now says `gait: intent`
(`actorModelIntendedGait`): the walk while the AI walks, the run or sprint while it hurries, as MM9's WalkTo and RunTo,
while that clip's rate stays within [1 / sqrt(2), 2]; outside it, the best suited clip when that one fits (the wolves
keep trotting, Giants and the Phantom Fighter keep walking rather than run in slow motion); when nothing fits, the
AI's clip if it is only too fast (its feet slide, as MM9's). `gait_audit.py --world mm9` mirrors it with MM9's speeds:
49 of 244 bindings change, all wanderers that ran (townsfolk, children, Zombies, Thralls, Nagates, Fish, the mice).
The walk strides of the townsfolk bindings were rewritten from `stride_audit.py` (men 1.05-1.2 to 1.28-1.44, the
dwarf boy 0.37 to 0.48 and his run 0.78 to 1.6, the dwarf MaleB 0.4 to 0.25, the boy 0.45 to 0.97 from the foot-joint
measure, which every joint-based check put at 0.8-1.2); a rebind from the creature projects' `stride.py` restores the
old values. Left: the women walk at 1.73x (binding 1.0, their foot joints say 1.2), and the dwarves' walks cover a
fifth of MM9's walking speed (0.39 m/s against 1.92), so they walk at the cap with their feet sliding 2.4-3.8x: new
walk clips (model work).

### A9. A coffin mummy snaps to its stand (low, proposal P3, done)

- **Ours.** `Coffin` blends to `Standing` over 0.12 s as it wakes (`after/dormant`), then runs.
- **MM9.** MummyAwaken.scr plays no Wakeup clip (plan, phase 4b): MM9 snaps too. The model has `wakeup` and `wakeup2`.

### A10. Deaths cut from a moving pose (low, proposal P4, done)

`blend=0.00` into Death while running or attacking (`after/ebora` 8.031 Concubine at 320 units/s,
`before/necromancer` 1.531 Skeleton Warrior). MM9's die state cuts through any state (terminal, §7.2.1), so a cut is
faithful; `death_blend_seconds` is 0 for every MM9 binding.

### A11. The gait judders above the AI rate (low, proposal P6, done)

Actors move in AI steps (128 a second) and the gait follows the distance moved. Above 128 frames a second, and in slow
motion, frames without a step hold the gait at its minimum rate and the next one jumps it: the Bird's rate read
0.80 and 1.30 on alternate frames at `time_scale` 0.25 (window trace of `view_bird`, kept in `bird_before/`).

### A12. Behaviour checks that matched MM9 (no change)

- **Wince** (`view_wince`): a hit at 20 % health or less rolls the wince; `Hit` replaces the pose over 0.06 s, full
  body, standing still (MM9's wince state: tracks without turning, §4.2; only a wince may replace an attack, §7.2.1).
  A wince cutting a swing did not occur in the arenas; it takes the same path (GotHit replaces the attack clip).
- **Taunts, Aware, Spawn, Cower, Resurrect, ResurrectSpell, Launch, hang and coffin poses** play their script clips
  (`taunt`, `aware`, `spawn`, `cower`, `resurrect`, `resurrect_spell`, `launch`, `hang`, `coffin`). The spawn-in's
  Aware plays Taunt (the demons have no Aware clip, as phase 4b assumed).
- **Townsfolk** run with their run clip now (`after/civilians` Commoner Running at 384); the phase 4b note about
  the walk gait is stale.
- **Facing**: the model turns at 540°/s toward the AI's yaw (MM9: 360°/s in PreAttack's FaceObject, 540°/s in Attack).
- **Monsters not on an MM9 loop** (the Oculus in `spell_conditions`) keep the MM6-MM8 presentation, reversed gait
  included (`after/spell_conditions` 9.961).

### A13. Headless arenas without models run differently (info, proposal P7, done)

`dragon_king` passes headless as shipped, but fails its "switch party dead" assertion when the arena poses the models
(`trace_animation`), with the binary before and after these fixes alike: something in the gameplay reads the posed
models (the launch sockets of the fire bolts are the likely one, `WorldFxSystem::actorLaunchPoint`). The window always
poses them, so the headless arenas do not quite reproduce window play.

### A14. First frame of a moving spawn shows the walk (low)

A monster spawned already moving shows its walk for one frame before its run (`after/*` lines at t=0.031); unchanged.

## Fixes made (presentation only)

All in `WorldFxSystem::syncActorModels` and two world-runtime presentation fields; first behind a `mm9Animator` flag
(actors with an MM9 loop profile), which the follow-ups removed: they apply to every 3D monster.

- **A1, attack legs held:** `advanceActorModelAttackLegs` (`ActorModelPresentation.h`). Unit test "Attack legs
  ..."; `skirmisher.yml` and `bird.yml` assert at most 3 (bird: 2) crossfades in any 0.3 s (`max_in_window`).
- **A2, backpedal by phase, nothing reversed:** `skirmishBackpedals` (`GameplayActorAiTypes.h`), `backpedalling` in
  both runtimes' `actorRuntimeState`. Unit test "MM9 skirmisher footwork ..."; `skirmisher.yml` asserts BackpedalRun
  and no reversed clip, `bird.yml` no reversed clip (the Bird had 14 reversed lines before).
- **A3, footwork faces the target:** `footwork` in both runtimes. Traces (`after/view_fight`).
- **A4, stand grace:** `ActorModelStandGraceSeconds` (was `Mm9StandGraceSeconds`). Traces.
- **A5, gait by command and held:** `holdActorModelGait`, a strike counts as hurrying. Unit test "Gait changes ..."; traces.
- Also asserted: `skirmisher.yml` the strafe attack swings over the run (`main=Running layer=AttackMelee`), `bird.yml`
  the pass strikes over the flight clip.

The AI is untouched: no file of `GameplayActorAiSystem` or `Mm9ActorRules` changed; `skirmishBackpedals` mirrors the
rule of `AI_SkirmishEvade` for presentation.

Totals over the 28 arenas and the `view_fight` and `view_bird` views (`traces/compare.txt`), before and after:

| | Before | After |
| --- | --- | --- |
| Crossfades | 2 462 | 1 749 |
| Rapid pairs (two within 0.15 s) | 678 | 100 |
| A-B-A flips within 0.3 s | 242 | 0 |
| Most crossfades of one arena in any 0.3 s | 9 | 3 |
| Lines with a reversed gait | 142 | 7 (the Oculus, not on an MM9 loop) |

The remaining rapid pairs are sequences, not flips: an attack layer ending as the footwork's clip changes, a taunt
starting as a backpedal ends.

## Proposals (AI, model or data changes)

All seven were approved and done on 2026-11-04 ("Follow-ups done" below says how).

- **P1 (AI/combat): hit at the clip's key.** Done, generically. Give MM9 actors `meleeAttackImpactSeconds` and
  `rangedAttackImpactSeconds` from their binding's `events` impacts (the MM9 `Attack`/`RangeAttack` keys the converter
  copied), so the blow lands, and arms its recovery (`hitRecoveryArmed`), at the key as in MM9; the wind-up then plays
  at rate 1 (A6).
- **P2 (data): masks as `Top`.** Done. For the whole-body `Top` models (Dragonfly, Banshee, Flying Icky, Winged
  Mutant, Ghost, Sea Monster, Evil Eye Terror) set `upper_body_root` to the skeleton's root; for the models without
  `Top` MM9 plays no layer at all. Keep the Wolf's neck-only layer (A7).
- **P3 (AI + presentation): wake clip.** Done. MM9 snaps; playing the model's `wakeup` while the AI waits for it reads
  better than MM9 (A9).
- **P4 (data): death blend.** Done, as the default of every 3D model (A10).
- **P5 (model): strides.** Done for the Evil Apprentice by data (its strides were mismeasured); the Wolf's walk is left
  (A8).
- **P6 (presentation, shared): smooth gait between AI steps.** Done (A11).
- **P7 (gameplay): models in headless arenas.** Done: arenas pose their models headless (A13).

## Follow-ups done (2026-11-04)

The user approved P1-P7 and asked for the presentation fixes to apply to every 3D monster, with one code path driven
by data rather than an MM6-MM8/MM9 split. Evidence in `output/mm9_rework/anim_followups/` (ignored): `traces/before`
(the binary before these follow-ups, `bin/openyamm_before`, on `before_root`/`before_review_root`: the same data less
the one new profile field it cannot read), `traces/after2` (all 31 arenas traced, `trace_animation` forced on by
`run_traces.py`), `traces/plain2` (the arenas as committed), `traces/compare_before_after.txt` (`compare_traces.py`),
`bursts/` (window runs and contact sheets).

**P1, the hit at the clip's key.** `resolveActorAttackTiming` (`GameplayActorAiTypes.h`), one rule for every world:
an authored sprite contact frame (`sprite_attack_timing.yml`) wins, as for every MM6-MM8 3D monster today (their
contact frames were picked against the models in `level_generation/creatures/timing_review/`); without one, the 3D
binding's impact key applies the attack within the sprite's action. A manifest whose models' clips are their
monsters' native timing says so in data, `attack_timing: clip` at the top of `worlds/mm9/models/actors.yml`: the
action then lasts the clip and applies at its key, over the contact frame of the row's stand-in sprite (MM9's rows
borrow MM6-MM8 sprites: the Skeletoid's `ske1at` is MM6's skeleton and has contact frame 4). The clips' lengths come
from the model files' JSON (`Engine::readGltfModelSummary`, no model loaded) through
`ActorModelManifest::attackClips`, which `MonsterTable::actorModels` hands both runtimes; spells use the model's cast
clip and `cast` key (`ActorRuntimeFacts::spellAttackAnimationSeconds`, `spellAttackImpactSeconds`). Recovery needed
no change: `mm9AttackStartCooldown` counts clip + recovery from the attack's start (restarted at the clip's end), the
hit arms hit time + recovery (`hitRecoveryArmed`), a wince before the key leaves none (`mm9CutAttackCooldown`); with
the action now the clip and the hit at its key that is section 7.2.1 as decoded. The trace gained `event=impact`
(`<ability> at <seconds into the action>`) and `layer_rate=`. Skeletoid (`traces/after2/skirmisher.trace.log`): the
blow lands 0.398-0.407 s into the 0.80 s action (key 0.40; before 0.49 s into a 0.75 s action), the swing plays at
1.02 (0.94 once per swing, the 0.1 s window over the impact frame) where it played its wind-up at 0.81. Window
burst: `bursts/skirmisher_swing_before_sheet.png`, `bursts/skirmisher_swing_after_sheet.png` (the strafe carries it
across the view quickly). The presentation now continues the clip from the planned impact time, not the frame that
first sees it (no held marker frame).

**P2, `Top` masks.** `upper_body_root: Scene Root` for the seven whole-body `Top` models (16 lines); `upper_body_root`
removed for every `NO-TOP` model of the comparison file (133 lines: the Crow, Lobbers, Dragon King, Yanmir, Njam,
Bjarni, the peasants and townsfolk, the animals, Giant, Greenman, Thrall, Zombie and the other named NPCs). The engine
makes the key optional: without it an attack plays with the whole body, moving or not (MM9's plain animator). Written
by the projects' binding scripts where they splice in place, else one splice (`output/mm9_rework/p2_top_masks/`), the
scripts brought up to date. The Bird's pass now strikes with its whole body (`bird.yml` asserts it, and no layer).

**P3, the mummy wake.** Profile `wakeup_seconds` (the model's `Wakeup` clip, `generate_mm9_monster_modifiers.py`; 4.37
s for the three mummy rows); `mm9WakeHoldSeconds`: a hanging start holds for its Launch, a lying one (coffin, sleep,
lie) for its Wakeup, then BaseInit looks for a target. The world plays `wakeup` straight from the coffin pose (the
first frame after a trigger keeps the pose until the AI steps). `dormant.yml`: Wakeup at 4.03 and 12.03, pursuit at
8.37 and 16.36 (was 4.05 and 12.05).

**P4, the death blend.** `death_blend_seconds` defaults to 0.1 s for every binding (`ActorModelDefaultDeathBlendSeconds`;
an explicit value, 0 included, still wins). Nothing in MM6-MM8 needs the cut: the 15 bindings that set a value set
0.1-0.3, none 0; burn, disintegration and corpse stand-ins start from the death state, not the pose.

**P5, foot sliding.** The Evil Apprentice's strides were mismeasured (0.90 / 1.36, the median of jerky keys); a planted
toe's backward travel over its stance gives 1.25 / 1.8 (`mm9_evilsorcerer_claude/scripts/bind_actors.py 1.25 1.8`),
so its walk needs 1.84 and its run 1.74 at MM9's speeds, under the 2.0 cap (wander at 224: the chooser plays the run at
0.87). The Wolf's walk stride is right (1.96 measured about 1.9): it covers a quarter of MM9's walk speed, so the gait
chooser plays its run there (0.86-0.89); only below about 174 units a second does the walk reach the cap. A
longer-strided trot clip is model work, left open. Not yet checked in the viewer.

**P6, the gait between AI steps.** `smoothActorModelGaitDistance`: the gait advances by the body's speed over the frame,
kept within two AI steps of the distance covered (exact over time, planted feet) instead of jumping a whole step on
the frames that see one; a stop advances what is left. Unit test: 300 frames a second over 128 steps advance the same
share every frame. Window, `time_scale` 0.25 (`bursts/bird_slow_after/ai_trace.log`): the Bird's flight writes no rate
change at all (the audit's 0.80/1.30 alternation is gone; the before binary cannot load the Crow's new binding, so
there is no window before for it).

**P7, posed models in headless arenas.** Gameplay reads one thing from posed models: a model actor's missile leaves
from its release socket (`WorldFxSystem::actorLaunchPoint`, both runtimes). The window poses every frame; headless
posed only with `trace_animation`, so the Dragon King's breath at 15.4 s, from his body, killed the Winged Mutant
headless and, from his mouth, missed it with the trace on. Arenas now pose their models headless whatever
`trace_animation` says (`ScenarioRuntimeDriver`), so headless arenas play as the window does; traced and plain runs of
all 31 arenas pass alike. Scenarios without an arena still launch from the body (open question below).

**Generalised presentation (A1, A2, A4, A5).** `mm9Animator` is gone: the attack legs held 0.25 s, the stand grace,
the gait by command (a strike hurries, the gait changes only while the body moves, a new gait holds 0.3 s) and the
backpedal on request apply to every 3D monster. The request is the AI's own output in any world: the skirmish phase
(`skirmishBackpedals`), which MM6-MM8 data does not use today, so MM6-MM8 models never reverse a gait or backpedal now
(before: when they moved against a facing that lagged the AI's). Facing the target while moving (footwork) is likewise
the AI's skirmish phase. Arena `mm6_3d_out` (two MM6 barbarians, an archer, a thief on New Sorpigal's green, MM6's
AI, with a party) before and after: crossfades 123 -> 109, rapid pairs 16 -> 8, A-B-A flips 1 -> 0, most crossfades of
one model in 0.3 s 3 -> 2; the scenario asserts no reversed gait and at most 2 in any 0.3 s. Their blows still land at
their sprites' contact frames (0.49 s). `mm8_melee_out01` shows the same clip sequence (MM8's random cooldown factor
moves its timing from run to run).

**A party in every arena.** Every arena scenario starts with `new_game_flow` (an invulnerable party), so blows and
spells land: 538 impacts over the arenas. Re-tuned: `alarm` (Skeletoid 2's join asserted by its landed blows),
`archer` (40 s: its first pursuit veto at 33.8 s), `bird` (whole-body pass), `dormant` (Wakeup), `dragon_king`
(posed: his bolts and breath from the mouth seldom hit the flying mutant, so the scenario kills it at 26 s; the wing
push at 37 s), `holder` (the Bandit closes in between blows: the party steps back to y 100), `necromancer` (the
apprentice casts after its clip: rise before 10.5 s), `ranged` (plain and strafe attacks, landed blows).

**Totals** over the 30 arenas and `mm6_3d_out` (`traces/compare_before_after.txt`), before and after the follow-ups:
crossfades 1 774 -> 1 651, rapid pairs 112 -> 63, A-B-A flips 1 -> 0, reversed-gait lines 7 -> 3 (the Oculus, which
backpedals on request without a backpedal clip), most crossfades of one model in 0.3 s 3 -> 3.

## MM6-MM8 regression

Before the follow-ups every change was gated by `mm9Animator`, and `mm8_melee_out01` logged the same presentation
before and after. The follow-ups change MM6-MM8 deliberately: the presentation rules above (no gait reversed or
backpedal without a request; the attack legs, stand grace and gait hold; a 0.1 s blend into death; the gait smoothed
between AI steps), and the attack timing of the 3D bindings whose sprites have no contact frame: they now strike at
the clip's key within the sprite's action (MM7: the zrat, zdog, zcat and zchicken pets, 24 roles; MM8: Dragon, Wimpy
Dragon, Wimpy Pirate Crossbowman (female), Troll and Minotaur peasants, Earth Elemental, 36 roles). Every MM6
binding's attack has a contact frame: no MM6 timing changes. Checks: `mm6_3d_out` and `mm8_melee_out01` above; the MM8
actor scenarios (`tests/scenarios/mm8_*.yml`) pass but `mm8_right_click_portrait_item` (already failing).

## Not established

- Whether LithTech crossfades between a tracker's animations (MM9's `SetCurAnim` was not followed into the engine), so
  the 0.12 s crossfades are OpenYAMM's own; MM9 may cut.
- ~~What clip MM9 plays for the Strafe state (0x0d)~~ Answered (2026-11-06,
  [blending RE](MM9_ACTOR_ANIMATION_BLENDING_RE.md), the section on strafe and fliers): the `Strafe` command never
  enters state 0x0d; it plays Run or Walk forwards within 100° of the facing, BackPedalRun or BackPedal beyond (a
  model without them gets Walk or Run in their lists). Strafe attacks and evade circles play the Run forwards: ours
  matches. A backpedal on a model without a backpedal clip plays its gait *forwards* in MM9 (a flier its `Flap`);
  ours played it reversed, and plays it forwards since 2026-11-06 (the plan's "Backpedal"). The Oculus's reversed
  lines above were that case.
- ~~The fliers' animator in flight~~ Answered (same section): fliers build their own animator, which keeps `Flap` on
  the main tracker (a flier always counts as moving) and puts the attack (`HAttackAir`, or `rAttack`) on the `Top`
  tracker, whose weight is 1 on every node: the whole body attacks; without `Top` the attack replaces the flight clip.
  Ours matches.
- Whether launching from his mouth socket makes the Dragon King too weak against flying targets in play (the arena
  now shows the window's fight: one hit on the mutant in 26 s).
