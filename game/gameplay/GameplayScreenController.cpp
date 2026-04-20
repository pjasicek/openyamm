#include "game/gameplay/GameplayScreenController.h"

#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/items/ItemRuntime.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"

#include <SDL3/SDL.h>

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
bool isResidentSelectionMode(const EventDialogContent &dialog)
{
    return !dialog.actions.empty()
        && std::all_of(
            dialog.actions.begin(),
            dialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
}
} // namespace

void GameplayScreenController::updateSharedFrameState(
    GameplayScreenRuntime &context,
    int width,
    int height,
    float deltaSeconds,
    const GameplayScreenFrameUpdateConfig &config)
{
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

void GameplayScreenController::updateStandardHudItemInspectOverlayFromMouse(
    GameplayScreenRuntime &context,
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

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
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
        || overlay.sourceType == GameplayUiController::ItemInspectSourceType::None
        || overlay.sourceType == GameplayUiController::ItemInspectSourceType::WorldItem)
    {
        return;
    }

    uint64_t interactionKey = uint64_t(overlay.objectDescriptionId);
    interactionKey ^= uint64_t(overlay.sourceMemberIndex + 1) << 16;
    interactionKey ^= uint64_t(overlay.sourceGridX) << 24;
    interactionKey ^= uint64_t(overlay.sourceGridY) << 32;
    interactionKey ^= uint64_t(overlay.sourceEquipmentSlot) << 40;
    interactionKey ^= uint64_t(overlay.sourceLootItemIndex) << 48;
    interactionKey ^= uint64_t(overlay.sourceType) << 56;

    if (context.interactionState().itemInspectInteractionLatch && context.interactionState().itemInspectInteractionKey == interactionKey)
    {
        return;
    }

    context.interactionState().itemInspectInteractionLatch = true;
    context.interactionState().itemInspectInteractionKey = interactionKey;

    const Character *pActiveMember = pParty->activeMember();
    const ItemDefinition *pItemDefinition = pItemTable->get(overlay.objectDescriptionId);

    if (pActiveMember == nullptr || pItemDefinition == nullptr)
    {
        return;
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
        };

    const auto forceIdentifyWithoutReaction =
        [&context, pParty, &overlay](std::string &statusText) -> bool
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                return pParty->identifyMemberInventoryItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceGridX,
                    overlay.sourceGridY,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                return pParty->identifyEquippedItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceEquipmentSlot,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->identifyActiveChestItem(overlay.sourceLootItemIndex, statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->identifyActiveCorpseItem(overlay.sourceLootItemIndex, statusText);
            }

            return false;
        };

    const auto tryIdentifyWithSkill =
        [&context, pParty, activeMemberIndex, pActiveMember, &overlay](std::string &statusText) -> bool
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                return pParty->tryIdentifyMemberInventoryItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceGridX,
                    overlay.sourceGridY,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                return pParty->tryIdentifyEquippedItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceEquipmentSlot,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryIdentifyActiveChestItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryIdentifyActiveCorpseItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            return false;
        };

    const auto tryRepairWithSkill =
        [&context, pParty, activeMemberIndex, pActiveMember, &overlay](std::string &statusText) -> bool
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                return pParty->tryRepairMemberInventoryItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceGridX,
                    overlay.sourceGridY,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                return pParty->tryRepairEquippedItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceEquipmentSlot,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryRepairActiveChestItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryRepairActiveCorpseItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            return false;
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
        else if (statusText == "Not skilled enough.")
        {
            context.setStatusBarEvent("Identify failed.");
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
        else if (statusText == "Not skilled enough.")
        {
            context.setStatusBarEvent("Repair failed.");
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
        context.worldRuntime()->advanceGameMinutes(advancedMinutes);
        restScreen.remainingMinutes = std::max(0.0f, restScreen.remainingMinutes - advancedMinutes);
    }

    if (restScreen.remainingMinutes > 0.0f)
    {
        return;
    }

    const GameplayUiController::RestMode completedMode = restScreen.mode;
    restScreen.mode = GameplayUiController::RestMode::None;
    restScreen.totalMinutes = 0.0f;
    restScreen.remainingMinutes = 0.0f;

    if (completedMode == GameplayUiController::RestMode::Heal && context.party() != nullptr)
    {
        context.party()->restAndHealAll();
    }

    if (completedMode == GameplayUiController::RestMode::Heal)
    {
        context.closeRestOverlay();
    }
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
    const bool *pKeyboardState,
    int width,
    int height,
    const GameplayUiOverlayInputConfig &config)
{
    GameplayUiOverlayInputResult result = GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
        context,
        pKeyboardState,
        width,
        height,
        config);

    if (result.journalInputConsumed && !config.activeEventDialog)
    {
        context.resetDialogueOverlayInteractionState();
    }

    return result;
}

void GameplayScreenController::handleSharedHotkeys(
    GameplayScreenRuntime &context,
    const bool *pKeyboardState,
    const GameplayScreenHotkeyConfig &config)
{
    GameplayScreenHotkeyController::handleGameplayScreenHotkeys(context, pKeyboardState, config);
}

