# `assets_dev` Engine/MM8 Split Inventory

This is an inventory of the current `assets_dev/` tree and the intended ownership split for the future world/mod
architecture.

The original goal was to classify what should eventually become shared engine/global content and what should become the
MM8 world package. The split is now incremental; entries marked as already moved should be treated as authoritative at
their new package path.

Update: active TXT/BIN gameplay tables are now flat MMerge/base data. Do not put gameplay TXT tables under
`assets_dev/worlds/*/data_tables`; MM6/MM7/MM8 world packages own maps, events, and presentation assets, while merged
table registries live under `assets_dev/engine/data_tables`.

Target roots:

```text
assets_dev/engine/      Shared engine/global content used by all worlds.
assets_dev/worlds/mm8/  MM8/Jadame world content.
```

If an intermediate migration uses `assets_dev/mm8/`, treat that as the same bucket as `assets_dev/worlds/mm8/`.

Current total: 20,859 files, about 1.1 GB.

## Summary By Current Root

| Current path | Files | Size | Target | Notes |
|---|---:|---:|---|---|
| `Anims/mightdod/` | 91 | 35 MB | `worlds/mm8/videos/legacy/` | Moved. MM8 house/transition-style OGVs. |
| `Music/` | 14 | 84 MB | `worlds/mm8/music/` | Moved. MM8 soundtrack tracks. |
| `Videos/Cutscenes/` | 13 | part of 50 MB | `worlds/mm8/videos/cutscenes/` | Moved. MM8 story/company/endgame videos. |
| `Videos/Houses/` | 78 | part of 50 MB | `worlds/mm8/videos/houses/` | Moved. MM8 house videos. |
| `Videos/Transitions/` | 51 | part of 50 MB | `worlds/mm8/videos/transitions/` | Moved. MM8 transition videos. |
| `Data/games/` | 125 | 64 MB | `worlds/mm8/maps/` | Moved. MM8 BLV/ODM and exported scene/geometry YAML. |
| `Data/scripts/maps/` | 61 | part of 1.5 MB | `worlds/mm8/events/maps/` | Moved. MM8 map event scripts. |
| `Data/scripts/Global.lua` | 1 | part of 1.5 MB | `worlds/mm8/events/` | Moved. MM8 global event script unless split later. |
| `Data/scripts/common/` | 1 | part of 1.5 MB | `engine/scripts/common/` | Moved. Shared Lua/event helper. |
| `Data/ui/` | 24 | 240 KB | `engine/ui/` | Moved to `assets_dev/engine/ui/`. Shared OpenYAMM/MM8-style UI layouts. |
| `Data/rendering/surface_materials.yml` | 1 | part of 1.8 MB | `engine/rendering/` | Moved. Shared material semantics. |
| `Data/rendering/sprite_frame_data_common.yml` | 1 | 1.8 MB group | `engine/rendering/` | Moved. Shared defaults. |
| `Data/rendering/sprite_frames/monsters/` | 199 | part of 1.8 MB | `worlds/mm8/rendering/` | Moved. MM8 monster frames. |
| `Data/data_tables/` | 67 | 1.6 MB | `engine/data_tables/` | Merged MMerge/base tables and OpenYAMM support tables live only in `engine/data_tables`. |
| `Data/EnglishT/` | 22 | 756 KB | split | Fonts and shared text moved; unused `.str` files removed. |
| `Data/EnglishD/` | 3,250 | 50 MB | split | Shared sounds moved to `engine/audio`; MM8 monster sounds moved to `worlds/mm8/audio`. |
| `Data/icons/` | 4,156 | 83 MB | split | Moved: fonts to `engine/fonts/icons`; 3,301 files to `engine/icons`; 841 files to `worlds/mm8/icons`. |
| `Data/bitmaps/` | 1,821 | 44 MB | split | Moved: 14 shared material frames to `engine/textures`; 1,807 MM8 texture/palette files to `worlds/mm8/textures`. |
| `Data/sprites/` | 10,688 | 655 MB | split | Moved: 1,115 common object/decoration/spell sprites to `engine/sprites`; 9,573 monster sprites to `worlds/mm8/sprites`. |
| `_legacy/` | 195 | 13 MB | `worlds/mm8/_legacy/` | Moved. MM8 source/import artifacts. |

## Data Tables

Keep table formats. Split by ownership and mount scope, not by changing the format.

### Moved To `engine/data_tables/`

