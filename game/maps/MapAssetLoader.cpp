#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "game/tables/SurfaceMaterialTable.h"
#include "game/tables/TextureFrameTable.h"
#include "engine/TextTable.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string dataTablePath(std::string_view fileName)
{
    return "Data/data_tables/" + std::string(fileName);
}

std::string monsterSpriteFrameFamilyPath(std::string_view familyRoot)
{
    return "Data/rendering/sprite_frames/monsters/" + std::string(familyRoot) + ".yml";
}

constexpr uint8_t WaterTileName[] = {'w', 't', 'r', 't', 'y', 'l', 0};
constexpr int TerrainTextureTileSize = 128;
constexpr int TerrainTextureAtlasColumns = 16;
constexpr uint16_t LevelDecorationInvisible = 0x0020;

bool faceHasInvisibleAttribute(uint32_t attributes)
{
    return (attributes & static_cast<uint32_t>(EvtFaceAttribute::Invisible)) != 0;
}

std::optional<std::string> resolveMonsterNameForSpawn(const MapStatsEntry &map, uint16_t typeId, uint16_t index);

int terrainTexturePhysicalTileSize(Engine::AssetScaleTier assetScaleTier)
{
    return TerrainTextureTileSize * Engine::assetScaleTierFactor(assetScaleTier);
}

std::string trimAsciiWhitespace(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

template <typename EntityType>
const DecorationEntry *resolveDecorationEntry(
    const DecorationTable &decorationTable,
    const EntityType &entity)
{
    const DecorationEntry *pDecoration = decorationTable.get(entity.decorationListId);

    if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
    {
        pDecoration = decorationTable.findByInternalName(entity.name);
    }

    return pDecoration;
}

template <typename EntityType>
bool shouldSkipDecorationCollision(const EntityType &entity, const DecorationEntry &decoration)
{
    if ((entity.aiAttributes & LevelDecorationInvisible) != 0)
    {
        return true;
    }

    if (hasDecorationFlag(decoration.flags, DecorationDescFlag::MoveThrough)
        || hasDecorationFlag(decoration.flags, DecorationDescFlag::DontDraw))
    {
        return true;
    }

    // Entries like "smoke" are effect emitters with no base sprite and should not block movement.
    if (decoration.spriteId == 0)
    {
        return true;
    }

    if (decoration.internalName.rfind("plant", 0) == 0)
    {
        return true;
    }

    return decoration.radius <= 0 || decoration.height == 0;
}

bool shouldSkipSpriteObjectCollision(const MapDeltaSpriteObject &spriteObject, const ObjectEntry &objectEntry)
{
    if (spriteObject.objectDescriptionId == 0)
    {
        return true;
    }

    if (objectEntry.radius <= 0 || objectEntry.height <= 0)
    {
        return true;
    }

    if ((objectEntry.flags & ObjectDescNoCollision) != 0)
    {
        return true;
    }

    if ((spriteObject.attributes & (SpriteAttrTemporary | SpriteAttrMissile | SpriteAttrRemoved)) != 0)
    {
        return true;
    }

    if ((objectEntry.flags & (ObjectDescTemporary | ObjectDescTrailParticle | ObjectDescTrailFire | ObjectDescTrailLine))
        != 0)
    {
        return true;
    }

    if (spriteObject.spellId != 0)
    {
        return true;
    }

    if (hasContainingItemPayload(spriteObject.rawContainingItem) && (objectEntry.flags & ObjectDescUnpickable) == 0)
    {
        return true;
    }

    return false;
}

bool isWaterTransitionTerrainTexture(const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);
    return normalizedTextureName.starts_with("wtrdr") || normalizedTextureName.starts_with("hwtrdr");
}

bool isAnimatedWaterTerrainTexture(const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);
    return normalizedTextureName == "wtrtyl"
        || normalizedTextureName == "hwtrtyl"
        || normalizedTextureName.starts_with("wtrdr")
        || normalizedTextureName.starts_with("hwtrdr");
}

std::string waterBaseTextureNameForTerrainTexture(const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);
    return normalizedTextureName.starts_with("hwtr") ? "hWTRTYL" : std::string(reinterpret_cast<const char *>(WaterTileName));
}

std::vector<uint8_t> compositeTerrainOverlayOverBase(
    const std::vector<uint8_t> &basePixels,
    const std::vector<uint8_t> &overlayPixels)
{
    if (basePixels.size() != overlayPixels.size())
    {
        return overlayPixels;
    }

    std::vector<uint8_t> compositedPixels = basePixels;

    for (size_t offset = 0; offset + 3 < compositedPixels.size(); offset += 4)
    {
        const uint32_t sourceAlpha = overlayPixels[offset + 3];

        if (sourceAlpha == 0)
        {
            continue;
        }

        if (sourceAlpha >= 255)
        {
            compositedPixels[offset + 0] = overlayPixels[offset + 0];
            compositedPixels[offset + 1] = overlayPixels[offset + 1];
            compositedPixels[offset + 2] = overlayPixels[offset + 2];
            compositedPixels[offset + 3] = 255;
            continue;
        }

        const uint32_t destinationAlpha = compositedPixels[offset + 3];
        const uint32_t inverseSourceAlpha = 255 - sourceAlpha;
        const uint32_t outAlpha = sourceAlpha + (destinationAlpha * inverseSourceAlpha + 127) / 255;

        for (int channel = 0; channel < 3; ++channel)
        {
            const uint32_t source = overlayPixels[offset + static_cast<size_t>(channel)];
            const uint32_t destination = compositedPixels[offset + static_cast<size_t>(channel)];
            const uint32_t blended =
                (source * sourceAlpha + destination * inverseSourceAlpha + 127) / 255;
            compositedPixels[offset + static_cast<size_t>(channel)] = static_cast<uint8_t>(blended);
        }

        compositedPixels[offset + 3] = static_cast<uint8_t>(std::min(outAlpha, 255u));
    }

    return compositedPixels;
}

bool loadDecorationRows(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<std::vector<std::string>> &rows)
{
    rows.clear();

    const std::optional<std::string> contents =
        assetFileSystem.readTextFile(dataTablePath("decoration_data.txt"));

    if (!contents)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*contents);

    if (!parsedTable)
    {
        return false;
    }

    rows.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return true;
}

bool loadTextureFrameRows(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<std::vector<std::string>> &rows)
{
    rows.clear();

    const std::optional<std::string> contents =
        assetFileSystem.readTextFile(dataTablePath("texture_frame_data.txt"));

    if (!contents)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*contents);

    if (!parsedTable)
    {
        return false;
    }

    rows.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return true;
}

std::optional<TextureFrameTable> loadTextureFrameTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextureFrameRows(assetFileSystem, rows))
    {
        return std::nullopt;
    }

    TextureFrameTable textureFrameTable = {};

    if (!textureFrameTable.loadRows(rows))
    {
        return std::nullopt;
    }

    return textureFrameTable;
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
    const MonsterEntry *pMonsterEntry)
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

void collectSummonMonsterSpriteFamilies(
    std::unordered_set<std::string> &neededMonsterFamilies,
    const MonsterTable &monsterTable)
{
    static constexpr std::array<int16_t, 3> SummonWispMonsterIds = {97, 98, 99};

    for (int16_t monsterId : SummonWispMonsterIds)
    {
        appendMonsterSpriteFamilies(neededMonsterFamilies, monsterTable.findById(monsterId));
    }
}

template <typename SpawnType>
void collectSpawnMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::vector<SpawnType> &spawns)
{
    for (const SpawnType &spawn : spawns)
    {
        const std::optional<std::string> monsterName = resolveMonsterNameForSpawn(map, spawn.typeId, spawn.index);

        if (!monsterName)
        {
            continue;
        }

        appendMonsterSpriteFamilies(families, monsterTable.findByInternalName(*monsterName));
    }
}

void collectMapDeltaMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    const MonsterTable &monsterTable,
    const std::optional<MapDeltaData> &mapDeltaData)
{
    if (!mapDeltaData)
    {
        return;
    }

    for (const MapDeltaActor &actor : mapDeltaData->actors)
    {
        const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
            monsterTable.findDisplayEntryById(actor.monsterInfoId);
        const MonsterEntry *pMonsterEntry = nullptr;

        if (pDisplayEntry != nullptr)
        {
            pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);
        }

        if (pMonsterEntry == nullptr)
        {
            pMonsterEntry = monsterTable.findById(actor.monsterId);
        }

        appendMonsterSpriteFamilies(families, pMonsterEntry);
    }
}

void collectEncounterMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    const MonsterTable &monsterTable,
    const MapStatsEntry &map)
{
    const std::array<const MapEncounterInfo *, 3> encounters = {{
        &map.encounter1,
        &map.encounter2,
        &map.encounter3,
    }};

    for (const MapEncounterInfo *pEncounter : encounters)
    {
        if (pEncounter == nullptr)
        {
            continue;
        }

        const std::string pictureBase = trimAsciiWhitespace(
            pEncounter->pictureName.empty() ? pEncounter->monsterName : pEncounter->pictureName);

        if (pictureBase.empty())
        {
            continue;
        }

        for (const char tierLetter : {'A', 'B', 'C'})
        {
            const MonsterTable::MonsterStatsEntry *pStats =
                monsterTable.findStatsByPictureName(pictureBase + " " + std::string(1, tierLetter));

            if (pStats == nullptr)
            {
                continue;
            }

            appendMonsterSpriteFamilies(families, monsterTable.findById(static_cast<int16_t>(pStats->id)));
        }
    }
}

std::optional<SurfaceMaterialTable> loadSurfaceMaterialTable(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::optional<std::string> contents =
        assetFileSystem.readTextFile("Data/rendering/surface_materials.yml");

    if (!contents)
    {
        return std::nullopt;
    }

    SurfaceMaterialTable materialTable = {};
    std::string errorMessage;

    if (!materialTable.loadFromYaml(*contents, errorMessage))
    {
        std::cerr << "Failed to load surface materials: " << errorMessage << '\n';
        return std::nullopt;
    }

    return materialTable;
}

