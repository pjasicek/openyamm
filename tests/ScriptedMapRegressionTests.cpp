#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/maps/MapAssetLoader.h"
#include "game/StringUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"

#include "tests/RegressionMapLoader.h"

#include <array>
#include <cstring>
#include <filesystem>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace
{
const OpenYAMM::Tests::RegressionMapLoader &requireRegressionMapLoader()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionMapLoaderLoaded(),
        OpenYAMM::Tests::regressionMapLoaderFailure().c_str());
    return OpenYAMM::Tests::regressionMapLoader();
}

bool hasMapGeometryAsset(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &fileName)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    const std::string normalizedFileName = OpenYAMM::Game::toLowerCopy(fileName);

    for (const std::string &entry : entries)
    {
        if (OpenYAMM::Game::toLowerCopy(entry) == normalizedFileName)
        {
            return true;
        }
    }

    return false;
}

std::vector<std::string> collectScriptedMapFileNames(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader)
{
    std::vector<std::string> scriptedMapFileNames;

    for (const OpenYAMM::Game::MapStatsEntry &entry : gameDataLoader.getMapStats().getEntries())
    {
        if (entry.fileName.empty())
        {
            continue;
        }

        const std::string extension =
            OpenYAMM::Game::toLowerCopy(std::filesystem::path(entry.fileName).extension().string());

        if (extension != ".odm" && extension != ".blv")
        {
            continue;
        }

        if (!hasMapGeometryAsset(assetFileSystem, entry.fileName))
        {
            continue;
        }

        const std::string scriptPath =
            "Data/scripts/maps/"
            + OpenYAMM::Game::toLowerCopy(std::filesystem::path(entry.fileName).stem().string())
            + ".lua";

        if (assetFileSystem.exists(scriptPath))
        {
            scriptedMapFileNames.push_back(entry.fileName);
        }
    }

    return scriptedMapFileNames;
}

bool loadOutdoorMapWithCompanionOptions(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions,
    OpenYAMM::Game::MapAssetInfo &mapAssetInfo)
{
    const OpenYAMM::Game::MapStatsEntry *pMapEntry = gameDataLoader.getMapStats().findByFileName(mapFileName);

    if (pMapEntry == nullptr)
    {
        return false;
    }

    OpenYAMM::Game::MapAssetLoader loader = {};
    const std::optional<OpenYAMM::Game::MapAssetInfo> loadedMap = loader.load(
        assetFileSystem,
        *pMapEntry,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getObjectTable(),
        loadPurpose,
        loadOptions);

    if (!loadedMap || !loadedMap->outdoorMapData || !loadedMap->outdoorMapDeltaData)
    {
        return false;
    }

    mapAssetInfo = *loadedMap;
    return true;
}

OpenYAMM::Game::Character makeRegressionPartyMember(
    const std::string &name,
    const std::string &className,
    const std::string &portraitTextureName,
    uint32_t characterDataId)
{
    OpenYAMM::Game::Character member = {};
    member.name = name;
    member.className = className;
    member.role = className;
    member.portraitTextureName = portraitTextureName;
    member.characterDataId = characterDataId;
    member.birthYear = 1160;
    member.experience = 0;
    member.level = 1;
    member.skillPoints = 5;
    member.might = 14;
    member.intellect = 14;
    member.personality = 14;
    member.endurance = 14;
    member.speed = 14;
    member.accuracy = 14;
    member.luck = 14;
    member.maxHealth = 40;
    member.health = 40;
    member.maxSpellPoints = 20;
    member.spellPoints = 20;
    return member;
}

OpenYAMM::Game::PartySeed createRegressionPartySeed()
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 200;
    seed.food = 7;
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));
    seed.members.push_back(makeRegressionPartyMember("Brom", "Cleric", "PC03-01", 3));
    seed.members.push_back(makeRegressionPartyMember("Cedric", "Druid", "PC05-01", 5));
    seed.members.push_back(makeRegressionPartyMember("Daria", "Sorcerer", "PC07-01", 7));
    return seed;
}

