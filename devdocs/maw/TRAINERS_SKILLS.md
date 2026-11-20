# MAW: trainers, teachers and skills

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`, compared with base
MMMerge (`reference/mmmerge`, `reference/mmerge_data_forus`) and OpenYAMM's own tables in
`assets_dev/engine/data_tables/`. This document deepens [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md) §1 and
corrects it where the code says otherwise (§8). Draft data files: [data/skill_rules.yml](data/skill_rules.yml) and
[data/mastery_requirements.yml](data/mastery_requirements.yml). Race flat bonuses live in
[data/race_bonuses.yml](data/race_bonuses.yml), class perks in [data/class_perks.yml](data/class_perks.yml).

Shorthand for MAW paths: `S` = `Scripts/General/zzMAW-Skills.lua`, `R` = `Scripts/Global/zzMAWRespec.lua`,
`MT` = `Scripts/Global/zzMAW_MoveTrainers.lua`, `IT` = `Scripts/General/zzMaw-Items.lua`,
`ST` = `Scripts/General/zzMaw-Stats.lua`, `SP` = `Scripts/General/zzMaw-Spells.lua`,
`DM` = `Scripts/Modules/MawCore/Damage.lua`, `F` = `Scripts/Modules/MawCore/Formulas.lua`,
`SK` = `Scripts/Modules/MawCore/Skills.lua`, `TT` = `Scripts/Modules/MawCore/SkillTooltip.lua`. OpenYAMM paths are
repository-relative. Mastery letters: B/N Novice, E Expert, M Master, G Grandmaster, S Supreme, `-`/`=` none.

Mode names used below (set at party creation, `Scripts/General/MenuExtraSettings.lua:237-290`): *Normal*;
*Doom* (`vars.Mode == 2`); *Insanity* ("Road to Insanity", also sets `vars.Mode = 2`); *Madness* ("Beyond Madness",
Insanity plus `madnessMode`, forces horizontal progression); *Austerity* (`vars.Mode == 8`). *Free* and *horizontal*
progression are the "Bolster monsters" toggle (`Game.freeProgression`). Difficulty (Easy to Nightmare) never changes
anything in this document.

---------------------------------------------------------------------------------------------------------------------

## 1. Trainer relocation

### 1.1 Mechanism

`MT:7-67` is a table keyed by the **map being loaded**; each entry is `{npcId, houseId}`. On every `LoadMap`, when
the per-install setting `enableAllTrainers` is true (default, `Scripts/General/zz_Maw-initialize.lua:35, 281`), MAW
calls `evt.MoveNPC(npc, house)` for every entry of that map (`MT:69-78`).

- `evt.MoveNPC` rewrites the NPC's house globally and the change is saved. MAW therefore needs "restore" entries:
  when you enter the NPC's home map the NPC is moved back home. The net effect is that a listed NPC appears in the
  listed house of whichever map you are on, and at home on its home map.
- The table has 64 entries on 19 map keys: 43 relocations and 21 home restores. It touches **21 distinct NPCs**, all
  teachers of the racial abilities (Vampire, Dark Elf, Dragon), Regeneration, Dodging, Unarmed and Identify Monster.
- Nothing else is moved. The guidebook's Alchemy, Armsmaster and Ascension (Learning) lines describe base MMMerge
  teachers (§1.4).
- `enableAllTrainers` is not a save setting: it lives in `MAWSettings.lua`, so it can differ between installs and
  takes effect on the next map load.

### 1.2 The 21 NPCs

All ids, names and homes below are identical in base MMMerge (`NPCData.txt`, `2DEvents.txt`) and OpenYAMM's
`npc.txt` / `house_data.txt` (row-by-row comparison of the NPC and house columns; no mismatch). Topic ids resolve
through `teacher_topics.txt` or, for 300-416, through `resolveMasteryTeacherTopic`
(`game/gameplay/MasteryTeacherDialog.cpp:91-98`).

| NPC | Name | Teaches (topic) | Home house | Home map |
|---|---|---|---|---|
| 172 | Flynn Shador | Expert Vampire Ability (366) | 585 House Shador | out06 Shadowspire |
| 173 | Douglas Dirthmoore | Master Vampire Ability (367) | 581 Dirthmoore Cottage | out06 Shadowspire |
| 174 | Payge Arachnia | GM Vampire Ability (368) | 580 House Arachnia | out06 Shadowspire |
| 175 | Fedwin Dervish | Expert Dark Elf Ability (363) | 516 Dervish Estate | out03 Alvar |
| 176 | Lanshee Caverhill | Master Dark Elf Ability (364) | 889 Caverhill Estate | out02 Ravenshore |
| 177 | Ton Agraynel | GM Dark Elf Ability (365) | 517 Agraynel Hall | out03 Alvar |
| 178 | Ishton | Expert Dragon Ability (369) | 572 Ishton's Cave | d17 Dragon Cave |
| 179 | Erthint | Master Dragon Ability (370) | 573 Ithilgore's Cave | d17 Dragon Cave |
| 180 | Klain Scarwing | GM Dragon Ability (371) | 574 Scarwing's Cave | d17 Dragon Cave |
| 214 | Kethric Tarent | Expert Regeneration (390) | 560 Tarent Hovel | out04 Ironsand Desert |
| 215 | William Sampson | Master Regeneration (391) | 618 Sampson Residence | out07 Murmurwoods |
| 216 | Ush the Many Tailed | GM Regeneration (392) | 885 Ush's Hut | out01 Dagger Wound Island |
| 530 | Sheldon Mist | Expert Dodging (396) | 1101 Mist Manor | 7out02 Harmondale |
| 531 | Oberic Crane | Master Dodging (397) | 987 Crane Residence | out09 Evenmorn Island |
| 532 | Kenneth Wain | GM Dodging (398) | 1132 Wain Manor | 7out03 Erathia |
| 533 | Kira Steeleye | Expert Unarmed (399) | 1101 Mist Manor | 7out02 Harmondale |
| 534 | Ulbrecht the Brawler | Master Unarmed (400) | 987 Crane Residence | out09 Evenmorn Island |
| 535 | Norris | GM Unarmed (401) | 1130 Norris' House | 7out03 Erathia |
| 536 | Alton Black | Expert Identify Monster (402) | 958 Black House | 7out04 Tularean Forest |
| 537 | Jeni Swiftfoot | Master Identify Monster (403) | 1023 Swiftfoot's House | out14 Avlee |
| 538 | Raven the Hunter | GM Identify Monster (404) | 1123 Weider Residence | 7out02 Harmondale |

Maps come from MAW's map keys (restore entries for homes). They disagree with the `Map` column of `house_data.txt`
for houses 247, 318, 319, 987, 1023 and 1576: for MM7 maps after the Bracada Desert that column is 2 higher than
the `map_stats.txt` row (987 says 70 The Barrow Downs, the house is on 68 Evenmorn). Do not resolve house maps
through that column.

### 1.3 What each map gains (the full relocation table)

| Map key (`MT` line) | House (type) | NPCs added | Skills and masteries |
|---|---|---|---|
| oute3 New Sorpigal (:8-11) | 197 Blades' End (merc guild) | 172, 175, 178 | Expert Vampire, Dark Elf, Dragon |
| | 191 Buccaneers' Lair (thieves' guild) | 530, 533, 536, 214 | Expert Dodging, Unarmed, ID Monster, Regen |
| outc2 Free Haven (:48-52) | 200 Duelists' Edge (merc guild) | 173, 176, 179 | Master Vampire, Dark Elf, Dragon |
| | 195 Smugglers' Guild (thieves' guild) | 531, 534, 537, 215 | Master Dodging, Unarmed, ID Monster, Regen |
| outa2 Paradise Valley (:56-59) | 1586 Sparring Ground (training) | 532, 535, 538, 216 | GM Dodge, Unarm, IDMon, Regen |
| | 280 The Last Chance (tavern) | 174, 177, 180 | GM Vampire, Dark Elf, Dragon |
| 7out02 Harmondale (:16-18) | 311 WelNin Cathedral (temple) | 214 | Expert Regeneration |
| 7out03 Erathia (:20-22) | 312 House of Solace (temple) | 215 | Master Regeneration |
| 7out13 Tatalia (:27) | 319 Order of Tatalia (temple) | 216, 172, 175, 178 | GM Regen; E Vampire, Dark Elf, Dragon |
| out09 Evenmorn Island (:43-46) | 247 The Laughing Monk (tavern) | 173, 176, 179 | Master Vampire, Dark Elf, Dragon |
| out10 Mount Nighon (:61-64) | 318 Offerings & Blessings (temple) | 532, 535, 538, 216 | GM Dodge, Unarm, IDMon, Regen |
| | 1576 Applied Instruction (training) | 174, 177, 180 | GM Vampire, Dark Elf, Dragon |
| out02 Ravenshore (:29-31) | 304 Sanctum (temple) | 530, 533 | Expert Dodging, Unarmed |
| out05 Garrote Gorge (:37) | 306 Sacred Steel (temple) | 531, 534 | Master Dodging, Unarmed |
| out13 Regna (:66) | 236 Pirate's Rest (tavern) | 532, 535 | GM Dodging, Unarmed |

Restore-only entries (NPC back to its home house): 7out02 (530, 533 to 1101; 538 to 1123), 7out03 (535 to 1130;
532 to 1132), 7out04 (536), d17 (178-180), out01 (216), out02 (176), out03 (175, 177), out04 (214), out06 (172-174),
out07 (215), out09 (531, 534 to 987), out14 (537).

Result per continent: Enroth gains every moved skill at E/M/GM; Antagarich gains the three racial abilities and
Regeneration (and duplicate GM Dodging/Unarmed/ID Monster teachers in Nighon); Jadame gains Dodging and Unarmed. Jadame
already has Identify Monster and Regeneration teachers, Antagarich already has Dodging, Unarmed and ID Monster.

### 1.4 Guidebook (`new_trainer_location_24.10.pdf`) versus code

| Guidebook line | Source | Check |
|---|---|---|
| Enroth race skill E/M/GM: Blades' End, Duelists' Edge, Paradise Valley tavern | MT | matches |
| Enroth Unarmed/Dodge/ID Monster/Regen E/M/GM: Buccaneers' Lair, Smugglers' Guild, Sparring Grounds | MT | matches |
| Enroth "All Master teachers are also GM teachers" | base | OpenYAMM has it: `Global_mm6_mmmerge.lua:18-77` |
| Enroth Alchemy E Castle Ironfist | base | 852 Walter Hargreaves, house 1240 outd3 (also E: 856 in Free Haven) |
| Enroth Alchemy M Free Haven | base | **not found**: Enroth's only Master Alchemy teacher is 819, house 1331, outc1 |
| Enroth Alchemy GM Castle Stromgard, Frozen Highlands | base | 819 Jacques Kohl (GM topic 413 via the Enroth GM list) |
| Enroth Armsmaster E/M/GM Free Haven | base | 1114 Lawrence Aleman (E, 1540); 860 Winston Historian (M, GM, 1281) |
| Enroth Ascension E New Sorpigal or Castle Ironfist; M, GM Silver Cove | base | 933 (1469), 880 (1225); 809 (1535) |
| Antagarich Regen E/M/GM temples of Harmondale, Erathia, Nighon | MT | matches; GM Regen also in the Tatalia temple |
| Antagarich race skill E Tatalia temple, M Evenmorn tavern, GM Applied Instruction | MT | matches |
| Antagarich Ascension E Deyja or Bracada, M Nighon, GM Evenmorn | base | 548, 587; 549 (996); 550 (988) |
| Jadame Unarmed and Dodge E Ravenshore temple, M Garrote Gorge temple, GM Pirate's Rest | MT | matches |
| Jadame Ascension E Murmurwoods, M Shadowspire, GM Garrote Gorge | base | 190 (614), 191 (579), 192 (564) |
| (not in the PDF) GM Dodging, Unarmed, ID Monster, Regen in the Nighon temple | MT | code only |

### 1.5 How OpenYAMM would express it

OpenYAMM already supports `evt.MoveNPC` (`game/events/EventRuntime.cpp:6049-6063`), stored as
`npcHouseOverrides` in the party and the save (`game/party/Party.cpp:4396-4404`, `game/maps/SaveGame.cpp:1098`), and
`NpcDialogTable::getNpcIdsForHouse` (`game/tables/NpcDialogTable.cpp:725-754`) resolves one house per NPC.

A literal port (per-map load hooks calling `MoveNPC`) would write 21 overrides into every MAW save, needs the 21
restore entries, and leaves NPCs displaced if the option is turned off. Proposed instead: a static **extra presence**
overlay owned by the MAW ruleset, read by `getNpcIdsForHouse` in addition to the home house and any override:

```yaml
# assets_dev/engine/rulesets/maw/npc_extra_houses.yml (proposal)
option: maw.all_trainers          # ruleset preference, default on; replaces MAWSettings enableAllTrainers
extra_houses:                     # npc -> houses where the NPC is ALSO present
  172: [197, 319]
  173: [247, 200]
  174: [280, 1576]
  175: [197, 319]
  176: [247, 200]
  177: [280, 1576]
  178: [197, 319]
  179: [247, 200]
  180: [280, 1576]
  214: [191, 311]
  215: [312, 195]
  216: [319, 1586, 318]
  530: [191, 304]
  531: [306, 195]
  532: [1586, 318, 236]
  533: [191, 304]
  534: [306, 195]
  535: [1586, 318, 236]
  536: [191]
  537: [195]
  538: [1586, 318]
