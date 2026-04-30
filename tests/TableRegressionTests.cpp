#include "doctest/doctest.h"

#include "game/party/Party.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"

#include "tests/RegressionGameData.h"

#include <filesystem>
#include <fstream>
#include <sstream>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

bool runtimeItemIsIdentified(
    const OpenYAMM::Game::EquippedItemRuntimeState &runtimeState,
    uint32_t equippedItemId)
{
    return equippedItemId == 0 || runtimeState.identified;
}

bool characterHasAnyEquippedItem(const OpenYAMM::Game::Character &character)
{
    return character.equipment.mainHand != 0
        || character.equipment.offHand != 0
        || character.equipment.bow != 0
        || character.equipment.armor != 0
        || character.equipment.helm != 0
        || character.equipment.belt != 0
        || character.equipment.cloak != 0
        || character.equipment.gauntlets != 0
        || character.equipment.boots != 0
        || character.equipment.amulet != 0
        || character.equipment.ring1 != 0
        || character.equipment.ring2 != 0
        || character.equipment.ring3 != 0
        || character.equipment.ring4 != 0
        || character.equipment.ring5 != 0
        || character.equipment.ring6 != 0;
}

bool characterHasItem(const OpenYAMM::Game::Character &character, uint32_t itemId)
{
    if (itemId == 0)
    {
        return false;
    }

    for (const OpenYAMM::Game::InventoryItem &item : character.inventory)
    {
        if (item.objectDescriptionId == itemId)
        {
            return true;
        }
    }

    return character.equipment.mainHand == itemId
        || character.equipment.offHand == itemId
        || character.equipment.bow == itemId
        || character.equipment.armor == itemId
        || character.equipment.helm == itemId
        || character.equipment.belt == itemId
        || character.equipment.cloak == itemId
        || character.equipment.gauntlets == itemId
        || character.equipment.boots == itemId
        || character.equipment.amulet == itemId
        || character.equipment.ring1 == itemId
        || character.equipment.ring2 == itemId
        || character.equipment.ring3 == itemId
        || character.equipment.ring4 == itemId
        || character.equipment.ring5 == itemId
        || character.equipment.ring6 == itemId;
}

std::string readSourceTextFile(const std::filesystem::path &path)
{
    std::ifstream stream(path);
    REQUIRE(stream.is_open());

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return buffer.str();
}

OpenYAMM::Game::SpriteFrameTable loadCommonSpriteFrameTable()
{
    const std::string yamlText =
        readSourceTextFile(
            std::filesystem::path(OPENYAMM_SOURCE_DIR)
            / "assets_dev/Data/rendering/sprite_frame_data_common.yml");

    OpenYAMM::Game::SpriteFrameTable spriteFrameTable;
    std::string errorMessage;
    REQUIRE(spriteFrameTable.loadFromYaml(yamlText, errorMessage, false));

    return spriteFrameTable;
}

void checkFirstSpriteFrameTexture(
    const OpenYAMM::Game::SpriteFrameTable &spriteFrameTable,
    const std::string &spriteName,
    const std::string &expectedTextureName,
    const std::string &expectedAssetFileName)
{
    const std::optional<uint16_t> spriteFrameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);
    REQUIRE(spriteFrameIndex.has_value());

    const OpenYAMM::Game::SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(*spriteFrameIndex, 0);
    REQUIRE(pFrame != nullptr);

    const OpenYAMM::Game::ResolvedSpriteTexture texture = OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
    CHECK_EQ(texture.textureName, expectedTextureName);
    CHECK(std::filesystem::exists(
        std::filesystem::path(OPENYAMM_SOURCE_DIR)
        / "assets_dev/Data/sprites"
        / expectedAssetFileName));
}
}

TEST_CASE("house data magic guild types are explicit")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::HouseEntry *pElementalGuild = gameData.houseTable.get(139);
    const OpenYAMM::Game::HouseEntry *pLightGuild = gameData.houseTable.get(142);
    const OpenYAMM::Game::HouseEntry *pDarkGuild = gameData.houseTable.get(143);

    REQUIRE(pElementalGuild != nullptr);
    REQUIRE(pLightGuild != nullptr);
    REQUIRE(pDarkGuild != nullptr);

    CHECK_EQ(pElementalGuild->type, "Elemental Guild");
    CHECK_EQ(pLightGuild->type, "Light Guild");
    CHECK_EQ(pDarkGuild->type, "Dark Guild");
}

