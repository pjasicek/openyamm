#include "editor/document/EditorSession.h"
#include "editor/import/IndoorSourceGeometryImport.h"
#include "editor/import/ObjModelImport.h"

#include "engine/TextTable.h"
#include "engine/scripting/LuaStateOwner.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/SpriteObjectDefs.h"

#include <SDL3/SDL.h>
#include <bimg/bimg.h>
#include <bimg/decode.h>
#include <bx/allocator.h>
#include <bx/error.h>
#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sstream>
#include <unordered_map>
#include <unordered_set>

extern "C"
{
#include <lauxlib.h>
}

namespace OpenYAMM::Editor
{
namespace
{
bool isKnownBitmapTextureName(const std::vector<std::string> &bitmapTextureNames, const std::string &textureName);
void assignIndoorEntityToSector(Game::IndoorMapData &indoorGeometry, size_t entityIndex);
void removeIndoorEntityFromSectors(Game::IndoorMapData &indoorGeometry, size_t entityIndex);
void repairIndoorEntitySectorReferencesAfterDelete(Game::IndoorMapData &indoorGeometry, size_t deletedEntityIndex);

constexpr size_t ChestItemRecordSize = 36;
constexpr size_t ChestItemRecordCount = 140;
constexpr size_t ChestInventoryCellCount = 140;
constexpr int ChestMatrixColumns = 14;

int snapIndoorActorZToFloor(const Game::IndoorMapData &indoorGeometry, int x, int y, int z)
{
    Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
    const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorGeometry.vertices,
        {static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)},
        &geometryCache);
    const Game::IndoorFloorSample floor = Game::sampleIndoorFloor(
        indoorGeometry,
        indoorGeometry.vertices,
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z),
        131072.0f,
        0.0f,
        sectorId,
        nullptr,
        &geometryCache);

    if (!floor.hasFloor || floor.height <= static_cast<float>(z))
    {
        return z;
    }

    return static_cast<int>(std::lround(floor.height));
}

std::string trimCopy(const std::string &value)
{
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    }).base();

    if (begin >= end)
    {
        return {};
    }

    return std::string(begin, end);
}

std::string toUpperCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::toupper(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

void appendUniqueLowerName(std::vector<std::string> &names, std::unordered_set<std::string> &seen, const std::string &name)
{
    if (name.empty())
    {
        return;
    }

    const std::string normalizedName = toLowerCopy(name);

    if (normalizedName.empty() || normalizedName == "pending" || seen.contains(normalizedName))
    {
        return;
    }

    seen.insert(normalizedName);
    names.push_back(normalizedName);
}

void sortTextureNames(std::vector<std::string> &names)
{
    std::sort(names.begin(), names.end(), [](const std::string &left, const std::string &right)
    {
        return toLowerCopy(left) < toLowerCopy(right);
    });
}

uint64_t fnv1a64(std::string_view text)
{
    uint64_t hash = 14695981039346656037ull;

    for (unsigned char character : text)
    {
        hash ^= static_cast<uint64_t>(character);
        hash *= 1099511628211ull;
    }

    return hash;
}

std::string generatedImportedTextureName(
    const std::filesystem::path &sourcePath,
    const std::string &sourceMaterialName)
{
    const uint64_t hash = fnv1a64(sourcePath.generic_string() + "|" + sourceMaterialName);
    char buffer[11] = {};
    std::snprintf(buffer, sizeof(buffer), "g%08x", static_cast<uint32_t>(hash & 0xffffffffu));
    return buffer;
}

EditorMaterialTextureRemap *findImportedMaterialRemap(
    std::vector<EditorMaterialTextureRemap> &remaps,
    const std::string &sourceMaterialName)
{
    const std::string normalizedSourceMaterialName = toLowerCopy(trimCopy(sourceMaterialName));

    for (EditorMaterialTextureRemap &remap : remaps)
    {
        if (toLowerCopy(trimCopy(remap.sourceMaterialName)) == normalizedSourceMaterialName)
        {
            return &remap;
        }
    }

    return nullptr;
}

bool decodeImportedTextureBytesBgra(
    const std::vector<uint8_t> &textureBytes,
    std::vector<uint8_t> &pixels,
    int &width,
    int &height)
{
    pixels.clear();
    width = 0;
    height = 0;

    if (textureBytes.empty())
    {
        return false;
    }

    bx::DefaultAllocator allocator;
    bx::Error error;
    bimg::ImageContainer *pImage = bimg::imageParse(
        &allocator,
        textureBytes.data(),
        static_cast<uint32_t>(textureBytes.size()),
        bimg::TextureFormat::BGRA8,
        &error);

    if (pImage == nullptr)
    {
        return false;
    }

    bimg::ImageMip mip = {};
    const bool gotRawData =
        bimg::imageGetRawData(*pImage, 0, 0, pImage->m_data, pImage->m_size, mip)
        && mip.m_data != nullptr
        && mip.m_width > 0
        && mip.m_height > 0
        && mip.m_bpp == 32;

    if (gotRawData)
    {
        width = static_cast<int>(mip.m_width);
        height = static_cast<int>(mip.m_height);
        pixels.assign(mip.m_data, mip.m_data + mip.m_size);
    }

    bimg::imageFree(pImage);
    return gotRawData;
}

bool saveImportedTextureBitmap(
    const std::filesystem::path &outputPath,
    const std::vector<uint8_t> &pixels,
    int width,
    int height)
{
    if (width <= 0 || height <= 0 || pixels.size() < static_cast<size_t>(width * height * 4))
    {
        return false;
    }

    SDL_Surface *pSurface = SDL_CreateSurfaceFrom(
        width,
        height,
        SDL_PIXELFORMAT_BGRA32,
        const_cast<uint8_t *>(pixels.data()),
        width * 4);

    if (pSurface == nullptr)
    {
        return false;
    }

    const bool saved = SDL_SaveBMP(pSurface, outputPath.string().c_str());
    SDL_DestroySurface(pSurface);
    return saved;
}

bool materializeImportedModelTextures(
    const Engine::AssetFileSystem &assetFileSystem,
    const ImportedModel &importedModel,
    const std::filesystem::path &sourcePath,
    const std::vector<std::string> &bitmapTextureNames,
    EditorBModelImportSource &importSource,
    bool &createdTextures,
    std::string &errorMessage)
{
    createdTextures = false;
    const std::filesystem::path bitmapDirectory = assetFileSystem.getEditorDevelopmentRoot() / "Data" / "bitmaps";
    std::error_code directoryError;
    std::filesystem::create_directories(bitmapDirectory, directoryError);

    if (directoryError)
    {
        errorMessage = "could not create bitmap import directory: " + bitmapDirectory.string();
        return false;
    }

    for (const ImportedModelMaterial &material : importedModel.materials)
    {
        const std::string sourceMaterialName = trimCopy(material.name);

        if (sourceMaterialName.empty() || material.textureBytes.empty())
        {
            continue;
        }

        EditorMaterialTextureRemap *pRemap = findImportedMaterialRemap(importSource.materialRemaps, sourceMaterialName);

        if (pRemap != nullptr && isKnownBitmapTextureName(bitmapTextureNames, pRemap->textureName))
        {
            continue;
        }

        std::vector<uint8_t> pixels;
        int width = 0;
        int height = 0;

        if (!decodeImportedTextureBytesBgra(material.textureBytes, pixels, width, height))
        {
            continue;
        }

        const std::string textureName = generatedImportedTextureName(sourcePath, sourceMaterialName);
        const std::filesystem::path bitmapPath = bitmapDirectory / (textureName + ".bmp");

        if (!saveImportedTextureBitmap(bitmapPath, pixels, width, height))
        {
            errorMessage = "could not save imported bitmap texture: " + bitmapPath.string();
            return false;
        }

        if (pRemap == nullptr)
        {
            importSource.materialRemaps.push_back({sourceMaterialName, textureName});
        }
        else
        {
            pRemap->textureName = textureName;
        }

        createdTextures = true;
    }

    return true;
}

std::optional<size_t> nextAvailableIndoorDoorIndex(
    const Game::IndoorSceneData &sceneData,
    size_t geometryDoorCount)
{
    std::vector<uint8_t> usedDoorIndices(geometryDoorCount, 0);

    for (const Game::IndoorSceneDoor &door : sceneData.initialState.doors)
    {
        if (door.doorIndex < usedDoorIndices.size())
        {
            usedDoorIndices[door.doorIndex] = 1;
        }
    }

    for (size_t doorIndex = 0; doorIndex < usedDoorIndices.size(); ++doorIndex)
    {
        if (usedDoorIndices[doorIndex] == 0)
        {
            return doorIndex;
        }
    }

    return std::nullopt;
}

bool loadTextTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::vector<std::vector<std::string>> &rows)
{
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(virtualPath);

    if (!fileContents)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*fileContents);

    if (!parsedTable)
    {
        return false;
    }

    rows.clear();
    rows.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return true;
}

bool loadEditorMonsterTable(const Engine::AssetFileSystem &assetFileSystem, Game::MonsterTable &monsterTable)
{
    std::vector<std::vector<std::string>> monsterDataRows;
    std::vector<std::vector<std::string>> monsterDescriptorRows;
    std::vector<std::vector<std::string>> placedMonsterRows;
    std::vector<std::vector<std::string>> monsterRelationRows;

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/monster_data.txt", monsterDataRows))
    {
        return false;
    }

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/monster_descriptors.txt", monsterDescriptorRows))
    {
        return false;
    }

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/english/place_mon.txt", placedMonsterRows))
    {
        return false;
    }

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/monster_relation_data.txt", monsterRelationRows))
    {
        return false;
    }

    return monsterTable.loadEntriesFromRows(monsterDescriptorRows)
        && monsterTable.loadDisplayNamesFromRows(monsterDataRows)
        && monsterTable.loadStatsFromRows(monsterDataRows)
        && monsterTable.loadUniqueNamesFromRows(placedMonsterRows)
        && monsterTable.loadRelationsFromRows(monsterRelationRows);
}

Game::OutdoorSceneEnvironment outdoorMapEnvironmentForTilesetPreset(EditorOutdoorMapTilesetPreset preset)
{
    Game::OutdoorSceneEnvironment environment = {};
    environment.groundTilesetName = "grastyl";

    switch (preset)
    {
    case EditorOutdoorMapTilesetPreset::Shadowspire:
        environment.masterTile = 1;
        environment.tileSetLookupIndices = {234, 198, 270, 414};
        break;

    case EditorOutdoorMapTilesetPreset::IronsandDesert:
        environment.masterTile = 2;
        environment.tileSetLookupIndices = {162, 126, 198, 414};
        break;

    case EditorOutdoorMapTilesetPreset::Grassland:
    default:
        environment.masterTile = 0;
        environment.tileSetLookupIndices = {90, 126, 162, 414};
        break;
    }

    return environment;
}

std::optional<std::string> validateOutdoorMapId(const std::string &mapId, std::string &errorMessage)
{
    const std::string trimmedMapId = trimCopy(mapId);

    if (trimmedMapId.empty())
    {
        errorMessage = "map id is empty";
        return std::nullopt;
    }

    for (char character : trimmedMapId)
    {
        const bool allowed =
            (character >= 'a' && character <= 'z')
            || (character >= 'A' && character <= 'Z')
            || (character >= '0' && character <= '9')
            || character == '_';

        if (!allowed)
        {
            errorMessage = "map id must use only letters, digits, and underscores";
            return std::nullopt;
        }
    }

    return toLowerCopy(trimmedMapId);
}

void buildMonsterOptions(
    const std::vector<std::vector<std::string>> &monsterDataRows,
    std::vector<EditorIdLabelOption> &monsterOptions)
{
    monsterOptions.clear();

    for (const std::vector<std::string> &row : monsterDataRows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::string idText = trimCopy(row[0]);

        if (idText.empty() || !std::isdigit(static_cast<unsigned char>(idText[0])))
        {
            continue;
        }

        const std::string name = trimCopy(row[1]);

        if (name.empty())
        {
            continue;
        }

        EditorIdLabelOption option = {};
        option.id = static_cast<uint32_t>(std::strtoul(idText.c_str(), nullptr, 10));
        option.label = name + " (#" + std::to_string(option.id) + ")";
        monsterOptions.push_back(std::move(option));
    }
}

bool loadEditorChestTable(const Engine::AssetFileSystem &assetFileSystem, Game::ChestTable &chestTable)
{
    std::vector<std::vector<std::string>> chestRows;

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/chest_data.txt", chestRows))
    {
        return false;
    }

    return chestTable.loadRows(chestRows);
}

bool loadEditorDecorationTable(const Engine::AssetFileSystem &assetFileSystem, Game::DecorationTable &decorationTable)
{
    std::vector<std::vector<std::string>> decorationRows;

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/decoration_data.txt", decorationRows))
    {
        return false;
    }

    return decorationTable.loadRows(decorationRows);
}

bool loadEditorEntityBillboardSpriteFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    Game::SpriteFrameTable &spriteFrameTable)
{
    const std::optional<std::string> contents =
        assetFileSystem.readTextFile("Data/rendering/sprite_frame_data_common.yml");

    if (!contents)
    {
        return false;
    }

    std::string errorMessage;
    return spriteFrameTable.loadFromYaml(*contents, errorMessage);
}

std::optional<std::string> monsterSpriteFamilyRoot(const std::string &spriteName)
{
    if (spriteName.size() < 4 || spriteName[0] != 'm')
    {
        return std::nullopt;
    }

    if (std::isdigit(static_cast<unsigned char>(spriteName[1])) == 0
        || std::isdigit(static_cast<unsigned char>(spriteName[2])) == 0
        || std::isdigit(static_cast<unsigned char>(spriteName[3])) == 0)
    {
        return std::nullopt;
    }

    return spriteName.substr(0, 4);
}

void appendMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    const Game::MonsterEntry *pMonsterEntry)
{
    if (pMonsterEntry == nullptr)
    {
        return;
    }

    for (const std::string &spriteName : pMonsterEntry->spriteNames)
    {
        if (const std::optional<std::string> familyRoot = monsterSpriteFamilyRoot(spriteName))
        {
            families.insert(*familyRoot);
        }
    }
}

const Game::MonsterEntry *resolveMonsterEntryForActor(
    const Game::MonsterTable &monsterTable,
    const Game::MapDeltaActor &actor)
{
    const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        monsterTable.findDisplayEntryById(actor.monsterInfoId);
    const Game::MonsterEntry *pMonsterEntry = nullptr;

    if (pDisplayEntry != nullptr)
    {
        pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);
    }

    if (pMonsterEntry == nullptr)
    {
        pMonsterEntry = monsterTable.findById(actor.monsterId);
    }

    return pMonsterEntry;
}

std::optional<std::string> resolveMonsterNameForSpawn(
    const Game::MapStatsEntry &map,
    uint16_t typeId,
    uint16_t index)
{
    if (typeId != 3)
    {
        return std::nullopt;
    }

    if (index >= 1 && index <= 3)
    {
        const Game::MapEncounterInfo *pEncounter = nullptr;

        if (index == 1)
        {
            pEncounter = &map.encounter1;
        }
        else if (index == 2)
        {
            pEncounter = &map.encounter2;
        }
        else
        {
            pEncounter = &map.encounter3;
        }

        if (pEncounter != nullptr && !pEncounter->monsterName.empty())
        {
            return pEncounter->monsterName + " A";
        }
    }

    if (index >= 4 && index <= 12)
    {
        const int encounterSlot = ((index - 4) % 3) + 1;
        const char tierSuffix = static_cast<char>('A' + ((index - 4) / 3));
        const Game::MapEncounterInfo *pEncounter = nullptr;

        if (encounterSlot == 1)
        {
            pEncounter = &map.encounter1;
        }
        else if (encounterSlot == 2)
        {
            pEncounter = &map.encounter2;
        }
        else
        {
            pEncounter = &map.encounter3;
        }

        if (pEncounter != nullptr && !pEncounter->monsterName.empty())
        {
            return pEncounter->monsterName + " " + std::string(1, tierSuffix);
        }
    }

    return std::nullopt;
}

bool loadMonsterSpriteFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_set<std::string> &monsterFamilies,
    Game::SpriteFrameTable &spriteFrameTable)
{
    const std::optional<std::string> commonContents =
        assetFileSystem.readTextFile("Data/rendering/sprite_frame_data_common.yml");

    if (!commonContents)
    {
        return false;
    }

    std::string errorMessage;

    if (!spriteFrameTable.loadFromYaml(*commonContents, errorMessage))
    {
        return false;
    }

    std::vector<std::string> sortedFamilies(monsterFamilies.begin(), monsterFamilies.end());
    std::sort(sortedFamilies.begin(), sortedFamilies.end());

    for (const std::string &familyRoot : sortedFamilies)
    {
        const std::optional<std::string> familyContents =
            assetFileSystem.readTextFile("Data/rendering/sprite_frames/monsters/" + familyRoot + ".yml");

        if (!familyContents)
        {
            return false;
        }

        if (!spriteFrameTable.loadFromYaml(*familyContents, errorMessage, true))
        {
            return false;
        }
    }

    return true;
}

bool loadEditorMapStats(const Engine::AssetFileSystem &assetFileSystem, Game::MapStats &mapStats)
{
    std::vector<std::vector<std::string>> mapRows;

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/map_stats.txt", mapRows))
    {
        return false;
    }

    if (!mapStats.loadFromRows(mapRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> navigationRows;

    if (loadTextTableRows(assetFileSystem, "Data/data_tables/map_navigation.txt", navigationRows))
    {
        if (!mapStats.applyOutdoorNavigationRows(navigationRows))
        {
            return false;
        }
    }

    return true;
}

void buildChestOptions(
    const std::vector<std::vector<std::string>> &chestRows,
    std::vector<EditorIdLabelOption> &chestOptions)
{
    chestOptions.clear();

    for (const std::vector<std::string> &row : chestRows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::string idText = trimCopy(row[0]);

        if (idText.empty() || !std::isdigit(static_cast<unsigned char>(idText[0])))
        {
            continue;
        }

        const std::string name = trimCopy(row[1]);
        EditorIdLabelOption option = {};
        option.id = static_cast<uint32_t>(std::strtoul(idText.c_str(), nullptr, 10));
        option.label = (name.empty() ? "Chest" : name) + " (#" + std::to_string(option.id) + ")";
        chestOptions.push_back(std::move(option));
    }
}

void buildBitmapTextureNames(const Engine::AssetFileSystem &assetFileSystem, std::vector<std::string> &textureNames)
{
    textureNames.clear();
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/bitmaps");

    for (const std::string &entry : entries)
    {
        const std::string lowerEntry = toLowerCopy(entry);

        if (!lowerEntry.ends_with(".bmp"))
        {
            continue;
        }

        const std::filesystem::path path(entry);
        const std::string stem = path.stem().string();

        if (!stem.empty())
        {
            textureNames.push_back(stem);
        }
    }

    std::sort(textureNames.begin(), textureNames.end(), [](const std::string &left, const std::string &right)
    {
        return toLowerCopy(left) < toLowerCopy(right);
    });
    textureNames.erase(
        std::unique(textureNames.begin(), textureNames.end(), [](const std::string &left, const std::string &right)
        {
            return toLowerCopy(left) == toLowerCopy(right);
        }),
        textureNames.end());
}

bool loadEditorObjectTable(const Engine::AssetFileSystem &assetFileSystem, Game::ObjectTable &objectTable)
{
    std::vector<std::vector<std::string>> objectRows;

    if (!loadTextTableRows(assetFileSystem, "Data/data_tables/object_list.txt", objectRows))
    {
        return false;
    }

    return objectTable.loadRows(objectRows);
}

void buildObjectOptions(
    const std::vector<std::vector<std::string>> &objectRows,
    std::vector<EditorIdLabelOption> &objectOptions)
{
    objectOptions.clear();
    uint32_t descriptionId = 0;

    for (const std::vector<std::string> &row : objectRows)
    {
        if (row.empty())
        {
            continue;
        }

        const std::string name = trimCopy(row[0]);

        if (!name.empty() && name[0] == '/')
        {
            continue;
        }

        if (row.size() < 13)
        {
            continue;
        }

        EditorIdLabelOption option = {};
        option.id = descriptionId++;
        option.label = name.empty() ? "Object" : name;
        option.label += " (#" + std::to_string(option.id) + ")";
        objectOptions.push_back(std::move(option));
    }
}

void buildDecorationOptions(
    const std::vector<std::vector<std::string>> &decorationRows,
    std::vector<EditorIdLabelOption> &decorationOptions)
{
    decorationOptions.clear();

    for (const std::vector<std::string> &row : decorationRows)
    {
        if (row.empty())
        {
            continue;
        }

        const std::string decorationNumber = trimCopy(row[0]);

        if (decorationNumber.empty()
            || !std::all_of(decorationNumber.begin(), decorationNumber.end(), [](unsigned char character)
            {
                return std::isdigit(character) != 0;
            }))
        {
            continue;
        }

        const int rawId = std::stoi(decorationNumber) - 1;

        if (rawId < 0)
        {
            continue;
        }

        const std::string internalName = row.size() > 1 ? trimCopy(row[1]) : std::string();
        const std::string hint = row.size() > 2 ? trimCopy(row[2]) : std::string();

        EditorIdLabelOption option = {};
        option.id = static_cast<uint32_t>(rawId);
        option.label = internalName.empty() ? "Decoration" : internalName;

        if (!hint.empty())
        {
            option.label += " - " + hint;
        }

        option.label += " (#" + std::to_string(option.id) + ")";
        decorationOptions.push_back(std::move(option));
    }
}

void buildEditorItemNames(
    const std::vector<std::vector<std::string>> &itemRows,
    std::unordered_map<uint32_t, std::string> &itemNames,
    std::vector<EditorIdLabelOption> &itemOptions)
{
    itemNames.clear();
    itemOptions.clear();

    for (const std::vector<std::string> &row : itemRows)
    {
        if (row.size() <= 2)
        {
            continue;
        }

        const std::string idText = trimCopy(row[0]);

        if (idText.empty() || !std::isdigit(static_cast<unsigned char>(idText[0])))
        {
            continue;
        }

        const uint32_t itemId = static_cast<uint32_t>(std::strtoul(idText.c_str(), nullptr, 10));
        const std::string name = trimCopy(row[2]);

        if (itemId == 0 || name.empty())
        {
            continue;
        }

        itemNames[itemId] = name;

        EditorIdLabelOption option = {};
        option.id = itemId;
        option.label = name + " (#" + std::to_string(itemId) + ")";
        itemOptions.push_back(std::move(option));
    }
}

std::vector<std::string> buildScriptPathCandidates(const std::string &baseName)
{
    if (baseName.empty())
    {
        return {};
    }

    std::vector<std::string> nameCandidates;
    const std::string lowerName = toLowerCopy(baseName);
    const std::string upperName = toUpperCopy(baseName);
    std::string titleName = lowerName;

    if (!titleName.empty())
    {
        titleName[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(titleName[0])));
    }

    nameCandidates.push_back(baseName);

    if (std::find(nameCandidates.begin(), nameCandidates.end(), lowerName) == nameCandidates.end())
    {
        nameCandidates.push_back(lowerName);
    }

    if (std::find(nameCandidates.begin(), nameCandidates.end(), upperName) == nameCandidates.end())
    {
        nameCandidates.push_back(upperName);
    }

    if (std::find(nameCandidates.begin(), nameCandidates.end(), titleName) == nameCandidates.end())
    {
        nameCandidates.push_back(titleName);
    }

    if (lowerName.rfind("out", 0) == 0 && lowerName.size() > 3)
    {
        const std::string outName = "Out" + lowerName.substr(3);

        if (std::find(nameCandidates.begin(), nameCandidates.end(), outName) == nameCandidates.end())
        {
            nameCandidates.push_back(outName);
        }
    }
    else if (lowerName.rfind("elem", 0) == 0 && lowerName.size() > 4)
    {
        std::string elemName = "Elem";
        elemName += static_cast<char>(std::toupper(static_cast<unsigned char>(lowerName[4])));

        if (std::find(nameCandidates.begin(), nameCandidates.end(), elemName) == nameCandidates.end())
        {
            nameCandidates.push_back(elemName);
        }
    }
    else if (lowerName == "pbp")
    {
        nameCandidates.push_back("PbP");
    }
    else if (lowerName.size() > 1 && lowerName[0] == 'd')
    {
        std::string dungeonName = lowerName;
        dungeonName[0] = 'D';

        if (std::find(nameCandidates.begin(), nameCandidates.end(), dungeonName) == nameCandidates.end())
        {
            nameCandidates.push_back(dungeonName);
        }
    }

    std::vector<std::string> pathCandidates;

    for (const std::string &nameCandidate : nameCandidates)
    {
        pathCandidates.push_back("Data/EnglishT/" + nameCandidate + ".EVT");
        pathCandidates.push_back("Data/EnglishT/" + nameCandidate + ".evt");
    }

    return pathCandidates;
}

std::optional<std::vector<uint8_t>> readFirstExistingBinary(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &virtualPaths)
{
    for (const std::string &virtualPath : virtualPaths)
    {
        const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(virtualPath);

        if (bytes)
        {
            return bytes;
        }
    }

    return std::nullopt;
}

std::optional<std::string> readFirstExistingText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &virtualPaths,
    std::string &resolvedPath)
{
    for (const std::string &virtualPath : virtualPaths)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(virtualPath);

        if (text)
        {
            resolvedPath = virtualPath;
            return text;
        }
    }

    return std::nullopt;
}

bool readPhysicalTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream stream(path, std::ios::binary);

    if (!stream.is_open())
    {
        return false;
    }

    text.assign(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
    return true;
}

std::optional<std::string> readFirstExistingPhysicalText(
    const std::vector<std::filesystem::path> &paths,
    std::string &resolvedPath)
{
    for (const std::filesystem::path &path : paths)
    {
        if (path.empty() || !std::filesystem::exists(path) || !std::filesystem::is_regular_file(path))
        {
            continue;
        }

        std::string text;

        if (!readPhysicalTextFile(path, text))
        {
            continue;
        }

        resolvedPath = path.lexically_normal().generic_string();
        return text;
    }

    return std::nullopt;
}

std::vector<std::string> buildLuaScriptPathCandidates(const std::string &baseName, bool globalScope)
{
    if (globalScope)
    {
        return {
            "Data/scripts/Global.lua",
            "Data/scripts/global.lua",
        };
    }

    const std::string lowerBaseName = toLowerCopy(baseName);
    return {
        "Data/scripts/maps/" + lowerBaseName + ".lua",
        "Data/scripts/maps/" + baseName + ".lua",
    };
}

