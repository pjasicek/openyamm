#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayOverlayInputController
{
public:
    static void handleDialogueOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool isResidentSelectionMode);
    static void handleLootOverlayInput(
        GameplayOverlayContext &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight,
        bool hasActiveLootView);
};
} // namespace OpenYAMM::Game
