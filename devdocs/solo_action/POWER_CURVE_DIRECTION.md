# Solo run: the power curve, the early game and a bigger tree (direction, 2026-11-15)

A discussion record, not a build plan. The user asked for direction on the MAW solo run: how to make it smoother
without making it trivial, with MAW as the baseline and the solo rules on top. This file keeps what the user said,
what was measured in answer, what was proposed, what is undecided and the next steps. Nothing here is built in the
game.

**Taking this work over? Start with [HANDOFF_POWER_CURVE.md](HANDOFF_POWER_CURVE.md).**

**Read §6 first:** the simulator was fixed later the same day; its corrected results replace several figures of §2
and change the direction of §3.

Background: [BALANCE_AND_TALENTS.md](BALANCE_AND_TALENTS.md), [TALENT_TREE_V2_BUILD.md](TALENT_TREE_V2_BUILD.md) (the
tree as built), the [solo simulation](../maw/solo_sim/README.md), its [results](../maw/solo_sim/RESULTS.md) and
[proposals](../maw/solo_sim/proposals/README.md).

## 1. What the user said (2026-11-15)

Kept close to the user's words. Where a line is a wish and where a doubt, it says so.

**The aim.**
- The solo mode stays "entirely beside MAW": it never changes the MAW ruleset. "I 100 % want to retain using MAW as
  the baseline and use 'my' stuff as the things 'on top of'." MAW's rules "by its core need likely to be retained";
  "but we can override stuff".
- "Make this less hardcore", "smoother", "not ultra giga daunting to play and completable only with select few
  classes", and at the same time "NOT make it that it is trivial".
- The question as posted on Discord: "MAW is balanced around a full party of 5. Say the full party of 5 has a power
  level (tankiness, utility, damage, ...) of an imaginary 100. What power level does the solo play mode need?" The
  user knows it is not linearly comparable (in a party of five the healer gets instagibbed, and so on).
- **The benchmark (later the same day):** the solo run, taken as a whole, should be about as hard as a party of five,
  "or like 25 % harder or something, I don't mind", knowing that the challenges along the way differ and cannot be
  compared in percentages.
- **The goal is to clear the entire map, not 90 % of it,** because completing a map pays rewards.
- "The game could be like run and mow stuff, I guess, but at the same time I would not like for the party to never be
  in any kind of danger." Never being in danger may happen "when min-maxing in lower difficulties, or also a bit
  higher ones"; the user is not sure where that line should be.

**The early game.**
- "The start is ULTRA hard for the party of one early, like DAUNTING."
- Missile homing will be 100 % on, so missiles cannot be dodged except by peeking through geometry ("which is fine").
- In dungeons, and likely outdoors, it is very difficult to pull less than one group (in dungeons one group at the
  least), and a group may be ranged or mixed.
- **"Deterministically 'nerf' a bit the early game, somehow,** while expecting the talents and other stuff to catch up
  in further locations, and then make the curve make sense."
- Many players "cheese" the early game: they do everything that pays experience and gold without fighting. The
  user's examples: the MM6 scroll quest to Kilburn, Kilburn's shield (with Air and Gate masters), the Frozen Highlands
  council quest, perhaps MM8's dimension travel to finish the Dagger Wound Dadeross quest by going to Ravenshore.
- The user would accept this being "more or less mandatory for the highest difficulties but not for the 'maw'
  difficulty". The MAW difficulty is for experienced people who "know what's what": they should know about the
  Kilburn quest, training up and basic skill upgrades.
- Bow cheese is fine early, also for Knight classes: clearing New Sorpigal by picking groups or single monsters off
  with a bow (the islands with the C-tier monsters and bosses cannot be charged).
- "The absolute start might be a bit difficult", but the curve should then smooth out.

**Experience.**
- "There was recently some 'nerf' to the xp gain in MAW which screws solo play a lot? Maybe revert that or adjust
  that."
- A solo at the end of Beyond Madness "should be much much higher level than 500".

**Talents.**
- "I very much like the talents and I like the 'unlock' of the misc skills to other classes", for the flexibility it
  gives.
- "I would not mind probably having 1 talent per 5 levels and increasing the amount of the talents", as the thing
  that may help the curve and the clear speed. Front-loading the points: "sure, no problem".
- "We need a much bigger tree, like the PoE stuff, but I don't know how this all fits in." "Going level 1000, how many
  talent points would we need?"
- "The start would always be: get Regeneration, that's for sure, as that's quality of life which removes the need for
  spamming potions (annoying)."

**More active skills (later the same day).**
- "I am not against having more 'active' skills available (e.g. buffs or other types of attacks)." As a place to look
  for ideas the user named Divinity: Original Sin 2's skill schools ("way of the archer, way of the warrior"), and
  stressed this is spitballing: "NOT SAYING WE SHOULD USE THIS".
- "OK fix the simulator I guess" (the go-ahead for §4 step 1).

