# Alvar versus Garrote Gorge for Castleview

[Alvar visual catalogue](../../catalogues/mm8_alvar/index.html) · [Side-by-side images](../../catalogues/mm8_alvar/images/alvar_vs_garrote.jpg) · [Measured candidate mapping](alvar_style_candidates.json) · [Existing Garrote proposal](GARROTE_STYLE_MAPPING.md)

**My recommendation is Alvar for most civilian houses, with Garrote retained for the city walls, gates, jail and royal fortifications.** Alvar better expresses the lived-in market town inside our Castleview walls: warm masonry, tiled roofs, compact cottages, service bays and larger shared establishments. This is a design judgement against our MM5 brief, not a claim that Alvar reproduces the original MM5 art.

This is a comparison before geometry authoring. It does not replace `architecture_mapping.json`, move buildings, change residents or change the approved minimap. Every resulting MM5 house/wall will still be newly constructed; the original BModels are rendered only as evidence.

## Where each reference is strongest

| Need in Castleview | Alvar | Garrote | Suggested use |
| --- | --- | --- | --- |
| Ordinary residents and shared homes | Warm brown wall panels, brown roof tiles, gables/hips, chamfered small cottages and domestic steps | Green-grey masonry and green roofs give a more consistent stone-settlement character | Alvar for the main residential streets; retain the planned quality differences |
| Shops and service houses | Parts 13–15 physically join four services; inns have a main body plus an entrance wing | More individually modeled camp service buildings | Alvar provides a stronger joined-premises reference, adapted into unequal bays |
| Temple and mayor/civic buildings | Recognizable nave/aisles, low formal houses, merchant guild with portico and corner towers | Fortified halls and dressed stone details | Alvar for the temple and civic frontage; no need to make the mayor’s office another keep |
| Walls, gates and jail | No complete city curtain/gate kit in Alvar; its fort and guildhouse are isolated compounds | Dragon Hunter Camp gives a measured curtain, real gate and fortified masses | Garrote remains stronger |
| Castle Kalindra | Merchant guildhouse offers civic portico/tower composition, but is broad and only 1024 high | Camp keep provides fortification details but is also low, at 960 | New taller royal composition; Garrote structure, selective Alvar civic details |
| Ellinger’s tower | A 1152-high polygonal guild tower gives an arcane accent, with a distinctive broad roof cap | Stone tower/gate details relate to the city’s fortifications | New tall tower; neither native silhouette is the finished design |
| Fountain and small public spaces | Parts 79–80 form a complete 800×800 fountain with a low stone basin | Wells and camp utilities are useful smaller references | Author our 512-wide HP fountain using Alvar’s basin/cascade idea; preserve its planned interaction |

## Scale and occupancy findings

- All 34 residential assemblies have one initial NPC-table occupant in the current merged base; the merchant guild adds Bastian Loudrin. There are also 12 named service proprietors. Alvar’s architecture does not justify splitting our established shared households.
- Garrote has 17 residential assemblies for 21 initial NPCs, including four two-person homes. The 576×448 Morningstar cottage demonstrates that two occupants do not require an estate.
- Alvar’s visible residential entrance faces measure 128×256 native units throughout. That agrees with the door scale already proposed for Castleview. Keep these dimensions while adding/removing wall bays and changing roof composition.
- Example Alvar exteriors: poor2 cottage 768×512×400; med1 gabled house 680×800×512; med3 house 736×768×576; rich1 low residence 1280×784×448; paired rich2 estate 1184×1296×896. Source family names are not a reliable height or wealth ranking.
- The four-shop block is 2272×2272; our tailor/cobbler reservation is 1792×768. Its whole symmetric footprint is unsuitable, but its independently entered connected shop bays are useful.
- Alvar’s training hall is 1152×1600; our training reservation is 1536×1000. It needs a new shorter/narrower arrangement. Its flat roof and buttresses also suit an institution better than a friendly cottage.
- The Merchant Guildhouse is 2816×3008×1024; it fits within Kalindra’s 4096×3072 outer reservation in plan, but leaves little depth margin and is far below the proposed 2560 roof / 3584 principal towers. This is a massing reference, not a ready-made castle.
- Havest Hall and nine other script house destinations have no active outdoor BModel entry in this source. They are listed separately in the catalogue; missing mesh bindings are not guessed onto neighbouring houses.

## Proposed references for all 24 town premises

The fit column compares only native exterior dimensions against the existing reservation, with a quarter-turn allowed. A yes does not certify streets, doors, room capacity or foundation fit. A no identifies geometry that must be recomposed; no uniform model scaling is proposed.