std::optional<SpriteFrameTable> loadSpriteFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_set<std::string> &monsterFamilies = {})
{
    const std::optional<std::string> contents =
        assetFileSystem.readTextFile("Data/rendering/sprite_frame_data_common.yml");

    if (!contents)
    {
        return std::nullopt;
    }

    SpriteFrameTable spriteFrameTable = {};
    std::string errorMessage;

    if (!spriteFrameTable.loadFromYaml(*contents, errorMessage))
    {
        std::cerr << "Failed to load sprite frame data: " << errorMessage << '\n';
        return std::nullopt;
    }

    std::vector<std::string> sortedFamilies(monsterFamilies.begin(), monsterFamilies.end());
    std::sort(sortedFamilies.begin(), sortedFamilies.end());

    for (const std::string &familyRoot : sortedFamilies)
    {
        const std::optional<std::string> familyContents =
            assetFileSystem.readTextFile(monsterSpriteFrameFamilyPath(familyRoot));

        if (!familyContents)
        {
            std::cerr << "Failed to load monster sprite frame family: " << familyRoot << '\n';
            return std::nullopt;
        }

        if (!spriteFrameTable.loadFromYaml(*familyContents, errorMessage, true))
        {
            std::cerr << "Failed to load monster sprite frame family " << familyRoot
                      << ": " << errorMessage << '\n';
            return std::nullopt;
        }
    }

    return spriteFrameTable;
}

SurfaceAnimationSequence staticSurfaceAnimation(const std::string &textureName)
{
    SurfaceAnimationSequence animation = {};
    SurfaceAnimationFrame frame = {};
    frame.textureName = textureName;
    animation.frames.push_back(std::move(frame));
    return animation;
}

SurfaceAnimationSequence resolveSurfaceAnimation(
    const std::string &textureName,
    uint32_t faceAttributes,
    bool isTerrain,
    const TextureFrameTable *pTextureFrameTable,
    const SurfaceMaterialTable *pSurfaceMaterialTable,
    std::optional<size_t> textureFrameTableIndex = std::nullopt)
{
    if (pSurfaceMaterialTable != nullptr)
    {
        if (const SurfaceMaterialDefinition *pMaterial =
                pSurfaceMaterialTable->findMatch(textureName, faceAttributes, isTerrain);
            pMaterial != nullptr && !pMaterial->animation.empty())
        {
            return pMaterial->animation;
        }
    }

    if (!isTerrain && pTextureFrameTable != nullptr)
    {
        if (const std::optional<SurfaceAnimationSequence> animation =
                pTextureFrameTable->findAnimationSequenceByName(textureName))
        {
            return *animation;
        }
    }

    if (!isTerrain && pTextureFrameTable != nullptr && textureFrameTableIndex && *textureFrameTableIndex > 0)
    {
        if (const std::optional<SurfaceAnimationSequence> animation =
                pTextureFrameTable->findAnimationSequenceByIndex(*textureFrameTableIndex))
        {
            return *animation;
        }
    }

    return staticSurfaceAnimation(textureName);
}

void appendTextureAnimationBindingIfMissing(
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> &bindings,
    const std::string &textureName,
    const SurfaceAnimationSequence &animation)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const auto &binding : bindings)
    {
        if (binding.first == normalizedTextureName)
        {
            return;
        }
    }

    bindings.emplace_back(normalizedTextureName, animation);
}

void appendAnimationTextureNamesIfMissing(
    std::vector<std::string> &textureNames,
    const SurfaceAnimationSequence &animation)
{
    for (const SurfaceAnimationFrame &frame : animation.frames)
    {
        const std::string normalizedTextureName = toLowerCopy(frame.textureName);

        if (std::find(textureNames.begin(), textureNames.end(), normalizedTextureName) == textureNames.end())
        {
            textureNames.push_back(normalizedTextureName);
        }
    }
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

bool containsCaseInsensitive(const std::string &value, const std::string &needle)
{
    return value.find(needle) != std::string::npos;
}

uint32_t colorFromTextureName(const std::string &textureName)
{
    const std::string loweredName = toLowerCopy(textureName);

    if (containsCaseInsensitive(loweredName, "wtr") || containsCaseInsensitive(loweredName, "wat"))
    {
        return makeAbgr(48, 86, 158);
    }

    if (containsCaseInsensitive(loweredName, "gras")
        || containsCaseInsensitive(loweredName, "gr")
        || containsCaseInsensitive(loweredName, "swmp"))
    {
        return makeAbgr(82, 118, 54);
    }

    if (containsCaseInsensitive(loweredName, "drt") || containsCaseInsensitive(loweredName, "dirt"))
    {
        return makeAbgr(118, 88, 52);
    }

    if (containsCaseInsensitive(loweredName, "sn") || containsCaseInsensitive(loweredName, "snow"))
    {
        return makeAbgr(218, 222, 228);
    }

    if (containsCaseInsensitive(loweredName, "lav") || containsCaseInsensitive(loweredName, "vol"))
    {
        return makeAbgr(188, 86, 34);
    }

    if (containsCaseInsensitive(loweredName, "rk") || containsCaseInsensitive(loweredName, "rock"))
    {
        return makeAbgr(124, 124, 124);
    }

    uint32_t hash = 2166136261u;

    for (const char character : loweredName)
    {
        hash ^= static_cast<uint8_t>(character);
        hash *= 16777619u;
    }

    const uint8_t red = static_cast<uint8_t>(96 + (hash & 0x3f));
    const uint8_t green = static_cast<uint8_t>(96 + ((hash >> 6) & 0x3f));
    const uint8_t blue = static_cast<uint8_t>(96 + ((hash >> 12) & 0x3f));
    return makeAbgr(red, green, blue);
}

void appendTextureNameIfMissing(std::vector<std::string> &textureNames, const std::string &textureName)
{
    if (std::find(textureNames.begin(), textureNames.end(), textureName) == textureNames.end())
    {
        textureNames.push_back(textureName);
    }
}

struct BitmapTextureRequest
{
    std::string textureName;
    int16_t paletteId = 0;
};

struct BitmapPixelsResult
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct IndexedBitmapData
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> indices;
    std::array<SDL_Color, 256> palette = {};
    int paletteColorCount = 0;
};

struct BitmapLoadCache
{
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
    std::unordered_map<std::string, std::optional<IndexedBitmapData>> indexedBitmapsByPath;
    std::unordered_map<std::string, std::optional<BitmapPixelsResult>> pixelsByKey;
};

