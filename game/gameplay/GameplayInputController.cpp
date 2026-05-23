#include "game/gameplay/GameplayInputController.h"

#include "game/audio/GameAudioSystem.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/app/GameSettings.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ArpgAetherRayRange = 1495.0f;
constexpr float ArpgAetherRaySourceHeight = 112.0f;
constexpr float ArpgAetherRayVisualRadius = 54.0f;
constexpr float ArpgAetherRayHitRadius = 82.0f;
constexpr float ArpgAetherRayDamageTickSeconds = 0.05f;
constexpr float ArpgAetherRayManaTickSeconds = 0.25f;
constexpr float ArpgAetherRayChannelAnimationSeconds = 0.55f;
constexpr int ArpgAetherRayManaPerTick = 1;
constexpr int ArpgAetherRayDamagePerTick = 2;
constexpr uint32_t ArpgAetherRayChannelSoundId = 49999u;
constexpr uint32_t ArpgAetherRayStableFxId = 0xa37e4121u;

uint32_t makeInputFxAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

float pointSegmentDistanceSquared(
    const GameplayWorldPoint &point,
    const GameplayWorldPoint &start,
    const GameplayWorldPoint &end)
{
    const float segmentX = end.x - start.x;
    const float segmentY = end.y - start.y;
    const float segmentZ = end.z - start.z;
    const float segmentLengthSquared = segmentX * segmentX + segmentY * segmentY + segmentZ * segmentZ;

    if (segmentLengthSquared <= 0.000001f)
    {
        const float deltaX = point.x - start.x;
        const float deltaY = point.y - start.y;
        const float deltaZ = point.z - start.z;
        return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
    }

    const float startToPointX = point.x - start.x;
    const float startToPointY = point.y - start.y;
    const float startToPointZ = point.z - start.z;
    const float t =
        std::clamp(
            (startToPointX * segmentX + startToPointY * segmentY + startToPointZ * segmentZ)
            / segmentLengthSquared,
            0.0f,
            1.0f);
    const float closestX = start.x + segmentX * t;
    const float closestY = start.y + segmentY * t;
    const float closestZ = start.z + segmentZ * t;
    const float deltaX = point.x - closestX;
    const float deltaY = point.y - closestY;
    const float deltaZ = point.z - closestZ;
    return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
}

bool isActionNewlyPressed(GameplayScreenRuntime &context, KeyboardAction action, const bool *pKeyboardState)
{
    if (pKeyboardState == nullptr)
    {
        return false;
    }

    const SDL_Scancode scancode = context.mutableSettings().keyboard.keyboardBinding(action);

    if (scancode <= SDL_SCANCODE_UNKNOWN || scancode >= SDL_SCANCODE_COUNT)
    {
        return false;
    }

    return pKeyboardState[scancode] && context.previousKeyboardState()[scancode] == 0;
}

bool isActionNewlyPressed(
    GameplayScreenRuntime &context,
    KeyboardAction action,
    const GameplayInputFrame *pInputFrame,
    const bool *pKeyboardState)
{
    if (pInputFrame != nullptr)
    {
        return pInputFrame->action(action).pressed;
    }

    return isActionNewlyPressed(context, action, pKeyboardState);
}

bool isActionHeld(
    GameplayScreenRuntime &context,
    KeyboardAction action,
    const GameplayInputFrame *pInputFrame,
    const bool *pKeyboardState)
{
    if (pInputFrame != nullptr)
    {
        return pInputFrame->action(action).held;
    }

    return context.mutableSettings().keyboard.isPressed(action, pKeyboardState);
}

bool isScancodeHeld(
    SDL_Scancode scancode,
    const GameplayInputFrame *pInputFrame,
    const bool *pKeyboardState)
{
    if (pInputFrame != nullptr)
    {
        return pInputFrame->isScancodeHeld(scancode);
    }

    return pKeyboardState != nullptr
        && scancode > SDL_SCANCODE_UNKNOWN
        && scancode < SDL_SCANCODE_COUNT
        && pKeyboardState[scancode];
}

bool isEscapeNewlyPressed(GameplayScreenRuntime &context, const bool *pKeyboardState)
{
    return pKeyboardState != nullptr
        && pKeyboardState[SDL_SCANCODE_ESCAPE]
        && context.previousKeyboardState()[SDL_SCANCODE_ESCAPE] == 0;
}

uint32_t mixAetherRayDamageTickRoll(uint32_t tickSequence, size_t actorIndex)
{
    uint32_t value = tickSequence ^ 0x9e3779b9u;
    value ^= static_cast<uint32_t>(actorIndex) + 0x85ebca6bu + (value << 6) + (value >> 2);
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return value;
}

