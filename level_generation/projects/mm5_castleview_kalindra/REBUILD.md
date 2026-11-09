# Rebuild the current MM5 environment checkpoint

Run ordinary Python commands from the repository root. The current output is the accepted environment release;
[GOAL.md](GOAL.md) defines the full deliverable and [PROGRESS.md](PROGRESS.md) records the completed review history.

## Sources and ownership

- Historical geographic/resident wireframe: `layout.json`, `landscape/`, original design documents.
- Implementation form/material choices: `prepare_architecture.py`; derived `implementation/architecture.json`.
- Newly authored facade/roof geometry: `author_architecture.py`; editable packed scene and source OBJ/metadata in
  `implementation/source/`. No original BModel vertices are copied.
- Polygonal tower/apse and original MOK lettering: `author_landmarks.py`, used by the same author.
- Great Western Tower shaft/crown and elevated roof entrance: `author_watchtower.py`; see
  [the separate ground/roof access specification](implementation/WESTERN_TOWER.md).
- Castle Kalindra's court, arch, benches and royal towers: `author_castle.py`; see
  [the restored exterior and retained interior contacts](implementation/KALINDRA.md).
- Temporary countryside shelters, Yog's tent and Kramer's wagon: `prepare_camps.py` and `author_camps.py`; see
  [the site purposes and review loop](implementation/CAMPS.md).
- Mine and three troll descents: `prepare_natural_entrances.py` and `author_natural_entrances.py`; see
  [the supported recesses and source routes](implementation/NATURAL_ENTRANCES.md).
- Sewer vault, grating and dry bank landing: `prepare_sewer.py` and `author_sewer.py`; see
  [the source location and support/review record](implementation/SEWER.md).
- Five town ground grilles: `prepare_town_sewers.py` and `author_town_sewers.py`; see
  [their distinct routes, fitted casings and review status](implementation/TOWN_SEWERS.md).
  `review_town_sewers.py` checks their written native geometry and bindings during the native build.
- Five ordinary town chests: `prepare_town_chests.py` and `author_town_chests.py`; see
  [their source identities, materials and review status](implementation/TOWN_CHESTS.md).
  `review_town_chests.py` checks native feet, body grounding, face bindings and clear sprite approaches during build.
- Six original water-contact wells use `prepare_source_wells.py` and `author_source_wells.py` in the active authoring
  path; `review_source_wells.py` checks their native support, roof winding, bindings and approaches during build.
  `render_source_well_study.py` also retains the isolated study; see [status and review evidence](implementation/SOURCE_WELLS.md).
  In Blender, run the study script with `REVIEW_PLACEMENTS: True` for all six actual-heightfield placements.
  It writes only its owned review scene/directory and does not regenerate the active map.
- Three original signs and the northern shrine: `prepare_source_signs.py`, `author_source_signs.py`,
  `prepare_source_shrine.py` and `author_source_shrine.py`; `review_waymarks.py` checks native support, artwork UVs,
  clear approaches and bindings. See [their source identities and review status](implementation/SIGNS_AND_SHRINE.md).
  `render_source_sign_study.py` retains the isolated sign study. The shared renderer accepts explicit `REVIEW_SCENE`,
  `REVIEW_SPEC` and `REVIEW_SEMANTIC` values for isolated studies without changing active map metadata.
  OBJ object labels use canonical semantic names, independently of Blender's duplicate-name suffixes in review scenes.
- Four shore message bottles: `prepare_message_bottles.py` and `author_message_bottles.py`; `review_message_bottles.py`
  checks their native support, local shore fit and bindings. `render_message_bottle_study.py` retains the isolated study.
  See [the waterside source identities and review record](implementation/WATERSIDE_FEATURES.md).
  `study_waterside_features.py` also produces the proposed wreck/bottle placement diagrams without changing active geometry.
- Four original melon patches: `prepare_melon_patches.py` and `author_melon_patches.py`;
  `render_melon_patch_study.py` retains the repeated source study. `review_melon_patches.py` checks written native
  bindings, fruit support and terrain-edge grounding. See [source identities and review status](implementation/MELON_PATCHES.md).