std::optional<std::string> findBitmapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(textureName);
    const auto cachedPathIt = bitmapLoadCache.bitmapPathByKey.find(cacheKey);

    if (cachedPathIt != bitmapLoadCache.bitmapPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto directoryAssetPathsIt = bitmapLoadCache.directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (directoryAssetPathsIt != bitmapLoadCache.directoryAssetPathsByPath.end())
    {
        pAssetPaths = &directoryAssetPathsIt->second;
    }
    else
    {
        std::vector<std::string> bitmapEntries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> assetPaths;

        for (const std::string &entry : bitmapEntries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths = &bitmapLoadCache.directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName) + ".bmp";
    const auto resolvedPathIt = pAssetPaths->find(normalizedTextureName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        bitmapLoadCache.bitmapPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    bitmapLoadCache.bitmapPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

std::optional<std::string> findAssetPathCaseInsensitive(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(fileName);
    const auto cachedPathIt = bitmapLoadCache.bitmapPathByKey.find(cacheKey);

    if (cachedPathIt != bitmapLoadCache.bitmapPathByKey.end())
    {
        return cachedPathIt->second;
    }

    const auto directoryAssetPathsIt = bitmapLoadCache.directoryAssetPathsByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (directoryAssetPathsIt != bitmapLoadCache.directoryAssetPathsByPath.end())
    {
        pAssetPaths = &directoryAssetPathsIt->second;
    }
    else
    {
        std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> assetPaths;

        for (const std::string &entry : entries)
        {
            assetPaths.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pAssetPaths = &bitmapLoadCache.directoryAssetPathsByPath.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedFileName = toLowerCopy(fileName);
    const auto resolvedPathIt = pAssetPaths->find(normalizedFileName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        bitmapLoadCache.bitmapPathByKey[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    bitmapLoadCache.bitmapPathByKey[cacheKey] = std::nullopt;
    return std::nullopt;
}

void appendBitmapTextureRequestIfMissing(
    std::vector<BitmapTextureRequest> &textureRequests,
    const std::string &textureName,
    int16_t paletteId
)
{
    const auto requestIt = std::find_if(
        textureRequests.begin(),
        textureRequests.end(),
        [&](const BitmapTextureRequest &request)
        {
            return request.textureName == textureName && request.paletteId == paletteId;
        }
    );

    if (requestIt == textureRequests.end())
    {
        BitmapTextureRequest request = {};
        request.textureName = textureName;
        request.paletteId = paletteId;
        textureRequests.push_back(std::move(request));
    }
}

std::optional<std::array<uint8_t, 256 * 3>> loadActPalette(
    const Engine::AssetFileSystem &assetFileSystem,
    int16_t paletteId,
    BitmapLoadCache &bitmapLoadCache
)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const auto cachedPaletteIt = bitmapLoadCache.actPalettesById.find(paletteId);

    if (cachedPaletteIt != bitmapLoadCache.actPalettesById.end())
    {
        return cachedPaletteIt->second;
    }

    char paletteFileName[16] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findAssetPathCaseInsensitive(assetFileSystem, "Data/bitmaps", paletteFileName, bitmapLoadCache);

    if (!palettePath)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    const std::string &palettePathString = *palettePath;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(palettePathString);
    std::optional<std::vector<uint8_t>> paletteBytes;

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        paletteBytes = cachedFileIt->second;
    }
    else
    {
        paletteBytes = assetFileSystem.readBinaryFile(palettePathString);
        bitmapLoadCache.binaryFilesByPath[palettePathString] = paletteBytes;
    }

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    bitmapLoadCache.actPalettesById[paletteId] = palette;
    return palette;
}

std::optional<IndexedBitmapData> loadIndexedBitmapData(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &bitmapPath,
    BitmapLoadCache &bitmapLoadCache
)
{
    const auto cachedBitmapIt = bitmapLoadCache.indexedBitmapsByPath.find(bitmapPath);

    if (cachedBitmapIt != bitmapLoadCache.indexedBitmapsByPath.end())
    {
        return cachedBitmapIt->second;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(bitmapPath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(bitmapPath);
        bitmapLoadCache.binaryFilesByPath[bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        bitmapLoadCache.indexedBitmapsByPath[bitmapPath] = std::nullopt;
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

    SDL_Palette *pBasePalette = SDL_GetSurfacePalette(pLoadedSurface);
    const bool canApplyPalette = pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8 && pBasePalette != nullptr;

    if (!canApplyPalette)
    {
        SDL_DestroySurface(pLoadedSurface);
        bitmapLoadCache.indexedBitmapsByPath[bitmapPath] = std::nullopt;
        return std::nullopt;
    }

    IndexedBitmapData indexedBitmap = {};
    indexedBitmap.width = pLoadedSurface->w;
    indexedBitmap.height = pLoadedSurface->h;
    indexedBitmap.paletteColorCount = pBasePalette->ncolors;
    indexedBitmap.indices.resize(static_cast<size_t>(indexedBitmap.width * indexedBitmap.height));

    for (int paletteIndex = 0; paletteIndex < std::min(256, pBasePalette->ncolors); ++paletteIndex)
    {
        indexedBitmap.palette[static_cast<size_t>(paletteIndex)] = pBasePalette->colors[paletteIndex];
    }

    for (int row = 0; row < indexedBitmap.height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels) + row * pLoadedSurface->pitch;
        uint8_t *pTargetRow = indexedBitmap.indices.data()
            + static_cast<ptrdiff_t>(row * indexedBitmap.width);
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(indexedBitmap.width));
    }

    SDL_DestroySurface(pLoadedSurface);
    bitmapLoadCache.indexedBitmapsByPath[bitmapPath] = indexedBitmap;
    return indexedBitmap;
}

std::optional<std::vector<uint8_t>> loadIndexedBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &bitmapPath,
    int16_t paletteId,
    int &width,
    int &height,
    bool applyTransparencyKey,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::optional<IndexedBitmapData> indexedBitmap =
        loadIndexedBitmapData(assetFileSystem, bitmapPath, bitmapLoadCache);
    const std::optional<std::array<uint8_t, 256 * 3>> overridePalette =
        loadActPalette(assetFileSystem, paletteId, bitmapLoadCache);

    if (!indexedBitmap || !overridePalette)
    {
        return std::nullopt;
    }

    width = indexedBitmap->width;
    height = indexedBitmap->height;
    std::vector<uint8_t> pixels(static_cast<size_t>(width * height * 4));

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow =
            indexedBitmap->indices.data() + static_cast<ptrdiff_t>(row * indexedBitmap->width);

        for (int column = 0; column < width; ++column)
        {
            const uint8_t paletteIndex = pSourceRow[column];
            const size_t pixelOffset = static_cast<size_t>((row * width + column) * 4);
            const SDL_Color sourceColor =
                paletteIndex < indexedBitmap->paletteColorCount
                    ? indexedBitmap->palette[paletteIndex]
                    : SDL_Color{0, 0, 0, 255};
            const bool isZeroIndexKey = applyTransparencyKey && paletteIndex == 0;
            const bool isMagentaKey = sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
            const bool isTealKey = applyTransparencyKey && sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
            const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;

            pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
            pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
            pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
            pixels[pixelOffset + 3] = (isZeroIndexKey || isMagentaKey || isTealKey) ? 0 : 255;
        }
    }

    return pixels;
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    bool forceTerrainTileSize,
    bool applyTransparencyKey,
    BitmapLoadCache &bitmapLoadCache,
    int16_t paletteId = 0
)
{
    const int forcedTerrainTileSize =
        forceTerrainTileSize ? terrainTexturePhysicalTileSize(assetFileSystem.getAssetScaleTier()) : 0;
    const std::string cacheKey =
        directoryPath + "|" + toLowerCopy(textureName)
        + "|" + std::to_string(forcedTerrainTileSize)
        + "|" + std::to_string(applyTransparencyKey ? 1 : 0)
        + "|" + std::to_string(static_cast<int>(paletteId));
    const auto cachedPixelsIt = bitmapLoadCache.pixelsByKey.find(cacheKey);

    if (cachedPixelsIt != bitmapLoadCache.pixelsByKey.end())
    {
        if (!cachedPixelsIt->second)
        {
            return std::nullopt;
        }

        width = cachedPixelsIt->second->width;
        height = cachedPixelsIt->second->height;
        return cachedPixelsIt->second->pixels;
    }

    const std::optional<std::string> bitmapPath =
        findBitmapPath(assetFileSystem, directoryPath, textureName, bitmapLoadCache);

    if (!bitmapPath)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(*bitmapPath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);
        bitmapLoadCache.binaryFilesByPath[*bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    if (paletteId > 0 && !forceTerrainTileSize)
    {
        if (const std::optional<std::vector<uint8_t>> indexedPixels = loadIndexedBitmapPixelsBgra(
                assetFileSystem,
                *bitmapPath,
                paletteId,
                width,
                height,
                applyTransparencyKey,
                bitmapLoadCache))
        {
            bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, *indexedPixels};
            return indexedPixels;
        }
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    SDL_Surface *pSurfaceToCopy = pConvertedSurface;

    if (forceTerrainTileSize
        && (pConvertedSurface->w != forcedTerrainTileSize || pConvertedSurface->h != forcedTerrainTileSize))
    {
        SDL_Surface *pScaledSurface =
            SDL_ScaleSurface(
                pConvertedSurface,
                forcedTerrainTileSize,
                forcedTerrainTileSize,
                SDL_SCALEMODE_NEAREST);
        SDL_DestroySurface(pConvertedSurface);
        pSurfaceToCopy = pScaledSurface;

        if (pSurfaceToCopy == nullptr)
        {
            bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
            return std::nullopt;
        }
    }

    width = pSurfaceToCopy->w;
    height = pSurfaceToCopy->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width * height * 4));

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pSurfaceToCopy->pixels) + row * pSurfaceToCopy->pitch;
        uint8_t *pTargetRow = pixels.data() + static_cast<size_t>(row * width * 4);
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(width * 4));
    }

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];

        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = applyTransparencyKey && red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pSurfaceToCopy);
    bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
    return pixels;
}

template <typename EntityType>
std::optional<DecorationBillboardSet> buildDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<EntityType> &entities,
    BitmapLoadCache &bitmapLoadCache
)
{
    DecorationBillboardSet billboardSet = {};

    const std::optional<SpriteFrameTable> spriteFrameTable = loadSpriteFrameTable(assetFileSystem);

    if (!spriteFrameTable)
    {
        return std::nullopt;
    }

    billboardSet.spriteFrameTable = *spriteFrameTable;

    std::vector<std::vector<std::string>> decorationRows;

    if (!loadDecorationRows(assetFileSystem, decorationRows)
        || !billboardSet.decorationTable.loadRows(decorationRows))
    {
        return std::nullopt;
    }

    std::vector<std::string> textureNames;

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const EntityType &entity = entities[entityIndex];
        const DecorationEntry *pDecoration = resolveDecorationEntry(billboardSet.decorationTable, entity);

        if (pDecoration == nullptr)
        {
            continue;
        }

        const bool isEmitterOnlyDecoration =
            pDecoration->spriteId == 0
            && (hasDecorationFlag(pDecoration->flags, DecorationDescFlag::EmitFire)
                || hasDecorationFlag(pDecoration->flags, DecorationDescFlag::EmitSmoke));

        if (pDecoration->spriteId == 0 && !isEmitterOnlyDecoration)
        {
            continue;
        }

        DecorationBillboard billboard = {};
        billboard.entityIndex = entityIndex;
        billboard.decorationId = entity.decorationListId;
        billboard.spriteId = pDecoration->spriteId;
        billboard.flags = pDecoration->flags;
        billboard.height = pDecoration->height;
        billboard.radius = pDecoration->radius;
        billboard.x = entity.x;
        billboard.y = entity.y;
        billboard.z = entity.z;
        billboard.facing = entity.facing;
        billboard.name = entity.name;
        billboardSet.billboards.push_back(std::move(billboard));

        if (pDecoration->spriteId != 0)
        {
            const std::vector<std::string> billboardTextureNames =
                billboardSet.spriteFrameTable.collectTextureNames(pDecoration->spriteId);

            for (const std::string &textureName : billboardTextureNames)
            {
                if (std::find(textureNames.begin(), textureNames.end(), textureName) == textureNames.end())
                {
                    textureNames.push_back(textureName);
                }
            }
        }
    }

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/sprites",
                textureName,
                textureWidth,
                textureHeight,
                false,
                true,
                bitmapLoadCache
            );

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
        billboardSet.textures.push_back(std::move(texture));
    }

    return billboardSet;
}

