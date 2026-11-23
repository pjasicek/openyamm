# Xeen: music per map

A6, 2026-11-20, applied by the orchestrator to `assets_dev/worlds/xeen/source/maps.yml` (`music`): MM6–MM8 tracks by
number (ROADMAP Q9). Since U-10 (2026-11-22, lane AU) Xeen also has eight themes of its own, tracks 92001–92008 (since U-13 the original MM4/MM5 songs with modern instruments), and
the town districts of six outdoor maps play the town themes (`world.yml` `musicAreas`): [Xeen's own
themes](#the-original-songs-modern-instruments-installed-2026-11-23-u-13). The per-map table below is the current state.

## The tracks there are

Xeen's own 92001–92008 are listed under [Xeen's own themes](#the-original-songs-modern-instruments-installed-2026-11-23-u-13).
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

Before U-10 each face's hub had a track of its own (Rivercity 32, Castleview 37, Vertigo Harmondale's 19); since
U-10 the hubs play the overworld themes on their open land and the town themes inside their districts.

## Per map

A6's first pass kept the 11 maps built then (marked "kept"); U-10 changed 21 rows (marked).

| Map | Track | Why |
| --- | --: | --- |
| X1 Vertigo Meadows | 92001 | Cloudside overworld (U-10; was 19); Vertigo itself 92003 by music area |
| X2 Rivercity and Lake Darzog | 92001 | Cloudside overworld (U-10; was 32); Rivercity 92003 by music area |
| X3 Lifeforce Lagoon | 48 | swamp and the vampire town |
| X4 Burlock Savannah | 92001 | Cloudside overworld (U-10; was 29); the village and castle grounds 92003 by music area |
| X5 Winterkill Tundra | 47 | snowfields |
| X6 Desert of the Sphinx | 17 | bright desert (Bracada) |
| X7 Mount Firestone | 26 | volcano (Mount Nighon) |
| X8 Cloudreach | 25 | sky islands (Celeste) |
| X9 Clouds of Xeen | 21 | airy and uncanny, Lord Xeen's sky |
| D1 Castleview Vale | 92002 | Darkside overworld (U-10; was 37); Castleview 92004 by music area |
| D2 Sprite Forest and Ogre Pass | 92002 | Darkside overworld (U-10; was 33) |
| D3 Sandcaster and the Aging Forest | 92002 | Darkside overworld (U-10; was 39); Sandcaster and the Crossroads 92004 by music area |
| D4 Lakeside and Blackfang | 92002 | Darkside overworld (U-10; was 41); Lakeside 92004 by music area |
| D5 Desert of Doom | 6 | harsh desert |
| D6 The Forbidden Zone | 11 | the dead and the ruined waste |
| D7 The Skyroads | 30 | the gods' roads and Olympus |
| P1 Plane of Fire of Xeen | 10 | MM8's Plane of Fire |
| P2 Plane of Air of Xeen | 9 | MM8's Plane of Air |
| P3 Plane of Earth of Xeen | 3 | MM8's Plane of Earth |
| P4 Plane of Water of Xeen | 7 | MM8's Plane of Water |
| P5 Clouds of the Ancients | 92008 | the finale (U-10; was 15) |
| XD-17 Shangri-La | 51 | paradise valley |
| XD-20 The Warzone | 45 | arena |
| DD-25 Bosco's Hall | 31 | dwarf hall |
| XD-01 Joe's Warehouse | 92006 | dungeon theme (U-10; was 18) |
| XD-02 Red Dwarf Mines | 18 | kept; MM7's Red Dwarf Mines |
| XD-03 Deep Mine | 18 | kept |
| XD-04 Witch Tower | 28 | kept; coven |
| XD-05 Orc Caves | 92006 | dungeon theme (U-10; was 18) |
| XD-06 Temple of Yak | 28 | kept; temple |
| XD-07 Castle Burlock | 92005 | castle theme (U-10; was 29) |
| XD-08 Tomb of a Thousand Terrors | 20 | tomb |
| XD-09 Golem Dungeon | 43 | cold keep in the snow |
| XD-10 Cave of Illusion | 2 | strange |
| XD-11 Tower of High Magic | 34 | wizard's tower |
| XD-12 Darzog's Tower | 22 | kept; evil sorcerer's tower |
| XD-13 Newcastle Keep (staged) | 92005 | castle theme (U-10; was 49) |
| XD-14 Castle Basenji | 92006 | dungeon theme (U-10; was 42) |
| XD-15 The Sphinx | 92007 | the Ancients (U-10; was 46) |
| XD-16 Volcano Cave | 7 | fire cave (Chain of Fire) |
| XD-18 Dragon Cave | 13 | dragon cave |
| XD-19 Castle Xeen | 22 | the villain's castle |
| XD-21 Robbers' Den | 92006 | dungeon theme (U-10; was 18) |
| XD-22 Ninja Pagoda | 12 | shrine |
| XD-23 Troll Warren | 8 | trolls |
| XD-24 Nightshadow Crypt | 3 | vampire crypt |
| XD-25 Asp Undercroft | 44 | undercroft |
| XD-26 Gargoyle Eyrie | 31 | mountain halls |
| XD-27 Ogre Lair | 92006 | dungeon theme (U-10; was 18) |
| DD-01 Castleview Sewer | 44 | sewer |
| DD-02 Ellinger's Tower | 34 | wizard's tower |
| DD-03 Castle Kalindra (staged) | 92005 | castle theme (U-10; was 29) |
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
| DD-15 Great Pyramid | 92007 | the Ancients (U-10; was 46) |
| DD-16 Corak's Pod | 92007 | the Ancients (U-10; was 46) |
| DD-17 Castle Alamar | 50 | sinister fortress |
| DD-18 Sandcaster Sewer | 44 | sewer |
| DD-19 Wizard Quarter | 34 | wizards |
| DD-20 Lakeside Coven and Sewer | 28 | coven |
| DD-21 Necropolis Sewer | 11 | the dead |
| DD-22 Sheltem's Pod | 92007 | the Ancients (U-10; was 46) |
| DD-23 Gargoyle Lair | 31 | mountain halls |
| DD-24 Giants' Hall | 31 | giants (Titans' Stronghold) |
| DD-26 Olympus Sewer | 44 | sewer |
| FD-01 Alamar Depths | 50 | continues Castle Alamar |
| FD-02 Southern Sphinx | 92007 | the Ancients (U-10; was 46) |
| FD-03 Darkstone Tower | 43 | sinister tower |
| FD-04 Dragon Tower and the Dungeon of Death | 13 | dragons |

