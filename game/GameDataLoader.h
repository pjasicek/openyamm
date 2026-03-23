#pragma once

#include "engine/AssetFileSystem.h"
#include "game/ChestTable.h"
#include "game/CharacterDollTable.h"
#include "game/ClassSkillTable.h"
#include "game/HouseTable.h"
#include "game/ItemTable.h"
#include "game/MapAssetLoader.h"
#include "game/MapRegistry.h"
#include "game/MapStats.h"
#include "game/MonsterProjectileTable.h"
#include "game/MonsterTable.h"
#include "game/NpcDialogTable.h"
#include "game/ObjectTable.h"
#include "game/RosterTable.h"
#include "game/SpellTable.h"

#include <cstddef>
#include <string>
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
    bool load(const Engine::AssetFileSystem &assetFileSystem);
    bool loadForGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMapById(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByIdForGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByIdForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapByFileName(const Engine::AssetFileSystem &assetFileSystem, const std::string &fileName);
    bool loadMapByFileNameForGameplay(const Engine::AssetFileSystem &assetFileSystem, const std::string &fileName);
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
    const ChestTable &getChestTable() const;
    const HouseTable &getHouseTable() const;
    const ClassSkillTable &getClassSkillTable() const;
    const NpcDialogTable &getNpcDialogTable() const;
    const RosterTable &getRosterTable() const;
    const CharacterDollTable &getCharacterDollTable() const;

private:
    bool loadInternal(const Engine::AssetFileSystem &assetFileSystem, MapLoadPurpose mapLoadPurpose);
    bool loadTable(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        size_t &dataRowCount,
        size_t &columnCount
    );
    static bool isDataRow(const std::vector<std::string> &row);
    bool loadInitialMap(const Engine::AssetFileSystem &assetFileSystem, MapLoadPurpose mapLoadPurpose);
    bool loadSelectedMap(const Engine::AssetFileSystem &assetFileSystem, int mapId, MapLoadPurpose mapLoadPurpose);
    bool loadMapStats(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterProjectileTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadObjectTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadSpellTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadItemTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadChestTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadHouseTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadClassSkillTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadNpcDialogTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadRosterTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadCharacterDollTable(const Engine::AssetFileSystem &assetFileSystem);
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
    MapRegistry m_mapRegistry;
    MapStats m_mapStats;
    MonsterTable m_monsterTable;
    MonsterProjectileTable m_monsterProjectileTable;
    ObjectTable m_objectTable;
    SpellTable m_spellTable;
    ItemTable m_itemTable;
    ChestTable m_chestTable;
    HouseTable m_houseTable;
    ClassSkillTable m_classSkillTable;
    NpcDialogTable m_npcDialogTable;
    RosterTable m_rosterTable;
    CharacterDollTable m_characterDollTable;
    std::optional<MapAssetInfo> m_selectedMap;
};
}