These define shared mechanics, shared character systems, shared items, shared spells, or common UI/runtime registries:

```text
Data/data_tables/arcomage_cards.txt
Data/data_tables/arcomage_rules.txt
Data/data_tables/character_data.txt
Data/data_tables/class_multipliers.txt
Data/data_tables/class_skills.txt
Data/data_tables/class_starting_skills.txt
Data/data_tables/doll_types.txt
Data/data_tables/face_animations.txt
Data/data_tables/hostile.txt
Data/data_tables/icon_frame_data.txt
Data/data_tables/items.txt
Data/data_tables/object_list.txt
Data/data_tables/portrait_frame_data.txt
Data/data_tables/portrait_fx_events.txt
Data/data_tables/random_items.txt
Data/data_tables/sounds.txt
Data/data_tables/special_item_enchants.txt
Data/data_tables/character_speech_events.txt
Data/data_tables/spell_fx.txt
Data/data_tables/spells.txt
Data/data_tables/standard_item_enchants.txt
```

Notes:

- `items.txt` should become the engine-global item repository.
- `spells.txt` and `spell_fx.txt` should be shared mechanics data.
- `object_list.txt` is mechanically shared, but world packages may add object rows through namespaced overlays.
- `sounds.txt` is a flat merged sound catalog under `engine/data_tables`; audio files may still be engine- or
  world-scoped presentation assets.

### Engine/Base Data Tables

These were previously considered MM8-world-local, but are now part of the flat MMerge/base table authority:

```text
Data/data_tables/chest_data.txt
Data/data_tables/decoration_data.txt
Data/data_tables/house_animations.txt
Data/data_tables/house_data.txt
Data/data_tables/house_rules.txt
Data/data_tables/map_navigation.txt
Data/data_tables/map_stats.txt
Data/data_tables/mon_list.txt
Data/data_tables/monster_data.txt
Data/data_tables/monster_death_drops.txt
Data/data_tables/monster_descriptors.txt
Data/data_tables/monster_projectiles.txt
Data/data_tables/monster_relation_data.txt
Data/data_tables/npc.txt
Data/data_tables/npc_greet.txt
Data/data_tables/npc_news.txt
Data/data_tables/npc_topic.txt
Data/data_tables/npc_topic_text.txt
Data/data_tables/roster.txt
Data/data_tables/terrain_tile_data.txt
Data/data_tables/terrain_tile_data_2.txt
Data/data_tables/terrain_tile_data_3.txt
Data/data_tables/texture_frame_data.txt
Data/data_tables/town_portal_switch.txt
Data/data_tables/transport_locations.txt
```

Notes:

- The table files above should exist under `assets_dev/engine/data_tables` if they are active.
- `map_stats.txt` is a direct MMerge import. The other support tables keep OpenYAMM schemas until matching MMerge
  sources are converted.
- Terrain/tile/texture frame data is currently merged MMerge/base data and lives under `engine/data_tables`.
- `town_portal_switch.txt` is the active MMerge Town Portal source; stables and boats consume
  `house_rules.txt` and `transport_locations.txt` directly. `roster.txt` is a flat base support table for now.

### Moved To `engine/data_tables/english/`

These are shared UI/mechanics strings or common localized descriptions:

```text
Data/data_tables/english/class.txt
Data/data_tables/english/credits.txt
Data/data_tables/english/launcher.txt
Data/data_tables/english/merchant.txt
Data/data_tables/english/pc_names.txt
Data/data_tables/english/potion.txt
Data/data_tables/english/scroll.txt
Data/data_tables/english/skill_des.txt
Data/data_tables/english/spells.txt
Data/data_tables/english/stats.txt
```

### Engine/Base English Registries

These are merged MMerge/base quest, history, place, NPC, or story registries:

```text
Data/data_tables/english/autonote.txt
Data/data_tables/english/awards.txt
Data/data_tables/english/history.txt
Data/data_tables/english/npc_group.txt
Data/data_tables/english/place_mon.txt
Data/data_tables/english/quest.txt
Data/data_tables/english/quests.txt
Data/data_tables/english/trans.txt
```

### Remove Or Ignore

```text
Data/data_tables/.~lock.map_stats.txt#
```

This is an editor lock/temp file and should not be part of either package.

## Maps And Event Scripts

Current MM8 maps have moved to `worlds/mm8/maps/`:

