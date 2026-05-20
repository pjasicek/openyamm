#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/TerrainTileData.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "game/tables/SurfaceMaterialTable.h"
#include "game/tables/TextureFrameTable.h"
#include "engine/ImageAssetLoader.h"
#include "engine/TextTable.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <future>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
double millisecondsFromNanoseconds(uint64_t nanoseconds)
{
    return static_cast<double>(nanoseconds) / 1000000.0;
}

bool mapLoadTimingEnabled()
{
    const char *pValue = std::getenv("OPENYAMM_MAP_LOAD_TIMING");
    return pValue != nullptr && std::string_view(pValue) != "0" && std::string_view(pValue) != "false";
}

class MapLoadTimingLogger
{
public:
    explicit MapLoadTimingLogger(const std::string &mapFileName)
        : m_enabled(mapLoadTimingEnabled())
        , m_mapFileName(mapFileName)
        , m_startTickNanoseconds(SDL_GetTicksNS())
        , m_lastTickNanoseconds(m_startTickNanoseconds)
    {
        if (m_enabled)
        {
            std::cerr << "[MapLoadTiming] map=" << m_mapFileName << " begin=asset_load\n";
        }
    }

    void stage(const std::string &stageName)
    {
        if (!m_enabled)
        {
            return;
        }

        const uint64_t nowNanoseconds = SDL_GetTicksNS();
        const uint64_t stageNanoseconds = nowNanoseconds - m_lastTickNanoseconds;
        const uint64_t totalNanoseconds = nowNanoseconds - m_startTickNanoseconds;
        m_lastTickNanoseconds = nowNanoseconds;

        std::cerr
            << "[MapLoadTiming] map=" << m_mapFileName
            << " stage=\"" << stageName << "\""
            << " delta_ms=" << millisecondsFromNanoseconds(stageNanoseconds)
            << " total_ms=" << millisecondsFromNanoseconds(totalNanoseconds)
            << '\n';
    }

private:
    bool m_enabled = false;
    std::string m_mapFileName;
    uint64_t m_startTickNanoseconds = 0;
    uint64_t m_lastTickNanoseconds = 0;
};

void pumpMapLoadProgress(const MapLoadProgressPump &progressPump)
{
    if (progressPump)
    {
        progressPump();
    }
}

std::string engineDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/" + std::string(fileName);
}

std::string monsterSpriteFrameFamilyPath(std::string_view familyRoot)
{
    return "Data/rendering/sprite_frames/monsters/" + std::string(familyRoot) + ".yml";
}

std::string monsterSpriteFrameFamilyDirectory()
{
    return "Data/rendering/sprite_frames/monsters";
}

constexpr int TerrainTextureTileSize = 128;
constexpr int TerrainTextureAtlasColumns = 16;
constexpr int TerrainTextureAtlasTilePadding = 2;
constexpr uint16_t LevelDecorationInvisible = 0x0020;
constexpr uint32_t EnvironmentFlagRain = 0x01;
constexpr uint32_t EnvironmentFlagSnow = 0x02;
constexpr uint32_t EnvironmentFlagUnderwater = 0x04;
constexpr uint32_t EnvironmentFlagAlwaysDark = 0x10;
constexpr uint32_t EnvironmentFlagAlwaysLight = 0x20;
constexpr uint32_t EnvironmentFlagAlwaysFoggy = 0x40;
constexpr uint32_t EnvironmentFlagRedFog = 0x80;
constexpr uint32_t MapWeatherFoggy = 0x01;
constexpr size_t MaxActorTexturePreloadWorkerCount = 2;

bool decodeOutdoorMapExtra(
    const MapDeltaLocationTime &locationTime,
    uint32_t &mapExtraBitsRaw,
    int32_t &ceiling)
{
    if (locationTime.reserved.size() < sizeof(mapExtraBitsRaw) + sizeof(ceiling))
    {
        mapExtraBitsRaw = 0;
        ceiling = 0;
        return false;
    }

    std::memcpy(&mapExtraBitsRaw, locationTime.reserved.data(), sizeof(mapExtraBitsRaw));
    std::memcpy(&ceiling, locationTime.reserved.data() + sizeof(mapExtraBitsRaw), sizeof(ceiling));
    return true;
}

OutdoorFogDistances fallbackAlwaysFogDistances(bool redFog, bool underwater)
{
    if (redFog)
    {
        return {0, 2048};
    }

    if (underwater)
    {
        return {0, 4096};
    }

    return {0, 4096};
}

OutdoorPrecipitationKind precipitationKindFromFlags(uint32_t mapExtraBitsRaw)
{
    if ((mapExtraBitsRaw & EnvironmentFlagSnow) != 0)
    {
        return OutdoorPrecipitationKind::Snow;
    }

    if ((mapExtraBitsRaw & EnvironmentFlagRain) != 0)
    {
        return OutdoorPrecipitationKind::Rain;
    }

    return OutdoorPrecipitationKind::None;
}

OutdoorPrecipitationKind precipitationKindFromSceneFlags(const OutdoorSceneEnvironment::Flags &flags)
{
    if (flags.snowing)
    {
        return OutdoorPrecipitationKind::Snow;
    }

    if (flags.raining)
    {
        return OutdoorPrecipitationKind::Rain;
    }

    return OutdoorPrecipitationKind::None;
}

OutdoorWeatherProfile buildOutdoorWeatherProfile(
    const OutdoorSceneEnvironment &environment,
    const MapDeltaLocationTime &locationTime)
{
    OutdoorWeatherProfile profile = {};
    profile.fogMode = environment.weather.fogMode;
    profile.defaultPrecipitation = environment.weather.precipitation != OutdoorPrecipitationKind::None
        ? environment.weather.precipitation
        : precipitationKindFromSceneFlags(environment.flags);
    profile.alwaysFoggy = environment.flags.alwaysFoggy;
    profile.alwaysDark = environment.flags.alwaysDark;
    profile.alwaysLight = environment.flags.alwaysLight;
    profile.redFog = environment.flags.redFog;
    profile.hasFogTint = environment.weather.hasFogTint;
    profile.fogTintRgb = environment.weather.fogTintRgb;
    profile.underwater = environment.flags.underwater;
    profile.defaultFog = {environment.fogWeakDistance, environment.fogStrongDistance};
    profile.smallFogChance = environment.weather.smallFogChance;
    profile.averageFogChance = environment.weather.averageFogChance;
    profile.denseFogChance = environment.weather.denseFogChance;
    profile.smallFog = environment.weather.smallFog;
    profile.averageFog = environment.weather.averageFog;
    profile.denseFog = environment.weather.denseFog;

    if (profile.alwaysFoggy && profile.defaultFog.strongDistance <= 0)
    {
        profile.defaultFog = fallbackAlwaysFogDistances(profile.redFog, profile.underwater);
    }

    if ((locationTime.weatherFlags & MapWeatherFoggy) != 0 && locationTime.fogStrongDistance > 0)
    {
        profile.defaultFog = {locationTime.fogWeakDistance, locationTime.fogStrongDistance};
    }

    return profile;
}

