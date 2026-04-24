#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/AudioSystem.h"
#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemRuntime.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/party/Party.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <cmath>
#include <filesystem>

namespace
{
struct SyntheticOutdoorWaterBoundaryScenario
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    float landX = 0.0f;
    float landY = 0.0f;
    float waterX = 0.0f;
    float waterY = 0.0f;
};

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
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

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadSyntheticScriptedProgram(
    const std::string &body,
    const std::string &chunkName,
    OpenYAMM::Game::ScriptedEventScope scope)
{
    std::string error;
    std::string luaSourceText = body;
    luaSourceText += "\n";
    luaSourceText += "evt.meta = evt.meta or {}\n";
    luaSourceText += "evt.meta.map = evt.meta.map or {}\n";
    luaSourceText += "evt.meta.global = evt.meta.global or {}\n";
    luaSourceText += "evt.meta.CanShowTopic = evt.meta.CanShowTopic or {}\n";

    const char *pScopeName = scope == OpenYAMM::Game::ScriptedEventScope::Global ? "global" : "map";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".onLoad = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".hint = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".summary = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".openedChestIds = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".textureNames = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".spriteNames = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".castSpellIds = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".timers = {}\n";

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(luaSourceText, chunkName, scope, error);
    INFO(error);
    return program;
}

std::optional<uint16_t> findSpecialEnchantId(
    const OpenYAMM::Game::SpecialItemEnchantTable &table,
    OpenYAMM::Game::SpecialItemEnchantKind kind)
{
    const std::vector<OpenYAMM::Game::SpecialItemEnchantEntry> &entries = table.entries();

    for (size_t index = 0; index < entries.size(); ++index)
    {
        if (entries[index].kind == kind)
        {
            return static_cast<uint16_t>(index + 1);
        }
    }

    return std::nullopt;
}

uint32_t findFirstItemIdBySkillGroup(const OpenYAMM::Game::ItemTable &itemTable, const std::string &skillGroup)
{
    for (const OpenYAMM::Game::ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId != 0 && entry.skillGroup == skillGroup)
        {
            return entry.itemId;
        }
    }

    return 0;
}

bool isOutdoorLandMaskWaterForDiagnostics(
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    if (!outdoorLandMask || outdoorLandMask->empty())
    {
        return false;
    }

    const float gridX = OpenYAMM::Game::outdoorWorldToGridXFloat(x);
    const float gridY = OpenYAMM::Game::outdoorWorldToGridYFloat(y);
    const int tileX = std::clamp(
        static_cast<int>(std::floor(gridX)),
        0,
        OpenYAMM::Game::OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(
        static_cast<int>(std::floor(gridY)),
        0,
        OpenYAMM::Game::OutdoorMapData::TerrainHeight - 2);
    const int landMaskWidth = OpenYAMM::Game::OutdoorMapData::TerrainWidth - 1;
    const size_t tileIndex = static_cast<size_t>(tileY * landMaskWidth + tileX);

    if (tileIndex >= outdoorLandMask->size())
    {
        return false;
    }

    return (*outdoorLandMask)[tileIndex] == 0;
}

bool isOutdoorPositionWaterForDiagnostics(
    const OpenYAMM::Game::OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    return OpenYAMM::Game::isOutdoorTerrainWater(outdoorMapData, x, y)
        || isOutdoorLandMaskWaterForDiagnostics(outdoorLandMask, x, y);
}

SyntheticOutdoorWaterBoundaryScenario createSyntheticOutdoorWaterBoundaryScenario()
{
    SyntheticOutdoorWaterBoundaryScenario scenario = {};
    scenario.mapData.heightMap.resize(
        static_cast<size_t>(
            OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight),
        0);
    scenario.mapData.attributeMap.resize(
        static_cast<size_t>(
            OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight),
        0);

    const int landTileX = 63;
    const int landTileY = 63;
    const int waterTileX = 62;
    const int waterTileY = 63;
    const size_t waterTileIndex =
        static_cast<size_t>(waterTileY * OpenYAMM::Game::OutdoorMapData::TerrainWidth + waterTileX);

    if (waterTileIndex < scenario.mapData.attributeMap.size())
    {
        scenario.mapData.attributeMap[waterTileIndex] = 0x02;
    }

    const float halfTile = static_cast<float>(OpenYAMM::Game::OutdoorMapData::TerrainTileSize) * 0.5f;

    const auto tileCenter =
        [halfTile](int tileX, int tileY) -> std::pair<float, float>
    {
        const float worldX = OpenYAMM::Game::outdoorGridCornerWorldX(tileX) + halfTile;
        const float worldY = OpenYAMM::Game::outdoorGridCornerWorldY(tileY) - halfTile;
        return {worldX, worldY};
    };

    const auto [landX, landY] = tileCenter(landTileX, landTileY);
    const auto [waterX, waterY] = tileCenter(waterTileX, waterTileY);
    scenario.landX = landX;
    scenario.landY = landY;
    scenario.waterX = waterX;
    scenario.waterY = waterY;
    return scenario;
}

bool initializeTestAssetFileSystem(OpenYAMM::Engine::AssetFileSystem &assetFileSystem)
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";
    return assetFileSystem.initialize(sourceRoot, assetsRoot, OpenYAMM::Engine::AssetScaleTier::X1);
}
}

