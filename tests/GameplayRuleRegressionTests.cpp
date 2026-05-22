#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/AudioSystem.h"
#include "engine/TextTable.h"
#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayWorldItemInteraction.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/items/InventoryItemMixingRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"
#include "game/tables/SurfaceMaterialTable.h"

#include "tests/RegressionGameData.h"
#include "tests/PartySpellTestHarness.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <utility>
#include <vector>

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

class CorpseLootTestWorldRuntime : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    OpenYAMM::Game::GameplayCorpseViewState corpseView = {};
    std::vector<OpenYAMM::Game::GameplayHeldItemDropRequest> dropRequests;
    bool activeCorpse = true;
    bool allowDrop = true;

    std::optional<OpenYAMM::Game::GameplayHeldItemDropRequest> buildHeldItemDropRequest() const override
    {
        return OpenYAMM::Game::GameplayHeldItemDropRequest{
            .sourceX = 100.0f,
            .sourceY = 200.0f,
            .sourceZ = 300.0f,
            .yawRadians = 1.0f,
        };
    }

    bool dropHeldItemToWorld(const OpenYAMM::Game::GameplayHeldItemDropRequest &request) override
    {
        if (!allowDrop)
        {
            return false;
        }

        dropRequests.push_back(request);
        return true;
    }

    OpenYAMM::Game::GameplayCorpseViewState *activeCorpseView() override
    {
        return activeCorpse ? &corpseView : nullptr;
    }

    const OpenYAMM::Game::GameplayCorpseViewState *activeCorpseView() const override
    {
        return activeCorpse ? &corpseView : nullptr;
    }

    bool takeActiveCorpseItem(size_t itemIndex, OpenYAMM::Game::GameplayChestItemState &item) override
    {
        if (!activeCorpse || itemIndex >= corpseView.items.size())
        {
            return false;
        }

        item = corpseView.items[itemIndex];
        corpseView.items.erase(corpseView.items.begin() + static_cast<ptrdiff_t>(itemIndex));

        if (corpseView.items.empty())
        {
            activeCorpse = false;
        }

        return true;
    }

    void closeActiveCorpseView() override
    {
        activeCorpse = false;
    }
};

class MonsterSpecialAttackTestWorldRuntime : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    std::optional<OpenYAMM::Game::GameplayCombatActorInfo> actorInfo;

    std::optional<OpenYAMM::Game::GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override
    {
        if (actorInfo && actorInfo->actorId == actorId)
        {
            return actorInfo;
        }

        return std::nullopt;
    }
};

OpenYAMM::Game::Party makeMonsterSpecialAttackTestParty()
{
    OpenYAMM::Game::Character member =
        OpenYAMM::Tests::makeSpellRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    member.might = 1;
    member.intellect = 1;
    member.personality = 1;
    member.endurance = 1;
    member.speed = 1;
    member.accuracy = 1;
    member.luck = 1;
    member.maxHealth = 100;
    member.health = 100;

    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(member);

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    party.setActiveMemberIndex(0);
    return party;
}

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

std::string loadSourceFileText(const std::string &relativePath)
{
    const std::filesystem::path path = std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath;
    std::ifstream file(path);
    REQUIRE(file.good());
    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}

std::vector<std::vector<std::string>> loadSourceTabSeparatedRows(const std::string &relativePath)
{
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(loadSourceFileText(relativePath));
    REQUIRE(table.has_value());

    std::vector<std::vector<std::string>> rows;
    rows.reserve(table->getRowCount());

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return rows;
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

OpenYAMM::Game::InventoryItem makeTestInventoryItem(uint32_t itemId, uint8_t width = 1, uint8_t height = 1)
{
    OpenYAMM::Game::InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    item.width = width;
    item.height = height;
    return item;
}

OpenYAMM::Game::GameplayChestItemState makeTestCorpseItem(
    uint32_t itemId,
    uint8_t width = 1,
    uint8_t height = 1)
{
    OpenYAMM::Game::InventoryItem inventoryItem = makeTestInventoryItem(itemId, width, height);
    OpenYAMM::Game::GameplayChestItemState corpseItem = {};
    corpseItem.item = inventoryItem;
    corpseItem.itemId = itemId;
    corpseItem.quantity = 1;
    corpseItem.width = width;
    corpseItem.height = height;
    return corpseItem;
}

void fillMemberInventory(OpenYAMM::Game::Party &party, size_t memberIndex, uint32_t firstItemId)
{
    OpenYAMM::Game::Character *pMember = party.member(memberIndex);
    REQUIRE(pMember != nullptr);
    pMember->inventory.clear();

    uint32_t itemId = firstItemId;

    for (uint8_t y = 0; y < OpenYAMM::Game::Character::InventoryHeight; ++y)
    {
        for (uint8_t x = 0; x < OpenYAMM::Game::Character::InventoryWidth; ++x)
        {
            REQUIRE(pMember->addInventoryItemAt(makeTestInventoryItem(itemId++), x, y));
        }
    }
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadSyntheticScriptedProgram(
    const std::string &body,
    const std::string &chunkName,
    OpenYAMM::Game::ScriptedEventScope scope,
    const std::vector<uint16_t> &onLoadEventIds = {})
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
    luaSourceText += ".onLoad = {";

    for (size_t index = 0; index < onLoadEventIds.size(); ++index)
    {
        if (index != 0)
        {
            luaSourceText += ", ";
        }

        luaSourceText += std::to_string(onLoadEventIds[index]);
    }

    luaSourceText += "}\n";
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

TEST_CASE("outdoor water damage tick reports drowning status text")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(std::move(movementDriver), itemTable);
    partyRuntime.initialize(boundary.waterX, boundary.waterY, 0.0f, true);

    partyRuntime.update(OpenYAMM::Game::OutdoorMovementInput{}, 1.0f);

    CHECK_EQ(partyRuntime.party().waterDamageTicks(), 1u);
    CHECK_EQ(partyRuntime.party().lastStatus(), "water damage");
    CHECK_EQ(partyRuntime.movementStatusText(), "You are drowning!");
}

TEST_CASE("outdoor water landing still applies fall damage")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementController movementController(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(std::move(movementDriver), itemTable);
    partyRuntime.initialize(boundary.waterX, boundary.waterY, 0.0f, true);

    OpenYAMM::Game::OutdoorPartyRuntime::Snapshot snapshot = partyRuntime.snapshot();
    snapshot.movementState = movementController.initializeState(boundary.waterX, boundary.waterY, 0.0f);
    snapshot.movementState.footZ += 768.0f;
    snapshot.movementState.airborne = true;
    snapshot.movementState.verticalVelocity = 0.0f;
    snapshot.movementState.fallStartZ = snapshot.movementState.footZ;
    snapshot.movementState.supportOnWater = false;
    snapshot.partyMovementState = {};
    partyRuntime.restoreSnapshot(snapshot);

    const int initialHealth = partyRuntime.party().totalHealth();

    for (int i = 0; i < 80 && partyRuntime.party().lastFallDamageDistance() <= 0.0f; ++i)
    {
        partyRuntime.update(OpenYAMM::Game::OutdoorMovementInput{}, 0.1f);
    }

    CHECK(partyRuntime.movementState().supportOnWater);
    CHECK_GT(partyRuntime.party().lastFallDamageDistance(), 512.0f);
    CHECK_LT(partyRuntime.party().totalHealth(), initialHealth);
}

TEST_CASE("classic outdoor flying ignores camera pitch for forward movement")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    movementDriver.initialize(boundary.landX, boundary.landY, 0.0f);
    movementDriver.setFlyingAvailable(true);
    movementDriver.setFlying(true);
    const float startFootZ = movementDriver.state().footZ;

    OpenYAMM::Game::OutdoorMovementInput movementInput = {};
    movementInput.forward = true;
    movementInput.pitchRadians = 0.75f;
    movementInput.usePitchForFlyingMovement = false;
    movementDriver.update(movementInput, 0.1f);

    CHECK_EQ(movementDriver.state().footZ, doctest::Approx(startFootZ).epsilon(0.001f));
}

TEST_CASE("modern outdoor flying keeps camera pitch for forward movement")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    movementDriver.initialize(boundary.landX, boundary.landY, 0.0f);
    movementDriver.setFlyingAvailable(true);
    movementDriver.setFlying(true);
    const float startFootZ = movementDriver.state().footZ;

    OpenYAMM::Game::OutdoorMovementInput movementInput = {};
    movementInput.forward = true;
    movementInput.pitchRadians = 0.75f;
    movementInput.usePitchForFlyingMovement = true;
    movementDriver.update(movementInput, 0.1f);

    CHECK_GT(movementDriver.state().footZ, startFootZ);
}

TEST_CASE("outdoor terrain descriptors expose liquid flags for non-default tilesets")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(initializeTestAssetFileSystem(assetFileSystem));

    OpenYAMM::Game::OutdoorMapData ironsand = {};
    ironsand.fileName = "out04.odm";
    ironsand.masterTile = 1;
    ironsand.tileSetLookupIndices = {594, 558, 450, 522};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> ironsandDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, ironsand);
    REQUIRE(ironsandDescriptors.has_value());
    CHECK((*ironsandDescriptors)[1].textureName == "plntyl");
    CHECK((*ironsandDescriptors)[126].textureName == "lavtyl");
    CHECK(((*ironsandDescriptors)[126].flags & OpenYAMM::Game::TerrainTileFlagWater) != 0);
    CHECK(((*ironsandDescriptors)[126].flags & OpenYAMM::Game::TerrainTileFlagBurn) != 0);

    const std::filesystem::path ironsandScenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out04.scene.yml";
    std::ifstream ironsandSceneFile(ironsandScenePath);
    REQUIRE(ironsandSceneFile.good());
    std::ostringstream ironsandSceneText;
    ironsandSceneText << ironsandSceneFile.rdbuf();

    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OpenYAMM::Game::OutdoorSceneData> ironsandScene =
        sceneLoader.loadFromText(ironsandSceneText.str(), sceneError);
    REQUIRE_MESSAGE(ironsandScene.has_value(), sceneError.c_str());
    OpenYAMM::Game::OutdoorSceneData mergedIronsandScene = *ironsandScene;

    const std::filesystem::path ironsandOverlayPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out04_1.scene.yml";
    std::ifstream ironsandOverlayFile(ironsandOverlayPath);
    REQUIRE(ironsandOverlayFile.good());
    std::ostringstream ironsandOverlayText;
    ironsandOverlayText << ironsandOverlayFile.rdbuf();
    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedIronsandScene, ironsandOverlayText.str(), sceneError),
        sceneError.c_str());
    CHECK(mergedIronsandScene.environment.flags.foggy);
    CHECK(mergedIronsandScene.environment.flags.alwaysFoggy);
    CHECK_EQ(mergedIronsandScene.environment.dayBitsRaw, 0x01);
    CHECK_EQ(mergedIronsandScene.environment.mapExtraBitsRaw, 0x40u);
    CHECK_EQ(mergedIronsandScene.environment.fogWeakDistance, 0);
    CHECK_EQ(mergedIronsandScene.environment.fogStrongDistance, 4096);
    REQUIRE_EQ(mergedIronsandScene.terrainFootstepSoundOverrides.size(), 72u);
    CHECK_EQ(mergedIronsandScene.terrainFootstepSoundOverrides.front().tileId, 90);
    CHECK_EQ(mergedIronsandScene.terrainFootstepSoundOverrides.front().walkSoundId, 91u);
    CHECK_EQ(mergedIronsandScene.terrainFootstepSoundOverrides.front().runSoundId, 52u);
    const auto ironsandLavaOverride = std::find_if(
        mergedIronsandScene.terrainFootstepSoundOverrides.begin(),
        mergedIronsandScene.terrainFootstepSoundOverrides.end(),
        [](const OpenYAMM::Game::OutdoorSceneTerrainFootstepSoundOverride &overrideEntry)
        {
            return overrideEntry.tileId == 126;
        });
    REQUIRE(ironsandLavaOverride != mergedIronsandScene.terrainFootstepSoundOverrides.end());
    CHECK_EQ(ironsandLavaOverride->walkSoundId, 101u);
    CHECK_EQ(ironsandLavaOverride->runSoundId, 62u);
    const auto ironsandDefaultOverride = std::find_if(
        mergedIronsandScene.terrainFootstepSoundOverrides.begin(),
        mergedIronsandScene.terrainFootstepSoundOverrides.end(),
        [](const OpenYAMM::Game::OutdoorSceneTerrainFootstepSoundOverride &overrideEntry)
        {
            return overrideEntry.tileId == 162;
        });
    REQUIRE(ironsandDefaultOverride != mergedIronsandScene.terrainFootstepSoundOverrides.end());
    CHECK_EQ(ironsandDefaultOverride->walkSoundId, 90u);
    CHECK_EQ(ironsandDefaultOverride->runSoundId, 51u);

    OpenYAMM::Game::OutdoorMapData shadowspire = {};
    shadowspire.fileName = "out06.odm";
    shadowspire.masterTile = 2;
    shadowspire.tileSetLookupIndices = {702, 738, 666, 774};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> shadowspireDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, shadowspire);
    REQUIRE(shadowspireDescriptors.has_value());
    CHECK((*shadowspireDescriptors)[1].textureName == "gdtyl");
    CHECK((*shadowspireDescriptors)[162].textureName == "tartyl");
    CHECK(((*shadowspireDescriptors)[162].flags & OpenYAMM::Game::TerrainTileFlagWater) != 0);
    CHECK(((*shadowspireDescriptors)[162].flags & OpenYAMM::Game::TerrainTileFlagBurn) == 0);
    CHECK((*shadowspireDescriptors)[174].textureName == "trne");
    CHECK(((*shadowspireDescriptors)[174].flags & OpenYAMM::Game::TerrainTileFlagTransition) != 0);

    const std::filesystem::path shadowspireScenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out06.scene.yml";
    std::ifstream shadowspireSceneFile(shadowspireScenePath);
    REQUIRE(shadowspireSceneFile.good());
    std::ostringstream shadowspireSceneText;
    shadowspireSceneText << shadowspireSceneFile.rdbuf();

    const std::optional<OpenYAMM::Game::OutdoorSceneData> shadowspireScene =
        sceneLoader.loadFromText(shadowspireSceneText.str(), sceneError);
    REQUIRE_MESSAGE(shadowspireScene.has_value(), sceneError.c_str());
    OpenYAMM::Game::OutdoorSceneData mergedShadowspireScene = *shadowspireScene;

    const std::filesystem::path shadowspireOverlayPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out06_1.scene.yml";
    std::ifstream shadowspireOverlayFile(shadowspireOverlayPath);
    REQUIRE(shadowspireOverlayFile.good());
    std::ostringstream shadowspireOverlayText;
    shadowspireOverlayText << shadowspireOverlayFile.rdbuf();
    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedShadowspireScene, shadowspireOverlayText.str(), sceneError),
        sceneError.c_str());
    REQUIRE_EQ(mergedShadowspireScene.terrainFootstepSoundOverrides.size(), 12u);
    CHECK_EQ(mergedShadowspireScene.terrainFootstepSoundOverrides.front().tileId, 1);
    CHECK_EQ(mergedShadowspireScene.terrainFootstepSoundOverrides.front().walkSoundId, 101u);
    CHECK_EQ(mergedShadowspireScene.terrainFootstepSoundOverrides.front().runSoundId, 62u);
}

TEST_CASE("outdoor scene overlays apply partial environment flags")
{
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;

    const std::filesystem::path scenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out06.scene.yml";
    std::ifstream sceneFile(scenePath);
    REQUIRE(sceneFile.good());
    std::ostringstream sceneText;
    sceneText << sceneFile.rdbuf();

    const std::optional<OpenYAMM::Game::OutdoorSceneData> scene =
        sceneLoader.loadFromText(sceneText.str(), sceneError);
    REQUIRE_MESSAGE(scene.has_value(), sceneError.c_str());

    OpenYAMM::Game::OutdoorSceneData mergedScene = *scene;
    const std::string overlayText =
        "format_version: 1\n"
        "kind: outdoor_scene_overlay\n"
        "environment:\n"
        "  flags:\n"
        "    foggy: true\n"
        "    underwater: true\n"
        "    always_foggy: true\n"
        "    red_fog: true\n"
        "  fog:\n"
        "    weak_distance: 128\n"
        "    strong_distance: 2048\n";

    REQUIRE_MESSAGE(sceneLoader.applyOverlayFromText(mergedScene, overlayText, sceneError), sceneError.c_str());
    CHECK(mergedScene.environment.flags.foggy);
    CHECK(mergedScene.environment.flags.underwater);
    CHECK(mergedScene.environment.flags.alwaysFoggy);
    CHECK(mergedScene.environment.flags.redFog);
    CHECK_EQ(mergedScene.environment.dayBitsRaw, 0x01);
    CHECK_EQ(mergedScene.environment.mapExtraBitsRaw, 0xc4u);
    CHECK_EQ(mergedScene.environment.fogWeakDistance, 128);
    CHECK_EQ(mergedScene.environment.fogStrongDistance, 2048);
}

TEST_CASE("outdoor scene overlays can override actor NPC ids")
{
    const auto loadText =
        [](const std::filesystem::path &path)
        {
            std::ifstream file(path);
            REQUIRE(file.good());
            std::ostringstream text;
            text << file.rdbuf();
            return text.str();
        };

    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::filesystem::path scenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/out01.scene.yml";

    const std::optional<OpenYAMM::Game::OutdoorSceneData> scene =
        sceneLoader.loadFromText(loadText(scenePath), sceneError);
    REQUIRE_MESSAGE(scene.has_value(), sceneError.c_str());
    REQUIRE_FALSE(scene->initialState.actors.empty());
    CHECK_EQ(scene->initialState.actors.front().npcId, 27);

    OpenYAMM::Game::OutdoorSceneData mergedScene = *scene;
    const std::string overlayText =
        "format_version: 1\n"
        "kind: outdoor_scene_overlay\n"
        "initial_state:\n"
        "  actor_npc_id_overrides:\n"
        "    - actor_index: 0\n"
        "      npc_id: 31\n";

    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedScene, overlayText, sceneError),
        sceneError.c_str());
    REQUIRE_FALSE(mergedScene.initialState.actors.empty());
    CHECK_EQ(mergedScene.initialState.actors.front().npcId, 31);
}

TEST_CASE("map decoration names take precedence over legacy decoration ids")
{
    OpenYAMM::Game::DecorationTable decorationTable;
    REQUIRE(decorationTable.loadRows(loadSourceTabSeparatedRows("assets_dev/engine/data_tables/decoration_data.txt")));

    const OpenYAMM::Game::DecorationLookupResult smoke =
        decorationTable.resolveMapDecoration(13, "smoke");
    REQUIRE(smoke.pEntry != nullptr);
    CHECK_EQ(smoke.decorationId, 22);
    CHECK_EQ(smoke.pEntry->internalName, "smoke");
    CHECK((smoke.pEntry->flags & static_cast<uint16_t>(OpenYAMM::Game::DecorationDescFlag::EmitSmoke)) != 0);

    const OpenYAMM::Game::DecorationLookupResult partyStart =
        decorationTable.resolveMapDecoration(13, "Party Start");
    REQUIRE(partyStart.pEntry != nullptr);
    CHECK_EQ(partyStart.decorationId, 14);
    CHECK_EQ(partyStart.pEntry->internalName, "party start");
    CHECK((partyStart.pEntry->flags & static_cast<uint16_t>(OpenYAMM::Game::DecorationDescFlag::DontDraw)) != 0);

    const OpenYAMM::Game::DecorationLookupResult fallback =
        decorationTable.resolveMapDecoration(13, "missing-decoration-name");
    REQUIRE(fallback.pEntry != nullptr);
    CHECK_EQ(fallback.decorationId, 13);
    CHECK_EQ(fallback.pEntry->internalName, "pending");

    const OpenYAMM::Game::DecorationLookupResult mm7BeaconFire =
        decorationTable.resolveMapDecoration(305, "dec61");
    REQUIRE(mm7BeaconFire.pEntry != nullptr);
    CHECK_EQ(mm7BeaconFire.decorationId, 306);
    CHECK_EQ(mm7BeaconFire.pEntry->internalName, "dec61");
    CHECK_EQ(mm7BeaconFire.pEntry->hint, "beacon fire");

    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OpenYAMM::Game::OutdoorSceneData> out01Scene =
        sceneLoader.loadFromText(loadSourceFileText("assets_dev/worlds/mm8/maps/out01.scene.yml"), sceneError);
    REQUIRE_MESSAGE(out01Scene.has_value(), sceneError.c_str());

    const OpenYAMM::Game::OutdoorSceneEntity *pSmokeEntity = nullptr;
    const OpenYAMM::Game::OutdoorSceneEntity *pPartyStartEntity = nullptr;

    for (const OpenYAMM::Game::OutdoorSceneEntity &entity : out01Scene->entities)
    {
        if (entity.entity.name == "smoke" && pSmokeEntity == nullptr)
        {
            pSmokeEntity = &entity;
        }
        else if (entity.entity.name == "Party Start" && pPartyStartEntity == nullptr)
        {
            pPartyStartEntity = &entity;
        }
    }

    REQUIRE(pSmokeEntity != nullptr);
    const OpenYAMM::Game::DecorationLookupResult out01Smoke =
        decorationTable.resolveMapDecoration(pSmokeEntity->entity.decorationListId, pSmokeEntity->entity.name);
    REQUIRE(out01Smoke.pEntry != nullptr);
    CHECK_EQ(out01Smoke.decorationId, 22);

    REQUIRE(pPartyStartEntity != nullptr);
    const OpenYAMM::Game::DecorationLookupResult out01PartyStart =
        decorationTable.resolveMapDecoration(
            pPartyStartEntity->entity.decorationListId,
            pPartyStartEntity->entity.name);
    REQUIRE(out01PartyStart.pEntry != nullptr);
    CHECK_EQ(out01PartyStart.decorationId, 14);
}

TEST_CASE("mm7 shoals scene overlay combines always dark fog with underwater tint")
{
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;

    const std::filesystem::path scenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm7/maps/7out15.scene.yml";
    std::ifstream sceneFile(scenePath);
    REQUIRE(sceneFile.good());
    std::ostringstream sceneText;
    sceneText << sceneFile.rdbuf();

    const std::optional<OpenYAMM::Game::OutdoorSceneData> scene =
        sceneLoader.loadFromText(sceneText.str(), sceneError);
    REQUIRE_MESSAGE(scene.has_value(), sceneError.c_str());

    OpenYAMM::Game::OutdoorSceneData mergedScene = *scene;

    const std::filesystem::path overlayPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm7/maps/7out15_1.scene.yml";
    std::ifstream overlayFile(overlayPath);
    REQUIRE(overlayFile.good());
    std::ostringstream overlayText;
    overlayText << overlayFile.rdbuf();

    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedScene, overlayText.str(), sceneError),
        sceneError.c_str());
    CHECK(mergedScene.environment.flags.underwater);
    CHECK(mergedScene.environment.flags.alwaysDark);
    CHECK(mergedScene.environment.flags.alwaysFoggy);
    CHECK_EQ(mergedScene.environment.dayBitsRaw, 0x00);
    CHECK_EQ(mergedScene.environment.mapExtraBitsRaw, 0x54u);
}

TEST_CASE("mm6 outdoor scene overlays restore mmmerge footstep sound overrides")
{
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;

    const auto loadSceneText = [](const std::filesystem::path &path)
    {
        std::ifstream file(path);
        REQUIRE(file.good());
        std::ostringstream text;
        text << file.rdbuf();
        return text.str();
    };

    const auto loadMergedScene =
        [&](const char *pMapName, const char *pOverlayName)
        {
            const std::filesystem::path scenePath =
                std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm6/maps" / pMapName;
            const std::filesystem::path overlayPath =
                std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm6/maps" / pOverlayName;

            const std::optional<OpenYAMM::Game::OutdoorSceneData> scene =
                sceneLoader.loadFromText(loadSceneText(scenePath), sceneError);
            REQUIRE_MESSAGE(scene.has_value(), sceneError.c_str());

            OpenYAMM::Game::OutdoorSceneData mergedScene = *scene;
            REQUIRE_MESSAGE(
                sceneLoader.applyOverlayFromText(mergedScene, loadSceneText(overlayPath), sceneError),
                sceneError);
            return mergedScene;
        };

    const auto findOverride =
        [](const OpenYAMM::Game::OutdoorSceneData &scene, uint16_t tileId)
        {
            return std::find_if(
                scene.terrainFootstepSoundOverrides.begin(),
                scene.terrainFootstepSoundOverrides.end(),
                [tileId](const OpenYAMM::Game::OutdoorSceneTerrainFootstepSoundOverride &overrideEntry)
                {
                    return overrideEntry.tileId == tileId;
                });
        };

    const OpenYAMM::Game::OutdoorSceneData outa2Scene = loadMergedScene("outa2.scene.yml", "outa2_1.scene.yml");
    const auto outa2DefaultOverride = findOverride(outa2Scene, 0);
    REQUIRE(outa2DefaultOverride != outa2Scene.terrainFootstepSoundOverrides.end());
    CHECK_EQ(outa2DefaultOverride->walkSoundId, 91u);
    CHECK_EQ(outa2DefaultOverride->runSoundId, 52u);

    const OpenYAMM::Game::OutdoorSceneData outa3Scene = loadMergedScene("outa3.scene.yml", "outa3_1.scene.yml");
    const auto outa3DefaultOverride = findOverride(outa3Scene, 0);
    REQUIRE(outa3DefaultOverride != outa3Scene.terrainFootstepSoundOverrides.end());
    CHECK_EQ(outa3DefaultOverride->walkSoundId, 91u);
    CHECK_EQ(outa3DefaultOverride->runSoundId, 52u);
    const auto outa3TileSetOverride = findOverride(outa3Scene, 6);
    REQUIRE(outa3TileSetOverride != outa3Scene.terrainFootstepSoundOverrides.end());
    CHECK_EQ(outa3TileSetOverride->walkSoundId, 90u);
    CHECK_EQ(outa3TileSetOverride->runSoundId, 51u);

    const OpenYAMM::Game::OutdoorSceneData outb3Scene = loadMergedScene("outb3.scene.yml", "outb3_1.scene.yml");
    const auto outb3TileSetOverride = findOverride(outb3Scene, 6);
    REQUIRE(outb3TileSetOverride != outb3Scene.terrainFootstepSoundOverrides.end());
    CHECK_EQ(outb3TileSetOverride->walkSoundId, 91u);
    CHECK_EQ(outb3TileSetOverride->runSoundId, 52u);

    const OpenYAMM::Game::OutdoorSceneData oute3Scene =
        loadMergedScene("oute3.scene.yml", "oute3.scene.1.yml");
    REQUIRE_GT(oute3Scene.initialState.actors.size(), 37u);
    CHECK_EQ(oute3Scene.initialState.actors[37].x, -8815);
    CHECK_EQ(oute3Scene.initialState.actors[37].y, -9070);
    CHECK_EQ(oute3Scene.initialState.actors[37].z, 458);
}

