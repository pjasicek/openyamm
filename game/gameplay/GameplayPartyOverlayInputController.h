#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayPartyOverlayInputController
{
public:
    static void handleUtilitySpellOverlayInput(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static void handleSpellbookOverlayInput(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static void handleCharacterOverlayInput(
        GameplayScreenRuntime &context,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
};
} // namespace OpenYAMM::Game
