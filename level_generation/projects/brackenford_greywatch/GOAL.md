# Test goal: generate two original, playable MM8-style maps

## Objective

Create and integrate two new maps in OpenYAMM using Blender MCP and the workflow in
[/home/pjasicek/github/OpenYAMM/level_generation/README.md](/home/pjasicek/github/OpenYAMM/level_generation/README.md):

1. **Brackenford**, a native outdoor ODM inspired by MM8 Ravenshore (`out02.odm`).
2. **Greywatch Vault**, a native indoor BLV inspired by MM8 Naga Vault (`d18.blv`).

These working location names are new; their inhabitants, dialogue topics, service profiles, monsters, items, textures
and decoration art must come from existing MM8 content. Produce original layouts and a coherent playable environment.
Do not duplicate, mirror, rotate, slightly deform or retexture the reference maps and call them new maps.

The result must load and work in OpenYAMM, with native geometry, actual gameplay bindings and completed Lua. Blender
renders, a greybox, a design document, placeholder events or an untested export are intermediate results, not completion.
Implement and validate the necessary missing generation/export tooling as part of this goal. Follow repository AGENTS.md.

## Scope and authority

### Unattended execution and completed Blender preflight

The driver explicitly authorized proceeding without routine confirmations and will be away. Use the concrete brief and
record reasonable design choices instead of waiting for approval of each modeling, texturing, export or review step.
This does not override actual platform/sandbox permission boundaries.

On 2026-09-06, the connected Blender 5.2.1 LTS instance passed live MCP tests without an approval prompt for scene
inspection, Python mesh/material edits, rendering, writing a `.blend`, OBJ import/export and viewport screenshots.
Workspace create/read/write/cleanup and the existing NumPy/Matplotlib/Pillow/PyYAML dependencies also passed.
The local Codex config already has `approval_mode = "approve"` for `get_scene_info`, `get_viewport_screenshot` and
`execute_blender_code`. Use these core tools for the requested Blender workflow. Keep writes in the OpenYAMM workspace
or `/tmp`; use installed tools and local MM8 assets. No external asset service or new Blender add-on is needed by this brief.

The optional `get_addon_status` diagnostic returned `No module named 'blender_mcp.config'`; the live core tool tests still
passed. Do not make that optional version check a blocker or reinstall/restart the working connection solely for it.
Connection loss, new dependency requirements or operations outside the authorized filesystem can still require separate
handling; a successful preflight is not a guarantee against every future environment failure or approval boundary.

### Work location and changes

Work in `/home/pjasicek/github/OpenYAMM`. Keep authoring sources, manifests and review evidence under
`level_generation/projects/brackenford_greywatch/`. Mount the resulting content through the existing world/mod package
architecture, in an MM8 context, with unique registered identities. Suggested native basenames are `lg01.odm` and
`lg02.blv`; validate filename/ID constraints and collisions before adopting them. Do not overwrite `out02`, `d18`, or
another original map. Do not change shared MM8 NPCs, shops, species or quest behavior globally to implement a local copy.

This goal authorizes map generation, required compiler/exporter fixes, map-local Lua, scoped content registrations,
integration and validation. Preserve unrelated workspace changes. Do not publish, deploy, push or send messages to others.
Do not stop for approval of normal modeling choices; record reasonable assumptions and proceed. Ask only when a missing
decision would materially alter the intended result or an actual permission boundary requires it.

### Two maps, two exterior dungeon entrances

The default interpretation is **exactly two new native map files**. The outdoor map has two distinct dungeon entrances:
an imposing castle entrance and a cave mouth in a hillside. They enter different, named arrival points in Greywatch Vault.
The castle enters the upper architectural entrance hall; the cave enters a lower rough service passage. Connect them
through the dungeon with an initially closed, operable shortcut so the two approaches feel different and have useful
return routes. These are two entrances to one connected dungeon, not a claim that two independent interiors were built.

