# Mine and three troll descents

These four existing reservations now have original source geometry. Each uses an asymmetric rock hood, a physical
recess, a supported walking apron and a dark clickable end. The mine adds two timber supports, a lintel and one
inert supply crate. The three troll sites retain separate source identities and unequal crown profiles; they do not
gain human furnishings or invented connecting tunnels.

The native terrain is unchanged. A BModel cannot cut a hole through that heightfield, so the troll treatment is a
shallow descent under a rocky cover: the approach rises gently to its lip and the interior descends 48 units.
The walking floor stays above the actual terrain throughout. Deeper shafts, falling behavior and BLV travel remain
deferred. This interpretation avoids visible grass through an open ring and does not strand the party in a pit.

| Site | Source destination | Geometry and future return |
| --- | --- | --- |
| Gemstone Mine | map 39 at (25,0) | Worked rock entrance; 288-unit recess behind the hood front. Keep a clear central passage between the timber supports. |
| Troll Hole west | map 40 at (3,3) | 224-unit shallow descent with an offset crown; voluntary descent and falling refer to the same source pocket. |
| Troll Hole east | map 40 at (9,3) | Separate descent with the higher left shoulder. |
| Troll Hole south | map 40 at (15,3) | Separate descent with its crown shifted further left. |

All four footprints remain within their original 768×576 local construction reservations. The apron begins six
units above native ground and the recessed floor retains at least eight units over its measured support maximum.
The mine's timber opening retains 256 units of headroom and width. Actual native walking, collision and visibility
still require gameplay checks; dimensions alone do not establish access.

[Source event evidence](natural_site_sources.json) preserves exact entry/return records. Each assembly also declares
an inactive return marker on its approach. Each recessed end has one explicit local placeholder venue; no NPCs,
monsters, travel or rewards are introduced. [venue_event_ids.json](venue_event_ids.json) freezes the existing venue
numbers and declares new ones, so adding natural contacts earlier in the inventory cannot renumber existing doors.

## Authoring and review

[prepare_natural_entrances.py](../prepare_natural_entrances.py) fits the entrance floors against native triangles.
[author_natural_entrances.py](../author_natural_entrances.py) creates all surfaces independently. Native Garrote
`T68A02A` rock and `solid01` recess materials follow the inspected Dragon Cave composition; no donor vertices are used.
The prior 240 OBJ files and the complete road specification are unchanged.

The first renders exposed open edges beneath the front rock shoulders and cropped crowns in eye views. Closed the
lower shoulders and moved the review camera back. Inspected repeated mine front/oblique, west oblique, east
front/oblique and south front/rear views. [Source review](../review/natural_entrances_v2/source_review.json) records
their image hashes. These views use actual terrain geometry with neutral ground, so they do not certify native
foliage/material context.

[review_natural_entrances.py](../review_natural_entrances.py) checks exported upward walking faces, grades, terrain
clearance, buried skirts/supports and actual native event bindings. The first native build passed all ten checks
with 252 BModels, 84 handlers and no actors/spawns. All four actual clicks work. Mine and west-troll entry, reload
and repeated longer backward exits are inspected; decoded saves retain map, gold, food, health and inventories.
[Native review](../review/natural_entrances_v2/native_review.json) records that evidence.

Those native views exposed conspicuous per-triangle texture restarts. Rock faces/floors now use a common local
dominant-axis UV projection; [repeated source views](../review/natural_entrances_v3/source_review.json) show the
correction. The fresh build passes all native checks; [all four repeated native views](../review/natural_entrances_v3/native_review.json)
show the correction. Eight rock/floor OBJ files changed; the previous 240 models and all four interaction caps remain
unchanged. This accepts the local UV correction only; broad countryside foregrounds and regional acceptance remain unfinished.
