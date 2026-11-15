# Solo action mode: the Dragon in first person

What a Dragon character shows and does in solo first-person play. It covers two claws for melee and the fire breath at
range. A study (2026-11-13), built on 2026-11-14: our own forelegs are installed and a dragon in a solo run draws them
(see "Built in the engine" below). No rule changes were needed.

## What the rules already do

Damage, hit and recovery stay with the MM rules; the view model only shows them.

- **Who is a dragon:** `ClassRules::isDragon`; MAW goes by the portrait's race. A dragon cannot wield weapons or wear
  body armour, so the view model never has a weapon or shield to show.
- **Items:** MAW counts a dragon's items (stats, HP, armour, resistances, Scales and Fangs) three times over; in a solo
  run 2.5 times (user's decision, 2026-11-14; `MawItemRules::applyEquippedEnchantEffects`, test in `MawGapTests.cpp`).
- **Attack key:** one attack per press, and the range decides which (`choosePartyAttackMode`):
  - A target in melee range takes the **melee attack**. In Standard it is the unarmed formula. In MAW it is **Fangs**
    (Unarmed renamed): damage and attack per Fangs level, and its recovery slows by ×(1 + 0.015 × Fangs).
    Once Dragon Ability ≥ Fangs, the blow throws the target back along it (`MawCombatRules` knockback).
  - Anything further takes the **breath**, `CharacterAttackMode::DragonBreath`, which needs Dragon Ability.
- **The breath** (`GameMechanics` attack profile, `GameplayActionController`):
  - Rules: it always hits; Irresistible damage of 1–10 × Dragon Ability in Standard; MAW uses its breath rows,
    critical hits, and the monster's lowest resistance.
  - Recovery: base recovery 100, and in MAW ×(1 + 0.015 × Dragon Ability).
  - Projectile: a FireBolt spell projectile. It leaves from the party point, lowered to `DragonBreathSourceHeight`
    (96).
  - Look and sound: it uses the plain `fire_bolt` effects; sound `SoundId::DragonBreath`.
  - MAW's Bow preference off (`bowDisabled`) turns the breath into the melee attack.
- **Dragon Abilities spells** (the Dragon Ability school, `spells.txt` 122–125). These are ordinary spells today:

  | Spell | Mastery | What it does |
  |---|---|---|
  | Fear | Normal | Fear; an area at Master, every creature in view at Grandmaster |
  | Flame Blast | Expert | A fireball-like explosion; MAW: 70–100 % of the breath |
  | Flight | Master | Flight (Fleet Foot in MM9) |
  | Wing Buffet | Grandmaster | Pushes opponents back |

  The spellbook, battle orders and quick keys already cast them, so they can go straight onto the action bar.

## On screen

**Idle:** two forelegs low in the lower corners, talons forward, breathing with the idle. No snout or head: from a
dragon's eye the head is behind the camera (see the check below).

**Claws (melee):**
- Swipes alternate right, left, right, like the Oblivion hand-to-hand set the arms use. As timing reference, its
  clips run 0.67 s, with Hit at 0.20 s and the chain to the other side at 0.43 s (`a:L`/`a:R`).
- Each swipe is one MM melee attack, held until its Hit like the weapons are (`ViewModelLink`).
- Every third chained blow can be a **bite**: the claws part and the jaw edge lunges up from the bottom of the view.
  It is visual only, the same melee attack. In MAW it matches the skill's name, Fangs.
- The hit effect: a three-streak **claw rake** drawn along the talon tip's path. That is a variant of the slash effect
  in `tools/fx/generate_melee_effects.py`; today an unarmed blow draws a crush.

**Breath (ranged):**
(Superseded on 2026-11-14: the breath now fires at once with no inhale; see "Built in the engine", item 3.)

1. **Inhale**, about 0.35 s: the forelegs drop out of the view, the bottom edge warms orange, a little heat shimmer.
2. **Release** at the clip's Hit: the projectile leaves from a mouth point just below the crosshair (first planned at
   the bottom centre of the view; see "The mouth point" below), with a short camera kick and an orange flash.
