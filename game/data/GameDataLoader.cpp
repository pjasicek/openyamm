#include "game/data/GameDataLoader.h"

#include "game/arcomage/ArcomageLoader.h"
#include "engine/ImageAssetLoader.h"
#include "engine/TextTable.h"
#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/maps/MapIdentity.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr bool VerboseMapLoadLogging = false;

double millisecondsFromNanoseconds(uint64_t nanoseconds)
{
    return static_cast<double>(nanoseconds) / 1000000.0;
}

bool mapLoadTimingEnabled()
{
    const char *pValue = std::getenv("OPENYAMM_MAP_LOAD_TIMING");
    return pValue != nullptr && std::string_view(pValue) != "0" && std::string_view(pValue) != "false";
}

class GameDataLoadTimingLogger
{
public:
    GameDataLoadTimingLogger(const std::string &mapFileName, const std::string &scope)
        : m_enabled(mapLoadTimingEnabled())
        , m_mapFileName(mapFileName)
        , m_scope(scope)
        , m_startTime(std::chrono::steady_clock::now())
        , m_lastTime(m_startTime)
    {
        if (m_enabled)
        {
            std::cerr
                << "[MapLoadTiming] map=" << m_mapFileName
                << " begin=" << m_scope
                << '\n';
        }
    }

    void stage(const std::string &stageName)
    {
        if (!m_enabled)
        {
            return;
        }

        const std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
        const uint64_t stageNanoseconds =
            static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(now - m_lastTime).count());
        const uint64_t totalNanoseconds =
            static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(now - m_startTime).count());
        m_lastTime = now;

        std::cerr
            << "[MapLoadTiming] map=" << m_mapFileName
            << " scope=" << m_scope
            << " stage=\"" << stageName << "\""
            << " delta_ms=" << millisecondsFromNanoseconds(stageNanoseconds)
            << " total_ms=" << millisecondsFromNanoseconds(totalNanoseconds)
            << '\n';
    }

private:
    bool m_enabled = false;
    std::string m_mapFileName;
    std::string m_scope;
    std::chrono::steady_clock::time_point m_startTime;
    std::chrono::steady_clock::time_point m_lastTime;
};

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

std::optional<std::string> readExistingTexts(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath
)
{
    std::string combinedText;
    std::string combinedPath;

    for (const std::string &candidate : candidates)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(candidate);

        if (!text)
        {
            continue;
        }

        if (!combinedText.empty())
        {
            combinedText += "\n\n";
        }

        combinedText += *text;

        if (!combinedPath.empty())
        {
            combinedPath += "; ";
        }

        combinedPath += candidate;
    }

    if (combinedText.empty())
    {
        return std::nullopt;
    }

    resolvedPath = combinedPath;
    return combinedText;
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
            "events/Global.lua",
            "events/global.lua",
        };
    }

    const std::string lowerBaseName = toLowerCopy(baseName);
    return {
        "events/maps/" + lowerBaseName + ".lua",
        "events/maps/" + baseName + ".lua",
    };
}

bool isLuaMapOverlayFileName(const std::string &entryName, const std::string &baseName)
{
    const std::string lowerEntryName = toLowerCopy(entryName);
    const std::string lowerBaseName = toLowerCopy(baseName);

    if (!lowerEntryName.ends_with(".lua"))
    {
        return false;
    }

    return lowerEntryName.starts_with(lowerBaseName + "_")
        || lowerEntryName == lowerBaseName + ".fixup.lua";
}

std::vector<std::string> buildLuaScriptOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &baseName)
{
    std::vector<std::string> candidates;

    for (const std::string &entryName : assetFileSystem.enumerate("events/maps"))
    {
        if (isLuaMapOverlayFileName(entryName, baseName))
        {
            candidates.push_back("events/maps/" + entryName);
        }
    }

    return candidates;
}

