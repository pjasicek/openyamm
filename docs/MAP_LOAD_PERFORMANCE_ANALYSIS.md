# Map Load Performance Analysis

This document captures the current map startup and transition bottlenecks, based on
`OPENYAMM_MAP_LOAD_TIMING=1` logs from MM6/MM7/MM8 map loading work.

The goal is not to rewrite the loader. The goal is to keep the current engine architecture, identify avoidable work,
cache immutable data, parallelize CPU-only preparation where it is safe, and keep bgfx/runtime mutation on the owning
thread.

## Current Measurements

### Startup Into `out01.odm`

After the selected-map reuse fix, startup no longer asset-loads the same map twice during `startNewSession()`.

Current shape:

- Initial asset load for `out01.odm`: about `1345 ms`.
- `loadCurrentSessionMap()` reuses the already selected map: about `0.02 ms` for the map-load stage.
- Selected outdoor runtime:
  - `outdoor runtime initialized`: about `71 ms`.
  - `outdoor on-load events applied`: about `11 ms`.
  - `outdoor scene runtime bound`: about `239 ms` in one startup trace, but `0.28 ms` in a later transition trace.
  - `outdoor view initialized`: about `2186 ms`.
- Current-session runtime/view total after reuse: about `2507 ms`.

Confirmed improvement already made:

- The duplicate startup map asset load was avoidable and is now avoided by reusing `GameDataLoader::getSelectedMap()`
  when it matches `GameSession::currentMapFileName()`.

Remaining startup bottleneck:

- The first map still does a full asset build.
- Outdoor view initialization is currently the largest measured startup block.
- Global gameplay tables are not being reloaded per transition, but startup still loads all base gameplay data before
  entering the first map.

### Same-Continent Transition To `out02.odm`

Transition trace:

- `game data loader map load`: about `1817 ms`.
- Inside `MapAssetLoader::load`: about `1392 ms`.
- `renderer shutdown`: about `52 ms`.
- Selected outdoor runtime:
  - `outdoor runtime initialized`: about `87 ms`.
  - `outdoor on-load events applied`: about `13 ms`.
  - `outdoor scene runtime bound`: about `0.28 ms`.
  - `outdoor view initialized`: about `2163 ms`.
- Runtime/view total: about `2263 ms`.
- Final `current session map load complete` delta: about `286 ms`.
- Full transition total: about `4418 ms`.

This is too slow for a same-continent outdoor transition. The data says the biggest target is not the raw ODM parse. The
main targets are:

- outdoor view initialization, around `2160 ms`;
- CPU asset preparation inside `MapAssetLoader::load`, around `1390 ms`;
- post-asset-load `GameDataLoader` work, around `425 ms`;
- final progress/render callback work, around `286 ms`;
- renderer shutdown, around `52 ms`.

## Current Bottleneck Inventory

### MapAssetLoader CPU Work

For `out02.odm`, the expensive asset-load stages are:

- `outdoor scene yml applied`: about `209 ms`.
- `outdoor terrain textures built`: about `57 ms`.
- `outdoor bmodel textures built`: about `14 ms`.
- `outdoor actor collisions built`: about `64 ms`.
- `outdoor decoration billboards built`: about `350 ms`.
- `outdoor actor previews built`: about `453 ms`.
- `outdoor sprite objects built`: about `229 ms`.

These stages appear mostly CPU-side and should be candidates for caching or parallel preparation, provided image/frame
caches and data structures are made thread-safe or task-local.

### Post-Asset GameDataLoader Work

For `out02.odm`, `GameDataLoader::loadSelectedMap()` costs about `1817 ms`, while `MapAssetLoader::load()` reports
about `1392 ms`. The missing `425 ms` likely includes some combination of:

- continent settings application;
- event script path resolution;
- support/global/local Lua loading or compilation;
- appending script-referenced textures and billboards;
- hint/event metadata normalization;
- selected map repository binding.

This needs deeper timing before changing behavior.

### Outdoor View Initialization

`outdoor view initialized` is currently the largest measured block: about `2160-2186 ms`.

Likely contributors:

- bgfx texture creation and texture uploads;
- bgfx vertex/index buffer creation;
- shader/program creation or lookup;
- billboard renderer warmup;
- terrain/bmodel renderer resource initialization;
- UI/HUD resource binding;
- sprite/material resource transfer from CPU-side map assets into renderer-side handles.

