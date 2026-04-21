#pragma once

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
class GameplayScreenRuntime;

class GameplayPartyOverlayInputController
{
public:
    static void handleUtilitySpellOverlayInput(
        GameplayScreenRuntime &context,
        const GameplayInputFrame &input);
    static void handleSpellbookOverlayInput(
        GameplayScreenRuntime &context,
        const GameplayInputFrame &input);
    static void handleCharacterOverlayInput(
        GameplayScreenRuntime &context,
        const GameplayInputFrame &input);
};
} // namespace OpenYAMM::Game