TEST_CASE("mm7 arena map fixups expose runtime restrictions and arena master topic")
{
    const std::filesystem::path arenaScenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm7/maps/7d05.scene.yml";
    std::ifstream arenaSceneFile(arenaScenePath);
    REQUIRE(arenaSceneFile.good());
    std::ostringstream arenaSceneText;
    arenaSceneText << arenaSceneFile.rdbuf();

    OpenYAMM::Game::IndoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OpenYAMM::Game::IndoorSceneData> arenaScene =
        sceneLoader.loadFromText(arenaSceneText.str(), sceneError);
    REQUIRE_MESSAGE(arenaScene.has_value(), sceneError.c_str());
    OpenYAMM::Game::IndoorSceneData mergedArenaScene = *arenaScene;

    const std::filesystem::path arenaOverlayPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm7/maps/7d05_1.scene.yml";
    std::ifstream arenaOverlayFile(arenaOverlayPath);
    REQUIRE(arenaOverlayFile.good());
    std::ostringstream arenaOverlayText;
    arenaOverlayText << arenaOverlayFile.rdbuf();
    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedArenaScene, arenaOverlayText.str(), sceneError),
        sceneError.c_str());
    CHECK_FALSE(mergedArenaScene.runtimeRestrictions.allowSaveGame);
    CHECK_FALSE(mergedArenaScene.runtimeRestrictions.allowLloydsBeacon);
    CHECK(mergedArenaScene.runtimeRestrictions.isArena);

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::NpcEntry *pArenaMaster = gameData.npcDialogTable.getNpc(639);
    REQUIRE(pArenaMaster != nullptr);
    REQUIRE_FALSE(pArenaMaster->topicIds.empty());
    CHECK_EQ(pArenaMaster->topicIds[0], 704u);
    CHECK(std::find(pArenaMaster->topicIds.begin(), pArenaMaster->topicIds.end(), 1149u)
          == pArenaMaster->topicIds.end());
}

TEST_CASE("mm8 arena map fixups expose runtime restrictions")
{
    const std::filesystem::path arenaScenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/d42.scene.yml";
    std::ifstream arenaSceneFile(arenaScenePath);
    REQUIRE(arenaSceneFile.good());
    std::ostringstream arenaSceneText;
    arenaSceneText << arenaSceneFile.rdbuf();

    OpenYAMM::Game::IndoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OpenYAMM::Game::IndoorSceneData> arenaScene =
        sceneLoader.loadFromText(arenaSceneText.str(), sceneError);
    REQUIRE_MESSAGE(arenaScene.has_value(), sceneError.c_str());
    OpenYAMM::Game::IndoorSceneData mergedArenaScene = *arenaScene;

    const std::filesystem::path arenaOverlayPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/maps/d42_1.scene.yml";
    std::ifstream arenaOverlayFile(arenaOverlayPath);
    REQUIRE(arenaOverlayFile.good());
    std::ostringstream arenaOverlayText;
    arenaOverlayText << arenaOverlayFile.rdbuf();
    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedArenaScene, arenaOverlayText.str(), sceneError),
        sceneError.c_str());
    CHECK_FALSE(mergedArenaScene.runtimeRestrictions.allowSaveGame);
    CHECK_FALSE(mergedArenaScene.runtimeRestrictions.allowLloydsBeacon);
    CHECK(mergedArenaScene.runtimeRestrictions.isArena);
}

TEST_CASE("mm6 Hive forbids Lloyds Beacon but allows saving")
{
    const std::filesystem::path hiveScenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm6/maps/hive.scene.yml";
    std::ifstream hiveSceneFile(hiveScenePath);
    REQUIRE(hiveSceneFile.good());
    std::ostringstream hiveSceneText;
    hiveSceneText << hiveSceneFile.rdbuf();

    OpenYAMM::Game::IndoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OpenYAMM::Game::IndoorSceneData> hiveScene =
        sceneLoader.loadFromText(hiveSceneText.str(), sceneError);
    REQUIRE_MESSAGE(hiveScene.has_value(), sceneError.c_str());
    OpenYAMM::Game::IndoorSceneData mergedHiveScene = *hiveScene;

    const std::filesystem::path hiveOverlayPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm6/maps/hive_1.scene.yml";
    std::ifstream hiveOverlayFile(hiveOverlayPath);
    REQUIRE(hiveOverlayFile.good());
    std::ostringstream hiveOverlayText;
    hiveOverlayText << hiveOverlayFile.rdbuf();
    REQUIRE_MESSAGE(
        sceneLoader.applyOverlayFromText(mergedHiveScene, hiveOverlayText.str(), sceneError),
        sceneError.c_str());

    CHECK(mergedHiveScene.runtimeRestrictions.allowSaveGame);
    CHECK_FALSE(mergedHiveScene.runtimeRestrictions.allowLloydsBeacon);
    CHECK_FALSE(mergedHiveScene.runtimeRestrictions.isArena);
}

TEST_CASE("mm7 Temple of the Moon scene keeps MMerge initial door states")
{
    const std::filesystem::path scenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm7/maps/7d06.scene.yml";
    std::ifstream sceneFile(scenePath);
    REQUIRE(sceneFile.good());
    std::ostringstream sceneText;
    sceneText << sceneFile.rdbuf();

    OpenYAMM::Game::IndoorSceneYmlLoader sceneLoader = {};
    std::string sceneError;
    const std::optional<OpenYAMM::Game::IndoorSceneData> scene =
        sceneLoader.loadFromText(sceneText.str(), sceneError);
    REQUIRE_MESSAGE(scene.has_value(), sceneError.c_str());

    const auto checkDoorState =
        [&](uint32_t doorId, uint16_t expectedState)
        {
            const auto doorIt = std::find_if(
                scene->initialState.doors.begin(),
                scene->initialState.doors.end(),
                [doorId](const OpenYAMM::Game::IndoorSceneDoor &door)
                {
                    return door.door.doorId == doorId;
                });
            REQUIRE(doorIt != scene->initialState.doors.end());
            CHECK_EQ(doorIt->door.state, expectedState);
        };

    for (uint32_t doorId : {5u, 6u, 7u, 8u})
    {
        checkDoorState(doorId, 2u);
    }

    for (uint32_t doorId : {9u, 10u})
    {
        checkDoorState(doorId, 0u);
    }
}

TEST_CASE("outdoor terrain descriptors use mm6 and mm7 merged tile tables")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(initializeTestAssetFileSystem(assetFileSystem));

    const std::optional<std::string> surfaceMaterialYaml =
        assetFileSystem.readTextFile("Data/rendering/surface_materials.yml");
    REQUIRE(surfaceMaterialYaml.has_value());

    OpenYAMM::Game::SurfaceMaterialTable surfaceMaterialTable;
    std::string surfaceMaterialError;
    REQUIRE(surfaceMaterialTable.loadFromYaml(*surfaceMaterialYaml, surfaceMaterialError));
    const OpenYAMM::Game::SurfaceMaterialDefinition *pMm6WaterMaterial =
        surfaceMaterialTable.findMatch("6wtrtyl", 0, true);
    REQUIRE(pMm6WaterMaterial != nullptr);
    REQUIRE(pMm6WaterMaterial->animation.frames.size() == 14);
    CHECK(pMm6WaterMaterial->animation.animationLengthTicks == 210);
    CHECK(pMm6WaterMaterial->animation.frames.front().textureName == "6hdwtr000");
    CHECK(pMm6WaterMaterial->animation.frames.back().textureName == "6hdwtr013");

    for (const OpenYAMM::Game::SurfaceAnimationFrame &frame : pMm6WaterMaterial->animation.frames)
    {
        CHECK(frame.frameLengthTicks == 15);
    }

    REQUIRE(surfaceMaterialTable.findMatch("6wtrdrNE", 0, true) != nullptr);

    const OpenYAMM::Game::SurfaceMaterialDefinition *pMm7WaterMaterial =
        surfaceMaterialTable.findMatch("7wtrtyl", 0, true);
    REQUIRE(pMm7WaterMaterial != nullptr);
    CHECK(pMm7WaterMaterial->animation.frames.front().textureName == "7hdwtr000");
    CHECK(pMm7WaterMaterial->animation.frames.back().textureName == "7hdwtr013");
    REQUIRE(surfaceMaterialTable.findMatch("7hwtrdrne", 0, true) != nullptr);

    const OpenYAMM::Game::SurfaceMaterialDefinition *pMm8WaterMaterial =
        surfaceMaterialTable.findMatch("wtrtyl", 0, true);
    REQUIRE(pMm8WaterMaterial != nullptr);
    CHECK(pMm8WaterMaterial->animation.frames.front().textureName == "hdwtr000");
    CHECK(pMm8WaterMaterial->animation.frames.back().textureName == "hdwtr013");

    const OpenYAMM::Game::SurfaceMaterialDefinition *pLavaMaterial =
        surfaceMaterialTable.findMatch("lavtyl", 0, true);
    REQUIRE(pLavaMaterial != nullptr);
    REQUIRE(pLavaMaterial->animation.frames.size() == 14);
    CHECK(pLavaMaterial->animation.frames.front().textureName == "hdlav000");
    CHECK(pLavaMaterial->animation.frames.back().textureName == "hdlav013");

    const OpenYAMM::Game::SurfaceMaterialDefinition *pOilMaterial =
        surfaceMaterialTable.findMatch("tartyl", 0, true);
    REQUIRE(pOilMaterial != nullptr);
    REQUIRE(pOilMaterial->animation.frames.size() == 14);
    CHECK(pOilMaterial->animation.frames.front().textureName == "hwoil000");
    CHECK(pOilMaterial->animation.frames.back().textureName == "hwoil013");

    OpenYAMM::Game::OutdoorMapData newSorpigal = {};
    newSorpigal.fileName = "oute3.odm";
    newSorpigal.masterTile = 2;
    newSorpigal.tileSetLookupIndices = {90, 126, 198, 774};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> newSorpigalDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, newSorpigal);
    REQUIRE(newSorpigalDescriptors.has_value());
    CHECK((*newSorpigalDescriptors)[1].textureName == "6dirttyl");
    CHECK((*newSorpigalDescriptors)[90].textureName == "6grastyl");
    CHECK((*newSorpigalDescriptors)[126].textureName == "6wtrtyl");
    CHECK(((*newSorpigalDescriptors)[126].flags & OpenYAMM::Game::TerrainTileFlagWater) != 0);

    OpenYAMM::Game::OutdoorMapData emeraldIsland = {};
    emeraldIsland.fileName = "7out01.odm";
    emeraldIsland.masterTile = 1;
    emeraldIsland.tileSetLookupIndices = {90, 126, 270, 414};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> emeraldIslandDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, emeraldIsland);
    REQUIRE(emeraldIslandDescriptors.has_value());
    CHECK((*emeraldIslandDescriptors)[1].textureName == "7dirttyl");
    CHECK((*emeraldIslandDescriptors)[90].textureName == "7grastyl");
    CHECK((*emeraldIslandDescriptors)[126].textureName == "7wtrtyl");
    CHECK(((*emeraldIslandDescriptors)[126].flags & OpenYAMM::Game::TerrainTileFlagWater) != 0);
    CHECK(assetFileSystem.exists("terrain/7wtrtyl.bmp"));

    OpenYAMM::Game::OutdoorMapData nighon = {};
    nighon.worldId = "mm7";
    nighon.fileName = "out10.odm";
    nighon.masterTile = 1;
    nighon.tileSetLookupIndices = {342, 126, 234, 414};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> nighonDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, nighon);
    REQUIRE(nighonDescriptors.has_value());
    CHECK((*nighonDescriptors)[1].textureName == "7dirttyl");
    CHECK((*nighonDescriptors)[90].textureName == "7snow");
    CHECK((*nighonDescriptors)[126].textureName == "7wtrtyl");
}

TEST_CASE("outdoor terrain descriptor flags are applied to movement attributes")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(initializeTestAssetFileSystem(assetFileSystem));

    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.fileName = "out04.odm";
    mapData.masterTile = 1;
    mapData.tileSetLookupIndices = {594, 558, 450, 522};
    mapData.tileMap.assign(
        static_cast<size_t>(OpenYAMM::Game::OutdoorMapData::TerrainWidth)
            * static_cast<size_t>(OpenYAMM::Game::OutdoorMapData::TerrainHeight),
        90);
    mapData.attributeMap.assign(mapData.tileMap.size(), 0);

    const size_t lavaCellIndex =
        static_cast<size_t>(63 * OpenYAMM::Game::OutdoorMapData::TerrainWidth + 63);
    mapData.tileMap[lavaCellIndex] = 126;

    REQUIRE(OpenYAMM::Game::applyTerrainTileDescriptorAttributes(assetFileSystem, mapData));
    CHECK((mapData.attributeMap[lavaCellIndex] & 0x02) != 0);
    CHECK((mapData.attributeMap[lavaCellIndex] & 0x01) != 0);
}

TEST_CASE("world item pickup decision prefers inventory before held item")
{
    const OpenYAMM::Game::GameplayWorldItemPickupDecision decision =
        OpenYAMM::Game::GameplayWorldItemInteraction::decidePickupDestination(
            OpenYAMM::Game::GameplayWorldItemPickupDecisionInput{
                .isGold = false,
                .goldAmount = 0,
                .canStoreInInventory = true,
                .heldItemActive = false,
            });

    CHECK(decision.destination == OpenYAMM::Game::GameplayWorldItemPickupDestination::Inventory);
    CHECK(decision.goldAmount == 0);
}

TEST_CASE("world item pickup decision falls back to held item only when hand is empty")
{
    const OpenYAMM::Game::GameplayWorldItemPickupDecision emptyHandDecision =
        OpenYAMM::Game::GameplayWorldItemInteraction::decidePickupDestination(
            OpenYAMM::Game::GameplayWorldItemPickupDecisionInput{
                .isGold = false,
                .goldAmount = 0,
                .canStoreInInventory = false,
                .heldItemActive = false,
            });
    const OpenYAMM::Game::GameplayWorldItemPickupDecision occupiedHandDecision =
        OpenYAMM::Game::GameplayWorldItemInteraction::decidePickupDestination(
            OpenYAMM::Game::GameplayWorldItemPickupDecisionInput{
                .isGold = false,
                .goldAmount = 0,
                .canStoreInInventory = false,
                .heldItemActive = true,
            });

    CHECK(emptyHandDecision.destination == OpenYAMM::Game::GameplayWorldItemPickupDestination::HeldItem);
    CHECK(occupiedHandDecision.destination == OpenYAMM::Game::GameplayWorldItemPickupDestination::None);
}

TEST_CASE("world item pickup decision always accepts gold")
{
    const OpenYAMM::Game::GameplayWorldItemPickupDecision decision =
        OpenYAMM::Game::GameplayWorldItemInteraction::decidePickupDestination(
            OpenYAMM::Game::GameplayWorldItemPickupDecisionInput{
                .isGold = true,
                .goldAmount = 0,
                .canStoreInInventory = false,
                .heldItemActive = true,
            });

    CHECK(decision.destination == OpenYAMM::Game::GameplayWorldItemPickupDestination::Gold);
    CHECK(decision.goldAmount == 1);
}

TEST_CASE("corpse auto loot tries members from active member before using cursor")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    REQUIRE(party.setActiveMemberIndex(1));
    fillMemberInventory(party, 1, 1000);

    CorpseLootTestWorldRuntime worldRuntime = {};
    worldRuntime.corpseView.items.push_back(makeTestCorpseItem(2000, 2, 2));
    OpenYAMM::Game::GameplayUiController::HeldInventoryItemState heldItem = {};

    const OpenYAMM::Game::GameplayCorpseAutoLootResult result =
        OpenYAMM::Game::autoLootActiveCorpseView(worldRuntime, party, nullptr, &heldItem);

    REQUIRE(result.lootedAny);
    CHECK_FALSE(heldItem.active);
    CHECK(worldRuntime.dropRequests.empty());

    const OpenYAMM::Game::Character *pActiveMember = party.member(1);
    const OpenYAMM::Game::Character *pNextMember = party.member(2);

    REQUIRE(pActiveMember != nullptr);
    REQUIRE(pNextMember != nullptr);
    CHECK(std::none_of(
        pActiveMember->inventory.begin(),
        pActiveMember->inventory.end(),
        [](const OpenYAMM::Game::InventoryItem &item)
        {
            return item.objectDescriptionId == 2000;
        }));
    CHECK(std::any_of(
        pNextMember->inventory.begin(),
        pNextMember->inventory.end(),
        [](const OpenYAMM::Game::InventoryItem &item)
        {
            return item.objectDescriptionId == 2000;
        }));
}

TEST_CASE("corpse auto loot drops occupied cursor item before holding unplaced corpse item")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        fillMemberInventory(party, memberIndex, 3000 + static_cast<uint32_t>(memberIndex) * 200);
    }

    CorpseLootTestWorldRuntime worldRuntime = {};
    worldRuntime.corpseView.items.push_back(makeTestCorpseItem(5000, 2, 2));

    OpenYAMM::Game::GameplayUiController::HeldInventoryItemState heldItem = {};
    heldItem.active = true;
    heldItem.item = makeTestInventoryItem(4000, 1, 1);

    const OpenYAMM::Game::GameplayCorpseAutoLootResult result =
        OpenYAMM::Game::autoLootActiveCorpseView(worldRuntime, party, nullptr, &heldItem);

    REQUIRE(result.lootedAny);
    REQUIRE(heldItem.active);
    CHECK_EQ(heldItem.item.objectDescriptionId, 5000u);
    REQUIRE_EQ(worldRuntime.dropRequests.size(), 1u);
    CHECK_EQ(worldRuntime.dropRequests.front().item.objectDescriptionId, 4000u);
}

TEST_CASE("corpse auto loot silently closes empty corpse view")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    CorpseLootTestWorldRuntime worldRuntime = {};
    REQUIRE(worldRuntime.activeCorpseView() != nullptr);

    const OpenYAMM::Game::GameplayCorpseAutoLootResult result =
        OpenYAMM::Game::autoLootActiveCorpseView(worldRuntime, party, nullptr, nullptr);

    CHECK_FALSE(result.lootedAny);
    CHECK_FALSE(result.blockedByInventory);
    CHECK(result.empty);
    CHECK(result.statusText.empty());
    CHECK(worldRuntime.activeCorpseView() == nullptr);
}

TEST_CASE("charged wand attack profile prefers wand over equipped bow")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    member.equipment.mainHand = 152;
    member.equipmentRuntime.mainHand.currentCharges = 3;
    member.equipmentRuntime.mainHand.maxCharges = 3;
    member.equipment.bow = findFirstItemIdBySkillGroup(gameData.itemTable, "Bow");
    member.equipmentRuntime.bow = {};

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);
    std::mt19937 rng(7);
    const OpenYAMM::Game::CharacterAttackResult attack =
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackAgainstArmorClass(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            10,
            1024.0f,
            rng);

    CHECK(profile.hasWand);
    CHECK(profile.hasBow);
    CHECK_EQ(profile.wandSpellId, OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt));
    CHECK_EQ(profile.rangedSkillLevel, 8u);
    CHECK_EQ(profile.rangedSkillMastery, static_cast<uint32_t>(OpenYAMM::Game::SkillMastery::Normal));
    CHECK(attack.mode == OpenYAMM::Game::CharacterAttackMode::Wand);
}

TEST_CASE("empty wand falls back to bow attack profile")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    member.equipment.mainHand = 152;
    member.equipmentRuntime.mainHand.currentCharges = 0;
    member.equipmentRuntime.mainHand.maxCharges = 3;
    member.equipment.bow = findFirstItemIdBySkillGroup(gameData.itemTable, "Bow");
    member.equipmentRuntime.bow = {};

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);
    std::mt19937 rng(7);
    const OpenYAMM::Game::CharacterAttackResult attack =
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackAgainstArmorClass(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            10,
            1024.0f,
            rng);

    CHECK_FALSE(profile.hasWand);
    CHECK(profile.hasBow);
    CHECK(attack.mode == OpenYAMM::Game::CharacterAttackMode::Bow);
}

TEST_CASE("party attack target filtering treats dying actors as unavailable")
{
    OpenYAMM::Game::GameplayPartyAttackActorFacts dyingActor = {
        .actorIndex = 0,
        .monsterId = 1,
        .displayName = "Dying Target",
        .position = {.x = 0.0f, .y = 0.0f, .z = 0.0f},
        .radius = 32,
        .height = 96,
        .currentHp = 0,
        .maxHp = 20,
        .effectiveArmorClass = 10,
        .isDead = false,
        .isInvisible = false,
        .hostileToParty = true,
        .visibleForFallback = true,
    };
    OpenYAMM::Game::GameplayPartyAttackActorFacts aliveActor = {
        .actorIndex = 1,
        .monsterId = 1,
        .displayName = "Alive Target",
        .position = {.x = 0.0f, .y = 0.0f, .z = 0.0f},
        .radius = 32,
        .height = 96,
        .currentHp = 20,
        .maxHp = 20,
        .effectiveArmorClass = 10,
        .isDead = false,
        .isInvisible = false,
        .hostileToParty = true,
        .visibleForFallback = true,
    };

    CHECK_FALSE(OpenYAMM::Game::GameplayActionController::isPartyAttackActorTargetable(dyingActor));
    CHECK_FALSE(OpenYAMM::Game::GameplayActionController::isPartyAttackFallbackCandidate(dyingActor));
    CHECK(OpenYAMM::Game::GameplayActionController::isPartyAttackActorTargetable(aliveActor));
    CHECK(OpenYAMM::Game::GameplayActionController::isPartyAttackFallbackCandidate(aliveActor));
}

TEST_CASE("party melee status text reports applied damage")
{
    OpenYAMM::Game::CharacterAttackResult attack = {};
    attack.mode = OpenYAMM::Game::CharacterAttackMode::Melee;
    attack.canAttack = true;
    attack.hit = true;
    attack.damage = 48;

    CHECK_EQ(
        OpenYAMM::Game::GameplayCombatController::formatPartyAttackStatusText(
            "Ariel",
            "Goblin",
            attack,
            false,
            12),
        "Ariel hits Goblin for 12 damage");

    CHECK_EQ(
        OpenYAMM::Game::GameplayCombatController::formatPartyAttackStatusText(
            "Ariel",
            "Goblin",
            attack,
            true,
            48),
        "Ariel inflicts 48 points killing Goblin");
}

TEST_CASE("zero monster resistance does not reduce incoming melee damage")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();

    OpenYAMM::Game::Character knight = {};
    knight.name = "Knight";
    knight.className = "Knight";
    knight.level = 1;
    knight.might = 25;
    knight.accuracy = 13;
    knight.speed = 13;
    knight.equipment.mainHand = 1;
    knight.skills["Sword"] = OpenYAMM::Game::CharacterSkill{"Sword", 1, OpenYAMM::Game::SkillMastery::Normal};
    knight.skills["Armsmaster"] =
        OpenYAMM::Game::CharacterSkill{"Armsmaster", 1, OpenYAMM::Game::SkillMastery::Normal};

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            knight,
            &gameData.itemTable,
            &gameData.spellTable);

    CHECK(profile.meleeMinDamage == 7);
    CHECK(profile.meleeMaxDamage == 11);

    auto observedHitDamages = [&]()
    {
        std::set<int> damages;

        for (uint32_t seed = 1; seed <= 200000 && damages.size() < 12; ++seed)
        {
            std::mt19937 rng(seed);
            const OpenYAMM::Game::CharacterAttackResult attack =
                OpenYAMM::Game::GameMechanics::resolveCharacterAttackAgainstArmorClass(
                    knight,
                    &gameData.itemTable,
                    &gameData.spellTable,
                    6,
                    128.0f,
                    rng);

            if (!attack.hit)
            {
                continue;
            }

            damages.insert(OpenYAMM::Game::GameMechanics::resolveMonsterIncomingDamage(
                attack.damage,
                attack.damageType,
                0,
                0,
                rng));
        }

        return damages;
    };

    CHECK(observedHitDamages() == std::set<int>{7, 8, 9, 10, 11});
}

