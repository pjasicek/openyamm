#pragma once

#include "game/items/InventoryItemUseRuntime.h"

#include <cstddef>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

// The row of markers under a spellbook (on a guild shelf, a merchant's list and the inspect popup): one per party
// member in portrait order, saying whether the member knows the spell, can learn it now, could after training, or
// never can. See level_generation/ui/spell_known_markers_20261113/README.md.
namespace SpellbookKnowledgeMarkers
{
// The plate's size in HUD units (the 640x480 reference) for a party of `memberCount`.
float plateWidth(size_t memberCount);
float plateHeight();
// Draws the plate with the middle of its top edge at (centerX, top) in screen pixels; `scale` is pixels per HUD unit.
void render(
    GameplayScreenRuntime &context,
    const std::vector<SpellbookKnowledge> &knowledge,
    float centerX,
    float top,
    float scale);
}
}
