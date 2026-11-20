# All-outdoor decoration reference catalogue

Open [the interactive map and asset browser](index.html), or read
[the generation guidelines](../../OUTDOOR_DECORATION_CALIBRATION.md).

## Coverage and provenance

This survey includes every `*.odm` under the mounted MM6, MM7 and MM8 map directories:
15 + 13 + 14 = 42 maps. MM8's tutorial and exceptional planes are retained, not treated
as ordinary countryside density targets. Celeste and The Pit are BLV maps; they and
Plane of Earth are outside this ODM survey. No generated Brackenford/MM5 maps are pooled.

Inputs are the mounted native files plus scene overrides and merged decoration/frame
registries. All 42 entity-count/XYZ-coordinate multisets match the corresponding local
`reference/mmerge_data_forus/Data/mm*.games.lod` ODMs, including duplicate coordinates.
This establishes placement preservation against that reference, not retail event parity.
See each map's `reference_parity`, [source hashes](sources.json) and [validation](validation.json).

## Reading the measurements

- **Total records** include starts, sound markers, hidden entries and effects.
- **Visible** means an initially drawable sprite descriptor: nonzero sprite ID,
  no descriptor `DontDraw`, and no initial instance invisible bit. It is not a
  visibility-culling result or a post-load Lua simulation. Emitter-only effects are separate.
- **Descriptor IDs** are zero-based merged runtime indices. Names/aliases are resolved
  like `DecorationTable::resolveMapDecoration`; original raw indices alone are not reliable.
- **Central land** means nonwater cells in the ±24,576-unit analytical square, 96×96
  native cells. Shores and steep land count. This is neither the travel boundary nor
  proven walkability. Full-map records and buffers remain available in the browser.
- **Rate** is central-land visible anchors divided by central nonwater area, expressed
  per 4,096×4,096 units. It does not include water/outside-window anchors in the numerator.
- **Far %** counts central nonwater cell centres over 2,048 units from any initially
  visible decoration anchor (including anchors outside the window). The gentle-land
  counterpart restricts the sample to maximum native triangle grade ≤0.5.
- **Local counts** use aligned 2,048×2,048 bins. They are counts, not area-normalized
  density at coasts. A tiny flower and a large tree each count once.
- **Near a BModel** is XY distance to the nearest bounding rectangle; that model can
  be a cliff, boat, bridge or wall, not necessarily a house. No automatic town classifier.
- **Road/water proximity** is distance to source cell centres, not a traced path/shoreline.
  Road cells are recognised by native crossing/straight/cap/paired-diagonal texture suffixes;
  a plain-dirt footpath without road artwork is not detected. Read the terrain key too.
- **Roles** are analytical visual/use groups. Explicit appearance tags distinguish
  inspected bare/snow trees and container plants. They are not historical author metadata.
- **Previews** decode the first frame with palette/alpha and preserve frame scale in
  metadata. They do not simulate animation, lighting, seasons or quest changes.
- **Event 0** does not prove a decoration is inert. Native rules can supply behavior.
  `script_visual_change_calls` is a list of source references, not evaluated reachability.

The sprite inventory excludes actors, loose items, modeled props and embedded texture
detail. A zero-sprite map can still contain substantial architecture, landform and effects.
The schematic terrain backdrop is not an exact textured minimap or a water-depth model.

## Complete map inventory

