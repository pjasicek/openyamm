# Castleview–Kalindra environment implementation progress

**2026-09-10 maintenance release:** [Geometry simplification](GEOMETRY_SIMPLIFICATION.md) removes 3,742 triangles;
current native SHA-256 is `48c1324d9d67cb38b50a03723e6d9a71d9a4b80299eb2497ffd4a2a72dff3ff5`.
Source/native checks, visual correction, refreshed minimap and release v2 installation are complete.
The original milestone evidence below retains its historical hashes.

## Completed — 2026-09-09

**All five goal milestones are complete.** The delivered map has 326 independently authored BModels, 45 premises
assemblies, 31 additional source features, 727 scenery records plus the start marker and 121 named Lua placeholders.
There are zero NPC/monster actors and spawn records. NPCs, encounters, rewards, services, quests and playable BLVs
remain deferred by the agreed scope.

Native SHA-256: `87c61c78629b56761ad46ff0280d35a5129238f6f34b3f576f5b49e107e57f24`.
All 24 native readback audits pass. Final native minimap v9 and the refreshed exploration save match this build.
[Consolidated acceptance evidence](COMPLETION.md) links the complete town, countryside, water/buffer, walking,
placeholder, population and save/reload reviews. [Final installed release review](review/delivery_final/runtime_review.json)
passes at 540/560/580 minutes with zero actors, timers and world items. The starting view, ordinary south-gate entry,
map book and reload were inspected in the installed release.

Run `./level_generation/projects/mm5_castleview_kalindra/play.sh`, then **Load Game → castleview_start**.
[Accepted ZIP and provenance](delivery/latest.json) · [Installation instructions](DELIVERY.md) · [Rebuild](REBUILD.md).

The numbered history below retains earlier defects, rejected views and partial checkpoints. Its historical pending
statements are superseded by this completion record and the final linked reviews.

## Visual review and corrections

Viewed the Alvar native material sheet and house contact sheet, and the Castleview wireframe before modeling.
Connected the installed Blender GUI through MCP and preserved its original default scene.

1. [First guild view](review/architecture_v1/guild_eye.png): a partial upper wall repeated the civic decoration band;
   corner segmentation also omitted the terminal corner strip on uneven facade lengths.
2. Corrected the upper partial panel to plain compatible plaster and reserved complete corner panels.
   [Repeated guild view](review/architecture_v2/guild_eye.png) and
   [forge oblique](review/architecture_v2/forge_oblique.png) show those corrections.
3. [Training v2](review/architecture_v2/training_oblique.png) had an excessively tall, windowed parapet.
   Reduced the top from 704 to 512 above its pad and removed parapet windows.
   [Training v3](review/architecture_v3/training_oblique.png) shows the lower roof terrace.
4. Moved the bank component division between the two actual venue doors. This exposed corner cuts inside door
   intervals: coplanar wall fragments covered the door panels and rendered black.
   Filtered every wall cut against door intervals, then rebuilt and captured
   [bank v4](review/architecture_v4/bank_eye.png). Both doors now render correctly.

Camera records accompany every review version. These are fixed native-unit prototype views on a neutral plane,
not proof of final terrain contact, native lighting or in-game visual acceptance.

5. First native load exposed a terrain registration gap: the loader uses descriptor row positions, not the index column.
   Changed the appended palette to contiguous rows 882–1025, then repeated the ordinary game load successfully.
6. Native mouse testing initially hit the HUD or rotated mouse-look. The capture tool now accepts an explicit control
   scheme; classic controls permit deterministic screen-coordinate clicks. The successful
   [guild click](review/gameplay/mm5_guild_classic_fixed_click.png) revealed garbled typographic punctuation.
   Authored display labels now use plain punctuation and meaningful venue names while source titles retain typography.
   [Repeated corrected click](review/gameplay/mm5_guild_label_fixed_click.png) visibly shows
   `Ol' Black Magic: not implemented yet.` No native house screen or map transition opens.
7. Reviewed [snapped town roads](review/roads_v1/town.png), the regional graph and the
   [written textured terrain plan](review/terrain_v1/town.png). Occupancy-based road connectivity created two small
   unintended loops. Changed tile selection to use the actual path edges, not every adjacent occupied cell.
   Also corrected the preview compositor to remove water's magenta key before downsampling.
8. [First terrain game view](review/gameplay/mm5_street_terrain_v1.png) verifies native house/road/material resolution at
   player height. It remains visibly sparse: only five prototypes exist, and scenery, walls, courts and finishing detail
   are absent. Broad source-cell biome contours and distant terrain grid appearance require later visual attention.
9. Reviewed the corrected [town plan](review/terrain_v2/town.png), [travel-area terrain](review/terrain_v2/travel.png)
   and [repeated game view](review/gameplay/mm5_street_terrain_v2.png). The two unintended loops are gone, preview
   shoreline transparency is clean, and all 287 cells connect through actual path edges. The repeated native bitmap
   audit still reports zero supported edge mismatches. Runtime logs report `outdoor actors: total=0 map_delta=0 spawn=0`.
   Latest reviewed native SHA-256: `6df255edd288d5aa89288dd68b5332325c414be895e37c1c3442fe0389130896`.
10. Compared the distant grid with original MM8 Ravenshore: both showed unrelated colours bleeding between terrain
    tiles in lower atlas mip levels. Terrain now uses independent texture-array layers and mipmaps while retaining
    native artwork and the CPU atlas. Repeated [MM5](review/gameplay/mm5_terrain_array_rebuilt.png) and
    [MM8](review/gameplay/mm8_terrain_array_rebuilt.png) game views show clean terrain edges and correct shores.
    Desktop build, the existing water-transition test (58 assertions) and Android ESSL shader compilation pass.
    No Android device run was performed. [Detailed evidence and limits](review/terrain_renderer/README.md).
11. Added roof fascia/soffits and closed the training parapet's mitered corners. Reviewed
    [bank v5](review/architecture_v5/bank_eye.png), guild, forge and training: both bank doors remain visible.
    Added the forge's independent chimney, a stock bench and roof-aligned canopy supports, plus shallow training-hall
    masonry piers within the reserved footprint. A new rear-yard view exposed reversed rafter winding; corrected it
    and repeated [forge rear](review/architecture_v7/forge_rear_yard.png),
    [forge front](review/architecture_v7/forge_oblique.png) and
    [training](review/architecture_v7/training_oblique.png). Later native frontage review is recorded below;
    joined-roof review remains pending.
12. Authored the central fountain at its existing planned location and foundation height, with a 512-unit footprint,
    low perimeter step, stone basin and raised bowl. Its Alvar fountain materials are verified native assets; the
    geometry is new. [First fountain](review/architecture_v8/healing_fountain_oblique.png) exposed a pinwheel in the
    water caused by triangle-local UV alignment. Assigned continuous world-plane UVs and inspected the
    [corrected fountain](review/architecture_v9/healing_fountain_oblique.png). Binding 1000 is status-only; its future
    HP rules remain in source data. The [native click](review/gameplay/mm5_fountain_v9_click.png) visibly displays
    `Healing Fountain: not implemented yet.` The basin, rim and surrounding bank facade render correctly.
    The initial native rear-forge camera was obstructed by the neighbouring chapterhouse. Repeated the check from
    the [actual side yard](review/gameplay/mm5_forge_yard_v7.png): shelter posts, roof underside, bench and chimney
    render with no missing faces or obvious terrain gaps. The clear side access remains usable; the planned anvil,
    ore stock and yard dressing are still absent.

13. Inspected Garrote's wall/gate material roles, then authored unequal guard volumes, open arched passages and solid
    parapets. [First gates](review/gates_v1/pass_gate_oblique.png) repeated barred windows too densely; reduced them
    to two intended upper levels and repeated [south](review/gates_v2/pass_gate_oblique.png) and
    [west](review/gates_v2/west_gate_oblique.png) views. The west gate moved 76 units north to the snapped road
    centre and follows the slightly angled curtain line. Original coordinates and deferred pass rules remain recorded.
14. Authored the full irregular curtain and reviewed it over the actual heightfield:
    [overview](review/curtain_v1/curtain_overview.png), [south junction](review/curtain_v1/south_context.png),
    [west junction](review/curtain_v1/west_context.png). Corner 7's round bastion abuts the south gate's western guard
    volume at the perimeter bend; this is a connected fortification assembly. Gate corner 8 gets no blocking tower.
    The [footprint audit](review/fortifications/footprints.json) checks all 45 planned premises and 295 road edges:
    no building overlaps or obstructions within a 64-unit walking corridor. Minimum road-centre clearance is 237.14.
    Gate widths are 768/512 with at least 768 conservative vertical clearance above their terrain support range.
15. Rebuilt and inspected the native [south entrance](review/gameplay/mm5_south_gate_v2_outside.png) and
    [west entrance](review/gameplay/mm5_west_gate_v2_outside.png): road, foundations and masonry render correctly.
    Initial `W` holds caused no movement because the classic binding is `Up`; those captures do not prove traversal.
    Repeated with `Up` held for five seconds: both [south passage](review/gameplay/mm5_south_gate_walk_inside.png)
    and [west passage](review/gameplay/mm5_west_gate_walk_inside.png) lead into the town. No post-load teleport,
    fly or collision bypass was used. The captions are supported by the inspected before/after gameplay views.