- Broken river ship: `prepare_wreck.py`, `author_wreck.py` and `render_wreck_study.py`; `review_wreck.py` checks
  native binding, shoreline contact and the submerged keel. See [the repeated waterside review](implementation/WATERSIDE_FEATURES.md).
- Barbarian camp: `prepare_barbarian_camp.py`, `author_barbarian_camp.py` and `render_barbarian_camp_study.py`.
  The active authoring/scenery path includes its prop-owned native fire; [its contract](implementation/BARBARIAN_CAMP.md)
  records the explicit light radius and shared camp placeholder requirements.
- Closed pyramid: `prepare_pyramid.py`, `author_pyramid.py` and `render_pyramid_study.py`.
  [The source/review record](implementation/CLOSED_PYRAMID.md) includes the exact MM6 bitmap import into an MM5-local alias.
  `review_camp_pyramid.py` checks both features during native build, including buried supports and the fire override.
- Dark Grove climbing rig: `prepare_skyrope.py` and `author_skyrope.py`; see
  [the rope study, source routes and fitted map rig](implementation/SKYROPE.md).
- Falista/Nibbler native clearings: `prepare_clearings.py`, fitted by `prepare_scenery.py`; see
  [native ownership and open-space requirements](implementation/NATURAL_CLEARINGS.md).
- Explicit local venue event numbers: `implementation/venue_event_ids.json`. Add a unique declared ID for a new
  venue; preserve existing assignments when adding contacts elsewhere in the inventory.
- Northern gemsmith benches, stock and trade emblems: `author_workshops.py`; see
  [the workshop composition and review notes](implementation/GEMSMITHS.md).
- Reger, Luna and Vespar exterior fittings and Luna's three-socket altar: `author_retreats.py`; see
  [the retreat composition and review notes](implementation/RETREATS.md).
- Both river/islet bridges: `prepare_bridges.py` and `author_bridges.py`, called by the main Blender author;
  [bridge construction and review](implementation/BRIDGES.md) records geometry, landings and acceptance limits.
- Joe's schematic map merchandise: editable `implementation/art/mm5map.svg`. The specification command renders it
  with ImageMagick `convert` into the MM5-local 128×128 `mm5map.png`; SVG and PNG hashes remain in material provenance.
  The native 128×64 `mm5lunch.svg` absence notice uses the same path and belongs to Joe's existing counter event 117.
  `render_joe_study.py` provides isolated counter/oblique reviews without replacing active geometry.
  The same specification command renders the four original `mm5ruby`, `mm5emerald`, `mm5saph` and `mm5diamond`
  SVG trade emblems at their native 64×64 size. Sorted stock uses these colors without creating inventory items.
  Kalindra's original `mm5royal.svg` crown banner is rendered at native 128×256 through the same path.
- Gate/curtain geometry: `author_fortifications.py`, called by the same Blender author. Both gates remain open.
- World rim: `world_rim.py` prepares the contour in `implementation/world_rim.json` and authors the dry ledge,
  descending rock, river spill and impassable-space faces through the normal architecture path. The native builder
  preserves explicit surface flags and writes transparent `mm5void.png`. This requires the corrected terrain renderer
  described in [the rim review](implementation/WORLD_RIM.md); the previous shared executable may still contain the
  opaque fallback defect. The verified isolated executable is `/tmp/openyamm-mm5-rim-build/game/openyamm`.
  `prepare_rim_study.py`, `author_rim_study.py`, `render_rim_study.py` and `build_rim_study.py` retain the separate
  experiment workflow. Current studies use V5; historical directories preserve their original scripts and evidence.
- Training basin, well, nine source benches and six service-stock groups: `author_props.py`, called after fortification authoring.
  `implementation/prop_placements.json` records native ground support and adjustments around current geometry.
- Southern chapterhouse court: `author_chapter_court.py` adds one independently authored bench and partial bed edging
  through the main Blender author. `implementation/chapter_court.json` records support and the clear southern approach.
  The same module owns twelve explicit existing-plant anchors used by `prepare_scenery.py`; their fixed placement must
  pass clearance checks. `review_chapter_court.py` checks the written native props and plant identities after building.
