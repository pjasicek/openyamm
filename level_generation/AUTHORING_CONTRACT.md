# Blender-to-native-map contract

Start or reuse the authoring application using [Blender MCP startup](BLENDER_MCP_STARTUP.md). Normal GUI launch with
automatic MCP connection is verified here; manual driver setup is not a prerequisite for each generation run.

**Review policy:** use [visual calibration](VISUAL_CALIBRATION.md) and the [quick checklist](REVIEW_CHECKLIST.md).
The semantic requirements below still apply, but ordinary outdoor content uses one quick static face/event/target
check. References to runtime/state/transaction tests are diagnostic guidance for new behavior, observed defects or
explicitly requested testing; they are not a requirement to rerun scenarios for every reused service or texture edit.


This is a **proposed generation contract**, not a declaration that every field below is consumed by the current importer.
See [pipeline status](PIPELINE_STATUS.md) for implemented behavior and gaps. A generation implementation must satisfy this
contract or document an explicit, tested revision. Names identify objects; structured properties carry their semantics.

## Source ownership and identity

Use stable semantic IDs such as `myworld:dragon_cave/room/main` in a manifest. Allocate compact runtime sector, face,
door, chest, event, house and actor IDs separately and save the mapping. Do not encode meaning in a transient face index,
Blender selection order, or an automatically suffixed `.001` name. Duplicate semantic IDs, unresolved references and
colliding runtime IDs are build errors. Use declared global registry ranges; custom QBits start at 10000+ and still
require collision checks. Map-local variables/events are local to the map, not global quest identities.

Recommended object vocabulary:

| Blender name | Required semantics | Native result / support note |
| --- | --- | --- |
| `ROOM_main` | room ID, shell faces, ambient, explicit member objects | BLV occupied sector; existing prefix |
| `STATIC_records_desk` | static geometry, explicit owning room in `rooms[].source_nodes` | Native collision/render faces in that sector; no event or extra sector |
| `PORTAL_main_tunnel` | front/back room IDs, oriented planar opening | BLV portal face shared by two sectors |
| `MECH_vault_door` | mechanism ID, room, moving mesh, axis, length, speeds, initial state | Linear native door; verify allowed kind |
| `TRIGGER_vault_button` | interaction ID, event ID, room, trigger mode, hint, face flags | Event-bearing faces; current compiler only handles part of flags |
| `DECOR_wall_torch` | decoration key, position, facing, flags, optional event/light ownership | Native decoration; marker bridge required for empties |
| `LIGHT_torch_pool` | position, RGB, radius, room, enabled state | Native light; no Blender-only energy assumption |
| `SPAWN_guard_group` | encounter slot/type/index, position, radius, room, count policy | Native spawn record, distinct from fixed actor |
| `ACTOR_named_guard` | canonical monster ID, unique name, group, position, loot policy | Proposed actor marker, not current compiler prefix |
| `CHEST_side_reward` | stable chest slot, mesh/decor target, open event, template, trap policy | Proposed high-level marker expands to separate records/bindings |
| `ANCHOR_party_default` | role `party_default`, position, facing, room if indoor, clearance | Proposed marker lowered to the supported default party start |
| `ANCHOR_arrival_east` | role `travel_arrival`, incoming connection ID, position, facing, clearance | Proposed named destination for one incoming travel connection |
| `ANCHOR_teleport_alcove` | role `teleport_destination`, position, facing, clearance | Proposed local teleport destination, distinct from its activation trigger |
| `ANCHOR_ambush_rear` | role `scripted_spawn`, event owner, position, room/clearance | Proposed location referenced by an agent-authored summon handler |
| `ITEM_loose_reward` | canonical item/template, position, placement and persistence policy | Proposed loose-item marker; separate from a chest or actor drop |
| `TERRAIN_native` | exact grid, height samples, tile IDs, attributes, bank selection | Proposed native ODM terrain authoring object |
| `BMODEL_tavern` | stable model ID, static geometry, face semantics, material keys | Proposed outdoor export object; current metadata has BModel imports |
| `REVIEW_*` | camera/cutaway/labels | Authoring only; never export to map |