Both entrances must work and must return to the correct outdoor doorway. Never send the party to original Ravenshore
when leaving the generated dungeon. Do not quietly create a third map or reuse the original Wolf Den as the second
interior. A later explicit driver instruction can revise this scope before implementation.

## Required references and planning

Read the playbook and its linked authoring contract, gameplay/scripting guide, pipeline status, marker definitions and
review gates. Inspect at least these local studies and source maps:

- Outdoor: Ravenshore `mm8/out02`; use Castle Ironfist `mm6/outd3` or Free Haven `mm6/outc2` for road/settlement structure
  only, keeping the generated map's asset selection MM8-owned.
- Indoor: Naga Vault `mm8/d18`, plus Ilsingore's Cave `mm8/d48` for the rough lower entrance and appropriate cave walls.
- Add a mechanism reference from the existing studies when needed for the lift, controls or hidden door.

Before modeling, save annotated reference plans and inspect textured oblique views, indoor ceiling-free views and
relevant eye-height details. Prepare an original scaled outdoor plan, indoor room/portal graph, elevation annotations,
mechanism state graph, service/NPC inventory, event inventory, spawn/arrival manifest and texture-key palette.
Write a short comparison explaining which qualities are borrowed and how the new layouts differ substantially.

The plans must guide structured geometry and event data; a generated minimap image is not a substitute for coordinates,
connectivity, tile assignments or semantic IDs. Keep stable identities across iterations and regenerate from source.

## Outdoor map: Brackenford

### Landscape, water and roads

Create a recognizable MM8 grassland region with an original, non-flat native ODM heightfield: rolling land, a raised
castle site, a cut hillside for the cave entrance, and believable passes or valleys where roads leave the region.
Keep the town's main streets comfortably walkable while allowing terraces and gentle elevation changes. Do not flatten
the whole landscape to simplify placement, and do not copy Ravenshore's height samples.

Use existing MM8 terrain tile families and transitions. Author the new terrain on, or resample it to, the native
128 × 128 height grid. Export native height/tile/attribute arrays, with correct quantization and terrain triangle split.
The continuous ground must be native ODM terrain. Use BModels for structures and shapes that cannot be heightfields.

Include a modest river, with an optional small pond/lake, occupying a subordinate part of the playable landscape.
Build a functional bridge along a useful road. Fit banks, shore tiles, water behavior and bridge approaches correctly;
no magenta transparency edges in the actual game, floating foundations, coplanar paving or impassable bridge lips.

Connect town streets, the stables, bridge, both dungeon approaches and the regional exit roads into a coherent route
network. Roads must use correct existing tile variants/transitions where represented as terrain. Review junctions,
corners, slopes and building thresholds at ground level. Add two distinct regional exit approaches integrated with
existing MM8 travel/navigation content; make their destinations and a route back to the new region explicit and tested.
The new region is not a seamless geographical replacement for Ravenshore; document its test-world connections.

### Town and services

Target **24 principal town buildings**, with a permitted range of 20–28 if the reviewed layout benefits. The castle and
cave entrance are additional landmarks. Use an intelligible square/street plan, smaller residential clusters and usable
space around doors. Every building intended as a house/service must have a meaningful working target. Decorative sheds
are acceptable when visually distinct from enterable houses.

Include these working places:

- One recognizable city/civic hall on the main square.
- One weapon shop, one armor shop and one magic-item shop with actual MM8 service behavior and inventories.
- Stables with an existing MM8 stablemaster/service presentation, a real schedule/travel action and a tested destination.
- A tavern, temple/healer, training hall and alchemist, using existing MM8 equivalents.
- At least four existing MM8 teachers covering different skills, each with working existing teaching conditions/actions.
  They can occupy residential houses; do not require a separate new character for each shop or teacher role.
- At least six additional resident dialogue interactions drawn from existing MM8 characters and ambient topics.
  Choose suitable existing conversations without requiring unrelated campaign quest progression.