OutdoorWeatherProfile buildOutdoorWeatherProfile(const MapDeltaLocationTime &locationTime)
{
    uint32_t mapExtraBitsRaw = 0;
    int32_t ceiling = 0;
    decodeOutdoorMapExtra(locationTime, mapExtraBitsRaw, ceiling);

    OutdoorWeatherProfile profile = {};
    profile.defaultPrecipitation = precipitationKindFromFlags(mapExtraBitsRaw);
    profile.alwaysFoggy = (mapExtraBitsRaw & EnvironmentFlagAlwaysFoggy) != 0;
    profile.alwaysDark = (mapExtraBitsRaw & EnvironmentFlagAlwaysDark) != 0;
    profile.alwaysLight = (mapExtraBitsRaw & EnvironmentFlagAlwaysLight) != 0;
    profile.redFog = (mapExtraBitsRaw & EnvironmentFlagRedFog) != 0;
    profile.underwater = (mapExtraBitsRaw & EnvironmentFlagUnderwater) != 0;
    profile.defaultFog = {locationTime.fogWeakDistance, locationTime.fogStrongDistance};

    if (profile.alwaysFoggy && profile.defaultFog.strongDistance <= 0)
    {
        profile.defaultFog = fallbackAlwaysFogDistances(profile.redFog, profile.underwater);
    }

    return profile;
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
    const DecorationEntry *pNamedDecoration = nullptr;

    if (!entity.name.empty())
    {
        pNamedDecoration = decorationTable.findByInternalName(entity.name);

        if (pNamedDecoration != nullptr
            && hasDecorationFlag(pNamedDecoration->flags, DecorationDescFlag::DontDraw))
        {
            return pNamedDecoration;
        }
    }

    const DecorationEntry *pDecoration = decorationTable.get(entity.decorationListId);

    if ((pDecoration == nullptr || pDecoration->spriteId == 0) && pNamedDecoration != nullptr)
    {
        pDecoration = pNamedDecoration;
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

bool hasTerrainTileFlag(const TerrainTileDescriptor &descriptor, uint16_t flag)
{
    return (descriptor.flags & flag) != 0;
}

bool isTerrainDescriptorLiquid(const TerrainTileDescriptor &descriptor)
{
    return (descriptor.flags & (TerrainTileFlagBurn | TerrainTileFlagWater)) != 0;
}

bool isTerrainDescriptorTransition(const TerrainTileDescriptor &descriptor)
{
    return hasTerrainTileFlag(descriptor, TerrainTileFlagTransition);
}

const TerrainTileDescriptor *findLiquidBaseTerrainDescriptor(
    const std::vector<TerrainTileDescriptor> &tileDescriptors,
    const TerrainTileDescriptor &descriptor)
{
    const TerrainTileDescriptor *pFallback = nullptr;

    for (const TerrainTileDescriptor &candidate : tileDescriptors)
    {
        if (candidate.tileset != descriptor.tileset
            || candidate.textureName.empty()
            || candidate.textureName == "pending"
            || !isTerrainDescriptorLiquid(candidate)
            || isTerrainDescriptorTransition(candidate))
        {
            continue;
        }

        if (pFallback == nullptr)
        {
            pFallback = &candidate;
        }

        if (candidate.variant == 0)
        {
            return &candidate;
        }
    }

    return pFallback;
}

const SurfaceMaterialDefinition *findTerrainSurfaceMaterialForDescriptor(
    const TerrainTileDescriptor &descriptor,
    const std::vector<TerrainTileDescriptor> &tileDescriptors,
    const SurfaceMaterialTable *pSurfaceMaterialTable,
    const TerrainTileDescriptor **ppBaseDescriptor)
{
    if (ppBaseDescriptor != nullptr)
    {
        *ppBaseDescriptor = nullptr;
    }

    if (pSurfaceMaterialTable == nullptr)
    {
        return nullptr;
    }

    const TerrainTileDescriptor *pBaseDescriptor = nullptr;

    if (isTerrainDescriptorTransition(descriptor))
    {
        pBaseDescriptor = findLiquidBaseTerrainDescriptor(tileDescriptors, descriptor);

        if (ppBaseDescriptor != nullptr)
        {
            *ppBaseDescriptor = pBaseDescriptor;
        }
    }

    if (const SurfaceMaterialDefinition *pMaterial =
            pSurfaceMaterialTable->findMatch(descriptor.textureName, 0, true))
    {
        return pMaterial;
    }

    if (pBaseDescriptor == nullptr)
    {
        pBaseDescriptor = findLiquidBaseTerrainDescriptor(tileDescriptors, descriptor);
    }

    if (pBaseDescriptor == nullptr)
    {
        return nullptr;
    }

    if (ppBaseDescriptor != nullptr)
    {
        *ppBaseDescriptor = pBaseDescriptor;
    }

    return pSurfaceMaterialTable->findMatch(pBaseDescriptor->textureName, 0, true);
}

std::vector<uint8_t> scrollTerrainPixels(
    const std::vector<uint8_t> &sourcePixels,
    int width,
    int height,
    int offsetX,
    int offsetY)
{
    if (width <= 0 || height <= 0 || sourcePixels.size() < static_cast<size_t>(width * height * 4))
    {
        return sourcePixels;
    }

    std::vector<uint8_t> scrolledPixels(sourcePixels.size(), 0);

    for (int y = 0; y < height; ++y)
    {
        const int sourceY = (y + offsetY + height) % height;

        for (int x = 0; x < width; ++x)
        {
            const int sourceX = (x + offsetX + width) % width;
            const size_t sourceOffset = static_cast<size_t>((sourceY * width + sourceX) * 4);
            const size_t targetOffset = static_cast<size_t>((y * width + x) * 4);
            std::memcpy(
                scrolledPixels.data() + static_cast<ptrdiff_t>(targetOffset),
                sourcePixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                4);
        }
    }

    return scrolledPixels;
}

SurfaceAnimationSequence fallbackLiquidSurfaceAnimation()
{
    constexpr uint32_t FallbackAnimationTicks = 128;
    constexpr int FallbackFrameCount = 7;

    SurfaceAnimationSequence animation = {};
    animation.animationLengthTicks = FallbackAnimationTicks;

    for (int frameIndex = 0; frameIndex < FallbackFrameCount; ++frameIndex)
    {
        SurfaceAnimationFrame frame = {};
        frame.textureName = "generated_liquid_scroll_" + std::to_string(frameIndex);
        frame.frameLengthTicks = FallbackAnimationTicks / FallbackFrameCount;
        animation.frames.push_back(std::move(frame));
    }

    return animation;
}

std::vector<std::vector<uint8_t>> buildFallbackLiquidAnimationFrames(
    const std::vector<uint8_t> &basePixels,
    int width,
    int height,
    SurfaceAnimationSequence &animation)
{
    std::vector<std::vector<uint8_t>> frames;
    animation = fallbackLiquidSurfaceAnimation();
    frames.reserve(animation.frames.size());

    for (size_t frameIndex = 0; frameIndex < animation.frames.size(); ++frameIndex)
    {
        frames.push_back(
            scrollTerrainPixels(
                basePixels,
                width,
                height,
                static_cast<int>(frameIndex) * 3,
                static_cast<int>(frameIndex) * 2));
    }

    return frames;
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
    std::vector<std::vector<std::string>> &rows,
    MapAssetLoadSharedCache *pSharedCache)
{
    rows.clear();

    if (pSharedCache != nullptr && pSharedCache->decorationRows)
    {
        rows = *pSharedCache->decorationRows;
        return true;
    }

    const std::optional<std::string> contents =
        assetFileSystem.readTextFile(engineDataTablePath("decoration_data.txt"));

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

    if (pSharedCache != nullptr)
    {
        pSharedCache->decorationRows = rows;
    }

    return true;
}

bool loadTextureFrameRows(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<std::vector<std::string>> &rows)
{
    rows.clear();

    const std::optional<std::string> contents =
        assetFileSystem.readTextFile(engineDataTablePath("texture_frame_data.txt"));

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

std::optional<TextureFrameTable> loadTextureFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    MapAssetLoadSharedCache *pSharedCache)
{
    if (pSharedCache != nullptr && pSharedCache->textureFrameTable)
    {
        return pSharedCache->textureFrameTable;
    }

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

    if (pSharedCache != nullptr)
    {
        pSharedCache->textureFrameTable = textureFrameTable;
    }

    return textureFrameTable;
}

std::optional<std::string> monsterSpriteFamilyRoot(const std::string &spriteName)
{
    const std::string normalizedName = toLowerCopy(spriteName);

    if (normalizedName.size() < 4 || normalizedName[0] != 'm')
    {
        return std::nullopt;
    }

    if (std::isdigit(static_cast<unsigned char>(normalizedName[1])) == 0
        || std::isdigit(static_cast<unsigned char>(normalizedName[2])) == 0
        || std::isdigit(static_cast<unsigned char>(normalizedName[3])) == 0)
    {
        return std::nullopt;
    }

    return normalizedName.substr(0, 4);
}

bool isWorldPrefixedMonsterSpriteName(const std::string &spriteName)
{
    const std::string normalizedName = toLowerCopy(spriteName);

    return normalizedName.size() >= 5
        && std::isdigit(static_cast<unsigned char>(normalizedName[0])) != 0
        && normalizedName[1] == 'm'
        && std::isdigit(static_cast<unsigned char>(normalizedName[2])) != 0
        && std::isdigit(static_cast<unsigned char>(normalizedName[3])) != 0
        && std::isdigit(static_cast<unsigned char>(normalizedName[4])) != 0;
}

void appendMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    std::unordered_set<std::string> &worldPrefixedSpriteNames,
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
        else if (isWorldPrefixedMonsterSpriteName(spriteName))
        {
            worldPrefixedSpriteNames.insert(toLowerCopy(spriteName));
        }
    }
}

void collectSummonMonsterSpriteFamilies(
    std::unordered_set<std::string> &neededMonsterFamilies,
    std::unordered_set<std::string> &neededWorldPrefixedMonsterSpriteNames,
    const MonsterTable &monsterTable)
{
    static constexpr std::array<int16_t, 3> SummonWispMonsterIds = {97, 98, 99};

    for (int16_t monsterId : SummonWispMonsterIds)
    {
        appendMonsterSpriteFamilies(
            neededMonsterFamilies,
            neededWorldPrefixedMonsterSpriteNames,
            monsterTable.findById(monsterId));
    }
}

template <typename SpawnType>
void collectSpawnMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    std::unordered_set<std::string> &worldPrefixedSpriteNames,
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

        appendMonsterSpriteFamilies(families, worldPrefixedSpriteNames, monsterTable.findByInternalName(*monsterName));
    }
}

void collectMapDeltaMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    std::unordered_set<std::string> &worldPrefixedSpriteNames,
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

        appendMonsterSpriteFamilies(families, worldPrefixedSpriteNames, pMonsterEntry);
    }
}

void collectEncounterMonsterSpriteFamilies(
    std::unordered_set<std::string> &families,
    std::unordered_set<std::string> &worldPrefixedSpriteNames,
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

            appendMonsterSpriteFamilies(
                families,
                worldPrefixedSpriteNames,
                monsterTable.findById(static_cast<int16_t>(pStats->id)));
        }
    }
}

std::optional<SurfaceMaterialTable> loadSurfaceMaterialTable(
    const Engine::AssetFileSystem &assetFileSystem,
    MapAssetLoadSharedCache *pSharedCache)
{
    if (pSharedCache != nullptr && pSharedCache->surfaceMaterialTable)
    {
        return pSharedCache->surfaceMaterialTable;
    }

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

    if (pSharedCache != nullptr)
    {
        pSharedCache->surfaceMaterialTable = materialTable;
    }

    return materialTable;
}

