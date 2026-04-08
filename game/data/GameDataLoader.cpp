#include "game/data/GameDataLoader.h"

#include "game/arcomage/ArcomageLoader.h"
#include "engine/TextTable.h"
#include "game/events/EventRuntime.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>

#include <cctype>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string toUpperCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::toupper(static_cast<unsigned char>(character)));
    }

    return result;
}

std::vector<std::string> buildScriptPathCandidates(const std::string &baseName, const std::string &extension)
{
    std::vector<std::string> candidates;
    candidates.push_back("Data/EnglishT/" + baseName + extension);
    candidates.push_back("Data/EnglishT/" + toUpperCopy(baseName) + extension);
    candidates.push_back("Data/EnglishT/" + baseName + toUpperCopy(extension));
    candidates.push_back("Data/EnglishT/" + toUpperCopy(baseName) + toUpperCopy(extension));
    return candidates;
}

std::optional<std::vector<uint8_t>> readFirstExistingBinary(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath
)
{
    for (const std::string &candidate : candidates)
    {
        const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(candidate);

        if (bytes)
        {
            resolvedPath = candidate;
            return bytes;
        }
    }

    return std::nullopt;
}

std::string mapScriptBaseName(const std::string &fileName)
{
    const std::filesystem::path path(fileName);
    return path.stem().string();
}

void writeTextFile(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream outputStream(path);
    outputStream << text;
}

size_t countChestItemSlots(const MapDeltaChest &chest)
{
    size_t occupiedSlots = 0;

    for (int16_t itemIndex : chest.inventoryMatrix)
    {
        if (itemIndex > 0)
        {
            ++occupiedSlots;
        }
    }

    return occupiedSlots;
}

std::vector<uint32_t> getOpenedChestIds(
    uint16_t eventId,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    if (eventId == 0)
    {
        return {};
    }

    if (localEvtProgram && localEvtProgram->hasEvent(eventId))
    {
        return localEvtProgram->getOpenedChestIds(eventId);
    }

    if (globalEvtProgram && globalEvtProgram->hasEvent(eventId))
    {
        return globalEvtProgram->getOpenedChestIds(eventId);
    }

    return {};
}

std::string summarizeChestTargets(
    const std::vector<uint32_t> &chestIds,
    const MapDeltaData &mapDeltaData,
    const ChestTable &chestTable
)
{
    if (chestIds.empty())
    {
        return {};
    }

    std::string summary;

    for (size_t chestIndex = 0; chestIndex < chestIds.size(); ++chestIndex)
    {
        if (chestIndex > 0)
        {
            summary += " | ";
        }

        const uint32_t chestId = chestIds[chestIndex];
        summary += "#" + std::to_string(chestId);

        if (chestId >= mapDeltaData.chests.size())
        {
            summary += ":out";
            continue;
        }

        const MapDeltaChest &chest = mapDeltaData.chests[chestId];
        const ChestEntry *pChestEntry = chestTable.get(chest.chestTypeId);
        summary += ":" + std::to_string(chest.chestTypeId);

        if (pChestEntry != nullptr && !pChestEntry->name.empty())
        {
            summary += ":" + pChestEntry->name;
        }

        summary += " s=" + std::to_string(countChestItemSlots(chest));
    }

    return summary;
}

void logOutdoorChestLinks(
    const OutdoorMapData &outdoorMapData,
    const MapDeltaData &mapDeltaData,
    const ChestTable &chestTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    bool anyLinks = false;

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OutdoorEntity &entity = outdoorMapData.entities[entityIndex];

        for (const uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
        {
            const std::vector<uint32_t> chestIds = getOpenedChestIds(eventId, localEvtProgram, globalEvtProgram);

            if (chestIds.empty())
            {
                continue;
            }

            if (!anyLinks)
            {
                std::cout << "  chest_links:\n";
                anyLinks = true;
            }

            std::cout << "    entity=" << entityIndex
                      << " evt=" << eventId
                      << " chests=" << summarizeChestTargets(chestIds, mapDeltaData, chestTable)
                      << '\n';
        }
    }

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bmodel.faces[faceIndex];
            const std::vector<uint32_t> chestIds = getOpenedChestIds(
                face.cogTriggeredNumber,
                localEvtProgram,
                globalEvtProgram
            );

            if (chestIds.empty())
            {
                continue;
            }

            if (!anyLinks)
            {
                std::cout << "  chest_links:\n";
                anyLinks = true;
            }

            std::cout << "    bmodel=" << bmodelIndex
                      << " face=" << faceIndex
                      << " evt=" << face.cogTriggeredNumber
                      << " chests=" << summarizeChestTargets(chestIds, mapDeltaData, chestTable)
                      << '\n';
        }
    }
}

void logIndoorChestLinks(
    const IndoorMapData &indoorMapData,
    const MapDeltaData &mapDeltaData,
    const ChestTable &chestTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    bool anyLinks = false;

    for (size_t entityIndex = 0; entityIndex < indoorMapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = indoorMapData.entities[entityIndex];

        for (const uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
        {
            const std::vector<uint32_t> chestIds = getOpenedChestIds(eventId, localEvtProgram, globalEvtProgram);

            if (chestIds.empty())
            {
                continue;
            }

            if (!anyLinks)
            {
                std::cout << "  chest_links:\n";
                anyLinks = true;
            }

            std::cout << "    entity=" << entityIndex
                      << " evt=" << eventId
                      << " chests=" << summarizeChestTargets(chestIds, mapDeltaData, chestTable)
                      << '\n';
        }
    }

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];
        const std::vector<uint32_t> chestIds = getOpenedChestIds(face.cogTriggered, localEvtProgram, globalEvtProgram);

        if (chestIds.empty())
        {
            continue;
        }

        if (!anyLinks)
        {
            std::cout << "  chest_links:\n";
            anyLinks = true;
        }

        std::cout << "    face=" << faceIndex
                  << " evt=" << face.cogTriggered
                  << " chests=" << summarizeChestTargets(chestIds, mapDeltaData, chestTable)
                  << '\n';
    }

    for (size_t mechanismIndex = 0; mechanismIndex < mapDeltaData.doors.size(); ++mechanismIndex)
    {
        const MapDeltaDoor &door = mapDeltaData.doors[mechanismIndex];
        uint16_t eventId = static_cast<uint16_t>(door.doorId);

        for (uint16_t faceId : door.faceIds)
        {
            if (faceId >= indoorMapData.faces.size())
            {
                continue;
            }

            const uint16_t linkedEventId = indoorMapData.faces[faceId].cogTriggered;

            if (linkedEventId != 0)
            {
                eventId = linkedEventId;
                break;
            }
        }

        const std::vector<uint32_t> chestIds = getOpenedChestIds(eventId, localEvtProgram, globalEvtProgram);

        if (chestIds.empty())
        {
            continue;
        }

        if (!anyLinks)
        {
            std::cout << "  chest_links:\n";
            anyLinks = true;
        }

        std::cout << "    mechanism=" << mechanismIndex
                  << " id=" << door.doorId
                  << " evt=" << eventId
                  << " chests=" << summarizeChestTargets(chestIds, mapDeltaData, chestTable)
                  << '\n';
    }
}