TEST_CASE("monster hour of power resistance bonus only affects OE elemental damage types")
{
    constexpr int Damage = 64;
    bool sawFireReduced = false;
    bool sawPhysicalReduced = false;

    for (uint32_t seed = 1; seed <= 1000; ++seed)
    {
        std::mt19937 fireRng(seed);
        const int fireDamage = OpenYAMM::Game::GameMechanics::resolveMonsterIncomingDamage(
            Damage,
            OpenYAMM::Game::CombatDamageType::Fire,
            0,
            100,
            fireRng);
        sawFireReduced = sawFireReduced || fireDamage < Damage;

        std::mt19937 physicalRng(seed);
        const int physicalDamage = OpenYAMM::Game::GameMechanics::resolveMonsterIncomingDamage(
            Damage,
            OpenYAMM::Game::CombatDamageType::Physical,
            0,
            100,
            physicalRng);
        sawPhysicalReduced = sawPhysicalReduced || physicalDamage < Damage;
    }

    CHECK(sawFireReduced);
    CHECK_FALSE(sawPhysicalReduced);
}

TEST_CASE("monster Attack1 projectile applies special attack condition")
{
    constexpr uint32_t ActorId = 77;

    OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();
    MonsterSpecialAttackTestWorldRuntime world = {};
    world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
        .actorId = ActorId,
        .monsterLevel = 100,
        .attackBonus = 1000,
        .specialAttackKind = OpenYAMM::Game::MonsterSpecialAttackKind::Paralyze,
        .specialAttackLevel = 1,
        .displayName = "Paralyzing Archer",
    };

    OpenYAMM::Game::GameplayCombatController controller = {};
    controller.recordPartyProjectileImpact(
        ActorId,
        1,
        1000,
        0,
        false,
        OpenYAMM::Game::CombatDamageType::Physical,
        OpenYAMM::Game::GameplayActorAttackAbility::Attack1);

    OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
    controller.handleAndClearPendingCombatEvents(context);

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    CHECK(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Paralyzed)));
}

TEST_CASE("monster non-Attack1 projectile does not apply special attack condition")
{
    constexpr uint32_t ActorId = 78;

    OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();
    MonsterSpecialAttackTestWorldRuntime world = {};
    world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
        .actorId = ActorId,
        .monsterLevel = 100,
        .attackBonus = 1000,
        .specialAttackKind = OpenYAMM::Game::MonsterSpecialAttackKind::Paralyze,
        .specialAttackLevel = 1,
        .displayName = "Paralyzing Caster",
    };

    OpenYAMM::Game::GameplayCombatController controller = {};
    controller.recordPartyProjectileImpact(
        ActorId,
        1,
        1000,
        0,
        false,
        OpenYAMM::Game::CombatDamageType::Physical,
        OpenYAMM::Game::GameplayActorAttackAbility::Attack2);

    OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
    controller.handleAndClearPendingCombatEvents(context);

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Paralyzed)));
}

TEST_CASE("Protection from Magic blocks regular monster condition special attacks")
{
    constexpr uint32_t ActorId = 79;

    OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();
    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::ProtectionFromMagic,
        60.0f,
        1,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::ProtectionFromMagic),
        1,
        OpenYAMM::Game::SkillMastery::Master,
        0);

    MonsterSpecialAttackTestWorldRuntime world = {};
    world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
        .actorId = ActorId,
        .monsterLevel = 100,
        .attackBonus = 1000,
        .specialAttackKind = OpenYAMM::Game::MonsterSpecialAttackKind::Paralyze,
        .specialAttackLevel = 1,
        .displayName = "Paralyzing Archer",
    };

    OpenYAMM::Game::GameplayCombatController controller = {};
    controller.recordMonsterMeleeImpact(
        ActorId,
        0,
        1000,
        OpenYAMM::Game::CombatDamageType::Physical,
        OpenYAMM::Game::GameplayActorAttackAbility::Attack1);

    OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
    controller.handleAndClearPendingCombatEvents(context);

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Paralyzed)));
    CHECK(party.partyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic) == nullptr);
}

TEST_CASE("grandmaster Protection from Magic blocks monster death and eradication special attacks")
{
    constexpr uint32_t ActorId = 80;

    const std::vector<std::pair<OpenYAMM::Game::MonsterSpecialAttackKind, OpenYAMM::Game::CharacterCondition>>
        protectedConditions = {
            {OpenYAMM::Game::MonsterSpecialAttackKind::Dead, OpenYAMM::Game::CharacterCondition::Dead},
            {OpenYAMM::Game::MonsterSpecialAttackKind::Eradicate, OpenYAMM::Game::CharacterCondition::Eradicated},
        };

    for (const std::pair<OpenYAMM::Game::MonsterSpecialAttackKind, OpenYAMM::Game::CharacterCondition> &testCase
        : protectedConditions)
    {
        OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();
        party.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::ProtectionFromMagic,
            60.0f,
            1,
            OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::ProtectionFromMagic),
            1,
            OpenYAMM::Game::SkillMastery::Grandmaster,
            0);

        MonsterSpecialAttackTestWorldRuntime world = {};
        world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
            .actorId = ActorId,
            .monsterLevel = 100,
            .attackBonus = 1000,
            .specialAttackKind = testCase.first,
            .specialAttackLevel = 1,
            .displayName = "Terminator Unit",
        };

        OpenYAMM::Game::GameplayCombatController controller = {};
        controller.recordMonsterMeleeImpact(
            ActorId,
            0,
            1000,
            OpenYAMM::Game::CombatDamageType::Physical,
            OpenYAMM::Game::GameplayActorAttackAbility::Attack1);

        OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
        controller.handleAndClearPendingCombatEvents(context);

        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(testCase.second)));
        CHECK(party.partyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic) == nullptr);
    }
}

TEST_CASE("master Protection from Magic does not block monster death and eradication special attacks")
{
    constexpr uint32_t ActorId = 81;

    const std::vector<std::pair<OpenYAMM::Game::MonsterSpecialAttackKind, OpenYAMM::Game::CharacterCondition>>
        unprotectedConditions = {
            {OpenYAMM::Game::MonsterSpecialAttackKind::Dead, OpenYAMM::Game::CharacterCondition::Dead},
            {OpenYAMM::Game::MonsterSpecialAttackKind::Eradicate, OpenYAMM::Game::CharacterCondition::Eradicated},
        };

    for (const std::pair<OpenYAMM::Game::MonsterSpecialAttackKind, OpenYAMM::Game::CharacterCondition> &testCase
        : unprotectedConditions)
    {
        OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();
        party.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::ProtectionFromMagic,
            60.0f,
            1,
            OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::ProtectionFromMagic),
            1,
            OpenYAMM::Game::SkillMastery::Master,
            0);

        MonsterSpecialAttackTestWorldRuntime world = {};
        world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
            .actorId = ActorId,
            .monsterLevel = 100,
            .attackBonus = 1000,
            .specialAttackKind = testCase.first,
            .specialAttackLevel = 1,
            .displayName = "Terminator Unit",
        };

        OpenYAMM::Game::GameplayCombatController controller = {};
        controller.recordMonsterMeleeImpact(
            ActorId,
            0,
            1000,
            OpenYAMM::Game::CombatDamageType::Physical,
            OpenYAMM::Game::GameplayActorAttackAbility::Attack1);

        OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
        controller.handleAndClearPendingCombatEvents(context);

        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK(pMember->conditions.test(static_cast<size_t>(testCase.second)));
        CHECK(party.partyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic) != nullptr);
    }
}

TEST_CASE("monster incapacitating special attacks reduce victim health to zero")
{
    constexpr uint32_t ActorId = 82;

    const std::vector<std::pair<OpenYAMM::Game::MonsterSpecialAttackKind, OpenYAMM::Game::CharacterCondition>>
        incapacitatingConditions = {
            {OpenYAMM::Game::MonsterSpecialAttackKind::Unconscious, OpenYAMM::Game::CharacterCondition::Unconscious},
            {OpenYAMM::Game::MonsterSpecialAttackKind::Dead, OpenYAMM::Game::CharacterCondition::Dead},
            {OpenYAMM::Game::MonsterSpecialAttackKind::Eradicate, OpenYAMM::Game::CharacterCondition::Eradicated},
        };

    for (const std::pair<OpenYAMM::Game::MonsterSpecialAttackKind, OpenYAMM::Game::CharacterCondition> &testCase
        : incapacitatingConditions)
    {
        OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();

        MonsterSpecialAttackTestWorldRuntime world = {};
        world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
            .actorId = ActorId,
            .monsterLevel = 100,
            .attackBonus = 1000,
            .specialAttackKind = testCase.first,
            .specialAttackLevel = 1,
            .displayName = "Incapacitating Monster",
        };

        OpenYAMM::Game::GameplayCombatController controller = {};
        controller.recordMonsterMeleeImpact(
            ActorId,
            0,
            1000,
            OpenYAMM::Game::CombatDamageType::Physical,
            OpenYAMM::Game::GameplayActorAttackAbility::Attack1);

        OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
        controller.handleAndClearPendingCombatEvents(context);

        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK(pMember->conditions.test(static_cast<size_t>(testCase.second)));
        CHECK(pMember->health == 0);
    }
}

TEST_CASE("monster break item uses regular inventory plus equipment candidates")
{
    constexpr uint32_t ActorId = 83;
    constexpr uint32_t RegularWeaponId = 31;
    constexpr uint32_t PotionId = 222;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::Party party = makeMonsterSpecialAttackTestParty();
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->inventory.clear();
    REQUIRE(pMember->addInventoryItemAt(makeTestInventoryItem(PotionId), 0, 0));
    pMember->equipment.mainHand = RegularWeaponId;

    MonsterSpecialAttackTestWorldRuntime world = {};
    world.actorInfo = OpenYAMM::Game::GameplayCombatActorInfo{
        .actorId = ActorId,
        .monsterLevel = 100,
        .attackBonus = 1000,
        .specialAttackKind = OpenYAMM::Game::MonsterSpecialAttackKind::BreakAny,
        .specialAttackLevel = 1,
        .displayName = "Item Breaker",
    };

    OpenYAMM::Game::GameplayCombatController controller = {};
    controller.recordMonsterMeleeImpact(
        ActorId,
        0,
        1000,
        OpenYAMM::Game::CombatDamageType::Physical,
        OpenYAMM::Game::GameplayActorAttackAbility::Attack2);

    OpenYAMM::Game::GameplayCombatController::PendingCombatEventContext context{party, &world, nullptr};
    controller.handleAndClearPendingCombatEvents(context);

    const OpenYAMM::Game::InventoryItem *pPotionItem = pMember->inventoryItemAt(0, 0);
    REQUIRE(pPotionItem != nullptr);
    CHECK_FALSE(pPotionItem->broken);
    CHECK(pMember->equipmentRuntime.mainHand.broken);
}

TEST_CASE("dispel magic clears party and character buffs through shared party helper")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::Haste,
        60.0f,
        0,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Haste),
        1,
        OpenYAMM::Game::SkillMastery::Expert,
        0);
    party.applyCharacterBuff(
        0,
        OpenYAMM::Game::CharacterBuffId::Bless,
        60.0f,
        5,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Bless),
        1,
        OpenYAMM::Game::SkillMastery::Expert,
        0);

    REQUIRE(party.hasDispellableBuffs());
    CHECK(party.clearDispellableBuffs());
    CHECK_FALSE(party.hasPartyBuff(OpenYAMM::Game::PartyBuffId::Haste));
    CHECK_FALSE(party.hasCharacterBuff(0, OpenYAMM::Game::CharacterBuffId::Bless));
    CHECK_FALSE(party.hasDispellableBuffs());
}

TEST_CASE("main-hand blaster shoots before bow and allows original zero minimum recovery")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    member.equipment.mainHand = findFirstItemIdBySkillGroup(gameData.itemTable, "Blaster");
    member.equipment.bow = findFirstItemIdBySkillGroup(gameData.itemTable, "Bow");
    member.skills["Blaster"] = {"Blaster", 10, OpenYAMM::Game::SkillMastery::Grandmaster};
    member.attackRecoveryReductionTicks = 1000;
    REQUIRE(member.equipment.mainHand != 0);
    REQUIRE(member.equipment.bow != 0);

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);
    std::mt19937 rng(7);
    const OpenYAMM::Game::CharacterAttackResult attack =
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackAgainstArmorClass(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            10,
            1024.0f,
            rng);

    CHECK(profile.hasBlaster);
    CHECK(profile.hasBow);
    REQUIRE(profile.rangedAttackBonus.has_value());
    CHECK_EQ(profile.rangedSkillLevel, 10u);
    CHECK_EQ(profile.rangedSkillMastery, static_cast<uint32_t>(OpenYAMM::Game::SkillMastery::Grandmaster));
    CHECK(profile.rangedRecoverySeconds == doctest::Approx(0.0f));
    CHECK(attack.mode == OpenYAMM::Game::CharacterAttackMode::Blaster);
    CHECK(attack.damageType == OpenYAMM::Game::CombatDamageType::Irresistible);
    CHECK(attack.resolvesOnImpact);
    CHECK(attack.recoverySeconds == doctest::Approx(0.0f));
    CHECK(attack.attackSoundHook == "blaster_shot");
}

TEST_CASE("blaster attack tuning can add scaling skill damage and minimum recovery")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    member.equipment.mainHand = findFirstItemIdBySkillGroup(gameData.itemTable, "Blaster");
    member.skills["Blaster"] = {"Blaster", 10, OpenYAMM::Game::SkillMastery::Master};
    member.attackRecoveryReductionTicks = 1000;
    REQUIRE(member.equipment.mainHand != 0);

    const OpenYAMM::Game::CharacterAttackProfile defaultProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);

    OpenYAMM::Game::CharacterAttackTuning attackTuning = {};
    attackTuning.blasterSkillScaling = OpenYAMM::Game::BlasterSkillScalingMode::ScalingDamage;
    attackTuning.blasterMinimumRecoveryTicks = 10;

    member.skills["Blaster"] = {"Blaster", 10, OpenYAMM::Game::SkillMastery::Expert};
    const OpenYAMM::Game::CharacterAttackProfile expertProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            attackTuning);

    CHECK_EQ(expertProfile.rangedMinDamage, defaultProfile.rangedMinDamage);
    CHECK_EQ(expertProfile.rangedMaxDamage, defaultProfile.rangedMaxDamage);

    member.skills["Blaster"] = {"Blaster", 10, OpenYAMM::Game::SkillMastery::Master};
    const OpenYAMM::Game::CharacterAttackProfile scalingProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            attackTuning);

    CHECK_EQ(scalingProfile.rangedMinDamage, defaultProfile.rangedMinDamage);
    CHECK_EQ(scalingProfile.rangedMaxDamage, defaultProfile.rangedMaxDamage);
    CHECK(scalingProfile.rangedRecoverySeconds == doctest::Approx(0.166667f));

    member.skills["Blaster"] = {"Blaster", 10, OpenYAMM::Game::SkillMastery::Grandmaster};
    const OpenYAMM::Game::CharacterAttackProfile grandmasterProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            attackTuning);

    CHECK_EQ(grandmasterProfile.rangedMinDamage, defaultProfile.rangedMinDamage + 10);
    CHECK_EQ(grandmasterProfile.rangedMaxDamage, defaultProfile.rangedMaxDamage + 10);
}

TEST_CASE("spell damage buffs do not increase blaster attack damage")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    member.equipment.mainHand = findFirstItemIdBySkillGroup(gameData.itemTable, "Blaster");
    member.skills["Blaster"] = {"Blaster", 10, OpenYAMM::Game::SkillMastery::Grandmaster};
    REQUIRE(member.equipment.mainHand != 0);

    const OpenYAMM::Game::CharacterAttackProfile baseProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);
    const OpenYAMM::Game::CharacterSheetSummary baseSummary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(member, &gameData.itemTable);

    OpenYAMM::Game::Character buffedMember = member;
    buffedMember.magicalBonuses.might += 100;
    buffedMember.magicalBonuses.meleeDamage += 50;
    buffedMember.magicalBonuses.rangedDamage += 50;
    buffedMember.weaponEnchantmentDamageBonus += 18;

    const OpenYAMM::Game::CharacterAttackProfile buffedProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            buffedMember,
            &gameData.itemTable,
            &gameData.spellTable);
    const OpenYAMM::Game::CharacterSheetSummary buffedSummary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(buffedMember, &gameData.itemTable);

    CHECK_EQ(buffedProfile.rangedMinDamage, baseProfile.rangedMinDamage);
    CHECK_EQ(buffedProfile.rangedMaxDamage, baseProfile.rangedMaxDamage);
    CHECK_EQ(buffedSummary.combat.meleeDamageText, baseSummary.combat.meleeDamageText);
}

TEST_CASE("blaster damage bypasses monster resistance")
{
    const int damage = 137;
    std::mt19937 rng(11);

    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveMonsterIncomingDamage(
            damage,
            OpenYAMM::Game::CombatDamageType::Irresistible,
            0,
            200,
            rng),
        damage);
}

TEST_CASE("monster energy attack type parses as energy damage")
{
    CHECK(
        OpenYAMM::Game::GameMechanics::parseCombatDamageType("Ener")
        == OpenYAMM::Game::CombatDamageType::Energy);
    CHECK(
        OpenYAMM::Game::GameMechanics::parseCombatDamageType("Energy")
        == OpenYAMM::Game::CombatDamageType::Energy);
}

TEST_CASE("energy damage does not use earth resistance or immunity")
{
    OpenYAMM::Game::Character character = {};
    character.permanentImmunities.earth = true;

    std::mt19937 rng(13);

    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterIncomingDamage(
            character,
            nullptr,
            nullptr,
            nullptr,
            137,
            OpenYAMM::Game::CombatDamageType::Earth,
            rng),
        0);

    rng.seed(13);
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterIncomingDamage(
            character,
            nullptr,
            nullptr,
            nullptr,
            137,
            OpenYAMM::Game::CombatDamageType::Energy,
            rng),
        137);
}

TEST_CASE("monster physical attack damage roll follows OE dice and bonus formula")
{
    std::mt19937 expectedRng(17);
    int expectedDamage = 2;
    std::uniform_int_distribution<int> distribution(1, 6);

    for (int rollIndex = 0; rollIndex < 3; ++rollIndex)
    {
        expectedDamage += distribution(expectedRng);
    }

    std::mt19937 rng(17);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::rollMonsterAttackDamage(3, 6, 2, rng), expectedDamage);

    rng.seed(23);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::rollMonsterAttackDamage(0, 0, 0, rng), 0);

    rng.seed(29);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::rollMonsterAttackDamage(0, 6, -3, rng), -3);
}

TEST_CASE("monster hit chance follows OE armor class formula")
{
    constexpr int ArmorClass = 40;
    constexpr int MonsterLevel = 7;
    constexpr int AttackBonus = 13;
    constexpr int RollUpperBound = ArmorClass + 2 * MonsterLevel + 10;

    for (uint32_t seed = 1; seed <= 32; ++seed)
    {
        std::mt19937 expectedRng(seed);
        const int hitRoll = std::uniform_int_distribution<int>(1, RollUpperBound)(expectedRng);
        const bool expectedHit = hitRoll + AttackBonus > ArmorClass + 5;

        std::mt19937 rng(seed);
        CHECK_EQ(
            OpenYAMM::Game::GameMechanics::monsterAttackHitsArmorClass(
                ArmorClass,
                MonsterLevel,
                AttackBonus,
                rng),
            expectedHit);
    }
}

TEST_CASE("luck factors into incoming physical damage reduction but not monster hit chance")
{
    OpenYAMM::Game::Character character = {};
    character.luck = 100;

    bool sawPhysicalDamageReducedByLuck = false;

    for (uint32_t seed = 1; seed <= 128; ++seed)
    {
        std::mt19937 expectedRng(seed);
        int expectedDamage = 128;

        for (int rollIndex = 0; rollIndex < 4; ++rollIndex)
        {
            if (std::uniform_int_distribution<int>(0, 40)(expectedRng) < 30)
            {
                break;
            }

            expectedDamage /= 2;
        }

        std::mt19937 rng(seed);
        CHECK_EQ(
            OpenYAMM::Game::GameMechanics::resolveCharacterIncomingDamage(
                character,
                nullptr,
                nullptr,
                nullptr,
                128,
                OpenYAMM::Game::CombatDamageType::Physical,
                rng),
            expectedDamage);

        if (expectedDamage < 128)
        {
            sawPhysicalDamageReducedByLuck = true;
        }
    }

    CHECK(sawPhysicalDamageReducedByLuck);

    constexpr int ArmorClass = 40;
    constexpr int MonsterLevel = 7;
    constexpr int AttackBonus = 13;
    constexpr int RollUpperBound = ArmorClass + 2 * MonsterLevel + 10;

    std::mt19937 expectedRng(61);
    const int hitRoll = std::uniform_int_distribution<int>(1, RollUpperBound)(expectedRng);
    const bool expectedHit = hitRoll + AttackBonus > ArmorClass + 5;

    std::mt19937 rng(61);
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::monsterAttackHitsArmorClass(
            ArmorClass,
            MonsterLevel,
            AttackBonus,
            rng),
        expectedHit);
}

TEST_CASE("shielded physical projectile damage uses OE truncating halving")
{
    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveShieldedPhysicalProjectileDamage(0), 0);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveShieldedPhysicalProjectileDamage(1), 0);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveShieldedPhysicalProjectileDamage(3), 1);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::resolveShieldedPhysicalProjectileDamage(10), 5);
}

TEST_CASE("dragon character normal attack uses dragon ability firebolt profile")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Duroth", "Dragon", "PC13-01", 13);
    member.skills["DragonAbility"] = {"DragonAbility", 9, OpenYAMM::Game::SkillMastery::Master};
    member.equipment.mainHand = 152;
    member.equipmentRuntime.mainHand.currentCharges = 3;
    member.equipmentRuntime.mainHand.maxCharges = 3;
    member.equipment.bow = findFirstItemIdBySkillGroup(gameData.itemTable, "Bow");

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);
    std::mt19937 rng(7);
    const OpenYAMM::Game::CharacterAttackResult attack =
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackAgainstArmorClass(
            member,
            &gameData.itemTable,
            &gameData.spellTable,
            100,
            1024.0f,
            rng);

    CHECK(profile.hasDragonBreath);
    CHECK_EQ(profile.rangedAttackBonus, 9);
    CHECK_EQ(profile.rangedMinDamage, 9);
    CHECK_EQ(profile.rangedMaxDamage, 90);
    CHECK_EQ(
        profile.rangedSpellId,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt));
    CHECK(attack.mode == OpenYAMM::Game::CharacterAttackMode::DragonBreath);
    CHECK(attack.resolvesOnImpact);
    CHECK(attack.hit);
    CHECK(attack.damageType == OpenYAMM::Game::CombatDamageType::Irresistible);
    CHECK_EQ(
        attack.spellId,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt));
    CHECK(attack.attackBonus == 9);
    CHECK(attack.damage >= 9);
    CHECK(attack.damage <= 90);
}

TEST_CASE("starting dragon ability deals one to ten damage")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Duroth", "Dragon", "PC13-01", 13);
    member.skills["DragonAbility"] = {"DragonAbility", 1, OpenYAMM::Game::SkillMastery::Normal};

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);

    CHECK(profile.hasDragonBreath);
    CHECK_EQ(profile.rangedAttackBonus, 1);
    CHECK_EQ(profile.rangedMinDamage, 1);
    CHECK_EQ(profile.rangedMaxDamage, 10);
}

TEST_CASE("dragon breath ranged recovery uses dragon breath spell data")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character member = makeRegressionPartyMember("Duroth", "Dragon", "PC13-01", 13);
    member.skills["DragonAbility"] = {"DragonAbility", 9, OpenYAMM::Game::SkillMastery::Master};

    const OpenYAMM::Game::CharacterAttackProfile profile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            member,
            &gameData.itemTable,
            &gameData.spellTable);

    CHECK(profile.hasDragonBreath);
    CHECK(profile.rangedRecoverySeconds == doctest::Approx(2.0f));
}

TEST_CASE("equipped wand charge consumption decrements to empty and then stops")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->equipment.mainHand = 152;
    pMember->equipmentRuntime.mainHand.currentCharges = 2;
    pMember->equipmentRuntime.mainHand.maxCharges = 2;

    CHECK(party.consumeEquippedWandCharge(0));
    CHECK_EQ(pMember->equipmentRuntime.mainHand.currentCharges, 1u);
    CHECK(party.consumeEquippedWandCharge(0));
    CHECK_EQ(pMember->equipmentRuntime.mainHand.currentCharges, 0u);
    CHECK_FALSE(party.consumeEquippedWandCharge(0));
}

TEST_CASE("inventory mixing creates reagent potion in target bottle")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->skills["Alchemy"] = {"Alchemy", 2, OpenYAMM::Game::SkillMastery::Normal};

    OpenYAMM::Game::InventoryItem bottle = {};
    bottle.objectDescriptionId = 220;
    REQUIRE(pMember->addInventoryItemAt(bottle, 0, 0));

    OpenYAMM::Game::InventoryItem heldReagent = {};
    heldReagent.objectDescriptionId = 200;

    const OpenYAMM::Game::InventoryItemMixResult result =
        OpenYAMM::Game::InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
            party,
            0,
            heldReagent,
            0,
            0,
            gameData.itemTable,
            gameData.potionMixingTable,
            gameData.mergedPotionSettingTable,
            gameData.mergedReagentSettingTable);

    REQUIRE(result.handled);
    CHECK(result.success);
    CHECK(result.heldItemConsumed);

    const OpenYAMM::Game::InventoryItem *pMixedPotion = pMember->inventoryItemAt(0, 0);
    REQUIRE(pMixedPotion != nullptr);
    CHECK_EQ(pMixedPotion->objectDescriptionId, 222u);
    CHECK_EQ(pMixedPotion->standardEnchantPower, 3u);
}

