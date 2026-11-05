#include "game/render/WaterCoverage.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/FaceEnums.h"
#include "game/content/WorldDecorations.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/maps/ActorModelManifest.h"
#include "game/maps/DecorationModelManifest.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/MapDecorationTextures.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/MapPresentation.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/TerrainTileData.h"
#include "game/indoor/IndoorBakedLighting.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorNavigationData.h"
#include "game/outdoor/OutdoorRenderData.h"
#include "game/render/TextureFiltering.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "game/tables/LiquidTable.h"
#include "game/tables/TextureFrameTable.h"
#include "engine/AssetScaleTier.h"
#include "engine/ImageAssetLoader.h"
#include "engine/ParallelFor.h"
#include "engine/SpriteAtlas.h"
#include "engine/TextTable.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <future>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <stdexcept>
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
bool applyActorLootOverrides(
    const MapItemSourceData &itemSources,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage)
{
    for (const MapActorLootOverride &overrideEntry : itemSources.actorLootOverrides)
    {
        const auto actorIterator = std::find_if(
            mapDeltaData.actors.begin(),
            mapDeltaData.actors.end(),
            [&overrideEntry](const MapDeltaActor &actor)
            {
                return actor.mm9SourceObjectIndex == overrideEntry.sourceObjectIndex;
            });
        if (actorIterator == mapDeltaData.actors.end())
        {
            errorMessage = "MM9 actor loot override does not resolve source object "
                + std::to_string(overrideEntry.sourceObjectIndex);
            return false;
        }
        actorIterator->proceduralDeathLoot = overrideEntry.proceduralDeathLoot;
    }
    return true;
}

double millisecondsFromNanoseconds(uint64_t nanoseconds)
{
    return static_cast<double>(nanoseconds) / 1000000.0;
}

bool mapLoadTimingEnabled()
{
    const char *pValue = std::getenv("OPENYAMM_MAP_LOAD_TIMING");
    return pValue != nullptr && std::string_view(pValue) != "0" && std::string_view(pValue) != "false";
}