16. Inspected the [street with its new curtain](review/gameplay/mm5_street_curtain_v1.png) and
    [training frontage](review/gameplay/mm5_training_front_v7.png). The green fortifications and brown civilian kit
    render together correctly, but the training frontage still reads as a tall blank box above the two doors.
    Rechecked [native Alvar training](../../catalogues/mm8_alvar/images/assembly_training.png): its stronger piers,
    upper decorative band and low pitched entrance hood are missing from this recomposition. Resolve those details
    before repeating the institution form. Pool, practice props and court dressing remain absent.

17. Rebuilt the training frontage with a low entrance hood, eight substantial piers and the native upper ornament.
    Inspected [training v10](review/gameplay/mm5_training_front_v10.png): both doors remain visible beneath the hood.
    Replaced the bank's intersecting hip roofs with one shared roof while retaining its distinct venues. The
    [native bank side](review/gameplay/mm5_bank_shared_roof.png) shows the continuous roof without the old intersection.
    These captures use native SHA-256 `72e25b08e394a472f66a8896e2b8079b90c9282e6e7f4eebaa42728f864c806f`.
18. Exported all 675 planned trees/plants/rocks, including 231 buffer placements. Seven anchors required bounded
    adjustments around architecture or approaches. All 55 orchard identities survive: 30 ordinary, 13 reward and
    12 food trees. The 25 reward/food trees use local secondary events. Inspected the real
    [orchard click](review/gameplay/mm5_orchard_v1_click.png), which displays `Orchard Tree: not implemented yet.`,
    [court scenery](review/gameplay/mm5_court_scenery_v1.png) and
    [southern woodland](review/gameplay/mm5_south_wood_v1.png). Native roots and crowns render correctly in these views.
    The woodland foreground still has a broad bare-soil area: address its local ground composition during the landscape
    pass. These three views do not certify all 675 placements or the final buffer. Captured native SHA-256:
    `cd2ba136f2c8814a8205d08d39b1ebe7d762244e4c4266c40ed1e7c88b90a828`.
