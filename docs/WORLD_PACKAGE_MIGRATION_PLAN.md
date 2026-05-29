# World Package Migration Plan

This checklist tracks the incremental transition from the current single `assets_dev/Data` layout to the flat
engine/world/mod package architecture.

Reference documents:

- `WORLD_CAMPAIGN_MOD_ARCHITECTURE.md`
- `ASSETS_DEV_ENGINE_MM8_SPLIT_INVENTORY.md`

## Phase 1: Mounting And Compatibility

Goal: make the runtime understand the future package roots while the current asset layout continues to work.

- [x] Keep legacy `assets_dev/` mounted as a fallback.
- [x] Mount optional `assets_dev/engine/` when present.
- [x] Mount optional `assets_dev/worlds/mm8/` when present.
- [x] Resolve legacy virtual paths such as `Data/ui/...` through package aliases before falling back.
- [x] Keep old `Data/...`, `Videos/...`, `Music/...`, and `_legacy/...` lookups working.
- [x] Add minimal manifest loading for active world, with MM8/default fallbacks.
- [x] Expose active world id to game startup.

Acceptance checks:

- Existing game/editor asset lookups still resolve from the current layout.
- If a file exists in a package alias and the legacy layout, the package file wins.
- If a file exists only in the legacy layout, it still resolves.
- Enumerating a legacy directory returns the union of package and legacy entries.

## Phase 2: Explicit World Identity

Goal: introduce world identity without changing gameplay behavior.

- [x] Add default MM8 world identity and canonical map id helpers.
- [x] Treat existing MM8 maps as `world.mm8.map.<legacy-name>`.
- [x] Keep `MapRegistry::findByFileName` compatibility for old callers.
- [x] Add canonical map id to `MapStatsEntry`.
- [x] Add canonical map id to selected map metadata.
- [x] Update runtime map snapshot keys to support canonical ids with legacy filename fallback.
- [ ] Keep existing save files loadable through an explicit MM8 migration path.

Acceptance checks:

- New saves include base/world/map identity.
- Existing MM8 map transitions still work.
- Old saves migrate into `base=mm8` or `base=default`, `world=mm8`.

## Phase 3: MM8 Package Restructure

Goal: move obvious MM8/world content and obvious engine-global/runtime-support content.

- [x] Move UI layouts to `assets_dev/engine/ui/`.
- [x] Move shared fonts to `assets_dev/engine/fonts/`.
- [x] Move English localization tables to the flat `assets_dev/engine/data_tables/english/` base.
- [x] Move shared mechanics tables to `assets_dev/engine/data_tables/`.
- [x] Move MM8 maps to `assets_dev/worlds/mm8/maps/`.
- [x] Move MM8 map scripts to `assets_dev/worlds/mm8/events/maps/`.
- [x] Promote active TXT/BIN gameplay tables to `assets_dev/engine/data_tables/`.
- [x] Move MM8 videos to `assets_dev/worlds/mm8/videos/`.
- [x] Move MM8 music to `assets_dev/worlds/mm8/music/`.
- [x] Move `_legacy/` to `assets_dev/worlds/mm8/_legacy/`.

Acceptance checks:

- The game runs with no dependency on moved legacy locations.
- The editor can enumerate and open MM8 maps through the package layout.
- Packaging can still produce the runtime asset zip.

## Phase 4: Mixed Asset Split

Goal: split large mixed folders by authoritative references rather than filename guesses.

- [x] Build a reference graph for `Data/icons`.
- [x] Build a reference graph for `Data/sprites`.
- [x] Build a reference graph for `Data/bitmaps`.
- [x] Build a reference graph for `Data/EnglishD`.
- [x] Move globally referenced MMerge assets to `assets_dev/engine/`.
- [x] Move MM8-local referenced assets to `assets_dev/worlds/mm8/`.
- [x] Leave aliases only where intentional.

Notes:

- `Data/sprites` is split by sprite-frame ownership: non-monster common sprite frames live in
  `engine/sprites`,
  monster family billboard art lives in `worlds/mm8/sprites`.
- `Data/bitmaps` is MM8-local by default; only the shared water/lava material animation frames currently live in
  `engine/textures`.
- `Data/icons` keeps player/item/UI/spell presentation in `engine/icons`; MM8 NPC, house, map, and
  terrain-local icons live in `worlds/mm8/icons`.
- `Data/EnglishD` is split: shared audio lives in `engine/audio`, MM8 monster audio lives in
  `worlds/mm8/audio`.
- `sounds.txt` is flat MMerge/base data in `engine/data_tables/sounds.txt`; audio files may still live in
  `engine/audio` or `worlds/<id>/audio`.

Acceptance checks:

- No missing assets during MM8 gameplay smoke tests.
- Inventory/item/spell/portrait assets resolve globally.
- MM8 monster/map/event assets resolve from the MM8 world package.

## Phase 5: Mods And More Worlds

Goal: make MM6/MM7/custom worlds mountable beside MM8.

- [x] Add world manifest parsing.
- [ ] Add new game world selection.
- [ ] Add world-scoped quest/event/map runtime state.
- [ ] Add native cross-world travel service.
- [ ] Import one MM6 or MM7 vertical-slice world package.
- [ ] Add flat mod manifest support with declared id ranges.
- [ ] Add global metaquest/difficulty hooks.

Acceptance checks:

- A new game can start in MM8 through the manifest path.
- The runtime can discover MM8 plus one additional test world.
- Cross-world travel preserves party/global state and switches world-local state.
