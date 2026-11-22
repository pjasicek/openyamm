# Xeen: story, quests and promotions

Proposal, 2026-11-12; revised 2026-11-14 for the user's decisions after the three reviews (README, "Decisions of
2026-11-14"; `reviews/`). Part of the [Xeen world design](README.md). Map codes (X1–X9 Cloudside, D1–D7 Darkside, P1–P5
planes and finale) are defined in [WORLD_DESIGN.md](WORLD_DESIGN.md#3-shape-of-the-world); dungeon codes (XD-, DD-, FD-)
in [MAPS.md](MAPS.md#dungeons). Source facts are in `research/MM4_CLOUDS_CONTENT.md` and
`research/MM5_DARKSIDE_CONTENT.md`; their section numbers are cited as [C§n] and [D§n].

**Rules used throughout.**
- The source's beats, characters and dependencies are kept. Short original lines (signs, plaques, NPC quips, jokes,
  Joe's invoice, the guidebook) are quoted or closely paraphrased; long dialogues are rewritten in MM6–MM8
  house-dialogue form in the original's spirit (decision of 2026-11-14; voice: WORLD_DESIGN §1).
- Rewards are MM6–MM8 sized: experience in the 1k–100k range by level (calibrate against MM7/MM8 quests of the same
  level), gold, items from a treasure level, and occasionally a skill point or +5 to a stat. **Never** permanent +levels,
  +20 stats or millions of experience, which the source hands out freely.
- Every quest has a journal line (qbit), one sentence in the source's terse style ("The dwarf mines are still being
  over-run. Please help them."), and each multi-step quest an autonote per step.
- Quest experience: at most 1.5 levels' worth per quest (1,000 × the act's typical party level × 1.5) in Acts I–II,
  1.0 in III–IV, 0.75 after. A promotion pays its act's share, inside the act's budget: the first (T1-A) about one
  level at its quest's level (8,000); a later promotion that is its own quest a quarter to a half of a level (Act IV:
  8–12k); one added to content already paid (a route choice, a talk, a fight in a story dungeon) about a tenth of a
  level (about 3k in Act IV) (D-1.1, D-16, 2026-11-20; §3). Act quest
  budgets per member: I 16.5k, II 83k, III 132k, IV 160k, V 209k, VI 210k, optional 70k (MAPS §0). Quest gold about
  0.4M over the campaign.
- **No early twist.** Topics and signs that say the court's Roland is false, or that the real Roland is Alamar's
  prisoner (Olympus, Castleview, Drusilla), show only after M21. Drusilla's "I sense Alamar is an assumed name" is
  fine before it, because it is about Alamar.
- **Riddles** follow the decision of 2026-11-13 (README): a password or riddle stays only where the game says the
  answer plainly first; the rows below name the answer-giver.
- "Peaceful or violent" choices of the source stay wherever they exist: both routes give the quest item; the peaceful
  one keeps a faction friendly (`relations.yml`), the violent one gives more loot and experience.

## 1. Main quest

42 journal steps: the top of the calibration range (25–30 per world), because this is two games' story. Steps
marked ◆ are the gates that decide the level curve.

### Act I. Vermin (X1, levels 1–7)

| # | Step | Where | Needs | Gives |
| --- | --- | --- | --- | --- |
| M1 | Opening message: "Vertigo. For weeks you dreamt of an old man in a dark tower who begged you to finish 'the sword'. Then a bolt from the sky destroyed Newcastle, and you woke here among its survivors." (Crodo's dreams, which he sent to Newcastle's scientists.) Mayor Gunther asks them to clear the town's plague of slimes and doom bugs. Crodo's bottle ("Help! I'm in Darzog's tower!--Crodo") lies in Pitchfork Creek (X1); a second on Lake Darzog's shore (X2) | Vertigo, town hall | — | Journal (until M2). No reward of its own: as in the source, Gunther thanks and pays the party once, for the cleanup and Joe's exposure together, in M2 (D-78) |
| M2 | Joe the Exterminator always arrives just after the pests. His locked warehouse holds an invoice for "breeder slimes, one mated pair". Expose him | Joe's Warehouse (XD-01, S) | Key under the rain barrel in his yard; the hiccuping drunk in Lady Geraldine's Tavern points to the warehouse ("He...he (hic) breeeds (hicup) Breeeeeds them in the (hic) warehouse") | Joe flees; his shop closes; Gunther's reward |
| M3 | Gunther: the Red Dwarf mines north of town are overrun by the Mad Dwarf Clan. Kill the Clan King | Red Dwarf Mines (XD-02, M), then the Deep Mine (XD-03, M) below it | — | Red Dwarf Badge; the dwarves reopen their mine as a shop and a teacher |
| M4 ◆ | Old Valia of Toad Meadow: the witches of the Witch Tower turn children into goblins. Bring back the Alacorn of Falista and the realm will call you **Crusaders** | Witch Tower (XD-04, M) | Crystal Key from Valia | Crusader title (party award); first-tier promotion T1-A (§3); the tower roof opens to X8 |