This stage must be split into sub-stages before optimizing. bgfx calls generally need to stay on the render/main thread.

### Renderer Shutdown

`renderer shutdown` costs about `52 ms` on the `out02.odm` transition.

This is not the largest block, but it suggests we may be destroying map-local and app-global render resources together.
If true, map transitions should eventually separate:

- map-local render resources, which are destroyed/replaced on map transition;
- app-global resources, which should live for the app lifetime.

### Final Progress Callback

The trace shows about `286 ms` after runtime/view initialization before `current session map load complete`.

This probably includes the `progressCallback(100)` path and loading overlay rendering/presentation work. It should be
timed directly before optimizing.

### Audio Decode Spam

Startup logs still include repeated:

```text
GameAudioSystem: avformat_open_input failed: Invalid data found when processing input
```

This is probably not the main map-load bottleneck, but it is noisy and can add startup/transition overhead if bad audio
paths are repeatedly attempted. It should be fixed as authoritative data or resolution behavior, not hidden with a broad
fallback.

## Game Start Plan

### 1. Measure Startup Phases Separately

Add gated timing for:

- global table loading;
- merged table post-processing;
- icon/sprite/audio/video index construction;
- global Lua support loading and compilation;
- selected map asset load;
- selected map runtime creation;
- selected map renderer/view initialization.

Expected result:

- Startup should tell us how much time is global data boot versus first-map boot.

### 2. Decide Whether Startup Should Load A Map At All

Current startup loads the selected map as part of gameplay start. That is correct once a session is being entered.

For main-menu startup, we should avoid loading a gameplay map until the user starts or loads a game. If current app flow
still loads a selected gameplay map before it is needed, split the loader into:

- `loadBaseGameplayData()`;
- `loadSelectedMapForSession()`.

Do this only if the app still starts through a menu/lobby where no map is needed yet.

### 3. Cache Immutable Global Data

These should be parsed once per app/data-root version, not per map:

- texture frame data;
- sprite frame data;
- decoration data;
- monster definitions and sprite families;
- surface material definitions;
- terrain/material descriptors;
- global/support Lua source and compiled chunks if supported safely;
- icons/sprites/audio virtual file indexes.

The cache key must include the active asset roots or campaign/mod manifest version.

### 4. Keep App-Global Renderer Resources Alive

Do not recreate resources that are independent of the current map:

- shared shaders/programs;
- fonts;
- HUD textures;
- shared UI atlases;
- common icon textures;
- common sprite textures that are used across many maps.

This should be done only after deeper timing proves which resources are recreated in `outdoor view initialized`.

## Map Transition Plan

### 1. Add Deeper Transition Timing

Before optimizing, split timings inside these areas:

- `GameDataLoader::loadSelectedMap()` after `MapAssetLoader::load()`:
  - continent settings;
  - local script load;
  - global/support script handling;
  - Lua compilation;
  - script texture/billboard append;
  - repository map binding.
- `OutdoorGameView::initialize()`:
  - renderer resource creation;
  - terrain renderer initialization;
  - bmodel renderer initialization;
  - billboard renderer initialization;
  - actor/decor/object runtime binding;
  - UI/HUD binding;
  - first bgfx frame or loading overlay update.
- `progressCallback(100)` and loading overlay render/present path.

Add counters alongside timing:

- files read;
- bytes read;
- images decoded;
- bitmap cache hits/misses;
- texture uploads;
- bgfx textures created;
- bgfx buffers created;
- shader/program creations.

### 2. Remove Avoidable Transition Work

Targets:

- Do not reload global gameplay tables on map transition. This appears already true, but keep a regression test or
  debug counter.
- Do not reload/parse immutable common frame data separately for decorations, actors, and sprite objects.
- Do not compile unchanged global/support Lua per map if the runtime can safely reuse compiled chunks.
- Gate noisy per-map actor/object diagnostics behind an explicit debug option.
- Fix invalid audio open attempts so bad paths are not retried repeatedly.

### 3. Cache CPU-Side Decoded Assets

Introduce deterministic CPU-side caches for:

- decoded bitmaps by virtual path, palette, transparency mode, and scale tier;
- parsed sprite frame data;
- parsed texture frame data;
- parsed surface materials;
- prepared billboard frame descriptors;
- prepared terrain texture descriptors.

This should reduce:

