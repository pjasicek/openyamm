# MMerge Table Audit Inventory

Fresh audit date: 2026-05-13.

This inventory tracks the MMerge table sources that should feed the flat OpenYAMM base tables. It is intentionally
separate from older migration notes because the previous checklist covered `Data/mmmerge.T.lod/` and `Data/Tables/`
but did not fully account for top-level MMerge overlay tables such as `Data/03 LocalizeTables.txt`.

## Summary

- Primary MMerge table sources audited: 93 files.
- `reference/mmerge_data_forus/Data/mmmerge.T.lod/`: 41 files.
- `reference/mmerge_data_forus/Data/Tables/`: 52 files.
- Top-level overlay/UI table sources additionally audited: 3 files.
- Primary source tables with an active OpenYAMM representation: 93 / 93.
- Primary source tables with runtime consumers still pending or partial: 7.
- Top-level overlay/UI sources fully integrated: 0 / 3.
- Top-level overlay/UI sources partially integrated: 1 / 3.
- Top-level overlay/UI sources missing as a source-table import: 2 / 3.

## Status Legend

- `Integrated direct`: Active table is copied in the same logical table shape.
- `Integrated converted`: Active table was imported into an OpenYAMM schema or generated asset shape.
- `Integrated sidecar`: Source was split into multiple active tables.
- `Loaded only`: Typed loader exists, but runtime does not meaningfully consume it yet.
- `Partial runtime`: Runtime consumes only some source fields.
- `Reference only`: Table is kept for traceability, but another MMerge table is authoritative at runtime.
- `Replaced`: Source table was intentionally superseded by another MMerge-compatible source.
- `Partial overlay`: Some rows/fields from an overlay source are applied, but the full overlay is not.
- `Missing`: No active source-table import or equivalent runtime data exists.

## Current Gaps

These are the real missing or partial areas from the fresh audit.

| Source | Status | Current OpenYAMM state | Missing or partial work |
| --- | --- | --- | --- |
| `Data/03 LocalizeTables.txt` | Partial overlay | `NPCDataTxt.Joins`, `Houses 45/48`, `NPCTopic 1765`, and `GlobalTxt 737` are applied to active engine tables. Many target rows were already present through other imports. | Import the overlay as a first-class patch source or apply all remaining fields explicitly. Known unapplied or divergent entries include `TransTxt 20/22`, `MapStats 205 EaxEnvironments`, and `GlobalTxt 634`. |
| `Data/patch.UI.txt` | Missing | No active table or typed loader. | Decide whether this belongs in the UI layout/config system or should stay reference-only. |
| `Data/UI.txt` | Missing | Present only in `reference/mmerge_datapatch/Data/UI.txt`; no active table or typed loader. | Decide whether this belongs in the UI layout/config system or should stay reference-only. |
| `Tables/Additional UI.txt` | Integrated direct, Loaded only | `assets_dev/engine/data_tables/additional_ui.txt`, `MergedAdditionalUiTable`. | Runtime presentation consumers pending for remaining UI knobs. |
| `Tables/Complex item pictures offsets.txt` | Integrated direct, Loaded only | `assets_dev/engine/data_tables/complex_item_picture_offsets.txt`, typed loader. | Apply portrait-specific equipment offsets if needed. |
| `Tables/Continent settings.txt` | Integrated direct, Partial runtime | `assets_dev/engine/data_tables/continent_settings.txt`, typed loader. | Remaining fields include saturation/softness and guard/shop reputation flags; specific water/loading pictures are intentionally inactive for now. |
| `Tables/HW water textures.txt` | Integrated direct, Loaded only | `assets_dev/engine/data_tables/hw_water_textures.txt`, typed loader. | Renderer/world presentation consumer pending. |
| `Tables/Overlay.txt` | Integrated direct, Loaded only | `assets_dev/engine/data_tables/overlay.txt`, typed loader. | Runtime/exporter use pending if overlay registry behavior becomes needed. |
| `Tables/Transport Index.txt` | Integrated direct, Reference only | `assets_dev/engine/data_tables/transport_index.txt`, typed loader. | No runtime gap while `House rules.txt` plus `Transport Locations.txt` remains authoritative. |

## Top-Level Overlay And UI Tables

| Source | Active target | Status | Notes |
| --- | --- | --- | --- |
| `Data/03 LocalizeTables.txt` | Several active tables | Partial overlay | MMerge script-time patch table. `NPCDataTxt.Joins`, `Houses 45/48`, `NPCTopic 1765`, and `GlobalTxt 737` have been applied; the file still needs a proper whole-table integration decision. |
| `Data/patch.UI.txt` | - | Missing | Exists in `reference/mmmerge/Data/` and `reference/mmerge_datapatch/Data/`. |
| `Data/UI.txt` | - | Missing | Exists in `reference/mmerge_datapatch/Data/` only. |