std::optional<std::string> loadMonsterSpriteFrameFamilyText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &familyRoot,
    MapAssetLoadSharedCache *pSharedCache,
    const std::string &familyPathOverride = {})
{
    const std::string normalizedFamilyRoot = toLowerCopy(familyRoot);

    if (pSharedCache != nullptr)
    {
        const auto cachedTextIt =
            pSharedCache->monsterSpriteFrameFamilyTextByRoot.find(normalizedFamilyRoot);

        if (cachedTextIt != pSharedCache->monsterSpriteFrameFamilyTextByRoot.end())
        {
            if (cachedTextIt->second || familyPathOverride.empty())
            {
                return cachedTextIt->second;
            }
        }
    }

    const std::optional<std::string> familyContents =
        assetFileSystem.readTextFile(
            familyPathOverride.empty()
                ? monsterSpriteFrameFamilyPath(normalizedFamilyRoot)
                : familyPathOverride);

    if (pSharedCache != nullptr)
    {
        pSharedCache->monsterSpriteFrameFamilyTextByRoot[normalizedFamilyRoot] = familyContents;
    }

    return familyContents;
}

std::vector<std::string> enumerateMonsterSpriteFrameFamilyEntries(
    const Engine::AssetFileSystem &assetFileSystem,
    MapAssetLoadSharedCache *pSharedCache)
{
    if (pSharedCache != nullptr && pSharedCache->monsterSpriteFrameFamilyEntries)
    {
        return *pSharedCache->monsterSpriteFrameFamilyEntries;
    }

    std::vector<std::string> familyEntries = assetFileSystem.enumerate(monsterSpriteFrameFamilyDirectory());

    if (pSharedCache != nullptr)
    {
        pSharedCache->monsterSpriteFrameFamilyEntries = familyEntries;
    }

    return familyEntries;
}

std::optional<SpriteFrameTable> loadCommonSpriteFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    MapAssetLoadSharedCache *pSharedCache)
{
    if (pSharedCache != nullptr && pSharedCache->commonSpriteFrameTable)
    {
        return pSharedCache->commonSpriteFrameTable;
    }

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

    if (pSharedCache != nullptr)
    {
        pSharedCache->commonSpriteFrameTable = spriteFrameTable;
    }

    return spriteFrameTable;
}

std::optional<SpriteFrameTable> loadSpriteFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_set<std::string> &monsterFamilies = {},
    const std::unordered_set<std::string> &worldPrefixedMonsterSpriteNames = {},
    MapAssetLoadSharedCache *pSharedCache = nullptr)
{
    const std::optional<SpriteFrameTable> commonSpriteFrameTable =
        loadCommonSpriteFrameTable(assetFileSystem, pSharedCache);

    if (!commonSpriteFrameTable)
    {
        return std::nullopt;
    }

    SpriteFrameTable spriteFrameTable = *commonSpriteFrameTable;
    std::string errorMessage;

    std::vector<std::string> sortedFamilies(monsterFamilies.begin(), monsterFamilies.end());
    std::sort(sortedFamilies.begin(), sortedFamilies.end());

    for (const std::string &familyRoot : sortedFamilies)
    {
        const std::optional<std::string> familyContents =
            loadMonsterSpriteFrameFamilyText(assetFileSystem, familyRoot, pSharedCache);

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

    std::unordered_set<std::string> unresolvedWorldPrefixedSprites;

    for (const std::string &spriteName : worldPrefixedMonsterSpriteNames)
    {
        if (!spriteFrameTable.findFrameIndexBySpriteName(spriteName))
        {
            unresolvedWorldPrefixedSprites.insert(spriteName);
        }
    }

    const std::vector<std::string> familyEntries =
        enumerateMonsterSpriteFrameFamilyEntries(assetFileSystem, pSharedCache);

    for (const std::string &familyEntry : familyEntries)
    {
        if (unresolvedWorldPrefixedSprites.empty())
        {
            break;
        }

        const std::string normalizedEntry = toLowerCopy(familyEntry);

        if (!normalizedEntry.ends_with(".yml"))
        {
            continue;
        }

        const std::string familyRoot = normalizedEntry.substr(0, normalizedEntry.size() - 4);

        if (monsterFamilies.find(familyRoot) != monsterFamilies.end())
        {
            continue;
        }

        const std::optional<std::string> familyContents =
            loadMonsterSpriteFrameFamilyText(
                assetFileSystem,
                familyRoot,
                pSharedCache,
                monsterSpriteFrameFamilyDirectory() + "/" + familyEntry);

        if (!familyContents)
        {
            continue;
        }

        std::vector<std::string> resolvedSpritesInFamily;
        const std::string normalizedContents = toLowerCopy(*familyContents);

        for (const std::string &spriteName : unresolvedWorldPrefixedSprites)
        {
            const std::string spriteNameNeedle = "sprite_name: \"" + spriteName + "\"";

            if (normalizedContents.find(spriteNameNeedle) != std::string::npos)
            {
                resolvedSpritesInFamily.push_back(spriteName);
            }
        }

        if (resolvedSpritesInFamily.empty())
        {
            continue;
        }

        if (!spriteFrameTable.loadFromYaml(*familyContents, errorMessage, true))
        {
            std::cerr << "Failed to load monster sprite frame family " << familyRoot
                      << ": " << errorMessage << '\n';
            return std::nullopt;
        }

        for (const std::string &spriteName : resolvedSpritesInFamily)
        {
            unresolvedWorldPrefixedSprites.erase(spriteName);
        }
    }

    for (const std::string &spriteName : unresolvedWorldPrefixedSprites)
    {
        std::cerr << "Failed to resolve world-prefixed monster sprite frame: " << spriteName << '\n';
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

std::unordered_set<std::string> collectTerrainFallbackTextureNames(
    const std::vector<std::pair<std::string, SurfaceAnimationSequence>> &animationBindings)
{
    std::unordered_set<std::string> fallbackTextureNames;

    for (const auto &binding : animationBindings)
    {
        const SurfaceAnimationSequence &animation = binding.second;

        if (animation.frames.size() <= 1)
        {
            continue;
        }

        fallbackTextureNames.insert(binding.first);

        for (const SurfaceAnimationFrame &frame : animation.frames)
        {
            fallbackTextureNames.insert(toLowerCopy(frame.textureName));
        }
    }

    return fallbackTextureNames;
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
    MapAssetLoadSharedCache *pSharedCache = nullptr;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryAssetPathsByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<std::string, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesByKey;
    std::unordered_map<std::string, std::optional<IndexedBitmapData>> indexedBitmapsByPath;
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> pixelsByKey;
};

std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &bitmapDirectoryAssetPathsByPath(
    BitmapLoadCache &bitmapLoadCache)
{
    return bitmapLoadCache.pSharedCache != nullptr
        ? bitmapLoadCache.pSharedCache->bitmapDirectoryAssetPathsByPath
        : bitmapLoadCache.directoryAssetPathsByPath;
}

std::unordered_map<std::string, std::optional<std::string>> &bitmapPathByKey(
    BitmapLoadCache &bitmapLoadCache)
{
    return bitmapLoadCache.pSharedCache != nullptr
        ? bitmapLoadCache.pSharedCache->bitmapPathByKey
        : bitmapLoadCache.bitmapPathByKey;
}

std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> &bitmapBinaryFilesByPath(
    BitmapLoadCache &bitmapLoadCache)
{
    return bitmapLoadCache.pSharedCache != nullptr
        ? bitmapLoadCache.pSharedCache->bitmapBinaryFilesByPath
        : bitmapLoadCache.binaryFilesByPath;
}

std::unordered_map<std::string, std::optional<std::array<uint8_t, 256 * 3>>> &bitmapActPalettesByKey(
    BitmapLoadCache &bitmapLoadCache)
{
    return bitmapLoadCache.pSharedCache != nullptr
        ? bitmapLoadCache.pSharedCache->actPalettesByKey
        : bitmapLoadCache.actPalettesByKey;
}

std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> &bitmapPixelsByKey(
    BitmapLoadCache &bitmapLoadCache)
{
    return bitmapLoadCache.pSharedCache != nullptr
        ? bitmapLoadCache.pSharedCache->bitmapPixelsByKey
        : bitmapLoadCache.pixelsByKey;
}

std::string actPaletteCacheKey(int16_t paletteId, const std::string &worldId)
{
    const std::string normalizedWorldId = worldId.empty() ? std::string() : normalizeWorldId(worldId);
    return normalizedWorldId + "|" + std::to_string(static_cast<int>(paletteId));
}

std::vector<std::string> actPaletteCandidatePaths(int16_t paletteId, const std::string &worldId)
{
    char paletteFileName[16] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));

    std::vector<std::string> paths;

    if (!worldId.empty())
    {
        paths.push_back("worlds/" + normalizeWorldId(worldId) + "/textures/" + paletteFileName);
    }

    paths.push_back(std::string("Data/bitmaps/") + paletteFileName);
    return paths;
}

std::optional<std::string> findBitmapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    BitmapLoadCache &bitmapLoadCache
)
{
    return Engine::findImageAssetPath(
        assetFileSystem,
        directoryPath,
        textureName,
        bitmapDirectoryAssetPathsByPath(bitmapLoadCache),
        bitmapPathByKey(bitmapLoadCache));
}

