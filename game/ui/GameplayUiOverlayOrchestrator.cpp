#include "game/ui/GameplayUiOverlayOrchestrator.h"
#include "game/ui/GameplayLootSummaryRenderer.h"
#include "game/ui/GameplayFormationBuilder.h"

#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/ui/GameplayAlchemyBenchRenderer.h"
#include "game/ui/GameplayDebugOverlayRenderer.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayTransportSchedule.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/ui/GameplayHudRenderer.h"
#include "game/ui/GameplayUiRenderer.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
GameplayUiOverlayInputResult GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
    GameplayScreenRuntime &overlayContext,
    const GameplayInputFrame &input,
    const GameplayUiOverlayInputConfig &config)
{
    GameplayOverlayInputController::handleLootOverlayInput(
        overlayContext,
        input,
        config.hasActiveLootView);

    GameplayUiOverlayInputResult result = {};
    result.journalInputConsumed = GameplayOverlayInputController::handleJournalOverlayInput(
        overlayContext,
        input,
        config.canToggleJournal,
        config.mapShortcutPressed,
        config.storyShortcutPressed,
        config.questsShortcutPressed,
        config.progressShortcutPressed,
        config.zoomInPressed,
        config.zoomOutPressed,
        config.mouseWheelDelta);

    if (config.activeEventDialog)
    {
        GameplayOverlayInputController::handleDialogueOverlayInput(
            overlayContext,
            input,
            config.residentSelectionMode);
    }
    else
    {
        overlayContext.resetDialogueOverlayInteractionState();
    }

    if (config.restActive)
    {
        (void)GameplayOverlayInputController::handleRestOverlayInput(overlayContext, input);
    }
    else if (config.menuActive)
    {
        // GameApplication promotes this shared pause state to the native menu screen.
        // Do not dispatch obsolete image-button hits during the transition frame.
    }
    else if (config.controlsActive)
    {
        (void)GameplayOverlayInputController::handleControlsOverlayInput(overlayContext, input);
    }
    else if (config.keyboardActive)
    {
        (void)GameplayOverlayInputController::handleKeyboardOverlayInput(overlayContext, input);
    }
    else if (config.videoOptionsActive)
    {
        (void)GameplayOverlayInputController::handleVideoOptionsOverlayInput(overlayContext, input);
    }
    else if (config.saveGameActive)
    {
        (void)GameplayOverlayInputController::handleSaveGameOverlayInput(overlayContext, input);
    }
    else if (config.quickReferenceActive)
    {
        (void)GameplayOverlayInputController::handleQuickReferenceOverlayInput(overlayContext, input);
    }

    if (config.spellbookActive)
    {
        GameplayPartyOverlayInputController::handleSpellbookOverlayInput(overlayContext, input);
    }
    else
    {
        overlayContext.resetSpellbookOverlayInteractionState();
    }

    if (config.characterScreenOpen)
    {
        GameplayPartyOverlayInputController::handleCharacterOverlayInput(overlayContext, input);
    }
    else
    {
        overlayContext.resetCharacterOverlayInteractionState();
    }

    return result;
}

