#include "game/gameplay/GameplayDialogUiFlow.h"

#include "game/gameplay/GameplayInputFrame.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
namespace
{
void resetDialogInteractionState(GameplayDialogUiFlowState &state, bool suppressInitialAccept)
{
    state.selectionIndex = 0;
    state.interactionState.eventDialogSelectUpLatch = false;
    state.interactionState.eventDialogSelectDownLatch = false;
    state.interactionState.eventDialogAcceptLatch = suppressInitialAccept;
    state.interactionState.eventDialogPartySelectLatches.fill(false);
}

bool shouldSuppressInitialAccept(const GameplayInputFrame &input)
{
    return input.isScancodeHeld(SDL_SCANCODE_SPACE)
        || input.isScancodeHeld(SDL_SCANCODE_RETURN)
        || input.isScancodeHeld(SDL_SCANCODE_KP_ENTER);
}
}

void presentPendingEventDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const GameplayDialogUiFlowPresentOptions &options,
    const std::function<void(const GameplayDialogController::PresentPendingDialogResult &)> &onOpened)
{
    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    state.uiController.closeInventoryNestedOverlay();
    state.interactionState.inventoryNestedOverlayClickLatch = false;
    state.interactionState.inventoryNestedOverlayPressedTarget = {};
    state.interactionState.inventoryNestedOverlayItemClickLatch = false;
    state.uiController.houseShopOverlay() = {};

    const bool showBankInputCursor = (SDL_GetTicks() / 500u) % 2u == 0u;
    const GameplayDialogController::PresentPendingDialogResult result =
        state.dialogController.presentPendingEventDialog(
            context,
            previousMessageCount,
            allowNpcFallbackContent,
            showBankInputCursor);

    if (!result.dialogOpened)
    {
        return;
    }

    resetDialogInteractionState(
        state,
        options.suppressInitialAcceptIfActivationKeysHeld
            && options.pInputFrame != nullptr
            && shouldSuppressInitialAccept(*options.pInputFrame));

    if (onOpened)
    {
        onOpened(result);
    }
}

void closeActiveEventDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->pendingDialogueContext.reset();
        pEventRuntimeState->dialogueState = {};
    }

    state.uiController.clearEventDialog();
    resetDialogInteractionState(state, false);
    state.interactionState.dialogueClickLatch = false;
    state.interactionState.dialoguePressedTarget = {};
    state.uiController.houseShopOverlay() = {};
    state.uiController.closeInventoryNestedOverlay();
    state.interactionState.inventoryNestedOverlayClickLatch = false;
    state.interactionState.inventoryNestedOverlayPressedTarget = {};
    state.interactionState.inventoryNestedOverlayItemClickLatch = false;
    state.uiController.clearHouseBankState();
}

bool refreshHouseBankInputDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context,
    bool showCursor)
{
    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    return state.dialogController.refreshHouseBankInputDialog(context, showCursor);
}

GameplayDialogController::Result returnToHouseBankMainDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context)
{
    state.interactionState.houseBankDigitLatches.fill(false);
    state.interactionState.houseBankBackspaceLatch = false;
    state.interactionState.houseBankConfirmLatch = false;

    if (pEventRuntimeState == nullptr)
    {
        return {};
    }

    return state.dialogController.returnToHouseBankMainDialog(context);
}

GameplayDialogController::Result confirmHouseBankInput(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context)
{
    if (pEventRuntimeState == nullptr)
    {
        state.interactionState.houseBankDigitLatches.fill(false);
        state.interactionState.houseBankBackspaceLatch = false;
        state.interactionState.houseBankConfirmLatch = false;
        return {};
    }

    const GameplayDialogController::Result result = state.dialogController.confirmHouseBankInput(context);
    state.interactionState.houseBankDigitLatches.fill(false);
    state.interactionState.houseBankBackspaceLatch = false;
    state.interactionState.houseBankConfirmLatch = false;
    return result;
}
}
