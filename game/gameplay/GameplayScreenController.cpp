#include "game/gameplay/GameplayScreenController.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/items/ItemRuntime.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<SDL_Scancode, 9> NumberHotkeyScancodes = {{
    SDL_SCANCODE_1,
    SDL_SCANCODE_2,
    SDL_SCANCODE_3,
    SDL_SCANCODE_4,
    SDL_SCANCODE_5,
    SDL_SCANCODE_6,
    SDL_SCANCODE_7,
    SDL_SCANCODE_8,
    SDL_SCANCODE_9
}};

constexpr std::array<SDL_Scancode, 9> KeypadNumberHotkeyScancodes = {{
    SDL_SCANCODE_KP_1,
    SDL_SCANCODE_KP_2,
    SDL_SCANCODE_KP_3,
    SDL_SCANCODE_KP_4,
    SDL_SCANCODE_KP_5,
    SDL_SCANCODE_KP_6,
    SDL_SCANCODE_KP_7,
    SDL_SCANCODE_KP_8,
    SDL_SCANCODE_KP_9
}};

bool isScancodeNewlyPressed(
    const GameplayInputFrame &input,
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState,
    SDL_Scancode scancode)
{
    return scancode > SDL_SCANCODE_UNKNOWN
        && scancode < SDL_SCANCODE_COUNT
        && input.keyboardHeld[scancode]
        && previousKeyboardState[scancode] == 0;
}

bool isNumberHotkeyNewlyPressed(
    const GameplayInputFrame &input,
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState,
    size_t numberIndex)
{
    if (numberIndex >= NumberHotkeyScancodes.size())
    {
        return false;
    }

    return isScancodeNewlyPressed(input, previousKeyboardState, NumberHotkeyScancodes[numberIndex])
        || isScancodeNewlyPressed(input, previousKeyboardState, KeypadNumberHotkeyScancodes[numberIndex]);
}

bool isHouseOccupantSelectionMode(const EventDialogContent &dialog)
{
    return !dialog.actions.empty()
        && std::all_of(
            dialog.actions.begin(),
            dialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseProprietor
                    || action.kind == EventDialogActionKind::HouseExtraExit
                    || action.kind == EventDialogActionKind::HouseResident;
            });
}

const char *itemInspectSourceTypeName(GameplayUiController::ItemInspectSourceType sourceType)
{
    switch (sourceType)
    {
        case GameplayUiController::ItemInspectSourceType::None:
            return "none";
        case GameplayUiController::ItemInspectSourceType::Inventory:
            return "inventory";
        case GameplayUiController::ItemInspectSourceType::Equipment:
            return "equipment";
        case GameplayUiController::ItemInspectSourceType::WorldItem:
            return "world_item";
        case GameplayUiController::ItemInspectSourceType::Chest:
            return "chest";
        case GameplayUiController::ItemInspectSourceType::Corpse:
            return "corpse";
    }

    return "unknown";
}
} // namespace

void GameplayScreenController::updateSharedFrameState(
    GameplayScreenRuntime &context,
    int width,
    int height,
    float deltaSeconds,
    const GameplayScreenFrameUpdateConfig &config)
{
    context.fxService().syncProjectilePresentation();
    context.fxService().advanceGameplayScreenOverlay(deltaSeconds);
    context.updatePartyPortraitAnimations(deltaSeconds);
    context.updateDelayedSpeechReactions(deltaSeconds);
    context.consumePendingPartyAudioRequests();

    GameplayUiController::JournalScreenState &journalScreen = context.journalScreenState();

    if (journalScreen.active)
    {
        journalScreen.hoverAnimationElapsedSeconds += std::max(0.0f, deltaSeconds);
    }

    float &statusBarRemainingSeconds = context.statusBarEventRemainingSeconds();

    if (statusBarRemainingSeconds > 0.0f)
    {
        statusBarRemainingSeconds = std::max(0.0f, statusBarRemainingSeconds - deltaSeconds);

        if (statusBarRemainingSeconds <= 0.0f)
        {
            context.statusBarEventText().clear();
        }
    }

    updateRestOverlayProgress(context, deltaSeconds);

    const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();
    const bool characterInventoryVisible =
        characterScreen.open && characterScreen.page == GameplayUiController::CharacterPage::Inventory;
    if (!characterInventoryVisible)
    {
        context.interactionState().inventoryOpenHookExecuted = false;
    }
    else if (!context.interactionState().inventoryOpenHookExecuted)
    {
        IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
        EventRuntimeState *pEventRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

        if (pWorldRuntime != nullptr && pEventRuntimeState != nullptr)
        {
            const std::optional<EventRuntimeState::ActiveHookContext> previousHookContext =
                pEventRuntimeState->activeHookContext;
            EventRuntimeState::ActiveHookContext hookContext = {};
            hookContext.kind = EventRuntimeHookKind::InventoryOpen;
            hookContext.inventorySource = static_cast<uint32_t>(characterScreen.source);
            hookContext.inventorySourceIndex = static_cast<uint32_t>(characterScreen.sourceIndex);
            hookContext.inventoryPage = static_cast<uint32_t>(characterScreen.page);
            pEventRuntimeState->activeHookContext = std::move(hookContext);
            pWorldRuntime->executeEventHooks(EventRuntimeHookKind::InventoryOpen);
            pEventRuntimeState->activeHookContext = previousHookContext;
        }

        context.interactionState().inventoryOpenHookExecuted = true;
    }

    GameplayHudOverlaySupport::updateCharacterInspectOverlay(context, width, height);
    GameplayHudOverlaySupport::updateCharacterDetailOverlay(context, width, height);
    GameplayHudOverlaySupport::updateSpellInspectOverlay(context, width, height);

    if (config.updateBuffInspectOverlay)
    {
        GameplayHudOverlaySupport::updateBuffInspectOverlay(context, width, height, true);
    }
    else
    {
        context.buffInspectOverlay() = {};
    }
}

