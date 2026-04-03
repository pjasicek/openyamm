#include "game/arcomage/ArcomageRules.h"

#include <algorithm>
#include <array>
#include <numeric>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
void appendShownCard(const ArcomagePlayedCard &card, ArcomageState &state)
{
    for (std::optional<ArcomagePlayedCard> &shownCard : state.shownCards)
    {
        if (!shownCard.has_value())
        {
            shownCard = card;
            return;
        }
    }

    for (size_t index = 1; index < state.shownCards.size(); ++index)
    {
        state.shownCards[index - 1] = state.shownCards[index];
    }

    state.shownCards.back() = card;
}

void clearShownCards(ArcomageState &state)
{
    for (std::optional<ArcomagePlayedCard> &shownCard : state.shownCards)
    {
        shownCard.reset();
    }
}

void applyMm8SpecialCard(const ArcomageCardDefinition &card, ArcomagePlayerState &player, ArcomagePlayerState &enemy)
{
    if (card.name == "Flood Water")
    {
        if (player.wall < enemy.wall)
        {
            player.dungeon = std::max(0, player.dungeon - 1);
            player.tower = std::max(0, player.tower - 2);
        }
        else if (player.wall > enemy.wall)
        {
            enemy.dungeon = std::max(0, enemy.dungeon - 1);
            enemy.tower = std::max(0, enemy.tower - 2);
        }
        else
        {
            player.dungeon = std::max(0, player.dungeon - 1);
            player.tower = std::max(0, player.tower - 2);
            enemy.dungeon = std::max(0, enemy.dungeon - 1);
            enemy.tower = std::max(0, enemy.tower - 2);
        }
    }
    else if (card.name == "Shift")
    {
        const int wall = player.wall;
        player.wall = enemy.wall;
        enemy.wall = wall;
    }
}
}

bool ArcomageRules::initializeMatch(
    const ArcomageLibrary &library,
    uint32_t houseId,
    const std::string &playerName,
    const std::string &opponentName,
    uint32_t randomSeed,
    ArcomageState &state
) const
{
    const ArcomageTavernRule *pRule = library.ruleForHouse(houseId);

    if (pRule == nullptr)
    {
        return false;
    }

    state = {};
    state.houseId = houseId;
    state.randomSeed = randomSeed != 0 ? randomSeed : 1u;
    state.winTower = pRule->winTower;
    state.winResources = pRule->winResources;
    state.aiMastery = pRule->aiMastery;
    state.players[0].name = playerName;
    state.players[1].name = opponentName;

    for (ArcomagePlayerState &player : state.players)
    {
        player.tower = pRule->startTower;
        player.wall = pRule->startWall;
        player.quarry = pRule->startQuarry;
        player.magic = pRule->startMagic;
        player.dungeon = pRule->startDungeon;
        player.bricks = pRule->startBricks;
        player.gems = pRule->startGems;
        player.recruits = pRule->startRecruits;
    }

    refillAndShuffleDeck(state);
    state.currentPlayerIndex = 0;
    state.needsTurnStart = false;

    for (size_t playerIndex = 0; playerIndex < state.players.size(); ++playerIndex)
    {
        while (handCount(state.players[playerIndex]) < ArcomageState::MinimumHandSize)
        {
            if (!drawCard(library, playerIndex, state))
            {
                return false;
            }
        }
    }

    return true;
}

bool ArcomageRules::canPlayCard(
    const ArcomageLibrary &library,
    const ArcomageState &state,
    size_t playerIndex,
    size_t handIndex
) const
{
    if (playerIndex >= state.players.size() || handIndex >= state.players[playerIndex].hand.size())
    {
        return false;
    }

    const int cardId = state.players[playerIndex].hand[handIndex];

    if (cardId < 0)
    {
        return false;
    }

    const ArcomageCardDefinition *pCard = library.cardById(static_cast<uint32_t>(cardId));

    if (pCard == nullptr)
    {
        return false;
    }

    const ArcomagePlayerState &player = state.players[playerIndex];
    return pCard->needQuarry <= player.quarry
        && pCard->needMagic <= player.magic
        && pCard->needDungeon <= player.dungeon
        && pCard->needBricks <= player.bricks
        && pCard->needGems <= player.gems
        && pCard->needRecruits <= player.recruits;
}

