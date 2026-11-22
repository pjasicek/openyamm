#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PlayerId.h"

#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// A world holds one open chest and one open corpse: those of the player who acts now, the local player but while
// another player's command runs (IGameplayWorldRuntime::swapActingParty). The open chest and corpse of every player
// who is not acting wait here. What waits here is in use: no other player opens that chest or corpse until its
// player closes it.
class WaitingPlayerViews
{
public:
    // Puts away what the player who acted has open and brings out what the next player has open.
    void exchange(
        PlayerId from,
        PlayerId to,
        std::optional<GameplayChestViewState> &chest,
        std::optional<GameplayCorpseViewState> &corpse)
    {
        if (from == to)
        {
            return;
        }

        if (chest || corpse)
        {
            Views &waiting = m_views[from];
            waiting.chest = std::move(chest);
            waiting.corpse = std::move(corpse);
        }

        chest.reset();
        corpse.reset();
        const std::unordered_map<PlayerId, Views>::iterator it = m_views.find(to);

        if (it != m_views.end())
        {
            chest = std::move(it->second.chest);
            corpse = std::move(it->second.corpse);
            m_views.erase(it);
        }
    }

    bool holdsChest(uint32_t chestId) const
    {
        for (const std::pair<const PlayerId, Views> &entry : m_views)
        {
            if (entry.second.chest && entry.second.chest->chestId == chestId)
            {
                return true;
            }
        }

        return false;
    }

    bool holdsCorpse(const GameplayCorpseViewState &corpse) const
    {
        for (const std::pair<const PlayerId, Views> &entry : m_views)
        {
            if (entry.second.corpse && entry.second.corpse->sourceIndex == corpse.sourceIndex
                && entry.second.corpse->fromSummonedMonster == corpse.fromSummonedMonster)
            {
                return true;
            }
        }

        return false;
    }

    // Forgets what players who left the game had open; the local player always stays.
    void keepPlayers(const std::vector<GameplayGuestBody> &guests)
    {
        std::erase_if(
            m_views,
            [&guests](const std::pair<const PlayerId, Views> &entry)
            {
                if (entry.first == LocalPlayer)
                {
                    return false;
                }

                for (const GameplayGuestBody &guest : guests)
                {
                    if (guest.player == entry.first)
                    {
                        return false;
                    }
                }

                return true;
            });
    }

    void clear()
    {
        m_views.clear();
    }

private:
    struct Views
    {
        std::optional<GameplayChestViewState> chest;
        std::optional<GameplayCorpseViewState> corpse;
    };

    std::unordered_map<PlayerId, Views> m_views;
};
}
