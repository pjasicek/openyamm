#include "game/ui/GameplayUiOverlayOrchestrator.h"

#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/ui/GameplayDebugOverlayRenderer.h"
#include "game/ui/GameplayDialogueRenderer.h"
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
        if (config.renderDialogueBelowHud || config.renderDialogueAboveHud || config.renderDebugDialogueFallback)
        {
            overlayContext.ensurePendingEventDialogPresented(true);
        }

        if (config.renderChestBelowHud)
        {
            GameplayHudOverlayRenderer::renderChestPanel(overlayContext, width, height, false);
        }

        if (config.renderInventoryBelowHud)
        {
            GameplayHudOverlayRenderer::renderInventoryNestedOverlay(overlayContext, width, height, false);
        }

        if (config.renderDialogueBelowHud && overlayContext.activeEventDialog().isActive)
        {
            GameplayDialogueRenderer::renderDialogueOverlay(overlayContext, width, height, false);
        }

        if (config.renderCharacterBelowHud)
        {
            GameplayPartyOverlayRenderer::renderCharacterOverlay(overlayContext, width, height, false);
        }

        GameplayHudRenderer::renderGameplayHudArt(overlayContext, width, height);
        GameplayHudRenderer::renderGameplayHud(overlayContext, width, height);

        if (config.renderChestAboveHud)
        {
            GameplayHudOverlayRenderer::renderChestPanel(overlayContext, width, height, true);
        }

        if (config.renderInventoryAboveHud)
        {
            GameplayHudOverlayRenderer::renderInventoryNestedOverlay(overlayContext, width, height, true);
        }

        if (config.renderCharacterAboveHud)
        {
            GameplayPartyOverlayRenderer::renderCharacterOverlay(overlayContext, width, height, true);
        }

        if (config.renderDialogueAboveHud && overlayContext.activeEventDialog().isActive)
        {
            GameplayDialogueRenderer::renderDialogueOverlay(overlayContext, width, height, true);
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

    if (config.renderDebugDialogueFallback)
    {
        overlayContext.ensurePendingEventDialogPresented(true);

        if (overlayContext.activeEventDialog().isActive)
        {
            GameplayDebugOverlayRenderer::renderEventDialogPanel(overlayContext, width, height);
        }
    }
}
} // namespace OpenYAMM::Game