**The simulator.**
- "Very much imperfect." It "generated some level 500 character for the end of Beyond Madness".
- The gear it generated is suboptimal, "and that's very generous": in the generated saves the Knight had Intellect on
  the weapon, the weapon was "pretty low level", "and similar for all other gear".

## 2. What was checked in answer

All from the solo simulation's work directory (`output/maw_solo_sim/`, the run of 2026-11-14), before any talents
unless said. "Whole groups" = every monster of a map group attacks at once (no pulling apart), which is the user's
"cannot pull less than a group". The model never sidesteps a missile, which matches homing on. It credits no kiting,
terrain or bow opener.

### 2.1 The level-500 character and the level lead

The "level 500" character is not the end of Beyond Madness. It is the simulator's last checkpoint: map 126 of 189,
monsters at level 302–320. The simulated Beyond Madness run ends at **level 804 against level-500 maps** (MM6–MM8
only: no Chedian, arena or dimension maps, so the true end is higher). The hardest third of Beyond Madness has no
fight data at all.

Character level over map monster level along the simulated run (`route/out_<difficulty>.jsonl`, the trajectory rows):

| Maps cleared | Nightmare: character / monsters | Beyond Madness: character / monsters |
| --- | --- | --- |
| 15 | 41 / 16 (2.5) | 79 / 41 (1.9) |
| 43 | 138 / 56 (2.5) | 191 / 97 (2.0) |
| 71 | 230 / 116 (2.0) | 287 / 151 (1.9) |
| 99 | 295 / 153 (1.9) | 394 / 232 (1.7) |
| 127 | 358 / 170 (2.1) | 505 / 320 (1.6) |
| 155 | 415 / 196 (2.1) | 656 / 403 (1.6) |
| 183 | 478 / 240 (2.0) | 781 / 500 (1.6) |

The lead holds at about 2.0 on Nightmare and falls to 1.56 on Beyond Madness, where gear also stops improving near
item level 450–640 (a level past 500 is worth L³ instead of L⁶, proposals/README.md).

### 2.2 The early game in numbers

Share of whole groups beaten, typical build (median of the 22), without / with potions (`data_real.json`, fields `ok`
and `okp`):

| Difficulty | Level 10 | Level 50 | Level 200 | Level 500 |
| --- | --- | --- | --- | --- |
| MAW | 80 / 96 % | 96 / 100 | 97 / 97 | 100 / 100 |
| Nightmare | 35 / 87 % | 84 / 96 | 77 / 78 | 92 / 94 |
| Doom | 6 / 72 % | 64 / 88 | 85 / 88 | 50 / 50 |
| Road to Insanity | 1 / 58 % | 72 / 86 | 79 / 82 | 44 / 44 |
| Beyond Madness | 4 / 34 % | 31 / 64 | 29 / 42 | 1 / 1 |

- A sword-and-shield Knight at level 10: 57 % on MAW, 16 % on Nightmare, 3–7 % on Doom and above (without potions).
- Groups on the first maps are 4–6 monsters at the median and 20–26 at the largest. One monster takes about 2 s on
  MAW, 3–4 s on Nightmare and 6–14 s on Doom and Road to Insanity.
- Level 10 is the first checkpoint, after one to three maps are already cleared. Levels 1–9 are not measured and are
  worse.
- By level 50 (first promotion, masteries, gear) the start is over on everything but Beyond Madness.
- So the split the user describes already exists: MAW difficulty is playable by someone who drinks; Nightmare needs
  potions and care; Doom and above cannot be started head-on.

### 2.3 How large an early monster cut would be

[early_cut_sweep.py](../maw/solo_sim/proposals/early_cut_sweep.py): the factor by which monster HP and damage (both)
must be divided for a typical build to beat **90 % of whole groups without potions or talents**. Median build; the
script also prints the Knight, the Archer, the Arch Mage and the worst build.

| Difficulty | Level 10 | Level 50 | Level 200 |
| --- | --- | --- | --- |
| MAW | 1.3 | 1.0 | 1.0 |
| Nightmare | 2.3 | 1.2 | 1.6 |
| Doom | 4.3 | 2.1 | 1.2 |
| Road to Insanity | 5.3 | 2.1 | 1.5 |
| Beyond Madness | 11.3 | 3.5 | 3.3 |

For **100 % of whole groups** (every group of the ten maps around the stage, the largest taken at once):

| Difficulty | Level 10 | Level 50 | Level 200 |
| --- | --- | --- | --- |
| MAW | 7.3 | 1.6 | 1.6 |
| Nightmare | 10.0 | 2.6 | 9.4 |
| Doom | 16.7 | 4.0 | 2.2 |
| Road to Insanity | 14.8 | 4.3 | 6.7 |
| Beyond Madness | 26.2 | 6.6 | 5.8 |

Reading: the 100 % rows are set by single groups of 20–40 monsters. No sensible cut makes those beatable all at once,
so "the whole map cleared" has to be measured with those groups split and with drinks allowed (§4.2).