### Act II. The King's Crusaders (Cloudside, levels 7–20)

| # | Step | Where | Needs | Gives |
| --- | --- | --- | --- | --- |
| M5 | The river road west to Rivercity (X2), the hub. Audience at Castle Burlock: "only Crusaders may enter". King Burlock wants the Sixth Mirror, last seen near the great volcano, and offers an earldom. "Prince Roland" stands at his side | Castle Burlock (XD-07) | M4 | Mirror quest; Princess Roxanne's side quest |
| M6 | Artemus, privately: Crodo, the kindly old sorcerer, was the King's friend, and Baron Darzog, the King's master sorcerer, was jealous of him. Both have vanished; Darzog's island tower has been sealed since. "If the King were not so obsessed with the Sixth Mirror, he would send you there himself." | Castle Burlock | M5 | Journal: find Crodo |
| M7 ◆ | Artemus: the old pyramids are said to lead to "the land below the land", where Roland went before he came home. The King will not hear of it, so he gives the party the **Pyramid Sigil** quietly. (No word that Roland is false.) | Castle Burlock | M6 | **Darkside opens** at about level 14 (Vertigo pyramid ↔ Castleview pyramid; D1 is set for 15–18). Starts Act III |
| M8 | Ebenezer the Taxman sells the ruins of Newcastle: 12,000 gold for the deed (MM6–MM8 never ask more of a level 10–15 party) | Newcastle site (X3) | — | Deed; starts the castle project (§4.1) |
| M9 | Emerson the royal engineer builds the walls for 5 King's Megacredits | Castle Burlock, Newcastle | Deed | Walls; the **Stone of a Thousand Terrors** |
| M10 | Megacredits lie in three evil places: the Temple of Yak (needs the Yak Stone, from Mirabeth's quest Q-C12), the Tomb of a Thousand Terrors, and the Golem Dungeon | Temple of Yak (XD-06, X2), Tomb (XD-08, X3), Golem Dungeon (XD-09, X5) | stones | Megacredits (8 + 8 + 14 in the source; keep 3 sources, 15 needed over M9, M11 and M22) |
| M11 | Keep for 5 more | Newcastle | walls | Keep; smith and training; the **Golem Stone** |
| M12 | A talking skull deep in the Cave of Illusion sells the Enchanted Key to the Tower of High Magic (gems, not gold) | Cave of Illusion (XD-10, M) | — | Enchanted Key |
| M13 ◆ | The Tower of High Magic holds the Skeleton Key to Darzog's Tower. Its roof opens to the High Magic half of X8 | Tower of High Magic (XD-11, M) | Enchanted Key | Skeleton Key |

### Act III. The Land Below (Darkside D1–D3, levels 18–30, in parallel with the end of Act II)

| # | Step | Where | Needs | Gives |
| --- | --- | --- | --- | --- |
| M14 | The party steps out of the pyramid under an amber sky with a small, pale sun. Castleview is besieged by the Queen's enemies and sabotaged by gremlins; strangers are not welcome. Justine the Thief sells a **Castleview pass**, or the mayor grants one for the gremlin quest | D1 | M7 | Entry to Castleview |
| M15 | Zelda the Herbalist found a glowing orb in a crater and does not want it. Madame Oorla the gypsy reads it: it belongs to the Dragon Pharaoh, but "first it must see Ellinger" | Castleview | — | **Dragon Pharaoh's Orb** |
| M16 | Nadia's onyx necklace was taken by the sewer rats; she holds the key to Ellinger's tower | Castleview Sewer (DD-01, M) | — | Key to Ellinger's Tower |
| M17 | Ellinger's Tower is a trap-laden test (a moral question at the door, the password "Ellinger" at the top). Ellinger: Alamar moved Castle Kalindra out of phase; **20 Energy Disks** bring it back, five at a time | Ellinger's Tower (DD-02, M) | Key | Energy Disk quest (§4.2); Darkside's sun begins to fade (sky preset `_fading`) |
| M18 | Disks come from the factions and towers of the Darkside: gremlins (3), sprites (2), giants (2), ogres (2), the four towers (2 each), the Temple of Bark (2), Kalindra's own safes (6) | many | — | Disks; each faction has a peaceful and a violent route |
| M19 | 5 disks: Kalindra's gate and first floor return. 10: second floor | Castle Kalindra (DD-03, staged) | disks | Throne room, Gem and Errol (teachers); Dimitri and Megan |
| M20 | Megan: her father Dimitri, captain of the guard, has lost all hope. Only the Songbird of Serenity can lift his despair; it is caged in the Dungeon of Lost Souls on the lake isle | Kalindra L2 | stage 2 | Key to the Dungeon of Lost Souls |

### Act IV. Unmasking (both faces, levels 30–42)

| # | Step | Where | Needs | Gives |
| --- | --- | --- | --- | --- |
| M21 ◆ | Darzog's Tower, where magic fails. Kill Baron Darzog and his clones; free **Crodo** from a secret room | Darzog's Tower (XD-12, L) | Skeleton Key | Crodo: "Roland" is **Lord Xeen**, an undead general of a greater master; his hideout is in the clouds above this tower; only the experimental sword buried under Newcastle can kill him. The roof opens to X9 |
| M22 | Artemus grants the Excavation Permit; Emerson clears the caved-in dungeon for 5 more Megacredits | Burlock, Newcastle | M21, M11 | Newcastle stage 3 (temple, bank) |
| M23 | The sword vault's door wants a password whose syllables lie scattered in the Newcastle ruins (la, bo, ra, to, ry); a Shangri-La NPC says it outright ("I hear the secret password for Newcastle dungeon is 'laboratory'. Not much of a secret if you ask me.") | Newcastle Keep's dungeon (XD-13, S, stage 3) | permit | **Xeen Slayer Sword** (unique artifact, §MONSTERS_AND_ITEMS) |
| M24 | The Songbird, freed at the bottom of five floors of "think positive" gates. Dimitri recovers: the Queen was given to Count Blackfang, who made her a vampire; only her own crown can undo it. He sends you to Ambrose | Dungeon of Lost Souls (DD-12, M), Kalindra | M20 | Kalindra L2 safe combination (6 disks); Ambrose's name |
| M25 | Ambrose, the Queen's Knight, has caught a griffin but needs its bridle enchanted. Natasha the Enchantress in Sandcaster can do it, for a fee and a Sandcaster pass (Vespar's quest Q-D8) | Griffin Pass (D6 south edge), Sandcaster | M24 | Enchanted bridle; the griffin flight |
| M26 | 15 and 20 disks: Kalindra's dungeon and third floor; the mirror network wakes | Castle Kalindra | disks | Services; Darkside mirrors; the crown safe |
| M27 ◆ | Castle Blackfang: the griffin lands the party on the walls. Kill Count Blackfang; find the Queen in the dungeon; bring her the crown from her own bedroom safe | Castle Blackfang (DD-14, M) | M25, M26 | Queen Kalindra restored (carried out after nightfall); **Key to the Great Pyramid**; award "Saved the Queen"; the sun fails further (sky preset `_failing`) |

