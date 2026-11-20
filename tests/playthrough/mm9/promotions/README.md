# MM9 promotion playthrough

A headless run of every MM9 promotion quest (the guide's "Promotion quests" section,
https://jasicek.net/openyamm/mm9-guide/#quests-promotion, built from `tools/mm9_site/story/side_*.yml`), as evidence
that each quest can be done and that it promotes the right classes. It is built and run by the
[Playthrough playbook](../../PLAYBOOK.md), with the main run's rules ([../README.md](../README.md)).

    cmake --build build --target openyamm -j25
    python3 tests/playthrough/mm9/promotions/run.py --start   # copy the main run's checkpoints 53 and 60, run everything
    python3 tests/playthrough/mm9/promotions/run.py 33 34     # some segments (their starting checkpoints must exist)
    python3 tests/playthrough/mm9/promotions/class_table.py --e-members 2   # rewrite 77, 84, 90-95 (MM9.Promotions)
    python3 tests/playthrough/mm9/promotions/run.py --reload  # the save-and-load run

Output (git-ignored): `output/playthrough/mm9/promotions/checkpoints/`, `logs/`, `report.md`. A full run takes about
20 minutes (the Lich Lab's walks are most of it).

State on 2026-11-09: all 53 segments pass twice and once with save and load.

## Starting point

`checkpoints/00_start.oysav` is a copy of the main run's `53_connecting_tunnels.oysav` (`run.py --start` makes it):
the party has reached Yorwick at the start of Chapter II, so every town, Lindisfarne, Frosgard and the Lich Lab
behind Yorwick are open. The party is the main run's new game: Knight, Cleric, Thief, Sorcerer (members 0-3).
Block E's branch starts from `00_after_krohn.oysav`, a copy of the main run's `60_krohn.oysav` (see Blocks).

## What is checked

The class lines are `MM9.Promotions` in `assets_dev/worlds/mm9/events/common/mm9_common.lua`
(devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes"): each quest promotes every member whose class is a
"from" of its row, at once, and pays its experience and gold whoever it promotes; once done, the promoter keeps
"Promote our eligible characters." (`assets_dev/worlds/mm9/dialogue/promotions.yml`), which promotes those eligible
now, without rewards.

1. **Every quest played** as a player would (talk by the line, dungeons walked, items picked up), its completion and
   rewards asserted (done key, gold, experience).
2. **The party's own promotions** where its classes fit, asserted with `classes()`:
   Mercenary (Knight -> Cavalier, Thief -> Rogue), Healer (Cleric -> Priest), Scholar (Sorcerer -> Wizard),
   Assassin (Rogue -> Assassin), Priest (Priest -> PriestLight), Lich (Wizard -> Lich).
3. **Any order, natural**: the Gladiator labours are done before the Mercenary promotion (rewards, nobody promoted);
   once the Knight is a Cavalier, Fridleif's "Promote our eligible characters." makes him a Champion. The Mage quest
   is done while the Sorcerer is still a Sorcerer (rewards only); after the Lich, Johannes has nobody to promote.
4. **Quests that promote nobody in this party** (Crusader, Ranger, Paladin, Druid, Mage): rewards paid, classes kept.
5. **The class table in bulk** (segment 90+): at each promoter, after his quest is done, the members are given that
   row's "from" classes four at a time (a logged test setup, `lua_event` `SetPlayerClass`), "Promote our eligible
   characters." is picked and every member's new class is asserted, together with one member of an ineligible class
   that must stay; picked again it must say "No one among you can take this promotion now.". The party's own
   classes are put back after. No quest is replayed for this; `class_table.py` writes these segments.

## Blocks

Segment numbers by block (two digits; gaps for inserts). Each block's prep sheet is `prep/<block>.md`.

| Block | Segments | Quests | Party's promotions |
| --- | --- | --- | --- |
| A Gladiator, Mercenary | 01-15 | Fridleif's three labours (basilisk skin, Kira's shield, the Arena at Lord level); Thorfinn's errand, Atli Sigmundssen's boat watch; Fridleif again | Mercenary: Cavalier, Rogue; then Champion at Fridleif |
| C Healer, Priest | 20-29 | Tjolnir (the Old Hag's hair, Nutty Nurtigan); Gray Slemnir's three tasks (young priest, Tree of Life, the Ritual) | Priest, then PriestLight |
| D Mage, Scholar, Ranger | 30-45 | Johannes's diary (rewards only), Tymon's Magreeb; Fenja's trials (Everstrike, Dungeon of Secrets / Chadwick's course) | Wizard |
| B Assassin, Crusader, Lich | 50-65 | Atli the Quick's two tasks; Keith Bloodaxe's Yobboes and the three items; the Lich Instructions and the Lich Lab | Assassin; Lich |
| E Paladin, Druid (own branch) | 70-85 | Grehgknak's Three Crusades (Sven, Harris Willington, the Oords); Menja and the Green Man's three tasks; the class table at Grehgknak and the Green Man | none |
| G Class table | 90-99 | the other promoters' "Promote our eligible characters." in bulk | every other row of `MM9.Promotions` |

Block E is a branch of its own. From the war council (key 40) until Krohn's task (key 108) every Jarl is away: Jarl
Sven and Jarl Tryygva are hidden, as in MM9 (NPC3.scr and NPC180.scr: haskey 40 vanishes them, 108 brings them back;
`thjorgardcity.lua`, `frosgardcity.lua`). The Paladin quest needs Sven's first talk, and the Druid quest needs
Tryygva's runestone, so in Chapter II neither can be finished. Block E therefore starts from
`checkpoints/00_after_krohn.oysav`, a copy of the main run's `60_krohn.oysav`, the first checkpoint with key 108.

## Segments

The chain runs A (01-15), C (20-26), D (30-40), B (50-63), G (90-95), each block from the previous one's last
checkpoint; block E (70-84) is its own branch. Classes along the chain: Knight Cleric Thief Sorcerer -> (13)
Cavalier Cleric Rogue Sorcerer -> (15) Champion -> (21) Priest -> (26) PriestLight -> (36) Wizard -> (52) Assassin ->
(61) Lich: Champion PriestLight Assassin Lich. Reward and "classes unchanged" checks compare with the state before
the talk (`remember`/`recall`, `gold()`, `experience()`), never exact totals.

Block A (from `00_start.oysav`; `prep/A_gladiator_mercenary.md`):

| Segment | Story | Checks |
| --- | --- | --- |
| 01_fridleif_labours | Sturmford's land gate; Fridleif's three labours taken while the Knight is a Knight | key 214; no "Promote our eligible characters." yet |
| 03_basilisk_skin | out by the north gate; a basilisk outside Anskram Keep killed, its corpse searched | the Basilisk Skin |
| 05_kira_shield | Thronheim City; Kira's council room, the shield (a world item) picked up | key 216 |
| 07_arena_lord | Thjorgard City, the Arena walked; "Send us in at Lord!", the fight won, "We won!" | keys 1007, 1011, 1020, 217 |
| 09_gladiator_done | the three hand-ins, "We've completed all the labors." | keys 215, 218-221, 26; +5 000 gold, +37 500 experience each, **nobody promoted**; the promote line answers "No one ..." |
| 11_thorfinn | Thronheim's tavern: Thorfinn's errand | key 124 |
| 13_atli_boat | Guberland: Atli, the boat watch on the rest screen (2, 3, 6 AM), the raiders | keys 125, 197, 126, 127; Knight -> Cavalier, Thief -> Rogue; +1 000 gold, +16 500 experience each |
| 14_thorfinn_after | Thorfinn's promote line after the quest | nobody to promote, nothing paid |
| 15_champion | Fridleif's "Promote our eligible characters." | Cavalier -> Champion, nothing paid |

Block C (from 15; `prep/C_healer_priest.md`):

| Segment | Story | Checks |
| --- | --- | --- |
| 20_tjolnir_hag_hair | Guberland City: Tjolnir's quest; Skarphedinn; the Lock of Hair at the Hag's stool | keys 206-208 |
| 21_nurtigan_healer | the potion's wait, the potion, Nurtigan cured, Tjolnir | keys 209-213; Cleric -> Priest; +1 000 gold, +16 500 experience each |
| 22_slemnir_tasks | Tjolnir's promote line (nobody); Gray Slemnir's three tasks | keys 250-252, 259 |
| 23_lindisfarne_priest | the monastery walked (no monk hurt): the Abbot, a day's rest, Robert Aefgil | keys 253-255 |
| 24_nathi_ritual | Frosgard City: Nath'i A'Mor writes the Ritual | keys 257, 258; +5 000 experience each |
| 25_ruined_temple_tree | the Ruined Temple walked in and out: the lift, the crypt, the spiral, the Tree of Life | key 256 |
| 26_slemnir_priest | Gray Slemnir's report | keys 260, 261; Priest -> PriestLight; +5 000 gold, +37 500 experience each; promote line answers "No one ..." |

Block D (from 26; research and routes: `prep/D_mage_scholar_ranger.md`):

| Segment | Story | Checks |
| --- | --- | --- |
| 30_johannes_task | to Thjorgard, the west gate, Johannes Bem: the diary | key 4; member 3 a Sorcerer |
| 31_verhoffin_fake_book | the Isle of Ashes; the Verhoffin Ruins walked: the bolt, the west rooms, the crevasse, Door5's key, Door5, the silver book, out | keys 281, 290; 10242 |
| 32_johannes_book_key | Thjorgard: the silver book is the wrong one | keys 286, 293, 288; 10242 gone, the Book Key 10244 |
| 33_drangheim_real_book | Drangheim: the cottage opened by the Book Key, the floorboard broken, the gold book | keys 283, 290; 10560, Eye of the Storm |
| 34_johannes_mage_done | Thjorgard: "Did that book work out for you?" | keys 289, 493, 294; +5 000 gold, +37 500 experience each, classes kept; "Promote our eligible characters." offered (nobody) |
| 35_tymon_magreeb | Tymon's task; out by the docks gate; the Magreeb sighted | keys 201, 202 |
| 36_tymon_scholar_done | Tymon: the Magreeb was green | keys 204, 205; member 3 Sorcerer -> Wizard, +1 000 gold, +11 000 experience each; Johannes offers "Promote our eligible characters." (not taken) |
| 37_fenja_trials | to Frosgard, the road gate; Fenja's Ranger's Trial | keys 238, 239, 240 |
| 38_dook_everstrike | to Guberland; the Dook's Castle and caverns walked: the shield, the caves, the rope bridges (13 logged jumps), the trapped chest | Everstrike 10184 |
| 39_dungeon_of_secrets | to Frosgard; Chadwick's trial run clean: ten sections, the pool's submerged tunnel, plate hops; his reward | keys 243, 245, 246, 247; no trap (key 244) |
| 40_fenja_ranger_done | Fenja: "We've completed the Ranger's Trial." | keys 241, 248, 249; +5 000 gold, +37 500 experience each, classes kept; "Promote our eligible characters." offered (nobody) |


Block B (from 40; `prep/B_assassin_crusader_lich.md`):

| Segment | Story | Checks |
| --- | --- | --- |
| 50_atli_tasks | Drangheim City: healed at the temple; Atli the Quick's two tasks; Guaire A'Velsi struck and killed; into Kluso's House | keys 222, 224, 225 |
| 51_klusos_house | Kluso's House walked: the library, the Blackheart (the alarm), out | key 223 |
| 52_atli_assassin | "We have completed your tasks." | keys 226, 227; Rogue -> Assassin; +5 000 gold, +37 500 experience each |
| 54_keith_yobboes | Keith's task; the Yobboe Gang dies; the herbs, plow and doll picked up | keys 128-132 |
| 55_villagers_items | the three owners take their things | keys 133-135, 198-200; +1 500 gold, +6 000 experience each |
| 56_keith_crusader | Keith's report | keys 136, 137; +5 000 gold, +16 500 experience each, **nobody promoted** |
| 58_chasm_lich_instructions | the Chasm of the Dead walked down its ledges to the X-shaped hall and back | key 296 |
| 60_lichlab_elixir | the Connecting Tunnels walked to Yorwick; the Lich Lab: jar and ingredients, cook pot and burner | the elixir in the Wizard's pack only |
| 61_lichlab_engine | walked down to the engine's pod; the switch | Wizard -> Lich, the others unchanged; +55 500 experience each; key 299 |
| 62_lichlab_out | walked out to Yorwick | |
| 63_johannes_no_one | the tunnels back; Thjorgard City: Johannes's promote line | "No one ..." (the Lich stays a Lich) |

Block G (from 63; written by `class_table.py`): 90 Fridleif (two rounds: Cavalier, Initiate, Minotaur, Troll; Dragon
and three that stay), 91 Thorfinn, 92 Keith and Atli the Quick, 93 Tjolnir and Gray Slemnir, 94 Tymon and Johannes,
95 Fenja. Each round sets the four members' classes, picks "Promote our eligible characters.", asserts every class,
and picks it again for "No one ...". The Lich row (Wizard -> Lich) is checked by block B's engine only.

Block E (from `00_after_krohn.oysav`; `cp output/playthrough/mm9/checkpoints/60_krohn.oysav
output/playthrough/mm9/promotions/checkpoints/00_after_krohn.oysav`; for `--reload`, also into `reload/checkpoints/`):

| Segment | Story | Checks |
| --- | --- | --- |
| 70_lindisfarne_grehgknak | out of the Hall of the Gods, Arslegard's bridge, the boat to Lindisfarne; the monastery walked to Grehgknak: the Three Crusades | keys 108, 153, 228, 229; the Letter; no monk hostile |
| 72_thjorgard_sven_assassin | Sven (back since 108) reads the letter; the Arena's door, Byri talked down; Sven, Harris Willington in Hreidmar's Stuff, Sven's reward | keys 230-232, 234, 235; +10 000 gold, +5 000 experience each, classes kept |
| 74_sturmford_oords | Fridleif's thieves; Hatlati arrested, the guard jails him; Itlor, Injor's job, Itlor | keys 154, 5009, 155-157 |
| 76_lindisfarne_crusades_done | the monastery walked again; "We have completed our Crusades." | keys 236, 237; +5 000 gold, +37 500 experience each, classes kept; "Promote our eligible characters." offered |
| 77_lindisfarne_paladin_table | Grehgknak's class table (Crusader -> Hero; Paladin, Hunter, Cavalier stay); out on foot | classes per round, the party's own put back |
| 78_frosgard_menja_green_man | Frosgard City: Menja; Fland on the road; the Green Man's three tasks | keys 262, 264-266 |
| 80_frosgard_city_tasks | Soxolf's maypole (500 gold) and pledge, Gudrun, Goti, Tuathal, Tjorvi; Tryygva (back since 108) and the runestone | keys 267-273, 277 (+5 000 experience each), 278; -500 gold |
| 82_frosgard_green_man_done | "We have completed your tasks." | keys 279, 280; +5 000 gold, +37 500 experience each, the amulet, classes kept; "Promote our eligible characters." offered |
| 84_frosgard_druid_table | the Green Man's class table (GreatDruid -> ArchDruid, DarkElf -> Patriarch; Druid, Priest stay) | classes per round, the party's own put back |

77 and 84 are written by `class_table.py` (`--e-members`: the party size at the branch's start): a four-class
round is played in chunks of the party's size.

## Known failures and open findings

- The Arena forbids saving since 2026-11-09 (as MM6-MM8's arenas; its map-load reset used to lose a won Lord fight's
  purse and Sven's staging on a load), so `--reload` skips the saves inside it in 07 and 72.
- The Dungeon of Secrets forbids saving too since 2026-11-09 (it starts a fresh trial on every load of the map), so
  `--reload` skips the saves inside it in 39.
- Logged ISSUEs: the Dook's caverns' rope bridges need 13 jumps (38); three hops in the Ruined Temple (25). (The
  Drangheim floorboard that "did not break" broke once the party was alive.)
- Items given on the cursor are put into the packs (`stow()`), as a player does: an item on the cursor stops attacks.
- **The party's health.** The main run's checkpoint 53 (this chain's start) used to have all four members Dead at
  1 HP, Weak, two Insane: the runner's `travel` passed its days awake (every dawn awake weakens the party and may
  madden or kill a member; the Immortal cheat keeps only the HP), and segment 01 had the party healed at Sturmford's
  temple. `travel` now passes the days as the game's travel does (resting on the road), so since 2026-11-09 the party
  arrives healthy, the temple offers no healing, and 01 checks that no member has a condition instead. Block E's
  branch starts from the main run's 60 with the same four members (77 and 84: `class_table.py --e-members 4`).
