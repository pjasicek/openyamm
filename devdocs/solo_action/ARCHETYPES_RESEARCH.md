# Solo archetypes: paths, the melee identity and a proper caster (research, 2026-11-18)

Research and a proposal for the MAW solo run's talents. **Built on 2026-11-18** as the user asked after the last
round of decisions: [ARCHETYPES_BUILD.md](ARCHETYPES_BUILD.md) says what is in the game and where the build differs
from this text. The user asked (2026-11-18, from a Discord thread with rough ideas for the melee archetype):

- how to make the melee archetype playable "with a lot of monsters focusing down the melee classes";
- whether talents should be picked as **archetypes** ("enable only that path until respec, so that sorcs can't take
  tanky talents from Arms, or archers");
- something "proper" for the sorcerer and caster classes, whose tree "was basically never tried" and "feels
  lackluster";
- with the archer as the reference for power and fun ("ultra fun now ... on Nightmare on big level in the dim maps").

The page for reading it: [ARCHETYPES_RESEARCH.html](ARCHETYPES_RESEARCH.html), published privately at
<https://claude.ai/artifact/2E3pJcThRn2BEGkyqtTzHe> (republish that file after a change). Background:
[the tree as built](TALENT_TREE_V2_BUILD.md), [talent interactions](TALENT_INTERACTIONS.md),
[the power curve record](POWER_CURVE_DIRECTION.md), the
[v2 simulation](../maw/solo_sim/proposals/TALENT_TREE_V2_RESULTS.md) and the shelved
[tree v3 study](../../level_generation/ui/solo_talents_v3_20261115/README.md).

Every statement below is marked by where it comes from: **code** (read in the source), **save** (the user's archer),
**sim** (the solo simulation, a model), **user** (decided by the user) or **proposal** (new here, numbers are first
values to tune in play). Distances are in game units (§0.3).

## 0. Where it stands

### 0.1 Decided (user, 2026-11-18, in four rounds after the first version of this document)

| | Decision | In the user's words |
| --- | --- | --- |
| The lock | One path per character, a hard lock | "hard lock" |
| The reset | Stays free | "talent reset stays free" |
| Onslaught | Moves to the Any tree with five ranks of 6 % (30 % at rank 5). It speeds every recovery, spell casts included | "onslaught to any, yes, 5 points into it, 6% each. it should be global recovery i think so also for spellcasters" |
| Shield Wall | Removed entirely | "shield wall - id remove it entirely" |
| Vanguard | 20 / 40 / 60 % by rank (80 % at the last rank until the user played it), on shots loosed from more than 800 units away; a monster's spells count as its missiles do | "vanguard - make it 20/40/60" (after "vanguard lets do 80 at first"); "vanguard radius 800, yes spells count as missiles" |
| Challenge, Grapple | Challenge is in, on every hostile that has noticed the character (not a radius). No Grapple, no Death Grip | "challenge for now is good, no grapple, no death grip"; "every hostile currently agroed" |
| Battle Frenzy | Counts the monsters nearby, not every monster that noticed the character; with Outnumbered within 768 (MAW's 512 until the user played it) | "only those nearby I think"; "make it 768 range" |
| The rage bar's place | An arc round the right side of the portrait (the user's sketch), not a third bar under SP | "rage bar should be here if possible" |
| Rage | Arms gets its own bar that fills from damage dealt and taken, at most about 20 a second. Its abilities are used on a **full bar**; the rest as proposed | "a separate 'rage' bar, which would fill when taking damage or dealing damage ... at max some limit, like max 20/s"; "rage - on full bar instead now. otherwise rage your proposed ok I guess" |
| Arcane Ward | In | "sure" |
| Resolve | Replaced by Arcane Ward | "sure"; confirmed: "yes" |
| Opening Volley | In, at 15 / 30 / 45 % | "mage - opening volley ok, but 15/30/45% instead I think" |
| Tree sizes | The three paths have the same number of talents | "archer/arms/mage should have I guess same amount of talents" |
| Distances | Given in game units | "tell me ingame units not meters" |
| Long Shot | Scales with distance: nothing under 1,536, rising to +3 / 6 / 9 % at the bow's full range (5 / 10 / 15 % until the user played it) | "scaling, +5/10/15% more dmg at max range, no bonus when less than 1536"; then "make it only 3/6/9%" |
| Hamstring | A critical strike slows the monster's movement, and only its movement, by 5 / 10 / 15 % for 3 s, not stacking | "critical strikes slow by 5/10/15% (non-stacking) for 3s"; "movement only" |
| Expose Weakness | Replaces Hunter's Mark: a critical strike exposes the monster, which takes 3 / 6 / 9 % more damage for 5 s (5 / 10 / 15 % until the user played it; "make it only 3/6/9%") | "i dont like this, Expose Weakness - critical strike on the enemy exposes its weakness, increasing damage done to target by up to 5/10/15% for 5s" |
| Shatter, Breach | Shatter is out. Breach takes its place: spells ignore 5 / 10 / 15 % of a monster's resistance | "arcana - something other than shatter, since that wouldnt have much effect"; "make the pen 5/10/15% instead" |
| Heroic Strike | 300 % (read as the last rank: 200 / 250 / 300; say so if a flat 300 at every rank was meant) | "300" |
| The mage | The user's thoughts: close to the archer but with spells; survivability and chaining have to be solved; "maybe like bigger recover, harder hitting" | §4.2 answers this with "artillery"; not objected to |

### 0.2 Short answers

1. **The path lock** is a hard lock with a free reset (user): one of Arms, Archery or Arcana at a time, the Any tree
   open to all. The reason is the point budget: a tree costs 15 to 17 points today and the reference archer has
   145. §2.
2. **Arms: "the pack is your armour", and it fights on rage.** Safest and strongest in the middle of the pack,
   weakest strung out between shooters. Vanguard, Outnumbered, Battle Frenzy and Challenge are the pack talents; two
   of them copy legendary affixes MAW already has. A rage bar filled by blows and by hits taken, when full, pays
   for one Heroic Strike or one Demoralizing Shout. §3.
3. **Arcana: artillery.** Same place on the field as the archer (at range, pulling with care), opposite tempo: few
   large casts where the archer has many small shots. The first volley decides the fight and the SP bar is the health
   bar. The present tree is weak by plumbing more than by concept. §4.
4. **Nine talents a path.** Arms has nine after Shield Wall's removal; Archery had five and Arcana seven. Archery
   gets Long Shot, Expose Weakness and Hamstring as the user wrote them, and Nimble (proposed, not objected to);
   Arcana gets Breach (in Shatter's place, user: 5 / 10 / 15 %) and Phase (proposed, not objected to). §5, §4.3.
5. **What makes the archer fun is a loop:** its ordinary shot spreads and feeds its two short cooldowns. Arms gets
   its loop from rage, Arcana from a Spell Surge fed by casts. §1.3.

### 0.3 Distances, in game units

| Units | What it is in the game today |
| --- | --- |
| 307 | Melee reach, the party's and the monsters' (code, `ActorMeleeRange`) |
| 353 | Inside this a monster never shoots (1.15 × melee reach) |
| 384 / 768 | What the party covers in one second strafing / running |
| 500 | Binding Circle |
| **512** | MAW's "nearby": the count legendaries 21 and 22 use, computed every frame |
| 800 | Vanguard's line (user) |
| 1,024 | Chaining Arrows' leap |
| 1,536 | Where Long Shot starts to count (user) |
| 1,600 | Blink |
| 2,500 | Charge's reach |
| 5,120 | The farthest a monster shoots and the bow's full range (code, `CharacterRangedAttackDistance`); where the fight alert starts |

Distances of the new talents: Outnumbered and Battle Frenzy at 512; Vanguard at 800 (user); Arc and Demoralizing
Shout at 1,024; Challenge at 2,048; Long Shot from 1,536 to 5,120 (user).

## 1. The reference: the archer

### 1.1 The character (save)

`saves/save154.oysav`, playthrough `8bdc5d4c22aa7912c2ec31588cf8c8d1`, read on a copy on 2026-11-18 with the current
build. MAW, Nightmare, free progression, solo run.

| | |
| --- | --- |
| Character | Dark Elf Patriarch, level 728 (753 effective); banked levels 363.8; 21 dimension runs cleared |
| HP / SP | 24,151 / 4,731; HP regeneration 1,438 a second (6 % of the bar); Mana Shield Master 50 |
| Defence | AC 3,252; all six resistances at the 90 % cap; armour takes 85 % off physical blows |
| Offence | Bow Grandmaster 170; ranged damage 12,026 to 17,136; crit chance 138.9 % against level-364 monsters |
| MAW sheet | Ranged Power 563,935; Melee Power 20.6K; Vitality 389,585 |
| Bow | Legendary: each hit also deals 2 % of the monster's current HP (1 % for multi-hit) |
| Other legendaries | all damage taken −10 %; a kill restores 10 % HP and 5 % SP; −3 % damage per nearby enemy; leech also restores mana |

**Talents** (145 points, none unspent; both keystones):

| Tree | Ranks |
| --- | --- |
| Archery | Multishot 3, Chaining Arrows 3, Power Shot 3, Steady Aim 3, Quickfoot 3 (the whole tree, 15 points) |
| Arms | Onslaught 3, Shield Wall 3 |
| Arcana | Resolve 5 |
| Any | Bloodthirst 5, Manathirst 5, Spell Suppression 41, Conditioning 68 |
| Keystones | Cheat Death, Unbroken |

Battle orders: Shield Wall below 40 % HP, Multishot at point-blank range, Power Shot, then the bow.

**Statistics of this timeline** (14.8 hours): 18,450 kills, almost all by missile (about 1,250 an hour); 760 M damage
dealt, all physical; 8.5 M taken (about 160 a second against 1,438 a second of regeneration); largest hit taken
21,550, which is 78 to 89 % of the bar (it read 27,521 HP in the save, 24,151 in today's build); one death. The
lifetime file has 79 deaths and 477 wipes, and several sessions ran with debug help (immortal 13, console 38), so the
death counts are not a clean measure.

### 1.2 What that says about the power level

- **Attrition cannot kill it.** Regeneration alone is nine times the average damage taken, before leech and Mana
  Shield. The only threat is a spike: one hit of four fifths of the bar or more. Cheat Death, Unbroken and Spell
  Suppression are the talents that answer spikes, and it has all three.
- **It kills at range, with full uptime.** Nothing it does needs it to stand in the pack.
- **Most of its points are not in its tree.** Archery took 15 of 145 points. 109 went to the two open-ended sinks
  (Conditioning, Spell Suppression) and 11 to other paths' talents.
- **Two of its tools come from Arms.** Onslaught (+30 % attack speed from kills; it speeds every weapon attack, bows
  included: code, `MawCombatRules.cpp:1609`) and Shield Wall, which works because the talent only checks that the off
  hand is not empty (code, `MawSoloTalents.cpp:215`) and the archer holds a dagger there.

### 1.3 Why it is fun: the loop

| | Ordinary attack spreads | What feeds the actives | Active cooldowns at rank 3 |
| --- | --- | --- | --- |
| **Archery** | Chaining Arrows: each arrow leaps to 3 more at up to 50 % | Multishot: 1 s off per ordinary hit. Power Shot: 0.5 s off per crit | 6 s and 4 s |
| **Arms** today | Sweeping Blows: 3 more in the arc at up to 50 % | Charge: 1 s off per ordinary attack. Nothing for Cleave or Shield Wall | 6 s, 19 s, 40 s |
| **Arcana** today | nothing | nothing | 11 s, 16 s, 35 s |

The archer presses an active every two or three seconds, and its ordinary shot is already an area attack. Per action
against a pack, Arms is on paper level with Archery (a swing with Sweeping Blows is 250 % of a blow over four
monsters, as a shot with Chaining Arrows is 250 % per arrow). What Arms lacks is **uptime** (walking between
monsters deals nothing), **safety on the way in** and **a reason to stand in the pack**. Arcana lacks the loop
itself.

After this proposal: Arms' blows fill rage, and a full bar is a Heroic Strike every 5 to 11 s; Arcana's casts take
a second each off Spell Surge.

## 2. Paths: one archetype per character (decided: a hard lock, free reset)

### 2.1 The problem in numbers

| Level | Talent points (1 per 5 levels) | Cost of all three path trees today |
| --- | --- | --- |
| 50 | 10 | 47 |
| 100 | 20 | 47 |
| 250 | 50 | 47 |
| 728 (the archer) | 145 | 47 |

From about level 250 a character can hold every path talent. So a talent cannot be strong for one archetype only:
"80 % less damage from far missiles" bought by an archer or a sorcerer removes their main danger for three points.

### 2.2 The options that were weighed

| | Rule | For | Against |
| --- | --- | --- | --- |
| **A. One path** (chosen, user) | Ranks in one of Arms, Archery, Arcana close the other two until a reset. Any is open to all | One rule; each path can be balanced on its own; cheapest to build; clear on the page | Hybrids choose (§2.6) |
| B. Main path and a minor path | The whole main tree; from one other tree only talents flagged as utility | Keeps some mixing | Two rules and a flag per talent |
| C. No lock, conditions on each talent | "While a melee weapon is drawn" and so on | No change to the page | Leaks: an archer swaps to the sword while walking in to take 80 % less, then back to the bow |
| D. Depth gates | A tree's strong talents need 10 or 20 points in it | Familiar from other games | Does nothing with 145 points to spend |

One cheap condition from C stays on the Arms defences: they need the melee weapon in the arms, so an Arms character
who shoots a bow does not walk around with them.

### 2.3 How it is represented (proposal)

- **Rule.** The path is the path tree that has ranks. `SoloTalentTable::canLearn` refuses a talent of another path
  tree while one has ranks. No new saved field: `Character::talentRanks` already says it.
- **Data.** One line in `talents.yml`: `paths: [arms, archery, arcana]` (trees not listed, such as `any`, stay open).
  A ruleset that replaces the table can list none and keep free mixing.
- **Reset (user: stays free).** As today: free, at any open trainer, clears everything (code,
  `SoloTalents.cpp:428-439`, `HouseInteraction.cpp:1612`). A player can change path between maps.
- **The page.** The three columns stay, now of equal length. Before a choice all three are lit and the header says
  "Choose a path". After the first rank the chosen column wears its crest and the others dim, with "Another path:
  reset at a trainer" where the rows were clickable. The Any row and the keystone strip do not change.
- **Old saves.** A character with ranks in two or three path trees keeps the tree with the most ranks; the other
  ranks, and Shield Wall's, come back as points, the way removed talents' points already do. The player is told
  once.

### 2.4 Onslaught in the Any tree (decided)

- **Rule (user).** Five ranks. Each kill gives 1 % speed, at most 6 / 12 / 18 / 24 / 30 stacks; the stacks last 60 s
  and every kill refreshes them, as built. It shortens **every** recovery: weapon attacks and spell casts.
- **Data.** `tree: any`, `max_rank: 5`, `per_rank: 6`.
- **Code.** Weapon attacks already read it (`MawCombatRules.cpp:1609`). Spell recovery does not yet:
  `MawSpellRules::recoveryTicks` (`MawSpellRules.cpp:634`) has to apply the same scale. A kill by a spell already
  adds a stack, since `applyPartyHitEffects` runs for spells too (`MawCombatRules.cpp:3212`).
- **The archer.** It keeps Onslaught through the lock. Its saved rank 3 becomes 18 % until two more points go in.
- **To check.** The archer's sheet reads "Recovery time: 20". If that is a floor, more speed does nothing for it.

### 2.5 What else changes for the reference archer

- **Resolve 5** goes with the Arcana tree; it did nothing (every resistance at the cap).
- **Shield Wall 3** goes because the talent is removed (user). It was the archer's panic button, set in its battle
  orders at 40 % HP. Nimble (§5) is the proposed Archery defence in its place.

### 2.6 Hybrids

| Class line | Natural path | Note |
| --- | --- | --- |
| Knight, Minotaur, Troll, Monk, Assassin, Vampire | Arms | |
| Seraph, Shaman, Death Knight | Arms | They cast, but their spells run off melee (weapon damage, on-hit gains), and their defence is the Arms problem |
| Dragon | Arms (claws) or Arcana (Overload counts Dragon Breath and Flame Blast) | Today it takes both. Having to choose is a small cut to the strongest solo class (6.5 times a party at the end of Nightmare, sim) |
| Archer line, any class with a trained bow | Archery | |
| Sorcerer, Elementalist, Necromancer, Druid, Cleric lines | Arcana | The Priest's low damage is a separate problem (2 % of Beyond Madness groups, sim) |

## 3. Arms: the melee identity

### 3.1 What a melee solo faces (facts)

- **Half the bestiary shoots.** 318 of the 655 monster types have a missile or a spell attack (the engine's monster
  table). On Hell and above MAW also gives pure-melee monsters a missile outdoors (10, 20, 30 % by tier; MAW,
  `COMBAT.md` §3.3).
- **Monsters shoot from up to 5,120 units and never inside 353.** A monster with a ranged attack uses it out of
  melee reach, more often the wider the gap (15 to 84 %); within 1.15 times melee reach it never shoots (code,
  `GameplayActorAiSystem.cpp:1213-1278`). Nothing makes a MAW monster hold its distance: they come closer and shoot
  on the way.
- **Missiles home.** A strafe (384 a second) is hit; only a run straight across the flight (768) escapes
  (DEVIATIONS 181). A character walking straight at the shooters takes every missile.
- **Magic is most of the damage late.** On Beyond Madness 74 % of the damage a solo takes is magic, and one magic
  hit is twice a physical one (sim, `RESULTS.md`).
- **Armour and resistance are capped.** MAW never lets them take more than 90 % off a hit. A late melee character
  sits on that cap, so more armour does nothing; only cuts applied after the cap count (Spell Suppression, Unbroken,
  legendaries 18 and 22).
- **In the simulation melee is fine in small pulls and fails on whole groups.** Nightmare level 500, four monsters
  at a time: every melee build beats 100 % at 2 s a monster. Beyond Madness whole groups: 31 to 53 %
  (`TALENT_TREE_V2_RESULTS.md`). The model has no shooters standing off and no walking between monsters, which is
  exactly where play hurts.
- **There is no play data for a late melee solo.** The user has not played one yet ("I will need to create a melee
  character myself and check the feel"). The numbers below are sized by reasoning and MAW's own precedents, not by
  measurement.
- **Cleave and Sweeping Blows miss without telling why** (a player's report in the same thread, 2026-11-18; one cause
  was fixed that day, a second report is coming). The pack talents below multiply what these two do, so they have to
  be reliable first.

### 3.2 The identity

**The pack is your armour, and the fight is your fuel.** Three verbs:

1. **Close.** Getting to the pack under fire is survivable (Vanguard, Charge, Challenge).
2. **Hold.** Surrounded, the character takes less and hits harder (Outnumbered, Battle Frenzy).
3. **Build.** Blows and hits taken fill rage, and a full bar buys the hard blow or the shout (Heroic Strike,
   Demoralizing Shout).

The risk moves instead of disappearing: a melee character is in danger **between** places (in the ring from 512 to
800 units, where a shooter is neither counted by the pack talents nor cut by Vanguard), with **few** monsters around
it (one to three give almost no cut) and against **one** hard hitter (a boss, where the pack talents give nothing;
that is what Heroic Strike and the Shout are for).

### 3.3 The Arms path after the change (nine talents, 27 points)

| Talent | Kind, ranks | Effect | State |
| --- | --- | --- | --- |
| Cleave | active 3 | As built | built |
| Sweeping Blows | passive 3 | As built | built |
| Charge | active 3 | As built; **each kill also takes 3 s off the cooldown** | small code |
| **Vanguard** | passive 3 | Missiles and spells a monster looses from more than 800 units away deal 20 / 40 / 60 % less | new (user: 20/40/60, 800 units, spells count) |
| **Outnumbered** | passive 3 | 2 / 3 / 4 % less damage for each hostile monster within 768, at most 10 monsters | new (user: 768) |
| **Battle Frenzy** | passive 3 | +2 / 3.5 / 5 % melee damage for each hostile monster within 768, at most 10 | new (user: nearby, 768) |
| **Challenge** | active 3 | Every hostile that has noticed you cannot shoot or cast for 4 / 5 / 6 s and comes at you; cooldown 30 / 26 / 22 s, 1 s off per ordinary hit | new (user: in) |
| **Heroic Strike** | active 3, a full rage bar | One blow at 200 / 250 / 300 % on the target, in half a swing's recovery; no cooldown | new (user: 300) |
| **Demoralizing Shout** | active 3, a full rage bar | Hostile monsters within 1,024 deal 30 % less damage for 6 / 8 / 10 s; cooldown 45 / 40 / 35 s | new (user) |

The rage bar comes with the path and costs no points (§3.5). The three passives need the melee weapon in the arms
(not the bow). Removed: Shield Wall (user). Moved to Any: Onslaught (§2.4). Out: Grapple (user).

The first version proposed a per-hit feed for Cleave's cooldown. With rage as the Arms loop it is dropped: one loop,
not two. Charge keeps its kill feed, because that one is about uptime (kill, dash to the next shooter, kill).

### 3.4 The pack talents

**Vanguard** (the user's first idea; 800 units decided, and 20 / 40 / 60 % after the user played the first 80 %).

- *Rule.* A missile or spell that a monster loosed while it stood more than 800 units from the character deals
  20 / 40 / 60 % less. A monster's spells count as its missiles do (user). The distance is taken **when the monster
  fires**, so a Charge during the flight does not turn a far shot into a full one.
- *Why 800 (user).* Monsters stop shooting inside 353, and the two pack talents count within 512. So there is a
  ring from 512 to 800 where a shooter fires at full strength and is not counted: the place a melee character must
  not linger. It is crossed in about a third of a second of running, and it is what Charge is for. (The second
  version of this document proposed 512, one radius for all three; the user kept 800.)
- *With Spell Suppression* (20 %) the two multiply: 80 % becomes 84 %.
- *Abuse.* The path lock keeps it from archers and casters. The melee-weapon condition keeps it from an Arms
  character shooting a bow. Left open: an Arms character casting spells with a sword out; if that proves a problem,
  the cut lapses for 3 s after the character deals spell damage.
- *Code.* (1) `ProjectileState` gets the shooter's distance to the party at spawn (`GameplayProjectileService.cpp`
  near 546 and 607; saved). (2) `recordPartyProjectileImpact` and `CharacterDamageHit` carry it, with a true
  "this was a missile" flag: today a fire missile from a monster's first attack arrives looking like a melee blow
  (`physicalProjectile` false, `spellId` 0). (3) A stage `solo-vanguard` at the end of `m_damageToCharacter`, beside
  `solo-spell-suppression`. (4) The rules cannot see which weapon is drawn (`soloBowDrawn` lives in the interaction
  controller); it has to be kept in `talentState` each frame, as Steady Aim's stillness is. Cost: small to medium,
  both world runtimes touched at one call each.
- *This answers an open question of the power-curve record* ("with missiles always homing, should the solo run give
  a way to answer ranged groups besides geometry?") and the v3 study's Deflect.

**Outnumbered** (the user's third idea).

- *Rule.* 2 / 3 / 4 % less damage for each hostile monster within 512, at most 10 monsters: 20 / 30 / 40 %.
- *MAW has this already.* Legendary 22 is 3 % per monster within 512, compounding, at most 50 %, applied after the
  90 % cap (code, `MawCombatRules.cpp:2715-2722`), and the count is `MawRules::nearbyMonsters()`, computed once a
  frame. The talent is that legendary in ranks; with both worn they multiply.
- *More monsters must never be safer than fewer.* Total damage from n monsters is n × (1 − 0.04 n) of one monster's:
  4 monsters hurt like 3.4, 10 like 6.0. It rises all the way to the cap of 10, so pulling more is still worse, only
  less steeply. Any retune has to keep that (the calculator on the page shows it).
- *One monster gets 4 %.* A boss fight is untouched, on purpose.
- *Code.* One stage after the cap, reading the cached count. Small.

**Battle Frenzy** (the user's second idea; counts nearby monsters, decided).

- *Rule.* +2 / 3.5 / 5 % melee damage for each hostile monster within 512, at most 10: +20 / 35 / 50 %. Melee blows
  only, Cleave's, Sweeping Blows' and Heroic Strike's included.
- *MAW has this already too.* Legendary 21: +5 % per monster within 512, at most double, on melee blows
  (`MawCombatRules.cpp:979-983`). The talent reads the same count as Outnumbered, so the two need nothing new.
- *Abuse.* None by construction: only a melee blow reads it.
- *Parity.* In a pack of ten a swing is 375 % of a blow against the archer's 250 % per arrow. That margin pays for
  the time a melee character spends walking.

**Challenge** (the user's "temporarily disable projectile and spell attacks ... to pull stacks of ranged mobs";
decided: in).

- *Rule.* Every hostile monster within 2,048 cannot shoot or cast for 4 / 5 / 6 s. The AI then does what it does
  when it cannot shoot: it walks into melee. Cooldown 30 / 26 / 22 s, 1 s off per ordinary hit. Bosses: half the
  time. It needs no rage: it is the opener, used when the bar is empty.
- *Why it matters.* It turns a spread group of shooters into the pack that Cleave, Sweeping Blows, Outnumbered and
  Battle Frenzy all want.
- *Code.* A blinded monster and one under Dark Grasp are already forced into melee
  (`GameplayActorAttackConstraintState`, `GameplayActorAiSystem.cpp:1205, 1320`). A third timer (silenced) in
  `GameplayActorSpellEffectState` and a third case of `debuffActor` in both runtimes; spell rolls must respect it
  too. Medium.

### 3.5 Rage (user: on a full bar; the rest as proposed)

**The bar.** 0 to 100, on Arms characters only. It comes with the path. Its two abilities are talents; each can be
used only when the bar is **full**, and using one empties it (user).

**How it fills.** The amounts are shares of a bar, not raw damage, so the formula means the same at level 20 and at
level 700:

| Source | Rage |
| --- | --- |
| A melee blow that hits | 6 × the blow's recovery in seconds (about 3 for a half-second swing), **plus** 30 × the share of the monster's full HP the blow took |
| An extra blow (Cleave's other monsters, Sweeping Blows) | a third of that, as their other on-hit gains are a third |
| A hit taken | 60 × the share of the character's full HP it took, after every cut |
| Limit | at most 20 a second in all (user) |
| Out of combat (no hostile aware of the character) | drains 5 a second |

- *"The more hits and the harder, the faster" (user).* Each blow gives a fixed part and a part for how much of the
  monster's bar it took. The fixed part is scaled by the weapon's speed so that fast and slow weapons fill alike.
- *Why the fixed part.* Against a boss a blow takes a fraction of a percent of the bar. Without the fixed part rage
  would barely fill in exactly the fight where Heroic Strike is wanted.
- *Why hits taken count.* A character in trouble fills faster, so the Shout is there when it is needed.

| Situation | Rage a second | A full bar every |
| --- | --- | --- |
| A pack: 2 swings a second, each 20 % of a monster's bar, Sweeping Blows on 3 more | 20 (the limit) | 5 s |
| A boss: 2 swings a second, each 0.5 % of its bar, taking 4 % of own HP a second | about 9 | 11 s |
| Walking in under fire, taking 5 % of own HP a second | 3 | 33 s |
| No fight | −5 | |

**What a full bar buys.**

- **Heroic Strike** (no cooldown): one blow at 200 / 250 / 300 % of a normal blow on the target, in half a swing's
  recovery, as Cleave and Power Shot are (user: 300; the lower ranks are read as 200 and 250). At rank 3 it adds
  about 30 % to the damage on its target in a pack (one every 5 s) and about 13 % on a boss (one every 11 s). It is
  the Arms answer to Power Shot (200 % every 4 s or less) and the single-target tool the pack talents do not give.
- **Demoralizing Shout** (cooldown 45 / 40 / 35 s): hostile monsters within 1,024 deal 30 % less damage for
  6 / 8 / 10 s. MAW already has this cut at this size: a monster under Shrinking Ray or Dark Grasp deals 30 % less,
  "together not more" (code, `MawCombatRules.cpp:1119-1124`, the `damageDebuffed` flag). The Shout sets the same
  flag, so it does not stack with those two. It acts on the monster's damage before the character's mitigation, so
  it counts in full for a character at the 90 % cap.
- **The choice** at a full bar is damage or defence: the strike now, or the shout if it is off its cooldown.

**Where it shows.** An arc round the right side of the portrait in the solo unit frame, gold when full (the user's
sketch; a third bar under HP and SP in the first build), and the two abilities' action-bar slots veiled until then.

**Code.**

- *State.* `SoloTalentState` gets the rage and its one-second budget (`game/party/SoloTalentState.h`).
- *Dealt.* `MawCombatRules::applyPartyHitEffects` already has the damage, the target's facts, `melee`, `extraBlow`
  and `killed` (`PartyHitOnMonster`, `CombatRules.h`), next to where Onslaught counts its kill.
- *Taken.* `MawCombatRules::absorbCharacterDamage` returns what is left of a hit.
- *Drain.* `MawSoloTalents::update` already gets `calm`.
- *Spending.* `useSoloTalent` checks a talent's `rage_cost` (100: the full bar) as it checks the cooldown.
- *Data.* A `rage:` block in `talents.yml` (the five numbers above) and `rage_cost` on a talent. Heroic Strike is
  otherwise Power Shot's fields (`share_by_rank`, `recovery: 50`).
- *The Shout.* A third source for `damageDebuffed` in both runtimes (`OutdoorWorldRuntime.cpp:17809`,
  `IndoorWorldRuntime.cpp:16750`). Challenge's "cannot shoot" timer is the same kind of work, so the two shouts are
  best built together.

### 3.6 All the cuts together

| Where the character stands | Before | After (rank 3, no legendary, no shout) |
| --- | --- | --- |
| Walking in: 0 within 512, 12 shooters beyond 800 | 12.0 | 2.4 |
| Engaged: 4 within 512, 8 shooters beyond 800 | 12.0 | 5.0 |
| Deep in: 10 within 512, 10 shooters beyond 800 | 20.0 | 8.0 |
| A boss alone | 1.0 | 0.96 (0.67 while the Shout holds) |

(In "one monster's damage"; every monster taken as equal. Spell Suppression is not counted on either side. A
shooter between 512 and 800 counts as one in full on both sides.)

**A shared floor.** Everything the solo run cuts (Vanguard, Outnumbered, Demoralizing Shout, Spell Suppression,
Unbroken's part, and Nimble and Phase on the other paths) should together never leave less than 20 % of the hit.
With Shield Wall gone only Vanguard with Spell Suppression reaches it (16 %); the floor is there for what is added
later.

### 3.7 Before any of it: make Cleave trustworthy

The pack talents multiply Cleave and Sweeping Blows. A report says they sometimes strike one monster in a crowd and
give no sign why. Whatever the coming report finds, the talents should say what they did (a count on the hit, a
"blocked by wall" line), and Cleave should never strike fewer monsters than an ordinary swing with Sweeping Blows
would have.

## 4. Arcana: a proper caster

### 4.1 What is wrong today (facts)

| Talent | Finding | Source |
| --- | --- | --- |
| Overload | Counts monsters near the spell's **named target** (within 384). Ground-aimed spells (Meteor Shower, Starburst, Fire Spike, Sparks, Ice Blast, Rock Blast, Death Blossom, Shrapmetal, Poison Spray) and untargeted ones (Inferno, Armageddon, Prismatic Light, Souldrinker) never name one. Only Fireball, Dragon Breath and Flame Blast can trigger it | code, `PartySpellSystem.cpp:1433-1449` |
| Overload | The simulation counted monsters **hit**, which is why it found Overload the caster's most valuable talent (taking it away cost 15 to 26 points on Beyond Madness). The game's Overload is not the simulated one | sim against code |
| Resolve | Multiplies resistances. Characters at the 90 % cap get nothing; a caster far from the cap gets a little | code and save |
| Spell Surge | 45 / 40 / 35 s cooldown, fed by nothing: once per two or three packs. Any spell spends it, a heal or a buff included | code, `MawSpellRules.cpp:560` |
| The loop | No talent changes the ordinary cast and none feeds a cooldown (§1.3) | |
| In play | Spell Surge, Overload and the passives were only unit-tested; Blink and Binding Circle were tried in the game | `TALENT_TREE_V2_BUILD.md` |
| Presentation | No cast clips for a staff; spells leave from the party's point and not from the hand | `WEAPONS.md` |

Around the tree (MAW's rules, unchanged by any of this):

- Spells are already slow and heavy: a typical spell's recovery is 100 ticks (1.67 s) before Speed and Haste, Meteor
  Shower's 200; Ascension multiplies a spell's damage and slows the cast. There are no cooldowns on spells and no
  movement lock while casting; spells and swings share one recovery.
- The Attack key already casts: a spell placed first in the battle orders is the caster's ordinary attack.
- The simulation's verdict: good from level 50 to 200, collapsing from 300. End of Nightmare: Arch Mage 0.7 of a
  party, Archer 1.0. With range and the v2 talents as simulated, the Arch Mage went from 2 % to between 41 and 52 %
  of Beyond Madness groups.

### 4.2 The identity: artillery

The user's thoughts (2026-11-18): the mage is "probably really similar to archer, just using spells instead of
shooting arrows"; it "needs to solve survivability" and "the chaining"; the archer is "pure zoom zoom damage"; the
mage "needs to pull carefully same as archer"; "maybe like bigger recover, harder hitting? that's even now like
this".

**Proposal: yes to all of that, and make the difference the tempo.** The mage stands where the archer stands and
pulls as carefully. The archer is the skirmisher: many small shots, always moving, never stopping. The mage is the
artillery: few casts, each large, and **the first volley decides the fight**. MAW already makes spells slow and
heavy; the talents should reward that, and should not try to make the mage a fast archer.

| | Archery: the skirmisher | Arms: the juggernaut | Arcana: the artillery |
| --- | --- | --- | --- |
| Tempo | fast and steady | builds with the fight (rage, kills) | slow, front-loaded |
| Area damage | every arrow chains | the arc in front; grows with the pack | area spells; bolts arc |
| Defence | HP, regeneration, speed (Nimble) | the pack itself, Vanguard on the way in, the Shout | the SP bar through Mana Shield, distance, Phase |
| Movement | Quickfoot: runs | Charge: dashes in | Blink: jumps out |
| Fuel | none; hits and crits feed cooldowns | rage | SP, for spells and for the shield |
| Rewarded for | staying far (Long Shot) | standing in the pack (Battle Frenzy) | the first hit (Opening Volley) |
| Loses when | swarmed, or hit by one spike | few around it, or one hard hitter | the first volley fails, or SP run out |

### 4.3 The Arcana path after the change (nine talents, 27 points)

| Talent | Kind, ranks | Effect | State |
| --- | --- | --- | --- |
| Blink | active 3 | As built | built |
| Binding Circle | active 3 | As built | built |
| Overload | passive 3 | **Counts the monsters each blast actually damages**, for every area spell | fix |
| Spell Surge | active 3 | The next **damaging** spell costs no SP and hits 50 % harder; **cooldown 20 / 16 / 12 s, 1 s off for each cast that hits a monster** | rework |
| **Arc** | passive 3 | A single-target spell leaps from the monster it strikes to the nearest other within 1,024, up to 1 / 2 / 3 times, each at 30 % + 0.25 % per point of the spell's school (at most 50 %) | new |
| **Arcane Ward** (replaces Resolve) | passive 3 | Mana Shield spends 10 / 20 / 30 % fewer SP for what it absorbs | new (user: in) |
| **Opening Volley** | passive 3 | +15 / 30 / 45 % spell damage to a monster at full health | new (user: in, at these numbers) |
| **Breach** | passive 3 | Your spells ignore 5 / 10 / 15 % of a monster's resistance | new (user: in, at these numbers) |
| **Phase** | passive 3 | For 3 s after a Blink you take 20 / 35 / 50 % less damage | new, proposed |

From the Any tree a caster takes Manathirst (it refills the shield), Spell Suppression, Conditioning, and now
Onslaught, which speeds casts once kills chain (user).

**Breach, in Shatter's place.** The user turned Shatter down: monsters are held or slowed for a few seconds in
twenty, so it "wouldn't have much effect". Breach is always on and needs no set-up.

- *Rule.* The character's spells count 5 / 10 / 15 % less of the monster's resistance (user's numbers; first
  proposed at twice that).
- *Why it has effect.* MAW divides a spell's damage by 2 for every 100 points of the monster's resistance (code,
  `MawCombatFormulas.cpp:152`). Counting less of it is worth:

  | The monster's resistance | Rank 1 | Rank 2 | Rank 3 |
  | --- | --- | --- | --- |
  | 0 | nothing | nothing | nothing |
  | 50 | +2 % | +4 % | +5 % |
  | 100 | +4 % | +7 % | +11 % |
  | 200 (the highest MAW gives) | +7 % | +15 % | +23 % |

  It is largest exactly against the monsters a caster cannot hurt today, and nothing against the ones it already
  kills. Resistance is also why the Dragon, whose breath ignores it, is the strongest solo class.
- *Code.* One factor on the resistance where the monster's mitigation is computed, for a spell of the party's. No
  state, no timer. Small.

**Phase** makes the escape an escape: a Blink out of a pack is followed by whatever was already in flight. Small to
build (a timer set by Blink, read where damage is absorbed). Proposed; not objected to.

**The three damage talents add; they do not multiply.** Spell Surge (+50 %), Overload (up to +90 %) and Opening
Volley (+45 %) together are at most +185 %, a little under three times a plain cast, where multiplying would give
4.1 times. MAW's developer avoids multiplicative stacks (`DISCORD_DISTILL.md`). Breach is not in that sum: it acts
on the monster's resistance, before them.

### 4.4 Chaining (solved by two things)

- **Arc** is Chaining Arrows for bolts, at the same 1,024: the cheap spell on the Attack key becomes an area attack,
  as the archer's ordinary shot is, and every hit feeds Spell Surge. MAW's Chain Lightning already hops
  (`spellChainMastery`, `MawCombatRules.cpp:2241`), and the arrows' chain was modelled on it, so there is code on
  both sides to start from. Chain Lightning itself is left out of Arc.
- **Overload, fixed,** makes every area spell count the pack it hits. That is the talent the simulation valued most
  for casters and the game barely has.

### 4.5 Survivability (three layers)

Why a mage dies, in the simulation's numbers at level 500 (its gear was poor, so read the proportions, not the
values): 8.1k HP, which is 40 % of what MAW expects; 8,150 SP; Mana Shield at Grandmaster absorbs every hit at 5 HP
for each SP, so the SP bar is worth about 41k HP. That is more than a Champion's 34k. But the mage's resistances are
far from the cap (it takes 33 to 44 % of a magic hit where the Champion takes 10 %), nothing regenerates SP the way
the archer regenerates HP, and the same bar pays for the spells.

1. **Kill first.** Opening Volley, a surged area spell and Overload: most of a pack should not survive to shoot
   back. This is the layer that fits the identity.
2. **Do not be reached.** Blink and Binding Circle, as built, and Phase for the seconds after the jump.
3. **Absorb what lands.** Mana Shield, with Arcane Ward (5 HP per SP becomes 7.1 at rank 3, the bar worth about
   58k), Manathirst to refill it from hits, Spell Suppression, and the two keystones (Unbroken was worth 16 to 24
   points for the Arch Mage alone in the simulation).

Arcane Ward does not make the mage a tank: with its resistances it still has about half a Champion's staying power.
It makes one mistake survivable. In the simulation the stronger version (Archon, 10 HP per SP) was worth 13 to 14
points for casters on Beyond Madness and up to 28 for the Arch Mage.

**Not known:** how a real late mage's sheet reads. There is no sorcerer save, and the simulation's kits were weak.
The first step is to read one at the archer's level (§6).

### 4.6 How a pull plays

Spell Surge is ready → the opener on a pack that has not moved (Meteor Shower, Starburst or Fireball: free, with
Opening Volley, Surge and Overload) → what is left runs in; bolts on the Attack key, Arc spreading them, each hit a
second off the next Surge → Binding Circle when they arrive → Blink out, Phase covering the jump. Kills stack
Onslaught, so the casts quicken through a long fight.

### 4.7 Notes by class

- **Elementalist.** Its stacks already reward casting without a pause; a fed Spell Surge and Onslaught fit. A weapon
  hit clears the stacks, so it will not want Arms.
- **Priest.** Still the weakest. Arcana helps its survival more than its damage; it needs its own answer and is out
  of scope here.
- **Dragon.** Overload counts its breath; with the fix it will count the breath's real hits, which makes the Arcana
  Dragon stronger. Check it first when simulating.

## 5. Archery: four more, to even the count

Three are the user's, as written on 2026-11-18; Nimble is proposed. None adds area damage. The archer also loses
Shield Wall, and its Onslaught is 18 % until two more points go in.

| Talent | Kind, ranks | Effect | From |
| --- | --- | --- | --- |
| Multishot, Chaining Arrows, Power Shot, Steady Aim, Quickfoot | | As built | built |
| **Long Shot** | passive 3 | Bow damage grows with the distance to the monster: nothing under 1,536 units, rising evenly to +3 / 6 / 9 % at the bow's full range of 5,120 | user |
| **Expose Weakness** | passive 3 | A critical strike exposes the monster: it takes 3 / 6 / 9 % more damage for 5 s. Not stacking; each critical strike renews it | user (replaces Hunter's Mark) |
| **Hamstring** | passive 3 | A critical strike slows the monster's movement by 5 / 10 / 15 % for 3 s. Movement only; not stacking | user |
| **Nimble** | passive 3 | 5 / 10 / 15 % less damage while moving | proposed |

**Long Shot.**

- *The curve at rank 3:* 0 at 1,536; +3.75 % at 2,432; +7.5 % at 3,328; +11.25 % at 4,224; +15 % at 5,120.
- *Code.* The distance is the arrow's flight, from where it left to where it struck: `ProjectileState` keeps its
  source point. 5,120 is `CharacterRangedAttackDistance` (`GameplayActionController.cpp:42`), the farthest the party
  shoots. One factor in the party's damage stages. Small.
- It mirrors Battle Frenzy: Arms is paid for standing in the pack, Archery for keeping its distance.

**Expose Weakness.**

- *Read as:* the percent is by rank ("up to 5/10/15 %"), and every hit on the exposed monster counts, the chained
  and Multishot arrows too.
- *Code.* MAW already keeps a "takes more damage" value on a monster: the Grandmaster spear's stack
  (`ActorRulesetFacts::spearDamageTaken`, read at `MawCombatRules.cpp:1041`). Expose Weakness is a second value of
  that kind with an end time. Small.

**Hamstring** (movement only, user).

- *Code.* The game's slow (`debuffActor(Slow, seconds, power)`, `OutdoorWorldRuntime.cpp:19423`) sets a monster's
  movement and its attack recovery together, so it cannot be used as it is. Hamstring needs a slow of movement
  alone: one more timed value on the monster in both world runtimes, read where the actor's speed is computed, kept
  at the stronger of two so it does not stack. Medium, and the same kind of work as Challenge's "cannot shoot": best
  built in that stage.
- *A side gain.* Binding Circle today holds monsters with the ordinary slow at a tenth, which also slows their
  attacks tenfold (a note of the build). With a movement-only slow it could become the root it was meant to be.

**Nimble** (proposed; not objected to). The archer's defence is speed. It pulls against Steady Aim (stand still for
Luck), which makes a choice in play, and takes the place Shield Wall had. Steady Aim's stillness is already tracked
in `talentState`; a stage after the cap, under the shared floor. Small.

**What the three do to the reference.** The archer's crit chance against its monsters is 138.9 % (save), so every
arrow is a critical strike. For it Expose Weakness and Hamstring are always up on everything it shoots: +9 %
damage, and monsters that walk 15 % slower. Long Shot adds up to 9 % more at the far end of its range. Together that is
roughly 9 to 19 % more damage for the reference archer at rank 3 (15 to 30 % at the first sizes of 5 / 10 / 15 %), less for a character whose crits are not
certain. The melee and caster numbers in this document were sized against the archer before this; the parity checks
of §6 are where that gets settled.

## 6. Parity: how to tell when melee and caster are "at the archer's level"

**The principle (proposal).** At the same level and gear tier the three paths clear the same map in about the same
time and die about as often, with the danger in different places (the last row of the table in §4.2).

**Three ways to measure, cheapest first.**

1. **MAW's own sheet.** The character sheet already prints Power (damage per second against a monster of the banked
   level) and Vitality. The archer: Ranged Power 564K, Vitality 390K. A melee and a caster character of level 728
   with gear of the same tier should be read against those two numbers before any talent is tuned; if a sheet is far
   below, talents are the wrong place to fix it.
2. **The simulation.** `talentfight.py` has the range model (groups start 1,200 units away, shooters stand off at
   600) and the talent proxies. Add the Arms talents and rage, the fixed Overload, the fed Spell Surge, Arc and
   Opening Volley; rerun Nightmare 300 and 500 and Beyond Madness 500 for Champion, Lich King, Monk, Arch Mage and
   Master of Elements beside the Archer. Whole groups, not pulls of four.
3. **Play.** One dimension map of the archer's tier (the quicksave sits in one: power 47, tier 490) with a melee
   and a caster test character made at its level. `testparty` takes a build written out in full
   ([HANDOFF_POWER_CURVE.md](HANDOFF_POWER_CURVE.md) §3.3). The user's rule stands: a number that contradicts their
   play is wrong.

**First targets for play** (against the archer on the same map): clear time within 25 %; no more deaths than the
archer; a hand on an active every 3 to 6 s; the largest single hit below 90 % of the bar.

## 7. Order of work (proposal)

| Stage | What | Size |
| --- | --- | --- |
| 0 | Read a melee and a mage sheet at the archer's level (§6). Fix Overload's count; make Cleave and Sweeping Blows say what they struck | small |
| 1 | The path lock (rule, page, migration). Shield Wall out. Onslaught to Any: five ranks, spell recovery | small |
| 2 | Arms passives: Outnumbered and Battle Frenzy (both ride on MAW's count), then Vanguard (the missile's firing distance); the shared floor; Charge's kill feed | medium |
| 3 | Rage: the bar, its place in the unit frame, Heroic Strike | medium |
| 4 | The new monster states together, in both runtimes: Challenge ("cannot shoot or cast"), Demoralizing Shout (30 % less damage) and Hamstring's slow of movement alone | medium |
| 5 | Arcana: Spell Surge rework, Arc, Arcane Ward in place of Resolve, Opening Volley, Breach, Phase | medium |
| 6 | Archery: Long Shot, Expose Weakness, Nimble; Hamstring on the state of stage 4 | small |
| 7 | Play all three paths on one dimension map; tune | — |

Each stage is playable alone. Stages 2 to 4 (Arms), 5 (Arcana) and 6 (Archery) do not depend on each other.

## 8. Dropped

- **Shield Wall:** removed entirely (user, 2026-11-18).
- **Grapple / Death Grip:** out (user, 2026-11-18).
- **Rage with a price on each ability:** replaced by "on a full bar" (user).
- **Cleave's per-hit feed:** dropped in favour of rage (§3.3).
- **Battle Frenzy counting every monster that noticed the character:** replaced by the nearby count (user).
- **Resolve:** replaced by Arcane Ward (as read, §0.1).
- **Shatter:** out (user: it "wouldn't have much effect"); Breach is proposed in its place.
- **Hunter's Mark:** out (user); Expose Weakness replaces it.
- **Hamstring as a slow on Multishot, Long Shot as a flat bonus past 1,024:** replaced by the user's versions.
- **Vanguard at 512, Heroic Strike at 300 / 400 / 500 %, Breach at 10 / 20 / 30 %, Hamstring on the game's ordinary
  slow:** replaced by the user's numbers (800; 300; 5 / 10 / 15 %; movement only).

## 9. Still open

Nothing is waiting on a design decision. Two readings to confirm, and what only play can answer:

1. **Heroic Strike's ranks:** "300" is read as the last rank, with 200 and 250 below it.
2. **Expose Weakness:** "up to 5/10/15 %" is read as the percent by rank, on every hit the exposed monster takes.
3. **Sizes.** Every number here is a first value. The archer rises by roughly 9 to 19 % with its three new talents
   (§5), and no late melee or mage character has been played or even read from a sheet (§6, step 1).

## 10. Sources

- **Save:** `saves/save154.oysav` read on a copy, headless (`player sheet`, `talent list`), and its sealed timeline;
  the save was written by an older build than the one that read it (HP settled at 24,151 from a stored 27,521).
- **Code:** `assets_dev/engine/data_tables/talents.yml`; `game/rules/SoloTalents.cpp`;
  `game/rules/maw/MawSoloTalents.cpp`, `MawCombatRules.cpp` (the damage stages, legendaries 21 and 22, the 30 %
  monster debuff, `applyPartyHitEffects`, `absorbCharacterDamage`, `updateCombat`), `MawSpellRules.cpp` (spell
  recovery); `game/gameplay/GameplayActorAiSystem.cpp` (ranged decisions, `ActorMeleeRange` 307.2,
  `MaximumRangedAttackDistance` 5120); `GameplayProjectileService` (`ProjectileState`);
  `GameplayInteractionController.cpp` (`useSoloTalent`, `soloBowDrawn`); `game/party/PartySpellSystem.cpp`
  (Overload's count); `game/party/SoloTalentState.h`.
- **Simulation:** `devdocs/maw/solo_sim/RESULTS.md`, `CURVE_RESULTS.md`, `proposals/TALENT_TREE_V2_RESULTS.md`,
  `proposals/TALENTS_AND_PROGRESSION.md`, `proposals/DISCORD_DISTILL.md`.
- **The user's ideas:** the Discord thread of 2026-11-18 (projectile cut outside close range by 80 or 90 %; attack
  damage per monster focusing the character; less damage per monster close; a talent that stops a monster's ranged
  attacks, or a Death Grip; gated so archers and mages cannot abuse it; talents as the only large divergence from
  MAW's balance), and the two rounds of decisions of the same day in §0.1.