std::vector<std::string> buildLuaGlobalScriptOverlayPathCandidates(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::string> candidates;

    for (const std::string &entryName : assetFileSystem.enumerate("events"))
    {
        if (isLuaMapOverlayFileName(entryName, "Global"))
        {
            candidates.push_back("events/" + entryName);
        }
    }

    return candidates;
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

std::string appendLuaScriptOverlays(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &baseName,
    const std::string &luaSource,
    std::string &resolvedPath)
{
    std::string combinedLuaSource = luaSource;

    for (const std::string &overlayPath : buildLuaScriptOverlayPathCandidates(assetFileSystem, baseName))
    {
        const std::optional<std::string> overlaySource = assetFileSystem.readTextFile(overlayPath);

        if (!overlaySource)
        {
            continue;
        }

        combinedLuaSource += "\n\n-- map overlay: " + overlayPath + "\n";
        combinedLuaSource += *overlaySource;
        resolvedPath += " + " + overlayPath;
    }

    return combinedLuaSource;
}

std::string appendLuaGlobalScriptOverlays(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &luaSource,
    std::string &resolvedPath)
{
    std::string combinedLuaSource = luaSource;

    for (const std::string &overlayPath : buildLuaGlobalScriptOverlayPathCandidates(assetFileSystem))
    {
        const std::optional<std::string> overlaySource = assetFileSystem.readTextFile(overlayPath);

        if (!overlaySource)
        {
            continue;
        }

        combinedLuaSource += "\n\n-- global overlay: " + overlayPath + "\n";
        combinedLuaSource += *overlaySource;
        resolvedPath += " + " + overlayPath;
    }

    return combinedLuaSource;
}


std::vector<std::string> buildLuaSupportPathCandidates()
{
    return {
        "scripts/common/event_support.lua",
        "scripts/common/EventSupport.lua",
    };
}

std::vector<std::string> buildLuaWorldCommonPathCandidates(const std::string &worldId)
{
    std::vector<std::string> candidates = {
        "events/common/world_common.lua",
        "events/common/cross_continents_common.lua",
        "events/common/common.lua",
    };

    if (!worldId.empty())
    {
        const std::string normalizedWorldId = normalizeWorldId(worldId);
        candidates.push_back("events/common/" + normalizedWorldId + "_common.lua");
    }

    return candidates;
}

std::string prependLuaSupport(
    const std::optional<std::string> &supportSource,
    const std::optional<std::string> &worldCommonSource,
    const std::optional<std::string> &scriptSource)
{
    if (!scriptSource)
    {
        return {};
    }

    std::string combinedSource;

    if (supportSource && !supportSource->empty())
    {
        combinedSource += *supportSource;
        combinedSource += "\n\n";
    }

    if (worldCommonSource && !worldCommonSource->empty())
    {
        combinedSource += *worldCommonSource;
        combinedSource += "\n\n";
    }

    combinedSource += *scriptSource;
    return combinedSource;
}

std::string dataTablePath(std::string_view fileName)
{
    return "engine/data_tables/" + std::string(fileName);
}

std::string trimCopy(std::string_view value)
{
    size_t first = 0;

    while (first < value.size() && std::isspace(static_cast<unsigned char>(value[first])) != 0)
    {
        ++first;
    }

    size_t last = value.size();

    while (last > first && std::isspace(static_cast<unsigned char>(value[last - 1])) != 0)
    {
        --last;
    }

    return std::string(value.substr(first, last - first));
}

std::string normalizedTableTextureName(const std::string &value)
{
    return toLowerCopy(trimCopy(value));
}

std::optional<std::string> skyTextureAssetStem(const std::string &entryName)
{
    const std::string normalizedEntryName = toLowerCopy(entryName);

    if (normalizedEntryName.ends_with(".png") || normalizedEntryName.ends_with(".bmp"))
    {
        return normalizedEntryName.substr(0, normalizedEntryName.size() - 4);
    }

    return std::nullopt;
}

std::unordered_set<std::string> buildSkyTextureAssetNameSet(const Engine::AssetFileSystem &assetFileSystem)
{
    std::unordered_set<std::string> textureNames;

    for (const std::string &entryName : assetFileSystem.enumerate("sky_textures"))
    {
        const std::optional<std::string> textureName = skyTextureAssetStem(entryName);

        if (textureName)
        {
            textureNames.insert(*textureName);
        }
    }

    return textureNames;
}

bool skyTextureAssetExists(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_set<std::string> *pSkyTextureAssetNames,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return false;
    }

    if (pSkyTextureAssetNames != nullptr)
    {
        return pSkyTextureAssetNames->find(toLowerCopy(textureName)) != pSkyTextureAssetNames->end();
    }

    const std::string basePath = "sky_textures/" + textureName;
    return assetFileSystem.exists(basePath + ".png") || assetFileSystem.exists(basePath + ".bmp");
}

void appendCandidateIfMissing(std::vector<std::string> &candidates, const std::string &candidate)
{
    if (!candidate.empty() && std::find(candidates.begin(), candidates.end(), candidate) == candidates.end())
    {
        candidates.push_back(candidate);
    }
}

std::string stripMergedWorldSkyPrefix(const std::string &textureName)
{
    if (textureName.size() > 1 && (textureName.front() == '6' || textureName.front() == '7'))
    {
        const std::string withoutPrefix = textureName.substr(1);

        if (withoutPrefix.starts_with("sky") || withoutPrefix.starts_with("plansky"))
        {
            return withoutPrefix;
        }
    }

    return {};
}

std::vector<std::string> buildMergedSkyTextureCandidates(
    const std::string &activeWorldId,
    const std::string &textureName)
{
    std::vector<std::string> candidates;
    const std::string normalizedTextureName = normalizedTableTextureName(textureName);

    appendCandidateIfMissing(candidates, normalizedTextureName);

    const std::string unprefixedTextureName = stripMergedWorldSkyPrefix(normalizedTextureName);
    appendCandidateIfMissing(candidates, unprefixedTextureName);

    if (activeWorldId == "mm6")
    {
        if (unprefixedTextureName.empty()
            && (normalizedTextureName.starts_with("sky") || normalizedTextureName.starts_with("plansky")))
        {
            appendCandidateIfMissing(candidates, "6" + normalizedTextureName);
        }
        else if (!unprefixedTextureName.empty())
        {
            appendCandidateIfMissing(candidates, "6" + unprefixedTextureName);
        }

        if (normalizedTextureName == "plansky3")
        {
            appendCandidateIfMissing(candidates, "6plansky1");
        }
        else if (unprefixedTextureName == "plansky3")
        {
            appendCandidateIfMissing(candidates, "6plansky1");
        }
        else if (normalizedTextureName == "plansky1")
        {
            appendCandidateIfMissing(candidates, "6plansky1");
        }
        else if (normalizedTextureName == "cloudsabove")
        {
            appendCandidateIfMissing(candidates, "6sky12");
        }
        else if (normalizedTextureName == "stormclds")
        {
            appendCandidateIfMissing(candidates, "6sky19");
        }
        else if (normalizedTextureName == "sunsetclouds")
        {
            appendCandidateIfMissing(candidates, "6sky02");
        }
    }
    else if (activeWorldId == "mm7")
    {
        if (normalizedTextureName.starts_with("plansky"))
        {
            appendCandidateIfMissing(candidates, "7" + normalizedTextureName);
        }
        else if (normalizedTextureName.starts_with("sky"))
        {
            appendCandidateIfMissing(candidates, "7" + normalizedTextureName);
        }
        else if (!unprefixedTextureName.empty())
        {
            appendCandidateIfMissing(candidates, "7" + unprefixedTextureName);
        }

        if (normalizedTextureName == "cloudsabove")
        {
            appendCandidateIfMissing(candidates, "sky12");
        }
        else if (normalizedTextureName == "stormclds")
        {
            appendCandidateIfMissing(candidates, "sky19");
        }
        else if (normalizedTextureName == "sunsetclouds")
        {
            appendCandidateIfMissing(candidates, "7sky02");
        }
    }
    else if (activeWorldId == "mm8")
    {
        if (normalizedTextureName == "7plansky3")
        {
            appendCandidateIfMissing(candidates, "plansky3");
        }
        else if (normalizedTextureName == "7sky01")
        {
            appendCandidateIfMissing(candidates, "sky01");
        }
        else if (normalizedTextureName == "6sky02")
        {
            appendCandidateIfMissing(candidates, "sky02");
        }
        else if (normalizedTextureName == "6sky12")
        {
            appendCandidateIfMissing(candidates, "cloudsabove");
        }
        else if (normalizedTextureName == "6sky19")
        {
            appendCandidateIfMissing(candidates, "stormclds");
        }
    }

    return candidates;
}

