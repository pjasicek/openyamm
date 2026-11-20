#include "game/arcomage/ArcomageAi.h"

#include "game/arcomage/ArcomageRules.h"

#include <algorithm>
#include <array>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
// A field of 99 sets the value to the other side's (ArcomageRules::applyScalarChange); any other field is a delta.
int scalarChange(int value, int otherValue, int field)
{
    return field == 99 ? std::max(0, otherValue) - value : field;
}

// The score of one value: the own and shared fields count as the AI's change, the enemy field against it. The fields
// are read in the order ArcomageRules::applyEffectBundle applies them, so the enemy field sees the AI's new value.
int valueGain(int ownValue, int enemyValue, int ownField, int enemyField, int bothField)
{
    const int ownChange = scalarChange(ownValue, enemyValue, ownField);
    const int enemyChange = scalarChange(enemyValue, ownValue + ownChange, enemyField);
    const int sharedChange = scalarChange(ownValue + ownChange, enemyValue + enemyChange, bothField);
    return ownChange + sharedChange - enemyChange;
}
}

ArcomageAi::Action ArcomageAi::chooseAction(const ArcomageLibrary &library, const ArcomageState &state) const
{
    const size_t playerIndex = state.currentPlayerIndex;

    if (playerIndex >= state.players.size())
    {
        return {};
    }

    const ArcomagePlayerState &player = state.players[playerIndex];
    const ArcomagePlayerState &enemy = state.players[(playerIndex + 1) % state.players.size()];
    const int mastery = std::clamp(state.aiMastery, 0, 2);
    ArcomageRules rules;

    if (mastery == 0)
    {
        std::vector<size_t> playableSlots;
        std::vector<size_t> discardableSlots;

        for (size_t handIndex = 0; handIndex < player.hand.size(); ++handIndex)
        {
            if (rules.canPlayCard(library, state, playerIndex, handIndex))
            {
                playableSlots.push_back(handIndex);
            }

            if (rules.canDiscardCard(library, state, playerIndex, handIndex))
            {
                discardableSlots.push_back(handIndex);
            }
        }

        std::mt19937 generator(state.randomSeed + 17u);

        if (!state.mustDiscard && !playableSlots.empty())
        {
            std::uniform_int_distribution<size_t> distribution(0, playableSlots.size() - 1);
            return {ActionKind::PlayCard, playableSlots[distribution(generator)]};
        }

        if (!discardableSlots.empty())
        {
            std::uniform_int_distribution<size_t> distribution(0, discardableSlots.size() - 1);
            return {ActionKind::DiscardCard, discardableSlots[distribution(generator)]};
        }

        return {};
    }

    int bestPlayableScore = std::numeric_limits<int>::min();
    size_t bestPlayableIndex = 0;
    bool foundPlayable = false;

    int worstDiscardScore = std::numeric_limits<int>::max();
    size_t worstDiscardIndex = 0;
    bool foundDiscard = false;

    for (size_t handIndex = 0; handIndex < player.hand.size(); ++handIndex)
    {
        const int cardId = player.hand[handIndex];

        if (cardId < 0)
        {
            continue;
        }

        const ArcomageCardDefinition *pCard = library.cardById(static_cast<uint32_t>(cardId));

        if (pCard == nullptr)
        {
            continue;
        }

        const int score = calculateCardPower(*pCard, player, enemy, mastery - 1);

        if (rules.canPlayCard(library, state, playerIndex, handIndex) && score > bestPlayableScore)
        {
            bestPlayableScore = score;
            bestPlayableIndex = handIndex;
            foundPlayable = true;
        }

        if (rules.canDiscardCard(library, state, playerIndex, handIndex) && score < worstDiscardScore)
        {
            worstDiscardScore = score;
            worstDiscardIndex = handIndex;
            foundDiscard = true;
        }
    }

    if (!state.mustDiscard && foundPlayable && bestPlayableScore > 0)
    {
        return {ActionKind::PlayCard, bestPlayableIndex};
    }

    if (foundDiscard)
    {
        return {ActionKind::DiscardCard, worstDiscardIndex};
    }

    return {};
}

