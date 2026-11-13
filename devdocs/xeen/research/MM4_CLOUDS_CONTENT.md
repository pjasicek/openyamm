# Might and Magic IV: Clouds of Xeen — content inventory

Research input for the Xeen-world design. Scope: MM4 (Clouds) only. Darkside, the World of Xeen finale, monster stat
tables and the item/skill systems are covered by other documents.

## Sources and conventions

- Map text: `reference/mm4_5_world_of_xeen/unpacked/text/xeen/aazeNNNN.txt.json`. Events:
  `events/xeen_initial_state/mazeNNNN.evt.json`, decoded with the ScummVM opcode, `ifProc` and `giveTake` semantics
  (`engines/mm/xeen/scripts.cpp`, `party.cpp`). Placements: `maps/xeen_initial_state/*.mob.json`. Monster names and
  XP/HP come from `raw/dark/xeen.mon`, the Clouds monster table that ScummVM's `create_xeen` extracts as
  `monsters.cld`. Mirror destinations come from `raw/dark/xeenmirr.txt`. Quest-item names come from ScummVM's
  `QUEST_ITEM_NAMES`. Backstory is from `original_files/Manual_world_of_xeen.pdf`, pages 3–6.
- Some behaviour lives in the engine, not in the scripts: tower keys, dungeon stones, the sphinx amulet, the Clan King
  and Lord Xeen kill flags, and the scepter drop. Those facts come from the ScummVM sources (`locations.cpp`,
  `combat.cpp`, `map.cpp`) and are marked **(engine)**. Facts not checked against the data are marked **(memory)**.
- The world is a 6×4 grid of 16×16 outdoor areas. Columns A–F run west to east and rows 1–4 run north to south, so A1
  is the north-west corner. Cell coordinates are `(x,y)` inside the area, with **y increasing northward**. Vertigo,
  Rivercity, the three cloud maps, the Temple of Yak, the Tomb, the Golem Dungeon and the Dragon Cave are 32×32.
- Outdoor surface codes come from `layers[0]`: desert, snow, dirt, grass, swamp, lava, scorched ground, water, deep
  water, road, and "space", which is the void at the edge of the flat world. Wall codes come from `layers[1]`:
  mountains, snow mountains, lava mountains, trees, snow trees, dead trees and palms.

## 1. Main storyline

Backstory (manual). A man claiming to be King Burlock's long-lost brother, **Prince Roland**, returns from Mount
Firestone. He had gone there looking for the "Land below the Land". He makes the king obsessed with finding the **Sixth
Mirror**, the only portable magic mirror, and the realm decays while the search goes on. The king's advisor **Crodo**
sees "Roland" summon a horned knight-spirit. He hits Roland with Dancing Blades, which reveals an undead creature: **Lord
Xeen**. Xeen captures Crodo and imprisons him in **Baron Darzog's** island tower, where magic cannot be used. Crodo sends
dreams to the party, the scientists of **Newcastle**, telling them to build a weapon that can kill Xeen. After the last
dream, a bolt from the sky destroys Newcastle. The survivors gather in **Vertigo**. A bottle message found twice in the
game says "Help! I'm in Darzog's Tower!—Crodo" (E3 and F3).