Reuse MM8 names, portraits, greetings, topic text and service/teacher behavior. Do not invent NPC names, biographies,
dialogue or classes. New scoped instance/house IDs are allowed when necessary to preserve ownership, but their content
must be traceable to the original MM8 records. Avoid duplicating one person visibly across several town roles.

Existing Ravenshore profiles to inspect in the current merged `house_data.txt` include:

| Role | Existing profile to inspect | Current house ID, verify before use |
| --- | --- | --- |
| Weapon shop | Keen Edge — Reaver | 2 |
| Armor shop | The Polished Shield — Walvis | 37 |
| Magic shop | Needful Things — Jed | 77 |
| Stables | Guild Caravans — Wayland | 452 |
| Tavern | Kessel's Kantina — Kessel | 229 |
| Temple | Sanctum — Maricia | 304 |
| Training | Gymnasium — Yarin | 1565 |

These are reference profiles, not instructions to hijack the original instances or their travel/quest state. Resolve
canonical/import identities using the current tables and record the provenance of every reused NPC, topic and service.

For the **city hall**, use an MM8 merchant/council-style civic interior and existing MM8 characters/topics. Do not pull a
MM6/MM7 Town Hall clerk from the merged table merely because its row says “Town Hall.” The building can be called a city
hall without inventing a new character or importing another game's bounty system. It must open a usable civic dialogue
with suitable existing MM8 content. Avoid exposing copied story actions whose original-map assumptions are invalid here.

For buildings other than the castle, reuse or generate geometry at your discretion. In either case arrange an original
town, use existing MM8 textures at appropriate scale, and check geometry/UVs/thresholds in the native result.

### Population, safe town and hard wilderness

Place approximately **8–10 guards and 16–24 villagers** using existing MM8 actor art/definitions, with appropriate local
group/hostility and placements. Town NPCs must not start hostile to the party or fight one another because of reused
species defaults. Use established runtime behavior and map-local data, not a global monster-table mutation.

Use a documented baseline test party around **level 25**, with ordinary appropriate MM8 equipment and no invulnerability,
invisibility or debug combat advantages. This is a rich midgame test region, not a starter map.

Outside town, create separated hard encounter packs suited to grassland/woodland: primarily **MM8 Ogre Warriors and
Ogre Mages**, including stronger existing variants, with an optional remote Dire Wolf pack. A useful starting pack is
4–6 melee ogres plus 1–2 ogre casters; adjust count/variant against actual combat tests rather than inventing new species.
Configure map-stat encounter families/weights and the actual spatial spawn records together. Do not populate from
map stats alone, and do not accidentally double-spawn fixed actors and encounter groups.

Keep dangerous packs well outside the town's occupied/used area, including the stables and main approach roads. Start
with a generous separation of roughly 8192 game units from town activity, then tune using actual detection, wandering,
projectile reach and terrain/LOS tests. That number is a design starting point, not an engine aggro guarantee.

The party must be able to arrive, stand in the square, visit all normal services and walk the town perimeter without
remote wilderness packs acquiring it or peppering the town with projectiles. Test at least five minutes of normal town
activity and observation with relevant actors active. Do not simulate safety by freezing all wilderness AI, lowering
the global detection range, making the whole town invulnerable or disabling enemies. Deliberately pulling a pursuing
pack into town is outside the normal no-aggro promise; state and test the intended behavior separately if supported.

### Loot and outdoor interactions

Set the outdoor map's **treasure level to 6**, validating the effective value after any difficulty/bolster overrides.
This intentionally exercises high-tier rewards; do not copy Ravenshore's current low treasure setting.

Build **two clearly separated wilderness loot sites**, away from ordinary town traffic. Each has:

- Two working chests with explicitly configured high-quality loot templates, distinct slots and open-event bindings.
- Two or three good existing MM8 items visibly placed on the ground nearby, with correct terrain contact and pick-up.
- A purposeful ogre guardian encounter, adequate combat space, and a readable approach and escape/return path.
- Placement that makes the reward appear guarded, not an accidental item pile beside an unrelated spawn.

Correlate raw chest template levels with map-stat treasure remapping, trap/disarm settings and refill policy. Inspect
actual generated chest contents across several seeds. Use real MM8 items; no invented item definitions are required.
Verify opening, looting, loose-item pickup, save/revisit and intended refill without duplicate rewards.

Add one obelisk on a scenic optional route. Reuse an MM8 obelisk model/texture and existing MM8 inscription text, with a
working click target and visible response. Record its discovery in isolated test-map state; it must not silently advance
the original campaign's obelisk quest or grant its treasure. Add a town well or fountain with one existing MM8-style
effect, an explicit charge/reset policy and tested repeat behavior.

### Two dungeon exteriors

1. **Hillside cave:** a rough cave mouth visually built into the terrain, with sloping rock sides and a fitting trail.
   Inspect Ravenshore's Dire Wolf Den exterior for construction language; generate a new mouth/arrangement. The native
   heightfield cannot contain a true undercut: combine it with appropriate entrance BModel geometry and a BLV transition
   without exposing a terrain sheet across the visible mouth.
2. **Greywatch castle:** generate an original, larger and imposing castle BModel composition using existing MM8 stone,
   roof, trim and door textures. Give it a strong silhouette, substantial entrance, towers/walls and a convincing raised
   site. Do not reuse an existing complete castle mesh or provide only a painted flat facade. It should be visibly more
   important than the town houses, with a usable approach and no terrain intersections.

Both entrances need hints, correctly bound event faces, safe arrival anchors, facing and tested bidirectional travel.

## Indoor map: Greywatch Vault

Use Naga Vault's compact linked polygonal rooms, bent passages, repeated masonry language, guarded treasures and
mechanism rhythm as references. Create an original floor plan. Reuse suitable existing MM8 textures, including d18's
palette where appropriate. The cave-entry section uses a restrained compatible rock palette and irregular sloping walls.

Target **8–12 meaningful chambers**, plus connectors and the lower cave approach. Room count is a design target, not a
sector count: author the actual sectors and portals required by visibility and elevation. Reserve the empty sector-0
convention and generate/validate derived data rather than depending on AABB guesses or manual finishing.

Required spatial and gameplay features:

- Upper castle arrival hall and lower cave arrival, with separate source/destination identities and safe landing areas.
- At least three useful floor elevations, connected by actual stairs. Keep elevation changes playable and visible in
  the plan/sections; a single sloped floor covering the whole dungeon does not satisfy this.
- A main progression route, at least two optional reward branches, and an unlockable shortcut between entry approaches.
- At least four operable doorway mechanisms, including one paired door and one button/lever-controlled gate.
- One short vertical lift using supported native linear mechanisms, controlled by a button, with safe boarding,
  movement, landing and a way to operate/recover it from either relevant level.
- One wall-concealed secret door leading to a real secret room with a chest. Apply the correct secret-face semantics,
  event bindings, moving geometry and collision. Provide an appropriate subtle visual clue.
- Two actual pressure-plate traps. At least one launches an existing MM8 spell/projectile effect; define a deliberate
  cooldown or one-shot reset rule. Mark at least one trap detectably secret and verify low/high Perception behavior.
  PressurePlate alone does not imply detection or damage. Do not damage the party continuously every frame on contact.
- Four indoor chests in total, including the secret-room chest and a final guarded reward. Set indoor map treasure to
  **5**, choose appropriate templates and explicitly configure perception/disarm/trap/refill values for the test party.
- Purposefully sparse decorations and torches/light pools, with native radii and sector ambient. Inspect torch off/on;
  the Blender study sun must not stand in for actual dungeon lighting.

