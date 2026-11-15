#pragma once

#include "game/party/QuickItemSlot.h"

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
// What one slot of the solo run's action bar holds (devdocs/solo_action/HUD.md "Action bar"). Saved per character;
// only a solo run shows and uses the bar.
enum class ActionBarSlotKind : uint8_t
{
    Empty = 0,
    // `id` is a spell id: pressing the key casts it through the quick spell's path.
    Spell,
    // `item` names a kind of potion or scroll, used as a quick item slot is.
    Item,
    // The weapon attack (Attack's own action), for players who want the swing on a key; `id` ActionBarWeaponSwapId
    // instead swaps the melee weapon and the bow (as KeyboardAction::NextWeapon does).
    Weapon,
    // A special skill (talent) of a MAW solo run: `id` is its index in the talent table (game/rules/SoloTalents.h).
    Talent,
};

struct ActionBarSlot
{
    ActionBarSlotKind kind = ActionBarSlotKind::Empty;
    uint32_t id = 0;
    QuickItemSlot item = {};

    bool operator==(const ActionBarSlot &) const = default;
};

// A weapon slot's id: 0 attacks, this swaps the melee weapon and the bow.
constexpr uint32_t ActionBarWeaponSwapId = 1;

// Two rows of ten (the main row on 1-0, a second row kept for a Shift row); the 2 x 5 layout uses the first ten.
constexpr size_t ActionBarSlotCount = 20;
}