| # | Beat | Where | Prerequisites / gate | Result |
|---|------|-------|----------------------|--------|
| 1 | Start in Vertigo. Mayor Gunther asks the party to clean the town of pests | Vertigo (F3 10,13) | — | Starts the town quest chain (§2). |
| 2 | Become **Crusaders**. Old Valia gives the **Crystal Key to Witch Tower** and asks for the **Alacorn of Falista** | Valia F4 (9,3). Witch Tower F4 (10,9), whose reaper checks the key **(engine)** | Witch Tower floors 1–4; the Alacorn is on floor 4 (7,4) | Valia grants the *Crusader* skill and 60,000 XP. A Falista branch gives the same title. |
| 3 | Audience at **Castle Burlock** | D2 (8,2); the gate says "Only Crusaders are allowed" | *Crusader* skill | King Burlock gives the Sixth Mirror quest: it was "last seen near the great volcano", reward an Earldom. Advisor **Artemus** voices his suspicion of Darzog and asks the party to find Crodo. Princess Roxanne gives the tiara side quest. |
| 4 | Get the **Enchanted Key to the Tower of High Magic** | Cave of Illusion L4 (7,14). Entrances B3 (0,2) and B4 (2,15) | A talking skull sells it for **300 gems** | Opens the Tower of High Magic (C4 6,15) **(engine)**. |
| 5 | Get the **Skeleton Key to Darzog's Tower** | Tower of High Magic L4, chest (7,12), with 100 gold | Climb floors 1–4 | Opens Darzog's Tower (D3 4,13) **(engine)**. |
| 6 | **Rescue Crodo**, kill **Darzog** | Darzog's Tower L3: Darzog, six Darzog Clones; Crodo in a secret room at (7,6) | Skeleton Key | 1,000,000 XP and an award. Crodo says Xeen's hideout is in the clouds above, the sword under Newcastle is needed, and Xeen plans to summon an army from the Darkside. L4 (5,5) leads up to the **Clouds of Xeen**. |
| 7 | Rebuild **Newcastle** (player stronghold) | Site at C4 (11,12): Ebenezer the Taxman. Engineer Emerson at Castle Burlock L1 (2,7) | Buy the land for **50,000 gold** to get the *Deed to New Castle*. Walls cost **5 King's Megacredits**; Ebenezer then gives the **Stone of a Thousand Terrors**. The keep costs 5 more; he then gives the **Golem Stone of Admittance** | The stones open the Tomb of 1000 Terrors (C4 6,6) and the Golem Dungeon (B4 11,9) **(engine)**. Ebenezer pays 50,000 gold of yearly taxes. |
| 8 | **Excavation Permit** | Artemus, Castle Burlock L1 (1,4) | Crodo freed | Emerson clears the caved-in dungeon for 5 more Megacredits. Newcastle L1 opens, with its smithy, training, temple, bank and "YOUR well" (+20 AC). |
| 9 | **Xeen Slayer Sword** | Newcastle L1 (12,14), a password door, to the Newcastle Dungeon pedestal | The password **"laboratory"**. Its syllables are scattered as notes (la/bo/ra on L1, to/ry on L2), and Elona in Shangri-La gives it outright | "The experimental Xeen Slayer Sword is yours." |
| 10 | Reach **Castle Xeen** | Clouds of Xeen (27). The gate at (16,29) says "No one may enter Castle Xeen without a cupie doll!" | Win the four carnival games of **Slick the Gamemaster** (Might, Speed, Endurance and Accuracy dolls), then trade them for a **Lord Xeen Cupie Doll** | Castle Xeen, levels 1–4. |
| 11 | Kill **Lord Xeen** | Castle Xeen L4. Xeen's Guards and **Xeen's Pet**. Guard-making machines and fire, electricity, cold and poison generators are destroyed on L1 and L4 (200,000 XP each) | **(engine)** Lord Xeen takes no damage from area spells, and only the Slayer Sword (weapon id ≥ 34) gets past his physical immunity. His death drops **Xeen's Scepter of Temporal Distortion** | — |
| 12 | Ending | Castle Xeen L4 (4,9): the **Sixth Mirror** | Without the Scepter, a force field "that reeks of Lord Xeen's magic" blocks the mirror. With the Scepter, its whine resonates with the mirror, the mirror shatters, the castle collapses, and the Clouds ending plays | The party is placed in Vertigo. King Burlock then thanks them, mourns the mirror and says "Your destiny lies on the darkside of Xeen." (He checks for the Scepter.) |

Megacredits needed to finish the castle: 15. Megacredits in the data: 8 in the Temple of Yak, 8 in the Tomb of 1000
Terrors and 14 in the Golem Dungeon. The Temple of Yak needs the *Yak Stone of Opening* from Mirabeth (§2), so the
**mermaid quest is effectively on the main path**.

**Rhyming statues on the cloud maps** form an in-world walkthrough. They need the *Linguist* skill, from the Book of
Languages in Castle Burlock:

- Witch Clouds: *Golem, Terror and Yak … have credits for King to hold* / *The Clerics of Yak you must outwit, Taxman
  then must have his bit* / *Five for your keep … Taxman gives stone to fear* / *Conquer terror … Illusion holds
  Magic's key*.
- High Magic Clouds: *Five more will raise your castle's walls, Taxman opens Golem's halls* / *Highest magic holds
  solution [to] Darzog's dark convolution* / *A secret room in tower drear holds the land's lost overseer* / *Though
  evil wizard has been beat you can't yet Lord Xeen defeat*.
- Clouds of Xeen: *Advisor will a dig permit, five coins more* / *Xeen's bane lies under castle* / *In clouds above
  island tower waits Lord Xeen* / *Only the sword Xeen's life can take*.

Not in MM4: **Ellinger** and **Alamar** appear only in Darkside. The real Prince Roland appears in the Darkside part
of the manual as Alamar's captive. In Clouds, Roland exists only as a plaque by "Prince Roland's ceremonial armor" in
Castle Burlock and as the backstory disguise. The Clouds hint NPC Psychic Sally says "Lord Xeen already has the Sixth
Mirror".

## 2. Quests and side quests

Reward columns come from the event scripts. Where a speaker only says "treasure", the event gives gold, gems or a
random item.

### 2a. Town and story-adjacent quests

