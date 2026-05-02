#include "doctest/doctest.h"

#include "tests/ArcomageTestHarness.h"
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
}

TEST_CASE("arcomage selected card data matches expected values")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ArcomageLibrary &library = gameData.arcomageLibrary;

    const OpenYAMM::Game::ArcomageCardDefinition *pAmethyst = library.cardByName("Amethyst");
    REQUIRE(pAmethyst != nullptr);
    CHECK_EQ(pAmethyst->slot, 42);
    CHECK_EQ(pAmethyst->resourceType, OpenYAMM::Game::ArcomageResourceType::Gems);
    CHECK_EQ(pAmethyst->needGems, 2);
    CHECK_EQ(pAmethyst->primary.playerTower, 3);

    const OpenYAMM::Game::ArcomageCardDefinition *pDiscord = library.cardByName("Discord");
    REQUIRE(pDiscord != nullptr);
    CHECK_EQ(pDiscord->slot, 59);
    CHECK_EQ(pDiscord->primary.bothMagic, -1);
    CHECK_EQ(pDiscord->primary.bothTower, -7);

    const OpenYAMM::Game::ArcomageCardDefinition *pWerewolf = library.cardByName("Werewolf");
    REQUIRE(pWerewolf != nullptr);
    CHECK_EQ(pWerewolf->slot, 99);
    CHECK_EQ(pWerewolf->resourceType, OpenYAMM::Game::ArcomageResourceType::Recruits);
    CHECK_EQ(pWerewolf->needRecruits, 9);
    CHECK_EQ(pWerewolf->primary.enemyBuildings, -9);
}

TEST_CASE("arcomage library initializes a playable match")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ArcomageLibrary &library = gameData.arcomageLibrary;

    REQUIRE_EQ(library.cards.size(), OpenYAMM::Game::ArcomageLibrary::CardCount);

    const OpenYAMM::Game::ArcomageTavernRule *pRule = library.ruleForHouse(228);
    REQUIRE(pRule != nullptr);

    OpenYAMM::Game::ArcomageRules rules;
    OpenYAMM::Game::ArcomageState state = {};

    REQUIRE(rules.initializeMatch(library, pRule->houseId, "Ariel", "Innkeeper", 1, state));
    REQUIRE(rules.startTurn(library, state));

    OpenYAMM::Game::ArcomageAi ai;
    const OpenYAMM::Game::ArcomageAi::Action action = ai.chooseAction(library, state);

    REQUIRE_NE(action.kind, OpenYAMM::Game::ArcomageAi::ActionKind::None);

    const bool applied = action.kind == OpenYAMM::Game::ArcomageAi::ActionKind::PlayCard
        ? rules.playCard(library, action.handIndex, state)
        : rules.discardCard(library, action.handIndex, state);

    CHECK(applied);
}

TEST_CASE("arcomage player play amethyst applies expected effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::ArcomageTestHarness harness = {};

    REQUIRE(harness.initialize(gameData.arcomageLibrary, 228));

    const std::optional<uint32_t> amethystId = harness.cardIdByName("Amethyst");
    REQUIRE(amethystId.has_value());

    harness.clearHands();
    REQUIRE(harness.setHand(0, std::vector<uint32_t>{*amethystId}));
    harness.state.players[0].gems = 10;
    harness.state.players[0].tower = 15;

    REQUIRE(harness.playCardById(0, *amethystId));
    CHECK_EQ(harness.state.players[0].gems, 8);
    CHECK_EQ(harness.state.players[0].tower, 18);
    REQUIRE(harness.state.lastPlayedCard.has_value());
    CHECK_EQ(harness.state.lastPlayedCard->cardId, *amethystId);
    CHECK_EQ(harness.state.lastPlayedCard->playerIndex, 0);
    CHECK_FALSE(harness.state.lastPlayedCard->discarded);
    CHECK_EQ(OpenYAMM::Tests::arcomageShownCardCount(harness.state), 1);
    CHECK_EQ(harness.state.currentPlayerIndex, 1);
    CHECK(harness.state.needsTurnStart);
}