template <typename EntityType>
std::optional<OutdoorDecorationCollisionSet> buildOutdoorDecorationCollisionSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<EntityType> &entities
)
{
    DecorationTable decorationTable;

    std::vector<std::vector<std::string>> decorationRows;

    if (!loadDecorationRows(assetFileSystem, decorationRows)
        || !decorationTable.loadRows(decorationRows))
    {
        return std::nullopt;
    }

    OutdoorDecorationCollisionSet collisionSet = {};

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const EntityType &entity = entities[entityIndex];
        const DecorationEntry *pDecoration = resolveDecorationEntry(decorationTable, entity);

        if (pDecoration == nullptr)
        {
            continue;
        }

        if (shouldSkipDecorationCollision(entity, *pDecoration))
        {
            continue;
        }

        OutdoorDecorationCollision collision = {};
        collision.entityIndex = entityIndex;
        collision.decorationId = entity.decorationListId;
        collision.descriptionFlags = pDecoration->flags;
        collision.instanceFlags = entity.aiAttributes;
        collision.radius = pDecoration->radius;
        collision.height = pDecoration->height;
        collision.worldX = entity.x;
        collision.worldY = entity.y;
        collision.worldZ = entity.z;
        collision.name = entity.name.empty() ? pDecoration->internalName : entity.name;
        collisionSet.colliders.push_back(std::move(collision));
    }

    if (collisionSet.colliders.empty())
    {
        return std::nullopt;
    }

    return collisionSet;
}

void appendMapDeltaActorCollisions(
    OutdoorActorCollisionSet &collisionSet,
    const MapDeltaData &mapDeltaData,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];

        if (actor.radius == 0 || actor.height == 0)
        {
            continue;
        }

        int actorZ = actor.z;

        if (pOutdoorMapData != nullptr)
        {
            actorZ = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actorZ))));
        }

        OutdoorActorCollision collision = {};
        collision.sourceIndex = actorIndex;
        collision.source = OutdoorActorCollisionSource::MapDelta;
        collision.radius = actor.radius;
        collision.height = actor.height;
        collision.worldX = actor.x;
        collision.worldY = actor.y;
        collision.worldZ = actorZ;
        collision.attributes = actor.attributes;
        collision.group = actor.group;
        collision.name = actor.name;
        collisionSet.colliders.push_back(std::move(collision));
    }
}

template <typename SpawnType>
void appendSpawnActorCollisions(
    OutdoorActorCollisionSet &collisionSet,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::vector<SpawnType> &spawns,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t spawnIndex = 0; spawnIndex < spawns.size(); ++spawnIndex)
    {
        const SpawnType &spawn = spawns[spawnIndex];
        const std::optional<std::string> monsterName = resolveMonsterNameForSpawn(map, spawn.typeId, spawn.index);

        if (!monsterName)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(*monsterName);

        if (pMonsterEntry == nullptr || pMonsterEntry->radius == 0 || pMonsterEntry->height == 0)
        {
            continue;
        }

        int actorZ = spawn.z;

        if (pOutdoorMapData != nullptr)
        {
            actorZ = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(actorZ))));
        }

        OutdoorActorCollision collision = {};
        collision.sourceIndex = spawnIndex;
        collision.source = OutdoorActorCollisionSource::Spawn;
        collision.radius = pMonsterEntry->radius;
        collision.height = pMonsterEntry->height;
        collision.worldX = spawn.x;
        collision.worldY = spawn.y;
        collision.worldZ = actorZ;
        collision.attributes = spawn.attributes;
        collision.group = spawn.group;
        collision.name = *monsterName;
        collisionSet.colliders.push_back(std::move(collision));
    }
}

template <typename SpawnType>
std::optional<OutdoorActorCollisionSet> buildOutdoorActorCollisionSet(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::vector<SpawnType> &spawns,
    const OutdoorMapData *pOutdoorMapData
)
{
    OutdoorActorCollisionSet collisionSet = {};

    if (mapDeltaData)
    {
        appendMapDeltaActorCollisions(collisionSet, *mapDeltaData, pOutdoorMapData);
    }

    appendSpawnActorCollisions(collisionSet, map, monsterTable, spawns, pOutdoorMapData);

    if (collisionSet.colliders.empty())
    {
        return std::nullopt;
    }

    return collisionSet;
}

std::optional<DecorationBillboardSet> buildOutdoorDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    std::optional<DecorationBillboardSet> billboardSet =
        buildDecorationBillboardSet(assetFileSystem, outdoorMapData.entities, bitmapLoadCache);

    if (!billboardSet)
    {
        return std::nullopt;
    }

    for (DecorationBillboard &billboard : billboardSet->billboards)
    {
        if (!hasDecorationFlag(billboard.flags, DecorationDescFlag::EmitFire)
            && !hasDecorationFlag(billboard.flags, DecorationDescFlag::EmitSmoke))
        {
            continue;
        }

        const float supportHeight = sampleOutdoorPlacementFloorHeight(
            outdoorMapData,
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z));
        billboard.z = static_cast<int>(std::lround(supportHeight));
    }

    return billboardSet;
}

std::optional<DecorationBillboardSet> buildIndoorDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const IndoorMapData &indoorMapData,
    BitmapLoadCache &bitmapLoadCache
)
{
    return buildDecorationBillboardSet(assetFileSystem, indoorMapData.entities, bitmapLoadCache);
}

std::optional<SpriteObjectBillboardSet> buildSpriteObjectBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const ObjectTable &objectTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    BitmapLoadCache &bitmapLoadCache
)
{
    if (!mapDeltaData || mapDeltaData->spriteObjects.empty())
    {
        return std::nullopt;
    }

    SpriteObjectBillboardSet billboardSet = {};

    const std::optional<SpriteFrameTable> spriteFrameTable = loadSpriteFrameTable(assetFileSystem);

    if (!spriteFrameTable)
    {
        return std::nullopt;
    }

    billboardSet.spriteFrameTable = *spriteFrameTable;

    std::vector<std::string> textureNames;

    for (size_t objectIndex = 0; objectIndex < mapDeltaData->spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = mapDeltaData->spriteObjects[objectIndex];
        const ObjectEntry *pObjectEntry = objectTable.get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & 0x0001) != 0 || pObjectEntry->spriteId == 0)
        {
            continue;
        }

        if (hasContainingItemPayload(spriteObject.rawContainingItem)
            && (pObjectEntry->flags & ObjectDescUnpickable) == 0)
        {
            continue;
        }

        const SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(pObjectEntry->spriteId, uint32_t(spriteObject.timeSinceCreated) * 8);

        SpriteObjectBillboard billboard = {};
        billboard.index = objectIndex;
        billboard.spriteFrameIndex = pObjectEntry->spriteId;
        billboard.objectDescriptionId = spriteObject.objectDescriptionId;
        billboard.objectSpriteId = pObjectEntry->spriteId;
        billboard.attributes = spriteObject.attributes;
        billboard.soundId = spriteObject.soundId;
        billboard.x = spriteObject.x;
        billboard.y = spriteObject.y;
        billboard.z = spriteObject.z;
        billboard.radius = pObjectEntry->radius;
        billboard.height = pObjectEntry->height;
        billboard.sectorId = spriteObject.sectorId;
        billboard.temporaryLifetime = spriteObject.temporaryLifetime;
        billboard.glowRadiusMultiplier = spriteObject.glowRadiusMultiplier;
        billboard.spellId = spriteObject.spellId;
        billboard.spellLevel = spriteObject.spellLevel;
        billboard.spellSkill = spriteObject.spellSkill;
        billboard.spellCasterPid = spriteObject.spellCasterPid;
        billboard.spellTargetPid = spriteObject.spellTargetPid;
        billboard.timeSinceCreatedTicks = uint32_t(spriteObject.timeSinceCreated) * 8;
        billboard.objectName = pObjectEntry->internalName;
        billboardSet.billboards.push_back(std::move(billboard));

        if (pFrame == nullptr)
        {
            continue;
        }

        const std::vector<std::string> billboardTextureNames =
            billboardSet.spriteFrameTable.collectTextureNames(pObjectEntry->spriteId);

        for (const std::string &textureName : billboardTextureNames)
        {
            appendTextureNameIfMissing(textureNames, textureName);
        }
    }

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/sprites",
                textureName,
                textureWidth,
                textureHeight,
                false,
                true,
                bitmapLoadCache
            );

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
        billboardSet.textures.push_back(std::move(texture));
    }

    for (const SpriteObjectBillboard &billboard : billboardSet.billboards)
    {
        const SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(billboard.objectSpriteId, billboard.timeSinceCreatedTicks);

        if (pFrame == nullptr)
        {
            ++billboardSet.missingTextureObjectCount;
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const auto textureIt = std::find_if(
            billboardSet.textures.begin(),
            billboardSet.textures.end(),
            [&resolvedTexture](const OutdoorBitmapTexture &texture)
            {
                return texture.textureName == resolvedTexture.textureName;
            }
        );

        if (textureIt == billboardSet.textures.end())
        {
            ++billboardSet.missingTextureObjectCount;
        }
        else
        {
            ++billboardSet.texturedObjectCount;
        }
    }

    return billboardSet;
}

std::optional<OutdoorSpriteObjectCollisionSet> buildOutdoorSpriteObjectCollisionSet(
    const ObjectTable &objectTable,
    const std::optional<MapDeltaData> &mapDeltaData
)
{
    if (!mapDeltaData || mapDeltaData->spriteObjects.empty())
    {
        return std::nullopt;
    }

    OutdoorSpriteObjectCollisionSet collisionSet = {};

    for (size_t objectIndex = 0; objectIndex < mapDeltaData->spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = mapDeltaData->spriteObjects[objectIndex];
        const ObjectEntry *pObjectEntry = objectTable.get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || shouldSkipSpriteObjectCollision(spriteObject, *pObjectEntry))
        {
            continue;
        }

        OutdoorSpriteObjectCollision collision = {};
        collision.sourceIndex = objectIndex;
        collision.objectDescriptionId = spriteObject.objectDescriptionId;
        collision.objectAttributes = spriteObject.attributes;
        collision.objectFlags = pObjectEntry->flags;
        collision.radius = static_cast<uint16_t>(pObjectEntry->radius);
        collision.height = static_cast<uint16_t>(pObjectEntry->height);
        collision.worldX = spriteObject.x;
        collision.worldY = spriteObject.y;
        collision.worldZ = spriteObject.z;
        collision.spellId = spriteObject.spellId;
        collision.name = pObjectEntry->internalName;
        collisionSet.colliders.push_back(std::move(collision));
    }

    if (collisionSet.colliders.empty())
    {
        return std::nullopt;
    }

    return collisionSet;
}