| Quest | Giver (area, cell) | Objective | Reward | Notes |
|---|---|---|---|---|
| Vertigo's pests | Mayor **Gunther**, Vertigo (14,5) | Clear the slimes and doom bugs. Search the crate in **Joe's storeroom** (9,22): an invoice for "Breeder Slimes, 1 mated pair" and "5 Doom Bugs" proves that **Joe the Exterminator** has been breeding the pests | 4,000 gold, 50 gems, 5,000 XP, award "outstanding citizenship" | A drunk tavern patron hints "he breeds them in the warehouse". Joe's shop becomes "Out of Business". |
| Dwarf mines | Gunther, after the pests quest | The Mad Dwarf Clan has overrun the Red Dwarf mines. Kill the **Clan King** in Deep Mine Omega | 50,000 XP, award "Red Dwarf Badge of Courage" | (engine) killing monster #20 in map 41 sets the completion flag. |
| Winterkill ghosts | Mayor **Randon**, Winterkill (8,13) | Banging the south gong (13,1) summons a wave: **Spirit Bones**, then **Polter-Fools**, then **Ghost Riders**, 20 each. Clear each wave and report back each time | 500,000 XP, award "Ghostslayers Extraordinaire" | Signboards spell out the loop: destroy the ghosts, bang the gong, visit Randon, repeat. |
| Asp's snake curse | Adam and Eve, Asp | Find and destroy the **transformer** that turns townsfolk into snakes (8,14). First solve the pedestal colour puzzle: start in the south-west corner, begin with red, alternate the colours around the well | 50,000 XP. The *Crystals of Piezoelectricity* become available at (8,11) | Snake Men and Guardian Asps guard the town. |
| Count of Nightshadow | Town clues, Nightshadow | Set **all three sundials to 9** ("A stitch in time", "Lives of a cat"). Open the coffin **at night** (before 5:00 or after 21:00): "Only at night can you put up a fight" | Coffin: 99,999 gold, items, 50,000 XP. Killing the Count (Count Draco) unlocks the well's **+10 temporary levels** | Vampire town: Bat Queens and Gnome Vampires. Its guildmaster is Count Du Monay. |
| Barok's pendant | **Barok** the Sorcerer, Rivercity (25,20) | Recover the pendant that the sorceresses of Rivercity stole (1,20) | *Enchant Item* spell (otherwise sold for 1,000 gold to Sorcerers and Archers) and 80,000 XP. The town fountain is restored from harmful to +100 SP | Patrons gossip that the tavern hired the sorceresses to drive Barok out. |
| Roxanne's tiara | **Princess Roxanne**, Castle Burlock L3 (2,11) | Defeat the Rivercity robber gang and its **Robber Boss**, who holds the tiara at (1,3) | 200,000 XP and treasure | Rivercity is also full of Yang Knights, Captain Yang and 41 Insane Beggars. |
| Scroll of Insight | **Arie** the apprentice, A1 (11,5) | The wizard cult of **Castle Basenji**, guarded by werewolves, killed her master. Recover the scroll from Basenji L3 (3,9) | 750,000 XP and the **Jeweled Amulet of the Northern Sphinx**, which opens the Sphinx (B1) **(engine)** | Basenji L2 has the password door **"There wolf"**; a trapped peasant in the dungeon gives the hint. |
| Elixir of Restoration | **Mirabeth**, a mermaid cursed with legs, D4 (12,3) | Gives the **Yak Stone of Opening**. Fetch the elixir from the evil Temple of Yak (E4 4,4); it is at (30,25) | 250,000 XP and +5 Personality (permanent) | Opens the Yak megacredits. |
| Rescue Celia | **Derek** the Ranger, F3 (4,5) | Untie his bride Celia in a hut in the zombie forest, D4 (15,15) | 20,000 XP and treasure | — |
| Witches and the Alacorn | **Valia**, F4 (9,3) | See main beat 2. Gives the Crystal Key | Crusader title and 60,000 XP | The witches turn children into goblins. Caged boys on every floor give XP; one gives the password **"Rosebud"**. |

### 2b. Wilderness fetch and kill quests

| Quest | Giver (area, cell) | Objective (location) | Reward |
|---|---|---|---|
| Seasons relay | **Summer Druid** B2 (1,10), **Autumn** C2 (15,9), **Winter** A3 (6,1), **Spring** E3 (3,14) | Relay the Last Flower of Summer, then the Last Leaf of Autumn, then the Last Snowflake of Winter, then the Last Raindrop of Spring. The Raindrop goes back to Summer, so the cycle can repeat | The Spring Druid "renews the year … so will I renew you": 150,000 XP and an award. **(memory)** It cures magical aging. Stumpy the Tree in Shangri-La hints at this. |
| Lava for the water clock | **Halon the Efficient**, B3 (9,6) | Bring the **Ever Hot Lava Rock** from E2 (7,11), near Mount Firestone | 150,000 XP and a *Widget*, a joke item |
| Troll problem | **Thickbark the Civilized**, a tree, B3 (6,3) | Burn the troll lair, B4 (2,7) | 75,000 XP and the *Super Shelter* spell |
| Cyclops outpost | **Glom the Gnome King**, A3 (10,0) | Burn the cyclops outpost, A4 (10,8) | 100,000 XP and treasure |
| Ninja Pagoda | **Kai Wu** the monk, A3 (15,12) | Drive the Ninja clan out of the pagoda, A3 (15,6) | 75,000 XP and full food |
| Scarab of Imaging | **Carlawna** the Cleric, C2 (10,6) | Gargoyles stole it and flew to the desert; it is at C1 (15,11), in the Gargoyle Range | 75,000 XP and the *Moon Ray* spell (otherwise 2,000 gold) |
| Crystals of Piezoelectricity | **Falagar** the Wizard, C2 (8,11) | Recover the crystals from Asp. Lore: the scarab and the crystals power a machine that makes reptile people | 75,000 XP and *Megavolts* (otherwise 2,000 gold) |
| Ogre boulders | **Captain Nystor**, C2 (9,1) | Destroy the ogre lair, C2 (5,0), in the Ogre Hills | 40,000 XP and a reward |
| Wand of Faery Magic | **Danulf the Faery King**, C3 (14,5) | Crazed Killer Sprites hold it; it is at D4 (8,14) | 40,000 XP and gold |
| Holy Book of Elvenkind | **Tito** the Elf Priest, C3 (3,8) | Lost in Troll Forest, B4 (14,13) | 60,000 XP and gold |
| Lake beasts | **Medin** the Fisherman, C3 (12,13) | Kill the three Water Dragons in D3 | 100,000 XP and a reward |
| Ligono's skull | **Ligono** the Spirit, trapped in the surf at D3 (12,8) | Find his skull near the edge of the world, D4 (2,1) | 40,000 XP and *Recharge Item* |
| Bone whistle | **Orothin** the Hermit, F3 (9,6) | Find the whistle lost "in Pitchfork Creek"; it is at E4 (5,14) | 15,000 XP. Two island statues in F3 then teach *Cure Poison* and *Cure Disease* |
| Phirna root | **Myra** the Herbalist, F3 (9,11) | Dig Phirna roots in Toad Meadow (F3/F4), one at a time | 5 antidote potions per root (repeatable) |

