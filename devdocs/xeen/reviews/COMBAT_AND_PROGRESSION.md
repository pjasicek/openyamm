# Xeen review: combat and progression

Review, 2026-11-13. Checks the Xeen plan (`MONSTERS_AND_ITEMS.md`, `MAPS.md`, `QUESTS.md`, `WORLD_DESIGN.md`,
`research/XEEN_SYSTEMS.md` §5) and the six built maps (X1, XD-01 to XD-05 in `output/studio_play/xeen_root`, world mm7,
MM7 stand-in monsters) against the progression curve MM6–MM8 ship. Nothing in the plan or the maps was changed.

Scripts and their outputs are in `output/xeen_review/combat/`: `shipped.py` / `shipped_in.py` (MM6–MM8 kill XP per
map), `xeen_built.py` / `xeen_spawns.py` (the built maps), `plan_xp.py` (the plan's XP as written), `proposed.py` (the
table in §5). Measured numbers come from `assets_dev/engine/data_tables/` (`monster_data.txt`, `map_stats.txt`,
`house_data.txt`, `house_rules.txt`), the engine code named below and `research/MM678_CALIBRATION.md` (monster counts
per map). Where a number is an estimate the method is stated.

## 1. The shipped curve (MM6–MM8 in OpenYAMM)

### 1.1 The arithmetic everything hangs on

- **Levels.** Reaching level L takes `1000 × L(L−1)/2` experience per member (`ExperienceRules::experienceForNextLevel`):
  L2 1,000 · L5 10,000 · L7 21,000 · L10 45,000 · L15 105,000 · L20 190,000 · L30 435,000 · L40 780,000 ·
  L50 1,225,000 · L60 1,770,000 · L75 2,775,000. Each level costs 1,000 × the current level.
- **Kill XP is split** over the eligible members (`Party::grantSharedExperience`); **quest XP goes to every member**
  (MM7 `ForPlayer(All)`; MM9 does the same since BALANCE_PLAN §3.1). With four members a kill is worth a quarter of
  its XP column to each.
- **Monster rows.** Almost every row follows HP = L²/10 + 3L and XP = L(L+10) (checked: L18 → 86 HP, 504 XP). Per-level
  medians of HP / AC / damage per hit / XP: L1–5 6/5/3/24, L6–10 30/8/8/144, L11–15 55/14/11.5/299, L16–20
  86/15/16.5/504, L21–30 153/20/22/999, L31–40 247/30/30.5/1,739, L41–55 400/35/38.5/3,000, L56–80 700/50/50/5,600,
  L81+ 1,244/90/72/10,488 (BALANCE_PLAN §7.1). **The highest level of any shipped row is 125** (Ruby Dragon, 1,937 HP);
  MM6's Mega-Dragon is 100.
- **Spawn tiers.** A group spawn takes A/B/C by the slot's Dif: d1 90/8/2, d2 70/20/10, d3 50/30/20, d4 30/40/30,
  d5 10/50/40 (`EncounterDifficultyTierWeights`). Shipped families keep C within about 2–3× of A (Goblin 4/6/10,
  Skeleton 6/10/14, Spider 5/8/12, Dwarf 10/20/30, Rat 2/4/6), so a d1 slot never surprises the party by more than a
  few levels.
- **Training** costs `level × hall multiplier × class tier` gold (tier 1 base, 2 first promotion, 3 second;
  `PriceCalculator::trainingPrice`), up to the hall's cap (`house_rules.txt`, "Training halls"):

  | World | Hall: cap (multiplier) |
  | --- | --- |
  | MM7 | Emerald Island 5 (×10) · Harmondale 15 (×20) · Erathia 25 (×25) · Tularean Forest 25 (×25) · Tatalia 50 (×40) · Avlee 50 (×80) · Stone City 100 (×40) · Celeste, The Pit 200 (×30) · Mount Nighon unlimited (×50) |
  | MM8 | Dagger Wound 5 (×10) · Ravenshore 15 (×20) · Alvar 25 (×25) · Garrote Gorge 25 (×25) · Shadowspire 200 (×30) · Balthazar Lair unlimited (×30) |
  | MM6 | New Sorpigal 15 (×10) · Bootleg Bay 20 (×20) · Misty Islands 30 (×15) · Silver Cove 40 (×25) · Frozen Highlands 50 (×25) · Free Haven 60 (×30) · Kriegspire 80 (×30) · Blackshire 100 (×40) · Castle Ironfist 200 (×30) · Paradise Valley unlimited (×50) |

  The caps are the real level gates: 5 at the start island, 15 at the hub, 25 in the second ring, 50–100 mid-world,
  unlimited only behind the endgame gate. Training to L20 at these halls costs about 4,000 per member, to L50 about
  50,000 per member (tier 1; double or triple after promotion).
- **New game:** four members at level 1 and 200 gold (`GameApplication`, `seed.gold = 200`), class starting skills and
  basic weapons.

### 1.2 Stages

Kill XP per member is a full clear of the map's first visit (count from MM678_CALIBRATION × the expected XP of its
families at their Dif), divided by four. Party levels are what that plus the stage's quests buy; MM7 as played leaves
about half the outdoor monsters alive (BALANCE_PLAN §3.3), so real parties sit a level or two below a full clear.