bool GameplayScreenController::updateRenderedHudItemInspectOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height,
    bool requireOpaqueHitTest)
{
    return GameplayHudOverlaySupport::tryPopulateItemInspectOverlayFromRenderedHudItems(
        context,
        width,
        height,
        requireOpaqueHitTest);
}

bool GameplayScreenController::canUpdateStandardHudItemInspectOverlayFromMouse(
    GameplayScreenRuntime &context,
    int width,
    int height,
    bool additionalBlock)
{
    if (width <= 0
        || height <= 0
        || additionalBlock
        || context.spellbookReadOnly().active
        || context.controlsScreenState().active
        || context.keyboardScreenState().active
        || context.menuScreenState().active
        || context.saveGameScreenState().active
        || context.loadGameScreenState().active)
    {
        return false;
    }

    return true;
}

bool GameplayScreenController::canUpdateStandardWorldInspectOverlayFromMouse(
    GameplayScreenRuntime &context,
    const GameplayStandardWorldInspectOverlayConfig &config)
{
    if (config.width <= 0
        || config.height <= 0
        || !config.worldReady
        || config.hasHeldItem
        || config.hasPendingSpellTarget
        || config.hasActiveLootView
        || context.activeEventDialog().isActive
        || context.characterScreenReadOnly().open
        || context.spellbookReadOnly().active
        || context.controlsScreenState().active
        || context.keyboardScreenState().active
        || context.menuScreenState().active
        || context.saveGameScreenState().active
        || context.loadGameScreenState().active)
    {
        return false;
    }

    return true;
}

bool GameplayScreenController::canRunStandardGameplayAction(
    GameplayScreenRuntime &context,
    const GameplayStandardGameplayActionGateConfig &config)
{
    if (config.hasActiveLootView
        || config.hasPendingSpellCast
        || context.activeEventDialog().isActive
        || context.spellbookReadOnly().active
        || context.restScreenState().active
        || context.menuScreenState().active
        || context.controlsScreenState().active
        || context.keyboardScreenState().active
        || context.saveGameScreenState().active
        || context.loadGameScreenState().active
        || context.journalScreenState().active)
    {
        return false;
    }

    if (config.blockOnCharacterScreen && context.characterScreenReadOnly().open)
    {
        return false;
    }

    if (config.blockOnHeldItem && config.hasHeldItem)
    {
        return false;
    }

    return true;
}

bool GameplayScreenController::canEnableGameplayMouseLook(
    GameplayScreenRuntime &context,
    const GameplayMouseLookEnableConfig &config)
{
    if (context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return false;
    }

    if (config.hasPendingSpellTarget)
    {
        return false;
    }

    if (config.blockOnReadableScrollOverlay && context.readableScrollOverlayReadOnly().active)
    {
        return false;
    }

    if (config.blockOnUtilitySpellOverlay && context.utilitySpellOverlayReadOnly().active)
    {
        const bool inventoryTargetMode =
            context.utilitySpellOverlayReadOnly().mode
            == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;

        if (!inventoryTargetMode || !config.utilitySpellInventoryTargetKeepsMouseLook)
        {
            return false;
        }
    }

    return true;
}

