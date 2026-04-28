#include "game/data/GameDataLoader.h"

#include "game/arcomage/ArcomageLoader.h"
#include "engine/TextTable.h"
#include "game/FaceEnums.h"
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
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr bool VerboseMapLoadLogging = false;

std::optional<std::string> readFirstExistingText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath
)
{
    for (const std::string &candidate : candidates)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(candidate);

        if (text)
        {
            resolvedPath = candidate;
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
    const std::vector<std::filesystem::path> &candidates,
    std::string &resolvedPath)
{
    for (const std::filesystem::path &candidate : candidates)
    {
        if (candidate.empty() || !std::filesystem::exists(candidate) || !std::filesystem::is_regular_file(candidate))
        {
            continue;
        }

        std::string text;

        if (!readPhysicalTextFile(candidate, text))
        {
            continue;
        }

        resolvedPath = candidate.lexically_normal().generic_string();
        return text;
    }

    return std::nullopt;
}

std::string mapScriptBaseName(const std::string &fileName)
{
    const std::filesystem::path path(fileName);
    return path.stem().string();
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
    const std::optional<std::filesystem::path> &geometryPath,
    const std::optional<std::filesystem::path> &scenePath)
{
    const std::string lowerBaseName = toLowerCopy(baseName);
    std::vector<std::filesystem::path> candidates;

    const auto appendDirectoryCandidates =
        [&](const std::optional<std::filesystem::path> &directory)
    {
        if (!directory || directory->empty())
        {
            return;
        }

        const std::filesystem::path normalizedDirectory = directory->lexically_normal();
        const std::filesystem::path lowerCandidate = normalizedDirectory / (lowerBaseName + ".lua");
        candidates.push_back(lowerCandidate);

        const std::filesystem::path exactCandidate = normalizedDirectory / (baseName + ".lua");

        if (exactCandidate != lowerCandidate)
        {
            candidates.push_back(exactCandidate);
        }
    };

    appendDirectoryCandidates(geometryPath ? std::optional<std::filesystem::path>(geometryPath->parent_path()) : std::nullopt);
    appendDirectoryCandidates(scenePath ? std::optional<std::filesystem::path>(scenePath->parent_path()) : std::nullopt);
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

std::string dataTablePath(std::string_view fileName)
{
    return "Data/data_tables/" + std::string(fileName);
}

std::string englishDataTablePath(std::string_view fileName)
{
    return "Data/data_tables/english/" + std::string(fileName);
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
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    if (eventId == 0)
    {
        return {};
    }

    if (localEventProgram && localEventProgram->hasEvent(eventId))
    {
        return localEventProgram->getOpenedChestIds(eventId);
    }

    if (globalEventProgram && globalEventProgram->hasEvent(eventId))
    {
        return globalEventProgram->getOpenedChestIds(eventId);
    }

    return {};
}

const ScriptedEventProgram *findOwningEventProgram(
    uint16_t eventId,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram)
{
    if (eventId == 0)
    {
        return nullptr;
    }

    if (localEventProgram && localEventProgram->hasEvent(eventId))
    {
        return &*localEventProgram;
    }

    if (localEventProgram && localEventProgram->isHintOnlyEvent(eventId))
    {
        return &*localEventProgram;
    }

    if (globalEventProgram && globalEventProgram->hasEvent(eventId))
    {
        return &*globalEventProgram;
    }

    if (globalEventProgram && globalEventProgram->isHintOnlyEvent(eventId))
    {
        return &*globalEventProgram;
    }

    return nullptr;
}

uint32_t normalizedHintOnlyAttributes(uint32_t attributes, bool hintOnly)
{
    if (hintOnly)
    {
        return attributes | faceAttributeBit(FaceAttribute::HasHint);
    }

    return attributes & ~faceAttributeBit(FaceAttribute::HasHint);
}

void normalizeOutdoorFaceHintOnlyAttributes(
    OutdoorMapData &outdoorMapData,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram)
{
    for (OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.cogTriggeredNumber == 0)
            {
                continue;
            }

            const ScriptedEventProgram *pProgram =
                findOwningEventProgram(face.cogTriggeredNumber, localEventProgram, globalEventProgram);

            if (pProgram == nullptr)
            {
                continue;
            }

            face.attributes =
                normalizedHintOnlyAttributes(face.attributes, pProgram->isHintOnlyEvent(face.cogTriggeredNumber));
        }
    }
}