### 2.4 The experience "nerf"

- Below level 100 the curve is the old one (1000 × level per level). Nothing changed for the early game.
- MAW 5.0 added a surcharge past level 100: +1 % per level until MAW `ba572ec2` (2026-11-10), +0.5 % since
  (`experienceStep`, `game/rules/maw/MawExperienceCurve.cpp`). Before 5.0, solo Madness runs ended at levels
  1,600–2,025 ([DISCORD_DISTILL.md](../maw/solo_sim/proposals/DISCORD_DISTILL.md)); that is the "much higher than 500"
  the user remembers.
- The same total experience converted to a character level, if only the **solo character's** surcharge changes and the
  monster bank stays on MAW's curve:

| End of run | 1 % (5.0 before 2026-11-10) | 0.5 % (now) | 0.25 % | None (before 5.0) |
| --- | --- | --- | --- | --- |
| Nightmare | 435 | 503 | 570 | 743 |
| Road to Insanity | 408 | 469 | 528 | 674 |
| Beyond Madness, the "level 500" checkpoint | 434 | 502 | 568 | 741 |
| Beyond Madness | 675 | 804 | 941 | 1,434 |

  A lower bound: a higher level also loosens the per-kill award cap of (level + 1) × 1000.
- It is one number, costs nothing early and grows where late Beyond Madness falls apart. Removing it fully also makes
  late Nightmare much stronger.

### 2.5 The quest route ("cheese")

MAW pays a solo five times a quest's experience and adds the quest's experience once to the monster level bank
(`MawExperienceRules::eventExperience`). From level 1, with nothing banked elsewhere:

| Peaceful quest experience (sum of rewards) | Solo level | Monster bank level |
| --- | --- | --- |
| 5,000 | 7.6 | 3.7 |
| 10,000 | 10.5 | 5.0 |
| 25,000 | 16.3 | 7.6 |
| 50,000 | 22.9 | 10.5 |
| 100,000 | 32.1 | 14.6 |

It buys levels, HP and skill points, not gear or a promotion. Whether level 16–23 on starting gear is enough on Doom
and above is not known: the simulator has no such checkpoint. The rewards of the quests the user named were not
looked up.

### 2.6 The gear complaint: two different things

- **The saves do not wear the simulator's gear.** `testparty` (`game/debug/MawTestParties.h`,
  `assets_dev/engine/rulesets/maw/debug/test_parties.yml`) rolls one random MAW item per slot at one rarity and the
  stage's gear level. `solo_madness_500` is `gear: {level: 256, rarity: legendary}`, `stats: 99`, `skill_level: 91`:
  random enchants (the Intellect sword), every stat 99, every skill 91. `gen_solo_stages.py` wrote only the level and
  rarity (the median drop level and commonest rarity of the run's best loot). Those saves are weaker than what the
  simulator fought with.
- **The simulator's kit is still not a player's kit.**
  - It wears the best of 40 candidates per slot by damage × toughness and crafts with the materials it found.
  - The 40 are kept by rarity, then drop level, then enchant size (`SoloRoute.cpp:201`), never by which stats they
    carry, so a well-rolled item of a lower rarity is thrown away.
  - No shops, no rerolls (Pearl, Mirror and Orbs are not spent), no farming, bounties, arena or resets.
  - Its level-500 Beyond Madness Knight (sword and shield, seed 1): Might 1,295, Endurance 431, Intellect 403,
    Personality 454; 33.9k HP, 17.9k damage per second, against monsters of 70k HP that hit for 48.5k before
    mitigation (4.9k after the 10 % floor).
  - An earlier estimate put chosen enchants at about ×2 HP (proposals/README.md, "Choosing enchant types").
- **The item level of about 300 on a level-500 character is MAW**, not a fault: items drop at monster level.
- **The calibration was never run.** proposals/README.md asked first for a `realfight.py` run with a character at
  MAW's own expected power for its level; the model says that character should beat pulls of four, and 17 of the 22
  simulated builds do not. Until that is done, every Beyond Madness number is pessimistic by an unknown amount.

### 2.7 The tree as built against the points

- 19 talents, 65 ranks, two keystones, one point per 10 levels (`talents.yml`).
- A melee build wants 23 ranks (Arms 20 and Bloodthirst 3): done at level 230 at one point per 10 levels, at level
  115 at one per 5. All 65 ranks: level 650, or 325.
- So faster points without more to buy only strengthen the middle of the run, which is already fine, and leave the end
  as it is.
- With the tree as built, melee builds beat (pulled four at a time, no potions, level 500, weakest / median): Nightmare
  100 / 100 %, Doom 86 / 97 %, Road to Insanity 81 / 91 %, Beyond Madness 12 / 35 %
  ([TALENT_TREE_V2_RESULTS.md](../maw/solo_sim/proposals/TALENT_TREE_V2_RESULTS.md), last update).
- Beyond Madness at level 500 needs about ×3 combined power (HP × damage ÷ damage taken) over the tree for "tough but
  fair" and about ×6 to roll through (the Legend-point columns of
  [SOLO_RULES.md](../maw/solo_sim/proposals/SOLO_RULES.md) §4: ×1.5, ×1.5, ×0.78 and ×2, ×2, ×0.61). The gap is
  estimated to be about four times wider at the end of the route.

