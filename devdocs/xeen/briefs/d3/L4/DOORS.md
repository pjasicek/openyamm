# D3 Sandcaster and the Aging Forest: doors and arrivals

A5, 2026-11-20 (seventh session). Written from the build (`output/studio_cal/d3/build_w/build.json`) after the
install of 18:21. Units: X east, Y north, Z up; facing in MoveToMap units (east 0, north 512, west 1024, south
1536). A4's `d3.yml` is still `planned`: these are the doors and points A4 fills in.

## Arrivals (for A4's `arrivals:` and Town Portal)

| Arrival | Cell | X, Y, Z | Facing | What |
| --- | --- | --- | --- | --- |
| `sandcaster_square` | (36, 30) | (-14336, 17408, 1504) (the paving 16 over it) | 1536 (south) | the square by the mirror (4612), the Town Portal anchor and the new-game start of the tests |
| `sandcaster_stables` | (39, 43) | (-12800, 10752, 1312) | 512 (north) | the fenced caravan yard outside the south gate, the gate in sight (D-28) |
| ~~`sandcaster_jetty`~~ | - | - | - | dropped (D-28: Lucio's Jetty only departs) |

## Map edges

- **West (D2)**: D3's west start `entrance:west_road` (20, 44) = (-22528, 10240, 1312) facing east (0); the whole west edge leads to D2's east start (21504, 10240, 1312) facing west (1024) by `span`/`arrival` in project.yml (edge_spans, as X3/X4).
- **North (D4, installed)**: the whole north edge leads to D4's south start `entrance:south_road` (88, 105) = (12288, -20992, 2112) facing north (512) (A2's row: `down`, 7 days); D4's south edge lands at D3's `entrance:north_road` (88, 20) = (12288, 22528, 1760) facing south (1536) (`up`, 7 days). D4 continues these north-edge spans and heights (D-28; cells along x, units = (x - 64) * 512): x 0-24 crags 2,600-3,400; x 24-82 dunes 1,500-2,000; **x 82-94 the Lakeside road, level 1,750, the crossing at x 88 (12288), the road's bed 1,760**, east of the River of Wrath; x 94-104 the Wrath crest's north shoulder 1,900-2,400; x 104-128 the rim (0). The built edge rows agree within 96 (tenth session).
- **East and south**: the world rim (x 104, y 104), a cliff above the stars.

## Dungeon doors (sealed until their maps are installed and their lanes give the inside point)

