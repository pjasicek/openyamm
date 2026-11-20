# MAW solo-class simulation: results (2026-11-14)

Method and how to rerun: [README.md](README.md). Page with every view: <https://jasicek.net/openyamm/maw-solo/>.
"Real groups" = the actual monster groups of the ten maps around each stage (README §5); "pulled 4" = four at a
time, resting between pulls; "generic pack" = B-tier physical melee monsters all attacking at once. Builds are the
22 in `scripts/gen.py`, gear from the simulated playthrough's own loot and crafting.

## Verdict

Ranked by the share of real-group monsters beaten, pulled four at a time without potions. Nightmare figures are
levels 50 / 200 / 500; Doom, Road to Insanity and Beyond Madness at level 500, where the builds separate.

| Tier | Build | Nightmare 50 / 200 / 500 | Doom 500 | Road to Insanity 500 | Beyond Madness 500 |
| --- | --- | --- | --- | --- | --- |
| 1 | Great Wyrm (Dragon), breath | 100 / 100 / 100 | 100 | 100 | 84 |
| 1 | Archangel (Seraph), two-handed sword + shield | 100 / 100 / 100 | 97 | 89 | 47 |
| 2 | War Troll (very slow: about 9 s per monster at Nightmare L500) | 100 / 100 / 100 | 100 | 100 | 57 |
| 2 | Marabou (Shaman), melee | 100 / 100 / 100 | 90 | 72 | 3 |
| 2 | Minotaur Lord two axes; Troll-race Champion | 100 / 100 / 100 | 89–92 | 63–69 | 4–10 |
| 3 | Black Knight (Vampire race); Champion sword + shield (two-handed axe: Doom 70, RtI 59) | 95–100 | 80–84 | 54–61 | 1–6 |
| 3 | Lich Kings, Nosferatu, Monk | 84–100 | 45–56 | 32–49 | 0–3 |
| 3 | Master Archer | 92 / 91 / 94 | 56 | 50 | 1 |
| 3 | Arch Mage, Master of Elements | 91–92 / 80–81 / 69–77 | 17–22 | 11–13 | 0 |
| avoid | Assassin | 86 / 82 / 80 | 38 | 25 | 0 |
| avoid | Priest of the Light (Cleric) | 46 / 47 / 19 | 4 | 2 | 0 |

- The generic pack test gives the same order up to Road to Insanity (Nightmare 50/200/500: Dragon and Seraph 40+,
  Troll 18 / 27 / 25, Shaman 16, Knights and Death Knights 8–17, Priest 2–4).
- Early game: at level 10 on Nightmare and harder, before any promotion, most builds need potions or careful pulls
  (a plain Knight beats 27 % of the groups around it on Nightmare, 4 % on Road to Insanity). Dragon, Seraph, Troll
  and Shaman are the exceptions. From level 50 the first promotion and gear carry everyone but the Cleric.
- Beyond Madness, second half (level 500, 126 of 189 maps cleared, monsters level 300–320): only the Dragon handles
  most groups standing; Troll and Seraph partly; every other build beats at most 10 % pulled four at a time, even with
  potions. Melee can still kill one to three at a time (largest generic pack 2–3), so progress needs single pulls,
  potions and the tricks the model leaves out. The character stays about 1.6 × the monster level to the end (level 804
  against level-490 maps), so it does not get easier later.

## Why a solo works: levels and experience

- Monsters are sized against one expected character of their own level: HP = power × hits to kill [1, 1.5, 2, 2.5,
  3, 3.5, 4, 4.5, 5] by difficulty, damage = vitality / [14, 10, 7, 6.5, 6, 5.5, 5, 4.5, 4]. Party size changes only
  Cover.
- Kills, quests and map completion pay a solo five times a party member's share, while the bank (which sets monster
  levels) grows as for a party. So a solo runs at about twice the bank level: monsters about 16 / 90 / 235 at
  character level 50 / 200 / 500 in free progression (first estimate 23 / 99 / 275). Even without quests a level-50
  solo meets level 14–20 monsters.
- No diminishing returns by character level: MAW shrinks a kill's award by the monster's HP against a monster of the
  bank's level, not the character's (`zzzMaw_Experience.lua:192-205`, same in OpenYAMM).
- Quest check (Nightmare; experience share kills / completion / quests):

| Quests counted | L50 | L200 | L500 | Full clear |
| --- | --- | --- | --- | --- |
| every award (251 + map scripts, the first count) | mon 16, 54 / 19 / 27 % | mon 89, 62 / 18 / 20 % | mon 242, 26 / 17 / 57 % | level 532 |
| one reward per event (used) | mon 16, 57 / 20 / 23 % | mon 88, 66 / 19 / 14 % | mon 240, 27 / 17 / 56 % | level 503 |
| none | mon 18, 75 / 24 / 1 % | mon 99, 77 / 23 / 0 % | not reached | level 379 |

  Road to Insanity: full clear 492 → 469 (none: 385); Beyond Madness 820 → 804 (none: 744). Late quests are large
  because MAW adds 500 × the levels banked on the other continents to each.

## Why the Seraph is this strong

Spirit and Body, both received in full by a solo.

- **Spirit: hits land at 25 %.** After armour every hit loses a flat amount, never below 25 %:
  `max(hit − flat, 0.25·hit)`. The flat amount is sized for an average party member at the bank: about the bank
  monster's hit before armour × Spirit skill ÷ expected skill. It assumes average armour, and a solo is about twice
  the bank level (L200: bank 99, Spirit 27 against an expected 19), so the cut exceeds the whole hit.

| Nightmare L200 | Champion | Archangel |
| --- | --- | --- |
| HP | 5,049 | 2,203 |
| B monster hit after armour | 94 | 131 |
| Spirit's flat cut | – | 335 (MAW's formula: 254) |
| Damage landing per hit | 94 (1.9 % of HP) | 33 (1.5 % of HP) |

- **Body: a heal on every blow.** `Body^1.3 × mastery × 2 × speed factor × (1 + Personality/1000)` to the most
  wounded member; a solo is always that member. Light speeds the swing (0.5 s at L200).

| Nightmare | Heal per blow | % of its HP per second |
| --- | --- | --- |
| L50 (Angel) | 94 | 21 % |
| L200 (Archangel) | 467 | 42 % |
| L500 (Archangel) | 2,264 | 44 % |

- Together at L200: one monster takes about 1 % of its HP per second, the heals return 42 %; about 40 monsters at
  once before it loses ground.
- Where it breaks: low HP (Expert Bodybuilding cap). In Beyond Madness L500 a physical B hit still floors (1,248
  lands, 16 % of 7,977 HP) but a magic one does not (below).
- Part of the strength is the flat-cut port difference (README, Open items); up to Road to Insanity it changes
  nothing, at Beyond Madness L500 MAW's formula lands 2,692 per physical hit instead of 1,248.

## Beyond Madness: magic decides it

- At level 500 (monsters about 302) a B monster's magic hit is 71,220 against 36,800 physical, and 74 % of the damage
  in the real maps is magic (Nightmare L200: 53 %). Real groups there: median 5, the largest tenth 11.
- Seraph: magic hit after resistances 10.5 k, minus the 3,792 flat cut, lands 6.7 k (84 % of its HP). Dragon: 21.9 k
  of 56 k HP (39 %); it resists magic about as well as physical (taken 31 % both).
- The generic packs hit only physically, so they rank the Seraph (12, MAW formula 6) above the Dragon (9; 31 with a
  3 s opener) at Beyond Madness L500; the real groups rank the Dragon first (84 % against 47 %).
- HP spread at Beyond Madness L500 (seed 1): Minotaur Lord 57.8 k, Dragon 56.4 k, War Troll 52.3 k, Champion 33.9 k,
  Lich King 11.8 k, Archangel 8.0 k. Death Knights and Seraphim stop at Expert Bodybuilding (skill 40 and 31 here);
  Minotaurs, Trolls and Dragons reach Grandmaster (69–77), plus race HP.
