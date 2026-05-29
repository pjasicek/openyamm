#pragma once

#include "engine/AssetFileSystem.h"
#include "game/arcomage/ArcomageTypes.h"
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
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RaceStartingStatsTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/SpellFxTable.h"
#include "game/tables/TransitionTable.h"

#include <cstddef>
#include <functional>
#include <optional>
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
    void setInitialMapFileName(const std::string &fileName);
    bool load(const Engine::AssetFileSystem &assetFileSystem);
    bool loadCommonForGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadForGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMapById(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByIdForGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByIdForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool selectMapMetadataOnlyById(int mapId);
    bool loadMapByFileName(const Engine::AssetFileSystem &assetFileSystem, const std::string &fileName);
    bool loadMapByFileNameForGameplay(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &fileName,
        const MapLoadProgressPump &progressPump = {});
    bool loadMapByFileNameForHeadlessGameplay(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &fileName
    );
    const std::vector<LoadedTableSummary> &getLoadedTables() const;
    const std::optional<MapAssetInfo> &getSelectedMap() const;
    const MapStats &getMapStats() const;
    const MonsterTable &getMonsterTable() const;
    const MonsterProjectileTable &getMonsterProjectileTable() const;
    const ObjectTable &getObjectTable() const;
    const SpellTable &getSpellTable() const;
    const ItemTable &getItemTable() const;
    const StandardItemEnchantTable &getStandardItemEnchantTable() const;
    const SpecialItemEnchantTable &getSpecialItemEnchantTable() const;
    const ChestTable &getChestTable() const;
    const HouseTable &getHouseTable() const;
    const JournalQuestTable &getJournalQuestTable() const;
    const JournalHistoryTable &getJournalHistoryTable() const;
    const JournalAutonoteTable &getJournalAutonoteTable() const;
    const ClassMultiplierTable &getClassMultiplierTable() const;
    const ClassSkillTable &getClassSkillTable() const;
    const NpcDialogTable &getNpcDialogTable() const;
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
    const MergedNpcProfessionTable &getMergedNpcProfessionTable() const;
    const MergedNpcNameTable &getMergedNpcNameTable() const;
    const MergedNpcBtbTable &getMergedNpcBtbTable() const;
    const MergedNewsTopicTable &getMergedNewsAreaTopicTable() const;
    const MergedNewsTopicTable &getMergedNewsContinentTopicTable() const;
    const MergedNewsProfessionTopicTable &getMergedNewsProfessionTopicTable() const;
    const MergedMonsterPortraitTable &getMergedMonsterPortraitTable() const;
    const MergedPotionSettingTable &getMergedPotionSettingTable() const;
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
    bool loadMapStats(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterProjectileTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadObjectTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadSpellTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadItemTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadItemEnchantTables(const Engine::AssetFileSystem &assetFileSystem);
    bool loadChestTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadHouseTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadJournalTables(const Engine::AssetFileSystem &assetFileSystem);
    bool loadClassMultiplierTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadClassSkillTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadNpcDialogTable(const Engine::AssetFileSystem &assetFileSystem);
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

    std::vector<LoadedTableSummary> m_loadedTables;
    std::string m_activeWorldId = "mm8";
    std::string m_initialMapFileName;
    std::optional<std::unordered_set<std::string>> m_skyTextureAssetNames;
    std::unordered_map<std::string, std::string> m_resolvedMergedSkyTextureNameByKey;
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
    StandardItemEnchantTable m_standardItemEnchantTable;
    SpecialItemEnchantTable m_specialItemEnchantTable;
    ChestTable m_chestTable;
    HouseTable m_houseTable;
    JournalQuestTable m_journalQuestTable;
    JournalHistoryTable m_journalHistoryTable;
    JournalAutonoteTable m_journalAutonoteTable;
    ClassMultiplierTable m_classMultiplierTable;
    ClassSkillTable m_classSkillTable;
    NpcDialogTable m_npcDialogTable;
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
    MergedNpcProfessionTable m_mergedNpcProfessionTable;
    MergedNpcNameTable m_mergedNpcNameTable;
    MergedNpcBtbTable m_mergedNpcBtbTable;
    MergedNewsTopicTable m_mergedNewsAreaTopicTable;
    MergedNewsTopicTable m_mergedNewsContinentTopicTable;
    MergedNewsProfessionTopicTable m_mergedNewsProfessionTopicTable;
    MergedMonsterPortraitTable m_mergedMonsterPortraitTable;
    MergedPotionSettingTable m_mergedPotionSettingTable;
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
};
}