bool ArcomageRules::canDiscardCard(
    const ArcomageLibrary &library,
    const ArcomageState &state,
    size_t playerIndex,
    size_t handIndex
) const
{
    if (playerIndex >= state.players.size() || handIndex >= state.players[playerIndex].hand.size())
    {
        return false;
    }

    const int cardId = state.players[playerIndex].hand[handIndex];

    if (cardId < 0)
    {
        return false;
    }

    const ArcomageCardDefinition *pCard = library.cardById(static_cast<uint32_t>(cardId));
    return pCard != nullptr && pCard->discardable;
}

bool ArcomageRules::startTurn(const ArcomageLibrary &library, ArcomageState &state) const
{
    if (state.result.finished || !state.needsTurnStart)
    {
        return !state.result.finished;
    }

    clearShownCards(state);
    ArcomagePlayerState &player = state.players[state.currentPlayerIndex];
    player.bricks += player.quarry;
    player.gems += player.magic;
    player.recruits += player.dungeon;

    while (handCount(player) < ArcomageState::MinimumHandSize)
    {
        if (!drawCard(library, state.currentPlayerIndex, state))
        {
            return false;
        }
    }

    state.mustDiscard = handCount(player) > ArcomageState::MinimumHandSize;
    state.continueTurnAfterDiscard = false;
    state.needsTurnStart = false;
    state.result = resolveResult(state);
    return true;
}

bool ArcomageRules::playCard(const ArcomageLibrary &library, size_t handIndex, ArcomageState &state) const
{
    if (state.result.finished)
    {
        return false;
    }

    startTurn(library, state);

    const size_t playerIndex = state.currentPlayerIndex;

    if (!canPlayCard(library, state, playerIndex, handIndex))
    {
        return false;
    }

    ArcomagePlayerState &player = state.players[playerIndex];
    ArcomagePlayerState &enemy = state.players[(playerIndex + 1) % state.players.size()];
    const uint32_t cardId = static_cast<uint32_t>(player.hand[handIndex]);
    const ArcomageCardDefinition *pCard = library.cardById(cardId);

    if (pCard == nullptr)
    {
        return false;
    }

    consumeCardCost(*pCard, player);
    const bool usePrimary = evaluateCondition(pCard->condition, player, enemy);
    const ArcomageEffectBundle &bundle = usePrimary ? pCard->primary : pCard->secondary;
    player.hand[handIndex] = -1;
    applyEffectBundle(bundle, player, enemy);
    applyMm8SpecialCard(*pCard, player, enemy);
    state.lastPlayedCard = ArcomagePlayedCard{cardId, playerIndex, false};
    appendShownCard(*state.lastPlayedCard, state);

    for (int drawIndex = 0; drawIndex < bundle.extraDraw; ++drawIndex)
    {
        drawCard(library, playerIndex, state);
    }

    if (bundle.playAgain && handCount(player) <= ArcomageState::MinimumHandSize)
    {
        if (!drawCard(library, playerIndex, state))
        {
            return false;
        }
    }

    state.mustDiscard = handCount(player) > ArcomageState::MinimumHandSize;
    state.continueTurnAfterDiscard = state.mustDiscard && bundle.playAgain;
    state.result = resolveResult(state);

    if (state.result.finished)
    {
        return true;
    }

    if (!state.mustDiscard)
    {
        state.currentPlayerIndex = bundle.playAgain ? playerIndex : (playerIndex + 1) % state.players.size();
        state.needsTurnStart = !bundle.playAgain;
        state.continueTurnAfterDiscard = false;
    }

    return true;
}

bool ArcomageRules::discardCard(const ArcomageLibrary &library, size_t handIndex, ArcomageState &state) const
{
    if (state.result.finished)
    {
        return false;
    }

    startTurn(library, state);

    const size_t playerIndex = state.currentPlayerIndex;

    if (!canDiscardCard(library, state, playerIndex, handIndex))
    {
        return false;
    }

    ArcomagePlayerState &player = state.players[playerIndex];
    const uint32_t cardId = static_cast<uint32_t>(player.hand[handIndex]);
    player.hand[handIndex] = -1;
    state.lastPlayedCard = ArcomagePlayedCard{cardId, playerIndex, true};
    appendShownCard(*state.lastPlayedCard, state);
    state.mustDiscard = handCount(player) > ArcomageState::MinimumHandSize;
    state.result = resolveResult(state);

    if (state.result.finished)
    {
        return true;
    }

    if (!state.mustDiscard)
    {
        if (state.continueTurnAfterDiscard)
        {
            state.currentPlayerIndex = playerIndex;
            state.needsTurnStart = false;
        }
        else
        {
            state.currentPlayerIndex = (playerIndex + 1) % state.players.size();
            state.needsTurnStart = true;
        }

        state.continueTurnAfterDiscard = false;
    }

    return true;
}

