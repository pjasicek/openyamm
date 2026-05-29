# MMerge Faithful Baseline Quest Completion Inventory

Purpose: this is the playthrough checklist for Milestone 1. It inventories the player-facing MM8, MM7, and MM6
quests from `assets_dev/engine/data_tables/english/quests.txt`, cross-checked against `npc.txt` notes where obvious.

Use it as a verification document, not as a final walkthrough. If a giver/location is marked `verify`, the quest table
or NPC notes were ambiguous enough that the playthrough should confirm the exact in-game source.

Status legend:

- `untested`: not checked in OpenYAMM yet.
- `blocked`: cannot complete because of an engine/event/content issue.
- `works`: completed in OpenYAMM from normal play.
- `skip`: intentionally not part of the faithful baseline.

## Baseline Acceptance Gates

- [ ] MM8 main story completable.
- [ ] MM7 main story completable on Light path.
- [ ] MM7 main story completable on Dark path.
- [ ] MM6 main story completable.
- [ ] Every MM8 promotion completable.
- [ ] Every MM7 promotion completable, including Light/Dark second promotions.
- [ ] Every MM6 promotion completable.
- [ ] Every listed quest-critical dungeon/event interaction works with mouse and keyboard.
- [ ] Quest state survives save/load and continent travel.

## MM8 Main And Progression

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 85 | Find Dadeross. | Start of game, Dagger Wound caravan. | Talk to Dadeross in Blood Drop / Lizardman throne room. | Leads to QBit 3. |
| [ ] | untested | 3 | Deliver Dadeross' letter to Elgar Fellmoon. | Dadeross, Dagger Wound. | Deliver to Elgar Fellmoon at Merchant House in Ravenshore. | Done QBit 4; lost item QBit 221. |
| [ ] | untested | 5 | Kill Regnan Pirate leader at Dagger Wound. | Ravenshore alliance council / Dadeross chain. | Kill pirate leader in Dagger Wound Pirate Outpost. | Done QBit 6; pirate timer/war state. |
| [ ] | untested | 9 | Deliver Fellmoon's blackmail letter to Arion Hunter and report back. | Elgar Fellmoon, Ravenshore Merchant House. | Deliver to Arion Hunter, then return to Fellmoon. | Delivered QBit 10, reward QBit 24, follow-up QBit 284, lost item QBit 222. |
| [ ] | untested | 284 | Report blackmail success to Fellmoon. | Continuation of QBit 9. | Return to Fellmoon in Ravenshore. | Verify this journal bit clears correctly. |
| [ ] | untested | 11 | Report to Bastian Loudrin in Alvar. | Elgar Fellmoon, Ravenshore. | Talk to Bastian Loudrin, Alvar Merchant Guild. | Done QBit 12. |
| [ ] | untested | 13 | Form an alliance among the major factions of Jadame. | Bastian Loudrin, Alvar Merchant Guild. | Form three required alliances and return to council flow. | Done QBit 34; depends on QBits 14-18 and alliance done bits 19-23. |
| [ ] | untested | 14 | Ally with Necromancers' Guild. | Bastian Loudrin; Sandro in Shadowspire. | Complete Sandro's Nightshade Brazier quest or alternate alliance condition. | Done QBit 19; see QBit 28/29. |
| [ ] | untested | 15 | Ally with Temple of the Sun. | Bastian Loudrin; Oskar Tyre in Murmurwoods. | Complete Skeleton Transformer quest or alternate alliance condition. | Done QBit 20; see QBit 26/27. |
| [ ] | untested | 16 | Ally with Dragon Hunters. | Bastian Loudrin; Charles Quixote in Garrote Gorge. | Return Dragon Egg to Charles Quixote. | Done QBit 21; mutually opposed to dragon alliance. |
| [ ] | untested | 17 | Ally with Dragons. | Bastian Loudrin; Deftclaw Redreaver in Garrote Gorge. | Return Dragon Egg to Deftclaw Redreaver. | Done QBit 22; mutually opposed to hunter alliance. |
| [ ] | untested | 18 | Ally with Minotaurs. | Bastian Loudrin; Minotaur quest chain. | Rescue minotaurs in Balthazar Lair / Minotaur Lair flow. | Done QBit 23; see QBit 30. |
| [ ] | untested | 25 | Find a witness to the lake of fire's formation. | Bastian Loudrin, Alvar. | Bring Overdune Snapfinger to Merchant Guild in Alvar. | Ironsand visit QBit 60; done QBit 59. |
| [ ] | untested | 91 | Consult Xanthor about the Ravenshore crystal. | Elgar Fellmoon / council flow. | Talk to Xanthor. | Done QBit 92. |
| [ ] | untested | 41 | Bring Heart of Water to Xanthor. | Xanthor. | Recover Plane of Water heart and return with all four hearts. | Completion grouped at QBit 45; got-heart QBit 241; lost item QBit 206. |
| [ ] | untested | 42 | Bring Heart of Air to Xanthor. | Xanthor. | Recover Plane of Air heart and return with all four hearts. | Completion grouped at QBit 45; got-heart QBit 243; lost item QBit 207. |
| [ ] | untested | 43 | Bring Heart of Earth to Xanthor. | Xanthor. | Recover Plane of Earth heart and return with all four hearts. | Completion grouped at QBit 45; got-heart QBit 244; lost item QBit 208. |
| [ ] | untested | 44 | Bring Heart of Fire to Xanthor. | Xanthor. | Recover Plane of Fire heart and return with all four hearts. | Completion grouped at QBit 45; got-heart QBit 242; lost item QBit 205. |
| [ ] | untested | 46 | Find the cause of the cataclysm through the Crystal Gateway. | Xanthor. | Reach Escaton through Crystal Gateway. | Done QBit 47; Escaton talk/riddle QBits 94-98, 235. |
| [ ] | untested | 48 | Rescue Pyrannaste, Lord of Fire. | Escaton. | Free Pyrannaste in Lord of Fire prison. | Done QBit 49. |
| [ ] | untested | 50 | Rescue Gralkor the Cruel, Lord of Earth. | Escaton. | Free Gralkor in Lord of Earth prison. | Done QBit 51. |
| [ ] | untested | 52 | Rescue Acwalander, Lord of Water. | Escaton. | Free Acwalander in Lord of Water prison. | Done QBit 53. |
| [ ] | untested | 54 | Rescue Shalwend, Lord of Air. | Escaton. | Free Shalwend in Lord of Air prison. | Done QBit 55; all lords QBit 56. |
| [ ] | untested | 36 | Sink the Regnan Fleet. | Ravenshore council chamber after alliances. | Complete Regna fleet sequence and return to council. | Fleet sunk QBit 37; quest done QBit 38; submarine QBit 223. |

