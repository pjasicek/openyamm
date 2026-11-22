# Xeen: music per map (proposal)

A6, 2026-11-20, for the orchestrator to apply to `assets_dev/worlds/xeen/source/maps.yml` (`music`). MM6–MM8 tracks
by number (ROADMAP Q9); new music may come later.

## The tracks there are

`Music/<n>.mp3`, from `assets_dev/worlds/mm8/music` (2–15), `mm7/music` (17–35) and `mm6/music` (37–51). There is no
1, 16 or 36: `map_stats.txt` gives MM8's Mad Necromancer's Lab track 16 and Escaton's Palace track 0, but no file
exists, so neither is used here. What the shipped maps use them for (`map_stats.txt`, column Track):

| Track | Shipped use | Mood used here |
| --: | --- | --- |
| 2 | MM8 tutorial, Escaton's Crystal, Church of Eep | strange, quirky |
| 3 | MM8 Alvar, Plane of Earth, crypts (Vampire Crypt, Korbu) | crypt, earth |
| 6 | MM8 Ironsand, Garrote Gorge, Ravage Roaming | harsh desert |
| 7 | MM8 Plane of Water, Chain of Fire | water plane, fire cave |
| 8 | MM8 Ancient Troll Home | trolls |
| 9 | MM8 Ravenshore, Plane of Air | air plane |
| 10 | MM8 Plane of Fire, Regna | fire plane |
| 11 | MM8 Shadowspire, Necromancers' Guild | the dead |
| 12 | MM8 Druid Circle, Tomb of Lord Brinne | grove, shrine |
| 13 | MM8 Murmurwoods, Ogre Fortress, Dragon Cave | ogres, dragons |
| 15 | MM8 Plane Between Planes | the finale |
| 17 | MM7 Deyja, Bracada Desert | bright desert |
| 18 | 17 MM7 dungeons (Erathian Sewers, Red Dwarf Mines …) | generic dungeon, mines |
| 19 | MM7 Harmondale, Tatalia, Avlee | **Cloudside's start** |
| 20 | MM7 Zokarr's Tomb and the fifteen barrows | tombs |
| 21 | MM7 Evenmorn Island | airy, uncanny |
| 22 | MM7 Castle Gloaming, the Pit | evil castle |
| 25 | MM7 Celeste | sky city |
| 26 | MM7 Mount Nighon | volcano |
| 28 | MM7 temples (Baa, the Moon, Light, Dark, Sun) | temple, coven |
| 29 | MM7 Castle Navan, Castle Gryphonheart | royal castle |
| 30 | MM7 Castle Lambent | light, celestial |
| 31 | MM7 Thunderfist Mountain, Titans' Stronghold, dragon caves | dwarves, giants, mountain halls |
| 32 | MM7 Erathia | **Cloudside's hub** |
| 33 | MM7 Tularean Forest | forest |
| 34 | MM7 School of Sorcery, Markham's Manor, Setag's Tower | towers, wizards |
| 37 | MM6 New Sorpigal, Misty Islands, Bootleg Bay | **Darkside's hub** |
| 39 | MM6 Silver Cove | merchant town |
| 41 | MM6 Hermit's Isle, Blackshire, Dragonsand | gloomy wilds |
| 42 | 31 MM6 dungeons | generic dungeon |
| 43 | MM6 Goblinwatch, Icewind Keep | cold keep, sinister tower |
| 44 | MM6 Abandoned Temple, Free Haven Sewer | sewers, undercrofts |
| 45 | MM6 Arena | arena |
| 46 | MM6 Tomb of VARN, Oracle, Control Center | **the Ancients** |
| 47 | MM6 Kriegspire, Frozen Highlands | snow |
| 48 | MM6 Mire of the Damned | swamp, vampires |
| 49 | MM6 temples and castles (Alamos, Darkmoor) | castle in stages |
| 50 | MM6 Temples of Baa | sinister fortress |
| 51 | MM6 Paradise Valley, Free Haven | paradise |

Each face's hub has a track of its own that no other map in the world uses: Rivercity (X2) **32**, Castleview (D1)
**37**; Vertigo, where the game starts, keeps Harmondale's **19**.

## Per map

The 11 built maps keep their tracks (marked "kept"); none is wrong.