- Native foliage and barrels: `prepare_scenery.py`, invoked by the native build. `implementation/scenery.json`
  retains original/fitted anchors, native descriptor/art provenance, orchard identities and local event IDs.
- Three selected southern woodland-floor pockets: `prepare_regional_understory.py`. Explicit `sceneryGroups` in the
  specification become semantic `scenery_groups` and native sprites through the normal build. They add no BModels,
  trees, interactions or actors. No venue-clearance rectangle is imposed on these ground-detail groups; fixed anchors
  must pass native terrain/collision checks while retaining all existing scenery placements.
  [Regional observations and review](review/region_composition_v1/checkpoint.json).
- Native map and world staging: `build_native.py`; output `implementation/runtime/worlds/mm5/`.
- Terrain materials: `terrain_materials.py` composes the Acid Pond surface registry and original donor aliases;
  `terrain_tiles.py` assigns native material/road selectors. See [material ownership and review](implementation/TERRAIN_MATERIALS.md).
  `review_terrain.py --source --version <review-directory>` checks authored arrays before native compilation;
  omit `--source` to check the written ODM. `render_terrain_materials.py` runs through Blender MCP for actual source views.
  `author_desert_materials.py` authors the twelve active native-resolution sand/dirt transitions and two endpoint checks
  through Blender MCP into `implementation/art/desert_terrain/`. Rebuilding embeds their hashes and copies their textures.
  `review_desert_material_study.py` and `build_desert_material_study.py` retain the isolated corrected study.
  Its local native views pass and the same selectors are integrated into the canonical map.
- Isolated test installation: `/tmp/openyamm-mm5-castleview/`. Existing stages require this project's ownership marker.

## Architectural specification

`audit_architecture_spec.py` reconciles all 45 premises, source people/services, attached interior contacts, component
identities and venue transforms. [Its evidence](review/architecture_specification/README.md) covers milestone 1;
[town detail completion](implementation/TOWN_DETAIL_COMPLETION.md) records exterior court/identity acceptance.

```sh
python3 level_generation/projects/mm5_castleview_kalindra/prepare_architecture.py
python3 level_generation/projects/mm5_castleview_kalindra/prepare_roads.py
```

## Blender authoring and visual reviews

Use the [Blender MCP procedure](../../BLENDER_MCP_STARTUP.md). Through `execute_blender_code`:

```python
from pathlib import Path
project = Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/mm5_castleview_kalindra')
for name in ['author_architecture.py', 'render_architecture.py']:
    path = project / name
    exec(compile(path.read_text(), str(path), 'exec'), {
        '__file__': str(path), '__name__': '__main__',
        'REVIEW_VERSION': 'architecture_current',
    })
```