## `Data/mmmerge.T.lod`

| Source | Active target | Status | Notes |
| --- | --- | --- | --- |
| `mmmerge.T.lod/2DEvents.txt` | `house_data.txt`, `house_animations.txt` | Integrated sidecar + partial overlay | House/event metadata and animation sidecar. `Data/03 LocalizeTables.txt` `Houses 45/48` overrides are applied. |
| `mmmerge.T.lod/Autonote.txt` | `english/autonote.txt` | Integrated direct | Active autonote registry. |
| `mmmerge.T.lod/Awards.txt` | `english/awards.txt` | Integrated direct | Active awards registry. |
| `mmmerge.T.lod/Credits.txt` | `english/credits.txt` | Integrated direct | Shared text. |
| `mmmerge.T.lod/DECLIST.TXT` | `decoration_data.txt` | Integrated converted | Exported from/generated against merged decoration data. |
| `mmmerge.T.lod/Global.TXT` | `english/Global.txt` | Integrated direct + partial overlay | `GlobalTxt 737` is applied. Some top-level `03 LocalizeTables.txt` overrides still need audit/application. |
| `mmmerge.T.lod/Hostile.txt` | `hostile.txt` | Integrated direct | Active relation table. |
| `mmmerge.T.lod/IFT.TXT` | `icon_frame_data.txt` | Integrated converted | Exported from generated MMerge icon frame data. |
| `mmmerge.T.lod/INTRO.TXT` | `english/INTRO.TXT` | Integrated direct | Shared text. |
| `mmmerge.T.lod/ITEMS.txt` | `items.txt` | Integrated direct | Active merged item table. |
| `mmmerge.T.lod/Launcher.txt` | `english/launcher.txt` | Integrated direct | Shared launcher text. |
| `mmmerge.T.lod/MERCHANT.TXT` | `english/merchant.txt` | Integrated direct | Merchant text. |
| `mmmerge.T.lod/MM7history.txt` | `english/mm7_history.txt` | Integrated direct | Runtime uses continent-local history text. |
| `mmmerge.T.lod/MONLIST.TXT` | `monster_descriptors.txt` | Integrated converted | Exported from generated merged monster descriptors. |
| `mmmerge.T.lod/MONSTERS.txt` | `monster_data.txt` | Integrated direct | Active merged monster table. |
| `mmmerge.T.lod/MapStats.txt` | `map_stats.txt` | Integrated direct | Active merged map registry; some overlay fields still need audit/application. |
| `mmmerge.T.lod/NPCData.txt` | `npc.txt` | Integrated direct + partial overlay | Active merged NPC registry; `NPCDataTxt.Joins` overlay is applied. |
| `mmmerge.T.lod/NPCGreet.txt` | `npc_greet.txt` | Integrated direct | Active NPC greetings. |
| `mmmerge.T.lod/NPCGroup.txt` | `english/npc_group.txt` | Integrated direct | Active NPC group text. |
| `mmmerge.T.lod/NPCNews.txt` | `npc_news.txt` | Integrated direct | Active NPC news. |
| `mmmerge.T.lod/NPCText.txt` | `npc_topic_text.txt` | Integrated direct | Active NPC topic text; many overlay rows are already present here. |
| `mmmerge.T.lod/NPCTopic.txt` | `npc_topic.txt` | Integrated direct + partial overlay | Active NPC topics; `NPCTopic 1765` is applied from the overlay. |
| `mmmerge.T.lod/OBJLIST.TXT` | `object_list.txt` | Integrated converted | Active object schema. |
| `mmmerge.T.lod/POTION.TXT` | `english/potion.txt` | Integrated direct | Runtime potion matrix/text source. |
| `mmmerge.T.lod/POTNOTES.TXT` | `english/potnotes.txt` | Integrated direct | Runtime potion autonote matrix. |
| `mmmerge.T.lod/Placemon.txt` | `english/place_mon.txt` | Integrated direct | Placed-monster display text. |
| `mmmerge.T.lod/Quests.txt` | `english/quests.txt` | Integrated direct | Active merged QBit registry. |
| `mmmerge.T.lod/SFT.TXT` | `rendering/sprite_frame_data_common.yml`, `rendering/sprite_frames/` | Integrated converted | Exported from generated MMerge sprite frame data. |
| `mmmerge.T.lod/SPCITEMS.TXT` | `special_item_enchants.txt`, `SPCITEMS.TXT` | Integrated direct | Active special enchant registry. |
| `mmmerge.T.lod/STDITEMS.TXT` | `standard_item_enchants.txt` | Integrated direct | Active standard enchant registry. |
| `mmmerge.T.lod/Skilldes.txt` | `english/skill_des.txt` | Integrated direct | Skill descriptions. |
| `mmmerge.T.lod/Spells.txt` | `english/spells.txt` | Integrated direct | Spell text. |
| `mmmerge.T.lod/Trans.txt` | `english/trans.txt` | Integrated direct | Transition text; top-level overlay text still needs audit/application. |
| `mmmerge.T.lod/class.txt` | `english/class.txt` | Integrated direct | Class text. |
| `mmmerge.T.lod/history.txt` | `english/history.txt` | Integrated direct | Runtime uses this for Jadame/MM8 history. |
| `mmmerge.T.lod/pcnames.txt` | `english/pc_names.txt` | Integrated direct | PC name pools. |
| `mmmerge.T.lod/rnditems.txt` | `random_items.txt` | Integrated direct | Random item table. |
| `mmmerge.T.lod/roster.txt` | `roster.txt` | Integrated direct | Active merged roster registry. |
| `mmmerge.T.lod/scroll.txt` | `english/scroll.txt` | Integrated direct | Scroll text. |
| `mmmerge.T.lod/sounds.txt` | `sounds.txt` | Integrated direct | Active merged sound catalog, with expanded table rows merged in. |
| `mmmerge.T.lod/stats.txt` | `english/stats.txt` | Integrated direct | Character inspect stat text. |