These are names on exported **nodes/objects**, not merely Blender collection names. Current source geometry import
operates on mesh-bearing nodes; Blender empties and Blender light objects are not automatically marker inputs. Implement
an explicit Blender manifest exporter that reads custom properties, or use supported mesh marker proxies consumed and
removed by the bridge. Do not leave invisible proxy cubes in collision. Name-based defaults must not silently fabricate
house IDs, chest contents, sector ownership, or event behavior.

## Party starts, arrivals and spawn markers

Every generated map must declare an explicit **default party start**, even when normal entry uses a travel-specific
destination. It provides a deliberate direct-load/test start. Also create a separate named arrival anchor for each
incoming connection that needs a different position or facing: outside entrance, lower passage, upper passage, return
from a dungeon, boat arrival, and so on. Several connections may intentionally share one anchor, but record that choice.
Do not scatter multiple indistinguishable `Party Start` entities and depend on load order to choose one.

There are several distinct marker purposes:

- **Default party start:** where a direct/default map entry places the party. The runtime recognizes the `party start`
  entity convention. Indoor scene metadata also supports `party_start_points`; its current default selection prefers
  `source_name: startpoint0`, otherwise the first entry. An authoring bridge must make the chosen default unambiguous.
- **Travel arrival:** where a particular incoming transition places the party. Bind the source exit/travel record to a
  named destination anchor, then resolve it to the runtime's destination coordinates/facing or supported arrival data.
  Extra Blender anchor names are not automatically runtime-selectable start points. Inspect both sides of the link.
- **Local teleport destination:** an arrival within the same map. Keep it separate from the clickable face/plate that
  activates teleportation; otherwise the party can arrive inside the source trigger and immediately retrigger it.
- **Encounter spawn (`SPAWN_*`):** a native population marker using spawn type/index, map-stat encounter slot/variant,
  placement radius and population/refill policy. It does not place the player or necessarily represent one monster.
- **Fixed actor (`ACTOR_*`):** one explicitly authored monster/NPC actor, including unique bosses, with canonical identity,
  placement, group/hostility and loot. Do not also create an encounter spawn for the same actor unintentionally.
- **Scripted spawn anchor:** a location consumed by an event's summon logic, with trigger, count and repeat policy.
  A coordinate marker alone must not create both an initial actor and a later summon.
- **Loose-item marker (`ITEM_*`):** an explicit placed object/reward or supported random-item template. It is separate
  from a chest's inventory and from an actor's guaranteed drop; validate the selected item-generation path independently.

Use Blender empties with direction arrows and distinct review colors for authoring these markers once the manifest
bridge exists. Colors are only a visual aid; role and IDs are structured data. Store game-space position, explicit facing
units/conversion, owning room where applicable, required floor/terrain contact and clearance. Add incoming connection or
event ownership for non-default anchors. Validate floor height, headroom, creature/party radius, hazard exposure and an
unobstructed departure path. Reject unresolved or unused required markers; never silently replace them with `(0,0,0)`.

Test every arrival separately, including facing and return travel. Test encounter population, fixed actors and scripted
spawns separately on fresh entry, revisit/refill and save/load. See
[IndoorSceneYml.cpp](../game/maps/IndoorSceneYml.cpp) for indoor start metadata and
[OutdoorGameView.cpp](../game/outdoor/OutdoorGameView.cpp) for outdoor party-start resolution. The proposed Blender names
above still require the exporter work listed in [pipeline status](PIPELINE_STATUS.md).

Store exact game-space coordinates and the authoring transform in the manifest. A useful authoring scale is 128 game
units per Blender unit, used by the study viewer; it is **not** a magic importer setting. Validate axis basis, handedness,
winding, glTF node transforms and unit scale with an asymmetric XYZ calibration fixture before full export. Apply the
transform once. Reject native integer range overflow. Do not rely on the compiler's current integer clamping.

## Indoor compiler obligations

1. Resolve stable room IDs to occupied sectors with sector 0 reserved empty. Validate all face and entity memberships;
   overlapping AABBs cannot decide stacked room ownership. Check containment against actual room geometry where needed.