std::vector<std::filesystem::path> buildLuaScriptSidecarPathCandidates(
    const std::string &baseName,
    const std::filesystem::path &geometryPath,
    const std::filesystem::path &scenePath)
{
    const std::string lowerBaseName = toLowerCopy(baseName);
    std::vector<std::filesystem::path> candidates;

    const auto appendDirectoryCandidates =
        [&](const std::filesystem::path &directory)
    {
        if (directory.empty())
        {
            return;
        }

        const std::filesystem::path normalizedDirectory = directory.lexically_normal();
        const std::filesystem::path lowerCandidate = normalizedDirectory / (lowerBaseName + ".lua");
        candidates.push_back(lowerCandidate);

        const std::filesystem::path exactCandidate = normalizedDirectory / (baseName + ".lua");

        if (exactCandidate != lowerCandidate)
        {
            candidates.push_back(exactCandidate);
        }
    };

    appendDirectoryCandidates(geometryPath.parent_path());
    appendDirectoryCandidates(scenePath.parent_path());
    appendDirectoryCandidates(std::filesystem::current_path());
    return candidates;
}

std::vector<std::string> buildLuaSupportPathCandidates()
{
    return {
        "Data/scripts/common/event_support.lua",
        "Data/scripts/common/EventSupport.lua",
    };
}

std::string prependLuaSupport(
    const std::optional<std::string> &supportSource,
    const std::optional<std::string> &scriptSource)
{
    if (!scriptSource)
    {
        return {};
    }

    if (!supportSource || supportSource->empty())
    {
        return *scriptSource;
    }

    return *supportSource + "\n\n" + *scriptSource;
}

constexpr char LuaScopeMap[] = "map";
constexpr char LuaScopeGlobal[] = "global";
constexpr char LuaScopeCanShowTopic[] = "CanShowTopic";
constexpr uint32_t LuaPreviewRegistryKey = 0x45565052u;

struct EditorPreviewLuaState
{
    const Game::MapDeltaData *pMapDeltaData = nullptr;
    std::array<uint8_t, 75> *pMapVars = nullptr;
    std::array<uint8_t, 125> *pDecorVars = nullptr;
    std::unordered_map<uint32_t, int32_t> *pVariables = nullptr;
    std::unordered_map<uint32_t, EditorPreviewMechanismState> *pMechanisms = nullptr;
    std::vector<std::string> *pMessages = nullptr;
    std::vector<std::string> *pStatusMessages = nullptr;
    std::vector<std::string> *pActivityMessages = nullptr;
    std::optional<std::string> pendingMessageText;
    uint16_t currentEventId = 0;
};

EditorPreviewLuaState *previewLuaStateFromLua(lua_State *pLuaState)
{
    lua_pushlightuserdata(pLuaState, const_cast<uint32_t *>(&LuaPreviewRegistryKey));
    lua_rawget(pLuaState, LUA_REGISTRYINDEX);
    EditorPreviewLuaState *pState = static_cast<EditorPreviewLuaState *>(lua_touserdata(pLuaState, -1));
    lua_pop(pLuaState, 1);
    return pState;
}

void appendPreviewActivity(lua_State *pLuaState, const std::string &message)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr && pState->pActivityMessages != nullptr)
    {
        pState->pActivityMessages->push_back(message);
    }
}

int32_t previewVariableValue(const EditorPreviewLuaState &state, uint32_t selector)
{
    if (selector >= static_cast<uint32_t>(Game::EvtVariable::MapPersistentVariableBegin)
        && selector <= static_cast<uint32_t>(Game::EvtVariable::MapPersistentVariableEnd)
        && state.pMapVars != nullptr)
    {
        return (*state.pMapVars)[selector - static_cast<uint32_t>(Game::EvtVariable::MapPersistentVariableBegin)];
    }

    if (selector >= static_cast<uint32_t>(Game::EvtVariable::MapPersistentDecorVariableBegin)
        && selector <= static_cast<uint32_t>(Game::EvtVariable::MapPersistentDecorVariableEnd)
        && state.pDecorVars != nullptr)
    {
        return (*state.pDecorVars)[selector - static_cast<uint32_t>(Game::EvtVariable::MapPersistentDecorVariableBegin)];
    }

    if (state.pVariables == nullptr)
    {
        return 0;
    }

    const auto iterator = state.pVariables->find(selector);
    return iterator != state.pVariables->end() ? iterator->second : 0;
}

void setPreviewVariableValue(EditorPreviewLuaState &state, uint32_t selector, int32_t value)
{
    if (selector >= static_cast<uint32_t>(Game::EvtVariable::MapPersistentVariableBegin)
        && selector <= static_cast<uint32_t>(Game::EvtVariable::MapPersistentVariableEnd)
        && state.pMapVars != nullptr)
    {
        const size_t index = selector - static_cast<uint32_t>(Game::EvtVariable::MapPersistentVariableBegin);
        (*state.pMapVars)[index] = std::clamp(value, 0, 255);
        return;
    }

    if (selector >= static_cast<uint32_t>(Game::EvtVariable::MapPersistentDecorVariableBegin)
        && selector <= static_cast<uint32_t>(Game::EvtVariable::MapPersistentDecorVariableEnd)
        && state.pDecorVars != nullptr)
    {
        const size_t index = selector - static_cast<uint32_t>(Game::EvtVariable::MapPersistentDecorVariableBegin);
        (*state.pDecorVars)[index] = std::clamp(value, 0, 255);
        return;
    }

    if (state.pVariables != nullptr)
    {
        (*state.pVariables)[selector] = value;
    }
}

float previewMechanismDistanceForState(const Game::MapDeltaDoor &door, uint16_t state, float timeSinceTriggeredMs)
{
    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Open))
    {
        return 0.0f;
    }

    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Closed) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
    {
        return std::min(
            timeSinceTriggeredMs * static_cast<float>(door.closeSpeed) / 1000.0f,
            static_cast<float>(door.moveLength));
    }

    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
    {
        return std::max(
            0.0f,
            static_cast<float>(door.moveLength)
                - timeSinceTriggeredMs * static_cast<float>(door.openSpeed) / 1000.0f);
    }

    return 0.0f;
}

EditorPreviewMechanismState buildPreviewMechanismState(const Game::MapDeltaDoor &door)
{
    EditorPreviewMechanismState state = {};
    state.state = door.state;
    state.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    state.currentDistance = previewMechanismDistanceForState(door, state.state, state.timeSinceTriggeredMs);
    state.isMoving =
        state.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening)
        || state.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing);
    return state;
}

const Game::MapDeltaDoor *findPreviewDoorById(const Game::MapDeltaData &mapDeltaData, uint32_t mechanismId)
{
    for (const Game::MapDeltaDoor &door : mapDeltaData.doors)
    {
        if (door.doorId == mechanismId)
        {
            return &door;
        }
    }

    return nullptr;
}

void applyPreviewMechanismAction(
    EditorPreviewMechanismState &state,
    const Game::MapDeltaDoor *pDoor,
    Game::EvtMechanismAction action)
{
    if (action == Game::EvtMechanismAction::Trigger)
    {
        if (state.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening)
            || state.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
        {
            return;
        }

        state.timeSinceTriggeredMs = 0.0f;
        state.state = state.state == static_cast<uint16_t>(Game::EvtMechanismState::Closed)
            ? static_cast<uint16_t>(Game::EvtMechanismState::Opening)
            : static_cast<uint16_t>(Game::EvtMechanismState::Closing);
        state.isMoving = true;
        return;
    }

    if (action == Game::EvtMechanismAction::Open)
    {
        if (state.state == static_cast<uint16_t>(Game::EvtMechanismState::Open)
            || state.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
        {
            return;
        }

        if (pDoor != nullptr && state.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
        {
            const float openDistance = std::max(0.0f, static_cast<float>(pDoor->moveLength) - state.currentDistance);
            state.timeSinceTriggeredMs =
                openDistance * 1000.0f / std::max(1.0f, static_cast<float>(pDoor->openSpeed));
        }
        else
        {
            state.timeSinceTriggeredMs = 0.0f;
        }

        state.state = static_cast<uint16_t>(Game::EvtMechanismState::Opening);
        state.isMoving = true;
        state.currentDistance = pDoor != nullptr
            ? previewMechanismDistanceForState(*pDoor, state.state, state.timeSinceTriggeredMs)
            : 0.0f;
        return;
    }

    if (action == Game::EvtMechanismAction::Close)
    {
        if (state.state == static_cast<uint16_t>(Game::EvtMechanismState::Closed)
            || state.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
        {
            return;
        }

        if (pDoor != nullptr && state.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
        {
            state.timeSinceTriggeredMs =
                state.currentDistance * 1000.0f / std::max(1.0f, static_cast<float>(pDoor->closeSpeed));
        }
        else
        {
            state.timeSinceTriggeredMs = 0.0f;
        }

        state.state = static_cast<uint16_t>(Game::EvtMechanismState::Closing);
        state.isMoving = true;
        state.currentDistance = pDoor != nullptr
            ? previewMechanismDistanceForState(*pDoor, state.state, state.timeSinceTriggeredMs)
            : state.currentDistance;
    }
}

void registerPreviewLuaFunction(lua_State *pLuaState, const char *pName, lua_CFunction function)
{
    lua_pushcfunction(pLuaState, function);
    lua_setfield(pLuaState, -2, pName);
}

void registerPreviewLuaNoOp(lua_State *pLuaState, const char *pName, lua_CFunction function)
{
    lua_pushstring(pLuaState, pName);
    lua_pushcclosure(pLuaState, function, 1);
    lua_setfield(pLuaState, -2, pName);
}

int luaPreviewBeginEvent(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr)
    {
        pState->currentEventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
        pState->pendingMessageText.reset();
    }

    return 0;
}

int luaPreviewBeginCanShowTopic(lua_State *pLuaState)
{
    (void)pLuaState;
    return 0;
}

int luaPreviewRandomJump(lua_State *pLuaState)
{
    luaL_checkinteger(pLuaState, 1);
    luaL_checkinteger(pLuaState, 2);
    luaL_checktype(pLuaState, 3, LUA_TTABLE);
    const size_t count = lua_rawlen(pLuaState, 3);

    for (size_t index = 1; index <= count; ++index)
    {
        lua_geti(pLuaState, 3, static_cast<lua_Integer>(index));

        if (lua_isinteger(pLuaState, -1))
        {
            const lua_Integer value = lua_tointeger(pLuaState, -1);
            lua_pop(pLuaState, 1);
            lua_pushinteger(pLuaState, value);
            return 1;
        }

        lua_pop(pLuaState, 1);
    }

    lua_pushinteger(pLuaState, 0);
    return 1;
}

int luaPreviewCompare(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);
    const uint32_t selector = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t compareValue = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
    const int32_t currentValue = pState != nullptr ? previewVariableValue(*pState, selector) : 0;
    lua_pushboolean(pLuaState, currentValue >= compareValue);
    return 1;
}

int luaPreviewAdd(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr)
    {
        const uint32_t selector = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
        const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
        setPreviewVariableValue(*pState, selector, previewVariableValue(*pState, selector) + value);
    }

    return 0;
}

int luaPreviewSubtract(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr)
    {
        const uint32_t selector = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
        const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
        setPreviewVariableValue(*pState, selector, previewVariableValue(*pState, selector) - value);
    }

    return 0;
}

int luaPreviewSet(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr)
    {
        const uint32_t selector = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
        const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
        setPreviewVariableValue(*pState, selector, value);
    }

    return 0;
}

int luaPreviewSetDoorState(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState == nullptr || pState->pMechanisms == nullptr || pState->pMapDeltaData == nullptr)
    {
        return 0;
    }

    const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t actionValue = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const Game::MapDeltaDoor *pDoor = findPreviewDoorById(*pState->pMapDeltaData, mechanismId);
    EditorPreviewMechanismState &mechanism = (*pState->pMechanisms)[mechanismId];

    if (mechanism.state == 0 && mechanism.currentDistance == 0.0f && !mechanism.isMoving && pDoor != nullptr)
    {
        mechanism = buildPreviewMechanismState(*pDoor);
    }

    Game::EvtMechanismAction action = Game::EvtMechanismAction::Open;

    if (actionValue == static_cast<uint32_t>(Game::EvtMechanismAction::Close))
    {
        action = Game::EvtMechanismAction::Close;
    }
    else if (actionValue == static_cast<uint32_t>(Game::EvtMechanismAction::Trigger))
    {
        action = Game::EvtMechanismAction::Trigger;
    }

    applyPreviewMechanismAction(mechanism, pDoor, action);
    return 0;
}

int luaPreviewStopDoor(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr && pState->pMechanisms != nullptr)
    {
        const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
        (*pState->pMechanisms)[mechanismId].isMoving = false;
    }

    return 0;
}

int luaPreviewStatusText(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr && pState->pStatusMessages != nullptr)
    {
        pState->pStatusMessages->push_back(luaL_checkstring(pLuaState, 1));
    }

    return 0;
}

int luaPreviewSetMessage(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState != nullptr)
    {
        pState->pendingMessageText = luaL_checkstring(pLuaState, 1);
    }

    return 0;
}

int luaPreviewSimpleMessage(lua_State *pLuaState)
{
    EditorPreviewLuaState *pState = previewLuaStateFromLua(pLuaState);

    if (pState == nullptr || pState->pMessages == nullptr)
    {
        return 0;
    }

    if (lua_gettop(pLuaState) >= 1 && lua_type(pLuaState, 1) == LUA_TSTRING)
    {
        pState->pMessages->push_back(lua_tostring(pLuaState, 1));
        return 0;
    }

    if (pState->pendingMessageText)
    {
        pState->pMessages->push_back(*pState->pendingMessageText);
    }

    return 0;
}

int luaPreviewNoOp(lua_State *pLuaState)
{
    const char *pName = lua_tostring(pLuaState, lua_upvalueindex(1));

    if (pName != nullptr)
    {
        appendPreviewActivity(pLuaState, std::string("Ignored evt.") + pName);
    }

    return 0;
}

int luaPreviewFalse(lua_State *pLuaState)
{
    const char *pName = lua_tostring(pLuaState, lua_upvalueindex(1));

    if (pName != nullptr)
    {
        appendPreviewActivity(pLuaState, std::string("Ignored evt.") + pName);
    }

    lua_pushboolean(pLuaState, 0);
    return 1;
}

void registerPreviewEventBindings(lua_State *pLuaState)
{
    lua_newtable(pLuaState);

    registerPreviewLuaFunction(pLuaState, "_BeginEvent", luaPreviewBeginEvent);
    registerPreviewLuaFunction(pLuaState, "_BeginCanShowTopic", luaPreviewBeginCanShowTopic);
    registerPreviewLuaFunction(pLuaState, "_RandomJump", luaPreviewRandomJump);
    registerPreviewLuaFunction(pLuaState, "Cmp", luaPreviewCompare);
    registerPreviewLuaFunction(pLuaState, "Add", luaPreviewAdd);
    registerPreviewLuaFunction(pLuaState, "Subtract", luaPreviewSubtract);
    registerPreviewLuaFunction(pLuaState, "Set", luaPreviewSet);
    registerPreviewLuaFunction(pLuaState, "SetDoorState", luaPreviewSetDoorState);
    registerPreviewLuaFunction(pLuaState, "StopDoor", luaPreviewStopDoor);
    registerPreviewLuaFunction(pLuaState, "StatusText", luaPreviewStatusText);
    registerPreviewLuaFunction(pLuaState, "SetMessage", luaPreviewSetMessage);
    registerPreviewLuaFunction(pLuaState, "SimpleMessage", luaPreviewSimpleMessage);

    const std::array<const char *, 31> noOpFunctions = {{
        "_InputString", "_PressAnyKey", "_SpecialJump", "ForPlayer", "EnterHouse", "PlaySound", "MoveToMap",
        "OpenChest", "FaceExpression", "DamagePlayer", "SetSnow", "SetRain", "SetTexture", "SetTextureOutdoors",
        "ShowMovie", "SetSprite", "SummonMonsters", "CastSpell", "SpeakNPC", "SetFacetBit",
        "SetFacetBitOutdoors", "SetMonsterBit", "Question", "SetLight", "SummonItem", "SummonObject",
        "SetNPCTopic", "MoveNPC", "GiveItem", "ChangeEvent", "RefundChestArtifacts"
    }};

    for (const char *pFunctionName : noOpFunctions)
    {
        registerPreviewLuaNoOp(pLuaState, pFunctionName, luaPreviewNoOp);
    }

    const std::array<const char *, 16> falseFunctions = {{
        "_IsNpcInParty", "CheckSkill", "CheckMonstersKilled", "CheckItemsCount", "Jump",
        "IsTotalBountyInRange", "CanPlayerAct", "SetNPCGroupNews", "SetMonsterGroup", "SetNPCItem",
        "SetNPCGreeting", "ChangeGroupToGroup", "ChangeGroupAlly", "SetMonGroupBit", "SetChestBit",
        "SetMonsterItem"
    }};

    for (const char *pFunctionName : falseFunctions)
    {
        registerPreviewLuaNoOp(pLuaState, pFunctionName, luaPreviewFalse);
    }

    registerPreviewLuaNoOp(pLuaState, "FaceAnimation", luaPreviewNoOp);

    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeGlobal);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeMap);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeCanShowTopic);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "hint");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "house");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "str");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "VarNum");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "Players");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "const");

    lua_newtable(pLuaState);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeGlobal);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeMap);
    lua_setfield(pLuaState, -2, "meta");

    lua_setglobal(pLuaState, "evt");
}

bool loadPreviewLuaProgram(
    const std::optional<Game::ScriptedEventProgram> &program,
    const std::string &fallbackChunkName,
    const Engine::LuaStateOwner &lua,
    std::string &errorMessage)
{
    if (!program || !program->luaSourceText())
    {
        return true;
    }

    std::optional<std::string> runtimeError;
    const std::string chunkName = program->luaSourceName().value_or(fallbackChunkName);

    if (!lua.runChunk(*program->luaSourceText(), chunkName, runtimeError))
    {
        errorMessage = runtimeError.value_or("failed to execute preview lua chunk");
        return false;
    }

    return true;
}

bool invokePreviewEventHandler(
    const Engine::LuaStateOwner &lua,
    const char *pScopeName,
    uint16_t eventId,
    std::string &errorMessage)
{
    lua_State *pLuaState = lua.state();
    lua_getglobal(pLuaState, "evt");

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 1);
        errorMessage = "preview lua did not create evt table";
        return false;
    }

    lua_getfield(pLuaState, -1, pScopeName);

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 2);
        errorMessage = std::string("preview lua is missing evt.") + pScopeName;
        return false;
    }

    lua_geti(pLuaState, -1, eventId);

    if (!lua_isfunction(pLuaState, -1))
    {
        lua_pop(pLuaState, 3);
        errorMessage = std::string("preview lua is missing evt.") + pScopeName + "[" + std::to_string(eventId) + "]";
        return false;
    }

    lua_remove(pLuaState, -2);
    lua_remove(pLuaState, -2);

    std::optional<std::string> runtimeError;

    if (!lua.call(0, 0, runtimeError))
    {
        errorMessage = runtimeError.value_or("failed to execute preview event");
        return false;
    }

    return true;
}

bool executePreviewEventScripts(
    const std::optional<Game::ScriptedEventProgram> &localProgram,
    const std::optional<Game::ScriptedEventProgram> &globalProgram,
    EditorPreviewLuaState &state,
    std::string &errorMessage,
    std::optional<uint16_t> eventId = std::nullopt)
{
    Engine::LuaStateOwner lua = {};

    if (!lua.isValid())
    {
        errorMessage = "lua state unavailable";
        return false;
    }

    lua.openApprovedLibraries();
    registerPreviewEventBindings(lua.state());
    lua_pushlightuserdata(lua.state(), const_cast<uint32_t *>(&LuaPreviewRegistryKey));
    lua_pushlightuserdata(lua.state(), &state);
    lua_rawset(lua.state(), LUA_REGISTRYINDEX);

    if (!loadPreviewLuaProgram(globalProgram, "@Global.lua", lua, errorMessage))
    {
        return false;
    }

    if (!loadPreviewLuaProgram(localProgram, "@Local.lua", lua, errorMessage))
    {
        return false;
    }

    if (!eventId.has_value())
    {
        if (globalProgram)
        {
            for (uint16_t onLoadEventId : globalProgram->onLoadEventIds())
            {
                std::string onLoadError;

                if (!invokePreviewEventHandler(lua, LuaScopeGlobal, onLoadEventId, onLoadError))
                {
                    appendPreviewActivity(lua.state(), "Ignored global onLoad " + std::to_string(onLoadEventId) + ": "
                        + onLoadError);
                }
            }
        }

        if (localProgram)
        {
            for (uint16_t onLoadEventId : localProgram->onLoadEventIds())
            {
                std::string onLoadError;

                if (!invokePreviewEventHandler(lua, LuaScopeMap, onLoadEventId, onLoadError))
                {
                    appendPreviewActivity(lua.state(), "Ignored local onLoad " + std::to_string(onLoadEventId) + ": "
                        + onLoadError);
                }
            }
        }

        return true;
    }

    const bool useLocalScope = localProgram && localProgram->hasEvent(*eventId);
    const bool useGlobalScope = globalProgram && globalProgram->hasEvent(*eventId);

    if (!useLocalScope && !useGlobalScope)
    {
        errorMessage = "preview lua did not resolve event " + std::to_string(*eventId);
        return false;
    }

    return invokePreviewEventHandler(lua, useLocalScope ? LuaScopeMap : LuaScopeGlobal, *eventId, errorMessage);
}

std::vector<uint32_t> getOpenedChestIds(
    uint16_t eventId,
    const std::optional<Game::ScriptedEventProgram> &localScriptedEventProgram,
    const std::optional<Game::ScriptedEventProgram> &globalScriptedEventProgram,
    const std::optional<Game::EvtProgram> &localEvtProgram,
    const std::optional<Game::EvtProgram> &globalEvtProgram)
{
    if (eventId == 0)
    {
        return {};
    }

    if (localScriptedEventProgram && localScriptedEventProgram->hasEvent(eventId))
    {
        return localScriptedEventProgram->getOpenedChestIds(eventId);
    }

    if (globalScriptedEventProgram && globalScriptedEventProgram->hasEvent(eventId))
    {
        return globalScriptedEventProgram->getOpenedChestIds(eventId);
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

bool hasResolvedEvent(
    uint16_t eventId,
    const std::optional<Game::ScriptedEventProgram> &localScriptedEventProgram,
    const std::optional<Game::ScriptedEventProgram> &globalScriptedEventProgram,
    const std::optional<Game::EvtProgram> &localEvtProgram,
    const std::optional<Game::EvtProgram> &globalEvtProgram)
{
    if (eventId == 0)
    {
        return true;
    }

    return (localScriptedEventProgram && localScriptedEventProgram->hasEvent(eventId))
        || (globalScriptedEventProgram && globalScriptedEventProgram->hasEvent(eventId))
        || (localEvtProgram && localEvtProgram->hasEvent(eventId))
        || (globalEvtProgram && globalEvtProgram->hasEvent(eventId));
}

std::optional<std::string> summarizeResolvedEvent(
    uint16_t eventId,
    const std::optional<Game::ScriptedEventProgram> &localScriptedEventProgram,
    const std::optional<Game::ScriptedEventProgram> &globalScriptedEventProgram,
    const std::optional<Game::EvtProgram> &localEvtProgram,
    const std::optional<Game::EvtProgram> &globalEvtProgram)
{
    if (eventId == 0)
    {
        return std::string("<none>");
    }

    const auto summarizeFromProgram = [eventId](const std::optional<Game::ScriptedEventProgram> &program)
        -> std::optional<std::string>
    {
        if (!program || !program->hasEvent(eventId))
        {
            return std::nullopt;
        }

        const std::optional<std::string> summary = program->summarizeEvent(eventId);

        if (summary && !summary->empty())
        {
            return summary;
        }

        const std::optional<std::string> hint = program->getHint(eventId);

        if (hint && !hint->empty())
        {
            return hint;
        }

        return std::string("Event #") + std::to_string(eventId);
    };

    if (const std::optional<std::string> summary = summarizeFromProgram(localScriptedEventProgram))
    {
        return *summary + " [Local]";
    }

    if (const std::optional<std::string> summary = summarizeFromProgram(globalScriptedEventProgram))
    {
        return *summary + " [Global]";
    }

    if (localEvtProgram && localEvtProgram->hasEvent(eventId))
    {
        return "Event #" + std::to_string(eventId) + " [Local EVT]";
    }

    if (globalEvtProgram && globalEvtProgram->hasEvent(eventId))
    {
        return "Event #" + std::to_string(eventId) + " [Global EVT]";
    }

    return std::nullopt;
}

bool isResolvedHintOnlyEvent(
    uint16_t eventId,
    const std::optional<Game::ScriptedEventProgram> &localScriptedEventProgram,
    const std::optional<Game::ScriptedEventProgram> &globalScriptedEventProgram)
{
    if (eventId == 0)
    {
        return false;
    }

    if (localScriptedEventProgram
        && (localScriptedEventProgram->hasEvent(eventId) || localScriptedEventProgram->isHintOnlyEvent(eventId)))
    {
        return localScriptedEventProgram->isHintOnlyEvent(eventId);
    }

    if (globalScriptedEventProgram
        && (globalScriptedEventProgram->hasEvent(eventId) || globalScriptedEventProgram->isHintOnlyEvent(eventId)))
    {
        return globalScriptedEventProgram->isHintOnlyEvent(eventId);
    }

    return false;
}

void appendScriptedEventOptions(
    const std::optional<Game::ScriptedEventProgram> &program,
    const char *pScopeLabel,
    std::vector<EditorIdLabelOption> &options,
    std::unordered_set<uint32_t> &seenEventIds)
{
    if (!program)
    {
        return;
    }

    for (uint16_t eventId : program->eventIds())
    {
        if (!seenEventIds.insert(eventId).second)
        {
            continue;
        }

        std::string label = "Event #" + std::to_string(eventId);

        if (const std::optional<std::string> summary = program->summarizeEvent(eventId); summary && !summary->empty())
        {
            label = *summary;
        }
        else if (const std::optional<std::string> hint = program->getHint(eventId); hint && !hint->empty())
        {
            label = *hint;
        }

        label += " (#" + std::to_string(eventId) + ")";
        label += " [";
        label += pScopeLabel;
        label += "]";
        options.push_back({eventId, std::move(label)});
    }
}

void appendIssue(std::vector<std::string> &issues, const std::string &issue)
{
    if (std::find(issues.begin(), issues.end(), issue) == issues.end())
    {
        issues.push_back(issue);
    }
}

void recordSummarizedIssue(size_t &count, std::string &example, const std::string &message)
{
    ++count;

    if (example.empty())
    {
        example = message;
    }
}

void appendSummarizedIssue(
    std::vector<std::string> &issues,
    size_t count,
    const std::string &summary,
    const std::string &example)
{
    if (count == 0)
    {
        return;
    }

    std::string message = std::to_string(count) + ' ' + summary;

    if (!example.empty())
    {
        message += " Example: " + example;
    }

    appendIssue(issues, message);
}

bool containsChestId(const std::vector<uint32_t> &chestIds, size_t chestIndex)
{
    return std::find(chestIds.begin(), chestIds.end(), chestIndex) != chestIds.end();
}

const Game::OutdoorSceneInteractiveFace *findInteractiveFace(
    const Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex)
        {
            return &interactiveFace;
        }
    }

    return nullptr;
}