std::string bytesToUpperHex(const std::vector<uint8_t> &bytes)
{
    static constexpr char HexDigits[] = "0123456789ABCDEF";

    std::string text;
    text.reserve(bytes.size() * 2);

    for (uint8_t value : bytes)
    {
        text.push_back(HexDigits[(value >> 4) & 0x0F]);
        text.push_back(HexDigits[value & 0x0F]);
    }

    return text;
}

void appendNormalizedPosition(std::ostringstream &stream, int x, int y, int z)
{
    stream << x << ',' << y << ',' << z;
}

std::string buildNormalizedOutdoorAuthoredSnapshot(const OpenYAMM::Game::MapAssetInfo &mapAssetInfo)
{
    std::ostringstream stream;

    if (!mapAssetInfo.outdoorMapData || !mapAssetInfo.outdoorMapDeltaData)
    {
        stream << "missing_outdoor_state\n";
        return stream.str();
    }

    const OpenYAMM::Game::OutdoorMapData &outdoorMapData = *mapAssetInfo.outdoorMapData;
    const OpenYAMM::Game::MapDeltaData &mapDeltaData = *mapAssetInfo.outdoorMapDeltaData;
    const std::string effectiveSkyTexture =
        !mapDeltaData.locationTime.skyTextureName.empty()
        ? mapDeltaData.locationTime.skyTextureName
        : outdoorMapData.skyTexture;
    uint32_t mapExtraBitsRaw = 0;
    int32_t ceiling = 0;

    if (mapDeltaData.locationTime.reserved.size() >= sizeof(mapExtraBitsRaw) + sizeof(ceiling))
    {
        std::memcpy(&mapExtraBitsRaw, mapDeltaData.locationTime.reserved.data(), sizeof(mapExtraBitsRaw));
        std::memcpy(
            &ceiling,
            mapDeltaData.locationTime.reserved.data() + sizeof(mapExtraBitsRaw),
            sizeof(ceiling));
    }

    stream << "environment\n";
    stream << "sky_texture=" << effectiveSkyTexture << '\n';
    stream << "ground_tileset_name=" << outdoorMapData.groundTilesetName << '\n';
    stream << "master_tile=" << static_cast<int>(outdoorMapData.masterTile) << '\n';
    stream << "tile_set_lookup_indices="
           << outdoorMapData.tileSetLookupIndices[0] << ','
           << outdoorMapData.tileSetLookupIndices[1] << ','
           << outdoorMapData.tileSetLookupIndices[2] << ','
           << outdoorMapData.tileSetLookupIndices[3] << '\n';
    stream << "day_bits_raw=" << mapDeltaData.locationTime.weatherFlags << '\n';
    stream << "map_extra_bits_raw=" << mapExtraBitsRaw << '\n';
    stream << "flag_foggy=" << (((mapDeltaData.locationTime.weatherFlags & 0x1) != 0) ? 1 : 0) << '\n';
    stream << "flag_raining=" << (((mapExtraBitsRaw & 0x1) != 0) ? 1 : 0) << '\n';
    stream << "flag_snowing=" << (((mapExtraBitsRaw & 0x2) != 0) ? 1 : 0) << '\n';
    stream << "flag_underwater=" << (((mapExtraBitsRaw & 0x4) != 0) ? 1 : 0) << '\n';
    stream << "flag_no_terrain=" << (((mapExtraBitsRaw & 0x8) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_dark=" << (((mapExtraBitsRaw & 0x10) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_light=" << (((mapExtraBitsRaw & 0x20) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_foggy=" << (((mapExtraBitsRaw & 0x40) != 0) ? 1 : 0) << '\n';
    stream << "flag_red_fog=" << (((mapExtraBitsRaw & 0x80) != 0) ? 1 : 0) << '\n';
    stream << "fog_weak_distance=" << mapDeltaData.locationTime.fogWeakDistance << '\n';
    stream << "fog_strong_distance=" << mapDeltaData.locationTime.fogStrongDistance << '\n';
    stream << "ceiling=" << ceiling << '\n';

    stream << "terrain\n";

    for (size_t cellIndex = 0; cellIndex < outdoorMapData.attributeMap.size(); ++cellIndex)
    {
        const uint8_t value = outdoorMapData.attributeMap[cellIndex];

        if (value == 0)
        {
            continue;
        }

        const size_t x = cellIndex % OpenYAMM::Game::OutdoorMapData::TerrainWidth;
        const size_t y = cellIndex / OpenYAMM::Game::OutdoorMapData::TerrainWidth;
        stream << x << ',' << y << ',' << static_cast<int>(value)
               << ',' << (((value & 0x01) != 0) ? 1 : 0)
               << ',' << (((value & 0x02) != 0) ? 1 : 0) << '\n';
    }

    stream << "interactive_faces\n";

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const OpenYAMM::Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

            if (face.attributes == 0
                && face.cogNumber == 0
                && face.cogTriggeredNumber == 0
                && face.cogTrigger == 0)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ','
                   << face.attributes << ','
                   << face.cogNumber << ','
                   << face.cogTriggeredNumber << ','
                   << face.cogTrigger << '\n';
        }
    }

    stream << "entities\n";

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OpenYAMM::Game::OutdoorEntity &entity = outdoorMapData.entities[entityIndex];
        const uint16_t decorationFlag =
            entityIndex < mapDeltaData.decorationFlags.size()
            ? mapDeltaData.decorationFlags[entityIndex]
            : 0;

        stream << entity.name << '|'
               << entity.decorationListId << '|'
               << entity.aiAttributes << '|';
        appendNormalizedPosition(stream, entity.x, entity.y, entity.z);
        stream << '|'
               << entity.facing << '|'
               << entity.eventIdPrimary << '|'
               << entity.eventIdSecondary << '|'
               << entity.variablePrimary << '|'
               << entity.variableSecondary << '|'
               << entity.specialTrigger << '|'
               << decorationFlag << '\n';
    }

    stream << "spawns\n";

    for (const OpenYAMM::Game::OutdoorSpawn &spawn : outdoorMapData.spawns)
    {
        appendNormalizedPosition(stream, spawn.x, spawn.y, spawn.z);
        stream << '|'
               << spawn.radius << '|'
               << spawn.typeId << '|'
               << spawn.index << '|'
               << spawn.attributes << '|'
               << spawn.group << '\n';
    }

    stream << "location\n";
    stream << mapDeltaData.locationInfo.respawnCount << '|'
           << mapDeltaData.locationInfo.lastRespawnDay << '|'
           << mapDeltaData.locationInfo.reputation << '|'
           << mapDeltaData.locationInfo.alertStatus << '\n';

    stream << "face_attribute_overrides\n";
    size_t flattenedFaceIndex = 0;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex, ++flattenedFaceIndex)
        {
            const uint32_t baseValue = bmodel.faces[faceIndex].attributes;
            const uint32_t overrideValue =
                flattenedFaceIndex < mapDeltaData.faceAttributes.size()
                ? mapDeltaData.faceAttributes[flattenedFaceIndex]
                : baseValue;

            if (overrideValue == baseValue)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ',' << overrideValue << '\n';
        }
    }

    stream << "actors\n";

    for (const OpenYAMM::Game::MapDeltaActor &actor : mapDeltaData.actors)
    {
        stream << actor.name << '|'
               << actor.npcId << '|'
               << actor.attributes << '|'
               << actor.hp << '|'
               << static_cast<int>(actor.hostilityType) << '|'
               << actor.monsterInfoId << '|'
               << actor.monsterId << '|'
               << actor.radius << '|'
               << actor.height << '|'
               << actor.moveSpeed << '|';
        appendNormalizedPosition(stream, actor.x, actor.y, actor.z);
        stream << '|'
               << actor.spriteIds[0] << ','
               << actor.spriteIds[1] << ','
               << actor.spriteIds[2] << ','
               << actor.spriteIds[3] << '|'
               << actor.sectorId << '|'
               << actor.currentActionAnimation << '|'
               << actor.group << '|'
               << actor.ally << '|'
               << actor.uniqueNameIndex << '\n';
    }

    stream << "sprite_objects\n";

    for (const OpenYAMM::Game::MapDeltaSpriteObject &spriteObject : mapDeltaData.spriteObjects)
    {
        stream << spriteObject.spriteId << '|'
               << spriteObject.objectDescriptionId << '|';
        appendNormalizedPosition(stream, spriteObject.x, spriteObject.y, spriteObject.z);
        stream << '|';
        appendNormalizedPosition(
            stream,
            spriteObject.velocityX,
            spriteObject.velocityY,
            spriteObject.velocityZ);
        stream << '|'
               << spriteObject.yawAngle << '|'
               << spriteObject.soundId << '|'
               << spriteObject.attributes << '|'
               << spriteObject.sectorId << '|'
               << spriteObject.timeSinceCreated << '|'
               << spriteObject.temporaryLifetime << '|'
               << spriteObject.glowRadiusMultiplier << '|'
               << spriteObject.spellId << '|'
               << spriteObject.spellLevel << '|'
               << spriteObject.spellSkill << '|'
               << spriteObject.field54 << '|'
               << spriteObject.spellCasterPid << '|'
               << spriteObject.spellTargetPid << '|'
               << static_cast<int>(spriteObject.lodDistance) << '|'
               << static_cast<int>(spriteObject.spellCasterAbility) << '|';
        appendNormalizedPosition(
            stream,
            spriteObject.initialX,
            spriteObject.initialY,
            spriteObject.initialZ);
        stream << '|'
               << bytesToUpperHex(spriteObject.rawContainingItem) << '\n';
    }

    stream << "chests\n";

    for (const OpenYAMM::Game::MapDeltaChest &chest : mapDeltaData.chests)
    {
        stream << chest.chestTypeId << '|'
               << chest.flags << '|'
               << bytesToUpperHex(chest.rawItems) << '|';

        for (size_t index = 0; index < chest.inventoryMatrix.size(); ++index)
        {
            if (index > 0)
            {
                stream << ',';
            }

            stream << chest.inventoryMatrix[index];
        }

        stream << '\n';
    }

    stream << "variables_map\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.mapVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.mapVars[index]);
    }

    stream << "\nvariables_decor\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.decorVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.decorVars[index]);
    }

    stream << '\n';
    return stream.str();
}
}