TEST_CASE("inventory mixing creates reagent potion when held bottle is used on reagent")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->skills["Alchemy"] = {"Alchemy", 2, OpenYAMM::Game::SkillMastery::Normal};

    OpenYAMM::Game::InventoryItem reagent = {};
    reagent.objectDescriptionId = 200;
    REQUIRE(pMember->addInventoryItemAt(reagent, 0, 0));

    OpenYAMM::Game::InventoryItem heldBottle = {};
    heldBottle.objectDescriptionId = 220;

    const OpenYAMM::Game::InventoryItemMixResult result =
        OpenYAMM::Game::InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
            party,
            0,
            heldBottle,
            0,
            0,
            gameData.itemTable,
            gameData.potionMixingTable,
            gameData.mergedPotionSettingTable,
            gameData.mergedReagentSettingTable,
            &gameData.potionNoteTable);

    REQUIRE(result.handled);
    CHECK(result.success);
    CHECK(result.heldItemConsumed);

    const OpenYAMM::Game::InventoryItem *pMixedPotion = pMember->inventoryItemAt(0, 0);
    REQUIRE(pMixedPotion != nullptr);
    CHECK_EQ(pMixedPotion->objectDescriptionId, 222u);
    CHECK_EQ(pMixedPotion->standardEnchantPower, 3u);
}

TEST_CASE("inventory mixing accepts merged reagent item ids")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->skills["Alchemy"] = {"Alchemy", 2, OpenYAMM::Game::SkillMastery::Normal};

    OpenYAMM::Game::InventoryItem bottle = {};
    bottle.objectDescriptionId = 220;
    REQUIRE(pMember->addInventoryItemAt(bottle, 0, 0));

    OpenYAMM::Game::InventoryItem heldReagent = {};
    heldReagent.objectDescriptionId = 1002;

    const OpenYAMM::Game::InventoryItemMixResult result =
        OpenYAMM::Game::InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
            party,
            0,
            heldReagent,
            0,
            0,
            gameData.itemTable,
            gameData.potionMixingTable,
            gameData.mergedPotionSettingTable,
            gameData.mergedReagentSettingTable);

    REQUIRE(result.handled);
    CHECK(result.success);
    CHECK(result.heldItemConsumed);

    const OpenYAMM::Game::InventoryItem *pMixedPotion = pMember->inventoryItemAt(0, 0);
    REQUIRE(pMixedPotion != nullptr);
    CHECK_EQ(pMixedPotion->objectDescriptionId, 222u);
    CHECK_EQ(pMixedPotion->standardEnchantPower, 3u);
}

TEST_CASE("inventory mixing combines valid potions and returns an empty bottle")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->skills["Alchemy"] = {"Alchemy", 2, OpenYAMM::Game::SkillMastery::Expert};

    OpenYAMM::Game::InventoryItem targetPotion = {};
    targetPotion.objectDescriptionId = 223;
    targetPotion.standardEnchantPower = 20;
    REQUIRE(pMember->addInventoryItemAt(targetPotion, 0, 0));

    OpenYAMM::Game::InventoryItem heldPotion = {};
    heldPotion.objectDescriptionId = 222;
    heldPotion.standardEnchantPower = 10;

    const OpenYAMM::Game::InventoryItemMixResult result =
        OpenYAMM::Game::InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
            party,
            0,
            heldPotion,
            0,
            0,
            gameData.itemTable,
            gameData.potionMixingTable,
            gameData.mergedPotionSettingTable,
            gameData.mergedReagentSettingTable,
            &gameData.potionNoteTable);

    REQUIRE(result.handled);
    CHECK(result.success);
    CHECK(result.heldItemConsumed);
    CHECK_FALSE(result.heldItemReplacement.has_value());
    CHECK_EQ(result.unlockedAutonoteId, 33u);

    const OpenYAMM::Game::InventoryItem *pMixedPotion = pMember->inventoryItemAt(0, 0);
    REQUIRE(pMixedPotion != nullptr);
    CHECK_EQ(pMixedPotion->objectDescriptionId, 226u);
    CHECK_EQ(pMixedPotion->standardEnchantPower, 15u);
    const bool hasReturnedBottle =
        pMember->inventoryItemAt(1, 0) != nullptr
        || pMember->inventoryItemAt(0, 1) != nullptr;
    CHECK(hasReturnedBottle);
}

TEST_CASE("inventory mixing invalid potion combination consumes both items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    OpenYAMM::Game::InventoryItem targetPotion = {};
    targetPotion.objectDescriptionId = 226;
    REQUIRE(pMember->addInventoryItemAt(targetPotion, 0, 0));

    OpenYAMM::Game::InventoryItem heldPotion = {};
    heldPotion.objectDescriptionId = 240;

    const OpenYAMM::Game::InventoryItemMixResult result =
        OpenYAMM::Game::InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
            party,
            0,
            heldPotion,
            0,
            0,
            gameData.itemTable,
            gameData.potionMixingTable,
            gameData.mergedPotionSettingTable,
            gameData.mergedReagentSettingTable);

    REQUIRE(result.handled);
    CHECK_FALSE(result.success);
    CHECK(result.heldItemConsumed);
    CHECK(result.targetItemRemoved);
    CHECK_EQ(result.failureDamageLevel, 3u);
    CHECK(pMember->inventoryItemAt(0, 0) == nullptr);
}

TEST_CASE("potion mixing table uses merged potion matrix columns")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    CHECK_EQ(gameData.potionMixingTable.combinationCount(), 4900u);

    const std::optional<OpenYAMM::Game::PotionMixingTable::PotionCombination> stoneToFleshWithMagic =
        gameData.potionMixingTable.potionCombination(262, 223);
    REQUIRE(stoneToFleshWithMagic.has_value());
    CHECK_EQ(stoneToFleshWithMagic->resultItemId, 806u);

    const std::optional<OpenYAMM::Game::PotionMixingTable::PotionCombination> strangeSelf =
        gameData.potionMixingTable.potionCombination(806, 806);
    REQUIRE(strangeSelf.has_value());
    CHECK(strangeSelf->noMix);
}

TEST_CASE("potion note table maps successful mixes to autonotes")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    CHECK_GT(gameData.potionNoteTable.entryCount(), 100u);

    const std::optional<uint32_t> redBlueNote = gameData.potionNoteTable.autonoteIdForMix(223u, 222u);
    REQUIRE(redBlueNote.has_value());
    CHECK_EQ(*redBlueNote, 33u);

    CHECK_FALSE(gameData.potionNoteTable.autonoteIdForMix(222u, 222u).has_value());
}

TEST_CASE("potion explosion level two damages the member and breaks one regular item")
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->health = 500;
    pMember->maxHealth = 500;

    OpenYAMM::Game::InventoryItem regularItem = {};
    regularItem.objectDescriptionId = 109;
    REQUIRE(pMember->addInventoryItemAt(regularItem, 0, 0));

    OpenYAMM::Game::InventoryItem potionItem = {};
    potionItem.objectDescriptionId = 222;
    REQUIRE(pMember->addInventoryItemAt(potionItem, 1, 0));

    REQUIRE(party.applyPotionExplosionToMember(0, 2));

    CHECK(pMember->health >= 400);
    CHECK(pMember->health <= 470);

    const OpenYAMM::Game::InventoryItem *pRegularItem = pMember->inventoryItemAt(0, 0);
    REQUIRE(pRegularItem != nullptr);
    CHECK(pRegularItem->broken);

    const OpenYAMM::Game::InventoryItem *pPotionItem = pMember->inventoryItemAt(1, 0);
    REQUIRE(pPotionItem != nullptr);
    CHECK_FALSE(pPotionItem->broken);
}

TEST_CASE("potion explosion level four eradicates the member and breaks all regular inventory items")
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));

    OpenYAMM::Game::Party party = {};
    party.seed(seed);

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    OpenYAMM::Game::InventoryItem firstRegularItem = {};
    firstRegularItem.objectDescriptionId = 109;
    REQUIRE(pMember->addInventoryItemAt(firstRegularItem, 0, 0));

    OpenYAMM::Game::InventoryItem secondRegularItem = {};
    secondRegularItem.objectDescriptionId = 111;
    REQUIRE(pMember->addInventoryItemAt(secondRegularItem, 1, 0));

    OpenYAMM::Game::InventoryItem potionItem = {};
    potionItem.objectDescriptionId = 222;
    REQUIRE(pMember->addInventoryItemAt(potionItem, 2, 0));

    REQUIRE(party.applyPotionExplosionToMember(0, 4));

    CHECK(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Eradicated)));

    const OpenYAMM::Game::InventoryItem *pFirstRegularItem = pMember->inventoryItemAt(0, 0);
    REQUIRE(pFirstRegularItem != nullptr);
    CHECK(pFirstRegularItem->broken);

    const OpenYAMM::Game::InventoryItem *pSecondRegularItem = pMember->inventoryItemAt(1, 0);
    REQUIRE(pSecondRegularItem != nullptr);
    CHECK(pSecondRegularItem->broken);

    const OpenYAMM::Game::InventoryItem *pPotionItem = pMember->inventoryItemAt(2, 0);
    REQUIRE(pPotionItem != nullptr);
    CHECK_FALSE(pPotionItem->broken);
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

TEST_CASE("outdoor actor movement ignores pre-existing actor overlap")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorMovementController movementController(
        boundary.mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = movementController.initializeState(boundary.landX, boundary.landY, 0.0f);
    OpenYAMM::Game::OutdoorActorCollision overlappedActor = {};
    overlappedActor.source = OpenYAMM::Game::OutdoorActorCollisionSource::MapDelta;
    overlappedActor.sourceIndex = 42;
    overlappedActor.radius = 64;
    overlappedActor.height = 160;
    overlappedActor.worldX = static_cast<int>(std::lround(state.x));
    overlappedActor.worldY = static_cast<int>(std::lround(state.y));
    overlappedActor.worldZ = static_cast<int>(std::lround(state.footZ));
    movementController.setActorColliders({overlappedActor});

    std::vector<size_t> contactedActorIndices;
    const OpenYAMM::Game::OutdoorMoveState resolved =
        movementController.resolveOutdoorActorMove(
            state,
            OpenYAMM::Game::OutdoorBodyDimensions{64.0f, 160.0f},
            256.0f,
            0.0f,
            0.0f,
            false,
            0.5f,
            &contactedActorIndices,
            OpenYAMM::Game::OutdoorIgnoredActorCollider{
                OpenYAMM::Game::OutdoorActorCollisionSource::MapDelta,
                7});

    CHECK(contactedActorIndices.empty());
    CHECK(resolved.x > state.x + 32.0f);
}

TEST_CASE("outdoor party can move out of pre-existing decoration overlap")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorDecorationCollision decoration = {};
    decoration.radius = 64;
    decoration.height = 192;
    decoration.worldX = static_cast<int>(std::lround(boundary.landX));
    decoration.worldY = static_cast<int>(std::lround(boundary.landY));
    decoration.worldZ = 0;
    decoration.name = "test tree";

    OpenYAMM::Game::OutdoorDecorationCollisionSet decorationSet = {};
    decorationSet.colliders.push_back(decoration);
    OpenYAMM::Game::OutdoorMovementController movementController(
        boundary.mapData,
        std::nullopt,
        decorationSet,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state =
        movementController.initializeState(boundary.landX + 90.0f, boundary.landY, 0.0f);

    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        256.0f,
        0.0f,
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

    CHECK_GT(resolved.x, state.x + 100.0f);
}

TEST_CASE("outdoor party is still blocked from entering decoration collision")
{
    const SyntheticOutdoorWaterBoundaryScenario boundary = createSyntheticOutdoorWaterBoundaryScenario();
    OpenYAMM::Game::OutdoorDecorationCollision decoration = {};
    decoration.radius = 64;
    decoration.height = 192;
    decoration.worldX = static_cast<int>(std::lround(boundary.landX));
    decoration.worldY = static_cast<int>(std::lround(boundary.landY));
    decoration.worldZ = 0;
    decoration.name = "test tree";

    OpenYAMM::Game::OutdoorDecorationCollisionSet decorationSet = {};
    decorationSet.colliders.push_back(decoration);
    OpenYAMM::Game::OutdoorMovementController movementController(
        boundary.mapData,
        std::nullopt,
        decorationSet,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state =
        movementController.initializeState(boundary.landX - 160.0f, boundary.landY, 0.0f);

    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        512.0f,
        0.0f,
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

    CHECK_LT(resolved.x, boundary.landX - 95.0f);
}

TEST_CASE("outdoor steep terrain slides stationary party downhill")
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);
    mapData.attributeMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);

    const int tileX = 64;
    const int tileY = 64;
    const size_t highCornerIndex = static_cast<size_t>(tileY * OpenYAMM::Game::OutdoorMapData::TerrainWidth + tileX);
    mapData.heightMap[highCornerIndex] = 64;

    const float x = OpenYAMM::Game::outdoorGridCornerWorldX(tileX) + 128.0f;
    const float y = OpenYAMM::Game::outdoorGridCornerWorldY(tileY) - 128.0f;
    OpenYAMM::Game::OutdoorMovementController movementController(
        mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = {};
    state.x = x;
    state.y = y;
    state.footZ = OpenYAMM::Game::sampleOutdoorRenderedTerrainHeight(mapData, x, y) + 1.0f;
    state.verticalVelocity = 0.0f;
    state.supportKind = OpenYAMM::Game::OutdoorSupportKind::Terrain;
    state.airborne = false;
    state.fallStartZ = state.footZ;

    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        0.0f,
        0.0f,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        1.0f / 128.0f);

    CHECK_GT(resolved.x, state.x);
    CHECK_LT(resolved.y, state.y);
    CHECK_EQ(resolved.supportKind, OpenYAMM::Game::OutdoorSupportKind::Terrain);
    CHECK_FALSE(resolved.airborne);
}

TEST_CASE("outdoor steep terrain rejects uphill input and keeps sliding downhill")
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);
    mapData.attributeMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);

    const int tileX = 64;
    const int tileY = 64;
    const size_t highCornerIndex = static_cast<size_t>(tileY * OpenYAMM::Game::OutdoorMapData::TerrainWidth + tileX);
    mapData.heightMap[highCornerIndex] = 64;

    const float x = OpenYAMM::Game::outdoorGridCornerWorldX(tileX) + 128.0f;
    const float y = OpenYAMM::Game::outdoorGridCornerWorldY(tileY) - 128.0f;
    OpenYAMM::Game::OutdoorMovementController movementController(
        mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = {};
    state.x = x;
    state.y = y;
    state.footZ = OpenYAMM::Game::sampleOutdoorRenderedTerrainHeight(mapData, x, y) + 1.0f;
    state.verticalVelocity = 0.0f;
    state.supportKind = OpenYAMM::Game::OutdoorSupportKind::Terrain;
    state.airborne = false;
    state.fallStartZ = state.footZ;

    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        -512.0f,
        512.0f,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        0.1f);

    CHECK_GT(resolved.x, state.x);
    CHECK_LT(resolved.y, state.y);
    CHECK_LE(resolved.footZ, state.footZ);
    CHECK_FALSE(resolved.airborne);
}

TEST_CASE("outdoor steep bmodel support slides stationary party downhill")
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);
    mapData.attributeMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);

    OpenYAMM::Game::OutdoorBModel bmodel = {};
    bmodel.vertices = {
        {0, 0, 0},
        {512, 0, 512},
        {512, 512, 512},
        {0, 512, 0},
    };
    bmodel.minX = 0;
    bmodel.maxX = 512;
    bmodel.minY = 0;
    bmodel.maxY = 512;
    bmodel.minZ = 0;
    bmodel.maxZ = 512;

    OpenYAMM::Game::OutdoorBModelFace steepFace = {};
    steepFace.vertexIndices = {0, 1, 2, 3};
    steepFace.polygonType = 4;
    bmodel.faces = {steepFace};
    mapData.bmodels = {bmodel};

    OpenYAMM::Game::OutdoorMovementController movementController(
        mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = {};
    state.x = 128.0f;
    state.y = 128.0f;
    state.footZ = 147.0f;
    state.verticalVelocity = 0.0f;
    state.supportKind = OpenYAMM::Game::OutdoorSupportKind::BModelFace;
    state.supportBModelIndex = 0;
    state.supportFaceIndex = 0;
    state.airborne = true;
    state.fallStartZ = state.footZ;

    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        0.0f,
        0.0f,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        1.0f / 128.0f);

    CHECK_LT(resolved.x, state.x);
    CHECK_EQ(resolved.supportKind, OpenYAMM::Game::OutdoorSupportKind::BModelFace);
}

TEST_CASE("outdoor stationary party keeps bmodel edge support instead of jiggling to nearby terrain")
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        4);
    mapData.attributeMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);

    OpenYAMM::Game::OutdoorBModel bmodel = {};
    bmodel.vertices = {
        {-128, -128, 112},
        {128, -128, 112},
        {128, 128, 112},
        {-128, 128, 112},
    };
    bmodel.minX = -128;
    bmodel.maxX = 128;
    bmodel.minY = -128;
    bmodel.maxY = 128;
    bmodel.minZ = 112;
    bmodel.maxZ = 112;

    OpenYAMM::Game::OutdoorBModelFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.polygonType = 3;
    bmodel.faces = {floor};
    mapData.bmodels = {bmodel};

    OpenYAMM::Game::OutdoorMovementController movementController(
        mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = {};
    state.x = 140.0f;
    state.y = 0.0f;
    state.footZ = 113.0f;
    state.verticalVelocity = 0.0f;
    state.supportKind = OpenYAMM::Game::OutdoorSupportKind::BModelFace;
    state.supportBModelIndex = 0;
    state.supportFaceIndex = 0;
    state.airborne = false;
    state.fallStartZ = state.footZ;

    const OpenYAMM::Game::OutdoorMoveState stationaryResolved = movementController.resolveMove(
        state,
        0.0f,
        0.0f,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        1.0f / 128.0f);

    CHECK_EQ(stationaryResolved.supportKind, OpenYAMM::Game::OutdoorSupportKind::BModelFace);
    CHECK_EQ(stationaryResolved.footZ, doctest::Approx(113.0f));
    CHECK_FALSE(stationaryResolved.airborne);

    const OpenYAMM::Game::OutdoorMoveState movingResolved = movementController.resolveMove(
        state,
        64.0f,
        0.0f,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        1.0f / 128.0f);

    CHECK_EQ(movingResolved.supportKind, OpenYAMM::Game::OutdoorSupportKind::Terrain);
    CHECK_EQ(movingResolved.footZ, doctest::Approx(129.0f));
}

TEST_CASE("outdoor stationary party uses bmodel stair tread under capsule footprint")
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);
    mapData.attributeMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);

    OpenYAMM::Game::OutdoorBModel bmodel = {};
    bmodel.vertices = {
        {-64, -64, 1424},
        {64, -64, 1424},
        {64, 64, 1424},
        {-64, 64, 1424},
        {65, -64, 1440},
        {193, -64, 1440},
        {193, 64, 1440},
        {65, 64, 1440},
    };
    bmodel.minX = -64;
    bmodel.maxX = 193;
    bmodel.minY = -64;
    bmodel.maxY = 64;
    bmodel.minZ = 1424;
    bmodel.maxZ = 1440;

    OpenYAMM::Game::OutdoorBModelFace lowerTread = {};
    lowerTread.vertexIndices = {0, 1, 2, 3};
    lowerTread.polygonType = 3;

    OpenYAMM::Game::OutdoorBModelFace upperTread = {};
    upperTread.vertexIndices = {4, 5, 6, 7};
    upperTread.polygonType = 3;

    bmodel.faces = {lowerTread, upperTread};
    mapData.bmodels = {bmodel};

    OpenYAMM::Game::OutdoorMovementController movementController(
        mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);

    OpenYAMM::Game::OutdoorMoveState state = {};
    state.x = 50.0f;
    state.y = 0.0f;
    state.footZ = 1440.0f;
    state.verticalVelocity = 0.0f;
    state.supportKind = OpenYAMM::Game::OutdoorSupportKind::BModelFace;
    state.supportBModelIndex = 0;
    state.supportFaceIndex = 0;
    state.airborne = false;
    state.fallStartZ = state.footZ;

    const OpenYAMM::Game::OutdoorMoveState resolved = movementController.resolveMove(
        state,
        0.0f,
        0.0f,
        0.0f,
        false,
        false,
        false,
        false,
        false,
        512.0f,
        0.0f,
        4000.0f,
        1.0f / 128.0f);

    CHECK_EQ(resolved.supportKind, OpenYAMM::Game::OutdoorSupportKind::BModelFace);
    CHECK_EQ(resolved.supportFaceIndex, 1u);
    CHECK_EQ(resolved.footZ, doctest::Approx(1441.0f));
    CHECK_EQ(resolved.verticalVelocity, doctest::Approx(0.0f));
    CHECK_FALSE(resolved.airborne);
}

TEST_CASE("indoor actor movement ignores pre-existing actor overlap")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-512, -512, 0},
        {512, -512, 0},
        {512, 512, 0},
        {-512, 512, 0},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    mapData.faces = {floor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 1;
    sector.nonBspFaceCount = 1;
    sector.minX = -512;
    sector.maxX = 512;
    sector.minY = -512;
    sector.maxY = 512;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.faceIds = {0};
    sector.nonBspFaceIds = {0};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{64.0f, 160.0f};
    const OpenYAMM::Game::IndoorMoveState state =
        movementController.initializeStateFromEyePosition(0.0f, 0.0f, 160.0f, body);
    REQUIRE(state.grounded);

    OpenYAMM::Game::IndoorActorCollision overlappedActor = {};
    overlappedActor.actorIndex = 42;
    overlappedActor.sectorId = state.sectorId;
    overlappedActor.x = 16.0f;
    overlappedActor.y = 0.0f;
    overlappedActor.z = state.footZ;
    overlappedActor.radius = 64.0f;
    overlappedActor.height = 160.0f;
    movementController.setActorColliders({overlappedActor});

    std::vector<size_t> contactedActorIndices;
    const OpenYAMM::Game::IndoorMoveState resolved =
        movementController.resolveMove(
            state,
            body,
            64.0f,
            0.0f,
            false,
            0.5f,
            &contactedActorIndices,
            7);

    CHECK(contactedActorIndices.empty());
    CHECK(resolved.x > state.x + 24.0f);
}

TEST_CASE("indoor steep in-between floor keeps support but rejects uphill walking")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-512, -512, 0},
        {512, -512, 2048},
        {512, 512, 2048},
        {-512, 512, 0},
    };

    OpenYAMM::Game::IndoorFace steepFloor = {};
    steepFloor.vertexIndices = {0, 1, 2, 3};
    steepFloor.facetType = 4;
    steepFloor.roomNumber = 1;
    mapData.faces = {steepFloor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 1;
    sector.nonBspFaceCount = 1;
    sector.minX = -512;
    sector.maxX = 512;
    sector.minY = -512;
    sector.maxY = 512;
    sector.minZ = 0;
    sector.maxZ = 2200;
    sector.floorFaceIds = {0};
    sector.faceIds = {0};
    sector.nonBspFaceIds = {0};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{37.0f, 160.0f};
    OpenYAMM::Game::IndoorMoveState state = {};
    state.x = 0.0f;
    state.y = 0.0f;
    state.footZ = 1024.0f;
    state.eyeHeight = body.height;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    state.supportFaceIndex = 0;
    state.grounded = true;

    const OpenYAMM::Game::IndoorMoveState uphill =
        movementController.resolveMove(state, body, 128.0f, 0.0f, false, 0.25f);

    CHECK(uphill.x <= state.x + 1.0f);
    CHECK(uphill.footZ <= state.footZ + 1.0f);

    const OpenYAMM::Game::IndoorMoveState stationary =
        movementController.resolveMove(state, body, 0.0f, 0.0f, false, 0.25f);

    CHECK(stationary.grounded);
    CHECK_EQ(stationary.supportFaceIndex, 0u);
    CHECK_EQ(stationary.footZ, doctest::Approx(state.footZ));
}

TEST_CASE("indoor lava support applies recurring burning damage")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-512, -512, 0},
        {512, -512, 0},
        {512, 512, 0},
        {-512, 512, 0},
    };

    OpenYAMM::Game::IndoorFace lavaFloor = {};
    lavaFloor.vertexIndices = {0, 1, 2, 3};
    lavaFloor.facetType = 3;
    lavaFloor.roomNumber = 1;
    lavaFloor.textureName = "Lava";
    mapData.faces = {lavaFloor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 1;
    sector.nonBspFaceCount = 1;
    sector.minX = -512;
    sector.maxX = 512;
    sector.minY = -512;
    sector.maxY = 512;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.faceIds = {0};
    sector.nonBspFaceIds = {0};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::IndoorPartyRuntime partyRuntime(std::move(movementController), itemTable);
    partyRuntime.initializeEyePosition(0.0f, 0.0f, 160.0f, true);

    REQUIRE(partyRuntime.movementState().grounded);
    REQUIRE_EQ(partyRuntime.movementState().supportFaceIndex, 0u);
    const int initialHealth = partyRuntime.party().totalHealth();

    partyRuntime.update(0.0f, 0.0f, false, false, 1.0f);

    CHECK_EQ(partyRuntime.party().burningDamageTicks(), 1u);
    CHECK_LT(partyRuntime.party().totalHealth(), initialHealth);
    CHECK_EQ(partyRuntime.party().lastStatus(), "burning damage");
    CHECK_EQ(partyRuntime.movementStatusText(), "You are burning!");
}

