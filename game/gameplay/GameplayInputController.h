#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

struct GameplayStandardUiHotkeyConfig
{
    const bool *pKeyboardState = nullptr;
    bool canOpenRest = false;
    bool blockMenuToggle = false;
    bool blockSpellbookToggle = false;
    bool blockInventoryToggle = false;
    bool blockPartyCycle = false;
    bool requireGameplayReadyForPartySelection = false;
};

class GameplayInputController
{
public:
    static void handleStandardUiHotkeys(
        GameplayScreenRuntime &context,
        const GameplayStandardUiHotkeyConfig &config);
};
} // namespace OpenYAMM::Game