| World | Map / source records | Context | Total | Visible | Types | Rate | Far % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| mm6 | [Sweet Water](maps/mm6_outa1.json) `outa1.odm` | blighted | 729 | 725 | 10 | 4.51 | 12.1 |
| mm6 | [Paradise Valley](maps/mm6_outa2.json) `outa2.odm` | lush highlands | 386 | 381 | 14 | 1.85 | 26.8 |
| mm6 | [Hermit's Isle](maps/mm6_outa3.json) `outa3.odm` | island | 345 | 341 | 10 | 2.38 | 12.1 |
| mm6 | [Kriegspire](maps/mm6_outb1.json) `outb1.odm` | highlands | 429 | 425 | 12 | 1.93 | 31.6 |
| mm6 | [Blackshire](maps/mm6_outb2.json) `outb2.odm` | dry settlement | 456 | 451 | 17 | 2.67 | 8.9 |
| mm6 | [Dragonsand](maps/mm6_outb3.json) `outb3.odm` | desert | 450 | 446 | 16 | 2.97 | 7.2 |
| mm6 | [Frozen Highlands](maps/mm6_outc1.json) `outc1.odm` | snow | 496 | 491 | 11 | 2.86 | 11.7 |
| mm6 | [Free Haven](maps/mm6_outc2.json) `outc2.odm` | temperate city | 461 | 455 | 16 | 2.78 | 8.1 |
| mm6 | [Mire of the Damned](maps/mm6_outc3.json) `outc3.odm` | haunted wetland | 464 | 460 | 19 | 3.28 | 9.2 |
| mm6 | [Silver Cove](maps/mm6_outd1.json) `outd1.odm` | coastal grassland | 522 | 519 | 15 | 4.87 | 1.7 |
| mm6 | [Bootleg Bay](maps/mm6_outd2.json) `outd2.odm` | tropical coast | 416 | 412 | 18 | 6.21 | 2.2 |
| mm6 | [Castle Ironfist](maps/mm6_outd3.json) `outd3.odm` | wooded highlands | 275 | 271 | 16 | 1.96 | 42.2 |
| mm6 | [Eel Infested Waters](maps/mm6_oute1.json) `oute1.odm` | islands | 176 | 173 | 14 | 3.79 | 6.2 |
| mm6 | [Misty Islands](maps/mm6_oute2.json) `oute2.odm` | island settlement | 157 | 156 | 12 | 3.9 | 7.3 |
| mm6 | [New Sorpigal](maps/mm6_oute3.json) `oute3.odm` | coastal village | 479 | 477 | 20 | 6.32 | 25.2 |
| mm7 | [Emerald Island](maps/mm7_7out01.json) `7out01.odm` | island village | 147 | 141 | 19 | 7.09 | 16.5 |
| mm7 | [Harmondale](maps/mm7_7out02.json) `7out02.odm` | temperate highlands | 568 | 564 | 21 | 3.94 | 21.6 |
| mm7 | [Erathia](maps/mm7_7out03.json) `7out03.odm` | temperate city | 547 | 523 | 27 | 4.03 | 30.9 |
| mm7 | [The Tularean Forest](maps/mm7_7out04.json) `7out04.odm` | forest | 469 | 465 | 21 | 4.55 | 23.8 |
| mm7 | [Deyja](maps/mm7_7out05.json) `7out05.odm` | necropolis | 284 | 282 | 10 | 2.11 | 52.1 |
| mm7 | [The Bracada Desert](maps/mm7_7out06.json) `7out06.odm` | desert city | 264 | 260 | 10 | 1.77 | 28.6 |
| mm7 | [Tatalia](maps/mm7_7out13.json) `7out13.odm` | wetland coast | 392 | 390 | 8 | 3.63 | 35.0 |
| mm7 | [Shoals](maps/mm7_7out15.json) `7out15.odm` | underwater | 3 | 2 | 2 | 0.01 | 98.9 |
| mm7 | [Evenmorn Island](maps/mm7_out09.json) `out09.odm` | ruined island | 374 | 371 | 21 | 9.47 | 5.9 |
| mm7 | [Mount Nighon](maps/mm7_out10.json) `out10.odm` | snow mountains | 236 | 235 | 12 | 1.73 | 53.5 |
| mm7 | [The Barrow Downs](maps/mm7_out11.json) `out11.odm` | burial landscape | 788 | 786 | 22 | 4.75 | 4.0 |
| mm7 | [The Land of the Giants](maps/mm7_out12.json) `out12.odm` | barren highlands | 384 | 383 | 18 | 3.52 | 37.4 |
| mm7 | [Avlee](maps/mm7_out14.json) `out14.odm` | forest coast | 188 | 184 | 20 | 1.97 | 60.9 |
| mm8 | [Plane of Air](maps/mm8_elema.json) `elema.odm` | air plane | 429 | 428 | 1 | 2.97 | 56.3 |
| mm8 | [Plane of Fire](maps/mm8_elemf.json) `elemf.odm` | fire plane | 1 | 0 | 0 | 0.0 | 100.0 |
| mm8 | [Plane of Water](maps/mm8_elemw.json) `elemw.odm` | water plane | 149 | 148 | 2 | 0.96 | 42.8 |
| mm8 | [Dagger Wound Island](maps/mm8_out01.json) `out01.odm` | tropical islands | 800 | 731 | 38 | 11.83 | 19.4 |
| mm8 | [Ravenshore](maps/mm8_out02.json) `out02.odm` | temperate city | 825 | 807 | 64 | 7.07 | 26.4 |
| mm8 | [Alvar](maps/mm8_out03.json) `out03.odm` | temperate city | 1043 | 1038 | 34 | 6.68 | 27.9 |
| mm8 | [Ironsand Desert](maps/mm8_out04.json) `out04.odm` | desert | 585 | 582 | 29 | 4.04 | 22.0 |
| mm8 | [Garrote Gorge](maps/mm8_out05.json) `out05.odm` | grass and dirt forts | 267 | 263 | 23 | 1.55 | 60.8 |
| mm8 | [Shadowspire](maps/mm8_out06.json) `out06.odm` | necropolis | 607 | 604 | 20 | 4.18 | 15.3 |
| mm8 | [Murmurwoods](maps/mm8_out07.json) `out07.odm` | forest | 1850 | 1847 | 23 | 10.08 | 10.6 |
| mm8 | [Ravage Roaming](maps/mm8_out08.json) `out08.odm` | dry grassland | 269 | 266 | 13 | 1.64 | 30.3 |
| mm8 | [Regna](maps/mm8_out13.json) `out13.odm` | tropical island | 447 | 446 | 23 | 6.55 | 13.0 |
| mm8 | [Tutorial](maps/mm8_out15.json) `out15.odm` | tutorial | 0 | 0 | 0 | 0.0 | 100.0 |
| mm8 | [Plane Between Planes](maps/mm8_pbp.json) `pbp.odm` | otherworld | 1 | 0 | 0 | 0.0 | 100.0 |

Totals: **18,158 records**, **17,929 initially visible sprites**,
**338 resolved descriptor identities**; all referenced sprite previews resolved.

## Files and regeneration

- [Map summary CSV](map_summary.csv): counts, rates, coverage and role totals.
- [Decoration × map CSV](decoration_usage.csv): every used descriptor and all its maps/counts.
- [Full inventory JSON](inventory.json): every placement, type and analytical measurement.
- `maps/`: individual reports with coordinates, geometry envelopes and event references.
- `sprites/`: palette-correct first-frame previews; `contacts/`: role contact sheets.
- `data.js`: local-file browser data, regenerated alongside the JSON.

Run from the repository root:

```sh
python3 level_generation/scripts/survey_outdoor_decorations.py
```

Requires PyYAML, NumPy, SciPy, Pillow and Matplotlib. This only writes reference evidence
under this catalogue. It does not edit maps, art, events or gameplay tables. Routine
generation should reuse the evidence rather than rerun the complete survey.