## 3. Proposed direction

Claude's proposals from the discussion. None is decided unless §1 says the user said so.

### 3.1 The target

- **Benchmark (user):** the solo run about as hard as a party of five, up to about 25 % harder, on the whole run and
  with whole maps cleared.
- As a first reading of "power": MAW sizes each monster against one character of the party's level, and a party is
  five of those. The solo classes that already play Nightmare well have about 2–3× that character's damage and 3–6× its
  staying power (BALANCE_AND_TALENTS.md §3.7): about half the party's kill speed and most of its survivability in one
  body.
- A feel band proposed before the user set the benchmark (pulled four at a time, no potions, typical build): Normal to
  Nightmare 95–100 % at 1.5–2 s per monster; Doom and Road to Insanity 85–95 % at about 2 s; Beyond Madness 70–85 % at
  2.5–3 s with potions mattering; the weakest class within about 20 points of the typical one. It should be restated
  against the party reference run (§4.1) and whole maps.
- **The shape of the problem:** the curve has two holes, the start (levels 1–30 on Nightmare and above) and late
  Beyond Madness (from about level 300). The middle is fine. The solo layer should fill the holes, not add power
  everywhere.

### 3.2 The start

- **Leave the MAW difficulty alone** (80 % of whole groups without potions at level 10, 96 % with).
- **A solo-run-only monster cut that fades,** tied to the map's monster level: full on the first maps, gone by
  monster level 25–30 (character level 50–60). MAW's balance model is not touched. §2.3 is the ceiling; potions,
  early talents and Regeneration cover part of it. First values to test: Nightmare ÷1.5, Doom and Road to Insanity
  ÷2, Beyond Madness ÷3.
- **On Doom and above the quest route stays the entry price,** as the user accepts. Target there: the Nightmare target
  after the route, not before it.
- **Front-loaded talent points** (user agreed): for example one every 2 levels up to level 20, so Cleave, Multishot or
  Blink arrive in the first hour.
- **Regeneration as the free root of the tree** at level 1: if everyone takes it first it is not a choice. Strong out
  of combat (it replaces the potion spam), modest in combat. Today Lone Discipline only makes it learnable at a temple.
- **Danger stays** if the target is 85–95 % with potions and not 100 %: the 20-monster groups and bosses still need a
  plan.

### 3.3 The late game

- **The experience surcharge for the solo character** as a solo-run override (§2.4). Start from 0.25 % and measure.
- **Back-load the tree:** the richest tiers only reachable past level 500. Nightmare ends near 503 and Road to
  Insanity near 469, so only a Beyond Madness run gets there, with no difficulty gate.
- Earlier accepted by the user (2026-11-14): Nightmare gets faster from ungated solo power (about 2.0 to 1.5 s per
  monster) while staying at 100 %.

### 3.4 A bigger tree

- **Rate:** one point per 5 levels, plus the front-load. Points: 10 at level 20, 26 at 100, 106 at 500, 166 at 804,
  about 206 at level 1,000.
- **What one build takes by level 1,000 (about 200 ranks):**

| Part | Ranks |
| --- | --- |
| The existing actives and skill talents | 25 |
| Cross-class skill unlocks (the user likes these) | 15 |
| Small nodes: +2 % HP, +2 % damage or −1 % damage taken | 120 |
| Notables (ten, three ranks each) | 30 |
| Keystones | free, one per 150 levels |

- **The whole tree about twice that (around 400 ranks),** so nobody fills it and builds differ, as in Path of Exile
  (small nodes leading to notables and keystones, in tiers opened by points spent).
