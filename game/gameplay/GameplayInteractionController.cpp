#include "game/gameplay/GameplayInteractionController.h"

#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/tables/ItemTable.h"

#include <SDL3/SDL_timer.h>

#include <chrono>

namespace OpenYAMM::Game
{
namespace
{
constexpr float NearHoverStatusDistance = 512.0f;
constexpr float ActorHoverStatusDistance = 8192.0f;
constexpr uint64_t HoverInspectRefreshNanoseconds = 33 * 1000 * 1000;
constexpr uint32_t ArrowProjectileObjectId = 545;
constexpr uint32_t BlasterProjectileObjectId = 555;

bool hasStatusText(const std::optional<std::string> &text)
{
    return text.has_value() && !text->empty();
}

bool hasActiveLootView(const GameplayScreenRuntime &runtime)
{
    const IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    return pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
}

std::string heldItemDisplayName(const GameplayScreenRuntime &runtime)
{
    const GameplayUiController::HeldInventoryItemState &heldItem = runtime.heldInventoryItem();
    const ItemTable *pItemTable = runtime.itemTable();
    const ItemDefinition *pItemDefinition =
        pItemTable != nullptr ? pItemTable->get(heldItem.item.objectDescriptionId) : nullptr;

    return pItemDefinition != nullptr && !pItemDefinition->name.empty()
        ? pItemDefinition->name
        : "item";
}

bool dropHeldItemToActiveWorld(
    GameplayScreenRuntime &runtime,
    const std::optional<GameplayHeldItemDropRequest> &dropRequest)
{
    GameplayUiController::HeldInventoryItemState &heldItem = runtime.heldInventoryItem();

    if (!heldItem.active || !dropRequest)
    {
        return false;
    }

    const std::string itemName = heldItemDisplayName(runtime);
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        runtime.setStatusBarEvent("Can't drop " + itemName);
        return false;
    }

    GameplayHeldItemDropRequest resolvedDropRequest = *dropRequest;
    resolvedDropRequest.item = heldItem.item;

    if (!pWorldRuntime->dropHeldItemToWorld(resolvedDropRequest))
    {
        runtime.setStatusBarEvent("Can't drop " + itemName);
        return false;
    }

    runtime.setStatusBarEvent("Dropped " + itemName);
    GameplayHeldItemController::clearHeldInventoryItem(heldItem);
    return true;
}

void clearWorldHover(IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime != nullptr)
    {
        pWorldRuntime->clearWorldHover();
    }
}

void refreshWorldHover(
    const GameplayInteractionController::HoverStateInput &input,
    IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime != nullptr)
    {
        pWorldRuntime->refreshWorldHover(input.hoverRequest);
    }
}

uint32_t partyAttackRandomSeed()
{
    const std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
    return uint32_t(std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count());
}

GameplayActionController::WorldPoint toActionWorldPoint(const GameplayWorldPoint &point)
{
    return GameplayActionController::WorldPoint{
        .x = point.x,
        .y = point.y,
        .z = point.z,
    };
}

GameplaySpellActionController::TargetQueries buildSpellActionTargetQueries(
    GameplayScreenState &screenState,
    const GameplayInputFrame &input)
{
    const GameplayScreenState::GameplayMouseLookState &mouseLookState = screenState.gameplayMouseLookState();

    GameplaySpellActionController::TargetQueries targetQueries = {};
    targetQueries.useCrosshairTarget =
        mouseLookState.mouseLookActive
        && !mouseLookState.cursorModeActive
        && input.screenWidth > 0
        && input.screenHeight > 0;
    targetQueries.cursorX = input.pointerX;
    targetQueries.cursorY = input.pointerY;
    targetQueries.screenWidth = static_cast<float>(input.screenWidth);
    targetQueries.screenHeight = static_cast<float>(input.screenHeight);
    return targetQueries;
}

