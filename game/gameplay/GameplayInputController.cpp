#include "game/gameplay/GameplayInputController.h"

#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
namespace
{
bool isActionNewlyPressed(GameplayScreenRuntime &context, KeyboardAction action, const bool *pKeyboardState)
{
    if (pKeyboardState == nullptr)
    {
        return false;
    }

    const SDL_Scancode scancode = context.mutableSettings().keyboard.binding(action);

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

bool isEscapeNewlyPressed(GameplayScreenRuntime &context, const bool *pKeyboardState)
{
    return pKeyboardState != nullptr
        && pKeyboardState[SDL_SCANCODE_ESCAPE]
        && context.previousKeyboardState()[SDL_SCANCODE_ESCAPE] == 0;
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
    const bool houseShopActive = context.houseShopOverlay().active;
    const bool houseBankInputActive = context.houseBankState().inputActive();

    if (isEscapeNewlyPressed(context, config.pKeyboardState))
    {
        if (spellbookActive)
        {
            context.closeSpellbookOverlay();
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
        && !context.inventoryNestedOverlay().active
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockMenuToggle;

    if (config.pKeyboardState != nullptr)
    {
        const bool escapePressed = config.pKeyboardState[SDL_SCANCODE_ESCAPE];

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

        if (config.canOpenRest)
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
        && !houseBankInputActive
        && !config.blockPartyCycle;

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

    const size_t nextMemberIndex = (pParty->activeMemberIndex() + 1) % pParty->members().size();
    const bool requireGameplayReady =
        config.requireGameplayReadyForPartySelection
        && !activeEventDialog
        && !hasActiveLootView
        && !houseShopActive;
    context.trySelectPartyMember(nextMemberIndex, requireGameplayReady);
}

void GameplayInputController::handleSharedGameplayHotkeys(
    GameplayScreenRuntime &context,
    const GameplaySharedGameplayHotkeyConfig &config)
{
    if (config.pKeyboardState == nullptr)
    {
        context.interactionState().alwaysRunToggleLatch = false;
        context.interactionState().adventurersInnToggleLatch = false;
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
        GameplayScreenController::canEnableGameplayMouseLook(
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
                            .blockInventoryToggle = heldInventoryItem.active,
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
        const bool isQuickCastPressed =
            isActionHeld(context, KeyboardAction::CastReady, config.pInputFrame, config.pKeyboardState);

        const GameplayActionController::QuickCastActionDecision quickCastDecision =
            GameplayActionController::updateQuickCastAction(
                quickSpellState,
                GameplayActionController::QuickCastActionConfig{
                    .canRunAction = true,
                    .quickCastPressed = isQuickCastPressed,
                    .hasReadyMember = config.hasReadyMember,
                });

        if (quickCastDecision.shouldBeginQuickCast)
        {
            GameplayActionController::QuickCastActionResult quickCastResult =
                GameplayActionController::QuickCastActionResult::Failed;

            if (config.canBeginQuickCast && context.worldRuntime() != nullptr)
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

    frameResult.worldInputBlocked = worldInputGateResult.blocked;
    return frameResult;
}
} // namespace OpenYAMM::Game