```text
Data/games/*.blv
Data/games/*.odm
Data/games/*.scene.yml
Data/games/*.geometry.yml
Data/games/*.map.yml
Data/games/*.terrain.yml
```

Current map set:

- 47 BLV indoor files.
- 14 ODM outdoor files.
- 64 YAML scene/geometry/map/terrain files.

MM8 map scripts have moved to `worlds/mm8/events/maps/`:

```text
Data/scripts/maps/*.lua
```

`Data/scripts/Global.lua` has moved to `worlds/mm8/events/Global.lua` until it is split. It is currently MM8
world/mod behavior, not engine behavior.

`Data/scripts/common/event_support.lua` has moved to `engine/scripts/common/event_support.lua`.

## UI And Fonts

UI layout YAML has moved to `engine/ui/`:

```text
Data/ui/gameplay/*.yml
Data/ui/menu/main_menu.yml
```

Fonts and the font palette have moved under `engine/fonts/`:

```text
Data/EnglishT/*.fnt -> engine/fonts/english_text/
Data/EnglishT/fontpal.pcx -> engine/fonts/english_text/
Data/icons/*.FNT -> engine/fonts/icons/
```

The package keeps separate `english_text` and `icons` font subdirectories for now. Most files are identical duplicates
with different legacy casing, but `LEGAL.FNT` differs between the two source roots, so a flat deduplicated directory
would change at least one legacy path. Deduplication should be explicit later, not a side effect of this move.

## English Text Files

Shared English text has moved to `engine/data_tables/english/`:

```text
Data/EnglishT/Global.txt
Data/EnglishT/INTRO.TXT
```

Removed unused legacy map string files:

```text
Data/EnglishT/d42.str
Data/EnglishT/d43.str
Data/EnglishT/d44.str
Data/EnglishT/d45.str
Data/EnglishT/d46.str
```

The runtime/editor no longer read these `.str` files; preserving a package alias for them would make dead content look
active. If a future importer needs them, recover them from the original game data or Git history as import-only source.

`Global.txt` may need a later semantic split. It contains shared UI/mechanics strings and MM8-specific text in the
legacy format. Keep it global during the first migration so existing lookups keep working, then split by referenced id.

## Audio

`Data/EnglishD/` has been split.

Reasoning:

- `engine/data_tables/sounds.txt` contains the merged sound id catalog.
- Audio files can remain in `engine/audio` or `worlds/<id>/audio`; the TXT catalog itself is not world-local.

Specific migrated inventory:

- 2,856 WAV files in `assets_dev/engine/audio/`.
- 394 MM8 monster and house/event WAV files in `assets_dev/worlds/mm8/audio/`.

## Icons

`Data/icons/` has been split.

Move to `engine/icons/`:

- item icons;
- spell icons;
- UI chrome, menu controls, book/page graphics, inventory paperdoll UI;
- fonts;
- shared character portraits and face/portrait assets;
- shared condition/status icons;
- shared cursor and interaction icons.

Move to `worlds/mm8/icons/`:

- MM8 house/chest/local UI art that only exists because of MM8 content;
- MM8 quest/local story icons;
- any icon referenced only by MM8-local tables, houses, maps, or events.

Specific current inventory:

- 3,301 icon/image files in `assets_dev/engine/icons/`.
- 841 MM8-local icon/image files in `assets_dev/worlds/mm8/icons/`.
- 14 icon font files in `assets_dev/engine/fonts/icons/`.

Classification used:

- player, item, UI, spell, condition, paperdoll, and shared menu presentation assets moved to `engine/icons`;
- NPC portrait, house, terrain/map, and MM8-local presentation assets moved to `worlds/mm8/icons`;
- ambiguous leftovers defaulted to `engine/icons` unless they were clearly MM8-local by table references or filename
  family.

## Bitmaps

`Data/bitmaps/` has been split. It mostly moved to the MM8 world because it primarily contains MM8 terrain, dungeon,
outdoor, sky, palette, and texture assets.

Move to `worlds/mm8/textures/` by default:

- terrain textures;
- indoor wall/floor/ceiling textures;
- map presentation textures;
- MM8 local effect textures;
- ACT palette files tied to those textures.

Move to `engine/effects/` only when the asset is referenced by global spell/effect systems rather than by MM8 maps.

Specific migrated inventory:

- 14 shared water/lava material animation frames in `assets_dev/engine/textures/`.
- 1,807 MM8 texture, sky, terrain, dungeon, effect, and ACT palette files in `assets_dev/worlds/mm8/textures/`.