bool ArcomageRules::resign(size_t playerIndex, ArcomageState &state) const
{
    if (playerIndex >= state.players.size() || state.result.finished)
    {
        return false;
    }

    state.result.finished = true;
    state.result.winnerIndex = (playerIndex + 1) % state.players.size();
    state.result.victoryKind = ArcomageVictoryKind::Resigned;
    return true;
}

std::vector<uint32_t> ArcomageRules::buildMasterDeck()
{
    std::vector<uint32_t> masterDeck;
    masterDeck.reserve(ArcomageState::MasterDeckSize);
    for (int cardId = 0; cardId < ArcomageState::MasterDeckSize; ++cardId)
    {
        masterDeck.push_back(static_cast<uint32_t>(cardId));
    }

    return masterDeck;
}

int ArcomageRules::handCount(const ArcomagePlayerState &player)
{
    return static_cast<int>(std::count_if(player.hand.begin(), player.hand.end(), [](int cardId) { return cardId >= 0; }));
}

int ArcomageRules::firstEmptyHandSlot(const ArcomagePlayerState &player)
{
    for (size_t slotIndex = 0; slotIndex < player.hand.size(); ++slotIndex)
    {
        if (player.hand[slotIndex] < 0)
        {
            return static_cast<int>(slotIndex);
        }
    }

    return -1;
}

bool ArcomageRules::drawCard(const ArcomageLibrary &library, size_t playerIndex, ArcomageState &state)
{
    if (playerIndex >= state.players.size())
    {
        return false;
    }

    int slotIndex = firstEmptyHandSlot(state.players[playerIndex]);

    if (slotIndex < 0)
    {
        return false;
    }

    if (state.deckIndex >= state.drawDeck.size())
    {
        refillAndShuffleDeck(state);
    }

    if (state.deckIndex >= state.drawDeck.size())
    {
        return false;
    }

    const uint32_t cardId = state.drawDeck[state.deckIndex++];

    if (library.cardById(cardId) == nullptr)
    {
        return false;
    }

    state.players[playerIndex].hand[slotIndex] = static_cast<int>(cardId);
    return true;
}

void ArcomageRules::refillAndShuffleDeck(ArcomageState &state)
{
    state.drawDeck = buildMasterDeck();
    std::mt19937 generator(state.randomSeed++);
    std::shuffle(state.drawDeck.begin(), state.drawDeck.end(), generator);
    state.deckIndex = 0;
}

bool ArcomageRules::evaluateCondition(
    ArcomageCondition condition,
    const ArcomagePlayerState &player,
    const ArcomagePlayerState &enemy)
{
    switch (condition)
    {
        case ArcomageCondition::AlwaysSecondary:
            return false;

        case ArcomageCondition::AlwaysPrimary:
            return true;

        case ArcomageCondition::LesserQuarry:
            return player.quarry < enemy.quarry;

        case ArcomageCondition::LesserMagic:
            return player.magic < enemy.magic;

        case ArcomageCondition::LesserDungeon:
            return player.dungeon < enemy.dungeon;

        case ArcomageCondition::EqualQuarry:
            return player.quarry == enemy.quarry;

        case ArcomageCondition::EqualMagic:
            return player.magic == enemy.magic;

        case ArcomageCondition::EqualDungeon:
            return player.dungeon == enemy.dungeon;

        case ArcomageCondition::GreaterQuarry:
            return player.quarry > enemy.quarry;

        case ArcomageCondition::GreaterMagic:
            return player.magic > enemy.magic;

        case ArcomageCondition::GreaterDungeon:
            return player.dungeon > enemy.dungeon;

        case ArcomageCondition::NoWall:
            return player.wall <= 0;

        case ArcomageCondition::HaveWall:
            return player.wall > 0;

        case ArcomageCondition::EnemyHasNoWall:
            return enemy.wall <= 0;

        case ArcomageCondition::EnemyHasWall:
            return enemy.wall > 0;

        case ArcomageCondition::LesserWall:
            return player.wall < enemy.wall;

        case ArcomageCondition::LesserTower:
            return player.tower < enemy.tower;

        case ArcomageCondition::EqualWall:
            return player.wall == enemy.wall;

        case ArcomageCondition::EqualTower:
            return player.tower == enemy.tower;

        case ArcomageCondition::GreaterWall:
            return player.wall > enemy.wall;

        case ArcomageCondition::GreaterTower:
            return player.tower > enemy.tower;

        case ArcomageCondition::TowerGreaterThanEnemyWall:
            return player.tower > enemy.wall;
    }

    return true;
}

