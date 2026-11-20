# Decoration settings for all 42 outdoor maps

These authoring settings are installed; see WORK_STATE.json for validation evidence. New Sorpigal remains the accepted calibration.

Density is a multiplier on each family baseline in [families.yml](families.yml): meadow/coastal/woodland/dry meadow 50 candidates per cell, dry/dead tufts 8, reeds 18, tropical cover 24, earth stones 10, snow stones 3, volcanic stones 6, other chips 4. Candidate counts precede masks, slope/building checks and patchiness; they are not instance predictions.

New version-2 maps use 4096-unit foliage distance and conservative short silhouettes; New Sorpigal retains its current settings including 6144-unit grass distance. Stones retain the renderer's shorter range. Missing materials do not receive speculative rules.

## MM6

| Map | Actual tile families (cell counts) | Decoration family × density | Placement intent |
| --- | --- | --- | --- |
| Sweet Water (`outa1`) | cracked 11142, snow 2876, dirt 1612, roads 281, water 156, shore 62 | Disabled | Sweet Water: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Paradise Valley (`outa2`) | cracked 9001, sand 3442, dirt 1956, water 1231, roads 411, shore 88 | Disabled | Paradise Valley: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Hermit's Isle (`outa3`) | water 6862, sand 5653, dirt 1982, volcano 981, shore 532, roads 119 | Disabled | Hermit's Isle: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Kriegspire (`outb1`) | snow 9412, dirt 4872, volcano 1511, roads 291, shore 32, water 11 | Disabled | Kriegspire: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Blackshire (`outb2`) | dirt 9691, sand 5177, grass 553, roads 343, water 217, shore 148 | grass: dry_meadow ×0.65 | Blackshire: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Dragonsand (`outb3`) | sand 9203, water 5248, grass 732, shore 634, dirt 181, roads 131 | grass: dry_meadow ×0.55 | Dragonsand: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Frozen Highlands (`outc1`) | snow 8269, dirt 6204, water 889, roads 448, shore 319 | Disabled | Frozen Highlands: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Free Haven (`outc2`) | dirt 11468, water 2228, grass 797, shore 764, roads 576, sand 296 | grass: meadow ×0.65 | Free Haven: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Mire of the Damned (`outc3`) | water 6046, swamp 5161, dirt 3756, shore 861, roads 305 | swamp: marsh_reed ×0.7 | Mire of the Damned: Taller reeds on masked swamp islands and transitions; other ground bare. |
| Silver Cove (`outd1`) | water 8354, grass 4205, dirt 2489, shore 890, roads 191 | grass: meadow ×0.7 | Silver Cove: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Bootleg Bay (`outd2`) | water 10228, dirt 2494, grass 2134, shore 572, tropical 441, roads 260 | grass: coastal_grass ×0.85; tropical: tropical_low ×0.8 | Bootleg Bay: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Castle Ironfist (`outd3`) | water 6361, grass 3210, dirt 2911, swamp 2137, shore 964, roads 546 | grass: meadow ×0.8; swamp: marsh_reed ×0.5 | Castle Ironfist: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Eel Infested Waters (`oute1`) | water 13987, grass 1570, shore 549, roads 18, dirt 5 | grass: coastal_grass ×0.9 | Eel Infested Waters: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Misty Islands (`oute2`) | water 13583, grass 1736, shore 684, roads 96, dirt 30 | grass: coastal_grass ×0.9 | Misty Islands: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| New Sorpigal (`oute3`) | water 11180, grass 2355, shore 976, dirt 974, volcano 528, roads 116 | grass: meadow ×1 | New Sorpigal: Retain accepted grass placement and masks; remove dirt stones. |

## MM7