| MM5 premises / residents | Alvar reference parts | Reserved XY / native XYZ | Native envelope fits? | Proposed treatment |
| --- | --- | --- | --- | --- |
| **Ol’ Black Magic** — Nool the Doomsayer; Metla the Rosterkeeper | [092](../../catalogues/mm8_alvar/models/092.md) | 1280 × 1100 / 1024 × 1024 × 1152 | yes, dimensions only | Use the polygonal guild vocabulary sparingly; author a lower main hall and membership wing, with Nool still outside. |
| **Ogre Foundry** — Service/interior contacts remain as planned | [013](../../catalogues/mm8_alvar/models/013.md), [014](../../catalogues/mm8_alvar/models/014.md), [015](../../catalogues/mm8_alvar/models/015.md) | 1536 × 1000 / 2272 × 2272 × 768 | no; recompose | Use one or two asymmetric shop bays and a Garrote-like working canopy; the whole four-way block is far too large. |
| **Tog’s Training / swimming annex** — Ordana the Swimming Instructor | [076](../../catalogues/mm8_alvar/models/076.md), [077](../../catalogues/mm8_alvar/models/077.md) | 1536 × 1000 / 1152 × 1600 × 576 | no; recompose | Shorten and narrow the hall to the reservation; keep the swimming annex separate. Its native buttressed flat roof is institutional, not a domestic default. |
| **Castleview Jail** — Jasper | Keep Garrote reference | 1088 × 1536 / — | — | Keep the fortified masonry and controlled prison threshold; Alvar cottages are not the right structural reference. |
| **First Drawkcab chapterhouse** — Tinit First Drawkcab Monk; Bob the Drawkcab Monk | [066](../../catalogues/mm8_alvar/models/066.md) | 1280 × 640 / 640 × 1408 × 448 | no; recompose | Shorten the long cottage and retain two study places under one roof; plain finish without an estate tower. |
| **Drawkcab study house** — Pip the Drawkcab Monk; Otto the Drawkcab Monk | [068](../../catalogues/mm8_alvar/models/068.md) | 1152 × 640 / 832 × 640 × 512 | yes, dimensions only | A smaller gabled companion house with an offset door/garden side, not a mirrored duplicate. |
| **Milken Savings / accounts** — Rex the Accountant | [065](../../catalogues/mm8_alvar/models/065.md) | 1408 × 832 / 704 × 1024 × 408 | yes, dimensions only | Compact finance house with a subordinate accounts room; one bank service and Rex retain their separate roles. |
| **Blacksmoke Tavern** — Tanya the Floozy; Gloria the Dreamer | [097](../../catalogues/mm8_alvar/models/097.md), [098](../../catalogues/mm8_alvar/models/098.md) | 1664 × 1280 / 1408 × 1472 × 800 | no; recompose | New main guest room and lower entrance wing; reduce depth to preserve the street and shared court. |
| **Adventurers’ lodging** — Esteban the Adventurer; Bleys the Burglar | [033](../../catalogues/mm8_alvar/models/033.md), [034](../../catalogues/mm8_alvar/models/034.md) | 1152 × 768 / 1184 × 1296 × 896 | no; recompose | Borrow unequal connected wings; omit the estate tower and reduce the footprint for shared modest lodging. |
| **Mapmakers’ court** — Jethro the Mapmaker; Miles the Cartographer; Lydia the Mapmaker | [040](../../catalogues/mm8_alvar/models/040.md) | 1664 × 1088 / 736 × 768 × 576 | yes, dimensions only | Maintained square house with a map room and visible window/door rhythm; reserve remaining space for the shared frontage. |
| **Mayor’s office and editorial room** — Majot the Editor; Mayor Snarfblad | [049](../../catalogues/mm8_alvar/models/049.md) | 1664 × 1088 / 1280 × 784 × 448 | yes, dimensions only | Wide low formal residence with an audience/office bay; restrained civic identity without another castle. |
| **Taskmaster’s hiring office** — Jojosh the Taskmaster | [011](../../catalogues/mm8_alvar/models/011.md) | 832 × 640 / 1216 × 960 × 512 | no; recompose | Borrow the timber canopy and loading details only; the native stables exceed this small yard reservation. |
| **Joe’s map stall** — Joe the Mapmaker | [067](../../catalogues/mm8_alvar/models/067.md) | 512 × 512 / 768 × 512 × 400 | no; recompose | Even the small Alvar cottage exceeds Joe’s 512-square envelope. Author a small lean-to/shelter; do not shrink doors or silently enlarge the lot. |
| **Goldur’s lodge** — Goldur the Ranger | [068](../../catalogues/mm8_alvar/models/068.md) | 832 × 640 / 832 × 640 × 512 | yes, dimensions only | Plain gabled cottage at normal door scale, with a practical garden-facing side. |
| **Zelda’s house and drying shed** — Zelda the Herbalist | [067](../../catalogues/mm8_alvar/models/067.md) | 1088 × 768 / 768 × 512 × 400 | yes, dimensions only | Small cottage with herb-drying details and planted court; quality comes from use and repair rather than a taller roof. |
| **Nadia’s house** — Nadia the Hoarder | [067](../../catalogues/mm8_alvar/models/067.md) | 896 × 768 / 768 × 512 × 400 | yes, dimensions only | Worn small cottage with an offset entrance and sparse trim; preserve the west-gate lane. |
| **Oorla’s house / Troyanna’s room** — Madame Oorla the Gypsy; Troyanna the Mindreader | [040](../../catalogues/mm8_alvar/models/040.md) | 1280 × 832 / 736 × 768 × 576 | yes, dimensions only | Shared study house, two interior work areas, restrained arched-window details; no need for two exterior towers. |
| **Gremlin court** — Gettlewaithe the Gremlin King | Keep Garrote reference | 1536 × 1664 / — | — | Keep the fortified audience annex distinct from ordinary housing. |
| **Ellinger’s Tower** — Service/interior contacts remain as planned | [092](../../catalogues/mm8_alvar/models/092.md) | 1536 × 1536 / 1024 × 1024 × 1152 | yes, dimensions only | Use the polygonal shaft/entry as a study only. Ellinger requires a much taller original composition with repeated normal-scale bays, not a stretched guild mushroom roof. |
| **Temple of Mok** — Ben the Benchman; Imble the Monk | [078](../../catalogues/mm8_alvar/models/078.md) | 1664 × 1280 / 1344 × 1024 × 768 | yes, dimensions only | The nave, lower side aisles and entrance porch suit Mok’s civic temple; create new symbols and preserve the taller planned nave. |
| **Tailor and cobbler row** — Gromlug the Tailor; Sojo the Cobbler | [013](../../catalogues/mm8_alvar/models/013.md), [014](../../catalogues/mm8_alvar/models/014.md), [015](../../catalogues/mm8_alvar/models/015.md) | 1792 × 768 / 2272 × 2272 × 768 | no; recompose | Create two unequal shallow work bays for tailor/cobbler with distinct doors. Do not use the cross-shaped symmetric four-shop plan. |
| **Workers’ shared house** — Daron the Efficient; Tolberti the chimney sweep | [067](../../catalogues/mm8_alvar/models/067.md) | 1024 × 512 / 768 × 512 × 400 | yes, dimensions only | One low cottage for Daron and Tolberti; shared occupancy is supported by the Garrote/Ravenshore study, not inferred from Alvar’s single-resident table. |
| **Keeper’s cottage and kennel** — Sinbolas the Dog Catcher; Raymond the Direct | [067](../../catalogues/mm8_alvar/models/067.md) | 896 × 640 / 768 × 512 × 400 | yes, dimensions only | Small shared cottage and newly fitted low kennel canopy; two residents do not imply a rich estate. |
| **Dyson’s public storehouse** — Dyson the Puzzlemaster | [076](../../catalogues/mm8_alvar/models/076.md), [077](../../catalogues/mm8_alvar/models/077.md) | 2176 × 1792 / 1152 × 1600 × 576 | yes, dimensions only | Broad low functional storehouse with two nine-chest bays and Dyson’s desk; no imported training service or native hall mesh. |

