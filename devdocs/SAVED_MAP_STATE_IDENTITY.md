# Saved map states and rebuilt maps

A save keeps a state for every map the party visited: door and mechanism positions per door index, actors, chests,
items on the ground, face and decoration flags, map and decoration variables, timers, the indoor party's place. That
state is laid out against the map it was saved on. When a map is rebuilt (an MM9 reconversion, a fixed MM6-MM8 map,
any update that ships a changed map), the old state no longer fits: on 2026-11-06 a save made before Anskram Keep was
reconverted (12826 to 13152 vertices) put its door states on the wrong doors, and the party walked through a shut gate
into a shaft. Since save version 162 such a state is reset, deterministically.

Code: `game/maps/MapLayoutIdentity.{h,cpp}` (identity and verdict), `GameSession::discardMapState`,
`resetSavedMapStateOfAnotherLayout` in `game/app/GameApplication.cpp`. Tests: `tests/MapLayoutIdentityTests.cpp`
(identity, verdict, save round trip), `tests/MapStateResetRuntimeTests.cpp` (stamping, reset keeps the party) and
`tests/scenarios/release/rebuilt_map_save.yml`, whose `save_game: {rebuilt_maps: [...]}` rewrites the saved identities
in place of changing a map file: loading then takes the same path as after a real rebuild.

## Layout identity

`MapAssetLoader::load` computes `MapAssetInfo::layoutIdentity`, a 64-bit FNV-1a hash of what a saved state indexes:

- indoor: vertex positions; each face's vertex list, attributes, event cogs, rooms, facet type and portal flag; the
  sector and outline counts; decorations (id, position, events, variables); spawns; scene movers and destructibles;
- outdoor: each model's vertex positions and faces (vertex list, attributes, event cogs, polygon type); decorations;
  spawns; mechanisms and destructibles;
- both: from the map's initial state (scene or companion), the doors (slot, id, direction, travel, vertex, face and
  sector lists), the chests (count and types), and the counts of placed actors and floor items.

Left out on purpose, so that changing them keeps saves: texture names, lights and baked lighting, outdoor terrain
heights and tiles (no saved state indexes them), event scripts (regenerated often; a script that reuses map variables
differently must ship with a map change or an explicit migration), and actor or item stats. The hash takes values
byte by byte, least significant first, so it is the same on every platform, and it is never 0. `LayoutIdentityAlgorithm`
is part of it: changing the hashed fields means bumping it, which resets every map state once.

The identity of the map whose runtime is up is stamped on its state each time the state is captured
(`GameSession::setCurrentMapLayoutIdentity`, `captureIndoorRuntimeState`, `captureOutdoorRuntimeState`), and saved
with it (`IndoorSceneRuntime::Snapshot::mapLayoutIdentity`, `OutdoorWorldRuntime::Snapshot::mapLayoutIdentity`).

## Reset rule

When a map is entered, by loading a save or by travelling, its saved state is judged before the map is built
(`judgeSavedMapState`):

- same identity: kept, exactly as before;
- another identity: the whole map state is dropped and the map starts from its initial state, as on a first visit.
  One log line (`Saved map state: map 7d05.blv changed since the save; its state was reset`) and a six-second status
  notice (`<map> has changed since this save: it starts afresh`).

A map is checked when it is entered because only then is its layout loaded; until then its old state is only data in
the save, and a save written meanwhile carries it with its old identity, so the reset still happens at the next entry.

Party-level state is never touched: members, inventory, gold, experience, QBits, journal and autonotes, hirelings and
followers, named global variables, the other maps' states.

The party inside a reset map (the loaded save was made there) starts at the map's start point, facing as the map
says; its saved position and camera are dropped. A saved position on what is still a floor is not kept: in a rebuilt
map a floor check cannot tell the right room from the far side of a moved gate or a sealed passage, and the start point
is the one place the new build is authored to receive the party. A map reached by travel is entered at the move's
destination as always.

## Saves without identities

States in saves before version 160 read identity 0, unknown. They are kept for the MM6, MM7 and MM8 worlds, whose
maps are the original games' converted maps and did not change, so those saves load exactly as before. For every
other world (MM9, Hesper, later ones) they are reset at entry: those maps were rebuilt since such saves were made, and
pre-release saves need not survive (user decision, 2026-11-06). Either way the next save records the current identity.
