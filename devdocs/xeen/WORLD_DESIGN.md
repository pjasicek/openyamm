# Xeen: world design

Proposal, 2026-11-12; revised 2026-11-14 for the user's decisions after the three reviews (README, "Decisions of
2026-11-14"; `reviews/`). Act I is built as a test (X1, XD-01 to XD-05); the rest is not. This file is the world
concept: what the world is, how it is laid
out, how the party moves through it, and what is borrowed from the source. Story and quests are in
[QUESTS.md](QUESTS.md), map sheets in [MAPS.md](MAPS.md), monsters and treasure in
[MONSTERS_AND_ITEMS.md](MONSTERS_AND_ITEMS.md), engine and production work in [PRODUCTION.md](PRODUCTION.md).

The sources are summarised in `research/`. They are World of Xeen (MM4 Clouds of Xeen, MM5 Darkside of Xeen and the
combined ending) read from `reference/mm4_5_world_of_xeen/unpacked/`, and measured MM6–MM8 calibration. The earlier MM5
projects in `level_generation/projects/mm5_*` are **not** the basis: they recreated MM5's square grid and produced an
empty map. Their inventories (`sites.csv`, `travel.csv`, chunk ownership) remain useful as a fact lookup.

## 1. The pitch in one paragraph

Xeen is a flat world, an Ancient construct with two inhabited faces. On the bright face, **Cloudside**, a usurper
calling himself Prince Roland has poisoned King Burlock's court and the land is falling to witches, cults and monster
nations. On the shadowed face, **Darkside**, the charming guest "Alamar" has stolen the Cube of Power, given Queen
Kalindra to a vampire and moved her castle out of phase. The party starts as survivors in Vertigo, earns the title of
Crusaders, and discovers through Burlock's suspicious advisor that the two faces are linked by Ancient pyramids. From
then on two threads run side by side: unmask and kill Lord Xeen on Cloudside, and restore Kalindra's kingdom on Darkside
until Corak can be smuggled into Alamar's fortress. They converge in a finale that wakes the four elemental sleepers,
frees the real Roland and unites the halves of the world. The game is played as an MM6–MM8 game: open outdoor maps
with towns, houses, guilds, stables and boats; short dungeons and a few large set pieces; the MMerge class system with
promotions; the MM6–MM8 item and treasure-level curve.