void GameplayScreenController::updateStandardHudItemInspectOverlayFromMouse(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input,
    int width,
    int height,
    bool enabled,
    bool requireOpaqueHitTest)
{
    GameplayUiController::ItemInspectOverlayState &overlay = context.itemInspectOverlay();
    overlay = {};

    if (!enabled || width <= 0 || height <= 0)
    {
        return;
    }

    if (!input.rightMouseButton.held)
    {
        context.interactionState().itemInspectInteractionLatch = false;
        context.interactionState().itemInspectInteractionKey = 0;
        return;
    }

    if (updateRenderedHudItemInspectOverlay(context, width, height, requireOpaqueHitTest))
    {
        applySharedItemInspectSkillInteraction(context);
    }
}

void GameplayScreenController::applySharedItemInspectSkillInteraction(
    GameplayScreenRuntime &context)
{
    GameplayUiController::ItemInspectOverlayState &overlay = context.itemInspectOverlay();
    Party *pParty = context.party();
    const ItemTable *pItemTable = context.itemTable();

    if (!overlay.active
        || !overlay.hasItemState
        || pParty == nullptr
        || pItemTable == nullptr
        || overlay.sourceType == GameplayUiController::ItemInspectSourceType::None)
    {
        return;
    }

    uint64_t interactionKey = uint64_t(overlay.objectDescriptionId);
    interactionKey ^= uint64_t(overlay.sourceMemberIndex + 1) << 16;
    interactionKey ^= uint64_t(overlay.sourceGridX) << 24;
    interactionKey ^= uint64_t(overlay.sourceGridY) << 32;
    interactionKey ^= uint64_t(overlay.sourceEquipmentSlot) << 40;
    interactionKey ^= uint64_t(overlay.sourceWorldItemIndex) << 44;
    interactionKey ^= uint64_t(overlay.sourceLootItemIndex) << 48;
    interactionKey ^= uint64_t(overlay.sourceType) << 56;

    if (context.interactionState().itemInspectInteractionLatch
        && context.interactionState().itemInspectInteractionKey == interactionKey)
    {
        return;
    }

    context.interactionState().itemInspectInteractionLatch = true;
    context.interactionState().itemInspectInteractionKey = interactionKey;

    std::string worldContext;
    const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();

    if (pWorldRuntime != nullptr)
    {
        const std::string sceneKind = pWorldRuntime->isIndoorMap() ? "indoor" : "outdoor";
        worldContext =
            " map=\"" + pWorldRuntime->mapName() + "\""
            + " scene_kind=" + sceneKind
            + " party=(" + std::to_string(pWorldRuntime->partyX())
            + "," + std::to_string(pWorldRuntime->partyY())
            + "," + std::to_string(pWorldRuntime->partyFootZ()) + ")"
            + " yaw=" + std::to_string(pWorldRuntime->gameplayCameraYawRadians())
            + " pitch=" + std::to_string(pWorldRuntime->gameplayCameraPitchRadians());
    }

    GAMEPLAY_DEBUG_TRACE(
        "item_inspect item_id=" + std::to_string(overlay.objectDescriptionId)
        + gameplayDebugTraceItemSummary(overlay.objectDescriptionId, pItemTable)
        + " source=" + itemInspectSourceTypeName(overlay.sourceType)
        + worldContext
        + " member_index=" + std::to_string(overlay.sourceMemberIndex)
        + " grid=(" + std::to_string(overlay.sourceGridX) + "," + std::to_string(overlay.sourceGridY) + ")"
        + " equipment_slot=" + std::to_string(static_cast<uint32_t>(overlay.sourceEquipmentSlot))
        + " world_item_index=" + std::to_string(overlay.sourceWorldItemIndex)
        + " loot_item_index=" + std::to_string(overlay.sourceLootItemIndex));

    const Character *pActiveMember = pParty->activeMember();
    const ItemDefinition *pItemDefinition = pItemTable->get(overlay.objectDescriptionId);

    if (pActiveMember == nullptr || pItemDefinition == nullptr)
    {
        return;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory
        || overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
    {
        const Character *pSourceMember = pParty->member(overlay.sourceMemberIndex);

        if (pSourceMember == nullptr || !GameMechanics::canAct(*pSourceMember))
        {
            return;
        }
    }

    const size_t activeMemberIndex = pParty->activeMemberIndex();
    bool reactionPlayed = false;
    const auto playSingleReaction =
        [&context, activeMemberIndex, &reactionPlayed](SpeechId speechId)
        {
            if (reactionPlayed)
            {
                return;
            }

            context.playSpeechReaction(activeMemberIndex, speechId, true);
            reactionPlayed = true;
        };

    const auto refreshOverlayItemState =
        [&context, pParty, &overlay]()
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                const Character *pSourceMember = pParty->member(overlay.sourceMemberIndex);

                if (pSourceMember == nullptr)
                {
                    return;
                }

                const InventoryItem *pItem = pSourceMember->inventoryItemAt(overlay.sourceGridX, overlay.sourceGridY);

                if (pItem != nullptr)
                {
                    overlay.itemState = *pItem;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                const std::optional<InventoryItem> item =
                    pParty->equippedItem(overlay.sourceMemberIndex, overlay.sourceEquipmentSlot);

                if (item.has_value())
                {
                    overlay.itemState = *item;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest)
            {
                IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
                const GameplayChestViewState *pChestView =
                    pWorldRuntime != nullptr ? pWorldRuntime->activeChestView() : nullptr;

                if (pChestView != nullptr && overlay.sourceLootItemIndex < pChestView->items.size())
                {
                    overlay.itemState = pChestView->items[overlay.sourceLootItemIndex].item;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse)
            {
                IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
                const GameplayCorpseViewState *pCorpseView =
                    pWorldRuntime != nullptr ? pWorldRuntime->activeCorpseView() : nullptr;

                if (pCorpseView != nullptr && overlay.sourceLootItemIndex < pCorpseView->items.size())
                {
                    overlay.itemState = pCorpseView->items[overlay.sourceLootItemIndex].item;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::WorldItem)
            {
                IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
                GameplayWorldItemInspectState worldItemState = {};

                if (pWorldRuntime != nullptr
                    && pWorldRuntime->worldItemInspectState(overlay.sourceWorldItemIndex, worldItemState)
                    && !worldItemState.isGold)
                {
                    overlay.itemState = worldItemState.item;
                }
            }
        };

    const auto forceIdentifyWithoutReaction =
        [&context, &overlay](std::string &statusText) -> bool
        {
            return context.itemService().identifyInspectedItem(overlay, statusText);
        };

    const auto tryIdentifyWithSkill =
        [&context, activeMemberIndex, &overlay](std::string &statusText) -> bool
        {
            return context.itemService().tryIdentifyInspectedItem(overlay, activeMemberIndex, statusText);
        };

    const auto tryRepairWithSkill =
        [&context, activeMemberIndex, &overlay](std::string &statusText) -> bool
        {
            return context.itemService().tryRepairInspectedItem(overlay, activeMemberIndex, statusText);
        };

    if (!overlay.itemState.identified)
    {
        std::string statusText;

        if (!ItemRuntime::requiresIdentification(*pItemDefinition))
        {
            if (forceIdentifyWithoutReaction(statusText))
            {
                refreshOverlayItemState();
            }
        }
        else if (tryIdentifyWithSkill(statusText))
        {
            refreshOverlayItemState();
            const SpeechId speechId =
                pItemDefinition->value < 100 * (int(pActiveMember->level) + 5)
                    ? SpeechId::IdentifyWeakItem
                    : SpeechId::IdentifyGreatItem;
            playSingleReaction(speechId);
        }
        else if (statusText == "Identify Failed")
        {
            context.setStatusBarEvent(statusText);
            playSingleReaction(SpeechId::IdentifyFailItem);
        }
    }

    if (overlay.itemState.broken)
    {
        std::string statusText;

        if (tryRepairWithSkill(statusText))
        {
            refreshOverlayItemState();
            playSingleReaction(SpeechId::RepairSuccess);
        }
        else if (statusText == "Repair Failed")
        {
            context.setStatusBarEvent(statusText);
            playSingleReaction(SpeechId::RepairFail);
        }
    }
}

void GameplayScreenController::updateRestOverlayProgress(
    GameplayScreenRuntime &context,
    float deltaSeconds)
{
    GameplayUiController::RestScreenState &restScreen = context.restScreenState();

    if (!restScreen.active)
    {
        return;
    }

    const float safeDeltaSeconds = std::max(0.0f, deltaSeconds);
    restScreen.hourglassElapsedSeconds += safeDeltaSeconds;

    if (restScreen.mode == GameplayUiController::RestMode::None || context.worldRuntime() == nullptr)
    {
        return;
    }

    constexpr float ShortestRestAnimationSeconds = 0.25f;
    constexpr float LongestRestAnimationSeconds = 2.0f;
    constexpr float RestMinutesPerAnimationSecond = 360.0f;
    const float animationDurationSeconds = std::clamp(
        restScreen.totalMinutes / RestMinutesPerAnimationSecond,
        ShortestRestAnimationSeconds,
        LongestRestAnimationSeconds);
    const float gameMinutesPerSecond = animationDurationSeconds > 0.0f
        ? restScreen.totalMinutes / animationDurationSeconds
        : restScreen.totalMinutes;
    const float advancedMinutes = std::min(
        restScreen.remainingMinutes,
        gameMinutesPerSecond * safeDeltaSeconds);

    if (advancedMinutes > 0.0f)
    {
        IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
        pWorldRuntime->advanceGameMinutes(advancedMinutes);
        EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();
        Party *pParty = context.party();
        if (pParty != nullptr)
        {
            pParty->advanceTimedStates(advancedMinutes * 60.0f);
        }
        if (pEventRuntimeState != nullptr && pParty != nullptr)
        {
            context.itemService().updateConnectorStoneRecharge(*pParty, *pEventRuntimeState, pWorldRuntime->gameMinutes());
        }
        restScreen.remainingMinutes = std::max(0.0f, restScreen.remainingMinutes - advancedMinutes);
    }

    if (restScreen.remainingMinutes > 0.0f)
    {
        return;
    }

    context.completeRestAction(false);
}

void GameplayScreenController::handlePartyPortraitInput(
    GameplayScreenRuntime &context,
    const GameplayPartyPortraitInputConfig &config)
{
    GameplayHudInputController::handlePartyPortraitInput(context, config);
}

void GameplayScreenController::handleGameplayHudButtonInput(
    GameplayScreenRuntime &context,
    const GameplayHudButtonInputConfig &config)
{
    GameplayHudInputController::handleGameplayHudButtonInput(context, config);
}

GameplayUiOverlayInputResult GameplayScreenController::handleSharedOverlayInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input,
    const GameplayUiOverlayInputConfig &config)
{
    GameplayUiOverlayInputResult result = GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
        context,
        input,
        config);

    if (result.journalInputConsumed && !config.activeEventDialog)
    {
        context.resetDialogueOverlayInteractionState();
    }

    return result;
}

GameplayUiOverlayInputResult GameplayScreenController::handleStandardUiInput(
    GameplayScreenRuntime &context,
    const GameplayStandardUiInputConfig &config)
{
    GameplayInputFrame fallbackInput = {};

    if (config.pInputFrame == nullptr)
    {
        fallbackInput.screenWidth = config.width;
        fallbackInput.screenHeight = config.height;
        fallbackInput.pointerX = config.pointerX;
        fallbackInput.pointerY = config.pointerY;
        fallbackInput.mouseWheelDelta = config.mouseWheelDelta;
        fallbackInput.leftMouseButton.held = config.leftButtonPressed;

        if (config.pKeyboardState != nullptr)
        {
            for (int scancode = 0; scancode < SDL_SCANCODE_COUNT; ++scancode)
            {
                fallbackInput.keyboardHeld[scancode] = config.pKeyboardState[scancode];
            }
        }
    }

    const GameplayInputFrame &input =
        config.pInputFrame != nullptr ? *config.pInputFrame : fallbackInput;
    const bool *pKeyboardState = input.keyboardState();
    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool activeEventDialog = context.activeEventDialog().isActive;
    const bool residentSelectionMode = isHouseOccupantSelectionMode(context.activeEventDialog());
    const bool spellbookActive = context.spellbookReadOnly().active;
    const bool characterScreenOpen = context.characterScreenReadOnly().open;
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

    const bool requirePortraitGameplayReady =
        config.requireGameplayReadyForPortraitSelection
        && !activeEventDialog
        && !hasActiveLootView
        && !houseShopActive;
#if defined(__ANDROID__)
    const bool allowPortraitPointerInput =
        config.allowGameplayPointerInput
        || input.leftMouseButton.held
        || context.interactionState().partyPortraitClickLatch;
#else
    const bool allowPortraitPointerInput = config.allowGameplayPointerInput;
#endif

    const bool gameplayReadyForPortraitClicks =
        allowPortraitPointerInput
        && config.width > 0
        && config.height > 0
        && !config.blockPortraitInput
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
        && !houseBankInputActive;

    if (gameplayReadyForPortraitClicks)
    {
        handlePartyPortraitInput(
            context,
            GameplayPartyPortraitInputConfig{
                .screenWidth = config.width,
                .screenHeight = config.height,
                .pointerX = config.pointerX,
                .pointerY = config.pointerY,
                .leftButtonPressed = config.leftButtonPressed,
                .allowInput = true,
                .requireGameplayReady = requirePortraitGameplayReady,
                .hasActiveLootView = hasActiveLootView,
                .onPortraitActivated = config.onPortraitActivated,
            });
    }
    else
    {
        handlePartyPortraitInput(context, GameplayPartyPortraitInputConfig{});
    }

    const bool canUsePartyNumberHotkeys =
        !config.blockPortraitInput
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
        && !houseBankInputActive;

    if (canUsePartyNumberHotkeys)
    {
        const GameplayPartyPortraitInputConfig portraitHotkeyConfig{
            .screenWidth = config.width,
            .screenHeight = config.height,
            .pointerX = config.pointerX,
            .pointerY = config.pointerY,
            .leftButtonPressed = false,
            .allowInput = true,
            .requireGameplayReady = requirePortraitGameplayReady,
            .hasActiveLootView = hasActiveLootView,
            .onPortraitActivated = config.onPortraitActivated,
        };

        for (size_t memberIndex = 0; memberIndex < 5; ++memberIndex)
        {
            if (isNumberHotkeyNewlyPressed(input, context.previousKeyboardState(), memberIndex))
            {
                GameplayHudInputController::activatePartyPortrait(context, memberIndex, portraitHotkeyConfig);
            }
        }
    }

    const bool allowGameplayHudPointerInput =
#if defined(__ANDROID__)
        config.allowGameplayPointerInput
        || input.leftMouseButton.held
        || context.interactionState().gameplayHudClickLatch;
#else
        config.allowGameplayPointerInput;
#endif

    const bool canClickGameplayHudButtons =
        config.width > 0
        && config.height > 0
        && allowGameplayHudPointerInput
        && !config.blockHudButtonInput
        && !activeEventDialog
        && !characterScreenOpen
        && !spellbookActive
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
        && !houseBankInputActive;

    handleGameplayHudButtonInput(
        context,
        GameplayHudButtonInputConfig{
            .screenWidth = config.width,
            .screenHeight = config.height,
            .pointerX = config.pointerX,
            .pointerY = config.pointerY,
            .leftButtonPressed = config.leftButtonPressed,
            .allowInput = canClickGameplayHudButtons,
        });

    const bool canUseFollowerNumberHotkeys =
        !activeEventDialog
        && !characterScreenOpen
        && !spellbookActive
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
        && !context.inventoryNestedOverlay().active
        && !context.readableScrollOverlayReadOnly().active
        && !context.utilitySpellOverlayReadOnly().active
        && !context.pendingSpellTargetActive();

    if (canUseFollowerNumberHotkeys)
    {
        for (size_t followerIndex = 0; followerIndex < 4; ++followerIndex)
        {
            if (isNumberHotkeyNewlyPressed(input, context.previousKeyboardState(), followerIndex + 5))
            {
                context.openFollowerNpcDialogueByIndex(followerIndex);
            }
        }
    }

    const bool canToggleJournal =
        !activeEventDialog
        && !hasActiveLootView
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !context.inventoryNestedOverlay().active
        && !quickReferenceActive
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockJournalToggle;

    const bool mapShortcutPressed =
        input.isScancodeHeld(SDL_SCANCODE_M)
        || input.action(KeyboardAction::MapBook).held;
    const bool storyShortcutPressed =
        input.action(KeyboardAction::History).held;
    const bool notesShortcutPressed = false;
    const bool zoomInPressed =
        input.action(KeyboardAction::ZoomIn).held;
    const bool zoomOutPressed =
        input.action(KeyboardAction::ZoomOut).held;

    return handleSharedOverlayInput(
        context,
        input,
        GameplayUiOverlayInputConfig{
            .hasActiveLootView = hasActiveLootView,
            .canToggleJournal = canToggleJournal,
            .mapShortcutPressed = mapShortcutPressed,
            .storyShortcutPressed = storyShortcutPressed,
            .notesShortcutPressed = notesShortcutPressed,
            .zoomInPressed = zoomInPressed,
            .zoomOutPressed = zoomOutPressed,
            .mouseWheelDelta = input.mouseWheelDelta,
            .activeEventDialog = activeEventDialog,
            .residentSelectionMode = residentSelectionMode,
            .restActive = restActive,
            .menuActive = menuActive,
            .controlsActive = controlsActive,
            .keyboardActive = keyboardActive,
            .videoOptionsActive = videoOptionsActive,
            .saveGameActive = saveGameActive,
            .quickReferenceActive = quickReferenceActive,
            .spellbookActive = spellbookActive,
            .characterScreenOpen = characterScreenOpen,
        });
}

GameplayStandardWorldInputGateResult GameplayScreenController::gateStandardWorldInput(
    GameplayScreenRuntime &context,
    const GameplayStandardWorldInputGateConfig &config)
{
    if (config.blockOnDialogue && context.activeEventDialog().isActive)
    {
        return {.blocked = true};
    }

    if (config.blockOnRest && context.restScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnSpellbook && context.spellbookReadOnly().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnUtilitySpellOverlay && context.utilitySpellOverlayReadOnly().active)
    {
        const bool inventoryTargetMode =
            context.utilitySpellOverlayReadOnly().mode
            == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;

        if (!inventoryTargetMode || !config.utilitySpellInventoryTargetKeepsWorldInput)
        {
            if (!inventoryTargetMode && config.pInputFrame != nullptr)
            {
                handleUtilitySpellOverlayInput(
                    context,
                    *config.pInputFrame);

                return {.blocked = true, .utilitySpellOverlayHandled = true};
            }

            return {.blocked = true};
        }
    }

    if (config.blockOnSaveGame && context.saveGameScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnLoadGame && context.loadGameScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnControls && context.controlsScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnKeyboard && context.keyboardScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnVideoOptions && context.videoOptionsScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnMenu && context.menuScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnCharacterScreen && context.characterScreenReadOnly().open)
    {
        return {.blocked = true};
    }

    if (config.blockOnJournal && context.journalScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.blockOnQuickReference && context.quickReferenceScreenState().active)
    {
        return {.blocked = true};
    }

    if (config.clearCharacterOverlayInputState)
    {
        context.resetCharacterOverlayInteractionState();
    }

    if (config.closeReadableScrollOverlay)
    {
        context.itemService().closeReadableScrollOverlay();
    }

    return {};
}

GameplayStandardWorldInteractionFrameState GameplayScreenController::captureStandardWorldInteractionFrameState(
    GameplayScreenRuntime &context)
{
    return GameplayStandardWorldInteractionFrameState{
        .restActiveBeforeInput = context.restScreenState().active,
        .menuActiveBeforeInput = context.menuScreenState().active,
        .controlsActiveBeforeInput = context.controlsScreenState().active,
        .keyboardActiveBeforeInput = context.keyboardScreenState().active,
        .videoOptionsActiveBeforeInput = context.videoOptionsScreenState().active,
        .saveGameActiveBeforeInput = context.saveGameScreenState().active,
        .loadGameActiveBeforeInput = context.loadGameScreenState().active,
        .journalActiveBeforeInput = context.journalScreenState().active,
        .quickReferenceActiveBeforeInput = context.quickReferenceScreenState().active,
    };
}

bool GameplayScreenController::isStandardWorldInteractionBlockedForFrame(
    GameplayScreenRuntime &context,
    const GameplayStandardWorldInteractionFrameGateConfig &config)
{
    return config.hasActiveLootView
        || context.activeEventDialog().isActive
        || context.characterScreenReadOnly().open
        || context.spellbookReadOnly().active
        || config.state.restActiveBeforeInput
        || context.restScreenState().active
        || config.state.menuActiveBeforeInput
        || context.menuScreenState().active
        || config.state.controlsActiveBeforeInput
        || context.controlsScreenState().active
        || config.state.keyboardActiveBeforeInput
        || context.keyboardScreenState().active
        || config.state.videoOptionsActiveBeforeInput
        || context.videoOptionsScreenState().active
        || config.state.saveGameActiveBeforeInput
        || context.saveGameScreenState().active
        || config.state.loadGameActiveBeforeInput
        || context.loadGameScreenState().active
        || config.state.journalActiveBeforeInput
        || context.journalScreenState().active
        || config.state.quickReferenceActiveBeforeInput
        || context.quickReferenceScreenState().active;
}

void GameplayScreenController::renderStandardUi(
    GameplayScreenRuntime &context,
    int width,
    int height,
    const GameplayStandardUiRenderConfig &config)
{
    if (!config.renderGameplayHud)
    {
        return;
    }

    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool renderChestUi =
        hasActiveLootView && pWorldRuntime != nullptr && pWorldRuntime->activeChestView() != nullptr;
    const bool deferDialogueInventoryServiceOverlay =
        context.inventoryNestedOverlay().active
        && (context.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || context.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || context.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
        && context.currentHudScreenState() == GameplayHudScreenState::Dialogue;
    renderSharedOverlays(
        context,
        width,
        height,
        GameplayScreenRenderConfig{
            .base =
                GameplayUiOverlayRenderConfig{
                    .canRenderHudOverlays = config.canRenderHudOverlays,
                    .hasActiveLootView = hasActiveLootView,
                    .activeEventDialog = context.activeEventDialog().isActive,
                    .renderGameplayMouseLookOverlay = config.renderGameplayMouseLookOverlay,
                    .renderChestBelowHud = renderChestUi,
                    .renderChestAboveHud = renderChestUi,
                    .renderInventoryBelowHud = !deferDialogueInventoryServiceOverlay,
                    .renderInventoryAboveHud = renderChestUi,
                    .renderDialogueBelowHud = true,
                    .renderDialogueAboveHud = true,
                    .renderCharacterBelowHud = true,
                    .renderCharacterAboveHud = true,
                    .renderItemInspectOverlay = !deferDialogueInventoryServiceOverlay,
                    .renderDebugDialogueFallback = config.renderDebugFallbacks,
                },
            .renderDeferredInventoryOverlay = deferDialogueInventoryServiceOverlay,
            .renderActorInspectOverlay = config.renderActorInspectOverlay,
        });

}

void GameplayScreenController::processStandardUiFrame(
    GameplayScreenRuntime &context,
    int width,
    int height,
    float deltaSeconds,
    const GameplayStandardUiFrameConfig &config)
{
    updateSharedFrameState(context, width, height, deltaSeconds, config.frame);
    const bool updateHudItemInspectOverlay =
        config.updateHudItemInspectOverlayFromMouse
        && canUpdateStandardHudItemInspectOverlayFromMouse(
            context,
            width,
            height,
            config.blockHudItemInspectOverlayFromMouseUpdate);
    updateStandardHudItemInspectOverlayFromMouse(
        context,
        config.input.pInputFrame != nullptr ? *config.input.pInputFrame : GameplayInputFrame{},
        width,
        height,
        updateHudItemInspectOverlay,
        config.requireOpaqueHudItemInspectHit);
    GameplayInputController::handleStandardUiHotkeys(context, config.hotkeys);
    handleStandardUiInput(context, config.input);
    renderStandardUi(context, width, height, config.render);

    const bool *pKeyboardState = config.hotkeys.pKeyboardState != nullptr
        ? config.hotkeys.pKeyboardState
        : config.input.pKeyboardState;
    context.updatePreviousKeyboardStateSnapshot(pKeyboardState);
}

GameplayUiOverlayInputResult GameplayScreenController::processStandardUiInputFrame(
    GameplayScreenRuntime &context,
    const GameplayStandardUiInputFrameConfig &config)
{
    GameplayInputController::handleStandardUiHotkeys(context, config.hotkeys);
    const GameplayUiOverlayInputResult result = handleStandardUiInput(context, config.input);
    const bool *pKeyboardState = config.hotkeys.pKeyboardState != nullptr
        ? config.hotkeys.pKeyboardState
        : config.input.pKeyboardState;
    context.updatePreviousKeyboardStateSnapshot(pKeyboardState);
    return result;
}

void GameplayScreenController::handleUtilitySpellOverlayInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input)
{
    GameplayPartyOverlayInputController::handleUtilitySpellOverlayInput(
        context,
        input);
}

void GameplayScreenController::renderSharedOverlays(
    GameplayScreenRuntime &context,
    int width,
    int height,
    const GameplayScreenRenderConfig &config)
{
    GameplayUiOverlayOrchestrator::renderStandardOverlays(context, width, height, config.base);

    if (!config.base.canRenderHudOverlays)
    {
        return;
    }

    if (config.renderDeferredInventoryOverlay)
    {
        GameplayHudOverlayRenderer::renderInventoryNestedOverlay(context, width, height, false);
        GameplayPartyOverlayRenderer::renderItemInspectOverlay(context, width, height);
    }

    if (config.renderUtilitySpellOverlay)
    {
        GameplayPartyOverlayRenderer::renderUtilitySpellOverlay(context, width, height);
    }

    if (config.renderCharacterInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderCharacterInspectOverlay(context, width, height);
    }

    if (config.renderBuffInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderBuffInspectOverlay(context, width, height);
    }

    if (config.renderCharacterDetailOverlay)
    {
        GameplayPartyOverlayRenderer::renderCharacterDetailOverlay(context, width, height);
    }

    if (config.renderActorInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderActorInspectOverlay(context, width, height);
    }

    if (config.renderSpellInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderSpellInspectOverlay(context, width, height);
    }

    if (config.renderReadableScrollOverlay)
    {
        GameplayPartyOverlayRenderer::renderReadableScrollOverlay(context, width, height);
    }
}
} // namespace OpenYAMM::Game
