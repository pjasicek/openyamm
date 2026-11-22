# Xeen entrance lines: draft `trans.txt` rows

**D-89 (A3 session 34, 2026-11-22):** XD-04, XD-06, XD-08, XD-09, XD-11, XD-15, DD-02, DD-06, DD-07, DD-08, DD-09, DD-12, DD-15 and Sandcaster no longer lock their outer doors; rows 4, 6, 8, 9 and 15 were rewritten without the retired keys, and the other rows that quote a lock line (XD-11, DD-08, DD-12, DD-15) should drop it when A1's format lands. The one-time unlock lines of those doors are gone too.

DRAFT, 2026-11-21. Xeen's rows for A1's world `trans.txt` contribution (D-90 point 4, `reviews/D90_DECISION.md`):
the line the MM6–MM8 entrance window shows in place of "Do you wish to enter X?". Ids are placeholders,
`XEEN_TRANS_BASE + n`, until A1 declares the world's id range and the row format. Texts are English, one or two
sentences, double spaces removed, in the world's deadpan voice (WORLD_DESIGN §1). An empty text means no row: the
engine falls back to "Do you wish to enter X?".

Sources: `xeen/aazeNNNN:i` and `dark/aazeNNNN:i` are `reference/mm4_5_world_of_xeen/unpacked/text/` strings
(ORIGINAL_LINES.md cites most of them). The MM4/MM5 entrance prompts are almost all bare questions ("Enter Mine?",
"Descend to the sewer?"), which the fallback already says, so most rows build on the map's own look instead:
"current map prompt" is the look in today's Yes/No question; "current map text" is a door's own message or hook line
(its locked or opening text, `xeen_quests.lua`); "new" has no source line. Events are `stem evt:<name> (id)`.
Shortcuts opened from inside (culverts, shafts, grates, back gates) get no row; they are named under the row so the
map lanes know they move without a text (`screen: none` or the fallback, A1's call).

| n | Dungeon | Entered by | Proposed text | Source | Current prompt or flavour |
| --- | --- | --- | --- | --- | --- |
| 1 | XD-01 Joe's Warehouse | x1 thing:warehouse_door (69). No row: x1 thing:culvert_grate (70, barred from inside) | A warehouse with a sign on the door: KEEP OUT. THIS MEANS YOU, GUNTHER. | current map text (m2.warehouse_door, locked) | none |
| 2 | XD-02 Red Dwarf Mines | x1 thing:mine_portal (71). No row: x4 thing:xd02_adit (117, cleared from inside); xd03 exit_cart (25, the Deep Line back up) | A dwarf adit propped with red-painted timbers. Somewhere below, a pick rings on stone and a dwarf swears. | new | none; exit_cart status "You climb into a cart and haul on the brake rope: the Deep Line carries you back up to the Red Dwarf Mines." |
| 3 | XD-03 Deep Mine | xd02 exit_deep (20), deep_cart (47). No row: x1 thing:shaft_head (72, barred from below) | The cart runs down the Deep Line into the dark. | current map text (xd02 status) | status "The cart runs down the Deep Line into the dark." |
| 4 | XD-04 Witch Tower | x1 thing:witch_tower_door (73) | A crooked tower on its rise. The witches fear nothing, and lock nothing. Something inside is bubbling. | new | none (locked: "The door is locked with crystal. Old Valia of Toad Meadow keeps the key.") |
| 5 | XD-05 Orc Caves | x1 thing:orc_cave_mouth (74). No row: x7 thing:xd05_gate (41, barred from within) | A cave mouth reeking of smoke and orc. The bones outside are not all animal. | new | none |
| 6 | XD-06 Temple of Yak | x2 door:thing:yak_temple (98) | The Temple of Yak. Incense, old stone, and something underneath that the incense is there to hide. | current map text (x2 98) | message, same text plus "The clerics within open to no one who does not carry the Yak Stone." |
| 7 | XD-07 Castle Burlock | x4 thing:castle_gate (180) | Castle Burlock, the King's seat. The banners are clean, and the guards are not smiling. | new (source "Enter Castle Burlock?", xeen/aaze0014:7, is the bare question) | none |
| 8 | XD-08 Tomb of a Thousand Terrors | x3 thing:tomb (85) | A tomb half sunk in the lagoon. Insanity is its fame, they say, and undead its game. | current map text (m10.tomb_door) | none (its welcome plaque, xeen/aaze0080:0, stays inside) |
| 9 | XD-09 Golem Dungeon | x5 thing:xd09_door (92) | A stone door in the tundra. Something heavy walks about inside. | current map text (m10.golem_door) + new | none |
| 10 | XD-10 Cave of Illusion | x5 thing:xd10_north (91), thing:xd10_south (110) | The Cave of Illusion. It may or may not be there. | new (source "Enter the Cave of Illusion?", xeen/aaze0007:15, aaze0008:5, bare) | none |
| 11 | XD-11 Tower of High Magic | x3 door:thing:high_magic (38) | The Tower of High Magic. Where the lock should be there is only a faint shimmer. | current map text (m13.tower_door) | none |
| 12 | XD-12 Darzog's Tower | x2 door:thing:darzog_tower (96) | Darzog's Tower. The door is black iron without a handle, and a keyhole shaped like a skull. | current map text (x2 96) | message, same text (locked); m21.arrival's long line inside |
| 13 | XD-13 Newcastle Keep | x3 thing:xd13_stair (81) | A stair down into the foundations of Newcastle. Your foundations, now. | new | none (before the purchase: "CROWN LAND. FOR SALE. ENQUIRE AT EBENEZER'S TENT.") |
| 14 | XD-14 Castle Basenji | x6 door:thing:castle_basenji (83) | Black oak doors under a pointed arch. Somewhere inside, a dog howls, then a man. Castle Basenji. | current map prompt; xeen/aaze0001:19 | Yes/No "Black oak doors under a pointed arch. Somewhere inside, a dog howls, then a man. Castle Basenji. Enter?" |
| 15 | XD-15 The Sphinx | x6 door:thing:northern_sphinx (81) | A door of sandstone between two paws the size of houses. The Sphinx asks its own name. | current map text (q-c9.door) | opening status "The amulet grows warm, and the stone between the paws slides aside." |
| 16 | XD-16 Volcano Cave | x7 thing:xd16_mouth (38); xd17 throat (20, Shangri-La's way out) | A cave mouth breathing heat between a demon and a devil carved in black rock. | current map prompt; xeen/aaze0017:1 | Yes/No "... carved in black rock. Enter the Volcano Cave?" |
| 17 | XD-17 Shangri-La | x7 thing:xd17_cleft (39); xd16 way_end (33) | Cool air and a smell of grass come up through the cleft, from a valley that should not be there. | current map text (xd17.cleft) + new | status "The cleft is clear. Cool air and a smell of grass come up from the valley." |
| 18 | XD-18 Dragon Cave | x7 thing:xd18_mouth (40) | Scorched rock, gnawed bones, and a smell of sulphur. The Dragon Cave smells pretty bad. Are you sure you wish to enter? | xeen/aaze0017:0; current map prompt | Yes/No, the same text |
| 19 | XD-19 Castle Xeen | x9 gate_l (16), gate_r (17) | Castle Xeen, sitting on its cloud as if it owned the sky. It does. | new (source "Enter Castle Xeen?", xeen/aaze0027:40, bare, not shown since D-72) | none (no doll: "No one may enter Castle Xeen without a cupie doll!") |
| 20 | XD-20 The Warzone | x6 door:thing:arena_gate (80) | An iron-bound gate cut into the cliff. Beyond it a crowd roars, and something roars back. | current map prompt; xeen/aaze0006:4 | Yes/No "... something roars back. Enter the War Zone?" |
| 21 | XD-21 Robbers' Den | x2 thing:den_door (114) | A hidden door in the riverbank. Hidden, apart from the well-trodden path to it. | new | none |
| 22 | XD-22 Ninja Pagoda | x5 door:thing:pagoda (61) | A pagoda in the snow, dark and silent. Nobody is watching you, very carefully. | new | none |
| 23 | XD-23 Troll Warren | x5 thing:warren (109) | Frozen hides hang across a hole in the snow. Behind them, something snores. | new (after the map's status) | status after the move "You drag the frozen hides aside." |
| 24 | XD-24 Nightshadow Crypt | x3 thing:coffin_open (47) | Count Draco's coffin, open. There are steps where the Count should be. | new | none |
| 25 | XD-25 Asp Undercroft | x4 thing:xd25_stair (99) | A stair under Asp, worn smooth by feet that no longer come back up. | new | none |
| 26 | XD-26 Gargoyle Eyrie | x4 thing:xd26_eyrie (118) | The way up to the Gargoyle Eyrie. The statues on the ledges are all facing your way. | new | none |
| 27 | XD-27 Ogre Lair | x2 thing:ogre_lair (135) | A cave with a boulder rolled aside for a door. Ogres expect no visitors they cannot eat. | new | none |
| 28 | DD-01 Castleview Sewer | d1 thing:dd01_hatch (145). No row: d1 thing:dd01_outfall (222, barred from inside) | An iron hatch over Castleview's sewer. The smell comes up to meet you. | new (source "Descend into the sewers?", dark/aaze0029:0, bare) | none |
| 29 | DD-02 Ellinger's Tower | d1 door:thing:ellinger_tower (102). D7 hatch_dd02 (42) never enters ("Bolted from below.") | Ellinger's Tower. A sign under the knocker reads: "Not now." | current map text (m17.tower_door) | none |
| 30 | DD-03 Castle Kalindra | d1 door:thing:kalindra_gate (123), door:thing:kalindra_gate_restored (254) | Castle Kalindra, back in phase and solid to the touch. Mostly. | new (source "Enter Castle Kalindra?", dark/aaze0004:35, bare) | none (out of phase: "Castle Kalindra stands on its rise like a reflection in a window. ...") |
| 31 | DD-04 The Gremlin Court | d1 thing:dd04_burrow (170) | A burrow under the wall, with a tiny door and a tiny sign: THE COURT. KNOCK LOUDLY. WE WILL IGNORE YOU. | current map text (q-d1.court_entrance) | message, the same text |
| 32 | DD-05 Western Tower of Mok, door | d1 door:thing:western_tower (118) | The Western Tower, warded from both sides. The heretics inside like it that way. | current map text (q-d6.front_door_outside) + new | message on opening "The key turns and the heretics' wards on the door die with a small, sulky pop." |
| 33 | DD-05 Western Tower of Mok, rope | d1 part:thing:tower_rope/rope (121) | A rope hangs from a window near the tower's top. Nobody looks out of the arrow slits. | current map prompt + text (q-d6.tower_rope) | Yes/No "A rope hangs from a window near the tower's top. Climb?" |
| 34 | DD-06 Southern Tower | d2 door:thing:southern_tower (20) | A brass plate on the door reads NO THIEVES. Under it, scratched: 'ha'. | current map text (q-d19.tower_door) | none |
| 35 | DD-07 Eastern Tower | d3 door:thing:eastern_tower (104) | The Great Eastern Tower. Its lock looks very smug about something. | current map text (q-d18.tower_door) | none |
| 36 | DD-08 Northern Tower | d5 door:thing:northern_tower (28) | The Northern Tower. Over the door: "Grnd rdr f Vwlss Knghts". | current map text (q-d17.tower_door) | message on opening "Bosco's key turns. Over the door: ..." |
| 37 | DD-09 Temple of Bark | d2 door:thing:great_tree (13) | A door in the trunk of the great tree: the Ancient Temple of Bark. | dark/aaze0012:6 (close); current map text (q-d9.bark_door) | none |
| 38 | DD-10A Gemstone Mines, west | d1 thing:dd10a_adit (187) | A timbered adit into the mountain. | current map prompt (d6 95); dark/aaze0006:1 | none |
| 39 | DD-10B Gemstone Mines, east | d2 thing:dd10b_adit (44) | A timbered adit into the mountain. | as row 38 | none |
| 40 | DD-10C Gemstone Mines, north | d6 thing:dd10c_adit (95) | A timbered adit into the mountain. | as row 38 | Yes/No "A timbered adit into the mountain. Enter the Mine?" |
| 41 | DD-11A Troll Holes, first | d2 thing:dd11a_hole (32) | Troll Hole. A rough shaft into the dark, with claw marks for a ladder. | dark/aaze0008:2 + new | status after the move "You let yourselves down into the troll hole." |
| 42 | DD-11B Troll Holes, second | d2 thing:dd11b_hole (33) | as row 41 | dark/aaze0008:3 + new | as row 41 |
| 43 | DD-11C Troll Holes, third | d2 thing:dd11c_hole (34) | as row 41 | dark/aaze0008:4 + new | as row 41 |
| 44 | DD-12 Dungeon of Lost Souls | d4 door:thing:isle_tower (34) | The ruined tower on the Isle of Lost Souls. Two iron-bound leaves, and stairs going down. | dark/aaze0022:0 (name); current map text (m24.isle_door) | status on opening "Megan's key turns, and the two leaves groan apart." |
| 45 | DD-13 Ogre Forts | d2 thing:dd13_west (49), thing:dd13_east (52) | Graalg's fort: a stockade of whole tree trunks, sharpened at both ends. | new | none |
| 46 | DD-14 Castle Blackfang | d4 door:thing:blackfang_gatehouse (41), by griffin. D7 hatch_dd14 (48) never enters | (empty: the griffin's offer is the choice; the flight should be `screen: none`) | none | Yes/No "Hello again, Adventurers. Would you like my griffin to fly you inside?"; on foot "Iron, black, and no handle on this side. ..." |
| 47 | DD-15 Great Pyramid | d5 door:thing:great_pyramid (1). D7 sky_door (105): fallback (its source "Enter the Pyramid?", dark/aazex102:0, is bare) | The Great Pyramid. A door of green stone with the Pharaoh's sign on it. | dark/aaze0014:21 (name); current map text (m28.door) | sky_door Yes/No "Enter the Pyramid?" |
| 48 | DD-16 Corak's Pod | d6 door:thing:corak_pod (42) | A strange craft of curved metal standing in cooled lava. Its hatch is open, as if it had been waiting. | dark/aaze0005:2 (close); current map text (m29.pod_door) | message on opening "The lava round the hatch is black and cool. The hatch slides aside with a sigh, ..." |
| 49 | DD-17 Castle Alamar, gate | d6 door:thing:alamar_gatehouse (33) | Castle Alamar. Every window is lit, and every one of them is looking at you. | current map prompt; dark/aaze0001:0 | Yes/No "Castle Alamar. Every window is lit, and every one of them is looking at you. Enter?" |
| 50 | DD-17 Castle Alamar, roof hatch | d7 hatch_dd17 (49, step 1) | A hatch in the castle roof. Scratched on it: The Megadragon has the key! | dark/aaze0089:5 (close) | Yes/No "Descend to Castle Alamar?" (dark/aaze0089:4) |
| 51 | DD-18 Sandcaster Sewer, lid | d3 thing:dd18_shaft (130) | An iron lid over Sandcaster's sewer. The sand has got in, as it gets into everything here. | new (source "Descend to the sewer?", dark/aaze0031:1, bare) | none |
| 52 | DD-18 Sandcaster Sewer, grate | d5 thing:dd18_grate (86) | An iron grate in the sand, bolted on this side. Beyond it runs a long tunnel. | current map text (dd18.d5_grate) | message "You draw the bolt. The grate swings open on a long tunnel." |
| 53 | DD-19 Wizard Quarter | d3 thing:dd19_gate (124) | The guild gate. Beyond it, the wizard quarter, and wizards who are sensitive to insults. | current map prompt (q-d14.quarter_gate) | message "... sensitive to insults. Enter?" then Yes/No "Enter?" |
| 54 | DD-20 Lakeside Coven and Sewer, back stair | d4 thing:guild_back_stair (49). Not an entrance: the front door's wrong answer (q-d22.guild_wrong) | The guild's back stair, down to the cellars. Members only. | new | non-members: status "A cellar door. The front door asks first." |
| 55 | DD-20 Lakeside Coven and Sewer, shaft | d4 thing:sewer_shaft (50) | A grated shaft down into Lakeside's sewer. | new | Yes/No "Climb down to the sewer?" |
| 56 | DD-21 Necropolis Sewer | d6 door:thing:dd21_crypt (57) | A crypt stair going down. The draught from below smells of drains and old graves. | new | none |
| 57 | DD-22 Sheltem's Pod | d6 door:thing:sheltem_pod (44) | A second strange craft, cold to the touch. Its hatch opens on a red-lit airlock. | dark/aaze0006:17 (close); current map text (d6.sheltem_hatch) | status on opening "With Sheltem gone, the pod's lock has died too. ..." |
| 58 | DD-23 Gargoyle Lair | d4 thing:dd23_lair (74) | A cave in the crag, its mouth white with droppings. Something up there is watching, very still. | current map prompt (q-d15.lair_door) | message "... very still. Enter the cave?" then Yes/No "Enter the cave?" |
| 59 | DD-24 Giants' Hall | d5 thing:giants_hall_doors (40) | Doors three times your height, with a handle you can reach by standing on each other. | new | none |
| 60 | DD-25 Bosco's Hall | d5 thing:bosco_door (85) | Bosco's Hall. The door stands open; Bosco is expecting company, or not worried about it. | new | none |
| 61 | DD-26 Olympus Sewer | d7 sewer_grate (104) | A marble grate in the road of the gods. Even their sewer is marble. | new (source "Descend into the sewer?", dark/aaze0037:1, bare) | Yes/No "Descend into the sewer?" |
| 62 | FD-01 Alamar Depths | d6 thing:fd01_stair (70); d7 hatch_dd17 (49, step 4, after the castle falls) | A stair down under the ruin, where Sheltem's mark has gone out. | current map text (m39.depths_door) | message on opening "The stair under the ruin is sealed with Sheltem's mark. The Cube of Power hums, and the mark goes out." |
| 63 | FD-02 Southern Sphinx | x6 door:thing:southern_sphinx (82) | The Sphinx's stone jaw stands open on a stair. | current map text (m40.sphinx_door) | message on opening "The Sphinx's stone eyes find Roland's amulet. Its jaw opens on a stair." |
| 64 | FD-03 Darkstone Tower | x5 door:thing:darkstone (59); p5 stair_door (38) | A tower of black stone, polished like a mirror. | current map text (m41.tower_door); dark/aazex129:14 is P5's bare "Descend into Darkstone Tower?" | x5 status on opening "The black key turns without a sound. So does the door." |
| 65 | FD-04 Dragon Tower | x7 thing:fd04_gate (66); x9 fd04_door (42) | The Dragon Tower. Two black leaves, warm to the touch, with a keyhole shaped like a dragon's eye. | current map text (q-f1.tower_door); dark/aazex128:0 is X9's bare "Descend into Dragon Tower?" | x7 status on opening "The black key turns with a sound like a sigh. ..." |

Notes for A1 and the lanes:
- Rows 38–40, 41–43 repeat one text per pocket (as MM6's Barrows rows 12–14 do); one shared row also works if A1's
  format allows several events per row.
- Opening lines ("Megan's key turns ...", "The black key turns ...") are one-time unlock messages, not entrance
  flavour; this draft leaves them where they are. The proposed texts drop any "Enter?" question: the window asks.
- Out of scope here: moves out to the open-air BLVs (D7 Skyroads, P1–P5, X8, X9), which are leaves, not entrances.

## Yes/No questions before a move into a BLV

Found by scanning every `-- evt:` block (and the hooks it calls) for `evt.AskQuestion`, `AskChoiceWithAnswerSteps` or
`AskQuestionWithAnswerSteps` together with a `MoveToMap` to a `.blv`: 60 events (13 into a dungeon, 45 out to an
open-air BLV, 2 choices that stay). D-90 counts 44 and does not say how; the lanes should work from this list.
`direct` marks moves written with `{direct = true}` today.

Into a dungeon (13; row n in brackets):
- xeen_d1 part:thing:tower_rope/rope (121) [33]
- xeen_d3 thing:dd19_gate (124) [53]
- xeen_d4 thing:sewer_shaft (50) [55]; thing:dd23_lair (74) [58]
- xeen_d6 door:thing:alamar_gatehouse (33) [49]; thing:dd10c_adit (95) [40]
- xeen_d7 hatch_dd17 (49, direct) [50, 62]; sewer_grate (104, direct) [61]; sky_door (105, direct) [47, fallback]
- xeen_x6 door:thing:arena_gate (80) [20]; door:thing:castle_basenji (83) [14]
- xeen_x7 thing:xd16_mouth (38) [16]; thing:xd18_mouth (40) [18]

Out to an open-air BLV (45, all direct): the leave window's own text or fallback applies.
- xeen_d1 part:thing:grove_rope/rope (117) → D7, "A rope hangs down out of the sky. Climb?"
- xeen_dd06 roof_trapdoor (46), xeen_dd07 roof_trapdoor (44), xeen_dd08 roof (45) → D7, "Climb up through the trapdoor?"
- xeen_dd15 sky_door (67) → D7, "Step out onto the Skyroads?"
- xeen_dd17 hatch (47) → D7, "Climb up through the hatch?"
- xeen_dd26 exit (10) → D7, "Climb up to Olympus?"
- xeen_fd01 ladder (21), ladder_rail_n (40), ladder_rail_s (41), ladder_rung_01 … ladder_rung_16 (42–57): 19 events,
  one ladder → D7, "Climb up through the hatch?"
- xeen_fd03 hatch (16) → P5, "Climb to the Clouds of the Ancients?"
- xeen_fd04 hatch (67) → X9, "Climb up through the hatch?"
- xeen_p1 way_up (10), dais (11), dais_disc (12), way_up_column (18) → D7
- xeen_p2 dais (4), way_up (22), dais_disc (23), way_up_column (28) → D7
- xeen_p3 dais (3), way_up (16), dais_disc (18), way_up_column (23) → D7
- xeen_p4 dais (4), way_up (15), dais_disc (17) → D7
- xeen_xd11 cloud_stair (11) → X8, "Stairway to Heaven. Climb?" / "Climb (Yes/No)?"
- xeen_xd12 cloud_stair → X9, "Climb the cloud stair into the sky?"

Choices that stay (D-90 1(d): a question that is a choice): xeen_d4 door:thing:blackfang_gatehouse (41), the griffin's
offer; xeen_d4 door:building:lk_guild, the riddle (its wrong answer drops the party into DD-20).

Not moves, but the same shape: xeen_d7 hatch_dd02, hatch_dd03, hatch_dd05, hatch_dd06, hatch_dd07, hatch_dd08,
hatch_dd14 (42–48) ask "Descend into ...?" (dark/aaze0092:5-6, aaze0091:1, aazex104:0, aazex111:4, aazex101:4,
aazex109:5) and then say "Bolted from below." They never enter, so they need no row; the lanes may make them status
lines.
