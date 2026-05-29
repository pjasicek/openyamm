# MMerge TXT Table Integration Inventory

This document tracks every `*.txt` / `*.TXT` table file currently present under
`reference/mmerge_data_forus/Data/`. There are no top-level TXT files directly in `Data/`; the MMerge table files are
inside `Data/mmmerge.T.lod/` and `Data/Tables/`.

Use this as the authoritative checklist when replacing OpenYAMM's subset tables with the flat MMerge base tables.
The intended end state is flat and MMerge-owned: MM6/MM7/MM8 worlds do not own active TXT/BIN gameplay tables.
If a current world asset still stores pre-MMerge numeric IDs, migrate that asset to the merged engine table IDs instead
of adding a world-first table fallback.

Status legend:

- `Integrated direct`: byte-for-byte copied from the MMerge reference into `assets_dev/engine/data_tables`.
- `Integrated direct + typed base loader`: byte-for-byte copied into `assets_dev/engine/data_tables` and parsed into
  typed base data. These tables are validated at load time, and runtime consumers may still be pending where wiring
  them would change current MM8 behavior unless noted.
- `Integrated converted`: imported into an existing OpenYAMM table shape; not byte-identical to the source.
- `Pending`: not yet integrated as authoritative runtime data.
- `Needs loader`: table has no current OpenYAMM loader/runtime behavior.
- `Use generated BIN`: prefer generated MMerge `reference/mmerge_data_forus/DataFiles/*.bin` when exporting this
  registry, not the older baseline BIN embedded in `mmmerge.T.lod`.
- `Legacy world-local`: still present as import/reference data only; should not be an active table source.

## Summary

- Total MMerge TXT/TXT table files tracked: 93.
- `Data/mmmerge.T.lod`: 41 files.
- `Data/Tables`: 52 files.
- Imported into active engine tables or converted engine schemas: 92 files.
- Direct source-table imports: 67 files.
- Converted/internal-schema imports: 25 files.
- Not imported as an active table yet: 0 files.
- Intentionally replaced instead of imported: 1 file, `Tables/Town Portal.txt`, because runtime now uses
  `Tables/TownPortalSwitch.txt` as the MMerge-compatible continent-aware source.
- Current cleanup state: `assets_dev/worlds/*/data_tables` has been removed. Active TXT gameplay/support
  tables are loaded from `assets_dev/engine/data_tables` only.

## Current Remaining Work

The missing-table scan was refreshed against `reference/mmerge_data_forus/Data/mmmerge.T.lod`,
`reference/mmerge_data_forus/Data/Tables`, `assets_dev/engine/data_tables`, and the current `GameDataLoader` typed base
loaders.

### Not Yet Imported

| Source | Recommended action | Notes |
| --- | --- | --- |
| - | - | All tracked MMerge TXT tables have an active engine import, converted target, or intentional replacement decision. |

### Imported And Typed, Runtime Consumer Still Pending Or Partial

| Source | Current state | Runtime work left |
| --- | --- | --- |
| `Tables/Additional UI.txt` | Loaded into `MergedAdditionalUiTable`. | Wire hostile indicator / selection-ring presentation settings. |
| `Tables/Bolster - formulas.txt` | Loaded into `MergedBolsterFormulaTable`; runtime uses built-in equivalents of the default MMerge formulas, including the special `76` HP row and bolstered monster hit checks against player AC. | Add a formula-expression evaluator only if runtime-editable/source-divergent formula rows become necessary. |
| `Tables/Bolster - monsters.txt` | Runtime consumed for generated outdoor NPC filtering, bounty-hunt exclusions, and feature-gated monster bolster behavior. New ranged attacks and generated monster spells are wired into shared actor combat. | Remaining metadata/special-action work, if needed: presentation-only classification differences and active summon/replicate execution beyond the currently exposed eligibility fields. |
| `Tables/Character selection.txt` | Converted to `character_selection.yml` and partially runtime consumed. | New Game still assumes Jadame/MM8, but character creation now uses MMerge continent/race/portrait rules, separate valid-class cycling, and MMerge-style add/remove/select controls for up to five starting characters. Future work: add the continent-selection screen. |
| `Tables/Complex item pictures offsets.txt` | Loaded into `MergedComplexItemPictureOffsetTable`; not consumed. | Apply portrait-specific equipment draw offsets if/when needed. Current source has one override row. |
| `Tables/Continent settings.txt` | Partially consumed for continent death movie, death-map coordinates, outdoor sky/weather context, profession-news gating, NPC follower gating, and continent NPC reputation behavior. | Remaining settings: saturation/softness and guard/shop reputation flags. Specific water and loading pictures are intentionally not active runtime targets for now. |
| `Tables/HW water textures.txt` | Loaded into `MergedHardwareWaterTextureTable`. | Use as the authoritative software-water to hardware-water animation mapping in renderer/world presentation. |
| `Tables/Transport Index.txt` | Loaded into `MergedTransportIndexTable`; reference-only for active runtime. | No current runtime need if `House rules.txt` plus `Transport Locations.txt` remains authoritative for routes. Revisit only if MMerge route-slot behavior diverges. |

