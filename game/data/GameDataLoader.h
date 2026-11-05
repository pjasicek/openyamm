#pragma once

#include "engine/AssetFileSystem.h"
#include "game/arcomage/ArcomageTypes.h"
#include "game/gameplay/TrainerDirectory.h"
#include "game/content/RulesetDefinition.h"
#include "game/tables/AwardTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/FaceAnimationTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/IconFrameTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/ItemTable.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/MapRegistry.h"
#include "game/mm9/Mm9MapTransition.h"
#include "game/mm9/Mm9TeacherSchedule.h"
#include "game/mm9/Mm9QuestMarkers.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9SkillTrainer.h"
#include "game/mm9/Mm9TransportRoute.h"
#include "game/outdoor/WeatherModel.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/PortraitFrameTable.h"
#include "game/tables/PortraitFxEventTable.h"
#include "game/tables/PotionMixingTable.h"
#include "game/tables/PotionNoteTable.h"
#include "game/rules/maw/MawCraftingData.h"
#include "game/rules/maw/MawDimensionMaps.h"
#include "game/rules/maw/MawTexts.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawPromotions.h"
#include "game/rules/maw/MawMonsterLevels.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RaceStartingStatsTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/SpellFxTable.h"
#include "game/tables/TransitionTable.h"

#include <cstddef>
#include <functional>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
struct LoadedTableSummary
{
    std::string virtualPath;
    size_t dataRowCount;
    size_t columnCount;
};