## For A1

`GameAudioSystem` plays `Music/<n>.mp3`. In a development root the MM6–MM8 tracks live in those worlds' folders;
a run with `--world xeen` must still find them (and a shipped Xeen package must either depend on them or carry
copies). Worth one check when the world first starts.

## The original songs, modern instruments (installed 2026-11-23, U-13)

Since U-13 the eight tracks 92001-92008 are the original Might and Magic IV/V songs: every note from the game's own
`.m` files (`reference/mm4_5_world_of_xeen/unpacked/music/`), the composer's MT-32 velocities and channel volumes and
the percussion track the AdLib never played, rendered with the MuseScore General SoundFont (MIT) through FluidSynth,
with performance, stereo placement, a hall and a seamless loop added. Method, checks and all 55 renders:
`level_generation/sounds/xeen_music_modern_20261123/README.md` (listening page `review/index.html` there). Credits
(the SoundFont's licence asks for them): `worlds/xeen/music/XEEN_MUSIC_CREDITS.md`.

| Track | Theme | Song (`.m`) | Loop |
| --: | --- | --- | --: |
| 92001 | Cloudside overworld | `xeen/outdoors` | 2:36 |
| 92002 | Darkside overworld | `dark/outday1` (the game picks outday1/2/4 at random; 2 and 4 and Dragon Pharaoh's `intro/outday3` are rendered too) | 1:03 |
| 92003 | Cloudside towns | `xeen/town` | 2:19 |
| 92004 | Darkside towns | `dark/newbrigh` (New Bright Town, also Darkside's main menu) | 0:59 |
| 92005 | Castles | `xeen/castle` (the whole 5:20 pass; the game started it at 1:28) | 5:20 |
| 92006 | Dungeons and caves | `xeen/dungeon` (`xeen/cavern` is rendered too) | 2:00 |
| 92007 | The Ancients' places | `dark/sf05` (Darkside's sci-fi places) | 0:49 |
| 92008 | The finale | `xeen/endgame` | 2:27 |

The keys follow the composer's MT-32 recordings, a whole tone above the decoded data. The previous Eleven Music
files are backed up in `output/xeen_music_modern_install/*.pre_modern` and kept in
`level_generation/sounds/xeen_music_20261122/out/`. Checked 2026-11-23: X1 starts 92001 and switches to 92003 in
Vertigo's area (`output/xeen_music_modern_install/runs/x1.out`, `OPENYAMM_AUDIO_TRACE=1`).

## Xeen's own themes (installed 2026-11-22, U-10; replaced by U-13)

Eight themes made with Eleven Music on the user's approval (plan B: one take each, 18 000 credits; one dungeon retake, 2 250): job file, ledger,
picks and review page in `level_generation/sounds/xeen_music_20261122/`; listen on the review page
(https://claude.ai/artifact/Tca95rfncnb6hzGFk7r97K, or `review/index.html` from disk). Each is a seamless loop folded
like Hesper's (5 s crossfade, -17 dBFS RMS target, 320 kbit/s MP3). The user approved the install on 2026-11-22
(U-10); it is applied as written below, with the finale on P5 only. Backups of the files before it:
`output/xeen_music_install/*.pre_music`.

### The tracks

Track numbers 92001–92008 (beside MM9's 90001–90017; MM6–MM8 use 2–51, Hesper's staged world 101–108).

| Track | Theme | File to install | Loop |
| --: | --- | --- | --: |
| 92001 | Cloudside overworld | `out/xeen_music_cloudside/xeen_music_cloudside.mp3` | 2:25 |
| 92002 | Darkside overworld | `out/xeen_music_darkside/xeen_music_darkside.mp3` | 2:21 |
| 92003 | Cloudside towns | `out/xeen_music_cloudside_town/xeen_music_cloudside_town.mp3` | 2:21 |
| 92004 | Darkside towns | `out/xeen_music_darkside_town/xeen_music_darkside_town.mp3` | 2:25 |
| 92005 | Castles | `out/xeen_music_castle/xeen_music_castle.mp3` | 2:22 |
| 92006 | Dungeons and caves | `out/xeen_music_dungeon/xeen_music_dungeon.mp3` (take 2) | 2:22 |
| 92007 | The Ancients' places | `out/xeen_music_ancients/xeen_music_ancients.mp3` | 2:20 |
| 92008 | The finale | `out/xeen_music_finale/xeen_music_finale.mp3` | 2:25 |

The dungeon is take 2 (the user asked for a retake; 2 250 more credits, 20 250 in all): take 1 had a sparse opening
and a last 45 s about 5 dB louder, so its wrap dropped 10–15 dB; take 2 spreads its swells through the track and its
wrap steps down about 3 dB (spread 7.2 dB). The others hold within 2.6–4.5 dB. See `picks.yml` `listening`.

### Per map (the 21 changes, already in the table above; every other map kept its track)

| Map | Now | Proposed | Why |
| --- | --: | --: | --- |
| X1 Vertigo Meadows | 19 | 92001 | Cloudside's green open land; Vertigo itself gets 92003 (music area) |
| X2 Rivercity and Lake Darzog | 32 | 92001 | the river country; Rivercity gets 92003 |
| X4 Burlock Savannah | 29 | 92001 | open savannah; the castle village gets 92003, the castle BLV 92005 |
| D1 Castleview Vale | 37 | 92002 | Darkside's face; Castleview gets 92004 |
| D2 Sprite Forest and Ogre Pass | 33 | 92002 | Darkside's open land |
| D3 Sandcaster and the Aging Forest | 39 | 92002 | Sandcaster and the Crossroads get 92004 |
| D4 Lakeside and Blackfang | 41 | 92002 | Lakeside gets 92004 |
| XD-07 Castle Burlock | 29 | 92005 | royal castle |
| DD-03 Castle Kalindra (staged) | 29 | 92005 | the Queen's castle |
| XD-13 Newcastle Keep (staged) | 49 | 92005 | the party's own castle |
| XD-01 Joe's Warehouse | 18 | 92006 | generic dungeon |
| XD-05 Orc Caves | 18 | 92006 | caves |
| XD-14 Castle Basenji | 42 | 92006 | ruined castle as a dungeon |
| XD-21 Robbers' Den | 18 | 92006 | den |
| XD-27 Ogre Lair | 18 | 92006 | lair |
| XD-15 The Sphinx | 46 | 92007 | Ancient |
| DD-15 Great Pyramid | 46 | 92007 | Ancient |
| DD-16 Corak's Pod | 46 | 92007 | Ancient |
| DD-22 Sheltem's Pod | 46 | 92007 | Ancient |
| FD-02 Southern Sphinx | 46 | 92007 | Ancient |
| P5 Clouds of the Ancients | 15 | 92008 | the finale |

Kept on purpose: the villains' castles (XD-12, XD-19 22; DD-17, FD-01 50; DD-14 3) keep their sinister tracks; the
mines (XD-02, XD-03, DD-10A–C) keep MM7's Red Dwarf Mines track 18, so 92006 does not play on every small dungeon;
sewers 44, towers 34/43, tombs 20, planes, sky maps, the snow, desert, swamp and volcano maps keep theirs. Bosco's
Hall keeps 31 (dwarf hall). After this, 92006 plays on five maps and 18 on five.

### Music areas (world.yml `musicAreas`, installed)

The engine plays another track while the party is inside a rectangle of an outdoor map
(`game/content/ContentManifest.h` `MusicArea`; `GameApplication::updateMusicArea`, the first rectangle holding the
party wins; no hysteresis, so keep the edges in open ground). Rectangles from the L4 sketches' `town:` districts
(`devdocs/xeen/briefs/<map>/L4/sketch.yml`, cell -> world as `tools/xeen/wall_check.py` `cell_to_world`, 512 per
cell); the map lanes should check them against the built towns:

```yaml
musicAreas:
  xeen_x1.odm: [{track: 92003, rect: [-16896, 1024, 3584, 13824]}]      # Vertigo
  xeen_x2.odm: [{track: 92003, rect: [-7168, -2560, 10240, 14848]}]     # Rivercity
  xeen_x4.odm: [{track: 92003, rect: [-4608, 1024, 2560, 10752]}]       # Burlock's village and castle grounds
  xeen_d1.odm: [{track: 92004, rect: [-7168, 0, 6144, 10240]}]          # Castleview
  xeen_d3.odm:
    - {track: 92004, rect: [-18944, 12800, -8704, 22528]}               # Sandcaster
    - {track: 92004, rect: [-4608, 7680, 512, 12800]}                   # the Crossroads market
  xeen_d4.odm: [{track: 92004, rect: [-2048, -16896, 11264, -9216]}]    # Lakeside
```

Not given a town theme: Asp (cursed), Winterkill (ghost town), Nightshadow (vampires), Newcastle (built in stages),
the hamlets and Sprite village (small).

### How a world's own music is referenced

1. **Files**: `assets_dev/worlds/xeen/music/<N>.mp3` (a new folder). Every world's `music/` is mounted at `/music`
   (`AssetFileSystem::mountMergedWorldMusicRoots`, the active world first), and `GameAudioSystem` reads
   `Music/<N>.mp3`. File names must be unique across all world packages unless identical
   (`validateMergedMusicRoots` fails on a conflict), hence 92001+.
2. **Map tracks**: `source/maps.yml` `music:` -> `tools/xeen/gen_maps.py` / `build_world.py` -> `map_stats.txt`
   Redbook column (column 28, any integer: MM9 uses 90001+). The file's comment "MM6-MM8 track number" should say
   "track number (MM6-MM8 2-51, Xeen 92001-92008)".
3. **Areas**: the `musicAreas` block above in `world.yml` (owner: the orchestrator).
4. **Package**: `tools/packaging/packs.yml` gives every world a `music` domain of two buckets, which Xeen inherits
   (no entry needed): packs `xeen.music.0` and `.1`, 21.9 + 21.7 MiB, 43.5 MiB in all at 320 kbit/s. The MM6–MM8
   tracks the other maps use come from those worlds (Xeen's `dependencies`).
5. **Checked 2026-11-22** (`build-xeen/game/openyamm`, isolated, `OPENYAMM_AUDIO_TRACE=1`; tours in
   `output/xeen_music_install/runs/`): X1 starts 92001 and switches to 92003 walking east along the west road into
   Vertigo's rectangle; D3 starts 92002 and switches to 92004 walking east along the caravan road into the
   Crossroads; P5 starts 92008. `build_world.py --check` 0 differ; `stale_bakes.py --check` 0 stale.