TEST_CASE("party ground movement blocks water entry without water walk")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementController movementController(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = movementController.initializeState(boundary.landX, boundary.landY, 0.0f);
    const float moveVelocityX = (boundary.waterX - boundary.landX) * 2.0f;
    const float moveVelocityY = (boundary.waterY - boundary.landY) * 2.0f;
    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        moveVelocityX,
        moveVelocityY,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        0.5f);

    CHECK_FALSE(resolved.supportOnWater);
    CHECK_FALSE(isOutdoorPositionWaterForDiagnostics(boundary.mapData, std::nullopt, resolved.x, resolved.y));
}

TEST_CASE("party airborne movement allows water entry without water walk")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementController movementController(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = movementController.initializeState(boundary.landX, boundary.landY, 0.0f);
    state.footZ += 64.0f;
    state.airborne = true;
    state.verticalVelocity = 0.0f;
    state.fallStartZ = state.footZ;

    const float moveVelocityX = (boundary.waterX - boundary.landX) * 2.0f;
    const float moveVelocityY = (boundary.waterY - boundary.landY) * 2.0f;
    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        moveVelocityX,
        moveVelocityY,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        0.5f);

    CHECK(isOutdoorPositionWaterForDiagnostics(boundary.mapData, std::nullopt, resolved.x, resolved.y));
}

TEST_CASE("recovery enchant increases recovery progress")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const std::optional<uint16_t> recoveryEnchantId = findSpecialEnchantId(
        gameData.specialItemEnchantTable,
        OpenYAMM::Game::SpecialItemEnchantKind::Recovery);
    REQUIRE(recoveryEnchantId.has_value());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    const OpenYAMM::Game::ItemDefinition *pRingDefinition = gameData.itemTable.get(137);
    REQUIRE(pMember != nullptr);
    REQUIRE(pRingDefinition != nullptr);

    OpenYAMM::Game::InventoryItem enchantedRing = {
        pRingDefinition->itemId,
        1,
        pRingDefinition->inventoryWidth,
        pRingDefinition->inventoryHeight,
        0,
        0,
        true,
        false,
        false,
        0,
        0,
        *recoveryEnchantId,
        0
    };
    std::optional<OpenYAMM::Game::InventoryItem> heldReplacement;

    REQUIRE(party.tryEquipItemOnMember(
        0,
        OpenYAMM::Game::EquipmentSlot::Ring1,
        enchantedRing,
        std::nullopt,
        false,
        heldReplacement));

    CHECK(std::abs(pMember->recoveryProgressMultiplier - 1.5f) < 0.001f);

    pMember->recoverySecondsRemaining = 2.0f;
    party.updateRecovery(1.0f);

    CHECK(std::abs(pMember->recoverySecondsRemaining - 0.5f) < 0.001f);
}

