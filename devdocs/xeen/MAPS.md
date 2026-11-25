# Xeen: map sheets

Proposal, 2026-11-12; revised 2026-11-14 for the user's decisions after the three reviews (README, "Decisions of
2026-11-14"; `reviews/`). Part of the [Xeen world design](README.md). The per-map progression table first, then one
sheet per outdoor map, then the dungeon list. Monster levels are **monster** levels (A-tier range of the map's
encounter families, highest C-tier level), not party levels; MM7 puts a level-10 party among level 4–24 monsters, and
so does this design. A sheet's monster band must contain its named families' A-to-C levels.

Density targets come from `research/MM678_CALIBRATION.md`, `research/MAP_CRAFT_CALIBRATION.md` §6 (the "not bland"
checklist) and `reviews/SCALE_AND_DENSITY.md`. Every sheet must satisfy: exactly one obelisk, ≥ 4 kinds of interaction
device with one permanent-effect device, the **POI budget** of its row (20–50 POIs 1,300–2,600 units apart, by map
type; counted as the shipped games were, one point per spot merging anything within 400, service doors included, D-11.4), 3–6 dungeon entrances, 4–10 outdoor chests with a reason each (start pocket 8–12), 45–70 spawn markers,
**hostiles at load as in the per-map table** (by map role, MONSTERS_AND_ITEMS §3), monsters in 3–8 **encounter areas**
of 6–30 cells of 4,096 with at least a third of the land cells quiet, first fight 4,096–8,192 from each map-edge arrival and the new-game start (5,888 when the marker's slot shoots or casts; marker centres 1,024 from a road; dungeon exits the same from each map's rebuild, D-142; road, lane or path alike, D-157; a start in a town that shares its point with a town arrival has no upper end and keeps the floors, D-158; town arrivals keep the town buffer instead, D-15), roads
on 1–4 % of land, height range ≥ 2,500.

Family names refer to [MONSTERS_AND_ITEMS.md](MONSTERS_AND_ITEMS.md#2-monster-families). "Tres" is the map_stats
treasure level on MM7's scale (chests at the map's level, one boss hoard per dungeon one step up), "L/T" lock and trap
difficulty.

## 0. Progression per map