- `outdoor decoration billboards built`;
- `outdoor actor previews built`;
- `outdoor sprite objects built`;
- `outdoor terrain textures built`;
- `outdoor bmodel textures built`.

### 4. Parallelize CPU-Only Preparation

Once caches are safe, the following can run in parallel after geometry and scene YAML are loaded:

- terrain texture CPU preparation;
- bmodel texture CPU preparation;
- decoration collision construction;
- actor collision construction;
- decoration billboard set construction;
- actor preview billboard set construction;
- sprite object billboard set construction.

Rules:

- Use a bounded worker pool.
- Keep bgfx calls on the render/main thread.
- Do not mutate shared caches without synchronization.
- Prefer task-local accumulators merged on the main thread.
- Preserve deterministic output order where render or tests depend on it.

### 5. Consider GPU Resource Caching

After CPU caching and timing, consider a renderer resource cache for:

- terrain textures shared across maps;
- bmodel textures shared across maps;
- sprite textures shared across maps;
- shader programs;
- static render states.

This must have explicit ownership and lifetime rules:

- app-global resources live until shutdown;
- map-local resources release on map unload;
- shared resources are reference-counted or retained by a central renderer cache.

Do not introduce a broad fallback lookup that hides asset ownership errors.

### 6. Add Background Prefetch For Known Next Maps

For same-continent transitions, the engine often knows likely next maps:

- outdoor boundary transitions from `outdoor_travels.txt`;
- house exits;
- scripted teleports;
- stable/boat destinations.

Prefetchable work:

- read geometry bytes;
- read scene YAML;
- parse static geometry;
- parse map delta;
- decode CPU-side images;
- build CPU-side billboard descriptors;
- build CPU-side collision structures.

Not prefetchable without careful renderer ownership:

- bgfx texture creation;
- bgfx buffer creation;
- runtime event execution;
- save-state mutation.

The target architecture is a `PreparedMapAsset` cache:

- immutable map asset data keyed by canonical map id and asset roots;
- mutable runtime state created fresh per session/map entry;
- cancellation for stale prefetches when the player goes elsewhere.

## Parallelization Candidates

Safe or likely safe after cache/thread review:

- file reads for independent map resources;
- YAML parsing for scene and support files;
- CPU image decode;
- CPU pixel conversion;
- billboard descriptor construction;
- collision structure construction;
- immutable lookup/index construction.

Not safe to parallelize directly:

- bgfx resource creation and destruction;
- SDL/audio mixer mutation;
- event runtime mutation;
- party/session/save-state mutation;
- UI runtime mutation;
- modifying `MapAssetInfo` from multiple threads without a merge step.

## Correctness Risks

Do not share mutable runtime data:

- map variables;
- qbits or quest state;
- sprite/decor state changed by events;
- actor HP/status/current position;
- event continuation state;
- house/dialog state;
- current map weather/time state if scripts can mutate it.

Asset cache keys must include:

- canonical virtual path;
- active campaign/world/mod roots;
- palette/transparency interpretation;
- generated asset version;
- source file timestamp or package hash in development mode.

Save/load must restore mutable state independently from cached immutable assets.

## Suggested Next Implementation Order

1. Add deeper gated timing inside `GameDataLoader::loadSelectedMap()` and `OutdoorGameView::initialize()`.
2. Add counters for decoded images, file reads, bgfx texture creations, and cache hits/misses.
3. Cache immutable parsed common tables used by outdoor map load.
4. Cache CPU-side decoded bitmaps and sprite frame data.
5. Parallelize CPU-only outdoor preparation with deterministic merge.
6. Split renderer resources into app-global and map-local lifetimes.
7. Add optional background prefetch for adjacent outdoor maps and known scripted destinations.

## Acceptance Targets

Initial targets after straightforward caching:

- Startup should not load the same selected map twice.
- Same-continent outdoor transition should avoid global table reloads.
- Same-continent outdoor transition should fall below `1500 ms` on the measured machine before background prefetch.
- With background prefetch and renderer resource reuse, same-continent outdoor transitions should aim below `1000 ms`.
- Timing and diagnostic logs must stay gated behind explicit debug/timing options.
- Runtime behavior must remain deterministic with and without prefetching.

These numbers are provisional. They should be adjusted after deeper timing identifies whether the `outdoor view
initialized` cost is mostly GPU upload, resource creation, first-frame synchronization, or CPU-side renderer setup.
