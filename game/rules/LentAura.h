#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
// An aura one player's party lends to the other players' parties that stand near it (co-op, a ruleset with auras:
// MAW): the spell and its holder's strength. The borrower's rules apply it as one of its own that nobody in the
// party holds; it reserves nothing there.
struct LentAura
{
    uint32_t spellId = 0;
    float skill = 0.0f;
    uint8_t mastery = 0;
    float level = 0.0f;

    bool operator==(const LentAura &) const = default;
};
}