3. **Recovery:** the forelegs come back up.

Two details for the breath:
- The breath's flight should use the dragons' own look (`dragon_fire` flight, `fire_large` impact, warm light), not
  the small fire bolt. That needs a party-side binding in `projectiles.yml`: today only monsters' pictures have
  variants.
- The breath stays one projectile with an always-hit roll. A held cone that sweeps with the aim (Skyrim's Flames,
  Elden Ring's dragon breath) would need new rules (damage per tick, an area). It is offered below as a Grandmaster
  special, not as the basic breath.

**Movement:** the forelegs bob with walking and running, from the view model's existing movement loops. Flight could
use a slow glide loop with the claws tucked.

Comparable games:
- Skyrim's werewolf: two clawed arms, alternating swipes, a power attack with both, a howl on a key. It is the closest
  match.
- *Aliens vs. Predator*'s Alien: claws, a jaw lunge and a tail attack seen from the eye.
- Skyrim's Fire Breath shout and Flames spell: a cone, and a held stream.
- Elden Ring's Dragon Communion: breath from the head, sweeping with the aim.

## Systems that carry it

| Need | Existing system | Change |
|---|---|---|
| Clawed forelegs on screen | `FirstPersonViewModel` | A new set, `Claws`: `kitFor` gives it to a dragon, with no weapon or shield. Clips `claws<action>` (`clawsidle`, `clawsattackright`, `clawsattackleft`, `clawsbite`, `clawsbreath`, `clawsforward` …) with the same text keys (`Hit`, `a:L`/`a:R`, `Blend: N`). |
| Hit only at the blow | `ViewModelLink` swing-then-hit | Melee works as it is. The breath needs the same wait: the `DragonBreath` attack runs at the breath clip's Hit, as melee now waits for the swing's Hit. |
| Direction of the hit effect | `MeleeContactEffectInput::blowDirection` | The talon tip node (`ClawTipR`/`ClawTipL`) takes the blade tip's place. Claw rake effect variant. |
| Breath start point | `dragonBreathSourcePoint` | Raise or keep the source to match the mouth point on screen; optional. |
| Breath look | `projectiles.yml` | A party/dragon binding for the breath's flight and impact. |
| Fear, Flame Blast, Flight, Wing Buffet on keys | Spells, battle orders, action bar | None beyond the action bar. Each plays `clawsbreath` (Flame Blast) or a roar or wing cast clip. |

## Art route (own art only)

Oblivion has no dragon arms, and nothing Oblivion may go into anything shippable. Two routes:

1. **Cut from the installed MM8 Dragon (`mm8_m492`): prototype only.** The check below kept just the foreleg vertices
   (1,736) of the 10,051-triangle body and raised them by IK in front of an eye between the shoulders.
   - It reads as a dragon at once.
   - Not shippable as it is:
     - The forelegs share the body's 2K atlas, so at view-model distance the scales are blotchy and the silhouette
       faceted.
     - Each leg has three bones (upper, lower, foot): the talons cannot curl or spread.
     - The legs are a quadruped's and far too short to reach in front of the eye.
   - The view model is a separate first-person rig anyway, as Oblivion's arms are, so that last point costs nothing.
2. **Dedicated first-person forelegs: the shippable route (recommended).**
   - **Reference images:** Codex HD master images of one dragon foreleg from the MM8 Dragon art. The step-0 rule of
     the creature playbooks applies.
   - **Mesh and texture:**
     - A Meshy model of one foreleg from shoulder to talons. It is mirrored for the other side, about 8–12k triangles
       for the pair.
     - One 2K texture set with colour ramps per dragon tint, following the creature textures rule.
     - The texture quality pass applies.
   - **Rig:** our own, with shoulder, upper, lower, wrist and four digits of 2–3 bones each, plus a `Camera01` eye and
     the talon tip nodes.
   - **Clips:** keyed in Blender, procedurally as the quadruped playbook does. The timing numbers above are a
     reference only; no Oblivion data is used.
   - **Cost:** about 25–40 Meshy credits; the MM6 lizard took 25. Plus a few hours of rigging and clips.
   - **Snout/jaw piece:** a small one for the bite and breath is optional, from the same job.

A cheap private feel test before any art work: attach the cut MM8 talons rigidly to the Oblivion hands in the private
proof of concept. That puts them on Oblivion's hand-to-hand swipes in game. It is never shipped, and it needs a small
attachment addition to the view model.

## Check (private renders)

`level_generation/solo_action_dragon_20261113/`:
- `scripts/render_viewmodel.py` cuts the forelegs out of `mm8_m492` and poses them by IK. It renders 1600×900 frames
  at the view model's 60° field of view, with a transparent film.
- `renders/comp_*.jpg` composite those frames over the HUD study's New Sorpigal scene: guard, right wind-up, right
  hit, left hit. `comp_sheet_v1.jpg` holds all four.
- `renders/reach_and_density.jpg` shows two things: the legs at full IK stretch from the side, and the foot at
  view-model distance (texture density).
- `scripts/render_fp.py` holds the eye-on-the-head attempt. From the brow, neither the snout nor the legs enter a 60°
  view: the snout is 51° below the eye line. So the body's own geometry cannot be the view model, and nothing of the
  head shows except during a bite or breath.

## Built: the first-person forelegs (2026-11-14)

The dedicated route is built as a candidate in `level_generation/solo_action_dragon_20261113/` (its README has the
pipeline, the clip table and the paid-job ledger):

- **Art, our own.** Codex HD masters of one right foreleg from the MM8 Dragon (charcoal scales with red seams, a gold
  scute strip, four digits, a wrist spur, ivory talons). The mesh is Meshy Smart Topology (6,664 triangles per leg),
  UV'd with the shared atlas and textured by a Meshy retexture from the masters. The left leg is the right one
  mirrored.
- **Rig and clips, made in Blender by script** (`scripts/build_forelegs.py`). Landmarks come from the mesh. One
  armature holds both legs, the eye and the contact nodes. Clips are keyed through IK targets and baked:
  - idle, walk and run bobs;
  - right and left rakes at Oblivion's hand-to-hand timing, as numbers only;
  - equip;
  - a Scales guard and its hit;
  - the breath (inhale, release, kick);
  - a bite lunge.
- **Checked in Blender** from Camera01 (`renders/forelegs_v4_sheet.jpg`) and **in game** on a MAW solo run
  (`renders/ingame_sheet.jpg`, from `tours/claws_ingame.yml`). The game check uses `export/dragon_forelegs_h2h.glb`:
  the same motion under the unarmed (handtohand) names, which today's engine plays on an unarmed kit. At the Hit, the
  claws cross the centre onto the target, and two live swipes kill a goblin.
- **Cost:** 15 Meshy credits (Smart Topology 5, retexture 10).
- **Space:** the view model's space looks along +Y with screen right +X (the Oblivion arms' `ZupToYup` root). A GLB
  authored looking along -Y loads but draws nothing: it sits behind the eye. Anyone making held models or own arms
  should know this.

