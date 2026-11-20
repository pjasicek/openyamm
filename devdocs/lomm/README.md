# Legends of Might and Magic (LoMM) content

Status (2026-10-30): survey and candidate lists only. Nothing is converted or installed, and the user has not yet chosen
the final lists.

LoMM is a 2001 LithTech 2.x team game set in the Might and Magic universe. The HD install lives in
`reference/legends_of_mm/` (git-ignored). Its assets are in `Data/*.REZ`; the loose `Data/` folders are the HD overrides
(textures at 512–2048 px and all map files).

## The plan

- The good LoMM maps become **standalone dungeons**, rebuilt as native BLVs and prettified the way the MM9 content is
  ([MM9 rework](../mm9_rework/README.md)).
- For now they open by consuming a map item from the inventory, like MAW's dimension maps.
- **Vision only, not current work:** each character builds or gets a Path of Exile style hideout (perhaps Castle
  Harmondale after clearing it), with a dimensional pedestal for moving between worlds and a mapping device that takes a
  map and maybe a mutator.

## Formats and tools

| Asset | Format | Reader | Result |
| --- | --- | --- | --- |
| Archives | REZ v1 | `tools/mm9_import_discovery/extract_rez.py` | 12 archives, 4,358 assets |
| Maps | DAT v66 | `transcode_mm9_dat_to_odm.read_dat_world` | all 107 files parse (87 unique maps) |
| Models | ABC v13 | `convert_abc_model.read_abc` | 576 of 580 parse; FISH, COFFINFANCY, COFFINRAISED and one debris piece fail |
| Textures | DTX -5 | `convert_abc_model.decode_dtx_mips` | one retail texture is version -4 |

Asset counts: 87 maps (20 retail, 67 community), 580 models, 1,509 animation clips, 1,536 textures, 1,490 WAV files,
345 interface PCX files, 131 `.scr` actor scripts.

Details that bit during the survey:

- Loose HD skins use mixed filename case; resolve them case-insensitively.
- Some HD skins (Bandit, Harpy, Evil Eye) have an empty alpha channel. Ignore alpha on opaque skins.
- `convert_abc_model.py` needs `pygltflib` for GLB export.

## Scale

**2.56, the same as MM9.** Measured from 422 retail doors: median 96 × 52 LithTech units, 246 × 133 at 2.56, against
246 × 164 for MM9 town doors.

## Map survey

Medians at scale 2.56. Floor is in million square units: LoMM's is the walkable floor from a flood fill out of the spawn
points, MM6–MM8's is every up-facing BLV face. Treat the LoMM figure as an estimate: grass skirts inflate some maps
(Dungeon Rescue, Wedding Day, Beach). LoMM polygons are VisBSP polygons, which are not directly equal to BLV faces.

| | LoMM retail (20) | LoMM community (67) | MM6 BLV | MM7 BLV | MM8 BLV |
| --- | --- | --- | --- | --- | --- |
| Floor | 98 | 74 | 40 | 38 | 24 |
| Longest span | 14.1k | 11.9k | 13.3k | 12.4k | 9.0k |
| Polygons or faces | 1,695 | 1,146 | 1,400 | 1,973 | 1,829 |
| Doors | 25 | 0 | 13 | 7 | 5 |
| Lights | 179 | 30 | 59 | 14 | 17 |
| Props or decorations | 50 | 2 | 65 | 22 | 14 |
| Placed monsters / spawn points | 18 monsters | 0 monsters | 41 spawns | 34 spawns | 18 spawns |

- Every map is BLV-sized. The largest span is about 30k, against about 45k of ODM play area.
- Detail density is low: about 17 polygons per million square units of floor, against 35–70 faces in MM6–MM8. Rooms are
  wide because the maps were built for FPS combat.
- Retail: 8 maps are mostly indoor, 8 mostly open-air. Community: 26 and 20.
- Monster density needs raising to MM6–MM8 levels when a map is rebuilt.

| Mechanisms | Retail | Community |
| --- | --- | --- |
| Doors | 505 (18 of 20 maps) | 243 (31 of 67) |
| Lifts | 9 | 80 |
| Teleporters | 8 | 68 |
| Traps | 12 | 191 |
| Destructibles, maps with any | 17 | 42 |
| Ladders, maps with any | 19 | 47 |
| Maps with script objects | 0 | 2 |

Every map: [map_table.txt](map_table.txt). Columns: reachable floor, sky share, span, height range, levels, polygons,
world-model polygons, textures; doors, lifts, buttons and triggers, teleporters, traps, destructibles, ladders, scripts,
spawners; props, lights, torches, sounds, chests, loot; hostile count, distinct types, animals; unresolved textures,
models and skins.

Open-air maps need sky in BLVs, which the engine lacks today (`skymarker` faces show a sky texture). The user expects
this to be a small change.

## Map candidates

Ranked by layout, not by the old look, because textures get rebuilt anyway.

Rebuild first:

