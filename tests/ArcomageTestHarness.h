#pragma once

#include "game/arcomage/ArcomageAi.h"
#include "game/arcomage/ArcomageRules.h"

#include <algorithm>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Tests
{
inline int arcomageShownCardCount(const Game::ArcomageState &state)
{
    return static_cast<int>(std::count_if(
        state.shownCards.begin(),
        state.shownCards.end(),
        [](const std::optional<Game::ArcomagePlayedCard> &shownCard)
        {
            return shownCard.has_value();
        }));
}

inline int arcomageHandCardCount(const Game::ArcomagePlayerState &player)
{
    return static_cast<int>(std::count_if(
        player.hand.begin(),
        player.hand.end(),
        [](int cardId)
        {
            return cardId >= 0;
        }));
}

struct ArcomageTestHarness
{
    const Game::ArcomageLibrary *m_pLibrary = nullptr;
    Game::ArcomageRules rules;
    Game::ArcomageAi ai;
    Game::ArcomageState state = {};

    bool initialize(const Game::ArcomageLibrary &library, uint32_t houseId, uint32_t seed = 1u)
    {
        m_pLibrary = &library;
        return rules.initializeMatch(library, houseId, "Ariel", "Innkeeper", seed, state);
    }

    void clearHands()
    {
        for (Game::ArcomagePlayerState &player : state.players)
        {
            player.hand.fill(-1);
        }

        state.mustDiscard = false;
    }

    bool setHand(size_t playerIndex, const std::vector<uint32_t> &cardIds)
    {
        if (playerIndex >= state.players.size() || cardIds.size() > state.players[playerIndex].hand.size())
        {
            return false;
        }

        state.players[playerIndex].hand.fill(-1);

        for (size_t index = 0; index < cardIds.size(); ++index)
        {
            state.players[playerIndex].hand[index] = static_cast<int>(cardIds[index]);
        }

        return true;
    }

    std::optional<uint32_t> cardIdByName(const std::string &name) const
    {
        if (m_pLibrary == nullptr)
        {
            return std::nullopt;
        }

        const Game::ArcomageCardDefinition *pCard = m_pLibrary->cardByName(name);
        return pCard != nullptr ? std::optional<uint32_t>{pCard->id} : std::nullopt;
    }

    bool playCardById(size_t playerIndex, uint32_t cardId)
    {
        if (m_pLibrary == nullptr)
        {
            return false;
        }

        const int handIndex = findHandIndex(playerIndex, cardId);

        if (handIndex < 0)
        {
            return false;
        }

        state.currentPlayerIndex = playerIndex;
        state.needsTurnStart = false;
        return rules.playCard(*m_pLibrary, static_cast<size_t>(handIndex), state);
    }

    bool discardCardById(size_t playerIndex, uint32_t cardId)
    {
        if (m_pLibrary == nullptr)
        {
            return false;
        }

        const int handIndex = findHandIndex(playerIndex, cardId);

        if (handIndex < 0)
        {
            return false;
        }

        state.currentPlayerIndex = playerIndex;
        state.needsTurnStart = false;
        return rules.discardCard(*m_pLibrary, static_cast<size_t>(handIndex), state);
    }

    bool applyAiAction(const Game::ArcomageAi::Action &action)
    {
        if (m_pLibrary == nullptr)
        {
            return false;
        }

        switch (action.kind)
        {
            case Game::ArcomageAi::ActionKind::PlayCard:
                return rules.playCard(*m_pLibrary, action.handIndex, state);

            case Game::ArcomageAi::ActionKind::DiscardCard:
                return rules.discardCard(*m_pLibrary, action.handIndex, state);

            case Game::ArcomageAi::ActionKind::None:
                return false;
        }

        return false;
    }

private:
    int findHandIndex(size_t playerIndex, uint32_t cardId) const
    {
        if (playerIndex >= state.players.size())
        {
            return -1;
        }

        const Game::ArcomagePlayerState &player = state.players[playerIndex];

        for (size_t handIndex = 0; handIndex < player.hand.size(); ++handIndex)
        {
            if (player.hand[handIndex] == static_cast<int>(cardId))
            {
                return static_cast<int>(handIndex);
            }
        }

        return -1;
    }
};
}
