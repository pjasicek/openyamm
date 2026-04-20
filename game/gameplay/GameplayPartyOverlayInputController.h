#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayPartyOverlayInputController
{
public:
    static void handleUtilitySpellOverlayInput(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static void handleSpellbookOverlayInput(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
    static void handleCharacterOverlayInput(
        GameplayOverlayContext &context,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
};
} // namespace OpenYAMM::Game