## MM8 Promotions

| Check | Status | QBit | Promotion / Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 39 | Dark Elf to Patriarch. Find Cauri Blackthorne. | Dantillion in Murmurwoods / Dark Elf promotion chain. | Find and rescue Cauri, return with her location/status. | Found QBit 40; restored QBit 84; award QBit 1537. |
| [ ] | untested | 68 | Troll to War Troll. Find Ancient Troll Homeland. | Volog Sandwind, Ironsand Desert. | Discover Ancient Troll Homeland and report back. | Found QBit 69; award QBits 1538/1539. |
| [ ] | untested | 70 | Knight to Champion. Find Blazen Stormlance and Ebonest. | Leane Stormlance, Garrote Gorge. | Recover Ebonest, continue cure chain, deliver Ebonest to Charles Quixote. | Found QBit 71; cure QBits 72/73/134; awards QBits 1540-1542. |
| [ ] | untested | 72 | Find cure for Blazen Stormlance. | Continuation of Knight promotion. | Ask Dervish Chevron in Ravenshore and apply cure. | Cure received QBit 73; Gem of Restoration lost QBit 217. |
| [ ] | untested | 74 | Dragon to Great Wyrm. Kill Dragon Slayers. | Deftclaw Redreaver / Dragon Cave. | Kill Dragon Slayers and return Sword of Whistlebone. | Done QBit 75; lost sword QBit 200; award QBits 1543/1544. |
| [ ] | untested | 76 | Minotaur to Minotaur Lord. Recover Axe of Balthazar. | Tessalar, Minotaur Lair. | Get Axe from Dark Dwarf Mines, authenticate with Dadeross, return to Tessalar. | Found QBit 77; lost axe QBit 201; award QBit 1545. |
| [ ] | untested | 78 | Cleric to Cleric of the Sun. Recover Prophecies of the Sun. | Stephen / Temple of the Sun. | Find Prophecies in Abandoned Temple and return them. | Found QBit 79, delivered QBit 88, lost item QBit 218; award QBit 1546. |
| [ ] | untested | 80 | Vampire to Nosferatu. Find Sarcophagus and Remains of Korbu. | Lathean, Shadowspire. | Recover Sarcophagus and Korbu's Remains and return. | Sarcophagus QBit 81; lost items QBits 211/219; award QBit 1547. |
| [ ] | untested | 82 | Necromancer to Lich. Find Lost Book of Khel. | Vetrinus Taleshire, Shadowspire. | Recover Lost Book of Khel and complete lich promotion flow. | Found QBit 83; lost book QBit 210; award QBit 1548. |

