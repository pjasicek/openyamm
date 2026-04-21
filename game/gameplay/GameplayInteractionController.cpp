#include "game/gameplay/GameplayInteractionController.h"

namespace OpenYAMM::Game
{
namespace
{
constexpr float NearHoverStatusDistance = 512.0f;
constexpr float ActorHoverStatusDistance = 8192.0f;

bool hasStatusText(const std::optional<std::string> &text)
{
    return text.has_value() && !text->empty();
}
}

GameplayInteractionController::HoverStateResult GameplayInteractionController::updateHoverState(
    const HoverStateInput &input)
{
    HoverStateResult result = {};

    if (!input.allowHover)
    {
        if (input.clearHover)
        {
            input.clearHover();
            result.cleared = true;
        }

        return result;
    }

    const bool shouldRefreshHover =
        !input.hasCachedHover
        || input.currentTickNanoseconds < input.lastUpdateNanoseconds
        || input.currentTickNanoseconds - input.lastUpdateNanoseconds >= input.refreshIntervalNanoseconds;

    GameplayHoverStatusPayload payload = {};

    if (shouldRefreshHover)
    {
        if (input.refreshHover)
        {
            payload = input.refreshHover();
            result.refreshed = true;
        }
    }
    else if (input.readCachedHover)
    {
        payload = input.readCachedHover();
    }

    const std::optional<std::string> statusText = resolveHoverStatusText(payload);
    result.hitKind = payload.worldHit.kind;
    result.statusText = statusText.value_or("");
    result.hasHover = result.hitKind != GameplayWorldHitKind::None || !result.statusText.empty();
    return result;
}

GameplayInteractionController::MouseClickInteractionResult GameplayInteractionController::updateMouseClickInteraction(
    GameplayScreenState::WorldInteractionInputState &state,
    const MouseClickInteractionInput &input)
{
    MouseClickInteractionResult result = {};

    if (input.leftMousePressed && !input.pointerOverPartyPortrait)
    {
        if (!state.inspectMouseActivateLatch)
        {
            state.pressedWorldHit = input.currentHit;
            state.inspectMouseActivateLatch = true;
            result.armed = true;
        }

        return result;
    }

    if (!state.inspectMouseActivateLatch)
    {
        return result;
    }

    result.released = true;

    if (!input.pointerOverPartyPortrait && isSameActivationTarget(state.pressedWorldHit, input.currentHit))
    {
        const bool canActivate = !input.canActivate || input.canActivate(input.currentHit);
        if (canActivate && input.activate)
        {
            result.activated = input.activate(input.currentHit);
        }
    }

    state.inspectMouseActivateLatch = false;
    state.pressedWorldHit = {};
    result.cleared = true;
    return result;
}

GameplayInteractionController::KeyboardInteractionResult GameplayInteractionController::updateKeyboardInteraction(
    GameplayScreenState::WorldInteractionInputState &state,
    const KeyboardInteractionInput &input)
{
    KeyboardInteractionResult result = {};

    if (!input.interactionPressed)
    {
        if (state.keyboardUseLatch)
        {
            result.cleared = true;
        }

        state.keyboardUseLatch = false;
        return result;
    }

    if (state.keyboardUseLatch)
    {
        return result;
    }

    if (!input.allowInteraction)
    {
        return result;
    }

    state.keyboardUseLatch = true;
    result.latched = true;

    GameplayWorldHit hit = {};

    if (input.pickHit)
    {
        hit = input.pickHit();
        result.picked = true;
    }

    if (!hit.hasHit)
    {
        return result;
    }

    const bool canActivate = !input.canActivate || input.canActivate(hit);
    if (canActivate && input.activate)
    {
        result.activated = input.activate(hit);
    }

    return result;
}

GameplayInteractionController::KeyboardActivationInteractionResult
GameplayInteractionController::updateKeyboardActivationInteraction(
    GameplayScreenState::WorldInteractionInputState &state,
    const KeyboardActivationInteractionInput &input)
{
    KeyboardActivationInteractionResult result = {};

    if (!input.activationPressed)
    {
        if (state.inspectKeyboardActivateLatch)
        {
            result.cleared = true;
        }

        state.inspectKeyboardActivateLatch = false;
        return result;
    }

    if (state.inspectKeyboardActivateLatch)
    {
        return result;
    }

    if (!input.allowInteraction)
    {
        return result;
    }

    state.inspectKeyboardActivateLatch = true;
    result.latched = true;

    if (!input.currentHit.hasHit)
    {
        return result;
    }

    const bool canActivate = !input.canActivate || input.canActivate(input.currentHit);
    if (canActivate && input.activate)
    {
        result.activated = input.activate(input.currentHit);
    }

    return result;
}

GameplayInteractionController::HeldItemWorldInteractionResult
GameplayInteractionController::updateHeldItemWorldInteraction(
    GameplayScreenState::WorldInteractionInputState &state,
    const HeldItemWorldInteractionInput &input)
{
    HeldItemWorldInteractionResult result = {};

    if (!input.heldItemActive)
    {
        if (state.heldInventoryDropLatch)
        {
            result.cleared = true;
        }

        state.heldInventoryDropLatch = false;
        return result;
    }

    if (input.leftMousePressed)
    {
        if (!state.heldInventoryDropLatch)
        {
            state.heldInventoryDropLatch = true;
            result.latched = true;
        }

        return result;
    }

    if (!state.heldInventoryDropLatch)
    {
        return result;
    }

    result.released = true;

    bool handledInteraction = input.pointerOverPartyPortrait;
    result.portraitHandled = handledInteraction;

    if (!handledInteraction)
    {
        GameplayWorldHit hit = {};

        if (input.pickHit)
        {
            hit = input.pickHit();
            result.picked = true;
        }

        if (hit.hasHit)
        {
            const bool canUseOnWorld = !input.canUseOnWorld || input.canUseOnWorld(hit);
            if (canUseOnWorld && input.useOnWorld)
            {
                handledInteraction = input.useOnWorld(hit);
                result.usedOnWorld = handledInteraction;
            }
        }
    }

    if (!handledInteraction)
    {
        result.dropRequested = true;

        if (input.dropHeldItem)
        {
            result.dropped = input.dropHeldItem();
        }
    }

    state.heldInventoryDropLatch = false;
    result.cleared = true;
    return result;
}

std::optional<std::string> GameplayInteractionController::resolveHoverStatusText(
    const GameplayHoverStatusPayload &payload)
{
    const GameplayWorldHit &hit = payload.worldHit;

    if (!hit.hasHit)
    {
        return std::nullopt;
    }

    if (hit.kind == GameplayWorldHitKind::Actor)
    {
        if (!hit.actor || hit.actor->distance > ActorHoverStatusDistance || hit.actor->displayName.empty())
        {
            return std::nullopt;
        }

        return hit.actor->displayName;
    }

    if (hit.kind != GameplayWorldHitKind::EventTarget
        || !hit.eventTarget
        || !hasStatusText(payload.eventTargetStatusText))
    {
        return std::nullopt;
    }

    const GameplayWorldEventTargetKind targetKind = hit.eventTarget->targetKind;
    const bool requireNearHover =
        targetKind == GameplayWorldEventTargetKind::Surface
        || targetKind == GameplayWorldEventTargetKind::Entity;

    if (requireNearHover && hit.eventTarget->distance > NearHoverStatusDistance)
    {
        return std::nullopt;
    }

    return payload.eventTargetStatusText;
}

bool GameplayInteractionController::canDispatchWorldActivation(const WorldActivationDispatchInput &input)
{
    if (!input.hit.hasHit)
    {
        return false;
    }

    if (input.hit.kind == GameplayWorldHitKind::Actor)
    {
        return input.canActivateActor && input.canActivateActor(input.hit);
    }

    if (input.hit.kind == GameplayWorldHitKind::WorldItem)
    {
        return input.canActivateWorldItem && input.canActivateWorldItem(input.hit);
    }

    if (input.hit.kind == GameplayWorldHitKind::Chest || input.hit.kind == GameplayWorldHitKind::Corpse)
    {
        return input.canActivateContainer && input.canActivateContainer(input.hit);
    }

    if (input.hit.kind == GameplayWorldHitKind::EventTarget)
    {
        return input.canActivateEventTarget && input.canActivateEventTarget(input.hit);
    }

    return input.canActivateFallback && input.canActivateFallback(input.hit);
}

bool GameplayInteractionController::dispatchWorldActivation(const WorldActivationDispatchInput &input)
{
    if (!input.hit.hasHit)
    {
        return false;
    }

    if (input.hit.kind == GameplayWorldHitKind::Actor)
    {
        return input.activateActor && input.activateActor(input.hit);
    }

    if (input.hit.kind == GameplayWorldHitKind::WorldItem)
    {
        return input.activateWorldItem && input.activateWorldItem(input.hit);
    }

    if (input.hit.kind == GameplayWorldHitKind::Chest || input.hit.kind == GameplayWorldHitKind::Corpse)
    {
        return input.activateContainer && input.activateContainer(input.hit);
    }

    if (input.hit.kind == GameplayWorldHitKind::EventTarget)
    {
        return input.activateEventTarget && input.activateEventTarget(input.hit);
    }

    return input.activateFallback && input.activateFallback(input.hit);
}

bool GameplayInteractionController::isSameActivationTarget(
    const GameplayWorldHit &lhs,
    const GameplayWorldHit &rhs)
{
    if (!lhs.hasHit || !rhs.hasHit || lhs.kind != rhs.kind)
    {
        return false;
    }

    if (lhs.kind == GameplayWorldHitKind::Actor)
    {
        return lhs.actor.has_value()
            && rhs.actor.has_value()
            && lhs.actor->actorIndex == rhs.actor->actorIndex;
    }

    if (lhs.kind == GameplayWorldHitKind::WorldItem)
    {
        return lhs.worldItem.has_value()
            && rhs.worldItem.has_value()
            && lhs.worldItem->worldItemIndex == rhs.worldItem->worldItemIndex;
    }

    if (lhs.kind == GameplayWorldHitKind::Chest || lhs.kind == GameplayWorldHitKind::Corpse)
    {
        return lhs.container.has_value()
            && rhs.container.has_value()
            && lhs.container->sourceKind == rhs.container->sourceKind
            && lhs.container->sourceIndex == rhs.container->sourceIndex;
    }

    if (lhs.kind == GameplayWorldHitKind::EventTarget)
    {
        return lhs.eventTarget.has_value()
            && rhs.eventTarget.has_value()
            && lhs.eventTarget->targetKind == rhs.eventTarget->targetKind
            && lhs.eventTarget->targetIndex == rhs.eventTarget->targetIndex
            && lhs.eventTarget->secondaryIndex == rhs.eventTarget->secondaryIndex
            && lhs.eventTarget->eventIdPrimary == rhs.eventTarget->eventIdPrimary
            && lhs.eventTarget->eventIdSecondary == rhs.eventTarget->eventIdSecondary
            && lhs.eventTarget->triggeredEventId == rhs.eventTarget->triggeredEventId
            && lhs.eventTarget->specialTrigger == rhs.eventTarget->specialTrigger;
    }

    if (lhs.kind == GameplayWorldHitKind::Object)
    {
        return lhs.object.has_value()
            && rhs.object.has_value()
            && lhs.object->objectIndex == rhs.object->objectIndex;
    }

    return false;
}
} // namespace OpenYAMM::Game
