#pragma once

#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/party/PartySpellSystem.h"

namespace OpenYAMM::Game
{
class GameplaySpellService;
class GameplayScreenRuntime;
struct GameplayInputFrame;

struct GameplayStandardUiHotkeyConfig
{
    const bool *pKeyboardState = nullptr;
    const GameplayInputFrame *pInputFrame = nullptr;
    bool canOpenRest = false;
    bool blockMenuToggle = false;
    bool blockSpellbookToggle = false;
    bool blockInventoryToggle = false;
    bool blockPartyCycle = false;
    bool requireGameplayReadyForPartySelection = false;
};

struct GameplayMouseLookPolicyConfig
{
    bool mouseLookAllowed = false;
    bool rightMousePressed = false;
};

struct GameplayMouseLookPolicyResult
{
    bool cursorModeActive = false;
    bool mouseLookActive = false;
    bool allowGameplayPointerInput = false;
};

// One frame of auto-walk (KeyboardAction::AutoWalk, OY-628).
struct GameplayAutoWalkInput
{
    bool togglePressed = false;
    bool forwardPressed = false;
    bool backwardPressed = false;
    // The party can walk: play with nothing open over it, no spell waiting for a target, no cinematic.
    bool canWalk = false;
    bool turnBased = false;
};

struct GameplaySharedGameplayHotkeyConfig
{
    const bool *pKeyboardState = nullptr;
    const GameplayInputFrame *pInputFrame = nullptr;
    bool canToggleAlwaysRun = false;
    bool canToggleAdventurersInn = false;
};

struct GameplaySharedInputFrameConfig
{
    const bool *pKeyboardState = nullptr;
    const GameplayInputFrame *pInputFrame = nullptr;
    float mouseWheelDelta = 0.0f;
    int screenWidth = 0;
    int screenHeight = 0;
    float pointerX = 0.0f;
    float pointerY = 0.0f;
    bool leftButtonPressed = false;
    bool rightButtonPressed = false;
    bool hasReadyMember = false;
    bool canBeginQuickCast = false;
    bool isUtilitySpellModalActive = false;
    // A reading overlay is open (a readable scroll, the loot summary): it takes the mouse from the HUD and world.
    bool isModalOverlayActive = false;
    bool processStandardUiInput = true;
    bool processSharedGameplayHotkeys = true;
    bool processQuickCast = true;
};

struct GameplaySharedInputFrameResult
{
    bool journalInputConsumed = false;
    bool worldInputBlocked = false;
    GameplayMouseLookPolicyResult mouseLookPolicy = {};
};

class GameplayInputController
{
public:
    // Whether auto-walk is on after this frame: its key turns it on and off; Forward, Backward, anything that stops the
    // party walking and turn-based combat turn it off.
    static bool updateAutoWalk(bool active, const GameplayAutoWalkInput &input);
    static GameplayMouseLookPolicyResult updateGameplayMouseLookPolicy(
        GameplayScreenState::GameplayMouseLookState &state,
        const GameplayMouseLookPolicyConfig &config);
    static void handleStandardUiHotkeys(
        GameplayScreenRuntime &context,
        const GameplayStandardUiHotkeyConfig &config);
    static void handleSharedGameplayHotkeys(
        GameplayScreenRuntime &context,
        const GameplaySharedGameplayHotkeyConfig &config);
    static GameplaySharedInputFrameResult updateSharedGameplayInputFrame(
        GameplayScreenState &screenState,
        GameplayScreenRuntime &context,
        GameplaySpellService &spellService,
        const GameplaySharedInputFrameConfig &config);
};
} // namespace OpenYAMM::Game