## MM8 Side Quests

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 7 | Bring Brekish Onefang's portal crystal to Fredrick Talimere. | Brekish Onefang, Blood Drop. | Talk to Fredrick Talimere with crystal. | Done QBit 8; lost crystals QBits 212/213; teleporters QBits 1/2/227. |
| [ ] | untested | 26 | Destroy the Skeleton Transformer. | Oskar Tyre, Temple of the Sun. | Destroy transformer in Necromancers' Guild and return to Oskar. | Destroyed QBit 27. |
| [ ] | untested | 28 | Bring Nightshade Brazier to Sandro. | Sandro, Shadowspire Necromancers' Guild. | Steal Brazier from Temple of the Sun and return. | Stolen QBit 29; lost item QBit 203. |
| [ ] | untested | 30 | Rescue trapped minotaurs. | Thanys / Minotaur clue NPC, Ravage Roaming. | Reach trapped minotaur leader in Minotaur Lair. | Alliance dependency. |
| [ ] | untested | 31 | Recover Dragon Egg for Charles Quixote. | Charles Quixote, Garrote Gorge. | Recover Dragon Egg from Zog's fortress and return to Quixote. | Done QBit 32; lost egg QBit 204. |
| [ ] | untested | 33 | Recover Dragon Egg for Deftclaw Redreaver. | Deftclaw Redreaver, Dragon Cave. | Recover Dragon Egg from Zog's fortress and return to Deftclaw. | Done QBit 35; lost egg QBit 204. |
| [ ] | untested | 61 | Put Vilebite's ashes in Dust village tomb. | Overdune Snapfinger. | Place ashes in troll tomb and return to Overdune. | Placed QBit 62; done QBit 63; lost ashes QBit 202. |
| [ ] | untested | 64 | Rescue the wererats. | Arion Hunter / Smuggler's Cove flow. | Rescue/resolve wererat prisoners. | Done QBit 65; verify exact giver and dungeon. |
| [ ] | untested | 66 | Kill ogres in Ogre Fort. | Alvar ogre bounty chain. | Kill required ogres in Ogre Fort. | Done QBit 67; related Alvar ogre side quest QBit 129/130. |
| [ ] | untested | 101 | Deliver Cure Disease scrolls to six huts. | Aislen, Dagger Wound. | Deliver to six outer huts and return. | Hut QBits 102-107; done QBit 108. |
| [ ] | untested | 109 | Bring Anointed Potion to Languid. | Languid, Dagger Wound. | Return Anointed Potion. | Done QBit 110; hint Wilburt; lost item QBit 245. |
| [ ] | untested | 111 | Bring Idol of the Snake to Hiss. | Hiss, Dagger Wound. | Recover Idol from Abandoned Temple and return. | Found QBit 112; award QBit 1549. |
| [ ] | untested | 113 | Bring Pure Speed ingredients to Thistle. | Thistle, Dagger Wound. | Return potion ingredients. | Done QBit 114. |
| [ ] | untested | 115 | Bring Pure Luck ingredients to Rihansi. | Rihansi, Alvar. | Return potion ingredients. | Done QBit 116. |
| [ ] | untested | 117 | Deliver false report to Dread Pirate Stanley. | Arion Hunter / Ravenshore smuggler chain. | Deliver report at Pirate's Rest Tavern on Regna. | Done QBit 118; lost item QBit 282; award QBit 1554. |
| [ ] | untested | 119 | Rescue Arion Hunter's daughter. | Arion Hunter, Smuggler's Cove. | Rescue Irabelle Hunter from Ogre Fortress in Alvar. | Done QBit 120; award QBit 1551. |
| [ ] | untested | 121 | Bring Pure Endurance ingredients to Talion. | Talion, Ironsand Desert. | Return potion ingredients. | Done QBit 122. |
| [ ] | untested | 123 | Bring Pure Intellect ingredients to Kelvin. | Kelvin, Shadowspire. | Return potion ingredients. | Done QBit 124. |
| [ ] | untested | 125 | Bring Pure Personality ingredients to Castigeir. | Castigeir, Murmurwoods. | Return potion ingredients. | Done QBit 126. |
| [ ] | untested | 127 | Recover Eclipse shield. | Lathius, Ravenshore. | Return Eclipse. | Done QBit 128; lost item QBit 283; award QBit 1550. |
| [ ] | untested | 129 | Kill all ogres in Alvar canyon/Ogre Fortress. | Keldon, Alvar. | Kill required ogres and return. | Done QBit 130; support QBit 131. |
| [ ] | untested | 132 | Bring Pure Accuracy ingredients to Galvinus. | Galvinus, Ravage Roaming. | Return potion ingredients. | Done QBit 133. |
| [ ] | untested | 135 | Find Prophecies of the Snake. | Pascella Tisk, Dagger Wound. | Find in Abandoned Temple and return. | Found QBit 136. |
| [ ] | untested | 137 | Find Isthric the Tongue. | Rohtnax, Blood Drop. | Find Isthric and return to Rohtnax. | Found QBit 138. |
| [ ] | untested | 139 | Kill all Dire Wolves in Ravenshore. | Maddigan, Ravenshore. | Kill required wolves and return. | Done QBit 140; support QBit 141; award QBit 1553. |
| [ ] | untested | 142 | Deliver Fire Resistance potions to Rust houses. | Hobert / Pole, Ironsand Desert. | Deliver to six southern Rust houses and return. | House QBits 143-148; done QBit 149. |
| [ ] | untested | 150 | Find Dragonbane Flower for Dragon Hunters. | Calindril, Garrote Gorge. | Return Dragonbane. | Found QBit 151. |
| [ ] | untested | 152 | Find Dragonbane Flower for Dragons. | Balion Tearwing, Dragon Cave. | Return Dragonbane. | Found QBit 153. |
| [ ] | untested | 154 | Kill all Dragons in Garrote Gorge wilderness. | Avalon, Garrote Gorge. | Kill dragons and return. | Done QBit 155; support QBit 156. |
| [ ] | untested | 157 | Kill all Dragon Hunters in Garrote Gorge wilderness. | Jerin Flame-eye, Dragon Cave. | Kill hunters and return. | Done QBit 158; support QBit 159. |
| [ ] | untested | 160 | Find Legendary Drum of Victory. | Zelim, Garrote Gorge. | Return Drum. | Found QBit 161; lost item QBit 246. |
| [ ] | untested | 162 | Find Iseldir's Puzzle Box. | Benefice, Shadowspire. | Return Puzzle Box. | Found QBit 163; lost item QBit 249. |
| [ ] | untested | 164 | Find Vial of Grave Dirt. | Hallien, Shadowspire. | Return Vial. | Found QBit 165; lost item QBit 248. |
| [ ] | untested | 166 | Find Bone of Doom. | Tantilion, Shadowspire. | Return Bone. | Found QBit 167; lost item QBit 247. |
| [ ] | untested | 172 | Challenge Arcomage Champion in each Jadame tavern. | Tonk Blueswan / Ravenshore. | Win required tavern games and return. | QBit 173 duplicate journal, won QBit 174, treasure QBit 175. |
| [ ] | untested | 236 | Find Dread Pirate Stanley's treasure. | One-Eye / Regna treasure chain. | Find treasure. | Found treasure QBit 168. |
| [ ] | untested | 176 | Find Frelandeau Cheese. | Asael Fromago, Alvar. | Return cheese. | Group done QBit 179. |
| [ ] | untested | 177 | Find Eldenbrie Cheese. | Asael Fromago, Alvar. | Return cheese. | Group done QBit 179. |
| [ ] | untested | 178 | Find Dunduck Cheese. | Asael Fromago, Alvar. | Return cheese. | Group done QBit 179. |

