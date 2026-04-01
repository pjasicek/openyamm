#pragma once

namespace OpenYAMM::Game
{
class OutdoorGameView;

class GameplayPartyOverlayInputController
{
public:
    static void handleSpellbookOverlayInput(
        OutdoorGameView &view,
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
