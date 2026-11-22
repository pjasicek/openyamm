# MAW in the World of Xeen

The World of Xeen (`assets_dev/worlds/xeen/`, git-ignored until it ships; [devdocs/xeen/](../xeen/README.md)) is
MAW's fifth world beside Jadame (MM8), Antagarich (MM7), Enroth (MM6) and Chedian (MM9). This file is its design and
what is built, in the shape of [MM9_SUPPORT.md](MM9_SUPPORT.md), whose rules it follows wherever Xeen does not need its
own. Lane MX of the Xeen project (`devdocs/xeen/lanes/MX.md`) owns it; the user asked for it on 2026-11-21 ("MAW
scaling for the world of xeen, including the conjoined promotions, as MM9 does").

Questions marked **[D-n]** are design questions; each names the option built (the cheaper to reverse) and the
alternatives. They are listed together in section 9.

## 1. One source of truth

As MM9: every Xeen number MAW uses lives in one hand-edited file,
`assets_dev/engine/rulesets/maw/worlds/xeen/balance.yml` (read by `MawMapLevels::loadWorldBalance` whenever the world
is mounted, exactly as MM9's). `tools/maw/xeen_balance.py` checks it and writes what is derived:

- `item_bases.yml` beside it (`MawItemData::loadWorldBases`), the bases of Xeen's ordinary gear (section 6);
- `new_game_continents.yml` beside it: Xeen's new-game card with MAW's four new class lines (section 8);
- `--draft FILE`: the suggested band and madness level of every map from Xeen's acts (section 2);
- `--review FILE`: the testers' table (act, Standard party and monster levels, band, madness, natives, placed
  families), the route check (a story map whose natives meet the party more than two levels below the story map
  before it) and the D-G rows placed where their stem family is native, with the level each rule gives (D-84 MX-3);
- `--check`: fails when the file disagrees with Xeen's tables or a derived file is stale. It also checks the `xeen`
  columns of `data/promotions.yml` against Xeen's quest bit registry (`events/common/xeen_quests.lua`), and that every
  pack reserve was placed against the installed scene (section 4).

Run it after a change to `balance.yml`, `promotions.yml`, Xeen's map registry, monster rows or new-game card.

## 2. Levels: bank, continents, bands, ladders

**Continents.** Xeen's map rows (`worlds/xeen/data_tables/bolster_maps.txt`, generated) put Cloudside's maps on
continent 6 and Darkside's on 7 (D1 in WORLD_DESIGN: Town Portal, skies and death maps go by face).

**One bank for both faces [D-1].** `MawGameState::continentLevels` grows to five banks: Jadame, Antagarich, Enroth,
Chedian, Xeen. `continentIndex(6)` and `continentIndex(7)` are both the fifth. The faces are one route (Darkside is
interleaved from about party level 14, D-12; the story alternates), so a Darkside map must not grow with what the party
earned on Cloudside: that would scale Xeen's monsters by Xeen's own levels twice. Before this change continents 6 and 7
had no bank at all: their experience went into Jadame's bank and `levelOutside(6)` counted Xeen's own levels, so Xeen's
monsters grew with the party (and Jadame's did not grow with Xeen).
- Alternative: two banks (Cloudside, Darkside), as MAW's separate continents. Rejected: the faces are not separate
  adventures, and a party that alternates would face monsters bolstered by its own progress.

**Save format [D-2, decided by the user: U-4].** A fifth bank is a new value in MAW's saved state: `SaveVersion` 200
(`SaveVersionMawXeenBank`): older saves read four banks and Xeen's is 0; MM6-MM9 games are unchanged in play. The
console's `ruleset banks <mm8> <mm7> <mm6> <mm9> [xeen]`, the scenario step `ruleset_banks {..., xeen}` and the test
parties' optional fifth `banks` value name it. This is the one change outside Xeen-only logic; it is built because
there is no cheaper correct option (deriving Xeen's bank as `bankedLevel` minus the four banks breaks as soon as a
debug command or scenario sets banks).

**Bands** (`maps.<file>.band`, balance.yml version 2). MM9's rule, adapted: Xeen's maps were balanced on MM6-MM8's
Standard levels (`devdocs/xeen/research/MM678_CALIBRATION.md`), each with a Standard party level (`source/maps.yml`
`party`). That party level on MAW's MM7 stages, the same curve MM9's acts were put on (party 6 -> 7, 17 -> 15,
33 -> 30, 45 -> 47, 51 -> 57, 58 -> 70, 64 -> 85; linear between), gives the level the map's natives meet the party
at: MAW pins one native to the band's low, two to its low and high, three to low, mid and high, so with one native
the low is the curve's value, with two or three the mean of low and high is (D-84 MX-8; version 1 put the curve at the
middle everywhere, and the 27 one-native maps read 15-20 % low). Low and high keep the map's own natives' spread
(highest B over lowest, held to 1.3-2.0, 1.4 where it has fewer than two). Result: Act I 3-9, Act II 6-23, Act III
11-43, Act IV 21-57, Act V 34-86, Act VI 45-103, the optional dragon dungeons 65-112. `ruleset maplevels` (the level a
fresh MAW party meets, free progression): Castle Xeen 44 -> 53 (after X9 and X7 at 51), Castle Blackfang 34 -> 41
(before the Desert of Doom at 45), Castle Alamar 51 -> 62 (before the Skyroads at 67), the Alamar Depths 61 -> 74
(after the planes at 70), Dragon Cave 67 -> 80; MM6-MM9's rows are unchanged. MAW's MM6-MM8 starts sit at
3-7 and their last quarters at 55-100, so Xeen is a full parallel ladder, like Chedian. Xeen's natives sit higher than
MM6-MM8's at the start (Vertigo's orcs B 7-12 pinned to 3-5): MAW's monsters are stronger per level, as on Chedian.
- Towns without monsters (Bosco's Hall, Shangri-La) and the finale (P5) take their act's band; it sets only drops and
  scripted spawns.
- **Natives** are the map table's encounter pictures. 14 Xeen dungeons list none (the planes, the finale dungeons,
  Giants' Hall and the towns): every family there is pulled halfway into the band, as on MAW's MM6-MM8 maps without
  encounters.
  `balance.yml` `natives` names them there (Giants' Hall, the planes, the finale dungeons, Dragon Cave). **Mount
  Firestone (X7)** is an Act V map under MAW: its natives are the north's three families (Elemental Golem, Hydra,
  Dragon; D-84), and the south slope's orcs (B 7), which Xeen counts in Act I, are pulled halfway into its band, to
  about 20. MAW's guide says so.

**Horizontal starters**: Vertigo (X1), Joe's Warehouse (XD-01), Red Dwarf Mines (XD-02), Orc Caves (XD-05), the
start pocket's maps, as MM9's four.

**Beyond Madness**: one ladder over both faces (the bank is one), each map at 500 x (position / 79)^1.2 in route order
(Standard party level); X1 and XD-01 are the madness start maps at 4; the last, FD-04 (Dragon Tower and the Dungeon of
Death), 500.

**Horizontal levels**: the engine's formula on the bands; `ruleset maplevels` gives each map's free, banked,
horizontal and Beyond Madness level (section 10).

**Route check** (`--review`): three story maps meet the party more than two levels below the story map before them
(XD-24 Nightshadow Crypt 21 after the Troll Warren's 24, DD-05 31 after D4's 35, DD-12 32 after DD-07's 37): parallel
Act III-IV branches at the same Standard party level, left for testers.

**Story bands**: none needed. Xeen's staged places (Newcastle, Castle Kalindra, the liberated towns) do not raise
monsters by stage; `story_bands` can be added per map if the playthrough finds one.

## 3. Monsters

**Families [D-3, decided: D-84 MX-3].** `mawMonsterFamily` reads a world's rows by their picture's tier letter A-C. Xeen's monster table
also uses D-G (28 families: a fourth tier such as the Frost Dragon, duplicates for other placements such as Octopod
D/E, named uniques such as Snog, Orc Warband D). Those rows are, by the current rule, families of their own at tier B:
their level is their own table level pulled into the band, not their family's. Built: nothing (the current rule).
- Alternative: D-G rows join their stem's A-C family above C. Needs a tier above 3 in every place that reads
  `family.tier` (boss levels, damage and health ratios, summons), which also serves MM6-MM9; not worth it while the
  D-G rows are mostly uniques and duplicates. The decider kept the rule; `--review` lists the 40 D-G rows placed
  where their stem is native with both levels (most within 5; the planes' guardians, FD-03's onyx golems and FD-04's
  liches and Frost Dragon would stand 15-60 higher as their stems' members). If play shows it matters: a per-world
  alias in `balance.yml`, not a fourth tier.

**Bosses**: as MM9, scripted actors (a Lua behaviour: Lord Xeen, the Dragon King, Sheltem...) never become MAW bosses,
and a world's monster must be hostile. **Arena**: the Warzone (XD-20, MM7-style arena: fighters by tier and party level,
D-8.1) is one of MAW's arenas (`mawArenaMap`): band [1, 1, 1], madness level 1, no bolster, no rewards in Beyond
Madness. **Completion**: Xeen's octopods (D4's lake trap, P4's sea) and X2's lake dragons (row 11640, the leashed
trap) never count toward a map's clearing (`completion_exclude`), MM9's rule for monsters that guard water.

**Open-air BLVs**: `world.yml` `openAirMaps` (X8, X9, XD-17, D7, P1-P5) count as outdoors for MAW through the generic
`isOpenAirMap`, as MM9's. Fly stays refused there by Xeen's own map rules (WORLD_DESIGN 3.4); MAW adds nothing.

## 4. Density [D-4, built: D-84 MX-4]

Xeen's 13 outdoor maps use spawn points (596) with encounter pictures: MAW's group sizes grow them by difficulty as on
MM6-MM8 (x1.2 Hard, x1.4 Nightmare over whole maps). So do 15 of Cloudside's 69 indoor maps (Joe's Warehouse, the
Red Dwarf and Deep Mines, the Witch Tower, the Orc Caves, the Temple of Yak, Castle Burlock, the Tomb of a Thousand
Terrors, the Golem Dungeon, the Tower of High Magic, Darzog's Tower, the Robbers' Den, the Asp Undercroft, the Gargoyle
Eyrie, the Ogre Lair: 258 spawn points in their BLVs); their placed actors stay as they are, as on MAW's own MM6-MM8
dungeons. The other indoor maps place every monster as a scene actor, which MAW's group sizes cannot grow: they get
MM9's **pack reserve**.

- **Density by difficulty** (`balance.yml` `density`, MM9's figures): Easy, Normal, MAW 1.0; Hard, Hell 1.2; Nightmare
  1.4; Doom 1.6; Road to Insanity 1.8; Beyond Madness 2.0 (a challenge mode's factor replaces the difficulty's). A
  map's own `density` would multiply it; none is set: Xeen's dungeons already hold MM6-MM8's counts (MM9's were
  sparser, which is why MM9 needed its per-map factors).
- **The reserve** (`rulesets/maw/maps/<stem>_zz_maw.scene.yml`, `initial_state.pack_reserve`): copies of the map's
  monsters beside them, read by MAW only (`MonsterRules::packDensityFactor`, `MapDeltaData::packReserve`); a copy whose
  `from_factor` the difficulty reaches joins at the map's first fill and each refill. Standard games never read it.
- **The tool**: `tools/maw/xeen_pack_reserve.py [stems]` (every indoor map without arguments; under a minute). It is
  MM9's `mm9_pack_reserve.py` made world-neutral: the shared part is `tools/maw/pack_reserve.py` (the MM9 converter's
  placement: floor, sector, walls, doors and movers, ladders, event faces, water; the crowd rule, never more than 6
  monsters within 400; the arrivals' leeway; ranking and the overlay), each world's front end says where its packs,
  scripting and arrivals come from. MM9's 28 reserves come out byte-identical (checked on all MM9 maps, 2026-11-21).
- **Xeen's packs**: the map's monsters in clusters (within 700, one sector); its monsters are hostile Xeen rows that
  are no people and are not left out of the clearing (the octopods).
- **Never copied**: actors hidden at the start, with an identity, named by the map's Lua (actor index or name) or
  cinematics, and bosses (`source/monsters.yml` `bosses`). Their share goes to the map's other packs. **Scripted
  groups take copies**: Xeen's Lua addresses a group only as a whole (`evt.SetMonGroupBit` to hide, show or calm it,
  group kill checks), and a copy keeps its member's group, so it hides, shows, calms and must be killed with it.