TEST_CASE("indoor party runtime applies fall damage after airborne landing")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-512, -512, 0},
        {512, -512, 0},
        {512, 512, 0},
        {-512, 512, 0},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    mapData.faces = {floor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 1;
    sector.nonBspFaceCount = 1;
    sector.minX = -512;
    sector.maxX = 512;
    sector.minY = -512;
    sector.maxY = 512;
    sector.minZ = -512;
    sector.maxZ = 2048;
    sector.floorFaceIds = {0};
    sector.faceIds = {0};
    sector.nonBspFaceIds = {0};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::IndoorPartyRuntime partyRuntime(std::move(movementController), itemTable);
    partyRuntime.initializeEyePosition(0.0f, 0.0f, 928.0f, true);

    REQUIRE_FALSE(partyRuntime.movementState().grounded);
    const int initialHealth = partyRuntime.party().totalHealth();

    for (int i = 0; i < 80 && partyRuntime.party().lastFallDamageDistance() <= 0.0f; ++i)
    {
        partyRuntime.update(0.0f, 0.0f, false, false, 0.1f);
    }

    CHECK(partyRuntime.movementState().grounded);
    CHECK_GT(partyRuntime.party().lastFallDamageDistance(), 512.0f);
    CHECK_LT(partyRuntime.party().totalHealth(), initialHealth);
    CHECK_EQ(partyRuntime.party().lastStatus(), "fall damage");
}

TEST_CASE("indoor movement rejects standing clearance below body height")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, -256, 0},
        {256, -256, 0},
        {256, 256, 0},
        {-256, 256, 0},
        {-256, -256, 100},
        {-256, 256, 100},
        {256, 256, 100},
        {256, -256, 100},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace ceiling = {};
    ceiling.vertexIndices = {4, 5, 6, 7};
    ceiling.facetType = 5;
    ceiling.roomNumber = 1;

    mapData.faces = {floor, ceiling};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.ceilingCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 300;
    sector.floorFaceIds = {0};
    sector.ceilingFaceIds = {1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = {0, 1};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{37.0f, 160.0f};
    OpenYAMM::Game::IndoorMoveState state = {};
    state.x = 300.0f;
    state.y = 0.0f;
    state.footZ = 0.0f;
    state.eyeHeight = body.height;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    state.supportFaceIndex = 0;
    state.grounded = true;

    const OpenYAMM::Game::IndoorMoveState resolved =
        movementController.resolveMove(state, body, -256.0f, 0.0f, false, 0.5f);

    CHECK(resolved.x > 250.0f);
    CHECK_EQ(resolved.footZ, doctest::Approx(state.footZ));
}

TEST_CASE("indoor movement rejects low ceiling even when body top starts above it")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, -256, 0},
        {256, -256, 0},
        {256, 256, 0},
        {-256, 256, 0},
        {-256, -256, 100},
        {-256, 256, 100},
        {256, 256, 100},
        {256, -256, 100},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace ceiling = {};
    ceiling.vertexIndices = {4, 5, 6, 7};
    ceiling.facetType = 5;
    ceiling.roomNumber = 1;

    mapData.faces = {floor, ceiling};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.ceilingCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 300;
    sector.floorFaceIds = {0};
    sector.ceilingFaceIds = {1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = {0, 1};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{37.0f, 160.0f};
    OpenYAMM::Game::IndoorMoveState state = {};
    state.x = 0.0f;
    state.y = 0.0f;
    state.footZ = 0.0f;
    state.eyeHeight = body.height;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    state.supportFaceIndex = 0;
    state.grounded = true;

    const OpenYAMM::Game::IndoorMoveState resolved =
        movementController.resolveMove(state, body, 0.0f, 0.0f, false, 0.25f);

    CHECK_EQ(resolved.footZ, doctest::Approx(state.footZ));
    CHECK(resolved.grounded);
}

TEST_CASE("indoor flying movement can rise below nearby floor surfaces")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, -256, 50},
        {256, -256, 50},
        {256, 256, 50},
        {-256, 256, 50},
        {-256, -256, 200},
        {-256, 256, 200},
        {256, 256, 200},
        {256, -256, 200},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace ceiling = {};
    ceiling.vertexIndices = {4, 5, 6, 7};
    ceiling.facetType = 5;
    ceiling.roomNumber = 1;

    mapData.faces = {floor, ceiling};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.ceilingCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = -64;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.ceilingFaceIds = {1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = {0, 1};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{4.0f, 20.0f};
    OpenYAMM::Game::IndoorMoveState state = {};
    state.x = 0.0f;
    state.y = 0.0f;
    state.footZ = 0.0f;
    state.eyeHeight = body.height;
    state.verticalVelocity = 16.0f;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    state.supportFaceIndex = static_cast<size_t>(-1);
    state.grounded = false;

    const OpenYAMM::Game::IndoorMoveState resolved =
        movementController.resolveMove(
            state,
            body,
            0.0f,
            0.0f,
            false,
            0.25f,
            nullptr,
            std::nullopt,
            false,
            nullptr,
            true);

    CHECK(resolved.footZ > state.footZ);
    CHECK_FALSE(resolved.grounded);
}

TEST_CASE("indoor flying movement is not clamped by portal ceiling samples")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, -256, 0},
        {256, -256, 0},
        {256, 256, 0},
        {-256, 256, 0},
        {-256, -256, 101},
        {-256, 256, 101},
        {256, 256, 101},
        {256, -256, 101},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace portalCeiling = {};
    portalCeiling.vertexIndices = {4, 5, 6, 7};
    portalCeiling.facetType = 5;
    portalCeiling.roomNumber = 1;
    portalCeiling.roomBehindNumber = 2;
    portalCeiling.isPortal = true;
    portalCeiling.attributes = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::IsPortal);

    mapData.faces = {floor, portalCeiling};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.ceilingCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = -256;
    sector.maxY = 256;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.ceilingFaceIds = {1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = {0, 1};
    sector.portalFaceIds = {1};
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController movementController(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{4.0f, 100.0f};
    OpenYAMM::Game::IndoorMoveState state = {};
    state.x = 0.0f;
    state.y = 0.0f;
    state.footZ = 0.0f;
    state.eyeHeight = body.height;
    state.verticalVelocity = 128.0f;
    state.sectorId = 1;
    state.eyeSectorId = 1;
    state.supportFaceIndex = static_cast<size_t>(-1);
    state.grounded = false;

    const OpenYAMM::Game::IndoorMoveState resolved =
        movementController.resolveMove(
            state,
            body,
            0.0f,
            0.0f,
            false,
            1.0f / 128.0f,
            nullptr,
            std::nullopt,
            false,
            nullptr,
            true);

    CHECK(resolved.footZ > state.footZ + 0.9f);
    CHECK_FALSE(resolved.grounded);
}

TEST_CASE("event revealed outdoor bmodel collision updates party and actor movement caches")
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.heightMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);
    mapData.attributeMap.assign(
        OpenYAMM::Game::OutdoorMapData::TerrainWidth * OpenYAMM::Game::OutdoorMapData::TerrainHeight,
        0);

    OpenYAMM::Game::OutdoorBModel bmodel = {};
    bmodel.vertices.push_back({128, -128, 0});
    bmodel.vertices.push_back({128, 128, 0});
    bmodel.vertices.push_back({128, 128, 256});
    bmodel.vertices.push_back({128, -128, 256});

    OpenYAMM::Game::OutdoorBModelFace face = {};
    face.attributes =
        OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible)
        | OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable);
    face.vertexIndices = {0, 1, 2, 3};
    face.planeNormalX = -65536;
    face.planeNormalY = 0;
    face.planeNormalZ = 0;
    face.polygonType = 1;
    bmodel.faces.push_back(face);
    mapData.bmodels.push_back(bmodel);

    OpenYAMM::Game::OutdoorMovementController movementController(
        mapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    const uint32_t revealedAttributes =
        OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);
    movementController.setFaceAttributes(0, 0, revealedAttributes);

    const OpenYAMM::Game::OutdoorMoveState partyStart = movementController.initializeState(0.0f, 0.0f, 0.0f);
    const OpenYAMM::Game::OutdoorMoveState partyResolved = movementController.resolveMove(
        partyStart,
        512.0f,
        0.0f,
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

    CHECK(partyResolved.x < 128.0f);

    OpenYAMM::Game::OutdoorMoveState actorStart = movementController.initializeStateForBody(0.0f, 32.0f, 0.0f, 40.0f);
    std::vector<size_t> contactedActorIndices;
    bx::Vec3 actorResolvedVelocity = {0.0f, 0.0f, 0.0f};
    bool actorResolvedVelocityUpdatesYaw = false;
    const OpenYAMM::Game::OutdoorMoveState actorResolved = movementController.resolveOutdoorActorMove(
        actorStart,
        OpenYAMM::Game::OutdoorBodyDimensions{40.0f, 128.0f},
        512.0f,
        128.0f,
        0.0f,
        false,
        0.5f,
        &contactedActorIndices,
        std::nullopt,
        &actorResolvedVelocity,
        &actorResolvedVelocityUpdatesYaw);

    CHECK(actorResolved.x < 128.0f);
    CHECK(actorResolved.y > actorStart.y);
    CHECK(actorResolvedVelocity.x == doctest::Approx(0.0f).epsilon(0.01));
    CHECK(actorResolvedVelocity.y > 0.0f);
    CHECK(actorResolvedVelocityUpdatesYaw);
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

TEST_CASE("running halves party recovery progress")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->recoverySecondsRemaining = 2.0f;
    party.updateRecovery(1.0f, 0.5f);

    CHECK(pMember->recoverySecondsRemaining == doctest::Approx(1.5f));
}

TEST_CASE("passive regeneration skill restores hit points over time")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    pMember->maxHealth = 200;
    pMember->health = 1;
    pMember->skills["Regeneration"] = {"Regeneration", 200, OpenYAMM::Game::SkillMastery::Grandmaster};
    party.refreshDerivedState();

    CHECK(pMember->healthRegenPerSecond == doctest::Approx(80.0f));

    party.updateRecovery(1.0f);

    CHECK_EQ(pMember->health, 81);
}

TEST_CASE("leather expertise removes leather recovery penalty")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Character normal = makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1);
    OpenYAMM::Game::Character expert = normal;
    const uint32_t leatherArmorId = findFirstItemIdBySkillGroup(gameData.itemTable, "Leather");
    REQUIRE(leatherArmorId != 0);

    normal.equipment.armor = leatherArmorId;
    normal.skills["LeatherArmor"] = {"LeatherArmor", 1, OpenYAMM::Game::SkillMastery::Normal};
    expert.equipment.armor = leatherArmorId;
    expert.skills["LeatherArmor"] = {"LeatherArmor", 1, OpenYAMM::Game::SkillMastery::Expert};

    const OpenYAMM::Game::CharacterAttackProfile normalProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            normal,
            &gameData.itemTable,
            &gameData.spellTable);
    const OpenYAMM::Game::CharacterAttackProfile expertProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            expert,
            &gameData.itemTable,
            &gameData.spellTable);

    CHECK(normalProfile.meleeRecoverySeconds > expertProfile.meleeRecoverySeconds);
}

TEST_CASE("haste reduces player attack recovery")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->equipment.mainHand = findFirstItemIdBySkillGroup(gameData.itemTable, "Sword");
    REQUIRE(pMember->equipment.mainHand != 0);
    pMember->skills["Sword"] = {"Sword", 1, OpenYAMM::Game::SkillMastery::Normal};

    const OpenYAMM::Game::CharacterAttackProfile baseProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            *pMember,
            &gameData.itemTable,
            &gameData.spellTable);

    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::Haste,
        60.0f,
        0,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Haste),
        1,
        OpenYAMM::Game::SkillMastery::Expert,
        0);

    const OpenYAMM::Game::CharacterAttackProfile hastedProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            *pMember,
            &gameData.itemTable,
            &gameData.spellTable);

    CHECK(hastedProfile.meleeRecoverySeconds < baseProfile.meleeRecoverySeconds);
}

TEST_CASE("haste reduces blaster attack recovery")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->equipment.mainHand = findFirstItemIdBySkillGroup(gameData.itemTable, "Blaster");
    REQUIRE(pMember->equipment.mainHand != 0);
    pMember->skills["Blaster"] = {"Blaster", 1, OpenYAMM::Game::SkillMastery::Normal};

    const OpenYAMM::Game::CharacterAttackProfile baseProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            *pMember,
            &gameData.itemTable,
            &gameData.spellTable);

    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::Haste,
        60.0f,
        0,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Haste),
        1,
        OpenYAMM::Game::SkillMastery::Expert,
        0);

    const OpenYAMM::Game::CharacterAttackProfile hastedProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            *pMember,
            &gameData.itemTable,
            &gameData.spellTable);

    CHECK(baseProfile.rangedRecoverySeconds > hastedProfile.rangedRecoverySeconds);
    CHECK(hastedProfile.rangedRecoverySeconds == doctest::Approx(0.0833333f));
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

TEST_CASE("lua random jump advances between repeated event activations")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    local a = evt._RandomJump(451, 1, {2, 5, 8, 11, 14, 20})\n"
        "    local b = evt._RandomJump(451, 1, {2, 5, 8, 11, 14, 20})\n"
        "    local c = evt._RandomJump(451, 1, {2, 5, 8, 11, 14, 20})\n"
        "    local d = evt._RandomJump(451, 1, {2, 5, 8, 11, 14, 20})\n"
        "    local e = evt._RandomJump(451, 1, {2, 5, 8, 11, 14, 20})\n"
        "    evt.StatusText(tostring(a) .. ',' .. tostring(b) .. ',' .. tostring(c) .. ',' .. tostring(d) .. ',' .. tostring(e))\n"
        "    return\n"
        "end\n",
        "@SyntheticRandomJump.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.eventRandomState = 1;

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "2,11,8,5,14");
}

TEST_CASE("history event variables are scoped to the active merged continent")
{
    const uint32_t historySevenVariable =
        static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::HistoryBegin) + 6u;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.Set(" + std::to_string(historySevenVariable) + ", 1)\n"
        "    return\n"
        "end\n",
        "@SyntheticScopedHistory.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    OpenYAMM::Game::setActiveHistoryContinent(runtimeState, 2u);
    CHECK(runtimeState.historyEventTimesByContinent[2u].contains(1u));
    CHECK(runtimeState.historyEventTimesByContinent[2u].contains(2u));

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    CHECK(runtimeState.historyEventTimesByContinent[2u].contains(7u));
    CHECK_FALSE(runtimeState.historyEventTimesByContinent[1u].contains(7u));

    OpenYAMM::Game::setActiveHistoryContinent(runtimeState, 1u);
    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    CHECK(runtimeState.historyEventTimesByContinent[1u].contains(1u));
    CHECK(runtimeState.historyEventTimesByContinent[1u].contains(7u));
    CHECK(runtimeState.historyEventTimesByContinent[2u].contains(7u));
}

TEST_CASE("lua SetSprite stores visibility and decoration id")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt.SetSprite(300, 1, \"6tree06\")\n"
        "    evt.SetSprite(-339, 0, \"swrdstx\")\n"
        "    return\n"
        "end\n",
        "@SyntheticSetSprite.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));

    const auto visibleIterator = runtimeState.spriteOverrides.find(300);
    REQUIRE(visibleIterator != runtimeState.spriteOverrides.end());
    CHECK_FALSE(visibleIterator->second.hidden);
    REQUIRE(visibleIterator->second.textureName.has_value());
    CHECK_EQ(*visibleIterator->second.textureName, "6tree06");

    const auto hiddenIterator = runtimeState.spriteOverrides.find(339);
    REQUIRE(hiddenIterator != runtimeState.spriteOverrides.end());
    CHECK(hiddenIterator->second.hidden);
    REQUIRE(hiddenIterator->second.textureName.has_value());
    CHECK_EQ(*hiddenIterator->second.textureName, "swrdstx");
}

TEST_CASE("level decoration script event id comes from legacy uEventID field")
{
    OpenYAMM::Game::IndoorEntity indoorEntity = {};
    indoorEntity.eventIdPrimary = 1;
    indoorEntity.eventIdSecondary = 376;
    CHECK_EQ(indoorEntity.scriptEventId(), 376u);
    CHECK_EQ(indoorEntity.spriteOverrideKey(7), 1u);

    indoorEntity.eventIdPrimary = 0;
    CHECK_EQ(indoorEntity.spriteOverrideKey(7), 7u);

    OpenYAMM::Game::OutdoorEntity outdoorEntity = {};
    outdoorEntity.eventIdPrimary = 1;
    outdoorEntity.eventIdSecondary = 376;
    CHECK_EQ(outdoorEntity.scriptEventId(), 376u);
    CHECK_EQ(outdoorEntity.spriteOverrideKey(7), 1u);

    outdoorEntity.eventIdPrimary = 0;
    CHECK_EQ(outdoorEntity.spriteOverrideKey(7), 7u);
}

TEST_CASE("interactive decoration rules cover MM6 and MM7 indoor loot decorations")
{
    auto makeDecoration = [](const std::string &internalName, const std::string &hint)
    {
        OpenYAMM::Game::DecorationEntry decoration = {};
        decoration.internalName = internalName;
        decoration.hint = hint;
        return decoration;
    };

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> mm6BarrelSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("bigbarel", "barrel"), "bigbarel");
    REQUIRE(mm6BarrelSpec.has_value());
    CHECK_EQ(mm6BarrelSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::Barrel);
    CHECK_EQ(mm6BarrelSpec->baseEventId, 268u);
    CHECK_EQ(mm6BarrelSpec->eventCount, 8u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> mm7BarrelSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("dec32", "barrel"), "dec32");
    REQUIRE(mm7BarrelSpec.has_value());
    CHECK_EQ(mm7BarrelSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::Barrel);
    CHECK_EQ(mm7BarrelSpec->baseEventId, 268u);
    CHECK_EQ(mm7BarrelSpec->eventCount, 8u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> flourSackSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("floursac", "sack"), "floursac");
    REQUIRE(flourSackSpec.has_value());
    CHECK_EQ(flourSackSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::FlourSack);
    CHECK_EQ(flourSackSpec->baseEventId, 1741u);
    CHECK_EQ(flourSackSpec->eventCount, 2u);
    CHECK_EQ(OpenYAMM::Game::initialInteractiveDecorationState(flourSackSpec->family, 13u), 1u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> largeBagSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("bag01", "bag"), "bag01");
    REQUIRE(largeBagSpec.has_value());
    CHECK_EQ(largeBagSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::LargeBag);
    CHECK_EQ(largeBagSpec->baseEventId, 1743u);
    CHECK_EQ(largeBagSpec->eventCount, 5u);
    CHECK_EQ(OpenYAMM::Game::initialInteractiveDecorationState(largeBagSpec->family, 0u), 1u);
    CHECK_EQ(OpenYAMM::Game::initialInteractiveDecorationState(largeBagSpec->family, 3u), 4u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> smallBagSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("bag_A", "bag"), "bag_A");
    REQUIRE(smallBagSpec.has_value());
    CHECK_EQ(smallBagSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::LargeBag);
    CHECK_EQ(smallBagSpec->baseEventId, 1743u);
    CHECK_EQ(smallBagSpec->eventCount, 5u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> bucketSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("Bucket", "bucket"), "Bucket");
    REQUIRE(bucketSpec.has_value());
    CHECK_EQ(bucketSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::Bucket);
    CHECK_EQ(bucketSpec->baseEventId, 1755u);
    CHECK_EQ(bucketSpec->eventCount, 4u);
    CHECK_EQ(OpenYAMM::Game::initialInteractiveDecorationState(bucketSpec->family, 0u), 1u);
    CHECK_EQ(OpenYAMM::Game::initialInteractiveDecorationState(bucketSpec->family, 2u), 3u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> mm6TrashHeapSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("trasheap", "trash heap"), "trasheap");
    REQUIRE(mm6TrashHeapSpec.has_value());
    CHECK_EQ(mm6TrashHeapSpec->family, OpenYAMM::Game::InteractiveDecorationFamily::MightAndMagicSixTrashHeap);
    CHECK_EQ(mm6TrashHeapSpec->baseEventId, 1748u);
    CHECK_EQ(mm6TrashHeapSpec->eventCount, 2u);
    CHECK_EQ(OpenYAMM::Game::initialInteractiveDecorationState(mm6TrashHeapSpec->family, 27u), 1u);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> mm7BeaconFireSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("dec61", "beacon fire"), "dec61");
    REQUIRE(mm7BeaconFireSpec.has_value());
    CHECK_EQ(mm7BeaconFireSpec->baseEventId, 550u);
    CHECK_EQ(mm7BeaconFireSpec->eventCount, 7u);
    CHECK(mm7BeaconFireSpec->useSeededInitialState);

    const std::optional<OpenYAMM::Game::InteractiveDecorationBindingSpec> mm8BeaconFireSpec =
        OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("dec40", "beacon fire"), "dec40");
    REQUIRE(mm8BeaconFireSpec.has_value());
    CHECK_EQ(mm8BeaconFireSpec->baseEventId, 543u);
    CHECK_EQ(mm8BeaconFireSpec->eventCount, 7u);
    CHECK(mm8BeaconFireSpec->useSeededInitialState);

    CHECK_FALSE(OpenYAMM::Game::resolveInteractiveDecorationBindingSpec(makeDecoration("", "bag"), "").has_value());
}

TEST_CASE("indoor decoration activation can use global events without local id collisions")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localProgram = loadSyntheticScriptedProgram(
        "evt.map[269] = function()\n"
        "    evt._BeginEvent(269)\n"
        "    evt.StatusText(\"local collision\")\n"
        "    return\n"
        "end\n",
        "@SyntheticIndoorDecorationLocalCollision.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalProgram = loadSyntheticScriptedProgram(
        "evt.global[268] = function()\n"
        "    evt._BeginEvent(268)\n"
        "    evt.StatusText(\"empty barrel\")\n"
        "    return\n"
        "end\n"
        "evt.global[269] = function()\n"
        "    evt._BeginEvent(269)\n"
        "    evt.StatusText(\"global barrel\")\n"
        "    evt.ChangeEvent(268)\n"
        "    return\n"
        "end\n",
        "@SyntheticIndoorDecorationGlobal.lua",
        OpenYAMM::Game::ScriptedEventScope::Global);
    REQUIRE(localProgram.has_value());
    REQUIRE(globalProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState localState = {};

    REQUIRE(eventRuntime.executeEventById(localProgram, globalProgram, 269, localState, nullptr, nullptr));
    REQUIRE_FALSE(localState.statusMessages.empty());
    CHECK_EQ(localState.statusMessages.back(), "local collision");

    OpenYAMM::Game::EventRuntimeState decorationState = {};
    decorationState.decorVars[0] = 1;
    OpenYAMM::Game::EventRuntimeState::ActiveDecorationContext context = {};
    context.decorVarIndex = 0;
    context.baseEventId = 268;
    context.currentEventId = 269;
    context.eventCount = 8;
    decorationState.activeDecorationContext = context;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 269, decorationState, nullptr, nullptr));
    REQUIRE_FALSE(decorationState.statusMessages.empty());
    CHECK_EQ(decorationState.statusMessages.back(), "global barrel");
    CHECK_EQ(decorationState.decorVars[0], 0u);
}

TEST_CASE("lua event runtime stores question answer metadata and resumes continuation step")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[166] = function(continueStep)\n"
        "    evt._BeginEvent(166)\n"
        "    if continueStep == 4 then\n"
        "        evt.SimpleMessage(\"ok\")\n"
        "        return\n"
        "    end\n"
        "    if continueStep == 2 then\n"
        "        evt.SimpleMessage(\"bad\")\n"
        "        return\n"
        "    end\n"
        "    evt.AskQuestion(166, 2, 603, 4, 104, 105, \"question\", {\"egg\", \"an egg\"})\n"
        "    return nil\n"
        "end\n",
        "@SyntheticAskQuestion.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 166, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::MapEvent);
    REQUIRE(runtimeState.pendingInputPrompt.has_value());
    CHECK_EQ(runtimeState.pendingInputPrompt->eventId, 166);
    CHECK_EQ(runtimeState.pendingInputPrompt->continueStep, 2);
    CHECK_EQ(runtimeState.pendingInputPrompt->correctStep, 4);
    CHECK_EQ(runtimeState.pendingInputPrompt->textId, 603u);
    REQUIRE_EQ(runtimeState.pendingInputPrompt->answerTextIds.size(), 2u);
    CHECK_EQ(runtimeState.pendingInputPrompt->answerTextIds[0], 104u);
    CHECK_EQ(runtimeState.pendingInputPrompt->answerTextIds[1], 105u);
    REQUIRE_EQ(runtimeState.pendingInputPrompt->answers.size(), 2u);
    CHECK_EQ(runtimeState.pendingInputPrompt->answers[0], "egg");
    CHECK_EQ(runtimeState.pendingInputPrompt->answers[1], "an egg");
    REQUIRE_FALSE(runtimeState.messages.empty());
    CHECK_EQ(runtimeState.messages.back(), "question");

    const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
        runtimeState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        0.0f);
    CHECK(dialog.isActive);
    REQUIRE_FALSE(dialog.lines.empty());
    CHECK_EQ(dialog.lines.back(), "question");

    OpenYAMM::Game::EventRuntimeState emptyMapEventState = {};
    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext emptyMapEventContext = {};
    emptyMapEventContext.kind = OpenYAMM::Game::DialogueContextKind::MapEvent;
    emptyMapEventState.pendingDialogueContext = emptyMapEventContext;
    const OpenYAMM::Game::EventDialogContent emptyDialog = OpenYAMM::Game::buildEventDialogContent(
        emptyMapEventState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        0.0f);
    CHECK_FALSE(emptyDialog.isActive);

    runtimeState.pendingInputPrompt.reset();

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 166, runtimeState, nullptr, nullptr, 4));
    REQUIRE_FALSE(runtimeState.messages.empty());
    CHECK_EQ(runtimeState.messages.back(), "ok");
}

