# Northern gemsmith workshops

These are the four separate source premises recorded in [resident assignments](../RESIDENTS.md) and the
[Garrote comparison](../GARROTE_STYLE_MAPPING.md). Positions retain the landscape's earlier 256-unit landward
adjustments, which give the buildings complete dry support triangles. No further position change is introduced here.
The Alvar domestic material family connects these small workplaces to Castleview's civilian architecture.

| Premises | Future contact | Exterior composition | Deferred source service |
| --- | --- | --- | --- |
| Ruby | Linus | Broad hall, left rear sorting canopy, red painted emblem | Five stones and 100 gems |
| Emerald | Simon | Long hall, right rear sorting canopy, green emblem | Five stones and 200 gems |
| Sapphire | Toby | Long hall, full-width rear loading/sorting canopy, blue emblem | Five stones and 400 gems |
| Diamond | Hector | Broad hall, right rear sorting canopy, pale emblem | Five stones and 1,000 gems |

All four retain independent stable venue IDs and ordinary 128×256 door panels. Recipe cost does not justify an
invented mansion, extra service, shared recipe or new resident. The source contacts remain planning identities;
none are instantiated as actors or NPC dialogue rows.

Each covered bench holds two small trays: rough stone and colored sorted stock. A small shipping crate sits beneath
the bench, between its legs. These are newly authored BModel geometry with no inventory or container behavior.
The four editable 64×64 SVG trade signs are original painted emblems, rasterized at native size; neither AI upscale
nor donor BModel copying is involved. They identify the trade without putting implementation text on the facade.

The exterior uses the decoration calibration's working-yard vocabulary: readable architecture, covered work surface,
bounded stock, and open standing/loading ground. Keep the surrounding northern shelf sparse; a garden border at each
workshop is not warranted. The [placement record](../review/gemsmiths_v1/site_placement.json) lists nearby current
scenery and exact terrain support. Counts alone do not approve the region's final visual composition.

The first [ruby frontage](../review/gemsmiths_v1/ruby_eye.png) exposed the sign top behind the roof fascia.
Raised the eaves from 320 to 352, retaining door size and roof apex; this leaves 16 units between the sign and fascia.
Inspected the repeated [ruby frontage](../review/gemsmiths_v2/ruby_eye.png),
[emerald oblique](../review/gemsmiths_v2/emerald_oblique.png),
[sapphire frontage](../review/gemsmiths_v2/sapphire_eye.png) and
[diamond frontage](../review/gemsmiths_v2/diamond_eye.png): the signs are clear of the roof trim.
Repeated native [ruby](../review/gameplay/mm5_ruby_door_v3_click.png),
[emerald](../review/gameplay/mm5_emerald_door_v3_click.png),
[sapphire](../review/gameplay/mm5_sapphire_door_v3_click.png) and
[diamond](../review/gameplay/mm5_diamond_door_v3_click.png) door clicks show the four unobstructed signs and the
correct individual placeholder text. These use native `bc64ac04c537eec2938ecace411b4802115ca6495a841340e2d301c9b69e9820`.
Inspected native sorting-yard views for [ruby](../review/gameplay/mm5_ruby_yard_close_v3.png),
[emerald](../review/gameplay/mm5_emerald_yard_close_v3.png),
[sapphire](../review/gameplay/mm5_sapphire_yard_close_v3.png) and
[diamond](../review/gameplay/mm5_diamond_yard_close_v3.png). Roof undersides, supports, stock trays and shipping
crates are visible and meet the local ground. The first distant ruby yard view looked almost along the sloping roof;
the closer side view reveals its underside. These views establish local geometry/material contact, not the final
region-wide scenery composition or all possible movement paths.

Native readback also exposed a truncated sapphire material key: `mm5sapphire` became `mm5sapphir` in the ten-byte
ODM texture-name field. The canonical source key is now `mm5saph`; no truncated-name alias is introduced.
The builder now rejects overlong keys before export and compares all written BModel material names with source,
normalizing legacy casing in the same way as asset lookup. The original
[readback defect](../review/gemsmiths_v2/material_name_defect.json) is retained for review.
The [native missing emblem](../review/gameplay/mm5_sapphire_material_defect_v2.png) shows only the wooden backing;
the repeated sapphire click above shows the restored blue emblem. The corrected build passes the new material check
for every BModel, not just the sapphire workshop.

The first native [ruby approach](../review/gameplay/mm5_ruby_context_v1.png) and
[emerald approach](../review/gameplay/mm5_emerald_context_v1.png) establish their dry shoreline setting, modest scale
and separation. These use the earlier clipped-sign export. The broader grass foreground is still sparse, and the
ordinary blue water does not yet establish Acid Pond's final identity. Preserve these as explicit remaining regional
composition/material work, rather than accepting the whole landscape from these architectural views.

Sources: [specification author](../prepare_architecture.py), [workshop details](../author_workshops.py),
[geometry author](../author_architecture.py), and the SVG files under `art/`.