### Act V. Two Thrones (levels 42–55; the two halves in either order)

| # | Step | Where | Needs | Gives |
| --- | --- | --- | --- | --- |
| M28 | The Great Pyramid: four puzzle floors (torch levers, a number lock, a teleport maze) up to the **Dragon Pharaoh**. Return his orb. He explains: Alamar is Sheltem, a guardian gone rogue, who would steer Xeen away from its sun | Great Pyramid (DD-15, L) | Pyramid key, Orb | The Pharaoh cools the lava around the "second meteor" |
| M29 | Escape Pod 1, half sunk in lava: the stasis field answers only an Ancient phrase, which the pod's console shows in plain words. **Corak** wakes; he must hide from Sheltem's senses | Corak's Pod (DD-16, S) | M28 | Journal: find a vessel |
| M30 ◆ | The Pharaoh names the party the **Chosen Ones** | Great Pyramid | M29 | Pass to Olympus; Lucio's celestial boats; the Skyroads (D7) |
| M31 | Olympus, the city of the gods. Take the only **Soul Box** from Soul Storage; a plaque names Alamar's true name | Olympus (D7) | M30 | Soul Box |
| M32 | Corak enters the Soul Box | Corak's Pod | M31 | Soul Box with Corak |
| M33 ◆ | **Castle Alamar** (annihilators and conveyor halls; the true-name gate on L2). Without the Soul Box the party is thrown out. With it Corak confronts Sheltem and starts his self-destruct; the party escapes with the **Cube of Power** | Castle Alamar (DD-17, L) | M32 | Cube of Power; "Defeated Sheltem" (cinematic); Darkside's sun returns to full strength |
| M34 | Slick the Gamemaster's carnival on the Clouds of Xeen (his patter verbatim, "No one may enter Castle Xeen without a cupie doll!"): four stat games (Might, Speed, Endurance, Accuracy) win four dolls; trade them for the Lord Xeen doll that the gate guard demands | X9 | M21 | Entry to Castle Xeen |
| M35 ◆ | **Castle Xeen**: destroy the guard machines and elemental generators that power its barriers; kill **Xeen's Pet** and **Lord Xeen**, whom only the Slayer Sword can harm | Castle Xeen (XD-19, L) | M23, M34 | **Xeen's Scepter**; the Sixth Mirror shatters (cinematic); King Burlock: "Thank you for rescuing Xeen from that foul spirit. It is a pity about the mirror, though." … "And my brother? If he lives, he is on the other side. Go to him." (The original "Your destiny lies on the darkside of Xeen" only if Darkside is still unvisited, possible only in the lean order.) Lord Xeen takes damage only from the Slayer Sword (per-actor behaviour, PRODUCTION E11) |