TEST_CASE("lua SetMessage is pending text until a display opcode consumes it")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> setOnlyProgram = loadSyntheticScriptedProgram(
        "evt.map[10] = function()\n"
        "    evt._BeginEvent(10)\n"
        "    evt.SetMessage(\"Exit\")\n"
        "end\n",
        "@SyntheticSetMessageOnly.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(setOnlyProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(setOnlyProgram, std::nullopt, 10, runtimeState, nullptr, nullptr));
    CHECK_FALSE(runtimeState.pendingDialogueContext.has_value());
    CHECK(runtimeState.messages.empty());

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> pressAnyKeyProgram = loadSyntheticScriptedProgram(
        "evt.map[11] = function()\n"
        "    evt._BeginEvent(11)\n"
        "    evt.SetMessage(\"Read this\")\n"
        "    evt._PressAnyKey(11, 3)\n"
        "end\n",
        "@SyntheticSetMessagePressAnyKey.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(pressAnyKeyProgram.has_value());

    runtimeState = {};
    REQUIRE(eventRuntime.executeEventById(pressAnyKeyProgram, std::nullopt, 11, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::MapEvent);
    REQUIRE(runtimeState.pendingInputPrompt.has_value());
    REQUIRE_FALSE(runtimeState.messages.empty());
    CHECK_EQ(runtimeState.messages.back(), "Read this");

    const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
        runtimeState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        0.0f);
    CHECK(dialog.isActive);
    CHECK(dialog.title.empty());
    REQUIRE_FALSE(dialog.lines.empty());
    CHECK_EQ(dialog.lines.back(), "Read this");
}

TEST_CASE("lua AskQuestion uses existing map message as dialog body")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[69] = function()\n"
        "    evt._BeginEvent(69)\n"
        "    evt.SimpleMessage(\"Restricted area - Keep out.\")\n"
        "    evt.AskQuestion(69, 17, 14, 20, 15, 16, \"What's the password?\", {\"JBARD\", \"jbard\"})\n"
        "    return nil\n"
        "end\n",
        "@SyntheticQuestionWithMessage.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 69, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.pendingInputPrompt.has_value());
    REQUIRE(runtimeState.pendingInputPrompt->text.has_value());
    CHECK_EQ(*runtimeState.pendingInputPrompt->text, "What's the password?");
    REQUIRE_EQ(runtimeState.messages.size(), 1u);
    CHECK_EQ(runtimeState.messages.back(), "Restricted area - Keep out.");

    const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
        runtimeState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        0.0f);
    CHECK(dialog.isActive);
    CHECK(dialog.title.empty());
    REQUIRE_EQ(dialog.lines.size(), 1u);
    CHECK_EQ(dialog.lines[0], "Restricted area - Keep out.");
}

TEST_CASE("lua on-load runtime preserves preseeded named globals")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[77] = function()\n"
        "    evt._BeginEvent(77)\n"
        "    evt.SetGlobalVar(\"Story.SeenOnLoad\", evt.GetGlobalVar(\"Story.Preseed\", 0))\n"
        "end\n",
        "@SyntheticNamedGlobalOnLoad.lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        {77});
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.namedGlobalVars["Story.Preseed"] = 42;

    REQUIRE(eventRuntime.buildOnLoadState(scriptedProgram, std::nullopt, std::nullopt, runtimeState));
    CHECK_EQ(runtimeState.namedGlobalVars["Story.Preseed"], 42);
    CHECK_EQ(runtimeState.namedGlobalVars["Story.SeenOnLoad"], 42);
}

TEST_CASE("lua map event continuations prefer local handlers over colliding global handlers")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localProgram = loadSyntheticScriptedProgram(
        "evt.map[69] = function(continueStep)\n"
        "    evt._BeginEvent(69)\n"
        "    if continueStep == 4 then\n"
        "        evt.SimpleMessage(\"local\")\n"
        "        return\n"
        "    end\n"
        "    evt.AskQuestion(69, 4, 0, 0, 0, 0, \"password\", {\"JBARD\"})\n"
        "    return nil\n"
        "end\n",
        "@SyntheticLocalMapEvent.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalProgram = loadSyntheticScriptedProgram(
        "evt.global[69] = function()\n"
        "    evt._BeginEvent(69)\n"
        "    evt.SimpleMessage(\"global\")\n"
        "    return\n"
        "end\n",
        "@SyntheticGlobalEvent.lua",
        OpenYAMM::Game::ScriptedEventScope::Global);
    REQUIRE(localProgram.has_value());
    REQUIRE(globalProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(localProgram, globalProgram, 69, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.pendingInputPrompt.has_value());
    CHECK_EQ(runtimeState.messages.back(), "password");

    runtimeState.pendingInputPrompt.reset();
    REQUIRE(eventRuntime.executeEventById(localProgram, globalProgram, 69, runtimeState, nullptr, nullptr, 4));
    CHECK_EQ(runtimeState.messages.back(), "local");

    OpenYAMM::Game::EventRuntimeState npcTopicRuntimeState = {};
    REQUIRE(eventRuntime.executeNpcTopicEventById(
        localProgram,
        globalProgram,
        69,
        npcTopicRuntimeState,
        nullptr,
        nullptr));
    CHECK_EQ(npcTopicRuntimeState.messages.back(), "global");

    OpenYAMM::Game::EventRuntimeState mapDialogTopicRuntimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext mapDialogContext = {};
    mapDialogContext.kind = OpenYAMM::Game::DialogueContextKind::MapEvent;
    mapDialogTopicRuntimeState.pendingDialogueContext = mapDialogContext;

    REQUIRE(eventRuntime.executeNpcTopicEventById(
        localProgram,
        globalProgram,
        69,
        mapDialogTopicRuntimeState,
        nullptr,
        nullptr));
    REQUIRE(mapDialogTopicRuntimeState.pendingInputPrompt.has_value());
    CHECK_EQ(mapDialogTopicRuntimeState.messages.back(), "password");
}

TEST_CASE("lua event runtime Set applies condition variables")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.Set(0x72, 0)\n"
        "    return\n"
        "end\n",
        "@SyntheticSetCondition.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setActiveMemberIndex(1);

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    const OpenYAMM::Game::Character *pActiveMember = party.member(1);
    REQUIRE(pActiveMember != nullptr);
    CHECK(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseMedium)));
    REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
    CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::Disease);
    REQUIRE_EQ(runtimeState.portraitFxRequests.front().memberIndices.size(), 1u);
    CHECK_EQ(runtimeState.portraitFxRequests.front().memberIndices.front(), 1u);
}

TEST_CASE("event runtime queues qbit portrait fx only for visible quest entries")
{
    OpenYAMM::Game::JournalQuestTable questTable = {};
    REQUIRE(questTable.loadFromRows({
        {"5", "Kill the leader of the Regnan Pirate outpost at Dagger Wound.", "", ""},
        {"777", "", "Internal bookkeeping qbit", ""}
    }));

    OpenYAMM::Game::Party party = {};
    party.setJournalQuestTable(&questTable);
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const OpenYAMM::Game::EventRuntime::VariableRef visibleQbit =
        OpenYAMM::Game::EventRuntime::decodeVariable(
            (5u << 16) | static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::QBits));
    const OpenYAMM::Game::EventRuntime::VariableRef internalQbit =
        OpenYAMM::Game::EventRuntime::decodeVariable(
            (777u << 16) | static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::QBits));

    OpenYAMM::Game::EventRuntime::setVariableValue(runtimeState, visibleQbit, 1, &party, {0});
    REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
    CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::QuestComplete);
    REQUIRE_EQ(runtimeState.pendingSounds.size(), 1u);
    CHECK_EQ(runtimeState.pendingSounds.front().soundId, static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));

    runtimeState.portraitFxRequests.clear();
    runtimeState.pendingSounds.clear();

    OpenYAMM::Game::EventRuntime::setVariableValue(runtimeState, visibleQbit, 1, &party, {0});
    CHECK(runtimeState.portraitFxRequests.empty());
    CHECK(runtimeState.pendingSounds.empty());

    OpenYAMM::Game::EventRuntime::addVariableValue(runtimeState, internalQbit, 777, &party, {0});
    CHECK(party.hasQuestBit(777));
    CHECK(runtimeState.portraitFxRequests.empty());
    CHECK(runtimeState.pendingSounds.empty());

    OpenYAMM::Game::EventRuntime::subtractVariableValue(runtimeState, visibleQbit, 5, &party, {0});
    CHECK_FALSE(party.hasQuestBit(5));
    CHECK(runtimeState.portraitFxRequests.empty());
    CHECK(runtimeState.pendingSounds.empty());
}

TEST_CASE("event runtime queues one quest sound for stat and autonote portrait fx")
{
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const OpenYAMM::Game::EventRuntime::VariableRef baseMight =
        OpenYAMM::Game::EventRuntime::decodeVariable(
            static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::BaseMight));
    const OpenYAMM::Game::EventRuntime::VariableRef autoNote =
        OpenYAMM::Game::EventRuntime::decodeVariable(
            (17u << 16) | static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::AutoNotes));

    OpenYAMM::Game::EventRuntime::addVariableValue(runtimeState, baseMight, 2, &party, {0});
    OpenYAMM::Game::EventRuntime::setVariableValue(runtimeState, autoNote, 17, &party, {0});

    REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 2u);
    CHECK_EQ(runtimeState.portraitFxRequests[0].kind, OpenYAMM::Game::PortraitFxEventKind::StatIncrease);
    CHECK_EQ(runtimeState.portraitFxRequests[1].kind, OpenYAMM::Game::PortraitFxEventKind::AutoNote);
    REQUIRE_EQ(runtimeState.pendingSounds.size(), 1u);
    CHECK_EQ(runtimeState.pendingSounds.front().soundId, static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));
}

TEST_CASE("lua event runtime Subtract clears condition variables")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.Subtract(0x72, 0)\n"
        "    return\n"
        "end\n",
        "@SyntheticSubtractCondition.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setActiveMemberIndex(1);
    OpenYAMM::Game::Character *pActiveMember = party.member(1);
    REQUIRE(pActiveMember != nullptr);
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseMedium));

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    CHECK_FALSE(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseMedium)));
}

TEST_CASE("lua event runtime door locked reaction targets active member")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(5)\n"
        "    evt.FaceAnimation(18)\n"
        "    return\n"
        "end\n",
        "@SyntheticDoorLockedReaction.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setActiveMemberIndex(2);

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    const std::vector<OpenYAMM::Game::Party::PendingAudioRequest> &requests = party.pendingAudioRequests();
    REQUIRE_EQ(requests.size(), 1u);
    CHECK_EQ(requests.front().kind, OpenYAMM::Game::Party::PendingAudioRequest::Kind::Speech);
    CHECK_EQ(requests.front().memberIndex, 2u);
    CHECK_EQ(requests.front().speechId, OpenYAMM::Game::SpeechId::DoorLocked);
}

TEST_CASE("lua event runtime maps non-door face animations to speech reactions")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(1)\n"
        "    evt.FaceAnimation(47)\n"
        "    evt.FaceAnimation(74)\n"
        "    return\n"
        "end\n",
        "@SyntheticFaceAnimationReactions.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    const std::vector<OpenYAMM::Game::Party::PendingAudioRequest> &requests = party.pendingAudioRequests();
    REQUIRE_EQ(requests.size(), 2u);
    CHECK_EQ(requests[0].memberIndex, 1u);
    CHECK_EQ(requests[0].speechId, OpenYAMM::Game::SpeechId::LeaveDungeon);
    CHECK_EQ(requests[1].memberIndex, 1u);
    CHECK_EQ(requests[1].speechId, OpenYAMM::Game::SpeechId::ShopRepair);
}

TEST_CASE("lua event CheckSkill supports effective checks and explicit mastery checks")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(5)\n"
        "    if evt.CheckSkill(31, 0, 8) then\n"
        "        evt.StatusText(\"skill pass\")\n"
        "    else\n"
        "        evt.StatusText(\"skill fail\")\n"
        "    end\n"
        "    return\n"
        "end\n"
        "evt.map[2] = function()\n"
        "    evt._BeginEvent(2)\n"
        "    evt.ForPlayer(5)\n"
        "    if evt.CheckSkill(94, 3, 40) then\n"
        "        evt.StatusText(\"gm pass\")\n"
        "    else\n"
        "        evt.StatusText(\"gm fail\")\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticCheckSkill.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->skills["Perception"] = {"Perception", 4, OpenYAMM::Game::SkillMastery::Expert};
    pMember->skills["DisarmTraps"] = {"DisarmTraps", 40, OpenYAMM::Game::SkillMastery::Grandmaster};

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "skill pass");

    pMember->skills["Perception"] = {"Perception", 7, OpenYAMM::Game::SkillMastery::Normal};
    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "skill fail");

    pMember->skills["Perception"] = {"Perception", 40, OpenYAMM::Game::SkillMastery::Master};
    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 2, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "gm fail");

    pMember->skills["Perception"] = {"Perception", 1, OpenYAMM::Game::SkillMastery::Grandmaster};
    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 2, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "gm pass");

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> disarmProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(5)\n"
        "    if evt.CheckSkill(33, 3, 40) then\n"
        "        evt.StatusText(\"disarm pass\")\n"
        "    else\n"
        "        evt.StatusText(\"disarm fail\")\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticCheckDisarmSkill.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(disarmProgram.has_value());

    pMember->skills["DisarmTraps"] = {"DisarmTraps", 1, OpenYAMM::Game::SkillMastery::Grandmaster};
    REQUIRE(eventRuntime.executeEventById(disarmProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "disarm pass");

    pMember->skills.erase("DisarmTraps");
    OpenYAMM::Game::Character *pOtherMember = party.member(1);
    REQUIRE(pOtherMember != nullptr);
    pOtherMember->skills["DisarmTraps"] = {"DisarmTraps", 1, OpenYAMM::Game::SkillMastery::Grandmaster};
    REQUIRE(eventRuntime.executeEventById(disarmProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "disarm pass");
}

TEST_CASE("lua event DamagePlayer uses its explicit player argument")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(5)\n"
        "    evt.DamagePlayer(0, 0, 10)\n"
        "    return\n"
        "end\n",
        "@SyntheticDamagePlayerTarget.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        OpenYAMM::Game::Character *pMember = party.member(memberIndex);
        REQUIRE(pMember != nullptr);
        pMember->health = 100;
        pMember->maxHealth = 100;
    }

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_GE(party.members().size(), 2u);
    CHECK_EQ(party.members()[0].health, 90);
    CHECK_EQ(party.members()[1].health, 100);
}

TEST_CASE("lua event player bits are character specific and unbounded")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.ForPlayer(0)\n"
        "    evt.Add(4522215, 69)\n"
        "    evt.ForPlayer(1)\n"
        "    if evt.Cmp(4522215, 69) then\n"
        "        evt.StatusText(\"member1 set\")\n"
        "    else\n"
        "        evt.StatusText(\"member1 clear\")\n"
        "    end\n"
        "    evt.ForPlayer(0)\n"
        "    if evt.Cmp(4522215, 69) then\n"
        "        evt.StatusText(\"member0 set\")\n"
        "    else\n"
        "        evt.StatusText(\"member0 clear\")\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticPlayerBits.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_GE(runtimeState.statusMessages.size(), 2u);
    CHECK_EQ(runtimeState.statusMessages[runtimeState.statusMessages.size() - 2], "member1 clear");
    CHECK_EQ(runtimeState.statusMessages.back(), "member0 set");

    const OpenYAMM::Game::Character *pMember0 = party.member(0);
    const OpenYAMM::Game::Character *pMember1 = party.member(1);
    REQUIRE(pMember0 != nullptr);
    REQUIRE(pMember1 != nullptr);
    CHECK(pMember0->playerBits.contains(69));
    CHECK_FALSE(pMember1->playerBits.contains(69));
}

TEST_CASE("lua class promotion API uses merged class metadata")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    if evt.GetClassId(\"Knight\") == 16 then\n"
        "        evt.StatusText(\"knight id ok\")\n"
        "    end\n"
        "    if evt.GetPlayerClass(0) == 16 then\n"
        "        evt.StatusText(\"member class ok\")\n"
        "    end\n"
        "    if evt.CanClassLearnSkill(19, \"Sword\", 4) then\n"
        "        evt.StatusText(\"champion sword ok\")\n"
        "    end\n"
        "    if evt.SetPlayerClass(0, 19) then\n"
        "        evt.StatusText(evt.GetPlayerClassName(0))\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticClassPromotionApi.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setClassSkillTable(&gameData.classSkillTable);

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_GE(runtimeState.statusMessages.size(), 4u);
    CHECK_EQ(runtimeState.statusMessages[runtimeState.statusMessages.size() - 4], "knight id ok");
    CHECK_EQ(runtimeState.statusMessages[runtimeState.statusMessages.size() - 3], "member class ok");
    CHECK_EQ(runtimeState.statusMessages[runtimeState.statusMessages.size() - 2], "champion sword ok");
    CHECK_EQ(runtimeState.statusMessages.back(), "Champion");

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    CHECK_EQ(pMember->className, "Champion");
}

TEST_CASE("lua event inventory possession checks include equipped items")
{
    constexpr uint32_t CloakOfBaaItemId = 2105;
    constexpr uint32_t InventoryVariableTag = 0x0011;
    const uint32_t cloakInventoryVariable = (CloakOfBaaItemId << 16) | InventoryVariableTag;

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        std::string("evt.map[1] = function()\n")
        + "    evt._BeginEvent(1)\n"
        + "    evt.ForPlayer(5)\n"
        "    if evt.Cmp(" + std::to_string(cloakInventoryVariable) + ", 1) then\n"
        "        evt.StatusText(\"has cloak\")\n"
        "    else\n"
        "        evt.StatusText(\"missing cloak\")\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticInventoryEquipped.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->inventory.clear();
    pMember->equipment.cloak = CloakOfBaaItemId;

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "has cloak");
}

TEST_CASE("lua event runtime SpeakNPC opens pending npc talk dialogue")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[451] = function()\n"
        "    evt._BeginEvent(451)\n"
        "    evt.SpeakNPC(39)\n"
        "    return\n"
        "end\n",
        "@SyntheticSpeakNpc.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 451, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::NpcTalk);
    CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 39u);
    CHECK_EQ(runtimeState.pendingDialogueContext->hostHouseId, 0u);
}

TEST_CASE("lua event runtime onload executes SpeakNPC handlers")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[451] = function()\n"
        "    evt._BeginEvent(451)\n"
        "    evt.SpeakNPC(39)\n"
        "    return\n"
        "end\n"
        "evt.map[452] = function()\n"
        "    evt._BeginEvent(452)\n"
        "    evt.StatusText(\"setup still ran\")\n"
        "    return\n"
        "end\n",
        "@SyntheticOnLoadSpeakNpc.lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        {451, 452});
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.buildOnLoadState(scriptedProgram, std::nullopt, std::nullopt, runtimeState));
    CHECK_EQ(runtimeState.localOnLoadEventsExecuted, 2u);
    CHECK_EQ(runtimeState.globalOnLoadEventsExecuted, 0u);
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::NpcTalk);
    CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 39u);
}

TEST_CASE("lua event debug print includes source and line")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[700] = function()\n"
        "    evt._BeginEvent(700)\n"
        "    evt.Debug(\"alpha\", 42, true)\n"
        "end\n",
        "@SyntheticDebugPrint.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    std::ostringstream capturedOutput;
    std::streambuf *pPreviousBuffer = std::cout.rdbuf(capturedOutput.rdbuf());

    const bool executed =
        eventRuntime.executeEventById(scriptedProgram, std::nullopt, 700, runtimeState, nullptr, nullptr);
    std::cout.rdbuf(pPreviousBuffer);

    REQUIRE(executed);
    CHECK_EQ(capturedOutput.str(), "[SyntheticDebugPrint.lua:3]: alpha\t42\ttrue\n");
}

TEST_CASE("lua event runtime onload sees party quest bits")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[2] = function()\n"
        "    evt._BeginEvent(2)\n"
        "    if evt.Cmp(2359312, 36) then\n"
        "        evt.SetFacetBit(25, 0x00002000, 0)\n"
        "    else\n"
        "        evt.SetFacetBit(25, 0x00002000, 1)\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticOnLoadPartyQuestBit.lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        {2});
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setQuestBit(36, true);

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const uint32_t invisibleBit = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);

    REQUIRE(eventRuntime.executeOnLoadEvents(scriptedProgram, std::nullopt, runtimeState, &party, nullptr));
    CHECK_EQ(runtimeState.localOnLoadEventsExecuted, 1u);
    REQUIRE(runtimeState.facetClearMasks.contains(25));
    CHECK((runtimeState.facetClearMasks.at(25) & invisibleBit) != 0);

    const auto setIt = runtimeState.facetSetMasks.find(25);
    const bool invisibleBitWasSet =
        setIt != runtimeState.facetSetMasks.end() && (setIt->second & invisibleBit) != 0;
    CHECK_FALSE(invisibleBitWasSet);
}

TEST_CASE("lua event runtime onload sets party quest bits")
{
    constexpr uint32_t QBitId = 721;
    constexpr uint32_t QBitSelector = (QBitId << 16) | static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::QBits);

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    if not evt.Cmp(" + std::to_string(QBitSelector) + ", " + std::to_string(QBitId) + ") then\n"
        "        evt.Add(" + std::to_string(QBitSelector) + ", " + std::to_string(QBitId) + ")\n"
        "    end\n"
        "    return\n"
        "end\n",
        "@SyntheticOnLoadSetPartyQuestBit.lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        {1});
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    party.setQuestBit(QBitId, false);

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeOnLoadEvents(scriptedProgram, std::nullopt, runtimeState, &party, nullptr));
    CHECK_EQ(runtimeState.localOnLoadEventsExecuted, 1u);
    CHECK(party.hasQuestBit(QBitId));
}

TEST_CASE("dagger wound onload seeds starting roster quest bits")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    REQUIRE(gameData.out01LocalEventProgram.has_value());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeOnLoadEvents(
        gameData.out01LocalEventProgram,
        gameData.globalEventProgram,
        runtimeState,
        &party,
        nullptr));
    CHECK_EQ(runtimeState.localOnLoadEventsExecuted, 4u);
    CHECK(party.hasQuestBit(226));
    CHECK(party.hasQuestBit(306));
    CHECK(party.hasQuestBit(401));
    CHECK(party.hasQuestBit(407));
}

TEST_CASE("lua event runtime resolves MM8 invisible event variable alias")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    if evt.Cmp(316, 0) then\n"
        "        evt.StatusText(\"blocked\")\n"
        "        return\n"
        "    end\n"
        "    evt.StatusText(\"warning\")\n"
        "    return\n"
        "end\n",
        "@SyntheticMm8InvisibleAlias.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "warning");

    runtimeState.statusMessages.clear();
    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::Invisibility,
        60.0f,
        0,
        0,
        0,
        OpenYAMM::Game::SkillMastery::Normal,
        0);

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, &party, nullptr));
    REQUIRE_FALSE(runtimeState.statusMessages.empty());
    CHECK_EQ(runtimeState.statusMessages.back(), "blocked");
}

TEST_CASE("lua event runtime separates persistent actor masks from current hostility requests")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.SetMonGroupBit(44, 0x01000000, 1)\n"
        "    return\n"
        "end\n"
        "evt.map[2] = function()\n"
        "    evt._BeginEvent(2)\n"
        "    evt.StatusText(\"plate reset\")\n"
        "    return\n"
        "end\n",
        "@SyntheticHostilityRequests.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const uint32_t hostileBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.actorGroupSetMasks.contains(44));
    CHECK((runtimeState.actorGroupSetMasks.at(44) & hostileBit) != 0);
    REQUIRE(runtimeState.actorGroupHostilityRequests.contains(44));
    CHECK(runtimeState.actorGroupHostilityRequests.at(44));

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 2, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.actorGroupSetMasks.contains(44));
    CHECK((runtimeState.actorGroupSetMasks.at(44) & hostileBit) != 0);
    CHECK(runtimeState.actorGroupHostilityRequests.empty());
}

TEST_CASE("lua event runtime treats numeric zero as false for actor group bits")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.SetMonGroupBit(44, 0x01000000, 0)\n"
        "    return\n"
        "end\n",
        "@SyntheticNumericZeroActorGroupBit.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const uint32_t hostileBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.actorGroupClearMasks.contains(44));
    CHECK((runtimeState.actorGroupClearMasks.at(44) & hostileBit) != 0);
    CHECK_FALSE(runtimeState.actorGroupSetMasks.contains(44));
    REQUIRE(runtimeState.actorGroupHostilityRequests.contains(44));
    CHECK_FALSE(runtimeState.actorGroupHostilityRequests.at(44));
}

TEST_CASE("lua event runtime treats numeric zero as false for facet bits")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.SetFacetBit(25, 0x00002000, 0)\n"
        "    return\n"
        "end\n",
        "@SyntheticNumericZeroFacetBit.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const uint32_t invisibleBit = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.facetClearMasks.contains(25));
    CHECK((runtimeState.facetClearMasks.at(25) & invisibleBit) != 0);

    const auto setIt = runtimeState.facetSetMasks.find(25);
    const bool invisibleBitWasSet =
        setIt != runtimeState.facetSetMasks.end() && (setIt->second & invisibleBit) != 0;
    CHECK_FALSE(invisibleBitWasSet);
}

