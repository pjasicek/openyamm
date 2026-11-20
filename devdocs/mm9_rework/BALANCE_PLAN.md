# MM9 balance plan: MM7 difficulty on MM6–MM8 rules

The MM9 world runs on the shared MM6–MM8 rules: party of five, MM6–MM8 classes, skills, spells and combat formulas. Its
content (monsters, items, loot, shops, quest rewards, encounter density) was made for MM9's own rules: four characters,
weaker spells, sparse maps. This plan re-expresses that content on MM6–MM8 scales so the MM9 campaign plays like MM7 in
OpenYAMM.

Status (2026-11-06): implemented and gated, except what waits for the map rebuilds and the playtests. In the MM9 world
data: items v2, monster balance, gold and drops, shop stock, random-loot weights, bolster rows; in the engine: the
world `random_items` contribution and one random loot pool of every world's items (2026-11-08); quest XP to every member, and the quest XP caps in the
converters (the transcoder's and the rework's; in the game at the next map conversion, section 3.1). The balance report (section 4) passes its gate.
Left: density per map with the rebuilds (3.6) and playtests. It replaces the "Item balance" proposal in
[ROADMAP.md](ROADMAP.md) and refines the "Balance calibration" section of [PLAN.md](PLAN.md).

Principles:

- **MM7-in-OpenYAMM is the reference**, measured from the engine tables and the MM7 maps in `assets_dev/worlds/mm7/`
  (party of five, MMerge tables), not from memory of the original game.
- **All changes are data.** Importers and generators in `tools/mm9_import_discovery/` read versioned profiles and
  regenerate the MM9 tables and scripts. No MM9 item-id or monster-id conditionals in gameplay code. The only engine work
  is the common loot pool (section 3.5) and anything the report finds missing in shared systems.
- **Measure, change, measure.** The balance report and gate (section 4) run after every change.

## 1. Goal

The MM9 campaign, from the Isle of Ashes to the Hall of the Gods, plays like MM7's at each stage, for a party of five
that clears what it finds:

- **Fights:** a pack costs the party the same share of its hit points as an MM7 pack at that stage (±20%), measured by
  the engine balance probe. Kills may take longer than in MM7 (MM9's HP is kept), up to 1.5×.
- **Levels:** the party levels at a pace that keeps those fights at MM7's cost; it ends MM9 near level 69 (MM7: 74).
  MM9's content tops out lower than MM7's (chapter 5's ordinary monsters average level 45 against MM7's 70), so its
  late chapters get larger packs instead of more XP.
- **Rewards:** XP per pack at least MM7's; kill gold plus quest gold over the campaign at MM7's total, item drops at
  MM7's count (±15%); shop tiers and loot treasure levels follow the party's stage as in MM7.
- **Items:** an MM9 item of a tier is worth, weighs and costs what an MM6–MM8 item of that family and tier does, so
  random loot rolls from one pool of both (section 3.5).

Measured on the generated MM9 tables by the balance report (section 4; 32,000 fights per chapter, MM9 against the MM7
stage of matching monster level, bolster on in both worlds as in the default game, both worlds' kills at the clear
shares of 3.3; `BALANCE_REPORT.md`, 2026-11-07):

| Act (measured as) | Party level (MM7) | Pack size (MM7) | Damage taken per pack vs MM7 | Pack clear time vs MM7 |
| --- | --- | --- | --- | --- |
| 1, the prologue (MM7 stage 1) | 6 (6) | 3.2 (3.2) | 0.75 | 1.05 |
| 2, the clans: its early maps (MM7 stage 2) | 17 (21) | 2.6 (3.2) | 0.93 | 1.01 |
| 2, the clans: the rest (MM7 stage 3) | 33 (37) | 3.2 (3.2) | 0.97 | 1.35 |
| 3, the war, with act 2's promotion and side dungeons (MM7 stage 4) | 51 (54) | 3.7 (3.3) | 0.77 | 0.79 |
| 4, the finale (MM7 stage 5) | 64 (68) | 7.1 (2.9) | 0.85 | 0.71 |

The open clans act is measured as a party takes it: first its maps next to Sturmford (Drangheim, Guberland, Thjorad
Mine, Ta'Sar Academy; `mm9_density_targets.CLANS_EARLY_MAPS`), then the rest; its optional promotion and side dungeons
with the act's strongest monsters (Klusos's House, Verhoffin Ruins, the Lich Lab, the Training Hall, levels 33–79;
`CLANS_LATE_DUNGEONS`) at the war's party level. At the late act's level alone they read 2.3–4.2× MM7's damage, the
act's outdoor regions 0.3–0.5× and its other dungeons 1.3–1.8×. A split by map median level does not work for MM9:
Thronheim, Lindisfarne, the Mountain Pass and Yanmir's Fort have medians of 15–20 with many monsters of 30–70.

The first measurement (2026-11-06: chapter 1 at 1.10) modelled packs from MM9's original placement and counted
Anskram Keep's peaceful guards and the outdoor Jellyspores; the rebuilt maps' real packs read 0.41 for chapter 1 until
its growth was raised (3.6).

The longer kills in chapters 1–3 are MM9's kept HP. With bolster off (both worlds), chapters 1–4 stay within the band
and chapter 5 is about 0.75× MM7's. With the probe's two main assumptions at their extremes (an area spell catching
40–100% of a pack; casters starting a fight with 20–100% of their SP), chapters 1–3 stay within about ±20% and
chapters 4–5 within about ±30%. MM9's AI is not in the probe; playtests settle the remainder.

## 2. Decisions (user, 2026-11-05 and 2026-11-06)

| Topic | Decision |
| --- | --- |
| Reference difficulty | MM7, including encounter density, item power and economy. MM6–MM8 scaling is the model. |
| Ordinary weapons | Grow both dice and flat bonus with MM9 quality, landing on the MM6–MM8 tier averages (3.4). |
| Loot from other worlds | One random loot pool of every world's items, except that MM6–MM8 maps roll no MM9 equipment unless the Gameplay setting "MM9 loot in MM6-MM8" is on (off by default, user, 2026-11-13; [LOOT_POOL.md](../LOOT_POOL.md)); shops keep their own world's stock. MM9's top quality may match MM6–MM8's top pieces, slightly above their level-6 average; prices on MM6–MM8's curves for any item (user, 2026-11-08; 3.4, 3.5). It replaced a three-option setting (default "own world only", 2026-11-06). |
| Monster HP | Keep MM9's HP; a small trim at high levels: ×0.95 for levels 41–60, ×0.90 above 60. |
| Monster XP per kill | Keep MM9's. |
| Monster attack speed | Change gently, so MM9 monsters do not feel sluggish: 75 ticks at levels 1–20, MM9's 59 above, damage ×0.75 at levels 1–5 (3.2). |
| Density | Never overcrowded or out of place (+20–40% at most in chapters 1–3); larger packs late in the game where MM9's monsters are too weak for the party (user, 2026-11-06): 2.3× in chapter 4, 5× in chapter 5, chapter 2 unchanged; a bit easier than MM7 is fine (3.6). Chapter 1 grows 1.9× so its packs reach MM7's, and swimmers (Jellyspores, Sea Monsters) on outdoor maps do not count (user, 2026-11-07). Klusos's House gets no extra monsters and the Temple of Honk takes what fits (user). |
| Bolster | MM9 maps get MMerge's LowerToEqual rows, as MM7's have; the balance is measured with bolster on (3.7). |
| Gold and drops | Per kill at MM7's gold and items per XP, scaled so campaign totals match MM7's as it is played: MM7 parties skip half of an outdoor map's monsters (Fly) and a tenth of a dungeon's, MM9's 15% outdoors and none in dungeons; a little in MM9's favour is fine, out of whack is not (user, 2026-11-07; 3.3). |
| Quest XP | Every member gets it. Each award capped by its chapter's monster level (3.1). |

## 3. Specification

### 3.1 Quest XP

- **Every member gets the full award** (done). `MM9.giveExperience` in `assets_dev/worlds/mm9/events/common/
  mm9_common.lua` selects all members, awards, and returns the selection to the current member. Before, only the active
  member got it. Original MM9 gives every member the amount (OpenMM9 `Party::grantSharedExperience`), as MM7's
  `ForPlayer(All)` quests do. Unit test: "MM9 quest experience goes to every member and leaves the current-member
  selection" (`tests/Mm9RudeDialogueTests.cpp`).
- **Caps** (done in the converter): an award pays at most **1.5 levels' worth in chapters 1–2 and 0.5 from chapter 3**,
  and a promotion at most 1.5 levels' worth, at the count-weighted monster level of the chapter its work belongs to
  (chapter 1: 7, 2: 11, 3: 25, 4: 37, 5: 45). One level's worth is 1,000 × the level; no award is cut below 2,000.
  - Result: first-tier promotions 16,500 (MM9 24,000–24,500; MM7 30,000); second-tier 37,500 (MM9 63,000; MM7 80,000;
    the Lich, a chapter 4 promotion, 55,500); chapter 2 story awards at most 16,500, chapter 3–5 at most 12,500 /
    18,500 / 22,500. The original scripts pay about 4.3M per member; the caps leave about 1.3M (MM7: about 1.7M).
    Per-award detail: [QUEST_XP_AUDIT.md](QUEST_XP_AUDIT.md).
  - Profile: `tools/mm9_import_discovery/mm9_quest_xp_profile.yml`, keyed by script file (or include), routine and
    original amount. `mm9_scr_to_lua.py` emits the capped amount with the original in a comment
    (`MM9.giveExperience(37500) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml`). The profile is built by
    `balance_prototypes/quest_xp_profile.py` from the audit; edit the rule there or an entry in the file. Tests:
    `tools/mm9_import_discovery/test_mm9_scr_to_lua.py`.
  - **Applying it (done 2026-11-06; in the game at the next conversion):** the MM9 world's event scripts are written by
    the rework converters (`level_generation/projects/mm9r_<map>/convert.py`, `citylua.py`, `regionlua.py`), not by
    `mm9_scr_to_lua.py`. Each of their awards now goes through `mm9r_common/quest_xp.py` (`balanced_experience`,
    `experience_lua`): the profile entry by `(key, original)`, else by `(script, routine, original)` (the four keyless
    entries, and six awards whose rework key differs from the profile's: the Priest promotion, Kira's letter, three
    Afterworld fires, Mountain Pass), else the original amount (not in the profile: under the cap); a capped award
    keeps the original in a comment, as above. 110 sites in 31 converters, 69 capped. Audit:
    `mm9r_common/quest_xp_audit.py` (static, no conversion) writes `quest_xp_audit.json` (every site's map, key,
    original and balanced amount; each profile entry with the sites that pay it); 58 of the 59 entries are paid by a
    site. Unmatched: Forad Darre's death (194,000 → 18,500, `Forad.scr :OnDeath`, key 494), because the rework's
    Frosgard City has no handler for it. Not routed: the Isle of Ashes' authored `story.lua` (5,200 and smaller, all under
    the cap) and the 1000 Terrors genie's random 100–1,000. Tests: `mm9r_common/test_quest_xp.py`.
