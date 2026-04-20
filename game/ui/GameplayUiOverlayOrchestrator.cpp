#include "game/ui/GameplayUiOverlayOrchestrator.h"

#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/ui/GameplayDebugOverlayRenderer.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/ui/GameplayHudRenderer.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"

namespace OpenYAMM::Game
{
GameplayUiOverlayInputResult GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
    GameplayOverlayContext &overlayContext,
    const bool *pKeyboardState,
    int width,
    int height,
    const GameplayUiOverlayInputConfig &config,
    const GameplayUiOverlayInputCallbacks &callbacks)
{
    GameplayOverlayInputController::handleLootOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height,
        config.hasActiveLootView);

    GameplayUiOverlayInputResult result = {};
    result.journalInputConsumed = GameplayOverlayInputController::handleJournalOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height,
        config.canToggleJournal,
        config.mapShortcutPressed,
        config.storyShortcutPressed,
        config.notesShortcutPressed,
        config.zoomInPressed,
        config.zoomOutPressed,
        config.mouseWheelDelta);

    if (config.activeEventDialog)
    {
        GameplayOverlayInputController::handleDialogueOverlayInput(
            overlayContext,
            pKeyboardState,
            width,
            height,
            config.residentSelectionMode);
    }
    else if (callbacks.resetDialogueInteractionState)
    {
        callbacks.resetDialogueInteractionState();
    }

    if (config.restActive)
    {
        (void)GameplayOverlayInputController::handleRestOverlayInput(overlayContext, pKeyboardState, width, height);
    }
    else if (config.menuActive)
    {
        (void)GameplayOverlayInputController::handleMenuOverlayInput(overlayContext, pKeyboardState, width, height);
    }
    else if (config.controlsActive)
    {
        (void)GameplayOverlayInputController::handleControlsOverlayInput(overlayContext, pKeyboardState, width, height);
    }
    else if (config.keyboardActive)
    {
        (void)GameplayOverlayInputController::handleKeyboardOverlayInput(overlayContext, pKeyboardState, width, height);
    }
    else if (config.videoOptionsActive)
    {
        (void)GameplayOverlayInputController::handleVideoOptionsOverlayInput(
            overlayContext,
            pKeyboardState,
            width,
            height);
    }
    else if (config.saveGameActive)
    {
        (void)GameplayOverlayInputController::handleSaveGameOverlayInput(overlayContext, pKeyboardState, width, height);
    }

    if (config.spellbookActive && callbacks.handleSpellbookOverlayInput)
    {
        callbacks.handleSpellbookOverlayInput(pKeyboardState, width, height);
    }

    if (config.characterScreenOpen && callbacks.handleCharacterOverlayInput)
    {
        callbacks.handleCharacterOverlayInput(pKeyboardState, width, height);
    }

    return result;
}

void GameplayUiOverlayOrchestrator::renderStandardOverlays(
    GameplayOverlayContext &overlayContext,
    int width,
    int height,
    const GameplayUiOverlayRenderConfig &config,
    const GameplayUiOverlayRenderCallbacks &callbacks)
{
    if (config.canRenderHudOverlays)
    {
        if (config.renderChestBelowHud && callbacks.renderChestOverlay)
        {
            callbacks.renderChestOverlay(false);
        }

        if (config.renderInventoryBelowHud && callbacks.renderInventoryNestedOverlay)
        {
            callbacks.renderInventoryNestedOverlay(false);
        }

        if (config.renderDialogueBelowHud && callbacks.renderDialogueOverlay)
        {
            callbacks.renderDialogueOverlay(false);
        }

        if (config.renderCharacterBelowHud && callbacks.renderCharacterOverlay)
        {
            callbacks.renderCharacterOverlay(false);
        }

        GameplayHudRenderer::renderGameplayHudArt(overlayContext, width, height);
        GameplayHudRenderer::renderGameplayHud(overlayContext, width, height);

        if (config.renderChestAboveHud && callbacks.renderChestOverlay)
        {
            callbacks.renderChestOverlay(true);
        }

        if (config.renderInventoryAboveHud && callbacks.renderInventoryNestedOverlay)
        {
            callbacks.renderInventoryNestedOverlay(true);
        }

        if (config.renderCharacterAboveHud && callbacks.renderCharacterOverlay)
        {
            callbacks.renderCharacterOverlay(true);
        }

        if (config.renderDialogueAboveHud && callbacks.renderDialogueOverlay)
        {
            callbacks.renderDialogueOverlay(true);
        }

        GameplayPartyOverlayRenderer::renderRestOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderMenuOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderControlsOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderKeyboardOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderVideoOptionsOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderSaveGameOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderLoadGameOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderJournalOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderSpellbookOverlay(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderHeldInventoryItem(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderItemInspectOverlay(overlayContext, width, height);

        if (callbacks.renderGameplayMouseLookOverlay)
        {
            callbacks.renderGameplayMouseLookOverlay();
        }

        return;
    }

    if (config.hasActiveLootView && config.renderDebugLootFallback)
    {
        GameplayDebugOverlayRenderer::renderChestPanel(overlayContext, width, height);
    }

    if (config.activeEventDialog && config.renderDebugDialogueFallback)
    {
        GameplayDebugOverlayRenderer::renderEventDialogPanel(overlayContext, width, height);
    }
}
} // namespace OpenYAMM::Game