TEST_CASE("arcomage conditional card branches match expected effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    SUBCASE("primary branch")
    {
        OpenYAMM::Tests::ArcomageTestHarness harness = {};

        REQUIRE(harness.initialize(gameData.arcomageLibrary, 228));
        harness.clearHands();
        REQUIRE(harness.setHand(0, std::vector<uint32_t>{4u}));
        harness.state.players[0].bricks = 20;
        harness.state.players[0].quarry = 1;
        harness.state.players[1].quarry = 3;

        REQUIRE(harness.playCardById(0, 4));
        CHECK_EQ(harness.state.players[0].bricks, 16);
        CHECK_EQ(harness.state.players[0].quarry, 3);
    }

    SUBCASE("secondary branch")
    {
        OpenYAMM::Tests::ArcomageTestHarness harness = {};

        REQUIRE(harness.initialize(gameData.arcomageLibrary, 228));
        harness.clearHands();
        REQUIRE(harness.setHand(0, std::vector<uint32_t>{4u}));
        harness.state.players[0].bricks = 20;
        harness.state.players[0].quarry = 3;
        harness.state.players[1].quarry = 1;

        REQUIRE(harness.playCardById(0, 4));
        CHECK_EQ(harness.state.players[0].bricks, 16);
        CHECK_EQ(harness.state.players[0].quarry, 4);
    }
}

TEST_CASE("arcomage player discard marks card as discarded")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::ArcomageTestHarness harness = {};

    REQUIRE(harness.initialize(gameData.arcomageLibrary, 228));

    const std::optional<uint32_t> amethystId = harness.cardIdByName("Amethyst");
    REQUIRE(amethystId.has_value());

    harness.clearHands();
    REQUIRE(harness.setHand(0, std::vector<uint32_t>{*amethystId}));

    REQUIRE(harness.discardCardById(0, *amethystId));
    REQUIRE(harness.state.lastPlayedCard.has_value());
    CHECK_EQ(harness.state.lastPlayedCard->cardId, *amethystId);
    CHECK(harness.state.lastPlayedCard->discarded);
    CHECK_EQ(OpenYAMM::Tests::arcomageShownCardCount(harness.state), 1);
    REQUIRE(harness.state.shownCards[0].has_value());
    CHECK(harness.state.shownCards[0]->discarded);
}

TEST_CASE("arcomage ai turn can be simulated headlessly")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::ArcomageTestHarness harness = {};

    REQUIRE(harness.initialize(gameData.arcomageLibrary, 228));

    const std::optional<uint32_t> amethystId = harness.cardIdByName("Amethyst");
    REQUIRE(amethystId.has_value());

    harness.clearHands();
    REQUIRE(harness.setHand(1, std::vector<uint32_t>{*amethystId}));
    harness.state.currentPlayerIndex = 1;
    harness.state.needsTurnStart = false;
    harness.state.players[1].gems = 10;
    harness.state.players[1].tower = 12;

    const OpenYAMM::Game::ArcomageAi::Action action = harness.ai.chooseAction(gameData.arcomageLibrary, harness.state);
    REQUIRE_EQ(action.kind, OpenYAMM::Game::ArcomageAi::ActionKind::PlayCard);
    CHECK_EQ(action.handIndex, 0);

    REQUIRE(harness.applyAiAction(action));
    CHECK_EQ(harness.state.players[1].gems, 8);
    CHECK_EQ(harness.state.players[1].tower, 15);
    REQUIRE(harness.state.lastPlayedCard.has_value());
    CHECK_EQ(harness.state.lastPlayedCard->playerIndex, 1);
}

TEST_CASE("arcomage mm8 special cards apply expected effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ArcomageLibrary &library = gameData.arcomageLibrary;

    SUBCASE("flood water targets the lower wall side")
    {
        OpenYAMM::Tests::ArcomageTestHarness harness = {};
        REQUIRE(harness.initialize(library, 228));

        const std::optional<uint32_t> floodWaterId = harness.cardIdByName("Flood Water");
        REQUIRE(floodWaterId.has_value());

        harness.clearHands();
        REQUIRE(harness.setHand(0, std::vector<uint32_t>{*floodWaterId}));
        harness.state.players[0].bricks = 10;
        harness.state.players[0].wall = 4;
        harness.state.players[0].tower = 18;
        harness.state.players[0].dungeon = 3;
        harness.state.players[1].wall = 8;
        harness.state.players[1].tower = 20;
        harness.state.players[1].dungeon = 5;

        REQUIRE(harness.playCardById(0, *floodWaterId));
        CHECK_EQ(harness.state.players[0].dungeon, 2);
        CHECK_EQ(harness.state.players[0].tower, 16);
        CHECK_EQ(harness.state.players[1].dungeon, 5);
        CHECK_EQ(harness.state.players[1].tower, 20);
    }

    SUBCASE("shift swaps the two walls")
    {
        OpenYAMM::Tests::ArcomageTestHarness harness = {};
        REQUIRE(harness.initialize(library, 228));

        const std::optional<uint32_t> shiftId = harness.cardIdByName("Shift");
        REQUIRE(shiftId.has_value());

        harness.clearHands();
        REQUIRE(harness.setHand(0, std::vector<uint32_t>{*shiftId}));
        harness.state.players[0].bricks = 20;
        harness.state.players[0].wall = 5;
        harness.state.players[1].wall = 14;

        REQUIRE(harness.playCardById(0, *shiftId));
        CHECK_EQ(harness.state.players[0].wall, 14);
        CHECK_EQ(harness.state.players[1].wall, 5);
    }
}

