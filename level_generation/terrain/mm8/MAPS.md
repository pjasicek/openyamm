# MM8 terrain map guide

All14 outdoor maps use the same world terrain pack. Switching maps does not require reinstalling.
Counts below come from the effective tile grid, including scene overrides.

| Map | Asset filename | Used static textures | Terrain families |
| --- | --- | ---: | --- |
| Plane of Air | `elema.odm` | 10 | roads dirt, rock |
| Plane of Fire | `elemf.odm` | 29 | dirt, lava, lava dirt, volcano |
| Plane of Water | `elemw.odm` | 1 | dirt |
| Dagger Wound Island | `out01.odm` | 60 | dirt, grass, roads dirt, shore dirt, volcano, water |
| Ravenshore | `out02.odm` | 62 | dirt, grass, roads dirt, rock, shore dirt, water |
| Alvar | `out03.odm` | 62 | dirt, grass, roads dirt, rock, shore dirt, water |
| Ironsand Desert | `out04.odm` | 40 | lava, lava plains, plains, plains sand, roads plains |
| Garrote Gorge | `out05.odm` | 48 | dirt, grass, red dirt, roads dirt, shore dirt, water |
| Shadowspire | `out06.odm` | 55 | grey dirt, grey stone, roads grey, shore grey, tar, tar grey, water |
| Murmurwoods | `out07.odm` | 29 | dirt, grass, roads dirt |
| Ravage Roaming | `out08.odm` | 40 | dirt, roads dirt, sandstone, shore dirt, water |
| Regna | `out13.odm` | 28 | dirt, grass, shore dirt, water |
| Tutorial | `out15.odm` | 1 | dirt |
| Plane Between Planes | `pbp.odm` | 43 | dirt, lava, lava dirt, shore dirt, volcano, water |

Animation adds14 frames each for water, lava and tar, shared by the maps that use those liquids.
The package preserves native map placement, including original incompatible corner/edge combinations.
See `reports/native_join_audit.json` and `reports/native_contexts/visual_review.json` for that distinction.