TEST_CASE("generated_lua_event_scripts_are_loaded_from_files")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = mapLoader.gameDataLoader.getSelectedMap();

    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->globalEventProgram.has_value());
    REQUIRE(selectedMap->globalEventProgram->luaSourceText().has_value());
    REQUIRE(selectedMap->globalEventProgram->luaSourceName().has_value());
    CHECK_EQ(*selectedMap->globalEventProgram->luaSourceName(), "@Data/scripts/Global.lua");

    REQUIRE(selectedMap->localEventProgram.has_value());
    REQUIRE(selectedMap->localEventProgram->luaSourceText().has_value());
    REQUIRE(selectedMap->localEventProgram->luaSourceName().has_value());

    const std::string expectedLocalSourceName =
        "@Data/scripts/maps/"
        + OpenYAMM::Game::toLowerCopy(std::filesystem::path(selectedMap->map.fileName).stem().string())
        + ".lua";

    CHECK_EQ(*selectedMap->localEventProgram->luaSourceName(), expectedLocalSourceName);
}

TEST_CASE("generated_lua_event_scripts_load_for_every_scripted_map")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::vector<std::string> scriptedMapFileNames =
        collectScriptedMapFileNames(mapLoader.assetFileSystem, mapLoader.gameDataLoader);

    REQUIRE_FALSE(scriptedMapFileNames.empty());

    OpenYAMM::Game::GameDataLoader loader = mapLoader.gameDataLoader;
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    for (const std::string &mapFileName : scriptedMapFileNames)
    {
        INFO(mapFileName);
        REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(mapLoader.assetFileSystem, mapFileName));

        const std::optional<OpenYAMM::Game::MapAssetInfo> &loadedMap = loader.getSelectedMap();
        REQUIRE(loadedMap.has_value());
        REQUIRE(loadedMap->globalEventProgram.has_value());
        REQUIRE(loadedMap->globalEventProgram->luaSourceText().has_value());
        REQUIRE(loadedMap->localEventProgram.has_value());
        REQUIRE(loadedMap->localEventProgram->luaSourceText().has_value());

        const std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData =
            loadedMap->outdoorMapDeltaData ? loadedMap->outdoorMapDeltaData : loadedMap->indoorMapDeltaData;
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        CHECK(eventRuntime.buildOnLoadState(
            loadedMap->localEventProgram,
            loadedMap->globalEventProgram,
            mapDeltaData,
            runtimeState));
    }
}