- **Dungeon awards** (Verhoffin Ruins, Yanmir's Fort, Yorwick, Lich Lab, the finale, ~2.3M of the original 4.3M): the
  rework converts them, through the same helper.
- **Script slip, fixed in conversion:** Mountain Pass's 14,000 could pay twice (the second branch does not check key
  80); `mm9r_mountainpass_blv/regionlua.py` pays it once (key 80 on the quest, else 176).

### 3.2 Monster stats and behaviour

Implemented (2026-11-06) in `tools/mm9_import_discovery/mm9_monster_balance.py`, which `generate_mm9_monster_tables.py`
applies to every generated row. It changes only the 145 combat rows of its families; townsfolk, animals and named story
characters (the Jarls, Forad Darre, Tamur Leng, Njam, the gods) keep MM9's numbers.

| Field | Rule |
| --- | --- |
| HP | MM9's; ×0.95 at levels 41–60, ×0.90 above 60. |
| AC, damage per hit, XP | MM9's, except damage ×0.75 at levels 1–5. |
| Recovery | 75 ticks (1.25 s) at levels 1–20; MM9's 59 above. Walking, running and turning stay MM9's. Damage per second then lands at 0.92–1.12× MM7's in every level band. |
| Spell use | About 0.4 × MM9's chance, at most 40%; condition spells (Fear, Paralyze, ...) at most 25%. MM9's 50–100% use comes from its own casting model and spams under ours. |
| Spell skill | At most MM6–MM8's highest monster spell skill for the ten levels (Zombie L17 had Harm M,28). |
| Resistances | Family profiles by name (`FAMILIES`, 20 themes): each of the seven schools takes the MM6–MM8 median for the level (0 to level 10, 5, 15, 18, 30 above 55), the theme's immunity `Imm`, its strong school 2 × base + 20 and its weak school 0. For example undead and vampires are immune to Mind, strong in Body and weak to Spirit; fire creatures and demons are immune to Fire and weak to Water; ice creatures the reverse; fighting people have no theme. MM9 had one value for the four elements and one for the self schools (up to 100 late), so a caster's best school yielded 0.62–0.87 of its damage against MM7's 0.93–1.0. Light, Dark and Physical stay MM9's. |
| On-hit conditions | None, as in MM9 (accepted as MM9 character). |

### 3.3 Gold and drops

Implemented (2026-11-06; treasure levels and factors revised 2026-11-07) in `mm9_monster_balance.py` (the treasure
column). Per kill, replacing the flat 25%: gold dice with average `XP × gold rate`, item chance `XP × item rate × 0.8`
(at most 50%),
treasure level by the monster's MM9 level on the second table. The rates are MM7's per level band
(`balance_prototypes/economy.py`); an MM9 monster gives about 1.5× the XP of an MM7 monster of its level, so it pays
about 1.5× the loot. The gold factor covers MM9's smaller quest gold (about 0.24M against MM7's 0.4–0.5M).
**Gold ×2.2** (`GOLD_FACTOR`, the user, 2026-11-08): kill gold at MM7's rate felt like nothing (a level-55 Specter
paid about 400); every monster's gold dice now average 2.2× the rate below (the Specter about 900, a level-79 Spectre
Dagrell about 2,900). This puts campaign kill gold well above MM7's on purpose; the totals below are from before.
**Items ×2, at most 75%** (`ITEM_FACTOR` 1.6, `ITEM_CHANCE_CAP` 75, the user, 2026-11-08: kills gave gold and almost
no items). MM9's chances per level matched MM6–MM8's, but its kills are fewer and its levels compressed; a kill now
drops an item about 5% of the time at levels 0–9, 14–21% at 10–39, 30–44% at 40–59 and 60–72% above (the Specter 47%).
Ground treasure markers are planned in [Ground treasure](GROUND_TREASURE_PLAN.md).

| Level | Gold per 1,000 XP | Items per 1M XP |
| --- | --- | --- |
| 1–5 | 109 | 180 |
| 6–10 | 107 | 253 |
| 11–15 | 80 (64 measured, smoothed) | 163 |
| 16–20 | 88 | 156 |
| 21–30 | 82 | 84 |
| 31–40 | 79 | 53 |
| 41–55 | 76 | 55 (116 measured) |
| 56–80 | 124 | 52 |
| 81+ | 142 | 62 |