std::optional<std::string> resolveMonsterNameForSpawn(const MapStatsEntry &map, uint16_t typeId, uint16_t index)
{
    if (typeId != 3)
    {
        return std::nullopt;
    }

    if (index >= 1 && index <= 3)
    {
        const MapEncounterInfo *pEncounter = nullptr;

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
        const MapEncounterInfo *pEncounter = nullptr;

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

int16_t resolveMapDeltaActorMonsterId(const MapDeltaActor &actor)
{
    if (actor.monsterInfoId > 0)
    {
        return actor.monsterInfoId;
    }

    if (actor.monsterId > 0)
    {
        return actor.monsterId;
    }

    return 0;
}

std::array<uint16_t, 8> buildMonsterActionSpriteFrameIndices(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry
)
{
    std::array<uint16_t, 8> spriteFrameIndices = {};

    if (pMonsterEntry == nullptr)
    {
        return spriteFrameIndices;
    }

    for (size_t actionIndex = 0; actionIndex < spriteFrameIndices.size(); ++actionIndex)
    {
        const std::string &spriteName = pMonsterEntry->spriteNames[actionIndex];

        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            spriteFrameIndices[actionIndex] = *frameIndex;
        }
    }

    return spriteFrameIndices;
}

void appendSpriteFrameTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    uint16_t spriteFrameIndex
)
{
    if (spriteFrameIndex == 0)
    {
        return;
    }

    size_t frameIndex = spriteFrameIndex;

    while (frameIndex <= std::numeric_limits<uint16_t>::max())
    {
        const SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(static_cast<uint16_t>(frameIndex), 0);

        if (pFrame == nullptr)
        {
            return;
        }

        for (int octant = 0; octant < 8; ++octant)
        {
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            appendBitmapTextureRequestIfMissing(textureRequests, resolvedTexture.textureName, pFrame->paletteId);
        }

        if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
        {
            return;
        }

        ++frameIndex;
    }
}

void appendMonsterActionTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    const std::array<uint16_t, 8> &actionSpriteFrameIndices
)
{
    for (uint16_t spriteFrameIndex : actionSpriteFrameIndices)
    {
        appendSpriteFrameTextures(textureRequests, spriteFrameTable, spriteFrameIndex);
    }
}

void appendMapDeltaActors(
    ActorPreviewBillboardSet &billboardSet,
    std::vector<BitmapTextureRequest> &textureRequests,
    const MonsterTable &monsterTable,
    const MapDeltaData &mapDeltaData,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];
        uint16_t spriteFrameIndex = 0;
        uint16_t savedSpriteFrameIndex = 0;
        const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
            monsterTable.findDisplayEntryById(actor.monsterInfoId);
        const MonsterEntry *pMonsterEntry = nullptr;
        std::string resolvedActorName = resolveMapDeltaActorName(monsterTable, actor);

        if (pDisplayEntry != nullptr)
        {
            pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);
        }
        else
        {
            pMonsterEntry = monsterTable.findById(actor.monsterId);
        }

        if (spriteFrameIndex == 0 && pMonsterEntry != nullptr)
        {
            for (const std::string &spriteName : pMonsterEntry->spriteNames)
            {
                if (spriteName.empty())
                {
                    continue;
                }

                const std::optional<uint16_t> frameIndex =
                    billboardSet.spriteFrameTable.findFrameIndexBySpriteName(spriteName);

                if (frameIndex)
                {
                    spriteFrameIndex = *frameIndex;
                    break;
                }
            }
        }

        const std::array<uint16_t, 8> actionSpriteFrameIndices =
            buildMonsterActionSpriteFrameIndices(billboardSet.spriteFrameTable, pMonsterEntry);

        for (const uint16_t spriteId : actor.spriteIds)
        {
            if (spriteId == 0)
            {
                continue;
            }

            const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(spriteId, 0);

            if (pFrame == nullptr)
            {
                continue;
            }

            savedSpriteFrameIndex = spriteId;
            break;
        }

        if (spriteFrameIndex == 0)
        {
            spriteFrameIndex = savedSpriteFrameIndex;
        }

        ActorPreviewBillboard billboard = {};
        billboard.spawnIndex = 0;
        billboard.runtimeActorIndex = actorIndex;
        billboard.spriteFrameIndex = spriteFrameIndex;
        billboard.actionSpriteFrameIndices = actionSpriteFrameIndices;
        billboard.npcId = actor.npcId;
        billboard.monsterId = resolveMapDeltaActorMonsterId(actor);
        billboard.x = actor.x;
        billboard.y = actor.y;
        billboard.z = actor.z;

        if (pOutdoorMapData != nullptr)
        {
            billboard.z = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(billboard.z))));
        }

        billboard.radius = actor.radius;
        billboard.height = actor.height;
        billboard.typeId = 3;
        billboard.index = 0;
        billboard.attributes = static_cast<uint16_t>(actor.attributes & 0xffff);
        billboard.group = actor.group;
        billboard.uniqueNameIndex = actor.uniqueNameIndex;
        billboard.useStaticFrame = spriteFrameIndex != 0 && spriteFrameIndex == savedSpriteFrameIndex;
        billboard.isFriendly = true;
        billboard.source = ActorPreviewSource::Companion;
        billboard.actorName = resolvedActorName;
        billboardSet.billboards.push_back(std::move(billboard));
        ++billboardSet.mapDeltaActorCount;

        appendMonsterActionTextures(textureRequests, billboardSet.spriteFrameTable, actionSpriteFrameIndices);
        appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, spriteFrameIndex);
    }
}

template <typename SpawnType>
void appendSpawnActors(
    ActorPreviewBillboardSet &billboardSet,
    std::vector<BitmapTextureRequest> &textureRequests,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::vector<SpawnType> &spawns,
    const OutdoorMapData *pOutdoorMapData
)
{
    for (size_t spawnIndex = 0; spawnIndex < spawns.size(); ++spawnIndex)
    {
        const SpawnType &spawn = spawns[spawnIndex];
        const std::optional<std::string> monsterName = resolveMonsterNameForSpawn(map, spawn.typeId, spawn.index);

        if (!monsterName)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(*monsterName);

        if (pMonsterEntry == nullptr)
        {
            continue;
        }

        std::string previewSpriteName;

        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (!spriteName.empty())
            {
                previewSpriteName = spriteName;
                break;
            }
        }

        if (previewSpriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex =
            billboardSet.spriteFrameTable.findFrameIndexBySpriteName(previewSpriteName);

        if (!frameIndex)
        {
            continue;
        }

        const std::array<uint16_t, 8> actionSpriteFrameIndices =
            buildMonsterActionSpriteFrameIndices(billboardSet.spriteFrameTable, pMonsterEntry);
        const MonsterTable::MonsterStatsEntry *pStats =
            monsterTable.findStatsByPictureName(*monsterName);

        ActorPreviewBillboard billboard = {};
        billboard.spawnIndex = spawnIndex;
        billboard.runtimeActorIndex = static_cast<size_t>(-1);
        billboard.spriteFrameIndex = *frameIndex;
        billboard.actionSpriteFrameIndices = actionSpriteFrameIndices;
        billboard.monsterId = pStats != nullptr ? static_cast<int16_t>(pStats->id) : 0;
        billboard.x = spawn.x;
        billboard.y = spawn.y;
        billboard.z = spawn.z;

        if (pOutdoorMapData != nullptr)
        {
            billboard.z = static_cast<int>(std::lround(sampleOutdoorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(billboard.z))));
        }

        billboard.radius = static_cast<uint16_t>(std::max<int>(pMonsterEntry->radius, 0));
        billboard.height = static_cast<uint16_t>(std::max<int>(pMonsterEntry->height, 0));
        billboard.typeId = spawn.typeId;
        billboard.index = spawn.index;
        billboard.attributes = spawn.attributes;
        billboard.group = spawn.group;
        billboard.uniqueNameIndex = 0;
        billboard.useStaticFrame = false;
        billboard.isFriendly = true;
        billboard.source = ActorPreviewSource::Spawn;
        billboard.actorName = *monsterName;
        billboardSet.billboards.push_back(std::move(billboard));
        ++billboardSet.spawnActorCount;

        appendMonsterActionTextures(textureRequests, billboardSet.spriteFrameTable, actionSpriteFrameIndices);
        appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, *frameIndex);
    }
}