| Map | Source | Type | Floor | Doors | Monsters (types) | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Secrets of the Sphinx | Retail | Egyptian tomb | 38 | 6 | 14 (3) | Pilot: small and fully indoor |
| Dragonblade | Retail | Desert temple | 114 | 18 | 31 (4) | 10 height levels, 10 traps, painted halls |
| Dungeons of Dragadune | Retail | Castle and dungeons | 84 | 74 | 23 (3) | Most mechanisms in retail; about 35% open-air |
| Spider's Den | Retail | Dark stronghold | 101 | 55 | 14 (1) | 7 chests, almost all indoor |
| On the Run | Retail | Palace dungeon | 69 | 25 | 24 (2) | Clean loop around a central round hall |
| Temple of Bark | Retail | Giant tree and lava | 91 | 0 | 27 (4) | Best set piece |
| Forgotten Keep | Retail | Keep with water court | 50 | 28 | 17 (4) | Compact, close to MM6–MM8 size |
| Colossus Bark | Community | Long quest temple | 185 | 2 | 85 (9) | Co-op route, 29 traps, 13 chests |
| The Drop | Community | Descent through caves | 127 | 11 | 79 (20) | 8.8k of height, 10 teleporters, 28 ladders |
| Hidden Cavern | Community | Dwarf mine | 61 | 0 | 32 (5) | 20 lifts, 10 chests, dense |
| Murders | Community | Walled castle and crypt | 41 | 12 | 1 (1) | Most detailed of all 87; needs monsters |
| SwordRunners | Community | Ring fortress | 97 | 6 | 0 | 5.4k of height; needs monsters |
| SwordRunners II | Community | Domed citadel | 56 | 12 | 0 | 89 textures; needs monsters |

Second batch:

- Open-air, needing BLV sky: Hideout, Cult of the Spider, Stoneham, Sword in the Stone, Ancient Lands, Never Surrender.
- Indoor or mixed: Dragon Slayers, Castle Witherhide, Illusions, Inconceivable Quest, Ice God, Iceblade, Temple of Tool,
  Chambers of Combat. Ice God and Iceblade have tiled "water" placeholder floors, which a rebuild replaces.

Leave out: Chateau Escape, Fahltee Tower, The Fortress and Battlegrounds (mostly empty ground or plain boxes), the Dark
Oddity maps and the rest of the community set.

Unresolved textures: Sword of Defiance (332 polygons), Fallen City (160), New Room (142), The Sewers (104) among
community
maps; Wedding Day (60), Fahltee Tower (46), Blood Feud (42) among retail maps.

Images: [retail overview](images/overview_retail.jpg); community overviews
[1](images/overview_community_1.jpg), [2](images/overview_community_2.jpg), [3](images/overview_community_3.jpg);
first-person shots of 37 maps [1](images/map_shots_1.jpg), [2](images/map_shots_2.jpg), [3](images/map_shots_3.jpg),
[4](images/map_shots_4.jpg), [5](images/map_shots_5.jpg). The shots have no props or baked lighting, and the black or
sky-only frames are bad camera placements, not map faults.

## Monsters

33 distinct hostile types are placed: 31 in retail maps, all 33 across community maps (Earth Elemental and Nobleman only
there). 15 are also in MM9.

- Same mesh as MM9: Basilisk, Dagrell, Dragonfly, Dwarf, Terror Eye, Lich, Troglodyte, and Evil Eye as a skin on Terror.
- Reworked in MM9: Lich King, Monk, Mummy, Nobleman, Skeleton, Skeleton Warrior, Zombie.
- Not in MM9 (18): Bandit, Goblin, Orc, Soldier, Spider, Nasty Spider, Lizardman, Lizard Warrior, Wight, Gargoyle,
  Harpy,
  Troll, Stone Golem, Earth Elemental, Dwarf King, Titan, Grand Titan, Red Dragon.

Orc is the only family with no equivalent in `monster_data.txt`; the others are new looks or new bosses.

| Priority | Monster | What it adds |
| --- | --- | --- |
| 1 | Orc + Orc Chief | New family, 2 skins, thrown axe and 3 melee attacks |
| 2 | Lizard Warrior | 3 ready tiers: green, brown, blue |
| 3 | Nasty Spider | 3 ready tiers: brown, red, black |
| 4 | Grand Titan | Boss, StepOn and Wipe attacks |
| 5 | Dwarf King | Boss for the Dwarf family |
| 6 | Red Dragon | Lair boss with Sleep and WakeUp; no walk or fly clip |
| 7 | Gargoyle | Statue ambush: Standup, then air-only combat |
| 8 | Harpy | Fullest clip set (25 clips) |
| 9 | Troll, Wight, big Spider | New 3D looks for those families |
| 10 | Stone Golem | Temple guardian for the Egyptian maps |

Skip for now: Goblin and Earth Elemental (MM6 3D versions exist), Bandit and Soldier (MM9's Highwayman and Guard fill
the
roles), Lich King, Zombie, Mummy, Monk and Skeleton (in MM9's queue).

[Monster sheet](images/monsters.jpg): bind pose with HD skins. The clips themselves have not been viewed; names and
counts
come from the model files. The expected route is MM9's: the original skeleton and clips on a new mesh. It has not been
tried on a LoMM model.

## Conversion notes

- The route is [the MM9 dungeon playbook](../../level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md). LoMM maps
  are
  the same DAT version. Its class table covers doors, rotating doors, destructibles, triggers, ladders, lights and
chests.
  Lifts and teleporters are not in that table and need checking.
- The converter writes into the MM9 world, so LoMM needs its own target world and prop conversion.
- Scenario logic (Princess Rescue, Sword in the Stone) does not carry over. Retail maps use no script objects.
- MAW dimension runs swap a map's three encounter families and refill its spawn points
  (`MawMonsterRules::enterMap`), so a rebuilt map with spawn points works with them.
- `dimension_maps.yml` only opens maps the party has completed, which a map reached only through a map item never is.
  LoMM targets need to bypass that gate.
- No authors or permissions were found for the community maps; settle this before shipping rebuilds of them.

## Survey data

Git-ignored working files in `output/lomm_review/`: the survey scripts in `survey_tools/`, `survey.json`, `table.json`,
`mm678.json`, full-size images and the Blender render scripts. The scripts read REZ contents extracted to a temporary
folder; re-extract with `extract_rez.py` to rerun them.