| MM9 level | 1–7 | 8–15 | 16–30 | 31–44 | 45–64 | 65+ |
| --- | --- | --- | --- | --- | --- | --- |
| Treasure level | 1 | 2 | 3 | 4 | 5 | 6 |

- **Treasure levels by stage, not level for level.** MM9's levels are compressed: its last chapter fights levels 30–79,
  MM7's last stage 65–100. MM6–MM8 give L5 at levels 61–79 and L6 from 80, so taking MM7's level curve (the first
  version) gave chapter 5 no L6 drop at all and flooded chapters 4–5 with L4 (297 L4 drops against MM7's 52; two L6
  drops in the game, both bosses). The second table is set so each chapter's drops take its MM7 stage's mix.
- **The 41–55 items rate** was MM7's measured 116 per 1M XP, twice its neighbours: one monster's, the Fire Hydra (level
  45, an L3 item on every kill, 76 kills). The band takes its neighbours' rate (55).
- **Against MM7 as it is played, not fully cleared** (the user, 2026-11-07): MM7 parties fly over or walk past about
  half of an outdoor map's monsters and leave a tenth of a dungeon's; MM9 has no Fly, so they kill 85% outdoors and all
  in dungeons (`balance_prototypes/fit_check.py` `CLEAR`, used for every kill count: XP, party levels, the probe's
  mixes, gold, drops; `--clear 1` counts everything). Against a full clear the factors were 1.15 gold and 1.0 items;
  realistic MM7 has 330 monster drops (not 442) and 0.85M kill and quest gold (not 0.98M), so they are 1.0 and 0.8.
  A little in MM9's favour is fine (the user); the gate's band is ±15%.
- **Story bosses** (`BOSSES`: the Dragon King, Njam the Meddler, Forad Darre, Tamur Leng) drop an L6 item on every kill,
  as MM6–MM8's dragons and lords. The six Jarls are friendly characters and keep no treasure; Ebora cannot be hurt.

Drops at the planned density (balance report, "Drops by treasure level"):

| Chapter | MM7 stage: L1 / L2 / L3 / L4 / L5 / L6 | MM9 before (2026-11-06) | MM9 now |
| --- | --- | --- | --- |
| 3 | 0 / 6 / 25 / 13 / 12 / 3 | 3 / 21 / 16 / 30 / 2 / 0 | 1 / 9 / 38 / 22 / 6 / 2 |
| 4 | 0 / 5 / 89 / 28 / 20 / 6 (Fire Hydra: 76 L3) | 0 / 13 / 9 / 149 / 39 / 0 | 0 / 5 / 22 / 63 / 73 / 22 |
| 5 | 0 / 0 / 0 / 0 / 37 / 71 | 0 / 0 / 0 / 118 / 50 / 0 | 0 / 0 / 0 / 12 / 68 / 51 |
| All | 35 / 59 / 145 / 52 / 70 / 82 (442) | 17 / 39 / 28 / 297 / 91 / 0 (470) | 8 / 26 / 65 / 97 / 146 / 75 (417) |

Campaign totals as played (the clear shares above): kill gold plus quest gold 0.85M against MM7's 0.85M (1.01×), item
drops 326 against 330 (0.99×), L6 drops 62 against 56 plus the bosses'. The drop table above is the full-clear
comparison before the factors changed. Chapters 1–2 give few items (about 24 against MM7's 128 in its first two stages)
because they have a fifth of MM7's kills: a density matter (3.6), not a treasure one. MM9's treasure type (Weapon,
Armour, Item, Random) stays the item category. This supersedes the "exact MM9 gold" and drop-chance parts of
[MM9_MONSTER_NPC_LOOT_IMPLEMENTATION_GOAL](../mm9/MM9_MONSTER_NPC_LOOT_IMPLEMENTATION_GOAL.md); its actor ownership,
fixed death items and save behaviour still hold.

### 3.4 Items: balance profile version 2

Implemented (2026-11-06) in `tools/mm9_import_discovery/mm9_item_balance.py`, applied by `import_mm9_items.py`; every row
records its rule in `x_mm9_balance_profile` (`mm9_balance_v2:weapon_ladder:Sword1H|...`). The importer keeps reading
MM9's own numbers (MASTERITEMLIST.csv, `mm9_item_effects.yml`), so the source stays MM9's.

**Ordinary weapons.** Targets are the MM6–MM8 medians per skill, handedness and tier (average damage including the flat
bonus, which is also the attack bonus in our engine):

| Family | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| Sword 1H | 4.7 (+0) | 6.4 (+0.7) | 9.6 (+3.4) | 13.4 (+7.7) | 17.8 (+12.2) | 20.3 (+14.6) |
| Sword 2H | 10.0 (+0) | 12.5 (+0.5) | 15.0 (+3) | 20.0 (+8.7) | 24.0 (+12) | 27.0 (+16) |
| Dagger | 2.2 (+0) | 3.5 (+0.6) | 5.5 (+2.6) | 7.9 (+5) | 9.5 (+7) | 12.0 (+8.7) |
| Axe 1H | 4.5 (+0) | 7.0 (+1) | 9.8 (+4.3) | 12.8 (+7.3) | 16.2 (+11) | 19.0 (+13) |
| Spear | 6.5 (+0) | 7.9 (+0.9) | 11.9 (+4.4) | 16.1 (+9.4) | 19.1 (+13) | 23.5 (+16) |
| Mace 1H | 4.5 (+0) | 6.2 (+1) | 8.8 (+3.6) | 12.4 (+7.1) | 16.0 (+11.5) | 18.3 (+12.7) |
| Staff 2H | 4.0 (+0) | 5.5 (+1) | 7.5 (+2.5) | 10.0 (+5.3) | 12.0 (+7) | 13.5 (+9) |
| Bow | 5.2 (+0) | 7.6 (+1) | 10.1 (+3.8) | 13.4 (+6.8) | 17.2 (+10.6) | 17.8 (+11.3) |

- Keep each MM9 family's dice at quality 1–2; raise the die size by one at quality 3 and again at quality 5
  (2d4 → 2d5 → 2d6; 3d3 → 3d4 → 3d5). Set the flat bonus so the average reaches the target; it ends near 80% of
  MM6–MM8's, so attack stays close to parity while the dice carry visible growth.
- MM9's five qualities stand for MM6–MM8 tiers 1, 2, 3, 4 and 6 (`reference_tier`; user, 2026-11-08): quality 5 is
  MM9's only ordinary equipment of treasure level 6, so it takes the L6 target, like MM6–MM8's top pieces (Lionheart
  Sword, Mighty Halberd), slightly above their level-6 average. Before, it took the L5 target and MM9's level-6 swords
  and spears were 0.87–0.94× MM6–MM8's.
- Example, short swords: Poor Sword (q1) 2d4+0 = 5.0; Shaba Couta (q2) 2d4+1 = 6.0; q3 2d5+3 = 9.0; q4 2d5+7 = 13.0;
  Imperial Sword (q5, base 3d3) 3d5+11 = 20.0.
- MM9 spears become one-or-two-handed like MM6–MM8 spears; halberds stay two-handed and follow the two-handed axes
  (10.5, 12.5, 14.5, 18.5, 25.0, 27.2), as do MM9's two-handed maces. Throwing weapons follow the dagger and axe ladders.
  Dice far above a tier's target (more than 25%) lose die size first (Flail 2d6 at tier 1 becomes 2d4). MM9 has no
  ordinary quality 6; tier 6 comes from enchanted shop and loot stock.
- Result: every family averages 0.98–1.09 of its target (balance report).

**Ordinary armour.** Armour value (base + bonus), MM6–MM8 medians, smoothed where a median dips; MM9's top ordinary
armour (quality 5) gets the L6 column, as its weapons do (2026-11-08):

| Slot | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| Leather | 3 | 4.5 | 7 | 10 | 16 | 24 |
| Chain | – | 7 | 12 | 20 | 28 | 39 |
| Plate | – | – | 18 | 26 | 38 | 59 |
| Shield | 3 | 5.5 | 10 | 14.5 | 16.5 | 18.5 |
| Helm | 1 | 3 | 6 | 9 | 12.5 | 15 |
| Boots | 1 | 1.5 | 4.5 | 8 | 11 | 14 |
| Gauntlets | 1 | 1.5 | 4.5 | 8 | 12 | 15 |

MM9 families keep their order within the slot: each piece is the tier target times its MM9 value over its tier group's
mean (shield tier 5 smoothed to 16.5). The early MM9 lead (leather 9.5 at tier 1) goes. Belts keep their small armour
value (mild MM9 character); rings and amulets stay at zero. Corrections of 2026-11-06 (evening):

- MM9 has no ordinary quality 6, so its tier 5 pieces are the only ordinary armour of treasure level 6. They took the
  midpoint of L5 and L6 until 2026-11-08 and now take L6, like MM6–MM8's top pieces: Dark Plate 60 (Noble Plate 58,
  Dragoning Plate 64), Chain Harness 40, Aklean Bouila 28.
