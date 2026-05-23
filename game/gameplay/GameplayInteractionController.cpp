#include "game/gameplay/GameplayInteractionController.h"

#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GameplayWorldItemInteraction.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/party/SpellIds.h"
#include "game/tables/ItemTable.h"

#include <SDL3/SDL_timer.h>

#include <algorithm>
#include <chrono>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr float NearHoverStatusDistance = 1024.0f;
constexpr float ActorHoverStatusDistance = 8192.0f;
constexpr uint64_t HoverInspectRefreshNanoseconds = 33 * 1000 * 1000;
constexpr uint64_t ContextActionRefreshNanoseconds = 250 * 1000 * 1000;
constexpr uint64_t ContextActionIdleRetryNanoseconds = 1000 * 1000 * 1000;
constexpr uint64_t KeyboardInteractionFirstRepeatNanoseconds = 500 * 1000 * 1000;
constexpr uint64_t KeyboardInteractionRepeatNanoseconds = 67 * 1000 * 1000;
constexpr float ContextActionRayOriginChangeThresholdSquared = 4.0f;
constexpr float ContextActionRayDirectionChangeThresholdSquared = 0.000001f;
constexpr uint32_t ArrowProjectileObjectId = 545;
constexpr uint32_t BlasterProjectileObjectId = 555;

#if defined(__ANDROID__)
bool usesMobileGroundTargetConfirm(uint32_t spellId)
{
    return isSpellId(spellId, SpellId::MeteorShower)
        || isSpellId(spellId, SpellId::Starburst);
}
#endif

bool hasStatusText(const std::optional<std::string> &text)
{
    return text.has_value() && !text->empty();
}

float arpgModeInteractionDepth(const GameplayScreenRuntime &runtime)
{
    return static_cast<float>(std::clamp(runtime.settingsSnapshot().keyboardInteractionDepth, 32, 4096));
}

GameplayWorldHit pickArpgModePopupInteractionTarget(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayScreenRuntime &runtime)
{
    return worldRuntime.pickNearbyInteractionTarget(arpgModeInteractionDepth(runtime));
}

GameplayWorldHit pickArpgModeForwardInteractionTarget(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayScreenRuntime &runtime)
{
    return worldRuntime.pickForwardInteractionTarget(arpgModeInteractionDepth(runtime));
}

GameplayWorldHit pickPrecisionContextActionTarget(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldPickRequest &request)
{
    GameplayWorldHit hit = worldRuntime.pickMouseInteractionTarget(request);

    if (worldRuntime.canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard))
    {
        return hit;
    }

    hit = worldRuntime.pickKeyboardInteractionTarget(request);

    if (worldRuntime.canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard))
    {
        return hit;
    }

    return {};
}

GameplayWorldHit pickArpgModePrecisionInteractionTarget(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldPickRequest &request)
{
    return pickPrecisionContextActionTarget(worldRuntime, request);
}

bool hasActiveLootView(const GameplayScreenRuntime &runtime)
{
    const IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    return pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
}

float vecDeltaSquared(const bx::Vec3 &left, const bx::Vec3 &right)
{
    const float deltaX = left.x - right.x;
    const float deltaY = left.y - right.y;
    const float deltaZ = left.z - right.z;

    return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
}

bool contextActionPickRayChanged(
    const GameplayContextActionState &state,
    const GameplayWorldPickRequest &request)
{
    if (!request.hasRay || !state.hasLastUpdateRay)
    {
        return request.hasRay != state.hasLastUpdateRay;
    }

    return vecDeltaSquared(request.rayOrigin, state.lastUpdateRayOrigin)
            >= ContextActionRayOriginChangeThresholdSquared
        || vecDeltaSquared(request.rayDirection, state.lastUpdateRayDirection)
            >= ContextActionRayDirectionChangeThresholdSquared;
}

const char *contextActionIconId(GameplayContextActionKind kind)
{
    switch (kind)
    {
    case GameplayContextActionKind::Talk:
        return "context_talk";
    case GameplayContextActionKind::PickUpItem:
        return "context_pickup_item";
    case GameplayContextActionKind::LootCorpse:
        return "context_loot_corpse";
    case GameplayContextActionKind::OpenChest:
        return "context_open_chest";
    case GameplayContextActionKind::EnterHouse:
        return "context_enter_house";
    case GameplayContextActionKind::OpenDoor:
        return "context_open_door";
    case GameplayContextActionKind::PressButton:
        return "context_press_button";
    case GameplayContextActionKind::UseLever:
        return "context_use_lever";
    case GameplayContextActionKind::GenericEvent:
        return "context_generic_event";
    case GameplayContextActionKind::None:
        break;
    }

    return "context_generic_event";
}

const char *contextActionDefaultLabel(GameplayContextActionKind kind)
{
    switch (kind)
    {
    case GameplayContextActionKind::Talk:
        return "Talk";
    case GameplayContextActionKind::PickUpItem:
        return "Pick Up";
    case GameplayContextActionKind::LootCorpse:
        return "Loot";
    case GameplayContextActionKind::OpenChest:
        return "Open Chest";
    case GameplayContextActionKind::EnterHouse:
        return "Enter";
    case GameplayContextActionKind::OpenDoor:
        return "Open Door";
    case GameplayContextActionKind::PressButton:
        return "Press";
    case GameplayContextActionKind::UseLever:
        return "Use Lever";
    case GameplayContextActionKind::GenericEvent:
        return "";
    case GameplayContextActionKind::None:
        break;
    }

    return "Use";
}

