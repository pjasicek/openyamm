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
    bool isReadableScrollOverlayActive = false;
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