void stopArpgAetherRaySound(GameplayScreenState::ArpgAetherRayState &rayState, GameplayScreenRuntime &context)
{
    if (rayState.channelSoundInstanceId == 0 || context.audioSystem() == nullptr)
    {
        rayState.channelSoundInstanceId = 0;
        return;
    }

    context.audioSystem()->stopSoundInstance(rayState.channelSoundInstanceId);
    rayState.channelSoundInstanceId = 0;
}

void clearArpgAetherRayChannel(GameplayScreenState::ArpgAetherRayState &rayState, GameplayScreenRuntime &context)
{
    const bool wasChanneling = rayState.active;
    stopArpgAetherRaySound(rayState, context);

    if (wasChanneling && context.worldRuntime() != nullptr)
    {
        context.worldRuntime()->cancelArpgModePartyActionAnimation();
    }

    rayState.clear();
}

void suspendArpgAetherRayChannelForMana(
    GameplayScreenState::ArpgAetherRayState &rayState,
    GameplayScreenRuntime &context)
{
    const bool wasChanneling = rayState.active;
    stopArpgAetherRaySound(rayState, context);

    if (wasChanneling && context.worldRuntime() != nullptr)
    {
        context.worldRuntime()->cancelArpgModePartyActionAnimation();
    }

    rayState.active = false;
    rayState.damageTickAccumulatorSeconds = 0.0f;
    rayState.manaTickAccumulatorSeconds = 0.0f;
}

bool closeActiveLootViewFromEscape(GameplayScreenRuntime &context, IGameplayWorldRuntime &worldRuntime)
{
    if (worldRuntime.activeChestView() == nullptr && worldRuntime.activeCorpseView() == nullptr)
    {
        return false;
    }

    if (context.inventoryNestedOverlay().active)
    {
        context.closeInventoryNestedOverlay();
    }
    else
    {
        if (worldRuntime.activeChestView() != nullptr)
        {
            context.playCommonUiSound(SoundId::ChestClose);
        }

        worldRuntime.closeActiveChestView();
        worldRuntime.closeActiveCorpseView();
        context.interactionState().activateInspectLatch = true;
        context.interactionState().chestSelectionIndex = 0;
    }

    context.interactionState().menuToggleLatch = true;
    context.interactionState().closeOverlayLatch = true;
    return true;
}

