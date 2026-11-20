#pragma once

#include "game/party/CharacterRulesetState.h"

#include <array>
#include <optional>

namespace OpenYAMM::Game
{
// A party inventory showing one of the party's pouches in the bags' place (rulesets with pouches; the hammer and
// potion buttons): which one, the row each pouch's view starts at, and the scrollbar's thumb being dragged (the
// pointer's offset from its top). Not saved.
struct InventoryPouchViewState
{
    std::optional<ItemPouch> shown;
    std::array<int, ItemPouchCount> firstRow = {};
    std::optional<float> thumbDragOffset;
};
}
