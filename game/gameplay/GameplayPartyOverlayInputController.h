#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;
class OutdoorGameView;

class GameplayPartyOverlayInputController
{
public:
    static void handleUtilitySpellOverlayInput(
        OutdoorGameView &view,
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
    static void handleCharacterOverlayInput(
        OutdoorGameView &view,
        const bool *pKeyboardState,
        int screenWidth,
        int screenHeight);
};
} // namespace OpenYAMM::Game