std::optional<std::string> findAssetPathCaseInsensitive(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    BitmapLoadCache &bitmapLoadCache
)
{
    const std::string cacheKey = directoryPath + "|" + toLowerCopy(fileName);
    std::unordered_map<std::string, std::optional<std::string>> &pathCache = bitmapPathByKey(bitmapLoadCache);
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> &directoryCache =
        bitmapDirectoryAssetPathsByPath(bitmapLoadCache);
    const auto cachedPathIt = pathCache.find(cacheKey);

    if (cachedPathIt != pathCache.end())
    {
        return cachedPathIt->second;
    }

    const auto directoryAssetPathsIt = directoryCache.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pAssetPaths = nullptr;

    if (directoryAssetPathsIt != directoryCache.end())
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

        pAssetPaths = &directoryCache.emplace(directoryPath, std::move(assetPaths)).first->second;
    }

    const std::string normalizedFileName = toLowerCopy(fileName);
    const auto resolvedPathIt = pAssetPaths->find(normalizedFileName);

    if (resolvedPathIt != pAssetPaths->end())
    {
        const std::optional<std::string> resolvedPath = resolvedPathIt->second;
        pathCache[cacheKey] = resolvedPath;
        return resolvedPath;
    }

    pathCache[cacheKey] = std::nullopt;
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
    BitmapLoadCache &bitmapLoadCache,
    const std::string &worldId = {}
)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const std::string cacheKey = actPaletteCacheKey(paletteId, worldId);
    std::unordered_map<std::string, std::optional<std::array<uint8_t, 256 * 3>>> &paletteCache =
        bitmapActPalettesByKey(bitmapLoadCache);
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> &binaryFileCache =
        bitmapBinaryFilesByPath(bitmapLoadCache);
    const auto cachedPaletteIt = paletteCache.find(cacheKey);

    if (cachedPaletteIt != paletteCache.end())
    {
        return cachedPaletteIt->second;
    }

    for (const std::string &palettePath : actPaletteCandidatePaths(paletteId, worldId))
    {
        const auto cachedFileIt = binaryFileCache.find(palettePath);
        std::optional<std::vector<uint8_t>> paletteBytes;

        if (cachedFileIt != binaryFileCache.end())
        {
            paletteBytes = cachedFileIt->second;
        }
        else
        {
            paletteBytes = assetFileSystem.readBinaryFile(palettePath);
            binaryFileCache[palettePath] = paletteBytes;
        }

        if (!paletteBytes || paletteBytes->size() < 256 * 3)
        {
            continue;
        }

        std::array<uint8_t, 256 * 3> palette = {};
        std::memcpy(palette.data(), paletteBytes->data(), palette.size());
        paletteCache[cacheKey] = palette;
        return palette;
    }

    paletteCache[cacheKey] = std::nullopt;
    return std::nullopt;
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
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> &binaryFileCache =
        bitmapBinaryFilesByPath(bitmapLoadCache);
    const auto cachedFileIt = binaryFileCache.find(bitmapPath);

    if (cachedFileIt != binaryFileCache.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(bitmapPath);
        binaryFileCache[bitmapPath] = bitmapBytes;
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
    BitmapLoadCache &bitmapLoadCache,
    const std::string &paletteWorldId = {}
)
{
    const std::optional<IndexedBitmapData> indexedBitmap =
        loadIndexedBitmapData(assetFileSystem, bitmapPath, bitmapLoadCache);
    const std::optional<std::array<uint8_t, 256 * 3>> overridePalette =
        loadActPalette(assetFileSystem, paletteId, bitmapLoadCache, paletteWorldId);

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
    int16_t paletteId = 0,
    const std::string &paletteWorldId = {}
)
{
    const int forcedTerrainTileSize =
        forceTerrainTileSize
            ? terrainTexturePhysicalTileSize(assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Terrain))
            : 0;
    const std::string cacheKey =
        directoryPath + "|" + toLowerCopy(textureName)
        + "|" + std::to_string(forcedTerrainTileSize)
        + "|" + std::to_string(applyTransparencyKey ? 1 : 0)
        + "|" + std::to_string(static_cast<int>(paletteId))
        + "|" + (paletteWorldId.empty() ? std::string() : normalizeWorldId(paletteWorldId));
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> &pixelCache =
        bitmapPixelsByKey(bitmapLoadCache);
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> &binaryFileCache =
        bitmapBinaryFilesByPath(bitmapLoadCache);
    const auto cachedPixelsIt = pixelCache.find(cacheKey);

    if (cachedPixelsIt != pixelCache.end())
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
        pixelCache[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = binaryFileCache.find(*bitmapPath);

    if (cachedFileIt != binaryFileCache.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);
        binaryFileCache[*bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        pixelCache[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = paletteId > 0 && !forceTerrainTileSize
        ? loadActPalette(assetFileSystem, paletteId, bitmapLoadCache, paletteWorldId)
        : std::nullopt;
    decodeOptions.applyPaletteZeroTransparencyKey = applyTransparencyKey;
    const bool isSpriteTexture = directoryPath == "Data/sprites";
    decodeOptions.applyMagentaTransparencyKey = !isSpriteTexture;
    decodeOptions.applyTealTransparencyKey = applyTransparencyKey && !isSpriteTexture;

    std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath, decodeOptions);

    if (!image)
    {
        pixelCache[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    std::vector<uint8_t> pixels = std::move(image->pixels);

    if (forceTerrainTileSize && (width != forcedTerrainTileSize || height != forcedTerrainTileSize))
    {
        pixels = Engine::scalePixelsNearestBgra(pixels, width, height, forcedTerrainTileSize, forcedTerrainTileSize);

        if (pixels.empty())
        {
            pixelCache[cacheKey] = std::nullopt;
            return std::nullopt;
        }

        width = forcedTerrainTileSize;
        height = forcedTerrainTileSize;
    }

    pixelCache[cacheKey] = MapAssetBitmapPixelsResult{width, height, pixels};
    return pixels;
}

size_t actorTexturePreloadWorkerCount(size_t requestCount)
{
    if (requestCount <= 1)
    {
        return requestCount;
    }

    const unsigned int hardwareThreadCount = std::thread::hardware_concurrency();
    const size_t availableThreadCount = hardwareThreadCount > 1 ? static_cast<size_t>(hardwareThreadCount - 1) : 1;
    const size_t cappedThreadCount = std::min(availableThreadCount, MaxActorTexturePreloadWorkerCount);
    return std::min(cappedThreadCount, requestCount);
}

OutdoorBitmapTexture decodeActorBitmapTextureRequest(
    const Engine::AssetFileSystem &assetFileSystem,
    const BitmapTextureRequest &textureRequest,
    Engine::AssetScaleTier spriteAssetScaleTier,
    const std::string &worldId,
    BitmapLoadCache &bitmapLoadCache)
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
            textureRequest.paletteId,
            worldId);

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        return {};
    }

    OutdoorBitmapTexture texture = {};
    texture.textureName = textureRequest.textureName;
    texture.paletteId = textureRequest.paletteId;
    texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, spriteAssetScaleTier);
    texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, spriteAssetScaleTier);
    texture.physicalWidth = textureWidth;
    texture.physicalHeight = textureHeight;
    texture.pixels = *pixels;
    return texture;
}

std::shared_ptr<std::vector<OutdoorBitmapTexture>> decodeActorBitmapTextureRequests(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<BitmapTextureRequest> &textureRequests,
    Engine::AssetScaleTier spriteAssetScaleTier,
    const std::string &worldId)
{
    std::shared_ptr<std::vector<OutdoorBitmapTexture>> pTextures =
        std::make_shared<std::vector<OutdoorBitmapTexture>>();

    if (textureRequests.empty())
    {
        return pTextures;
    }

    const size_t workerCount = actorTexturePreloadWorkerCount(textureRequests.size());
    std::vector<std::future<std::vector<OutdoorBitmapTexture>>> futures;
    futures.reserve(workerCount);

    for (size_t workerIndex = 0; workerIndex < workerCount; ++workerIndex)
    {
        futures.push_back(std::async(
            std::launch::async,
            [&assetFileSystem, &textureRequests, spriteAssetScaleTier, worldId, workerIndex, workerCount]()
            {
                BitmapLoadCache workerBitmapLoadCache = {};
                std::vector<OutdoorBitmapTexture> textures;

                for (size_t requestIndex = workerIndex; requestIndex < textureRequests.size(); requestIndex += workerCount)
                {
                    OutdoorBitmapTexture texture =
                        decodeActorBitmapTextureRequest(
                            assetFileSystem,
                            textureRequests[requestIndex],
                            spriteAssetScaleTier,
                            worldId,
                            workerBitmapLoadCache);

                    if (!texture.pixels.empty() && texture.physicalWidth > 0 && texture.physicalHeight > 0)
                    {
                        textures.push_back(std::move(texture));
                    }
                }

                return textures;
            }));
    }

    for (std::future<std::vector<OutdoorBitmapTexture>> &future : futures)
    {
        std::vector<OutdoorBitmapTexture> workerTextures = future.get();
        pTextures->insert(
            pTextures->end(),
            std::make_move_iterator(workerTextures.begin()),
            std::make_move_iterator(workerTextures.end()));
    }

    return pTextures;
}