## MM7 Main And Progression

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 513 | Scavenger Hunt: red potion. | Thomas the Judge, Emerald Island. | Return red potion. | Piece done QBit 520. |
| [ ] | untested | 514 | Scavenger Hunt: seashell. | Thomas the Judge, Emerald Island. | Return seashell. | Piece done QBit 521. |
| [ ] | untested | 515 | Scavenger Hunt: longbow. | Thomas the Judge, Emerald Island. | Return longbow. | Piece done QBit 522. |
| [ ] | untested | 516 | Scavenger Hunt: floor tile. | Thomas the Judge, Emerald Island. | Return floor tile. | Piece done QBit 523. |
| [ ] | untested | 517 | Scavenger Hunt: musical instrument. | Thomas the Judge, Emerald Island. | Return instrument. | Piece done QBit 524. |
| [ ] | untested | 518 | Scavenger Hunt: wealthy hat. | Thomas the Judge, Emerald Island. | Return hat. | Piece done QBit 525; full hunt QBit 519; boat QBit 527. |
| [ ] | untested | 528 | Find missing contestants on Emerald Island. | Lord Markham, Emerald Island. | Bring proof to Lord Markham. | Verify interaction with scavenger hunt completion. |
| [ ] | untested | 587 | Clean out Castle Harmondale. | Butler / On the House tavern, Harmondale. | Clear castle and report to Butler. | Player castle start. |
| [ ] | untested | 658 | Talk to Stone City dwarves about repairing Castle Harmondale. | Harmondale castle flow. | Talk to dwarves in Stone City. | Leads to Red Dwarf Mines rescue. |
| [ ] | untested | 588 | Rescue dwarves from Red Dwarf Mines. | Dwarf King Hothfarr IX, Stone City. | Rescue dwarves and return. | Castle repair progression. |
| [ ] | untested | 589 | Retrieve Fort Riverstride plans. | Eldrich Parson, Castle Navan. | Recover plans from Fort Riverstride and return. | Plans chest QBit 604; honest QBit 592; false-plan branch QBit 606/594/603. |
| [ ] | untested | 590 | Rescue Loren Steel. | Queen Catherine, Castle Gryphonheart. | Rescue Loren from Tularean Caves and return. | Loren QBit 605; honest QBit 593; imposter branch QBit 607/595/602. |
| [ ] | untested | 606 | Give false Riverstride plans to Eldrich Parson. | War/spy branch after Riverstride plans. | Deliver false plans to Castle Navan. | Betrayal branch; false plans QBit 594; Queen told QBit 603. |
| [ ] | untested | 607 | Return the Loren imposter to Queen Catherine. | War/spy branch after Loren rescue. | Deliver imposter to Castle Gryphonheart. | Betrayal branch; false Loren QBit 595; Catherine told QBit 602. |
| [ ] | untested | 591 | Retrieve Gryphonheart's Trumpet. | War/arbiter progression. | Give trumpet to humans or elves. | Human QBit 596; elf QBit 597; arbiter QBit 659. |
| [ ] | untested | 665 | Choose a new Arbiter. | Harmondale / council after Judge Grey. | Pick Judge Fairweather or Judge Sleen. | Light/Dark path opens after later choice. |
| [ ] | untested | 663 | Enter The Pit and talk to Archibald. | Dark path entry. | Enter via Hall of the Pit and speak to Archibald. | Path QBit 612. |
| [ ] | untested | 664 | Enter Celeste and talk to Gavin Magnus. | Light path entry. | Enter via Bracada grand teleporter and speak to Gavin. | Path QBit 611. |
| [ ] | untested | 616 | Slay Xenofex in Colony Zod. | Resurectra, Celeste. | Kill Xenofex and return. | Done QBit 617; Light final chain. |
| [ ] | untested | 635 | Slay Xenofex in Colony Zod. | Kastore, The Pit. | Kill Xenofex and return. | Dark equivalent. |
| [ ] | untested | 642 | Retrieve Oscillation Overthruster for Resurectra. | Resurectra, Celeste. | Retrieve from Lincoln and return. | Light ending; final part lost QBit 748. |
| [ ] | untested | 643 | Retrieve Oscillation Overthruster for Kastore. | Kastore, The Pit. | Retrieve from Lincoln and return. | Dark ending; final part lost QBit 748. |

## MM7 Promotions