std::string resolveMergedSkyTextureName(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_set<std::string> *pSkyTextureAssetNames,
    const std::string &activeWorldId,
    const std::string &textureName)
{
    for (const std::string &candidate : buildMergedSkyTextureCandidates(activeWorldId, textureName))
    {
        if (skyTextureAssetExists(assetFileSystem, pSkyTextureAssetNames, candidate))
        {
            return candidate;
        }
    }

    return {};
}

std::string engineDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/" + std::string(fileName);
}

std::string engineEnglishDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/english/" + std::string(fileName);
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
    return Engine::findImageAssetPath(
        assetFileSystem,
        directoryPath,
        textureName,
        directoryAssetPathsByPath,
        bitmapPathByKey);
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &directoryAssetPathsByPath,
    std::unordered_map<std::string, std::optional<std::string>> &bitmapPathByKey,
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> &pixelsByKey
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(textureName);
    const auto cachedPixelsIt = pixelsByKey.find(cacheKey);

    if (cachedPixelsIt != pixelsByKey.end())
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
        findBitmapPath(
            assetFileSystem,
            directoryPath,
            textureName,
            directoryAssetPathsByPath,
            bitmapPathByKey);

    if (!bitmapPath)
    {
        pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath);

    if (!image)
    {
        pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    pixelsByKey[cacheKey] = MapAssetBitmapPixelsResult{width, height, image->pixels};
    return image->pixels;
}

void appendDecorationScriptBillboardTextures(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    std::optional<DecorationBillboardSet> &billboardSet,
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &directoryAssetPathsByPath,
    std::unordered_map<std::string, std::optional<std::string>> &bitmapPathByKey,
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> &pixelsByKey
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

    const Engine::AssetScaleTier decorationAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Decorations);

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
                    bitmapPathByKey,
                    pixelsByKey);

            if (!pixels || textureWidth <= 0 || textureHeight <= 0)
            {
                continue;
            }

            OutdoorBitmapTexture texture = {};
            texture.textureName = toLowerCopy(textureName);
            texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, decorationAssetScaleTier);
            texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, decorationAssetScaleTier);
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
    std::optional<IndoorTextureSet> &indoorTextureSet,
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &directoryAssetPathsByPath,
    std::unordered_map<std::string, std::optional<std::string>> &bitmapPathByKey,
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> &pixelsByKey
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

    const Engine::AssetScaleTier textureAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Textures);

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
                bitmapPathByKey,
                pixelsByKey);

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, textureAssetScaleTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, textureAssetScaleTier);
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
    return loadInternal(assetFileSystem, MapLoadPurpose::Full, true);
}

void GameDataLoader::setActiveWorldId(const std::string &worldId)
{
    const std::string normalizedWorldId = normalizeWorldId(worldId);

    if (m_activeWorldId != normalizedWorldId)
    {
        m_mapAssetLoadSharedCache = {};
        m_skyTextureAssetNames.reset();
        m_resolvedMergedSkyTextureNameByKey.clear();
        m_scriptBitmapDirectoryAssetPathsByPath.clear();
        m_scriptBitmapPathByKey.clear();
        m_scriptBitmapPixelsByKey.clear();
    }

    m_activeWorldId = normalizedWorldId;
}

void GameDataLoader::setInitialMapFileName(const std::string &fileName)
{
    m_initialMapFileName = fileName;
}

bool GameDataLoader::loadForGameplay(const Engine::AssetFileSystem &assetFileSystem)
{
    return loadInternal(assetFileSystem, MapLoadPurpose::FullGameplay, true);
}

bool GameDataLoader::loadCommonForGameplay(const Engine::AssetFileSystem &assetFileSystem)
{
    return loadInternal(assetFileSystem, MapLoadPurpose::FullGameplay, false);
}

bool GameDataLoader::loadForHeadlessGameplay(const Engine::AssetFileSystem &assetFileSystem)
{
    return loadInternal(assetFileSystem, MapLoadPurpose::HeadlessGameplay, true);
}