void GameplayUiOverlayOrchestrator::renderStandardOverlays(
    GameplayScreenRuntime &overlayContext,
    int width,
    int height,
    const GameplayUiOverlayRenderConfig &config,
    GameplayUiOverlayFramePerformanceDiagnostics *pPerformanceDiagnostics)
{
    if (pPerformanceDiagnostics != nullptr)
    {
        *pPerformanceDiagnostics = {};
        pPerformanceDiagnostics->collected = true;
    }

    const uint64_t totalBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    uint64_t stageBeginTickCount = totalBeginTickCount;
    const auto recordStage =
        [&](uint64_t GameplayUiOverlayFramePerformanceDiagnostics::*pField)
        {
            if (pPerformanceDiagnostics == nullptr)
            {
                return;
            }

            const uint64_t nowTickCount = SDL_GetTicksNS();
            pPerformanceDiagnostics->*pField += nowTickCount - stageBeginTickCount;
            stageBeginTickCount = nowTickCount;
        };
    const auto finishDiagnostics =
        [&]()
        {
            if (pPerformanceDiagnostics != nullptr)
            {
                pPerformanceDiagnostics->totalNanoseconds = SDL_GetTicksNS() - totalBeginTickCount;
            }
        };

    overlayContext.beginRenderedInspectableHudFrame();
    recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::beginInspectableFrameNanoseconds);
    // The character screen's two passes share what it works out for the frame.
    std::shared_ptr<CharacterOverlayFrameData> characterFrameData;

    if (config.canRenderHudOverlays)
    {
        const bool activeOrPendingDialog =
            overlayContext.activeEventDialog().isActive || overlayContext.hasPendingEventDialog();

        if ((config.renderDialogueBelowHud || config.renderDialogueAboveHud || config.renderDebugDialogueFallback)
            && activeOrPendingDialog)
        {
            overlayContext.ensurePendingEventDialogPresented(true);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::pendingDialogNanoseconds);

        overlayContext.fxService().renderGameplayScreenOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::screenFxNanoseconds);

        if (config.renderChestBelowHud)
        {
            GameplayHudOverlayRenderer::renderChestPanel(overlayContext, width, height, false);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::chestBelowNanoseconds);

        if (config.renderInventoryBelowHud)
        {
            GameplayHudOverlayRenderer::renderInventoryNestedOverlay(overlayContext, width, height, false);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::inventoryBelowNanoseconds);

        if (config.renderDialogueBelowHud && overlayContext.activeEventDialog().isActive)
        {
            GameplayDialogueRenderer::renderDialogueOverlay(overlayContext, width, height, false);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::dialogueBelowNanoseconds);

        if (config.renderCharacterBelowHud)
        {
            GameplayPartyOverlayRenderer::renderCharacterOverlay(
                overlayContext, width, height, false, characterFrameData);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::characterBelowNanoseconds);

        GameplayUiRenderer::renderGameplayHudArt(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::hudArtNanoseconds);
        GameplayHudRenderer::renderGameplayHud(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::hudNanoseconds);

        if (config.renderChestAboveHud)
        {
            GameplayHudOverlayRenderer::renderChestPanel(overlayContext, width, height, true);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::chestAboveNanoseconds);

        if (config.renderInventoryAboveHud)
        {
            GameplayHudOverlayRenderer::renderInventoryNestedOverlay(overlayContext, width, height, true);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::inventoryAboveNanoseconds);

        if (config.renderCharacterAboveHud)
        {
            GameplayPartyOverlayRenderer::renderCharacterOverlay(
                overlayContext, width, height, true, characterFrameData);
            GameplayAlchemyBenchRenderer::render(overlayContext, width, height);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::characterAboveNanoseconds);

        if (config.renderDialogueAboveHud && overlayContext.activeEventDialog().isActive)
        {
            GameplayDialogueRenderer::renderDialogueOverlay(overlayContext, width, height, true);
        }

        GameplayTransportSchedule::render(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::dialogueAboveNanoseconds);

        GameplayPartyOverlayRenderer::renderRestOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::restNanoseconds);
        // The native pause screen is rendered by GameApplication above the frozen game view.
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::menuNanoseconds);
        GameplayPartyOverlayRenderer::renderControlsOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::controlsNanoseconds);
        GameplayPartyOverlayRenderer::renderKeyboardOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::keyboardNanoseconds);
        GameplayPartyOverlayRenderer::renderVideoOptionsOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::videoOptionsNanoseconds);
        GameplayPartyOverlayRenderer::renderSaveGameOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::saveGameNanoseconds);
        GameplayPartyOverlayRenderer::renderLoadGameOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::loadGameNanoseconds);
        GameplayPartyOverlayRenderer::renderJournalOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::journalNanoseconds);
        GameplayPartyOverlayRenderer::renderQuickReferenceOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::quickReferenceNanoseconds);
        GameplayPartyOverlayRenderer::renderSpellbookOverlay(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::spellbookNanoseconds);
        // Under the held item and the item popup, so its items can be inspected.
        GameplayLootSummaryRenderer::render(overlayContext, width, height);
        GameplayFormationBuilder::render(overlayContext, width, height);
        GameplayPartyOverlayRenderer::renderHeldInventoryItem(overlayContext, width, height);
        GameplayUiRenderer::renderMobileInspectButton(overlayContext, width, height);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::heldItemNanoseconds);
        if (config.renderItemInspectOverlay)
        {
            GameplayPartyOverlayRenderer::renderItemInspectOverlay(overlayContext, width, height);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::itemInspectNanoseconds);
        GameplayHudOverlaySupport::renderGameplayMouseLookOverlay(
            overlayContext,
            width,
            height,
            config.renderGameplayMouseLookOverlay);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::mouseLookNanoseconds);

        finishDiagnostics();
        return;
    }

    if (config.renderDebugDialogueFallback
        && (overlayContext.activeEventDialog().isActive || overlayContext.hasPendingEventDialog()))
    {
        overlayContext.ensurePendingEventDialogPresented(true);
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::pendingDialogNanoseconds);

        if (overlayContext.activeEventDialog().isActive)
        {
            GameplayDebugOverlayRenderer::renderEventDialogPanel(overlayContext, width, height);
        }
        recordStage(&GameplayUiOverlayFramePerformanceDiagnostics::dialogueAboveNanoseconds);
    }

    finishDiagnostics();
}
} // namespace OpenYAMM::Game