std::string fileStemLowerCopy(const std::string &value)
{
    std::filesystem::path path(value);
    const std::string stem = path.stem().string();
    return toLowerCopy(stem.empty() ? value : stem);
}

std::string canonicalBitmapTextureName(
    const std::vector<std::string> &bitmapTextureNames,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return {};
    }

    const std::string normalizedName = fileStemLowerCopy(trimCopy(textureName));

    if (normalizedName.empty())
    {
        return {};
    }

    for (const std::string &candidate : bitmapTextureNames)
    {
        if (toLowerCopy(candidate) == normalizedName)
        {
            return candidate;
        }
    }

    return normalizedName.substr(0, std::min<size_t>(normalizedName.size(), 10));
}

std::string resolveImportedMaterialTextureName(
    const std::vector<std::string> &bitmapTextureNames,
    const EditorBModelImportSource *pImportSource,
    const std::string &materialName)
{
    const std::string resolvedDefaultTexture =
        pImportSource != nullptr
        ? canonicalBitmapTextureName(bitmapTextureNames, pImportSource->defaultTextureName)
        : std::string();

    if (materialName.empty())
    {
        return resolvedDefaultTexture;
    }

    if (pImportSource != nullptr)
    {
        const std::string normalizedMaterialName = toLowerCopy(trimCopy(materialName));

        for (const EditorMaterialTextureRemap &remap : pImportSource->materialRemaps)
        {
            if (toLowerCopy(trimCopy(remap.sourceMaterialName)) == normalizedMaterialName)
            {
                const std::string remappedTextureName =
                    canonicalBitmapTextureName(bitmapTextureNames, remap.textureName);

                if (!remappedTextureName.empty())
                {
                    return remappedTextureName;
                }
            }
        }
    }

    const std::string canonicalMaterialTextureName = canonicalBitmapTextureName(bitmapTextureNames, materialName);

    if (!canonicalMaterialTextureName.empty())
    {
        return canonicalMaterialTextureName;
    }

    return resolvedDefaultTexture;
}

bool isKnownBitmapTextureName(const std::vector<std::string> &bitmapTextureNames, const std::string &textureName)
{
    const std::string normalizedName = fileStemLowerCopy(trimCopy(textureName));

    if (normalizedName.empty())
    {
        return false;
    }

    for (const std::string &candidate : bitmapTextureNames)
    {
        if (toLowerCopy(candidate) == normalizedName)
        {
            return true;
        }
    }

    return false;
}

void assignIndoorEntityToSector(Game::IndoorMapData &indoorGeometry, size_t entityIndex)
{
    if (entityIndex >= indoorGeometry.entities.size())
    {
        return;
    }

    removeIndoorEntityFromSectors(indoorGeometry, entityIndex);

    const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
    Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
    const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorGeometry.vertices,
        {
            static_cast<float>(entity.x),
            static_cast<float>(entity.y),
            static_cast<float>(entity.z)
        },
        &geometryCache);

    if (!sectorId.has_value() || *sectorId < 0 || static_cast<size_t>(*sectorId) >= indoorGeometry.sectors.size())
    {
        return;
    }

    std::vector<uint16_t> &decorationIds = indoorGeometry.sectors[static_cast<size_t>(*sectorId)].decorationIds;
    const uint16_t clampedEntityIndex = static_cast<uint16_t>(std::min<size_t>(entityIndex, 65535));

    if (std::find(decorationIds.begin(), decorationIds.end(), clampedEntityIndex) == decorationIds.end())
    {
        decorationIds.push_back(clampedEntityIndex);
    }
}

void removeIndoorEntityFromSectors(Game::IndoorMapData &indoorGeometry, size_t entityIndex)
{
    const uint16_t clampedEntityIndex = static_cast<uint16_t>(std::min<size_t>(entityIndex, 65535));

    for (Game::IndoorSector &sector : indoorGeometry.sectors)
    {
        sector.decorationIds.erase(
            std::remove(sector.decorationIds.begin(), sector.decorationIds.end(), clampedEntityIndex),
            sector.decorationIds.end());
    }
}

void repairIndoorEntitySectorReferencesAfterDelete(Game::IndoorMapData &indoorGeometry, size_t deletedEntityIndex)
{
    for (Game::IndoorSector &sector : indoorGeometry.sectors)
    {
        std::vector<uint16_t> repairedDecorationIds;
        repairedDecorationIds.reserve(sector.decorationIds.size());

        for (uint16_t entityIndex : sector.decorationIds)
        {
            if (entityIndex == deletedEntityIndex)
            {
                continue;
            }

            repairedDecorationIds.push_back(
                entityIndex > deletedEntityIndex ? static_cast<uint16_t>(entityIndex - 1) : entityIndex);
        }

        sector.decorationIds = std::move(repairedDecorationIds);
    }
}

std::vector<EditorMaterialTextureRemap> collectImportedMaterialRemaps(
    const std::vector<std::string> &bitmapTextureNames,
    const ImportedModel &importedModel,
    const Game::OutdoorBModel &bmodel,
    const std::vector<EditorMaterialTextureRemap> &existingRemaps)
{
    std::vector<EditorMaterialTextureRemap> remaps = existingRemaps;
    std::unordered_set<std::string> seenRemapKeys;

    for (const EditorMaterialTextureRemap &remap : remaps)
    {
        seenRemapKeys.insert(toLowerCopy(trimCopy(remap.sourceMaterialName)));
    }

    const size_t faceCount = std::min(importedModel.faces.size(), bmodel.faces.size());

    for (size_t faceIndex = 0; faceIndex < faceCount; ++faceIndex)
    {
        const ImportedModelFace &importedFace = importedModel.faces[faceIndex];

        if (importedFace.materialName.empty())
        {
            continue;
        }

        const std::string normalizedMaterialName = toLowerCopy(trimCopy(importedFace.materialName));

        if (normalizedMaterialName.empty() || seenRemapKeys.contains(normalizedMaterialName))
        {
            continue;
        }

        const std::string textureName = canonicalBitmapTextureName(bitmapTextureNames, bmodel.faces[faceIndex].textureName);

        if (textureName.empty())
        {
            continue;
        }

        remaps.push_back({importedFace.materialName, textureName});
        seenRemapKeys.insert(normalizedMaterialName);
    }

    std::sort(
        remaps.begin(),
        remaps.end(),
        [](const EditorMaterialTextureRemap &left, const EditorMaterialTextureRemap &right)
        {
            return toLowerCopy(left.sourceMaterialName) < toLowerCopy(right.sourceMaterialName);
        });
    return remaps;
}

std::vector<EditorImportedMaterialDiagnostic> buildImportedMaterialDiagnostics(
    const std::vector<std::string> &bitmapTextureNames,
    const ImportedModel &importedModel,
    const EditorBModelImportSource &importSource)
{
    std::vector<EditorImportedMaterialDiagnostic> diagnostics;
    std::unordered_set<std::string> seenMaterialNames;

    for (const ImportedModelFace &face : importedModel.faces)
    {
        if (trimCopy(face.materialName).empty())
        {
            continue;
        }

        const std::string normalizedMaterialName = toLowerCopy(trimCopy(face.materialName));

        if (normalizedMaterialName.empty() || seenMaterialNames.contains(normalizedMaterialName))
        {
            continue;
        }

        seenMaterialNames.insert(normalizedMaterialName);

        EditorImportedMaterialDiagnostic diagnostic = {};
        diagnostic.sourceMaterialName = face.materialName;
        diagnostic.resolvedTextureName = resolveImportedMaterialTextureName(bitmapTextureNames, &importSource, face.materialName);
        diagnostic.usesDefaultFallback = true;

        for (const EditorMaterialTextureRemap &remap : importSource.materialRemaps)
        {
            if (toLowerCopy(trimCopy(remap.sourceMaterialName)) == normalizedMaterialName)
            {
                diagnostic.hasExplicitRemap = true;
                diagnostic.usesDefaultFallback = false;
                break;
            }
        }

        if (!diagnostic.hasExplicitRemap)
        {
            const std::string canonicalMaterialTextureName =
                canonicalBitmapTextureName(bitmapTextureNames, face.materialName);
            diagnostic.usesDefaultFallback = !isKnownBitmapTextureName(bitmapTextureNames, canonicalMaterialTextureName);
        }

        diagnostic.resolvesToKnownBitmap =
            isKnownBitmapTextureName(bitmapTextureNames, diagnostic.resolvedTextureName);
        diagnostics.push_back(std::move(diagnostic));
    }

    std::sort(
        diagnostics.begin(),
        diagnostics.end(),
        [](const EditorImportedMaterialDiagnostic &left, const EditorImportedMaterialDiagnostic &right)
        {
            return toLowerCopy(left.sourceMaterialName) < toLowerCopy(right.sourceMaterialName);
        });
    return diagnostics;
}

bool loadBitmapTextureSize(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &bitmapTextureNames,
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::string canonicalName = canonicalBitmapTextureName(bitmapTextureNames, textureName);

    if (canonicalName.empty())
    {
        return false;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes =
        assetFileSystem.readBinaryFile("Data/bitmaps/" + canonicalName + ".bmp");

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return false;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return false;
    }

    SDL_Surface *pSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pSurface == nullptr)
    {
        return false;
    }

    width = pSurface->w;
    height = pSurface->h;
    SDL_DestroySurface(pSurface);
    return width > 0 && height > 0;
}

uint8_t classifyImportedPolygonType(
    const ImportedModel &importedModel,
    const ImportedModelFace &face)
{
    if (face.vertices.size() < 3)
    {
        return 0;
    }

    const ImportedModelPosition &a = importedModel.positions[face.vertices[0].positionIndex];
    const ImportedModelPosition &b = importedModel.positions[face.vertices[1].positionIndex];
    const ImportedModelPosition &c = importedModel.positions[face.vertices[2].positionIndex];
    const float abX = b.x - a.x;
    const float abY = b.y - a.y;
    const float abZ = b.z - a.z;
    const float acX = c.x - a.x;
    const float acY = c.y - a.y;
    const float acZ = c.z - a.z;
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float normalLength = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);

    if (normalLength <= 0.0001f)
    {
        return 0;
    }

    const float normalZNormalized = std::fabs(normalZ / normalLength);

    if (normalZNormalized >= 0.85f)
    {
        return 0x3;
    }

    if (normalZNormalized >= 0.45f)
    {
        return 0x4;
    }

    return 0;
}

float faceNormalZ(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    return abX * acY - abY * acX;
}

float faceOutwardDot(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;

    float faceCenterX = 0.0f;
    float faceCenterY = 0.0f;
    float faceCenterZ = 0.0f;

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            continue;
        }

        faceCenterX += static_cast<float>(vertices[vertexIndex].x);
        faceCenterY += static_cast<float>(vertices[vertexIndex].y);
        faceCenterZ += static_cast<float>(vertices[vertexIndex].z);
    }

    const float invVertexCount = 1.0f / static_cast<float>(face.vertexIndices.size());
    faceCenterX *= invVertexCount;
    faceCenterY *= invVertexCount;
    faceCenterZ *= invVertexCount;
    const float offsetX = faceCenterX - modelCenterX;
    const float offsetY = faceCenterY - modelCenterY;
    const float offsetZ = faceCenterZ - modelCenterZ;
    return normalX * offsetX + normalY * offsetY + normalZ * offsetZ;
}

void reverseImportedFaceWinding(Game::OutdoorBModelFace &face)
{
    std::reverse(face.vertexIndices.begin(), face.vertexIndices.end());
    std::reverse(face.textureUs.begin(), face.textureUs.end());
    std::reverse(face.textureVs.begin(), face.textureVs.end());
}

void orientImportedFaceWinding(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    bool shouldReverse = false;

    if (face.polygonType == 0x3 || face.polygonType == 0x4)
    {
        shouldReverse = faceNormalZ(vertices, face) < 0.0f;
    }
    else
    {
        shouldReverse = faceOutwardDot(vertices, face, modelCenterX, modelCenterY, modelCenterZ) < 0.0f;
    }

    if (shouldReverse)
    {
        reverseImportedFaceWinding(face);
    }
}

void generateFallbackFaceTextureCoordinates(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float absNormalX = std::fabs(normalX);
    const float absNormalY = std::fabs(normalY);
    const float absNormalZ = std::fabs(normalZ);

    face.textureUs.clear();
    face.textureVs.clear();
    face.textureUs.reserve(face.vertexIndices.size());
    face.textureVs.reserve(face.vertexIndices.size());

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            face.textureUs.push_back(0);
            face.textureVs.push_back(0);
            continue;
        }

        const Game::OutdoorBModelVertex &vertex = vertices[vertexIndex];
        int16_t textureU = 0;
        int16_t textureV = 0;

        if (absNormalZ >= absNormalX && absNormalZ >= absNormalY)
        {
            textureU = static_cast<int16_t>(std::clamp(vertex.x, -32768, 32767));
            textureV = static_cast<int16_t>(std::clamp(-vertex.y, -32768, 32767));
        }
        else if (absNormalX >= absNormalY)
        {
            textureU = static_cast<int16_t>(std::clamp(vertex.y, -32768, 32767));
            textureV = static_cast<int16_t>(std::clamp(-vertex.z, -32768, 32767));
        }
        else
        {
            textureU = static_cast<int16_t>(std::clamp(vertex.x, -32768, 32767));
            textureV = static_cast<int16_t>(std::clamp(-vertex.z, -32768, 32767));
        }

        face.textureUs.push_back(textureU);
        face.textureVs.push_back(textureV);
    }
}

void recomputeBModelBounds(Game::OutdoorBModel &bmodel)
{
    if (bmodel.vertices.empty())
    {
        bmodel.positionX = 0;
        bmodel.positionY = 0;
        bmodel.positionZ = 0;
        bmodel.minX = 0;
        bmodel.minY = 0;
        bmodel.minZ = 0;
        bmodel.maxX = 0;
        bmodel.maxY = 0;
        bmodel.maxZ = 0;
        bmodel.boundingCenterX = 0;
        bmodel.boundingCenterY = 0;
        bmodel.boundingCenterZ = 0;
        bmodel.boundingRadius = 0;
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    const float centerX = (minX + maxX) * 0.5f;
    const float centerY = (minY + maxY) * 0.5f;
    const float centerZ = (minZ + maxZ) * 0.5f;
    float maxRadiusSquared = 0.0f;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float deltaX = static_cast<float>(vertex.x) - centerX;
        const float deltaY = static_cast<float>(vertex.y) - centerY;
        const float deltaZ = static_cast<float>(vertex.z) - centerZ;
        maxRadiusSquared = std::max(maxRadiusSquared, deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    }

    bmodel.positionX = static_cast<int>(std::lround(centerX));
    bmodel.positionY = static_cast<int>(std::lround(centerY));
    bmodel.positionZ = static_cast<int>(std::lround(centerZ));
    bmodel.minX = static_cast<int>(std::floor(minX));
    bmodel.minY = static_cast<int>(std::floor(minY));
    bmodel.minZ = static_cast<int>(std::floor(minZ));
    bmodel.maxX = static_cast<int>(std::ceil(maxX));
    bmodel.maxY = static_cast<int>(std::ceil(maxY));
    bmodel.maxZ = static_cast<int>(std::ceil(maxZ));
    bmodel.boundingCenterX = static_cast<int>(std::lround(centerX));
    bmodel.boundingCenterY = static_cast<int>(std::lround(centerY));
    bmodel.boundingCenterZ = static_cast<int>(std::lround(centerZ));
    bmodel.boundingRadius = static_cast<int>(std::ceil(std::sqrt(maxRadiusSquared)));
}

EditorBModelSourceTransform sourceTransformFromBModel(const Game::OutdoorBModel &bmodel)
{
    EditorBModelSourceTransform transform = {};

    if (bmodel.vertices.empty())
    {
        transform.originX = static_cast<float>(bmodel.boundingCenterX);
        transform.originY = static_cast<float>(bmodel.boundingCenterY);
        transform.originZ = static_cast<float>(bmodel.boundingCenterZ);
        return transform;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    transform.originX = (minX + maxX) * 0.5f;
    transform.originY = (minY + maxY) * 0.5f;
    transform.originZ = (minZ + maxZ) * 0.5f;
    return transform;
}

Game::OutdoorBModelVertex transformImportedVertex(
    const EditorBModelSourceTransform &transform,
    float localX,
    float localY,
    float localZ)
{
    Game::OutdoorBModelVertex vertex = {};
    const float worldX =
        transform.originX
        + localX * transform.basisX[0]
        + localY * transform.basisY[0]
        + localZ * transform.basisZ[0];
    const float worldY =
        transform.originY
        + localX * transform.basisX[1]
        + localY * transform.basisY[1]
        + localZ * transform.basisZ[1];
    const float worldZ =
        transform.originZ
        + localX * transform.basisX[2]
        + localY * transform.basisY[2]
        + localZ * transform.basisZ[2];
    vertex.x = static_cast<int>(std::lround(worldX));
    vertex.y = static_cast<int>(std::lround(worldY));
    vertex.z = static_cast<int>(std::lround(worldZ));
    return vertex;
}

Game::OutdoorBModel buildImportedBModel(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &bitmapTextureNames,
    const ImportedModel &importedModel,
    const std::filesystem::path &sourcePath,
    float importScale,
    const EditorBModelImportSource &importSource,
    const Game::OutdoorBModel *pPlacementTemplate,
    const EditorBModelSourceTransform *pSourceTransform,
    std::string &errorMessage)
{
    Game::OutdoorBModel bmodel = {};
    bmodel.name = importedModel.name.empty() ? sourcePath.stem().string() : importedModel.name;
    bmodel.secondaryName = bmodel.name;

    if (importScale <= 0.0f)
    {
        errorMessage = "import scale must be greater than zero";
        return {};
    }

    std::vector<Game::OutdoorBModelVertex> importedVertices;
    importedVertices.reserve(importedModel.positions.size());
    float importedMinX = std::numeric_limits<float>::max();
    float importedMinY = std::numeric_limits<float>::max();
    float importedMinZ = std::numeric_limits<float>::max();
    float importedMaxX = std::numeric_limits<float>::lowest();
    float importedMaxY = std::numeric_limits<float>::lowest();
    float importedMaxZ = std::numeric_limits<float>::lowest();

    for (const ImportedModelPosition &position : importedModel.positions)
    {
        const float scaledX = position.x * importScale;
        const float scaledY = position.y * importScale;
        const float scaledZ = position.z * importScale;
        Game::OutdoorBModelVertex vertex = {};
        vertex.x = static_cast<int>(std::lround(scaledX));
        vertex.y = static_cast<int>(std::lround(scaledY));
        vertex.z = static_cast<int>(std::lround(scaledZ));
        importedVertices.push_back(vertex);
        importedMinX = std::min(importedMinX, static_cast<float>(vertex.x));
        importedMinY = std::min(importedMinY, static_cast<float>(vertex.y));
        importedMinZ = std::min(importedMinZ, static_cast<float>(vertex.z));
        importedMaxX = std::max(importedMaxX, static_cast<float>(vertex.x));
        importedMaxY = std::max(importedMaxY, static_cast<float>(vertex.y));
        importedMaxZ = std::max(importedMaxZ, static_cast<float>(vertex.z));
    }

    const float importedCenterX = (importedMinX + importedMaxX) * 0.5f;
    const float importedCenterY = (importedMinY + importedMaxY) * 0.5f;
    const float importedCenterZ = (importedMinZ + importedMaxZ) * 0.5f;
    EditorBModelSourceTransform sourceTransform = {};
    sourceTransform.originX = importedCenterX;
    sourceTransform.originY = importedCenterY;
    sourceTransform.originZ = importedCenterZ;

    if (pPlacementTemplate != nullptr && !pPlacementTemplate->vertices.empty())
    {
        bmodel.name = pPlacementTemplate->name.empty() ? bmodel.name : pPlacementTemplate->name;
        bmodel.secondaryName =
            pPlacementTemplate->secondaryName.empty() ? bmodel.secondaryName : pPlacementTemplate->secondaryName;
    }

    if (pSourceTransform != nullptr)
    {
        sourceTransform = *pSourceTransform;
    }
    else if (pPlacementTemplate != nullptr)
    {
        sourceTransform = sourceTransformFromBModel(*pPlacementTemplate);

        if (!pPlacementTemplate->vertices.empty())
        {
            float templateMinZ = std::numeric_limits<float>::max();

            for (const Game::OutdoorBModelVertex &vertex : pPlacementTemplate->vertices)
            {
                templateMinZ = std::min(templateMinZ, static_cast<float>(vertex.z));
            }

            sourceTransform.originZ = templateMinZ + (importedCenterZ - importedMinZ);
        }
    }

    for (Game::OutdoorBModelVertex &vertex : importedVertices)
    {
        const float localX = static_cast<float>(vertex.x) - importedCenterX;
        const float localY = static_cast<float>(vertex.y) - importedCenterY;
        const float localZ = static_cast<float>(vertex.z) - importedCenterZ;
        vertex = transformImportedVertex(sourceTransform, localX, localY, localZ);
    }

    bmodel.vertices = std::move(importedVertices);

    for (const ImportedModelFace &importedFace : importedModel.faces)
    {
        Game::OutdoorBModelFace face = {};
        face.attributes = 0;
        face.bitmapIndex = 0;
        face.textureDeltaU = 0;
        face.textureDeltaV = 0;
        face.cogNumber = 0;
        face.cogTriggeredNumber = 0;
        face.cogTrigger = 0;
        face.reserved = 0;
        face.polygonType = classifyImportedPolygonType(importedModel, importedFace);
        face.shade = 0;
        face.visibility = 31;
        face.textureName = resolveImportedMaterialTextureName(
            bitmapTextureNames,
            &importSource,
            importedFace.materialName);

        int textureWidth = 256;
        int textureHeight = 256;
        loadBitmapTextureSize(assetFileSystem, bitmapTextureNames, face.textureName, textureWidth, textureHeight);
        bool allVerticesHaveUv = true;
        bool hasVaryingUv = false;
        float firstU = 0.0f;
        float firstV = 0.0f;
        bool firstUvAssigned = false;

        for (const ImportedModelFaceVertex &importedVertex : importedFace.vertices)
        {
            face.vertexIndices.push_back(static_cast<uint16_t>(importedVertex.positionIndex));

            if (importedVertex.hasUv)
            {
                if (!firstUvAssigned)
                {
                    firstU = importedVertex.u;
                    firstV = importedVertex.v;
                    firstUvAssigned = true;
                }
                else if (std::fabs(importedVertex.u - firstU) > 0.0001f
                    || std::fabs(importedVertex.v - firstV) > 0.0001f)
                {
                    hasVaryingUv = true;
                }

                face.textureUs.push_back(
                    static_cast<int16_t>(std::clamp(
                        static_cast<int>(std::lround(importedVertex.u * static_cast<float>(textureWidth))),
                        -32768,
                        32767)));
                face.textureVs.push_back(static_cast<int16_t>(
                    std::clamp(
                        static_cast<int>(std::lround((1.0f - importedVertex.v) * static_cast<float>(textureHeight))),
                        -32768,
                        32767)));
            }
            else
            {
                allVerticesHaveUv = false;
                face.textureUs.push_back(0);
                face.textureVs.push_back(0);
            }
        }

        orientImportedFaceWinding(
            bmodel.vertices,
            face,
            sourceTransform.originX,
            sourceTransform.originY,
            sourceTransform.originZ);

        if (!allVerticesHaveUv || !hasVaryingUv)
        {
            generateFallbackFaceTextureCoordinates(bmodel.vertices, face);
        }

        bmodel.faces.push_back(std::move(face));
    }

    recomputeBModelBounds(bmodel);
    return bmodel;
}

void pruneInteractiveFaceReferences(Game::OutdoorSceneData &sceneData, size_t bmodelIndex, size_t faceCount)
{
    sceneData.interactiveFaces.erase(
        std::remove_if(
            sceneData.interactiveFaces.begin(),
            sceneData.interactiveFaces.end(),
            [bmodelIndex, faceCount](const Game::OutdoorSceneInteractiveFace &face)
            {
                return face.bmodelIndex == bmodelIndex && face.faceIndex >= faceCount;
            }),
        sceneData.interactiveFaces.end());

    sceneData.initialState.faceAttributeOverrides.erase(
        std::remove_if(
            sceneData.initialState.faceAttributeOverrides.begin(),
            sceneData.initialState.faceAttributeOverrides.end(),
            [bmodelIndex, faceCount](const Game::OutdoorSceneFaceAttributeOverride &face)
            {
                return face.bmodelIndex == bmodelIndex && face.faceIndex >= faceCount;
            }),
        sceneData.initialState.faceAttributeOverrides.end());
}

void repairBModelReferencesAfterDelete(Game::OutdoorSceneData &sceneData, size_t deletedBModelIndex)
{
    sceneData.interactiveFaces.erase(
        std::remove_if(
            sceneData.interactiveFaces.begin(),
            sceneData.interactiveFaces.end(),
            [deletedBModelIndex](Game::OutdoorSceneInteractiveFace &face)
            {
                if (face.bmodelIndex == deletedBModelIndex)
                {
                    return true;
                }

                if (face.bmodelIndex > deletedBModelIndex)
                {
                    --face.bmodelIndex;
                }

                return false;
            }),
        sceneData.interactiveFaces.end());

    sceneData.initialState.faceAttributeOverrides.erase(
        std::remove_if(
            sceneData.initialState.faceAttributeOverrides.begin(),
            sceneData.initialState.faceAttributeOverrides.end(),
            [deletedBModelIndex](Game::OutdoorSceneFaceAttributeOverride &face)
            {
                if (face.bmodelIndex == deletedBModelIndex)
                {
                    return true;
                }

                if (face.bmodelIndex > deletedBModelIndex)
                {
                    --face.bmodelIndex;
                }

                return false;
            }),
        sceneData.initialState.faceAttributeOverrides.end());
}

void copyBModelSceneReferences(
    const Game::OutdoorSceneData &sourceSceneData,
    size_t sourceBModelIndex,
    size_t targetBModelIndex,
    Game::OutdoorSceneData &targetSceneData)
{
    std::vector<Game::OutdoorSceneInteractiveFace> copiedInteractiveFaces;
    std::vector<Game::OutdoorSceneFaceAttributeOverride> copiedFaceOverrides;

    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sourceSceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex != sourceBModelIndex)
        {
            continue;
        }

        Game::OutdoorSceneInteractiveFace copiedFace = interactiveFace;
        copiedFace.bmodelIndex = targetBModelIndex;
        copiedInteractiveFaces.push_back(std::move(copiedFace));
    }

    for (const Game::OutdoorSceneFaceAttributeOverride &faceOverride : sourceSceneData.initialState.faceAttributeOverrides)
    {
        if (faceOverride.bmodelIndex != sourceBModelIndex)
        {
            continue;
        }

        Game::OutdoorSceneFaceAttributeOverride copiedOverride = faceOverride;
        copiedOverride.bmodelIndex = targetBModelIndex;
        copiedFaceOverrides.push_back(std::move(copiedOverride));
    }

    targetSceneData.interactiveFaces.insert(
        targetSceneData.interactiveFaces.end(),
        copiedInteractiveFaces.begin(),
        copiedInteractiveFaces.end());
    targetSceneData.initialState.faceAttributeOverrides.insert(
        targetSceneData.initialState.faceAttributeOverrides.end(),
        copiedFaceOverrides.begin(),
        copiedFaceOverrides.end());
}
}

