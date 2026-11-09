# Castleview–Kalindra environment acceptance

**2026-09-10 maintenance release:** [Geometry simplification](GEOMETRY_SIMPLIFICATION.md) removes 3,742 triangles;
current native SHA-256 is `48c1324d9d67cb38b50a03723e6d9a71d9a4b80299eb2497ffd4a2a72dff3ff5`.
Source/native checks, visual correction, refreshed minimap and release v2 installation are complete.
The original milestone evidence below retains its historical hashes.

Status: **complete — all five milestones accepted on 2026-09-09**. The four duplicate gate-tower deck
surfaces were removed and both gates passed repeated game views. All 24 native readback audits pass on the final
native `87c61c78629b56761ad46ff0280d35a5129238f6f34b3f576f5b49e107e57f24`.
[Gate correction](review/gate_decks_v1/review.json) and [final minimap](review/native_minimap_v9/source_review.json)
record the last visual iteration. Historical review files retain their checkpoint hashes and stated limits.

## Environment and authoring

The map contains 24 town assemblies and 21 countryside destinations, 31 additional source exterior features,
326 independently authored BModels and 727 scenery records plus the party-start marker. Original Alvar/Garrote
textures inform the civilian/fortified division; donor BModel vertices were not reused. Resident assignments stay
in planning data, including shared buildings and venues. All 55 source orchard identities remain represented.

| Requirement | Authoritative evidence |
| --- | --- |
| Complete premises and venue identities | [Specification audit](review/architecture_specification/README.md), [native interaction inventory](review/native/interaction_inventory.json) |
| Town architecture, working yards and courts | [Town inventory](implementation/TOWN_DETAIL_COMPLETION.md), [local context](review/town_context_v1/native_review.json), [final context review](review/town_context_v1/final_context_review.json) |
| Five final working/court settings | [Native appearance and ordinary passage/reload review](review/town_working_details_v4/native_review.json) |
| Kalindra, Western Tower and retreats | [Kalindra](review/kalindra_v2/native_review.json), [Western Tower](review/western_v2/native_review.json), [retreats](review/retreats_v2/native_review.json) |
| Camps, caves, sewer and natural sites | [Camps](review/camps_v2/native_review.json), [natural entrances](review/natural_entrances_v3/native_review.json), [clearings](review/clearings_v1/native_review.json), [site inventory](implementation/REMAINING_COUNTRY_SITES.md) |
| All 31 separate source features | [Feature inventory and individual evidence links](implementation/FEATURE_BACKLOG.json) |
| Native roads, fitted steps and crossings | [Road review](review/roads_v2/native_review.json), [inner-road correction](review/inner_road_grade_v1/native_review.json), [bridge evidence](implementation/BRIDGES.md) |
| Region-wide scenery, forest floor and deliberate clearings | [Regional review](review/region_composition_v1/native_review.json), [written native placement preservation](review/region_composition_v1/native_readback.json) |
| Water, dry shelves and finished outer buffer | [Terrain materials](implementation/TERRAIN_MATERIALS.md), [world rim](review/world_rim_v1/native_review.json), [regional review](review/region_composition_v1/native_review.json) |

The complete stored terrain remains separate from the ±24,576 travel crop. Water continues into the appropriate
buffer; the western/southern boundary follows the source void rim. Native scenery and ground detail use purposeful
local groups, retaining clear approaches and open meadow/court space. The minimap bake includes native terrain and
BModels; billboards are omitted from that static bake and reviewed in actual gameplay.

## Runtime and interactions

[The native build](review/native/build.json) regenerates from fresh source inputs and runs 24 existing readback
audits. These establish arrays, material keys, geometry/instance bindings, native grounding and identity coverage;
they do not substitute for the linked game views and actual clicks.

All 121 map-local handlers use named status-only feedback. The [complete handler smoke check](review/placeholder_handlers/smoke.json)
pins the unchanged Lua hash. Representative actual house, shared-venue, service, dungeon, prop and route clicks
are retained in the individual reviews. [Both unavailable foot routes](review/travel_placeholder_v1/native_review.json)
provide named feedback and allow ordinary retreat/reload without loading missing destinations.

The explicit [MM5 common-script policy](review/script_policy_v1/runtime_review.json) removes inherited population
and reward hooks only in this world. [Installed candidate v3](review/delivery_v3/runtime_review.json) independently
passes fresh start, time advance across the former timer alarm and save/reload: zero actors, timers and world items
at 540, 560 and 580 minutes. Its actual starting view, lodging click, map book and reload are inspected. Existing
MM8 positive-control population and shared MM8/MM9 minimap regression evidence remain recorded in prior reviews.

## Delivery boundary

[Rebuild instructions](REBUILD.md) describe editable Blender/OBJ sources, preparation scripts, native compilation,
minimap staging and isolated delivery. [Player instructions](DELIVERY.md) describe the standalone launcher and save.
The package uses a reviewed Linux executable and an existing donor asset base; composed global registries belong
to its isolated `engine/`, while MM5 owns map-local geography, artwork and Lua. It does not alter the donor base.

NPCs, monsters, encounters, functional services, quests/rewards, playable BLVs and other MM5 regions are deliberately
deferred. The 18 puzzle chests and 11 beds reserved inside future interiors are not scattered outdoors. Placeholder
doors and props identify their future use but grant nothing. Future travel days and destinations remain design data.

## Accepted release

[Release manifest and launcher](delivery/latest.json) pin the final archive, executable, native map and start-save
hashes. [Final installation review](review/delivery_final/runtime_review.json) passes fresh start, time advance,
normal south-gate entry, map-book/exploration alignment and save/reload. Archive CRCs and every packaged file hash
match the installed release. There are no known unresolved environment defects within this goal's scope.

Run `./level_generation/projects/mm5_castleview_kalindra/play.sh` and load `castleview_start`.
For another installation, use [the accepted ZIP](delivery/release_v1/mm5_castleview_runtime.zip) and its installer.
The earlier installed lodging click uses the identical reviewed executable and map Lua; all 121 bindings retain the
same semantics after the gate-only geometry correction. Functional gameplay remains explicitly deferred.