GameplayContextActionKind contextActionKindFromMetadataKind(const std::string &kind)
{
    if (kind == "open_chest")
    {
        return GameplayContextActionKind::OpenChest;
    }

    if (kind == "enter_house" || kind == "enter_dungeon" || kind == "leave_dungeon"
        || kind == "passage" || kind == "travel" || kind == "teleport")
    {
        return GameplayContextActionKind::EnterHouse;
    }

    if (kind == "open_door")
    {
        return GameplayContextActionKind::OpenDoor;
    }

    if (kind == "press_button")
    {
        return GameplayContextActionKind::PressButton;
    }

    if (kind == "use_lever" || kind == "use_switch" || kind == "use_elevator" || kind == "use_pedestal")
    {
        return GameplayContextActionKind::UseLever;
    }

    return GameplayContextActionKind::GenericEvent;
}

std::string contextActionIconIdFromMetadataKind(const std::string &kind, GameplayContextActionKind fallbackKind)
{
    if (kind.empty())
    {
        return contextActionIconId(fallbackKind);
    }

    return "context_" + kind;
}

std::string contextActionDefaultLabelFromMetadata(
    const GameplayEventTargetContextActionMetadata &metadata,
    GameplayContextActionKind actionKind)
{
    if (metadata.targetName && !metadata.targetName->empty())
    {
        return *metadata.targetName;
    }

    if (metadata.kind == "leave_dungeon")
    {
        return "Exit";
    }

    if (metadata.kind == "travel")
    {
        return "Travel";
    }

    if (metadata.kind == "passage")
    {
        return "Passage";
    }

    if (metadata.kind == "teleport")
    {
        return "Teleport";
    }

    if (metadata.kind == "use_switch")
    {
        return "Use Switch";
    }

    if (metadata.kind == "use_elevator")
    {
        return "Use Elevator";
    }

    if (metadata.kind == "use_pedestal")
    {
        return "Use Pedestal";
    }

    if (metadata.kind == "fountain")
    {
        return "Fountain";
    }

    if (metadata.kind == "well")
    {
        return "Well";
    }

    if (metadata.kind == "shrine")
    {
        return "Shrine";
    }

    if (metadata.kind == "obelisk")
    {
        return "Obelisk";
    }

    if (metadata.kind == "boost")
    {
        return "Boost";
    }

    if (metadata.kind == "read")
    {
        return "Read";
    }

    if (metadata.kind == "secret_event")
    {
        return "???";
    }

    if (metadata.kind == "generic_event")
    {
        return "";
    }

    return contextActionDefaultLabel(actionKind);
}

std::string contextActionLabelWithName(const char *pVerb, const std::string &name)
{
    if (name.empty())
    {
        return pVerb != nullptr ? pVerb : "";
    }

    return std::string(pVerb != nullptr ? pVerb : "") + " (" + name + ")";
}

GameplayContextActionKind classifyEventTargetContextAction(const GameplayWorldHit &hit)
{
    if (!hit.eventTarget)
    {
        return GameplayContextActionKind::GenericEvent;
    }

    if (hit.eventTarget->contextActionMetadata)
    {
        return contextActionKindFromMetadataKind(hit.eventTarget->contextActionMetadata->kind);
    }

    if (!hit.eventTarget->openedChestIds.empty())
    {
        return GameplayContextActionKind::OpenChest;
    }

    if (hit.eventTarget->targetKind == GameplayWorldEventTargetKind::Mechanism)
    {
        return GameplayContextActionKind::UseLever;
    }

    return GameplayContextActionKind::GenericEvent;
}

std::optional<GameplayContextAction> buildContextAction(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldHit &hit,
    const std::optional<std::string> &eventTargetStatusText)
{
    if (!hit.hasHit || !worldRuntime.canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard))
    {
        return std::nullopt;
    }

    GameplayContextAction action = {};
    action.worldHit = hit;

    if (hit.kind == GameplayWorldHitKind::Actor && hit.actor)
    {
        GameplayRuntimeActorState actorState = {};
        const bool hasActorState = worldRuntime.actorRuntimeState(hit.actor->actorIndex, actorState);
        action.kind = hasActorState && actorState.isDead
            ? GameplayContextActionKind::LootCorpse
            : GameplayContextActionKind::Talk;
        if (action.kind == GameplayContextActionKind::Talk)
        {
            action.label = !hit.actor->displayName.empty()
                ? hit.actor->displayName
                : contextActionDefaultLabel(action.kind);
        }
        else
        {
            action.label = contextActionLabelWithName(contextActionDefaultLabel(action.kind), hit.actor->displayName);
        }
    }
    else if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        action.kind = GameplayContextActionKind::PickUpItem;
        action.label =
            contextActionLabelWithName("Pick", hit.worldItem->displayName);
    }
    else if (hit.kind == GameplayWorldHitKind::Chest && hit.container)
    {
        action.kind = GameplayContextActionKind::OpenChest;
        action.label = contextActionDefaultLabel(action.kind);
    }
    else if (hit.kind == GameplayWorldHitKind::Corpse && hit.container)
    {
        action.kind = GameplayContextActionKind::LootCorpse;
        action.label =
            contextActionLabelWithName(contextActionDefaultLabel(action.kind), hit.container->displayName);
    }
    else if (hit.kind == GameplayWorldHitKind::EventTarget && hit.eventTarget)
    {
        if (hit.eventTarget->hintOnlyEvent)
        {
            return std::nullopt;
        }

        action.kind = classifyEventTargetContextAction(hit);
        if (hit.eventTarget->contextActionMetadata)
        {
            const GameplayEventTargetContextActionMetadata &metadata = *hit.eventTarget->contextActionMetadata;
            action.label = contextActionDefaultLabelFromMetadata(metadata, action.kind);
            action.iconId = contextActionIconIdFromMetadataKind(metadata.kind, action.kind);
        }
        else
        {
            action.label = hasStatusText(eventTargetStatusText)
                ? *eventTargetStatusText
                : (!hit.eventTarget->name.empty()
                    ? hit.eventTarget->name
                    : contextActionDefaultLabel(action.kind));
        }
    }
    else
    {
        return std::nullopt;
    }

    if (action.iconId.empty())
    {
        action.iconId = contextActionIconId(action.kind);
    }
    return action;
}