The author replaces only its owned scene. Save deliberate manual edits before regenerating it. Default selection is
all 24 town assemblies, four countryside gemsmith workshops, Reger/Luna/Vespar retreats, Luna's altar, central fountain,
training basin, well, benches, stock, both gates, full curtain, both bridges, the Great Western Tower, Kalindra,
Dreyfus/Justine shelters, Yog's camp, Kramer's caravan yard, the mine, all three troll descents and the sewer outfall.
Falista/Nibbler additionally use source-owned native scenery. The Skyroad rig has local native silhouette/access/click/reload review; [site preparation](implementation/REMAINING_COUNTRY_SITES.md)
records their measured ground and construction requirements. Local native acceptance is recorded in the linked review notes.
[Natural-site source evidence](implementation/NATURAL_SITES.md) retains their original entrance/return records and
the source river-bank placement retained by the supported sewer landing.
Forge details include an anvil/ore bin;
herbalist and keeper sheds include drying shelves and a kennel. The tavern has a lower entrance wing, and the
two craft venues have unequal shallow work canopies. Render outputs are
review-only, with native-unit camera metadata. Inspect actual images before accepting any revision.
The jail has a barred threshold; Joe uses a counter/display binding instead of a house door. The storehouse's two
long roofs use `ridgeAxis: y`, and the Gremlin court keeps its lower controlled entry in front of the taller hall.
Ellinger is an original octagonal tower; the temple has unequal lower wings and a polygonal apse.
For workshop views pass `REVIEW_IDS: ['ruby', 'emerald', 'sapphire', 'diamond']`; the renderer includes front,
oblique and rear sorting-yard views. The painted emblems are decorative; the ordinary doors dispatch their venues.
For the Western Tower pass `REVIEW_IDS: ['western']` and `REVIEW_TERRAIN: True`; its views include the full shaft
from player height and the elevated roof doorway. `heightAbovePad`/`localDepth` locate elevated venue faces;
`baseHeight` locates the upper house. Those venues are excluded from ground road/frontage and scenery-approach checks.
For Kalindra pass `REVIEW_IDS: ['kalindra']` and `REVIEW_TERRAIN: True`; views include the courtyard and its open exit.
Terrain eye cameras sample ground at the actual camera position before adding eye height. Optional `REVIEW_VIEWS`
selects named views for a focused repeated review; save changed views under a new review version.
For temporary sites pass `REVIEW_IDS: ['dreyfus', 'justine', 'yog', 'kramer']` and `REVIEW_TERRAIN: True`.
The author creates visible camp counters or a tent flap for the existing venues; it does not add ordinary house doors.
For the mine and descents pass `REVIEW_IDS: ['mine', 'troll_a', 'troll_b', 'troll_c']` and `REVIEW_TERRAIN: True`.
Their natural recesses use fitted walking floors and dark end faces with local placeholder bindings.
For the sewer pass `REVIEW_IDS: ['sewer_out']` and `REVIEW_TERRAIN: True`; inspect front, oblique and rear
views, then actual native water context and ordinary bank access.

For service equipment pass `REVIEW_IDS: ['forge', 'training_pool']`. The basin's neutral-plane Blender view
checks geometry only; inspect its retaining wall and northern step against native terrain in the actual game.
For gate views pass `REVIEW_IDS: ['pass_gate', 'west_gate']` to the renderer. For full curtain context pass
`REVIEW_IDS: []` and `REVIEW_WALLS: True`; those views use the actual heightfield with neutral ground material.
`review_fortifications.py` checks the authored solids against all planned premises and the snapped road graph.
The source audit does not replace native visual or movement checks.

## Native build and readback

```sh
python3 level_generation/projects/mm5_castleview_kalindra/build_native.py
python3 level_generation/projects/mm5_castleview_kalindra/review_terrain.py --version terrain_current
python3 level_generation/projects/mm5_castleview_kalindra/review_fortifications.py
```

`review_roads.py` independently compares written road artwork ports and painted edge coverage with the route graph.
It runs during native build, but does not certify local street grade or player-height appearance. See
[the diagonal-road native review](review/roads_v2/native_review.json) for that distinction.
For aerial diagnostics only, `capture_gameplay.py --diagnostic-flying` enables flight in the isolated capture settings
after faithful save preparation. Use a `J` hold action to ascend; an elevated `--pose` alone can fall during loading.
The capture metadata labels this override. Ordinary access/collision evidence must keep it disabled.

