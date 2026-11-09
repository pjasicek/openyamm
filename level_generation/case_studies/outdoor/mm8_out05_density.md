# MM8 Garrote Gorge: settlement density and enclosure

Focused native-data/visual supplement, not a replacement for a full map/event survey. Source: `mm8/out05.odm`, its
exported Lua house bindings and native terrain/tile records. See [measurement method and full comparison](../../SETTLEMENT_DENSITY.md).

The outer village sample has 17 physical residences with a median nearest-envelope gap of **895 units**. Geometry bases
range from **32 to 448**, consistent with its uneven ground. Houses form irregular open groups; intervening grass and
local paths are appropriate. Compound services should not set the outer village's layout rule.

The southern compound sample has **six surrounding service buildings**: magic shop (model 16, event 175), temple
(17/185), stables (18/181), weapon shop (19/171), armor shop (20/173), and inn (assembly 21+22, active event 191).
The keep (15) is a separate dungeon entrance (event 401; label 501), not a seventh ordinary residence. The training
building (54+55, active event 187) stands on the approach outside this service sample. Do not split these multipart
buildings when counting neighbors. Outer residence assemblies include 35+36, 37+38 and 39+40.

All six compound services have native geometry bases at **640**. Their median nearest-envelope gap is **896 units**,
but tall perimeter walls and the central keep contain the larger shared yard. Similar gap numbers do not mean this
space feels like the open village: enclosure, mass height and the purpose of the empty center matter.

![Native compound plan](../../projects/brackenford_greywatch/review/density_revision/garrote_service_compound.png)

There **are stone paths inside the walls**. Native raw tile IDs 198+ resolve through lookup bank 414 to the `drsr*`
road textures; raw IDs 1–9 include the ordinary dirt yard. The plan shows the gate approach and paths around the keep.
An assumption of a completely roadless training camp would be wrong.

![Game courtyard view](../../projects/brackenford_greywatch/review/gameplay/density_garrote_inner.png)

The keep at left, inn ahead and perimeter wall behind it enclose the yard. Stone paths occupy strips in a much wider
dirt surface. Borrow this arrangement for a fortified service compound; preserve a usable work/gathering space rather
than filling every gap with housing or vegetation. This is an interpretation supported by the visible arrangement,
not a statement of known author intent.

[Outer-village plan](../../projects/brackenford_greywatch/review/density_revision/garrote_outer_village.png) and
[raw membership/hashes/metrics](../../projects/brackenford_greywatch/review/density_revision/measurements.json).