### Act VI. One World (levels 55–65, optional content to 70)

| # | Step | Where | Needs | Gives |
| --- | --- | --- | --- | --- |
| M36 | The Pharaoh: Sheltem's plan nearly tore Xeen apart. To make it whole: wake the four machines at the corners of the bright face, wake the four elemental sleepers, and bring the Scepter and the Cube together on the cloud above Darkstone Tower | Great Pyramid | M33, M35 | Finale journal |
| M37 | The four **Reflectors**, Ancient machines on the world rim at the corners of Cloudside (X6 north-west, X7 north-east, X5 south-west, X1 south-east), each guarded. Requiring them at the shrine is ours: the source's shrine checks only the Scepter, the Cube and the four sleeper awards | X1, X5, X6, X7 | M36 | 4 reflector qbits |
| M38 | The **elemental sleepers**: each plane is reached by stepping off a Skyroad corner after naming the element; each has a test and a sleeper who wakes only for the Chosen Ones | P1–P4 | M30, M37 | 4 sleeper awards |
| M39 | Free **Prince Roland** from stasis in the depths of Castle Alamar (opened by the Cube) | Alamar Depths (FD-01, M) | M33 | Amulet of the Southern Sphinx; Roland: he and Kalindra will marry on the cloud |
| M40 | The Southern Sphinx: Picard the Aged trades the **Chime of Opening** for a Widget (from Halon's lava-rock quest, Q-C14) | Southern Sphinx (FD-02, S), X6 | M39 | Chime |
| M41 | Darkstone Tower: onyx golems and a plaque grid; the Chime breaks the seal on its roof | Darkstone Tower (FD-03, M), X5 | Chime | P5 |
| M42 | **Clouds of the Ancients**: the walk past the Rest Stop signs (the Pharaoh: "It's a long road ahead so rest where you can. But don't forget to recast your spells."); the Pharaoh's shrine takes the Scepter and the Cube; the four sleepers answer; the wedding of Roland and Kalindra; Xeen is one world | P5 | M35, M38, M33 | **Ending** (completion certificate) |

## 2. Side quests

Selected from the source's 60-odd side quests: the ones with a place, a character and a reason, 54 in total plus two
optional finale quests (calibration 20–30 per world; this is two worlds' worth, and many double as promotions). Rewards are MM6–MM8 sized; "item Tn" means a random item of that
treasure level. "Level" is the party level the quest is set for (MAPS §0).

### 2.1 Cloudside

| ID | Quest | Giver (map) | Objective | Reward | Level |
| --- | --- | --- | --- | --- | --: |
| Q-C1 | The Seasons Relay | Summer, Autumn, Winter, Spring druids (X6, X4, X5, X1) | Carry the Last Flower, Leaf, Snowflake and Raindrop around the four groves | Removes magical aging | 15–30 |
| Q-C2 | Barok's Pendant | Barok the Sorcerer (X2) | Take the pendant back from the sorceresses who drove him out of Rivercity | T1-B promotion; the town fountain turns healing | 12 |
| Q-C3 | The Tiara | Princess Roxanne (Castle Burlock) | The Rivercity robber boss holds her tiara in the den under the bridge | T1-E promotion; item T3 | 14 |
| Q-C4 | The Ninja Pagoda | Kai Wu the monk (X5) | Drive the ninja clan out of their pagoda (or side with them, see L/D) | T1-D promotion | 25 |
| Q-C5 | The Snakes of Asp | Adam and Eve (Asp, X4) | Solve the colour pedestals round the well; destroy the transformer under the town | **Asp liberated**; Crystals of Piezoelectricity | 16 |
| Q-C6 | Ghosts of Winterkill | Mayor Randon (X5) | Ring the gongs, clear three waves of ghosts, report after each | **Winterkill liberated** | 26 |
| Q-C7 | The Count of Nightshadow | the town's signs (X3) | Set all three sundials to nine (a sign says "The Count wakes at nine and sleeps at nine."); open the coffin at night (time-of-day gate, PRODUCTION E12); open the coffin at night; kill Count Draco | **Nightshadow liberated**; Nosferatu promotion (racial) | 24 |
| Q-C8 | The Scroll of Insight | Arie the apprentice (X6) | The wizard cult of Castle Basenji killed her master. Recover the scroll (password "There wolf", written on her master's note that Arie gives) | Jewelled Amulet of the Northern Sphinx | 26 |
| Q-C9 | The Sphinx | — (X6) | The name riddle (GOLUX; Arie or a Basenji prisoner says "Its name is Golux"); the hieroglyph dungeon for wrong answers; the thrones | Titles = small permanent bonuses (+5 stat, once per character); spell scrolls | 28 |
| Q-C10 | Scarab of Imaging | Carlawna the Cleric (X4) | Gargoyles stole it to their range | +item T3; a Cleric teacher; T1-C promotion | 18 |
| Q-C11 | Crystals of Piezoelectricity | Falagar the Wizard (X4) | Bring the crystals from Asp | Lore: the scarab and crystals power a reptile-making machine (link to Asp); item T3 | 18 |
| Q-C12 | Mirabeth's Elixir | Mirabeth, a mermaid cursed with legs (X3) | Gives the Yak Stone; fetch the Elixir of Restoration from the Temple of Yak (XD-06, X2) | +5 Personality; she returns to the sea (a boat stop) | 18 |
| Q-C13 | Lake Beasts | Medin the Fisherman (X2) | Kill the three water dragons of Lake Darzog | item T4; boat route to the island | 24 |
| Q-C14 | Lava for the Water Clock | Halon the Efficient (X5) | The Ever-Hot Lava Rock from Mount Firestone | **Widget** (needed in M40) | 35 |
| Q-C15 | Troll Problem | Thickbark the Civilized, a tree (X5) | Burn the troll lair | Leafpoint on Darkside will talk to you ("Civilized One") | 25 |
| Q-C16 | Cyclops Outpost | Glom the Gnome King (X5) | Burn the cyclops outpost in the Land of Giants corner | item T4 | 28 |
| Q-C17 | Wand of Faery Magic | Danulf the Faery King (X2) | Crazed killer sprites hold it in the south woods | Patriarch promotion (racial) | 18 |
| Q-C18 | Holy Book of Elvenkind | Tito the Elf Priest (X2) | Lost in the Troll Forest | Spirit teacher | 25 |
| Q-C19 | Ligono's Skull | Ligono, a spirit trapped in the surf (X2) | Find his skull at the world's edge | Ligono waits in Olympus later with a warning | 14 |
| Q-C20 | The Bone Whistle | Orothin the Hermit (X1) | Lost in Pitchfork Creek | Two island statues teach Cure Poison / Cure Disease | 5 |
| Q-C21 | Phirna Root | Myra the Herbalist (X1) | Dig roots in Toad Meadow (repeatable) | Cure Poison potions | 3 |
| Q-C22 | Rescue Celia | Derek the Ranger (X1) | His bride is tied up in a hut in the zombie wood | Celia and Derek reappear on Darkside with a sword | 6 |
| Q-C23 | The Ogre Boulders | Captain Nystor (X2) | Destroy the ogre lair blocking the river | Boat route upriver | 12 |
| Q-C24 | Joe's Second Business | (after M2) Joe reappears on Darkside selling fake maps, under his Vertigo slogan so players recognise him | Trade the fake map for a real one (it also frees Jasper, Q-D2) | Slibo's cache on D4, or Slibo buys the map | 19 |
| Q-C25 | The Dragon Tax | the urn in the Dragon Cave (X7) | Pay the tax or be thrown out; read the five Dragon Lore volumes | Titles and Dragon skills; GreatWyrm promotion (racial) | 50 |
| Q-C26 | Shangri-La | the demon and devil skulls (Volcano Cave) | Smash both skulls to open the hidden valley | Shangri-La; grandmaster teachers | 40 |

### 2.2 Darkside

| ID | Quest | Giver (map) | Objective | Reward | Level |
| --- | --- | --- | --- | --- | --: |
| Q-D1 | The Gremlin Court | Mayor Snarfblad (Castleview) | Stop Gettlewaithe's sabotage: three rounds of court dialogue, or a fight | 3 Energy Disks; Castleview pass | 19 |
| Q-D2 | Jasper in Jail | Jethro the mapmaker (Castleview) | His brother was framed by Joe the con man; break him out | Real treasure map (→ Slibo, D4) | 19 |
| Q-D3 | The Drawkcab Way | four palindrome monks (Castleview), Brother Reger (D1) | Take the lessons in order; say the word | Master promotion (Light), once M20 has started (D-12.2) | 32 |
| Q-D4 | Public Storage | Dyson the puzzlemaster (Castleview) | Close the numbered and lettered chests in the right order | items T3 | 20 |
| Q-D5 | Rooka | Valio the Simple (Castleview Sewer) | Kill the queen rat | Valio's chest | 19 |
| Q-D6 | The Heretics of Mok | Dreyfus, high priest (D1) | Heretics hold the Western Tower; the key lies at the top, so climb in from the roof by the Dark Grove rope | 2 Disks; Hero/PriestLight promotion (Light) | 30 |
| Q-D7 | The Gemsmiths | Linus, Simon, Toby, Hector (D1) | Five rocks of their gem plus gems → gem-material weapon or armour (repeatable) | Linus's Ruby Broadsword (12540), Simon's Emerald Leather (12541), Toby's Sapphire Staff (12542), Hector's Diamond Plate (12543): one per five rocks of the gem and 2/4/6/10 gems (`q-d7.yml`, items.yml `crafted`) | 20–45 |
| Q-D8 | Vespar's Staff | Vespar the Wizard (D1) | Find the emerald handle in the east | **Pass to Sandcaster** | 21 |
| Q-D9 | Nibbler's Melons | Nibbler the monkeydog (D2) | Feed him Monga melons | Key to the Temple of Bark | 22 |
| Q-D10 | Princess Sheewana | Sharla of the Sprites (D2) | Rescue her from the orcs of the Temple of Bark (polite, mercenary or robbery route) | 2 Disks | 23 |
| Q-D11 | Graalg's Ogres | Graalg (D2) / Kramer the caravan owner (D1) | Make peace for 2 disks, **or** burn both ogre forts for Kramer's bounty | 2 Disks / BountyHunter promotion (Dark) | 24 |
| Q-D12 | Yog's Barbarians | Yog (D1) | Talk or fight | Friends of the giants (easier Q-D16) | 20 |
| Q-D13 | Hobstadt's Trolls | Hobstadt (Troll Holes) | Give gold, sacrifice, or fight; the Thieves' Guild hunts its stolen gold | WarTroll promotion (racial) | 24 |
| Q-D14 | The Wizard Quarter | Astra the Good Sorceress (Sandcaster) | Defeat Xenoc and Morgana who seized the guilds | **Wizard quarter opens**; Spy promotion (Light) | 39 (Act IV, D-16) |
| Q-D15 | Caleb's Magnifying Glass | Caleb the Inventor (Crossroads) | Destroy the gargoyle lair | item T4 | 30 |
| Q-D16 | Gurodel's Giants | Gurodel (D5) | Diplomacy or the bloody throne | 2 Disks | about 45 (Act V, D-16) |
| Q-D17 | The Chalice of Protection | Bosco the Dwarf King (D5) | Fetch it from the Northern Tower (answer the voice; the Voweless Knights' answers are a compilation sold in Castleview's library) | 2 Disks; BlackKnight/Villain promotion if you side with the Voweless Knights instead (Dark) | about 50 (Act V, D-16) |
| Q-D18 | The Jewel of Ages | Thaddeus, fountain keeper (D3) | From the Eastern Tower | Fountain of Youth; ArchMage promotion (Light) via Ellinger's sealed letter on the top floor | 32 |
| Q-D19 | The Southern Tower | Thaddeus (key) | The thieves' ledger: who bought Luna's statuettes; the Master Thief | 2 Disks; Assassin/Sniper promotion (Dark) | 30 |
| Q-D20 | Luna's Statuettes | Luna the Druid (D1) | Golden Pegasus, Dragon and Griffin statuettes from three dungeons | +item T5 each (rescaled from +5 levels) | 34 |
| Q-D21 | Ector's Ring | Ector the Woodsman (D4) | In a woodpile on Magic Mountain | Obsidian battle-axe (item) | 30 |
| Q-D22 | The Coven | Naomi the prisoner (Lakeside) | Free the five prisoners; break the coven (the guild's word WITCH: Naomi says it, or membership is sold) | **Lakeside liberated**; Necropolis pass from the head witch's chest; Warlock promotion if you join the coven instead (Dark) | 32 |
| Q-D23 | Sandro's Heart | Sandro the Lich (Necropolis) | Fight him, then take his heart from the sewer so he cannot rise | Lich/PriestDark promotion (Dark); key to the Dungeon of Death below the Dragon Tower (FD-04, finale optional) | 45 |
| Q-D24 | The Enchanted Boulders | seven boulders (D5) | Their letter clues spell a word (PALADIN) | A dead paladin's armour (artifact-grade) | about 43 (Act V, D-16) |
| Q-D25 | The Minotaur's Labyrinth | (Dungeon of Lost Souls, deepest floor) | Survive the maze | MinotaurLord promotion (racial) | 32 |
| Q-D26 | The Megadragon | (D7, optional superboss) | Guards a shortcut onto Castle Alamar's roof (into FD-01's rubble shaft after M33, D-61, D-69) | Hoard: artifact | 60 |
| Q-D27 | Genie Lamps | ~10 lamps on D-maps and D7 | Wish choices; greed is punished | small stat bonuses, gold, or a curse | any |
| Q-D28 | Cyrano's Tribble | Cyrano Jones (Olympus sewer) | A password from note fragments (TR/IB/BL/ES), the whole word in Cyrano's patter to a tribble's owner (aaze0038:15); the Tribble sells for 25,000 (D-65) | A useless and expensive pet (joke item) | 45 |

### 2.3 Optional finale content

| ID | Quest | Where | Notes |
| --- | --- | --- | --- |
| Q-F1 | Alister and the Dragon Egg | Dragon Tower (FD-04, X7) | Alister is a fraud (a dead adventurer's note says so); the Eye of the Dragon's riddle (INFINITY, given on a second dead adventurer's note) on Dragon Clouds pays an artifact; the Key to the Dragon Tower lies in FD-01's key vault on M39's path (D-57 Q23, D-69) |
| Q-F2 | The Dungeon of Death | FD-04's lower half (X7; moved from X1 on 2026-11-14), key from Sandro | Sandro's old home: the walk-in crossword, the four Shrines of Evil, the **Lord Xeen Machine** (destroy it) |

## 3. Promotions

The composite model of MM9 (`assets_dev/worlds/mm9/dialogue/promotions.yml`, `MM9.Promotions`): each promotion quest
promotes every eligible member of the class lines it serves. Tier 1 is played on Cloudside (levels 7–30), tier 2 on
Darkside (levels about 23–50; D-12, 2026-11-20) with MM7's **Light or Dark** choice: a member promoted by a Light quest cannot take the Dark one
and vice versa, and the party may promote different members on different paths. Racial classes have one promotion
each.

### 3.1 Tier 1 (Cloudside)

| ID | Quest | Promotes |
| --- | --- | --- |
| T1-A | The Crusade (M4, Valia and the Witch Tower) | Knight → Cavalier, Paladin → Crusader, Ranger → Hunter |
| T1-B | Barok's Pendant (Q-C2) | Sorcerer → Wizard, Archer → Warrior Mage |
| T1-C | The Scarab of Imaging (Q-C10, Carlawna; D-1, 2026-11-20) | Druid → Great Druid, Cleric → Priest |
| T1-D | The Ninja Pagoda (Q-C4) | Monk → Initiate |
| T1-E | The Tiara (Q-C3) | Thief → Rogue |

T1-A is also a main-quest step; that is deliberate (the source's "Crusader" title).

### 3.2 Tier 2 (Darkside, Light or Dark)

| Class line (tier 1 →) | Light | Dark |
| --- | --- | --- |
| Cavalier | Champion: **Dimitri's Test** (clear Kalindra's dungeon of the imprisoned liches, after stage 3) | Black Knight: **the Voweless Knights** (Q-D17, side with the knights in the Northern Tower) |
| Crusader | Hero: **the Heretics of Mok** (Q-D6) | Villain: **the Voweless Knights** (Q-D17) |
| Hunter | Ranger Lord: **Sharla's Sprites** (Q-D10, the polite route) | Bounty Hunter: **Kramer's Bounty** (Q-D11, burn the ogre forts) |
| Warrior Mage | Master Archer: **Luna's Statuettes** (Q-D20) | Sniper: **the Southern Tower** (Q-D19) |
| Priest | Priest of Light: **the Heretics of Mok** (Q-D6) | Priest of Dark: **Sandro's Heart** (Q-D23, freeing Sandro instead of destroying him) |
| Great Druid | Arch Druid: **Leafpoint's Grove** (Leafpoint, D4; needs Q-C15's "Civilized One") | Warlock: **the Coven** (Q-D22, join it) |
| Initiate | Master: **the Drawkcab Way** (Q-D3) | Ninja: return to **the Ninja Pagoda** (Q-C4, side with the clan) |
| Rogue | Spy: **the Wizard Quarter** (Q-D14) | Assassin: **the Southern Tower** (Q-D19) |
| Wizard | Archmage: **the Jewel of Ages** (Q-D18) | Lich: **Sandro's Heart** (Q-D23) |

Racial promotions: Minotaur → Minotaur Lord (Q-D25), Troll → War Troll (Q-D13), Vampire → Nosferatu (Q-C7), Dragon →
Great Wyrm (Q-C25), Dark Elf → Patriarch (Q-C17). The MMerge Necromancer line (if the ruleset offers it) takes its
promotion from Sandro (Q-D23).

That is **5 tier-1 quests, 15 tier-2 quests (several shared) and 5 racial quests, about 20 distinct quests**, every one
of them an existing Xeen side quest with a promotion attached, so no promotion-only content has to be invented.

A promotion pays its act's share, inside the act's budget. The first (T1-A) pays about one level at its quest's level.
Later promotions that are their own quest pay like a substantial side quest, about a quarter to a half of a level at
their quest's level (Act IV: 8–12k per member). A promotion added to content that is already paid (a route choice, a
talk, a fight inside a story dungeon) pays about a tenth of a level (about 3k in Act IV). The class change is the
reward. MM7's 80k/40k was paid per class, which does not carry over to a model where every promotion quest pays the
whole party. (D-16, 2026-11-20.)

## 4. Systems and mini-games

### 4.1 Newcastle (Cloudside home)

| Stage | Cost | Unlocks | Visual |
| --- | --- | --- | --- |
| 0 | 12,000 gold (deed) | Site: rubble, Ebenezer's tent, Wood Golems in the foundation | Ruin BModels |
| 1 Walls | 5 Megacredits | Stone of a Thousand Terrors; Ebenezer pays a small yearly tax income | Walls appear |
| 2 Keep | 5 Megacredits | Golem Stone; smith and training in the keep | Keep appears |
| 3 Dungeon | 5 Megacredits + Excavation Permit | Temple and bank; "your well" (+AC buff); the sword vault | Banners, lights |

Engine: ODM BModel groups shown and hidden by qbit (PRODUCTION §2.3). The keep is a small BLV; its service houses open
by qbit.

### 4.2 Castle Kalindra (Darkside home)

Four stages of 5 Energy Disks (the source has four stages, not the 5/5/10 the old study claimed). Ellinger takes the
disks in his study in his tower (DD-02), five at a time, as in the source; a lift between his tower's ground floor and
his study runs both ways after the first climb (decision D-9.2, 2026-11-20). The exterior fades in
wing by wing (ODM BModel groups by qbit, translucent "out of phase" state for the missing wings). Interior: one BLV,
whose out-of-phase wings are sealed by shimmering translucent walls (`translucent_faces`) until their stage.

| Disks | Opens |
| --: | --- |
| 5 | Gate, throne room, Gem (Perception) and Errol (Armsmaster) teachers, thievery safes |
| 10 | Second floor: Dimitri and Megan, the disk safe (4 disks, Dimitri's combination; A3 2026-11-21), the telescope (Identify Item teacher) |
| 15 | Dungeon: Guido the convict, Scraps the pet dragon, imprisoned liches (Champion promotion) |
| 20 | Third floor: the Queen's bedroom and crown safe, temple, bank, training, smith, stables; wakes the Darkside mirrors |

25 disks exist; 20 are needed; the faction choices decide which ones the party ends up with.

### 4.3 Other recurring systems

| System | Design | Count |
| --- | --- | --- |
| **Obelisks** | One per surface map (calibration: exactly one). Each face's seven or six obelisks spell one line of the rhyming walkthrough of its villain; the full line points to a buried hoard | 13 |
| **Rhyming statues** | On the sky maps, readable after the Book of Languages: the in-world walkthrough of the source, in verse | 3 per sky map |
| **Fountains, wells, shrines** | 2–6 per map. One permanent +2 stat fountain per map (MapVar charges, MM6 style); temporary stat and resistance wells; the source's named wells keep their names ("Waters of Great Power" → +25 HP temporary). Each face has 6 elemental shrines (+resistance, permanent once) | ~45 |
| **Burn the camp** | Destroyable camps of orcs, barbarians, ogres, cyclops, evil rangers, harpy and roc nests: an outdoor destructible + a small reward. The source's cheapest repeatable outdoor objective | 2–4 per wilderness map |
| **Faction diplomacy** | Gremlins, sprites, giants, ogres, trolls, barbarians, Voweless Knights, the coven: talk or fight. Peace flips the faction friendly in `relations.yml` | 8 factions |
| **Talking skulls** | Sell stat points or spells for **gems** (gems become a second currency, as in the source; gem drops added to the loot tables) | Cave of Illusion, Witch Tower |
| **Slick's carnival** | Four stat games on X9 (stat checks with escalating thresholds, small fee) | 1 |
| **Warzone arena** | MM6–MM8 arena with four tiers (Page → Lord) | 1 |
| **Gemsmiths** | Rocks from the Gemstone Mines + gems → gem-material gear; the God of Minerals refills the rocks for a large fee | 4 smiths |
| **Mirrors** | Transport houses, free, destinations by discovery (WORLD_DESIGN §3.3) | 13 |
| **Seer** | Psychic Sally (Shangri-La) and Madame Oorla (Castleview) give the next main-quest hint, MM6/MM8-seer style | 2 |
| **Arcomage** | Not used (not Xeen) unless the user wants it in taverns | 0 |