void setSingleContextAction(
    GameplayScreenRuntime &runtime,
    const std::optional<GameplayContextAction> &action,
    uint64_t updateTickNanoseconds,
    const GameplayWorldPickRequest &pickRequest)
{
    GameplayContextActionState &state = runtime.contextActionState();
    state = {};
    state.lastUpdateNanoseconds = updateTickNanoseconds;
    state.hasLastUpdateRay = pickRequest.hasRay;

    if (pickRequest.hasRay)
    {
        state.lastUpdateRayOrigin = pickRequest.rayOrigin;
        state.lastUpdateRayDirection = pickRequest.rayDirection;
    }

    if (!action)
    {
        return;
    }

    state.visible = true;
    state.actions.push_back(*action);
    state.primaryIndex = 0;
}

std::string formatFoundItemStatusText(const std::string &itemName)
{
    const std::string resolvedItemName = itemName.empty() ? "item" : itemName;
    return "You found an item (" + resolvedItemName + ")!";
}

std::string formatFoundGoldStatusText(int goldAmount)
{
    return "You found " + std::to_string(std::max(0, goldAmount)) + " gold!";
}

int followerAdjustedGoldAmount(int goldAmount, const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState == nullptr || goldAmount <= 0)
    {
        return std::max(0, goldAmount);
    }

    return static_cast<int>(hiredNpcGoldAfterBonusAndFees(static_cast<uint32_t>(goldAmount), *pEventRuntimeState));
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
    if (Party *pParty = runtime.party())
    {
        pParty->clearHeldItemForQueries();
    }
    return true;
}

std::string worldItemDisplayName(
    const GameplayWorldItemInspectState &worldItemState,
    const ItemTable *pItemTable)
{
    const ItemDefinition *pItemDefinition =
        pItemTable != nullptr ? pItemTable->get(worldItemState.item.objectDescriptionId) : nullptr;

    return pItemDefinition != nullptr && !pItemDefinition->name.empty()
        ? pItemDefinition->name
        : "item";
}

bool canStoreWorldItemInInventory(
    Party &party,
    const InventoryItem &item,
    size_t &recipientMemberIndex)
{
    const Party::Snapshot snapshot = party.snapshot();
    const ScopedGameplayDebugTraceSuppression traceSuppression;
    const bool canStore = party.tryGrantInventoryItem(item, &recipientMemberIndex);
    party.restoreSnapshot(snapshot);
    return canStore;
}

void recordWorldItemActivationResult(
    IGameplayWorldRuntime &worldRuntime,
    const std::string &result)
{
    EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->lastActivationResult = result;
    }
}

std::string gameplayTraceWorldContext(const IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime == nullptr)
    {
        return {};
    }

    std::ostringstream out;
    out << " map=\"" << pWorldRuntime->mapName() << "\""
        << " scene_kind=" << (pWorldRuntime->isIndoorMap() ? "indoor" : "outdoor")
        << " party=(" << pWorldRuntime->partyX()
        << "," << pWorldRuntime->partyY()
        << "," << pWorldRuntime->partyFootZ() << ")"
        << " yaw=" << pWorldRuntime->gameplayCameraYawRadians()
        << " pitch=" << pWorldRuntime->gameplayCameraPitchRadians();
    return out.str();
}