std::optional<std::vector<uint8_t>> loadTerrainBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int &width,
    int &height,
    bool applyTransparencyKey,
    BitmapLoadCache &bitmapLoadCache)
{
    std::optional<std::vector<uint8_t>> pixels =
        loadBitmapPixelsBgra(
            assetFileSystem,
            "terrain",
            textureName,
            width,
            height,
            true,
            applyTransparencyKey,
            bitmapLoadCache);

    if (pixels)
    {
        return pixels;
    }

    return loadBitmapPixelsBgra(
        assetFileSystem,
        "terrain_textures",
        textureName,
        width,
        height,
        true,
        applyTransparencyKey,
        bitmapLoadCache);
}

template <typename EntityType>
std::optional<DecorationBillboardSet> buildDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<EntityType> &entities,
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    DecorationBillboardSet billboardSet = {};

    const std::optional<SpriteFrameTable> spriteFrameTable =
        loadSpriteFrameTable(assetFileSystem, {}, {}, pSharedCache);

    if (!spriteFrameTable)
    {
        return std::nullopt;
    }

    billboardSet.spriteFrameTable = *spriteFrameTable;

    std::vector<std::vector<std::string>> decorationRows;

    if (!loadDecorationRows(assetFileSystem, decorationRows, pSharedCache)
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
        billboard.eventIdPrimary = entity.eventIdPrimary;
        billboard.eventIdSecondary = entity.eventIdSecondary;
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

    const Engine::AssetScaleTier decorationAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Decorations);

    for (const std::string &textureName : textureNames)
    {
        pumpMapLoadProgress(progressPump);
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
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, decorationAssetScaleTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, decorationAssetScaleTier);
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
    const std::vector<EntityType> &entities,
    MapAssetLoadSharedCache *pSharedCache
)
{
    DecorationTable decorationTable;

    std::vector<std::vector<std::string>> decorationRows;

    if (!loadDecorationRows(assetFileSystem, decorationRows, pSharedCache)
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
            actorZ = static_cast<int>(std::lround(sampleOutdoorActorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actorZ),
                std::max(5.0f, static_cast<float>(actor.radius)))));
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
            actorZ = static_cast<int>(std::lround(sampleOutdoorActorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(actorZ),
                std::max(5.0f, static_cast<float>(pMonsterEntry->radius)))));
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
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    std::optional<DecorationBillboardSet> billboardSet =
        buildDecorationBillboardSet(
            assetFileSystem,
            outdoorMapData.entities,
            bitmapLoadCache,
            progressPump,
            pSharedCache);

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
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    std::optional<DecorationBillboardSet> billboardSet =
        buildDecorationBillboardSet(
            assetFileSystem,
            indoorMapData.entities,
            bitmapLoadCache,
            progressPump,
            pSharedCache);

    if (!billboardSet)
    {
        return std::nullopt;
    }

    std::vector<int16_t> entitySectorIds(indoorMapData.entities.size(), -1);

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorIndex];

        for (uint16_t decorationId : sector.decorationIds)
        {
            if (decorationId < entitySectorIds.size())
            {
                entitySectorIds[decorationId] = static_cast<int16_t>(sectorIndex);
            }
        }
    }

    // Match the editor's room assignment for legacy maps that do not already carry complete decoration lists.
    // This runs while loading the indoor billboard asset; render frames only consume cached sector ids.
    IndoorFaceGeometryCache geometryCache(indoorMapData.faces.size());

    for (DecorationBillboard &billboard : billboardSet->billboards)
    {
        const std::optional<int16_t> resolvedSectorId =
            findIndoorSectorForPoint(
                indoorMapData,
                indoorMapData.vertices,
                {
                    static_cast<float>(billboard.x),
                    static_cast<float>(billboard.y),
                    static_cast<float>(billboard.z)
                },
                &geometryCache);

        if (resolvedSectorId)
        {
            billboard.sectorId = *resolvedSectorId;
        }
        else if (billboard.entityIndex < entitySectorIds.size())
        {
            billboard.sectorId = entitySectorIds[billboard.entityIndex];
        }
    }

    return billboardSet;
}

std::optional<SpriteObjectBillboardSet> buildSpriteObjectBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const ObjectTable &objectTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    if (!mapDeltaData || mapDeltaData->spriteObjects.empty())
    {
        return std::nullopt;
    }

    SpriteObjectBillboardSet billboardSet = {};

    const std::optional<SpriteFrameTable> spriteFrameTable =
        loadSpriteFrameTable(assetFileSystem, {}, {}, pSharedCache);

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

    const Engine::AssetScaleTier spriteAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Sprites);

    for (const std::string &textureName : textureNames)
    {
        pumpMapLoadProgress(progressPump);
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
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, spriteAssetScaleTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, spriteAssetScaleTier);
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

const MapEncounterInfo *mapEncounterInfoBySlot(const MapStatsEntry &map, int encounterSlot)
{
    switch (encounterSlot)
    {
        case 1:
            return &map.encounter1;
        case 2:
            return &map.encounter2;
        case 3:
            return &map.encounter3;
        default:
            return nullptr;
    }
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

void appendArpgModePlayerMonsterTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    const MonsterTable &monsterTable)
{
    static constexpr std::array<const char *, 2> ArpgModePlayerMonsterDescriptors = {
        "Lich A",
        "Lich C",
    };

    for (const char *pDescriptorName : ArpgModePlayerMonsterDescriptors)
    {
        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(pDescriptorName);

        if (pMonsterEntry == nullptr)
        {
            continue;
        }

        appendMonsterActionTextures(
            textureRequests,
            spriteFrameTable,
            buildMonsterActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry));
    }
}

void appendEncounterSlotTierTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    int encounterSlot)
{
    const MapEncounterInfo *pEncounter = mapEncounterInfoBySlot(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return;
    }

    const std::string pictureBase =
        trimAsciiWhitespace(pEncounter->pictureName.empty() ? pEncounter->monsterName : pEncounter->pictureName);

    if (pictureBase.empty())
    {
        return;
    }

    for (char tierLetter : {'A', 'B', 'C'})
    {
        const std::string pictureName = pictureBase + " " + std::string(1, tierLetter);
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsByPictureName(pictureName);

        if (pStats == nullptr)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry = monsterTable.findById(static_cast<int16_t>(pStats->id));

        if (pMonsterEntry == nullptr)
        {
            continue;
        }

        appendMonsterActionTextures(
            textureRequests,
            spriteFrameTable,
            buildMonsterActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry));
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
            billboard.z = static_cast<int>(std::lround(sampleOutdoorActorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(billboard.z),
                std::max(5.0f, static_cast<float>(actor.radius)))));
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
            billboard.z = static_cast<int>(std::lround(sampleOutdoorActorPlacementFloorHeight(
                *pOutdoorMapData,
                static_cast<float>(spawn.x),
                static_cast<float>(spawn.y),
                static_cast<float>(billboard.z),
                std::max(5.0f, static_cast<float>(pMonsterEntry->radius)))));
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

        if (spawn.typeId == 3 && spawn.index >= 1 && spawn.index <= 3)
        {
            appendEncounterSlotTierTextures(
                textureRequests,
                billboardSet.spriteFrameTable,
                map,
                monsterTable,
                spawn.index);
        }
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
    bool decodeTextures = true,
    const MapLoadProgressPump &progressPump = {},
    MapAssetLoadSharedCache *pSharedCache = nullptr
)
{
    ActorPreviewBillboardSet billboardSet = {};

    std::unordered_set<std::string> neededMonsterFamilies;
    std::unordered_set<std::string> neededWorldPrefixedMonsterSpriteNames;
    collectMapDeltaMonsterSpriteFamilies(
        neededMonsterFamilies,
        neededWorldPrefixedMonsterSpriteNames,
        monsterTable,
        mapDeltaData);
    collectSpawnMonsterSpriteFamilies(
        neededMonsterFamilies,
        neededWorldPrefixedMonsterSpriteNames,
        map,
        monsterTable,
        spawns);
    collectEncounterMonsterSpriteFamilies(
        neededMonsterFamilies,
        neededWorldPrefixedMonsterSpriteNames,
        monsterTable,
        map);
    collectSummonMonsterSpriteFamilies(
        neededMonsterFamilies,
        neededWorldPrefixedMonsterSpriteNames,
        monsterTable);
    neededMonsterFamilies.insert("m271");
    neededMonsterFamilies.insert("m273");

    const std::optional<SpriteFrameTable> spriteFrameTable =
        loadSpriteFrameTable(
            assetFileSystem,
            neededMonsterFamilies,
            neededWorldPrefixedMonsterSpriteNames,
            pSharedCache);

    if (!spriteFrameTable)
    {
        return std::nullopt;
    }

    billboardSet.spriteFrameTable = *spriteFrameTable;

    std::vector<BitmapTextureRequest> textureRequests;
    appendArpgModePlayerMonsterTextures(textureRequests, billboardSet.spriteFrameTable, monsterTable);

    if (mapDeltaData)
    {
        appendMapDeltaActors(billboardSet, textureRequests, monsterTable, *mapDeltaData, pOutdoorMapData);
    }

    appendSpawnActors(billboardSet, textureRequests, map, monsterTable, spawns, pOutdoorMapData);

    if (decodeTextures)
    {
        const Engine::AssetScaleTier spriteAssetScaleTier =
            assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Sprites);

        for (const BitmapTextureRequest &textureRequest : textureRequests)
        {
            pumpMapLoadProgress(progressPump);
            OutdoorBitmapTexture texture =
                decodeActorBitmapTextureRequest(
                    assetFileSystem,
                    textureRequest,
                    spriteAssetScaleTier,
                    map.worldId,
                    bitmapLoadCache);

            if (texture.pixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
            {
                continue;
            }

            billboardSet.textures.push_back(std::move(texture));
        }
    }
    else if (!textureRequests.empty())
    {
        const Engine::AssetScaleTier spriteAssetScaleTier =
            assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Sprites);
        const std::vector<BitmapTextureRequest> asyncTextureRequests = textureRequests;
        const std::string worldId = map.worldId;
        billboardSet.texturePreloadFuture =
            std::async(
                std::launch::async,
                [&assetFileSystem, asyncTextureRequests, spriteAssetScaleTier, worldId]()
                {
                    return decodeActorBitmapTextureRequests(
                        assetFileSystem,
                        asyncTextureRequests,
                        spriteAssetScaleTier,
                        worldId);
                }).share();
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
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
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
            const bool isWaterTile =
                hasTerrainTileFlag((*tileDescriptors)[rawTileId], TerrainTileFlagWater);
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
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
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
            const std::string &textureName = (*tileDescriptors)[rawTileId].textureName;
            tileColors[static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX)] =
                colorFromTextureName(textureName);
        }
    }

    return tileColors;
}