### 2c. Destroy-the-camp events (no giver, XP only)

Barbarian camps A3 (8,14) and C2 (1,8): 25,000 XP. Archer camp B4 (10,12): 20,000. Troll lair B4: 20,000. Evil Ranger
camp C4 (1,11): 10,000. Sprite eggs D3 (3,1): 10,000. Orc outposts E2, E3 and F3: 1,000 each. Orc caves F2: 10,000
each. Undead shrine E4 (9,14): 5,000. Harpy nests on the Witch Clouds: 5,000 each. Roc nests on the Clouds of Xeen:
50,000 each. Several of these also complete a quest flag. **This "burn the camp" verb is a cheap, repeatable outdoor
objective that suits MM6–8.**

### 2d. Skills, trainers and teachers

| Skill | Where | Cost |
|---|---|---|
| Cartographer | Mylo the Mapmaker, Vertigo | 100 |
| Pathfinder (forests) | Rialdo the Ranger, Vertigo | 2,500 |
| Guild membership | Vertigo: Vern (25 dues). Rivercity: Vatawna (500). Asp: Sarah Slither (500). Winterkill: Casper (a 1,000 "gift"). Nightshadow: Count Du Monay (250 "because you are still alive"). Shangri-La: Brunhilde (free) | — |
| Arms Master / Body Builder | Flint and Arnold, Rivercity | 300 / 1,000 |
| Mountaineer / Navigator / Swimmer | Martin, Magneto and Darlene, Rivercity | 5,000 / 2,000 / 100 |
| Merchant | Joe the Merchant, D2 (14,2) | 6,000 |
| Spot Secret Doors | Oslo the Observant, E3 (11,12) | 500 |
| Prayer Master | Saul, A2 (6,13): "free", after putting 10,000 gold in his urn | 10,000 |
| Linguist / Astrologer | The Book of Languages and the Book of Astrology, Castle Burlock L1 | free |
| Danger Sense / Direction Sense | Hidden spots in Dwarf Mine 3 and Dwarf Mine 5 | free |
| Prestidigitator | "The Art of Magic", Tower of High Magic L4 | free |
| Crusader | Valia or Falista quest | quest |
| **Every skill** | Jack Alltrades, Shangri-La | 100,000 |

Other services: Lindon's Temps in Rivercity pays 100 gold for a week of work. Captain Nystor's boat runs between
Rivercity and the eastern shore at D3 (10,12) for 100 gold. The **mirror network** (§5) is in every town and dwarf mine.

Spell teachers outside the guilds:

- Witch Tower skulls sell Sleep, Pain, Beast Master, Clairvoyance, Toxic Cloud and Lightning Bolt for 5–10 gems.
- Temple of Yak books teach Light, Sparks, Acid Spray and Hypnotize.
- Tower of High Magic L4 teaches Prismatic Light.
- Sphinx Head teaches Divine Intervention and Starburst.
- Sphinx Dungeon teaches Teleport and Item to Gold.

### 2e. Stat wells, shrines and fountains (outdoor; mostly temporary or daily)

| Area (cell) | Name | Effect |
|---|---|---|
| A1 (4,12) / (7,6) | Waters of Great Power / Shrine of Energy | +250 HP / +50 Energy resistance |
| A3 (3,14) | Fountain of Great Protection | +30 AC |
| A4 (3,3) / (12,14) | Waters of Great Magic / Shrine of Cold | +250 SP / +50 Cold resistance |
| B3 (0,3) / (15,4) | Well of Accuracy / Well of Intellect | +50 each |
| C1 (2,4) | Well of Endurance | +50 |
| C3 (15,10) / (0,0) / (15,0) | Olympian Fountain / Well of Personality / Shrine of Magic | +10 Might, Endurance, Speed and Accuracy / +50 / +50 Magic resistance |
| D2 (3,8) | Well of Might | +50 |
| D3 (8,9) / (15,4) | Sage's Fountain / Shrine of Electricity | +10 Intellect and Personality / +50 |
| E2 (3,4) / (13,3) | Well of Speed / Shrine of Fire | +50 / +50 |
| E3 (8,6) / (9,14) | Waters of Magic / Elemental Shrine | +25 SP / +20 to four resistances |
| F3 (0,1), (1,7), (7,7), (12,12), (14,6) | Fountain of Ability / Wishing Well / Waters of Power / Fountain of Protection / Shrine of Poison | +5 levels / +60 Luck / +25 HP / +5 AC / +50 |

Permanent stat sources:

- Dwarf-mine coloured liquids: +2 to one stat each.
- Cave of Illusion skulls: +2/+3/+5 for 10–50 gems and +10 for 200 gems.
- Temple of Yak and Tomb of 1000 Terrors pools: +5.
- Tower of High Magic brews: +10 to one resistance each.
- Darzog's Tower L2 books: **+20** Might, Intellect, Personality, Endurance, Speed or Accuracy, one per book.
- Burlock Dungeon black liquid: +10 Might.
- Witch Tower vats: +1 to all stats.
- **Levels:** Shangri-La well, Golem Dungeon ("Master of Golems") and the Witch Clouds explorer statue each give +1
  level.

## 3. Geography

### 3a. Outdoor grid (dominant surface; named regions from the mirror table)

| | A (west) | B | C | D | E | F (east) |
|---|---|---|---|---|---|---|
| **1 (north)** | Desert, mountain edge. **Castle Basenji**, Air Corner reflector | Desert. **Desert of the Sphinx, Northern Sphinx** | Desert and palms. **Gargoyle Range** | Lava and scorched ground. **Lava Lake**, Dragon Tower (Darkside key) | Scorched, lava mountains. **Volcano Cave, Dragon Cave** | Scorched and lava. **Mount Firestone**, Fire Corner reflector |
| **2** | Desert. Southern Sphinx (Darkside amulet), Saul | Desert, road. **Barbaric Mountains, Warzone** gate, Summer Druid | Dirt and savannah. **Jousters' Savannah, Asp** gate, Autumn Druid | Dirt, river. **Castle Burlock**, Dwarf Mine 5 | Scorched, mountains. **Red Dwarf Range**, Dwarf Mines 3 and 4 | Scorched, dirt. **Red River Basin**, orc caves |
| **3** | Snow and tundra. **Winterkill**, Ninja Pagoda, Winter Druid, Glom | Snow, lake, snowy woods. **Ogre Hills**, Cave of Illusion, Darkstone Tower (Darkside key) | Dirt, deep river, woods. **Rivercity**, Faery King, Tito | Lakes, woods. **Fairy Forest, Darzog's Tower** (island), Ligono | Grass, creek, woods. **Pitchfork Creek**, Spring Druid, Oslo | Grass, river. **Vertigo**, **Toad Meadow, Magic Delta, Ever Blossom Orchard**, Dwarf Mines 1 and 2 |
| **4 (south)** | Snow. **Land of the Giants** (cyclops), Earth Corner reflector | Snowy forest. **Troll Forest, Golem Dungeon**, Cave of Illusion | Swamp and dirt. **Newcastle** site, Tower of High Magic, Tomb of 1000 Terrors | Swamp, water. **Lifeforce Lagoon, Nightshadow**, Mirabeth | Dense dead forest. **Temple of Yak**, undead shrine | Grass and forest. **Forest of the Walking Dead, Witch Tower**, Valia, Water Corner reflector |

Reading the map: the start is the green south-east (F3/F4). Fire and volcanic badlands lie to the north-east, desert
to the north-west, snow to the south-west, and the river heartland and swamps in the centre-south. "Space" tiles ring
the map edge: the flat world drops into the stars. Six small **pyramids**, at A3 (5,8), C2 (10,11), C3 (10,6), D4
(14,8), F3 (8,10) and in Shangri-La, are World of Xeen portals to Darkside; standalone Clouds answers "the moons are
not aligned". The four elemental **Reflectors** in the corners are switched on and set flags 33–36, but they have no
visible use inside Clouds. **(memory)** They probably belong to the World of Xeen.

### 3b. Towns (outdoor entrance cell; services)