| Door | Thing | Where | Its lane needs |
| --- | --- | --- | --- |
| DD-18 Sandcaster Sewer | `thing:dd18_shaft` (event `evt:thing:dd18_shaft`) | (30, 32) = (-17408, 16384, 1504), an iron lid against Barticus' Gym's south wall | A8: the inside point (foot of the shaft ladder in the members' room) |
| DD-19 Wizard Quarter (open, 24th session) | `thing:dd19_gate` (q-d14.quarter_gate, its line ending on "Enter?", then Yes/No buttons; Yes into DD-19's `entrance:d3_guild_gate` (0, 384, 0) facing north) | (43.5, 20.15) = (-10496, 22451, 1728), in the quarter's north wall, facing south | A8: DD-19's map with its arrival `entrance:d3_guild_gate` facing north (512); DD-19's way out lands on D3 at (-10496, 22150, 1728) = (43.5, 20.74) facing south (1536), kept clear; the guild precinct behind the gate is drawn north of the wall (D-42) |
| DD-07 Eastern Tower | `thing:eastern_tower` door (q-d18.tower_door, then sealed) | the tower on its knoll at (97, 46), door facing west, floor 1,952 | A7: the inside point (foot of its stair) |

## House doors (door id -> A4 house)

| Door | House | Name | Kind | Door point |
| --- | --- | --- | --- | --- |
| `building:sc_lucio_jetty` | 4649 | Lucio's Jetty | boats | (-18176, 21296, 1504) |
| `building:sc_guild_mind` | 4608 | Sandcaster Guild of Mind | mind_guild | (-16768, 20848, 1504) |
| `building:sc_guild_spirit` | 4609 | Sandcaster Guild of Spirit | spirit_guild | (-15232, 20848, 1504) |
| `building:sc_guild_light` | 4610 | Sandcaster Guild of Light | light_guild | (-13696, 20848, 1504) |
| `building:sc_magic` | 4603 | Aladdin's Lamps | magic_shop | (-15360, 19008, 1504) |
| `building:sc_alchemist` | 4604 | Vulture Repellant and Other Remedies | alchemist | (-13184, 19008, 1504) |
| `building:sc_temple` | 4605 | Temple of the Desert Sun | temple | (-17216, 19072, 1504) |
| `building:sc_training` | 4607 | Barticus' Gym | training | (-17200, 17280, 1504) |
| `building:sc_tavern` | 4606 | The Thirsty Camel | tavern | (-14640, 14208, 1504) |
| `building:sc_weapons` | 4601 | Sandsteel Blades | weapon_shop | (-11776, 16064, 1504) |
| `building:sc_armour` | 4602 | The Brass Scale | armor_shop | (-10496, 16064, 1504) |
| `building:sc_houses#1` | 4618 | Astra's House | residence | (-12800, 21056, 1504) |
| `building:sc_houses#2` | 4619 | Natasha the Enchantress | residence | (-14208, 19264, 1504) |
| `building:sc_houses#3` | 4620 | Madame Gloriana's | residence | (-15936, 18432, 1504) |
| `building:sc_houses#4` | 4621 | School of Trade | residence | (-15936, 17408, 1504) |
| `building:sc_houses#5` | 4622 | School of Letters | residence | (-15936, 16640, 1504) |
| `building:sc_houses#6` | 4623 | The Quiet House | residence | (-18304, 15680, 1504) |
| `building:sc_houses#7` | 4624 | School of Navigation | residence | (-17984, 14848, 1504) |
| `building:sc_houses#8` | 4625 | School of Tongues | residence | (-18304, 14016, 1504) |
| `building:sc_houses#9` | 4626 | The Knife House | residence | (-17408, 14016, 1504) |
| `building:sc_houses#10` | 4627 | Saffron House | residence | (-15936, 15232, 1504) |
| `building:sc_houses#11` | 4628 | The Archer's House | residence | (-16512, 13504, 1504) |
| `building:sc_houses#12` | 4629 | Dune House | residence | (-9472, 16064, 1504) |
| `building:sc_houses#13` | 4630 | The Dyer's | residence | (-13248, 15104, 1504) |
| `building:sc_houses#14` | 4631 | Glassblower's House | residence | (-13248, 13952, 1504) |
| `building:sc_houses#15` | 4632 | The Water Seller's | residence | (-11648, 14784, 1504) |
| `building:sc_houses#16` | 4633 | Camel House | residence | (-10496, 14784, 1504) |
| `building:sc_houses#17` | 4634 | Scribe's House | residence | (-9664, 14592, 1504) |
| `building:sc_houses#18` | 4635 | Potter's Yard | residence | (-11392, 13504, 1504) |
| `building:sc_houses#19` | 4636 | The Tax House | residence | (-9856, 13504, 1504) |
| `building:sc_houses#20` | 4637 | Courtyard House | residence | (-11904, 17728, 1504) |
| `building:sc_houses#21` | 4638 | Sandal Maker's | residence | (-10240, 17728, 1504) |
| `building:sc_houses#22` | 4639 | Date Palm House | residence | (-9216, 17728, 1504) |
| `building:sc_houses#23` | 4640 | Well House | residence | (-16768, 20160, 1504) |
| `building:wq_guild_dark` | 4613 | The Guild of Night | dark_guild | (-11120, 21760, 1728) |
| `building:wq_magic` | 4614 | Esoterica | magic_shop | (-9472, 21616, 1728) |
| `building:wq_houses#1` | 4615 | The Mindwright's Tower | residence | (-11356, 19584, 1728) |
| `building:wq_houses#2` | 4616 | The Appraiser's Tower | residence | (-10368, 19876, 1728) |
| `building:wq_houses#3` | 4617 | The Alembic Tower | residence | (-9636, 20352, 1728) |
| `building:sc_stables` | 4611 | Sandcaster Caravans | stables | (-11984, 11648, 1312) |
| `building:xr_stall#1` | 4641 | The Food Stall | tavern | (-2896, 9216, 1248) |
| `building:xr_stall#2` | 4642 | Robes and Cloaks | armor_shop | (-3152, 10752, 1248) |
| `building:xr_stall#3` | 4643 | Necklaces of Note | magic_shop | (-2560, 11344, 1248) |
| `building:xr_stall#4` | 4644 | Belts and Buckles | armor_shop | (-1200, 11264, 1248) |
| `building:xr_stall#5` | 4645 | Boots for the Road | armor_shop | (-944, 9728, 1248) |
| `building:xr_stall#6` | 4646 | Caleb's Workshop | residence | (-1664, 9136, 1248) |
| `building:celia_derek_cottage` | 4647 | Celia and Derek's Cottage | residence | (384, 8512, 1248) |
| `building:thaddeus_hut` | 4648 | The Fountain Keeper's Hut | residence | (8768, -5504, 960) |

The mirror 4612 is `thing:sc_mirror` on the square (`Xeen.useMirror(4612, eventId, continueStep)`).