class GameDataLoader
{
public:
    void setActiveWorldId(const std::string &worldId);
    // The ruleset whose table overrides the next load applies; Standard (no overrides) until set.
    void setActiveRuleset(const RulesetDefinition &ruleset);
    const RulesetDefinition &activeRuleset() const;
    // The paths of the active ruleset's table contributions the last load applied, so a test can find one that no
    // loader reads (audit DAT-1: map_stats.txt was skipped for weeks).
    const std::set<std::string> &appliedRulesetContributions() const;
    // The active ruleset's package directory ("engine/rulesets/<id>/"), whose map and event overlays load after the worlds';
    // empty for Standard.
    std::string activeRulesetRoot() const;
    void setInitialMapFileName(const std::string &fileName);
    // Actor models (settings `actor_models`): the merged models/actors.yml of every mounted world, or only
    // overrideManifestPath when it is set. Map loads then skip the sprites of the monsters they bind.
    void setActorModels(bool enabled, const std::string &overrideManifestPath);
    // Whether map loads read the surface material maps of face textures (video.surface_materials).
    void setSurfaceMaterials(bool enabled) { m_surfaceMaterials = enabled; }
    // Loads the actor model manifest (every mounted world's actors.yml) when actor models are on; a map load does it.
    bool ensureActorModelManifest(const Engine::AssetFileSystem &assetFileSystem);
    // Null while actor models are off or before the first map load.
    const std::shared_ptr<const ActorModelManifest> &actorModelManifest() const;
    bool load(const Engine::AssetFileSystem &assetFileSystem);
    bool loadCommonForGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadForGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMapById(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByIdForGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByIdForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByFileName(const Engine::AssetFileSystem &assetFileSystem, const std::string &fileName);
    bool loadMapByFileNameForGameplay(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &fileName,
        const MapLoadProgressPump &progressPump = {});
    bool loadMapByFileNameForHeadlessGameplay(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &fileName
    );
    // Decoration billboards without baked lighting (MapLoadPurpose::DecorationPlacements).
    bool loadMapByFileNameForDecorationPlacements(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &fileName
    );
    const std::vector<LoadedTableSummary> &getLoadedTables() const;
    const std::optional<MapAssetInfo> &getSelectedMap() const;
    size_t releaseSelectedMapRenderSourcePixels();
    bool selectedMapRenderSourcePixelsReleased() const;
    size_t lastReleasedMapRenderSourcePixelBytes() const;
    const MapStats &getMapStats() const;
    const MonsterTable &getMonsterTable() const;
    const MonsterProjectileTable &getMonsterProjectileTable() const;
    const ObjectTable &getObjectTable() const;
    const SpellTable &getSpellTable() const;
    const ItemTable &getItemTable() const;
    const std::unordered_map<std::string, uint32_t> &getLoadedContentPackageSchemas() const;
    const StandardItemEnchantTable &getStandardItemEnchantTable() const;
    const SpecialItemEnchantTable &getSpecialItemEnchantTable() const;
    const ChestTable &getChestTable() const;
    const HouseTable &getHouseTable() const;
    const AwardTable &getAwardTable() const;
    const JournalQuestTable &getJournalQuestTable() const;
    const JournalHistoryTable &getJournalHistoryTable() const;
    const JournalAutonoteTable &getJournalAutonoteTable() const;
    const ClassMultiplierTable &getClassMultiplierTable() const;
    const ClassSkillTable &getClassSkillTable() const;
    const NpcDialogTable &getNpcDialogTable() const;
    const Mm9MapTransitionTable &getMm9MapTransitionTable() const;
    const Mm9TeacherScheduleTable &getMm9TeacherScheduleTable() const;
    const Mm9RudeDialogueTable &getMm9RudeDialogueTable() const;
    const Mm9SkillTrainerTable &getMm9SkillTrainerTable() const;
    const Mm9TransportRouteTable &getMm9TransportRouteTable() const;
    const Mm9QuestInteractionTable &getMm9QuestInteractionTable() const;
    const RosterTable &getRosterTable() const;
    const CharacterDollTable &getCharacterDollTable() const;
    const CharacterInspectTable &getCharacterInspectTable() const;
    const RaceStartingStatsTable &getRaceStartingStatsTable() const;
    const ReadableScrollTable &getReadableScrollTable() const;
    const PotionMixingTable &getPotionMixingTable() const;
    const PotionNoteTable &getPotionNoteTable() const;
    const ArcomageLibrary &getArcomageLibrary() const;
    const PortraitFrameTable &getPortraitFrameTable() const;
    const IconFrameTable &getIconFrameTable() const;
    const SpellFxTable &getSpellFxTable() const;
    const PortraitFxEventTable &getPortraitFxEventTable() const;
    const FaceAnimationTable &getFaceAnimationTable() const;
    const TransitionTable &getTransitionTable() const;
    const MergedClassExtraTable &getMergedClassExtraTable() const;
    const MergedCharacterSelectionTable &getMergedCharacterSelectionTable() const;
    const MergedRaceSkillTable &getMergedRaceSkillTable() const;
    const MergedTeacherTopicTable &getMergedTeacherTopicTable() const;
    const MergedTeacherAutonoteTable &getMergedTeacherAutonoteTable() const;
    const TrainerDirectory &getTrainerDirectory() const;
    const MergedNpcProfessionTable &getMergedNpcProfessionTable() const;
    const MergedNpcNameTable &getMergedNpcNameTable() const;
    const MergedNpcBtbTable &getMergedNpcBtbTable() const;
    const MergedNewsTopicTable &getMergedNewsAreaTopicTable() const;
    const MergedNewsTopicTable &getMergedNewsContinentTopicTable() const;
    const MergedNewsProfessionTopicTable &getMergedNewsProfessionTopicTable() const;
    const MergedMonsterPortraitTable &getMergedMonsterPortraitTable() const;
    const MergedPotionSettingTable &getMergedPotionSettingTable() const;
    // The MAW ruleset's map level data; null unless MAW is the active ruleset.
    const MawMapLevels *mawMapLevels() const;
    // The MAW ruleset's item data (artifacts, legendary affixes); null unless MAW is the active ruleset.
    const MawItemData *mawItemData() const;
    const MawPromotionData *mawPromotionData() const;
    const MawCraftingData *mawCraftingData() const;
    const MawDimensionData *mawDimensionData() const;
    const MawTextData *mawTextData() const;
    const MergedReagentSettingTable &getMergedReagentSettingTable() const;
    const MergedAdditionalUiTable &getMergedAdditionalUiTable() const;
    const MergedBolsterFormulaTable &getMergedBolsterFormulaTable() const;
    const MergedBolsterMapTable &getMergedBolsterMapTable() const;
    const MergedBolsterMonsterTable &getMergedBolsterMonsterTable() const;
    const MergedCharacterVoiceTable &getMergedCharacterVoiceTable() const;
    const MergedClassStartingStatTable &getMergedClassStartingStatsSourceTable() const;
    const MergedComplexItemPictureOffsetTable &getMergedComplexItemPictureOffsetTable() const;
    const MergedComplexItemPictureTable &getMergedComplexItemPictureTable() const;
    const MergedContinentSettingTable &getMergedContinentSettingTable() const;
    const MergedContinentSettingEntry *findMergedContinentSettingsForMap(const MapStatsEntry &map) const;
    const MergedHardwareWaterTextureTable &getMergedHardwareWaterTextureTable() const;
    const MergedHouseExitTable &getMergedHouseExitTable() const;
    const MergedHouseRuleTable &getMergedHouseRuleTable() const;
    const MergedHistoryTable &getMergedMm7HistoryTable() const;
    const MergedOutdoorTravelTable &getMergedOutdoorTravelTable() const;
    const MergedOverlayTable &getMergedOverlayTable() const;
    const MergedTownPortalSwitchTable &getMergedTownPortalSwitchTable() const;
    const MergedTransportIndexTable &getMergedTransportIndexTable() const;
    const MergedTransportLocationTable &getMergedTransportLocationTable() const;

private:
    bool loadInternal(const Engine::AssetFileSystem &assetFileSystem, MapLoadPurpose mapLoadPurpose, bool loadInitialMap);
    bool loadTable(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        size_t &dataRowCount,
        size_t &columnCount
    );
    static bool isDataRow(const std::vector<std::string> &row);
    bool loadInitialMap(const Engine::AssetFileSystem &assetFileSystem, MapLoadPurpose mapLoadPurpose);
    bool loadSelectedMap(
        const Engine::AssetFileSystem &assetFileSystem,
        int mapId,
        MapLoadPurpose mapLoadPurpose,
        const MapLoadProgressPump &progressPump = {});
    void applyMergedContinentSettingsToSelectedMap(const Engine::AssetFileSystem &assetFileSystem);
    // An indoor map open to the sky with scene `sky: {weather}` (MM9's outdoor regions as BLVs): its weather profile
    // (weather.yml rules and this map's chances), as an outdoor map's; nothing for every other indoor map.
    void applyOpenSkyWeatherToSelectedMap(const Engine::AssetFileSystem &assetFileSystem);
    const WeatherRules &weatherRules(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMapStats(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterProjectileTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadObjectTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadSpellTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadItemTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadItemEnchantTables(const Engine::AssetFileSystem &assetFileSystem);
    bool loadChestTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadHouseTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadAwardTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadJournalTables(const Engine::AssetFileSystem &assetFileSystem);
    bool loadClassMultiplierTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadClassSkillTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadNpcDialogTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMm9MapTransitionTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMm9TeacherScheduleTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMm9RudeDialogueTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMm9SkillTrainerTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMm9TransportRouteTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMm9QuestInteractionTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadRosterTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadCharacterDollTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadCharacterInspectTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadRaceStartingStatsTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadReadableScrollTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadPotionMixingTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadPotionNoteTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadArcomageLibrary(const Engine::AssetFileSystem &assetFileSystem);
    bool loadPortraitFrameTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadIconFrameTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadSpellFxTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadPortraitFxEventTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadFaceAnimationTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadTransitionTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMergedBaseTables(const Engine::AssetFileSystem &assetFileSystem);
    bool applyMergedRuntimeTables();
    bool loadFirstTextTableRows(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::vector<std::string> &virtualPaths,
        std::vector<std::vector<std::string>> &rows
    );
    bool loadTextTableRows(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        std::vector<std::vector<std::string>> &rows
    );
    // A whole data file (not a text table) under the active ruleset: its replacement if it has one.
    std::optional<std::string> readRulesetDataFile(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath
    ) const;
    bool loadPotionEffects(const Engine::AssetFileSystem &assetFileSystem);
    bool loadRulesetData(const Engine::AssetFileSystem &assetFileSystem);
    // Every skill teacher from the loaded tables, with trainer_places.txt (and the active world's own rows) and the
    // Ledger of Teachers' teacher_ledger.yml.
    bool loadTrainerDirectory(const Engine::AssetFileSystem &assetFileSystem);
    // Applies the active ruleset's override or replacement of this engine table, if it has one.
    bool applyActiveRulesetTable(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        std::vector<std::vector<std::string>> &rows
    ) const;

    std::vector<LoadedTableSummary> m_loadedTables;
    std::string m_activeWorldId = "mm8";
    RulesetDefinition m_activeRuleset = standardRulesetDefinition();
    mutable std::set<std::string> m_appliedRulesetContributions;
    bool m_actorModelsEnabled = false;
    bool m_surfaceMaterials = false;
    std::string m_actorModelManifestOverride;
    std::shared_ptr<const ActorModelManifest> m_pActorModelManifest;
    // The world and asset content m_pActorModelManifest was read for.
    std::string m_actorModelManifestWorldId;
    uint64_t m_actorModelManifestGeneration = 0;
    std::string m_initialMapFileName;
    std::optional<std::unordered_set<std::string>> m_knownSkyNames;
    std::unordered_map<std::string, std::string> m_resolvedMergedSkyTextureNameByKey;
    std::optional<WeatherRules> m_weatherRules;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> m_scriptBitmapDirectoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> m_scriptBitmapPathByKey;
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> m_scriptBitmapPixelsByKey;
    MapRegistry m_mapRegistry;
    MapStats m_mapStats;
    MonsterTable m_monsterTable;
    MonsterProjectileTable m_monsterProjectileTable;
    ObjectTable m_objectTable;
    SpellTable m_spellTable;
    ItemTable m_itemTable;
    void recordActiveRulesetSchema();
    std::unordered_map<std::string, uint32_t> m_loadedContentPackageSchemas = {{"engine", 1}};
    StandardItemEnchantTable m_standardItemEnchantTable;
    SpecialItemEnchantTable m_specialItemEnchantTable;
    ChestTable m_chestTable;
    HouseTable m_houseTable;
    AwardTable m_awardTable;
    JournalQuestTable m_journalQuestTable;
    JournalHistoryTable m_journalHistoryTable;
    JournalAutonoteTable m_journalAutonoteTable;
    ClassMultiplierTable m_classMultiplierTable;
    ClassSkillTable m_classSkillTable;
    NpcDialogTable m_npcDialogTable;
    std::shared_ptr<Mm9MapTransitionTable> m_pMm9MapTransitionTable;
    std::shared_ptr<Mm9TeacherScheduleTable> m_pMm9TeacherScheduleTable;
    std::shared_ptr<Mm9RudeDialogueTable> m_pMm9RudeDialogueTable;
    std::shared_ptr<Mm9SkillTrainerTable> m_pMm9SkillTrainerTable;
    std::shared_ptr<Mm9TransportRouteTable> m_pMm9TransportRouteTable;
    Mm9QuestInteractionTable m_mm9QuestInteractionTable;
    RosterTable m_rosterTable;
    CharacterDollTable m_characterDollTable;
    CharacterInspectTable m_characterInspectTable;
    RaceStartingStatsTable m_raceStartingStatsTable;
    ReadableScrollTable m_readableScrollTable;
    PotionMixingTable m_potionMixingTable;
    PotionNoteTable m_potionNoteTable;
    ArcomageLibrary m_arcomageLibrary;
    PortraitFrameTable m_portraitFrameTable;
    IconFrameTable m_iconFrameTable;
    SpellFxTable m_spellFxTable;
    PortraitFxEventTable m_portraitFxEventTable;
    FaceAnimationTable m_faceAnimationTable;
    TransitionTable m_transitionTable;
    MergedClassExtraTable m_mergedClassExtraTable;
    MergedCharacterSelectionTable m_mergedCharacterSelectionTable;
    MergedRaceSkillTable m_mergedRaceSkillTable;
    MergedTeacherTopicTable m_mergedTeacherTopicTable;
    MergedTeacherAutonoteTable m_mergedTeacherAutonoteTable;
    TrainerDirectory m_trainerDirectory;
    MergedNpcProfessionTable m_mergedNpcProfessionTable;
    MergedNpcNameTable m_mergedNpcNameTable;
    MergedNpcBtbTable m_mergedNpcBtbTable;
    MergedNewsTopicTable m_mergedNewsAreaTopicTable;
    MergedNewsTopicTable m_mergedNewsContinentTopicTable;
    MergedNewsProfessionTopicTable m_mergedNewsProfessionTopicTable;
    MergedMonsterPortraitTable m_mergedMonsterPortraitTable;
    MergedPotionSettingTable m_mergedPotionSettingTable;
    std::optional<MawMapLevels> m_mawMapLevels;
    std::optional<MawItemData> m_mawItemData;
    std::optional<MawPromotionData> m_mawPromotionData;
    std::optional<MawCraftingData> m_mawCraftingData;
    std::optional<MawDimensionData> m_mawDimensionData;
    std::optional<MawTextData> m_mawTextData;
    MergedReagentSettingTable m_mergedReagentSettingTable;
    MergedAdditionalUiTable m_mergedAdditionalUiTable;
    MergedBolsterFormulaTable m_mergedBolsterFormulaTable;
    MergedBolsterMapTable m_mergedBolsterMapTable;
    MergedBolsterMonsterTable m_mergedBolsterMonsterTable;
    MergedCharacterVoiceTable m_mergedCharacterVoiceTable;
    MergedClassStartingStatTable m_mergedClassStartingStatsSourceTable;
    MergedComplexItemPictureOffsetTable m_mergedComplexItemPictureOffsetTable;
    MergedComplexItemPictureTable m_mergedComplexItemPictureTable;
    MergedContinentSettingTable m_mergedContinentSettingTable;
    MergedHardwareWaterTextureTable m_mergedHardwareWaterTextureTable;
    MergedHouseExitTable m_mergedHouseExitTable;
    MergedHouseRuleTable m_mergedHouseRuleTable;
    MergedHistoryTable m_mergedMm7HistoryTable;
    MergedOutdoorTravelTable m_mergedOutdoorTravelTable;
    MergedOverlayTable m_mergedOverlayTable;
    MergedTownPortalSwitchTable m_mergedTownPortalSwitchTable;
    MergedTransportIndexTable m_mergedTransportIndexTable;
    MergedTransportLocationTable m_mergedTransportLocationTable;
    MapAssetLoadSharedCache m_mapAssetLoadSharedCache;
    std::optional<MapAssetInfo> m_selectedMap;
    bool m_selectedMapRenderSourcePixelsReleased = false;
    size_t m_lastReleasedMapRenderSourcePixelBytes = 0;
};
}