TEST_CASE("monster spell descriptors preserve skill mastery and level")
{
    OpenYAMM::Game::MonsterTable monsterTable;
    std::vector<std::string> row(37, "0");
    row[0] = "999";
    row[1] = "Test Caster";
    row[2] = "test caster";
    row[3] = "12";
    row[4] = "40";
    row[5] = "3";
    row[12] = "2";
    row[13] = "200";
    row[14] = "80";
    row[24] = "35";
    row[25] = "Lightning Bolt,M,7";
    row[26] = "45";
    row[27] = "Fireball,G,9";

    REQUIRE(monsterTable.loadStatsFromRows({row}));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(999);
    REQUIRE(pStats != nullptr);
    CHECK_EQ(pStats->spell1Name, "lightning bolt");
    CHECK_EQ(pStats->spell1SkillMastery, OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(pStats->spell1SkillLevel, 7u);
    CHECK_EQ(pStats->spell2Name, "fireball");
    CHECK_EQ(pStats->spell2SkillMastery, OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(pStats->spell2SkillLevel, 9u);
}

TEST_CASE("monster vampire family is hostile to the party by default")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    CHECK_FALSE(gameData.monsterTable.isHostileToParty(49));
    CHECK(gameData.monsterTable.isHostileToParty(52));
    CHECK(gameData.monsterTable.isHostileToParty(53));
    CHECK(gameData.monsterTable.isHostileToParty(54));
}

TEST_CASE("harm projectile sprite resolves to an existing billboard texture")
{
    const OpenYAMM::Game::SpriteFrameTable spriteFrameTable = loadCommonSpriteFrameTable();

    checkFirstSpriteFrameTexture(spriteFrameTable, "spell70", "spell70b10", "Spell70b10.bmp");
}

TEST_CASE("light bolt sprites resolve to existing billboard textures")
{
    const OpenYAMM::Game::SpriteFrameTable spriteFrameTable = loadCommonSpriteFrameTable();

    checkFirstSpriteFrameTexture(spriteFrameTable, "sp78b", "sp78b", "sp78b.bmp");
    checkFirstSpriteFrameTexture(spriteFrameTable, "sp78c", "sp78c", "sp78c.bmp");
}

TEST_CASE("roster join offer mapping samples")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    struct ExpectedRosterJoinOffer
    {
        uint32_t topicId = 0;
        uint32_t rosterId = 0;
        uint32_t inviteTextId = 0;
        uint32_t partyFullTextId = 0;
    };

    const std::array<ExpectedRosterJoinOffer, 9> expectedOffers = {{
        {602, 2, 202, 203},
        {604, 4, 206, 207},
        {606, 6, 210, 211},
        {611, 11, 220, 221},
        {627, 27, 252, 253},
        {630, 30, 258, 259},
        {632, 32, 262, 263},
        {634, 34, 266, 267},
        {635, 35, 268, 269},
    }};

    for (const ExpectedRosterJoinOffer &expectedOffer : expectedOffers)
    {
        const std::optional<OpenYAMM::Game::NpcDialogTable::RosterJoinOffer> actualOffer =
            gameData.npcDialogTable.getRosterJoinOfferForTopic(expectedOffer.topicId);

        REQUIRE(actualOffer.has_value());
        CHECK_EQ(actualOffer->rosterId, expectedOffer.rosterId);
        CHECK_EQ(actualOffer->inviteTextId, expectedOffer.inviteTextId);
        CHECK_EQ(actualOffer->partyFullTextId, expectedOffer.partyFullTextId);
    }

    CHECK_FALSE(gameData.npcDialogTable.getRosterJoinOfferForTopic(600).has_value());
    CHECK_FALSE(gameData.npcDialogTable.getRosterJoinOfferForTopic(650).has_value());
}

TEST_CASE("recruit roster member loads birth experience resistances and items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(3);
    const OpenYAMM::Game::RosterEntry *pBlazenRosterEntry = gameData.rosterTable.get(35);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(pBlazenRosterEntry != nullptr);
    CHECK_EQ(pRosterEntry->unlockQuestBitId, 403u);
    CHECK_EQ(pBlazenRosterEntry->unlockQuestBitId, 435u);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    REQUIRE(party.recruitRosterMember(*pRosterEntry));

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    CHECK_EQ(pMember->birthYear, pRosterEntry->birthYear);
    CHECK_EQ(pMember->experience, pRosterEntry->experience);
    CHECK_EQ(pMember->baseResistances.fire, pRosterEntry->baseResistances.fire);
    CHECK_EQ(pMember->baseResistances.body, pRosterEntry->baseResistances.body);
    CHECK((!pMember->inventory.empty() || characterHasAnyEquippedItem(*pMember)));

    for (const OpenYAMM::Game::InventoryItem &item : pMember->inventory)
    {
        CHECK(item.identified);
    }

    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.mainHand, pMember->equipment.mainHand));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.offHand, pMember->equipment.offHand));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.bow, pMember->equipment.bow));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.armor, pMember->equipment.armor));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.helm, pMember->equipment.helm));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.belt, pMember->equipment.belt));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.cloak, pMember->equipment.cloak));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.gauntlets, pMember->equipment.gauntlets));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.boots, pMember->equipment.boots));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.amulet, pMember->equipment.amulet));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring1, pMember->equipment.ring1));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring2, pMember->equipment.ring2));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring3, pMember->equipment.ring3));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring4, pMember->equipment.ring4));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring5, pMember->equipment.ring5));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring6, pMember->equipment.ring6));

    for (uint32_t itemId : pRosterEntry->startingInventoryItemIds)
    {
        CHECK(characterHasItem(*pMember, itemId));
    }

    REQUIRE_FALSE(pBlazenRosterEntry->startingItems.empty());
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].rawValue, 5005u);
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].itemId, 5u);
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].enchantmentLevel, 5u);

    OpenYAMM::Game::Party blazenParty = {};
    blazenParty.setItemTable(&gameData.itemTable);
    blazenParty.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    REQUIRE(blazenParty.recruitRosterMember(*pBlazenRosterEntry));

    const OpenYAMM::Game::Character *pBlazen = blazenParty.member(0);
    REQUIRE(pBlazen != nullptr);
    CHECK(characterHasAnyEquippedItem(*pBlazen));

    for (uint32_t itemId : pBlazenRosterEntry->startingInventoryItemIds)
    {
        CHECK(characterHasItem(*pBlazen, itemId));
    }
}