This uses the existing `build/editor/openyamm-editor` with `--world mm5`, a fresh temporary source package and an
isolated composed base. It checks terrain arrays, model/entity counts and native door bindings, and writes
`review/native/build.json` plus the build log.
All BModel material keys must fit the native ten-byte texture-name field. The builder rejects overlong/non-ASCII
keys before export and compares every written model's material set with its source, using native case-insensitive lookup.
`review_environment.py` refreshes baseline identity coverage, main-shell terrain support and the 45-premises
`review/native/interaction_inventory.json` after every build;
additional site props such as the training basin are reported separately from the 698 original decoration records. It does not certify runtime clicks or visual completion.
The temporary package snapshots referenced OBJ files too; the report records their hashes and the resulting ODM hash.
`review_bridges.py` checks the actual exported walking faces, beam undersides and buried structural feet against
native triangles. These checks complement the required native visual and ordinary movement evidence.
`review_watchtower.py` checks both actual native door elevations, the upward terrace face and roof approach support,
the elevated house's skirt and retained inactive arrival markers. Roof walking/click/save-reload captures provide
the separate runtime evidence; the initial review party pose on the terrace does not implement Skyroad travel.
`review_castle.py` checks Kalindra's native paving clearance, buried arch/bench feet, single door quad/event,
retained interior contacts and inactive return marker. Native passage traversal and placeholder clicks remain
separate visual/runtime checks.
`review_camps.py` checks native temporary-structure feet, supplies/counter support, four wheel tread contacts,
retained residents and the corresponding event bindings. Actual game reviews verify appearance, access and clicks.
`review_natural_entrances.py` checks the mine/troll native walking floors, upward winding, grade, buried supports,
recessed event faces and inactive return markers. Actual native movement and click evidence remain separate.
`review_sewer.py` checks native ramp/landing faces, grade, buried supports, water-level clearance, rear skirt
separation, grating event faces and inactive return marker. Actual shore appearance and access remain runtime checks.
`review_clearings.py` checks native-only site ownership, exact descriptor IDs/grounded anchors, instance-local
stump events, and empty approach/future-crop reservations. Actual native crown/root and click views remain separate.
`review_skyrope.py` checks the rope contact, written coil grounding, nondegenerate native faces, inert anchor tree
and inactive return. Native full-silhouette/attachment, movement and click review remain separate.

The source has 692 foliage/rock/stump sprites, six stat barrels and one campfire, plus the invisible start marker. Native descriptor
numbers are one-based; entity descriptor IDs are number minus one. Food/reward orchard trees and all six barrels use
`event_id_secondary` for instance-local status handlers. The engine skips intrinsic decoration reward bindings for
these explicit script events. Keep this distinction when adding further interactive props; event zero is not proof
that a native descriptor is inert. The well is a newly authored BModel with its own local event. Reward rules remain
documented source data and are deliberately not executed by this environment milestone.

The MM5 manifest's `sourceGame: mm8` describes the reused asset/runtime baseline; its actual identity and map
registration are `mm5`. Dependencies name the MM8/MM7 donor worlds. The isolated global terrain registry appends a
compact palette of actual donor bitmap/flag records, avoiding the four-bank waste from duplicate base textures.
`implementation/terrain_rows.tsv` records those additions; original base rows are left intact. Pending reserved slots
are never selected by the map. A later deployable composition must retain this explicit base registration.

No compilation is needed for content-only revisions when the required binaries match the current build path.
If shared compiler/runtime code changes, follow the repository build commands and run focused affected checks.

## Ordinary game view and native door click

After a completed native build, prepare an ordinary playtest start:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/prepare_playtest.py \
  --binary /home/pjasicek/github/OpenYAMM/build/game/openyamm
/tmp/openyamm-mm5-castleview/play-mm5.sh
```

Choose **Load Game**, then `castleview_start`. This uses the established five-member level-25 calibration party,
with 50,000 gold and 40 food; it is an exploration fixture, not the future campaign's starting balance.
Build the current shared renderer and map-presentation changes before preparing the launcher. They include the
transparent-terrain correction, world-declared minimap selection and cropped-image exploration mapping. The review
records each executable hash; the current reviewed snapshot is `/tmp/openyamm-mm5-minimap-reviewed` to avoid
unrelated development rebuilds changing an in-progress capture or playtest.
The launcher explicitly selects MM5 and opens the main menu. Settings and ordinary saves live under
`/tmp/openyamm-mm5-castleview/playtest/`; preparation replaces only its owned starting save and retains other saves.
Previous versions of that starting slot are preserved by hash under `playtest/previous_starts/` before replacement.
`review/playtest/latest.json` records the native, binary, party-fixture and starting-save hashes.
Use `--stage /path/to/owned/stage` after building to a different isolated stage. This remains a development checkpoint
with donor assets mounted from this checkout; it is not the final distributable package.

```sh
xvfb-run -a -s '-screen 0 1600x1200x24' python3 \
  level_generation/projects/brackenford_greywatch/capture_gameplay.py mm5_guild_review \
  --world mm5 --control-scheme classic --map mm5_sw.odm \
  --stage /tmp/openyamm-mm5-castleview \
  --review-directory level_generation/projects/mm5_castleview_kalindra/review/gameplay \
  --pose 200 -3408 672 0 0 \
  --actions level_generation/projects/mm5_castleview_kalindra/review/gameplay/guild_classic_actions.json \
  --warmup 2 --seconds 3
