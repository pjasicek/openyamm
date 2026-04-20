#pragma once

#include "game/app/KeyboardBindings.h"

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

struct GameplayScreenHotkeyConfig
{
    bool canToggleSpellbook = false;
    bool canToggleInventory = false;
    bool canCyclePartyMember = false;
    bool hasActiveLootView = false;
    bool requireGameplayReadyForPartySelection = false;
};

class GameplayScreenHotkeyController
{
public:
    static void handleGameplayScreenHotkeys(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        const GameplayScreenHotkeyConfig &config);
};
} // namespace OpenYAMM::Game
