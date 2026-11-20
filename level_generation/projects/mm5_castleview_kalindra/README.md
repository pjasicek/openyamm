# Castleview–Kalindra: source-backed minimap and settlement layout

The [implementation goal](GOAL.md) is complete: the native outdoor environment in a prepared
MM5 world, with door/prop Lua placeholders and no NPCs, monsters or encounters. It supersedes the earlier partial-sample
and gameplay-integration completion proposals below. All five milestones passed; see
[current checkpoint and visual corrections](PROGRESS.md), [consolidated acceptance evidence](COMPLETION.md),
[rebuild instructions](REBUILD.md) and [isolated delivery instructions](DELIVERY.md).

The [geometry simplification](GEOMETRY_SIMPLIFICATION.md) removes 3,742 triangles while preserving the reviewed forms,
with [before/after native views](review/geometry_simplification_v1/index.html). The
[original geometry audit](GEOMETRY_COST_AUDIT.md) retains the baseline measurements and MM8 comparisons.

Run [play.sh](play.sh), then **Load Game → castleview_start**. The launcher prepares the accepted release under
`local_playtest/` on first use, using the current development executable and asset base. Settings and saves persist
inside this project across `/tmp` cleanup. Run `./play.sh --restage` to refresh copied assets and composed registries
after base-content changes; private saves/settings are preserved and the previous installation is backed up.

[Heightmap and decoration review](landscape/index.html) · [Landscape details](LANDSCAPE.md) · [Garrote architectural mapping](GARROTE_STYLE_MAPPING.md) · [Visual Garrote catalogue](../../catalogues/mm8_garrote_gorge/index.html) · [Open the interactive wireframe](index.html) · [Town PNG](castleview_wireframe.png) · [Region PNG](region_wireframe.png) · [Original MM5 town](../mm5_world_feasibility/plans/029.png) · [Complete residents/venues](RESIDENTS.md) · [Structured plan](layout.json) · [Checks](verification.json)

This is the first detailed **SW surface region** in the six-region MM5 land-world proposal: original A3, A4, B3, B4 and
the embedded city of Castleview. The linked wireframes and [landscape design](landscape/index.html) are source planning
views. The complete native ODM and isolated MM5 installation are delivered under the implementation goal;
[launch the accepted release](DELIVERY.md). The other five surface regions remain at the [world-layout study](../mm5_world_feasibility/world_layout/index.html)
stage. The historical gameplay proposals below remain future design records: the current goal keeps gates open,
uses a friendly restored Kalindra exterior and permits only status placeholders.

The [Alvar catalogue](../../catalogues/mm8_alvar/index.html) supplies a second complete architectural reference. The
[Alvar versus Garrote comparison](ALVAR_STYLE_COMPARISON.md) informed the current Alvar civilian / Garrote fortified
assignment in [implementation/ARCHITECTURE.md](implementation/ARCHITECTURE.md). The historical all-Garrote mapping is
retained as design evidence.

