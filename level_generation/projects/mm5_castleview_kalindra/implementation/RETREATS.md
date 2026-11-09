# Countryside retreat exteriors

These are independently authored buildings and fittings using the established native Alvar/Garrote material palette.
The [layout](../layout.json), [resident inventory](../RESIDENTS.md), and [landscape contract](../LANDSCAPE.md) supply
their identities and geography. Forms and fittings are new design interpretations; no donor BModel geometry is copied.

| Place | Source contact and purpose | Exterior composition |
| --- | --- | --- |
| Reger's hermitage | Map 4, cell 1,4; Brother Reger, the final Drawkcab challenge | Small hipped dwelling on the original islet, east-facing door, wall-supported study ledge overlooking the south shore. The documented foundation is 448×384 in world axes, inside the 832×640 planning reservation. |
| Luna's sanctuary | Map 4, cell 13,15; Luna, animal healer and three-statuette quest | Unequal hut and low animal shelter, inert drinking trough, and a separate altar in the western clearing. Three shallow sockets remain empty. The source explains the missing statuettes; the props do not imply that the quest is already solved. |
| Vespar's retreat | Map 7, cell 7,1; Vespar, staff-handle quest and Sandcaster pass | Maintained cottage with a shallow entrance hood and a small original metal astronomical dial. No default guild or spell-shop service is introduced. |

Each contact retains one ordinary 128×256 entrance and its future occupant identity. Reger and Luna have 288-unit
eaves, providing clearance above their full-size doors. Vespar's main eave remains 320. The altar has a separate
named status-only interaction, event 1010. The trough and dial are inert. No NPCs, animals, quest items, rewards,
stat increases or new gameplay tables are created.

## Authoritative sources and rebuild

[prepare_architecture.py](../prepare_architecture.py) owns the component bounds, identities, props and material choices.
[author_retreats.py](../author_retreats.py) builds the original fittings and recessed altar, and
[author_architecture.py](../author_architecture.py) builds the houses and exports the editable scene/native inputs.
Follow [REBUILD.md](../REBUILD.md). For the dedicated Blender views use
`REVIEW_IDS: ['reger', 'luna', 'vespar', 'luna_altar']`.

Reger's earlier implementation specification incorrectly derived wall dimensions from the large planning envelope.
The correction uses `layout.json`'s explicit `foundationFootprint`, preserving the islet and its documented terrain
instead of enlarging the land. Its front moves 160 units west to match the smaller building. Both connecting bridges
remain required; visual inspection of the house is not proof of ordinary walking access to the islet.

## Review evidence and limits

The [placement audit](../review/retreats_v1/placement.json) samples footprint edges at native grid and triangle
breakpoints. All three main shells, Luna's shelter/trough and Vespar's hood/dial are on their flat pads. The altar's
ground spans Z 576–578 against its foundation bottom 544; its full base remains embedded.

Actually inspected the first Blender [Reger](../review/retreats_v1/reger_oblique.png),
[Luna](../review/retreats_v1/luna_oblique.png), [animal shelter](../review/retreats_v1/luna_side_yard.png),
[Vespar](../review/retreats_v1/vespar_oblique.png), and [altar](../review/retreats_v1/luna_altar_oblique.png) views.
The roofs have visible thickness, the doors clear their trim, and all three empty sockets are modeled recesses.
These neutral-ground views establish local form/material readability only. Native terrain, foliage, access and
interaction review remain separate requirements.

The scenery refit preserves all baseline identities. `luna_garden/010` moves from (-7120,8696) to (-7096,8755),
about 64 units, to clear the new altar; its original anchor remains in the generated scenery record. No new uniform
decoration scatter is added. The sanctuary's existing garden and grove must be reviewed together in the game.

Native build `883ce583bc6cb72e3e9d7606427d8a58c1b5b35d2e26d7229bf74b7e1a3c38ed` passed readback with
195 BModels, 73 distinct handlers and 40 supported main shells. Actually inspected real
[Reger](../review/gameplay/mm5_reger_door_v1_click.png), [Luna](../review/gameplay/mm5_luna_door_v1_click.png),
[Vespar](../review/gameplay/mm5_vespar_door_v1_click.png) and [altar](../review/gameplay/mm5_luna_altar_v1_click.png)
click screenshots; all show the matching named placeholders. Event collision checking caught an initial reuse of
south-gate event 1001 before export; the altar uses the independent 1010 binding.

The altar view revealed a nearby tree canopy obstructing the standing area. Added an explicit approach clearing;
`dark_grove/030` now moves from (-7152,8240) to (-7424,8512), retaining its source identity and material/group.
The repeated [same-pose altar click](../review/gameplay/mm5_luna_altar_v2_click.png) shows the unobstructed altar
and correct status feedback. The [sanctuary-side context](../review/gameplay/mm5_luna_context_v2.png) now shows
the cottage, altar and shelter together, and the [close trough](../review/gameplay/mm5_luna_trough_v2.png) shows
its recessed water and grounded sides/posts. [Capture provenance](../review/retreats_v2/native_review.json)
records native `1845ae6db8cb69b167c5bc67a9dc9ad31d45881c3b159ea0d953cb6b76aad5d9`.
Both connecting bridges now have [ordinary traversal evidence](BRIDGES.md), including arrival at Reger's door.
Vespar's [context](../review/gameplay/mm5_vespar_context_v1.png) shows
the maintained house and dial, with broad dirt foreground still awaiting the regional scenery pass.
