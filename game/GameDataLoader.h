#pragma once

#include "engine/AssetFileSystem.h"
#include "game/ChestTable.h"
#include "game/HouseTable.h"
#include "game/MapAssetLoader.h"
#include "game/MapRegistry.h"
#include "game/MapStats.h"
#include "game/MonsterTable.h"
#include "game/ObjectTable.h"

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
    bool loadMapById(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    const std::vector<LoadedTableSummary> &getLoadedTables() const;
    const std::optional<MapAssetInfo> &getSelectedMap() const;
    const MapStats &getMapStats() const;
    const MonsterTable &getMonsterTable() const;
    const ObjectTable &getObjectTable() const;
    const ChestTable &getChestTable() const;
    const HouseTable &getHouseTable() const;

private:
    bool loadTable(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        size_t &dataRowCount,
        size_t &columnCount
    );
    static bool isDataRow(const std::vector<std::string> &row);
    bool loadInitialMap(const Engine::AssetFileSystem &assetFileSystem);
    bool loadSelectedMap(const Engine::AssetFileSystem &assetFileSystem, int mapId);
    bool loadMapStats(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadObjectTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadChestTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadHouseTable(const Engine::AssetFileSystem &assetFileSystem);
    bool loadMonsterTextTable(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &virtualPath,
        std::vector<std::vector<std::string>> &rows
    );

    std::vector<LoadedTableSummary> m_loadedTables;
    MapRegistry m_mapRegistry;
    MapStats m_mapStats;
    MonsterTable m_monsterTable;
    ObjectTable m_objectTable;
    ChestTable m_chestTable;
    HouseTable m_houseTable;
    std::optional<MapAssetInfo> m_selectedMap;
};
}