TEST_CASE("arcomage play again refills hand like oe")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::ArcomageLibrary &library = gameData.arcomageLibrary;

    SUBCASE("plain play again card refills to five without discard")
    {
        OpenYAMM::Tests::ArcomageTestHarness harness = {};
        REQUIRE(harness.initialize(library, 228));

        const std::optional<uint32_t> luckyCacheId = harness.cardIdByName("Lucky Cache");
        REQUIRE(luckyCacheId.has_value());

        harness.clearHands();
        REQUIRE(harness.setHand(0, std::vector<uint32_t>{*luckyCacheId, 2u, 3u, 4u, 5u}));
        harness.state.players[0].bricks = 10;

        REQUIRE(harness.playCardById(0, *luckyCacheId));
        CHECK_EQ(
            OpenYAMM::Tests::arcomageHandCardCount(harness.state.players[0]),
            OpenYAMM::Game::ArcomageState::MinimumHandSize);
        CHECK_EQ(harness.state.currentPlayerIndex, 0);
        CHECK_FALSE(harness.state.needsTurnStart);
        CHECK_FALSE(harness.state.mustDiscard);
    }

    SUBCASE("extra draw play again card requires one discard but keeps the turn")
    {
        OpenYAMM::Tests::ArcomageTestHarness harness = {};
        REQUIRE(harness.initialize(library, 228));

        const std::optional<uint32_t> prismId = harness.cardIdByName("Prism");
        REQUIRE(prismId.has_value());

        harness.clearHands();
        REQUIRE(harness.setHand(0, std::vector<uint32_t>{*prismId, 2u, 3u, 4u, 5u}));
        harness.state.players[0].gems = 10;

        REQUIRE(harness.playCardById(0, *prismId));
        CHECK_EQ(
            OpenYAMM::Tests::arcomageHandCardCount(harness.state.players[0]),
            OpenYAMM::Game::ArcomageState::MinimumHandSize + 1);
        CHECK(harness.state.mustDiscard);
        CHECK_EQ(harness.state.currentPlayerIndex, 0);
        CHECK_FALSE(harness.state.needsTurnStart);

        REQUIRE(harness.discardCardById(0, 2u));
        CHECK_EQ(harness.state.currentPlayerIndex, 0);
        CHECK_FALSE(harness.state.needsTurnStart);
        CHECK_FALSE(harness.state.mustDiscard);
    }
}

TEST_CASE("arcomage turn change clears previous shown cards")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::ArcomageTestHarness harness = {};

    REQUIRE(harness.initialize(gameData.arcomageLibrary, 228));

    const std::optional<uint32_t> amethystId = harness.cardIdByName("Amethyst");
    REQUIRE(amethystId.has_value());

    harness.clearHands();
    REQUIRE(harness.setHand(0, std::vector<uint32_t>{*amethystId}));
    REQUIRE(harness.setHand(1, std::vector<uint32_t>{*amethystId}));
    harness.state.players[0].gems = 10;
    harness.state.players[1].gems = 10;

    REQUIRE(harness.playCardById(0, *amethystId));
    CHECK_EQ(OpenYAMM::Tests::arcomageShownCardCount(harness.state), 1);

    REQUIRE(harness.rules.startTurn(gameData.arcomageLibrary, harness.state));
    CHECK_EQ(OpenYAMM::Tests::arcomageShownCardCount(harness.state), 0);

    REQUIRE(harness.playCardById(1, *amethystId));
    CHECK_EQ(OpenYAMM::Tests::arcomageShownCardCount(harness.state), 1);
}