TEST_CASE("event experience variable awards direct member experience without learning bonus")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pFirst = party.member(0);
    OpenYAMM::Game::Character *pSecond = party.member(1);
    REQUIRE(pFirst != nullptr);
    REQUIRE(pSecond != nullptr);

    pFirst->skills["Learning"] = {"Learning", 10, OpenYAMM::Game::SkillMastery::Grandmaster};
    pSecond->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead));

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(5)\n"
        "    evt.Add(13, 50)\n"
        "    return\n"
        "end\n",
        "@SyntheticExperience.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    CHECK_EQ(pFirst->experience, 50u);
    CHECK_EQ(pSecond->experience, 50u);
}

TEST_CASE("lua event runtime supports evt jump alias")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.Jump(90, 0, 10)\n"
        "    evt.StatusText(\"jump ok\")\n"
        "    return\n"
        "end\n",
        "@SyntheticJump.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "jump ok");
}

TEST_CASE("lua event runtime treats explicit hint-only events as handled no-ops")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        "evt.meta.map.hint = {[42] = \"Bookshelf\"}\n"
        "evt.meta.map.summary = {[42] = \"Bookshelf\"}\n",
        "@SyntheticHintOnlyEvent.lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        error);
    REQUIRE(scriptedProgram.has_value());
    CHECK(scriptedProgram->isHintOnlyEvent(42));

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    CHECK(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 42, runtimeState, nullptr, nullptr));
}

TEST_CASE("event runtime caches facet invisible override state")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const uint32_t invisibleBit = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);

    runtimeState.facetSetMasks[12] = invisibleBit;
    CHECK(runtimeState.hasFacetInvisibleOverride(12));
    CHECK_FALSE(runtimeState.hasFacetInvisibleOverride(13));

    runtimeState.facetClearMasks[12] = invisibleBit;
    ++runtimeState.outdoorSurfaceRevision;
    CHECK_FALSE(runtimeState.hasFacetInvisibleOverride(12));

    runtimeState.facetClearMasks.erase(12);
    ++runtimeState.outdoorSurfaceRevision;
    CHECK(runtimeState.hasFacetInvisibleOverride(12));
}

TEST_CASE("resolve character attack sound id uses shared weapon family mapping")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ItemTable &itemTable = gameData.itemTable;

    OpenYAMM::Game::Character character = {};
    const uint32_t swordId = findFirstItemIdBySkillGroup(itemTable, "Sword");
    const uint32_t daggerId = findFirstItemIdBySkillGroup(itemTable, "Dagger");
    const uint32_t axeId = findFirstItemIdBySkillGroup(itemTable, "Axe");
    const uint32_t spearId = findFirstItemIdBySkillGroup(itemTable, "Spear");
    const uint32_t maceId = findFirstItemIdBySkillGroup(itemTable, "Mace");

    REQUIRE_NE(swordId, 0u);
    REQUIRE_NE(daggerId, 0u);
    REQUIRE_NE(axeId, 0u);
    REQUIRE_NE(spearId, 0u);
    REQUIRE_NE(maceId, 0u);

    character.equipment.mainHand = swordId;
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Melee),
        OpenYAMM::Game::SoundId::SwingSword01);

    character.equipment.mainHand = daggerId;
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Melee),
        OpenYAMM::Game::SoundId::SwingSword02);

    character.equipment.mainHand = axeId;
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Melee),
        OpenYAMM::Game::SoundId::SwingAxe01);

    character.equipment.mainHand = spearId;
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Melee),
        OpenYAMM::Game::SoundId::SwingAxe03);

    character.equipment.mainHand = maceId;
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Melee),
        OpenYAMM::Game::SoundId::SwingBlunt03);

    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Bow),
        OpenYAMM::Game::SoundId::ShootBow);
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::Blaster),
        OpenYAMM::Game::SoundId::ShootBlaster);
}

TEST_CASE("audio shutdown remains safe after SDL quit")
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();
    REQUIRE(pEnvironment != nullptr);
    REQUIRE(SDL_SetEnvironmentVariable(pEnvironment, "SDL_AUDIODRIVER", "dummy", true));

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(initializeTestAssetFileSystem(assetFileSystem));

    OpenYAMM::Engine::AudioSystem audioSystem;
    REQUIRE(audioSystem.initialize(assetFileSystem));

    SDL_Quit();
    audioSystem.shutdown();
    CHECK(SDL_Init(0));
}