| Stage | MM7 | MM8 | MM6 | Monster A–C | Tres | Kill XP per member | Party level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Start pocket | Emerald Island (66 mons) + Temple of the Moon (62) | Dagger Wound (168) + Abandoned Temple (116) | New Sorpigal (219) + Goblinwatch | 1–15, mean 2–5 | 0 | MM7 0.5k + 0.8k, MM8 2.2k + 2.1k, MM6 2.6k | 1 → 3–5 (mostly quest XP; MM7's island is almost all quests) |
| Hub | Harmondale (288) + Castle Harmondale (164), White Cliff, Erathian Sewers | Ravenshore (261) + Smuggler's Cove, Dire Wolf Den | Castle Ironfist (410), Misty Isles | 4–24, mean 10–12 | 0–1 | MM7 18k + 2–6k, MM8 18k + 5k | 4 → 10–12; hall cap 15 |
| Second ring | Erathia, Tularean, Barrow Downs (80–130 each) | Alvar, Shadowspire | Mire, Bootleg Bay, Free Haven | 8–35, mean 11–16 | 1–2 | 8–18k per map, dungeons 1–6k | 10 → 18–22; caps 25 |
| Mid plateau | Deyja, Bracada, Tatalia, Avlee; Stone City, Tidewater, Gloaming, The Pit | Ironsand, Murmurwoods, Ravage Roaming, Garrote, Regna | Frozen Highlands, Silver Cove, Blackshire, Kriegspire | 12–50, mean 13–30 | 2–4 | 10–50k per map, dungeons 3–30k | 20 → 35–40; caps 50–100 |
| Late | Mount Nighon (172), Thunderfist, The Maze, Eeofol tunnels, Lambent/Gloaming | Planes of Air/Fire/Water (136–216), Castles of Air/Fire | Dragonsand, Sweet Water, the Hive | 25–90, mean 37–55 | 3–5 | 50–190k per map | 40 → 50–55 |
| Endgame / trap | Land of the Giants (132, L65–100), Titans' Stronghold, Lincoln | Plane Between Planes (224), Escaton's Palace, Prisons of the Lords | Paradise Valley, Hermit's Isle, Dragonsand | 40–125, mean 60–80 | 5–6 | 100–300k per map | 50 → 55–65 |

Whole campaign (BALANCE_PLAN §7.4): MM7 about 4,100 monsters and **5.0M party kill XP (1.25M per member)**, quest XP
about **1.7M per member** on one Light/Dark branch, quest gold 0.4–0.5M and campaign gold about 0.85M as played. A full
clear plus all quests reaches the high 70s; real parties finish around 55–65.

**Ratios the three games keep:**
- In a map the party must clear, **A-tier ≈ party level and C-tier ≤ about 2× party level**. Bosses sit at 2–3×.
- Trap maps (Dragonsand, Eel-Infested Waters, Garrote Gorge, Land of the Giants) break that on purpose, are visible
  from a safe map and are never on the main path at the level they first appear.
- Outdoor groups 2.4–2.5 (MM7/MM8 median; MM6 4.5), dungeon groups 3.4–4.5 (BALANCE_PLAN §7.3).
- Treasure follows the stage, not the level-for-level XP. Shipped drop levels by monster level (median level of the
  rows that drop it): **item L1 ≈ 10, L2 ≈ 18, L3 ≈ 29, L4 ≈ 39, L5 ≈ 60, L6 ≈ 80**. Map Tres runs 0 → 1 → 2 → 3–4 → 5–6
  with Lock/Trap 0/1 → 4/2 → 8/4 → 10/5 → 20/10.

### 1.3 Fights per level

Kills alone, four members, monsters a few levels above the party (quests roughly halve these):

| Party level | XP to next (per member) | Typical monster | Its XP per member | Kills to level | Packs of 3 |
| --- | --- | --- | --- | --- | --- |
| 3 | 3,000 | L4 (56) | 14 | ~210 | ~70 |
| 8 | 8,000 | L10 (200) | 50 | ~160 | ~55 |
| 15 | 15,000 | L18 (504) | 126 | ~120 | ~40 |
| 25 | 25,000 | L30 (1,200) | 300 | ~85 | ~28 |
| 40 | 40,000 | L50 (3,000) | 750 | ~55 | ~18 |
| 55 | 55,000 | L70 (5,600) | 1,400 | ~40 | ~13 |

Early levels come from quests (an MM7 Emerald Island quest pays 250–1,500 per member); from the hub on, one outdoor map
plus its dungeons is worth one to two levels by kills; late, one dungeon is a level.

### 1.4 The first hour

Level 1, four members, 200 gold, starting weapons. MM7: Emerald Island's 66 dragonflies (L2–8, 24–144 XP, 2D2–4D2+2)
and the Temple of the Moon's rats, bats and spiders pay about 1,300 per member in kills; the scavenger hunt and small
island quests carry the party to L3–5 before the boat to Harmondale (hall cap 5). MM8 Dagger Wound: 168 lizardmen,
pirates and couatls (L1–15), about 4,300 per member with the Abandoned Temple, then Ravenshore (cap 5 → 15). The first
level comes within the first 20–40 minutes, mostly from a quest; damage taken per hit is 2–8.

## 2. The Xeen plan against the curve

### 2.1 What the plan says

Act bands (QUESTS §1): I 1–10, II 10–20, III 14–30 (parallel), IV 28–42, V 40–55, VI 55–75. The conversion rule
(MONSTERS_AND_ITEMS §1) is right: it uses the shipped HP and XP formulas and the §7.1 medians, and drops every Xeen
number. Density (§3) at MM7/MM8 medians, about 4,700 monsters. Treasure: MM9's stage table on monster level plus
"chests one step above".

### 2.2 What the plan's numbers produce

`plan_xp.py` takes each map's band from MAPS.md (typical monster = A + 0.3 × (C − A), the d1–d2 mix), the density
targets (ODM 135, sky 80, plane 55, dungeon S 28 / M 50 / L 95) and XP = L(L+10):

| Act | Monsters | Party kill XP | Level after the act, kills only (full clear) | With MM7's quest share |
| --- | --- | --- | --- | --- |
| I | 319 | 30k | 4 | 6 |
| II | 925 | 509k | 16 | ~25 |
| III | 1,098 | 764k | 26 | ~39 |
| IV | 838 | 1.58M | 38 | ~59 |
| V | 1,004 | 3.83M | 58 | ~89 |
| VI | 484 | 2.76M | 69 | ~105 |
| Optional | 195 | 1.61M | 74 | ~115 |
| **All** | **4,863** | **11.1M (2.2× MM7)** | | |

The plan's first half is on the curve; from Act IV it runs away. The reason is the late bands: XP grows with L², and
Acts V–VI put most monsters at 60–100, with the Darkside's dragons at 80–150. Two endgames (Cloudside's X7, Castle
Xeen and Dragon Cave; Darkside's D5–D7, planes and five finale dungeons) each sit at the level of MM7's single one.

### 2.3 The built maps

From the scenes and map_stats rows 9130–9135 (stand-ins are MM7 rows; the final Xeen monsters will replace them):

| Map | Placed hostile | Spawns (slot, Dif, count) | Est. monsters | Levels met | Party kill XP | Chests: item levels, gold | map Tres, L/T |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X1 | 15 Goblins (L4); townsfolk and 4 town Guards (L17) | 43: Goblin d1 3–5 ×24, Dragonfly d1 2–4 ×10, Skeleton d1 2–5 ×9 | ~173 | 2–14 | ~11k | 6 chests × 3 random L1 items | 1, 0/1 |
| XD-01 | 8 Giant Rats (2), 2 Fire Rats (6) as the Wobbles | 9: Rat d1, Dragonfly d1, 2–3 each | ~32 | 2–6 | ~1.0k | L1, L0, L1, L2, L0; 402 gold | 1, 0/1 |
| XD-02 | 3 Dwarven Soldiers (10), **Lieutenant (20)**, 3 Venomous Spiders (8), 4 Troglodyte Drones (9) | 23: Dwarf d1, Spider d2 (some tier A), Bat d1 | ~71 | 3–20 | ~10.7k | L2, L1, L1, L1, **L3**, L2; 590 gold | 2, 1/1 |
| XD-03 | 15 Dwarven Soldiers (10), **Dwarven Commander (30)** as the Clan King, 2 Inferno Bats (9) | 10: Dwarf d1, Spider d3, Troglodyte d1 | ~40 | 8–30 | ~8.8k | **L3, L4, L4**, L2, L3; 1,110 gold | 3, 2/1 |
| XD-04 | 3 Acolytes (10), **Cleric of the Moon (20)** as the Head Witch, Goblin Lord (10), 2 Inferno Bats (9), 4 caged children | 21: Goblin d2 (tiers fixed a/b/c), Cleric Moon d1, Bat d3 | ~55 | 4–20 | ~6.1k | L3, L1, L2, L2 (+ fixed items); 460 gold | 2, 2/2 |
| XD-05 | 4 Goblin Lords (10) as Drum-Master and guards | 15: Goblin d2, Bat d1, Spider d1 | ~41 | 3–10 | ~3.3k | L2, L1, L1, L2; 400 gold | 1, 1/1 |

Act I as built: **about 41k party kill XP, 10.3k per member: level 5 by kills**, L7–8 with Act I's quests. That is
on the MM7/MM8 curve (MM8's Dagger Wound plus Abandoned Temple: 4.3k per member; MM7's start plus Harmondale: about
21k). The weight is uneven: XD-02 and XD-03 carry 47 % of it because the MM7 Dwarf family starts at level 10 (the plan's
Mad Dwarf is 7).

## 3. Findings, ranked

1. **The late game runs about two times too rich, and Act V–VI party levels would end near 90+, not 55–75.** The plan's
   monsters give 11.1M party kill XP against MM7's 5.0M (§2.2); with quests at even half MM7's 1.7M per member, a
   party finishing Act V is level 70–80 and ends near 100. Monster level and treasure then outrun MM6–MM8 too. Cause:
   Acts V–VII hold 1,680 monsters at typical levels 55–90, twice MM7's late content. Fix: cap ordinary families at
   about 90 and named bosses at 110–125 (the shipped maximum is 125), cut late dungeons to S/M size, and make the
   planes 30 monsters each. The table in §5 gives 6.3M party kill XP and a level-65 finish as played.
2. **Ten families span far more than MM6–MM8's 2–3×, so a slot's d1 roll can drop a monster three to nine times the map's
   level, and a late map gets early monsters.** Serpents 5/35/45, Swarms 2/12/20, Rats 5/12/35, Bats 3/10/20, Swamp
   things 11/26/60, Burrowers 9/38/45, Orcs 7/12/25, Witches 14/32/50, Barbarians 12/30/38, Rotting dead 10/18/30. On X1
   a serpent slot at d1 rolls a level-45 Killer Cobra 2 % of the time; on D3 the same family yields level-5 snakes.
   The rule's own "1.5–2.5× from A to C" is broken by these rows. Split each into two or three families, one per
   stage (§6.1).
3. **Several map sheets name monsters above their own band, so the maps would play harder than the sheets say,
   most of all at the Cloudside hub.** X2 (sheet A 6–10, C 24): its families are Killer sprites 12–20, Archers 20–36
   and Ogres 18–30, so the hub plays at 12–36, like MM7's Bracada for a party that has just left the start pocket. X3:
   swamp things reach 60. X4: knights 24–40 and gargoyles 22–40 against a sheet A of 10–16. D3: mantis ants 38,
   killer cobras 45, hell hornets 45 and armadillos 45 are all C-tier or boss rows; as slot monsters D3 would play at
   38–45, not 20–28. D4: vulture rocs 58, octopods 60 (sheet A 28–35). The opposite on X1 and D1: X1's sheet says A 2–4,
   but orcs are 7 and toads 11; D1's sheet says A 12–18, but its goblins and gremlins are the Cloudside 4/6/10 family,
   which would make the Darkside hub a level-4 map for a level-15 party.
4. **Act II's mandatory Megacredit dungeons spike.** M10 needs the Temple of Yak (Yak Master 50, ×2–4 HP), the Tomb
   (18–40) and the Golem Dungeon (24–52, Diamond Golem 70) for a party of level 10–20. In MM6–MM8 terms, mandatory bosses
   at 3–4× party level, and a dungeon whose A-tier (24) is above the party. Bring them to 14–28 / 35, 15–30 and
   18–40 / 50, or make one of the three sources optional (the plan's "keep 3 sources, 15 needed" does not say whether all
   three are needed).
5. **Act IV's story dungeons sit at endgame levels.** Lost Souls (M24, 45–65, minotaurs 58/65/78) and Castle Blackfang
   (M27, 48–75, Count 90) for a party of 28–42: A-tier 1.5× the party, the Count 2–3×. MM7's mid-game story dungeons
   have A ≈ party level (Castle Gloaming and The Pit 20–50 for a level-30 party). Lower to 35–55 and 36–58 / Count 70.
   Act V likewise: Great Pyramid 60–88, Alamar 70–90, Castle Xeen 55–90 / Lord Xeen 110 for a party of 40–55.
6. **The treasure rule is one step richer than MM6–MM8 at every boundary, two steps with "chests one step above".**
   The plan uses MM9's compressed stage table (1–7 → 1, 8–15 → 2, 16–30 → 3, 31–44 → 4, 45–64 → 5, 65+ → 6), made for
   MM9's last chapter at 30–79. Xeen uses MM6–MM8 levels, where L5 drops start near 60 and L6 near 80. As built, the
   Deep Mine gives two level-4 and two level-3 chests to a level 5–6 party, and the Red Dwarf Mines a level-3 chest to a
   level 3–4 party; MM7's first-ring dungeons are Tres 0–1. Use 1–12 → 1, 13–22 → 2, 23–34 → 3, 35–49 → 4, 50–74 → 5,
   75+ → 6, chests at the map's level, one boss hoard per dungeon one step up.
7. **Act I cannot end at level 10.** As built and as planned, Act I's kills give level 4–5; level 10 (45,000 per member)
   would need about 35,000 per member from Act I's four main quests and four side quests. MM7 and MM8 reach 10 only
   after the hub. Make Act I 1–7; Act II 7–20 then matches the hub and second ring.
8. **Bosses cannot carry their hit points yet.** Placed actors' `hp` is ignored (XD-01 notes; XD-03 Clan King `hp: 300`
   on a 180-HP row, XD-04 Head Witch 300 on 100, XD-05 Drum-Master on 40). The rule's "Bosses ×2–4 HP" needs one
   monster_data row per boss (as MM6–MM8 do: Goblin King, Lord Markham's guards), not a scene override.
9. **Built-map spikes for the stand-ins.** XD-02's placed Dwarven Lieutenant (L20, 100 HP, 4D2+8) and XD-03's Dwarven
   Commander (L30, 180 HP, 4D2+16, about 21 per blow) face a level 3–6 party: 4–6× party level, above MM6–MM8's
   early-boss ratio. The Commander alone pays 1,200 XP, 14 % of the dungeon. The XD-01 Fire Rats (L6, 1D8+6) as the
   Wobbles are 3× a level-2 party, sharp for a first dungeon but MM-like. Fine as stand-ins; the Xeen rows should land
   at the plan's 4 / 18 / 14 or §5's.
10. **The Newcastle deed (M8, 50,000 gold) is about 60 % of the gold a party has earned by the end of Act II** (kill
    gold at MM7's 80–110 per 1,000 XP plus the act's quest gold, about 80k by level 20, less training and teachers).
    MM6–MM8 never ask that of a level 10–15 party. Make it 10,000–15,000, or let the deed be paid off over the
    Megacredit steps.
11. **No training caps are planned.** WORLD_DESIGN lists training at Vertigo, Rivercity, Castle Burlock, Newcastle,
    Castleview, Kalindra, Sandcaster and Olympus without caps or multipliers. Caps are how MM6–MM8 gate level; §5.2
    proposes them.
12. **Bolster rows are missing.** XEEN_SYSTEMS §5 asks for `LowerToEqual` rows; xeen_root's `bolster_maps.txt` has X1
    with kind 0 and no rows for XD-01..05.
13. **Smaller points.** The Crusader promotion (T1-A, 16,500 XP each) at the end of Act I is worth one and a half levels
    at level 7, and two and a half at the plan's quest cap; acceptable but it should be counted in Act I's quest
    budget. X1 as built (about 173 hostiles, goblin packs 3–5) is MM8-dense rather than MM7-sparse; fine for a start
    pocket that also sends the party into five dungeons. The X2 lake's three level-60 water dragons are a correct trap.
    DD-01 (5–15) and DD-04 (6–15) are too low for a party arriving at 15–18; raise to 10–20 and 12–20.

## 4. Where the plan plays harder or easier than MM6–MM8

| Part | Plan as written | Compared with MM6–MM8 |
| --- | --- | --- |
| X1 and XD-01..05 | levels 2–18, ~320 monsters | On the curve (as built: slightly rich in XP and items) |
| X2 hub | families 12–36 | **Harder**: the hub plays like MM7's mid plateau |
| X3, X4 | families to 40–60 | Harder than the sheets: swamp things, knights, gargoyles |
| Act II dungeons | Yak 50, Golem 52/70 | **Spike**: bosses 3–4× party level on the main path |
| D1 Darkside hub | gremlins at 4/6/10 | **Easier**: a level-4 map for a level-15 party |
| D2, X5 | 16–40 | On the curve |
| D3, D4 | named monsters 38–60 | Harder than the sheets |
| Act IV story dungeons | Lost Souls 45–65, Blackfang 48–75 / 90 | **Spike** for a 28–42 party |
| Act V | Pyramid 60–88, Alamar 70–90, Castle Xeen 55–90 / 110 | Harder, then the XP overshoot makes Act VI easier |
| Act VI, optional | planes, FD 80–110, Megadragon 150 | Above any shipped row; overshoots the level curve by 20–30 levels |
| Treasure | MM9 table + one step | **Richer** by one to two item levels throughout |

## 5. Proposed curve

### 5.1 Per-map table

Party levels are a full clear (kills at the counts and bands below, plus the quest budget per act); a party that
skips half the outdoor monsters is one to three levels lower. Monster bands are A-tier to C-tier, boss after the
comma. "Kill XP" is per member, full clear. Tres is map_stats on MM7's scale; chests at the map's treasure level, one
boss hoard per dungeon one step up.

| Map | Act | Party arrive → leave | Monsters A–C, boss | Groups | Tres | Monsters | Kill XP per member |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X1 Vertigo Meadows | I | 1 → 4 | 2–12 | 2–4 (orcs 3–5) | 1 | 130 | 2.4k |
| XD-01 Joe's Warehouse | I | 1 → 3 | 2–6, Wobbles 4 (boss row) | 2–3 | 1 | 28 | 0.3k |
| XD-02 Red Dwarf Mines | I | 3 → 5 | 3–10 | 2–3 | 1 | 55 | 1.1k |
| XD-05 Orc Caves | I | 3 → 5 | 4–10, Drum-Master 12 | 2–3 | 1 | 30 | 0.7k |
| XD-03 Deep Mine | I | 5 → 6 | 6–12, Clan King 18 | 2–3 | 1 (hoard 2) | 28 | 1.0k |
| XD-04 Witch Tower | I | 5 → 7 | 4–14, Head Witch 20 | 2–3 | 1 (hoard 2) | 50 | 1.5k |
| X2 Rivercity | II | 7 → 11 | 6–24 (lake dragons 60, trap) | 2–4 | 1 | 135 | 8.2k |
| XD-21 Robbers' Den | II | 9 → 11 | 10–18 | 2–3 | 2 | 28 | 1.9k |
| XD-27 Ogre Lair | II | 10 → 12 | 12–20 | 2–3 | 2 | 28 | 2.5k |
| X4 Burlock Savannah | II | 11 → 15 | 10–30 | 2–4 | 2 | 135 | 14.0k |
| XD-07 Castle Burlock | II | 12 → 14 | 10–24 (caged fire dragon optional) | 2–3 | 2 | 50 | 4.3k |
| X3 Lifeforce Lagoon | II | 13 → 16 | 10–30 | 2–4 | 2 | 135 | 14.0k |
| XD-06 Temple of Yak | II | 14 → 16 | 14–28, Yak Master 35 | 2–3 | 2 | 50 | 6.4k |
| XD-08 Tomb of 1000 Terrors | II | 15 → 17 | 15–30 | 2–3 | 2 | 50 | 7.2k |
| XD-09 Golem Dungeon | II | 16 → 18 | 18–40, Diamond Golem 50 | 1–2 | 3 | 45 | 9.6k |
| XD-10 Cave of Illusion | II | 17 → 19 | 18–28 | 2–3 | 3 | 50 | 8.1k |
| XD-11 Tower of High Magic | II | 18 → 20 | 18–32 | 2–3 | 3 | 50 | 8.9k |
| X8 Cloudreach (sky) | II | 18 → 20 | 14–30 (cloud golem 50 rare) | 2–3 | 3 | 60 | 8.1k |
| D1 Castleview Vale | III | 18 → 21 | 14–30 | 2–4 | 2 | 135 | 18.3k |
| DD-01 Castleview Sewer | III | 18 → 20 | 10–20 | 3–4 | 2 | 50 | 3.7k |
| DD-04 Gremlin Court | III | 19 → 20 | 12–20, Gettlewaithe 24 | 2–4 | 2 | 28 | 2.5k |
| DD-02 Ellinger's Tower | III | 20 → 22 | 14–24 | 2–3 | 2 | 50 | 5.7k |
| D2 Sprite Forest | III | 21 → 25 | 16–38 | 2–4 | 3 | 135 | 24.9k |
| DD-06, DD-09, DD-13 | III | 22 → 26 | 14–32 (Barkman 60 optional) | 2–3 | 3 | 120 | 17.1k |
| DD-10, DD-11 (6 pockets) | III | 23 → 27 | 16–38, Hobstadt 42 | 2–3 | 3 | 120 | 22.1k |
| X5 Winterkill Tundra | III | 24 → 28 | 16–40 (cyclops corner 36–50, trap) | 2–4 | 3 | 135 | 26.0k |
| XD-22, XD-23, XD-24 | III | 25 → 29 | 18–40, Count Draco 45 | 2–3 | 3 | 84 | 17.9k |
| D3 Sandcaster | III | 27 → 30 | 20–45 | 2–4 | 3 | 135 | 34.8k |
| DD-18 Sandcaster Sewer | III | 28 → 30 | 25–40 | 2–3 | 3 | 50 | 14.6k |
| X6 Desert of the Sphinx | IV | 30 → 33 | 22–50 | 2–4 | 3 | 135 | 41.5k |
| XD-14, XD-15 | IV | 31 → 34 | 22–45 | 2–3 | 4 | 90 | 25.3k |
| DD-03 Castle Kalindra (staged) | IV | 30 → 40 | 28–48 (Scraps 70 optional) | 2–3 | 4 | 55 | 20.6k |
| XD-12 Darzog's Tower | IV | 33 → 36 | 30–48, Darzog 55 | 2–4 | 4 | 80 | 32.1k |
| D4 Lakeside and Blackfang | IV | 35 → 38 | 26–50 (octopods 60, lake trap) | 2–4 | 4 | 120 | 43.0k |
| DD-05, DD-20, DD-23 | IV | 35 → 39 | 24–45 | 2–3 | 4 | 100 | 30.5k |
| DD-12 Dungeon of Lost Souls | IV | 37 → 39 | 35–55 | 2–3 | 4 | 45 | 23.5k |
| DD-14 Castle Blackfang | IV | 39 → 42 | 36–58, Count Blackfang 70 | 2–4 | 4 (hoard 5) | 70 | 39.2k |
| DD-19 Wizard Quarter | IV | 38 → 41 | 32–55, Xenoc 60 | 2–3 | 4 | 50 | 23.8k |
| D5 Desert of Doom | V | 42 → 45 | 32–55 | 2–3 | 5 | 110 | 52.3k |
| DD-15 Great Pyramid | V | 44 → 47 | 42–65 | 2–3 | 5 | 70 | 50.4k |
| DD-16, DD-24 | V | 45 → 47 | 38–58 | 1–3 | 5 | 45 | 26.7k |
| X9 Clouds of Xeen (sky) | V | 46 → 48 | 35–55 | 2–3 | 5 | 50 | 26.1k |
| XD-19 Castle Xeen | V | 47 → 50 | 42–70, Xeen's Pet 75, Lord Xeen 85 | 2–3 | 5 (hoard 6) | 70 | 53.3k |
| D6 The Forbidden Zone | V | 48 → 51 | 38–65 | 2–3 | 5 | 110 | 71.1k |
| DD-07, DD-08, DD-21 | V | 49 → 52 | 40–62, Sandro 65 | 2–3 | 5 | 90 | 59.3k |
| DD-17 Castle Alamar | V | 52 → 55 | 50–75 | 2–3 | 5 (hoard 6) | 70 | 67.9k |
| X7 Mount Firestone (trap map) | V | 40 → 55 | south 6–12 orcs; north 40–85 | 1–3 | 5 | 90 | 76.4k |
| XD-16 Volcano Cave | V | 48 → 52 | 42–58 | 2–3 | 5 | 40 | 26.6k |
| D7 The Skyroads (sky) | VI | 55 → 58 | 50–75 (Megadragon 125, optional) | 1–3 | 6 | 50 | 48.5k |
| P1–P4 planes | VI | 56 → 60 | 55–70, sleepers' guardians 75 | 2–3 | 6 | 4 × 30 | 124.1k |
| FD-01, FD-02 | VI | 58 → 61 | 55–80 | 2–3 | 6 | 60 | 68.0k |
| FD-03 Darkstone Tower | VI | 60 → 63 | 60–85 | 2–3 | 6 | 45 | 58.9k |
| DD-22, DD-26 | VI | 56 → 60 | 48–65 | 2–3 | 6 | 40 | 33.5k |
| XD-18 Dragon Cave (optional) | opt. | 60 → 64 | 65–100, Dragon King 110 | 1–2 | 6 | 40 | 64.6k |
| FD-04, FD-05 (optional) | opt. | 62 → 66 | 65–100 | 1–3 | 6 | 60 | 96.8k |
| XD-20 Warzone | any | — | by tier | — | — | — | — |

Totals: **about 4,080 monsters, 6.3M party kill XP (1.57M per member; MM7 1.25M)**, quest XP about 0.88M per member
(Act I 16.5k, II 83k, III 132k, IV 160k, V 209k, VI 210k, optional 70k; MM7 1.7M, MM9 capped 1.3M). Full clear of the
main path: level 67; with the optional content 70; as played about 62–65. Act ends (full clear): I 7, II 20, III 32,
IV 44, V 58.

### 5.2 Training halls

| Hall | Cap | Multiplier | Shipped analogue |
| --- | --- | --- | --- |
| Vertigo (Thylon's Training) | 10 | ×10 | New Sorpigal 15 / Emerald Island 5 |
| Rivercity (Street Fightin') | 25 | ×20 | Harmondale 15, Erathia 25 |
| Castle Burlock | 40 | ×25 | Silver Cove 40 |
| Castleview | 40 | ×25 | Alvar 25, Frozen Highlands 50 |
| Newcastle (stage 2) | 60 | ×30 | Free Haven 60 |
| Sandcaster | 80 | ×40 | Kriegspire 80 |
| Castle Kalindra (stage 4) | 200 | ×50 | Shadowspire, Celeste 200 |
| Olympus | unlimited | ×80 | Mount Nighon, Paradise Valley |

### 5.3 Quest experience and gold

- Award cap per quest, as MM9's: at most 1.5 levels' worth (1,000 × the act's typical party level × 1.5) in Acts I–II,
  1.0 in III–IV, 0.75 after; the act budgets in §5.1 are the targets.
- Promotions: MM9's 16,500 (tier 1) and 37,500 (tier 2) fit; count them in the act budget.
- Gold: kill gold at MM7's per-XP rates (BALANCE_PLAN §3.3 table, before MM9's ×2.2); quest gold about 0.4M over the
  campaign; the Newcastle deed 10,000–15,000.

## 6. Proposed text changes (not applied)

### 6.1 MONSTERS_AND_ITEMS.md

**§1, Level row**, replace with:

> Level: by role and region (MAPS.md), checked against the MM6–MM8 monster of the same role. **A family spans at most
> 2.5× from A to C and at most 25 levels; a Xeen group whose monsters lie further apart becomes two or three families.**
> On a map that must be cleared, A-tier ≈ the arriving party's level and C-tier ≤ 2× it; bosses 2–3×; trap maps exempt.
> **Ordinary families stop at level 100; named bosses at 125** (MM6–MM8's highest row).

**§1, Behaviour row**, add: "Every boss has its own monster_data row with its HP multiplier and treasure; scene `hp`
is not read."

**§2, family table**, replace these rows:

| Family | A / B / C (levels) | Where |
| --- | --- | --- |
| Orcs | Orc 5 / Orc Archer 7 / Orc Guard 10 | X1, Orc Caves |
| Orc warband | Orc Elite 16 / Orc Shaman 20 / Orc Captain 26; Shaalth 30 | Temple of Bark |
| Goblins (Cloudside) | Goblin 4 / Gremlin 6 / Gremlin Guard 10 | Witch Tower, X1 |
| Gremlins (Darkside) | Gremlin 14 / Gremlin Saboteur 18 / Gremlin Guard 22; Gettlewaithe 24 | D1, Gremlin Court |
| Barbarians | Barbarian 14 / Sardaj Warrior 20 / Barbarian Chief 28; Yog | X5, D1, X6 |
| Witches | Wicked Witch 10 / Witch 14 / Head Witch row 20 | Witch Tower |
| Coven | Witch 32 / Coven Witch 40 / Coven Mother 50 | Lakeside |
| Rotting dead | Zombie 8 / Ghoul 12 / Grave Ghoul 18 (Mummy 30 joins the Pyramid mummies' A tier as Tomb Mummy) | X1, X3, Tomb |
| Bats | Giant Bat 3 / Cave Bat 6 / Mine Bat 9 | Mines |
| Night bats | Bat Queen 10 / Vampire Bat 14 / Beholder Bat 20 | Nightshadow, Ellinger, Gem Mines |
| Swarms | Doom Bug 2 / Insect Swarm 4 / Stingers 6 | Vertigo, Witch Tower |
| Hornets | Hell Hornet 35 / Hornet Swarm 42 / Hornet Queen 50 | D3 Aging Forest |
| Rats | Sewer Rat 3 / Rooka 6 / Sewer Stalker 9 | Vertigo, Castleview sewers |
| Sewer stalkers | Rooka 18 / Sewer Stalker 25 / Stalker Matriarch 35 | Sandcaster, Necropolis sewers |
| Burrowers | Tiger Mole 6 / Rock Mole 9 / Tunnel Mole 12 | Mines |
| Sand burrowers | Sand Worm 30 / Armadillo 38 / Great Worm 45 | X6, D3 |
| Toads | Giant Toad 5 / Bog Toad 8 / Swamp Toad 11 | X1 Toad Meadow, X3 |
| Swamp things | Swamp Thing 20 / Bog Thing 26 / Marsh Horror 32 | X3 |
| Octopods | Octopod 50 / Great Octopod 60 / Kraken 70 | D4 lake (trap) |
| Serpents | Giant Snake 5 / Viper 8 / Constrictor 12 | X1 |
| Cobras | Guardian Asp 30 / Killer Cobra 38 / King Cobra 45 | Asp, D3 |

and in the existing rows: Minotaurs and gorgons **38 / 45 / 55**, Liches **35 / 50 / 65** (Power Lich 75 and Skeletal
Lich 85 move to the finale as named rows), Darkside dragons **70 / 80 / 90** (Phase Dragon, Energy Dragon and the
**Megadragon 125** as named rows), Lord Xeen **85**, Count Blackfang **70**, Yak Master **35**, Diamond Golem **50**
(Onyx Golem 85), Dragon King **110**.

**§3 Density**, change the whole-world row to: "≈ 4,100 monsters: 13 ODMs × 110–135, 3 sky maps × 50–60, 4 planes ×
30, dungeons ≈ 2,000; late dungeons (Act V on) S or M. Target: party kill XP ≈ 6M (MM7 5.0M), checked with
`output/xeen_review/combat/proposed.py` or its successor after each map sheet change."

**§4.1 Treasure levels**, replace the first sentence with: "Treasure level from monster level on MM6–MM8's own drop
curve: 1–12 → 1, 13–22 → 2, 23–34 → 3, 35–49 → 4, 50–74 → 5, 75+ → 6 (median drop levels of the shipped rows: L1 10,
L2 18, L3 29, L4 39, L5 60, L6 80). Chests at the map's level; one boss hoard per dungeon one step up." Map Tres as in
REVIEW §5.1 (X1 and its dungeons 1, X2 1, X3/X4 2, Act II dungeons 2–3, Act III 2–3, Act IV 3–4, Act V 5, Act VI 6).

**§4.3**, add: "Training halls and caps: Vertigo 10 (×10), Rivercity 25 (×20), Castle Burlock and Castleview 40 (×25),
Newcastle 60 (×30), Sandcaster 80 (×40), Castle Kalindra 200 (×50), Olympus unlimited (×80). Every Xeen map gets a
`LowerToEqual` row in `bolster_maps.txt`."

### 6.2 MAPS.md

Introduction: add "Party levels on arrival and leaving, group sizes, monster counts and the kill-XP budget per map are
in `reviews/COMBAT_AND_PROGRESSION.md` §5; a sheet's monster band must contain its named families' A-to-C levels."

Map sheet Monsters rows:

- **X1**: "A 2–5, C ≤ 12. **Orcs** (5/7/10, d1), **Toads and snakes** (5–12, Toad Meadow), **Skeletons and zombies** (6–18,
  dead forest, d2). Pests only in Joe's warehouse and the town's first quest. Party 1 → 4. Tres 1, L/T 0/1."
- **X2**: "A 6–12, C 24. **Killer sprites** (10/14/18), **Evil rangers** (8/12/18, the north bank camps), **Ogres** (18–30,
  d1, river crossings only). Three named water dragons (60) in the lake: a trap. Party 7 → 11. Tres 1, L/T 2/1."
- **X3**: "A 10–15, C 32. **Swamp things** (20/26/32, d1), **Toads** (5–11, d3 at the edge), **Zombies/ghouls** around the
  Tomb, **Night bats** near Nightshadow. Party 13 → 16. Tres 2."
- **X4**: "A 10–16, C 30. **Burlock knights** at 14/20/26 (Jousters; King's Guard 40 stays inside Castle Burlock),
  **Ogres**, **Gargoyles** (d1, the range). Party 11 → 15. Tres 2."
- **D1**: "A 14–18, C 30. **Gremlins** (Darkside family 14/18/22), **Barbarians** (14–28), **Arachnoids** (a 14/18/24 spider
  row) **and electrapedes** (Dark Grove). Party 18 → 21. Tres 2, L/T 4/2."
- **D3**: "A 20–28, C 45. **Cobras** (30/38/45, d1), **Mantis ants** as the A tier of a 22/30/38 crawler family, **Hell
  hornets** (35–50, the Aging Forest only, d1), **Sand burrowers** (30–45, scrub). Party 27 → 30. Tres 3."
- **D4**: "A 26–35, C 50. **Gargoyles** (Magic Mountain), **Vulture rocs** as the A tier of a 30/38/48 bird family,
  **Octopods** (50–70) in the deep water only: the lake is the trap. Party 35 → 38. Tres 4."
- **D6**: "A 38–50, C 65. **Gamma gazers** (Eyes 40/50/65), **Lava dwellers**, **Griffins**; robot patrols near Alamar.
  Party 48 → 51. Tres 5, L/T 15/8."
- **X7**: "South slopes: orcs 5–12 (the trap map's safe edge). North: A 40–55, C 85. Tres 5, L/T 10/5. Visible from X1 and
  X4; no main-path step before Act V."

Sky maps and planes table: X8 "Harpies 14–24, Flying feet / Guardians 18–24, Cloud golems 50 (rare); 60 placed", X9
"35–55; 50 placed", D7 "50–75, Megadragon 125 (optional); 50 placed", P1–P4 "55–70, guardians 75; 30 each".

Dungeon tables, Monster levels column:

| Code | Now | Proposed |
| --- | --- | --- |
| XD-03 Deep Mine | 8–18 | 6–12, Clan King 18 (boss row) |
| XD-04 Witch Tower | 4–14 | 4–14, Head Witch 20 (boss row) |
| XD-06 Temple of Yak | 16–30 (Yak Master 50) | 14–28 (Yak Master 35) |
| XD-08 Tomb | 18–40 | 15–30 |
| XD-09 Golem Dungeon | 24–52 (Diamond 70) | 18–40 (Diamond 50) |
| XD-12 Darzog's Tower | 35–55 | 30–48, Darzog 55 |
| XD-15 The Sphinx | 30–50 | 28–45 |
| XD-16 Volcano Cave | 50–62 | 42–58 |
| XD-18 Dragon Cave | 75–100 | 65–100, Dragon King 110 |
| XD-19 Castle Xeen | 55–90 (Lord Xeen 110) | 42–70, Xeen's Pet 75, Lord Xeen 85 |
| DD-01 Castleview Sewer | 5–15 | 10–20 |
| DD-03 Castle Kalindra | 30–60 (Scraps 95) | 28–48 (Scraps 70, optional) |
| DD-04 Gremlin Court | 6–15 | 12–20, Gettlewaithe 24 |
| DD-07 Eastern Tower | 45–70 | 40–60 |
| DD-08 Northern Tower | 45–75 | 40–62 |
| DD-12 Lost Souls | 45–65 | 35–55 |
| DD-14 Castle Blackfang | 48–75 (Count 90) | 36–58 (Count 70) |
| DD-15 Great Pyramid | 60–88 | 42–65 |
| DD-16 Corak's Pod | 50–70 | 40–58 |
| DD-17 Castle Alamar | 70–90 | 50–75 |
| DD-19 Wizard Quarter | 36–65 | 32–55, Xenoc 60 |
| FD-01 Alamar Depths | 80–95 | 55–80 |
| FD-02 Southern Sphinx | 70–85 | 55–75 |
| FD-03 Darkstone Tower | 80–100 | 60–85 |
| FD-04 Dragon Tower | 80–100 | 65–95 |
| FD-05 Dungeon of Death | 85–110 | 70–100 |

QUESTS.md (for the owner of that file): act bands I 1–7, II 7–20, III 18–30, IV 30–42, V 42–55, VI 55–65 (optional
content to 70); M8's deed 10,000–15,000.