## `Data/Tables`

| Source | Active target | Status | Notes |
| --- | --- | --- | --- |
| `Tables/Additional UI.txt` | `additional_ui.txt` | Integrated direct, Loaded only | Runtime consumers pending for remaining UI metadata. |
| `Tables/Bolster - formulas.txt` | `bolster_formulas.txt` | Integrated direct | Runtime uses built-in equivalents of default formula rows. |
| `Tables/Bolster - maps.txt` | `bolster_maps.txt` | Integrated direct | Runtime consumed for continent ids, map bolster metadata, rarity caps, and outdoor sky lookup. |
| `Tables/Bolster - monsters.txt` | `bolster_monsters.txt` | Integrated direct | Runtime consumed for generated NPC filtering and feature-gated monster bolster data. |
| `Tables/Character doll types.txt` | `doll_types.txt` | Integrated converted | Converted to active paperdoll-type schema. |
| `Tables/Character portraits.txt` | `character_data.txt` | Integrated converted | Converted to active portrait/paperdoll schema. |
| `Tables/Character selection.txt` | `character_selection.yml` | Integrated converted | Runtime partially consumed by new-game character creation. |
| `Tables/Character voices.txt` | `character_voices.txt` | Integrated direct | Runtime speech playback consumed. |
| `Tables/Chest.txt` | `chest_data.txt` | Integrated converted | Active table adds OpenYAMM UI/grid metadata. |
| `Tables/Class Extra.txt` | `class_extra.txt` | Integrated direct | Runtime consumed for class kind and promotion-step metadata. |
| `Tables/Class HP SP.txt` | `class_multipliers.txt` | Integrated converted | Converted HP/SP and mana stat codes. |
| `Tables/Class Skills.txt` | `class_skills.txt` | Integrated direct | Active class skill caps. |
| `Tables/Class Starting Skills.txt` | `class_starting_skills.txt` | Integrated converted | Transposed to active class-row schema. |
| `Tables/Class Starting Stats.txt` | `class_starting_stats.txt` | Integrated direct | Runtime consumed by new-game stat editing. |
| `Tables/Complex item pictures offsets.txt` | `complex_item_picture_offsets.txt` | Integrated direct, Loaded only | One source override row; runtime consumer pending. |
| `Tables/Complex item pictures.txt` | `complex_item_pictures.txt` | Integrated direct | Runtime consumed for equipped doll item placement. |
| `Tables/Continent settings.txt` | `continent_settings.txt` | Integrated direct, Partial runtime | Runtime consumes travel/death/weather/NPC gates; remaining presentation/reputation flags pending. |
| `Tables/DecList.txt` | `decoration_data.txt` | Integrated converted | Exported from generated merged decoration data. |
| `Tables/HW water textures.txt` | `hw_water_textures.txt` | Integrated direct, Loaded only | Renderer/world presentation consumer pending. |
| `Tables/House Movies.txt` | `house_movies.txt`, `house_animations.txt` | Integrated sidecar | Runtime consumed for house movie and sound resolution. |
| `Tables/House exits.txt` | `house_exits.txt` | Integrated direct | Runtime consumed for direct house exits. |
| `Tables/House rules.txt` | `house_rules.txt` | Integrated direct | Runtime consumed for shops, spellbook shops, training, Arcomage, and travel routes. |
| `Tables/IFT.txt` | `icon_frame_data.txt` | Integrated converted | Exported from generated MMerge icon frame data. |
| `Tables/MonList.txt` | `monster_descriptors.txt` | Integrated converted | Exported from generated merged monster descriptors. |
| `Tables/MonPortraits.txt` | `monster_portraits.txt` | Integrated direct | Runtime consumed for generated/generic NPC portrait resolution. |
| `Tables/Monster Kinds.txt` | `monster_data.txt` kinds column | Integrated converted | Source flags promoted into authoritative monster rows. |
| `Tables/NPC BTB.txt` | `npc_btb.txt` | Integrated direct | Runtime consumed for beg/bribe/threat gates. |
| `Tables/NPC names.txt` | `npc_names.txt` | Integrated direct | Runtime consumed for generated NPC names. |
| `Tables/NPC professions.txt` | `npc_professions.txt` | Integrated direct | Runtime consumed for hire costs, join/recruit flags, actions, descriptions, and news. |
| `Tables/News topics - area.txt` | `news_topics_area.txt` | Integrated direct | Runtime consumed for generic actor/NPC area news. |
| `Tables/News topics - continent.txt` | `news_topics_continent.txt` | Integrated direct | Runtime consumed for continent fallback news. |
| `Tables/News topics - profession.txt` | `news_topics_profession.txt` | Integrated direct | Runtime consumed for profession/day news. |
| `Tables/ObjList.txt` | `object_list.txt` | Integrated converted | Active object schema. |
| `Tables/Outdoor travels.txt` | `outdoor_travels.txt` | Integrated direct | Runtime consumed for outdoor map-edge travel. |
| `Tables/Overlay.txt` | `overlay.txt` | Integrated direct, Loaded only | Runtime/exporter use pending if needed. |
| `Tables/PFT.txt` | `portrait_frame_data.txt` | Integrated converted | Exported from generated MMerge portrait frame data. |
| `Tables/Potion settings.txt` | `potion_settings.txt` | Integrated direct | Runtime consumed for potion item ids and mastery requirements. |
| `Tables/Race Skills.txt` | `race_skills.yml` | Integrated converted | Runtime consumed through effective race/class skill caps. |
| `Tables/Reagent settings.txt` | `reagent_settings.txt` | Integrated direct | Runtime consumed for reagent item ids and produced potions. |
| `Tables/SFT.txt` | `rendering/sprite_frame_data_common.yml`, `rendering/sprite_frames/` | Integrated converted | Exported from generated MMerge sprite frame data. |
| `Tables/Sounds.txt` | `sounds.txt` | Integrated converted | Expanded MMerge sound ids merged into active catalog. |
| `Tables/Spells2.txt` | `spells.txt` | Integrated converted | Mana/recovery/damage data applied to active spell table. |
| `Tables/TFT.txt` | `texture_frame_data.txt` | Integrated converted | Exported from generated MMerge texture frame data. |
| `Tables/Teacher autonotes.txt` | `teacher_autonotes.txt` | Integrated direct | Runtime consumed for teacher map notes. |
| `Tables/Teacher topics.txt` | `teacher_topics.txt` | Integrated direct | Runtime consumed for mastery teacher detection/evaluation. |
| `Tables/Tile.txt` | `terrain_tile_data.txt` | Integrated converted | Exported from generated MMerge tile data. |
| `Tables/Tile2.txt` | `terrain_tile_data_2.txt` | Integrated converted | Exported from generated MMerge tile data. |
| `Tables/Tile3.txt` | `terrain_tile_data_3.txt` | Integrated converted | Exported from generated MMerge tile data. |
| `Tables/Town Portal.txt` | `town_portal_switch.txt` | Replaced | Intentionally superseded by MMerge-compatible `TownPortalSwitch.txt`. |
| `Tables/TownPortalSwitch.txt` | `town_portal_switch.txt` | Integrated direct | Runtime consumed for continent-aware Town Portal UI/destinations. |
| `Tables/Transport Index.txt` | `transport_index.txt` | Integrated direct, Reference only | Active travel uses `House rules.txt` plus `Transport Locations.txt`. |
| `Tables/Transport Locations.txt` | `transport_locations.txt` | Integrated direct | Runtime consumed for stable/boat destinations. |

## Reference Source Variants

The audited `Tables/` files exist in all three local MMerge references:

- `reference/mmerge_data_forus/Data/Tables/`
- `reference/mmmerge/Data/Tables/`
- `reference/mmerge_datapatch/Data/Tables/`

The datapatch `Tables/` files currently match `mmerge_data_forus`. Top-level overlay/UI files are not present in
`mmerge_data_forus`, so they must be tracked separately from the main table directory audit.