- The helm medians counted hats and crowns, which have no armour; counting armoured helms only, helms match boots and
  gauntlets (Jarl's Helm 9 → 16).
- Plate L4 is the geometric mean of L3 and L5 (26): its median, 21, is the entry plate of MM6 and MM7 and was no better
  than tier 4 chain (20) for a heavier skill.
- MM6–MM8 have no L1 shields, boots or gauntlets; MM9's tier 1 pieces kept MM9's values and beat tier 2 (Footman's
  Buckler 10 against Small Shield 6). They now take a step below L2.

**Prices.** An ordinary MM9 item costs what an MM6–MM8 item of its strength costs (2026-11-08 for weapons and
jewellery):

- Armour: MM6–MM8 armour prices are a function of armour value per slot (about 50 gold per point for body armour, 75
  for helms, boots and gauntlets; `ARMOR_PRICE_CURVES`): Field Plate 750, Heavy Plate 1,300, Dark Plate 3,500, Padded
  Leather 100.
- Weapons: the MM6–MM8 price of the weapon's average damage in its family, on the monotone least-squares curve through
  MM6–MM8's ordinary weapons (`EngineReference.weapon_price`, read from the engine tables at import; halberds on the
  spear curve, two-handed maces on the two-handed axes'). The tier envelope had priced MM9's spears as two-handed
  weapons (Crude Spear 150 against MM6–MM8's 15–100 for its damage, Abli Duta 550 against 250), its staves and daggers
  at two to three times MM6–MM8's, and its two-handed swords a third low. Now: Crude Spear 65, Abli Duta 250, Imperial
  Spear 1,300, Flamberge 1,800, Truth Staff 600, Imperial Sword 900.
- Belts, rings and amulets: the MM6–MM8 median of the kind at the tier, below their lowest tier that tier's cheapest
  (MM6–MM8 start them at tier 2–3): Diamond Ring 2,100, Thjoradric Amulet 1,800, Soldier's Belt 60.
- Every MM9 price is round like MM6–MM8's: a multiple of 5 below 100, of 50 below 1,000 and of 100 above
  (`round_price`; the balance report checks it). Before 2026-11-06, every piece of a category and tier cost the same
  clamp bound (437, 1,093, 1,468), whatever its armour.

**Artifacts, relics and sets** (as implemented):

| Item group | Change |
| --- | --- |
| Artifact and relic weapons | Dice kept; a flat bonus brings the average to 24 (one-handed), 30 (two-handed) or 20 (missile), the bonus between +5 and +18 (Sing Sword 2d6+17, Mevan Sword 10d5+5, Gungnir 3d9+15). |
| Integris | Melee attack +35 → +20 and damage +35 → +15; its weapon damage and poison stay. |
| Artifact armour | Capped by slot: plate 75, chain 50, leather 32, shield 32, helm, boots and gauntlets 15 (Swordsbane 93 → 75 with its +40 melee AC kept, Arrowfoe 64 → 32, Laet'ax 31 → 15, Brongnoker 26 → 15, Death Cuirass 43 → 32). |
| Regeneration | 0.2 → 1.0 HP/s on every MM9 item and set that regenerates. |
| Relics | Weregild gains Luck +30 (it already pays 1,000 gold a week against its −40 party Endurance); Fizbin of Misfortune, the one with drawbacks only, gains Might +15, Accuracy +15 and all resistances +10. Screever keeps its immunity to all conditions. |
| Pendant of the Spheres | +5 → +3 in each of the nine schools; Learning and Meditation +3 stay. |
| Weak artifacts and relics (OY-589, 2026-11-13) | Raised into the MM6–MM8 curve (about +40 in stats or a +20 pair with a perk; relics more, with a drawback), `PER_ITEM_EFFECTS`: Igdrasine Intellect and Personality +10 → +30; Jorhgamesh Speed +40, Accuracy +40, SP −50 (MM9's drawback; the data had +50); Bloodaxe and Arrowfoe Endurance +30; Everstrike Bow +5 and faster recovery; Tillhygge +5 disease damage (its disease flag had no damage to carry); Formanir Might +50; Einherjar Might +40; Blutterbunger Might +40, Endurance +20; Spencer's Obedience Speed +30, Might +20; Mjulnir Might +50; Poltergeist Speed +30; Laet'ax Luck +40, Disarm Traps +10, Accuracy −20; Mountbatten Personality +30; Fre's Heart HP +100, Endurance +30, SP −20. Sygnir's +6 Blade is Axe (it is an axe), not Sword. |
| Effect text (OY-588) | Each artifact and relic description ends with an "(Effects: ...)" list written by the importer from its final effect (`effect_text`), not MM9's own list; MM9's typos in the stories are corrected (`DESCRIPTION_CORRECTIONS`). Set pieces keep MM9's list. |
| Sets | Piece effects and five-piece bonuses stay; Prize Shield and Prize Skullcap gain +4 armour. |

### 3.5 Shops and the random loot pool

- **Shops** (implemented 2026-11-06, `tools/mm9_import_discovery/mm9_vendor_balance.py`, stock generation version 5 since tier 5 moved toward levels 5–6 on 2026-11-07):
  equipment shops (weapon, armour, general store, apothecary) stock at the treasure level of MM7's shops at the same
  stage: Sturmford 1 (Emerald Island, Harmondale), Drangheim and Guberland 2 (Erathia, Tularean Forest), Thjorgard,
  Frosgard, Thronheim and Lindisfarne 3 (Avlee, Tatalia), Yorwick 4 (Mount Nighon, The Pit), Arslegard 5 (past
  MM7's shops); the standard shelf at that level, the special shelf one higher. Item tiers by the tier mix of the level (`RANDOM_WEIGHTS`);
  enchants as the engine rolls them (`ItemEnchantRuntime.cpp`): standard bonus 40% (75% at level 6) with the level's
  power (+1–5 up to +15–25), specials at the level's weapon or equipment chance among the rarities it allows (A–B at
  3 ... D at 6). As in MM7, the special shelf is only the higher level: nothing is enchanted by force, so Sturmford
  sells tier 1–3 weapons without specials (version 3 stocked levels 2/3 with every special-shelf item enchanted,
  which put an Assassins' Dark Bow, tier 4 with poison, in the first city). Seeded per shop, shelf, page and slot, so
  stock stays authored. Books and libraries keep MM9's stock. Saves' stock regenerates on the version change.
- **One random loot pool** (user, 2026-11-08; [LOOT_POOL.md](../LOOT_POOL.md)): monster drops, random chests and
  random map treasure roll from every mounted world's items in every world; shops keep their world's own equipment.
  Artifacts and relics drop only in their own world (`World:<id>`; MM9's only from its black chests,
  `chestArtifactsOnly`). It replaced the setting "random loot from other
  worlds" of 2026-11-06 (own world only by default, own artifacts with shared items, all worlds), which is gone.
- **Random weights** (revised 2026-11-08): `import_mm9_items.py` writes `data_tables/random_items.txt` (133 ordinary MM9
  items), contributed through `world.yml` (`table: random_items`). Each MM9 item weighs what MM6–MM8's items of its
  family and tier weigh, their mean weights per treasure level (`EngineReference.weights`; an MM6–MM8 item's tier is its
  weighted mean level, rounded; quality 5 as tier 6). Where MM6–MM8 have none of a family's tier (boots, gauntlets,
  shields, belts, rings and amulets start at tier 2), the nearest tier's. So the pool keeps MM6–MM8's shapes: entry plate
  drops mostly at level 4 (as Rusty Breastplate, Plate Armor), not level 3, and two-handed swords stay rare. Measured in
  the balance report ("Random loot pool"): the main families' mean damage and armour in the pool stay within 0–15% of
  MM6–MM8's alone at every level; MM9's items are 36% of the equipment at level 1 (MM9 has one of every family there)
  and 18% at levels 5–6; an untyped drop is equipment 68–81% of the time against 58–78% (MM9 brings no consumables).
  Before, MM9's
  columns were scaled so its 133 pieces weighed what MM6–MM8's 428 do, right for an MM9-only pool but three times an
  MM6–MM8 item each in a mixed one.

### 3.6 Density

Spawns use ordinary native spawn points against the MM9 map-stats rows, with A/B/C families built from MM9 rows (PLAN.md,
"Spawns"): Dragonfly Mite / Dragonfly / Fire Dragonfly; Imply / Imp / Imp Elder; Nagate Hatchling / Nagate / Nagate
Elder; Field Thrall / Thrall / Thrall Master; Skeleton / Skeleton Warrior / Skeleton Master; Grey / Red / Black Wolf;
Canopic / Embalmed / Petrified Mummy; Basilisk / Fibrase / King Basilisk; Lizard-Orc / Warrior / Mage.

Measured on the rebuilt maps (2026-11-06; `mm9_balance_report.py --runs 32000`, bolster on). The user's band: a bit
easier than MM7 is fine, especially at the start, so the gate takes 0.7–1.2× MM7's damage per pack and nothing is tuned
up to exactly MM7.

| Act | Monsters vs today | Why |
| --- | --- | --- |
| 1 | 1.9× | A little easier than MM7's start, as the user wants. Was 1.4× (packs 2.3, 0.76 projected, 0.41 once the outdoor swimmers stopped counting: they had been most of the chapter's measured threat); raised 2026-11-07 so its packs reach MM7's. |
| 2 | 1.4×; none on the early maps | The early maps' level 6–20 monsters are MM9's strongest against MM7's and the party is furthest behind (17 against 21); +10% read 1.19–1.24, on the band's top (user, 2026-11-06). Yanmir's Fort, the Lich Lab, Verhoffin Ruins and the Training Hall came from chapter 4's 2.3× (2026-11-07). Yanmir's Fort does not grow: its map Lua names every one of its 65 monsters, so the converter copies none. Thjorad Mine 1.4× since 2026-11-09 (the user, after a day at 1.8×: as the rest of the act; 77 → 108 Troglodytes; MAW adds more). |
| 3 | 2.3× | MM9's war monsters average level 37–44 against MM7's 46. |
| 4 | 5×; the Tomb 2× | The finale's ordinary monsters average level 45 against MM7's 70: packs of about seven demons and terrors in the Tomb of 1000 Terrors. Grown at last on 2026-11-09, its 5× piled about ten times the monsters into its open halls (7 within 4,000 units of one spot became 72), so the user set it to 2× (186 monsters). |

**Re-frozen 2026-11-07** for Isle of Ashes, Sturmford, Beethoven, Anskram Keep, Thronheim, Thjorgard and Guberland
(`mm9_density_targets.py --force --maps ...`, from their actors before growth; `density_anchors.py --maps ...`):
outdoor swimmers no longer count and chapter 1 grows 1.9×. The converter's growth also changed then
(`dungeon/density.py`): a pack's copies follow its own mix (the row furthest below its share, not the first member
listed), and a copy that must move goes to a pack with an ordinary member of its row. Under the first rule Beethoven's
growth was 22 Bone Thrashers of 33; its script-named Lobbers' and hidden Mummies' copies went to the roomiest packs.

**Targets** (`tools/mm9_import_discovery/mm9_density_targets.py` writes `mm9_density_targets.yml`, the frozen
pre-growth baseline; it refuses to overwrite it without `--force`): per map its chapter, factor, counted monsters today
(1,476 in all) and the target (2,723), and per pack its placed actor indices, size, target, room-check capacity and
`add`, the copies of the pack's own monsters the rework converter places next to it. The counting rule is in the
script (`counted_actor`): a hostile combat-family monster, not an NPC, civilian or passive scripted actor, not a
swimmer on an outdoor map (`modifiers.yml` `movement: swim`, the Jellyspore family and the Sea Monsters: outdoors
they stay in the sea and lakes and the party need not fight them, in a dungeon's pools they count; the user,
2026-11-07), below level 150. The report reads these targets by default (`--mm9-source targets`); after the rebuild the gate runs on the scenes
as installed (`--mm9-source scenes`). Today's ungrown scenes read 0.51 / 0.97 / 0.61 / 0.40 / 0.23.

- Grow packs at the existing positions; do not add packs, except in the largest halls and long empty stretches, and
  never on roads between towns. MM9 dungeons already meet a pack as often as MM7's (spacing 1,790 against 1,860).
- The larger packs late in the game raise kill XP (end level about 69), which the measured fight costs above include.
- **Room check** (`balance_prototypes/pack_room_check.py`, 2026-11-06, on the rebuilt chapter 4–5 BLVs): with each pack
  grown to 4 (chapter 4) or 7 (chapter 5), or kept when already larger, and a pack allowed at most a third of the free
  space where it stands (16 rays to the walls from each member), 180 of 197 chapter 4 packs and 58 of 71 chapter 5 packs
  fit. The misses are single monsters in alcoves and narrow passages (0.15–0.27M units², 160–390 units wide: Orbuses
  and Oculi in the Tomb's side rooms, Terrors along the Dark Passageway); they stay small and the neighbouring rooms
  take the extra monsters. Counted the same way, the maps hold about twice what the plan adds (chapter 4: 1,730 places
  for 830 monsters; chapter 5: 616 for 393, the Tomb alone 585 for 335); the targets above use the same check per pack. Two scripted story maps do not follow the
  chapter factor (user, 2026-11-06): Klusos's House gets no extra monsters (a scripted dungeon whose guards sleep until
  woken), and the Temple of Honk takes what fits (room for about 31 of the 58 the factor asks; its Honks are a scripted
  congregation). The chapter's other maps do not make up the difference. Passive
  scripted actors (the Tomb's flying critters) and unique bosses (the Dragon King) are not packs and do not grow.
  Yorwick and the Afterworld are outdoor maps with room to spare.
- **Forced arrivals** (user, 2026-11-09): where a teleporter or trap puts the party, growth adds at most a few copies,
  so a weak party is not dropped into a grown pack with no way out. Per map in overrides.yml
  `map: density_arrivals` (`dungeon/density.py`): Dark Passageway's one-way landings 2 copies within 3,400 units
  (Teleporter0, the ocean cage's, was MM9's 4 Terrors and became 10; now 6), Lake and Mountain kept at their 3;
  Wizard's Lab's stations Green 3, White/Red/Yellow 2 within 2,000. The other copies move to the map's other packs.
- Small dungeons take the low end; measure per area, not per map (MM9 exteriors range from 13k to 45k units across).
- No Fly in the MM9 world (Fleet Foot instead): every placed pack is a forced fight, which the threat targets include.

### 3.7 Bolster

Implemented (2026-11-06): `assets_dev/engine/data_tables/bolster_maps.txt` has a row for each of MM9's 44 maps (ids
9001–9079, the Bootcamp left out): `LowerToEqual`, spells allowed, summons off, as most MM7 maps; continent 0, so MM9's
sky and weather stay its own `weather.yml`'s. Bolster is on by default (`[features] bolster_monsters`): monsters below
the party's level rise toward it, and their hits meet the party's AC scaled by their level against the party's
(`gameplayBolsterPlayerArmorClass`). MM7's maps have the same rows, so the balance is measured with bolster on in both
worlds (section 1). A party arriving from MM7 at level 50 finds chapter 1–3 monsters raised as on the other continents,
which MM9 as a start continent needs.

### 3.8 Chests and artifacts

The user's rules (2026-11-06): in MM9 only black chests hold artifacts; a black chest always holds an artifact or relic
while any is left to find, otherwise gold and a level-6 item.

- **Which artifacts roll** (fixed 2026-11-07): the level-7 slot picks artifacts and relics without `NoRandom`, and every
  MM9 one carried it, so no black chest could give one (each gave gold and an L6 item). `import_mm9_items.py` now flags
  MM9 artifacts and relics `Unique` only, except those with a fixed source (`FIXED_SOURCE_RARE_RAW_IDS`: Black's Heart,
  Everstrike, Gungnir and Spencer's Obedience, hand-placed in black chests, and The Green Man, Frosgard's quest reward)
  and the two quest items (Thjorad, Fizbin of Misfortune), which keep `NoRandom` so no chest gives a second copy. 36 of
  MM9's 43 artifacts and relics roll for the 15 level-7 slots; the balance report checks the fixed sources against the
  scenes and event scripts. Set pieces (Prize, Broderick's, Death, Fre's) are not artifacts in the engine and have no
  source yet.
- **Engine:** `world.yml chestArtifactsOnly: true` turns off the 5% artifact roll on level-6 loot in that world
  (monster drops, ordinary chests, events) and makes an exhausted level-7 chest slot give gold and a level-6 item
  (MM6–MM8 keep an empty slot, as OpenEnroth). Loot containers take an optional `random_records` (default 1): that
  many random records of their level, each rolling 1–5 times as an MM6–MM8 chest slot.
- **Data** (`tools/mm9_import_discovery/mm9_chest_balance.py`, called by the rework converters): black chests' random
  slot is one level-7 record (15 chests; the 6 with hand-placed items keep them); level-0 random containers (13, mostly
  chapter 1, empty until now: the engine fills nothing at level 0) take their map's most common chest level; every
  other random container holds 3 records, MM7's average chest (1,194 random records in 406 chests).
- **Chest tiers** (`TIERS`, the user, 2026-11-08, after T2 chests in Ta'Sar Academy): every map's ordinary chests
  give set item tiers. The user set act 2's (Ta'Sar Academy, Yanmir's Fort, the Chasm of the Dead T4; Dook's Castle,
  the Training Hall, Thjorgard, Thronheim T3; Drangheim T2-T3); the other maps follow them, about a tier above MM9's
  own levels and rising through each act:

  | Act | Tiers |
  | --- | --- |
  | 1 | Isle of Ashes, Sturmford T1-T2; Beethoven, Anskram Keep T2 |
  | 2 | Drangheim, its prison T2-T3; Dook's Castle, Training Hall, Thjorgard, Thronheim, Thronheim City, Lindisfarne T3; Frosgard, Mountain Pass, Ta'Sar Academy, Inventastorca T3-T4; Yanmir's Fort, Chasm of the Dead, Ruined Temple T4; Lich Lab, Verhoffin Ruins T4-T5 (Verhoffin's first chest, TreasureChest3, T4: `CONTAINER_TIERS`) |
  | 3 | Yorwick T4-T5; Wizard's Lab, Connecting Tunnels, Bathhouse T5; Dark Passageway T5-T6 |
  | 4 | Temple of Honk T5-T6; 1000 Terrors half T5, half T6 (by chest: its four nearest the start T5, `CONTAINER_TIERS`; the user, 2026-11-09) |

  Each record takes the lowest level the engine's chest remap (ChestRuntime.cpp) turns into exactly those tiers on its
  map's treasure level, e.g. 6 on Ta'Sar Academy (map level 2) for T4. A level-0 map gives only T1 and a level-1 map
  T1-T2, so act 1's maps have treasure level 1 and Drangheim, Drangheim Prison, Thronheim City and Lindisfarne 2
  (`MAP_TREASURE_LEVEL`, written into their map_stats rows by dungeon/tables.py); their monster drops and floor
  treasure remap against that level too.
- **Against MM7** (`balance_prototypes/chests.py`, through the engine's chest rules and map treasure levels): each MM9
  chest holds what an average MM7 chest holds. MM9 has fewer chests (167 against MM7's 406) and that is not made up with
  fuller ones (the user, 2026-11-06), so MM9's chests give about 460 items over the game against MM7's 1,430 (156 before,
  one record each).

| Chapter | MM7 stage: chests, items, mean level | MM9 before: items | MM9 planned: chests, items, mean level, artifacts |
| --- | --- | --- | --- |
| 1 | 58, 173, 1.3 | 17 | 27, 90, 1.0, 0 |
| 2 | 188, 708, 2.4 | 16 | 29, 47, 1.5, 1 |
| 3 | 88, 311, 2.9 | 47 | 41, 133, 2.8, 2 |
| 4 | 57, 169, 3.4 | 54 | 49, 148, 3.5, 5 |
| 5 | 15, 72, 4.7 | 23 | 21, 43, 5.1, 7 |

  Item levels follow MM7's by chapter, a step lower in chapters 1–2 (set by those maps' treasure levels in
  `map_stats.txt`).

## 4. Verification

**Balance probe** (`tools/balance_probe_main.cpp`, target `openyamm_balance_probe`; read-only). Engine-built reference
parties fight each MM9 chapter's packs and each MM7 stage's packs (MM7 maps grouped by their median monster level), with
the engine's own rules:

- Party of five, the same in both worlds: Knight, Paladin, Archer, Cleric, Sorcerer lines, promoted at levels 20 and 40.
  Skill points by the MM6–MM8 rule (5 a level plus one per ten levels), spent on each class's main skills; masteries
  from the class skill caps and `SkillRules::masteryRequiredLevel`; every spell the masteries allow;
  `refreshCharacterBaseResources` for HP and SP. Stats grow with level (primary 18 + 0.8 × level).
- Gear: the median ordinary engine item of each slot at the chapter's shop tier (tier 2–6), standing in for the section
  3.4 ladders (`--mm9-items` wears today's MM9 items instead).
- Attacks: `GameMechanics::buildCharacterAttackProfile` and `resolveCharacterAttackAgainstArmorClass`; spells:
  `CombatRules::rollSpellDamage` at the caster's rank and mastery, area spells (Fireball, Meteor Shower, Inferno,
  Starburst, ...) catching 70% of a pack, spreads of projectiles hitting one target 1 + 0.3 per extra projectile;
  casters start a fight with half their SP and take the spell with the best damage per second, else their weapon.
- Monsters: the monster table rows as generated (section 3.2 is in MM9's table; `--no-mm9-changes --no-profiles` keep
  the probe from applying its own older stand-ins), with their attacks, missiles, spells (base + skill dice, as
  `GameplayProjectileService`) and use chances; hit rolls `monsterAttackHitsArmorClass` against the sheet AC; damage
  through `resolveCharacterIncomingDamage` and `resolveMonsterIncomingDamage`. `--bolster` runs the engine's
  `resolveGameplayMonsterBolster` with a map row of the world and `gameplayBolsterPlayerArmorClass`, as play does.
- Each fight: one monster family per pack, its size around the chapter's mean; real-time turns by recovery; result:
  clear time and damage taken as a share of the party's hit points.

Run (party levels come from the XP curve of `fit_check.py`, with the quest XP profile and the decided density):

    cmake --build build --target openyamm_balance_probe -j25
    python3 devdocs/mm9_rework/balance_prototypes/probe_input.py output/mm9_balance/probe_input.tsv
    ./build/tools/openyamm_balance_probe output/mm9_balance/probe_input.tsv output/mm9_balance/probe_out.tsv --runs 8000 \
        --no-mm9-changes --no-profiles --bolster
    python3 devdocs/mm9_rework/balance_prototypes/probe_compare.py output/mm9_balance/probe_out.tsv

Options: `--bolster`, `--mm9-items`, `--no-mm9-changes`, `--no-profiles`, `--area SHARE`, `--sp SHARE`, `--dump`
(prints every party).
What the variants showed (2026-11-06): without the section 3.2 monster changes chapter 2 costs 1.52× MM7's; with today's
MM9 items kills take up to 1.5× longer in chapters 2–3; without the resistance profiles fights cost 5–15% more and kills
take 10–25% longer.

Not in the probe: MM9's AI and positioning (melee monsters reach the party at once), healing and buffs, on-hit
conditions (which MM7 monsters have and MM9 monsters do not), item enchantments.

**Fit check** (`balance_prototypes/fit_check.py`): the level-based first model, kept for the XP curve (party level per
chapter from kill and quest XP) that the probe takes its party levels from. Its party side is a stand-in (damage
5 × (level + 5), AC 2.5 × level + 15), so its fight numbers are superseded by the probe's.

**Balance report and gate** (`tools/mm9_import_discovery/mm9_balance_report.py`, writing
`devdocs/mm9_rework/BALANCE_REPORT.md`; `--gate` exits 1 when a value leaves its band): every ordinary MM9 weapon and
armour family against its ladder target (±25%); the monster rules on every combat row (recovery, spell caps, a
resistance profile, treasure); shop stock per city (enchant power within the shelf's treasure levels); campaign kill
gold plus quest gold and item drops from the generated treasure fields against MM7's (±15%); each chapter's mean drop
treasure level against its MM7 stage's (±0.6, MM7's Fire Hydra left out) and the campaign's L6 drops (0.75–1.25×); the
equipment share of an untyped random item per treasure level against MM6–MM8's (±5 points); the artifacts the black
chests can roll (fixed-source ones keep `NoRandom`, at least one per level-7 slot); quest XP per chapter;
and the probe per chapter with bolster on (damage per pack 0.7–1.2× MM7's, kill time at most 1.5×). The default
`--mm9-source targets` scales each map to its frozen target from today's count, so maps already grown count as they
stand. Run after any change to the MM9 tables:

    cmake --build build --target openyamm_balance_probe -j25
    python3 tools/mm9_import_discovery/mm9_balance_report.py --gate

Unit tests: the balance rules in `tools/mm9_import_discovery/test_mm9_balance_profiles.py`; the shop stock in
`test_generate_mm9_vendors.py`; the quest XP caps in `test_mm9_scr_to_lua.py`; the engine's world `random_items` rows and
shops' own-world filter of the common loot pool in `tests/LootPoolTests.cpp`; MM9 world data (a balanced monster row,
stock version 5, black chests rolling MM9's own artifacts, the L6 equipment mix) in `tests/Mm9RudeDialogueTests.cpp`;
artifacts staying in their world in `tests/LootPoolTests.cpp`.

**Playtests:** chapter 1 against Emerald Island and Harmondale, then chapter by chapter. The values to move: density per
chapter (3.6), the cap sizes (3.1), the gold and item factors (3.3), the HP trim (3.2).

## 5. Order of work

| Step | Work | Status |
| --- | --- | --- |
| 1 | Quest XP to every member | done 2026-11-06 |
| 2 | Quest XP caps in the converters and profile | done 2026-11-06 (the transcoder and the rework converters); in the game at the next conversion (3.1) |
| 3 | Balance probe and the balance report and gate (section 4) | done 2026-11-06 |
| 4 | Items: weapon and armour ladders, artifacts, relics and sets (3.4) | done 2026-11-06 |
| 5 | Monsters: recovery, low-level damage, HP trim, spell use and skill, resistance profiles, gold and drops (3.2, 3.3) | done 2026-11-06 |
| 6 | Bolster rows (3.7) | done 2026-11-06 |
| 7 | Shops, MM9 items in the random pools, the loot setting (3.5) | done 2026-11-06; one common pool 2026-11-08 |
| 8 | Density per map as each map is rebuilt (3.6), checked by the report | with the map rebuilds |
| 9 | Playtests, chapter by chapter | after the rebuilds |

## 6. Open points

| Point | Recommendation | Why |
| --- | --- | --- |
| Chapter of each map | Check the table below against the quest flow when the report is built. Dook's Castle moved from chapter 2 to 3 on 2026-11-06 (its monsters are levels 22–51). | The per-chapter levels and caps depend on it. |
| MM9 floor area | Exclude brush tops in the report's raster. | The current figure may run 10–30% high. |
| Quest XP caps in the rework converters | **Done 2026-11-06**: `mm9r_common/quest_xp.py`, every rework award routed through it, `quest_xp_audit.json` (58 of 59 entries paid; Forad Darre's death not carried). In the game at the next conversion. | 3.1: the rework scripts in the world paid MM9's original amounts. |

**Acts** (the user, 2026-11-07; they replace the five-chapter draft from the inventory's level ranges, in which the clans
act was cut into two chapters and its Yanmir's Fort, Klusos's House, Dungeon of Secrets, Verhoffin Ruins, Lich Lab and
Training Hall were treated as late game). `mm9_density_targets.CHAPTER_MAPS` holds them; the balance report measures
each act against MM7's stages of it (`fit_check.ACT_OF_STAGE`).

| Act | Story | Maps | MM7 equivalent |
| --- | --- | --- | --- |
| 1 | The prologue: off the Isle of Ashes, Sturmford and Anskram Keep (Bjarni's and Sigmund's first tasks) | Isle of Ashes, Sturmford, Sturmford City, Beethoven, Anskram Keep | Emerald Island, Harmondale (stage 1) |
| 2 | Uniting the clans, in any order: the six Jarls' twelve mainline quests, both promotions, the side quests on the way | Drangheim and its prison and city, Guberland and its city, Thjorad Mine, Ta'Sar Academy, Thjorgard and its city, Thronheim and its city, Frosgard and its city, Mountain Pass, Lindisfarne and its monastery, Chasm of the Dead, Ruined Temple, Inventastorca, the Arena, Dook's Castle, Yanmir's Fort (Tryggva), Klusos's House (Assassin), Dungeon of Secrets (Ranger), Verhoffin Ruins (Mage; the Capstone later), Lich Lab (Lich), Training Hall | Erathia, Tularean Forest, Deyja, Bracada, Tatalia, Avlee (stages 2–3) |
| 3 | The war: the war council, Connecting Tunnels to Yorwick, the Wyrdes and the Capstone, Arslegard's gate | Yorwick, Wizard's Lab, Connecting Tunnels, Dark Passageway, Bathhouse, Great Gate | Nighon, Eeofol, Shoals (stage 4) |
| 4 | The finale | Temple of Honk, 1000 Terrors, Arslegard, Dragon Stadium, Hall of the Gods, the Afterworld | Land of the Giants, the Lincoln, Titans' Stronghold (stage 5) |

The Jarls' quests: Bjarni (Anskram Keep, Drangheim Prison), Sigmund (Anskram Keep's defences, Chasm of the Dead),
Markel (Ta'Sar Academy, Ivan's trivia in Guberland), Sven (Thjorad Mine, Lindisfarne Monastery), Tryggva (Frosgard's
docks, Yanmir's Fort), Kira (Thronheim's Honks, the Mountain Pass). Quest XP keeps the audit's per-award amounts
(QUEST_XP_AUDIT.md, by its five chapters); the report sums them by act, both promotion tiers in act 2.

Bootcamp is the tutorial and has no act. Verhoffin Ruins is reached from the Isle of Ashes and is first visited for the Mage promotion (act 2).

## 7. Background: where MM9 stood (measured 2026-11-05 and 2026-11-06)

### 7.1 Monsters per level (non-NPC rows, medians)

| Level | MM6–8 HP / AC / dmg per hit / XP | MM9 HP / AC / dmg per hit / XP |
| --- | --- | --- |
| 1–5 | 6 / 5 / 3.0 / 24 | 4 / 3 / 3.0 / 17 |
| 6–10 | 30 / 8 / 8.0 / 144 | 34 / 10 / 9.0 / 216 |
| 11–15 | 55 / 14 / 11.5 / 299 | 72 / 14 / 12.0 / 504 |
| 16–20 | 86 / 15 / 16.5 / 504 | 120 / 17 / 15.0 / 900 |
| 21–30 | 153 / 20 / 22.0 / 999 | 169 / 22 / 22.5 / 1,313 |
| 31–40 | 247 / 30 / 30.5 / 1,739 | 289 / 30 / 30.0 / 2,363 |
| 41–55 | 400 / 35 / 38.5 / 3,000 | 525 / 35 / 35.0 / 4,500 |
| 56–80 | 700 / 50 / 50.0 / 5,600 | 945 / 60 / 44.0 / 8,400 |
| 81+ | 1,244 / 90 / 72.0 / 10,488 | 1,800 / 100 / 87.0 / 16,500 |

Damage per hit and AC are at parity; HP is 10–45% higher and XP about 50% higher. The monster hit roll
(`GameMechanics::monsterAttackHitsArmorClass`) depends only on monster level, attack bonus and party AC. Before the
recovery change, MM9's fixed 59 ticks gave low-level MM9 monsters 1.3–1.7× MM7's damage per second:

| Level | MM6–8 recovery (ticks) | MM9 recovery | MM9 ÷ MM6–8 damage per second | Ranged share MM6–8 / MM9 |
| --- | --- | --- | --- | --- |
| 1–5 | 100 | 59 | 1.69 | 1% / 29% |
| 6–10 | 90 | 59 | 1.34 | 14% / 64% |
| 11–15 | 90 | 59 | 1.27 | 25% / 64% |
| 16–20 | 90 | 59 | 1.17 | 25% / 39% |
| 21–30 | 80 | 59 | 1.12 | 43% / 53% |
| 31–40 | 80 | 59 | 1.04 | 41% / 40% |
| 41–55 | 70 | 59 | 1.07 | 45% / 28% |
| 56–80 | 70 | 59 | 0.97 | 34% / 45% |

MM9 casters cast 50–100% of the time; MM6–MM8's mostly 20–30%. MM9 has no on-hit conditions (about 37% of MM6–MM8 rows
carry one). MM9 monsters emitted no gold, and item drops were a flat 25%.

One MM9 monster is worth this many MM7 monsters of its level in threat (HP × damage per second, after the recovery
change, `balance_prototypes/threat.py`): 0.67 at levels 1–5, 1.3–1.4 at 6–20, 1.1–1.15 at 21–80, about 1.6 above.

### 7.2 Party power: MM6–MM8 rules against original MM9

From `SPELL.txt` descriptions, `MM9_AI_NATIVE_RE.md` and `reference/openmm9/docs/mm9_combat_formula_re_findings.md`:
mastery thresholds are the same (rank 4/7/10). Per cast, single target, OpenYAMM ≈ 1.2–1.5× MM9; area spells well over
2×; melee ≈ 1.0–1.3×. Original MM9 also had four characters. MM9's monster counts were tuned for that weaker party.

### 7.3 Density

Measured on the rebuilt MM9 dungeons in `output/mm9_rework/` (native BLV, placed actors) and every MM6–MM8 map (spawn
points at the mean of the map-stats range, plus placed actors). Packs are monsters within 1,200 units of each other.

| Dungeons (medians) | Floor (M units²) | Monsters | Per 1M units² | Packs | Pack size | Pack spacing |
| --- | --- | --- | --- | --- | --- | --- |
| MM6 | 50 | 152 | 2.5 | 16 | 8.8 | 2,090 |
| MM7 | 38 | 39 | 1.1 | 9 | 3.4 | 1,860 |
| MM8 | 24 | 36 | 1.6 | 7 | 4.5 | 1,860 |
| MM9 | 134 | 43 | 0.34 | 24 | 2.1 | 1,790 |

| Outdoors (medians) | Monsters | Packs | Pack size | Pack spacing |
| --- | --- | --- | --- | --- |
| MM6 | 202 | 45 | 4.5 | 2,830 |
| MM7 | 108 | 45 | 2.5 | 1,910 |
| MM8 | 148 | 64 | 2.4 | 2,130 |
| MM9 | 45 | 28 | 1.8 | 2,740 |

### 7.4 Campaign totals and levelling

| | MM7 | MM9 before this plan |
| --- | --- | --- |
| Maps | 81 (15 small barrows) | 45 (8 monster-free cities) |
| Monsters, monster XP | ~4,100, ~5.0M | ~1,880, ~3.1M |
| Quest XP per member | ~1.7M (one Light/Dark branch, promotions with honorary shares) | ~4.3M in the original scripts (QUEST_XP_AUDIT.md); ~2.0M converted, and only the active member got it |
| Quest gold | ~0.4–0.5M (one branch) | ~0.24M |

Both worlds use the same level curve: 1000 × L × (L+1) / 2 from level L to L+1 (`ExperienceRules`; OpenMM9's
`originalExperienceThresholdForLevel`). Kill XP is split over the members; quest XP goes to each member. With the
original amounts, quests alone would carry the party to about level 98, far above MM9's monsters from chapter 3.

### 7.5 Items

- Ordinary MM9 weapons kept the same dice at every quality and no flat bonus: by tier 5 they hit like MM6–MM8 tier 1–2.
  Original MM9 added a material/quality bonus (tables `0x100D4E7C`/`0x100D4E40` in cshell.dll, values not recovered);
  the import dropped it.
- Ordinary armour was flat across qualities: ahead of MM6–MM8 at tiers 1–2, behind from tier 5.
- Prices already follow the MM6–MM8 tier envelopes. MM9 shop enchants are mostly +2 (421 of 608).
- Artifact weapons: median 12.5 average damage with +0 against MM6–MM8's 22.5 with +15–19. Artifact armour AC far above
  MM6–MM8 (Swordsbane 93, Arrowfoe 64, Laet'ax 31). Regeneration 0.2 HP/s against 1.0. Several relics are drawbacks
  only.

The measurement scripts are in [balance_prototypes/](balance_prototypes/README.md).