bool tryActivateWorldItem(
    GameplayScreenRuntime &runtime,
    IGameplayWorldRuntime &worldRuntime,
    size_t worldItemIndex)
{
    Party *pParty = runtime.party();

    if (pParty == nullptr)
    {
        return false;
    }

    GameplayWorldItemInspectState worldItemState = {};

    if (!worldRuntime.worldItemInspectState(worldItemIndex, worldItemState))
    {
        return false;
    }

    GameplayUiController::HeldInventoryItemState &heldItem = runtime.heldInventoryItem();
    size_t recipientMemberIndex = 0;
    const bool canStoreInInventory =
        !worldItemState.isGold
        && canStoreWorldItemInInventory(*pParty, worldItemState.item, recipientMemberIndex);
    const GameplayWorldItemPickupDecision pickupDecision =
        GameplayWorldItemInteraction::decidePickupDestination(
            GameplayWorldItemPickupDecisionInput{
                .isGold = worldItemState.isGold,
                .goldAmount = worldItemState.goldAmount,
                .canStoreInInventory = canStoreInInventory,
                .heldItemActive = heldItem.active,
            });

    if (pickupDecision.destination == GameplayWorldItemPickupDestination::None)
    {
        if (!worldItemState.isGold && !canStoreInInventory && heldItem.active)
        {
            runtime.setStatusBarEvent("Pack is Full!");
            runtime.playSpeechReaction(pParty->activeMemberIndex(), SpeechId::InventoryRoom, true);
        }

        return false;
    }

    GameplayWorldItemInspectState removedItemState = {};

    if (!worldRuntime.takeWorldItemInspectState(worldItemIndex, removedItemState))
    {
        return false;
    }

    if (pickupDecision.destination == GameplayWorldItemPickupDestination::Gold)
    {
        const int goldAmount = followerAdjustedGoldAmount(
            pickupDecision.goldAmount,
            worldRuntime.eventRuntimeState());
        pParty->addGold(goldAmount);
        pParty->requestSound(SoundId::Gold);
        const std::string statusText = formatFoundGoldStatusText(goldAmount);
        runtime.setStatusBarEvent(statusText);
        recordWorldItemActivationResult(
            worldRuntime,
            "picked up " + std::to_string(goldAmount) + " gold");
        return true;
    }

    const std::string itemName = worldItemDisplayName(removedItemState, runtime.itemTable());

    if (pickupDecision.destination == GameplayWorldItemPickupDestination::Inventory)
    {
        if (!pParty->tryGrantInventoryItem(removedItemState.item, &recipientMemberIndex))
        {
            return false;
        }

        GAMEPLAY_DEBUG_TRACE(
            "item_received destination=inventory source=world_item item_id="
            + std::to_string(removedItemState.item.objectDescriptionId)
            + gameplayDebugTraceItemSummary(removedItemState.item.objectDescriptionId, runtime.itemTable())
            + " world_item_index=" + std::to_string(worldItemIndex)
            + " member_index=" + std::to_string(recipientMemberIndex));
        pParty->requestSound(SoundId::Gold);
        runtime.playSpeechReaction(recipientMemberIndex, SpeechId::FoundItem, true);
        runtime.setStatusBarEvent(formatFoundItemStatusText(itemName));
        recordWorldItemActivationResult(worldRuntime, "picked up " + itemName);
        return true;
    }

    GameplayHeldItemController::setHeldInventoryItem(heldItem, removedItemState.item);
    pParty->setHeldItemForQueries(removedItemState.item);
    GAMEPLAY_DEBUG_TRACE(
        "item_received destination=held source=world_item item_id="
        + std::to_string(removedItemState.item.objectDescriptionId)
        + gameplayDebugTraceItemSummary(removedItemState.item.objectDescriptionId, runtime.itemTable())
        + " world_item_index=" + std::to_string(worldItemIndex));
    pParty->requestSound(SoundId::Gold);
    runtime.playSpeechReaction(pParty->activeMemberIndex(), SpeechId::FoundItem, true);
    runtime.setStatusBarEvent(formatFoundItemStatusText(itemName));
    recordWorldItemActivationResult(worldRuntime, "picked up " + itemName + " into hand");
    return true;
}

bool tryActivateWorldHit(
    GameplayScreenRuntime *pRuntime,
    IGameplayWorldRuntime *pWorldRuntime,
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod)
{
    if (pWorldRuntime == nullptr || !pWorldRuntime->canActivateWorldHit(hit, interactionMethod))
    {
        GAMEPLAY_DEBUG_TRACE(
            "interact method="
            + std::string(interactionMethod == GameplayInteractionMethod::Keyboard ? "keyboard" : "mouse")
            + gameplayTraceWorldContext(pWorldRuntime)
            + " can_activate=false "
            + gameplayDebugTraceWorldHitSummary(hit));
        return false;
    }

    GAMEPLAY_DEBUG_TRACE(
        "interact method="
        + std::string(interactionMethod == GameplayInteractionMethod::Keyboard ? "keyboard" : "mouse")
        + gameplayTraceWorldContext(pWorldRuntime)
        + " can_activate=true "
        + gameplayDebugTraceWorldHitSummary(hit));

    if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        return pRuntime != nullptr
            && tryActivateWorldItem(*pRuntime, *pWorldRuntime, hit.worldItem->worldItemIndex);
    }

    return pWorldRuntime->activateWorldHit(hit);
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

uint32_t interactionRandomSeed(uint32_t salt)
{
    const std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
    const uint64_t ticks = static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(now.time_since_epoch()).count());
    return static_cast<uint32_t>((ticks >> 32u) ^ ticks ^ salt);
}

GameplayActionController::WorldPoint toActionWorldPoint(const GameplayWorldPoint &point)
{
    return GameplayActionController::WorldPoint{
        .x = point.x,
        .y = point.y,
        .z = point.z,
    };
}

std::optional<GameplayActionController::WorldPoint> partyRangedTargetFromWorldHit(const GameplayWorldHit &hit)
{
    if (!hit.hasHit)
    {
        return std::nullopt;
    }

    switch (hit.kind)
    {
        case GameplayWorldHitKind::WorldItem:
            if (hit.worldItem)
            {
                return GameplayActionController::WorldPoint{
                    .x = hit.worldItem->hitPoint.x,
                    .y = hit.worldItem->hitPoint.y,
                    .z = hit.worldItem->hitPoint.z,
                };
            }
            break;
        case GameplayWorldHitKind::EventTarget:
            if (hit.eventTarget)
            {
                return GameplayActionController::WorldPoint{
                    .x = hit.eventTarget->hitPoint.x,
                    .y = hit.eventTarget->hitPoint.y,
                    .z = hit.eventTarget->hitPoint.z,
                };
            }
            break;
        case GameplayWorldHitKind::Object:
            if (hit.object)
            {
                return GameplayActionController::WorldPoint{
                    .x = hit.object->hitPoint.x,
                    .y = hit.object->hitPoint.y,
                    .z = hit.object->hitPoint.z,
                };
            }
            break;
        case GameplayWorldHitKind::Ground:
            if (hit.ground && hit.ground->isValid)
            {
                return GameplayActionController::WorldPoint{
                    .x = hit.ground->worldPoint.x,
                    .y = hit.ground->worldPoint.y,
                    .z = hit.ground->worldPoint.z,
                };
            }
            break;
        case GameplayWorldHitKind::Actor:
        case GameplayWorldHitKind::Chest:
        case GameplayWorldHitKind::Corpse:
        case GameplayWorldHitKind::None:
        default:
            break;
    }

    return std::nullopt;
}