template <typename SpawnType>
std::optional<ActorPreviewBillboardSet> buildActorPreviewBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::vector<SpawnType> &spawns,
    BitmapLoadCache &bitmapLoadCache,
    const OutdoorMapData *pOutdoorMapData = nullptr,
    bool decodeTextures = true
)
{
    ActorPreviewBillboardSet billboardSet = {};

    std::unordered_set<std::string> neededMonsterFamilies;
    collectMapDeltaMonsterSpriteFamilies(neededMonsterFamilies, monsterTable, mapDeltaData);
    collectSpawnMonsterSpriteFamilies(neededMonsterFamilies, map, monsterTable, spawns);
    collectEncounterMonsterSpriteFamilies(neededMonsterFamilies, monsterTable, map);
    collectSummonMonsterSpriteFamilies(neededMonsterFamilies, monsterTable);

    const std::optional<SpriteFrameTable> spriteFrameTable =
        loadSpriteFrameTable(assetFileSystem, neededMonsterFamilies);

    if (!spriteFrameTable)
    {
        return std::nullopt;
    }

    billboardSet.spriteFrameTable = *spriteFrameTable;

    std::vector<BitmapTextureRequest> textureRequests;

    if (mapDeltaData)
    {
        appendMapDeltaActors(billboardSet, textureRequests, monsterTable, *mapDeltaData, pOutdoorMapData);
    }

    appendSpawnActors(billboardSet, textureRequests, map, monsterTable, spawns, pOutdoorMapData);

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    if (decodeTextures)
    {
        for (const BitmapTextureRequest &textureRequest : textureRequests)
        {
            int textureWidth = 0;
            int textureHeight = 0;
            const std::optional<std::vector<uint8_t>> pixels =
                loadBitmapPixelsBgra(
                    assetFileSystem,
                    "Data/sprites",
                    textureRequest.textureName,
                    textureWidth,
                    textureHeight,
                    false,
                    true,
                    bitmapLoadCache,
                    textureRequest.paletteId);

            if (!pixels || textureWidth <= 0 || textureHeight <= 0)
            {
                continue;
            }

            OutdoorBitmapTexture texture = {};
            texture.textureName = textureRequest.textureName;
            texture.paletteId = textureRequest.paletteId;
            texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, assetFileSystem.getAssetScaleTier());
            texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, assetFileSystem.getAssetScaleTier());
            texture.physicalWidth = textureWidth;
            texture.physicalHeight = textureHeight;
            texture.pixels = *pixels;
            billboardSet.textures.push_back(std::move(texture));
        }
    }

    for (const ActorPreviewBillboard &billboard : billboardSet.billboards)
    {
        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(billboard.spriteFrameIndex, 0);

        if (pFrame == nullptr)
        {
            ++billboardSet.missingTextureActorCount;
            continue;
        }

        if (!decodeTextures)
        {
            ++billboardSet.texturedActorCount;
        }
        else
        {
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const auto textureIt = std::find_if(
                billboardSet.textures.begin(),
                billboardSet.textures.end(),
                [&resolvedTexture, pFrame](const OutdoorBitmapTexture &texture)
                {
                    return texture.textureName == resolvedTexture.textureName && texture.paletteId == pFrame->paletteId;
                }
            );

            if (textureIt == billboardSet.textures.end())
            {
                ++billboardSet.missingTextureActorCount;
            }
            else
            {
                ++billboardSet.texturedActorCount;
            }
        }
    }

    return billboardSet;
}

std::optional<std::vector<uint8_t>> buildOutdoorLandMask(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData
)
{
    const std::optional<std::vector<std::string>> tileTextureNames =
        loadTerrainTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    std::vector<uint8_t> landMask(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1) * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1),
        0
    );

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex =
                static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const std::string &textureName = (*tileTextureNames)[rawTileId];
            const bool isWaterTile = textureName == reinterpret_cast<const char *>(WaterTileName);
            landMask[static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX)] = isWaterTile ? 0 : 1;
        }
    }

    return landMask;
}

std::optional<std::vector<uint32_t>> buildOutdoorTileColors(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData
)
{
    const std::optional<std::vector<std::string>> tileTextureNames =
        loadTerrainTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    std::vector<uint32_t> tileColors(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1) * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1),
        makeAbgr(96, 96, 96)
    );

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex =
                static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const std::string &textureName = (*tileTextureNames)[rawTileId];
            tileColors[static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX)] =
                colorFromTextureName(textureName);
        }
    }

    return tileColors;
}

std::optional<OutdoorTerrainTextureAtlas> buildOutdoorTerrainTextureAtlas(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache,
    const SurfaceMaterialTable *pSurfaceMaterialTable
)
{
    const std::optional<std::vector<std::string>> tileTextureNames =
        loadTerrainTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    const int terrainTileSize = terrainTexturePhysicalTileSize(assetFileSystem.getAssetScaleTier());
    OutdoorTerrainTextureAtlas textureAtlas = {};
    textureAtlas.tileSize = terrainTileSize;
    textureAtlas.width = TerrainTextureAtlasColumns * terrainTileSize;
    textureAtlas.height = TerrainTextureAtlasColumns * terrainTileSize;
    textureAtlas.pixels.resize(static_cast<size_t>(textureAtlas.width * textureAtlas.height * 4), 0);

    std::unordered_map<std::string, std::vector<std::vector<uint8_t>>> animatedTerrainFramesByKey;
    std::unordered_set<std::string> missingTextureNames;
    std::unordered_set<std::string> invalidSizeTextureNames;
    size_t validTileCount = 0;

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const std::string &textureName = (*tileTextureNames)[tileIndex];

        if (textureName.empty() || textureName == "pending")
        {
            continue;
        }

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> tilePixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                true,
                false,
                bitmapLoadCache
            );

        if (!tilePixels)
        {
            missingTextureNames.insert(textureName);
            continue;
        }

        if (textureWidth != terrainTileSize || textureHeight != terrainTileSize)
        {
            invalidSizeTextureNames.insert(
                textureName + " (" + std::to_string(textureWidth) + "x" + std::to_string(textureHeight) + ")");
            continue;
        }

        std::vector<uint8_t> resolvedTilePixels = *tilePixels;
        std::vector<std::vector<uint8_t>> animatedSurfaceFrames;
        SurfaceAnimationSequence surfaceAnimation = staticSurfaceAnimation(textureName);
        const SurfaceMaterialDefinition *pSurfaceMaterial =
            pSurfaceMaterialTable != nullptr ? pSurfaceMaterialTable->findMatch(textureName, 0, true) : nullptr;

        if (pSurfaceMaterial != nullptr && !pSurfaceMaterial->animation.empty())
        {
            surfaceAnimation = pSurfaceMaterial->animation;
            const std::string cacheKey = pSurfaceMaterial->id + "|" + toLowerCopy(textureName);
            const auto cachedFramesIt = animatedTerrainFramesByKey.find(cacheKey);

            if (cachedFramesIt != animatedTerrainFramesByKey.end())
            {
                animatedSurfaceFrames = cachedFramesIt->second;
            }
            else
            {
                animatedSurfaceFrames.reserve(pSurfaceMaterial->animation.frames.size());

                for (const SurfaceAnimationFrame &frame : pSurfaceMaterial->animation.frames)
                {
                    int frameWidth = 0;
                    int frameHeight = 0;
                    const std::optional<std::vector<uint8_t>> framePixels =
                        loadBitmapPixelsBgra(
                            assetFileSystem,
                            "Data/bitmaps",
                            frame.textureName,
                            frameWidth,
                            frameHeight,
                            true,
                            false,
                            bitmapLoadCache
                        );

                    if (!framePixels || frameWidth != terrainTileSize || frameHeight != terrainTileSize)
                    {
                        animatedSurfaceFrames.clear();
                        break;
                    }

                    if (pSurfaceMaterial->terrainTransitionOverlay && isWaterTransitionTerrainTexture(textureName))
                    {
                        animatedSurfaceFrames.push_back(
                            compositeTerrainOverlayOverBase(*framePixels, *tilePixels));
                    }
                    else
                    {
                        animatedSurfaceFrames.push_back(*framePixels);
                    }
                }

                if (!animatedSurfaceFrames.empty())
                {
                    animatedTerrainFramesByKey.emplace(cacheKey, animatedSurfaceFrames);
                }
            }

            if (!animatedSurfaceFrames.empty())
            {
                resolvedTilePixels = animatedSurfaceFrames.front();
            }
        }

        const int atlasColumn = tileIndex % TerrainTextureAtlasColumns;
        const int atlasRow = tileIndex / TerrainTextureAtlasColumns;
        const int atlasX = atlasColumn * terrainTileSize;
        const int atlasY = atlasRow * terrainTileSize;

        for (int row = 0; row < terrainTileSize; ++row)
        {
            const size_t sourceOffset = static_cast<size_t>(row * terrainTileSize * 4);
            const size_t targetOffset = static_cast<size_t>(
                ((atlasY + row) * textureAtlas.width + atlasX) * 4
            );
            std::memcpy(
                textureAtlas.pixels.data() + static_cast<ptrdiff_t>(targetOffset),
                resolvedTilePixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                static_cast<size_t>(terrainTileSize * 4)
            );
        }

        OutdoorTerrainAtlasRegion region = {};
        region.u0 = static_cast<float>(atlasX) / static_cast<float>(textureAtlas.width);
        region.v0 = static_cast<float>(atlasY) / static_cast<float>(textureAtlas.height);
        region.u1 = static_cast<float>(atlasX + terrainTileSize) / static_cast<float>(textureAtlas.width);
        region.v1 = static_cast<float>(atlasY + terrainTileSize) / static_cast<float>(textureAtlas.height);
        region.isValid = true;
        region.isWater = pSurfaceMaterial != nullptr
            && pSurfaceMaterial->semantic == SurfaceMaterialSemantic::Water;
        textureAtlas.tileRegions[static_cast<size_t>(tileIndex)] = region;

        if (!animatedSurfaceFrames.empty())
        {
            OutdoorAnimatedWaterTileSource animatedWaterTile = {};
            animatedWaterTile.region = region;
            animatedWaterTile.framePixels = std::move(animatedSurfaceFrames);
            animatedWaterTile.animation = surfaceAnimation;
            animatedWaterTile.currentFrameIndex = 0;
            textureAtlas.animatedWaterTiles.push_back(std::move(animatedWaterTile));
        }

        ++validTileCount;
    }

    if (!missingTextureNames.empty() || !invalidSizeTextureNames.empty())
    {
        std::cout << "Terrain atlas diagnostics for " << outdoorMapData.fileName
                  << ": master_tile=" << static_cast<int>(outdoorMapData.masterTile)
                  << " valid_tiles=" << validTileCount
                  << " missing_textures=" << missingTextureNames.size()
                  << " invalid_size_textures=" << invalidSizeTextureNames.size() << '\n';

        for (const std::string &textureName : missingTextureNames)
        {
            std::cout << "  missing terrain bitmap: " << textureName << '\n';
        }

        for (const std::string &textureName : invalidSizeTextureNames)
        {
            std::cout << "  invalid terrain bitmap size: " << textureName << '\n';
        }
    }

    return textureAtlas;
}