int ArcomageRules::applyScalarChange(int &target, int otherValue, int delta)
{
    const int previous = target;

    if (delta == 99)
    {
        target = std::max(0, otherValue);
    }
    else
    {
        target = std::max(0, target + delta);
    }

    return target - previous;
}

int ArcomageRules::applyBuildingDamage(ArcomagePlayerState &player, int delta)
{
    if (delta == 0)
    {
        return 0;
    }

    const int previousWall = player.wall;
    const int previousTower = player.tower;

    if (delta > 0)
    {
        player.wall = std::max(0, player.wall + delta);
    }
    else if (player.wall >= -delta)
    {
        player.wall += delta;
    }
    else
    {
        int remainingDamage = delta + player.wall;
        player.wall = 0;
        player.tower = std::max(0, player.tower + remainingDamage);
    }

    return (player.wall - previousWall) + (player.tower - previousTower);
}

void ArcomageRules::applyEffectBundle(
    const ArcomageEffectBundle &bundle,
    ArcomagePlayerState &player,
    ArcomagePlayerState &enemy)
{
    applyScalarChange(player.quarry, enemy.quarry, bundle.playerQuarry);
    applyScalarChange(player.magic, enemy.magic, bundle.playerMagic);
    applyScalarChange(player.dungeon, enemy.dungeon, bundle.playerDungeon);
    applyScalarChange(player.bricks, enemy.bricks, bundle.playerBricks);
    applyScalarChange(player.gems, enemy.gems, bundle.playerGems);
    applyScalarChange(player.recruits, enemy.recruits, bundle.playerRecruits);
    applyBuildingDamage(player, bundle.playerBuildings);
    applyScalarChange(player.wall, enemy.wall, bundle.playerWall);
    applyScalarChange(player.tower, enemy.tower, bundle.playerTower);

    applyScalarChange(enemy.quarry, player.quarry, bundle.enemyQuarry);
    applyScalarChange(enemy.magic, player.magic, bundle.enemyMagic);
    applyScalarChange(enemy.dungeon, player.dungeon, bundle.enemyDungeon);
    applyScalarChange(enemy.bricks, player.bricks, bundle.enemyBricks);
    applyScalarChange(enemy.gems, player.gems, bundle.enemyGems);
    applyScalarChange(enemy.recruits, player.recruits, bundle.enemyRecruits);
    applyBuildingDamage(enemy, bundle.enemyBuildings);
    applyScalarChange(enemy.wall, player.wall, bundle.enemyWall);
    applyScalarChange(enemy.tower, player.tower, bundle.enemyTower);

    applyScalarChange(player.quarry, enemy.quarry, bundle.bothQuarry);
    applyScalarChange(enemy.quarry, player.quarry, bundle.bothQuarry);
    applyScalarChange(player.magic, enemy.magic, bundle.bothMagic);
    applyScalarChange(enemy.magic, player.magic, bundle.bothMagic);
    applyScalarChange(player.dungeon, enemy.dungeon, bundle.bothDungeon);
    applyScalarChange(enemy.dungeon, player.dungeon, bundle.bothDungeon);
    applyScalarChange(player.bricks, enemy.bricks, bundle.bothBricks);
    applyScalarChange(enemy.bricks, player.bricks, bundle.bothBricks);
    applyScalarChange(player.gems, enemy.gems, bundle.bothGems);
    applyScalarChange(enemy.gems, player.gems, bundle.bothGems);
    applyScalarChange(player.recruits, enemy.recruits, bundle.bothRecruits);
    applyScalarChange(enemy.recruits, player.recruits, bundle.bothRecruits);
    applyBuildingDamage(player, bundle.bothBuildings);
    applyBuildingDamage(enemy, bundle.bothBuildings);
    applyScalarChange(player.wall, enemy.wall, bundle.bothWall);
    applyScalarChange(enemy.wall, player.wall, bundle.bothWall);
    applyScalarChange(player.tower, enemy.tower, bundle.bothTower);
    applyScalarChange(enemy.tower, player.tower, bundle.bothTower);
}

