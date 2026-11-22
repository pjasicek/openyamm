# Xeen promotion playthrough

A headless run of the Xeen promotion quests (devdocs/xeen/QUESTS.md §3: five tier-1 quests, tier 2 with Light or Dark,
five racial), as evidence that each can be done and that it promotes the right classes. Built and run by the
[Playthrough playbook](../../PLAYBOOK.md) with the main chain's rules ([../run.py](../run.py)), on the model of MM9's
`tests/playthrough/mm9/promotions/`. Owner: A3 (sub-lane A3-promo). Not in CI; a long check (AGENTS.md).

    python3 tests/playthrough/xeen/promotions/run.py --start   # copy the main chain's checkpoints (STARTS), run all
    python3 tests/playthrough/xeen/promotions/run.py 31 33     # some segments (their starting checkpoints must exist)
    python3 tests/playthrough/xeen/promotions/class_table.py   # rewrite the class-table segments, print the coverage
    python3 tests/playthrough/xeen/promotions/run.py --reload  # the save-and-load run

Output (git-ignored): `output/playthrough/xeen/promotions/checkpoints/`, `logs/`, `report.md`; `reload/` for the
save-and-load run (`--start` refreshes its starting copies too). Every run also checks each segment's
`CONVENTION prerequisite` line (D-75): it must end `; proven by <test path>`, that test must exist and assert the
line's qbit (`qbit_set`); a miss is an ISSUE (printed, in the report's "ISSUE" section, and the run fails). Binary:
`build-xeen/game/openyamm` (A1's). A full run takes about two minutes, `--reload` about three.

## What is checked

The class lines are `Xeen.Promotions` in `assets_dev/worlds/xeen/events/common/xeen_common.lua` (hand-written, A3).
Each promotion quest promotes, at its hand-in, every member whose class is a "from" of its row and pays its experience
whoever it promotes (MM9's composite model); the promoter then keeps a topic (or a map hook) that promotes members
eligible later, unpaid.

1. **Every promotion quest played** as a player would (talk by the line, dungeons walked, exits by their prompts), its
   completion and rewards asserted (done bits, experience per member, items).
2. **The chain party's own promotions**, asserted by class: the party is the main chain's Knight, Paladin, Sorcerer,
   Ranger. The main chain itself plays T1-A (09: Cavalier, Crusader, Hunter), T1-B (17: Wizard), Q-D10 (49: Ranger
   Lord), Q-D6 (63: Hero), Q-D18 (65: Archmage). This chain adds T2-A (31: Cavalier -> Champion), Q-D17's oath
   (35: Crusader -> Villain) and Q-D11's burning (47: Hunter -> Bounty Hunter).
3. **Quests that promote nobody in the party**: rewards paid, classes kept, the later-members topic not offered:
   Q-C10 (11), Q-C4 (21), Q-D22's joining (81), Q-D20 (85), Q-D23's release (89: the Archmage stays an Archmage, the
   ritual is not asked), Q-D3 (91), Q-D14 (95), Q-C7 (61), Q-D13's tribute (63) and its fight (69: the vacant throne),
   Q-C25's first volume (67); the main chain plays
   T1-E (21), Q-C17 (17), Q-D25 (57) and Q-D19 (55) with nobody to promote. Promoters whose quest pays only on a
   promotion or needs an eligible member (T2-LEAFPOINT 51, T2-CLAN 25, Q-D19's inner circle 55, Q-C25's Great Wyrm 67)
   get one by a logged test setup (`SetPlayerClass`, as the class table), the party's classes put back after; so do
   the later paths of Q-D13's two endings (63's Sacrifice one, 69's vacant throne: two Trolls, D-74 3), each Troll
   logged just before its `SetPlayerClass` in D-77's fixed form (`devdocs/xeen/reviews/D77_DECISION.md` Q2:
   `CLASSES test setup later-member Q-D13: member N <before> -> Troll by SetPlayerClass, standing for a Troll
   recruited after <the ending> (D-74 3)`). These are test setups, not CONVENTIONs: each later path is first played
   with nobody eligible, only the class changes, and the unpaid result is asserted.
4. **The Light or Dark rule** (D-74 2: no crossing; a later member may use either surviving promoter): a member promoted
   on one path is no longer of the class the other path's quest promotes, so that quest leaves him alone. Segment 35:
   the Champion (Light, Dimitri) is not made a Black Knight by the Voweless oath while the Crusader beside him becomes a
   Villain; 89: the Archmage (Light, Nasir) is not made a Lich by Sandro; every class-table round 1 also gives a member
   the other path's result (a Black Knight at Dimitri, a Villain and a Priest of Dark at Dreyfus, a Priest of Light at
   Morbius), who must stay. `class_table.py` asserts the invariant on load: no "from" class of a tier-2 or racial row
   of `Xeen.Promotions` is a step-2 class in `class_extra.txt` (it stops with the faulty rows). Engine item O2 will add
   an explicit per-character Light/Dark choice inside `Xeen.promotionTarget` / `Xeen.promote`; no quest file changes.