void updateBitmapAlphaInfo(OutdoorBitmapTexture &texture, const std::vector<uint8_t> &pixels)
{
    for (size_t offset = 3; offset < pixels.size(); offset += 4)
    {
        const uint8_t alpha = pixels[offset];
        if (alpha < 255)
        {
            texture.hasTransparentPixels = true;
        }
        if (alpha > 0 && alpha < 255)
        {
            texture.hasPartialAlphaPixels = true;
        }
        if (texture.hasTransparentPixels && texture.hasPartialAlphaPixels)
        {
            return;
        }
    }
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

bool isMergedLegacyIndoorLight(const IndoorLight &light)
{
    return light.radius > 0
        && light.brightness > 0
        && light.id == 0
        && light.red == 0
        && light.green == 0
        && light.blue == 0;
}

bool hasMergedLegacyIndoorLightData(const IndoorMapData &mapData)
{
    if (mapData.version != 8)
    {
        return false;
    }

    bool foundLegacyLight = false;

    for (const IndoorLight &light : mapData.lights)
    {
        if (light.radius <= 0 || light.brightness <= 0)
        {
            continue;
        }

        if (light.id != 0 || light.red != 0 || light.green != 0 || light.blue != 0)
        {
            return false;
        }

        foundLegacyLight = true;
    }

    return foundLegacyLight;
}

void normalizeMergedMm6IndoorStaticLights(const MapStatsEntry &map, IndoorMapData &mapData)
{
    if (normalizeWorldId(map.worldId) != "mm6" && !hasMergedLegacyIndoorLightData(mapData))
    {
        return;
    }

    for (IndoorLight &light : mapData.lights)
    {
        if (!isMergedLegacyIndoorLight(light))
        {
            continue;
        }

        light.red = 255;
        light.green = 255;
        light.blue = 255;
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

constexpr uint32_t EnvironmentFlagRain = 0x01;
constexpr uint32_t EnvironmentFlagSnow = 0x02;
constexpr uint32_t EnvironmentFlagUnderwater = 0x04;
constexpr uint32_t EnvironmentFlagNoTerrain = 0x08;
constexpr uint32_t EnvironmentFlagAlwaysDark = 0x10;
constexpr uint32_t EnvironmentFlagAlwaysLight = 0x20;
constexpr uint32_t EnvironmentFlagAlwaysFoggy = 0x40;
constexpr uint32_t EnvironmentFlagRedFog = 0x80;
constexpr uint32_t MapWeatherFoggy = 0x01;
constexpr size_t MaxActorTexturePreloadWorkerCount = 2;
constexpr std::array<int16_t, 3> SummonWispMonsterIds = {97, 98, 99};

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
    profile.authoredDayFog = environment.weather.authoredDayFog;
    profile.authoredNightFog = environment.weather.authoredNightFog;

    if (profile.alwaysFoggy && profile.defaultFog.strongDistance <= 0)
    {
        profile.defaultFog = fallbackAlwaysFogDistances(profile.redFog, profile.underwater);
    }

    if ((locationTime.weatherFlags & MapWeatherFoggy) != 0 && locationTime.fogStrongDistance > 0)
    {
        profile.defaultFog = {locationTime.fogWeakDistance, locationTime.fogStrongDistance};
    }

    if (environment.locationType == OutdoorLocationType::Enclosed)
    {
        profile.defaultPrecipitation = OutdoorPrecipitationKind::None;
        profile.smallFogChance = 0;
        profile.averageFogChance = 0;
        profile.denseFogChance = 0;
        profile.mergedWeatherConfigured = false;
        profile.mergedWeatherEnabled = false;
        profile.weatherMap = {};
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
DecorationLookupResult resolveDecorationEntry(
    const DecorationTable &decorationTable,
    const EntityType &entity)
{
    return decorationTable.resolveMapDecoration(entity.decorationListId, entity.name);
}

// Invisible decorations (map flag or evt.SetSprite) are skipped at runtime, since an event can show them again.
bool shouldSkipDecorationCollision(const DecorationEntry &decoration)
{
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

const LiquidDefinition *findTerrainLiquidForDescriptor(
    const TerrainTileDescriptor &descriptor,
    const std::vector<TerrainTileDescriptor> &tileDescriptors,
    const LiquidTable *pLiquidTable,
    const TerrainTileDescriptor **ppBaseDescriptor)
{
    if (ppBaseDescriptor != nullptr)
    {
        *ppBaseDescriptor = nullptr;
    }

    if (pLiquidTable == nullptr)
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

    if (const LiquidDefinition *pLiquid = pLiquidTable->findMatch(descriptor.textureName, 0, true))
    {
        return pLiquid;
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

    return pLiquidTable->findMatch(pBaseDescriptor->textureName, 0, true);
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

    std::string errorMessage;

    if (!loadDecorationTableRows(assetFileSystem, rows, errorMessage))
    {
        std::cerr << "Failed to load the decoration table: " << errorMessage << '\n';
        return false;
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

// A tier sized from another tier's standing sprite (actors.yml scale_reference) needs that tier's frames too, even when
// only it is on the map (the MM7 dragon lair places ADragon B and C): the model scale reads both frame scales.
void appendScaleReferenceSpriteFamilies(
    std::unordered_set<std::string> &families,
    std::unordered_set<std::string> &worldPrefixedSpriteNames,
    const MonsterTable &monsterTable,
    const ActorModelManifest *pActorModels)
{
    if (pActorModels == nullptr)
    {
        return;
    }

    for (const auto &[descriptor, entry] : pActorModels->entries())
    {
        const YAML::Node reference = entry.node["scale_reference"];
        const MonsterEntry *pMonsterEntry = reference ? monsterTable.findByInternalName(descriptor) : nullptr;

        if (pMonsterEntry == nullptr || pMonsterEntry->spriteNames[0].empty())
        {
            continue;
        }

        const std::string &standing = pMonsterEntry->spriteNames[0];
        const std::optional<std::string> familyRoot = monsterSpriteFamilyRoot(standing);
        const bool needed = familyRoot ? families.contains(*familyRoot)
                                       : worldPrefixedSpriteNames.contains(toLowerCopy(standing));

        if (needed)
        {
            appendMonsterSpriteFamilies(
                families,
                worldPrefixedSpriteNames,
                monsterTable.findByInternalName(reference.as<std::string>()));
        }
    }
}

void collectSummonMonsterSpriteFamilies(
    std::unordered_set<std::string> &neededMonsterFamilies,
    std::unordered_set<std::string> &neededWorldPrefixedMonsterSpriteNames,
    const MonsterTable &monsterTable)
{
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

std::optional<LiquidTable> loadLiquidTable(
    const Engine::AssetFileSystem &assetFileSystem,
    MapAssetLoadSharedCache *pSharedCache)
{
    if (pSharedCache != nullptr && pSharedCache->liquidTable)
    {
        return pSharedCache->liquidTable;
    }

    constexpr const char *pPath = "engine/liquids/liquids.yml";
    const std::optional<std::string> contents = assetFileSystem.readTextFile(pPath);

    if (!contents)
    {
        std::cerr << "Failed to read liquids: " << pPath << '\n';
        return std::nullopt;
    }

    LiquidTable liquidTable = {};
    std::string errorMessage;

    if (!liquidTable.loadFromYaml(*contents, errorMessage))
    {
        std::cerr << "Failed to load liquids: " << errorMessage << '\n';
        return std::nullopt;
    }

    if (pSharedCache != nullptr)
    {
        pSharedCache->liquidTable = liquidTable;
    }

    return liquidTable;
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

// Safe on any thread.
std::optional<SpriteFrameTable> parseCommonSpriteFrameTable(const Engine::AssetFileSystem &assetFileSystem)
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

    // Engine-authored item sprites live apart from the native table, which outdoor lighting bakes depend on.
    const std::string engineItemsPath = "Data/rendering/sprite_frame_data_engine_items.yml";
    const std::optional<std::string> engineItems = assetFileSystem.readTextFile(engineItemsPath);

    if (engineItems && !spriteFrameTable.loadFromYaml(*engineItems, errorMessage, true))
    {
        std::cerr << "Failed to load engine item sprite frame data from " << engineItemsPath << ": "
                  << errorMessage << '\n';
        return std::nullopt;
    }

    std::vector<std::string> worldPackages = assetFileSystem.enumerate("worlds");
    std::sort(worldPackages.begin(), worldPackages.end());

    for (const std::string &worldPackage : worldPackages)
    {
        const std::string contributionPath =
            "worlds/" + worldPackage + "/rendering/sprite_frame_data_world_items.yml";
        const std::optional<std::string> contribution = assetFileSystem.readTextFile(contributionPath);

        if (!contribution)
        {
            continue;
        }

        if (!spriteFrameTable.loadFromYaml(*contribution, errorMessage, true))
        {
            std::cerr << "Failed to load world-item sprite frame data from "
                      << contributionPath << ": " << errorMessage << '\n';
            return std::nullopt;
        }
    }

    if (!appendWorldDecorationSpriteFrames(assetFileSystem, spriteFrameTable, errorMessage))
    {
        std::cerr << "Failed to load world decoration sprite frame data: " << errorMessage << '\n';
        return std::nullopt;
    }

    // Contact frames and attack sound delays of monster attack sprites; an attack sprite without a contact frame
    // applies its attack at the animation's end, and without a delay plays its sound as the attack starts.
    const std::string attackTimingPath = "Data/rendering/sprite_attack_timing.yml";
    const std::optional<std::string> attackTiming = assetFileSystem.readTextFile(attackTimingPath);

    if (attackTiming && !spriteFrameTable.loadAttackTimingFromYaml(*attackTiming, errorMessage))
    {
        std::cerr << "Failed to load " << attackTimingPath << ": " << errorMessage << '\n';
        return std::nullopt;
    }

    return spriteFrameTable;
}

std::optional<SpriteFrameTable> loadCommonSpriteFrameTable(
    const Engine::AssetFileSystem &assetFileSystem,
    MapAssetLoadSharedCache *pSharedCache)
{
    if (pSharedCache == nullptr)
    {
        return parseCommonSpriteFrameTable(assetFileSystem);
    }
    if (!pSharedCache->commonSpriteFrameTable)
    {
        pSharedCache->commonSpriteFrameTable = pSharedCache->commonSpriteFrameTableLoading.valid()
            ? pSharedCache->commonSpriteFrameTableLoading.get() : parseCommonSpriteFrameTable(assetFileSystem);
        pSharedCache->commonSpriteFrameTableLoading = {};
    }
    return pSharedCache->commonSpriteFrameTable;
}

bool appendMonsterSpriteFrameFamilies(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_set<std::string> &monsterFamilies,
    const std::unordered_set<std::string> &worldPrefixedMonsterSpriteNames,
    SpriteFrameTable &spriteFrameTable,
    MapAssetLoadSharedCache *pSharedCache)
{
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
            return false;
        }

        if (!spriteFrameTable.loadFromYaml(*familyContents, errorMessage, true))
        {
            std::cerr << "Failed to load monster sprite frame family " << familyRoot
                      << ": " << errorMessage << '\n';
            return false;
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
            return false;
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

    return true;
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

    if (!appendMonsterSpriteFrameFamilies(
            assetFileSystem,
            monsterFamilies,
            worldPrefixedMonsterSpriteNames,
            spriteFrameTable,
            pSharedCache))
    {
        return std::nullopt;
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

// An animated indoor face whose texture name is no frame table sequence falls back to the sequence index stored at
// face +0x3A. Haunted Mansion (7d37) face 1844 keeps the leftover water name hdwtr010 over the cleric portrait
// sequence 13. A stored sequence that is itself a liquid stays with the liquid shader.
std::optional<SurfaceAnimationSequence> resolveStoredFaceAnimation(
    const std::string &textureName,
    uint32_t faceAttributes,
    int16_t textureFrameTableIndex,
    const TextureFrameTable *pTextureFrameTable,
    const LiquidTable *pLiquidTable)
{
    if (pTextureFrameTable == nullptr
        || !hasFaceAttribute(faceAttributes, FaceAttribute::Animated)
        || textureFrameTableIndex <= 0
        || pTextureFrameTable->findAnimationSequenceByName(textureName))
    {
        return std::nullopt;
    }

    std::optional<SurfaceAnimationSequence> animation =
        pTextureFrameTable->findAnimationSequenceByIndex(static_cast<size_t>(textureFrameTableIndex));

    if (!animation || animation->frames.empty()
        || (pLiquidTable != nullptr
            && pLiquidTable->findMatch(animation->frames.front().textureName, faceAttributes, false) != nullptr))
    {
        return std::nullopt;
    }

    return animation;
}

SurfaceAnimationSequence resolveSurfaceAnimation(
    const std::string &textureName,
    uint32_t faceAttributes,
    bool isTerrain,
    const TextureFrameTable *pTextureFrameTable,
    const LiquidTable *pLiquidTable)
{
    // Liquids are drawn by the liquid shader: their legacy frame animations are never loaded.
    if (pLiquidTable != nullptr && pLiquidTable->findMatch(textureName, faceAttributes, isTerrain) != nullptr)
    {
        return staticSurfaceAnimation(textureName);
    }

    if (!isTerrain && pTextureFrameTable != nullptr)
    {
        if (const std::optional<SurfaceAnimationSequence> animation =
                pTextureFrameTable->findAnimationSequenceByName(textureName))
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

void appendMm9BarrelLiquidTextureNames(
    std::vector<std::string> &textureNames,
    const MapItemSourceData *pItemSourceData)
{
    if (pItemSourceData == nullptr)
    {
        return;
    }

    for (const MapMm9BarrelSource &barrel : pItemSourceData->mm9Barrels)
    {
        for (const std::string &textureAlias : barrel.liquidTextureAliases)
        {
            appendTextureNameIfMissing(textureNames, toLowerCopy(textureAlias));
        }
    }
}

struct BitmapTextureRequest
{
    std::string textureName;
    int16_t paletteId = 0;
};

void appendSpriteFrameTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    uint16_t spriteFrameIndex);

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
    bool retainBinaryFiles = true;
    bool retainDecodedPixels = true;
    // Face textures read their surface material maps (MapCompanionLoadOptions::surfaceMaterials).
    bool surfaceMaterials = false;
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
    if (textureName.empty())
    {
        return;
    }

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

// The cooked file a world surface texture resolves to in the active scale tier; empty when its best match is a source
// image. Uses the load's path caches, so it runs on the loading thread.
std::optional<std::string> findCookedSurfaceTexturePath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    Engine::DirectoryAssetPathCache &directoryAssetPathsByPath,
    Engine::AssetPathLookupCache &assetPathByKey)
{
    const std::optional<std::string> path = Engine::findCookedOrImageAssetPath(
        assetFileSystem, "Data/bitmaps", textureName, directoryAssetPathsByPath, assetPathByKey);
    if (!path || toLowerCopy(std::filesystem::path(*path).extension().string()) != ".oytex")
    {
        return std::nullopt;
    }
    return path;
}

// A cooked world surface texture from its file's bytes; safe on any thread.
OutdoorBitmapTexture decodeCookedSurfaceTexture(
    const std::string &textureName,
    const std::string &path,
    const std::optional<std::vector<uint8_t>> &bytes)
{
    if (!bytes || bytes->empty())
    {
        throw std::runtime_error("Cannot read cooked surface texture " + path);
    }

    std::shared_ptr<Engine::CookedTexture> cooked;
    try
    {
        cooked = std::make_shared<Engine::CookedTexture>(Engine::decodeCookedTexture(*bytes));
    }
    catch (const std::exception &exception)
    {
        throw std::runtime_error("Cannot load cooked surface texture " + path + ": " + exception.what());
    }
    // The BModel upload path: raw (non-sRGB) texels, box-filtered mips without cutout coverage, the full chain.
    if (cooked->semantic != Engine::ImageMipSemantic::Linear || cooked->alphaCutoff != 0
        || cooked->levels != Engine::cookedTextureFullChainLevels(cooked->width, cooked->height)
        || !cooked->statistics)
    {
        throw std::runtime_error("Cooked surface texture " + path
            + " was prepared for another use or before source statistics; run tools/cook_surface_textures.py");
    }

    const Engine::AssetScaleTier tier = Engine::assetScaleTierFromResolvedPath(path);
    OutdoorBitmapTexture texture = {};
    texture.textureName = textureName;
    texture.physicalWidth = cooked->width;
    texture.physicalHeight = cooked->height;
    texture.width = Engine::scalePhysicalPixelsToLogical(cooked->width, tier);
    texture.height = Engine::scalePhysicalPixelsToLogical(cooked->height, tier);
    texture.hasTransparentPixels = cooked->statistics->alphaUse != Engine::CookedTextureAlphaUse::Opaque;
    texture.hasPartialAlphaPixels = cooked->statistics->alphaUse == Engine::CookedTextureAlphaUse::Partial;
    texture.cookedTexture = std::move(cooked);
    return texture;
}

// A cooked surface material map beside a surface texture, or null when the texture has none: the colour texture's size
// halved (tools/surface_materials.py MAP_REDUCTION) with the full mip chain below it. The maps share its texture
// coordinates, and every texture of one size its arrays.
std::shared_ptr<const Engine::CookedTexture> decodeSurfaceMaterialMap(const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path, const Engine::CookedTexture &color)
{
    const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(path);
    if (!bytes)
    {
        return nullptr;
    }
    std::shared_ptr<Engine::CookedTexture> map;
    try
    {
        map = std::make_shared<Engine::CookedTexture>(Engine::decodeCookedTexture(*bytes));
    }
    catch (const std::exception &exception)
    {
        throw std::runtime_error("Cannot load surface material map " + path + ": " + exception.what());
    }
    if (map->semantic != Engine::ImageMipSemantic::Linear || map->width * 2 != color.width
        || map->height * 2 != color.height
        || map->levels != Engine::cookedTextureFullChainLevels(map->width, map->height))
    {
        throw std::runtime_error("Surface material map " + path
            + " does not match its texture's size or mips; run tools/cook_surface_textures.py");
    }
    return map;
}

// The surface material maps of a cooked surface texture (tools/surface_materials.py): <stem>_n.oytex and
// <stem>_d.oytex in the surface_materials folder of the same scale tier beside its textures folder. Safe on any
// thread.
void loadSurfaceMaterialMaps(const Engine::AssetFileSystem &assetFileSystem, const std::string &texturePath,
    OutdoorBitmapTexture &texture)
{
    const std::filesystem::path path(texturePath);
    const std::string folder = path.parent_path().filename().string();
    if (!folder.starts_with("textures") || texture.cookedTexture == nullptr)
    {
        return;
    }
    const std::string materialFolder =
        (path.parent_path().parent_path() / ("surface_materials" + folder.substr(8))).generic_string();
    const std::string stem = path.stem().string();
    texture.materialNormal =
        decodeSurfaceMaterialMap(assetFileSystem, materialFolder + "/" + stem + "_n.oytex", *texture.cookedTexture);
    texture.materialDetail =
        decodeSurfaceMaterialMap(assetFileSystem, materialFolder + "/" + stem + "_d.oytex", *texture.cookedTexture);
    if ((texture.materialNormal == nullptr) != (texture.materialDetail == nullptr))
    {
        throw std::runtime_error("Surface texture " + texturePath
            + " has only one of its two material maps; run tools/cook_surface_textures.py");
    }
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    bool applyTransparencyKey,
    BitmapLoadCache &bitmapLoadCache,
    int16_t paletteId = 0,
    const std::string &paletteWorldId = {},
    Engine::AssetScaleTier *pLoadedTier = nullptr
)
{
    const std::string cacheKey =
        directoryPath + "|" + toLowerCopy(textureName)
        + "|" + std::to_string(applyTransparencyKey ? 1 : 0)
        + "|" + std::to_string(static_cast<int>(paletteId))
        + "|" + (paletteWorldId.empty() ? std::string() : normalizeWorldId(paletteWorldId));
    std::unordered_map<std::string, std::optional<MapAssetBitmapPixelsResult>> *pPixelCache =
        bitmapLoadCache.retainDecodedPixels ? &bitmapPixelsByKey(bitmapLoadCache) : nullptr;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> &binaryFileCache =
        bitmapBinaryFilesByPath(bitmapLoadCache);

    if (bitmapLoadCache.pSharedCache != nullptr)
    {
        bitmapLoadCache.pSharedCache->touchBitmap(cacheKey);
    }
    if (pPixelCache != nullptr)
    {
        const auto cachedPixelsIt = pPixelCache->find(cacheKey);

        if (cachedPixelsIt != pPixelCache->end())
        {
            if (!cachedPixelsIt->second)
            {
                return std::nullopt;
            }

            width = cachedPixelsIt->second->width;
            height = cachedPixelsIt->second->height;
            if (pLoadedTier != nullptr)
            {
                *pLoadedTier = cachedPixelsIt->second->assetScaleTier;
            }
            return cachedPixelsIt->second->pixels;
        }
    }

    const std::optional<std::string> bitmapPath =
        findBitmapPath(assetFileSystem, directoryPath, textureName, bitmapLoadCache);

    if (!bitmapPath)
    {
        if (pPixelCache != nullptr)
        {
            (*pPixelCache)[cacheKey] = std::nullopt;
        }

        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> uncachedBitmapBytes;
    const std::vector<uint8_t> *pBitmapBytes = nullptr;

    if (bitmapLoadCache.retainBinaryFiles)
    {
        auto cachedFileIt = binaryFileCache.find(*bitmapPath);

        if (cachedFileIt == binaryFileCache.end())
        {
            std::optional<std::vector<uint8_t>> loadedBitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);
            cachedFileIt = binaryFileCache.emplace(*bitmapPath, std::move(loadedBitmapBytes)).first;
        }

        if (cachedFileIt->second)
        {
            pBitmapBytes = &*cachedFileIt->second;
        }
    }
    else
    {
        uncachedBitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);

        if (uncachedBitmapBytes)
        {
            pBitmapBytes = &*uncachedBitmapBytes;
        }
    }

    if (pBitmapBytes == nullptr || pBitmapBytes->empty())
    {
        if (pPixelCache != nullptr)
        {
            (*pPixelCache)[cacheKey] = std::nullopt;
        }

        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = paletteId > 0
        ? loadActPalette(assetFileSystem, paletteId, bitmapLoadCache, paletteWorldId)
        : std::nullopt;
    decodeOptions.applyPaletteZeroTransparencyKey = applyTransparencyKey;
    const bool isSpriteTexture = directoryPath == "Data/sprites";
    decodeOptions.applyMagentaTransparencyKey = !isSpriteTexture;
    decodeOptions.applyTealTransparencyKey = applyTransparencyKey && !isSpriteTexture;

    std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*pBitmapBytes, *bitmapPath, decodeOptions);

    if (!image)
    {
        if (pPixelCache != nullptr)
        {
            (*pPixelCache)[cacheKey] = std::nullopt;
        }

        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    std::vector<uint8_t> pixels = std::move(image->pixels);
    const Engine::AssetScaleTier loadedTier = Engine::assetScaleTierFromResolvedPath(*bitmapPath);
    if (pLoadedTier != nullptr)
    {
        *pLoadedTier = loadedTier;
    }

    if (pPixelCache != nullptr)
    {
        (*pPixelCache)[cacheKey] = MapAssetBitmapPixelsResult{width, height, pixels, loadedTier};
    }

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

void prepareBillboardTextureForUpload(OutdoorBitmapTexture &texture)
{
    if (texture.pixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
    {
        return;
    }

    prepareBgraTexturePixelsForUploadInPlace(
        static_cast<uint16_t>(texture.physicalWidth),
        static_cast<uint16_t>(texture.physicalHeight),
        texture.pixels,
        TextureFilterProfile::Billboard);
    texture.pixelsPreparedForUpload = true;
}

void prepareBillboardTexturesForUploadParallel(std::vector<OutdoorBitmapTexture> &textures)
{
    const size_t workerCount = actorTexturePreloadWorkerCount(textures.size());

    if (workerCount <= 1)
    {
        for (OutdoorBitmapTexture &texture : textures)
        {
            prepareBillboardTextureForUpload(texture);
        }

        return;
    }

    std::vector<std::future<void>> futures;
    futures.reserve(workerCount);

    for (size_t workerIndex = 0; workerIndex < workerCount; ++workerIndex)
    {
        futures.push_back(std::async(
            std::launch::async,
            [&textures, workerIndex, workerCount]()
            {
                for (size_t textureIndex = workerIndex; textureIndex < textures.size(); textureIndex += workerCount)
                {
                    prepareBillboardTextureForUpload(textures[textureIndex]);
                }
            }));
    }

    for (std::future<void> &future : futures)
    {
        future.get();
    }
}

OutdoorBitmapTexture decodeActorBitmapTextureRequest(
    const Engine::AssetFileSystem &assetFileSystem,
    const BitmapTextureRequest &textureRequest,
    const std::string &worldId,
    BitmapLoadCache &bitmapLoadCache)
{
    int textureWidth = 0;
    int textureHeight = 0;
    std::optional<std::vector<uint8_t>> pixels =
        loadBitmapPixelsBgra(
            assetFileSystem,
            "Data/sprites",
            textureRequest.textureName,
            textureWidth,
            textureHeight,
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
    texture.width = textureWidth;
    texture.height = textureHeight;
    texture.physicalWidth = textureWidth;
    texture.physicalHeight = textureHeight;
    updateBitmapAlphaInfo(texture, *pixels);
    texture.pixels = std::move(*pixels);
    prepareBillboardTextureForUpload(texture);
    return texture;
}

template <typename EntityType>
std::optional<DecorationBillboardSet> buildDecorationBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<EntityType> &entities,
    const std::string &worldId,
    const std::string &mapFile,
    const std::vector<OutdoorBitmapTexture> &decorationTextures,
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

    // A broken manifest leaves every sprite loaded; DecorationModelSet::load reports it and draws the sprites.
    std::vector<std::string> modelledNames;
    std::string modelError;
    if (modelledDecorationNames(assetFileSystem, worldId, mapFile, modelledNames, modelError))
    {
        for (const std::string &name : modelledNames)
        {
            const DecorationEntry *pModelled = billboardSet.decorationTable.findByInternalName(name);
            if (pModelled != nullptr && pModelled->spriteId != 0)
            {
                billboardSet.modelSpriteIds.insert(pModelled->spriteId);
            }
        }
    }

    std::vector<BitmapTextureRequest> textureRequests;

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const EntityType &entity = entities[entityIndex];
        const DecorationLookupResult decoration = resolveDecorationEntry(billboardSet.decorationTable, entity);
        const DecorationEntry *pDecoration = decoration.pEntry;

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
        billboard.decorationId = decoration.decorationId;
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

        if (pDecoration->spriteId != 0 && !billboardSet.modelSpriteIds.contains(pDecoration->spriteId))
        {
            appendSpriteFrameTextures(
                textureRequests,
                billboardSet.spriteFrameTable,
                pDecoration->spriteId);
        }
        if (entity.scriptEventId() == 0)
        {
            const DecorationEntry *counterpart =
                toggleableDecorationCounterpart(billboardSet.decorationTable, *pDecoration);
            if (counterpart != nullptr && !billboardSet.modelSpriteIds.contains(counterpart->spriteId))
            {
                appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, counterpart->spriteId);
            }
        }
    }

    if (billboardSet.billboards.empty())
    {
        return std::nullopt;
    }

    // Include scripted alternate states even when they have no initial map placement.
    billboardSet.textures = decorationTextures;

    for (const BitmapTextureRequest &textureRequest : textureRequests)
    {
        if (std::any_of(decorationTextures.begin(), decorationTextures.end(),
            [&textureRequest](const OutdoorBitmapTexture &texture)
            {
                return texture.textureName == textureRequest.textureName
                    && texture.paletteId == textureRequest.paletteId;
            }))
        {
            continue;
        }
        pumpMapLoadProgress(progressPump);
        int textureWidth = 0;
        int textureHeight = 0;
        std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/sprites",
                textureRequest.textureName,
                textureWidth,
                textureHeight,
                true,
                bitmapLoadCache,
                textureRequest.paletteId,
                worldId
            );

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureRequest.textureName;
        texture.paletteId = textureRequest.paletteId;
        texture.width = textureWidth;
        texture.height = textureHeight;
        texture.physicalWidth = textureWidth;
        texture.physicalHeight = textureHeight;
        updateBitmapAlphaInfo(texture, *pixels);
        texture.pixels = std::move(*pixels);
        billboardSet.textures.push_back(std::move(texture));
    }

    prepareBillboardTexturesForUploadParallel(billboardSet.textures);

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
    collisionSet.clearRules = decorationClearRules(std::span<const EntityType>(entities), decorationTable);

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const EntityType &entity = entities[entityIndex];
        const DecorationLookupResult decoration = resolveDecorationEntry(decorationTable, entity);
        const DecorationEntry *pDecoration = decoration.pEntry;

        if (pDecoration == nullptr)
        {
            continue;
        }

        if (shouldSkipDecorationCollision(*pDecoration))
        {
            continue;
        }

        OutdoorDecorationCollision collision = {};
        collision.entityIndex = entityIndex;
        collision.decorationId = decoration.decorationId;
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
    const std::string &worldId,
    const std::string &mapFile,
    const std::vector<OutdoorBitmapTexture> &decorationTextures,
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    std::optional<DecorationBillboardSet> billboardSet =
        buildDecorationBillboardSet(
            assetFileSystem,
            outdoorMapData.entities,
            worldId,
            mapFile,
            decorationTextures,
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
    const std::string &worldId,
    const std::string &mapFile,
    const std::vector<OutdoorBitmapTexture> &decorationTextures,
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    std::optional<DecorationBillboardSet> billboardSet =
        buildDecorationBillboardSet(
            assetFileSystem,
            indoorMapData.entities,
            worldId,
            mapFile,
            decorationTextures,
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

    resolveDuplicateTorchLights(indoorMapData, *billboardSet);
    return billboardSet;
}

void appendSpriteFrameTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    const SpriteFrameTable &spriteFrameTable,
    uint16_t spriteFrameIndex);

std::optional<SpriteObjectBillboardSet> buildSpriteObjectBillboardSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const ObjectTable &objectTable,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::string &worldId,
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache
)
{
    SpriteObjectBillboardSet billboardSet = {};

    const std::optional<SpriteFrameTable> spriteFrameTable =
        loadSpriteFrameTable(assetFileSystem, {}, {}, pSharedCache);

    if (!spriteFrameTable)
    {
        return std::nullopt;
    }

    billboardSet.spriteFrameTable = *spriteFrameTable;

    // Only placed objects that draw a sprite need one. Items on the ground are models and spell missiles and impacts
    // are models and effects, so nothing is preloaded for objects the map might spawn later.
    std::vector<BitmapTextureRequest> textureRequests;

    if (mapDeltaData)
    {
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

            appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, pObjectEntry->spriteId);

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
        }
    }

    for (const BitmapTextureRequest &textureRequest : textureRequests)
    {
        pumpMapLoadProgress(progressPump);
        OutdoorBitmapTexture texture =
            decodeActorBitmapTextureRequest(
                assetFileSystem,
                textureRequest,
                worldId,
                bitmapLoadCache);

        if (texture.pixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
        {
            continue;
        }

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
            [&resolvedTexture, pFrame](const OutdoorBitmapTexture &texture)
            {
                return texture.textureName == resolvedTexture.textureName && texture.paletteId == pFrame->paletteId;
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

void noteModelDescriptor(ActorPreviewBillboardSet &billboardSet, const MonsterEntry &monster)
{
    if (std::find(billboardSet.modelDescriptors.begin(), billboardSet.modelDescriptors.end(), monster.internalName)
        == billboardSet.modelDescriptors.end())
    {
        billboardSet.modelDescriptors.push_back(monster.internalName);
    }
}

// The A, B and C tiers of a map encounter slot (MapStats monsters 1-3), as spawn points and SummonMonsters use them.
std::vector<const MonsterEntry *> encounterSlotTierMonsters(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    int encounterSlot)
{
    std::vector<const MonsterEntry *> monsters;
    const MapEncounterInfo *pEncounter = mapEncounterInfoBySlot(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return monsters;
    }

    const std::string pictureBase =
        trimAsciiWhitespace(pEncounter->pictureName.empty() ? pEncounter->monsterName : pEncounter->pictureName);

    if (pictureBase.empty())
    {
        return monsters;
    }

    for (char tierLetter : {'A', 'B', 'C'})
    {
        const std::string pictureName = pictureBase + " " + std::string(1, tierLetter);
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsByPictureName(pictureName);
        const MonsterEntry *pMonsterEntry =
            pStats != nullptr ? monsterTable.findById(static_cast<int16_t>(pStats->id)) : nullptr;

        if (pMonsterEntry != nullptr)
        {
            monsters.push_back(pMonsterEntry);
        }
    }

    return monsters;
}

// Monsters that can appear later without being placed. Every encounter slot of the map, which its event scripts may
// summon (SummonMonsters) even when no spawn point uses it, has its models built with the map so a summon does not
// stall gameplay. Wisps are summoned rarely: only their sprites are preloaded, a wisp model loads when first summoned.
void appendSummonableMonsters(
    std::vector<BitmapTextureRequest> &textureRequests,
    ActorPreviewBillboardSet &billboardSet,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable)
{
    for (int encounterSlot = 1; encounterSlot <= 3; ++encounterSlot)
    {
        for (const MonsterEntry *pMonsterEntry : encounterSlotTierMonsters(map, monsterTable, encounterSlot))
        {
            if (billboardSet.drawsModel(pMonsterEntry))
            {
                noteModelDescriptor(billboardSet, *pMonsterEntry);
            }
        }
    }

    for (int16_t monsterId : SummonWispMonsterIds)
    {
        const MonsterEntry *pMonsterEntry = monsterTable.findById(monsterId);

        if (billboardSet.drawsModel(pMonsterEntry))
        {
            continue;
        }

        appendMonsterActionTextures(
            textureRequests,
            billboardSet.spriteFrameTable,
            buildMonsterActionSpriteFrameIndices(billboardSet.spriteFrameTable, pMonsterEntry));
    }
}

void appendEncounterSlotTierTextures(
    std::vector<BitmapTextureRequest> &textureRequests,
    ActorPreviewBillboardSet &billboardSet,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    int encounterSlot)
{
    for (const MonsterEntry *pMonsterEntry : encounterSlotTierMonsters(map, monsterTable, encounterSlot))
    {
        if (billboardSet.drawsModel(pMonsterEntry))
        {
            noteModelDescriptor(billboardSet, *pMonsterEntry);
            continue;
        }

        appendMonsterActionTextures(
            textureRequests,
            billboardSet.spriteFrameTable,
            buildMonsterActionSpriteFrameIndices(billboardSet.spriteFrameTable, pMonsterEntry));
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
        billboard.modelled = billboardSet.drawsModel(pMonsterEntry);
        billboard.source = ActorPreviewSource::Companion;
        billboard.actorName = resolvedActorName;
        billboardSet.billboards.push_back(std::move(billboard));
        ++billboardSet.mapDeltaActorCount;

        if (billboardSet.billboards.back().modelled)
        {
            noteModelDescriptor(billboardSet, *pMonsterEntry);
            continue;
        }

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
        billboard.modelled = billboardSet.drawsModel(pMonsterEntry);
        billboard.source = ActorPreviewSource::Spawn;
        billboard.actorName = *monsterName;
        billboardSet.billboards.push_back(std::move(billboard));
        ++billboardSet.spawnActorCount;

        if (billboardSet.billboards.back().modelled)
        {
            noteModelDescriptor(billboardSet, *pMonsterEntry);
        }
        else
        {
            appendMonsterActionTextures(textureRequests, billboardSet.spriteFrameTable, actionSpriteFrameIndices);
            appendSpriteFrameTextures(textureRequests, billboardSet.spriteFrameTable, *frameIndex);
        }

        if (spawn.typeId == 3 && spawn.index >= 1 && spawn.index <= 3)
        {
            appendEncounterSlotTierTextures(
                textureRequests,
                billboardSet,
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
    bool decodeAllTextures = true,
    const MapLoadProgressPump &progressPump = {},
    MapAssetLoadSharedCache *pSharedCache = nullptr,
    std::shared_ptr<const ActorModelManifest> pActorModels = {}
)
{
    ActorPreviewBillboardSet billboardSet = {};
    billboardSet.actorModels = std::move(pActorModels);

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

    if (map.arena)
    {
        // The Arena starts empty. Its possible opponents still need animation definitions before spawning.
        // Texture pixels remain loaded on demand for the actual challenge.
        for (int id = map.arena->minimumMonsterId; id <= map.arena->maximumMonsterId; ++id)
        {
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(id));
            if (pStats != nullptr && !pStats->hasKind(MonsterKind::NoArena))
            {
                appendMonsterSpriteFamilies(neededMonsterFamilies, neededWorldPrefixedMonsterSpriteNames,
                    monsterTable.findById(int16_t(id)));
            }
        }
    }

    appendScaleReferenceSpriteFamilies(
        neededMonsterFamilies,
        neededWorldPrefixedMonsterSpriteNames,
        monsterTable,
        billboardSet.actorModels.get());

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

    if (mapDeltaData)
    {
        appendMapDeltaActors(billboardSet, textureRequests, monsterTable, *mapDeltaData, pOutdoorMapData);
    }

    appendSpawnActors(billboardSet, textureRequests, map, monsterTable, spawns, pOutdoorMapData);
    appendSummonableMonsters(textureRequests, billboardSet, map, monsterTable);

    // A map without placed actors keeps the set while its encounter monsters (models now, no sprites) can be summoned:
    // their models build with the map and their tier scales read its sprite-frame table.
    if (billboardSet.billboards.empty() && textureRequests.empty() && billboardSet.modelDescriptors.empty()
        && !map.arena)
    {
        return std::nullopt;
    }

    if (decodeAllTextures)
    {
        for (const BitmapTextureRequest &textureRequest : textureRequests)
        {
            pumpMapLoadProgress(progressPump);
            if (Engine::parseSpriteAtlasReference(textureRequest.textureName))
            {
                // Cooked atlases are validated/uploaded by the shared GPU cache, not the bitmap preview loader.
                continue;
            }
            OutdoorBitmapTexture texture =
                decodeActorBitmapTextureRequest(
                    assetFileSystem,
                    textureRequest,
                    map.worldId,
                    bitmapLoadCache);

            if (texture.pixels.empty() || texture.physicalWidth <= 0 || texture.physicalHeight <= 0)
            {
                continue;
            }

            billboardSet.textures.push_back(std::move(texture));
        }
    }

    for (const ActorPreviewBillboard &billboard : billboardSet.billboards)
    {
        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(billboard.spriteFrameIndex, 0);

        if (billboard.modelled)
        {
            ++billboardSet.texturedActorCount;
            continue;
        }

        if (pFrame == nullptr)
        {
            ++billboardSet.missingTextureActorCount;
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        if (!decodeAllTextures || Engine::parseSpriteAtlasReference(resolvedTexture.textureName))
        {
            ++billboardSet.texturedActorCount;
        }
        else
        {
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

// Per raw tile id: whether the tile is a shallow liquid (liquids.yml depth: shallow), waded through rather than deep
// water. All false when the world has no shallow liquid.
std::array<bool, 256> shallowLiquidTiles(
    const std::vector<TerrainTileDescriptor> &tileDescriptors,
    const LiquidTable *pLiquidTable)
{
    std::array<bool, 256> shallow = {};

    if (pLiquidTable == nullptr || !pLiquidTable->hasShallowLiquids())
    {
        return shallow;
    }

    for (size_t tileIndex = 0; tileIndex < shallow.size() && tileIndex < tileDescriptors.size(); ++tileIndex)
    {
        const LiquidDefinition *pLiquid =
            findTerrainLiquidForDescriptor(tileDescriptors[tileIndex], tileDescriptors, pLiquidTable, nullptr);
        shallow[tileIndex] = pLiquid != nullptr && pLiquid->shallow;
    }

    return shallow;
}

// A shallow liquid's cells are never deep water: the party wades through them instead of drowning.
void applyShallowLiquidTerrainAttributes(
    const Engine::AssetFileSystem &assetFileSystem,
    OutdoorMapData &outdoorMapData,
    const LiquidTable *pLiquidTable)
{
    if (pLiquidTable == nullptr || !pLiquidTable->hasShallowLiquids())
    {
        return;
    }

    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
    {
        return;
    }

    const std::array<bool, 256> shallow = shallowLiquidTiles(*tileDescriptors, pLiquidTable);
    const size_t cellCount = std::min(outdoorMapData.attributeMap.size(), outdoorMapData.tileMap.size());

    for (size_t cellIndex = 0; cellIndex < cellCount; ++cellIndex)
    {
        if (shallow[outdoorMapData.tileMap[cellIndex]])
        {
            outdoorMapData.attributeMap[cellIndex] =
                static_cast<uint8_t>(outdoorMapData.attributeMap[cellIndex] & ~TerrainTileFlagWater);
        }
    }
}

std::optional<std::vector<uint8_t>> buildOutdoorLandMask(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    const LiquidTable *pLiquidTable
)
{
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
    {
        return std::nullopt;
    }

    const std::array<bool, 256> shallow = shallowLiquidTiles(*tileDescriptors, pLiquidTable);

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
                hasTerrainTileFlag((*tileDescriptors)[rawTileId], TerrainTileFlagWater) && !shallow[rawTileId];
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

// The map's terrain tile table: each used tile's name and its part in the liquids, and the coverage masks of its
// liquid edge tiles (cooked by tools/terrain_materials.py from the native tiles; the runtime loads no tile art).
std::optional<OutdoorTerrainTiles> buildOutdoorTerrainTiles(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    const LiquidTable *pLiquidTable
)
{
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
    {
        return std::nullopt;
    }

    // Only the tile ids the map's cells use: a tileset's other slots are never drawn.
    std::array<bool, 256> usedTileIds = {};
    for (const uint8_t tileId : outdoorMapData.tileMap)
    {
        usedTileIds[tileId] = true;
    }

    OutdoorTerrainTiles terrainTiles;
    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const TerrainTileDescriptor &descriptor = (*tileDescriptors)[tileIndex];
        const std::string &textureName = descriptor.textureName;

        if (!usedTileIds[tileIndex] || textureName.empty() || textureName == "pending")
        {
            continue;
        }

        const TerrainTileDescriptor *pBaseDescriptor = nullptr;
        const LiquidDefinition *pLiquid =
            findTerrainLiquidForDescriptor(descriptor, *tileDescriptors, pLiquidTable, &pBaseDescriptor);
        // An edge tile over a liquid keeps its overlay's alpha as the liquid's coverage; a liquid tile has no art.
        const bool liquidEdge = pLiquid != nullptr
            && pLiquid->terrainTransitionOverlay
            && isTerrainDescriptorTransition(descriptor)
            && pBaseDescriptor != nullptr
            && pBaseDescriptor->textureName != textureName;
        OutdoorTerrainTile &tile = terrainTiles.tiles[size_t(tileIndex)];
        tile.textureName = textureName;
        tile.valid = true;
        tile.water = hasTerrainTileFlag(descriptor, TerrainTileFlagWater) || pLiquid != nullptr;
        tile.waterSurface = pLiquid != nullptr;
        tile.transitionOverlay = liquidEdge;
        tile.liquid = pLiquid != nullptr ? pLiquid->kind : LiquidKind::None;
        tile.waterColorAbgr = pLiquid != nullptr ? pLiquid->colorAbgr : 0;
        tile.liquidReflects = pLiquid == nullptr || pLiquid->reflects;

        if (liquidEdge)
        {
            const std::string maskPath =
                "worlds/" + outdoorMapData.worldId + "/terrain_materials/liquid_edges/" + textureName + ".png";
            const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(maskPath);
            const std::optional<Engine::ImagePixelsBgra> mask =
                bytes ? Engine::decodeImagePixelsBgra(*bytes, maskPath) : std::nullopt;

            if (!mask || mask->width != WaterCoverageSize || mask->height != WaterCoverageSize)
            {
                std::cerr << "Terrain liquid edge mask missing or not " << WaterCoverageSize << "x"
                          << WaterCoverageSize << ": " << maskPath << " (tools/terrain_materials.py edges --world "
                          << outdoorMapData.worldId << ")\n";
                return std::nullopt;
            }

            std::vector<uint8_t> &coverage = terrainTiles.liquidCoverageMasks[size_t(tileIndex)];
            coverage.resize(size_t(WaterCoverageSize) * WaterCoverageSize);
            for (size_t texel = 0; texel < coverage.size(); ++texel)
            {
                coverage[texel] = mask->pixels[texel * 4 + 2];
            }
        }
    }

    return terrainTiles;
}

// A liquid face texture has no art: the liquid shader draws it. Native liquid textures are 128 texels square, which
// keeps the face UVs (and so the flow speed of flowing liquids) as authored.
OutdoorBitmapTexture liquidFaceTexture(const std::string &textureName, const LiquidDefinition &liquid)
{
    constexpr int LiquidTextureSize = 128;
    constexpr int PlaceholderSize = 4;
    OutdoorBitmapTexture texture = {};
    texture.textureName = textureName;
    texture.width = LiquidTextureSize;
    texture.height = LiquidTextureSize;
    texture.physicalWidth = PlaceholderSize;
    texture.physicalHeight = PlaceholderSize;
    texture.liquid = liquid.kind;
    texture.waterColorAbgr = liquidFaceColorAbgr(liquid);
    const std::array<uint8_t, 4> bgra = {
        uint8_t(liquid.colorAbgr >> 16), uint8_t(liquid.colorAbgr >> 8), uint8_t(liquid.colorAbgr), 255};
    for (int pixel = 0; pixel < PlaceholderSize * PlaceholderSize; ++pixel)
    {
        texture.pixels.insert(texture.pixels.end(), bgra.begin(), bgra.end());
    }
    return texture;
}

// Loads face textures by name: liquids as their colour, other textures from Data/bitmaps (cooked first).
std::vector<OutdoorBitmapTexture> loadFaceTextures(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &textureNames,
    const std::unordered_map<std::string, const LiquidDefinition *> &liquidTextures,
    BitmapLoadCache &bitmapLoadCache,
    const MapLoadProgressPump &progressPump)
{
    std::vector<OutdoorBitmapTexture> textures;

    // Cooked files resolve through the load's caches here, then read and decode on the load workers.
    struct CookedSlot
    {
        std::optional<std::string> path;
        const std::optional<std::vector<uint8_t>> *pCachedBytes = nullptr;
        std::optional<std::vector<uint8_t>> readBytes;
        std::optional<OutdoorBitmapTexture> texture;
    };
    std::vector<CookedSlot> cookedSlots(textureNames.size());
    for (size_t index = 0; index < textureNames.size(); ++index)
    {
        pumpMapLoadProgress(progressPump);
        if (liquidTextures.contains(textureNames[index]))
        {
            continue;
        }
        CookedSlot &slot = cookedSlots[index];
        slot.path = findCookedSurfaceTexturePath(assetFileSystem, textureNames[index],
            bitmapDirectoryAssetPathsByPath(bitmapLoadCache), bitmapPathByKey(bitmapLoadCache));
        if (slot.path && bitmapLoadCache.retainBinaryFiles)
        {
            const auto cachedIt = bitmapBinaryFilesByPath(bitmapLoadCache).find(*slot.path);
            if (cachedIt != bitmapBinaryFilesByPath(bitmapLoadCache).end())
            {
                slot.pCachedBytes = &cachedIt->second;
            }
        }
    }
    const bool surfaceMaterials = bitmapLoadCache.surfaceMaterials;
    Engine::parallelFor(cookedSlots.size(), [&assetFileSystem, &textureNames, &cookedSlots, surfaceMaterials](
        size_t index)
    {
        CookedSlot &slot = cookedSlots[index];
        if (!slot.path)
        {
            return;
        }
        if (slot.pCachedBytes == nullptr)
        {
            slot.readBytes = assetFileSystem.readBinaryFile(*slot.path);
        }
        slot.texture = decodeCookedSurfaceTexture(textureNames[index], *slot.path,
            slot.pCachedBytes != nullptr ? *slot.pCachedBytes : slot.readBytes);
        if (surfaceMaterials)
        {
            loadSurfaceMaterialMaps(assetFileSystem, *slot.path, *slot.texture);
        }
    });

    for (size_t index = 0; index < textureNames.size(); ++index)
    {
        const std::string &textureName = textureNames[index];
        if (const auto liquid = liquidTextures.find(textureName); liquid != liquidTextures.end())
        {
            textures.push_back(liquidFaceTexture(textureName, *liquid->second));
            continue;
        }
        CookedSlot &slot = cookedSlots[index];
        if (slot.texture)
        {
            if (slot.pCachedBytes == nullptr && bitmapLoadCache.retainBinaryFiles)
            {
                bitmapBinaryFilesByPath(bitmapLoadCache).emplace(*slot.path, std::move(slot.readBytes));
            }
            textures.push_back(std::move(*slot.texture));
            continue;
        }
        int textureWidth = 0;
        int textureHeight = 0;
        Engine::AssetScaleTier loadedTier = Engine::AssetScaleTier::X1;
        const std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                "Data/bitmaps",
                textureName,
                textureWidth,
                textureHeight,
                false,
                bitmapLoadCache,
                0,
                {},
                &loadedTier
            );

        if (!pixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        OutdoorBitmapTexture texture = {};
        texture.textureName = textureName;
        texture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, loadedTier);
        texture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, loadedTier);
        texture.physicalWidth = textureWidth;
        texture.physicalHeight = textureHeight;
        updateBitmapAlphaInfo(texture, *pixels);
        texture.pixels = *pixels;
        textures.push_back(std::move(texture));
    }

    return textures;
}

std::optional<OutdoorBModelTextureSet> buildOutdoorBModelTextureSet(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache,
    const TextureFrameTable *pTextureFrameTable,
    const LiquidTable *pLiquidTable,
    const std::vector<OutdoorSceneSurfaceAnimation> *pSceneSurfaceAnimations,
    const MapItemSourceData *pItemSourceData,
    const MapLoadProgressPump &progressPump
)
{
    std::vector<std::string> textureNames;
    std::unordered_map<std::string, const LiquidDefinition *> liquidTextures;
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
            const OutdoorSceneSurfaceAnimation *pSceneAnimation = nullptr;

            if (pSceneSurfaceAnimations != nullptr)
            {
                const auto sceneAnimationIt = std::find_if(
                    pSceneSurfaceAnimations->begin(),
                    pSceneSurfaceAnimations->end(),
                    [&normalizedName](const OutdoorSceneSurfaceAnimation &animation)
                    {
                        return animation.textureName == normalizedName;
                    });

                if (sceneAnimationIt != pSceneSurfaceAnimations->end())
                {
                    pSceneAnimation = &*sceneAnimationIt;
                }
            }

            const SurfaceAnimationSequence animation = pSceneAnimation != nullptr
                ? pSceneAnimation->animation
                : resolveSurfaceAnimation(
                    face.textureName,
                    face.attributes,
                    false,
                    pTextureFrameTable,
                    pLiquidTable);

            if (const LiquidDefinition *pLiquid = pLiquidTable != nullptr
                    ? pLiquidTable->findMatch(normalizedName, face.attributes, false) : nullptr)
            {
                liquidTextures.try_emplace(normalizedName, pLiquid);
            }

            appendTextureNameIfMissing(textureNames, normalizedName);
            appendAnimationTextureNamesIfMissing(textureNames, animation);
            appendTextureAnimationBindingIfMissing(animationBindings, normalizedName, animation);
        }
    }
    appendMm9BarrelLiquidTextureNames(textureNames, pItemSourceData);

    if (textureNames.empty())
    {
        return std::nullopt;
    }

    OutdoorBModelTextureSet textureSet = {};
    textureSet.animationBindings = animationBindings;
    textureSet.textures = loadFaceTextures(
        assetFileSystem, textureNames, liquidTextures, bitmapLoadCache, progressPump);

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
    const LiquidTable *pLiquidTable,
    const MapItemSourceData *pItemSourceData,
    const MapLoadProgressPump &progressPump
)
{
    std::vector<std::string> textureNames;
    std::unordered_map<std::string, const LiquidDefinition *> liquidTextures;
    std::vector<std::pair<std::string, SurfaceAnimationSequence>> animationBindings;

    for (const IndoorFace &face : indoorMapData.faces)
    {
        if (face.isPortal || face.textureName.empty())
        {
            continue;
        }

        const std::string normalizedName = toLowerCopy(face.textureName);
        const std::optional<SurfaceAnimationSequence> storedAnimation =
            resolveStoredFaceAnimation(
                face.textureName,
                face.attributes,
                face.textureFrameTableIndex,
                pTextureFrameTable,
                pLiquidTable);
        const SurfaceAnimationSequence animation = storedAnimation
            ? *storedAnimation
            : resolveSurfaceAnimation(face.textureName, face.attributes, false, pTextureFrameTable, pLiquidTable);

        if (const LiquidDefinition *pLiquid = pLiquidTable != nullptr && !storedAnimation
                ? pLiquidTable->findMatch(normalizedName, face.attributes, false) : nullptr)
        {
            liquidTextures.try_emplace(normalizedName, pLiquid);
        }

        appendTextureNameIfMissing(textureNames, normalizedName);
        appendAnimationTextureNamesIfMissing(textureNames, animation);
        appendTextureAnimationBindingIfMissing(animationBindings, normalizedName, animation);
    }
    appendMm9BarrelLiquidTextureNames(textureNames, pItemSourceData);

    if (textureNames.empty())
    {
        return std::nullopt;
    }

    IndoorTextureSet textureSet = {};
    textureSet.animationBindings = animationBindings;
    textureSet.textures = loadFaceTextures(
        assetFileSystem, textureNames, liquidTextures, bitmapLoadCache, progressPump);

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

// The world's overlays in name order, then the active ruleset's (`rulesetRoot`, empty for Standard).
std::vector<std::string> buildSceneOverlayPathCandidates(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneFileName,
    const std::string &rulesetRoot)
{
    std::vector<std::string> candidates;
    const auto collect = [&](const std::string &directory)
    {
        std::vector<std::string> found;

        for (const std::string &entryName : assetFileSystem.enumerate(directory))
        {
            if (isSceneOverlayFileName(entryName, sceneFileName))
            {
                found.push_back(directory + "/" + entryName);
            }
        }

        std::sort(found.begin(), found.end(), [](const std::string &left, const std::string &right)
        {
            return toLowerCopy(left) < toLowerCopy(right);
        });
        candidates.insert(candidates.end(), found.begin(), found.end());
    };

    collect("Data/games");

    if (!rulesetRoot.empty())
    {
        collect(rulesetRoot + "maps");
    }

    return candidates;
}
}

bool ensureMonsterSpriteFramesLoaded(
    const Engine::AssetFileSystem &assetFileSystem,
    const MonsterTable &monsterTable,
    int16_t monsterId,
    SpriteFrameTable &spriteFrameTable,
    const ActorModelManifest *pActorModels)
{
    const MonsterEntry *pMonsterEntry = monsterTable.findById(monsterId);

    if (pMonsterEntry == nullptr)
    {
        return false;
    }

    // The monster, and the tier its model is sized from (actors.yml scale_reference). A family already in the table
    // (one of its sprites is there) is not loaded again: the table rejects a family loaded twice, which stopped the
    // load of a second tier sized from the same reference (MM7 Harpy C summoned after Harpy B).
    std::vector<const MonsterEntry *> monsterEntries = {pMonsterEntry};
    const ActorModelManifest::Entry *pModel =
        pActorModels != nullptr ? pActorModels->find(pMonsterEntry->internalName) : nullptr;

    if (pModel != nullptr && pModel->node["scale_reference"])
    {
        monsterEntries.push_back(monsterTable.findByInternalName(pModel->node["scale_reference"].as<std::string>()));
    }

    std::unordered_set<std::string> monsterFamilies;
    std::unordered_set<std::string> loadedFamilies;
    std::unordered_set<std::string> worldPrefixedMonsterSpriteNames;

    for (const MonsterEntry *pEntry : monsterEntries)
    {
        if (pEntry == nullptr)
        {
            continue;
        }

        for (const std::string &spriteName : pEntry->spriteNames)
        {
            const bool present = spriteFrameTable.findFrameIndexBySpriteName(spriteName).has_value();

            if (const std::optional<std::string> familyRoot = monsterSpriteFamilyRoot(spriteName))
            {
                (present ? loadedFamilies : monsterFamilies).insert(*familyRoot);
            }
            else if (!present && isWorldPrefixedMonsterSpriteName(spriteName))
            {
                worldPrefixedMonsterSpriteNames.insert(toLowerCopy(spriteName));
            }
        }
    }

    for (const std::string &familyRoot : loadedFamilies)
    {
        monsterFamilies.erase(familyRoot);
    }

    if (monsterFamilies.empty() && worldPrefixedMonsterSpriteNames.empty())
    {
        return spriteFrameTable.findFrameIndexBySpriteName(pMonsterEntry->spriteNames[0]).has_value();
    }

    if (!appendMonsterSpriteFrameFamilies(
            assetFileSystem,
            monsterFamilies,
            worldPrefixedMonsterSpriteNames,
            spriteFrameTable,
            nullptr))
    {
        return false;
    }

    for (const std::string &spriteName : pMonsterEntry->spriteNames)
    {
        if (!spriteName.empty() && spriteFrameTable.findFrameIndexBySpriteName(spriteName))
        {
            return true;
        }
    }

    return false;
}

std::optional<OutdoorBitmapTexture> loadCookedSurfaceTexture(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    Engine::DirectoryAssetPathCache &directoryAssetPathsByPath,
    Engine::AssetPathLookupCache &assetPathByKey,
    Engine::BinaryAssetCache *pBinaryFilesByPath)
{
    const std::optional<std::string> path =
        findCookedSurfaceTexturePath(assetFileSystem, textureName, directoryAssetPathsByPath, assetPathByKey);
    if (!path)
    {
        return std::nullopt;
    }
    if (pBinaryFilesByPath == nullptr)
    {
        return decodeCookedSurfaceTexture(textureName, *path, assetFileSystem.readBinaryFile(*path));
    }
    auto cachedIt = pBinaryFilesByPath->find(*path);
    if (cachedIt == pBinaryFilesByPath->end())
    {
        cachedIt = pBinaryFilesByPath->emplace(*path, assetFileSystem.readBinaryFile(*path)).first;
    }
    return decodeCookedSurfaceTexture(textureName, *path, cachedIt->second);
}

bool hasSurfaceMaterialMaps(const std::vector<OutdoorBitmapTexture> &textures)
{
    return std::any_of(textures.begin(), textures.end(), [](const OutdoorBitmapTexture &texture)
    {
        return texture.materialNormal != nullptr;
    });
}

std::optional<OutdoorBitmapTexture> loadSurfaceTexture(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName)
{
    BitmapLoadCache bitmapLoadCache = {};
    bitmapLoadCache.retainBinaryFiles = false;
    bitmapLoadCache.retainDecodedPixels = false;
    std::vector<OutdoorBitmapTexture> textures =
        loadFaceTextures(assetFileSystem, {toLowerCopy(textureName)}, {}, bitmapLoadCache, {});

    if (textures.empty())
    {
        return std::nullopt;
    }

    return std::move(textures.front());
}

namespace
{
size_t texturePixelBytes(const std::vector<OutdoorBitmapTexture> &textures)
{
    size_t byteCount = 0;

    for (const OutdoorBitmapTexture &texture : textures)
    {
        byteCount += texture.pixels.size() + (texture.cookedTexture ? texture.cookedTexture->blocks.size() : 0)
            + (texture.materialNormal ? texture.materialNormal->blocks.size() : 0)
            + (texture.materialDetail ? texture.materialDetail->blocks.size() : 0);
    }

    return byteCount;
}

void clearTexturePixels(std::vector<OutdoorBitmapTexture> &textures)
{
    for (OutdoorBitmapTexture &texture : textures)
    {
        std::vector<uint8_t>().swap(texture.pixels);
        texture.cookedTexture.reset();
        texture.materialNormal.reset();
        texture.materialDetail.reset();
    }
}

size_t billboardSetPixelBytes(const std::optional<DecorationBillboardSet> &billboardSet)
{
    return billboardSet ? texturePixelBytes(billboardSet->textures) : 0;
}

size_t billboardSetPixelBytes(const std::optional<ActorPreviewBillboardSet> &billboardSet)
{
    return billboardSet ? texturePixelBytes(billboardSet->textures) : 0;
}

size_t billboardSetPixelBytes(const std::optional<SpriteObjectBillboardSet> &billboardSet)
{
    return billboardSet ? texturePixelBytes(billboardSet->textures) : 0;
}

template <typename BillboardSet>
void clearBillboardSetPixels(std::optional<BillboardSet> &billboardSet)
{
    if (billboardSet)
    {
        clearTexturePixels(billboardSet->textures);
    }
}
}

size_t mapRenderSourcePixelBytes(const MapAssetInfo &mapAssetInfo)
{
    size_t byteCount = 0;

    if (mapAssetInfo.outdoorMapData && mapAssetInfo.outdoorMapData->lightingData)
    {
        for (const OutdoorLightmapAtlasPage &page : mapAssetInfo.outdoorMapData->lightingData->atlasPages)
        {
            byteCount += page.pixelsBgra.size() * sizeof(uint32_t);
        }
    }

    if (mapAssetInfo.outdoorBModelTextureSet)
    {
        byteCount += texturePixelBytes(mapAssetInfo.outdoorBModelTextureSet->textures);
    }

    byteCount += billboardSetPixelBytes(mapAssetInfo.outdoorDecorationBillboardSet);
    byteCount += billboardSetPixelBytes(mapAssetInfo.outdoorActorPreviewBillboardSet);
    byteCount += billboardSetPixelBytes(mapAssetInfo.outdoorSpriteObjectBillboardSet);
    byteCount += billboardSetPixelBytes(mapAssetInfo.indoorDecorationBillboardSet);
    byteCount += billboardSetPixelBytes(mapAssetInfo.indoorActorPreviewBillboardSet);
    byteCount += billboardSetPixelBytes(mapAssetInfo.indoorSpriteObjectBillboardSet);

    if (mapAssetInfo.indoorTextureSet)
    {
        byteCount += texturePixelBytes(mapAssetInfo.indoorTextureSet->textures);
    }

    return byteCount;
}

void resolveDuplicateTorchLights(const IndoorMapData &indoorMapData, DecorationBillboardSet &billboardSet)
{
    constexpr float ClaimDistance = 128.0f;
    billboardSet.mapLightsReplacedByDecorations.assign(indoorMapData.lights.size(), false);
    // Light-emitting decorations and their reach (the larger of the light and the sprite glow, as the lighting uses).
    std::vector<std::pair<size_t, float>> emitters;
    for (size_t index = 0; index < billboardSet.billboards.size(); ++index)
    {
        const DecorationBillboard &billboard = billboardSet.billboards[index];
        const DecorationEntry *pDecoration = billboardSet.decorationTable.get(billboard.decorationId);
        if (pDecoration == nullptr)
        {
            continue;
        }
        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(pDecoration->spriteId, 0);
        const float glowRadius = pFrame != nullptr ? float(pFrame->glowRadius) : 0.0f;
        const float radius = std::max(float(pDecoration->lightRadius), glowRadius);
        if (radius > 0.0f)
        {
            emitters.emplace_back(index, radius);
        }
    }
    std::vector<bool> claimed(emitters.size(), false);
    for (size_t lightId = 0; lightId < indoorMapData.lights.size(); ++lightId)
    {
        const IndoorLight &light = indoorMapData.lights[lightId];
        if (light.radius <= 0)
        {
            continue;
        }
        size_t nearest = emitters.size();
        float nearestSquared = ClaimDistance * ClaimDistance;
        for (size_t emitter = 0; emitter < emitters.size(); ++emitter)
        {
            const DecorationBillboard &billboard = billboardSet.billboards[emitters[emitter].first];
            const float dx = float(billboard.x - light.x);
            const float dy = float(billboard.y - light.y);
            const float dz = float(billboard.z - light.z);
            const float distanceSquared = dx * dx + dy * dy + dz * dz;
            if (!claimed[emitter] && distanceSquared <= nearestSquared)
            {
                nearest = emitter;
                nearestSquared = distanceSquared;
            }
        }
        if (nearest == emitters.size())
        {
            continue;
        }
        claimed[nearest] = true;
        if (float(light.radius) > emitters[nearest].second)
        {
            billboardSet.billboards[emitters[nearest].first].litByMapLight = true;
        }
        else
        {
            billboardSet.mapLightsReplacedByDecorations[lightId] = true;
        }
    }
}

void clearMapRenderSourcePixels(MapAssetInfo &mapAssetInfo)
{
    if (mapAssetInfo.outdoorMapData && mapAssetInfo.outdoorMapData->lightingData)
    {
        for (OutdoorLightmapAtlasPage &page : mapAssetInfo.outdoorMapData->lightingData->atlasPages)
        {
            std::vector<uint32_t>().swap(page.pixelsBgra);
        }
    }

    if (mapAssetInfo.outdoorBModelTextureSet)
    {
        clearTexturePixels(mapAssetInfo.outdoorBModelTextureSet->textures);
    }

    clearBillboardSetPixels(mapAssetInfo.outdoorDecorationBillboardSet);
    clearBillboardSetPixels(mapAssetInfo.outdoorActorPreviewBillboardSet);
    clearBillboardSetPixels(mapAssetInfo.outdoorSpriteObjectBillboardSet);
    clearBillboardSetPixels(mapAssetInfo.indoorDecorationBillboardSet);
    clearBillboardSetPixels(mapAssetInfo.indoorActorPreviewBillboardSet);
    clearBillboardSetPixels(mapAssetInfo.indoorSpriteObjectBillboardSet);

    if (mapAssetInfo.indoorTextureSet)
    {
        clearTexturePixels(mapAssetInfo.indoorTextureSet->textures);
    }
}

bool ActorPreviewBillboardSet::drawsModel(const MonsterEntry *pMonster) const
{
    return actorModels != nullptr && pMonster != nullptr && actorModels->binds(pMonster->internalName);
}

bool ActorPreviewBillboardSet::drawsModel(int16_t monsterId) const
{
    return actorModels != nullptr && actorModels->bindsMonster(monsterId);
}

std::optional<MapAssetInfo> MapAssetLoader::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    MapLoadPurpose purpose,
    const MapCompanionLoadOptions &companionLoadOptions,
    const MapLoadProgressPump &progressPump,
    MapAssetLoadSharedCache *pSharedCache,
    std::shared_ptr<const ActorModelManifest> pActorModels
) const
{
    BitmapLoadCache bitmapLoadCache = {};
    bitmapLoadCache.surfaceMaterials = companionLoadOptions.surfaceMaterials;
    if (pSharedCache != nullptr)
    {
        pSharedCache->beginLoad(assetFileSystem.contentGeneration());
        // The common sprite frame table (one large YAML parse, kept for the session) parses on a worker while this
        // thread reads the map, its scene and its lighting; loadCommonSpriteFrameTable collects it.
        if (!pSharedCache->commonSpriteFrameTable && !pSharedCache->commonSpriteFrameTableLoading.valid()
            && std::thread::hardware_concurrency() > 1)
        {
            pSharedCache->commonSpriteFrameTableLoading = std::async(std::launch::async, [&assetFileSystem]()
            {
                return parseCommonSpriteFrameTable(assetFileSystem);
            }).share();
        }
    }
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

    std::optional<MapPresentation> mapPresentation;

    if (!map.worldId.empty())
    {
        const std::optional<std::string> catalogPath = findAssetPathInDirectory(
            assetFileSystem,
            "worlds/" + map.worldId + "/ui/maps",
            "catalog.yml");

        if (catalogPath)
        {
            const std::optional<std::string> catalogText = assetFileSystem.readTextFile(*catalogPath);

            if (!catalogText)
            {
                std::cerr << "Failed to load map presentation catalog for " << map.fileName << '\n';
                return std::nullopt;
            }

            std::string presentationError;
            mapPresentation = loadMapPresentationFromCatalog(*catalogText, map.fileName, presentationError);

            if (!presentationError.empty())
            {
                std::cerr << "Failed to parse map presentation for " << map.fileName
                          << ": " << presentationError << '\n';
                return std::nullopt;
            }
        }
    }

    std::optional<std::vector<uint8_t>> companionBytes;
    std::optional<std::string> sceneText;
    std::vector<std::pair<std::string, std::string>> sceneOverlays;
    std::vector<OutdoorSceneSurfaceAnimation> outdoorSceneSurfaceAnimations;

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

                for (const std::string &overlayPath : buildSceneOverlayPathCandidates(
                         assetFileSystem, *sceneFileName, companionLoadOptions.rulesetRoot))
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
    const bool loadDecorationBillboards = loadFullPresentation || purpose == MapLoadPurpose::BillboardPreviews
        || purpose == MapLoadPurpose::DecorationPlacements;
    const bool loadSpriteObjectBillboards = loadFullPresentation;

    std::vector<OutdoorBitmapTexture> decorationTextures;
    if (loadDecorationBillboards)
    {
        std::string error;
        std::optional<std::vector<OutdoorBitmapTexture>> overrides =
            loadMapDecorationTextures(assetFileSystem, map.worldId, map.fileName, error);
        if (!overrides)
        {
            std::cerr << "Failed to load map decoration textures: " << error << '\n';
            return std::nullopt;
        }
        decorationTextures = std::move(*overrides);
    }

    std::optional<TextureFrameTable> textureFrameTable;
    std::optional<LiquidTable> liquidTable;

    if (loadRenderSurfaces)
    {
        textureFrameTable = loadTextureFrameTable(assetFileSystem, pSharedCache);
        logStageComplete("texture frame table loaded");
    }

    // Liquids decide how liquid tiles and faces look and, for every load, which liquid terrain is only waded
    // through. The map's world sees its own liquids before the shared ones.
    liquidTable = loadLiquidTable(assetFileSystem, pSharedCache);

    if (liquidTable)
    {
        liquidTable = liquidTable->forWorld(map.worldId);
    }

    logStageComplete("liquids loaded");

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
            assetInfo.outdoorMapData->mapPresentation = mapPresentation;

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
                outdoorSceneSurfaceAnimations = sceneData->surfaceAnimations;
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

                if (!applyActorLootOverrides(sceneData->itemSources, sceneMapDeltaData, sceneError))
                {
                    std::cerr << "Failed to apply outdoor item sources for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                assetInfo.outdoorMapDeltaData = std::move(sceneMapDeltaData);
                assetInfo.itemSourceData = sceneData->itemSources;
                assetInfo.outdoorWeatherProfile =
                    buildOutdoorWeatherProfile(sceneData->environment, assetInfo.outdoorMapDeltaData->locationTime);
                assetInfo.authoredCompanionSource = AuthoredCompanionSource::SceneYml;
                logStageComplete("outdoor scene yml applied");

                if (sceneData->sceneProfile == OutdoorSceneProfile::BModelWorld)
                {
                    const std::optional<std::string> navigationFileName = buildNavigationFileName(map.fileName);
                    const std::optional<std::string> navigationPath = navigationFileName
                        ? findAssetPath(assetFileSystem, map.worldId, *navigationFileName)
                        : std::nullopt;
                    const std::optional<std::vector<uint8_t>> navigationBytes = navigationPath
                        ? assetFileSystem.readBinaryFile(*navigationPath)
                        : std::nullopt;

                    if (!navigationPath || !navigationBytes)
                    {
                        std::cerr << "Failed to load cooked outdoor navigation for " << map.fileName << '\n';
                        return std::nullopt;
                    }

                    OutdoorNavigationDataLoader navigationLoader = {};
                    std::optional<OutdoorNavigationData> navigationData = navigationLoader.loadFromBytes(
                        *navigationBytes,
                        *geometryBytes,
                        *assetInfo.outdoorMapData,
                        sceneError);

                    if (!navigationData)
                    {
                        std::cerr << "Failed to parse cooked outdoor navigation for " << map.fileName
                                  << ": " << sceneError << '\n';
                        return std::nullopt;
                    }

                    assetInfo.navigationPath = *navigationPath;
                    assetInfo.navigationSize = navigationBytes->size();
                    assetInfo.outdoorMapData->navigationData = std::move(*navigationData);
                    logStageComplete("cooked outdoor navigation loaded");

                    const std::optional<std::string> renderDataFileName =
                        buildRenderDataFileName(map.fileName);
                    const std::optional<std::string> renderDataPath = renderDataFileName
                        ? findAssetPath(assetFileSystem, map.worldId, *renderDataFileName)
                        : std::nullopt;
                    const std::optional<std::vector<uint8_t>> renderDataBytes = renderDataPath
                        ? assetFileSystem.readBinaryFile(*renderDataPath)
                        : std::nullopt;

                    if (!renderDataPath || !renderDataBytes)
                    {
                        std::cerr << "Failed to load cooked outdoor render data for " << map.fileName << '\n';
                        return std::nullopt;
                    }

                    OutdoorRenderDataLoader renderDataLoader = {};
                    std::optional<OutdoorRenderData> renderData = renderDataLoader.loadFromBytes(
                        *renderDataBytes,
                        *geometryBytes,
                        *assetInfo.outdoorMapData,
                        sceneError);

                    if (!renderData)
                    {
                        std::cerr << "Failed to parse cooked outdoor render data for " << map.fileName
                                  << ": " << sceneError << '\n';
                        return std::nullopt;
                    }

                    assetInfo.renderDataPath = *renderDataPath;
                    assetInfo.renderDataSize = renderDataBytes->size();
                    assetInfo.outdoorMapData->renderData = std::move(*renderData);
                    logStageComplete("cooked outdoor render data loaded");

                }
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

            const std::optional<std::string> lightingDataFileName =
                buildLightingDataFileName(map.fileName);
            const std::optional<std::string> lightingDataPath =
                lightingDataFileName && purpose != MapLoadPurpose::DecorationPlacements
                ? findAssetPath(assetFileSystem, map.worldId, *lightingDataFileName)
                : std::nullopt;

            if (lightingDataPath)
            {
                const std::optional<std::vector<uint8_t>> lightingDataBytes =
                    assetFileSystem.readBinaryFile(*lightingDataPath);

                if (!lightingDataBytes)
                {
                    std::cerr << "Failed to load cooked outdoor lighting for " << map.fileName << '\n';
                    return std::nullopt;
                }

                std::string lightingError;
                OutdoorLightingDataLoader lightingDataLoader = {};
                std::optional<OutdoorLightingData> lightingData = lightingDataLoader.loadFromBytes(
                    *lightingDataBytes,
                    *geometryBytes,
                    *assetInfo.outdoorMapData,
                    lightingError);

                if (!lightingData)
                {
                    std::cerr << "Failed to parse cooked outdoor lighting for " << map.fileName
                              << ": " << lightingError << '\n';
                    return std::nullopt;
                }

                if (assetInfo.outdoorMapData->sceneProfile == OutdoorSceneProfile::BModelWorld)
                {
                    scaleOutdoorLightingBrightness(
                        *lightingData,
                        assetInfo.outdoorMapData->lightmapBrightnessScale);
                }

                assetInfo.lightingDataPath = *lightingDataPath;
                assetInfo.lightingDataSize = lightingDataBytes->size();
                assetInfo.outdoorMapData->lightingData = std::move(*lightingData);
                logStageComplete("cooked outdoor lighting loaded");
            }

            if (!applyTerrainTileDescriptorAttributes(assetFileSystem, *assetInfo.outdoorMapData))
            {
                std::cerr << "Failed to apply outdoor terrain tile flags for " << map.fileName << '\n';
            }

            applyShallowLiquidTerrainAttributes(
                assetFileSystem, *assetInfo.outdoorMapData, liquidTable ? &*liquidTable : nullptr);

            if (assetInfo.outdoorMapDeltaData)
            {
                uint32_t mapExtraBitsRaw = 0;
                int32_t ceiling = 0;
                decodeOutdoorMapExtra(assetInfo.outdoorMapDeltaData->locationTime, mapExtraBitsRaw, ceiling);
                assetInfo.outdoorMapData->noTerrain = (mapExtraBitsRaw & EnvironmentFlagNoTerrain) != 0;
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
                        // Gameplay streams exact actor frames and viewing angles through OutdoorGameView.
                        purpose != MapLoadPurpose::FullGameplay,
                        progressPump,
                        pSharedCache,
                        pActorModels
                    );
                logStageComplete("outdoor actor previews built");
            }

            if (loadRenderSurfaces)
            {
                assetInfo.outdoorLandMask = buildOutdoorLandMask(
                    assetFileSystem, *assetInfo.outdoorMapData, liquidTable ? &*liquidTable : nullptr);
                logStageComplete("outdoor land mask built");
                assetInfo.outdoorTileColors = buildOutdoorTileColors(assetFileSystem, *assetInfo.outdoorMapData);
                logStageComplete("outdoor tile colors built");
                if (!assetInfo.outdoorMapData->noTerrain)
                {
                    assetInfo.outdoorTerrainTiles = buildOutdoorTerrainTiles(
                        assetFileSystem, *assetInfo.outdoorMapData, liquidTable ? &*liquidTable : nullptr);
                    if (!assetInfo.outdoorTerrainTiles)
                    {
                        std::cerr << "Failed to build the outdoor terrain tiles for " << map.fileName << '\n';
                        return std::nullopt;
                    }
                    logStageComplete("outdoor terrain tiles built");
                }
                assetInfo.outdoorBModelTextureSet =
                    buildOutdoorBModelTextureSet(
                        assetFileSystem,
                        *assetInfo.outdoorMapData,
                        bitmapLoadCache,
                        textureFrameTable ? &*textureFrameTable : nullptr,
                        liquidTable ? &*liquidTable : nullptr,
                        outdoorSceneSurfaceAnimations.empty() ? nullptr : &outdoorSceneSurfaceAnimations,
                        assetInfo.itemSourceData ? &*assetInfo.itemSourceData : nullptr,
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
                        map.worldId,
                        map.fileName,
                        decorationTextures,
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
                        map.worldId,
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
        if (assetInfo.indoorMapData)
        {
            normalizeMergedMm6IndoorStaticLights(map, *assetInfo.indoorMapData);
        }
        logStageComplete("indoor geometry parsed");

        if (assetInfo.indoorMapData)
        {
            assetInfo.indoorMapData->mapPresentation = mapPresentation;

            // Opt-in baked lighting: a valid sidecar lightmaps the map; a stale or broken one is ignored (the map
            // renders with its point lights and ambient, as every map without one does) and tools/lighting/
            // stale_bakes.py lists it.
            const std::optional<std::string> lightingDataFileName = buildLightingDataFileName(map.fileName);
            const std::optional<std::string> lightingDataPath = lightingDataFileName && loadFullPresentation
                ? findAssetPath(assetFileSystem, map.worldId, *lightingDataFileName)
                : std::nullopt;
            const std::optional<std::vector<uint8_t>> lightingDataBytes =
                lightingDataPath ? assetFileSystem.readBinaryFile(*lightingDataPath) : std::nullopt;

            if (lightingDataBytes)
            {
                std::string lightingError;
                std::optional<IndoorBakedLighting> lighting = loadIndoorBakedLighting(
                    *lightingDataBytes, *geometryBytes, *assetInfo.indoorMapData, lightingError);

                if (lighting)
                {
                    assetInfo.lightingDataPath = *lightingDataPath;
                    assetInfo.lightingDataSize = lightingDataBytes->size();
                    assetInfo.indoorMapData->bakedLighting =
                        std::make_shared<const IndoorBakedLighting>(std::move(*lighting));
                    logStageComplete("indoor baked lighting loaded");
                }
                else
                {
                    std::cerr << "Ignoring the baked lighting of " << map.fileName << ": " << lightingError << '\n';
                }
            }

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
                assetInfo.map.arena = sceneData->arena;
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

                if (!applyActorLootOverrides(sceneData->itemSources, sceneMapDeltaData, sceneError))
                {
                    std::cerr << "Failed to apply indoor item sources for " << map.fileName
                              << ": " << sceneError << '\n';
                    return std::nullopt;
                }

                assetInfo.indoorMapDeltaData = std::move(sceneMapDeltaData);
                assetInfo.itemSourceData = sceneData->itemSources;
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

            // Shallow liquid floors slow the party wading through them (liquids.yml wade_speed).
            if (liquidTable)
            {
                const std::vector<IndoorFace> &faces = assetInfo.indoorMapData->faces;

                for (size_t faceIndex = 0; faceIndex < faces.size(); ++faceIndex)
                {
                    const LiquidDefinition *pLiquid = faces[faceIndex].isPortal ? nullptr
                        : liquidTable->findMatch(toLowerCopy(faces[faceIndex].textureName), faces[faceIndex].attributes,
                            false);

                    if (pLiquid != nullptr && pLiquid->wadeSpeed < 1.0f)
                    {
                        assetInfo.indoorFaceWadeSpeeds.resize(faces.size(), 1.0f);
                        assetInfo.indoorFaceWadeSpeeds[faceIndex] = pLiquid->wadeSpeed;
                    }
                }
            }

            if (loadFullPresentation)
            {
                assetInfo.indoorTextureSet = buildIndoorTextureSet(
                    assetFileSystem,
                    *assetInfo.indoorMapData,
                    bitmapLoadCache,
                    textureFrameTable ? &*textureFrameTable : nullptr,
                    liquidTable ? &*liquidTable : nullptr,
                    assetInfo.itemSourceData ? &*assetInfo.itemSourceData : nullptr,
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
                        map.worldId,
                        map.fileName,
                        decorationTextures,
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
                        assetInfo.map,
                        monsterTable,
                        assetInfo.indoorMapDeltaData,
                        assetInfo.indoorMapData->spawns,
                        bitmapLoadCache,
                        nullptr,
                        true,
                        progressPump,
                        pSharedCache,
                        pActorModels
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
                        map.worldId,
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

std::optional<std::string> MapAssetLoader::buildNavigationFileName(const std::string &fileName)
{
    const std::string normalized = toLower(fileName);

    if (normalized.size() < 4 || !normalized.ends_with(".odm"))
    {
        return std::nullopt;
    }

    return normalized.substr(0, normalized.size() - 4) + ".nav";
}

std::optional<std::string> MapAssetLoader::buildRenderDataFileName(const std::string &fileName)
{
    const std::string normalized = toLower(fileName);

    if (normalized.size() < 4 || !normalized.ends_with(".odm"))
    {
        return std::nullopt;
    }

    return normalized.substr(0, normalized.size() - 4) + ".render";
}

std::optional<std::string> MapAssetLoader::buildLightingDataFileName(const std::string &fileName)
{
    const std::string normalized = toLower(fileName);

    if (normalized.size() < 4 || (!normalized.ends_with(".odm") && !normalized.ends_with(".blv")))
    {
        return std::nullopt;
    }

    return normalized.substr(0, normalized.size() - 4) + ".lighting";
}
}
