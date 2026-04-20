#pragma once

#include "game/gameplay/GameplayDialogController.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"

#include <functional>

namespace OpenYAMM::Game
{
struct GameplayDialogUiFlowState
{
    GameplayUiController &uiController;
    GameplayOverlayInteractionState &interactionState;
    GameplayDialogController &dialogController;
    size_t &selectionIndex;
};

using GameplayDialogUiContextBuilder = std::function<GameplayDialogController::Context(EventRuntimeState &)>;

struct GameplayDialogUiFlowPresentOptions
{
    bool suppressInitialAcceptIfActivationKeysHeld = false;
};

void presentPendingEventDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    const GameplayDialogUiContextBuilder &buildContext,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const GameplayDialogUiFlowPresentOptions &options = {},
    const std::function<void(const GameplayDialogController::PresentPendingDialogResult &)> &onOpened = {});

void closeActiveEventDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    const std::function<void(uint32_t hostHouseId)> &onClosed = {});

bool refreshHouseBankInputDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    const GameplayDialogUiContextBuilder &buildContext,
    bool showCursor);

GameplayDialogController::Result returnToHouseBankMainDialog(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    const GameplayDialogUiContextBuilder &buildContext);

GameplayDialogController::Result confirmHouseBankInput(
    GameplayDialogUiFlowState &state,
    EventRuntimeState *pEventRuntimeState,
    const GameplayDialogUiContextBuilder &buildContext);
}
