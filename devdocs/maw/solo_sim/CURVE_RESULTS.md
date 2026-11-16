# The solo power curve against a party of five: results (2026-11-15)

The run behind [the solo power-curve direction](../../solo_action/POWER_CURVE_DIRECTION.md) §4 step 1 ("fix the
simulator"). Method and how to rerun: [README.md](README.md), "The power curve run". Work directory:
`output/maw_solo_sim_v2/` (`data_curve.json`, `curve_tables.md`). The tables are printed by
`scripts/agg_curve.py tables` and `proposals/early_cut_sweep.py`.

Read every number as a comparison, not as a prediction of play: the fights are expected values, everyone stands and
trades, nobody kites, uses terrain, crowd control or a bow opener, and conditions are left out (README "Known
limits"). The party is fought by the same model, so the solo-against-party comparison is fair to both.

## Findings

1. **The kit was the simulator's largest error, as the user suspected.** With items kept for what is on them, a bought
   weapon and armour where the loot has none, and the Hourglass, Eye and Pearl used as a player uses them, the
   level-500 Beyond Madness melee builds beat 15–86 % of groups pulled four at a time without potions, against 1–57 %
   before (the Assassin 2 % against 0 %; last table). The end-of-run Champion's "damage × toughness" doubles. The
   2026-11-14 tables and every figure quoted from them are superseded.
2. **The old level-10 stage was wrong outright:** a build whose loot held no weapon or armour of its kind fought
   bare-handed and unarmoured (a sword-and-shield Knight at 3 damage a second).
3. **The melee kits now match MAW's own design.** MAW sizes a B-tier monster to die in 2 / 3.5 / 5 attacks of the
   expected character (MAW / Nightmare / Beyond Madness). The reference party's two-handed Knight needs 0.5–2.0,
   1.0–4.3 and 1.1–8.9 along the run (seed 1), and has 100–210 % of the expected HP until late Beyond Madness (84 %).
   The casters do not: the party's Arch Mage and Priest have 20–40 % of the HP MAW expects from level 100 on (Mana
   Shield is counted in the fights, not in that figure), and the Priest needs 8–65 attacks. The party reference is
   therefore
   two strong fighters, an archer and two weak casters; a sturdier party would raise its line.
4. **Measured against the party, the solo is behind only at the start.**
   - At the start (level 5, a common weapon and armour) the party clears every map on every difficulty; the typical
     solo build clears 67 % of them on MAW, 16 % on Nightmare and none on Doom and above, even splitting groups and
     drinking.
   - The solo draws level with the party in maps cleared at level 10–20 on MAW to Nightmare, 30–50 on Doom and
     Road to Insanity, and 50–100 on Beyond Madness.
   - From level 100 on the solo is level with or ahead of the party on every difficulty: it needs fewer potions
     (Nightmare level 200: none against the party's 34 per 100 monsters) and loses nobody, while the party loses
     0.1–2.6 members per 100 monsters on Nightmare.
5. **Late Beyond Madness is hard for the party too.** From stage 400 (monsters at level 236 and above) the party
   clears 12 % of the maps and then 0–10 %; the typical solo 32 %, then 0–10 %. The end of Doom and Road to Insanity
   is similar: the party clears 60 % and 20 % of the last maps, the typical solo 100 % and 60 %. In this model that
   wall is Beyond
   Madness's own, not a solo's handicap. Real parties finish Beyond Madness with everything the model leaves out, so
   the absolute figures there say little; the comparison says the solo is not the worse off.
6. **The early cut that would level the start is nearly the same on every difficulty.** Dividing monster HP and
   damage so that a typical solo build beats whole groups as often as the party does (no potions): ÷2.5–2.9 at the
   start, ÷2.0–2.5 at level 10, ÷2.0 at 20, ÷1.8 at 30, ÷1.2–1.7 at 50, none at 100 (table below).
7. **The class spread is a caster problem.** On Nightmare every melee build and the Dragon clear 80–100 % of the
   maps from level 20 to the end (the Lich King 70 % and the Assassin 60 % at level 300); the Arch Mage, the Master of
   Elements and the Priest clear 0–80 % and collapse at level 300. They are judged without range, so this is the
   model's known blind spot as much as a
   balance fact.

## Solo against the party, by stage

Stage = the solo's character level when the snapshot was taken; the party stands at the same number of cleared maps.
"Maps cleared" = share of the ten maps around the stage fully cleared, potions allowed, a group split in fours when
it cannot be beaten whole. "Solo typical" is the median of the 22 builds, with the weakest and best in brackets.
Potions and seconds are per monster of the beaten groups; a party's potions are all five members'.

### MAW

| Stage | Level solo / party | Monsters | Maps cleared: party | solo typical (weakest–best) | Whole groups, no potions: party | solo | Potions per 100 monsters: party | solo | Seconds per monster: party | solo | Party deaths per 100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| start | 5 / 2 | 4 | 100 % | 67 % (0–100) | 94 % | 42 % | 1.0 | 29.4 | 1.0 | 2.9 | 0.0 |
| 10 | 11 / 5 | 4 | 100 % | 100 % (50–100) | 98 % | 84 % | 0.0 | 4.7 | 0.7 | 2.0 | 0.0 |
| 20 | 21 / 9 | 6 | 100 % | 100 % (90–100) | 99 % | 94 % | 0.0 | 1.1 | 0.4 | 1.5 | 0.0 |
| 30 | 30 / 13 | 12 | 100 % | 100 % (100–100) | 100 % | 90 % | 0.0 | 2.6 | 0.4 | 1.6 | 0.0 |
| 50 | 51 / 23 | 20 | 100 % | 100 % (100–100) | 100 % | 96 % | 0.0 | 1.4 | 0.5 | 1.6 | 0.0 |
| 100 | 102 / 45 | 40 | 100 % | 90 % (80–100) | 94 % | 95 % | 14.2 | 2.5 | 0.8 | 1.2 | 0.4 |
| 150 | 152 / 70 | 63 | 100 % | 100 % (70–100) | 98 % | 99 % | 1.0 | 0.0 | 0.8 | 1.1 | 0.1 |
| 200 | 200 / 98 | 101 | 100 % | 100 % (100–100) | 95 % | 97 % | 3.3 | 0.0 | 0.8 | 0.8 | 0.2 |
| 300 | 301 / 158 | 150 | 100 % | 100 % (80–100) | 100 % | 100 % | 0.0 | 0.0 | 0.8 | 0.8 | 0.0 |
| 400 | 402 / 218 | 202 | 100 % | 100 % (70–100) | 100 % | 100 % | 1.0 | 0.0 | 0.6 | 0.8 | 0.0 |
| end | 489 / 268 | 232 | 100 % | 100 % (60–100) | 100 % | 100 % | 0.0 | 0.0 | 0.8 | 0.9 | 0.0 |

### Nightmare

| Stage | Level solo / party | Monsters | Maps cleared: party | solo typical (weakest–best) | Whole groups, no potions: party | solo | Potions per 100 monsters: party | solo | Seconds per monster: party | solo | Party deaths per 100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| start | 5 / 2 | 4 | 100 % | 16 % (0–100) | 65 % | 8 % | 39.2 | 67.2 | 2.0 | 5.1 | 0.6 |
| 10 | 12 / 5 | 4 | 100 % | 75 % (0–100) | 91 % | 42 % | 7.8 | 24.6 | 1.3 | 3.0 | 0.2 |
| 20 | 20 / 9 | 5 | 100 % | 100 % (67–100) | 97 % | 83 % | 1.7 | 5.9 | 0.8 | 2.0 | 0.1 |
| 30 | 30 / 13 | 10 | 100 % | 100 % (80–100) | 94 % | 82 % | 1.5 | 5.8 | 0.6 | 1.9 | 0.1 |
| 50 | 50 / 23 | 20 | 100 % | 100 % (50–100) | 94 % | 83 % | 6.8 | 13.2 | 1.0 | 2.4 | 0.1 |
| 100 | 102 / 46 | 40 | 80 % | 80 % (50–100) | 76 % | 82 % | 57.0 | 9.1 | 1.5 | 1.7 | 2.0 |
| 150 | 150 / 69 | 63 | 90 % | 90 % (30–100) | 86 % | 89 % | 36.2 | 2.2 | 1.6 | 1.6 | 1.2 |
| 200 | 200 / 98 | 97 | 100 % | 100 % (70–100) | 76 % | 86 % | 33.7 | 0.0 | 1.5 | 1.4 | 2.6 |
| 300 | 301 / 159 | 157 | 60 % | 100 % (0–100) | 80 % | 88 % | 25.0 | 0.0 | 1.9 | 1.3 | 0.7 |
| 400 | 400 / 217 | 190 | 100 % | 100 % (40–100) | 98 % | 100 % | 2.7 | 0.0 | 1.4 | 1.1 | 0.1 |
| 500 | 502 / 276 | 240 | 100 % | 100 % (0–100) | 95 % | 95 % | 1.6 | 0.0 | 1.8 | 1.4 | 0.0 |
| end | 502 / 276 | 240 | 100 % | 100 % (0–100) | 95 % | 95 % | 1.6 | 0.0 | 1.8 | 1.4 | 0.0 |

### Doom

| Stage | Level solo / party | Monsters | Maps cleared: party | solo typical (weakest–best) | Whole groups, no potions: party | solo | Potions per 100 monsters: party | solo | Seconds per monster: party | solo | Party deaths per 100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| start | 5 / 2 | 4 | 100 % | 0 % (0–100) | 53 % | 4 % | 739.4 | 96.4 | 9.3 | 6.6 | 2.0 |
| 10 | 10 / 4 | 4 | 100 % | 40 % (0–100) | 74 % | 17 % | 167.3 | 43.9 | 3.1 | 4.1 | 0.8 |
| 20 | 20 / 9 | 5 | 100 % | 100 % (22–100) | 86 % | 54 % | 10.6 | 16.0 | 1.3 | 2.6 | 0.2 |
| 30 | 32 / 15 | 14 | 100 % | 90 % (20–100) | 75 % | 50 % | 120.6 | 25.6 | 2.3 | 2.9 | 0.5 |
| 50 | 51 / 23 | 20 | 100 % | 100 % (70–100) | 82 % | 64 % | 12.1 | 19.0 | 1.7 | 3.1 | 0.2 |
| 100 | 101 / 45 | 33 | 100 % | 100 % (100–100) | 66 % | 67 % | 10.6 | 7.0 | 1.6 | 1.9 | 0.3 |
| 150 | 152 / 71 | 52 | 100 % | 100 % (100–100) | 97 % | 98 % | 0.9 | 0.0 | 1.2 | 1.4 | 0.0 |
| 200 | 200 / 99 | 74 | 89 % | 100 % (89–100) | 84 % | 93 % | 5.0 | 0.8 | 1.3 | 1.3 | 0.1 |
| 300 | 300 / 158 | 129 | 90 % | 100 % (70–100) | 90 % | 98 % | 8.5 | 0.0 | 1.5 | 1.3 | 0.1 |
| 400 | 401 / 217 | 192 | 60 % | 90 % (0–100) | 88 % | 98 % | 20.2 | 0.0 | 1.8 | 1.3 | 0.4 |
| end | 470 / 258 | 226 | 60 % | 100 % (0–100) | 53 % | 80 % | 80.7 | 0.0 | 2.4 | 1.3 | 2.8 |

### Road to Insanity

| Stage | Level solo / party | Monsters | Maps cleared: party | solo typical (weakest–best) | Whole groups, no potions: party | solo | Potions per 100 monsters: party | solo | Seconds per monster: party | solo | Party deaths per 100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| start | 5 / 2 | 4 | 100 % | 0 % (0–25) | 43 % | 2 % | 1359.1 | 92.3 | 16.1 | 6.3 | 3.8 |
| 10 | 10 / 4 | 4 | 100 % | 30 % (0–100) | 63 % | 13 % | 459.7 | 50.8 | 6.5 | 5.0 | 1.7 |
| 20 | 20 / 9 | 5 | 100 % | 78 % (0–100) | 81 % | 40 % | 103.8 | 24.8 | 2.5 | 3.2 | 0.5 |
| 30 | 33 / 15 | 14 | 100 % | 90 % (20–100) | 77 % | 46 % | 14.9 | 24.1 | 1.6 | 2.7 | 0.5 |
| 50 | 51 / 23 | 20 | 100 % | 100 % (70–100) | 84 % | 72 % | 6.0 | 16.1 | 1.2 | 2.4 | 0.0 |
| 100 | 102 / 45 | 33 | 100 % | 100 % (100–100) | 74 % | 71 % | 2.9 | 5.5 | 0.9 | 1.4 | 0.1 |
| 150 | 151 / 70 | 52 | 100 % | 100 % (100–100) | 97 % | 97 % | 0.0 | 0.0 | 0.9 | 1.1 | 0.0 |
| 200 | 200 / 98 | 75 | 89 % | 100 % (89–100) | 77 % | 90 % | 11.0 | 0.0 | 1.2 | 1.0 | 0.2 |
| 300 | 303 / 160 | 129 | 90 % | 100 % (70–100) | 87 % | 98 % | 10.5 | 0.0 | 1.4 | 1.2 | 0.2 |
| 400 | 403 / 218 | 201 | 60 % | 90 % (0–100) | 84 % | 95 % | 36.9 | 0.0 | 2.2 | 1.5 | 0.9 |
| end | 468 / 256 | 226 | 20 % | 60 % (20–100) | 53 % | 70 % | 22.7 | 0.0 | 2.0 | 1.3 | 0.8 |

### Beyond Madness

| Stage | Level solo / party | Monsters | Maps cleared: party | solo typical (weakest–best) | Whole groups, no potions: party | solo | Potions per 100 monsters: party | solo | Seconds per monster: party | solo | Party deaths per 100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| start | 5 / 2 | 4 | 100 % | 0 % (0–33) | 29 % | 0 % | 1326.1 | 99.1 | 12.5 | 6.0 | 2.3 |
| 10 | 12 / 5 | 6 | 80 % | 40 % (0–80) | 41 % | 10 % | 2890.3 | 61.1 | 31.7 | 5.0 | 8.3 |
| 20 | 23 / 10 | 21 | 44 % | 44 % (0–44) | 26 % | 10 % | 1497.6 | 86.8 | 17.4 | 5.1 | 7.6 |
| 30 | 33 / 15 | 22 | 60 % | 40 % (30–70) | 37 % | 18 % | 431.8 | 50.0 | 6.2 | 3.7 | 1.9 |
| 50 | 52 / 23 | 26 | 60 % | 60 % (20–100) | 44 % | 32 % | 53.4 | 46.5 | 2.4 | 3.4 | 1.7 |
| 100 | 104 / 46 | 52 | 60 % | 80 % (40–100) | 46 % | 46 % | 60.6 | 30.1 | 1.8 | 2.2 | 2.1 |
| 150 | 154 / 72 | 80 | 70 % | 55 % (30–100) | 55 % | 56 % | 71.7 | 45.8 | 2.1 | 2.8 | 1.1 |
| 200 | 201 / 99 | 98 | 90 % | 90 % (60–100) | 30 % | 41 % | 26.1 | 14.0 | 2.0 | 2.0 | 0.3 |
| 300 | 301 / 159 | 159 | 33 % | 72 % (11–100) | 32 % | 53 % | 131.2 | 2.9 | 2.5 | 1.6 | 1.6 |
| 400 | 400 / 217 | 236 | 12 % | 32 % (12–100) | 9 % | 26 % | 87.2 | 3.6 | 3.1 | 2.0 | 1.1 |
| 500 | 502 / 276 | 319 | 0 % | 10 % (0–100) | 2 % | 8 % | 388.8 | 0.0 | 5.4 | 2.7 | 12.8 |
| 600 | 600 / 333 | 370 | 0 % | 0 % (0–80) | 2 % | 5 % | 243.2 | 0.0 | 4.5 | 2.2 | 9.1 |
| 700 | 703 / 393 | 445 | 10 % | 10 % (0–40) | 1 % | 4 % | 429.3 | 0.0 | 5.5 | 2.4 | 22.4 |
| 800 | 804 / 452 | 499 | 0 % | 0 % (0–0) | 0 % | 0 % | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| end | 804 / 452 | 499 | 0 % | 0 % (0–0) | 0 % | 0 % | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

The Beyond Madness "800" and "end" rows have no beaten group at all for anyone (five maps at level 499), hence the
zeros. Party potion counts at the start of Doom and above are large because five members each drink small potions
through long fights.

## By build

**Nightmare: maps fully cleared, best effort with potions (%)**

| Build | start | 10 | 20 | 50 | 100 | 200 | 300 | end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Party of five** | 100 | 100 | 100 | 100 | 80 | 100 | 60 | 100 |
| Champion, sword and shield | 0 | 100 | 100 | 100 | 80 | 100 | 100 | 100 |
| Champion, two-handed axe | 0 | 50 | 100 | 100 | 80 | 100 | 100 | 100 |
| Minotaur Lord, two axes | 33 | 67 | 100 | 100 | 80 | 100 | 100 | 100 |
| Lich King (Vampire race) | 33 | 67 | 100 | 100 | 80 | 100 | 70 | 100 |
| War Troll | 67 | 100 | 100 | 100 | 90 | 100 | 100 | 100 |
| Archangel (Seraph) | 100 | 100 | 100 | 100 | 90 | 100 | 100 | 100 |
| Master (Monk) | 0 | 83 | 100 | 100 | 80 | 100 | 100 | 100 |
| Assassin | 33 | 83 | 100 | 100 | 80 | 90 | 60 | 80 |
| Master Archer | 0 | 67 | 100 | 100 | 80 | 90 | 90 | 100 |
| Arch Mage | 0 | 17 | 67 | 70 | 70 | 80 | 10 | 60 |
| Master of Elements | 0 | 0 | 67 | 50 | 60 | 70 | 0 | 0 |
| Priest of Light | 0 | 0 | 67 | 80 | 50 | 80 | 10 | 60 |
| Great Wyrm (Dragon) | 67 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |

**Beyond Madness: maps fully cleared, best effort with potions (%)**

| Build | start | 10 | 20 | 50 | 100 | 200 | 300 | 400 | 500 | 700 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Party of five** | 100 | 80 | 44 | 60 | 60 | 90 | 33 | 12 | 0 | 10 |
| Champion, sword and shield | 0 | 80 | 44 | 60 | 80 | 100 | 44 | 25 | 10 | 10 |
| Champion, two-handed axe | 0 | 0 | 33 | 60 | 70 | 90 | 78 | 38 | 10 | 10 |
| Minotaur Lord, two axes | 0 | 20 | 33 | 60 | 90 | 90 | 78 | 38 | 20 | 10 |
| Lich King (Vampire race) | 0 | 40 | 33 | 60 | 90 | 90 | 67 | 12 | 10 | 10 |
| War Troll | 0 | 80 | 44 | 90 | 90 | 100 | 89 | 100 | 70 | 10 |
| Archangel (Seraph) | 33 | 80 | 44 | 100 | 90 | 100 | 89 | 88 | 50 | 10 |
| Master (Monk) | 0 | 40 | 44 | 60 | 60 | 90 | 78 | 25 | 0 | 10 |
| Assassin | 0 | 80 | 44 | 60 | 40 | 90 | 33 | 12 | 0 | 0 |
| Master Archer | 0 | 20 | 44 | 60 | 80 | 90 | 44 | 12 | 0 | 10 |
| Arch Mage | 0 | 0 | 11 | 30 | 50 | 90 | 11 | 12 | 0 | 0 |
| Master of Elements | 0 | 0 | 0 | 20 | 60 | 60 | 11 | 12 | 0 | 0 |
| Priest of Light | 0 | 0 | 33 | 30 | 40 | 60 | 11 | 12 | 0 | 0 |
| Great Wyrm (Dragon) | 0 | 80 | 44 | 100 | 100 | 100 | 100 | 100 | 100 | 40 |

**Beyond Madness: groups pulled four at a time, no potions (%), old run → this run**

| Build | 10 | 50 | 200 | 500 |
| --- | --- | --- | --- | --- |
| Champion, sword and shield | 14 → 15 | 32 → 33 | 98 → 99 | 1 → 20 |
| Champion, two-handed axe | 1 → 12 | 54 → 64 | 86 → 99 | 3 → 27 |
| Minotaur Lord, two axes | 6 → 37 | 85 → 84 | 98 → 99 | 10 → 62 |
| Lich King (Vampire race) | 13 → 35 | 85 → 82 | 99 → 99 | 1 → 19 |
| War Troll | 48 → 46 | 89 → 93 | 99 → 100 | 57 → 86 |
| Archangel (Seraph) | 51 → 51 | 93 → 94 | 100 → 100 | 47 → 69 |
| Master (Monk) | 25 → 31 | 50 → 53 | 91 → 98 | 2 → 15 |
| Assassin | 5 → 5 | 23 → 23 | 54 → 53 | 0 → 2 |
| Master Archer | 1 → 1 | 26 → 28 | 96 → 96 | 1 → 12 |
| Arch Mage | 0 → 1 | 56 → 56 | 75 → 98 | 0 → 1 |
| Master of Elements | 0 → 1 | 52 → 50 | 52 → 69 | 0 → 1 |
| Priest of Light | 0 → 0 | 10 → 10 | 0 → 0 | 0 → 0 |
| Great Wyrm (Dragon) | 54 → 57 | 99 → 99 | 100 → 100 | 84 → 100 |

## The early cut that levels the start

`CUT_STAGES=1,10,20,30,50,100 CUT_TARGET=party python3 proposals/early_cut_sweep.py`: the factor k by which monster HP
and damage are both divided so that the build beats the same share of whole groups, without potions, as the party
beats at that stage. Median build / Champion sword and shield / Archer / Arch Mage / worst build but the Priest.

| Difficulty | Start | Level 10 | Level 20 | Level 30 | Level 50 | Level 100 |
| --- | --- | --- | --- | --- | --- | --- |
| MAW | 2.9 / 3.6 / 5.5 / 9.0 / 9.0 | 1.9 / 2.5 / 3.1 / 1.7 / 3.9 | 8.6 / 11.5 / 17.6 / 2.1 / 29.3 | 4.3 / 5.5 / 8.2 / 1.5 / 11.9 | 1.5 / 1.8 / 1.9 / 1.1 / 2.8 | 1.0 / 1.0 / 1.5 / 1.0 / 1.9 |
| Nightmare | 2.7 / 3.6 / 4.5 / 6.7 / 6.7 | 2.1 / 2.7 / 3.7 / 2.0 / 4.5 | 1.9 / 2.5 / 3.4 / 1.7 / 5.0 | 1.9 / 2.9 / 3.2 / 1.5 / 3.6 | 1.6 / 1.9 / 2.1 / 1.4 / 2.4 | 1.0 / 1.0 / 1.5 / 1.0 / 1.6 |
| Doom | 2.8 / 4.0 / 5.0 / 6.7 / 8.5 | 2.2 / 2.9 / 3.7 / 4.4 / 5.2 | 2.0 / 2.5 / 3.0 / 1.9 / 4.4 | 1.7 / 2.1 / 2.2 / 1.8 / 2.4 | 1.4 / 1.7 / 2.0 / 1.3 / 2.3 | 1.0 / 1.0 / 1.2 / 1.0 / 1.4 |
| Road to Insanity | 2.9 / 4.6 / 5.4 / 6.7 / 9.3 | 2.2 / 3.0 / 3.6 / 4.3 / 5.6 | 2.1 / 2.8 / 3.3 / 1.8 / 5.0 | 1.7 / 2.4 / 2.7 / 1.5 / 3.6 | 1.7 / 1.8 / 2.0 / 1.2 / 2.5 | 1.3 / 1.7 / 1.5 / 1.0 / 1.9 |
| Beyond Madness | 2.5 / 4.3 / 4.5 / 6.0 / 7.4 | 2.5 / 2.9 / 4.3 / 4.7 / 5.7 | 2.1 / 2.7 / 3.2 / 4.8 / 4.8 | 1.9 / 2.7 / 3.2 / 1.8 / 3.2 | 1.2 / 1.7 / 1.9 / 1.1 / 1.9 | 1.0 / 1.4 / 1.1 / 1.1 / 1.7 |

The MAW row at levels 20 and 30 is an artefact: the party beats 99–100 % there, so the target is set by the one
largest group. A cap of 90 % on the target would give about 2 there, as on the other difficulties.

## The party line

`proposals/party_line_sweep.py` (`party_line.json`, `party_line.md` in the work directory): the factor h by which
monster HP and damage can both be multiplied while 90 % of the monsters in whole groups are still beaten without
potions, for every solo build and for the party; solo h ÷ party h is the solo's strength against the party's.
Typical build (median of 22), with the weakest and the best:

| Stage | MAW | Nightmare | Doom | Road to Insanity | Beyond Madness |
| --- | --- | --- | --- | --- | --- |
| start | 0.35 (0.12–1.11) | 0.34 (0.10–1.49) | 0.27 (0.05–1.45) | 0.29 (0.06–1.21) | 0.28 (0.05–1.30) |
| 10 | 0.46 (0.15–1.36) | 0.49 (0.17–1.41) | 0.42 (0.17–1.71) | 0.41 (0.13–1.46) | 0.33 (0.11–1.35) |
| 20 | 0.45 (0.20–1.26) | 0.54 (0.23–1.80) | 0.46 (0.19–1.96) | 0.43 (0.15–1.63) | 0.34 (0.08–1.83) |
| 30 | 0.44 (0.19–1.21) | 0.56 (0.20–1.86) | 0.51 (0.22–2.02) | 0.58 (0.22–2.50) | 0.46 (0.13–2.54) |
| 50 | 0.63 (0.22–1.45) | 0.66 (0.23–1.90) | 0.69 (0.31–2.39) | 0.70 (0.33–2.52) | 0.81 (0.32–3.27) |
| 100 | 1.04 (0.39–4.25) | 1.13 (0.42–4.76) | 0.78 (0.20–4.21) | 0.72 (0.21–4.70) | 0.53 (0.16–4.85) |
| 150 | 1.21 (0.46–4.60) | 1.20 (0.42–4.62) | 1.32 (0.48–3.64) | 1.35 (0.52–3.95) | 0.90 (0.27–4.08) |
| 200 | 1.69 (0.48–5.92) | 1.31 (0.45–6.48) | 1.42 (0.46–6.40) | 1.40 (0.37–5.88) | 0.96 (0.22–4.60) |
| 300 | 1.97 (0.62–5.60) | 1.55 (0.39–7.41) | 1.64 (0.44–6.30) | 1.54 (0.43–7.08) | 1.52 (0.46–7.94) |
| 400 | 1.72 (0.46–5.40) | 1.68 (0.37–5.48) | 1.73 (0.47–7.05) | 1.45 (0.45–6.14) | 1.00 (0.21–8.61) |
| end | 1.47 (0.48–5.62) | 1.35 (0.43–6.48) | 1.95 (0.29–9.18) | 1.56 (0.24–7.23) | 0.93 (0.32–7.20) |

The weakest is the Priest throughout and the best the Dragon. A solo starts at about a third of the party, crosses it
between level 100 and 150 and stays at 1.3 to 2 times the party (about level with it on Beyond Madness). It is the
budget any solo rule has to respect if a solo is never to be stronger than a full party
([direction §7](../../solo_action/POWER_CURVE_DIRECTION.md)); the cut proposed there ends at level 75.

## Rerun with Lone Discipline (2026-11-15, night)

The solo builds above had no Lone Discipline, the solo run's innate rule: every class may train Bodybuilding and
Regeneration (`gen_pool.py` `LONE_DISCIPLINE`; `LONE=0` gives the earlier cases, whose outputs are kept in
`before_regeneration/` of the work directory). The rerun trains Regeneration at weight 0.6 on every solo build and
Bodybuilding at 0.8 where its cap is lifted; the party's members are unchanged. **Every table above this section is
the run without it.** The simulated Regeneration matches the game's: a level-20 Archer on Nightmare has 184 HP and
regenerates 10 HP a second in combat; the user's level-15 Dark Elf measured about 6 to 8 on 170 HP.

Solo strength ÷ party strength with Lone Discipline, typical build (weakest–best):

| Stage | MAW | Nightmare | Doom | Road to Insanity | Beyond Madness |
| --- | --- | --- | --- | --- | --- |
| start | 0.38 (0.18–1.11) | 0.34 (0.18–1.49) | 0.33 (0.17–1.45) | 0.31 (0.17–1.21) | 0.33 (0.16–1.30) |
| 10 | 0.51 (0.25–1.36) | 0.52 (0.31–1.41) | 0.46 (0.31–1.71) | 0.44 (0.28–1.46) | 0.36 (0.22–1.35) |
| 20 | 0.52 (0.37–1.26) | 0.61 (0.39–1.80) | 0.54 (0.30–1.96) | 0.43 (0.27–1.63) | 0.40 (0.23–1.83) |
| 30 | 0.50 (0.34–1.21) | 0.62 (0.37–1.86) | 0.57 (0.43–2.02) | 0.59 (0.39–2.50) | 0.48 (0.27–2.54) |
| 50 | 0.69 (0.38–1.45) | 0.74 (0.41–1.90) | 0.75 (0.51–2.39) | 0.79 (0.44–2.52) | 0.80 (0.61–3.27) |
| 100 | 1.31 (0.53–4.25) | 1.29 (0.58–4.76) | 0.89 (0.45–3.93) | 0.88 (0.39–4.70) | 0.63 (0.30–4.85) |
| 150 | 1.54 (0.69–4.60) | 1.39 (0.63–4.62) | 1.58 (0.70–3.64) | 1.52 (0.75–3.95) | 0.99 (0.54–4.08) |
| 200 | 1.98 (0.73–5.92) | 1.77 (0.69–6.48) | 1.81 (0.69–6.40) | 1.75 (0.59–5.88) | 1.16 (0.55–4.60) |
| 300 | 2.33 (0.89–5.60) | 1.97 (0.68–7.41) | 2.18 (0.67–6.30) | 2.03 (0.75–7.08) | 2.04 (0.70–7.94) |
| 400 | 2.11 (0.78–5.40) | 2.13 (0.62–5.48) | 1.98 (0.78–7.05) | 1.85 (0.82–6.14) | 1.38 (0.43–8.61) |
| end | 1.94 (0.69–5.62) | 1.83 (0.73–6.48) | 2.28 (0.63–9.18) | 1.96 (0.49–7.23) | 1.55 (0.32–7.20) |

Against the run without it the typical solo gains 0.03 to 0.08 up to level 50 and 0.15 to 0.5 from level 100;
two-handed Knights and the Priest gain most early (a Knight 0.28 → 0.38 at level 10 on Nightmare). The start is still
far under the party: Regeneration does not change that a fresh solo stands in a whole group alone.

The cut that would level a solo with the party, with Lone Discipline (median build / Champion sword and shield /
Archer / Arch Mage / worst but the Priest):

| Difficulty | Start | Level 10 | Level 20 | Level 30 | Level 50 | Level 100 |
| --- | --- | --- | --- | --- | --- | --- |
| MAW | 2.9 / 2.6 / 3.5 / 4.7 / 5.5 | 1.8 / 1.8 / 2.4 / 1.4 / 2.4 | 6.2 / 6.1 / 8.1 / 2.0 / 10.7 | 3.0 / 3.2 / 4.1 / 1.2 / 5.6 | 1.3 / 1.3 / 1.4 / 1.0 / 1.7 | 1.0 / 1.0 / 1.0 / 1.0 / 1.1 |
| Nightmare | 2.6 / 3.3 / 3.5 / 4.5 / 4.9 | 2.0 / 2.3 / 2.7 / 1.7 / 2.7 | 1.7 / 1.8 / 2.0 / 1.6 / 2.5 | 1.6 / 2.1 / 2.1 / 1.4 / 2.5 | 1.4 / 1.5 / 1.7 / 1.4 / 1.7 | 1.0 / 1.0 / 1.0 / 1.0 / 1.0 |
| Doom | 2.7 / 3.3 / 3.6 / 4.6 / 4.9 | 2.2 / 2.3 / 2.8 / 3.0 / 3.1 | 1.9 / 1.9 / 2.4 / 1.7 / 3.0 | 1.6 / 1.8 / 2.0 / 1.5 / 2.0 | 1.2 / 1.3 / 1.4 / 1.1 / 1.7 | 1.0 / 1.0 / 1.0 / 1.0 / 1.1 |
| Road to Insanity | 2.8 / 3.4 / 4.0 / 4.6 / 4.7 | 2.1 / 2.4 / 2.7 / 2.9 / 3.4 | 2.1 / 2.3 / 2.5 / 3.0 / 3.0 | 1.6 / 1.9 / 2.3 / 1.5 / 2.4 | 1.4 / 1.6 / 1.6 / 1.0 / 2.0 | 1.1 / 1.3 / 1.2 / 1.0 / 1.5 |
| Beyond Madness | 2.5 / 2.9 / 3.9 / 4.5 / 4.5 | 2.3 / 2.2 / 3.1 / 3.3 / 3.4 | 1.9 / 2.2 / 2.7 / 3.4 / 3.4 | 1.9 / 2.0 / 2.5 / 1.6 / 3.0 | 1.1 / 1.5 / 1.6 / 1.0 / 1.6 | 1.0 / 1.1 / 1.1 / 1.0 / 1.5 |

(The MAW row at levels 20 and 30 is the same artefact as before.) On Nightmare: ÷2.6 at the start, 2.0 at level 10,
1.7 at 20, 1.6 at 30, 1.4 at 50, none at 100. That is close to the first table built in the game (2.5, 2.0, 1.8,
1.7, 1.4, 1.1 at 75) and above the lowered one the user chose by play (2.5, 2.0 at 5, 1.6 at 10, 1.4 at 20, 1.25 at
30, none from 50): [direction §8](../../solo_action/POWER_CURVE_DIRECTION.md). The user then took the simulation's
1.4 at 50 with a linear fade to nothing at 75 (2.5, 2.0 at 5, 1.6 at 10, 1.4 at 50, none from 75), keeping the
start their play had set.

Why play felt easier than these numbers say: the party itself beats 91 to 97 % of whole groups without a potion at
levels 10 to 20 on Nightmare, so "as strong as the party" there already means hardly ever dying; and the user fought
with a bow from range, which this model does not credit (every monster of a group hits from the first moment).

## What this means for the direction

- **The benchmark "about as hard as a party of five" is met from about level 100 without any solo rule,** and
  missed badly before level 20–50. The solo layer's first job is the start, not the end.
- **An early cut of about ÷2.7 fading to nothing by character level 100** (monster level about 40) makes the start
  as hard as a party's on that difficulty. (Later the same day the cut was set at ÷2.5 fading out by level 75, to
  leave room for the early talents: direction §7.) It is one curve for all difficulties, which keeps "MAW is for
  people who know what they are doing, Doom needs the quest route" exactly as MAW has it for parties.
- **Talent points and the tree do not have to carry late Beyond Madness for the solo to be "as hard as a party".**
  Whether Beyond Madness should be made easier than a party finds it is a separate decision.
- **Casters need the range model** before anything is concluded about them.

## Playing the simulated characters

`scripts/gen_solo_stages.py` writes the solo stages of the debug console's `testparty`
(`assets_dev/engine/rulesets/maw/debug/test_parties.yml`): levels 10, 50, 100, 200, 300 and 500 on MAW, Nightmare and
Beyond Madness, and `solo_madness_end` (level 804). Each stage now carries `builds`: for the eight solo test parties
the simulation's own character at that stage, with its stats, skills and the kit it chose and crafted
(`game/debug/MawTestParties`, `MawTestPartyBuild`). For example:

```
testparty solo_madness_500 solo_champion nightmare beyond_madness horizontal solo
testparty solo_nightmare_10 solo_archer nightmare free solo
```

Checked headless: the Champion of `solo_madness_500` wears all 14 items of its kit. Not carried over: the potion
buffs the simulation assumes (drink them from the stage's kits) and the Elder and Ultimate promotions of several
continents. The `.oysav` saves made on 2026-11-14 predate this and still hold the randomly rolled gear.

## Not done

- The party reference is one composition and one skill split per member; its casters are weak (finding 3).
- No ranged approach, kiting or crowd control (the talent fight model `talentfight.py` has range; it was not rerun on
  the new kits and stages).
- No shops beyond the plain weapon and armour, no gold, no Mirror or Orbs, no farming.
- The start scenarios "after the peaceful quest route" and "bow opener" are not built.
- The talent tables (`TALENT_TREE_V2_RESULTS.md`) still stand on the old kits.
- The public page was not rebuilt.