## Keeping the combined style coherent

Use a deliberate material hierarchy: warmer Alvar domestic walls and brown tiled roofs within the town, heavier Garrote-style masonry at the perimeter and royal structures. Keep common door size, related mortar/stone tones, matching foundation courses and restrained trim. Do not alternate the two complete texture families randomly from house to house. The next visual blockout should compare both materials under the actual Castleview lighting before settling the wall/house transition.

Alvar’s common domestic family is `t05*`, including `t05a05` roof tiles and `t05a03` doors; Garrote’s is `t18*`. Native role swatches and exact UV/texel measurements are in their catalogues. Alvar buildings already share compatible temperate grass/dirt surroundings, but terrain tile-bank selection still follows the Brackenford calibration.

For Kalindra, prioritize the user’s taller friendly royal silhouette. Use a portico or a few corner/wing relationships from Alvar’s merchant guild if useful, then design the keep and towers at the actual reserved site. Avoid inheriting the guild’s low, broad roof or importing its MM8 signs, factions and dialogue.

The most informative first comparison blockout would contain one modest shared cottage, two unequal shop bays, the temple frontage, the 512-wide fountain and a short wall/gate segment. That exposes the domestic/fortified material relationship, ordinary door scale and shared frontage before extending the style across the city.

Rebuild this review with `python3 level_generation/scripts/compare_alvar_castleview.py` after updating the catalogue or MM5 reservations.