void copyTerrainTileIntoAtlasPixels(
    std::vector<uint8_t> &atlasPixels,
    int atlasWidth,
    int atlasHeight,
    int innerAtlasX,
    int innerAtlasY,
    int tileSize,
    int tilePadding,
    const std::vector<uint8_t> &tilePixels)
{
    if (atlasWidth <= 0
        || atlasHeight <= 0
        || tileSize <= 0
        || tilePixels.size() < static_cast<size_t>(tileSize * tileSize * 4))
    {
        return;
    }

    const int cellStartX = innerAtlasX - tilePadding;
    const int cellStartY = innerAtlasY - tilePadding;
    const int paddedTileSize = tileSize + tilePadding * 2;

    for (int paddedY = 0; paddedY < paddedTileSize; ++paddedY)
    {
        const int sourceY = std::clamp(paddedY - tilePadding, 0, tileSize - 1);
        const int targetY = cellStartY + paddedY;

        if (targetY < 0 || targetY >= atlasHeight)
        {
            continue;
        }

        for (int paddedX = 0; paddedX < paddedTileSize; ++paddedX)
        {
            const int sourceX = std::clamp(paddedX - tilePadding, 0, tileSize - 1);
            const int targetX = cellStartX + paddedX;

            if (targetX < 0 || targetX >= atlasWidth)
            {
                continue;
            }

            const size_t sourceOffset = static_cast<size_t>((sourceY * tileSize + sourceX) * 4);
            const size_t targetOffset = static_cast<size_t>((targetY * atlasWidth + targetX) * 4);
            std::memcpy(
                atlasPixels.data() + static_cast<ptrdiff_t>(targetOffset),
                tilePixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                4);
        }
    }
}

std::optional<OutdoorTerrainTextureAtlas> buildOutdoorTerrainTextureAtlas(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache,
    const SurfaceMaterialTable *pSurfaceMaterialTable,
    const MapLoadProgressPump &progressPump
)
{
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
    {
        return std::nullopt;
    }

    const Engine::AssetScaleTier terrainAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Terrain);
    const int terrainTileSize = terrainTexturePhysicalTileSize(terrainAssetScaleTier);
    const int atlasTilePadding = TerrainTextureAtlasTilePadding;
    const int atlasCellSize = terrainTileSize + atlasTilePadding * 2;
    OutdoorTerrainTextureAtlas textureAtlas = {};
    textureAtlas.tileSize = terrainTileSize;
    textureAtlas.tilePadding = atlasTilePadding;
    textureAtlas.width = TerrainTextureAtlasColumns * atlasCellSize;
    textureAtlas.height = TerrainTextureAtlasColumns * atlasCellSize;
    textureAtlas.pixels.resize(static_cast<size_t>(textureAtlas.width * textureAtlas.height * 4), 0);

    std::unordered_map<std::string, std::vector<std::vector<uint8_t>>> animatedTerrainFramesByKey;
    std::unordered_set<std::string> missingTextureNames;
    std::unordered_set<std::string> invalidSizeTextureNames;
    size_t validTileCount = 0;

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        pumpMapLoadProgress(progressPump);
        const TerrainTileDescriptor &descriptor = (*tileDescriptors)[tileIndex];
        const std::string &textureName = descriptor.textureName;

        if (textureName.empty() || textureName == "pending")
        {
            continue;
        }

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> tilePixels =
            loadTerrainBitmapPixelsBgra(
                assetFileSystem,
                textureName,
                textureWidth,
                textureHeight,
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
        std::vector<uint8_t> fallbackLiquidBasePixels = resolvedTilePixels;
        std::vector<std::vector<uint8_t>> animatedSurfaceFrames;
        SurfaceAnimationSequence surfaceAnimation = staticSurfaceAnimation(textureName);
        const TerrainTileDescriptor *pBaseDescriptor = nullptr;
        const SurfaceMaterialDefinition *pSurfaceMaterial =
            findTerrainSurfaceMaterialForDescriptor(
                descriptor,
                *tileDescriptors,
                pSurfaceMaterialTable,
                &pBaseDescriptor);
        std::vector<uint8_t> transitionOverlayPixels;
        bool useTransitionOverlay = pSurfaceMaterial != nullptr
            && pSurfaceMaterial->terrainTransitionOverlay
            && isTerrainDescriptorTransition(descriptor)
            && pBaseDescriptor != nullptr
            && pBaseDescriptor->textureName != textureName;

        if (useTransitionOverlay)
        {
            int overlayTextureWidth = 0;
            int overlayTextureHeight = 0;
            const std::optional<std::vector<uint8_t>> overlayTilePixels =
                loadTerrainBitmapPixelsBgra(
                    assetFileSystem,
                    textureName,
                    overlayTextureWidth,
                    overlayTextureHeight,
                    true,
                    bitmapLoadCache
                );
            int baseTextureWidth = 0;
            int baseTextureHeight = 0;
            const std::optional<std::vector<uint8_t>> baseTilePixels =
                loadTerrainBitmapPixelsBgra(
                    assetFileSystem,
                    pBaseDescriptor->textureName,
                    baseTextureWidth,
                    baseTextureHeight,
                    false,
                    bitmapLoadCache
                );

            if (overlayTilePixels
                && overlayTextureWidth == terrainTileSize
                && overlayTextureHeight == terrainTileSize
                && baseTilePixels
                && baseTextureWidth == terrainTileSize
                && baseTextureHeight == terrainTileSize)
            {
                transitionOverlayPixels = *overlayTilePixels;
                fallbackLiquidBasePixels = *baseTilePixels;
                resolvedTilePixels = compositeTerrainOverlayOverBase(*baseTilePixels, transitionOverlayPixels);
            }
            else
            {
                useTransitionOverlay = false;
            }
        }

        if (pSurfaceMaterial != nullptr && !pSurfaceMaterial->animation.empty())
        {
            surfaceAnimation = pSurfaceMaterial->animation;
            const std::string cacheKey = pSurfaceMaterial->id
                + "|"
                + toLowerCopy(useTransitionOverlay && pBaseDescriptor != nullptr
                    ? pBaseDescriptor->textureName
                    : textureName)
                + "|"
                + (useTransitionOverlay ? toLowerCopy(textureName) : std::string());
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
                    pumpMapLoadProgress(progressPump);
                    int frameWidth = 0;
                    int frameHeight = 0;
                    const std::optional<std::vector<uint8_t>> framePixels =
                        loadTerrainBitmapPixelsBgra(
                            assetFileSystem,
                            frame.textureName,
                            frameWidth,
                            frameHeight,
                            false,
                            bitmapLoadCache
                        );

                    if (!framePixels || frameWidth != terrainTileSize || frameHeight != terrainTileSize)
                    {
                        animatedSurfaceFrames.clear();
                        break;
                    }

                    if (useTransitionOverlay)
                    {
                        animatedSurfaceFrames.push_back(
                            compositeTerrainOverlayOverBase(*framePixels, transitionOverlayPixels));
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
        else if (pSurfaceMaterial != nullptr
            && (pSurfaceMaterial->semantic == SurfaceMaterialSemantic::Water
                || pSurfaceMaterial->semantic == SurfaceMaterialSemantic::Lava))
        {
            surfaceAnimation = staticSurfaceAnimation(textureName);
            const std::string cacheKey = pSurfaceMaterial->id
                + "|fallback|"
                + toLowerCopy(useTransitionOverlay && pBaseDescriptor != nullptr
                    ? pBaseDescriptor->textureName
                    : textureName)
                + "|"
                + (useTransitionOverlay ? toLowerCopy(textureName) : std::string());
            const auto cachedFramesIt = animatedTerrainFramesByKey.find(cacheKey);

            if (cachedFramesIt != animatedTerrainFramesByKey.end())
            {
                animatedSurfaceFrames = cachedFramesIt->second;
            }
            else
            {
                animatedSurfaceFrames = buildFallbackLiquidAnimationFrames(
                    fallbackLiquidBasePixels,
                    terrainTileSize,
                    terrainTileSize,
                    surfaceAnimation);

                if (useTransitionOverlay)
                {
                    for (std::vector<uint8_t> &framePixels : animatedSurfaceFrames)
                    {
                        framePixels = compositeTerrainOverlayOverBase(framePixels, transitionOverlayPixels);
                    }
                }

                animatedTerrainFramesByKey.emplace(cacheKey, animatedSurfaceFrames);
            }

            if (!animatedSurfaceFrames.empty())
            {
                resolvedTilePixels = animatedSurfaceFrames.front();
            }
        }

        const int atlasColumn = tileIndex % TerrainTextureAtlasColumns;
        const int atlasRow = tileIndex / TerrainTextureAtlasColumns;
        const int atlasX = atlasColumn * atlasCellSize + atlasTilePadding;
        const int atlasY = atlasRow * atlasCellSize + atlasTilePadding;

        copyTerrainTileIntoAtlasPixels(
            textureAtlas.pixels,
            textureAtlas.width,
            textureAtlas.height,
            atlasX,
            atlasY,
            terrainTileSize,
            atlasTilePadding,
            resolvedTilePixels);

        OutdoorTerrainAtlasRegion region = {};
        region.u0 = static_cast<float>(atlasX) / static_cast<float>(textureAtlas.width);
        region.v0 = static_cast<float>(atlasY) / static_cast<float>(textureAtlas.height);
        region.u1 = static_cast<float>(atlasX + terrainTileSize) / static_cast<float>(textureAtlas.width);
        region.v1 = static_cast<float>(atlasY + terrainTileSize) / static_cast<float>(textureAtlas.height);
        region.isValid = true;
        region.isWater = hasTerrainTileFlag(descriptor, TerrainTileFlagWater)
            || (pSurfaceMaterial != nullptr && pSurfaceMaterial->semantic == SurfaceMaterialSemantic::Water);
        region.isTransitionOverlay = useTransitionOverlay;
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
    const SurfaceMaterialTable *pSurfaceMaterialTable,
    const MapLoadProgressPump &progressPump
)
{
    std::vector<std::string> textureNames;
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.textureName.empty())
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
    const Engine::AssetScaleTier textureAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Textures);
    const Engine::AssetScaleTier terrainAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Terrain);
    const std::unordered_set<std::string> terrainFallbackTextureNames =
        collectTerrainFallbackTextureNames(animationBindings);

    for (const std::string &textureName : textureNames)
    {
        pumpMapLoadProgress(progressPump);
        int textureWidth = 0;
        int textureHeight = 0;
        Engine::AssetScaleTier loadedAssetScaleTier = textureAssetScaleTier;
        std::optional<std::vector<uint8_t>> pixels =
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

        if ((!pixels || textureWidth <= 0 || textureHeight <= 0)
            && terrainFallbackTextureNames.find(toLowerCopy(textureName)) != terrainFallbackTextureNames.end())
        {
            pixels = loadTerrainBitmapPixelsBgra(
                assetFileSystem,
                textureName,
                textureWidth,
                textureHeight,
                false,
                bitmapLoadCache);
            loadedAssetScaleTier = terrainAssetScaleTier;
        }

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, loadedAssetScaleTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, loadedAssetScaleTier);
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
    const SurfaceMaterialTable *pSurfaceMaterialTable,
    const MapLoadProgressPump &progressPump
)
{
    std::vector<std::string> textureNames;
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;

    for (const IndoorFace &face : indoorMapData.faces)
    {
        if (face.isPortal || face.textureName.empty())
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
    const Engine::AssetScaleTier textureAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Textures);
    const Engine::AssetScaleTier terrainAssetScaleTier =
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Terrain);
    const std::unordered_set<std::string> terrainFallbackTextureNames =
        collectTerrainFallbackTextureNames(animationBindings);

    for (const std::string &textureName : textureNames)
    {
        pumpMapLoadProgress(progressPump);
        int textureWidth = 0;
        int textureHeight = 0;
        Engine::AssetScaleTier loadedAssetScaleTier = textureAssetScaleTier;
        std::optional<std::vector<uint8_t>> pixels =
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

        if ((!pixels || textureWidth <= 0 || textureHeight <= 0)
            && terrainFallbackTextureNames.find(toLowerCopy(textureName)) != terrainFallbackTextureNames.end())
        {
            pixels = loadTerrainBitmapPixelsBgra(
                assetFileSystem,
                textureName,
                textureWidth,
                textureHeight,
                false,
                bitmapLoadCache);
            loadedAssetScaleTier = terrainAssetScaleTier;
        }

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, loadedAssetScaleTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, loadedAssetScaleTier);
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