bool GameDataLoader::loadInternal(
    const Engine::AssetFileSystem &assetFileSystem,
    MapLoadPurpose mapLoadPurpose,
    bool loadInitialMap)
{
    m_activeWorldId = normalizeWorldId(assetFileSystem.getActiveWorldId());
    m_loadedTables.clear();
    m_selectedMap.reset();
    m_mapAssetLoadSharedCache = {};
    m_skyTextureAssetNames.reset();
    m_resolvedMergedSkyTextureNameByKey.clear();
    m_scriptBitmapDirectoryAssetPathsByPath.clear();
    m_scriptBitmapPathByKey.clear();
    m_scriptBitmapPixelsByKey.clear();

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

    if (!loadPotionNoteTable(assetFileSystem))
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

    if (!loadMergedBaseTables(assetFileSystem))
    {
        return false;
    }

    if (!applyMergedRuntimeTables())
    {
        return false;
    }

    if (!loadArcomageLibrary(assetFileSystem))
    {
        return false;
    }

    if (loadInitialMap && !this->loadInitialMap(assetFileSystem, mapLoadPurpose))
    {
        return false;
    }

    const std::vector<std::string> tablePaths = {
        engineDataTablePath("spells.txt"),
        engineDataTablePath("random_items.txt"),
        engineEnglishDataTablePath("scroll.txt")
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
    const std::string &fileName,
    const MapLoadProgressPump &progressPump)
{
    const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findByFileName(fileName);

    if (!selectedMap)
    {
        return false;
    }

    return loadSelectedMap(assetFileSystem, selectedMap->id, MapLoadPurpose::FullGameplay, progressPump);
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

const PotionNoteTable &GameDataLoader::getPotionNoteTable() const
{
    return m_potionNoteTable;
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

const MergedClassExtraTable &GameDataLoader::getMergedClassExtraTable() const
{
    return m_mergedClassExtraTable;
}

const MergedCharacterSelectionTable &GameDataLoader::getMergedCharacterSelectionTable() const
{
    return m_mergedCharacterSelectionTable;
}

const MergedRaceSkillTable &GameDataLoader::getMergedRaceSkillTable() const
{
    return m_mergedRaceSkillTable;
}

const MergedTeacherTopicTable &GameDataLoader::getMergedTeacherTopicTable() const
{
    return m_mergedTeacherTopicTable;
}

const MergedTeacherAutonoteTable &GameDataLoader::getMergedTeacherAutonoteTable() const
{
    return m_mergedTeacherAutonoteTable;
}

const MergedNpcProfessionTable &GameDataLoader::getMergedNpcProfessionTable() const
{
    return m_mergedNpcProfessionTable;
}

const MergedNpcNameTable &GameDataLoader::getMergedNpcNameTable() const
{
    return m_mergedNpcNameTable;
}

const MergedNpcBtbTable &GameDataLoader::getMergedNpcBtbTable() const
{
    return m_mergedNpcBtbTable;
}

const MergedNewsTopicTable &GameDataLoader::getMergedNewsAreaTopicTable() const
{
    return m_mergedNewsAreaTopicTable;
}

const MergedNewsTopicTable &GameDataLoader::getMergedNewsContinentTopicTable() const
{
    return m_mergedNewsContinentTopicTable;
}

const MergedNewsProfessionTopicTable &GameDataLoader::getMergedNewsProfessionTopicTable() const
{
    return m_mergedNewsProfessionTopicTable;
}

const MergedMonsterPortraitTable &GameDataLoader::getMergedMonsterPortraitTable() const
{
    return m_mergedMonsterPortraitTable;
}

const MergedPotionSettingTable &GameDataLoader::getMergedPotionSettingTable() const
{
    return m_mergedPotionSettingTable;
}

const MergedReagentSettingTable &GameDataLoader::getMergedReagentSettingTable() const
{
    return m_mergedReagentSettingTable;
}

const MergedAdditionalUiTable &GameDataLoader::getMergedAdditionalUiTable() const
{
    return m_mergedAdditionalUiTable;
}

const MergedBolsterFormulaTable &GameDataLoader::getMergedBolsterFormulaTable() const
{
    return m_mergedBolsterFormulaTable;
}

const MergedBolsterMapTable &GameDataLoader::getMergedBolsterMapTable() const
{
    return m_mergedBolsterMapTable;
}

const MergedBolsterMonsterTable &GameDataLoader::getMergedBolsterMonsterTable() const
{
    return m_mergedBolsterMonsterTable;
}

const MergedCharacterVoiceTable &GameDataLoader::getMergedCharacterVoiceTable() const
{
    return m_mergedCharacterVoiceTable;
}

const MergedClassStartingStatTable &GameDataLoader::getMergedClassStartingStatsSourceTable() const
{
    return m_mergedClassStartingStatsSourceTable;
}

const MergedComplexItemPictureOffsetTable &GameDataLoader::getMergedComplexItemPictureOffsetTable() const
{
    return m_mergedComplexItemPictureOffsetTable;
}

const MergedComplexItemPictureTable &GameDataLoader::getMergedComplexItemPictureTable() const
{
    return m_mergedComplexItemPictureTable;
}

const MergedContinentSettingTable &GameDataLoader::getMergedContinentSettingTable() const
{
    return m_mergedContinentSettingTable;
}

const MergedContinentSettingEntry *GameDataLoader::findMergedContinentSettingsForMap(
    const MapStatsEntry &map) const
{
    const MergedBolsterMapEntry *pBolsterMap = m_mergedBolsterMapTable.findById(static_cast<uint32_t>(map.id));

    if (pBolsterMap == nullptr || pBolsterMap->continent == 0)
    {
        return nullptr;
    }

    return m_mergedContinentSettingTable.findById(pBolsterMap->continent);
}

const MergedHardwareWaterTextureTable &GameDataLoader::getMergedHardwareWaterTextureTable() const
{
    return m_mergedHardwareWaterTextureTable;
}

const MergedHouseExitTable &GameDataLoader::getMergedHouseExitTable() const
{
    return m_mergedHouseExitTable;
}

const MergedHouseRuleTable &GameDataLoader::getMergedHouseRuleTable() const
{
    return m_mergedHouseRuleTable;
}

const MergedHistoryTable &GameDataLoader::getMergedMm7HistoryTable() const
{
    return m_mergedMm7HistoryTable;
}

const MergedOutdoorTravelTable &GameDataLoader::getMergedOutdoorTravelTable() const
{
    return m_mergedOutdoorTravelTable;
}

const MergedOverlayTable &GameDataLoader::getMergedOverlayTable() const
{
    return m_mergedOverlayTable;
}

const MergedTownPortalSwitchTable &GameDataLoader::getMergedTownPortalSwitchTable() const
{
    return m_mergedTownPortalSwitchTable;
}

const MergedTransportIndexTable &GameDataLoader::getMergedTransportIndexTable() const
{
    return m_mergedTransportIndexTable;
}

const MergedTransportLocationTable &GameDataLoader::getMergedTransportLocationTable() const
{
    return m_mergedTransportLocationTable;
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

    if (!m_mapStats.loadFromRows(rows, DefaultWorldId))
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

    const std::string monsterDataPath = engineDataTablePath("monster_data.txt");

    if (!loadTextTableRows(assetFileSystem, monsterDataPath, monsterDataRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> monsterDescriptorRows;

    const std::string monsterDescriptorPath = engineDataTablePath("monster_descriptors.txt");

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

    std::vector<std::vector<std::string>> monsterDeathDropRows;

    const std::string monsterDeathDropPath = dataTablePath("monster_death_drops.txt");

    if (!loadTextTableRows(assetFileSystem, monsterDeathDropPath, monsterDeathDropRows))
    {
        return false;
    }

    if (!m_monsterTable.loadDeathDropsFromRows(monsterDeathDropRows))
    {
        std::cerr << "Failed to parse monster death drops: " << monsterDeathDropPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> placedMonsterRows;

    const std::string placeMonPath = engineEnglishDataTablePath("place_mon.txt");

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

    const std::string monsterRelationPath = engineDataTablePath("hostile.txt");

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
        std::vector<std::vector<std::string>> movieRows;

        if (loadTextTableRows(assetFileSystem, dataTablePath("house_movies.txt"), movieRows))
        {
            m_houseTable.loadAnimationRows(animationRows, movieRows);
        }
        else
        {
            m_houseTable.loadAnimationRows(animationRows);
        }
    }

    return true;
}

bool GameDataLoader::loadNpcDialogTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> greetingRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineDataTablePath("npc_greet.txt")},
            greetingRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> textRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineDataTablePath("npc_topic_text.txt")},
            textRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> topicRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineDataTablePath("npc_topic.txt")},
            topicRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> npcRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineDataTablePath("npc.txt")},
            npcRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> newsRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineDataTablePath("npc_news.txt")},
            newsRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> groupRows;

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineEnglishDataTablePath("npc_group.txt")},
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

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("quests.txt")}, questRows))
    {
        std::cerr << "Failed to read journal quest table\n";
        return false;
    }

    std::vector<std::vector<std::string>> historyRows;

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("history.txt")}, historyRows))
    {
        std::cerr << "Failed to read journal history table\n";
        return false;
    }

    std::vector<std::vector<std::string>> autonoteRows;

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("autonote.txt")}, autonoteRows))
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

    std::vector<std::vector<std::string>> mm7HistoryRows;

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("mm7_history.txt")}, mm7HistoryRows))
    {
        std::cerr << "Failed to read MM7 journal history table\n";
        return false;
    }

    if (!m_journalHistoryTable.loadFromRowsForContinent(2u, mm7HistoryRows))
    {
        std::cerr << "Failed to parse MM7 journal history table\n";
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

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_skills.txt"), capRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> startingRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_starting_skills.txt"), startingRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> classExtraRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_extra.txt"), classExtraRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> classMultiplierRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_multipliers.txt"), classMultiplierRows))
    {
        return false;
    }

    if (!m_classSkillTable.loadCapsFromRows(capRows)
        || !m_classSkillTable.loadStartingSkillsFromRows(startingRows)
        || !m_classSkillTable.loadClassMetadataFromRows(classExtraRows)
        || !m_classSkillTable.loadClassSpellPointMetadataFromRows(classMultiplierRows))
    {
        std::cerr << "Failed to parse class skill tables\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadClassMultiplierTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_multipliers.txt"), rows))
    {
        return false;
    }

    if (!m_classMultiplierTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse class multiplier table\n";
        return false;
    }

    std::vector<std::vector<std::string>> classExtraRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_extra.txt"), classExtraRows))
    {
        return false;
    }

    if (!m_classMultiplierTable.applyClassExtraRows(classExtraRows))
    {
        std::cerr << "Failed to apply class metadata table\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadRosterTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    const std::string rosterPath = engineDataTablePath("roster.txt");

    if (!loadTextTableRows(assetFileSystem, rosterPath, rows))
    {
        return false;
    }

    if (!m_rosterTable.loadFromRows(rows, &m_classSkillTable))
    {
        std::cerr << "Failed to parse roster table: " << rosterPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadCharacterDollTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> characterRows;

    const std::string characterDataPath = engineDataTablePath("character_data.txt");

    if (!loadTextTableRows(assetFileSystem, characterDataPath, characterRows))
    {
        std::cerr << "Failed to read character doll table: " << characterDataPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> dollTypeRows;

    const std::string dollTypesPath = engineDataTablePath("doll_types.txt");

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

    const std::string statsPath = engineEnglishDataTablePath("stats.txt");

    if (!loadTextTableRows(assetFileSystem, statsPath, statRows))
    {
        std::cerr << "Failed to read character inspect table: " << statsPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> skillRows;

    const std::string skillDesPath = engineEnglishDataTablePath("skill_des.txt");

    if (!loadTextTableRows(assetFileSystem, skillDesPath, skillRows))
    {
        std::cerr << "Failed to read character inspect table: " << skillDesPath << '\n';
        return false;
    }

    std::vector<std::vector<std::string>> classRows;

    const std::string classPath = engineEnglishDataTablePath("class.txt");

    if (!loadTextTableRows(assetFileSystem, classPath, classRows))
    {
        std::cerr << "Failed to read character inspect table: " << classPath << '\n';
        return false;
    }

    if (!m_characterInspectTable.loadStatRows(statRows)
        || !m_characterInspectTable.loadSkillRows(skillRows)
        || !m_characterInspectTable.loadClassRows(classRows))
    {
        std::cerr << "Failed to parse character inspect tables\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadRaceStartingStatsTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;
    const std::string tablePath = engineDataTablePath("class_starting_stats.txt");

    if (!loadTextTableRows(assetFileSystem, tablePath, rows))
    {
        std::cerr << "Failed to read class starting stats table: " << tablePath << '\n';
        return false;
    }

    if (!m_raceStartingStatsTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse class starting stats table: " << tablePath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadReadableScrollTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("scroll.txt")}, rows))
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

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("potion.txt")}, rows))
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

bool GameDataLoader::loadPotionNoteTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("potnotes.txt")}, rows))
    {
        return false;
    }

    if (!m_potionNoteTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse potion note table\n";
        return false;
    }

    return true;
}

