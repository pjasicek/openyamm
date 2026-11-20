# Castleview–Kalindra implementation architecture

This is the current Alvar/Garrote implementation assignment derived from the accepted goal.
It supersedes the earlier all-Garrote material assignment in the historical wireframe.
Locations, people, venue identities and source interactions remain grounded in `layout.json`.

The [structured specification](architecture.json) records every component footprint, roof form,
height, facade basis, transformed door, resident/venue ownership and actual texture source.
Geometry is newly authored. Reference mesh dimensions are comparisons, never scale instructions.

Facade planes start 32 units inside the planning envelope to reserve roof overhang; exact road
snapping and native terrain contact can require documented corrections during the blockout.
Natural sites retain specialist forms and receive no invented domestic building.

See [the specification audit](../review/architecture_specification/README.md) for retained identities
and [town detail completion](TOWN_DETAIL_COMPLETION.md) for remaining exterior work versus deferred interiors.

| Premises | Form | Material family | Eave / highest top above pad | Venues |
| --- | --- | --- | ---: | ---: |
| T01 Ol’ Black Magic | wing_hall | alvar_civic | 384 / 640 | 1 |
| T02 Ogre Foundry | workshop | alvar_domestic | 384 / 640 | 1 |
| T03 Tog’s Training / swimming annex | institution | alvar_institution | 448 / 512 | 2 |
| T04 Castleview Jail | fortified_hall | garrote_jail | 640 / 768 | 1 |
| T05 First Drawkcab chapterhouse | long_hip | alvar_domestic | 256 / 448 | 1 |
| T06 Drawkcab study house | long_hip | alvar_domestic | 256 / 384 | 1 |
| T07 Milken Savings / accounts | paired_frontage | alvar_civic | 384 / 576 | 2 |
| T08 Blacksmoke Tavern | wing_hall | alvar_domestic | 448 / 704 | 1 |
| T09 Adventurers’ lodging | gable_hall | alvar_domestic | 384 / 640 | 1 |
| T10 Mapmakers’ court | wing_hall | alvar_domestic | 384 / 640 | 3 |
| T11 Mayor’s office and editorial room | civic_wing | alvar_civic | 448 / 704 | 2 |
| T12 Taskmaster’s hiring office | workshop | alvar_domestic | 256 / 448 | 1 |
| T13 Joe’s map stall | canopy | alvar_domestic | 240 / 304 | 1 |
| T14 Goldur’s lodge | hip_cottage | alvar_domestic | 256 / 448 | 1 |
| T15 Zelda’s house and drying shed | cottage_shed | alvar_domestic | 256 / 448 | 1 |
| T16 Nadia’s house | hip_cottage | alvar_domestic | 256 / 384 | 1 |
| T17 Oorla’s house / Troyanna’s room | gable_hall | alvar_domestic | 320 / 512 | 1 |
| T18 Gremlin court | fortified_hall | garrote_fortified | 704 / 896 | 1 |
| T19 Ellinger’s Tower | arcane_tower | alvar_civic | 2304 / 3072 | 1 |
| T20 Temple of Mok | apsed_hall | alvar_temple | 704 / 1024 | 1 |
| T21 Tailor and cobbler row | paired_frontage | alvar_domestic | 320 / 512 | 2 |
| T22 Workers’ shared house | long_hip | alvar_domestic | 256 / 384 | 1 |
| T23 Keeper’s cottage and kennel | cottage_shed | alvar_domestic | 256 / 448 | 1 |
| T24 Dyson’s public storehouse | institution | alvar_domestic | 512 / 704 | 1 |
| R01 Dreyfus’s refuge | canopy | camp_equipment | 288 / 352 | 1 |
| R02 Linus’s ruby workshop | workshop | alvar_domestic | 352 / 512 | 1 |
| R03 Simon’s emerald workshop | workshop | alvar_domestic | 352 / 480 | 1 |
| R04 Toby’s sapphire workshop | workshop | alvar_domestic | 352 / 512 | 1 |
| R05 Hector’s diamond workshop | workshop | alvar_domestic | 352 / 512 | 1 |
| R06 Brother Reger’s hermitage | hip_cottage | alvar_domestic | 288 / 416 | 1 |
| R07 Falista’s sanctuary | sanctuary | alvar_domestic | 0 / 0 | 1 |
| R08 Luna’s animal sanctuary | cottage_shed | alvar_domestic | 288 / 416 | 1 |
| R09 Justine’s gate-side shelter | canopy | camp_equipment | 256 / 288 | 1 |
| R10 Yog’s Sardaj camp | canvas_camp | camp_equipment | 0 / 432 | 1 |
| R11 Vespar’s retreat | hip_cottage | alvar_domestic | 320 / 512 | 1 |
| R12 Kramer’s caravan yard | caravan_yard | camp_equipment | 256 / 392 | 1 |
| R13 Nibbler’s clearing | natural_shelter | alvar_domestic | 0 / 0 | 1 |
| R14 Castle Kalindra | royal_keep | kalindra_royal | 3424 / 3584 | 1 |
| R15 Great Western Tower | watch_tower | garrote_fortified | 2432 / 2816 | 2 |
| R16 Gemstone Mine entrance | rock_portal | natural_entrances | 310 / 518 | 1 |
| R17 Troll Hole west | descent_rim | natural_entrances | 354 / 562 | 1 |
| R18 Troll Hole east | descent_rim | natural_entrances | 332 / 540 | 1 |
| R19 Troll Hole south | descent_rim | natural_entrances | 358 / 566 | 1 |
| R20 Riverside sewer outfall | masonry_drain | sewer_masonry | 160 / 384 | 1 |
| R21 Dark Grove Skyroad rope | rope_anchor | skyrope_timber | 400 / 744 | 1 |

## First visual checks

Review guild, forge, training hall, one modest shared home and the fountain court with the south gate.
Keep ordinary door panels 128×256 and facade modules at one native unit per texel. Inspect matching
front/oblique and player-height views; correct the largest discrepancy before repeating the kit.
Alvar civilian materials and Garrote fortifications must also be reviewed together in native lighting.

## Rebuild

From the repository root:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/prepare_architecture.py
```

This regenerates the implementation specification only. It does not regenerate the historical
wireframe, copy native geometry or claim native/runtime completion.
