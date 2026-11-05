#pragma once

#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class GameplaySpellService;
struct GameplayInputFrame;
struct GameplaySharedInputFrameResult;

class GameplayInteractionController
{
public:
    struct HoverStateInput
    {
        bool allowHover = false;
        uint64_t currentTickNanoseconds = 0;
        uint64_t refreshIntervalNanoseconds = 0;
        GameplayWorldHoverRequest hoverRequest = {};
        // Autonotes, for the effects of events the party has learned (Orange Barrel (+2 Intellect)).
        const GameplayScreenRuntime *pScreenRuntime = nullptr;
    };

    struct HoverStateResult
    {
        bool hasHover = false;
        bool refreshed = false;
        bool cleared = false;
        GameplayWorldHitKind hitKind = GameplayWorldHitKind::None;
        GameplayWorldHit worldHit = {};
        std::optional<std::string> eventTargetStatusText;
        std::string statusText;
    };

    struct MouseClickInteractionInput
    {
        bool leftMousePressed = false;
        bool pointerOverPartyPortrait = false;
        GameplayWorldHit currentHit;
        GameplayScreenRuntime *pRuntime = nullptr;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
        GameplayInteractionMethod interactionMethod = GameplayInteractionMethod::Mouse;
    };

    struct MouseClickInteractionResult
    {
        bool armed = false;
        bool released = false;
        bool activated = false;
        bool cleared = false;
    };

    struct KeyboardInteractionInput
    {
        bool interactionPressed = false;
        bool allowInteraction = false;
        uint64_t currentTickNanoseconds = 0;
        GameplayWorldHit pickedHit;
        bool hasPickedHit = false;
        GameplayScreenRuntime *pRuntime = nullptr;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
        GameplayInteractionMethod interactionMethod = GameplayInteractionMethod::Keyboard;
    };

    struct KeyboardInteractionResult
    {
        bool latched = false;
        bool picked = false;
        bool activated = false;
        bool cleared = false;
    };

    struct KeyboardActivationInteractionInput
    {
        bool activationPressed = false;
        bool allowInteraction = false;
        uint64_t currentTickNanoseconds = 0;
        GameplayWorldHit currentHit;
        GameplayScreenRuntime *pRuntime = nullptr;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
        GameplayInteractionMethod interactionMethod = GameplayInteractionMethod::Keyboard;
    };

    struct KeyboardActivationInteractionResult
    {
        bool latched = false;
        bool activated = false;
        bool cleared = false;
    };

    struct HeldItemWorldInteractionInput
    {
        bool heldItemActive = false;
        bool leftMousePressed = false;
        bool pointerOverPartyPortrait = false;
        GameplayWorldHit pickedHit;
        bool hasPickedHit = false;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
    };

    struct HeldItemWorldInteractionResult
    {
        bool latched = false;
        bool released = false;
        bool picked = false;
        bool portraitHandled = false;
        bool usedOnWorld = false;
        bool dropRequested = false;
        bool dropped = false;
        bool cleared = false;
    };

    struct WorldInteractionPointerPolicyInput
    {
        bool pendingSpellActive = false;
        bool heldItemActive = false;
        bool mouseLookActive = false;
        bool cursorModeActive = false;
        bool leftMousePressed = false;
        bool rightMousePressed = false;
        bool keyboardActivationPressed = false;
        bool keyboardAttackPressed = false;
        float pointerX = 0.0f;
        float pointerY = 0.0f;
        float screenWidth = 0.0f;
        float screenHeight = 0.0f;
        bool pointerOverPortrait = false;
    };

    struct WorldInteractionPointerPolicy
    {
        bool useCenterGameplayPoint = false;
        bool leftMousePressed = false;
        bool pointerOverPartyPortrait = false;
        bool activationPressed = false;
        bool attackPressed = false;
        float inspectScreenX = 0.0f;
        float inspectScreenY = 0.0f;
    };

    struct WorldInteractionFrameResult
    {
        bool blocked = false;
        bool pendingSpellHandled = false;
        bool heldItemHandled = false;
        bool keyboardUseActivated = false;
        bool keyboardActivationActivated = false;
        bool mouseActivationActivated = false;
        bool attackAttempted = false;
        HoverStateResult hover = {};
    };

    static HoverStateResult updateHoverState(
        const HoverStateInput &input,
        IGameplayWorldRuntime *pWorldRuntime);
    static MouseClickInteractionResult updateMouseClickInteraction(
        GameplayScreenState::WorldInteractionInputState &state,
        const MouseClickInteractionInput &input);
    static KeyboardInteractionResult updateKeyboardInteraction(
        GameplayScreenState::WorldInteractionInputState &state,
        const KeyboardInteractionInput &input);
    static KeyboardActivationInteractionResult updateKeyboardActivationInteraction(
        GameplayScreenState::WorldInteractionInputState &state,
        const KeyboardActivationInteractionInput &input);
    static HeldItemWorldInteractionResult updateHeldItemWorldInteraction(
        GameplayScreenState::WorldInteractionInputState &state,
        const HeldItemWorldInteractionInput &input);
    static std::optional<std::string> resolveHoverStatusText(
        const GameplayHoverStatusPayload &payload,
        bool heldItemActive);
    static WorldInteractionPointerPolicy resolveWorldInteractionPointerPolicy(
        const WorldInteractionPointerPolicyInput &input);
    // The Space target: what is under the crosshair (or cursor) when Space can use it, otherwise the world's screen
    // scan for the usable target nearest the crosshair. Empty when neither is usable.
    static GameplayWorldHit pickKeyboardUseTarget(
        IGameplayWorldRuntime &worldRuntime,
        const GameplayWorldPickRequest &request);
    // Ctrl + left click steals from the creature clicked, as in the original: under the cursor, or with mouse look
    // the one in the crosshair.
    static bool stealClickPressed(
        const GameplayInputFrame &input,
        const WorldInteractionPointerPolicy &pointerPolicy);
    // Whether the attack waits: from a steal click until the left button is released, so the next ready member
    // does not strike while the button is still held.
    static bool stealClickHoldsAttack(bool &stealClickLatch, const GameplayInputFrame &input, bool stealPressed);
    static WorldInteractionFrameResult updateWorldInteractionFrame(
        GameplayScreenState &screenState,
        GameplayOverlayInteractionState &overlayInteractionState,
        GameplayScreenRuntime &runtime,
        GameplaySpellService &spellService,
        const GameplayInputFrame &input,
        const GameplaySharedInputFrameResult &sharedInput,
        bool worldInputBlocked);
    // Drops the held item in front of the party, for the touch Drop buttons.
    static bool dropHeldItemInFrontOfParty(GameplayScreenRuntime &runtime);

private:
    static bool isSameActivationTarget(const GameplayWorldHit &lhs, const GameplayWorldHit &rhs);
};
} // namespace OpenYAMM::Game