| Check | Status | QBit | Promotion / Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 530 | Thief to Rogue. Steal Markham's vase. | William Lasker, Erathian Sewers. | Steal vase from Lord Markham's estate and return. | Lost vase QBit 724; awards QBits 1560/1561. |
| [ ] | untested | 531 | Rogue to Spy. Move Watchtower 6 weight. | William Lasker, Erathian Sewers. | Move weight from top to bottom of Watchtower 6 and return. | Done QBit 532; support QBits 568/708; awards QBits 1562/1563. |
| [ ] | untested | 533 | Spy to Assassin. Kill Lady Eleanor Carmine. | Seknit Undershadow, Deyja Moors. | Kill Carmine in Celestial Court and return with proof. | Lost dagger QBit 725; awards QBits 1564/1565. |
| [ ] | untested | 534 | Paladin to Crusader. Kill Wromthrax. | Sir Charles Quixote. | Kill Wromthrax in Tatalia cave and report. | Killed QBit 535; awards QBits 1590/1591. |
| [ ] | untested | 536 | Crusader to Hero. Rescue Alice Hargreaves. | Sir Charles Quixote. | Rescue Alice from William's Tower and report. | QBit 537. |
| [ ] | untested | 538 | Crusader to Villain. Capture Alice Hargreaves. | William Setag / Dark paladin path. | Capture Alice from Gryphonheart and return to Deyja tower. | QBit 537; awards QBits 1592-1595 depending path. |
| [ ] | untested | 539 | Monk to Initiate. Find lost meditation spot. | Bartholomew Hume / Stephan Sand branch. | Find spot in Dwarven Barrows. | Awards QBits 1572/1573. |
| [ ] | untested | 540 | Initiate to Master. Kill High Priest of Baa. | Bartholomew Hume, Harmondale. | Kill High Priest in Temple of Baa, Avlee, and return. | Killed QBit 755; awards QBits 1574/1575. |
| [ ] | untested | 541 | Initiate to Ninja. Crack School of Sorcery code. | Stephan Sand, The Pit. | Reveal Tomb of Ashwar Nog'Nogoth, enter it, and return. | Done QBit 569; lost cipher QBit 727; awards QBits 1576/1577. |
| [ ] | untested | 542 | Archer to Warrior Mage. Retrieve Perfect Bow. | Lawrence Mark, Harmondale. | Get Perfect Bow from Titans' Stronghold and return. | Perfect bow QBit 675/753; awards QBits 1584/1585. |
| [ ] | untested | 543 | Warrior Mage path. Sabotage Red Dwarf Mines lift. | Steagal Snick, Avlee. | Sabotage lift and return. | Done QBit 570. |
| [ ] | untested | 544 | Archer to Master Archer/Sniper. Retrieve Perfect Bow. | Steagal Snick, Avlee. | Return Perfect Bow. | Awards QBits 1586-1589. |
| [ ] | untested | 545 | Knight to Champion. Win five arena challenges. | Leda Rowan, Bracada Desert. | Win five arena challenges and return. | Done QBit 571; awards QBits 1568/1569. |
| [ ] | untested | 546 | Knight to Cavalier. Destroy Haunted House undead. | Frederick Org, Erathia. | Clear Haunted House and return. | Done QBits 652/654; awards QBits 1566/1567. |
| [ ] | untested | 547 | Cavalier to Black Knight. Raid Elven Treasury. | Frederick Org, Erathia. | Rob Castle Navan treasury and return. | Done QBit 572; awards QBits 1570/1571. |
| [ ] | untested | 548 | Ranger to Hunter. Calm Tularean trees. | Lysander Sweet, Bracada Desert. | Speak to Oldest Tree and return. | Oldest Tree QBit 552; solved QBit 553; awards QBits 1578/1579. |
| [ ] | untested | 549 | Hunter to Ranger Lord. Solve Faerie Mound entrance. | Faerie King / Ranger path. | Enter Faerie Mound and speak to Faerie King. | Entered QBit 709; awards QBits 1580/1581. |
| [ ] | untested | 550 | Ranger to Bounty Hunter. Collect 10,000 gold in bounties. | Ebednezer Sower, Tularean Forest. | Return after bounty total reaches threshold. | Done QBit 573; awards QBits 1582/1583. |
| [ ] | untested | 554 | Cleric to Priest of Light. Purify Altar of Evil. | Rebecca Devine, Celeste. | Purify Temple of the Moon altar and return. | Done QBit 574; awards QBits 1609/1610. |
| [ ] | untested | 556 | Cleric to Priest of Dark. Deface Altar of Good. | Daedalus Falk, Deyja Moors. | Deface Temple of the Sun altar and return. | Done QBit 575; awards QBits 1611/1612. |
| [ ] | untested | 557 | Sorcerer to Wizard. Build a complete golem. | Thomas Grey, School of Sorcery. | Collect six golem pieces, build golem, return. | Pieces QBits 578-586; awards QBits 1619/1620. |
| [ ] | untested | 559 | Wizard to Archmage. Retrieve Book of Divine Intervention. | Thomas Grey, School of Sorcery. | Get book from Breeding Zone and return. | Got QBit 751; lost QBit 738; awards QBits 1621/1622. |
| [ ] | untested | 560 | Sorcerer to Lich. Retrieve lich jars. | Halfgild Wynac, The Pit. | Get jars from Proving Grounds and return. | Jars QBits 660-662/741/749; awards QBits 1623/1624. |
| [ ] | untested | 561 | Druid to Great Druid. Visit three stonehenges. | Anthony Green, Tularean Forest. | Visit Tatalia, Evenmorn, and Avlee monoliths and return. | Visits QBits 562-565; awards QBits 1613/1614. |
| [ ] | untested | 566 | Great Druid to Arch Druid. Return Dwarf King's bones. | Anthony Green, Tularean Forest. | Retrieve bones and place them in Barrow Downs. | Returned QBit 577; lost QBit 740; awards QBits 1615/1616. |
| [ ] | untested | 567 | Warlock promotion. Retrieve Dragon Egg. | Tor Anwyn, Mount Nighon. | Get Dragon Egg from Land of the Giants cave and return. | Lost QBit 739; awards QBits 1617/1618. |
| [ ] | untested | 613 | Light path task: Walls of Mist. | Gavin Magnus, Celeste. | Complete without killing opponents and return. | Done QBits 614/626. |
| [ ] | untested | 615 | Light path task: retrieve altar pieces. | Resurectra, Celeste. | Retrieve Light/Dark altar pieces and return. | Lost QBits 744/745; done QBit 627. |
| [ ] | untested | 618 | Light path task: investigate Wine Cellar. | Crag Hack, Celeste. | Kill vampire / complete Wine Cellar and return. | Done QBits 619/628. |
| [ ] | untested | 620 | Light path task: retrieve Soul Jars. | Sir Caneghem, Celeste. | Retrieve Soul Jars from Castle Gloaming and return. | Done QBit 629. |
| [ ] | untested | 621 | Light path task: assassinate Tolberti. | Robert the Wise, Celeste. | Kill Tolberti and return Control Cube. | Killed evil MM3 person QBit 631; lost cube QBit 746. |
| [ ] | untested | 634 | Dark path task: retrieve altar pieces. | Kastore, The Pit. | Retrieve Light/Dark altar pieces and return. | Done QBit 623. |
| [ ] | untested | 636 | Dark path task: retrieve Soul Jars. | Maximus, The Pit. | Retrieve Case of Soul Jars from Warlocks in Thunderfist Mountain. | Lost case QBit 743; done QBit 624. |
| [ ] | untested | 637 | Dark path task: destroy Clanker's Lab defenses. | Dark Shade, The Pit. | Destroy magical defenses and return. | Done QBits 638/625. |
| [ ] | untested | 639 | Dark path task: assassinate Robert the Wise. | Tolberti, The Pit. | Kill Robert in Celeste and return. | Killed good MM3 person QBit 630. |
| [ ] | untested | 640 | Dark path task: complete Breeding Zone. | Archibald, The Pit. | Complete Breeding Zone and return. | Done QBit 641. |