```

The harness makes a faithful scenario save, loads it through the actual game menus, and records screenshots plus
binary/settings/native hashes. Inspect the `_click.png` image and log: successful execution alone does not establish
correct visual state or click dispatch. Use distinct capture names to preserve historical evidence. Rendering requires
the graphical execution permissions of the local environment.

The gate traversal captures use `south_gate_walk_up_actions.json` and `west_gate_walk_up_actions.json` in
`review/gameplay/`. The harness supports a bounded `hold` action; the current classic forward binding is `Up`.
Use new capture names when repeating checks, and inspect both outside/inside views before claiming traversal.

The well/barrel/shared-house checks use `well_props_actions.json`, `barrel_props_actions.json` and
`workers_props_actions.json`; these click the actual view and then use `F9` to make an ordinary quicksave.
The well check supplies `low_gold_party.json` so its future charity threshold would be satisfied. These are isolated
test-party fixtures, not map population. Existing `build/tools/openyamm_levelgen_inspect_save` reads health, inventory,
gold and food for before/after comparison; the barrel evidence additionally records the selected member's stat fields.

## Native minimap bake and world presentation

After a successful source build, run `build_minimap_blender.py` through Blender MCP. It imports the **written ODM**
terrain, palette lookups, visible BModel faces and native UVs into an owned review scene. Inspect the generated
`review/native_minimap_v1/travel_crop.png`, `full_terrain.png` and `town.png`. The travel image uses X/Y ±24,576;
the separate full-terrain image includes the scenery buffer. Billboard sprites are omitted from this bake.

Then stage the inspected crop and its provenance:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/stage_minimap.py
```

This writes the world-local `ui/maps/catalog.yml`, `mm5_sw.png` and provenance into the runtime package and owned
stage. It rejects a stale native/render hash or changed crop contract. The catalogue retains exploration fog.
`OutdoorWorldRuntime` and `IndoorWorldRuntime` now honor a declared presentation for any world. The shared journal
converts image coordinates back to world coordinates before sampling the existing native exploration save mask.
Original map presentations and save-mask coordinates remain intact.

Inspect a normal map-book view at a town landmark and a distant road, plus save/reload, after staging. Re-bake after
later geometry or terrain changes; this intermediate minimap does not satisfy the final-map gate until it matches
the finished environment. See `review/native_minimap_v1/native_review.json` for current evidence and limits.

## Inner bank/diviners road grade

`grade_inner_road.py` owns nine bounded height adjustments. Run it before geometry authoring when applying this
revision to the earlier landscape draft; the full `build_landscape.py` generator also applies it before writing
its height outputs. It updates U8/raw/U16 height assets and explicitly separates graded supporting vertices from
remaining flat-pad constraints. Building floor elevations stay at 640 and 864.

`prepare_architecture.py` declares Oorla's three step bounds and refits the nearby source chest to the changed slope;
`author_architecture.py` builds them through Blender MCP. The existing scenery fitter reserves the detail bounds.
`review_inner_road.py` checks actual written treads, upward winding, support burial, leading riser, threshold alignment,
scenery clearance and lane crossfall during the full native build. Player-height appearance and ordinary movement
remain separate required checks. The 311-model build and all 20 readback audits passed; see
`review/inner_road_grade_v1/native_review.json` for actual walking, named click, reload and grounding views.

## Placeholder handler smoke

Run `python3 level_generation/projects/mm5_castleview_kalindra/review_placeholder_handlers.py` after generating map
Lua. It executes every registered handler in Lua with only the permitted status-text API, rejects unexpected lifecycle
behavior and matches registrations to the source event inventory. Results and the actual Lua hash are retained in
`review/placeholder_handlers/smoke.json`. This is the all-handler smoke check; native picking, descriptor overrides,
population channels and ordinary save-state behavior still need the separate readback/runtime evidence.

