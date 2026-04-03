#pragma once

#include "game/arcomage/ArcomageTypes.h"

#include <cstddef>

namespace OpenYAMM::Game
{
class ArcomageAi
{
public:
    enum class ActionKind : uint8_t
    {
        None = 0,
        PlayCard,
        DiscardCard,
    };

    struct Action
    {
        ActionKind kind = ActionKind::None;
        size_t handIndex = 0;
    };

    Action chooseAction(const ArcomageLibrary &library, const ArcomageState &state) const;

private:
    static int calculateCardPower(
        const ArcomageCardDefinition &card,
        const ArcomagePlayerState &player,
        const ArcomagePlayerState &enemy,
        int mastery
    );
};
}
