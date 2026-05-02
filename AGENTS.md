# AI Agent Instructions

These rules apply to all AI-generated contributions in this repository.

## Core Rules

- Generate new code. Never copy code from OpenEnroth or mm_mapview2.
- Use `reference/OpenEnroth-git/` and mm_mapview2 only as behavioral/structural references.
- Use GrayFace's decompiled scripts in `reference/mmext-scripts/Decompiled_Scripts/` as semi-authoritative event
  behavior references for MM6/MM7/MM8. Prefer the per-world `txt/` folders for readable control flow when checking or
  repairing exported EVT Lua. Do not copy script code into OpenYAMM; use it to understand intent and validate behavior.
- Prefer simple, maintainable solutions over clever abstractions.
- Do not add adapter/forwarding layers that only hide duplicated ownership.
- Keep temporary diagnostics and noisy logs out of final changes.
- Do not add hack fixes or broad compatibility fallbacks that mask stale/broken state. Fix the authoritative data,
  event script, schema, or system behavior instead; if old saves/assets need migration, make that an explicit migration.

## Workflow

- Use the local OpenEnroth checkout at `reference/OpenEnroth-git/`; do not search OpenEnroth on the web when local
  reference is available.
- Preferred build command: `cmake --build build --target openyamm -j25`.
- Prefer doctest/unit coverage for pure logic.
- Use focused headless coverage for runtime/map behavior when unit tests are not enough.
- If a task explicitly names planning documents, follow those documents for that task only; do not treat stale plans as
  active global instructions.

## Coding Style

- C++20.
- Maximum line length: 120 characters.
- Braces on new lines.
- Naming: classes `CamelCase`, methods/variables `camelCase`, members `m_variable`.
- Pointer names: `pPointer`; member pointers: `m_pPointer`.
- Prefer const correctness and minimal headers.
- Prefer explicit types over `auto`; use `auto` only when it clearly improves readability or is effectively required.
- Do not use `[[nodiscard]]`.
- Prefer unqualified integer and size types: `uint32_t`, `int16_t`, `size_t`.
- Avoid raw `new`/`delete`, global state, unnecessary macros, and unnecessary `static_cast`.
- Always use `override` where applicable.

Example:

```cpp
if (condition)
{
    doSomething();
}
```

## Architecture

Subsystem layers:

- `engine/`
- `game/`
- `editor/`
- `tools/`

Treat gameplay systems as shared by default. Fixes for HUD, UI screens, input/keybind semantics, inventory, items,
dialogue, shops, chests, rest, spell casting, projectiles, particles, combat rules, monster AI, party state, qbits,
journal, save/load, audio reactions, and gameplay FX should normally live in shared gameplay code.

Indoor/outdoor-specific code should normally be limited to BLV/ODM world representation:

- map loading
- geometry rendering
- visibility/culling
- picking and LOS
- collision, floor resolution, and movement integration
- projectile collision against world geometry
- event-face/decor/mechanism lookup
- world-specific decal placement

If a bug appears only indoors or only outdoors, first check whether the shared system is called with different data or
missing world hooks. Prefer fixing the shared path or the world hook over adding divergent logic to `IndoorGameView` or
`OutdoorGameView`.

### Flat Base, World, And Mod Content

- The long-term content architecture is documented in `WORLD_CAMPAIGN_MOD_ARCHITECTURE.md`.
- OpenYAMM is the engine. Worlds such as MM8, MM7, MM6, or future custom settings should be mounted content packages,
  not separate engines or hardcoded runtime modes.
- Use a flat MMerge-like base: `assets_dev/engine/` is the global/base content layer and `assets_dev/worlds/*` contains
  world-local maps, events, and presentation assets. MM6/MM7/MM8 worlds must not own active TXT/BIN gameplay tables;
  import or migrate their references to the merged MMerge-owned tables under `assets_dev/engine/`. Do not add a
  separate campaign package layer for now.
- The flat base decides which worlds are mounted, which worlds can be chosen at new game start, and how cross-world
  travel, metaquests, difficulty profiles, and global overrides work.
- Keep shared content in the engine/base scope when the party can carry it or when it defines base mechanics:
  items, skills, spells, classes, races, portraits, paperdolls, formulas, base state, and the merged QBit journal
  registry (`quests.txt`). The default MMerge global tables belong under `assets_dev/engine/`.
- Keep geography and map-local content world-scoped: maps, map events, map/local event vars, loading screens, monster
  art, and world presentation. In the MMerge-style flat base, merged journal/autonote/history/NPC dialogue, house,
  travel, monster, decoration, object, and other TXT/BIN registries live globally under `assets_dev/engine/`.
- Treat QBits as global party/save state. Worlds and mods may own declared QBit ranges, with custom content starting at
  `10000+`, but those bits merge into the shared registry and must not silently collide.
- Use canonical namespaced ids for world-specific data. Treat MM6/MM7/MM8 raw ids as import aliases, not global truth.
- Implement world support incrementally around existing runtime systems through package mounting, world manifests, mod
  manifests, declared id ranges, and active-world context. Do not rewrite the game engine for this.
- For MM6/MMerge import work, use the "MM6 Import Reference From MMerge" section in
  `WORLD_CAMPAIGN_MOD_ARCHITECTURE.md`. Treat `reference/mmerge_data_forus/` and `reference/mmmerge/` as data and
  behavior references only; import into normal world/mod architecture instead of reproducing MMerge's memory-hook
  runtime shape.
- Track MMerge TXT table integration in `MMERGE_TXT_TABLE_INTEGRATION_INVENTORY.md` and update it whenever a table is
  promoted, converted, skipped, or given a loader.
- Track MMerge icon ownership in `MMERGE_ICON_OWNERSHIP.md`. Keep merge-owned/global icons in
  `assets_dev/engine/icons`, original-world NPC portraits in `assets_dev/worlds/mm*/icons`, and preserve the documented
  lowercase/0644 import rules.

## Assets And Runtime

- Keep original asset formats whenever practical: TXT gameplay data, WAV audio, MP3/FLAC music, OGV video, ZIP packages.
- Development assets live under `assets_dev/`; runtime packages live under `assets/*.zip`.
- Renderer uses bgfx. Keep rendering simple: static meshes, sprites/billboards, UI, basic lighting, fog.
- Audio uses SDL3 with an engine mixer layer for effects, music, volume groups, and fades.
- Video uses FFmpeg OGV decoding with audio/video sync and looping/cutscene support.
- Editor code must reuse runtime engine systems and must not duplicate gameplay logic.