2. Convert valid planar face geometry, normals/planes, winding, bounds, floor/wall/ceiling types, textures and texture
   coordinates. Split non-planar/oversized polygons deliberately while preserving semantic IDs and flags on every child.
   Preserve separate moving vertices. Resolve UVs using the actual source texture dimensions, not a blanket 256 divisor.
3. Validate each portal has two distinct existing room references, sits in an actual shared opening, has consistent
   orientation and reciprocal memberships, and creates the intended connectivity. Check transitions while walking and
   viewing through it; disconnected or accidentally visible sectors are failures.
4. Produce required sector face lists, portal lists, bounds, BSP/visibility data and automap outlines with deterministic
   ordering. If a particular derived structure is intentionally omitted, prove runtime behavior and performance before
   adopting that contract. An empty BSP or outline list in the current compiler is not proof that this requirement is met.
5. Produce mechanisms with valid affected face/vertex/sector IDs, travel direction/length/speeds, baseline coordinates,
   texture-motion policy and initial state. Define multi-part door groups explicitly. Do not weld an elevator into the
   floor. Compile control events separately and validate all endpoints and intermediate collision/party carrying.
   Source compiler metadata `door.source_pose` is `open` (the existing native baseline default) or `closed`.
   Set it explicitly for new authoring. `door.direction` points **from open toward closed**; native distance is zero
   when open and `move_length` when closed. For a platform authored at its lower, closed landing which opens upward,
   use `source_pose: closed`, `direction: [0,0,-1]`. The compiler derives open-position offsets and rejects endpoint
   overflow. `initial_state` chooses the runtime state independently of the authored pose. State-only assertions do
   not prove collision placement: walk against closed doors, through open doors, and ride lifts at both endpoints.
6. Emit native lights, decorations, spawns, scene actors/chests and complete face flags. Resolve logical face groups used
   by SetFacetBit separately from runtime face indices. Preserve group identity after triangulation/reordering.
7. Write the BLV with the authoritative writer, reopen it, and produce a source-to-runtime report. Check native limits
   in the selected writer/runtime version rather than inventing universal maximums.

## Outdoor compiler obligations

The terrain authoring mesh must retain grid identity despite object order. For each sample `(gx, gy)` in `[0,127]²`,
export `heightByte = round(gameZ / 32)` with a documented tie rule and validate `0 <= heightByte <= 255`. X/Y must match
the native lattice. For arbitrary sculpt input, resample using a specified vertical projection; reject ambiguous
multiple surfaces. Emit all 16384 height, tile and attribute bytes in row-major order. Quantization error and boundary
handling belong in the build report, as do the map's terrain-bank lookup and master-tile selection.

The current `.terrain.yml` schema uses `version: 1`, `map_file`, `height_map_hex`, `tile_map_hex`, and `attribute_map_hex`.
Each array is 16384 bytes / 32768 hex characters. Use the metadata writer/loader; do not introduce a competing hidden
terrain format in Blender. The higher-level authoring manifest may carry sculpt/mask provenance and semantic tile names,
but must lower deterministically to the native arrays and lookup rules.

Resolve terrain textures through the correct world table (`terrain_tile_data_3` for MM6, `_2` for MM7, default for MM8 in
the current imports). Native tile bytes below 90, banked values 90–233, and MM8 master-tile remapping have different
interpretations. Use [TerrainTileData.cpp](../game/maps/TerrainTileData.cpp) as the authority; reject invalid assignments.
Road-bank membership alone does not guarantee a road texture. Check actual resolved keys and flags for every used ID.

The planning manifest should additionally retain these authoring semantics (they are not new native binary fields):

- District type, reference membership, physical assembly ID, recurring architectural form and intended open-space role.
- Per building: local footprint, transform, door center/offset/outward normal, shared-block membership and
  `street_frontage` or `dedicated_lane`. Preserve the resolved road cells and the stated setback measurement method.
- Per palette: active bank lookup, verified corner/edge artwork, unsupported-material transition policy and diagonal
  pairing/junction rules. Arbitrary preview UV rotation must not substitute for a supported native tile ID.
