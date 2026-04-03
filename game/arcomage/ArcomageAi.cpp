#include "game/arcomage/ArcomageAi.h"

#include "game/arcomage/ArcomageRules.h"

#include <algorithm>
#include <array>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
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

    const ArcomageEffectBundle &bundle = card.primary;
    const int masteryIndex = std::clamp(mastery, 0, 1);
    int score = 0;

    const int towerGain = bundle.playerTower + bundle.bothTower - bundle.enemyTower;
    score += (player.tower >= 10 ? MasteryCoeff[0][masteryIndex] : 20) * towerGain;

    const int wallGain = bundle.playerWall + bundle.bothWall - bundle.enemyWall;
    score += (player.wall >= 10 ? MasteryCoeff[1][masteryIndex] : 5) * wallGain;

    score += 7 * (bundle.playerBuildings + bundle.bothBuildings - bundle.enemyBuildings);
    score += 40 * (bundle.playerQuarry + bundle.bothQuarry - bundle.enemyQuarry);
    score += 40 * (bundle.playerMagic + bundle.bothMagic - bundle.enemyMagic);
    score += 40 * (bundle.playerDungeon + bundle.bothDungeon - bundle.enemyDungeon);
    score += 2 * (bundle.playerBricks + bundle.bothBricks - bundle.enemyBricks);
    score += 2 * (bundle.playerGems + bundle.bothGems - bundle.enemyGems);
    score += 2 * (bundle.playerRecruits + bundle.bothRecruits - bundle.enemyRecruits);

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

    if (enemy.tower + std::min(0, bundle.enemyTower) <= 0)
    {
        score += 9999;
    }

    return score;
}
}