void executePartyAttack(
    GameplayScreenRuntime &runtime,
    GameplaySpellService &spellService,
    const GameplayPartyAttackFrameInput &partyAttackInput,
    const GameplayInteractionController::HoverStateInput &standardHoverInput,
    const GameplaySpellActionController::TargetQueries &targetQueries,
    const GameplayActionController::AttackActionDecision &decision,
    const GameplayWorldHit &currentHit)
{
    if (!partyAttackInput.enabled)
    {
        return;
    }

    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    Party *pParty = pWorldRuntime->party();

    if (pParty == nullptr)
    {
        return;
    }

    const std::optional<size_t> directActorIndex =
        currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? std::optional<size_t>(currentHit.actor->actorIndex)
            : std::nullopt;
    const std::string directTargetName =
        currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? currentHit.actor->displayName
            : "";

    GameplayActionController::executePartyAttack(
        GameplayActionController::PartyAttackConfig{
            .pRuntime = &runtime,
            .pSpellService = &spellService,
            .pWorldRuntime = pWorldRuntime,
            .pParty = pParty,
            .pItemTable = runtime.itemTable(),
            .pSpellTable = runtime.spellTable(),
            .pMonsterTable = runtime.monsterTable(),
            .pSpecialItemEnchantTable = runtime.specialItemEnchantTable(),
            .directTargetActorIndex = directActorIndex,
            .directTargetName = directTargetName,
            .partyPosition = toActionWorldPoint(partyAttackInput.partyPosition),
            .rangedSource = toActionWorldPoint(partyAttackInput.rangedSource),
            .defaultRangedTarget = toActionWorldPoint(partyAttackInput.defaultRangedTarget),
            .rayRangedTarget = toActionWorldPoint(partyAttackInput.rayRangedTarget),
            .hasRayRangedTarget = partyAttackInput.hasRayRangedTarget,
            .fallbackQuery = partyAttackInput.fallbackQuery,
            .worldInspectionRefreshRequest = standardHoverInput.hoverRequest,
            .randomSeed = partyAttackRandomSeed(),
            .arrowProjectileObjectId = ArrowProjectileObjectId,
            .blasterProjectileObjectId = BlasterProjectileObjectId,
            .pressedThisFrame = decision.pressedThisFrame,
            .targetQueries = targetQueries,
        });
}

void clearWorldInteractionFrameState(
    GameplayScreenState &screenState,
    GameplayOverlayInteractionState &overlayInteractionState,
    GameplayScreenRuntime &runtime)
{
    GameplayScreenState::PendingSpellTargetState &pendingSpellCast = screenState.pendingSpellTarget();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();
    GameplayScreenState::AttackActionState &attackActionState = screenState.attackActionState();
    GameplayScreenState::WorldInteractionInputState &worldInteractionInputState =
        screenState.worldInteractionInputState();

    worldInteractionInputState.keyboardUseLatch = false;
    worldInteractionInputState.inspectKeyboardActivateLatch = false;
    pendingSpellCast.clickLatch = false;
    worldInteractionInputState.heldInventoryDropLatch = false;
    overlayInteractionState.activateInspectLatch = false;
    worldInteractionInputState.inspectMouseActivateLatch = false;
    worldInteractionInputState.pressedWorldHit = {};
    attackActionState.clear();
    quickSpellState.clear();

    clearWorldHover(runtime.worldRuntime());
    runtime.mutableStatusBarHoverText().clear();
}
}

