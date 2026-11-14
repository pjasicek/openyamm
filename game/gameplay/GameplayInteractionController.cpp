#include "game/gameplay/GameplayInteractionController.h"
#include "engine/Localization.h"

#include "game/ui/GameplayFormationBuilder.h"
#include "game/ui/GameplaySoloBarSelector.h"
#include "game/ui/GameplayQuickItems.h"

#include "game/gameplay/GameplayHeldItemController.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/MeleeContactEffects.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/party/BattleOrders.h"
#include "game/rules/SoloTalents.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GameplayWorldItemInteraction.h"
#include "game/gameplay/GameplayWorldItemPolicy.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/items/ItemRuntime.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/tables/ItemTable.h"
#include "game/gameplay/ActorNameText.h"

#include <SDL3/SDL_timer.h>

#include <algorithm>
#include <chrono>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float NearHoverStatusDistance = 1024.0f;
constexpr float ActorHoverStatusDistance = 8192.0f;
// A hovered item within reach reads "Get <name>", as the native status bar does (depth 0x200).
constexpr float WorldItemGetStatusDistance = 512.0f;
constexpr uint64_t HoverInspectRefreshNanoseconds = 33 * 1000 * 1000;
constexpr uint64_t ContextActionDirectionRefreshNanoseconds = 33 * 1000 * 1000;
constexpr uint64_t ContextActionRefreshNanoseconds = 250 * 1000 * 1000;
constexpr uint64_t ContextActionIdleRetryNanoseconds = 1000 * 1000 * 1000;
constexpr uint64_t KeyboardInteractionFirstRepeatNanoseconds = 500 * 1000 * 1000;
constexpr uint64_t KeyboardInteractionRepeatNanoseconds = 67 * 1000 * 1000;
constexpr float ContextActionRayOriginChangeThresholdSquared = 4.0f;
constexpr float ContextActionRayDirectionChangeThresholdSquared = 0.000001f;
constexpr uint32_t ArrowProjectileObjectId = 545;
constexpr uint32_t FireArrowProjectileObjectId = 550;
constexpr uint32_t ThrowingDaggerProjectileObjectId = 307;
constexpr uint32_t ThrowingAxeProjectileObjectId = 309;
constexpr uint32_t BlasterProjectileObjectId = 555;

// "Orange Barrel (+2 Intellect)", "Drink from the Fountain (+50 Might (Temporary))": the effect of the hovered event
// once the party has the autonote recording it.
void appendLearnedEventEffect(
    GameplayHoverStatusPayload &payload,
    const IGameplayWorldRuntime &worldRuntime,
    const GameplayScreenRuntime *pScreenRuntime)
{
    const std::optional<GameplayEventTargetHit> &eventTarget = payload.worldHit.eventTarget;

    if (pScreenRuntime == nullptr || !eventTarget || eventTarget->nameEventId == 0
        || !payload.eventTargetStatusText || payload.eventTargetStatusText->empty())
    {
        return;
    }

    const std::optional<ScriptedEventProgram> *pProgram = eventTarget->nameEventIsLocal
        ? worldRuntime.localEventProgram()
        : worldRuntime.globalEventProgram();

    if (pProgram == nullptr || !*pProgram)
    {
        return;
    }

    const std::optional<ScriptedEventProgram::LearnedEffect> effect =
        (*pProgram)->learnedEffect(eventTarget->nameEventId);

    if (effect && pScreenRuntime->isAutonoteUnlocked(effect->autonoteId))
    {
        *payload.eventTargetStatusText += " (" + effect->effect + ")";
    }
}

// Names a hovered item as its inventory would: an unidentified item by its class, an enchanted one in full.
void resolveWorldItemHoverName(
    GameplayHoverStatusPayload &payload,
    const IGameplayWorldRuntime &worldRuntime,
    const GameplayScreenRuntime *pScreenRuntime)
{
    std::optional<GameplayWorldItemTargetHit> &worldItem = payload.worldHit.worldItem;

    if (pScreenRuntime == nullptr || payload.worldHit.kind != GameplayWorldHitKind::WorldItem || !worldItem)
    {
        return;
    }

    const ItemTable *pItemTable = pScreenRuntime->itemTable();
    GameplayWorldItemInspectState itemState = {};

    if (pItemTable == nullptr || !worldRuntime.worldItemInspectState(worldItem->worldItemIndex, itemState))
    {
        return;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(itemState.item.objectDescriptionId);

    if (pItemDefinition != nullptr)
    {
        worldItem->displayName = ItemRuntime::displayName(
            itemState.item,
            *pItemDefinition,
            pScreenRuntime->standardItemEnchantTable(),
            pScreenRuntime->specialItemEnchantTable());
    }
}

// Names a hovered ground item above the pointer in the colour the rules give its name (MAW's rarities, none for
// Common), while the status bar names it.
void updateWorldItemHoverLabel(
    GameplayScreenRuntime &runtime,
    const IGameplayWorldRuntime *pWorldRuntime,
    const GameplayInteractionController::HoverStateResult &hover,
    float screenX,
    float screenY)
{
    GameplayWorldItemInspectState itemState = {};

    if (pWorldRuntime == nullptr || hover.hitKind != GameplayWorldHitKind::WorldItem || !hover.worldHit.worldItem
        || hover.statusText.empty() || hover.worldHit.worldItem->displayName.empty()
        || !pWorldRuntime->worldItemInspectState(hover.worldHit.worldItem->worldItemIndex, itemState)
        || itemState.isGold)
    {
        runtime.setWorldItemHoverLabel({}, 0, 0, 0);
        return;
    }

    const std::optional<uint32_t> color = gameRulesFor(runtime.partyReadOnly()).items.nameColor(itemState.item);

    if (!color)
    {
        runtime.setWorldItemHoverLabel({}, 0, 0, 0);
        return;
    }

    const uint32_t colorAbgr = 0xff000000u | ((*color & 0xffu) << 16) | (*color & 0xff00u) | ((*color >> 16) & 0xffu);
    runtime.setWorldItemHoverLabel(
        Engine::localizeKnown(hover.worldHit.worldItem->displayName), colorAbgr, screenX, screenY);
}

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
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

float vecDeltaSquared(const bx::Vec3 &left, const bx::Vec3 &right)
{
    const float deltaX = left.x - right.x;
    const float deltaY = left.y - right.y;
    const float deltaZ = left.z - right.z;

    return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
}

bool contextActionPickRayOriginChanged(
    const GameplayContextActionState &state,
    const GameplayWorldPickRequest &request)
{
    if (!request.hasRay || !state.hasLastUpdateRay)
    {
        return request.hasRay != state.hasLastUpdateRay;
    }

    return vecDeltaSquared(request.rayOrigin, state.lastUpdateRayOrigin)
        >= ContextActionRayOriginChangeThresholdSquared;
}

bool contextActionPickRayDirectionChanged(
    const GameplayContextActionState &state,
    const GameplayWorldPickRequest &request)
{
    if (!request.hasRay || !state.hasLastUpdateRay)
    {
        return request.hasRay != state.hasLastUpdateRay;
    }

    return vecDeltaSquared(request.rayDirection, state.lastUpdateRayDirection)
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
    case GameplayContextActionKind::DropHeldItem:
        return "context_drop_item";
    case GameplayContextActionKind::None:
        break;
    }

    return "context_generic_event";
}

