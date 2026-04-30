#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorService.h"
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

bool loadIndoorMapWithCompanionOptions(
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

    if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData)
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

TEST_CASE("d19 blv MoveNPC updates party global npc house overrides")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapStatsEntry *pMapEntry =
        mapLoader.gameDataLoader.getMapStats().findByFileName("d19.blv");
    const std::optional<std::string> supportLua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> d19Lua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/maps/d19.lua");

    REQUIRE(pMapEntry != nullptr);
    REQUIRE(supportLua.has_value());
    REQUIRE(d19Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *d19Lua,
            "@Data/scripts/maps/d19.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());
    party.setQuestBit(19, true);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        6,
        runtimeState,
        &party));

    CHECK_EQ(runtimeState.npcHouseOverrides[9], 0u);
    CHECK_EQ(runtimeState.npcHouseOverrides[69], 175u);
    CHECK_EQ(runtimeState.npcHouseOverrides[76], 180u);

    OpenYAMM::Game::EventRuntimeState seededRuntimeState = {};
    party.applyGlobalNpcStateTo(seededRuntimeState);

    CHECK_EQ(seededRuntimeState.npcHouseOverrides[9], 0u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[69], 175u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[76], 180u);
}

TEST_CASE("d16 on-leave events move allied dragon hunters before map exit")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::optional<std::string> supportLua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> d16Lua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/maps/d16.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(d16Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *d16Lua,
            "@Data/scripts/maps/d16.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
    REQUIRE_EQ(localEventProgram->onLeaveEventIds().size(), 5u);
    CHECK_EQ(localEventProgram->onLeaveEventIds()[0], 6u);
    CHECK_EQ(localEventProgram->onLeaveEventIds()[4], 10u);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());
    party.setQuestBit(21, true);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeOnLeaveEvents(localEventProgram, std::nullopt, runtimeState, &party));

    CHECK_EQ(runtimeState.npcHouseOverrides[19], 0u);
    CHECK_EQ(runtimeState.npcHouseOverrides[65], 175u);
    CHECK_EQ(runtimeState.npcHouseOverrides[64], 179u);

    OpenYAMM::Game::EventRuntimeState seededRuntimeState = {};
    party.applyGlobalNpcStateTo(seededRuntimeState);

    CHECK_EQ(seededRuntimeState.npcHouseOverrides[19], 0u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[65], 175u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[64], 179u);
}

TEST_CASE("out05 authored special actors preserve relation override and carried item")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out05.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.outdoorMapDeltaData.has_value());
    REQUIRE_GT(loadedMap.outdoorMapDeltaData->actors.size(), 3u);

    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[0].monsterInfoId, 72);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[0].uniqueNameIndex, 3);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[0].ally, 15u);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[1].ally, 15u);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[2].ally, 15u);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[3].monsterInfoId, 45);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[3].uniqueNameIndex, 2);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[3].carriedItemId, 540u);

    OpenYAMM::Game::GameplayActorService actorService = {};
    actorService.bindTables(&mapLoader.gameDataLoader.getMonsterTable(), &mapLoader.gameDataLoader.getSpellTable());

    OpenYAMM::Game::GameplayActorTargetPolicyState dragonslayer = {};
    dragonslayer.monsterId = 45;
    dragonslayer.relationMonsterId = actorService.relationMonsterId(dragonslayer.monsterId, 15);
    dragonslayer.height = 160;

    OpenYAMM::Game::GameplayActorTargetPolicyState pet = {};
    pet.monsterId = 72;
    pet.relationMonsterId = actorService.relationMonsterId(pet.monsterId, 15);
    pet.height = 500;

    CHECK_GT(mapLoader.gameDataLoader.getMonsterTable().getRelationBetweenMonsters(45, 72), 0);
    CHECK_FALSE(actorService.resolveActorTargetPolicy(dragonslayer, pet).canTarget);

    OpenYAMM::Game::GameplayActorTargetPolicyState naturalDragonslayer = dragonslayer;
    naturalDragonslayer.relationMonsterId =
        actorService.relationMonsterId(naturalDragonslayer.monsterId, 0);

    OpenYAMM::Game::GameplayActorTargetPolicyState naturalDragon = pet;
    naturalDragon.relationMonsterId = actorService.relationMonsterId(naturalDragon.monsterId, 0);

    CHECK(actorService.resolveActorTargetPolicy(naturalDragonslayer, naturalDragon).canTarget);
    CHECK_FALSE(actorService.resolveActorTargetPolicy(naturalDragon, naturalDragonslayer).canTarget);

    naturalDragonslayer.group = 24;
    naturalDragon.group = 24;
    CHECK_FALSE(actorService.resolveActorTargetPolicy(naturalDragonslayer, naturalDragon).canTarget);
}

TEST_CASE("d06 indoor actor loader preserves Blackwell Cooper guaranteed key drop")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "d06.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = false,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.indoorMapDeltaData.has_value());
    REQUIRE_GT(loadedMap.indoorMapDeltaData->actors.size(), 0u);

    const OpenYAMM::Game::MapDeltaActor &blackwell = loadedMap.indoorMapDeltaData->actors[0];
    CHECK_EQ(blackwell.uniqueNameIndex, 1);
    CHECK_EQ(blackwell.sectorId, 11);
    CHECK_EQ(blackwell.carriedItemId, 619u);

    OpenYAMM::Game::MapAssetInfo sceneLoadedMap = {};
    REQUIRE(loadIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "d06.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        sceneLoadedMap));
    REQUIRE(sceneLoadedMap.indoorMapDeltaData.has_value());
    REQUIRE_GT(sceneLoadedMap.indoorMapDeltaData->actors.size(), 0u);
    CHECK_EQ(sceneLoadedMap.indoorMapDeltaData->actors[0].carriedItemId, 619u);
}

TEST_CASE("d06 submarine event plays cutscene and moves to small sub pen")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::optional<std::string> supportLua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> d06Lua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/maps/d06.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(d06Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *d06Lua,
            "@Data/scripts/maps/d06.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::InventoryItem pirateLeaderKey = {};
    pirateLeaderKey.objectDescriptionId = 619;
    REQUIRE(party.tryGrantInventoryItem(pirateLeaderKey));

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, runtimeState, &party, nullptr));
    REQUIRE(runtimeState.pendingMovie.has_value());
    CHECK_EQ(runtimeState.pendingMovie->movieName, "\"Subcut\" ");
    CHECK(runtimeState.pendingMovie->restoreAfterPlayback);
    REQUIRE(runtimeState.pendingMapMove.has_value());
    CHECK_EQ(runtimeState.pendingMapMove->mapName, std::optional<std::string>("D34.blv"));
    CHECK_EQ(runtimeState.pendingMapMove->x, -2416);
    CHECK_EQ(runtimeState.pendingMapMove->y, 1850);
    CHECK_EQ(runtimeState.pendingMapMove->z, -687);
}

TEST_CASE("corpse loot includes authored guaranteed carried item")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MonsterTable::LootPrototype noRandomLoot = {};

    const OpenYAMM::Game::GameplayCorpseViewState corpse = OpenYAMM::Game::buildMonsterCorpseView(
        "Jeric Whistlebone",
        noRandomLoot,
        &mapLoader.gameDataLoader.getItemTable(),
        nullptr,
        540);

    REQUIRE_EQ(corpse.items.size(), 1u);
    CHECK_EQ(corpse.items.front().itemId, 540u);
    CHECK_EQ(corpse.items.front().item.objectDescriptionId, 540u);
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
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
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