void EditorSession::initialize(const Engine::AssetFileSystem &assetFileSystem)
{
    m_pAssetFileSystem = &assetFileSystem;
    m_pendingSpawn = {};
    m_pendingSpawn.radius = 512;
    m_pendingSpawn.typeId = 3;
    m_pendingSpawn.index = 1;
    m_pendingActor = {};
    m_pendingActor.hp = 1;
    m_pendingActor.radius = 64;
    m_pendingActor.height = 128;
    m_pendingActor.moveSpeed = 256;

    std::vector<std::vector<std::string>> monsterDataRows;
    std::vector<std::vector<std::string>> monsterDescriptorRows;
    std::vector<std::vector<std::string>> placedMonsterRows;
    std::vector<std::vector<std::string>> monsterRelationRows;

    if (loadTextTableRows(assetFileSystem, "Data/data_tables/monster_data.txt", monsterDataRows)
        && loadTextTableRows(assetFileSystem, "Data/data_tables/monster_descriptors.txt", monsterDescriptorRows)
        && loadTextTableRows(assetFileSystem, "Data/data_tables/english/place_mon.txt", placedMonsterRows)
        && loadTextTableRows(assetFileSystem, "Data/data_tables/monster_relation_data.txt", monsterRelationRows))
    {
        m_monsterTable.loadEntriesFromRows(monsterDescriptorRows);
        m_monsterTable.loadDisplayNamesFromRows(monsterDataRows);
        m_monsterTable.loadStatsFromRows(monsterDataRows);
        m_monsterTable.loadUniqueNamesFromRows(placedMonsterRows);
        m_monsterTable.loadRelationsFromRows(monsterRelationRows);
        buildMonsterOptions(monsterDataRows, m_monsterOptions);
    }

    std::vector<std::vector<std::string>> chestRows;

    if (loadTextTableRows(assetFileSystem, "Data/data_tables/chest_data.txt", chestRows))
    {
        m_chestTable.loadRows(chestRows);
        buildChestOptions(chestRows, m_chestOptions);
    }

    std::vector<std::vector<std::string>> decorationRows;
    m_hasDecorationTable = loadTextTableRows(assetFileSystem, "Data/data_tables/decoration_data.txt", decorationRows)
        && m_decorationTable.loadRows(decorationRows);

    if (m_hasDecorationTable)
    {
        buildDecorationOptions(decorationRows, m_decorationOptions);

        if (!m_decorationOptions.empty())
        {
            m_pendingEntityDecorationListId = static_cast<uint16_t>(m_decorationOptions.front().id);
        }
    }

    m_hasEntityBillboardSpriteFrameTable =
        loadEditorEntityBillboardSpriteFrameTable(assetFileSystem, m_entityBillboardSpriteFrameTable);

    loadEditorMapStats(assetFileSystem, m_mapStats);

    std::vector<std::vector<std::string>> objectRows;

    if (loadTextTableRows(assetFileSystem, "Data/data_tables/object_list.txt", objectRows))
    {
        m_objectTable.loadRows(objectRows);
        buildObjectOptions(objectRows, m_objectOptions);

        if (!m_objectOptions.empty())
        {
            m_pendingSpriteObjectDescriptionId = static_cast<uint16_t>(m_objectOptions.front().id);
        }
    }

    std::vector<std::vector<std::string>> itemRows;
    std::vector<std::vector<std::string>> randomItemRows;

    if (loadTextTableRows(assetFileSystem, "Data/data_tables/items.txt", itemRows))
    {
        buildEditorItemNames(itemRows, m_itemNames, m_itemOptions);
        loadTextTableRows(assetFileSystem, "Data/data_tables/random_items.txt", randomItemRows);
        m_itemTable.load(assetFileSystem, itemRows, randomItemRows);

        if (!m_itemOptions.empty())
        {
            m_pendingSpriteObjectItemId = m_itemOptions.front().id;

            if (const std::optional<uint16_t> objectDescriptionId =
                    objectDescriptionIdForItem(m_pendingSpriteObjectItemId))
            {
                m_pendingSpriteObjectDescriptionId = *objectDescriptionId;
            }
        }
    }

    buildBitmapTextureNames(assetFileSystem, m_bitmapTextureNames);
}

bool EditorSession::openDefaultOutdoorDocument(std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    const std::vector<std::string> entries = m_pAssetFileSystem->enumerate("Data/games");
    std::string selectedMapFileName;
    bool selectedMapIsIndoor = false;

    for (const std::string &entry : entries)
    {
        if (entry == "d18.scene.yml" || entry == "d18.blv")
        {
            selectedMapFileName = "d18.blv";
            selectedMapIsIndoor = true;
            break;
        }
    }

    if (selectedMapFileName.empty())
    {
        for (const std::string &entry : entries)
        {
            if (entry == "out01.map.yml" || entry == "out01.scene.yml")
            {
                selectedMapFileName = "out01.odm";
                break;
            }
        }
    }

    if (selectedMapFileName.empty())
    {
        for (const std::string &entry : entries)
        {
            if (entry.ends_with(".blv"))
            {
                selectedMapFileName = std::filesystem::path(entry).filename().string();
                selectedMapIsIndoor = true;
                break;
            }

            if (entry.ends_with(".map.yml"))
            {
                const std::filesystem::path path(entry);
                selectedMapFileName = path.stem().stem().string() + ".odm";
                break;
            }

            if (entry.ends_with(".scene.yml"))
            {
                const std::filesystem::path path(entry);
                selectedMapFileName = path.stem().stem().string() + ".odm";
                break;
            }
        }
    }

    if (selectedMapFileName.empty())
    {
        errorMessage = "could not find any indoor or outdoor .scene.yml / .map.yml document in Data/games";
        return false;
    }

    return selectedMapIsIndoor
        ? openIndoorMap(selectedMapFileName, errorMessage)
        : openOutdoorMap(selectedMapFileName, errorMessage);
}

bool EditorSession::openOutdoorMap(const std::string &mapFileName, std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!m_document.loadOutdoorMapPackage(*m_pAssetFileSystem, mapFileName, errorMessage))
    {
        return false;
    }

    loadOutdoorEditorSupportData(mapFileName);
    resetHistory();
    resetPreviewEventRuntimeState();
    m_document.synchronizeOutdoorGeometryMetadata();
    m_savedSnapshot = m_document.createOutdoorSceneSnapshot();
    refreshValidation();
    m_selection = {EditorSelectionKind::Summary, 0};
    appendLog("info", "Opened outdoor document " + m_document.displayName());
    return true;
}

bool EditorSession::openIndoorMap(const std::string &mapFileName, std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!m_document.loadIndoorMapPackage(*m_pAssetFileSystem, mapFileName, errorMessage))
    {
        return false;
    }

    loadOutdoorEditorSupportData(mapFileName);
    resetHistory();
    resetPreviewEventRuntimeState();
    m_savedSnapshot = m_document.createIndoorSceneSnapshot();
    refreshValidation();
    m_selection = {EditorSelectionKind::Summary, 0};
    appendLog("info", "Opened indoor document " + m_document.displayName());
    return true;
}

bool EditorSession::openMapPhysicalPath(const std::filesystem::path &path, std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!m_document.loadMapPhysicalPath(*m_pAssetFileSystem, path, errorMessage))
    {
        return false;
    }

    loadOutdoorEditorSupportData(m_document.displayName());
    resetHistory();
    resetPreviewEventRuntimeState();

    if (m_document.kind() == EditorDocument::Kind::Outdoor)
    {
        m_document.synchronizeOutdoorGeometryMetadata();
        m_savedSnapshot = m_document.createOutdoorSceneSnapshot();
        appendLog("info", "Opened outdoor document " + m_document.displayName());
    }
    else
    {
        m_savedSnapshot = m_document.createIndoorSceneSnapshot();
        appendLog("info", "Opened indoor document " + m_document.displayName());
    }

    refreshValidation();
    m_selection = {EditorSelectionKind::Summary, 0};
    return true;
}

bool EditorSession::createNewOutdoorMap(
    const std::string &mapId,
    const std::string &displayName,
    EditorOutdoorMapTilesetPreset tilesetPreset,
    std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    const std::optional<std::string> normalizedMapId = validateOutdoorMapId(mapId, errorMessage);

    if (!normalizedMapId)
    {
        return false;
    }

    const std::string mapFileName = *normalizedMapId + ".odm";
    const std::string resolvedDisplayName = trimCopy(displayName).empty() ? *normalizedMapId : trimCopy(displayName);
    const Game::OutdoorSceneEnvironment environment = outdoorMapEnvironmentForTilesetPreset(tilesetPreset);

    if (!m_document.createNewOutdoorMapPackage(
            *m_pAssetFileSystem,
            mapFileName,
            resolvedDisplayName,
            environment,
            errorMessage))
    {
        return false;
    }

    loadEditorMapStats(*m_pAssetFileSystem, m_mapStats);
    loadOutdoorEditorSupportData(mapFileName);
    resetHistory();
    m_document.synchronizeOutdoorGeometryMetadata();
    m_savedSnapshot = m_document.createOutdoorSceneSnapshot();
    refreshValidation();
    m_selection = {EditorSelectionKind::Summary, 0};
    appendLog("info", "Created outdoor document " + m_document.displayName());
    return true;
}

bool EditorSession::saveActiveDocumentAs(
    const std::string &mapId,
    const std::string &displayName,
    std::string &errorMessage)
{
    if (!hasDocument() || document().kind() != EditorDocument::Kind::Outdoor)
    {
        errorMessage = "no outdoor document is loaded";
        return false;
    }

    const std::optional<std::string> normalizedMapId = validateOutdoorMapId(mapId, errorMessage);

    if (!normalizedMapId)
    {
        return false;
    }

    const std::string mapFileName = *normalizedMapId + ".odm";
    const std::string resolvedDisplayName = trimCopy(displayName).empty() ? *normalizedMapId : trimCopy(displayName);
    const std::filesystem::path targetScenePath =
        m_pAssetFileSystem->getEditorDevelopmentRoot() / "Data" / "games" / (*normalizedMapId + ".scene.yml");
    m_document.prepareOutdoorMapPackageIdentityForMapFile(mapFileName, resolvedDisplayName);
    m_document.synchronizeOutdoorGeometryMetadata();
    m_document.synchronizeOutdoorTerrainMetadata();

    if (!m_document.saveSourceAs(targetScenePath, errorMessage))
    {
        return false;
    }

    if (!m_document.buildRuntimeAs(targetScenePath, errorMessage))
    {
        return false;
    }

    loadEditorMapStats(*m_pAssetFileSystem, m_mapStats);
    loadOutdoorEditorSupportData(mapFileName);
    m_savedSnapshot = m_document.createOutdoorSceneSnapshot();
    refreshDirtyState();
    refreshValidation();
    appendLog("info", "Saved outdoor document as " + m_document.displayName());
    return true;
}

bool EditorSession::duplicateActiveDocumentAs(
    const std::string &mapId,
    const std::string &displayName,
    std::string &errorMessage)
{
    if (!saveActiveDocumentAs(mapId, displayName, errorMessage))
    {
        return false;
    }

    appendLog("info", "Duplicated outdoor document as " + m_document.displayName());
    return true;
}

bool EditorSession::deleteActiveDocumentPackage(std::string &errorMessage)
{
    if (!hasDocument() || document().kind() != EditorDocument::Kind::Outdoor)
    {
        errorMessage = "no outdoor document is loaded";
        return false;
    }

    const std::filesystem::path gamesPath = m_document.scenePhysicalPath().parent_path().lexically_normal();
    const std::filesystem::path editorGamesPath =
        m_pAssetFileSystem->getEditorDevelopmentRoot() / "Data" / "games";
    const std::vector<std::filesystem::path> paths = {
        m_document.scenePhysicalPath(),
        m_document.geometryPhysicalPath(),
        m_document.geometryMetadataPhysicalPath(),
        m_document.terrainMetadataPhysicalPath(),
        m_document.mapPackagePhysicalPath()
    };

    for (const std::filesystem::path &path : paths)
    {
        if (path.empty())
        {
            continue;
        }

        if (path.lexically_normal().parent_path() != gamesPath)
        {
            errorMessage = "refusing to delete map files outside Data/games";
            return false;
        }
    }

    if (gamesPath != editorGamesPath.lexically_normal())
    {
        errorMessage = "refusing to delete map files outside the editor authored root";
        return false;
    }

    const std::string deletedMapFileName = m_document.displayName();

    for (const std::filesystem::path &path : paths)
    {
        if (path.empty())
        {
            continue;
        }

        std::error_code errorCode;
        std::filesystem::remove(path, errorCode);

        if (errorCode)
        {
            errorMessage = "could not delete " + path.filename().string() + ": " + errorCode.message();
            return false;
        }
    }

    if (!openDefaultOutdoorDocument(errorMessage))
    {
        errorMessage = "deleted " + deletedMapFileName + ", but could not open another document: " + errorMessage;
        return false;
    }

    appendLog("info", "Deleted outdoor document " + deletedMapFileName);
    return true;
}

bool EditorSession::saveActiveDocument(std::string &errorMessage)
{
    if (m_document.kind() == EditorDocument::Kind::Outdoor)
    {
        m_document.synchronizeOutdoorGeometryMetadata();
        m_document.synchronizeOutdoorTerrainMetadata();
    }

    if (!m_document.saveSource(errorMessage))
    {
        return false;
    }

    m_savedSnapshot = m_document.kind() == EditorDocument::Kind::Indoor
        ? m_document.createIndoorSceneSnapshot()
        : m_document.createOutdoorSceneSnapshot();
    refreshDirtyState();
    refreshValidation();
    appendLog("info", "Saved source " + m_document.sceneVirtualPath());
    return true;
}

bool EditorSession::buildActiveDocument(std::string &errorMessage)
{
    if (!m_document.buildRuntime(errorMessage))
    {
        return false;
    }

    if (m_pAssetFileSystem != nullptr)
    {
        loadEditorMapStats(*m_pAssetFileSystem, m_mapStats);

        if (hasDocument())
        {
            loadOutdoorEditorSupportData(m_document.displayName());
        }
    }

    refreshDirtyState();
    refreshValidation();
    appendLog("info", "Built runtime " + m_document.sceneVirtualPath());
    return true;
}

void EditorSession::beginFrameEditTracking()
{
    m_frameMutationCaptured = false;
}

void EditorSession::captureUndoSnapshot()
{
    if (!hasDocument())
    {
        return;
    }

    if (m_frameMutationCaptured)
    {
        return;
    }

    m_undoSnapshots.push_back(
        m_document.kind() == EditorDocument::Kind::Indoor
            ? m_document.createIndoorSceneSnapshot()
            : m_document.createOutdoorSceneSnapshot());

    if (m_undoSnapshots.size() > 256)
    {
        m_undoSnapshots.erase(m_undoSnapshots.begin(), m_undoSnapshots.begin() + 64);
    }

    m_redoSnapshots.clear();
    m_frameMutationCaptured = true;
}

void EditorSession::noteDocumentMutated(const std::string &reason)
{
    if (!hasDocument())
    {
        return;
    }

    pruneBModelImportSources();
    m_document.synchronizeOutdoorGeometryMetadata();
    m_document.touchSceneRevision();
    resetPreviewEventRuntimeState();
    refreshDirtyState();
    refreshValidation();

    if (!reason.empty())
    {
        appendLog("info", reason);
    }
}

bool EditorSession::canUndo() const
{
    return !m_undoSnapshots.empty() && m_pAssetFileSystem != nullptr;
}

bool EditorSession::canRedo() const
{
    return !m_redoSnapshots.empty() && m_pAssetFileSystem != nullptr;
}

bool EditorSession::undo(std::string &errorMessage)
{
    if (!canUndo())
    {
        errorMessage = "nothing to undo";
        return false;
    }

    const std::string currentSnapshot = m_document.kind() == EditorDocument::Kind::Indoor
        ? m_document.createIndoorSceneSnapshot()
        : m_document.createOutdoorSceneSnapshot();
    const std::string targetSnapshot = m_undoSnapshots.back();
    m_undoSnapshots.pop_back();

    const bool restored = m_document.kind() == EditorDocument::Kind::Indoor
        ? m_document.restoreIndoorSceneSnapshot(*m_pAssetFileSystem, targetSnapshot, errorMessage)
        : m_document.restoreOutdoorSceneSnapshot(*m_pAssetFileSystem, targetSnapshot, errorMessage);

    if (!restored)
    {
        return false;
    }

    m_redoSnapshots.push_back(currentSnapshot);
    pruneBModelImportSources();
    refreshDirtyState();
    refreshValidation();
    appendLog("info", "Undo");
    return true;
}

bool EditorSession::redo(std::string &errorMessage)
{
    if (!canRedo())
    {
        errorMessage = "nothing to redo";
        return false;
    }

    const std::string currentSnapshot = m_document.kind() == EditorDocument::Kind::Indoor
        ? m_document.createIndoorSceneSnapshot()
        : m_document.createOutdoorSceneSnapshot();
    const std::string targetSnapshot = m_redoSnapshots.back();
    m_redoSnapshots.pop_back();

    const bool restored = m_document.kind() == EditorDocument::Kind::Indoor
        ? m_document.restoreIndoorSceneSnapshot(*m_pAssetFileSystem, targetSnapshot, errorMessage)
        : m_document.restoreOutdoorSceneSnapshot(*m_pAssetFileSystem, targetSnapshot, errorMessage);

    if (!restored)
    {
        return false;
    }

    m_undoSnapshots.push_back(currentSnapshot);
    pruneBModelImportSources();
    refreshDirtyState();
    refreshValidation();
    appendLog("info", "Redo");
    return true;
}

bool EditorSession::createOutdoorObject(EditorSelectionKind kind, int x, int y, int z, std::string &errorMessage)
{
    if (!hasDocument())
    {
        errorMessage = "no document is loaded";
        return false;
    }

    captureUndoSnapshot();
    EditorSelection newSelection = {};
    std::string createdLabel;

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        Game::IndoorMapData &indoorGeometry = m_document.mutableIndoorGeometry();
        Game::IndoorSceneData &sceneData = m_document.mutableIndoorSceneData();

        switch (kind)
        {
        case EditorSelectionKind::Entity:
        {
            Game::IndoorEntity entity = {};
            entity.decorationListId = m_pendingEntityDecorationListId;
            entity.x = x;
            entity.y = y;
            entity.z = z;

            if (const Game::DecorationEntry *pDecoration = m_decorationTable.get(entity.decorationListId))
            {
                entity.name = pDecoration->internalName;
            }

            indoorGeometry.entities.push_back(std::move(entity));
            assignIndoorEntityToSector(indoorGeometry, indoorGeometry.entities.size() - 1);
            indoorGeometry.spriteCount = indoorGeometry.entities.size();
            newSelection = {EditorSelectionKind::Entity, indoorGeometry.entities.size() - 1};
            createdLabel = "decoration";
            break;
        }

        case EditorSelectionKind::Actor:
        {
            Game::MapDeltaActor actor = m_pendingActor;
            actor.x = x;
            actor.y = y;
            actor.z = snapIndoorActorZToFloor(indoorGeometry, x, y, z);
            actor.sectorId = Game::findIndoorSectorForPoint(
                indoorGeometry,
                indoorGeometry.vertices,
                {static_cast<float>(actor.x), static_cast<float>(actor.y), static_cast<float>(actor.z)})
                .value_or(-1);
            sceneData.initialState.actors.push_back(std::move(actor));
            newSelection = {EditorSelectionKind::Actor, sceneData.initialState.actors.size() - 1};
            createdLabel = "actor";
            break;
        }

        case EditorSelectionKind::Spawn:
        {
            Game::IndoorSpawn spawn = {};
            spawn.x = x;
            spawn.y = y;
            spawn.radius = m_pendingSpawn.radius;
            spawn.typeId = m_pendingSpawn.typeId;
            spawn.index = m_pendingSpawn.index;
            spawn.attributes = m_pendingSpawn.attributes;
            spawn.group = m_pendingSpawn.group;
            spawn.z = snapIndoorActorZToFloor(indoorGeometry, x, y, z);
            indoorGeometry.spawns.push_back(std::move(spawn));
            indoorGeometry.spawnCount = indoorGeometry.spawns.size();
            newSelection = {EditorSelectionKind::Spawn, indoorGeometry.spawns.size() - 1};
            createdLabel = "spawn";
            break;
        }

        case EditorSelectionKind::SpriteObject:
        {
            Game::MapDeltaSpriteObject spriteObject = {};
            spriteObject.objectDescriptionId = m_pendingSpriteObjectDescriptionId;
            spriteObject.x = x;
            spriteObject.y = y;
            spriteObject.z = z;
            spriteObject.initialX = x;
            spriteObject.initialY = y;
            spriteObject.initialZ = z;
            Game::writeSpriteObjectContainedItemPayload(spriteObject.rawContainingItem, m_pendingSpriteObjectItemId);

            if (const Game::ObjectEntry *pObjectEntry = m_objectTable.get(spriteObject.objectDescriptionId))
            {
                spriteObject.spriteId = pObjectEntry->spriteId;
                spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
            }

            sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
            newSelection = {EditorSelectionKind::SpriteObject, sceneData.initialState.spriteObjects.size() - 1};
            createdLabel = "sprite object";
            break;
        }

        case EditorSelectionKind::Chest:
        {
            Game::MapDeltaChest chest = {};
            chest.rawItems.assign(ChestItemRecordCount * ChestItemRecordSize, 0);
            chest.inventoryMatrix.assign(ChestInventoryCellCount, 0);
            sceneData.initialState.chests.push_back(std::move(chest));
            newSelection = {EditorSelectionKind::Chest, sceneData.initialState.chests.size() - 1};
            createdLabel = "chest";
            break;
        }

        default:
            errorMessage = "selected indoor kind cannot be created in Wave 2";
            return false;
        }
    }
    else
    {
        Game::OutdoorSceneData &sceneData = m_document.mutableOutdoorSceneData();

        switch (kind)
        {
        case EditorSelectionKind::Entity:
        {
            Game::OutdoorSceneEntity entity = {};
            entity.entityIndex = sceneData.entities.size();
            entity.entity.decorationListId = m_pendingEntityDecorationListId;
            entity.entity.x = x;
            entity.entity.y = y;
            entity.entity.z = z;

            if (const Game::DecorationEntry *pDecoration = m_decorationTable.get(entity.entity.decorationListId))
            {
                entity.entity.name = pDecoration->internalName;
            }

            sceneData.entities.push_back(std::move(entity));
            newSelection = {EditorSelectionKind::Entity, sceneData.entities.size() - 1};
            createdLabel = "entity";
            break;
        }

        case EditorSelectionKind::Spawn:
        {
            Game::OutdoorSceneSpawn spawn = {};
            spawn.spawnIndex = sceneData.spawns.size();
            spawn.spawn = m_pendingSpawn;
            spawn.spawn.x = x;
            spawn.spawn.y = y;
            spawn.spawn.z = z;
            sceneData.spawns.push_back(std::move(spawn));
            newSelection = {EditorSelectionKind::Spawn, sceneData.spawns.size() - 1};
            createdLabel = "spawn";
            break;
        }

        case EditorSelectionKind::Actor:
        {
            Game::MapDeltaActor actor = m_pendingActor;
            actor.x = x;
            actor.y = y;
            actor.z = z;
            sceneData.initialState.actors.push_back(std::move(actor));
            newSelection = {EditorSelectionKind::Actor, sceneData.initialState.actors.size() - 1};
            createdLabel = "actor";
            break;
        }

        case EditorSelectionKind::SpriteObject:
        {
            Game::MapDeltaSpriteObject spriteObject = {};
            spriteObject.objectDescriptionId = m_pendingSpriteObjectDescriptionId;
            spriteObject.x = x;
            spriteObject.y = y;
            spriteObject.z = z;
            spriteObject.initialX = x;
            spriteObject.initialY = y;
            spriteObject.initialZ = z;
            Game::writeSpriteObjectContainedItemPayload(spriteObject.rawContainingItem, m_pendingSpriteObjectItemId);

            if (const Game::ObjectEntry *pObjectEntry = m_objectTable.get(spriteObject.objectDescriptionId))
            {
                spriteObject.spriteId = pObjectEntry->spriteId;
                spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
            }

            sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
            newSelection = {EditorSelectionKind::SpriteObject, sceneData.initialState.spriteObjects.size() - 1};
            createdLabel = "sprite object";
            break;
        }

        default:
            errorMessage = "selected kind cannot be created";
            return false;
        }
    }

    if (m_document.kind() == EditorDocument::Kind::Outdoor)
    {
        normalizeOutdoorSceneCollections();
    }

    m_selection = newSelection;
    noteDocumentMutated("Created " + createdLabel);
    return true;
}