std::optional<GameplayActionController::WorldPoint> arpgModeOutdoorActorRangedTargetFromWorldHit(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldHit &hit)
{
    if (worldRuntime.isIndoorMap()
        || hit.kind != GameplayWorldHitKind::Actor
        || !hit.actor)
    {
        return std::nullopt;
    }

    const std::optional<bx::Vec3> actorTargetPoint =
        worldRuntime.spellActionActorTargetPoint(hit.actor->actorIndex);
    const bx::Vec3 targetPoint = actorTargetPoint.value_or(hit.actor->hitPoint);

    return GameplayActionController::WorldPoint{
        .x = targetPoint.x,
        .y = targetPoint.y,
        .z = targetPoint.z,
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

    TurnBasedCombatRuntime &turnBasedCombatRuntime = runtime.turnBasedCombatRuntime();
    if (turnBasedCombatRuntime.active())
    {
        if (turnBasedCombatRuntime.stage() == TurnBasedCombatStage::Movement)
        {
            turnBasedCombatRuntime.finishMovementPhase();
            GAMEPLAY_DEBUG_TRACE("turn_based_attack_finished_movement stage=movement");
            return;
        }

        if (!turnBasedCombatRuntime.canBeginPlayerAction(*pParty))
        {
            return;
        }
    }

    const bool arpgMode = runtime.settingsSnapshot().arpgModeEnabled;
    const std::optional<size_t> directActorIndex =
        !arpgMode && currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? std::optional<size_t>(currentHit.actor->actorIndex)
            : std::nullopt;
    const std::string directTargetName =
        !arpgMode && currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? currentHit.actor->displayName
            : "";
    const std::optional<GameplayActionController::WorldPoint> hitRangedTarget =
        arpgMode
            ? arpgModeOutdoorActorRangedTargetFromWorldHit(*pWorldRuntime, currentHit)
            : partyRangedTargetFromWorldHit(currentHit);

    const GameplayActionController::PartyAttackExecutionResult attackResult =
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
            .rangedRight = toActionWorldPoint(partyAttackInput.rangedRight),
            .defaultRangedTarget = toActionWorldPoint(partyAttackInput.defaultRangedTarget),
            .rayRangedTarget = hitRangedTarget.value_or(toActionWorldPoint(partyAttackInput.rayRangedTarget)),
            .hasRayRangedTarget = hitRangedTarget.has_value() || partyAttackInput.hasRayRangedTarget,
            .fallbackQuery = partyAttackInput.fallbackQuery,
            .worldInspectionRefreshRequest = standardHoverInput.hoverRequest,
            .randomSeed = partyAttackRandomSeed(),
            .arrowProjectileObjectId = ArrowProjectileObjectId,
            .blasterProjectileObjectId = BlasterProjectileObjectId,
            .pressedThisFrame = decision.pressedThisFrame,
            .targetQueries = targetQueries,
        });

    if (turnBasedCombatRuntime.active() && attackResult.actionPerformed)
    {
        turnBasedCombatRuntime.applyPlayerAction(
            *pParty,
            attackResult.actingMemberIndex,
            attackResult.appliedRecoverySeconds);
    }
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
    worldInteractionInputState.arpgContextActionTriggerLatch = false;
    worldInteractionInputState.inspectKeyboardActivateLatch = false;
    worldInteractionInputState.keyboardUseNextRepeatTickNanoseconds = 0;
    worldInteractionInputState.inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
    pendingSpellCast.clickLatch = false;
    worldInteractionInputState.heldInventoryDropLatch = false;
    overlayInteractionState.activateInspectLatch = false;
    worldInteractionInputState.inspectMouseActivateLatch = false;
    worldInteractionInputState.pressedWorldHit = {};
    attackActionState.clear();
    quickSpellState.clear();

    clearWorldHover(runtime.worldRuntime());
    runtime.clearStatusBarHoverText();
    runtime.clearContextActionState();
}

