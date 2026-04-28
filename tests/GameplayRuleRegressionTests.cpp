#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/AudioSystem.h"
#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayWorldItemInteraction.h"
#include "game/gameplay/SavePreviewImage.h"
#include "game/items/InventoryItemMixingRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <random>

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

TEST_CASE("outdoor terrain descriptors expose liquid flags for non-default tilesets")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(initializeTestAssetFileSystem(assetFileSystem));

    OpenYAMM::Game::OutdoorMapData ironsand = {};
    ironsand.fileName = "out04.odm";
    ironsand.masterTile = 1;
    ironsand.tileSetLookupIndices = {234, 198, 270, 414};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> ironsandDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, ironsand);
    REQUIRE(ironsandDescriptors.has_value());
    CHECK((*ironsandDescriptors)[126].textureName == "lavtyl");
    CHECK(((*ironsandDescriptors)[126].flags & OpenYAMM::Game::TerrainTileFlagWater) != 0);
    CHECK(((*ironsandDescriptors)[126].flags & OpenYAMM::Game::TerrainTileFlagBurn) != 0);

    OpenYAMM::Game::OutdoorMapData shadowspire = {};
    shadowspire.fileName = "out06.odm";
    shadowspire.masterTile = 2;
    shadowspire.tileSetLookupIndices = {162, 126, 198, 414};

    const std::optional<std::vector<OpenYAMM::Game::TerrainTileDescriptor>> shadowspireDescriptors =
        OpenYAMM::Game::loadTerrainTileDescriptors(assetFileSystem, shadowspire);
    REQUIRE(shadowspireDescriptors.has_value());
    CHECK((*shadowspireDescriptors)[162].textureName == "tartyl");
    CHECK(((*shadowspireDescriptors)[162].flags & OpenYAMM::Game::TerrainTileFlagWater) != 0);
    CHECK(((*shadowspireDescriptors)[162].flags & OpenYAMM::Game::TerrainTileFlagBurn) == 0);
    CHECK((*shadowspireDescriptors)[174].textureName == "trne");
    CHECK(((*shadowspireDescriptors)[174].flags & OpenYAMM::Game::TerrainTileFlagTransition) != 0);
}

TEST_CASE("outdoor terrain descriptor flags are applied to movement attributes")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(initializeTestAssetFileSystem(assetFileSystem));

    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.fileName = "out04.odm";
    mapData.masterTile = 1;
    mapData.tileSetLookupIndices = {234, 198, 270, 414};
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
            gameData.potionMixingTable);

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
            gameData.potionMixingTable);

    REQUIRE(result.handled);
    CHECK(result.success);
    CHECK(result.heldItemConsumed);
    CHECK_FALSE(result.heldItemReplacement.has_value());

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
            gameData.potionMixingTable);

    REQUIRE(result.handled);
    CHECK_FALSE(result.success);
    CHECK(result.heldItemConsumed);
    CHECK(result.targetItemRemoved);
    CHECK_EQ(result.failureDamageLevel, 3u);
    CHECK(pMember->inventoryItemAt(0, 0) == nullptr);
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
        "    evt.MoveToMap(-500, -1567, -63, 512, 0, 0, 204, 9, \"\1D18.blv\")\n"
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
    CHECK_EQ(runtimeState.pendingDialogueContext->transitionTextId, 204u);
    CHECK_EQ(runtimeState.pendingDialogueContext->transitionImageId, 9u);
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
    context.transitionTextId = 204;
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