GameplayUiOverlayInputResult GameplayScreenController::handleStandardUiInput(
    GameplayScreenRuntime &context,
    const GameplayStandardUiInputConfig &config)
{
    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool activeEventDialog = context.activeEventDialog().isActive;
    const bool residentSelectionMode = isResidentSelectionMode(context.activeEventDialog());
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
    const bool houseShopActive = context.houseShopOverlay().active;
    const bool houseBankInputActive = context.houseBankState().inputActive();

    const bool gameplayReadyForPortraitClicks =
        config.allowGameplayPointerInput
        && config.width > 0
        && config.height > 0
        && !config.blockPortraitInput
        && !activeEventDialog
        && !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !houseShopActive
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
                .requireGameplayReady =
                    config.requireGameplayReadyForPortraitSelection && !hasActiveLootView,
                .hasActiveLootView = hasActiveLootView,
                .onPortraitActivated = config.onPortraitActivated,
            });
    }
    else
    {
        handlePartyPortraitInput(context, GameplayPartyPortraitInputConfig{});
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
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockSpellbookToggle;

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
        && !config.blockInventoryToggle;

    const bool canCyclePartyMember =
        !activeEventDialog
        && !hasActiveLootView
        && !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockPartyCycle;

    const bool canToggleMenu =
        !activeEventDialog
        && !hasActiveLootView
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !context.inventoryNestedOverlay().active
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockMenuToggle;

    handleSharedHotkeys(
        context,
        config.pKeyboardState,
        GameplayScreenHotkeyConfig{
            .canToggleMenu = canToggleMenu,
            .canOpenRest = config.canOpenRest,
            .canToggleSpellbook = canToggleSpellbook,
            .canToggleInventory = canToggleInventory,
            .canCyclePartyMember = canCyclePartyMember,
            .hasActiveLootView = hasActiveLootView,
            .requireGameplayReadyForPartySelection = config.requireGameplayReadyForPartySelection,
        });

    const bool canClickGameplayHudButtons =
        config.allowGameplayPointerInput
        && config.width > 0
        && config.height > 0
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
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockJournalToggle;

    const bool mapShortcutPressed =
        config.pKeyboardState != nullptr
        && (config.pKeyboardState[SDL_SCANCODE_M]
            || context.mutableSettings().keyboard.isPressed(KeyboardAction::MapBook, config.pKeyboardState));
    const bool storyShortcutPressed =
        config.pKeyboardState != nullptr
        && context.mutableSettings().keyboard.isPressed(KeyboardAction::History, config.pKeyboardState);
    const bool notesShortcutPressed =
        config.pKeyboardState != nullptr
        && context.mutableSettings().keyboard.isPressed(KeyboardAction::AutoNotes, config.pKeyboardState);
    const bool zoomInPressed =
        config.pKeyboardState != nullptr
        && context.mutableSettings().keyboard.isPressed(KeyboardAction::ZoomIn, config.pKeyboardState);
    const bool zoomOutPressed =
        config.pKeyboardState != nullptr
        && context.mutableSettings().keyboard.isPressed(KeyboardAction::ZoomOut, config.pKeyboardState);

    return handleSharedOverlayInput(
        context,
        config.pKeyboardState,
        config.width,
        config.height,
        GameplayUiOverlayInputConfig{
            .hasActiveLootView = hasActiveLootView,
            .canToggleJournal = canToggleJournal,
            .mapShortcutPressed = mapShortcutPressed,
            .storyShortcutPressed = storyShortcutPressed,
            .notesShortcutPressed = notesShortcutPressed,
            .zoomInPressed = zoomInPressed,
            .zoomOutPressed = zoomOutPressed,
            .mouseWheelDelta = config.mouseWheelDelta,
            .activeEventDialog = activeEventDialog,
            .residentSelectionMode = residentSelectionMode,
            .restActive = restActive,
            .menuActive = menuActive,
            .controlsActive = controlsActive,
            .keyboardActive = keyboardActive,
            .videoOptionsActive = videoOptionsActive,
            .saveGameActive = saveGameActive,
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
            context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;

        if (!inventoryTargetMode || !config.utilitySpellInventoryTargetKeepsWorldInput)
        {
            if (!inventoryTargetMode && config.pKeyboardState != nullptr)
            {
                handleUtilitySpellOverlayInput(
                    context,
                    config.pKeyboardState,
                    config.width,
                    config.height);

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

    if (config.clearCharacterOverlayInputState)
    {
        context.resetCharacterOverlayInteractionState();
    }

    if (config.closeReadableScrollOverlay)
    {
        context.closeReadableScrollOverlay();
    }

    return {};
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
                    .renderDebugLootFallback = config.renderDebugFallbacks && hasActiveLootView,
                    .renderDebugDialogueFallback = config.renderDebugFallbacks,
                },
            .renderDeferredInventoryOverlay = deferDialogueInventoryServiceOverlay,
            .renderActorInspectOverlay = config.renderActorInspectOverlay,
        });

    if (config.onRenderedHud)
    {
        config.onRenderedHud();
    }
}

void GameplayScreenController::handleUtilitySpellOverlayInput(
    GameplayScreenRuntime &context,
    const bool *pKeyboardState,
    int width,
    int height)
{
    GameplayPartyOverlayInputController::handleUtilitySpellOverlayInput(
        context,
        pKeyboardState,
        width,
        height);
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