bool EditorSession::duplicateSelectedObject(std::string &errorMessage)
{
    if (!hasDocument())
    {
        errorMessage = "no document is loaded";
        return false;
    }

    constexpr int DuplicateOffset = 256;

    captureUndoSnapshot();
    std::string duplicatedLabel;

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        Game::IndoorMapData &indoorGeometry = m_document.mutableIndoorGeometry();
        Game::IndoorSceneData &sceneData = m_document.mutableIndoorSceneData();

        switch (m_selection.kind)
        {
        case EditorSelectionKind::Entity:
            if (m_selection.index >= indoorGeometry.entities.size())
            {
                errorMessage = "selected decoration is out of range";
                return false;
            }
            else
            {
                Game::IndoorEntity entity = indoorGeometry.entities[m_selection.index];
                entity.x += DuplicateOffset;
                entity.y += DuplicateOffset;
                indoorGeometry.entities.push_back(std::move(entity));
                assignIndoorEntityToSector(indoorGeometry, indoorGeometry.entities.size() - 1);
                indoorGeometry.spriteCount = indoorGeometry.entities.size();
                m_selection = {EditorSelectionKind::Entity, indoorGeometry.entities.size() - 1};
                duplicatedLabel = "decoration";
            }
            break;

        case EditorSelectionKind::Actor:
            if (m_selection.index >= sceneData.initialState.actors.size())
            {
                errorMessage = "selected actor is out of range";
                return false;
            }
            else
            {
                Game::MapDeltaActor actor = sceneData.initialState.actors[m_selection.index];
                actor.x += DuplicateOffset;
                actor.y += DuplicateOffset;
                sceneData.initialState.actors.push_back(std::move(actor));
                m_selection = {EditorSelectionKind::Actor, sceneData.initialState.actors.size() - 1};
                duplicatedLabel = "actor";
            }
            break;

        case EditorSelectionKind::Spawn:
            if (m_selection.index >= indoorGeometry.spawns.size())
            {
                errorMessage = "selected spawn is out of range";
                return false;
            }
            else
            {
                Game::IndoorSpawn spawn = indoorGeometry.spawns[m_selection.index];
                spawn.x += DuplicateOffset;
                spawn.y += DuplicateOffset;
                indoorGeometry.spawns.push_back(std::move(spawn));
                indoorGeometry.spawnCount = indoorGeometry.spawns.size();
                m_selection = {EditorSelectionKind::Spawn, indoorGeometry.spawns.size() - 1};
                duplicatedLabel = "spawn";
            }
            break;

        case EditorSelectionKind::SpriteObject:
            if (m_selection.index >= sceneData.initialState.spriteObjects.size())
            {
                errorMessage = "selected sprite object is out of range";
                return false;
            }
            else
            {
                Game::MapDeltaSpriteObject spriteObject = sceneData.initialState.spriteObjects[m_selection.index];
                spriteObject.x += DuplicateOffset;
                spriteObject.y += DuplicateOffset;
                spriteObject.initialX += DuplicateOffset;
                spriteObject.initialY += DuplicateOffset;
                sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
                m_selection = {EditorSelectionKind::SpriteObject, sceneData.initialState.spriteObjects.size() - 1};
                duplicatedLabel = "sprite object";
            }
            break;

        case EditorSelectionKind::Chest:
            if (m_selection.index >= sceneData.initialState.chests.size())
            {
                errorMessage = "selected chest is out of range";
                return false;
            }
            else
            {
                Game::MapDeltaChest chest = sceneData.initialState.chests[m_selection.index];
                sceneData.initialState.chests.push_back(std::move(chest));
                m_selection = {EditorSelectionKind::Chest, sceneData.initialState.chests.size() - 1};
                duplicatedLabel = "chest";
            }
            break;

        case EditorSelectionKind::Door:
            if (m_selection.index >= sceneData.initialState.doors.size())
            {
                errorMessage = "selected door override is out of range";
                return false;
            }
            else
            {
                const std::optional<size_t> newDoorIndex =
                    nextAvailableIndoorDoorIndex(sceneData, m_document.indoorGeometry().doorCount);

                if (!newDoorIndex)
                {
                    errorMessage = "no unused indoor geometry door slot is available";
                    return false;
                }

                Game::IndoorSceneDoor door = sceneData.initialState.doors[m_selection.index];
                door.doorIndex = *newDoorIndex;
                door.door.slotIndex = *newDoorIndex;
                sceneData.initialState.doors.push_back(std::move(door));
                m_selection = {EditorSelectionKind::Door, sceneData.initialState.doors.size() - 1};
                duplicatedLabel = "door override";
            }
            break;

        default:
            errorMessage = "selected indoor item cannot be duplicated in Wave 2";
            return false;
        }
    }
    else
    {
        Game::OutdoorSceneData &sceneData = m_document.mutableOutdoorSceneData();

        switch (m_selection.kind)
        {
        case EditorSelectionKind::BModel:
            if (m_selection.index >= m_document.mutableOutdoorGeometry().bmodels.size())
            {
                errorMessage = "selected bmodel is out of range";
                return false;
            }
            else
            {
                Game::OutdoorMapData &outdoorGeometry = m_document.mutableOutdoorGeometry();
                Game::OutdoorBModel duplicatedBModel = outdoorGeometry.bmodels[m_selection.index];
                const size_t newBModelIndex = outdoorGeometry.bmodels.size();
                outdoorGeometry.bmodels.push_back(std::move(duplicatedBModel));
                copyBModelSceneReferences(
                    sceneData,
                    m_selection.index,
                    newBModelIndex,
                    sceneData);

                const std::optional<EditorBModelImportSource> sourceImport =
                    m_document.outdoorBModelImportSource(m_selection.index);

                if (sourceImport)
                {
                    m_document.copyOutdoorBModelImportSource(m_selection.index, newBModelIndex);
                }

                m_selection = {EditorSelectionKind::BModel, newBModelIndex};
                duplicatedLabel = "bmodel";
            }
            break;

        case EditorSelectionKind::Entity:
            if (m_selection.index >= sceneData.entities.size())
            {
                errorMessage = "selected entity is out of range";
                return false;
            }
            else
            {
                Game::OutdoorSceneEntity entity = sceneData.entities[m_selection.index];
                entity.entity.x += DuplicateOffset;
                entity.entity.y += DuplicateOffset;
                sceneData.entities.push_back(std::move(entity));
                normalizeOutdoorSceneCollections();
                m_selection = {EditorSelectionKind::Entity, sceneData.entities.size() - 1};
                duplicatedLabel = "entity";
            }
            break;

        case EditorSelectionKind::Spawn:
            if (m_selection.index >= sceneData.spawns.size())
            {
                errorMessage = "selected spawn is out of range";
                return false;
            }
            else
            {
                Game::OutdoorSceneSpawn spawn = sceneData.spawns[m_selection.index];
                spawn.spawn.x += DuplicateOffset;
                spawn.spawn.y += DuplicateOffset;
                sceneData.spawns.push_back(std::move(spawn));
                normalizeOutdoorSceneCollections();
                m_selection = {EditorSelectionKind::Spawn, sceneData.spawns.size() - 1};
                duplicatedLabel = "spawn";
            }
            break;

        case EditorSelectionKind::Actor:
            if (m_selection.index >= sceneData.initialState.actors.size())
            {
                errorMessage = "selected actor is out of range";
                return false;
            }
            else
            {
                Game::MapDeltaActor actor = sceneData.initialState.actors[m_selection.index];
                actor.x += DuplicateOffset;
                actor.y += DuplicateOffset;
                sceneData.initialState.actors.push_back(std::move(actor));
                m_selection = {EditorSelectionKind::Actor, sceneData.initialState.actors.size() - 1};
                duplicatedLabel = "actor";
            }
            break;

        case EditorSelectionKind::SpriteObject:
            if (m_selection.index >= sceneData.initialState.spriteObjects.size())
            {
                errorMessage = "selected sprite object is out of range";
                return false;
            }
            else
            {
                Game::MapDeltaSpriteObject spriteObject = sceneData.initialState.spriteObjects[m_selection.index];
                spriteObject.x += DuplicateOffset;
                spriteObject.y += DuplicateOffset;
                spriteObject.initialX += DuplicateOffset;
                spriteObject.initialY += DuplicateOffset;
                sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
                m_selection = {EditorSelectionKind::SpriteObject, sceneData.initialState.spriteObjects.size() - 1};
                duplicatedLabel = "sprite object";
            }
            break;

        default:
            errorMessage = "selected item cannot be duplicated";
            return false;
        }
    }

    noteDocumentMutated("Duplicated " + duplicatedLabel);
    return true;
}

bool EditorSession::deleteSelectedObject(std::string &errorMessage)
{
    if (!hasDocument())
    {
        errorMessage = "no document is loaded";
        return false;
    }

    captureUndoSnapshot();
    std::string deletedLabel;

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        Game::IndoorMapData &indoorGeometry = m_document.mutableIndoorGeometry();
        Game::IndoorSceneData &sceneData = m_document.mutableIndoorSceneData();

        switch (m_selection.kind)
        {
        case EditorSelectionKind::Entity:
            if (m_selection.index >= indoorGeometry.entities.size())
            {
                errorMessage = "selected decoration is out of range";
                return false;
            }
            else
            {
                indoorGeometry.entities.erase(
                    indoorGeometry.entities.begin() + static_cast<ptrdiff_t>(m_selection.index));
                repairIndoorEntitySectorReferencesAfterDelete(indoorGeometry, m_selection.index);
                indoorGeometry.spriteCount = indoorGeometry.entities.size();
                deletedLabel = "decoration";
                m_selection = indoorGeometry.entities.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::Entity,
                        std::min(m_selection.index, indoorGeometry.entities.size() - 1)};
            }
            break;

        case EditorSelectionKind::Actor:
            if (m_selection.index >= sceneData.initialState.actors.size())
            {
                errorMessage = "selected actor is out of range";
                return false;
            }
            else
            {
                sceneData.initialState.actors.erase(
                    sceneData.initialState.actors.begin() + static_cast<ptrdiff_t>(m_selection.index));
                deletedLabel = "actor";
                m_selection = sceneData.initialState.actors.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::Actor,
                        std::min(m_selection.index, sceneData.initialState.actors.size() - 1)};
            }
            break;

        case EditorSelectionKind::Spawn:
            if (m_selection.index >= indoorGeometry.spawns.size())
            {
                errorMessage = "selected spawn is out of range";
                return false;
            }
            else
            {
                indoorGeometry.spawns.erase(
                    indoorGeometry.spawns.begin() + static_cast<ptrdiff_t>(m_selection.index));
                indoorGeometry.spawnCount = indoorGeometry.spawns.size();
                deletedLabel = "spawn";
                m_selection = indoorGeometry.spawns.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::Spawn,
                        std::min(m_selection.index, indoorGeometry.spawns.size() - 1)};
            }
            break;

        case EditorSelectionKind::SpriteObject:
            if (m_selection.index >= sceneData.initialState.spriteObjects.size())
            {
                errorMessage = "selected sprite object is out of range";
                return false;
            }
            else
            {
                sceneData.initialState.spriteObjects.erase(
                    sceneData.initialState.spriteObjects.begin() + static_cast<ptrdiff_t>(m_selection.index));
                deletedLabel = "sprite object";
                m_selection = sceneData.initialState.spriteObjects.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::SpriteObject,
                        std::min(m_selection.index, sceneData.initialState.spriteObjects.size() - 1)};
            }
            break;

        case EditorSelectionKind::Chest:
            if (m_selection.index >= sceneData.initialState.chests.size())
            {
                errorMessage = "selected chest is out of range";
                return false;
            }
            else
            {
                sceneData.initialState.chests.erase(
                    sceneData.initialState.chests.begin() + static_cast<ptrdiff_t>(m_selection.index));
                deletedLabel = "chest";
                m_selection = sceneData.initialState.chests.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::Chest,
                        std::min(m_selection.index, sceneData.initialState.chests.size() - 1)};
            }
            break;

        case EditorSelectionKind::Door:
            if (m_selection.index >= sceneData.initialState.doors.size())
            {
                errorMessage = "selected door override is out of range";
                return false;
            }
            else
            {
                sceneData.initialState.doors.erase(
                    sceneData.initialState.doors.begin() + static_cast<ptrdiff_t>(m_selection.index));
                deletedLabel = "door override";
                m_selection = sceneData.initialState.doors.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::Door,
                        std::min(m_selection.index, sceneData.initialState.doors.size() - 1)};
            }
            break;

        default:
            errorMessage = "selected indoor item cannot be deleted in Wave 2";
            return false;
        }
    }
    else
    {
        Game::OutdoorSceneData &sceneData = m_document.mutableOutdoorSceneData();

        switch (m_selection.kind)
        {
        case EditorSelectionKind::BModel:
            if (m_selection.index >= m_document.mutableOutdoorGeometry().bmodels.size())
            {
                errorMessage = "selected bmodel is out of range";
                return false;
            }
            else
            {
                Game::OutdoorMapData &outdoorGeometry = m_document.mutableOutdoorGeometry();
                const size_t deletedBModelIndex = m_selection.index;
                outdoorGeometry.bmodels.erase(
                    outdoorGeometry.bmodels.begin() + static_cast<ptrdiff_t>(deletedBModelIndex));
                repairBModelReferencesAfterDelete(sceneData, deletedBModelIndex);

                m_document.eraseOutdoorBModelImportSource(deletedBModelIndex);
                deletedLabel = "bmodel";
                m_selection = outdoorGeometry.bmodels.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::BModel,
                        std::min(deletedBModelIndex, outdoorGeometry.bmodels.size() - 1)};
            }
            break;

        case EditorSelectionKind::Entity:
            if (m_selection.index >= sceneData.entities.size())
            {
                errorMessage = "selected entity is out of range";
                return false;
            }
            else
            {
                sceneData.entities.erase(sceneData.entities.begin() + static_cast<ptrdiff_t>(m_selection.index));
                normalizeOutdoorSceneCollections();
                deletedLabel = "entity";
                m_selection = sceneData.entities.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{EditorSelectionKind::Entity, std::min(m_selection.index, sceneData.entities.size() - 1)};
            }
            break;

        case EditorSelectionKind::Spawn:
            if (m_selection.index >= sceneData.spawns.size())
            {
                errorMessage = "selected spawn is out of range";
                return false;
            }
            else
            {
                sceneData.spawns.erase(sceneData.spawns.begin() + static_cast<ptrdiff_t>(m_selection.index));
                normalizeOutdoorSceneCollections();
                deletedLabel = "spawn";
                m_selection = sceneData.spawns.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{EditorSelectionKind::Spawn, std::min(m_selection.index, sceneData.spawns.size() - 1)};
            }
            break;

        case EditorSelectionKind::Actor:
            if (m_selection.index >= sceneData.initialState.actors.size())
            {
                errorMessage = "selected actor is out of range";
                return false;
            }
            else
            {
                sceneData.initialState.actors.erase(
                    sceneData.initialState.actors.begin() + static_cast<ptrdiff_t>(m_selection.index));
                deletedLabel = "actor";
                m_selection = sceneData.initialState.actors.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::Actor,
                        std::min(m_selection.index, sceneData.initialState.actors.size() - 1)};
            }
            break;

        case EditorSelectionKind::SpriteObject:
            if (m_selection.index >= sceneData.initialState.spriteObjects.size())
            {
                errorMessage = "selected sprite object is out of range";
                return false;
            }
            else
            {
                sceneData.initialState.spriteObjects.erase(
                    sceneData.initialState.spriteObjects.begin() + static_cast<ptrdiff_t>(m_selection.index));
                deletedLabel = "sprite object";
                m_selection = sceneData.initialState.spriteObjects.empty()
                    ? EditorSelection{EditorSelectionKind::Summary, 0}
                    : EditorSelection{
                        EditorSelectionKind::SpriteObject,
                        std::min(m_selection.index, sceneData.initialState.spriteObjects.size() - 1)};
            }
            break;

        default:
            errorMessage = "selected item cannot be deleted";
            return false;
        }
    }

    noteDocumentMutated("Deleted " + deletedLabel);
    return true;
}

bool EditorSession::replaceSelectedBModelFromModel(
    const std::string &sourcePath,
    float importScale,
    const std::string &defaultTextureName,
    const std::string &sourceMeshName,
    bool mergeCoplanarFaces,
    std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        errorMessage = "no outdoor document is loaded";
        return false;
    }

    if (m_selection.kind != EditorSelectionKind::BModel)
    {
        errorMessage = "no bmodel is selected";
        return false;
    }

    const std::string trimmedSourcePath = trimCopy(sourcePath);

    if (trimmedSourcePath.empty())
    {
        errorMessage = "model path is empty";
        return false;
    }

    Game::OutdoorMapData &outdoorGeometry = m_document.mutableOutdoorGeometry();

    if (m_selection.index >= outdoorGeometry.bmodels.size())
    {
        errorMessage = "selected bmodel is out of range";
        return false;
    }

    const std::filesystem::path absoluteSourcePath = std::filesystem::absolute(std::filesystem::path(trimmedSourcePath));
    ImportedModel importedModel = {};
    const std::optional<EditorBModelSourceTransform> existingSourceTransform =
        m_document.outdoorBModelSourceTransform(m_selection.index);
    EditorBModelImportSource importSource = {};
    importSource.sourcePath = absoluteSourcePath.string();
    importSource.importScale = importScale;
    importSource.mergeCoplanarFaces = mergeCoplanarFaces;
    importSource.defaultTextureName = canonicalBitmapTextureName(m_bitmapTextureNames, defaultTextureName);
    const std::optional<EditorBModelImportSource> existingImportSource =
        m_document.outdoorBModelImportSource(m_selection.index);
    const std::string resolvedSourceMeshName = trimCopy(sourceMeshName);

    if (existingImportSource)
    {
        importSource.materialRemaps = existingImportSource->materialRemaps;
    }

    if (!loadImportedModelFromFile(
            absoluteSourcePath,
            importedModel,
            errorMessage,
            resolvedSourceMeshName,
            mergeCoplanarFaces))
    {
        return false;
    }

    bool createdImportedTextures = false;

    if (!materializeImportedModelTextures(
            *m_pAssetFileSystem,
            importedModel,
            absoluteSourcePath,
            m_bitmapTextureNames,
            importSource,
            createdImportedTextures,
            errorMessage))
    {
        return false;
    }

    if (createdImportedTextures)
    {
        buildBitmapTextureNames(*m_pAssetFileSystem, m_bitmapTextureNames);
    }

    importSource.sourceMeshName = resolvedSourceMeshName;

    Game::OutdoorBModel importedBModel = buildImportedBModel(
        *m_pAssetFileSystem,
        m_bitmapTextureNames,
        importedModel,
        absoluteSourcePath,
        importScale,
        importSource,
        &outdoorGeometry.bmodels[m_selection.index],
        existingSourceTransform ? &*existingSourceTransform : nullptr,
        errorMessage);

    if (!errorMessage.empty() && importedBModel.vertices.empty())
    {
        return false;
    }

    captureUndoSnapshot();
    outdoorGeometry.bmodels[m_selection.index] = std::move(importedBModel);
    pruneInteractiveFaceReferences(
        m_document.mutableOutdoorSceneData(),
        m_selection.index,
        outdoorGeometry.bmodels[m_selection.index].faces.size());
    importSource.materialRemaps =
        collectImportedMaterialRemaps(m_bitmapTextureNames, importedModel, outdoorGeometry.bmodels[m_selection.index], importSource.materialRemaps);
    m_document.setOutdoorBModelImportSource(m_selection.index, importSource);
    m_document.setOutdoorBModelSourceTransform(
        m_selection.index,
        existingSourceTransform.value_or(sourceTransformFromBModel(outdoorGeometry.bmodels[m_selection.index])));
    noteDocumentMutated("Replaced bmodel " + std::to_string(m_selection.index) + " from model");
    return true;
}

bool EditorSession::importNewBModelFromModel(
    const std::string &sourcePath,
    float importScale,
    const std::string &defaultTextureName,
    const std::string &sourceMeshName,
    bool splitByMesh,
    bool mergeCoplanarFaces,
    std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        errorMessage = "no outdoor document is loaded";
        return false;
    }

    const std::string trimmedSourcePath = trimCopy(sourcePath);

    if (trimmedSourcePath.empty())
    {
        errorMessage = "model path is empty";
        return false;
    }

    const std::filesystem::path absoluteSourcePath = std::filesystem::absolute(std::filesystem::path(trimmedSourcePath));
    const std::string canonicalDefaultTextureName =
        canonicalBitmapTextureName(m_bitmapTextureNames, defaultTextureName);
    const std::string trimmedSourceMeshName = trimCopy(sourceMeshName);

    if (!splitByMesh)
    {
        ImportedModel importedModel = {};
        EditorBModelImportSource importSource = {};
        importSource.sourcePath = absoluteSourcePath.string();
        importSource.sourceMeshName = trimmedSourceMeshName;
        importSource.importScale = importScale;
        importSource.mergeCoplanarFaces = mergeCoplanarFaces;
        importSource.defaultTextureName = canonicalDefaultTextureName;

        if (!loadImportedModelFromFile(
                absoluteSourcePath,
                importedModel,
                errorMessage,
                trimmedSourceMeshName,
                mergeCoplanarFaces))
        {
            return false;
        }

        bool createdImportedTextures = false;

        if (!materializeImportedModelTextures(
                *m_pAssetFileSystem,
                importedModel,
                absoluteSourcePath,
                m_bitmapTextureNames,
                importSource,
                createdImportedTextures,
                errorMessage))
        {
            return false;
        }

        if (createdImportedTextures)
        {
            buildBitmapTextureNames(*m_pAssetFileSystem, m_bitmapTextureNames);
        }

        Game::OutdoorBModel importedBModel = buildImportedBModel(
            *m_pAssetFileSystem,
            m_bitmapTextureNames,
            importedModel,
            absoluteSourcePath,
            importScale,
            importSource,
            nullptr,
            nullptr,
            errorMessage);

        if (!errorMessage.empty() && importedBModel.vertices.empty())
        {
            return false;
        }

        captureUndoSnapshot();
        Game::OutdoorMapData &outdoorGeometry = m_document.mutableOutdoorGeometry();
        outdoorGeometry.bmodels.push_back(std::move(importedBModel));
        const size_t newIndex = outdoorGeometry.bmodels.size() - 1;
        m_selection = {EditorSelectionKind::BModel, newIndex};
        importSource.materialRemaps =
            collectImportedMaterialRemaps(m_bitmapTextureNames, importedModel, outdoorGeometry.bmodels[newIndex], {});
        m_document.setOutdoorBModelImportSource(newIndex, importSource);
        m_document.setOutdoorBModelSourceTransform(newIndex, sourceTransformFromBModel(outdoorGeometry.bmodels[newIndex]));
        noteDocumentMutated("Imported new bmodel from model");
        return true;
    }

    std::vector<ImportedModel> importedModels;

    if (!loadImportedModelsFromFile(absoluteSourcePath, importedModels, errorMessage, mergeCoplanarFaces))
    {
        return false;
    }

    std::vector<Game::OutdoorBModel> builtBModels;
    std::vector<EditorBModelImportSource> importSources;
    std::vector<EditorBModelSourceTransform> sourceTransforms;
    builtBModels.reserve(importedModels.size());
    importSources.reserve(importedModels.size());
    sourceTransforms.reserve(importedModels.size());

    bool refreshedImportedTextureNames = false;

    for (const ImportedModel &importedModel : importedModels)
    {
        EditorBModelImportSource importSource = {};
        importSource.sourcePath = absoluteSourcePath.string();
        importSource.sourceMeshName = importedModel.name;
        importSource.importScale = importScale;
        importSource.mergeCoplanarFaces = mergeCoplanarFaces;
        importSource.defaultTextureName = canonicalDefaultTextureName;
        bool createdImportedTextures = false;

        if (!materializeImportedModelTextures(
                *m_pAssetFileSystem,
                importedModel,
                absoluteSourcePath,
                m_bitmapTextureNames,
                importSource,
                createdImportedTextures,
                errorMessage))
        {
            return false;
        }

        refreshedImportedTextureNames = refreshedImportedTextureNames || createdImportedTextures;

        Game::OutdoorBModel importedBModel = buildImportedBModel(
            *m_pAssetFileSystem,
            m_bitmapTextureNames,
            importedModel,
            absoluteSourcePath,
            importScale,
            importSource,
            nullptr,
            nullptr,
            errorMessage);

        if (!errorMessage.empty() && importedBModel.vertices.empty())
        {
            return false;
        }

        importSource.materialRemaps =
            collectImportedMaterialRemaps(m_bitmapTextureNames, importedModel, importedBModel, {});
        sourceTransforms.push_back(sourceTransformFromBModel(importedBModel));
        builtBModels.push_back(std::move(importedBModel));
        importSources.push_back(std::move(importSource));
    }

    if (refreshedImportedTextureNames)
    {
        buildBitmapTextureNames(*m_pAssetFileSystem, m_bitmapTextureNames);
    }

    captureUndoSnapshot();
    Game::OutdoorMapData &outdoorGeometry = m_document.mutableOutdoorGeometry();
    const size_t firstNewIndex = outdoorGeometry.bmodels.size();

    for (size_t modelIndex = 0; modelIndex < builtBModels.size(); ++modelIndex)
    {
        outdoorGeometry.bmodels.push_back(std::move(builtBModels[modelIndex]));
        const size_t newIndex = firstNewIndex + modelIndex;
        m_document.setOutdoorBModelImportSource(newIndex, importSources[modelIndex]);
        m_document.setOutdoorBModelSourceTransform(newIndex, sourceTransforms[modelIndex]);
    }

    m_selection = {EditorSelectionKind::BModel, firstNewIndex};
    noteDocumentMutated("Imported " + std::to_string(importedModels.size()) + " bmodels from model");
    return true;
}

