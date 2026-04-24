#include "doctest/doctest.h"

#include "game/party/Party.h"

#include "tests/RegressionGameData.h"

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

    const std::array<ExpectedRosterJoinOffer, 7> expectedOffers = {{
        {602, 2, 202, 203},
        {606, 6, 210, 211},
        {611, 11, 220, 221},
        {627, 27, 252, 253},
        {630, 30, 258, 259},
        {632, 32, 262, 263},
        {634, 34, 266, 267},
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

    REQUIRE(pRosterEntry != nullptr);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);

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
}