void normalizeIndoorFaceHintOnlyAttributes(
    IndoorMapData &indoorMapData,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram)
{
    for (IndoorFace &face : indoorMapData.faces)
    {
        if (face.cogTriggered == 0)
        {
            continue;
        }

        const ScriptedEventProgram *pProgram =
            findOwningEventProgram(face.cogTriggered, localEventProgram, globalEventProgram);

        if (pProgram == nullptr)
        {
            continue;
        }

        face.attributes = normalizedHintOnlyAttributes(face.attributes, pProgram->isHintOnlyEvent(face.cogTriggered));
    }
}

void normalizeMapFaceHintOnlyAttributes(
    MapAssetInfo &mapAssetInfo,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram)
{
    if (mapAssetInfo.outdoorMapData)
    {
        normalizeOutdoorFaceHintOnlyAttributes(*mapAssetInfo.outdoorMapData, localEventProgram, globalEventProgram);
    }

    if (mapAssetInfo.indoorMapData)
    {
        normalizeIndoorFaceHintOnlyAttributes(*mapAssetInfo.indoorMapData, localEventProgram, globalEventProgram);
    }
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
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    bool anyLinks = false;

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OutdoorEntity &entity = outdoorMapData.entities[entityIndex];

        for (const uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
        {
            const std::vector<uint32_t> chestIds = getOpenedChestIds(eventId, localEventProgram, globalEventProgram);

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
                localEventProgram,
                globalEventProgram
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
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    bool anyLinks = false;

    for (size_t entityIndex = 0; entityIndex < indoorMapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = indoorMapData.entities[entityIndex];

        for (const uint16_t eventId : {entity.eventIdPrimary, entity.eventIdSecondary})
        {
            const std::vector<uint32_t> chestIds = getOpenedChestIds(eventId, localEventProgram, globalEventProgram);

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
        const std::vector<uint32_t> chestIds = getOpenedChestIds(face.cogTriggered, localEventProgram, globalEventProgram);

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

        const std::vector<uint32_t> chestIds = getOpenedChestIds(eventId, localEventProgram, globalEventProgram);

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

void appendDecorationScriptBillboardTextures(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    std::optional<DecorationBillboardSet> &billboardSet
)
{
    if (!billboardSet)
    {
        return;
    }

    std::vector<std::string> spriteNames;

    if (localEventProgram)
    {
        spriteNames.insert(
            spriteNames.end(),
            localEventProgram->spriteNames().begin(),
            localEventProgram->spriteNames().end());
    }

    if (globalEventProgram)
    {
        spriteNames.insert(
            spriteNames.end(),
            globalEventProgram->spriteNames().begin(),
            globalEventProgram->spriteNames().end());
    }

    std::sort(spriteNames.begin(), spriteNames.end());
    spriteNames.erase(std::unique(spriteNames.begin(), spriteNames.end()), spriteNames.end());

    if (spriteNames.empty())
    {
        return;
    }

    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;

    for (const std::string &spriteName : spriteNames)
    {
        uint16_t spriteId = 0;

        if (const DecorationEntry *pDecoration = billboardSet->decorationTable.findByInternalName(spriteName))
        {
            spriteId = pDecoration->spriteId;
        }
        else if (const std::optional<uint16_t> frameIndex =
                     billboardSet->spriteFrameTable.findFrameIndexBySpriteName(spriteName))
        {
            spriteId = *frameIndex;
        }

        if (spriteId == 0)
        {
            continue;
        }

        const std::vector<std::string> textureNames = billboardSet->spriteFrameTable.collectTextureNames(spriteId);

        for (const std::string &textureName : textureNames)
        {
            bool alreadyPresent = false;

            for (const OutdoorBitmapTexture &texture : billboardSet->textures)
            {
                if (toLowerCopy(texture.textureName) == toLowerCopy(textureName))
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
            texture.textureName = toLowerCopy(textureName);
            texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, assetFileSystem.getAssetScaleTier());
            texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, assetFileSystem.getAssetScaleTier());
            texture.physicalWidth = textureWidth;
            texture.physicalHeight = textureHeight;
            texture.pixels = *pixels;
            billboardSet->textures.push_back(std::move(texture));
        }
    }
}

void appendIndoorScriptTextures(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    std::optional<IndoorTextureSet> &indoorTextureSet
)
{
    if (!indoorTextureSet)
    {
        return;
    }

    std::vector<std::string> textureNames;

    if (localEventProgram)
    {
        textureNames.insert(
            textureNames.end(),
            localEventProgram->textureNames().begin(),
            localEventProgram->textureNames().end());
    }

    if (globalEventProgram)
    {
        textureNames.insert(
            textureNames.end(),
            globalEventProgram->textureNames().begin(),
            globalEventProgram->textureNames().end());
    }

    std::sort(textureNames.begin(), textureNames.end());
    textureNames.erase(std::unique(textureNames.begin(), textureNames.end()), textureNames.end());

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

    if (!loadClassMultiplierTable(assetFileSystem))
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

    if (!loadRaceStartingStatsTable(assetFileSystem))
    {
        return false;
    }

    if (!loadReadableScrollTable(assetFileSystem))
    {
        return false;
    }

    if (!loadPotionMixingTable(assetFileSystem))
    {
        return false;
    }

    if (!loadArcomageLibrary(assetFileSystem))
    {
        return false;
    }

    if (!loadPortraitFrameTable(assetFileSystem))
    {
        return false;
    }

    if (!loadIconFrameTable(assetFileSystem))
    {
        return false;
    }

    if (!loadSpellFxTable(assetFileSystem))
    {
        return false;
    }

    if (!loadPortraitFxEventTable(assetFileSystem))
    {
        return false;
    }

    if (!loadFaceAnimationTable(assetFileSystem))
    {
        return false;
    }

    if (!loadTransitionTable(assetFileSystem))
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
        dataTablePath("spells.txt"),
        dataTablePath("random_items.txt"),
        englishDataTablePath("scroll.txt")
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

    if constexpr (VerboseMapLoadLogging)
    {
        std::cout << "Loaded gameplay tables:\n";
        std::cout << "  " << dataTablePath("map_stats.txt")
                  << " entries=" << m_mapStats.getEntries().size() << '\n';

        for (const LoadedTableSummary &loadedTable : m_loadedTables)
        {
            std::cout << "  " << loadedTable.virtualPath
                      << " rows=" << loadedTable.dataRowCount
                      << " columns=" << loadedTable.columnCount << '\n';
        }
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

const ClassMultiplierTable &GameDataLoader::getClassMultiplierTable() const
{
    return m_classMultiplierTable;
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

const RaceStartingStatsTable &GameDataLoader::getRaceStartingStatsTable() const
{
    return m_raceStartingStatsTable;
}

const ReadableScrollTable &GameDataLoader::getReadableScrollTable() const
{
    return m_readableScrollTable;
}

const PotionMixingTable &GameDataLoader::getPotionMixingTable() const
{
    return m_potionMixingTable;
}

const ArcomageLibrary &GameDataLoader::getArcomageLibrary() const
{
    return m_arcomageLibrary;
}

const PortraitFrameTable &GameDataLoader::getPortraitFrameTable() const
{
    return m_portraitFrameTable;
}

const IconFrameTable &GameDataLoader::getIconFrameTable() const
{
    return m_iconFrameTable;
}

const SpellFxTable &GameDataLoader::getSpellFxTable() const
{
    return m_spellFxTable;
}

const PortraitFxEventTable &GameDataLoader::getPortraitFxEventTable() const
{
    return m_portraitFxEventTable;
}

const FaceAnimationTable &GameDataLoader::getFaceAnimationTable() const
{
    return m_faceAnimationTable;
}

const TransitionTable &GameDataLoader::getTransitionTable() const
{
    return m_transitionTable;
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
    const std::string mapStatsPath = dataTablePath("map_stats.txt");
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(mapStatsPath);

    if (!fileContents)
    {
        std::cerr << "Failed to read typed gameplay table: " << mapStatsPath << '\n';
        return false;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*fileContents);

    if (!parsedTable)
    {
        std::cerr << "Failed to parse typed gameplay table: " << mapStatsPath << '\n';
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

    const std::string navigationPath = dataTablePath("map_navigation.txt");
    const std::optional<std::string> navigationContents = assetFileSystem.readTextFile(navigationPath);

    if (navigationContents.has_value())
    {
        const std::optional<Engine::TextTable> navigationTable =
            Engine::TextTable::parseTabSeparated(*navigationContents);

        if (!navigationTable)
        {
            std::cerr << "Failed to parse typed gameplay table: " << navigationPath << '\n';
            return false;
        }

        std::vector<std::vector<std::string>> navigationRows;

        for (size_t rowIndex = 0; rowIndex < navigationTable->getRowCount(); ++rowIndex)
        {
            navigationRows.push_back(navigationTable->getRow(rowIndex));
        }

        if (!m_mapStats.applyOutdoorNavigationRows(navigationRows))
        {
            return false;
        }
    }

    m_mapRegistry.initialize(m_mapStats.getEntries());
    return true;
}

bool GameDataLoader::loadMonsterTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> monsterDataRows;

    const std::string monsterDataPath = dataTablePath("monster_data.txt");

    if (!loadTextTableRows(assetFileSystem, monsterDataPath, monsterDataRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> monsterDescriptorRows;

    const std::string monsterDescriptorPath = dataTablePath("monster_descriptors.txt");

    if (!loadTextTableRows(assetFileSystem, monsterDescriptorPath, monsterDescriptorRows))
    {
        return false;
    }

    if (!m_monsterTable.loadEntriesFromRows(monsterDescriptorRows))
    {
        std::cerr << "Failed to parse monster descriptor data: " << monsterDescriptorPath << '\n';
        return false;
    }

    if (!m_monsterTable.loadDisplayNamesFromRows(monsterDataRows))
    {
        std::cerr << "Failed to parse monster display names: " << monsterDataPath << '\n';
        return false;
    }

    if (!m_monsterTable.loadStatsFromRows(monsterDataRows))
    {
        std::cerr << "Failed to parse monster runtime stats: " << monsterDataPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> placedMonsterRows;

    const std::string placeMonPath = englishDataTablePath("place_mon.txt");

    if (!loadTextTableRows(assetFileSystem, placeMonPath, placedMonsterRows))
    {
        return false;
    }

    if (!m_monsterTable.loadUniqueNamesFromRows(placedMonsterRows))
    {
        std::cerr << "Failed to parse placed monster names: " << placeMonPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> monsterRelationRows;

    const std::string monsterRelationPath = dataTablePath("monster_relation_data.txt");

    if (!loadTextTableRows(assetFileSystem, monsterRelationPath, monsterRelationRows))
    {
        return false;
    }

    if (!m_monsterTable.loadRelationsFromRows(monsterRelationRows))
    {
        std::cerr << "Failed to parse monster relation table: " << monsterRelationPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadHouseTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string sourcePath = dataTablePath("house_data.txt");

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

    if (loadTextTableRows(assetFileSystem, dataTablePath("house_animations.txt"), animationRows))
    {
        m_houseTable.loadAnimationRows(animationRows);
    }

    std::vector<std::vector<std::string>> transportRows;

    if (loadTextTableRows(assetFileSystem, dataTablePath("transport_schedules.txt"), transportRows))
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
            {dataTablePath("npc_greet.txt")},
            greetingRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> textRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {dataTablePath("npc_topic_text.txt")},
            textRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> topicRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {dataTablePath("npc_topic.txt")},
            topicRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> npcRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {dataTablePath("npc.txt")},
            npcRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> newsRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {dataTablePath("npc_news.txt")},
            newsRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> groupRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {englishDataTablePath("npc_group.txt")},
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

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("quests.txt")}, questRows))
    {
        std::cerr << "Failed to read journal quest table\n";
        return false;
    }

    std::vector<std::vector<std::string>> historyRows;

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("history.txt")}, historyRows))
    {
        std::cerr << "Failed to read journal history table\n";
        return false;
    }

    std::vector<std::vector<std::string>> autonoteRows;

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("autonote.txt")}, autonoteRows))
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

    if (!loadTextTableRows(assetFileSystem, dataTablePath("class_skills.txt"), capRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> startingRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("class_starting_skills.txt"), startingRows))
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

bool GameDataLoader::loadClassMultiplierTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("class_multipliers.txt"), rows))
    {
        return false;
    }

    if (!m_classMultiplierTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse class multiplier table\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadRosterTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    const std::string rosterPath = dataTablePath("roster.txt");

    if (!loadTextTableRows(assetFileSystem, rosterPath, rows))
    {
        return false;
    }

    if (!m_rosterTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse roster table: " << rosterPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadCharacterDollTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> characterRows;

    const std::string characterDataPath = dataTablePath("character_data.txt");

    if (!loadTextTableRows(assetFileSystem, characterDataPath, characterRows))
    {
        std::cerr << "Failed to read character doll table: " << characterDataPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> dollTypeRows;

    const std::string dollTypesPath = dataTablePath("doll_types.txt");

    if (!loadTextTableRows(assetFileSystem, dollTypesPath, dollTypeRows))
    {
        std::cerr << "Failed to read doll type table: " << dollTypesPath << '\n';
        return false;
    }

    if (!m_characterDollTable.loadCharacterRows(characterRows))
    {
        std::cerr << "Failed to parse character doll table: " << characterDataPath << '\n';
        return false;
    }

    if (!m_characterDollTable.loadDollTypeRows(dollTypeRows))
    {
        std::cerr << "Failed to parse doll type table: " << dollTypesPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadCharacterInspectTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> statRows;

    const std::string statsPath = englishDataTablePath("stats.txt");

    if (!loadTextTableRows(assetFileSystem, statsPath, statRows))
    {
        std::cerr << "Failed to read character inspect table: " << statsPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> skillRows;

    const std::string skillDesPath = englishDataTablePath("skill_des.txt");

    if (!loadTextTableRows(assetFileSystem, skillDesPath, skillRows))
    {
        std::cerr << "Failed to read character inspect table: " << skillDesPath << '\n';
        return false;
    }

    if (!m_characterInspectTable.loadStatRows(statRows) || !m_characterInspectTable.loadSkillRows(skillRows))
    {
        std::cerr << "Failed to parse character inspect tables\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadRaceStartingStatsTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = dataTablePath("race_starting_stats.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read race starting stats table: " << tablePath << '\n';
        return false;
    }

    if (!m_raceStartingStatsTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse race starting stats table: " << tablePath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadReadableScrollTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("scroll.txt")}, rows))
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

bool GameDataLoader::loadPotionMixingTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("potion.txt")}, rows))
    {
        return false;
    }

    if (!m_potionMixingTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse potion mixing table\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadTransitionTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("trans.txt")}, rows))
    {
        return false;
    }

    if (!m_transitionTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse transition table.\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadArcomageLibrary(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> ruleRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("arcomage_rules.txt"), ruleRows))
    {
        std::cerr << "Failed to read Arcomage tavern rule table\n";
        return false;
    }

    std::vector<std::vector<std::string>> cardRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("arcomage_cards.txt"), cardRows))
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

bool GameDataLoader::loadPortraitFrameTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = dataTablePath("portrait_frame_data.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read portrait frame table: " << tablePath << '\n';
        return false;
    }

    if (!m_portraitFrameTable.loadRows(rows))
    {
        std::cerr << "Failed to parse portrait frame table: " << tablePath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadIconFrameTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = dataTablePath("icon_frame_data.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read icon frame table: " << tablePath << '\n';
        return false;
    }

    if (!m_iconFrameTable.loadRows(rows))
    {
        std::cerr << "Failed to parse icon frame table: " << tablePath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadSpellFxTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = dataTablePath("spell_fx.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read spell FX table: " << tablePath << '\n';
        return false;
    }

    if (!m_spellFxTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse spell FX table: " << tablePath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadPortraitFxEventTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = dataTablePath("portrait_fx_events.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read portrait FX event table: " << tablePath << '\n';
        return false;
    }

    if (!m_portraitFxEventTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse portrait FX event table: " << tablePath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadFaceAnimationTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = dataTablePath("face_animations.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read face animation table: " << tablePath << '\n';
        return false;
    }

    if (!m_faceAnimationTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse face animation table: " << tablePath << '\n';
        return false;
    }

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
    std::vector<std::vector<std::string>> objectRows;
    const std::string objectListPath = dataTablePath("object_list.txt");

    if (!loadTextTableRows(assetFileSystem, objectListPath, objectRows))
    {
        return false;
    }

    if (!m_objectTable.loadRows(objectRows))
    {
        std::cerr << "Failed to parse object table from " << objectListPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadMonsterProjectileTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    const std::string monsterProjectilesPath = dataTablePath("monster_projectiles.txt");

    if (!loadTextTableRows(assetFileSystem, monsterProjectilesPath, rows))
    {
        return false;
    }

    if (!m_monsterProjectileTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse monster projectile table: " << monsterProjectilesPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadSpellTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    const std::string spellsPath = dataTablePath("spells.txt");

    if (!loadTextTableRows(assetFileSystem, spellsPath, rows))
    {
        return false;
    }

    if (!m_spellTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse spell table: " << spellsPath << '\n';
        return false;
    }

    const std::string supplementalSpellsPath = dataTablePath("spells_supplemental.txt");

    if (assetFileSystem.exists(supplementalSpellsPath))
    {
        std::vector<std::vector<std::string>> supplementalRows;

        if (!loadTextTableRows(assetFileSystem, supplementalSpellsPath, supplementalRows))
        {
            return false;
        }

        rows.insert(rows.end(), supplementalRows.begin(), supplementalRows.end());

        if (!m_spellTable.loadFromRows(rows))
        {
            std::cerr << "Failed to parse spell table: " << supplementalSpellsPath << '\n';
            return false;
        }
    }

    return true;
}

bool GameDataLoader::loadItemTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> itemRows;

    const std::string itemsPath = dataTablePath("items.txt");

    if (!loadTextTableRows(assetFileSystem, itemsPath, itemRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> randomItemRows;

    const std::string randomItemsPath = dataTablePath("random_items.txt");

    if (!loadTextTableRows(assetFileSystem, randomItemsPath, randomItemRows))
    {
        return false;
    }

    if (!m_itemTable.load(assetFileSystem, itemRows, randomItemRows))
    {
        std::cerr << "Failed to parse item table: " << itemsPath << " / " << randomItemsPath << '\n';
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
            {dataTablePath("standard_item_enchants.txt")},
            standardRows))
    {
        std::cerr << "Failed to read standard item enchant table: STDITEMS.TXT\n";
        return false;
    }

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {dataTablePath("special_item_enchants.txt")},
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

    const std::string itemEquipPosPath = dataTablePath("item_equip_pos.txt");

    if (!loadTextTableRows(assetFileSystem, itemEquipPosPath, rows))
    {
        return false;
    }

    if (!m_itemEquipPosTable.load(rows))
    {
        std::cerr << "Failed to parse item equip position table: " << itemEquipPosPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadChestTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> chestRows;

    const std::string chestDataPath = dataTablePath("chest_data.txt");

    if (!loadTextTableRows(assetFileSystem, chestDataPath, chestRows))
    {
        return false;
    }

    if (!m_chestTable.loadRows(chestRows))
    {
        std::cerr << "Failed to parse chest table: " << chestDataPath << '\n';
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
    std::string resolvedSupportLuaPath;
    const std::optional<std::string> supportLuaSource = readFirstExistingText(
        assetFileSystem,
        buildLuaSupportPathCandidates(),
        resolvedSupportLuaPath);
    const std::vector<std::filesystem::path> localLuaSidecarCandidates =
        buildLuaScriptSidecarPathCandidates(
            localScriptBaseName,
            assetFileSystem.resolvePhysicalPath(m_selectedMap->geometryPath),
            m_selectedMap->scenePath ? assetFileSystem.resolvePhysicalPath(*m_selectedMap->scenePath) : std::nullopt);

    {
        std::string resolvedLuaPath;
        std::optional<std::string> luaSource =
            readFirstExistingPhysicalText(localLuaSidecarCandidates, resolvedLuaPath);

        if (!luaSource)
        {
            luaSource = readFirstExistingText(
                assetFileSystem,
                buildLuaScriptPathCandidates(localScriptBaseName, false),
                resolvedLuaPath
            );
        }

        if (luaSource)
        {
            std::string error;
            const std::string combinedLuaSource = prependLuaSupport(supportLuaSource, luaSource);
            std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
                combinedLuaSource,
                "@" + resolvedLuaPath,
                ScriptedEventScope::Map,
                error);

            if (!program)
            {
                std::cerr << "Failed to load local event Lua: " << resolvedLuaPath << ": " << error << '\n';
                return false;
            }

            m_selectedMap->localEventProgram = std::move(program);
        }
    }

    {
        std::string resolvedLuaPath;
        const std::optional<std::string> luaSource = readFirstExistingText(
            assetFileSystem,
            buildLuaScriptPathCandidates("Global", true),
            resolvedLuaPath
        );

        if (luaSource)
        {
            std::string error;
            const std::string combinedLuaSource = prependLuaSupport(supportLuaSource, luaSource);
            std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
                combinedLuaSource,
                "@" + resolvedLuaPath,
                ScriptedEventScope::Global,
                error);

            if (!program)
            {
                std::cerr << "Failed to load global event Lua: " << resolvedLuaPath << ": " << error << '\n';
                return false;
            }

            m_selectedMap->globalEventProgram = std::move(program);
        }
    }

    normalizeMapFaceHintOnlyAttributes(
        *m_selectedMap,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram);

    appendIndoorScriptTextures(
        assetFileSystem,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram,
        m_selectedMap->indoorTextureSet
    );
    appendDecorationScriptBillboardTextures(
        assetFileSystem,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram,
        m_selectedMap->indoorDecorationBillboardSet
    );
    appendDecorationScriptBillboardTextures(
        assetFileSystem,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram,
        m_selectedMap->outdoorDecorationBillboardSet
    );

    {
        EventRuntime eventRuntime = {};
        const std::optional<MapDeltaData> &mapDeltaData = m_selectedMap->outdoorMapDeltaData
            ? m_selectedMap->outdoorMapDeltaData
            : m_selectedMap->indoorMapDeltaData;
        EventRuntimeState runtimeState = {};
        eventRuntime.buildOnLoadState(
            m_selectedMap->localEventProgram,
            m_selectedMap->globalEventProgram,
            mapDeltaData,
            runtimeState
        );
        m_selectedMap->eventRuntimeState = std::move(runtimeState);
    }

    if constexpr (VerboseMapLoadLogging)
    {
        std::cout << "Selected map:\n";
        std::cout << "  id=" << m_selectedMap->map.id << '\n';
        std::cout << "  name=" << m_selectedMap->map.name << '\n';
        std::cout << "  file=" << m_selectedMap->geometryPath << '\n';
        std::cout << "  size=" << m_selectedMap->geometrySize << " bytes\n";
        std::cout << "  environment=" << m_selectedMap->map.environmentName << '\n';
        std::cout << "  top_level_area=" << (m_selectedMap->map.isTopLevelArea ? "yes" : "no") << '\n';

        if (m_selectedMap->companionPath && m_selectedMap->companionSize)
        {
            std::cout << "  legacy_companion=" << *m_selectedMap->companionPath
                      << " (" << *m_selectedMap->companionSize << " bytes)\n";
        }

        if (m_selectedMap->scenePath && m_selectedMap->sceneSize)
        {
            std::cout << "  scene=" << *m_selectedMap->scenePath
                      << " (" << *m_selectedMap->sceneSize << " bytes)\n";
        }

        if (m_selectedMap->authoredCompanionSource == AuthoredCompanionSource::SceneYml)
        {
            std::cout << "  authored_source=scene_yml\n";
        }
        else if (m_selectedMap->authoredCompanionSource == AuthoredCompanionSource::LegacyCompanion)
        {
            std::cout << "  authored_source=legacy_companion\n";
        }

        if (m_selectedMap->localEventProgram)
        {
            std::cout << "  local_lua_events=" << m_selectedMap->localEventProgram->eventIds().size() << '\n';

            if (m_selectedMap->localEventProgram->luaSourceName())
            {
                std::cout << "  local_lua_source=" << *m_selectedMap->localEventProgram->luaSourceName() << '\n';
            }
        }

        if (m_selectedMap->globalEventProgram)
        {
            std::cout << "  global_lua_events=" << m_selectedMap->globalEventProgram->eventIds().size() << '\n';

            if (m_selectedMap->globalEventProgram->luaSourceName())
            {
                std::cout << "  global_lua_source=" << *m_selectedMap->globalEventProgram->luaSourceName() << '\n';
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
            std::cout << "  height_range_world="
                      << (outdoorMapData.minHeightSample * OutdoorMapData::TerrainHeightScale)
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
    }

    return true;
}
}