Populate the vault primarily with existing **MM8 Human Mercenary B/C** actors: Mercenaries and Mercenary Captains,
with a few weaker Soldiers of Fortune only where useful for pacing. No nagas. Use groups/door-controlled ambushes and
room layout to create resistance, with roughly 18–28 hostile actors across the complete map as an initial budget.
Tune the fight against the same test party; do not alter the shared species definition or rely on absurd actor density.
The final room may use a small captain-led group with an existing high-tier item as its reward. No invented named boss
or unique item is necessary for this test.

Test actor clearance through passages and open doors, stairs/lift interaction, targeting and LOS through portals,
trap spell origins/trajectories, secret discovery, every mechanism state and rewards after saving/reloading/revisiting.
The dungeon must be completable and escapable from either intended entry route; make shortcut/key/button dependencies
explicit so entering from the cave cannot bypass all meaningful content or trap the party behind an inaccessible control.

## Semantic markers, scripting and reproducible output

Use the playbook's named Blender objects and structured manifest properties. Explicitly distinguish default party start,
travel arrivals, teleport destinations if any, encounter spawns, fixed actors, scripted summons, loose items, chest
targets, decorations, lights, triggers, portals and moving mechanisms. Export only intended native content; no marker
proxy cubes or review objects in runtime collision.

Allocate stable event/house/chest/actor/door/sector IDs and preserve semantic-to-runtime correspondence. Every interaction
and lifecycle hook must have a generated registration and at least a placeholder Lua handler during scaffolding. Then
author and test the actual Lua logic. **No required placeholder may remain in the finished maps.** Preserve authored
handlers when regenerating geometry/events, using the documented supported assembly/overlay approach.

Use scoped instance registrations for reused content where needed. Preserve existing MM8 character text and service
behavior while avoiding shared-instance inventory, route or quest-state collisions. Write a provenance table mapping
each reused asset/NPC/topic/service/monster/item to its actual source identity. Do not edit generated legacy EVT/STR Lua.

All sectors, portals, faces/flags, mechanisms, terrain arrays, BModels, scene records, travel and event bindings must be
generated through a repeatable source build. No hand-edited final BLV/ODM repairs or manual finishing by the driver.
Reopen the written native files, compare them with the manifest, render the reimported geometry and load the maps in-game.

## Work sequence and review loop

1. Audit available Blender MCP and native build capabilities. Close necessary gaps in small tested fixtures, then reuse
   that path for the actual maps. Do not turn this into an unrelated engine/editor rewrite.
2. Write the brief, structured plans, marker/interaction inventories and scoped registration plan. Record major design
   assumptions, reference-derived proportions and planned test-party state.
3. Build/load greyboxes: native terrain with bridge/town pads and both entrances; indoor rooms/portals/elevations and
   essential movers. Establish walking, culling, collision and bidirectional travel before detail.
4. Apply MM8 textures and populate services, NPCs, encounters, rewards, decorations and lighting. Complete Lua.
5. Inspect actual saved images at multiple scales: outdoor full-map/tile/height views, town/bridge/castle close-ups,
   player-height approaches; indoor plan, opposite cutaways, floor sections and complete-ceiling player views.
6. Run focused automated checks and real runtime interaction/visual review. Log concrete failures with location/state,
   fix source/compiler, rebuild and repeat affected checks. Validate the compiled result, not only Blender source.
7. Finish only when both maps meet the brief and all relevant playbook review gates. Keep a progress/review file so a
   continuing `/goal` session can resume from the actual state instead of restarting or treating the plan as completion.

## Acceptance and final handoff

The completed goal must demonstrate:

- Two original native maps and the stated two-entry dungeon arrangement, integrated into a playable MM8 test context.
- A coherent non-flat grassland town with the required services, existing MM8 teachers/topics, population, river/bridge,
  connected roads, functional stables/travel and a newly modeled imposing castle exterior.