std::optional<size_t> nextSelectableMemberIndex(const Party &party, bool requireGameplayReady)
{
    const size_t memberCount = party.members().size();

    for (size_t offset = 1; offset <= memberCount; ++offset)
    {
        const size_t memberIndex = (party.activeMemberIndex() + offset) % memberCount;

        if (!requireGameplayReady || party.canSelectMemberInGameplay(memberIndex))
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

GameplaySpellActionController::TargetQueries buildSpellActionTargetQueries(
    const GameplayScreenState &screenState,
    const GameplaySharedInputFrameConfig &config)
{
    const GameplayScreenState::GameplayMouseLookState &mouseLookState = screenState.gameplayMouseLookState();

    GameplaySpellActionController::TargetQueries targetQueries = {};
    targetQueries.useCrosshairTarget =
        mouseLookState.mouseLookActive
        && !mouseLookState.cursorModeActive
        && config.screenWidth > 0
        && config.screenHeight > 0;
    targetQueries.cursorX = config.pointerX;
    targetQueries.cursorY = config.pointerY;
    targetQueries.screenWidth = static_cast<float>(config.screenWidth);
    targetQueries.screenHeight = static_cast<float>(config.screenHeight);
    return targetQueries;
}

void faceArpgAetherRayTarget(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldPoint &target)
{
    PartySpellCastRequest facingRequest = {};
    facingRequest.hasTargetPoint = true;
    facingRequest.targetX = target.x;
    facingRequest.targetY = target.y;
    facingRequest.targetZ = target.z;
    worldRuntime.faceArpgModePartyActionTarget(facingRequest);
}

void applyArpgAetherRayDamageTick(
    IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldPoint &source,
    const GameplayWorldPoint &end,
    uint32_t damageTickSequence)
{
    const size_t actorCount = worldRuntime.mapActorCount();

    for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
    {
        GameplayRuntimeActorState actor = {};

        if (!worldRuntime.actorRuntimeState(actorIndex, actor)
            || actor.isDead
            || actor.isInvisible)
        {
            continue;
        }

        const float actorMinZ = actor.preciseZ - 48.0f;
        const float actorMaxZ = actor.preciseZ + static_cast<float>(actor.height) + 48.0f;

        if (source.z < actorMinZ && end.z < actorMinZ)
        {
            continue;
        }

        if (source.z > actorMaxZ && end.z > actorMaxZ)
        {
            continue;
        }

        GameplayWorldPoint actorPoint = {};
        actorPoint.x = actor.preciseX;
        actorPoint.y = actor.preciseY;
        actorPoint.z = source.z;

        const float hitRadius = ArpgAetherRayHitRadius + std::max(24.0f, static_cast<float>(actor.radius));
        const float distanceSquared = pointSegmentDistanceSquared(actorPoint, source, end);

        if (distanceSquared > hitRadius * hitRadius)
        {
            continue;
        }

        const bool allowHitReaction =
            (mixAetherRayDamageTickRoll(damageTickSequence, actorIndex) % 100u) < 5u;
        worldRuntime.applyPartyChannelDamage(
            actorIndex,
            ArpgAetherRayDamagePerTick,
            source,
            allowHitReaction);
    }

}

void updateArpgAetherRayChannel(
    GameplayScreenState &screenState,
    GameplayScreenRuntime &context,
    const GameplaySharedInputFrameConfig &config,
    bool canRunStandardGameplayAction,
    bool blockedByOverlay)
{
    GameplayScreenState::ArpgAetherRayState &rayState = screenState.arpgAetherRayState();
    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    Party *pParty = context.party();
    Character *pCaster = pParty != nullptr ? pParty->activeMember() : nullptr;
    const bool channelHeld =
        context.settingsSnapshot().arpgModeEnabled
        && config.pInputFrame != nullptr
        && config.pInputFrame->isScancodeHeld(SDL_SCANCODE_F);

    if (!channelHeld
        || !canRunStandardGameplayAction
        || blockedByOverlay
        || !config.hasReadyMember
        || pWorldRuntime == nullptr
        || pCaster == nullptr)
    {
        clearArpgAetherRayChannel(rayState, context);
        return;
    }

    if (pCaster->spellPoints < ArpgAetherRayManaPerTick)
    {
        if (!rayState.manaWarningLatch)
        {
            context.setStatusBarEvent("Not enough spell points.");
            rayState.manaWarningLatch = true;
        }

        suspendArpgAetherRayChannelForMana(rayState, context);
        return;
    }

    rayState.manaWarningLatch = false;

    if (!rayState.active)
    {
        rayState.active = true;
        rayState.immediateDamageTickPending = true;
        rayState.damageTickAccumulatorSeconds = 0.0f;
        rayState.manaTickAccumulatorSeconds = ArpgAetherRayManaTickSeconds;
    }

    GameplayWorldPoint source = {};
    source.x = pWorldRuntime->partyX();
    source.y = pWorldRuntime->partyY();
    source.z = pWorldRuntime->partyFootZ() + ArpgAetherRaySourceHeight;

    if (rayState.channelSoundInstanceId == 0 && context.audioSystem() != nullptr)
    {
        rayState.channelSoundInstanceId =
            context.audioSystem()->playSoundInstance(
                engineSound(ArpgAetherRayChannelSoundId),
                GameAudioSystem::PlaybackGroup::World,
                std::nullopt,
                true);
    }

    const GameplaySpellActionController::TargetQueries targetQueries =
        buildSpellActionTargetQueries(screenState, config);
    const float targetScreenX =
        targetQueries.useCrosshairTarget && targetQueries.screenWidth > 0.0f
            ? targetQueries.screenWidth * 0.5f
            : targetQueries.cursorX;
    const float targetScreenY =
        targetQueries.useCrosshairTarget && targetQueries.screenHeight > 0.0f
            ? targetQueries.screenHeight * 0.5f
            : targetQueries.cursorY;
    std::optional<bx::Vec3> targetPoint;

    targetPoint =
        pWorldRuntime->spellActionCursorPlaneTargetPoint(
            targetScreenX,
            targetScreenY,
            source.z,
            ArpgAetherRayRange);

    float yawRadians = pWorldRuntime->gameplayCameraYawRadians();

    if (targetPoint)
    {
        const float deltaX = targetPoint->x - source.x;
        const float deltaY = targetPoint->y - source.y;

        if (deltaX * deltaX + deltaY * deltaY > 1.0f)
        {
            yawRadians = std::atan2(deltaY, deltaX);
        }
    }

    GameplayWorldPoint end = {};
    end.x = source.x + std::cos(yawRadians) * ArpgAetherRayRange;
    end.y = source.y + std::sin(yawRadians) * ArpgAetherRayRange;
    end.z = source.z;
    end = pWorldRuntime->clipChannelBeamTarget(source, end);

    faceArpgAetherRayTarget(*pWorldRuntime, end);
    pWorldRuntime->sustainArpgModePartyActionAnimation(ArpgAetherRayChannelAnimationSeconds, true);

    const float deltaSeconds = std::clamp(config.deltaSeconds, 0.0f, 0.10f);
    rayState.channelElapsedSeconds += deltaSeconds;
    rayState.damageTickAccumulatorSeconds += deltaSeconds;
    rayState.manaTickAccumulatorSeconds += deltaSeconds;

    GameplayChannelBeamFx beam = {};
    beam.start = source;
    beam.end = end;
    beam.radius = ArpgAetherRayVisualRadius;
    beam.intensity = 1.0f;
    beam.phaseSeconds = rayState.channelElapsedSeconds;
    beam.coreColorAbgr = makeInputFxAbgr(230, 255, 190, 235);
    beam.glowColorAbgr = makeInputFxAbgr(70, 255, 126, 205);
    beam.stableId = ArpgAetherRayStableFxId;
    pWorldRuntime->addChannelBeamFx(beam);

    if (rayState.immediateDamageTickPending)
    {
        applyArpgAetherRayDamageTick(
            *pWorldRuntime,
            source,
            end,
            rayState.damageTickSequence);
        ++rayState.damageTickSequence;
        rayState.immediateDamageTickPending = false;
    }

    while (rayState.manaTickAccumulatorSeconds >= ArpgAetherRayManaTickSeconds)
    {
        if (pCaster->spellPoints < ArpgAetherRayManaPerTick)
        {
            context.setStatusBarEvent("Not enough spell points.");
            rayState.manaWarningLatch = true;
            suspendArpgAetherRayChannelForMana(rayState, context);
            return;
        }

        pCaster->spellPoints -= ArpgAetherRayManaPerTick;
        rayState.manaTickAccumulatorSeconds -= ArpgAetherRayManaTickSeconds;
    }

    while (rayState.damageTickAccumulatorSeconds >= ArpgAetherRayDamageTickSeconds)
    {
        applyArpgAetherRayDamageTick(
            *pWorldRuntime,
            source,
            end,
            rayState.damageTickSequence);
        ++rayState.damageTickSequence;
        rayState.damageTickAccumulatorSeconds -= ArpgAetherRayDamageTickSeconds;
    }
}
} // namespace

GameplayMouseLookPolicyResult GameplayInputController::updateGameplayMouseLookPolicy(
    GameplayScreenState::GameplayMouseLookState &state,
    const GameplayMouseLookPolicyConfig &config)
{
    const bool cursorModeActive = config.mouseLookAllowed && config.rightMousePressed;
    const bool mouseLookActive = config.mouseLookAllowed && !cursorModeActive;

    state.cursorModeActive = cursorModeActive;
    state.mouseLookActive = mouseLookActive;

    GameplayMouseLookPolicyResult result = {};
    result.cursorModeActive = cursorModeActive;
    result.mouseLookActive = mouseLookActive;
    result.allowGameplayPointerInput = !config.mouseLookAllowed || cursorModeActive;
    return result;
}

void GameplayInputController::handleStandardUiHotkeys(
    GameplayScreenRuntime &context,
    const GameplayStandardUiHotkeyConfig &config)
{
    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool activeEventDialog = context.activeEventDialog().isActive;
    const bool characterScreenOpen = context.characterScreenReadOnly().open;
    const bool spellbookActive = context.spellbookReadOnly().active;
    const bool restActive = context.restScreenState().active;
    const bool menuActive = context.menuScreenState().active;
    const bool controlsActive = context.controlsScreenState().active;
    const bool keyboardActive = context.keyboardScreenState().active;
    const bool videoOptionsActive = context.videoOptionsScreenState().active;
    const bool saveGameActive = context.saveGameScreenState().active;
    const bool loadGameActive = context.loadGameScreenState().active;
    const bool journalActive = context.journalScreenState().active;
    const bool quickReferenceActive = context.quickReferenceScreenState().active;
    const bool houseShopActive = context.houseShopOverlay().active;
    const bool houseBankInputActive = context.houseBankState().inputActive();
    const bool gameplayHudActive = context.currentHudScreenState() == GameplayHudScreenState::Gameplay;
    const bool canOpenRestFromGameplay =
        config.canOpenRest
        && gameplayHudActive
        && !activeEventDialog
        && !hasActiveLootView
        && !characterScreenOpen
        && !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !quickReferenceActive
        && !context.inventoryNestedOverlay().active
        && !context.readableScrollOverlayReadOnly().active
        && !context.utilitySpellOverlayReadOnly().active
        && !houseShopActive
        && !houseBankInputActive;

    if (isEscapeNewlyPressed(context, config.pKeyboardState))
    {
        if (pWorldRuntime != nullptr && closeActiveLootViewFromEscape(context, *pWorldRuntime))
        {
            return;
        }

        if (spellbookActive)
        {
            context.closeSpellbookOverlay();
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (quickReferenceActive)
        {
            context.closeQuickReferenceOverlay();
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (characterScreenOpen)
        {
            context.characterScreen().open = false;
            context.characterScreen().dollJewelryOverlayOpen = false;
            context.characterScreen().adventurersInnRosterOverlayOpen = false;
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (activeEventDialog || houseShopActive || houseBankInputActive)
        {
            context.handleDialogueCloseRequest();
            context.interactionState().menuToggleLatch = true;
            context.interactionState().closeOverlayLatch = true;
            return;
        }
    }

    const bool canToggleMenu =
        !activeEventDialog
        && !hasActiveLootView
        && !characterScreenOpen
        && !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !quickReferenceActive
        && !context.inventoryNestedOverlay().active
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockMenuToggle;

    if (config.pKeyboardState != nullptr)
    {
        const bool escapePressed = config.pKeyboardState[SDL_SCANCODE_ESCAPE];
        const bool turnBasedActive = context.turnBasedCombatRuntime().active();

        if (canToggleMenu)
        {
            if (escapePressed)
            {
                if (!context.interactionState().menuToggleLatch)
                {
                    context.openMenuOverlay();
                    context.interactionState().menuToggleLatch = true;
                }
            }
            else
            {
                context.interactionState().menuToggleLatch = false;
            }
        }

        if (canOpenRestFromGameplay && turnBasedActive)
        {
            if (isActionHeld(context, KeyboardAction::Rest, config.pInputFrame, config.pKeyboardState))
            {
                if (!context.interactionState().restToggleLatch)
                {
                    context.setStatusBarEvent("You can't rest in turn-based mode!");
                    context.playCantRestHereReaction();
                    context.interactionState().restToggleLatch = true;
                }
            }
            else
            {
                context.interactionState().restToggleLatch = false;
            }
        }
        else if (canOpenRestFromGameplay)
        {
            if (isActionHeld(context, KeyboardAction::Rest, config.pInputFrame, config.pKeyboardState))
            {
                if (!context.interactionState().restToggleLatch)
                {
                    context.openRestOverlay();
                    context.interactionState().restToggleLatch = true;
                }
            }
            else
            {
                context.interactionState().restToggleLatch = false;
            }
        }
        else
        {
            context.interactionState().restToggleLatch = false;
        }
    }
    else
    {
        context.interactionState().menuToggleLatch = false;
        context.interactionState().restToggleLatch = false;
    }

    const bool canToggleSpellbook =
        !activeEventDialog
        && !characterScreenOpen
        && !hasActiveLootView
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !quickReferenceActive
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockSpellbookToggle;

    if (isActionNewlyPressed(context, KeyboardAction::Cast, config.pInputFrame, config.pKeyboardState))
    {
        if (context.spellbookReadOnly().active)
        {
            context.closeSpellbookOverlay();
        }
        else if (canToggleSpellbook)
        {
            context.openSpellbookOverlay();
        }
    }

    const bool canToggleInventory =
        !activeEventDialog
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !quickReferenceActive
        && !config.blockInventoryToggle;

    if (isActionNewlyPressed(context, KeyboardAction::Quest, config.pInputFrame, config.pKeyboardState)
        && canToggleInventory)
    {
        if (hasActiveLootView)
        {
            if (context.inventoryNestedOverlay().active)
            {
                context.closeInventoryNestedOverlay();
            }
            else
            {
                context.openChestTransferInventoryOverlay();
            }
        }
        else
        {
            context.toggleCharacterInventoryScreen();
        }
    }

    const bool canCyclePartyMember =
        !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !quickReferenceActive
        && !houseBankInputActive
        && !config.blockPartyCycle;

    const bool canToggleQuickReference =
        !activeEventDialog
        && !hasActiveLootView
        && !characterScreenOpen
        && !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !context.inventoryNestedOverlay().active
        && !context.readableScrollOverlayReadOnly().active
        && !context.utilitySpellOverlayReadOnly().active
        && !houseShopActive
        && !houseBankInputActive;

    if (isActionNewlyPressed(context, KeyboardAction::QuickRef, config.pInputFrame, config.pKeyboardState))
    {
        if (quickReferenceActive)
        {
            context.closeQuickReferenceOverlay();
        }
        else if (canToggleQuickReference)
        {
            context.openQuickReferenceOverlay();
        }
    }

    if (!canCyclePartyMember
        || !isActionNewlyPressed(context, KeyboardAction::CharCycle, config.pInputFrame, config.pKeyboardState))
    {
        return;
    }

    Party *pParty = context.party();

    if (pParty == nullptr || pParty->members().empty())
    {
        return;
    }

    const bool requireGameplayReady =
        config.requireGameplayReadyForPartySelection
        && !activeEventDialog
        && !hasActiveLootView
        && !houseShopActive;
    const std::optional<size_t> nextMemberIndex = nextSelectableMemberIndex(*pParty, requireGameplayReady);

    if (nextMemberIndex.has_value())
    {
        context.trySelectPartyMember(*nextMemberIndex, requireGameplayReady);
    }
}

void GameplayInputController::handleSharedGameplayHotkeys(
    GameplayScreenRuntime &context,
    const GameplaySharedGameplayHotkeyConfig &config)
{
    if (config.pKeyboardState == nullptr)
    {
        context.interactionState().alwaysRunToggleLatch = false;
        context.interactionState().adventurersInnToggleLatch = false;
        context.interactionState().turnBasedToggleLatch = false;
        return;
    }

    if (config.canToggleAlwaysRun
        && isActionHeld(context, KeyboardAction::AlwaysRun, config.pInputFrame, config.pKeyboardState))
    {
        if (!context.interactionState().alwaysRunToggleLatch)
        {
            GameSettings &settings = context.mutableSettings();
            settings.alwaysRun = !settings.alwaysRun;

            if (IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime())
            {
                pWorldRuntime->setAlwaysRunEnabled(settings.alwaysRun);
            }

            context.commitSettingsChange();
            context.interactionState().alwaysRunToggleLatch = true;
        }
    }
    else
    {
        context.interactionState().alwaysRunToggleLatch = false;
    }

    const bool combatPressed =
        config.canToggleAlwaysRun
        && (isActionHeld(context, KeyboardAction::Combat, config.pInputFrame, config.pKeyboardState)
            || isScancodeHeld(SDL_SCANCODE_KP_ENTER, config.pInputFrame, config.pKeyboardState));
    if (combatPressed)
    {
        if (!context.interactionState().turnBasedToggleLatch)
        {
            Party *pParty = context.party();

            if (pParty != nullptr)
            {
                const bool wasTurnBasedActive = context.turnBasedCombatRuntime().active();
                if (context.turnBasedCombatRuntime().toggle(*pParty, context.worldRuntime()))
                {
                    context.playCommonUiSound(
                        wasTurnBasedActive
                            ? SoundId::EndTurnBasedMode
                            : SoundId::StartTurnBasedMode);
                    context.setStatusBarEvent(
                        context.turnBasedCombatRuntime().active()
                            ? "Turn-based mode"
                            : "Realtime mode");
                }
                else
                {
                    context.setStatusBarEvent("Cannot leave turn-based mode now.");
                }
            }

            context.interactionState().turnBasedToggleLatch = true;
        }
    }
    else
    {
        context.interactionState().turnBasedToggleLatch = false;
    }

    if (config.canToggleAdventurersInn && config.pKeyboardState[SDL_SCANCODE_P])
    {
        if (!context.interactionState().adventurersInnToggleLatch)
        {
            GameplayUiController::CharacterScreenState &characterScreen = context.characterScreen();

            if (context.isAdventurersInnCharacterSourceActive())
            {
                characterScreen.open = false;
                characterScreen.dollJewelryOverlayOpen = false;
                characterScreen.adventurersInnRosterOverlayOpen = false;
            }
            else if (context.party() != nullptr && !context.party()->adventurersInnMembers().empty())
            {
                characterScreen.open = true;
                characterScreen.adventurersInnRosterOverlayOpen = true;
                characterScreen.source = GameplayUiController::CharacterScreenSource::AdventurersInn;
                characterScreen.sourceIndex = 0;
                characterScreen.adventurersInnScrollOffset = 0;
                characterScreen.page = GameplayUiController::CharacterPage::Inventory;
                characterScreen.dollJewelryOverlayOpen = false;
            }
            else
            {
                context.setStatusBarEvent("The Adventurer's Inn is empty.");
            }

            context.interactionState().adventurersInnToggleLatch = true;
        }
    }
    else
    {
        context.interactionState().adventurersInnToggleLatch = false;
    }
}

GameplaySharedInputFrameResult GameplayInputController::updateSharedGameplayInputFrame(
    GameplayScreenState &screenState,
    GameplayScreenRuntime &context,
    GameplaySpellService &spellService,
    const GameplaySharedInputFrameConfig &config)
{
    GameplaySharedInputFrameResult frameResult = {};
    GameplayScreenState::PendingSpellTargetState &pendingSpellCast = screenState.pendingSpellTarget();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();
    GameplayScreenState::GameplayMouseLookState &gameplayMouseLookState = screenState.gameplayMouseLookState();

    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool hasPendingSpellCast = pendingSpellCast.active;
    const GameplayUiController::HeldInventoryItemState &heldInventoryItem = context.heldInventoryItem();
    const bool blocksUnderlyingMouseInput =
        context.currentHudScreenState() != GameplayHudScreenState::Gameplay
        || config.isReadableScrollOverlayActive;
    const bool gameplayMouseLookAllowed =
        context.settingsSnapshot().controlScheme == ControlScheme::Modern
        && !context.settingsSnapshot().arpgModeEnabled
        && GameplayScreenController::canEnableGameplayMouseLook(
            context,
            GameplayMouseLookEnableConfig{
                .hasPendingSpellTarget = hasPendingSpellCast,
                .blockOnReadableScrollOverlay = true,
                .blockOnUtilitySpellOverlay = true,
            });

    frameResult.mouseLookPolicy =
        updateGameplayMouseLookPolicy(
            gameplayMouseLookState,
            GameplayMouseLookPolicyConfig{
                .mouseLookAllowed = gameplayMouseLookAllowed,
                .rightMousePressed = config.rightButtonPressed,
            });

    const bool canToggleAdventurersInn =
        GameplayScreenController::canRunStandardGameplayAction(
            context,
            GameplayStandardGameplayActionGateConfig{
                .hasActiveLootView = hasActiveLootView,
                .hasPendingSpellCast = hasPendingSpellCast,
                .hasHeldItem = heldInventoryItem.active,
                .blockOnHeldItem = true,
            });

    updateArpgAetherRayChannel(
        screenState,
        context,
        config,
        canToggleAdventurersInn,
        blocksUnderlyingMouseInput || config.isUtilitySpellModalActive);

    if (config.processStandardUiInput)
    {
        const GameplayUiOverlayInputResult overlayInputResult =
            GameplayScreenController::processStandardUiInputFrame(
                context,
                GameplayStandardUiInputFrameConfig{
                    .hotkeys =
                        GameplayStandardUiHotkeyConfig{
                            .pKeyboardState = config.pKeyboardState,
                            .pInputFrame = config.pInputFrame,
                            .canOpenRest = true,
                            .blockMenuToggle =
                                hasPendingSpellCast
                                || context.characterScreenReadOnly().open
                                || heldInventoryItem.active,
                            .blockSpellbookToggle = hasPendingSpellCast || heldInventoryItem.active,
                            .blockInventoryToggle = false,
                            .blockPartyCycle = hasPendingSpellCast || context.characterScreenReadOnly().open,
                            .requireGameplayReadyForPartySelection = true,
                        },
                    .input =
                        GameplayStandardUiInputConfig{
                            .pKeyboardState = config.pKeyboardState,
                            .pInputFrame = config.pInputFrame,
                            .width = config.screenWidth,
                            .height = config.screenHeight,
                            .pointerX = config.pointerX,
                            .pointerY = config.pointerY,
                            .leftButtonPressed = config.leftButtonPressed,
                            .allowGameplayPointerInput = frameResult.mouseLookPolicy.allowGameplayPointerInput,
                            .mouseWheelDelta = config.mouseWheelDelta,
                            .blockPortraitInput =
                                config.isUtilitySpellModalActive || config.isReadableScrollOverlayActive,
                            .blockHudButtonInput = blocksUnderlyingMouseInput || config.isUtilitySpellModalActive,
                            .blockJournalToggle =
                                hasPendingSpellCast
                                || context.characterScreenReadOnly().open
                                || heldInventoryItem.active,
                            .requireGameplayReadyForPortraitSelection = !hasPendingSpellCast,
                            .onPortraitActivated =
                                [&screenState, &context, &spellService, &config, hasPendingSpellCast](
                                    size_t memberIndex)
                                {
                                    if (!hasPendingSpellCast)
                                    {
                                        return false;
                                    }

                                    GameplaySpellActionController::PendingTargetSelectionInput pendingTargetInput = {};
                                    pendingTargetInput.confirmPressed = true;
                                    pendingTargetInput.portraitMemberIndex = memberIndex;
                                    pendingTargetInput.targetQueries =
                                        buildSpellActionTargetQueries(screenState, config);

                                    const GameplaySpellActionController::PendingTargetSelectionResult result =
                                        GameplaySpellActionController::updatePendingTargetSelection(
                                            screenState,
                                            context,
                                            spellService,
                                            pendingTargetInput);

                                    if (result.castSucceeded)
                                    {
                                        if (IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime())
                                        {
                                            pWorldRuntime->applyPendingSpellCastWorldEffects(result.castResult);
                                            pWorldRuntime->clearWorldHover();
                                        }
                                    }

                                    return true;
                                },
                        },
                });

        frameResult.journalInputConsumed = overlayInputResult.journalInputConsumed;
    }

    if (frameResult.journalInputConsumed)
    {
        return frameResult;
    }

    const bool canRunStandardGameplayAction =
        GameplayScreenController::canRunStandardGameplayAction(
            context,
            GameplayStandardGameplayActionGateConfig{
                .hasActiveLootView = hasActiveLootView,
                .hasPendingSpellCast = hasPendingSpellCast,
                .blockOnCharacterScreen = true,
            });

    if (config.processSharedGameplayHotkeys)
    {
        handleSharedGameplayHotkeys(
            context,
            GameplaySharedGameplayHotkeyConfig{
                .pKeyboardState = config.pKeyboardState,
                .pInputFrame = config.pInputFrame,
                .canToggleAlwaysRun = canRunStandardGameplayAction,
                .canToggleAdventurersInn = canToggleAdventurersInn,
            });
    }

    if (canRunStandardGameplayAction && config.processQuickCast)
    {
        if (context.turnBasedCombatRuntime().active()
            && isActionNewlyPressed(context, KeyboardAction::Pass, config.pInputFrame, config.pKeyboardState))
        {
            Party *pParty = context.party();
            if (pParty != nullptr)
            {
                if (context.turnBasedCombatRuntime().stage() == TurnBasedCombatStage::Movement)
                {
                    context.turnBasedCombatRuntime().finishMovementPhase();
                }
                else if (context.turnBasedCombatRuntime().canBeginPlayerAction(*pParty))
                {
                    context.turnBasedCombatRuntime().applyPlayerAction(*pParty, pParty->activeMemberIndex(), 0.0f);
                }
            }
        }

        const bool isArpgModeQuickCastPressed =
            context.settingsSnapshot().arpgModeEnabled
            && config.pInputFrame != nullptr
            && config.pInputFrame->isScancodeHeld(SDL_SCANCODE_Q);
        const bool isQuickCastPressed =
            isActionHeld(context, KeyboardAction::CastReady, config.pInputFrame, config.pKeyboardState);

        const GameplayActionController::QuickCastActionDecision quickCastDecision =
            GameplayActionController::updateQuickCastAction(
                quickSpellState,
                GameplayActionController::QuickCastActionConfig{
                    .canRunAction = true,
                    .quickCastPressed = isQuickCastPressed || isArpgModeQuickCastPressed,
                    .hasReadyMember = config.hasReadyMember,
                });

        if (quickCastDecision.shouldBeginQuickCast)
        {
            GameplayActionController::QuickCastActionResult quickCastResult =
                GameplayActionController::QuickCastActionResult::Failed;
            bool quickCastHandledByTurnBasedMode = false;

            if (context.turnBasedCombatRuntime().active())
            {
                Party *pParty = context.party();
                if (context.turnBasedCombatRuntime().stage() == TurnBasedCombatStage::Movement)
                {
                    context.turnBasedCombatRuntime().finishMovementPhase();
                    quickCastHandledByTurnBasedMode = true;
                }
                else if (pParty == nullptr || !context.turnBasedCombatRuntime().canBeginPlayerAction(*pParty))
                {
                    quickCastHandledByTurnBasedMode = true;
                }
            }

            if (!quickCastHandledByTurnBasedMode && config.canBeginQuickCast && context.worldRuntime() != nullptr)
            {
                const GameplaySpellActionController::SpellActionResult spellActionResult =
                    GameplaySpellActionController::tryBeginQuickSpellCast(
                        context,
                        spellService,
                        buildSpellActionTargetQueries(screenState, config));

                if (spellActionResult == GameplaySpellActionController::SpellActionResult::AttackFallback)
                {
                    quickCastResult = GameplayActionController::QuickCastActionResult::AttackFallback;
                }
                else if (spellActionResult == GameplaySpellActionController::SpellActionResult::CastStarted)
                {
                    quickCastResult = GameplayActionController::QuickCastActionResult::CastStarted;
                }
            }

            GameplayActionController::applyQuickCastActionResult(quickSpellState, quickCastResult);
        }
    }
    else if (config.processQuickCast)
    {
        GameplayActionController::updateQuickCastAction(
            quickSpellState,
            GameplayActionController::QuickCastActionConfig{});
    }

    const GameplayStandardWorldInputGateResult worldInputGateResult =
        GameplayScreenController::gateStandardWorldInput(
            context,
            GameplayStandardWorldInputGateConfig{
                .pKeyboardState = config.pKeyboardState,
                .pInputFrame = config.pInputFrame,
                .width = config.screenWidth,
                .height = config.screenHeight,
            });

    frameResult.worldInputBlocked = hasActiveLootView || worldInputGateResult.blocked;
    return frameResult;
}
} // namespace OpenYAMM::Game