## MM5 common-script policy

`implementation/world_policy/events/common/cross_continents_common.lua` is the authoritative, deliberately inert
MM5 override of the shared cross-continent common script. It prevents this environment-only world from registering
Verdant contact, the recurring cross-continent timer, chest-scroll rewards or connector-stone hooks. The active world's
file takes precedence at that exact virtual path; no generated Global.lua or original-world script is edited.
The shared loader may concatenate multiple common files, so merely adding `world_common.lua` is insufficient.

`build_native.py` stages this policy through `stage_script_policy.py`. A script-only revision can be staged without
recompiling unchanged geometry:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/stage_script_policy.py
```

`review/script_policy_v1/runtime_review.json` records the observed former global timer 65201 and the fresh
540 → 560 → save/reload → 580 minute check after applying the policy. All three current saves have zero outdoor
actors, timers and world items. This does not claim that shared NPC table entries are absent; those registries remain
part of the base. Replace the explicit policy during future campaign implementation.

The playtest manifest now includes hashes of world-local Lua and the staged minimap provenance. The current
311-model minimap evidence is `review/native_minimap_v2/native_review.json`; the prior shared MM8/MM9 regression
evidence remains under `native_minimap_v1`. To retain earlier review images on future bakes, pass `MINIMAP_OUTPUT`
to the Blender execution globals and the matching `--review` directory to `stage_minimap.py`.

## Unavailable regional foot routes

`author_route_placeholders.py` appends two source-owned, invisible pressure-plate BModels for `sw_sc` and `sw_nw`.
Each is a 512×1,536 strip on the inside of the existing travel boundary. Six upward faces follow the actual native
terrain triangles at a one-unit offset; arrivals and visible terrain/roads are unchanged. The normal event generator
uses their explicit `Invisible | PressurePlate` attributes instead of the default clickable-door attributes.
Local events 4000/4001 emit only the named unimplemented status. They specify no destination, days, rewards or timers.

`review_route_placeholders.py` checks written faces, winding, attributes, events, ground offsets and scenery clearance
as part of the native build. `review_route_plan.py` regenerates the annotated source plan. Source obliques and plan
are in `review/travel_placeholder_v1`; actual native approach, feedback, return and reload remain separate required
evidence. See that directory's `checkpoint.json` before treating the route work as accepted.

## Ranger woodcraft source study

`author_ranger_yard.py` and `render_ranger_yard_study.py` define and inspect the proposed lodge workbench, short timber
stock, chopping block and embedded axe. The latter uses an isolated Blender scene and output directory, so it can
run while a preceding native package compiles. Pass `REVIEW_VERSION` to preserve earlier images. The revised blade
and actual-site source views are in `review/ranger_yard_v2/source_review.json`.

The group is now integrated through `prepare_architecture.py` and `author_architecture.py`. Five fixed native
`plant26`/`plant32` anchors form a small practice garden north of the open lodge approach. The source-owned prop
reserves its working-ground footprint; `prepare_scenery.py` checks both the plants and clear approach without moving
rejected garden anchors. `review_ranger_plan.py` regenerates the physical placement plan. `review_ranger_yard.py`
checks actual native support vertices, burial, retained plant IDs and inert bindings during the native build.
See `review/ranger_yard_v3/checkpoint.json` for current build and player-height acceptance status.

The first close orthographic context views began some rays inside neighbouring roof volumes. The corrected camera
stays on the same viewing axis but farther back, retaining the intended projection while clearing foreground roofs.
Keep that camera placement in `review/ranger_yard_v3/blender/oblique_camera.json` when repeating this context.

## Frontage sign source study

`author_frontage_signs.py` defines three named mapmaker plaques and two craft signs supported under the existing
canopies. The original SVG artwork is in `implementation/art/mm5{jethro,lydia,miles,tailor,cobble}.svg`.
Rasterize each SVG with `convert INPUT.svg -strip review/frontage_signs_v1/art/KEY.png`, then run
`render_frontage_signs_study.py` through Blender MCP. It owns an isolated scene and study OBJ outputs; it does not
change the canonical source/native map. The default views are supplemented by a wider craft-frontage view.

See `review/frontage_signs_v1/source_review.json` for inspected images, the corrected lettering-overlap defect and
remaining native checks. The 314-model baseline is preserved in that review directory's `before/` tree. The signs
are integrated through `prepare_architecture.py` and the existing `Author.service_details` path; the study uses
that same geometry ownership. The native readback checks artwork extent, outward winding, mount vertices and
inert faces separately from the existing venue-door events. See `checkpoint.json` for native build/review status.

## Public notice source study

`author_public_notices.py` defines three wall-mounted displays in the guild, mayor and hiring-office facade bays.
Their original SVGs are `mm5guild`, `mm5civic` and `mm5hiring` under `implementation/art/`. Rasterize them to
`review/public_notices_v1/art/` with `convert INPUT.svg -strip OUTPUT.png`, then run
`render_public_notices_study.py` through Blender MCP. The study owns its scene and output models, preserves the
canonical package, and adds an offset civic-frontage camera because the standard centered view crops that board.
The three notices are integrated through `prepare_architecture.py` and `author_architecture.py`; the study uses
that same ownership. `review_public_notices.py` checks written artwork extents, fitted envelopes and inert faces
during the native build. Source review is in `review/public_notices_v1/source_review.json`; consult `checkpoint.json`
for the current native build and actual view status.

## Training-yard targets

`author_training_yard.py` defines a padded striking post and a timber shield target in the two clear south wall bays.
Run `render_training_yard_study.py` through Blender MCP with `REVIEW_VERSION='training_yard_v3'` for the reviewed
revision. The study includes the hall and actual pool and owns its own scene/OBJ outputs. The main prepare/author
paths now integrate both targets as inert source-owned props. `review_training_yard_plan.py` overlays conservative road-tile envelopes, the hall, pool,
both service approaches and target footprints at native scale. The corrected shield UVs use the native wood's
actual 32×64 dimensions. Source evidence and integration work are recorded in `review/training_yard_v3`.

## Remaining working settings and fountain seating

`author_town_working_details.py` defines the hiring repair table, keeper workbench, Nadia storage, workers sweep
tools and one public bench facing the fountain. The main prepare/author paths now integrate all five as inert props. Run
`render_town_working_details_study.py` through Blender MCP with `REVIEW_VERSION='town_working_details_v4'`.
The study preserves canonical source and the running native build. Its source review and full-road-tile/native
scenery placement checks are in `review/town_working_details_v4/`. Native build and actual review are tracked
in that directory’s `checkpoint.json`.

## Isolated delivery

`build_delivery.py --output <new-directory>` freezes the current native world, accepted minimap, refreshed starting
save, reviewed executable and the three composed global registries. It verifies native/source/save provenance and
records hashes of the required donor registry, script and artwork dependencies. It does not imply visual acceptance.

The copied `install_delivery.py` requires `--base-assets <existing-assets_dev> --destination <new-directory>`.
It verifies the bundle and pinned dependencies before composing an isolated installation. Package metadata and
registry files are copied; complete artwork/map/event directories are mounted, matching `build_native.py`.
Do not replace this with individual file or whole-world symlinks: those prevented native table/manifest lookup in
rejected delivery candidates v1/v2. Candidate v3 passes the fresh-start/population/reload scenario.

The installation has `play-mm5.sh`, `playtest/settings.ini` and `playtest/saves/castleview_start.oysav`.
For capture tooling, pass `--stage <installation>/playtest --binary <installation>/bin/openyamm` so its actual
asset-root settings are used. See [delivery instructions](DELIVERY.md) and [installed runtime evidence](review/delivery_v3/runtime_review.json).
The final gate-deck correction, minimap v9, refreshed save and installed release are accepted; see
[final delivery evidence](review/delivery_final/runtime_review.json) and [release provenance](delivery/latest.json).