Regional minimaps show only the ±24,576 travel envelope. The [full terrain authoring view](landscape/buffer.html) separately shows the outer scenery buffer, sampled from adjoining A2/B2/C2/C3/C4 geography. Acid Pond and the river continue across their travel boundaries; the western/southern rim continues as void. See [buffer coordinates and overlap rules](LANDSCAPE.md#playable-crop-and-outer-scenery-buffer).

The plan accounts for **48 original NPC locations, all six standard services, 218 spatial event sites and 1,408 spatial event records**. There are **24 proposed physical town assemblies** and 21 regional destinations; those regional destinations include caves, a rope, a drain, a camp and natural sanctuaries, not 21 more houses. Every original NPC has a building, venue or explicitly public/restricted location. None is silently discarded to make the town smaller.

## People, houses and buildings are three different counts

The native MM8 audit follows event-bearing BModel faces to `EnterHouse`, then joins the unique house destination to NPC table column 6. Proprietors are recorded separately. It measures the supplied merged base's initial NPC assignments, not simultaneous occupancy after all quest scripts have run. Conditional Merchant House rooms are separate destinations; those explain why this census need not equal an earlier hand-selected count of ordinary houses.

| Reference | Destinations with NPC rows | One NPC | Two NPCs | NPC rows total |
| --- | ---: | ---: | ---: | ---: |
| Ravenshore | 43 | 41 | 2 | 45 |
| Garrote Gorge | 17 | 13 | 4 | 21 |
| Proposed Castleview ordinary NPC venues | 24 | 17 | 7 | 31 |

Ravenshore has 61 house destinations in the static face/event audit, including 18 with no NPC-table occupants; Garrote Gorge has 24, including seven with no NPC-table occupants. A zero does **not** mean an empty service: its proprietor can come from the house table instead. The recorded Ravenshore assemblies include one three-destination block and two four-destination blocks. Garrote's audited assemblies each have one destination. Membership, NPC names, source lines and hashes are in [reference_occupancy.json](reference_occupancy.json).

The Castleview distribution deliberately sits closer to Garrote's shared residences than to Ravenshore's many single-NPC destinations. Its seven paired venues are two Drawkcab houses, the keeper's house, workers' lodging, diviners' rooms, tavern contacts and adventurers' lodging. This is a modest adaptation, not an attempt to put six unrelated characters behind every door. Jethro/Lydia/Miles, bank/accounts, mayor/editor and tailor/cobbler share **physical assemblies while keeping separate destinations**.

The other four Castleview NPCs are two public contacts (Nool and Ben) and two restricted contacts (Jasper and Gettlewaithe). Thus 31 + 2 + 2 = all **35 original urban NPC sites**. Thirteen more NPC sites remain in the countryside. An additional [23 interior contacts/services](interior_contacts.json) are mapped to the attached BLV complexes, including three more teachers: Felix (Direction Sense), Errol (Arms Master) and Gem (Danger Sense). Ellinger and Kalindra's court stay inside their original tower/castle complexes; they do not inflate the outdoor census. The source's six service functions remain identifiable even when sharing premises with a teacher or resident.

## What the minimap proposes

The common regional travel envelope is 49,152 units wide: ±24,576, inside the larger native 128×128, 512-unit terrain grid. The source 32×32 regional patch supplies geographic relationships and watercourses, not a scale for an individual town house.

Castleview expands into the grassland **north of the existing southern river**. Its internal district arrangement is turned 180° so the original entry end faces the southern trade road. This is a deliberate adaptation: north in both review sheets is true proposed world north. The old outer gate alias A4(14,10) maps to the new south gate, while original 32×32 urban coordinates remain attached to each person and interaction. It is not a claimed reproduction of the source compass orientation.

The source city's broad relationships survive the rotation: guild/training/forge and jail occupy one side; the human/contact quarter and mapmakers occupy the other; the monks sit between these; temple, public storage puzzles and Ellinger are farther from the entrance; the Gremlin court remains a distinct enclave. Streets are re-authored around correctly sized premises, not copied as 32 equal blocks.

- The regional trade road links the Western Tower, Kalindra approach, Castleview gate and eastward travel. It skirts the expanded town. The northern regional exit remains **off-road**. Travel-day values remain unassigned; inventing them would obscure the scale decision.
- The town has a bending main street, an unequal western loop, a larger human-quarter loop, a smaller temple/craft circuit, and short working lanes. Separate hiring and storage courts serve real activities. Diagonal stretches are intentional; native road-bank painting follows the Brackenford diagonal/corner calibration later.
- A second, smaller **west gate toward Kalindra** links the human quarter to the outer trade road through the gap between Nadia and Zelda. Its 384-unit lane preserves the existing building positions. Both gates check the same Castleview pass; Justine remains outside the south gate. This is an explicit accessibility adaptation, not an extra original MM5 entrance.
- Kalindra remains a western landmark with a restoration-dependent entrance and a clear forecourt. Its first exterior is not a fully restored castle regardless of quest state.
- The four gemsmiths stay outside town in a staggered northern cluster. Their four recipes and costs remain distinct. Dreyfus keeps a temporary refuge near the Western Tower.
- Luna moves north of the enlarged city to avoid putting her animal sanctuary inside the street grid. Justine moves just outside the new pass gate. The sewer outfall moves to the adjacent riverbank. Original aliases and proposed coordinates are both retained.
- Reger, Falista, Nibbler, the mine, troll holes and quest-food patches keep countryside roles. They do not acquire long road spurs merely because they are quest locations.

The rectangles are **conservative physical envelopes**, including planned roof/step space, not final rectangular buildings. Each record specifies a compact, long, L-shaped, hall, octagonal or compound form and its architectural role. Joined buildings have multiple reserved thresholds in `venues`; the diagrams show those thresholds. Ordinary doors stay 128×256. A higher-status institution gets a different assembly, material treatment and height hierarchy rather than an enlarged door.

Current town checks give **488 units median nearest-envelope gap**, **1,725 units median nearest-center distance**, approximately **31% coverage of the collective building-envelope hull**, and approximately **430 units median primary-door distance to the road centerline**. This is a compact town, near the measured Ravenshore market's 30% envelope coverage. These are planning-envelope comparisons, not measurements of exported collision geometry. All 24 building envelopes lie inside the proposed wall and clear its 256-unit curtain strip. Building envelopes and authored road strips are mutually clear; primary approaches leave the correct face and do not cross another building.

## Terrain, water, planting and decoration

Source water cells are retained in the regional diagram. The northern Acid Pond, the southern winding river and the black world rim are distinct. The black rim is **the edge of Xeen, not a surrounding ocean**. No lake, port or volcano has been invented here.

Two water-related additions are explicitly design choices:

1. A small **896×512 teaching basin** beside Ordana's training premises. It is a working teaching space, not a new natural lake or a healing source.
2. A **north–south footbridge** over the western river reach, allowing a conventional MM6–8 party to reach the southern meadow. This replaces neither the whole river nor its original encounters. Its complete deck footprint has now been sampled against the quantized heightfield; final abutments and bank ramps remain geometry work. It also makes the unresolved MM5 Swimming-to-MM6–8 mechanic conversion visible rather than pretending that original traversal works unchanged.

Use the existing calibrated temperate ground palette (`grastyl`, `grastyl2`, `dirttyl`), Ravage Roaming-style exposed dirt/rock on the northern/eastern shelves, and the native water family. The source's harmful pond needs a distinct effect/shore treatment; do not turn all blue water into damaging terrain. Final four-bank terrain allocation is still a native-authoring step.

Twelve bounded planting groups select real names already used in Brackenford: trees `tree10`–`tree13`; low plants `plant17`, `plant19`, `plant21`, `plant23`, `plant26`, `plant27`, `plant32`; rocks `rock01`, `rock02`, `rock05`, `rock20`. The groups have centers, extents, target counts, purposes and exclusion rules. The [landscape pass](LANDSCAPE.md) resolves these budgets into individual points with native-triangle Z, visual-crown, route, building, water and wall exclusions. Three cosmetic groups initially fit fewer placements than requested; the report preserves requested and accepted counts. Final mesh/billboard collision remains an in-engine check. Dark Grove, the troll-hole forest, dry northern shelves, southern meadow and town working gardens receive different treatments. No evenly spaced ring of trees and no uniform ground-cover carpet.

Each town assembly has a functional prop list: guild notice board, forge material bins, hiring board, map racks, herb drying beds, kennels, separate study stations, accounting desks, shared lodging and named benches. The original bed/tree/food/reward interactions retain distinct source identities and assigned premises. A public orchard terrace behind the temple holds all 55 original tree sites (30 ordinary, 13 reward-bearing, 12 food trees); these are included in its planting budget, not added a second time. The 11 beds are assigned explicitly to prison, boarding and civic/mapmaking rooms. The 55 orchard trees now have individual source-bound landscape positions. Bed coordinates still come with room authoring; the plan does not confuse all 66 furnishing triggers with separate buildings or generic random loot.

The generated heightmap resolves the earlier provisional elevations into shared native shelves: town foundation pads are 640–864, with the temple at 864 and Ellinger at 832. This supersedes the earlier isolated 1,152-pad sketch; neighbouring footprints that share terrain vertices share a shelf. The region reaches 1,536. [Landscape checks](landscape/verification.json) cover flat supporting vertices and road grades; eye-height screening and exported native collision still need blockout review.

## Encounters, rewards and access constraints

The [visual-object census](source_objects.json) also retains non-event benches and empty chest props, so event-only extraction does not silently omit them.

The source MOB census finds **151 initially spatial monster records plus 15 off-map reserves** in the five logical source maps. Original counts and coordinates remain in the plan. Among the source species are Goblins, Gremlins, Gremlin Guards, Barbarians, Arachnoids, Electrapedes and Medusa Sprites. Encounter rectangles are **new aggregate volumes and provisional counts**, not a one-for-one conversion of grid encounters to MM6–8 actors. Art donor and canonical monster IDs remain unassigned until the behavior/art pass; names in the wireframe are MM5 species.

Ten proposed encounter spaces distinguish northern patrols, grove nests, Yog's conditional audience, the separate burnable camp, guarded melon territory, troll-hole woods, two contained town skirmishes and scripted guards inside the Gremlin court. Yog is not automatically hostile. Arrival/return pads require at least 1,536 units of hostile-spawn separation; the source rope, outfall and dungeon returns are explicit exclusions when the aggregate volumes are populated. Aggro containment at the town courts needs the future walls and room graph.

Preserve **five ordinary town chests** (plus six already-open empty chest props, inventoried separately in [source_objects.json](source_objects.json)), **two nine-chest puzzles**, and the separate moving-treasure challenge. The puzzle bays preserve each source coordinate and ordered topology. The original message gives the puzzle's role; its toggle graph is still carried by the original event records and must be converted faithfully. No eighteen fresh random-loot rolls. Monga Melons are four original quest pickups, not chests. The wreck, bottled messages, springs, shrine and burnable camp have their own markers and event owners.

Five urban sewer connectors and the exterior outfall remain distinct. Jasper's prison wing and the Gremlin audience are covered annexes connected to the future sewer BLV so free flight cannot simply land behind their locked access. They can share that BLV as disconnected/appropriately linked sectors: this proposal does **not** silently add two dungeons or assume arbitrary new tunnels. Preserve source arrival/return pairs and inspect the complete sewer topology when that BLV is authored.

## Quest routes to keep visible in the layout

| Chain | Local places reserved | External or interior dependency |
| --- | --- | --- |
| Orb / main story | Zelda → Oorla → Ellinger; later Kalindra returns | Tower/castle interiors and Dragon Pharaoh |
| Necklace / tower key | Nadia → sewer connectors → Nadia → Ellinger entrance | Original sewer reward and key gate |
| Gremlin trouble | Mayor → sewer/covered Gremlin court → Mayor | Dialogue escalation, guards, surrender/death, three disks |
| Jasper / real map | Jethro → sewer/prison → Jethro; Joe kept separate | Later map destination and its actual reward |
| Drawkcab | Four identifiable monks in two houses → Reger | Preserve ordered lessons and final answer state |
| Swimming / pathfinding / cartography | Ordana, Goldur, Lydia; Miles separate | Explicit design needed for MM6–8 equivalents; no invented mastery promotions |
| Luna | Sanctuary with three altar places | Southern Tower sales-record clue → Western Tower, Lakeside and Necropolis retrievals |
| Dreyfus | Refuge → Skyroad rope → Western Tower roof → tower interior | Distinct ground/roof access and return/reward state |
| Nibbler | Four melon patches → Nibbler; later growing patch | Visit Bark, return for key; do not pre-grow quest melons in his yard |
| Vespar | Retreat on eastern approach | Emerald handle elsewhere; Sandcaster pass reward |
| Kramer | Caravan repair/loading yard | Ogre Pass resolution; don't invent a new stable route |
| Yog | Separate, negotiable Sardaj camp | Food/hostility state and stolen disks; not the burnable camp |
| Falista | Initially empty creature sanctuary | Rescue condition before restoration benefit |

## How this was calibrated and what comes next

The proposal follows [settlement density](../../SETTLEMENT_DENSITY.md), [sketch layout](../../SKETCH_LAYOUT_CALIBRATION.md), [population/composition](../../POPULATION_AND_COMPOSITION.md), [Ravenshore's measured building catalogue](../../catalogues/mm8_ravenshore/README.md), and Brackenford's [road-purpose revision](../brackenford_greywatch/ROAD_PURPOSE_REVISION.md). It separates physical assemblies, destinations, people and scenery, as those calibrations require.

The [Garrote mapping](GARROTE_STYLE_MAPPING.md) now defines the architectural references for every assembly, the irregular town curtain and a taller friendly Castle Kalindra. Native Garrote meshes appear only in reference renders; all proposed MM5 geometry will be authored anew.

The immediate review decisions are whether the rotated, river-facing Castleview fits the desired interpretation; whether the shared households and joined workshops feel right; and the fountain/well/barrel rules and terrain/planting refinements documented in LANDSCAPE.md. After layout review, the next concrete step is a native blockout of **the guild/forge/training group, one small shared dwelling, and a short wall/gate corner**, at these coordinates and calibrated facade sizes. Then author the rest of the region against the approved wireframe. No native geometry generation was started by this planning run.

A future mounted `assets_dev/worlds/mm5/` package is appropriate. Ordinary NPC/dialogue append support is **not yet wired through the current loader**, despite existing manifest contribution syntax. [World integration notes](WORLD_INTEGRATION.md) separate verified support from required implementation; no global table rows or numeric ranges were allocated during this layout task.

Rebuild all derived review artifacts from the repository root:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/build_review.py
```

The check covers source census completeness, unique identities, puzzle/connector counts, envelope and road clearance, primary frontage direction/obstructions, and town building placement clear of source water/void. The landscape report adds quantized terrain/pad, road-grade, bridge-footprint and individual scenery checks. It does not certify native terrain collision, AI, final sprite scatter, loot balance, dialogue execution or save/load. Those systems have not been generated here.