| Town | Entrance | Services | Theme and set piece | Monsters |
|---|---|---|---|---|
| **Vertigo** (32×32) | F3 (10,13) | Smithy (Norman's Ironworks), Thylon's Training, Gilbert's Hexes (guild), Lady Geraldine's Tavern, bank, Slime Temple, Mylo's Maps, mirror | A half-empty starter town with a pest plague, a scam exterminator and a doom-preaching Plague Cult. A money tree grows here. Stealing from display cases means a year in jail | Slimes, Doom Bugs, 2 Breeder Slimes |
| **Rivercity** (32×32) | C3 (11,7), a bridge crossing | Rivercity Smithing, Street Fightin' (training), Witch's Cauldron (guild), Bull's Tavern, The Bank, Pray N Pay (temple), Arnold's Gym, Martial Training, Lindon's Temps, mirror, boat | A "wild", crime-ridden river city with the skill trainers. Robber gang, sorceresses | 41 Insane Beggars, 26 Robbers, 6 Robber Bosses, 7 Sorceresses, 12 Yang Knights, Captain Yang |
| **Asp** | C2 (9,15) | Guild only (Asp Guild), Snake Oil, Scale House, Travel Pit, mirror | Townsfolk are being turned into snakes; colour-pedestal puzzle | 18 Snake Men, 8 Guardian Asps |
| **Winterkill** | A3 (4,6) | Guild (Mindmeld Guild), mirror, a strength well | A haunted ghost town with gongs that summon each wave | 20 each of Spirit Bones, Polter-Fools and Ghost Riders |
| **Nightshadow** | D4 (13,5) | Guild (Moon Guild), Treasure Trove, Gnome Home, mirror | A vampire town of sundials, a coffin and a night-only fight | 18 Bat Queens, 9 Gnome Vampires, Count Draco |
| **Shangri-La** (hidden) | Volcano Cave L3 (9,10), after smashing both skulls on L1 | Earth Temple, Arm and Hammer (smithy), Tavern Xanadu, guild, Public Library ("An Education": Jack Alltrades), +1 level well | A secret utopia of hint-giving NPCs: Maurice, Alexander, Princess Pilar, Elona, Psychic Sally, Lacey the Unicorn and others | none |
| **Newcastle** (player-built) | C4 (11,12) | Smithy and training (L1); temple and bank (L2); "YOUR well" | The party's own castle; see beats 7–9 | Wood Golems in the ruined foundation |

### 3c. Castles, towers and dungeons

| Site (levels) | Entrance / key | Theme | Main monsters (XP each) | Notable content |
|---|---|---|---|---|
| **Castle Burlock** (3 floors and a dungeon) | D2 (8,2); Crusaders only | The royal court | Castle Guards (10k), King's Guards (10k), Mad Fools. Dungeon: Ice Trolls and a Fire Dragon | King, Artemus, Emerson, Roxanne. Books (Linguist, Astrologer). Joke plaques. A throne that teleports the party into the air outside |
| **Castle Basenji** (3 floors and a dungeon) | A1 (8,8) | Fortress of a wizard cult | 22 Werewolves (9k), Wizards (25k), Cult Leader (30k) | Readable scrolls need Linguist: stat boosts, plus traps (Scroll of Aging +25 years, Death, Insanity). "There wolf" password. Trapped peasants |
| **Witch Tower** (4) | F4 (10,9); Crystal Key | Witches' goblin factory | Goblins, Wicked Witches (1.2k), Head Witch | Caged children, "Rosebud", spell-selling skulls, vats (+1 all stats), the Alacorn. The roof leads to the **Witch Clouds** |
| **Tower of High Magic** (4) | C4 (6,15); Enchanted Key | Alchemy and magic | Flying Feet (3k), Sorcerers (30k), a Fire Dragon | Elemental brews (+10 resistance), Pandorian boxes, Prestidigitation, Prismatic Light, the Skeleton Key. "Stairway to Heaven" leads to the **High Magic Clouds** |
| **Darzog's Tower** (4) | D3 (4,13), on the lake island; Skeleton Key | The prison of an evil baron | Carnage Hands (12k), Darzog Clones (30k), Darzog (50k) | Teleport-pit floors on L2, the six +20 stat books, Crodo's secret room, a rope ladder over a cage. L4 leads to the **Clouds of Xeen** |
| **Castle Xeen** (4) | Clouds of Xeen (16,29); Cupie Doll | The villain's sky fortress ("Now entering Xeendom", "Xeen's Aviary") | Xeen's Guards (20k), Xeen's Pet (100k, 400 HP), Lord Xeen (600k, 500 HP) | Guard-making machines and elemental generators whose destruction drops elemental barriers. The Sixth Mirror |
| **Temple of Yak** (32×32) | E4 (4,4); Yak Stone | An evil cleric temple | 42 Skeletons, 20 Clerics of Yak, Yak Priests (5k), 9 Yak Liches (20k), the Yak Master (50k) | The Elixir, 8 Megacredits, spell books, a pool that makes the party ill, switch puzzles |
| **Tomb of a 1000 Terrors** (32×32) | C4 (6,6); Stone of 1000 Terrors | Undead torture tomb: "Insanity is our fame, undead is our game" | Ghouls, Tomb Guards, Tomb Terrors (13k) | Coloured tomb juices (+5 stat each), manacles, iron maiden, stocks, 8 Megacredits |
| **Golem Dungeon** (32×32) | B4 (11,9); Golem Stone | Four halls: Wood, Stone, Iron and Diamond | Wood (10k), Stone (20k), Iron (25k) and Diamond (30k, 1000 HP) Golems | A three-part puzzle: "cut the branches", "push blocks, expose six rocks", "set the tumblers". +1 level. 14 Megacredits |
| **Sphinx** (Body, Head, Dungeon) | B1 (12,8); Northern Sphinx amulet | Desert pyramid-sphinx | Mummies, Stone and Earth Golems | The name riddle **"Golux"**. Wrong answers lead to the Dungeon, whose hieroglyph clues need Linguist. Thrones grant titles at 500k each: King, Queen, Thieves ("Prince of Thieves"), and the five races in the Head ("Legendary Human/Elf/Gnome/Orc/Dwarf"). Spell books |
| **Cave of Illusion** (4) | B3 (0,2) / B4 (2,15) | A watery illusion maze | Guardians (1.5k), Water Golems (4k) | Mirage walls ("dissipates with your touch"), stat-selling skulls, a phantom safe, a plug that drains the cave (Might 50), the 300-gem key |
| **Volcano Cave** (3) | E1 (15,2) | Hellish lava caverns | Demons (30k), Devils (40k) | Demon and devil skulls, 250k XP each. Smashing both opens the way to Shangri-La. Exploding chests |
| **Dragon Cave** (32×32) | E1 (14,12) | Dragon lair and library | 17 Fire Dragons (80k), 14 Frost Dragons (100k), the **Dragon King** (250k, 2000 HP) | A "Dragon tax" urn (2,000 gold and 20 gems, or the party is ejected). Dragon Lore volumes 1–5 and "The Art of Taxation" give titles (Loremaster of Worms … of Dragons, Taxman Emeritus) and 50k–500k XP |
| **Dwarf Mines 1–5** | F3 (5,13) and (7,15); E2 (1,1) and (9,1); D2 (9,9) | Mines overrun by the Mad Dwarf Clan | Giant Bats, Giant Spiders, Mad Dwarves (200), Tiger Moles | Gold veins, coloured stat liquids, mine cars, cave-ins, travel-code notes that spell "Alpha" |
| **Deep Mines Alpha, Theta, Kappa, Omega** | Mirrors only, using spoken codes | Deeper mines | As above, plus Clan Sergeants and the **Clan King** (Omega) | Each mine's note gives the next code |
| **The Warzone** | B2 (12,4) | Arena | Waves chosen by the arena master | Repeatable battles; the party is returned to Vertigo |
| Clouds: **Witch Clouds, High Magic Clouds, Clouds of Xeen** (32×32 each) | Tower roofs | Walkable cloud tops. "Use Levitate before you enter the cloud world" | Harpies and the Harpy Queen / Flying Feet, Sorcerers, Cloud Golems / Cloud Golems and Rocs | Rhyme statues, nests, "Offering" statues that give items to Crusaders and damage everyone else, Slick's carnival, Castle Xeen |

## 4. Monster placement by area (.mob, initial state; XP per monster in parentheses)

| Tier | Areas | Placed monsters |
|---|---|---|
| Starter (≤500) | Vertigo; F3, F4, E4; Dwarf Mines 1–5 | Slimes (50), Doom Bugs (75). Orcs (200), Giant Snakes (100), Giant Toads (500). Skeletons (250), Zombies (300). Bats, Spiders, Mad Dwarves (200), Tiger Moles (400) |
| Early (500–3k) | E2, E3, F2; Witch Tower; Deep Mines; Cave of Illusion | Orcs (27 in F2), Insect Swarms (1.3k), Goblins (150), Wicked Witches (1.2k). Clan Sergeants (600), Clan King (2k). Guardians (1.5k), Water Golems (4k) |
| Mid (3k–10k) | C3, C4, D3, D4, D2; Rivercity; Asp; Winterkill; Temple of Yak; Tomb | Killer Sprites (1.6k), Stingers (3.6k), Swamp Things (6k), Evil Rangers (7k), Jousters (5k), Water Dragons (50k: the lake beasts). Robbers and Sorceresses (10k), Yang Knights (8k). Snake Men (5k). Ghosts (2–4k). Yak clergy (1.6k–50k). Ghouls, Tomb Terrors (13k) |
| Upper-mid (6k–15k) | A3, A4, B2, B3, B4, C1, C2; Nightshadow; Castle Basenji; Golem Dungeon | Ninjas (2k), Snow Beasts (7k), Barbarians (10k, 200 HP), Cyclops (10k). Ogres (6k), Evil Archers (10k), Ice Trolls (14k). Gargoyles (11k, 17 in C1). Gnome Vampires (12k). Werewolves (9k), Wizards (25k). Golems (10k–30k) |
| Late (10k–40k) | A1, A2, B1 desert; the Sphinx; Tower of High Magic and High Magic Clouds; Darzog's Tower | Giant Scorpions (1k), Sand Golems (8k), Sand Worms (10k, 250 HP). Mummies, Stone and Earth Golems. Flying Feet, Sorcerers (30k), Cloud Golems (30k). Carnage Hands, Darzog Clones, Darzog |
| Endgame (20k–250k) | D1, E1, F1 volcanic north; Volcano Cave; Dragon Cave; Clouds of Xeen; Castle Xeen | Acid Dragons (60k), Lava Golems (20k, 500 HP), Great Hydras (50k, 1000 HP). Demons and Devils. Fire and Frost Dragons, the Dragon King. Rocs (20k). Xeen's Guards, Xeen's Pet, Lord Xeen |

The difficulty slope runs **south-east to north and west**: the green start, then the river heartland, then the snow
and desert flanks, then the volcanic north-east. Every dungeon is a fixed-tier "zone", so the world is wide open; gating
comes from keys and the Crusader title, not from geography.

## 5. Characters, factions, items, set pieces

**Unique NPCs.**

- Story: King Burlock, Artemus (advisor), Emerson (engineer), Princess Roxanne, Crodo (overseer, imprisoned), Baron
  Darzog, Lord Xeen ("Prince Roland").
- Townsfolk: Mayor Gunther, Joe the Exterminator, Mayor Randon, Count Du Monay / Count Draco, Barok, Ebenezer the
  Taxman, Slick the Gamemaster.
- Wilderness: Captain Nystor, Valia and Falista the Unicorn, the four seasonal druids, Glom, Kai Wu, Thickbark,
  Danulf, Tito, Carlawna and her brother Falagar, Halon, Ligono, Orothin, Myra, Derek and Celia, Mirabeth, Arie.
- Shangri-La: hint characters, Jack Alltrades and Kublai Khan the bouncer.

**Factions.**

- Lord Xeen's side: Darzog, Xeen's Guards, gargoyles hired as thieves.
- The Burlock crown and court.
- Evil groups: the Basenji wizard cult and its werewolves; the witches of Toad Meadow; the clerics of Yak; the Mad
  Dwarf Clan, against the Red Dwarves.
- Rivercity: the robber gang, Captain Yang and the Yang Knights, the sorceresses.
- The Ninja clan, against the gnome monks.
- Fey and nature: faeries against crazed sprites; treants against trolls; the druids of the four seasons.
- Monster nations with camps: barbarians, ogres, cyclops, orcs, evil rangers and archers.
- Dragons, ruled by the Dragon King.

**Quest items (34 Clouds entries).**

- Keys and passes: the Deed, the Crystal Key, the Skeleton Key, the Enchanted Key, the Northern Sphinx Amulet, the
  Stone of 1000 Terrors, the Golem Stone, the Yak Stone.
- Story items: the Scepter, the King's Megacredits, the Excavation Permit, the carnival dolls (Cupie, Might, Speed,
  Endurance, Accuracy; a Luck doll exists but is unused).
