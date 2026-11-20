# House repetition and variety calibration

Count a physical architectural form once regardless of cardinal rotation or source suffix. Count an assembled
service block once even when several BModels/doors form it. A material tint or small size adjustment does not
automatically create another form. This is an architectural classification, not a byte-identical mesh count.

| Category | Ravenshore | Revised Brackenford |
| --- | --- | --- |
| Ordinary residence / teacher / storage instances | 44 | 20 |
| Repeated ordinary forms | 13 | 5 |
| Ordinary instances per form | 3.38 | 4.00 |
| Land house/service destinations | 59 | 29 |
| Physical house/service assemblies | 51 | 28 |
| Whole-building architectural forms | 20 | 10 |
| Physical assemblies per form, including landmarks | 2.55 | 2.80 |

Ravenshore has 45 House-type destination records: 44 ordinary house/storage instances plus the unique Oracle.
Its other 14 land destinations are services. Two boat destinations are excluded. Six dungeon exterior complexes
are also excluded from the house ratio. Their BModel part counts are not house counts.

The 51 physical assemblies are 44 ordinary houses, Oracle, Sanctum, Dancing Ogre, Adventurer’s Inn and three
joined service blocks (north-east, north-west, south-east). The latter seven add seven distinct whole-building
compositions to the 13 ordinary forms. The Merchant House south-west block is a dungeon exterior.

Brackenford has 29 logical service/resident doors in 28 physical buildings/blocks.
Weapon and armor shops share Smiths Row. Ordinary roles come from the house registry, excluding the civic manor;
this includes the five added court/well-lane homes. Services reuse some ordinary forms and add landmark compositions.
The driver accepted this infill revision. Use [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md) for future maps;
the earlier facade-stage 15/5 ratio remains historical evidence, not the current count or an exact quota.

## Native repeated forms

| Form | Instances | BModels |
| --- | --- | --- |
| `delf_med1` | 4 | [14, 15, 17, 19] |
| `delf_med2` | 1 | [30] |
| `delf_poor1` | 6 | [9, 22, 23, 24, 26, 32] |
| `delf_poor2` | 3 | [38, 39, 58] |
| `delf_poor3` | 1 | [33] |
| `delf_rich1` | 3 | [40, 41, 42] |
| `delf_rich2` | 4 | [43, 44, 45, 89] |
| `dock_wh2` | 2 | [13, 18] |
| `hcleric_med1` | 4 | [34, 35, 36, 37] |
| `hcleric_poor1` | 8 | [10, 12, 16, 21, 25, 28, 29, 31] |
| `hcleric_rich1` | 2 | [61, 62] |
| `ogre_med1` | 3 | [8, 59, 60] |
| `ogre_poor1` | 3 | [11, 20, 27] |

## Generated repeated forms

| Form | Instances | Buildings |
| --- | --- | --- |
| `barn` | 3 | warehouse_1, warehouse_2, court_west_long |
| `flat` | 5 | teacher_2, resident_1, resident_5, residence_7, court_west_small |
| `gable` | 6 | teacher_1, teacher_4, resident_3, residence_8, well_lane_cottage, court_east_small |
| `hipped` | 5 | teacher_3, resident_4, resident_6, residence_9, court_south_long |
| `turret_house` | 1 | resident_2 |

## Apply to future generation

Choose a reference settlement and report both ordinary-house repetition and whole-building/service composition.
For a comparable Ravenshore-like brief, roughly three to four ordinary houses per recurring form is a useful start,
with several common forms and a few rarer ones. The reference and accepted example are evidence, not universal quotas.
Make landmarks and joined service blocks deliberate exceptions. Preserve a coherent texture kit and measured
facade scale across variants. Inspect a street and a town overview: a ratio alone cannot establish visual quality.
Do not count a changed rotation, extra chimney, window decal or arbitrary material swap as useful architectural variety.

[Catalogue](catalogues/mm8_ravenshore/README.md) · [Calibration](VISUAL_CALIBRATION.md) ·
[Current measured membership](projects/brackenford_greywatch/review/house_variety/house_variety.json)

Regenerate with `python3 level_generation/scripts/measure_house_variety.py`. Sources are the Ravenshore catalogue
and current `outdoor_plan.json` plus `source/town_registry.json`; native families and semantic IDs make counts reviewable.
Historical facade evidence remains in the project’s `review/facade_revision/house_variety.json`.