Classification used:

- frames explicitly referenced by `engine/rendering/surface_materials.yml` moved to `engine/textures`;
- all other current bitmap assets moved to `worlds/mm8/textures`;
- later shared spell/effect bitmap assets can be promoted to `engine/effects` when their runtime owner is made explicit.

## Sprites

`Data/sprites/` has been split.

Move to `worlds/mm8/sprites/`:

- MM8 monster sprites.

Move to `engine/sprites/` only for genuinely global mechanics:

- common projectile sprites;
- common spell effect sprites;
- shared cursor/marker/interaction sprites, if any;
- shared object sprites only if `object_list.txt` is global and the object is not MM8-specific.

Specific migrated inventory:

- 1,115 common object, decoration, projectile, and spell/effect sprites in `assets_dev/engine/sprites/`.
- 9,573 MM8 monster billboard sprites in `assets_dev/worlds/mm8/sprites/`.

Classification used:

- sprite files whose names start with an MM-style monster family id, such as `m412...`, moved to `worlds/mm8/sprites`;
- all other current sprite files moved to `engine/sprites` because they are referenced by the shared common sprite frame
  table and shared object/spell systems;
- future world packages can still override common sprite names from their own `sprites/` root.

## Rendering Metadata

Rendering metadata has moved to `engine/rendering/`:

```text
Data/rendering/surface_materials.yml
Data/rendering/sprite_frame_data_common.yml
```

MM8 monster frame metadata has moved to `worlds/mm8/rendering/sprite_frames/monsters/`:

```text
Data/rendering/sprite_frames/monsters/*.yml
```

The monster frame metadata is world-local because monsters are world-local.

## Videos

Current videos have moved to `worlds/mm8/videos/`:

```text
Videos/Cutscenes/*.ogv
Videos/Houses/*.ogv
Videos/Transitions/*.ogv
Anims/mightdod/*.ogv
```

Current inventory:

- 13 cutscenes.
- 78 house videos.
- 51 transition videos.
- 91 legacy `Anims/mightdod` videos.

Company logos and original intro/legal videos are still MM8 package content, not engine content. A future original game
or a mod can provide its own equivalents.

## Music

Current music has moved to `worlds/mm8/music/`:

```text
Music/*.mp3
```

Current inventory:

- 14 MP3 files.

Music is world content, not engine content.

## Legacy Source Artifacts

Move the entire `_legacy/` tree to `worlds/mm8/_legacy/`:

```text
_legacy/SFT.TXT
_legacy/bin_tables/*.bin
_legacy/events/*.EVT
_legacy/events/*.STR
_legacy/map_delta/*.dlv
_legacy/map_delta/*.ddm
_legacy/tile_tables/*.bin
```

Current inventory:

- 10 legacy bin tables.
- 62 EVT files.
- 58 STR files.
- 47 DLV files.
- 14 DDM files.
- 3 tile bin tables.
- 1 `SFT.TXT`.

These are MM8 import/source artifacts. They should not live in engine-global content.

## Recommended Migration Order

1. Add mount support for `assets_dev/engine/` and `assets_dev/worlds/mm8/` while keeping the current layout as a
   compatibility mount.
2. Move `Data/ui/`, shared fonts, and shared mechanics tables to `engine/`.
3. Move `Data/games/`, `Data/scripts/maps/`, MM8 map strings, and `_legacy/` to `worlds/mm8/`.
4. Promote active TXT/BIN gameplay tables to the flat MMerge/base layer under `engine/data_tables/`.
5. Move videos and music to `worlds/mm8/`.
6. Split `Data/icons/`, `Data/EnglishD/`, `Data/bitmaps/`, and `Data/sprites/` using reference graphs from tables,
   event scripts, and map YAML. Done.
7. Remove the compatibility mount once all runtime lookups use package-aware paths or active-world aliases.

## Open Questions

- `Global.txt` needs semantic splitting after the first migration.
- `object_list.txt` may remain global or become a global table with world overlays.
- Some bitmap spell/effect assets currently live in `worlds/mm8/textures` by default. Promote them to `engine/effects`
  only when a shared runtime owner is explicit.
- Future world sound tables may add local event/environment audio. Keep duplicate sound ids invalid within a single
  scope, but allow worlds to reuse numeric ids already used by engine/global audio or by another world.