std::string contextActionDefaultLabel(GameplayContextActionKind kind)
{
    switch (kind)
    {
    case GameplayContextActionKind::Talk:
        return Engine::tr("Talk");
    case GameplayContextActionKind::PickUpItem:
        return Engine::tr("Pick Up");
    case GameplayContextActionKind::LootCorpse:
        return Engine::tr("Loot");
    case GameplayContextActionKind::OpenChest:
        return Engine::tr("Open Chest");
    case GameplayContextActionKind::EnterHouse:
        return Engine::tr("Enter");
    case GameplayContextActionKind::OpenDoor:
        return Engine::tr("Open Door");
    case GameplayContextActionKind::PressButton:
        return Engine::tr("Press");
    case GameplayContextActionKind::UseLever:
        return Engine::tr("Use Lever");
    case GameplayContextActionKind::GenericEvent:
        return "";
    case GameplayContextActionKind::DropHeldItem:
        return Engine::tr("Drop Item");
    case GameplayContextActionKind::None:
        break;
    }

    return Engine::tr("Use");
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
        return Engine::tr("Exit");
    }

    if (metadata.kind == "travel")
    {
        return Engine::tr("Travel");
    }

    if (metadata.kind == "passage")
    {
        return Engine::tr("Passage");
    }

    if (metadata.kind == "teleport")
    {
        return Engine::tr("Teleport");
    }

    if (metadata.kind == "use_switch")
    {
        return Engine::tr("Use Switch");
    }

    if (metadata.kind == "use_elevator")
    {
        return Engine::tr("Use Elevator");
    }

    if (metadata.kind == "use_pedestal")
    {
        return Engine::tr("Use Pedestal");
    }

    if (metadata.kind == "fountain")
    {
        return Engine::tr("Fountain");
    }

    if (metadata.kind == "well")
    {
        return Engine::tr("Well");
    }

    if (metadata.kind == "shrine")
    {
        return Engine::tr("Shrine");
    }

    if (metadata.kind == "obelisk")
    {
        return Engine::tr("Obelisk");
    }

    if (metadata.kind == "boost")
    {
        return Engine::tr("Boost");
    }

    if (metadata.kind == "read")
    {
        return Engine::tr("Read");
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

std::string contextActionLabelWithName(const std::string &verb, const std::string &name)
{
    if (name.empty())
    {
        return verb;
    }

    return Engine::tr("{action} ({target})", {{"action", verb}, {"target", name}});
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
                ? localizedActorName(hit.actor->displayName)
                : contextActionDefaultLabel(action.kind);
        }
        else
        {
            action.label = contextActionLabelWithName(
                contextActionDefaultLabel(action.kind), localizedActorName(hit.actor->displayName));
        }
    }
    else if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        action.kind = GameplayContextActionKind::PickUpItem;
        action.label =
            contextActionLabelWithName(Engine::tr("Pick"), Engine::localizeKnown(hit.worldItem->displayName));
    }
    else if (hit.kind == GameplayWorldHitKind::Chest && hit.container)
    {
        action.kind = GameplayContextActionKind::OpenChest;
        action.label = contextActionDefaultLabel(action.kind);
    }
    else if (hit.kind == GameplayWorldHitKind::Corpse && hit.container)
    {
        action.kind = GameplayContextActionKind::LootCorpse;
        action.label = contextActionLabelWithName(
            contextActionDefaultLabel(action.kind), Engine::localizeKnown(hit.container->displayName));
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
            // In the interface language, as the status bar shows the same text (issue #31, OY-578).
            action.label = hasStatusText(eventTargetStatusText)
                ? Engine::localize(*eventTargetStatusText)
                : (!hit.eventTarget->name.empty()
                    ? Engine::localize(hit.eventTarget->name)
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
    const std::string resolvedItemName = itemName.empty() ? Engine::tr("item") : itemName;
    return Engine::tr("You found an item ({item})!", {{"item", resolvedItemName}});
}

std::string heldItemDisplayName(const GameplayScreenRuntime &runtime)
{
    const GameplayUiController::HeldInventoryItemState &heldItem = runtime.heldInventoryItem();
    const ItemTable *pItemTable = runtime.itemTable();
    const ItemDefinition *pItemDefinition =
        pItemTable != nullptr ? pItemTable->get(heldItem.item.objectDescriptionId) : nullptr;

    return pItemDefinition != nullptr ? ItemRuntime::displayName(heldItem.item, *pItemDefinition) : "item";
}

void setHeldItemDropContextAction(GameplayScreenRuntime &runtime)
{
    GameplayContextAction action = {};
    action.kind = GameplayContextActionKind::DropHeldItem;
    action.label = Engine::tr("Drop {item}", {{"item", heldItemDisplayName(runtime)}});
    action.iconId = contextActionIconId(action.kind);

    GameplayContextActionState &state = runtime.contextActionState();
    state = {};
    state.visible = true;
    state.actions.push_back(std::move(action));
    state.primaryIndex = 0;
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
    const ItemTable *pItemTable = runtime.itemTable();
    const ItemDefinition *pItemDefinition =
        pItemTable != nullptr ? pItemTable->get(heldItem.item.objectDescriptionId) : nullptr;

    const bool droppable = pItemDefinition == nullptr
        || gameRulesFor(runtime.partyReadOnly()).items.canDropToWorld(heldItem.item, *pItemDefinition);

    if (pWorldRuntime == nullptr || !droppable)
    {
        runtime.setStatusBarEvent(Engine::tr("Can't drop {item}", {{"item", itemName}}));
        return false;
    }

    GameplayHeldItemDropRequest resolvedDropRequest = *dropRequest;
    resolvedDropRequest.item = heldItem.item;

    if (!pWorldRuntime->dropHeldItemToWorld(resolvedDropRequest))
    {
        runtime.setStatusBarEvent(Engine::tr("Can't drop {item}", {{"item", itemName}}));
        return false;
    }

    runtime.setStatusBarEvent(Engine::tr("Dropped {item}", {{"item", itemName}}));
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

    return pItemDefinition != nullptr ? ItemRuntime::foundItemName(*pItemDefinition) : Engine::tr("item");
}

bool canStoreWorldItemInInventory(
    Party &party,
    const InventoryItem &item,
    const ItemTable *pItemTable)
{
    const Party::Snapshot snapshot = party.snapshot();
    const ScopedGameplayDebugTraceSuppression traceSuppression;
    const bool canStore = storePickedUpItem(party, item, pItemTable).has_value();
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
    const bool canStoreInInventory =
        !worldItemState.isGold && canStoreWorldItemInInventory(*pParty, worldItemState.item, runtime.itemTable());
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
            runtime.setStatusBarEvent(Engine::tr("Pack is Full!"));
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
        const FoundGold foundGold = resolveFoundGold(
            static_cast<uint32_t>(std::max(0, pickupDecision.goldAmount)),
            worldRuntime.eventRuntimeState(),
            pParty);
        pParty->addGold(static_cast<int>(foundGold.partyAmount), GoldReason::LootGround);
        pParty->requestSound(SoundId::Gold);
        runtime.setStatusBarEvent(foundGoldStatusText(foundGold));
        recordWorldItemActivationResult(
            worldRuntime,
            "picked up " + std::to_string(foundGold.partyAmount) + " gold");
        return true;
    }

    const std::string itemName = worldItemDisplayName(removedItemState, runtime.itemTable());

    if (pickupDecision.destination == GameplayWorldItemPickupDestination::Inventory)
    {
        const std::optional<StoredPickup> stored =
            storePickedUpItem(*pParty, removedItemState.item, runtime.itemTable());

        if (!stored)
        {
            return false;
        }

        GAMEPLAY_DEBUG_TRACE(
            "item_received destination=inventory source=world_item item_id="
            + std::to_string(removedItemState.item.objectDescriptionId)
            + gameplayDebugTraceItemSummary(removedItemState.item.objectDescriptionId, runtime.itemTable())
            + " world_item_index=" + std::to_string(worldItemIndex)
            + " member_index=" + std::to_string(stored->memberIndex));
        pParty->requestSound(SoundId::Gold);
        runtime.playSpeechReaction(stored->memberIndex, SpeechId::FoundItem, true);
        runtime.setStatusBarEvent(formatFoundItemStatusText(itemName) + storedPickupOwnerSuffix(*pParty, *stored));
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
        if (pWorldRuntime->hasCustomWorldItemActivation(hit.worldItem->worldItemIndex))
        {
            return pWorldRuntime->activateCustomWorldItem(hit.worldItem->worldItemIndex);
        }

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

// A solo run with the bow in the arms shoots at any range: the bow swapped in, or an archer's bow with nothing (or only
// a broken weapon) in the main hand, as the view model's kit shows it.
bool soloBowDrawn(GameplayScreenRuntime &runtime, const Character *pMember)
{
    const bool archer = pMember != nullptr && pMember->equipment.bow != 0 && !pMember->equipmentRuntime.bow.broken
        && (pMember->equipment.mainHand == 0 || pMember->equipmentRuntime.mainHand.broken);
    return runtime.soloRun() && (runtime.viewModelLink().bowSelected || archer);
}

// Whether a solo dragon's attack press shows the breath rather than the claws: it can breathe and its target is out of
// claw reach, as executePartyAttack decides at the release (choosePartyAttackMode). Only what the forelegs play
// depends on it; the rules decide again at the release.
bool soloDragonBreathes(IGameplayWorldRuntime &world, const Party &party, const Character &member,
    const CharacterAttackProfile &profile, const GameplayWorldHit &attackHit,
    const GameplayWorldPickRequest &pickRequest)
{
    if (!gameRulesFor(&party).classes.isDragon(member) || !profile.hasDragonBreath
        || !profile.rangedAttackBonus.has_value())
    {
        return false;
    }
    const std::optional<size_t> directActor = attackHit.kind == GameplayWorldHitKind::Actor && attackHit.actor
        ? std::optional<size_t>(attackHit.actor->actorIndex) : std::nullopt;
    return !GameplayActionController::partyAttackTargetInMeleeReach(
        world, world.buildPartyAttackFrameInput(pickRequest), directActor);
}

// A solo run's talent blow (devdocs/solo_action/TALENTS.md): a set target, a share of the damage, an extra blow without
// sound or recovery, a shot.
std::vector<size_t> collectTalentTargets(IGameplayWorldRuntime &world, const GameplayPartyAttackFrameInput &attackInput,
    float reach, float arcDegrees, size_t maxCount);

struct TalentBlow
{
    std::optional<size_t> actorIndex;
    float share = 1.0f;
    bool extra = false;
    bool shot = false;
};

// Sweeping Blows (a melee blow also strikes the nearest others in its arc) and Piercing Arrows (a bow shot also hits the
// monsters behind its target) for the ordinary attack about to hit `target`. Archery never touches a dragon's breath:
// Piercing Arrows needs a bow in hand.
template <typename StrikeBlow>
void strikeFollowUpTalentBlows(GameplayScreenRuntime &runtime, IGameplayWorldRuntime &world,
    const GameplayPartyAttackFrameInput &attackInput, size_t target, bool bowDrawn, StrikeBlow strike)
{
    Party *pParty = world.party();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    if (pMember == nullptr || !GameMechanics::canTakeGameplayAction(*pMember) || !runtime.soloTalents())
    {
        return;
    }
    const std::optional<GameplayPartyAttackActorFacts> facts = world.partyAttackActorFacts(target, false);
    if (!facts)
    {
        return;
    }
    const GameplayWorldPoint party = attackInput.partyPosition;
    const float targetDistance = std::max(0.0f,
        std::hypot(facts->position.x - party.x, facts->position.y - party.y) - float(facts->radius));
    constexpr float MeleeReach = 407.2f;
    const SoloTalentTable &table = soloTalentTable();
    const bool melee = !bowDrawn && targetDistance <= MeleeReach;
    const bool bow = pMember->equipment.bow != 0 && (bowDrawn || targetDistance > MeleeReach);

    if (const int rank = talentRank(*pMember, "sweeping_blows"); melee && rank > 0)
    {
        if (const TalentDefinition *pTalent = table.find("sweeping_blows"))
        {
            const size_t extra = size_t(std::max(1, int(pTalent->perRank) * rank));
            std::vector<size_t> beside = collectTalentTargets(world, attackInput, MeleeReach, pTalent->arc, extra + 1);
            beside.erase(std::remove(beside.begin(), beside.end(), target), beside.end());
            const float share = talentSkillShare(*pTalent, *pMember);
            for (size_t index = 0; index < beside.size() && index < extra; ++index)
            {
                strike(TalentBlow{beside[index], share, true, false});
            }
        }
    }

    if (const int rank = talentRank(*pMember, "piercing_arrows"); bow && rank > 0)
    {
        if (const TalentDefinition *pTalent = table.find("piercing_arrows"))
        {
            constexpr float Reach = 5120.0f;
            const std::vector<size_t> line = collectTalentTargets(world, attackInput, Reach, pTalent->arc, 64);
            const auto found = std::find(line.begin(), line.end(), target);
            const size_t extra = size_t(std::max(1, int(pTalent->perRank) * rank));
            const float share = talentSkillShare(*pTalent, *pMember);
            size_t struck = 0;
            for (auto it = found == line.end() ? line.end() : std::next(found); it != line.end() && struck < extra; ++it)
            {
                strike(TalentBlow{*it, share, true, true});
                ++struck;
            }
        }
    }
}

GameplayActionController::PartyAttackExecutionResult executePartyAttack(
    GameplayScreenRuntime &runtime,
    GameplaySpellService &spellService,
    const GameplayPartyAttackFrameInput &partyAttackInput,
    const GameplayInteractionController::HoverStateInput &standardHoverInput,
    const GameplaySpellActionController::TargetQueries &targetQueries,
    const GameplayActionController::AttackActionDecision &decision,
    const GameplayWorldHit &currentHit,
    bool viewModelSwingShown = false,
    const TalentBlow *pTalentBlow = nullptr)
{
    if (!partyAttackInput.enabled)
    {
        return {};
    }

    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return {};
    }

    Party *pParty = pWorldRuntime->party();

    if (pParty == nullptr)
    {
        return {};
    }

    TurnBasedCombatRuntime &turnBasedCombatRuntime = runtime.turnBasedCombatRuntime();
    if (turnBasedCombatRuntime.active())
    {
        if (turnBasedCombatRuntime.stage() == TurnBasedCombatStage::Movement)
        {
            turnBasedCombatRuntime.finishMovementPhase();
            GAMEPLAY_DEBUG_TRACE("turn_based_attack_finished_movement stage=movement");
            return {};
        }

        // Also makes the member whose turn it is the attacker, whoever the player selected.
        if (!turnBasedCombatRuntime.beginPlayerActionOrFinishMovement(*pParty))
        {
            return {};
        }
    }

    const bool bowDrawn = soloBowDrawn(runtime, pParty->activeMember());

    const std::optional<size_t> directActorIndex = pTalentBlow != nullptr && pTalentBlow->actorIndex
        ? pTalentBlow->actorIndex
        : currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? std::optional<size_t>(currentHit.actor->actorIndex)
            : std::nullopt;
    // A solo run's Sweeping Blows and Piercing Arrows: extra blows on the monsters beside or behind the target, struck
    // before the blow that pays the recovery (a recovering member strikes no more).
    if (pTalentBlow == nullptr && directActorIndex && runtime.soloTalents() && !turnBasedCombatRuntime.active())
    {
        strikeFollowUpTalentBlows(runtime, *pWorldRuntime, partyAttackInput, *directActorIndex, bowDrawn,
            [&](const TalentBlow &blow)
            {
                executePartyAttack(runtime, spellService, partyAttackInput, standardHoverInput, targetQueries, decision,
                    GameplayWorldHit{}, false, &blow);
            });
    }

    // Shown in combat messages, in the interface language.
    const std::string directTargetName =
        currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? localizedActorName(currentHit.actor->displayName)
            : "";
    const std::optional<size_t> directTargetBModelIndex =
        currentHit.kind == GameplayWorldHitKind::EventTarget
            && currentHit.eventTarget
            && currentHit.eventTarget->targetKind == GameplayWorldEventTargetKind::Surface
        ? std::optional<size_t>(currentHit.eventTarget->targetIndex)
        : std::nullopt;
    const std::optional<size_t> directTargetEntityIndex =
        currentHit.kind == GameplayWorldHitKind::EventTarget
            && currentHit.eventTarget
            && currentHit.eventTarget->targetKind == GameplayWorldEventTargetKind::Entity
        ? std::optional<size_t>(currentHit.eventTarget->targetIndex)
        : std::nullopt;
    const float directWorldTargetDistance = directTargetBModelIndex || directTargetEntityIndex
        ? currentHit.eventTarget->distance
        : 0.0f;
    const std::optional<GameplayActionController::WorldPoint> hitRangedTarget =
        partyRangedTargetFromWorldHit(currentHit);
    const std::optional<GameplayActionController::WorldPoint> directTargetHitPoint =
        currentHit.kind == GameplayWorldHitKind::Actor && currentHit.actor
            ? std::optional<GameplayActionController::WorldPoint>(
                GameplayActionController::WorldPoint{
                    currentHit.actor->hitPoint.x,
                    currentHit.actor->hitPoint.y,
                    currentHit.actor->hitPoint.z,
                })
            : std::nullopt;

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
            .pMonsterProjectileTable = runtime.monsterProjectileTable(),
            .pSpecialItemEnchantTable = runtime.specialItemEnchantTable(),
            .pMm9HirelingTable = runtime.mm9HirelingTable(),
            .directTargetActorIndex = directActorIndex,
            .directTargetHitPoint = directTargetHitPoint,
            .directTargetBModelIndex = directTargetBModelIndex,
            .directTargetEntityIndex = directTargetEntityIndex,
            .directWorldTargetDistance = directWorldTargetDistance,
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
            .fireArrowProjectileObjectId = FireArrowProjectileObjectId,
            .throwingDaggerProjectileObjectId = ThrowingDaggerProjectileObjectId,
            .throwingAxeProjectileObjectId = ThrowingAxeProjectileObjectId,
            .blasterProjectileObjectId = BlasterProjectileObjectId,
            .pressedThisFrame = decision.pressedThisFrame,
            .targetQueries = targetQueries,
            .blowScreenDirection = viewModelSwingShown ? runtime.viewModelLink().blowDirection : std::nullopt,
            .swingSoundPlayed = viewModelSwingShown,
            .recoverySpentSeconds = viewModelSwingShown ? runtime.viewModelLink().swingWaitSeconds : 0.0f,
            .talentShare = pTalentBlow != nullptr ? pTalentBlow->share : 1.0f,
            .talentExtraBlow = pTalentBlow != nullptr && pTalentBlow->extra,
            .talentShot = pTalentBlow != nullptr && pTalentBlow->shot,
            .preferBow = bowDrawn,
            .preferMelee = runtime.soloRun() && !bowDrawn,
        });

    // The view model shows the action: a swing or cast it already played (or a talent's own clip) needs nothing more.
    if (attackResult.actionPerformed && pTalentBlow == nullptr
        && !(viewModelSwingShown
            && (attackResult.attack.mode == CharacterAttackMode::Melee || runtime.viewModelLink().waitIsCast)))
    {
        const CharacterAttackMode mode = attackResult.attack.mode;
        runtime.noteViewModelAction(mode == CharacterAttackMode::Melee
            ? GameplayScreenRuntime::ViewModelAction::Melee
            : (mode == CharacterAttackMode::None || mode == CharacterAttackMode::Wand
                ? GameplayScreenRuntime::ViewModelAction::Cast : GameplayScreenRuntime::ViewModelAction::Shot));
    }
    if (turnBasedCombatRuntime.active() && attackResult.actionPerformed)
    {
        turnBasedCombatRuntime.applyPlayerAction(
            *pParty,
            attackResult.actingMemberIndex,
            attackResult.attack.recoverySeconds);
    }
    // A member whose battle orders hold passes the turn, as the Pass key does.
    else if (turnBasedCombatRuntime.active() && attackResult.held)
    {
        runtime.passTurnBasedTurn();
    }

    return attackResult;
}