Adopted by the user on 2026-11-14 from `reviews/COMBAT_AND_PROGRESSION.md` §5.1, with the changes noted under the
table. Party levels are a full clear (kills at these counts and bands plus the act's quest budget); a party that skips
half the outdoor monsters is one to three levels lower, and finishes at about 62–65. Monster bands are A-tier to
C-tier, boss after the comma. "Kill XP" is per member (four members), full clear.

| Map | Act | Party arrive → leave | Monsters A–C, boss | Groups | Tres | Monsters | Kill XP per member |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X1 Vertigo Meadows | I | 1 → 4 | 2–12 | 2–3, about 60 groups (orcs 3–5) | 1 | 175 | 3.3k |
| XD-01 Joe's Warehouse | I | 1 → 3 | 2–6, Wobbles 4 (boss row) | 2–3 | 1 | 28 | 0.3k |
| XD-02 Red Dwarf Mines | I | 3 → 5 | 3–10 | 2–3 | 1 | 55 | 1.1k |
| XD-05 Orc Caves | I | 3 → 5 | 4–10, Drum-Master 12 | 2–3 | 1 | 40 | 0.9k |
| XD-03 Deep Mine | I | 5 → 6 | 6–12, Clan King 18 | 2–3 | 1 (hoard 2) | 40 | 1.4k |
| XD-04 Witch Tower | I | 5 → 7 | 4–14, Head Witch 20 | 2–3 | 1 (hoard 2) | 50 | 1.5k |
| X2 Rivercity | II | 7 → 11 | 6–24 (lake dragons 60, trap) | 2–4 | 1 | 135 | 8.2k |
| XD-21 Robbers' Den | II | 9 → 11 | 10–18 | 2–3 | 2 | 28 | 1.9k |
| XD-27 Ogre Lair | II | 10 → 12 | 12–20 | 2–3 | 2 | 28 | 2.5k |
| X4 Burlock Savannah | II | 11 → 15 | 10–30 | 2–4 | 2 | 135 | 14.0k |
| XD-07 Castle Burlock | II | 12 → 14 | 10–24 (caged fire dragon optional) | 2–3 | 2 | 50 | 4.3k |
| XD-25 Asp Undercroft | II | 14 → 16 | 14–26 | 2–3 | 2 | 28 | 3.4k |
| XD-26 Gargoyle Eyrie | II | 15 → 17 | 16–28 | 2–3 | 2 | 28 | 4.1k |
| X3 Lifeforce Lagoon | II | 13 → 16 | 10–30 | 2–4 | 2 | 135 | 14.0k |
| XD-13 Newcastle Keep (staged) | II–IV | 14 → 16 | 16–24 (wood golems) | 2–3 | 2 | 28: Act II 15, Act IV 10 (D-4; A2) | 5.6k: Act II 1.9k, Act IV 3.7k |
| XD-06 Temple of Yak | II | 14 → 16 | 14–28, Yak Master 35 | 2–3 | 2 | 50 | 6.4k |
| XD-08 Tomb of 1000 Terrors | II | 15 → 17 | 15–30 | 2–3 | 2 | 50 | 7.2k |
| XD-09 Golem Dungeon | II | 16 → 18 | 18–40, Diamond Golem 50 | 1–2 | 3 | 45 | 9.6k |
| XD-10 Cave of Illusion | II | 17 → 19 | 18–28 | 2–3 | 3 | 50 | 8.1k |
| XD-11 Tower of High Magic | II | 18 → 20 | 18–32 | 2–3 | 3 | 50 | 8.9k |
| X8 Cloudreach (sky) | II | 18 → 20 | 14–30 (cloud golem 50 rare) | 2–3 | 3 | 60 | 8.1k |
| D1 Castleview Vale | III | 18 → 21 | 14–30 | 2–4 | 2 | 135 | 18.3k |
| DD-01 Castleview Sewer | III | 18 → 20 | 10–20, Rooka the Rat Queen 24 | 3–4 | 2 | 50 | 3.7k |
| DD-04 Gremlin Court | III | 19 → 20 | 14–22, Gettlewaithe 24 | 2–4 | 2 | 28 | 2.5k |
| DD-02 Ellinger's Tower | III | 20 → 22 | 14–24 | 2–3 | 2 | 50 | 5.7k |
| D2 Sprite Forest | III | 21 → 25 | 16–38 | 2–4 | 3 | 135 | 24.9k |
| DD-06, DD-09, DD-13 | III | 22 → 26 | 14–32 (Barkman 60 optional) | 2–3 | 3 | 120 | 17.1k |
| DD-10, DD-11 (5 pockets; the north pocket in Act V, D-27) | III | 23 → 27 | 16–38, Hobstadt 42 | 2–3 | 3 | 100 | 22.1k |
| X5 Winterkill Tundra | III | 24 → 28 | 16–40 (cyclops corner 36–50, trap) | 2–4 | 3 | 135 | 26.0k |
| XD-22, XD-23, XD-24 | III | 25 → 29 | 18–40, Count Draco 45 | 2–3 | 3 | 84 | 17.9k |
| D3 Sandcaster | III | 27 → 30 | 22–45 (A 22–35, C 45; D-28) | 2–4 | 3 | 135 | 34.8k (planned 37.4k, +7 %, accepted by D-28) |
| DD-18 Sandcaster Sewer | III | 28 → 30 | 25–40 | 2–3 | 3 | 50 | 14.6k |
| X6 Desert of the Sphinx | IV | 30 → 33 | 22–50 | 2–4 | 3 | 135 | 41.5k |
| XD-14, XD-15 | IV | 31 → 34 | 22–45 | 2–3 | 4 | 90 | 25.3k (D-39: 26.85k, +6 %) |
| DD-03 Castle Kalindra (staged) | III–IV | 24 → 40 | 26–45 (Scraps 70 optional) | 2–3 | 4 | 54: Act III 24, Act IV 30 (D-26; A2) | 20.9k: Act III 6.8k, Act IV 14.1k |
| XD-12 Darzog's Tower | IV | 33 → 36 | 30–48, Darzog 55 | 2–4 | 4 | 80 | 32.1k |
| D4 Lakeside and Blackfang | IV | 35 → 38 | 26–50 (octopods 60, lake trap) | 2–4 | 4 | 120 | 43.0k |
| DD-05, DD-20, DD-23 | IV | 35 → 39 | 24–45, Cult Leader 45, Head Witch 45 | 2–3 | 4 | 105 (D-42) | 30.5k (D-39/D-42: 105 monsters, 32.84k, +7.7 %) |
| DD-12 Dungeon of Lost Souls | IV | 37 → 39 | 35–55 | 2–3 | 4 | 45 | 23.5k (D-42: 23.79k, +1.2 %) |
| DD-14 Castle Blackfang | IV | 39 → 42 | 36–58, Count Blackfang 70 | 2–4 | 4 (hoard 5) | 70 | 39.2k (D-42: 40.91k, +4.4 %) |
| DD-19 Wizard Quarter | IV | 38 → 41 | 32–55, Xenoc 60, Morgana 60 | 2–3 | 4 | 50 | 23.8k (D-42: 24.7k, +3.8 %) |
| D5 Desert of Doom | V | 42 → 45 | 30–62 (D-49) | 2–3 | 5 | 110 | 52.3k (L1 55.6k, +6 %, D-49) |
| DD-15 Great Pyramid | V | 44 → 47 | 42–65 | 2–3 | 5 | 70 | 50.4k (51.92k, +3.0 %, D-61) |
| DD-16, DD-24 | V | 45 → 47 | 38–58 (the People 38/50/58, D-47) | 1–3 | 5 | 37 (7 + 30, D-47) | 26.7k (25.59k, −4.2 %, D-47) |
| X9 Clouds of Xeen (sky) | V | 46 → 48 | 35–55 | 2–3 | 5 | 50 | 26.1k (L1 26.0k, −0.4 %, D-50) |
| XD-19 Castle Xeen | V | 47 → 50 | 42–70, Xeen's Pet 75, Lord Xeen 85 | 2–3 | 5 (hoard 6) | 70 | 53.3k (54.38k, +2.0 %; 57.99k with the bosses, D-47) |
| D6 The Forbidden Zone | V | 48 → 51 | 30–75 (D-49) | 2–3 | 5 | 110 | 71.1k (L1 73.4k, +3 %, D-49) |
| DD-10C Gemstone Mines, north pocket (D-27) | V | 48 → 51 | 40–50 (Floating Eye, Terrible Eye, Patrol) | 2–3 | 5 | 20 | 11.5k (11.50k, 0.0 %, D-62) |
| DD-07 Eastern Tower (moved to Act IV, D-9.3) | IV | 36 → 40 | 28–48 | 2–3 | 4 | 30 | 11.2k (D-39: 11.57k, +3 %) |
| DD-08, DD-21 | V | 49 → 52 | 40–62, Sandro 65 | 2–3 | 5 | 60 + Sandro (DD-08 45; DD-21 15 + Sandro, D-62) | 39.6k (41.84k, +5.7 %: DD-08 31.14k, DD-21 10.70k, D-62) |
| DD-17 Castle Alamar | V | 52 → 55 | 50–75 | 2–3 | 5 (hoard 6) | 70 | 67.9k (68.85k, +1.4 %, D-61) |
| X7 Mount Firestone (trap map) | V | 40 → 55 | south 5–10 orcs (counted in Act I, D-40); north 40–85 | 1–3 | 5 | 90 | 76.4k |
| XD-16 Volcano Cave | V | 48 → 52 | 42–58 | 2–3 | 5 | 40 (under M's 45, D-47) | 26.6k (27.34k, +2.8 %, D-47) |
| D7 The Skyroads (sky) | VI | 55 → 58 | 48–75 (griffins 48; Megadragon 125, optional; D-58) | 1–3 | 6 | 50 | 48.5k (L1 48.8k, +0.6 %, D-58) |
| P1–P4 planes | VI | 56 → 60 | 55–70, sleepers' guardians 75 | 2–3 | 6 | 4 × 30 | 124.1k (L1 128.0k, +3.1 %, D-58) |
| FD-01, FD-02 | VI | 58 → 61 | 55–80 | 2–3 | 6 | 60 (FD-02 26; FD-01 34, D-57, D-69) | 68.0k (71.88k, +5.7 %: FD-02 31.07k, FD-01 40.81k, D-69) |
| FD-03 Darkstone Tower | VI | 60 → 63 | 60–85 | 2–3 | 6 | 45 | 58.9k (60.70k, +3.1 %, D-57) |
| DD-22, DD-26 | VI | 56 → 60 | 48–65 | 2–3 | 6 | 40 (DD-22 20; DD-26 20, D-65) | 33.5k (35.96k, +7.3 %: DD-22 17.20k, DD-26 18.76k, D-65) |
| XD-18 Dragon Cave (optional) | opt. | 60 → 64 | 65–100, Dragon King 110 | 1–2 | 6 | 40 (under M's 45, D-57) | 64.6k (66.64k, +3.2 %; 69.94k with the King, D-57) |
| FD-04 Dragon Tower and Dungeon of Death (optional) | opt. | 62 → 66 | 65–100 | 1–3 | 6 | 60 | 96.8k (100.22k, +3.5 %, D-57) |
| XD-20 Warzone | any | — | by tier | — | — | — | — |

Correction (DECISIONS D-9.3, 2026-11-20, A2's recount at the table's rules): DD-07 moves to Act IV with 30 monsters
at 28–48, 11.2k; DD-08 and DD-21 keep 60 monsters in Act V, 39.6k (the three were 90 monsters and 59.3k in Act V).
Act IV's kill XP goes from 279.5k to 290.7k (+4 %), Act V's from 510.1k to 490.4k (−4 %): both inside the 15 % rule.

Correction (DECISIONS D-1.3, 2026-11-20): X1 is fuller, about 175 hostiles (160–190) in about 60 groups of 2–3 near
the roads, kill XP 3.3k (was 130 and 2.4k); Act I's kill budget becomes about 8.5k (was 7.6k).

Changes against the review's table: XD-03 and XD-05 carry their built 40 monsters (they are M by the decision of
2026-11-14; kill XP scaled); XD-06 is on X2 and FD-05 is merged into FD-04 (below), with unchanged numbers; XD-13,
XD-25 and XD-26 were missing from the review's table and are added at its rules (typical monster A + 0.3 × (C − A),
XP = L(L+10)). Totals: **about 4,200 monsters, 6.35M party kill XP (1.58M per member; MM7 1.25M)**; quest XP about
0.88M per member (Act I 16.5k, II 83k, III 132k, IV 160k, V 209k, VI 210k, optional 70k). Act ends (full clear):
I 7, II 20, III 32, IV 44, V 58; main path 67, with the optional content 70, as played about 62–65. Re-count after
each act's builds with `output/xeen_review/combat/proposed.py` or its successor; an act over its share by more than
15 % is trimmed.

## 1. Cloudside surface

Grid (WORLD_DESIGN §3.1), south row west to east: X5, X3, X2, X1; north row: X6, X4 (above X3 and X2), X7. Rivercity
(X2) is the first road hop from Vertigo (decision of 2026-11-14); in the source both Rivercity and the Lagoon border
Vertigo's squares.

### X1 Vertigo Meadows: start pocket

| | |
| --- | --- |
| Source | Clouds E3, E4, F3, F4 (+ the Red River edge of F2) |
| Biome and sky | Green meadow, orchard and river delta; Pitchfork Creek; a dead forest in the south-west corner (Forest of the Walking Dead). The **east edge is the world rim**: meadow ending in white cliffs above the stars. `fair` sky, light rain |
| Monsters | A 2–5, C ≤ 12. **Orcs** (5/7/10, d1, orc outposts to burn), **Toads and snakes** (5–12, Toad Meadow), **Skeletons and zombies** (6–18, dead forest, d2). Pests (slimes, doom bugs) only in Joe's warehouse and the town's first quest. Party 1 → 4. 130 hostiles at load in four areas (the northern hills' orc country, Toad Meadow, the dead forest, the orc outposts' road). Tres 1, L/T 0/1 |
| Town | **Vertigo** (full services, start; WORLD_DESIGN §5.1), on the river with a bridge and a walled core. Toad Meadow hamlet: Myra the Herbalist, Valia's cottage |
| Dungeons | **Four sites, five BLVs**: Joe's Warehouse (XD-01) in town; the Red Dwarf Mines (XD-02) in the northern hills, with the Deep Mine (XD-03) below them, reached only by XD-02's mine cart (its escape shaft surfaces in the X1 hills as a one-way exit, a shortcut once its lever is thrown); Witch Tower (XD-04) in the south-east; Orc Caves (XD-05) in the north-east hills. The Temple of Yak moved to X2 and the Dungeon of Death into FD-04 on X7 (decision of 2026-11-14: Vertigo keeps 3–4 dungeons) |
| Outdoor content | Obelisk; Fountain of Ability (+2 permanent Luck, charges); Waters of Power (temporary HP); Wishing Well; Shrine of Poison (Body resistance, permanent once); 3 orc outposts to burn; Orothin's island statues; Derek's camp and Celia's hut; the **travel pyramid** (to Castleview) on a knoll east of town; the **Water Reflector** on the rim (M37, guarded late); Spring Druid's grove; Crodo's bottle in Pitchfork Creek ("Help! I'm in Darzog's tower!--Crodo", QUESTS M1) |
| POI budget | Named items 20; add 20–30 generic devices to reach the hub band of 40–50: wells or fountains 4, camps with a fire 4, graves or ruins with a chest 4, signposts at forks 4, one stat challenge or buff pedestal; at most 6,000 of road or open land without a POI or fight. 8–12 outdoor chests, half of them in plain sight for a level-1 party |
| Arrivals | Start in Vertigo square; **river road west to X2 (Rivercity)**; road north to X7; Captain Nystor's boat from Rivercity up the river; pyramid from D1 |
| Signature view | The orchard road east of Vertigo ending at the rim, the stars below |
| Original lines | Gunther's welcome (town hall); Joe's "I've just about got the situation under control" (before M2); four Plague Cult members ("Sinners must repent." …); signs "This space for rent", "Pest control by Joe", "Please help clean up our beautiful town." (later "Thank you"); the hiccuping drunk in the tavern (M2's clue); the money-tree sceptic; Vern's guild dues; Joe's "Out of Business" after M2; Valia's Falista story. Texts and references: `reviews/STORY_AND_ATMOSPHERE.md` §3.1 |
| Notes | The safe pocket of calibration: complete services, four dungeon sites, d1 monsters, 3–5 wells. The witch tower and its goblins are visible from town from day one. Nothing more goes on X1. Decorations at most 800 (MM8 town level); keep ≥ 40 central land cells with fewer than 3 decorations as open meadow. Built 2026-11-13; what it must change: [CHANGES_FOR_BUILT_MAPS.md](CHANGES_FOR_BUILT_MAPS.md) |
| Added by the Act I briefs | Joe's warehouse key under a rain barrel by the warehouse; a culvert grate on Vertigo's riverbank (XD-01's second exit, opened from inside); the shaft head of the Clan King's escape shaft in the hills (XD-03, one-way out until its lever is thrown); Tam, Oslo's son, held in the Orc Caves (small reward at Oslo's hut); once the orcs' war drums burn (XD-05) the orc outposts stop refilling (a map state). Briefs: `briefs/xd01`–`xd05`, `briefs/x1` |

### X2 Rivercity and Lake Darzog: the hub

| | |
| --- | --- |
| Source | Clouds C3, D3 |
| Biome and sky | Broad river and a lake with a wooded island; fairy woods to the south; farmland north. `fair`/`cloudy` |
| Monsters | A 6–12, C 24. **Killer sprites** (10/14/18), **Evil rangers** (8/12/18, the north bank camps), **Ogres** (18–30, d1, river crossings only). Three named water dragons (60) in the lake (Q-C13): a trap. Party 7 → 11. 135 hostiles, none inside the town buffer. Tres 1, L/T 2/1 |
| Town | **Rivercity** (hub; full services, boats and the skill row), built across the river on a great bridge. The robbers' den is under the bridge |
| Dungeons | Rivercity Robbers' Den (XD-21), **Darzog's Tower** (XD-12) on the lake island (boat or Water Walk, key-gated), Ogre Lair (XD-27), **Temple of Yak** (XD-06) in the fairy woods' dark south end (moved from X1; a return visit at 14–16, like MM6's Gharik's Forge) |
| Outdoor content | Obelisk; Sage's Fountain (+2 permanent Intellect); Shrine of Electricity; Danulf the Faery King's ring of stones; Tito's chapel; Medin's jetty; Ligono trapped in the surf at the rim (the **south edge is the world rim**); 2 evil-ranger camps; Captain Nystor's dock; Crodo's second bottle on the lakeshore |
| POI budget | Named items 17; add 23–33 generic devices to reach 40–50 (wells 4, camps 4, graves or ruins with a chest 4, signposts 4, one stat challenge) |
| Arrivals | X1 (east, the river road), X3 (west), X4 (north); boat down the river to Vertigo (X1) |
| Original lines | Rivercity's ads ("If you can read this ad, so can your customers." / "Pray, pay, and be healed today." / "What did you expect, money?" / "REAL adventurers try Deep Mine Alpha!"); the mirror tips ("If you say the name of a town to a mirror …", "say 'Warzone' to a mirror"); Flint's and the gym's teacher lines; Barok's tavern rumours; the drunk ("Get Lost! Can't you see I'm drinkin'?") |

### X3 Lifeforce Lagoon

| | |
| --- | --- |
| Source | Clouds C4, D4 |
| Biome and sky | Swamp, lagoon and dark marsh woods; the ruined Newcastle on a rise; Nightshadow in a perpetual mist (a local weather override: always overcast, the sun never reaches the town). `swamp` ground with pools |
| Monsters | A 10–15, C 32. **Swamp things** (20/26/32, d1), **Toads** (5–11, d3 at the edge), **Zombies/ghouls** around the Tomb, **Night bats** near Nightshadow. Party 13 → 16. 135 hostiles. Tres 2, L/T 4/2 |
| Town | **Nightshadow** (cursed vampire town), **Newcastle** (the party's castle site). From day one, outside the curse: a tavern-and-temple at Ebenezer's camp (WORLD_DESIGN §5.1) |
| Dungeons | Newcastle Keep (XD-13, staged), Tower of High Magic (XD-11), Tomb of a Thousand Terrors (XD-08), Nightshadow Crypt (XD-24) |
| Outdoor content | Obelisk; Mirabeth's lagoon rock; 3 sundials in Nightshadow and a sign "The Count wakes at nine and sleeps at nine."; Ebenezer's tent; Emerson's work yard (barrels, crates); an evil-ranger camp; a well of temporary resistance; swamp food trees |
| POI budget | Named items 15; add generic devices to reach 30–40 (two settlements and a camp; D-15 replaced the swamp band of 25–30) |
| Arrivals | X2 (east), X4 (north), X5 (west); mirror |
| Original lines | Count Du Monay's fee for the living; the rhymes "Only at night can you put up a fight." / "If the Dials are properly set, The count will definitely be upset." |

### X4 Burlock Savannah

POI band for this two-town map: 35–55 (MAP_CRAFT §6.2's town-hub band; D-20 replaced D-11.5's 30–45), counted as the shipped census counts (bound events chained within 400, one set piece one spot).

| | |
| --- | --- |
| Source | Clouds C1, C2, D1, D2 (Gargoyle Range in the north) |
| Biome and sky | Rolling savannah and jousting fields in the south, the river's upper reach, red dwarf hills; **Gargoyle Range** of bare peaks in the north; lava fields of D1 at the north-east edge. `fair`, dry tint |
| Monsters | A 10–16, C 30. **Burlock knights** at 14/20/26 (Jousters; the King's Guard 40 stays inside Castle Burlock), **Ogres**, **Gargoyles** (d1, the range). Party 11 → 15. 135 hostiles. Tres 2, L/T 4/2 |
| Town | **Castle Burlock** (royal seat, a castle BLV and a small walled village whose services do not need the Crusaders title), **Asp** (cursed; from day one its Travel Pit stables and a roadside temple work), Autumn Druid's grove |
| Dungeons | Castle Burlock (XD-07), Asp Undercroft (XD-25), Gargoyle Eyrie (XD-26), the Red Dwarf Mines' west adit (XD-02's second entrance, cleared from inside with a winch: once open, a permanent underground shortcut between X1 and X4 for Act II) |
| Outdoor content | Obelisk; Well of Might (temporary) and Olympian Fountain (+2 permanent Might); the jousting lists (a stat challenge); Carlawna's and Falagar's huts; Joe the Merchant's caravan (Merchant teacher); barbarian camp to burn; Captain Nystor's upriver landing |
| POI budget | Named items 15; add 15–25 generic devices to reach the town-and-wilderness band of 30–40 |
| Arrivals | X2 and X3 (south), X6 (west), X7 (east); stables |
| Original lines | Asp: Adam and Eve, Sarah Slither's lisp ("I'll ssslip your name into the guild rollsss"), the pedestal rhyme ("The southwest corner is where to start / Begin with red to tell them apart") |

### X5 Winterkill Tundra

| | |
| --- | --- |
| Source | Clouds A3, A4, B3, B4 |
| Biome and sky | Snowfields, frozen lakes and a snowy troll forest; the Land of the Giants in the south-west corner. **South-west is the world rim**, a glacier ending in the stars. `winter_overcast`, snow |
| Monsters | A 15–22, C 40. **Snow beasts and wolves** (d2), **Barbarians** (camps), **Trolls** (Troll Forest; Ice Troll tier). The Land of the Giants corner holds **cyclopes** (36–50) at d4: the face's first trap pocket. Party 24 → 28. 135 hostiles. Tres 3, L/T 6/3 |
| Town | **Winterkill** (ghost town), Glom the Gnome King's burrow (2 houses), Kai Wu's monastery (temple and training from day one) |
| Dungeons | Golem Dungeon (XD-09), Cave of Illusion (XD-10, two entrances), Ninja Pagoda (XD-22), Troll Warren (XD-23), **Darkstone Tower** (FD-03, sealed until the finale) |
| Outdoor content | Obelisk; Fountain of Great Protection (temporary AC); Waters of Great Magic; Shrine of Cold (Water resistance, permanent once); Thickbark the tree; Halon's water clock workshop; Winter Druid; cyclops outpost and barbarian camp to burn; the **Earth Reflector** on the rim |
| POI budget | Named items 17; add 11–18 generic devices to reach the snow band of 28–35 |
| Arrivals | X3 (east), X6 (north) |
| Original lines | Casper's bribe ("I may fall asleep with the roll book open. (wink, wink)"); "Acme Ghost Visualization System"; the gong rhyme and Randon's numbered list; the title "Ghostslayers Extraordinaire" |

### X6 Desert of the Sphinx

| | |
| --- | --- |
| Source | Clouds A1, A2, B1, B2 |
| Biome and sky | Desert of dunes and red mesas; the Barbaric Mountains; Castle Basenji on a cliff. **West is the world rim**: dunes pouring over the edge into the stars, with sand streaming off in the wind (particles). `clear`, `arid` theme |
| Monsters | A 22–30, C 50. **Sand burrowers** (30–45; worms surface near travellers), **Sand and elemental golems** (ruins), **Werewolves** around Basenji (no scorpions, D-31). Party 30 → 33. 135 hostiles. Tres 3, L/T 8/4 |
| Town | Saul's hermitage (urn), a caravan stop (tavern, stables); no full town: wilderness map |
| Dungeons | Castle Basenji (XD-14), The Sphinx (XD-15), Warzone arena (XD-20), Southern Sphinx (FD-02, sealed until Roland's amulet) |
| Outdoor content | Obelisk; oasis fountain (+2 permanent Endurance); Well of Accuracy; Shrine of Energy; bone fields; Arie's camp; Summer Druid; ruins with chests; the **Air Reflector** on the rim corner |
| POI budget | Named items 17; the wilderness band 20–30, cap 30 at L4 (D-31) |
| Arrivals | X4 (east), X5 (south); coach to the Warzone |

### X7 Mount Firestone: trap and endgame

| | |
| --- | --- |
| Source | Clouds E1, E2, F1, F2 (and the Lava Lake of D1) |
| Biome and sky | Volcanic badlands, lava rivers, ash fall; the Red Dwarf Range's southern slopes are mild and early (the Orc Caves' back exit, XD-05), the north is deadly. **North is the world rim** with lava falling into space. fair (Cloudside preset), `ashen` theme, ash fall on ~40 % of days (D-40) |
| Monsters | South slopes: orcs 5–10 (the trap map's safe edge; counted in Act I, D-40; D-5.2's "levels 20–30" is the party level for Sablewing's teaching). North: A 40–55, C 85: **acid and fire dragons**, **Lava golems**, **Great hydras**. 90 hostiles. Tres 5, L/T 10/5. Visible from X1 and X4; no main-path step before Act V |
| Town | none (wilderness); the abandoned dwarves' watch on the south slope (a note at the pay chest, D-40); Shangri-La's cleft opens from inside after the first exit (D-40) |
| Dungeons | Volcano Cave (XD-16) → **Shangri-La** (XD-17, hidden), **Dragon Cave** (XD-18, the hardest optional dungeon), **Dragon Tower and the Dungeon of Death** (FD-04, optional finale; the Dungeon of Death is its lower half, moved from X1), Orc Caves' back exit (XD-05, a back gate opened from inside) |
| Outdoor content | Obelisk; Shrine of Fire; Well of Speed; the Ever-Hot Lava Rock (Q-C14) on an island in a lava lake; demon idols; the **Fire Reflector**; Shangri-La's pyramid is reached only through the valley |
| POI budget | Named items 15; add 8–13 generic devices to reach the trap band of 22–28 |
| Arrivals | X1 (south), X4 (west) |

## 2. Darkside surface

Darkside maps share Darkside's sky: day and night, an amber day sky and a sun that weakens by story stage
(`xeen_darkside_day`, `_fading`, `_failing`; WORLD_DESIGN §4). Its levels start where Cloudside's middle is
(calibration: the second region of an open middle, not a second tutorial).

### D1 Castleview Vale: Darkside hub

| | |
| --- | --- |
| Source | Darkside A3, A4, B3, B4 |
| Biome and sky | River vale and grassland around a besieged walled town; the **Dark Grove**, a forest whose tallest tree carries a rope into the sky; acid pond; melon fields; a castaway's shipwreck on the river; Castle Kalindra on a rise to the south-west, **out of phase**: a translucent ghost of a castle until restored |
| Monsters | A 14–18, C 30. **Gremlins** (Darkside family 14/18/22), **Barbarians** (14–28; Yog's Sardaj camp, peaceful if Q-D12), **Arachnoids** (14/18/24) **and electrapedes** (Dark Grove). Party 18 → 21. 135 hostiles, none inside the town buffer. Tres 2, L/T 4/2 |
| Town | **Castleview** (hub, full services, pass at the gate); Castle Kalindra (staged) |
| Dungeons | Castleview Sewer (DD-01), Ellinger's Tower (DD-02, inside the walls), Castle Kalindra (DD-03), The Gremlin Court (DD-04), Western Tower (DD-05), Gemstone Mines (DD-10, west entrance) |
| Outdoor content | Obelisk; four gemsmith workshops; Luna's grove; Falista's hut; Justine's camp; Brother Reger's cell; well of +2 permanent Might; prayer shrine (temporary levels rescaled to +10 all stats until rest); Dark Grove rope (→ D7); the **travel pyramid** (→ Vertigo) outside the north gate |
| POI budget | Named items 20; add 20–30 generic devices to reach 40–50 |
| Arrivals | Pyramid; D2 (east); D6 (north, a long mountain road); stables; mirror |
| Notes | No fight within 4,096 (5,888 for a shooter) of the pyramid (D-142, D-161); no fight inside the town buffer. The gremlins' sabotage is visible: broken bridges, a burned mill |
| Original lines | "This bench reserved for Lyle the Pigeon Feeder"; "Ellinger has a great fondness for boots."; the gremlin complaint about Mayor Snarfblad; Eeried's guidebook on sale (also in Vertigo) |

### D2 Sprite Forest and Ogre Pass

| | |
| --- | --- |
| Source | Darkside C3, C4, D3, D4 |
| Biome and sky | Enchanted forest with glowing mushrooms and the great tree of the Temple of Bark; the Gemstone Range's foothills; Ogre Pass with two forts; Southern Tower in the woods |
| Monsters | A 16–22, C 38. **Sprites** (medusa and killer sprites, d2), **Dark wolves and sabertooths** (d2), **Ogres** (the pass, d3; peaceful if Q-D11). **Trolls** near the troll holes. Party 21 → 25. 135 hostiles. Tres 3, L/T 6/3 |
| Town | Nibbler's hollow; Sharla's treehouse village (sprite vendors: potions, a Light guild branch); no human town |
| Dungeons | Temple of Bark (DD-09), Troll Holes (DD-11, three pockets), Ogre Forts (DD-13), Southern Tower (DD-06), Gemstone Mines (DD-10, east entrance) |
| Outdoor content | Obelisk; Shrine of the Elements (+resistances); Forbidden Fruit hut (+2 permanent stat and a condition); genie lamp (the Monga melons are D1's, q-d9); troll holes as pits in the forest floor; hidden Leprechaun's pot of gold |
| POI budget | Named items 16; add 6–14 generic devices to reach the forest band of 22–30 |
| Arrivals | D1 (west), D3 (east) |
| Original lines | Sharla's three replies; the Forbidden Fruit messages ("the coconut of confusion", "the plum of unconsciousness") |

### D3 Sandcaster and the Aging Forest

| | |
| --- | --- |
| Source | Darkside E3, E4, F3, F4 |
| Biome and sky | Sandstone city at the desert's edge; **the Crossroads**, an open market; the Aging Forest (old trees, leaves fall all year) and the Howling Woods; the River of Wrath; Venom Pond. **East edge: the rim**, with the bright face's glow above it |
| Monsters | A 22–35, C 45 (D-28). **Cobras** (30/38/45, d1), **Mantis ants** as the A tier of a 22/30/38 crawler family, **Hell hornets** (35–50, the Aging Forest only, d1), **Sand burrowers** (30–45, scrub). Party 27 → 30. 135 hostiles. Tres 3, L/T 8/4 |
| Town | **Sandcaster** (wizard-ruled city, wizard quarter closed), **Crossroads** market |
| Dungeons | Sandcaster Sewer (DD-18), Wizard Quarter (DD-19), Eastern Tower (DD-07) |
| Outdoor content | Obelisk; Thaddeus's Fountain of Youth (dry until Q-D18); Cornelius the Leprechaun (outdoor teacher); Fountain of Great Protection; Celia and Derek's cottage (Clouds award link); fruit huts; Vespar's emerald handle in a ruin |
| POI budget | Named items 13; the two-town band 35–55 (D-28, as D-20's X4), cap 55 at L4 |
| Arrivals | D2 (west), D4 (north); stables; Lucio's boat (late) |
| Original lines | The Vulture Repellant stall and the street line that it does not work; Aladdin the Lamp Cleaner; Madame Gloriana the palm reader; the wizards' "sensitive to insults" warning; the bow teacher's "accuracy, accuracy, and accuracy" |

### D4 Lakeside and Blackfang

| | |
| --- | --- |
| Source | Darkside E1, E2, F1, F2 |
| Biome and sky | Great lake (Octopod Lake) with the **Isle of Lost Souls**; Snow River Rapids in the north; the Forest of Peril; Magic Mountain; **Castle Blackfang** on a crag in a storm of bats. North-east corner: rim |
| Monsters | A 26–35, C 50. **Gargoyles** (Magic Mountain), **Vulture rocs** as the A tier of a 30/38/48 bird family, **Octopods** (50–70) in the deep water only: the lake is the trap. Witches near Lakeside until Q-D22. Party 35 → 38. 120 hostiles. Tres 4, L/T 10/5 |
| Town | **Lakeside** (coven town), Xanthus and Slibo's wizard camp on Magic Mountain |
| Dungeons | Lakeside Coven and Sewer (DD-20), Dungeon of Lost Souls (DD-12, by ferry), Castle Blackfang (DD-14, griffin only), Gargoyle Lair (DD-23) |
| Outdoor content | Obelisk; Xanthus' fountain (+SP temporary); Leafpoint the tree (Arch Druid); Ector's woodpile; Mirabeth Point (a statue to the Clouds mermaid); well of magic resistance; genie lamps |
| POI budget | Named items 13; add 17–22 generic devices to reach the lake band of 30–35 |
| Arrivals | D3 (south), D5 (west); ferry; Lucio |
| Original lines | Before liberation: "These stairs once led to a tavern, but it was destroyed long ago."; "This boat under repair."; the potion-recipe skulls |

### D5 Desert of Doom and the Great Pyramid

D4–D5 crossing (D-36): at y 80, a level valley at 1,500 out of the Forest of Peril; D5's east edge continues D4's west border spans and heights, its arrival facing west.

| | |
| --- | --- |
| Source | Darkside C1, C2, D1, D2 |
| Biome and sky | The Desert of Doom and the Perishing Sands; the Quivering Forest on the highland edge; the Great Pyramid rising from the dunes; the Parabolic Barrier (a shimmering Ancient wall) in the north |
| Monsters | A 30–42, C 62 (D-49). **Iguanasaurus** (d3), wild cyclopes in the Quivering Forest; the People at Gurodel's hold (peaceful until war, not counted at load; D-49), **Griffins** (cliffs), great birds. Party 42 → 45. 110 hostiles. Tres 5, L/T 12/6 |
| Town | **Bosco's Hall** (dwarf hall, small BLV), Gurodel's giant hold |
| Dungeons | Great Pyramid (DD-15), Northern Tower (DD-08), Giants' Hall (DD-24), Bosco's Hall (DD-25), the Sandcaster Sewer's far exit |
| Outdoor content | Obelisk; the seven **enchanted boulders** (Q-D24) in two clusters (D-49); Shrine of Great Power; the Last Water, +2 permanent Accuracy (D-49); broken travel pyramid (story prop); genie lamps |
| POI budget | Named items 13; add 7–12 generic devices to reach the desert band of 20–25 |
| Arrivals | D4 (east), D6 (west) |
| Original lines | Gurodel's "Greetings, little ones." and the tax-collector reply choices verbatim; Bosco's "I dub thee royal taste tester" |

### D6 The Forbidden Zone

| | |
| --- | --- |
| Source | Darkside A1, A2, B1, B2 |
| Biome and sky | Volcanic waste and Ancient ruins; **two crashed escape pods**, one in a lava lake; Griffin Pass; the walled **Necropolis**; **Castle Alamar**, a fortress of metal and stone with energy fields. Ash fall. North-west corner: rim |
| Monsters | A 30–50, C 75 (D-49). **Gamma gazers** (Eyes 40/50/65), **Lava dwellers**, **Griffins**; robot patrols on Alamar's mesa behind the castle (none within 5,888 of the gate or the pyramid); lava dwellers on Corak's lake's north shore and in the moat's arms (D-164). Party 48 → 51. 110 hostiles, few and strong. Tres 5, L/T 15/8 |
| Town | **Necropolis** (city of the dead, pass required), Ambrose's camp at Griffin Pass |
| Dungeons | Castle Alamar (DD-17), Corak's Pod (DD-16), Sheltem's Pod (DD-22), Necropolis Sewer (DD-21), Alamar Depths (FD-01, after Alamar) |
| Outdoor content | Obelisk; Fountain of Super Resilience (temporary HP); barbarian archer camp (rows 11104/11105, D-49); a travel pyramid outside Alamar's gate (to Shangri-La after M30, D-50); mine entrances to the Forbidden Zone mines (small BLV pockets of DD-10) |
| POI budget | Named items 13; add 8–15 generic devices to reach the trap band of 22–28 |
| Arrivals | D5 (east), D1 (south, a long mountain road); mirror (no Lucio, D-5.3, D-49) |
| Original lines | Necropolis: the aging books, the "Food for the dead, keep warm." barrel, the skull's story of the two necromancers; Sandro's two lines |

## 3. Sky maps, planes and finale (open-air BLVs)

All use the MM9 open-air BLV route (`level_generation/projects/mm9r_common/outdoor_blv.py`, `devdocs/INDOOR_OPEN_SKY.md`):
cloud islands and causeways as geometry, `below_horizon: sky`, a fall trigger below the clouds that moves the party to
the surface map underneath at the matching position.

| Map | Content | Monsters (A–C) | Size | Notes |
| --- | --- | --- | --- | --- |
| **X8 Cloudreach** | Two archipelagos joined by a long rope bridge: the Witch Clouds (harpy nests, the explorer statue, offering statues) and the High Magic Clouds (flying feet, cloud golems, a sorcerer's observatory). Three rhyming statues | Harpies 14–24, Flying feet / Guardians 18–24, Cloud golems 50 (rare); 60 placed | ~ 60 % of an ODM | Reached from the Witch Tower (X1) and Tower of High Magic (X3) roofs; falls land on X1/X3 |
| **X9 Clouds of Xeen** | Slick's carnival on a cloud plaza (Slick's patter verbatim); roc nests; Castle Xeen's gate; rhyming statues | Rocs 38, Griffins 48, Cloud Golems 50; 50 placed (D-50) | ~ 70 % of an ODM | Reached from Darzog's Tower roof (X2); falls land on X2. Later the Dragon Clouds (Q-F1) are a sealed island here |
| **D7 The Skyroads** | Cloud roads linking floating rest stops; **Olympus** (city of the gods: "The people are so small they look like ants", Ligono waiting); the Sky Lake; elemental merchants; scarab sellers; sky bandits' toll ("This is a robbery …"); the **Megadragon** on the road to Alamar's roof; three causeways to Olympus; four tolls with peaceful bandits; scarab sellers paying in gems (permanent resistances); the Megadragon on Alamar's roof hatch at the end of its own road (D-58) | 50–75, Megadragon 125 (optional); 50 placed | ~ 1 ODM | Reached by the Dark Grove rope, tower roofs and Lucio's boats; the four corners lead to the planes |
| **P1 Fire, P2 Air, P3 Earth, P4 Water** | One compact plane each ("the Plane of Fire of Xeen" …; WORLD_DESIGN §1.1): a test of the element and a sleeper's chamber | 55–70, guardians 75; 30 each | S–M dungeon scale each | MM8's planes were whole ODMs; these are deliberately small: 26 × 26-cell open-air BLVs (Fire a lava crater, Air islands, Earth a bowl, Water a drowned temple); the test raises the guardians; the way up always open (D-58) |
| **P5 Clouds of the Ancients** | The finale: one ring of cloud road (29,137 to the shrine) past three Rest Stop huts, ten billboards naming New World Computing's games and the closed observatory; the Pharaoh's 'long road' note at the start by the stair house; the Pharaoh's shrine; after the ceremony the wedding pavilion (Roland, Kalindra, a treasure-6 gift, a disc back to the crown) (D-56) | none | small | Open-air BLV; ending cinematic `unification` (`evt.PlayCinematic`), then the completion certificate; falls to X5's `entrance:p5_fall` (D-56) |

## Dungeons

Size classes (WORLD_DESIGN §6, measured on all shipped MM7/MM8 BLVs): **S** 6–15 sectors, 7–20 M units², 15–30
monsters, 0–3 chests, 3–8 doors. **M** 20–45 sectors, 30–90 M units², 45–75 monsters, 3–7 chests, 6–16 doors.
**L** 50–75 sectors, 120–200 M units²; four set pieces only, carrying §0's 70–80 monsters plus their bosses (shipped
L dungeons hold 120–180; see WORLD_DESIGN §6). An S brief that grows past 15 sectors is cut or re-classed
as M; new S briefs carry the line "S: at most 15 sectors and 20 M units²" in their L1. Monster counts and levels follow
§0. "Story" marks main-quest dungeons; "Promo" promotion dungeons.

### Cloudside

| Code | Dungeon | Map | Class | Monster levels | Role | Set piece |
| --- | --- | --- | --- | --- | --- | --- |
| XD-01 | Joe's Warehouse | X1 | S (built; the upper bound of S) | 2–6, Wobbles 4 | Story M2 | A 16-sided cistern with six barred slime pens behind gates on one feeding lever; the invoice crate. Cellar north of the warehouse, loft beside the hall (briefs L3: 24 rooms, 11 M units²) |
| XD-02 | Red Dwarf Mines | X1, X4 | M | 3–10 | Story M3 | Cart trestle over a chasm and a funnel stope with a spiral of ramps and railed ledges; coloured stat pools (+2 permanent, one each), gold veins; carts are scripted rides until the studio has horizontal movers (briefs L3: 50 rooms, 33.5 M units²) |
| XD-03 | Deep Mine | X1 (by XD-02's mine cart) | M (as built) | 6–12, Clan King 18 | Story M3 | The Clan King's six-sided hall with four pillars and a stepped dais; a slag channel crossed by two bridges, with steps out of it; the escape shaft to the X1 hills (briefs L3: 37 rooms, 21.6 M units²) |
| XD-04 | Witch Tower | X1 | M | 4–14, Head Witch 20 | Story M4, Promo T1-A | A crooked tower: four floors each a quarter turn further round one tall cauldron shaft, every floor's balcony looking down into it; the Alacorn pier on a buttress up the shaft; a hoist cage; caged children; the key door (was "Rosebud"); roof exit to X8 (briefs L3: 32 rooms, 34.9 M units²) |
| XD-05 | Orc Caves | X1 | M (as built) | 4–10, Drum-Master 12 | Optional | The drum hall: terraces down to a bowl, the Drum-Master's scaffold reached by a gangway under fire; burn three drums; the chimney loop; Tam the captive (briefs L3: 45 rooms, 24.2 M units²) |
| XD-06 | Temple of Yak | X2 (moved from X1) | M | 14–28, Yak Master 35 | Story M10 (Megacredits) | Switch puzzles; a pool that sickens; the Elixir |
| XD-07 | Castle Burlock | X4 | M | 10–24 | Story M5–M7 | Throne room; the "Crusaders only" gate; Prince Roland's ceremonial armour; a throne that throws you into the sky; dungeon with ice trolls and a caged fire dragon (optional) |
| XD-08 | Tomb of a Thousand Terrors | X3 | M | 15–30 | Story M10 | Torture devices as interactive props; coloured juices |
| XD-09 | Golem Dungeon | X5 | M | 18–40, Diamond Golem 50 | Story M10 | Four halls: wood, stone, iron, diamond; each a puzzle (cut the branches, push blocks, set tumblers) |
| XD-10 | Cave of Illusion | X5 | M | 18–28 | Story M12 | Illusory walls (`translucent_faces` + no collision); a drain plug that empties the cave (water level mover); stat-selling skulls |
| XD-11 | Tower of High Magic | X3 | M | 18–32 | Story M13 | Alchemy floors with resistance brews; "Stairway to Heaven" to X8 |
| XD-12 | Darzog's Tower | X2 | **L** | 30–48, Darzog 55 | Story M21 | No spells inside (map flag); trapdoor floors; the six study books (+5 stat, rescaled from +20); Crodo's secret room; roof to X9 |
| XD-13 | Newcastle Keep | X3 | S (staged) | 16–24 (wood golems) | Story M8–M23 | Changes with each stage; the sword vault, password "laboratory" said plainly in Shangri-La |
| XD-14 | Castle Basenji | X6 | M | 24–45, Basenji Cult Leader 45 | Q-C8 | Werewolf kennels; readable scrolls (blessings and curses); "There wolf" door, its password on Arie's note |
| XD-15 | The Sphinx | X6 | M | 22–45 | Q-C9 | Body, head and the hieroglyph dungeon as one BLV; the name riddle at the head (Arie or a Basenji prisoner says "Its name is Golux"); the thrones |
| XD-16 | Volcano Cave | X7 | M | 42–58 | Q-C26 | The demon and devil skulls; exploding chests |
| XD-17 | Shangri-La | X7 (hidden) | town | — | Q-C26 | Open-air BLV valley: a hidden town (5 services, 10 residences, no monsters); the well 15,000 experience once per character (D-50, D-53); the pyramid to D6's Alamar gate after M30 (D-50) |
| XD-18 | Dragon Cave | X7 | M (few, strong) | 65–100, Dragon King 110 | Q-C25, optional | The dragon tax urn; the library of Dragon Lore; the Dragon King |
| XD-19 | Castle Xeen | X9 | **L** | 42–70, Xeen's Pet 75, Lord Xeen 85 | Story M35 | Guard-making machines and elemental generators (with elemental guards of four elements, D-47) that drop barriers; Xeen's aviary; the Sixth Mirror |
| XD-20 | The Warzone | X6 | arena | by tier | Arena | MM6–MM8 arena |
| XD-21 | Robbers' Den | X2 | S | 10–18 | Q-C3, Promo T1-E | Under the bridge; a vault with the tiara |
| XD-22 | Ninja Pagoda | X5 | S | 20–40 | Q-C4, Promo T1-D / Ninja | Five-storey pagoda (vertical), paper walls (destructibles) |
| XD-23 | Troll Warren | X5 | S | 18–28 | Q-C15 | Burn the warren from inside |
| XD-24 | Nightshadow Crypt | X3 | S | 30–40, Count Draco 45 | Q-C7, Promo Nosferatu | The coffin opens at night only |
| XD-25 | Asp Undercroft | X4 | S | 14–26 | Q-C5 | The transformer machine |
| XD-26 | Gargoyle Eyrie | X4 | S | 16–28 | Q-C10 | Vertical cave with ledges (ladders) |
| XD-27 | Ogre Lair | X2 | S | 12–20 | Q-C23 | — |

### Darkside

| Code | Dungeon | Map | Class | Monster levels | Role | Set piece |
| --- | --- | --- | --- | --- | --- | --- |
| DD-01 | Castleview Sewer | D1 | M | 10–20, Rooka the Rat Queen 24 | Story M16, Q-D5 | Five town shafts; the rat queen's nest |
| DD-02 | Ellinger's Tower | D1 | M | 14–24 | Story M17 | The moral question at the door; beholder bats; the password at the top (Ellinger's own name, given by Oorla) |
| DD-03 | Castle Kalindra | D1 | M (staged) | 26–45 (Scraps 70, optional) | Story M19–M27, Promo Champion | Out-of-phase wings behind shimmering walls; safes; the throne room |
| DD-04 | The Gremlin Court | D1 | S | 14–22, Gettlewaithe 24 | Q-D1 | A three-round court dialogue or a fight |
| DD-05 | Western Tower of Mok | D1 | M | 25–45, Cult Leader 45 | Q-D6, Promo Hero/Priest of Light | Entered at the top by the heretics' rope on D1's north wall of the tower (D-9.3); the heretics' altar |
| DD-06 | Southern Tower | D2 | M | 14–30 | Q-D19, Promo Assassin/Sniper | Thieves' den: gongs, the "open sesame" chest |
| DD-07 | Eastern Tower | D3 | M | 28–48 (Act IV, D-9.3) | Q-D18, Promo Archmage | Floating mages; the Jewel of Ages; the Griffin statuette (Q-D20, D-9.3) |
| DD-08 | Northern Tower | D5 | M | 40–62 | Q-D17, Promo Black Knight/Villain | The Voweless Knights' proverbs with the vowels removed (the answers' compilation sold in Castleview's library); the knights friendly after the oath; Ormond sells the answers (D-61) |
| DD-09 | Temple of Bark | D2 | M | 14–30 (Barkman 60, optional) | Q-D10, disks | A temple grown inside a giant tree; the "feed me" alcoves |
| DD-10 | Gemstone Mines (3 pockets) | D1, D2, D6 | S ×3 | 16–28 (A, B, Act III); C 40–50 (Act V, D-27) | Q-D7 | Gem rock veins; the God of Minerals |
| DD-11 | Troll Holes (3 pockets) | D2 | S ×3 | 18–38, Hobstadt 42 | Q-D13, Promo War Troll | You fall in; each pocket has one way out |
| DD-12 | Dungeon of Lost Souls | D4 (isle) | M | 35–55 | Story M24, Promo Minotaur Lord | Five "think positive" gates (dialogue choices that open doors); the labyrinth; the songbird |
| DD-13 | Ogre Forts | D2 | S | 18–30 | Q-D11 | Two forts in one BLV; burnable |
| DD-14 | Castle Blackfang | D4 | M (large: 70 monsters, 40–45 sectors) | 36–58, Count Blackfang 70 | Story M27 | Griffin landing on the walls (Ambrose's griffin both ways from D4's gate, D-42); coffins; the Queen in the dungeon |
| DD-15 | Great Pyramid | D5 | **L** | 42–65 | Story M28–M30 | Torch levers that wake the chapels' mummies, the registry lock (1701), a pad maze, the Pharaoh; optional number niches; the Pharaoh's lift after the first audience; the sky door to D7 after M30 (D-61) |
| DD-16 | Corak's Pod | D6 | S | 40–55 (few: 7, D-47) | Story M29, M32 | Starship interior; the stasis cipher, shown in plain words on the console; log computers |
| DD-17 | Castle Alamar | D6 | **L** | 50–75 | Story M33 | Conveyor rides to four Lava Heads that drop four energy fields; element sundials raising four bridges; the true-name gate; the trapdoor deck; Sheltem and Corak by cinematic; the roof hatch to D7 (D-61) |
| DD-18 | Sandcaster Sewer | D3 | M | 25–40 | Optional: Barticus' members' room; the long tunnel to D5 | Barticus' gym; the long tunnel to D5 |
| DD-19 | Wizard Quarter | D3 | M | 32–55, Xenoc 60, Morgana 60 | Q-D14, Promo Spy | Xenoc and Morgana's guild halls |
| DD-20 | Lakeside Coven and Sewer | D4 | M | 25–45, Head Witch 45 | Q-D22, Promo Warlock | Five prisoners; the guild (membership sold, or Naomi says the word); the dragon statuette |
| DD-21 | Necropolis Sewer | D6 | S | 40–62, Sandro 65 | Q-D23, Promo Lich/Priest of Dark | Sandro's heart in a green jar in the lowest culvert; Sandro falls once and waits, risen, by his bier (D-62) |
| DD-22 | Sheltem's Pod | D6 | S | 48–65 | Optional lore | The other ship's log (six pages); opens after M33 (D-62) |
| DD-23 | Gargoyle Lair | D4 | S | 30–45 | Q-D15 | Natural cave, no doors (D-39) |
| DD-24 | Giants' Hall | D5 | S | 38–58 (the People: 38/50/58, D-47) | Q-D16 | The bloody throne |
| DD-25 | Bosco's Hall | D5 | town | — | Q-D17 | Dwarf hall with services: a walk-in throne hall; forge, alehall, Earth guild and three residences (D-62) |
| DD-26 | Olympus Sewer | D7 | S | 48–65 | Q-D28 | The tribble door; a marble ring of channels round Cyrano's Pets Unlimited; the tribble door opens the offering vault (D-65) |

### Finale

| Code | Dungeon | Map | Class | Monster levels | Role |
| --- | --- | --- | --- | --- | --- |
| FD-01 | Alamar Depths | D6 | M | 55–80 (robots 62/75 placed, D-69) | Story M39 (Roland) | The castle's undercroft round the west maze: two levers, the Dragon Tower key, one skull door (the Cube), Roland's stasis vault a lift below, the bolted grate's way back; a second way in from D7's roof hatch after M33 (Q-D26's key, D-61) |
| FD-02 | Southern Sphinx | X6 | S | 55–75 (62–72 placed, D-57) | Story M40 (Picard, the Chime) |
| FD-03 | Darkstone Tower | X5 | M | 60–85 (onyx golems 62/72, Onyx Golem 85, D-57) | Story M41 |
| FD-04 | Dragon Tower and the Dungeon of Death | X7 | M | 65–100 | Optional Q-F1 (the tower), Q-F2 (its lower half, opened with Sandro's key) |

FD-05 is retired: the Dungeon of Death left X1 (decision of 2026-11-14) and is the lower half of FD-04, as
`reviews/SCALE_AND_DENSITY.md` §3 proposed.

### Totals

| | S | M | L | Dungeons (BLV) |
| --- | --: | --: | --: | --: |
| Cloudside XD (without the Shangri-La town and the arena) | 9 | 14 | 2 (Darzog's Tower, Castle Xeen) | 25 |
| Darkside DD (the DD-10 and DD-11 pockets as 3 each; without Bosco's Hall) | 14 | 13 | 2 (Great Pyramid, Castle Alamar) | 29 |
| Finale FD-01 to FD-04 | 1 | 3 | 0 | 4 |
| **Total** | **24** | **30** | **4** | **58** |

On top come 2 town BLVs (Shangri-La, Bosco's Hall), the arena, 3 sky maps, 4 planes and P5: **69 BLV files** (MM7 61,
MM8 45). 24 dungeons are on the main path (Cloudside 13, Darkside 8, finale 3), about 20 serve promotions, the rest are
optional, matching MM7/MM8's "a third to a half optional". 41 % are S (shipped: 45–52 % under 40 monsters); the
review's target of half S would also need XD-10, DD-02 and DD-06 to become S, which the adopted per-map table does
not do (HANDOFF, "Not reconciled").

### Original lines by dungeon

Each map carries at least three short original lines from its source map, quoted or closely paraphrased, listed in
its NOTES with the `aaze` reference (decision of 2026-11-14 on original text; `reviews/STORY_AND_ATMOSPHERE.md` §3).
The dungeons' placements:

| Dungeon | Lines |
| --- | --- |
| XD-01 | The invoice with its arithmetic ("Breeder Slimes, 1 mated pair 287 / 5 Doom Bugs at 145 each 725 / Total: 1012 gold"); a Plague Cult slogan painted on a wall |
| XD-02 | The dwarves' shopping list ("1 bottle orc's milk, 2 boxes of Dwarf biscuits …"); "There are many DEEP mines." at the Deep Line |
| XD-03 | "Robbers and thieves take a good look at your fate …" and "Dead men tell no tales." by the bones near the hoard |
| XD-04 | The skulls: "Feed me!", "Goblins back to work!" over the pens, the two vanity skulls in the coven's bedchamber, the levitate hint on the roof stair; a freed child's "I want to go home". The goblin slate is ours (WORLD_DESIGN §1.2) |
| XD-05 | The outpost wording for the drums ("… Destroy?", "… collapses in a heap of ashes, smoke, and smoldering timber.") |
| XD-07 | Castle Burlock's plaques ("Don't worry, be happy." …), Burlock's "NO MIRROR?!? Get out of my sight!", Roxanne's "I'm not a damsel in distress" |
| XD-08 | "Welcome to the Tomb of a Thousand Terrors. Insanity is our fame, undead is our game." |
| XD-09 | The plaque "Solve the wood, it's like a tree / Cut the branches and return to me …" |
| XD-17 | The hint NPCs (the hidden-camera joke as "the hidden crystal in the wall", the "laboratory" password, "The moons will align …") |
| XD-18 | The Dragon Tax urn's line and the Loremaster titles up to "Taxman Emeritus" |
| XD-20 | The arena master's lines (aaze0085:0–4), incl. "No. Goodbye..." for the lowest tier |
| DD-01 | Valio's diploma and "Hey, that's MY chest." |
| DD-03 | Guido's note ("Try 10,11,12 on the tougher safes"); "Beware of Scraps!" signs |
| DD-04 | Gettlewaithe's challenge and the three answers |
| DD-12 | "Never underestimate the power of positive thinking." at the entrance |
| DD-15 | The Prime Directive book at the top |
| DD-16, DD-22 | The pod logs |
| DD-17 | Alamar's propaganda statues, one per floor, and the crackling true-name statue |
| DD-20 | The five prisoners' lines, the last one's "(yawn)" |
| DD-26 | The tribble note |

## Layout sketches

Two sketches of the first maps show the intended composition. They are plans for review, not geometry: 128 × 128
terrain cells, north up, one character ≈ 4 cells. The X1 sketch is updated for 2026-11-14 (the west edge leads to X2,
no Temple of Yak); the review page still shows the first version.

### X1 Vertigo Meadows

```text
 N   hills ^^^^^^^ [Red Dwarf Mines]^^^^ [Orc Caves]  ^^^ X7 exit (north road)
     ^^ orc outpost *  (Deep Mine below; shaft head)       orc outpost *
 X2  ~~~~~~~~~~~~~~ Pitchfork Creek ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      | R
 <== river road +=================[ VERTIGO ]==== orchard road =========> | I
 (Rivercity)   |                 walls, river, bridge   (pyramid knoll)    | M
     Spring    |   Oslo's hut       mirror, square          Waters of      | .
     Druid o   |                   Joe's warehouse          Power  o       | s
               |  Orothin's isles ~~~ delta ~~~~                           | t
               |     Fountain of Ability o         Toad Meadow: Myra,      | a
               |                                    Valia's cottage        | r
   dead forest |  Derek's camp                     [WITCH TOWER]           | s
   (Walking    |      Celia's hut (zombie wood)       Wishing Well o       |
     Dead)     |                                         Water Reflector * |
 S  ------------------------------------------------------------------------
```

### D1 Castleview Vale

```text
 N   Western Tower [top, by the heretics' rope]  Dark Grove (rope to the sky) |  barbarian camp (Yog)
        gemsmiths ^ ^ ^              arachnoids, electrapedes  |      Kramer's caravan
                 Acid Pond             PYRAMID (from Vertigo) |      Vespar's tower
 W  ---------------------------------- north gate ------------+------------ road ==> D2
  rim   Luna's grove          [ CASTLEVIEW ]  walls, gremlins, |   melon fields
  edge                        Ellinger's Tower inside, sewer   |   (Nibbler's hollow and the
        Falista's hut   Queen's Gate (SW wall, D-23)           |   troll holes are D2's, d2.yml)
        Justine's camp                 |                       |
  [CASTLE KALINDRA, SW of the town] ghost castle on a rise    |   Hector's diamond shop
        river ~~~~~~~ shipwreck ~~~~~~~~~~~ river ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 S                    Brother Reger's cell     prayer shrine   Well of Luck
```
