# Brackenford MM8 town reuse inventory

New numeric IDs own local house/NPC state. Original NPCs, dialogue text and service rules remain unchanged.

| Building | House instance / source | MM8 proprietor or resident | Topics / service |
| --- | --- | --- | --- |
| stables | 12000 ← 452 | Wayland | Stables |
| weapon_shop | 12001 ← 2 | Reaver | Weapon Shop |
| armor_shop | 12002 ← 37 | Walvis | Armor Shop |
| magic_shop | 12003 ← 77 | Jed | Magic Shop |
| civic_hall | 12004 ← 773 | Myles Greydawn (NPC 12000 ← 245) | 664: Ogres and Bandits |
| tavern | 12005 ← 229 | Kessel | Tavern |
| temple | 12006 ← 304 | Maricia | Temple |
| training | 12007 ← 1568 | Lehava | Training |
| alchemist | 12008 ← 111 | Tristan | Alchemist |
| teacher_1 | 12009 ← 538 | Jaycin Cardron (NPC 12001 ← 113) | 304: Master Sword |
| teacher_2 | 12010 ← 556 | Gregory Mist (NPC 12002 ← 149) | 343: Master Water Magic |
| teacher_3 | 12011 ← 518 | Kelli Lightfingers (NPC 12003 ← 182) | 394: Master Disarm Trap |
| teacher_4 | 12012 ← 593 | Helga Steeleye (NPC 12004 ← 185) | 388: Master Perception |
| resident_1 | 12013 ← 888 | Ethan Hillsman (NPC 12005 ← 247) | 661: Pirate Raids |
| resident_2 | 12014 ← 814 | Holden (NPC 12006 ← 248) | 662: Regnans, 671: Ore Traders |
| resident_3 | 12015 ← 777 | Karlin Ivers (NPC 12007 ← 249) | 663: Empire of the Endless Ocean, 662: Regnans |
| resident_4 | 12016 ← 886 | Thomas Laraselle (NPC 12008 ← 253) | 666: Smugglers |
| resident_5 | 12017 ← 525 | Asael Fromago (NPC 12009 ← 254) | 655: Vori Cheese Masters |
| resident_6 | 12018 ← 621 | Davee Sail (NPC 12010 ← 315) | 718: The Easy Life |
| warehouse_1 | 12019 ← 557 | Heather Goblinreaver (NPC 12011 ← 242) | 671: Ore Traders |
| warehouse_2 | 12020 ← 539 | Isram Delver (NPC 12012 ← 230) | 674: Other Dragons |
| residence_7 | 12021 ← 824 | Aznog Black (NPC 12013 ← 221) | 677: The Destroyer |
| residence_8 | 12022 ← 675 | Mortie Bith (NPC 12014 ← 220) | 678: Temple of Eep |
| residence_9 | 12023 ← 608 | Yoel Wargreen (NPC 12015 ← 319) | 722: Hidden Treasure |
| well_lane_cottage | 12024 ← 799 | Elsie Apple (NPC 12016 ← 217) | 676: The Destroyer |
| court_west_long | 12025 ← 844 | Jillian Applebee (NPC 12017 ← 218) | 679: Cheese |
| court_west_small | 12026 ← 541 | Chadric Benson (NPC 12018 ← 219) | 675: Dragon on Regna |
| court_south_long | 12027 ← 558 | Benjamin Greenstorm (NPC 12019 ← 243) | 669: Sea of Fire |
| court_east_small | 12028 ← 559 | Julian Greensward (NPC 12020 ← 244) | 670: Find us a home! |

The JSON inventory records exact portrait, greeting, topic, video and source-table provenance.
Four teachers cover Master Sword, Master Water Magic, Master Disarm Trap and Master Perception.
The civic hall uses the MM8 Merchant Guildhouse presentation and Myles Greydawn’s existing Ogres and Bandits topic.
Content-only placement revisions use quick native binding/registry checks and visual review. Re-run focused runtime checks when behavior changes.