```

- No restores, no save data, toggling the option is immediate. The guard for "already moved by an event" is moot:
  none of the 50 `MoveNPC` calls in our Lua events names any of these 21 NPCs.
- `house_data.txt` and `npc.txt` stay shared and unchanged.
- Houses list NPCs in id order (`NpcDialogTable.cpp:752`); a house with a resident proprietor keeps its own topics.

---------------------------------------------------------------------------------------------------------------------

## 2. Teacher rules

### 2.1 Horizontal skills

MAW rewrites requirements and prices only for the **horizontal skills** (`S:219`): every weapon (0-7), armour and
Shield (8-11), magic school (12-20), racial ability (21-23), Bodybuilding (27), Meditation (28), Regeneration (30),
Dodging (32), Unarmed (33), Armsmaster (35) and Learning/Ascension (38). Identify Item, Merchant, Repair, Perception,
Disarm Traps, Identify Monster, Stealing and Alchemy keep vanilla requirements and prices. OpenYAMM's Throwing skill
has no MAW counterpart; treating it as a horizontal weapon is the natural choice.

### 2.2 Skill level required (base skill, no item bonuses; `S:215-233`, checked at `S:1958`)

| Mode and progression | Expert | Master | GM |
|---|---|---|---|
| Normal or Austerity, free progression | 4 | 7 | 10 |
| Normal or Austerity, horizontal progression | 6 | 12 | 20 |
| Doom (either progression) | 6 | 12 | 20 |
| Road to Insanity | 8 | 16 | 25 |
| Beyond Madness | 10 | 24 | 40 |
| Non-horizontal skills, any mode | 4 | 7 | 10 |

No stat requirements are added. MAW only tightens the engine's verdict (`S:1953` returns unless the engine already
allowed the lesson), so every vanilla check survives: class/race limit, knowing the skill, holding the previous
mastery, the topic's `Req. Skill` or 4/7/10, the 50-point stat requirements for Master Merchant (Personality), Master
Bodybuilding (Endurance) and Master Learning (Intellect), and the GM Dodging/Unarmed cross requirement as OpenYAMM
models them today (`MasteryTeacherDialog.cpp:363-445`).

### 2.3 Prices and escalation (`S:1841-1874`)

| Mode (first match wins) | Expert | Master | GM |
|---|---|---|---|
| Beyond Madness | 15,000 | 300,000 | 1,250,000 |
| Road to Insanity | 10,000 | 50,000 | 250,000 |
| Doom (`vars.Mode == 2`) | 2,000 | 10,000 | 50,000 |
| Normal, Austerity (free or horizontal) | 1,000 | 4,000 | 20,000 |

`cost = base × (1 + N)`. N counts, over all horizontal skills of the active character:

- skills with base level above 0 and mastery **at or above** the mastery being taught;
- plus skills whose respec-remembered mastery minus 1 is **above** the taught mastery (`S:1868`). Remembered
  masteries are stored 1..4 (Novice = 1) and taught masteries are 2..4, so a remembered mastery only counts when it is
  two ranks higher. This looks like an off-by-one; a port should count `max(current, remembered) >= taught`.

Examples (Normal): the first Expert costs 1,000; Expert in a fifth horizontal skill when four are already Expert or
better costs 5,000; GM Sword with GM Plate and GM Shield costs 20,000 × 3 = 60,000. Vanilla prices (our
`masteryTeacherCost`, `MasteryTeacherDialog.cpp:146-332`) are 1,000-2,000 / 3,000-5,000 / 7,000-10,000 for these
skills, so MAW is cheaper for a first Expert and much dearer from the second GM on.

### 2.4 `CanTeachSkillMastery` (`S:1950-1973`) step by step

1. Skill not horizontal: leave the engine's result alone.
2. Engine already refused (`t.Allow == false`): leave it. The engine's gold check used the **vanilla** price, so a
   party holding at least MAW's price but less than the vanilla price is refused (MAW quirk; do not copy).
3. Base skill below the mode's requirement: refuse with NPC text 128.
4. Set the price to the MAW cost. Gold below it: refuse with text 125. Otherwise replace every number in the offer
   text ("Become Expert in Staff for 2000 gold") with the cost.

The text-128 string is forced to "You don't meet the requirements, and cannot be taught until you do." on every
action (`S:2302-2305`); our `npc_topic_text.txt` already has that wording.

### 2.5 Topic text rewrite (`S:1876-1949`)

On opening a "TeachSkill" dialogue for a horizontal skill MAW takes the teach text (the clicked topic's text from
`Teacher topics.txt`, else NPC text `298 + 3·skill + mastery`) and, for the selected character:

- every number ≥ 100 becomes the MAW price;
- the first number equal to the vanilla requirement (4/7/10), or failing that the first number ≤ 12, becomes the
  mode's requirement;
- if either is missing, `"\n\nYou need at least <req> skill and <cost> gold."` is appended (Blaster and some MM6/MM7
  texts);
- the message is rebuilt when another character is selected (action 110) and the hooks are removed on leaving
  (action 113).

Example (topic 300, Normal mode, horizontal progression, two Expert skills already): "...first you must have a skill
level of **6** with the staff and of course there is my small fee of **3000** gold." Topic 1295 (Expert Blaster, no
price in the text) gets the appended line.

### 2.6 Masteries without a teacher

Covered in §4: respec memory, the free/horizontal switch, extended-skill ladders (Cover, Mana Shield, Enlightenment,
Retaliation), Armsmaster Supreme and solo utility masteries. None of them goes through `CanTeachSkillMastery`.

### 2.7 Comparison with OpenYAMM's `MasteryTeacherDialog.cpp`

| Aspect | OpenYAMM today | MAW | Change for the MAW ruleset |
|---|---|---|---|
| Thresholds | 4/7/10 hard-coded (`:363-424`) | per mode, horizontal skills | from `mastery_requirements.yml` |
| Stat and cross requirements | stats 50, Dodging/Unarmed 10 (`:377-440`) | kept (engine) | keep |
| Price | vanilla table (`:146-332`) or `Req. Gold` | per mode × (1 + N) | ruleset price function of the character |
| Gold check | against the shown price (`:595`) | engine checks the vanilla price first | check the MAW price only |
| Class and race cap | `getEffectiveCap` (`:520-543`) | Class Skillz + Race Skillz | same call; tables per §6 |
| Offer text | generated "Become X in Y for N gold" (`:601-605`) | numbers rewritten | feed MAW numbers |
| Topic text | NPC text verbatim | numbers rewritten (§2.5) | rewrite numbers or append a generated line |
| Masteries without teacher | none | §4 | in the skill-raise path (`Party.cpp:3850-3876`), not here |
| Supreme | `SkillMastery` stops at Grandmaster | Armsmaster S | extend the enum or model Supreme as a flag |

`evaluateSkillMasteryTraining` (`:491-607`) is the single choke point for both topic and group training, so a ruleset
hook there (requirement, price, refusal text) covers MAW. The topic table's `Req. Gold` should be ignored for
horizontal skills under MAW, as MAW overrides `t.Cost`.

---------------------------------------------------------------------------------------------------------------------

## 3. Training halls

### 3.1 Time and price

- Training takes **2 days** (`S:1616-1626`, `t.Time = const.Day*2`), replacing the engine's time. OpenYAMM uses
  7 days plus the time to the next dawn plus 4 hours, 12 hours more in two MM7 halls
  (`game/gameplay/HouseInteraction.cpp:83-104`).
- Training is instant only while an online multiplayer session is active (`vars.ChallengeMode` is set only by
  `Scripts/General/zzzOnlineVariableSender.lua:299-312`; `CalcTrainingTime` at `:339-341`).
- Price: the engine formula is unchanged (OpenYAMM: level × house price multiplier × class tier, a third at least
  after the merchant discount, `game/items/PriceCalculator.cpp:352-379`). In Road to Insanity and Beyond Madness MAW
  sets the training house's price multiplier (`Val`) to `estimateSkill(level) + 4` of the selected character after
  every UI action inside a training hall (`S:1643-1658`). `estimateSkill(L)` is the skill level a character reaches
  spreading its level-up points over five skills (`Scripts/Modules/MawCore/Estimates.lua:79-95`): 4.0 at level 10,
  8.1 at 30, 11.4 at 50, 19.1 at 100, 33.7 at 200. Base multipliers are 10-80.
- Points per level-up are unchanged (§4.1).

### 3.2 Level caps (`S:1627-1675`)

At game start MAW reads every hall's cap from `House rules.txt` (`-1`/unlimited counts as 2750, minimum 10). On each
map load it rescales the halls **of the current continent only** (Jadame halls 1-6, Antagarich 7-16, Enroth 20-29;
placeholders 17-19 untouched): `cap = round(base^1.5 / 20) × 10`, Beyond Madness `round(base^1.5 / 10) × 10`.
MAW's `House rules.txt` training rows equal base MMMerge and ours.

| Hall | House | Base | MAW | Madness | | Hall | House | Base | MAW | Madness |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1564 Rites of Passage | 5 | 20 | 30 | | 16 | 1579 War College | 100 | 500 | 1000 |
| 2 | 1565 Gymnasium | 15 | 30 | 60 | | 20 | 1583 New Sorpigal Training Grounds | 15 | 30 | 60 |
| 3 | 1566 Guild Training Hall | 25 | 60 | 130 | | 21 | 1584 Free Haven Academy | 60 | 230 | 460 |
| 4 | 1567 Godric's Gauntlet | 25 | 60 | 130 | | 22 | 1585 Abdul's Discount Training | 40 | 130 | 250 |
| 5 | 1568 Assassin's School | 200 | 1410 | 2830 | | 23 | 1586 The Sparring Ground | ∞ | ∞ | ∞ |
| 6 | 1569 Balthazar Academy | ∞ | ∞ | ∞ | | 24 | 1587 Training-by-the-Sea | 20 | 40 | 90 |
| 7 | 1570 Island Training Grounds | 5 | 20 | 30 | | 25 | 1588 Wolf's Den | 100 | 500 | 1000 |
| 8 | 1571 Basic Principles | 15 | 30 | 60 | | 26 | 1589 Royal Gymnasium | 200 | 1410 | 2830 |
| 9 | 1572 In Her Majesty's Service | 25 | 60 | 130 | | 27 | 1590 Island Testing Center | 30 | 80 | 160 |
| 10 | 1573 The Proving Grounds | 25 | 60 | 130 | | 28 | 1591 Lone Tree Training | 80 | 360 | 720 |
| 11 | 1574 Trial of Honor | 200 | 1410 | 2830 | | 29 | 1592 Riverside Academy | 50 | 180 | 350 |
| 12 | 1575 Perdition's Flame | 200 | 1410 | 2830 | | | | | | |
| 13 | 1576 Applied Instruction | ∞ | ∞ | ∞ | | | | | | |
| 14 | 1577 Training Essentials | 50 | 180 | 350 | | | | | | |
| 15 | 1578 Avlee Gymnasium | 50 | 180 | 350 | | | | | | |

∞: unlimited stays unlimited (2750 → 72,110; 144,210 in Madness). Base 5 halls are first clamped to 10.

**Per-continent bolstering is not implemented.** `vars.trainings[continent]` counts trainings (only when party slot 0
trains, `S:1617-1620`; seeded from `vars.MMLVL` for old saves, `S:1610-1614`), and `S:1663-1668` sums the other
continents' counts into `bolster`, but that value is never used. The intent was presumably to raise caps with
trainings done elsewhere; a port should either implement it explicitly or drop the counter.

### 3.3 OpenYAMM

`house_rules.txt` → `trainingMaxLevel` (`HouseInteraction.cpp:1284, 1976, 2011`). The MAW ruleset can patch the
"Training halls" rows with the computed caps (two variants: normal and Madness) instead of rescaling at runtime, since
the formula depends only on the base value and the mode.

---------------------------------------------------------------------------------------------------------------------

## 4. Skill-point economy

### 4.1 Points per level

Unchanged from MM8 and OpenYAMM: a level-up to level L gives `5 + floor(L / 10)` points
(`game/party/Party.cpp:3745, 3775`; MAW relies on the engine, and its balance model uses the same closed form
`Estimates.lua:79-86`: points earned from level 1 to L = `5(L−1) + 5q(q−1) + q(r+1)` with `q = floor(L/10)`,
`r = L − 10q`). Other point sources in MAW: Transcendence black potions (`Scripts/General/zzAlchemy.lua:243, 300`) and
a quest reward of 8 (`Scripts/Maps/7out01.lua:21`).

### 4.2 Shared-cost discount (`S:238-262`, run on the "+" click, action 121)

- **Set**: Staff, Sword, Dagger, Axe, Spear, Bow, Mace, Blaster and skills 12-22 (`S:1135`), which are the nine magic
  schools **plus Dark Elf Ability (21) and Vampire Ability (22)**. Dragon Ability (23) is not in the set. For the
  Shaman, Seraphim, Death Knight and Assassin class lines only 12-22 count (`S:240-243`).
- **Cost** of raising skill X from `s` to `s+1`: `ceil((s+1) / n)`, `n = 1 + number of OTHER skills of the set
  whose base level is ≥ s+1`. Skills outside the set cost `s+1` as before.
- **Mechanics**: the engine charges `s+1`; MAW refunds `(s+1) − cost` beforehand, and only when the character has at
  least `cost` points, so the click succeeds with just the discounted amount. Raises costing over 1000 are never
  discounted.
- **Order does not matter.** For each level v, the k-th skill of the set to reach v pays `ceil(v/k)`, whatever the
  order. Total for a set: `Σ_v Σ_{k=1..c(v)} ceil(v/k)`, `c(v)` = number of set skills at level ≥ v.

Examples (checked with a Lua re-implementation, scratch only):

| Situation | Vanilla | MAW |
|---|---|---|
| Fire 9 → 10, Air 10, Water 12 | 10 | `ceil(10/3)` = 4 |
| Earth 1 → 2 with Fire 10, Air 10, Water 12 | 2 | `ceil(2/4)` = 1 |
| Build Fire 12, Air 12, Water 8, Dagger 6 from 1 (any order) | 209 | 139 |
| Second school alone to 10 next to a first one at 10 | 54 | 29 |

OpenYAMM: `Party::canIncreaseActiveMemberSkillLevel` / `increaseActiveMemberSkillLevel`
(`game/party/Party.cpp:3830-3876`) charge `level + 1`; the MAW ruleset needs a cost function there and in any UI that
shows the price of the "+" button.

### 4.3 Other rules on the "+" click (`S:348-364`, in this order)

1. `refundSharedCost` (above).
2. `restoreMasteries` (§4.5): remembered masteries come back one rank per click.
3. `applyCap`: Alchemy 60, Cover 30, Mana Shield 50, Retaliation 50; at the cap the click is swallowed and any excess
   refunded (`S:300-320`). Reaching Cover 30 also learns Retaliation at 1 (`S:185-196`).
4. `autoLearnMastery`: extended-skill ladders (§5, `S:322-335`), bounded by the class/race limit.
5. `armsmasterSupreme`: a status message when Armsmaster reaches 30/50/70 for classes 16-19 (`S:337-346`).

### 4.4 One-time migrations (old saves and new games)

| Flag | Effect | Source |
|---|---|---|
| `vars.UncappedSkills` | re-encodes mastery bits for the 0x3FF skill limit | `S:1-22` |
| `vars.weaponSkillRefunded` | refunds old magic-only discount minus new shared-set cost (greedy, §4.5) | `S:1136-1218` |
| `vars.learningFix[id]` | refunds Learning `s + … + 2`, sets it to 0 (unlearned), new games too (1) | `S:1543-1560` |
| `vars.dragonMeditationRemoved` | refunds Dragon Meditation the same way and removes it | `zzClasses.lua:346-361` |
| `vars.BBFIX` | clamps Bodybuilding mastery to the class limit | `S:2629-2640` |
| `vars.hirelingFix` | repairs corrupted skill words above 4864 | `S:1511-1535` |
| `vars.needToFixCover` | new games set Cover, Mana Shield, Enlightenment to 0 | `S:2402-2419` |

(1) The loop covers `Party.PlayersArray`, which holds the recruitable roster from the start of a game, so on a new
game the first map load already strips Learning from every roster hero (the stop at the first fixed character only
matters on later loads). OpenYAMM applies it when a roster hero is built (`ExperienceRules::prepareRosterCharacter`,
audit FSPS-2-11 and CHM-1).

None of these is needed by a native MAW ruleset that starts from new games, except the rule they encode: under MAW
nobody starts with Learning/Ascension, even classes whose starting table offers it.

### 4.5 Respec (`R`)

- **NPCs**: 314 Oracle (house 757, out02 Ravenshore), 413 Judge Grey (house 1165 Arbiter, 7out02 Harmondale),
  794 The Seer (house 450, outd3). Ids, names and houses match OpenYAMM's tables. Topic slot 3: "Skill reset info"
  (explanation) switches to "I want to reset" (action) (`R:3-39`). Judge Grey can die or leave in the MM7 story, which
  removes Antagarich's respec NPC.
- **Cost**: 1000 gold × the active character's base level (`R:45-50`). Not enough gold: "Not enough gold."
- **Refund** for the active character (`R:58-123`):
  - Shared set (§4.2, class-dependent): all masteries in the set reset to Novice, then the greedy loop repeats "take
    the highest skill (first one on ties), refund `ceil(level / number of set skills at that level)`, lower it by
    one" until every set skill is at 1. This equals the cost paid under §4.2 in any order.
  - Other skills above 1 except Alchemy: refund `s(s+1)/2 − 1`, set to 1 with Novice mastery.
  - **Alchemy is not reset**: it keeps level and mastery; its triangular cost is only subtracted from the floor.
  - Cover, Mana Shield, Enlightenment, Retaliation: refund `s(s+1)/2 − 1` each, set to 1 (mastery lost, ladders
    re-grant it).
  - **Floor**: unspent points become at least `Σ_{i=2..L} (4 + floor(i/10 + 1)) − alchemyCost`, the points earned
    from level-ups (a fix for mercenaries created with too few points).
- **Mastery memory** (`R:127-137`): before the reset, `vars.oldPlayerMasteries[index][skill]` keeps the highest
  mastery ever held (all 39 base skills). On later "+" clicks (`S:292-297`) the next rank returns as soon as the new
  level reaches the current mode's requirement, one rank per click, without a teacher or gold. Remembered masteries
  also raise future teacher prices (§2.3).
- **Austerity**: paying sets Identify Monster to level 0 GM for every party member (`R:51-55`).
- **Bug**: `R:63` tests the global `pl`, not the respecced character, for the Assassin class.

Worked example. Sorcerer, level 30, 3 unspent points, Fire 12 M, Air 12 M, Water 8 E, Dagger 6 E, Meditation 10 M,
Alchemy 5 E. Free progression, Normal mode.

| Step | Value |
|---|---|
| Gold | 30 × 1000 = 30,000 |
| Shared set (Fire, Air, Water, Dagger) back to 1 | 139 (vanilla triangular would be 209) |
| Meditation back to 1 | 10·11/2 − 1 = 54 |
| Alchemy | unchanged (level 5, Expert); cost 14 |
| Points after reset | 3 + 139 + 54 = 196 |
| Floor | Σ_{i=2..30}(5 + floor(i/10)) = 178, minus 14 = 164, so 196 stands |
| Remembered | Fire 3, Air 3, Water 2, Dagger 2, Meditation 3 (1 = Novice) |
| Re-raising Fire | Expert returns on the click from 3 to 4, Master on the click from 6 to 7 |

OpenYAMM has a triangular refund helper already (`refundAndClearSkill`, `game/party/Party.cpp:1018-1036`, used by
the Lich transformation). The respec needs the shared-set refund, the floor, the memory table in the save and two
NPC topics.

### 4.6 Solo utility masteries (`S:2126-2168`)

While the party has one member (checked every second): Identify Item, Merchant, Repair, Perception, Disarm Traps,
Identify Monster and Alchemy get mastery = number of thresholds 1/4/7/10 reached by the base level. The mastery is
**set**, so it can also fall; class caps are not consulted. The previous masteries are remembered and restored when the
party grows.

### 4.7 Other automatic masteries

- Extended-skill ladders (`S:176-181`): Cover 6/12/20 (Insanity and Madness 8/20/30), Mana Shield 6/12/20 (8/20/32),
  Enlightenment 6/12/20, Retaliation 10/24/40.
- Free → horizontal switch (`S:1976-2011`): for skills 0-23 masteries above the new requirement are stripped and
  stored; switching back restores them at once; "+" clicks also restore them rank by rank (`S:284-291`).
- Armsmaster Supreme: automatic at base 30 (Insanity 50, Madness 70) with GM, classes 16-19 (§5).

---------------------------------------------------------------------------------------------------------------------

## 5. Per-skill numbers

The complete rules with sources are in [data/skill_rules.yml](data/skill_rules.yml) (per mastery: attack, recovery,
damage %, AC and resistance %, armour penalties, specials, caps, ladders, regeneration formulas, Ascension constants,
party utility formulas, the four new skills) and [data/mastery_requirements.yml](data/mastery_requirements.yml)
(requirements, prices, escalation, dialogue rules, automatic masteries, limit tables). Summary:

| Skill | Per point N / E / M / G | Specials |
|---|---|---|
| Staff | atk 1-4; AC, res 0/2/3/4 % of weapon atk × (s+10), res party-wide; dmg +2 % | M stun 2 s, G 4 s; G + Unarmed |
| Sword | atk 1-4; speed 0/1/1/2 %; AC 0/0/1/2 %; dmg +2 % | M dual wield (not Seraphim) |
| Dagger | atk 1-4; speed 0/0/0/1 %; dmg +2 % | E dual wield; M crit +5 % + 1 %/pt ÷ min(1+lvl/200, 4) |
| Axe | atk 1-4; speed 0/1/1/1 %; dmg +2 % | G +1 % crit damage per point |
| Spear | atk 2/4/6/8; AC 0/4/6/8 %; dmg +2 % | M one-handed; G stacking +(2+0.02s) % damage taken |
| Bow | atk 1-4; speed 0/1/1/2 %; dmg +4 % and +1 flat | M two arrows; G fire arrows |
| Mace | atk 1-4; dmg +2 % | M stun 2 s, G 4 s (both paralyse) |
| Blaster | atk 1-4; dmg +4 % | recovery fixed 40, melee ×0.4 |
| Unarmed | atk 2/2/3/3; speed 0/1/1/2 %; +2 flat damage | |
| Leather / Chain / Plate | AC 3/4/5/6 % of worn armour AC; res 2-5, 1-4, 0-3 % | penalty % (none/N/E/M/G) (2) |
| Shield | AC and res 4/6/8/10 % of shield AC | penalty 10/10/0/0/0 %; G ×0.85 damage (twice for magic) |
| Dodging | flat AC 4/5/6/6 | M with Leather; G dodge `1 − 1/(1 + (s+10)/200)` |
| Armsmaster | dmg 0/1/1/1.5 (S 2), speed 0/0/1/1 (S 1) %, atk 1 | not with staff; Supreme for classes 16-19 |
| Bodybuilding | +0.5/1/1.5/2 % HP, plus HPFactor × s × m (GM as 5) | |
| Meditation | SP regen rate 2/2.5/3/4 %, plus SPFactor × s × m (GM as 5) | ×2 after 20 s without loss, ×4 out of combat |
| Regeneration | HP regen rate 5/7.5/10/10 % | G ×(1 + (1 − hp%)²); Dragon melee leech |
| Perception | trap/lava damage ×0.9/0.7/0.5/0.3 | own skill, not party best |
| Learning → Ascension | mana ×0.875/0.75/0.625/0.5 | power dial, see the YAML |
| Alchemy | training cap 60 | M 1.5, G 2 power per point |
| Cover (50) | chance 10 % + 1 %/pt, max 40 % | N physical, E elemental, M spells, G +15 % after own hit |
| Mana Shield (51) | absorbs 25/50/75/100 % of each hit | 1 + min(s,50)^1.4/60 damage per SP; cap 50 |
| Enlightenment (52) | +0.5/1/1.5/2 % mana | aura reservation ÷ (classSPFactor + m/2) |
| Retaliation (53) | 1 %/pt chance per cover to store a stack | damage, stun, recovery at every mastery; G 3 stacks (3) |

(2) Recovery penalties: Leather 10/10/0/0/0, Chain 20/20/10/0/0, Plate 20/20/10/10/0 (unskilled, N, E, M, G).
(3) Per stack: power × vitality coefficient × s damage, 25 % stun for 2 s, −30 % next recovery; cap 50.

---------------------------------------------------------------------------------------------------------------------

## 6. Table diffs, mapped onto OpenYAMM's tables

### 6.1 Which MAW table is authoritative

- **Class caps come from `Class Skillz.txt`, not `Class Skills.txt`.** MAW ships no `Skillz.dll`, so its Lua port is
  active (`SK:1-14`). It parses `Class Skillz.txt` (`SK:264-286`) and at `GameInitialized2` overwrites the engine's
  class table for the 39 base skills (`SK:350-361, 874-876`). Where the two MAW files disagree, `Class Skillz.txt`
  wins. MAW's `Class Skills.txt` differs from base in 432 cells; the effective change (base `Class Skills.txt` versus
  MAW `Class Skillz.txt`) is 503 cells, 134 of which exist only in `Class Skillz.txt` (marked `*` below) and 4 MAW
  `Class Skills.txt` edits that `Class Skillz.txt` undoes (Bodybuilding Minotaur Lord, Armsmaster Minotaur Lord,
  Bounty Hunter, Ranger Lord).
- **Race limits come from `Race Skillz.txt` only.** MAW's `Scripts/Structs/RacialSkills.lua` is an empty file
  (0 bytes; base MMMerge's 386-line reader of `Race Skills.txt` is gone), so `Race Skills.txt` is dead data in MAW. The
  port reads `Race Skillz.txt` for the 39 base skills (`SK:288-303`) and combines it with the class letter
  (`SK:217-247, 336-347`).
- `Extra Skillz.txt` (race × class overrides) has only its header.
- `Class Starting Skillz.txt` has no reader in MAW's Lua (presumably only `Skillz.dll` read it); it is stale
  (26 cells differ from `Class Starting Skills.txt`, e.g. Knight still starts with Leather). `Class Starting
  Skills.txt` is the live one (MMMerge `DataTables`, indexed by `floor(class / 2)`:
  `Scripts/General/MenuChooseCharacter.lua:215`).

Letters: `N` (Skillz) = `B` (ours) = Novice; `=` (Skillz) = `-` (ours) = cannot learn; `S` = Supreme, which our
`parseSkillMasteryToken` and `SkillMastery` cannot express yet (Grandmaster is the maximum).

### 6.2 `class_skills.txt`: changed cells for the existing 53 classes

Format: `Class old→new`, old = base MMMerge = ours (our file equals base apart from the extra Throwing row, which MAW
does not have and the patch leaves alone). Rows use our skill row names, columns our class header names
(`DarkArchMage` = our "Dark Archmage"; `n/u(52)` is the last column). `*` marks cells where MAW's
`Class Skills.txt` says something else and only `Class Skillz.txt` has the effective value.

- Staff: Archer B→E, WarriorMage B→M, MasterArcher B→M, Sniper B→M, Druid B→E, GreatDruid B→M, Warlock B→M, ArchDruid
  B→M, Knight E→M, Cavalier E→M, BlackKnight E→G, Champion E→G, Paladin B→E, Crusader B→M, Hero B→M, Villain B→M,
  Ranger B→E, Hunter B→E, BountyHunter B→E, RangerLord B→E, Vampire -→E, Nosferatu -→M
- Sword: WarriorMage E→M, MasterArcher E→M, Sniper E→M, MinotaurLord E→M, Hunter E→M, BountyHunter E→M, RangerLord
  E→M, WarTroll M→G*
- Dagger: Archer E→M*, WarriorMage E→M, MasterArcher E→G*, Sniper E→G*, Wizard E→M, Lich E→M, ArchMage E→M,
  DarkArchMage E→M, Master Wizard E→M
- Axe: WarriorMage E→M, MasterArcher E→M, Sniper E→M, Knight E→M, Cavalier E→M, BlackKnight M→G, Champion M→G,
  Minotaur E→M, MinotaurLord M→G, Crusader E→M, Hero E→M, Villain E→M, Ranger M→E
- Spear: Archer M→E, DarkElf -→E*, Patriarch -→M*, Crusader E→M, Hero E→M, Villain E→M, Hunter E→M, BountyHunter E→G,
  RangerLord E→G*, WarTroll E→M
- Bow: Cleric B→E, Priest B→M, PriestLight B→M, PriestDark B→M, Druid B→E, GreatDruid B→E, Warlock B→E, ArchDruid B→E,
  BlackKnight E→M, Champion E→M, BountyHunter M→G, RangerLord M→G, Rogue E→M, Assassin E→M, Spy E→M, Troll B→E,
  WarTroll B→M, High Priest B→M
- Mace: Cleric M→E, BlackKnight M→G*, Champion M→G*, Assassin E→M*, Spy E→M*, Nosferatu E→M
- Shield: Cleric M→E, Thief B→-*, Rogue B→-*, Assassin B→-*, Spy B→-*, Troll -→E, WarTroll -→M*
- Leather: Knight M→E, Cavalier M→E, BlackKnight M→E, Champion M→E, Wizard E→M, Lich E→M, ArchMage E→M, DarkArchMage
  E→M, Master Wizard E→M
- Chain: PriestLight E→M, PriestDark E→M, MinotaurLord M→G, Paladin E→M, Crusader E→M, Hero E→M, Villain E→M, Assassin
  E→M*, Spy E→M*, High Priest E→M
- Plate: Minotaur M→E, MinotaurLord M→E, Hero M→G, Villain M→G
- Fire: Archer B→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Ranger -→E, Hunter B→E, BountyHunter E→M,
  RangerLord E→M, Thief -→E*, Rogue B→M*, Assassin B→G*, Spy B→G*
- Air: Archer B→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Ranger -→E, Hunter B→E, BountyHunter E→M, RangerLord
  E→M, Thief -→E*, Rogue B→M*, Assassin B→G*, Spy B→G*
- Water: Archer B→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Patriarch M→G*, Ranger -→E, Hunter B→E,
  BountyHunter E→G*, RangerLord E→G*, Thief -→E*, Rogue B→M*, Assassin B→G*, Spy B→G*
- Earth: Archer B→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Ranger -→E, Hunter B→E, BountyHunter E→M,
  RangerLord E→M, Thief -→E*, Rogue B→M*, Assassin B→G*, Spy B→G*
- Spirit: Minotaur B→E, MinotaurLord E→M, Paladin B→E, Crusader E→M, Hero M→G, Villain M→G, Ranger -→E, Hunter B→E,
  BountyHunter E→M, RangerLord E→M
- Mind: Minotaur B→E, MinotaurLord E→M, Paladin B→E, Crusader E→M, Hero M→G, Villain M→G, Ranger -→E, Hunter B→E,
  BountyHunter E→M, RangerLord E→M, Vampire E→M*, Nosferatu M→G*
- Body: Minotaur B→E, MinotaurLord E→M, Paladin B→E, Crusader E→M, Ranger -→E, Hunter B→E, BountyHunter E→M,
  RangerLord E→M
- Light: MasterArcher B→G*, Hero B→G*, RangerLord -→E*, High Priest M→G*, Master Wizard M→G*, n/u(52) M→G*
- Dark: Sniper B→G*, Villain B→G*, BountyHunter -→E*, High Priest M→G*, Master Wizard M→G*, n/u(52) M→G*
- IdentifyItem: Archer -→M, WarriorMage -→M, MasterArcher -→G, Sniper -→G, Cleric -→B, Priest -→B, PriestLight -→B,
  PriestDark -→B, Knight -→B, Cavalier -→E, BlackKnight -→E, Champion -→E, Minotaur -→B, MinotaurLord -→B, Monk -→E,
  Initiate -→M, Master -→M, Ninja -→M, Paladin -→E, Crusader -→M, Hero -→M, Villain -→M, Troll -→B, WarTroll -→B,
  DarkArchMage M→G*, Peasant -→B, n/u(49) -→B, High Priest -→B, Master Wizard M→G*
- Merchant: PriestLight M→G, PriestDark M→G, Monk -→B, Initiate -→B, Master -→B, Ninja -→B, Hero E→M*, Villain E→M*,
  Ranger B→M, Hunter B→M, BountyHunter B→M, RangerLord B→M, Peasant -→B, n/u(49) -→B, High Priest M→G
- Repair: MasterArcher E→M, Sniper E→M, Dragon -→B, GreatWyrm -→B, Druid -→B, GreatDruid -→B, Warlock -→B, ArchDruid
  -→B, Minotaur -→B, MinotaurLord -→B, Monk -→B, Initiate -→B, Master -→B, Ninja -→B, Vampire -→B, Nosferatu -→B,
  Sorcerer -→E, Necromancer -→E, Lich -→M, ArchMage E→M, DarkArchMage E→M, Peasant -→B, n/u(49) -→B, Master Wizard E→M
- Bodybuilding: WarriorMage E→M, MasterArcher E→M, Sniper E→M, Cleric B→M*, Priest B→M*, PriestLight B→M*, PriestDark
  B→M*, DarkElf -→E, Patriarch -→M*, GreatWyrm M→G*, Druid -→E*, GreatDruid -→E*, Warlock -→E*, ArchDruid -→E*,
  BlackKnight M→G*, Champion M→G*, Hunter E→M, BountyHunter E→M, RangerLord E→M, Vampire -→E, Nosferatu -→M, Sorcerer
  -→E*, Wizard -→E*, Necromancer -→E*, Lich -→E*, ArchMage -→E*, DarkArchMage -→E*, Peasant -→B, High Priest B→M*,
  Master Wizard -→E*
- Meditation: WarriorMage E→M, MasterArcher E→M, Sniper E→M, PriestLight M→G*, PriestDark M→G*, Patriarch E→G*, Dragon
  M→-, GreatWyrm M→-, Minotaur -→E, MinotaurLord -→M, Monk -→E*, Initiate -→M*, Master -→G*, Ninja -→G*, Hero E→M,
  Villain E→M, Ranger B→E, Hunter B→M, BountyHunter B→M, RangerLord B→M, Rogue -→E, Assassin -→M, Spy -→M, Vampire
  -→E*, Nosferatu -→G*, Lich M→G*, ArchMage M→G*, High Priest M→G*, Master Wizard M→G*
- Perception: Cavalier E→M, BlackKnight E→M, Champion E→M, Paladin B→E, Crusader B→M, Hero B→M, Villain B→M, WarTroll
  B→E
- Regeneration: Dragon E→M*, GreatWyrm E→G*, Minotaur -→B, MinotaurLord -→E, Monk -→B, Initiate -→E, Master -→E, Ninja
  -→E, Vampire E→M*, Nosferatu M→G*
- DisarmTraps: Cleric -→B, Priest -→B, PriestLight -→B, PriestDark -→B, Dragon -→B, GreatWyrm -→B, Druid -→B,
  GreatDruid -→B, Warlock -→B, ArchDruid -→B, Knight B→E*, Cavalier B→M*, BlackKnight B→M*, Champion B→M*, Paladin
  -→B, Crusader -→B, Hero -→B, Villain -→B, Sorcerer -→B, Wizard -→B, Peasant -→B, n/u(49) -→B, High Priest -→B
- Dodging: Dragon -→M*, GreatWyrm -→G*, Thief M→E*, Assassin M→G, Spy M→G
- Unarmed: Dragon -→M*, GreatWyrm -→G*, WarTroll E→M*
- IdentifyMonster: Archer -→B, WarriorMage -→B, MasterArcher -→B, Sniper -→B, Cleric E→M, Priest E→G, PriestLight E→G,
  PriestDark E→G, DarkElf -→B, Patriarch -→B, Knight B→E, Cavalier B→E, BlackKnight B→E, Champion B→E, Minotaur -→B,
  MinotaurLord -→B, Paladin -→M*, Crusader -→M*, Hero -→G*, Villain -→G*, Thief -→B, Rogue -→B, Assassin -→E*, Spy
  -→E*, Peasant -→B, n/u(49) -→B, High Priest E→G*
- Armsmaster: MasterArcher E→M, Sniper E→M, Cleric -→E, Priest -→E, PriestLight B→E, PriestDark B→E, Patriarch E→M*,
  Cavalier M→G*, BlackKnight G→S*, Champion G→S*, Minotaur M→E*, Monk M→-*, Initiate M→-*, Master M→-*, Ninja M→-*,
  Crusader E→M, Hero E→M, Villain E→M, Thief M→-*, Rogue M→-*, Assassin M→-*, Spy M→-*, Vampire B→M, Nosferatu B→G,
  High Priest B→E*
- Alchemy: DarkElf E→M, Patriarch E→G, GreatDruid M→G*, Knight -→B, Cavalier -→B, BlackKnight -→B, Champion -→B, Monk
  -→M, Initiate -→G*, Master -→G, Ninja -→G, Paladin -→B, Crusader -→E, Hero -→E, Villain -→E, Ranger B→M, Hunter B→G,
  BountyHunter B→G, RangerLord B→G, Thief E→M, Rogue E→G*, Assassin M→G, Spy M→G, Troll -→E*, WarTroll -→E*, Nosferatu
  M→G, Wizard M→G*, ArchMage M→G, DarkArchMage M→G, Peasant -→B, n/u(49) -→B, Master Wizard M→G
- Learning: MasterArcher M→G, PriestLight M→G, PriestDark M→G, DarkElf E→M, Patriarch E→G, Dragon M→-*, GreatWyrm
  G→-*, Warlock M→G, ArchDruid M→G, Knight B→-, Cavalier B→-, BlackKnight B→-, Champion B→-, Minotaur B→M,
  MinotaurLord B→G, Paladin B→M, Crusader B→M, Hero B→G, Villain B→G, Ranger E→M, Hunter E→M, BountyHunter E→G,
  RangerLord E→G, Thief E→-, Rogue E→-*, Assassin E→-*, Spy E→-*, Troll B→-, WarTroll B→-, Vampire B→M, Nosferatu B→G,
  Lich M→G, ArchMage M→G, DarkArchMage M→G, High Priest M→G, Master Wizard M→G

Notable effects: the Thief line loses Shield and Armsmaster, Monks lose Armsmaster, Dragons, Knights, Thieves, Rogues,
Assassins, Spies and Trolls lose Learning/Ascension; Black Knight and Champion reach Armsmaster Supreme; Archers and
hybrids gain Expert/Master/GM in weapons and all four elements; misc skills open at Novice almost everywhere.

### 6.3 `class_skills.txt`: twelve new class columns and four new skill rows

New columns (MAW class ids 53-64): Ser Seraphim, Ang Angel, Arch Archangel, DK Death Knight, DL Death Lord, LK Lich
King, Sha Shaman, Sek Sekhem, Mar Marabou, Ele Elementalist, EA Elemental Adept, MoE Master of Elements. Values from
`Class Skillz.txt`; they differ from MAW's `Class Skills.txt` in Bodybuilding, Meditation, Disarm Traps and Alchemy.

| Skill | Ser | Ang | Arch | DK | DL | LK | Sha | Sek | Mar | Ele | EA | MoE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Staff | E | E | E | - | - | - | E | M | M | E | E | M |
| Sword | M | M | G | M | M | G | - | - | - | - | - | - |
| Dagger | - | - | - | - | - | - | E | M | M | E | E | E |
| Axe | E | E | E | M | M | G | E | M | M | - | - | - |
| Spear | M | M | G | - | - | - | E | M | M | - | - | - |
| Bow | E | E | E | E | E | E | E | E | E | B | B | B |
| Mace | E | M | M | M | M | M | E | M | M | E | E | E |
| Blaster | G | G | G | G | G | G | G | G | G | - | - | - |
| Shield | M | M | M | - | - | - | E | E | E | - | - | - |
| Leather | E | E | E | E | E | E | E | M | M | E | E | M |
| Chain | M | M | M | M | M | M | E | E | E | - | - | - |
| Plate | M | M | M | M | M | G | - | - | - | - | - | - |
| Fire | - | - | - | - | - | - | E | M | G | M | M | G |
| Air | - | - | - | - | - | - | E | M | G | M | M | G |
| Water | - | - | - | E | M | G | E | M | G | M | M | G |
| Earth | - | - | - | - | - | - | E | M | G | M | M | G |
| Spirit | E | M | M | - | - | - | E | M | G | - | - | - |
| Mind | E | M | M | - | - | - | E | M | G | - | - | - |
| Body | E | M | M | E | M | G | E | M | G | - | - | - |
| Light | M | M | G | - | - | - | - | - | - | - | - | - |
| Dark | - | - | - | E | M | G | - | - | - | - | - | - |
| DarkElfAbility | - | - | - | - | - | - | - | - | - | - | - | - |
| VampireAbility | - | - | - | - | - | - | - | - | - | - | - | - |
| DragonAbility | - | - | - | - | - | - | - | - | - | - | - | - |
| IdentifyItem | E | E | E | E | M | M | M | M | G | M | M | G |
| Merchant | M | M | G | E | E | M | E | E | E | E | E | E |
| Repair | E | E | E | M | M | G | E | M | M | B | B | B |
| Bodybuilding | E | E | E | E | E | E | B | B | B | B | B | B |
| Meditation | E | M | M | - | - | - | B | B | B | M | M | G |
| Perception | M | M | G | E | M | M | E | E | E | B | B | B |
| Regeneration | - | - | - | B | E | E | - | - | - | - | - | - |
| DisarmTraps | M | M | G | B | B | E | E | E | E | E | E | M |
| Dodging | - | - | - | - | - | - | - | - | - | - | - | - |
| Unarmed | - | - | - | - | - | - | E | M | M | - | - | - |
| IdentifyMonster | B | B | B | E | E | E | M | M | G | M | M | G |
| Armsmaster | - | - | - | - | - | - | E | E | E | - | - | - |
| Stealing | - | - | - | - | - | - | - | - | - | - | - | - |
| Alchemy | B | B | B | M | G | G | M | G | G | M | G | G |
| Learning | M | M | G | - | - | - | - | - | - | - | - | - |
| Cover (new) | M | M | G | M | M | G | - | - | - | - | - | - |
| ManaShield (new) | B | E | M | - | - | - | B | B | E | M | M | G |
| Enlightenment (new) | E | M | G | - | - | - | E | M | G | M | M | G |
| Retaliation (new) | M | M | G | M | M | G | - | - | - | - | - | - |

New skill rows for the existing classes (`Class Skillz.txt` rows 50-53; classes not listed get `-`). Peasant and both
`n/u` columns get `-`. These rows also need canonical skill names (`game/party/SkillData.cpp` keeps a fixed list of
40 names).

- Cover: Dragon M, GreatWyrm G, Knight M, Cavalier M, BlackKnight G, Champion G, Minotaur M, MinotaurLord G, Monk E,
  Initiate M, Master M, Ninja M, Paladin M, Crusader M, Hero G, Villain G, Troll M, WarTroll G
- ManaShield: Archer B, WarriorMage E, MasterArcher M, Sniper M, Cleric E, Priest E, PriestLight M, PriestDark M,
  DarkElf B, Patriarch M, Druid E, GreatDruid M, Warlock G, ArchDruid G, Minotaur E, MinotaurLord M, Initiate E,
  Master M, Ninja M, Paladin E, Crusader E, Hero E, Villain E, Ranger E, Hunter E, BountyHunter E, RangerLord E,
  Vampire E, Nosferatu M, Sorcerer E, Wizard M, Necromancer M, Lich G, ArchMage G, DarkArchMage G, High Priest M,
  Master Wizard G
- Enlightenment: Archer E, WarriorMage M, MasterArcher G, Sniper G, Cleric M, Priest M, PriestLight G, PriestDark G,
  DarkElf M, Patriarch G, Druid M, GreatDruid M, Warlock G, ArchDruid G, Minotaur M, MinotaurLord G, Initiate E,
  Master G, Ninja G, Paladin E, Crusader M, Hero G, Villain G, Ranger E, Hunter M, BountyHunter G, RangerLord G,
  Vampire M, Nosferatu G, Sorcerer M, Wizard M, Necromancer M, Lich G, ArchMage G, DarkArchMage G, High Priest G,
  Master Wizard G
- Retaliation: Dragon M, GreatWyrm G, Knight M, Cavalier M, BlackKnight G, Champion G, Minotaur M, MinotaurLord G,
  Monk E, Initiate M, Master M, Ninja M, Paladin M, Crusader M, Hero G, Villain G, Troll M, WarTroll G

### 6.4 Race tables → `race_skills.yml`

**MAW `Race Skills.txt` versus base** (dead in MAW, listed for completeness): 33 padding columns for class kinds
17-19 (all `-`; kind 20, Elementalist, has none); Sword Human `-`→`0/0/0` (no-op); Plate Minotaur `E/1/0`→`-`;
Bodybuilding Minotaur `0/1/0`→`-`; Dark Elf, Vampire and Dragon Ability `E/0/0`→`M/0/0`; Meditation Vampire, Dark Elf,
Dragon `E/0/W`→`-` and Elf `0/1/0`→`-`; Regeneration Troll `0/1/0`→`M/0/0`; Dodging and Unarmed Dragon `-`→`M/0/0`.

**`Race Skillz.txt`** (live), non-default cells. Token grammar (`SK:217-247`): upper-case letter = minimum, lower-case
letter or `0` = maximum, `+`/`-` = shift; applied as `limit = max(min(class + shift, max), min)`.

| Race | Skill | Token | Meaning |
|---|---|---|---|
| Human | IdentifyItem, Merchant, RepairItem, Perception, DisarmTraps, IdentifyMonster, Alchemy | `+` | one rank up |
| Vampire | VampireAbility | `M` | at least Master |
| DarkElf | DarkElfAbility | `M` | at least Master |
| Minotaur | Axe | `E` | at least Expert |
| Minotaur | Dagger | `0` | never (axes take the off hand) |
| Troll | Regeneration | `+` | one rank above the class |
| Dragon | Staff, Sword, Dagger, Axe, Spear, Bow, Mace, Blaster, Shield, Leather, Chain, Plate | `0` | never |
| Dragon | DragonAbility, Dodging, Unarmed | `M` | at least Master |
| Dwarf | Axe | `E` | at least Expert |

**Patch for our `race_skills.yml`** (whole-list replacement under MAW, because the base rules are dead there and the
semantics differ):

- Remove all 19 current rules. Lost under MAW: Human Learning +1, Vampire Perception +1 and Meditation min E,
  Dark Elf Merchant +1 and Meditation min E, Minotaur Axe `E/1/2`, Plate `E/1/0`, Bodybuilding +1 and our own Throwing
  min E, Troll Regeneration +1 (replaced by the shift below), Dragon Ability min E, Dragon Meditation min E and
  Identify Monster +1, Elf Meditation +1, Goblin Disarm +1, Dwarf Axe `E/1/2` and Repair +1.
- Add the 28 rules of the table above.
- Extend the schema: a `max_mastery` field (for `0`), and a `shift` that, unlike our `add`
  (`ClassSkillTable::getEffectiveCap`, `game/tables/ClassSkillTable.cpp:365-410`, applied only when the class cap is
  not None, after the minimum), is applied before the clamps and also to a class value of None. Example: a Troll
  Sorcerer (free class selection) can learn Novice Regeneration in MAW; with our `add` it could not.
- Caps above Grandmaster (`S`) need the enum extension of §6.1.

```yaml
# assets_dev/engine/rulesets/maw/race_skills.yml (proposal, replaces the engine list)
version: 2
semantics: skillz            # limit = max(min(class + shift, max_mastery), min_mastery)
rules:
  - {race: Human, skill: IdentifyItem, shift: 1}
  - {race: Human, skill: Merchant, shift: 1}
  - {race: Human, skill: RepairItem, shift: 1}
  - {race: Human, skill: Perception, shift: 1}
  - {race: Human, skill: DisarmTraps, shift: 1}
  - {race: Human, skill: IdentifyMonster, shift: 1}
  - {race: Human, skill: Alchemy, shift: 1}
  - {race: Vampire, skill: VampireAbility, min_mastery: master}
  - {race: DarkElf, skill: DarkElfAbility, min_mastery: master}
  - {race: Minotaur, skill: Axe, min_mastery: expert}
  - {race: Minotaur, skill: Dagger, max_mastery: none}
  - {race: Troll, skill: Regeneration, shift: 1}
  - {race: Dragon, skill: [Staff, Sword, Dagger, Axe, Spear, Bow, Mace, Blaster, Shield, LeatherArmor, ChainArmor,
                          PlateArmor], max_mastery: none}
  - {race: Dragon, skill: [DragonAbility, Dodging, Unarmed], min_mastery: master}
  - {race: Dwarf, skill: Axe, min_mastery: expert}