std::optional<std::string> findBitmapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &directoryAssetPathsByPath,
    std::unordered_map<std::string, std::optional<std::string>> &bitmapPathByKey
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(textureName);
    const auto cachedPathIt = bitmapPathByKey.find(cacheKey);

    if (cachedPathIt != bitmapPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto assetPathsIt = directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (assetPathsIt != directoryAssetPathsByPath.end())
    {
        pAssetPaths = &assetPathsIt->second;
    }
    else
    {
        std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> assetPaths;

        for (const std::string &entry : entries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths = &directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName) + ".bmp";
    const auto resolvedPathIt = pAssetPaths->find(normalizedTextureName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        bitmapPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    bitmapPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &directoryAssetPathsByPath,
    std::unordered_map<std::string, std::optional<std::string>> &bitmapPathByKey
)
{
    const std::optional<std::string> bitmapPath =
        findBitmapPath(
            assetFileSystem,
            directoryPath,
            textureName,
            directoryAssetPathsByPath,
            bitmapPathByKey);

    if (!bitmapPath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}

void collectSetTextureNames(const EvtProgram &evtProgram, std::vector<std::string> &textureNames)
{
    for (const EvtEvent &event : evtProgram.getEvents())
    {
        for (const EvtInstruction &instruction : event.instructions)
        {
            if (instruction.opcode != EvtOpcode::SetTexture || !instruction.stringValue || instruction.stringValue->empty())
            {
                continue;
            }

            const std::string normalizedName = toLowerCopy(*instruction.stringValue);

            if (std::find(textureNames.begin(), textureNames.end(), normalizedName) == textureNames.end())
            {
                textureNames.push_back(normalizedName);
            }
        }
    }
}

void appendIndoorScriptTextures(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram,
    std::optional<IndoorTextureSet> &indoorTextureSet
)
{
    if (!indoorTextureSet)
    {
        return;
    }

    std::vector<std::string> textureNames;

    if (localEvtProgram)
    {
        collectSetTextureNames(*localEvtProgram, textureNames);
    }

    if (globalEvtProgram)
    {
        collectSetTextureNames(*globalEvtProgram, textureNames);
    }

    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;

    for (const std::string &textureName : textureNames)
    {
        bool alreadyPresent = false;

        for (const OutdoorBitmapTexture &texture : indoorTextureSet->textures)
        {
            if (toLowerCopy(texture.textureName) == textureName)
            {
                alreadyPresent = true;
                break;
            }
        }

        if (alreadyPresent)
        {
            continue;
        }

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                directoryAssetPathsByPath,
                bitmapPathByKey);

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, assetFileSystem.getAssetScaleTier());
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, assetFileSystem.getAssetScaleTier());
        texture.physicalWidth = textureWidth;
        texture.physicalHeight = textureHeight;
        texture.pixels = *pixels;
        indoorTextureSet->textures.push_back(std::move(texture));
    }
}

void logIndoorDoors(
    const IndoorMapData &indoorMapData,
    const MapDeltaData &mapDeltaData
)
{
        std::cout << "  door_records:\n";

    for (size_t doorIndex = 0; doorIndex < mapDeltaData.doors.size(); ++doorIndex)
    {
        const MapDeltaDoor &door = mapDeltaData.doors[doorIndex];
        bool hasValidVertex = false;
        int minX = 0;
        int minY = 0;
        int minZ = 0;
        int maxX = 0;
        int maxY = 0;
        int maxZ = 0;
        int64_t sumX = 0;
        int64_t sumY = 0;
        int64_t sumZ = 0;
        uint32_t validVertexCount = 0;

        for (uint16_t vertexId : door.vertexIds)
        {
            if (vertexId >= indoorMapData.vertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = indoorMapData.vertices[vertexId];

            if (!hasValidVertex)
            {
                minX = maxX = vertex.x;
                minY = maxY = vertex.y;
                minZ = maxZ = vertex.z;
                hasValidVertex = true;
            }
            else
            {
                if (vertex.x < minX)
                {
                    minX = vertex.x;
                }

                if (vertex.y < minY)
                {
                    minY = vertex.y;
                }

                if (vertex.z < minZ)
                {
                    minZ = vertex.z;
                }

                if (vertex.x > maxX)
                {
                    maxX = vertex.x;
                }

                if (vertex.y > maxY)
                {
                    maxY = vertex.y;
                }

                if (vertex.z > maxZ)
                {
                    maxZ = vertex.z;
                }
            }

            sumX += vertex.x;
            sumY += vertex.y;
            sumZ += vertex.z;
            ++validVertexCount;
        }

        std::cout << "    door=" << doorIndex
                  << " slot=" << door.slotIndex
                  << " id=" << door.doorId
                  << " attr=0x" << std::hex << door.attributes << std::dec
                  << " state=" << door.state
                  << " trig_ms=" << door.timeSinceTriggered
                  << " dir=(" << door.directionX << "," << door.directionY << "," << door.directionZ << ")"
                  << " move=" << door.moveLength
                  << " open=" << door.openSpeed
                  << " close=" << door.closeSpeed
                  << " verts=" << door.numVertices
                  << " faces=" << door.numFaces
                  << " sectors=" << door.numSectors
                  << " offsets=" << door.numOffsets
                  << " valid_verts=" << validVertexCount;

        if (hasValidVertex && validVertexCount > 0)
        {
            std::cout << " center=("
                      << (sumX / static_cast<int64_t>(validVertexCount)) << ","
                      << (sumY / static_cast<int64_t>(validVertexCount)) << ","
                      << (sumZ / static_cast<int64_t>(validVertexCount)) << ")"
                      << " bounds=("
                      << minX << "," << minY << "," << minZ << ")->("
                      << maxX << "," << maxY << "," << maxZ << ")";
        }

        std::cout << '\n';
    }
}
}

bool GameDataLoader::load(const Engine::AssetFileSystem &assetFileSystem)
{
    return loadInternal(assetFileSystem, MapLoadPurpose::Full);
}