- **Small nodes sell only what still scales in MAW:** HP, damage, sustain, and a damage-taken cut applied after MAW's
  10 % floor with a cap (the proposals' shared clamp, no lower than ×0.25 in total). Armour and resistance are already
  at the floor.
- **Size check:** 120 small nodes spread evenly give about ×2.2 HP, ×2.2 damage and ×0.67 taken, about ×7 combined;
  75 passive points at level 500 give about ×3.5. That is the size of the measured Beyond Madness gap (§2.7), before
  the simulator's gear is corrected.
- **Class spread through unlocks, not multipliers:** nodes that let a class learn a skill, or one mastery more of it
  (Dodging, Meditation, Armsmaster, Shield and the like, per weak class). They use MAW's own formulas, so the power
  stays inside MAW's scale. Measured for the Bodybuilding unlock: Death Knight 1 % to 22–38 % at Beyond Madness level
  500. The Priest (2 %) needs its own damage answer.
- The user dropped uncapped Legend lines on 2026-11-14. The small nodes are the same power as capped nodes with
  choices, paid by level points; whether that is what the user wants is open (§5).

## 4. Next steps (proposed order)

1. **Fix the simulator before sizing anything.**
   1. A player's kit: keep candidates by merit and not by rarity, an "optimised" mode with chosen enchant types and
      shop purchases at the same drop level, and the calibration against MAW's expected character of the same level.
      Report "found" and "optimised" as two bounds.
   2. **A party-of-five reference run** on the same route with the same fight model (characters at the bank level,
      the model's gear, five bodies, a healer). Without it the user's benchmark cannot be measured.
   3. **"Map fully cleared" as the measure:** per map, the hardest group beaten with splitting and drinks allowed;
      report the share of maps cleared and the potions and time per map, for the solo and for the party.
   4. **Checkpoints from level 1** (1, 5, 10, 20, 30) and every 100 levels to the end of Beyond Madness (now 804), so
      the curve is a line and not four points. Add Chedian when the route can carry it.
   5. **Start scenarios per difficulty:** straight from level 1, after the peaceful quest route (look up the named
      quests' rewards), and with a bow opener or kiting.
   6. **Inputs to sweep:** the solo surcharge, the early monster cut and its fade, the point rate and a node table.
   7. Make `gen_solo_stages.py` write saves that wear the simulated kit, so a save can be judged by playing it.
2. **Rerun, then size** the early cut and the surcharge from the gap between the solo and the party.
3. **Draft the tree** (about 400 ranks, the tiers, the unlock nodes, Regeneration as the root) against those numbers,
   with a talent-page study, since the page as built is three columns of rows.

## 5. Open questions

- **The benchmark's unit.** "As hard as a party of five, or 25 % harder" in what: potions per map, deaths, time per
  map, share of maps cleared without a reload?
- **Where danger should remain.** A min-maxed solo on the lower difficulties may never be in danger; is that
  acceptable, and from which difficulty up must it not happen?
- **The early cut.** Is a fading monster cut the wanted "deterministic nerf", on which difficulties (not MAW?), and
  should it be shown to the player? Should it key on the map's monster level or on the character's level?
- **The quest route on high difficulties.** Leave it as knowledge, or tell the player in the game?
- **The surcharge.** 0.25 %, none, or left as MAW has it; and is a faster late Nightmare still accepted?
- **The small nodes.** Are capped +2 % nodes acceptable where the uncapped Legend lines were not?
- **Regeneration.** A free root for everyone, or still learned (temple, class cap)? How strong in combat?
- **Homing.** With missiles always homing, should the solo run give a way to answer ranged groups besides geometry (a
  talent, a shield rule), or is peeking enough?
- **Pulling.** Should the solo run make smaller pulls possible (a lure, a quieter approach), or is "one group at the
  least" part of the intended difficulty?
- **The level at the end.** With Chedian, the arena and dimension maps the run ends above 804; what level should the
  tree be planned to (the user said 1,000)?
- **The page.** A Path of Exile-like web is a new screen; a tiered list is cheaper. Which?

## 6. After the simulator fix (2026-11-15, later)

Step 1 of §4 is done, except the "after the quest route" and "bow opener" start scenarios, shops beyond a plain weapon
and armour, and Chedian. Full results: [the curve results](../maw/solo_sim/CURVE_RESULTS.md). **The figures of §2.2,
§2.3, §2.6 and §2.7 above come from the old kits and are superseded;** the level trajectory (§2.1), the experience
surcharge (§2.4) and the quest route (§2.5) stand.

What the corrected run says:

- **The user was right about the gear.** The old pool kept items by rarity and then drop level (the best two-handed
  axe of a level-500 Knight was of drop level 55), left a slot empty when the loot had no weapon or armour of the
  kind (the level-10 stage fought bare-handed), and crafted without previews. Fixed, the level-500 Beyond Madness
  melee builds beat 15–86 % of groups pulled four at a time without potions, against 1–57 %.
- **The melee kits now match MAW's design numbers** (a party-level two-handed Knight kills a B-tier monster in 1–4
  attacks on Nightmare against MAW's 3.5). The casters stay far below MAW's expected HP.
- **Against a simulated party of five on the same route, the solo is behind only at the start.** Maps fully cleared,
  typical solo build against the party: at the start 67 % against 100 % on MAW, 16 % against 100 % on Nightmare, 0 %
  against 100 % on Doom and above. The solo draws level at level 10–20 (MAW to Nightmare), 30–50 (Doom, Road to
  Insanity) and 50–100 (Beyond Madness). From level 100 on it is level with or ahead of the party on every
  difficulty, drinks less and loses nobody.
- **Late Beyond Madness is a wall for the party too** in this stand-and-trade model (the party clears 12 % of the maps
  at stage 400 and 0–10 % after; the typical solo 32 %, then 0–10 %). It is Beyond Madness's own difficulty, not a
  solo handicap.
- **The early cut that levels the start with the party's is one curve for every difficulty:** monster HP and damage
  ÷2.5–2.9 at the start, ÷2.0–2.5 at level 10, ÷2.0 at 20, ÷1.8 at 30, ÷1.2–1.7 at 50, nothing at 100.

What that changes in §3:

- **§3.2, the start, is now the main job,** and its numbers are measured against the benchmark: one fading cut of
  about ÷2.7, the same on every difficulty (the first guess was ÷1.5 to ÷3 by difficulty), gone by character level
  100 (monster level about 40). The difficulty differences then stay exactly as MAW has them for parties, including
  "Doom and above need the quest route".
- **§3.3 and §3.4 are no longer needed for the benchmark.** By "as hard as a party of five" the solo already
  qualifies from level 100, late Beyond Madness included. The surcharge, the back-loaded tiers and the size of the
  small nodes are now a separate decision: whether a solo should find Beyond Madness *easier* than a party does.
  The bigger tree can then be sized for identity and choice, not to close a gap.
- **Casters** (Arch Mage, Master of Elements, Priest) are the class-spread problem on every difficulty, but they are
  judged without range; the range model has to run on the new kits before anything is concluded.

New open questions:

- Should the solo run make late Beyond Madness easier than a party finds it, or is "as hard as a party" the whole
  aim? (It decides the surcharge and the small nodes.)
- Is one fading cut of ÷2.7 for every difficulty wanted, or a smaller one on the difficulties where the start
  should stay a knowledge check?
- The party reference has two weak casters. Should the benchmark party be a sturdier one (it would raise the bar the
  solo is held to)?

Next steps, in order: (1) the early cut and the front-loaded points as solo-run data, to play; (2) the start
scenarios after the quest route and with a bow opener; (3) the range model (`talentfight.py`) on the new kits, for
the casters and the Archer; (4) a second reference party; (5) the tree draft.

## 7. The early cut settled, the party line and talent tree v3 (2026-11-15, evening)

**What the user said.**
- "Division by 2.5 in the early seems fine I guess for the solo, then taper off to 100 or something, up to you,
  maybe earlier?"
- "Then do some mockups for the talent trees etc.: the amount of points, what to put where, how it affects what
  and everything."
- "At no point, I think, should the solo char be better than a full party?"

**The party line** ([party_line_sweep.py](../maw/solo_sim/proposals/party_line_sweep.py), results in
[CURVE_RESULTS.md](../maw/solo_sim/CURVE_RESULTS.md) "The party line"). How strong the monsters may be for a solo and
for the party to beat 90 % of whole groups without potions; solo ÷ party, typical build, MAW alone:

| Level | Start | 10 | 20 | 30 | 50 | 100 | 150 | 200 | 300 | 400 | End |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAW | 0.35 | 0.46 | 0.45 | 0.44 | 0.63 | 1.04 | 1.21 | 1.69 | 1.97 | 1.72 | 1.47 |
| Nightmare | 0.34 | 0.49 | 0.54 | 0.56 | 0.66 | 1.13 | 1.20 | 1.31 | 1.55 | 1.68 | 1.35 |
| Doom | 0.27 | 0.42 | 0.46 | 0.51 | 0.69 | 0.78 | 1.32 | 1.42 | 1.64 | 1.73 | 1.95 |
| Beyond Madness | 0.28 | 0.33 | 0.34 | 0.46 | 0.81 | 0.53 | 0.90 | 0.96 | 1.52 | 1.00 | 0.93 |

So a solo starts at about a third of a party, crosses the party's strength between level 100 and 150, and stays at
1.3 to 2 times a party afterwards (Beyond Madness about level with it). By class at the end of Nightmare: Dragon
6.5, Troll 3.7, Seraph 2.5, Minotaur 1.6, Champions 1.2–1.4, Archer 1.0, Arch Mage 0.7, Priest 0.4. **Plain MAW
already breaks "never better than a full party" from about level 150** for every melee class and the Dragon.

**The early cut, as proposed for the solo run** (solo runs only, by the character's level, every difficulty; monster
HP and damage divided by it, linear between the points):

| Character level | 1–5 | 10 | 20 | 30 | 50 | 75 and up |
| --- | --- | --- | --- | --- | --- | --- |
| Divisor | 2.5 | 2.0 | 1.7 | 1.55 | 1.3 | 1 |

It starts at the user's 2.5 and ends at 75, earlier than 100: sized so that the cut times the early talents of an
ordinary build keeps the typical solo at or just under the party on MAW and Nightmare (0.86 at the start, 0.95 to
1.02 from level 10 to 50), and a little under it on Doom and above. Not built.

**Talent tree v3, the draft the mockups show**
([mockups and viewer](../../level_generation/ui/solo_talents_v3_20261115/README.md),
<https://claude.ai/artifact/BAHdNVgqL1aTPqvLiD4fFs>):
- one point every 2 levels up to 20, then one every 5 (206 at level 1,000); a keystone slot per 150 levels;
- Second Wind (Regeneration) free at level 1;
- five paths of five tiers: Arms, Archery, Arcana, Bulwark, Lore; 75 nodes and 395 ranks (the 19 built talents and
  56 new: 16 active skills, notables, small nodes of about 1 % a rank, six skill unlocks for any class);
- six new keystones that are trades;
- Deflect against homing missiles, Lure to pull one monster, Recuperate and Second Skin against potion spam, Bow
  Training for the bow opener.

**What the mockups make plain.** An ordinary build of the draft is worth about ×1.1 in monster strength at level 20,
×1.3 at 100, ×2.3 at 500 (estimates, not simulated). On top of MAW's own lead that puts a typical solo at 1.7 times
a party at level 150 and 3 to 4.5 times from 400. The user's rule and a tree with real numbers cannot both hold
unless one of these is chosen:
1. **A two-sided solo scale:** after level 75 a solo's monsters grow stronger by what an ordinary build is ahead (the
   last column of the party-line mockup: ×1.4 at 100, ×2.1 at 200, ×3 at 500). The tree then keeps a solo level
   with a party, as MAW's own model assumes skills.
2. **A tree of trades:** nodes move power between damage, toughness and utility with no net gain; MAW's mid-game lead
   stays as MAW made it.
3. **The rule binds only what the solo run adds:** where MAW alone already has the solo ahead, the tree is allowed its
   draft numbers anyway.

The simulated party is one composition with two weak casters, so its line may be low; that argues for starting any
upward scale well under the measured figures.

**Open decisions:** which of the three; what to do about the class spread (a Dragon at 4 to 10 times a party, a Priest
at 0.2 to 0.5); columns or constellation for the page; and the node values, which the simulation has to measure.

**Next steps:** the early cut and the front-loaded points as solo-run data (small, playable); the tree's nodes in the
simulation's fight model so the estimates become measurements; then the chosen way of keeping the rule.

## 8. Keep the built talents (user, 2026-11-15, late)

**What the user said.** "For now, the talents: I like them more as they are now. I don't want to implement some
additional skills or mechanics on top of what we have." "Let's stick with the 'simple' talents that we have now."

So talent tree v3 (§7, the mockups) is shelved as a study. The solo run keeps the built tree: 19 talents, 65 ranks,
two keystones, one point per 10 levels (one per 5 since the user's change on 2026-11-16).

**What the built tree is worth**, by the same rough build model as the mockups (estimates, not simulated; the
simulation's own talent runs still stand on the old kits): about ×1.03 in monster strength at level 20, ×1.09 at
50, ×1.15 at 100, ×1.28 at 200 and ×1.35 from level 300, where a build has everything it can use. The ×2.3 at level
500 quoted in §7 was the v3 draft, not this tree.

**Against the party with the built tree** (typical build, MAW alone × the tree): Nightmare 1.3 at level 100, 1.7 at
200, 2.1 at 300, 1.8 at 500; Beyond Madness 0.6, 1.2, 2.0, 1.8.

**The early cut for the built tree.** Its early talents add almost nothing, so the cut can follow the measured gap
and run to level 100: monster HP and damage divided by 2.5 up to level 5, 2.0 at 10, 1.8 at 20, 1.7 at 30, 1.4 at
50, 1.1 at 75, nothing from 100 (replacing §7's table, which made room for v3's early points).

**Built (user: "OK then let's do the first cut", 2026-11-15).** A MAW solo run only; a party of one in plain MAW and
every party game are untouched.
- **Data:** `early_monster_cut` in `assets_dev/engine/data_tables/talents.yml`, `[character level, divisor]` pairs,
  linear between them and nothing past the last (`SoloTalentTable::earlyMonsterCut`). Remove the list for no cut.
- **Level:** the higher of the character's level and the level its experience has earned
  (`MawSoloTalents::earlyMonsterCut`), so holding off training does not keep a larger cut. The rules hold the
  current divisor (`MawRules::soloMonsterCut`), set when the character's bonuses are applied and on every class
  update.
- **Effect** (`MawCombatRules`, two stages named `solo-early-cut`): a monster's hit on the character is divided
  right after MAW computes it, before armour, resistances and the class's flat cut (falls and traps are not cut);
  the character's hits on monsters are multiplied last of all. That is the monster's damage and HP both divided,
  without changing the monster's own HP, its experience, its loot or what the inspect screen shows.
- **Not shown to the player** anywhere yet: monsters' sheets show MAW's numbers, and the damage the character deals
  reads higher (the status line and floating numbers show the multiplied hit).
- **Checked:** `tests/SoloTalentTests.cpp` (the table, the fade, earned levels) and `tests/MawGapTests.cpp` (both
  stages, falls, monster against monster, a game that is not a solo run); the 364 MAW and solo unit cases pass.
  Headless, a level-50 Knight's blows on Nightmare land for 1.37 times their roll and a level-100 one's for 1.0;
  plain MAW with one character lands the roll.

**Still open:** whether a solo's monsters should grow stronger after level 100 so that a solo is never ahead of a
party (about ×1.3 at 100, ×1.7 at 200, ×2 from 300 on Nightmare), or whether MAW's mid-game lead stays as it is.

**Lowered after the first play (user, 2026-11-15, night).** The user at level 15 on Nightmare, Misty Islands
(`oute2.odm`), a Dark Elf with a bow and Expert Regeneration: "they can't really kill me even if I am not careful
with pulling". Checked on a copy of the quicksave, headless:
- the cut was 1.9 as the table said (monsters of level 3, 5 and 7 with raw hits of 10.5, 15.9 and 23.9; the hits
  of 3 to 7 on screen fit);
- next to Bounty Hunters (level 5) the character lost 0.4 HP a second against one, 1.9 against two, 7.4 against
  four and 22.8 against eight, of 170 HP; one Bounty Hunter did about 3.9 HP a second with the cut, 7.3 without;
- Regeneration gave about 6 to 8 HP a second in combat (an estimate from those runs) and about 30 out of combat;
- four Assassins (level 7) killed the character from full HP inside 3 seconds in two of six tries.

The simulation that sized the cut has no Regeneration on its bow build (Lone Discipline's Regeneration came after its
builds) and no ranged play, so the cut was too generous for such a character. New table, built: divisor 2.5 at
level 1, 2.0 at 5, 1.6 at 10, 1.4 at 20, 1.25 at 30, nothing from 50. **Still to do:** give every simulated build
Lone Discipline's Regeneration, rerun the curve and the party line, and size the cut from that.

**The simulation with Regeneration (user: "then add regeneration there I guess").** Done: the solo builds train
under Lone Discipline and the curve was rerun ([CURVE_RESULTS.md](../maw/solo_sim/CURVE_RESULTS.md), "Rerun with Lone
Discipline"). Regeneration moves the early solo little (typical +0.03 to +0.08 of a party up to level 50). Toe to
toe against whole groups the simulation still asks for about ÷2.6 at the start, 2.0 at level 10, 1.7 at 20, 1.6 at
30 and 1.4 at 50 to equal the party on Nightmare: close to the first table, above the lowered one in the game. The
gap to what the user felt is range (a bow user never stands in the whole group) and the benchmark itself (the party
is hardly ever in danger at those levels, so equalling it is soft). The lowered table stays, by the user's play; a
melee solo will find the start harder with it than the bow user did. Missing from the model: a ranged approach.


**The tail lengthened (user, 2026-11-15, night).** "Make it linear to like the 75 as you proposed, 1.4 at 50 if
that's how it should go." Built: divisor 2.5 at level 1, 2.0 at 5, 1.6 at 10 (the start as play set it), 1.4 at 50
(the simulation's number), nothing from 75. Linear between the points: about 1.58 at 15, 1.55 at 20, 1.5 at 30, 1.45
at 40, 1.24 at 60. Against the lowered table that is the same up to level 10, a little more from there (1.55 instead
of 1.4 at 20, 1.5 instead of 1.25 at 30) and a cut that lasts to 75 instead of 50.

**The experience surcharge halved for solo runs (user, 2026-11-15, night).** "Did we already halve the MAW 5.0 xp
penalty? ... for solo play only." "Yes, 0.25 % for solo only." It had not been: MAW itself went from 1 % to 0.5 % for
everyone (`ba572ec2`). Built:
- **Data:** `experience_surcharge: 0.0025` in `talents.yml` (`SoloTalentTable::experienceSurcharge`); without the line
  a solo run trains by MAW's curve.
- **Curve:** `MawExperienceCurve` is a class with its surcharge; `mawExperienceCurve()` is MAW's 0.5 %. In a solo run
  `MawRules::characterCurve()` is the same curve at the table's surcharge, and `MawExperienceRules::
  experienceForNextLevel` (training, the level a character can reach) goes by it. Level 200 to 201 costs 250,000
  instead of 300,000; nothing changes up to level 100.
- **Unchanged:** the continent banks and monster levels stay on MAW's curve, and a kill's award reads the member's
  level on MAW's curve, so the solo earns what MAW gives and only turns it into more levels (§2.4's table: a Nightmare
  run ends near 570 instead of 503, Beyond Madness near 941 instead of 804, as lower bounds). The early cut is not
  touched (it ends at 75, the surcharge starts at 100). Existing solo saves past level 100 can simply train further.
- **Checked:** `tests/MawGapTests.cpp` ("A solo run's experience surcharge ..."), `tests/SoloTalentTests.cpp`; the
  MAW, solo and experience unit cases (384) and the `rulesets/maw_test_parties` scenario pass.
- **Not in the simulator** yet: its curve (`scripts/gen.py` `step`) is MAW's 0.5 % for every case.
