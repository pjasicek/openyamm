#pragma once

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
// Which carried bottle a quick item slot drinks: the weakest saves the strong ones for later (the default).
enum class QuickItemBottleRule : uint8_t
{
    Weakest = 0,
    Strongest,
};

// One of a character's quick item slots (the potion radial, devdocs/maw/GAPS.md H.6): a kind of potion or scroll, by
// item id. Using it takes the first matching item from the character's bags; the slot keeps its kind when none is left.
struct QuickItemSlot
{
    uint32_t itemId = 0;
    QuickItemBottleRule bottleRule = QuickItemBottleRule::Weakest;

    bool operator==(const QuickItemSlot &) const = default;
};

constexpr size_t QuickItemSlotCount = 6;
}
