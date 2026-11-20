# Five ordinary Castleview chests

Status: all five native appearances and grounding/binding checks pass; a representative real click and reload are reviewed.

These five exterior contacts retain their original town coordinates, source sprite-15 object identities and separate
future loot records. The eighteen puzzle chests remain deferred with the interiors. No rewards are implemented.

| Town cell | Center | Facing | Local event |
| --- | --- | --- | --- |
| 29 (10,29) | −804, −4058 | North | 3023 |
| 29 (10,30) | −954, −4608 | North | 3024 |
| 29 (11,29) | −1204, −4008 | North | 3025 |
| 29 (18,30) | −4704, −5108 | East | 3027 |
| 29 (20,11) | −5054, 1792 | West | 3028 |

`prepare_town_chests.py` retains all five centers and reserves clear interaction standing points. The chest beside
the mayor faces east; the northern chest faces west. Footprint checks include the front hasp and rear hinges.
Four short feet meet the native grade without floating a broad bottom surface. The smallest building clearance is
36 units; a standing reserve alone does not establish final game access.

`author_town_chests.py` creates original 192-unit timber bodies, curved lids, iron straps, hinges and hasps using
`t06a10`, `gn_mtl03` and `solid01`. Curved timber UVs continue along the lid arc at native texture scale. No donor
BModel is copied. All faces dispatch the chest's distinct map-local status handler; there is no opening animation,
native loot container, item grant or depletion state in this milestone.

The [source review](../review/town_chests_v1/source_review.json) and
[ten-view contact sheet](../review/town_chests_v1/contact_sheet.jpg) record the inspected geometry and provenance.
Five new OBJ files are added; the concurrent West Gate sewer fix changes one prior OBJ, while the other 261 remain
unchanged. Scenery refitting retains all 698 baseline identities, 55 orchard records and ten previous moves.

`review_town_chests.py` runs after native export and checks written face bindings, materials, four grounded feet,
body clearance, sprite approaches and empty native loot state. The
[native review](../review/town_chests_v1/native_review.json) shows the three grouped chests near the south wall and
both individual side-house sites. The mayor-side chest displays its named status and remains closed after click/reload;
the exposed save fields are unchanged and no native chest container is materialized. This local review does not
complete the surrounding service-yard and street composition.