std::optional<OutdoorBModelTextureSet> buildOutdoorBModelTextureSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache,
    const TextureFrameTable *pTextureFrameTable,
    const SurfaceMaterialTable *pSurfaceMaterialTable
)
{
    std::vector<std::string> textureNames;
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (faceHasInvisibleAttribute(face.attributes) || face.textureName.empty())
            {
                continue;
            }

            const std::string normalizedName = toLowerCopy(face.textureName);
            const SurfaceAnimationSequence animation =
                resolveSurfaceAnimation(
                    face.textureName,
                    face.attributes,
                    false,
                    pTextureFrameTable,
                    pSurfaceMaterialTable);

            appendTextureNameIfMissing(textureNames, normalizedName);
            appendAnimationTextureNamesIfMissing(textureNames, animation);
            appendTextureAnimationBindingIfMissing(animationBindings, normalizedName, animation);
        }
    }

    if (textureNames.empty())
    {
        return std::nullopt;
    }

    OutdoorBModelTextureSet textureSet = {};
    textureSet.animationBindings = animationBindings;

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                false,
                false,
                bitmapLoadCache
            );

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
        textureSet.textures.push_back(std::move(texture));
    }

    if (textureSet.textures.empty())
    {
        return std::nullopt;
    }

    return textureSet;
}

std::optional<IndoorTextureSet> buildIndoorTextureSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const IndoorMapData &indoorMapData,
    BitmapLoadCache &bitmapLoadCache,
    const TextureFrameTable *pTextureFrameTable,
    const SurfaceMaterialTable *pSurfaceMaterialTable
)
{
    std::vector<std::string> textureNames;
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;

    for (const IndoorFace &face : indoorMapData.faces)
    {
        if (faceHasInvisibleAttribute(face.attributes) || face.isPortal || face.textureName.empty())
        {
            continue;
        }

        const std::string normalizedName = toLowerCopy(face.textureName);
        const std::optional<size_t> textureFrameTableIndex =
            face.textureFrameTableIndex > 0 ? std::optional<size_t>(face.textureFrameTableIndex) : std::nullopt;
        const SurfaceAnimationSequence animation =
            resolveSurfaceAnimation(
                face.textureName,
                face.attributes,
                false,
                pTextureFrameTable,
                pSurfaceMaterialTable,
                textureFrameTableIndex);

        appendTextureNameIfMissing(textureNames, normalizedName);
        appendAnimationTextureNamesIfMissing(textureNames, animation);
        appendTextureAnimationBindingIfMissing(animationBindings, normalizedName, animation);
    }

    if (textureNames.empty())
    {
        return std::nullopt;
    }

    IndoorTextureSet textureSet = {};
    textureSet.animationBindings = animationBindings;

    for (const std::string &textureName : textureNames)
    {
        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                false,
                false,
                bitmapLoadCache
            );

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
        textureSet.textures.push_back(std::move(texture));
    }

    if (textureSet.textures.empty())
    {
        return std::nullopt;
    }

    return textureSet;
}
}

