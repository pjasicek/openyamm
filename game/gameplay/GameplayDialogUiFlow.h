#pragma once

#include "game/gameplay/GameplayDialogController.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"

#include <functional>

namespace OpenYAMM::Game
{
struct GameplayInputFrame;

struct GameplayDialogUiFlowState
{
    GameplayUiController &uiController;
    GameplayOverlayInteractionState &interactionState;
    GameplayDialogController &dialogController;
    size_t &selectionIndex;
};

struct GameplayDialogUiFlowPresentOptions
{
    const GameplayInputFrame *pInputFrame = nullptr;
    bool suppressInitialAcceptIfActivationKeysHeld = false;
};

void presentPendingEventDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const GameplayDialogUiFlowPresentOptions &options = {},
    const std::function<void(const GameplayDialogController::PresentPendingDialogResult &)> &onOpened = {});

void closeActiveEventDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState);

bool refreshHouseBankInputDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context,
    bool showCursor);

GameplayDialogController::Result returnToHouseBankMainDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context);

GameplayDialogController::Result confirmHouseBankInput(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    GameplayDialogController::Context &context);
}