bool GameDataLoader::loadForGameplay(const Engine::AssetFileSystem &assetFileSystem)
{
    return loadInternal(assetFileSystem, MapLoadPurpose::FullGameplay);
}

bool GameDataLoader::loadForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem)
{
    return loadInternal(assetFileSystem, MapLoadPurpose::HeadlessGameplay);
}

bool GameDataLoader::loadInternal(const Engine::AssetFileSystem &assetFileSystem, MapLoadPurpose mapLoadPurpose)
{
    m_loadedTables.clear();

    if (!loadMapStats(assetFileSystem))
    {
        return false;
    }

    if (!loadMonsterTable(assetFileSystem))
    {
        return false;
    }

    if (!loadMonsterProjectileTable(assetFileSystem))
    {
        return false;
    }

    if (!loadObjectTable(assetFileSystem))
    {
        return false;
    }

    if (!loadSpellTable(assetFileSystem))
    {
        return false;
    }

    if (!loadItemTable(assetFileSystem))
    {
        return false;
    }

    if (!loadItemEnchantTables(assetFileSystem))
    {
        return false;
    }

    if (!loadItemEquipPosTable(assetFileSystem))
    {
        return false;
    }

    if (!loadChestTable(assetFileSystem))
    {
        return false;
    }

    if (!loadHouseTable(assetFileSystem))
    {
        return false;
    }

    if (!loadJournalTables(assetFileSystem))
    {
        return false;
    }

    if (!loadClassSkillTable(assetFileSystem))
    {
        return false;
    }

    if (!loadCharacterInspectTable(assetFileSystem))
    {
        return false;
    }

    if (!loadReadableScrollTable(assetFileSystem))
    {
        return false;
    }

    if (!loadArcomageLibrary(assetFileSystem))
    {
        return false;
    }

    if (!loadNpcDialogTable(assetFileSystem))
    {
        return false;
    }

    if (!loadRosterTable(assetFileSystem))
    {
        return false;
    }

    if (!loadCharacterDollTable(assetFileSystem))
    {
        return false;
    }

    m_npcDialogTable.resolveSpecialTopics(m_rosterTable);

    if (!loadInitialMap(assetFileSystem, mapLoadPurpose))
    {
        return false;
    }

    const std::vector<std::string> tablePaths = {
        "Data/EnglishT/Spells.txt",
        "Data/EnglishT/rnditems.txt",
        "Data/EnglishT/scroll.txt"
    };

    for (const std::string &tablePath : tablePaths)
    {
        size_t dataRowCount = 0;
        size_t columnCount = 0;

        if (!loadTable(assetFileSystem, tablePath, dataRowCount, columnCount))
        {
            return false;
        }

        m_loadedTables.push_back({tablePath, dataRowCount, columnCount});
    }

    std::cout << "Loaded gameplay tables:\n";
    std::cout << "  Data/EnglishT/mapstats.txt entries=" << m_mapStats.getEntries().size() << '\n';

    for (const LoadedTableSummary &loadedTable : m_loadedTables)
    {
        std::cout << "  " << loadedTable.virtualPath
                  << " rows=" << loadedTable.dataRowCount
                  << " columns=" << loadedTable.columnCount << '\n';
    }

    return true;
}

bool GameDataLoader::loadMapById(const Engine::AssetFileSystem &assetFileSystem, int mapId)
{
    return loadSelectedMap(assetFileSystem, mapId, MapLoadPurpose::Full);
}

bool GameDataLoader::loadMapByIdForGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId)
{
    return loadSelectedMap(assetFileSystem, mapId, MapLoadPurpose::FullGameplay);
}

bool GameDataLoader::loadMapByIdForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem, int mapId)
{
    return loadSelectedMap(assetFileSystem, mapId, MapLoadPurpose::HeadlessGameplay);
}

bool GameDataLoader::loadMapByFileName(const Engine::AssetFileSystem &assetFileSystem, const std::string &fileName)
{
    const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findByFileName(fileName);

    if (!selectedMap)
    {
        return false;
    }

    return loadSelectedMap(assetFileSystem, selectedMap->id, MapLoadPurpose::Full);
}

bool GameDataLoader::loadMapByFileNameForGameplay(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &fileName)
{
    const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findByFileName(fileName);

    if (!selectedMap)
    {
        return false;
    }

    return loadSelectedMap(assetFileSystem, selectedMap->id, MapLoadPurpose::FullGameplay);
}

bool GameDataLoader::loadMapByFileNameForHeadlessGameplay(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &fileName
)
{
    const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findByFileName(fileName);

    if (!selectedMap)
    {
        return false;
    }

    return loadSelectedMap(assetFileSystem, selectedMap->id, MapLoadPurpose::HeadlessGameplay);
}

const std::vector<LoadedTableSummary> &GameDataLoader::getLoadedTables() const
{
    return m_loadedTables;
}

const std::optional<MapAssetInfo> &GameDataLoader::getSelectedMap() const
{
    return m_selectedMap;
}

const MapStats &GameDataLoader::getMapStats() const
{
    return m_mapStats;
}

const MonsterTable &GameDataLoader::getMonsterTable() const
{
    return m_monsterTable;
}

const MonsterProjectileTable &GameDataLoader::getMonsterProjectileTable() const
{
    return m_monsterProjectileTable;
}

const ObjectTable &GameDataLoader::getObjectTable() const
{
    return m_objectTable;
}

const SpellTable &GameDataLoader::getSpellTable() const
{
    return m_spellTable;
}

const ItemTable &GameDataLoader::getItemTable() const
{
    return m_itemTable;
}

const StandardItemEnchantTable &GameDataLoader::getStandardItemEnchantTable() const
{
    return m_standardItemEnchantTable;
}

const SpecialItemEnchantTable &GameDataLoader::getSpecialItemEnchantTable() const
{
    return m_specialItemEnchantTable;
}

const ItemEquipPosTable &GameDataLoader::getItemEquipPosTable() const
{
    return m_itemEquipPosTable;
}

const ChestTable &GameDataLoader::getChestTable() const
{
    return m_chestTable;
}

const HouseTable &GameDataLoader::getHouseTable() const
{
    return m_houseTable;
}

const JournalQuestTable &GameDataLoader::getJournalQuestTable() const
{
    return m_journalQuestTable;
}

const JournalHistoryTable &GameDataLoader::getJournalHistoryTable() const
{
    return m_journalHistoryTable;
}

const JournalAutonoteTable &GameDataLoader::getJournalAutonoteTable() const
{
    return m_journalAutonoteTable;
}

const ClassSkillTable &GameDataLoader::getClassSkillTable() const
{
    return m_classSkillTable;
}