| Map | Track | Why |
| --- | --: | --- |
| X1 Vertigo Meadows | 19 | kept; Harmondale's home-town theme for the start |
| X2 Rivercity and Lake Darzog | 32 | kept; Erathia's city theme, Cloudside's hub |
| X3 Lifeforce Lagoon | 48 | swamp and the vampire town |
| X4 Burlock Savannah | 29 | the royal seat (MM7's royal castles) |
| X5 Winterkill Tundra | 47 | snowfields |
| X6 Desert of the Sphinx | 17 | bright desert (Bracada) |
| X7 Mount Firestone | 26 | volcano (Mount Nighon) |
| X8 Cloudreach | 25 | sky islands (Celeste) |
| X9 Clouds of Xeen | 21 | airy and uncanny, Lord Xeen's sky |
| D1 Castleview Vale | 37 | MM6's town theme, Darkside's hub |
| D2 Sprite Forest and Ogre Pass | 33 | forest |
| D3 Sandcaster and the Aging Forest | 39 | merchant city |
| D4 Lakeside and Blackfang | 41 | gloomy lake and woods |
| D5 Desert of Doom | 6 | harsh desert |
| D6 The Forbidden Zone | 11 | the dead and the ruined waste |
| D7 The Skyroads | 30 | the gods' roads and Olympus |
| P1 Plane of Fire of Xeen | 10 | MM8's Plane of Fire |
| P2 Plane of Air of Xeen | 9 | MM8's Plane of Air |
| P3 Plane of Earth of Xeen | 3 | MM8's Plane of Earth |
| P4 Plane of Water of Xeen | 7 | MM8's Plane of Water |
| P5 Clouds of the Ancients | 15 | the finale (Plane Between Planes) |
| XD-17 Shangri-La | 51 | paradise valley |
| XD-20 The Warzone | 45 | arena |
| DD-25 Bosco's Hall | 31 | dwarf hall |
| XD-01 Joe's Warehouse | 18 | kept |
| XD-02 Red Dwarf Mines | 18 | kept; MM7's Red Dwarf Mines |
| XD-03 Deep Mine | 18 | kept |
| XD-04 Witch Tower | 28 | kept; coven |
| XD-05 Orc Caves | 18 | kept |
| XD-06 Temple of Yak | 28 | kept; temple |
| XD-07 Castle Burlock | 29 | royal castle |
| XD-08 Tomb of a Thousand Terrors | 20 | tomb |
| XD-09 Golem Dungeon | 43 | cold keep in the snow |
| XD-10 Cave of Illusion | 2 | strange |
| XD-11 Tower of High Magic | 34 | wizard's tower |
| XD-12 Darzog's Tower | 22 | kept; evil sorcerer's tower |
| XD-13 Newcastle Keep (staged) | 49 | castle built in stages |
| XD-14 Castle Basenji | 42 | ruined desert castle |
| XD-15 The Sphinx | 46 | Ancient monument |
| XD-16 Volcano Cave | 7 | fire cave (Chain of Fire) |
| XD-18 Dragon Cave | 13 | dragon cave |
| XD-19 Castle Xeen | 22 | the villain's castle |
| XD-21 Robbers' Den | 18 | kept |
| XD-22 Ninja Pagoda | 12 | shrine |
| XD-23 Troll Warren | 8 | trolls |
| XD-24 Nightshadow Crypt | 3 | vampire crypt |
| XD-25 Asp Undercroft | 44 | undercroft |
| XD-26 Gargoyle Eyrie | 31 | mountain halls |
| XD-27 Ogre Lair | 18 | kept |
| DD-01 Castleview Sewer | 44 | sewer |
| DD-02 Ellinger's Tower | 34 | wizard's tower |
| DD-03 Castle Kalindra (staged) | 29 | royal castle |
| DD-04 The Gremlin Court | 2 | quirky |
| DD-05 Western Tower of Mok | 34 | tower |
| DD-06 Southern Tower | 34 | tower |
| DD-07 Eastern Tower | 43 | sinister tower |
| DD-08 Northern Tower | 43 | sinister tower |
| DD-09 Temple of Bark | 12 | grove temple |
| DD-10A Gemstone Mines, west pocket | 18 | mines |
| DD-10B Gemstone Mines, east pocket | 18 | mines |
| DD-10C Gemstone Mines, north pocket | 18 | mines |
| DD-11A Troll Holes, first pocket | 8 | trolls |
| DD-11B Troll Holes, second pocket | 8 | trolls |
| DD-11C Troll Holes, third pocket | 8 | trolls |
| DD-12 Dungeon of Lost Souls | 20 | tomb |
| DD-13 Ogre Forts | 13 | ogres |
| DD-14 Castle Blackfang | 3 | vampire castle |
| DD-15 Great Pyramid | 46 | Ancient |
| DD-16 Corak's Pod | 46 | Ancient |
| DD-17 Castle Alamar | 50 | sinister fortress |
| DD-18 Sandcaster Sewer | 44 | sewer |
| DD-19 Wizard Quarter | 34 | wizards |
| DD-20 Lakeside Coven and Sewer | 28 | coven |
| DD-21 Necropolis Sewer | 11 | the dead |
| DD-22 Sheltem's Pod | 46 | Ancient |
| DD-23 Gargoyle Lair | 31 | mountain halls |
| DD-24 Giants' Hall | 31 | giants (Titans' Stronghold) |
| DD-26 Olympus Sewer | 44 | sewer |
| FD-01 Alamar Depths | 50 | continues Castle Alamar |
| FD-02 Southern Sphinx | 46 | Ancient |
| FD-03 Darkstone Tower | 43 | sinister tower |
| FD-04 Dragon Tower and the Dungeon of Death | 13 | dragons |

## For A1

`GameAudioSystem` plays `Music/<n>.mp3`. In a development root the MM6–MM8 tracks live in those worlds' folders;
a run with `--world xeen` must still find them (and a shipped Xeen package must either depend on them or carry
copies). Worth one check when the world first starts.