std::optional<MapAssetInfo> MapAssetLoader::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    MapLoadPurpose purpose,
    const MapCompanionLoadOptions &companionLoadOptions
) const
{
    const auto loadStart = std::chrono::steady_clock::now();
    BitmapLoadCache bitmapLoadCache = {};
    auto logStageComplete = [&loadStart](const std::string &stageName)
    {
        const auto now = std::chrono::steady_clock::now();
        const auto elapsedMs = std::chrono::duration_cast<std::chrono::milliseconds>(now - loadStart).count();
        std::cout << "  [" << elapsedMs << " ms] " << stageName << '\n';
    };

    std::cout << "Loading map assets for " << map.fileName << "...\n";
    const std::optional<std::string> geometryPath = findAssetPath(assetFileSystem, map.fileName);

    if (!geometryPath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> geometryBytes = assetFileSystem.readBinaryFile(*geometryPath);

    if (!geometryBytes)
    {
        return std::nullopt;
    }

    logStageComplete("geometry bytes loaded");

    MapAssetInfo assetInfo = {};
    assetInfo.map = map;
    assetInfo.geometryPath = *geometryPath;
    assetInfo.geometrySize = geometryBytes->size();
    assetInfo.geometryHeader.assign(
        geometryBytes->begin(),
        geometryBytes->begin() + std::min<size_t>(geometryBytes->size(), 64)
    );

    std::optional<std::vector<uint8_t>> companionBytes;
    std::optional<std::string> sceneText;

    const std::optional<std::string> companionFileName =
        companionLoadOptions.allowLegacyCompanion ? buildCompanionFileName(map.fileName) : std::nullopt;

    if (companionFileName)
    {
        const std::optional<std::string> companionPath = findAssetPath(assetFileSystem, *companionFileName);

        if (companionPath)
        {
            companionBytes = assetFileSystem.readBinaryFile(*companionPath);

            if (companionBytes)
            {
                assetInfo.companionPath = companionPath;
                assetInfo.companionSize = companionBytes->size();
                logStageComplete("companion bytes loaded");
            }
        }
    }

    const std::optional<std::string> sceneFileName =
        companionLoadOptions.allowSceneYml ? buildSceneFileName(map.fileName) : std::nullopt;

    if (sceneFileName)
    {
        const std::optional<std::string> scenePath = findAssetPath(assetFileSystem, *sceneFileName);

        if (scenePath)
        {
            sceneText = assetFileSystem.readTextFile(*scenePath);

            if (sceneText)
            {
                assetInfo.scenePath = scenePath;
                assetInfo.sceneSize = sceneText->size();
                logStageComplete("scene yml loaded");
            }
        }
    }

    std::optional<TextureFrameTable> textureFrameTable;
    std::optional<SurfaceMaterialTable> surfaceMaterialTable;

    if (purpose == MapLoadPurpose::Full || purpose == MapLoadPurpose::FullGameplay)
    {
        textureFrameTable = loadTextureFrameTable(assetFileSystem);
        logStageComplete("texture frame table loaded");
        surfaceMaterialTable = loadSurfaceMaterialTable(assetFileSystem);
        logStageComplete("surface materials loaded");
    }

    const std::string normalizedFileName = toLowerCopy(map.fileName);

    if (normalizedFileName.ends_with(".odm"))
    {
        const OutdoorMapDataLoader outdoorMapDataLoader;
        assetInfo.outdoorMapData = outdoorMapDataLoader.loadFromBytes(*geometryBytes);
        logStageComplete("outdoor geometry parsed");

        if (assetInfo.outdoorMapData)
        {
            if (sceneText)
            {
                OutdoorSceneYmlLoader sceneLoader = {};
                std::string sceneError;
                const std::optional<OutdoorSceneData> sceneData = sceneLoader.loadFromText(*sceneText, sceneError);

                if (!sceneData)
                {
                    std::cerr << "Failed to parse outdoor scene yml for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                if (!sceneData->geometryFile.empty()
                    && toLowerCopy(sceneData->geometryFile) != toLowerCopy(map.fileName))
                {
                    std::cerr << "Failed to build outdoor scene state for " << map.fileName
                              << ": scene geometry_file does not match loaded outdoor geometry\n";
                    return std::nullopt;
                }

                MapDeltaData sceneMapDeltaData = {};

                if (!buildOutdoorMapStateFromScene(
                        *sceneData,
                        *assetInfo.outdoorMapData,
                        sceneMapDeltaData,
                        sceneError))
                {
                    std::cerr << "Failed to build outdoor scene state for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                assetInfo.outdoorMapDeltaData = std::move(sceneMapDeltaData);
                assetInfo.authoredCompanionSource = AuthoredCompanionSource::SceneYml;
                logStageComplete("outdoor scene yml applied");
            }
            else if (companionBytes)
            {
                const MapDeltaDataLoader mapDeltaDataLoader;
                assetInfo.outdoorMapDeltaData =
                    mapDeltaDataLoader.loadOutdoorFromBytes(*companionBytes, *assetInfo.outdoorMapData);

                if (assetInfo.outdoorMapDeltaData)
                {
                    assetInfo.authoredCompanionSource = AuthoredCompanionSource::LegacyCompanion;
                    logStageComplete("outdoor map delta parsed");
                }
            }

            if (purpose == MapLoadPurpose::Full || purpose == MapLoadPurpose::FullGameplay)
            {
                assetInfo.outdoorLandMask = buildOutdoorLandMask(assetFileSystem, *assetInfo.outdoorMapData);
                logStageComplete("outdoor land mask built");
                assetInfo.outdoorTileColors = buildOutdoorTileColors(assetFileSystem, *assetInfo.outdoorMapData);
                logStageComplete("outdoor tile colors built");
                assetInfo.outdoorTerrainTextureAtlas =
                    buildOutdoorTerrainTextureAtlas(
                        assetFileSystem,
                        *assetInfo.outdoorMapData,
                        bitmapLoadCache,
                        surfaceMaterialTable ? &*surfaceMaterialTable : nullptr);
                logStageComplete("outdoor terrain textures built");
                assetInfo.outdoorBModelTextureSet =
                    buildOutdoorBModelTextureSet(
                        assetFileSystem,
                        *assetInfo.outdoorMapData,
                        bitmapLoadCache,
                        textureFrameTable ? &*textureFrameTable : nullptr,
                        surfaceMaterialTable ? &*surfaceMaterialTable : nullptr);
                logStageComplete("outdoor bmodel textures built");
                assetInfo.outdoorDecorationCollisionSet =
                    buildOutdoorDecorationCollisionSet(assetFileSystem, assetInfo.outdoorMapData->entities);
                logStageComplete("outdoor decoration collisions built");
                assetInfo.outdoorActorCollisionSet =
                    buildOutdoorActorCollisionSet(
                        map,
                        monsterTable,
                        assetInfo.outdoorMapDeltaData,
                        assetInfo.outdoorMapData->spawns,
                        &*assetInfo.outdoorMapData
                    );
                logStageComplete("outdoor actor collisions built");
                assetInfo.outdoorSpriteObjectCollisionSet =
                    buildOutdoorSpriteObjectCollisionSet(objectTable, assetInfo.outdoorMapDeltaData);
                logStageComplete("outdoor sprite object collisions built");
                assetInfo.outdoorDecorationBillboardSet =
                    buildOutdoorDecorationBillboardSet(assetFileSystem, *assetInfo.outdoorMapData, bitmapLoadCache);
                logStageComplete("outdoor decoration billboards built");
                assetInfo.outdoorActorPreviewBillboardSet =
                    buildActorPreviewBillboardSet(
                        assetFileSystem,
                        map,
                        monsterTable,
                        assetInfo.outdoorMapDeltaData,
                        assetInfo.outdoorMapData->spawns,
                        bitmapLoadCache,
                        &*assetInfo.outdoorMapData,
                        purpose == MapLoadPurpose::Full
                    );
                logStageComplete("outdoor actor previews built");
                assetInfo.outdoorSpriteObjectBillboardSet =
                    buildSpriteObjectBillboardSet(
                        assetFileSystem,
                        objectTable,
                        assetInfo.outdoorMapDeltaData,
                        bitmapLoadCache
                    );
                logStageComplete("outdoor sprite objects built");

                if (assetInfo.outdoorActorPreviewBillboardSet)
                {
                    const ActorPreviewBillboardSet &actorSet = *assetInfo.outdoorActorPreviewBillboardSet;
                    std::cout
                        << "  outdoor actors: total=" << actorSet.billboards.size()
                        << " map_delta=" << actorSet.mapDeltaActorCount
                        << " spawn=" << actorSet.spawnActorCount
                        << " textured=" << actorSet.texturedActorCount
                        << " missing=" << actorSet.missingTextureActorCount << '\n';
                }

                if (assetInfo.outdoorSpriteObjectBillboardSet)
                {
                    const SpriteObjectBillboardSet &objectSet = *assetInfo.outdoorSpriteObjectBillboardSet;
                    std::cout
                        << "  outdoor sprite objects: total=" << objectSet.billboards.size()
                        << " textured=" << objectSet.texturedObjectCount
                        << " missing=" << objectSet.missingTextureObjectCount << '\n';

                    for (const SpriteObjectBillboard &billboard : objectSet.billboards)
                    {
                        std::cout
                            << "    object"
                            << " name=\"" << billboard.objectName << "\""
                            << " desc=" << billboard.objectDescriptionId
                            << " sprite=" << billboard.objectSpriteId
                            << " x=" << billboard.x
                            << " y=" << billboard.y
                            << " z=" << billboard.z
                            << " h=" << billboard.height
                            << " r=" << billboard.radius
                            << " attr=0x" << std::hex << billboard.attributes << std::dec
                            << " sound=" << billboard.soundId
                            << " sector=" << billboard.sectorId
                            << " life_ticks=" << billboard.timeSinceCreatedTicks
                            << " temp=" << billboard.temporaryLifetime
                            << " glow=" << billboard.glowRadiusMultiplier
                            << " spell=" << billboard.spellId
                            << " lvl=" << billboard.spellLevel
                            << " skill=" << billboard.spellSkill
                            << " caster=" << billboard.spellCasterPid
                            << " target=" << billboard.spellTargetPid
                            << '\n';
                    }
                }
            }
            else
            {
                std::cout
                    << "  headless gameplay load: skipped outdoor render assets"
                        << '\n';
            }
        }
    }
    else if (normalizedFileName.ends_with(".blv"))
    {
        const IndoorMapDataLoader indoorMapDataLoader;
        assetInfo.indoorMapData = indoorMapDataLoader.loadFromBytes(*geometryBytes);
        logStageComplete("indoor geometry parsed");

        if (assetInfo.indoorMapData)
        {
            if (companionBytes)
            {
                const MapDeltaDataLoader mapDeltaDataLoader;
                assetInfo.indoorMapDeltaData =
                    mapDeltaDataLoader.loadIndoorFromBytes(*companionBytes, *assetInfo.indoorMapData);

                if (assetInfo.indoorMapDeltaData)
                {
                    logStageComplete("indoor map delta parsed");
                }
            }

            if (purpose == MapLoadPurpose::Full || purpose == MapLoadPurpose::FullGameplay)
            {
                assetInfo.indoorTextureSet = buildIndoorTextureSet(
                    assetFileSystem,
                    *assetInfo.indoorMapData,
                    bitmapLoadCache,
                    textureFrameTable ? &*textureFrameTable : nullptr,
                    surfaceMaterialTable ? &*surfaceMaterialTable : nullptr
                );
                logStageComplete("indoor textures built");
                assetInfo.indoorDecorationBillboardSet =
                    buildIndoorDecorationBillboardSet(assetFileSystem, *assetInfo.indoorMapData, bitmapLoadCache);
                logStageComplete("indoor decoration billboards built");
                assetInfo.indoorActorPreviewBillboardSet =
                    buildActorPreviewBillboardSet(
                        assetFileSystem,
                        map,
                        monsterTable,
                        assetInfo.indoorMapDeltaData,
                        assetInfo.indoorMapData->spawns,
                        bitmapLoadCache,
                        nullptr,
                        true
                    );
                logStageComplete("indoor actor previews built");
                assetInfo.indoorSpriteObjectBillboardSet =
                    buildSpriteObjectBillboardSet(
                        assetFileSystem,
                        objectTable,
                        assetInfo.indoorMapDeltaData,
                        bitmapLoadCache
                    );
                logStageComplete("indoor sprite objects built");

                if (assetInfo.indoorActorPreviewBillboardSet)
                {
                    const ActorPreviewBillboardSet &actorSet = *assetInfo.indoorActorPreviewBillboardSet;
                    std::cout
                        << "  indoor actors: total=" << actorSet.billboards.size()
                        << " map_delta=" << actorSet.mapDeltaActorCount
                        << " spawn=" << actorSet.spawnActorCount
                        << " textured=" << actorSet.texturedActorCount
                        << " missing=" << actorSet.missingTextureActorCount << '\n';
                }

                if (assetInfo.indoorSpriteObjectBillboardSet)
                {
                    const SpriteObjectBillboardSet &objectSet = *assetInfo.indoorSpriteObjectBillboardSet;
                    std::cout
                        << "  indoor sprite objects: total=" << objectSet.billboards.size()
                        << " textured=" << objectSet.texturedObjectCount
                        << " missing=" << objectSet.missingTextureObjectCount << '\n';

                    for (const SpriteObjectBillboard &billboard : objectSet.billboards)
                    {
                        std::cout
                            << "    object"
                            << " name=\"" << billboard.objectName << "\""
                            << " desc=" << billboard.objectDescriptionId
                            << " sprite=" << billboard.objectSpriteId
                            << " x=" << billboard.x
                            << " y=" << billboard.y
                            << " z=" << billboard.z
                            << " h=" << billboard.height
                            << " r=" << billboard.radius
                            << " attr=0x" << std::hex << billboard.attributes << std::dec
                            << " sound=" << billboard.soundId
                            << " sector=" << billboard.sectorId
                            << " life_ticks=" << billboard.timeSinceCreatedTicks
                            << " temp=" << billboard.temporaryLifetime
                            << " glow=" << billboard.glowRadiusMultiplier
                            << " spell=" << billboard.spellId
                            << " lvl=" << billboard.spellLevel
                            << " skill=" << billboard.spellSkill
                            << " caster=" << billboard.spellCasterPid
                            << " target=" << billboard.spellTargetPid
                            << '\n';
                    }
                }
            }
            else
            {
                std::cout
                    << "  headless gameplay load: skipped indoor render assets"
                        << '\n';
            }
        }
    }

    logStageComplete("map asset load complete");

    return assetInfo;
}

std::string MapAssetLoader::toLower(const std::string &value)
{
    std::string lowered = value;

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}

std::optional<std::string> MapAssetLoader::findAssetPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &fileName
)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    const std::string normalizedFileName = toLower(fileName);

    for (const std::string &entry : entries)
    {
        if (toLower(entry) == normalizedFileName)
        {
            return std::string("Data/games/") + entry;
        }
    }

    return std::nullopt;
}

std::optional<std::string> MapAssetLoader::buildCompanionFileName(const std::string &fileName)
{
    const std::string normalized = toLower(fileName);

    if (normalized.size() < 4)
    {
        return std::nullopt;
    }

    const std::string stem = normalized.substr(0, normalized.size() - 4);
    const std::string extension = normalized.substr(normalized.size() - 4);

    if (extension == ".odm")
    {
        return stem + ".ddm";
    }

    if (extension == ".blv")
    {
        return stem + ".dlv";
    }

    return std::nullopt;
}

std::optional<std::string> MapAssetLoader::buildSceneFileName(const std::string &fileName)
{
    const std::string normalized = toLower(fileName);

    if (normalized.size() < 4)
    {
        return std::nullopt;
    }

    const std::string stem = normalized.substr(0, normalized.size() - 4);
    const std::string extension = normalized.substr(normalized.size() - 4);

    if (extension == ".odm")
    {
        return stem + ".scene.yml";
    }

    return std::nullopt;
}
}