- Fetch items: the Alacorn, the Elixir, the Wand, the Tiara, the Holy Book, the Scarab, the Crystals, the Scroll of
  Insight, Phirna Root, the Bone Whistle, Barok's Pendant, Ligono's Skull, the four season tokens, the Lava Rock, the
  Widget.
- Unique weapon: the **Xeen Slayer Sword**.

**Set pieces that translate well to MM6–8.**

- **Building your own castle** with a taxman and a royal engineer, paid in Megacredits looted from three dungeons. Each
  stage unlocks the next dungeon. This maps naturally onto MM7's Harmondale.
- **Joe's scam**: an investigation-reveal quest with physical evidence in a warehouse crate.
- **Seasons relay** between four druids in four biomes, which rejuvenates the party.
- **Ghost waves on demand** (Winterkill gongs), **night-only vampire coffin** with sundial settings (Nightshadow),
  **colour-pedestal disenchantment** (Asp).
- **Password doors fed by NPC rumours**: "Rosebud" from a rescued child, "There wolf" from a prisoner, "laboratory"
  assembled from scattered syllables.
- **Sphinx riddle** ("My first is in giant but not in defiant …" → GOLUX), with throne titles per race and class.
- **Golem Dungeon** material puzzles. **Dragon library** of titles behind a dragon tax.
- **Volcano skulls opening a hidden utopia** (Shangri-La) full of hint NPCs.
- **Carnival of stat games** guarding the villain's door.
- **Tower roofs that open onto walkable cloud islands**, each with rhyming walkthrough statues. In MM6–8 these become
  outdoor sky maps reached by Fly or a beanstalk-style transition.