bool isSceneOverlayFileName(const std::string &entryName, const std::string &sceneFileName)
{
    const std::string lowerEntryName = toLowerCopy(entryName);
    const std::string lowerSceneFileName = toLowerCopy(sceneFileName);

    if (!lowerEntryName.ends_with(".yml") || lowerEntryName == lowerSceneFileName)
    {
        return false;
    }

    if (lowerEntryName.ends_with(".scene.yml"))
    {
        const std::string underscoreOverlayPrefix =
            lowerSceneFileName.substr(0, lowerSceneFileName.size() - 10) + "_";

        if (lowerEntryName.starts_with(underscoreOverlayPrefix))
        {
            return true;
        }
    }

    const std::string numberedOverlayPrefix = lowerSceneFileName.substr(0, lowerSceneFileName.size() - 4) + ".";
    return lowerEntryName.starts_with(numberedOverlayPrefix);
}

std::vector<std::string> buildSceneOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneFileName)
{
    std::vector<std::string> candidates;

    for (const std::string &entryName : assetFileSystem.enumerate("Data/games"))
    {
        if (isSceneOverlayFileName(entryName, sceneFileName))
        {
            candidates.push_back("Data/games/" + entryName);
        }
    }

    std::sort(candidates.begin(), candidates.end(), [](const std::string &left, const std::string &right)
    {
        return toLowerCopy(left) < toLowerCopy(right);
    });
    return candidates;
}
}

