# Xeen: the original-lines ledger

Owner: A3. Every short MM4/MM5 line the Xeen world quotes or closely paraphrases (README, decision of 2026-11-14;
WORLD_DESIGN §1), with its source reference and where it is used. References are `reference/mm4_5_world_of_xeen/unpacked/text/<game>/aazeNNNN.txt.json`, string index after the colon (`xeen/aaze0028:1`). Double spaces of the source are
removed; "(close)" marks a light paraphrase. Long dialogues are rewritten, not listed here.

Each map needs at least three lines (ROADMAP §5.1 item 6); the "Owner" column says who places the line: A3 in quest and
NPC files (topics, hook texts), A4 in greetings, the map lane in its own events. A map lane that adds a line adds a row.

## X1 Vertigo Meadows and its dungeons

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Welcome to Vertigo. Sadly, most of the population has left because the town is infested with pests. A couple years ago I hired Joe the exterminator ..." | xeen/aaze0028:1 | Gunther, topic Pests (m1.yml); his greeting | A3, A4 |
| "Thank you for cleaning up Vertigo and discovering Joe's treachery. ... Help them and report back." | xeen/aaze0028:2 | Gunther, Joe's invoice (m2.yml) | A3 |
| "The dwarf mines are still being over-run. Please help them." | xeen/aaze0028:3 | M3 journal line; Gunther, Dwarves (m3.yml) | A3 |
| "The local dwarves have informed me of your great deed ... The Red Dwarf Badge of Courage. Congratulations." | xeen/aaze0028:4 | Gunther, Dwarves (m3.yml) | A3 |
| "My favorite citizens, I'm always glad to see you." | xeen/aaze0028:5 | Gunther's second greeting | A4 |
| "Two years ago, I came to this town on contract to control the vermin infestation. ... I've just about got the situation under control." | xeen/aaze0028:7 | Joe, topic Pests (m2.yml); his greeting | A3, A4 |
| "I'll put anyone on the guild roll for free. Dues will cost 25 gold, though." | xeen/aaze0028:13 | Vern, topic Dues (npcs/x1.yml); his greeting | A3, A4 |
| The invoice: "Breeder Slimes, 1 mated pair 287 / 5 Doom Bugs at 145 each 725 / Total: 1012 gold" and "It appears that Joe has been buying monsters and distributing them around town! Mayor Gunther will want to hear about this." | xeen/aaze0028:16 | m2.invoice_crate (XD-01) | A3 (A7 wires) |
| "Sinners must repent." / "The end is near." / "The plague is upon us." / "Slime lords shall rule" | xeen/aaze0028:17-19, :21 | the four Plague Cult members' greetings; topics of two (npcs/x1.yml) | A4, A3 |
| "This space for rent" | xeen/aaze0028:20 | x1.sign_rent | A3 (A5 wires) |
| "Pest control by Joe" | xeen/aaze0028:22 | x1.sign_joe; Joe's second greeting | A3, A4 |
| "Get Lost! Can't you see I'm drinkin'?" | xeen/aaze0028:23 | Dudley's greeting (also Rivercity's and Sandcaster's drunks) | A4 |
| "Some fool said money's now growing on trees. Ha!" | xeen/aaze0028:24 | Old Thorne, greeting and topic Money tree | A4, A3 |
| "This place is deserted. You should go to Rivercity--Now there's a town full of action!" | xeen/aaze0028:25 | Bramble, greeting and topic Vertigo | A4, A3 |
| "That Gunther, what a dunce! He paid that con man Joe a fortune to clean up this town." | xeen/aaze0028:26 | Fenwick, greeting and topic Gunther | A4, A3 |
| "He...he (hic) breeeds (hicup) Breeeeeds them in the (hic) warehouse (hicup)" | xeen/aaze0028:27 | Dudley, topic Joe (m2.yml): M2's clue | A3 |
| "Where to?" | xeen/aaze0028:38 | the mirrors' choice (xeen_common.lua Xeen.useMirror) | A3 |
| "You found some money growing on this tree!" | xeen/aaze0028:46 | x1.money_tree | A3 (A5 wires) |
| "A sign hanging on the side of the desk reads: 'Out of Business'" | xeen/aaze0028:49 | m2.out_of_business (Joe's shop door after M2) | A3 (A5 wires) |
| "The water is cool and refreshing." | xeen/aaze0028:62 | world-wide well line | map lanes |
| "Please help clean up our beautiful town." (after M2 "Thank you.") | xeen/aaze0028:63 | m2.gate_sign | A3 (A5 wires) |
| Myra: "Toad meadow is the only known source of Phirna root ... I will give you five potions for each Phirna root you bring me." / "What, no Phirna root? ..." / "Thanks for the ingredients. I'll make a batch right away." | xeen/aaze0023:0, :2, :3 | Myra, topic Phirna root (q-c21.yml) | A3 |
| "You have found a Phirna plant. Dig it up?" / "Ok, you dug it up." / "Sensing that you already have another Phirna root, the plant stubbornly resists your greedy fingers." | xeen/aaze0023:8-10 (close: the question is dropped) | q-c21.phirna_plant | A3 (A5 wires) |
| Derek: "I am searching for my intended bride, Celia. ..." / "You have not rescued Celia from the zombies yet. Please hurry." / "You have rescued my Celia! ..." | xeen/aaze0023:6-8 | Derek, topic Celia (q-c22.yml) | A3 |
| "Help! I'm in Darzog's tower!--Crodo" | xeen/aaze0019:2, xeen/aaze0023:19 | m1.crodo_bottle_creek (X1), m1.crodo_bottle_lake (X2); M1 journal line | A3 (A5 wires) |
| Orothin: "A couple of years ago I built a statue on each of the two islands near here. ..." / "No luck finding the whistle? ..." / "The Whistle! Thank you. I'll activate the statues now. Bye." | xeen/aaze0023:37-39 | Orothin, topic Whistle (q-c20.yml) | A3 |
| "The statue repels you." | xeen/aaze0023:22 | q-c20.statue_poison, statue_disease (fail) | A3 |
| "You have found an observation post for the Orcs! Destroy?" / "The outpost collapses in a heap of ashes, smoke, and smoldering timber." | xeen/aaze0019:6-7 | X1's orc outposts (A5) | A5 |
| "As I renew the year, so will I renew you." | xeen/aaze0019:15 | the Spring Druid's greeting; Q-C1's hand-in (phase 2) | A4, A3 |
| Valia: "I am just an old woman but before I die I wish to see the witches of Toad Meadow destroyed. ..." (D-89, 2026-11-22: the key line dropped, "The witches fear nothing, and lock nothing." in its place) | xeen/aaze0024:5 | Valia, topic Falista (m4.yml) | A3 |
| "I am waiting for you to destroy the witches and return the Alacorn." | xeen/aaze0024:6 | Valia, Falista (m4.yml) | A3 |
| "You have destroyed the witches and for that I am grateful. For your gallant deeds, I dub thee all Crusaders! ..." | xeen/aaze0024:7 | Valia, Falista (m4.yml) | A3 |
| "I, Falista, grant all great adventurers the title of Crusader." | xeen/aaze0024:11 | Valia, topic Crusaders (t1-a.yml) | A3 |
| "A boy crawls out of the cage. "Thanks for getting me out of there," he says. "I thought the witches were going to turn me into a goblin for sure. I want to go home."" | xeen/aaze0051:3 | m4.cage_3 (XD-04, the hidden cage; the built map's words since 2026-11-20) | A3 (A7 wires) |
| "Feed me!" (toss a gem) / "Goblins back to work!" / "You are the fairest one of all" / "You are the most beautiful creature in all the land" / "Don't forget to use the levitate spell before you enter the cloud world!" | xeen/aaze0051:7, :21, :18-20 | XD-04's skulls (CHANGES XD04-2) | A7 |
| "1 bottle orc's milk, 2 boxes of Dwarf biscuits, 1 can of split toadsoup, and one everlasting stick of troll jerky" / "There are many DEEP mines." | xeen/aaze0033:9, xeen/aaze0034:14 | XD-02 (CHANGES XD02-3) | A7 |
| "Robbers and thieves take a good look at your fate, should you decide to steal from these mines!" / "Dead men tell no tales." | xeen/aaze0035:11, :10 | XD-03 (CHANGES XD03-4) | A7 |
| "Slime lords shall rule" (the slogan daubed in the grain hall) / "The end is near." (under it, in another hand) | xeen/aaze0028:21, :18 | XD-01 `evt:slogan` | A7 |
| "The mine car doesn't move." / "A cave in!" / "The barrel is empty." | xeen/aaze0033:25, :34, :5 (also aaze0034:30, :31) | XD-02: the chained Deep Line cart, the foot drift's rockfall, the barrels beside the two notes | A7 |
| "Nothing here but bones." | xeen/aaze0035:8 | XD-03: the prospector's skeleton in the mole warren | A7 |
| "You have found a war drum of the Orcs! Destroy?" (close: "observation post" made "war drum") / "The drum collapses in a heap of ashes, smoke, and smoldering timber." (close) | xeen/aaze0019:6-7 | XD-05's three drums (`evt:drum_*`, `evt:drum_*_out`) | A7 |
| "Crude furnishings and filthy bedding tell you that orcs have been living in this cave." | xeen/aaze0022 (the orc cave) | XD-05: entering the sleeping hollows (`evt:hollows_voice`) | A7 |

## X2 Rivercity (lines A3 places later; A4's greetings already carry several)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Pray, pay, and be healed today." | xeen/aaze0030:31 | Deacon Coyne's greeting | A4 |
| "If Barok ever got his pendant back, this place might charge me for drinks." / "The tavern hired the sorceresses to run Barok out of town." | xeen/aaze0030:19, :21 | tavern patrons' greetings | A4 |
| "NO MIRROR?!? Get out of my sight!" | xeen/aaze0064:13 | King Burlock's repeat topic (M5, phase 2) | A3 |

| "The sorceresses of Rivercity have stolen a magical pendant of mine. I want it back, and I will reward you if you return it." / "No pendant, no reward." / "Thank you for returning my pendant. Please accept the Enchant Item spell as your reward. I will also return the drinking fountain to normal." | xeen/aaze0030:34-36 | Barok, topic Pendant (q-c2.yml) | A3 |
| "If you can read this ad, so can your customers." / "REAL adventurers try Deep Mine Alpha!" / "School of Navigation 9N" / "Mountains in your way? Try due N." | xeen/aaze0030:29, :67, :27-28 | x2.ad_customers, ad_deep_mine, ad_navigation, ad_mountains | A3 (A5 wires) |
| "What did you expect, money?" | xeen/aaze0030:33 | x2.bank_chest; q-c3.vault (else) | A3 (A5, A8 wire) |
| "For 2,000 gold I will teach you how to use the stars to keep from getting lost." / "For the low, low, price of 5,000 gold, I will teach you how to climb the highest mountains." / "I can teach you how to swim for a mere 100 gold." / "I'll give you 100 gold for a week of work." / "Fighting is simple. ..." / "I see that you are pale and weak. ..." | xeen/aaze0030:9, :7, :11, :1, :3, :5 | Rivercity's skill row: greetings and topics (npcs/x2.yml) | A4, A3 |
| "If you say the name of a town to a mirror, it will take you there." | xeen/aaze0030:68 (close: our mirrors take a touch, not a name) | Ott, topic Mirrors (npcs/x2.yml) | A3 |
| Medin: "The fish supply is low. ..." / "The beasts still live. I wish someone would kill them." / "You have slain the monsters of the lake! ..." / "My friends, I am always glad to see you." | xeen/aaze0011:9-12 | Medin, topic Lake beasts (q-c13.yml) | A3 |
| Danulf: "A terrible thing has happened. My Wand of Faery Magic has been stolen by the Sprites. ..." / "The Sprites still possess my Wand. Try harder." / "You have returned my Wand of Faery Magic! ..." | xeen/aaze0011:1-3 | Danulf, topic Wand (q-c17.yml) | A3 |
| Tito: "While travelling through Troll forest recently, I was ambushed. ..." / "I see you haven't found the Holy Book of Elvenkind. Please keep looking." / "You have recovered the Holy Book of Elvenkind! ..." (D-21 appends the Spirit Master offer) | xeen/aaze0011:5-7 | Tito, topic Holy Book (q-c18.yml) | A3 |
| Ligono: "I hate the surf. ..." / "I see you don't have my skull yet. ..." / "My skull! Thank you! Already I can feel my tie to this world fading. Listen to the sound of the surf for your spell." | xeen/aaze0015:10-12 | Ligono, topic Skull (q-c19.yml) | A3 |
| Nystor: "Those Ogres are ruining me! ..." / "The Ogres aren't gone yet. I think their base of operation is in the hills to the Southwest of here." / "Thank you for getting rid of the Ogres. Here is your reward." | xeen/aaze0010:23-25 | Nystor, topic Ogres (q-c23.yml) | A3 |

## X2's dungeons (A8's rebase lists, 2026-11-20)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "You have found the Elixir of Restoration!" | xeen/aaze0079:0 | q-c12.reliquary (XD-06) | A3 (A8 wires) |
| "There is nothing on, in, or under the bed." / "There is nothing in the crate." / "There is nothing in the coffin." | xeen/aaze0079:1-3 | XD-06's beds, crates, coffins; m10.yak_treasury and q-c12.reliquary (else) | A8, A3 |
| "Yak Pool" / "The pool makes you ill." / "+ 5 Endurance (permanent)" (as +2) / "You are not strong enough to open the coffin." / "Leave the Temple of Yak?" | xeen/aaze0079:7, :25, :14, :18, :17 | XD-06's pool, coffins and exit | A8 |
| "King's Megacredit!" | xeen/aaze0079:26 | m10.yak_treasury ("King's Megacredits!") | A3 (A8 wires) |
| "Leave Darzog's Tower?" | xeen/aaze0059:2 | XD-12's door | A8 |
| "Book of Might" ... "+20 Might (permanent)" (as +5) | xeen/aaze0059-0062 | XD-12's six study books (player bits 11230-11235, m21.yml) | A8 |
| "Thank you for rescuing me from Darzog's clutches. I didn't know that someone else had received my message. Xeen's hideout is just above us in the clouds. You will need the sword ... Newcastle to defeat Lord Xeen. You must make haste. Xeen plans to summon an army from the Darkside to conquer our world." | xeen/aaze0061:0 (one sentence of ours added: Roland is Lord Xeen) | m21.crodo (XD-12) | A3 (A8 wires) |
| "Crodo the Overseer" | xeen/aaze0061:1 | m21.crodo | A3 |
| "Now THIS is a wild town." / "There is nothing on, in, or under the bed." | xeen/aaze0030:23-24 | XD-21's dicing table and bunks | A8 |
| "Don't look so disappointed. I'm not a damsel in distress, but there is a quest you could perform for me. My servants have informed me that my diamond tiara has been stolen ..." | xeen/aaze0066:0 | Roxanne, Q-C3 (phase 2; no longer XD-21's arrival) | A3 |
| "You have found an Ogre lair. Destroy?" / "You break everything you can find in the lair." | xeen/aaze0010:0-1 | q-c23.chieftain (XD-27) | A3 (A8 wires) |

## Act II: Castle Burlock, X3, X4 and their dungeons (2026-11-20)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Ah, more adventurers! I charge you with the quest of finding the Sixth Mirror. ... I will reward the one who returns it to me with an Earldom." | xeen/aaze0064:12 | King Burlock, topic Sixth Mirror (m5.yml) | A3 |
| "NO MIRROR?!? Get out of my sight!" | xeen/aaze0064:13 | King Burlock, Sixth Mirror after the audience (m5.yml); his second greeting | A3, A4 |
| "Only Crusaders are allowed to enter Castle Burlock." | xeen/aaze0014:8 | m5.crusaders_gate (fail text) | A3 (A7 wires) |
| "Years ago King Burlock met Crodo, a kindly old sorcerer ... I'm sure he would have you search for him there." / "You haven't found Crodo yet. Keep searching." | xeen/aaze0064:2-3 | Artemus, topic Crodo (m6.yml) | A3 |
| "Every defensible piece of land needs a wall around it. I can have craftsmen and laborers working on your land for 5 King's Megacredits." / "How about a keep to go with those walls? Just 5 Megacredits!" / "You don't have enough Megacredits." / "I'm sorry, but I cannot do any work on land that you do not own! Buy some land and we'll talk." / "Thanks! We'll have the work done by the time you get back to the site." / "We want to make sure you approve of the work we have already done. Please go and take a look at your castle." | xeen/aaze0064:19-20, :23, :30-31, :37 | Emerson, topics Walls and Keep (m9.yml, m11.yml) | A3 |
| "Wanna buy the land this lovely castle rests upon? Only 50,000 gold!" (as twelve thousand) / "Thanks a lot! You won't regret your decision." / "If you want to make some improvements here you should see the King's engineers. I am sure they will be able to help you." | xeen/aaze0012:1-2, :5 | Ebenezer, topics Newcastle and Buy the deed (m8.yml) | A3 |
| "The workers have finished cleaning out the rubble and patching up the stone work. ... One of the workers found this stone ..." / "If you have enough Megacredits you should think about building up your castle. ..." (D-89, 2026-11-22: the stones retired; the workers name the tomb and the dungeon instead) | xeen/aaze0012:6-8 | Ebenezer, topic Workers (m9.yml) | A3 |
| "You have come upon an Evil Ranger camp. Destroy?" / "You ruin their food, burn their tents, and poison their water." | xeen/aaze0012:3-4 | X3's ranger camp (the map's question; x3.ranger_camp, npcs/x3.yml) | A5, A3 |
| "A plaque at the base of the statue reads: Welcome to the Tomb of a Thousand Terrors. Insanity is our fame, undead is our game." / "King's Megacredit!" / "The coffin is empty." | xeen/aaze0080:0, :26, :1 | m10.tomb_welcome, m10.tomb_vault (XD-08) | A3 (A7 wires) |
| The Golem Dungeon's plaque "Solve the wood, it's like a tree / ... / Set the tumblers and you'll be free." / "All is set, it is plain to see / Master of Golems I now dub thee." / "The chest is empty." | xeen/aaze0081:0-1, :8, :11 | m10.golem_plaque, m10.golem_vault (XD-09); award Master of Golems | A3 (A8 wires) |
| "For 300 gems I'll give you a key," the skull says. (as ten) / "The skull gives you the key to the tower of High Magic." | xeen/aaze0045:48, :54 | m12.skull (XD-10) | A3 (A8 wires) |
| "You found a skeleton key in the chest." | xeen/aaze0058:7 | m13.skeleton_key (XD-11) | A3 (A8 wires) |
| Roxanne: "Don't look so disappointed. I'm not a damsel in distress, but there is a quest you could perform for me." (greeting) / "My servants have informed me that my diamond tiara has been stolen ..." / "I see that you have not recovered my tiara. Please keep trying." / "You have recovered my tiara and gotten rid of that bothersome robber gang. I am pleased. As a reward I give you this treasure." / "It is always exhilarating to see adventurers such as yourselves." | xeen/aaze0066:0-3 | Roxanne's greeting (A4); topic Tiara (q-c3.yml) | A4, A3 |
| The plaques: "King Burlock's ceremonial armor." / "Prince Roland's ceremonial armor." / "Don't worry, be happy." / "Peasant's choice award--Best Ruler of the Year (597)" / "Have a nice day." / "Remember, he who is too sharp sometimes cuts himself." / "Speak softly, but carry a large magic sword." / "Remember, today is the first day of the rest of your life." / "Remember, eat less and think thin." | xeen/aaze0064:6-8, aaze0065:0-3, aaze0066:5-6 | xd07.plaque_* (npcs/xd07.yml) | A3 (A7 wires) |
| "You teleported into the air outside the tower!" | xeen/aaze0065:7 | xd07.old_throne | A3 (A7 wires) |
| "The water refreshes you." | xeen/aaze0064:29 | XD-07's well court | A7 |
| Mirabeth: "I was once a beautiful mermaid. ... " (D-89, 2026-11-22: the Yak Stone line dropped) (the temple placed in Rivercity's woods) / "I'm waiting for you to bring me the elixir of restoration from the evil clerics." / "Thank you so much for getting me the elixir! ... As a reward, I blow my kiss to all of you." | xeen/aaze0016:8-10 | Mirabeth, topic Elixir (q-c12.yml) | A3 |
| Adam: "A terrible thing has happened to Asp. A foul curse has been placed on the town that turns people into snakes. Please save us!" / "Thank you for saving us!" ; Eve: "There is a transformer somewhere in town that is turning people into snakes. If you destroy it, the curse will surely end." (with her lisp) / "The curse is over! Thank you so much!" | xeen/aaze0031:9, :11, :22, :24 | Adam, topic Curse; Eve, topic Transformer (q-c5.yml) | A3 |
| "A message appears in the stone: The southwest corner is where to start / Begin with red to tell them apart" and "Alternate the colors around the well / Then the machine can no longer repel" / "The pedestal is cool to the touch" / "You have found the transformer! Do you wish to destroy it?" | xeen/aaze0031:4-7 | q-c5.pedestal_rhyme, pedestal_touch (X4); the transformer's question (XD-25, the map's) | A3, A5, A7 |
| Carlawna: "The other day I was using my Scarab of Imaging ... flew off toward the desert (as the Gargoyle Range) ..." / "I see you haven't recovered my Scarab of Imaging yet. ..." / "Oh, thank you so much for recovering my Scarab. Now I can complete my spell." | xeen/aaze0010:9-11 | Carlawna, topic Scarab (q-c10.yml) | A3 |
| Falagar: "This region is in a lot of danger. First, my sister Carlawna's Scarab of Imaging was stolen ..." / "You haven't brought me my Crystals of Piezoelectricity. Perhaps they are in Asp." / "Thank the Gods! You've recovered the crystals. You are truly great adventurers." | xeen/aaze0010:15-17 | Falagar, topic Crystals (q-c11.yml) | A3 |
| "Asp-->" / "You have stumbled upon a Barbarian encampment. Burn?" / "The encampment burns to the sound of distant howls of anger and frustration." | xeen/aaze0010:4, :2-3 | x4.sign_asp, x4.barbarian_camp (npcs/x4.yml) | A3 (A5 wires) |
| Autumn Druid: "I am the Autumn Druid. I require the Last Flower of Summer ..." / "Thank you for the Last Flower of Summer. ..." / "Please take the Last Fallen Leaf of Autumn to the Winter Druid." | xeen/aaze0010:5, :7, :29 | q-c1.yml (outline, Act III: waits on the Summer and Winter Druids' ids) | A3 |

## A4's greetings and flavour topics (A4's third session, 2026-11-20)

Copied from A4's list (`devdocs/xeen/lanes/A4.md`, "Original lines for A3's ledger (third session)"); A4 places
each in its greetings or `npcs/flavour/` topics.

| Map | Line | Ref | Where | Owner |
| --- | --- | --- | --- | --- |
| D1 | "The Gremlin King has more bark than bite. He'll send his guards against you, but he's too cowardly to fight..." | dark/aaze0029:46 | npc 4906, flavour topic Gremlins (npcs/flavour/d1.yml) | A4 |
| D1 | "Don't trust Joe. He has some sort of scheme to sell fake treasure maps to fools willing to believe his lies..." | dark/aaze0029:10 | npc 4906, flavour topic Joe (npcs/flavour/d1.yml) | A4 |
| D1 | "Monsters can't count. Monsters can't spel, either. That's why the vault is safe." | dark/aaze0029:145, :147 (close) | npc 4907, flavour topic Monsters (npcs/flavour/d1.yml) | A4 |
| D1 | "You will have a hard time finding spells if you don't look for them in the guild. That's a hint." | dark/aaze0029:39 (close) | npc 4910, flavour topic Spells (npcs/flavour/d1.yml) | A4 |
| D1 | "'This bench reserved for Lyle the Pigeon Feeder.' That's me. I had the sign made. I've sat on it twice." | dark/aaze0029:6 | npc 4927, flavour topic The bench (npcs/flavour/d1.yml) | A4 |
| D1 | "Don't listen to the Drawkcab Monks. Little of what they say makes sense, and what little makes sense is jus..." | dark/aaze0029:44 | npc 4931, flavour topic The monks (npcs/flavour/d1.yml) | A4 |
| D1 | "Every city requires a pass to enter since Alamar took over. Someone is selling passes to Castleview just ou..." | dark/aaze0029:14 (close) | npc 4932, flavour topic Passes (npcs/flavour/d1.yml) | A4 |
| D1 | "Wanna job? Fifty gold a week, no experience necessary. You'd be fixing what the gremlins break. Forever." | dark/aaze0029:42 (close) | npc 4935, flavour topic Work (npcs/flavour/d1.yml) | A4 |
| D1 | "Each tower requires a key for entry... but sometimes they leave the door on top of the towers unlocked. You..." | dark/aaze0029:52 | npc 4937, flavour topic Towers (npcs/flavour/d1.yml) | A4 |
| D1 | "Don't waste your time chasing treasure that runs from you. You can't catch it. My husband tried." | dark/aaze0029:50 (close) | npc 4938, flavour topic Treasure (npcs/flavour/d1.yml) | A4 |
| D1 | "It is the beginning of the end. These are the final days! Ruin is upon us! We are doomed, DOOMED I tell you..." | dark/aaze0029:8 (close: the Queen's fate left out) | npc 4939, flavour topic Doom (npcs/flavour/d1.yml) | A4 |
| D1 | "Ellinger has a great fondness for boots. Why, I couldn't say. I make saddles." | dark/aaze0029:7 | npc 4941, flavour topic Ellinger (npcs/flavour/d1.yml) | A4 |
| D1 | "The Gremlins sure have ruined this city. Mayor Snarfblad is too nice. He should have executed those little ..." | dark/aaze0029:11 | npc 4943, flavour topic Gremlins (npcs/flavour/d1.yml) | A4 |
| D1 | "Perhaps Alamar will just go away if we close our eyes and wish real hard!" | dark/aaze0029:54 | npc 4944, flavour topic Alamar (npcs/flavour/d1.yml) | A4 |
| D3 | "Never take all of a genie's money. It's greedy." | dark/aaze0031:41 | npc 5203, flavour topic Genies (npcs/flavour/d3.yml) | A4 |
| D3 | "Special today! Vulture Repellant, only 25,000 gold!" | dark/aaze0031:19 | npc 5204, flavour topic Vulture Repellant (npcs/flavour/d3.yml) | A4 |
| D3 | "I predict you will go on a long journey. I also predict that you will become very rich and famous. I furthe..." | dark/aaze0031:49 | npc 5219, flavour topic Your palm (npcs/flavour/d3.yml) | A4 |
| D3 | "I hear there is a huge hoard of treasure buried somewhere in the land, but the map to it was lost years ago." | dark/aaze0031:47 | npc 5223, flavour topic Treasure (npcs/flavour/d3.yml) | A4 |
| D3 | "I sense Alamar is an assumed name. I study names, I would know. What the real one is, I can't tell." | dark/aaze0031:27 (close) | npc 5224, flavour topic Names (npcs/flavour/d3.yml) | A4 |
| D3 | "No matter how skilled a wizard is, he'll go down before a good sword and a steady hand. Face them down! If ..." | dark/aaze0031:31 | npc 5225, flavour topic Wizards (npcs/flavour/d3.yml) | A4 |
| D3 | "The wizards in this town are sensitive to insults. Watch what you say!" | dark/aaze0031:29 | npc 5228, flavour topic Wizards (npcs/flavour/d3.yml) | A4 |
| D3 | "Never try to burn green wood. It just doesn't catch fire as easily. Glass needs a hot fire; I learned the s..." | dark/aaze0031:23 | npc 5230, flavour topic Firewood (npcs/flavour/d3.yml) | A4 |
| D3 | "Vulture Repellant doesn't work." | dark/aaze0031:25 | npc 5231, flavour topic Vulture Repellant (npcs/flavour/d3.yml) | A4 |
| D3 | "Natasha will sometimes enchant ordinary things with spells of calm and friendship. The enchantment is usefu..." | dark/aaze0031:35 | npc 5232, flavour topic Natasha (npcs/flavour/d3.yml) | A4 |
| D3 | "A dying paladin gave all his magical armor to the enchanted boulders of the land for safekeeping." | dark/aaze0031:21 | npc 5236, flavour topic The paladin (npcs/flavour/d3.yml) | A4 |
| D3 | "The Barbarians are friends of the Giants. Insult the one and you anger the other." | dark/aaze0031:45 | npc 5237, flavour topic Barbarians (npcs/flavour/d3.yml) | A4 |
| D3 | "There is a passage in the sewer that leads a long ways under the desert." | dark/aaze0031:33 | npc 5239, flavour topic The sewer (npcs/flavour/d3.yml) | A4 |
| D3 | "Spotting secret doors is an art that has taken many years to master, but I could teach you in a matter of m..." | dark/aaze0020:1 (close: the price is the teacher's) | npc 5247, flavour topic Secret doors (npcs/flavour/d3.yml) | A4 |
| D7 | "Fill your packs with the nectar of the Gods while you are here. Those supplies will last much longer than t..." | dark/aaze0037:21 | npc 5602, flavour topic Nectar (npcs/flavour/d7.yml) | A4 |
| D7 | "The people are so small they look like ants, and the mountains and trees look like children's toys. I'm the..." | dark/aaze0037:17 (close) | npc 5608, flavour topic Ants (npcs/flavour/d7.yml) | A4 |
| D7 | "Alamar's birth number is nine, so he naturally prefers to use that number, for any particular purpose, abov..." | dark/aaze0037:25 | npc 5611, flavour topic Nine (npcs/flavour/d7.yml) | A4 |
| DD-03 | "As an empath, I am quite perceptive to my surroundings. Since you are on a quest to save the world, I'll te..." | dark/aaze0041:13 (close: not for free) | npc 5002, flavour topic Empath (npcs/flavour/dd03.yml) | A4 |
| DD-03 | "I am the castle Armsmaster. I will teach you to use your weapons more accurately in combat, if you like." | dark/aaze0041:16 (close: not for free) | npc 5003, flavour topic Armsmaster (npcs/flavour/dd03.yml) | A4 |
| DD-03 | "Thanks for bringing the castle back to reality. We've been trapped here ever since Alamar moved the Castle ..." | dark/aaze0041:19 | npc 5009, flavour topic Out of phase (npcs/flavour/dd03.yml) | A4 |
| DD-03 | "Surely you must know what Alamar has done! No? Why, he slew the guards and stole the Cube of Power, that's ..." | dark/aaze0041:21 | npc 5010, flavour topic Alamar (npcs/flavour/dd03.yml) | A4 |
| DD-03 | "If it weren't for our large stockpile of sun dried lizard innards we surely would have starved to death. Th..." | dark/aaze0041:33 (close) | npc 5012, flavour topic Lizard innards (npcs/flavour/dd03.yml) | A4 |
| DD-03 | "The place is full of secret doors and traps. If you ever come to a dead end in the castle, just keep walkin..." | dark/aaze0041:35 (close) | npc 5014's greeting (Carl the Mason, towns/dd03.yml) | A4 |
| X5 | "The guild is closed to all newcomers, so I can't enter your name on the rolls. If I receive a gift of 1000 ..." | xeen/aaze0032:1 | npc 4501, flavour topic The rolls (npcs/flavour/x5.yml) | A4 |
| X5 | "My name you have heard, and you come to me to learn how to climb mountains. Climbing is mostly not falling...." | dark/aaze0006:15 (close) | npc 4527, flavour topic Mountains (npcs/flavour/x5.yml) | A4 |
| X6 | "Everyone should learn how to pray properly. I can teach anyone for free! The first thing you will have to d..." | xeen/aaze0002:1 (close: the skill's name dropped) | npc 4602, flavour topic Prayer (npcs/flavour/x6.yml) | A4 |
| XD-17 | "Try peanut butter and honey on your morning toast." | xeen/aaze0049:22 | npc 4701, flavour topic Toast (npcs/flavour/xd17.yml) | A4 |
| XD-17 | "I will teach you everything for 100,000 gold. Or learning for less, and you can work out the rest yourselves." | xeen/aaze0049:3 (close) | npc 4706, flavour topic Everything (npcs/flavour/xd17.yml) | A4 |
| XD-17 | "Smile. The intent expression you are wearing is being broadcast to millions from the hidden crystal in the ..." | xeen/aaze0049:14 (close) | npc 4713, flavour topic The crystal (npcs/flavour/xd17.yml) | A4 |
| XD-17 | "Once you have purchased a dungeon you have no need for Megacredits. Not that I would know. I inherited mine." | xeen/aaze0049:24 (close) | npc 4715, flavour topic Megacredits (npcs/flavour/xd17.yml) | A4 |
| XD-17 | "The tavern in Shangri-La has the best tips. Wilbur's tip: honey. Kublai's tip: leave quietly." | xeen/aaze0049:31 (close) | npc 4717, flavour topic Tips (npcs/flavour/xd17.yml) | A4 |
| XD-17 | "If you have suffered magical aging, the druids can help you. Visit the Druid of Summer first." | xeen/aaze0049:6 | npc 4718, flavour topic Aging (npcs/flavour/xd17.yml) | A4 |
| XD-17 | "The moons will align when you are able to visit the Darkside. Then again, you probably already have." | xeen/aaze0049:18 (close) | npc 4719, flavour topic The moons (npcs/flavour/xd17.yml) | A4 |
| D7 | "Celestial boats. Castleview, Sandcaster, Lakeside. Don't lean over the side." | dark/aaze0095, aaze0098 (Lucio the Boatman) | 5607 Lucio's greeting (towns/d7.yml) | A4 |
| D7 | "Ever lie down on your belly and look over the edge of the cloud? The people are so small they look like ants." | dark/aaze0037:17 | 5608 Adonis's greeting (towns/d7.yml) | A4 |
| D7 | "Fill your packs with the nectar of the Gods while you are here. Then pick up a spear." | dark/aaze0037:21 (close) | 5609 Athena's greeting (towns/d7.yml) | A4 |
| D7 | "Pears just about everywhere cost but 1 gold. Know that, and you know trade." | dark/aaze0037:23 | 5610 Hermes's greeting (towns/d7.yml) | A4 |
| D7 | "I'm waiting for my friend Ligono. If you see him, tell him to meet me here." | dark/aaze0037:35 | 5613 Hera's greeting (towns/d7.yml) | A4 |
| DD-25 | "A seer says I'll die of a poisoned drink. So I've stopped drinking. It's terrible." | dark/aaze0013:14 (close) | 5401 Bosco's greeting (towns/dd25.yml) | A4 |
| XD-17 | "Try peanut butter and honey on your morning toast. Or anything on anything. It's Shangri-La." | xeen/aaze0049:22 | 4701 Wilbur's greeting (towns/xd17.yml) | A4 |
| XD-17 | "Shangri-La welcomes you!" | xeen/aaze0049:29 | 4702 Kublai Khan's greeting (towns/xd17.yml) | A4 |
| XD-17 | "You folks look like you want membership in the Shangri-La Wizard's Guild. I'll put your name on the list. T..." | xeen/aaze0049:0 (close) | 4705 Brunhilde's greeting (towns/xd17.yml; it now ends "Membership is free here.") | A4 |
| XD-17 | "I will teach you everything. Well, learning. Learning is everything, if you think about it." | xeen/aaze0049:3 (close) | 4706 Jack Alltrades's greeting (towns/xd17.yml) | A4 |
| XD-17 | "Smile. The intent expression you are wearing is being broadcast to millions from the hidden crystal in the ..." | xeen/aaze0049:14 (close: the camera in your monitor as a crystal in the wall) | 4713 Benedict's greeting (towns/xd17.yml) | A4 |
| XD-17 | "The tavern in Shangri-La has the best tips. I wander here for them." | xeen/aaze0049:31 | 4717 Martok's greeting (towns/xd17.yml) | A4 |
| XD-17 | "If you have suffered magical aging, the druids can help you. Visit the Druid of Summer first." | xeen/aaze0049:6 | 4718 Stumpy's greeting (towns/xd17.yml) | A4 |
| XD-17 | "The moons will align when you are able to visit the Darkside." | xeen/aaze0049:18 | 4719 Lacey's greeting (towns/xd17.yml) | A4 |
| D5 | "Greetings, little ones." | dark/aaze0013:19 | 5452 Gurodel's greeting (towns/d5.yml) | A4 |
| X2 | "The tavern pays us to keep Barok out of town. You are not Barok. Sit, but touch nothing." | xeen/aaze0030:21 (the tavern hired the sorceresses) | 4156 Velda's greeting (towns/x2.yml) | A4 |
| D4 | "These stairs once led to a tavern, but it was destroyed long ago. / ... to a blacksmith shop ..." | dark/aaze0033:1-2 | closed text of houses 4652, 4653 (towns/d4.yml) | A4 |
| D4 | "There is a sign here that reads "This boat under repair."" | dark/aaze0033:18 | closed text of 4655 Lakeside Yachts (towns/d4.yml) | A4 |

## Act III: X3, X5, X6 and the druids; Darkside's main steps (A3, fourth session, 2026-11-20)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| The Summer, Autumn, Winter and Spring Druids' relay lines ("I am the Winter Druid. I require the Last Fallen Leaf of Autumn ...", "Please take the last Snowflake of Winter to the Spring Druid.") (close) | xeen/aaze0006, aaze0010, aaze0003, aaze0019 | Q-C1's four druids (q-c1.yml) | A3 |
| Kai Wu: "I am a peace loving old monk driven from my sacred home. ..." / "There are still Ninja in my Pagoda. ..." / "You have destroyed the Ninja Clan ... please let me fill your packs with food." | xeen/aaze0003 | Kai Wu, The Pagoda (q-c4.yml) | A3 |
| "You have dishonored the Ninjas by entering the Pagoda. They surely will not return to reclaim it." | xeen/aaze0003 | q-c4.clan_master (XD-22) | A3 |
| Randon: "The people of this fair city were driven out by a curse ..." / "You haven't driven the spirits from Winterkill yet. Keep trying." / the two "Congratulations! You've successfully driven out ..." / "... I dub thee Ghostslayers Extraordinaire." / "Always a pleasure to see you, Ghostslayers." | xeen/aaze0032 | Randon, Ghosts (q-c6.yml) | A3 |
| "1) Destroy all ghosts. 2) Bang southern gong. 3) Re-visit Randon. 4) Repeat as necessary." / "Bang twice on each northern gong ..." / "We have great treasure you can see / Bang the gong and set us free" / "You'll never win this game of war / The dead shall rule forevermore" / "Acme Ghost Visualization System" | xeen/aaze0032 | q-c6 hooks (X5) | A3 (A6 wires) |
| "If the Dials are properly set, / The count will definitely be upset. / Open his coffin and bid him farewell; / only then can you use the magic of the well." / "Only at night can you put up a fight." / "A stitch in time" / "Lives of a cat" / "The lid refuses to budge. A symbol etched on the surface of the lid flashes pale blue whenever you try to move it." | xeen/aaze0029 | q-c7 hooks (X3) | A3 (A5 wires) |
| Halon: "I am Halon the Efficient. ..." / "You don't have the lava! ..." / "Lava! Great! ..." / "It is wonderful to see my clock work year round. ..." | xeen/aaze0007 | Halon, Water clock (q-c14.yml) | A3 |
| Thickbark: "It is good to see some civilized people around here. ..." (close) / "The Trolls are not dead yet. ..." / "Thank you for killing the trolls, civilized ones. ..." (close) / "You are welcome to converse with us anytime, civilized ones." | xeen/aaze0007 | Thickbark, Trolls (q-c15.yml) | A3 |
| Glom: "Oh mighty heroes, your fame preceeds you. ..." / "Every day the casualties increase. ..." / "We saw the Cyclops' outpost burning in the distance. ..." / "Friends, you are always welcome here." / "You destroy the outpost. Glom will be pleased." | xeen/aaze0003, aaze0004 | Glom, Cyclopes (q-c16.yml); q-c16.outpost | A3 |
| "Every city requires a pass to enter since Alamar took over." (close) | dark/aaze0029 | m14.gate (fail) | A3 |
| The moral question at Ellinger's door, its three answers; "Begone!", "Who do you seek?", "You may pass!" | dark/aaze0053, aaze0056 | m17.question, m17.password | A3 (A8 wires) |
| "Boots of Paradise, By Ellinger J. Hofenhager" / "Ah, lovely boots! Sweet leather foot holders, hard iron hobnail, how I adore thee!" | dark/aaze0056 | m17.book_of_boots | A3 |
| Ellinger: "Welcome. I'm glad you made it to the top of my tower. ..." and his disc lines ("Ahh! I see you have energy discs for me! ...", "Excellent work. ...", "Good, good. More discs. ...", "Have I taken the time to tell you that you are doing a wonderful job? ...", "No discs? Well, don't worry. ...", "This is fantastic! ...", "So close! ...", "Congratulations! We've done it! The Castle is free! ...") (close, shortened) | dark/aaze0056 | Ellinger, Alamar (m17.yml), Energy discs (m19.yml, m26.yml) | A3 |

## Darkside side quests (A3's helper's outlines, made full in session 8, 2026-11-20)

The topic and hook texts of the outline files quote these strings (exact or "(close)"); the rows name the source
strings per file, the files carry the lines themselves.

| Lines | Ref | Where | Owner |
| --- | --- | --- | --- |
| The gremlin court's rounds, Gettlewaithe, Snarfblad | dark/aaze0029:85-87, :93, :95, :97 (close), :98, :103 (close), :105-107, :132-133 | q-d1.yml | A3 |
| Jethro, Jasper, Warden Krupp | dark/aaze0029:72-75, :77 | q-d2.yml | A3 |
| Joe's maps ("Don't trust Joe ...") | dark/aaze0029:60, :76; dark/aaze0017:1 (close) | q-c24.yml | A3 |
| The Drawkcab monks and Brother Reger | dark/aaze0029:63, :65, :67, :69, :70; dark/aaze0004:27, :31-34; dark/aaze0037:6 | q-d3.yml | A3 |
| Dyson's chests | dark/aaze0029:157 | q-d4.yml | A3 |
| Valio and Rooka | dark/aaze0030:10, :12, :22, :23 (close), :24, :25 | q-d5.yml | A3 |
| Dreyfus, the heretics, the clerics | dark/aaze0003:22 (close), :24, :25; dark/aaze0060:8 (close), :9; dark/aaze0057:4, :5 | q-d6.yml | A3 |
| The four gemsmiths, the God of Minerals | dark/aaze0003:3, :6, :8-11; dark/aaze0007:7, :9 | q-d7.yml | A3 |
| Vespar and his handle | dark/aaze0007:17-19 (close); dark/aaze0019:0 | q-d8.yml | A3 |
| Nibbler and the melons | dark/aaze0008:11 (close), :12-15; dark/aaze0012:6 | q-d9.yml | A3 |
| Sharla's three replies, Sheewana, the alcoves | dark/aaze0012:23, :25, :26, :30-34; dark/aaze0075:19; dark/aaze0077:0, :14 | q-d10.yml | A3 |
| Kramer, Graalg, the forts | dark/aaze0007:3-5; dark/aaze0015:12, :16, :18, :20-24 | q-d11.yml | A3 |
| The forts: "You've found an Ogre fort, but the Ogres are out hunting. Burn?" (the map's question) / "The fort collapses in a heap of burning timbers and smoldering ash." (the source's experience dropped) | dark/aaze0015:7, :8 | DD-13's fort halls (A7's question); q-d11 fort_west, fort_east | A7, A3 |
| Yog | dark/aaze0007:13, :22, :27, :28 | q-d12.yml | A3 |
| Hobstadt | dark/aaze0008:2; dark/aaze0040:5, :9, :11 | q-d13.yml | A3 |
| Caleb and the gargoyles | dark/aaze0019:13, :16 (close), :17, :23; dark/aaze0021:7 | q-d15.yml | A3 |
| Thaddeus, the Jewel of Ages | dark/aaze0024:17-19 (close), :21 | q-d18.yml | A3 |
| The Southern Tower (Thaddeus's key, the thieves) | dark/aaze0024:17; dark/aaze0062:1 (prices dropped), :2; dark/aaze0063:6-8 | q-d19.yml | A3 |
| Luna's statuettes | dark/aaze0004:21-25 (close); dark/aaze0057:3, :4; dark/aaze0034:7 (aaze0035:29 is DD-21's grille now, D-62 Q45) | q-d20.yml | A3 |
| Astra and the wizard quarter (session 8) | dark/aaze0031:75 (close), :76, :77 (close), :78, :79 (close), :80 | q-d14.yml | A3 |

## Act V: M31-M35 (A3, eighth session, 2026-11-20)

| Lines | Ref | Where | Owner |
| --- | --- | --- | --- |
| "All beings have a true name. Alamar's true name, for instance, is Sheltem."; the four prophecy statues | dark/aaze0037:4, :12-15 | m31.yml (Soul Storage plaque, statue_1-4) | A3 |
| Zeus: "Prince Roland is held by Alamar in the bottom level of the Castle." | dark/aaze0037:27 | m31.yml (npc 5612) | A3 |
| Corak: "Ah! A Soulbox! You have done well ..." ; "I cannot leave the safety of this ship ..." ; his awakening (close) | dark/aaze0087:2 (close), :3, :4 | m32.yml (npc 5513) | A3 |
| The sundials and the gate: "The time is not right. Access denied!", "What is Alamar's true name?", "Access approved!", "Wrong! Access denied!" | dark/aaze0050:17, :19-21 | m33.yml | A3 |
| The four sundials: "Fire Time", "Air Time", "Earth Time", "Water Time"; "The sundial reads N.  Turn?" (all four must read nine, the gate checks them together) | dark/aaze0050:1-16; maze0050 events (0,15), (14,15), (14,1), (0,1), the gate (7,8) | `Xeen.alamarSundial` (xeen_common.lua) | A3 (A8 calls it on DD-17 L2) |
| The Pharaoh on Lord Xeen and the scepter (close) | dark/aaze0086:15, :17 | m33.yml (npc 5453, Lord Xeen) | A3 |
| Slick's patter and prizes; "No one may enter Castle Xeen without a cupie doll!"; the four statues | xeen/aaze0027:2-5, :10, :12-26, :31, :42-43 | m34.yml | A3 |
| King Burlock: "Thank you for rescuing Xeen from that foul spirit. It is a pity about the mirror, though."; "Your destiny lies on the darkside of Xeen." | xeen/aaze0064:14, :15 | m35.yml (npc 4401), m5.yml | A3 |

## Act VI and Act V's side quests: M36-M42, Q-C26, Q-D16, Q-D17, Q-D23, Q-D24 (A3, ninth session, 2026-11-20)

| Lines | Ref | Where | Owner |
| --- | --- | --- | --- |
| The Pharaoh's checklist: "the destiny of Xeen is in sight ... turn on the four machines ... awaken the elemental sleepers ... have you rescued Prince Roland ...?" (close) | dark/aaze0086:17 | m36.yml (npc 5453) | A3 |
| "Reflector. Activate?" / "The Reflector hums quietly." | xeen/aaze0001:17-18, aaze0004:0-1 | m37.yml (four hooks) | A3 |
| "A disc of dark crystal on a stone stem, turned toward the stars below the rim. Reflector. Activate?" (X1, Water); the pale-crystal disc "turned toward the wind off the edge" (X6, Air); the red-crystal disc "turned toward the heat off the mountain" (X7, Fire) | xeen/aaze0001:17, aaze0021:0 ("Reflector. Activate?", whole), joined after the map's own look at the disc into one Yes/No prompt (D-66 item 6); X5's Earth Reflector still has no question (A6) | the Reflectors' map events on X1 (79), X6 (43), X7 (37), then m37.reflector_* | A5, A3 |
| The sleepers' three answers ("The Guardian has not informed me ...", "Awaiting Grunfeld field activation.", "Grunfeld field generator is active ..."); the four Steps; "Accept the test of Fire?" | dark/aaze0025-0028 | m38.yml | A3 |
| The Alamar statue's boast; "Nine is the time."; "Access denied! You do not have the proper I.D."; Roland's thanks (shortened) | dark/aaze0052:3-13 | m39.yml | A3 |
| "Box"; "Nothing here." (the key vault's box, then empty) | dark/aaze0052:2, :16 | FD-01's key box (q-f1.tower_key's find, 117844) (D-69) | A8 |
| "The skull says, "Access denied! You do not have the proper I.D.""; "Access granted." rewritten for the Cube: "The skull sees the Cube of Power and says, "Access granted."" (the world has no I.D. cards, D-57 Q18; :5-6, the Gold card's door, unused: one skull door, D-69 Q64) | dark/aaze0052:3, :4 (rewritten) | m39.skull_door (FD-01, between the warden's room and the stasis lift) | A3 (A8 wires) |
| "Coffin" (the stasis coffin's and its field's hover); "Prince Roland"; Roland's thanks, shortened, his lid sliding back first ("The coffin's lid slides back and a man sits up, blinking.", ours) | dark/aaze0052:7, :8, :9 (shortened) | m39.roland (FD-01) (D-69 change 2) | A3, A8 |
| "The message on the plaque reads: Nine is the time." | dark/aaze0052:12 | m39.plaque_nine (FD-01, the Hall of Nine by the lever hall) | A3 (A8 wires) |
| The statue's boast ("The statue speaks as you approach: Not only is Alamar a wise and just ruler ...", shortened) | dark/aaze0052:13 | m39.statue (FD-01's first hall, once: 117840) | A3 (A8 wires) |
| "The message on the plaque reads: FEWAEEFFWAEFAWEEWWEFAW / Remember: A = Air, E = Earth, F = Fire, W = Water." (lore: the order of DD-17's belts) | dark/aaze0052:14 | FD-01's assembly hall plaque (map-local) | A8 |
| "Lever"; "The lever won't budge." (after the first pull); the first pull's tells "Far to the west, a wall grinds down into the floor." / "... east ..." (ours, D-69 change 1) | dark/aaze0052:15, :17 | m39.lever_west, lever_east (FD-01, 117841-117842) | A3 (A8 wires) |
| "You draw the bolt."; "Bolted from the other side." (the bolted grate's two faces); "Its light is out. Its twin stands outside the gate." (the dead pyramid); "You climb down through smoke and rubble to the floor of what was Castle Alamar." (the shaft's first arrival from D7, once, 117846); "Climb up through the hatch?" / "Bolted from above." (the shaft's way up) | ours (D-69 changes 4, 5, Q70; the way up as DD-17's, D-58 D-5) | m39.grate_bolt, grate_bolted, pyramid, shaft_arrival; q-d26.depths_hatch | A3 (A8 wires) |
| "What is my name?" / "Correct, come on up!" / "Wrong"; Picard's widget lines (close; Halon is "the Efficient, the clockmaker, whose workshop stands east of Darkstone Tower" where the source has "the Inventor, who lives just north of Darkstone Tower": X5's workshop lies about 20,000 east, G's question 43) | dark/aazex125:16-19, aazex126:0-8 | m40.yml (pending Picard) | A3 |
| "A voice booms: No Sound No Ground!"; "An invisible seal prevents passage."; "The seal has been broken." | dark/aazex116:2, :7-8 | m41.yml | A3 |
| The Pharaoh's note on its post at the start: "A message reads: It's a long road ahead so rest where you can. But don't forget to recast your spells. Signed, The Dragon Pharaoh"; the shrine's refusal "Dragon Pharaoh, Guardian of Xeen: In order for me to commence the unification ceremony ..." | dark/aazex129:12-13, :15 | m42.yml (pharaoh_note, shrine) | A3 (A5 wires) |
| "Rest Stop" (the three huts' signs, hover and click) | dark/aazex129:0 | m42.rest_stop | A3 (A5 wires) |
| The ten boards, hover and click, the source's spelling: "Might and Magic", "King's Bounty", "Empire Deluxe", "Spaceward Ho!", "Vegas Games", "Inherit the Earth", "New World Computing", "Tunnels and Trolls", "Nuclear War", "Planets Edge" (the lettered faces read the same, D-56 change 8) | dark/aazex129:1-10 | m42.board_* (ten hooks) | A3 (A5 wires and letters) |
| "The observatory is closed." | dark/aazex129:11 | m42.observatory | A3 (A5 wires) |
| "Descend into Darkstone Tower?" (the stair house's way down, both ways: the `exit` preset's question means this) | dark/aazex129:14 | P5's stair house (the map's `exit` preset) | A5 |
| Gurodel: "Greetings, little ones."; "You search the bloody throne and find two energy disks." | dark/aaze0013:19, :34 | q-d16.yml | A3 |
| Bosco's seer and the Chalice; "I dub thee royal taste tester"; "Have you learned nothing of the Voweless Knights? Begone!"; the knights' vowel-less style | dark/aaze0013:14-16, aaze0072:6, aaze0069-0071 | q-d17.yml | A3 |
| Sandro: "I am Sandro, the most accomplished sorcerer ..."; "Do not come to me without my heart ..."; "Thank you for returning my heart ... Alamar CAN be defeated." | dark/aaze0035:26-28 | q-d23.yml | A3 |
| The seven boulders' riddle lines; "Correct! You have solved my riddle ..."; the dying paladin's sign | dark/aaze0010:1-9, aaze0014:1-13, aaze0031:21 | q-d24.yml | A3 |
| XD-24's vault door by day (paraphrase, D-25 Q1: the source's coffin lid made the door): "The door refuses to budge. A symbol etched on its surface flashes pale blue whenever you try to move it." | xeen/aaze0029:24 (close) | XD-24 (A7's door event) | A7 |
| DD-11B's second thieves' letter (paraphrase, D-25): "A message on thieves' guild letterhead reads: To all members: Troll holes located by the Forbidden Fruit hut, by the dead adventurer's pack, and the wide one near the rim. The wide one is the King's." | dark/aaze0040:6-7 (paraphrase: the grid squares become D2's three holes) | DD-11B, the thief's satchel (A7's text) | A7 |
| "Troll Juice" / "This stuff is poisonous, but the experience improves you." (the source's +1 to all statistics dropped: D-25 Q8, +2 Endurance) | dark/aaze0040:1-2 (close) | q-d13.yml (troll_juice); DD-11B's vat (A7) | A3 |
| "Prince Book" / "For the eyes of the prince only!" | dark/aaze0064:3-4 | q-d19.yml (prince_book, its first state); DD-06's library (A7) | A3 |
| XD-23's lair: "The stench of this cave tells you that Trolls have been living in it. It is filled with things that Trolls find valuable: Bones, straw beds, fist-sized rocks and hides. Destroy the lair?" | xeen/aaze0008:2 | XD-23's last hall (A7's question); q-c15.lair | A7 |
| DD-09's prisoners: Nathan "... Remember, Orcs can't jump."; Sky "... I haven't seen the sun in days!"; Snog "... for refusing to do evil ..."; Alicia "The Orc Shaman tells lies, and his tea is poisonous. Watch yourself." | dark/aaze0073:3, :5; aaze0075:9, :11 | q-d10.yml (npcs 5111-5114, Thanks) | A3 |
| The Book of Sorcerer's Knowledge: the headache text; "Reading the book improves your mind. +2 Intellect (permanent)." (+25 rescaled, D-26); "You read the book, but learn nothing new." | dark/aaze0056:5-7 | m17.yml (sorcerer_book hooks, DD-02) | A3 |
| Castle Kalindra's prisoner list: Vexor the Black, Clemon the Dead, Saxar the Permanent; Iron Vithnipravad, Argonax, Drothnavod the Weighty (A.K.A. Scraps) (close: "Dragon Mummy" becomes "Bone Dragon", two liches added, D-26) | dark/aaze0044:8 | t2-a.yml (cells) | A3 |
| The Book of Ascension's scrap, ending "... pull lever and drink of the Crystal Water." (D-27); "You are hereby dubbed a Disciple of Bark!"; "The water is cool and refreshing."; the Dark Water's first sentence (its death made survivable, D-27) | dark/aaze0076:2, :6-8 | q-d10.yml (book_of_ascension, crystal_water, dark_water) | A3 |
| The Orcs' tea: "Other beings say that we Orcs just aren't civilized. I now invite you in for a cup of tea to debate on this issue." | dark/aaze0075:17 | q-d10.yml (kettle) | A3 |
| Barticus' gym: "It costs 5,000 gold to use the gym. Pay?" (50,000 rescaled, D-27); "Enjoy the facilities."; "What do ya think this is, a charity gym? Come back when you have enough gold."; the brews (+10 rescaled to +2) | dark/aaze0032:3, :5, :7-10, :14 | npcs/dd18.yml | A3 |

| Source | Here | Why |
| --- | --- | --- |
| Roland +5,000,000 experience, Sandro +2,000,000, the boulders +1,000,000, the Volcano skulls 250,000 each | 40,000; 12,000; 10,000; 5,000 each | QUESTS rules |
| Darkstone Tower's skull riddle (answer 120) | dropped | no answer-giver (README 2026-11-13) |
| The Northern Tower's voice wants "Chalice" | "Chlc", the knights' own way, told by Bosco | the tower's vowel-less books; a plain answer-giver |

## Acts IV-V: the main steps M22-M30, Shangri-La's hints, the Sphinx (A3, fifth session, 2026-11-20)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Only one sword can slay Lord Xeen. It lies in the ruins of the dungeon under Newcastle." | xeen/aaze0049:8 | npc 4710 Maurice, The sword (npcs/xd17.yml) | A3 |
| "The name of the Sphinx is Golux." | xeen/aaze0049:10 | npc 4711 Alexander, The Sphinx (npcs/xd17.yml) | A3 |
| "The key to the Tower of High Magic lies in the Cave of Illusion." | xeen/aaze0049:12 | npc 4712 Princess Pilar, The key (npcs/xd17.yml) | A3 |
| "Lord Xeen already has the Sixth Mirror." | xeen/aaze0049:16 | npc 4716 Psychic Sally, The mirror (npcs/xd17.yml) | A3 |
| "I hear the secret password for Newcastle dungeon is 'laboratory'. Not much of a secret if you ask me." | xeen/aaze0049:20 | npc 4714 Elona, The password (npcs/xd17.yml); riddle of m23.vault_door | A3 |
| "Never underestimate the power of positive thinking." | MAPS DD-12 (dark, Dungeon of Lost Souls) | m24.arrival (DD-12) | A3 (A8 wires) |
| The combinations 64-52-31 (Dimitri) and 3-31-62 (the Queen); "Who sent you?" answered Dimitri | dark research 1, steps 10, 11, 15 | m24 Dimitri, m24.disk_safes, m25 Ambrose, m27 the Queen, m27.crown_safe | A3 |
| "You're looking for my name, it's five letters long." / "I think you'll like my name. Try not to get it wrong." / "What is my name?" | xeen/aaze0082:2-4 | q-c9.riddle (XD-15) | A3 (A7 wires) |
| "My first is in giant but not in defiant." ... "My fifth is in XEEN but not in Queen." (five clues) | xeen/aaze0084:2-6 | q-c9.hieroglyphs (XD-15) | A3 (A7 wires) |
| "There wolf" | xeen research (Castle Basenji L2) | q-c8.l2_door, Arie, the Basenji peasant | A3 (A7 wires) |
| The registry NCC-1701 and "where no man has gone before" | dark research 1, steps 16-17 | m28.registry_lock, m29.stasis (DD-15, DD-16) | A3 (A8, A7 wire) |
| The dragon tax, 2,000 gold and 20 gems; Dragon Lore 1-5, The Art of Taxation, the Loremaster titles to Taxman Emeritus | xeen research (Dragon Cave) | q-c25 (XD-18) | A3 (A7 wires) |
| Q-D22's coven, Naomi and the prisoners | dark/aaze0033:4, :7, :8, :24-28 (:24-26 close) | q-d22 (outline: Naomi's id) | A3 (A8 wires DD-20) |
| Humble and Pious, the heretic clerics | dark/aaze0058:6-7, dark/aaze0059:6-7 | q-d6 (DD-05) | A3 (A8 wires) |
| Graalg on Alamar | dark/aaze0015:26 | q-d11 Graalg | A3 |
| "Three's the charm." | dark/aaze0064:9 | q-d19.guild_memo (DD-06) | A3 (A7 wires) |

## Act IV dungeons (D-39: XD-14, XD-15, XD-20, DD-07; D-42: DD-05, DD-12, DD-14, DD-19, DD-20) and X7 (D-40) (A3, thirteenth session, 2026-11-20)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Trapped Peasant" (his name); "Thank you for saving me!"; "I once overheard the cult leader say something about "There wolf"." (close) | xeen/aaze0067:2-4 | A2's row 11233; q-c8.peasant_freed; q-c8.peasant (XD-14) | A2, A3 (A7 wires) |
| "STOP! What is the password?"; "There wolf" / "Therewolf"; "Wrong!" (close: "\"Wrong,\" says the door ...") | xeen/aaze0069:8-10, :16 | XD-14's password door (the map's prompt); q-c8.l2_door, q-c8.l2_wrong | A7, A3 |
| The scroll names: Scroll of Intellect, Personality, Speed, Magic, Aging, Fire, Electricity, Energy, Depression, Confusion, Insanity, Weakness, Death | xeen/aaze0068:2-7, aaze0069:0-4, aaze0070:0-5, aaze0067:5-6 | XD-14's hover names; the first words of q-c8.scroll_* | A7, A3 |
| "You have been aged 25 years!!!" (close: "You have been aged ten years!") | xeen/aaze0069:15 | q-c8.scroll_aging (XD-14) | A3 (A7 wires) |
| "My first is in giant but not in defiant." / "My second is in mole but not in mule." / "My third is in lich but not in stitch." / "My fourth is in guard but not in Girard." / "My fifth is in XEEN but not in Queen.", each as "The message reads: ..." | xeen/aaze0084:2-6 | XD-15's five clue walls as map-local signs, one clue each: the drop cell (:2), the west hall (:3), the east hall (:4, :5), the library (:6) (D-39 Q2) | A7 |
| "Hieroglyphs", and the five clues as one text | xeen/aaze0084:0, :2-6 | the library's end wall, the scribes' summary (q-c9.hieroglyphs) | A3 (A7 wires) |
| "King's throne" / "Queen's throne" / "Thieves throne"; Human, Elf, Gnome, Orc, Dwarf throne carved in the throne of legends | xeen/aaze0082:8-10, aaze0083:0-4 | XD-15's hover names; q-c9.throne_* | A7, A3 |
| "You look like tough fighters. Would you like to participate in the War Games? The odds can be high but the thrill of victory is well worth the risk." | xeen/aaze0085:0 | Varro the Arena Master (4609), first greeting (XD-20) | A4 |
| "If you didn't come to fight then you have no business being here! Come back when you have the mettle to do battle for glory!" (close: "If you didn't come to fight, you have no business being here! Pick your battle, or come back when you have the mettle to do battle for glory!") | xeen/aaze0085:1 | Varro (4609), later greeting | A4 |
| "I knew that you were true adventurers! Let the battle begin!" | xeen/aaze0085:2 | XD-20's floor: a step message when the party lands on its mark | A7 |
| "Congratulations on your most spectacular victory! ... I will now send you back to Vertigo ..." (adapted: "Congratulations on your most spectacular victory! The gate is open. Gorm's coach waits in the yard.") | xeen/aaze0085:3 | XD-20's floor, after the engine's reward line | A7 |
| "The battle is not yet won! Get back in there and either hold your head high in victory or die in a blaze of glory!" | xeen/aaze0085:4 | XD-20's booth window before the last opponent is dead | A7 |
| "Fountain of Minimal Abilities"; "Your statistics have increased!"; "The water is cool and refreshing." | dark/aaze0068:1-3 | q-d18.minimal_fountain (DD-07) | A3 (A7 wires) |
| "Book of Fantastic Knowledge"; "Your intellect is already fantastic!" | dark/aaze0068:5-6 | q-d18.fantastic_book (DD-07) | A3 (A7 wires) |
| "A magic aura around the book pushes you back." (+ "The book answers to no one living.") | dark/aaze0068:7 | q-d18.great_power_book (DD-07; D-39: a final refusal) | A3 (A7 wires) |
| "You have found a rock that is still hot from an ancient volcanic eruption! Strangely, you are able to pick it up without getting burnt." | xeen/aaze0018:8 | q-c14.lava_rock (X7, the cooled-flow island) | A3 (A5 wires) |
| "You have found an Orc Outpost. Put it to the torch?"; "The Outpost burns well." | xeen/aaze0018:3-4 | X7's outpost question (event 22, joined to the look; D-72, see "Outdoor prompts"); x7.orc_outpost | A5, A3 |
| "Shrine of Fire"; "You don't think anyone is listening." | xeen/aaze0018:5-6 | x7.shrine_fire, x7.shrine_fire_again (daily) | A3 (A5 wires) |
| "Well of Speed"; "The water is cool and refreshing." | xeen/aaze0018:0-1 | x7.well_speed, x7.well_speed_again | A3 (A5 wires) |

| "Fountain"; "The water is cool and refreshing." (+10 resistances rescaled to +5) | dark/aaze0058:0-3, aaze0059:0-3 | q-d6.fountain_fire, _air, _water, _body (DD-05, D-42) | A3 (A8 wires) |
| "Cauldron" (+25 Personality, Endurance, Speed rescaled to +2) | dark/aaze0033:29-32 | q-d22.cauldron_personality, _endurance, _speed (DD-20, D-42) | A3 (A8 wires) |
| "Joseph the Prayermaster": "Knowing how to pray properly can sure come in handy when the going gets tough. I can teach you for 10,000 gold." | dark/aaze0034:3-4 | not used: Joseph is left out (D-42 DD-20 Q5); kept here for the record | — |
| "Soul Waters"; "Refreshing." (+654,321 and +7,654,321 experience rescaled to 1,000 and 2,000 per drinking member); "Minotaur's Private Reserve" | dark/aaze0080:1-2, :19, aaze0081:3-6 | m24.soul_waters_l3, m24.soul_waters_l4 (DD-12, D-42 Q5) | A3 (A8 wires) |
| "There seems to be no way in."; "Hello again, Adventurers. Would you like my griffin to fly you inside?" | dark/aaze0021:3, :9 | D4's Blackfang gate before and after M25 (the map's question); m25.gate_flight | A6, A3 |
| "Are you ready to leave this awful place, friends?" | dark/aaze0045:1 | Ambrose on DD-14's landing: the perch's question and his topic Fly us out (m27, D-52); both call m27.fly_out, which moves the party | A8, A3 |
| "A force like wind pushes you back, lightly at first, but gaining strength as you put more effort into advancing. You are unable to descend." | dark/aaze0047:0 | m27.dungeon_stair's fail text (DD-14, D-42 Q6) | A3 (A8 wires) |
| "How dare you speak to me? You can learn to show respect to your betters on your own, or I can teach it to you." | dark/aaze0031:51 | Blastem the Wizard (5248)'s greeting (DD-19) | A4 |
| "I think we're ready for that lesson right now." / "Do you need your boots licked?" (the two answers, as topic labels "The lesson", "Boots licked"); "It's always a pleasure to be able to converse with other beings as intelligent as I." | dark/aaze0031:110, :112 | Blastem's topics (q-d14.yml, NPC 5248, D-42 Q5) | A3 |
| "Orange Potion" / "Purple Potion" (+10 rescaled to +2) | dark/aaze0031:57-60 | q-d14.orange_potion, q-d14.purple_potion (DD-19) | A3 (A8 wires) |
| Source | Here | Why |
| --- | --- | --- |
| Basenji's scrolls: +5 stats and +10 resistances with 5,000 experience each; Aging 25 years | +2 stats and +5 resistances once per character, no experience; ten years; Death makes Unconscious | D-4's sizes (D-39 Q3) |
| The Sphinx's thrones: titles, "+500,000 experience points" | +2 Might, Personality, Accuracy, Endurance once per character | D-39 Q1 |
| The Sphinx's Book of Teleport and Book of Alchemy (Item to Gold) | two gem finds; the Starburst and Divine Intervention books on the legend throne | MM7 has neither spell (D-39 Q3) |
| DD-07: "+50 Intellect (permanent)"; the Book of Great Power's "+5 Levels ... you lost all your secondary skills!"; the Bubbling Vat's "+1 Level" and 50 years | +2 Intellect; the book refuses everyone; the vat is dressing | no levels (QUESTS rules, D-39 Q3) |
| The Warzone: "I will now send you back to Vertigo" | "The gate is open. Gorm's coach waits in the yard." | D-8.1: the coach yard (D-39) |
| X7: "+ 50 speed"; "+50 fire resistance."; the outpost's "+ 1,000 experience" | +2 Speed once per character; +10 Fire resistance until tomorrow, daily; 500 experience | D-40 |
| DD-05's fountains +10, DD-20's cauldrons +25, DD-19's potions +10 (all permanent) | +5 resistances, +2 statistics, once per character | D-4's sizes (D-42) |
| DD-12's Soul Waters, +654,321 and +7,654,321 experience | 1,000 and 2,000 per drinking member, once | D-42 Q5 |
| XD-16's skulls "+ 250,000 experience"; XD-19's "+ 200,000 experience" | 5,000 per skull; nothing for machines or generators (the scepter's 35,000 carries M35) | MM6-MM8 sizes (D-47 Q15) |
| DD-16's alien device: statistics raised to at least 50, age +50 | +1 to every statistic and five years, once per character | D-47 Q18 |

## Act V dungeons (D-47: XD-16, XD-19, DD-16, DD-24) (A3, fourteenth session, 2026-11-20)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "The skull of a demon grins wickedly at you, and you have a sudden desire to smash it.  Destroy?"; "The skull of a devil stares at you as though daring you to damage it.  Destroy?" | xeen/aaze0046:0, :1 | XD-16's two altars (the map's question; Yes calls q-c26.demon_skull, devil_skull) | A7 |
| "The chest is empty."; "The chest explodes!" | xeen/aaze0046:2, :6 | XD-16's five trap chests (map-local, D-47 Q2) | A7 |
| "You smash the skull." (the "+ 250,000 experience" dropped) | xeen/aaze0046:4 | q-c26.demon_skull, devil_skull (close) | A3 |
| "Leave the Volcano Cave?" | xeen/aaze0046:5 | XD-16's exit preset | A7 |
| "Down Level?" / "Up Level?" | xeen/aaze0047:0-1, aaze0048:0-1 | ledger only: XD-16's stairs are walked (D-47) | — |
| "Guard Making Machine.  Destroy?"; "Fire / Electricity / Cold / Poison Generator.  Destroy?" as Fire, Air, Water, Earth Generator | xeen/aaze0075:0-4, aaze0078:0-2 | XD-19's two machines and four generators (the map's question; m35.gen_* `where`) | A7, A3 |
| "+ 200,000 experience" | xeen/aaze0075:5, aaze0078:3 | ledger only: no experience for machines or generators (D-47 Q15) | — |
| "Exit Castle Xeen?" | xeen/aaze0075:6 | XD-19's exit preset | A7 |
| "You have found the Sixth Mirror! ... Xeen's scepter emits a high pitched whine ... the mirror shatters in a spectacular display of light, noise, and violence. The castle gives an awful shudder ... proceed to the nearest exit in an orderly fashion." | xeen/aaze0078:4 (close, four subtitles) | m35.scepter's `cinematic_subtitles` (XD-19's cinematic) | A3 (A7 wires) |
| "The mirror is protected by some sort of force field that reeks of Lord Xeen's peculiar brand of magic.  You are unable to use or touch it." | xeen/aaze0078:5 | m35.mirror | A3 (A7 wires) |
| "The great Castle Xeen recently stood here." | xeen/aaze0027:44 | X9's gate spot after m35.done | A5 |
| "A strange energy field surrounds a figure suspended within it." | dark/aaze0087:0 | DD-16's field (map-local) | A7 |
| "The strange alien device seems to be dormant."; "Strange energy device"; "Your statistics have all been raised ..., but your age has also increased by ..." (50 and 50 rescaled to one and five years) | dark/aaze0087:5, :8, :10 | m29.alien_device | A3 (A7 wires) |
| "Exit Escape Pod 1?" | dark/aaze0087:6 | DD-16's exit preset | A7 |
| "Main Power Console.  Acivate?" (the typo mended: "Activate?") | dark/aaze0087:7 | DD-16's console question; m29.power_console after Yes | A7, A3 |
| "Phaser Control ... Fire anyway?"; "Photon Control ... Fire anyway?"; "Nothing happens." | dark/aaze0087:9, :11, :12 | DD-16's gun deck (map-local) | A7 |
| Log Entries 1-15 (Terra, S.H.E.L.T.E.M., C.O.R.A.K., VARN 6, King Alamar, CRON, the seedship, the pods, "May the Gods smile upon me.") | dark/aaze0087:13, :25-33 (abridged into five pages) | m29.log_page_1 ... log_page_5 | A3 (A7 pages) |
| "Scanning Console ... X.E.E.N. (Xylonite Experimental Expansion Nacelle) Starseed Project ..." | dark/aaze0087:22 | DD-16's main deck (map-local) | A7 |
| "Stasis field deactivated." | dark/aaze0087:24 | DD-16's console after m32.done (map-local) | A7 |
| "Though he denies it, Alamar's plans will ultimately destroy all creatures on Darkside.  No sane people could support a tyrant with plans such as his." | dark/aaze0013:26 (close) | q-d16.law_stone (DD-24's long hall) | A3 (A7 wires) |
| "We recognize you as enemies!  Prepare to defend yourselves!" | dark/aaze0013:33 | q-d16.war_threshold (once per war); Gurodel's line after hall_attacked (close) | A3 |
| "You search the bloody throne and find two energy disks." | dark/aaze0013:34 | q-d16.throne (at war, without friends) | A3 |

## D5 and D6 (D-49: the Desert of Doom, the Forbidden Zone, the genie lamps) (A3, fifteenth session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "You have found a Giant's lair.  Destroy?" | dark/aaze0009:1 (also aaze0013:7) | D5's lair, the map's question before d5.lair | A6 |
| "You put your backs into it and tear the place apart." (the "+50,000 experience" dropped) | dark/aaze0009:2 (also aaze0013:8) | d5.lair | A3 (A6 wires) |
| "The water is cool and refresing." (the typo mended); "Your spine tingles and the hair on the back of your neck stands on end." (the "+50 energy resistance" as +5 Air) | dark/aaze0009:4, :5 | d5.fountain_energy | A3 (A6 wires) |
| "Shrine of Great Power. Will the party pray?" | dark/aaze0010:15 | D5's shrine, the map's question before d5.shrine | A6 |
| "Only silence greets your supplications."; "Recognizing the urgency of your quest, the Gods answer your prayers." (the "+15 levels" as +15 to every statistic until rest) | dark/aaze0010:16, :17 | d5.shrine | A3 (A6 wires) |
| "SOMEONE in the party got the munchies and ate all the food!" | dark/aaze0010:18, aaze0014:20 | d5.munchies | A3 (A6 wires) |
| "Fountain of Might"; "The water is cool and refreshing."; "Fantastic Might surges through your body as the water passes your lips." (the "+100 Might" as +20 until rest) | dark/aaze0013:9-11 | d5.fountain_might | A3 (A6 wires) |
| "The pyramid portal has been destroyed." | dark/aaze0013:12 | obelisks.dark_hoard's fail and else lines (the capstone spot) | A3 (A6 wires) |
| "Correct! You have solved my riddle.  Please take the magical things that I have left in the care of these enchanted boulders.  Be sure to visit the other boulders for their treasure." (the experience dropped); "The boulder disappears and leaves behind..." as "The boulder crumbles to sand and leaves behind ..." | dark/aaze0010:2, :9; aaze0014:2 ... :14 | q-d24.answer, q-d24.boulder_1 ... boulder_6 (after solved) | A3 (A6 wires) |
| "Lucky day!  For freeing me, I will grant you one of the following three wishes:" (close: "one of three wishes", the three as buttons Experience, Gold, Gems, rescaled to 3,000 experience, 10,000 gold, ten gems) | dark/aaze0010:13-14, aaze0014:17-18 | Xeen.genieLamp's question (q-d27 wish lamps) | A3 |
| "My powers are low.  I can give you 100,000 gold, but it is all that I have.  Do you want it?" (10,000); "Well here, why don't we share it, since neither of us seem to be greedy."; "Now that I have my powers back I've decided to teach you not to be so greedy.  I'm taking my gold back, plus interest!" | dark/aaze0006:7-9 | Xeen.genieLamp's greedy question, q-d27.share, q-d27.greed (D6's crag) | A3 |
| "Never take all of a genie's money.  It's greedy." | dark/aaze0031:41 | Aladdin's topic (A4's flavour, D3): the greedy lamp's hint | A4 |
| "You have discovered a barbarian camp.  Destroy?" | dark/aaze0006:11 | D6's archers' camp, the map's question before d6.archers_camp | A6 |
| "Smoke rises into the sky as you put the camp to the torch." (the experience dropped) | dark/aaze0006:12 | d6.archers_camp | A3 (A6 wires) |
| "Forbidden Zone.  Keep Out!" as "The Forbidden Zone." plus A3's warning | dark/aaze0002:1, aaze0005:3, aaze0006:10 | d6.zone_sign (D-49 change 9) | A3 (A6 wires) |
| The magic skull's tale of the two necromancers, Darkness and Death (shortened; A3's last two sentences) | dark/aaze0035:24, :31, :32 (close) | d6.skull | A3 (A6 wires) |
| "Book of the Dead Vol. 1" ... ; "You've already read it."; "The experience aged you." (+25 years and 999,999 experience as +8 years and 3,000) | dark/aaze0035:2, :3, :6-16 | d6.book_dead_1 ... book_dead_3 | A3 (A6 wires) |

## X9 and XD-17 (D-50: the Clouds of Xeen, Shangri-La) and the Linguist gate (A3, fifteenth session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Roc Nest.  Destroy?" (Yes/No; the "+ 50,000 experience", :34, as 2,000) | xeen/aaze0027:0 | X9's five nests, the map's question before x9.nest_* | A5 |
| "You are unable to understand the strange runes." | xeen/aaze0027:1 | m34.statue_1-4 and xd07.runes (X8's rhymes): the fail line without the Linguist gate | A3 (A5, A6 wire) |
| "Xeen--9N."; "Danger! Go back!"; "Now entering Xeendom"; "Xeen's Aviary" | xeen/aaze0027:6-9 | x9.sign_nine_north, sign_danger, sign_xeendom, sign_aviary | A3 (A5 wires) |
| "No one may enter Castle Xeen without a cupie doll!" | xeen/aaze0027:10 | m34.gate's fail line | A3 (A5 wires) |
| "Offering" | xeen/aaze0027:33 | X9's six offering statues' title (x9.offering_1-6; the behaviour X8's) | A5 |
| "Enter Castle Xeen?" | xeen/aaze0027:40 | not shown; the gate enters at once (D-72) | A5 |
| "The great Castle Xeen recently stood here." | xeen/aaze0027:44 | x9.castle_gone (the gate's spot after m35.done) | A3 (A5 wires) |
| "The water is cool and refreshing." | xeen/aaze0049:4 | xd17.well after the first drink | A3 (A5 wires) |
| "The moons are not aligned.  You are unable to pass." | xeen/aaze0049:25 | xd17.pyramid's fail line (before m30.done) | A3 (A5 wires) |
| "Congratulations, You found Shangri-La!" (the "+ 1 Level (permanent)" as +20,000 experience, once per character, and the award, D-50 Q1) | xeen/aaze0049:26-27 | xd17.well | A3 (A5 wires) |
| "Leave Shangri-La?" | xeen/aaze0049:32 | the meaning of XD-17's exit windows (the exit preset; the back passage calls xd17.cleft_opened first) | A5 |
| Benedict's "Smile.  The intent expression you are wearing is being broadcast to millions from the hidden camera in your monitor." (paid off, close) | xeen/aaze0049:14 | xd17.crystal (D-50 Q5) | A3 (A5 wires) |
| The Book of Languages (the source's Linguist skill, here the party's: award 420) | research MM4 4, Castle Burlock L1 | xd07.book_languages | A3 (A7 wires) |

## Act VI dungeons (D-57: XD-18, FD-02, FD-03, FD-04) and the Dragon Clouds (D-57 Q36, D-59) (A3, nineteenth session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "The Dragon Cave smells pretty bad. Are you sure you wish to enter?" | xeen/aaze0017:0 | X7's door:xd18 (event 40), joined to the look (D-72; see "Outdoor prompts") | A5 |
| "Dragon tax! 2000 gold pieces and 20 gems fly from your packs and into the urn. Peering inside the urn, you see that your money has vanished." (with Scaldrith's receipt) | xeen/aaze0050:0 | q-c25.yml (Scaldrith 5702, The tax) | A3 |
| "The urn is empty and powerless." | xeen/aaze0050:1 | q-c25.urn (after the tax) | A3 (A7 wires) |
| "Not having enough money to pay the Dragon Tax, you are teleported outside." (close: "Tax first," says the door; D-89, 2026-11-22: no throw, the door stays shut) | xeen/aaze0050:2 | q-c25.king_door's fail line (the Dragon King's door; was inner_door with the map's `leave`) | A3 (A7 wires) |
| "Dragon Lore Volume 1" to "Volume 5", "The Art of Taxation" (hovers) | xeen/aaze0050:5-10 | XD-18's lectern, shelves and ledger stand | A7 |
| The titles "Loremaster of Worms", "... of Lizards", "... of Serpents", "... of Drakes", "... of Dragons", "Taxman Emeritus" (the experience rescaled) | xeen/aaze0050:12-16, :18 | q-c25.yml awards 430-435 | A3 |
| "Exit Dragon Cave?" | xeen/aaze0050:17 | XD-18's exit preset (its meaning) | A7 |
| "Exit Darkstone Tower?" | dark/aazex113:0 | FD-03's exit preset | A7 |
| "Gong"; "A voice booms: \"No Sound No Ground!\"" | dark/aazex113-116:1-2 | FD-03's gongs (hover), m41.gong_voice, the top steps' plates | A3, A7 |
| The plaques' letter rows ("A plaque reads: NWDA---Y-HNA" ...) and L4's heads ("Head 13 speaks: ..."); read down: "NEW WORLD THANKS YOU FOR PLAYING MIGHT AND MAGIC", "SO ENDS THE SAGA OF CORAK AND SHELTEM!", "1994 BEGINS THE NEXT MIGHT AND MAGIC SAGA!", "TYPE \"COMPUTER\" ON LEVEL 4 OF THE DUNGEON OF DEATH. SEE YA SOON!" | dark/aazex113:3-6, aazex114:3-6, aazex115:3-6, aazex116:3-6 | the rows: FD-03's plaques (A7's map texts); the summaries m41.plaques_l1-l4, autonote 4720 | A7, A3 |
| "A force repels you."; "The skull is silent." | dark/aazex116:0, :15 | FD-03's vault field and skull | A7 |
| "An invisible seal prevents passage."; "The seal has been broken." | dark/aazex116:7-8 | m41.seal | A3 |
| Alister's three lines: the dragon egg, "Well, I can see you weren't brave enough to steal an egg, either ...", "You are truly courageous! ... Now I'll just drink this egg potion and..." (the experience dropped) | dark/aazex117:1-3 | q-f1.yml (Alister 5705, Dragon egg) | A3 |
| "Exit Dragon Tower?" | dark/aazex117:4 | FD-04's exit preset | A7 |
| "Bed"; "Nothing here."; "Bones"; "Treasure" | dark/aazex118:0-2, :5, aazex119:0-1, :4, :7, aazex120:0-1, :5 | FD-04's hovers and empty clicks | A7 |
| The dead adventurers' notes: "I don't trust that druid guy ... ten million gold pieces!" (close: "had no 10,000,000"), "I think the secret of the dragon has something to do with forever, or really, really big...", "You have to be pretty smart to survive a look in one of the crystal balls on the Dragon Cloud." | dark/aazex118:3-4, aazex119:5 | q-f1.note_fraud, note_forever, note_balls | A3 (A7 wires) |
| "Potion" (its "+40 end. perm" as +2 Endurance once per character) | dark/aazex119:2-3 | q-f1.endurance | A3 (A7 wires) |
| "Tome of Great Experience"; "You learn nothing new from the Tome" (its +10,000,000 as 4,000 once per character) | dark/aazex120:2-4 | q-f1.tome | A3 (A7 wires) |
| "Exit this Dungeon of Death?" | dark/aazex121:0 | FD-04's dungeon exit preset | A7 |
| "Sorry, the crossword puzzle is not done yet. You may not descend!"; "You may pass. For completing the puzzle here is your reward." (its +5 Level Perm as 6,000); "Wrong!"; "Correct!" | dark/aazex121:1-2, :7-8 | q-f2.crossword, clue_wrong, clue_* | A3 (A7 wires) |
| The twelve clues: "1 Across: King's Staff", "5 Across: Count Blackfang", "6 Across: Imprisoned Queen", "13 Across: Freed from spaceship", "21 Across: Castle beyond the Forbidden Zone", "24 Across: City of the undead", "40 Across: City of sorcerers", "44 Down: Ellinger's Tower is located here", "45 Down: City of Ghosts", "47 Down: You need an amulet to gain entry", "76 Down: Way of transportation in the Land of Xeen", "77 Down: He had a pet dragon" (with "Answer?") | dark/aazex121:10-11, :18-21, :34-35, :50-51, :56-57, :88-89, :96-99, :102-103, :160-163 | q-f2.clue_* (the map's prompts) | A3 (A7 wires) |
| "Welcome", "Ballroom", "Game Room", "Do Not Disturb", "Coffin", "Throne of the Dead", "The Master's Throne", "Lever", "Fountain" (signs and hovers); "You feel strange."; "It's stuck."; "The lever won't budge."; "Ahh, refreshing!" | dark/aazex122:0-6, :8-10, :19, :25, aazex123:1-2, :4-5 | FD-04's map texts | A7 |
| "You try to open lid of the coffin but it is too heavy and you are too weak." (close) | dark/aazex122:7 | q-f2.coffin | A3 (A7 wires) |
| "Shrine of Minor Evil. Destroy?", "... Lesser ...", "... Great ..." (the 1M/2M/5M as 1,000/2,000/3,000); "Shrine of Ultimate Evil. Destroy?" (with a tell, D-57 Q26); "You destroy the shrine, which destroys this dungeon, taking you with it." | dark/aazex122:11-18 | the map's questions; q-f2.shrine_* | A7, A3 |
| Sandro's note: "Gone to Necropolis, will return soon. Please keep the place clean ... leave them alone. Have fun... (signed) Sandro" | dark/aazex122:24 | q-f2.note | A3 (A7 wires) |
| "Gong"; "A voice Booms: Ring the four gongs and then pull the lever. Touch any treasure and you'll have to start over!" | dark/aazex123:0, :3 | FD-04's gong hall (map texts); its reset line is q-f2.gongs_reset | A7 |
| "Lord Xeen Machine. Destroy?" | dark/aazex124:0 | the map's question before q-f2.machine | A7 |
| "Table"; "You find some papers that tell of the World of Xeen maintenance schedules..."; the core terminals ("A message flashes on the terminal screen: Fire Core Operational" ...); "Maintenance", "Control Room" | dark/aazex124:1-6, :12-13 | FD-04's map texts | A7 |
| "Main Terminal / Enter Code"; "Computer" (its +5,000,000 as 2,000); "The screen flashes with the response: You are a Goober!" / "... You are a SUPER Goober!" | dark/aazex124:7-11 | the map's prompt; q-f2.terminal, terminal_wrong | A3 (A7 wires) |
| "Preservation Room" (the step lines, aazex125:0-1), "Home of the Aged" (signs); "Exit the Southern Sphinx?"; "Sarcophagus"; "Barrel"; "Nothing here." | dark/aazex125:0-4, :20-21, aazex126:11-12 | FD-02's map texts and exit preset | A7 |
| "You are too weak to open the sarcophagus." | dark/aazex125:5 | FD-02's sarcophagi (Might 60, D-57 Q10) | A7 |
| The masks: "For 2 million gold I can protect you from the Swinging Death. Will you pay?" (and the Chopping Death; 2,000 gold); "For another million I'll give you a clue. Will you pay?" (500); "There's one born every minute."; "Well, maybe next time."; "Begone, then!" | dark/aazex125:9-14 | the map's questions; m40.mask_swinging, mask_chopping, mask_clue, mask_no | A3 (A7 wires) |
| "Throne of Legends" (Picard's chair, hover only) | dark/aazex126:10 | FD-02's chair; m40.chair | A7, A3 |
| "Book" (hover); Picard's four books: "The book seems to be an account of one of Picard's favorite adventurers. You open the book to a random page and begin reading: ..." (Encoplius and the mad fools; Bruno and "yet another insane beggar", the source's "begger"; princess Shiela with the editor's excision), "This book has been hollowed out and used to store old cigars." | dark/aazex126:13-17 (adapted as FD-02's NOTES say) | FD-02's lecterns (map text) | A7 |
| "Runes"; the six lessons "The strange writings seem to give a lesson about the letter \"P\"" ... "\"D\""; "The strange runes read: \"Study the lessons to learn my name.\""; "... \"Don't feed the dragons.\"" | dark/aazex127:0, :2-9 | m40.rune_p ... rune_d, stair_plaque, crypt_sign | A3 (A7 wires) |
| "It was an illusion! An angry voice booms: \"No one steals from ME!\"" | dark/aazex127:14 | m40.illusion | A3 (A7 wires) |
| New map lines, no source text (listed so the ledger shows every Act VI map line): XD-18 "Sulphur and old smoke on the air. Somewhere far in, something very large is breathing." (the arrival), the ledge's, the starwell's and the library's first looks, "A heavy grate, set deep in the rock behind the dais. It does not move.", "The Dragon King is dead. Behind the dais the grate grinds up into the rock."; FD-03 "Darkstone Tower: black stone, polished like a mirror. Far above, the stair to the Clouds of the Ancients." and the hatch's sealed line; FD-04 the arrival "The Dragon Tower: warm black stone, and somewhere far above, something very large breathing.", the gongs' two lines, the lever's two lines, "The shrine lies broken.", "Its lights blink in an order you cannot follow.", the cores' "... Core Offline", "Climb onto the Dragon Clouds" | ours | XD-18, FD-03, FD-04 (map text; `briefs/<map>/L4/NOTES.md`) | A7 |
| "Descend into Dragon Tower?" | dark/aazex128:0 | X9's way down to FD-04 (exit preset) | A5 |
| "Look into the eye of the Dragon and despair" / "Answer correctly or perish!"; "What is the secret of the Dragon?"; "Die fools!"; "Very good, mortals!" | dark/aazex128:1-5 | the map's prompt; q-f1.eye, eye_wrong | A3 (A5 wires) |
| "Well of Fantastic Skill"; "The water is cool and refreshing." (its +50 Level (temp) as +20 to every statistic until rest, D-59) | dark/aazex128:6-8 | q-f1.well | A3 (A5 wires) |
| "Ancient Book of the Dragon"; "You are unable to understand the strange Dragon Runes."; "You decipher the strange Dragon Runes and are puzzled by the simplicity of the inscription: IN" (FI, NI, TY) | dark/aazex128:9-14 | q-f1.runes_in ... runes_ty (a Linguist reads them) | A3 (A5 wires) |
| "Dragon Power Crystal"; "The power from the Dragon Crystal discharges into your body in a nearly fatal surge. Your body is able to absorb some of the mystic energy." (+3/+4/+5 Levels Perm as 3,000/4,000/5,000 experience once per character, D-59) | dark/aazex128:15-18 | q-f1.crystal_1-3 | A3 (A5 wires) |
| "Mind of the Dragon", "Past of the Dragon", "Future of the Dragon"; the success texts (close, shortened) with "The knowledge is limitless.", "The history is endless.", "The possibilities are unlimited."; the failures (close, made survivable) | dark/aazex128:19-27 | q-f1.ball_mind, ball_past, ball_future (Intellect 60, D-59) | A3 (A5 wires) |

## The Skyroads' corners and the planes (D-58, first part) (A3, nineteenth session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "What do you seek?" | dark/aaze0089:6, aaze0092:8, aazex109:6, aazex112:5 | the four corners' question before m38.corner_* (the source's "Begone, impudent fools!" not used) | A6 (D7's question), A3 |
| "Accept the test of Fire?" (Air, Earth, Water) | dark/aaze0025:6, aaze0026:5, aaze0027:5, aaze0028:5 | the planes' pedestals before m38.test_* | A6, A3 |
| The hazards: "A vent flares!", "Lightning strikes from a clear sky!", "Rocks fall from above!", "A freezing wave breaks over you!" (one time in three, 50 damage: the source's rule) | the planes' maze events (P1-P4 L1 NOTES) | npcs/planes.yml (vent, storm, rockfall, wave) | A3 (A6 wires) |
| "The water is cool and refreshing." (the Tide Pool, and the Ember Font's "The fire is cool and refreshing.", close) | the stock well line | planes.tide_pool, planes.font | A3 (A6 wires) |

## The Skyroads (D-58, the rest) (A3, twentieth session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Fire Zone", "Water Zone", "Air Zone", "Earth Zone" | dark/aaze0089:0, aaze0092:0, aazex109:0, aazex112:0 | the four corners' boards (hover only, D-58 D-7) | A6 |
| "DANGER! Mega Dragon"; "XEEN Skyroad"; "Eat at Joe's"; "Speeding??", "Speeding???"; "Rest Stop"; "Sky Lake" | dark/aaze0090:0, aaze0093:0; aaze0092:1; aaze0091:0, aaze0096:0, aazex100:0; aazex101:0, aazex111:0, aazex112:4, aazex109:1; aazex105:0, aazex108:0; aazex107:0 | the boards (hover only) | A6 |
| The tolls: "Pay us 10,000 gold or else!" (OK. / Or else WHAT?); "You have invaded our territory. Appease us with 10,000 gold or face our wrath!"; "Many apologies, good folks, but this is a robbery. I'm afraid we are going to have to ask you for 10,000 gold."; "Hold! The toll for passing this part of the road is 10,000 gold!" (the answers shortened as buttons, below) | dark/aaze0097:2-3, aazex109:3-4, aazex100:2-3, aaze0092:3-4 | `Xeen.Tolls` (xeen_common.lua); d7.toll_paid, d7.toll_refused | A3 (A6 wires) |
| The four riddles: "Between Fire and Air I constantly travel, a simple clue to unravel. What's my cargo?" (smoke; Air and Earth: dust; Fire and Water: steam; Water and Earth: mud), "Correct.", "Wrong.", "You know my cargo is Smoke. Please be on your way." (Dust, Steam, Mud) | dark/aaze0090:4-10, aaze0097:4-10, aazex104:4-10, aazex110:0-6 | `Xeen.Merchants`; d7.merchant_* | A3 (A6 wires) |
| The genies: "(yawn) The people before you used up two wishes. There's one left. Take your pick."; "Thank you for releasing me. I like you, and I will grant you one wish."; "What took you so long? I've been stuck in that little lamp for 2000 years. ... You can give up your life or the lives of your friends. What will it be?" ("You have 10 seconds to make up your mind." dropped: no timer); "Die selfish scum!"; "Your throne awaits!" | dark/aaze0093:11-14, aazex105:11-14, aaze0099:2-6 | `Xeen.GenieLamps` d7_*; q-d27.angry_* | A3 (A6 wires) |
| The bottles: "Evil Genies NEVER let their victims off the hook. They will always kill someone."; "The test of the elements is merely difficult, not impossible."; "Help! I'm stranded on an air island ..." (the places changed, below) | dark/aazex103:1-2, aazex107:2-3 | d7.bottle_* | A3 (A6 wires) |
| The scarab sellers: Rahib "I have the best possible Fire scarab available, just 8 gems. Would you like to purchase it?"; Wardoz the Blue "What would you pay for a powerful scarab that will protect you from electricity? ..."; Clara the Cold "I sell scarabs that protect against cold. Buy it for 8 gems or begone."; Dorion the Energy Merchant "Will you buy my Kinetic Scarab for 16 gems? Guaranteed..." (the prices changed, below) | dark/aazex107:4-11 | d7.scarab_* (the map asks the question) | A3 (A6 wires) |
| The hatches: "Descend into Ellinger's Tower?", "Descend into Castle Kalindra?", "Enter West Tower?", "Descend into the South Tower?", "Descend to the East Tower?", "Descend to the North Tower?", "Descend to Castle Blackfang?" (then "Bolted from below."); "Enter the Pyramid?" | dark/aaze0092:5-6, aaze0091:1, aazex104:0, aazex111:4, aazex101:4, aazex109:5; aazex102:0 | d7.hatch_*, d7.pyramid_door | A3 (A6 wires) |
| "Descend to Castle Alamar?"; "The door is locked. Scratched on the surface are some words: The Megadragon has the key!" | dark/aaze0089:4-5 | q-d26.hatch | A3 (A6 wires) |
| "Descend to the Darkness Below?", "Pull up the rope?", "Bucket o' Darkness" | dark/aaze0091:5-7, aaze0095:0-1 | the rope's head (D7) and foot (D1) | A6 |

## DD-15, DD-17 and DD-08 (D-61: the Great Pyramid, Castle Alamar, the Northern Tower) (A3, twenty-second session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| The welcome, torch and history statues ("Welcome to the Royal Pyramid! The Dragon Pharoah is currently indisposed ...", "Don't forget to light four torches before trying the stairs.", "Built during the Creation, the Royal Dragon Pyramid has stood the test of time ...") | dark/aaze0083:6, :7 (six torches made four), :8 | m28.welcome_statue, torch_statue, history_statue | A3 (A8 wires) |
| "Enter the eight numbers to pass the test / They are in a row, so do your best."; "They total fifty-two / the rest is up to you." | dark/aaze0083:9-10 | m28.rule_statue_1, _2 | A3 (A8 wires) |
| The eight niches ("I'm the smallest. What's my number?" ... "I'm the largest. What's my number?", 3/Three ... 10/Ten), "Wrong!", "Correct!" | dark/aaze0083:13-38, :16-17 | Xeen.pyramidNiche (m28.niches) | A3 (A8 wires) |
| "Access denied!" (the stair door); "The lever is stuck." | dark/aaze0083:12, :39 | m28.stair_door; the lit torches (A8) | A3, A8 |
| "As you approach the Brew of Pure Power, the Dragon Pharaoh says, "Get away from that! You'll hurt yourself!"" | dark/aaze0086:0 | m28.brew (then brew_drink: "He did warn you.", ours) | A3 (A8 wires) |
| "Enter Combination. ... Left?" / "Right?" / "Left?" (20, 30, 1), "No Luck." | dark/aaze0086:19-29 | Xeen.pharaohSafe (m28.safe) | A3 (A8 wires) |
| "Access Denied!" | dark/aaze0086:5 | d7.sky_door_dd15 (before m30.done) | A3 (A8 wires) |
| The Prime Directive book ("The book is blank but for a single page in the middle that reads: Prime Directive: Obey the Ancients, Secondary Directive: Protect Xeen, Tertiary Directive: Complete the Destiny of Xeen."), "You learn nothing new from reading the book again." | dark/aaze0086:30 (without its +1,000,000 experience), :31 | m28.prime_directive | A3 (A8 wires) |
| "The Head speaks: "Fire power field operational." Shut the field down?" (Air, Water, Earth) | dark/aaze0049:7-10 and m33.head_*'s question, joined into one Yes/No prompt (D-66 item 5) | the Lava Heads while they run (A8); m33.head_* after | A8 |
| "The time is right. What is Alamar's true name?" | dark/aaze0050:19, whole, as the gate's typed prompt (D-66 item 5; no message before it) | Castle Alamar's true-name gate (m33.true_name_gate) | A8 |
| "Fire Time", "Air Time", "Earth Time", "Water Time", "The sundial reads N. Turn?" | dark/aaze0050:1-16 | Xeen.alamarSundial (the dial lines at nine are ours, D-61) | A3 |
| "XEEN Power Juice" | dark/aaze0051:0 (its "+5 levels (permanent)." dropped, :1) | m33.power_juice | A3 (A8 wires) |
| The seven books ("The book is blank but for one page with the letters: "Lt slpng dgs l" So say the Voweless Knights." ...), "A blank line underneath awaits your answer.", "The book slams shut in disgust...your answer must have been wrong.", the proverbs and their vowels | dark/aaze0069:8-12, :18-20; aaze0070:2-6, :11-12; aaze0071:2-8, :14-16 (their +500,000 experience lines not used) | Xeen.vowelessBook, q-d17.book_*, book_wrong | A3 (A8 wires) |
| "Very Good! Lv Lng nd prspr!"; "Have you learned nothing of the Voweless Knights? Begone!"; "That's not why you are here! Study your lessons."; the answers "aie" and "Chalice" | dark/aaze0072:5, :6, :7, :3-4 | q-d17.voice, voice_wrong, voice_other | A3 (A8 asks aaze0072:2) |
| "You feel depressed.", "You feel confused.", "You feel heart broken.", "You feel insane."; "It feels so good!"; "You're not worthy!"; "You feel euphoric!" | dark/aaze0072:21-24, :11, :12, :25 (its "+2 Levels (perm). +5 to all 7 Stats (perm)." rescaled to +1 to all seven, D-61 Q26) | q-d17.throne_*, euphoria, unworthy, dunce | A3 (A8 wires) |

## DD-25, DD-21, DD-10C and DD-22 (D-62: Bosco's Hall, the Necropolis Sewer, the north pocket, Sheltem's Pod) (A3, twenty-second session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Bosco / The Dwarf King" | dark/aaze0013:13 | Bosco's name and title (towns/dd25.yml) | A4 |
| The seer and the Chalice ("Recently, my tribal seer told me I will die by imbibing a poison drink ..."); "Please get the Chalice. I live in fear for my life."; "Oh, thank the Gods! You have the Chalice. For saving my life, I dub thee royal taste tester and give you this treasure." | dark/aaze0013:14-16 (its "+1,000,000 experience." is 14,000) | q-d17 Bosco's Chalice topic | A3 |
| "Ah, the taste testers! Please, please, sit down and drink with me for awhile! My halls will always be open to you." | dark/aaze0013:17 | Bosco's later greeting 5407 (`greet_after`, A4), set by q-d17's hand-in (`evt.SetNPCGreeting(5401, 5407)`) | A4, A3 |
| "Sandro / the Lich"; "... And now my hunger for the living compels me to attack you." | dark/aaze0035:25, the last sentence of :26 | q-d23.first_entry | A3 (A8 wires) |
| "Don't even THINK about taking my statuette!" | dark/aaze0035:29 | q-d23.grille (before the release) | A3 (A8 wires) |
| "Descend to the sewer?" | dark/aaze0035:17 | D6's crypt door (optional) | A6 |
| "Barrel", "A sign on the barrel says: Food for the dead, keep warm."; "You are not strong enough to pry the lid off the barrel."; "Dead Food" | dark/aaze0036:4-5, :7-8 | q-d23.barrel_sign, dead_food | A3 (A8 wires) |
| "The strange alien device seems to be dormant."; "Exit Escape Pod 2?"; "Phaser Control. / Photon Control. A status indicator on the weapon shows it to be disarmed. Fire anyway?"; "Main Console. / Scanning Console. The computer seems to be malfunctioning." | dark/aaze0088:0-3, :5-6 | DD-22's devices and consoles (A8); dd22.weapons ("Nothing happens.") | A8, A3 |
| Sheltem's log, six pages abridged ("Memory core retrieval error ... data integrity 67.3%", "My first directive is to obey the Ancients ...", "WORDS CANNOT EXPRESS HOW ANGRY THAT MAKES ME!", "P.S. My impersonation of King Alamar is working well. No one suspects, not even Corak.", "My cover is ruined!", "I HAVE RETURNED TO TERRA!", "Corak has somehow put his head back on his shoulders and is ... stalking me.", "Rage boils within me.", "My stasis generator will protect me ... Mostly.", "Corak's escape pod landed in lava and is stuck there. How sad.", "I must leave this escape pod to conquer Xeen and find a way to return to Terra.") | dark/aaze0088:4, :7-17 | dd22.log_page_1 ... log_page_6 (the sixth adds the autonote "Sheltem's log", 4139) | A3 (A8 wires) |

## DD-26 (D-65: the Olympus Sewer, Q-D28 Cyrano's Tribble) (A3, twenty-fourth session, 2026-11-21)

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Drain"; "You find a piece of a note that reads: TR" / "IB" / "BL" / "ES" | dark/aaze0038:0-4 | q-d28.drain_tr ... drain_es (once each; "Drain" after, on the status line; the hover "Drain"); the fourth piece adds the autonote "The tribble note" (4680) | A3 (A8 wires) |
| "A disembodied voice booms, \"What's the password?\""; "tribbles", "tribble"; "Wrong! You may not pass!"; "Correct! You may pass." | dark/aaze0038:5-9 | the tribble door: `Xeen.tribbleDoor` asks :5 as the typed prompt's own text (D-65 change 2), takes :6 or :7 in any case; q-d28.tribble_wrong, q-d28.tribble_door (117805) | A3 (A8 wires) |
| "Scroll"; "Search the drains." | dark/aaze0038:10-11 | the pinned scroll by the stair: its hover and q-d28.scroll (D-65 change 1) | A8, A3 |
| "Cyrano sells the password." | dark/aaze0038:12 | the den's map door (D-65 Q57) | A8 |
| "Cyrano Jones / the Salesman" | dark/aaze0038:13 | npc 5614's name and title, "Salesman" (D-21 drops "the"; towns/dd26.yml) | A4 |
| "How would you like one of these little furry creatures? They make great companions and they are only 25,000 gold. What do you say?" | dark/aaze0038:14 (100,000 rescaled, D-65 Q58) | q-d28 Cyrano's Tribbles topic: its typed question (`ask:`) | A3 |
| "You know TRIBBLES are great companions but you'll be surprised what doors they can open for you!" | dark/aaze0038:15 | q-d28 Cyrano's Companions topic, after the first sale (`bought`, 113560) | A3 |
| "Bed"; "Nothing here." | dark/aaze0038:16-17 | Cyrano's bed: its hover and q-d28.bed's after-line (the first search gives one treasure-6 item) | A8, A3 |
| "Maybe some other time." | dark/aaze0038:18 | q-d28 Tribbles: any answer but yes, or too little gold | A3 |
| "Pets Unlimited" | dark/aaze0038:19 | house 4815's name (towns/dd26.yml) and the sign over Cyrano's counter | A4, A8 |
| "Descend into the sewer?" | dark/aaze0037:1 | D7's marble grate (q-d28.sewer_grate's question; A6 at DD-26's install) | A6 |

## Outdoor prompts (D-72: entering a dungeon from an outdoor map; A3, twenty-seventh session, 2026-11-21)

Each joined prompt is one Yes/No button prompt whose own text is the look followed by the source question, with no
message before it (A5's twenty-second session; the source's double spaces after a full stop made single).

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "Castle Basenji. Enter?", joined: "Black oak doors under a pointed arch. Somewhere inside, a dog howls, then a man. Castle Basenji. Enter?" | xeen/aaze0001:19 | X6 83 (Castle Basenji's door) | A5 |
| "Enter the War Zone?", joined: "An iron-bound gate cut into the cliff. Beyond it a crowd roars, and something roars back. Enter the War Zone?" | xeen/aaze0006:4 | X6 80 (the War Zone's gate) | A5 |
| "Shrine of Energy. Pray?", joined: "A pedestal crackling with blue sparks under an open roof. Shrine of Energy. Pray?" | xeen/aaze0001:0 | X6 40 (the Shrine of Energy) | A5 |
| "Enter the Volcano Cave?", joined: "A cave mouth breathing heat between a demon and a devil carved in black rock. Enter the Volcano Cave?" | xeen/aaze0017:1 | X7 38 (the Volcano Cave's mouth) | A5 |
| "The Dragon Cave smells pretty bad. Are you sure you wish to enter?", joined: "Scorched rock, gnawed bones, and a smell of sulphur. The Dragon Cave smells pretty bad. Are you sure you wish to enter?" | xeen/aaze0017:0 | X7 40 (door:xd18) | A5 |
| "You have found an Orc Outpost. Put it to the torch?", joined: "Hides stretched on poles round a fire pit, bones and filth everywhere. You have found an Orc Outpost. Put it to the torch?" | xeen/aaze0018:3 | X7 22 (the orc outpost) | A5 |
| "Enter Strange Craft?" | dark/aaze0005:2; dark/aaze0006:17 | not used: the pod hooks' opening lines (m29.pod_door, d6.sheltem_hatch) replace it, and the hatches enter at once (D-72) | A6, A3 |
| "Enter the Mine?" | dark/aaze0006:1 | D6 95 (the adit), its Yes/No buttons at D6's next rebuild (D-72) | A6 |
| "Enter Castle Xeen?" | xeen/aaze0027:40 | not shown; the gate enters at once (D-72) | A5 |

## Books

| Line | Ref | Where | Owner |
| --- | --- | --- | --- |
| "The World of Xeen on 30 gold a day", "by Eerie the Cartographer", "There is much to see in the World of Xeen.", "a traveller wishing to follow in my footsteps should expect to spend around thirty gold pieces per day on living expenses", "Xeen, while beautiful, can be deadly." | dark/aaze2121:5 | Eeried's guide, Cloudside volume (npcs/books.yml) | A3 |

## Lines the source gives that we change

| Source | Ours | Why |
| --- | --- | --- |
| The statues teach Cure Poison and Cure Disease (xeen/aaze0023:20-21); Barok teaches Enchant Item (xeen/aaze0030:36); Ligono Recharge Item (xeen/aaze0015:14) | the spell's book | no event teaches a spell in OpenYAMM (decision of 2026-11-20, O) |
| The arrival messages of XD-06, XD-12, XD-21, XD-27 (A8's stand-ins told the quests) | short arrival lines (`m10.yak_arrival`, `m21.arrival`, `q-c3.arrival`, `q-c23.arrival`); the quests are told by their givers | house dialogue exists now |
| "+ 60,000 experience" (Valia), "+ 50,000 experience" (Gunther), "+ 20,000" (Orothin) | 8,000 / 1,500 / 1,000 per member | MM6–MM8 sized rewards (QUESTS rules) |
| Ebenezer sells the land for 50,000 gold (xeen/aaze0012:1) | 12,000 | QUESTS M8 (MM6-MM8 never ask more of a level 10-15 party) |
| The Cave of Illusion's skull wants 300 gems for the key (xeen/aaze0045:48) | 10 gems | MM6-MM8 parties carry a handful of gems |
| Carlawna teaches Moon Ray, Falagar Megavolts (xeen/aaze0010:11, :17) | an item of treasure level 3 each | no event teaches a spell |
| "Master of Golems": + 1 level (xeen/aaze0081:9) | the award and 3,000 experience | no permanent levels (QUESTS rules) |
| Rosebud as a password (xeen/aaze0051:4, :14-17) | Rosebud whispers his name; the door takes a key | the user's playtest, 2026-11-13 |
| The dragon tax's Loremaster titles, 50k-500k experience each (xeen research, Dragon Cave) | 2,000 experience and the title | QUESTS rules |
| Luna's Griffin statuette in Sandro's alcove (Necropolis sewer) | in the Eastern Tower's L2 (DD-07) | D-9.3: Q-D20 in Act IV |
| "the Sceptor of Temporal Distortion" (the shrine's refusal, dark/aazex129:13) | "the Scepter of Temporal Distortion" | the item's name (A2's row); the boards keep the source's "Planets Edge" (D-56) |
| Darkstone's crossword clue "42 Down: Tower located in Troll Forest" (Darkstone; dark/aazex121:92-93) | "45 Down: City of Ghosts" (Winterkill) | Darkstone stands in X5's frozen mere, not the Troll Forest (D-57 Q25) |
| "The eye of the Dragon holds the Silver Key Card." (dark/aazex119:6) | "... holds the Elder Staff." | Q-F1's reward is an existing artifact (D-57 Q36) |
| The masks' 2,000,000 and 1,000,000 gold; the crossword's +5 levels, the shrines' 1M/2M/5M, the machine's 5M, the code's 5M, Alister's 1M, the Tome's 10M experience (dark/aazex121-125) | 2,000 and 500 gold; 6,000; 1,000/2,000/3,000; 10,000; 2,000; 5,000; 4,000 once per character | D-57 Q9, Q32 |
| The Shrine of Ultimate Evil kills the party; the crystal balls kill a member too weak of mind (dark/aazex122:12, aazex128:22, :24, :26) | Fire damage and the throw-out to X7; damage and Weak | never lethal (D-4, D-57 Q26, D-59) |
| The XD-18 titles of Wyverns and Wyrms (A3's earlier awards 431, 433) | the source's Lizards, Serpents, Drakes | the source's own titles |
| The sky bandits' answers ("1) Yes...Sir. Here is our gold. Please let us go. 2) En Guarde!" ...) | short buttons: "OK." / "Or else WHAT?", "Take our money" / "Bow down before us!", "Here you are" / "We must decline", "Here you go" / "Draw steel, knave!" | dialogue buttons hold a few words |
| The merchants' "+250,000 experience" (dark/aaze0090:9 ...) | 1,000 per member | MM6-MM8 sized, Act VI's budget |
| The genies' "2 million experience / 200,000 gold / 2,000 gems" (dark/aaze0093:14, aazex105:14) | Q-D27's wishes: 2,000 / 10,000 / ten gems | D-53 |
| The angry genie kills the one who answers (dark/aaze0099:4-7) | the volunteer struck unconscious (+500 experience), the selfish one cursed and weak, the would-be king turned to stone | never lethal (D-4) |
| "Help! I'm stranded on an air island in A2 at 12,14." / "in C3 at 7,0." (dark/aazex107:2-3) | "off the West Lookout" / "past the genie's rock, south of the old launch" | OpenYAMM shows no map squares; the islands are where D7's plan put them |
| The scarabs' 300, 300, 300 and 600 gems; Wardoz's "100 gems? 200?" (dark/aazex107:5, :7, :9, :11) | 8, 8, 8 and 16 gems; "3 gems? 5?"; no scarab item, +10 to a resistance for good, once per character | A2's gem ledger, the source's 1:1:1:2; D-58 Q5 |
| The Prime Directive's "+1,000,000 experience." (dark/aaze0086:30) | the book's text only | no experience is added (D-61 Q8) |
| The Power Juice's "+5 levels (permanent)." (dark/aaze0051:1) | +2 Might once per character | D-61 Q19 (the most-experience line stays under 1.15) |
| The Voweless books' "+500,000 experience" each (dark/aaze0069:21-22, aaze0070:13-14, aaze0071:17-19) | +1 to a different statistic each, once per character, every member present | D-61 Q25 |
| The Euphoria Throne's "+2 Levels (perm). +5 to all 7 Stats (perm)." (dark/aaze0072:25) | +1 to all seven, once per character | D-61 Q26 |
| "Don't forget to light six torches before trying the stairs." (dark/aaze0083:7) | "... four torches ..." | DD-15 has four torches (D-61 Q2) |
| Sandro's "Though you have defeated me once in combat, I still am not dead. Once again you must defeat me, or die." (dark/aaze0035:27) | "You have beaten me once, and it changed nothing. Bring the heart." | Sandro is fought once; the risen Sandro talks (D-62 Q41) |
| "Eating the Food of the Dead gives you 1 level (permanent)." (dark/aaze0036:9) | +2 Endurance, once per character, every member present | D-62 Q43 (quest experience is closed) |
| Cyrano's tribble "only 100,000 gold" (dark/aaze0038:14) | "only 25,000 gold" | D-65 Q58: D7's tolls are 10,000; 25,000 is two and a half tolls and five times the Tribble's value |