| Map | Actual tile families (cell counts) | Decoration family × density | Placement intent |
| --- | --- | --- | --- |
| Emerald Island (`7out01`) | water 14938, grass 766, shore 196, dirt 107, roads 67, swamp 55 | grass: coastal_grass ×0.9; swamp: marsh_reed ×0.4 | Emerald Island: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Harmondale (`7out02`) | grass 8003, dirt 5410, snow 1872, roads 342, shore 254, water 248 | grass: meadow ×0.45 | Harmondale: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Erathia (`7out03`) | grass 11387, water 2655, dirt 600, shore 568, snow 502, roads 417 | grass: meadow ×0.25 | Erathia: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| The Tularean Forest (`7out04`) | grass 8693, water 6231, shore 646, dirt 299, roads 260 | grass: woodland_grass ×0.3 | Tularean Forest: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Deyja (`7out05`) | waste 9190, water 2989, sand 2847, dirt 742, shore 188, roads 173 | Disabled | Deyja: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| The Bracada Desert (`7out06`) | sand 6457, waste 4192, dirt 4155, water 1082, shore 142, roads 101 | Disabled | Bracada Desert: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Tatalia (`7out13`) | dirt 5062, snow 4281, water 4236, swamp 2101, shore 313, roads 136 | swamp: marsh_reed ×0.8 | Tatalia: Taller reeds on masked swamp islands and transitions; other ground bare. |
| Shoals (`7out15`) | sand 16129 | Disabled | Shoals: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Evenmorn Island (`out09`) | water 13621, grass 1959, shore 506, sand 42, dirt 1 | grass: coastal_grass ×0.8 | Evenmorn Island: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Mount Nighon (`out10`) | dirt 10434, snow 2733, water 1698, sand 973, shore 252, roads 39 | Disabled | Mount Nighon: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| The Barrow Downs (`out11`) | dirt 8625, grass 4677, water 1456, shore 1259, roads 112 | grass: dry_meadow ×0.65 | Barrow Downs: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| The Land of the Giants (`out12`) | water 6678, waste 6068, snow 2024, dirt 1019, shore 328, roads 12 | Disabled | Land of the Giants: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Avlee (`out14`) | grass 10469, water 4614, shore 747, dirt 215, roads 84 | grass: woodland_grass ×0.25 | Avlee: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |

## MM8

| Map | Actual tile families (cell counts) | Decoration family × density | Placement intent |
| --- | --- | --- | --- |
| Plane of Air (`elema`) | rock 16128, roads_dirt 1 | Disabled | Plane of Air: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Plane of Fire (`elemf`) | lava 11937, volcano 2874, lava_dirt 1314, dirt 4 | Disabled | Plane of Fire: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Plane of Water (`elemw`) | dirt 16129 | Disabled | Plane of Water: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Dagger Wound Island (`out01`) | water 11280, grass 2601, shore_dirt 1177, volcano 570, dirt 373, roads_dirt 128 | grass: tropical_low ×0.55 | Dagger Wound Island: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Ravenshore (`out02`) | grass 7994, water 4063, rock 1823, dirt 1155, shore_dirt 584, roads_dirt 510 | grass: meadow ×0.35 | Ravenshore: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Alvar (`out03`) | grass 9647, rock 3148, water 1138, dirt 938, shore_dirt 746, roads_dirt 512 | grass: meadow ×0.3 | Alvar: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Ironsand Desert (`out04`) | plains 7781, plains_sand 4950, lava 2725, lava_plains 451, roads_plains 222 | Disabled | Ironsand: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Garrote Gorge (`out05`) | dirt 10247, grass 4853, shore_dirt 547, roads_dirt 313, water 168, red_dirt 1 | grass: dry_meadow ×0.5 | Garrote Gorge: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Shadowspire (`out06`) | grey_dirt 9504, grey_stone 4255, water 1489, tar_grey 316, roads_grey 315, tar 138, shore_grey 112 | Disabled | Shadowspire: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Murmurwoods (`out07`) | grass 11163, dirt 4777, roads_dirt 189 | grass: woodland_grass ×0.25 | Murmurwoods: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Ravage Roaming (`out08`) | sandstone 7073, dirt 6043, water 2216, shore_dirt 607, roads_dirt 190 | Disabled | Ravage Roaming: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Regna (`out13`) | water 11813, grass 3662, shore_dirt 653, dirt 1 | grass: coastal_grass ×0.7 | Regna: Decorations only on grass/tropical/swamp portions; all other terrain stays bare. |
| Tutorial (`out15`) | dirt 16129 | Disabled | Tutorial: No grass/tropical/swamp cover selected; terrain decorations disabled. |
| Plane Between Planes (`pbp`) | dirt 10851, water 1661, lava 1454, volcano 1409, lava_dirt 407, shore_dirt 347 | Disabled | Plane Between Planes: No grass/tropical/swamp cover selected; terrain decorations disabled. |