- **Arrivals**: no copy within 1,500 of where the party arrives: the scene's start points, every `evt.MoveToMap` onto
  the map (any Xeen script, and the map's own in-map teleports), the scripts' arrival tables (`{x, y, z, yaw, map}`:
  the planes, Shangri-La, the Skyroads), the data tables' landings and transports, and `balance.yml` `arrivals`.
- **Skipped**: the Warzone (an arena), the finale (P5), Bosco's Hall and Shangri-La (towns without monsters), and the
  spawn-point maps above.
- **Result** (2026-11-21): 48 maps have a reserve, 39 of them reaching x2.0 (Beyond Madness); short of it, by room
  near their monsters or scripted members: Castle Kalindra (DD-03) 1.44 (36 of its monsters are hidden armies of
  the story), the Gremlin Court (DD-04) 1.79 (17 named by its Lua), the Troll Holes (DD-11A/B) 1.65/1.70, the Gargoyle
  Lair (DD-23) 1.27, Giants' Hall (DD-24) 1.50, the Dungeon of Death (FD-04) 1.78, Dragon Cave (XD-18) 1.68, the Ninja
  Pagoda (XD-22) 1.74. No reserve: Corak's Pod (DD-16, 7 monsters, all near its arrivals) and Newcastle Keep (XD-13,
  every monster scripted by the castle's stages).
- **A rebuilt map stales its reserve**: the overlay records the scene it was placed against (`scene_actors`,
  `scene_check`); after a rebuild the game skips the reserve (and says so in the log) and `xeen_balance.py --check`
  fails naming the map. **Map lanes rerun `python3 tools/maw/xeen_pack_reserve.py <stem>` after every rebuild** of an
  indoor Xeen map, then `xeen_balance.py --check`.
- Test: `tests/scenarios/xeen/maw_density.yml` (Ellinger's Tower 51 at MAW, 71 at Nightmare, 102 at Beyond Madness
  and after a save; Castle Xeen 144 and the Alamar Depths 68 at Beyond Madness; Standard 51 and 72). Captures:
  `output/xeen_mx/s2/tour_dd02_grid.jpg` (a hall of Ellinger's Tower at Beyond Madness and in Standard).

## 5. Promotions: Xeen as the fifth world

MAW counts a class line's final promotion on each world (`data/promotions.yml`, `mawPromotionWorlds`); two worlds make
its final classes Elder (x1.25 HP and SP per level), three Ultimate (x1.5), four Supreme (x1.75, DEVIATIONS 183).
Xeen gets a `xeen` column by MM9's rule: the quest bits of the closest Xeen promotion quest of the line's theme, any of
them. Xeen's promotions (`Xeen.Promotions`, QUESTS.md 3) are tier 1 on Cloudside and tier 2 on Darkside with MM7's
Light or Dark choice, plus five racial ones, so each line takes **both** its Light and its Dark tier-2 quest (either
counts) and the racial lines their racial quest. The bit is the one each later promoter's topic waits for
(`RegisterCanShowTopic(... IsQBitSet(QBit(n)) and Xeen.canPromote(key))`), i.e. the quest done, whoever was promoted.

| MAW kind | Xeen bits (Light / Dark) | Quests |
|---|---|---|
| 1 Archer | 113407 / 113384 | Luna's Statuettes (Master Archer) / the Southern Tower (Sniper) |
| 2 Cleric | 113127 / 113462 | the Heretics of Mok (Priest of Light) / Sandro's Heart (Priest of Dark) |
| 3 Dark Elf | 112341 | the Wand of Faery Magic (Patriarch, racial) |
| 4 Dragon | 112507 | the Dragon Tax's Great Wyrm (racial; set when a dragon rises) |
| 5 Druid | 114560 / 113449 | Leafpoint's Grove (Arch Druid) / the Coven, joined (Warlock) |
| 6 Knight | 114522 / 113344 | Dimitri's Test (Champion) / the Voweless Knights' oath (Black Knight) |
| 7 Minotaur | 113500 | the Minotaur's Labyrinth (racial) |
| 8 Monk | 113066 / 114540 | the Drawkcab Way (Master) / the Ninja Pagoda's clan (Ninja) |
| 9 Paladin | 113127 / 113344 | the Heretics of Mok (Hero) / the Voweless Knights (Villain) |
| 10 Ranger | 113201 / 113228 | Sharla's Sprites, polite (Ranger Lord) / Kramer's Bounty (Bounty Hunter) |
| 11 Thief | 113281 / 113384 | the Wizard Quarter (Spy) / the Southern Tower (Assassin) |
| 12 Troll | 113262 | Hobstadt's trial (War Troll, racial) |
| 13 Vampire | 112141 | the Count of Nightshadow (Nosferatu, racial) |
| 14 Sorcerer | 113365 / 113462 | the Jewel of Ages (Archmage) / Sandro's Heart (Lich) |
| 15 Necromancer | 113365 / 113462 | as the Sorcerer (MM9's precedent: Mage and Lich) |
| 17 Seraphim | 113127 / 113462; mid 112201 | the Cleric's; mid: the Seasons Relay (T1-C, Cleric -> Priest) |
| 18 Death Knight | 114522 / 113344; mid 110047 | the Knight's; mid: the Crusade (T1-A, Knight -> Cavalier) |
| 19 Shaman | 114560 / 113449; mid 112201 | the Druid's; mid: the Seasons Relay (T1-C, Druid -> Great Druid) |
| 20 Elementalist | 113365; mid 110204 | Archmage only (MM9: Mage only); mid: Barok's Pendant (T1-B, Sorcerer -> Wizard) |

**Five worlds [D-5, decided by the user: U-4].** `promotionFactor` already caps the count at four and `displayName` reads four and up as
Supreme, so Xeen counts as one more world: **Supreme from any four of the five**, the fifth adds nothing. Nothing
changes for a game without Xeen (no Xeen bit can be set there). Built.
- Alternatives (they change MM6-MM9 rules, not built): Supreme only at all five (a game without Xeen could never reach
  it again); a sixth rung at five worlds (x2.0, a new deviation).

The racial bits Dragon (112507) and Troll (113262) are set only when such a member is promoted (the Great Wyrm topic
and Hobstadt's trial need one in the party); that is the racial line's promotion done, which is what MAW counts.
Xeen's own `Xeen.promote` still renames members of the classes it knows (Knight -> Cavalier ...); MAW then moves a kind
to its final step once a world's bit is set, as on Chedian. Test: `MawClassTests` "MAW counts Xeen's promotion quests
as a fifth world, Supreme from any four"; scenario `tests/scenarios/xeen/maw_new_game.yml`.

## 6. Items, shops, loot

- **Xeen's gear** (U-1): no new equipment but the gem gear (Ruby Broadsword, Emerald Leather, Sapphire Staff, Diamond
  Plate, rows 12540-12543), which wears artifacts' pictures. **[D-6, decided: D-84 MX-6]** Each sits on the MAW rung of
  its Xeen tier (`source/items.yml` `crafted.*.tier`: Ruby Broadsword 4, Emerald Leather and Sapphire Staff 5, Diamond
  Plate 6) by MM9's table (tiers 1-4 and 6 on rungs 1, 2.25, 3.5, 4.75, 6; tier 5, which MM9 lacks, between them at
  5.375), with its own dice, MAW's mean armour of its slot at that rung and the slot's reference armour, at strength
  1.10, 1.15 for the Diamond Plate (MM9's figures): `[4.75, 3, 0, 0, 0, 1.1]`, `[5.375, 0, 0, 25, 30, 1.1]`,
  `[5.375, 3, 1, 0, 0, 1.1]`, `[6, 0, 0, 59, 60, 1.15]` (`GEM_GEAR` in `xeen_balance.py`, `item_bases.yml`).
- **Artifacts and relics** keep their table values and fixed effects, as MAW's own and MM9's; the Slayer Sword (value
  0, NoDrop) is untouched.
- **Shops**: Xeen's houses are MM6-MM8 house types (`house_data` rows 4001+), so MAW's shop rules apply as on MM6-MM8;
  `MawItemRules::shopRerollCost` now knows Xeen's houses (continent 6, the Xeen bank). **Loot**: Xeen rolls its own pool
  plus MM6-MM8's (D-80); MAW's loot rules apply unchanged.
- **Spellbooks**: Xeen sells MM6-MM8 books (no world books of its own), priced by MAW's tables.

## 7. MAW's people in Xeen [D-7, built: D-84 MX-7]

MAW gives each continent a Seer (skill reset, Dimensional Maps), town bounty offices and a continent teleporter in
its start town. Xeen's NPCs are MM6-MM8-style (`npc.txt` rows 4001+), so MAW's own topics serve them.

- **Seers**: **Zephyra**, Castle Burlock's Court Magician (X4, The Weathervane, npc 4312), and **Madame Oorla**, the
  fortune teller of Castleview (D1, npc 4921), offer MAW's skill reset (global events 10010, 10011) and Dimensional
  Maps (10040) in their free topic slots 2-4: five topics each with their own two. Both live in towns that Town
  Portal reaches (Castle Burlock, Castleview) and stay there at every story stage. Artemus, the decider's first
  choice, has six topics already (no room); Zephyra is the court's nearest who fits. The patch is MAW's only:
  `rulesets/maw/worlds/xeen/npc_seers_patch.txt`, a `world: xeen` entry of `ruleset.yml` on Xeen's
  `data_tables/npc.txt`; `Global_maw.lua`'s Dimensional Maps slots name them too and touch a slot only where its NPC
  has the topic (a game without Xeen sets nothing new).
- **Bounties**: nothing new. Xeen's town halls (Vertigo, Castleview, ...) are MM6-MM8 town halls, whose Bounty Hunt
  MAW already runs: none until the town's map is cleared ("clear ... COMPLETELY first"), then a named boss target with
  a "Bounty" map note, and the reward once it is slain.
- **Continent teleporter** (horizontal progression): a dimensional travel pedestal under a glowing orb on Vertigo
  Square, south of the party's start. Since 2026-11-21 it is the world's own, in every ruleset, as New Sorpigal's,
  Ravenshore's, Harmondale's and Sturmford City's are (`worlds/xeen/maps/xeen_x1_dimensional_travel.scene.yml`, event
  1777 in `worlds/xeen/events/maps/xeen_x1_dimensional_travel.lua`, both picked up by file name beside the Map Studio
  project's X1 files, which stay untouched); MAW's first copy (`rulesets/maw/maps/xeen_x1_zz_maw.scene.yml`,
  `xeen_x1_maw.lua`) is gone, so a MAW game has one pedestal. It opens the continents' portals; their screens' Xeen
  door lands at Vertigo (`worlds/xeen/data_tables/dimension_doors.yml`). A return pedestal elsewhere is a separate
  request.
- Tests: `tests/scenarios/xeen/maw_seers_and_bounties.yml` (both Seers; Vertigo's and Castleview's bounty: refusal,
  target and note, reward; Standard has no Seer topics), `tests/scenarios/xeen/dimensional_travel_vertigo.yml` (the
  pedestal in Standard and MAW; New Sorpigal's opens the same screen). Capture: `output/xeen_mx/s2/tour_x1.jpg`.

## 8. New game

- `ruleset.yml` `worlds` lists `xeen`: the Xeen card (world contribution `new_game_continents`, continent 6) is
  offered under MAW; without the world installed it stays hidden as before.
- **MAW's four new class lines on Xeen's card**: a ruleset's `world: xeen` `replace` of
  `data_tables/new_game_continents.yml` now applies to a world's card (`appendWorldNewGameContinents` reads it through
  `readRulesetDataFile`); MAW's copy is `worlds/xeen/new_game_continents.yml`, written by `xeen_balance.py` from
  Xeen's generated card plus classes 53, 56, 59, 62. Xeen's races stay its own.
- Start: Vertigo (X1), as Standard.

## 9. Design questions

| # | Question | Built (cheaper to reverse) | Alternatives |
|---|---|---|---|
| D-1 | Xeen's level bank | one bank for both faces | decided (D-84): kept |
| D-2 | Save format for the fifth bank | SaveVersion 200, older saves read four banks | decided by the user (U-4): accepted |
| D-3 | Xeen's D-G picture tiers | families of their own (current rule) | decided (D-84): kept; `--review` lists them |
| D-4 | Density of Xeen's placed-only dungeons | MM9's pack reserve, generalised (built 2026-11-21) | decided (D-84) |
| D-5 | Supreme with five worlds | any four of five; fifth adds nothing | decided by the user (U-4): accepted |
| D-6 | Gem gear bases | Xeen's tiers as rungs, strength 1.10 / 1.15 | decided (D-84) |
| D-7 | MAW's people in Xeen | Seers Zephyra (X4) and Madame Oorla (D1); town halls' bounties; Vertigo's pedestal (the world's own since 2026-11-21) | decided (D-84) |
| D-8 | Bands curve | MM9's curve, the natives meeting it (v2), X7 an Act V map | decided (D-84) |

## Decided by the user

- **U-4 (2026-11-21)**: MX's D-2 and D-5 accepted as built: save version 200 stores the fifth (Xeen) MAW bank, older
  saves load with four; a MAW class line promoted on any four of the five worlds is Supreme (x1.75 unchanged), so Xeen
  can stand in for MM9 (`devdocs/xeen/DECISIONS.md` U-4).
- The decider's answers to D-1, D-3, D-4, D-6, D-7 and D-8 are `devdocs/xeen/reviews/D84_DECISION.md` (D-84).

## 10. Built (2026-11-21, lane MX session 1)

- Data: `rulesets/maw/worlds/xeen/balance.yml` (version 1, 82 maps), `item_bases.yml`, `new_game_continents.yml`;
  `data/promotions.yml` `xeen` columns and Xeen `mid` bits; `ruleset.yml` `worlds` with xeen and the card replace;
  `data/texts.yml` Level popup names the Xeen bank.
- Tool: `tools/maw/xeen_balance.py` (check, derive, `--draft`, `--review`).
- Engine: `MawGameState` five banks (continents 6 and 7 the fifth), `SaveVersionMawXeenBank` 200, `MawPromotionKind::xeen`
  counted by `mawPromotionWorlds` (0-5), the Progress tab's Xeen card (continents 6 and 7, shown while it has maps),
  the Level popup's `levels_xeen`/`bolster_xeen`, `ruleset banks` with an optional fifth value, the scenario step's
  `xeen`, test parties' optional fifth bank, `shopRerollCost` for Xeen houses, the Warzone in `mawArenaMap`, world
  card replacement by a ruleset.
- Tests: `MawClassTests` (Xeen promotions, Supreme from four of five), `MawMonsterLevelTests` (the fifth bank, the
  Warzone), `RulesetTests` (MAW supports xeen; the save round trip with five banks); scenario
  `tests/scenarios/xeen/maw_new_game.yml`.
- Guide: the MAW guide has Xeen as its fifth continent (maps, levels, teachers, promotions from the Xeen guide's data)
  and a section, `tools/maw_site/content/xeen.html`; deployed to https://jasicek.net/openyamm/maw-guide/.

## 11. Built (2026-11-21, lane MX session 2)

- `balance.yml` version 2 (bands, X7's natives, `density`); gem gear on Xeen's tiers; `xeen_balance.py` `--review`
  route check and D-G list, `--check` of the reserves.
- Density: `tools/maw/pack_reserve.py` (shared), `mm9_pack_reserve.py` on it (MM9's output byte-identical),
  `xeen_pack_reserve.py`; 48 reserves `rulesets/maw/maps/xeen_*_zz_maw.scene.yml`.
- People: the Seers' patch, `Global_maw.lua`'s Dimensional Maps slots; Vertigo's pedestal overlay and event, moved
  to the world on 2026-11-21 (every ruleset).
- Tests: `tests/scenarios/xeen/maw_density.yml`, `maw_seers_and_bounties.yml`, `dimensional_travel_vertigo.yml`
  (Standard and MAW). No engine change.

Open: the Xeen playthrough has not been run under MAW; tester feedback on the bands and the reserves.