const NpcDialogTable &GameDataLoader::getNpcDialogTable() const
{
    return m_npcDialogTable;
}

const RosterTable &GameDataLoader::getRosterTable() const
{
    return m_rosterTable;
}

const CharacterDollTable &GameDataLoader::getCharacterDollTable() const
{
    return m_characterDollTable;
}

const CharacterInspectTable &GameDataLoader::getCharacterInspectTable() const
{
    return m_characterInspectTable;
}

const ReadableScrollTable &GameDataLoader::getReadableScrollTable() const
{
    return m_readableScrollTable;
}

const ArcomageLibrary &GameDataLoader::getArcomageLibrary() const
{
    return m_arcomageLibrary;
}

bool GameDataLoader::loadTable(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    size_t &dataRowCount,
    size_t &columnCount
)
{
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(virtualPath);

    if (!fileContents)
    {
        std::cerr << "Failed to read gameplay table: " << virtualPath << '\n';
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*fileContents);

    if (!parsedTable)
    {
        std::cerr << "Failed to parse gameplay table: " << virtualPath << '\n';
        return false;
    }

    dataRowCount = 0;
    columnCount = 0;

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> &row = parsedTable->getRow(rowIndex);

        if (!isDataRow(row))
        {
            continue;
        }

        ++dataRowCount;

        if (row.size() > columnCount)
        {
            columnCount = row.size();
        }
    }

    if (dataRowCount == 0)
    {
        std::cerr << "Gameplay table contains no data rows: " << virtualPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::isDataRow(const std::vector<std::string> &row)
{
    if (row.empty() || row.front().empty())
    {
        return false;
    }

    for (const char character : row.front())
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}

bool GameDataLoader::loadMapStats(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile("Data/EnglishT/mapstats.txt");

    if (!fileContents)
    {
        std::cerr << "Failed to read typed gameplay table: Data/EnglishT/mapstats.txt\n";
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*fileContents);

    if (!parsedTable)
    {
        std::cerr << "Failed to parse typed gameplay table: Data/EnglishT/mapstats.txt\n";
        return false;
    }

    std::vector<std::vector<std::string>> rows;

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    if (!m_mapStats.loadFromRows(rows))
    {
        return false;
    }

    m_mapRegistry.initialize(m_mapStats.getEntries());
    return true;
}

bool GameDataLoader::loadMonsterTable(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::optional<std::vector<uint8_t>> monsterTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dmonlist.bin");

    if (!monsterTableBytes)
    {
        std::cerr << "Failed to read monster table: Data/EnglishT/dmonlist.bin\n";
        return false;
    }

    if (!m_monsterTable.loadFromBytes(*monsterTableBytes))
    {
        std::cerr << "Failed to parse monster table: Data/EnglishT/dmonlist.bin\n";
        return false;
    }

    std::vector<std::vector<std::string>> monsterRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/MONSTERS.txt", monsterRows))
    {
        return false;
    }

    if (!m_monsterTable.loadDisplayNamesFromRows(monsterRows))
    {
        std::cerr << "Failed to parse monster display names: Data/EnglishT/MONSTERS.txt\n";
        return false;
    }

    if (!m_monsterTable.loadStatsFromRows(monsterRows))
    {
        std::cerr << "Failed to parse monster runtime stats: Data/EnglishT/MONSTERS.txt\n";
        return false;
    }

    std::vector<std::vector<std::string>> placedMonsterRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/placemon.txt", placedMonsterRows))
    {
        return false;
    }

    if (!m_monsterTable.loadUniqueNamesFromRows(placedMonsterRows))
    {
        std::cerr << "Failed to parse placed monster names: Data/EnglishT/placemon.txt\n";
        return false;
    }

    std::vector<std::vector<std::string>> monsterRelationRows;

    if (!loadTextTableRows(assetFileSystem, "Data/MONSTER_RELATION_DATA.txt", monsterRelationRows))
    {
        return false;
    }

    if (!m_monsterTable.loadRelationsFromRows(monsterRelationRows))
    {
        std::cerr << "Failed to parse monster relation table: Data/MONSTER_RELATION_DATA.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadHouseTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string sourcePath = "Data/HOUSE_DATA.txt";

    if (!loadTextTableRows(assetFileSystem, sourcePath, rows))
    {
        return false;
    }

    if (!m_houseTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse house table: " << sourcePath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> animationRows;

    if (loadTextTableRows(assetFileSystem, "Data/HOUSE_ANIMATIONS.txt", animationRows))
    {
        m_houseTable.loadAnimationRows(animationRows);
    }

    std::vector<std::vector<std::string>> transportRows;

    if (loadTextTableRows(assetFileSystem, "Data/TRANSPORT_SCHEDULES.txt", transportRows))
    {
        m_houseTable.loadTransportScheduleRows(transportRows);
    }

    return true;
}

bool GameDataLoader::loadNpcDialogTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> greetingRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {"Data/NPC_GREET.txt"},
            greetingRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> textRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {"Data/NPC_TOPIC_TEXT.txt"},
            textRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> topicRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {"Data/NPC_TOPIC.txt"},
            topicRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> npcRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {"Data/NPC.txt"},
            npcRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> newsRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {"Data/NPC_NEWS.txt"},
            newsRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> groupRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {"Data/EnglishT/NPCGROUP.TXT", "Data/EnglishT/npcgroup.txt"},
            groupRows))
    {
        return false;
    }

    if (!m_npcDialogTable.loadGreetingsFromRows(greetingRows)
        || !m_npcDialogTable.loadNewsFromRows(newsRows)
        || !m_npcDialogTable.loadGroupNewsFromRows(groupRows)
        || !m_npcDialogTable.loadTextsFromRows(textRows)
        || !m_npcDialogTable.loadTopicsFromRows(topicRows)
        || !m_npcDialogTable.loadNpcRows(npcRows))
    {
        std::cerr << "Failed to parse NPC dialog tables\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadJournalTables(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> questRows;

    if (!loadFirstTextTableRows(assetFileSystem, {"Data/EnglishT/quests.txt", "Data/EnglishT/QUESTS.txt"}, questRows))
    {
        std::cerr << "Failed to read journal quest table\n";
        return false;
    }

    std::vector<std::vector<std::string>> historyRows;

    if (!loadFirstTextTableRows(assetFileSystem, {"Data/EnglishT/history.txt", "Data/EnglishT/HISTORY.txt"}, historyRows))
    {
        std::cerr << "Failed to read journal history table\n";
        return false;
    }

    std::vector<std::vector<std::string>> autonoteRows;

    if (!loadFirstTextTableRows(assetFileSystem, {"Data/EnglishT/Autonote.txt", "Data/EnglishT/AUTONOTE.txt"}, autonoteRows))
    {
        std::cerr << "Failed to read journal autonote table\n";
        return false;
    }

    if (!m_journalQuestTable.loadFromRows(questRows))
    {
        std::cerr << "Failed to parse journal quest table\n";
        return false;
    }

    if (!m_journalHistoryTable.loadFromRows(historyRows))
    {
        std::cerr << "Failed to parse journal history table\n";
        return false;
    }

    if (!m_journalAutonoteTable.loadFromRows(autonoteRows))
    {
        std::cerr << "Failed to parse journal autonote table\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadClassSkillTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> capRows;

    if (!loadTextTableRows(assetFileSystem, "Data/CLASS_SKILLS.txt", capRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> startingRows;

    if (!loadTextTableRows(assetFileSystem, "Data/CLASS_STARTING_SKILLS.txt", startingRows))
    {
        return false;
    }

    if (!m_classSkillTable.loadCapsFromRows(capRows) || !m_classSkillTable.loadStartingSkillsFromRows(startingRows))
    {
        std::cerr << "Failed to parse class skill tables\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadRosterTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/roster.txt", rows))
    {
        return false;
    }

    if (!m_rosterTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse roster table: Data/EnglishT/roster.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadCharacterDollTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> characterRows;

    if (!loadTextTableRows(assetFileSystem, "Data/CHARACTER_DATA.txt", characterRows))
    {
        std::cerr << "Failed to read character doll table: Data/CHARACTER_DATA.txt\n";
        return false;
    }

    std::vector<std::vector<std::string>> dollTypeRows;

    if (!loadTextTableRows(assetFileSystem, "Data/DOLL_TYPES.txt", dollTypeRows))
    {
        std::cerr << "Failed to read doll type table: Data/DOLL_TYPES.txt\n";
        return false;
    }

    if (!m_characterDollTable.loadCharacterRows(characterRows))
    {
        std::cerr << "Failed to parse character doll table: Data/CHARACTER_DATA.txt\n";
        return false;
    }

    if (!m_characterDollTable.loadDollTypeRows(dollTypeRows))
    {
        std::cerr << "Failed to parse doll type table: Data/DOLL_TYPES.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadCharacterInspectTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> statRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/stats.txt", statRows))
    {
        std::cerr << "Failed to read character inspect table: Data/EnglishT/stats.txt\n";
        return false;
    }

    std::vector<std::vector<std::string>> skillRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/Skilldes.txt", skillRows))
    {
        std::cerr << "Failed to read character inspect table: Data/EnglishT/Skilldes.txt\n";
        return false;
    }

    if (!m_characterInspectTable.loadStatRows(statRows) || !m_characterInspectTable.loadSkillRows(skillRows))
    {
        std::cerr << "Failed to parse character inspect tables\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadReadableScrollTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {"Data/EnglishT/scroll.txt", "Data/EnglishT/SCROLL.txt"}, rows))
    {
        std::cerr << "Failed to read readable scroll table\n";
        return false;
    }

    if (!m_readableScrollTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse readable scroll table\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadArcomageLibrary(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> ruleRows;

    if (!loadTextTableRows(assetFileSystem, "Data/ARCOMAGE_RULES.txt", ruleRows))
    {
        std::cerr << "Failed to read Arcomage tavern rule table\n";
        return false;
    }

    std::vector<std::vector<std::string>> cardRows;

    if (!loadTextTableRows(assetFileSystem, "Data/ARCOMAGE_CARDS.txt", cardRows))
    {
        std::cerr << "Failed to read Arcomage card table\n";
        return false;
    }

    ArcomageLoader loader;

    if (!loader.load(ruleRows, cardRows))
    {
        std::cerr << "Failed to parse Arcomage tables\n";
        return false;
    }

    m_arcomageLibrary = loader.library();
    return true;
}

bool GameDataLoader::loadFirstTextTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &virtualPaths,
    std::vector<std::vector<std::string>> &rows
)
{
    for (const std::string &virtualPath : virtualPaths)
    {
        const std::optional<std::string> fileContents = assetFileSystem.readTextFile(virtualPath);

        if (!fileContents)
        {
            continue;
        }

        const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*fileContents);

        if (!parsedTable)
        {
            std::cerr << "Failed to parse gameplay table: " << virtualPath << '\n';
            return false;
        }

        rows.clear();

        for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
        {
            rows.push_back(parsedTable->getRow(rowIndex));
        }

        if (!rows.empty())
        {
            return true;
        }
    }

    if (!virtualPaths.empty())
    {
        std::cerr << "Failed to read gameplay table: " << virtualPaths.front() << '\n';
    }

    return false;
}

bool GameDataLoader::loadObjectTable(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::optional<std::vector<uint8_t>> objectTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dobjlist.bin");

    if (!objectTableBytes)
    {
        std::cerr << "Failed to read object table: Data/EnglishT/dobjlist.bin\n";
        return false;
    }

    if (!m_objectTable.loadFromBytes(*objectTableBytes))
    {
        std::cerr << "Failed to parse object table: Data/EnglishT/dobjlist.bin\n";
        return false;
    }

    std::vector<std::vector<std::string>> objectRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/OBJLIST.TXT", objectRows))
    {
        return false;
    }

    if (!m_objectTable.loadDisplayRows(objectRows))
    {
        std::cerr << "Failed to augment object table from Data/EnglishT/OBJLIST.TXT\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadMonsterProjectileTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, "Data/MONSTER_PROJECTILES.txt", rows))
    {
        return false;
    }

    if (!m_monsterProjectileTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse monster projectile table: Data/MONSTER_PROJECTILES.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadSpellTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, "Data/SPELLS.txt", rows))
    {
        return false;
    }

    if (!m_spellTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse spell table: Data/SPELLS.txt\n";
        return false;
    }

    if (assetFileSystem.exists("Data/SPELLS_SUPPLEMENTAL.txt"))
    {
        std::vector<std::vector<std::string>> supplementalRows;

        if (!loadTextTableRows(assetFileSystem, "Data/SPELLS_SUPPLEMENTAL.txt", supplementalRows))
        {
            return false;
        }

        rows.insert(rows.end(), supplementalRows.begin(), supplementalRows.end());

        if (!m_spellTable.loadFromRows(rows))
        {
            std::cerr << "Failed to parse spell table: Data/SPELLS_SUPPLEMENTAL.txt\n";
            return false;
        }
    }

    return true;
}

bool GameDataLoader::loadItemTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> itemRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/ITEMS.txt", itemRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> randomItemRows;

    if (!loadTextTableRows(assetFileSystem, "Data/EnglishT/rnditems.txt", randomItemRows))
    {
        return false;
    }

    if (!m_itemTable.load(assetFileSystem, itemRows, randomItemRows))
    {
        std::cerr << "Failed to parse item table: Data/EnglishT/ITEMS.txt / rnditems.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadItemEnchantTables(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> standardRows;
    std::vector<std::vector<std::string>> specialRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {
                "Data/EnglishT/STDITEMS.TXT",
                "Data/EnglishT/stditems.txt",
            },
            standardRows))
    {
        std::cerr << "Failed to read standard item enchant table: STDITEMS.TXT\n";
        return false;
    }

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {
                "Data/EnglishT/SPCITEMS.TXT",
                "Data/EnglishT/spcitems.txt",
            },
            specialRows))
    {
        std::cerr << "Failed to read special item enchant table: SPCITEMS.TXT\n";
        return false;
    }

    if (!m_standardItemEnchantTable.load(standardRows) || !m_specialItemEnchantTable.load(specialRows))
    {
        std::cerr << "Failed to parse item enchant tables: STDITEMS / SPCITEMS\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadItemEquipPosTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, "Data/ITEM_EQUIP_POS.txt", rows))
    {
        return false;
    }

    if (!m_itemEquipPosTable.load(rows))
    {
        std::cerr << "Failed to parse item equip position table: Data/ITEM_EQUIP_POS.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadChestTable(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::optional<std::vector<uint8_t>> chestTableBytes =
        assetFileSystem.readBinaryFile("Data/EnglishT/dchest.bin");
    const std::optional<std::string> chestUiText =
        assetFileSystem.readTextFile("Data/CHEST_UI.txt");

    if (!chestTableBytes)
    {
        std::cerr << "Failed to read chest table: Data/EnglishT/dchest.bin\n";
        return false;
    }

    if (!chestUiText)
    {
        std::cerr << "Failed to read chest UI table: Data/CHEST_UI.txt\n";
        return false;
    }

    if (!m_chestTable.loadFromBytes(*chestTableBytes))
    {
        std::cerr << "Failed to parse chest table: Data/EnglishT/dchest.bin\n";
        return false;
    }

    if (!m_chestTable.loadUiLayoutFromText(*chestUiText))
    {
        std::cerr << "Failed to parse chest UI table: Data/CHEST_UI.txt\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadTextTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::vector<std::vector<std::string>> &rows
)
{
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(virtualPath);

    if (!fileContents)
    {
        std::cerr << "Failed to read gameplay table: " << virtualPath << '\n';
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*fileContents);

    if (!parsedTable)
    {
        std::cerr << "Failed to parse gameplay table: " << virtualPath << '\n';
        return false;
    }

    rows.clear();

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return true;
}

bool GameDataLoader::loadInitialMap(const Engine::AssetFileSystem &assetFileSystem, MapLoadPurpose mapLoadPurpose)
{
    return loadSelectedMap(assetFileSystem, 1, mapLoadPurpose);
}

bool GameDataLoader::loadSelectedMap(
    const Engine::AssetFileSystem &assetFileSystem,
    int mapId,
    MapLoadPurpose mapLoadPurpose
)
{
    const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findById(mapId);

    if (!selectedMap)
    {
        std::cerr << "Failed to select map from map registry: id=" << mapId << '\n';
        return false;
    }

    const MapAssetLoader mapAssetLoader;
    m_selectedMap = mapAssetLoader.load(assetFileSystem, *selectedMap, m_monsterTable, m_objectTable, mapLoadPurpose);

    if (!m_selectedMap)
    {
        std::cerr << "Failed to load initial map asset for " << selectedMap->fileName << '\n';
        return false;
    }

    const std::string localScriptBaseName = mapScriptBaseName(selectedMap->fileName);
    std::string resolvedEvtPath;
    const std::optional<std::vector<uint8_t>> localEvtBytes = readFirstExistingBinary(
        assetFileSystem,
        buildScriptPathCandidates(localScriptBaseName, ".evt"),
        resolvedEvtPath
    );

    if (localEvtBytes)
    {
        EvtProgram evtProgram = {};

        if (!evtProgram.loadFromBytes(*localEvtBytes))
        {
            std::cerr << "Failed to parse local event program: " << resolvedEvtPath << '\n';
            return false;
        }

        m_selectedMap->localEvtProgram = std::move(evtProgram);
    }

    std::string resolvedStrPath;
    const std::optional<std::vector<uint8_t>> localStrBytes = readFirstExistingBinary(
        assetFileSystem,
        buildScriptPathCandidates(localScriptBaseName, ".str"),
        resolvedStrPath
    );

    if (localStrBytes)
    {
        StrTable strTable = {};

        if (!strTable.loadFromBytes(*localStrBytes))
        {
            std::cerr << "Failed to parse local string table: " << resolvedStrPath << '\n';
            return false;
        }

        m_selectedMap->localStrTable = std::move(strTable);
    }

    std::string resolvedGlobalEvtPath;
    const std::optional<std::vector<uint8_t>> globalEvtBytes = readFirstExistingBinary(
        assetFileSystem,
        buildScriptPathCandidates("Global", ".evt"),
        resolvedGlobalEvtPath
    );

    if (globalEvtBytes)
    {
        EvtProgram evtProgram = {};

        if (!evtProgram.loadFromBytes(*globalEvtBytes))
        {
            std::cerr << "Failed to parse global event program: " << resolvedGlobalEvtPath << '\n';
            return false;
        }

        m_selectedMap->globalEvtProgram = std::move(evtProgram);
    }

    std::string resolvedGlobalStrPath;
    std::optional<StrTable> globalStrTable;
    const std::optional<std::vector<uint8_t>> globalStrBytes = readFirstExistingBinary(
        assetFileSystem,
        buildScriptPathCandidates("Global", ".str"),
        resolvedGlobalStrPath
    );

    if (globalStrBytes)
    {
        StrTable strTable = {};

        if (!strTable.loadFromBytes(*globalStrBytes))
        {
            std::cerr << "Failed to parse global string table: " << resolvedGlobalStrPath << '\n';
            return false;
        }

        globalStrTable = std::move(strTable);
    }

    appendIndoorScriptTextures(
        assetFileSystem,
        m_selectedMap->localEvtProgram,
        m_selectedMap->globalEvtProgram,
        m_selectedMap->indoorTextureSet
    );

    const HouseTable &houseTable = m_houseTable;
    const StrTable emptyStrTable = {};
    const StrTable &resolvedLocalStrTable = m_selectedMap->localStrTable ? *m_selectedMap->localStrTable : emptyStrTable;
    const StrTable &resolvedGlobalStrTable = globalStrTable ? *globalStrTable : emptyStrTable;

    if (m_selectedMap->localEvtProgram)
    {
        const std::filesystem::path dumpPath =
            std::filesystem::path("script_dumps") / (localScriptBaseName + ".evt.txt");
        writeTextFile(dumpPath, m_selectedMap->localEvtProgram->dump(resolvedLocalStrTable));

        EventIrProgram eventIrProgram = {};
        eventIrProgram.buildFromEvtProgram(
            *m_selectedMap->localEvtProgram,
            resolvedLocalStrTable,
            houseTable,
            m_npcDialogTable
        );
        const std::filesystem::path irDumpPath =
            std::filesystem::path("script_dumps") / (localScriptBaseName + ".ir.txt");
        writeTextFile(irDumpPath, eventIrProgram.dump());
        m_selectedMap->localEventIrProgram = std::move(eventIrProgram);
    }

    if (m_selectedMap->globalEvtProgram)
    {
        const std::filesystem::path dumpPath = std::filesystem::path("script_dumps") / "Global.evt.txt";
        writeTextFile(dumpPath, m_selectedMap->globalEvtProgram->dump(resolvedGlobalStrTable));

        EventIrProgram eventIrProgram = {};
        eventIrProgram.buildFromEvtProgram(
            *m_selectedMap->globalEvtProgram,
            resolvedGlobalStrTable,
            houseTable,
            m_npcDialogTable
        );
        const std::filesystem::path irDumpPath = std::filesystem::path("script_dumps") / "Global.ir.txt";
        writeTextFile(irDumpPath, eventIrProgram.dump());
        m_selectedMap->globalEventIrProgram = std::move(eventIrProgram);
    }

    {
        EventRuntime eventRuntime = {};
        const std::optional<MapDeltaData> &mapDeltaData = m_selectedMap->outdoorMapDeltaData
            ? m_selectedMap->outdoorMapDeltaData
            : m_selectedMap->indoorMapDeltaData;
        EventRuntimeState runtimeState = {};
        eventRuntime.buildOnLoadState(
            m_selectedMap->localEventIrProgram,
            m_selectedMap->globalEventIrProgram,
            mapDeltaData,
            runtimeState
        );
        m_selectedMap->eventRuntimeState = std::move(runtimeState);
    }

    std::cout << "Selected map:\n";
    std::cout << "  id=" << m_selectedMap->map.id << '\n';
    std::cout << "  name=" << m_selectedMap->map.name << '\n';
    std::cout << "  file=" << m_selectedMap->geometryPath << '\n';
    std::cout << "  size=" << m_selectedMap->geometrySize << " bytes\n";
    std::cout << "  environment=" << m_selectedMap->map.environmentName << '\n';
    std::cout << "  top_level_area=" << (m_selectedMap->map.isTopLevelArea ? "yes" : "no") << '\n';

    if (m_selectedMap->companionPath && m_selectedMap->companionSize)
    {
        std::cout << "  companion=" << *m_selectedMap->companionPath
                  << " (" << *m_selectedMap->companionSize << " bytes)\n";
    }

    if (m_selectedMap->localStrTable)
    {
        std::cout << "  local_str_entries=" << m_selectedMap->localStrTable->getEntries().size() << '\n';
    }

    if (m_selectedMap->localEvtProgram)
    {
        std::cout << "  local_evt_events=" << m_selectedMap->localEvtProgram->getEvents().size() << '\n';
        std::cout << "  local_evt_instructions=" << m_selectedMap->localEvtProgram->getInstructionCount() << '\n';
        std::cout << "  local_evt_dump=script_dumps/" << localScriptBaseName << ".evt.txt\n";

        if (m_selectedMap->localEventIrProgram)
        {
            std::cout << "  local_ir_events=" << m_selectedMap->localEventIrProgram->getEvents().size() << '\n';
            std::cout << "  local_ir_instructions=" << m_selectedMap->localEventIrProgram->getInstructionCount() << '\n';
            std::cout << "  local_ir_dump=script_dumps/" << localScriptBaseName << ".ir.txt\n";
        }
    }

    if (m_selectedMap->globalEvtProgram)
    {
        if (globalStrTable)
        {
            std::cout << "  global_str_entries=" << globalStrTable->getEntries().size() << '\n';
        }

        std::cout << "  global_evt_events=" << m_selectedMap->globalEvtProgram->getEvents().size() << '\n';
        std::cout << "  global_evt_instructions=" << m_selectedMap->globalEvtProgram->getInstructionCount() << '\n';
        std::cout << "  global_evt_dump=script_dumps/Global.evt.txt\n";

        if (m_selectedMap->globalEventIrProgram)
        {
            std::cout << "  global_ir_events=" << m_selectedMap->globalEventIrProgram->getEvents().size() << '\n';
            std::cout << "  global_ir_instructions=" << m_selectedMap->globalEventIrProgram->getInstructionCount() << '\n';
            std::cout << "  global_ir_dump=script_dumps/Global.ir.txt\n";
        }
    }

    if (m_selectedMap->eventRuntimeState)
    {
        std::cout << "  onload_local_events=" << m_selectedMap->eventRuntimeState->localOnLoadEventsExecuted << '\n';
        std::cout << "  onload_global_events=" << m_selectedMap->eventRuntimeState->globalOnLoadEventsExecuted << '\n';
        std::cout << "  onload_facet_overrides=" << m_selectedMap->eventRuntimeState->facetSetMasks.size() << '\n';
        std::cout << "  onload_mechanisms=" << m_selectedMap->eventRuntimeState->mechanisms.size() << '\n';
        std::cout << "  onload_texture_overrides=" << m_selectedMap->eventRuntimeState->textureOverrides.size() << '\n';
        std::cout << "  onload_light_overrides=" << m_selectedMap->eventRuntimeState->indoorLightsEnabled.size() << '\n';
        std::cout << "  onload_npc_topic_overrides="
                  << m_selectedMap->eventRuntimeState->npcTopicOverrides.size() << '\n';
        std::cout << "  onload_messages=" << m_selectedMap->eventRuntimeState->messages.size() << '\n';

        for (const std::string &message : m_selectedMap->eventRuntimeState->messages)
        {
            std::cout << "    message=" << message << '\n';
        }
    }

    if (m_selectedMap->outdoorMapData)
    {
        const OutdoorMapData &outdoorMapData = *m_selectedMap->outdoorMapData;
        size_t outdoorBModelVertexCount = 0;
        size_t outdoorBModelFaceCount = 0;

        for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
        {
            outdoorBModelVertexCount += bmodel.vertices.size();
            outdoorBModelFaceCount += bmodel.faces.size();
        }

        std::cout << "Outdoor terrain:\n";
        std::cout << "  version=" << outdoorMapData.version << '\n';
        std::cout << "  terrain=" << OutdoorMapData::TerrainWidth
                  << "x" << OutdoorMapData::TerrainHeight << '\n';
        std::cout << "  tile_size=" << OutdoorMapData::TerrainTileSize << '\n';
        std::cout << "  height_range_samples=" << outdoorMapData.minHeightSample
                  << ".." << outdoorMapData.maxHeightSample << '\n';
        std::cout << "  height_range_world=" << (outdoorMapData.minHeightSample * OutdoorMapData::TerrainHeightScale)
                  << ".." << (outdoorMapData.maxHeightSample * OutdoorMapData::TerrainHeightScale) << '\n';
        std::cout << "  unique_tiles=" << outdoorMapData.uniqueTileCount << '\n';
        std::cout << "  terrain_normals=" << outdoorMapData.terrainNormalCount << '\n';
        std::cout << "  bmodels=" << outdoorMapData.bmodelCount << '\n';
        std::cout << "  bmodel_vertices=" << outdoorBModelVertexCount << '\n';
        std::cout << "  bmodel_faces=" << outdoorBModelFaceCount << '\n';
        std::cout << "  entities=" << outdoorMapData.entityCount << '\n';
        std::cout << "  id_list=" << outdoorMapData.idListCount << '\n';
        std::cout << "  spawns=" << outdoorMapData.spawnCount << '\n';

        if (m_selectedMap->outdoorMapDeltaData)
        {
            std::cout << "Outdoor map delta:\n";
            std::cout << "  respawn_count=" << m_selectedMap->outdoorMapDeltaData->locationInfo.respawnCount << '\n';
            std::cout << "  last_respawn_day=" << m_selectedMap->outdoorMapDeltaData->locationInfo.lastRespawnDay << '\n';
            std::cout << "  reputation=" << m_selectedMap->outdoorMapDeltaData->locationInfo.reputation << '\n';
            std::cout << "  alert_status=" << m_selectedMap->outdoorMapDeltaData->locationInfo.alertStatus << '\n';
            std::cout << "  sprite_objects=" << m_selectedMap->outdoorMapDeltaData->spriteObjects.size() << '\n';
            std::cout << "  chests=" << m_selectedMap->outdoorMapDeltaData->chests.size() << '\n';

            for (size_t chestIndex = 0; chestIndex < m_selectedMap->outdoorMapDeltaData->chests.size(); ++chestIndex)
            {
                const MapDeltaChest &chest = m_selectedMap->outdoorMapDeltaData->chests[chestIndex];
                const ChestEntry *pChestEntry = m_chestTable.get(chest.chestTypeId);
                std::cout << "    chest=" << chestIndex
                          << " type=" << chest.chestTypeId
                          << " flags=0x" << std::hex << chest.flags << std::dec
                          << " slots=" << countChestItemSlots(chest);

                if (pChestEntry != nullptr)
                {
                    std::cout << " name=" << pChestEntry->name
                              << " size=" << static_cast<unsigned>(pChestEntry->width)
                              << "x" << static_cast<unsigned>(pChestEntry->height)
                              << " tex=" << pChestEntry->textureName
                              << " grid=" << pChestEntry->gridOffsetX
                              << "," << pChestEntry->gridOffsetY;
                }

                std::cout << '\n';
            }
        }
    }

    if (m_selectedMap->indoorMapData)
    {
        const IndoorMapData &indoorMapData = *m_selectedMap->indoorMapData;
        std::cout << "Indoor geometry:\n";
        std::cout << "  version=" << indoorMapData.version << '\n';
        std::cout << "  vertices=" << indoorMapData.vertices.size() << '\n';
        std::cout << "  faces=" << indoorMapData.faces.size() << '\n';
        std::cout << "  sectors=" << indoorMapData.sectorCount << '\n';
        std::cout << "  sprites=" << indoorMapData.spriteCount << '\n';
        std::cout << "  entities=" << indoorMapData.entities.size() << '\n';
        std::cout << "  lights=" << indoorMapData.lightCount << '\n';
        std::cout << "  spawns=" << indoorMapData.spawns.size() << '\n';

        if (m_selectedMap->indoorMapDeltaData)
        {
            std::cout << "Indoor map delta:\n";
            std::cout << "  respawn_count=" << m_selectedMap->indoorMapDeltaData->locationInfo.respawnCount << '\n';
            std::cout << "  last_respawn_day=" << m_selectedMap->indoorMapDeltaData->locationInfo.lastRespawnDay << '\n';
            std::cout << "  reputation=" << m_selectedMap->indoorMapDeltaData->locationInfo.reputation << '\n';
            std::cout << "  alert_status=" << m_selectedMap->indoorMapDeltaData->locationInfo.alertStatus << '\n';
            std::cout << "  sprite_objects=" << m_selectedMap->indoorMapDeltaData->spriteObjects.size() << '\n';
            std::cout << "  chests=" << m_selectedMap->indoorMapDeltaData->chests.size() << '\n';
            std::cout << "  door_slots=" << m_selectedMap->indoorMapDeltaData->doorSlotCount << '\n';
            std::cout << "  doors=" << m_selectedMap->indoorMapDeltaData->doors.size() << '\n';

            for (size_t chestIndex = 0; chestIndex < m_selectedMap->indoorMapDeltaData->chests.size(); ++chestIndex)
            {
                const MapDeltaChest &chest = m_selectedMap->indoorMapDeltaData->chests[chestIndex];
                const ChestEntry *pChestEntry = m_chestTable.get(chest.chestTypeId);
                std::cout << "    chest=" << chestIndex
                          << " type=" << chest.chestTypeId
                          << " flags=0x" << std::hex << chest.flags << std::dec
                          << " slots=" << countChestItemSlots(chest);

                if (pChestEntry != nullptr)
                {
                    std::cout << " name=" << pChestEntry->name
                              << " size=" << static_cast<unsigned>(pChestEntry->width)
                              << "x" << static_cast<unsigned>(pChestEntry->height)
                              << " tex=" << pChestEntry->textureName
                              << " grid=" << pChestEntry->gridOffsetX
                              << "," << pChestEntry->gridOffsetY;
                }

                std::cout << '\n';
            }
            logIndoorDoors(indoorMapData, *m_selectedMap->indoorMapDeltaData);
        }
    }

    return true;
}
}