**Voice.** Xeen talks in short lines. Signs, plaques and townsfolk are deadpan and often funny: the con man's slogan,
the drunk who will not be disturbed, a plaque that says "Don't worry, be happy" in a royal castle. Danger is played
straight; the world winks around it. Cloudside is cheerful and a little silly. Darkside is drier and satirical (a
tyrant's propaganda statues, a palm reader, Vulture Repellant that does not work). Quest text is one or two sentences.
No epic inscriptions, no lore dumps outside the Ancient logs and the Bark scriptures. Short original MM4/MM5 lines
(signs, NPC quips, jokes, Joe's invoice, the guidebook) may be quoted or closely paraphrased; longer text is rewritten
in the original's spirit (decision of 2026-11-14). Every map carries at least three short original lines from its
source map, listed in its NOTES with the `aaze` reference; MAPS.md names them per map. World-wide stock lines: "There
is nothing on, in, or under the bed." on beds, "The water is cool and refreshing." on wells, and the drunk ("Get Lost!
Can't you see I'm drinkin'?") in Vertigo, Rivercity and Sandcaster. Eeried's guidebook ("The World of Xeen on 30 gold
a day") is a readable book sold in Vertigo and Castleview, in chapters by face.

### 1.1 Xeen and the other worlds (assumed, the user may change)

Xeen is a separate world, an Ancient nacelle with its own sun. It is reached only from its new-game card and has no
ship, portal or Town Portal link to the MM6–MM9 continents. The logs keep the source's names (Terra, VARN, CRON, the
Ancients, Corak, Sheltem). Nothing ties Xeen's events to Enroth's dates, and no NPC mentions the Kreegan. The ending is
Xeen's own: Corak and Sheltem destroy each other in Castle Alamar (M33), the halves unite, and Roland marries
Kalindra. Xeen's elemental planes are "the Plane of Fire of Xeen" and so on, with their own map stems and names, never
MM8's planes.

The party is native to Xeen: the Newcastle survivors who received Crodo's dreams (QUESTS M1), not the Terran crew of
MM5's backstory. Darkside lines that assume strangers from the sky are reworded to "strangers from the other side".

### 1.2 Other assumptions (the user may change)

- **Darkside's amber days** (§4): day and night with an amber day sky and a failing sun, instead of perpetual dusk.
- **The goblin slate** in XD-04 ("HOW TO BE A PROPER GOBLIN. 1. Never say please. 2. Never wash. 3. Forget your
  name." with Rosebud's name scratched in the corner) is ours, not the original's. It stays, recorded as ours in
  XD-04's NOTES, with the original's witch-tower lines beside it (MAPS, "Original lines by dungeon").

## 2. Decisions this design makes (each open to the user's veto)

| # | Decision | Why |
| --- | --- | --- |
| D1 | **One world package, `xeen`, with two faces.** Each face behaves like a continent for Town Portal pages and loading screens, but they are one world, one save, one new-game card | The source is one game with one ending (World of Xeen). Two packages would duplicate everything that links the halves |
| D2 | **New maps, not a recreation of the MM4/MM5 grids.** Each outdoor map is one region of the source (2×2 or 2×3 original squares), keeping its towns, landmarks, relative directions and story relations, but laid out fresh at MM6–MM8 scale | Square-by-square conversion gives filler and the wrong town scale (MM5 critique, `research/MM5_DARKSIDE_CONTENT.md` §7) |
| D3 | **MM6–MM8 style, not MM9 style.** Heightfield ODMs for the surface with towns inside them, house dialogue shops, guild houses, stables and boats, spawn-plus-placed monsters, Fly allowed | User preference. MM9's open-air BLV route is used only where a heightfield cannot work: the sky maps, the elemental planes and the hidden valley of Shangri-La |
| D4 | **Start on Cloudside; Darkside opens early (the Pyramid Sigil at about level 14; D1 is set for arrival at 15–18) and is played in parallel** | MM4 starts easy and MM5 also starts easy; played back to back the curve resets. Interleaving makes Darkside the second region of an MM7-style "open middle", not a second tutorial |
| D5 | **Story kept, grid tricks and number inflation dropped.** Rewards rescaled to MM6–MM8 (no +5 permanent levels, no +250 HP wells, no 5M xp quests). Grid-only puzzles (step teleports, facing tricks, runaway chests) are replaced with movers, levers and dialogue | MM6–MM8 balance and engine; `research/MM4_CLOUDS_CONTENT.md` §5, `research/MM5_DARKSIDE_CONTENT.md` §6 |
| D6 | **Composite promotions with the MM7 Light/Dark second tier**, assigned to existing Xeen side quests where possible | MM9's composite model needs about a dozen quests instead of 27; Xeen has natural "light" (crown, Corak) and "dark" (Sandro, thieves, coven) factions |
| D7 | **Two restoration projects as the long-running "Harmondale"**: Newcastle is built on Cloudside with King's Megacredits; Castle Kalindra is restored on Darkside with Energy Disks | Both are in the source, both pace the midgame and both give the party a home with services |
| D8 | **Cursed towns liberate into working towns.** Asp, Winterkill, Nightshadow, Lakeside and Sandcaster's wizard quarter start hostile or closed and open their houses after their quest | The most distinctive structural idea in the source; it gives visible progress and makes small towns worth revisiting |
| D9 | **The world's edge is visible.** Maps on the rim of a face end in a cliff above a starfield, not in mountains or sea | The single strongest visual identity of Xeen, and cheap with the existing sky system (`below_horizon: sky`) |

Questions the user should answer before production are listed in [README.md](README.md#open-questions).

## 3. Shape of the world

### 3.1 The two faces

Each face is a 3-column, 2-row arrangement of regions, the same orientation as the source grids (north up, A–F west to
east). Cloudside has seven surface maps because its south-centre band (Rivercity, Darzog, Newcastle, Nightshadow) is
too dense for one map. Darkside has six. Rivercity (X2) lies next to Vertigo, so that the first road hop from the
start leads to the hub (decision of 2026-11-14: a road joins Vertigo Meadows to X2); in the source both Rivercity and
the Lagoon border Vertigo's squares.

```text
CLOUDSIDE (bright face)                                   DARKSIDE (shadowed face)

+-----------------+-----------------+-----------------+   +-----------------+-----------------+-----------------+
| X6 DESERT OF    | X4 BURLOCK      | X7 MOUNT        |   | D6 FORBIDDEN    | D5 DESERT OF    | D4 LAKESIDE &   |
| THE SPHINX      | SAVANNAH        | FIRESTONE       |   | ZONE            | DOOM            | BLACKFANG       |
| Basenji, Sphinx | Castle Burlock, | Volcano Cave,   |   | Necropolis,     | Great Pyramid,  | Lakeside, Isle  |
| Warzone arena   | Asp, Gargoyles  | Dragon Cave     |   | Alamar, pods    | Northern Tower  | of Lost Souls   |
| L 22-30 (C 50)  | L 10-16 (C 30)  | S 5-12/N 40-55  |   | L 38-50 (C 65)  | L 32-42 (C 55)  | L 26-35 (C 50)  |
+-----------------+--------+--------+-----------------+   +-----------------+-----------------+-----------------+
| X5 WINTERKILL   | X3 LIFE-| X2 RIVER-| X1 VERTIGO    |   | D1 CASTLEVIEW   | D2 SPRITE FOREST| D3 SANDCASTER & |
| TUNDRA          | FORCE   | CITY     | MEADOWS       |   | VALE            | & OGRE PASS     | AGING FOREST    |
| Winterkill,     | Newcastle| Rivercity| Vertigo,     |   | Castleview,     | Temple of Bark, | Sandcaster,     |
| Golem Dungeon   | Nightsh.| Darzog,  | Witch Tower,  |   | Kalindra        | Troll Holes     | Crossroads      |
|                 |         | Yak      | dwarf mines   |   |                 |                 |                 |
| L 15-22 (C 40)  | L 10-15 | L 6-12   | L 2-5 (C 12)  |   | L 14-18 (C 30)  | L 16-22 (C 38)  | L 20-28 (C 45)  |
+-----------------+---------+----------+---------------+   +-----------------+-----------------+-----------------+
  START: X1 (Vertigo)                                        ARRIVAL: D1 (Castleview pyramid)
```

"L" is the A-tier monster level range of the map's encounter families and "C" the highest C-tier level. Levels,
party levels and monster counts per map are the adopted table in [MAPS.md §0](MAPS.md#0-progression-per-map)
(`reviews/COMBAT_AND_PROGRESSION.md` §5.1, adopted 2026-11-14).

Map roles: **start pocket** X1; **hubs** X2 and D1; **town maps of the middle** X3, X4, D2, D3; **wilderness** X5, X6,
D4, D5; **trap and endgame** X7, D6. Hostiles at load by role are in MONSTERS_AND_ITEMS §3.

Above the faces sit the **sky maps**, reached through tower roofs and celestial boats, and beyond them the **elemental
planes** and the **Clouds of the Ancients**:

| Layer | Map | Reached from | A-level |
| --- | --- | --- | --- |
| Cloudside sky | **X8 Cloudreach** (the Witch Clouds and High Magic Clouds as one archipelago) | Witch Tower roof (X1), Tower of High Magic roof (X3) | 14–30 |
| Cloudside sky | **X9 Clouds of Xeen** (Castle Xeen, Slick's carnival, roc nests) | Darzog's Tower roof (X2) | 35–55 |
| Darkside sky | **D7 The Skyroads** (Olympus, Lucio's boats, the Megadragon) | Dark Grove rope (D1), tower roofs, Lucio's boats | 50–75 |
| Planes | **P1–P4 Fire, Air, Earth, Water** (small, one sleeper each) | Falls from the four Skyroad corners | 55–70 |
| Finale | **P5 Clouds of the Ancients** | Darkstone Tower seal (X5) | — |

Falling off a sky map's edge lands the party on the surface map below it (with falling damage unless Feather Fall is
up), exactly as in the source. This replaces walls at the sky maps' edges and makes the layering legible.

### 3.2 Map count against calibration

| | This design | MM7 | MM8 | Target from calibration |
| --- | --: | --: | --: | --- |
| Surface outdoor maps (ODM) | 13 | 13 | 9 | 9–13 per world; Xeen is two games, so the top of the range |
| Sky / plane / special outdoor-like maps | 3 sky + 4 planes + 1 finale (open-air BLVs, compact) | 0 | 4 planes + PBP | 1–4 gated zones |
| Dungeons (BLV) | 58 (24 S, 30 M, 4 L; §6 and [MAPS.md](MAPS.md#dungeons)) + 2 town BLVs + the arena | 61 | 45 | 40–60, about half small, 2–4 large |

A **lean variant** that cuts production by about a fifth is given in [PRODUCTION.md](PRODUCTION.md#lean-variant): merge
X3 into X2, merge D5 into D6, one Cloudside sky map, one shared elemental plane.

### 3.3 How the faces connect

| Link | How | When it opens |
| --- | --- | --- |
| Cloudside ↔ Darkside | **Travel pyramids**. The pyramid outside Vertigo (X1) and the one outside Castleview (D1) are a pair. Shangri-La's pyramid (X7) and the one in Castle Alamar's dungeon (D6) become a second pair late | Main quest step M7: Artemus gives the Pyramid Sigil (≈ level 14) |
| Inside a face, neighbours | Map-edge travel, 5 days (wilderness edges 7) | Always |
| Inside a face, towns | **Stables** (Vertigo, Rivercity, Burlock; Castleview, Sandcaster, Castle Kalindra after stage 4) and **boats** (Rivercity's Captain Nystor on the Great River and lakes; Lakeside's ferry to the Isle of Lost Souls) | Always, schedule-bound |
| Sky | **Celestial boats** of Lucio the Boatman (Darkside sky ↔ Castleview, Sandcaster, Lakeside, Olympus). Tower roofs are one-way up; falls are one-way down | Lucio: Chosen Ones (M30) |
| Fast travel | **Mirrors**: every town has a magic mirror that works as a free transport house to every *discovered* mirror on the same face. Town Portal and Lloyd's Beacon work normally on the surface | Cloudside mirrors from the start; Darkside mirrors after Castle Kalindra stage 4 (as in the source) |
| Arena | The **Warzone** (X6), coach once a week from Rivercity and Castleview | Always |

Town Portal destinations (6 per face, calibration rule): Cloudside: Vertigo, Rivercity, Castle Burlock, Winterkill,
Nightshadow, Newcastle. Darkside: Castleview, Castle Kalindra, Sandcaster, Lakeside, Necropolis, Olympus. Each is unlocked
by touching the town's mirror.

### 3.4 Flight

MM6–MM8 Fly stays (decision D3), with these rules so it does not skip the story:

- Sky maps and planes are open-air BLVs: **Fly is not cast there**; the clouds are the floor ("the winds of the high
  clouds tear at spellcraft"). Falling is the only way down.
- Story fortresses (Castle Xeen, Castle Blackfang, Castle Alamar, Darzog's Tower, Olympus) are entered through BLV
  doors or scripted transitions only; their exterior models have no walkable roofs.
- Castle Blackfang's exterior is wrapped in a storm of bats that knocks a flying party to the ground; the only way in is
  Ambrose's griffin (a scripted transition). This keeps the source's set piece.
- Ordinary outdoor maps: flying over a desert or a lake is allowed and is part of the late-game feel.

If the user prefers the MM9 rule (no Fly, Fleet Foot), these restrictions simply disappear; nothing else in the design
depends on it.

## 4. Visual identity per face

| | Cloudside | Darkside | Sky maps | Planes |
| --- | --- | --- | --- | --- |
| Light | Normal day/night; warm, MM6/MM7 brightness | **Amber days and a failing sun** (assumed, the user may change; `reviews/STORY_AND_ATMOSPHERE.md` F1). Darkside keeps day and night (its story needs them: the vampire Queen can only be carried out after nightfall). By day the sky is a low amber-gold cloud band under a pale, small sun; nights are dark with many stars. Through Acts III–V the sun weakens as Alamar steers Xeen away: three data presets (`xeen_darkside_day`, `_fading`, `_failing`) are chosen by main-quest qbits (M17, M27), and the sky returns to full strength after M33 (Sheltem defeated). See PRODUCTION E8 | Bright, high sun, cloud sea below (`below_horizon: sky`) | One theme each: `plane_fire`, `plane_air`, `underwater`, a new earth preset |
| Palette | Green south-east, river blue-green centre, white south-west, ochre north-west, black-red north-east | Desaturated greens, slate rock, glowing fungus and crystal accents; lamps and windows burn all day only in the failing-sun stage | Cloud white, gold, sky blue | Element colours |
| Architecture | Half-timbered towns (MM6 lineage); royal castles of white stone; witch towers of black timber | Stone and slate towns built low; Sandcaster sandstone; Ancient metal surfacing in the north-west | Marble (Olympus), cloud-stone causeways, rope bridges | Crystal, basalt, ice, coral |
| Signature view | The **world rim**: a meadow ending in a cliff above the stars (X1 east coast, X5 south-west, X6 west, X7 north) | The **rim lights**: the bright face's glow showing above the rim at the edge of D3 and D4; the crashed pods' lava glow in D6 | Looking down through gaps in the clouds at the surface map | — |
| Weather | Rain, snow in X5, ash fall in X7 | Rare rain, mist, ash fall in D6 | Wind, no rain | — |

The world rim is the cheapest high-value feature in the design: terrain stops in a cliff at the rim side of a rim map,
the sky preset renders below the horizon, and a fall over the edge is a death trigger ("you fall from the edge of the
world"). It needs no new engine work beyond the edge-fall trigger.

## 5. Towns and services

Calibration (`research/MM678_CALIBRATION.md` §7): the start and the hub get the full service set, regional towns 6–9
services, wilderness 0–3; 13–20 residences per town is typical. Xeen's town names and several of its shop names are
kept for flavour.

### 5.1 Cloudside

| Town | Map | Role | Services at full strength | Res. | Special |
| --- | --- | --- | --- | --: | --- |
| **Vertigo** | X1 | Start pocket; walled river town in the green south-east | Norman's Ironworks (W), Vertigo Armoury (A), Gilbert's Hexes (M), an alchemist, Fire/Air/Water/Earth guilds, the Slime Temple → renamed after the pest quest, Lady Geraldine's Tavern, bank, Thylon's Training, stables, mirror, **Adventurer's Inn** (roster) | 18 | Joe the Exterminator's shop and warehouse (the scam), Mylo's Maps, a money tree in the square |
| **Rivercity** | X2 | Hub; a bridge city across the Great River, crime-ridden | Rivercity Smithing (W), (A), Witch's Cauldron (M), alchemist, Pray N Pay (temple), Bull's Tavern, The Bank, Street Fightin' (training), Body/Mind/Spirit guilds, **boat** (Captain Nystor), stables, mirror | 30 | Skill school row: Arnold's Gym, Martial Training, Lindon's Temps (paid work); robber gang, sorceresses, Captain Yang's knights |
| **Castle Burlock** | X4 | Royal seat (a castle BLV with a small walled village outside) | Royal Armoury (W/A), temple, training, stables, **Throne room** | 8 | Crusaders-only gate; King, Artemus, Emerson, Roxanne, "Prince Roland" |
| **Asp** | X4 | Cursed: the townsfolk are turning into snakes | Before: nothing. After: Snake Oil (alchemist), Scale House (A), Asp Guild (Earth/Body), Travel Pit (stables), mirror | 10 | Colour-pedestal puzzle and the transformer (Q-C5) |
| **Winterkill** | X5 | Ghost town in the snow | Before: the Mindmeld Guild only. After: tavern, temple, inn, Mind/Dark guilds, mirror | 12 | Gongs summon ghost waves (Q-C6) |
| **Nightshadow** | X3 | Vampire town; never sunny | Before: Moon Guild (Dark) only, open at night. After: temple, tavern, Treasure Trove (M), Gnome Home (residences), mirror | 10 | Sundials, the Count's coffin (Q-C7) |
| **Newcastle** | X3 | The party's castle, built in stages | Stage 1 walls: nothing; stage 2 keep: smith, training; stage 3 dungeon dug: temple, bank, "your well" | — | See QUESTS §4.1 |
| **Shangri-La** | X7 (hidden, open-air BLV valley) | Secret utopia behind the Volcano Cave | Arm and Hammer (W/A), Earth Temple, Tavern Xanadu, Light guild, **Public Library** (grandmaster teachers), +1 level well rescaled | 8 | Hint NPCs; Jack Alltrades; the second travel pyramid |
| Hamlets | X2, X5, X6 | Waypoints | tavern, stables or boat; 1–3 houses | 3–6 | Druid groves, hermits, Saul's urn |

Every cursed or unbuilt town has one working service at the edge from day one, outside the curse
(`reviews/SCALE_AND_DENSITY.md` §9): X3 a tavern-and-temple at Ebenezer's camp, X4 Asp's Travel Pit (stables) and a
roadside temple, X5 Kai Wu's monastery as temple and training. Castle Burlock's village services do not need the
Crusaders title (only the throne room does). Each cursed town keeps one open house with its source guildmaster's joke:
Asp's Sarah Slither, Winterkill's Casper, Nightshadow's Count Du Monay.

**Training halls and caps** (`reviews/COMBAT_AND_PROGRESSION.md` §5.2, adopted 2026-11-14): Vertigo (Thylon's
Training) 10 (×10), Rivercity (Street Fightin') 25 (×20), Castle Burlock 40 (×25), Castleview 40 (×25), Newcastle
stage 2 60 (×30), Sandcaster 80 (×40), Castle Kalindra stage 4 200 (×50), Olympus unlimited (×80). Kai Wu's monastery
(not in the review's list) trains to Castle Burlock's cap, 40 (×25).

### 5.2 Darkside

| Town | Map | Role | Services at full strength | Res. | Special |
| --- | --- | --- | --- | --: | --- |
| **Castleview** | D1 | Darkside hub; besieged human town | smith (W), armourer (A), magic shop, alchemist, temple, tavern, bank, training, Fire/Air/Water/Earth/Body guilds, stables, mirror, Adventurer's Inn, **travel pyramid** outside | 28 | Gremlin court of Gettlewaithe; jail; Public Storage chest puzzles; the Drawkcab monks; Castleview Sewer |
| **Castle Kalindra** | D1 | The Queen's castle, out of phase; restored in four stages | Stage 4: smith, temple, bank, training, stables, mirror network switch | — | See QUESTS §4.2 |
| **Sandcaster** | D3 | Sandstone merchant city ruled by evil wizards | W, A, M, alchemist, temple, tavern, training, Mind/Spirit/Light guilds, stables (caravan), mirror. **Wizard quarter** closed until Astra's quest; then the Dark guild and a second magic shop open | 26 | Skill-school town (Navigator, Linguist, Merchant teachers); Natasha the Enchantress; Sandcaster Sewer and Barticus' gym |
| **Crossroads** | D3 | Open-air market where six roads meet | MM9-style stalls: food, robes, necklaces, belts, boots, Caleb the inventor | 0 | Uses street vendors (generalised MM9 vendor code) or six small house doors |
| **Lakeside** | D4 | Coven-ruled lakeshore town | Before: Lakeside guild only (riddle). After: tavern, smith, temple, ferry to the Isle of Lost Souls, mirror | 10 | Five prisoners; children turned into goblins |
| **Necropolis** | D6 | City of the undead; a walled necropolis that the living may enter with a pass | Dark guild, Necromancer house (promotion), temple of the dead (resurrection, cheaper Raise Dead), black-market magic shop, mirror | 6 | Sandro the Lich; deadly aging books |
| **Olympus** | D7 | City of the gods on the Skyroads | smith, tavern, temple, training, Light/Spirit guilds (grandmaster), mirror, Lucio's dock | 6 | Soul Storage; prophecy statues; Sheltem's true name |
| **Bosco's Hall** | D5 | Dwarf hall dug into the highlands (small BLV) | smith, tavern, Earth guild | 2 | Bosco the Dwarf King |

### 5.3 Teachers, hirelings and NPC density

- **Teachers:** about 120 offers (calibration 100–145), three per skill (Expert, Master, Grandmaster in different towns,
  Grandmaster usually late or remote: Shangri-La, Olympus, Necropolis, Sandcaster's quarter). Town teachers live in
  houses as in MM6–MM8. Xeen's wandering teachers become **outdoor teachers** on the road, MM9-style, where the source has
  them: Freeda the Mountaineer on a pass (Bodybuilding), Cornelius the Leprechaun in the Aging Forest (Perception),
  Saul at his urn (Meditation), Rialdo the Ranger (Bow), Martin and Magneto on Rivercity's skill row. This needs the MM9
  street-teacher loader generalised (PRODUCTION §2).
- **Xeen secondary skills → MM6–MM8 skills:** Arms Master → Armsmaster; Body Builder → Bodybuilding; Merchant →
  Merchant; Spot Secret Doors and Danger Sense → Perception; Prayer Master → Meditation; Prestidigitator → Learning;
  Astrologer → Identify Item; Cartographer → the free Wizard Eye map (flavour only); Swimmer → Water Walk scrolls sold
  by Darlene; Mountaineer, Pathfinder, Navigator, Direction Sense have no equivalent and are not used as gates. Linguist
  becomes a party-wide unlock: reading the Book of Languages in Castle Burlock makes the rhyming statues and runes
  readable.
- **Hirelings:** MM7/MM8 street peasants with professions, plus an **Adventurer's Inn roster** in Vertigo and Castleview
  (Xeen's inns are where characters are recruited). Roster characters from both faces, including Xeen's iconic
  pre-made party names as flavour.
- **Named NPCs:** target 300–380 across both faces (calibration 300–450); two thirds with topics. MM5's one-line joke
  NPCs become rumour topics, not houses (MM5 critique point 3).

## 6. Dungeons in one view

Size classes, measured on all shipped MM7/MM8 BLVs (`reviews/SCALE_AND_DENSITY.md` §1; decision of 2026-11-14):
**S** 6–15 sectors, 7–20 M units², 15–30 monsters, 0–3 chests, 3–8 doors: a 10–20 minute visit (the Wine Cellar,
Zokarr's Tomb, a Barrow). **M** 20–45 sectors, 30–90 M units², 45–75 monsters, 3–7 chests, 6–16 doors (the Temple of
the Moon, White Cliff Cave). **L** 50–75 sectors, 120–200 M units² (Castle Harmondale, the Nighon Tunnels). An S brief
that grows past 15 sectors is cut or re-classed as M; it does not stay "S". Doors: S 3–8, M 6–16, L up to 25; pens and
gates count. XD-03 and XD-05 count as M as built; XD-01 stays the upper-bound S.

**Four L set pieces** instead of six: Darzog's Tower, Castle Xeen, the Great Pyramid and Castle Alamar. Castle
Blackfang becomes a large M (70 monsters, 40–45 sectors) and the Dragon Cave an M of few, strong dragons. Shipped L
dungeons hold 120–180 monsters; the four Xeen ones carry the adopted per-map table's 70–80 plus their bosses (about
1.2–1.5 per sector), so the late game stays inside its experience budget (MAPS §0). The full list with levels, story
role and set pieces is in [MAPS.md](MAPS.md#dungeons).

| Face | S | M | L | Main path | Total |
| --- | --: | --: | --: | --: | --: |
| Cloudside (without Shangri-La and the arena) | 9 | 14 | 2 (Darzog's Tower, Castle Xeen) | 13 | 25 |
| Darkside (mine and hole pockets as 3 each; without Bosco's Hall) | 14 | 13 | 2 (Great Pyramid, Castle Alamar) | 8 | 29 |
| Finale (both faces) | 1 | 3 | 0 | 3 | 4 (+ 4 planes, + Clouds of the Ancients) |
| **Total** | **24** | **30** | **4** | **24** | **58** |

With 2 town BLVs, the arena, 3 sky maps, 4 planes and P5 the world has 69 BLV files (MM7 61, MM8 45). Vertigo Meadows
(X1) keeps four dungeon sites (XD-01; XD-02 with XD-03 below it; XD-04; XD-05); the Temple of Yak moved to X2 and the
Dungeon of Death became the lower half of FD-04 on X7 (decision of 2026-11-14).

The source's many-floor towers (four floors each) become **one BLV per tower** with real vertical architecture: a
central stair or lift core and floors stacked around it, as MM6's Temple of Baa fits seven levels in a small footprint.
The source's split mine and hole pockets (Dwarf Mines 1–5, Gemstone Mines, Troll Holes) become a few small BLVs, each
with one entrance, not a joined network.

## 7. Pacing in one view

| Act | Faces | Party level | Main content | Ends with |
| --- | --- | --- | --- | --- |
| I. Vermin | Cloudside X1 | 1–7 | Vertigo's pests and Joe's scam; dwarf mines; Witch Tower; Crusaders | Crusader title, first promotions |
| II. The King's Crusaders | Cloudside X2–X4 | 7–20 | Burlock's audience; Artemus's suspicion; Newcastle land; Megacredits from three dungeons; the key chain through the Cave of Illusion and the Tower of High Magic | The Pyramid Sigil; Darkside opens |
| III. The Land Below | Darkside D1–D3 (Cloudside continues: X5 and its dungeons) | 18–30 | Castleview; the Pharaoh's orb; Ellinger; Energy Disks from negotiated factions and towers; Kalindra stages 1–2; Sandcaster | Kalindra stage 2, Megan's songbird quest |
| IV. Unmasking | both | 30–42 | Darzog's Tower, Crodo freed: "Roland" is Lord Xeen. Songbird, Dimitri, Ambrose, the bridle, Castle Blackfang, the Queen cured. Newcastle's dig permit and the Xeen Slayer Sword | The Pyramid key; the Slayer Sword |
| V. Two Thrones | both | 42–55 | The Great Pyramid and the Dragon Pharaoh; Corak's pod; Chosen Ones; Olympus and the Soul Box; Clouds of Xeen and Castle Xeen (Scepter); Castle Alamar (Cube) | Lord Xeen and Sheltem defeated (either order) |
| VI. One World | both + sky + planes | 55–65 (optional content to 70) | Reflectors at the four Cloudside corners; four elemental sleepers; Roland freed in Alamar's dungeon; Southern Sphinx and the Chime; Darkstone Tower; Clouds of the Ancients | Unification ending, completion certificate |

Optional late content runs alongside V–VI: the Dragon Cave and the Dragon King, the Megadragon, the Dragon Tower with
the Dungeon of Death below it (FD-04) and the Dragon Clouds, the Warzone arena's top tier. Act levels are a full clear
of the adopted per-map table (MAPS §0); as played, the party ends at about 62–65.