## MM7 Side Quests

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 551 | Find Heart of the Forest. | Oldest Tree, Tularean Forest. | Retrieve from Mercenary Guild in Tatalia and return. | Lost item QBit 729. |
| [ ] | untested | 555 | Find lost pirate map. | Daedalus Falk, Deyja Moors. | Return map from Tidewater Caverns. | Lost map QBit 730. |
| [ ] | untested | 667 | Retrieve Lantern of Light. | Tarin Withern, Harmondale. | Get from Barrow Downs and return. | Got QBit 674. |
| [ ] | untested | 668 | Retrieve Haldar's Remains. | Mazim Dusk, Nighon. | Get from The Maze and return. | Verify item-loss bit if any. |
| [ ] | untested | 669 | Retrieve Davrik's Signet Ring. | Davrik Peladium, Harmondale. | Get from Bandit Caves and return. | Got QBit 672. |
| [ ] | untested | 670 | Deliver sealed letter to Lord Markham. | Norbert Thrush, Erathia. | Deliver to Lord Markham in Tatalia. | Leads to QBit 671. |
| [ ] | untested | 671 | Return Parson's Quill to Norbert Thrush. | Follow-up to sealed letter. | Return Quill to Norbert Thrush. | Verify branch after Markham delivery. |
| [ ] | untested | 691 | Take sealed letter to Faerie King. | verify; tied to Faerie King / Johann Kerrid chain. | Deliver to Faerie King in Hall under the Hill. | Leads to QBit 692. |
| [ ] | untested | 692 | Take Faerie Pipes to Johann Kerrid. | Faerie King. | Deliver pipes to Johann Kerrid in Tularean Forest. | Verify reward and completion. |
| [ ] | untested | 693 | Go to Mercenary Guild within two weeks. | Niles Stantley chain. | Reach Mercenary Guild in Tatalia and talk to Niles. | Failure QBit 695. |
| [ ] | untested | 694 | Steal associate's tapestry. | Niles Stantley, Mercenary Guild. | Steal tapestry from associate's castle and return. | Tapestry QBit 711; failure QBit 695. |
| [ ] | untested | 698 | Kill Troglodytes under Stone City. | Spark Burnkindle, Stone City. | Kill required troglodytes and return. | Verify all-monsters condition. |
| [ ] | untested | 699 | Kill Griffins in Erathia and Bracada. | Seth Drakkson, Deyja Moors. | Kill all required griffins and return. | Erathia QBit 700; Bracada QBit 701. |
| [ ] | untested | 706 | Find fate of Darron's brother. | Darron Temper, Harmondale. | Investigate White Cliff Caves and return. | Quest table text says Arcomage cards note in NPC table; verify. |
| [ ] | untested | 707 | Retrieve Seasons' Stole. | Gary Zimm, Bracada Desert. | Retrieve from Hall of the Pit and return. | Verify item-loss bit if any. |
| [ ] | untested | 712 | Retrieve three statuettes and place them on shrines. | Thom Lumbra, Tularean Forest. | Place in Bracada, Tatalia, Avlee, then return. | Placed QBits 713-715. |
| [ ] | untested | 716 | Retrieve three paintings. | Ferdinand Visconti, Tatalia. | Return Roland, Archibald, and Angel paintings. | Painting QBits 776-778. |
| [ ] | untested | 717 | Win Arcomage in all thirteen taverns. | Gina Barnes, Erathia. | Win all tavern games and return. | Won QBit 750; treasure QBit 756. |

