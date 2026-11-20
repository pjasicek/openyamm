# MM5 world ownership and additive content

The current [environment implementation goal](GOAL.md) requires a working MM5 world/map mount and local status-text
interaction placeholders. The NPC/dialogue/service integration requirements below describe the later gameplay phase;
they are not prerequisites for this environment-only milestone.

The eventual content identity should be **`mm5`**, mounted as a world through the existing flat engine/base architecture. Map-local geography, presentation and events belong under `assets_dev/worlds/mm5/`. Do not create a separate MM5 engine, a second campaign layer, or world-owned replacements for the merged global gameplay tables.

This layout project intentionally remains in `level_generation/projects/mm5_castleview_kalindra/`. Its semantic IDs already use `mm5:`. It has not mounted a half-built world or changed the normal new-game list.

## Verified current implementation

| Concern | Current evidence | Consequence |
| --- | --- | --- |
| World identity/start map | `assets_dev/worlds/mm8/world.yml`; `game/content/ContentManifest.cpp` | A named MM5 mounted world and map-local start are an existing architectural concept. |
| Dependencies, ID ranges and table contributions | `ContentManifest.cpp`, `WorldManifest` | Manifest syntax supports `dependencies`, `idRanges` and `tableContributions`; parsing a table contribution does not prove its consumer exists. |
| Keyed append composition | `game/content/ContentTableComposer.cpp` | Existing shared machinery can validate/compose supported keyed additions. Reuse it rather than introducing another owner of the same registries. |
| Monster data/descriptors | `GameDataLoader::loadMonsterTable` | Mounted-world append composition exists for these tables, with declared ranges. |
| Vendors/service venues | `GameDataLoader::loadHouseTable` | Explicit vendor/service-venue contributions are consumed for the active world. This is not generic append support for all legacy house rows. |
| Ordinary house definitions | `GameDataLoader::loadHouseTable` | `house_data.txt` is loaded through the existing table path. Adding a manifest entry called `house_data` alone does not append it. |
| Ordinary NPCs and dialogue | `GameDataLoader::loadNpcDialogTable` | NPCs, greetings, topic definitions and topic text load from engine/base tables. No generic world contribution loop is present here. |
| Teachers and travel | `loadMm9SkillTrainerTable` and adjacent loader functions / contribution table names | There are specific distribution consumers for trainers, routes, transitions and teacher schedules. Their MM9-specific paths are not evidence that an MM5 world automatically inherits an authoring API. |
| Brackenford content staging | `build_town_content.py`, `content_package.py` in the Brackenford project | The project builds additive rows and installs them into an isolated base. That demonstrates an explicit staging solution, not a universal mounted NPC overlay system. |

The root AGENTS instructions refer to `WORLD_CAMPAIGN_MOD_ARCHITECTURE.md`; that file was not present in this checkout when this review was made. These notes therefore use the supplied ownership rules and actual current loaders, not an invented schema from the missing document.

## Proposed package layout

This is an ownership sketch, **not a ready-to-mount manifest**:

```text
assets_dev/worlds/mm5/
  world.yml
  maps/mm5_sw.odm
  maps/mm5_sw.scene.yml
  maps/mm5_castleview_sewer.blv
  events/maps/mm5_sw.lua
  events/maps/mm5_castleview_sewer.lua
  icons/                   # world portraits, minimap, presentation
  textures/                # genuinely world-local additions
  contributions/           # explicit append inputs, after consumer support exists
    npcs.tsv
    npc_topics.tsv
    npc_topic_text.tsv
    houses.tsv
    quests.tsv
```

Existing MM6–8 assets should be resolved through the normal mounted/base ownership rules. A diagram's donor label is not itself an asset resolver alias. Resolve and record actual canonical texture, sprite, portrait and table identities at authoring time.

## Required before this becomes playable

1. Add shared, deterministic append handling for the specific NPC/dialogue/house/journal inputs needed by MM5, or explicitly generate an isolated composed base as Brackenford does for an early prototype. Keep a single authoritative merged registry in either case. Do not rely on a world-local file shadowing the whole NPC table.
2. Allocate collision-checked ranges for houses, NPCs, topics/text, map records and QBits; custom QBits begin at 10000 or above. The plan keeps numeric `runtimeId` values null deliberately. Brackenford's 12000-era example is not a reservation to reuse.
3. Lower semantic IDs such as `mm5:castleview/maps` and each `mm5:castleview/venue/...` separately into physical models, face events, house destinations and occupants. Multiple NPCs may share a venue; multiple venues may share one assembly. Neither relationship implies another physical house.
4. Write source-derived MM5 dialogue/quest handlers as world-local events. Keep global quest state in declared QBits; use local variables for local mechanisms. Never modify generated MM6–8 Lua to host MM5 logic.
5. Preserve distinct start, regional arrival, dungeon-return, sky-rope and tower-roof anchors. Bind both directions of travel. The wireframe's `days: null` is an unresolved design input, not zero-day travel.
6. Explicitly decide the MM5 skill conversions, bank behavior, time-based work, gemsmith crafting and growth/restoration states. This task located their places and contacts; it did not invent MM6–8 mechanics for them.

An ordinary new world manifest can name the world and starting map once those files exist. A speculative `sourceGame: mm5` value, arbitrary global numeric IDs or unconsumed contribution declarations should not be committed as if they already work.