TEST_CASE("save preview bmp decoder accepts current 32 bit preview payloads")
{
    const std::vector<uint8_t> sourcePixels = {
        10, 20, 30, 255,
        40, 50, 60, 128
    };
    const std::vector<uint8_t> bmp = OpenYAMM::Game::SavePreviewImage::encodeBgraToBmp(2, 1, sourcePixels);
    REQUIRE_FALSE(bmp.empty());

    int width = 0;
    int height = 0;
    std::vector<uint8_t> decodedPixels;
    CHECK(OpenYAMM::Game::SavePreviewImage::decodeBmpBytesToBgra(bmp, width, height, decodedPixels));
    CHECK_EQ(width, 2);
    CHECK_EQ(height, 1);
    CHECK_EQ(decodedPixels, sourcePixels);
}

TEST_CASE("lua MoveToMap with transition ids opens shared transition dialog instead of immediate move")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.MoveToMap(-500, -1567, -63, 512, 0, 0, 363, 9, \"\1D18.blv\")\n"
        "    return\n"
        "end\n",
        "@SyntheticDungeonTransition.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    CHECK_FALSE(runtimeState.pendingMapMove.has_value());
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::MapTransition);
    REQUIRE(runtimeState.pendingDialogueContext->transitionMapMove.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->transitionMapMove->mapName, std::optional<std::string>("D18.blv"));
    CHECK_EQ(runtimeState.pendingDialogueContext->transitionMapMove->x, -500);
    CHECK_EQ(runtimeState.pendingDialogueContext->transitionTextId, 363u);
    CHECK_EQ(runtimeState.pendingDialogueContext->transitionImageId, 9u);
}

TEST_CASE("lua MoveToMap without transition ids queues direct map move")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.MoveToMap(12808, 6832, 64, 512, 0, 0, 0, 0, \"outb3.odm\")\n"
        "    return\n"
        "end\n",
        "@SyntheticDirectMapMove.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    CHECK_FALSE(runtimeState.pendingDialogueContext.has_value());
    REQUIRE(runtimeState.pendingMapMove.has_value());
    CHECK_EQ(runtimeState.pendingMapMove->mapName, std::optional<std::string>("outb3.odm"));
    CHECK_EQ(runtimeState.pendingMapMove->x, 12808);
    CHECK_EQ(runtimeState.pendingMapMove->y, 6832);
    CHECK_EQ(runtimeState.pendingMapMove->z, 64);
}

TEST_CASE("lua MoveToMap current-map sentinel queues same-map teleport")
{
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
        "evt.map[1] = function()\n"
        "    evt._BeginEvent(1)\n"
        "    evt.MoveToMap(-3136, 2240, 224, 1024, 0, 0, 0, 0, \"0.\")\n"
        "    return\n"
        "end\n",
        "@SyntheticSameMapMove.lua",
        OpenYAMM::Game::ScriptedEventScope::Map);
    REQUIRE(scriptedProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(scriptedProgram, std::nullopt, 1, runtimeState, nullptr, nullptr));
    CHECK_FALSE(runtimeState.pendingDialogueContext.has_value());
    REQUIRE(runtimeState.pendingMapMove.has_value());
    CHECK_FALSE(runtimeState.pendingMapMove->mapName.has_value());
    CHECK_EQ(runtimeState.pendingMapMove->x, -3136);
    CHECK_EQ(runtimeState.pendingMapMove->y, 2240);
    CHECK_EQ(runtimeState.pendingMapMove->z, 224);
}

TEST_CASE("dungeon transition dialog uses trans table title text icon and transition video metadata")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingMapMove mapMove = {};
    mapMove.mapName = std::string("D18.blv");
    mapMove.x = -500;
    mapMove.y = -1567;
    mapMove.z = -63;

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    context.transitionMapMove = mapMove;
    context.transitionTextId = 363;
    context.transitionImageId = 9;
    runtimeState.pendingDialogueContext = context;

    const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
        runtimeState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        &gameData.transitionTable,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(dialog.isActive);
    CHECK_EQ(dialog.presentation, OpenYAMM::Game::EventDialogPresentation::Transition);
    CHECK_EQ(dialog.title, "Naga Vault");
    REQUIRE_FALSE(dialog.lines.empty());
    CHECK(dialog.lines.front().find("stonework") != std::string::npos);
    CHECK_EQ(dialog.participantTextureName, "IDOOR");
    CHECK_EQ(dialog.videoName, "naga_vlt");
    CHECK_EQ(dialog.videoDirectory, "Videos/Transitions");
    REQUIRE_EQ(dialog.actions.size(), 2u);
    CHECK_EQ(dialog.actions[0].kind, OpenYAMM::Game::EventDialogActionKind::MapTransitionConfirm);
    CHECK_EQ(dialog.actions[1].kind, OpenYAMM::Game::EventDialogActionKind::MapTransitionCancel);
}

TEST_CASE("merged dungeon transition dialog uses world house movie metadata before shared title fallback")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::EventRuntimeState mm6RuntimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingMapMove mm6MapMove = {};
    mm6MapMove.mapName = std::string("6d02.blv");

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext mm6Context = {};
    mm6Context.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    mm6Context.transitionMapMove = mm6MapMove;
    mm6Context.transitionTextId = 166;
    mm6Context.transitionImageId = 1;
    mm6RuntimeState.pendingDialogueContext = mm6Context;

    OpenYAMM::Game::MapStatsEntry newSorpigal = {};
    newSorpigal.id = 151;
    newSorpigal.name = "New Sorpigal";
    newSorpigal.fileName = "oute3.odm";
    OpenYAMM::Game::MapStatsEntry mm6AbandonedTemple = {};
    mm6AbandonedTemple.id = 153;
    mm6AbandonedTemple.name = "Abandoned Temple";
    mm6AbandonedTemple.fileName = "6d02.blv";
    const std::vector<OpenYAMM::Game::MapStatsEntry> mm6MapEntries = {newSorpigal, mm6AbandonedTemple};

    const OpenYAMM::Game::EventDialogContent mm6Dialog = OpenYAMM::Game::buildEventDialogContent(
        mm6RuntimeState,
        0,
        true,
        nullptr,
        &gameData.houseTable,
        nullptr,
        nullptr,
        &gameData.transitionTable,
        &newSorpigal,
        &mm6MapEntries,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(mm6Dialog.isActive);
    CHECK_EQ(mm6Dialog.title, "Abandoned Temple");
    CHECK_EQ(mm6Dialog.videoName, "d02");
    CHECK_EQ(mm6Dialog.videoDirectory, "Videos/Transitions");

    OpenYAMM::Game::EventRuntimeState mm6ExitRuntimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingMapMove mm6ExitMapMove = {};
    mm6ExitMapMove.mapName = std::string("oute3.odm");

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext mm6ExitContext = {};
    mm6ExitContext.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    mm6ExitContext.transitionMapMove = mm6ExitMapMove;
    mm6ExitContext.transitionImageId = 1;
    mm6ExitRuntimeState.pendingDialogueContext = mm6ExitContext;

    const OpenYAMM::Game::EventDialogContent mm6ExitDialog = OpenYAMM::Game::buildEventDialogContent(
        mm6ExitRuntimeState,
        0,
        true,
        nullptr,
        &gameData.houseTable,
        nullptr,
        nullptr,
        &gameData.transitionTable,
        &mm6AbandonedTemple,
        &mm6MapEntries,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(mm6ExitDialog.isActive);
    CHECK_EQ(mm6ExitDialog.title, "Abandoned Temple");
    CHECK(mm6ExitDialog.videoName.empty());
    CHECK(mm6ExitDialog.videoDirectory.empty());

    OpenYAMM::Game::EventRuntimeState mm7RuntimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingMapMove mm7MapMove = {};
    mm7MapMove.mapName = std::string("7d06.blv");

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext mm7Context = {};
    mm7Context.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    mm7Context.transitionMapMove = mm7MapMove;
    mm7Context.transitionTextId = 131;
    mm7Context.transitionImageId = 1;
    mm7RuntimeState.pendingDialogueContext = mm7Context;

    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.id = 62;
    emeraldIsland.name = "Emerald Island";
    emeraldIsland.fileName = "7out01.odm";
    OpenYAMM::Game::MapStatsEntry mm7TempleOfTheMoon = {};
    mm7TempleOfTheMoon.id = 80;
    mm7TempleOfTheMoon.name = "The Temple of the Moon";
    mm7TempleOfTheMoon.fileName = "7d06.blv";
    const std::vector<OpenYAMM::Game::MapStatsEntry> mm7MapEntries = {emeraldIsland, mm7TempleOfTheMoon};

    const OpenYAMM::Game::EventDialogContent mm7Dialog = OpenYAMM::Game::buildEventDialogContent(
        mm7RuntimeState,
        0,
        true,
        nullptr,
        &gameData.houseTable,
        nullptr,
        nullptr,
        &gameData.transitionTable,
        &emeraldIsland,
        &mm7MapEntries,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(mm7Dialog.isActive);
    CHECK_EQ(mm7Dialog.title, "The Temple of the Moon");
    CHECK_EQ(mm7Dialog.videoName, "out01 temple of the moon");
    CHECK_EQ(mm7Dialog.videoDirectory, "Videos/Transitions");

    OpenYAMM::Game::EventRuntimeState mm7ExitRuntimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingMapMove mm7ExitMapMove = {};
    mm7ExitMapMove.mapName = std::string("7out01.odm");

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext mm7ExitContext = {};
    mm7ExitContext.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    mm7ExitContext.transitionMapMove = mm7ExitMapMove;
    mm7ExitContext.transitionImageId = 1;
    mm7ExitRuntimeState.pendingDialogueContext = mm7ExitContext;

    const OpenYAMM::Game::EventDialogContent mm7ExitDialog = OpenYAMM::Game::buildEventDialogContent(
        mm7ExitRuntimeState,
        0,
        true,
        nullptr,
        &gameData.houseTable,
        nullptr,
        nullptr,
        &gameData.transitionTable,
        &mm7TempleOfTheMoon,
        &mm7MapEntries,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(mm7ExitDialog.isActive);
    CHECK_EQ(mm7ExitDialog.title, "The Temple of the Moon");
    CHECK(mm7ExitDialog.videoName.empty());
    CHECK(mm7ExitDialog.videoDirectory.empty());
}

TEST_CASE("outdoor boundary transition dialog uses default outdoor map icon")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::MapStatsEntry originMap = {};
    originMap.name = "Ravenshore";
    originMap.fileName = "Out02.odm";
    OpenYAMM::Game::MapEdgeTransition eastTransition = {};
    eastTransition.destinationMapFileName = "Out06.odm";
    eastTransition.travelDays = 1;
    originMap.eastTransition = eastTransition;

    OpenYAMM::Game::MapStatsEntry destinationMap = {};
    destinationMap.name = "Garrote Gorge";
    destinationMap.fileName = "Out06.odm";
    const std::vector<OpenYAMM::Game::MapStatsEntry> mapEntries = {originMap, destinationMap};

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    context.sourceId = static_cast<uint32_t>(OpenYAMM::Game::MapBoundaryEdge::East);
    runtimeState.pendingDialogueContext = context;

    const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
        runtimeState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        &originMap,
        &mapEntries,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(dialog.isActive);
    CHECK_EQ(dialog.presentation, OpenYAMM::Game::EventDialogPresentation::Transition);
    CHECK_EQ(dialog.participantVisual, OpenYAMM::Game::EventDialogParticipantVisual::MapIcon);
    CHECK_EQ(dialog.title, "Garrote Gorge");
    CHECK_EQ(dialog.participantTextureName, "Outside");
}

TEST_CASE("dungeon to outdoor transition dialog keeps dungeon transition icon")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntimeState::PendingMapMove mapMove = {};
    mapMove.mapName = std::string("Out02.odm");

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    context.transitionMapMove = mapMove;
    runtimeState.pendingDialogueContext = context;

    OpenYAMM::Game::MapStatsEntry currentMap = {};
    currentMap.name = "Abandoned Temple";
    currentMap.fileName = "D18.blv";
    OpenYAMM::Game::MapStatsEntry destinationMap = {};
    destinationMap.name = "Ravenshore";
    destinationMap.fileName = "Out02.odm";
    const std::vector<OpenYAMM::Game::MapStatsEntry> mapEntries = {currentMap, destinationMap};

    const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
        runtimeState,
        0,
        true,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        &currentMap,
        &mapEntries,
        nullptr,
        nullptr,
        0.0f);

    REQUIRE(dialog.isActive);
    CHECK_EQ(dialog.presentation, OpenYAMM::Game::EventDialogPresentation::Transition);
    CHECK_EQ(dialog.title, "Abandoned Temple");
    CHECK_EQ(dialog.participantTextureName, "Ticon01");
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

TEST_CASE("lua map hint-only events shadow colliding global handlers")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        "evt.meta.map.hint = {[176] = \"Needful Things\"}\n"
        "evt.meta.map.summary = {[176] = \"Needful Things\"}\n",
        "@SyntheticLocalHintOnlyEvent.lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        error);
    REQUIRE_MESSAGE(localProgram.has_value(), error.c_str());
    REQUIRE(localProgram->isHintOnlyEvent(176));

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalProgram = loadSyntheticScriptedProgram(
        "evt.global[176] = function()\n"
        "    evt._BeginEvent(176)\n"
        "    evt.SimpleMessage(\"global\")\n"
        "    return\n"
        "end\n",
        "@SyntheticGlobalCollisionEvent.lua",
        OpenYAMM::Game::ScriptedEventScope::Global);
    REQUIRE(globalProgram.has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    CHECK(eventRuntime.executeEventById(localProgram, globalProgram, 176, runtimeState, nullptr, nullptr));
    CHECK(runtimeState.messages.empty());

    OpenYAMM::Game::EventRuntimeState localOnlyState = {};
    CHECK_FALSE(eventRuntime.executeEventById(
        std::nullopt,
        globalProgram,
        176,
        localOnlyState,
        nullptr,
        nullptr,
        std::nullopt,
        false));
    CHECK(localOnlyState.messages.empty());

    OpenYAMM::Game::EventRuntimeState explicitFallbackState = {};
    CHECK(eventRuntime.executeEventById(
        std::nullopt,
        globalProgram,
        176,
        explicitFallbackState,
        nullptr,
        nullptr,
        std::nullopt,
        true));
    REQUIRE_EQ(explicitFallbackState.messages.size(), 1u);
    CHECK_EQ(explicitFallbackState.messages.front(), "global");
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

TEST_CASE("outdoor bmodel collision geometry keeps invisible faces and uses authored planes")
{
    OpenYAMM::Game::OutdoorBModel bmodel = {};
    bmodel.vertices.push_back({0, 0, 0});
    bmodel.vertices.push_back({128, 0, 0});
    bmodel.vertices.push_back({128, 128, 0});
    bmodel.vertices.push_back({0, 128, 0});

    OpenYAMM::Game::OutdoorBModelFace face = {};
    face.attributes = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);
    face.vertexIndices = {0, 1, 2, 3};
    face.planeNormalX = 65536;
    face.planeNormalY = 0;
    face.planeNormalZ = 0;

    OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};
    REQUIRE(OpenYAMM::Game::buildOutdoorFaceGeometry(bmodel, 0, face, 0, geometry));
    CHECK(geometry.normal.x > 0.99f);
    CHECK(std::abs(geometry.normal.z) < 0.01f);

    face.attributes = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable);
    CHECK_FALSE(OpenYAMM::Game::buildOutdoorFaceGeometry(bmodel, 0, face, 0, geometry));
    CHECK(OpenYAMM::Game::buildOutdoorFaceGeometry(bmodel, 0, face, 0, geometry, true));
}

TEST_CASE("indoor support sampling includes mechanism floor faces omitted from sector floor lists")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {0, 0, 0},
        {512, 0, 0},
        {512, 1024, 0},
        {0, 1024, 0},
        {512, 0, 0},
        {1024, 0, 0},
        {1024, 1024, 0},
        {512, 1024, 0},
    };

    OpenYAMM::Game::IndoorFace staticFloor = {};
    staticFloor.vertexIndices = {0, 1, 2, 3};
    staticFloor.facetType = 3;
    staticFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace platformFloor = {};
    platformFloor.vertexIndices = {4, 5, 6, 7};
    platformFloor.facetType = 3;
    platformFloor.roomNumber = 1;

    mapData.faces = {staticFloor, platformFloor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = 0;
    sector.maxX = 1024;
    sector.minY = 0;
    sector.maxY = 1024;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    OpenYAMM::Game::MapDeltaDoor platform = {};
    platform.doorId = 71;
    platform.directionZ = 65536;
    platform.moveLength = 640;
    platform.openSpeed = 150;
    platform.closeSpeed = 150;
    platform.state = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Open);
    platform.vertexIds = {4, 5, 6, 7};
    platform.faceIds = {1};
    platform.xOffsets = {512, 1024, 1024, 512};
    platform.yOffsets = {0, 0, 1024, 1024};
    platform.zOffsets = {0, 0, 0, 0};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    mapDeltaData->doors.push_back(platform);
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState state =
        controller.initializeStateFromEyePosition(768.0f, 512.0f, 160.0f, body);

    CHECK(state.grounded);
    CHECK_EQ(state.supportFaceIndex, 1u);
    CHECK_EQ(state.footZ, doctest::Approx(0.0f));
}

TEST_CASE("indoor support sampling does not treat side-opening doors as carry platforms")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {0, 0, 0},
        {512, 0, 0},
        {512, 1024, 0},
        {0, 1024, 0},
        {512, 0, 0},
        {1024, 0, 0},
        {1024, 1024, 0},
        {512, 1024, 0},
    };

    OpenYAMM::Game::IndoorFace staticFloor = {};
    staticFloor.vertexIndices = {0, 1, 2, 3};
    staticFloor.facetType = 3;
    staticFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace sideDoorFloor = {};
    sideDoorFloor.vertexIndices = {4, 5, 6, 7};
    sideDoorFloor.facetType = 3;
    sideDoorFloor.roomNumber = 1;

    mapData.faces = {staticFloor, sideDoorFloor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = 0;
    sector.maxX = 1024;
    sector.minY = 0;
    sector.maxY = 1024;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    OpenYAMM::Game::MapDeltaDoor sideDoor = {};
    sideDoor.doorId = 72;
    sideDoor.directionX = 65536;
    sideDoor.moveLength = 640;
    sideDoor.openSpeed = 150;
    sideDoor.closeSpeed = 150;
    sideDoor.state = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Open);
    sideDoor.vertexIds = {4, 5, 6, 7};
    sideDoor.faceIds = {1};
    sideDoor.xOffsets = {512, 1024, 1024, 512};
    sideDoor.yOffsets = {0, 0, 1024, 1024};
    sideDoor.zOffsets = {0, 0, 0, 0};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    mapDeltaData->doors.push_back(sideDoor);
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState state =
        controller.initializeStateFromEyePosition(768.0f, 512.0f, 160.0f, body);

    CHECK_NE(state.supportFaceIndex, 1u);
}

TEST_CASE("indoor movement steps over floor lip equal to ground snap slack")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, 0, 0},
        {256, 0, 0},
        {256, 160, 0},
        {-256, 160, 0},
        {-256, 160, 8},
        {256, 160, 8},
        {256, 192, 8},
        {-256, 192, 8},
        {-256, 192, 0},
        {256, 192, 0},
        {256, 384, 0},
        {-256, 384, 0},
    };

    OpenYAMM::Game::IndoorFace sourceFloor = {};
    sourceFloor.vertexIndices = {0, 1, 2, 3};
    sourceFloor.facetType = 3;
    sourceFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace lipFloor = {};
    lipFloor.vertexIndices = {4, 5, 6, 7};
    lipFloor.facetType = 3;
    lipFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace targetFloor = {};
    targetFloor.vertexIndices = {8, 9, 10, 11};
    targetFloor.facetType = 3;
    targetFloor.roomNumber = 1;

    mapData.faces = {sourceFloor, lipFloor, targetFloor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 3;
    sector.faceCount = 3;
    sector.nonBspFaceCount = 3;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = 0;
    sector.maxY = 384;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0, 1, 2};
    sector.faceIds = {0, 1, 2};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 80.0f, body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.supportFaceIndex, 0u);

    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(initial, body, 0.0f, 240.0f, false, 1.0f);

    CHECK(moved.y > 224.0f);
    CHECK(moved.grounded);
    CHECK_EQ(moved.supportFaceIndex, 2u);
    CHECK_EQ(moved.footZ, doctest::Approx(0.0f));
}

TEST_CASE("indoor actor ledge guard blocks grounded non-flying drops")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, 0, 0},
        {256, 0, 0},
        {256, 128, 0},
        {-256, 128, 0},
        {-256, 128, -160},
        {256, 128, -160},
        {256, 512, -160},
        {-256, 512, -160},
    };

    OpenYAMM::Game::IndoorFace upperFloor = {};
    upperFloor.vertexIndices = {0, 1, 2, 3};
    upperFloor.facetType = 3;

    OpenYAMM::Game::IndoorFace lowerFloor = {};
    lowerFloor.vertexIndices = {4, 5, 6, 7};
    lowerFloor.facetType = 3;

    mapData.faces = {upperFloor, lowerFloor};

    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 2;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = 0;
    sector.maxY = 512;
    sector.minZ = -256;
    sector.maxZ = 256;
    sector.floorFaceIds = {0, 1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 64.0f, body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.supportFaceIndex, 0u);

    const OpenYAMM::Game::IndoorMoveState unguarded =
        controller.resolveMove(initial, body, 0.0f, 400.0f, false, 0.5f);

    CHECK_GT(unguarded.y, 128.0f);

    const OpenYAMM::Game::IndoorMoveState guarded =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            400.0f,
            false,
            0.5f,
            nullptr,
            std::nullopt,
            false,
            nullptr,
            false,
            false,
            420.0f,
            1.0f,
            false,
            true);

    CHECK_LT(guarded.y, 128.0f);
    CHECK(guarded.grounded);
    CHECK_EQ(guarded.supportFaceIndex, 0u);
    CHECK_EQ(guarded.footZ, doctest::Approx(0.0f));
}

TEST_CASE("indoor actor ledge guard blocks leading footprint drops")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, 0, 0},
        {256, 0, 0},
        {256, 256, 0},
        {-256, 256, 0},
        {-256, 256, -160},
        {256, 256, -160},
        {256, 512, -160},
        {-256, 512, -160},
    };

    OpenYAMM::Game::IndoorFace upperFloor = {};
    upperFloor.vertexIndices = {0, 1, 2, 3};
    upperFloor.facetType = 3;

    OpenYAMM::Game::IndoorFace lowerFloor = {};
    lowerFloor.vertexIndices = {4, 5, 6, 7};
    lowerFloor.facetType = 3;

    mapData.faces = {upperFloor, lowerFloor};

    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 2;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -256;
    sector.maxX = 256;
    sector.minY = 0;
    sector.maxY = 512;
    sector.minZ = -256;
    sector.maxZ = 256;
    sector.floorFaceIds = {0, 1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 180.0f, body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.supportFaceIndex, 0u);

    const OpenYAMM::Game::IndoorMoveState unguarded =
        controller.resolveMove(initial, body, 0.0f, 100.0f, false, 0.5f);

    CHECK_GT(unguarded.y + body.radius, 256.0f);

    const OpenYAMM::Game::IndoorMoveState guarded =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            100.0f,
            false,
            0.5f,
            nullptr,
            std::nullopt,
            false,
            nullptr,
            false,
            false,
            420.0f,
            1.0f,
            false,
            true);

    CHECK_LT(guarded.y + body.radius, unguarded.y + body.radius - 8.0f);
    CHECK(guarded.grounded);
    CHECK_EQ(guarded.supportFaceIndex, 0u);
    CHECK_EQ(guarded.footZ, doctest::Approx(0.0f));
}