TEST_CASE("outdoor_terrain_texture_atlas_builds_for_non_default_master_tiles")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    static constexpr std::array<const char *, 2> RequiredMaps = {
        "out04.odm",
        "out06.odm",
    };

    for (const char *pMapFileName : RequiredMaps)
    {
        INFO(pMapFileName);
        OpenYAMM::Game::MapAssetInfo loadedMap = {};
        REQUIRE(loadOutdoorMapWithCompanionOptions(
            mapLoader.assetFileSystem,
            mapLoader.gameDataLoader,
            pMapFileName,
            OpenYAMM::Game::MapLoadPurpose::Full,
            OpenYAMM::Game::MapCompanionLoadOptions{.allowSceneYml = true, .allowLegacyCompanion = true},
            loadedMap));
        REQUIRE(loadedMap.outdoorMapData.has_value());
        REQUIRE(loadedMap.outdoorTerrainTextureAtlas.has_value());

        size_t validTileCount = 0;

        for (const OpenYAMM::Game::OutdoorTerrainAtlasRegion &region :
             loadedMap.outdoorTerrainTextureAtlas->tileRegions)
        {
            if (region.isValid)
            {
                ++validTileCount;
            }
        }

        CHECK_GT(validTileCount, 0u);
    }
}

TEST_CASE("lua_event_runtime_has_complete_handler_inventory_for_every_scripted_map")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::vector<std::string> scriptedMapFileNames =
        collectScriptedMapFileNames(mapLoader.assetFileSystem, mapLoader.gameDataLoader);

    REQUIRE_FALSE(scriptedMapFileNames.empty());

    OpenYAMM::Game::GameDataLoader loader = mapLoader.gameDataLoader;

    for (const std::string &mapFileName : scriptedMapFileNames)
    {
        INFO(mapFileName);
        REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(mapLoader.assetFileSystem, mapFileName));

        const std::optional<OpenYAMM::Game::MapAssetInfo> &loadedMap = loader.getSelectedMap();
        REQUIRE(loadedMap.has_value());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeBindingReport report = {};

        REQUIRE(eventRuntime.validateProgramBindings(
            loadedMap->localEventProgram,
            loadedMap->globalEventProgram,
            report));
        CHECK(report.missingLocalHandlerEventIds.empty());
        CHECK(report.missingGlobalHandlerEventIds.empty());
        CHECK(report.missingCanShowTopicEventIds.empty());
        CHECK_FALSE(report.errorMessage.has_value());
    }
}