- Per decoration group: biome palette, spatial role/extent, deterministic seed, requested/accepted count, clearance
  rules and final surface grounding. Keep actor/arrival/interaction exclusions tied to current placements.

Exporters may store these in planning JSON/YAML or Blender properties; do not claim that the engine reads them without
an implemented bridge. See [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md) for the corresponding review steps.

BModel conversion must produce native vertices/faces/UVs/flags, bounds and any required spatial lookup data through the
existing outdoor writer/build path. Use explicit contiguous runtime indices where current metadata requires them, while
retaining stable semantic IDs independently. Compile face events and decoration events along with scene records. Verify
terrain contact against the renderer's triangle split, including house thresholds and stair bases.

## Events and generated files

The manifest must list every interactive face/group, decoration, trigger, house, chest, mechanism control, well, fountain,
travel anchor, local teleport, scripted spawn, named-monster hook, lifecycle event and timer requested by the brief.
Record the event ID, semantic owner, activation mode, hint/context action, target records, state scope, and handler name.
One event can intentionally bind many faces; multiple unrelated objects must not share an event accidentally.

The build emits deterministic registration wrappers, metadata and **at least one Lua placeholder per distinct intended
event/hook**. Placeholders have a named purpose and implementation status. The agent fills the handlers; the geometry
generator does not invent dialogue, puzzle logic or quest conditions. A release build checks that all required handlers
are implemented and all referenced APIs/IDs resolve. An intentional no-op is explicit and justified, not a missing handler.

Preserve agent-written logic across rebuilds: keep authored handlers in a separate source file, and assemble that file
with generated registrations into the runtime map Lua. Do not assume filesystem `require`, `dofile`, `io`, or `os` exists
in the sandboxed Lua runtime. Alternatively use a verified existing overlay mechanism with explicit ownership. Never
regenerate over handwritten handlers or edit exported legacy EVT/STR Lua. Keep orphaned handlers visible for review after
an interaction is removed; do not silently discard authored work.

The current event API supports this shape (illustrative new-map code, not a generator implemented here):

```lua
-- Agent-owned source fragment; initially scaffolded, then completed by the agent.
local handlers = {}
handlers.openSideChest = function()
    -- TODO: implement manifest interaction side_reward; draft only.
end

-- Generated fragment, assembled after the authored definitions.
SetMapMetadata({
    onLoad = {},
    openedChestIds = { [201] = {0} },
})
RegisterEvent(201, "Side chest", handlers.openSideChest)
```

The scaffold inventory, not a text search for `TODO` alone, tracks completion. Add the appropriate metadata for hints,
context actions, lifecycle events, timers and monster hooks. Validate the exact API with
[event_support.lua](../assets_dev/engine/scripts/common/event_support.lua) and
[ScriptedEventProgram.cpp](../game/events/ScriptedEventProgram.cpp).

## Required outputs and reproducibility

Keep the brief, `.blend`, source meshes/material-key map, authoring manifest, stable ID allocation, agent-owned handlers,
and build configuration as source. Generated outputs are the native BLV/ODM, scene and map metadata, assembled Lua,
event inventory, registry contribution data, source-to-runtime correspondence, validation report and review images.
Package geography/events in the target world/mod and shared tables through the engine-owned content architecture.

A clean build from these sources must reproduce the same logical map and IDs. Rebuilding twice must preserve authored
Lua and not duplicate actors, lights, chests, registrations or mechanisms. Reimport the actual build, test it in the
runtime and compare it against the brief. All finishing changes belong in source or the authoritative compiler.

### Native indoor ambient setting

Set `rooms[].min_ambient_light_level` explicitly (integer 0–31). The compiler writes the native sector field; higher values mean darker ambient. Omitted fields retain the historical fully lit value 0 for old sources. MM8 Naga Vault and Ilsingore's Cave use 22, which is the Greywatch starting point. Author a matching `min_ambient_light_level` custom property on each `ROOM_` object. Do not confuse this inverse ambient level with a point light's brightness. Inspect complete-ceiling native views and controlled lights-on/off views; Blender inspection lighting cannot validate it.