### Engine changes to adopt it (made on 2026-11-14: "Built in the engine" below)

1. **A `Claws` weapon set.**
   - `FirstPersonViewModel::WeaponSet::Claws` with `setPrefix` → `"claws"`.
   - `kitFor` (or `GameApplication`'s kit choice) gives it to a dragon member: `ClassRules::isDragon`, and MAW's
     race check. No weapon, no shield.
   - The loader's `handtohandidle` requirement should accept `clawsidle` when the GLB is a dragon set. Or load the
     dragon set as a second view model: the arms GLB for humanoids, `dragon_forelegs.glb` for dragons.
2. **Slash direction.** For the claws, `bladeScreenPoint` reads `ClawTipR` on a right swipe and `ClawTipL` on a left
   one, instead of the weapon model's far end.
3. **Breath like a swing.** `CharacterAttackMode::DragonBreath` waits for `clawsbreath`'s Hit through `ViewModelLink`,
   as melee and the bow's Release do. The press starts the clip, and the projectile leaves at the Hit.
4. **The mouth point.** The breath's source moves to the view model's `Mouth` node mapped into the world: 10 units
   forward and 16 below the eye in the arms' space. `dragonBreathSourcePoint` can take that point instead of party
   height 96, so the projectile visibly leaves the bottom centre.
5. **Look and feel.**
   - The breath binds its own recipe through a recipe override in `GameplayPartySpellProjectileRequest`, as
     `effectSoundIdOverride` does. Options: `projectiles.yml`'s existing `dragon_breath` (the `flame_gout` flight,
     the `fireball` impact, a warm light), or the monster dragons' `dragon_fire` with `fire_large`.
   - The release gets a camera kick (`GameplayActorHitFeedback::triggerCameraKick`).
   - The inhale gets a warm screen edge: an orange radial vignette drawn after the arms, with alpha following the
     clip from 0 to 0.4 s, gone by 0.6 s.

