# Four message bottles and the wreck

Status: four bottles and the wreck have local native visual and representative click/reload review.
The regional landscape remains unfinished.

The original sprite 7 is a green bottle with visible paper; sprite 5 is a broken wooden boat and mast. Their water
locations are meaningful. Preserve their source objects and deferred note/reward records while making local bank fits.
Do not create roads or long walkways to tiny river contacts.

| Source | Proposed center | Shift from source | Dry standing point |
| --- | --- | ---: | --- |
| 4 (2,2), Queen Kalindra note | −20032, −20736 | 704 east | −19712, −20736 |
| 4 (8,8), Xanthus invitation | −11520, −12096 | 576 south | −11520, −12416 |
| 7 (13,0), Lakeside plea | 20736, 1408 | 640 north | 20736, 1728 |
| 8 (7,15), rapids warning | 11520, −128 | 640 north | 11520, 192 |
| 4 (2,7), wreck | −20736, −13696 | 640 south | −20736, −14656 |

Each shift is less than half the 1536-unit original outdoor cell spacing. These retain the immediate source
neighborhood, although some cross a cell boundary. The original unshifted positions remain the source identities.
The wreck's proposed 448×1280 envelope straddles the southern bank: its bow reaches the source point, while the stern
at −20736, −14336 supplies a bank-side contact. Author a broken hull and mast, not a solid rectangular platform.

`study_waterside_features.py` writes only [the placement review](../review/waterside_placements_v1/source_review.json).
All five actual donor-bitmap diagrams were inspected. The source terrain, painted shore pixels and 96-unit dry standing
rings are recorded in [placements.json](../review/waterside_placements_v1/placements.json). The Xanthus bottle point
is in the painted shallows; the other three sit at the immediate dry/wet margin. Ground is unmodified.

This does not certify model scale, support, scenery clearance, collision, visibility or actual clicks. Check those
after authoring. Preserve the river setting without treating the western black void rim as finished landscape.
All future effects remain deferred; use named status-only handlers and no loose pickup/reward object.

## Authored bottles

`prepare_message_bottles.py` owns the four bottle fits; the placement diagram reuses them. `author_message_bottles.py`
creates a rigid eight-sided bottle resting on its side, with a tapered shoulder, open lip and hollow paper roll. The
44-unit body height and 150-unit overall length fit the small original water-contact identity. Explicit native-sized
`mm5glass.svg` (64×64) and `mm5paper.svg` (32×64) supply painted opaque glass and paper colors without transparency shaders.
Original source records and events 3006, 3011, 3016 and 3020 remain attached.

The [V3 study](../review/message_bottle_study_v3/source_review.json) follows two corrections: black gradient fills and
an unstable tilted pose in V1; unwanted inherited SVG outlines in V2. V3 uses explicit filled colors and a stable side
rest. Four individual views and the complete twelve-view contact sheet were inspected. All four integrated OBJ files
and both bitmaps match that study exactly, with the 277 preceding referenced models unchanged. The scenery refit
retains 698 sprites, fourteen prior moves and all 55 orchard identities.

`review_message_bottles.py` checks native face/event identities, edge grounding, 44-unit height, source displacement,
texture sizes and dry standing rings during the build. [Integrated source evidence](../review/message_bottles_v1/source_review.json)
records acceptance limits. The [native review](../review/message_bottles_v1/native_review.json) records all four
actual water-margin views and the Queen Kalindra bottle's named click/reload. Exposed health, inventory, gold and food
remain unchanged. The native audit confirms zero edge-ground gaps, the intended 44-unit body height and dry standing
rings. This accepts the local bottle forms; the black void rim, regional scenery and final landscape remain unfinished.

## Authored wreck

`prepare_wreck.py` owns the 640-unit local bank fit; the original source point lies at the bow. The bank-side stern
is 320 units from the dry standing point. `author_wreck.py` independently creates an open planked hull, two missing
strakes, exposed ribs, snapped mast and small torn sail. Existing `t06a10`, `t06c11` and `gnecclg2` textures supply
timber and cloth. This creates no boat interior, deck platform, loot or sinking effect.

The [repeated study](../review/wreck_study_v4/source_review.json) records V1's unsupported pieces, V2's corrected
supports/UVs, V3's removal of overlapping stern end caps and V4's narrower inner skin at the pointed bow. The final
474-face OBJ matches the integrated source exactly; all 285 preceding model hashes remain unchanged.
The [source audit](../review/wreck_v1/source_review.json) confirms clear approaches and unchanged scenery counts.
`review_wreck.py` checks the native binding, dry standing ring, stern contact and deliberately submerged keel.
The [native review](../review/wreck_v1/native_review.json) records inspected bank, shore, click, reload and wider
context images. The real stern click displays `Broken river ship: not implemented yet.`; exposed health, inventory,
gold and food remain unchanged after reload. The hull reaches the dry bank and its bow remains over water.
The regional landscape and black void rim remain unfinished.