19. Authored the [workers' shared cottage](review/court_props_v1/workers_oblique.png) at the existing low, modest
    dimensions. Daron and Tolberti share one venue and door; no actors are instantiated. Added all nine source benches,
    six stock groups and the well. [Bench](review/court_props_v1/source_bench_572_oblique.png) and
    [stock](review/court_props_v1/working_crates_0_oblique.png) previews show the new timber geometry and native artwork.
    Prop placement checks use the authored curtain and all planned buildings/door approaches; the south-gate bench
    moved 256 units south because its old position lay in a new guard volume. The other 15 modeled props keep their
    planned anchors. [Placement inventory](implementation/prop_placements.json) retains the original source records.
20. The [first well](review/court_props_v1/water_well_oblique.png) exposed coplanar overlapping crank/beam/post faces.
    Separated those timber intervals and repeated the [well view](review/court_props_v3/water_well_oblique.png).
    Six native `dec03` barrels now have local secondary event IDs 1200–1205, and well event 1100 is status-only.
    Runtime `rebuildInteractiveDecorationBindings` skips instances with an explicit script event, preventing inherited
    MM8 barrel rewards. Native click/state review for these new props follows below.
21. Inspected the native [well click](review/gameplay/mm5_well_props_v3_click.png),
    [shared-house click](review/gameplay/mm5_workers_props_v1_click.png) and
    [barrel/forge stock](review/gameplay/mm5_barrel_props_v1_click.png). Each displays its own local placeholder.
    The well's 100-gold party remains at 100; [before/after save comparison](review/gameplay/well_placeholder_state.json)
    also preserves food, health and inventory. The [barrel comparison](review/gameplay/barrel_placeholder_stats.json)
    confirms the selected first character's seven base stats, permanent bonuses, health/SP and resistances are unchanged.
    These are representative checks with documented limits, not a complete future gameplay-state audit.
    These captures use native SHA-256 `b53e11c521959d8bc17ab294e748bd2cb6e57e53c38e88aaba989ec7307171a5`.
22. The [first native gate bench](review/gameplay/mm5_gate_bench_props_v1.png) is clear of the guard volume, but faces
    the wall. Changed seating to look into its usable yard/approach, with backs toward the associated premises;
    the gate seat follows the gate's outward facing. Repeated the
    [bench preview](review/court_props_v4/source_bench_568_oblique.png),
    [native gate seat](review/gameplay/mm5_gate_bench_props_v4.png) and
    [workers' court](review/gameplay/mm5_workers_court_props_v4.png). Seating now faces out from the buildings.
    The workers' court view and wider [gate grounding view](review/gameplay/mm5_gate_bench_ground_v4.png) expose
    the entire bench feet against the terrain. The gate's paved passage remains clear beside the seating.
23. [Baseline decoration coverage](review/native/decoration_coverage.json) matches all 698 original landscape identities
    exactly once: 681 sprite instances and 17 modeled props. This includes all 467 playable-area and 231 buffer records.
    It does not certify all individual views or include the additional service/site-specific props and chests still
    required by the goal. Runtime preparation logs continue to report zero map-delta/spawn actors.

24. Extended the civilian kit to 18 town assemblies. The [tavern](review/civilian_v1/tavern_oblique.png) has a lower
    entrance wing and taller guest hall; [crafts](review/civilian_v1/crafts_eye.png) has unequal shallow work canopies
    with narrow posts that preserve both door approaches. Also inspected [mapmakers](review/civilian_v1/maps_oblique.png),
    [mayor](review/civilian_v1/mayor_oblique.png) and [lodging](review/civilian_v3/lodging_oblique.png).
    Occupant identities remain attached to venues; these additions instantiate no NPC actors.
25. Rear-shelter review exposed coplanar dark bands where the old box posts overlapped sloping rafters. Matched each
    post top to the rafter underside and repeated [keeper](review/civilian_v2/keeper_side_yard.png) and
    [forge](review/civilian_v3/forge_rear_yard.png). Herbalist shelf boards also overlapped their uprights; shortened
    them to fit between the posts and repeated [drying shelves](review/civilian_v3/herbalist_side_yard.png).
26. Inspected the actual [new street](review/gameplay/mm5_civilian_street_v3.png),
    [kennel](review/gameplay/mm5_keeper_kennel_v3.png) and [herbalist yard](review/gameplay/mm5_herbalist_yard_v3.png).
    The first keeper view had a bench in the foreground; the closer repeated view exposes the kennel opening.
    Separate [Jethro](review/gameplay/mm5_mapmaker_jethro_v3_click.png),
    [Lydia](review/gameplay/mm5_mapmaker_lydia_v3_click.png) and
    [Gromlug](review/gameplay/mm5_crafts_gromlug_v3_click.png) clicks display their correct individual placeholders.
    These views use native SHA-256 `4873c915f2fe79623ae6ef184fcd89fbb37074175a72a84da021b29ad1b40eee`.
27. Authored an anvil on a timber base and an open ore bin inside the forge's reserved stock shelter. The first native
    view placed a post in front of the anvil; repeated from the [open side](review/gameplay/mm5_forge_equipment_clear_v2.png)
    and [ore-bin side](review/gameplay/mm5_forge_ore_v2.png). The worn metal, horn, timber support and loose stones
    render correctly without adding reward/container behavior. The equipment remains below the roof and within the
    existing workshop reservation. No original meshes were reused.
28. Added Ordana's [constructed basin](review/service_equipment_v2/training_pool_oblique.png) at the planned location.
    Native terrain rises north across the footprint, so the water sits at 832, with a rim at 848 and a northern step
    at 816. The [south retaining wall](review/gameplay/mm5_training_pool_south_v2.png) meets the lower grade;
    the [north step](review/gameplay/mm5_training_pool_step_side_v2.png) joins the higher yard with space toward the keeper.
    The basin uses a solid, inert water-art face; swimming behavior is deferred and instruction remains at the training
    door. [Ordinary movement](review/gameplay/pool_step_review.json) from the north crosses the step and basin without
    a collision bypass: inspected [before](review/gameplay/mm5_training_pool_walk_v2_before.png) and
    [after](review/gameplay/mm5_training_pool_walk_v2_after.png), then reloaded its ordinary quicksave and inspected the
    [restored view](review/gameplay/mm5_training_pool_reload_v2.png). This verifies that local path and checkpoint
    save/reload, not final-map acceptance. Early native `equipment_v1` / `pool_*_v1` captures predate this export and are
    excluded as evidence for the new equipment/basin; their recorded native hashes identify the older map.
29. Added an automatic [environment audit](review_environment.py) after native builds. It refreshes
    [decoration coverage](review/native/decoration_coverage.json), preserving all 698 baseline identities exactly once
    and reporting the training basin separately. The [foundation audit](review/native/foundation_support.json) splits
    the edges of all 22 main-shell components across actual native triangle boundaries: no foundation gaps. Door standing-point rise
    is zero except the bank's existing 15-unit grade. Open shelters, bridges, props and complete approach corridors
    remain outside that structural check. The current native preparation log still reports zero actors and spawns.

30. Authored the remaining [jail](review/special_town_v1/jail_oblique.png),
    [Gremlin court](review/special_town_v1/king_oblique.png),
    [Joe's stall](review/special_town_v2/joe_counter.png) and
    [Dyson's storehouse](review/special_town_v2/puzzle_oblique.png). The prison has high barred windows and a reinforced
    ordinary-size threshold. The court has a lower controlled entry and higher audience roof. Dyson's two long
    storage roofs have a closed central seam; the eighteen puzzle chests remain attached-interior records.
    Joe's small open stall retains its original footprint; independently drawn SVG merchandise supplies its map display.
    No original BModels or unrelated residents/services are imported.
31. Native [jail](review/gameplay/mm5_jail_v2_click.png), [court](review/gameplay/mm5_king_v2_click.png) and
    [storehouse](review/gameplay/mm5_puzzle_v2_click.png) clicks reached their own placeholders on native
    `10abce4f2848ed4b867bf5e60595d4a28d8ebb692a909476f3087d329856d359`. Joe's first display was unbound; moved its
    actual map face into the counter's interaction model. The first repeated view was still too far from the rear
    display; a [closer native click](review/gameplay/mm5_joe_display_close_v3_click.png) displays Joe's status.
    The counter and map retain one venue and handler. His out-to-lunch sign remains a planned detail.
32. Authored [Ellinger's octagonal tower](review/civic_landmarks_v1/tower_oblique.png) and
    [Temple of Mok](review/civic_landmarks_v1/temple_oblique.png), completing source geometry for all 24 town assemblies.
    The temple has unequal lower wings, a faceted apse and original MOK lettering. Its first gable repeated a facade
    brick strip near the peak; selected plain masonry for that face and repeated the
    [corrected preview](review/civic_landmarks_v2/temple_oblique.png) and
    [native frontage](review/gameplay/mm5_temple_context_v2.png). The porch, lettering and arched windows are readable.
    Real [temple](review/gameplay/mm5_temple_door_v2_click.png) and
    [tower](review/gameplay/mm5_ellinger_door_v2_click.png) door clicks show their correct placeholders.
    These and Joe's closer click use native `ca909ef0e998a0dd4f12b15ce3cf16bbcfc00e0fb94e40b9f108e6a547b18f98`.
33. The [town geometry overview](review/full_town_v1/curtain_overview.png) shows the new masses inside the irregular
    curtain; its ground is the actual heightfield with a neutral review material and it omits native sprite scenery.
    The [native tower street view](review/gameplay/mm5_ellinger_context_v2.png) nearly hides the shallow roof cap behind
    the tall shaft. Native vertices prove the apex is present at world Z 3904; this is a silhouette issue, not a missing
    exported roof. Lowered the eave from 2560 to 2304 while retaining the 3072-above-pad apex and five window levels.
    The [steeper cap preview](review/civic_landmarks_v3/tower_oblique.png) and the repeated
    [same native street view](review/gameplay/mm5_ellinger_context_v3.png) show the pitched cap clearly above the shaft.
    This closes that silhouette defect; broader city skyline acceptance remains outstanding.
34. The new [interaction inventory](review/native/interaction_inventory.json) lists all 45 planned premises, their
    future occupants, current native model/face or decoration bindings and local handlers. All 65 current bindings
    resolve in the actual native readback and Lua registry. This is structural coverage, not a claim of scripted NPCs,
    complete country-site interactions or every individual click. The foundation audit now covers 33 main shells,
    including the actual tower/apse polygons; open stall supports remain outside that main-shell audit.

35. Authored the four northern [gemsmith workshops](implementation/GEMSMITHS.md), retaining Linus, Simon, Toby and
    Hector as separate future contacts at their source-derived premises. The compact halls use the Alvar domestic
    palette with different rear canopy arrangements. Each has a sorting bench, two bounded stock trays and a small
    shipping crate; these are inert BModels. Four original editable SVG trade emblems identify the gems at native
    64×64 resolution. No donor meshes, extra services, inventory rewards or actors were introduced.
36. The first [ruby frontage](review/gemsmiths_v1/ruby_eye.png) clipped its sign behind the roof fascia. Raised the
    workshop eaves by 32 while preserving the ordinary doors and roof apexes, then inspected repeated ruby,
    emerald, sapphire and diamond renders under `review/gemsmiths_v2/`. Native readback then exposed a truncated
    eleven-byte sapphire texture name; the [game image](review/gameplay/mm5_sapphire_material_defect_v2.png) showed
    only the sign's backing. Renamed the authoritative texture to `mm5saph`, with no truncated-name fallback.
    The builder now rejects material names longer than ten ASCII bytes and checks every written BModel's material
    set against source using case-insensitive native lookup. All 183 current models pass.
37. Real [ruby](review/gameplay/mm5_ruby_door_v3_click.png),
    [emerald](review/gameplay/mm5_emerald_door_v3_click.png),
    [sapphire](review/gameplay/mm5_sapphire_door_v3_click.png) and
    [diamond](review/gameplay/mm5_diamond_door_v3_click.png) clicks show the correct individual placeholders and all
    four unobstructed trade signs. Inspected the close native sorting-yard views for
    [ruby](review/gameplay/mm5_ruby_yard_close_v3.png), [emerald](review/gameplay/mm5_emerald_yard_close_v3.png),
    [sapphire](review/gameplay/mm5_sapphire_yard_close_v3.png) and
    [diamond](review/gameplay/mm5_diamond_yard_close_v3.png): canopy undersides, supported posts, trays and crates.
    The first distant ruby yard view was nearly aligned with the roof slope; the closer side view reveals the roof.
    These use native `bc64ac04c537eec2938ecace411b4802115ca6495a841340e2d301c9b69e9820` and establish local
    architectural contact/materials, not final acceptance of the broad grassy foreground or Acid Pond's blue water.
    The automatic foundation audit now covers 37 main shells, with all 698 baseline scenery identities preserved.
38. Added [playtest preparation](prepare_playtest.py), an isolated launcher, and an ordinary starting save. It uses the
    established five-member level-25 calibration fixture, with 50,000 gold and 40 food; no population is added to
    the world. The launcher explicitly mounts MM5 and its settings open the main menu, avoiding the default seeded
    start. The [first restored start](review/gameplay/mm5_playtest_start_v1.png) exposed a marker-unit defect:
    authored facing `512` was interpreted as degrees, so the party looked along the wall. Changed the native author
    to derive degrees from the layout's north-facing arrival (`90`) and verify written entity facings. Rebuilt and
    regenerated the starting save, then inspected the [restored start](review/gameplay/mm5_playtest_start_v2.png)
    without a forced camera pose: the party now faces through the south gate toward the town street and tower.
    The [decoded comparison](review/playtest/start_marker_fix.json) proves only the start facing changed, including
    its duplicate raw-record field; geometry and other map data are unchanged. The
    [starting-save checkpoint](review/playtest/start_v2.json) records the matching map/save/binary hashes.
    Existing saves stay isolated; the previous starting slot is archived by hash. This accepts the starting direction,
    not final street composition, the surrounding scenery, or the complete environment.
39. Authored the [three retreat exteriors](implementation/RETREATS.md) and Luna's separate three-socket altar.
    Corrected Reger's earlier envelope-derived foundation to the landscape's explicit 448×384 world-axis footprint.
    Inspected the first Blender oblique and eye views, then built native
    `883ce583bc6cb72e3e9d7606427d8a58c1b5b35d2e26d7229bf74b7e1a3c38ed`.
    Real [Reger](review/gameplay/mm5_reger_door_v1_click.png),
    [Luna](review/gameplay/mm5_luna_door_v1_click.png), [Vespar](review/gameplay/mm5_vespar_door_v1_click.png),
    and [altar](review/gameplay/mm5_luna_altar_v1_click.png) clicks show their individual named placeholders.
    The first export preflight rejected the altar's collision with south-gate event 1001; the altar now uses 1010.
    All 698 baseline scenery identities remain represented, and the native foundation audit covers 40 main shells.
40. The altar screenshot exposed a tree canopy across the standing area. Added an explicit 400-unit approach and
    256-unit standing radius to the altar, then refitted `dark_grove/030` from (-7152,8240) to (-7424,8512).
    Its identity and original anchor are preserved. The repeated
    [same-pose click](review/gameplay/mm5_luna_altar_v2_click.png) shows the cleared altar and matching feedback.
    The new [sanctuary-side view](review/gameplay/mm5_luna_context_v2.png) shows the cottage, altar and shelter;
    the [close trough view](review/gameplay/mm5_luna_trough_v2.png) shows recessed water and supported masonry/posts.
    These close the local obstruction/context review, not the complete regional scenery pass.
    Vespar's native context shows the cottage and dial but also unfinished bare dirt.
41. Authored both original timber bridges with continuous decks, supporting piles/beams, rails and masonry bank ramps.
    [Bridge planning](prepare_bridges.py) checks full surface triangles against native terrain; actual OBJ checks
    cover 112 walking/beam/foot contacts. First renders exposed coplanar rail/post faces and inconsistent ramp UV scale.
    Narrowed rails relative to posts, ended deck posts at the walking surface, tucked crossbeams into piles, and
    matched deck/ramp UVs to the actual 32×64 wood texture. Inspected repeated
    [ramp](review/bridges_v3/river_crossing_start_landing.png) and
    [landing](review/bridges_v3/reger_crossing_end_landing.png) views. Source and native map now have 215 BModels;
    all [112 native bridge contact checks](review/bridges_v3/native_support.json) pass. Inspected both directions of
    ordinary traversal on each span, including midspans, opposite landings and fully loaded restored views.
    [Traversal evidence](review/bridges_v3/native_traversal.json) records captures and decoded before/after saves:
    map, gold, food, health and inventory remain unchanged. Reger's door is reachable without flight or teleport.
    The first movement captures overshot useful landing views; shorter v2 holds retain the crossing context.
    Reload captures now wait ten seconds instead of recording the loading screen at two seconds.
    The views still expose unfinished meadow composition and the western world rim.
42. Refreshed the isolated ordinary starting save for the complete current 215-model checkpoint. The
    [starting-save record](review/playtest/start_bridges.json) ties it to the bridge native and current game binary.
    Existing ordinary saves and previous starting slots remain preserved. No final package completion is claimed.

43. Authored the [Great Western Tower](implementation/WESTERN_TOWER.md): fortified shaft, sparse upper apertures,
    projected courses, crenellated terrace and separate pitched roof-access house. Lowered its terrace to 2432 above
    pad so the normal-size roof door and its cover fit below the retained 2816 crown. Its two original ground/roof
    route pairs and separate inactive arrival markers remain recorded for future BLV/Skyroad work.
    The initial roof render showed wall masonry striping on the floor; changed it to calibrated Garrote paving and
    inspected the repeated roof and full-height eye views. No existing OBJ geometry changed.
44. Native tower build has 219 BModels, 75 handlers and 41 ground-supported main shells. The
    [tower readback](review/western_v2/native_geometry.json) verifies both actual door quads/events, Z800/Z3232
    thresholds, the roof's upward walking face, 36 approach-support samples and the upper house's embedded skirt.
    The roof house is deliberately excluded from the terrain-foundation audit; it stands on the tower terrace.
    All 698 baseline scenery identities and 112 bridge contact checks still pass. Inspected the
    [native ground click](review/gameplay/mm5_western_ground_v1_click.png),
    [roof arrival](review/gameplay/mm5_western_roof_v1_arrival.png),
    [roof click](review/gameplay/mm5_western_roof_v1_click.png),
    [restored roof](review/gameplay/mm5_western_roof_v1_restored.png), and
    [road approach](review/gameplay/mm5_western_context_v1.png).
    Ordinary roof movement and both named placeholders work; decoded before/after saves retain map, health,
    gold, food and inventories. [Review provenance](review/western_v2/native_review.json) records the checks.
    The nearby bare ground remains part of the unfinished regional scenery. The isolated
    [starting save](review/playtest/start_western.json) now matches this native map.
45. Default countryside entrance records now carry their source contact IDs, closing the empty occupant arrays for
    the four gemsmith venues. No NPC rows or actors are created. Elevated venues are excluded from ground road and
    scenery approach calculations. Isolated road regeneration with current architecture reproduces the same paths,
    287 cells, control-point adjustments and ground-frontage measurements.

46. Authored [Castle Kalindra](implementation/KALINDRA.md) within its existing reservation: an open arch, paved court,
    offset keep, unequal wings/towers, two inward-facing benches and original crown banners. Its single ordinary door
    retains all 15 attached interior contacts without inventing separate outdoor houses. Original entry/return and
    restoration-state records remain deferred. All previous 219 OBJ files and the complete road specification are unchanged.
    Repeated cropped/misdirected render views. A subsequent camera-ground check found that the distant eye camera
    used the castle pad instead of its higher local terrain; corrected the shared terrain-eye placement and inspected
    [the repeated player-height view](review/kalindra_v3/kalindra_eye.png).
47. Kalindra's completed native build contains 228 BModels and 76 handlers. The
    [native castle audit](review/kalindra_v2/native_geometry.json) verifies its door quad/event, constant six-unit court
    clearance, buried arch/bench feet and retained inactive arrival. All 46 ground foundations, baseline decoration
    coverage, both bridge support checks and Western Tower checks pass. Inspected the native overview, inward walk,
    real door click, restored doorway, outward walk and bench feet. Both directions of ordinary arch traversal work;
    the door displays its named placeholder. Decoded saves retain map, gold, food, health and inventories, and runtime
    load/reload has zero actors. [Native review evidence](review/kalindra_v2/native_review.json) records the images,
    hashes and checks. The [starting save](review/playtest/start_kalindra.json) now matches this native map.
48. Prepared the [remaining twelve countryside sites](implementation/REMAINING_COUNTRY_SITES.md) against their
    measured terrain. In particular, the sewer reservation lies at river level and requires a supported dry approach;
    Falista's sloping natural sanctuary must not become a flat house pad. This is preparation, not completed geometry.

49. Authored [four temporary countryside sites](implementation/CAMPS.md): Dreyfus/Justine cloth shelters, Yog's tent
    with cold cooking equipment and Kramer's covered wagon. Their twelve new models preserve all 228 earlier OBJ
    files and the complete road specification. Render inspection exposed coplanar black canvas, floating guy ends
    and a gap below the wagon cover. Added physical cloth thickness, fitted ropes and closed the cover skirt;
    repeated affected views, including the tent's convex front pieces and proud interaction flap.
    [Source review](review/camps_v2/source_review.json) records the specific inspected views and corrections.
50. The native camp checkpoint has 240 BModels, 80 handlers and 44 building venue bindings. All
    [37 native camp support checks](review/camps_v2/native_geometry.json), prior foundation/bridge checks and baseline
    scenery identities pass. Actual clicks at all four sites show their named placeholders. Inspected ordinary
    refuge access, its restored interior view, Kramer's restored counter view, and full native tent/wagon context.
    [Native review](review/camps_v2/native_review.json) records 13 inspected images across seven captures and two
    decoded save comparisons retaining map, gold, food, held item, health and inventories. The
    [starting save](review/playtest/start_camps.json) matches this checkpoint. Broad bare foregrounds and distant
    unfinished terrain joins remain part of regional finishing.
51. Prepared source-backed entry/return pairs for the [eight natural sites](implementation/NATURAL_SITES.md),
    including three distinct troll-hole returns, the sewer, mine and Skyroad rope. Falista and Nibbler remain
    natural destination treatments with preserved source identities. This is planning data; no natural-site
    geometry or active travel is claimed.

52. Authored the [mine and three troll descents](implementation/NATURAL_ENTRANCES.md), with original faceted rock
    hoods, recessed ends, supported aprons and shallow descending troll floors above unchanged terrain. The mine has
    timber supports and an inert supply crate. Native source destinations and inactive return markers remain separate.
    All 240 earlier model files and the complete road specification are unchanged. Introduced an explicit venue-event
    registry preserving existing numbers when new contacts appear earlier in the inventory.
    Source renders exposed open lower shoulders and cropped crowns; closed the shoulders and repeated affected views.
53. The first natural-entrance native build has 252 BModels, 84 handlers and no actors/spawn records. All ten native
    entrance support/grade checks pass, alongside prior environment checks. All four real clicks display their named
    placeholders. Mine and west-troll inward movement and save/reload work; repeated longer backward holds show a
    complete exit. Decoded saves retain map, gold, food, held item, health and inventories.
    [Native evidence](review/natural_entrances_v2/native_review.json) records the inspected views and their limits.
    The [starting save](review/playtest/start_natural_entrances.json) matches this first native revision.
54. Native views exposed a further visual defect: independent UV origins/directions made a conspicuous triangle
    pattern across the rock. Changed only the new rock surfaces to a shared dominant-axis local projection and
    inspected [repeated source views](review/natural_entrances_v3/source_review.json). The fresh native build passes;
    [all four repeated game views](review/natural_entrances_v3/native_review.json) show the continuous projection.
    The change affects only eight rock/floor OBJ files; all previous 240 models and interaction caps remain unchanged.
    The local correction is accepted; broader regional composition remains outstanding.
55. Measured a [sewer landing proposal](review/sewer_approach_proposal.json) that retains its original outfall position.
    A 256-wide approach runs from southern bank Z358 to threshold Z288; both proposed triangles clear native ground.
    Native frontage tiles are shore/transition `wtrdrs`, distinct from the original source water mask. Actual landing
    construction followed in the next step; gameplay/shoreline inspection remains outstanding.
56. Authored the [sewer outfall](implementation/SEWER.md): low Garrote masonry vault, recessed grating and supported
    bank ramp/landing. The first source views exposed triangle UV restarts on the rear closure; fixed their common
    projection. The second rear view exposed a coplanar landing skirt/closure overlap; shortened the hidden threshold
    by eight units. [Repeated V3 views](review/sewer_v3/source_review.json) show both corrections. All previous 252
    source models are unchanged. The new native build passes all ten sewer checks and prior environment checks.
    [Seven inspected game views](review/sewer_v3/native_review.json) show real bank/ramp access, grating collision,
    the named click, save/reload and backward exit, plus corrected rear masonry over the river. Decoded saves
    preserve map, gold, food, held item, party health and inventories. The isolated starting save is refreshed.
57. Prepared a [measured Falista/Nibbler clearing proposal](implementation/NATURAL_CLEARINGS.md) using inspected
    native trees, stumps, flowers and rocks. All anchors fit grass terrain and avoid roads/other assemblies.
    The first plan view exposed an approach/crop-reservation overlap at Nibbler; shifted the route west and
    inspected the repeated diagram. These are review-only proposals; no native entities or bindings are added yet.
58. Authored both [natural clearings](implementation/NATURAL_CLEARINGS.md) as 16 fixed native sprites and two
    explicit contact venues. Canonical descriptor-name checks caught the draft's zero-/one-based ID confusion
    before export; corrected the proposal metadata. Source fitting preserves open approaches, the empty crop plot
    and baseline identity coverage. All 255 BModels are unchanged. Added a native clearing readback audit;
    the new native build and actual player-height/click review are pending.
59. The first successful native clearing export exposed a baseline flower inside Falista's reserved approach.
    Applied whole clearing/crop reservations to the baseline fitter: only `meadow_plants/028` moves, about 64 units,
    with its source identity retained. [Refit evidence](review/clearings_v1/approach_refit.json) preserves both anchors.
    A fresh native build is running; the failed approach revision has no gameplay acceptance.
60. Prepared an isolated [Skyroad climbing-rig study](implementation/SKYROPE.md) while native export runs. Verified
    that the original exterior sprite is the shared hut marker; the accepted exposed rope/anchor mapping remains
    deliberate. Corrected the study alpha material, disconnected-looking brace and floating coil, then inspected
    all three repeated V3 views. The study is not yet fitted or exported into the actual map.


61. Completed the clearing native build after the one-flower approach correction. Inspected each site's outside,
    approach, real click, reload, withdrawal and side-group views. Both stumps display their named status and retain
    checked party/save values. Falista's adjacent unfinished void edge remains explicitly open for the terrain pass.
62. Integrated the original Skyroad rig with one source-owned native tree and event 151. Inspected three source
    renders on the actual heightfield; preserved all 255 prior OBJ hashes. Native export adds two BModels and one
    inert tree. Corrected an XY/XYZ error in the new audit and reran that audit without changing the exported map.
63. Inspected native rope front/side silhouettes, ordinary approach, actual click, reload and withdrawal. The
    named placeholder works; inspected save values remain unchanged. [Native rope review](review/skyrope_v1/native_review.json)
    records images, hashes and limits. All 45 premises now have authored environments; this is not full feature completion.
64. Preserved [diagonal-road candidates](review/road_diagonal_study/proposal.json) and inspected two before/after
    bitmap crops. The 44 candidates retain road cells/graph ports; no active terrain changed in this study.
    [Material findings](review/terrain_material_study/findings.json) retain the sand/dirt mismatch and Plane-of-Air
    whole-terrain hiding limitation. Separately enumerated the 31 required exterior features still missing.

65. Exported the 44 reviewed diagonal road selectors and inspected the new native material preview and repeated
    player views. Independently checked 287 road cells and 291 painted joins against the current ODM. Close views
    reveal sharp grade/road-edge discontinuities; an earlier executable and an independently textured native
    heightfield study retain the angular shape. Keep local grade/frontage refinement open. The
    [road review](review/roads_v2/native_review.json) preserves findings, actual build hashes and an initial stale-audit
    correction. The final aerial diagnostic uses an explicitly labelled flight override; earlier falling poses do
    not count as aerial evidence. No shared renderer code was changed.
66. Authored all five town sewer grilles from the original ground-grille interpretation. Inspected ten source
    ground/eye renders, preserved all 257 prior OBJ hashes, and refitted all 698 native sprites without additional
    moves. Five distinct local handlers and inactive returns are present in source. The South Wall casing has a
    documented small move; the West Gate return faces east to avoid the towers. A fresh native build is running.
    [Town sewer specification](implementation/TOWN_SEWERS.md) records the pending native click/context checks,
    especially ordinary passage across the West Gate road grille. The exterior backlog now has five source-authored
    features and 26 not yet source-authored; none of these five has native gameplay acceptance yet.

67. Completed the five-grille native export: 425 faces, distinct local bindings and checked ground/access reserves.
    Inspected all five native contexts. West Gate click and reload work, but ordinary walking stopped at its raised
    casing. [The V1 review](review/town_sewers_v1/native_review.json) explicitly rejects the misleadingly named
    `crossed` image as crossing proof. Revised only this grate to follow its planar road slope with a low beveled
    outer lip; both [repeated source views](review/town_sewers_v2/source_review.json) are inspected. Native repeat pending.
68. Authored all five ordinary town chests at unchanged source points, with fitted feet, curved timber lids, iron
    straps and distinct placeholder handlers. Inspected all ten source eye/oblique views and preserved 261 prior
    OBJ hashes; only West Gate changes alongside the five new models. Scenery refit retains 698 records, 55 orchard
    identities and ten existing moves, with no unresolved placements. Added native chest support/binding/access
    checks. [Chest source review](review/town_chests_v1/source_review.json) records the limits. The native build is
    running with 267 source models; its log is `review/town_chests_v1/native_build.log`.
69. Prepared the six original roofed wells in an isolated study while native export runs. Inspected the original
    sprite, three corrected template views and twelve fits on the actual heightfield. All source centers and future
    water effects are retained; the royal-quarter well faces east and needs nearby planting refit. The
    [well specification](implementation/SOURCE_WELLS.md) records the inspected source study and pending integration.
    The active 267 map OBJ hashes remain unchanged; these six are not yet counted as integrated features.

70. Completed the corrected grate and five-chest native build: 267 BModels, 98 handlers and zero actors/spawns.
    Both ordinary forward crossings over the West Gate grate pass, from opposite sides. Named click, reload and
    exposed save values are reviewed. The shorter equal-time backward leg is not reverse-crossing proof; the
    [V2 native review](review/town_sewers_v2/native_review.json) records that distinction and the current executable hash.
71. Inspected all five native chests in their actual sites, including the three-chest south-wall group. The mayor-side
    real click shows its named placeholder; reload retains the closed chest and inspected save values remain unchanged.
    [Native chest review](review/town_chests_v1/native_review.json) records appearance, readback and representative interaction evidence.
72. Integrated all six roofed wells and inspected twelve active-source ground views. All 267 prior OBJ hashes remain
    unchanged. Four royal-quarter planting records move, keeping source identities. Corrected the first refit's
    incomplete approach reservation to cover the full corridor; all six source sprite-approach checks now pass.
    The refit retains 698 records, 55 orchard identities, fourteen total moves and no unresolved records. Added
    native support/water/roof/binding checks and started the 273-model build in
    `review/source_wells_v1/native_build.log`. [Source evidence](review/source_wells_v1/source_review.json) retains
    the moves and their purpose. Sixteen of the 31 separate exterior features are now integrated; fifteen remain.

73. Completed native readback and actual game review of all six source wells. The royal well has a successful named
    placeholder click and save/reload; exposed health, gold, food and inventory remain unchanged. Native geometry
    confirms support and positive water clearance. Black void rim and sparse countryside remain open landscape defects.
    [Native well evidence](review/source_wells_v1/native_review.json) records the exact images and limits.
74. Authored three original wooden signs and the northern four-column shrine. Inspected nine sign and three shrine
    study views, then integrated their exact geometry/art at the original centers. Source approach checks pass.
    Corrected exported object labels to use canonical semantic names, independent of duplicate Blender study objects;
    six well headers changed but their geometry/UV/material data did not. Started the 277-model native build in
    `review/waymarks_v1/native_build.log`. [Source evidence](review/waymarks_v1/source_review.json) records the inputs.
    Twenty of the 31 separate exterior features are integrated; eleven remain unauthored.
75. Inspected five [waterside placement diagrams](review/waterside_placements_v1/source_review.json) using the actual
    donor bitmaps and current source terrain. Four message bottles can shift 576–704 units toward their local bank;
    the wreck can straddle the southern shore with a reachable stern. All proposed standing rings are on painted dry
    ground. [The placement contract](implementation/WATERSIDE_FEATURES.md) preserves original source positions and
    limits. This study changes no active models, terrain or scenery; geometry and runtime review remain pending.

76. Completed the 277-model native build and inspected actual appearances of the three signs and northern shrine.
    Ordinary forward movement crosses the shrine's center, with a rear view confirming passage. Close West Tower and
    shrine clicks show their named placeholders and survive reload; exposed save values remain unchanged. Earlier wide
    camera clicks were outside the configured 512-unit mouse interaction range and are not dispatch evidence.
    [Native review](review/waymarks_v1/native_review.json) preserves the repeats and regional-composition limits.
77. Authored four source message bottles at the reviewed local shore fits. V1 exposed black SVG gradient fills and an
    unstable tilted pose; V2 exposed inherited black outlines. V3 uses explicit painted colors and rests horizontally.
    Inspected four individual views and all twelve placement views in the contact sheet. The integrated four OBJ files
    and two native-sized bitmaps match that accepted study; all 277 preceding referenced models remain unchanged.
    The scenery refit retains 698 sprites, fourteen moves and all 55 orchard identities. Started the 281-model native
    build in `review/message_bottles_v1/native_build.log`; native water context and representative clicks remain pending.
    [Source review](review/message_bottles_v1/source_review.json) records the repeats. Twenty-four of the 31 separate
    features are now integrated; seven remain unauthored.
78. Created an isolated [four-patch melon study](implementation/MELON_PATCHES.md). V2 connects detached leaf settings
    with stalks and adds foliage along each vine. Inspected three individual views and all eight in the contact sheet.
    All four source centers remain fixed. Source 4 (14,3) needs a local refit of `meadow_plants/024` (96-unit approach
    clearance versus 128); the other three approaches pass. These studies have not changed active source/scenery while
    the preceding bottle build runs. Integration and native appearance/click checks remain pending.

79. Completed the 281-model bottle build and inspected all four native water-margin appearances. The Queen Kalindra
    bottle's real click shows its named placeholder and reload preserves appearance; exposed save values match.
    [Native bottle review](review/message_bottles_v1/native_review.json) records evidence and the unfinished rim/context.
80. Integrated the four inspected V2 melon patches with their original centers. All 281 preceding OBJ hashes remain
    unchanged. One meadow plant moved 59 units east and 24 south, improving approach clearance from 96 to 155 units.
    The refit retains 698 sprites and 55 orchard identities, with fifteen total moves and no unresolved records.
    [Integrated source evidence](review/melon_patches_v1/source_review.json) records the exact change. The 285-model
    native build is running; actual native appearance and representative click review remain pending.
    Twenty-eight of the 31 separate features are now source-authored; wreck, camp and pyramid remain.

81. Completed the 285-model native build and inspected all four actual melon-patch appearances. The southwest patch's
    real click reaches its named placeholder; reload and exposed save values are unchanged. Native fruit contact gaps
    are 0–0.875 units. [Local native review](review/melon_patches_v1/native_review.json) retains regional-art limits.
82. Authored the broken river ship in an isolated study. Repeated views corrected unsupported fragments/spar, diagonal
    stern grain and overlapping end caps; a final bow-skin correction prevents crossing the centerline. Integrated
    the inspected 474-face source with all 285 prior OBJ hashes unchanged and no additional scenery moves.
    [Source review](review/wreck_v1/source_review.json) records the fit and repeated images. The 286-model native build
    is running in `review/wreck_v1/native_build.log`; water context and a real bank-side click remain pending.
    Twenty-nine of the 31 separate features are source-authored; barbarian camp and closed pyramid remain.

83. Created and inspected the barbarian camp source study: two unequal shelters, central native-fire preview, supplies
    and equipment rack. Corrected floating bedding and repeated all three V2 views. Source approaches pass.
    [The camp contract](implementation/BARBARIAN_CAMP.md) records its pending native-fire staging and interaction check.
    It remains isolated while the wreck build runs; the active environment count is unchanged.
84. Measured the closed pyramid's wall conflict and a bounded 256-unit eastward fit; candidate center and standing
    clearances pass. Inspected the original triangular masonry sprite and MM6 pyramid materials.
    [Placement/material findings](implementation/CLOSED_PYRAMID.md) retain the source identity and required foundation.
    No pyramid geometry or bitmap has been added yet.

85. Completed the 286-model wreck build and inspected its actual bank/shore appearance, real stern click, reload and
    wider context. The named placeholder is visible and exposed save values match. The bow remains over water and
    stern contacts the bank. [Native review](review/wreck_v1/native_review.json) preserves the images and unfinished-rim limit.
86. Authored the closed pyramid and corrected front masonry density to match its sides; inspected all three repeated
    V2 views. Imported the exact MM6 masonry bitmap under an MM5-local alias with provenance. Integrated both pyramid
    and the inspected V2 barbarian camp, preserving all 286 prior OBJ hashes. The camp adds one native fire with an
    explicit local event override and light radius. Scenery now totals 699 records, including all 55 orchard identities,
    with fifteen prior moves and no unresolved fits. [Source audit](review/camp_pyramid_v1/source_review.json) records
    the agreement. The 288-model build runs in `review/camp_pyramid_v1/native_build.log`; actual fire behavior/light,
    pyramid street context and real clicks remain pending. All 31 separate features are now source-authored.

87. Completed the 288-model native export. Its first post-build census omitted prop-owned native scenery; corrected
    that ownership enumeration and reran all eighteen native readback checks successfully on the unchanged ODM.
    [Readback retry](review/camp_pyramid_v1/readback_retry.json) records the recovery without a second export.
    Actual camp and pyramid clicks show their named placeholders, with reload and unchanged exposed non-clock saved
    values. The fire animates and casts warm ground light; food remains 40. The pyramid fits the wall-side street.
    [Native review](review/camp_pyramid_v1/native_review.json) records a required camp correction: its flat pale cloth
    and bedding look like rigid slabs. Do not accept that appearance merely because its supports and events pass.
88. Measured and inspected [remaining terrain boundaries](review/landscape_boundaries_v1/measurements.json) and the
    source cross-section plot. The 347 exclusions comprise 260 void, 81 desert and six scorched cells. Only 26 of
    4,810 void cells slope, at river contacts. Rock paint on those slopes alone cannot finish the long land/void rim.
    This read-only study changes no active terrain, water planes or travel bounds.

89. Corrected camp fabric after the native V1 review: sagging roof, pleated windbreaks and thin blankets with rolled
    ends. Inspected all three [V3 source views](review/barbarian_camp_study_v3/source_review.json), then integrated
    the exact accepted study OBJ with the other 287 model hashes unchanged. The repeated native build is running;
    [source evidence](review/barbarian_camp_v2/source_review.json) does not claim the required native repeat.

90. Tested a transparent void tile in a separate installation using the unchanged 288-model native map. Inspected
    [the actual game capture](review/gameplay/mm5_rim_alpha_wreck_v1.png): existing alpha discard removes the black
    apron, but exposes a flat lower-sky color. [Experiment evidence](review/landscape_boundaries_v1/alpha_study.json)
    records that collision remains unchanged. This is a rendering capability, not an accepted rim treatment; cliff
    geometry, lower atmosphere and movement behavior remain required. The canonical map keeps its original void tile.

91. Completed the corrected camp build and inspected front/rear context, ordinary approach, real click and reload.
    [Repeated native review](review/barbarian_camp_v2/native_review.json) accepts its sagging covers and rolled bedding
    locally. Food stays 40 and exposed non-clock saved fields match. Source and native now agree; regional context remains open.
92. Walked from land onto the transparent rim experiment using ordinary movement. Existing gameplay traces confirm
    a floor at height zero beyond the visible land edge, with flying and airborne both false.
    [Movement evidence](review/landscape_boundaries_v1/void_movement.json) rejects alpha-only completion. The canonical
    map is unchanged; the final rim needs physical boundary treatment as well as cliff geometry and atmosphere.

93. Authored Joe's planned counter notice, inspected both actual source renders and integrated the accepted OBJ.
    All other 287 models are unchanged; no extra venue or NPC is introduced. The updated native export is running
    under `review/joe_notice_v1/`; actual notice appearance and click remain pending.
94. Completed [the architectural specification audit](review/architecture_specification/README.md): all 45 premises,
    52 venues, 54 retained people/services and 23 attached interior contacts agree with their source identities.
    Corrected eight omitted interior ownership links in the preparation path and regenerated metadata with all 288
    OBJ hashes unchanged. Milestone 1 is complete; the other four milestones retain their full acceptance scope.
95. Identified the original edge's [space-surface meaning](implementation/WORLD_RIM.md): 1,113 in-world void quads
    derive from surface 15, and 3,697 continue beyond the original world. ScummVM's normal Xeen surface movement
    rejects space. Preserve an explicit impassable edge; do not invent a required falling/respawn system.
96. Inspected fresh native fountain/chapterhouse court views and repeated the chapterhouse from its road approach.
    [Court evidence](review/city_courts_v1/native_review.json) records the unfinished loose plant setting and a
    historical garden reservation crossing the snapped fork. [Town detail completion](implementation/TOWN_DETAIL_COMPLETION.md)
    distinguishes remaining exterior identity/court work from furniture kept in deferred interiors.

97. Completed Joe's updated native export and inspected ordinary context, approach, real notice click, reload and
    return view. [Native review](review/joe_notice_v1/native_review.json) shows the named event-117 placeholder;
    exposed non-clock saved fields match. The source and native agree. The refreshed isolated starting save is
    recorded in `review/playtest/start_joe_notice.json`.

98. Authored an isolated full-contour rim experiment: 259 boundary edges, 18 original rim models and 14 nearby
    context models. Terrain, tile and attribute arrays are unchanged. [V1 native review](review/rim_geometry_study_v1/native_review.json)
    verifies one ordinary approach stops before space, with reload and return evidence. Appearance fails: the edge
    disappears into lower sky at the stopped view. [V2 source review](review/rim_geometry_study_v2/source_review.json)
    records the exposed lip iteration, remaining slab-like contour and cap opening. [Native V2 review](review/rim_geometry_study_v2/native_review.json)
    confirms the lip is visible inland but still disappears at the blocked viewpoint, including after reload; rejected.
    The shared executable changed externally between captures; actual binary hashes are recorded in each review.
    The terrain sampler now correctly accepts the final stored row/column; all 16,384 stored vertices and 508 outer
    edge midpoints pass exact-height checks. Canonical geometry and native map have not adopted the rim studies.

99. Closed the rim cap's terrain opening by splitting contact at every native triangle crossing, and extended the
    exposed ledge beyond the unchanged source collision boundary. [V3 native review](review/rim_geometry_study_v3/native_review.json)
    now shows the ledge at the stopped ordinary viewpoint, after reload and on return. An airborne hit and oblique
    movement along a straight edge are recorded; this does not establish corner or flying acceptance.
100. Added two original river-spill models with 168 scrolling `WtrTyl` faces across 21 water/space segments.
     V4 preserves all 18 V3 rim OBJ inputs and all terrain arrays. [Native bank review](review/rim_geometry_study_v4/native_review.json)
     exposed a renderer defect: the opaque fallback terrain remains under the transparent tile, hiding the descending
     cliff/spill. Its RGB exactly matches the `mm5void` fallback color. Earlier lower-sky-only diagnoses are superseded.
101. Corrected fallback terrain generation to retain colored triangles only where the atlas lacks a valid texture.
     [Diagnosis and validation scope](review/rim_render_fix_v1/diagnosis.json) records the narrow renderer change,
     pre-edit snapshots and separate `/tmp/openyamm-mm5-rim-build` compilation. The release build passed.
102. Inspected the corrected native river and matched MM6 town / MM7 shore / MM8 shore comparisons.
     [Native renderer review](review/rim_render_fix_v1/native_review.json) shows the descending rock and waterfall
     are now visible, without a visible regression in those existing-world views. Frame differences establish water
     animation; UV/flags establish intended direction, not a measured screen-space flow direction.
     [Actual J flight](review/rim_geometry_study_v4/flying_review.json) reaches about 4,000 units and stops at the
     source boundary. Those flight images predate the renderer fix and establish collision only.
103. Repeated the corrected-renderer dry approach and reload: the ledge remains visible. At a convex corner both
     perpendicular boundary faces stop the ordinary party, but the low ledge nearly disappears behind the HUD.
     V5 widens the exposed dry ledge by 176 units, preserving terrain and the source collision boundary. Its source
     renders and isolated native build are prepared for the affected repeat. Canonical adoption remains pending.
104. Inspected all five V5 source views and the repeated native corner/turn/reload/return views. The wider ledge
     remains clearly visible above the HUD. The ordinary islet-facing view shows the spill beside its existing bridge.
     [V5 native review](review/rim_geometry_study_v5/native_review.json) accepts the correction locally.
105. Integrated the reviewed rim through `world_rim.py` and the normal specification/Blender/native pipeline.
     [Source comparison](review/world_rim_v1/source_review.json) verifies all 288 previous OBJ files unchanged and
     all 20 added models identical to the reviewed V5 study. Source now has 308 BModels, 58 materials and nine
     separately identified rim groups. The complete native rebuild is running; final regional acceptance remains open.
106. Verified the renderer's missing-texture case in a separate installation: the observed fallback RGB exactly
     matches the deliberately absent texture's hash-derived color. Added a fast X11 frame-burst action to the capture
     tool because ordinary PNG captures were about 1.6 seconds apart and aliased the water motion. The resulting
     [16-frame native sequence](review/rim_render_fix_v1/flow_tracking.json), spaced 62–82 ms apart, shows downward
     water motion in all 15 adjacent comparisons while the rock control remains stationary. Actual full frames were
     inspected; this closes the direction check without changing the correct spill UVs or flags.
107. Completed the full native export. Its later small-prop audit exposed an ownership error: rim groups were listed
     with radius-bearing props. Moved them to explicit landscape metadata and regenerated with all 308 OBJ hashes
     unchanged. [Readback retry](review/world_rim_v1/readback_retry.json) passes all 18 audits without recompiling
     the unchanged ODM. All original 288 native model records are exact; the new 20 match the reviewed study apart
     from the expected index offset. Terrain arrays, entities and zero-population records remain unchanged.
108. Inspected the integrated native corner approach/turn/reload/return and river views. The ledge remains visible
     and the cliff/spill is present beside the wreck. [Native integration review](review/world_rim_v1/native_review.json)
     records local acceptance and the remaining background/context review. Refreshed the starting save and launcher
     to use the explicitly reviewed executable; `review/playtest/start_world_rim.json` records that checkpoint.

109. Added a distinct Acid Pond material using original MM8 `SLIMYwtr`, separate native water/shore records and a
     composed surface registry. Replaced the six northern scorched cells with native volcanic/dirt transitions.
     Source renders and the independent tile-corner audit pass. The isolated full-context game views establish local
     pond appearance, animation, save/reload and an unchanged blue river; [review evidence](review/terrain_materials_v1/native_review.json).
     The full canonical source rebuild passed; [readback evidence](review/terrain_materials_v1/full_build_readback.json)
     verifies all 308 OBJ hashes and native geometry. Heights, water planes, scenery, actors and interactions remain unchanged.
110. Authored twelve sand/dark-dirt transitions through Blender using unchanged native donor textures. Rejected the
     first bake after finding raster-edge discrepancies; V2 pins mask edge samples and passes all 100 compatible joins.
     Both donor endpoint renders retain original RGB within one step. The isolated native approach and close views pass
     locally. [The material study](review/desert_materials_v2/native_review.json) retains all evidence and its frozen source.
     Accepted material assets are in `implementation/art/desert_terrain/`; canonical selector integration is complete.
     The isolated study uses the editor's existing native-plus-terrain metadata path, verifies every source OBJ against
     its build provenance, and confirms all 308 BModels and all entities/spawns/heights/attributes remain unchanged.
111. Promoted the reviewed desert revision over the freshly rebuilt geometry. The complete parsed native payload
     changes only in `tile_map`; all composed terrain rows match the reviewed study. The final native bitmap-corner
     audit includes sand and scorch, has zero mismatches, and excludes only geometry-owned space edges. The new
     canonical pond view is inspected and the starting save is refreshed. [Promotion evidence](review/terrain_materials_v1/desert_promotion.json).
     `author_desert_materials.py` reproduces all 14 material images pixel-for-pixel; PNG metadata carries changing
     timestamps/timings, so file hashes are recorded separately. [Material ownership](implementation/TERRAIN_MATERIALS.md).
112. Authored the southern chapterhouse court: one fitted timber bench, two unequal low masonry bed edges, and
     twelve deliberately repositioned existing garden plants. The direct south-door corridor is 250 units wide;
     both snapped road branches remain clear. The first source renders revealed mismatched green fortress edging;
     the repeated renders use the chapterhouse's brown masonry. All preceding 308 OBJ inputs remain unchanged;
     the source now has 310 models. [Source review](review/chapter_court_v1/source_review.json) and
     [continuation checkpoint](review/chapter_court_v1/checkpoint.json) distinguish this from native acceptance.
     The fresh full-source native build has completed; all 19 readback audits and the planted native context, approach, click and reload review now pass locally.
     A new native view of the inner-town descending road confirms its angular appearance. Its bank/diviners terrace
     supports need a coordinated grade/frontage correction; no terrain heights were changed in this court revision.

113. Completed the 310-model native minimap bake/staging and corrected two shared runtime assumptions exposed by
     actual game views: world presentation selection was gated to MM9, and journal fog sampled crop UV as native
     exploration UV. The coordinate fix preserves saved exploration data. Town and eastern-road alignment, map-book
     title, ordinary save/reload, and MM8/MM9 regression views pass. Both existing-world map-book comparisons and the
     MM5 reload pair are pixel-identical. Four focused map tests pass (39 assertions). See
     [minimap evidence](review/native_minimap_v1/native_review.json). The playtest now uses the frozen reviewed
     `/tmp/openyamm-mm5-minimap-reviewed` executable; [start provenance](review/playtest/start_minimap.json).
     The bake omits billboard sprites and must be refreshed after remaining environment work.

114. Authored the coordinated inner-road grade revision. Nine source height samples now ease the bank/diviners
     crossfall from 43.75% to 12.5%, retaining both building floor elevations and buried shell skirts. Three shallow
     stone steps reach Oorla's existing door. Of the preceding models, 309 OBJ files remain unchanged and the nearby
     town chest is refitted to the revised ground. The new stair model brings the source to 311. Source oblique and
     close step renders and the completed native lane, steps, bank frontage and refitted chest views are inspected.
     All 20 readback audits pass; ordinary steps approach, named door click and reload pass locally.
     [Current build/review checkpoint](review/inner_road_grade_v1/checkpoint.json).
     Explicit graded support records replace flat-pad claims only for the affected samples. Water, rim, door identities
     and source population exclusion remain intact. The refreshed 311-model minimap is staged and reviewed.

115. Executed all 119 authored placeholder callbacks in restricted Lua. Each emits exactly one matching named
     status message; unexpected global APIs/state writes and lifecycle callbacks are rejected. Registration IDs match
     the current source inventory. [Handler smoke evidence](review/placeholder_handlers/smoke.json) records the Lua
     hash and scope. This does not substitute for native picking, descriptor-override or population checks.

116. Resolved the inherited cross-continent common-script timer through an explicit MM5 world-local policy.
     The source-owned override registers no cross-continent hooks; the shared base script is byte-identical.
     Fresh start, advance past the former 550-minute alarm, save/reload and another advance all retain zero outdoor
     actors, timers and world items, with unchanged gold/food and empty fixture inventories.
     [Runtime policy evidence](review/script_policy_v1/runtime_review.json). Shared NPC registry entries are not
     map population; the full final population gate remains open.

117. Completed local native acceptance of the inner-road grade revision: reciprocal lane views, all three fitted
     steps, ordinary approach/click/return/reload, both bank frontages and refitted chest grounding are inspected.
     [Native grade evidence](review/inner_road_grade_v1/native_review.json). Re-baked the actual 311-model ODM through
     Blender MCP, preserved the prior minimap review, and staged the new crop. The repeated map-book/reload pair is
     pixel-identical, with zero actors/timers in its ordinary save. The refreshed launcher records world-script and
     minimap hashes alongside the native build. [Current minimap evidence](review/native_minimap_v2/native_review.json).

118. Added two source-owned, invisible grounded route contacts with named status-only handlers. All preceding
     311 OBJ inputs are unchanged. The 313-model build and 21 readback audits passed. Inspected actual eastern and
     northern approach, boundary, retreat and reload images; both messages appear and neither route loads a missing
     destination. Returned saves remain inside the contact boundary with zero actors, timers and world items.
     [Route evidence and limits](review/travel_placeholder_v1/native_review.json). Re-baked and inspected the minimap,
     full terrain and town views; all are pixel-identical to the previous bake and the new provenance is staged.

119. Studied a restrained ranger woodcraft yard in isolation: trestle table, short timber stock, chopping block and
     embedded axe, south of the clear lodge approach. Revised the first hammer-like blade/handle silhouette and
     repeated the daylit source context views. [Source review](review/ranger_yard_v2/source_review.json) retains the
     actual native frontage comparison and limitations. Integration, garden treatment and native review remain open;
     this study is not part of the current 313-model map.

120. Integrated the ranger woodcraft group and five fixed native garden plants through the canonical prepare/author
     paths. The 314-model build and all 22 readback audits passed, including actual support vertices and 16-unit
     burial. Inspected the player-height garden and work area, ordinary road-to-door walk, Goldur's named click,
     retreat and reload. The returned save has zero actors, timers and world items, with unchanged fixture resources.
     [Local ranger review](review/ranger_yard_v3/native_review.json). Re-baked and inspected the current native minimap,
     full terrain and town view, staged the crop and refreshed the isolated starting save. A Blender crash interrupted
     source review; the saved source was restored, and the corrected source views completed before native acceptance.

121. Identified the pale shapes behind the wreck using the retained capture's actual saved camera height and rays
     through the matching native ODM. Exposed pixels hit corner tower `town_corner_05` and two curtain sections,
     all with the normal `t18a01a` stone. A closer actual view confirms textured wall/tower surfaces. This closes
     the unknown-geometry item; final regional skyline/composition remains separate.
     [Identification evidence and limits](review/wreck_background_v1/native_review.json).

122. Authored and inspected an isolated frontage-sign study: three named mapmaker plaques and two craft signs
     suspended under the existing unequal canopies. Fixed a rasterization defect that put scissor handles over the
     tailor lettering, then repeated artwork and building views. Added a wider eye view to show both craft entrances
     and signs together. [Source review and remaining native checks](review/frontage_signs_v1/source_review.json).
     The canonical 314-model source/native map remains unchanged; palette/configuration integration, native build
     and actual appearance/access review are next. This source checkpoint does not complete the town-detail gate.

123. Integrated the five frontage signs into the canonical prepare/author paths: 316 BModels and 63 architecture
     materials. All preceding 314 OBJ inputs, 88 architectural event definitions and 704 scenery records are
     unchanged. [Source delta](review/frontage_signs_v1/source_delta.json). Native compilation and the focused
     artwork/mount/door-ownership readback are in progress; no native sign appearance is accepted yet.
     Separately authored and inspected three civic/membership/hiring notice displays in an isolated study. Fixed
     a clipped civic heading and repeated the affected views; the three displays are not in the compiling map.
     [Public-notice source evidence](review/public_notices_v1/source_review.json).

124. Completed the 316-model native build and all 23 readback audits. Inspected all five frontage signs in actual
     game views; corrected a mapmaker camera that started inside the opposite tavern. The cobbler's ordinary
     approach, named click, retreat and reload pass beside the hanging sign. The returned save retains the test
     resources and has zero actors, timers and world items. [Native sign review](review/frontage_signs_v1/native_review.json).
     Refreshed and inspected the native minimap and prepared a new standalone starting save. The three public
     notices remain source studies; final town/regional review and milestones 2–5 remain open.

125. Integrated the three public-notice displays into the canonical prepare/author paths. The source now contains
     319 BModels and 66 architecture materials; all 316 preceding OBJ inputs are unchanged. The native build and
     notice readback are in progress. [Source delta and checkpoint](review/public_notices_v1/checkpoint.json).
     Independently studied two inert training targets in the clear south wall bays. Corrected a window alignment
     and an over-stretched wood bitmap, then inspected the repeated source detail/context and road-clearance plan.
     [Training-yard source review](review/training_yard_v3/source_review.json). These targets are not yet integrated.

126. Completed the 319-model native build and all 24 readback audits. Guild, civic and hiring notices have
     inspected actual game views. The hiring door passes ordinary approach, named click, retreat and reload;
     saved resources remain unchanged with zero actors, timers and world items.
     [Native notice review](review/public_notices_v1/native_review.json). All 316 preceding OBJ inputs,
     88 architectural event definitions and 704 scenery records remain unchanged. Inspected and staged minimap
     v6 and prepared the matching starting save. Training targets remain source-reviewed, pending integration.

127. Integrated the two reviewed training targets into the canonical prepare/author paths: 321 source BModels,
     with all 319 preceding OBJ inputs unchanged. The native build is running as session 61001;
     [checkpoint](review/training_yard_v3/checkpoint.json) retains the previous written map separately.
     Authored and inspected five remaining exterior settings together: hiring repair table, keeper workbench,
     Nadia storage, workers sweep tools and one fountain-facing public bench. Corrected unsupported tools and
     their silhouettes, then repeated affected views. These remain isolated, pending the next combined integration.
     [Source review](review/town_working_details_v4/source_review.json). Current native forge/herbalist/temple/jail
     context observations are recorded in [town review](review/town_context_v1/native_review.json).

128. Completed the 321-model native build and all 24 existing build readbacks, plus focused target-foot/material
     inspection. The targets have actual appearance, ordinary passage, retreat and reload evidence. Corrected a
     camera route that initially walked into existing stock rather than toward the targets; no geometry change
     was needed. The pool's north view shows its water, rim and clear step. The returned save has unchanged
     resources and zero actors, timers and world items. [Training review](review/training_yard_v3/native_review.json).
     Inspected/staged minimap v7 and prepared its matching starting save. The five remaining working/court
     settings remain source-reviewed; all final town/regional and delivery gates remain open.

129. Integrated the five reviewed working/court settings together: 326 source BModels, 60 props and the same
     66 architecture materials. All 321 preceding OBJ inputs are unchanged. Their native build is running;
     [checkpoint and source delta](review/town_working_details_v4/checkpoint.json). The last accepted native
     checkpoint remains 321 until the new readbacks and actual views pass. Milestones 2–5 remain open.

130. Completed the 326-model build and all 24 native readbacks, plus focused support/material/inert-face checks
     for five courtyard settings. The hiring table, keeper bench, workers' tools and Nadia storage have inspected
     local native views. A misplaced Nadia camera was rejected and repeated inside the curtain passage.
     [Working/court native review](review/town_working_details_v4/native_review.json).
131. Reviewed southern woods, Dark Grove, the royal meadow skyline and the northern working route in the game.
     Preserve the coherent grove and open meadow/route; add three selected native woodland-floor pockets only.
     The initial generic approach reservations displaced four trees and their build was stopped before export.
     Corrected groups retain all 704 existing scenery records and all 326 OBJ inputs, adding 23 inert stumps,
     shrubs and rocks. The corrected native build is running.
     [Regional observations and source delta](review/region_composition_v1/checkpoint.json).

132. The three southern woodland-floor groups pass native local appearance, ordinary gap walking and reload review.
     All 326 existing BModels and 704 previous scenery records are unchanged in native `a412724b…`; 23 inert sprites
     were appended. Dark Grove, royal meadow, northern workshop route and Acid Pond contexts were inspected and
     retained without filler. Minimap v8 and the starting save match this native checkpoint.
133. Candidate delivery v1 failed individual table symlinks, v2 failed donor-world manifest lookup. Candidate v3 uses
     the proven directory-mount/metadata-copy layout and passes the seven-step fresh population/reload scenario.
     No base asset is edited. The first attempted town aerial was under Justine's shelter; the repeated clear-road
     ascent shows the town and reveals overlapping gate cornice/deck faces. Removed only the four cornice top faces;
     the parapet owns each exposed floor. Native rebuild and repeated aerial review remain pending.

134. The overall game view exposed duplicate coplanar trim-box tops and parapet floors on four rectangular gate
     towers. Removed only the four duplicate top faces through the Blender author. Fresh native export and all 24
     readbacks pass; 322 other BModels, all 728 entities and every terrain array remain exact. Repeated southern
     overview and complete western gate views show clean floors and closed parapets. Final minimap v9 was inspected
     in town/travel/full-terrain views, staged and paired with a refreshed starting save.
135. The final release archive and isolated installation verify all packaged hashes. Fresh-start/time-advance/reload
     population checks pass, as do actual starting view, ordinary complete south-gate entry, map book and reload.
     The identical reviewed Lua retains all 121 status-only handlers and earlier real venue/prop/route clicks.
     All five milestones accepted; final source/runtime/review/launcher links are in COMPLETION.md and delivery/latest.json.

## Remaining work

No required environment work remains for this goal. Future work is the separately scoped gameplay phase:
NPCs/dialogue, functional services, quests/rewards, encounters/monsters, connected BLVs and the other MM5 regions.
Preserve the existing resident identities, spatial reservations and original interaction rules when starting it.