## `Data/mmmerge.T.lod`

| Source | Status | OpenYAMM target / next step | Notes |
| --- | --- | --- | --- |
| `mmmerge.T.lod/2DEvents.txt` | Integrated direct + sidecar + localization overlay | `assets_dev/engine/data_tables/house_data.txt`, `assets_dev/engine/data_tables/house_animations.txt` | Merged house/event metadata. Runtime derives missing service skill offers from MMerge house type where the old OpenYAMM support column no longer exists. `Data/03 LocalizeTables.txt` house name/picture overrides for `Houses 45/48` are applied. |
| `mmmerge.T.lod/Autonote.txt` | Integrated direct | `assets_dev/engine/data_tables/english/autonote.txt` | Flat MMerge base registry. |
| `mmmerge.T.lod/Awards.txt` | Integrated direct | `assets_dev/engine/data_tables/english/awards.txt` | Flat MMerge base registry. |
| `mmmerge.T.lod/Credits.txt` | Integrated direct | `assets_dev/engine/data_tables/english/credits.txt` | Shared text. |
| `mmmerge.T.lod/DECLIST.TXT` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/decoration_data.txt` | Exported from generated `DataFiles/ddeclist.bin`. Runtime/editor use this as authoritative; existing MM8 scene decoration IDs were remapped to this merged table. |
| `mmmerge.T.lod/Global.TXT` | Integrated direct + localization overlay | `assets_dev/engine/data_tables/english/Global.txt` | Shared global text. `Data/03 LocalizeTables.txt` `GlobalTxt 737` is applied; remaining `GlobalTxt` overrides need per-use audit before application. |
| `mmmerge.T.lod/Hostile.txt` | Integrated direct | `assets_dev/engine/data_tables/hostile.txt` | Merged relation source for the flat base. Any remaining world-local relation use is transitional and should be removed by migrating dependent IDs. |
| `mmmerge.T.lod/IFT.TXT` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/icon_frame_data.txt` | Exported from generated `DataFiles/dift.bin`. |
| `mmmerge.T.lod/INTRO.TXT` | Integrated direct | `assets_dev/engine/data_tables/english/INTRO.TXT` | Shared text. |
| `mmmerge.T.lod/ITEMS.txt` | Integrated direct | `assets_dev/engine/data_tables/items.txt` | Authoritative merged item table. |
| `mmmerge.T.lod/Launcher.txt` | Integrated direct | `assets_dev/engine/data_tables/english/launcher.txt` | Shared launcher text. |
| `mmmerge.T.lod/MERCHANT.TXT` | Integrated direct | `assets_dev/engine/data_tables/english/merchant.txt` | Shared merchant text. |
| `mmmerge.T.lod/MM7history.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/english/mm7_history.txt` | Authoritative MM7/Antagarich history book. Runtime keeps MMerge-compatible continent-local `History(n)` semantics without swapping global tables: MM8/Jadame uses `history.txt`, MM7/Antagarich uses `mm7_history.txt`, and save state stores history unlock times per merged continent. |
| `mmmerge.T.lod/MONLIST.TXT` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/monster_descriptors.txt` | Exported from generated `DataFiles/dmonlist.bin` against the merged monster table. |
| `mmmerge.T.lod/MONSTERS.txt` | Integrated direct | `assets_dev/engine/data_tables/monster_data.txt` | Flat merged monster registry. |
| `mmmerge.T.lod/MapStats.txt` | Integrated direct | `assets_dev/engine/data_tables/map_stats.txt` | Flat merged map registry. World ownership is derived from map packages/active world during load, not from a world-local table. |
| `mmmerge.T.lod/NPCData.txt` | Integrated direct + localization overlay | `assets_dev/engine/data_tables/npc.txt` | Merged NPC registry for the flat base, with `Data/03 LocalizeTables.txt` `NPCDataTxt.Joins` overrides applied. Any remaining world-local NPC use is transitional and should be removed by migrating dependent IDs. |
| `mmmerge.T.lod/NPCGreet.txt` | Integrated direct | `assets_dev/engine/data_tables/npc_greet.txt` | Merged NPC greetings for the flat base. |
| `mmmerge.T.lod/NPCGroup.txt` | Integrated direct | `assets_dev/engine/data_tables/english/npc_group.txt` | Merged NPC group text for the flat base. |
| `mmmerge.T.lod/NPCNews.txt` | Integrated direct | `assets_dev/engine/data_tables/npc_news.txt` | Merged NPC news for the flat base. |
| `mmmerge.T.lod/NPCText.txt` | Integrated direct | `assets_dev/engine/data_tables/npc_topic_text.txt` | Merged NPC topic text for the flat base. |
| `mmmerge.T.lod/NPCTopic.txt` | Integrated direct + localization overlay | `assets_dev/engine/data_tables/npc_topic.txt` | Merged NPC topics for the flat base. `Data/03 LocalizeTables.txt` `NPCTopic 1765` is applied. |
| `mmmerge.T.lod/OBJLIST.TXT` | Integrated converted | `assets_dev/engine/data_tables/object_list.txt` | Converted to OpenYAMM internal object schema. Runtime/editor use this as authoritative. |
| `mmmerge.T.lod/POTION.TXT` | Integrated direct + runtime consumed | `assets_dev/engine/data_tables/english/potion.txt` | Authoritative merged potion mix matrix and potion/reagent display text. Runtime parses the target potion ids from the matrix header, including MMerge's extra potion ids. |
| `mmmerge.T.lod/POTNOTES.TXT` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/english/potnotes.txt` | Potion mix autonote unlock matrix. Runtime keeps it separate from `POTION.TXT` and unlocks non-zero `autonote.txt` ids after successful potion mixing. |
| `mmmerge.T.lod/Placemon.txt` | Integrated direct | `assets_dev/engine/data_tables/english/place_mon.txt` | Flat merged placed-monster display text for the flat base. |
| `mmmerge.T.lod/Quests.txt` | Integrated direct | `assets_dev/engine/data_tables/english/quests.txt` | Merged QBit registry. |
| `mmmerge.T.lod/SFT.TXT` | Integrated converted, Use generated BIN | `assets_dev/engine/rendering/sprite_frame_data_common.yml`, `assets_dev/engine/rendering/sprite_frames/monsters/*.yml` | Exported from generated `DataFiles/dsft.bin`. |
| `mmmerge.T.lod/SPCITEMS.TXT` | Integrated direct | `assets_dev/engine/data_tables/special_item_enchants.txt`, `SPCITEMS.TXT` | Kept both current target names. |
| `mmmerge.T.lod/STDITEMS.TXT` | Integrated direct | `assets_dev/engine/data_tables/standard_item_enchants.txt` | Standard item enchants. |
| `mmmerge.T.lod/Skilldes.txt` | Integrated direct | `assets_dev/engine/data_tables/english/skill_des.txt` | Skill descriptions. |
| `mmmerge.T.lod/Spells.txt` | Integrated direct | `assets_dev/engine/data_tables/english/spells.txt` | Spell text. |
| `mmmerge.T.lod/Trans.txt` | Integrated direct | `assets_dev/engine/data_tables/english/trans.txt` | Transition text registry for the flat base. Any remaining world-local transition use is transitional and should be removed by migrating event references. |
| `mmmerge.T.lod/class.txt` | Integrated direct | `assets_dev/engine/data_tables/english/class.txt` | Class descriptions. |
| `mmmerge.T.lod/history.txt` | Integrated direct + runtime consumed | `assets_dev/engine/data_tables/english/history.txt` | Authoritative MM8/Jadame history book. Runtime uses this as merged continent 1 history text and keeps unlock state separate from MM7 history ids. |
| `mmmerge.T.lod/pcnames.txt` | Integrated direct | `assets_dev/engine/data_tables/english/pc_names.txt` | PC names. |
| `mmmerge.T.lod/rnditems.txt` | Integrated direct | `assets_dev/engine/data_tables/random_items.txt` | Random item table. |
| `mmmerge.T.lod/roster.txt` | Integrated direct | `assets_dev/engine/data_tables/roster.txt` | Flat merged roster registry for the flat base. Any remaining world-local roster use is transitional and should be removed by migrating dependent IDs. |
| `mmmerge.T.lod/scroll.txt` | Integrated direct | `assets_dev/engine/data_tables/english/scroll.txt` | Required TSV parser fix before promotion. |
| `mmmerge.T.lod/sounds.txt` | Integrated direct | `assets_dev/engine/data_tables/sounds.txt` | Flat engine sound catalog. |
| `mmmerge.T.lod/stats.txt` | Integrated direct | `assets_dev/engine/data_tables/english/stats.txt` | Character inspect stat text. |