// Effects and the sound of a blink-like move (the monster blink's), from where the party left to where it arrived.
void queueTalentMovePresentation(IGameplayWorldRuntime &world, const std::array<float, 3> &from,
    const std::array<float, 3> &to)
{
    EventRuntimeState *pEvents = world.eventRuntimeState();
    if (pEvents == nullptr)
    {
        return;
    }
    for (const std::array<float, 3> &point : {from, to})
    {
        EventRuntimeState::WorldEffectRequest effect = {};
        effect.id = "openyamm:fx/arcane_pulse";
        effect.position = point;
        pEvents->worldEffectRequests.push_back(std::move(effect));
    }
    EventRuntimeState::PendingSound sound = {};
    sound.soundScope = SoundScope::World;
    sound.soundName = "monster_blink";
    sound.fallbackSoundName = "30teleport03";
    sound.x = int32_t(std::lround(to[0]));
    sound.y = int32_t(std::lround(to[1]));
    sound.z = int32_t(std::lround(to[2]));
    sound.positional = true;
    sound.hasExplicitZ = true;
    pEvents->pendingSounds.push_back(std::move(sound));
}

// The living hostiles a sweeping talent strikes (pickTalentTargets over the world's actors near the party).
std::vector<size_t> collectTalentTargets(IGameplayWorldRuntime &world, const GameplayPartyAttackFrameInput &attackInput,
    float reach, float arcDegrees, size_t maxCount)
{
    const GameplayWorldPoint party = attackInput.partyPosition;
    std::vector<TalentTargetCandidate> candidates;
    for (const size_t index : world.collectMapActorIndicesWithinRadius(
             party.x, party.y, party.z, reach + 512.0f, true, party.x, party.y, party.z))
    {
        const std::optional<GameplayPartyAttackActorFacts> facts = world.partyAttackActorFacts(index, false);
        if (!facts)
        {
            continue;
        }
        candidates.push_back({index, facts->position.x, facts->position.y, facts->position.z, float(facts->radius),
            !facts->isDead && facts->currentHp > 0 && facts->hostileToParty && !facts->isInvisible});
    }
    return pickTalentTargets(candidates, party.x, party.y, party.z, world.gameplayCameraYawRadians(), reach, arcDegrees,
        maxCount);
}