GameplayInteractionController::HoverStateResult GameplayInteractionController::updateHoverState(
    const HoverStateInput &input,
    IGameplayWorldRuntime *pWorldRuntime)
{
    HoverStateResult result = {};

    if (!input.allowHover)
    {
        if (pWorldRuntime != nullptr)
        {
            pWorldRuntime->clearWorldHover();
            result.cleared = true;
        }

        return result;
    }

    if (pWorldRuntime == nullptr)
    {
        return result;
    }

    const GameplayWorldHoverCacheState cacheState = pWorldRuntime->worldHoverCacheState();
    const bool shouldRefreshHover =
        !cacheState.hasCachedHover
        || input.currentTickNanoseconds < cacheState.lastUpdateNanoseconds
        || input.currentTickNanoseconds - cacheState.lastUpdateNanoseconds >= input.refreshIntervalNanoseconds;

    GameplayHoverStatusPayload payload = {};

    if (shouldRefreshHover)
    {
        payload = pWorldRuntime->refreshWorldHover(input.hoverRequest);
        result.refreshed = true;
    }
    else
    {
        payload = pWorldRuntime->readCachedWorldHover();
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
        const bool canActivate =
            input.pWorldRuntime != nullptr
            && input.pWorldRuntime->canActivateWorldHit(input.currentHit, input.interactionMethod);
        if (canActivate)
        {
            result.activated = input.pWorldRuntime->activateWorldHit(input.currentHit);
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

    const GameplayWorldHit &hit = input.pickedHit;
    result.picked = input.hasPickedHit;

    if (!hit.hasHit)
    {
        return result;
    }

    const bool canActivate =
        input.pWorldRuntime != nullptr
        && input.pWorldRuntime->canActivateWorldHit(hit, input.interactionMethod);
    if (canActivate)
    {
        result.activated = input.pWorldRuntime->activateWorldHit(hit);
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

    const bool canActivate =
        input.pWorldRuntime != nullptr
        && input.pWorldRuntime->canActivateWorldHit(input.currentHit, input.interactionMethod);
    if (canActivate)
    {
        result.activated = input.pWorldRuntime->activateWorldHit(input.currentHit);
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
        const GameplayWorldHit &hit = input.pickedHit;
        result.picked = input.hasPickedHit;

        if (hit.hasHit)
        {
            const bool canUseOnWorld =
                input.pWorldRuntime != nullptr
                && input.pWorldRuntime->canUseHeldItemOnWorld(hit);
            if (canUseOnWorld)
            {
                handledInteraction = input.pWorldRuntime->useHeldItemOnWorld(hit);
                result.usedOnWorld = handledInteraction;
            }
        }
    }

    if (!handledInteraction)
    {
        result.dropRequested = true;
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

GameplayInteractionController::WorldInteractionPointerPolicy
GameplayInteractionController::resolveWorldInteractionPointerPolicy(
    const WorldInteractionPointerPolicyInput &input)
{
    WorldInteractionPointerPolicy policy = {};
    policy.useCenterGameplayPoint = input.mouseLookActive && !input.cursorModeActive;
    policy.inspectScreenX =
        policy.useCenterGameplayPoint ? input.screenWidth * 0.5f : input.pointerX;
    policy.inspectScreenY =
        policy.useCenterGameplayPoint ? input.screenHeight * 0.5f : input.pointerY;
    policy.leftMousePressed =
        (input.pendingSpellActive || input.heldItemActive || !policy.useCenterGameplayPoint)
            && input.leftMousePressed;
    policy.pointerOverPartyPortrait =
        (input.pendingSpellActive || input.heldItemActive || !policy.useCenterGameplayPoint)
            && input.pointerOverPortrait;
    policy.activationPressed = input.keyboardActivationPressed && !input.rightMousePressed;
    policy.attackPressed =
        (input.keyboardAttackPressed && !input.rightMousePressed)
        || (policy.useCenterGameplayPoint && input.leftMousePressed && !input.rightMousePressed);
    return policy;
}

GameplayInteractionController::WorldInteractionFrameResult
GameplayInteractionController::updateWorldInteractionFrame(
    GameplayScreenState &screenState,
    GameplayOverlayInteractionState &overlayInteractionState,
    GameplayScreenRuntime &runtime,
    GameplaySpellService &spellService,
    const GameplayInputFrame &input,
    const GameplaySharedInputFrameResult &sharedInput,
    bool worldInputBlocked)
{
    WorldInteractionFrameResult result = {};
    GameplayScreenState::PendingSpellTargetState &pendingSpellCast = screenState.pendingSpellTarget();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();
    GameplayScreenState::AttackActionState &attackActionState = screenState.attackActionState();
    GameplayScreenState::WorldInteractionInputState &worldInteractionInputState =
        screenState.worldInteractionInputState();
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const bool heldItemActive = runtime.heldInventoryItem().active;
    const float screenWidth = static_cast<float>(input.screenWidth);
    const float screenHeight = static_cast<float>(input.screenHeight);
    const bool worldReady = pWorldRuntime != nullptr && pWorldRuntime->worldInteractionReady();
    const bool inspectModeActive = pWorldRuntime != nullptr && pWorldRuntime->worldInspectModeActive();
    const bool pendingSpellCancelPressed = input.isScancodeHeld(SDL_SCANCODE_ESCAPE);
    const bool keyboardUsePressed = input.action(KeyboardAction::Trigger).held;
    const bool activationPressed = input.isScancodeHeld(SDL_SCANCODE_E);
    const bool attackPressed = input.action(KeyboardAction::Attack).held;
    const bool leftMousePressed = input.leftMouseButton.held;
    const bool rightMousePressed = input.rightMouseButton.held;
    const bool mouseLookActive = sharedInput.mouseLookPolicy.mouseLookActive;
    const bool cursorModeActive = sharedInput.mouseLookPolicy.cursorModeActive;
    const std::optional<size_t> hoveredPortraitMemberIndex =
        runtime.resolvePartyPortraitIndexAtPoint(
            input.screenWidth,
            input.screenHeight,
            input.pointerX,
            input.pointerY);
    const Party *pParty = pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
    const bool hasReadyMember = pParty != nullptr && pParty->hasSelectableMemberInGameplay();
    const WorldInteractionPointerPolicy pointerPolicy =
        resolveWorldInteractionPointerPolicy(
            WorldInteractionPointerPolicyInput{
                .pendingSpellActive = pendingSpellCast.active,
                .heldItemActive = heldItemActive,
                .mouseLookActive = mouseLookActive,
                .cursorModeActive = cursorModeActive,
                .leftMousePressed = leftMousePressed,
                .rightMousePressed = rightMousePressed,
                .keyboardActivationPressed = activationPressed,
                .keyboardAttackPressed = attackPressed,
                .pointerX = input.pointerX,
                .pointerY = input.pointerY,
                .screenWidth = screenWidth,
                .screenHeight = screenHeight,
                .pointerOverPortrait = hoveredPortraitMemberIndex.has_value(),
            });
    const GameplaySpellActionController::TargetQueries targetQueries =
        buildSpellActionTargetQueries(screenState, input);

    const uint64_t currentTickNanoseconds = SDL_GetTicksNS();

    if (worldInputBlocked)
    {
        clearWorldInteractionFrameState(screenState, overlayInteractionState, runtime);
        result.blocked = true;
        return result;
    }

    if (pendingSpellCast.active)
    {
        GameplayWorldPickRequest pendingSpellPickRequest = {};
        GameplayWorldPickRequest centerHoverPickRequest = {};

        if (pWorldRuntime != nullptr)
        {
            pendingSpellPickRequest =
                pWorldRuntime->buildWorldPickRequest(
                    GameplayWorldPickRequestInput{
                        .screenX = input.pointerX,
                        .screenY = input.pointerY,
                        .screenWidth = input.screenWidth,
                        .screenHeight = input.screenHeight,
                    });
            centerHoverPickRequest =
                pWorldRuntime->buildWorldPickRequest(
                    GameplayWorldPickRequestInput{
                        .screenX = screenWidth * 0.5f,
                        .screenY = screenHeight * 0.5f,
                        .screenWidth = input.screenWidth,
                        .screenHeight = input.screenHeight,
                    });
        }

        HoverStateInput pendingSpellHoverInput = {};
        pendingSpellHoverInput.allowHover = !hoveredPortraitMemberIndex && worldReady;
        pendingSpellHoverInput.currentTickNanoseconds = currentTickNanoseconds;
        pendingSpellHoverInput.refreshIntervalNanoseconds = HoverInspectRefreshNanoseconds;
        pendingSpellHoverInput.hoverRequest =
            GameplayWorldHoverRequest{
                .probeKind = GameplayWorldHoverProbeKind::PendingSpell,
                .primaryPickRequest = pendingSpellPickRequest,
                .secondaryPickRequest = centerHoverPickRequest,
                .updateTickNanoseconds = currentTickNanoseconds,
            };

        GameplaySpellActionController::PendingTargetSelectionInput pendingTargetInput = {};
        pendingTargetInput.cancelPressed = false;

        updateHoverState(pendingSpellHoverInput, pWorldRuntime);

        if (targetQueries.screenWidth > 0.0f || targetQueries.screenHeight > 0.0f)
        {
            pendingTargetInput.targetQueries = targetQueries;
        }

        if (hoveredPortraitMemberIndex)
        {
            pendingTargetInput.portraitMemberIndex = hoveredPortraitMemberIndex;
        }

        if (pendingSpellCancelPressed)
        {
            pendingTargetInput.cancelPressed = true;
        }

        if (pointerPolicy.leftMousePressed && !pendingTargetInput.cancelPressed)
        {
            pendingTargetInput.confirmPressed = true;

            if (!pendingSpellCast.clickLatch
                && !hoveredPortraitMemberIndex
                && worldReady
                && pWorldRuntime != nullptr)
            {
                const GameplayPendingSpellWorldTargetFacts targetFacts =
                    pWorldRuntime->pickPendingSpellWorldTarget(pendingSpellPickRequest);
                pendingTargetInput.worldHit = targetFacts.worldHit;
                pendingTargetInput.fallbackGroundTargetPoint = targetFacts.fallbackGroundTargetPoint;
            }
        }

        const GameplaySpellActionController::PendingTargetSelectionResult pendingTargetResult =
            GameplaySpellActionController::updatePendingTargetSelection(
                screenState,
                runtime,
                spellService,
                pendingTargetInput);

        if (pendingTargetResult.castSucceeded)
        {
            IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

            if (pWorldRuntime != nullptr)
            {
                pWorldRuntime->applyPendingSpellCastWorldEffects(pendingTargetResult.castResult);
            }

            clearWorldHover(pWorldRuntime);
        }

        worldInteractionInputState.keyboardUseLatch = false;
        worldInteractionInputState.heldInventoryDropLatch = false;
        overlayInteractionState.activateInspectLatch = false;
        worldInteractionInputState.inspectKeyboardActivateLatch = false;
        worldInteractionInputState.inspectMouseActivateLatch = false;
        worldInteractionInputState.pressedWorldHit = {};
        attackActionState.inspectLatch = false;
        attackActionState.inspectRepeatCooldownSeconds = 0.0f;
        result.pendingSpellHandled = true;
        return result;
    }

    GameplayWorldHit keyboardUseHit = {};
    bool hasKeyboardUseHit = false;

    if (keyboardUsePressed
        && !worldInteractionInputState.keyboardUseLatch
        && worldReady
        && pWorldRuntime != nullptr)
    {
        const GameplayWorldPickRequest keyboardUsePickRequest =
            pWorldRuntime->buildWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = pointerPolicy.inspectScreenX,
                    .screenY = pointerPolicy.inspectScreenY,
                    .screenWidth = input.screenWidth,
                    .screenHeight = input.screenHeight,
                    .includeRay = true,
                });
        keyboardUseHit = pWorldRuntime->pickKeyboardInteractionTarget(keyboardUsePickRequest);
        hasKeyboardUseHit = true;
    }

    const KeyboardInteractionResult keyboardInteractionResult =
        updateKeyboardInteraction(
            worldInteractionInputState,
            KeyboardInteractionInput{
                .interactionPressed = keyboardUsePressed,
                .allowInteraction = worldReady,
                .pickedHit = keyboardUseHit,
                .hasPickedHit = hasKeyboardUseHit,
                .pWorldRuntime = pWorldRuntime,
                .interactionMethod = GameplayInteractionMethod::Keyboard,
            });

    if (keyboardInteractionResult.activated)
    {
        result.keyboardUseActivated = true;
        clearWorldHover(pWorldRuntime);
    }

    if (heldItemActive)
    {
        GameplayWorldHit heldItemWorldHit = {};
        bool hasHeldItemWorldHit = false;

        if (!pointerPolicy.leftMousePressed
            && worldInteractionInputState.heldInventoryDropLatch
            && !pointerPolicy.pointerOverPartyPortrait
            && worldReady
            && pWorldRuntime != nullptr)
        {
            const GameplayWorldPickRequest heldItemWorldPickRequest =
                pWorldRuntime->buildWorldPickRequest(
                    GameplayWorldPickRequestInput{
                        .screenX = input.pointerX,
                        .screenY = input.pointerY,
                        .screenWidth = input.screenWidth,
                        .screenHeight = input.screenHeight,
                        .includeRay = true,
                    });
            heldItemWorldHit = pWorldRuntime->pickHeldItemWorldTarget(heldItemWorldPickRequest);
            hasHeldItemWorldHit = true;
        }

        const HeldItemWorldInteractionResult heldItemWorldInteractionResult =
            updateHeldItemWorldInteraction(
                worldInteractionInputState,
                HeldItemWorldInteractionInput{
                    .heldItemActive = heldItemActive,
                    .leftMousePressed = pointerPolicy.leftMousePressed,
                    .pointerOverPartyPortrait = pointerPolicy.pointerOverPartyPortrait,
                    .pickedHit = heldItemWorldHit,
                    .hasPickedHit = hasHeldItemWorldHit,
                    .pWorldRuntime = pWorldRuntime,
                });

        if (heldItemWorldInteractionResult.dropRequested)
        {
            const std::optional<GameplayHeldItemDropRequest> heldItemDropRequest =
                pWorldRuntime != nullptr ? pWorldRuntime->buildHeldItemDropRequest() : std::nullopt;
            dropHeldItemToActiveWorld(runtime, heldItemDropRequest);
        }

        result.heldItemHandled = true;
        return result;
    }

    if (!inspectModeActive || !worldReady)
    {
        clearWorldInteractionFrameState(screenState, overlayInteractionState, runtime);
        return result;
    }

    GameplayWorldPickRequest currentInteractionPickRequest = {};

    if (pWorldRuntime != nullptr)
    {
        currentInteractionPickRequest =
            pWorldRuntime->buildWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = pointerPolicy.inspectScreenX,
                    .screenY = pointerPolicy.inspectScreenY,
                    .screenWidth = input.screenWidth,
                    .screenHeight = input.screenHeight,
                    .includeRay = true,
                });
    }

    HoverStateInput standardHoverInput = {};
    standardHoverInput.allowHover = inspectModeActive && worldReady;
    standardHoverInput.currentTickNanoseconds = currentTickNanoseconds;
    standardHoverInput.refreshIntervalNanoseconds = HoverInspectRefreshNanoseconds;
    standardHoverInput.hoverRequest =
        GameplayWorldHoverRequest{
            .probeKind = GameplayWorldHoverProbeKind::Standard,
            .primaryPickRequest = currentInteractionPickRequest,
            .updateTickNanoseconds = currentTickNanoseconds,
        };

    result.hover = updateHoverState(standardHoverInput, pWorldRuntime);

    GameplayWorldHit currentHit = {};
    bool currentHitRefreshed = false;
    const auto pickCurrentHit =
        [&]() -> GameplayWorldHit
        {
            if (!currentHitRefreshed && worldReady && pWorldRuntime != nullptr)
            {
                currentHit = pWorldRuntime->pickMouseInteractionTarget(currentInteractionPickRequest);
                currentHitRefreshed = true;
            }

            return currentHit;
        };

    if (pointerPolicy.activationPressed
        || pointerPolicy.attackPressed
        || pointerPolicy.leftMousePressed
        || worldInteractionInputState.inspectMouseActivateLatch)
    {
        pickCurrentHit();
    }

    const bool hadLootViewBeforeActivation = hasActiveLootView(runtime);

    const KeyboardActivationInteractionResult keyboardActivationResult =
        updateKeyboardActivationInteraction(
            worldInteractionInputState,
            KeyboardActivationInteractionInput{
                .activationPressed = pointerPolicy.activationPressed,
                .allowInteraction = worldReady,
                .currentHit = currentHit,
                .pWorldRuntime = pWorldRuntime,
                .interactionMethod = GameplayInteractionMethod::Mouse,
            });

    if (keyboardActivationResult.latched)
    {
        overlayInteractionState.activateInspectLatch = true;
    }
    else if (!pointerPolicy.activationPressed)
    {
        overlayInteractionState.activateInspectLatch = false;
    }

    if (keyboardActivationResult.activated)
    {
        result.keyboardActivationActivated = true;
        refreshWorldHover(standardHoverInput, pWorldRuntime);

        const bool hasLootViewAfterActivation = hasActiveLootView(runtime);

        if (!hadLootViewBeforeActivation && hasLootViewAfterActivation)
        {
            overlayInteractionState.lootChestItemLatch = true;
        }
    }

    const MouseClickInteractionResult mouseInteractionResult =
        updateMouseClickInteraction(
            worldInteractionInputState,
            MouseClickInteractionInput{
                .leftMousePressed = pointerPolicy.leftMousePressed,
                .pointerOverPartyPortrait = pointerPolicy.pointerOverPartyPortrait,
                .currentHit = currentHit,
                .pWorldRuntime = pWorldRuntime,
                .interactionMethod = GameplayInteractionMethod::Mouse,
            });

    if (mouseInteractionResult.activated)
    {
        result.mouseActivationActivated = true;
        refreshWorldHover(standardHoverInput, pWorldRuntime);
    }

    const GameplayActionController::AttackActionDecision attackActionDecision =
        GameplayActionController::updateAttackAction(
            attackActionState,
            quickSpellState,
            GameplayActionController::AttackActionConfig{
                .attackPressed = pointerPolicy.attackPressed,
                .hasReadyMember = hasReadyMember,
            });

    if (attackActionDecision.shouldAttemptAttack)
    {
        pickCurrentHit();
        const GameplayPartyAttackFrameInput partyAttackInput =
            pWorldRuntime != nullptr
            ? pWorldRuntime->buildPartyAttackFrameInput(currentInteractionPickRequest)
            : GameplayPartyAttackFrameInput{};
        result.attackAttempted = true;
        executePartyAttack(
            runtime,
            spellService,
            partyAttackInput,
            standardHoverInput,
            targetQueries,
            attackActionDecision,
            currentHit);
    }

    runtime.mutableStatusBarHoverText() = result.hover.statusText;

    return result;
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
