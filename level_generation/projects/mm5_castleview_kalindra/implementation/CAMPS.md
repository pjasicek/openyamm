# Temporary countryside sites and caravan yard

Four existing reservations receive original temporary construction. Source residents remain attached to their single
venues, with no actors or service implementation. Garrote tent part 7 was inspected for material roles and scale;
no donor vertices are imported. Its `GNecClg2` canvas and 32×32 `t06a10`/`t06c11` timber textures are reused at native
texel scale. Existing metal and crate artwork supplies the equipment. No upscaling or new global gameplay table is needed.

| Site | Ground / highest geometry | Construction and interaction |
| --- | --- | --- |
| Dreyfus's refuge | Z1056 / 352 above pad | Open cloth shelter with rear/side windbreak, travel packs, folded bedding and a book at a low contact counter. Dreyfus remains the displaced priest associated with Western Tower access. |
| Justine's shelter | Z608 / 288 above pad | Smaller open cover, rear windbreak and packed belongings. The contact counter stays outside the pass checkpoint; the pass purchase is deferred. The old 192-unit cover proposal was raised to provide usable headroom. |
| Yog's camp | Z1152 / 432 above pad | Enclosed cloth tent with a normal 128×256 flap, fitted guy ropes, packed supplies and a cold cooking tripod. Tribal negotiation, hostility and food rewards remain future records. |
| Kramer's caravan yard | Z1152 / 392 above pad | New covered wagon with four spoked wheels, axles, sideboards, three roof hoops and folded shafts. A low loading counter and supplies preserve the clear front approach. The caravan quest does not create scheduled travel. |

Each assembly adds three BModels: principal structure, supplies, and its explicit interaction surface. The wagon's
complete wheel/shaft envelope fits the existing 768×576 reservation. Its tires have radius 88, centered 88 above
the flat pad; they touch ground without lifting the body artificially. No pad, road or neighbouring building is moved.

The existing semantic venue IDs remain `mm5:sw/<site>/entrance`. Dreyfus, Justine and Kramer use a visible 256-wide,
96-high counter rather than a freestanding fake house door. Yog's flap lies four units outside the tent front, with
its semantic position adjusted accordingly. Hover/click labels identify each venue. All behavior is a named local
status stub; resident, item, faction, quest and service effects remain deferred.

## Sources and visual corrections

[prepare_camps.py](../prepare_camps.py) defines forms, heights, surface kinds and the restricted palette.
[author_camps.py](../author_camps.py) creates the geometry through the shared project author. Camps are included in
its default selection. The twelve added models leave all 228 earlier OBJ files unchanged.

Actually inspected the first oblique views of all four sites, Dreyfus's eye view, Justine's rear, Yog's front and the
wagon rear. Coplanar opposing canvas faces made the tent ends, wagon end and refuge side screen black. Gave those
surfaces physical thickness, fitted the tent's guy ropes to the actual sloping canvas, and closed the wagon's gap
between the cover and sideboards. The repeated `review/camps_v2/` views show those corrections. Yog's first eye
camera also cropped the ridge; the repeated view includes the complete tent and cooking group.

The tent front uses explicit convex pieces around its ordinary flap for native export. The flap is slightly proud
of the front cloth, with its own closed thickness. Its final affected views are in `review/camps_v3/`.
These render directories use actual heightfield geometry with neutral ground material, not native foliage or lighting.

[review_camps.py](../review_camps.py) verifies actual exported shelter/frame/stake/tripod/counter feet, supply bases,
wheel tread contacts, resident assignments and event bindings. The normal foundation audit deliberately excludes
open shelters and wheeled structures; it does not pretend they have house skirts.

The native checkpoint has 240 BModels, 80 handlers and no scene actors or spawn records. All 37 camp support checks
and four venue bindings pass. [Native review](../review/camps_v2/native_review.json) records inspected player-height
views and actual clicks on all four venues. Dreyfus's clear approach permits ordinary movement under the cover;
F9/F10 restores that interior viewpoint and Kramer's counter viewpoint. Decoded before/after map, gold, food,
held item, health and inventories remain unchanged. Full native context views show the tent/tripod and wagon/wheels.
The isolated [starting save](../review/playtest/start_camps.json) matches this checkpoint.

This is local geometry and interaction evidence. Broad bare foregrounds, regional scenery and distant terrain joins
remain unfinished; these captures do not establish whole-region visual acceptance or an exhaustive collision sweep.