## Built in the engine (2026-11-14)

**How to see it.** Start a MAW solo run with a dragon: on the New Game screen choose MAW, tick "Solo run" on the party
roster and make a Dragon (MAW's dragon race portrait), or in an existing solo run use the debug console's
`testparty apply early solo_dragon` (a level-20 dragon, `assets_dev/engine/rulesets/maw/debug/test_parties.yml`). A
whole new game from the console: `testparty early solo_dragon solo`. Under Standard, a solo run with the Dragon (or
Great Wyrm) class shows them too. For example:

```sh
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated dragon --world mm6 --map oute3.odm --ruleset maw:solo \
  --set debug.console=true --visible --seconds 0
# then, in the console (~): testparty apply early solo_dragon
```

Checked with the tours in `level_generation/solo_action_dragon_20261113/tours/`: `claws_engine_oute3.yml` (the knight's
arms, the swap to the forelegs, held poses, a held-Attack fight and a breath at range), `claws_engine_6d05.yml` (the
same indoors, the guard on the real block button), `claws_engine_live_slow.yml` and `claws_engine_breath_slow.yml` (a
claw fight and a breath at a quarter speed, so the rake and the release are caught); their headers hold the commands.
Captures in `level_generation/solo_action_dragon_20261113/renders/engine/`, the overview `renders/engine_sheet.jpg`.

What was built, item by item:

1. **Install and kit.** `scripts/build_forelegs.py --install <OpenYAMM checkout>` installs the export as a view model
   source (`assets_source/engine/view_model/dragon_forelegs.glb`, `tools/install_model.py --view-model`) cooked into
   `assets_dev/engine/view_model/`, with its text keys beside the cooked copy. The forelegs are a second view
   model (`GameApplication::m_dragonViewModel`): a member for whom `ClassRules::isDragon` holds (MAW: the portrait's
   race) gets `FirstPersonViewModel::dragonKit()` (`WeaponSet::Claws`, prefix `claws`, no weapon, shield or bow) on
   `packagedModelPath()`'s forelegs; everyone else the arms as before. A change between the two (another member, a
   loaded game) lands a waiting blow and `resume()`s the other model, which reads the serials afresh and plays
   `clawsequip`. The loader accepts `clawsidle` in place of `handtohandidle`. The `viewmodel` console commands (pose,
   clips, trace, fx, path) act on the model shown.
2. **Slash direction and the claw rake.** For the claws `bladeScreenPoint` reads `ClawTipR`/`ClawTipL`, and the blow
   follows the talon that travelled further. A dragon's blows (`MeleeWeaponClass::Claw`, for any dragon, solo or not)
   draw `openyamm:fx/melee/claw*`: three thinner arcs side by side, staggered, from `tools/fx/generate_melee_effects.py`
   (`claw_recipe`; it reuses the arc sprites, so nothing new is cooked). The bite's rake runs down the screen.