TEST_CASE("indoor movement does not collide with current sloped support floor")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {9064, 4250, 112},
        {9064, 3994, 112},
        {10088, 3994, 240},
        {10088, 4250, 240},
        {11496, 3994, 240},
        {11496, 4250, 240},
        {10088, 4250, 496},
        {10088, 3994, 496},
    };

    OpenYAMM::Game::IndoorFace ramp = {};
    ramp.vertexIndices = {0, 1, 2, 3};
    ramp.facetType = 4;
    ramp.roomNumber = 19;

    OpenYAMM::Game::IndoorFace flatFloor = {};
    flatFloor.vertexIndices = {3, 2, 4, 5};
    flatFloor.facetType = 3;
    flatFloor.roomNumber = 20;

    OpenYAMM::Game::IndoorFace portal = {};
    portal.vertexIndices = {3, 6, 7, 2};
    portal.facetType = 1;
    portal.roomNumber = 20;
    portal.roomBehindNumber = 19;
    portal.attributes = OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::IsPortal);
    portal.isPortal = true;

    mapData.faces = {ramp, flatFloor, portal};

    mapData.sectors.resize(21);
    OpenYAMM::Game::IndoorSector &rampSector = mapData.sectors[19];
    rampSector.floorCount = 1;
    rampSector.portalCount = 1;
    rampSector.faceCount = 2;
    rampSector.nonBspFaceCount = 2;
    rampSector.minX = 9064;
    rampSector.maxX = 10088;
    rampSector.minY = 3994;
    rampSector.maxY = 4250;
    rampSector.minZ = 112;
    rampSector.maxZ = 496;
    rampSector.floorFaceIds = {0};
    rampSector.portalFaceIds = {2};
    rampSector.faceIds = {0, 2};
    rampSector.nonBspFaceIds = rampSector.faceIds;

    OpenYAMM::Game::IndoorSector &flatSector = mapData.sectors[20];
    flatSector.floorCount = 1;
    flatSector.portalCount = 1;
    flatSector.faceCount = 2;
    flatSector.nonBspFaceCount = 2;
    flatSector.minX = 10088;
    flatSector.maxX = 11496;
    flatSector.minY = 3994;
    flatSector.maxY = 4250;
    flatSector.minZ = 240;
    flatSector.maxZ = 496;
    flatSector.floorFaceIds = {1};
    flatSector.portalFaceIds = {2};
    flatSector.faceIds = {1, 2};
    flatSector.nonBspFaceIds = flatSector.faceIds;

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const float startX = 10078.9f;
    const float startY = 4126.26f;
    const float startFootZ = 238.862f;
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(startX, startY, startFootZ + body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.supportFaceIndex, 0u);
    CHECK_EQ(initial.footZ, doctest::Approx(startFootZ).epsilon(0.001));

    OpenYAMM::Game::IndoorMoveDebugInfo debugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            -767.635f,
            -23.677f,
            false,
            1.0f / 64.0f,
            nullptr,
            std::nullopt,
            true,
            &debugInfo);

    CHECK(moved.x < initial.x - 1.0f);
    CHECK(moved.grounded);
    CHECK_EQ(moved.supportFaceIndex, 0u);
    CHECK(debugInfo.hitFaceIndex != 0u);
}

TEST_CASE("indoor airborne movement does not endpoint-collide with steep floor-like wall facets")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -72, -45},
        {128, -72, -45},
        {128, 0, 0},
        {-128, 0, 0},
        {-128, 0, 0},
        {128, 0, 0},
        {128, 48, 96},
        {-128, 48, 96},
    };

    OpenYAMM::Game::IndoorFace lowerSlope = {};
    lowerSlope.vertexIndices = {0, 1, 2, 3};
    lowerSlope.facetType = 4;
    lowerSlope.roomNumber = 1;

    OpenYAMM::Game::IndoorFace steepBoatSlope = {};
    steepBoatSlope.vertexIndices = {4, 5, 6, 7};
    steepBoatSlope.facetType = 4;
    steepBoatSlope.roomNumber = 1;

    mapData.faces = {lowerSlope, steepBoatSlope};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.wallCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -128;
    sector.maxX = 128;
    sector.minY = -72;
    sector.maxY = 48;
    sector.minZ = -64;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.wallFaceIds = {1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};

    OpenYAMM::Game::IndoorMoveState initial = {};
    initial.x = 0.0f;
    initial.y = -11.65f;
    initial.footZ = 22.4f;
    initial.eyeHeight = body.height;
    initial.verticalVelocity = -9000.0f;
    initial.sectorId = 1;
    initial.eyeSectorId = 1;
    initial.supportFaceIndex = static_cast<size_t>(-1);
    initial.grounded = false;

    OpenYAMM::Game::IndoorMoveDebugInfo debugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            768.0f,
            false,
            1.0f / 128.0f,
            nullptr,
            std::nullopt,
            false,
            &debugInfo);

    CHECK(moved.y > initial.y + 1.0f);
    CHECK(moved.footZ < initial.footZ);
    CHECK_NE(debugInfo.hitFaceIndex, 1u);
}

TEST_CASE("indoor flying actor horizontal pass does not inherit uphill sloped face vertical response")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -72, -45},
        {128, -72, -45},
        {128, 0, 0},
        {-128, 0, 0},
        {-128, 0, 0},
        {128, 0, 0},
        {128, 48, 96},
        {-128, 48, 96},
    };

    OpenYAMM::Game::IndoorFace lowerSlope = {};
    lowerSlope.vertexIndices = {0, 1, 2, 3};
    lowerSlope.facetType = 4;
    lowerSlope.roomNumber = 1;

    OpenYAMM::Game::IndoorFace steepBoatSlope = {};
    steepBoatSlope.vertexIndices = {4, 5, 6, 7};
    steepBoatSlope.facetType = 4;
    steepBoatSlope.roomNumber = 1;

    mapData.faces = {lowerSlope, steepBoatSlope};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.wallCount = 1;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -128;
    sector.maxX = 128;
    sector.minY = -72;
    sector.maxY = 48;
    sector.minZ = -64;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.wallFaceIds = {1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};

    OpenYAMM::Game::IndoorMoveState initial = {};
    initial.x = 0.0f;
    initial.y = -11.65f;
    initial.footZ = 22.4f;
    initial.eyeHeight = body.height;
    initial.verticalVelocity = 120.0f;
    initial.sectorId = 1;
    initial.eyeSectorId = 1;
    initial.supportFaceIndex = static_cast<size_t>(-1);
    initial.grounded = false;

    OpenYAMM::Game::IndoorMoveDebugInfo horizontalDebugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            768.0f,
            false,
            1.0f / 128.0f,
            nullptr,
            std::nullopt,
            false,
            &horizontalDebugInfo,
            true,
            false,
            420.0f,
            1.0f,
            true);

    CHECK(moved.y > initial.y + 1.0f);
    CHECK_LE(moved.footZ, initial.footZ);
    CHECK_LE(horizontalDebugInfo.responseStep.z, 0.0f);
}

TEST_CASE("indoor movement keeps sector while walking onto steep floor-like wall facet")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, 0, 0},
        {128, 0, 0},
        {128, 128, 0},
        {-128, 128, 0},
        {-128, -16, 0},
        {128, -16, 0},
        {128, 0, 0},
        {-128, 0, 0},
        {-128, -64, -96},
        {128, -64, -96},
        {128, -16, 0},
        {-128, -16, 0},
    };

    OpenYAMM::Game::IndoorFace flatFloor = {};
    flatFloor.vertexIndices = {0, 1, 2, 3};
    flatFloor.facetType = 3;
    flatFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace narrowTread = {};
    narrowTread.vertexIndices = {4, 5, 6, 7};
    narrowTread.facetType = 3;
    narrowTread.roomNumber = 1;

    OpenYAMM::Game::IndoorFace steepRamp = {};
    steepRamp.vertexIndices = {8, 9, 10, 11};
    steepRamp.facetType = 4;
    steepRamp.roomNumber = 1;

    mapData.faces = {flatFloor, narrowTread, steepRamp};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 3;
    sector.faceCount = 3;
    sector.nonBspFaceCount = 3;
    sector.minX = -128;
    sector.maxX = 128;
    sector.minY = -64;
    sector.maxY = 128;
    sector.minZ = -128;
    sector.maxZ = 256;
    sector.floorFaceIds = {0, 1, 2};
    sector.faceIds = {0, 1, 2};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 8.0f, body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.supportFaceIndex, 0u);

    OpenYAMM::Game::IndoorMoveDebugInfo debugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            -128.0f,
            false,
            0.25f,
            nullptr,
            std::nullopt,
            false,
            &debugInfo);

    CHECK(moved.y < -20.0f);
    CHECK(moved.footZ <= initial.footZ);
    CHECK_EQ(moved.sectorId, 1);
    CHECK_EQ(moved.eyeSectorId, 1);
    CHECK_NE(debugInfo.primaryBlockKind, OpenYAMM::Game::IndoorMoveBlockKind::InvalidPosition);
}

TEST_CASE("indoor movement steps from steep floor-like wall facet onto footprint floor")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, 0, 0},
        {128, 0, 0},
        {128, 128, 0},
        {-128, 128, 0},
        {-128, -64, -96},
        {128, -64, -96},
        {128, -16, 0},
        {-128, -16, 0},
    };

    OpenYAMM::Game::IndoorFace flatFloor = {};
    flatFloor.vertexIndices = {0, 1, 2, 3};
    flatFloor.facetType = 3;
    flatFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace steepRamp = {};
    steepRamp.vertexIndices = {4, 5, 6, 7};
    steepRamp.facetType = 4;
    steepRamp.roomNumber = 1;

    mapData.faces = {flatFloor, steepRamp};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 2;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -128;
    sector.maxX = 128;
    sector.minY = -64;
    sector.maxY = 128;
    sector.minZ = -128;
    sector.maxZ = 256;
    sector.floorFaceIds = {0, 1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};

    OpenYAMM::Game::IndoorMoveState initial = {};
    initial.x = 0.0f;
    initial.y = -26.0f;
    initial.footZ = -20.0f;
    initial.eyeHeight = body.height;
    initial.sectorId = 1;
    initial.eyeSectorId = 1;
    initial.supportFaceIndex = 1;
    initial.grounded = true;

    OpenYAMM::Game::IndoorMoveDebugInfo debugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            768.0f,
            false,
            1.0f / 128.0f,
            nullptr,
            std::nullopt,
            false,
            &debugInfo);

    CHECK(moved.y > initial.y + 1.0f);
    CHECK_EQ(moved.supportFaceIndex, 0u);
    CHECK_EQ(moved.footZ, doctest::Approx(0.0f));
    CHECK_NE(debugInfo.primaryBlockKind, OpenYAMM::Game::IndoorMoveBlockKind::InvalidPosition);
}

TEST_CASE("indoor movement leaves flat edge using leading footprint floor")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, 0, 0},
        {128, 0, 0},
        {128, 128, 0},
        {-128, 128, 0},
        {-128, -16, -32},
        {128, -16, -32},
        {128, 0, 0},
        {-128, 0, 0},
    };

    OpenYAMM::Game::IndoorFace flatFloor = {};
    flatFloor.vertexIndices = {0, 1, 2, 3};
    flatFloor.facetType = 3;
    flatFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace steepRamp = {};
    steepRamp.vertexIndices = {4, 5, 6, 7};
    steepRamp.facetType = 4;
    steepRamp.roomNumber = 1;

    mapData.faces = {flatFloor, steepRamp};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 2;
    sector.faceCount = 2;
    sector.nonBspFaceCount = 2;
    sector.minX = -128;
    sector.maxX = 128;
    sector.minY = -16;
    sector.maxY = 128;
    sector.minZ = -64;
    sector.maxZ = 256;
    sector.floorFaceIds = {0, 1};
    sector.faceIds = {0, 1};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body{8.0f, 160.0f};
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 6.0f, body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.supportFaceIndex, 0u);

    OpenYAMM::Game::IndoorMoveDebugInfo debugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            0.0f,
            -128.0f,
            false,
            1.0f / 64.0f,
            nullptr,
            std::nullopt,
            false,
            &debugInfo);

    CHECK(moved.y < initial.y - 1.0f);
    CHECK_NE(debugInfo.primaryBlockKind, OpenYAMM::Game::IndoorMoveBlockKind::InvalidPosition);
}

TEST_CASE("indoor movement crosses d03 moat edge toward boat slope")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-9696, 2376, -1848},
        {-9312, 2376, -1848},
        {-9312, 2976, -1848},
        {-9696, 2976, -1848},
        {-9756, 2364, -1848},
        {-9168, 2364, -1848},
        {-9168, 2376, -1848},
        {-9756, 2376, -1848},
        {-9756, 2316, -1944},
        {-9180, 2316, -1944},
        {-9180, 2364, -1848},
        {-9756, 2364, -1848},
    };

    OpenYAMM::Game::IndoorFace moatFloor = {};
    moatFloor.vertexIndices = {0, 1, 2, 3};
    moatFloor.facetType = 3;
    moatFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace edgeFloor = {};
    edgeFloor.vertexIndices = {4, 5, 6, 7};
    edgeFloor.facetType = 3;
    edgeFloor.roomNumber = 1;

    OpenYAMM::Game::IndoorFace boatSlope = {};
    boatSlope.vertexIndices = {8, 9, 10, 11};
    boatSlope.facetType = 4;
    boatSlope.roomNumber = 1;

    mapData.faces = {moatFloor, edgeFloor, boatSlope};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 3;
    sector.faceCount = 3;
    sector.nonBspFaceCount = 3;
    sector.minX = -9800;
    sector.maxX = -9100;
    sector.minY = 2300;
    sector.maxY = 3000;
    sector.minZ = -2000;
    sector.maxZ = -1600;
    sector.floorFaceIds = {0, 1, 2};
    sector.faceIds = {0, 1, 2};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};

    OpenYAMM::Game::IndoorMoveState initial = {};
    initial.x = -9556.89f;
    initial.y = 2379.93f;
    initial.footZ = -1848.0f;
    initial.eyeHeight = body.height;
    initial.sectorId = 1;
    initial.eyeSectorId = 1;
    initial.supportFaceIndex = 0;
    initial.grounded = true;

    OpenYAMM::Game::IndoorMoveDebugInfo debugInfo = {};
    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            -3.22991f,
            -767.993f,
            false,
            1.0f / 64.0f,
            nullptr,
            std::nullopt,
            false,
            &debugInfo);

    CHECK(moved.y < initial.y - 1.0f);
    CHECK_NE(debugInfo.primaryBlockKind, OpenYAMM::Game::IndoorMoveBlockKind::InvalidPosition);
}

TEST_CASE("indoor movement rejects positions whose eye point leaves all sectors")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-256, -128, 0},
        {256, -128, 0},
        {256, 128, 0},
        {-256, 128, 0},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    mapData.faces = {floor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 1;
    sector.nonBspFaceCount = 1;
    sector.minX = -64;
    sector.maxX = 64;
    sector.minY = -128;
    sector.maxY = 128;
    sector.minZ = 0;
    sector.maxZ = 256;
    sector.floorFaceIds = {0};
    sector.faceIds = {0};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    const OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 0.0f, body.height, body);

    REQUIRE(initial.grounded);
    REQUIRE_EQ(initial.eyeSectorId, 1);

    const OpenYAMM::Game::IndoorMoveState moved =
        controller.resolveMove(
            initial,
            body,
            128.0f,
            0.0f,
            false,
            1.0f);

    CHECK_EQ(moved.x, doctest::Approx(initial.x));
    CHECK_EQ(moved.y, doctest::Approx(initial.y));
    CHECK(moved.grounded);
    CHECK_EQ(moved.supportFaceIndex, 0u);
}

TEST_CASE("indoor flying actor movement keeps horizontal progress when vertical movement is blocked")
{
    OpenYAMM::Game::IndoorMapData mapData = {};
    mapData.vertices = {
        {-128, -128, 0},
        {256, -128, 0},
        {256, 128, 0},
        {-128, 128, 0},
    };

    OpenYAMM::Game::IndoorFace floor = {};
    floor.vertexIndices = {0, 1, 2, 3};
    floor.facetType = 3;
    floor.roomNumber = 1;
    mapData.faces = {floor};

    OpenYAMM::Game::IndoorSector dummySector = {};
    OpenYAMM::Game::IndoorSector sector = {};
    sector.floorCount = 1;
    sector.faceCount = 1;
    sector.nonBspFaceCount = 1;
    sector.minX = -128;
    sector.maxX = 256;
    sector.minY = -128;
    sector.maxY = 128;
    sector.minZ = 0;
    sector.maxZ = 180;
    sector.floorFaceIds = {0};
    sector.faceIds = {0};
    sector.nonBspFaceIds = sector.faceIds;
    mapData.sectors = {dummySector, sector};

    std::optional<OpenYAMM::Game::MapDeltaData> mapDeltaData = OpenYAMM::Game::MapDeltaData{};
    std::optional<OpenYAMM::Game::EventRuntimeState> eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    OpenYAMM::Game::IndoorMovementController controller(mapData, &mapDeltaData, &eventRuntimeState);
    const OpenYAMM::Game::IndoorBodyDimensions body = {};
    OpenYAMM::Game::IndoorMoveState initial =
        controller.initializeStateFromEyePosition(0.0f, 0.0f, body.height, body);
    initial.verticalVelocity = 128.0f;

    REQUIRE_EQ(initial.eyeSectorId, 1);

    const OpenYAMM::Game::IndoorMoveState combinedMove =
        controller.resolveMove(
            initial,
            body,
            64.0f,
            0.0f,
            false,
            1.0f,
            nullptr,
            std::nullopt,
            false,
            nullptr,
            true);

    const OpenYAMM::Game::IndoorMoveState splitMove =
        controller.resolveFlyingActorMove(
            initial,
            body,
            64.0f,
            0.0f,
            1.0f);

    CHECK_EQ(combinedMove.x, doctest::Approx(initial.x));
    CHECK(splitMove.x > initial.x + 60.0f);
    CHECK_EQ(splitMove.footZ, doctest::Approx(initial.footZ));
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
    CHECK_EQ(
        OpenYAMM::Game::GameMechanics::resolveCharacterAttackSoundId(
            character,
            &itemTable,
            OpenYAMM::Game::CharacterAttackMode::DragonBreath),
        OpenYAMM::Game::SoundId::DragonBreath);
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

TEST_CASE("event reputation variable mutates runtime location reputation")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::Party party;
    const OpenYAMM::Game::EventRuntime::VariableRef reputationVariable =
        OpenYAMM::Game::EventRuntime::decodeVariable(
            static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::ReputationInCurrentLocation));

    const std::vector<size_t> targetMemberIndices = {};

    OpenYAMM::Game::EventRuntime::setVariableValue(
        runtimeState,
        reputationVariable,
        12,
        &party,
        targetMemberIndices);
    CHECK_EQ(runtimeState.currentLocationReputation, 12);
    CHECK_EQ(
        party.eventVariableValue(
            static_cast<uint16_t>(OpenYAMM::Game::EvtVariable::ReputationInCurrentLocation)),
        0);

    OpenYAMM::Game::EventRuntime::addVariableValue(
        runtimeState,
        reputationVariable,
        3,
        &party,
        targetMemberIndices);
    CHECK_EQ(runtimeState.currentLocationReputation, 15);

    OpenYAMM::Game::EventRuntime::subtractVariableValue(
        runtimeState,
        reputationVariable,
        20,
        &party,
        targetMemberIndices);
    CHECK_EQ(runtimeState.currentLocationReputation, -5);

    OpenYAMM::Game::EventRuntime::subtractVariableValue(
        runtimeState,
        reputationVariable,
        20000,
        &party,
        targetMemberIndices);
    CHECK_EQ(runtimeState.currentLocationReputation, OpenYAMM::Game::MinReputation);
}

TEST_CASE("effective reputation includes OE criminal follower penalty")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.hiredNpcFollowers.push_back({100, 45, 0});
    runtimeState.hiredNpcFollowers.push_back({101, 51, 0});
    runtimeState.hiredNpcFollowers.push_back({102, 36, 0});

    CHECK_EQ(OpenYAMM::Game::hiredNpcReputationPenalty(runtimeState), 10);
    CHECK_EQ(OpenYAMM::Game::effectivePartyReputation(-6, &runtimeState), 4);
    CHECK_EQ(OpenYAMM::Game::reputationLabel(-25), "Saintly");
    CHECK_EQ(OpenYAMM::Game::reputationLabel(25), "Notorious");
}

TEST_CASE("merchant pricing uses effective reputation")
{
    OpenYAMM::Game::Character merchant = {};
    merchant.skills["Merchant"] = {"Merchant", 4, OpenYAMM::Game::SkillMastery::Normal};

    CHECK_EQ(OpenYAMM::Game::PriceCalculator::playerMerchant(&merchant, 0), 11);
    CHECK_EQ(OpenYAMM::Game::PriceCalculator::playerMerchant(&merchant, 10), 1);
    CHECK_EQ(OpenYAMM::Game::PriceCalculator::playerMerchant(&merchant, -10), 21);
    CHECK_EQ(OpenYAMM::Game::PriceCalculator::applyMerchantDiscount(&merchant, 1000, 10), 990);
    CHECK_EQ(OpenYAMM::Game::PriceCalculator::applyMerchantDiscount(&merchant, 1000, -10), 790);

    OpenYAMM::Game::Character grandmaster = {};
    grandmaster.skills["Merchant"] = {"Merchant", 1, OpenYAMM::Game::SkillMastery::Grandmaster};
    CHECK_EQ(OpenYAMM::Game::PriceCalculator::playerMerchant(&grandmaster, 50), 100);
}

TEST_CASE("house identify and repair service prices match OE formulas")
{
    OpenYAMM::Game::InventoryItem cheapItem = {};
    cheapItem.objectDescriptionId = 1;

    OpenYAMM::Game::ItemDefinition cheapDefinition = {};
    cheapDefinition.itemId = 1;
    cheapDefinition.value = 10;

    OpenYAMM::Game::Character noMerchant = {};

    CHECK_EQ(
        OpenYAMM::Game::PriceCalculator::itemIdentificationPrice(
            &noMerchant,
            cheapItem,
            cheapDefinition,
            1.0f),
        50);

    OpenYAMM::Game::Character merchant = {};
    merchant.skills["Merchant"] = {"Merchant", 30, OpenYAMM::Game::SkillMastery::Master};

    CHECK_EQ(
        OpenYAMM::Game::PriceCalculator::itemIdentificationPrice(
            &merchant,
            cheapItem,
            cheapDefinition,
            2.0f),
        33);

    OpenYAMM::Game::InventoryItem expensiveItem = {};
    expensiveItem.objectDescriptionId = 2;

    OpenYAMM::Game::ItemDefinition expensiveDefinition = {};
    expensiveDefinition.itemId = 2;
    expensiveDefinition.value = 1000;

    CHECK_EQ(
        OpenYAMM::Game::PriceCalculator::itemIdentificationPrice(
            &noMerchant,
            expensiveItem,
            expensiveDefinition,
            1.0f),
        50);
    CHECK_EQ(
        OpenYAMM::Game::PriceCalculator::itemRepairPrice(
            &noMerchant,
            expensiveItem,
            expensiveDefinition,
            1.0f),
        200);
}

TEST_CASE("item inspect value preserves zero value items")
{
    OpenYAMM::Game::InventoryItem item = {};
    OpenYAMM::Game::ItemDefinition zeroValueDefinition = {};
    zeroValueDefinition.itemId = 600;
    zeroValueDefinition.value = 0;

    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::itemInspectValue(item, zeroValueDefinition, nullptr, nullptr),
        0);
    CHECK_EQ(
        OpenYAMM::Game::PriceCalculator::itemValue(item, zeroValueDefinition, nullptr, nullptr),
        1);

    OpenYAMM::Game::ItemDefinition missingValueDefinition = {};
    missingValueDefinition.itemId = 601;
    CHECK_EQ(
        OpenYAMM::Game::ItemEnchantRuntime::itemInspectValue(item, missingValueDefinition, nullptr, nullptr),
        0);
}

TEST_CASE("MMerge monster kill reputation applies peasant and guard deltas")
{
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.setCurrentLocationReputation(0);

    OpenYAMM::Game::MonsterTable::MonsterStatsEntry peasant = {};
    peasant.kindFlags = OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Peasant);

    const OpenYAMM::Game::MonsterKillReputationResult peasantResult =
        OpenYAMM::Game::applyMonsterKillReputationPenalty(worldRuntime, &peasant, 85);

    CHECK(peasantResult.applied);
    CHECK_EQ(peasantResult.reputationDelta, 1);
    CHECK_EQ(worldRuntime.currentLocationReputation(), 1);

    OpenYAMM::Game::MonsterTable::MonsterStatsEntry guard = {};
    const OpenYAMM::Game::MonsterKillReputationResult guardResult =
        OpenYAMM::Game::applyMonsterKillReputationPenalty(worldRuntime, &guard, 55);

    CHECK(guardResult.applied);
    CHECK_EQ(guardResult.reputationDelta, 2);
    CHECK_EQ(worldRuntime.currentLocationReputation(), 3);

    const OpenYAMM::Game::MonsterKillReputationResult peasantGuardResult =
        OpenYAMM::Game::applyMonsterKillReputationPenalty(worldRuntime, &peasant, 38);

    CHECK(peasantGuardResult.applied);
    CHECK_EQ(peasantGuardResult.reputationDelta, 3);
    CHECK_EQ(worldRuntime.currentLocationReputation(), 6);
}

TEST_CASE("MMerge civilian aggression links guards and peasants")
{
    OpenYAMM::Game::MonsterTable::MonsterStatsEntry peasant = {};
    peasant.kindFlags = OpenYAMM::Game::monsterKindFlag(OpenYAMM::Game::MonsterKind::Peasant);

    OpenYAMM::Game::MonsterTable::MonsterStatsEntry monster = {};

    CHECK(OpenYAMM::Game::actorSharesCivilianAggression(55, &monster, 85, &peasant));
    CHECK(OpenYAMM::Game::actorSharesCivilianAggression(85, &peasant, 55, &monster));
    CHECK(OpenYAMM::Game::actorSharesCivilianAggression(38, &monster, 85, &peasant));
    CHECK(OpenYAMM::Game::actorSharesCivilianAggression(12, &peasant, 85, &peasant));
    CHECK_FALSE(OpenYAMM::Game::actorSharesCivilianAggression(12, &monster, 85, &peasant));
    CHECK_FALSE(OpenYAMM::Game::actorSharesCivilianAggression(55, &monster, 12, &monster));
}

TEST_CASE("MMerge monster kill reputation ignores ordinary monsters")
{
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.setCurrentLocationReputation(12);

    OpenYAMM::Game::MonsterTable::MonsterStatsEntry monster = {};
    const OpenYAMM::Game::MonsterKillReputationResult result =
        OpenYAMM::Game::applyMonsterKillReputationPenalty(worldRuntime, &monster, 85);

    CHECK_FALSE(result.applied);
    CHECK_EQ(result.reputationDelta, 0);
    CHECK_EQ(worldRuntime.currentLocationReputation(), 12);
}
