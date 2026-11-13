# Xeen: map sheets

Proposal, 2026-11-12. Part of the [Xeen world design](README.md). One sheet per outdoor map, then the dungeon list.
Monster levels are **monster** levels (A-tier range of the map's three encounter families, highest C-tier level), not
party levels; MM7 puts a level-10 party among level 4–24 monsters, and so does this design. Density targets come from
`research/MM678_CALIBRATION.md` and `research/MAP_CRAFT_CALIBRATION.md` §6, the "not bland" checklist, which every
sheet must satisfy: exactly one obelisk, ≥ 4 kinds of interaction device with one permanent-effect device, 25–55 POIs
1,300–2,600 units apart, 3–6 dungeon entrances, 4–10 outdoor chests with a reason each, 45–75 spawn markers and 110–150
hostiles at load in 8–15 named encounter areas, first fight 2,000–6,000 from each arrival, roads on 1–4 % of land,
height range ≥ 2,500.

Family names refer to [MONSTERS_AND_ITEMS.md](MONSTERS_AND_ITEMS.md#2-monster-families). "Tres" is the map_stats
treasure level, "L/T" lock and trap difficulty.

## 1. Cloudside surface

### X1 Vertigo Meadows: start pocket

| | |
| --- | --- |
| Source | Clouds E3, E4, F3, F4 (+ the Red River edge of F2) |
| Biome and sky | Green meadow, orchard and river delta; Pitchfork Creek; a dead forest in the south-west corner (Forest of the Walking Dead). The **east edge is the world rim**: meadow ending in white cliffs above the stars. `fair` sky, light rain |
| Monsters | A 2–4, C ≤ 12. **Orcs** (d1, orc outposts to burn), **Giant toads and snakes** (Toad Meadow), **Skeletons and zombies** (dead forest, d2). Pests (slimes, doom bugs) only in Joe's warehouse and the town's first quest. Tres 1, L/T 0/1 |
| Town | **Vertigo** (full services, start; WORLD_DESIGN §5.1), on the river with a bridge and a walled core. Toad Meadow hamlet: Myra the Herbalist, Valia's cottage |
| Dungeons | Joe's Warehouse (XD-01), Red Dwarf Mines (XD-02) and Deep Mine (XD-03) in the northern hills, Witch Tower (XD-04) in the south-east, Orc Caves (XD-05), **Temple of Yak** (XD-06) in the dead forest (a late return, like MM6's Gharik's Forge) |
| Outdoor content | Obelisk; Fountain of Ability (+2 permanent Luck, charges); Waters of Power (temporary HP); Wishing Well; Shrine of Poison (Body resistance, permanent once); 3 orc outposts to burn; Orothin's island statues; Derek's camp and Celia's hut; the **travel pyramid** (to Castleview) on a knoll east of town; the **Water Reflector** on the rim (M37, guarded late); Spring Druid's grove |
| Arrivals | Start in Vertigo square; road west to X3 and north to X7; Captain Nystor's boat from Rivercity up the river; pyramid from D1 |
| Signature view | The orchard road east of Vertigo ending at the rim, the stars below |
| Notes | The safe pocket of calibration: complete services, 2–3 entry dungeons, d1 monsters, 3–5 wells. The witch tower and its goblins are visible from town from day one |
| Added by the Act I briefs | Joe's warehouse key under a rain barrel by the warehouse; a culvert grate on Vertigo's riverbank (XD-01's second exit, opened from inside); the shaft head of the Clan King's escape shaft in the hills (XD-03, one-way out until its lever is thrown); Tam, Oslo's son, held in the Orc Caves (small reward at Oslo's hut); once the orcs' war drums burn (XD-05) the orc outposts stop refilling (a map state). Briefs: `briefs/xd01`–`xd05` |

### X2 Rivercity and Lake Darzog: the hub

| | |
| --- | --- |
| Source | Clouds C3, D3 |
| Biome and sky | Broad river and a lake with a wooded island; fairy woods to the south; farmland north. `fair`/`cloudy` |
| Monsters | A 6–10, C 24. **Killer sprites** (fairy woods), **Evil rangers and archers** (d2, the north bank camps), **Ogres** (river crossings). Three named **water dragons** in the lake (Q-C13): a visible danger, an early trap. Tres 2, L/T 2/1 |
| Town | **Rivercity** (hub; full services, boats and the skill row), built across the river on a great bridge. The robbers' den is under the bridge |
| Dungeons | Rivercity Robbers' Den (XD-21), **Darzog's Tower** (XD-12) on the lake island (boat or Water Walk, key-gated), Ogre Lair (XD-27) |
| Outdoor content | Obelisk; Sage's Fountain (+2 permanent Intellect); Shrine of Electricity; Danulf the Faery King's ring of stones; Tito's chapel; Medin's jetty; Ligono trapped in the surf at the rim (the **south edge is the world rim**); 2 evil-ranger camps; Captain Nystor's dock |
| Arrivals | From X3 (east), X4 (north), X5 (west); boat down the river to Vertigo (X1) |

### X3 Lifeforce Lagoon

| | |
| --- | --- |
| Source | Clouds C4, D4 |
| Biome and sky | Swamp, lagoon and dark marsh woods; the ruined Newcastle on a rise; Nightshadow in a perpetual mist (a local weather override: always overcast, the sun never reaches the town). `swamp` ground with pools |
| Monsters | A 10–15, C 30. **Swamp things** and **giant toads** (d2), **zombies/ghouls** around the Tomb, **bats** (Bat Queens) near Nightshadow at night. Tres 2–3, L/T 4/2 |
| Town | **Nightshadow** (cursed vampire town), **Newcastle** (the party's castle site) |
| Dungeons | Newcastle Keep (XD-13, staged), Tower of High Magic (XD-11), Tomb of a Thousand Terrors (XD-08), Nightshadow Crypt (XD-24) |
| Outdoor content | Obelisk; Mirabeth's lagoon rock; 3 sundials in Nightshadow; Ebenezer's tent; Emerson's work yard (barrels, crates); an evil-ranger camp; a well of temporary resistance; swamp food trees |
| Arrivals | X1, X2, X5 edge; mirror |

### X4 Burlock Savannah

| | |
| --- | --- |
| Source | Clouds C1, C2, D1, D2 (Gargoyle Range in the north) |
| Biome and sky | Rolling savannah and jousting fields in the south, the river's upper reach, red dwarf hills; **Gargoyle Range** of bare peaks in the north; lava fields of D1 at the north-east edge. `fair`, dry tint |
| Monsters | A 10–16, C 32. **Burlock knights** (jousters on the savannah, d2), **Ogres** (Ogre Hills), **Gargoyles** (the range, d3, north). Tres 2–3, L/T 4/2 |
| Town | **Castle Burlock** (royal seat, a castle BLV and a small walled village), **Asp** (cursed), Autumn Druid's grove |
| Dungeons | Castle Burlock (XD-07), Asp Undercroft (XD-25), Gargoyle Eyrie (XD-26), the Red Dwarf Mines' west adit (XD-02's second entrance, cleared from inside with a winch: once open, a permanent underground shortcut between X1 and X4 for Act II) |
| Outdoor content | Obelisk; Well of Might (temporary) and Olympian Fountain (+2 permanent Might); the jousting lists (a stat challenge); Carlawna's and Falagar's huts; Joe the Merchant's caravan (Merchant teacher); barbarian camp to burn; Captain Nystor's upriver landing |
| Arrivals | X2 (south), X6 (west), X7 (east); stables |

### X5 Winterkill Tundra

| | |
| --- | --- |
| Source | Clouds A3, A4, B3, B4 |
| Biome and sky | Snowfields, frozen lakes and a snowy troll forest; the Land of the Giants in the south-west corner. **South-west is the world rim**, a glacier ending in the stars. `winter_overcast`, snow |
| Monsters | A 15–22, C 40. **Snow beasts and wolves** (d2), **Barbarians** (camps), **Trolls** (Troll Forest; Ice Troll tier). The Land of the Giants corner holds **cyclopes** at d4: the face's first trap pocket. Tres 3, L/T 6/3 |
| Town | **Winterkill** (ghost town), Glom the Gnome King's burrow (2 houses), Kai Wu's monastery |
| Dungeons | Golem Dungeon (XD-09), Cave of Illusion (XD-10, two entrances), Ninja Pagoda (XD-22), Troll Warren (XD-23), **Darkstone Tower** (FD-03, sealed until the finale) |
| Outdoor content | Obelisk; Fountain of Great Protection (temporary AC); Waters of Great Magic; Shrine of Cold (Water resistance, permanent once); Thickbark the tree; Halon's water clock workshop; Winter Druid; cyclops outpost and barbarian camp to burn; the **Earth Reflector** on the rim |
| Arrivals | X2 (east), X6 (north) |

### X6 Desert of the Sphinx

| | |
| --- | --- |
| Source | Clouds A1, A2, B1, B2 |
| Biome and sky | Desert of dunes and red mesas; the Barbaric Mountains; Castle Basenji on a cliff. **West is the world rim**: dunes pouring over the edge into the stars, with sand streaming off in the wind (particles). `clear`, `arid` theme |
| Monsters | A 22–30, C 50. **Giant scorpions and sand worms** (d3; worms surface near travellers), **Sand golems** (ruins), **Werewolves** around Basenji. Tres 4, L/T 8/4 |
| Town | Saul's hermitage (urn), a caravan stop (tavern, stables); no full town: wilderness map |
| Dungeons | Castle Basenji (XD-14), The Sphinx (XD-15), Warzone arena (XD-20), Southern Sphinx (FD-02, sealed until Roland's amulet) |
| Outdoor content | Obelisk; oasis fountain (+2 permanent Endurance); Well of Accuracy; Shrine of Energy; bone fields; Arie's camp; Summer Druid; ruins with chests; the **Air Reflector** on the rim corner |
| Arrivals | X4 (east), X5 (south); coach to the Warzone |

### X7 Mount Firestone: trap and endgame

| | |
| --- | --- |
| Source | Clouds E1, E2, F1, F2 (and the Lava Lake of D1) |
| Biome and sky | Volcanic badlands, lava rivers, ash fall; the Red Dwarf Range's southern slopes are mild and early (the Orc Caves' back exit, XD-05), the north is deadly. **North is the world rim** with lava falling into space. `ember` / `plane_fire` theme, ash |
| Monsters | A 40–55, C 90. **Acid and fire dragons** (d3), **Lava golems**, **Great hydras**; the south slopes have orcs at d1 so an early party can visit the dwarf entrance and see what waits further north (calibration "trap map"). Tres 5–6, L/T 10/5 |
| Town | none (wilderness); a dwarf outpost on the south slope |
| Dungeons | Volcano Cave (XD-16) → **Shangri-La** (XD-17, hidden), **Dragon Cave** (XD-18, the hardest optional dungeon), Dragon Tower (FD-04, optional finale), Orc Caves' back exit (XD-05, a back gate opened from inside) |
| Outdoor content | Obelisk; Shrine of Fire; Well of Speed; the Ever-Hot Lava Rock (Q-C14) on an island in a lava lake; demon idols; the **Fire Reflector**; Shangri-La's pyramid is reached only through the valley |
| Arrivals | X1 (south), X4 (west) |

## 2. Darkside surface

Darkside maps share the `xeen_darkside_dusk` sky. Its levels start where Cloudside's middle is (calibration: the
second region of an open middle, not a second tutorial).

### D1 Castleview Vale: Darkside hub

| | |
| --- | --- |
| Source | Darkside A3, A4, B3, B4 |
| Biome and sky | River vale and grassland around a besieged walled town; the **Dark Grove**, a forest whose tallest tree carries a rope into the sky; acid pond; melon fields; a castaway's shipwreck on the river; Castle Kalindra on a rise to the south-west, **out of phase**: a translucent ghost of a castle until restored |
| Monsters | A 12–18, C 30. **Goblins and gremlins** (outside the walls, d2), **Barbarians** (Yog's Sardaj camp; peaceful if Q-D12), **Arachnoids and electrapedes** (Dark Grove). Tres 2–3, L/T 4/2 |
| Town | **Castleview** (hub, full services, pass at the gate); Castle Kalindra (staged) |
| Dungeons | Castleview Sewer (DD-01), Ellinger's Tower (DD-02, inside the walls), Castle Kalindra (DD-03), The Gremlin Court (DD-04), Western Tower (DD-05), Gemstone Mines (DD-10, west entrance) |
| Outdoor content | Obelisk; four gemsmith workshops; Luna's grove; Falista's hut; Justine's camp; Brother Reger's cell; well of +2 permanent Might; prayer shrine (temporary levels rescaled to +10 all stats until rest); Dark Grove rope (→ D7); the **travel pyramid** (→ Vertigo) outside the north gate |
| Arrivals | Pyramid; D2 (east); stables; mirror |
| Notes | First fight within 3,000 of the pyramid; no fight inside the town buffer. The gremlins' sabotage is visible: broken bridges, a burned mill |

### D2 Sprite Forest and Ogre Pass

| | |
| --- | --- |
| Source | Darkside C3, C4, D3, D4 |
| Biome and sky | Enchanted forest with glowing mushrooms and the great tree of the Temple of Bark; the Gemstone Range's foothills; Ogre Pass with two forts; Southern Tower in the woods |
| Monsters | A 16–22, C 38. **Sprites** (medusa and killer sprites, d2), **Dark wolves and sabertooths** (d2), **Ogres** (the pass, d3; peaceful if Q-D11). **Trolls** near the troll holes. Tres 3, L/T 6/3 |
| Town | Nibbler's hollow; Sharla's treehouse village (sprite vendors: potions, a Light guild branch); no human town |
| Dungeons | Temple of Bark (DD-09), Troll Holes (DD-11, three pockets), Ogre Forts (DD-13), Southern Tower (DD-06), Gemstone Mines (DD-10, east entrance) |
| Outdoor content | Obelisk; Shrine of the Elements (+resistances); Forbidden Fruit hut (+2 permanent stat and a condition); Monga melons; genie lamp; troll holes as pits in the forest floor; hidden Leprechaun's pot of gold |
| Arrivals | D1 (west), D3 (east) |

### D3 Sandcaster and the Aging Forest

| | |
| --- | --- |
| Source | Darkside E3, E4, F3, F4 |
| Biome and sky | Sandstone city at the desert's edge; **the Crossroads**, an open market; the Aging Forest (old trees, leaves fall all year) and the Howling Woods; the River of Wrath; Venom Pond. **East edge: the rim**, with the bright face's glow above it |
| Monsters | A 20–28, C 45. **Mantis ants and killer cobras** (d2), **Hell hornets** (Aging Forest), **Armadillos** (scrub). Tres 3–4, L/T 8/4 |
| Town | **Sandcaster** (wizard-ruled city, wizard quarter closed), **Crossroads** market |
| Dungeons | Sandcaster Sewer (DD-18), Wizard Quarter (DD-19), Eastern Tower (DD-07) |
| Outdoor content | Obelisk; Thaddeus's Fountain of Youth (dry until Q-D18); Cornelius the Leprechaun (outdoor teacher); Fountain of Great Protection; Celia and Derek's cottage (Clouds award link); fruit huts; Vespar's emerald handle in a ruin |
| Arrivals | D2 (west), D4 (north); stables; Lucio's boat (late) |

### D4 Lakeside and Blackfang

| | |
| --- | --- |
| Source | Darkside E1, E2, F1, F2 |
| Biome and sky | Great lake (Octopod Lake) with the **Isle of Lost Souls**; Snow River Rapids in the north; the Forest of Peril; Magic Mountain; **Castle Blackfang** on a crag in a storm of bats. North-east corner: rim |
| Monsters | A 28–35, C 55. **Gargoyles** (Magic Mountain, d3), **Vulture rocs**, **Octopods** in the shallows. Witches near Lakeside until Q-D22. Tres 4, L/T 10/5 |
| Town | **Lakeside** (coven town), Xanthus and Slibo's wizard camp on Magic Mountain |
| Dungeons | Lakeside Coven and Sewer (DD-20), Dungeon of Lost Souls (DD-12, by ferry), Castle Blackfang (DD-14, griffin only), Gargoyle Lair (DD-23) |
| Outdoor content | Obelisk; Xanthus' fountain (+SP temporary); Leafpoint the tree (Arch Druid); Ector's woodpile; Mirabeth Point (a statue to the Clouds mermaid); well of magic resistance; genie lamps |
| Arrivals | D3 (south), D5 (west); ferry; Lucio |

### D5 Desert of Doom and the Great Pyramid

| | |
| --- | --- |
| Source | Darkside C1, C2, D1, D2 |
| Biome and sky | The Desert of Doom and the Perishing Sands; the Quivering Forest on the highland edge; the Great Pyramid rising from the dunes; the Parabolic Barrier (a shimmering Ancient wall) in the north |
| Monsters | A 32–42, C 65. **Iguanasaurus** (d3), **Giants** (the highlands; peaceful if Q-D16), **Griffins** (cliffs). Tres 4–5, L/T 12/6 |
| Town | **Bosco's Hall** (dwarf hall, small BLV), Gurodel's giant hold |
| Dungeons | Great Pyramid (DD-15), Northern Tower (DD-08), Giants' Hall (DD-24), Bosco's Hall (DD-25), the Sandcaster Sewer's far exit |
| Outdoor content | Obelisk; the seven **enchanted boulders** (Q-D24); Shrine of Great Power; fountain of +2 permanent Endurance; broken travel pyramid (story prop); genie lamps |
| Arrivals | D4 (east), D6 (west) |

### D6 The Forbidden Zone

| | |
| --- | --- |
| Source | Darkside A1, A2, B1, B2 |
| Biome and sky | Volcanic waste and Ancient ruins; **two crashed escape pods**, one in a lava lake; Griffin Pass; the walled **Necropolis**; **Castle Alamar**, a fortress of metal and stone with energy fields. Ash fall. North-west corner: rim |
| Monsters | A 45–55, C 85. **Gamma gazers** (d3), **Lava dwellers** (fire elementals), **Griffins** (the pass); robot patrols near Alamar. Tres 5–6, L/T 15/8 |
| Town | **Necropolis** (city of the dead, pass required), Ambrose's camp at Griffin Pass |
| Dungeons | Castle Alamar (DD-17), Corak's Pod (DD-16), Sheltem's Pod (DD-22), Necropolis Sewer (DD-21), Alamar Depths (FD-01, after Alamar) |
| Outdoor content | Obelisk; Fountain of Super Resilience (temporary HP); Freeda the Mountaineer's camp (outdoor teacher); barbarian archer camp; mine entrances to the Forbidden Zone mines (small BLV pockets of DD-10) |
| Arrivals | D5 (east), D1 (south, a long mountain road); Lucio |

## 3. Sky maps, planes and finale (open-air BLVs)

All use the MM9 open-air BLV route (`level_generation/projects/mm9r_common/outdoor_blv.py`, `devdocs/INDOOR_OPEN_SKY.md`):
cloud islands and causeways as geometry, `below_horizon: sky`, a fall trigger below the clouds that moves the party to
the surface map underneath at the matching position.

| Map | Content | Monsters (A–C) | Size | Notes |
| --- | --- | --- | --- | --- |
| **X8 Cloudreach** | Two archipelagos joined by a long rope bridge: the Witch Clouds (harpy nests, the explorer statue, offering statues) and the High Magic Clouds (flying feet, cloud golems, a sorcerer's observatory). Three rhyming statues | Harpies 14–24, Flying feet / Guardians 18–24, Cloud golems 50 (rare) | ~ 60 % of an ODM | Reached from the Witch Tower (X1) and Tower of High Magic (X3) roofs; falls land on X1/X3 |
| **X9 Clouds of Xeen** | Slick's carnival on a cloud plaza; roc nests; Castle Xeen's gate; rhyming statues | Rocs 35, Cloud golems 50, Xeen's guards 60 | ~ 70 % of an ODM | Reached from Darzog's Tower roof (X2); falls land on X2. Later the Dragon Clouds (Q-F1) are a sealed island here |
| **D7 The Skyroads** | Cloud roads linking floating rest stops; **Olympus** (city of the gods); the Sky Lake; elemental merchants; scarab sellers; sky bandits' toll; the **Megadragon** on the road to Alamar's roof | Sky golems 80, Cloud and green dragons 80–88, Griffins 48 | ~ 1 ODM | Reached by the Dark Grove rope, tower roofs and Lucio's boats; the four corners lead to the planes |
| **P1 Fire, P2 Air, P3 Earth, P4 Water** | One compact plane each: a test of the element and a sleeper's chamber | Greater elementals 80, element-themed guardians | S–M dungeon scale each | MM8's planes were whole ODMs; these are deliberately small |
| **P5 Clouds of the Ancients** | The finale: the Pharaoh's shrine, the wedding pavilion | none (or a last guardian) | small | Ending cinematic (`evt.PlayCinematic`) |

## Dungeons

S < 40 monsters, M 40–100, L > 100 (calibration). "Story" marks main-quest dungeons; "Promo" promotion dungeons. Monster
levels are the families' range inside.

### Cloudside

| Code | Dungeon | Map | Class | Monster levels | Role | Set piece |
| --- | --- | --- | --- | --- | --- | --- |
| XD-01 | Joe's Warehouse | X1 | S | 2–4 | Story M2 | A 16-sided cistern with six barred slime pens behind gates on one feeding lever; the invoice crate. Cellar north of the warehouse, loft beside the hall (briefs L3: 24 rooms, 11 M units²) |
| XD-02 | Red Dwarf Mines | X1, X4 | M | 3–10 | Story M3 | Cart trestle over a chasm and a funnel stope with a spiral of ramps and railed ledges; coloured stat pools (+2 permanent, one each), gold veins; carts are scripted rides until the studio has horizontal movers (briefs L3: 50 rooms, 33.5 M units²) |
| XD-03 | Deep Mine | X1 (via mine cart) | S | 8–18 | Story M3 | The Clan King's six-sided hall with four pillars and a stepped dais; a slag channel crossed by two bridges, with steps out of it; the escape shaft to the X1 hills (briefs L3: 37 rooms, 21.6 M units²) |
| XD-04 | Witch Tower | X1 | M | 4–14 | Story M4, Promo T1-A | A crooked tower: four floors each a quarter turn further round one tall cauldron shaft, every floor's balcony looking down into it; the Alacorn pier on a buttress up the shaft; a hoist cage; caged children; the "Rosebud" door; roof exit to X8 (briefs L3: 32 rooms, 34.9 M units²) |
| XD-05 | Orc Caves | X1 | S | 5–9 | Optional | The drum hall: terraces down to a bowl, the Drum-Master's scaffold reached by a gangway under fire; burn three drums; the chimney loop; Tam the captive (briefs L3: 45 rooms, 24.2 M units²) |
| XD-06 | Temple of Yak | X1 | M | 16–30 (Yak Master 50) | Story M10 (Megacredits) | Switch puzzles; a pool that sickens; the Elixir |
| XD-07 | Castle Burlock | X4 | M | 10–30 | Story M5–M6 | Throne room; the "Crusaders only" gate; Prince Roland's ceremonial armour; a throne that throws you into the sky; dungeon with ice trolls and a caged fire dragon (optional) |
| XD-08 | Tomb of a Thousand Terrors | X3 | M | 18–40 | Story M10 | Torture devices as interactive props; coloured juices |
| XD-09 | Golem Dungeon | X5 | M | 24–52 (Diamond Golem 70) | Story M10 | Four halls: wood, stone, iron, diamond; each a puzzle (cut the branches, push blocks, set tumblers) |
| XD-10 | Cave of Illusion | X5 | M | 18–28 | Story M12 | Illusory walls (`translucent_faces` + no collision); a drain plug that empties the cave (water level mover); stat-selling skulls |
| XD-11 | Tower of High Magic | X3 | M | 18–35 | Story M13 | Alchemy floors with resistance brews; "Stairway to Heaven" to X8 |
| XD-12 | Darzog's Tower | X2 | L | 35–55 | Story M21 | No spells inside (map flag); trapdoor floors; the six study books (+5 stat, rescaled from +20); Crodo's secret room; roof to X9 |
| XD-13 | Newcastle Keep | X3 | S (staged) | 20–26 (wood golems) | Story M8–M23 | Changes with each stage; the sword vault with the syllable password |
| XD-14 | Castle Basenji | X6 | M | 20–45 | Q-C8 | Werewolf kennels; readable scrolls (blessings and curses); "There wolf" door |
| XD-15 | The Sphinx | X6 | M | 30–50 | Q-C9 | Body, head and the hieroglyph dungeon as one BLV; the riddle at the head; the thrones |
| XD-16 | Volcano Cave | X7 | M | 50–62 | Q-C26 | The demon and devil skulls; exploding chests |
| XD-17 | Shangri-La | X7 (hidden) | town | — | Q-C26 | Open-air BLV valley: a hidden town |
| XD-18 | Dragon Cave | X7 | L | 75–100 | Q-C25, optional | The dragon tax urn; the library of Dragon Lore; the Dragon King |
| XD-19 | Castle Xeen | X9 | L | 55–90 (Lord Xeen 110) | Story M35 | Guard-making machines and elemental generators that drop barriers; Xeen's aviary; the Sixth Mirror |
| XD-20 | The Warzone | X6 | arena | by tier | Arena | MM6–MM8 arena |
| XD-21 | Robbers' Den | X2 | S | 10–18 | Q-C3, Promo T1-E | Under the bridge; a vault with the tiara |
| XD-22 | Ninja Pagoda | X5 | S | 20–40 | Q-C4, Promo T1-D / Ninja | Five-storey pagoda (vertical), paper walls (destructibles) |
| XD-23 | Troll Warren | X5 | S | 18–28 | Q-C15 | Burn the warren from inside |
| XD-24 | Nightshadow Crypt | X3 | S | 30–45 | Q-C7, Promo Nosferatu | The coffin opens at night only |
| XD-25 | Asp Undercroft | X4 | S | 24–35 | Q-C5 | The transformer machine |
| XD-26 | Gargoyle Eyrie | X4 | S | 22–33 | Q-C10 | Vertical cave with ledges (ladders) |
| XD-27 | Ogre Lair | X2 | S | 12–20 | Q-C23 | — |

### Darkside

| Code | Dungeon | Map | Class | Monster levels | Role | Set piece |
| --- | --- | --- | --- | --- | --- | --- |
| DD-01 | Castleview Sewer | D1 | M | 5–15 (Rooka 12) | Story M16, Q-D5 | Five town shafts; the rat queen's nest |
| DD-02 | Ellinger's Tower | D1 | M | 14–20 | Story M17 | The moral question at the door; beholder bats; the password at the top |
| DD-03 | Castle Kalindra | D1 | M → L (staged) | 30–60 (Scraps 95, optional) | Story M19–M27, Promo Champion | Out-of-phase wings behind shimmering walls; safes; the throne room |
| DD-04 | The Gremlin Court | D1 | S | 6–15 (Gettlewaithe 15) | Q-D1 | A three-round court dialogue or a fight |
| DD-05 | Western Tower of Mok | D1 | M | 25–45 | Q-D6, Promo Hero/Priest of Light | Entered from the roof (rope → D7 → roof); the heretics' altar |
| DD-06 | Southern Tower | D2 | M | 12–30 | Q-D19, Promo Assassin/Sniper | Thieves' den: gongs, the "open sesame" chest |
| DD-07 | Eastern Tower | D3 | M | 45–70 | Q-D18, Promo Archmage | Floating mages; the Jewel of Ages |
| DD-08 | Northern Tower | D5 | M | 45–75 | Q-D17, Promo Black Knight/Villain | The Voweless Knights' proverbs with the vowels removed |
| DD-09 | Temple of Bark | D2 | M | 12–30 (Barkman 70, optional) | Q-D10, disks | A temple grown inside a giant tree; the "feed me" alcoves |
| DD-10 | Gemstone Mines (3 pockets) | D1, D2, D6 | S ×3 | 16–28 | Q-D7 | Gem rock veins; the God of Minerals |
| DD-11 | Troll Holes (3 pockets) | D2 | S ×3 | 18–38 | Q-D13, Promo War Troll | You fall in; each pocket has one way out |
| DD-12 | Dungeon of Lost Souls | D4 (isle) | M | 45–65 | Story M24, Promo Minotaur Lord | Five "think positive" gates (dialogue choices that open doors); the labyrinth; the songbird |
| DD-13 | Ogre Forts | D2 | S | 18–30 | Q-D11 | Two forts in one BLV; burnable |
| DD-14 | Castle Blackfang | D4 | L | 48–75 (Count 90) | Story M27 | Griffin landing on the walls; coffins; the Queen in the dungeon |
| DD-15 | Great Pyramid | D5 | L | 60–88 | Story M28–M30 | Torch levers, a number lock, a teleport maze, the Pharaoh |
| DD-16 | Corak's Pod | D6 | S | 50–70 (few) | Story M29, M32 | Starship interior; the stasis cipher; log computers |
| DD-17 | Castle Alamar | D6 | L | 70–90 | Story M33 | Conveyor halls (movers), element sundials, the true-name gate, energy fields (shields) |
| DD-18 | Sandcaster Sewer | D3 | M | 25–40 | Q-D14 | Barticus' gym; the long tunnel to D5 |
| DD-19 | Wizard Quarter | D3 | M | 36–65 | Q-D14, Promo Spy | Xenoc and Morgana's guild halls |
| DD-20 | Lakeside Coven and Sewer | D4 | M | 14–50 | Q-D22, Promo Warlock | Five prisoners; the riddle guild; the dragon statuette |
| DD-21 | Necropolis Sewer | D6 | S | 45–60 | Q-D23, Promo Lich/Priest of Dark | Sandro's heart |
| DD-22 | Sheltem's Pod | D6 | S | 60–70 | Optional lore | The other ship's log |
| DD-23 | Gargoyle Lair | D4 | S | 22–40 | Q-D15 | — |
| DD-24 | Giants' Hall | D5 | S | 36–62 | Q-D16 | The bloody throne |
| DD-25 | Bosco's Hall | D5 | town | — | Q-D17 | Dwarf hall with services |
| DD-26 | Olympus Sewer | D7 | S | 50–60 | Q-D28 | The tribble door |

### Finale

| Code | Dungeon | Map | Class | Monster levels | Role |
| --- | --- | --- | --- | --- | --- |
| FD-01 | Alamar Depths | D6 | M | 80–95 | Story M39 (Roland) |
| FD-02 | Southern Sphinx | X6 | S | 70–85 | Story M40 (Picard, the Chime) |
| FD-03 | Darkstone Tower | X5 | M | 80–100 | Story M41 |
| FD-04 | Dragon Tower | X7 | M | 80–100 | Optional Q-F1 |
| FD-05 | Dungeon of Death | X1 | M | 85–110 | Optional Q-F2 |

**Totals:** 27 S (counting the six mine and hole pockets), 21 M, 6 L, plus 2 town BLVs and the arena: within the
calibration target of 40–60 dungeons, about 55 % small. 26 are on the main path, about 20 serve promotions, the rest
are optional, matching MM7/MM8's "a third to a half optional".

## Layout sketches

Two sketches of the first maps show the intended composition. They are plans for review, not geometry: 128 × 128
terrain cells, north up, one character ≈ 4 cells. The same sketches are drawn to scale on the review page.

### X1 Vertigo Meadows

```text
 N   hills ^^^^^^^ [Red Dwarf Mines]^^^^ [Orc Caves]  ^^^ X7 exit (north road)
     ^^ orc outpost *        ^^   Deep Mine via cart       orc outpost *
 X3  ~~~~~~~~~~~~~~ Pitchfork Creek ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      | R
 <== river ====+==================[ VERTIGO ]==== orchard road =========> | I
               |                 walls, river, bridge   (pyramid knoll)    | M
     Spring    |   Oslo's hut       mirror, square          Waters of      | .
     Druid o   |                   Joe's warehouse          Power  o       | s
               |  Orothin's isles ~~~ delta ~~~~                           | t
  X3 <== road =+     Fountain of Ability o         Toad Meadow: Myra,      | a
               |                                    Valia's cottage        | r
   dead forest |  Derek's camp                     [WITCH TOWER]           | s
   [Temple of  |      Celia's hut (zombie wood)       Wishing Well o       |
     Yak]      |                                         Water Reflector * |
 S  ------------------------------------------------------------------------
```

### D1 Castleview Vale

```text
 N   Western Tower [roof only]   Dark Grove (rope to the sky) |  barbarian camp (Yog)
        gemsmiths ^ ^ ^              arachnoids, electrapedes  |      Kramer's caravan
                 Acid Pond             PYRAMID (from Vertigo) |      Vespar's tower
 W  ---------------------------------- north gate ------------+------------ road ==> D2
  rim   Luna's grove          [ CASTLEVIEW ]  walls, gremlins, |   Nibbler's hollow
  edge                        Ellinger's Tower inside, sewer   |   melon fields
        Falista's hut              south gate                  |   troll hole (pit)
        Justine's camp                 |                       |
               [CASTLE KALINDRA]  ghost castle on a rise       |   Hector's diamond shop
        river ~~~~~~~ shipwreck ~~~~~~~~~~~ river ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 S                    Brother Reger's cell     prayer shrine   Well of Luck
```