std::optional<MapAssetInfo> MapAssetLoader::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    MapLoadPurpose purpose,
    const MapCompanionLoadOptions &companionLoadOptions,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
) const
{
    BitmapLoadCache bitmapLoadCache = {};
    bitmapLoadCache.pSharedCache = pSharedCache;
    MapLoadTimingLogger timingLogger(map.fileName);
    auto logStageComplete = [&progressPump, &timingLogger](const std::string &stageName)
    {
        timingLogger.stage(stageName);
        pumpMapLoadProgress(progressPump);
    };

    const std::optional<std::string> geometryPath = findAssetPath(assetFileSystem, map.worldId, map.fileName);

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
    std::vector<std::pair<std::string, std::string>> sceneOverlays;

    const std::optional<std::string> sceneFileName =
        companionLoadOptions.allowSceneYml ? buildSceneFileName(map.fileName) : std::nullopt;

    if (sceneFileName)
    {
        const std::optional<std::string> scenePath = findAssetPath(assetFileSystem, map.worldId, *sceneFileName);

        if (scenePath)
        {
            sceneText = assetFileSystem.readTextFile(*scenePath);

            if (sceneText)
            {
                assetInfo.scenePath = scenePath;
                assetInfo.sceneSize = sceneText->size();
                logStageComplete("scene yml loaded");

                for (const std::string &overlayPath : buildSceneOverlayPathCandidates(assetFileSystem, *sceneFileName))
                {
                    const std::optional<std::string> overlayText = assetFileSystem.readTextFile(overlayPath);

                    if (!overlayText)
                    {
                        continue;
                    }

                    sceneOverlays.emplace_back(overlayPath, *overlayText);
                    *assetInfo.scenePath += " + " + overlayPath;
                    *assetInfo.sceneSize += overlayText->size();
                }
            }
        }
    }

    const std::optional<std::string> companionFileName =
        !sceneText && companionLoadOptions.allowLegacyCompanion ? buildCompanionFileName(map.fileName) : std::nullopt;

    if (companionFileName)
    {
        const std::optional<std::string> companionPath =
            findCompanionAssetPath(assetFileSystem, map.worldId, *companionFileName);

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

    const bool loadFullPresentation = purpose == MapLoadPurpose::Full || purpose == MapLoadPurpose::FullGameplay;
    const bool loadRenderSurfaces = loadFullPresentation || purpose == MapLoadPurpose::RenderSurfaces;
    const bool loadActorPreviews = loadFullPresentation
        || purpose == MapLoadPurpose::ActorPreviews
        || purpose == MapLoadPurpose::BillboardPreviews;
    const bool loadDecorationBillboards = loadFullPresentation || purpose == MapLoadPurpose::BillboardPreviews;
    const bool loadSpriteObjectBillboards = loadFullPresentation;

    std::optional<TextureFrameTable> textureFrameTable;
    std::optional<SurfaceMaterialTable> surfaceMaterialTable;

    if (loadRenderSurfaces)
    {
        textureFrameTable = loadTextureFrameTable(assetFileSystem, pSharedCache);
        logStageComplete("texture frame table loaded");
        surfaceMaterialTable = loadSurfaceMaterialTable(assetFileSystem, pSharedCache);
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
            assetInfo.outdoorMapData->worldId = map.worldId;
            assetInfo.outdoorMapData->fileName = map.fileName;

            if (sceneText)
            {
                OutdoorSceneYmlLoader sceneLoader = {};
                std::string sceneError;
                std::optional<OutdoorSceneData> sceneData = sceneLoader.loadFromText(*sceneText, sceneError);

                if (!sceneData)
                {
                    std::cerr << "Failed to parse outdoor scene yml for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                for (const std::pair<std::string, std::string> &overlay : sceneOverlays)
                {
                    if (!sceneLoader.applyOverlayFromText(*sceneData, overlay.second, sceneError))
                    {
                        std::cerr << "Failed to parse outdoor scene yml overlay for " << map.fileName
                                  << ": " << overlay.first << ": " << sceneError << '\n';
                        return std::nullopt;
                    }
                }

                if (!sceneData->geometryFile.empty()
                    && toLowerCopy(sceneData->geometryFile) != toLowerCopy(map.fileName))
                {
                    std::cerr << "Failed to build outdoor scene state for " << map.fileName
                              << ": scene geometry_file does not match loaded outdoor geometry\n";
                    return std::nullopt;
                }

                assetInfo.map.runtimeRestrictions = sceneData->runtimeRestrictions;
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
                assetInfo.outdoorWeatherProfile =
                    buildOutdoorWeatherProfile(sceneData->environment, assetInfo.outdoorMapDeltaData->locationTime);
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
                    assetInfo.outdoorWeatherProfile =
                        buildOutdoorWeatherProfile(assetInfo.outdoorMapDeltaData->locationTime);
                    assetInfo.authoredCompanionSource = AuthoredCompanionSource::LegacyCompanion;
                    logStageComplete("outdoor map delta parsed");
                }
            }

            if (!applyTerrainTileDescriptorAttributes(assetFileSystem, *assetInfo.outdoorMapData))
            {
                std::cerr << "Failed to apply outdoor terrain tile flags for " << map.fileName << '\n';
            }

            if (loadActorPreviews)
            {
                assetInfo.outdoorActorPreviewBillboardSet =
                    buildActorPreviewBillboardSet(
                        assetFileSystem,
                        map,
                        monsterTable,
                        assetInfo.outdoorMapDeltaData,
                        assetInfo.outdoorMapData->spawns,
                        bitmapLoadCache,
                        &*assetInfo.outdoorMapData,
                        purpose != MapLoadPurpose::FullGameplay,
                        progressPump,
                        pSharedCache
                    );
                logStageComplete("outdoor actor previews built");
            }

            if (loadRenderSurfaces)
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
                        surfaceMaterialTable ? &*surfaceMaterialTable : nullptr,
                        progressPump);
                logStageComplete("outdoor terrain textures built");
                assetInfo.outdoorBModelTextureSet =
                    buildOutdoorBModelTextureSet(
                        assetFileSystem,
                        *assetInfo.outdoorMapData,
                        bitmapLoadCache,
                        textureFrameTable ? &*textureFrameTable : nullptr,
                        surfaceMaterialTable ? &*surfaceMaterialTable : nullptr,
                        progressPump);
                logStageComplete("outdoor bmodel textures built");
            }

            if (loadFullPresentation)
            {
                assetInfo.outdoorDecorationCollisionSet =
                    buildOutdoorDecorationCollisionSet(
                        assetFileSystem,
                        assetInfo.outdoorMapData->entities,
                        pSharedCache);
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
            }

            if (loadDecorationBillboards)
            {
                assetInfo.outdoorDecorationBillboardSet =
                    buildOutdoorDecorationBillboardSet(
                        assetFileSystem,
                        *assetInfo.outdoorMapData,
                        bitmapLoadCache,
                        progressPump,
                        pSharedCache);
                logStageComplete("outdoor decoration billboards built");
            }

            if (loadSpriteObjectBillboards)
            {
                assetInfo.outdoorSpriteObjectBillboardSet =
                    buildSpriteObjectBillboardSet(
                        assetFileSystem,
                        objectTable,
                        assetInfo.outdoorMapDeltaData,
                        bitmapLoadCache,
                        progressPump,
                        pSharedCache
                    );
                logStageComplete("outdoor sprite objects built");
            }

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
    }
    else if (normalizedFileName.ends_with(".blv"))
    {
        const IndoorMapDataLoader indoorMapDataLoader;
        assetInfo.indoorMapData = indoorMapDataLoader.loadFromBytes(*geometryBytes);
        logStageComplete("indoor geometry parsed");

        if (assetInfo.indoorMapData)
        {
            if (sceneText)
            {
                IndoorSceneYmlLoader sceneLoader = {};
                std::string sceneError;
                std::optional<IndoorSceneData> sceneData = sceneLoader.loadFromText(*sceneText, sceneError);

                if (!sceneData)
                {
                    std::cerr << "Failed to parse indoor scene yml for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                for (const std::pair<std::string, std::string> &overlay : sceneOverlays)
                {
                    if (!sceneLoader.applyOverlayFromText(*sceneData, overlay.second, sceneError))
                    {
                        std::cerr << "Failed to parse indoor scene yml overlay for " << map.fileName
                                  << ": " << overlay.first << ": " << sceneError << '\n';
                        return std::nullopt;
                    }
                }

                if (!sceneData->geometryFile.empty()
                    && toLowerCopy(sceneData->geometryFile) != toLowerCopy(map.fileName))
                {
                    std::cerr << "Failed to build indoor scene state for " << map.fileName
                              << ": scene geometry_file does not match loaded indoor geometry\n";
                    return std::nullopt;
                }

                assetInfo.map.runtimeRestrictions = sceneData->runtimeRestrictions;
                MapDeltaData sceneMapDeltaData = {};

                if (!buildIndoorMapStateFromScene(
                        *sceneData,
                        *assetInfo.indoorMapData,
                        sceneMapDeltaData,
                        sceneError))
                {
                    std::cerr << "Failed to build indoor scene state for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                assetInfo.indoorMapDeltaData = std::move(sceneMapDeltaData);
                assetInfo.authoredCompanionSource = AuthoredCompanionSource::SceneYml;
                logStageComplete("indoor scene yml applied");
            }
            else if (companionBytes)
            {
                const MapDeltaDataLoader mapDeltaDataLoader;
                assetInfo.indoorMapDeltaData =
                    mapDeltaDataLoader.loadIndoorFromBytes(*companionBytes, *assetInfo.indoorMapData);

                if (assetInfo.indoorMapDeltaData)
                {
                    assetInfo.authoredCompanionSource = AuthoredCompanionSource::LegacyCompanion;
                    logStageComplete("indoor map delta parsed");
                }
            }

            if (loadFullPresentation)
            {
                assetInfo.indoorTextureSet = buildIndoorTextureSet(
                    assetFileSystem,
                    *assetInfo.indoorMapData,
                    bitmapLoadCache,
                    textureFrameTable ? &*textureFrameTable : nullptr,
                    surfaceMaterialTable ? &*surfaceMaterialTable : nullptr,
                    progressPump
                );
                logStageComplete("indoor textures built");
            }

            if (loadDecorationBillboards)
            {
                assetInfo.indoorDecorationBillboardSet =
                    buildIndoorDecorationBillboardSet(
                        assetFileSystem,
                        *assetInfo.indoorMapData,
                        bitmapLoadCache,
                        progressPump,
                        pSharedCache);
                logStageComplete("indoor decoration billboards built");
            }

            if (loadActorPreviews)
            {
                assetInfo.indoorActorPreviewBillboardSet =
                    buildActorPreviewBillboardSet(
                        assetFileSystem,
                        map,
                        monsterTable,
                        assetInfo.indoorMapDeltaData,
                        assetInfo.indoorMapData->spawns,
                        bitmapLoadCache,
                        nullptr,
                        true,
                        progressPump,
                        pSharedCache
                    );
                logStageComplete("indoor actor previews built");
            }

            if (loadSpriteObjectBillboards)
            {
                assetInfo.indoorSpriteObjectBillboardSet =
                    buildSpriteObjectBillboardSet(
                        assetFileSystem,
                        objectTable,
                        assetInfo.indoorMapDeltaData,
                        bitmapLoadCache,
                        progressPump,
                        pSharedCache
                    );
                logStageComplete("indoor sprite objects built");
            }

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

std::optional<std::string> MapAssetLoader::findAssetPathInDirectory(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName
)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
    const std::string normalizedFileName = toLower(fileName);

    for (const std::string &entry : entries)
    {
        if (toLower(entry) == normalizedFileName)
        {
            return directoryPath + "/" + entry;
        }
    }

    return std::nullopt;
}

std::optional<std::string> MapAssetLoader::findCompanionAssetPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    const std::string &fileName
)
{
    const std::optional<std::string> gamesPath = findAssetPath(assetFileSystem, worldId, fileName);

    if (gamesPath)
    {
        return gamesPath;
    }

    return findAssetPathInDirectory(assetFileSystem, "_legacy/map_delta", fileName);
}

std::optional<std::string> MapAssetLoader::findAssetPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    const std::string &fileName
)
{
    if (!worldId.empty())
    {
        const std::optional<std::string> worldPath =
            findAssetPathInDirectory(assetFileSystem, "worlds/" + worldId + "/maps", fileName);

        if (worldPath)
        {
            return worldPath;
        }
    }

    return findAssetPathInDirectory(assetFileSystem, "Data/games", fileName);
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

    if (extension == ".blv")
    {
        return stem + ".scene.yml";
    }

    return std::nullopt;
}
}