// Uses a talent from the action bar: what the status line says (a refusal or what happened; empty for nothing).
template <typename PickCurrentHit>
std::string useSoloTalent(GameplayScreenRuntime &runtime, GameplaySpellService &spellService,
    const GameplayInteractionController::HoverStateInput &standardHoverInput,
    const GameplaySpellActionController::TargetQueries &targetQueries,
    const GameplayWorldPickRequest &pickRequest, uint32_t talentIndex, PickCurrentHit &pickCurrentHit)
{
    IGameplayWorldRuntime *pWorld = runtime.worldRuntime();
    Party *pParty = pWorld != nullptr ? pWorld->party() : nullptr;
    const SoloTalentTable &table = soloTalentTable();
    if (pParty == nullptr || !runtime.soloTalents() || talentIndex >= table.talents().size()
        || runtime.turnBasedCombatRuntime().active())
    {
        return {};
    }
    const TalentDefinition &talent = table.talents()[talentIndex];
    Character *pMember = pParty->activeMember();
    const int rank = pMember != nullptr ? talentRank(*pMember, talent.id) : 0;
    if (pMember == nullptr || rank <= 0 || talent.kind != TalentKind::Active)
    {
        return {};
    }
    const std::string name = Engine::tr(talent.name);
    float &cooldown = pMember->talentState.cooldownSeconds[talent.id];
    if (cooldown > 0.0f)
    {
        return Engine::tr("{talent} is ready in {seconds} s",
            {{"talent", name}, {"seconds", int64_t(std::ceil(cooldown))}});
    }
    if (!GameMechanics::canTakeGameplayAction(*pMember) || pMember->recoverySecondsRemaining > 0.0f)
    {
        return {};
    }

    pickCurrentHit();
    const GameplayWorldHit crosshair = pWorld->pickPartyAttackTarget(pickRequest);
    const GameplayPartyAttackFrameInput attackInput = pWorld->buildPartyAttackFrameInput(pickRequest);
    const GameplayActionController::AttackActionDecision press = {.shouldAttemptAttack = true, .pressedThisFrame = true};
    const std::optional<size_t> crosshairActor = crosshair.kind == GameplayWorldHitKind::Actor && crosshair.actor
        ? std::optional<size_t>(crosshair.actor->actorIndex)
        : std::nullopt;
    const auto blow = [&](std::optional<size_t> actor, float share, bool extra, bool shot)
    {
        const TalentBlow talentBlow = {actor, share, extra, shot};
        return executePartyAttack(runtime, spellService, attackInput, standardHoverInput, targetQueries, press,
            actor ? GameplayWorldHit{} : crosshair, false, &talentBlow);
    };
    const float share = talent.share / 100.0f;
    const auto startCooldown = [&]() { cooldown = talentCooldownSeconds(talent, rank); };
    const auto showClip = [&](const char *pClip) { runtime.noteViewModelTalent(pClip); };
    // A talent's own sound (engine/audio/solo_talents/), from the party.
    const auto playTalentSound = [&](const char *pSound)
    {
        if (GameAudioSystem *pAudio = runtime.audioSystem())
        {
            pAudio->playSoundByName(pSound, GameAudioSystem::PlaybackGroup::World, SoundScope::Engine,
                GameAudioSystem::WorldPosition{pWorld->partyX(), pWorld->partyY(), pWorld->partyFootZ() + 96.0f});
        }
    };

    if (talent.id == "cleave")
    {
        // A burst: every monster in the arc takes the talent's share (150 %).
        constexpr float Reach = 407.2f;
        const size_t limit = size_t(std::max(1, talent.targets));
        std::vector<size_t> targets = collectTalentTargets(*pWorld, attackInput, Reach, talent.arc, limit);
        if (crosshairActor)
        {
            targets.erase(std::remove(targets.begin(), targets.end(), *crosshairActor), targets.end());
            targets.insert(targets.begin(), *crosshairActor);
            targets.resize(std::min(targets.size(), limit));
        }
        if (targets.empty())
        {
            return Engine::tr("Nothing in reach");
        }
        // The extra blows first: the one that pays the recovery (and plays the sound) puts the member into recovery,
        // and a recovering member strikes no more.
        for (size_t index = 1; index < targets.size(); ++index)
        {
            blow(targets[index], share, true, false);
        }
        blow(targets[0], share, false, false);
        playTalentSound("talent_cleave");
        startCooldown();
        showClip("cleave");
        return {};
    }
    if (talent.id == "multishot")
    {
        // 2/3/4 arrows over the cone; each hits the first monster in its line, so with fewer monsters than arrows the
        // nearest take several.
        constexpr float Reach = 5120.0f;
        const size_t arrows = size_t(std::max(1, talent.targets + int(talent.perRank) * (rank - 1)));
        std::vector<size_t> targets = collectTalentTargets(*pWorld, attackInput, Reach, talent.arc, arrows);
        if (crosshairActor)
        {
            targets.erase(std::remove(targets.begin(), targets.end(), *crosshairActor), targets.end());
            targets.insert(targets.begin(), *crosshairActor);
            targets.resize(std::min(targets.size(), arrows));
        }
        for (size_t arrow = 1; arrow < arrows && !targets.empty(); ++arrow)
        {
            blow(targets[arrow % targets.size()], share, true, true);
        }
        blow(targets.empty() ? std::nullopt : std::optional<size_t>(targets[0]), share, false, true);
        startCooldown();
        showClip("volley");
        return {};
    }
    if (talent.id == "binding_circle")
    {
        // Every hostile within the circle is held almost still (MAW's slow at a tenth) for the duration.
        const std::vector<size_t> held = collectTalentTargets(*pWorld, attackInput, talent.distance, 180.0f, 64);
        if (held.empty())
        {
            return Engine::tr("Nothing in reach");
        }
        for (const size_t actor : held)
        {
            pWorld->debuffActor(actor, GameplayActorHitDebuff::Slow, talentDurationSeconds(talent, rank), 10.0f);
        }
        startCooldown();
        showClip("binding_circle");
        return Engine::tr("{name}: Binding Circle", {{"name", pMember->name}});
    }
    if (talent.id == "pinning_shot")
    {
        const GameplayActionController::PartyAttackExecutionResult shot = blow(std::nullopt, 1.0f, false, true);
        if (shot.targetActorIndex)
        {
            pWorld->debuffActor(*shot.targetActorIndex, GameplayActorHitDebuff::Slow,
                talentDurationSeconds(talent, rank), 2.0f);
        }
        startCooldown();
        showClip("volley");
        return {};
    }
    if (talent.id == "charge")
    {
        GameplayRuntimeActorState target = {};
        if (!crosshairActor || !pWorld->actorRuntimeState(*crosshairActor, target) || target.isDead)
        {
            return Engine::tr("Charge needs a target");
        }
        const float dx = target.preciseX - pWorld->partyX();
        const float dy = target.preciseY - pWorld->partyY();
        const float distance = std::hypot(dx, dy);
        constexpr float StopShort = 260.0f;
        if (distance > talent.distance)
        {
            return Engine::tr("Out of range");
        }
        playTalentSound("talent_charge");
        if (distance > StopShort)
        {
            pWorld->dashParty(dx / distance, dy / distance, distance - StopShort);
        }
        blow(crosshairActor, 1.0f, false, false);
        pWorld->stunActor(*crosshairActor, talentDurationSeconds(talent, rank));
        startCooldown();
        showClip("charge");
        return {};
    }
    if (talent.id == "blink")
    {
        const float yaw = pWorld->gameplayCameraYawRadians();
        const std::array<float, 3> from = {pWorld->partyX(), pWorld->partyY(), pWorld->partyFootZ() + 96.0f};
        if (!pWorld->dashParty(std::cos(yaw), std::sin(yaw), talent.distance))
        {
            return Engine::tr("Cannot move there");
        }
        queueTalentMovePresentation(*pWorld, from,
            {from[0] + std::cos(yaw) * talent.distance, from[1] + std::sin(yaw) * talent.distance, from[2]});
        startCooldown();
        showClip("blink");
        return {};
    }
    if (talent.id == "shield_wall")
    {
        if (pMember->equipment.offHand == 0)
        {
            return Engine::tr("Shield Wall needs a shield");
        }
        pMember->talentState.shieldWallSeconds = talentDurationSeconds(talent, rank);
        startCooldown();
        showClip("shield_wall");
        return Engine::tr("{name}: Shield Wall", {{"name", pMember->name}});
    }
    if (talent.id == "spell_surge")
    {
        pMember->talentState.spellSurgeArmed = true;
        startCooldown();
        showClip("spell_surge");
        return Engine::tr("{name}: Spell Surge", {{"name", pMember->name}});
    }
    return {};
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
    runtime.clearWorldStatusBarHoverText();
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

    appendLearnedEventEffect(payload, *pWorldRuntime, input.pScreenRuntime);
    resolveWorldItemHoverName(payload, *pWorldRuntime, input.pScreenRuntime);
    const bool heldItemActive = input.pScreenRuntime != nullptr && input.pScreenRuntime->heldInventoryItem().active;
    const std::optional<std::string> statusText = resolveHoverStatusText(payload, heldItemActive);
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

    if (!keyboardRepeatInteractionDue(
        state.inspectKeyboardActivateLatch,
        state.inspectKeyboardActivateNextRepeatTickNanoseconds,
        input.currentTickNanoseconds))
    {
        return result;
    }

    result.latched = true;

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
    const GameplayHoverStatusPayload &payload,
    bool heldItemActive)
{
    const GameplayWorldHit &hit = payload.worldHit;

    if (!hit.hasHit)
    {
        return std::nullopt;
    }

    if (hit.kind == GameplayWorldHitKind::WorldItem)
    {
        if (!hit.worldItem || hit.worldItem->displayName.empty())
        {
            return std::nullopt;
        }

        const std::string itemName = Engine::localizeKnown(hit.worldItem->displayName);
        std::string text = !heldItemActive && hit.worldItem->distance < WorldItemGetStatusDistance
            ? Engine::tr("Get {item}", {{"item", itemName}})
            : itemName;

        // An item drawing the missing-model placeholder says so, so that players report it.
        if (hit.worldItem->missingGroundModelItemId != 0)
        {
            text = Engine::tr("{text} [missing 3D model for item {id} - please report]",
                {{"text", text}, {"id", hit.worldItem->missingGroundModelItemId}});
        }

        return text;
    }

    if (hit.kind == GameplayWorldHitKind::Actor)
    {
        if (!hit.actor || hit.actor->distance > ActorHoverStatusDistance || hit.actor->displayName.empty())
        {
            return std::nullopt;
        }

        return localizedActorName(hit.actor->displayName);
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

GameplayWorldHit GameplayInteractionController::pickKeyboardUseTarget(
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
    policy.attackPressed = input.keyboardAttackPressed && !input.rightMousePressed;
    return policy;
}

bool GameplayInteractionController::stealClickPressed(
    const GameplayInputFrame &input,
    const WorldInteractionPointerPolicy &pointerPolicy)
{
    return input.leftMouseButton.pressed
        && (pointerPolicy.leftMousePressed || pointerPolicy.useCenterGameplayPoint)
        && (input.isScancodeHeld(SDL_SCANCODE_LCTRL) || input.isScancodeHeld(SDL_SCANCODE_RCTRL));
}

bool GameplayInteractionController::stealClickHoldsAttack(
    bool &stealClickLatch,
    const GameplayInputFrame &input,
    bool stealPressed)
{
    if (stealPressed)
    {
        stealClickLatch = true;
    }
    else if (!input.leftMouseButton.held)
    {
        stealClickLatch = false;
    }

    return stealClickLatch;
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
    // A click on the quick item ring is its own: Attack on the left button must not attack as well.
    // So is the solo bar selector's (the Ctrl click that opened it, the click that closed it).
    const bool keyboardUsePressed = input.action(KeyboardAction::Trigger).held
        && !GameplayQuickItems::takesPointerAction(runtime, KeyboardAction::Trigger)
        && !GameplaySoloBarSelector::takesPointerAction(runtime, KeyboardAction::Trigger);
    const bool usePressed = input.action(KeyboardAction::Use).held
        && !GameplayQuickItems::takesPointerAction(runtime, KeyboardAction::Use)
        && !GameplaySoloBarSelector::takesPointerAction(runtime, KeyboardAction::Use);
    const bool attackPressed = input.action(KeyboardAction::Attack).held
        && !GameplayQuickItems::takesPointerAction(runtime, KeyboardAction::Attack)
        && !GameplaySoloBarSelector::takesPointerAction(runtime, KeyboardAction::Attack);
    const bool leftMousePressed = input.leftMouseButton.held && !GameplayQuickItems::takesPointer(runtime)
        && !GameplaySoloBarSelector::takesPointer(runtime);
    const bool rightMousePressed = input.rightMouseButton.held;
    const bool mouseLookActive = sharedInput.mouseLookPolicy.mouseLookActive;
    const bool cursorModeActive = sharedInput.mouseLookPolicy.cursorModeActive;
    // A combatant: the members' portraits and the MM9 hirelings' faces (a spell's character target).
    const std::optional<size_t> hoveredPortraitMemberIndex =
        runtime.resolveCombatantPortraitIndexAtPoint(
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
                .pointerX = input.pointerX,
                .pointerY = input.pointerY,
                .screenWidth = screenWidth,
                .screenHeight = screenHeight,
                .pointerOverPortrait = hoveredPortraitMemberIndex.has_value(),
            });
    const GameplaySpellActionController::TargetQueries targetQueries =
        buildSpellActionTargetQueries(screenState, input);

    const uint64_t currentTickNanoseconds = SDL_GetTicksNS();

    // A steal click holds the attack back only while its button stays down, also when the release lands on a frame
    // that returns early below (an overlay opened with the button still held).
    if (!input.leftMouseButton.held)
    {
        worldInteractionInputState.stealClickLatch = false;
        worldInteractionInputState.smartClick = GameplayScreenState::WorldInteractionInputState::SmartClick::None;
    }

    if (worldInputBlocked)
    {
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
        const bool preserveHeldItemDropAction =
            heldItemActive
            && overlayInteractionState.gameplayHudClickLatch
            && overlayInteractionState.gameplayHudPressedTarget.type
                == GameplayHudPointerTargetType::ContextActionButton
            && overlayInteractionState.gameplayHudPressedContextActionActive;
#endif
        clearWorldInteractionFrameState(screenState, overlayInteractionState, runtime);
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
        if (preserveHeldItemDropAction)
        {
            setHeldItemDropContextAction(runtime);
        }
#endif
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
        pendingSpellHoverInput.pScreenRuntime = &runtime;
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

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
        const bool mobileGroundTargetConfirmSpell = usesMobileGroundTargetConfirm(pendingSpellCast.spellId);
#else
        const bool mobileGroundTargetConfirmSpell = false;
#endif

        if (mobileGroundTargetConfirmSpell
            && pendingSpellCast.targetKind == PartySpellCastTargetKind::GroundPoint
            && !confirmFromMobileHudButton
            && input.leftMouseButton.held
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
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
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
            if (confirmFromPointer)
            {
                attackActionState.suppressAttackUntilRelease = true;
            }

            IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

            if (pWorldRuntime != nullptr)
            {
                pWorldRuntime->applyPendingSpellCastWorldEffects(pendingTargetResult.castResult);
            }

            clearWorldHover(pWorldRuntime);
        }

        worldInteractionInputState.keyboardUseLatch = false;
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
        keyboardUseHit = pickKeyboardUseTarget(*pWorldRuntime, keyboardUsePickRequest);
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
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
        if (overlayInteractionState.gameplayHudDropHeldItemRequested)
        {
            overlayInteractionState.gameplayHudDropHeldItemRequested = false;
            dropHeldItemInFrontOfParty(runtime);
            runtime.clearContextActionState();
            result.heldItemHandled = true;
            return result;
        }

        setHeldItemDropContextAction(runtime);
#else
        runtime.clearContextActionState();
#endif
        // Use puts the held item (such as one taken from a loot bag) into the packs instead of dropping it.
        if (input.action(KeyboardAction::Use).pressed
            && !GameplayQuickItems::takesPointerAction(runtime, KeyboardAction::Use))
        {
            runtime.tryStowHeldInventoryItemInParty();
            worldInteractionInputState.heldInventoryDropLatch = false;
            // The press is spent: holding Use on must not activate what is under the crosshair once the cursor is
            // empty, until the key is released.
            worldInteractionInputState.inspectKeyboardActivateLatch = true;
            worldInteractionInputState.inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
            result.heldItemHandled = true;
            return result;
        }

        GameplayWorldHit heldItemWorldHit = {};
        bool hasHeldItemWorldHit = false;

#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
        const bool heldItemPointerPressed = false;
        worldInteractionInputState.heldInventoryDropLatch = false;
#else
        const bool heldItemPointerPressed = pointerPolicy.leftMousePressed;
#endif

        if (!heldItemPointerPressed
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
                    .leftMousePressed = heldItemPointerPressed,
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

    overlayInteractionState.gameplayHudDropHeldItemRequested = false;

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
    standardHoverInput.pScreenRuntime = &runtime;
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
            contextActionState.visible ? ContextActionRefreshNanoseconds : ContextActionIdleRetryNanoseconds;
        const bool contextActionRayOriginChanged =
            contextActionPickRayOriginChanged(contextActionState, currentInteractionPickRequest);
        const bool contextActionRayDirectionChanged =
            contextActionPickRayDirectionChanged(contextActionState, currentInteractionPickRequest);
        const uint64_t effectiveRefreshIntervalNanoseconds = contextActionRayDirectionChanged
            ? ContextActionDirectionRefreshNanoseconds
            : (contextActionRayOriginChanged
                ? ContextActionRefreshNanoseconds
                : contextActionRefreshIntervalNanoseconds);
        const bool contextActionRefreshDue =
            contextActionState.lastUpdateNanoseconds == 0
            || currentTickNanoseconds < contextActionState.lastUpdateNanoseconds
            || currentTickNanoseconds - contextActionState.lastUpdateNanoseconds
                >= effectiveRefreshIntervalNanoseconds;

        if (contextActionRefreshDue)
        {
            std::optional<GameplayContextAction> contextAction =
                buildContextAction(*pWorldRuntime, result.hover.worldHit, result.hover.eventTargetStatusText);

            if (!contextAction)
            {
                contextActionHit =
                    pickKeyboardUseTarget(*pWorldRuntime, currentInteractionPickRequest);

                if (isSameActivationTarget(contextActionHit, result.hover.worldHit))
                {
                    contextActionEventStatusText = result.hover.eventTargetStatusText;
                }

                contextAction = buildContextAction(*pWorldRuntime, contextActionHit, contextActionEventStatusText);
            }

            setSingleContextAction(
                runtime,
                contextAction,
                currentTickNanoseconds,
                currentInteractionPickRequest);
        }
        else
        {
            const bool visibleActionInvalid = contextActionState.visible
                && contextActionState.primaryIndex >= contextActionState.actions.size();
            const bool visibleActionNoLongerActivatable = contextActionState.visible
                && !visibleActionInvalid
                && !pWorldRuntime->canActivateWorldHit(
                    contextActionState.actions[contextActionState.primaryIndex].worldHit,
                    GameplayInteractionMethod::Keyboard);

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

    const bool stealPressed = stealClickPressed(input, pointerPolicy);
    bool activationPressed = pointerPolicy.activationPressed;
    bool attackPressedNow = pointerPolicy.attackPressed;
    // The smart left click: the left button's Attack (Modern) or Use (Classic) uses what is under the cursor or
    // crosshair when Use could act on it, and attacks otherwise. The choice is made on the press and kept while the
    // button is held, so a held attack keeps striking; the other action keeps its own key.
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    const bool smartClickEnabled = false;
#else
    const bool smartClickEnabled = runtime.settingsSnapshot().smartClick;
#endif
    const InputBinding leftButton = mouseButtonInputBinding(SDL_BUTTON_LEFT);
    const InputBinding attackBinding = runtime.settingsSnapshot().keyboard.binding(KeyboardAction::Attack);
    const InputBinding useBinding = runtime.settingsSnapshot().keyboard.binding(KeyboardAction::Use);
    const bool leftAttacks =
        attackBinding.kind == leftButton.kind && attackBinding.mouseButton == leftButton.mouseButton;
    const bool leftUses = useBinding.kind == leftButton.kind && useBinding.mouseButton == leftButton.mouseButton;

    if (smartClickEnabled && (leftAttacks || leftUses))
    {
        using SmartClick = GameplayScreenState::WorldInteractionInputState::SmartClick;
        SmartClick &smartClick = worldInteractionInputState.smartClick;
        const bool leftPressed = input.leftMouseButton.held && (leftAttacks ? attackPressedNow : activationPressed);

        if (!leftPressed)
        {
            smartClick = SmartClick::None;
        }
        else if (smartClick == SmartClick::None)
        {
            // A steal click (Ctrl) stays an attack, which the steal then holds back until the button is released.
            const GameplayWorldHit hit = stealPressed ? GameplayWorldHit{} : pickCurrentHit();
            const bool usable = hit.hasHit
                && pWorldRuntime != nullptr
                && pWorldRuntime->canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard);
            smartClick = usable ? SmartClick::Use : SmartClick::Attack;
        }

        const bool smartUse = smartClick == SmartClick::Use;
        const bool smartAttack = smartClick == SmartClick::Attack;
        activationPressed = leftUses ? smartUse : activationPressed || smartUse;
        attackPressedNow = leftAttacks ? smartAttack : attackPressedNow || smartAttack;
    }

    const bool worldAttackPressed =
        attackPressedNow
        && !stealClickHoldsAttack(worldInteractionInputState.stealClickLatch, input, stealPressed);

    if (worldAttackPressed
        || pointerPolicy.leftMousePressed
        || stealPressed
        || worldInteractionInputState.inspectMouseActivateLatch)
    {
        pickCurrentHit();
    }

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

    GameplayWorldHit keyboardActivationHit = {};

    // Use activates only what is under the cursor or crosshair. Unlike Trigger and the context popup, it never
    // falls back to the nearest interactable on screen.
    if (activationPressed && worldReady && pWorldRuntime != nullptr)
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
        keyboardActivationHit = pWorldRuntime->pickMouseInteractionTarget(keyboardActivationPickRequest);
    }

    const KeyboardActivationInteractionResult keyboardActivationResult =
        updateKeyboardActivationInteraction(
            worldInteractionInputState,
            KeyboardActivationInteractionInput{
                .activationPressed = activationPressed,
                .allowInteraction = worldReady,
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
    else if (!activationPressed)
    {
        overlayInteractionState.activateInspectLatch = false;
    }

    if (keyboardActivationResult.activated)
    {
        result.keyboardActivationActivated = true;
        refreshWorldHover(standardHoverInput, pWorldRuntime);
        runtime.clearContextActionState();
    }

    const GameplayActionController::AttackActionDecision attackActionDecision =
        GameplayActionController::updateAttackAction(
            attackActionState,
            quickSpellState,
            GameplayActionController::AttackActionConfig{
                .attackPressed = worldAttackPressed,
                .hasReadyMember = hasReadyMember,
                .turnBased = runtime.turnBasedCombatRuntime().active(),
                .fastRepeat = runtime.settingsSnapshot().fastAttackRepeat,
            });

    const auto runPartyAttack = [&](const GameplayActionController::AttackActionDecision &decision, bool swingShown)
    {
        pickCurrentHit();
        const GameplayWorldHit attackHit = pWorldRuntime != nullptr
            ? pWorldRuntime->pickPartyAttackTarget(currentInteractionPickRequest)
            : currentHit;
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
            decision,
            attackHit,
            swingShown);
    };

    // A solo dragon whose target is out of claw reach breathes at once, as a party dragon does: no swing and no
    // inhale (devdocs/solo_action/DRAGON.md). Battle orders holding a spell show that cast instead, as below.
    const auto soloDragonBreathesNow = [&]() -> bool
    {
        const Party *pParty = pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
        const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
        if (pMember == nullptr || soloBowDrawn(runtime, pMember)
            || std::any_of(pMember->battleOrders.begin(), pMember->battleOrders.end(), [](const BattleOrder &order)
                { return order.enabled && order.kind == BattleOrderKind::Spell; }))
        {
            return false;
        }
        const CharacterAttackProfile profile = GameMechanics::buildCharacterAttackProfile(
            *pMember,
            runtime.itemTable(),
            runtime.spellTable(),
            characterAttackTuningFromSettings(runtime.settingsSnapshot()));
        pickCurrentHit();
        return soloDragonBreathes(*pWorldRuntime, *pParty, *pMember, profile,
            pWorldRuntime->pickPartyAttackTarget(currentInteractionPickRequest), currentInteractionPickRequest);
    };

    // The prototype view model's swing: a melee attack starts it and lands at its blow, against what is in reach
    // then (GameplayScreenRuntime::ViewModelLink). A swing under way takes further presses.
    GameplayScreenRuntime::ViewModelLink &viewModel = runtime.viewModelLink();
    if (attackActionDecision.shouldAttemptAttack)
    {
        if (viewModel.swingWaiting)
        {
            result.attackAttempted = true;
        }
        else if (viewModel.meleeSwings && hasReadyMember && !runtime.turnBasedCombatRuntime().active()
                 && pWorldRuntime != nullptr && pWorldRuntime->party() != nullptr
                 && pWorldRuntime->party()->activeMember() != nullptr
                 && !GameMechanics::canTakeGameplayAction(*pWorldRuntime->party()->activeMember()))
        {
            // The active member is still recovering: the press waits (a held key retries), no swing is shown.
            result.attackAttempted = true;
        }
        else if (viewModel.meleeSwings && hasReadyMember && !runtime.turnBasedCombatRuntime().active()
                 && soloDragonBreathesNow())
        {
            runPartyAttack(attackActionDecision, false);
        }
        else if (viewModel.meleeSwings && hasReadyMember && !runtime.turnBasedCombatRuntime().active())
        {
            viewModel.swingWaiting = true;
            viewModel.blowReleased = false;
            viewModel.blowDirection.reset();
            viewModel.swingWaitSeconds = 0.0f;
            viewModel.swingRecoverySeconds = 0.0f;
            viewModel.waitIsCast = false;
            viewModel.quickCastWaiting = false;
            result.attackAttempted = true;
            const Party *pSwingParty = pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
            const Character *pAttacker = pSwingParty != nullptr ? pSwingParty->activeMember() : nullptr;
            // An Attack whose battle orders hold a spell shows that spell's cast (the first enabled one; the orders
            // still decide at the release what is done, as they would at the press).
            if (pAttacker != nullptr)
            {
                for (const BattleOrder &order : pAttacker->battleOrders)
                {
                    if (order.enabled && order.kind == BattleOrderKind::Spell
                        && GameplaySpellActionController::prepareViewModelCast(runtime, *pAttacker, order.spellName))
                    {
                        viewModel.waitIsCast = true;
                        break;
                    }
                }
            }
            if (pAttacker != nullptr && runtime.itemTable() != nullptr)
            {
                // The weapon's strongest element tints the swing's trail.
                ElementalDamageBonuses elements = ItemEnchantRuntime::characterAttackElementalDamageRange(
                    *pAttacker, CharacterAttackMode::Melee, runtime.itemTable(), runtime.specialItemEnchantTable())
                                                      .maximum;
                elements += ItemEnchantRuntime::characterWeaponDamageElements(
                    *pAttacker, CharacterAttackMode::Melee, runtime.itemTable());
                const std::vector<MeleeWeaponElement> weaponElements = meleeWeaponElementsFor(elements);
                viewModel.weaponElement = uint8_t(weaponElements.empty() ? MeleeWeaponElement::None
                                                                         : weaponElements.front());
            }
            ++viewModel.swingSerial;
            // The swing (or the drawn bow's shot) fits the member's recovery for it; a swing's whoosh plays now
            // rather than at the blow, while the bow sounds as the arrow leaves.
            if (const Character *pMember = viewModel.waitIsCast ? nullptr : pAttacker)
            {
                const bool shot = soloBowDrawn(runtime, pMember);
                const CharacterAttackProfile profile = GameMechanics::buildCharacterAttackProfile(
                    *pMember,
                    runtime.itemTable(),
                    runtime.spellTable(),
                    characterAttackTuningFromSettings(runtime.settingsSnapshot()));
                viewModel.swingRecoverySeconds = shot ? profile.rangedRecoverySeconds : profile.meleeRecoverySeconds;
                // Rules that decide the recovery themselves (MAW: weapon delay, speed, Haste) give theirs, in the
                // original's ticks (128 per 2.13 s of real time, as MawCombatRules turns them into seconds).
                if (runtime.itemTable() != nullptr)
                {
                    if (const std::optional<int> ticks = gameRulesFor(pSwingParty).combat.characterAttackRecoveryTicks(
                            *pMember,
                            shot ? CharacterAttackMode::Bow : CharacterAttackMode::Melee,
                            *runtime.itemTable(), runtime.standardItemEnchantTable(),
                            runtime.specialItemEnchantTable()))
                    {
                        constexpr float RealtimeSecondsPerTick = 2.133333333333333f / 128.0f;
                        viewModel.swingRecoverySeconds = float(*ticks) * RealtimeSecondsPerTick;
                    }
                }
                if (!shot)
                {
                    GameplayActionController::playMeleeSwingSound(
                        runtime, *pMember, runtime.itemTable(), pWorldRuntime->partyX(), pWorldRuntime->partyY(),
                        pWorldRuntime->partyFootZ() + 96.0f);
                }
            }
        }
        else
        {
            runPartyAttack(attackActionDecision, false);
        }
    }
    // A blow the view model never reports (its clip missing, the view model gone) still lands, after two seconds of
    // game time (the view model counts it).
    constexpr float SwingTimeoutSeconds = 2.0f;
    if (viewModel.swingWaiting && !viewModel.quickCastWaiting
        && (viewModel.blowReleased || viewModel.swingWaitSeconds > SwingTimeoutSeconds))
    {
        viewModel.swingWaiting = false;
        if (viewModel.waitIsCast)
        {
            // A cast's recovery counts from the press too: the time the clip took comes off whatever the attack set
            // (the blow path is told nothing, so a fallback blow is not shortened twice).
            const float spent = viewModel.swingWaitSeconds;
            viewModel.swingWaitSeconds = 0.0f;
            runPartyAttack({.shouldAttemptAttack = true, .pressedThisFrame = true}, true);
            Party *pCastParty = pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
            Character *pCaster =
                pCastParty != nullptr ? pCastParty->member(pCastParty->activeMemberIndex()) : nullptr;
            if (pCaster != nullptr)
            {
                pCaster->recoverySecondsRemaining = std::max(0.0f, pCaster->recoverySecondsRemaining - spent);
            }
        }
        else
        {
            runPartyAttack({.shouldAttemptAttack = true, .pressedThisFrame = true}, true);
        }
        viewModel.blowDirection.reset();
    }

    // A solo run's talent from the action bar (devdocs/solo_action/TALENTS.md).
    if (overlayInteractionState.soloTalentRequested)
    {
        const uint32_t talentIndex = *overlayInteractionState.soloTalentRequested;
        overlayInteractionState.soloTalentRequested.reset();
        const std::string status = useSoloTalent(runtime, spellService, standardHoverInput, targetQueries,
            currentInteractionPickRequest, talentIndex, pickCurrentHit);
        if (!status.empty())
        {
            runtime.setStatusBarEvent(status);
        }
        result.attackAttempted = true;
    }

    // A solo run's weapon swap (its key or the action bar's swap slot): the arms draw the bow instead of the melee
    // weapon, or back, and with the bow drawn Attack shoots even at melee range. Not while a swing waits for its blow.
    const bool swapRequested = input.action(KeyboardAction::SwapWeapon).pressed
        || std::exchange(runtime.interactionState().soloWeaponSwapRequested, false);
    if (swapRequested && runtime.soloRun() && !viewModel.swingWaiting && pWorldRuntime != nullptr
        && pWorldRuntime->party() != nullptr)
    {
        const Character *pMember = pWorldRuntime->party()->activeMember();
        if (pMember != nullptr && pMember->equipment.bow != 0 && !pMember->equipmentRuntime.bow.broken)
        {
            viewModel.bowSelected = !viewModel.bowSelected;
        }
    }

    // MAW's Knight Charge: a lone Knight dashes at the monster under the cursor.
    if (input.action(KeyboardAction::KnightCharge).pressed && pWorldRuntime != nullptr
        && pWorldRuntime->party() != nullptr)
    {
        pickCurrentHit();
        const GameplayWorldHit chargeHit = pWorldRuntime->pickPartyAttackTarget(currentInteractionPickRequest);
        const std::optional<size_t> targetActorIndex =
            chargeHit.kind == GameplayWorldHitKind::Actor && chargeHit.actor
                ? std::optional<size_t>(chargeHit.actor->actorIndex)
                : std::nullopt;
        const std::optional<std::string> status =
            GameplayActionController::tryPartyCharge(*pWorldRuntime->party(), *pWorldRuntime, targetActorIndex);

        if (status && !status->empty())
        {
            runtime.setStatusBarEvent(*status);
        }
    }

    // The quick item ring or popup hides the world's hover text: its plate would lie over the ring's lowest slot.
    if (GameplayQuickItems::needsCursor(runtime) || GameplayFormationBuilder::isOpen(runtime))
    {
        runtime.clearWorldStatusBarHoverText();
        runtime.setWorldItemHoverLabel({}, 0, 0, 0);
    }
    // A solo run's bar slot under the free pointer says how to choose what goes on its key.
    else if (const std::string barHint = !mouseLookActive || cursorModeActive
                 ? GameplaySoloBarSelector::barHoverText(runtime, input.screenWidth, input.screenHeight,
                       input.pointerX, input.pointerY)
                 : std::string();
             !barHint.empty())
    {
        runtime.setStatusBarHoverText(barHint);
        runtime.setWorldItemHoverLabel({}, 0, 0, 0);
    }
    else
    {
        runtime.setWorldStatusBarHoverText(result.hover.statusText);
        updateWorldItemHoverLabel(
            runtime, pWorldRuntime, result.hover, pointerPolicy.inspectScreenX, pointerPolicy.inspectScreenY);
    }

    return result;
}

bool GameplayInteractionController::dropHeldItemInFrontOfParty(GameplayScreenRuntime &runtime)
{
    const IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const std::optional<GameplayHeldItemDropRequest> dropRequest =
        pWorldRuntime != nullptr ? pWorldRuntime->buildHeldItemDropRequest() : std::nullopt;
    return dropHeldItemToActiveWorld(runtime, dropRequest);
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
