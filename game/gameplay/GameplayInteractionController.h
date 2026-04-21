#pragma once

#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplayWorldInteraction.h"

#include <cstdint>
#include <functional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayInteractionController
{
public:
    struct HoverStateInput
    {
        bool allowHover = false;
        bool hasCachedHover = false;
        uint64_t currentTickNanoseconds = 0;
        uint64_t lastUpdateNanoseconds = 0;
        uint64_t refreshIntervalNanoseconds = 0;
        std::function<GameplayHoverStatusPayload()> refreshHover;
        std::function<GameplayHoverStatusPayload()> readCachedHover;
        std::function<void()> clearHover;
    };

    struct HoverStateResult
    {
        bool hasHover = false;
        bool refreshed = false;
        bool cleared = false;
        GameplayWorldHitKind hitKind = GameplayWorldHitKind::None;
        std::string statusText;
    };

    struct MouseClickInteractionInput
    {
        bool leftMousePressed = false;
        bool pointerOverPartyPortrait = false;
        GameplayWorldHit currentHit;
        std::function<bool(const GameplayWorldHit &hit)> canActivate;
        std::function<bool(const GameplayWorldHit &hit)> activate;
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
        std::function<GameplayWorldHit()> pickHit;
        std::function<bool(const GameplayWorldHit &hit)> canActivate;
        std::function<bool(const GameplayWorldHit &hit)> activate;
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
        GameplayWorldHit currentHit;
        std::function<bool(const GameplayWorldHit &hit)> canActivate;
        std::function<bool(const GameplayWorldHit &hit)> activate;
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
        std::function<GameplayWorldHit()> pickHit;
        std::function<bool(const GameplayWorldHit &hit)> canUseOnWorld;
        std::function<bool(const GameplayWorldHit &hit)> useOnWorld;
        std::function<bool()> dropHeldItem;
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

    struct WorldActivationDispatchInput
    {
        GameplayWorldHit hit;
        std::function<bool(const GameplayWorldHit &hit)> canActivateActor;
        std::function<bool(const GameplayWorldHit &hit)> activateActor;
        std::function<bool(const GameplayWorldHit &hit)> canActivateWorldItem;
        std::function<bool(const GameplayWorldHit &hit)> activateWorldItem;
        std::function<bool(const GameplayWorldHit &hit)> canActivateContainer;
        std::function<bool(const GameplayWorldHit &hit)> activateContainer;
        std::function<bool(const GameplayWorldHit &hit)> canActivateEventTarget;
        std::function<bool(const GameplayWorldHit &hit)> activateEventTarget;
        std::function<bool(const GameplayWorldHit &hit)> canActivateFallback;
        std::function<bool(const GameplayWorldHit &hit)> activateFallback;
    };

    static HoverStateResult updateHoverState(const HoverStateInput &input);
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
    static std::optional<std::string> resolveHoverStatusText(const GameplayHoverStatusPayload &payload);
    static bool canDispatchWorldActivation(const WorldActivationDispatchInput &input);
    static bool dispatchWorldActivation(const WorldActivationDispatchInput &input);

private:
    static bool isSameActivationTarget(const GameplayWorldHit &lhs, const GameplayWorldHit &rhs);
};
} // namespace OpenYAMM::Game
