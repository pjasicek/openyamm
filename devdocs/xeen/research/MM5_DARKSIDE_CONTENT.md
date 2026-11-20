# MM5 Darkside of Xeen and the World of Xeen finale: content research

Research input for a new MM6–MM8-style world that adapts the Xeen story. It covers Darkside (MM5), the combined World
of Xeen (WoX) finale and the 17 WoX-only maps stored in `DARK.CC`. It also reviews the earlier MM5 design projects.
Clouds of Xeen (MM4) content and monster, item and skill statistics are covered by other research notes.

**Sources.** Everything here was checked against `reference/mm4_5_world_of_xeen/unpacked/`:

- the event scripts `events/dark_initial_state/*.evt.json`, decoded with ScummVM's opcode, condition and give/take
  tables (the decoding script is described below);
- the map strings `text/dark/aaze*.txt.json`, the mirror list `darkmirr.txt` and the map names in `maps/index.csv`;
- the quest log `raw/dark/qnotes.bin`, `award.bin` and the Darkside-ending lines in `special.bin`;
- the monster table `raw/dark/dark.mon` (95 records of 60 bytes) and the `.mob` monster placements;
- the WoX manual (the Dragon Pharaoh's log, pp. 6–9).

Statements based only on memory are marked **(memory)**. Statements inferred from the data but not traced through the
grid are marked **(inferred)**. Map coordinates are written `A3(8,10)`, meaning outdoor square A3, x=8, y=10, or
`map#(x,y)` for interiors. Darkside squares run A–F from west to east and 1–4 from north to south.

How the scripts were decoded. A conditional (opcodes 8–10) jumps when its test is true. Opcode 8 with parameters
`[9,0,n]` is used as an unconditional goto. Opcode 24 rewrites a line of the same event, which is how scripts move from
one state to the next. `TownEvent` 8 opens a keyed tower door, 9 a keyed dungeon door, 11 a travel pyramid and 12 a town
gate that needs a pass. Quest item *n* in a give/take is item id 82+*n* (ScummVM `QUEST_ITEM_NAMES`). The decoding
script (`decomp.py`) was a temporary scratch file and was not kept in the repository.

---

## 1. Darkside main storyline

### Backstory

The backstory comes from the manual's Dragon Pharaoh log and the log computers in the two escape pods.

- Sheltem is a rogue Ancient guardian AI: the **S.H.E.L.T.E.M.** unit, originally Terra's guardian. He removed his own
  obedience directives, imprisoned his Ancient handlers (one of them Corak), posed as King Alamar on VARN, tried to
  throw the CRON ship and its VARNs into the sun, then returned to Terra.
- Corak (**C.O.R.A.K.**) chased Sheltem off Terra. Both escape pods crashed into the **X.E.E.N.** project ("Xylonite
  Experimental Expansion Nacelle Starseed Project"), a flat artificial world. The Terran ship that followed them burned
  up, but it beamed its crew down first (these are the MM3 heroes).
- Sheltem's pod landed safely. Corak's pod landed in lava and he stayed in stasis.
- As "Alamar", Sheltem became Queen Kalindra's charming guest. He stole the **Cube of Power** (the control of Xeen) and
  the key to the Royal Pyramid. He gave Kalindra to Count Blackfang, who made her a vampire, and moved Castle Kalindra
  "out of phase".
- Alamar's rebel army, which includes the Pharaoh's former allies, took the Great Pyramid. The Pharaoh sealed himself in
  its top level and sent his **orb** into the world to find heroes.
- Ellinger, the Queen's wizard, also sealed himself inside his tower. Alamar captured the real Prince Roland, the
  emissary from the other side of the world, and sent his own "ambassador" in Roland's place. The manual's Crodo story
  shows that the Roland at King Burlock's court on the Clouds side is a monster. That impostor is Lord Xeen, whom the
  Pharaoh calls Sheltem's general.
- Alamar's plan, explained by the Pharaoh and by Gurodel: steer Xeen away from the sun and use it as a ship back to
  Terra. Everything living on Xeen would freeze.

### Main quest, step by step

| # | Step | Where | Requires | Result / reward |
| ---: | --- | --- | --- | --- |
| 1 | Zelda the Herbalist found an orb in a crater and gives it to you | Castleview (25,21) | none | **Dragon Pharaoh's Orb** |
| 2 | Troyanna the mindreader sends you to Madame Oorla (the dialogue calls her "Neena"). The gypsy says the orb belongs to the Pharaoh but must first go to Ellinger | Castleview (20,20), (17,10) | Orb | Oorla's advice updates at each later stage |
| 3 | Nadia's onyx necklace: kill the sewer rats | Nadia at Castleview (27,19); necklace in Castleview Sewer | none | **Key to Ellinger's Tower**, 100k xp |
| 4 | Climb Ellinger's Tower. The tower is a gauntlet: a moral question at the L1 entrance, traps, the password "Ellinger" on L4 | Castleview (12–13,10); maps 53–56 | Tower key | Ellinger: +250k xp, his gift in Castleview's runaway chest; flag 114 |
| 5 | Ellinger: the Pyramid key is in Castle Kalindra, which is out of phase. **20 Energy Disks** restore it in four stages of 5 | Ellinger L4 (4,8) | none | Each 5 disks unlock a stage (table below) |
| 6 | Collect the disks: see the disk sources table below | many places | many | — |
| 7 | 5 disks: Kalindra **L1** opens. 10 disks: **L2**. 15 disks: the **dungeon**. 20 disks: **L3** and the whole castle | A4(5,14); maps 41–44 | disks | "Restored Castle Kalindra" award; Ellinger's role ends |
| 8 | Megan, Dimitri's daughter: her father, captain of the guard, is despondent. Fetch the **Songbird of Serenity** | Kalindra L2 (11,15) | L2 restored | **Key to the Dungeon of Lost Souls** |
| 9 | Dungeon of Lost Souls, 5 levels of "positive thinking" yes/no gates. Free the Songbird on L5 | Isle of Lost Souls F2(6,10), reached by Lakeside's boat | Lost Souls key | Songbird |
| 10 | Dimitri recovers. Only the Queen's **crown** can undo her vampirism, and it is in her L3 wall safe. He gives the L2 disk-safe combination **64-52-31** and sends you to Ambrose for a way into Blackfang | Kalindra L2 | Songbird | 5 gear items, award "Cheered Dimitri"; Megan then gives +3M xp |
| 11 | Ambrose, the Queen's Knight, at Griffin Pass asks "Who sent you?" (answer **Dimitri**). He has caught a griffin and needs his **bridle enchanted** | B1(12,5) | Dimitri's name | Bridle |
| 12 | Natasha the Enchantress enchants the bridle | Sandcaster | **Pass to Sandcaster**, 50,000 gold | Enchanted Bridle; Ambrose gives 500k xp and 50k gold, then leaves for Blackfang |
| 13 | Ambrose's griffin flies you into **Castle Blackfang**, which has no other way in | F1(9,11) | Ambrose helped (flag 164) | Blackfang L1 |
| 14 | Blackfang: vampires on 3 floors and coffins. **Count Blackfang** on L3 blocks the way down until he is killed. The Queen is in the dungeon | maps 45–48 | — | Queen: "go see Dimitri" |
| 15 | The Queen gives her safe combination **3-31-62**. Take the **crown** from her L3 safe and bring it to her | Kalindra L3 safe; Blackfang dungeon (1,1) | talked to Dimitri | **Key to the Ancient Pyramid**, +5M xp, "Saved the Queen". Ambrose flies everyone out |
| 16 | The Great Pyramid: L1 has cloud and green dragons and a lever/torch puzzle and number puzzle; L2 a "Starfleet registry" code; L3 a teleport maze; L4 the **Dragon Pharaoh** | D2(0,5); maps 83–86 | Pyramid key, Orb | The Orb is returned (+5M xp). The Pharaoh explains Alamar's plan and the **second meteor**, and cools the lava around it (flag 170) |
| 17 | **Escape Pod 1** (Corak). Decode the Ancients' message to switch off the stasis field (the answer is "where no man has gone before") | B2(3,8), closed by lava until step 16 | flag 170 | Corak freed (+5M xp). He needs a way to hide from Sheltem's senses |
| 18 | The Pharaoh names you the **Chosen Ones**. The only **Soul Box** is in Olympus | Pyramid L4 | Corak freed (flag 169) | **Pass to Olympus**, award "Chosen one". Opens Lucio's boats, the sleepers and the Pyramid's sky door |
| 19 | **Olympus**, the hidden city in the sky (Sky C2). Take the Soul Box from "Soul Storage". The statues give the four prophecy verses; one plaque says Alamar's true name is **Sheltem** | Sky C2(2,7); map 37 (10,14) | Olympus pass; reach the sky layer | Soul Box |
| 20 | Corak hides in the Soul Box | Escape Pod 1 | Soul Box | **Soul Box with Corak inside** |
| 21 | **Castle Alamar**: annihilators. L1 conveyor corridors; L2 four element sundials, the "Nine is the time" clue and the true-name gate (**Sheltem**); L3 "Come to ME!" | A1(10,4); maps 49–52 | Soul Box with Corak | Without the box, the party is wiped out ("You Fools!"). With it, the Darkside ending (below) |

**Darkside ending** (`END_DARKSIDE`, plus the `special.bin` lines). Corak comes out of the box and fights Sheltem. Sheltem
taunts him, and Corak gives up the fight and starts **self-destruct code 0-0-1**, taking Sheltem with him. The party
gets "DEFEATED SHELTEM" and +5M xp, wakes in Castleview, and the engine gives them the **Cube of Power** (quest item 53).
The Pharaoh later says that Xeen is returning to its proper orbit.

**Kalindra restoration stages** (flags in brackets):

| Disks | Flag | What opens |
| ---: | --- | --- |
| 5 | 168 | The outer gate at A4(5,14) and L1: throne room, Gem (Danger Sense), Errol (Arms Master), servants, 6 thievery safes |
| 10 | 153 | L2: Dimitri, Megan, 6 disk safes, the Astrologer skill spot |
| 15 | 154 | The dungeon: Guido the convict (gives safe combination 10-11-12), Scraps the pet dragon, imprisoned liches and dragon mummies, a prisoner ledger |
| 20 | 155 | L3: the Queen's bedroom and crown safe, trainer/temple/bank/smith, +10 Personality and +10 Might, and the **mirror portals** switch (flag 115, which wakes the mirrors in Ellinger's tower and the four towers) |

**Disk sources** (25 in total; 20 are needed):

| Source | Disks | Notes |
| --- | ---: | --- |
| Gettlewaithe, the Gremlin King, Castleview | 3 | Given if you make him submit by talking; found under his throne if you kill him |
| Sharla's Sprites, C4 | 2 | Reward for rescuing the captive sprite, or taken from the treehouse after a murderous stick-up |
| Gurodel's Giants, D1 | 2 | Gift if diplomacy goes well, or "the bloody throne" if you fight |
| Graalg's Ogres, D3 | 2 | Gift if diplomacy goes well, or found by searching the fort |
| Western Tower L1 | 2 | Alcoves |
| Southern Tower L3 | 2 | |
| Eastern Tower L3 | 2 | |
| Northern Tower L4 | 2 | |
| Temple of Bark L5 | 2 | "Feed me! Give gem?" alcoves |
| Kalindra L2 safes | 6 | Need 10 disks already and Dimitri's combination |

Every negotiated faction has both a peaceful and a violent route to its disks. This is good material to keep.

---

## 2. World of Xeen combined finale and the 17 WoX-only maps

### Travel between the two sides

- The small travel pyramids on Clouds lead to the **Castleview pyramid**. The Castleview pyramid leads to the pyramid
  outside Vertigo (manual).
- Darkside's other pyramids are broken ("The Portal has been destroyed" at B2(5,4), D1(9,1) and E3(13,14)). They are
  props that tell the story of the war.
- Castle Alamar's dungeon has a second working pyramid at map 52 (2,2).
- The four maps in `DARK.CC` that open onto the surface run `FlipWorld 0` on exit. They are physically on the
  **Clouds side**, even though their data ships with Darkside.

### The finale chain

The order below is mostly data-backed. The order of the ID-card doors is (inferred).

| # | Step | Where | Gives / requires |
| ---: | --- | --- | --- |
| 1 | Win Darkside | Castle Alamar L3 | **Cube of Power** |
| 2 | Win Clouds: kill Lord Xeen, who holds **Xeen's Scepter of Temporal Distortion** (Clouds content) | Castle Xeen | Scepter. The Pharaoh asks for this explicitly if you return with the Cube only |
| 3 | **Activate the four Reflectors** in the corners of the Clouds side. These are flags 33–36; signs mark the Earth, Fire and Water corners | Clouds A1, A4, F1, F4 | "Step One" on the Fire plane's statue. The final shrine does **not** check them |
| 4 | **Wake the four Elemental Sleepers.** Each plane is reached by a fall from a Skyroad corner after answering "What do you seek?" with the element's name: Fire at Sky A1, Air at Sky F1, Earth at Sky F4, Water at Sky A4. Each plane has a "test of the element" and a chest | Maps 25–28 | Needs the "Chosen one" award. Gives the four "Awakened … Sleeper" awards |
| 5 | Free **Prince Roland** from stasis in the lowest level of Alamar's dungeon | Alamar dungeon (13,15) | +5M xp, award "Rescued Roland", **Amulet of the Southern Sphinx**. Roland says he and Kalindra will marry on the cloud above Darkstone Tower |
| 6 | Alamar's dungeon also holds the **Key to Dragon Tower** (13,3) and the **Key to Darkstone Tower** (11,9), five stations of +5 permanent levels, and two skull doors that need the Silver and Gold ID cards | map 52 | Probable order (inferred): Dragon Tower key → Silver card → Darkstone key → Gold card → Roland |
| 7 | **Dragon Tower** (Clouds D1): Alister the druid wants a **Dragon Egg** (the egg is on L3). Endurance stations, tomes worth 10M xp. Its roof leads to **Dragon Clouds**: the Eye of the Dragon asks "What is the secret of the Dragon?" (**Infinity**) and gives the **Silver ID Card**. Also four rune tiles, crystal balls (wisdom checks that can kill), a +50 temporary level well and Dragon Crystals (+3/+4/+5 permanent levels) | maps 117–120, 128 | — |
| 8 | **Darkstone Tower** (Clouds B3): onyx golems; plaques on every level form a letter grid; a skull puzzle (answer **120**). L4 has the **Gold ID Card** and the seal to the clouds, which only the **Chime of Opening** breaks | maps 113–116 | — |
| 9 | **Southern Sphinx** (Clouds A2), opened with the Sphinx amulet. Picard the Aged trades the **Chime of Opening** for a **Widget**. The Widget comes from Halon the inventor on Clouds (after the Everhot Lava Rock quest). There are paid trap "protections", runes that spell PICARD, dragon mummies and a Super Dragon Embalmer (+5 levels) | maps 125–127 | Widget |
| 10 | **Clouds of the Ancients** (above Darkstone Tower). Signs on the "Rest Stop" walk carry developer jokes (other New World Computing games). The Pharaoh's shrine checks for the Scepter, the Cube and all four sleeper awards | map 129 (13,15) | **`END_WORLD`**, the unification ceremony |

The Pharaoh's dialogue after Darkside gives the finale's own checklist: turn on the four machines, wake the sleepers,
open the way to the cloud above Darkstone Tower, and free Roland "before he can get married". The four plane statues
repeat the steps: Step One machines, Step Two sleepers, Step Three bring the Cube and Scepter together, Step Four go to
the shrine on the cloud. The ending cinematic itself is not in the event data. **(memory)** The two halves of Xeen are
united, Roland and Kalindra marry, and Xeen becomes a whole world.

### The 17 WoX-only logical maps in `DARK.CC`

| Map ids | Name | Exit on the Clouds side | Key / entry | Content |
| --- | --- | --- | --- | --- |
| 113–116 | Darkstone Tower 1–4 | B3(11,0) | Darkstone key (Alamar dungeon) | Onyx golems; plaque grid puzzle; Gold ID card; Chime seal leading to map 129 |
| 117–120 | Dragon Tower 1–4 | D1(10,5) | Dragon Tower key (Alamar dungeon) | Alister and the Dragon Egg (1M xp); stat stations; 10M xp tomes; roof to map 128 |
| 121–124 | Dungeon of Death 1–4 | E3(3,4) | **Key to Dungeon of Death**, from Sandro once he is freed ("my old home on the other side") | L1: a walk-in **89-clue crossword** of Xeen trivia (+5 levels when complete). L2: Sandro's ballroom and coffins, and four **Shrines of Evil** to destroy (minor 1M xp, lesser 2M, great 5M; the "Ultimate" shrine destroys the dungeon with you in it). L3: gongs and lever, fountain. L4: **Lord Xeen Machine** (destroy for 5M xp), four elemental cores, maintenance papers, a main terminal ("Goober" / "Super Goober" awards) |
| 125–127 | Southern Sphinx 1–3 | A2(11,9) | Amulet of the Southern Sphinx (Roland) | Picard's "Home of the Aged"; Chime of Opening; mummies |
| 128 | Dragon Clouds | via the Dragon Tower roof | — | Silver ID card riddle; runes IN/FI/NI/TY (INFINITY); level crystals |
| 129 | Clouds of the Ancients | via the Darkstone roof | Chime of Opening | Final shrine, `END_WORLD` |

Monster placements in maps 113–129 do not decode reliably against `dark.mon`. For example, they produce "Sandro ×7" in
Dragon Tower and "Yog ×39" in the Dungeon of Death, so these maps probably use another monster table when the side is
flipped. The plausible results are onyx golems in Darkstone, phase and energy dragons in Dragon Clouds, mummies in the
Sphinx, and skeletal liches and screamers in Dungeon of Death L2.

### Darkside content that depends on the Clouds side

- Falista's hut A4(7,1) restores spell points only with the Clouds award "Restored Falista".
- Leafpoint the Tree E2(8,15) talks only to "Civilized One" holders (a Clouds award) and tells of Clouds trees.
- Celia and Derek F4(13,9) need "Rescued Celia" (Clouds) and give a sword.
- Ligono's ghost waits in Olympus after "Freed Ligono" (Clouds) and warns about the Megadragon.
- Southern Tower L4 has a "for the eyes of the prince only" book behind the "Prince of Thieves" award (Clouds).

---

## 3. Side quests, teachers, wells and memberships

### Darkside quest log

The quest log is `qnotes.bin` entries 30–54. Rewards come from the event scripts.

| Quest | Giver (location) | Objective | Reward | Prereq / notes |
| --- | --- | --- | --- | --- |
| Dreyfus, High Priest of Mok | A3(8,10) | Heretics have taken his Western Tower. Get the **tower key** (it lies on L4, so climb in from the roof: Dark Grove rope A3(14,7) → Sky A3 → tower roof), defeat Cult Leader and heretics, meet him at the top | 500k xp, 10k gold, 200 gems, "Helped Dreyfus" | Two clerics (Humble, Pious) beg for mercy; killing them is recorded |
| Four gemsmiths | Linus A3(12,14) ruby; Simon A3(13,12) emerald; Toby A3(15,11) sapphire; Hector B3(1,12) diamond | 5 rocks of their gem plus 100/200/400/1000 gems → a chosen weapon or armour in ruby, emerald, sapphire or diamond | Material-tier gear, repeatable | Rocks come from the Gemstone Mines; the God of Minerals refills them for 250k gold |
| Luna the Druid | A4(13,15) | Return the three **golden statuettes** (Pegasus: Western Tower L1; Dragon: Lakeside sewer; Griffin: Sandro's alcove in Necropolis) | **+5 permanent levels** for each character | The Southern Tower thieves' ledger records who bought each statuette; Thaddeus holds the Southern Tower key |
| Ambrose's bridle | B1(12,5) | Have an enchantress enchant the bridle | 500k xp, 50k gold | Main path; Natasha in Sandcaster |
| Kramer, caravan owner | B3(11,4) | Burn both Ogre forts at D3 (flags 143, 172) | 150k xp, 150k gold | Conflicts with Graalg's friendship |
| Vespar the Wizard | B3(7,1) | Find his staff's **emerald handle** (lying at E3(13,5)) | **Pass to Sandcaster**, 200k xp | Gates the main path |
| Nibbler the monkeydog | B4(3,12) | **Monga Melons** (A4 ×3, B4 ×1) | **Key to Temple of Bark**; later hints about the Sprite Forest dungeon | Feeding him is a running joke |
| Sharla, the Sprites | C4(1,7) | Rescue Princess Sheewana from the Orcs in the Temple of Bark | 40k gold, 2 disks, 200 gems, 250k xp | Dialogue offers polite, mercenary or robbery routes |
| Bosco, the Dwarf King | D1(1,8) | Get the **Chalice of Protection** from the Northern Tower (answer "Chalice" to the voice on L4) | 1M xp, 100k gold, "Taste Tester Royale" | Bosco gives the **Northern Tower key** |
| Ector the Woodsman | E2(3,12) | His ring is in a woodpile at E1(11,12) | Obsidian battleaxe, 500k xp | |
| Caleb the Inventor | E3(13,13) | Gargoyles stole his magnifying glass: destroy the gargoyle lair F1(10,0) | 50k gold, 500k xp | |
| Thaddeus, fountain keeper | F4(6,7) | The **Jewel of Ages** (Eastern Tower L3) | Fountain of Youth (removes magical aging), 1M xp | Gives the **Southern Tower key** |
| Mayor Snarfblad | Castleview (23,27) | Stop **Gettlewaithe** and the gremlin sabotage (talk or fight) | 10k gold, 50k xp | The Gremlin King dialogue is a 3-round choice tree |
| Jethro the mapmaker | Castleview (22,24) | Break his brother **Jasper** out of the town jail (Joe the con man framed him) | 6.5k gold, 10k xp. Trading in Joe's fake map gets a **real treasure map** | The real map leads to Slibo the wizard at E1, who buys it for 2,000 gems and runs off to the Desert of Doom |
| Nadia's necklace | Castleview (27,19) | See main step 3 | Ellinger's tower key | |
| Astra the Good Sorceress | Sandcaster | Defeat **Xenoc** and **Morgana**, who took over the wizard and sorceress guilds | 2M xp, 1,000 gems | Sandcaster's wizards attack if insulted (Blastem's dialogue) |
| Sandro the Lich | Necropolis (10,8) | Fight him, then return his **heart** from the Necropolis sewer | 2M xp, his treasure room, **Key to Dungeon of Death** (WoX) | Without the heart he resurrects and fights again |
| Megan / Dimitri / Queen | Kalindra | Main path | 3M, 5M xp | |
| Alister (WoX) | Dragon Tower L1 | A Dragon Egg | 1M xp, then he drinks the egg potion | A dead adventurer's note says Alister is a fraud |
| Valio the Simple | Castleview sewer | Kill **Rooka** the Queen Rat | 25k xp | His chest holds a diploma from a "School of Evil Wizardry". A "Valio" monster record exists |

### Smaller interactions worth keeping

- **Drawkcab monks.** Four palindrome monks in Castleview give lessons in order, then the Drawkcab award and 25k xp.
  Brother Reger A4(1,4) then asks for the word "Palindromes" (500k xp).
- **Skill challenges.** Miles' cartographer puzzle and James' merchant arithmetic (answer 100 gold) give 100k and 250k xp.
  Edmund's apprentice word problem (answer 3) gives "Superior Intellect".
- **Castleview Public Storage chest puzzles.** One set is numbered 1–9, one lettered PITCHFORK; closing all chests gives
  50k / 250k xp, and Dyson the puzzlemaster comments on them. There is also a runaway treasure chest.
- **Enchanted boulders.** Seven boulders in C2/D2 give letter clues (answer PALADIN, worked out from the clues) and
  release a dead paladin's armour, 1M xp.
- **Diplomacy with factions.** Yog's Sardaj barbarians (B3), Gurodel's giants (D1), Graalg's ogres (D3), Sharla's
  sprites (C4) and Hobstadt's trolls (Troll Holes; "give gold / sacrifice one / fight") each choose peace or war.
- **Camps and lairs.** Barbarian camps A2, B2 and B3, giant lairs C1 and D1, ogre forts D3 and the gargoyle lair F1
  give 50k–100k xp each when burned.
- **Genie lamps.** About 14 lamps on the surface and Skyroads offer wish choices with moral traps: selfish choices kill,
  and one genie takes back its gold "plus interest".
- **Forbidden Fruit huts.** In C4, E4, F3 and F4, each fruit gives a condition plus +10 to one permanent stat.
- **Jojosh the Taskmaster.** Work 10 days for 50 gold. Pure flavour.
- **Elemental merchants on the Skyroads.** Riddles about what lies "between" two elements: Smoke, Dust, Steam, Mud.
  250k xp each.
- **Scarab merchants** at Sky E3 sell resistance scarabs for 300–600 gems.
- **Cyrano Jones** in the Olympus sewer sells a **Tribble** for 100,000 gold. The sewer password door's answer is
  "tribble", and the note fragments TR / IB / BL / ES spell it.
- **Barticus' gym** in the Sandcaster sewer: 50k gold for Body Builder plus +10 End and +10 Might.
- **Sky bandits** charge 10,000-gold tolls; pay or fight.

### Skill teachers

| Skill | Teacher | Place | Price |
| --- | --- | --- | --- |
| Path Finder | Goldur | Castleview | 1,500 |
| Cartographer | Lydia | Castleview | 10 |
| Swimmer | Ordana | Castleview | 250 |
| Direction Sense | Felix | Castleview sewer | 1,000 |
| Mountaineer | Freeda | B2(13,14) | 5,000 |
| Spot Secret Doors | Cornelius the Leprechaun | E4(5,12) | 500 |
| Navigator | Gregor | Sandcaster | 10,000 |
| Prestidigitation | Tibora | Sandcaster | 1,000 gems |
| Merchant | Morgan | Sandcaster | 5,000 |
| Linguist | Natalie | Sandcaster | 25,000 |
| Body Builder | Barticus | Sandcaster sewer | 50,000 |
| Prayer Master | Joseph | Lakeside sewer | 10,000 |
| Danger Sense, Arms Master | Gem, Errol | Kalindra L1 | free |
| Astrologer | (telescope spot) | Kalindra L2 (3,6) | free |

Townsfolk also state travel rules: the desert needs Navigator, and forests and mountains need **two** Path Finders or
Mountaineers.

### Guilds and town passes

| Town | Guild membership | Pass to enter (a quest item) |
| --- | --- | --- |
| Castleview | Metla, 50 gold | Justine the Thief, A4(15,12), 1,000 gold |
| Sandcaster | Niccolo, 20,000 gold | Vespar's quest |
| Lakeside | Riddle at the coven ("WITCH"); a wrong answer drops you into the sewer | Geoffrey in Sandcaster, 5,000 gold |
| Necropolis | 50,000 gold | The head witch's chest in Lakeside's north-west room (Naomi the prisoner tells you where) |
| Olympus | Free | Dragon Pharaoh (Chosen Ones) |

### Darkside stat wells

The well list is `qnotes.bin` 157–171 and 204–205, checked against the events. "Temporary" means the boost lasts until
the next rest.

| Square | Effect | Square | Effect |
| --- | --- | --- | --- |
| A1(2,13) | +2,500 HP, temporary | D1(6,13) | +100 Might, temporary |
| B1(14,13) | +100 all resistances, temporary | D4(12,4) | +10 all stats (shrine prayer) |
| A3(8,14) | +3 levels, temporary (prayer) | D4(2,4) | +50 elemental resistance |
| A3(3,3) / A3(2,10) | +50 HP / +50 SP | E1(2,10) | +1,000 SP (Xanthus' fountain) |
| A4(9,11) / A4(3,10) | +25 Might / +10 AC | F1(13,8) | +500 HP |
| B4(2,2) | +100 Luck (costs 1 gold) | F2(8,5) | +50 magic resistance |
| C1(1,7) | +50 energy resistance | F4(14,3) | +50 AC |
| C2(1,8) | +15 levels, temporary (Shrine of Great Power) | F4(6,7) | Fountain of Youth (after the Jewel quest) |

### Permanent boosts inside dungeons

| Where | Boost |
| --- | --- |
| Ellinger L2 books | +20 fire / +20 electricity resistance |
| Ellinger L4 book | +25 Int, Sorcerers only |
| Temple of Bark L4 | Disciple of Bark: +19 all stats (dial puzzle) |
| Temple of Bark L5 | +50 to four resistances |
| Lost Souls L5 | Caged birds: +6 to one stat each |
| Eastern Tower L4 | +10 all stats; +1 level for +50 years of age; +5 levels for losing every secondary skill |
| Northern Tower L4 | Pillow notes: conditions; one gives +2 levels and +5 all stats |
| Necropolis books | +999,999 xp each, +25 to +100 years of age |
| Necropolis sewer | "Food of the dead": +1 level |
| Alamar L3 and dungeon | +5 levels at each station |
| Escape pods | Alien device: all stats to at least 50, +50 years of age |
| Dragon Tower | +40 Endurance stations |

**Mega Credits, arena, Dragon Clan.** These do not exist on Darkside. The Mega Credits (Newcastle) and the Warzone arena
are Clouds content. There is no "Dragon Clan" in the Darkside data. Dragon content is the Dragon Pharaoh with his
pyramid dragons, Crindr Amn's hatchlings (manual log), the Megadragon on the Skyroads, Scraps, and the WoX Dragon Tower and
Dragon Clouds.

---

## 4. Geography and locations

Place names and coordinates come from `darkmirr.txt` (32 mirror destinations).

| Square | Names and landmarks | Theme | Services, NPCs and entrances |
| --- | --- | --- | --- |
| A1 | Castle Alamar (10,4) | Volcanic waste, lava | Waters of +2,500 HP; Alamar's gate |
| A2 | Forbidden Zone (south border) | Barren highlands | 3 mine entrances; barbarian archer camp |
| B1 | Griffin Pass (12,4) | Mountains | Ambrose and his griffin; Escape Pod 2, Sheltem's pod (2,9); +100 resistances well |
| B2 | Necropolis gate (8,11); Forbidden Zone (15,15) | Lava and mountains | Escape Pod 1, Corak's pod, in lava (3,8); Freeda; 3 genies; barbarian camp; 2 mines; broken pyramid |
| A3 | Dark Grove (14,6); Western Tower (5,9) | Forest | Dreyfus; three gemsmiths; rope to the sky; +3 levels prayer; small wells |
| A4 | Castleview gate (14,11); Castle Kalindra (6,14) | Grassland and river; the start | Luna, Justine, Brother Reger, Falista's hut, melons, castaway shipwreck, bottle messages |
| B3 | Acid Pond (2,13) | Grass and barbarian land | Yog's Sardaj camp, Kramer, Vespar, Hector (diamonds), mine |
| B4 | — | Meadows | Nibbler, melons, 3 troll holes, +100 Luck well |
| C1 | Quivering Forest (11,4) | Highland forest | Giant lair; +50 energy resistance |
| C2 | Desert of Doom (15,1) | Desert | Enchanted boulders (PALADIN); +15 levels shrine; genies; food thieves |
| D1 | Northern Tower (2,9); Parabolic Barrier | Highlands | Gurodel's giants, Bosco's dwarf hall, +100 Might, broken pyramid |
| D2 | Great Pyramid (0,5); Perishing Sands (15,4) | Desert | Sandcaster sewer exit (12,2); boulders |
| C3 | Gemstone Range (5,7) | Mountains | 3 mines; troll hole |
| C4 | Sprite Forest (1,9) | Enchanted forest | Sharla; Temple of Bark entrance (2,8); 5 troll holes; Forbidden Fruit |
| D3 | Ogre Pass (11,9) | Hills | Graalg and two ogre forts; mine; genie |
| D4 | Southern Tower (2,7) | Woods | +10 all stats shrine; +50 elemental resistance; troll holes |
| E1 | Magic Mountain (1,12) | Mountain | Xanthus and Slibo (wizards' camp); +1,000 SP fountain; Ector's ring |
| E2 | Forest of Peril (7,15) | Deep forest | Leafpoint the tree, Ector |
| F1 | Snow River Rapids (6,3); Castle Blackfang (9,11) | Snow and river | Ambrose's griffin entry; gargoyle lair; +500 HP |
| F2 | Lakeside gate (2,15); Isle of Lost Souls (6,8); Octopod Lake (6,3) | Lake | Boat to the isle; Mirabeth Point; Lost Souls entrance (6,10) |
| E3 | Sandcaster gate (5,12); Crossroads (14,11) | Trade road and desert edge | Crossroads stalls: Aldo (food), Luigi (robes, 50k), Katrina (necklaces), Buckler (belts), Erica (boots), Caleb; Vespar's handle |
| E4 | Aging Forest (13,10); Howling Woods (0,14) | Forest | Cornelius; pot of gold 250k (Leafpoint's treasure); low branches |
| F3 | Eastern Tower (9,9); River of Wrath (2,5) | Forest and river | Fruit huts |
| F4 | Venom Pond (4,10) | Swamp and forest | Thaddeus, Celia and Derek; +50 AC |

### Towns

| Town | Size | Character | Services | Key content |
| --- | --- | --- | --- | --- |
| **Castleview** | 32×32 | The besieged human hub. Humans, elves, dwarves and gnomes are confined here; Gettlewaithe's gremlins sabotage it | Bank, smith, guild, tavern, temple, training, travel pyramid | Story start; 35 NPC sites; sewer with 5 shafts; Ellinger's Tower; jail; storage puzzles |
| **Sandcaster** | 32×32 | Merchant city ruled by evil wizards (Xenoc, Morgana, roughly 47 hostile casters) | Smith, guild, tavern, temple, training. **No bank event** | Skill school town; Natasha; Astra's quest; sewer with gym and a long tunnel to D2 |
| **Lakeside** | 16×16 | Witch coven. Children are turned into goblins; failed recruits become monsters for Blackfang or the Isle | Guild only; tavern and smith destroyed | 5 prisoners to free (200k xp each); statuette in the sewer; boat to the Isle |
| **Necropolis** | 16×16 | City of the undead (power liches, higher mummies) | Guild | Sandro; deadly aging books; a skull's long necromancer tale; sewer with his heart |
| **Olympus** | 16×16 | Hidden city of the gods on the Skyroads (Sky C2); Greek gods give hints | Smith, tavern, temple, training, guild | Soul Box; prophecy plaques; Sheltem's name; Lucio's sky boats |

### Castles, towers and dungeons

| Place | Levels | Theme | Main monsters |
| --- | --- | --- | --- |
| Ellinger's Tower | 4 | Wizard's trapped tower | Beholder bats |
| Castle Kalindra | 3 + dungeon | Restored royal castle; safes | Dungeon: Scraps (pet dragon, 3,000 HP), dragon mummies, power liches |
| Castle Blackfang | 3 + dungeon | Vampire castle; coffins | Vampires, vampire lords, Count Blackfang; octopods in the dungeon |
| Castle Alamar | 3 + dungeon | Machine fortress; statues praise Alamar; power-field heads | Annihilators, autobots |
| Western Tower (Mok) | 4 | Religious schism | Clerics of Mok, Mok heretics, Cult Leader |
| Southern Tower | 4 | Thieves' den; gongs; Ali Baba chest ("open sesame", 300k gold) | Rogues, thieves, Master Thief |
| Eastern Tower | 4 | Mages | Mystic, Magic and Mega Mages, a Gamma Gazer |
| Northern Tower | 4 | Voweless Knights' disemvowelled proverbs | Slayer, Death and Doom Knights |
| Temple of Bark | 5 (L5 32×32) | Orc tree cult: Bark, the Weed, Barkman | Orc guards, shamans, elites; Shaalth the Orc King (poison tea); 9 Barkmen (4M xp) |
| Dungeon of Lost Souls | 5 (L5 32×32; ids 78/80/79/81/82 in floor order) | "Think positive" | Minotaurs, gorgons |
| Great Pyramid | 4 (three 32×32) | The Pharaoh's seat, built "during the Creation" | Cloud and green dragons |
| Escape Pods 1–2 | 32×16 each | Starship interiors (phaser and photon consoles, logs) | — |
| Gemstone Mines | 32×32, separate pockets | Mines with rock veins | Beholder bats, sabertooths |
| Troll Holes | 32×32, separate pockets | Pits you fall into; the Thieves' Guild hunts its stolen gold | Troll grunts, guards and chiefs; Hobstadt |
| 4 town sewers + Olympus sewer | — | — | Rats and slugs, hags and beholder bats, sewer stalkers, lava roaches |

### Sky layer

The sky layer is the **Skyroads**: a 6×4 grid of squares above the surface.

- **Ways up:** the Dark Grove rope (A3), tower roofs, Castle Kalindra L3 (to Sky A4), Ellinger's L4, Alamar L3 and
  Blackfang L3, and Lucio's boats for the Chosen Ones.
- **Content:** the Megadragon guards Alamar's roof door at A1; sky golems, griffins and cloud/green dragons patrol. Also
  rest stops, "Eat at Joe's" and "Speeding??" signs, bandits, elemental merchants, scarab sellers and the Sky Lake.
- **Falling** off the edge drops you to the surface (or to a mirror destination at Sky E3).

### Elemental planes

There are four 16×16 maps, each with its sleeper, its test and its chest. They exist in MM5's data, but only the WoX
finale needs them.

---

## 5. Monster progression by area

Placements come from the `.mob` sprite tables against `dark.mon`. The experience values are MM5's per-monster award, a
rough difficulty proxy.

| Tier | Areas | Monsters (MM5 xp) |
| --- | --- | --- |
| 1, start | Castleview, its sewer | Goblins (1k; 52 in town), gremlins and gremlin guards (2–3k), sewer rats and slugs (1–2k), Rooka |
| 2 | A3, A4, B3, B4 | Barbarians (5k), arachnoids (4k), electrapedes (10k), medusa sprites (5k) |
| 2–3 | C4, C3, D4, Temple of Bark | Medusa sprites, dark wolves (10k), ogres (10k); orc guards, shamans and elites (5–15k), Shaalth; Barkman (4M, optional L5) |
| 3 | Troll Holes, Gemstone Mines, Southern Tower | Trolls (10–25k), sabertooths, beholder bats (10k); rogues and thieves (5–20k) |
| 4 | Western Tower, D3, C2, D1, C1 | Clerics and heretics (30–50k); ogres; iguanasaurus (100k), sand flowers; giants (100k), griffins (60k) |
| 5 | Sandcaster and its sewer; E and F squares | Wizards and sorceresses (60–120k), Xenoc and Morgana; sewer hags (50k); mantis ants (40k), killer cobras, hell hornets (50k), armadillos (60k), gargoyles (30k), vulture rocs (200k) |
| 6 | Lakeside, Eastern Tower, Northern Tower, Lakeside sewer | Witches (80–120k); mages (100–500k); knights (50–500k); sewer stalkers |
| 7 | Lost Souls, Necropolis, Blackfang | Minotaurs and gorgons (250k); mummies and power liches (100–200k), Sandro; vampires (200–400k), Count Blackfang (2M) |
| 8 | Kalindra dungeon, Great Pyramid, Skyroads | Scraps and dragon mummies (2M); cloud and green dragons (500k); sky golems (200k); griffins |
| 9 | North-west: A1, A2, B1, B2 | Gamma gazers (1M), lava dwellers (500k), iguanasaurus, griffins, giants |
| 10, end | Castle Alamar; elemental planes | Annihilators (1M; 50 on L2), autobots (1M); Fire Blower, Whirlwind, Earth Blaster, Tidal Terror (250–500k) |
| Optional superboss | Sky A1 | **Mega Dragon** (100M xp, 64,000 HP), guarding Alamar's roof |
| WoX | Dragon Clouds, Darkstone, Dungeon of Death, Sphinx | Phase and energy dragons (2M), onyx golems (1M), skeletal liches and screamers, dragon and ghost mummies |

Difficulty rises toward the north-west, the same direction as the story. The south-west start is safe, the east is mid
game, and the north-west volcanic region and Alamar come last.

---

## 6. NPCs, factions, items and set pieces

### NPCs and factions

- **Major characters:** Dragon Pharaoh (Guardian of Xeen, a reptile), Ellinger, Queen Kalindra, Dimitri and Megan,
  Ambrose, Prince Roland, Corak, Sheltem/Alamar, Count Blackfang, Sandro, Xenoc and Morgana against Astra.
- **Factions:** Gettlewaithe's Gremlins, Yog's Sardaj barbarians (friends of the giants), Gurodel's Giants, Graalg's
  Ogres (paid by Alamar), Sharla's Sprites, Shaalth's Orcs and the cult of Bark, the Lakeside coven, the Mok priesthood
  and its heretics, the Voweless Knights, the Drawkcab monks, the Thieves' Guild, and the Olympus gods.
- **Comic recurring cast:** genies, Joe and his fake maps, Nibbler, Cyrano and the tribble, Leafpoint's endless
  philosophy.

### Quest items

| Group | Items |
| --- | --- |
| Main path | Dragon Pharaoh's Orb, Energy Disks ×20, Songbird of Serenity, Bridle and Enchanted Bridle, Queen Kalindra's Crown, Key to the Ancient Pyramid, Pass to Olympus, Soul Box / Soul Box with Corak, Cube of Power |
| Keys | Ellinger's Tower, Great Western, Southern, Eastern and Northern Towers, Temple of Bark, Dungeon of Lost Souls; WoX: Dragon Tower, Darkstone Tower, Dungeon of Death |
| Passes | Castleview, Sandcaster, Lakeside, Necropolis, Olympus |
| Side quests | Golden Pegasus, Dragon and Griffin Statuettes, Chalice of Protection, Jewel of Ages, Sandro's Heart, Ector's Ring, Vespar's Emerald Handle, Caleb's Magnifying Glass, Onyx Necklace, Monga Melon, Ruby/Emerald/Sapphire/Diamond Rocks, Treasure Map and Fake Map, Vulture Repellant (a 25k gold scam), Tribble |
| WoX | Amulet of the Southern Sphinx, Chime of Opening, Gold and Silver ID Cards, Dragon Egg, Widget, Xeen's Scepter |

### Set pieces worth keeping

1. The **orb** that chooses its bearer, linking a herbalist's find to a sealed dragon god.
2. The **out-of-phase castle restored in four stages**. As a 3D space it can fade in wing by wing.
3. The **griffin flight** into a castle with no way in, and the vampire Queen cured by her crown.
4. The **sealed pyramid**, its puzzle floors and the reptile Pharaoh.
5. **Crashed starships in lava**, with log computers that reveal the science-fiction truth. The Corak cipher.
6. **Corak smuggled in a Soul Box** into the enemy's lair. The self-destruct ending.
7. **Olympus**, a city of the gods in the clouds, reached by a celestial boatman.
8. **Factions that can be talked to**, with peaceful and violent ways to the same reward.
9. The **Megadragon** as an optional superboss guarding a shortcut.
10. The **Gremlin court** and its escalating dialogue.
11. The Lost Souls "think positive" gates.
12. Alamar's statues praising a rogue AI, and the "true name" gate.
13. WoX: a wedding on the clouds, sleepers in the four elemental planes and reflectors at the world's corners.

### Grid-only tricks that will not carry over directly

| MM5 trick | Why it fails in MM6–MM8 | Possible replacement |
| --- | --- | --- |
| Teleport-conveyor corridors (Alamar L1) and fall tiles to L1 (Alamar L2/L3) | Rely on stepping onto a single cell | Moving floors, trapdoors |
| Facing-direction events and blocks that turn into walls when you step on them | Depend on grid facing and grid steps | — |
| Out-of-phase stairs that "pass through like mist" | Grid trigger | Locked or ghosted geometry |
| Runaway treasure chests | Move one cell at a time | — |
| Answers typed into word or number prompts | Overused relative to MM6–MM8 dialogue | Some fit MM6–MM8; others can become dialogue choices |
| Cell-based crossword (Dungeon of Death L1) | Built from cells | — |
| Skyroad falls through the void | No separate sky layer at the same position | Floating islands or a separate sky map |
| Forest and mountain passage needing two Path Finders or Mountaineers, the desert needing Navigator | MM6–MM8 have no matching traversal skills | — |
| Thievery-percentage safe cracking with false combination hints | Grid prompt mechanics | Disarm-trap or lockpick checks |
| Permanent +level and +stat stations everywhere (+5 levels, Luna's +5, Bark's +19) | Incompatible with MM6–MM8 balance | Rescale or turn into skill and stat books |
| 6 Sky / 4 plane layers as cardinal-grid squares | No equivalent geography | Authored maps |

Pass checks at every town gate are possible in MM6–MM8 but tedious. Keep them only where the story needs them
(Olympus, Necropolis).

---

## 7. Critique of the earlier MM5 projects

### What was built

**Projects reviewed:**

- `level_generation/projects/mm5_world_feasibility/` — feasibility study and data inventories.
- `level_generation/projects/mm5_castleview_kalindra/` — the Castleview–Kalindra region build.

**What exists:**

- One **environment-only** ODM, `mm5_sw.odm` (Castleview plus the A3/A4/B3/B4 countryside). It has 326 BModels, 727
  scenery records and **121 Lua placeholders that only print "not implemented yet"**.
- It has **no NPCs, monsters, encounters, rewards, services, quests or BLVs**. All five milestones were "accepted" on
  2026-09-09.
- It runs only from an isolated `local_playtest/` installation, using `play.sh` and a level-25 test party.
- **No `mm5` world is mounted in `assets_dev/worlds/`**; only mm6–mm9 exist there.
- The project folder holds about 12 GB, mostly reviews, staged copies and four backup installations.
- Nothing else was built: no sky fixture, no other region, no interiors.

### Reliable and reusable

- **Chunk ownership and logical-map assembly** (`MAP_INVENTORY.md`, `chunks.csv`): which blocks form the 32×32 maps, the
  32×16 pods and the Lost Souls floor order. This matches `index.csv`.
- **Identification of the 17 maps** 113–129 as WoX content. The map list is correct.
- **Raw position data** (`sites.csv`, `travel.csv`, `inventory.json`): mechanical lists of every event coordinate, label
  and teleport. They are reliable as lookup tables, though they do not decode quest logic.
- **Region and landmark anchors** from `darkmirr.txt`, and the correction that Castleview's gate is in A4.
- The **indoor wall-bit decoding fix**.
- The list of **town passes and key relationships** in FEASIBILITY §8. It is mostly right, with the errors below.
- `RESIDENTS.md` and `interior_contacts.json`, as a census of who stands where in Castleview. It gives no reason to keep
  all of them.

### Factual errors or gaps found

| Earlier claim | What the data shows |
| --- | --- |
| Kalindra takes energy disks "in successive groups of 5, 5 and 10" | **Four stages of 5**: L1, L2, dungeon, L3 (flags 168, 153, 154, 155) |
| The Soul Box route is "sewer-dependent" | The Soul Box is on the Olympus street map (10,14), behind the "Soul Storage" door. The sewer holds Cyrano's tribble password door. No sewer dependency was found |
| The 17 WoX maps are "excluded" | For a WoX adaptation this is backwards. The real ending, Roland, the sleepers and the cross-side tie-ins (Falista, Celia, Leafpoint, Ligono, Prince of Thieves) all depend on it. The study never looked at Clouds |
| The quest list is "a key dependency inventory, not a decompilation" | Accurate as a description. The rewards, stage flags, dialogue branches and peaceful-or-violent outcomes were therefore never captured. This document supplies them |
| The elemental planes are "standalone MM5 maps" | They are reachable in MM5, but their sleepers need "Chosen one" and only matter for the WoX finale |

### Weak decisions for a new-map, MM6–MM8-style design

1. **Copying the geography: 2×2 MM5 squares per ODM, 6 surface + 6 sky + 4 planes = 16 outdoor maps, plus about 22 BLVs.**
   This preserves MM5's square layout instead of the story's needs. Many squares contain one fountain and a genie, and
   the 3×2 regional grid forces filler.
   - Instead, the story needs about 5–7 outdoor maps, each a story act or biome: the Castleview valley, the eastern trade
     coast with Sandcaster, the lake country with Lakeside and Blackfang, the desert with the pyramid, and the
     north-west volcanic land with Alamar, Necropolis and the pods.
   - It also needs one sky map (Olympus and the Skyroads) and one or four plane maps.
2. **Calculating world scale from source cells** (1 cell = 1,446–1,536 units) and travel-edge profiles for neighbours
   that will never be built. This scale planning has no use once maps are designed fresh.
3. **Town density decided by MM5 interaction-cell counts.** All 48 Castleview NPC sites were kept, including one-line
   joke NPCs, and they drove 24 town assemblies. MM6–MM8 towns use houses with NPC dialogue, so most of these one-liners
   should become rumours or topics.
4. **Rotating Castleview 180°** to fit the grassland "while keeping source coordinates attached". This shows the effort
   went into staying faithful to the source rather than into designing the town.
5. **Environment first, gameplay never.** The work produced a polished empty map with heavy evidence (24 readback audits,
   hash-pinned releases, 135 progress entries) before any quest, monster or interior. Nothing on the story's critical
   path was proven: the out-of-phase castle, the griffin flight, the pyramid floors, the pod, the sky.
6. **Flight left unresolved.** Flight was named as the main compatibility issue and then left as "explicitly designed
   local rules". A new design should decide this up front: MM6–MM8 Fly makes the Skyroads, the Blackfang approach and
   town walls trivial, so these need indoor or roofed solutions or the MM9 Fleet-Foot rule.
7. **Six standard services kept per town, with MM5 skill gating** (two Path Finders and so on) kept as constraints.
   These should be translated into MM6–MM8 terms rather than preserved.

**What to reuse:** the inventories as a fact lookup (sites, travel, chunks) and this document's quest graph. Treat the
Castleview ODM as a visual study only. It cannot be extended into the new world.

---

## 8. Suggested playthrough order

MM5 levels are approximate and based on memory and the monster xp tiers in §5. The MM6–MM8 bands are suggestions for
the new world's curve.

| Act | Content | MM5 party level (memory, approx.) | Suggested MM6–8 band |
| --- | --- | --- | --- |
| 1 | Castleview: orb, Oorla, Nadia's sewer (rats, Rooka, Valio), Jasper, Drawkcab, Gremlin court (3 disks); buy the Castleview pass | 1–6 | 1–6 |
| 2 | SW countryside: Luna, Nibbler and melons, Justine, gemsmiths and the first mines; Ellinger's Tower (key from Nadia) | 5–10 | 5–10 |
| 3 | Sprite Forest and the Temple of Bark (sprite rescue, 2+2 disks); Yog; Ogre Pass (Graalg or Kramer); Troll Holes | 8–15 | 8–14 |
| 4 | Western Tower by the sky rope (Dreyfus, Pegasus statuette, 2 disks). Kalindra L1 once you have 5 disks | 12–20 | 12–18 |
| 5 | Vespar's handle, then Sandcaster: skills, Natasha, Astra against Xenoc and Morgana, Barticus; the Eastern Tower key from a chest | 18–30 | 16–24 |
| 6 | The east: Crossroads, Caleb (gargoyles), Ector, Leafpoint, Thaddeus (Southern key), Southern Tower (thieves' ledger, 2 disks); Bosco and the Northern Tower (Chalice, 2 disks); giants (2 disks) | 20–35 | 18–28 |
| 7 | Kalindra L2 with 10 disks: Megan, then the Lakeside pass, the witches, the boat, Lost Souls, the Songbird, Dimitri; L2 safes (6 disks); Eastern Tower (Jewel) | 30–40 | 24–32 |
| 8 | Ambrose and the bridle, Necropolis (pass from the Lakeside head witch; Sandro), dungeon and L3 with 20 disks, Blackfang (Count), crown, Queen; Luna's three statuettes | 35–50 | 28–38 |
| 9 | Great Pyramid, Pharaoh, Corak's pod, Chosen Ones, Lucio, Olympus, Soul Box, Corak | 45–60 | 35–45 |
| 10 | North-west wilds (gamma gazers), then Castle Alamar; Darkside ending, Cube | 55–70+ | 40–50 |
| WoX | Clouds main quest and the Scepter (other note); reflectors; elemental planes and sleepers; Roland and the Alamar dungeon keys; Dragon Tower and Dragon Clouds; Darkstone; Sandro's Dungeon of Death; Southern Sphinx (Widget from Halon); Clouds of the Ancients | 70–100+ (memory) | 50–60+ |

Optional at any late point: the Megadragon (Sky A1), the Dungeon of Death shrines and crossword, the Dragon Tower tomes.

---

## Appendix: event state flags used above

| Flags | Meaning |
| --- | --- |
| 114 / 156 / 170 | Met Ellinger / Queen saved / Orb returned (Oorla's dialogue states) |
| 168, 153, 154, 155 | Kalindra L1, L2, dungeon, L3 restored |
| 157, 158, 160–162 | Dimitri and Queen dialogue states |
| 164 | Ambrose has the enchanted bridle (griffin flight unlocked) |
| 167 | Sprite rescued |
| 169 | Corak freed |
| 117–118 | Chosen-One access (Olympus, Lucio) |
| 123–126 | Sleepers awakened |
| 143, 172 | Ogre forts burned |
| 159 | Sandro freed |
| 115 | Mirror portals active |