TEST_CASE("lua_event_runtime_executes_scripted_map_handlers_without_errors")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::vector<std::string> scriptedMapFileNames =
        collectScriptedMapFileNames(mapLoader.assetFileSystem, mapLoader.gameDataLoader);

    REQUIRE_FALSE(scriptedMapFileNames.empty());

    OpenYAMM::Game::GameDataLoader loader = mapLoader.gameDataLoader;
    bool executedGlobalHandlers = false;

    for (const std::string &mapFileName : scriptedMapFileNames)
    {
        INFO(mapFileName);
        REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(mapLoader.assetFileSystem, mapFileName));

        const std::optional<OpenYAMM::Game::MapAssetInfo> &loadedMap = loader.getSelectedMap();
        REQUIRE(loadedMap.has_value());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        const std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData =
            loadedMap->outdoorMapDeltaData ? loadedMap->outdoorMapDeltaData : loadedMap->indoorMapDeltaData;
        OpenYAMM::Game::EventRuntimeState baseState = {};

        REQUIRE(eventRuntime.buildOnLoadState(
            loadedMap->localEventProgram,
            loadedMap->globalEventProgram,
            mapDeltaData,
            baseState));

        if (!executedGlobalHandlers && loadedMap->globalEventProgram.has_value())
        {
            for (uint16_t eventId : loadedMap->globalEventProgram->eventIds())
            {
                INFO(eventId);
                OpenYAMM::Game::EventRuntimeState eventState = baseState;
                CHECK(eventRuntime.executeEventById(
                    std::nullopt,
                    loadedMap->globalEventProgram,
                    eventId,
                    eventState,
                    nullptr,
                    nullptr));
            }

            executedGlobalHandlers = true;
        }

        if (loadedMap->localEventProgram.has_value())
        {
            for (uint16_t eventId : loadedMap->localEventProgram->eventIds())
            {
                INFO(eventId);
                OpenYAMM::Game::EventRuntimeState eventState = baseState;
                CHECK(eventRuntime.executeEventById(
                    loadedMap->localEventProgram,
                    loadedMap->globalEventProgram,
                    eventId,
                    eventState,
                    nullptr,
                    nullptr));
            }
        }
    }
}