5. **The class table in bulk** (`class_table.py`, from `Xeen.Promotions`): at each promoter, once his quest is done,
   round 1 gives the members the row's "from" classes and classes the row must leave alone (its own results, the other
   path's results, the line's earlier step) by a logged test setup (`SetPlayerClass` in a `lua_event`, as MM9); the
   promote is picked, every class asserted, and it is no longer offered (or, for a topic with states and a map hook,
   says its nobody-left line). Round 2 has nobody eligible: the promote is not offered (or says that line). The party's
   own classes are put back. Map hooks (the coven's cauldron, the oath plaque, the horned throne) are played by their
   click and question.
6. **The party can act (D-82, `devdocs/xeen/reviews/D82_DECISION.md` point 5):** the main runner checks every segment
   before its last save (no member Dead, Eradicated, Petrified, Paralyzed or Unconscious; `PARTY NN end` in the
   report), and each hand-in and class table asserts the same just before it (`PARTY NN before <hand-in>`): their
   results read every member's experience or class. A member who is down is cured at the first temple on the route
   (`heal_at_temple: {house, min: 0}`) or the cause is fought first; neither is a CONVENTION. Lesser conditions are
   logged only.

## Blocks

Each block starts from a copy of the main chain's checkpoint just before or after the quest it covers (`run.py`
STARTS: `00_main_NN.oysav`), so nothing the main chain plays is replayed. Every segment is a branch; a block's later
segments load its earlier ones.

**State (2026-11-21 21:20, A3-promo session 7):** binary build-xeen of merge point 37 (18:35:58); fresh starts copied
by `--start` from the main chain's checkpoints of A3 session 33 (merge point 37, 20:08-20:39), on the maps rebuilt since
session 6 (X1, X2 by D-85/D-88, X4, X5, X6, D1, D2, D3, D6, D7, P1, XD-12). The whole folder, 41 segments: normal 41 of
41 pass twice (21:01, 21:10); `--reload` 21:01: 41 of 41 pass (1,454 reloads). D-75: 2 lines proven, no ISSUE, no
BLOCKER. **D-82:** the main runner's party check runs before every segment's last save (`PARTY NN end`, the report's
PARTY section; a member Dead, Eradicated, Petrified, Paralyzed or Unconscious fails the segment), and every hand-in and
class table first asserts that no member is down (`PARTY NN before <hand-in>`, D-82 point 5; class_table.py writes it
before the rounds). The causes answered as a player would (D-82 3) are in "Known failures" below; session 7 added one
(21: XD-22's clan master's hall knocks a member Unconscious at the stair head in the reload run; the hall is now fought
from the stair) and, by D-85, lowered Danulf's ring clear (03) from 9,000 back to 3,000 (3 of 3 clean in each mode with
X2's sprite markers moved). Lesser conditions (Weak, Diseased, Poisoned) are logged only. Earlier: session 6 (18:43
normal, 18:54 `--reload`) on A3 session 32's checkpoints.