## MM6 Main And Progression

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 1105 | Show Sulman's letter to Andover Potbello. | Starting party letter. | Talk to Andover Potbello in New Sorpigal. | Mapped from original QBit 81. |
| [ ] | untested | 1106 | Bring Sulman's letter to Wilbur Humphrey. | Andover Potbello. | Deliver to Regent Wilbur Humphrey at Castle Ironfist. | Opens council/castle path. |
| [ ] | untested | 1110 | Find Lord Kilburn's Shield. | Wilbur Humphrey, Castle Ironfist. | Return shield to Wilbur Humphrey. | Quest item bit QBit 1206; local found QBit 1328. |
| [ ] | untested | 1112 | Rescue a Damsel in Distress. | Wilbur Humphrey, Castle Ironfist. | Rescue Melody Silver and return. | Rescued QBits 1151/1195. |
| [ ] | untested | 1113 | Slay Longfang Witherhide. | Wilbur Humphrey, Castle Ironfist. | Kill dragon near Castle Darkmoor and return. | Verify proof/reward. |
| [ ] | untested | 1114 | Entertain Nicolai. | Wilbur Humphrey / Castle Ironfist. | Take Nicolai to circus. | Follow-up QBit 1119. |
| [ ] | untested | 1119 | Find and return Prince Nicolai. | Castle Ironfist after circus. | Find Nicolai and return him to Castle Ironfist. | Circus map transition critical. |
| [ ] | untested | 1224 | Find cure for Slicker Silvertongue. | Wilbur Humphrey after council refusal. | Investigate Superior Temple of Baa. | Replaced by treason-letter quest QBit 1225. |
| [ ] | untested | 1225 | Bring Silvertongue treason letter to High Council. | Wilbur Humphrey after finding proof. | Deliver letter to High Council in Free Haven. | Exposes traitor QBits 1191/1192. |
| [ ] | untested | 1186 | Restore Memory Crystal Alpha. | Oracle, Free Haven. | Find in Supreme Temple of Baa and restore to module altar. | Inserted QBit 1124; item bit QBit 1215. |
| [ ] | untested | 1187 | Restore Memory Crystal Beta. | Oracle, Free Haven. | Find in Castle Alamos and restore. | Inserted QBit 1125; item bit QBit 1216. |
| [ ] | untested | 1188 | Restore Memory Crystal Delta. | Oracle, Free Haven. | Find in Castle Darkmoor and restore. | Inserted QBit 1126; item bit QBit 1217. |
| [ ] | untested | 1189 | Restore Memory Crystal Epsilon. | Oracle, Free Haven. | Find in Castle Kriegspire and restore. | Inserted QBit 1127; item bit QBit 1218. |
| [ ] | untested | 1190 | Retrieve Control Cube from Tomb of VARN. | Oracle, Free Haven. | Bring Control Cube to Oracle. | Allowed to enter Control Center QBit 1193; item bit QBit 1219. |
| [ ] | untested | 1259 | Obtain Arcane Magic from Archibald. | Oracle / Royal Library flow. | Free/consult Archibald in Castle Ironfist library. | Needed for Control Center / main ending. |

## MM6 Council And Promotion Quests

| Check | Status | QBit | Promotion / Council Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 1122 | Capture the Prince of Thieves. | Lord Anthony Stone, Castle Stone. | Capture Prince in Free Haven sewer and return. | Captured QBit 1194. |
| [ ] | untested | 1129 | Rebuild Temple Stone. | Lord Anthony Stone, Castle Stone. | Hire Stonecutter and Carpenter, repair Temple Stone, return. | Complete QBit 1130. |
| [ ] | untested | 1131 | Return Sacred Chalice. | Lord Anthony Stone, Castle Stone. | Take Chalice from island temple, place in Temple Stone, return. | Placed QBit 1132; item bit QBit 1212. |
| [ ] | untested | 1134 | Retrieve Hourglass of Time. | Lord Albert Newton, Mist. | Find Hourglass and return. | Item bit QBit 1207; dungeon bit QBit 1029. |
| [ ] | untested | 1135 | Drink from the Fountain of Magic. | Lord Albert Newton, Mist. | Drink from required fountain and return. | Verify exact fountain event. |
| [ ] | untested | 1136 | Retrieve Crystal of Terrax. | Lord Albert Newton, Mist. | Recover Crystal and return. | Item bit QBit 1210; glass shard QBit 1026. |
| [ ] | untested | 1137 | Destroy the Devil's Outpost. | Lord Osric Temper, Castle Temper. | Destroy outpost and return. | Item bit QBit 1208. |
| [ ] | untested | 1138 | Get Knight's nomination from Chadwick. | Lord Osric Temper, Castle Temper. | Get nomination from Chadwick Blackpoole in Free Haven inn and return. | Verify topic handoff. |
| [ ] | untested | 1139 | Defeat the Warlord. | Lord Osric Temper, Castle Temper. | Kill Warlord and bring proof. | Verify proof item/award. |
| [ ] | untested | 1140 | Fix prices at all nine stables. | Lady Loretta Fleise, Silver Cove. | Visit all nine stables and return. | Visits QBits 1171-1179; all visited QBit 1141. |
| [ ] | untested | 1142 | Visit Altar of the Sun. | Lady Loretta Fleise, Silver Cove. | Visit stone circle north of Silver Cove on equinox/solstice. | Great Druid promotion. |
| [ ] | untested | 1143 | Visit Altar of the Moon. | Lady Loretta Fleise, Silver Cove. | Visit Temple of the Moon at midnight of full moon. | Arch Druid promotion. |
| [ ] | untested | 1144 | End winter. | Lord Erik von Stromgard, Frozen Highlands. | End winter and return. | Ended QBit 1199; Hermit involved. |
| [ ] | untested | 1145 | Retrieve Dragon Tower key. | Lord Erik von Stromgard, Frozen Highlands. | Get key from Icewind Keep and return. | Item bit QBit 1213. |
| [ ] | untested | 1146 | Reset all Dragon Towers. | Lord Erik von Stromgard, Frozen Highlands. | Reset towers in each town and return. | Tower QBits 1180-1185; all towers QBit 1147. |
| [ ] | untested | 1169 | Unward Hall of the Fire Lord doors. | Lord of Fire, Hall of the Fire Lord. | Unward doors and return. | Unwarded QBit 1170; reward QBit 1401. |