bool EditorSession::importIndoorSourceGeometryFromModel(
    const std::string &sourcePath,
    std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Indoor)
    {
        errorMessage = "no indoor document is loaded";
        return false;
    }

    const std::string trimmedSourcePath = trimCopy(sourcePath);

    if (trimmedSourcePath.empty())
    {
        errorMessage = "model path is empty";
        return false;
    }

    IndoorSourceGeometryImportResult importResult = {};

    if (!importIndoorSourceGeometryMetadataFromModel(
            std::filesystem::path(trimmedSourcePath),
            m_document.displayName(),
            importResult,
            errorMessage))
    {
        return false;
    }

    captureUndoSnapshot();
    m_document.mutableIndoorGeometryMetadata() = std::move(importResult.metadata);
    noteDocumentMutated(
        "Imported indoor source geometry metadata from "
        + std::to_string(importResult.importedMeshCount)
        + " meshes");

    for (const std::string &warning : importResult.warnings)
    {
        logInfo("Indoor source import warning: " + warning);
    }

    return true;
}

bool EditorSession::reimportSelectedBModel(std::string &errorMessage)
{
    if (m_selection.kind != EditorSelectionKind::BModel)
    {
        errorMessage = "no bmodel is selected";
        return false;
    }

    const std::optional<EditorBModelImportSource> importSource =
        m_document.outdoorBModelImportSource(m_selection.index);

    if (!importSource)
    {
        errorMessage = "selected bmodel has no remembered import source";
        return false;
    }

    return replaceSelectedBModelFromModel(
        importSource->sourcePath,
        importSource->importScale,
        importSource->defaultTextureName,
        importSource->sourceMeshName,
        importSource->mergeCoplanarFaces,
        errorMessage);
}

bool EditorSession::captureSelectedBModelMaterialRemaps(std::string &errorMessage)
{
    if (m_pAssetFileSystem == nullptr)
    {
        errorMessage = "editor session is not initialized";
        return false;
    }

    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        errorMessage = "no outdoor document is loaded";
        return false;
    }

    if (m_selection.kind != EditorSelectionKind::BModel)
    {
        errorMessage = "no bmodel is selected";
        return false;
    }

    if (m_selection.index >= m_document.outdoorGeometry().bmodels.size())
    {
        errorMessage = "selected bmodel is out of range";
        return false;
    }

    const std::optional<EditorBModelImportSource> existingImportSource =
        m_document.outdoorBModelImportSource(m_selection.index);

    if (!existingImportSource || trimCopy(existingImportSource->sourcePath).empty())
    {
        errorMessage = "selected bmodel has no remembered import source";
        return false;
    }

    ImportedModel importedModel = {};
    const std::filesystem::path sourcePath = std::filesystem::absolute(existingImportSource->sourcePath);

    if (!loadImportedModelFromFile(
            sourcePath,
            importedModel,
            errorMessage,
            existingImportSource->sourceMeshName,
            existingImportSource->mergeCoplanarFaces))
    {
        return false;
    }

    EditorBModelImportSource updatedImportSource = *existingImportSource;
    updatedImportSource.materialRemaps = collectImportedMaterialRemaps(
        m_bitmapTextureNames,
        importedModel,
        m_document.outdoorGeometry().bmodels[m_selection.index],
        {});

    captureUndoSnapshot();
    m_document.setOutdoorBModelImportSource(m_selection.index, updatedImportSource);
    noteDocumentMutated("Captured bmodel material remaps");
    return true;
}

void EditorSession::select(EditorSelectionKind kind, size_t index)
{
    m_selection.kind = kind;
    m_selection.index = index;

    if (kind == EditorSelectionKind::InteractiveFace)
    {
        m_selectedInteractiveFaceIndices.assign(1, index);
    }
    else
    {
        m_selectedInteractiveFaceIndices.clear();
    }
}

void EditorSession::replaceInteractiveFaceSelection(size_t flatIndex)
{
    m_selection = {EditorSelectionKind::InteractiveFace, flatIndex};
    m_selectedInteractiveFaceIndices.assign(1, flatIndex);
}

void EditorSession::addInteractiveFaceSelection(size_t flatIndex)
{
    if (std::find(m_selectedInteractiveFaceIndices.begin(), m_selectedInteractiveFaceIndices.end(), flatIndex)
        == m_selectedInteractiveFaceIndices.end())
    {
        m_selectedInteractiveFaceIndices.push_back(flatIndex);
    }

    m_selection = {EditorSelectionKind::InteractiveFace, flatIndex};
}

void EditorSession::toggleInteractiveFaceSelection(size_t flatIndex)
{
    const auto it =
        std::find(m_selectedInteractiveFaceIndices.begin(), m_selectedInteractiveFaceIndices.end(), flatIndex);

    if (it == m_selectedInteractiveFaceIndices.end())
    {
        m_selectedInteractiveFaceIndices.push_back(flatIndex);
        m_selection = {EditorSelectionKind::InteractiveFace, flatIndex};
        return;
    }

    const bool wasPrimary = m_selection.kind == EditorSelectionKind::InteractiveFace && m_selection.index == flatIndex;
    m_selectedInteractiveFaceIndices.erase(it);

    if (m_selectedInteractiveFaceIndices.empty())
    {
        m_selection = {EditorSelectionKind::Summary, 0};
    }
    else if (wasPrimary)
    {
        m_selection = {EditorSelectionKind::InteractiveFace, m_selectedInteractiveFaceIndices.back()};
    }
}

void EditorSession::clearInteractiveFaceSelection()
{
    m_selectedInteractiveFaceIndices.clear();

    if (m_selection.kind == EditorSelectionKind::InteractiveFace)
    {
        m_selection = {EditorSelectionKind::Summary, 0};
    }
}

bool EditorSession::isInteractiveFaceSelected(size_t flatIndex) const
{
    return std::find(m_selectedInteractiveFaceIndices.begin(), m_selectedInteractiveFaceIndices.end(), flatIndex)
        != m_selectedInteractiveFaceIndices.end();
}

const std::vector<size_t> &EditorSession::selectedInteractiveFaceIndices() const
{
    return m_selectedInteractiveFaceIndices;
}

const EditorSelection &EditorSession::selection() const
{
    return m_selection;
}

const Engine::AssetFileSystem *EditorSession::assetFileSystem() const
{
    return m_pAssetFileSystem;
}

bool EditorSession::hasDocument() const
{
    return m_document.hasDocument();
}

EditorDocument &EditorSession::document()
{
    return m_document;
}

const EditorDocument &EditorSession::document() const
{
    return m_document;
}

const Game::MonsterTable &EditorSession::monsterTable() const
{
    return m_monsterTable;
}

const Game::ChestTable &EditorSession::chestTable() const
{
    return m_chestTable;
}

const Game::MapStats &EditorSession::mapStats() const
{
    return m_mapStats;
}

const Game::MapStatsEntry *EditorSession::currentMapStatsEntry() const
{
    if (!hasDocument() || document().displayName().empty())
    {
        return nullptr;
    }

    return m_mapStats.findByFileName(document().displayName());
}

const Game::ObjectTable &EditorSession::objectTable() const
{
    return m_objectTable;
}

const Game::DecorationTable &EditorSession::decorationTable() const
{
    return m_decorationTable;
}

const Game::ItemTable &EditorSession::itemTable() const
{
    return m_itemTable;
}

const std::vector<EditorIdLabelOption> &EditorSession::monsterOptions() const
{
    return m_monsterOptions;
}

const std::vector<EditorIdLabelOption> &EditorSession::chestOptions() const
{
    return m_chestOptions;
}

const std::vector<EditorIdLabelOption> &EditorSession::decorationOptions() const
{
    return m_decorationOptions;
}

const std::vector<EditorIdLabelOption> &EditorSession::objectOptions() const
{
    return m_objectOptions;
}

const std::vector<EditorIdLabelOption> &EditorSession::itemOptions() const
{
    return m_itemOptions;
}

std::optional<EditorBModelImportSource> EditorSession::bmodelImportSource(size_t bmodelIndex) const
{
    return m_document.outdoorBModelImportSource(bmodelIndex);
}

uint16_t EditorSession::pendingEntityDecorationListId() const
{
    return m_pendingEntityDecorationListId;
}

void EditorSession::setPendingEntityDecorationListId(uint16_t decorationListId)
{
    m_pendingEntityDecorationListId = decorationListId;
}

const Game::OutdoorSpawn &EditorSession::pendingSpawn() const
{
    return m_pendingSpawn;
}

Game::OutdoorSpawn &EditorSession::mutablePendingSpawn()
{
    return m_pendingSpawn;
}

void EditorSession::setPendingSpawn(const Game::OutdoorSpawn &spawn)
{
    m_pendingSpawn = spawn;
}

const Game::MapDeltaActor &EditorSession::pendingActor() const
{
    return m_pendingActor;
}

Game::MapDeltaActor &EditorSession::mutablePendingActor()
{
    return m_pendingActor;
}

void EditorSession::setPendingActor(const Game::MapDeltaActor &actor)
{
    m_pendingActor = actor;
}

uint32_t EditorSession::pendingSpriteObjectItemId() const
{
    return m_pendingSpriteObjectItemId;
}

void EditorSession::setPendingSpriteObjectItemId(uint32_t itemId)
{
    m_pendingSpriteObjectItemId = itemId;
}

uint16_t EditorSession::pendingSpriteObjectDescriptionId() const
{
    return m_pendingSpriteObjectDescriptionId;
}

void EditorSession::setPendingSpriteObjectDescriptionId(uint16_t objectDescriptionId)
{
    m_pendingSpriteObjectDescriptionId = objectDescriptionId;
}

std::optional<uint16_t> EditorSession::objectDescriptionIdForItem(uint32_t itemId) const
{
    const Game::ItemDefinition *pItemDefinition = m_itemTable.get(itemId);

    if (pItemDefinition == nullptr || pItemDefinition->spriteIndex == 0)
    {
        return std::nullopt;
    }

    return m_objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));
}

uint16_t EditorSession::resolvedSpriteObjectObjectDescriptionId(
    const Game::MapDeltaSpriteObject &spriteObject) const
{
    const uint32_t containedItemId = Game::spriteObjectContainedItemId(spriteObject.rawContainingItem);

    if (containedItemId != 0)
    {
        const std::optional<uint16_t> objectDescriptionId = objectDescriptionIdForItem(containedItemId);

        if (objectDescriptionId)
        {
            return *objectDescriptionId;
        }
    }

    return spriteObject.objectDescriptionId;
}

bool EditorSession::isHintOnlyEvent(uint16_t eventId) const
{
    return isResolvedHintOnlyEvent(eventId, m_localScriptedEventProgram, m_globalScriptedEventProgram);
}

std::string EditorSession::itemDisplayName(uint32_t itemId) const
{
    const auto itemIt = m_itemNames.find(itemId);

    if (itemIt != m_itemNames.end())
    {
        return itemIt->second;
    }

    return "Item #" + std::to_string(itemId);
}

const std::vector<std::string> &EditorSession::bitmapTextureNames() const
{
    return m_bitmapTextureNames;
}

std::vector<std::string> EditorSession::usedBitmapTextureNamesInMap() const
{
    std::vector<std::string> result;

    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor || m_pAssetFileSystem == nullptr)
    {
        return result;
    }

    std::unordered_set<std::string> seen;
    const Game::OutdoorMapData &outdoorGeometry = m_document.outdoorGeometry();

    const std::optional<std::vector<std::string>> tileTextureNames =
        Game::loadTerrainTileTextureNames(*m_pAssetFileSystem, outdoorGeometry);

    if (tileTextureNames)
    {
        std::array<bool, 256> usedTileIds = {};

        for (uint8_t tileId : outdoorGeometry.tileMap)
        {
            usedTileIds[tileId] = true;
        }

        for (size_t tileId = 0; tileId < usedTileIds.size(); ++tileId)
        {
            if (usedTileIds[tileId])
            {
                appendUniqueLowerName(result, seen, (*tileTextureNames)[tileId]);
            }
        }
    }

    for (const Game::OutdoorBModel &bmodel : outdoorGeometry.bmodels)
    {
        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            appendUniqueLowerName(result, seen, face.textureName);
        }
    }

    sortTextureNames(result);
    return result;
}

std::vector<std::string> EditorSession::usedBitmapTextureNamesForBModel(size_t bmodelIndex) const
{
    std::vector<std::string> result;

    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        return result;
    }

    const Game::OutdoorMapData &outdoorGeometry = m_document.outdoorGeometry();

    if (bmodelIndex >= outdoorGeometry.bmodels.size())
    {
        return result;
    }

    std::unordered_set<std::string> seen;

    for (const Game::OutdoorBModelFace &face : outdoorGeometry.bmodels[bmodelIndex].faces)
    {
        appendUniqueLowerName(result, seen, face.textureName);
    }

    sortTextureNames(result);
    return result;
}

std::vector<EditorChestContentRecord> EditorSession::decodeChestContents(size_t chestIndex) const
{
    std::vector<EditorChestContentRecord> records;

    if (!hasDocument())
    {
        return records;
    }

    const std::vector<Game::MapDeltaChest> &chests =
        m_document.kind() == EditorDocument::Kind::Indoor
        ? m_document.indoorSceneData().initialState.chests
        : m_document.outdoorSceneData().initialState.chests;

    if (chestIndex >= chests.size())
    {
        return records;
    }

    const Game::MapDeltaChest &chest = chests[chestIndex];

    if (chest.rawItems.size() < ChestItemRecordSize)
    {
        return records;
    }

    const size_t recordCount = chest.rawItems.size() / ChestItemRecordSize;
    records.reserve(recordCount);

    for (size_t recordIndex = 0; recordIndex < recordCount; ++recordIndex)
    {
        int32_t rawItemId = 0;
        std::memcpy(&rawItemId, chest.rawItems.data() + recordIndex * ChestItemRecordSize, sizeof(rawItemId));

        if (rawItemId == 0)
        {
            continue;
        }

        EditorChestContentRecord record = {};
        record.recordIndex = recordIndex;
        record.rawItemId = rawItemId;

        if (rawItemId > 0)
        {
            record.summary = "Fixed item: " + itemDisplayName(rawItemId) + " (#" + std::to_string(rawItemId) + ")";
        }
        else if (rawItemId >= -7)
        {
            record.summary = "Random treasure level " + std::to_string(-rawItemId) + " (may generate gold/items)";
        }
        else
        {
            record.summary = "Reserved legacy chest record " + std::to_string(rawItemId);
        }

        std::vector<std::string> anchors;

        for (size_t cellIndex = 0; cellIndex < chest.inventoryMatrix.size(); ++cellIndex)
        {
            if (chest.inventoryMatrix[cellIndex] != static_cast<int16_t>(recordIndex + 1))
            {
                continue;
            }

            const int column = cellIndex % ChestMatrixColumns;
            const int row = cellIndex / ChestMatrixColumns;
            anchors.push_back("(" + std::to_string(column) + ", " + std::to_string(row) + ")");
        }

        if (anchors.empty())
        {
            record.anchor = "auto";
        }
        else if (anchors.size() == 1)
        {
            record.anchor = anchors.front();
        }
        else
        {
            std::ostringstream anchorStream;
            anchorStream << anchors.front() << " +" << (anchors.size() - 1);
            record.anchor = anchorStream.str();
        }

        records.push_back(std::move(record));
    }

    return records;
}

const Game::SpriteFrameTable *EditorSession::entityBillboardSpriteFrameTable() const
{
    return m_hasEntityBillboardSpriteFrameTable ? &m_entityBillboardSpriteFrameTable : nullptr;
}

const std::vector<EditorEntityBillboardPreview> &EditorSession::entityBillboardPreviews() const
{
    ensureOutdoorDerivedCaches();
    return m_cachedEntityBillboardPreviews;
}

const Game::SpriteFrameTable *EditorSession::actorBillboardSpriteFrameTable() const
{
    ensureOutdoorDerivedCaches();
    return m_hasCachedActorBillboardSpriteFrameTable ? &m_cachedActorBillboardSpriteFrameTable : nullptr;
}

const std::vector<EditorActorBillboardPreview> &EditorSession::actorBillboardPreviews() const
{
    ensureOutdoorDerivedCaches();
    return m_cachedActorBillboardPreviews;
}

const std::vector<std::vector<uint16_t>> &EditorSession::effectiveOutdoorFaceEvents() const
{
    ensureOutdoorDerivedCaches();
    return m_cachedEffectiveFaceEvents;
}

const std::vector<std::optional<uint16_t>> &EditorSession::derivedOutdoorBModelDefaultEvents() const
{
    ensureOutdoorDerivedCaches();
    return m_cachedDefaultBModelEvents;
}

std::optional<std::pair<std::string, int16_t>> EditorSession::previewDecorationTexture(uint16_t decorationListId) const
{
    const Game::DecorationEntry *pDecoration = m_decorationTable.get(decorationListId);
    const Game::SpriteFrameTable *pSpriteFrameTable = entityBillboardSpriteFrameTable();

    if (pDecoration == nullptr || pSpriteFrameTable == nullptr || pDecoration->spriteId == 0)
    {
        return std::nullopt;
    }

    const Game::SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(pDecoration->spriteId, 0);

    if (pFrame == nullptr)
    {
        return std::nullopt;
    }

    const Game::ResolvedSpriteTexture resolvedTexture = Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
    return std::pair<std::string, int16_t>{resolvedTexture.textureName, pFrame->paletteId};
}

std::optional<std::pair<std::string, int16_t>> EditorSession::previewObjectTexture(uint16_t objectDescriptionId) const
{
    const Game::ObjectEntry *pObjectEntry = m_objectTable.get(objectDescriptionId);
    const Game::SpriteFrameTable *pSpriteFrameTable = entityBillboardSpriteFrameTable();

    if (pObjectEntry == nullptr || pSpriteFrameTable == nullptr)
    {
        return std::nullopt;
    }

    uint16_t spriteFrameIndex = pObjectEntry->spriteId;

    if (!pObjectEntry->spriteName.empty())
    {
        const std::optional<uint16_t> frameIndex =
            pSpriteFrameTable->findFrameIndexBySpriteName(pObjectEntry->spriteName);

        if (frameIndex)
        {
            spriteFrameIndex = *frameIndex;
        }
    }

    if (spriteFrameIndex == 0)
    {
        return std::nullopt;
    }

    const Game::SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, 0);

    if (pFrame == nullptr)
    {
        return std::nullopt;
    }

    const Game::ResolvedSpriteTexture resolvedTexture = Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
    return std::pair<std::string, int16_t>{resolvedTexture.textureName, pFrame->paletteId};
}

std::optional<std::pair<std::string, int16_t>> EditorSession::previewMonsterTexture(
    int16_t monsterInfoId,
    int16_t monsterId) const
{
    const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry = m_monsterTable.findDisplayEntryById(monsterInfoId);
    const Game::MonsterEntry *pMonsterEntry = nullptr;

    if (pDisplayEntry != nullptr)
    {
        pMonsterEntry = m_monsterTable.findByInternalName(pDisplayEntry->pictureName);
    }

    if (pMonsterEntry == nullptr && monsterId > 0)
    {
        pMonsterEntry = m_monsterTable.findById(monsterId);
    }

    if (pMonsterEntry == nullptr && monsterInfoId > 0)
    {
        pMonsterEntry = m_monsterTable.findById(monsterInfoId);
    }

    if (pMonsterEntry == nullptr)
    {
        return std::nullopt;
    }

    const Game::SpriteFrameTable *pCachedTable = actorBillboardSpriteFrameTable();

    if (pCachedTable != nullptr)
    {
        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (spriteName.empty())
            {
                continue;
            }

            const std::optional<uint16_t> frameIndex = pCachedTable->findFrameIndexBySpriteName(spriteName);

            if (!frameIndex)
            {
                continue;
            }

            const Game::SpriteFrameEntry *pFrame = pCachedTable->getFrame(*frameIndex, 0);

            if (pFrame != nullptr)
            {
                const Game::ResolvedSpriteTexture resolvedTexture = Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                return std::pair<std::string, int16_t>{resolvedTexture.textureName, pFrame->paletteId};
            }
        }
    }

    if (m_pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    std::unordered_set<std::string> families;
    appendMonsterSpriteFamilies(families, pMonsterEntry);

    if (families.empty())
    {
        return std::nullopt;
    }

    Game::SpriteFrameTable spriteFrameTable = {};

    if (!loadMonsterSpriteFrameTable(*m_pAssetFileSystem, families, spriteFrameTable))
    {
        return std::nullopt;
    }

    for (const std::string &spriteName : pMonsterEntry->spriteNames)
    {
        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (!frameIndex)
        {
            continue;
        }

        const Game::SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(*frameIndex, 0);

        if (pFrame != nullptr)
        {
            const Game::ResolvedSpriteTexture resolvedTexture = Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
            return std::pair<std::string, int16_t>{resolvedTexture.textureName, pFrame->paletteId};
        }
    }

    return std::nullopt;
}

std::optional<std::pair<std::string, int16_t>> EditorSession::previewSpawnMonsterTexture(
    uint16_t typeId,
    uint16_t index) const
{
    const Game::MapStatsEntry *pMapEntry = currentMapStatsEntry();

    if (typeId != 3 || pMapEntry == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<std::string> monsterName = resolveMonsterNameForSpawn(*pMapEntry, typeId, index);

    if (!monsterName)
    {
        return std::nullopt;
    }

    const Game::MonsterEntry *pMonsterEntry = m_monsterTable.findByInternalName(*monsterName);

    if (pMonsterEntry == nullptr)
    {
        return std::nullopt;
    }

    const Game::SpriteFrameTable *pCachedTable = actorBillboardSpriteFrameTable();

    if (pCachedTable != nullptr)
    {
        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (spriteName.empty())
            {
                continue;
            }

            const std::optional<uint16_t> frameIndex = pCachedTable->findFrameIndexBySpriteName(spriteName);

            if (!frameIndex)
            {
                continue;
            }

            const Game::SpriteFrameEntry *pFrame = pCachedTable->getFrame(*frameIndex, 0);

            if (pFrame != nullptr)
            {
                const Game::ResolvedSpriteTexture resolvedTexture =
                    Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                return std::pair<std::string, int16_t>{resolvedTexture.textureName, pFrame->paletteId};
            }
        }
    }

    if (m_pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    std::unordered_set<std::string> families;
    appendMonsterSpriteFamilies(families, pMonsterEntry);

    if (families.empty())
    {
        return std::nullopt;
    }

    Game::SpriteFrameTable spriteFrameTable = {};

    if (!loadMonsterSpriteFrameTable(*m_pAssetFileSystem, families, spriteFrameTable))
    {
        return std::nullopt;
    }

    for (const std::string &spriteName : pMonsterEntry->spriteNames)
    {
        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (!frameIndex)
        {
            continue;
        }

        const Game::SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(*frameIndex, 0);

        if (pFrame != nullptr)
        {
            const Game::ResolvedSpriteTexture resolvedTexture =
                Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
            return std::pair<std::string, int16_t>{resolvedTexture.textureName, pFrame->paletteId};
        }
    }

    return std::nullopt;
}

const std::vector<EditorIdLabelOption> &EditorSession::mapEventOptions() const
{
    return m_mapEventOptions;
}

std::optional<std::string> EditorSession::describeMapEvent(uint16_t eventId) const
{
    return summarizeResolvedEvent(
        eventId,
        m_localScriptedEventProgram,
        m_globalScriptedEventProgram,
        m_localEvtProgram,
        m_globalEvtProgram);
}

std::optional<std::string> EditorSession::localScriptModulePath() const
{
    return m_localScriptModulePath;
}

bool EditorSession::ensurePreviewEventRuntimeState(std::string &errorMessage)
{
    if (!hasDocument())
    {
        errorMessage = "no document is loaded";
        return false;
    }

    const std::string runtimeKey = previewEventRuntimeKey();

    if (runtimeKey == m_previewEventRuntimeKey
        && m_hasPreviewEventRuntimeState)
    {
        return true;
    }

    m_hasPreviewEventRuntimeState = false;
    m_previewEventMapVars = {};
    m_previewEventDecorVars = {};
    m_previewEventVariables.clear();
    m_previewEventMechanisms.clear();
    m_lastPreviewEventId.reset();
    m_lastPreviewEventMessages.clear();
    m_lastPreviewEventStatusMessages.clear();

    Game::MapDeltaData mapDeltaData = {};
    bool builtState = false;

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        Game::IndoorMapData indoorMapData = {};
        builtState = m_document.buildIndoorAuthoredRuntimeState(indoorMapData, mapDeltaData, errorMessage);
    }
    else
    {
        Game::OutdoorMapData outdoorMapData = {};
        builtState = m_document.buildOutdoorAuthoredRuntimeState(outdoorMapData, mapDeltaData, errorMessage);
    }

    if (!builtState)
    {
        return false;
    }

    m_previewEventMapVars = mapDeltaData.eventVariables.mapVars;
    m_previewEventDecorVars = mapDeltaData.eventVariables.decorVars;

    for (const Game::MapDeltaDoor &door : mapDeltaData.doors)
    {
        m_previewEventMechanisms[door.doorId] = buildPreviewMechanismState(door);
    }

    std::vector<std::string> previewActivityMessages;
    EditorPreviewLuaState previewState = {};
    previewState.pMapDeltaData = &mapDeltaData;
    previewState.pMapVars = &m_previewEventMapVars;
    previewState.pDecorVars = &m_previewEventDecorVars;
    previewState.pVariables = &m_previewEventVariables;
    previewState.pMechanisms = &m_previewEventMechanisms;
    previewState.pMessages = &m_lastPreviewEventMessages;
    previewState.pStatusMessages = &m_lastPreviewEventStatusMessages;
    previewState.pActivityMessages = &previewActivityMessages;

    if (!executePreviewEventScripts(
            m_localScriptedEventProgram,
            m_globalScriptedEventProgram,
            previewState,
            errorMessage))
    {
        resetPreviewEventRuntimeState();
        return false;
    }

    m_lastPreviewEventMessages.clear();
    m_lastPreviewEventStatusMessages.clear();

    for (const std::string &message : previewActivityMessages)
    {
        appendLog("evt", message);
    }

    m_hasPreviewEventRuntimeState = true;
    m_previewEventRuntimeKey = runtimeKey;
    return true;
}

void EditorSession::syncPreviewMechanismState(uint32_t mechanismId, uint16_t state, float distance, bool isMoving)
{
    if (!m_hasPreviewEventRuntimeState || mechanismId == 0)
    {
        return;
    }

    EditorPreviewMechanismState &mechanism = m_previewEventMechanisms[mechanismId];
    mechanism.state = state;
    mechanism.currentDistance = distance;
    mechanism.isMoving = isMoving;
}