- Burn-the-camp objectives. Stat wells with mixed blessings and curses (Basenji scrolls of aging). Talking skulls that
  sell stats or spells for gems. The flat world's starry edge.

**Things that do not translate directly.**

- Grid-cell scripting: the teleport-step chains used for the river ferry and bridges (C3/D3, Rivercity), Darzog L2 pit
  squares, events tied to facing direction, the illusion-wall cells and cell-surface swaps after draining the cave.
- Terrain-gate skills: Mountaineer, Pathfinder, Swimmer, Navigator, Direction Sense and Danger Sense have no MM6–8
  equivalent. Use Water Walk, Fly, paths and keys instead.
- **Typed mirror travel** by place name (including secret codes such as "alpha"). Replace it with a portal that lists
  discovered destinations, keeping hidden codes as optional passwords.
- Party-wide "everyone learns the spell" rewards. MM6–8 restrict spells by class and school.
- Temporary +5/+10 level fountains and +250 HP waters; the MM6–8 power curve needs different numbers.
- Stealing means a year in jail (aging). Random stat-threshold minigames.
- The Darkside portals, Reflectors and Darkside-key towers (Dragon Tower, Darkstone Tower, Dungeon of Death, Southern
  Sphinx), which only work in World of Xeen.

## 6. Suggested playthrough order (levels are estimates from monster XP and placement)

| Phase | Approx. levels | Content |
|---|---|---|
| Early | 1–8 | Vertigo pests and Joe; train and join the Vertigo guild. F3/F4: Celia, Orothin, Myra, orc outposts, Toad Meadow. Dwarf Mines 1–5 (stat liquids, travel codes). Rivercity trainers (Swimmer, Arms Master, Body Builder), Lindon's Temps |
| Early-mid | 8–15 | Witch Tower → Crusader. Castle Burlock audience (Linguist, Astrologer, quests). Seasons relay. Tito, Danulf, Medin, Ligono. Deep Mines → Clan King. Barok's pendant |
| Mid | 15–25 | Asp, Winterkill ghosts, Nightshadow vampires. Thickbark, Glom, Kai Wu, Nystor, Carlawna, Falagar. Mirabeth → Temple of Yak. Buy the Newcastle land and fund the walls → Tomb of 1000 Terrors → keep → Golem Dungeon. Cave of Illusion (stat skulls, buy the key). Rivercity robbers → tiara |
| Late | 25–40 | Castle Basenji → amulet → Sphinx. Tower of High Magic and the High Magic Clouds. Darzog's Tower → Crodo → permit → Newcastle dungeon → Xeen Slayer Sword. Volcano Cave → Shangri-La (+1 level, Jack Alltrades) |
| Endgame | 40+ | Desert and volcanic north outdoors. Dragon Cave (optional, hardest). Clouds of Xeen (Rocs, dolls) → Castle Xeen → Lord Xeen → Sixth Mirror ending |

For an MM6–8 adaptation, keep the hub-and-spoke shape: Vertigo, then the Crusader gate, then the castle-building
economy and the key chain, then the sky finale. Compress the stat-well economy into the MM6–8 fountain-and-shrine
tables.