- Real groups in Beyond Madness L500 include rooms such as 27 Warlocks (level 329, C tier, 125,645 magic damage each)
  and 25 Maddening Eyes: whole-room aggro is death for everyone but the Dragon.

## The Dragon

- Best class at every stage and difficulty, early and late. Breath hits about three quarters of a group and takes
  each monster's lowest resistance; rings, amulet and gauntlets count three times, so it gears from few drops;
  Grandmaster Regeneration; 75 k HP and 26.5 k area damage per second at Beyond Madness L500, losing 5.75 % of its HP
  per second per monster (Seraph 7.5 % on 10.7 k, Lich King 14 % on 13.5 k).
- Undersold: it is ranged (a 3 s opener lifts its generic pack at Beyond Madness L500 from 9 to 31) and has Fear
  (spell 122) as crowd control; neither is in the fights.

## Notes per candidate

- Troll: survival yes, speed no (Grandmaster Regeneration 8–15 % of max HP per second, 12 HP per level). A Troll-race
  Champion has only Novice Regeneration but is among the best plain melee builds.
- Death Knight: fine on Nightmare, weak late on the harder difficulties (no Armsmaster, Expert Bodybuilding, 7 HP per
  level; 10–15 % melee leech and Blood's physical cut). Its spells are not simulated.
- Vampire Black Knight: 5 % race leech, Knight HP and Armsmaster; a little ahead of a Human Champion.
- Bowman: hits hard, 6 HP per level and no sustain; better in pulls than standing in a pack.
- Minotaur knight: Minotaur Lord with two axes is the best plain melee in real groups despite no helm or boots;
  Minotaur-race Champion with two two-handed axes has the fastest single-target kills.
- Casters: good about level 50–200 (Grandmaster Mana Shield absorbs up to 5 HP per spell point), weak at L500. Keep
  Learning low: Ascension raises mana cost far faster than damage. A level-10 Sorcerer knows little.
- Thief (dagger, Dodging): cannot learn Armsmaster in MAW; about 2,000 HP at L200; energy pays a third of its blows.
- Cleric: the slowest kills and the worst survival of all 22 builds.

## Measured tables

Generated by `scripts/results_tables.py` from the 2026-11-14 run.

### Playthrough (median of five seeds)

Per stage: monster level there · maps cleared · monsters killed · chests opened · quest share of experience.

| Difficulty | Level 10 | Level 50 | Level 200 | Level 500 | Full clear ends at |
|---|---|---|---|---|---|
| Normal | L1 · 3 · 223 · 12 · 48 % | L17 · 20 · 3,228 · 137 · 22 % | L95 · 62 · 9,772 · 394 · 19 % | not reached (stand-in: end of clear, monsters L231) | level 486 |
| MAW | L1 · 3 · 215 · 12 · 45 % | L16 · 19 · 3,058 · 128 · 23 % | L93 · 60 · 9,716 · 393 · 16 % | not reached (stand-in: end of clear, monsters L232) | level 489 |
| Hard | L1 · 3 · 229 · 12 · 51 % | L17 · 20 · 3,160 · 136 · 26 % | L94 · 61 · 9,914 · 385 · 19 % | not reached (stand-in: end of clear, monsters L235) | level 498 |
| Hell | L1 · 3 · 223 · 12 · 48 % | L16 · 19 · 2,927 · 125 · 26 % | L94 · 62 · 10,116 · 394 · 19 % | not reached (stand-in: end of clear, monsters L233) | level 494 |
| Nightmare | L1 · 3 · 247 · 12 · 42 % | L16 · 19 · 3,406 · 128 · 23 % | L88 · 58 · 11,145 · 391 · 14 % | L240 · 189 · 21,077 · 1049 · 56 % | level 503 |
| Doom | L4 · 1 · 268 · 12 · 27 % | L17 · 19 · 2,978 · 132 · 37 % | L71 · 87 · 11,429 · 536 · 48 % | not reached (stand-in: end of clear, monsters L226) | level 471 |
| Road to Insanity | L4 · 1 · 276 · 12 · 25 % | L17 · 19 · 3,026 · 132 · 37 % | L72 · 88 · 12,666 · 537 · 49 % | not reached (stand-in: end of clear, monsters L226) | level 469 |
| Beyond Madness | L4 · 2 · 255 · 27 · 50 % | L7 · 10 · 1,641 · 95 · 27 % | L97 · 48 · 6,678 · 284 · 33 % | L302 · 126 · 17,931 · 746 · 25 % | level 804 |

### Real map groups: Normal

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 100 / 100 / 100 · 0.3 · Dragon | 100 / 100 / 100 · 0.3 · Dragon | 100 / 100 / 100 · 0.2 · GreatWyrm | 100 / 100 / 100 · 0.1 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 100 / 100 / 98 · 1.1 · Seraphim | 100 / 100 / 100 · 1.2 · Angel | 100 / 100 / 100 · 0.8 · Archangel | 100 / 100 / 100 · 0.9 · Ultimate Archangel |
| War Troll, mace + shield | 100 / 100 / 97 · 1.4 · Troll | 100 / 100 / 100 · 1.6 · Troll | 100 / 100 / 100 · 1.3 · WarTroll | 100 / 100 / 100 · 2.7 · Ultimate WarTroll |
| War Troll, two-handed staff | 100 / 100 / 97 · 1.5 · Troll | 100 / 100 / 100 · 1.5 · Troll | 100 / 100 / 100 · 1.6 · WarTroll | 100 / 100 / 100 · 2.7 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 98 / 100 / 94 · 1.7 · Shaman | 100 / 100 / 100 · 1.4 · Sekhem | 100 / 100 / 100 · 1.0 · Marabou | 100 / 100 / 100 · 1.1 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 100 / 100 / 94 · 1.7 · Minotaur | 100 / 100 / 99 · 1.3 · Minotaur | 100 / 100 / 100 · 0.8 · MinotaurLord | 100 / 100 / 100 · 0.7 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 100 / 100 / 93 · 1.1 · Knight | 100 / 100 / 100 · 1.2 · Cavalier | 100 / 100 / 100 · 0.6 · Champion | 100 / 100 / 100 · 0.9 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 100 / 100 / 94 · 1.0 · Knight | 100 / 100 / 100 · 1.0 · Cavalier | 100 / 100 / 100 · 0.6 · BlackKnight | 100 / 100 / 100 · 0.6 · Ultimate BlackKnight |
| Champion, sword + shield | 96 / 100 / 88 · 1.2 · Knight | 100 / 100 / 99 · 1.2 · Cavalier | 100 / 100 / 100 · 0.6 · Champion | 100 / 100 / 100 · 1.0 · Ultimate Champion |
| Champion, two-handed axe | 100 / 100 / 85 · 1.5 · Knight | 100 / 100 / 99 · 1.3 · Cavalier | 100 / 100 / 100 · 0.8 · Champion | 100 / 100 / 100 · 0.7 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 100 / 100 / 87 · 1.4 · Knight | 100 / 100 / 96 · 1.3 · Cavalier | 100 / 100 / 100 · 0.8 · Champion | 100 / 100 / 100 · 0.7 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 100 / 100 / 94 · 1.7 · Minotaur | 100 / 100 / 99 · 1.5 · Minotaur | 100 / 100 / 100 · 0.9 · MinotaurLord | 100 / 100 / 100 · 1.0 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 100 / 100 / 94 · 1.5 · DeathKnight | 100 / 100 / 100 · 1.5 · DeathLord | 100 / 100 / 100 · 0.9 · LichKing | 100 / 100 / 100 · 1.0 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 100 / 100 / 93 · 1.4 · DeathKnight | 100 / 100 / 100 · 1.3 · DeathLord | 100 / 100 / 100 · 0.8 · LichKing | 100 / 100 / 100 · 0.7 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 100 / 100 / 93 · 1.4 · DeathKnight | 100 / 100 / 100 · 1.4 · DeathLord | 100 / 100 / 100 · 0.9 · LichKing | 100 / 100 / 100 · 1.0 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 100 / 100 / 95 · 1.3 · Vampire | 100 / 100 / 100 · 0.8 · Vampire | 100 / 100 / 100 · 0.5 · Nosferatu | 100 / 100 / 100 · 0.8 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 100 / 100 / 91 · 1.5 · Monk | 100 / 100 / 100 · 1.5 · Initiate | 100 / 100 / 100 · 0.8 · Master | 100 / 100 / 100 · 1.1 · Ultimate Master |
| Master Archer, bow | 85 / 100 / 62 · 2.1 · Archer | 100 / 100 / 99 · 1.0 · WarriorMage | 100 / 100 / 100 · 0.5 · MasterArcher | 100 / 100 / 100 · 0.6 · Ultimate MasterArcher |
| Arch Mage, Fire | 96 / 100 / 93 · 0.8 · Sorcerer | 100 / 100 / 100 · 0.7 · Wizard | 100 / 100 / 100 · 0.7 · ArchMage | 100 / 100 / 100 · 0.9 · Ultimate ArchMage |
| Master of Elements, four elements | 100 / 100 / 96 · 0.5 · Elementalist | 100 / 100 / 100 · 0.5 · ElementalAdept | 100 / 100 / 100 · 0.7 · MasterOfElements | 96 / 97 / 98 · 0.4 · Ultimate MasterOfElements |
| Assassin, two daggers | 87 / 100 / 60 · 1.7 · Thief | 100 / 100 / 93 · 0.8 · Rogue | 100 / 100 / 100 · 0.5 · Assassin | 100 / 100 / 100 · 0.6 · Ultimate Assassin |
| Priest of Light | 25 / 99 / 18 · 4.7 · Cleric | 86 / 100 / 67 · 6.7 · Priest | 100 / 100 / 96 · 3.5 · PriestLight | 95 / 100 / 95 · 4.0 · Ultimate PriestLight |

### Real map groups: MAW

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 100 / 100 / 98 · 0.4 · Dragon | 100 / 100 / 100 · 0.4 · Dragon | 100 / 100 / 100 · 0.2 · GreatWyrm | 100 / 100 / 100 · 0.1 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 100 / 100 / 97 · 1.4 · Seraphim | 100 / 100 / 100 · 1.5 · Angel | 100 / 100 / 100 · 1.0 · Archangel | 100 / 100 / 100 · 1.1 · Ultimate Archangel |
| War Troll, mace + shield | 100 / 100 / 95 · 1.8 · Troll | 100 / 100 / 100 · 1.8 · Troll | 100 / 100 / 100 · 2.3 · WarTroll | 100 / 100 / 100 · 3.5 · Ultimate WarTroll |
| War Troll, two-handed staff | 100 / 100 / 94 · 1.6 · Troll | 100 / 100 / 100 · 1.7 · Troll | 100 / 100 / 100 · 1.9 · WarTroll | 100 / 100 / 100 · 3.5 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 92 / 100 / 83 · 1.9 · Shaman | 100 / 100 / 100 · 1.5 · Sekhem | 100 / 100 / 97 · 1.1 · Marabou | 100 / 100 / 100 · 1.1 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 97 / 100 / 85 · 1.9 · Minotaur | 100 / 100 / 94 · 1.4 · Minotaur | 100 / 100 / 97 · 0.9 · MinotaurLord | 100 / 100 / 100 · 1.0 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 92 / 100 / 76 · 2.1 · Knight | 100 / 100 / 96 · 1.5 · Cavalier | 100 / 100 / 97 · 1.0 · Champion | 100 / 100 / 100 · 1.1 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 96 / 100 / 86 · 1.1 · Knight | 100 / 100 / 98 · 1.2 · Cavalier | 100 / 100 / 97 · 0.7 · BlackKnight | 100 / 100 / 100 · 0.8 · Ultimate BlackKnight |
| Champion, sword + shield | 82 / 100 / 57 · 2.2 · Knight | 100 / 100 / 93 · 1.5 · Cavalier | 100 / 100 / 97 · 1.0 · Champion | 100 / 100 / 100 · 1.1 · Ultimate Champion |
| Champion, two-handed axe | 86 / 100 / 64 · 1.8 · Knight | 100 / 100 / 93 · 1.4 · Cavalier | 100 / 100 / 95 · 0.9 · Champion | 100 / 100 / 100 · 0.9 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 90 / 100 / 68 · 1.7 · Knight | 100 / 100 / 92 · 1.3 · Cavalier | 100 / 100 / 95 · 0.9 · Champion | 100 / 100 / 100 · 0.7 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 97 / 100 / 85 · 1.9 · Minotaur | 100 / 100 / 93 · 1.5 · Minotaur | 100 / 100 / 97 · 1.1 · MinotaurLord | 100 / 100 / 100 · 1.3 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 93 / 100 / 83 · 1.7 · DeathKnight | 100 / 100 / 96 · 1.6 · DeathLord | 100 / 100 / 97 · 1.0 · LichKing | 100 / 100 / 100 · 1.1 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 93 / 100 / 80 · 1.6 · DeathKnight | 100 / 100 / 96 · 1.4 · DeathLord | 100 / 100 / 95 · 0.9 · LichKing | 100 / 100 / 100 · 0.9 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 93 / 100 / 80 · 1.6 · DeathKnight | 100 / 100 / 96 · 1.5 · DeathLord | 100 / 100 / 93 · 1.2 · LichKing | 100 / 100 / 97 · 1.2 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 92 / 100 / 80 · 2.0 · Vampire | 100 / 100 / 97 · 1.0 · Vampire | 100 / 100 / 97 · 0.7 · Nosferatu | 100 / 100 / 100 · 0.8 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 92 / 100 / 75 · 1.8 · Monk | 100 / 100 / 96 · 1.7 · Initiate | 100 / 100 / 95 · 0.9 · Master | 100 / 100 / 100 · 1.2 · Ultimate Master |
| Master Archer, bow | 51 / 99 / 25 · 2.9 · Archer | 100 / 100 / 94 · 1.0 · WarriorMage | 100 / 100 / 95 · 0.6 · MasterArcher | 100 / 100 / 100 · 0.7 · Ultimate MasterArcher |
| Arch Mage, Fire | 78 / 93 / 66 · 1.9 · Sorcerer | 100 / 100 / 100 · 1.2 · Wizard | 100 / 100 / 95 · 1.4 · ArchMage | 100 / 100 / 99 · 1.0 · Ultimate ArchMage |
| Master of Elements, four elements | 89 / 98 / 86 · 0.7 · Elementalist | 99 / 100 / 99 · 0.7 · ElementalAdept | 99 / 100 / 94 · 1.6 · MasterOfElements | 97 / 97 / 97 · 0.5 · Ultimate MasterOfElements |
| Assassin, two daggers | 62 / 100 / 31 · 2.6 · Thief | 98 / 100 / 85 · 1.1 · Rogue | 100 / 100 / 91 · 0.6 · Assassin | 100 / 100 / 100 · 0.8 · Ultimate Assassin |
| Priest of Light | 6 / 96 / 6 · 7.1 · Cleric | 77 / 100 / 58 · 7.2 · Priest | 90 / 100 / 78 · 5.6 · PriestLight | 90 / 99 / 88 · 5.0 · Ultimate PriestLight |

### Real map groups: Hard

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 100 / 100 / 98 · 0.4 · Dragon | 100 / 100 / 100 · 0.4 · Dragon | 100 / 100 / 100 · 0.3 · GreatWyrm | 100 / 100 / 100 · 0.2 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 100 / 100 / 96 · 2.0 · Seraphim | 100 / 100 / 100 · 1.7 · Angel | 100 / 100 / 100 · 0.9 · Archangel | 100 / 100 / 100 · 1.4 · Ultimate Archangel |
| War Troll, mace + shield | 100 / 100 / 93 · 2.4 · Troll | 100 / 100 / 100 · 2.2 · Troll | 100 / 100 / 100 · 2.3 · WarTroll | 100 / 100 / 100 · 5.0 · Ultimate WarTroll |
| War Troll, two-handed staff | 100 / 100 / 92 · 1.9 · Troll | 100 / 100 / 100 · 2.2 · Troll | 100 / 100 / 100 · 1.9 · WarTroll | 100 / 100 / 100 · 4.4 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 92 / 100 / 86 · 2.0 · Shaman | 100 / 100 / 98 · 1.6 · Sekhem | 100 / 100 / 100 · 1.2 · Marabou | 100 / 100 / 100 · 1.4 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 94 / 100 / 85 · 2.0 · Minotaur | 100 / 100 / 92 · 1.5 · Minotaur | 100 / 100 / 100 · 1.0 · MinotaurLord | 100 / 100 / 100 · 1.2 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 87 / 100 / 69 · 2.3 · Knight | 100 / 100 / 95 · 1.8 · Cavalier | 100 / 100 / 100 · 1.0 · Champion | 100 / 100 / 100 · 1.6 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 93 / 100 / 85 · 1.5 · Knight | 100 / 100 / 95 · 1.4 · Cavalier | 100 / 100 / 100 · 0.7 · BlackKnight | 100 / 100 / 98 · 1.2 · Ultimate BlackKnight |
| Champion, sword + shield | 73 / 100 / 45 · 2.4 · Knight | 99 / 100 / 91 · 1.9 · Cavalier | 100 / 100 / 100 · 1.0 · Champion | 100 / 100 / 100 · 1.6 · Ultimate Champion |
| Champion, two-handed axe | 88 / 99 / 62 · 1.8 · Knight | 100 / 100 / 92 · 1.6 · Cavalier | 100 / 100 / 98 · 1.0 · Champion | 100 / 100 / 98 · 1.2 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 89 / 99 / 63 · 1.7 · Knight | 100 / 100 / 91 · 1.4 · Cavalier | 100 / 100 / 98 · 0.9 · Champion | 100 / 100 / 100 · 1.0 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 94 / 100 / 85 · 2.0 · Minotaur | 100 / 100 / 92 · 1.7 · Minotaur | 100 / 100 / 98 · 1.2 · MinotaurLord | 100 / 100 / 100 · 1.7 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 94 / 100 / 85 · 1.8 · DeathKnight | 100 / 100 / 96 · 1.7 · DeathLord | 100 / 100 / 100 · 1.1 · LichKing | 100 / 100 / 100 · 1.3 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 94 / 100 / 81 · 1.6 · DeathKnight | 100 / 100 / 95 · 1.5 · DeathLord | 100 / 100 / 98 · 1.0 · LichKing | 100 / 100 / 96 · 1.2 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 94 / 100 / 81 · 1.6 · DeathKnight | 100 / 100 / 95 · 1.6 · DeathLord | 100 / 100 / 98 · 1.2 · LichKing | 100 / 100 / 96 · 1.6 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 90 / 100 / 78 · 2.3 · Vampire | 100 / 100 / 93 · 1.2 · Vampire | 100 / 100 / 100 · 0.6 · Nosferatu | 100 / 100 / 98 · 1.1 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 89 / 99 / 73 · 2.0 · Monk | 100 / 100 / 93 · 2.2 · Initiate | 100 / 100 / 98 · 0.9 · Master | 100 / 100 / 96 · 1.8 · Ultimate Master |
| Master Archer, bow | 36 / 100 / 20 · 3.3 · Archer | 99 / 100 / 91 · 1.5 · WarriorMage | 100 / 100 / 97 · 0.8 · MasterArcher | 100 / 100 / 100 · 0.9 · Ultimate MasterArcher |
| Arch Mage, Fire | 73 / 92 / 61 · 1.9 · Sorcerer | 98 / 100 / 94 · 1.5 · Wizard | 100 / 100 / 97 · 1.4 · ArchMage | 97 / 97 / 92 · 1.5 · Ultimate ArchMage |
| Master of Elements, four elements | 80 / 87 / 77 · 0.7 · Elementalist | 98 / 100 / 98 · 0.9 · ElementalAdept | 99 / 100 / 96 · 1.6 · MasterOfElements | 94 / 95 / 92 · 1.0 · Ultimate MasterOfElements |
| Assassin, two daggers | 42 / 100 / 22 · 3.2 · Thief | 96 / 100 / 83 · 1.4 · Rogue | 100 / 100 / 92 · 0.6 · Assassin | 99 / 99 / 93 · 1.0 · Ultimate Assassin |
| Priest of Light | 5 / 89 / 5 · 5.7 · Cleric | 71 / 100 / 49 · 8.7 · Priest | 99 / 100 / 78 · 6.6 · PriestLight | 70 / 97 / 70 · 5.9 · Ultimate PriestLight |

### Real map groups: Hell

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 100 / 100 / 98 · 0.5 · Dragon | 100 / 100 / 100 · 0.5 · Dragon | 100 / 100 / 100 · 0.3 · GreatWyrm | 100 / 100 / 100 · 0.3 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 100 / 100 / 92 · 2.6 · Seraphim | 100 / 100 / 100 · 2.0 · Angel | 100 / 100 / 100 · 1.2 · Archangel | 100 / 100 / 100 · 1.9 · Ultimate Archangel |
| War Troll, mace + shield | 99 / 100 / 85 · 3.1 · Troll | 100 / 100 / 100 · 2.6 · Troll | 100 / 100 / 100 · 2.5 · WarTroll | 100 / 100 / 100 · 5.4 · Ultimate WarTroll |
| War Troll, two-handed staff | 100 / 100 / 88 · 2.2 · Troll | 100 / 100 / 100 · 2.4 · Troll | 100 / 100 / 100 · 2.2 · WarTroll | 100 / 100 / 97 · 5.5 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 92 / 100 / 85 · 2.1 · Shaman | 100 / 100 / 98 · 1.8 · Sekhem | 100 / 100 / 100 · 1.3 · Marabou | 100 / 100 / 94 · 1.6 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 92 / 100 / 82 · 2.1 · Minotaur | 100 / 100 / 90 · 1.7 · Minotaur | 100 / 100 / 98 · 1.0 · MinotaurLord | 100 / 100 / 94 · 1.5 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 78 / 100 / 57 · 3.0 · Knight | 100 / 100 / 91 · 2.2 · Cavalier | 100 / 100 / 98 · 1.1 · Champion | 100 / 100 / 94 · 2.1 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 90 / 100 / 82 · 2.0 · Knight | 100 / 100 / 94 · 1.7 · Cavalier | 100 / 100 / 100 · 0.8 · BlackKnight | 100 / 100 / 94 · 1.4 · Ultimate BlackKnight |
| Champion, sword + shield | 58 / 100 / 37 · 3.1 · Knight | 99 / 100 / 87 · 2.2 · Cavalier | 100 / 100 / 98 · 1.1 · Champion | 100 / 100 / 94 · 2.1 · Ultimate Champion |
| Champion, two-handed axe | 85 / 100 / 64 · 1.9 · Knight | 100 / 100 / 88 · 1.7 · Cavalier | 100 / 100 / 98 · 0.9 · Champion | 100 / 100 / 93 · 1.4 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 86 / 99 / 67 · 1.9 · Knight | 100 / 100 / 88 · 1.5 · Cavalier | 100 / 100 / 98 · 0.8 · Champion | 100 / 100 / 94 · 1.1 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 92 / 100 / 82 · 2.1 · Minotaur | 100 / 100 / 89 · 1.9 · Minotaur | 100 / 100 / 98 · 1.1 · MinotaurLord | 100 / 100 / 94 · 2.2 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 92 / 100 / 84 · 2.0 · DeathKnight | 100 / 100 / 95 · 1.8 · DeathLord | 100 / 100 / 98 · 1.2 · LichKing | 100 / 100 / 94 · 1.7 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 93 / 100 / 83 · 1.8 · DeathKnight | 100 / 100 / 94 · 1.6 · DeathLord | 100 / 100 / 98 · 1.0 · LichKing | 100 / 100 / 94 · 1.2 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 93 / 100 / 83 · 1.8 · DeathKnight | 100 / 100 / 94 · 1.8 · DeathLord | 100 / 100 / 96 · 1.2 · LichKing | 100 / 100 / 93 · 2.1 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 86 / 100 / 70 · 2.7 · Vampire | 100 / 100 / 91 · 1.5 · Vampire | 100 / 100 / 98 · 1.0 · Nosferatu | 100 / 100 / 93 · 1.4 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 84 / 99 / 61 · 2.9 · Monk | 100 / 100 / 88 · 2.6 · Initiate | 100 / 100 / 98 · 1.0 · Master | 100 / 100 / 93 · 2.1 · Ultimate Master |
| Master Archer, bow | 51 / 99 / 31 · 3.6 · Archer | 98 / 100 / 85 · 1.8 · WarriorMage | 100 / 100 / 96 · 0.8 · MasterArcher | 100 / 100 / 93 · 1.1 · Ultimate MasterArcher |
| Arch Mage, Fire | 66 / 88 / 55 · 2.2 · Sorcerer | 98 / 100 / 94 · 1.8 · Wizard | 100 / 100 / 96 · 1.9 · ArchMage | 91 / 91 / 88 · 1.7 · Ultimate ArchMage |
| Master of Elements, four elements | 74 / 87 / 68 · 1.1 · Elementalist | 99 / 100 / 96 · 1.2 · ElementalAdept | 96 / 100 / 97 · 2.0 · MasterOfElements | 76 / 85 / 76 · 2.2 · Ultimate MasterOfElements |
| Assassin, two daggers | 16 / 100 / 14 · 3.9 · Thief | 94 / 100 / 72 · 1.8 · Rogue | 100 / 100 / 91 · 0.8 · Assassin | 83 / 93 / 83 · 1.4 · Ultimate Assassin |
| Priest of Light | 2 / 80 / 2 · 8.7 · Cleric | 48 / 100 / 37 · 10.1 · Priest | 92 / 100 / 77 · 8.5 · PriestLight | 58 / 91 / 58 · 7.9 · Ultimate PriestLight |

### Real map groups: Nightmare

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 100 / 100 / 98 · 0.7 · Dragon | 100 / 100 / 100 · 0.5 · Dragon | 100 / 100 / 96 · 0.5 · GreatWyrm | 100 / 100 / 100 · 0.3 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 90 / 100 / 82 · 3.2 · Seraphim | 100 / 100 / 100 · 2.0 · Angel | 100 / 100 / 94 · 1.8 · Archangel | 100 / 100 / 96 · 2.4 · Ultimate Archangel |
| War Troll, mace + shield | 92 / 100 / 70 · 3.7 · Troll | 100 / 100 / 95 · 3.1 · Troll | 100 / 100 / 94 · 3.5 · WarTroll | 100 / 100 / 96 · 9.0 · Ultimate WarTroll |
| War Troll, two-handed staff | 94 / 100 / 72 · 3.4 · Troll | 100 / 100 / 96 · 2.7 · Troll | 100 / 100 / 92 · 3.6 · WarTroll | 100 / 100 / 96 · 7.2 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 80 / 100 / 55 · 3.2 · Shaman | 100 / 100 / 94 · 1.9 · Sekhem | 100 / 100 / 86 · 1.6 · Marabou | 100 / 100 / 96 · 1.9 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 77 / 99 / 40 · 3.0 · Minotaur | 100 / 100 / 84 · 1.8 · Minotaur | 100 / 100 / 85 · 1.5 · MinotaurLord | 100 / 100 / 95 · 2.0 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 56 / 100 / 25 · 3.5 · Knight | 100 / 100 / 85 · 2.3 · Cavalier | 100 / 100 / 86 · 1.6 · Champion | 100 / 100 / 95 · 2.7 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 73 / 100 / 36 · 2.9 · Knight | 100 / 100 / 87 · 1.8 · Cavalier | 100 / 100 / 85 · 1.3 · BlackKnight | 100 / 100 / 95 · 1.7 · Ultimate BlackKnight |
| Champion, sword + shield | 27 / 99 / 16 · 3.7 · Knight | 95 / 100 / 76 · 2.3 · Cavalier | 100 / 100 / 83 · 1.6 · Champion | 96 / 98 / 91 · 3.0 · Ultimate Champion |
| Champion, two-handed axe | 52 / 97 / 24 · 2.7 · Knight | 99 / 100 / 83 · 1.9 · Cavalier | 94 / 94 / 75 · 1.4 · Champion | 98 / 98 / 90 · 1.7 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 49 / 96 / 22 · 2.6 · Knight | 99 / 100 / 82 · 1.7 · Cavalier | 93 / 94 / 75 · 1.4 · Champion | 98 / 98 / 91 · 1.5 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 77 / 99 / 40 · 3.0 · Minotaur | 97 / 100 / 81 · 2.1 · Minotaur | 94 / 94 / 75 · 2.0 · MinotaurLord | 97 / 97 / 91 · 3.1 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 80 / 97 / 50 · 3.0 · DeathKnight | 100 / 100 / 90 · 1.9 · DeathLord | 91 / 94 / 75 · 1.8 · LichKing | 98 / 100 / 93 · 2.0 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 71 / 94 / 39 · 2.4 · DeathKnight | 100 / 100 / 87 · 1.8 · DeathLord | 92 / 92 / 78 · 1.5 · LichKing | 96 / 100 / 91 · 1.8 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 71 / 94 / 39 · 2.4 · DeathKnight | 98 / 100 / 86 · 2.2 · DeathLord | 84 / 91 / 71 · 1.8 · LichKing | 90 / 93 / 88 · 2.6 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 68 / 99 / 34 · 3.3 · Vampire | 97 / 100 / 81 · 1.5 · Vampire | 91 / 91 / 76 · 1.3 · Nosferatu | 100 / 100 / 95 · 2.2 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 38 / 97 / 18 · 4.3 · Monk | 98 / 100 / 81 · 2.8 · Initiate | 94 / 94 / 76 · 1.4 · Master | 100 / 100 / 92 · 3.1 · Ultimate Master |
| Master Archer, bow | 14 / 95 / 8 · 7.5 · Archer | 92 / 100 / 76 · 2.0 · WarriorMage | 91 / 94 / 71 · 1.4 · MasterArcher | 94 / 95 / 88 · 1.6 · Ultimate MasterArcher |
| Arch Mage, Fire | 20 / 56 / 15 · 3.6 · Sorcerer | 92 / 98 / 84 · 2.1 · Wizard | 80 / 83 / 69 · 2.4 · ArchMage | 77 / 78 / 75 · 4.0 · Ultimate ArchMage |
| Master of Elements, four elements | 27 / 67 / 17 · 2.2 · Elementalist | 91 / 97 / 86 · 1.6 · ElementalAdept | 81 / 82 / 78 · 2.4 · MasterOfElements | 69 / 75 / 67 · 4.6 · Ultimate MasterOfElements |
| Assassin, two daggers | 8 / 99 / 5 · 7.9 · Thief | 86 / 100 / 64 · 1.9 · Rogue | 82 / 90 / 64 · 1.3 · Assassin | 80 / 92 / 79 · 1.9 · Ultimate Assassin |
| Priest of Light | 0 / 66 / 0 · 10.6 · Cleric | 46 / 100 / 31 · 11.9 · Priest | 47 / 74 / 40 · 9.0 · PriestLight | 19 / 83 / 19 · 15.3 · Ultimate PriestLight |

### Real map groups: Doom

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 98 / 99 / 91 · 1.0 · Dragon | 100 / 100 / 100 · 0.7 · Dragon | 100 / 100 / 100 · 0.4 · Elder GreatWyrm | 100 / 100 / 98 · 0.5 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 85 / 100 / 64 · 3.1 · Seraphim | 100 / 100 / 98 · 2.4 · Angel | 100 / 100 / 100 · 1.3 · Elder Archangel | 97 / 97 / 84 · 2.7 · Ultimate Archangel |
| War Troll, mace + shield | 66 / 100 / 28 · 4.7 · Troll | 100 / 100 / 80 · 3.4 · Troll | 100 / 100 / 100 · 3.4 · Elder WarTroll | 100 / 100 / 84 · 8.5 · Ultimate WarTroll |
| War Troll, two-handed staff | 42 / 98 / 16 · 9.0 · Troll | 100 / 100 / 84 · 3.2 · Troll | 100 / 100 / 98 · 3.1 · Elder WarTroll | 100 / 100 / 80 · 7.0 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 67 / 97 / 40 · 7.6 · Shaman | 100 / 100 / 86 · 2.1 · Sekhem | 100 / 100 / 93 · 2.3 · Elder Marabou | 90 / 90 / 66 · 2.0 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 3 / 90 / 3 · 14.0 · Minotaur | 97 / 100 / 64 · 1.8 · Minotaur | 100 / 100 / 85 · 1.9 · Elder MinotaurLord | 92 / 92 / 63 · 1.9 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 49 / 100 / 17 · 5.6 · Knight | 98 / 100 / 69 · 3.2 · Cavalier | 100 / 100 / 93 · 1.3 · Elder Champion | 89 / 89 / 60 · 2.8 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 42 / 97 / 16 · 7.2 · Knight | 95 / 100 / 67 · 2.2 · Cavalier | 100 / 100 / 93 · 1.1 · Elder BlackKnight | 80 / 80 / 56 · 1.5 · Ultimate BlackKnight |
| Champion, sword + shield | 20 / 99 / 7 · 5.9 · Knight | 90 / 100 / 56 · 3.2 · Cavalier | 100 / 100 / 90 · 1.4 · Elder Champion | 84 / 85 / 58 · 2.6 · Ultimate Champion |
| Champion, two-handed axe | 9 / 87 / 4 · 8.1 · Knight | 93 / 100 / 56 · 2.2 · Cavalier | 99 / 99 / 75 · 2.0 · Elder Champion | 70 / 71 / 52 · 1.6 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 0 / 79 / 0 · 12.7 · Knight | 94 / 100 / 62 · 1.6 · Cavalier | 100 / 100 / 77 · 1.2 · Elder Champion | 60 / 60 / 50 · 1.1 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 3 / 90 / 3 · 14.0 · Minotaur | 95 / 100 / 61 · 2.4 · Minotaur | 100 / 100 / 79 · 3.1 · Elder MinotaurLord | 58 / 59 / 50 · 2.4 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 50 / 90 / 18 · 7.6 · DeathKnight | 99 / 100 / 72 · 2.3 · DeathLord | 99 / 100 / 82 · 2.4 · Elder LichKing | 55 / 57 / 47 · 2.5 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 3 / 89 / 3 · 13.0 · DeathKnight | 99 / 100 / 71 · 1.7 · DeathLord | 99 / 100 / 79 · 1.6 · Elder LichKing | 56 / 57 / 47 · 1.6 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 3 / 89 / 3 · 13.0 · DeathKnight | 96 / 100 / 64 · 2.3 · DeathLord | 97 / 99 / 64 · 2.8 · Elder LichKing | 45 / 46 / 39 · 2.0 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 39 / 98 / 13 · 8.7 · Vampire | 95 / 100 / 61 · 2.0 · Vampire | 100 / 100 / 91 · 1.1 · Elder Nosferatu | 54 / 59 / 45 · 2.4 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 28 / 91 / 11 · 5.8 · Monk | 93 / 100 / 56 · 3.3 · Initiate | 100 / 100 / 85 · 1.4 · Elder Master | 56 / 64 / 48 · 2.5 · Ultimate Master |
| Master Archer, bow | 3 / 95 / 3 · 10.7 · Archer | 87 / 100 / 50 · 2.3 · WarriorMage | 99 / 100 / 74 · 1.3 · Elder MasterArcher | 56 / 57 / 47 · 1.2 · Ultimate MasterArcher |
| Arch Mage, Fire | 0 / 44 / 0 · 10.3 · Sorcerer | 81 / 99 / 66 · 3.6 · Wizard | 98 / 98 / 78 · 2.5 · Elder ArchMage | 22 / 22 / 18 · 3.5 · Ultimate ArchMage |
| Master of Elements, four elements | 0 / 25 / 0 · 10.0 · Elementalist | 75 / 97 / 62 · 2.5 · ElementalAdept | 93 / 98 / 88 · 1.5 · Elder MasterOfElements | 17 / 17 / 21 · 2.1 · Ultimate MasterOfElements |
| Assassin, two daggers | 3 / 90 / 3 · 10.0 · Thief | 64 / 100 / 37 · 2.2 · Rogue | 97 / 100 / 66 · 1.0 · Elder Assassin | 38 / 44 / 26 · 1.9 · Ultimate Assassin |
| Priest of Light | 0 / 81 / 0 · 11.6 · Cleric | 37 / 100 / 25 · 10.9 · Priest | 72 / 99 / 36 · 9.1 · Elder PriestLight | 4 / 27 / 4 · 14.5 · Ultimate PriestLight |

### Real map groups: Road to Insanity

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 93 / 99 / 80 · 1.1 · Dragon | 100 / 100 / 100 · 0.5 · Dragon | 100 / 100 / 100 · 0.4 · Elder GreatWyrm | 100 / 100 / 99 · 0.6 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 56 / 100 / 33 · 12.9 · Seraphim | 100 / 100 / 100 · 2.6 · Angel | 100 / 100 / 97 · 1.3 · Elder Archangel | 89 / 89 / 68 · 2.4 · Ultimate Archangel |
| War Troll, mace + shield | 62 / 100 / 28 · 5.1 · Troll | 100 / 100 / 78 · 2.9 · Troll | 100 / 100 / 94 · 2.7 · Elder WarTroll | 100 / 100 / 77 · 9.4 · Ultimate WarTroll |
| War Troll, two-handed staff | 29 / 98 / 12 · 12.4 · Troll | 100 / 100 / 78 · 2.1 · Troll | 100 / 100 / 93 · 2.6 · Elder WarTroll | 99 / 99 / 69 · 7.4 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 36 / 98 / 17 · 11.0 · Shaman | 100 / 100 / 85 · 1.7 · Sekhem | 100 / 100 / 89 · 1.9 · Elder Marabou | 72 / 78 / 58 · 2.8 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 1 / 91 / 1 · 14.0 · Minotaur | 98 / 100 / 72 · 1.7 · Minotaur | 100 / 100 / 80 · 1.2 · Elder MinotaurLord | 69 / 69 / 53 · 1.8 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 24 / 99 / 10 · 6.0 · Knight | 98 / 100 / 73 · 2.5 · Cavalier | 100 / 100 / 77 · 1.3 · Elder Champion | 63 / 63 / 51 · 2.4 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 0 / 88 / 0 · 13.5 · Knight | 98 / 100 / 75 · 2.0 · Cavalier | 100 / 100 / 89 · 1.0 · Elder BlackKnight | 61 / 61 / 50 · 1.8 · Ultimate BlackKnight |
| Champion, sword + shield | 4 / 99 / 3 · 6.4 · Knight | 98 / 100 / 68 · 2.5 · Cavalier | 100 / 100 / 83 · 1.3 · Elder Champion | 54 / 55 / 48 · 2.5 · Ultimate Champion |
| Champion, two-handed axe | 0 / 89 / 0 · 11.8 · Knight | 98 / 100 / 68 · 1.9 · Cavalier | 100 / 100 / 74 · 1.5 · Elder Champion | 59 / 59 / 49 · 1.7 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 0 / 72 / 0 · 15.7 · Knight | 98 / 100 / 69 · 1.7 · Cavalier | 99 / 99 / 72 · 1.1 · Elder Champion | 47 / 47 / 44 · 1.2 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 1 / 89 / 1 · 14.0 · Minotaur | 98 / 100 / 68 · 2.0 · Minotaur | 99 / 99 / 72 · 2.5 · Elder MinotaurLord | 45 / 45 / 39 · 2.6 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 6 / 93 / 3 · 11.1 · DeathKnight | 98 / 100 / 75 · 1.8 · DeathLord | 99 / 100 / 74 · 2.1 · Elder LichKing | 49 / 49 / 43 · 2.0 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 0 / 80 / 0 · 14.0 · DeathKnight | 98 / 100 / 74 · 1.6 · DeathLord | 100 / 100 / 78 · 1.0 · Elder LichKing | 44 / 44 / 39 · 1.4 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 0 / 75 / 0 · 14.0 · DeathKnight | 98 / 100 / 71 · 1.8 · DeathLord | 96 / 99 / 65 · 2.2 · Elder LichKing | 32 / 33 / 29 · 2.1 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 12 / 91 / 5 · 14.3 · Vampire | 98 / 100 / 67 · 2.0 · Vampire | 100 / 100 / 83 · 1.0 · Elder Nosferatu | 41 / 42 / 36 · 3.2 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 18 / 90 / 7 · 7.4 · Monk | 98 / 100 / 68 · 2.3 · Initiate | 100 / 100 / 81 · 1.1 · Elder Master | 46 / 46 / 40 · 2.5 · Ultimate Master |
| Master Archer, bow | 1 / 93 / 1 · 7.1 · Archer | 98 / 100 / 63 · 1.7 · WarriorMage | 98 / 99 / 69 · 1.2 · Elder MasterArcher | 50 / 50 / 42 · 1.4 · Ultimate MasterArcher |
| Arch Mage, Fire | 0 / 33 / 0 · 12.2 · Sorcerer | 97 / 100 / 76 · 2.2 · Wizard | 96 / 99 / 85 · 1.8 · Elder ArchMage | 13 / 16 / 9 · 6.3 · Ultimate ArchMage |
| Master of Elements, four elements | 0 / 17 / 0 · 11.5 · Elementalist | 78 / 94 / 57 · 1.3 · ElementalAdept | 93 / 96 / 76 · 1.2 · Elder MasterOfElements | 11 / 11 / 11 · 1.9 · Ultimate MasterOfElements |
| Assassin, two daggers | 0 / 84 / 0 · 11.3 · Thief | 83 / 100 / 50 · 2.6 · Rogue | 97 / 99 / 67 · 0.9 · Elder Assassin | 25 / 32 / 21 · 2.0 · Ultimate Assassin |
| Priest of Light | 0 / 69 / 0 · 12.4 · Cleric | 74 / 100 / 44 · 7.6 · Priest | 84 / 96 / 42 · 9.1 · Elder PriestLight | 2 / 16 / 1 · 17.3 · Ultimate PriestLight |

### Real map groups: Beyond Madness

Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. Class = the class the character has at that stage.

| Build | L10: P4 / P4+ / W · s · class | L50: P4 / P4+ / W · s · class | L200: P4 / P4+ / W · s · class | L500: P4 / P4+ / W · s · class |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 54 / 68 / 44 · 1.1 · Dragon | 99 / 100 / 96 · 1.0 · Dragon | 100 / 100 / 100 · 0.4 · Dragon | 84 / 84 / 60 · 2.0 · Ultimate GreatWyrm |
| Archangel (Seraph), two-handed sword + shield | 51 / 72 / 32 · 14.5 · Seraphim | 93 / 100 / 74 · 3.4 · Seraphim | 100 / 100 / 94 · 2.4 · Angel | 47 / 47 / 29 · 4.8 · Ultimate Archangel |
| War Troll, mace + shield | 48 / 70 / 20 · 5.1 · Troll | 89 / 99 / 53 · 4.9 · Troll | 99 / 100 / 42 · 4.6 · Troll | 57 / 66 / 26 · 53.7 · Ultimate WarTroll |
| War Troll, two-handed staff | 41 / 68 / 17 · 3.8 · Troll | 92 / 97 / 52 · 3.2 · Troll | 99 / 100 / 44 · 3.6 · Troll | 40 / 48 / 19 · 75.2 · Ultimate WarTroll |
| Marabou (Shaman), axe + seven schools | 31 / 53 / 17 · 7.0 · Shaman | 83 / 93 / 53 · 2.4 · Shaman | 100 / 100 / 64 · 2.6 · Sekhem | 3 / 4 / 2 · 4.3 · Ultimate Marabou |
| Minotaur Lord, two two-handed axes | 6 / 52 / 3 · 7.4 · Minotaur | 85 / 95 / 39 · 2.4 · Minotaur | 98 / 99 / 25 · 2.2 · Minotaur | 10 / 10 / 4 · 3.5 · Ultimate MinotaurLord |
| Champion (Troll race), sword + shield | 31 / 75 / 12 · 32.8 · Knight | 51 / 97 / 25 · 4.4 · Knight | 97 / 99 / 30 · 2.6 · Cavalier | 4 / 6 / 2 · 5.9 · Ultimate Champion |
| Black Knight (Vampire race), two-handed sword | 20 / 72 / 6 · 27.5 · Knight | 69 / 97 / 31 · 3.5 · Knight | 99 / 99 / 35 · 2.2 · Cavalier | 6 / 6 / 3 · 2.9 · Ultimate BlackKnight |
| Champion, sword + shield | 14 / 75 / 5 · 39.8 · Knight | 32 / 97 / 17 · 4.8 · Knight | 98 / 99 / 29 · 2.6 · Cavalier | 1 / 2 / 0 · 3.6 · Ultimate Champion |
| Champion, two-handed axe | 1 / 49 / 1 · 11.1 · Knight | 54 / 90 / 25 · 3.2 · Knight | 86 / 99 / 21 · 3.3 · Cavalier | 3 / 3 / 1 · 3.2 · Ultimate Champion |
| Champion (Minotaur race), two two-handed axes | 0 / 41 / 0 · 13.6 · Knight | 56 / 86 / 22 · 2.5 · Knight | 96 / 99 / 26 · 1.8 · Cavalier | 4 / 4 / 2 · 2.2 · Ultimate Champion |
| Minotaur Lord, one two-handed axe | 6 / 52 / 3 · 7.4 · Minotaur | 64 / 93 / 28 · 3.3 · Minotaur | 52 / 89 / 14 · 4.2 · Minotaur | 3 / 3 / 1 · 4.8 · Ultimate MinotaurLord |
| Lich King (Vampire race), two-handed axe | 13 / 50 / 5 · 6.6 · DeathKnight | 85 / 94 / 47 · 2.8 · DeathKnight | 99 / 100 / 38 · 3.1 · DeathLord | 1 / 2 / 0 · 5.6 · Ultimate LichKing |
| Lich King (Minotaur race), two two-handed axes | 1 / 49 / 1 · 13.0 · DeathKnight | 73 / 85 / 31 · 2.3 · DeathKnight | 99 / 100 / 34 · 2.1 · DeathLord | 3 / 3 / 1 · 2.4 · Ultimate LichKing |
| Lich King (Minotaur race), two-handed axe | 1 / 49 / 1 · 13.0 · DeathKnight | 63 / 89 / 29 · 3.2 · DeathKnight | 90 / 99 / 22 · 3.8 · DeathLord | 0 / 0 / 0 · 3.5 · Ultimate LichKing |
| Nosferatu (Vampire), two daggers | 32 / 75 / 13 · 28.2 · Vampire | 72 / 97 / 33 · 3.1 · Vampire | 92 / 98 / 24 · 1.6 · Vampire | 2 / 2 / 1 · 2.9 · Ultimate Nosferatu |
| Master (Monk), staff + Unarmed | 25 / 57 / 7 · 4.4 · Monk | 50 / 89 / 22 · 3.6 · Monk | 91 / 98 / 22 · 3.2 · Initiate | 2 / 2 / 1 · 4.3 · Ultimate Master |
| Master Archer, bow | 1 / 59 / 1 · 31.1 · Archer | 26 / 93 / 14 · 4.6 · Archer | 96 / 99 / 29 · 1.4 · WarriorMage | 1 / 1 / 0 · 1.8 · Ultimate MasterArcher |
| Arch Mage, Fire | 0 / 42 / 0 · 9.4 · Sorcerer | 56 / 83 / 33 · 2.8 · Sorcerer | 75 / 92 / 34 · 3.2 · Wizard | 0 / 0 / 0 · 0.0 · Ultimate ArchMage |
| Master of Elements, four elements | 0 / 22 / 0 · 8.8 · Elementalist | 52 / 77 / 33 · 1.7 · Elementalist | 52 / 80 / 24 · 1.8 · ElementalAdept | 0 / 0 / 0 · 0.0 · Ultimate MasterOfElements |
| Assassin, two daggers | 5 / 69 / 3 · 29.4 · Thief | 23 / 94 / 12 · 4.0 · Thief | 54 / 98 / 13 · 1.7 · Rogue | 0 / 0 / 0 · 4.0 · Ultimate Assassin |
| Priest of Light | 0 / 50 / 0 · 13.7 · Cleric | 10 / 81 / 6 · 11.5 · Cleric | 0 / 92 / 0 · 28.2 · Priest | 0 / 0 / 0 · 0.0 · Ultimate PriestLight |

### Generic packs: largest pack survived standing, no potions

B-tier physical melee monsters of the content level, all attacking from the first second; 40 = 40 or more. Columns: Normal, MAW, Hard, Hell, Nightmare, Doom, Road to Insanity, Beyond Madness.

| Build | L10 | L50 | L200 | L500 |
|---|---|---|---|---|
| Great Wyrm (Dragon), bite + breath | 40 40 40 40 40 11 9 10 | 40 40 40 40 40 40 40 40 | 40 40 40 40 40 40 40 40 | 40 40 40 40 40 40 40 9 |
| Archangel (Seraph), two-handed sword + shield | 20 17 13 11 11 8 4 6 | 40 40 40 40 40 31 30 32 | 40 40 40 40 40 40 40 32 | 40 40 40 40 40 31 27 12 |
| War Troll, mace + shield | 14 9 8 7 8 4 4 4 | 31 24 20 20 18 11 11 17 | 40 35 32 23 27 40 40 7 | 40 34 30 26 25 21 15 5 |
| War Troll, two-handed staff | 13 10 10 7 7 3 2 4 | 29 24 21 18 17 10 14 16 | 39 31 29 22 24 36 36 7 | 40 31 26 24 19 17 13 5 |
| Marabou (Shaman), axe + seven schools | 11 9 9 8 6 5 3 3 | 20 18 16 16 16 14 16 16 | 24 19 18 15 16 24 28 10 | 25 20 19 18 16 13 10 3 |
| Minotaur Lord, two two-handed axes | 9 7 7 7 6 1 1 2 | 13 11 10 11 10 8 9 11 | 19 16 15 14 14 16 21 5 | 18 15 16 14 12 10 9 3 |
| Champion (Troll race), sword + shield | 8 6 5 4 4 3 2 3 | 17 13 12 12 10 8 10 11 | 22 18 19 15 16 24 16 5 | 25 17 20 19 12 10 8 2 |
| Black Knight (Vampire race), two-handed sword | 10 8 5 5 5 3 1 2 | 20 17 16 12 10 8 9 15 | 31 22 20 14 17 24 23 6 | 27 25 15 17 14 10 8 3 |
| Champion, sword + shield | 6 5 4 3 3 2 2 2 | 16 11 10 10 8 7 8 9 | 20 17 17 15 14 21 20 5 | 23 15 21 18 10 8 8 2 |
| Champion, two-handed axe | 6 5 5 5 5 2 1 1 | 12 10 11 10 10 8 8 9 | 16 13 14 12 13 12 16 5 | 15 13 12 13 10 8 6 2 |
| Champion (Minotaur race), two two-handed axes | 7 5 5 5 5 1 1 1 | 11 10 9 10 9 7 8 8 | 14 11 12 11 11 15 14 5 | 13 11 11 12 10 8 7 3 |
| Minotaur Lord, one two-handed axe | 9 7 7 7 6 1 1 2 | 13 11 10 11 10 8 8 11 | 17 16 13 14 12 14 15 4 | 16 14 15 14 9 7 6 2 |
| Lich King (Vampire race), two-handed axe | 9 7 7 7 5 3 1 2 | 18 15 15 14 14 11 11 15 | 22 16 15 15 15 15 19 6 | 18 14 14 15 10 9 5 2 |
| Lich King (Minotaur race), two two-handed axes | 9 7 7 7 6 1 1 1 | 15 12 12 12 11 10 10 11 | 17 14 12 12 12 17 18 6 | 16 12 12 12 10 8 7 2 |
| Lich King (Minotaur race), two-handed axe | 9 7 7 7 6 1 1 1 | 15 13 12 12 12 9 10 12 | 16 14 12 11 11 11 11 5 | 13 11 11 12 7 6 4 1 |
| Nosferatu (Vampire), two daggers | 9 7 5 5 5 2 2 3 | 19 12 11 11 11 7 9 14 | 25 18 14 12 14 19 23 4 | 21 15 13 12 10 8 6 1 |
| Master (Monk), staff + Unarmed | 8 6 6 4 4 3 2 2 | 17 14 12 11 10 6 7 10 | 19 16 15 14 13 18 18 4 | 18 17 14 13 9 9 7 2 |
| Master Archer, bow | 5 4 3 3 2 1 1 1 | 13 13 10 7 7 6 6 7 | 16 15 10 9 9 12 12 5 | 19 14 17 11 11 7 6 2 |
| Arch Mage, Fire | 40 7 7 3 3 1 1 1 | 31 27 23 22 20 12 17 40 | 39 33 23 11 19 23 34 6 | 23 19 14 9 5 4 3 1 |
| Master of Elements, four elements | 31 19 5 4 4 1 1 1 | 40 40 40 16 15 11 7 40 | 40 40 40 11 40 40 40 3 | 15 11 15 11 11 7 7 1 |
| Assassin, two daggers | 5 4 3 2 2 2 1 2 | 10 8 8 7 6 5 5 7 | 14 10 8 7 7 10 11 4 | 19 10 8 8 6 4 4 1 |
| Priest of Light | 3 2 2 2 2 1 0 1 | 5 5 4 3 4 4 5 4 | 8 6 5 4 4 6 7 1 | 6 4 4 3 2 2 2 0 |