bool EditorSession::simulateMapEvent(uint16_t eventId, std::string &errorMessage)
{
    if (eventId == 0)
    {
        errorMessage = "event id is zero";
        return false;
    }

    if (!ensurePreviewEventRuntimeState(errorMessage) || !m_hasPreviewEventRuntimeState)
    {
        return false;
    }

    if (!m_localScriptedEventProgram
        && !m_globalScriptedEventProgram)
    {
        errorMessage = "no Lua event program is loaded for this map";
        return false;
    }

    m_lastPreviewEventId = eventId;
    m_lastPreviewEventMessages.clear();
    m_lastPreviewEventStatusMessages.clear();
    std::vector<std::string> previewActivityMessages;
    Game::MapDeltaData mapDeltaData = {};
    bool builtState = false;

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        Game::IndoorMapData indoorMapData = {};
        builtState = m_document.buildIndoorAuthoredRuntimeState(indoorMapData, mapDeltaData, errorMessage);
    }
    else
    {
        Game::OutdoorMapData outdoorMapData = {};
        builtState = m_document.buildOutdoorAuthoredRuntimeState(outdoorMapData, mapDeltaData, errorMessage);
    }

    if (!builtState)
    {
        return false;
    }

    EditorPreviewLuaState previewState = {};
    previewState.pMapDeltaData = &mapDeltaData;
    previewState.pMapVars = &m_previewEventMapVars;
    previewState.pDecorVars = &m_previewEventDecorVars;
    previewState.pVariables = &m_previewEventVariables;
    previewState.pMechanisms = &m_previewEventMechanisms;
    previewState.pMessages = &m_lastPreviewEventMessages;
    previewState.pStatusMessages = &m_lastPreviewEventStatusMessages;
    previewState.pActivityMessages = &previewActivityMessages;

    if (!executePreviewEventScripts(
            m_localScriptedEventProgram,
            m_globalScriptedEventProgram,
            previewState,
            errorMessage,
            eventId))
    {
        return false;
    }

    for (const std::string &message : m_lastPreviewEventStatusMessages)
    {
        appendLog("evt", "status: " + message);
    }

    for (const std::string &message : m_lastPreviewEventMessages)
    {
        appendLog("evt", "message: " + message);
    }

    for (const std::string &message : previewActivityMessages)
    {
        appendLog("evt", message);
    }

    return true;
}

void EditorSession::resetPreviewEventRuntimeState()
{
    m_hasPreviewEventRuntimeState = false;
    m_previewEventMapVars = {};
    m_previewEventDecorVars = {};
    m_previewEventVariables.clear();
    m_previewEventMechanisms.clear();
    m_lastPreviewEventId.reset();
    m_lastPreviewEventMessages.clear();
    m_lastPreviewEventStatusMessages.clear();
    m_previewEventRuntimeKey.clear();
}

std::optional<EditorPreviewMechanismState> EditorSession::previewMechanismState(uint32_t mechanismId) const
{
    const auto iterator = m_previewEventMechanisms.find(mechanismId);
    return iterator != m_previewEventMechanisms.end()
        ? std::optional<EditorPreviewMechanismState>(iterator->second)
        : std::nullopt;
}

std::optional<uint16_t> EditorSession::lastPreviewEventId() const
{
    return m_lastPreviewEventId;
}

const std::vector<std::string> &EditorSession::lastPreviewEventMessages() const
{
    return m_lastPreviewEventMessages;
}

const std::vector<std::string> &EditorSession::lastPreviewEventStatusMessages() const
{
    return m_lastPreviewEventStatusMessages;
}

void EditorSession::ensureOutdoorDerivedCaches() const
{
    if (!hasDocument())
    {
        m_hasCachedOutdoorDerivedState = false;
        m_cachedOutdoorDerivedKind = EditorDocument::Kind::None;
        m_cachedOutdoorDerivedSceneRevision = 0;
        m_cachedOutdoorDerivedPendingActorMonsterInfoId = 0;
        m_cachedOutdoorDerivedPendingActorMonsterId = 0;
        m_cachedOutdoorDerivedPendingSpawnTypeId = 0;
        m_cachedOutdoorDerivedPendingSpawnIndex = 0;
        m_cachedEntityBillboardPreviews.clear();
        m_cachedActorBillboardPreviews.clear();
        m_cachedEffectiveFaceEvents.clear();
        m_cachedDefaultBModelEvents.clear();
        m_cachedChestLinks.clear();
        m_cachedImportedMaterialDiagnostics.clear();
        m_cachedImportedMaterialDiagnosticsValid.clear();
        m_cachedActorBillboardSpriteFrameTable = {};
        m_hasCachedActorBillboardSpriteFrameTable = false;
        return;
    }

    if (m_hasCachedOutdoorDerivedState
        && m_cachedOutdoorDerivedKind == m_document.kind()
        && m_cachedOutdoorDerivedSceneRevision == m_document.sceneRevision()
        && m_cachedOutdoorDerivedPendingActorMonsterInfoId == m_pendingActor.monsterInfoId
        && m_cachedOutdoorDerivedPendingActorMonsterId == m_pendingActor.monsterId
        && m_cachedOutdoorDerivedPendingSpawnTypeId == m_pendingSpawn.typeId
        && m_cachedOutdoorDerivedPendingSpawnIndex == m_pendingSpawn.index)
    {
        return;
    }

    m_cachedEntityBillboardPreviews.clear();
    m_cachedActorBillboardPreviews.clear();
    m_cachedEffectiveFaceEvents.clear();
    m_cachedDefaultBModelEvents.clear();
    m_cachedChestLinks.clear();
    m_cachedImportedMaterialDiagnostics.clear();
    m_cachedActorBillboardSpriteFrameTable = {};
    m_hasCachedActorBillboardSpriteFrameTable = false;

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = m_document.indoorGeometry();
        const Game::IndoorSceneData &sceneData = m_document.indoorSceneData();
        std::unordered_set<std::string> actorFamilies;

        if (m_pAssetFileSystem != nullptr)
        {
            appendMonsterSpriteFamilies(actorFamilies, resolveMonsterEntryForActor(m_monsterTable, m_pendingActor));

            for (const Game::MapDeltaActor &actor : sceneData.initialState.actors)
            {
                const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
                    m_monsterTable.findDisplayEntryById(actor.monsterInfoId);
                const Game::MonsterEntry *pMonsterEntry = nullptr;

                if (pDisplayEntry != nullptr)
                {
                    pMonsterEntry = m_monsterTable.findByInternalName(pDisplayEntry->pictureName);
                }

                if (pMonsterEntry == nullptr)
                {
                    pMonsterEntry = m_monsterTable.findById(actor.monsterId);
                }

                appendMonsterSpriteFamilies(actorFamilies, pMonsterEntry);
            }

            if (const Game::MapStatsEntry *pMapEntry = currentMapStatsEntry())
            {
                if (const std::optional<std::string> monsterName =
                        resolveMonsterNameForSpawn(*pMapEntry, m_pendingSpawn.typeId, m_pendingSpawn.index))
                {
                    appendMonsterSpriteFamilies(actorFamilies, m_monsterTable.findByInternalName(*monsterName));
                }

                for (const Game::IndoorSpawn &spawn : indoorGeometry.spawns)
                {
                    const std::optional<std::string> monsterName =
                        resolveMonsterNameForSpawn(*pMapEntry, spawn.typeId, spawn.index);

                    if (!monsterName)
                    {
                        continue;
                    }

                    appendMonsterSpriteFamilies(actorFamilies, m_monsterTable.findByInternalName(*monsterName));
                }
            }

            if (!actorFamilies.empty())
            {
                m_hasCachedActorBillboardSpriteFrameTable =
                    loadMonsterSpriteFrameTable(
                        *m_pAssetFileSystem,
                        actorFamilies,
                        m_cachedActorBillboardSpriteFrameTable);
            }
        }

        if (m_hasDecorationTable)
        {
            for (size_t entityIndex = 0; entityIndex < indoorGeometry.entities.size(); ++entityIndex)
            {
                const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
                const Game::DecorationEntry *pDecoration = m_decorationTable.get(entity.decorationListId);

                if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
                {
                    pDecoration = m_decorationTable.findByInternalName(entity.name);
                }

                if (pDecoration == nullptr || pDecoration->spriteId == 0)
                {
                    continue;
                }

                EditorEntityBillboardPreview preview = {};
                preview.entityIndex = entityIndex;
                preview.spriteId = pDecoration->spriteId;
                preview.flags = pDecoration->flags;
                preview.height = pDecoration->height;
                preview.radius = pDecoration->radius;
                preview.x = entity.x;
                preview.y = entity.y;
                preview.z = entity.z;
                preview.facing = entity.facing;
                preview.name = entity.name;
                m_cachedEntityBillboardPreviews.push_back(std::move(preview));
            }
        }

        if (m_hasCachedActorBillboardSpriteFrameTable)
        {
            for (size_t actorIndex = 0; actorIndex < sceneData.initialState.actors.size(); ++actorIndex)
            {
                const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
                const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
                    m_monsterTable.findDisplayEntryById(actor.monsterInfoId);
                const Game::MonsterEntry *pMonsterEntry = nullptr;

                if (pDisplayEntry != nullptr)
                {
                    pMonsterEntry = m_monsterTable.findByInternalName(pDisplayEntry->pictureName);
                }

                if (pMonsterEntry == nullptr)
                {
                    pMonsterEntry = m_monsterTable.findById(actor.monsterId);
                }

                uint16_t spriteFrameIndex = 0;

                if (pMonsterEntry != nullptr)
                {
                    for (const std::string &spriteName : pMonsterEntry->spriteNames)
                    {
                        if (spriteName.empty())
                        {
                            continue;
                        }

                        const std::optional<uint16_t> frameIndex =
                            m_cachedActorBillboardSpriteFrameTable.findFrameIndexBySpriteName(spriteName);

                        if (frameIndex)
                        {
                            spriteFrameIndex = *frameIndex;
                            break;
                        }
                    }
                }

                if (spriteFrameIndex == 0)
                {
                    for (uint16_t spriteId : actor.spriteIds)
                    {
                        if (spriteId != 0)
                        {
                            spriteFrameIndex = spriteId;
                            break;
                        }
                    }
                }

                if (spriteFrameIndex == 0)
                {
                    continue;
                }

                EditorActorBillboardPreview preview = {};
                preview.source = EditorActorBillboardPreview::Source::Actor;
                preview.sourceIndex = actorIndex;
                preview.spriteFrameIndex = spriteFrameIndex;
                preview.x = actor.x;
                preview.y = actor.y;
                preview.z = snapIndoorActorZToFloor(indoorGeometry, actor.x, actor.y, actor.z);
                preview.radius = actor.radius;
                preview.height = actor.height;
                preview.name = actor.name;
                m_cachedActorBillboardPreviews.push_back(std::move(preview));
            }

            if (const Game::MapStatsEntry *pMapEntry = currentMapStatsEntry())
            {
                for (size_t spawnIndex = 0; spawnIndex < indoorGeometry.spawns.size(); ++spawnIndex)
                {
                    const Game::IndoorSpawn &spawn = indoorGeometry.spawns[spawnIndex];
                    const std::optional<std::string> monsterName =
                        resolveMonsterNameForSpawn(*pMapEntry, spawn.typeId, spawn.index);

                    if (!monsterName)
                    {
                        continue;
                    }

                    const Game::MonsterEntry *pMonsterEntry = m_monsterTable.findByInternalName(*monsterName);

                    if (pMonsterEntry == nullptr)
                    {
                        continue;
                    }

                    uint16_t spriteFrameIndex = 0;

                    for (const std::string &spriteName : pMonsterEntry->spriteNames)
                    {
                        if (spriteName.empty())
                        {
                            continue;
                        }

                        const std::optional<uint16_t> frameIndex =
                            m_cachedActorBillboardSpriteFrameTable.findFrameIndexBySpriteName(spriteName);

                        if (frameIndex)
                        {
                            spriteFrameIndex = *frameIndex;
                            break;
                        }
                    }

                    if (spriteFrameIndex == 0)
                    {
                        continue;
                    }

                    EditorActorBillboardPreview preview = {};
                    preview.source = EditorActorBillboardPreview::Source::Spawn;
                    preview.sourceIndex = spawnIndex;
                    preview.spriteFrameIndex = spriteFrameIndex;
                    preview.x = spawn.x;
                    preview.y = spawn.y;
                    preview.z = snapIndoorActorZToFloor(indoorGeometry, spawn.x, spawn.y, spawn.z);
                    preview.radius = static_cast<uint16_t>(std::max<int>(pMonsterEntry->radius, 0));
                    preview.height = static_cast<uint16_t>(std::max<int>(pMonsterEntry->height, 0));
                    preview.name = *monsterName;
                    m_cachedActorBillboardPreviews.push_back(std::move(preview));
                }
            }
        }

        m_hasCachedOutdoorDerivedState = true;
        m_cachedOutdoorDerivedKind = m_document.kind();
        m_cachedOutdoorDerivedSceneRevision = m_document.sceneRevision();
        m_cachedOutdoorDerivedPendingActorMonsterInfoId = m_pendingActor.monsterInfoId;
        m_cachedOutdoorDerivedPendingActorMonsterId = m_pendingActor.monsterId;
        m_cachedOutdoorDerivedPendingSpawnTypeId = m_pendingSpawn.typeId;
        m_cachedOutdoorDerivedPendingSpawnIndex = m_pendingSpawn.index;
        return;
    }

    if (m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        m_hasCachedOutdoorDerivedState = true;
        m_cachedOutdoorDerivedKind = m_document.kind();
        m_cachedOutdoorDerivedSceneRevision = m_document.sceneRevision();
        m_cachedOutdoorDerivedPendingActorMonsterInfoId = m_pendingActor.monsterInfoId;
        m_cachedOutdoorDerivedPendingActorMonsterId = m_pendingActor.monsterId;
        m_cachedOutdoorDerivedPendingSpawnTypeId = m_pendingSpawn.typeId;
        m_cachedOutdoorDerivedPendingSpawnIndex = m_pendingSpawn.index;
        return;
    }

    const Game::OutdoorSceneData &sceneData = m_document.outdoorSceneData();
    const Game::OutdoorMapData &outdoorGeometry = m_document.outdoorGeometry();
    m_cachedEffectiveFaceEvents.resize(outdoorGeometry.bmodels.size());
    m_cachedDefaultBModelEvents.resize(outdoorGeometry.bmodels.size());
    m_cachedChestLinks.resize(sceneData.initialState.chests.size());
    m_cachedImportedMaterialDiagnostics.resize(outdoorGeometry.bmodels.size());
    m_cachedImportedMaterialDiagnosticsValid.assign(outdoorGeometry.bmodels.size(), false);

    if (m_pAssetFileSystem != nullptr)
    {
        std::unordered_set<std::string> actorFamilies;

        appendMonsterSpriteFamilies(actorFamilies, resolveMonsterEntryForActor(m_monsterTable, m_pendingActor));

        for (const Game::MapDeltaActor &actor : sceneData.initialState.actors)
        {
            const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
                m_monsterTable.findDisplayEntryById(actor.monsterInfoId);
            const Game::MonsterEntry *pMonsterEntry = nullptr;

            if (pDisplayEntry != nullptr)
            {
                pMonsterEntry = m_monsterTable.findByInternalName(pDisplayEntry->pictureName);
            }

            if (pMonsterEntry == nullptr)
            {
                pMonsterEntry = m_monsterTable.findById(actor.monsterId);
            }

            appendMonsterSpriteFamilies(actorFamilies, pMonsterEntry);
        }

        if (const Game::MapStatsEntry *pMapEntry = currentMapStatsEntry())
        {
            if (const std::optional<std::string> monsterName =
                    resolveMonsterNameForSpawn(*pMapEntry, m_pendingSpawn.typeId, m_pendingSpawn.index))
            {
                appendMonsterSpriteFamilies(actorFamilies, m_monsterTable.findByInternalName(*monsterName));
            }

            for (const Game::OutdoorSceneSpawn &spawn : sceneData.spawns)
            {
                const std::optional<std::string> monsterName =
                    resolveMonsterNameForSpawn(*pMapEntry, spawn.spawn.typeId, spawn.spawn.index);

                if (!monsterName)
                {
                    continue;
                }

                appendMonsterSpriteFamilies(actorFamilies, m_monsterTable.findByInternalName(*monsterName));
            }
        }

        if (!actorFamilies.empty())
        {
            m_hasCachedActorBillboardSpriteFrameTable =
                loadMonsterSpriteFrameTable(
                    *m_pAssetFileSystem,
                    actorFamilies,
                    m_cachedActorBillboardSpriteFrameTable);
        }
    }

    if (m_hasCachedActorBillboardSpriteFrameTable)
    {
        for (size_t actorIndex = 0; actorIndex < sceneData.initialState.actors.size(); ++actorIndex)
        {
            const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
            const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
                m_monsterTable.findDisplayEntryById(actor.monsterInfoId);
            const Game::MonsterEntry *pMonsterEntry = nullptr;

            if (pDisplayEntry != nullptr)
            {
                pMonsterEntry = m_monsterTable.findByInternalName(pDisplayEntry->pictureName);
            }

            if (pMonsterEntry == nullptr)
            {
                pMonsterEntry = m_monsterTable.findById(actor.monsterId);
            }

            uint16_t spriteFrameIndex = 0;

            if (pMonsterEntry != nullptr)
            {
                for (const std::string &spriteName : pMonsterEntry->spriteNames)
                {
                    if (spriteName.empty())
                    {
                        continue;
                    }

                    const std::optional<uint16_t> frameIndex =
                        m_cachedActorBillboardSpriteFrameTable.findFrameIndexBySpriteName(spriteName);

                    if (frameIndex)
                    {
                        spriteFrameIndex = *frameIndex;
                        break;
                    }
                }
            }

            if (spriteFrameIndex == 0)
            {
                for (uint16_t spriteId : actor.spriteIds)
                {
                    if (spriteId != 0)
                    {
                        spriteFrameIndex = spriteId;
                        break;
                    }
                }
            }

            if (spriteFrameIndex == 0)
            {
                continue;
            }

            EditorActorBillboardPreview preview = {};
            preview.source = EditorActorBillboardPreview::Source::Actor;
            preview.sourceIndex = actorIndex;
            preview.spriteFrameIndex = spriteFrameIndex;
            preview.x = actor.x;
            preview.y = actor.y;
            preview.z = actor.z;
            preview.radius = actor.radius;
            preview.height = actor.height;
            preview.name = actor.name;
            m_cachedActorBillboardPreviews.push_back(std::move(preview));
        }

        if (const Game::MapStatsEntry *pMapEntry = currentMapStatsEntry())
        {
            for (size_t spawnIndex = 0; spawnIndex < sceneData.spawns.size(); ++spawnIndex)
            {
                const Game::OutdoorSpawn &spawn = sceneData.spawns[spawnIndex].spawn;
                const std::optional<std::string> monsterName =
                    resolveMonsterNameForSpawn(*pMapEntry, spawn.typeId, spawn.index);

                if (!monsterName)
                {
                    continue;
                }

                const Game::MonsterEntry *pMonsterEntry = m_monsterTable.findByInternalName(*monsterName);

                if (pMonsterEntry == nullptr)
                {
                    continue;
                }

                uint16_t spriteFrameIndex = 0;

                for (const std::string &spriteName : pMonsterEntry->spriteNames)
                {
                    if (spriteName.empty())
                    {
                        continue;
                    }

                    const std::optional<uint16_t> frameIndex =
                        m_cachedActorBillboardSpriteFrameTable.findFrameIndexBySpriteName(spriteName);

                    if (frameIndex)
                    {
                        spriteFrameIndex = *frameIndex;
                        break;
                    }
                }

                if (spriteFrameIndex == 0)
                {
                    continue;
                }

                EditorActorBillboardPreview preview = {};
                preview.source = EditorActorBillboardPreview::Source::Spawn;
                preview.sourceIndex = spawnIndex;
                preview.spriteFrameIndex = spriteFrameIndex;
                preview.x = spawn.x;
                preview.y = spawn.y;
                preview.z = spawn.z;
                preview.radius = static_cast<uint16_t>(std::max<int>(pMonsterEntry->radius, 0));
                preview.height = static_cast<uint16_t>(std::max<int>(pMonsterEntry->height, 0));
                preview.name = *monsterName;
                m_cachedActorBillboardPreviews.push_back(std::move(preview));
            }
        }
    }

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
        std::vector<uint16_t> &faceEvents = m_cachedEffectiveFaceEvents[bmodelIndex];
        faceEvents.resize(bmodel.faces.size());

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            faceEvents[faceIndex] = bmodel.faces[faceIndex].cogTriggeredNumber;
        }
    }

    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex >= m_cachedEffectiveFaceEvents.size())
        {
            continue;
        }

        std::vector<uint16_t> &faceEvents = m_cachedEffectiveFaceEvents[interactiveFace.bmodelIndex];

        if (interactiveFace.faceIndex >= faceEvents.size())
        {
            continue;
        }

        faceEvents[interactiveFace.faceIndex] = interactiveFace.cogTriggeredNumber;
    }

    std::unordered_map<uint16_t, std::vector<uint32_t>> openedChestIdsByEventId;
    const auto resolveOpenedChestIds = [this, &openedChestIdsByEventId](uint16_t eventId) -> const std::vector<uint32_t> &
    {
        const auto existingIt = openedChestIdsByEventId.find(eventId);

        if (existingIt != openedChestIdsByEventId.end())
        {
            return existingIt->second;
        }

        return openedChestIdsByEventId.emplace(
            eventId,
            getOpenedChestIds(
                eventId,
                m_localScriptedEventProgram,
                m_globalScriptedEventProgram,
                m_localEvtProgram,
                m_globalEvtProgram)).first->second;
    };

    for (size_t bmodelIndex = 0; bmodelIndex < m_cachedEffectiveFaceEvents.size(); ++bmodelIndex)
    {
        std::unordered_map<uint16_t, int> eventCounts;
        const std::vector<uint16_t> &faceEvents = m_cachedEffectiveFaceEvents[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < faceEvents.size(); ++faceIndex)
        {
            const uint16_t eventId = faceEvents[faceIndex];

            if (eventId == 0)
            {
                continue;
            }

            ++eventCounts[eventId];

            const std::vector<uint32_t> &chestIds = resolveOpenedChestIds(eventId);

            for (uint32_t chestId : chestIds)
            {
                if (chestId >= m_cachedChestLinks.size())
                {
                    continue;
                }

                EditorChestLink link = {};
                link.kind = EditorChestLink::Kind::Face;
                link.bmodelIndex = bmodelIndex;
                link.faceIndex = faceIndex;
                link.eventId = eventId;
                m_cachedChestLinks[chestId].push_back(std::move(link));
            }
        }

        uint16_t bestEventId = 0;
        int bestCount = 0;

        for (const auto &[eventId, count] : eventCounts)
        {
            if (count > 15 && count > bestCount)
            {
                bestEventId = eventId;
                bestCount = count;
            }
        }

        if (bestEventId != 0)
        {
            m_cachedDefaultBModelEvents[bmodelIndex] = bestEventId;
        }
    }

    for (size_t entityIndex = 0; entityIndex < sceneData.entities.size(); ++entityIndex)
    {
        const Game::OutdoorEntity &entity = sceneData.entities[entityIndex].entity;

        if (m_hasDecorationTable)
        {
            const Game::DecorationEntry *pDecoration = m_decorationTable.get(entity.decorationListId);

            if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
            {
                pDecoration = m_decorationTable.findByInternalName(entity.name);
            }

            if (pDecoration != nullptr && pDecoration->spriteId != 0)
            {
                EditorEntityBillboardPreview preview = {};
                preview.entityIndex = entityIndex;
                preview.spriteId = pDecoration->spriteId;
                preview.flags = pDecoration->flags;
                preview.height = pDecoration->height;
                preview.radius = pDecoration->radius;
                preview.x = entity.x;
                preview.y = entity.y;
                preview.z = entity.z;
                preview.facing = entity.facing;
                preview.name = entity.name;
                m_cachedEntityBillboardPreviews.push_back(std::move(preview));
            }
        }

        for (uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
        {
            const std::vector<uint32_t> &chestIds = resolveOpenedChestIds(eventId);

            for (uint32_t chestId : chestIds)
            {
                if (chestId >= m_cachedChestLinks.size())
                {
                    continue;
                }

                EditorChestLink link = {};
                link.kind = EditorChestLink::Kind::Entity;
                link.entityIndex = entityIndex;
                link.eventId = eventId;
                m_cachedChestLinks[chestId].push_back(std::move(link));
            }
        }
    }

    m_hasCachedOutdoorDerivedState = true;
    m_cachedOutdoorDerivedKind = m_document.kind();
    m_cachedOutdoorDerivedSceneRevision = m_document.sceneRevision();
    m_cachedOutdoorDerivedPendingActorMonsterInfoId = m_pendingActor.monsterInfoId;
    m_cachedOutdoorDerivedPendingActorMonsterId = m_pendingActor.monsterId;
    m_cachedOutdoorDerivedPendingSpawnTypeId = m_pendingSpawn.typeId;
    m_cachedOutdoorDerivedPendingSpawnIndex = m_pendingSpawn.index;
}

uint16_t EditorSession::effectiveOutdoorFaceEventId(size_t bmodelIndex, size_t faceIndex) const
{
    ensureOutdoorDerivedCaches();

    if (bmodelIndex >= m_cachedEffectiveFaceEvents.size() || faceIndex >= m_cachedEffectiveFaceEvents[bmodelIndex].size())
    {
        return 0;
    }

    return m_cachedEffectiveFaceEvents[bmodelIndex][faceIndex];
}

std::optional<uint16_t> EditorSession::derivedBModelDefaultEventId(size_t bmodelIndex) const
{
    ensureOutdoorDerivedCaches();

    if (bmodelIndex >= m_cachedDefaultBModelEvents.size())
    {
        return std::nullopt;
    }

    return m_cachedDefaultBModelEvents[bmodelIndex];
}

std::vector<EditorChestLink> EditorSession::findChestLinks(size_t chestIndex) const
{
    ensureOutdoorDerivedCaches();

    if (chestIndex >= m_cachedChestLinks.size())
    {
        return {};
    }

    return m_cachedChestLinks[chestIndex];
}

