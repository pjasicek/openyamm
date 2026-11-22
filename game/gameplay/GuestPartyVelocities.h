#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <algorithm>
#include <span>
#include <vector>

namespace OpenYAMM::Game
{
// How fast the other players' parties move, for the monsters that lead their shots (a co-op host's game). Another
// player's party is placed where its own game says, some twenty times a second, so its speed is taken between two
// places it was told at, not between two frames (most frames it has not moved at all).
class GuestPartyVelocities
{
public:
    void update(std::span<const GameplayGuestBody> guests, float deltaSeconds)
    {
        std::erase_if(m_entries, [guests](const Entry &entry)
            {
                return std::none_of(guests.begin(), guests.end(),
                    [&entry](const GameplayGuestBody &guest) { return guest.player == entry.player; });
            });

        for (const GameplayGuestBody &guest : guests)
        {
            auto entry = std::find_if(m_entries.begin(), m_entries.end(),
                [&guest](const Entry &known) { return known.player == guest.player; });

            if (entry == m_entries.end())
            {
                m_entries.push_back(Entry{guest.player, {}, 0.0f});
                entry = std::prev(m_entries.end());
            }

            entry->sinceToldSeconds += deltaSeconds;

            // A new place, or none for a while: it stands.
            if (!entry->tracker.hasLast || guest.body.x != entry->tracker.lastX || guest.body.y != entry->tracker.lastY
                || entry->sinceToldSeconds >= StandingAfterSeconds)
            {
                entry->tracker.update(guest.body.x, guest.body.y, entry->sinceToldSeconds);
                entry->sinceToldSeconds = 0.0f;
            }
        }
    }

    // Zero for a player not known here.
    ActorPartyVelocityTracker of(PlayerId player) const
    {
        for (const Entry &entry : m_entries)
        {
            if (entry.player == player)
            {
                return entry.tracker;
            }
        }

        return {};
    }

private:
    static constexpr float StandingAfterSeconds = 0.25f;

    struct Entry
    {
        PlayerId player = LocalPlayer;
        ActorPartyVelocityTracker tracker;
        float sinceToldSeconds = 0.0f;
    };

    std::vector<Entry> m_entries;
};
}