## `Data/Tables`

| Source | Status | OpenYAMM target / next step | Notes |
| --- | --- | --- | --- |
| `Tables/Additional UI.txt` | Integrated direct + typed base loader | `assets_dev/engine/data_tables/additional_ui.txt` | Loaded as base data; runtime UI/config consumer pending. |
| `Tables/Bolster - formulas.txt` | Integrated direct + typed base loader, Runtime covered | `assets_dev/engine/data_tables/bolster_formulas.txt` | Loaded as base data. Runtime monster bolster uses C++ equivalents of the default MMerge formula rows, the special `76` HP formula, and the bolstered PlayerAC formula; no dynamic formula-expression evaluator exists yet. |
| `Tables/Bolster - maps.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/bolster_maps.txt` | Runtime applies this table to `MapStats` for continent ids, map bolster metadata, profession rarity caps, custom outdoor sky lookup, and feature-gated monster bolster map settings. |
| `Tables/Bolster - monsters.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/bolster_monsters.txt` | Runtime uses this table for generated outdoor NPC filtering, peasant gating, name gender, profession rarity context, bounty-hunt exclusions, and feature-gated monster bolster behavior: family-level extra points, immobile classification, HP sizing/caps, new ranged attacks, generated spells, and summon/replicate eligibility. Generated ranged attacks/spells are wired into shared actor combat; active summon/replicate execution can be added later if we model MMerge monster special actions. |
| `Tables/Character doll types.txt` | Integrated converted | `assets_dev/engine/data_tables/doll_types.txt` | Converted the full MMerge paperdoll-type set. Target keeps Y values negated for the existing OpenYAMM loader/UI convention. |
| `Tables/Character portraits.txt` | Integrated converted | `assets_dev/engine/data_tables/character_data.txt` | Converted the full merged portrait/paperdoll list. Source `#` was shifted to the active one-based `StatsUI` id; unused helm coordinates remain unsupported by the target schema. |
| `Tables/Character selection.txt` | Integrated converted + typed base loader, Partially runtime consumed | `assets_dev/engine/data_tables/character_selection.yml` | MMerge parses the source TXT in `Scripts/General/MenuChooseCharacter.lua` and `Scripts/General/CharacterOutfits.lua` for race/class availability, continent starts, and portrait/outfit rules. OpenYAMM stores the active table as YAML with separate `race_class_availability` and `new_game_continents` sections. New-game creation currently assumes the Jadame/MM8 continent, cycles available portraits from `character_data.txt`, uses separate class selector buttons to cycle valid classes for the selected portrait/race/continent, and supports MMerge-style add/remove/select controls for up to five starting characters; the future continent-selection screen will pass the selected continent instead of this temporary fixed key. |
| `Tables/Character voices.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/character_voices.txt` | Runtime speech playback resolves `SpeechId` through `character_speech_events.txt` to MMerge sound-type rows in this table, then selects the active character voice-set sound id directly. The active speech reaction table now covers the MMerge extended face-animation ids used by `Faces.lua`/`const.FaceAnimation`, including shop, house, BTB, quest, award, travel, and stat reactions. The old `sounds.txt` comment-key/inferred speech-block lookup has been removed. |
| `Tables/Chest.txt` | Integrated converted | `assets_dev/engine/data_tables/chest_data.txt` | Active table is a superset: MMerge name/size/image ids match, and OpenYAMM adds texture names plus UI grid metadata. |
| `Tables/Class Extra.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/class_extra.txt` | MMerge parses this in `Scripts/Structs/After/RemoveClassLimits.lua` as expanded class kind and promotion-step metadata. Runtime applies this metadata to class resource rows and uses it for promotion-chain skill-cap lookups. |
| `Tables/Class HP SP.txt` | Integrated converted | `assets_dev/engine/data_tables/class_multipliers.txt` | Converted MMerge HP/SP values; compact mana stat codes are expanded to the active enum names. |
| `Tables/Class Skills.txt` | Integrated direct | `assets_dev/engine/data_tables/class_skills.txt` | Same orientation as OpenYAMM after canonical class-name parsing; extra merged class columns are accepted. |
| `Tables/Class Starting Skills.txt` | Integrated converted | `assets_dev/engine/data_tables/class_starting_skills.txt` | Transposed from skill rows to class rows; the combined High Priest/Master Wizard column is split for the active class-name model. |
| `Tables/Class Starting Stats.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/class_starting_stats.txt` | Source is parsed into typed race stat data including `base/max` and `+ add` progression cells. New-game stat editing now uses this MMerge table directly; the old generated `race_starting_stats.txt` support table was removed from the active engine data path. |
| `Tables/Complex item pictures offsets.txt` | Integrated direct + typed base loader, Not consumed | `assets_dev/engine/data_tables/complex_item_picture_offsets.txt` | Loaded as base data only. Runtime deliberately does not consume this portrait-specific offset table yet; current MMerge source has one override row. |
| `Tables/Complex item pictures.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/complex_item_pictures.txt` | Authoritative equipped doll item placement source. Runtime body-equipment rendering reads per-item/per-doll-type coordinates directly from this table. The old generated `item_equip_pos.txt` support table was removed. |
| `Tables/Continent settings.txt` | Integrated direct + typed base loader, Partially runtime consumed | `assets_dev/engine/data_tables/continent_settings.txt` | Runtime uses continent settings with bolster-map continent ids for outdoor sky/weather setup, continent-specific death movie/respawn/start destinations, profession-news gating, NPC follower gating, and NPC reputation gating. Remaining candidates are saturation/softness and guard/shop reputation flags; specific water and loading pictures are intentionally skipped for now. |
| `Tables/DecList.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/decoration_data.txt` | Exported from generated `DataFiles/ddeclist.bin`. Runtime/editor use this as authoritative; existing MM8 scene decoration IDs were remapped to this merged table. |
| `Tables/HW water textures.txt` | Integrated direct + typed base loader | `assets_dev/engine/data_tables/hw_water_textures.txt` | Loaded as base data; renderer/world presentation consumer pending. |
| `Tables/House Movies.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/house_movies.txt`, `assets_dev/engine/data_tables/house_animations.txt` | Direct table is loaded to resolve MM7 house animation ids to movie stems. The converted sidecar resolves MMerge `Sounds` groups through the MMerge sound tables into explicit house sound base ids, so house speech no longer falls back to the original MM8 room-sound formula. |
| `Tables/House exits.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/house_exits.txt` | Runtime applies this table to MMerge `2DEvents.txt` other-exit rows: exit picture slots, destination map ids, quest-bit restrictions, and per-map entrance coordinates now drive direct house exit actions. |
| `Tables/House rules.txt` | Integrated direct + typed base loader + runtime consumed | `assets_dev/engine/data_tables/house_rules.txt` | Source is parsed into typed base data. Runtime applies shop stock quality/item-type rows, spellbook shop quality, training caps, Arcomage tavern rules, and stable/boat route slots directly from this table. The old OpenYAMM-only `arcomage_rules.txt` support table was removed. |
| `Tables/IFT.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/icon_frame_data.txt` | Exported from generated `DataFiles/dift.bin`. |
| `Tables/MonList.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/monster_descriptors.txt` | Exported from generated `DataFiles/dmonlist.bin` against the merged monster table. |
| `Tables/MonPortraits.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/monster_portraits.txt` | MMerge parses this in `Scripts/Structs/After/RemoveMonPortraitsLimits.lua` for expanded monster/NPC portrait group lookup. Runtime generic actor/NPC dialogue uses this table to resolve actor names to NPC portrait ids; generated NPCs persist the resolved portrait override and the follower HUD renders those `npc####` portraits. |
| `Tables/Monster Kinds.txt` | Integrated converted, Runtime consumed | `assets_dev/engine/data_tables/monster_data.txt` `Kinds` column | MMerge monster category flags are promoted into the authoritative merged monster rows as comma-separated tags parsed into typed runtime flags. Runtime slaying-family checks and undead spell targeting now read the monster stats flags directly; `titan` is an OpenYAMM extension tag for the existing David/Titan slaying enchant. `monster_kinds.txt` remains reference/import source data only. |
| `Tables/NPC BTB.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/npc_btb.txt` | MMerge uses this from `Scripts/General/NPCFollowers.lua` for beg/bribe/threat personality gates and related text ids. Runtime NPC fallback dialogue now uses the parsed personalities to offer BTB actions and display the table-owned success/fail text ids. |
| `Tables/NPC names.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/npc_names.txt` | MMerge uses this with `Scripts/General/NPCNewsTopics.lua` for generated NPC names and news/NPC table support. Runtime generated generic actor NPCs now use the merged male/female name pools when assigned to MMerge free NPC slots. |
| `Tables/NPC professions.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/npc_professions.txt` | MMerge uses this from `Scripts/General/NPCFollowers.lua` for profession text ids, rarity, hire cost, personality, action topic, and join/recruit flags. Runtime NPC fallback dialogue now uses it for profession actions, descriptions, hire offers, follower cost/state/view data, profession news lookup, generated generic actor profession assignment capped by bolster map rarity, and MMerge-style stable/boat travel day reductions. |
| `Tables/News topics - area.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/news_topics_area.txt` | MMerge uses this from `Scripts/General/NPCNewsTopics.lua` for area-filtered NPC news topics. Runtime generic actor/NPC dialogue uses this table to resolve map-area fallback news. |
| `Tables/News topics - continent.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/news_topics_continent.txt` | MMerge uses this from `Scripts/General/NPCNewsTopics.lua` for continent-filtered NPC news topics. Runtime generic actor/NPC dialogue uses active merged continent ids as the fallback after explicit group news and map-area news. |
| `Tables/News topics - profession.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/news_topics_profession.txt` | MMerge uses this from `Scripts/General/NPCNewsTopics.lua` for profession/day-specific NPC news topics. Runtime NPC dialogue uses this table with merged NPC professions to offer profession news actions when an NPC has no explicit topics. |
| `Tables/ObjList.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/object_list.txt` | Exported from generated `DataFiles/dobjlist.bin` into OpenYAMM's internal object schema. Runtime/editor use this as authoritative. |
| `Tables/Outdoor travels.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/outdoor_travels.txt` | Runtime applies this table to `MapStats` during load to configure outdoor map bounds and edge transitions, including cross-world/local outdoor travel destinations and travel days. Audited in `MMERGE_TRANSPORT_TOWN_PORTAL_AUDIT.md`. |
| `Tables/Overlay.txt` | Integrated direct + typed base loader, Use generated BIN | `assets_dev/engine/data_tables/overlay.txt` | TXT is parsed into typed base data for ownership/tracking. Prefer generated overlay registry path for future runtime/exporter use. |
| `Tables/PFT.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/portrait_frame_data.txt` | Exported from generated `DataFiles/dpft.bin`. |
| `Tables/Potion settings.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/potion_settings.txt` | MMerge uses this from `Scripts/Structs/RemoveItemsLimits.lua` for potion item ids, mastery requirements, and drinkable/usable flags. Runtime item classification and potion mixing mastery checks use this table instead of MM8 item-id ranges. Combination results come from the MMerge `POTION.TXT` matrix. |
| `Tables/Race Skills.txt` | Integrated converted + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/race_skills.yml` | Converted from MMerge's sparse-in-practice race/class matrix into OpenYAMM's sparse YAML rule list. Runtime applies the rules through `ClassSkillTable` effective race/class skill caps and creation learnability while preserving base class-only caps for class queries. |
| `Tables/Reagent settings.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/reagent_settings.txt` | MMerge uses this from `Scripts/Structs/RemoveItemsLimits.lua` for reagent item ids and resulting potion item ids. Runtime bottle/reagent mixing now resolves reagent item ids and produced potions from this table instead of the MM8 `200..219` hardcoded range. |
| `Tables/SFT.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/rendering/sprite_frame_data_common.yml`, `assets_dev/engine/rendering/sprite_frames/monsters/*.yml` | Exported from generated `DataFiles/dsft.bin`; exporter marks exact-name one-frame textures as `Image1` when the asset set has no directional-suffix files. |
| `Tables/Sounds.txt` | Integrated converted | `assets_dev/engine/data_tables/sounds.txt` | Active catalog keeps the lowercase LOD rows/comments and now includes every nonzero sound id present in this expanded MMerge table. The import intentionally preserves existing lowercase-LOD names for sound ids that conflict with the expanded table and only fills missing ids from the expanded table. |
| `Tables/Spells2.txt` | Integrated converted | `assets_dev/engine/data_tables/spells.txt` | Spell mana, recovery, and damage columns were applied to the active merged spell table. The old OpenYAMM-only `spells_supplemental.txt` overlay was removed; event cannonball is handled as an event projectile, and monster-only unsupported mechanics are tracked in monster spell support instead of the spell table. |
| `Tables/TFT.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/texture_frame_data.txt` | Exported from generated `DataFiles/dtft.bin`. |
| `Tables/Teacher autonotes.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/teacher_autonotes.txt` | MMerge uses this from `Scripts/General/NPCTeacherAutonotes.lua` to map teacher topics/NPC ids to autonotes. Runtime NPC entry checks current/overridden NPC topic slots, applies explicit `(topic id, NPC id) -> autonote id` mappings first, and otherwise creates MMerge-style generated teacher map notes from the teacher topic table. |
| `Tables/Teacher topics.txt` | Integrated direct + typed base loader, Runtime consumed | `assets_dev/engine/data_tables/teacher_topics.txt` | MMerge parses this in `Scripts/Structs/After/RemoveNPCTablesLimits.lua` for teacher topic ids, skill/mastery, text id, gold, and required skill. Runtime mastery teacher detection/evaluation now uses this table plus the narrow original MM8 `300..416` teacher-topic range fallback for gaps such as Blaster `321`/`323`; label decoding is no longer teacher authority. |
| `Tables/Tile.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/terrain_tile_data.txt` | Exported from generated `DataFiles/dtile.bin`; runtime uses this flat engine table. |
| `Tables/Tile2.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/terrain_tile_data_2.txt` | Exported from generated `DataFiles/dtile2.bin`; runtime uses this flat engine table. |
| `Tables/Tile3.txt` | Integrated converted, Use generated BIN | `assets_dev/engine/data_tables/terrain_tile_data_3.txt` | Exported from generated `DataFiles/dtile3.bin`; runtime uses this flat engine table. |
| `Tables/Town Portal.txt` | Replaced by switch table | - | Removed the OpenYAMM-only converted table. Runtime Town Portal is now driven by `TownPortalSwitch.txt` so MM6/MM7/MM8 use the same continent-aware source as MMerge. |
| `Tables/TownPortalSwitch.txt` | Integrated direct + typed base loader + runtime consumed | `assets_dev/engine/data_tables/town_portal_switch.txt` | `GameDataLoader` owns the typed table. Runtime Town Portal selects the active continent group, background, button icons, positions, unlock QBits, and destinations from this table. Audited in `MMERGE_TRANSPORT_TOWN_PORTAL_AUDIT.md`. |
| `Tables/Transport Index.txt` | Integrated direct + typed base loader, Reference only for active runtime | `assets_dev/engine/data_tables/transport_index.txt` | Source is parsed into typed base data for tracking/reference. Active stable/boat routes use `House rules.txt` plus `Transport Locations.txt`, matching MMerge's final route slots. Audited in `MMERGE_TRANSPORT_TOWN_PORTAL_AUDIT.md`. |
| `Tables/Transport Locations.txt` | Integrated direct + typed base loader + runtime consumed | `assets_dev/engine/data_tables/transport_locations.txt` | Source is parsed into typed base data. Active stable/boat routes use this table directly with route slots from `House rules.txt`; the old `transport_schedules.txt` support table was removed. Audited in `MMERGE_TRANSPORT_TOWN_PORTAL_AUDIT.md`. |