bool keyboardRepeatInteractionDue(
    bool &latched,
    uint64_t &nextRepeatTickNanoseconds,
    uint64_t currentTickNanoseconds)
{
    if (!latched)
    {
        latched = true;
        nextRepeatTickNanoseconds = currentTickNanoseconds + KeyboardInteractionFirstRepeatNanoseconds;
        return true;
    }

    if (nextRepeatTickNanoseconds == 0
        || currentTickNanoseconds < nextRepeatTickNanoseconds)
    {
        return false;
    }

    nextRepeatTickNanoseconds = currentTickNanoseconds + KeyboardInteractionRepeatNanoseconds;
    return true;
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
    result.worldHit = payload.worldHit;
    result.eventTargetStatusText = payload.eventTargetStatusText;
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
            tryActivateWorldHit(
                input.pRuntime,
                input.pWorldRuntime,
                input.currentHit,
                input.interactionMethod);
        if (canActivate)
        {
            result.activated = true;
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
        state.keyboardUseNextRepeatTickNanoseconds = 0;
        return result;
    }

    if (!input.allowInteraction)
    {
        return result;
    }

    if (!keyboardRepeatInteractionDue(
        state.keyboardUseLatch,
        state.keyboardUseNextRepeatTickNanoseconds,
        input.currentTickNanoseconds))
    {
        return result;
    }

    result.latched = true;

    const GameplayWorldHit &hit = input.pickedHit;
    result.picked = input.hasPickedHit;

    if (!hit.hasHit)
    {
        return result;
    }

    const bool canActivate =
        tryActivateWorldHit(
            input.pRuntime,
            input.pWorldRuntime,
            hit,
            input.interactionMethod);
    if (canActivate)
    {
        result.activated = true;
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
        state.inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
        return result;
    }

    if (!input.allowInteraction)
    {
        return result;
    }

    const bool firstActivationPress = !state.inspectKeyboardActivateLatch;

    if (!keyboardRepeatInteractionDue(
        state.inspectKeyboardActivateLatch,
        state.inspectKeyboardActivateNextRepeatTickNanoseconds,
        input.currentTickNanoseconds))
    {
        return result;
    }

    result.latched = true;

    if (input.activateArpgLootPopupFirst
        && firstActivationPress
        && input.pWorldRuntime != nullptr
        && input.pWorldRuntime->tryActivateArpgModeLootPopup())
    {
        result.activated = true;
        return result;
    }

    if (!input.currentHit.hasHit)
    {
        return result;
    }

    const bool canActivate =
        tryActivateWorldHit(
            input.pRuntime,
            input.pWorldRuntime,
            input.currentHit,
            input.interactionMethod);
    if (canActivate)
    {
        result.activated = true;
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

        if (hit.hasHit && hit.kind != GameplayWorldHitKind::WorldItem)
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
        || targetKind == GameplayWorldEventTargetKind::Entity
        || targetKind == GameplayWorldEventTargetKind::Mechanism;

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

    if (input.arpgMode)
    {
        policy.useCenterGameplayPoint = false;
        policy.inspectScreenX = input.pointerX;
        policy.inspectScreenY = input.pointerY;
        policy.leftMousePressed = input.leftMousePressed;
        policy.pointerOverPartyPortrait = input.pointerOverPortrait;
        policy.activationPressed = input.keyboardActivationPressed && !input.rightMousePressed;
        policy.attackPressed = input.rightMousePressed;
        return policy;
    }

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
#if !defined(__ANDROID__)
        || (policy.useCenterGameplayPoint && input.leftMousePressed && !input.rightMousePressed);
#else
        ;
#endif
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
    const bool arpgMode =
        runtime.settingsSnapshot().arpgModeEnabled && !screenState.arpgModeFirstPersonUseMode();
    const bool keyboardUsePressed = !arpgMode && input.action(KeyboardAction::Trigger).held;
    const bool contextActionTriggerPressed = arpgMode && input.action(KeyboardAction::Trigger).held;
    const bool usePressed = input.action(KeyboardAction::Use).held;
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
                .keyboardActivationPressed = usePressed,
                .keyboardAttackPressed = attackPressed,
                .arpgMode = arpgMode,
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
        runtime.clearContextActionState();
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

        if (overlayInteractionState.gameplayHudSpellTargetCancelRequested)
        {
            pendingTargetInput.cancelPressed = true;
            overlayInteractionState.gameplayHudSpellTargetCancelRequested = false;
        }

        const bool confirmFromMobileHudButton =
            overlayInteractionState.gameplayHudSpellTargetConfirmRequested;
        overlayInteractionState.gameplayHudSpellTargetConfirmRequested = false;

#if defined(__ANDROID__)
        const bool mobileGroundTargetConfirmSpell = usesMobileGroundTargetConfirm(pendingSpellCast.spellId);
#else
        const bool mobileGroundTargetConfirmSpell = false;
#endif

        if (mobileGroundTargetConfirmSpell
            && pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint
            && !confirmFromMobileHudButton
            && !hoveredPortraitMemberIndex
            && worldReady
            && pWorldRuntime != nullptr)
        {
            const GameplayPendingSpellWorldTargetFacts targetFacts =
                pWorldRuntime->pickPendingSpellWorldTarget(pendingSpellPickRequest);
            const std::optional<bx::Vec3> groundTargetPoint =
                GameplaySpellActionController::resolveGroundTargetPointForWorldHit(
                    targetFacts.worldHit,
                    pWorldRuntime,
                    targetFacts.fallbackGroundTargetPoint);

            if (groundTargetPoint)
            {
                pendingSpellCast.hasSelectedGroundTargetPoint = true;
                pendingSpellCast.selectedGroundTargetX = groundTargetPoint->x;
                pendingSpellCast.selectedGroundTargetY = groundTargetPoint->y;
                pendingSpellCast.selectedGroundTargetZ = groundTargetPoint->z;
            }
        }

        bool confirmFromPointer = pointerPolicy.leftMousePressed;
#if defined(__ANDROID__)
        if (mobileGroundTargetConfirmSpell)
        {
            confirmFromPointer = false;
        }
#endif

        if ((confirmFromPointer || confirmFromMobileHudButton) && !pendingTargetInput.cancelPressed)
        {
            pendingTargetInput.confirmPressed = true;

            if (confirmFromMobileHudButton
                && mobileGroundTargetConfirmSpell
                && pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint
                && pendingSpellCast.hasSelectedGroundTargetPoint)
            {
                pendingTargetInput.fallbackGroundTargetPoint = bx::Vec3{
                    pendingSpellCast.selectedGroundTargetX,
                    pendingSpellCast.selectedGroundTargetY,
                    pendingSpellCast.selectedGroundTargetZ
                };
            }
            else if (!pendingSpellCast.clickLatch
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
        worldInteractionInputState.arpgContextActionTriggerLatch = false;
        worldInteractionInputState.keyboardUseNextRepeatTickNanoseconds = 0;
        worldInteractionInputState.heldInventoryDropLatch = false;
        overlayInteractionState.activateInspectLatch = false;
        worldInteractionInputState.inspectKeyboardActivateLatch = false;
        worldInteractionInputState.inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
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
                .currentTickNanoseconds = currentTickNanoseconds,
                .pickedHit = keyboardUseHit,
                .hasPickedHit = hasKeyboardUseHit,
                .pRuntime = &runtime,
                .pWorldRuntime = pWorldRuntime,
                .interactionMethod = GameplayInteractionMethod::Keyboard,
            });

    if (keyboardInteractionResult.activated)
    {
        result.keyboardUseActivated = true;
        clearWorldHover(pWorldRuntime);
        runtime.clearContextActionState();
    }

    if (heldItemActive)
    {
        runtime.clearContextActionState();
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

    if (runtime.settingsSnapshot().contextActionPopup && pWorldRuntime != nullptr)
    {
        GameplayWorldHit contextActionHit = {};
        std::optional<std::string> contextActionEventStatusText;
        GameplayContextActionState &contextActionState = runtime.contextActionState();
        const uint64_t contextActionRefreshIntervalNanoseconds =
            arpgMode
                ? ContextActionRefreshNanoseconds
                : contextActionState.visible ? ContextActionRefreshNanoseconds : ContextActionIdleRetryNanoseconds;
        const bool contextActionRayChanged =
            !arpgMode && contextActionPickRayChanged(contextActionState, currentInteractionPickRequest);
        const bool contextActionRefreshDue =
            contextActionState.lastUpdateNanoseconds == 0
            || currentTickNanoseconds < contextActionState.lastUpdateNanoseconds
            || contextActionRayChanged
            || currentTickNanoseconds - contextActionState.lastUpdateNanoseconds
                >= contextActionRefreshIntervalNanoseconds;

        if (contextActionRefreshDue)
        {
            std::optional<GameplayContextAction> contextAction;

            if (arpgMode)
            {
                contextActionHit = pickArpgModePopupInteractionTarget(*pWorldRuntime, runtime);
                contextAction = buildContextAction(*pWorldRuntime, contextActionHit, contextActionEventStatusText);
            }
            else
            {
                contextAction =
                    buildContextAction(*pWorldRuntime, result.hover.worldHit, result.hover.eventTargetStatusText);

                if (!contextAction)
                {
                    contextActionHit =
                        pickPrecisionContextActionTarget(*pWorldRuntime, currentInteractionPickRequest);

                    if (isSameActivationTarget(contextActionHit, result.hover.worldHit))
                    {
                        contextActionEventStatusText = result.hover.eventTargetStatusText;
                    }

                    contextAction = buildContextAction(*pWorldRuntime, contextActionHit, contextActionEventStatusText);
                }
            }

            setSingleContextAction(
                runtime,
                contextAction,
                currentTickNanoseconds,
                currentInteractionPickRequest);
        }
        else
        {
            const bool visibleActionInvalid =
                contextActionState.visible && contextActionState.primaryIndex >= contextActionState.actions.size();
            bool visibleActionNoLongerActivatable = false;

            if (!arpgMode && contextActionState.visible && !visibleActionInvalid)
            {
                const GameplayWorldHit &visibleActionHit =
                    contextActionState.actions[contextActionState.primaryIndex].worldHit;
                visibleActionNoLongerActivatable =
                    !pWorldRuntime->canActivateWorldHit(visibleActionHit, GameplayInteractionMethod::Keyboard);
            }

            if (visibleActionInvalid || visibleActionNoLongerActivatable)
            {
                runtime.clearContextActionState();
            }
        }
    }
    else
    {
        runtime.clearContextActionState();
    }

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

    if (pointerPolicy.attackPressed
        || pointerPolicy.leftMousePressed
        || worldInteractionInputState.inspectMouseActivateLatch)
    {
        pickCurrentHit();
    }

    const bool stealPressed =
        !arpgMode
        && input.leftMouseButton.pressed
        && pointerPolicy.leftMousePressed
        && (input.isScancodeHeld(SDL_SCANCODE_LCTRL) || input.isScancodeHeld(SDL_SCANCODE_RCTRL));

    if (stealPressed
        && currentHit.kind == GameplayWorldHitKind::Actor
        && currentHit.actor
        && pWorldRuntime != nullptr)
    {
        TurnBasedCombatRuntime &turnBasedCombatRuntime = runtime.turnBasedCombatRuntime();
        Party *pMutableParty = pWorldRuntime->party();

        if (turnBasedCombatRuntime.active()
            && (pMutableParty == nullptr || !turnBasedCombatRuntime.beginPlayerActionOrFinishMovement(*pMutableParty)))
        {
            return result;
        }

        const bool stole = pWorldRuntime->tryStealFromActor(
            currentHit.actor->actorIndex,
            interactionRandomSeed(0x9e3779b9u),
            interactionRandomSeed(0x7f4a7c15u));

        if (stole)
        {
            if (turnBasedCombatRuntime.active() && pMutableParty != nullptr)
            {
                const size_t memberIndex = pMutableParty->activeMemberIndex();
                const Character *pMember = pMutableParty->member(memberIndex);
                const float recoverySeconds = pMember != nullptr ? pMember->recoverySecondsRemaining : 0.0f;
                turnBasedCombatRuntime.applyPlayerAction(*pMutableParty, memberIndex, recoverySeconds);
            }

            result.mouseActivationActivated = true;
            clearWorldHover(pWorldRuntime);
            return result;
        }
    }

    const bool hadLootViewBeforeActivation = hasActiveLootView(runtime);

    if (arpgMode && contextActionTriggerPressed)
    {
        if (!worldInteractionInputState.arpgContextActionTriggerLatch && worldReady && pWorldRuntime != nullptr)
        {
            worldInteractionInputState.arpgContextActionTriggerLatch = true;
            const GameplayContextActionState &contextActionState = runtime.contextActionStateReadOnly();
            const bool hasPrimaryContextAction =
                contextActionState.visible && contextActionState.primaryIndex < contextActionState.actions.size();
            bool activated = pWorldRuntime->tryActivateArpgModeLootPopup();

            if (!activated)
            {
                const GameplayWorldHit activationHit =
                    hasPrimaryContextAction
                        ? contextActionState.actions[contextActionState.primaryIndex].worldHit
                        : runtime.settingsSnapshot().contextActionPopup
                            ? pickArpgModePopupInteractionTarget(*pWorldRuntime, runtime)
                            : pickArpgModeForwardInteractionTarget(*pWorldRuntime, runtime);
                activated =
                    tryActivateWorldHit(
                        &runtime,
                        pWorldRuntime,
                        activationHit,
                        GameplayInteractionMethod::Keyboard);
            }

            if (activated)
            {
                result.keyboardUseActivated = true;
                refreshWorldHover(standardHoverInput, pWorldRuntime);
                runtime.clearContextActionState();

                const bool hasLootViewAfterActivation = hasActiveLootView(runtime);

                if (!hadLootViewBeforeActivation && hasLootViewAfterActivation)
                {
                    overlayInteractionState.lootChestItemLatch = true;
                }
            }
        }
    }
    else if (arpgMode)
    {
        worldInteractionInputState.arpgContextActionTriggerLatch = false;
    }

    GameplayWorldHit keyboardActivationHit = {};

    if (pointerPolicy.activationPressed && worldReady && pWorldRuntime != nullptr)
    {
        if (arpgMode)
        {
            keyboardActivationHit =
                pickArpgModePrecisionInteractionTarget(*pWorldRuntime, currentInteractionPickRequest);

            if (!keyboardActivationHit.hasHit)
            {
                const GameplayContextActionState &contextActionState = runtime.contextActionStateReadOnly();

                if (contextActionState.visible
                    && contextActionState.primaryIndex < contextActionState.actions.size())
                {
                    keyboardActivationHit = contextActionState.actions[contextActionState.primaryIndex].worldHit;
                }
                else
                {
                    keyboardActivationHit = pickArpgModeForwardInteractionTarget(*pWorldRuntime, runtime);
                }
            }
        }
        else
        {
            const GameplayContextActionState &contextActionState = runtime.contextActionStateReadOnly();
            const bool hasPrimaryContextAction =
                contextActionState.visible && contextActionState.primaryIndex < contextActionState.actions.size();

            if (hasPrimaryContextAction)
            {
                keyboardActivationHit = contextActionState.actions[contextActionState.primaryIndex].worldHit;
            }
            else
            {
                const GameplayWorldPickRequest keyboardActivationPickRequest =
                    pWorldRuntime->buildWorldPickRequest(
                        GameplayWorldPickRequestInput{
                            .screenX = pointerPolicy.inspectScreenX,
                            .screenY = pointerPolicy.inspectScreenY,
                            .screenWidth = input.screenWidth,
                            .screenHeight = input.screenHeight,
                            .includeRay = true,
                        });
                keyboardActivationHit =
                    pickPrecisionContextActionTarget(*pWorldRuntime, keyboardActivationPickRequest);
            }
        }
    }

    const KeyboardActivationInteractionResult keyboardActivationResult =
        updateKeyboardActivationInteraction(
            worldInteractionInputState,
            KeyboardActivationInteractionInput{
                .activationPressed = pointerPolicy.activationPressed,
                .allowInteraction = worldReady,
                .activateArpgLootPopupFirst = arpgMode,
                .currentTickNanoseconds = currentTickNanoseconds,
                .currentHit = keyboardActivationHit,
                .pRuntime = &runtime,
                .pWorldRuntime = pWorldRuntime,
                .interactionMethod = GameplayInteractionMethod::Keyboard,
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
        runtime.clearContextActionState();

        const bool hasLootViewAfterActivation = hasActiveLootView(runtime);

        if (!hadLootViewBeforeActivation && hasLootViewAfterActivation)
        {
            overlayInteractionState.lootChestItemLatch = true;
        }
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

    runtime.setStatusBarHoverText(result.hover.statusText);

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