int ArcomageAi::calculateCardPower(
    const ArcomageCardDefinition &card,
    const ArcomagePlayerState &player,
    const ArcomagePlayerState &enemy,
    int mastery
)
{
    static const std::array<std::array<int, 2>, 9> MasteryCoeff = {{
        {{10, 5}},
        {{2, 1}},
        {{1, 10}},
        {{1, 3}},
        {{1, 7}},
        {{1, 5}},
        {{1, 40}},
        {{1, 40}},
        {{1, 2}},
    }};

    const ArcomageEffectBundle &bundle =
        ArcomageRules::evaluateCondition(card.condition, player, enemy) ? card.primary : card.secondary;
    const ArcomageRules::SpecialCardEffect special = ArcomageRules::specialCardEffect(card, player, enemy);
    const int masteryIndex = std::clamp(mastery, 0, 1);

    const int towerGain = valueGain(player.tower, enemy.tower, bundle.playerTower, bundle.enemyTower, bundle.bothTower)
        + special.playerTower - special.enemyTower;
    const int wallGain = valueGain(player.wall, enemy.wall, bundle.playerWall, bundle.enemyWall, bundle.bothWall)
        + special.playerWall - special.enemyWall;
    const int buildingsGain = bundle.playerBuildings + bundle.bothBuildings - bundle.enemyBuildings;
    const int quarryGain =
        valueGain(player.quarry, enemy.quarry, bundle.playerQuarry, bundle.enemyQuarry, bundle.bothQuarry);
    const int magicGain = valueGain(player.magic, enemy.magic, bundle.playerMagic, bundle.enemyMagic, bundle.bothMagic);
    const int dungeonGain =
        valueGain(player.dungeon, enemy.dungeon, bundle.playerDungeon, bundle.enemyDungeon, bundle.bothDungeon)
        + special.playerDungeon - special.enemyDungeon;
    const int bricksGain =
        valueGain(player.bricks, enemy.bricks, bundle.playerBricks, bundle.enemyBricks, bundle.bothBricks);
    const int gemsGain = valueGain(player.gems, enemy.gems, bundle.playerGems, bundle.enemyGems, bundle.bothGems);
    const int recruitsGain =
        valueGain(player.recruits, enemy.recruits, bundle.playerRecruits, bundle.enemyRecruits, bundle.bothRecruits);

    int score = 0;
    score += (player.tower >= 10 ? MasteryCoeff[0][masteryIndex] : 20) * towerGain;
    score += (player.wall >= 10 ? MasteryCoeff[1][masteryIndex] : 5) * wallGain;
    score += 7 * buildingsGain;
    score += 40 * (quarryGain + magicGain + dungeonGain);
    score += 2 * (bricksGain + gemsGain + recruitsGain);

    // A card whose selected effects change nothing only spends resources; discarding it is free.
    if (score == 0 && !bundle.playAgain && bundle.extraDraw <= 0)
    {
        return 0;
    }

    if (bundle.playAgain || bundle.extraDraw > 0)
    {
        score *= 10;
    }

    int spareResource = 0;

    switch (card.resourceType)
    {
        case ArcomageResourceType::Bricks:
            spareResource = player.bricks - card.needBricks;
            break;

        case ArcomageResourceType::Gems:
            spareResource = player.gems - card.needGems;
            break;

        case ArcomageResourceType::Recruits:
            spareResource = player.recruits - card.needRecruits;
            break;

        case ArcomageResourceType::None:
            break;
    }

    score += 5 * std::min(3, spareResource);

    const int enemyTowerChange = scalarChange(enemy.tower, player.tower, bundle.enemyTower) + special.enemyTower;
    const int buildingDamage = std::max(0, -bundle.enemyBuildings);
    const int towerDamageThroughWall = std::max(0, buildingDamage - enemy.wall);

    if (enemy.tower + std::min(0, enemyTowerChange) - towerDamageThroughWall <= 0)
    {
        score += 9999;
    }

    return score;
}
}