```

The flat racial skill bonuses (+3 and +1 per 10 base levels) are not a table in MAW (`S:2350-2400`); see
[data/race_bonuses.yml](data/race_bonuses.yml).

### 6.5 `Class Starting Skills.txt` → `class_starting_skills.txt`

Our file is the base table transposed (rows are the `floor(class/2)` slots, labelled with base names; columns are our
skill names). Our "Master Wizard" row already differs from base in four cells (LeatherArmor, LightMagic, DarkMagic,
Perception) and is left alone. Changed cells (`-` none, `C` choosable, `F` free):

| Our row (slot) | Changed cells |
|---|---|
| Dragon (5) | Learning C→- |
| Knight (8) | LeatherArmor F→-, PlateArmor -→F |
| Paladin (13) | LeatherArmor C→-, PlateArmor -→C |
| Ranger (15) | Bow C→F, Perception F→C |
| Thief (17) | Sword -→C, LeatherArmor C→F, FireMagic, AirMagic, WaterMagic, EarthMagic -→F, Dodging C→-, |
| | Stealing F→-, Learning C→- |
| Rogue (18, the Assassin/Spy slot) | Learning C→- |
| Vampire (20) | Sword F→C, Dagger C→F |

New rows (our layout looks rows up by class name, so each new class needs its own row; MAW slots in parentheses):

| New row | Free (F) | Choosable (C) |
|---|---|---|
| Seraphim (26) | Sword, LightMagic | Spear, Shield, ChainArmor, PlateArmor, SpiritMagic, Merchant, RepairItem, |
| | | Bodybuilding, Meditation |
| DeathKnight (28) | Axe, PlateArmor, DarkMagic, Perception | Sword, Bow, WaterMagic, BodyMagic, IdentifyItem, |
| | | Merchant, RepairItem, Bodybuilding, Regeneration, Armsmaster |
| Shaman (29) | Dagger, EarthMagic | Mace, LeatherArmor, WaterMagic, SpiritMagic, BodyMagic, Meditation, Perception, |
| | | Alchemy, Learning |
| Elementalist (31) | Staff, FireMagic | Dagger, LeatherArmor, AirMagic, WaterMagic, EarthMagic, IdentifyItem, |
| | | Merchant, IdentifyMonster, Alchemy |

- MAW's slot 26 is shared by class 52 (`n/u`) and Seraphim; in base it held "Master Wizard"-labelled data, which our
  name-based lookup keeps on the "Master Wizard" row. Do not patch that row.
- Slots 27 (Angel, Archangel) and 30 (Sekhem, Marabou) are only read for mercenaries
  (`Scripts/General/NPCMercenaries.lua:253` clamps the slot to 31). Slot 27 is a copy of the Death Knight slot (Axe,
  Plate, Dark, Perception free), which looks like a MAW mistake; slot 30 has Leather and Perception free, Bow and
  Learning choosable. Master of Elements (64) maps to slot 32, which does not exist.
- Shaman's Learning choice is wiped by the Learning migration (§4.4): nobody keeps Learning at the start.

### 6.6 `Class Starting Stats.txt` → `class_starting_stats.txt`

Our file equals base. Changed cells (row, column):

| Row | Column | Base | MAW |
|---|---|---|---|
| Might | Dragon (5) | 11/30 | 14/50 |
| + add (after Might) | Dragon (5) | 1 | 3 |
| Intellect | Dark elf (2) | 11/25 | 14/30 |
| + add (after Intellect) | Dark elf (2) | 1 | 2 |
| Endurance, Accuracy, Speed, Luck | Dragon (5) | 11/30 | 14/50 |
| + add (after each of those four) | Dragon (5) | 1 | 3 |

Dragon Intellect and Personality stay 11/30, +1.

### 6.7 `Class HP SP.txt` → `class_multipliers.txt`

Our columns are `BaseHP HPPerLevel BaseMana ManaPerLevel ManaStat` with `ManaStat` spelled out (I = Intellect,
P = Personality, IP = Mixed, - = None). Numbers equal base. Changed cells:

| Class | Change |
|---|---|
| PriestLight, PriestDark | HPPerLevel 3→4, ManaPerLevel 5→6 |
| Patriarch | HPPerLevel 4→5 |
| Dragon | HPPerLevel 10→5, ManaPerLevel 5→0 |
| GreatWyrm | BaseMana 50→120, ManaPerLevel 10→0 |
| Warlock, ArchDruid | ManaPerLevel 5→6 |
| Knight | HPPerLevel 5→4 |
| Cavalier | HPPerLevel 7→6 |
| Minotaur | HPPerLevel 4→6 |
| MinotaurLord | HPPerLevel 6→12 |
| Monk | HPPerLevel 5→4 |
| Master, Ninja | ManaPerLevel 1→2 |
| Ranger | BaseMana 0→5, ManaPerLevel 0→1, ManaStat None→Mixed |
| Hunter, BountyHunter, RangerLord | BaseMana 0→5 |
| Thief | BaseHP 35→25, HPPerLevel 4→3, BaseMana 0→60, ManaStat None→Intellect |
| Rogue | BaseHP 35→25, HPPerLevel 6→4, BaseMana 0→70, ManaPerLevel 1→0 |
| Assassin, Spy | BaseHP 35→25, HPPerLevel 8→5, BaseMana 0→80, ManaPerLevel 1→0 |
| Troll | HPPerLevel 5→6 |
| WarTroll | HPPerLevel 8→12 |
| Nosferatu | HPPerLevel 4→5 |
| Lich, ArchMage, Dark ArchMage, Master Wizard | HPPerLevel 3→4 |
| High Priest | HPPerLevel 3→4, ManaPerLevel 5→6 |

New rows:

| Class | BaseHP | HPPerLevel | BaseMana | ManaPerLevel | ManaStat |
|---|---|---|---|---|---|
| Seraphim | 40 | 3 | 15 | 1 | Personality |
| Angel | 40 | 4 | 15 | 2 | Personality |
| Archangel | 40 | 5 | 15 | 3 | Personality |
| DeathKnight | 35 | 4 | 60 | 0 | Intellect |
| DeathLord | 35 | 5 | 80 | 0 | Intellect |
| LichKing | 35 | 7 | 100 | 0 | Intellect |
| Shaman | 25 | 3 | 10 | 1 | Mixed |
| Sekhem | 25 | 4 | 10 | 1 | Mixed |
| Marabou | 25 | 5 | 10 | 1 | Mixed |
| Elementalist | 15 | 2 | 30 | 4 | Intellect |
| ElementalAdept | 15 | 2 | 30 | 6 | Intellect |
| MasterOfElements | 15 | 3 | 30 | 8 | Intellect |

Runtime overrides that the table does not show (belong to the class and stat documents, listed so the patch is not
mistaken for the whole story): Dragon base mana 60, Great Wyrm 120, both mana stat 3 (`zzClasses.lua:320-325`);
Elemental Adept HPPerLevel 2.5 (`zzClasses.lua:606`); Minotaur 6 and Minotaur Lord 12 again (`zzClasses.lua:669-670`);
every caster's `SPStats` forced to 2 (`IT:4427-4433`, which also overwrites the Dragon value if it runs after
`zzClasses.lua`); Elder/Ultimate promotions scale HP and SP factors by 1.25/1.5 (`zzClasses.lua:96-106`).

### 6.8 `Class Extra.txt` → `class_extra.txt`

Our file equals base (rows 0-52). Append:

| # | Kind | Step | Note |
|---|---|---|---|
| 53 | 17 | 0 | Seraphim |
| 54 | 17 | 1 | Angel |
| 55 | 17 | 2 | Archangel |
| 56 | 18 | 0 | Death Knight |
| 57 | 18 | 1 | Death Lord |
| 58 | 18 | 2 | Lich King |
| 59 | 19 | 0 | Shaman |
| 60 | 19 | 1 | Sekhem |
| 61 | 19 | 2 | Marabou |
| 62 | 20 | 0 | Elementalist |
| 63 | 20 | 1 | Elemental Adept |
| 64 | 20 | 2 | Master of Elements |

The new ids sit above our last id (52), so they can be a declared id range of the ruleset.

---------------------------------------------------------------------------------------------------------------------

## 7. Skill tooltips MAW shows

MAW composes each skill's right-click text from a static store plus per-player builders (`TT:1-95`): part 1 is the
body, parts 2-6 are the Novice, Expert, Master, Grand and Supreme rows. Every mastery row is coloured white if the
character's class and race can reach it, yellow if the class's last promotion can, red otherwise (`TT:69-85`). If
items or buffs change the skill, the text ends with `Bonus: +N` (`TT:86-93`). Everything below can be generated from
`skill_rules.yml`; MAW builds it from the same tables.

- **Weapons 0-7 and Unarmed** (`S:748-826`).
  - Body: vanilla text, then "This skill increases the damage gained from weapon[, armsmaster, and special
    abilities] by X% per skill point, never less than 1 damage per point, when equipping a <weapon>." Bow adds "+1
    per skill point"; Unarmed says "Unarmed combat deals 2 extra damage per skill point." Staff, Sword and Spear add
    the AC (Staff: and party Resistances) sentence "counting an extra +10 points of skill".
  - Then a separator and a header built from the columns that are non-zero at some mastery: Attack, Speed, AC, Res.
    Rows give the per-point numbers of those columns.
  - Specials appended to rows (`S:880-904`): Dagger E "can dual wield", M "5+1 crit%/skill"; Axe G "increases
    critical strike damage by 1% per skill point"; Bow M "2 arrows", G "shoots fire arrows, dealing highest between
    fire and physical damage"; Mace M "15% to stun for 2s", G "stun lasts 4s"; Staff M "10% to stun for 2s", G
    "usable with Unarm., stun lasts 4s"; Spear M "can hold with 1 hand"; Sword M "can dual wield".
  - Mace body also carries a stale sentence: paralysis 5 s on regular monsters, 2 s on bosses (`S:749`). The GM row
    is rebuilt per player: "Chance to Stun (M) / Paralyze (G) vs level <reference level>: X%" (`TT:285-299`).
  - Spear GM row per player: "Each spear attack makes the target take X% more physical damage, stacking until it
    dies. Increased by 50% with Halberds" (`TT:187-198`).
- **Leather, Chain, Plate, Shield** (`TT:202-229`, `S:829-911`). Body: role text plus "boosts the AC and Resistances
  gained by ALL armors when equipping a <type> by a percent amount"; when such armour is worn: "Current AC from
  items", "Bonus AC", "Bonus Resistances". Header "AC% | Res%". Rows: per-point percentages; Leather E "recovery
  penalty eliminated"; Chain E "recovery penalty halved", M "eliminated"; Plate E "rec. pen. halved", G "rec. pen.
  elim."; Shield E "recovery penalty eliminated", G "15% Damage reduction".
- **Dodging** (`S:853-856, 931-932`). Header AC / Res, rows 4/5/6/6 and 0. The Master row is built from the GM row
  text plus "usable with Leather Armor" (bug); GM adds "0.5% dodge chance" (code: `1 − 1/(1 + (s+10)/200)`).
- **Armsmaster** (`S:912-936`, `TT:304-307`). Body: "tricks of the trade ... all weapons except staves ... Damage
  added by armsmaster skill scales with your weapon skill", plus "Knights can learn up to a Supreme level, which is
  learned automatically at skill level 30" (50/70 by mode). Rows "Each skill point adds 1 dmg, 1 atk, 1% speed" style
  (Novice "1 atk"); Supreme row adds "Knights only. Each 10 points of armsmaster raise every melee weapon skill by 1,
  up to double its base value."
- **Bodybuilding** (`ST:257-261`): vanilla plus "Hit Points are also increased 0.5-1-1.5-2% per skill point,
  depending on mastery."
- **Regeneration** (`TT:140-156`, `S:2461-2477`). Body: vanilla plus "Current HP Regeneration: X" and "Next Level
  Bonus: +Y HP Regen"; Dragons also "Melee Life Leech vs equal level: X%" and its next-level gain. Rows: N "Increases
  hit points regained over time", E "+50% effect of skill", M "+100% effect of skill", GM "Increase your regeneration
  by 1% per every 1% of hp lost" (code is quadratic).
- **Meditation** (`TT:158-164`, `S:2461-2477`). Body: vanilla plus "Increases spell points based on SP per level and
  mastery", current SP regeneration and next-level bonus. Rows: N "Increases spell points regained over time",
  E +25 %, M +50 %, GM +100 % effect of skill.
- **Learning, renamed Ascension** (`S:1562-1568`, `TT:166-185`). Body: "Increases spell damage and healing at the
  expense of higher mana cost and cast time." plus "Current bonuses at skill s": damage base and scaling, healing base
  and scaling, mana cost and cast time, as percentages. Rows: "Mana cost reduced by 12.5% / 25% / 37.5% / 50%".
- **Perception** (`S:1570-1573`): rows "Reduces traps and lava damage by 10% / 30% / 50% / 70%."
- **Alchemy** (`zzAlchemy.lua:707-709`): body adds "Master will grant 1% to drop random reagents from Monsters. At GM
  this chance is doubled."; M row "Allows to make white potions. Power when mixing will be increased to 1.5 per skill
  point."; GM row "black potions ... 2 ... increases potion duration by 6 Minutes per skill point ... Endless potion".
- **Cover** (`TT:249-263`, `S:2175-2179`). Body: description, ladder "6-12-20" ("8-20-30" in Insanity), "Grants 10
  plus 1% chance per skill point to Cover, up to 40%", "Current cover chance: X%", a solo paragraph (a cover takes
  50 % off the blow), "Press P to enable/disable", "Currently enabled/disabled". Rows: "Allow use to Cover Physical
  damage", "... Projectiles damage", "... Spells damage", GM "Attacking will increase you next Cover chance by 15%".
- **Mana Shield** (`TT:265-273`, `S:2426-2430`). Body: "consume mana to reduce damage when an hit would take you below
  a certain threshold" (no threshold in code), ladder, "stops growing past skill 50", "Current Damage reduction per
  Mana: X", "Press M", state. Rows "Absorb up to 25% / 50% / 75% damage", GM "All damage is absorbed by mana".
- **Enlightenment** (`S:2439-2445`): description, ladder 6-12-20; rows "Mana is increased by 0.5/1/1.5/2% per skill
  level, cost divisor increased by 0.5/1/1.5/2".
- **Retaliation** (`TT:275-281`, `S:2455-2458`). Body: "1% per skill point chance to activate after a successful
  Cover", ladder from the table (10, 24, 40; the static text says 12, 30, 50), "Melee Power coefficient", "Vitality
  coefficient", "Total Damage". Rows: E "additional damage, multiplied by skill level", M "recovery time is reduced by
  30%", G "25% chance to stun the enemy for 2 seconds", Supreme slot "can stack up to 3 times".
- **Class schools** (`TT:317-528`): Shaman, Death Knight, Seraphim, Elementalist and Assassin replace the school texts
  with their perks and live numbers; see [data/class_perks.yml](data/class_perks.yml).
- **Dragons** (`TT:530-555`): Unarmed and Dodging read as Fangs and Scales, with damage or AC per level and
  Attack/Dmg or AC%/Res% rows.

Tooltip facts that disagree with code (fix in a port, do not copy): the Dodging Master row, the GM dodge text, the
Regeneration GM text, the Mace paralysis durations, the Ascension healing curve (tooltip `(1+0.05s)·1.02^s` and
`(1+0.03s²)·1.02^s`, code `(1+0.02s)·1.015^s` and `(1+0.01s²)·1.015^s`), the Mana Shield "below a certain threshold"
wording (no threshold in code), and the Retaliation mastery rows (all effects work at every mastery).

Improvements OpenYAMM can make cheaply: show the next point and next mastery values, the mode's requirement and
teacher price with the nearest teacher (from §1.3), the discounted "+" cost (§4.2) and the remembered mastery that
will return after a respec.

---------------------------------------------------------------------------------------------------------------------

## 8. Corrections to existing docs

Not applied; listed for whoever revises those files.

- **SKILLS_SPELLS_ALCHEMY.md:759**: says `Class Skillz.txt` rows 0-38 identical to MAW `Class Skills.txt`. Code: 157
  cells differ (12 new classes included), and `Class Skillz.txt` is the one the game uses (§6.1).
- **SKILLS_SPELLS_ALCHEMY.md:465-472**: says class cap summary from `Class Skills.txt`. Code: e.g. Thief line loses
  Shield and Armsmaster, Monks lose Armsmaster, Assassin/Spy get GM elements, Dragons/Rogues/Assassins/Spies lose
  Learning (§6.2).
- **README.md:348, SKILLS_SPELLS_ALCHEMY.md:696, 761-764**: says race limits from `Race
  Skills.txt` and `Race Skillz.txt`. Code: `Race Skills.txt` is never read in MAW (`Scripts/Structs/RacialSkills.lua`
  is empty); only `Race Skillz.txt` counts, and base racial bonuses such as Human Learning +1 or Goblin Disarm +1 are
  gone (§6.4).
- **SKILLS_SPELLS_ALCHEMY.md:25, 484**: says Troll Regeneration "min Master" from `Race Skills.txt`. Code: only the
  `+` shift applies.
- **SKILLS_SPELLS_ALCHEMY.md:150, 152**: says shared set = weapons 0-7 and "magic 12-22". Code: 21 and 22 are Dark Elf
  and Vampire Ability, also in the set; Dragon Ability (23) is not.
- **SKILLS_SPELLS_ALCHEMY.md:163**: says horizontal requirements when `vars.Mode==2` or bolster off. Code: `vars.Mode
  == 2` is Doom (also set by Insanity/Madness): Doom uses 6/12/20 even with free progression; prices never depend on
  progression.
- **SKILLS_SPELLS_ALCHEMY.md:185**: says Alchemy is reset at respec but excluded from the floor. Code: Alchemy is not
  touched (level and mastery kept); only its cost is subtracted from the floor (`R:68, 103-105`).
- **SKILLS_SPELLS_ALCHEMY.md:191, UI_CONTENT.md:292-293**: says 60+ (about 60) trainer NPCs moved, 18 maps. Code: 21
  distinct NPCs, 64 entries (43 moves, 21 restores) on 19 map keys.
- **UI_CONTENT.md:386-393**: says the whole guidebook PDF is implemented by `zzMAW_MoveTrainers.lua`. Code: only
  racial, Dodging, Unarmed, ID Monster and Regeneration lines; Alchemy, Armsmaster and Ascension lines are base
  teachers; "Alchemy Master Free Haven" matches no NPC (§1.4).
- **README.md:157**: says trainers moved so every continent teaches every skill. Code: the moves cover five skill
  groups (§1.3); the rest relies on base teachers.
- **SKILLS_SPELLS_ALCHEMY.md:194**: says training takes 0 days "in challenge mode". Code: `vars.ChallengeMode` is only
  set during an online multiplayer session.
- **SKILLS_SPELLS_ALCHEMY.md:195**: says training caps "bolstered by trainings on other continents". Code: the sum is
  computed and never used; only the current continent's halls are rescaled (§3.2).
- **SKILLS_SPELLS_ALCHEMY.md:61, 67**: says Staff/Mace stun "2 s (1 s at M)". Code: 4 s at GM, 2 s at Master
  (`const.Minute*2`, 2 s per game minute); both are the paralysis buff.
- **SKILLS_SPELLS_ALCHEMY.md:61**: says GM Staff adds Unarmed "at ½ effect". Code: half Unarmed replaces Armsmaster,
  and the full Unarmed attack and +2/pt damage are added too (`IT:3189-3199`).
- **SKILLS_SPELLS_ALCHEMY.md:63**: says dagger crit "+5 % +1 %/pt, divided by min(1+lvl/200, 4)". Code: only the
  per-point part is divided.
- **SKILLS_SPELLS_ALCHEMY.md:117**: says Cover: N physical melee, E projectiles, M spells. Code: N physical attacks, E
  other (elemental) attacks, M spells; converted monster missiles use a second, uncapped formula
  (`zzMaw-Monsters.lua:3883-3990`).
- **SKILLS_SPELLS_ALCHEMY.md:121**: says Retaliation effects by mastery E/M/G. Code: damage, 25 %/stack stun (2 s, 1 s
  on bosses) and −30 %/stack recovery apply at every mastery; mastery only raises the stack cap to 3 at GM; stacks
  expire after 10 s.
- **SKILLS_SPELLS_ALCHEMY.md:123**: says Mana Shield absorbs hits that would drop you below a threshold. Code: it
  absorbs 25-100 % of every hit while enabled (`zzMaw_Legendaries.lua:61-90`).
- **SKILLS_SPELLS_ALCHEMY.md:111-114**: says Learning: retroactive refund. Code: also sets Learning to 0 for everyone,
  new games included, so nobody starts with Ascension (§4.4).
- **SKILLS_SPELLS_ALCHEMY.md:78**: says Supreme for Black Knight/Champion. Code: the code grants Supreme effects to
  classes 16-19 (Knight and Cavalier too) at GM and the skill threshold, regardless of the `S` letter.
- **SKILLS_SPELLS_ALCHEMY.md:755**: says Dark Elf Int 11/25 → 14/30. Code: also its "+ add" 1 → 2.
- **SKILLS_SPELLS_ALCHEMY.md:765**: says +3 starting-skill columns "Seraphim, DK, Shaman/Elementalist". Code: MAW's
  slots are 26 Seraphim, 28 DK, 29 Shaman, 31 Elementalist; 27 and 30 are promotion slots (mercenaries only) (§6.5).
- **README.md:156, SKILLS_SPELLS_ALCHEMY.md:182**: says "Judge Gray". Code: NPC 413 is "Judge Grey".
- **SKILLS_SPELLS_ALCHEMY.md:167-171**: says teacher price formula. Code: escalation also counts respec-remembered
  masteries, with an off-by-one (§2.3); the engine still refuses parties that cannot pay the vanilla price (§2.4).

## 9. Not covered

- Spell-side effects of the magic schools and Ascension's spell lists, crowd control and buff auras (see
  SKILLS_SPELLS_ALCHEMY.md §2 and the spells/aura data files).
- Class perks of Seraphim, Death Knight, Shaman, Elementalist and the Assassin rework beyond their table rows
  ([data/class_perks.yml](data/class_perks.yml)); promotions ([data/promotions.yml](data/promotions.yml)).
- Stat effects and the SP formula that replaces `ManaStat` (`IT:3131-3146`), damage and mitigation pipelines
  (COMBAT.md).
- Mercenary generation (`Scripts/General/NPCMercenaries.lua`), which reads the starting-skill slots and its own skill
  price table.
- Shop "learn skill" prices for the new skills at training halls and magic shops; the engine's default learn price was
  not traced.
- NPC follower skill bonuses (`Scripts/Global/NPCFollowersSkills.lua`, max instead of sum).
- Whether Judge Grey's death in our MM7 events removes NPC 413 from house 1165 (affects Antagarich respec).
- `Class-Skills-Matrix.html` and the class PDFs of the guidebook were not compared cell by cell with
  `Class Skillz.txt`.
- The engine-side checks MAW relies on (stat requirements, Dodging/Unarmed cross requirement) were taken from
  OpenYAMM's model of them, not re-verified in the MM8 executable.