void ArcomageRules::consumeCardCost(const ArcomageCardDefinition &card, ArcomagePlayerState &player)
{
    player.bricks = std::max(0, player.bricks - card.needBricks);
    player.gems = std::max(0, player.gems - card.needGems);
    player.recruits = std::max(0, player.recruits - card.needRecruits);
}

ArcomageResult ArcomageRules::resolveResult(const ArcomageState &state)
{
    ArcomageResult result = {};
    const ArcomagePlayerState &player = state.players[0];
    const ArcomagePlayerState &enemy = state.players[1];

    if (player.tower < state.winTower && enemy.tower >= state.winTower)
    {
        result.finished = true;
        result.winnerIndex = 1;
        result.victoryKind = ArcomageVictoryKind::TowerBuilt;
        return result;
    }

    if (player.tower >= state.winTower && enemy.tower < state.winTower)
    {
        result.finished = true;
        result.winnerIndex = 0;
        result.victoryKind = ArcomageVictoryKind::TowerBuilt;
        return result;
    }

    if (player.tower >= state.winTower && enemy.tower >= state.winTower)
    {
        result.finished = true;
        result.victoryKind = player.tower == enemy.tower ? ArcomageVictoryKind::Draw : ArcomageVictoryKind::TowerBuilt;

        if (player.tower > enemy.tower)
        {
            result.winnerIndex = 0;
        }
        else if (enemy.tower > player.tower)
        {
            result.winnerIndex = 1;
        }

        return result;
    }

    if (player.tower <= 0 && enemy.tower > 0)
    {
        result.finished = true;
        result.winnerIndex = 1;
        result.victoryKind = ArcomageVictoryKind::TowerDestroyed;
        return result;
    }

    if (player.tower > 0 && enemy.tower <= 0)
    {
        result.finished = true;
        result.winnerIndex = 0;
        result.victoryKind = ArcomageVictoryKind::TowerDestroyed;
        return result;
    }

    if (player.tower <= 0 && enemy.tower <= 0)
    {
        result.finished = true;

        if (player.tower == enemy.tower && player.wall == enemy.wall)
        {
            const int playerResource = highestResource(player);
            const int enemyResource = highestResource(enemy);

            if (playerResource == enemyResource)
            {
                result.victoryKind = ArcomageVictoryKind::Draw;
            }
            else
            {
                result.winnerIndex = playerResource > enemyResource ? 0 : 1;
                result.victoryKind = ArcomageVictoryKind::TiebreakResource;
            }
        }
        else if (player.tower == enemy.tower)
        {
            result.winnerIndex = player.wall > enemy.wall ? 0 : 1;
            result.victoryKind = ArcomageVictoryKind::TowerDestroyed;
        }
        else
        {
            result.winnerIndex = player.tower > enemy.tower ? 0 : 1;
            result.victoryKind = ArcomageVictoryKind::TowerDestroyed;
        }

        return result;
    }

    const int playerResource = highestResource(player);
    const int enemyResource = highestResource(enemy);

    if (playerResource < state.winResources && enemyResource >= state.winResources)
    {
        result.finished = true;
        result.winnerIndex = 1;
        result.victoryKind = ArcomageVictoryKind::ResourceVictory;
        return result;
    }

    if (playerResource >= state.winResources && enemyResource < state.winResources)
    {
        result.finished = true;
        result.winnerIndex = 0;
        result.victoryKind = ArcomageVictoryKind::ResourceVictory;
        return result;
    }

    if (playerResource >= state.winResources && enemyResource >= state.winResources)
    {
        result.finished = true;
        result.victoryKind = playerResource == enemyResource ? ArcomageVictoryKind::Draw : ArcomageVictoryKind::ResourceVictory;

        if (playerResource > enemyResource)
        {
            result.winnerIndex = 0;
        }
        else if (enemyResource > playerResource)
        {
            result.winnerIndex = 1;
        }

        return result;
    }

    return result;
}

int ArcomageRules::highestResource(const ArcomagePlayerState &player)
{
    return std::max({player.bricks, player.gems, player.recruits});
}
}