3. **The breath fires at once (user, 2026-11-14).** At the press, a dragon whose target is out of claw reach
   (`GameplayActionController::partyAttackTargetInMeleeReach`, the same target choice as the attack) breathes at once,
   as a party dragon does: no swing wait and no inhale clip, and the forelegs stay as they are. First built as a swing
   (the forelegs played `clawsbreath` fitted to the breath's recovery and the breath left at its Hit, from the mouth),
   but the inhale and the gout never agreed on screen: at the bottom edge the gout seemed to leave from the crosshair
   (from so close below the eye it reaches the target's height on screen within about 70 units), and just below the
   crosshair the two still read as separate. The user chose to skip the windup. Battle orders holding a spell still
   show that cast.
4. **The source point.** The breath leaves where a party dragon's does (`dragonBreathSourcePoint`: the party's ranged
   source, no higher than 96 units above the feet). Flame Blast and other target spells cast from the forelegs still
   play the breath clip, their glow just below the crosshair (`breathPoint()`, `BreathScreenHeight`), since the camera
   is the dragon's eyes and its jaws are just below them.
5. **Look and feel.** The breath is exactly a party dragon's: a Fire Bolt by the rules and in looks (`fire_bolt`
   flight, `fire_small` impact), with the dragon breath sounds. In a solo run it kicks the view up by 0.035 rad (with
   `meleeCameraKick` on). On 2026-11-14 it briefly wore Dragon Breath's `flame_gout` look for every party dragon (a
   presentation spell, a `presented_impact`, a gout grown from the mouth with a flame ribbon); the user found party
   games changed and the gout morphing from a bolt into a ball, so all of it was taken out again.

Defaults chosen for the open decisions (changeable):
- **Bite:** the combo's fifth blow, the power attack's slot (`clawsAction`: right, left, right, left, bite). Visual only,
  the same melee attack. A slow recovery no longer breaks a combo: a blow within a second of the member being ready
  again continues it (a MAW dragon's recovery is about 1.8 s, longer after a blow taken), for the arms too.
- **Basic breath:** one fire bolt as now.
- **Block:** none. The held block was removed from the solo run (user, 2026-11-14); the Scales guard clip
  (`clawsblockidle`) stays in the model for a talent that holds it.
- **Tint:** one (the charcoal and red of the masters).
- Talents: out of scope.

Seen in the captures: the rakes cross onto the target and the claw rake (two or three staggered streaks with the blood)
follows the talon; the breath flies as a party dragon's Fire Bolt. MAW's dragon blow throws a light
target out of claw reach (Dragon Ability at or above Fangs), so the next press breathes; that is the rules, and the
forelegs follow it.

Not done: the jaw mesh for the bite (only the eye lunges), the player dragon's colour ramps, a heat shimmer, the roar
and wing clips for Fear and Wing Buffet, and a live capture of the bite (the test targets died by the fourth blow; the
bite is checked as a held pose and by the combo test).

## Special skills for the action bar

The four Dragon Abilities spells go on the bar as they are. New talents, which need rules, by school:
- **Fangs** (Unarmed):
  - **Rend** (Expert, passive): claw hits bleed.
  - **Tail Sweep** (Master, active): strikes everything in a half circle around and knocks it down; it is the dragon's
    cleave.
  - **Pounce** (Grandmaster, active): a leap to the target, the dragon's Charge.
- **Scales** (Dodging in MAW):
  - **Harden Scales** (Master, active): the dragon's Shield Wall, since it has no shield to block with.
  - The block button raises the forelegs as a guard; it reduces damage only if Scales is learned.
- **Dragon Ability:**
  - **Roar** (Expert): Fear on everything in front, taking Fear's slot as the shout.
  - **Searing Breath** (Grandmaster, active): the held cone, about 3 s on a long cooldown, spending SP each second.
  - A dragon's SP refill timer (`dragonSecondsSinceLoss`) already exists.

## Open decisions

Defaults were chosen on 2026-11-14 ("Built in the engine"); each can still change:
- Bite: the fifth blow of the combo now; a dedicated Bite key instead?
- Basic breath: one fire bolt now; a short cone needs new rules.
- Breath look: the `dragon_breath` recipe now; the monster dragons' `dragon_fire` and `fire_large` are the other option.
- The Scales guard: unused since the held block was removed; a talent (Harden Scales) could hold it.
- Tint: one now; the player dragon's colour ramps later.