bool GameDataLoader::loadTransitionTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadFirstTextTableRows(assetFileSystem, {engineEnglishDataTablePath("trans.txt")}, rows))
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

bool GameDataLoader::loadMergedBaseTables(const Engine::AssetFileSystem &assetFileSystem)
{
    const auto loadBaseTable =
        [this, &assetFileSystem](const char *pFileName, auto &table, const char *pDisplayName) -> bool
        {
            const std::string tablePath = engineDataTablePath(pFileName);
            std::vector<std::vector<std::string>> rows;

            if (!loadTextTableRows(assetFileSystem, tablePath, rows))
            {
                std::cerr << "Failed to read merged base table: " << tablePath << '\n';
                return false;
            }

            if (!table.loadFromRows(rows))
            {
                std::cerr << "Failed to parse merged base table: " << pDisplayName << '\n';
                return false;
            }

            return true;
        };

    const auto loadBaseYamlTable =
        [&assetFileSystem](const char *pFileName, auto &table, const char *pDisplayName) -> bool
        {
            const std::string tablePath = engineDataTablePath(pFileName);
            const std::optional<std::string> fileContents = assetFileSystem.readTextFile(tablePath);

            if (!fileContents)
            {
                std::cerr << "Failed to read merged base table: " << tablePath << '\n';
                return false;
            }

            std::string errorMessage;

            if (!table.loadFromYaml(*fileContents, errorMessage))
            {
                std::cerr << "Failed to parse merged base table: " << pDisplayName << ": " << errorMessage << '\n';
                return false;
            }

            return true;
        };

    return loadBaseTable(
        "class_extra.txt",
        m_mergedClassExtraTable,
        "Class Extra.txt")
        && loadBaseYamlTable(
            "character_selection.yml",
            m_mergedCharacterSelectionTable,
            "character_selection.yml")
        && loadBaseYamlTable(
            "race_skills.yml",
            m_mergedRaceSkillTable,
            "race_skills.yml")
        && loadBaseTable(
            "teacher_topics.txt",
            m_mergedTeacherTopicTable,
            "Teacher topics.txt")
        && loadBaseTable(
            "teacher_autonotes.txt",
            m_mergedTeacherAutonoteTable,
            "Teacher autonotes.txt")
        && loadBaseTable(
            "npc_professions.txt",
            m_mergedNpcProfessionTable,
            "NPC professions.txt")
        && loadBaseTable(
            "npc_names.txt",
            m_mergedNpcNameTable,
            "NPC names.txt")
        && loadBaseTable(
            "npc_btb.txt",
            m_mergedNpcBtbTable,
            "NPC BTB.txt")
        && loadBaseTable(
            "news_topics_area.txt",
            m_mergedNewsAreaTopicTable,
            "News topics - area.txt")
        && loadBaseTable(
            "news_topics_continent.txt",
            m_mergedNewsContinentTopicTable,
            "News topics - continent.txt")
        && loadBaseTable(
            "news_topics_profession.txt",
            m_mergedNewsProfessionTopicTable,
            "News topics - profession.txt")
        && loadBaseTable(
            "monster_portraits.txt",
            m_mergedMonsterPortraitTable,
            "MonPortraits.txt")
        && loadBaseTable(
            "potion_settings.txt",
            m_mergedPotionSettingTable,
            "Potion settings.txt")
        && loadBaseTable(
            "reagent_settings.txt",
            m_mergedReagentSettingTable,
            "Reagent settings.txt")
        && loadBaseTable(
            "additional_ui.txt",
            m_mergedAdditionalUiTable,
            "Additional UI.txt")
        && loadBaseTable(
            "bolster_formulas.txt",
            m_mergedBolsterFormulaTable,
            "Bolster - formulas.txt")
        && loadBaseTable(
            "bolster_maps.txt",
            m_mergedBolsterMapTable,
            "Bolster - maps.txt")
        && loadBaseTable(
            "bolster_monsters.txt",
            m_mergedBolsterMonsterTable,
            "Bolster - monsters.txt")
        && loadBaseTable(
            "character_voices.txt",
            m_mergedCharacterVoiceTable,
            "Character voices.txt")
        && loadBaseTable(
            "class_starting_stats.txt",
            m_mergedClassStartingStatsSourceTable,
            "Class Starting Stats.txt")
        && loadBaseTable(
            "complex_item_picture_offsets.txt",
            m_mergedComplexItemPictureOffsetTable,
            "Complex item pictures offsets.txt")
        && loadBaseTable(
            "complex_item_pictures.txt",
            m_mergedComplexItemPictureTable,
            "Complex item pictures.txt")
        && loadBaseTable(
            "continent_settings.txt",
            m_mergedContinentSettingTable,
            "Continent settings.txt")
        && loadBaseTable(
            "hw_water_textures.txt",
            m_mergedHardwareWaterTextureTable,
            "HW water textures.txt")
        && loadBaseTable(
            "house_exits.txt",
            m_mergedHouseExitTable,
            "House exits.txt")
        && loadBaseTable(
            "house_rules.txt",
            m_mergedHouseRuleTable,
            "House rules.txt")
        && loadBaseTable(
            "english/mm7_history.txt",
            m_mergedMm7HistoryTable,
            "MM7history.txt")
        && loadBaseTable(
            "outdoor_travels.txt",
            m_mergedOutdoorTravelTable,
            "Outdoor travels.txt")
        && loadBaseTable(
            "overlay.txt",
            m_mergedOverlayTable,
            "Overlay.txt")
        && loadBaseTable(
            "town_portal_switch.txt",
            m_mergedTownPortalSwitchTable,
            "TownPortalSwitch.txt")
        && loadBaseTable(
            "transport_index.txt",
            m_mergedTransportIndexTable,
            "Transport Index.txt")
        && loadBaseTable(
            "transport_locations.txt",
            m_mergedTransportLocationTable,
            "Transport Locations.txt");
}