TEST_CASE("outdoor_scene_yml_matches_legacy_ddm_authored_state")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    static constexpr std::array<const char *, 4> RequiredMaps = {
        "out01.odm",
        "out02.odm",
        "out05.odm",
        "out13.odm",
    };

    for (const char *pMapFileName : RequiredMaps)
    {
        INFO(pMapFileName);

        OpenYAMM::Game::MapAssetInfo legacyMap = {};
        REQUIRE(loadOutdoorMapWithCompanionOptions(
            mapLoader.assetFileSystem,
            mapLoader.gameDataLoader,
            pMapFileName,
            OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = false,
                .allowLegacyCompanion = true,
            },
            legacyMap));

        OpenYAMM::Game::MapAssetInfo migratedMap = {};
        REQUIRE(loadOutdoorMapWithCompanionOptions(
            mapLoader.assetFileSystem,
            mapLoader.gameDataLoader,
            pMapFileName,
            OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = true,
                .allowLegacyCompanion = false,
            },
            migratedMap));

        CHECK_EQ(migratedMap.authoredCompanionSource, OpenYAMM::Game::AuthoredCompanionSource::SceneYml);

        const std::string legacySnapshot = buildNormalizedOutdoorAuthoredSnapshot(legacyMap);
        const std::string migratedSnapshot = buildNormalizedOutdoorAuthoredSnapshot(migratedMap);
        CHECK_MESSAGE(
            legacySnapshot == migratedSnapshot,
            "legacy and scene-authored outdoor state diverged");

        OpenYAMM::Game::MapAssetInfo mixedMap = {};
        REQUIRE(loadOutdoorMapWithCompanionOptions(
            mapLoader.assetFileSystem,
            mapLoader.gameDataLoader,
            pMapFileName,
            OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = true,
                .allowLegacyCompanion = true,
            },
            mixedMap));

        CHECK_EQ(mixedMap.authoredCompanionSource, OpenYAMM::Game::AuthoredCompanionSource::SceneYml);

        const std::string mixedSnapshot = buildNormalizedOutdoorAuthoredSnapshot(mixedMap);
        CHECK_MESSAGE(
            mixedSnapshot == migratedSnapshot,
            "mixed companion loading did not prefer the scene-authored state");
    }
}

TEST_CASE("outdoor_party_runtime_wait_advances_buff_durations_with_game_clock")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out01.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.outdoorMapData.has_value());

    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        *loadedMap.outdoorMapData,
        loadedMap.outdoorLandMask,
        loadedMap.outdoorDecorationCollisionSet,
        loadedMap.outdoorActorCollisionSet,
        loadedMap.outdoorSpriteObjectCollisionSet);
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(
        std::move(movementDriver),
        mapLoader.gameDataLoader.getItemTable());
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());
    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::FireResistance,
        36000.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);
    partyRuntime.setParty(party);
    partyRuntime.initialize(8704.0f, 2000.0f, 686.0f, false);

    const OpenYAMM::Game::PartyBuffState *pInitialBuff =
        partyRuntime.party().partyBuff(OpenYAMM::Game::PartyBuffId::FireResistance);
    REQUIRE(pInitialBuff != nullptr);
    CHECK(pInitialBuff->remainingSeconds == doctest::Approx(36000.0f));

    OpenYAMM::Game::OutdoorMovementInput idleInput = {};
    partyRuntime.update(idleInput, 2.0f);

    const OpenYAMM::Game::PartyBuffState *pUpdatedBuff =
        partyRuntime.party().partyBuff(OpenYAMM::Game::PartyBuffId::FireResistance);
    REQUIRE(pUpdatedBuff != nullptr);
    CHECK(pUpdatedBuff->remainingSeconds == doctest::Approx(35940.0f));
}