## MM6 Side Quests

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes / Related QBits |
|---|---|---:|---|---|---|---|
| [ ] | untested | 1107 | Find Goblinwatch vault combination. | New Sorpigal Town Hall. | Discover combination and return. | Discovered QBit 1109; used key QBit 1324. |
| [ ] | untested | 1108 | Get Chime of Harmony from Temple of Baa. | New Sorpigal Town Hall. | Destroy altar / recover Chime and return. | Verify Chime item handling. |
| [ ] | untested | 1120 | Find the Third Eye. | Prince Nicolai, Castle Ironfist. | Bring Third Eye to Nicolai. | Item bit QBit 1220. |
| [ ] | untested | 1148 | Kill Snergle and return his axe. | Avinril Smythers, The Haunt tavern, Mire of the Damned. | Kill Snergle in Snergle's Caverns and return axe. | Axe quest QBits 1046/1051; key QBit 1025; lost item handled by Seer. |
| [ ] | untested | 1149 | Expose Silver Helm corruption. | Constable Charles D'Sorpigal, Mist. | Recover evidence from Silver Helm Outpost and return. | Evidence QBit 1039. |
| [ ] | untested | 1150 | Retrieve candelabra. | Andover Potbello, New Sorpigal. | Get candelabra from Abandoned Temple and return. | Candelabra quest is separate from Sulman letter. |
| [ ] | untested | 1152 | Retrieve Andrew Besper's harp. | Andrew Besper, Castle Ironfist. | Recover harp from Dragoon's Caverns and return. | Harp QBit 1027. |
| [ ] | untested | 1153 | Retrieve Ethric's skull. | Gabriel Cartman, Free Haven. | Recover skull from Ethric's Tomb and return. | Skull QBit 1048. |
| [ ] | untested | 1154 | Kill Queen of the Spiders. | Buford T. Allman, New Sorpigal. | Kill queen in Abandoned Temple and return heart. | Done QBit 1055. |
| [ ] | untested | 1155 | Deface Monolith altar. | Eleanor Vanderbilt, Silver Cove. | Deface altar and return. | Done QBits 1047/1156. |
| [ ] | untested | 1158 | Destroy Temple of the Fist crystal. | Winston Schezar, Bootleg Bay. | Destroy crystal and return. | Done QBits 1045/1159. |
| [ ] | untested | 1160 | Rescue Emmanuel. | Joanne Cravitz, Blackshire. | Rescue Emmanuel from Temple of the Snake and return. | Found QBit 1227. |
| [ ] | untested | 1161 | Retrieve lost artifact. | Zoltan Phelps, Free Haven. | Recover from Dragoons' Keep near Castle Temper and return. | Dungeon artifact QBit 1028. |
| [ ] | untested | 1162 | Rescue Sharry. | Frank Fairchild, New Sorpigal. | Rescue Sharry from Shadow Guild Hideout and return. | Verify party/NPC state. |
| [ ] | untested | 1163 | Rescue Angela. | Violet Dawson, New Sorpigal. | Rescue Angela from Abandoned Temple and return. | Dungeon bit QBit 1036. |
| [ ] | untested | 1164 | Rescue Sherell. | Carlo Tormini, Free Haven. | Rescue Sherell from cannibals east of Free Haven and return. | Prisoner QBit 1030. |
| [ ] | untested | 1165 | Destroy Werewolf altar. | Maria Trepan, Blackshire. | Destroy altar in Lair of the Wolf and return. | Werewolf QBits 1040-1044. |
| [ ] | untested | 1167 | Bring Pearl of Putrescence to Balthasar's ghost. | Ghost of Balthasar / Lair of the Wolf. | Find Pearl and bring to ghost. | Active QBit 1166; black pearl done QBit 1059. |
| [ ] | untested | 1168 | Retrieve jewelled egg. | Emil Lime, Kriegspire village. | Get egg from Castle Kriegspire and return. | No-more-chest QBit 1323. |
| [ ] | untested | 1228 | Destroy Book of Liches. | Terry Ros, Darkmoor village. | Destroy Book of Liches in Castle Darkmoor and return. | Original lich side quest; local QBits 1033/1064. |
| [ ] | untested | 1243 | Place five statuettes. | Twillen, Blackshire. | Place statuettes in Sweet Water, Kriegspire, Dragonsand, Mire, Bootleg Bay and return. | Placed QBits 1246-1250; chest/reward QBits 1244/1245/1251. |

## Cross-Continent / MMerge-Specific Quests

| Check | Status | QBit | Quest | Start / Giver | Completion / Condition | Notes |
|---|---|---:|---|---|---|---|
| [ ] | untested | 1712 | Mysterious woman asked you to travel in time and fulfill destinies of other heroes. | Cross-continent quest start. | Verify MMerge-specific main travel flow. | From Cross Continent Q rows. |
| [ ] | untested | 1713 | Enter the Controlled Breach and find Runaway Chaos. | Cross-continent quest chain. | Bring Runaway Chaos to Uneasy Origin Matter. | Verify after baseline worlds work. |
| [ ] | untested | 1714 | Find your friends. | Cross-continent quest chain. | Verify completion target. | MMerge-specific. |
| [ ] | untested | 1715 | Find entrance to the main Breach structure. | Cross-continent quest chain. | Verify completion target. | MMerge-specific. |

## Tracking Notes For Playthrough

When validating a quest, record:

- build commit;
- world and map;
- start NPC/topic or trigger;
- quest item obtained/lost behavior;
- dungeon/event face used;
- completion NPC/topic or trigger;
- final QBits/awards observed;
- whether save/load before completion still works.

High-risk systems to watch while testing:

- NPC topic replacement after quest start/completion;
- map-local versus global QBit collisions;
- quest item recovery via Seer/lost-item QBits;
- indoor buttons/levers/chests that are needed for progression;
- Light/Dark branch exclusivity in MM7;
- MM8 alliance branch exclusivity;
- time/date-sensitive MM6 druid promotions;
- Arcomage global win counters;
- cross-continent travel preserving quest state.