bool GameDataLoader::applyMergedRuntimeTables()
{
    if (!m_classSkillTable.applyRaceSkillOverrides(m_mergedRaceSkillTable))
    {
        std::cerr << "Failed to apply merged race skill rules.\n";
        return false;
    }

    if (!m_mapStats.applyMergedBolsterMaps(m_mergedBolsterMapTable))
    {
        std::cerr << "Failed to apply merged bolster maps.\n";
        return false;
    }

    if (!m_monsterTable.applyKindFlagsFromBolsterMonsterTable(m_mergedBolsterMonsterTable))
    {
        std::cerr << "Failed to apply merged bolster monster kind flags.\n";
        return false;
    }

    if (!m_houseTable.applyHouseRules(
            m_mergedHouseRuleTable,
            m_mergedTransportLocationTable,
            m_mapStats))
    {
        std::cerr << "Failed to apply merged house rules.\n";
        return false;
    }

    if (!m_houseTable.applyHouseExits(m_mergedHouseExitTable, m_mapStats))
    {
        std::cerr << "Failed to apply merged house exits.\n";
        return false;
    }

    if (!m_mapStats.applyMergedOutdoorTravels(m_mergedOutdoorTravelTable))
    {
        std::cerr << "Failed to apply merged outdoor travels.\n";
        return false;
    }

    m_mapRegistry.initialize(m_mapStats.getEntries());
    return true;
}