| Block | Segments | Start | Quests and tables | Normal (x2) | Reload |
| --- | --- | --- | --- | --- | --- |
| A tier 1, main chain's | 01, 03, 05 | main 09, 17, 21 | tables: Valia (T1-A), Barok (T1-B), Danulf (Q-C17 elf), Roxanne (T1-E, XD-07 walked) | pass | pass |
| B T1-C | 11, 13 | main 21 | Q-C10 played (X4, XD-26): 9,000 each, treasure, nobody promoted; tables: Carlawna, the Autumn Druid | pass | pass |
| C T1-D, T2-CLAN | 21, 23, 25, 27 | main 33 | Q-C4 played (X5, XD-22): 16,000 each, nobody promoted, the Clan Master alive on arrival; Kai Wu's table; T2-CLAN (Shinobu in XD-22's cellar; CONVENTION prerequisite m20.started, D-75): an Initiate a Ninja, 3,000 each; Shinobu's table | pass | pass |
| D tier 2, Kalindra, D5, Ogre Pass | 31, 33, 35, 37, 41, 43, 45, 47, 49 | main 59, 49, 63, 65, 43 | T2-A played (no workaround since merge point 31): Cavalier -> Champion; Q-D17 oath: Crusader -> Villain; the oath plaque's table (oath_again); Q-D11's forts burned after the peace: Hunter -> Bounty Hunter, 1,000 each and 1,000 gold; tables: Dimitri, Sharla, Dreyfus, Nasir, Kramer | pass | pass |
| E Leafpoint | 51, 53 | main 57 | T2-LEAFPOINT (D4; CONVENTION prerequisite q-c15.done, D-75): a Great Druid an Arch Druid, 3,000 each; Leafpoint's table | pass | pass |
| G the inner circle | 55, 57 | main 55 | Q-D19's Master Thief (DD-06 walked again): a Rogue an Assassin, nothing paid; his table | pass | pass |
| R racial | 61-69 | main 35, 49, 57, 83 | Q-C7 played (X3, XD-24): 10,000 each; Q-D13's tribute (DD-11A, DD-11C) and D-74's new Sacrifice one states; Q-D13 fought (69: Hobstadt killed, the vacant throne: nobody a Troll, then two later Trolls); the horned throne again (DD-12 walked); Q-C25 (X7, XD-18; CONVENTION gems): a Dragon a Great Wyrm, 12,000 each; tables: Du Monay, Hobstadt, the horned throne (later Minotaur), Scaldrith | pass | pass |
| F Lakeside, Luna, Sandro | 81, 83, 85, 87, 89, 99 | main 65 | Q-D22 joined (DD-20: the trapdoor, the Golden Dragon, the riddle, the cauldron, the Head Witch's chest: the Necropolis pass); the cauldron's table; Q-D20 (DD-05 L1's Pegasus, Luna: 9,000 each, the altar); Luna's table; Q-D23 (D6, DD-21: Sandro's fall, the heart, the release: 12,000 each, the Archmage kept); Morbius's table (D-74 5, a Necromancer in round 1) | pass | pass |
| H Drawkcab | 91, 93 | main 59 | Q-D3 (D1's four monks, Reger's word): 11,000 each, nobody promoted; Reger's table | pass | pass |
| I the wizard quarter | 95, 97 | main 65 | Q-D14 (D3's guild gate, Yes; DD-19: the Mirage Guild, the mirror, Xenoc, the bolt and bridge, the ward's two lamps, Morgana; out by the gate): 10,000 each, nobody promoted, the quarter's Guild of Night open; Astra's table | pass | pass |

`class_table.py` coverage (2026-11-21): 24 of 24 rows (`quarter` at Astra, 97, since A5 opened D3's guild gate at
13:05). Each map hook's later path is in its quest file since D-74 (Q-D13's states and throne, Q-D22's cauldron
states, Q-D23 at Morbius).

## Segments

| Segment | Story | Checks |
| --- | --- | --- |
| 01_valia_table | X1, Old Valia's "Crusaders" | crusade rows; topic gone when nobody is eligible |
| 03_barok_danulf_table | X2, Barok's "Promotion", Danulf's "Patriarch" | pendant, elf rows |
| 05_roxanne_table | XD-07 walked to the east tower; "Rogues"; out | tiara row |
| 11_carlawna_scarab | Q-C10: Carlawna, the Gargoyle Eyrie walked (winch, hoist, roost), the Scarab, Carlawna | 112200-112202; 9,000 each, treasure; classes kept; no "Ordination" |
| 13_carlawna_autumn_table | Carlawna's "Ordination", the Autumn Druid's "The turning year" | seasons row at both |
| 21_kaiwu_pagoda | Q-C4: Kai Wu, the Ninja Pagoda walked to the clan master, Kai Wu | 112080-112082; 16,000 each; classes kept; no "Initiation" |
| 23_kaiwu_table | Kai Wu's "Initiation" | pagoda row |
| 25_clan_return | T2-CLAN: XD-22 again, the cellar; Shinobu without and with an Initiate, before and after m20 | 114540; 3,000 each once; Initiate -> Ninja |
| 27_shinobu_table | Shinobu's "The clan"; out of the pagoda | clan row |
| 31_dimitri_test | T2-A: Castle Kalindra walked, Dimitri, the dungeon's liches, Dimitri, out | 114520-114522; 6,000 each; **Champion** Crusader Wizard RangerLord |
| 33_dimitri_table | Dimitri's "The dungeon" | dimitri row (a Black Knight kept) |
| 35_voweless_oath | Q-D17 oath: Bosco (key), the Northern Tower walked, "Chlc", the Chalice, the oath plaque | 113340-113345; 14,000 each, 2 disks; Champion **Villain** Wizard RangerLord; plaque again: nothing; Bosco refuses the Light hand-in |
| 37_plaque_table | DD-08 walked to the oath plaque (oath_again), out | knights row (a hook) |
| 41_sharla_table | Sharla's "Forest lords" (T2-LATER) | sprites row (a Bounty Hunter kept) |
| 43_dreyfus_table | Dreyfus's "Mok's blessing" (T2-LATER) | heretics row (a Villain, a Priest of Dark kept) |
| 45_nasir_table | Nasir's "Archmage's robes" (T2-LATER) | jewel row (a Lich kept) |
| 47_ogre_forts_burned | Q-D11 after the peace: DD-13's west and east forts burned (Yes), Kramer's Bounty | 113224, 113225, 113228; 1,000 each, 1,000 gold; Hunter -> **BountyHunter** |
| 49_kramer_table | Kramer's "Guild title" (T2-LATER) | bounty row (a Ranger Lord kept) |
| 51_leafpoint | T2-LEAFPOINT: Leafpoint as a stranger, as Civilized Ones without and with a Great Druid | 114560; 3,000 each once; Great Druid -> Arch Druid |
| 53_leafpoint_table | Leafpoint's "Civilized ones" | leafpoint row (a Warlock kept) |
| 55_inner_circle | Q-D19: DD-06 walked again (the gong doors open) to the Master Thief, without and with a Rogue | 113385; nothing paid; Rogue -> Assassin |
| 57_master_thief_table | The Master Thief's "New members" (T2-LATER); the chute and out | southern row (a Spy, a Master Archer kept) |
| 61_nightshadow_count | Q-C7 (X3, XD-24), see prep/F_racial.md | 112140-112143; 10,000 each; classes kept |
| 62_dumonay_table | Du Monay's "Nosferatu" | vampire row |
| 63_hobstadt_tribute | Q-D13 by tribute (DD-11A, DD-11C); D-74's Sacrifice one states by setup | 113260-113262, 113266; 4,000 each |
| 64_hobstadt_table | DD-11C walked; Hobstadt's "Sacrifice one"; out | troll row (states) |
| 65_horned_throne | DD-12 walked back to the horned throne; nobody a Minotaur | its line; nothing paid |
| 66_horned_throne_table | The horned throne again (its later-Minotaur state) | minotaur row (a hook) |
| 67_dragon_tax | Q-C25: the tax, volume 1, the Great Wyrm by setup | 112500, 112501, 112507; 12,000 each once |
| 68_scaldrith_table | XD-18 walked; Scaldrith's "Great Wyrm"; out | dragon row (states) |
| 69_hobstadt_fight | Q-D13 by the fight: D2's hole C, DD-11C, "Fight to the death", Hobstadt killed, the vacant throne, the hoard; two later Trolls by setup; out | 113263-113266; 4,000 each, 2,500 gold; throne with nobody: vacant; Troll -> War Troll twice, unpaid |
| 81_lakeside_coven | Q-D22 joined: D3 -> D4, the riddle wrong (the trapdoor), DD-20's sewer, the Golden Dragon, the cauldron cold, the riddle right, joined, the Head Witch's chest | 113402, 113442, 113448, 113449; classes kept |
| 83_cauldron_table | DD-20's cauldron ("Drink?" Yes) | coven row (a hook) |
| 85_luna_statuettes | Q-D20: D4 -> D3 -> D2 -> D1, DD-05 L1's Pegasus, Luna (three statuettes, the altar) | 113401-113407; 9,000 each; classes kept |
| 87_luna_table | Luna's "The altar's light" (T2-LATER) | statuettes row (a Sniper kept) |
| 89_sandros_heart | Q-D23: D1 -> D6, the Necropolis gate with the pass, Morbius, DD-21 walked: Sandro's fall, the sluice, the heart, the release | 113460, 113462; 12,000 each; the **Archmage kept**; no ritual asked |
| 91_drawkcab_way | Q-D3: Reger's door, the four lessons, the word, Reger | 113060-113066; 11,000 each; classes kept |
| 93_reger_table | Reger's "Masters" (T2-LATER) | drawkcab row (a Ninja kept) |
| 95_wizard_quarter | Q-D14: Astra (story, We will help), the sealed Guild of Night, the guild gate (Yes), DD-19 walked (Xenoc, the ward, Morgana), out, Astra | 113280-113284, 117520; 10,000 each; classes kept; no "The guilds' word"; the Guild of Night opens |
| 97_astra_table | Astra's "The guilds' word" (T2-LATER) | quarter row (an Assassin kept) |
| 99_morbius_table | Morbius's "Sandro" (D-74 5) | sandro row: Priest, Wizard, **Necromancer** -> Priest of Dark, Lich, Lich |

## Known failures and open findings

- **D-82 (sessions 6 and 7):** no member may be down at a segment's end or before a hand-in or class round. The cures:
  11 (X4's Chapel of the Crown after XD-26's Gargoyles, Paralyze), 85 (D1's Temple of Mok after D2), 89 (D6's
  Necropolis temple after DD-21's crypt, Dead); the temples are kept although D2's edges and D6 were rebuilt (they cost
  nothing when nobody needs them). 89's dais release is logged, not asserted: Q-D23's release reads only classes
  (`Xeen.canPromote`), and DD-21 has no temple. 55 clears 6,000 on arrival at D2's west edge (a Dark Sprite spawn
  Stoned a member during session 6's reload settles; kept). 21 (session 7, reload run, 3 of 5 condition-logged probes):
  at the head of XD-22's top stair the clan master's hall knocked members 0 and/or 2 Unconscious during the reload
  settle; the hall is now fought from the stair (`clear_hostiles: 1500` on both walks into it) and the Clan Master's
  "alive" assert (112081 clear) moved to the stair's foot; 4 of 4 probes clean. 03 (D-85): session 6 cleared 9,000
  round Danulf's ring (X2's Dark Sprites, Curse and Stone); with X2's sprite markers moved 5,888 clear (D-85, D-88)
  the ring's 3,000 passed 3 of 3 normal and 3 of 3 reload (`output/a3promo_s7/probe03.py`), so it is 3,000 again.
- **Fixed (merge point 31, 12:47):** `checkMonstersKilled` counted hidden actors dead, so DD-03's liches timer set
  `t2-a.liches_slain` at stage 1; 31 cleared it by a logged workaround. Since merge point 31 the workaround is gone:
  31 starts from main 59 rerun on the new binary, asserts 114521 clear and fights the liches.
- **Fixed (merge point 33): the Clan Master (21)** died when the armoury door (event 12) opened: `open_door`'s 1,500
  clear at z 1536 reached his dais at z 2096. Clears are storey-bound now; 21 asserts 112081 clear on arrival.
- **Fixed (A3-side, 13:00): D25-1 (66):** the horned throne promoted a later Minotaur but showed its else line;
  `q-d25.throne` is now a states hook without `once`, and 66 asserts its later-Minotaur line again ("The Minotaur sits,
  and rises a lord of the maze.").
- **Fixed (A5, 13:05): Q-D14:** D3's guild gate (event 124) asks "Enter?" and Yes enters DD-19; 95 and 97 play it.
- **Fixed (A3-side, 13:00): Q-D13 texts:** the troll holes move the party at once with a status line (D-72; 63 and 69
  assert it); after the tribute, "Sacrifice one" says "You paid. Go where you like." (63 asserts it).
- **CONVENTION lines** (D-68; prerequisites by D-75, `devdocs/xeen/reviews/D75_DECISION.md`, branch chains only): two
  `CONVENTION prerequisite` lines in the fixed form, each played closed first, asserted clear at its segment's start,
  one bit set, and checked by `run.py` (the named test exists and asserts the bit): m20.started (111400) in 25 (block
  C is on Cloudside after Q-C4; proven by `tests/playthrough/xeen/57_lost_souls.yml`) and q-c15.done (112302) in 51
  (Q-C15 is Cloudside side content; proven by `tests/scenarios/xeen/side_quests/q-c15_troll_problem.yml`). The tax
  gems in 67 are a D-68 loot CONVENTION (gems up to the fee; D-75 case 3: unchanged).
- **Necromancer:** the Standard ruleset's character creation offers Human Necromancers (MMerge class 44, step 1);
  QUESTS §3 gives the line its promotion from Sandro, so `Xeen.Promotions.sandro` has `Necromancer = "Lich"`
  (2026-11-21, kept by D-74 6). MAW's own lines (Seraphim, Death Knight, Shaman, Elementalist) have no Xeen promotion.
- **Later members (D-74 1):** every promoter keeps an unpaid later path. The NPC promoters' topics are in
  `source/quests/t2-later.yml` (A3-promo); the map hooks' later paths are in their quest files (A3-side, D-74 3-5).
- X5 says "Winterkill Tundra has changed since this save: it starts afresh" on loading main 33's checkpoint (X5 was
  rebuilt since): harmless here.
