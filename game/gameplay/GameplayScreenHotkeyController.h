#pragma once

#include "game/app/KeyboardBindings.h"

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

struct GameplayScreenHotkeyConfig
{
    bool canToggleMenu = false;
    bool canOpenRest = false;
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
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        const GameplayScreenHotkeyConfig &config);
};
} // namespace OpenYAMM::Game
