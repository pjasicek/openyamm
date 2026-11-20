# Original barbarian camp

Status: corrected native cloth/bedding, fire animation/light, ordinary approach and real click/reload reviewed locally.

Retain source 7 (13,10), at (20736, 16128), with the original sprite-11 fire as the focal point. This camp is separate
from Yog's named contact. The future destruction/100,000-experience event remains deferred; no actors or encounters.

`prepare_barbarian_camp.py` places two unequal, differently angled cloth shelters behind an open southern approach.
`author_barbarian_camp.py` creates their timber frames, canvas covers, folded bedding, two inert supply crates and an
empty equipment rack. These are independently authored forms using existing MM8 timber/canvas/crate textures.
The [V2 study](../review/barbarian_camp_study_v2/source_review.json) follows a correction to V1's floating bedding;
all three repeated views were inspected. The original center and main approach stay clear.

The central `dec25` fire uses the Garrote Gorge `out05` entity 265 as its appearance reference: native descriptor 307,
sprite `DEC25A` and 128-unit descriptor light radius. `native_scenery.native_records` now accepts explicitly declared
light radii; its default continues to require inert, non-emissive records. Active fixed-scenery staging includes this
prop-owned fire at its original anchor, with the explicitly permitted dirt surface and descriptor light radius.

Native campfires belong to an interactive family. The fire's secondary event is assigned to the same authored camp
placeholder as its geometry, without creating a duplicate handler. `review_camp_pyramid.py` checks written binding,
ground contact, light/flags and the ten buried frame/rack feet during native build. The native review below establishes animation, light appearance and real fire dispatch; a first-frame Blender
preview alone does not establish these runtime results.

The [integrated source audit](../review/camp_pyramid_v1/source_review.json) records exact agreement with the accepted
V2 study, all 286 preceding model hashes unchanged and all 55 orchard identities retained. The new fire brings scenery
to 699 records. Its bedding is inert camp equipment, not an additional outdoor bed/service event.

The broad regional composition and final native acceptance remain pending.

[Native review](../review/camp_pyramid_v1/native_review.json) confirms a named fire click, food unchanged at 40,
visible animation and warm ground light. Exposed non-clock saved fields match after reload. The game view reveals
rigid-looking cloth panels and slab-like bedding; refine their fabric form and repeat affected views before accepting
the camp appearance. The original V2 source study did not expose this weakness as clearly as the native context.

The [V3 fabric study](../review/barbarian_camp_study_v3/source_review.json) now has sagging roofs, shallow curtain
pleats and thin blankets with rolled ends. All three repeated views were inspected and the exact OBJ integrated.
The other 287 referenced models remain unchanged. The [repeated native review](../review/barbarian_camp_v2/native_review.json)
now accepts the corrected front/rear appearance, ordinary approach, named fire click and reload. Food remains 40 and
all exposed non-clock saved fields match. Broad regional terrain and scenery remain unfinished.