bool GameDataLoader::loadArcomageLibrary(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> cardRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("arcomage_cards.txt"), cardRows))
    {
        std::cerr << "Failed to read Arcomage card table\n";
        return false;
    }

    ArcomageLoader loader;

    if (!loader.loadFromHouseRules(m_mergedHouseRuleTable, m_houseTable, cardRows))
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
    const std::string tablePath = engineDataTablePath("portrait_frame_data.txt");

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
    const std::string tablePath = engineDataTablePath("icon_frame_data.txt");

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
    const std::string tablePath = engineDataTablePath("spell_fx.txt");

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
    const std::string tablePath = engineDataTablePath("portrait_fx_events.txt");

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
    const std::string tablePath = engineDataTablePath("face_animations.txt");

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
    const std::string objectListPath = engineDataTablePath("object_list.txt");

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

    const std::string spellsPath = engineDataTablePath("spells.txt");

    if (!loadTextTableRows(assetFileSystem, spellsPath, rows))
    {
        return false;
    }

    if (!m_spellTable.loadFromRows(rows))
    {
        std::cerr << "Failed to parse spell table: " << spellsPath << '\n';
        return false;
    }

    return true;
}

bool GameDataLoader::loadItemTable(const Engine::AssetFileSystem &assetFileSystem)
{
    std::vector<std::vector<std::string>> itemRows;

    const std::string itemsPath = engineDataTablePath("items.txt");

    if (!loadTextTableRows(assetFileSystem, itemsPath, itemRows))
    {
        return false;
    }

    std::vector<std::vector<std::string>> randomItemRows;

    const std::string randomItemsPath = engineDataTablePath("random_items.txt");

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
            {engineDataTablePath("standard_item_enchants.txt")},
            standardRows))
    {
        std::cerr << "Failed to read standard item enchant table: STDITEMS.TXT\n";
        return false;
    }

    if (!loadFirstTextTableRows(
            assetFileSystem,
            {engineDataTablePath("special_item_enchants.txt")},
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
    if (!m_initialMapFileName.empty())
    {
        const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findByFileName(m_initialMapFileName);

        if (!selectedMap)
        {
            std::cerr << "Failed to select initial map from map registry: file=" << m_initialMapFileName << '\n';
            return false;
        }

        return loadSelectedMap(assetFileSystem, selectedMap->id, mapLoadPurpose);
    }

    const std::string activeWorldCanonicalPrefix = "world." + m_activeWorldId + ".map.";

    for (const MapStatsEntry &entry : m_mapRegistry.getEntries())
    {
        if (toLowerCopy(entry.canonicalId).starts_with(activeWorldCanonicalPrefix))
        {
            return loadSelectedMap(assetFileSystem, entry.id, mapLoadPurpose);
        }
    }

    const std::optional<MapStatsEntry> defaultMap = m_mapRegistry.findById(1);

    if (defaultMap)
    {
        return loadSelectedMap(assetFileSystem, defaultMap->id, mapLoadPurpose);
    }

    const std::vector<MapStatsEntry> &entries = m_mapRegistry.getEntries();

    if (entries.empty())
    {
        std::cerr << "Failed to select initial map from empty map registry\n";
        return false;
    }

    return loadSelectedMap(assetFileSystem, entries.front().id, mapLoadPurpose);
}

bool GameDataLoader::loadSelectedMap(
    const Engine::AssetFileSystem &assetFileSystem,
    int mapId,
    MapLoadPurpose mapLoadPurpose,
    const MapLoadProgressPump &progressPump
)
{
    const std::optional<MapStatsEntry> selectedMap = m_mapRegistry.findById(mapId);

    if (!selectedMap)
    {
        std::cerr << "Failed to select map from map registry: id=" << mapId << '\n';
        return false;
    }

    GameDataLoadTimingLogger timingLogger(selectedMap->fileName, "game_data_loader");
    const MapAssetLoader mapAssetLoader;
    std::optional<MapAssetInfo> loadedMap = mapAssetLoader.load(
        assetFileSystem,
        *selectedMap,
        m_monsterTable,
        m_objectTable,
        mapLoadPurpose,
        {},
        progressPump,
        &m_mapAssetLoadSharedCache);

    if (!loadedMap)
    {
        m_selectedMap.reset();
        std::cerr << "Failed to load initial map asset for " << selectedMap->fileName << '\n';
        return false;
    }
    timingLogger.stage("map assets loaded");

    m_selectedMap.emplace(std::move(*loadedMap));

    applyMergedContinentSettingsToSelectedMap(assetFileSystem);
    timingLogger.stage("continent settings applied");

    const std::string localScriptBaseName = mapScriptBaseName(selectedMap->fileName);
    std::string resolvedSupportLuaPath;
    const std::optional<std::string> supportLuaSource = readFirstExistingText(
        assetFileSystem,
        buildLuaSupportPathCandidates(),
        resolvedSupportLuaPath);
    std::string resolvedWorldCommonLuaPath;
    const std::optional<std::string> worldCommonLuaSource = readExistingTexts(
        assetFileSystem,
        buildLuaWorldCommonPathCandidates(selectedMap->worldId),
        resolvedWorldCommonLuaPath);
    const std::vector<std::filesystem::path> localLuaSidecarCandidates =
        buildLuaScriptSidecarPathCandidates(
            localScriptBaseName,
            assetFileSystem.resolvePhysicalPath(m_selectedMap->geometryPath),
            m_selectedMap->scenePath ? assetFileSystem.resolvePhysicalPath(*m_selectedMap->scenePath) : std::nullopt);
    timingLogger.stage("lua support sources resolved");

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
            const std::string mapLuaSource = appendLuaScriptOverlays(
                assetFileSystem,
                localScriptBaseName,
                *luaSource,
                resolvedLuaPath);
            const std::string combinedLuaSource =
                prependLuaSupport(supportLuaSource, worldCommonLuaSource, mapLuaSource);
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
    timingLogger.stage("local lua loaded");

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
            const std::string globalLuaSource =
                appendLuaGlobalScriptOverlays(assetFileSystem, *luaSource, resolvedLuaPath);
            const std::string combinedLuaSource =
                prependLuaSupport(supportLuaSource, worldCommonLuaSource, globalLuaSource);
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
    timingLogger.stage("global lua loaded");

    normalizeMapFaceHintOnlyAttributes(
        *m_selectedMap,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram);
    timingLogger.stage("map face hints normalized");

    appendIndoorScriptTextures(
        assetFileSystem,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram,
        m_selectedMap->indoorTextureSet,
        m_scriptBitmapDirectoryAssetPathsByPath,
        m_scriptBitmapPathByKey,
        m_scriptBitmapPixelsByKey
    );
    appendDecorationScriptBillboardTextures(
        assetFileSystem,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram,
        m_selectedMap->indoorDecorationBillboardSet,
        m_scriptBitmapDirectoryAssetPathsByPath,
        m_scriptBitmapPathByKey,
        m_scriptBitmapPixelsByKey
    );
    appendDecorationScriptBillboardTextures(
        assetFileSystem,
        m_selectedMap->localEventProgram,
        m_selectedMap->globalEventProgram,
        m_selectedMap->outdoorDecorationBillboardSet,
        m_scriptBitmapDirectoryAssetPathsByPath,
        m_scriptBitmapPathByKey,
        m_scriptBitmapPixelsByKey
    );
    timingLogger.stage("script textures appended");

    {
        EventRuntime eventRuntime(&m_houseTable, &m_npcDialogTable);
        const std::optional<MapDeltaData> &mapDeltaData = m_selectedMap->outdoorMapDeltaData
            ? m_selectedMap->outdoorMapDeltaData
            : m_selectedMap->indoorMapDeltaData;
        EventRuntimeState runtimeState = {};
        eventRuntime.initializeMapRuntimeState(mapDeltaData, runtimeState);
        runtimeState.mapFileName = m_selectedMap->map.fileName;
        m_selectedMap->eventRuntimeState = std::move(runtimeState);
    }
    timingLogger.stage("event runtime state built");

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

    timingLogger.stage("selected map data load complete");
    return true;
}

void GameDataLoader::applyMergedContinentSettingsToSelectedMap(const Engine::AssetFileSystem &assetFileSystem)
{
    if (!m_selectedMap || !m_selectedMap->outdoorMapData || !m_selectedMap->outdoorMapDeltaData)
    {
        return;
    }

    const MergedBolsterMapEntry *pBolsterMap =
        m_mergedBolsterMapTable.findById(static_cast<uint32_t>(m_selectedMap->map.id));

    if (pBolsterMap == nullptr || pBolsterMap->continent == 0)
    {
        return;
    }

    const MergedContinentSettingEntry *pContinentSetting =
        m_mergedContinentSettingTable.findById(pBolsterMap->continent);

    if (pContinentSetting == nullptr)
    {
        return;
    }

    if (!m_skyTextureAssetNames)
    {
        m_skyTextureAssetNames = buildSkyTextureAssetNameSet(assetFileSystem);
    }

    auto resolveMergedSkyTextureNameCached =
        [this, &assetFileSystem](const std::string &textureName) -> std::string
        {
            const std::string cacheKey = m_activeWorldId + "|" + normalizedTableTextureName(textureName);
            const auto cachedNameIt = m_resolvedMergedSkyTextureNameByKey.find(cacheKey);

            if (cachedNameIt != m_resolvedMergedSkyTextureNameByKey.end())
            {
                return cachedNameIt->second;
            }

            const std::string resolvedName = resolveMergedSkyTextureName(
                assetFileSystem,
                m_skyTextureAssetNames ? &*m_skyTextureAssetNames : nullptr,
                m_activeWorldId,
                textureName);
            m_resolvedMergedSkyTextureNameByKey[cacheKey] = resolvedName;
            return resolvedName;
        };

    OutdoorWeatherProfile profile = m_selectedMap->outdoorWeatherProfile.value_or(OutdoorWeatherProfile{});
    profile.mergedWeatherConfigured = true;
    profile.mergedMapId = static_cast<uint32_t>(m_selectedMap->map.id);
    profile.mergedWeatherEnabled = pBolsterMap->weather;
    profile.mergedRainEnabled = pBolsterMap->weather && pBolsterMap->rain;
    profile.mergedSnowEnabled = pBolsterMap->weather && pBolsterMap->snow;
    profile.mergedRainChancePercent = 20;
    profile.mergedSnowChancePercent = 15;
    profile.mergedCustomSkyTextureName = resolveMergedSkyTextureNameCached(pBolsterMap->customSky);
    profile.mergedSkyTextureNames.clear();

    for (const std::string &skyTextureName : pContinentSetting->skies)
    {
        const std::string resolvedSkyTextureName = resolveMergedSkyTextureNameCached(skyTextureName);

        if (!resolvedSkyTextureName.empty())
        {
            profile.mergedSkyTextureNames.push_back(resolvedSkyTextureName);
        }
    }

    const std::string initialSkyTextureName = !profile.mergedCustomSkyTextureName.empty()
        ? profile.mergedCustomSkyTextureName
        : (!profile.mergedSkyTextureNames.empty() ? profile.mergedSkyTextureNames.front() : std::string{});

    if (!initialSkyTextureName.empty())
    {
        m_selectedMap->outdoorMapData->skyTexture = initialSkyTextureName;
        m_selectedMap->outdoorMapDeltaData->locationTime.skyTextureName = initialSkyTextureName;
    }

    m_selectedMap->outdoorWeatherProfile = std::move(profile);
}
}