- Normal town activity safe from distant wild encounters, with the timed observation and route test recorded.
- Two separately guarded high-tier outdoor loot sites, real loose-item pickup, functioning obelisk and well/fountain.
- A Naga-Vault-like but original humanoid dungeon with meaningful elevation, doors, controlled lift, secret room, plates,
  traps, treasure, native lights and correct state persistence.
- Correct native export/round-trip, complete event coverage, stable IDs, no missing textures or unresolved registrations,
  no accidental dependencies on the original maps' quest state and no manual binary repairs.
- Focused tests for changed pure compiler logic and relevant headless/runtime scenarios for gameplay. Follow the repo's
  build/test commands. Check affected original MM8 paths, and shared MM6/MM7 behavior if shared code was changed.
- Visual review of native output and gameplay performance with real actors/decorations, compared fairly against useful
  references on the same settings. No unmeasured terrain-performance assertions or screenshots hiding unimplemented work.

Deliver editable `.blend` sources, structured authoring data, authored Lua, generated native package, stable ID and reuse
provenance reports, exact clean build/install/launch instructions, test-party setup, test results, and before/after review
images. Include a final concise checklist tied to the requirements above and precise remaining limitations, if any.
Do not mark the goal complete while a required feature is missing, a required handler is a placeholder, or the driver
would still need to finish the maps manually.

## Driver clarification — 2026-09-06

The driver returned and asked the agent to use its best judgement for difficulty, based on comparable dungeons'
monster density and room placement. The driver will review and tune final balance personally. Do not spend the
generation run exhaustively tuning combat difficulty or treat proof of a particular survival rate as a completion
gate. Keep the required encounter species, purposeful room/loot placement, active AI, ordinary test-party setup,
functional combat/LOS/clearance checks, safe town behavior and mechanism/escape-route validation. Record the
reference-based placement rationale and observed combat limitations without claiming final balance approval.

The driver also reconnected Blender MCP after finding it disconnected. A live scene inspection after reconnection
confirmed the current Greywatch authoring scene with 147 objects. The disconnect's cause is not established.

## Driver visual and interaction revision — 2026-09-07

Reinspect all 30 original MM6/MM7/MM8 reference maps for native decorations, with contextual screenshot
captures and highlighted placements. Extend the case studies with biome-specific palettes, city/countryside
placement, slope/flat-ground treatment, indoor props and torch/brazier lighting. Distinguish measured facts
from inferred design intent. Earlier geometry-only Blender previews omit decorations and cannot satisfy this review.
Include focused Harmondale, Alvar and Murmurwoods studies where needed for the named terrain/travel comparisons.

Revise Brackenford from this evidence: populate fitting foliage, rocks and props; introduce several coherent
house shapes/sizes and orientations informed by New Sorpigal, Ravenshore and Dagger Wound; give town terrain
useful slopes/terraces. Review Tularean Forest, Harmondale, Dagger Wound and Ravenshore heightfields, especially
Ravenshore–Shadowspire and Alvar–Murmurwoods elevated approaches. Use ridges, folds and screened routes to
create successive reveals and prevent seeing the whole map at once. Preserve the engine's current view distance.
Keep paths, entrances, actors, bridge and foundations usable after the terrain/population changes; rebuild and
repeat affected native movement, interaction and safety checks.

Review Greywatch's entrance-room wall texture continuity against the rest of the dungeon. Ordinary doors should
open by directly clicking the door; buttons are reserved for purposeful mechanisms or useful return controls.
A lift may share its button event with a pressure plate for automatic travel; prevent repeated contact from
oscillating the platform or trapping the party. Validate controls, movement and persisted mechanism state.

The driver reconnected Blender MCP on port 9876 following a PC reboot and authorizes continuing this goal
unattended. Preserve editable sources, update the playbook/case studies, inspect actual native output and finish
the existing functional and handoff gates alongside this visual revision.