const std::vector<EditorImportedMaterialDiagnostic> &EditorSession::importedMaterialDiagnostics(size_t bmodelIndex) const
{
    ensureOutdoorDerivedCaches();

    static const std::vector<EditorImportedMaterialDiagnostic> EmptyDiagnostics;

    if (m_pAssetFileSystem == nullptr
        || bmodelIndex >= m_cachedImportedMaterialDiagnostics.size()
        || bmodelIndex >= m_cachedImportedMaterialDiagnosticsValid.size())
    {
        return EmptyDiagnostics;
    }

    if (m_cachedImportedMaterialDiagnosticsValid[bmodelIndex])
    {
        return m_cachedImportedMaterialDiagnostics[bmodelIndex];
    }

    const std::optional<EditorBModelImportSource> importSource = m_document.outdoorBModelImportSource(bmodelIndex);

    if (!importSource || trimCopy(importSource->sourcePath).empty())
    {
        m_cachedImportedMaterialDiagnosticsValid[bmodelIndex] = true;
        return m_cachedImportedMaterialDiagnostics[bmodelIndex];
    }

    ImportedModel importedModel = {};
    std::string errorMessage;

    if (!loadImportedModelFromFile(
            std::filesystem::absolute(importSource->sourcePath),
            importedModel,
            errorMessage,
            importSource->sourceMeshName,
            importSource->mergeCoplanarFaces))
    {
        m_cachedImportedMaterialDiagnosticsValid[bmodelIndex] = true;
        return m_cachedImportedMaterialDiagnostics[bmodelIndex];
    }

    m_cachedImportedMaterialDiagnostics[bmodelIndex] =
        buildImportedMaterialDiagnostics(m_bitmapTextureNames, importedModel, *importSource);
    m_cachedImportedMaterialDiagnosticsValid[bmodelIndex] = true;
    return m_cachedImportedMaterialDiagnostics[bmodelIndex];
}

uint8_t EditorSession::terrainPaintTileId() const
{
    return m_terrainPaintTileId;
}

void EditorSession::setTerrainPaintTileId(uint8_t tileId)
{
    m_terrainPaintTileId = tileId;
}

EditorTerrainPaintMode EditorSession::terrainPaintMode() const
{
    return m_terrainPaintMode;
}

void EditorSession::setTerrainPaintMode(EditorTerrainPaintMode mode)
{
    m_terrainPaintMode = mode;
}

int EditorSession::terrainPaintRadius() const
{
    return m_terrainPaintRadius;
}

void EditorSession::setTerrainPaintRadius(int radius)
{
    m_terrainPaintRadius = std::clamp(radius, 0, 32);
}

int EditorSession::terrainPaintEdgeNoise() const
{
    return m_terrainPaintEdgeNoise;
}

void EditorSession::setTerrainPaintEdgeNoise(int edgeNoise)
{
    m_terrainPaintEdgeNoise = std::clamp(edgeNoise, 0, 100);
}

bool EditorSession::terrainPaintEnabled() const
{
    return m_terrainPaintEnabled;
}

void EditorSession::setTerrainPaintEnabled(bool enabled)
{
    m_terrainPaintEnabled = enabled;
}

bool EditorSession::terrainSculptEnabled() const
{
    return m_terrainSculptEnabled;
}

void EditorSession::setTerrainSculptEnabled(bool enabled)
{
    m_terrainSculptEnabled = enabled;
}

EditorTerrainSculptMode EditorSession::terrainSculptMode() const
{
    return m_terrainSculptMode;
}

void EditorSession::setTerrainSculptMode(EditorTerrainSculptMode mode)
{
    m_terrainSculptMode = mode;
}

int EditorSession::terrainSculptRadius() const
{
    return m_terrainSculptRadius;
}

void EditorSession::setTerrainSculptRadius(int radius)
{
    m_terrainSculptRadius = std::clamp(radius, 0, 48);
}

int EditorSession::terrainSculptStrength() const
{
    return m_terrainSculptStrength;
}

void EditorSession::setTerrainSculptStrength(int strength)
{
    m_terrainSculptStrength = std::clamp(strength, 1, 32);
}

EditorTerrainFalloffMode EditorSession::terrainSculptFalloffMode() const
{
    return m_terrainSculptFalloffMode;
}

void EditorSession::setTerrainSculptFalloffMode(EditorTerrainFalloffMode mode)
{
    m_terrainSculptFalloffMode = mode;
}

EditorTerrainFlattenTargetMode EditorSession::terrainFlattenTargetMode() const
{
    return m_terrainFlattenTargetMode;
}

void EditorSession::setTerrainFlattenTargetMode(EditorTerrainFlattenTargetMode mode)
{
    m_terrainFlattenTargetMode = mode;
}

int EditorSession::terrainFlattenTargetHeight() const
{
    return m_terrainFlattenTargetHeight;
}

void EditorSession::setTerrainFlattenTargetHeight(int height)
{
    m_terrainFlattenTargetHeight = std::clamp(height, 0, 255);
}

bool EditorSession::hasTerrainFlattenSampledTarget() const
{
    return m_hasTerrainFlattenSampledTarget;
}

void EditorSession::setTerrainFlattenSampledTargetHeight(int height)
{
    m_terrainFlattenTargetHeight = std::clamp(height, 0, 255);
    m_hasTerrainFlattenSampledTarget = true;
}

void EditorSession::logInfo(const std::string &message)
{
    appendLog("info", message);
}

void EditorSession::logError(const std::string &message)
{
    appendLog("error", message);
}

const std::vector<std::string> &EditorSession::logMessages() const
{
    return m_logMessages;
}

const std::vector<std::string> &EditorSession::validationMessages() const
{
    return m_validationMessages;
}

void EditorSession::appendLog(const std::string &prefix, const std::string &message)
{
    m_logMessages.push_back('[' + prefix + "] " + message);

    if (m_logMessages.size() > 256)
    {
        m_logMessages.erase(m_logMessages.begin(), m_logMessages.begin() + 64);
    }
}

void EditorSession::refreshValidation()
{
    if (!hasDocument())
    {
        m_validationMessages.clear();
        return;
    }

    m_validationMessages = m_document.validate();

    if (m_document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = m_document.indoorGeometry();
        const Game::IndoorSceneData &sceneData = m_document.indoorSceneData();
        std::unordered_set<std::string> knownBitmapNames;

        for (const std::string &textureName : m_bitmapTextureNames)
        {
            knownBitmapNames.insert(toLowerCopy(textureName));
        }

        size_t faceTooFewVerticesCount = 0;
        std::string faceTooFewVerticesExample;
        size_t invalidFaceVertexIndexCount = 0;
        std::string invalidFaceVertexIndexExample;
        size_t degenerateFaceCount = 0;
        std::string degenerateFaceExample;
        size_t emptyTextureFaceCount = 0;
        std::string emptyTextureFaceExample;
        size_t missingTextureFaceCount = 0;
        std::string missingTextureFaceExample;
        size_t missingEntityEventCount = 0;
        std::string missingEntityEventExample;
        size_t missingFaceEventCount = 0;
        std::string missingFaceEventExample;

        for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
        {
            const Game::IndoorFace &face = indoorGeometry.faces[faceIndex];

            if (face.vertexIndices.size() < 3)
            {
                recordSummarizedIssue(
                    faceTooFewVerticesCount,
                    faceTooFewVerticesExample,
                    "Face " + std::to_string(faceIndex) + " has fewer than 3 vertices.");
                continue;
            }

            bool hasInvalidVertexIndex = false;

            for (uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= indoorGeometry.vertices.size())
                {
                    hasInvalidVertexIndex = true;
                    break;
                }
            }

            if (hasInvalidVertexIndex)
            {
                recordSummarizedIssue(
                    invalidFaceVertexIndexCount,
                    invalidFaceVertexIndexExample,
                    "Face " + std::to_string(faceIndex) + " references an invalid vertex index.");
                continue;
            }

            Game::IndoorFaceGeometryData geometry = {};

            if (Game::buildIndoorFaceGeometry(indoorGeometry, indoorGeometry.vertices, faceIndex, geometry))
            {
                const float normalLengthSquared =
                    geometry.normal.x * geometry.normal.x
                    + geometry.normal.y * geometry.normal.y
                    + geometry.normal.z * geometry.normal.z;

                if (normalLengthSquared <= 0.01f)
                {
                    recordSummarizedIssue(
                        degenerateFaceCount,
                        degenerateFaceExample,
                        "Face " + std::to_string(faceIndex) + " is degenerate.");
                }
            }

            const std::string textureName = toLowerCopy(trimCopy(face.textureName));

            if (textureName.empty())
            {
                recordSummarizedIssue(
                    emptyTextureFaceCount,
                    emptyTextureFaceExample,
                    "Face " + std::to_string(faceIndex) + " has an empty texture name.");
            }
            else if (!knownBitmapNames.empty() && !knownBitmapNames.contains(textureName))
            {
                recordSummarizedIssue(
                    missingTextureFaceCount,
                    missingTextureFaceExample,
                    "Face " + std::to_string(faceIndex) + " uses missing texture '" + face.textureName + "'.");
            }

            Game::IndoorFace effectiveFace = face;

            if (const Game::IndoorSceneFaceAttributeOverride *pOverride =
                    Game::findIndoorSceneFaceOverride(sceneData, faceIndex))
            {
                Game::applyIndoorSceneFaceOverride(*pOverride, effectiveFace);
            }

            const uint16_t eventId = effectiveFace.cogTriggered;

            if (eventId != 0 && !hasResolvedEvent(
                    eventId,
                    m_localScriptedEventProgram,
                    m_globalScriptedEventProgram,
                    m_localEvtProgram,
                    m_globalEvtProgram))
            {
                recordSummarizedIssue(
                    missingFaceEventCount,
                    missingFaceEventExample,
                    "Face " + std::to_string(faceIndex) + " references missing event " + std::to_string(eventId) + ".");
            }
        }

        for (size_t entityIndex = 0; entityIndex < indoorGeometry.entities.size(); ++entityIndex)
        {
            const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];

            for (uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
            {
                if (!hasResolvedEvent(
                        eventId,
                        m_localScriptedEventProgram,
                        m_globalScriptedEventProgram,
                        m_localEvtProgram,
                        m_globalEvtProgram))
                {
                    recordSummarizedIssue(
                        missingEntityEventCount,
                        missingEntityEventExample,
                        "Entity " + std::to_string(entityIndex) + " references missing event "
                            + std::to_string(eventId) + ".");
                }
            }
        }

        appendSummarizedIssue(
            m_validationMessages,
            faceTooFewVerticesCount,
            "faces have fewer than 3 vertices.",
            faceTooFewVerticesExample);
        appendSummarizedIssue(
            m_validationMessages,
            invalidFaceVertexIndexCount,
            "faces reference invalid vertex indices.",
            invalidFaceVertexIndexExample);
        appendSummarizedIssue(
            m_validationMessages,
            degenerateFaceCount,
            "faces are degenerate.",
            degenerateFaceExample);
        appendSummarizedIssue(
            m_validationMessages,
            emptyTextureFaceCount,
            "faces have empty texture names.",
            emptyTextureFaceExample);
        appendSummarizedIssue(
            m_validationMessages,
            missingTextureFaceCount,
            "faces use missing textures.",
            missingTextureFaceExample);
        appendSummarizedIssue(
            m_validationMessages,
            missingEntityEventCount,
            "entity event references are unresolved.",
            missingEntityEventExample);
        appendSummarizedIssue(
            m_validationMessages,
            missingFaceEventCount,
            "face event references are unresolved.",
            missingFaceEventExample);
        return;
    }

    const Game::OutdoorMapData &outdoorGeometry = m_document.outdoorGeometry();
    const Game::OutdoorSceneData &sceneData = m_document.outdoorSceneData();
    std::unordered_set<std::string> knownBitmapNames;

    for (const std::string &textureName : m_bitmapTextureNames)
    {
        knownBitmapNames.insert(toLowerCopy(textureName));
    }

    std::unordered_set<size_t> seenTerrainOverrides;
    size_t faceTooFewVerticesCount = 0;
    std::string faceTooFewVerticesExample;
    size_t invalidFaceVertexIndexCount = 0;
    std::string invalidFaceVertexIndexExample;
    size_t degenerateFaceCount = 0;
    std::string degenerateFaceExample;
    size_t emptyTextureFaceCount = 0;
    std::string emptyTextureFaceExample;
    size_t missingTextureFaceCount = 0;
    std::string missingTextureFaceExample;
    size_t invalidImportedSourceCount = 0;
    std::string invalidImportedSourceExample;
    size_t unresolvedImportedMaterialBindingCount = 0;
    std::string unresolvedImportedMaterialBindingExample;
    size_t missingEntityEventCount = 0;
    std::string missingEntityEventExample;
    size_t missingFaceEventCount = 0;
    std::string missingFaceEventExample;

    for (const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        const size_t flatIndex = static_cast<size_t>(overrideEntry.y) * Game::OutdoorMapData::TerrainWidth
            + static_cast<size_t>(overrideEntry.x);

        if (!seenTerrainOverrides.insert(flatIndex).second)
        {
            appendIssue(
                m_validationMessages,
                "Terrain override (" + std::to_string(overrideEntry.x) + ", "
                    + std::to_string(overrideEntry.y) + ") is duplicated.");
        }
    }

    std::unordered_set<std::string> seenInteractiveFaces;

    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        const std::string key = std::to_string(interactiveFace.bmodelIndex) + ":" + std::to_string(interactiveFace.faceIndex);

        if (!seenInteractiveFaces.insert(key).second)
        {
            appendIssue(
                m_validationMessages,
                "Interactive face (" + std::to_string(interactiveFace.bmodelIndex) + ", "
                    + std::to_string(interactiveFace.faceIndex) + ") is duplicated.");
        }
    }

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

            if (face.vertexIndices.size() < 3)
            {
                recordSummarizedIssue(
                    faceTooFewVerticesCount,
                    faceTooFewVerticesExample,
                    "BModel " + std::to_string(bmodelIndex) + " face " + std::to_string(faceIndex)
                        + " has fewer than 3 vertices.");
                continue;
            }

            bool hasInvalidVertexIndex = false;

            for (uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= bmodel.vertices.size())
                {
                    hasInvalidVertexIndex = true;
                    break;
                }
            }

            if (hasInvalidVertexIndex)
            {
                recordSummarizedIssue(
                    invalidFaceVertexIndexCount,
                    invalidFaceVertexIndexExample,
                    "BModel " + std::to_string(bmodelIndex) + " face " + std::to_string(faceIndex)
                        + " references an invalid vertex index.");
                continue;
            }

            const Game::OutdoorBModelVertex &a = bmodel.vertices[face.vertexIndices[0]];
            const Game::OutdoorBModelVertex &b = bmodel.vertices[face.vertexIndices[1]];
            const Game::OutdoorBModelVertex &c = bmodel.vertices[face.vertexIndices[2]];
            const float abX = static_cast<float>(b.x - a.x);
            const float abY = static_cast<float>(b.y - a.y);
            const float abZ = static_cast<float>(b.z - a.z);
            const float acX = static_cast<float>(c.x - a.x);
            const float acY = static_cast<float>(c.y - a.y);
            const float acZ = static_cast<float>(c.z - a.z);
            const float normalX = abY * acZ - abZ * acY;
            const float normalY = abZ * acX - abX * acZ;
            const float normalZ = abX * acY - abY * acX;
            const float normalLengthSquared = normalX * normalX + normalY * normalY + normalZ * normalZ;

            if (normalLengthSquared <= 0.01f)
            {
                recordSummarizedIssue(
                    degenerateFaceCount,
                    degenerateFaceExample,
                    "BModel " + std::to_string(bmodelIndex) + " face " + std::to_string(faceIndex)
                        + " is degenerate.");
            }

            const std::string textureName = toLowerCopy(trimCopy(face.textureName));

            if (textureName.empty())
            {
                recordSummarizedIssue(
                    emptyTextureFaceCount,
                    emptyTextureFaceExample,
                    "BModel " + std::to_string(bmodelIndex) + " face " + std::to_string(faceIndex)
                        + " has an empty texture name.");
            }
            else if (!knownBitmapNames.empty() && !knownBitmapNames.contains(textureName))
            {
                recordSummarizedIssue(
                    missingTextureFaceCount,
                    missingTextureFaceExample,
                    "BModel " + std::to_string(bmodelIndex) + " face " + std::to_string(faceIndex)
                        + " uses missing texture '" + face.textureName + "'.");
            }
        }

        const std::optional<EditorBModelImportSource> importSource = m_document.outdoorBModelImportSource(bmodelIndex);

        if (!importSource || trimCopy(importSource->sourcePath).empty())
        {
            continue;
        }

        ImportedModel importedModel = {};
        std::string importErrorMessage;

        if (!loadImportedModelFromFile(
                std::filesystem::absolute(importSource->sourcePath),
                importedModel,
                importErrorMessage,
                importSource->sourceMeshName,
                importSource->mergeCoplanarFaces))
        {
            recordSummarizedIssue(
                invalidImportedSourceCount,
                invalidImportedSourceExample,
                "BModel " + std::to_string(bmodelIndex) + " import source cannot be reloaded: "
                    + importErrorMessage);
            continue;
        }

        const std::vector<EditorImportedMaterialDiagnostic> diagnostics =
            buildImportedMaterialDiagnostics(m_bitmapTextureNames, importedModel, *importSource);

        for (const EditorImportedMaterialDiagnostic &diagnostic : diagnostics)
        {
            if (diagnostic.resolvesToKnownBitmap)
            {
                continue;
            }

            const std::string resolvedTextureName =
                trimCopy(diagnostic.resolvedTextureName).empty()
                ? "<empty>"
                : diagnostic.resolvedTextureName;
            recordSummarizedIssue(
                unresolvedImportedMaterialBindingCount,
                unresolvedImportedMaterialBindingExample,
                "BModel " + std::to_string(bmodelIndex) + " imported material '"
                    + diagnostic.sourceMaterialName + "' resolves to missing texture '"
                    + resolvedTextureName + "'.");
        }
    }

    for (size_t entityIndex = 0; entityIndex < sceneData.entities.size(); ++entityIndex)
    {
        const Game::OutdoorEntity &entity = sceneData.entities[entityIndex].entity;

        for (uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
        {
            if (!hasResolvedEvent(
                    eventId,
                    m_localScriptedEventProgram,
                    m_globalScriptedEventProgram,
                    m_localEvtProgram,
                    m_globalEvtProgram))
            {
                recordSummarizedIssue(
                    missingEntityEventCount,
                    missingEntityEventExample,
                    "Entity " + std::to_string(entityIndex) + " references missing event "
                        + std::to_string(eventId) + ".");
            }
        }
    }

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            uint16_t eventId = bmodel.faces[faceIndex].cogTriggeredNumber;
            const Game::OutdoorSceneInteractiveFace *pInteractiveFace = findInteractiveFace(
                sceneData,
                bmodelIndex,
                faceIndex);

            if (pInteractiveFace != nullptr)
            {
                eventId = pInteractiveFace->cogTriggeredNumber;
            }

            if (!hasResolvedEvent(
                    eventId,
                    m_localScriptedEventProgram,
                    m_globalScriptedEventProgram,
                    m_localEvtProgram,
                    m_globalEvtProgram))
            {
                recordSummarizedIssue(
                    missingFaceEventCount,
                    missingFaceEventExample,
                    "BModel " + std::to_string(bmodelIndex) + " face " + std::to_string(faceIndex)
                        + " references missing event " + std::to_string(eventId) + ".");
            }
        }
    }

    appendSummarizedIssue(
        m_validationMessages,
        faceTooFewVerticesCount,
        "faces have fewer than 3 vertices.",
        faceTooFewVerticesExample);
    appendSummarizedIssue(
        m_validationMessages,
        invalidFaceVertexIndexCount,
        "faces reference invalid vertex indices.",
        invalidFaceVertexIndexExample);
    appendSummarizedIssue(
        m_validationMessages,
        degenerateFaceCount,
        "faces are degenerate.",
        degenerateFaceExample);
    appendSummarizedIssue(
        m_validationMessages,
        emptyTextureFaceCount,
        "faces have empty texture names.",
        emptyTextureFaceExample);
    appendSummarizedIssue(
        m_validationMessages,
        missingTextureFaceCount,
        "faces use missing textures.",
        missingTextureFaceExample);
    appendSummarizedIssue(
        m_validationMessages,
        invalidImportedSourceCount,
        "source-backed bmodels cannot reload their imported source.",
        invalidImportedSourceExample);
    appendSummarizedIssue(
        m_validationMessages,
        unresolvedImportedMaterialBindingCount,
        "imported material bindings resolve to missing textures.",
        unresolvedImportedMaterialBindingExample);
    appendSummarizedIssue(
        m_validationMessages,
        missingEntityEventCount,
        "entity event references are unresolved.",
        missingEntityEventExample);
    appendSummarizedIssue(
        m_validationMessages,
        missingFaceEventCount,
        "face event references are unresolved.",
        missingFaceEventExample);
}

void EditorSession::refreshDirtyState()
{
    if (!hasDocument())
    {
        return;
    }

    m_document.setDirty(
        (m_document.kind() == EditorDocument::Kind::Indoor
            ? m_document.createIndoorSceneSnapshot()
            : m_document.createOutdoorSceneSnapshot())
        != m_savedSnapshot);
}

void EditorSession::resetHistory()
{
    m_undoSnapshots.clear();
    m_redoSnapshots.clear();
    m_frameMutationCaptured = false;
}

void EditorSession::normalizeOutdoorSceneCollections()
{
    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        return;
    }

    Game::OutdoorSceneData &sceneData = m_document.mutableOutdoorSceneData();

    for (size_t index = 0; index < sceneData.entities.size(); ++index)
    {
        sceneData.entities[index].entityIndex = index;
    }

    for (size_t index = 0; index < sceneData.spawns.size(); ++index)
    {
        sceneData.spawns[index].spawnIndex = index;
    }
}

void EditorSession::loadOutdoorEditorSupportData(const std::string &mapFileName)
{
    m_localEvtProgram.reset();
    m_globalEvtProgram.reset();
    m_localScriptedEventProgram.reset();
    m_globalScriptedEventProgram.reset();
    m_mapEventOptions.clear();
    m_localScriptModulePath.reset();

    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const std::string mapBaseName = std::filesystem::path(mapFileName).stem().string();
    const std::optional<std::vector<uint8_t>> localBytes =
        readFirstExistingBinary(*m_pAssetFileSystem, buildScriptPathCandidates(mapBaseName));

    if (localBytes)
    {
        Game::EvtProgram program = {};

        if (program.loadFromBytes(*localBytes))
        {
            m_localEvtProgram = std::move(program);
        }
    }

    const std::optional<std::vector<uint8_t>> globalBytes = readFirstExistingBinary(
        *m_pAssetFileSystem,
        {"Data/EnglishT/Global.EVT", "Data/EnglishT/GLOBAL.EVT", "Data/EnglishT/global.evt"});

    if (globalBytes)
    {
        Game::EvtProgram program = {};

        if (program.loadFromBytes(*globalBytes))
        {
            m_globalEvtProgram = std::move(program);
        }
    }

    std::string resolvedSupportLuaPath;
    const std::optional<std::string> supportLuaSource =
        readFirstExistingText(*m_pAssetFileSystem, buildLuaSupportPathCandidates(), resolvedSupportLuaPath);

    const std::string packageScriptModule = m_document.outdoorMapPackageMetadata().scriptModule;
    std::vector<std::string> localLuaCandidates;

    if (!packageScriptModule.empty())
    {
        localLuaCandidates.push_back(packageScriptModule);
    }

    const std::vector<std::filesystem::path> localLuaSidecarCandidates =
        buildLuaScriptSidecarPathCandidates(
            mapBaseName,
            m_document.geometryPhysicalPath(),
            m_document.scenePhysicalPath());
    const std::vector<std::string> defaultLuaCandidates = buildLuaScriptPathCandidates(mapBaseName, false);
    localLuaCandidates.insert(localLuaCandidates.end(), defaultLuaCandidates.begin(), defaultLuaCandidates.end());

    {
        std::string resolvedLuaPath;
        std::optional<std::string> luaSource =
            readFirstExistingPhysicalText(localLuaSidecarCandidates, resolvedLuaPath);

        if (!luaSource)
        {
            luaSource = readFirstExistingText(*m_pAssetFileSystem, localLuaCandidates, resolvedLuaPath);
        }

        if (luaSource)
        {
            std::string errorMessage;
            const std::string combinedLuaSource = prependLuaSupport(supportLuaSource, luaSource);
            std::optional<Game::ScriptedEventProgram> program = Game::ScriptedEventProgram::loadFromLuaText(
                combinedLuaSource,
                "@" + resolvedLuaPath,
                Game::ScriptedEventScope::Map,
                errorMessage);

            if (program)
            {
                m_localScriptedEventProgram = std::move(program);
                m_localScriptModulePath = resolvedLuaPath;
            }
        }
    }

    {
        std::string resolvedLuaPath;
        const std::optional<std::string> luaSource =
            readFirstExistingText(*m_pAssetFileSystem, buildLuaScriptPathCandidates("Global", true), resolvedLuaPath);

        if (luaSource)
        {
            std::string errorMessage;
            const std::string combinedLuaSource = prependLuaSupport(supportLuaSource, luaSource);
            std::optional<Game::ScriptedEventProgram> program = Game::ScriptedEventProgram::loadFromLuaText(
                combinedLuaSource,
                "@" + resolvedLuaPath,
                Game::ScriptedEventScope::Global,
                errorMessage);

            if (program)
            {
                m_globalScriptedEventProgram = std::move(program);
            }
        }
    }

    std::unordered_set<uint32_t> seenEventIds;
    appendScriptedEventOptions(m_localScriptedEventProgram, "Local", m_mapEventOptions, seenEventIds);
    std::sort(m_mapEventOptions.begin(), m_mapEventOptions.end(), [](const EditorIdLabelOption &left, const EditorIdLabelOption &right)
    {
        return left.id < right.id;
    });
}

void EditorSession::pruneBModelImportSources()
{
    if (!hasDocument() || m_document.kind() != EditorDocument::Kind::Outdoor)
    {
        return;
    }
    m_document.synchronizeOutdoorGeometryMetadata();

    const size_t bmodelCount = m_document.outdoorGeometry().bmodels.size();

    if (m_selection.kind == EditorSelectionKind::BModel && m_selection.index >= bmodelCount)
    {
        m_selection = {EditorSelectionKind::Summary, 0};
    }
}

std::string EditorSession::previewEventRuntimeKey() const
{
    if (!hasDocument())
    {
        return {};
    }

    return m_document.sceneVirtualPath()
        + "|"
        + std::to_string(static_cast<unsigned long long>(m_document.sceneRevision()));
}
}
